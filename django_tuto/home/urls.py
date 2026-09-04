from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.registerpage, name="register"),
    path("login/", views.loginpage, name="login"),
    path("logout/", views.logoutuser, name="logout"),
]
