"""
URL configuration for the Wall-e Django project.

Wall-e — local AI desktop assistant (ChatGPT clone).
Routes requests to the chat app web UI and the REST API.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('chat.urls')),          # Web UI + API (API prefixed with /api/ inside chat.urls)
]
