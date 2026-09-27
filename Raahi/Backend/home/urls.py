from django.urls import path
from . import views

urlpatterns = [
    path("", views.homepage, name="home"),
    path("map/", views.mappage, name="map"),
    path("search-place/", views.search_place, name="search_place"),
    path("reverse-geocode/", views.reverse_geocode, name="reverse_geocode"),
    path("chat/ask/", views.chat_ask, name="chat_ask"),
    path("itinerary/start/", views.itinerary_start, name="itinerary_start"),
    path("tasks/<str:task_id>/", views.task_status, name="task_status"),
]
