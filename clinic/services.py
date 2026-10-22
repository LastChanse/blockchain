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
    """
    Формирует представление (view-model) для блокчейн-записей.
    Выполняет валидацию целостности цепочки (проверка хэшей и связей).
    """
    
    # 1. Загрузка данных
    if patient:
        # Если запрошен конкретный пациент, берем только его цепочку
        blocks = list_blocks(patient)
    else:
        # Если пациент не указан (глобальный обзор), загружаем все блоки.
        # Сортировка по patient_id критически важна для дальнейшей группировки.
        blocks = list(ChainBlock.objects.all().order_by("patient_id", "index"))
        
    # 2. Индексация блоков по цепочкам (критически важный шаг)
    # В блокчейне у каждого пациента своя независимая цепочка, начинающаяся с index=0.
    # Если создать плоский словарь {index: block}, блоки с одинаковым индексом
    # от разных пациентов перезапишут друг друга. Поэтому используем вложенный словарь:
    # { patient_id: { block_index: block_object } }
    by_patient = {}
    for b in blocks:
        if b.patient_id not in by_patient:
            by_patient[b.patient_id] = {}
        by_patient[b.patient_id][b.index] = b

    records = []
    for b in blocks:
        # Нас интересуют только блоки с медицинскими записями (пропускаем genesis и пр.)
        if b.type != "medical_record":
            continue
            
        # 3. Проверка целостности самого блока (Proof of Work / Content Hash)
        # Пересчитываем хэш на основе текущих данных в БД и сравниваем с сохраненным.
        # Если данные в payload были изменены в обход блокчейна, хэши не совпадут.
        recomputed = _recompute(b)
        match = "OK" if b.hash == recomputed else "BROKEN"
        
        # 4. Проверка связности цепочки (Chain Link validation)
        if b.index == 0:
            # Genesis-блок не имеет предыдущего
            prev_link = "-"
        else:
            # Ищем предыдущий блок СТРОГО в рамках цепочки текущего пациента.
            # Благодаря структуре by_patient, мы гарантированно не наткнемся 
            # на блок с таким же индексом, но от другого пациента.
            prev = by_patient[b.patient_id].get(b.index - 1)
            
            # Проверяем, что ссылка на предыдущий хэш в текущем блоке 
            # совпадает с реальным хэшем предыдущего блока.
            prev_link = "OK" if prev and b.prev_hash == prev.hash else "BROKEN"
            
        # 5. Формирование плоской структуры для шаблона (View DTO)
        records.append({
            "patient_name": b.payload.get("patient_name"),
            "diagnosis": b.payload.get("diagnosis"),
            "index": b.index,
            "hash_short": f"{b.hash[:12]}...",           # Для компактного отображения в UI
            "hash_full": b.hash,                         # Для tooltip или детальной страницы
            "recomputed_short": f"{recomputed[:12]}...", # Показать, каким хэш должен быть
            "match": match,                              # Статус целостности содержимого
            "prev_link": prev_link,                      # Статус связности с предыдущим блоком
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