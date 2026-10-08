import json
import os

from core.block import Block, BlockHeader


class Chain:
    """Цепочка связанных блоков."""

    GENESIS_PREV_HASH = "0" * 64

    def __init__(self) -> None:
        self.blocks: list[Block] = []
        self._create_genesis()

    # ---------- построение ----------

    def _create_genesis(self) -> None:
        header = BlockHeader(prev_hash=self.GENESIS_PREV_HASH, type="genesis")
        genesis = Block(index=0, header=header, payload={"msg": "genesis"})
        genesis.hash = genesis.compute_hash()
        self.blocks.append(genesis)

    def add_block(self, type: str, payload: dict) -> Block:
        prev = self.blocks[-1]
        header = BlockHeader(prev_hash=prev.hash, type=type)
        block = Block(index=len(self.blocks), header=header, payload=payload)
        block.hash = block.compute_hash()
        self.blocks.append(block)
        return block

    # ---------- чтение ----------

    def get_block(self, index: int) -> Block | None:
        """Прочитать блок по индексу. None, если индекса нет."""
        if not 0 <= index < len(self.blocks):
            return None
        return self.blocks[index]

    def get_by_hash(self, block_hash: str) -> Block | None:
        """Прочитать блок по хэшу."""
        for b in self.blocks:
            if b.hash == block_hash:
                return b
        return None

    def last(self) -> Block:
        return self.blocks[-1]

    def height(self) -> int:
        return len(self.blocks) - 1

    def __len__(self) -> int:
        return len(self.blocks)

    def __iter__(self):
        return iter(self.blocks)

    # ---------- валидация ----------

    def is_valid(self) -> bool:
        if not self.blocks:
            return False

        genesis = self.blocks[0]
        if genesis.index != 0:
            return False
        if genesis.header.prev_hash != self.GENESIS_PREV_HASH:
            return False
        if genesis.hash != genesis.compute_hash():
            return False

        for i in range(1, len(self.blocks)):
            cur = self.blocks[i]
            prev = self.blocks[i - 1]
            if cur.index != prev.index + 1:
                return False
            if cur.hash != cur.compute_hash():
                return False
            if cur.header.prev_hash != prev.hash:
                return False

        return True

    # ---------- сериализация ----------

    def to_dict(self) -> dict:
        return {"blocks": [b.to_dict() for b in self.blocks]}

    def save(self, path: str, *, create_dirs: bool = True) -> None:
        """
        Сохранить цепочку в JSON.

        create_dirs=True — создать родительские директории, если их нет.
        """
        if create_dirs:
            parent = os.path.dirname(os.path.abspath(path))
            os.makedirs(parent, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "Chain":
        """Загрузить цепочку из JSON и проверить её валидность."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        blocks = [cls._block_from_dict(b) for b in data["blocks"]]
        return cls._from_blocks(blocks)

    @staticmethod
    def _block_from_dict(b: dict) -> Block:
        header = BlockHeader(
            prev_hash=b["prev_hash"],
            type=b["type"],
            timestamp=b["timestamp"],
        )
        return Block(
            index=b["index"],
            header=header,
            payload=b["payload"],
            hash=b["hash"],
        )

    @classmethod
    def _from_blocks(cls, blocks: list[Block]) -> "Chain":
        """Собрать цепочку из готовых блоков, минуя создание genesis."""
        chain = cls.__new__(cls)
        chain.blocks = blocks
        if not chain.is_valid():
            raise ValueError("Загруженная цепочка невалидна")
        return chain

    def __repr__(self) -> str:
        return f"Chain(height={self.height()})"