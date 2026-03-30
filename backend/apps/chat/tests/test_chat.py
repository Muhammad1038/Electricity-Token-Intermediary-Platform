"""
chat — Tests for Conversation/Message models, ChatService, and API views.
"""
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from apps.chat.knowledge import ETIP_FAQ, build_faq_section
from apps.chat.models import Conversation, Message
from conftest import UserFactory


@pytest.mark.django_db
class TestChatModels:
    def test_conversation_one_per_user(self, user):
        conv = Conversation.objects.create(user=user)
        assert Conversation.objects.filter(user=user).count() == 1
        assert str(conv).startswith("Chat:")

    def test_message_ordering(self, user):
        conv = Conversation.objects.create(user=user)
        m1 = Message.objects.create(conversation=conv, role="user", content="Hello")
        m2 = Message.objects.create(conversation=conv, role="assistant", content="Hi!")
        msgs = list(conv.messages.all())
        assert msgs[0] == m1
        assert msgs[1] == m2


class TestKnowledge:
    def test_faq_not_empty(self):
        assert len(ETIP_FAQ) > 0

    def test_build_faq_section(self):
        section = build_faq_section()
        assert "Frequently Asked Questions" in section
        assert "ETIP" in section


@pytest.mark.django_db
class TestChatViews:
    @patch("apps.chat.views.ChatService")
    def test_send_message(self, MockService, auth_client, user):
        mock_instance = MockService.return_value
        mock_instance.get_reply.return_value = "I can help you with that!"

        resp = auth_client.post(
            reverse("chat-send"),
            {"message": "What DISCOs do you support?"},
            format="json",
        )
        assert resp.status_code == 200
        assert "assistant_message" in resp.data
        assert "user_message" in resp.data
        # Both messages should be saved
        assert Message.objects.filter(
            conversation__user=user, role="user"
        ).count() == 1
        assert Message.objects.filter(
            conversation__user=user, role="assistant"
        ).count() == 1

    @patch("apps.chat.views.ChatService")
    def test_chat_history(self, MockService, auth_client, user):
        # Create a conversation with messages
        conv = Conversation.objects.create(user=user)
        Message.objects.create(conversation=conv, role="user", content="Hi")
        Message.objects.create(conversation=conv, role="assistant", content="Hello!")

        resp = auth_client.get(reverse("chat-history"))
        assert resp.status_code == 200

    def test_clear_chat(self, auth_client, user):
        conv = Conversation.objects.create(user=user)
        Message.objects.create(conversation=conv, role="user", content="Hi")
        Message.objects.create(conversation=conv, role="assistant", content="Hello!")

        resp = auth_client.delete(reverse("chat-clear"))
        assert resp.status_code == 200
        assert conv.messages.count() == 0

    def test_send_message_unauthenticated(self, api_client):
        resp = api_client.post(
            reverse("chat-send"),
            {"message": "Hello"},
            format="json",
        )
        assert resp.status_code == 401
