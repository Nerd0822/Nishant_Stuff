"""
DRF serializers for the Wall-e chat models.
"""
from rest_framework import serializers

from .models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    """Serialize a Conversation (title + timestamps)."""

    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "updated_at", "message_count"]
        read_only_fields = ["id", "created_at", "updated_at"]

    @staticmethod
    def get_message_count(obj: Conversation) -> int:
        return obj.messages.count()


class MessageSerializer(serializers.ModelSerializer):
    """Serialize a Message (role + content + timestamps)."""

    class Meta:
        model = Message
        fields = ["id", "conversation", "role", "content", "created_at"]
        read_only_fields = ["id", "created_at", "conversation"]