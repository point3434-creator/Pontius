from __future__ import annotations

import ast
import unittest
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
from itertools import pairwise
from pathlib import Path

from pontius.capacity_filling_action_abstraction import (
    ADR0305_CAPACITY_FILLING_SOURCE_ID,
    ADR0305_CAPACITY_FILLING_SOURCE_SHA256,
    ADR0305_MAXIMUM_ACTIONS,
    ADR0305_MAXIMUM_RAISES,
    CapacityFillingActionAbstraction,
    CapacityFillingActionAbstractionSource,
)
from pontius.collision_repair_action_abstraction import (
    ADR0300_COLLISION_REPAIR_SOURCE_ID,
    ADR0300_COLLISION_REPAIR_SOURCE_SHA256,
    CollisionRepairActionAbstractionSource,
)
from pontius.legal_action_abstraction import (
    ExactPotOddsDistance,
    RaiseSizeOriginKind,
    select_capacity_filling_pot_odds_refill,
)
from pontius.no_limit_betting import CALL, CHECK, FOLD, NoLimitBettingState, raise_to
from pontius.reduced_river_sizing_oracle import two_live_seat_river_opening_state

_ROOT = Path(__file__).parents[1]


def _pot_odds(*, pot_after_call: int, base_raise_to: int, raise_to: int) -> Fraction:
    increment = raise_to - base_raise_to
    return Fraction(increment, pot_after_call + 2 * increment)


def _brute_refill(
    *,
    state: NoLimitBettingState,
    retained: tuple[int, ...],
) -> tuple[int, int, int, Fraction]:
    decision = state.legal_decision()
    base = decision.street_contribution + decision.call_amount
    pot_after_call = state.pot + decision.call_amount
    best: tuple[int, int, int, Fraction] | None = None
    for left, right in pairwise(retained):
        for candidate in range(left + 1, right):
            coordinate = _pot_odds(
                pot_after_call=pot_after_call,
                base_raise_to=base,
                raise_to=candidate,
            )
            score = min(
                coordinate
                - _pot_odds(
                    pot_after_call=pot_after_call,
                    base_raise_to=base,
                    raise_to=left,
                ),
                _pot_odds(
                    pot_after_call=pot_after_call,
                    base_raise_to=base,
                    raise_to=right,
                )
                - coordinate,
            )
            contender = (candidate, left, right, score)
            if (
                best is None
                or score > best[3]
                or (score == best[3] and candidate < best[0])
            ):
                best = contender
    assert best is not None
    return best


class CapacityFillingActionAbstractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = CapacityFillingActionAbstractionSource(
            source_id=ADR0305_CAPACITY_FILLING_SOURCE_ID
        )
        self.parent_source = CollisionRepairActionAbstractionSource(
            source_id=ADR0300_COLLISION_REPAIR_SOURCE_ID
        )

    def test_same_ceiling_refills_every_available_slot_and_preserves_v3(self) -> None:
        expected = {
            (6, 30): (2, 3, 4, 6, 8, 12, 30),
            (12, 20): (2, 3, 6, 8, 12, 18, 20),
            (40, 10): (2, 3, 4, 5, 6, 7, 10),
            (10, 12): (2, 3, 4, 5, 7, 10, 12),
        }
        for (pot, stack), expected_sizes in expected.items():
            state = two_live_seat_river_opening_state(pot=pot, stack=stack)
            decision = state.legal_decision()
            parent = self.parent_source.build(betting=state, decision=decision)
            abstraction = self.source.build(betting=state, decision=decision)
            sizes = tuple(
                int(value.action.raise_to) for value in abstraction.raise_sizes
            )
            self.assertEqual(sizes, expected_sizes)
            self.assertLessEqual(set(parent.actions), set(abstraction.actions))
            assert decision.raise_bounds is not None
            exact_raise_count = (
                decision.raise_bounds.maximum_raise_to
                - decision.raise_bounds.minimum_raise_to
                + 1
            )
            self.assertEqual(
                len(abstraction.raise_sizes),
                min(ADR0305_MAXIMUM_RAISES, exact_raise_count),
            )
            self.assertLessEqual(len(abstraction.actions), ADR0305_MAXIMUM_ACTIONS)
            self.assertEqual(
                tuple(
                    origin.capacity_refill_rank
                    for origin in abstraction.refill_origins
                ),
                tuple(range(1, len(abstraction.refill_origins) + 1)),
            )

        state = two_live_seat_river_opening_state(pot=6, stack=30)
        abstraction = self.source.build(
            betting=state,
            decision=state.legal_decision(),
        )
        self.assertEqual(
            tuple(
                (
                    origin.capacity_refill_rank,
                    origin.capacity_refill.raise_to,
                    origin.capacity_refill.left_raise_to,
                    origin.capacity_refill.right_raise_to,
                    origin.capacity_refill.score.fraction,
                )
                for origin in abstraction.refill_origins
                if origin.capacity_refill is not None
            ),
            (
                (1, 4, 3, 6, Fraction(1, 28)),
                (2, 8, 6, 12, Fraction(1, 33)),
            ),
        )

    def test_closed_short_all_in_and_small_exact_intervals_are_unchanged(self) -> None:
        small = two_live_seat_river_opening_state(pot=2, stack=3)
        small_result = self.source.build(
            betting=small,
            decision=small.legal_decision(),
        )
        self.assertEqual(
            tuple(int(value.action.raise_to) for value in small_result.raise_sizes),
            (2, 3),
        )
        self.assertEqual(small_result.refill_origins, ())

        short = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(20, 20, 20, 20, 3, 20),
            small_blind=1,
            big_blind=2,
        ).apply_action(CALL)
        short_result = self.source.build(
            betting=short,
            decision=short.legal_decision(),
        )
        self.assertEqual(short_result.actions, (FOLD, CALL, raise_to(3)))
        self.assertEqual(short_result.refill_origins, ())

        closed = short.apply_action(raise_to(3))
        for _ in range(4):
            closed = closed.apply_action(CALL)
        closed_result = self.source.build(
            betting=closed,
            decision=closed.legal_decision(),
        )
        self.assertEqual(closed_result.actions, (FOLD, CALL))
        self.assertEqual(closed_result.raise_sizes, ())

    def test_unequal_stacks_and_cumulative_short_all_ins_refill_exact_bounds(self) -> None:
        unequal = NoLimitBettingState.new_hand(
            button=0,
            starting_stacks=(50, 20, 20, 100, 20, 20),
            small_blind=1,
            big_blind=2,
        )
        unequal_result = self.source.build(
            betting=unequal,
            decision=unequal.legal_decision(),
        )
        unequal_by_amount = {
            int(value.action.raise_to): value
            for value in unequal_result.raise_sizes
        }
        self.assertTrue(
            unequal_by_amount[50].has_origin(
                RaiseSizeOriginKind.MAXIMUM_CONTESTABLE
            )
        )
        self.assertTrue(
            unequal_by_amount[100].has_origin(RaiseSizeOriginKind.ALL_IN)
        )
        self.assertEqual(len(unequal_result.raise_sizes), ADR0305_MAXIMUM_RAISES)

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
        reopened_result = self.source.build(
            betting=reopened,
            decision=reopened_decision,
        )
        minimum = next(
            value for value in reopened_result.raise_sizes if value.action == raise_to(6)
        )
        self.assertTrue(minimum.has_origin(RaiseSizeOriginKind.MINIMUM))
        self.assertEqual(len(reopened_result.raise_sizes), ADR0305_MAXIMUM_RAISES)

    def test_exact_midpoint_helper_matches_brute_force_and_ties_smaller(self) -> None:
        for pot in range(2, 14, 2):
            for stack in (10, 17, 29):
                state = two_live_seat_river_opening_state(pot=pot, stack=stack)
                decision = state.legal_decision()
                assert decision.raise_bounds is not None
                retained = (
                    decision.raise_bounds.minimum_raise_to,
                    decision.raise_bounds.maximum_raise_to,
                )
                selected = select_capacity_filling_pot_odds_refill(
                    betting=state,
                    decision=decision,
                    retained_raise_to=retained,
                )
                brute = _brute_refill(state=state, retained=retained)
                self.assertEqual(
                    (
                        selected.raise_to,
                        selected.left_raise_to,
                        selected.right_raise_to,
                        selected.score.fraction,
                    ),
                    brute,
                )

        tie_state = two_live_seat_river_opening_state(pot=2, stack=29)
        tied = select_capacity_filling_pot_odds_refill(
            betting=tie_state,
            decision=tie_state.legal_decision(),
            retained_raise_to=(2, 29),
        )
        self.assertEqual(tied.raise_to, 4)
        self.assertEqual(tied.score.fraction, Fraction(1, 15))
        self.assertEqual(
            _pot_odds(pot_after_call=2, base_raise_to=0, raise_to=4)
            - _pot_odds(pot_after_call=2, base_raise_to=0, raise_to=2),
            _pot_odds(pot_after_call=2, base_raise_to=0, raise_to=29)
            - _pot_odds(pot_after_call=2, base_raise_to=0, raise_to=5),
        )

    def test_huge_chip_interval_uses_bounded_source_and_projection_is_exact(self) -> None:
        huge = two_live_seat_river_opening_state(pot=6, stack=1_000_000_000)
        huge_result = self.source.build(
            betting=huge,
            decision=huge.legal_decision(),
        )
        self.assertEqual(len(huge_result.raise_sizes), ADR0305_MAXIMUM_RAISES)
        self.assertEqual(huge_result.raise_sizes[0].action, raise_to(2))
        self.assertEqual(
            huge_result.raise_sizes[-1].action,
            raise_to(1_000_000_000),
        )

        path = _ROOT / "src/pontius/legal_action_abstraction.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        helper = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "select_capacity_filling_pot_odds_refill"
        )
        called_names = {
            node.func.id
            for node in ast.walk(helper)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("range", called_names)
        self.assertNotIn("float", called_names)

        state = two_live_seat_river_opening_state(pot=6, stack=30)
        abstraction = self.source.build(
            betting=state,
            decision=state.legal_decision(),
        )
        projection = abstraction.project(raise_to(5))
        self.assertEqual(
            tuple(atom.action for atom in projection.atoms),
            (raise_to(4), raise_to(6)),
        )
        self.assertEqual(
            tuple(atom.weight.fraction for atom in projection.atoms),
            (Fraction(1, 2), Fraction(1, 2)),
        )
        self.assertEqual(projection.abstraction_digest, abstraction.digest)

    def test_source_and_refill_provenance_are_immutable_and_fail_closed(self) -> None:
        self.assertEqual(self.source.digest, ADR0305_CAPACITY_FILLING_SOURCE_SHA256)
        self.assertEqual(
            self.parent_source.digest,
            ADR0300_COLLISION_REPAIR_SOURCE_SHA256,
        )
        with self.assertRaises(FrozenInstanceError):
            self.source.source_id = "mutable"  # type: ignore[misc]
        with self.assertRaisesRegex(ValueError, "differs from ADR-0305"):
            CapacityFillingActionAbstractionSource(source_id="renamed")

        state = two_live_seat_river_opening_state(pot=40, stack=10)
        result = self.source.build(betting=state, decision=state.legal_decision())
        inner = result.legal_abstraction
        rank_one = result.refill_origins[0]
        rank_one_amount = int(rank_one.projected_raise_to)
        rank_one_index = next(
            index
            for index, value in enumerate(inner.raise_sizes)
            if int(value.action.raise_to) == rank_one_amount
        )

        wrong_rank = replace(rank_one, capacity_refill_rank=2)
        wrong_size = replace(
            inner.raise_sizes[rank_one_index],
            origins=(wrong_rank,),
        )
        wrong_sizes = tuple(
            wrong_size if index == rank_one_index else value
            for index, value in enumerate(inner.raise_sizes)
        )
        with self.assertRaisesRegex(ValueError, "ranks"):
            replace(inner, raise_sizes=wrong_sizes)

        assert rank_one.capacity_refill is not None
        wrong_selection = replace(
            rank_one.capacity_refill,
            left_raise_to=rank_one.capacity_refill.left_raise_to + 1,
        )
        wrong_origin = replace(rank_one, capacity_refill=wrong_selection)
        wrong_size = replace(
            inner.raise_sizes[rank_one_index],
            origins=(wrong_origin,),
        )
        wrong_sizes = tuple(
            wrong_size if index == rank_one_index else value
            for index, value in enumerate(inner.raise_sizes)
        )
        with self.assertRaisesRegex(ValueError, "not maximin"):
            replace(inner, raise_sizes=wrong_sizes)

        last_refill = result.refill_origins[-1]
        last_refill_amount = int(last_refill.projected_raise_to)
        missing_size = next(
            value
            for value in inner.raise_sizes
            if int(value.action.raise_to) == last_refill_amount
        )
        with self.assertRaisesRegex(ValueError, "slot unused"):
            replace(
                inner,
                actions=tuple(
                    action for action in inner.actions if action != missing_size.action
                ),
                raise_sizes=tuple(
                    value for value in inner.raise_sizes if value != missing_size
                ),
            )

        wrong_parent = replace(
            inner,
            capacity_filling_parent_source_digest="f" * 64,
        )
        with self.assertRaisesRegex(ValueError, "wrong parent"):
            CapacityFillingActionAbstraction(legal_abstraction=wrong_parent)
        with self.assertRaises(TypeError):
            ExactPotOddsDistance(False, 10)  # type: ignore[arg-type]

        changed = state.apply_action(CHECK)
        with self.assertRaisesRegex(ValueError, "stale"):
            self.source.build(betting=changed, decision=state.legal_decision())
        with self.assertRaisesRegex(TypeError, "exact betting"):
            self.source.build(  # type: ignore[arg-type]
                betting="state",
                decision=state.legal_decision(),
            )

    def test_source_has_no_value_panel_or_integration_import(self) -> None:
        path = _ROOT / "src/pontius/capacity_filling_action_abstraction.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported_modules = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        forbidden = (
            "blueprint",
            "convex",
            "fresh",
            "qualification",
            "replay",
            "resolver",
            "river",
            "sizing",
            "strategy",
        )
        for module in imported_modules:
            self.assertFalse(any(fragment in module for fragment in forbidden), module)


if __name__ == "__main__":
    unittest.main()
