from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.contrib.auth.models import User 

from . import services
from .models import DoctorProfile

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
        # Ищем пациента по имени, которое ввел врач
        patient_name = request.POST.get("patient_name")
        try:
            # Ищем пользователя в базе по имени
            target_patient = User.objects.get(username=patient_name)
        except User.DoesNotExist:
            # Если такого пациента нет, можно вывести ошибку (пока просто игнорируем или создадим)
            # В идеале тут нужно вернуть форму с ошибкой
            return render(request, "clinic/data.html", {
                "records": services.build_records_view(None),
                "error": f"Пациент с именем {patient_name} не найден"
            })

        # Проверка того, что пациент закреплен за врачом
        try:
            doctor_profile = request.user.doctor_profile
        except DoctorProfile.DoesNotExist:
            return render(request, "clinic/data.html", {
                "records": services.build_records_view(None),
                "error": "У текущего пользователя нет профиля врача",
            })

        if not doctor_profile.patients.filter(pk=target_patient.pk).exists():
            return render(request, "clinic/data.html", {
                "records": services.build_records_view(None),
                "error": f"Пациент {patient_name} не закреплён за вами",
            })

        # Добавляем блок для найденного пациента
        services.add_block(target_patient, "medical_record", {
            "patient_name": patient_name,
            "diagnosis": request.POST.get("diagnosis"),
        })
        return redirect(request.path)
        
    return render(request, "clinic/data.html", {
        "records": services.build_records_view(None),
    })

@login_required
def doctor_list(request):
    _require_doctor(request.user)
    return render(request, "clinic/doctor_list.html", {
        "patients": services.list_available_patients(),
        "mine": services.list_doctor_patients(request.user),
    })


@login_required
def doctor_assign(request, patient_id):
    _require_doctor(request.user)
    if request.method == "POST":
        if request.user.doctor_profile.patients.filter(pk=patient_id).exists():
            return redirect("clinic-doctor-list")
        services.assign_patient(request.user, patient_id)
        return redirect("clinic-doctor-list")
    return render(request, "clinic/doctor_assign.html", {"patient_id": patient_id})