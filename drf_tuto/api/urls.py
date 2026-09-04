from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("authors-viewset", views.Authorviewset, basename="authors-viewsetapi")
router.register(
    "authors-modelviewset", views.Authormodelviewset, basename="authors-modelviewsetapi"
)

urlpatterns = [
    path("authors/", views.authorslist),
    path("authors/<int:pk>/", views.authordetail),
    path("authors/info/<int:pk>/", views.AuthorInfo.as_view()),
    path("books/", views.Bookapi.as_view()),
    path("books/<int:pk>/", views.Bookinfoapi.as_view()),
    path("genre/", views.Genreapi.as_view()),
    path("genre/<int:pk>/", views.Genreinfoapi.as_view()),
    path("", include(router.urls)),
]
