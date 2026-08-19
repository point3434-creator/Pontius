from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
