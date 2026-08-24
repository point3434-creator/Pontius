from __future__ import annotations

import unittest

from pontius.legal_river_continuation import LegalHeadsUpRiverContinuation
from pontius.one_seat_row_growth_audit import audit_one_seat_row_growth
from pontius.responder_raise_semantics_keystone import _checked_to_river
from pontius.river import RiverDeal, make_hole, parse_cards


class OneSeatRowGrowthAuditTests(unittest.TestCase):
    def game(self) -> LegalHeadsUpRiverContinuation:
        parsed = {
            "button": 0,
            "starting_stack": 6,
            "small_blind": 1,
            "big_blind": 2,
        }
        return LegalHeadsUpRiverContinuation(
            board=parse_cards("2c", "7d", "9h", "Js", "Qc"),
            base_state=_checked_to_river(parsed),
            deals=((RiverDeal(make_hole("As", "Ad"), make_hole("Kh", "Kd")), 1.0),),
        )

    def test_observes_the_production_h1_generation_without_a_shadow_solver(self) -> None:
        audit = audit_one_seat_row_growth(
            self.game(),
            {},
            acting_player=0,
            guard=0.25,
            max_iterations=128,
            tolerance=1e-10,
        )

        self.assertTrue(audit.result.converged)
        self.assertEqual(len(audit.result.iterations), 2)
        self.assertEqual(audit.result.response_rows_by_player, (1, 2))
        self.assertEqual(len(audit.evaluations), 3)
        self.assertEqual(len(audit.masters), 2)
        self.assertEqual(len(audit.response_rows), 3)
        self.assertEqual(
            [(row.phase, row.after_iteration, row.target_player) for row in audit.response_rows],
            [
                ("initial", None, 0),
                ("initial", None, 1),
                ("generated", 1, 1),
            ],
        )
        self.assertEqual(audit.best_response_calls, 7)
        self.assertEqual(audit.expected_utilities_calls, 6)
        self.assertEqual(audit.open_axis_coefficient_calls, 4)

    def test_response_signature_identity_is_exact_tuple_deduplication(self) -> None:
        audit = audit_one_seat_row_growth(
            self.game(),
            {},
            acting_player=0,
            guard=0.25,
            max_iterations=128,
            tolerance=1e-10,
        )

        seen: set[tuple[int, object]] = set()
        for row in audit.response_rows:
            key = (row.target_player, row.signature)
            self.assertNotIn(key, seen)
            seen.add(key)
            self.assertIsInstance(row.signature, tuple)
            self.assertTrue(all(isinstance(item, tuple) for item in row.signature))

    def test_invalid_call_restores_the_production_boundaries(self) -> None:
        with self.assertRaises(ValueError):
            audit_one_seat_row_growth(
                self.game(),
                {},
                acting_player=0,
                guard=-1.0,
            )
        audit = audit_one_seat_row_growth(
            self.game(),
            {},
            acting_player=0,
            guard=0.25,
            max_iterations=128,
            tolerance=1e-10,
        )
        self.assertTrue(audit.result.converged)


if __name__ == "__main__":
    unittest.main()
