from __future__ import annotations

import unittest
from dataclasses import replace

from pontius.full_width_reference_policy import ImmutableFullWidthReferencePolicy
from pontius.holdem_cards import (
    HandRank,
    OneSeatCardState,
    SixSeatHoldemDeal,
    make_hole,
    parse_cards,
)
from pontius.immutable_blueprint import (
    BlueprintActionEntry,
    BlueprintDecisionKey,
    ImmutableBlueprintActionSource,
)
from pontius.no_limit_betting import (
    CALL,
    CHECK,
    SEAT_COUNT,
    BettingStreet,
    NoLimitBettingState,
    TerminalReason,
    raise_to,
)
from pontius.reference_hand_replay import (
    OpponentActionEvent,
    ReferenceHandResult,
    ReferenceHandSpec,
    ReplayOperationKind,
    replay_reference_hand,
)


class _StepClock:
    def __init__(self, *, step_ns: int = 1_000_000) -> None:
        self.value = 0
        self.step_ns = step_ns

    def __call__(self) -> int:
        observed = self.value
        self.value += self.step_ns
        return observed


def _deal_a() -> SixSeatHoldemDeal:
    return SixSeatHoldemDeal(
        private_hands=(
            make_hole("As", "Ad"),
            make_hole("Kh", "Kd"),
            make_hole("Ts", "8s"),
            make_hole("Ks", "Td"),
            make_hole("Ah", "3h"),
            make_hole("4s", "5s"),
        ),
        board_runout=parse_cards("2c", "7d", "9h", "Js", "Qc"),
    )


def _deal_b() -> SixSeatHoldemDeal:
    return SixSeatHoldemDeal(
        private_hands=(
            make_hole("As", "Ad"),
            make_hole("Th", "8h"),
            make_hole("Kc", "Tc"),
            make_hole("Kh", "Kd"),
            make_hole("Ah", "3h"),
            make_hole("4s", "5s"),
        ),
        board_runout=parse_cards("2c", "7d", "9h", "Js", "Qc"),
    )


def _postflop_checks(street: BettingStreet) -> tuple[OpponentActionEvent, ...]:
    return tuple(
        OpponentActionEvent(street, seat, CHECK)
        for seat in (1, 2, 4, 5, 0)
    )


def _fixture_a(
    *,
    blueprint: ImmutableBlueprintActionSource | None = None,
    opponent_actions: tuple[OpponentActionEvent, ...] | None = None,
    full_width_policy: ImmutableFullWidthReferencePolicy | None = None,
) -> ReferenceHandSpec:
    default_actions = (
        OpponentActionEvent(BettingStreet.PREFLOP, 4, CALL),
        OpponentActionEvent(BettingStreet.PREFLOP, 5, CALL),
        OpponentActionEvent(BettingStreet.PREFLOP, 0, CALL),
        OpponentActionEvent(BettingStreet.PREFLOP, 1, CALL),
        OpponentActionEvent(BettingStreet.PREFLOP, 2, CHECK),
        *_postflop_checks(BettingStreet.FLOP),
        *_postflop_checks(BettingStreet.TURN),
        *_postflop_checks(BettingStreet.RIVER),
    )
    return ReferenceHandSpec(
        deal=_deal_a(),
        button=0,
        controlled_seat=3,
        starting_stacks=(200,) * SEAT_COUNT,
        small_blind=1,
        big_blind=2,
        blueprint=(
            ImmutableBlueprintActionSource("fixture-a-empty-v1")
            if blueprint is None
            else blueprint
        ),
        opponent_actions=(
            default_actions if opponent_actions is None else opponent_actions
        ),
        full_width_policy=full_width_policy,
    )


def _fixture_b() -> ReferenceHandSpec:
    return ReferenceHandSpec(
        deal=_deal_b(),
        button=0,
        controlled_seat=5,
        starting_stacks=(10, 6, 4, 20, 20, 20),
        small_blind=1,
        big_blind=2,
        blueprint=ImmutableBlueprintActionSource("fixture-b-empty-v1"),
        opponent_actions=(
            OpponentActionEvent(BettingStreet.PREFLOP, 3, raise_to(10)),
            OpponentActionEvent(BettingStreet.PREFLOP, 4, CALL),
            OpponentActionEvent(BettingStreet.PREFLOP, 0, CALL),
            OpponentActionEvent(BettingStreet.PREFLOP, 1, CALL),
            OpponentActionEvent(BettingStreet.PREFLOP, 2, CALL),
            OpponentActionEvent(BettingStreet.FLOP, 3, raise_to(10)),
            OpponentActionEvent(BettingStreet.FLOP, 4, CALL),
        ),
    )


def _independent_pots(
    contributions: tuple[int, ...],
    folded: tuple[bool, ...],
) -> tuple[tuple[int, tuple[int, ...]], ...]:
    """Build actual pots one chip depth at a time without production assembly."""

    pots: list[tuple[int, tuple[int, ...]]] = []
    for depth in range(1, max(contributions, default=0) + 1):
        contributors = tuple(
            seat
            for seat, contribution in enumerate(contributions)
            if contribution >= depth
        )
        eligible = tuple(seat for seat in contributors if not folded[seat])
        if not eligible:
            raise AssertionError("independent pot layer has no live claimant")
        if pots and pots[-1][1] == eligible:
            pots[-1] = (pots[-1][0] + len(contributors), eligible)
        else:
            pots.append((len(contributors), eligible))
    return tuple(pots)


def _independent_payouts(
    result: ReferenceHandResult,
    strengths: tuple[HandRank | None, ...],
) -> tuple[int, ...]:
    payouts = [0] * SEAT_COUNT
    odd_order = tuple(
        (result.final_betting.button + offset) % SEAT_COUNT
        for offset in range(1, SEAT_COUNT + 1)
    )
    for amount, eligible in _independent_pots(
        result.final_betting.total_contributions,
        result.final_betting.folded,
    ):
        eligible_strengths = tuple(strengths[seat] for seat in eligible)
        if any(strength is None for strength in eligible_strengths):
            raise AssertionError("live independent pot claimant has no strength")
        best = max(strength for strength in eligible_strengths if strength is not None)
        winners = tuple(seat for seat in eligible if strengths[seat] == best)
        share, odd = divmod(amount, len(winners))
        for winner in winners:
            payouts[winner] += share
        for winner in (seat for seat in odd_order if seat in winners):
            if odd == 0:
                break
            payouts[winner] += 1
            odd -= 1
    return tuple(payouts)


class ReferenceHandReplayTests(unittest.TestCase):
    def assert_complete_timing_trace(self, result: ReferenceHandResult) -> None:
        self.assertEqual(
            tuple(snapshot.street for snapshot in result.completed_street_deadlines),
            ("preflop", "flop", "turn", "river"),
        )
        for snapshot in result.completed_street_deadlines:
            self.assertEqual(snapshot.maximum_seconds, 15.0)
            self.assertFalse(snapshot.deadline_crossed)
            operations = tuple(
                operation
                for operation in result.charged_operations
                if operation.street.value == snapshot.street
            )
            self.assertEqual(len(operations), snapshot.charge_intervals)
            self.assertEqual(
                tuple(
                    (operation.interval_before, operation.interval_after)
                    for operation in operations
                ),
                tuple((index, index + 1) for index in range(len(operations))),
            )
            self.assertEqual(
                operations[-1].charged_after_seconds,
                snapshot.charged_compute_seconds,
            )
            self.assertTrue(
                all(
                    operation.charged_after_seconds
                    > operation.charged_before_seconds
                    for operation in operations
                )
            )
        self.assertEqual(
            sum(snapshot.charge_intervals for snapshot in result.completed_street_deadlines),
            len(result.charged_operations),
        )

    def test_fixture_a_replays_passive_four_street_showdown(self) -> None:
        spec = _fixture_a()
        result = replay_reference_hand(spec, clock_ns=_StepClock())
        self.assertEqual(result.final_betting.terminal_reason, TerminalReason.SHOWDOWN)
        self.assertEqual(result.final_betting.total_contributions, (2,) * SEAT_COUNT)
        self.assertEqual(result.final_betting.pot, 12)
        self.assertEqual(
            tuple(pot.amount for pot in result.settlement.side_pots),
            (12,),
        )
        self.assertEqual(result.settlement.payouts, (0, 0, 0, 12, 0, 0))
        self.assertEqual(result.opponent_events_consumed, 20)
        self.assertEqual(
            tuple(record.seat for record in result.final_betting.history),
            (
                3, 4, 5, 0, 1, 2,
                1, 2, 3, 4, 5, 0,
                1, 2, 3, 4, 5, 0,
                1, 2, 3, 4, 5, 0,
            ),
        )
        self.assertEqual(
            tuple(selection.action for selection in result.controlled_selections),
            (CALL, CHECK, CHECK, CHECK),
        )
        self.assertTrue(
            all(not selection.table_hit for selection in result.controlled_selections)
        )
        self.assertEqual(
            tuple(emission.selected for emission in result.controlled_emissions),
            (CALL, CHECK, CHECK, CHECK),
        )
        strengths = result.showdown_strengths
        assert strengths is not None
        assert strengths[3] is not None
        self.assertEqual(strengths[3], max(strength for strength in strengths if strength))
        self.assert_complete_timing_trace(result)
        self.assertGreaterEqual(result.post_hand_verification_wall_seconds, 0.0)

    def test_fixture_b_reproduces_four_actual_pots_and_independent_payouts(self) -> None:
        spec = _fixture_b()
        result = replay_reference_hand(spec, clock_ns=_StepClock())
        self.assertEqual(result.final_betting.terminal_reason, TerminalReason.SHOWDOWN)
        self.assertEqual(
            result.final_betting.total_contributions,
            (10, 6, 4, 20, 20, 20),
        )
        independent = _independent_pots(
            result.final_betting.total_contributions,
            result.final_betting.folded,
        )
        self.assertEqual(
            tuple(amount for amount, _ in independent),
            (24, 10, 16, 30),
        )
        self.assertEqual(
            tuple((pot.amount, pot.eligible_seats) for pot in result.settlement.side_pots),
            independent,
        )
        strengths = result.showdown_strengths
        assert strengths is not None
        for seat in range(SEAT_COUNT):
            assert strengths[seat] is not None
        self.assertGreater(strengths[2], strengths[1])  # type: ignore[operator]
        self.assertGreater(strengths[1], strengths[0])  # type: ignore[operator]
        self.assertGreater(strengths[0], strengths[3])  # type: ignore[operator]
        self.assertGreater(strengths[3], strengths[4])  # type: ignore[operator]
        self.assertGreater(strengths[4], strengths[5])  # type: ignore[operator]
        self.assertEqual(
            _independent_payouts(result, strengths),
            (16, 10, 24, 30, 0, 0),
        )
        self.assertEqual(result.settlement.payouts, (16, 10, 24, 30, 0, 0))
        self.assertEqual(sum(result.settlement.net_returns), 0)
        self.assertEqual(sum(result.settlement.final_stacks), sum(spec.starting_stacks))
        self.assertEqual(
            tuple(selection.action for selection in result.controlled_selections),
            (CALL, CALL),
        )
        self.assertEqual(result.opponent_events_consumed, 7)
        self.assert_complete_timing_trace(result)

    def test_card_domains_and_blueprint_keys_never_reveal_future_or_opponent_cards(self) -> None:
        spec = _fixture_a()
        result = replay_reference_hand(spec, clock_ns=_StepClock())
        self.assertEqual(
            tuple(
                (domain.street, domain.public_board_size, domain.compatible_opponent_hands)
                for domain in result.card_domains
            ),
            (
                (BettingStreet.PREFLOP, 0, 1_225),
                (BettingStreet.FLOP, 3, 1_081),
                (BettingStreet.TURN, 4, 1_035),
                (BettingStreet.RIVER, 5, 990),
            ),
        )
        for selection in result.controlled_selections:
            key = selection.key
            self.assertEqual(key.private_hand, spec.deal.hand(spec.controlled_seat))
            self.assertEqual(key.board, spec.deal.public_cards(key.street))
        self.assertEqual(
            sum(
                operation.kind is ReplayOperationKind.CARD_DOMAIN_AUDIT
                for operation in result.charged_operations
            ),
            4,
        )

    def test_ordinary_monotonic_clock_completes_the_maintained_replay(self) -> None:
        result = replay_reference_hand(_fixture_a())
        self.assertFalse(
            any(snapshot.deadline_crossed for snapshot in result.completed_street_deadlines)
        )
        self.assertTrue(
            all(
                snapshot.charged_compute_seconds >= 0.0
                for snapshot in result.completed_street_deadlines
            )
        )

    def test_full_width_policy_and_five_opponent_belief_cross_four_streets(self) -> None:
        policy = ImmutableFullWidthReferencePolicy("fixture-a-full-width-v1")
        result = replay_reference_hand(_fixture_a(full_width_policy=policy))
        belief = result.final_full_width_belief
        assert belief is not None

        self.assertEqual(result.full_width_policy_digest, policy.digest)
        self.assertEqual(
            tuple(distribution.selected_action for distribution in result.controlled_policy_distributions),
            (CALL, CHECK, CHECK, CHECK),
        )
        self.assertEqual(
            tuple(emission.reason.value for emission in result.controlled_emissions),
            ("candidate",) * 4,
        )
        self.assertTrue(
            all(not emission.used_fallback for emission in result.controlled_emissions)
        )
        self.assertEqual(len(result.opponent_action_likelihoods), 20)
        self.assertEqual(len(belief.likelihood_digests), 20)
        self.assertEqual(
            belief.likelihood_digests,
            tuple(likelihood.digest for likelihood in result.opponent_action_likelihoods),
        )
        self.assertEqual(
            tuple(snapshot.opponent_hand_counts for snapshot in result.full_width_belief_snapshots),
            ((1_225,) * 5, (1_081,) * 5, (1_035,) * 5, (990,) * 5),
        )
        self.assertEqual(
            tuple(snapshot.likelihood_updates for snapshot in result.full_width_belief_snapshots),
            (0, 5, 10, 15),
        )
        self.assertEqual(belief.opponent_hand_counts, (990,) * 5)
        self.assertEqual(result.final_betting.pot, 12)
        self.assertEqual(result.settlement.payouts, (0, 0, 0, 12, 0, 0))
        self.assertEqual(result.opponent_events_consumed, 20)
        self.assertEqual(
            sum(
                operation.kind is ReplayOperationKind.OPPONENT_ACTION_LIKELIHOOD
                for operation in result.charged_operations
            ),
            20,
        )
        self.assertEqual(
            sum(
                operation.kind is ReplayOperationKind.FULL_WIDTH_BELIEF_UPDATE
                for operation in result.charged_operations
            ),
            20,
        )
        self.assertEqual(
            sum(
                operation.kind is ReplayOperationKind.FULL_WIDTH_POLICY_SELECTION
                for operation in result.charged_operations
            ),
            4,
        )
        self.assert_complete_timing_trace(result)

    def test_wrong_actor_street_missing_and_extra_events_fail_closed(self) -> None:
        spec = _fixture_a()
        first = spec.opponent_actions[0]
        wrong_actor = (
            replace(first, seat=5),
            *spec.opponent_actions[1:],
        )
        with self.assertRaisesRegex(ValueError, "wrong acting seat"):
            replay_reference_hand(
                replace(spec, opponent_actions=wrong_actor),
                clock_ns=_StepClock(),
            )
        wrong_street = (
            replace(first, street=BettingStreet.FLOP),
            *spec.opponent_actions[1:],
        )
        with self.assertRaisesRegex(ValueError, "wrong street"):
            replay_reference_hand(
                replace(spec, opponent_actions=wrong_street),
                clock_ns=_StepClock(),
            )
        with self.assertRaisesRegex(ValueError, "ended before"):
            replay_reference_hand(
                replace(spec, opponent_actions=spec.opponent_actions[:-1]),
                clock_ns=_StepClock(),
            )
        extra = (
            *spec.opponent_actions,
            OpponentActionEvent(BettingStreet.RIVER, 1, CHECK),
        )
        with self.assertRaisesRegex(ValueError, "events after"):
            replay_reference_hand(
                replace(spec, opponent_actions=extra),
                clock_ns=_StepClock(),
            )

    def test_illegal_blueprint_entry_aborts_before_controlled_emission(self) -> None:
        spec = _fixture_a()
        cards = OneSeatCardState.preflop(
            controlled_seat=spec.controlled_seat,
            private_hand=spec.deal.hand(spec.controlled_seat),
        )
        betting = NoLimitBettingState.new_hand(
            button=spec.button,
            starting_stacks=spec.starting_stacks,
            small_blind=spec.small_blind,
            big_blind=spec.big_blind,
        )
        key = BlueprintDecisionKey.from_state(
            cards=cards,
            betting=betting,
            decision=betting.legal_decision(),
        )
        illegal = ImmutableBlueprintActionSource(
            "fixture-a-illegal-check",
            (BlueprintActionEntry(key, CHECK),),
        )
        with self.assertRaisesRegex(ValueError, "unavailable action kind"):
            replay_reference_hand(
                replace(spec, blueprint=illegal),
                clock_ns=_StepClock(),
            )

    def test_reference_spec_rejects_controlled_events_and_mutable_aliases(self) -> None:
        spec = _fixture_a()
        with self.assertRaisesRegex(ValueError, "controlled-seat actions"):
            replace(
                spec,
                opponent_actions=(
                    OpponentActionEvent(BettingStreet.PREFLOP, 3, CALL),
                ),
            )
        with self.assertRaisesRegex(TypeError, "immutable tuple"):
            replace(spec, opponent_actions=list(spec.opponent_actions))  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "immutable tuple"):
            replace(spec, starting_stacks=list(spec.starting_stacks))  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "semantic"):
            OpponentActionEvent(  # type: ignore[arg-type]
                BettingStreet.PREFLOP,
                4,
                "call",
            )
        with self.assertRaisesRegex(TypeError, "immutable and semantic"):
            replace(spec, full_width_policy="policy")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
