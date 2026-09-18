from django.shortcuts import render
import requests


# Create your views here.
def homepage(request):
    if request.method == "POST":
        user_message = request.POST.get("usermessage")
        response = requests.post(
            url="http://127.0.0.1:8080/chat", json={"user": user_message}
        )
        context = {"response": response}
        # print(f"this is the user message {user_message}")
        return render(request, "home.html", context)

    if request.method == "GET":
        response = requests.get(url="http://127.0.0.1:8080/status")
        context = {"response": response}
        return render(request, "home.html", context)


# use fast api to serve the model
# model to store session or chat


# todo
# there are some errors in the serialization whenthe data reaches the fastapi,can just use it in the django app
