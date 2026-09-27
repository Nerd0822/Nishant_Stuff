from unittest.mock import AsyncMock, patch

from django.test import Client, TestCase

from accounts.models import Profile, SearchHistory

GEOCODE_RESULT = {"lat": 28.6, "lon": 77.2, "name": "Delhi"}


class SearchTrackingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Profile.objects.create_user(
            username="tester", password="StrongPass123!"
        )

    def _search(self):
        with patch(
            "home.views.convert_place_to_cords",
            new=AsyncMock(return_value=GEOCODE_RESULT),
        ):
            return self.client.post("/search-place/", {"destination": "Delhi"})

    def test_authed_search_is_logged(self):
        self.client.force_login(self.user)
        r = self._search()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(SearchHistory.objects.filter(user=self.user).count(), 1)

    def test_anon_search_works_but_is_not_logged(self):
        r = self._search()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(SearchHistory.objects.count(), 0)

    def test_invalid_form_returns_400(self):
        r = self.client.post("/search-place/", {})
        self.assertEqual(r.status_code, 400)
