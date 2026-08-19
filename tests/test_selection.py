from __future__ import annotations

import unittest

from pontius.selection import (
    FrozenSelectionRule,
    evaluate_frozen_selection,
    rule_digest,
)


def rule_document() -> dict:
    return {
        "schema_version": 1,
        "name": "test-rule",
        "status": "frozen",
        "rule": {
            "candidate_config": {"search_solver": "lcfr"},
            "candidate_policy": "average",
            "risk_metric": "risk",
            "maximum_risk": 0.2,
        },
    }


def compact_run(
    risk: float,
    delta: float,
    seconds: float = 0.01,
    depth_limit: int = 2,
) -> dict:
    return {
        "config": {"search_solver": "lcfr", "depth_limit": depth_limit},
        "metrics": {
            "risk": risk,
            "perturbed_average_nash_conv_delta_from_blueprint": delta,
            "perturbed_search_seconds": seconds,
        },
    }


class FrozenSelectionTests(unittest.TestCase):
    def test_threshold_is_inclusive_and_candidate_is_validated(self) -> None:
        rule = FrozenSelectionRule.from_document(rule_document())
        self.assertTrue(rule.selects_search({"risk": 0.2}))
        self.assertFalse(rule.selects_search({"risk": 0.20001}))
        rule.validate_candidate({"search_solver": "lcfr"})
        with self.assertRaises(ValueError):
            rule.validate_candidate({"search_solver": "cfr_plus"})

    def test_evaluation_compares_rule_with_no_op_search_and_oracle(self) -> None:
        matrix = {
            "experiment_type": "paired_leaf_error_matrix",
            "matrix_config": {},
            "environment": {},
            "run_count": 4,
            "wall_seconds": 1.0,
            "runs": [
                compact_run(0.1, -0.3),
                compact_run(0.1, 0.2),
                compact_run(0.3, -0.4, depth_limit=1),
                compact_run(0.3, 0.1, depth_limit=1),
            ],
        }

        result = evaluate_frozen_selection(matrix, rule_document())
        summary = result["summary"]
        self.assertEqual(summary["searched"], 2)
        self.assertEqual(summary["harmful_searches"], 1)
        self.assertEqual(summary["missed_beneficial_searches"], 1)
        self.assertEqual(summary["correct_no_ops"], 1)
        self.assertAlmostEqual(
            summary["selected_mean_nash_conv_delta_from_blueprint"],
            -0.025,
        )
        self.assertAlmostEqual(summary["mean_oracle_regret"], 0.15)
        self.assertAlmostEqual(
            result["baselines"]["unconditional_search"][
                "mean_nash_conv_delta_from_blueprint"
            ],
            -0.1,
        )
        depth_groups = result["subgroups"]["depth_limit"]
        self.assertEqual([group["value"] for group in depth_groups], [1, 2])

    def test_rule_digest_is_canonical_and_invalid_documents_fail(self) -> None:
        document = rule_document()
        reordered = {
            "status": document["status"],
            "rule": document["rule"],
            "name": document["name"],
            "schema_version": document["schema_version"],
        }
        self.assertEqual(rule_digest(document), rule_digest(reordered))
        document["status"] = "draft"
        with self.assertRaises(ValueError):
            FrozenSelectionRule.from_document(document)


if __name__ == "__main__":
    unittest.main()
