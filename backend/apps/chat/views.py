"""
chat.views — API endpoints for the AI chat assistant.
"""
import logging

from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.pagination import StandardResultsPagination
from .models import Conversation, Message
from .serializers import MessageSerializer, SendMessageSerializer
from .services import ChatService

logger = logging.getLogger(__name__)


class SendMessageView(APIView):
    """
    POST /api/v1/chat/send/
    Send a message and receive an AI reply.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_text = serializer.validated_data["message"]

        # Get or create conversation for this user
        conversation, _ = Conversation.objects.get_or_create(user=request.user)

        # Save user message
        user_msg = Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_text,
        )

        # Get AI reply
        try:
            service = ChatService(user=request.user, conversation=conversation)
            reply_text = service.get_reply(user_text)
        except Exception as e:
            logger.exception("ChatService error for user %s: %s", request.user.id, e)
            reply_text = (
                "I'm having trouble connecting right now. "
                "Please try again in a moment, or contact support at support@etip.ng."
            )

        # Save assistant message
        assistant_msg = Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=reply_text,
        )

        # Touch conversation updated_at
        conversation.save(update_fields=["updated_at"])

        return Response(
            {
                "user_message": MessageSerializer(user_msg).data,
                "assistant_message": MessageSerializer(assistant_msg).data,
            },
            status=status.HTTP_200_OK,
        )


class ChatHistoryView(ListAPIView):
    """
    GET /api/v1/chat/history/
    Returns paginated message history (oldest first).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        conversation = Conversation.objects.filter(user=self.request.user).first()
        if not conversation:
            return Message.objects.none()
        return conversation.messages.order_by("created_at")


class ClearChatView(APIView):
    """
    DELETE /api/v1/chat/clear/
    Delete all messages for the current user's conversation.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        conversation = Conversation.objects.filter(user=request.user).first()
        if conversation:
            count, _ = conversation.messages.all().delete()
            logger.info("Cleared %d chat messages for user %s", count, request.user.id)
        return Response({"detail": "Chat history cleared."}, status=status.HTTP_200_OK)
