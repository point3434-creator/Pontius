from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_retained_affine_selector_cascade_replay_v3 import (
    _memory_snapshot_alias,
    parse_h32_retained_affine_selector_cascade_v3_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments/configs/h32-retained-affine-selector-cascade-replay-v3.json"
)


class H32RetainedAffineSelectorCascadeReplayV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_complete_v1_scientific_protocol_is_reused(self) -> None:
        parsed = parse_h32_retained_affine_selector_cascade_v3_config(self.config)
        base = parsed["v1_base"]
        self.assertEqual(base["primary_candidate_set"], "regret_vertex_only")
        self.assertEqual(base["gates"]["expected_candidate_rows"], 108)
        self.assertEqual(base["gates"]["expected_affine_seat_rows"], 648)
        self.assertEqual(
            parsed["source_memory_schema"],
            [
                "gpu_free_bytes",
                "gpu_pool_total_bytes",
                "gpu_pool_used_bytes",
                "gpu_total_bytes",
            ],
        )

    def test_alias_preserves_all_four_fields_and_adds_only_one(self) -> None:
        source = {
            "gpu_free_bytes": 100,
            "gpu_total_bytes": 200,
            "gpu_pool_used_bytes": 30,
            "gpu_pool_total_bytes": 40,
        }
        corrected = _memory_snapshot_alias(lambda _cp: source)(object())
        self.assertEqual(set(source), set(corrected) - {"gpu_physical_free_bytes"})
        self.assertEqual(
            {key: corrected[key] for key in source},
            source,
        )
        self.assertEqual(corrected["gpu_physical_free_bytes"], source["gpu_free_bytes"])

    def test_alias_rejects_missing_extra_or_preexisting_alias_fields(self) -> None:
        valid = {
            "gpu_free_bytes": 100,
            "gpu_total_bytes": 200,
            "gpu_pool_used_bytes": 30,
            "gpu_pool_total_bytes": 40,
        }
        variants = [
            {key: value for key, value in valid.items() if key != "gpu_total_bytes"},
            {**valid, "extra": 1},
            {**valid, "gpu_physical_free_bytes": 100},
        ]
        for source in variants:
            with self.subTest(keys=sorted(source)):
                corrected = _memory_snapshot_alias(lambda _cp, row=source: row)
                with self.assertRaisesRegex(ValueError, "wrong memory schema"):
                    corrected(object())

    def test_config_and_source_mutations_are_rejected(self) -> None:
        changed = dict(self.config)
        changed["source_memory_schema"] = ["gpu_free_bytes"]
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_retained_affine_selector_cascade_v3_config(changed)

        changed = dict(self.config)
        changed["expected_memory_helper_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_retained_affine_selector_cascade_v3_config(changed)


if __name__ == "__main__":
    unittest.main()
