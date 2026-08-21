from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.evidence_protocol import DEFAULT_GPU_NUMERICAL_IDENTITY
from pontius.h32_fresh_selector_stable_affine_street_audit import (
    _digest_absent_at_commit,
    _start_allowed,
    parse_h32_fresh_selector_stable_affine_street_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT / "experiments/configs/h32-fresh-selector-stable-affine-street-v1.json"
)


class H32FreshSelectorStableAffineStreetAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_fresh_panel_and_fixed_live_rule_are_exact(self) -> None:
        parsed = parse_h32_fresh_selector_stable_affine_street_config(self.config)
        self.assertEqual(len(parsed["targets"]), 4)
        self.assertEqual(parsed["target_seat"], 0)
        self.assertEqual(parsed["acting_seat"], 0)
        self.assertEqual(parsed["direction_family"], "regret_vertex")
        self.assertEqual(parsed["candidate_ready_cutoff_ms"], 14000.0)
        self.assertEqual(parsed["post_step_candidate_proof_guard_ms"], 1000.0)
        self.assertEqual(parsed["post_construction_affine_guard_ms"], 500.0)
        self.assertEqual(
            parsed["maximum_warm_start_probability_error"],
            DEFAULT_GPU_NUMERICAL_IDENTITY.maximum_policy_probability_error,
        )
        self.assertNotIn("require_warm_start_digest_identity", parsed)
        self.assertNotIn("minimum_live_non_blueprint_emissions", parsed["gates"])
        self.assertNotIn("minimum_certified_value", parsed["gates"])

    def test_fresh_hashes_are_absent_from_the_sealed_base_commit(self) -> None:
        parsed = parse_h32_fresh_selector_stable_affine_street_config(self.config)
        for target in parsed["targets"]:
            self.assertTrue(
                _digest_absent_at_commit(
                    target["target_belief_sha256"],
                    parsed["freshness_base_commit"],
                )
            )
            self.assertTrue(
                _digest_absent_at_commit(
                    target["target_descriptor_sha256"],
                    parsed["freshness_base_commit"],
                )
            )

    def test_deadline_start_guards_include_the_emission_reserve(self) -> None:
        self.assertTrue(
            _start_allowed(
                12999.0,
                work_guard_ms=1000.0,
                emission_reserve_ms=1000.0,
                street_budget_ms=15000.0,
            )
        )
        self.assertFalse(
            _start_allowed(
                13000.1,
                work_guard_ms=1000.0,
                emission_reserve_ms=1000.0,
                street_budget_ms=15000.0,
            )
        )
        self.assertTrue(
            _start_allowed(
                13500.0,
                work_guard_ms=500.0,
                emission_reserve_ms=1000.0,
                street_budget_ms=15000.0,
            )
        )

    def test_outcome_and_hash_mutations_are_rejected(self) -> None:
        changed = json.loads(json.dumps(self.config))
        changed["post_construction_affine_guard_ms"] = 750.0
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_fresh_selector_stable_affine_street_config(changed)

        changed = json.loads(json.dumps(self.config))
        changed["gates"]["minimum_live_non_blueprint_emissions"] = 1
        with self.assertRaisesRegex(ValueError, "gates differ"):
            parse_h32_fresh_selector_stable_affine_street_config(changed)

        changed = json.loads(json.dumps(self.config))
        changed["expected_affine_verifier_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_fresh_selector_stable_affine_street_config(changed)


if __name__ == "__main__":
    unittest.main()
