from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from celery.result import AsyncResult
import json
from dotenv import load_dotenv
from home.tasks import chat_with_gemini, search_hotels as search_hotels_task
from home.models import ChatHistory, SavedPlace

load_dotenv()


@login_required
def set_place(request):
    if request.method == "POST":
        if request.htmx:
            place = request.POST.get("place", "")
        else:
            data = json.loads(request.body)
            place = data.get("place", "")
            request.session["lat"] = data.get("lat", "")
            request.session["lon"] = data.get("lon", "")
        request.session["place"] = place
        if request.htmx:
            html = f'<i class="fa-solid fa-calendar-plus"></i> {"Discover in " + place if place else "Generate Smart Itinerary Plan"}'
            return HttpResponse(
                f'<button class="btn-plan-itinerary" id="discoverBtn">{html}</button>'
            )
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "only post"}, status=405)


@login_required
def get_place(request):
    if request.method == "GET":
        return JsonResponse({"place": request.session.get("place", "")})
    return JsonResponse({"error": "only get allowed"})


@login_required
def chat(request):
    if request.method == "POST":
        if request.htmx:
            message = request.POST.get("message", "")
        else:
            data = json.loads(request.body)
            message = data.get("message", "")

        # Run Gemini in Celery worker and wait for result
        task: AsyncResult = chat_with_gemini.delay(message)  # type: ignore
        reply = task.get(timeout=60)  # Wait up to 60s for the worker

        ChatHistory.objects.create(user=request.user, message=message, response=reply)

        if request.htmx:
            user_html = render_to_string(
                "_fragments/user_bubble.html", {"message": message}
            )
            bot_html = render_to_string("_fragments/bot_bubble.html", {"reply": reply})
            return HttpResponse(user_html + bot_html)
        return JsonResponse({"reply": reply})
    return JsonResponse({"reply": "this method is not allowed"})


@login_required
def search_hotels(request):
    if request.method == "POST":
        body = json.loads(request.body)
        lat = body.get("lat")
        lon = body.get("lon")
        place_name = body.get("place", "")
    else:
        lat = request.GET.get("lat")
        lon = request.GET.get("lon")
        place_name = request.GET.get("place", "")

    if not lat or not lon:
        return JsonResponse({"error": "lat and lon required"}, status=400)

    # Run SerpAPI search in Celery worker and wait for result
    task = search_hotels_task.delay(lat, lon, place_name)
    result = task.get(timeout=30)  # Wait up to 30s for the worker

    if isinstance(result, dict) and "error" in result:
        return JsonResponse({"error": result["error"]}, status=500)

    if request.htmx:
        return render(
            request,
            "_fragments/hotels_list.html",
            {
                "hotels": result,
                "place_name": place_name,
            },
        )
    return JsonResponse(result, safe=False)


@login_required
def save_place(request):
    if request.method == "POST":
        if request.htmx:
            name = request.POST.get("name", "")
            lat = request.POST.get("lat", "0")
            lon = request.POST.get("lon", "0")
            notes = request.POST.get("notes", "")
        else:
            data = json.loads(request.body)
            name = data["name"]
            lat = data["lat"]
            lon = data["lon"]
            notes = data.get("notes", "")
        SavedPlace.objects.create(
            user=request.user,
            name=name,
            latitude=float(lat),
            longitude=float(lon),
            notes=notes,
        )
        if request.htmx:
            return render(
                request,
                "_fragments/toast.html",
                {
                    "type": "success",
                    "icon": "fa-solid fa-circle-check",
                    "title": "Saved!",
                    "message": f"{name} added to your saved places.",
                },
            )
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "only post"}, status=405)


@login_required
def delete_place(request, id):
    if request.method == "POST":
        SavedPlace.objects.filter(id=id, user=request.user).delete()
        if request.htmx:
            return HttpResponse()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "only post"}, status=405)
