from django.urls import path
from . import views, internal_views, network_views

urlpatterns = [
    path("", views.index, name="clinic-index"),
    path("data/", views.data, name="clinic-data"),
    path("doctor/", views.doctor_list, name="clinic-doctor-list"),
    path("doctor/assign/<int:patient_id>/", views.doctor_assign, name="clinic-doctor-assign"),
    path("internal/users", internal_views.sync_user, name="internal-sync-user"),

    path("network/height", network_views.network_height, name="network-height"),
    path("network/blocks", network_views.network_blocks, name="network-blocks"),
]