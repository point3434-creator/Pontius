from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from pontius.multiway_search_experiment import (
    parse_multiway_search_config,
    run_multiway_search_experiment,
)


ROOT = Path(__file__).parents[1]
FROZEN = json.loads(
    (
        ROOT
        / "experiments"
        / "configs"
        / "multiway-river-search-acceptance-development-v1.json"
    ).read_text(encoding="utf-8")
)


def tiny_config() -> dict[str, object]:
    config = copy.deepcopy(FROZEN)
    config.update(
        {
            "requested_groups": 1,
            "seed": 0,
            "hands_per_player": 2,
            "families": ["balanced"],
            "pot_options": [12.0],
            "bet_to_pot_options": [0.5],
            "range_weight_options": [1.0],
            "target_specs": [FROZEN["target_specs"][0]],
            "blueprint_quality_checkpoints": [2, 4],
            "maximum_source_normalized_nash_conv": 1.0,
            "candidate_solvers": ["dcfr"],
            "candidate_checkpoints": [1, 2],
            "primary_solver": "dcfr",
            "primary_checkpoint": 2,
        }
    )
    config["gates"].update(
        {
            "minimum_development_groups": 1,
            "hot_tape_strictly_faster_than_ordinary_evaluation": False,
            "two_candidate_reuse_strictly_faster_than_two_ordinary_evaluations": False,
            "primary_aggregate_acceptance_strictly_beats_blind_raw_reduction": False,
            "primary_aggregate_acceptance_hot_rate_strictly_beats_blind": False,
            "minimum_primary_unilateral_accept_target_fraction": 0.0,
            "minimum_primary_coalition_accept_target_fraction": 0.0,
            "primary_coalition_acceptance_has_positive_normalized_reduction": False,
        }
    )
    return config


class MultiwaySearchExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_multiway_search_experiment(tiny_config())

    def test_frozen_config_and_all_source_hashes_parse(self) -> None:
        parsed = parse_multiway_search_config(copy.deepcopy(FROZEN))
        self.assertEqual(parsed["included_splits"], ("development",))
        self.assertEqual(parsed["primary_solver"], "dcfr")
        self.assertEqual(parsed["primary_checkpoint"], 32)

    def test_tiny_run_has_exact_nested_acceptance_records(self) -> None:
        self.assertEqual(
            self.result["experiment_type"],
            "multiway_river_full_search_acceptance_development",
        )
        self.assertEqual(
            self.result["counts"],
            {
                "groups": 1,
                "contexts": 1,
                "targets": 1,
                "candidate_records": 2,
                "reserved_contexts_materialized": 0,
            },
        )
        self.assertTrue(self.result["gates"]["correctness_passed"])
        self.assertTrue(self.result["gates"]["passed"])
        self.assertEqual(
            self.result["aggregate"]["best_response_action_mismatches"],
            0,
        )
        self.assertLessEqual(
            self.result["aggregate"]["maximum_absolute_evaluation_error"],
            1e-10,
        )
        for row in self.result["records"]:
            acceptance = row["acceptance"]
            if acceptance["coalition_stress"]:
                self.assertTrue(acceptance["unilateral_pareto"])
            if acceptance["unilateral_pareto"]:
                self.assertTrue(acceptance["aggregate_exact"])
            self.assertGreater(row["timing_ms"]["charged"]["blind"], 0.0)
            self.assertGreater(
                row["timing_ms"]["charged"]["tape_exact_one_shot"],
                row["timing_ms"]["charged"]["blind"],
            )

    def test_arm_quality_is_monotone_under_nested_positive_acceptance(self) -> None:
        summary = self.result["primary_summary"]
        reductions = summary["arm_raw_reduction"]
        self.assertGreaterEqual(reductions["aggregate_exact"], reductions["unilateral_pareto"])
        self.assertGreaterEqual(reductions["unilateral_pareto"], reductions["coalition_stress"])
        self.assertGreaterEqual(reductions["aggregate_exact"], reductions["blind"])
        self.assertGreaterEqual(reductions["coalition_stress"], 0.0)

    def test_target_and_solver_features_do_not_mix_future_labels(self) -> None:
        target_features = self.result["targets"][0]["boundary_features"]
        solver_features = self.result["records"][0]["causal_solver_features"]
        forbidden = ("nash_conv", "deviation_gain", "coalition", "accept")
        self.assertFalse(any(token in key for key in target_features for token in forbidden))
        self.assertFalse(any(token in key for key in solver_features for token in forbidden))

    def test_hash_split_and_schema_mutations_are_rejected(self) -> None:
        changed_hash = tiny_config()
        changed_hash["expected_context_generator_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "frozen hash mismatch"):
            parse_multiway_search_config(changed_hash)

        reserved = tiny_config()
        reserved["included_splits"] = ["development", "validation"]
        with self.assertRaisesRegex(ValueError, "only development"):
            parse_multiway_search_config(reserved)

        unknown = tiny_config()
        unknown["post_label_override"] = True
        with self.assertRaisesRegex(ValueError, "fields differ"):
            parse_multiway_search_config(unknown)


if __name__ == "__main__":
    unittest.main()
