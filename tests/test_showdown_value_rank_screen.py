from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from pontius.factorized_belief import FactorizedCardBelief
from pontius.factorized_belief_audit import _raw_factors, generate_hand_axes
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.river import parse_cards
from pontius.showdown_value_rank_screen import (
    _decompose_operators,
    _game_from_belief,
    _operator_groups,
    _terminal_groups,
    _terminal_tensor_for_layout,
    parse_showdown_value_rank_config,
)
from pontius.terminal_tensor_evaluation import evaluate_with_terminal_values

_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "showdown-value-operator-rank-screen-v1.json"
)


def config() -> dict[str, object]:
    return json.loads(_CONFIG.read_text(encoding="utf-8"))


class ShowdownValueRankScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parsed = parse_showdown_value_rank_config(config())
        board = parse_cards(*cls.parsed["board"])
        axes = generate_hand_axes(
            board=board,
            players=6,
            hands_per_player=2,
            family="balanced",
            seed=31,
        )
        mixture, unaries = _raw_factors(
            hands_by_player=axes,
            components=1,
            seed=31,
            family="balanced",
        )
        belief = FactorizedCardBelief(
            hands_by_player=axes,
            mixture_weights=mixture,
            unary_weights=unaries,
            board=board,
        )
        cls.axes = axes
        cls.layout = PublicTreeTensorEvaluator(
            _game_from_belief(
                belief=belief,
                pot=12.0,
                stack=30.0,
                bet_size=3.0,
            )
        )
        cls.groups = _terminal_groups(cls.layout)
        cls.operators = _operator_groups(
            groups=cls.groups,
            board=board,
            hands_by_player=axes,
            pot=12.0,
            bet_size=3.0,
        )

    def test_frozen_config_and_terminal_group_count(self) -> None:
        self.assertEqual(self.parsed["rank_caps"], (1, 2, 4, 8, 16, 32))
        self.assertEqual(len(self.groups), 64)
        self.assertEqual(
            sum(len(group.terminal_slots) for group in self.groups),
            self.layout.terminal_node_count,
        )

    def test_full_cartesian_payoff_extension_gathers_literal_compatible_values(self) -> None:
        terminal = _terminal_tensor_for_layout(
            layout=self.layout,
            groups=self.groups,
            reconstructed=self.operators,
            hands_by_player=self.axes,
        )
        np.testing.assert_allclose(
            terminal,
            self.layout.terminal_values,
            atol=1e-12,
            rtol=0.0,
        )
        self.assertLessEqual(float(np.max(np.abs(np.sum(terminal, axis=2)))), 1e-12)
        expected = self.layout.evaluate({})
        actual = evaluate_with_terminal_values(self.layout, {}, terminal)
        self.assertEqual(actual.best_response_actions, expected.best_response_actions)

    def test_untruncated_operator_decomposition_is_exact_and_zero_sum(self) -> None:
        one_operator = {self.groups[0].key: self.operators[self.groups[0].key]}
        rows, retained = _decompose_operators(
            operators=one_operator,
            arms=("rank_1", "untruncated_tt_svd"),
            numerical_rank_threshold=1e-12,
            retain_reconstructions=True,
        )
        exact = next(row for row in rows if row["arm"] == "untruncated_tt_svd")
        self.assertLessEqual(exact["maximum_absolute_operator_error"], 1e-10)
        self.assertLessEqual(exact["maximum_zero_sum_error"], 1e-10)
        self.assertEqual(set(retained), {"rank_1", "untruncated_tt_svd"})

    def test_unknown_stage_hash_rank_and_gate_mutations_fail(self) -> None:
        unknown = config()
        unknown["fit_rank_by_family"] = True
        with self.assertRaisesRegex(ValueError, "fields differ"):
            parse_showdown_value_rank_config(unknown)

        hidden = config()
        hidden["evidence_stage"] = "validation"
        with self.assertRaisesRegex(ValueError, "revealed engineering"):
            parse_showdown_value_rank_config(hidden)

        changed_hash = config()
        changed_hash["expected_factorized_belief_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash mismatch"):
            parse_showdown_value_rank_config(changed_hash)

        changed_rank = config()
        changed_rank["rank_caps"] = [1, 2, 4, 8]
        with self.assertRaisesRegex(ValueError, "differs from ADR-0063"):
            parse_showdown_value_rank_config(changed_rank)

        relaxed = config()
        relaxed["gates"]["maximum_safe_action_mismatches"] = 1
        with self.assertRaisesRegex(ValueError, "must remain zero"):
            parse_showdown_value_rank_config(relaxed)


if __name__ == "__main__":
    unittest.main()
