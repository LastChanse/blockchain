import hashlib

from django.contrib.auth.models import User
from django.db import transaction

from core import Block, BlockHeader
from core.block import canonical_json

from .models import ChainBlock, DoctorProfile

GENESIS_PREV_HASH = "0" * 64


def _last_global():
    """Возвращает самый последний блок в глобальной цепочке."""
    return ChainBlock.objects.order_by("-index").first()

@transaction.atomic
def _ensure_genesis():
    """Создает единый Genesis-блок, если цепочка пуста."""
    if _last_global() is not None:
        return
    header = BlockHeader(prev_hash=GENESIS_PREV_HASH, type="genesis")
    block = Block(index=0, header=header, payload={"msg": "global genesis"})
    block.hash = block.compute_hash()
    ChainBlock.objects.create(
        patient=None,
        index=0,
        timestamp=block.header.timestamp,
        prev_hash=block.header.prev_hash,
        hash=block.hash,
        type=block.header.type,
        payload=block.payload,
    )


@transaction.atomic
def add_block(patient, type_, payload):
    """Добавляет блок в глобальную цепочку."""
    _ensure_genesis()
    
    # Блокируем таблицу на чтение/запись на время добавления, 
    # чтобы избежать Race Condition при одновременном добавлении двумя врачами
    last = ChainBlock.objects.select_for_update().order_by("-index").first()
    
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


def list_blocks(patient=None):
    """Возвращает всю глобальную цепочку (или отфильтрованную, если нужно)."""
    qs = ChainBlock.objects.all().order_by("index")
    if patient:
        # Если нужна выборка по пациенту — фильтруем.
        # Но это уже не "цепочка пациента", а вырванные из общей цепочки блоки!
        qs = qs.filter(patient=patient)
    return list(qs)

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
    # Загружаем ВСЮ глобальную цепочку для проверки связей
    all_blocks = list(ChainBlock.objects.all().order_by("index"))
    by_index = {b.index: b for b in all_blocks}

    records = []
    for b in all_blocks:
        # Если передан пациент, пропускаем блоки других пациентов
        if patient and b.patient_id != patient.id:
            continue
        # Пропускаем системные блоки
        if b.type != "medical_record":
            continue
            
        recomputed = _recompute(b)
        match = "OK" if b.hash == recomputed else "BROKEN"
        
        if b.index == 0:
            prev_link = "-"
        else:
            # Ищем предыдущий блок в глобальной цепочке
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

def list_available_patients(doctor_user):
    """
    Возвращает пациентов, которых еще нет у данного врача.
    """
    profile = get_or_create_doctor(doctor_user)
    return User.objects.filter(doctor_profile__isnull=True).exclude(
        assigned_doctors=profile
    ).order_by("username")

def assign_patient(doctor_user, patient_id):
    profile = get_or_create_doctor(doctor_user)
    profile.patients.add(User.objects.get(pk=patient_id))


def list_doctor_patients(doctor_user):
    profile = DoctorProfile.objects.filter(user=doctor_user).first()
    return list(profile.patients.all()) if profile else []

def validate_chain():
    """
    Проходит по всей цепочке от начала до конца.
    Возвращает кортеж (is_valid, error_info).
    error_info содержит индекс блока и текст ошибки, если цепочка сломана.
    """
    blocks = list(ChainBlock.objects.all().order_by("index"))
    
    if not blocks:
        return True, None # Пустая цепочка

    by_index = {b.index: b for b in blocks}

    for b in blocks:
        # 1. Проверка: не пропущен ли блок (дырка в индексах)
        if b.index > 0 and (b.index - 1) not in by_index:
            return False, {
                "index": b.index, 
                "error": f"Пропущен предыдущий блок (ожидался индекс {b.index - 1})"
            }

        # 2. Проверка собственного хэша блока
        recomputed = _recompute(b)
        if b.hash != recomputed:
            return False, {
                "index": b.index, 
                "error": f"Хэш блока не совпадает! В БД: {b.hash[:8]}..., Пересчитан: {recomputed[:8]}..."
            }
        
        # 3. Проверка связи с предыдущим блоком (не разорвана ли цепочка)
        if b.index > 0:
            prev = by_index[b.index - 1]
            if b.prev_hash != prev.hash:
                return False, {
                    "index": b.index, 
                    "error": f"Ссылка на предыдущий блок неверна! Указан: {b.prev_hash[:8]}..., Реальный: {prev.hash[:8]}..."
                }
                
    return True, None