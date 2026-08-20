from __future__ import annotations

import unittest

import numpy as np

from pontius.factor_tt_contraction import FactorTTBeliefWorkspace, FactorTTTopology
from pontius.factorized_belief import FactorizedCardBelief
from pontius.factorized_belief_audit import _raw_factors, generate_hand_axes
from pontius.public_policy_tt import (
    compose_public_policy_root_tt,
    dense_public_policy_root,
    information_schema_for_axes,
    representative_public_tree,
)
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.river import parse_cards
from pontius.showdown_value_rank_screen import (
    _game_from_belief,
    _operator_groups,
    _policies,
    _terminal_groups,
)
from pontius.tensor_train import TensorTrain
from pontius.tensor_train_algebra import round_tensor_train


class PublicPolicyTTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        board = parse_cards("2c", "7d", "9h", "Js", "Qc")
        axes = generate_hand_axes(
            board=board,
            players=3,
            hands_per_player=2,
            family="balanced",
            seed=57,
        )
        mixture, unaries = _raw_factors(
            hands_by_player=axes,
            components=3,
            seed=57,
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
        cls.groups = _terminal_groups(cls.layout)
        cls.operators = _operator_groups(
            groups=cls.groups,
            board=board,
            hands_by_player=axes,
            pot=12.0,
            bet_size=3.0,
        )

    def test_axis_schema_matches_literal_materialized_layout(self) -> None:
        literal = PublicTreeTensorEvaluator(
            _game_from_belief(
                belief=self.belief,
                pot=12.0,
                stack=30.0,
                bet_size=3.0,
            )
        )
        self.assertEqual(
            information_schema_for_axes(self.layout, self.belief.hands_by_player),
            literal.information_schema(),
        )

    def test_exact_tt_public_policy_root_matches_independent_dense_oracle(self) -> None:
        schema = information_schema_for_axes(self.layout, self.belief.hands_by_player)
        policy = _policies(schema, 91)["hashed_dense"]
        dense_terminals = {
            key: values[0] for key, values in self.operators.items()
        }
        terminal_trains = {
            key: round_tensor_train(
                TensorTrain.from_dense(values),
                relative_tolerance=1e-13,
            ).train
            for key, values in dense_terminals.items()
        }
        dense_root = dense_public_policy_root(
            self.layout,
            self.belief.hands_by_player,
            policy,
            dense_terminals,
        )
        composition = compose_public_policy_root_tt(
            self.layout,
            self.belief.hands_by_player,
            policy,
            terminal_trains,
            relative_tolerance=1e-12,
            maximum_rank=None,
        )
        np.testing.assert_allclose(
            composition.root.to_dense(),
            dense_root,
            atol=1e-9,
            rtol=0.0,
        )
        topology = FactorTTTopology.compile(self.belief, split_index=1)
        workspace = FactorTTBeliefWorkspace.compile(topology, self.belief)
        direct = workspace.contract(composition.root).expectation
        materialized = self.belief.materialize()
        indices = np.asarray(materialized.assignments, dtype=np.int32)
        literal = float(materialized.probabilities @ dense_root[tuple(indices.T)])
        self.assertAlmostEqual(direct, literal, places=10)
        self.assertEqual(composition.strategic_rounds, self.layout.strategic_node_count)

    def test_terminal_schema_and_shape_mismatches_are_rejected(self) -> None:
        dense = {key: values[0] for key, values in self.operators.items()}
        missing = dict(dense)
        missing.pop(next(iter(missing)))
        with self.assertRaisesRegex(ValueError, "payoff groups"):
            dense_public_policy_root(
                self.layout,
                self.belief.hands_by_player,
                {},
                missing,
            )
        trains = {key: TensorTrain.from_dense(values) for key, values in dense.items()}
        trains[next(iter(trains))] = TensorTrain.from_dense(np.ones((2, 2)))
        with self.assertRaisesRegex(ValueError, "modes"):
            compose_public_policy_root_tt(
                self.layout,
                self.belief.hands_by_player,
                {},
                trains,
                relative_tolerance=1e-12,
                maximum_rank=8,
            )


if __name__ == "__main__":
    unittest.main()
