"""
REST API views for the Wall-e chat application.

Built with Django REST Framework (DRF).  Provides full CRUD for
conversations and messages, plus a dedicated endpoint for sending
a message and receiving the AI reply.
"""

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .agent import get_response
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


class ConversationListCreateAPIView(generics.ListCreateAPIView):
    """List all conversations or create a new one."""

    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer


class ConversationDetailAPIView(generics.RetrieveDestroyAPIView):
    """Retrieve or delete a single conversation."""

    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer


class ConversationMessagesAPIView(generics.ListCreateAPIView):
    """List or create messages within a conversation."""

    serializer_class = MessageSerializer

    def get_queryset(self):
        return Message.objects.filter(conversation_id=self.kwargs["pk"]).order_by("created_at")

    def perform_create(self, serializer):
        conversation = get_object_or_404(Conversation, pk=self.kwargs["pk"])
        serializer.save(conversation=conversation)


class SendMessageAPIView(APIView):
    """Send a user message to the Wall-e agent and return the AI reply.

    POST body: ``{"message": "your text here"}``
    Response:  ``{"response": "AI reply text"}``
    """

    def post(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        user_message = request.data.get("message", "").strip()

        if not user_message:
            return Response({"error": "No message provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Save the user message
        Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_USER,
            content=user_message,
        )

        # Load history
        prev_messages = list(
            conversation.messages.filter(role__in=["user", "assistant"])
            .values("role", "content")
            .order_by("created_at")
        )

        # Get AI response
        try:
            ai_reply = get_response(user_message, prev_messages)
        except Exception as exc:  # noqa: BLE001
            ai_reply = f"Sorry, something went wrong: {type(exc).__name__}: {exc}"

        # Save the AI response
        Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_ASSISTANT,
            content=ai_reply,
        )

        return Response({"response": ai_reply})