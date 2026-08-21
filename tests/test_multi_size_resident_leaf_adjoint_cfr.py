from __future__ import annotations

import importlib.util
import unittest

import numpy as np

from pontius.axis_public_cfr import AxisPublicCFRState
from pontius.cupy_sparse_incidence import CuPyBidirectionalIncidence
from pontius.multi_size_leaf_adjoint import multi_size_leaf_adjoint_cfr_traverser
from pontius.multi_size_resident_leaf_adjoint_cfr import (
    MultiSizeResidentLeafAdjointPublicTreeCFR,
    multi_size_resident_leaf_adjoint_cfr_traverser,
)
from pontius.resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
import tests.test_multi_size_leaf_adjoint as sized_fixture


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class MultiSizeResidentLeafAdjointCFRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sized_fixture.MultiSizeLeafAdjointTests.setUpClass()
        cls.source = sized_fixture.MultiSizeLeafAdjointTests
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

    def test_resident_sized_traverser_matches_both_directions(self) -> None:
        for seat in (0, 3):
            expected = multi_size_leaf_adjoint_cfr_traverser(
                self.source.layout,
                self.source.workspace,
                self.source.sparse,
                self.source.probabilities,
                self.source.automata[seat],
                traverser=seat,
                maximum_feature_width_per_batch=96,
                cupy_sparse=self.gpu,
            )
            actual = multi_size_resident_leaf_adjoint_cfr_traverser(
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
            self.assertEqual(actual.terminal_contractions, 385)
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

    def test_complete_sized_resident_dcfr_step_matches_transferred(self) -> None:
        reference = AxisPublicCFRState(
            self.source.layout,
            self.source.belief.hands_by_player,
            "dcfr",
        )
        resident = MultiSizeResidentLeafAdjointPublicTreeCFR(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.automata,
            "dcfr",
            belief_cache=self.belief_cache,
            automaton_caches=self.automaton_caches,
            cupy_sparse=self.gpu,
            maximum_feature_width_per_batch=96,
            hands_by_player=self.source.belief.hands_by_player,
        )
        reference.warm_start(self.source.policy, 2.5)
        resident.warm_start(self.source.policy, 2.5)

        reference.iteration += 1
        for traverser in range(6):
            probabilities = reference.immutable_strategies()
            reference.accumulate_average_for_traverser(traverser, probabilities)
            result = multi_size_leaf_adjoint_cfr_traverser(
                self.source.layout,
                self.source.workspace,
                self.source.sparse,
                probabilities,
                self.source.automata[traverser],
                traverser=traverser,
                maximum_feature_width_per_batch=96,
                cupy_sparse=self.gpu,
            )
            reference.apply_regret_deltas(
                tuple((row.node_index, row.regret_deltas) for row in result.reads)
            )
        reference._discount_accumulators()
        resident.step()

        reference_regrets = reference.regret_table()
        resident_regrets = resident.regret_table()
        maximum_regret_error = max(
            abs(resident_regrets[key][action] - reference_regrets[key][action])
            for key in reference_regrets
            for action in reference_regrets[key]
        )
        self.assertLessEqual(maximum_regret_error, 2e-12)

        reference_sums = reference.strategy_sum_table()
        resident_sums = resident.strategy_sum_table()
        maximum_sum_error = max(
            abs(resident_sums[key][action] - reference_sums[key][action])
            for key in reference_sums
            for action in reference_sums[key]
        )
        self.assertLessEqual(maximum_sum_error, 2e-12)
        self.assertIsNotNone(resident.last_step_work)
        assert resident.last_step_work is not None
        self.assertEqual(len(resident.last_step_work.traversers), 6)

    def test_sized_cache_identity_contract_is_strict(self) -> None:
        with self.assertRaisesRegex(ValueError, "one automaton cache"):
            MultiSizeResidentLeafAdjointPublicTreeCFR(
                self.source.layout,
                self.source.workspace,
                self.source.sparse,
                self.source.automata,
                "dcfr",
                belief_cache=self.belief_cache,
                automaton_caches=self.automaton_caches[:-1],
                cupy_sparse=self.gpu,
                maximum_feature_width_per_batch=96,
                hands_by_player=self.source.belief.hands_by_player,
            )


if __name__ == "__main__":
    unittest.main()
