from __future__ import annotations

import importlib.util
import unittest

import numpy as np

import tests.test_leaf_adjoint_cfr as leaf_fixture
from pontius.cross_payoff_adjoint_result import (
    evaluate_typed_cross_payoff_leaf_adjoint,
)
from pontius.cross_payoff_leaf_adjoint import (
    project_public_node_direction_slope,
    splice_fixed_response_probability_tape,
)
from pontius.incremental_leaf_adjoint_response import (
    compile_leaf_adjoint_response_caches,
)
from pontius.incremental_policy_tt import compile_policy_probability_tape
from pontius.leaf_adjoint_evaluation import evaluate_leaf_adjoint_seat
from pontius.selector_stable_affine_response import (
    evaluate_selector_stable_affine_leaf_adjoint_seat,
)


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class CrossPayoffLeafAdjointTests(unittest.TestCase):
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
        cls.acting_player = 0
        cls.changed_node = next(
            node_index
            for node_index, node in enumerate(cls.layout.nodes)
            if node.player == cls.acting_player and len(node.actions) > 1
        )
        node = cls.layout.nodes[cls.changed_node]
        endpoint_policy = {key: dict(row) for key, row in cls.policy.items()}
        for hand_index, key in enumerate(node.information_keys):
            endpoint_policy[key] = {
                action: float(action_index == (hand_index + 1) % len(node.actions))
                for action_index, action in enumerate(node.actions)
            }
        cls.endpoint_probabilities = compile_policy_probability_tape(
            cls.layout,
            cls.layout.hands_by_player,
            endpoint_policy,
        )

    def test_cross_payoff_profile_slope_is_exact_for_large_one_node_edit(self) -> None:
        payoff_player = 1
        adjoint = evaluate_typed_cross_payoff_leaf_adjoint(
            self.layout,
            self.workspace,
            self.sparse,
            self.probabilities,
            self.automata[payoff_player],
            acting_player=self.acting_player,
            payoff_player=payoff_player,
            maximum_feature_width_per_batch=96,
        )
        self.assertEqual(adjoint.acting_player, self.acting_player)
        self.assertEqual(adjoint.payoff_player, payoff_player)
        predicted = project_public_node_direction_slope(
            adjoint,
            self.layout,
            self.probabilities,
            self.endpoint_probabilities,
            acting_player=self.acting_player,
            changed_public_node=self.changed_node,
        )
        source = evaluate_leaf_adjoint_seat(
            self.layout,
            self.workspace,
            self.sparse,
            self.probabilities,
            self.automata[payoff_player],
            target_player=payoff_player,
            maximum_feature_width_per_batch=96,
        )
        endpoint = evaluate_leaf_adjoint_seat(
            self.layout,
            self.workspace,
            self.sparse,
            self.endpoint_probabilities,
            self.automata[payoff_player],
            target_player=payoff_player,
            maximum_feature_width_per_batch=96,
        )
        self.assertLessEqual(
            abs(predicted - (endpoint.profile_utility - source.profile_utility)),
            2e-12,
        )

    def test_profile_and_fixed_response_slopes_match_affine_teacher(self) -> None:
        caches = compile_leaf_adjoint_response_caches(
            self.layout,
            self.workspace,
            self.sparse,
            self.policy,
            self.automata,
            hands_by_player=self.layout.hands_by_player,
            maximum_feature_width_per_batch=96,
        )
        maximum_profile_error = 0.0
        maximum_response_error = 0.0
        maximum_gain_error = 0.0
        for payoff_player, cache in enumerate(caches):
            teacher = evaluate_selector_stable_affine_leaf_adjoint_seat(
                cache,
                self.endpoint_probabilities,
                acting_player=self.acting_player,
                maximum_feature_width_per_batch=96,
            )
            profile = evaluate_typed_cross_payoff_leaf_adjoint(
                self.layout,
                self.workspace,
                self.sparse,
                self.probabilities,
                self.automata[payoff_player],
                acting_player=self.acting_player,
                payoff_player=payoff_player,
                maximum_feature_width_per_batch=96,
            )
            profile_slope = project_public_node_direction_slope(
                profile,
                self.layout,
                self.probabilities,
                self.endpoint_probabilities,
                acting_player=self.acting_player,
                changed_public_node=self.changed_node,
            )
            if payoff_player == self.acting_player:
                response_slope = 0.0
            else:
                response_tape = splice_fixed_response_probability_tape(
                    self.layout,
                    self.probabilities,
                    cache.source_evaluation.best_response_actions,
                    responding_player=payoff_player,
                )
                response = evaluate_typed_cross_payoff_leaf_adjoint(
                    self.layout,
                    self.workspace,
                    self.sparse,
                    response_tape,
                    self.automata[payoff_player],
                    acting_player=self.acting_player,
                    payoff_player=payoff_player,
                    maximum_feature_width_per_batch=96,
                )
                response_slope = project_public_node_direction_slope(
                    response,
                    self.layout,
                    self.probabilities,
                    self.endpoint_probabilities,
                    acting_player=self.acting_player,
                    changed_public_node=self.changed_node,
                )
            gain_slope = response_slope - profile_slope
            maximum_profile_error = max(
                maximum_profile_error,
                abs(profile_slope - teacher.profile_utility_slope),
            )
            maximum_response_error = max(
                maximum_response_error,
                abs(response_slope - teacher.best_response_value_slope),
            )
            maximum_gain_error = max(
                maximum_gain_error,
                abs(gain_slope - teacher.deviation_gap_slope),
            )
        self.assertLessEqual(maximum_profile_error, 2e-12)
        self.assertLessEqual(maximum_response_error, 2e-12)
        self.assertLessEqual(maximum_gain_error, 2e-12)

    def test_role_and_one_node_scope_guards_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "another payoff"):
            evaluate_typed_cross_payoff_leaf_adjoint(
                self.layout,
                self.workspace,
                self.sparse,
                self.probabilities,
                self.automata[1],
                acting_player=0,
                payoff_player=2,
            )
        adjoint = evaluate_typed_cross_payoff_leaf_adjoint(
            self.layout,
            self.workspace,
            self.sparse,
            self.probabilities,
            self.automata[1],
            acting_player=self.acting_player,
            payoff_player=1,
            maximum_feature_width_per_batch=96,
        )
        contaminated = list(self.endpoint_probabilities)
        second = next(
            node_index
            for node_index, node in enumerate(self.layout.nodes)
            if node.player == 1 and node_index != self.changed_node
        )
        contaminated[second] = np.roll(contaminated[second], 1, axis=1)
        with self.assertRaisesRegex(ValueError, "exactly the declared"):
            project_public_node_direction_slope(
                adjoint,
                self.layout,
                self.probabilities,
                tuple(contaminated),
                acting_player=self.acting_player,
                changed_public_node=self.changed_node,
            )


if __name__ == "__main__":
    unittest.main()
