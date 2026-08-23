"""Reduced one-bet river security oracle for candidate bet-size lattices.

The opener observes its private hand and chooses check or one exact integer bet.
The responder observes its own hand and the bet, then chooses fold or call.  A
compact behavioral maximin LP keeps one fold/call lower envelope per responder
information set.  A deliberately separate bounded normal-form teacher checks
the formulation on two-hand/two-bet projections.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from itertools import product
from math import gcd, isfinite

from .linear_program import maximize_linear_program
from .matrix_game import solve_zero_sum_matrix_game
from .no_limit_betting import BettingStreet, NoLimitBettingState
from .reduced_river_sizing_lp import (
    compile_reduced_river_sizing_lp,
    validate_reduced_river_bet_sizes,
)
from .river import Card, HoleCards, evaluate_seven


def _require_integer(value: object, *, label: str, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < (1 if positive else 0):
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{label} must be {qualifier}")
    return value


def _canonical_hand(value: object, *, label: str) -> HoleCards:
    if not isinstance(value, tuple) or len(value) != 2:
        raise TypeError(f"{label} must be an immutable two-card tuple")
    cards = tuple(sorted(value))
    if any(
        isinstance(card, bool) or not isinstance(card, int) or card not in range(52)
        for card in cards
    ):
        raise ValueError(f"{label} contains an invalid card")
    if cards[0] == cards[1]:
        raise ValueError(f"{label} cards must be distinct")
    return cards


def _canonical_board(value: object) -> tuple[Card, ...]:
    if not isinstance(value, tuple) or len(value) != 5:
        raise TypeError("reduced river board must be an immutable five-card tuple")
    if any(
        isinstance(card, bool) or not isinstance(card, int) or card not in range(52)
        for card in value
    ):
        raise ValueError("reduced river board contains an invalid card")
    if len(set(value)) != 5:
        raise ValueError("reduced river board cards must be distinct")
    return value


@dataclass(frozen=True, slots=True)
class ExactDealProbability:
    """One exact joint-deal probability, not a policy or projection weight."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        numerator = _require_integer(self.numerator, label="deal-probability numerator")
        denominator = _require_integer(
            self.denominator,
            label="deal-probability denominator",
            positive=True,
        )
        if numerator > denominator:
            raise ValueError("deal probability must lie in [0, 1]")
        common = gcd(numerator, denominator)
        object.__setattr__(self, "numerator", numerator // common)
        object.__setattr__(self, "denominator", denominator // common)

    @classmethod
    def from_fraction(cls, value: Fraction) -> ExactDealProbability:
        if not isinstance(value, Fraction):
            raise TypeError("deal probability conversion requires an exact fraction")
        return cls(value.numerator, value.denominator)

    @property
    def fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


@dataclass(frozen=True, slots=True)
class ProbabilitySimplexAllowance:
    """Dimensionless post-solve policy-simplex allowance."""

    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, float) or not isfinite(self.value) or self.value <= 0.0:
            raise ValueError("probability-simplex allowance must be a positive finite float")


@dataclass(frozen=True, slots=True)
class ChipObjectiveAllowance:
    """Chip-valued post-solve objective reconstruction allowance."""

    chips: float

    def __post_init__(self) -> None:
        if not isinstance(self.chips, float) or not isfinite(self.chips) or self.chips <= 0.0:
            raise ValueError("chip-objective allowance must be a positive finite float")


@dataclass(frozen=True, slots=True)
class ReducedRiverSizingContext:
    """Exact cards, chips, and joint range for one reduced sizing game."""

    context_id: str
    board: tuple[Card, ...]
    pot: int
    stack: int
    minimum_bet: int
    opener_hands: tuple[HoleCards, ...]
    responder_hands: tuple[HoleCards, ...]
    joint_probabilities: tuple[tuple[ExactDealProbability, ...], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.context_id, str) or not self.context_id.strip():
            raise ValueError("reduced sizing context id must be nonempty")
        board = _canonical_board(self.board)
        pot = _require_integer(self.pot, label="reduced pot", positive=True)
        stack = _require_integer(self.stack, label="reduced stack", positive=True)
        minimum = _require_integer(
            self.minimum_bet,
            label="minimum reduced bet",
            positive=True,
        )
        if pot % 2:
            raise ValueError("reduced zero-sum pot must split into integer half-pot units")
        if minimum > stack:
            raise ValueError("minimum reduced bet exceeds the effective stack")
        if not isinstance(self.opener_hands, tuple) or not self.opener_hands:
            raise TypeError("opener hands must be a nonempty immutable tuple")
        if not isinstance(self.responder_hands, tuple) or not self.responder_hands:
            raise TypeError("responder hands must be a nonempty immutable tuple")
        opener = tuple(
            _canonical_hand(hand, label=f"opener hand {index}")
            for index, hand in enumerate(self.opener_hands)
        )
        responder = tuple(
            _canonical_hand(hand, label=f"responder hand {index}")
            for index, hand in enumerate(self.responder_hands)
        )
        if len(set(opener)) != len(opener) or len(set(responder)) != len(responder):
            raise ValueError("each reduced private-hand axis must be unique")
        board_cards = set(board)
        if any(board_cards & set(hand) for hand in (*opener, *responder)):
            raise ValueError("reduced private hand overlaps the public board")
        for opener_hand in opener:
            for responder_hand in responder:
                if set(opener_hand) & set(responder_hand):
                    raise ValueError("a reduced joint deal contains overlapping private cards")

        if not isinstance(self.joint_probabilities, tuple) or len(self.joint_probabilities) != len(
            opener
        ):
            raise TypeError("joint probabilities must have one immutable row per opener hand")
        if any(
            not isinstance(row, tuple) or len(row) != len(responder)
            for row in self.joint_probabilities
        ):
            raise TypeError("joint-probability rows must match the responder-hand axis")
        if any(
            not isinstance(probability, ExactDealProbability)
            for row in self.joint_probabilities
            for probability in row
        ):
            raise TypeError("joint range contains a nonsemantic deal probability")
        total = sum(
            (probability.fraction for row in self.joint_probabilities for probability in row),
            start=Fraction(0),
        )
        if total != 1:
            raise ValueError("joint deal probabilities must sum exactly to one")
        if any(
            probability.numerator == 0 for row in self.joint_probabilities for probability in row
        ):
            raise ValueError("frozen reduced contexts require positive support on every deal")

        object.__setattr__(self, "board", board)
        object.__setattr__(self, "pot", pot)
        object.__setattr__(self, "stack", stack)
        object.__setattr__(self, "minimum_bet", minimum)
        object.__setattr__(self, "opener_hands", opener)
        object.__setattr__(self, "responder_hands", responder)

    @property
    def payoff_span(self) -> int:
        return self.pot + 2 * self.stack

    @property
    def showdown_signs(self) -> tuple[tuple[int, ...], ...]:
        opener_ranks = tuple(evaluate_seven((*self.board, *hand)) for hand in self.opener_hands)
        responder_ranks = tuple(
            evaluate_seven((*self.board, *hand)) for hand in self.responder_hands
        )
        return tuple(
            tuple((left > right) - (left < right) for right in responder_ranks)
            for left in opener_ranks
        )

    @property
    def digest(self) -> str:
        payload = {
            "board": self.board,
            "context_id": self.context_id,
            "joint_probabilities": tuple(
                tuple((value.numerator, value.denominator) for value in row)
                for row in self.joint_probabilities
            ),
            "minimum_bet": self.minimum_bet,
            "opener_hands": self.opener_hands,
            "pot": self.pot,
            "responder_hands": self.responder_hands,
            "stack": self.stack,
            "version": "reduced-river-sizing-context-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()

    def bounded_two_by_two(self) -> ReducedRiverSizingContext:
        """Return the exact renormalized leading 2x2 projection for a teacher."""

        if len(self.opener_hands) < 2 or len(self.responder_hands) < 2:
            raise ValueError("a two-by-two teacher projection requires two hands per seat")
        raw = tuple(
            tuple(self.joint_probabilities[row][column].fraction for column in range(2))
            for row in range(2)
        )
        total = sum((value for row in raw for value in row), start=Fraction(0))
        normalized = tuple(
            tuple(ExactDealProbability.from_fraction(value / total) for value in row) for row in raw
        )
        return ReducedRiverSizingContext(
            context_id=f"{self.context_id}-leading-2x2",
            board=self.board,
            pot=self.pot,
            stack=self.stack,
            minimum_bet=self.minimum_bet,
            opener_hands=self.opener_hands[:2],
            responder_hands=self.responder_hands[:2],
            joint_probabilities=normalized,
        )


@dataclass(frozen=True, slots=True)
class ReducedRiverSizingSolution:
    context_digest: str
    bet_sizes: tuple[int, ...]
    opening_policy: tuple[tuple[float, ...], ...]
    responder_best_actions: tuple[tuple[str, ...], ...]
    value_chips: float
    reconstructed_value_chips: float
    max_probability_simplex_residual: float
    chip_objective_reconstruction_error: float
    linear_program_duality_gap: float
    linear_program_max_constraint_violation: float
    max_envelope_constraint_violation_chips: float
    simplex_pivots: int


@dataclass(frozen=True, slots=True)
class NormalFormSizingTeacherSolution:
    context_digest: str
    bet_sizes: tuple[int, ...]
    responder_pure_plan_count: int
    opener_pure_plan_count: int
    value_chips: float
    duality_gap: float


def _validate_bet_sizes(
    context: ReducedRiverSizingContext,
    bet_sizes: object,
) -> tuple[int, ...]:
    return validate_reduced_river_bet_sizes(
        minimum_bet=context.minimum_bet,
        stack=context.stack,
        bet_sizes=bet_sizes,
    )


def solve_reduced_river_sizing(
    context: ReducedRiverSizingContext,
    bet_sizes: tuple[int, ...],
    *,
    probability_allowance: ProbabilitySimplexAllowance,
    chip_allowance: ChipObjectiveAllowance,
    solver_tolerance: float = 1e-11,
    max_pivots: int = 100_000,
) -> ReducedRiverSizingSolution:
    """Solve the opener's compact behavioral security-value program."""

    if not isinstance(context, ReducedRiverSizingContext):
        raise TypeError("reduced sizing solve requires a semantic context")
    if not isinstance(probability_allowance, ProbabilitySimplexAllowance):
        raise TypeError("probability residual requires its semantic allowance")
    if not isinstance(chip_allowance, ChipObjectiveAllowance):
        raise TypeError("chip reconstruction requires its semantic allowance")
    if not isinstance(solver_tolerance, float) or not isfinite(solver_tolerance):
        raise ValueError("solver tolerance must be a finite float")
    if solver_tolerance <= 0.0:
        raise ValueError("solver tolerance must be positive")
    if isinstance(max_pivots, bool) or not isinstance(max_pivots, int):
        raise TypeError("reduced sizing maximum pivots must be an integer")
    if max_pivots <= 0:
        raise ValueError("reduced sizing maximum pivots must be positive")
    sizes = _validate_bet_sizes(context, bet_sizes)

    signs = context.showdown_signs
    compiled = compile_reduced_river_sizing_lp(
        pot=context.pot,
        stack=context.stack,
        minimum_bet=context.minimum_bet,
        joint_probabilities=tuple(
            tuple(probability.fraction for probability in row)
            for row in context.joint_probabilities
        ),
        showdown_signs=signs,
        bet_sizes=sizes,
    )
    layout = compiled.layout
    opener_count = layout.opener_count
    responder_count = layout.responder_count
    half_pot = context.pot / 2.0
    maximum_stake = compiled.maximum_stake_chips

    def policy_index(opener: int, action: int) -> int:
        return layout.policy_index(opener, action)

    def envelope_index(responder: int, bet_index: int) -> int:
        return layout.envelope_index(responder, bet_index)

    solved = maximize_linear_program(
        list(compiled.objective),
        [list(row) for row in compiled.coefficients],
        list(compiled.bounds),
        tolerance=solver_tolerance,
        max_pivots=max_pivots,
    )
    policy = tuple(
        tuple(
            solved.variables[policy_index(opener, action)] for action in range(layout.action_count)
        )
        for opener in range(opener_count)
    )
    probability_residual = max(
        max((abs(sum(row) - 1.0) for row in policy), default=0.0),
        max(
            (max(0.0, -value, value - 1.0) for row in policy for value in row),
            default=0.0,
        ),
    )
    if probability_residual > probability_allowance.value:
        raise AssertionError("reduced sizing policy exceeds its probability allowance")

    envelope_constraint_violation = 0.0
    for responder in range(responder_count):
        for bet_index, bet in enumerate(sizes):
            envelope = solved.variables[envelope_index(responder, bet_index)]
            fold_value = 0.0
            call_value = 0.0
            for opener in range(opener_count):
                mass = (
                    float(context.joint_probabilities[opener][responder].fraction)
                    * policy[opener][bet_index + 1]
                )
                fold_value += mass * half_pot
                call_value += mass * signs[opener][responder] * (half_pot + bet)
            envelope_constraint_violation = max(
                envelope_constraint_violation,
                envelope - fold_value - maximum_stake,
                envelope - call_value - maximum_stake,
            )

    reconstructed = 0.0
    for opener in range(opener_count):
        for responder in range(responder_count):
            probability = float(context.joint_probabilities[opener][responder].fraction)
            reconstructed += probability * policy[opener][0] * signs[opener][responder] * half_pot
    best_actions: list[tuple[str, ...]] = []
    for responder in range(responder_count):
        actions: list[str] = []
        for bet_index, bet in enumerate(sizes):
            fold_value = 0.0
            call_value = 0.0
            for opener in range(opener_count):
                mass = (
                    float(context.joint_probabilities[opener][responder].fraction)
                    * policy[opener][bet_index + 1]
                )
                fold_value += mass * half_pot
                call_value += mass * signs[opener][responder] * (half_pot + bet)
            if fold_value <= call_value:
                actions.append("fold")
                reconstructed += fold_value
            else:
                actions.append("call")
                reconstructed += call_value
        best_actions.append(tuple(actions))

    value = solved.objective + compiled.objective_offset_chips
    objective_error = abs(value - reconstructed)
    if objective_error > chip_allowance.chips:
        raise AssertionError("reduced sizing objective exceeds its chip allowance")
    return ReducedRiverSizingSolution(
        context_digest=context.digest,
        bet_sizes=sizes,
        opening_policy=policy,
        responder_best_actions=tuple(best_actions),
        value_chips=value,
        reconstructed_value_chips=reconstructed,
        max_probability_simplex_residual=probability_residual,
        chip_objective_reconstruction_error=objective_error,
        linear_program_duality_gap=solved.duality_gap,
        linear_program_max_constraint_violation=solved.max_constraint_violation,
        max_envelope_constraint_violation_chips=max(
            0.0,
            envelope_constraint_violation,
        ),
        simplex_pivots=solved.pivots,
    )


def solve_bounded_normal_form_sizing_teacher(
    context: ReducedRiverSizingContext,
    bet_sizes: tuple[int, ...],
    *,
    solver_tolerance: float = 1e-11,
) -> NormalFormSizingTeacherSolution:
    """Independently enumerate a bounded complete normal form.

    This intentionally refuses dimensions beyond the preregistered two-hand,
    two-bet control so an accidental production-sized enumeration fails fast.
    """

    if not isinstance(context, ReducedRiverSizingContext):
        raise TypeError("normal-form sizing teacher requires a semantic context")
    sizes = _validate_bet_sizes(context, bet_sizes)
    if len(context.opener_hands) > 2 or len(context.responder_hands) > 2 or len(sizes) > 2:
        raise ValueError("normal-form sizing teacher is bounded to two hands and two bets")
    if not isinstance(solver_tolerance, float) or not isfinite(solver_tolerance):
        raise ValueError("teacher solver tolerance must be a finite float")
    if solver_tolerance <= 0.0:
        raise ValueError("teacher solver tolerance must be positive")

    opener_plans = tuple(product(range(len(sizes) + 1), repeat=len(context.opener_hands)))
    responder_plans = tuple(
        product(
            (0, 1),
            repeat=len(context.responder_hands) * len(sizes),
        )
    )
    half_pot = context.pot / 2.0
    signs = tuple(
        tuple(
            (
                evaluate_seven((*context.board, *opener_hand))
                > evaluate_seven((*context.board, *responder_hand))
            )
            - (
                evaluate_seven((*context.board, *opener_hand))
                < evaluate_seven((*context.board, *responder_hand))
            )
            for responder_hand in context.responder_hands
        )
        for opener_hand in context.opener_hands
    )
    payoffs: list[list[float]] = []
    for responder_plan in responder_plans:
        row: list[float] = []
        for opener_plan in opener_plans:
            value = 0.0
            for opener, action in enumerate(opener_plan):
                for responder in range(len(context.responder_hands)):
                    probability = float(context.joint_probabilities[opener][responder].fraction)
                    if action == 0:
                        utility = signs[opener][responder] * half_pot
                    else:
                        response_index = responder * len(sizes) + action - 1
                        if responder_plan[response_index] == 0:
                            utility = half_pot
                        else:
                            utility = signs[opener][responder] * (half_pot + sizes[action - 1])
                    value += probability * utility
            row.append(value)
        payoffs.append(row)
    solved = solve_zero_sum_matrix_game(
        payoffs,
        tolerance=solver_tolerance,
    )
    return NormalFormSizingTeacherSolution(
        context_digest=context.digest,
        bet_sizes=sizes,
        responder_pure_plan_count=len(responder_plans),
        opener_pure_plan_count=len(opener_plans),
        value_chips=solved.value,
        duality_gap=solved.duality_gap,
    )


def two_live_seat_river_opening_state(*, pot: int, stack: int) -> NoLimitBettingState:
    """Create the exact six-seat shell used only by the reduced sizing gate."""

    pot_value = _require_integer(pot, label="two-seat river pot", positive=True)
    stack_value = _require_integer(stack, label="two-seat river stack", positive=True)
    if pot_value % 2:
        raise ValueError("two-seat river pot must be even")
    contribution = pot_value // 2
    return NoLimitBettingState(
        button=5,
        small_blind=1,
        big_blind=2,
        street=BettingStreet.RIVER,
        starting_stacks=(stack_value + contribution, stack_value + contribution, 2, 2, 2, 2),
        stacks=(stack_value, stack_value, 2, 2, 2, 2),
        total_contributions=(contribution, contribution, 0, 0, 0, 0),
        street_contributions=(0, 0, 0, 0, 0, 0),
        folded=(False, False, True, True, True, True),
        pending_seats=(0, 1),
        last_full_raise_size=2,
        acted_at_bet=(None, None, None, None, None, None),
    )


__all__ = [
    "ChipObjectiveAllowance",
    "ExactDealProbability",
    "NormalFormSizingTeacherSolution",
    "ProbabilitySimplexAllowance",
    "ReducedRiverSizingContext",
    "ReducedRiverSizingSolution",
    "solve_bounded_normal_form_sizing_teacher",
    "solve_reduced_river_sizing",
    "two_live_seat_river_opening_state",
]
