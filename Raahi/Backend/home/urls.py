from django.urls import path
from django.views.generic import RedirectView
from home.views import handle_auth, handle_pages, mappage_views
from home.views import support

urlpatterns = [
    path("", RedirectView.as_view(url="home")),
    path("register/", handle_auth.register_view, name="register"),
    path("login/", handle_auth.login_view, name="login"),
    path("logout/", handle_auth.logout_view, name="logout"),
    path("profile/", handle_auth.profile_view, name="profile"),
    path("home/", handle_pages.homepage, name="home"),
    path("go-map/", handle_pages.mappage, name="go_map"),
    path("set-place/", mappage_views.set_place, name="set_place"),
    path("get-place/", mappage_views.get_place, name="get_place"),
    path("save-place/", mappage_views.save_place, name="save_place"),
    path("delete-place/<int:id>/", mappage_views.delete_place, name="delete_place"),
    path("chat/", mappage_views.chat, name="chat"),
    path("get-places/", mappage_views.search_hotels, name="search_hotels"),
    path("support/", support.support_page, name="support"),
    path("support/send/", support.send_support_email, name="send_support"),
]
