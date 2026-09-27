import asyncio
from functools import wraps

from asgiref.sync import sync_to_async
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST, require_GET

from accounts.models import SearchHistory
from .forms import PlaceForm
from .helper import convert_place_to_cords, reverse_geocode_coords
from . import tasks as bg_tasks


def async_login_required(view_func):
    """Decorator to require login for async views."""
    @wraps(view_func)
    async def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=401)
        return await view_func(request, *args, **kwargs)
    return wrapper


# Create your views here.
def homepage(request):
    return render(request, "home.html")


@login_required
def mappage(request):
    form = PlaceForm()
    return render(request, "map.html", {"form": form})


@async_login_required
async def reverse_geocode(request):
    """Turn coordinates from the browser into a place name (used by "use my location")."""
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    if not lat or not lon:
        return JsonResponse({"error": "lat and lon are required."}, status=400)

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return JsonResponse({"error": "lat and lon must be numbers."}, status=400)

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return JsonResponse({"error": "lat or lon is out of range."}, status=400)

    try:
        name = await reverse_geocode_coords(lat, lon)
    except Exception:
        return JsonResponse({"error": "Geocoding service unavailable."}, status=503)

    return JsonResponse({"lat": lat, "lon": lon, "name": name})


@async_login_required
@require_POST
async def search_place(request):
    form = PlaceForm(request.POST)
    if not form.is_valid():
        form_errors=[]
        for field_errors in form.errors.values():
            for e in field_errors:
                form_errors.append(str(e))
        return JsonResponse(
            {"start": None, "destination": None, "errors": form_errors},
            status=400,
        )

    destination = form.cleaned_data.get("destination")or ""
    start_location = form.cleaned_data.get("start_location") or ""
    start_lat = form.cleaned_data.get("start_lat")
    start_lon = form.cleaned_data.get("start_lon")

    location = None
    if destination:
        try:
            location = await convert_place_to_cords(destination)
        except Exception:
            location = None

    if start_lat is not None and start_lon is not None:
        start = {"lat": start_lat, "lon": start_lon, "name": "Current location"}
    elif start_location:
        try:
            start = await convert_place_to_cords(start_location)
        except Exception:
            start = None
    else:
        start = None

    errors = []
    if destination and location is None:
        errors.append(f"Could not find '{destination}'. Try a different search.")
    if start_location and start is None:
        errors.append(f"Could not find the start location '{start_location}'.")

    # Log the search for signed-in users (sync ORM call inside an async view).
    # NOTE: even reading request.user hits the DB (session lookup), so the
    # whole auth check runs in a thread via sync_to_async.
    is_authenticated = await sync_to_async(lambda: request.user.is_authenticated)()
    if is_authenticated:
        authed_user = await sync_to_async(lambda: request.user)()
        log_lat = start_lat if start_lat is not None else (location["lat"] if location else None)
        log_lon = start_lon if start_lon is not None else (location["lon"] if location else None)
        await sync_to_async(SearchHistory.objects.create)(
            user=authed_user,
            query=start_location or destination or "Unknown",
            lat=log_lat,
            lon=log_lon,
            location_name=(location["name"] if location else "") or "",
        )

    return JsonResponse(
        {
            "start": start,
            "destination": location,
            "errors": errors,
        }
    )


@login_required
@require_POST
def chat_ask(request):
    """Start a background chat job. Returns {"task_id": ...} instantly."""
    question = (request.POST.get("question") or "").strip()
    place_name = (request.POST.get("place") or "").strip()
    if not question:
        return JsonResponse({"error": "Type a question first."}, status=400)
    job = bg_tasks.chat_with_ollama.delay(question, place_name)
    return JsonResponse({"task_id": job.id, "status": "PENDING"})


@login_required
@require_POST
def itinerary_start(request):
    """Start a background itinerary job. Returns {"task_id": ...} instantly."""
    place_name = (request.POST.get("place") or "").strip()
    if not place_name:
        return JsonResponse({"error": "Search a destination first."}, status=400)
    job = bg_tasks.build_itinerary.delay(place_name)
    return JsonResponse({"task_id": job.id, "status": "PENDING"})


@login_required
@require_GET
def task_status(request, task_id: str):
    """Poll a Celery job. Frontend calls this every ~3s until SUCCESS/FAILURE."""
    result = bg_tasks.chat_with_ollama.AsyncResult(task_id)
    # build_itinerary shares the same backend, so one lookup covers both.
    if result.state in ("PENDING", "STARTED", "RETRY"):
        return JsonResponse({"task_id": task_id, "status": result.state})
    if result.state == "SUCCESS":
        # Result is ready; get with short timeout to avoid blocking indefinitely
        payload = result.get(timeout=2)
        return JsonResponse({"task_id": task_id, "status": "SUCCESS", "result": payload})
    return JsonResponse(
        {"task_id": task_id, "status": "FAILURE", "error": str(result.info)},
        status=500,
    )


# todo
# 1. add a map page so that user can use navigation -- done
# 2. show the route use wants take -- done
# 3. add a gps (like allow map to update based on your live location, like using gps while in a car.)
# 4. add chatbot
# 5. show recommendations (build a recomendation system for it)
# 6. show itinerary with details of restaraunts
# 7. add user login
# 8. dockerize
# 9. add nginx