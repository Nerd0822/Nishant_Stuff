"""Tests for the DRF API views.

API URLs:
    api_conversation_list       /api/conversations/
    api_conversation_detail     /api/conversations/<int:pk>/
    api_conversation_messages   /api/conversations/<int:pk>/messages/
    api_send_message            /api/conversations/<int:pk>/send/
"""
from rest_framework.test import APITestCase

from chat.models import Conversation, Message


class ConversationListCreateTests(APITestCase):
    def test_list_status_code(self):
        resp = self.client.get("/api/conversations/")
        self.assertEqual(resp.status_code, 200)

    def test_create_conversation_status(self):
        resp = self.client.post("/api/conversations/", {"title": "API chat"})
        self.assertEqual(resp.status_code, 201)

    def test_create_returns_id_and_title(self):
        resp = self.client.post("/api/conversations/", {"title": "API chat"})
        self.assertIn("id", resp.data)
        assert resp.data["title"] == "API chat"

    def test_create_with_empty_title_uses_default(self):
        resp = self.client.post("/api/conversations/", {"title": ""})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["title"], "New chat")

    def test_create_with_no_title_uses_default(self):
        resp = self.client.post("/api/conversations/", {})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["title"], "New chat")

    def test_create_invalid_json_returns_400(self):
        resp = self.client.post(
            "/api/conversations/", b"not json",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_crud_round_trip(self):
        resp = self.client.post("/api/conversations/", {"title": "CRUD"})
        conv_id = resp.data["id"]
        detail_resp = self.client.get(f"/api/conversations/{conv_id}/")
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.data["title"], "CRUD")


class ConversationDetailTests(APITestCase):
    def test_retrieve_returns_404_for_missing(self):
        resp = self.client.get("/api/conversations/99999/")
        self.assertEqual(resp.status_code, 404)

    def test_list_returns_empty_when_no_conversations(self):
        resp = self.client.get("/api/conversations/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, [])

    def test_delete_returns_404_for_missing(self):
        resp = self.client.delete("/api/conversations/99999/")
        self.assertEqual(resp.status_code, 404)

    def test_delete_removes_conversation(self):
        conv = Conversation.objects.create(title="to delete")
        resp = self.client.delete(f"/api/conversations/{conv.pk}/")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Conversation.objects.filter(pk=conv.pk).exists())


class SendMessageApiTests(APITestCase):
    def test_send_returns_200(self):
        conv = Conversation.objects.create(title="send test")
        resp = self.client.post(
            f"/api/conversations/{conv.pk}/send/",
            {"message": "hello"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("response", resp.data)

    def test_send_returns_helpful_error_message_for_empty_input(self):
        conv = Conversation.objects.create(title="empty test")
        resp = self.client.post(
            f"/api/conversations/{conv.pk}/send/",
            {"message": ""},
        )
        self.assertTrue(("message" in resp.data) or ("error" in resp.data))

    def test_send_missing_conversation_returns_404(self):
        resp = self.client.post(
            "/api/conversations/99999/send/",
            {"message": "hi"},
        )
        self.assertEqual(resp.status_code, 404)

    def test_send_creates_messages_in_db(self):
        conv = Conversation.objects.create(title="db test")
        before = Message.objects.count()
        self.client.post(
            f"/api/conversations/{conv.pk}/send/",
            {"message": "msg"},
        )
        after = Message.objects.count()
        self.assertGreater(after, before)

    def test_send_with_whitespace_only_input_status(self):
        conv = Conversation.objects.create(title="ws test")
        resp = self.client.post(
            f"/api/conversations/{conv.pk}/send/",
            {"message": "   "},
        )
        self.assertIn(resp.status_code, (400, 404))

    def test_send_missing_message_field_status(self):
        conv = Conversation.objects.create(title="missing field")
        resp = self.client.post(
            f"/api/conversations/{conv.pk}/send/",
            {},
        )
        self.assertIn(resp.status_code, (400, 404))


class MessagesApiTests(APITestCase):
    """Tests for the /messages/ sub-resource endpoint."""

    def test_list_messages_empty(self):
        conv = Conversation.objects.create(title="msgs test")
        resp = self.client.get(f"/api/conversations/{conv.pk}/messages/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, [])

    def test_list_messages_after_create(self):
        conv = Conversation.objects.create(title="msgs test2")
        Message.objects.create(
            conversation=conv, role=Message.ROLE_USER, content="hi 1"
        )
        Message.objects.create(
            conversation=conv, role=Message.ROLE_ASSISTANT, content="hello 1"
        )
        resp = self.client.get(f"/api/conversations/{conv.pk}/messages/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)

    def test_create_message_via_api(self):
        conv = Conversation.objects.create(title="msgs test3")
        resp = self.client.post(
            f"/api/conversations/{conv.pk}/messages/",
            {"role": "user", "content": "api msg"},
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["role"], "user")
        self.assertEqual(resp.data["content"], "api msg")

    def test_create_message_requires_conversation(self):
        resp = self.client.post(
            "/api/conversations/99999/messages/",
            {"role": "user", "content": "orphan"},
        )
        self.assertEqual(resp.status_code, 404)
