from django.shortcuts import render

def index(request):
    return render(request, "portal/index.html")

def apply(request):
    return render(request, "portal/apply.html")

def register(request):
    return render(request, "portal/register.html")