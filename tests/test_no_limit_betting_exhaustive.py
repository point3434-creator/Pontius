from __future__ import annotations

import unittest
from collections import deque

from pontius.no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    SEAT_COUNT,
    BettingAction,
    NoLimitBettingState,
    TerminalReason,
    raise_to,
)


def _semantic_key(state: NoLimitBettingState) -> tuple[object, ...]:
    return (
        state.button,
        state.street,
        state.stacks,
        state.total_contributions,
        state.street_contributions,
        state.folded,
        state.pending_seats,
        state.last_full_raise_size,
        state.acted_at_bet,
        state.round_complete,
        state.terminal_reason,
    )


def _all_legal_integer_actions(state: NoLimitBettingState) -> tuple[BettingAction, ...]:
    decision = state.legal_decision()
    actions = [FOLD, CALL] if decision.can_call else [CHECK]
    bounds = decision.raise_bounds
    if bounds is not None:
        actions.extend(
            raise_to(amount)
            for amount in range(
                bounds.minimum_raise_to,
                bounds.maximum_raise_to + 1,
            )
        )
    return tuple(actions)


def _independent_pots(
    state: NoLimitBettingState,
) -> tuple[tuple[int, tuple[int, ...]], ...]:
    """Build actual pots one chip-depth at a time, independently of production."""

    pots: list[tuple[int, tuple[int, ...]]] = []
    for depth in range(1, max(state.total_contributions, default=0) + 1):
        contributors = tuple(
            seat
            for seat, contribution in enumerate(state.total_contributions)
            if contribution >= depth
        )
        if not contributors:
            continue
        eligible = tuple(seat for seat in contributors if not state.folded[seat])
        if not eligible:
            raise AssertionError("independent layer has no live claimant")
        if pots and pots[-1][1] == eligible:
            pots[-1] = (pots[-1][0] + len(contributors), eligible)
        else:
            pots.append((len(contributors), eligible))
    return tuple(pots)


def _independent_payouts(
    state: NoLimitBettingState,
    strengths: tuple[int | None, ...] | None,
) -> tuple[int, ...]:
    payouts = [0] * SEAT_COUNT
    odd_order = tuple(
        (state.button + offset) % SEAT_COUNT
        for offset in range(1, SEAT_COUNT + 1)
    )
    for amount, eligible in _independent_pots(state):
        if state.terminal_reason is TerminalReason.FOLD:
            winners = eligible
        else:
            assert strengths is not None
            best = max(strengths[seat] for seat in eligible)
            winners = tuple(
                seat for seat in eligible if strengths[seat] == best
            )
        share, odd = divmod(amount, len(winners))
        for winner in winners:
            payouts[winner] += share
        for winner in (seat for seat in odd_order if seat in winners):
            if odd == 0:
                break
            payouts[winner] += 1
            odd -= 1
    return tuple(payouts)


class ExhaustiveNoLimitBettingOracleTests(unittest.TestCase):
    def test_every_three_chip_six_seat_state_matches_independent_pot_oracle(self) -> None:
        queue: deque[NoLimitBettingState] = deque(
            NoLimitBettingState.new_hand(
                button=button,
                starting_stacks=(3,) * SEAT_COUNT,
                small_blind=1,
                big_blind=2,
            )
            for button in range(SEAT_COUNT)
        )
        seen: set[tuple[object, ...]] = set()
        terminal_count = 0
        edge_count = 0
        while queue:
            state = queue.popleft()
            state_key = _semantic_key(state)
            if state_key in seen:
                continue
            seen.add(state_key)
            state.assert_invariants()
            expected_pots = _independent_pots(state)
            actual_pots = tuple(
                (pot.amount, pot.eligible_seats)
                for pot in state.side_pots()
            )
            self.assertEqual(actual_pots, expected_pots)

            if state.is_terminal:
                terminal_count += 1
                if state.terminal_reason is TerminalReason.FOLD:
                    profiles: tuple[tuple[int | None, ...] | None, ...] = (None,)
                else:
                    profiles = (
                        tuple(
                            0 if seat in state.live_seats else None
                            for seat in range(SEAT_COUNT)
                        ),
                        tuple(
                            seat % 3 if seat in state.live_seats else None
                            for seat in range(SEAT_COUNT)
                        ),
                    )
                for strengths in profiles:
                    self.assertEqual(
                        state.settle(strengths).payouts,
                        _independent_payouts(state, strengths),
                    )
                continue

            if state.round_complete:
                queue.append(state.advance_street())
                edge_count += 1
                continue
            for action in _all_legal_integer_actions(state):
                queue.append(state.apply_action(action))
                edge_count += 1

        self.assertEqual(len(seen), 45_456)
        self.assertEqual(terminal_count, 7_830)
        self.assertEqual(edge_count, 60_732)


if __name__ == "__main__":
    unittest.main()
