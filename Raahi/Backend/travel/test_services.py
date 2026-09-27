from unittest.mock import AsyncMock

from django.core.cache import cache
from django.test import SimpleTestCase
from django.test.utils import override_settings

from travel.services import find_hotels, find_nearby_places

OVERPASS_PAYLOAD = {
    "elements": [
        {
            "lat": 28.61,
            "lon": 77.20,
            "tags": {"name": "Spice House", "amenity": "restaurant"},
        },
        {
            "lat": 28.62,
            "lon": 77.21,
            "tags": {"amenity": "restaurant"},  # unnamed -> "Unknown"
        },
    ]
}

LOC_MEM = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def make_fake_client(calls):
    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            calls.append(kwargs.get("data", args[1] if len(args) > 1 else ""))
            return FakeResponse(OVERPASS_PAYLOAD)

    return FakeClient


@override_settings(CACHES=LOC_MEM)
class TravelServiceTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    async def test_parses_overpass_response(self):
        from unittest.mock import patch

        with patch("travel.services.httpx.AsyncClient", make_fake_client([])):
            places = await find_nearby_places(28.6, 77.2, category="restaurant")
        self.assertEqual(len(places), 2)
        self.assertEqual(places[0]["name"], "Spice House")
        self.assertEqual(places[0]["icon"], "restaurant")
        self.assertEqual(places[1]["name"], "Unknown")

    async def test_second_call_hits_cache(self):
        from unittest.mock import patch

        calls = []
        with patch("travel.services.httpx.AsyncClient", make_fake_client(calls)):
            await find_nearby_places(28.6, 77.2, category="restaurant")
            await find_nearby_places(28.6, 77.2, category="restaurant")
        self.assertEqual(len(calls), 1)

    async def test_hotels_query_covers_tourism_tags(self):
        from unittest.mock import patch

        calls = []
        with patch("travel.services.httpx.AsyncClient", make_fake_client(calls)):
            await find_hotels(28.6, 77.2)
        self.assertEqual(len(calls), 1)
        self.assertIn("tourism", calls[0]["data"])
