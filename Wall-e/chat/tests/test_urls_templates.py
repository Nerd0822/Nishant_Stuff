"""Tests for URL resolution and template rendering.

URL names (from chat/urls.py):
    chat:index          -> /chat/
    chat:new_chat       -> /chat/new/
    chat:chat_view      -> /chat/<int:pk>/
    chat:send_message   -> /chat/<int:pk>/send/
    chat:delete_chat    -> /chat/<int:pk>/delete/
"""
from django.urls import reverse, resolve
from django.test import TestCase, override_settings
import os

from chat.models import Conversation

_STATIC_ROOT = "/tmp/wall-e-test-static-2"
if not os.path.isdir(_STATIC_ROOT):
    os.makedirs(_STATIC_ROOT, exist_ok=True)


@override_settings(STATIC_ROOT=_STATIC_ROOT, ALLOWED_HOSTS=["*"])
class ChatUrlResolutionTests(TestCase):
    def test_index_url_resolves(self):
        url = reverse("chat:index")
        self.assertEqual(url, "/chat/")

    def test_new_chat_url_resolves(self):
        url = reverse("chat:new_chat")
        self.assertEqual(url, "/chat/new/")

    def test_chat_view_url_resolves_with_pk(self):
        url = reverse("chat:chat_view", args=[123])
        self.assertEqual(url, "/chat/123/")

    def test_send_message_url_resolves_with_pk(self):
        url = reverse("chat:send_message", args=[123])
        self.assertEqual(url, "/chat/123/send/")

    def test_delete_chat_url_resolves_with_pk(self):
        url = reverse("chat:delete_chat", args=[123])
        self.assertEqual(url, "/chat/123/delete/")

    def test_chat_view_resolver_name(self):
        func, args, kwargs = resolve("/chat/42/")
        self.assertEqual(kwargs["pk"], "42")
        self.assertTrue(func.view_name.startswith("chat:"))

    def test_send_message_view_resolver_name(self):
        func, args, kwargs = resolve("/chat/7/send/")
        self.assertEqual(kwargs["pk"], "7")
        self.assertTrue(func.view_name.startswith("chat:"))


class TemplateRenderingTests(TestCase):
    def test_index_template_renders(self):
        resp = self.client.get("/chat/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed("base.html")
        self.assertTemplateUsed("chat/index.html")

    def test_chat_template_renders_with_conversation(self):
        conv = Conversation.objects.create(title="template test")
        resp = self.client.get(reverse("chat:chat_view", args=[conv.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed("chat/chat.html")
        self.assertContains(resp, conv.title)

    def test_chat_template_footer_has_copyright_year(self):
        resp = self.client.get("/chat/")
        self.assertContains(resp, "2026")
