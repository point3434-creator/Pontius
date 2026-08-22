from __future__ import annotations

import importlib.util
from types import SimpleNamespace
import unittest

import numpy as np

from pontius.behavioral_open_axis import behavioral_open_axis_payoff_row
from pontius.continuation_public_tree_tensor import (
    ContinuationPublicTreeTensorEvaluator,
)
from pontius.cross_payoff_leaf_adjoint import evaluate_cross_payoff_leaf_adjoint
from pontius.incremental_policy_tt import compile_policy_probability_tape
from pontius.leaf_adjoint_cfr import build_leaf_adjoint_terminal_automata
from pontius.showdown_value_rank_screen import _rank_codes
from pontius.sequence_form_open_axis import (
    splice_fixed_response_probability_tape_for_axes,
)
import tests.test_leaf_adjoint_cfr as leaf_fixture
import tests.test_sparse_open_mode_cfr as sparse_fixture


def _endpoint_policy(layout: object, source: dict, acting_player: int) -> dict:
    result = {key: dict(row) for key, row in source.items()}
    for node_index, node in enumerate(layout.nodes):
        if node.player != acting_player:
            continue
        for hand_index, key in enumerate(node.information_keys):
            selected = (node_index + hand_index + 1) % len(node.actions)
            result[key] = {
                action: float(action_index == selected)
                for action_index, action in enumerate(node.actions)
            }
    return result


def _fixed_response_policy(layout: object, source: dict, actions: dict) -> dict:
    result = {key: dict(row) for key, row in source.items()}
    schema = layout.information_schema()
    for key, selected in actions.items():
        result[key] = {
            action: float(action == selected) for action in schema[key]
        }
    return result


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class BehavioralOpenAxisTests(unittest.TestCase):
    def test_post_bet_full_behavioral_row_matches_dense_endpoint(self) -> None:
        sparse_fixture.SparseOpenModeCFRTests.setUpClass()
        source = sparse_fixture.SparseOpenModeCFRTests
        layout = ContinuationPublicTreeTensorEvaluator(
            source.layout.game,
            public_prefix=((0, "check"), (1, "bet")),
        )
        hands = source.belief.hands_by_player
        probabilities = compile_policy_probability_tape(layout, hands, source.policy)
        acting_player = 0
        payoff_player = 3
        endpoint_policy = _endpoint_policy(layout, source.policy, acting_player)
        endpoint = compile_policy_probability_tape(layout, hands, endpoint_policy)
        codes = tuple(
            np.ascontiguousarray(values, dtype=np.int32)
            for values in _rank_codes(source.board, hands)
        )
        automata = build_leaf_adjoint_terminal_automata(
            layout,
            codes,
            pot=12.0,
            bet_size=3.0,
        )
        result = evaluate_cross_payoff_leaf_adjoint(
            layout,
            source.workspace,
            source.sparse,
            probabilities,
            automata[payoff_player],
            acting_player=acting_player,
            payoff_player=payoff_player,
            maximum_feature_width_per_batch=96,
        )
        source_value = layout.evaluate(source.policy).evaluation.utilities[payoff_player]
        row = behavioral_open_axis_payoff_row(
            layout,
            probabilities,
            result,
            acting_player=acting_player,
            source_value=source_value,
        )
        endpoint_value = layout.evaluate(endpoint_policy).evaluation.utilities[
            payoff_player
        ]
        self.assertLessEqual(abs(row.value(probabilities) - source_value), 2e-12)
        self.assertLessEqual(abs(row.value(endpoint) - endpoint_value), 2e-12)
        self.assertEqual(len(row.nodes), 16)

    def test_post_bet_full_fixed_response_row_matches_dense_endpoint(self) -> None:
        sparse_fixture.SparseOpenModeCFRTests.setUpClass()
        source = sparse_fixture.SparseOpenModeCFRTests
        layout = ContinuationPublicTreeTensorEvaluator(
            source.layout.game,
            public_prefix=((0, "check"), (1, "bet")),
        )
        hands = source.belief.hands_by_player
        probabilities = compile_policy_probability_tape(layout, hands, source.policy)
        acting_player = 0
        payoff_player = 3
        endpoint_policy = _endpoint_policy(layout, source.policy, acting_player)
        endpoint = compile_policy_probability_tape(layout, hands, endpoint_policy)
        codes = tuple(
            np.ascontiguousarray(values, dtype=np.int32)
            for values in _rank_codes(source.board, hands)
        )
        automata = build_leaf_adjoint_terminal_automata(
            layout,
            codes,
            pot=12.0,
            bet_size=3.0,
        )
        actions = layout.evaluate(source.policy).best_response_actions[payoff_player]
        response_probabilities = splice_fixed_response_probability_tape_for_axes(
            layout,
            probabilities,
            actions,
            responding_player=payoff_player,
            hands_by_player=hands,
        )
        result = evaluate_cross_payoff_leaf_adjoint(
            layout,
            source.workspace,
            source.sparse,
            response_probabilities,
            automata[payoff_player],
            acting_player=acting_player,
            payoff_player=payoff_player,
            maximum_feature_width_per_batch=96,
        )
        source_response_policy = _fixed_response_policy(
            layout,
            source.policy,
            actions,
        )
        endpoint_response_policy = _fixed_response_policy(
            layout,
            endpoint_policy,
            actions,
        )
        source_value = layout.evaluate(source_response_policy).evaluation.utilities[
            payoff_player
        ]
        row = behavioral_open_axis_payoff_row(
            layout,
            response_probabilities,
            result,
            acting_player=acting_player,
            source_value=source_value,
        )
        endpoint_value = layout.evaluate(endpoint_response_policy).evaluation.utilities[
            payoff_player
        ]
        self.assertLessEqual(abs(row.value(response_probabilities) - source_value), 2e-12)
        self.assertLessEqual(abs(row.value(endpoint) - endpoint_value), 2e-12)
        self.assertEqual(len(row.nodes), 16)

    def test_repeated_actor_topology_fails_before_read_use(self) -> None:
        leaf_fixture.LeafAdjointCFRTests.setUpClass()
        source = leaf_fixture.LeafAdjointCFRTests
        with self.assertRaisesRegex(ValueError, "compiled public path"):
            behavioral_open_axis_payoff_row(
                source.layout,
                source.probabilities,
                SimpleNamespace(traverser=0, reads=()),
                acting_player=0,
                source_value=0.0,
            )

    def test_exact_acting_node_coverage_is_required(self) -> None:
        sparse_fixture.SparseOpenModeCFRTests.setUpClass()
        source = sparse_fixture.SparseOpenModeCFRTests
        layout = ContinuationPublicTreeTensorEvaluator(
            source.layout.game,
            public_prefix=((0, "check"), (1, "bet")),
        )
        probabilities = compile_policy_probability_tape(
            layout,
            source.belief.hands_by_player,
            source.policy,
        )
        with self.assertRaisesRegex(ValueError, "exactly cover"):
            behavioral_open_axis_payoff_row(
                layout,
                probabilities,
                SimpleNamespace(traverser=2, reads=()),
                acting_player=2,
                source_value=0.0,
            )


if __name__ == "__main__":
    unittest.main()
