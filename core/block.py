import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone


def canonical_json(obj) -> str:
    """
    Каноничное JSON-представление для подсчёта хэша.

    Правила:
      - ключи приводятся к строкам и сортируются лексикографически (рекурсивно);
      - без пробелов (separators=(",", ":"));
      - не-ASCII не экранируется (ensure_ascii=False);
      - NaN/Infinity запрещены (allow_nan=False).
    """
    def _normalize(value):
        if isinstance(value, dict):
            return {str(k): _normalize(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [_normalize(v) for v in value]
        return value

    return json.dumps(
        _normalize(obj),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


@dataclass
class BlockHeader:
    """
    Заголовок блока.

    Поля из ТЗ: type, schema_version, merkle_root, anchor_ref.
    Пока используются как есть — логика под них появится позже.
    """

    prev_hash: str
    type: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __repr__(self) -> str:
        return (
            f"BlockHeader(type={self.type!r}, "
            f"prev_hash={self.prev_hash[:8]}…, "
            f"timestamp={self.timestamp})"
        )


@dataclass
class Block:
    """
    Блок = заголовок + payload + подписи.

    Хэш считается от заголовка и payload, поле hash НЕ входит в расчёт.
    """

    index: int
    header: BlockHeader
    payload: dict
    hash: str = ""

    def _hashable_body(self) -> dict:
        """Каноничное представление блока для подсчёта хэша."""
        return {
            "index": self.index,
            "prev_hash": self.header.prev_hash,
            "type": self.header.type,
            "timestamp": self.header.timestamp,
            "payload": self.payload,
        }

    def compute_hash(self) -> str:
        raw = canonical_json(self._hashable_body()).encode("utf-8")
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

    def __repr__(self) -> str:
        short_hash = self.hash[:8] if self.hash else "<no-hash>"
        return (
            f"Block(index={self.index}, type={self.header.type!r}, "
            f"hash={short_hash}…)"
        )