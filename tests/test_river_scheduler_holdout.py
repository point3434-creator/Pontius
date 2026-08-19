from __future__ import annotations

import unittest

from pontius.river_scheduler_holdout import run_river_scheduler_holdout
from pontius.river_scheduler_screen import _fold


def _artifacts(
    *,
    split: str = "validation",
    adaptive_signal: bool = True,
) -> tuple[dict, dict]:
    folds = 5
    group_ids: list[str] = []
    per_fold = {fold: 0 for fold in range(folds)}
    index = 0
    while min(per_fold.values()) < 4:
        group_id = f"reserved-group-{index}"
        index += 1
        fold = _fold(group_id, folds)
        if per_fold[fold] < 4:
            per_fold[fold] += 1
            group_ids.append(group_id)

    checkpoints = [0, 1, 2, 3, 4, 6, 8]
    contexts = []
    records = []
    for group_id in group_ids:
        for kind in ("low", "high"):
            context_id = f"{group_id}-{kind}"
            is_high = kind == "high"
            contexts.append(
                {
                    "context_id": context_id,
                    "group_id": group_id,
                    "split": split,
                    "provenance_digest": f"digest-{context_id}",
                    "oracle_labels": {
                        "duality_gap": 0.0,
                        "nash_conv": 0.0,
                        "simplex_pivots": 3,
                        "simplex_backend": "packing",
                    },
                }
            )
            feature = float(is_high) if adaptive_signal else 0.0
            exploitability = {
                0: 10.0,
                1: 10.0,
                2: 10.0 if is_high else 9.0,
                3: 9.0,
                4: 8.0,
                6: 0.0 if is_high and adaptive_signal else 8.0,
                8: 0.0 if is_high and adaptive_signal else 8.0,
            }
            for checkpoint in checkpoints:
                records.append(
                    {
                        "context_id": context_id,
                        "group_id": group_id,
                        "split": split,
                        "family": kind,
                        "solver": "dcfr",
                        "checkpoint": checkpoint,
                        "online_features": {
                            "positive_regret_mass": feature,
                            "active_regret_summary_milliseconds": 0.001,
                            "cumulative_alternating_state_visits": checkpoint * 100,
                            "cumulative_solver_milliseconds": float(checkpoint),
                        },
                        "labels": {"exploitability": exploitability[checkpoint]},
                    }
                )
    generation = {
        "allocation_average_iteration_budgets": [4],
        "checkpoints": checkpoints,
        "families": ["synthetic"],
        "groups": len(group_ids),
        "hands_per_player": 2,
        "seed": 17,
        "sequential_raise": True,
        "solvers": ["dcfr"],
        "split_order": ["validation", "test"],
        "store_policies": False,
    }
    source = {
        "experiment_type": "exact_river_early_opportunity_trace",
        "config": {
            **generation,
            "included_splits": [split],
            "measure_active_regret_summary_cost": True,
            "shadow_regret_variants": {},
        },
        "contexts": contexts,
        "records": records,
    }
    source["config"].pop("split_order")
    rule = {
        "rule_id": "frozen-test-rule",
        "status": "frozen_before_reserved",
        "solver": {
            "active_variant": "dcfr",
            "fixed_checkpoint": 4,
            "probe_checkpoint": 2,
            "shadow_regret_enabled": False,
        },
        "score": {
            "name": "active_raw",
            "feature": "positive_regret_mass",
            "direction": "high",
        },
        "macro": {
            "name": "shallow_12_5",
            "recipient_checkpoint": 6,
            "maximum_recipient_fraction": 0.125,
        },
        "reserved_generation": generation,
        "reserved_evaluation": {
            "folds": folds,
            "validation_gates": {
                "aggregate_fraction_of_perfect_post_probe_uplift_at_least": 0.25
            },
        },
    }
    return source, rule


class RiverSchedulerHoldoutTests(unittest.TestCase):
    def test_validation_applies_one_rule_without_selection(self) -> None:
        source, rule = _artifacts()
        result = run_river_scheduler_holdout(
            source,
            rule,
            split="validation",
            source_provenance={"sha256": "source"},
            rule_provenance={"sha256": "rule"},
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["status"], "validation_passed_test_authorized")
        self.assertTrue(result["test_authorized"])
        self.assertFalse(result["candidate_selection_performed"])
        self.assertEqual(result["candidate_id"], "active_raw::shallow_12_5")
        self.assertTrue(all(result["gates"].values()))
        self.assertTrue(
            all(
                fold["candidate"]["raw_exploitability_uplift_over_fixed"] > 0.0
                for fold in result["folds"]
            )
        )

    def test_validation_failure_keeps_test_sealed(self) -> None:
        source, rule = _artifacts(adaptive_signal=False)
        result = run_river_scheduler_holdout(
            source,
            rule,
            split="validation",
        )

        self.assertFalse(result["passed"])
        self.assertEqual(
            result["status"],
            "validation_failed_keep_fixed_test_sealed",
        )
        self.assertFalse(result["test_authorized"])

    def test_test_requires_passing_validation_from_the_same_rule(self) -> None:
        validation_source, rule = _artifacts()
        rule_provenance = {"sha256": "rule"}
        validation = run_river_scheduler_holdout(
            validation_source,
            rule,
            split="validation",
            rule_provenance=rule_provenance,
        )
        test_source, _ = _artifacts(split="test")

        with self.assertRaisesRegex(ValueError, "sealed"):
            run_river_scheduler_holdout(test_source, rule, split="test")

        result = run_river_scheduler_holdout(
            test_source,
            rule,
            split="test",
            validation_result=validation,
            rule_provenance=rule_provenance,
            validation_provenance={"sha256": "validation"},
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["status"], "test_passed")
        self.assertFalse(result["candidate_selection_performed"])

        changed_rule = {**rule, "rule_id": "changed"}
        with self.assertRaisesRegex(ValueError, "different frozen rule"):
            run_river_scheduler_holdout(
                test_source,
                changed_rule,
                split="test",
                validation_result=validation,
                rule_provenance=rule_provenance,
            )

    def test_reserved_source_must_match_frozen_generation(self) -> None:
        source, rule = _artifacts()
        source["config"]["seed"] += 1
        with self.assertRaisesRegex(ValueError, "seed"):
            run_river_scheduler_holdout(
                source,
                rule,
                split="validation",
            )

    def test_production_rule_requires_its_frozen_hash(self) -> None:
        source, rule = _artifacts()
        rule["rule_id"] = "river-post-probe-scheduler-v1"
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            run_river_scheduler_holdout(
                source,
                rule,
                split="validation",
                rule_provenance={"sha256": "changed"},
            )


if __name__ == "__main__":
    unittest.main()
