from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_atomic_street_scheduler_audit import (
    may_start_certificate,
    parse_h32_atomic_street_scheduler_config,
)


_ROOT = Path(__file__).parents[1]


class H32AtomicStreetSchedulerTests(unittest.TestCase):
    def test_config_rejects_clock_source_and_gate_mutations(self) -> None:
        config = json.loads(
            (_ROOT / "experiments/configs/h32-atomic-street-scheduler-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(parse_h32_atomic_street_scheduler_config(config), config)
        for field, value in (
            ("certificate_start_reserve_ms", 1000.0),
            ("expected_lifecycle_result_sha256", "0" * 64),
        ):
            mutated = dict(config)
            mutated[field] = value
            with self.assertRaises(ValueError):
                parse_h32_atomic_street_scheduler_config(mutated)
        mutated = json.loads(json.dumps(config))
        mutated["gates"]["maximum_candidate_probability_error"] = 1e-6
        with self.assertRaisesRegex(ValueError, "gates differ"):
            parse_h32_atomic_street_scheduler_config(mutated)

    def test_certificate_start_guard_preserves_emission_cutoff(self) -> None:
        common = {
            "decision_budget_ms": 15000.0,
            "emission_reserve_ms": 1000.0,
            "certificate_start_reserve_ms": 1250.0,
        }
        self.assertTrue(may_start_certificate(elapsed_ms=12750.0, **common))
        self.assertFalse(may_start_certificate(elapsed_ms=12750.0001, **common))
        with self.assertRaisesRegex(ValueError, "finite and nonnegative"):
            may_start_certificate(elapsed_ms=-1.0, **common)


if __name__ == "__main__":
    unittest.main()
