from __future__ import annotations

import importlib.util
import unittest

import numpy as np

from pontius.cupy_sparse_incidence import CuPyBidirectionalIncidence
from pontius.leaf_adjoint_cfr import (
    LeafAdjointPublicTreeCFR,
    leaf_adjoint_cfr_traverser,
)
from pontius.resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
from pontius.resident_leaf_adjoint_cfr import (
    ResidentLeafAdjointPublicTreeCFR,
    resident_leaf_adjoint_cfr_traverser,
)
import tests.test_leaf_adjoint_cfr as leaf_fixture


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class ResidentLeafAdjointCFRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        leaf_fixture.LeafAdjointCFRTests.setUpClass()
        cls.source = leaf_fixture.LeafAdjointCFRTests
        cls.gpu = CuPyBidirectionalIncidence.compile(cls.source.sparse)
        cls.belief_cache = CuPyResidentBeliefCache.compile(cls.source.workspace)
        cls.automaton_caches = tuple(
            CuPyResidentAutomatonCache.compile(
                cls.source.workspace,
                cls.source.automata[seat],
                target_seat=seat,
            )
            for seat in range(6)
        )

    def test_resident_traverser_matches_both_transferred_directions(self) -> None:
        for seat in (0, 3):
            expected = leaf_adjoint_cfr_traverser(
                self.source.layout,
                self.source.workspace,
                self.source.sparse,
                self.source.probabilities,
                self.source.automata[seat],
                traverser=seat,
                maximum_feature_width_per_batch=96,
                terminal_batch_mode="heterogeneous",
                cupy_sparse=self.gpu,
            )
            actual = resident_leaf_adjoint_cfr_traverser(
                self.source.layout,
                self.source.workspace,
                self.source.sparse,
                self.source.probabilities,
                self.source.automata[seat],
                traverser=seat,
                belief_cache=self.belief_cache,
                automaton_cache=self.automaton_caches[seat],
                cupy_sparse=self.gpu,
                maximum_feature_width_per_batch=96,
            )
            self.assertEqual(actual.terminal_contractions, 193)
            self.assertEqual(len(actual.reads), len(expected.reads))
            for resident, transferred in zip(actual.reads, expected.reads, strict=True):
                self.assertEqual(resident.node_index, transferred.node_index)
                np.testing.assert_allclose(
                    resident.counterfactual_reaches,
                    transferred.counterfactual_reaches,
                    atol=2e-13,
                    rtol=0.0,
                )
                np.testing.assert_allclose(
                    resident.action_numerators,
                    transferred.action_numerators,
                    atol=2e-12,
                    rtol=0.0,
                )
                np.testing.assert_allclose(
                    resident.regret_deltas,
                    transferred.regret_deltas,
                    atol=2e-12,
                    rtol=0.0,
                )

    def test_complete_resident_dcfr_step_matches_transferred_solver(self) -> None:
        transferred = LeafAdjointPublicTreeCFR(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.automata,
            "dcfr",
            maximum_feature_width_per_batch=96,
            terminal_batch_mode="heterogeneous",
            cupy_sparse=self.gpu,
        )
        resident = ResidentLeafAdjointPublicTreeCFR(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.automata,
            "dcfr",
            belief_cache=self.belief_cache,
            automaton_caches=self.automaton_caches,
            cupy_sparse=self.gpu,
            maximum_feature_width_per_batch=96,
        )
        transferred.warm_start(self.source.policy, 2.5)
        resident.warm_start(self.source.policy, 2.5)
        transferred.step()
        resident.step()

        transferred_regrets = transferred.regret_table()
        resident_regrets = resident.regret_table()
        self.assertEqual(resident_regrets.keys(), transferred_regrets.keys())
        maximum_regret_error = max(
            abs(
                resident_regrets[key][action]
                - transferred_regrets[key][action]
            )
            for key in transferred_regrets
            for action in transferred_regrets[key]
        )
        self.assertLessEqual(maximum_regret_error, 2e-12)

        transferred_sums = transferred.strategy_sum_table()
        resident_sums = resident.strategy_sum_table()
        maximum_sum_error = max(
            abs(resident_sums[key][action] - transferred_sums[key][action])
            for key in transferred_sums
            for action in transferred_sums[key]
        )
        self.assertLessEqual(maximum_sum_error, 2e-12)
        self.assertIsNotNone(resident.last_step_work)
        assert resident.last_step_work is not None
        self.assertEqual(len(resident.last_step_work.traversers), 6)
        self.assertTrue(
            all(
                row.resident_work.operator_backend == "gpu_cupy_resident"
                for row in resident.last_step_work.traversers
            )
        )
        self.assertGreater(
            resident.memory_summary()["resident_automaton_numeric_bytes"],
            0,
        )

    def test_cache_identity_contract_is_strict(self) -> None:
        with self.assertRaisesRegex(ValueError, "one automaton cache"):
            ResidentLeafAdjointPublicTreeCFR(
                self.source.layout,
                self.source.workspace,
                self.source.sparse,
                self.source.automata,
                "dcfr",
                belief_cache=self.belief_cache,
                automaton_caches=self.automaton_caches[:-1],
                cupy_sparse=self.gpu,
                maximum_feature_width_per_batch=96,
            )


if __name__ == "__main__":
    unittest.main()
