from __future__ import annotations

import unittest

from pontius.composition_matrix import run_composition_matrix


class CompositionMatrixTests(unittest.TestCase):
    def test_matrix_caches_blueprints_and_compares_architectures(self) -> None:
        result = run_composition_matrix(
            {
                "base": {
                    "search_iterations": 2,
                    "depth_limit": 1,
                },
                "axes": {
                    "blueprint_iterations": [3, 4],
                    "in_search_blueprint_weight": [0.99],
                },
                "max_runs": 2,
            }
        )

        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["run_count"], 2)
        self.assertEqual(result["prepared_blueprints"], 2)
        for architecture in (
            "prefix",
            "continual",
            "local_gated_continual",
            "global_control",
        ):
            self.assertEqual(
                result["architecture_summary"][architecture]["cases"],
                2,
            )
        self.assertIn("global_beats_continual", result["paired_summary"])
        self.assertIn(
            "continual_reach_weighted_root_candidate_model_gain",
            result["signal_diagnostics"],
        )

    def test_invalid_matrix_is_rejected_before_running(self) -> None:
        with self.assertRaises(ValueError):
            run_composition_matrix({"axes": {}})
        with self.assertRaises(ValueError):
            run_composition_matrix({"axes": {"typo": [1]}})
        with self.assertRaises(ValueError):
            run_composition_matrix(
                {
                    "axes": {"depth_limit": [1, 2]},
                    "max_runs": 1,
                }
            )


if __name__ == "__main__":
    unittest.main()
