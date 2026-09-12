"""Deterministic clocks exercise boundary selection without relying on wall speed."""
from fractions import Fraction as Q
import unittest
import experiment as e


class FakeEngine:
    def __init__(self):
        self.iteration = 10
        self.sums = [e.c.np.array([[5., 5.]]) for _ in (0, 1)]

    def step(self):
        self.iteration += 1
        for value in self.sums:
            value[0, 0] += 1


class TimingTests(unittest.TestCase):
    def test_before_core_crossing_and_after_total_crossing(self):
        clock = iter([0., .1, 1., 1.1, 2., 2.1]).__next__
        result = e.timed_continue(FakeEngine(), .15, .25, clock=clock, block=1, cap=20)
        self.assertEqual(result['matched']['iteration'], 11)
        self.assertEqual(result['generous']['iteration'], 13)
        self.assertLessEqual(result['matched']['active_seconds'], .15)
        self.assertGreater(result['matched']['crossing_seconds'], .15)
        self.assertGreaterEqual(result['generous']['active_seconds'], .25)
        self.assertEqual(result['matched']['coefficients'], [[5/11], [5/11]])

    def test_zero_extra_updates_if_first_block_crosses_core_budget(self):
        clock = iter([0., .3]).__next__
        result = e.timed_continue(FakeEngine(), .05, .2, clock=clock, block=1, cap=20)
        self.assertEqual(result['matched']['iteration'], 10)
        self.assertEqual(result['matched']['active_seconds'], 0)

    def test_iteration_cap_fails_instead_of_returning_partial_result(self):
        clock = iter([0., .1]).__next__
        with self.assertRaises(ValueError):
            e.timed_continue(FakeEngine(), .2, .3, clock=clock, block=1, cap=11)

    def test_invalid_budget_order_fails(self):
        with self.assertRaises(ValueError):
            e.timed_continue(FakeEngine(), 2., 1.)

    def test_budget_includes_fresh_witness_proposal_setup_and_gate(self):
        row = dict(baseline_lp_seconds=1., proposal_seconds=2., gate_seconds=4.,
            records=dict(repaired=[{}, dict(setup_seconds=3., active_seconds=5.)]))
        self.assertEqual(e.budgets(row), dict(work_seconds=11., total_seconds=15.))


if __name__ == '__main__':
    unittest.main()
