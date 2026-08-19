from __future__ import annotations

import copy
import unittest

from pontius.constrained_generation_matrix import run_constrained_generation_matrix
from pontius.opportunity_trace import (
    FORBIDDEN_ONLINE_NAME_FRAGMENTS,
    _fixed_checkpoint_selection,
    analyze_opportunity_matrices,
)


class OpportunityTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = run_constrained_generation_matrix(
            {
                "base": {
                    "blueprint_iterations": 20,
                    "max_updates": 4,
                    "verify_generated_responses": False,
                    "verify_realization_equivalence": False,
                },
                "axes": {"blueprint_solver": ["lcfr"]},
                "store_records": True,
                "deadline_milliseconds": [5.0],
            }
        )

    def test_builds_causal_phase_records_without_oracle_features(self) -> None:
        result = analyze_opportunity_matrices(
            [("development", self.matrix)],
            deadlines_ms=(5.0,),
            quantum_ms=0.1,
        )

        counts = result["phase_record_counts"]
        self.assertEqual(counts["boundary_start"], result["boundary_count"])
        self.assertGreater(counts["candidate_ready"], counts["boundary_start"])
        self.assertGreater(counts["after_pricing"], 0)
        self.assertEqual(result["status"], "measurement_only_no_scheduler_fit")
        self.assertEqual(
            len(result["blueprint_regime_allocation"]["regimes"]),
            1,
        )
        for record in result["records"]:
            for feature_name in record["features"]:
                self.assertFalse(
                    any(
                        fragment in feature_name
                        for fragment in FORBIDDEN_ONLINE_NAME_FRAGMENTS
                    ),
                    feature_name,
                )

        mutated = copy.deepcopy(self.matrix)
        for row in mutated["records"]:
            row["exact_sum_margin_optimum"] += 100.0
            row["exact_hidden_br_optimum"] += 200.0
            row["incumbent_hidden_br_reduction"] -= 300.0
        mutated_result = analyze_opportunity_matrices(
            [("development", mutated)],
            deadlines_ms=(5.0,),
            quantum_ms=0.1,
        )

        self.assertEqual(
            [record["features"] for record in result["records"]],
            [record["features"] for record in mutated_result["records"]],
        )
        self.assertNotEqual(
            [record["labels"] for record in result["records"]],
            [record["labels"] for record in mutated_result["records"]],
        )

    def test_candidate_ready_cannot_see_current_pricing_result(self) -> None:
        baseline = analyze_opportunity_matrices(
            [("development", self.matrix)],
            deadlines_ms=(5.0,),
            quantum_ms=0.1,
        )
        mutated = copy.deepcopy(self.matrix)
        row = next(record for record in mutated["records"] if record["update"] == 1)
        row["best_pricing_score"] = float(row["best_pricing_score"] or 0.0) + 123.0
        row["best_reduced_cost"] = float(row["best_reduced_cost"] or 0.0) + 456.0
        row["added_column"] = "counterfactual-pricing-output"
        row["columns_after_update"] += 1
        changed = analyze_opportunity_matrices(
            [("development", mutated)],
            deadlines_ms=(5.0,),
            quantum_ms=0.1,
        )
        boundary_id = f"development:{row['boundary_id']}"
        candidate_id = f"{boundary_id}:candidate:1"
        pricing_id = f"{boundary_id}:pricing:1"

        def features(result: dict, decision_id: str) -> dict:
            return next(
                record["features"]
                for record in result["records"]
                if record["decision_id"] == decision_id
            )

        self.assertEqual(
            features(baseline, candidate_id),
            features(changed, candidate_id),
        )
        self.assertNotEqual(
            features(baseline, pricing_id),
            features(changed, pricing_id),
        )

    def test_pooled_oracle_can_reallocate_an_easy_boundary_budget(self) -> None:
        template = self.matrix["records"][0]
        records = []
        for boundary_id, cost_ms, gain in (("A", 5.0, 1.0), ("B", 10.0, 10.0)):
            row = copy.deepcopy(template)
            row.update(
                {
                    "boundary_id": boundary_id,
                    "update": 1,
                    "actual_sum_margin": gain,
                    "actual_min_margin": 0.0,
                    "total_positive_frontier_violation": 0.0,
                    "safe_candidate": True,
                    "incumbent_updated": True,
                    "incumbent_sum_margin": gain,
                    "exact_sum_margin_optimum": gain,
                    "incumbent_hidden_br_reduction": gain,
                    "exact_hidden_br_optimum": gain,
                    "added_column": None,
                    "pricing_performed": False,
                    "pricing_seconds": 0.0,
                    "best_pricing_score": None,
                    "best_reduced_cost": None,
                    "converged": False,
                    "final_converged": False,
                    "final_update": 1,
                    "cumulative_candidate_compute_seconds": cost_ms / 1_000.0,
                    "cumulative_decision_compute_seconds": cost_ms / 1_000.0,
                }
            )
            records.append(row)
        matrix = {
            "experiment_type": "dynamic_constrained_generation_matrix",
            "records": records,
        }

        result = analyze_opportunity_matrices(
            [("synthetic", matrix)],
            deadlines_ms=(5.0,),
            quantum_ms=1.0,
        )
        oracle = result["allocation_oracles"][0]

        self.assertAlmostEqual(
            oracle["independent_phase_fit_oracle"]["aggregate_sum_margin"],
            1.0,
        )
        self.assertAlmostEqual(
            oracle["pooled_perfect_information"]["conservative_sum_margin"],
            10.0,
        )
        self.assertAlmostEqual(
            oracle["pooled_perfect_information"]["optimistic_sum_margin"],
            10.0,
        )
        self.assertEqual(
            oracle["best_uniform_checkpoint_under_aggregate_budget"][
                "uniform_update_budget"
            ],
            0,
        )

    def test_fixed_checkpoint_skips_only_its_terminal_pricing(self) -> None:
        early = copy.deepcopy(self.matrix["records"][0])
        later_one = copy.deepcopy(self.matrix["records"][0])
        later_two = copy.deepcopy(self.matrix["records"][1])
        early.update(
            {
                "update": 1,
                "final_converged": True,
                "final_update": 1,
                "cumulative_candidate_compute_seconds": 0.005,
                "cumulative_decision_compute_seconds": 0.009,
                "incumbent_sum_margin": 1.0,
            }
        )
        later_one.update(
            {
                "update": 1,
                "final_converged": False,
                "final_update": 2,
                "cumulative_candidate_compute_seconds": 0.004,
                "cumulative_decision_compute_seconds": 0.006,
            }
        )
        later_two.update(
            {
                "update": 2,
                "final_converged": False,
                "final_update": 2,
                "cumulative_candidate_compute_seconds": 0.010,
                "cumulative_decision_compute_seconds": 0.010,
            }
        )
        grouped = {"early": [early], "later": [later_one, later_two]}

        at_one = _fixed_checkpoint_selection(grouped, 1)
        at_two = _fixed_checkpoint_selection(grouped, 2)

        self.assertEqual(at_one[0]["cost_milliseconds"], 5.0)
        self.assertEqual(at_two[0]["cost_milliseconds"], 9.0)

    def test_invalid_sources_deadlines_and_quantum_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            analyze_opportunity_matrices([])
        with self.assertRaisesRegex(ValueError, "deadlines"):
            analyze_opportunity_matrices(
                [("development", self.matrix)], deadlines_ms=(float("nan"),)
            )
        with self.assertRaisesRegex(ValueError, "quantum"):
            analyze_opportunity_matrices(
                [("development", self.matrix)], quantum_ms=0.0
            )


if __name__ == "__main__":
    unittest.main()
