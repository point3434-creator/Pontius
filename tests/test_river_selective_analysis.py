from __future__ import annotations

import copy
import unittest

from pontius.river_selective_analysis import analyze_selective_expansion_development


MASKS = ("b1r1", "b2r1", "b3r1", "b3r2")
PRIMARY_REDUCTIONS = (
    (3.0, 2.0, 1.0, 1.0),
    (1.0, 3.0, 1.0, 1.0),
    (1.0, 2.0, 4.0, 1.0),
)


def _artifact() -> dict[str, object]:
    targets = []
    records = []
    for group_index in range(3):
        context_id = f"context-{group_index}"
        group_id = f"group-{group_index}"
        target_name = "blocker_reweight_p0"
        targets.append(
            {
                "context_id": context_id,
                "group_id": group_id,
                "family": "balanced",
                "target_name": target_name,
                "target_kind": "blocker_reweight",
                "boundary_feature_seconds": 0.0005,
                "boundary_online_features": {
                    "signal": float(group_index),
                    "target_payoff_span": 10.0,
                },
            }
        )
        for budget in (4, 32):
            reductions = (
                PRIMARY_REDUCTIONS[group_index]
                if budget == 32
                else (0.2 + 0.1 * group_index, 0.1, 0.1, 0.1)
            )
            for mask, reduction in zip(MASKS, reductions, strict=True):
                records.append(
                    {
                        "context_id": context_id,
                        "group_id": group_id,
                        "family": "balanced",
                        "target_name": target_name,
                        "target_kind": "blocker_reweight",
                        "mask_name": mask,
                        "warm_start_multiplier_by_payoff_span": 0.1,
                        "full_tree_equivalent_iteration_budget": budget,
                        "nash_conv_reduction_from_blueprint": reduction,
                        "actual_state_visits": budget * (MASKS.index(mask) + 1) * 100,
                        "hot_with_probe_feature_seconds": 0.001,
                        "cold_exact_leaf_online_seconds": 0.002,
                        "cold_exact_leaf_with_probe_feature_seconds": 0.0021,
                        "solver_probe_features": {
                            "probe_signal": float(group_index),
                            "probe_constant": 1.0,
                        },
                    }
                )
    return {
        "experiment_type": "river_selective_expansion_development_matrix",
        "evidence_stage": "group_separated_development",
        "selection_authorized": False,
        "config_sha256": "synthetic",
        "config": {
            "masks": [{"name": name} for name in MASKS],
            "warm_start_multipliers_by_payoff_span": [0.1],
            "full_tree_equivalent_iteration_budgets": [4, 32],
            "gates": {"primary_full_tree_equivalent_iteration_budget": 32},
        },
        "gates": {"passed": True, "results": {}},
        "targets": targets,
        "records": records,
    }


class RiverSelectiveAnalysisTests(unittest.TestCase):
    def test_reports_preregistered_opportunity_and_group_transfer(self) -> None:
        result = analyze_selective_expansion_development(
            _artifact(),
            input_sha256="artifact-sha",
        )

        self.assertFalse(result["selection_authorized"])
        self.assertFalse(result["selector_fitted"])
        self.assertEqual(result["frozen_probe"]["mask_name"], "b1r1")
        self.assertEqual(result["frozen_probe"]["full_tree_equivalent_iteration_budget"], 4)
        self.assertEqual(result["counts"]["groups"], 3)
        self.assertEqual(result["counts"]["primary_instances"], 3)

        primary = result["primary_opportunity"]
        self.assertAlmostEqual(primary["mask_oracle_with_no_op_total_reduction"], 10.0)
        self.assertAlmostEqual(primary["full_mask_with_no_op_total_reduction"], 3.0)
        self.assertAlmostEqual(primary["opportunity_uplift"], 7.0)
        self.assertAlmostEqual(primary["positive_group_fraction"], 1.0)

        transfer = result["leave_one_group_out_best_fixed_mask"]
        self.assertAlmostEqual(transfer["held_out_selected_with_no_op_total_reduction"], 5.0)
        self.assertAlmostEqual(transfer["held_out_selected_minus_full"], 2.0)
        self.assertAlmostEqual(
            transfer["available_oracle_opportunity_captured_fraction"],
            2.0 / 7.0,
        )
        self.assertFalse(transfer["selection_authorized"])

    def test_ranks_only_online_boundary_and_paid_probe_features(self) -> None:
        result = analyze_selective_expansion_development(_artifact())

        boundary = result["boundary_feature_ranks"]
        probe = result["paid_probe_feature_ranks"]
        self.assertEqual(boundary["feature_count"], 2)
        self.assertEqual(probe["feature_count"], 2)
        self.assertEqual(
            boundary["ranked_by_absolute_spearman"][
                "normalized_no_op_search_opportunity"
            ][0]["feature"],
            "signal",
        )
        self.assertEqual(
            probe["ranked_by_absolute_spearman"][
                "normalized_raw_mask_advantage"
            ][0]["feature"],
            "probe_signal",
        )
        self.assertFalse(boundary["selection_authorized"])
        self.assertFalse(probe["selection_authorized"])

    def test_rejects_teacher_labels_and_non_development_artifacts(self) -> None:
        leaked = _artifact()
        leaked["targets"][0]["boundary_online_features"]["oracle_signal"] = 1.0
        with self.assertRaisesRegex(ValueError, "forbidden fragment"):
            analyze_selective_expansion_development(leaked)

        pilot = copy.deepcopy(_artifact())
        pilot["experiment_type"] = "river_selective_expansion_pilot"
        with self.assertRaisesRegex(ValueError, "development matrix"):
            analyze_selective_expansion_development(pilot)


if __name__ == "__main__":
    unittest.main()
