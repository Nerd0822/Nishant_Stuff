"""Background tasks for Raahi. Slow work (LLM, web research) runs here so
views can return instantly and the browser polls for results."""

from celery import shared_task

from .helper import ask_ollama_sync, fetch_place_summary_sync


@shared_task(bind=True, max_retries=0, time_limit=660)
def chat_with_ollama(self, question: str, place_name: str = "") -> dict:
    """Ask the local Ollama model. Returns {"reply": ...} or {"error": ...}."""
    try:
        context = f"The user is looking at {place_name} on the map." if place_name else ""
        reply = ask_ollama_sync(question, context=context)
        return {"reply": reply, "place": place_name}
    except Exception as exc:
        return {"error": f"Ollama failed: {exc}"}


@shared_task(bind=True, max_retries=0, time_limit=660)
def build_itinerary(self, place_name: str) -> dict:
    """Research a place (Wikipedia/DDG) then ask Ollama for an itinerary.

    Returns {"itinerary": ..., "facts": ..., "source": ...} or {"error": ...}.
    """
    try:
        facts = fetch_place_summary_sync(place_name)
        context = facts["text"] or f"No background information found for {place_name}."
        prompt = (
            f"Plan a short 1-day itinerary for a road trip to {place_name}. "
            "Keep it to 3-4 stops with one line each."
        )
        itinerary = ask_ollama_sync(prompt, context=context)
        return {"itinerary": itinerary, "facts": facts["text"], "source": facts["source"]}
    except Exception as exc:
        return {"error": f"Itinerary failed: {exc}"}
