from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .services import find_hotels, find_nearby_places


def async_login_required(view_func):
    """Decorator to require login for async views."""
    from functools import wraps
    @wraps(view_func)
    async def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=401)
        return await view_func(request, *args, **kwargs)
    return wrapper


@async_login_required
@require_GET
async def nearby_places(request):
    """Return nearby places as JSON for map markers."""
    try:
        lat = float(request.GET.get("lat", ""))
        lon = float(request.GET.get("lon", ""))
    except (TypeError, ValueError):
        return JsonResponse({"error": "lat and lon are required."}, status=400)
    category = request.GET.get("category", "restaurant")
    places = await find_nearby_places(lat, lon, category=category)
    return JsonResponse({"places": places})


@async_login_required
@require_GET
async def hotels(request):
    """Return nearby hotels as JSON for map markers."""
    try:
        lat = float(request.GET.get("lat", ""))
        lon = float(request.GET.get("lon", ""))
    except (TypeError, ValueError):
        return JsonResponse({"error": "lat and lon are required."}, status=400)
    results = await find_hotels(lat, lon)
    return JsonResponse({"hotels": results})
