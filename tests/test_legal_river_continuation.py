from __future__ import annotations

from dataclasses import replace
import unittest

from pontius.legal_river_continuation import (
    LegalHeadsUpRiverContinuation,
    LegalHeadsUpRiverState,
)
from pontius.no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    BettingActionKind,
    BettingStreet,
    NoLimitBettingState,
    raise_to,
)
from pontius.one_seat_convex_generation import (
    path_single_visit_report,
    require_behavioral_affine_shortcut,
)
from pontius.river import RiverDeal, make_hole, parse_cards


def _checked_to_river() -> NoLimitBettingState:
    state = NoLimitBettingState.new_hand(
        button=0,
        starting_stacks=(6,) * 6,
        small_blind=1,
        big_blind=2,
    )
    for expected_seat, action in (
        (3, FOLD),
        (4, FOLD),
        (5, FOLD),
        (0, FOLD),
        (1, CALL),
        (2, CHECK),
    ):
        if state.acting_seat != expected_seat:
            raise AssertionError("reference preflop order drifted")
        state = state.apply_action(action)
    for street in (BettingStreet.FLOP, BettingStreet.TURN, BettingStreet.RIVER):
        state = state.advance_street()
        if state.street is not street:
            raise AssertionError("reference street order drifted")
        if street is not BettingStreet.RIVER:
            state = state.apply_action(CHECK).apply_action(CHECK)
    if state.acting_seat != 1:
        raise AssertionError("reference river order drifted")
    state = state.apply_action(CHECK)
    if state.acting_seat != 2:
        raise AssertionError("checked-to root actor drifted")
    return state


def _game(
    *,
    deals: tuple[tuple[RiverDeal, float], ...] | None = None,
) -> LegalHeadsUpRiverContinuation:
    if deals is None:
        deals = (
            (
                RiverDeal(
                    make_hole("As", "Ad"),
                    make_hole("Kh", "Kd"),
                ),
                1.0,
            ),
        )
    return LegalHeadsUpRiverContinuation(
        board=parse_cards("2c", "7d", "9h", "Js", "Qc"),
        base_state=_checked_to_river(),
        deals=deals,
    )


def _dealt(game: LegalHeadsUpRiverContinuation, deal: RiverDeal | None = None):
    selected = game.deals[0][0] if deal is None else deal
    return game.initial_state().apply_action(selected)


class LegalRiverContinuationTests(unittest.TestCase):
    def test_reference_root_uses_every_kernel_legal_integer_bet(self) -> None:
        game = _game()
        dealt = _dealt(game)

        self.assertEqual(game.table_seats, (2, 1))
        self.assertEqual(dealt.legal_actions(), (CHECK, raise_to(2), raise_to(3), raise_to(4)))
        self.assertEqual(game.base_state.pot, 4)
        self.assertEqual(tuple(game.base_state.stacks[seat] for seat in game.table_seats), (4, 4))

    def test_short_all_in_and_full_raise_have_distinct_final_response_records(self) -> None:
        dealt = _dealt(_game())

        facing_three = dealt.apply_action(raise_to(3))
        self.assertEqual(facing_three.legal_actions(), (FOLD, CALL, raise_to(4)))
        short_all_in = facing_three.apply_action(raise_to(4))
        self.assertFalse(short_all_in.betting.history[-1].full_raise)
        self.assertEqual(short_all_in.legal_actions(), (FOLD, CALL))

        facing_two = dealt.apply_action(raise_to(2))
        self.assertEqual(facing_two.legal_actions(), (FOLD, CALL, raise_to(4)))
        full_raise = facing_two.apply_action(raise_to(4))
        self.assertTrue(full_raise.betting.history[-1].full_raise)
        self.assertEqual(full_raise.legal_actions(), (FOLD, CALL))

        facing_four = dealt.apply_action(raise_to(4))
        self.assertEqual(facing_four.legal_actions(), (FOLD, CALL))

    def test_exact_settlement_covers_check_fold_call_and_both_raise_classes(self) -> None:
        dealt = _dealt(_game())

        self.assertEqual(dealt.apply_action(CHECK).returns(), (2.0, -2.0))
        self.assertEqual(
            dealt.apply_action(raise_to(2)).apply_action(FOLD).returns(),
            (2.0, -2.0),
        )
        self.assertEqual(
            dealt.apply_action(raise_to(2)).apply_action(CALL).returns(),
            (4.0, -4.0),
        )
        self.assertEqual(
            dealt
            .apply_action(raise_to(2))
            .apply_action(raise_to(4))
            .apply_action(FOLD)
            .returns(),
            (-4.0, 4.0),
        )
        self.assertEqual(
            dealt
            .apply_action(raise_to(3))
            .apply_action(raise_to(4))
            .apply_action(FOLD)
            .returns(),
            (-5.0, 5.0),
        )
        self.assertEqual(
            dealt
            .apply_action(raise_to(3))
            .apply_action(raise_to(4))
            .apply_action(CALL)
            .returns(),
            (6.0, -6.0),
        )

    def test_information_keys_hide_opponent_cards_and_remember_exact_raise_totals(self) -> None:
        own = make_hole("As", "Ad")
        first = RiverDeal(own, make_hole("Kh", "Kd"))
        second = RiverDeal(own, make_hole("Th", "Td"))
        game = _game(deals=((first, 0.5), (second, 0.5)))

        root_keys = {
            _dealt(game, deal).information_state_key(0)
            for deal in (first, second)
        }
        post_raise_keys = {
            _dealt(game, deal)
            .apply_action(raise_to(3))
            .apply_action(raise_to(4))
            .information_state_key(0)
            for deal in (first, second)
        }
        self.assertEqual(len(root_keys), 1)
        self.assertEqual(len(post_raise_keys), 1)
        self.assertIn("p0:raise-to-3/p1:raise-to-4", next(iter(post_raise_keys)))

    def test_repeated_actor_forces_sequence_form(self) -> None:
        game = _game()
        report = path_single_visit_report(game)

        self.assertFalse(report.passed)
        self.assertEqual(report.repeated_player, 0)
        with self.assertRaisesRegex(ValueError, "player 0 repeats"):
            require_behavioral_affine_shortcut(game)

    def test_structure_digest_excludes_range_but_provenance_includes_it(self) -> None:
        first = _game()
        source_deal = first.deals[0][0]
        other = RiverDeal(make_hole("As", "Ad"), make_hole("Th", "Td"))
        second = _game(deals=((source_deal, 0.75), (other, 0.25)))

        self.assertEqual(first.structural_digest, second.structural_digest)
        self.assertNotEqual(first.provenance_digest, second.provenance_digest)

    def test_invalid_entry_states_and_actions_fail_closed(self) -> None:
        base = _checked_to_river()
        deal = RiverDeal(make_hole("As", "Ad"), make_hole("Kh", "Kd"))
        kwargs = {
            "board": parse_cards("2c", "7d", "9h", "Js", "Qc"),
            "deals": ((deal, 1.0),),
        }
        with self.assertRaisesRegex(ValueError, "river"):
            LegalHeadsUpRiverContinuation(
                base_state=replace(base, street=BettingStreet.TURN),
                **kwargs,
            )
        with self.assertRaisesRegex(ValueError, "zero committed"):
            LegalHeadsUpRiverContinuation(
                base_state=replace(
                    base,
                    starting_stacks=(7, *base.starting_stacks[1:]),
                    total_contributions=(1, *base.total_contributions[1:]),
                ),
                **kwargs,
            )
        dealt = _dealt(_game())
        with self.assertRaisesRegex(ValueError, "illegal continuation action"):
            dealt.apply_action(raise_to(5))
        with self.assertRaisesRegex(ValueError, "exact history replay"):
            LegalHeadsUpRiverState(
                game=dealt.game,
                betting=dealt.betting.apply_action(raise_to(2)),
                deal=dealt.deal,
            )
        with self.assertRaisesRegex(ValueError, "actor is inconsistent"):
            LegalHeadsUpRiverState(
                game=dealt.game,
                betting=dealt.betting,
                deal=dealt.deal,
                continuation_history=((1, CHECK),),
            )
        self.assertEqual(
            dealt.apply_action(raise_to(3)).betting.legal_decision().action_kinds,
            (BettingActionKind.FOLD, BettingActionKind.CALL, BettingActionKind.RAISE),
        )


if __name__ == "__main__":
    unittest.main()
