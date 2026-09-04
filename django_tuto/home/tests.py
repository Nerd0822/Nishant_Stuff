"""
Test suite for the `home` app.

Covers:
    * View behaviour (home, register, login, logout)
    * Access control (@login_required protected views)
    * Registration form validation
    * Login / logout flow
    * Template inheritance (every page extends base.html)
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import LoginForm, RegisterForm


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------


class HomePageTests(TestCase):
    """Tests for the home view."""

    def setUp(self):
        User.objects.create_user(username="testuser", password="Str0ngPass!123")
        self.client.login(username="testuser", password="Str0ngPass!123")

    def test_home_url_exists(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_home_anonymous_user_is_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_home_authenticated_user_gets_200(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_home_greets_logged_in_user_by_username(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "testuser")

    def test_home_uses_correct_template(self):
        response = self.client.get(reverse("home"))
        self.assertTemplateUsed(response, "home.html")


# ---------------------------------------------------------------------------
# Register page
# ---------------------------------------------------------------------------


class RegisterPageTests(TestCase):
    """Tests for the registration view."""

    def setUp(self):
        self.valid_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "Sup3rSecret!pass",
            "password2": "Sup3rSecret!pass",
        }

    def test_register_page_loads(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "register.html")

    def test_register_page_contains_form(self):
        response = self.client.get(reverse("register"))
        self.assertContains(response, "<form")

    def test_successful_registration_creates_user(self):
        self.client.post(reverse("register"), self.valid_data)
        self.assertEqual(User.objects.filter(username="newuser").count(), 1)

    def test_successful_registration_redirects_to_login(self):
        response = self.client.post(reverse("register"), self.valid_data)
        self.assertRedirects(response, reverse("login"))

    def test_mismatched_passwords_do_not_create_user(self):
        data = self.valid_data.copy()
        data["password2"] = "DifferentPassword!123"
        self.client.post(reverse("register"), data)
        self.assertEqual(User.objects.filter(username="newuser").count(), 0)

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username="newuser", password="SomePassword!123"
        )
        self.client.post(reverse("register"), self.valid_data)
        # Still only one user named "newuser"
        self.assertEqual(User.objects.filter(username="newuser").count(), 1)

    def test_common_password_is_rejected(self):
        data = self.valid_data.copy()
        data["password1"] = "password123"
        data["password2"] = "password123"
        self.client.post(reverse("register"), data)
        # NOTE: the account must never be created with a weak/common password.
        self.assertEqual(User.objects.count(), 0)

    def test_numeric_only_password_is_rejected(self):
        data = self.valid_data.copy()
        data["password1"] = "12345678"
        data["password2"] = "12345678"
        self.client.post(reverse("register"), data)
        self.assertEqual(User.objects.count(), 0)

    def test_too_short_password_is_rejected(self):
        data = self.valid_data.copy()
        data["password1"] = "abc12"
        data["password2"] = "abc12"
        self.client.post(reverse("register"), data)
        self.assertEqual(User.objects.count(), 0)


# ---------------------------------------------------------------------------
# Login page
# ---------------------------------------------------------------------------


class LoginPageTests(TestCase):
    """Tests for the login view."""

    def setUp(self):
        User.objects.create_user(
            username="testuser", password="Str0ngPass!123"
        )

    def _post_credentials(self, username, password):
        return self.client.post(
            reverse("login"),
            {"username": username, "password": password},
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

    def test_login_page_contains_form(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "<form")

    def test_valid_login_redirects_to_home(self):
        response = self._post_credentials("testuser", "Str0ngPass!123")
        self.assertRedirects(response, reverse("home"))

    def test_valid_login_logs_user_in(self):
        self._post_credentials("testuser", "Str0ngPass!123")
        user = User.objects.get(username="testuser")
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(user.pk))

    def test_wrong_password_does_not_log_in(self):
        response = self._post_credentials("testuser", "WrongPassword!123")
        self.assertNotIn("_auth_user_id", self.client.session)
        # Page is re-rendered with errors (status 200, not a redirect)
        self.assertEqual(response.status_code, 200)

    def test_unknown_username_does_not_log_in(self):
        response = self._post_credentials("ghost", "Whatever!123")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 200)

    def test_login_page_shows_link_to_register(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, reverse("register"))


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class LogoutTests(TestCase):
    """Tests for the logout view."""

    def setUp(self):
        User.objects.create_user(username="testuser", password="Str0ngPass!123")
        self.client.login(username="testuser", password="Str0ngPass!123")

    def test_logout_redirects_to_login(self):
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("login"))

    def test_logout_ends_the_session(self):
        self.client.get(reverse("logout"))
        response = self.client.get(reverse("home"))
        # After logout the user should be bounced back to login again
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)


# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------


class RegisterFormTests(TestCase):
    """Unit tests for the RegisterForm."""

    def test_form_declares_expected_fields(self):
        form = RegisterForm()
        expected = {"username", "email", "password1", "password2"}
        self.assertEqual(set(form.fields.keys()), expected)

    def test_valid_form(self):
        form = RegisterForm(
            data={
                "username": "formuser",
                "email": "formuser@example.com",
                "password1": "Sup3rSecret!pass",
                "password2": "Sup3rSecret!pass",
            }
        )
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_username(self):
        form = RegisterForm(
            data={
                "username": "",
                "email": "x@example.com",
                "password1": "Sup3rSecret!pass",
                "password2": "Sup3rSecret!pass",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)


class LoginFormTests(TestCase):
    """Unit tests for the LoginForm."""

    def test_form_has_username_and_password_fields(self):
        form = LoginForm()
        self.assertIn("username", form.fields)
        self.assertIn("password", form.fields)


# ---------------------------------------------------------------------------
# Templates / shared layout
# ---------------------------------------------------------------------------


class TemplateInheritanceTests(TestCase):
    """
    Every public page must inherit from the single shared base template:
    templates/base.html.
    """

    PUBLIC_PAGES = ("login", "register")

    def test_base_template_exists(self):
        import os

        from django.conf import settings

        template_dir = settings.TEMPLATES[0]["DIRS"][0]
        base_path = os.path.join(template_dir, "base.html")
        self.assertTrue(os.path.exists(base_path), "base.html must exist")

    def test_all_pages_extend_base_template(self):
        # Authenticated home page
        User.objects.create_user(username="testuser", password="Str0ngPass!123")
        self.client.login(username="testuser", password="Str0ngPass!123")
        response = self.client.get(reverse("home"))
        self.assertTemplateUsed(response, "base.html")

        # Public pages
        for name in self.PUBLIC_PAGES:
            response = self.client.get(reverse(name))
            self.assertEqual(
                response.status_code,
                200,
                f"Page '{name}' did not load successfully.",
            )
            self.assertTemplateUsed(response, "base.html")

    def test_pages_render_shared_header_and_footer_markers(self):
        """Pages should include content coming from base.html."""
        response = self.client.get(reverse("login"))
        html = response.content.decode()
        for marker in ("<header", "<footer", "</html>"):
            self.assertIn(marker, html)

