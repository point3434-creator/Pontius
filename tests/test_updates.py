from __future__ import annotations

import unittest

from pontius.updates import update_rule


class CFRUpdateRuleTests(unittest.TestCase):
    def test_cfr_plus_clips_regret_and_uses_quadratic_average(self) -> None:
        rule = update_rule("cfr_plus")
        self.assertEqual(rule.add_regret(1.0, -3.0), 0.0)
        self.assertAlmostEqual(rule.discount_strategy(1.0, 2), (2.0 / 3.0) ** 2)

    def test_lcfr_matches_linear_discount_factors(self) -> None:
        rule = update_rule("lcfr")
        self.assertAlmostEqual(rule.discount_regret(3.0, 2), 2.0)
        self.assertAlmostEqual(rule.discount_regret(-3.0, 2), -2.0)
        self.assertAlmostEqual(rule.discount_strategy(3.0, 2), 2.0)

    def test_default_dcfr_uses_published_parameters(self) -> None:
        rule = update_rule("dcfr")
        positive_factor = 2.0**1.5 / (2.0**1.5 + 1.0)
        self.assertAlmostEqual(rule.discount_regret(1.0, 2), positive_factor)
        self.assertAlmostEqual(rule.discount_regret(-1.0, 2), -0.5)
        self.assertAlmostEqual(rule.discount_strategy(1.0, 2), (2.0 / 3.0) ** 2)

    def test_unknown_rule_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            update_rule("unknown")


if __name__ == "__main__":
    unittest.main()

