import math
import unittest

from pontius.h32_continuation_depth_ledger import (
    depth_hard_ledger_ms,
    recover_discounted_step_regret_deltas,
)
from pontius.updates import update_rule


class ContinuationDepthLedgerTests(unittest.TestCase):
    def test_latest_dcfr_delta_is_recovered_through_sign_discount(self) -> None:
        rule = update_rule("dcfr")
        before = {"info": {"check": 2.0, "bet": -1.0, "fold": 0.5}}
        instantaneous = {"info": {"check": 3.0, "bet": -4.0, "fold": -0.5}}
        updated = {
            action: before["info"][action] + instantaneous["info"][action]
            for action in before["info"]
        }
        after = {
            "info": {
                action: rule.discount_regret(value, 2)
                for action, value in updated.items()
            }
        }
        recovered = recover_discounted_step_regret_deltas(
            before, after, rule=rule, iteration=2
        )
        for action, expected in instantaneous["info"].items():
            self.assertAlmostEqual(recovered["info"][action], expected, places=14)

    def test_regret_recovery_fails_closed_on_schema_and_values(self) -> None:
        rule = update_rule("dcfr")
        with self.assertRaises(ValueError):
            recover_discounted_step_regret_deltas(
                {"a": {"check": 0.0}},
                {"b": {"check": 0.0}},
                rule=rule,
                iteration=1,
            )
        with self.assertRaises(ValueError):
            recover_discounted_step_regret_deltas(
                {"a": {"check": 0.0}},
                {"a": {"check": math.nan}},
                rule=rule,
                iteration=1,
            )
        with self.assertRaises(ValueError):
            recover_discounted_step_regret_deltas(
                {"a": {"check": 0.0}},
                {"a": {"check": 0.0}},
                rule=rule,
                iteration=0,
            )

    def test_hard_ledger_charges_every_step_candidate_and_reserve(self) -> None:
        self.assertEqual(
            depth_hard_ledger_ms(
                step_ms=(1000.0, 1100.0),
                candidate_ms=(100.0, 200.0, 300.0),
                certificate_reserve_ms=1250.0,
                emission_reserve_ms=1000.0,
            ),
            4950.0,
        )
        with self.assertRaises(ValueError):
            depth_hard_ledger_ms(
                step_ms=(),
                candidate_ms=(1.0,),
                certificate_reserve_ms=1.0,
                emission_reserve_ms=1.0,
            )


if __name__ == "__main__":
    unittest.main()
