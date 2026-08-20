from __future__ import annotations

import importlib.util
import unittest

import numpy as np

from pontius.open_mode_showdown import contract_open_mode_showdown_batch
from pontius.sparse_incidence_open_mode import (
    SparseBidirectionalIncidence,
    contract_sparse_open_mode_showdown_batch,
)
from pontius.structured_showdown_automaton import build_structured_showdown_automaton
from tests.test_open_mode_factor_tt import _belief, _compile


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class SparseIncidenceOpenModeTests(unittest.TestCase):
    def test_sparse_backend_matches_frozen_numpy_for_weighted_automata(self) -> None:
        belief = _belief(components=3)
        _, _, workspace = _compile(belief)
        sparse = SparseBidirectionalIncidence.compile(workspace)
        codes = tuple(
            np.asarray((0, 1, 2), dtype=np.int32) for _ in belief.hand_counts
        )
        automata = (
            build_structured_showdown_automaton(
                strength_codes=codes,
                contenders=(0, 1, 2, 3),
                target_player=0,
                contributed=True,
                pot=12.0,
                bet_size=3.0,
            ),
            build_structured_showdown_automaton(
                strength_codes=codes,
                contenders=(0, 1),
                target_player=3,
                contributed=False,
                pot=12.0,
                bet_size=3.0,
            ),
        )
        factors = (
            np.asarray((0.2, 1.0, 0.4)),
            np.asarray((1.0, 0.3, 0.7)),
            np.asarray((0.9, 0.4, 0.8)),
            np.asarray((0.5, 1.0, 0.6)),
        )
        expected = contract_open_mode_showdown_batch(
            workspace,
            automata,
            target_seats=(0, 1, 2, 3),
            mode_factors=factors,
            maximum_feature_width_per_batch=6,
        )
        actual = contract_sparse_open_mode_showdown_batch(
            workspace,
            sparse,
            automata,
            target_seats=(0, 1, 2, 3),
            mode_factors=factors,
            maximum_feature_width_per_batch=6,
        )

        self.assertGreater(sparse.numeric_bytes, 0)
        self.assertEqual(actual.middle_ranks, expected.middle_ranks)
        for automaton in range(2):
            for target in range(4):
                first = actual.for_automaton(automaton).for_seat(target)
                second = expected.for_automaton(automaton).for_seat(target)
                np.testing.assert_allclose(
                    first.root_normalized_numerators,
                    second.root_normalized_numerators,
                    atol=5e-13,
                    rtol=0.0,
                )
                np.testing.assert_allclose(
                    first.root_normalized_reaches,
                    second.root_normalized_reaches,
                    atol=5e-14,
                    rtol=0.0,
                )
                np.testing.assert_allclose(
                    first.conditional_values,
                    second.conditional_values,
                    atol=5e-13,
                    rtol=0.0,
                )

    def test_sparse_operator_shape_and_workspace_identity_are_strict(self) -> None:
        belief = _belief(components=1)
        _, _, workspace = _compile(belief)
        sparse = SparseBidirectionalIncidence.compile(workspace)
        with self.assertRaisesRegex(ValueError, "source records"):
            sparse.right_to_left.accumulate(np.ones((1, 1)))
        with self.assertRaisesRegex(ValueError, "incidence entries"):
            sparse.right_to_left.query(np.ones((1, 1)))
        _, _, other = _compile(belief)
        automaton = build_structured_showdown_automaton(
            strength_codes=tuple(
                np.asarray((0, 1, 2), dtype=np.int32)
                for _ in belief.hand_counts
            ),
            contenders=(0, 1, 2, 3),
            target_player=0,
            contributed=False,
            pot=12.0,
            bet_size=3.0,
        )
        with self.assertRaisesRegex(ValueError, "another topology"):
            contract_sparse_open_mode_showdown_batch(
                other,
                sparse,
                (automaton,),
            )


if __name__ == "__main__":
    unittest.main()
