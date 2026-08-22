from __future__ import annotations

import importlib.util
import unittest

import numpy as np

from pontius.behavioral_one_seat_master import (
    BehavioralOneSeatAxis,
    solve_behavioral_one_seat_master,
)
from pontius.continuation_public_tree_tensor import (
    ContinuationPublicTreeTensorEvaluator,
)
from pontius.sequence_form_open_axis import (
    OpenAxisNodeCoefficients,
    SequenceFormAffineRow,
)
import tests.test_sparse_open_mode_cfr as sparse_fixture


def _row(axis: BehavioralOneSeatAxis, layout: object, first: float, second: float) -> SequenceFormAffineRow:
    nodes = []
    hand_count = len(axis.information_sets) // len(axis.acting_nodes)
    for node_index in axis.acting_nodes:
        actions = len(layout.nodes[node_index].actions)
        self_values = np.zeros((hand_count, actions), dtype=np.float64)
        self_values[:, 0] = first
        self_values[:, 1] = second
        self_values.flags.writeable = False
        nodes.append(OpenAxisNodeCoefficients(node_index, self_values))
    return SequenceFormAffineRow(axis.acting_player, 0.0, tuple(nodes))


@unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy screen")
class BehavioralOneSeatMasterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sparse_fixture.SparseOpenModeCFRTests.setUpClass()
        source = sparse_fixture.SparseOpenModeCFRTests
        cls.source = source
        cls.layout = ContinuationPublicTreeTensorEvaluator(
            source.layout.game,
            public_prefix=((0, "check"), (1, "bet")),
        )
        cls.axis = BehavioralOneSeatAxis.compile(
            cls.layout,
            source.belief.hands_by_player,
            source.policy,
            acting_player=2,
        )

    def test_sparse_master_minimizes_a_known_single_row(self) -> None:
        zero = _row(self.axis, self.layout, 0.0, 0.0)
        first_action_cost = _row(self.axis, self.layout, 1.0, 0.0)
        rows = ((first_action_cost,), *((zero,) for _ in range(5)))
        solved = solve_behavioral_one_seat_master(
            self.axis,
            rows,
            (10.0,) * 6,
            tolerance=1e-10,
        )
        policy, projection_error = self.axis.policy_from_variables(
            solved.variables,
            self.source.policy,
            tolerance=1e-10,
        )
        self.assertLessEqual(solved.lower_bound, 1e-10)
        self.assertLessEqual(projection_error, 1e-10)
        for information_set in self.axis.information_sets:
            self.assertAlmostEqual(policy[information_set.key][information_set.actions[0]], 0.0)
            self.assertAlmostEqual(policy[information_set.key][information_set.actions[1]], 1.0)
        self.assertLessEqual(solved.duality_gap, 1e-9)
        self.assertLessEqual(solved.maximum_stationarity_error, 1e-9)

    def test_second_exact_row_tightens_the_restricted_lower_bound(self) -> None:
        zero = _row(self.axis, self.layout, 0.0, 0.0)
        first = _row(self.axis, self.layout, 1.0, 0.0)
        second = _row(self.axis, self.layout, 0.0, 1.0)
        initial = solve_behavioral_one_seat_master(
            self.axis,
            ((first,), *((zero,) for _ in range(5))),
            (10.0,) * 6,
            tolerance=1e-10,
        )
        tightened = solve_behavioral_one_seat_master(
            self.axis,
            ((first, second), *((zero,) for _ in range(5))),
            (10.0,) * 6,
            tolerance=1e-10,
        )
        hand_count = len(self.source.belief.hands_by_player[2])
        self.assertLessEqual(initial.lower_bound, 1e-10)
        self.assertAlmostEqual(tightened.lower_bound, hand_count / 2.0, places=9)
        self.assertGreater(tightened.lower_bound, initial.lower_bound)
        self.assertEqual(tightened.row_counts_by_player[0], 2)

    def test_cap_infeasibility_fails_closed(self) -> None:
        expensive = _row(self.axis, self.layout, 1.0, 1.0)
        zero = _row(self.axis, self.layout, 0.0, 0.0)
        with self.assertRaisesRegex(ValueError, "did not solve"):
            solve_behavioral_one_seat_master(
                self.axis,
                ((expensive,), *((zero,) for _ in range(5))),
                (0.0,) * 6,
                tolerance=1e-10,
            )

    def test_projection_rejects_more_than_solver_noise(self) -> None:
        with self.assertRaisesRegex(ArithmeticError, "projection exceeds"):
            self.axis.policy_from_variables(
                np.full(self.axis.variable_count, 0.6, dtype=np.float64),
                self.source.policy,
                tolerance=1e-10,
            )


if __name__ == "__main__":
    unittest.main()
