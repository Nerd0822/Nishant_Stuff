from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import auth
from django.shortcuts import redirect, render

from .forms import LoginForm, RegisterForm


# Create your views here.
@login_required
def home(request):
    return render(request, "home.html")


def loginpage(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = request.POST.get("username")
            password = request.POST.get("password")

            user = authenticate(request, username=username, password=password)

            if user is not None:
                auth.login(request, user)

                return redirect("home")

    form = LoginForm()
    context = {"loginform": form}
    return render(request, "login.html", context)


def registerpage(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")

    form = RegisterForm()
    context = {"registerform": form}
    return render(request, "register.html", context=context)

@login_required
def logoutuser(request):
    auth.logout(request)
    return redirect("login")
