from .chain import Chain
from .block import Block


def tamper(chain: Chain, index: int, new_payload: dict) -> Block:
    """
    Тестовый метод: вмешаться в payload блока.
    Хеш НЕ пересчитываем — так и увидим, что он поехал.
    Возвращает испорченный блок.
    """
    block = chain.blocks[index]
    block.payload = new_payload
    return block


def dump_hashes(chain: Chain) -> list[dict]:
    """
    Удобно для отладки: показывает для каждого блока
    сохранённый хеш и пересчитанный.
    Если они разные — блок испорчен.
    """
    out = []
    for b in chain:
        out.append({
            "index": b.index,
            "type": b.header.type,
            "saved_hash": b.hash,
            "recomputed_hash": b.compute_hash(),
            "ok": b.hash == b.compute_hash(),
        })
    return out