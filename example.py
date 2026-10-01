from core.chain import Chain
from core import tamper


def build_chain() -> Chain:
    chain = Chain()  # блок 0, genesis
    chain.add_block("data", {"from": "alice", "to": "bob",   "amount": 10})  # 1
    chain.add_block("data", {"from": "bob",   "to": "carol", "amount": 5})   # 2
    chain.add_block("data", {"from": "carol", "to": "dave",  "amount": 3})   # 3
    return chain


def print_chain(title: str, chain: Chain) -> None:
    """
    Печатает цепочку с тремя колонками:
      saved      — что лежит в поле block.hash
      recomputed — что получается из текущих данных блока
      match      — совпадают ли они
    Плюс проверка связи prev_hash == prev.hash.
    """
    print(f"\n=== {title} ===")
    print(f"{'idx':>3} | {'saved hash':<14} | {'recomputed':<14} | {'match':<6} | {'prev link':<9} | payload")
    print("-" * 110)

    for b in chain:
        saved      = b.hash
        recomputed = b.compute_hash()
        match      = "OK" if saved == recomputed else "BROKEN"

        if b.index == 0:
            prev_link = "-"
        else:
            prev = chain.get_block(b.index - 1)
            prev_link = "OK" if b.header.prev_hash == prev.hash else "BROKEN"

        print(
            f"{b.index:>3} | "
            f"{saved[:12]+'...':<14} | "
            f"{recomputed[:12]+'...':<14} | "
            f"{match:<6} | "
            f"{prev_link:<9} | "
            f"{b.payload}"
        )

    print(f"\nis_valid() = {chain.is_valid()}")


def explain(chain: Chain) -> None:
    """Объясняет, почему цепочка невалидна, если это так."""
    problems = []
    for b in chain:
        if b.hash != b.compute_hash():
            problems.append(
                f"  • блок {b.index}: saved_hash != recomputed_hash "
                f"(данные изменены, hash не пересчитан)"
            )
        if b.index > 0:
            prev = chain.get_block(b.index - 1)
            if b.header.prev_hash != prev.hash:
                problems.append(
                    f"  • блок {b.index}: prev_hash не совпадает с hash блока {prev.index}"
                )

    if problems:
        print("\nПричины, почему is_valid() = False:")
        for p in problems:
            print(p)
    else:
        print("\nВсе хеши совпадают, связи целы. Цепочка валидна.")


# ---------- сценарий ----------

original = build_chain()
print_chain("ИСХОДНАЯ ЦЕПОЧКА", original)
explain(original)

broken = build_chain()
tamper(broken, 2, {"from": "bob", "to": "carol", "amount": 999999})
print_chain("СЛОМАННАЯ ЦЕПОЧКА (испорчен блок 2, hash не пересчитан)", broken)
explain(broken)