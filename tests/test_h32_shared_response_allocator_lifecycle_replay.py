from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_shared_response_allocator_lifecycle_replay import (
    _manifest_digest,
    _pointer_manifest,
    parse_h32_shared_response_allocator_lifecycle_config,
)


_ROOT = Path(__file__).parents[1]


class _Pointer:
    def __init__(self, ptr: int) -> None:
        self.ptr = ptr


class _Array:
    def __init__(self, ptr: int, nbytes: int) -> None:
        self.data = _Pointer(ptr)
        self.nbytes = nbytes


class H32SharedResponseAllocatorLifecycleTests(unittest.TestCase):
    def test_config_rejects_workload_source_and_gate_mutations(self) -> None:
        config = json.loads(
            (_ROOT / "experiments/configs/h32-shared-response-allocator-lifecycle-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            parse_h32_shared_response_allocator_lifecycle_config(config), config
        )
        for field, value in (
            ("replay_order", "target_shift_outer_then_acting_seat"),
            ("expected_residency_result_sha256", "0" * 64),
        ):
            mutated = dict(config)
            mutated[field] = value
            with self.assertRaises(ValueError):
                parse_h32_shared_response_allocator_lifecycle_config(mutated)
        mutated = json.loads(json.dumps(config))
        mutated["gates"]["minimum_physical_free_bytes"] = 1
        with self.assertRaisesRegex(ValueError, "gates differ"):
            parse_h32_shared_response_allocator_lifecycle_config(mutated)

    def test_pointer_manifest_binds_names_addresses_and_widths(self) -> None:
        arrays = {"right": _Array(22, 8), "left": _Array(11, 16)}
        manifest = _pointer_manifest(arrays)
        self.assertEqual(manifest, {"left": (11, 16), "right": (22, 8)})
        self.assertEqual(_manifest_digest(manifest), _manifest_digest(dict(manifest)))
        changed = dict(manifest)
        changed["left"] = (12, 16)
        self.assertNotEqual(_manifest_digest(manifest), _manifest_digest(changed))


if __name__ == "__main__":
    unittest.main()
