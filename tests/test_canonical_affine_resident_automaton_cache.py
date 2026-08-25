from __future__ import annotations

import gc
import importlib.util
import unittest

import numpy as np

from pontius.affine_resident_heterogeneous_leaf_contraction import (
    _affine_basis_digest,
)
from pontius.canonical_affine_resident_automaton_cache import (
    CuPyCanonicalAffineResidentAutomatonCache,
    canonical_affine_basis_digest,
)
from pontius.cupy_sparse_incidence import CuPyBidirectionalIncidence, _cupy_modules
from pontius.multi_size_affine_resident_leaf_adjoint_cfr import (
    MultiSizeAffineResidentLeafAdjointPublicTreeCFR,
)
from pontius.multi_size_resident_leaf_adjoint_cfr import (
    MultiSizeResidentLeafAdjointPublicTreeCFR,
)
from pontius.open_mode_showdown import _automaton_half_vectors
from pontius.resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
from pontius.structured_showdown_automaton import build_structured_showdown_automaton
import tests.test_multi_size_leaf_adjoint as sized_fixture


def _five_way_tie_scale_family():
    strengths = (
        *(np.asarray([1, 2], dtype=np.int32) for _ in range(5)),
        np.asarray([0, 2], dtype=np.int32),
    )
    common = {
        "strength_codes": strengths,
        "contenders": (0, 1, 2, 3, 4, 5),
        "target_player": 0,
        "pot": 12.0,
    }
    return (
        build_structured_showdown_automaton(
            **common,
            contributed=False,
            bet_size=0.0,
        ),
        build_structured_showdown_automaton(
            **common,
            contributed=True,
            bet_size=3.0,
        ),
        build_structured_showdown_automaton(
            **common,
            contributed=True,
            bet_size=6.0,
        ),
    )


class CanonicalAffineBasisIdentityTests(unittest.TestCase):
    def test_five_way_share_is_scale_canonical(self) -> None:
        family = _five_way_tie_scale_family()
        self.assertEqual(tuple(row.final_pot for row in family), (12.0, 30.0, 48.0))
        self.assertGreater(len({_affine_basis_digest(row) for row in family}), 1)
        self.assertEqual(
            len({canonical_affine_basis_digest(row) for row in family}),
            1,
        )

    def test_changed_final_mode_basis_remains_distinct(self) -> None:
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
        self.assertNotEqual(
            canonical_affine_basis_digest(first),
            canonical_affine_basis_digest(second),
        )


@unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy screen")
class CanonicalAffineResidentCacheTests(unittest.TestCase):
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
        cls.canonical_caches = tuple(
            CuPyCanonicalAffineResidentAutomatonCache.compile(
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
        for name in ("canonical_caches", "raw_caches", "belief_cache", "gpu"):
            if hasattr(cls, name):
                delattr(cls, name)
        gc.collect()
        cp.get_default_memory_pool().free_all_blocks()
        cp.get_default_pinned_memory_pool().free_all_blocks()
        cp.cuda.get_current_stream().synchronize()

    def test_five_way_scale_family_shares_one_device_basis(self) -> None:
        cp, _ = _cupy_modules()
        family = _five_way_tie_scale_family()
        cache = CuPyCanonicalAffineResidentAutomatonCache.compile(
            self.source.workspace,
            {str(index): automaton for index, automaton in enumerate(family)},
            target_seat=0,
        )
        self.assertEqual(cache.unique_automata, 3)
        self.assertEqual(cache.shared_topologies, 1)
        for automaton in family:
            expected_left, expected_right = _automaton_half_vectors(
                automaton,
                self.source.workspace,
            )
            ref = cache.half_vectors[id(automaton)]
            np.testing.assert_allclose(
                cp.asnumpy(ref.left_basis),
                expected_left,
                atol=1e-13,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                cp.asnumpy(ref.right_basis * ref.right_coefficients[None, :]),
                expected_right,
                atol=1e-13,
                rtol=0.0,
            )

    def test_complete_canonical_step_matches_raw(self) -> None:
        self.assertEqual(
            sum(cache.unique_automata for cache in self.canonical_caches),
            762,
        )
        self.assertEqual(
            sum(cache.shared_topologies for cache in self.canonical_caches),
            378,
        )
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
        canonical = MultiSizeAffineResidentLeafAdjointPublicTreeCFR(
            self.source.layout,
            self.source.workspace,
            self.source.sparse,
            self.source.automata,
            "dcfr",
            belief_cache=self.belief_cache,
            automaton_caches=self.canonical_caches,
            cupy_sparse=self.gpu,
            maximum_feature_width_per_batch=96,
            hands_by_player=self.source.belief.hands_by_player,
        )
        raw.warm_start({}, 2.5)
        canonical.warm_start({}, 2.5)
        raw.step()
        canonical.step()
        for left, right in (
            (raw.regret_table(), canonical.regret_table()),
            (raw.strategy_sum_table(), canonical.strategy_sum_table()),
        ):
            maximum = max(
                abs(float(left[key][action]) - float(right[key][action]))
                for key in left
                for action in left[key]
            )
            self.assertLessEqual(maximum, 2e-12)


if __name__ == "__main__":
    unittest.main()
