import hashlib

from django.contrib.auth.models import User

from core import Block, BlockHeader
from core.block import canonical_json

from .models import ChainBlock, DoctorProfile

GENESIS_PREV_HASH = "0" * 64


def _last(patient):
    return ChainBlock.objects.filter(patient=patient).order_by("-index").first()


def _ensure_genesis(patient):
    if _last(patient) is not None:
        return
    header = BlockHeader(prev_hash=GENESIS_PREV_HASH, type="genesis")
    block = Block(index=0, header=header, payload={"msg": "genesis"})
    block.hash = block.compute_hash()
    ChainBlock.objects.create(
        patient=patient,
        index=0,
        timestamp=block.header.timestamp,
        prev_hash=block.header.prev_hash,
        hash=block.hash,
        type=block.header.type,
        payload=block.payload,
    )


def add_block(patient, type_, payload):
    _ensure_genesis(patient)
    last = _last(patient)
    header = BlockHeader(prev_hash=last.hash, type=type_)
    block = Block(index=last.index + 1, header=header, payload=payload)
    block.hash = block.compute_hash()
    return ChainBlock.objects.create(
        patient=patient,
        index=block.index,
        timestamp=block.header.timestamp,
        prev_hash=block.header.prev_hash,
        hash=block.hash,
        type=block.header.type,
        payload=block.payload,
    )


def list_blocks(patient):
    return list(ChainBlock.objects.filter(patient=patient).order_by("index"))


def _recompute(b):
    body = {
        "index": b.index,
        "prev_hash": b.prev_hash,
        "type": b.type,
        "timestamp": b.timestamp,
        "payload": b.payload,
    }
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def build_records_view(patient=None):
    # Если patient передан — берем только его блоки. Если нет — берем ВСЕ блоки.
    if patient:
        blocks = list_blocks(patient)
    else:
        blocks = list(ChainBlock.objects.all().order_by("patient_id", "index"))
        
    by_index = {b.index: b for b in blocks}
    records = []
    for b in blocks:
        if b.type != "medical_record":
            continue
        recomputed = _recompute(b)
        match = "OK" if b.hash == recomputed else "BROKEN"
        if b.index == 0:
            prev_link = "-"
        else:
            prev = by_index.get(b.index - 1)
            prev_link = "OK" if prev and b.prev_hash == prev.hash else "BROKEN"
            
        records.append({
            "patient_name": b.payload.get("patient_name"),
            "diagnosis": b.payload.get("diagnosis"),
            "index": b.index,
            "hash_short": f"{b.hash[:12]}...",
            "hash_full": b.hash,
            "recomputed_short": f"{recomputed[:12]}...",
            "match": match,
            "prev_link": prev_link,
        })
    return records


def is_doctor(user):
    return DoctorProfile.objects.filter(user=user).exists()


def get_or_create_doctor(user):
    profile, _ = DoctorProfile.objects.get_or_create(user=user)
    return profile


def list_all_patients():
    return User.objects.filter(doctor_profile__isnull=True).order_by("username")


def assign_patient(doctor_user, patient_id):
    profile = get_or_create_doctor(doctor_user)
    profile.patients.add(User.objects.get(pk=patient_id))


def list_doctor_patients(doctor_user):
    profile = DoctorProfile.objects.filter(user=doctor_user).first()
    return list(profile.patients.all()) if profile else []