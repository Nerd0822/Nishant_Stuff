"""
Admin registration for the Wall-e chat models.
"""
from django.contrib import admin

from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "updated_at", "message_count")
    search_fields = ("title",)
    date_hierarchy = "created_at"

    @admin.display(description="Messages")
    def message_count(self, obj: Conversation) -> int:
        return obj.messages.count()


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "role", "conversation", "content_preview")
    list_filter = ("role", "conversation")
    search_fields = ("content",)
    date_hierarchy = "created_at"
    raw_id_fields = ("conversation",)

    @admin.display(description="Content", ordering="content")
    def content_preview(self, obj: Message) -> str:
        return (obj.content[:80] + "…") if len(obj.content) > 80 else obj.content
