from __future__ import annotations

import unittest

from pontius.legal_action_abstraction import ImmutableActionAbstractionSource
from pontius.no_limit_betting import BettingActionKind
from pontius.reduced_river_sizing_oracle import (
    ChipObjectiveAllowance,
    ExactDealProbability,
    ProbabilitySimplexAllowance,
    ReducedRiverSizingContext,
    solve_bounded_normal_form_sizing_teacher,
    solve_reduced_river_sizing,
    two_live_seat_river_opening_state,
)
from pontius.river import make_hole, parse_cards


def _probabilities(
    weights: tuple[tuple[int, ...], ...],
    denominator: int,
) -> tuple[tuple[ExactDealProbability, ...], ...]:
    return tuple(
        tuple(ExactDealProbability(value, denominator) for value in row)
        for row in weights
    )


def _contexts() -> tuple[ReducedRiverSizingContext, ...]:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    opener = (
        make_hole("Ks", "Td"),
        make_hole("As", "Ad"),
        make_hole("4s", "5s"),
    )
    responder = (
        make_hole("Ts", "8s"),
        make_hole("Kh", "Kd"),
        make_hole("Ah", "3h"),
    )
    specifications = (
        ("uniform-pot10-stack20", 10, 20, ((1, 1, 1), (1, 1, 1), (1, 1, 1)), 9),
        ("weighted-pot20-stack20", 20, 20, ((1, 2, 1), (2, 1, 2), (1, 2, 1)), 13),
        ("weighted-pot6-stack20", 6, 20, ((4, 1, 1), (1, 3, 1), (1, 1, 2)), 15),
        ("weighted-pot12-stack12", 12, 12, ((1, 1, 1), (1, 2, 1), (3, 2, 1)), 13),
    )
    return tuple(
        ReducedRiverSizingContext(
            context_id=context_id,
            board=board,
            pot=pot,
            stack=stack,
            minimum_bet=2,
            opener_hands=opener,
            responder_hands=responder,
            joint_probabilities=_probabilities(weights, denominator),
        )
        for context_id, pot, stack, weights, denominator in specifications
    )


class ReducedRiverSizingOracleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contexts = _contexts()
        self.probability_allowance = ProbabilitySimplexAllowance(1e-9)
        self.chip_allowance = ChipObjectiveAllowance(1e-9)

    def test_frozen_cards_create_the_expected_strict_showdown_tiers(self) -> None:
        expected = (
            (1, 1, 1),
            (-1, 1, 1),
            (-1, -1, -1),
        )
        for context in self.contexts:
            self.assertEqual(context.showdown_signs, expected)
            self.assertEqual(context.payoff_span, context.pot + 2 * context.stack)

    def test_compact_lp_matches_independent_bounded_normal_form(self) -> None:
        for context in self.contexts:
            bounded = context.bounded_two_by_two()
            sizes = (bounded.minimum_bet, bounded.stack)
            compact = solve_reduced_river_sizing(
                bounded,
                sizes,
                probability_allowance=self.probability_allowance,
                chip_allowance=self.chip_allowance,
            )
            teacher = solve_bounded_normal_form_sizing_teacher(bounded, sizes)
            self.assertAlmostEqual(compact.value_chips, teacher.value_chips, delta=1e-9)
            self.assertLessEqual(teacher.duality_gap, 1e-9)
            self.assertEqual(teacher.opener_pure_plan_count, 9)
            self.assertEqual(teacher.responder_pure_plan_count, 16)

    def test_preregistered_candidate_lattice_is_rejected_by_frozen_quality_gates(
        self,
    ) -> None:
        source = ImmutableActionAbstractionSource(source_id="adr-0291-reduced-quality-v1")
        normalized_losses: list[float] = []
        positive_gaps: list[tuple[float, float]] = []
        nondegenerate = 0

        for context in self.contexts:
            state = two_live_seat_river_opening_state(
                pot=context.pot,
                stack=context.stack,
            )
            abstraction = source.build(
                betting=state,
                decision=state.legal_decision(),
            )
            candidate_sizes = tuple(
                int(action.raise_to)
                for action in abstraction.actions
                if action.kind is BettingActionKind.RAISE
            )
            full_sizes = tuple(range(context.minimum_bet, context.stack + 1))
            narrow_sizes = (context.minimum_bet, context.stack)
            full = solve_reduced_river_sizing(
                context,
                full_sizes,
                probability_allowance=self.probability_allowance,
                chip_allowance=self.chip_allowance,
            )
            candidate = solve_reduced_river_sizing(
                context,
                candidate_sizes,
                probability_allowance=self.probability_allowance,
                chip_allowance=self.chip_allowance,
            )
            narrow = solve_reduced_river_sizing(
                context,
                narrow_sizes,
                probability_allowance=self.probability_allowance,
                chip_allowance=self.chip_allowance,
            )
            for solution in (full, candidate, narrow):
                self.assertLessEqual(solution.max_probability_simplex_residual, 1e-9)
                self.assertLessEqual(solution.chip_objective_reconstruction_error, 1e-9)
                self.assertLessEqual(
                    solution.max_envelope_constraint_violation_chips,
                    1e-9,
                )
            self.assertGreaterEqual(full.value_chips + 1e-9, candidate.value_chips)
            self.assertGreaterEqual(candidate.value_chips + 1e-9, narrow.value_chips)

            gap = full.value_chips - narrow.value_chips
            if gap > 1e-6 * context.payoff_span:
                nondegenerate += 1
                positive_gaps.append((gap, candidate.value_chips - narrow.value_chips))
            normalized_losses.append(
                max(0.0, full.value_chips - candidate.value_chips) / context.payoff_span
            )
            self.assertLessEqual(len(abstraction.actions), 9)
            if context.stack == 20:
                self.assertLess(len(abstraction.actions), len(full_sizes) + 1)
                self.assertLess(2 * len(abstraction.actions), len(full_sizes) + 1)

        self.assertEqual(nondegenerate, 1)
        aggregate_gap = sum(gap for gap, _ in positive_gaps)
        aggregate_recovered = sum(recovered for _, recovered in positive_gaps)
        recovered_fraction = aggregate_recovered / aggregate_gap
        self.assertAlmostEqual(recovered_fraction, 0.0, delta=1e-9)
        self.assertLessEqual(max(normalized_losses), 0.01)
        self.assertLessEqual(sum(normalized_losses) / len(normalized_losses), 0.005)
        self.assertFalse(nondegenerate >= 2 and recovered_fraction >= 0.80)

    def test_units_and_invalid_contexts_fail_closed(self) -> None:
        context = self.contexts[0]
        with self.assertRaisesRegex(TypeError, "semantic allowance"):
            solve_reduced_river_sizing(
                context,
                (2, 20),
                probability_allowance=self.chip_allowance,  # type: ignore[arg-type]
                chip_allowance=self.chip_allowance,
            )
        with self.assertRaisesRegex(TypeError, "semantic allowance"):
            solve_reduced_river_sizing(
                context,
                (2, 20),
                probability_allowance=self.probability_allowance,
                chip_allowance=self.probability_allowance,  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(ValueError, "increase strictly"):
            solve_reduced_river_sizing(
                context,
                (20, 2),
                probability_allowance=self.probability_allowance,
                chip_allowance=self.chip_allowance,
            )
        with self.assertRaisesRegex(TypeError, "maximum pivots"):
            solve_reduced_river_sizing(
                context,
                (2, 20),
                probability_allowance=self.probability_allowance,
                chip_allowance=self.chip_allowance,
                max_pivots=True,  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(ValueError, "maximum pivots"):
            solve_reduced_river_sizing(
                context,
                (2, 20),
                probability_allowance=self.probability_allowance,
                chip_allowance=self.chip_allowance,
                max_pivots=0,
            )
        with self.assertRaisesRegex(ValueError, "bounded"):
            solve_bounded_normal_form_sizing_teacher(context, (2, 20))
        with self.assertRaisesRegex(ValueError, "sum exactly"):
            ReducedRiverSizingContext(
                context_id="bad-probability",
                board=context.board,
                pot=context.pot,
                stack=context.stack,
                minimum_bet=context.minimum_bet,
                opener_hands=context.opener_hands,
                responder_hands=context.responder_hands,
                joint_probabilities=tuple(
                    tuple(ExactDealProbability(1, 10) for _ in row)
                    for row in context.joint_probabilities
                ),
            )
        with self.assertRaisesRegex(TypeError, "integer"):
            ExactDealProbability(True, 2)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
