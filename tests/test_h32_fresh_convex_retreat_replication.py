from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from pontius.h32_fresh_convex_retreat_replication import (
    FreshCandidateBarrier,
    _parse_config,
    fresh_replication_promotion,
)


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "experiments/configs/h32-fresh-convex-retreat-replication-v1.json"
IMPLEMENTATION = ROOT / "src/pontius/h32_fresh_convex_retreat_replication.py"


def _target_row(
    target_id: str,
    family: str,
    value: float,
    *,
    accepted: bool = True,
    measured_fit: bool = True,
    conservative_fit: bool = True,
) -> dict[str, object]:
    return {
        "target_id": target_id,
        "range_family": family,
        "retreat": {
            "shadow_accepted": accepted,
            "exact_positive_value": value,
        },
        "ledger": {
            "fits_measured_street": measured_fit,
            "fits_effective_conservative_street": conservative_fit,
        },
    }


class H32FreshConvexRetreatReplicationTests(unittest.TestCase):
    def test_candidate_barrier_fails_closed_before_strategy_label(self) -> None:
        barrier = FreshCandidateBarrier("target")
        with self.assertRaisesRegex(RuntimeError, "changed before label"):
            barrier.freeze_candidate({"identity": True, "projection": False})
        self.assertEqual(barrier.phase, "inputs_pinned")

        barrier = FreshCandidateBarrier("target")
        barrier.freeze_candidate({"identity": True, "projection": True})
        barrier.complete_retreat_certificate()
        self.assertEqual(
            barrier.events,
            [
                "inputs_pinned",
                "candidate_frozen",
                "retreat_certificate_complete",
            ],
        )
        with self.assertRaisesRegex(RuntimeError, "frozen candidate"):
            FreshCandidateBarrier("other").complete_retreat_certificate()

    def test_promotion_requires_material_breadth_and_every_schedule(self) -> None:
        rows = [
            _target_row("b0", "balanced", 0.002),
            _target_row("b1", "balanced", 0.003),
            _target_row("k0", "blocker_heavy", 0.004),
            _target_row("k1", "blocker_heavy", 0.005),
            _target_row("small", "balanced", 0.001),
            _target_row("rejected", "blocker_heavy", 1.0, accepted=False),
        ]
        promotion = fresh_replication_promotion(
            rows,
            minimum_material_targets=4,
            minimum_material_exact_value=0.001,
        )
        self.assertEqual(promotion["material_target_count"], 4)
        self.assertTrue(promotion["both_range_families_represented"])
        self.assertTrue(promotion["authorizes_latin_f_confirmation"])

        one_family = copy.deepcopy(rows)
        for row in one_family:
            if row["retreat"]["shadow_accepted"]:
                row["range_family"] = "balanced"
        self.assertFalse(
            fresh_replication_promotion(
                one_family,
                minimum_material_targets=4,
                minimum_material_exact_value=0.001,
            )["authorizes_latin_f_confirmation"]
        )

        late = copy.deepcopy(rows)
        late[-1]["ledger"]["fits_effective_conservative_street"] = False
        self.assertFalse(
            fresh_replication_promotion(
                late,
                minimum_material_targets=4,
                minimum_material_exact_value=0.001,
            )["authorizes_latin_f_confirmation"]
        )

    def test_config_freezes_latin_e_only_and_distinct_tolerances(self) -> None:
        parsed = _parse_config(json.loads(CONFIG.read_text(encoding="utf-8")))
        targets = parsed["target_specs"]
        self.assertEqual(len(targets), 6)
        self.assertEqual({row["round"] for row in targets}, {"latin_e"})
        self.assertEqual({row["observed_bettor"] for row in targets}, set(range(6)))
        self.assertEqual({row["acting_player"] for row in targets}, set(range(6)))
        self.assertTrue(
            all(
                row["acting_player"] == (row["observed_bettor"] - 1) % 6
                for row in targets
            )
        )
        self.assertNotEqual(
            parsed["cap_numerical_allowance"],
            parsed["epigraph_separation_allowance"],
        )
        self.assertEqual(parsed["maximum_cut_rounds"], 1)
        self.assertEqual(parsed["interior_retreat_factor"], 0.5)
        self.assertTrue(parsed["gates"]["require_no_global_optimality_claim"])

    def test_stack_is_not_reused_as_payoff_span_or_guard(self) -> None:
        source = IMPLEMENTATION.read_text(encoding="utf-8")
        self.assertNotIn('parsed["stack"]', source)
        self.assertIn("payoff_span(layout)", source)
        self.assertIn("raw_guard(layout", source)


if __name__ == "__main__":
    unittest.main()
