from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


# Create your models here.
class Profile(AbstractUser):
    TRAVEL_STYLE_CHOICES = [
        ("adventure", "Adventure"),
        ("relaxed", "Relaxed"),
        ("budget", "Budget"),
        ("luxury", "Luxury"),
    ]
    bio = models.TextField(max_length=500, blank=True)
    preferred_travel_style = models.CharField(
        max_length=50,
        choices=TRAVEL_STYLE_CHOICES,
        default="adventure",
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "profile"

    def __str__(self):
        return self.username


class SearchHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="searchhistory",
    )
    query = models.CharField(max_length=255)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} searched '{self.query}'"


class SavedLocation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_locations",
    )
    name = models.CharField(max_length=255)
    lat = models.FloatField()
    lon = models.FloatField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.name}"
