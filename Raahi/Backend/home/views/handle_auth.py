from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

from home.models import SavedPlace, ChatHistory

from dotenv import load_dotenv

load_dotenv()
# Create your views here.


def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get("next", "home")
            return redirect(next_url)
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def profile_view(request):
    user = request.user
    saved_places = SavedPlace.objects.filter(user=user)
    chat_history = ChatHistory.objects.filter(user=user)

    return render(
        request,
        "profile.html",
        {"saved_places": saved_places, "chat_history": chat_history},
    )
