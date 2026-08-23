from __future__ import annotations

import unittest
from dataclasses import replace
from fractions import Fraction

from pontius.legal_action_abstraction import (
    ClipDirection,
    ImmutableActionAbstractionSource,
    PotFraction,
    RaiseSizeOrigin,
    RaiseSizeOriginKind,
)
from pontius.no_limit_betting import (
    CALL,
    FOLD,
    NoLimitBettingState,
    raise_to,
)


class LegalActionAbstractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = ImmutableActionAbstractionSource(source_id="unit-fixture-v1")

    def test_initial_lattice_retains_exact_anchors_and_dedup_provenance(self) -> None:
        state = NoLimitBettingState.six_max_100bb(button=0)
        abstraction = self.source.build(
            betting=state,
            decision=state.legal_decision(),
        )

        self.assertEqual(
            abstraction.actions,
            (
                FOLD,
                CALL,
                raise_to(4),
                raise_to(5),
                raise_to(7),
                raise_to(10),
                raise_to(200),
            ),
        )
        self.assertEqual(abstraction.exact_action_count, 199)
        by_amount = {
            int(value.action.raise_to): value for value in abstraction.raise_sizes
        }
        self.assertEqual(
            tuple(origin.kind for origin in by_amount[4].origins),
            (RaiseSizeOriginKind.MINIMUM, RaiseSizeOriginKind.POT_FRACTION),
        )
        self.assertEqual(
            tuple(origin.kind for origin in by_amount[200].origins),
            (RaiseSizeOriginKind.MAXIMUM_CONTESTABLE, RaiseSizeOriginKind.ALL_IN),
        )
        self.assertTrue(all(origin.clip is ClipDirection.NONE for origin in by_amount[4].origins))
        snapshot = abstraction.snapshot()
        self.assertEqual(snapshot.abstract_action_count, 7)
        self.assertEqual(snapshot.abstract_raise_count, 5)
        self.assertEqual(snapshot.merged_origin_count, 2)
        self.assertEqual(snapshot.digest, abstraction.digest)

    def test_off_tree_projection_is_exact_adjacent_and_barycentric(self) -> None:
        state = NoLimitBettingState.six_max_100bb(button=0)
        abstraction = self.source.build(
            betting=state,
            decision=state.legal_decision(),
        )

        projection = abstraction.project(raise_to(6))
        self.assertEqual(
            tuple(atom.action for atom in projection.atoms),
            (raise_to(5), raise_to(7)),
        )
        self.assertEqual(
            tuple(atom.weight.fraction for atom in projection.atoms),
            (Fraction(1, 2), Fraction(1, 2)),
        )
        self.assertEqual(
            sum(
                atom.weight.fraction * int(atom.action.raise_to)
                for atom in projection.atoms
            ),
            6,
        )
        self.assertEqual(abstraction.betting, state)

        identity = abstraction.project(CALL)
        self.assertEqual(tuple(atom.action for atom in identity.atoms), (CALL,))
        self.assertEqual(identity.atoms[0].weight.fraction, 1)

    def test_projection_rejects_an_illegal_action_without_mutating_state(self) -> None:
        state = NoLimitBettingState.six_max_100bb(button=0)
        abstraction = self.source.build(
            betting=state,
            decision=state.legal_decision(),
        )
        with self.assertRaisesRegex(ValueError, "not legal"):
            abstraction.project(raise_to(201))
        self.assertEqual(abstraction.betting, state)

    def test_clipping_and_dedup_are_explicit_near_both_bounds(self) -> None:
        state = NoLimitBettingState.six_max_100bb(button=0).apply_action(raise_to(100))
        abstraction = self.source.build(
            betting=state,
            decision=state.legal_decision(),
        )

        self.assertEqual(
            tuple(int(value.action.raise_to) for value in abstraction.raise_sizes),
            (198, 200),
        )
        origins = tuple(
            origin for value in abstraction.raise_sizes for origin in value.origins
        )
        self.assertTrue(any(origin.clip is ClipDirection.LOW for origin in origins))
        self.assertTrue(any(origin.clip is ClipDirection.HIGH for origin in origins))
        self.assertEqual(len(origins), 7)
        self.assertEqual(abstraction.snapshot().merged_origin_count, 5)
        for action in abstraction.actions:
            state.apply_action(action)

    def test_short_all_in_only_and_closed_raising_are_preserved_exactly(self) -> None:
        state = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(20, 20, 20, 20, 3, 20),
            small_blind=1,
            big_blind=2,
        ).apply_action(CALL)
        decision = state.legal_decision()
        assert decision.raise_bounds is not None
        self.assertTrue(decision.raise_bounds.all_in_only)
        abstraction = self.source.build(betting=state, decision=decision)
        self.assertEqual(abstraction.actions, (FOLD, CALL, raise_to(3)))

        state = state.apply_action(raise_to(3))
        for _ in range(4):
            state = state.apply_action(CALL)
        closed = self.source.build(betting=state, decision=state.legal_decision())
        self.assertEqual(closed.actions, (FOLD, CALL))
        self.assertEqual(closed.raise_sizes, ())
        self.assertEqual(closed.exact_action_count, 2)

    def test_cumulative_short_all_ins_reopen_with_the_new_exact_minimum(self) -> None:
        state = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(30, 30, 30, 30, 3, 4),
            small_blind=1,
            big_blind=2,
        )
        state = state.apply_action(CALL)
        state = state.apply_action(raise_to(3))
        state = state.apply_action(raise_to(4))
        for _ in range(3):
            state = state.apply_action(CALL)
        decision = state.legal_decision()
        assert decision.raise_bounds is not None
        self.assertEqual(decision.raise_bounds.minimum_raise_to, 6)
        abstraction = self.source.build(betting=state, decision=decision)
        self.assertIn(raise_to(6), abstraction.actions)
        minimum = next(value for value in abstraction.raise_sizes if value.action == raise_to(6))
        self.assertTrue(minimum.has_origin(RaiseSizeOriginKind.MINIMUM))

    def test_unequal_stacks_keep_contestable_and_own_all_in_as_distinct_anchors(self) -> None:
        state = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(50, 20, 20, 100, 20, 20),
            small_blind=1,
            big_blind=2,
        )
        decision = state.legal_decision()
        assert decision.raise_bounds is not None
        self.assertEqual(decision.raise_bounds.maximum_contestable_raise_to, 50)
        self.assertEqual(decision.raise_bounds.maximum_raise_to, 100)
        abstraction = self.source.build(betting=state, decision=decision)
        by_amount = {
            int(value.action.raise_to): value for value in abstraction.raise_sizes
        }
        self.assertTrue(by_amount[50].has_origin(RaiseSizeOriginKind.MAXIMUM_CONTESTABLE))
        self.assertTrue(by_amount[100].has_origin(RaiseSizeOriginKind.ALL_IN))

    def test_huge_stack_width_is_counted_without_integer_interval_materialization(self) -> None:
        stack = 10**12
        state = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(stack,) * 6,
            small_blind=1,
            big_blind=2,
        )
        abstraction = self.source.build(
            betting=state,
            decision=state.legal_decision(),
        )
        self.assertEqual(abstraction.exact_action_count, stack - 1)
        self.assertLessEqual(len(abstraction.actions), 9)
        self.assertEqual(abstraction.actions[-1], raise_to(stack))

    def test_source_and_abstraction_digests_bind_semantic_inputs(self) -> None:
        other = ImmutableActionAbstractionSource(
            source_id="unit-fixture-v1",
            pot_fractions=(PotFraction(1, 2), PotFraction(1, 1)),
        )
        renamed = ImmutableActionAbstractionSource(source_id="unit-fixture-v2")
        self.assertNotEqual(self.source.digest, other.digest)
        self.assertNotEqual(self.source.digest, renamed.digest)

        state = NoLimitBettingState.six_max_100bb(button=0)
        first = self.source.build(betting=state, decision=state.legal_decision())
        changed = state.apply_action(CALL)
        second = self.source.build(
            betting=changed,
            decision=changed.legal_decision(),
        )
        self.assertNotEqual(first.digest, second.digest)

    def test_stale_or_forged_inputs_fail_closed(self) -> None:
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
        with self.assertRaisesRegex(TypeError, "integer"):
            PotFraction(True, 2)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "immutable"):
            ImmutableActionAbstractionSource(  # type: ignore[arg-type]
                source_id="mutable",
                pot_fractions=[PotFraction(1, 2)],
            )
        with self.assertRaisesRegex(ValueError, "increase strictly"):
            ImmutableActionAbstractionSource(
                source_id="unordered",
                pot_fractions=(PotFraction(1, 1), PotFraction(1, 2)),
            )

        forged = replace(decision, acting_seat=4)
        with self.assertRaisesRegex(ValueError, "stale"):
            self.source.build(betting=state, decision=forged)

        abstraction = self.source.build(betting=state, decision=decision)
        bad_minimum = RaiseSizeOrigin(
            kind=RaiseSizeOriginKind.MINIMUM,
            raw_raise_to=3,
            projected_raise_to=4,
            clip=ClipDirection.LOW,
        )
        first_raise = abstraction.raise_sizes[0]
        forged_raise = replace(
            first_raise,
            origins=(bad_minimum, *first_raise.origins[1:]),
        )
        with self.assertRaisesRegex(ValueError, "mismatched raise provenance"):
            replace(
                abstraction,
                raise_sizes=(forged_raise, *abstraction.raise_sizes[1:]),
            )


if __name__ == "__main__":
    unittest.main()
