from __future__ import annotations

import unittest

import numpy as np

from pontius.factorized_belief import FactorizedCardBelief
from pontius.factorized_belief_audit import _raw_factors, generate_hand_axes
from pontius.incremental_policy_tt import (
    ancestor_closure,
    compile_policy_delta_tt_cache,
    recompose_policy_delta_tt,
)
from pontius.public_policy_tt import (
    _information_key,
    dense_public_policy_root,
    information_schema_for_axes,
    representative_public_tree,
)
from pontius.river import parse_cards
from pontius.showdown_value_rank_screen import (
    _operator_groups,
    _policies,
    _terminal_groups,
)
from pontius.tensor_train import TensorTrain
from pontius.tensor_train_algebra import round_tensor_train


def _copy_policy(policy: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    return {key: dict(distribution) for key, distribution in policy.items()}


class IncrementalPolicyTTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        board = parse_cards("2c", "7d", "9h", "Js", "Qc")
        axes = generate_hand_axes(
            board=board,
            players=3,
            hands_per_player=2,
            family="balanced",
            seed=713,
        )
        mixture, unaries = _raw_factors(
            hands_by_player=axes,
            components=2,
            seed=713,
            family="balanced",
        )
        cls.belief = FactorizedCardBelief(
            hands_by_player=axes,
            mixture_weights=mixture,
            unary_weights=unaries,
            board=board,
        )
        cls.layout = representative_public_tree(
            cls.belief,
            pot=12.0,
            stack=30.0,
            bet_size=3.0,
        )
        schema = information_schema_for_axes(cls.layout, axes)
        cls.baseline_policy = _policies(schema, 991)["hashed_dense"]
        operators = _operator_groups(
            groups=_terminal_groups(cls.layout),
            board=board,
            hands_by_player=axes,
            pot=12.0,
            bet_size=3.0,
        )
        cls.dense_terminals = {
            key: values[0].copy(order="C") for key, values in operators.items()
        }
        cls.terminal_trains = {}
        cls.terminal_bounds = {}
        for key, values in cls.dense_terminals.items():
            rounded = round_tensor_train(
                TensorTrain.from_dense(values),
                relative_tolerance=1e-13,
            )
            cls.terminal_trains[key] = rounded.train
            cls.terminal_bounds[key] = rounded.discarded_frobenius_bound

    def _compile(self, policy: dict[str, dict[str, float]]):
        return compile_policy_delta_tt_cache(
            self.layout,
            self.belief.hands_by_player,
            policy,
            self.terminal_trains,
            self.terminal_bounds,
            relative_tolerance=1e-12,
            maximum_rank=None,
        )

    def _swap_at_node(
        self,
        policy: dict[str, dict[str, float]],
        node_index: int,
        hand_index: int,
    ) -> dict[str, dict[str, float]]:
        candidate = _copy_policy(policy)
        node = self.layout.nodes[node_index]
        hand = self.belief.hands_by_player[node.player][hand_index]
        key = _information_key(self.layout, node.player, hand, node.history)
        first, second = node.actions
        distribution = candidate[key]
        distribution[first], distribution[second] = (
            distribution[second],
            distribution[first],
        )
        return candidate

    def test_single_deep_node_edit_recomputes_only_ancestor_path(self) -> None:
        baseline = self._compile(self.baseline_policy)
        strategic = [
            index for index, node in enumerate(self.layout.nodes) if node.children
        ]
        deepest = max(strategic, key=lambda index: int(baseline.depths[index]))
        candidate = self._swap_at_node(self.baseline_policy, deepest, 0)
        delta = recompose_policy_delta_tt(baseline, candidate)

        self.assertEqual(delta.changed_policy_nodes, (deepest,))
        expected = ancestor_closure(baseline.parents, (deepest,))
        self.assertEqual(delta.dirty_nodes, expected)
        self.assertEqual(delta.recomputed_strategic_nodes, len(expected))
        self.assertEqual(
            delta.reused_node_train_objects,
            self.layout.public_node_count - len(expected),
        )
        for index in set(range(self.layout.public_node_count)) - set(expected):
            self.assertIs(baseline.node_trains[index], delta.cache.node_trains[index])

    def test_incremental_root_and_bound_match_cold_and_dense(self) -> None:
        baseline = self._compile(self.baseline_policy)
        candidate = self._swap_at_node(self.baseline_policy, 0, 0)
        incremental = recompose_policy_delta_tt(baseline, candidate).cache
        cold = self._compile(candidate)
        dense = dense_public_policy_root(
            self.layout,
            self.belief.hands_by_player,
            candidate,
            self.dense_terminals,
        )

        np.testing.assert_allclose(
            incremental.root.to_dense(),
            cold.root.to_dense(),
            atol=1e-12,
            rtol=0.0,
        )
        actual_error = float(np.max(np.abs(incremental.root.to_dense() - dense)))
        machine = (
            np.finfo(np.float64).eps
            * 256.0
            * incremental.public_depth
            * 30.0
        )
        self.assertLessEqual(actual_error, incremental.root_bound + machine)
        self.assertGreater(incremental.numeric_bytes, incremental.root.storage_bytes)

    def test_terminal_bound_schema_is_strict(self) -> None:
        bounds = dict(self.terminal_bounds)
        bounds.pop(next(iter(bounds)))
        with self.assertRaisesRegex(ValueError, "keys"):
            compile_policy_delta_tt_cache(
                self.layout,
                self.belief.hands_by_player,
                self.baseline_policy,
                self.terminal_trains,
                bounds,
                relative_tolerance=1e-12,
                maximum_rank=None,
            )


if __name__ == "__main__":
    unittest.main()
