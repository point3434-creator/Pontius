from __future__ import annotations

import unittest

import numpy as np

from pontius.batched_factor_tt_contraction import contract_weighted_sum
from pontius.clean_fringe_tt import (
    compile_clean_fringe_plan,
    compile_clean_fringe_delta_terms,
    compose_clean_fringe_delta_train,
)
from pontius.factor_tt_contraction import FactorTTBeliefWorkspace, FactorTTTopology
from pontius.factorized_belief import FactorizedCardBelief
from pontius.incremental_policy_tt import (
    compile_policy_delta_tt_cache,
    plan_policy_delta_tt,
)
from pontius.public_policy_tt import dense_public_policy_root
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.river import HoleCards, parse_cards
from pontius.river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem
from pontius.showdown_value_rank_screen import (
    _payoff_operator,
    _policies,
    _rank_codes,
    _terminal_groups,
)
from pontius.tensor_train import TensorTrain


def _case() -> tuple[FactorizedCardBelief, MultiwayRiverHoldem]:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    available = tuple(card for card in range(52) if card not in set(board))
    cursor = 0
    axes: list[tuple[HoleCards, ...]] = []
    weights = []
    for player in range(3):
        hands = []
        row = []
        for hand_index in range(2):
            hands.append(tuple(sorted((available[cursor], available[cursor + 1]))))
            cursor += 2
            row.append(float(1 + player + hand_index))
        axes.append(tuple(hands))
        weights.append([row])
    belief = FactorizedCardBelief(
        hands_by_player=tuple(axes),
        mixture_weights=[1.0],
        unary_weights=tuple(weights),
        board=board,
    )
    materialized = belief.materialize()
    joint = {
        MultiwayRiverDeal(
            tuple(belief.hands_by_player[p][assignment[p]] for p in range(3))
        ): float(probability)
        for assignment, probability in zip(
            materialized.assignments, materialized.probabilities, strict=True
        )
    }
    game = MultiwayRiverHoldem.from_joint_weights(
        board=board,
        pot=12.0,
        stacks=(30.0,) * 3,
        bet_size=3.0,
        joint_weights=joint,
    )
    return belief, game


class CleanFringeTTTests(unittest.TestCase):
    def test_whole_seat_overlapping_edits_match_dense_and_scalar_oracles(self) -> None:
        belief, game = _case()
        layout = PublicTreeTensorEvaluator(game)
        axes = layout.hands_by_player
        groups = _terminal_groups(layout)
        rank_codes = _rank_codes(game.board, axes)
        dense = {}
        trains = {}
        for group in groups:
            values = _payoff_operator(
                group=group,
                rank_codes=rank_codes,
                pot=game.pot,
                bet_size=game.bet_size,
            )[0]
            dense[group.key] = values
            trains[group.key] = TensorTrain.from_dense(values)
        bounds = {key: 0.0 for key in trains}
        policies = _policies(layout.information_schema(), 17)
        baseline = policies["hashed_dense"]
        candidate = {key: dict(row) for key, row in baseline.items()}
        for node in layout.nodes:
            if node.player != 1:
                continue
            for key in node.information_keys:
                first, second = node.actions
                candidate[key][first], candidate[key][second] = (
                    candidate[key][second], candidate[key][first]
                )

        cache = compile_policy_delta_tt_cache(
            layout,
            axes,
            baseline,
            trains,
            bounds,
            relative_tolerance=0.0,
            maximum_rank=None,
        )
        policy_plan = plan_policy_delta_tt(cache, candidate)
        fringe_plan = compile_clean_fringe_plan(cache, policy_plan)
        delta = compose_clean_fringe_delta_train(
            cache,
            fringe_plan,
            belief_components=belief.component_count,
            split_index=1,
        )
        self.assertIsNotNone(delta.train)
        assert delta.train is not None
        expected_dense = dense_public_policy_root(
            layout, axes, candidate, dense
        ) - dense_public_policy_root(layout, axes, baseline, dense)
        np.testing.assert_allclose(
            delta.train.to_dense(), expected_dense, atol=2e-12, rtol=0.0
        )

        topology = FactorTTTopology.compile(belief, split_index=1)
        workspace = FactorTTBeliefWorkspace.compile(topology, belief)
        estimate = workspace.contract(delta.train).expectation
        streamed_terms = compile_clean_fringe_delta_terms(
            cache,
            fringe_plan,
            belief_components=belief.component_count,
            split_index=1,
        )
        streamed = contract_weighted_sum(
            workspace,
            streamed_terms.terms,
            maximum_feature_width_per_batch=4,
        ).expectation
        exact = (
            layout._expected_utilities(layout._prepare_policy(candidate))[0]
            - layout._expected_utilities(layout._prepare_policy(baseline))[0]
        )
        self.assertAlmostEqual(estimate, exact, delta=2e-12)
        self.assertAlmostEqual(streamed, exact, delta=2e-12)
        self.assertGreater(len(fringe_plan.frontier_nodes), 0)
        self.assertGreater(len(fringe_plan.delta_support_frontier_nodes), 0)
        self.assertLessEqual(
            len(fringe_plan.delta_support_frontier_nodes),
            len(fringe_plan.frontier_nodes),
        )
        self.assertEqual(delta.shared_fringe_error_bound, 0.0)

    def test_no_change_has_root_frontier_and_zero_delta(self) -> None:
        belief, game = _case()
        layout = PublicTreeTensorEvaluator(game)
        groups = _terminal_groups(layout)
        rank_codes = _rank_codes(game.board, layout.hands_by_player)
        trains = {}
        for group in groups:
            values = _payoff_operator(
                group=group,
                rank_codes=rank_codes,
                pot=game.pot,
                bet_size=game.bet_size,
            )[0]
            trains[group.key] = TensorTrain.from_dense(values)
        policy = _policies(layout.information_schema(), 19)["hashed_dense"]
        cache = compile_policy_delta_tt_cache(
            layout,
            layout.hands_by_player,
            policy,
            trains,
            {key: 0.0 for key in trains},
            relative_tolerance=0.0,
            maximum_rank=None,
        )
        fringe = compile_clean_fringe_plan(cache, plan_policy_delta_tt(cache, policy))
        delta = compose_clean_fringe_delta_train(
            cache, fringe, belief_components=1, split_index=1
        )
        self.assertEqual(fringe.frontier_nodes, (0,))
        self.assertEqual(fringe.delta_support_frontier_nodes, ())
        self.assertIsNone(delta.train)
        self.assertEqual(delta.shared_fringe_error_bound, 0.0)


if __name__ == "__main__":
    unittest.main()
