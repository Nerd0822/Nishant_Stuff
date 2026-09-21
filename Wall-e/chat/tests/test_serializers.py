"""Tests for the chat serializers."""
from chat.serializers import ConversationSerializer, MessageSerializer


class ConversationSerializerTests:
    """Tests for ConversationSerializer."""

    def test_fields_are_id_title_message_count_created_at_updated_at(self):
        assert set(ConversationSerializer.Meta.fields) == {
            "id",
            "title",
            "message_count",
            "created_at",
            "updated_at",
        }

    def test_message_count_is_not_in_writable_fields(self):
        serializer = ConversationSerializer()
        writable = set(serializer.fields.keys())
        assert "message_count" not in writable
        assert "id" not in writable

    def test_message_count_returns_zero_for_empty_conversation(self):
        from chat.models import Conversation
        conv = Conversation.objects.create(title="empty")
        data = ConversationSerializer(instance=conv).data
        assert data["message_count"] == 0

    def test_message_count_returns_correct_count(self):
        from chat.models import Conversation, Message
        conv = Conversation.objects.create(title="c")
        Message.objects.create(conversation=conv, role=Message.ROLE_USER, content="a")
        Message.objects.create(conversation=conv, role=Message.ROLE_ASSISTANT, content="b")
        data = ConversationSerializer(instance=conv).data
        assert data["message_count"] == 2

    def test_output_keys_are_correct(self):
        from chat.models import Conversation
        conv = Conversation.objects.create(title="t")
        data = ConversationSerializer(instance=conv).data
        assert set(data.keys()) == {"id", "title", "message_count", "created_at", "updated_at"}

    def test_str_fields(self):
        from chat.models import Conversation
        conv = Conversation.objects.create(title="hi")
        s = ConversationSerializer(instance=conv)
        assert s.data["title"] == "hi"


class MessageSerializerTests:
    """Tests for MessageSerializer."""

    def test_fields_are_id_role_content_conversation_created_at(self):
        assert set(MessageSerializer.Meta.fields) == {
            "id", "role", "content", "conversation", "created_at",
        }

    def test_conversation_is_read_only(self):
        from chat.models import Conversation, Message
        conv = Conversation.objects.create(title="c")
        msg = Message.objects.create(conversation=conv, role=Message.ROLE_USER, content="hi")
        data = MessageSerializer(instance=msg).data
        assert "conversation" in data
        assert data["conversation"] == conv.pk

    def test_role_is_valid_string(self):
        from chat.models import Conversation
        conv = Conversation.objects.create(title="c")
        data = MessageSerializer(instance=Message.objects.create(
            conversation=conv, role=Message.ROLE_USER, content="hi")).data
        assert data["role"] == "user"

    def test_output_keys_are_correct(self):
        from chat.models import Conversation, Message
        conv = Conversation.objects.create(title="c")
        msg = Message.objects.create(conversation=conv, role=Message.ROLE_ASSISTANT, content="resp")
        data = MessageSerializer(instance=msg).data
        assert set(data.keys()) == {"id", "role", "content", "conversation", "created_at"}
