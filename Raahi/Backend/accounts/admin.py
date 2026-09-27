from django.contrib import admin

from .models import Profile, SavedLocation, SearchHistory


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "preferred_travel_style", "created_at")
    list_filter = ("preferred_travel_style",)
    search_fields = ("username", "email")


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "query", "location_name", "created_at")
    list_filter = ("created_at",)
    search_fields = ("query", "location_name", "user__username")


@admin.register(SavedLocation)
class SavedLocationAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "created_at")
    search_fields = ("name", "user__username")
