from __future__ import annotations

import hashlib
import unittest

import numpy as np

from pontius.evaluation import Policy
from pontius.factor_tt_contraction import FactorTTBeliefWorkspace, FactorTTTopology
from pontius.factorized_belief import FactorizedCardBelief
from pontius.game import TERMINAL_PLAYER
from pontius.incremental_policy_tt import (
    compile_policy_delta_tt_cache_from_probabilities,
    compile_policy_probability_tape,
)
from pontius.open_mode_cfr_bridge import (
    dense_cfr_action_comparisons,
    open_mode_cfr_action_read,
)
from pontius.open_mode_factor_tt import (
    BidirectionalFactorTTTopology,
    OpenModeFactorTTWorkspace,
)
from pontius.public_policy_tt import _terminal_keys_by_slot
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.public_tree_tensor_cfr import PublicTreeTensorCFR
from pontius.river import HoleCards, parse_cards
from pontius.river_multiway import MultiwayRiverHoldem
from pontius.tensor_train import TensorTrain


def _game(players: int = 3, hands_per_player: int = 2) -> MultiwayRiverHoldem:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    available = tuple(card for card in range(52) if card not in set(board))
    cursor = 0
    ranges: list[dict[HoleCards, float]] = []
    for player in range(players):
        weights = {}
        for hand_index in range(hands_per_player):
            hand = tuple(sorted((available[cursor], available[cursor + 1])))
            cursor += 2
            weights[hand] = float(1 + player + 2 * hand_index)
        ranges.append(weights)
    return MultiwayRiverHoldem.from_independent_ranges(
        board=board,
        pot=12.0,
        stacks=(30.0,) * players,
        bet_size=3.0,
        player_weights=tuple(ranges),
    )


def _dense_policy(schema: dict[str, tuple[str, ...]]) -> Policy:
    result: Policy = {}
    for key, actions in schema.items():
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        weights = np.asarray(
            [1.0 + digest[index] % 13 for index in range(len(actions))],
            dtype=np.float64,
        )
        weights /= np.sum(weights)
        result[key] = {
            action: float(weights[index])
            for index, action in enumerate(actions)
        }
    return result


def _belief(layout: PublicTreeTensorEvaluator) -> FactorizedCardBelief:
    unaries = []
    for player, hands in enumerate(layout.hands_by_player):
        marginal = layout.game.marginal_distribution(player)
        unaries.append(
            np.asarray([[marginal[hand] for hand in hands]], dtype=np.float64)
        )
    belief = FactorizedCardBelief(
        hands_by_player=layout.hands_by_player,
        mixture_weights=[1.0],
        unary_weights=tuple(unaries),
        board=layout.game.board,
    )
    materialized = belief.materialize()
    self_weights = {
        assignment: probability
        for assignment, probability in zip(
            materialized.assignments,
            materialized.probabilities,
            strict=True,
        )
    }
    for deal_index, hand_ids in enumerate(layout.hand_ids):
        if abs(self_weights[tuple(int(value) for value in hand_ids)] - layout.weights[deal_index]) > 1e-14:
            raise AssertionError("test belief does not reproduce the public deal weights")
    return belief


def _terminal_trains(
    layout: PublicTreeTensorEvaluator,
    target: int,
) -> tuple[dict[str, TensorTrain], dict[str, float]]:
    keys = _terminal_keys_by_slot(layout)
    shape = tuple(len(hands) for hands in layout.hands_by_player)
    trains = {}
    for key in sorted(set(keys)):
        slot = keys.index(key)
        dense = np.full(shape, np.nan, dtype=np.float64)
        for deal_index, hand_ids in enumerate(layout.hand_ids):
            dense[tuple(int(value) for value in hand_ids)] = layout.terminal_values[
                slot, deal_index, target
            ]
        if np.any(np.isnan(dense)):
            raise AssertionError("test terminal Cartesian control is incomplete")
        trains[key] = TensorTrain.from_dense(dense)
    return trains, {key: 0.0 for key in trains}


def _workspace(
    belief: FactorizedCardBelief,
) -> OpenModeFactorTTWorkspace:
    base_topology = FactorTTTopology.compile(belief, split_index=1)
    base = FactorTTBeliefWorkspace.compile(
        base_topology,
        belief,
        query_chunk_records=2,
    )
    topology = BidirectionalFactorTTTopology.compile(base_topology)
    return OpenModeFactorTTWorkspace.compile(topology, base)


class OpenModeCFRBridgeTests(unittest.TestCase):
    def assert_comparison_close(self, actual: object, expected: object) -> None:
        for field in (
            "counterfactual_reaches",
            "action_numerators",
            "conditional_action_values",
            "policy_values",
            "regret_deltas",
        ):
            np.testing.assert_allclose(
                getattr(actual, field),
                getattr(expected, field),
                atol=2e-11,
                rtol=0.0,
                err_msg=field,
            )
        np.testing.assert_array_equal(actual.positive_reach, expected.positive_reach)
        np.testing.assert_array_equal(
            actual.selected_action_indices,
            expected.selected_action_indices,
        )

    def test_open_tables_match_literal_trace_and_actual_cfr_regret_change(self) -> None:
        layout = PublicTreeTensorEvaluator(_game())
        belief = _belief(layout)
        workspace = _workspace(belief)
        policy = _dense_policy(layout.information_schema())
        probabilities = compile_policy_probability_tape(
            layout, layout.hands_by_player, policy
        )

        for traverser in range(layout.num_players):
            terminal_trains, terminal_bounds = _terminal_trains(layout, traverser)
            cache = compile_policy_delta_tt_cache_from_probabilities(
                layout,
                layout.hands_by_player,
                probabilities,
                terminal_trains,
                terminal_bounds,
                relative_tolerance=0.0,
                maximum_rank=None,
            )
            expected_rows = dense_cfr_action_comparisons(
                layout, probabilities, traverser=traverser
            )
            self.assertGreater(len(expected_rows), 0)
            for expected in expected_rows:
                actual = open_mode_cfr_action_read(
                    workspace,
                    cache,
                    node_index=expected.node_index,
                    maximum_feature_width_per_batch=2,
                )
                self.assertEqual(actual.comparison.actions, expected.actions)
                self.assert_comparison_close(actual.comparison, expected)
                self.assertEqual(
                    len(actual.contraction.trains),
                    len(expected.actions),
                )

        # Player zero is traversed before any regret update can change the
        # cached strategy.  Its literal trace must therefore equal the actual
        # delta applied by the production quotient solver's first CFR step.
        solver = PublicTreeTensorCFR(layout, "cfr")
        solver.warm_start(policy, 1.0)
        before = solver.regret_table()
        expected_by_node = {
            row.node_index: row
            for row in dense_cfr_action_comparisons(
                layout, probabilities, traverser=0
            )
        }
        solver.step()
        after = solver.regret_table()
        for node_index, expected in expected_by_node.items():
            node = layout.nodes[node_index]
            for hand_index, key in enumerate(node.information_keys):
                for action_index, action in enumerate(node.actions):
                    self.assertAlmostEqual(
                        after[key][action] - before[key][action],
                        expected.regret_deltas[hand_index, action_index],
                        places=11,
                    )

    def test_zero_reach_selects_first_action_and_leaves_regret_row_unchanged(self) -> None:
        layout = PublicTreeTensorEvaluator(_game())
        belief = _belief(layout)
        workspace = _workspace(belief)
        policy = _dense_policy(layout.information_schema())
        original = compile_policy_probability_tape(
            layout, layout.hands_by_player, policy
        )

        root = layout.nodes[0]
        self.assertNotEqual(root.player, TERMINAL_PLAYER)
        selected_child = root.children[0]
        descendant = next(
            node_index
            for node_index in range(selected_child, layout.public_node_count)
            if layout.nodes[node_index].player not in (TERMINAL_PLAYER, root.player)
            and layout.nodes[node_index].history[:1] == (
                (root.player, root.actions[0]),
            )
        )
        target = layout.nodes[descendant].player
        edited = list(original)
        root_values = np.zeros_like(original[0])
        assert root_values is not None
        root_values[:, 1:] = 1.0 / (len(root.actions) - 1)
        root_values.flags.writeable = False
        edited[0] = root_values
        probabilities = tuple(edited)

        terminal_trains, terminal_bounds = _terminal_trains(layout, target)
        cache = compile_policy_delta_tt_cache_from_probabilities(
            layout,
            layout.hands_by_player,
            probabilities,
            terminal_trains,
            terminal_bounds,
            relative_tolerance=0.0,
            maximum_rank=None,
        )
        expected = {
            row.node_index: row
            for row in dense_cfr_action_comparisons(
                layout,
                probabilities,
                traverser=target,
            )
        }[descendant]
        actual = open_mode_cfr_action_read(
            workspace,
            cache,
            node_index=descendant,
            maximum_feature_width_per_batch=2,
        ).comparison

        self.assert_comparison_close(actual, expected)
        self.assertEqual(actual.zero_reach_hands, len(actual.positive_reach))
        np.testing.assert_array_equal(
            actual.selected_action_indices,
            np.zeros_like(actual.selected_action_indices),
        )
        np.testing.assert_array_equal(actual.regret_deltas, 0.0)
        seeded = np.asarray(
            [[0.25 + hand, 0.75 + hand] for hand in range(len(actual.positive_reach))],
            dtype=np.float64,
        )
        np.testing.assert_array_equal(seeded + actual.regret_deltas, seeded)


if __name__ == "__main__":
    unittest.main()
