"""Tests for the chat web views (HTML + HTMX)."""
from django.urls import reverse
from django.test import TestCase, override_settings
import os

from chat.models import Conversation, Message

_STATIC_ROOT = "/tmp/wall-e-test-static"
if not os.path.isdir(_STATIC_ROOT):
    os.makedirs(_STATIC_ROOT, exist_ok=True)


@override_settings(STATIC_ROOT=_STATIC_ROOT, ALLOWED_HOSTS=["*"])
class IndexViewTests(TestCase):
    """Tests for the index/conversation-list view."""

    def test_status_code(self):
        resp = self.client.get(reverse("chat:index"))
        self.assertEqual(resp.status_code, 200)

    def test_uses_template(self):
        resp = self.client.get(reverse("chat:index"))
        self.assertTemplateUsed("chat/index.html")

    def test_contains_new_message_link(self):
        resp = self.client.get(reverse("chat:index"))
        self.assertContains(resp, "New chat")


class ConversationListViewTests(TestCase):
    """The conversation list is served by the index view (same endpoint)."""

    def test_status_code(self):
        resp = self.client.get(reverse("chat:index"))
        self.assertEqual(resp.status_code, 200)

    def test_uses_template(self):
        resp = self.client.get(reverse("chat:index"))
        self.assertTemplateUsed("chat/index.html")

    def test_lists_conversations(self):
        Conversation.objects.create(title="First")
        Conversation.objects.create(title="Second")
        resp = self.client.get(reverse("chat:index"))
        self.assertContains(resp, "First")
        self.assertContains(resp, "Second")

    def test_empty_list_renders_fallback(self):
        resp = self.client.get(reverse("chat:index"))
        self.assertEqual(resp.status_code, 200)


class ChatViewTests(TestCase):
    """Tests for the single-conversation chat thread view."""

    def setUp(self):
        self.conv = Conversation.objects.create(title="Test chat")

    def test_status_code(self):
        resp = self.client.get(reverse("chat:chat_view", args=[self.conv.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_uses_template(self):
        resp = self.client.get(reverse("chat:chat_view", args=[self.conv.pk]))
        self.assertTemplateUsed("chat/chat.html")

    def test_submits_message_and_returns_200(self):
        data = {"message": "Hello assistant"}
        resp = self.client.post(
            reverse("chat:send_message", args=[self.conv.pk]),
            data=data,
            follow=False,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)

    def test_empty_message_rejected(self):
        data = {"message": ""}
        resp = self.client.post(
            reverse("chat:send_message", args=[self.conv.pk]),
            data=data,
            follow=False,
            HTTP_HX_REQUEST="true",
        )
        self.assertIn(resp.status_code, (302, 400))

    def test_whitespace_only_message_rejected(self):
        data = {"message": "   "}
        resp = self.client.post(
            reverse("chat:send_message", args=[self.conv.pk]),
            data=data,
            follow=False,
            HTTP_HX_REQUEST="true",
        )
        self.assertIn(resp.status_code, (302, 400))

    def test_message_is_persisted(self):
        before = Message.objects.count()
        self.client.post(
            reverse("chat:send_message", args=[self.conv.pk]),
            data={"message": "persisted?"},
            follow=True,
        )
        after = Message.objects.count()
        self.assertGreater(after, before)

    def test_conversation_missing_returns_404(self):
        resp = self.client.get(reverse("chat:chat_view", args=[9999]))
        self.assertEqual(resp.status_code, 404)

    def test_conversation_404_on_post(self):
        """POST to non-existent conversation also 404s."""
        resp = self.client.post(
            reverse("chat:send_message", args=[9999]),
            data={"message": "hi"},
            follow=False,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 404)

    def test_render_history_on_page(self):
        Message.objects.create(
            conversation=self.conv, role=Message.ROLE_USER, content="user msg"
        )
        Message.objects.create(
            conversation=self.conv,
            role=Message.ROLE_ASSISTANT,
            content="assistant reply",
        )
        resp = self.client.get(reverse("chat:chat_view", args=[self.conv.pk]))
        self.assertContains(resp, "user msg")
        self.assertContains(resp, "assistant reply")


class SendHtmxEndpointTests(TestCase):
    """The send_message view also serves HTMX partial updates."""

    def test_htmx_send_returns_200(self):
        conv = Conversation.objects.create(title="htmx test")
        resp = self.client.post(
            reverse("chat:send_message", args=[conv.pk]),
            data={"message": "hi"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)

    def test_htmx_send_with_empty_message_status(self):
        conv = Conversation.objects.create(title="htmx2")
        resp = self.client.post(
            reverse("chat:send_message", args=[conv.pk]),
            data={"message": ""},
            HTTP_HX_REQUEST="true",
        )
        self.assertIn(resp.status_code, (302, 400))

    def test_htmx_send_missing_conversation_404(self):
        resp = self.client.post(
            reverse("chat:send_message", args=[9999]),
            data={"message": "hi"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 404)

    def test_htmx_send_creates_message(self):
        conv = Conversation.objects.create(title="create test")
        before = Message.objects.count()
        self.client.post(
            reverse("chat:send_message", args=[conv.pk]),
            data={"message": "new message"},
            HTTP_HX_REQUEST="true",
            follow=True,
        )
        self.assertGreater(Message.objects.count(), before)
