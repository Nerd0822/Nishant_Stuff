from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from explore.models import Comment, Like, Post

User = get_user_model()


class PostTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="tester", password="StrongPass123!"
        )
        self.client.force_login(self.user)

    def test_create_post(self):
        r = self.client.post(
            reverse("create_post"),
            {"title": "Leh ride", "content": "Amazing roads!", "location_name": "Leh"},
        )
        self.assertRedirects(r, reverse("explore"))
        post = Post.objects.get(title="Leh ride")
        self.assertEqual(post.user, self.user)

    def test_like_then_unlike(self):
        post = Post.objects.create(user=self.user, title="T", content="C")
        self.client.post(reverse("toggle_like", args=[post.pk]))
        self.assertEqual(Like.objects.filter(post=post).count(), 1)
        self.client.post(reverse("toggle_like", args=[post.pk]))
        self.assertEqual(Like.objects.filter(post=post).count(), 0)

    def test_comment(self):
        post = Post.objects.create(user=self.user, title="T", content="C")
        r = self.client.post(reverse("add_comment", args=[post.pk]), {"content": "Nice!"})
        self.assertRedirects(r, post.get_absolute_url())
        self.assertEqual(Comment.objects.filter(post=post).count(), 1)

    def test_feed_renders_for_anonymous_users(self):
        Post.objects.create(user=self.user, title="T", content="C")
        Client().get(reverse("explore"))
        r = Client().get(reverse("explore"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "T")

    def test_detail_has_open_graph_tags(self):
        post = Post.objects.create(user=self.user, title="T", content="C")
        r = Client().get(post.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "og:title")
