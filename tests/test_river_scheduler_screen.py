from __future__ import annotations

import unittest

from pontius.river_scheduler_screen import run_river_scheduler_screen


def _artifacts(*, adaptive_signal: bool = True) -> tuple[dict, dict, dict]:
    contexts = []
    records = []
    shadow_records = []
    for group_index in range(10):
        group_id = f"group-{group_index}"
        for kind in ("low", "high"):
            context_id = f"{group_id}-{kind}"
            is_high = kind == "high"
            contexts.append(
                {
                    "context_id": context_id,
                    "group_id": group_id,
                    "split": "development",
                    "provenance_digest": f"digest-{context_id}",
                }
            )
            feature = float(is_high) if adaptive_signal else 0.0
            exploitabilities = {
                0: 10.0,
                2: 10.0 if is_high else 9.0,
                4: 8.0,
                6: 0.0 if is_high and adaptive_signal else 8.0,
                8: 0.0 if is_high and adaptive_signal else 8.0,
            }
            for checkpoint in (0, 2, 4, 6, 8):
                records.append(
                    {
                        "context_id": context_id,
                        "group_id": group_id,
                        "split": "development",
                        "solver": "dcfr",
                        "checkpoint": checkpoint,
                        "online_features": {
                            "positive_regret_mass": feature,
                            "normalized_positive_regret_mass": feature,
                            "raise_to_pot": 1.0,
                            "cumulative_alternating_state_visits": checkpoint * 100,
                            "cumulative_solver_milliseconds": float(checkpoint),
                        },
                        "labels": {"exploitability": exploitabilities[checkpoint]},
                    }
                )
            shadow_records.append(
                {
                    "context_id": context_id,
                    "group_id": group_id,
                    "split": "development",
                    "family": kind,
                    "provenance_digest": f"digest-{context_id}",
                    "checkpoint": 2,
                    "online_features": {
                        "normalized_positive_regret_mass": feature,
                        "shadow_cfr_plus_positive_regret_mass": feature,
                        "shadow_cfr_plus_normalized_positive_regret_mass": feature,
                    },
                    "timing": {
                        "plain_active_feature_summary_milliseconds": 0.001,
                        "conservative_instrumentation_overhead_milliseconds": 0.002,
                    },
                }
            )
    source = {
        "experiment_type": "exact_river_early_opportunity_trace",
        "config": {
            "solvers": ["dcfr"],
            "checkpoints": [0, 2, 4, 6, 8],
            "included_splits": ["development"],
            "sequential_raise": True,
        },
        "contexts": contexts,
        "records": records,
    }
    shadow = {
        "experiment_type": "exact_river_shadow_regret_probe",
        "source_provenance": None,
        "records": shadow_records,
    }
    rule = {
        "rule_id": "test-rule",
        "status": "preregistered_development_only",
        "frozen_source": {"contexts": 20},
        "solver": {
            "active_variant": "dcfr",
            "fixed_checkpoint": 4,
            "probe_checkpoint": 2,
            "shadow_regret_variant": "cfr_plus",
        },
        "folds": {"count": 2},
        "scores": [
            {
                "name": "active",
                "terms": [
                    {
                        "feature": "positive_regret_mass",
                        "direction": "high",
                        "weight": 1.0,
                    }
                ],
            }
        ],
        "macro_options": [
            {
                "name": "shallow_half",
                "recipient_checkpoint": 6,
                "maximum_recipient_fraction": 0.5,
            }
        ],
        "allocator": {"required_checkpoints": [0, 2, 4, 6, 8]},
    }
    return source, shadow, rule


class RiverSchedulerScreenTests(unittest.TestCase):
    def test_group_cross_validation_passes_a_real_causal_signal(self) -> None:
        source, shadow, rule = _artifacts()
        result = run_river_scheduler_screen(source, shadow, rule)

        self.assertTrue(result["development_gate_passed"])
        self.assertEqual(result["counts"]["adaptive_candidates"], 1)
        self.assertEqual(
            result["all_development_selection"]["selected_candidate_id"],
            "active::shallow_half",
        )
        for fold in result["cross_validation"]:
            held_out = fold["held_out"]
            self.assertGreater(held_out["raw_exploitability_uplift_over_fixed"], 0.0)
            self.assertLessEqual(
                held_out["candidate_iterations"], held_out["fixed_iterations"]
            )
            self.assertLessEqual(
                held_out["candidate_state_visits"], held_out["fixed_state_visits"]
            )

    def test_fixed_fallback_wins_when_adaptation_has_no_uplift(self) -> None:
        source, shadow, rule = _artifacts(adaptive_signal=False)
        result = run_river_scheduler_screen(source, shadow, rule)

        self.assertFalse(result["development_gate_passed"])
        self.assertEqual(
            result["all_development_selection"]["selected_candidate_id"],
            "fixed_checkpoint_4",
        )
        self.assertTrue(
            all(
                fold["selected_candidate_id"] == "fixed_checkpoint_4"
                for fold in result["cross_validation"]
            )
        )

    def test_source_hash_is_enforced_when_provided(self) -> None:
        source, shadow, rule = _artifacts()
        rule["frozen_source"]["sha256"] = "expected"
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            run_river_scheduler_screen(
                source,
                shadow,
                rule,
                source_provenance={"sha256": "different"},
            )


if __name__ == "__main__":
    unittest.main()
