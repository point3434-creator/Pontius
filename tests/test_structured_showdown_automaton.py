from __future__ import annotations

from itertools import product
from unittest.mock import patch
import unittest

import numpy as np

from pontius.structured_showdown_automaton import (
    build_structured_showdown_automaton,
)


def _literal(
    strengths: tuple[np.ndarray, ...],
    assignment: tuple[int, ...],
    contenders: tuple[int, ...],
    target: int,
    contributed: bool,
    pot: float,
    bet: float,
) -> float:
    players = len(strengths)
    selected = tuple(int(strengths[p][assignment[p]]) for p in range(players))
    maximum = max(selected[p] for p in contenders)
    winners = tuple(p for p in contenders if selected[p] == maximum)
    contribution = bet if contributed and target in contenders else 0.0
    value = -pot / players - contribution
    if target in winners:
        final_pot = pot + (bet * len(contenders) if contributed else 0.0)
        value += final_pot / len(winners)
    return value


class StructuredShowdownAutomatonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.strengths = (
            np.asarray([0, 3, 1], dtype=np.int32),
            np.asarray([2, 3, 0], dtype=np.int32),
            np.asarray([1, 2, 3], dtype=np.int32),
        )
        self.shape = (3, 3, 3)

    def test_sparse_automaton_and_direct_tt_match_literal_payoffs(self) -> None:
        contenders = (0, 1, 2)
        for target in range(3):
            automaton = build_structured_showdown_automaton(
                strength_codes=self.strengths,
                contenders=contenders,
                target_player=target,
                contributed=True,
                pot=12.0,
                bet_size=3.0,
            )
            assignments = np.asarray(tuple(product(range(3), repeat=3)), dtype=np.int32)
            expected = np.asarray(
                [
                    _literal(
                        self.strengths,
                        tuple(int(value) for value in assignment),
                        contenders,
                        target,
                        True,
                        12.0,
                        3.0,
                    )
                    for assignment in assignments
                ]
            )
            np.testing.assert_allclose(
                automaton.evaluate_assignments(assignments),
                expected,
                atol=0.0,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                automaton.to_dense(),
                expected.reshape(self.shape),
                atol=0.0,
                rtol=0.0,
            )
            np.testing.assert_allclose(
                automaton.to_tensor_train().to_dense(),
                expected.reshape(self.shape),
                atol=1e-14,
                rtol=0.0,
            )
            self.assertEqual(automaton.transition_mismatches(self.strengths), 0)
            self.assertLessEqual(automaton.maximum_construction_array_ndim, 2)
            self.assertLess(
                automaton.maximum_construction_array_elements,
                np.prod(self.shape),
            )

    def test_all_targets_are_zero_sum_and_outside_target_is_rank_one(self) -> None:
        contenders = (0, 2)
        automata = tuple(
            build_structured_showdown_automaton(
                strength_codes=self.strengths,
                contenders=contenders,
                target_player=target,
                contributed=True,
                pot=12.0,
                bet_size=3.0,
            )
            for target in range(3)
        )
        assignments = np.asarray(tuple(product(range(3), repeat=3)), dtype=np.int32)
        utilities = np.stack(
            [automaton.evaluate_assignments(assignments) for automaton in automata]
        )
        np.testing.assert_allclose(np.sum(utilities, axis=0), 0.0, atol=1e-14)
        self.assertTrue(automata[1].constant_winner_shortcut)
        self.assertEqual(automata[1].state_ranks, (1, 1, 1, 1))
        self.assertEqual(automata[1].to_tensor_train().ranks, (1, 1, 1, 1))

    def test_build_is_deterministic_and_strength_sort_cannot_add_runs(self) -> None:
        kwargs = {
            "contenders": (0, 1, 2),
            "target_player": 0,
            "contributed": False,
            "pot": 12.0,
            "bet_size": 3.0,
        }
        first = build_structured_showdown_automaton(
            strength_codes=self.strengths,
            **kwargs,
        )
        second = build_structured_showdown_automaton(
            strength_codes=self.strengths,
            **kwargs,
        )
        sorted_strengths = tuple(np.sort(values) for values in self.strengths)
        ordered = build_structured_showdown_automaton(
            strength_codes=sorted_strengths,
            **kwargs,
        )
        self.assertEqual(first.digest, second.digest)
        self.assertLessEqual(ordered.transition_run_count, first.transition_run_count)
        self.assertEqual(ordered.state_ranks, first.state_ranks)
        self.assertEqual(ordered.numeric_bytes, first.numeric_bytes)

    def test_builder_and_direct_export_do_not_call_svd(self) -> None:
        with patch("numpy.linalg.svd", side_effect=AssertionError("SVD called")):
            automaton = build_structured_showdown_automaton(
                strength_codes=self.strengths,
                contenders=(0, 1, 2),
                target_player=1,
                contributed=False,
                pot=12.0,
                bet_size=3.0,
            )
            automaton.to_tensor_train()

    def test_invalid_strengths_contenders_and_assignments_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "strength"):
            build_structured_showdown_automaton(
                strength_codes=(np.asarray([-1]), np.asarray([0])),
                contenders=(0,),
                target_player=0,
                contributed=False,
                pot=12.0,
                bet_size=3.0,
            )
        with self.assertRaisesRegex(ValueError, "contenders"):
            build_structured_showdown_automaton(
                strength_codes=self.strengths,
                contenders=(2, 0),
                target_player=0,
                contributed=False,
                pot=12.0,
                bet_size=3.0,
            )
        automaton = build_structured_showdown_automaton(
            strength_codes=self.strengths,
            contenders=(0, 1, 2),
            target_player=0,
            contributed=False,
            pot=12.0,
            bet_size=3.0,
        )
        with self.assertRaisesRegex(ValueError, "outside"):
            automaton.evaluate_assignments(np.asarray([[0, 0, 3]]))


if __name__ == "__main__":
    unittest.main()
