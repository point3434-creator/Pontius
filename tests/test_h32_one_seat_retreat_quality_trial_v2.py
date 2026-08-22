from __future__ import annotations

import unittest

from pontius.h32_one_seat_retreat_quality_trial_v2 import (
    NumericalQualityLabelBarrier,
    _first_oracle_reproduction,
)


class H32OneSeatRetreatQualityTrialV2Tests(unittest.TestCase):
    def test_policy_digest_mismatch_is_recorded_but_not_authoritative(self) -> None:
        barrier = NumericalQualityLabelBarrier()
        barrier.freeze_candidate(
            {
                "blueprint_policy": True,
                "cut_players": True,
                "initial_lower_bound": True,
                "final_lower_bound": True,
                "first_candidate_policy": False,
                "endpoint_policy": False,
                "retreat_policy": False,
            }
        )
        self.assertEqual(
            barrier.policy_digest_diagnostics,
            {
                "endpoint_policy": False,
                "first_candidate_policy": False,
                "retreat_policy": False,
            },
        )
        self.assertTrue(all(barrier.semantic_identity_checks.values()))
        barrier.complete_retreat_certificate()
        barrier.open_sealed_comparator()

    def test_algorithmic_branch_mismatch_still_fails_before_label(self) -> None:
        barrier = NumericalQualityLabelBarrier()
        with self.assertRaisesRegex(RuntimeError, "algorithmic branch"):
            barrier.freeze_candidate(
                {
                    "cut_players": False,
                    "first_candidate_policy": True,
                    "endpoint_policy": True,
                    "retreat_policy": True,
                }
            )
        with self.assertRaisesRegex(ValueError, "diagnostics are incomplete"):
            NumericalQualityLabelBarrier().freeze_candidate({"cut_players": True})

    def test_first_oracle_reproduction_uses_numerical_and_discrete_gates(self) -> None:
        signatures = ["a", "b"]
        parsed = {
            "quality_numerical_allowance": 1e-10,
            "expected_first_oracle_objective": 0.5,
            "expected_first_oracle_maximum_cap_violation": 0.1,
            "expected_first_oracle_maximum_epigraph_violation": 0.2,
            "expected_first_oracle_response_signatures": signatures,
            "expected_cut_players": [1],
            "cap_numerical_allowance": 2e-11,
            "epigraph_separation_allowance": 1e-9,
        }
        target = {
            "first_oracle": {
                "nash_conv": 0.5 + 5e-11,
                "maximum_cap_violation": 0.1 - 5e-11,
                "maximum_epigraph_violation": 0.2 + 5e-11,
                "response_signature_sha256": signatures,
                "epigraph_violating_players": [1],
                "cap_allowance": 2e-11,
                "epigraph_allowance": 1e-9,
                "cap_feasible": False,
                "epigraph_closed": False,
            }
        }
        checks = _first_oracle_reproduction(parsed, target)
        self.assertTrue(all(checks.values()))

        target["first_oracle"]["response_signature_sha256"] = ["a", "changed"]
        checks = _first_oracle_reproduction(parsed, target)
        self.assertFalse(checks["response_signatures"])


if __name__ == "__main__":
    unittest.main()
