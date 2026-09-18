from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# show pages
@login_required
def homepage(request):
    return render(request, "home.html")


@login_required
def mappage(request):
    context = {
        "last_searched_place": request.session.get("place", ""),
        "last_searched_lat": request.session.get("lat", ""),
        "last_searched_lon": request.session.get("lon", ""),
    }
    return render(request, "map.html", context)
