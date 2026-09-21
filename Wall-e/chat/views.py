"""
Web views for the Wall-e chat application.

These views power the ChatGPT-like UI:
- ``index``     — conversation list / landing page
- ``chat_view`` — conversation thread with messages
- ``new_chat``  — create a fresh conversation
- ``send_message`` — accept a user message, call the agent, return the AI reply
- ``delete_chat``  — remove a conversation
"""

from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .agent import get_response
from .models import Conversation, Message


@ensure_csrf_cookie
def index(request):
    """Landing page — show the conversation sidebar and a welcome screen."""
    conversations = Conversation.objects.all()
    return render(request, "chat/index.html", {"conversations": conversations})


@ensure_csrf_cookie
def chat_view(request, pk):
    """Display a single conversation thread with its messages."""
    conversation = get_object_or_404(Conversation, pk=pk)
    messages = conversation.messages.all()
    conversations = Conversation.objects.all()
    context = {
        "conversation": conversation,
        "messages": messages,
        "conversations": conversations,
    }
    return render(request, "chat/chat.html", context)


def new_chat(request):
    """Create a new empty conversation and redirect to its chat page."""
    conversation = Conversation.objects.create(title="New chat")
    return redirect("chat:chat_view", pk=conversation.pk)


@require_POST
def send_message(request, pk):
    """Accept a user message, run it through the agent, and return the reply.

    Supports both regular POST (redirect) and HTMX partial updates.
    """
    conversation = get_object_or_404(Conversation, pk=pk)

    # Read the user's message
    raw = request.POST.get("message", "").strip()
    if not raw:
        return HttpResponseBadRequest("No message provided")

    # Persist the user message
    Message.objects.create(conversation=conversation, role=Message.ROLE_USER, content=raw)

    # Load the conversation history as plain dicts for the agent
    prev_messages = list(
        conversation.messages.filter(role__in=["user", "assistant"])
        .values("role", "content")
        .order_by("created_at")
    )

    # Auto-generate a conversation title from the first user message
    if conversation.title == "New chat":
        conversation.title = raw[:50] + ("…" if len(raw) > 50 else "")
        conversation.save(update_fields=["title"])

    # Call the Wall-e agent
    try:
        ai_reply = get_response(raw, prev_messages)
    except Exception as exc:  # noqa: BLE001
        ai_reply = f"Sorry, something went wrong: {type(exc).__name__}: {exc}"

    # Persist the assistant's reply
    Message.objects.create(
        conversation=conversation,
        role=Message.ROLE_ASSISTANT,
        content=ai_reply,
    )

    # Update the conversation's updated_at timestamp
    conversation.save(update_fields=["updated_at"])

    # Respond appropriately based on the request type
    if request.headers.get("HX-Request") == "true":
        # HTMX partial — return just the assistant message HTML
        return render(request, "chat/_assistant_message.html", {"content": ai_reply})

    return JsonResponse({"response": ai_reply})


@require_POST
def delete_chat(request, pk):
    """Delete a conversation and redirect to the index."""
    conversation = get_object_or_404(Conversation, pk=pk)
    conversation.delete()
    return redirect("chat:index")
