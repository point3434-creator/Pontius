from __future__ import annotations

import unittest

from pontius.benefit_experiment import run_benefit_experiment
from pontius.composition_experiment import run_composition_experiment
from pontius.leaf_experiment import prepare_blueprint


class CompositionExperimentTests(unittest.TestCase):
    def test_three_target_blind_architectures_are_reported(self) -> None:
        result = run_composition_experiment(
            {
                "blueprint_iterations": 10,
                "search_iterations": 3,
                "depth_limit": 2,
            }
        )

        self.assertEqual(result["schema_version"], 1)
        self.assertTrue(
            result["protocol"][
                "full_game_target_never_enters_policy_construction"
            ]
        )
        self.assertFalse(result["protocol"]["continual_safety_guarantee"])
        self.assertEqual(result["continual"]["searched_public_histories"], 4)
        for architecture in (
            "prefix",
            "continual",
            "local_gated_continual",
            "global_control",
        ):
            self.assertIn("candidate", result[architecture])
            self.assertIn(
                "nash_conv_improvement_over_blueprint",
                result[architecture]["candidate"],
            )
        self.assertAlmostEqual(
            result["local_gated_continual"]["candidate"][
                "decision_compute_seconds"
            ],
            result["local_gated_continual"][
                "expected_search_seconds_per_hand"
            ]
            + result["local_gated_continual"][
                "expected_gate_evaluation_seconds_per_hand"
            ],
        )

    def test_prefix_arm_matches_existing_exact_leaf_experiment(self) -> None:
        prepared = prepare_blueprint("kuhn2", "lcfr", 20)
        config = {
            "blueprint_iterations": 20,
            "search_iterations": 5,
            "depth_limit": 2,
            "in_search_blueprint_weight": 0.99,
        }
        composition = run_composition_experiment(
            config,
            prepared_blueprint=prepared,
        )
        benefit = run_benefit_experiment(
            {**config, "probe_iterations": 1},
            prepared_blueprint=prepared,
        )

        self.assertAlmostEqual(
            composition["prefix"]["candidate"][
                "nash_conv_improvement_over_blueprint"
            ],
            benefit["targets"]["full_game_nash_conv_improvement"],
        )

    def test_full_anchor_is_no_op_for_every_architecture(self) -> None:
        result = run_composition_experiment(
            {
                "blueprint_iterations": 10,
                "search_iterations": 2,
                "in_search_blueprint_weight": 1.0,
            }
        )

        for architecture in (
            "prefix",
            "continual",
            "local_gated_continual",
            "global_control",
        ):
            self.assertAlmostEqual(
                result[architecture]["candidate"][
                    "nash_conv_improvement_over_blueprint"
                ],
                0.0,
            )

    def test_invalid_configuration_and_prepared_blueprint_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_composition_experiment({"depth_limit": 0})
        with self.assertRaises(ValueError):
            run_composition_experiment({"search_solver": "imaginary"})

        prepared = prepare_blueprint("kuhn2", "lcfr", 2)
        with self.assertRaises(ValueError):
            run_composition_experiment(
                {"blueprint_iterations": 3},
                prepared_blueprint=prepared,
            )


if __name__ == "__main__":
    unittest.main()
