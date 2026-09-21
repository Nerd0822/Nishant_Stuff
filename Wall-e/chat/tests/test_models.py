"""
Tests for the Conversation and Message database models.

Covers creation, defaults, __str__ output, ordering, role validation,
cascade deletion, and edge cases (long titles/contents, unicode).
"""
from django.db import IntegrityError
from django.test import TestCase

from chat.models import Conversation, Message


class ConversationModelTest(TestCase):
    """Tests for the Conversation model."""

    def test_create_conversation_with_default_title(self):
        conv = Conversation.objects.create()
        self.assertEqual(conv.title, "New chat")
        self.assertIsNotNone(conv.pk)

    def test_create_conversation_with_custom_title(self):
        conv = Conversation.objects.create(title="My project discussion")
        self.assertEqual(conv.title, "My project discussion")

    def test_str_returns_title(self):
        conv = Conversation.objects.create(title="Hello world")
        self.assertEqual(str(conv), "Hello world")

    def test_created_at_and_updated_at_set_automatically(self):
        conv = Conversation.objects.create()
        self.assertIsNotNone(conv.created_at)
        self.assertIsNotNone(conv.updated_at)

    def test_updated_at_changes_on_save(self):
        conv = Conversation.objects.create(title="before")
        original_updated = conv.updated_at
        conv.title = "after"
        conv.save()
        conv.refresh_from_db()
        self.assertEqual(conv.title, "after")
        self.assertGreaterEqual(conv.updated_at, original_updated)

    def test_save_does_not_overwrite_custom_title(self):
        """A conversation with a non-default title keeps it after re-saving."""
        conv = Conversation.objects.create(title="Custom")
        conv.save()
        conv.refresh_from_db()
        self.assertEqual(conv.title, "Custom")

    def test_save_does_not_regenerate_title_when_messages_exist_later(self):
        """Title auto-generation only runs on the very first save."""
        conv = Conversation.objects.create(title="New chat")
        Message.objects.create(
            conversation=conv, role=Message.ROLE_USER, content="First message!"
        )
        conv.save()
        conv.refresh_from_db()
        # title unchanged because is_new was False on this save
        self.assertEqual(conv.title, "New chat")

    def test_ordering_most_recently_updated_first(self):
        c1 = Conversation.objects.create(title="old")
        c2 = Conversation.objects.create(title="middle")
        c3 = Conversation.objects.create(title="newest")
        # touch c1 so it becomes the most recently updated
        c1.title = "old (updated)"
        c1.save()
        titles = list(Conversation.objects.values_list("title", flat=True))
        self.assertEqual(titles[0], "old (updated)")

    def test_unicode_title_is_preserved(self):
        conv = Conversation.objects.create(title="résumé — 日本語 chat")
        conv.refresh_from_db()
        self.assertEqual(conv.title, "résumé — 日本語 chat")

    def test_cascade_delete_removes_messages(self):
        conv = Conversation.objects.create(title="doomed")
        Message.objects.create(conversation=conv, role=Message.ROLE_USER, content="hi")
        Message.objects.create(
            conversation=conv, role=Message.ROLE_ASSISTANT, content="hello"
        )
        self.assertEqual(conv.messages.count(), 2)
        conv.delete()
        self.assertEqual(Message.objects.count(), 0)


class ConversationMessageRelationTest(TestCase):
    """Tests for the Conversation <-> Message relationship."""

    def setUp(self):
        self.c = Conversation.objects.create(title="rel")

    def test_related_name(self):
        Message.objects.create(conversation=self.c, role=Message.ROLE_USER, content="a")
        self.assertEqual(self.c.messages.count(), 1)

    def test_count_via_reverse(self):
        for i in range(3):
            Message.objects.create(conversation=self.c, role=Message.ROLE_USER, content=f"m{i}")
        self.assertEqual(self.c.messages.count(), 3)

    def test_orphan_message_rejected(self):
        with self.assertRaises(IntegrityError):
            Message.objects.create(role=Message.ROLE_USER, content="orphan")

    def test_messages_ordered_by_created_at(self):
        m1 = Message.objects.create(conversation=self.c, role=Message.ROLE_USER, content="first")
        m2 = Message.objects.create(conversation=self.c, role=Message.ROLE_ASSISTANT, content="second")
        self.assertEqual(list(self.c.messages.all()), [m1, m2])


class MessageModelTest(TestCase):
    """Tests for the Message model."""

    def setUp(self):
        self.c = Conversation.objects.create(title="msg tests")

    def make(self, role=Message.ROLE_USER, content="hello"):
        return Message.objects.create(conversation=self.c, role=role, content=content)

    def test_user_message(self):
        m = self.make()
        self.assertEqual(m.role, "user")
        self.assertEqual(m.content, "hello")
        self.assertEqual(m.conversation, self.c)

    def test_assistant_message(self):
        m = self.make(role=Message.ROLE_ASSISTANT)
        self.assertEqual(m.role, "assistant")

    def test_role_choices(self):
        self.assertEqual(Message.ROLE_CHOICES, [("user", "User"), ("assistant", "Assistant")])

    def test_str_short(self):
        m = self.make(content="short")
        self.assertEqual(str(m), "[user] short")

    def test_str_truncated_with_ellipsis(self):
        m = self.make(content="x" * 100)
        self.assertEqual(str(m), f"[user] {'x' * 60}\u2026")

    def test_str_exactly_60_not_truncated(self):
        m = self.make(content="y" * 60)
        self.assertEqual(str(m), f"[user] {'y' * 60}")

    def test_str_61_truncated(self):
        m = self.make(content="y" * 61)
        self.assertEqual(str(m), f"[user] {'y' * 60}\u2026")

    def test_created_at_set(self):
        m = self.make()
        self.assertIsNotNone(m.created_at)

    def test_empty_content_allowed(self):
        m = self.make(content="")
        m.refresh_from_db()
        self.assertEqual(m.content, "")

    def test_unicode_content(self):
        m = self.make(content="héllo 🤖 日本語")
        m.refresh_from_db()
        self.assertEqual(m.content, "héllo 🤖 日本語")

    def test_large_content(self):
        m = self.make(content="z" * 100_000)
        m.refresh_from_db()
        self.assertEqual(len(m.content), 100_000)

    def test_role_values(self):
        self.assertEqual(Message.ROLE_USER, "user")
        self.assertEqual(Message.ROLE_ASSISTANT, "assistant")

    def test_invalid_role_rejected(self):
        m = Message(conversation=self.c, role="other", content="x")
        with self.assertRaises(Exception):
            m.full_clean()

    def test_cascade_delete_removes_message(self):
        m = self.make(content="del me")
        pk = m.pk
        self.c.delete()
        self.assertFalse(Message.objects.filter(pk=pk).exists())

