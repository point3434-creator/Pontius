from __future__ import annotations

import importlib.util
import unittest

import numpy as np

from pontius.continuation_public_tree_tensor import (
    ContinuationPublicTreeTensorEvaluator,
)
from pontius.cross_payoff_leaf_adjoint import splice_fixed_response_probability_tape
from pontius.incremental_policy_tt import compile_policy_probability_tape
from pontius.leaf_adjoint_cfr import build_leaf_adjoint_terminal_automata
from pontius.one_seat_convex_generation import (
    require_compiled_behavioral_affine_shortcut,
)
from pontius.public_policy_tt import _information_key
from pontius.sequence_form_open_axis import (
    affine_row_conditioning,
    constant_minus_affine_row,
    extract_sequence_form_open_axis_payoff,
    sequence_form_realization_tape,
    splice_fixed_response_probability_tape_for_axes,
    subtract_affine_rows,
)
from pontius.showdown_value_rank_screen import _rank_codes
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


def _fixed_response_policy(layout: object, source: dict, response_actions: dict) -> dict:
    result = {key: dict(row) for key, row in source.items()}
    schema = layout.information_schema()
    for key, selected in response_actions.items():
        result[key] = {
            action: float(action == selected)
            for action in schema[key]
        }
    return result


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class SequenceFormOpenAxisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        leaf_fixture.LeafAdjointCFRTests.setUpClass()
        source = leaf_fixture.LeafAdjointCFRTests
        cls.layout = source.layout
        cls.workspace = source.workspace
        cls.sparse = source.sparse
        cls.policy = source.policy
        cls.probabilities = source.probabilities
        cls.automata = source.automata
        cls.hands = source.layout.hands_by_player

    def test_full_tree_sequence_rows_match_dense_repeated_actor_payoffs(self) -> None:
        acting_player = 0
        endpoint_policy = _endpoint_policy(self.layout, self.policy, acting_player)
        endpoint = compile_policy_probability_tape(
            self.layout,
            self.hands,
            endpoint_policy,
        )
        source_realization = sequence_form_realization_tape(
            self.layout,
            self.probabilities,
            acting_player=acting_player,
            hands_by_player=self.hands,
        )
        endpoint_realization = sequence_form_realization_tape(
            self.layout,
            endpoint,
            acting_player=acting_player,
            hands_by_player=self.hands,
        )
        source_utilities = self.layout.evaluate(self.policy).evaluation.utilities
        endpoint_utilities = self.layout.evaluate(endpoint_policy).evaluation.utilities
        rows = []
        for payoff_player in range(self.layout.num_players):
            result = extract_sequence_form_open_axis_payoff(
                self.layout,
                self.workspace,
                self.sparse,
                self.probabilities,
                self.automata[payoff_player],
                acting_player=acting_player,
                payoff_player=payoff_player,
                hands_by_player=self.hands,
                maximum_feature_width_per_batch=96,
            )
            rows.append(result.row)
            self.assertLessEqual(
                abs(result.row.value(source_realization) - source_utilities[payoff_player]),
                2e-12,
            )
            self.assertLessEqual(
                abs(
                    result.row.value(endpoint_realization)
                    - endpoint_utilities[payoff_player]
                ),
                2e-12,
            )
        conditioning = affine_row_conditioning(tuple(rows), tolerance=1e-12)
        self.assertEqual(conditioning.rows, self.layout.num_players)
        self.assertGreater(conditioning.numerical_rank, 0)

        with self.assertRaisesRegex(ValueError, "compiled public path"):
            require_compiled_behavioral_affine_shortcut(self.layout)

    def test_fixed_response_row_matches_dense_source_and_endpoint(self) -> None:
        acting_player = 0
        payoff_player = 1
        source_evaluation = self.layout.evaluate(self.policy)
        endpoint_policy = _endpoint_policy(self.layout, self.policy, acting_player)
        endpoint = compile_policy_probability_tape(
            self.layout,
            self.hands,
            endpoint_policy,
        )
        response_actions = source_evaluation.best_response_actions[payoff_player]
        source_response_policy = _fixed_response_policy(
            self.layout,
            self.policy,
            response_actions,
        )
        endpoint_response_policy = _fixed_response_policy(
            self.layout,
            endpoint_policy,
            response_actions,
        )
        source_response = splice_fixed_response_probability_tape_for_axes(
            self.layout,
            self.probabilities,
            response_actions,
            responding_player=payoff_player,
            hands_by_player=self.hands,
        )
        endpoint_response = splice_fixed_response_probability_tape_for_axes(
            self.layout,
            endpoint,
            response_actions,
            responding_player=payoff_player,
            hands_by_player=self.hands,
        )
        result = extract_sequence_form_open_axis_payoff(
            self.layout,
            self.workspace,
            self.sparse,
            source_response,
            self.automata[payoff_player],
            acting_player=acting_player,
            payoff_player=payoff_player,
            hands_by_player=self.hands,
            maximum_feature_width_per_batch=96,
        )
        source_realization = sequence_form_realization_tape(
            self.layout,
            source_response,
            acting_player=acting_player,
            hands_by_player=self.hands,
        )
        endpoint_realization = sequence_form_realization_tape(
            self.layout,
            endpoint_response,
            acting_player=acting_player,
            hands_by_player=self.hands,
        )
        source_value = self.layout.evaluate(
            source_response_policy
        ).evaluation.utilities[payoff_player]
        endpoint_value = self.layout.evaluate(
            endpoint_response_policy
        ).evaluation.utilities[payoff_player]
        self.assertLessEqual(abs(result.row.value(source_realization) - source_value), 2e-12)
        self.assertLessEqual(
            abs(result.row.value(endpoint_realization) - endpoint_value),
            2e-12,
        )

        profile = extract_sequence_form_open_axis_payoff(
            self.layout,
            self.workspace,
            self.sparse,
            self.probabilities,
            self.automata[payoff_player],
            acting_player=acting_player,
            payoff_player=payoff_player,
            hands_by_player=self.hands,
            maximum_feature_width_per_batch=96,
        )
        gain = subtract_affine_rows(result.row, profile.row)
        self.assertAlmostEqual(
            gain.value(source_realization),
            source_value
            - self.layout.evaluate(self.policy).evaluation.utilities[payoff_player],
        )
        own_profile = extract_sequence_form_open_axis_payoff(
            self.layout,
            self.workspace,
            self.sparse,
            self.probabilities,
            self.automata[acting_player],
            acting_player=acting_player,
            payoff_player=acting_player,
            hands_by_player=self.hands,
            maximum_feature_width_per_batch=96,
        )
        own_gain = constant_minus_affine_row(
            source_evaluation.evaluation.best_response_values[acting_player],
            own_profile.row,
        )
        self.assertAlmostEqual(
            own_gain.value(source_realization),
            source_evaluation.evaluation.deviation_gains[acting_player],
        )

    def test_post_bet_sequence_row_is_behavioral_shortcut_safe(self) -> None:
        sparse_fixture.SparseOpenModeCFRTests.setUpClass()
        source = sparse_fixture.SparseOpenModeCFRTests
        continuation = ContinuationPublicTreeTensorEvaluator(
            source.layout.game,
            public_prefix=((0, "check"), (1, "bet")),
        )
        require_compiled_behavioral_affine_shortcut(continuation)
        hands = source.belief.hands_by_player
        probabilities = compile_policy_probability_tape(
            continuation,
            hands,
            source.policy,
        )
        endpoint_policy = _endpoint_policy(continuation, source.policy, 2)
        endpoint = compile_policy_probability_tape(
            continuation,
            hands,
            endpoint_policy,
        )
        codes = tuple(
            np.ascontiguousarray(values, dtype=np.int32)
            for values in _rank_codes(source.board, hands)
        )
        automata = build_leaf_adjoint_terminal_automata(
            continuation,
            codes,
            pot=12.0,
            bet_size=3.0,
        )
        result = extract_sequence_form_open_axis_payoff(
            continuation,
            source.workspace,
            source.sparse,
            probabilities,
            automata[3],
            acting_player=2,
            payoff_player=3,
            hands_by_player=hands,
            maximum_feature_width_per_batch=96,
        )
        source_realization = sequence_form_realization_tape(
            continuation,
            probabilities,
            acting_player=2,
            hands_by_player=hands,
        )
        endpoint_realization = sequence_form_realization_tape(
            continuation,
            endpoint,
            acting_player=2,
            hands_by_player=hands,
        )
        self.assertLessEqual(
            abs(
                result.row.value(source_realization)
                - continuation.evaluate(source.policy).evaluation.utilities[3]
            ),
            2e-12,
        )
        self.assertLessEqual(
            abs(
                result.row.value(endpoint_realization)
                - continuation.evaluate(endpoint_policy).evaluation.utilities[3]
            ),
            2e-12,
        )

    def test_external_axis_order_mutation_defeats_embedded_key_splice(self) -> None:
        axes = tuple(tuple(reversed(axis)) for axis in self.hands)
        probabilities = compile_policy_probability_tape(
            self.layout,
            axes,
            self.policy,
        )
        responding_player = 1
        response_actions = {}
        for node in self.layout.nodes:
            if node.player != responding_player:
                continue
            for hand_index, hand in enumerate(axes[responding_player]):
                key = _information_key(
                    self.layout,
                    responding_player,
                    hand,
                    node.history,
                )
                response_actions[key] = node.actions[hand_index % len(node.actions)]
        corrected = splice_fixed_response_probability_tape_for_axes(
            self.layout,
            probabilities,
            response_actions,
            responding_player=responding_player,
            hands_by_player=axes,
        )
        embedded = splice_fixed_response_probability_tape(
            self.layout,
            probabilities,
            response_actions,
            responding_player=responding_player,
        )
        differences = 0
        for node_index, node in enumerate(self.layout.nodes):
            if node.player != responding_player:
                continue
            actual = corrected[node_index]
            assert actual is not None
            for hand_index, hand in enumerate(axes[responding_player]):
                key = _information_key(
                    self.layout,
                    responding_player,
                    hand,
                    node.history,
                )
                selected = node.actions.index(response_actions[key])
                self.assertEqual(actual[hand_index, selected], 1.0)
            old = embedded[node_index]
            assert old is not None
            differences += int(np.count_nonzero(actual != old))
        self.assertGreater(differences, 0)


if __name__ == "__main__":
    unittest.main()
