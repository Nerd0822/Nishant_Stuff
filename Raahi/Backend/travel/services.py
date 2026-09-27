"""Service layer for external travel APIs.

Each function returns structured data. Free-tier sources are used where
possible. To upgrade to a paid API, replace the function body — the views
and frontend stay the same.
"""

import httpx
from django.core.cache import cache

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "Raahi/3.0"}


def _icon_key(category: str) -> str:
    """Map an OSM amenity/tourism value to an icon key.

    The frontend maps each key to an inline SVG, so the API stays free
    of presentation details.
    """
    mapping = {
        "restaurant": "restaurant",
        "hotel": "hotel",
        "cafe": "cafe",
        "bar": "bar",
        "tourist_attraction": "attraction",
        "museum": "attraction",
        "park": "park",
        "pharmacy": "pharmacy",
        "fuel": "fuel",
    }
    return mapping.get(category, "pin")


async def find_nearby_places(
    lat: float, lon: float, radius: int = 5000, category: str = "restaurant"
) -> list:
    """Find nearby places using the OSM Overpass API (free, no key needed).

    Results are cached in Redis for 5 minutes to respect rate limits.
    """
    cache_key = f"travel:places:{lat:.4f}:{lon:.4f}:{category}:{radius}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    overpass_query = (
        f"[out:json];"
        f'node(around:{radius},{lat},{lon})["amenity"="{category}"];'
        f"out body;"
    )
    async with httpx.AsyncClient(timeout=20, headers=HEADERS) as client:
        response = await client.post(OVERPASS_URL, data={"data": overpass_query})
        response.raise_for_status()
        data = response.json()

    places = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        places.append(
            {
                "name": tags.get("name", "Unknown"),
                "lat": element.get("lat"),
                "lon": element.get("lon"),
                "type": tags.get("amenity", category),
                "address": tags.get("addr:street", ""),
                "icon": _icon_key(tags.get("amenity", category)),
            }
        )

    cache.set(cache_key, places, timeout=300)
    return places


async def find_hotels(lat: float, lon: float, radius: int = 10000) -> list:
    """Find nearby hotels.

    Hotels are usually tagged tourism=hotel/hostel/guest_house in OSM
    (not amenity=hotel), so this uses its own query covering both.
    Results are cached in Redis for 5 minutes.
    """
    cache_key = f"travel:hotels:{lat:.4f}:{lon:.4f}:{radius}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    overpass_query = (
        f"[out:json];"
        f"("
        f'node(around:{radius},{lat},{lon})["amenity"="hotel"];'
        f'node(around:{radius},{lat},{lon})["tourism"~"hotel|hostel|guest_house|apartment"];'
        f");"
        f"out body;"
    )
    async with httpx.AsyncClient(timeout=20, headers=HEADERS) as client:
        response = await client.post(OVERPASS_URL, data={"data": overpass_query})
        response.raise_for_status()
        data = response.json()

    places = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        kind = tags.get("tourism", tags.get("amenity", "hotel"))
        places.append(
            {
                "name": tags.get("name", "Unknown"),
                "lat": element.get("lat"),
                "lon": element.get("lon"),
                "type": kind,
                "address": tags.get("addr:street", ""),
                "icon": "hotel",
            }
        )

    cache.set(cache_key, places, timeout=300)
    return places


async def find_flights(origin: str, destination: str, date: str) -> list:
    """Stub for flight search. Plug in the Kiwi Tequila API when ready.

    https://api.tequila.kiwi.com/ — free tier available with an API key.
    """
    return []


async def find_buses(origin: str, destination: str, date: str) -> list:
    """Stub for bus search. Plug in the RedBus / MakeMyTrip API when ready."""
    return []
