from django.contrib import admin
from .models import UserProfile, SavedPlace, ChatHistory, SupportTicket

# Register your models here.

admin.site.register([UserProfile, SavedPlace, ChatHistory, SupportTicket])
