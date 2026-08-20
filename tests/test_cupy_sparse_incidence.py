from __future__ import annotations

import importlib.util
import unittest

import numpy as np

from pontius.cupy_sparse_incidence import CuPyBidirectionalIncidence
from pontius.heterogeneous_leaf_contraction import (
    HeterogeneousLeafTerm,
    contract_heterogeneous_leaf_terms,
)
from pontius.leaf_adjoint_cfr import (
    _parent_metadata,
    _target_omitted_path_factors,
)
from pontius.leaf_adjoint_evaluation import evaluate_leaf_adjoint_seat
from pontius.public_policy_tt import _terminal_keys_by_slot
from pontius.resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
    contract_resident_heterogeneous_leaf_terms,
)
from pontius.resident_leaf_adjoint_evaluation import (
    evaluate_resident_leaf_adjoint_seat,
)
import tests.test_leaf_adjoint_cfr as leaf_fixture


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class CuPySparseIncidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        leaf_fixture.LeafAdjointCFRTests.setUpClass()
        cls.source = leaf_fixture.LeafAdjointCFRTests
        cls.gpu = CuPyBidirectionalIncidence.compile(cls.source.sparse)

    def test_gpu_sparse_chain_matches_cpu_with_transfer_charged(self) -> None:
        operator = self.source.sparse.right_to_left
        gpu = self.gpu.right_to_left
        rng = np.random.default_rng(20260820)
        features = np.ascontiguousarray(
            rng.normal(size=(operator.source_records, 9)),
            dtype=np.float64,
        )
        expected = operator.query(operator.accumulate(features))
        actual, work = gpu.transform(features)
        np.testing.assert_allclose(actual, expected, atol=2e-12, rtol=0.0)
        self.assertGreater(work.host_to_device_ms, 0.0)
        self.assertGreater(work.kernel_ms, 0.0)
        self.assertGreater(work.device_to_host_ms, 0.0)
        self.assertGreater(work.pool_total_bytes, 0)

    def test_gpu_heterogeneous_leaf_batch_matches_cpu_final_vectors(self) -> None:
        layout = self.source.layout
        parents, parent_actions = _parent_metadata(layout)
        terminal_keys = _terminal_keys_by_slot(layout)
        terms = []
        for node_index, node in enumerate(layout.nodes):
            if node.terminal_slot < 0:
                continue
            terms.append(
                HeterogeneousLeafTerm(
                    key=node_index,
                    automaton=self.source.automata[0][
                        terminal_keys[node.terminal_slot]
                    ],
                    mode_factors=_target_omitted_path_factors(
                        layout,
                        self.source.probabilities,
                        parents,
                        parent_actions,
                        terminal_node=node_index,
                        traverser=0,
                        shape=self.source.workspace.topology.base.hand_counts,
                    ),
                )
            )
            if len(terms) == 12:
                break
        cpu = contract_heterogeneous_leaf_terms(
            self.source.workspace,
            self.source.sparse,
            tuple(terms),
            target_seat=0,
            maximum_feature_width_per_batch=96,
        )
        gpu = contract_heterogeneous_leaf_terms(
            self.source.workspace,
            self.source.sparse,
            tuple(terms),
            target_seat=0,
            maximum_feature_width_per_batch=96,
            cupy_sparse=self.gpu,
        )
        self.assertEqual(gpu.work.operator_backend, "gpu_cupy")
        self.assertGreater(gpu.work.gpu_kernel_ms, 0.0)
        for key, expected in cpu.values:
            actual = gpu.for_key(key)
            np.testing.assert_allclose(
                actual.root_normalized_reaches,
                expected.root_normalized_reaches,
                atol=2e-13,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                actual.root_normalized_numerators,
                expected.root_normalized_numerators,
                atol=2e-12,
                rtol=0.0,
            )

    def test_resident_gpu_batch_matches_transferred_gpu_vectors(self) -> None:
        layout = self.source.layout
        parents, parent_actions = _parent_metadata(layout)
        terminal_keys = _terminal_keys_by_slot(layout)
        terms = []
        for node_index, node in enumerate(layout.nodes):
            if node.terminal_slot < 0:
                continue
            terms.append(
                HeterogeneousLeafTerm(
                    key=node_index,
                    automaton=self.source.automata[0][
                        terminal_keys[node.terminal_slot]
                    ],
                    mode_factors=_target_omitted_path_factors(
                        layout,
                        self.source.probabilities,
                        parents,
                        parent_actions,
                        terminal_node=node_index,
                        traverser=0,
                        shape=self.source.workspace.topology.base.hand_counts,
                    ),
                )
            )
            if len(terms) == 12:
                break
        expected = contract_heterogeneous_leaf_terms(
            self.source.workspace,
            self.source.sparse,
            tuple(terms),
            target_seat=0,
            maximum_feature_width_per_batch=96,
            cupy_sparse=self.gpu,
        )
        belief_cache = CuPyResidentBeliefCache.compile(self.source.workspace)
        automaton_cache = CuPyResidentAutomatonCache.compile(
            self.source.workspace,
            self.source.automata[0],
            target_seat=0,
        )
        actual = contract_resident_heterogeneous_leaf_terms(
            self.source.workspace,
            self.source.sparse,
            tuple(terms),
            target_seat=0,
            belief_cache=belief_cache,
            automaton_cache=automaton_cache,
            cupy_sparse=self.gpu,
            maximum_feature_width_per_batch=96,
        )
        self.assertEqual(actual.work.operator_backend, "gpu_cupy_resident")
        self.assertGreater(actual.work.resident_pipeline_gpu_ms, 0.0)
        self.assertLess(
            actual.work.per_call_host_to_device_bytes,
            actual.work.legacy_equivalent_host_to_device_bytes,
        )
        self.assertLess(
            actual.work.per_call_device_to_host_bytes,
            actual.work.legacy_equivalent_device_to_host_bytes,
        )
        for key, expected_values in expected.values:
            actual_values = actual.for_key(key)
            np.testing.assert_allclose(
                actual_values.root_normalized_reaches,
                expected_values.root_normalized_reaches,
                atol=2e-13,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                actual_values.root_normalized_numerators,
                expected_values.root_normalized_numerators,
                atol=2e-12,
                rtol=0.0,
            )

    def test_resident_leaf_adjoint_seat_matches_transferred_gpu(self) -> None:
        belief_cache = CuPyResidentBeliefCache.compile(self.source.workspace)
        automaton_cache = CuPyResidentAutomatonCache.compile(
            self.source.workspace,
            self.source.automata[0],
            target_seat=0,
        )
        expected = evaluate_leaf_adjoint_seat(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.probabilities,
            self.source.automata[0],
            target_player=0,
            maximum_feature_width_per_batch=96,
            cupy_sparse=self.gpu,
        )
        actual = evaluate_resident_leaf_adjoint_seat(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.probabilities,
            self.source.automata[0],
            target_player=0,
            belief_cache=belief_cache,
            automaton_cache=automaton_cache,
            cupy_sparse=self.gpu,
            maximum_feature_width_per_batch=96,
        )
        self.assertAlmostEqual(actual.profile_utility, expected.profile_utility, 11)
        self.assertAlmostEqual(
            actual.best_response_value,
            expected.best_response_value,
            11,
        )
        self.assertAlmostEqual(actual.deviation_gain, expected.deviation_gain, 11)
        self.assertEqual(actual.best_response_actions, expected.best_response_actions)


if __name__ == "__main__":
    unittest.main()
