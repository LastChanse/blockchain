import unittest

from core import Block, BlockHeader


FIXED_TS = "2025-01-01T00:00:00+00:00"


def make_header(prev_hash: str = "a" * 64, type: str = "tx") -> BlockHeader:
    return BlockHeader(prev_hash=prev_hash, type=type, timestamp=FIXED_TS)


class TestBlockHash(unittest.TestCase):
    def _make_block(self, **overrides) -> Block:
        defaults = dict(
            index=1,
            header=make_header(),
            payload={"msg": "hello"},
        )
        defaults.update(overrides)
        return Block(**defaults)

    def test_compute_hash_is_deterministic(self):
        b1 = self._make_block()
        b2 = self._make_block()
        self.assertEqual(b1.compute_hash(), b2.compute_hash())

    def test_hash_changes_with_payload(self):
        b1 = self._make_block(payload={"msg": "hello"})
        b2 = self._make_block(payload={"msg": "other"})
        self.assertNotEqual(b1.compute_hash(), b2.compute_hash())

    def test_hash_changes_with_prev_hash(self):
        b1 = self._make_block(header=make_header(prev_hash="a" * 64))
        b2 = self._make_block(header=make_header(prev_hash="b" * 64))
        self.assertNotEqual(b1.compute_hash(), b2.compute_hash())

    def test_hash_changes_with_index(self):
        b1 = self._make_block(index=1)
        b2 = self._make_block(index=2)
        self.assertNotEqual(b1.compute_hash(), b2.compute_hash())

    def test_hash_changes_with_type(self):
        b1 = self._make_block(header=make_header(type="tx"))
        b2 = self._make_block(header=make_header(type="genesis"))
        self.assertNotEqual(b1.compute_hash(), b2.compute_hash())

    def test_hash_changes_with_timestamp(self):
        h1 = BlockHeader(prev_hash="a" * 64, type="tx", timestamp="2025-01-01T00:00:00+00:00")
        h2 = BlockHeader(prev_hash="a" * 64, type="tx", timestamp="2025-01-02T00:00:00+00:00")
        b1 = Block(index=1, header=h1, payload={"x": 1})
        b2 = Block(index=1, header=h2, payload={"x": 1})
        self.assertNotEqual(b1.compute_hash(), b2.compute_hash())

    def test_hash_does_not_include_hash_field(self):
        b = self._make_block()
        h_before = b.compute_hash()
        b.hash = "deadbeef" * 8
        self.assertEqual(h_before, b.compute_hash())

    def test_hash_is_hex_sha256(self):
        h = self._make_block().compute_hash()
        self.assertEqual(len(h), 64)
        int(h, 16)  # не должно упасть

    def test_hash_is_order_independent_of_payload_keys(self):
        b1 = self._make_block(payload={"a": 1, "b": 2})
        b2 = self._make_block(payload={"b": 2, "a": 1})
        self.assertEqual(b1.compute_hash(), b2.compute_hash())

    def test_hash_normalizes_non_string_keys(self):
        b1 = self._make_block(payload={1: "x", "1": "y"})
        b2 = self._make_block(payload={"1": "y"})
        self.assertEqual(b1.compute_hash(), b2.compute_hash())

    def test_hash_is_stable_for_nested_structures(self):
        b1 = self._make_block(payload={"outer": {"b": 2, "a": 1}, "list": [{"y": 1, "x": 2}]})
        b2 = self._make_block(payload={"list": [{"x": 2, "y": 1}], "outer": {"a": 1, "b": 2}})
        self.assertEqual(b1.compute_hash(), b2.compute_hash())


class TestBlockSerialization(unittest.TestCase):
    def test_to_dict_contains_expected_keys(self):
        b = Block(
            index=1,
            header=make_header(),
            payload={"msg": "hello"},
            hash="f" * 64,
        )
        d = b.to_dict()
        self.assertEqual(
            set(d.keys()),
            {"index", "prev_hash", "type", "timestamp", "payload", "hash"},
        )
        self.assertEqual(d["index"], 1)
        self.assertEqual(d["prev_hash"], "a" * 64)
        self.assertEqual(d["type"], "tx")
        self.assertEqual(d["payload"], {"msg": "hello"})
        self.assertEqual(d["hash"], "f" * 64)
        self.assertEqual(d["timestamp"], FIXED_TS)

    def test_repr_is_compact(self):
        b = Block(
            index=1,
            header=make_header(),
            payload={"msg": "hello"},
            hash="f" * 64,
        )
        r = repr(b)
        self.assertIn("index=1", r)
        self.assertIn("type='tx'", r)
        self.assertIn("ffffffff", r)


class TestBlockHeader(unittest.TestCase):
    def test_timestamp_auto_generated(self):
        h = BlockHeader(prev_hash="a" * 64, type="tx")
        self.assertTrue(h.timestamp)

    def test_timestamp_can_be_overridden(self):
        h = BlockHeader(prev_hash="a" * 64, type="tx", timestamp=FIXED_TS)
        self.assertEqual(h.timestamp, FIXED_TS)

    def test_repr(self):
        h = BlockHeader(prev_hash="a" * 64, type="tx", timestamp=FIXED_TS)
        self.assertIn("type='tx'", repr(h))
        self.assertIn("aaaaaaaa", repr(h))


if __name__ == "__main__":
    unittest.main()