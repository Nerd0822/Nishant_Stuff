from django.urls import path
from . import views

urlpatterns = [
    path("", views.homepage, name="home"),
    # path("api-chat/", views.api_chat_response, name="chat"),
]
