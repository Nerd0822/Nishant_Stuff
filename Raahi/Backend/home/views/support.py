from django.shortcuts import render
from django.http import JsonResponse
import json
from home.tasks import send_support_email as send_support_email_task


def support_page(request):
    return render(request, "support.html")


def send_support_email(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    subject = data.get("subject", "").strip()
    message = data.get("message", "").strip()

    if not all([name, email, subject, message]):
        return JsonResponse({"error": "All fields are required."}, status=400)

    # Send email via Celery worker in background
    task = send_support_email_task.delay(name, email, subject, message)
    result = task.get(timeout=30)

    if "error" in result:
        return JsonResponse({"error": result["error"]}, status=500)
    return JsonResponse({"success": "Message sent successfully!"})
