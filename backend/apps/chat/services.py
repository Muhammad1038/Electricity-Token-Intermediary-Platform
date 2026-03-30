"""
chat.services — AI-powered customer support using Google Gemini (FREE tier).

Tools available to the AI:
  • lookup_transaction   — find a transaction by reference
  • get_recent_transactions — last N transactions for the user
  • check_token_status   — detailed status of a specific transaction
  • get_disco_info       — info about a DISCO (name, min amount, area)
  • resend_failed_token  — trigger a resend for a failed transaction

Gemini free tier: 15 RPM, 1 million tokens/day — perfect for a student project.
"""
import json
import logging
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from apps.transactions.models import Transaction, TokenStatus, PaymentStatus
from .knowledge import build_faq_section
from .models import Message

logger = logging.getLogger(__name__)

# ── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are **ETIP Assistant**, the friendly AI helper for the Electricity Token Intermediary Platform (ETIP).

Your responsibilities:
- Help users with token purchases, transaction lookups, and DISCO information
- Answer common questions about the platform
- Look up specific transactions when asked
- Check token delivery status
- Offer to resend failed tokens (with user confirmation)
- Be concise, helpful, and Nigerian-context aware
- Use Naira (₦) for money amounts
- If you cannot resolve an issue, offer to escalate to human support at support@etip.ng

Important rules:
- You can ONLY see the current user's own transactions — never cross-user data
- Always be empathetic about failed transactions — the user's money is safe
- When looking up transactions, show relevant details (reference, amount, status, date)
- Format token values clearly with spacing for readability
- Keep responses concise — 2-4 sentences when possible, more if explaining a process

{faq_section}
""".format(faq_section=build_faq_section())

# ── Gemini Function Declarations ─────────────────────────────────────────────
# google.genai uses a slightly different schema than OpenAI.

TOOL_DECLARATIONS = [
    {
        "name": "lookup_transaction",
        "description": "Look up a specific transaction by its reference number (e.g., ETIP-XXXXXXXXXX).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "reference": {
                    "type": "STRING",
                    "description": "The transaction reference (e.g., ETIP-A978A0C25F4D)",
                }
            },
            "required": ["reference"],
        },
    },
    {
        "name": "get_recent_transactions",
        "description": "Get the user's most recent transactions. Use when the user asks about their recent purchases or transaction history.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "count": {
                    "type": "INTEGER",
                    "description": "Number of recent transactions to return (default 5, max 10).",
                }
            },
            "required": [],
        },
    },
    {
        "name": "check_token_status",
        "description": "Check the detailed token delivery status for a transaction. Use when the user asks if their token has been delivered.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "reference": {
                    "type": "STRING",
                    "description": "The transaction reference to check.",
                }
            },
            "required": ["reference"],
        },
    },
    {
        "name": "get_disco_info",
        "description": "Get information about a specific DISCO (electricity distribution company) — name, minimum amount, service area.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "disco_code": {
                    "type": "STRING",
                    "description": "The DISCO code (e.g., EEDC, IBEDC, EKEDC, KAEDCO, AEDC, PHED, JED, BEDC, KEDCO, YEDC, IE).",
                }
            },
            "required": ["disco_code"],
        },
    },
    {
        "name": "resend_failed_token",
        "description": "Trigger a resend for a failed or pending token. Only use when the user explicitly asks to resend and confirms.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "reference": {
                    "type": "STRING",
                    "description": "The transaction reference to resend.",
                }
            },
            "required": ["reference"],
        },
    },
]

# ── DISCO Info Data ──────────────────────────────────────────────────────────

DISCO_INFO = {
    "EEDC": {"name": "Enugu Electricity Distribution Company", "min_amount": 1000, "area": "South-East Nigeria (Enugu, Anambra, Imo, Abia, Ebonyi)"},
    "IBEDC": {"name": "Ibadan Electricity Distribution Company", "min_amount": 1500, "area": "South-West Nigeria (Oyo, Ogun, Osun, Kwara)"},
    "EKEDC": {"name": "Eko Electricity Distribution Company", "min_amount": 1000, "area": "Lagos (Apapa, Lekki, V/Island, Mushin, Ojo)"},
    "KAEDCO": {"name": "Kaduna Electricity Distribution Company", "min_amount": 1500, "area": "North-West Nigeria (Kaduna, Sokoto, Kebbi, Zamfara)"},
    "AEDC": {"name": "Abuja Electricity Distribution Company", "min_amount": 1000, "area": "FCT Abuja, Niger, Kogi, Nasarawa"},
    "PHED": {"name": "Port Harcourt Electricity Distribution", "min_amount": 1000, "area": "South-South Nigeria (Rivers, Bayelsa, Cross River, Akwa Ibom)"},
    "JED": {"name": "Jos Electricity Distribution", "min_amount": 1000, "area": "North-Central Nigeria (Plateau, Benue, Gombe, Bauchi)"},
    "BEDC": {"name": "Benin Electricity Distribution Company", "min_amount": 1000, "area": "South-South Nigeria (Edo, Delta, Ondo, Ekiti)"},
    "KEDCO": {"name": "Kano Electricity Distribution Company", "min_amount": 1000, "area": "North-West Nigeria (Kano, Jigawa, Katsina)"},
    "YEDC": {"name": "Yola Electricity Distribution Company", "min_amount": 1000, "area": "North-East Nigeria (Adamawa, Borno, Taraba, Yobe)"},
    "IE": {"name": "Ikeja Electric", "min_amount": 1000, "area": "Lagos (Ikeja, Ikorodu, Shomolu, Agege)"},
}


class ChatService:
    """
    Orchestrates conversation with Google Gemini, including function calling.
    Uses the free gemini-2.0-flash model.
    """

    def __init__(self, user, conversation):
        self.user = user
        self.conversation = conversation
        self.max_context = getattr(settings, "CHAT_MAX_CONTEXT_MESSAGES", 20)
        self.model = getattr(settings, "CHAT_MODEL", "gemini-2.0-flash")

    # ── Public API ───────────────────────────────────────────────────────────

    def get_reply(self, user_text: str) -> str:
        """
        Build conversation context, call Gemini (with function-calling loop),
        and return the final assistant reply text.
        Includes automatic retry for rate-limit (429) errors.
        """
        import time
        from google import genai
        from google.genai import types
        from google.genai.errors import ClientError

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Build Gemini contents (conversation history)
        contents = self._build_contents(user_text)

        # Configure tools for function calling
        tools = types.Tool(function_declarations=TOOL_DECLARATIONS)

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[tools],
            temperature=0.7,
            max_output_tokens=600,
        )

        # Iterative loop: model may request function calls
        for _ in range(5):  # max 5 rounds to prevent infinite loops
            # Retry up to 3 times on rate-limit errors
            response = None
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=config,
                    )
                    break  # success
                except ClientError as e:
                    if e.status_code == 429 and attempt < 2:
                        wait = (attempt + 1) * 8  # 8s, 16s
                        logger.warning("[Chat] Rate limited (429), retrying in %ds (attempt %d/3)", wait, attempt + 1)
                        time.sleep(wait)
                        continue
                    raise  # re-raise if not 429 or final attempt

            if response is None:
                return "I'm a bit busy right now. Please try again in a minute!"

            # Check if model wants to call functions
            part = response.candidates[0].content.parts[0]

            if part.function_call:
                fn_call = part.function_call
                fn_name = fn_call.name
                fn_args = dict(fn_call.args) if fn_call.args else {}

                logger.info("[Chat] Gemini function call: %s(%s)", fn_name, fn_args)

                # Execute the tool
                result = self._execute_tool(fn_name, fn_args)

                # Feed function call + result back into the conversation
                contents.append(response.candidates[0].content)
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_function_response(
                            name=fn_name,
                            response=result,
                        )],
                    )
                )
                continue
            else:
                # Final text reply
                text = response.text
                return text or "I'm not sure how to help with that. Try asking a different way!"

        return "I ran into an issue processing your request. Please try again."

    # ── Content Builder ──────────────────────────────────────────────────────

    def _build_contents(self, latest_user_text: str) -> list:
        """
        Build the Gemini contents array from conversation history.
        Gemini uses role='user' and role='model' (not 'assistant').
        """
        from google.genai import types

        contents = []

        # Load recent conversation history
        recent = (
            Message.objects
            .filter(conversation=self.conversation)
            .order_by("-created_at")[: self.max_context]
        )
        for m in reversed(list(recent)):
            role = "model" if m.role == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m.content)]))

        # The latest user message
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=latest_user_text)]))

        return contents

    # ── Tool Execution ───────────────────────────────────────────────────────

    def _execute_tool(self, name: str, args: dict) -> dict:
        """Dispatch tool calls to local handlers."""
        logger.info("[Chat] Tool call: %s(%s) for user %s", name, args, self.user.id)
        try:
            if name == "lookup_transaction":
                return self._tool_lookup_transaction(args["reference"])
            elif name == "get_recent_transactions":
                return self._tool_recent_transactions(args.get("count", 5))
            elif name == "check_token_status":
                return self._tool_check_token_status(args["reference"])
            elif name == "get_disco_info":
                return self._tool_get_disco_info(args["disco_code"])
            elif name == "resend_failed_token":
                return self._tool_resend_token(args["reference"])
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            logger.exception("[Chat] Tool error: %s", e)
            return {"error": str(e)}

    def _tool_lookup_transaction(self, reference: str) -> dict:
        """Find a transaction by reference, scoped to current user."""
        txn = (
            Transaction.objects
            .filter(user=self.user, reference__iexact=reference.strip())
            .first()
        )
        if not txn:
            return {"found": False, "message": f"No transaction found with reference '{reference}' on your account."}
        return self._serialize_transaction(txn)

    def _tool_recent_transactions(self, count: int) -> dict:
        count = min(max(count, 1), 10)
        txns = Transaction.objects.filter(user=self.user).order_by("-created_at")[:count]
        if not txns:
            return {"found": False, "message": "You don't have any transactions yet."}
        return {
            "found": True,
            "count": len(txns),
            "transactions": [self._serialize_transaction(t) for t in txns],
        }

    def _tool_check_token_status(self, reference: str) -> dict:
        txn = (
            Transaction.objects
            .filter(user=self.user, reference__iexact=reference.strip())
            .first()
        )
        if not txn:
            return {"found": False, "message": f"No transaction found with reference '{reference}'."}

        result = self._serialize_transaction(txn)
        # Add extra detail for status check
        result["can_resend"] = txn.can_resend_token
        result["resend_attempts"] = txn.resend_attempts
        result["max_resend_attempts"] = 3
        if txn.token_status == TokenStatus.PENDING:
            result["advice"] = "Token is still being processed. Please wait a few minutes."
        elif txn.token_status == TokenStatus.FAILED:
            if txn.can_resend_token:
                result["advice"] = "Token delivery failed. You can ask me to resend it for you."
            else:
                result["advice"] = "Token failed and resend attempts exhausted. Please contact support@etip.ng."
        elif txn.token_status in [TokenStatus.DELIVERED, TokenStatus.RESENT]:
            result["advice"] = "Token was delivered successfully! Check 'My Tokens' tab in the app."
        return result

    def _tool_get_disco_info(self, disco_code: str) -> dict:
        code = disco_code.strip().upper()
        info = DISCO_INFO.get(code)
        if not info:
            return {"found": False, "message": f"Unknown DISCO code: {code}. Try EEDC, IBEDC, EKEDC, etc."}
        return {
            "found": True,
            "code": code,
            "name": info["name"],
            "minimum_amount": f"₦{info['min_amount']:,}",
            "service_area": info["area"],
        }

    def _tool_resend_token(self, reference: str) -> dict:
        txn = (
            Transaction.objects
            .filter(user=self.user, reference__iexact=reference.strip())
            .first()
        )
        if not txn:
            return {"success": False, "message": f"No transaction found with reference '{reference}'."}
        if not txn.can_resend_token:
            if txn.token_status in [TokenStatus.DELIVERED, TokenStatus.RESENT]:
                return {"success": False, "message": "This token was already delivered successfully!"}
            if txn.resend_attempts >= 3:
                return {"success": False, "message": "Maximum resend attempts (3) reached. Please contact support@etip.ng."}
            return {"success": False, "message": "This transaction cannot be resent right now."}

        # Trigger the resend via Celery task
        from apps.transactions.tasks import generate_token
        txn.resend_attempts += 1
        txn.last_resend_at = timezone.now()
        txn.token_status = TokenStatus.PENDING
        txn.save(update_fields=["resend_attempts", "last_resend_at", "token_status", "updated_at"])
        generate_token.delay(str(txn.id))

        return {
            "success": True,
            "message": f"Token resend triggered for {reference}! Check 'My Tokens' tab in a few seconds.",
            "resend_attempt": txn.resend_attempts,
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _serialize_transaction(self, txn: Transaction) -> dict:
        """Serialize a transaction for the AI to read."""
        return {
            "found": True,
            "reference": txn.reference,
            "meter_number": txn.meter_number,
            "disco": txn.disco,
            "meter_owner_name": txn.meter_owner_name or "N/A",
            "amount": f"₦{txn.amount:,.2f}",
            "service_fee": f"₦{txn.service_fee:,.2f}",
            "total": f"₦{txn.total_amount:,.2f}",
            "payment_status": txn.payment_status,
            "token_status": txn.token_status,
            "token_delivered_at": str(txn.token_delivered_at) if txn.token_delivered_at else None,
            "created_at": str(txn.created_at),
        }
