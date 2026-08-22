from __future__ import annotations

import inspect
import json
import math
from pathlib import Path
import unittest

from pontius.h32_retained_affine_selector_cascade_direct_replay import (
    assemble_environment,
    memory_extrema,
    parse_h32_retained_affine_selector_cascade_direct_config,
    serialize_result,
)
from pontius.reporting import environment_metadata


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments/configs/h32-retained-affine-selector-cascade-direct-v1.json"
)
_IMPLEMENTATION = (
    _ROOT / "src/pontius/h32_retained_affine_selector_cascade_direct_replay.py"
)


def _memory_row(value: int) -> dict[str, int]:
    return {
        "gpu_free_bytes": value,
        "gpu_total_bytes": 1000,
        "gpu_pool_used_bytes": 100,
        "gpu_pool_total_bytes": 200 + value,
    }


class H32RetainedAffineSelectorCascadeDirectReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_complete_scientific_protocol_is_reused_without_a_wrapper(self) -> None:
        parsed = parse_h32_retained_affine_selector_cascade_direct_config(
            self.config
        )
        science = parsed["science"]
        self.assertEqual(science["primary_candidate_set"], "regret_vertex_only")
        self.assertEqual(science["gates"]["expected_candidate_rows"], 108)
        self.assertEqual(science["gates"]["expected_affine_seat_rows"], 648)
        source = _IMPLEMENTATION.read_text(encoding="utf-8")
        self.assertNotIn("science._memory_snapshot =", source)
        self.assertNotIn("gpu_physical_free_bytes", source)

    def test_raw_four_field_memory_extrema_are_consumed_directly(self) -> None:
        result = memory_extrema([_memory_row(500), _memory_row(400)])
        self.assertEqual(result["minimum_gpu_free_bytes"], 400)
        self.assertEqual(result["maximum_gpu_pool_bytes"], 700)
        variants = [
            {**_memory_row(500), "extra": 1},
            {
                key: value
                for key, value in _memory_row(500).items()
                if key != "gpu_total_bytes"
            },
            {**_memory_row(500), "gpu_physical_free_bytes": 500},
        ]
        for row in variants:
            with self.subTest(keys=sorted(row)):
                with self.assertRaisesRegex(ValueError, "memory schema differs"):
                    memory_extrema([row])

    def test_environment_api_and_explicit_merge_are_exact(self) -> None:
        self.assertEqual(tuple(inspect.signature(environment_metadata).parameters), ())
        result = assemble_environment(
            {"python": "3.x", "platform": "test", "git": {"dirty": True}},
            {"cuda": "13.2"},
            {"commit": "abc", "dirty": False},
        )
        self.assertEqual(
            result,
            {
                "python": "3.x",
                "platform": "test",
                "cuda": "13.2",
                "git": {"commit": "abc", "dirty": False},
            },
        )

    def test_exact_serializer_accepts_finite_and_rejects_nan(self) -> None:
        serialized = serialize_result({"passed": True, "value": 1.0})
        self.assertEqual(json.loads(serialized), {"passed": True, "value": 1.0})
        with self.assertRaises(ValueError):
            serialize_result({"value": math.nan})

    def test_config_and_source_mutations_are_rejected(self) -> None:
        changed = dict(self.config)
        changed["memory_rule"] = "use_alias"
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_retained_affine_selector_cascade_direct_config(changed)

        changed = dict(self.config)
        changed["expected_reporting_helper_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_retained_affine_selector_cascade_direct_config(changed)


if __name__ == "__main__":
    unittest.main()
