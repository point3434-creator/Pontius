from __future__ import annotations

import unittest

from pontius.incremental_policy_tt import compile_policy_probability_tape
from pontius.multi_size_leaf_adjoint import multi_size_leaf_adjoint_cfr_traverser
from pontius.public_node_behavioral_axis import (
    compile_public_node_behavioral_axis,
)
from pontius.public_node_open_axis import public_node_open_axis_payoff_row
import tests.test_multi_size_leaf_adjoint as sized_fixture


def _changed_node_policy(layout: object, source: dict, node_index: int) -> dict:
    result = {key: dict(row) for key, row in source.items()}
    node = layout.nodes[node_index]
    for hand_index, key in enumerate(node.information_keys):
        selected = (node_index + hand_index + 1) % len(node.actions)
        result[key] = {
            action: float(action_index == selected)
            for action_index, action in enumerate(node.actions)
        }
    return result


class PublicNodeOpenAxisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sized_fixture.MultiSizeLeafAdjointTests.setUpClass()
        cls.source = sized_fixture.MultiSizeLeafAdjointTests

    def test_single_current_node_row_is_exact_on_repeated_actor_topology(self) -> None:
        acting_player = 0
        payoff_player = 4
        public_node = 0
        result = multi_size_leaf_adjoint_cfr_traverser(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.probabilities,
            self.source.automata[payoff_player],
            traverser=acting_player,
            maximum_feature_width_per_batch=96,
        )
        source_value = self.source.layout.evaluate(
            self.source.policy
        ).evaluation.utilities[payoff_player]
        row = public_node_open_axis_payoff_row(
            self.source.layout,
            self.source.probabilities,
            result,
            acting_player=acting_player,
            public_node=public_node,
            source_value=source_value,
        )
        endpoint = _changed_node_policy(
            self.source.layout,
            self.source.policy,
            public_node,
        )
        endpoint_probabilities = compile_policy_probability_tape(
            self.source.layout,
            self.source.belief.hands_by_player,
            endpoint,
        )
        endpoint_value = self.source.layout.evaluate(
            endpoint
        ).evaluation.utilities[payoff_player]
        self.assertLessEqual(
            abs(row.value(endpoint_probabilities) - endpoint_value),
            2e-11,
        )
        self.assertEqual([item.node_index for item in row.nodes], [public_node])

    def test_axis_opens_only_current_node_and_widens_to_three_actions(self) -> None:
        axis = compile_public_node_behavioral_axis(
            self.source.layout,
            self.source.belief.hands_by_player,
            self.source.policy,
            public_node=0,
        )
        self.assertEqual(axis.acting_player, 0)
        self.assertEqual(axis.acting_nodes, (0,))
        self.assertEqual(len(axis.information_sets), 2)
        self.assertEqual(axis.variable_count, 6)
        self.assertTrue(all(len(row.actions) == 3 for row in axis.information_sets))

    def test_off_node_contamination_is_not_silently_described_by_local_row(self) -> None:
        acting_player = 0
        payoff_player = 4
        public_node = 0
        result = multi_size_leaf_adjoint_cfr_traverser(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.probabilities,
            self.source.automata[payoff_player],
            traverser=acting_player,
            maximum_feature_width_per_batch=96,
        )
        source_value = self.source.layout.evaluate(
            self.source.policy
        ).evaluation.utilities[payoff_player]
        row = public_node_open_axis_payoff_row(
            self.source.layout,
            self.source.probabilities,
            result,
            acting_player=acting_player,
            public_node=public_node,
            source_value=source_value,
        )
        off_node = next(
            index
            for index, node in enumerate(self.source.layout.nodes)
            if index != public_node and node.player == acting_player
        )
        contaminated = _changed_node_policy(
            self.source.layout,
            self.source.policy,
            off_node,
        )
        contaminated_probabilities = compile_policy_probability_tape(
            self.source.layout,
            self.source.belief.hands_by_player,
            contaminated,
        )
        exact = self.source.layout.evaluate(
            contaminated
        ).evaluation.utilities[payoff_player]
        self.assertGreater(abs(row.value(contaminated_probabilities) - exact), 1e-8)


if __name__ == "__main__":
    unittest.main()
