from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

from pontius.atomic_json_checkpoint import write_atomic_json_checkpoint


class AtomicJsonCheckpointTests(unittest.TestCase):
    def test_digest_names_persisted_lf_bytes_and_replace_is_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            first = write_atomic_json_checkpoint({"attempted": 1}, path)
            second = write_atomic_json_checkpoint({"attempted": 2}, path)
            raw = path.read_bytes()

            self.assertNotEqual(first, second)
            self.assertEqual(second, hashlib.sha256(raw).hexdigest())
            self.assertNotIn(b"\r\n", raw)
            self.assertTrue(raw.endswith(b"\n"))
            self.assertEqual(json.loads(raw)["attempted"], 2)
            self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_nonfinite_payload_fails_before_creating_a_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            with self.assertRaises(ValueError):
                write_atomic_json_checkpoint({"bad": math.nan}, path)
            self.assertFalse(path.exists())
            self.assertFalse(path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
