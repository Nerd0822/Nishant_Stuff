from celery import shared_task
from home.helper import chatbot
from django.core.mail import send_mail
import os
import requests
import json


@shared_task(bind=True)
def chat_with_gemini(self, message):
    """Run Gemini chat in background. Returns the response text."""
    response = chatbot.generate(prompt=message)
    return response


@shared_task(bind=True)
def search_hotels(self, lat, lon, place_name=""):
    """Search hotels via SerpAPI in background."""
    api_key = os.getenv("serpAPI")
    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={
                "engine": "google_hotels",
                "api_key": api_key,
                "lat": lat,
                "lng": lon,
                "hl": "en",
                "gl": "us",
            },
            timeout=10,
        )
        data = resp.json()
        properties = data.get("properties", [])
        hotels = []
        for p in properties:
            hotels.append(
                {
                    "title": p.get("name", "Hotel"),
                    "address": p.get("address", ""),
                    "rating": p.get("rating", "N/A"),
                    "reviews": p.get("reviews", 0),
                    "price": p.get("total_rate", {}).get(
                        "extracted_before_fees", "$ N/A"
                    ),
                    "thumbnail": (
                        (p.get("images") or [{}])[0].get("thumbnail", "")
                        if p.get("images")
                        else ""
                    ),
                }
            )
        return hotels
    except Exception as e:
        return {"error": str(e)}


@shared_task(bind=True)
def send_support_email(self, name, email, subject, message):
    """Send support email in background."""
    full_message = f"From: {name} <{email}>\n\n{message}"
    try:
        send_mail(
            subject=f"[Raahi Support] {subject}",
            message=full_message,
            from_email=email,
            recipient_list=[str(os.environ.get("dev_mail"))],
            fail_silently=False,
        )
        return {"success": "Message sent successfully!"}
    except Exception as e:
        return {"error": f"Failed to send: {str(e)}"}
