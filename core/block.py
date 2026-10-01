import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class BlockHeader:
    """
    Заголовок блока.
    Поля из ТЗ: type, schema_version, merkle_root, anchor_ref.
    Пока используются как есть — логика под них появится позже.
    """
    prev_hash: str
    type: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class Block:
    """
    Блок = заголовок + payload + подписи.
    Хеш считается от заголовка и payload, поле hash НЕ входит в расчёт.
    """
    index: int
    header: BlockHeader
    payload: dict
    hash: str = ""

    def compute_hash(self) -> str:
        body = {
            "index": self.index,
            "prev_hash": self.header.prev_hash,
            "type": self.header.type,
            "timestamp": self.header.timestamp,
            "payload": self.payload,
        }
        raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "prev_hash": self.header.prev_hash,
            "type": self.header.type,
            "timestamp": self.header.timestamp,
            "payload": self.payload,
            "hash": self.hash,
        }