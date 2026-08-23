from __future__ import annotations

import unittest

from test_reduced_river_sizing_oracle import _contexts

from pontius.action_abstraction_confirmation import build_adr0293_confirmation_panel
from pontius.legal_action_abstraction import (
    ImmutableActionAbstractionSource,
    LegalActionAbstraction,
    PotFraction,
)
from pontius.no_limit_betting import BettingActionKind
from pontius.reduced_river_sizing_oracle import (
    ChipObjectiveAllowance,
    ProbabilitySimplexAllowance,
    solve_bounded_normal_form_sizing_teacher,
    solve_reduced_river_sizing,
    two_live_seat_river_opening_state,
)


def _v1_source() -> ImmutableActionAbstractionSource:
    return ImmutableActionAbstractionSource(source_id="adr-0291-reduced-quality-v1")


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


def _bet_sizes(abstraction: LegalActionAbstraction) -> tuple[int, ...]:
    return tuple(
        int(action.raise_to)
        for action in abstraction.actions
        if action.kind is BettingActionKind.RAISE
    )


class DyadicActionAbstractionConfirmationTests(unittest.TestCase):
    def test_open_development_control_fits_but_is_not_confirmation(self) -> None:
        v2_source = _v2_source()
        probability_allowance = ProbabilitySimplexAllowance(1e-9)
        chip_allowance = ChipObjectiveAllowance(1e-9)
        informative: list[tuple[float, float]] = []
        losses: list[float] = []
        for context in _contexts():
            state = two_live_seat_river_opening_state(
                pot=context.pot,
                stack=context.stack,
            )
            abstraction = v2_source.build(
                betting=state,
                decision=state.legal_decision(),
            )
            full, v2, narrow = tuple(
                solve_reduced_river_sizing(
                    context,
                    sizes,
                    probability_allowance=probability_allowance,
                    chip_allowance=chip_allowance,
                )
                for sizes in (
                    tuple(range(context.minimum_bet, context.stack + 1)),
                    _bet_sizes(abstraction),
                    (context.minimum_bet, context.stack),
                )
            )
            gap = full.value_chips - narrow.value_chips
            if gap > 1e-6 * context.payoff_span:
                informative.append((gap, v2.value_chips - narrow.value_chips))
            losses.append(
                max(0.0, full.value_chips - v2.value_chips) / context.payoff_span
            )

        self.assertEqual(len(informative), 1)
        aggregate_gap = sum(gap for gap, _ in informative)
        aggregate_recovered = sum(recovered for _, recovered in informative)
        self.assertGreaterEqual(aggregate_recovered / aggregate_gap + 1e-12, 0.80)
        self.assertLessEqual(max(losses), 0.01)
        self.assertLessEqual(sum(losses) / len(losses), 0.005)

    def test_frozen_confirmation_is_rejected_on_panel_power(self) -> None:
        panel = build_adr0293_confirmation_panel()
        v1_source = _v1_source()
        v2_source = _v2_source()
        probability_allowance = ProbabilitySimplexAllowance(1e-9)
        chip_allowance = ChipObjectiveAllowance(1e-9)
        informative: list[tuple[float, float]] = []
        v2_losses: list[float] = []
        v1_losses: list[float] = []

        for context in panel.contexts:
            state = two_live_seat_river_opening_state(
                pot=context.pot,
                stack=context.stack,
            )
            decision = state.legal_decision()
            v2_abstraction = v2_source.build(betting=state, decision=decision)
            v1_abstraction = v1_source.build(betting=state, decision=decision)

            full_sizes = tuple(range(context.minimum_bet, context.stack + 1))
            v2_sizes = _bet_sizes(v2_abstraction)
            v1_sizes = _bet_sizes(v1_abstraction)
            narrow_sizes = (context.minimum_bet, context.stack)
            full, v2, v1, narrow = tuple(
                solve_reduced_river_sizing(
                    context,
                    sizes,
                    probability_allowance=probability_allowance,
                    chip_allowance=chip_allowance,
                )
                for sizes in (full_sizes, v2_sizes, v1_sizes, narrow_sizes)
            )

            for solution in (full, v2, v1, narrow):
                self.assertLessEqual(solution.max_probability_simplex_residual, 1e-9)
                self.assertLessEqual(solution.chip_objective_reconstruction_error, 1e-9)
            self.assertGreaterEqual(full.value_chips + 1e-9, v2.value_chips)
            self.assertGreaterEqual(v2.value_chips + 1e-9, narrow.value_chips)

            bounded = context.bounded_two_by_two()
            teacher_sizes = (bounded.minimum_bet, bounded.stack)
            compact_teacher_control = solve_reduced_river_sizing(
                bounded,
                teacher_sizes,
                probability_allowance=probability_allowance,
                chip_allowance=chip_allowance,
            )
            normal_form = solve_bounded_normal_form_sizing_teacher(
                bounded,
                teacher_sizes,
            )
            self.assertAlmostEqual(
                compact_teacher_control.value_chips,
                normal_form.value_chips,
                delta=1e-9,
            )
            self.assertLessEqual(normal_form.duality_gap, 1e-9)

            gap = full.value_chips - narrow.value_chips
            if gap > 1e-6 * context.payoff_span:
                informative.append((gap, v2.value_chips - narrow.value_chips))
            v2_losses.append(
                max(0.0, full.value_chips - v2.value_chips) / context.payoff_span
            )
            v1_losses.append(
                max(0.0, full.value_chips - v1.value_chips) / context.payoff_span
            )
            self.assertLessEqual(len(v2_abstraction.actions), 9)
            self.assertLess(len(v2_abstraction.actions), len(full_sizes) + 1)

        self.assertEqual(len(informative), 5)
        aggregate_gap = sum(gap for gap, _ in informative)
        aggregate_recovered = sum(recovered for _, recovered in informative)
        self.assertGreaterEqual(aggregate_recovered / aggregate_gap + 1e-12, 0.80)
        self.assertLessEqual(max(v2_losses), 0.01)
        self.assertLessEqual(sum(v2_losses) / len(v2_losses), 0.005)
        self.assertLessEqual(sum(v2_losses), sum(v1_losses) + 1e-9)
        self.assertFalse(len(informative) >= 8)


if __name__ == "__main__":
    unittest.main()
