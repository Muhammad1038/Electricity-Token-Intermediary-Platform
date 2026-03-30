"""
chat.knowledge — FAQ knowledge base for the AI assistant.
Injected into the system prompt so the model can answer common questions
without needing function calls.
"""

ETIP_FAQ = {
    "What is ETIP?": (
        "ETIP (Electricity Token Intermediary Platform) is a mobile app that lets "
        "you buy prepaid electricity tokens instantly from your phone. We connect to "
        "your DISCO (electricity distribution company) and deliver your token in seconds."
    ),
    "Which DISCOs do you support?": (
        "We currently support these DISCOs:\n"
        "• EEDC (Enugu Electricity Distribution Company)\n"
        "• IBEDC (Ibadan Electricity Distribution Company)\n"
        "• EKEDC (Eko Electricity Distribution Company)\n"
        "• KAEDCO (Kaduna Electricity Distribution Company)\n"
        "• AEDC (Abuja Electricity Distribution Company)\n"
        "• PHED (Port Harcourt Electricity Distribution)\n"
        "• JED (Jos Electricity Distribution)\n"
        "• BEDC (Benin Electricity Distribution Company)\n"
        "• KEDCO (Kano Electricity Distribution Company)\n"
        "• YEDC (Yola Electricity Distribution Company)\n"
        "• IE (Ikeja Electric)"
    ),
    "What is the minimum purchase amount?": (
        "The minimum amount depends on your DISCO:\n"
        "• IBEDC: ₦1,500\n"
        "• KAEDCO: ₦1,500\n"
        "• All others: ₦1,000"
    ),
    "How long does token delivery take?": (
        "Token delivery usually takes under 30 seconds after payment is confirmed. "
        "In rare cases (DISCO delays), it could take up to 2 minutes. "
        "The app checks automatically every 5 seconds."
    ),
    "What payment methods are supported?": (
        "We accept:\n"
        "• Debit/credit cards (Visa, Mastercard, Verve)\n"
        "• Bank transfer\n"
        "• USSD banking\n"
        "All payments are processed securely through Paystack."
    ),
    "My token failed — what should I do?": (
        "If your token failed:\n"
        "1. Go to 'My Tokens' tab\n"
        "2. Find the transaction with a red 'Failed' indicator\n"
        "3. Tap the '🔄 Resend Token' button (up to 3 attempts)\n"
        "Your payment is safe — we only charge you once and will keep trying to get your token."
    ),
    "I was charged but didn't receive a token": (
        "Don't worry — your money is safe. This can happen if the DISCO is slow to respond.\n"
        "1. Check 'My Tokens' tab — it may still show as 'Processing'\n"
        "2. Wait 2-3 minutes — the app auto-checks for your token\n"
        "3. If it shows 'Failed', tap 'Resend Token'\n"
        "4. If the issue persists, give me your transaction reference and I'll look it up for you."
    ),
    "How do I add a meter?": (
        "To add a meter:\n"
        "1. Go to the 'Meters' tab\n"
        "2. Enter your 11-13 digit meter number\n"
        "3. Select your DISCO\n"
        "4. Give it a nickname (e.g., 'Home', 'Office')\n"
        "5. Tap 'Save Meter'\n"
        "You can save multiple meters."
    ),
    "Is my payment information safe?": (
        "Absolutely. We never store your card details. All payments go through "
        "Paystack, a PCI-DSS Level 1 certified payment processor. "
        "Your electricity tokens are also stored encrypted."
    ),
    "How do I contact support?": (
        "You're chatting with our AI assistant right now! I can help with most issues.\n"
        "If I can't resolve something, you can reach our team at:\n"
        "• Email: support@etip.ng\n"
        "• WhatsApp: +234 XXX XXX XXXX"
    ),
    "Can I get a refund?": (
        "If your token delivery failed permanently and resend attempts are exhausted, "
        "our team will review and process a refund. Please contact support@etip.ng "
        "with your transaction reference."
    ),
    "How do I view my receipt?": (
        "On the 'My Tokens' tab, find a delivered token and tap '🧾 View Receipt'. "
        "From the receipt screen you can:\n"
        "• Share the receipt as a PDF via WhatsApp, email, etc.\n"
        "• Download the PDF directly to your phone storage."
    ),
    "Why is my meter blinking red really fast?": (
        "That's the pulse indicator. It blinks faster when you use more appliances. "
        "Turn off heavy appliances like heaters to slow it down and save power."
    ),
    "What do the green and yellow lights mean on my meter?": (
        "Green means you have plenty of power left. Yellow is a warning that credit is getting low. "
        "If it turns red, your balance is critical—time to recharge!"
    ),
    "My meter is flashing and showing an error code": (
        "This usually means a fault, voltage drop, or tampering is detected. "
        "Please contact your electricity distributor to investigate or reset the meter."
    ),
    "Electricity prices changed. Do I need to update my meter?": (
        "No extra steps needed! The new prices automatically update on your meter the next time you load a standard recharge token."
    ),
    "My meter rejected my token, is it a tariff issue?": (
        "Yes, this often happens if your meter needs a software update. Your utility must provide "
        "two 20-digit Key Change Tokens (KCTs) to enter before your regular token. Contact them to request it."
    ),
    "How do I check my remaining balance?": (
        "Try typing code 009 or 07 and pressing Enter. For Hexing meters, enter Q801. For Landis+Gyr, try 007!"
    ),
    "My keypad gives 'USED' when I load a token": (
        "This means the token was already successfully loaded in the past. "
        "Double-check your receipts to ensure you aren't re-entering an old token."
    ),
    "What does Error 30, E07, or Conn_Fail mean?": (
        "This is a communication error between the keypad and the main meter outside. "
        "Try plugging the keypad into a wall socket closer to the main meter, replace its batteries, "
        "or turn off interference-causing appliances."
    ),
    "What are codes 005 and 006 for?": (
        "It depends on the brand! On some meters, 005 checks the time, and 006 checks your live power usage. "
        "On others (like Conlog), they are 'Reserved for future use' and do nothing."
    ),
}


def build_faq_section() -> str:
    """Format FAQ into a string for the system prompt."""
    lines = ["## Frequently Asked Questions\n"]
    for q, a in ETIP_FAQ.items():
        lines.append(f"**Q: {q}**")
        lines.append(f"A: {a}\n")
    return "\n".join(lines)
