from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from . import services


def _require_doctor(user):
    if not services.is_doctor(user):
        raise PermissionDenied


def index(request):
    return render(request, "clinic/index.html", {
        "node_id": settings.NODE_ID,
        "node_role": settings.NODE_ROLE,
    })


@login_required
def data(request):
    if request.method == "POST":
        services.add_block(request.user, "medical_record", {
            "patient_name": request.POST.get("patient_name"),
            "diagnosis": request.POST.get("diagnosis"),
        })
        return redirect(request.path)
    return render(request, "clinic/data.html", {
        "records": services.build_records_view(request.user),
    })


@login_required
def doctor_list(request):
    _require_doctor(request.user)
    return render(request, "clinic/doctor_list.html", {
        "patients": services.list_all_patients(),
        "mine": services.list_doctor_patients(request.user),
    })


@login_required
def doctor_assign(request, patient_id):
    _require_doctor(request.user)
    if request.method == "POST":
        services.assign_patient(request.user, patient_id)
        return redirect("clinic-doctor-list")
    return render(request, "clinic/doctor_assign.html", {"patient_id": patient_id})