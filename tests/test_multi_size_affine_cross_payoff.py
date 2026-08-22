from __future__ import annotations

import gc
import importlib.util
import unittest

import numpy as np

from pontius.canonical_affine_resident_automaton_cache import (
    CuPyCanonicalAffineResidentAutomatonCache,
)
from pontius.cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    release_cupy_memory_pool,
)
from pontius.incremental_policy_tt import compile_policy_probability_tape
from pontius.multi_size_affine_cross_payoff import (
    evaluate_multi_size_affine_cross_payoff,
)
from pontius.multi_size_leaf_adjoint import multi_size_leaf_adjoint_cfr_traverser
from pontius.public_node_open_axis import public_node_open_axis_payoff_row
from pontius.resident_heterogeneous_leaf_contraction import (
    CuPyResidentBeliefCache,
)
import tests.test_multi_size_leaf_adjoint as sized_fixture


def _endpoint_policy(layout: object, source: dict, node_index: int) -> dict:
    result = {key: dict(row) for key, row in source.items()}
    node = layout.nodes[node_index]
    for hand_index, key in enumerate(node.information_keys):
        selected = (node_index + hand_index + 1) % len(node.actions)
        result[key] = {
            action: float(action_index == selected)
            for action_index, action in enumerate(node.actions)
        }
    return result


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class MultiSizeAffineCrossPayoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sized_fixture.MultiSizeLeafAdjointTests.setUpClass()
        cls.source = sized_fixture.MultiSizeLeafAdjointTests
        cls.gpu = CuPyBidirectionalIncidence.compile(cls.source.sparse)
        cls.belief_cache = CuPyResidentBeliefCache.compile(cls.source.workspace)
        cls.caches = tuple(
            CuPyCanonicalAffineResidentAutomatonCache.compile(
                cls.source.workspace,
                cls.source.automata[seat],
                target_seat=seat,
            )
            for seat in range(6)
        )

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.caches, cls.belief_cache, cls.gpu
        gc.collect()
        release_cupy_memory_pool()

    def test_cross_payoff_reads_match_raw_and_dense_endpoints(self) -> None:
        acting_player = 0
        payoff_player = 4
        public_node = 0
        raw = multi_size_leaf_adjoint_cfr_traverser(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.probabilities,
            self.source.automata[payoff_player],
            traverser=acting_player,
            maximum_feature_width_per_batch=96,
        )
        resident = evaluate_multi_size_affine_cross_payoff(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.probabilities,
            self.source.automata[payoff_player],
            acting_player=acting_player,
            payoff_player=payoff_player,
            belief_cache=self.belief_cache,
            automaton_cache=self.caches[payoff_player],
            cupy_sparse=self.gpu,
            maximum_feature_width_per_batch=96,
        )
        raw_by_node = {row.node_index: row for row in raw.reads}
        self.assertEqual(set(raw_by_node), {row.node_index for row in resident.reads})
        for row in resident.reads:
            expected = raw_by_node[row.node_index]
            np.testing.assert_allclose(
                row.counterfactual_reaches,
                expected.counterfactual_reaches,
                atol=2e-12,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                row.action_numerators,
                expected.action_numerators,
                atol=2e-12,
                rtol=0.0,
            )

        source_value = self.source.layout.evaluate(
            self.source.policy
        ).evaluation.utilities[payoff_player]
        row = public_node_open_axis_payoff_row(
            self.source.layout,
            self.source.probabilities,
            resident,
            acting_player=acting_player,
            public_node=public_node,
            source_value=source_value,
        )
        endpoint_policy = _endpoint_policy(
            self.source.layout,
            self.source.policy,
            public_node,
        )
        endpoint_probabilities = compile_policy_probability_tape(
            self.source.layout,
            self.source.belief.hands_by_player,
            endpoint_policy,
        )
        endpoint_value = self.source.layout.evaluate(
            endpoint_policy
        ).evaluation.utilities[payoff_player]
        self.assertLessEqual(
            abs(row.value(endpoint_probabilities) - endpoint_value),
            2e-11,
        )

    def test_payoff_role_mismatch_fails_before_contraction(self) -> None:
        with self.assertRaisesRegex(ValueError, "wrong payoff role"):
            evaluate_multi_size_affine_cross_payoff(
                self.source.layout,
                self.source.workspace,
                self.source.sparse,
                self.source.probabilities,
                self.source.automata[4],
                acting_player=0,
                payoff_player=4,
                belief_cache=self.belief_cache,
                automaton_cache=self.caches[3],
                cupy_sparse=self.gpu,
                maximum_feature_width_per_batch=96,
            )


if __name__ == "__main__":
    unittest.main()
