"""
chat — AI conversation persistence.
One active conversation per user. Messages have role (user / assistant / system).
"""
import uuid

from django.conf import settings
from django.db import models


class MessageRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"
    SYSTEM = "system", "System"


class Conversation(models.Model):
    """
    A single chat thread per user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_conversation",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_conversations"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Chat:{self.user} ({self.messages.count()} msgs)"


class Message(models.Model):
    """
    A single message in a conversation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=MessageRole.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self):
        preview = self.content[:60] + ("..." if len(self.content) > 60 else "")
        return f"[{self.role}] {preview}"
