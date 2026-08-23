from __future__ import annotations

import unittest

import tests.test_multi_size_leaf_adjoint as sized_fixture
from pontius.cross_payoff_adjoint_result import (
    evaluate_typed_multi_size_cross_payoff_leaf_adjoint,
)
from pontius.incremental_policy_tt import compile_policy_probability_tape
from pontius.public_node_behavioral_axis import (
    compile_public_node_behavioral_axis,
)
from pontius.public_node_open_axis import (
    PublicNodeAffineSourceContext,
    build_public_node_affine_source_context,
    public_node_open_axis_payoff_row,
)


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
        result = evaluate_typed_multi_size_cross_payoff_leaf_adjoint(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.probabilities,
            self.source.automata[payoff_player],
            acting_player=acting_player,
            payoff_player=payoff_player,
            maximum_feature_width_per_batch=96,
        )
        self.assertEqual(result.acting_player, acting_player)
        self.assertEqual(result.payoff_player, payoff_player)
        context = build_public_node_affine_source_context(
            self.source.layout,
            self.source.probabilities,
            result,
            acting_player=acting_player,
            payoff_player=payoff_player,
            public_node=public_node,
        )
        row = public_node_open_axis_payoff_row(context)
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
        result = evaluate_typed_multi_size_cross_payoff_leaf_adjoint(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.probabilities,
            self.source.automata[payoff_player],
            acting_player=acting_player,
            payoff_player=payoff_player,
            maximum_feature_width_per_batch=96,
        )
        context = build_public_node_affine_source_context(
            self.source.layout,
            self.source.probabilities,
            result,
            acting_player=acting_player,
            payoff_player=payoff_player,
            public_node=public_node,
        )
        row = public_node_open_axis_payoff_row(context)
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

    def test_nonroot_public_node_fails_closed_before_row_extraction(self) -> None:
        acting_player = 0
        payoff_player = 4
        nonroot = next(
            index
            for index, node in enumerate(self.source.layout.nodes)
            if index != 0 and node.player == acting_player
        )
        result = evaluate_typed_multi_size_cross_payoff_leaf_adjoint(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.probabilities,
            self.source.automata[payoff_player],
            acting_player=acting_player,
            payoff_player=payoff_player,
            maximum_feature_width_per_batch=96,
        )
        with self.assertRaisesRegex(ValueError, "only root public node 0"):
            build_public_node_affine_source_context(
                self.source.layout,
                self.source.probabilities,
                result,
                acting_player=acting_player,
                payoff_player=payoff_player,
                public_node=nonroot,
            )

    def test_crossed_payoff_result_and_source_role_fails_closed(self) -> None:
        acting_player = 0
        result_payoff_player = 4
        source_payoff_player = 3
        result = evaluate_typed_multi_size_cross_payoff_leaf_adjoint(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.probabilities,
            self.source.automata[result_payoff_player],
            acting_player=acting_player,
            payoff_player=result_payoff_player,
            maximum_feature_width_per_batch=96,
        )
        with self.assertRaisesRegex(ValueError, "payoff roles are crossed"):
            build_public_node_affine_source_context(
                self.source.layout,
                self.source.probabilities,
                result,
                acting_player=acting_player,
                payoff_player=source_payoff_player,
                public_node=0,
            )

    def test_untyped_raw_traverser_result_is_rejected(self) -> None:
        acting_player = 0
        payoff_player = 4
        result = evaluate_typed_multi_size_cross_payoff_leaf_adjoint(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.probabilities,
            self.source.automata[payoff_player],
            acting_player=acting_player,
            payoff_player=payoff_player,
            maximum_feature_width_per_batch=96,
        )
        with self.assertRaisesRegex(TypeError, "typed cross-payoff result"):
            build_public_node_affine_source_context(
                self.source.layout,
                self.source.probabilities,
                result.raw_result,  # type: ignore[arg-type]
                acting_player=acting_player,
                payoff_player=payoff_player,
                public_node=0,
            )

    def test_context_constructor_and_caller_source_scalar_are_not_available(self) -> None:
        with self.assertRaisesRegex(TypeError, "factory-only"):
            PublicNodeAffineSourceContext(  # type: ignore[call-arg]
                layout=self.source.layout,
                probabilities=self.source.probabilities,
                acting_player=0,
                payoff_player=4,
                public_node=0,
                source_value=0.0,
                action_coefficients=self.source.probabilities[0],
                identity=object(),
            )


if __name__ == "__main__":
    unittest.main()
