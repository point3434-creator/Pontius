from __future__ import annotations

import json
from pathlib import Path
import unittest

from pontius import h32_fresh_convex_retreat_replication as core
from pontius.h32_continuation_root_ledger import _setup as historical_setup
from pontius.h32_decision_aligned_continuation_setup import (
    build_decision_aligned_continuation_setup,
    decision_aligned_core_setup_adapter,
)


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "experiments/configs/h32-decision-aligned-live-shadow-v1.json"


class H32DecisionAlignedLiveShadowTrialTests(unittest.TestCase):
    def test_setup_adapter_is_scoped_and_restores_after_success(self) -> None:
        self.assertIs(core._setup, historical_setup)
        with decision_aligned_core_setup_adapter():
            self.assertIs(core._setup, build_decision_aligned_continuation_setup)
        self.assertIs(core._setup, historical_setup)

    def test_setup_adapter_restores_after_failure(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "negative control"):
            with decision_aligned_core_setup_adapter():
                self.assertIs(core._setup, build_decision_aligned_continuation_setup)
                raise RuntimeError("negative control")
        self.assertIs(core._setup, historical_setup)

    def test_setup_adapter_rejects_nested_or_preexisting_replacement(self) -> None:
        with decision_aligned_core_setup_adapter():
            with self.assertRaisesRegex(RuntimeError, "already replaced"):
                with decision_aligned_core_setup_adapter():
                    self.fail("nested adapter unexpectedly opened")
        self.assertIs(core._setup, historical_setup)

    def test_config_freezes_six_fresh_current_decisions(self) -> None:
        from pontius.h32_decision_aligned_live_shadow_trial import _parse_config

        parsed = _parse_config(json.loads(CONFIG.read_text(encoding="utf-8")))
        targets = parsed["target_specs"]
        self.assertEqual(len(targets), 6)
        self.assertEqual({row["round"] for row in targets}, {"decision_aligned_call_v1"})
        self.assertEqual({row["observed_bettor"] for row in targets}, set(range(6)))
        self.assertEqual({row["observed_responder"] for row in targets}, set(range(6)))
        self.assertEqual({row["acting_player"] for row in targets}, set(range(6)))
        self.assertTrue(
            all(
                row["observed_responder"] == (row["observed_bettor"] + 1) % 6
                and row["acting_player"] == (row["observed_bettor"] + 2) % 6
                and row["observed_response"] == "call"
                for row in targets
            )
        )
        self.assertEqual(parsed["gates"]["expected_behavioral_information_sets"], 32)
        self.assertEqual(parsed["gates"]["expected_policy_variables"], 64)
        self.assertEqual(parsed["interior_retreat_factor"], 0.5)
        self.assertEqual(parsed["minimum_material_targets"], 4)
        self.assertEqual(parsed["minimum_material_exact_value"], 0.001)

    def test_transfer_threshold_is_separate_from_process_success(self) -> None:
        from pontius.h32_decision_aligned_live_shadow_trial import (
            decision_aligned_shadow_decision,
            decision_aligned_transfer_assessment,
        )

        def row(target: str, family: str, value: float, accepted: bool = True):
            return {
                "target_id": target,
                "range_family": family,
                "retreat": {
                    "shadow_accepted": accepted,
                    "exact_positive_value": value,
                },
                "ledger": {
                    "fits_measured_street": True,
                    "fits_effective_conservative_street": True,
                },
            }

        rows = [
            row("b0", "balanced", 0.002),
            row("b1", "balanced", 0.003),
            row("k0", "blocker_heavy", 0.004),
            row("k1", "blocker_heavy", 0.005),
            row("small", "balanced", 0.001),
            row("abstain", "blocker_heavy", 1.0, accepted=False),
        ]
        assessed = decision_aligned_transfer_assessment(
            rows,
            minimum_material_targets=4,
            minimum_material_exact_value=0.001,
        )
        self.assertTrue(assessed["decision_aligned_value_transfers"])
        self.assertEqual(
            decision_aligned_shadow_decision(process_passed=False, transfers=True),
            "reject_decision_aligned_live_shadow_execution",
        )
        self.assertEqual(
            decision_aligned_shadow_decision(process_passed=True, transfers=False),
            "accept_decision_aligned_shadow_execution_but_reject_transfer_claim",
        )
        self.assertEqual(
            decision_aligned_shadow_decision(process_passed=True, transfers=True),
            "accept_decision_aligned_shadow_transfer_and_authorize_post_fold_preregistration",
        )


if __name__ == "__main__":
    unittest.main()
