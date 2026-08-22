from __future__ import annotations

import unittest

from pontius.h32_one_seat_retreat_quality_trial import (
    QualityLabelBarrier,
    _extract_fallback_comparator,
    adjudicate_retreat_replication,
)


class H32OneSeatRetreatQualityTrialTests(unittest.TestCase):
    def test_label_barrier_rejects_early_comparator_and_bad_identity(self) -> None:
        barrier = QualityLabelBarrier()
        with self.assertRaisesRegex(RuntimeError, "before retreat certification"):
            barrier.open_sealed_comparator()
        with self.assertRaisesRegex(RuntimeError, "differs before"):
            barrier.freeze_candidate({"endpoint": False})

        barrier = QualityLabelBarrier()
        barrier.freeze_candidate({"endpoint": True, "retreat": True})
        with self.assertRaisesRegex(RuntimeError, "requires a frozen candidate"):
            QualityLabelBarrier().complete_retreat_certificate()
        barrier.complete_retreat_certificate()
        barrier.open_sealed_comparator()
        self.assertEqual(
            barrier.events,
            [
                "inputs_pinned",
                "candidate_frozen",
                "retreat_certificate_complete",
                "sealed_comparator_opened",
            ],
        )

    def test_replication_requires_material_value_and_conservative_rate(self) -> None:
        passed = adjudicate_retreat_replication(
            retreat_value=0.01,
            retreat_conservative_ledger_ms=14000.0,
            fallback_value=0.002,
            fallback_ledger_ms=10000.0,
            raw_guard_value=3e-9,
        )
        self.assertTrue(passed["material_value_win"])
        self.assertTrue(passed["conservative_rate_win"])
        self.assertTrue(passed["authorizes_fresh_target_replication"])

        rate_loss = adjudicate_retreat_replication(
            retreat_value=0.0021,
            retreat_conservative_ledger_ms=15000.0,
            fallback_value=0.002,
            fallback_ledger_ms=10000.0,
            raw_guard_value=3e-9,
        )
        self.assertTrue(rate_loss["material_value_win"])
        self.assertFalse(rate_loss["conservative_rate_win"])
        self.assertFalse(rate_loss["authorizes_fresh_target_replication"])
        with self.assertRaisesRegex(ValueError, "ledgers must be positive"):
            adjudicate_retreat_replication(
                retreat_value=0.01,
                retreat_conservative_ledger_ms=0.0,
                fallback_value=0.002,
                fallback_ledger_ms=10000.0,
                raw_guard_value=3e-9,
            )

    def test_fallback_extractor_requires_exact_sealed_arm(self) -> None:
        parsed = {
            "target": {"target_id": "target"},
            "expected_fallback_depth": 1,
            "expected_fallback_blocks": 31,
            "expected_blueprint_policy_sha256": "blueprint",
            "expected_fallback_candidate_id": "candidate",
            "expected_fallback_policy_sha256": "policy",
            "expected_source_nash_conv": 1.0,
            "quality_numerical_allowance": 1e-10,
            "street_budget_ms": 15000.0,
        }
        artifact = {
            "passed": True,
            "target_rows": [
                {
                    "target_id": "target",
                    "arms": [
                        {
                            "depth": 1,
                            "block_manifest_count": 31,
                            "restricted_blueprint_policy_sha256": "blueprint",
                            "raw_guard": 3e-9,
                            "payoff_span": 30.0,
                            "blueprint_quality": {"nash_conv": 1.0},
                            "teacher": {
                                "candidate_id": "candidate",
                                "policy_sha256": "policy",
                                "exact_positive_value": 0.2,
                                "charged_ledger_ms": 10000.0,
                                "accepted_by_shadow_rule": True,
                                "complete": True,
                                "independent_incremental_certificate": True,
                                "usable_before_emission_cutoff": True,
                                "quality": {"nash_conv": 0.8},
                            },
                        }
                    ],
                }
            ],
        }
        comparator, checks = _extract_fallback_comparator(artifact, parsed)
        self.assertEqual(comparator["candidate_id"], "candidate")
        self.assertTrue(all(checks.values()))

        artifact["target_rows"][0]["arms"][0]["teacher"][
            "independent_incremental_certificate"
        ] = False
        _, checks = _extract_fallback_comparator(artifact, parsed)
        self.assertFalse(checks["certificate"])


if __name__ == "__main__":
    unittest.main()
