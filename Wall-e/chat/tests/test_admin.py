"""Tests for the Django admin registration."""
from django.contrib import admin
from django.test import TestCase
from chat.models import Conversation, Message


class AdminSmokeTests(TestCase):
    """Minimal admin registration checks. Full admin UI tests are rare."""

    def test_conversation_registered(self):
        self.assertIsNotNone(admin.site._registry.get(Conversation))

    def test_message_registered(self):
        self.assertIsNotNone(admin.site._registry.get(Message))

