from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius.h32_latin_f_convex_retreat_confirmation import (
    _parse_config,
    latin_f_confirmation_assessment,
    latin_f_confirmation_decision,
)


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "experiments/configs/h32-latin-f-convex-retreat-confirmation-v1.json"
LATIN_E_RESULT = (
    ROOT / "experiments/results/h32-fresh-convex-retreat-replication-v2.json"
)


def _row(
    target_id: str,
    family: str,
    value: float,
    *,
    accepted: bool = True,
    fit: bool = True,
) -> dict[str, object]:
    return {
        "target_id": target_id,
        "range_family": family,
        "retreat": {
            "shadow_accepted": accepted,
            "exact_positive_value": value,
        },
        "ledger": {
            "fits_measured_street": fit,
            "fits_effective_conservative_street": fit,
        },
    }


class H32LatinFConvexRetreatConfirmationTests(unittest.TestCase):
    def test_confirmation_reuses_strict_breadth_threshold(self) -> None:
        rows = [
            _row("b0", "balanced", 0.002),
            _row("b1", "balanced", 0.003),
            _row("k0", "blocker_heavy", 0.004),
            _row("k1", "blocker_heavy", 0.005),
            _row("small", "balanced", 0.001),
            _row("rejected", "blocker_heavy", 1.0, accepted=False),
        ]
        result = latin_f_confirmation_assessment(
            rows,
            minimum_material_targets=4,
            minimum_material_exact_value=0.001,
        )
        self.assertEqual(result["material_target_count"], 4)
        self.assertTrue(result["both_range_families_represented"])
        self.assertTrue(result["confirms_latin_e_breadth"])

        rows[-1]["ledger"]["fits_effective_conservative_street"] = False
        self.assertFalse(
            latin_f_confirmation_assessment(
                rows,
                minimum_material_targets=4,
                minimum_material_exact_value=0.001,
            )["confirms_latin_e_breadth"]
        )

    def test_decision_separates_process_failure_from_negative_science(self) -> None:
        self.assertEqual(
            latin_f_confirmation_decision(process_passed=False, confirms=True),
            "reject_latin_f_confirmation_execution",
        )
        self.assertEqual(
            latin_f_confirmation_decision(process_passed=True, confirms=False),
            "retain_latin_e_evidence_and_reject_live_shadow_preregistration",
        )
        self.assertEqual(
            latin_f_confirmation_decision(process_passed=True, confirms=True),
            "accept_latin_ef_breadth_and_authorize_live_shadow_preregistration",
        )

    def test_config_freezes_all_and_only_untouched_latin_f_targets(self) -> None:
        raw = json.loads(CONFIG.read_text(encoding="utf-8"))
        parsed = _parse_config(raw)
        targets = parsed["target_specs"]
        latin_e = json.loads(LATIN_E_RESULT.read_text(encoding="utf-8"))
        latin_e_ids = {row["target_id"] for row in latin_e["target_rows"]}

        self.assertEqual(len(targets), 6)
        self.assertEqual({row["round"] for row in targets}, {"latin_f"})
        self.assertFalse({row["target_id"] for row in targets} & latin_e_ids)
        self.assertEqual({row["source"] for row in targets}, {
            "panel_1/balanced",
            "panel_1/blocker_heavy",
            "panel_2/balanced",
            "panel_2/blocker_heavy",
            "panel_3/balanced",
            "panel_3/blocker_heavy",
        })
        self.assertEqual({row["observed_bettor"] for row in targets}, set(range(6)))
        self.assertEqual({row["acting_player"] for row in targets}, set(range(6)))
        self.assertTrue(
            all(
                row["acting_player"] == (row["observed_bettor"] - 1) % 6
                for row in targets
            )
        )
        self.assertEqual(parsed["interior_retreat_factor"], 0.5)
        self.assertEqual(parsed["minimum_material_targets"], 4)
        self.assertEqual(parsed["minimum_material_exact_value"], 0.001)
        self.assertEqual(parsed["cap_numerical_allowance"], 2e-11)
        self.assertEqual(parsed["epigraph_separation_allowance"], 1e-9)
        self.assertNotIn("latin_e_pooled_value_threshold", raw)
        self.assertNotIn("expected_latin_f_value", raw)


if __name__ == "__main__":
    unittest.main()
