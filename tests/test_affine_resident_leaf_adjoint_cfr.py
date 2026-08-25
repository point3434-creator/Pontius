from __future__ import annotations

import gc
import importlib.util
import unittest

import numpy as np

from pontius.affine_resident_heterogeneous_leaf_contraction import (
    CuPyAffineResidentAutomatonCache,
    _affine_basis_digest,
)
from pontius.cupy_sparse_incidence import CuPyBidirectionalIncidence, _cupy_modules
from pontius.multi_size_affine_resident_leaf_adjoint_cfr import (
    MultiSizeAffineResidentLeafAdjointPublicTreeCFR,
    multi_size_affine_resident_leaf_adjoint_cfr_traverser,
)
from pontius.multi_size_resident_leaf_adjoint_cfr import (
    MultiSizeResidentLeafAdjointPublicTreeCFR,
    multi_size_resident_leaf_adjoint_cfr_traverser,
)
from pontius.open_mode_showdown import _automaton_half_vectors
from pontius.resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
from pontius.structured_showdown_automaton import build_structured_showdown_automaton
import tests.test_multi_size_leaf_adjoint as sized_fixture


def _final_mode_basis_pair():
    shared = tuple(np.asarray([0, 1], dtype=np.int32) for _ in range(5))
    first = build_structured_showdown_automaton(
        strength_codes=(*shared, np.asarray([0, 1], dtype=np.int32)),
        contenders=(0, 1, 2, 3, 4, 5),
        target_player=0,
        contributed=True,
        pot=12.0,
        bet_size=3.0,
    )
    second = build_structured_showdown_automaton(
        strength_codes=(*shared, np.asarray([1, 0], dtype=np.int32)),
        contenders=(0, 1, 2, 3, 4, 5),
        target_player=0,
        contributed=True,
        pot=12.0,
        bet_size=6.0,
    )
    return first, second


class AffineBasisIdentityTests(unittest.TestCase):
    def test_affine_digest_binds_final_mode_winner_basis(self) -> None:
        first, second = _final_mode_basis_pair()
        for left, right in zip(first.transitions, second.transitions, strict=True):
            np.testing.assert_array_equal(left, right)
        for left, right in zip(first.bond_states, second.bond_states, strict=True):
            np.testing.assert_array_equal(left, right)
        self.assertFalse(
            np.array_equal(
                first.terminal_winner_values / first.final_pot,
                second.terminal_winner_values / second.final_pot,
            )
        )
        self.assertNotEqual(_affine_basis_digest(first), _affine_basis_digest(second))


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class AffineResidentLeafAdjointCFRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sized_fixture.MultiSizeLeafAdjointTests.setUpClass()
        cls.source = sized_fixture.MultiSizeLeafAdjointTests
        cls.gpu = CuPyBidirectionalIncidence.compile(cls.source.sparse)
        cls.belief_cache = CuPyResidentBeliefCache.compile(cls.source.workspace)
        cls.raw_caches = tuple(
            CuPyResidentAutomatonCache.compile(
                cls.source.workspace,
                cls.source.automata[seat],
                target_seat=seat,
            )
            for seat in range(6)
        )
        cls.affine_caches = tuple(
            CuPyAffineResidentAutomatonCache.compile(
                cls.source.workspace,
                cls.source.automata[seat],
                target_seat=seat,
            )
            for seat in range(6)
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cp, _ = _cupy_modules()
        cp.cuda.get_current_stream().synchronize()
        for name in ("affine_caches", "raw_caches", "belief_cache", "gpu"):
            if hasattr(cls, name):
                delattr(cls, name)
        gc.collect()
        cp.get_default_memory_pool().free_all_blocks()
        cp.get_default_pinned_memory_pool().free_all_blocks()
        cp.cuda.get_current_stream().synchronize()

    def test_affine_cache_reconstructs_every_raw_half_vector(self) -> None:
        cp, _ = _cupy_modules()
        maximum = 0.0
        for seat, cache in enumerate(self.affine_caches):
            self.assertEqual(cache.unique_automata, 127)
            self.assertEqual(cache.shared_topologies, 63)
            for automaton in self.source.automata[seat].values():
                expected_left, expected_right = _automaton_half_vectors(
                    automaton, self.source.workspace
                )
                ref = cache.half_vectors[id(automaton)]
                actual_left = cp.asnumpy(ref.left_basis)
                actual_right = cp.asnumpy(
                    ref.right_basis * ref.right_coefficients[None, :]
                )
                maximum = max(
                    maximum,
                    float(np.max(np.abs(actual_left - expected_left))),
                    float(np.max(np.abs(actual_right - expected_right))),
                )
        self.assertLessEqual(maximum, 1e-13)
        raw_bytes = sum(cache.numeric_bytes for cache in self.raw_caches)
        affine_bytes = sum(cache.numeric_bytes for cache in self.affine_caches)
        self.assertLess(affine_bytes / raw_bytes, 0.60)

    def test_affine_cache_does_not_group_different_final_mode_bases(self) -> None:
        first, second = _final_mode_basis_pair()
        cache = CuPyAffineResidentAutomatonCache.compile(
            self.source.workspace,
            {"first": first, "second": second},
            target_seat=0,
        )
        self.assertEqual(cache.unique_automata, 2)
        self.assertEqual(cache.shared_topologies, 2)

    def test_affine_traverser_matches_raw_resident_in_both_directions(self) -> None:
        for seat in (0, 3):
            expected = multi_size_resident_leaf_adjoint_cfr_traverser(
                self.source.layout,
                self.source.workspace,
                self.source.sparse,
                self.source.probabilities,
                self.source.automata[seat],
                traverser=seat,
                belief_cache=self.belief_cache,
                automaton_cache=self.raw_caches[seat],
                cupy_sparse=self.gpu,
                maximum_feature_width_per_batch=96,
            )
            actual = multi_size_affine_resident_leaf_adjoint_cfr_traverser(
                self.source.layout,
                self.source.workspace,
                self.source.sparse,
                self.source.probabilities,
                self.source.automata[seat],
                traverser=seat,
                belief_cache=self.belief_cache,
                automaton_cache=self.affine_caches[seat],
                cupy_sparse=self.gpu,
                maximum_feature_width_per_batch=96,
            )
            self.assertEqual(actual.terminal_contractions, 385)
            for shared, raw in zip(actual.reads, expected.reads, strict=True):
                self.assertEqual(shared.node_index, raw.node_index)
                np.testing.assert_allclose(
                    shared.counterfactual_reaches,
                    raw.counterfactual_reaches,
                    atol=2e-13,
                    rtol=0.0,
                )
                np.testing.assert_allclose(
                    shared.action_numerators,
                    raw.action_numerators,
                    atol=2e-12,
                    rtol=0.0,
                )
                np.testing.assert_allclose(
                    shared.regret_deltas,
                    raw.regret_deltas,
                    atol=2e-12,
                    rtol=0.0,
                )
            self.assertEqual(
                actual.resident_work.operator_backend,
                "gpu_cupy_affine_resident",
            )

    def test_complete_affine_dcfr_step_matches_raw_resident(self) -> None:
        raw = MultiSizeResidentLeafAdjointPublicTreeCFR(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.automata,
            "dcfr",
            belief_cache=self.belief_cache,
            automaton_caches=self.raw_caches,
            cupy_sparse=self.gpu,
            maximum_feature_width_per_batch=96,
            hands_by_player=self.source.belief.hands_by_player,
        )
        affine = MultiSizeAffineResidentLeafAdjointPublicTreeCFR(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.automata,
            "dcfr",
            belief_cache=self.belief_cache,
            automaton_caches=self.affine_caches,
            cupy_sparse=self.gpu,
            maximum_feature_width_per_batch=96,
            hands_by_player=self.source.belief.hands_by_player,
        )
        raw.warm_start(self.source.policy, 2.5)
        affine.warm_start(self.source.policy, 2.5)
        raw.step()
        affine.step()

        raw_regrets = raw.regret_table()
        affine_regrets = affine.regret_table()
        maximum_regret_error = max(
            abs(affine_regrets[key][action] - raw_regrets[key][action])
            for key in raw_regrets
            for action in raw_regrets[key]
        )
        self.assertLessEqual(maximum_regret_error, 2e-12)
        raw_sums = raw.strategy_sum_table()
        affine_sums = affine.strategy_sum_table()
        maximum_sum_error = max(
            abs(affine_sums[key][action] - raw_sums[key][action])
            for key in raw_sums
            for action in raw_sums[key]
        )
        self.assertLessEqual(maximum_sum_error, 2e-12)

    def test_affine_cache_rejects_wrong_target(self) -> None:
        with self.assertRaisesRegex(ValueError, "target seat"):
            CuPyAffineResidentAutomatonCache.compile(
                self.source.workspace,
                self.source.automata[0],
                target_seat=1,
            )


if __name__ == "__main__":
    unittest.main()
