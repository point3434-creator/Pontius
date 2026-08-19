from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from pontius.safe_solver_gap_matrix import run_safe_solver_gap_matrix


class SafeSolverGapMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_safe_solver_gap_matrix(
            {
                "base": {
                    "blueprint_iterations": 20,
                    "search_solvers": ["cfr_plus"],
                    "checkpoints": [1],
                    "output_policies": ["average"],
                    "initializations": [
                        {
                            "name": "blueprint_10",
                            "source": "blueprint",
                            "regret_mass": 10.0,
                        }
                    ],
                },
                "axes": {"blueprint_solver": ["lcfr"]},
                "store_records": False,
            }
        )

    def test_matrix_aggregates_candidate_and_incumbent_groups(self) -> None:
        self.assertEqual(self.result["run_count"], 1)
        self.assertEqual(self.result["prepared_blueprints"], 1)
        self.assertEqual(self.result["candidate_record_count"], 4)
        self.assertEqual(self.result["incumbent_record_count"], 4)
        self.assertEqual(len(self.result["candidate_summary"]), 1)
        self.assertEqual(len(self.result["incumbent_summary"]), 1)
        self.assertNotIn("candidate_records", self.result)
        self.assertIsNotNone(self.result["best_available_initialization"])

    def test_invalid_matrix_is_rejected_before_execution(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown safe-solver-gap"):
            run_safe_solver_gap_matrix(
                {
                    "base": {"mystery": 1},
                    "axes": {"blueprint_iterations": [20]},
                }
            )

    def test_frozen_v1_rule_digest_cannot_change_silently(self) -> None:
        path = (
            Path(__file__).parents[1]
            / "experiments"
            / "rules"
            / "safe-solver-incumbent-v1.json"
        )
        document = json.loads(path.read_text(encoding="utf-8"))
        canonical = json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()

        self.assertEqual(
            hashlib.sha256(canonical).hexdigest(),
            "403980953b1cfbb4c5cdb50a5ffcdd892f30bdaa9abfe87292ffe9504c147450",
        )


if __name__ == "__main__":
    unittest.main()
