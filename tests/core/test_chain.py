import json
import os
import tempfile
import unittest

from core import Chain


class TestChainBasic(unittest.TestCase):
    def test_genesis_created_on_init(self):
        chain = Chain()
        self.assertEqual(len(chain), 1)
        self.assertEqual(chain.height(), 0)

        genesis = chain.get_block(0)
        self.assertIsNotNone(genesis)
        self.assertEqual(genesis.index, 0)
        self.assertEqual(genesis.header.prev_hash, Chain.GENESIS_PREV_HASH)
        self.assertEqual(genesis.header.type, "genesis")
        self.assertEqual(genesis.hash, genesis.compute_hash())

    def test_add_block_links_to_previous(self):
        chain = Chain()
        prev = chain.last()
        block = chain.add_block(type="tx", payload={"amount": 10})
        self.assertEqual(block.index, 1)
        self.assertEqual(block.header.prev_hash, prev.hash)
        self.assertEqual(block.hash, block.compute_hash())
        self.assertEqual(chain.height(), 1)
        self.assertEqual(len(chain), 2)

    def test_add_multiple_blocks_chains_hashes(self):
        chain = Chain()
        b1 = chain.add_block(type="tx", payload={"x": 1})
        b2 = chain.add_block(type="tx", payload={"x": 2})
        self.assertEqual(b2.header.prev_hash, b1.hash)
        self.assertEqual(b2.index, 2)

    def test_get_block_by_index(self):
        chain = Chain()
        b = chain.add_block(type="tx", payload={"x": 1})
        self.assertIs(chain.get_block(1), b)

    def test_get_block_out_of_range_returns_none(self):
        chain = Chain()
        self.assertIsNone(chain.get_block(999))
        self.assertIsNone(chain.get_block(-1))

    def test_get_by_hash(self):
        chain = Chain()
        b = chain.add_block(type="tx", payload={"x": 1})
        self.assertIs(chain.get_by_hash(b.hash), b)
        self.assertIsNone(chain.get_by_hash("0" * 64))

    def test_last_and_height(self):
        chain = Chain()
        b = chain.add_block(type="tx", payload={"x": 1})
        self.assertIs(chain.last(), b)
        self.assertEqual(chain.height(), 1)

    def test_iter_yields_all_blocks(self):
        chain = Chain()
        chain.add_block(type="tx", payload={"x": 1})
        chain.add_block(type="tx", payload={"x": 2})
        self.assertEqual([b.index for b in chain], [0, 1, 2])

    def test_repr(self):
        chain = Chain()
        chain.add_block(type="tx", payload={"x": 1})
        self.assertIn("height=1", repr(chain))


class TestChainValidity(unittest.TestCase):
    # ---------- общие ----------

    def test_fresh_chain_is_valid(self):
        chain = Chain()
        chain.add_block(type="tx", payload={"x": 1})
        self.assertTrue(chain.is_valid())

    def test_empty_chain_is_invalid(self):
        chain = Chain.__new__(Chain)
        chain.blocks = []
        self.assertFalse(chain.is_valid())

    # ---------- genesis ----------

    def test_genesis_with_wrong_index_invalidates_chain(self):
        chain = Chain()
        chain.blocks[0].index = 1
        self.assertFalse(chain.is_valid())

    def test_genesis_with_wrong_prev_hash_invalidates_chain(self):
        chain = Chain()
        chain.blocks[0].header.prev_hash = "f" * 64
        self.assertFalse(chain.is_valid())

    def test_tampered_genesis_hash_invalidates_chain(self):
        chain = Chain()
        chain.blocks[0].hash = "f" * 64
        self.assertFalse(chain.is_valid())

    def test_tampered_genesis_payload_invalidates_chain(self):
        chain = Chain()
        chain.blocks[0].payload["msg"] = "hacked"
        self.assertFalse(chain.is_valid())

    # ---------- обычные блоки ----------

    def test_tampered_payload_invalidates_chain(self):
        chain = Chain()
        chain.add_block(type="tx", payload={"x": 1})
        chain.blocks[1].payload["x"] = 999
        self.assertFalse(chain.is_valid())

    def test_tampered_hash_invalidates_chain(self):
        chain = Chain()
        chain.add_block(type="tx", payload={"x": 1})
        chain.blocks[1].hash = "f" * 64
        self.assertFalse(chain.is_valid())

    def test_broken_index_sequence_invalidates_chain(self):
        chain = Chain()
        chain.add_block(type="tx", payload={"x": 1})
        chain.blocks[1].index = 5
        # пересчитываем хэш, чтобы изолировать проверку порядка индексов
        chain.blocks[1].hash = chain.blocks[1].compute_hash()
        self.assertFalse(chain.is_valid())

    def test_broken_link_invalidates_chain(self):
        chain = Chain()
        chain.add_block(type="tx", payload={"x": 1})
        chain.blocks[1].header.prev_hash = "f" * 64
        # пересчитываем хэш, чтобы изолировать проверку связи
        chain.blocks[1].hash = chain.blocks[1].compute_hash()
        self.assertFalse(chain.is_valid())

    def test_same_index_repeated_invalidates_chain(self):
        chain = Chain()
        chain.add_block(type="tx", payload={"x": 1})
        chain.add_block(type="tx", payload={"x": 2})
        chain.blocks[2].index = 1
        chain.blocks[2].hash = chain.blocks[2].compute_hash()
        self.assertFalse(chain.is_valid())


class TestChainPersistence(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmpdir.name, "chain.json")

    def tearDown(self):
        self._tmpdir.cleanup()

    def _build_chain(self) -> Chain:
        chain = Chain()
        chain.add_block(type="tx", payload={"amount": 10})
        chain.add_block(type="tx", payload={"amount": 20})
        return chain

    # ---------- save ----------

    def test_save_writes_valid_json(self):
        chain = self._build_chain()
        chain.save(self.path)
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("blocks", data)
        self.assertEqual(len(data["blocks"]), 3)
        self.assertEqual(data["blocks"][0]["type"], "genesis")

    def test_save_creates_parent_dirs(self):
        nested = os.path.join(self._tmpdir.name, "a", "b", "chain.json")
        chain = self._build_chain()
        chain.save(nested)
        self.assertTrue(os.path.exists(nested))

    def test_save_without_create_dirs_raises_on_missing_parent(self):
        nested = os.path.join(self._tmpdir.name, "missing", "chain.json")
        chain = self._build_chain()
        with self.assertRaises(FileNotFoundError):
            chain.save(nested, create_dirs=False)

    # ---------- load: happy path ----------

    def test_roundtrip_preserves_chain(self):
        original = self._build_chain()
        original.save(self.path)

        loaded = Chain.load(self.path)

        self.assertEqual(len(loaded), len(original))
        self.assertEqual(loaded.height(), original.height())
        self.assertTrue(loaded.is_valid())
        for a, b in zip(original, loaded):
            self.assertEqual(a.index, b.index)
            self.assertEqual(a.hash, b.hash)
            self.assertEqual(a.header.prev_hash, b.header.prev_hash)
            self.assertEqual(a.header.type, b.header.type)
            self.assertEqual(a.header.timestamp, b.header.timestamp)
            self.assertEqual(a.payload, b.payload)

    def test_load_does_not_recreate_genesis(self):
        original = self._build_chain()
        original.save(self.path)

        loaded = Chain.load(self.path)

        self.assertEqual(loaded.get_block(0).header.type, "genesis")
        self.assertEqual(len(loaded), 3)

    # ---------- load: negative ----------

    def test_load_rejects_tampered_payload(self):
        chain = self._build_chain()
        chain.save(self.path)

        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        data["blocks"][1]["payload"]["amount"] = 999
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        with self.assertRaises(ValueError):
            Chain.load(self.path)

    def test_load_rejects_missing_blocks_key(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"nope": []}, f)
        with self.assertRaises(KeyError):
            Chain.load(self.path)

    def test_load_rejects_empty_blocks(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"blocks": []}, f)
        with self.assertRaises(ValueError):
            Chain.load(self.path)

    def test_load_rejects_tampered_link(self):
        chain = self._build_chain()
        chain.save(self.path)

        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        data["blocks"][1]["prev_hash"] = "f" * 64
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        with self.assertRaises(ValueError):
            Chain.load(self.path)


if __name__ == "__main__":
    unittest.main()