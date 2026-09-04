from django.contrib import admin

from .models import Blog, Comment, UserPost

# Register your models here.
admin.site.register(Blog)
admin.site.register(UserPost)
admin.site.register(Comment)
