from django.urls import path
from . import views

urlpatterns = [
    path('nearby/', views.nearby_places, name='nearby_places'),
    path('hotels/', views.hotels, name='hotels'),
]
