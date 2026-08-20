from __future__ import annotations

import importlib.util
import unittest

import numpy as np

from pontius.game import TERMINAL_PLAYER
from pontius.incremental_policy_tt import compile_policy_probability_tape
from pontius.heterogeneous_leaf_contraction import (
    HeterogeneousLeafTerm,
    contract_heterogeneous_leaf_terms,
)
from pontius.leaf_adjoint_cfr import (
    LeafAdjointPublicTreeCFR,
    _parent_metadata,
    _target_omitted_path_factors,
    build_leaf_adjoint_terminal_automata,
    leaf_adjoint_cfr_traverser,
)
from pontius.open_mode_cfr_bridge import dense_cfr_action_comparisons
from pontius.public_tree_tensor_cfr import PublicTreeTensorCFR
from pontius.public_policy_tt import _terminal_keys_by_slot
from pontius.public_policy_tt import representative_public_tree
from pontius.showdown_value_rank_screen import _rank_codes
from pontius.sparse_incidence_open_mode import contract_sparse_open_mode_showdown_batch
import tests.test_sparse_open_mode_cfr as sparse_fixture


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class LeafAdjointCFRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        source = sparse_fixture.SparseOpenModeCFRTests
        source.setUpClass()
        cls.layout = source.layout
        cls.workspace = source.workspace
        cls.sparse = source.sparse
        cls.policy = source.policy
        codes = tuple(
            np.ascontiguousarray(values, dtype=np.int32)
            for values in _rank_codes(source.board, source.belief.hands_by_player)
        )
        cls.automata = build_leaf_adjoint_terminal_automata(
            cls.layout,
            codes,
            pot=12.0,
            bet_size=3.0,
        )
        cls.probabilities = compile_policy_probability_tape(
            cls.layout,
            source.belief.hands_by_player,
            cls.policy,
        )

    def test_target_omitted_leaf_adjoint_matches_every_dense_action_table(self) -> None:
        maximum_reach = 0.0
        maximum_numerator = 0.0
        maximum_regret = 0.0
        reads = 0
        for traverser in range(6):
            expected = {
                row.node_index: row
                for row in dense_cfr_action_comparisons(
                    self.layout,
                    self.probabilities,
                    traverser=traverser,
                )
            }
            actual = leaf_adjoint_cfr_traverser(
                self.layout,
                self.workspace,
                self.sparse,
                self.probabilities,
                self.automata[traverser],
                traverser=traverser,
                maximum_feature_width_per_batch=96,
            )
            self.assertEqual(actual.terminal_contractions, 193)
            self.assertEqual(len(actual.reads), 32)
            self.assertLessEqual(actual.maximum_child_reach_disagreement, 2e-13)
            for row in actual.reads:
                oracle = expected[row.node_index]
                maximum_reach = max(
                    maximum_reach,
                    float(
                        np.max(
                            np.abs(
                                row.counterfactual_reaches
                                - oracle.counterfactual_reaches
                            )
                        )
                    ),
                )
                maximum_numerator = max(
                    maximum_numerator,
                    float(
                        np.max(
                            np.abs(row.action_numerators - oracle.action_numerators)
                        )
                    ),
                )
                maximum_regret = max(
                    maximum_regret,
                    float(np.max(np.abs(row.regret_deltas - oracle.regret_deltas))),
                )
                reads += 1

        self.assertEqual(reads, 192)
        self.assertLessEqual(maximum_reach, 2e-13)
        self.assertLessEqual(maximum_numerator, 2e-12)
        self.assertLessEqual(maximum_regret, 2e-12)

    def test_terminal_library_and_probability_contract_are_strict(self) -> None:
        with self.assertRaisesRegex(ValueError, "payoff groups"):
            leaf_adjoint_cfr_traverser(
                self.layout,
                self.workspace,
                self.sparse,
                self.probabilities,
                {},
                traverser=0,
            )
        with self.assertRaisesRegex(ValueError, "outside"):
            leaf_adjoint_cfr_traverser(
                self.layout,
                self.workspace,
                self.sparse,
                self.probabilities,
                self.automata[0],
                traverser=6,
            )

    def test_complete_leaf_adjoint_dcfr_step_matches_dense_solver(self) -> None:
        dense = PublicTreeTensorCFR(self.layout, "dcfr")
        leaf = LeafAdjointPublicTreeCFR(
            self.layout,
            self.workspace,
            self.sparse,
            self.automata,
            "dcfr",
            maximum_feature_width_per_batch=96,
        )
        dense.warm_start(self.policy, 2.5)
        leaf.warm_start(self.policy, 2.5)
        dense.step()
        leaf.step()
        dense_regrets = dense.regret_table()
        leaf_regrets = leaf.regret_table()
        self.assertEqual(leaf_regrets.keys(), dense_regrets.keys())
        maximum = max(
            abs(leaf_regrets[key][action] - dense_regrets[key][action])
            for key in dense_regrets
            for action in dense_regrets[key]
        )
        self.assertLessEqual(maximum, 2e-12)
        dense_sums = dense.strategy_sum_table()
        leaf_sums = leaf.strategy_sum_table()
        self.assertEqual(leaf_sums, dense_sums)
        self.assertIsNotNone(leaf.last_step_work)
        assert leaf.last_step_work is not None
        self.assertEqual(
            sum(row.terminal_contractions for row in leaf.last_step_work.traversers),
            6 * 193,
        )
        self.assertGreater(
            leaf.memory_summary()["terminal_automaton_numeric_bytes"],
            0,
        )

    def test_heterogeneous_leaf_batch_matches_independent_terminal_reads(self) -> None:
        parents, parent_actions = _parent_metadata(self.layout)
        terminal_keys = _terminal_keys_by_slot(self.layout)
        terminal_nodes = tuple(
            node_index
            for node_index, node in enumerate(self.layout.nodes)
            if node.player == TERMINAL_PLAYER
        )[:12]
        terms = []
        expected = {}
        for node_index in terminal_nodes:
            node = self.layout.nodes[node_index]
            factors = _target_omitted_path_factors(
                self.layout,
                self.probabilities,
                parents,
                parent_actions,
                terminal_node=node_index,
                traverser=0,
                shape=self.workspace.topology.base.hand_counts,
            )
            automaton = self.automata[0][terminal_keys[node.terminal_slot]]
            terms.append(
                HeterogeneousLeafTerm(
                    key=node_index,
                    automaton=automaton,
                    mode_factors=factors,
                )
            )
            expected[node_index] = contract_sparse_open_mode_showdown_batch(
                self.workspace,
                self.sparse,
                (automaton,),
                target_seats=(0,),
                mode_factors=factors,
                maximum_feature_width_per_batch=96,
            ).for_automaton(0).for_seat(0)

        actual = contract_heterogeneous_leaf_terms(
            self.workspace,
            self.sparse,
            tuple(terms),
            target_seat=0,
            maximum_feature_width_per_batch=96,
        )
        self.assertEqual(actual.work.terms, len(terms))
        self.assertLess(actual.work.batches, 2 * len(terms))
        for key, oracle in expected.items():
            values = actual.for_key(key)
            np.testing.assert_allclose(
                values.root_normalized_reaches,
                oracle.root_normalized_reaches,
                atol=2e-14,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                values.root_normalized_numerators,
                oracle.root_normalized_numerators,
                atol=2e-13,
                rtol=0.0,
            )

    def test_external_axis_topology_matches_dense_deal_layout_step(self) -> None:
        topology = representative_public_tree(
            sparse_fixture.SparseOpenModeCFRTests.belief,
            pot=12.0,
            stack=30.0,
            bet_size=3.0,
        )
        self.assertEqual(
            tuple((node.player, node.actions, node.children) for node in topology.nodes),
            tuple((node.player, node.actions, node.children) for node in self.layout.nodes),
        )
        codes = tuple(
            np.ascontiguousarray(values, dtype=np.int32)
            for values in _rank_codes(
                sparse_fixture.SparseOpenModeCFRTests.board,
                sparse_fixture.SparseOpenModeCFRTests.belief.hands_by_player,
            )
        )
        automata = build_leaf_adjoint_terminal_automata(
            topology,
            codes,
            pot=12.0,
            bet_size=3.0,
        )
        dense = PublicTreeTensorCFR(self.layout, "dcfr")
        axis = LeafAdjointPublicTreeCFR(
            topology,
            self.workspace,
            self.sparse,
            automata,
            "dcfr",
            maximum_feature_width_per_batch=96,
            hands_by_player=(
                sparse_fixture.SparseOpenModeCFRTests.belief.hands_by_player
            ),
        )
        dense.warm_start(self.policy, 1.0)
        axis.warm_start(self.policy, 1.0)
        dense.step()
        axis.step()
        dense_regrets = dense.regret_table()
        axis_regrets = axis.regret_table()
        self.assertEqual(axis_regrets.keys(), dense_regrets.keys())
        maximum = max(
            abs(axis_regrets[key][action] - dense_regrets[key][action])
            for key in dense_regrets
            for action in dense_regrets[key]
        )
        self.assertLessEqual(maximum, 2e-12)


if __name__ == "__main__":
    unittest.main()
