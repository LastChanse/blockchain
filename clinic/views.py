from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.contrib.auth.models import User

import requests

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
    is_valid, error_info = services.validate_chain()

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
                "records": services.build_records_view(),
                "is_valid": is_valid,
                "error_info": error_info,
                "error": f"Пациент с именем {patient_name} не найден"
            })

        # Проверка того, что пациент закреплен за врачом
        try:
            doctor_profile = request.user.doctor_profile
        except DoctorProfile.DoesNotExist:
            return render(request, "clinic/data.html", {
                "records": services.build_records_view(None),
                "is_valid": is_valid,
                "error_info": error_info,
                "error": "У текущего пользователя нет профиля врача",
            })

        if not doctor_profile.patients.filter(pk=target_patient.pk).exists():
            return render(request, "clinic/data.html", {
                "records": services.build_records_view(None),
                "is_valid": is_valid,
                "error_info": error_info,
                "error": f"Пациент {patient_name} не закреплён за вами",
            })

        # Добавляем блок для найденного пациента
        services.add_block(target_patient, "medical_record", {
            "patient_name": patient_name,
            "diagnosis": request.POST.get("diagnosis"),
        })
        return redirect(request.path)
        
    return render(request, "clinic/data.html", {
        "records": services.build_records_view(),
        "is_valid": is_valid,
        "error_info": error_info,
    })

@login_required
def doctor_list(request):
    _require_doctor(request.user)
    return render(request, "clinic/doctor_list.html", {
        "patients": services.list_available_patients(request.user),
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


# ---------- Страница «Сеть» ----------

def _peers():
    return [p.rstrip("/") for p in getattr(settings, "PEERS", []) if p]


def _headers():
    token = getattr(settings, "INTERNAL_SYNC_TOKEN", "")
    return {"X-Internal-Token": token} if token else {}


def _url(base, path):
    # clinic.urls подключён как path("clinic/", include(...)),
    # значит API живёт под /clinic/network/...
    return f"{base}/clinic/network{path}"


def _fetch_peer_height(base):
    r = requests.get(_url(base, "/height"), headers=_headers(), timeout=3)
    r.raise_for_status()
    return r.json()


def _fetch_peer_blocks(base, since=0):
    r = requests.get(
        _url(base, "/blocks"),
        params={"from": since},
        headers=_headers(),
        timeout=3,
    )
    r.raise_for_status()
    return r.json()


def _post_block(base, block):
    r = requests.post(
        _url(base, "/blocks"),
        json=block,
        headers=_headers(),
        timeout=3,
    )
    try:
        data = r.json()
    except ValueError:
        data = {"raw": r.text}
    data["status_code"] = r.status_code
    return data


def _collect_peers_info():
    infos = []
    for peer in _peers():
        try:
            info = _fetch_peer_height(peer)
            infos.append({
                "peer": peer,
                "online": True,
                "node_id": info.get("node_id"),
                "height": info.get("height"),
                "last_hash": info.get("last_hash"),
            })
        except requests.RequestException as exc:
            infos.append({"peer": peer, "online": False, "error": str(exc)})
    return infos


def _broadcast_last_block():
    last = services._last_global()
    if last is None:
        return [{"peer": "—", "error": "локальная цепочка пуста"}]

    block = {
        "index": last.index,
        "prev_hash": last.prev_hash,
        "type": last.type,
        "timestamp": last.timestamp,
        "content_hash": last.content_hash,
        "payload": last.payload,
        "hash": last.hash,
    }
    results = []
    for peer in _peers():
        try:
            results.append({"peer": peer, **_post_block(peer, block)})
        except requests.RequestException as exc:
            results.append({"peer": peer, "_status": None, "error": str(exc)})
    return results


def _sync_from_peers():
    """Догнать пиров: GET height → GET blocks?from=N → validate → add."""
    local_index = services.local_height()
    report = []
    for peer in _peers():
        rep = {"peer": peer, "accepted": 0, "errors": []}
        try:
            info = _fetch_peer_height(peer)
            peer_height = int(info.get("height", -1))
            if peer_height <= local_index:
                report.append(rep)
                continue
            data = _fetch_peer_blocks(peer, since=local_index + 1)
            for block in data.get("blocks", []):
                ok, err = services.validate_incoming_block(block)
                if not ok:
                    rep["errors"].append(
                        {"index": block.get("index"), "error": err}
                    )
                    break
                services.add_block_from_dict(block)
                rep["accepted"] += 1
                local_index = block["index"]
        except requests.RequestException as exc:
            rep["errors"].append({"error": str(exc)})
        report.append(rep)
    return report


@login_required
def network(request):
    peers_info = _collect_peers_info()
    sync_report = None
    broadcast_report = None

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "sync":
            sync_report = _sync_from_peers()
        elif action == "broadcast_last":
            broadcast_report = _broadcast_last_block()

    if sync_report is not None:
        peers_info = _collect_peers_info()

    return render(request, "clinic/network.html", {
        "node_id": settings.NODE_ID,
        "node_role": settings.NODE_ROLE,
        "peers_info": peers_info,
        "sync_report": sync_report,
        "broadcast_report": broadcast_report,
        "local_height": services.local_height(),
        "peer_nodes_setting": settings.PEERS,
    })