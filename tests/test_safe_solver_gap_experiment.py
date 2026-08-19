from __future__ import annotations

import unittest

from pontius.leaf_experiment import prepare_blueprint
from pontius.safe_solver_gap_experiment import run_safe_solver_gap_experiment


class SafeSolverGapExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_safe_solver_gap_experiment(
            {
                "blueprint_iterations": 20,
                "search_solvers": ["cfr_plus"],
                "checkpoints": [1, 3],
                "output_policies": ["average", "current"],
                "initializations": [
                    {"name": "cold", "source": "none"},
                    {
                        "name": "blueprint_10",
                        "source": "blueprint",
                        "regret_mass": 10.0,
                    },
                ],
            },
            environment={"test": True},
        )

    def test_exact_targets_are_hidden_from_candidate_construction(self) -> None:
        self.assertEqual(len(self.result["boundaries"]), 4)
        self.assertFalse(
            self.result["protocol"][
                "full_game_target_enters_candidate_construction"
            ]
        )
        self.assertTrue(
            self.result["protocol"]["hidden_best_response_is_diagnostic_only"]
        )
        for boundary in self.result["boundaries"]:
            self.assertGreater(
                boundary["exact"]["sum_margin"]["objective_value"],
                0.0,
            )
            self.assertGreater(
                boundary["exact"]["hidden_best_response"]["objective_value"],
                0.0,
            )

    def test_blueprint_warm_average_begins_as_certified_no_op(self) -> None:
        for boundary in self.result["boundaries"]:
            trajectory = next(
                item
                for item in boundary["trajectories"]
                if item["initialization"]["name"] == "blueprint_10"
            )
            candidate = trajectory["checkpoints"][0]["candidates"]["average"]

            self.assertTrue(candidate["safe_at_strict_tolerance"])
            self.assertAlmostEqual(
                candidate["mean_resolver_tv_from_blueprint"],
                0.0,
            )
            self.assertAlmostEqual(candidate["signed_sum_frontier_margin"], 0.0)

    def test_safe_scores_respect_oracles_and_incumbents_are_monotone(self) -> None:
        for boundary in self.result["boundaries"]:
            sum_optimum = boundary["exact"]["sum_margin"]["objective_value"]
            hidden_optimum = boundary["exact"]["hidden_best_response"][
                "objective_value"
            ]
            for trajectory in boundary["trajectories"]:
                prior_incumbent = 0.0
                for checkpoint in trajectory["checkpoints"]:
                    incumbent = checkpoint["incumbent"][
                        "strict_sum_margin_score"
                    ]
                    self.assertGreaterEqual(incumbent + 1e-12, prior_incumbent)
                    prior_incumbent = incumbent
                    for candidate in checkpoint["candidates"].values():
                        if candidate["safe_at_strict_tolerance"]:
                            self.assertLessEqual(
                                candidate["signed_sum_frontier_margin"],
                                sum_optimum + 1e-8,
                            )
                            self.assertLessEqual(
                                candidate["opponent_best_response_reduction"],
                                hidden_optimum + 1e-8,
                            )

    def test_root_frontier_sum_equals_full_opponent_br_reduction(self) -> None:
        root = self.result["boundaries"][0]
        self.assertEqual(root["history"], [])
        for trajectory in root["trajectories"]:
            for checkpoint in trajectory["checkpoints"]:
                for candidate in checkpoint["candidates"].values():
                    self.assertAlmostEqual(
                        candidate["signed_sum_frontier_margin"],
                        candidate["opponent_best_response_reduction"],
                    )

    def test_invalid_and_mismatched_configurations_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive, unique, and increasing"):
            run_safe_solver_gap_experiment({"checkpoints": [3, 1]})
        with self.assertRaisesRegex(ValueError, "cannot have regret_mass"):
            run_safe_solver_gap_experiment(
                {
                    "initializations": [
                        {"name": "bad", "source": "none", "regret_mass": 1.0}
                    ]
                }
            )
        prepared = prepare_blueprint("kuhn2", "lcfr", 10)
        with self.assertRaisesRegex(ValueError, "does not match"):
            run_safe_solver_gap_experiment(
                {"blueprint_iterations": 20},
                prepared_blueprint=prepared,
            )


if __name__ == "__main__":
    unittest.main()
