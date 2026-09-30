from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="portal-index"),
    path("apply/", views.apply, name="portal-apply"),
    path("register/", views.register, name="portal-register"),
]