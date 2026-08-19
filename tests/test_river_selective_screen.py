from __future__ import annotations

import copy
import json
import random
import unittest

from pontius.river_selective_screen import run_selective_width_screen


def _rule() -> dict[str, object]:
    return {
        "rule_id": "synthetic-selective-screen",
        "status": "preregistered_discovery_only",
        "frozen_source": {
            "sha256": "source-sha",
            "config_sha256": "config-sha",
            "groups": 10,
            "targets": 40,
        },
        "solver_regime": {
            "warm_start_multiplier_by_payoff_span": 0.1,
            "full_tree_equivalent_iteration_budget": 32,
            "fallback_mask": "b3r2",
            "candidate_arms": ["no_op", "b3r1", "b3r2"],
        },
        "feature_tiers": [{"name": "signal", "features": ["signal"]}],
        "tree_family": {
            "maximum_depths": [1],
            "risk_standard_error_multipliers": [0.0],
            "minimum_leaf_instances": 12,
            "minimum_leaf_board_groups": 4,
            "leaf_tie_order": ["no_op", "b3r2", "b3r1"],
        },
        "selection_gates": {
            "minimum_board_groups": 10,
            "aggregate_raw_reduction_strictly_beats_fixed_b3r2": True,
            "aggregate_normalized_reduction_strictly_beats_fixed_b3r2": True,
            "minimum_positive_raw_uplift_group_fraction": 0.6,
            "minimum_compact_oracle_opportunity_capture_fraction": 0.15,
            "aggregate_state_visits_not_above_fixed_b3r2": True,
            "charged_raw_reduction_per_millisecond_strictly_beats_fixed_b3r2": True,
            "maximum_selected_target_harm_not_above_fixed_b3r2": True,
        },
    }


def _artifact(*, adaptive_signal: bool = True) -> dict[str, object]:
    targets = []
    records = []
    for group_index in range(10):
        group_id = f"group-{group_index}"
        for target_index in range(4):
            context_id = f"context-{group_index}-{target_index}"
            target_name = "range_update"
            high = target_index >= 2
            signal = float(high) if adaptive_signal else 0.0
            targets.append(
                {
                    "context_id": context_id,
                    "group_id": group_id,
                    "family": "synthetic",
                    "target_name": target_name,
                    "target_kind": "synthetic",
                    "boundary_feature_seconds": 0.00001,
                    "boundary_online_features": {
                        "signal": signal,
                        "target_payoff_span": 10.0,
                    },
                }
            )
            if adaptive_signal:
                reductions = {
                    "b3r1": 1.0 if high else 0.5,
                    "b3r2": 2.0 if high else -1.0,
                }
            else:
                reductions = {"b3r1": 0.0, "b3r2": 1.0}
            for mask, reduction in reductions.items():
                records.append(
                    {
                        "context_id": context_id,
                        "group_id": group_id,
                        "family": "synthetic",
                        "target_name": target_name,
                        "target_kind": "synthetic",
                        "mask_name": mask,
                        "warm_start_multiplier_by_payoff_span": 0.1,
                        "full_tree_equivalent_iteration_budget": 32,
                        "nash_conv_reduction_from_blueprint": reduction,
                        "actual_state_visits": 90 if mask == "b3r1" else 100,
                        "cold_exact_leaf_online_seconds": 0.001,
                        "full_evaluation_label_seconds": 0.0002,
                    }
                )
    return {
        "experiment_type": "river_selective_expansion_development_matrix",
        "evidence_stage": "group_separated_development",
        "selection_authorized": False,
        "config_sha256": "config-sha",
        "targets": targets,
        "records": records,
    }


def _without_runtime_noise(value):
    volatile = {
        "decision_seconds",
        "total_seconds",
        "raw_reduction_per_millisecond",
    }
    if isinstance(value, dict):
        return {
            key: _without_runtime_noise(item)
            for key, item in value.items()
            if key not in volatile
        }
    if isinstance(value, list):
        return [_without_runtime_noise(item) for item in value]
    return value


def _decision_signature(result: dict[str, object]) -> dict[str, object]:
    selection = result["cross_validated_selection"]
    final_fit = result["all_development_fit"]
    return {
        "status": result["status"],
        "replication_authorized": result["replication_authorized"],
        "selected_candidate_id": selection["selected_candidate_id"],
        "selected_counts": selection["selected_metrics"]["selection_counts"],
        "selection_gates": result["selection_gates"],
        "compact_oracle_counts": result["compact_oracle"]["selection_counts"],
        "candidate_counts": {
            row["candidate_id"]: row["aggregate"]["selection_counts"]
            for row in result["leaderboard"]
        },
        "selected_fold_trees": sorted(
            json.dumps(fold["tree"], sort_keys=True)
            for fold in selection["selected_fold_details"]
        ),
        "final_tree": None if final_fit is None else final_fit["tree"],
    }


def _scale_payoffs(artifact: dict[str, object], scale: float) -> dict[str, object]:
    scaled = copy.deepcopy(artifact)
    for target in scaled["targets"]:
        target["boundary_online_features"]["target_payoff_span"] *= scale
    for record in scaled["records"]:
        record["nash_conv_reduction_from_blueprint"] *= scale
    return scaled


class RiverSelectiveWidthScreenTests(unittest.TestCase):
    def test_grouped_causal_tree_passes_and_serializes_without_labels(self) -> None:
        result = run_selective_width_screen(_artifact(), _rule())

        self.assertTrue(result["selection_gates"]["passed"])
        self.assertTrue(result["replication_authorized"])
        self.assertEqual(result["counts"]["groups"], 10)
        self.assertEqual(result["counts"]["adaptive_candidate_specifications"], 1)
        selected = result["cross_validated_selection"]
        self.assertEqual(selected["selected_candidate_id"], "signal__depth_1__risk_0")
        self.assertAlmostEqual(selected["positive_raw_uplift_group_fraction"], 1.0)
        self.assertGreater(selected["raw_uplift_over_fixed"], 0.0)
        self.assertLessEqual(
            selected["selected_metrics"]["state_visits"],
            result["fixed_b3r2"]["state_visits"],
        )
        tree = result["all_development_fit"]["tree"]
        self.assertEqual(tree["type"], "split")
        rendered_tree = json.dumps(tree)
        self.assertNotIn("reduction", rendered_tree)
        self.assertNotIn("score", rendered_tree)
        self.assertFalse(result["selection_authorized"])
        self.assertFalse(result["reserved_validation_or_test_authorized"])

    def test_fixed_fallback_wins_when_tree_has_no_incremental_value(self) -> None:
        result = run_selective_width_screen(
            _artifact(adaptive_signal=False),
            _rule(),
        )

        self.assertFalse(result["selection_gates"]["passed"])
        self.assertFalse(result["replication_authorized"])
        self.assertEqual(
            result["cross_validated_selection"]["selected_candidate_id"],
            "fixed_b3r2",
        )
        self.assertIsNone(result["all_development_fit"])

    def test_source_hash_and_forbidden_features_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "source SHA-256"):
            run_selective_width_screen(
                _artifact(),
                _rule(),
                source_provenance={"sha256": "different"},
            )

        leaked = copy.deepcopy(_rule())
        leaked["feature_tiers"][0]["features"] = ["oracle_signal"]
        with self.assertRaisesRegex(ValueError, "forbidden fragment"):
            run_selective_width_screen(_artifact(), leaked)

    def test_incomplete_arm_and_noncausal_source_contracts_fail(self) -> None:
        incomplete = _artifact()
        incomplete["records"] = [
            row for row in incomplete["records"] if row["mask_name"] != "b3r1"
        ]
        with self.assertRaisesRegex(ValueError, "every compact arm"):
            run_selective_width_screen(incomplete, _rule())

        selected = _artifact()
        selected["selection_authorized"] = True
        with self.assertRaisesRegex(ValueError, "prohibit prior selection"):
            run_selective_width_screen(selected, _rule())

    def test_record_order_repeats_and_unused_labels_cannot_change_decision(self) -> None:
        artifact = _artifact()
        baseline = run_selective_width_screen(artifact, _rule())
        repeated = run_selective_width_screen(copy.deepcopy(artifact), _rule())
        self.assertEqual(
            _without_runtime_noise(repeated),
            _without_runtime_noise(baseline),
        )

        permuted = copy.deepcopy(artifact)
        generator = random.Random(20260819)
        generator.shuffle(permuted["targets"])
        generator.shuffle(permuted["records"])
        permuted_result = run_selective_width_screen(permuted, _rule())
        self.assertEqual(
            _without_runtime_noise(permuted_result),
            _without_runtime_noise(baseline),
        )

        unused = copy.deepcopy(artifact)
        for target in unused["targets"]:
            target["boundary_online_features"]["oracle_signal"] = 1e100
        for record in unused["records"]:
            record["future_nash_conv_label"] = -1e100
        unused_result = run_selective_width_screen(unused, _rule())
        self.assertEqual(
            _without_runtime_noise(unused_result),
            _without_runtime_noise(baseline),
        )

    def test_group_names_do_not_change_fits_or_selection(self) -> None:
        artifact = _artifact()
        baseline = run_selective_width_screen(artifact, _rule())
        renamed = copy.deepcopy(artifact)
        mapping = {f"group-{index}": f"renamed-{9 - index}" for index in range(10)}
        for target in renamed["targets"]:
            target["group_id"] = mapping[target["group_id"]]
        for record in renamed["records"]:
            record["group_id"] = mapping[record["group_id"]]

        renamed_result = run_selective_width_screen(renamed, _rule())
        self.assertEqual(_decision_signature(renamed_result), _decision_signature(baseline))
        for key in (
            "raw_reduction",
            "normalized_reduction",
            "maximum_target_harm",
            "state_visits",
            "solve_seconds",
        ):
            self.assertAlmostEqual(
                renamed_result["cross_validated_selection"]["selected_metrics"][key],
                baseline["cross_validated_selection"]["selected_metrics"][key],
            )

    def test_payoff_rescaling_preserves_normalized_selector_decisions(self) -> None:
        baseline = run_selective_width_screen(_artifact(), _rule())
        baseline_selection = baseline["cross_validated_selection"]
        baseline_by_candidate = {
            row["candidate_id"]: row for row in baseline["leaderboard"]
        }
        for scale in (0.5, 2.0, 4.0):
            result = run_selective_width_screen(
                _scale_payoffs(_artifact(), scale),
                _rule(),
            )
            self.assertEqual(_decision_signature(result), _decision_signature(baseline))
            selection = result["cross_validated_selection"]
            self.assertAlmostEqual(
                selection["selected_metrics"]["raw_reduction"],
                scale * baseline_selection["selected_metrics"]["raw_reduction"],
            )
            self.assertAlmostEqual(
                selection["selected_metrics"]["normalized_reduction"],
                baseline_selection["selected_metrics"]["normalized_reduction"],
            )
            self.assertAlmostEqual(
                result["compact_oracle"]["raw_reduction"],
                scale * baseline["compact_oracle"]["raw_reduction"],
            )
            for row in result["leaderboard"]:
                base = baseline_by_candidate[row["candidate_id"]]
                self.assertAlmostEqual(
                    row["aggregate"]["raw_reduction"],
                    scale * base["aggregate"]["raw_reduction"],
                )
                self.assertAlmostEqual(
                    row["aggregate"]["normalized_reduction"],
                    base["aggregate"]["normalized_reduction"],
                )

    def test_exact_ties_prefer_no_op_but_fixed_control_wins_model_tie(self) -> None:
        artifact = _artifact()
        for record in artifact["records"]:
            record["nash_conv_reduction_from_blueprint"] = 0.0

        result = run_selective_width_screen(artifact, _rule())

        self.assertEqual(
            result["compact_oracle"]["selection_counts"],
            {"no_op": 40},
        )
        self.assertTrue(
            all(
                row["aggregate"]["selection_counts"] == {"no_op": 40}
                for row in result["leaderboard"]
            )
        )
        self.assertEqual(
            result["cross_validated_selection"]["selected_candidate_id"],
            "fixed_b3r2",
        )
        self.assertFalse(result["selection_gates"]["passed"])


if __name__ == "__main__":
    unittest.main()
