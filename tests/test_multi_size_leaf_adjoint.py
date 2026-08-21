from __future__ import annotations

import hashlib
import importlib.util
from itertools import product
import unittest

import numpy as np

from pontius.factorized_belief import FactorizedCardBelief
from pontius.incremental_policy_tt import compile_policy_probability_tape
from pontius.multi_size_leaf_adjoint import (
    build_multi_size_leaf_adjoint_terminal_automata,
    multi_size_leaf_adjoint_cfr_traverser,
    multi_size_terminal_groups,
    multi_size_terminal_keys_by_slot,
)
from pontius.multi_size_public_tree_tensor import MultiSizePublicTreeTensorEvaluator
from pontius.open_mode_audit import _open_workspace
from pontius.open_mode_cfr_bridge import dense_cfr_action_comparisons
from pontius.river import HoleCards, parse_cards
from pontius.river_multiway import MultiwayRiverDeal
from pontius.river_multiway_multi_size import MultiwayMultiSizeRiverHoldem
from pontius.showdown_value_rank_screen import _rank_codes
from pontius.sparse_incidence_open_mode import SparseBidirectionalIncidence


def _fixture() -> tuple[
    FactorizedCardBelief,
    MultiSizePublicTreeTensorEvaluator,
    object,
    SparseBidirectionalIncidence,
]:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    available = [card for card in range(52) if card not in set(board)]
    hands: list[tuple[HoleCards, ...]] = []
    cursor = 0
    for _ in range(6):
        cards = available[cursor : cursor + 4]
        cursor += 4
        hands.append(
            (
                tuple(sorted((cards[0], cards[1]))),
                tuple(sorted((cards[2], cards[3]))),
            )
        )
    axes = tuple(hands)
    belief = FactorizedCardBelief(
        hands_by_player=axes,
        mixture_weights=np.ones(1),
        unary_weights=tuple(np.ones((1, 2)) for _ in range(6)),
        board=board,
    )
    materialized = belief.materialize()
    joint = {
        MultiwayRiverDeal(tuple(axes[seat][indices[seat]] for seat in range(6))): mass
        for indices, mass in zip(
            materialized.assignments,
            materialized.probabilities,
            strict=True,
        )
    }
    game = MultiwayMultiSizeRiverHoldem.from_joint_weights(
        board=board,
        pot=12.0,
        stacks=(30.0,) * 6,
        bet_sizes=(3.0, 6.0),
        joint_weights=joint,
    )
    layout = MultiSizePublicTreeTensorEvaluator(game)
    workspace, _ = _open_workspace(belief, split_index=3, query_chunk_records=256)
    sparse = SparseBidirectionalIncidence.compile(workspace)
    return belief, layout, workspace, sparse


def _policy(layout: MultiSizePublicTreeTensorEvaluator) -> dict[str, dict[object, float]]:
    result = {}
    for key, actions in layout.information_schema().items():
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        weights = tuple(float(1 + digest[index] % 23) for index in range(len(actions)))
        total = sum(weights)
        result[key] = {
            action: weights[index] / total
            for index, action in enumerate(actions)
        }
    return result


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class MultiSizeLeafAdjointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.belief, cls.layout, cls.workspace, cls.sparse = _fixture()
        cls.codes = tuple(
            np.ascontiguousarray(values, dtype=np.int32)
            for values in _rank_codes(
                cls.belief.board,
                cls.belief.hands_by_player,
            )
        )
        cls.automata = build_multi_size_leaf_adjoint_terminal_automata(
            cls.layout,
            cls.codes,
            pot=12.0,
        )
        cls.policy = _policy(cls.layout)
        cls.probabilities = compile_policy_probability_tape(
            cls.layout,
            cls.belief.hands_by_player,
            cls.policy,
        )

    def test_terminal_groups_keep_bet_sizes_distinct_and_match_dense_values(self) -> None:
        groups = multi_size_terminal_groups(self.layout)
        self.assertEqual(len(groups), 127)
        self.assertEqual(len(multi_size_terminal_keys_by_slot(self.layout)), 385)
        assignments = tuple(product(range(2), repeat=6))
        slot_by_key = {
            group.key: group.terminal_slots[0]
            for group in groups
        }
        maximum = 0.0
        for target, library in enumerate(self.automata):
            for key, automaton in library.items():
                dense = self.layout.terminal_values[
                    slot_by_key[key],
                    :,
                    target,
                ].reshape((2,) * 6)
                maximum = max(
                    maximum,
                    float(np.max(np.abs(automaton.to_dense() - dense))),
                )
                sampled = automaton.evaluate_assignments(assignments)
                np.testing.assert_allclose(sampled, dense.reshape(-1), atol=1e-13, rtol=0.0)
        self.assertLessEqual(maximum, 1e-13)

    def test_leaf_adjoint_action_tables_match_dense_deal_axis(self) -> None:
        traverser = 3
        expected = {
            row.node_index: row
            for row in dense_cfr_action_comparisons(
                self.layout,
                self.probabilities,
                traverser=traverser,
            )
        }
        actual = multi_size_leaf_adjoint_cfr_traverser(
            self.layout,
            self.workspace,
            self.sparse,
            self.probabilities,
            self.automata[traverser],
            traverser=traverser,
            maximum_feature_width_per_batch=96,
        )
        self.assertEqual(actual.terminal_contractions, 385)
        self.assertEqual(len(actual.reads), 63)
        maximum = 0.0
        for row in actual.reads:
            oracle = expected[row.node_index]
            maximum = max(
                maximum,
                float(np.max(np.abs(row.counterfactual_reaches - oracle.counterfactual_reaches))),
                float(np.max(np.abs(row.action_numerators - oracle.action_numerators))),
                float(np.max(np.abs(row.regret_deltas - oracle.regret_deltas))),
            )
            actual_selected = np.argmax(row.action_numerators, axis=1)
            actual_selected[~row.positive_reach] = 0
            np.testing.assert_array_equal(actual_selected, oracle.selected_action_indices)
        self.assertLessEqual(maximum, 2e-11)
        self.assertLessEqual(actual.maximum_child_reach_disagreement, 2e-13)


if __name__ == "__main__":
    unittest.main()
