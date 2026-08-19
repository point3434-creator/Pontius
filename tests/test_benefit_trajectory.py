from __future__ import annotations

import copy
import unittest

from pontius.benefit_trajectory import analyze_probe_trajectories


def synthetic_matrix() -> dict:
    runs = []
    for case, target in (("good", 0.5), ("bad", -0.5)):
        direction = 1.0 if case == "good" else -1.0
        for checkpoint in (1, 3, 5, 10, 25):
            movement = checkpoint / 100.0
            runs.append(
                {
                    "config": {
                        "case": case,
                        "probe_iterations": checkpoint,
                    },
                    "signals": {
                        "probe_local_nash_conv_improvement": (
                            direction * checkpoint / 10.0
                        ),
                        "probe_mean_policy_tv": movement,
                        "full_local_nash_conv_improvement": direction,
                        "full_local_improvement_per_mean_policy_tv": (
                            direction * 2.0
                        ),
                        "full_policy_stability": -0.5,
                    },
                    "targets": {
                        "full_game_nash_conv_improvement": target,
                    },
                    "metrics": {
                        "probe_search_seconds": checkpoint / 1_000.0,
                        "probe_to_full_search_time_ratio": checkpoint / 100.0,
                    },
                }
            )
    return {"runs": runs}


class BenefitTrajectoryTests(unittest.TestCase):
    def test_groups_checkpoints_and_reports_unfitted_rankings(self) -> None:
        result = analyze_probe_trajectories({"toy": synthetic_matrix()})

        self.assertEqual(result["schema_version"], 1)
        source = result["sources"]["toy"]
        self.assertEqual(source["ranking_diagnostics"]["cases"], 2)
        self.assertEqual(
            source["ranking_diagnostics"]["positive_full_game_improvement"],
            1,
        )
        auc = source["ranking_diagnostics"]["features"][
            "probe_model_gain_at_1"
        ]["roc_auc_for_positive_full_game_improvement"]
        self.assertEqual(auc, 1.0)
        self.assertAlmostEqual(
            source["timing"]["10"]["mean_probe_search_milliseconds"],
            10.0,
        )
        self.assertTrue(result["protocol"]["analysis_fits_no_selector_or_threshold"])

    def test_rejects_incomplete_or_inconsistent_trajectories(self) -> None:
        incomplete = synthetic_matrix()
        incomplete["runs"].pop()
        with self.assertRaises(ValueError):
            analyze_probe_trajectories({"toy": incomplete})

        inconsistent = copy.deepcopy(synthetic_matrix())
        inconsistent["runs"][1]["targets"][
            "full_game_nash_conv_improvement"
        ] = 0.25
        with self.assertRaises(ValueError):
            analyze_probe_trajectories({"toy": inconsistent})

    def test_rejects_invalid_checkpoint_contract(self) -> None:
        with self.assertRaises(ValueError):
            analyze_probe_trajectories({})
        with self.assertRaises(ValueError):
            analyze_probe_trajectories(
                {"toy": synthetic_matrix()},
                checkpoints=(3, 1),
            )


if __name__ == "__main__":
    unittest.main()
