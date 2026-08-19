from __future__ import annotations

import unittest

from pontius.cfr import TabularCFR
from pontius.evaluation import evaluate_profile
from pontius.kuhn import KuhnPoker


class CFRTests(unittest.TestCase):
    def test_vanilla_cfr_approaches_kuhn_value(self) -> None:
        game = KuhnPoker()
        solver = TabularCFR(game, "cfr")
        solver.run(10_000)
        evaluation = evaluate_profile(game, solver.average_strategy())
        self.assertAlmostEqual(evaluation.utilities[0], -1.0 / 18.0, delta=0.01)
        self.assertLess(evaluation.nash_conv, 0.04)
        self.assertEqual(len(solver.information_sets), 12)

    def test_linear_cfr_approaches_kuhn_value(self) -> None:
        game = KuhnPoker()
        solver = TabularCFR(game, "lcfr")
        solver.run(10_000)
        evaluation = evaluate_profile(game, solver.average_strategy())
        self.assertAlmostEqual(evaluation.utilities[0], -1.0 / 18.0, delta=0.01)
        self.assertLess(evaluation.nash_conv, 0.04)

    def test_unknown_variant_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TabularCFR(KuhnPoker(), "not-cfr")  # type: ignore[arg-type]

    def test_three_player_cfr_produces_a_zero_sum_profile(self) -> None:
        game = KuhnPoker(3)
        solver = TabularCFR(game, "lcfr")
        solver.run(100)
        evaluation = evaluate_profile(game, solver.average_strategy())
        self.assertAlmostEqual(sum(evaluation.utilities), 0.0)
        self.assertGreater(len(solver.information_sets), 12)
        self.assertGreaterEqual(evaluation.nash_conv, 0.0)


if __name__ == "__main__":
    unittest.main()
