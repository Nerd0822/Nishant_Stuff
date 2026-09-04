from django.urls import path

from . import views

urlpatterns = [
    path("", views.Bloglist.as_view()),
    path("info/<int:pk>/", views.Bloginfo.as_view()),
    path("post/", views.UserPostgenerics.as_view()),
    path("post/<int:pk>/", views.UserPostviews.as_view()),
    path("comment/<int:pk>/", views.Commentgenerics.as_view()),
]
