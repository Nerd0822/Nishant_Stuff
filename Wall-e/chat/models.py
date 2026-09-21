"""
Database models for the Wall-e chat application.

Uses SQLite (Django default) to persist conversations and messages.
"""
from django.db import models


class Conversation(models.Model):
    """A chat thread — a collection of messages between the user and Wall-e."""

    title = models.CharField(max_length=200, default="New chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name_plural = "conversations"

    def __str__(self) -> str:
        return self.title or "New chat"

    def save(self, *args, **kwargs) -> None:
        """Auto-generate a title from the first user message if still default."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            first = self.messages.first()
            if first and first.content:
                self.title = first.content[:50]
                if len(first.content) > 50:
                    self.title += "…"
                super().save(update_fields=["title"])


class Message(models.Model):
    """A single message in a conversation (user or assistant)."""

    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        preview = self.content[:60]
        if len(self.content) > 60:
            preview += "…"
        return f"[{self.role}] {preview}"
