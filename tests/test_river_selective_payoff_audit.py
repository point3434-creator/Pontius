from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from pontius.river_selective_payoff_audit import (
    _difference_paths,
    _signature_error,
    _validate_config,
    searched_payoff_span,
)


class RiverSelectivePayoffAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(
            Path(
                "experiments/configs/river-selective-payoff-span-correction-audit-v1.json"
            ).read_text(encoding="utf-8")
        )

    def test_frozen_config_parses_without_relaxing_mutation_scope(self) -> None:
        parsed = _validate_config(self.config)
        self.assertEqual(parsed["old_span_field"], "target_payoff_span")
        self.assertEqual(
            parsed["mutated_fields"],
            ("targets[*].boundary_online_features.target_payoff_span",),
        )
        self.assertEqual(parsed["gates"]["maximum_nonspan_field_mutations"], 0.0)

    def test_searched_span_uses_the_full_action_universe(self) -> None:
        self.assertEqual(
            searched_payoff_span(12.0, (0.25, 0.5, 0.75), (1.5, 2.0)),
            60.0,
        )
        self.assertEqual(
            searched_payoff_span(20.0, (0.25, 0.5, 0.75), (1.5, 2.0)),
            100.0,
        )
        with self.assertRaisesRegex(ValueError, "positive"):
            searched_payoff_span(0.0, (0.5,), (1.5,))

    def test_recursive_difference_audit_detects_only_exact_mutated_path(self) -> None:
        source = {
            "targets": [
                {
                    "boundary_online_features": {
                        "target_payoff_span": 10.0,
                        "target_pot": 4.0,
                    }
                }
            ],
            "labels": [1.0, 2.0],
        }
        corrected = copy.deepcopy(source)
        corrected["targets"][0]["boundary_online_features"]["target_payoff_span"] = 20.0
        self.assertEqual(
            _difference_paths(source, corrected),
            ["targets[0].boundary_online_features.target_payoff_span"],
        )
        corrected["labels"][1] = 3.0
        self.assertEqual(
            set(_difference_paths(source, corrected)),
            {
                "targets[0].boundary_online_features.target_payoff_span",
                "labels[1]",
            },
        )

    def test_quality_signature_comparison_separates_numeric_and_structure(self) -> None:
        signature = {
            "fixed": {
                "raw_reduction": 1.0,
                "normalized_reduction": 0.1,
                "selection_counts": {"b3r2": 2},
                "state_visits": 20,
            },
            "selected": {
                "candidate_id": "fixed_b3r2",
                "raw_reduction": 1.0,
                "normalized_reduction": 0.1,
                "selection_counts": {"b3r2": 2},
                "state_visits": 20,
            },
            "leaderboard": {
                "candidate": {
                    "raw_reduction": 1.1,
                    "normalized_reduction": 0.11,
                    "selection_counts": {"b3r1": 1, "b3r2": 1},
                    "state_visits": 15,
                }
            },
            "gates": {"quality": False},
        }
        perturbed = copy.deepcopy(signature)
        perturbed["leaderboard"]["candidate"]["normalized_reduction"] += 1e-13
        error, identity = _signature_error(signature, perturbed)
        self.assertLessEqual(error, 1.1e-13)
        self.assertTrue(identity)
        perturbed["leaderboard"]["candidate"]["selection_counts"] = {"b3r2": 2}
        _, identity = _signature_error(signature, perturbed)
        self.assertFalse(identity)

    def test_post_freeze_formula_or_mutation_expansion_is_rejected(self) -> None:
        changed = dict(self.config)
        changed["correction_formula"] = "pot"
        with self.assertRaisesRegex(ValueError, "frozen"):
            _validate_config(changed)
        changed = dict(self.config)
        changed["mutated_fields"] = [
            "targets[*].boundary_online_features.target_payoff_span",
            "records[*].nash_conv_reduction_from_blueprint",
        ]
        with self.assertRaisesRegex(ValueError, "frozen"):
            _validate_config(changed)


if __name__ == "__main__":
    unittest.main()
