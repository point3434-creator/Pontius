from __future__ import annotations

import json
from pathlib import Path
import unittest

import numpy as np

from pontius.factorized_belief import FactorizedCardBelief
from pontius.real_policy_representation_audit_v2 import (
    _canonicalized_factorized_belief,
    parse_real_policy_representation_v2_config,
)
from pontius.river import parse_cards


class RealPolicyRepresentationAuditV2Tests(unittest.TestCase):
    def test_correction_config_freezes_the_unchanged_base_audit(self) -> None:
        path = (
            Path(__file__).parents[1]
            / "experiments"
            / "configs"
            / "real-policy-representation-audit-v2.json"
        )
        parsed = parse_real_policy_representation_v2_config(
            json.loads(path.read_text(encoding="utf-8"))
        )
        self.assertTrue(parsed["base_workload_and_gates_unchanged"])
        self.assertFalse(parsed["representation_results_observed_before_correction"])

    def test_axis_sort_carries_unary_columns_and_preserves_distribution(self) -> None:
        axes = (
            ((8, 9), (0, 1), (4, 5)),
            ((10, 11), (2, 3), (6, 7)),
        )
        mixture = np.array([1.0, 2.0])
        unaries = (
            np.array([[0.2, 0.4, 0.6], [0.3, 0.5, 0.7]]),
            np.array([[0.8, 1.0, 1.2], [0.9, 1.1, 1.3]]),
        )
        board = parse_cards("As", "Kd", "Qh", "Jc", "9s")
        ordinary = FactorizedCardBelief(
            hands_by_player=axes,
            mixture_weights=mixture,
            unary_weights=unaries,
            board=board,
        )
        corrected = _canonicalized_factorized_belief(
            hands_by_player=axes,
            mixture_weights=mixture,
            unary_weights=unaries,
            board=board,
        )
        first = ordinary.materialize()
        second = corrected.materialize()
        first_by_hands = {
            tuple(axes[player][assignment[player]] for player in range(2)): weight
            for assignment, weight in zip(
                first.assignments, first.unnormalized_weights, strict=True
            )
        }
        second_by_hands = {
            tuple(
                corrected.hands_by_player[player][assignment[player]]
                for player in range(2)
            ): weight
            for assignment, weight in zip(
                second.assignments, second.unnormalized_weights, strict=True
            )
        }
        self.assertEqual(set(first_by_hands), set(second_by_hands))
        for hands in first_by_hands:
            self.assertAlmostEqual(first_by_hands[hands], second_by_hands[hands])
        self.assertEqual(
            corrected.hands_by_player,
            tuple(tuple(sorted(hands)) for hands in axes),
        )


if __name__ == "__main__":
    unittest.main()
