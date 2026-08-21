from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_fresh_selector_stable_affine_street_audit import (
    _digest_absent_at_commit,
)
from pontius.h32_fresh_selector_stable_affine_street_seat5_audit import (
    _rename_seat5_candidate_ids,
    parse_h32_fresh_selector_stable_affine_street_seat5_config,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments/configs/h32-fresh-selector-stable-affine-street-seat5-v1.json"
)


class H32FreshSelectorStableAffineStreetSeat5AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_only_target_and_acting_seats_change_from_the_live_core(self) -> None:
        parsed = parse_h32_fresh_selector_stable_affine_street_seat5_config(
            self.config
        )
        base = parsed["seat0_base"]
        self.assertEqual(parsed["target_seat"], 4)
        self.assertEqual(parsed["acting_seat"], 5)
        self.assertEqual(len(parsed["targets"]), 4)
        for field in (
            "solver_variant",
            "warm_regret_mass_payoff_fraction",
            "direction_family",
            "selector_margin_allowance",
            "envelope_numerical_allowance",
            "safety_fraction",
            "numerical_floor",
            "street_budget_ms",
            "emission_reserve_ms",
            "candidate_ready_cutoff_ms",
            "post_step_candidate_proof_guard_ms",
            "post_construction_affine_guard_ms",
            "gates",
        ):
            self.assertEqual(parsed[field], base[field])

    def test_fresh_hashes_are_absent_from_the_sealed_seat0_result_commit(self) -> None:
        parsed = parse_h32_fresh_selector_stable_affine_street_seat5_config(
            self.config
        )
        for target in parsed["targets"]:
            for field in ("target_belief_sha256", "target_descriptor_sha256"):
                self.assertTrue(
                    _digest_absent_at_commit(
                        target[field],
                        parsed["freshness_base_commit"],
                    )
                )

    def test_inherited_descriptive_candidate_ids_are_renamed(self) -> None:
        result = {
            "target_rows": [
                {
                    "live": {"emitted_candidate_id": "seat0_regret_vertex_affine"},
                    "block": {
                        "selected_validation": {
                            "direct": {"candidate_id": "seat0_regret_vertex_affine_teacher"}
                        }
                    },
                },
                {
                    "live": {"emitted_candidate_id": "blueprint_average64"},
                    "block": {"selected_validation": None},
                },
            ]
        }
        _rename_seat5_candidate_ids(result)
        self.assertEqual(
            result["target_rows"][0]["live"]["emitted_candidate_id"],
            "seat5_regret_vertex_affine",
        )
        self.assertEqual(
            result["target_rows"][0]["block"]["selected_validation"]["direct"][
                "candidate_id"
            ],
            "seat5_regret_vertex_affine_teacher",
        )
        self.assertEqual(
            result["target_rows"][1]["live"]["emitted_candidate_id"],
            "blueprint_average64",
        )

    def test_outcome_and_source_mutations_are_rejected(self) -> None:
        changed = dict(self.config)
        changed["acting_seat"] = 4
        with self.assertRaisesRegex(ValueError, "workload differs"):
            parse_h32_fresh_selector_stable_affine_street_seat5_config(changed)

        changed = dict(self.config)
        changed["expected_seat0_result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            parse_h32_fresh_selector_stable_affine_street_seat5_config(changed)


if __name__ == "__main__":
    unittest.main()
