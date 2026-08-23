from __future__ import annotations

import unittest
from collections import deque

from pontius.legal_action_abstraction import ImmutableActionAbstractionSource
from pontius.no_limit_betting import (
    CALL,
    CHECK,
    FOLD,
    SEAT_COUNT,
    BettingAction,
    NoLimitBettingState,
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


class ExhaustiveLegalActionAbstractionTests(unittest.TestCase):
    def test_all_three_chip_states_retain_legal_actions_and_project_every_exact_edge(self) -> None:
        source = ImmutableActionAbstractionSource(source_id="exhaustive-three-chip-v1")
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
        edge_count = 0
        active_count = 0
        while queue:
            state = queue.popleft()
            key = _semantic_key(state)
            if key in seen:
                continue
            seen.add(key)
            state.assert_invariants()

            if state.is_terminal:
                continue
            if state.round_complete:
                queue.append(state.advance_street())
                edge_count += 1
                continue

            active_count += 1
            decision = state.legal_decision()
            abstraction = source.build(betting=state, decision=decision)
            self.assertLessEqual(len(abstraction.actions), 9)
            for retained in abstraction.actions:
                state.apply_action(retained)

            exact_actions = _all_legal_integer_actions(state)
            self.assertEqual(abstraction.exact_action_count, len(exact_actions))
            for action in exact_actions:
                projection = abstraction.project(action)
                self.assertEqual(projection.exact_action, action)
                self.assertEqual(projection.source_digest, source.digest)
                queue.append(state.apply_action(action))
                edge_count += 1

        self.assertEqual(len(seen), 45_456)
        self.assertEqual(active_count, 22_920)
        self.assertEqual(edge_count, 60_732)


if __name__ == "__main__":
    unittest.main()
