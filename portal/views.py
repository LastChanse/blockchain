from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render

from clinic.services import get_or_create_doctor


def index(request):
    return render(request, "portal/index.html")


def apply(request):
    return render(request, "portal/apply.html")


def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role", "patient")
        # public_key принимаем, но пока не используем
        if not username or not password:
            return render(request, "portal/register.html",
                          {"error": "Заполните логин и пароль"})
        if role not in ("patient", "doctor"):
            return render(request, "portal/register.html",
                          {"error": "Неизвестная роль"})
        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, password=password)
                if role == "doctor":
                    get_or_create_doctor(user)
        except IntegrityError:
            return render(request, "portal/register.html",
                          {"error": "Пользователь уже существует"})
        return redirect("login")
    return render(request, "portal/register.html")


def data(request):
    return redirect("clinic-data")