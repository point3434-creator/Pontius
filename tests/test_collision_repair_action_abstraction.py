from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction

from pontius.collision_repair_action_abstraction import (
    ADR0300_COLLISION_REPAIR_SOURCE_ID,
    ADR0300_COLLISION_REPAIR_SOURCE_SHA256,
    CollisionRepairActionAbstractionSource,
)
from pontius.legal_action_abstraction import (
    ClipDirection,
    ImmutableActionAbstractionSource,
    PotFraction,
    RaiseSizeOriginKind,
    select_collision_repair_overbet,
)
from pontius.no_limit_betting import CALL, FOLD, NoLimitBettingState, raise_to
from pontius.reduced_river_sizing_oracle import two_live_seat_river_opening_state


def _v2_source() -> ImmutableActionAbstractionSource:
    return ImmutableActionAbstractionSource(
        source_id="adr-0293-dyadic-pot-odds-v2",
        pot_fractions=(
            PotFraction(1, 4),
            PotFraction(1, 2),
            PotFraction(1, 1),
            PotFraction(2, 1),
        ),
    )


class CollisionRepairActionAbstractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = CollisionRepairActionAbstractionSource(
            source_id=ADR0300_COLLISION_REPAIR_SOURCE_ID
        )

    def test_distinct_two_pot_target_retains_primary_branch_and_v2_actions(self) -> None:
        state = two_live_seat_river_opening_state(pot=6, stack=30)
        decision = state.legal_decision()
        fraction, collided = select_collision_repair_overbet(
            betting=state,
            decision=decision,
        )
        abstraction = self.source.build(betting=state, decision=decision)
        v2 = _v2_source().build(betting=state, decision=decision)

        self.assertEqual(fraction, PotFraction(2, 1))
        self.assertFalse(collided)
        self.assertEqual(
            tuple(int(value.action.raise_to) for value in abstraction.raise_sizes),
            (2, 3, 6, 12, 30),
        )
        self.assertLessEqual(set(v2.actions), set(abstraction.actions))
        adaptive = next(
            origin
            for value in abstraction.raise_sizes
            for origin in value.origins
            if origin.kind is RaiseSizeOriginKind.COLLISION_REPAIR_OVERBET
        )
        self.assertEqual(adaptive.pot_fraction, PotFraction(2, 1))
        self.assertEqual(adaptive.raw_raise_to, 12)
        self.assertEqual(adaptive.projected_raise_to, 12)
        self.assertIs(adaptive.clip, ClipDirection.NONE)
        self.assertIs(adaptive.collision_repair_triggered, False)

    def test_all_in_collision_substitutes_three_halves_without_losing_v2_action(self) -> None:
        state = two_live_seat_river_opening_state(pot=12, stack=20)
        decision = state.legal_decision()
        fraction, collided = select_collision_repair_overbet(
            betting=state,
            decision=decision,
        )
        abstraction = self.source.build(betting=state, decision=decision)
        v2 = _v2_source().build(betting=state, decision=decision)

        self.assertEqual(fraction, PotFraction(3, 2))
        self.assertTrue(collided)
        self.assertEqual(
            tuple(int(value.action.raise_to) for value in abstraction.raise_sizes),
            (2, 3, 6, 12, 18, 20),
        )
        self.assertLessEqual(set(v2.actions), set(abstraction.actions))
        adaptive = next(
            origin
            for value in abstraction.raise_sizes
            for origin in value.origins
            if origin.kind is RaiseSizeOriginKind.COLLISION_REPAIR_OVERBET
        )
        self.assertEqual(adaptive.pot_fraction, PotFraction(3, 2))
        self.assertEqual(adaptive.raw_raise_to, 18)
        self.assertEqual(adaptive.projected_raise_to, 18)
        self.assertIs(adaptive.clip, ClipDirection.NONE)
        self.assertIs(adaptive.collision_repair_triggered, True)

    def test_fallback_clipping_and_deduplication_retain_every_origin(self) -> None:
        state = two_live_seat_river_opening_state(pot=40, stack=10)
        decision = state.legal_decision()
        abstraction = self.source.build(betting=state, decision=decision)

        self.assertEqual(
            tuple(int(value.action.raise_to) for value in abstraction.raise_sizes),
            (2, 10),
        )
        all_in = abstraction.raise_sizes[-1]
        self.assertEqual(len(all_in.origins), 6)
        adaptive = next(
            origin
            for origin in all_in.origins
            if origin.kind is RaiseSizeOriginKind.COLLISION_REPAIR_OVERBET
        )
        self.assertEqual(adaptive.pot_fraction, PotFraction(3, 2))
        self.assertEqual(adaptive.raw_raise_to, 60)
        self.assertEqual(adaptive.projected_raise_to, 10)
        self.assertIs(adaptive.clip, ClipDirection.HIGH)
        self.assertIs(adaptive.collision_repair_triggered, True)
        self.assertTrue(all_in.has_origin(RaiseSizeOriginKind.MAXIMUM_CONTESTABLE))
        self.assertTrue(all_in.has_origin(RaiseSizeOriginKind.ALL_IN))
        v2 = _v2_source().build(betting=state, decision=decision)
        self.assertLessEqual(set(v2.actions), set(abstraction.actions))

    def test_projection_is_exact_barycentric_and_does_not_mutate_state(self) -> None:
        state = two_live_seat_river_opening_state(pot=12, stack=20)
        abstraction = self.source.build(
            betting=state,
            decision=state.legal_decision(),
        )

        projection = abstraction.project(raise_to(17))
        self.assertEqual(
            tuple(atom.action for atom in projection.atoms),
            (raise_to(12), raise_to(18)),
        )
        self.assertEqual(
            tuple(atom.weight.fraction for atom in projection.atoms),
            (Fraction(1, 6), Fraction(5, 6)),
        )
        self.assertEqual(
            sum(
                atom.weight.fraction * int(atom.action.raise_to)
                for atom in projection.atoms
            ),
            17,
        )
        self.assertEqual(abstraction.betting, state)

    def test_unequal_stacks_and_cumulative_short_all_ins_keep_exact_anchors(self) -> None:
        unequal = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(50, 20, 20, 100, 20, 20),
            small_blind=1,
            big_blind=2,
        )
        unequal_decision = unequal.legal_decision()
        unequal_abstraction = self.source.build(
            betting=unequal,
            decision=unequal_decision,
        )
        by_amount = {
            int(value.action.raise_to): value
            for value in unequal_abstraction.raise_sizes
        }
        self.assertTrue(by_amount[50].has_origin(
            RaiseSizeOriginKind.MAXIMUM_CONTESTABLE
        ))
        self.assertTrue(by_amount[100].has_origin(RaiseSizeOriginKind.ALL_IN))

        reopened = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(30, 30, 30, 30, 3, 4),
            small_blind=1,
            big_blind=2,
        )
        reopened = reopened.apply_action(CALL)
        reopened = reopened.apply_action(raise_to(3))
        reopened = reopened.apply_action(raise_to(4))
        for _ in range(3):
            reopened = reopened.apply_action(CALL)
        reopened_decision = reopened.legal_decision()
        assert reopened_decision.raise_bounds is not None
        self.assertEqual(reopened_decision.raise_bounds.minimum_raise_to, 6)
        reopened_abstraction = self.source.build(
            betting=reopened,
            decision=reopened_decision,
        )
        minimum = next(
            value
            for value in reopened_abstraction.raise_sizes
            if value.action == raise_to(6)
        )
        self.assertTrue(minimum.has_origin(RaiseSizeOriginKind.MINIMUM))

    def test_short_all_in_and_closed_raising_are_preserved(self) -> None:
        state = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(20, 20, 20, 20, 3, 20),
            small_blind=1,
            big_blind=2,
        ).apply_action(CALL)
        abstraction = self.source.build(
            betting=state,
            decision=state.legal_decision(),
        )
        self.assertEqual(abstraction.actions, (FOLD, CALL, raise_to(3)))

        state = state.apply_action(raise_to(3))
        for _ in range(4):
            state = state.apply_action(CALL)
        closed = self.source.build(betting=state, decision=state.legal_decision())
        self.assertEqual(closed.actions, (FOLD, CALL))
        self.assertEqual(closed.raise_sizes, ())

    def test_source_is_digest_bound_immutable_and_fails_closed(self) -> None:
        same = CollisionRepairActionAbstractionSource(
            source_id=ADR0300_COLLISION_REPAIR_SOURCE_ID
        )
        renamed = CollisionRepairActionAbstractionSource(source_id="renamed-v3")
        self.assertEqual(self.source.canonical_bytes, same.canonical_bytes)
        self.assertEqual(self.source.digest, same.digest)
        self.assertEqual(
            self.source.digest,
            ADR0300_COLLISION_REPAIR_SOURCE_SHA256,
        )
        self.assertNotEqual(self.source.digest, renamed.digest)
        with self.assertRaises(FrozenInstanceError):
            self.source.source_id = "mutable"  # type: ignore[misc]
        with self.assertRaisesRegex(ValueError, "nonempty"):
            CollisionRepairActionAbstractionSource(source_id=" ")

        state = NoLimitBettingState.six_max_100bb(button=0)
        decision = state.legal_decision()
        changed = state.apply_action(CALL)
        with self.assertRaisesRegex(ValueError, "stale"):
            self.source.build(betting=changed, decision=decision)
        with self.assertRaisesRegex(TypeError, "exact betting"):
            self.source.build(  # type: ignore[arg-type]
                betting="state",
                decision=decision,
            )
        with self.assertRaisesRegex(TypeError, "exact legal"):
            self.source.build(  # type: ignore[arg-type]
                betting=state,
                decision="decision",
            )
        no_reopen = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(20, 20, 20, 20, 3, 20),
            small_blind=1,
            big_blind=2,
        ).apply_action(CALL)
        no_reopen = no_reopen.apply_action(raise_to(3))
        for _ in range(4):
            no_reopen = no_reopen.apply_action(CALL)
        with self.assertRaisesRegex(ValueError, "legal raise interval"):
            select_collision_repair_overbet(
                betting=no_reopen,
                decision=no_reopen.legal_decision(),
            )

        forged = replace(decision, acting_seat=4)
        with self.assertRaisesRegex(ValueError, "stale"):
            select_collision_repair_overbet(betting=state, decision=forged)

        primary_state = two_live_seat_river_opening_state(pot=6, stack=30)
        primary = self.source.build(
            betting=primary_state,
            decision=primary_state.legal_decision(),
        )
        adaptive_index = next(
            index
            for index, value in enumerate(primary.raise_sizes)
            if value.has_origin(RaiseSizeOriginKind.COLLISION_REPAIR_OVERBET)
        )
        adaptive_size = primary.raise_sizes[adaptive_index]
        forged_origins = tuple(
            replace(origin, pot_fraction=PotFraction(3, 2))
            if origin.kind is RaiseSizeOriginKind.COLLISION_REPAIR_OVERBET
            else origin
            for origin in adaptive_size.origins
        )
        forged_size = replace(adaptive_size, origins=forged_origins)
        forged_sizes = tuple(
            forged_size if index == adaptive_index else value
            for index, value in enumerate(primary.raise_sizes)
        )
        with self.assertRaisesRegex(ValueError, "wrong collision-repair branch"):
            replace(primary, raise_sizes=forged_sizes)

        forged_origins = tuple(
            replace(origin, collision_repair_triggered=True)
            if origin.kind is RaiseSizeOriginKind.COLLISION_REPAIR_OVERBET
            else origin
            for origin in adaptive_size.origins
        )
        forged_size = replace(adaptive_size, origins=forged_origins)
        forged_sizes = tuple(
            forged_size if index == adaptive_index else value
            for index, value in enumerate(primary.raise_sizes)
        )
        with self.assertRaisesRegex(ValueError, "wrong collision decision"):
            replace(primary, raise_sizes=forged_sizes)


if __name__ == "__main__":
    unittest.main()
