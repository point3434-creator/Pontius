from __future__ import annotations

import unittest
from collections import deque

from pontius.capacity_filling_action_abstraction import (
    ADR0305_CAPACITY_FILLING_SOURCE_ID,
    CapacityFillingActionAbstractionSource,
)
from pontius.collision_repair_action_abstraction import (
    ADR0300_COLLISION_REPAIR_SOURCE_ID,
    CollisionRepairActionAbstractionSource,
)
from pontius.legal_action_abstraction import (
    ImmutableActionAbstractionSource,
    PotFraction,
)
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
        v2_source = ImmutableActionAbstractionSource(
            source_id="adr-0293-dyadic-pot-odds-v2",
            pot_fractions=(
                PotFraction(1, 4),
                PotFraction(1, 2),
                PotFraction(1, 1),
                PotFraction(2, 1),
            ),
        )
        v3_source = CollisionRepairActionAbstractionSource(
            source_id=ADR0300_COLLISION_REPAIR_SOURCE_ID
        )
        v4_source = CapacityFillingActionAbstractionSource(
            source_id=ADR0305_CAPACITY_FILLING_SOURCE_ID
        )
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
            v2_abstraction = v2_source.build(betting=state, decision=decision)
            v3_abstraction = v3_source.build(betting=state, decision=decision)
            v4_abstraction = v4_source.build(betting=state, decision=decision)
            self.assertLessEqual(len(abstraction.actions), 9)
            self.assertLessEqual(len(v3_abstraction.raise_sizes), 7)
            self.assertLessEqual(len(v3_abstraction.actions), 9)
            self.assertLessEqual(
                set(v2_abstraction.actions),
                set(v3_abstraction.actions),
            )
            self.assertLessEqual(
                set(v3_abstraction.actions),
                set(v4_abstraction.actions),
            )
            exact_raise_count = (
                0
                if decision.raise_bounds is None
                else (
                    decision.raise_bounds.maximum_raise_to
                    - decision.raise_bounds.minimum_raise_to
                    + 1
                )
            )
            self.assertEqual(
                len(v4_abstraction.raise_sizes),
                min(7, exact_raise_count),
            )
            self.assertLessEqual(len(v4_abstraction.actions), 9)
            for retained in abstraction.actions:
                state.apply_action(retained)
            for retained in v3_abstraction.actions:
                state.apply_action(retained)
            for retained in v4_abstraction.actions:
                state.apply_action(retained)

            exact_actions = _all_legal_integer_actions(state)
            self.assertEqual(abstraction.exact_action_count, len(exact_actions))
            self.assertEqual(v3_abstraction.exact_action_count, len(exact_actions))
            self.assertEqual(v4_abstraction.exact_action_count, len(exact_actions))
            for action in exact_actions:
                projection = abstraction.project(action)
                self.assertEqual(projection.exact_action, action)
                self.assertEqual(projection.source_digest, source.digest)
                v3_projection = v3_abstraction.project(action)
                self.assertEqual(v3_projection.exact_action, action)
                self.assertEqual(v3_projection.source_digest, v3_source.digest)
                v4_projection = v4_abstraction.project(action)
                self.assertEqual(v4_projection.exact_action, action)
                self.assertEqual(v4_projection.source_digest, v4_source.digest)
                queue.append(state.apply_action(action))
                edge_count += 1

        self.assertEqual(len(seen), 45_456)
        self.assertEqual(active_count, 22_920)
        self.assertEqual(edge_count, 60_732)


if __name__ == "__main__":
    unittest.main()
