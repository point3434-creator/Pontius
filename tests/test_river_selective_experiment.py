from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from pontius.river_selective_experiment import run_selective_expansion_pilot


def _config() -> dict:
    return {
        "groups": 1,
        "seed": 83,
        "hands_per_player": 2,
        "families": ["balanced"],
        "included_splits": ["development"],
        "bet_pot_fractions": [0.25, 0.5, 0.75],
        "raise_to_pot_fractions": [1.5, 2.0],
        "masks": [
            {
                "name": "b1r1",
                "expanded_bet_pot_fractions": [0.5],
                "expanded_raise_to_pot_fractions": [1.5],
            },
            {
                "name": "b2r1",
                "expanded_bet_pot_fractions": [0.25, 0.5],
                "expanded_raise_to_pot_fractions": [1.5],
            },
            {
                "name": "b3r1",
                "expanded_bet_pot_fractions": [0.25, 0.5, 0.75],
                "expanded_raise_to_pot_fractions": [1.5],
            },
            {
                "name": "b3r2",
                "expanded_bet_pot_fractions": [0.25, 0.5, 0.75],
                "expanded_raise_to_pot_fractions": [1.5, 2.0],
            },
        ],
        "blueprint_solver": "dcfr",
        "blueprint_iterations": 2,
        "online_solver": "dcfr",
        "warm_start_multipliers_by_payoff_span": [0.1],
        "full_tree_equivalent_iteration_budgets": [1, 2],
        "target_names": ["factorized_likelihood_p0"],
        "root_tv_budget": 0.01,
        "maximum_donor_fraction": 0.75,
        "factorized_likelihood_minimum": 0.5,
        "factorized_likelihood_maximum": 1.5,
    }


def _source_hash(filename: str) -> str:
    path = Path(__file__).parents[1] / "src" / "pontius" / filename
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _development_config() -> dict:
    config = _config()
    config.pop("blueprint_iterations")
    config.update(
        {
            "evidence_stage": "group_separated_development",
            "blueprint_quality_checkpoints": [2, 4],
            "warm_start_multipliers_by_payoff_span": [0.1],
            "boundary_feature_families": [
                "source_context",
                "target_context",
                "context_delta",
                "range_delta",
                "target_blueprint_public_policy",
            ],
            "record_solver_probe_features": True,
            "expected_selective_tree_sha256": _source_hash("selective_tree.py"),
            "expected_river_selective_sha256": _source_hash("river_selective.py"),
            "gates": {
                "minimum_development_board_groups": 1,
                "maximum_source_normalized_nash_conv": 10.0,
                "primary_full_tree_equivalent_iteration_budget": 2,
                "minimum_mask_no_op_oracle_relative_uplift": 0.0,
                "minimum_positive_group_uplift_fraction": 0.0,
            },
        }
    )
    return config


class RiverSelectiveExpansionExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = _config()
        cls.result = run_selective_expansion_pilot(cls.config)

    def test_pilot_is_full_universe_development_only_and_nonselecting(self) -> None:
        self.assertEqual(
            self.result["experiment_type"],
            "river_selective_expansion_pilot",
        )
        self.assertTrue(self.result["pilot"])
        self.assertFalse(self.result["selection_authorized"])
        self.assertFalse(self.result["native_latency_claim_authorized"])
        self.assertTrue(self.result["gates"]["passed"])
        self.assertTrue(all(self.result["gates"]["results"].values()))
        self.assertEqual(self.result["counts"]["contexts"], 1)
        self.assertEqual(self.result["counts"]["targets"], 1)
        self.assertEqual(self.result["counts"]["candidate_records"], 8)

    def test_nested_work_and_full_expansion_controls_are_explicit(self) -> None:
        structures = self.result["structures"]
        counts = [row["tree_states_per_traversal"] for row in structures]
        self.assertEqual(counts, sorted(set(counts)))
        self.assertGreater(structures[0]["cutoff_states"], 0)
        self.assertEqual(structures[-1]["mask_name"], "b3r2")
        self.assertTrue(structures[-1]["is_full_mask"])
        self.assertEqual(structures[-1]["cutoff_states"], 0)
        self.assertEqual(structures[-1]["full_tree_state_fraction"], 1.0)

        full_rows = [
            row for row in self.result["records"] if row["mask_name"] == "b3r2"
        ]
        for row in full_rows:
            self.assertEqual(
                row["solver_iterations"],
                row["full_tree_equivalent_iteration_budget"],
            )

    def test_every_quality_record_charges_work_and_exact_leaf_cost(self) -> None:
        for row in self.result["records"]:
            self.assertLessEqual(row["actual_state_visits"], row["state_visit_budget"])
            self.assertGreater(row["actual_state_visits"], 0)
            self.assertGreater(row["budget_utilization"], 0.0)
            self.assertLessEqual(row["budget_utilization"], 1.0)
            self.assertGreaterEqual(
                row["cold_exact_leaf_online_seconds"],
                row["hot_online_seconds"],
            )
            self.assertIn("full_universe_nash_conv", row)
            self.assertIn("nash_conv_reduction_from_blueprint", row)
        self.assertTrue(
            self.result["interpretation_limits"][
                "exact_continuation_values_are_oracle_control"
            ]
        )
        self.assertTrue(
            all(not row["selection_authorized"] for row in self.result["oracle_ceiling"])
        )
        fixed_warm = self.result["fixed_warm_mask_oracle"]
        self.assertEqual(len(fixed_warm), 2)
        self.assertTrue(all(not row["selection_authorized"] for row in fixed_warm))
        self.assertTrue(
            all(
                row["mask_oracle_with_no_op_total_reduction"]
                >= row["full_mask_with_no_op_total_reduction"]
                for row in fixed_warm
            )
        )

    def test_reserved_splits_non_nested_masks_and_unknown_fields_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "development-only"):
            run_selective_expansion_pilot(
                {**self.config, "included_splits": ["validation"]}
            )
        reversed_masks = list(reversed(self.config["masks"]))
        with self.assertRaisesRegex(ValueError, "nested"):
            run_selective_expansion_pilot({**self.config, "masks": reversed_masks})
        with self.assertRaisesRegex(ValueError, "unknown"):
            run_selective_expansion_pilot({**self.config, "future_axis": 1})


class RiverSelectiveExpansionDevelopmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = _development_config()
        cls.result = run_selective_expansion_pilot(cls.config)

    def test_threshold_blueprint_and_frozen_sources_are_reported(self) -> None:
        self.assertEqual(
            self.result["experiment_type"],
            "river_selective_expansion_development_matrix",
        )
        self.assertFalse(self.result["pilot"])
        self.assertEqual(
            self.result["evidence_stage"],
            "group_separated_development",
        )
        blueprint = self.result["blueprints"][0]
        self.assertTrue(blueprint["quality_threshold_passed"])
        self.assertIn(blueprint["iterations"], (2, 4))
        self.assertTrue(blueprint["quality_trajectory"])
        self.assertTrue(
            self.result["gates"]["results"]["selective_tree_source_is_frozen"]
        )
        self.assertTrue(
            self.result["gates"]["results"]["river_selective_source_is_frozen"]
        )

    def test_boundary_and_probe_features_cannot_contain_teacher_labels(self) -> None:
        forbidden = (
            "nash",
            "exploit",
            "best_response",
            "future",
            "gain",
            "label",
            "reduction",
            "oracle",
        )
        boundary = self.result["targets"][0]["boundary_online_features"]
        probe = self.result["records"][0]["solver_probe_features"]
        self.assertTrue(boundary)
        self.assertTrue(probe)
        self.assertTrue(
            all(not any(part in key for part in forbidden) for key in boundary)
        )
        self.assertTrue(
            all(not any(part in key for part in forbidden) for key in probe)
        )
        self.assertGreaterEqual(
            self.result["records"][0]["hot_with_probe_feature_seconds"],
            self.result["records"][0]["hot_online_seconds"],
        )
        self.assertGreaterEqual(
            self.result["records"][0][
                "cold_exact_leaf_with_probe_feature_seconds"
            ],
            self.result["records"][0]["cold_exact_leaf_online_seconds"],
        )
        self.assertIsNotNone(self.result["primary_opportunity"])

    def test_development_contract_rejects_warm_selection_and_missing_hashes(self) -> None:
        with self.assertRaisesRegex(ValueError, "one warm-start"):
            run_selective_expansion_pilot(
                {
                    **self.config,
                    "warm_start_multipliers_by_payoff_span": [0.1, 1.0],
                }
            )
        missing_hash = dict(self.config)
        missing_hash.pop("expected_selective_tree_sha256")
        with self.assertRaisesRegex(ValueError, "lowercase SHA-256"):
            run_selective_expansion_pilot(missing_hash)


if __name__ == "__main__":
    unittest.main()
