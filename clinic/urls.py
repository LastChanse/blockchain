from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="clinic-index"),
    path("data/", views.data, name="clinic-data"),
    path("doctor/", views.doctor_list, name="clinic-doctor-list"),
    path("doctor/assign/<int:patient_id>/", views.doctor_assign, name="clinic-doctor-assign"),
]