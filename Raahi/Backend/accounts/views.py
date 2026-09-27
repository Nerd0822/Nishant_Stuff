from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProfileLoginForm, ProfileRegistrationForm
from .models import Profile


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = ProfileRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Raahi, {user.username}!")
            return redirect("home")
    else:
        form = ProfileRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = ProfileLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = ProfileLoginForm()
    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(Profile, username=username)
    search_history = profile_user.searchhistory.all()[:10]
    saved_locations = profile_user.saved_locations.all()[:10]
    posts = profile_user.posts.all()[:10]
    return render(
        request,
        "accounts/profile.html",
        {
            "profile_user": profile_user,
            "search_history": search_history,
            "saved_locations": saved_locations,
            "posts": posts,
        },
    )
