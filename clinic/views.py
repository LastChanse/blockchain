from django.conf import settings
from django.shortcuts import render

def index(request):
    return render(request, "clinic/index.html", {
        "node_id": settings.NODE_ID,
        "node_role": settings.NODE_ROLE,
    })