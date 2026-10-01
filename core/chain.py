from core import Block, BlockHeader

class Chain:
    GENESIS_PREV_HASH = "0" * 64

    def __init__(self):
        self.blocks: list[Block] = []
        self._create_genesis()

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

    def get_block(self, index: int) -> Block:
        """Прочитать блок по индексу."""
        return self.blocks[index]

    def get_by_hash(self, block_hash: str) -> Block | None:
        """Прочитать блок по хешу."""
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

    def is_valid(self) -> bool:
        for i in range(1, len(self.blocks)):
            cur = self.blocks[i]
            prev = self.blocks[i - 1]
            if cur.hash != cur.compute_hash():
                return False
            if cur.header.prev_hash != prev.hash:
                return False
        return True