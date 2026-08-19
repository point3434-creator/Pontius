from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from pontius.constrained_generation_matrix import (
    run_constrained_generation_matrix,
)


class ConstrainedGenerationMatrixTests(unittest.TestCase):
    def test_carries_converged_incumbents_across_anytime_budgets(self) -> None:
        result = run_constrained_generation_matrix(
            {
                "base": {
                    "blueprint_iterations": 20,
                    "max_updates": 4,
                },
                "axes": {"blueprint_solver": ["lcfr"]},
                "store_records": False,
            }
        )

        self.assertEqual(result["run_count"], 1)
        self.assertEqual(result["boundary_count"], 4)
        self.assertNotIn("records", result)
        self.assertEqual(len(result["anytime_summary"]), 4)
        self.assertEqual(result["anytime_summary"][0]["update_budget"], 1)
        self.assertGreaterEqual(
            result["best_update_budget"]["update_budget"],
            1,
        )

    def test_invalid_matrix_is_rejected_before_execution(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "unknown constrained-generation matrix",
        ):
            run_constrained_generation_matrix(
                {
                    "base": {"mystery": 1},
                    "axes": {"blueprint_solver": ["lcfr"]},
                }
            )

    def test_frozen_v1_rule_digest_cannot_change_silently(self) -> None:
        path = (
            Path(__file__).parents[1]
            / "experiments"
            / "rules"
            / "constrained-generation-v1.json"
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
            "3ffa9bc62d0f5bd6d6cde4e56bad53f4bc95dbcc02324b714250e187bc5c32f1",
        )


if __name__ == "__main__":
    unittest.main()
