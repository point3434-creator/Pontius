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
from pontius.public_policy_tt import _terminal_keys_by_slot
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


if __name__ == "__main__":
    unittest.main()
