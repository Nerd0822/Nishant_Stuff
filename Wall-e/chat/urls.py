"""
URL routes for the Wall-e chat app.

Provides both web UI views (HTMX-friendly) and a DRF REST API.
"""
from django.urls import path

from . import views
from . import api_views

app_name = "chat"

urlpatterns = [
    # --- Web UI ----------------------------------------------------------
    path("", views.index, name="index"),
    path("new/", views.new_chat, name="new_chat"),
    path("chat/<int:pk>/", views.chat_view, name="chat_view"),
    path("chat/<int:pk>/send/", views.send_message, name="send_message"),
    path("chat/<int:pk>/delete/", views.delete_chat, name="delete_chat"),
    # --- API -------------------------------------------------------------
    path("api/conversations/", api_views.ConversationListCreateAPIView.as_view(), name="api_conversation_list"),
    path("api/conversations/<int:pk>/", api_views.ConversationDetailAPIView.as_view(), name="api_conversation_detail"),
    path("api/conversations/<int:pk>/messages/", api_views.ConversationMessagesAPIView.as_view(), name="api_conversation_messages"),
    path("api/conversations/<int:pk>/send/", api_views.SendMessageAPIView.as_view(), name="api_send_message"),
]