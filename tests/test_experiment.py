from __future__ import annotations

import unittest

from pontius.experiment import run_experiment


class ExperimentRunnerTests(unittest.TestCase):
    def test_small_run_records_reproduction_and_exact_metrics(self) -> None:
        result = run_experiment(
            {
                "game": "kuhn2",
                "solver": "lcfr",
                "iterations": 20,
                "report_every": 10,
                "seed": 7,
            }
        )
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["config"]["seed"], 7)
        self.assertEqual(result["solver"]["iterations"], 20)
        self.assertEqual(len(result["trace"]), 2)
        self.assertGreater(result["timing"]["solver_seconds"], 0.0)
        self.assertIn("nash_conv", result["average"])
        self.assertEqual(len(result["average"]["utilities"]), 2)


if __name__ == "__main__":
    unittest.main()

