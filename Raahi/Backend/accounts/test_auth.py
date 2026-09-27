from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="tester", email="t@t.com", password="StrongPass123!"
        )

    def test_register_creates_user_and_logs_in(self):
        r = self.client.post(
            reverse("register"),
            {
                "username": "newbie",
                "email": "n@n.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "preferred_travel_style": "budget",
            },
        )
        self.assertRedirects(r, reverse("home"))
        self.assertTrue(User.objects.filter(username="newbie").exists())
        # Auto-login: the profile page is reachable right after registering.
        r = self.client.get(reverse("profile", args=["newbie"]))
        self.assertEqual(r.status_code, 200)

    def test_login(self):
        r = self.client.post(
            reverse("login"), {"username": "tester", "password": "StrongPass123!"}
        )
        self.assertRedirects(r, reverse("home"))

    def test_profile_requires_login(self):
        r = self.client.get(reverse("profile", args=["tester"]))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r.url)
