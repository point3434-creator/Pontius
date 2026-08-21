from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_shared_response_residency_replay import (
    _descriptor_core,
    parse_h32_shared_response_residency_config,
)


_ROOT = Path(__file__).parents[1]


class H32SharedResponseResidencyReplayTests(unittest.TestCase):
    def test_frozen_config_rejects_workload_source_and_gate_mutations(self) -> None:
        config = json.loads(
            (_ROOT / "experiments/configs/h32-shared-response-residency-replay-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(parse_h32_shared_response_residency_config(config), config)
        for field, value in (
            ("range_family", "blocker_heavy"),
            ("expected_atomic_result_sha256", "0" * 64),
        ):
            mutated = dict(config)
            mutated[field] = value
            with self.assertRaises(ValueError):
                parse_h32_shared_response_residency_config(mutated)
        mutated = json.loads(json.dumps(config))
        mutated["gates"]["maximum_utility_error"] = 1e-6
        with self.assertRaisesRegex(ValueError, "gates differ"):
            parse_h32_shared_response_residency_config(mutated)

    def test_descriptor_core_excludes_measurement_fields_only(self) -> None:
        descriptor = {
            "shift": "fixed",
            "selected_seat": 3,
            "source_partition": 1.0,
            "target_partition": 2.0,
            "marginal_measurement_ms": 3.0,
        }
        self.assertEqual(
            _descriptor_core(descriptor),
            {"shift": "fixed", "selected_seat": 3},
        )


if __name__ == "__main__":
    unittest.main()
