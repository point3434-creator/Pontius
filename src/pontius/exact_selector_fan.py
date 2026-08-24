"""Exact one-dimensional normal-fan maps for finite best responses.

Each section is a sequence-form realization segment for one acting player.
Fixed response tapes induce affine values on that segment.  Their optimality
cells are therefore closed rational intervals, ties are exact facets (or
degenerate intervals), and no epsilon is permitted to elect a neighbor.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping, TypeAlias

from .exact_selector_window_oracle import (
    ExactBestResponseTrace,
    exact_best_response_trace,
    exact_fixed_response_trace,
)
from .exact_sequence_form_coefficient_oracle import exact_sequence_axis
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState


ExactPolicy: TypeAlias = Mapping[str, Mapping[Action, Fraction | float]]
ResponseTape: TypeAlias = tuple[tuple[str, Action], ...]


@dataclass(frozen=True, slots=True)
class ExactTapeCell:
    """Closed scale interval on which one total response tape is optimal."""

    response_tape: ResponseTape
    lower: Fraction
    upper: Fraction


@dataclass(frozen=True, slots=True)
class ExactFanSegment:
    """One open interval with constant three-valued selector classifications."""

    lower: Fraction
    upper: Fraction
    witness: Fraction
    response_tape: ResponseTape
    reachable_tape: ResponseTape
    total_state: str
    reachable_state: str
    total_tie_information_sets: tuple[str, ...]
    reachable_tie_information_sets: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExactFanPoint:
    """Exact boundary point, retained separately from interval measure."""

    scale: Fraction
    response_tape: ResponseTape
    reachable_tape: ResponseTape
    total_state: str
    reachable_state: str
    total_tie_information_sets: tuple[str, ...]
    reachable_tie_information_sets: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExactSelectorFanSection:
    """Complete exact map of one target player's BR fan along one direction."""

    acting_player: int
    target_player: int
    source_tape: ResponseTape
    source_cell_upper: Fraction
    legacy_source_breakpoint: Fraction
    cells: tuple[ExactTapeCell, ...]
    segments: tuple[ExactFanSegment, ...]
    points: tuple[ExactFanPoint, ...]
    total_fixed_measure: Fraction
    total_tie_unresolved_measure: Fraction
    total_switched_measure: Fraction
    reachable_fixed_measure: Fraction
    reachable_tie_unresolved_measure: Fraction
    reachable_switched_measure: Fraction
    total_tie_points: tuple[Fraction, ...]
    reachable_tie_points: tuple[Fraction, ...]


def _fraction(value: Fraction | float) -> Fraction:
    if isinstance(value, bool):
        raise TypeError("Boolean is not an exact fan scalar")
    return value if isinstance(value, Fraction) else Fraction.from_float(float(value))


def _row(
    policy: ExactPolicy,
    key: str,
    actions: tuple[Action, ...],
) -> Mapping[Action, Fraction]:
    supplied = policy.get(key)
    if supplied is None:
        probability = Fraction(1, len(actions))
        return MappingProxyType({action: probability for action in actions})
    if set(supplied) - set(actions):
        raise ValueError("exact fan policy contains an unavailable action")
    weights = {
        action: _fraction(supplied.get(action, Fraction(0))) for action in actions
    }
    if any(value < 0 for value in weights.values()):
        raise ValueError("exact fan policy contains a negative probability")
    total = sum(weights.values(), Fraction(0))
    if total <= 0:
        raise ValueError("exact fan policy has zero probability mass")
    return MappingProxyType(
        {action: value / total for action, value in weights.items()}
    )


def _tape(trace: ExactBestResponseTrace) -> ResponseTape:
    return tuple(sorted(trace.selected_actions.items()))


def realization_interpolated_policy(
    game: ExtensiveFormGame,
    source_policy: ExactPolicy,
    endpoint_policy: ExactPolicy,
    *,
    acting_player: int,
    scale: Fraction,
) -> dict[str, dict[Action, Fraction]]:
    """Interpolate one player's exact sequence realization, then behavioralize."""

    if scale < 0 or scale > 1:
        raise ValueError("exact fan scale lies outside [0, 1]")
    axis = exact_sequence_axis(game, acting_player)

    def realization(policy: ExactPolicy) -> dict[tuple[str, Action], Fraction]:
        result: dict[tuple[str, Action], Fraction] = {}
        for information_set in axis.information_sets:
            parent = (
                Fraction(1)
                if information_set.parent is None
                else result[information_set.parent]
            )
            distribution = _row(
                policy,
                information_set.key,
                information_set.actions,
            )
            for action in information_set.actions:
                result[(information_set.key, action)] = (
                    parent * distribution[action]
                )
        return result

    source_realization = realization(source_policy)
    endpoint_realization = realization(endpoint_policy)
    mixed = {
        token: (Fraction(1) - scale) * source_realization[token]
        + scale * endpoint_realization[token]
        for token in axis.variables
    }
    result = {
        key: {action: value for action, value in row.items()}
        for key, row in source_policy.items()
    }
    for information_set in axis.information_sets:
        parent = (
            Fraction(1)
            if information_set.parent is None
            else mixed[information_set.parent]
        )
        if parent == 0:
            distribution = _row(
                source_policy,
                information_set.key,
                information_set.actions,
            )
        else:
            distribution = MappingProxyType(
                {
                    action: mixed[(information_set.key, action)] / parent
                    for action in information_set.actions
                }
            )
            if sum(distribution.values(), Fraction(0)) != 1:
                raise ArithmeticError("exact fan realization violates flow")
        result[information_set.key] = dict(distribution)
    return dict(sorted(result.items()))


def reachable_response_tape(
    game: ExtensiveFormGame,
    policy: ExactPolicy,
    player: int,
    response_tape: Mapping[str, Action],
) -> ResponseTape:
    """Return selected entries reached by positive chance/opponent support."""

    reached: dict[str, Action] = {}

    def walk(state: GameState, positive: bool) -> None:
        if not positive:
            return
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            for action, probability in state.chance_outcomes():
                walk(state.apply_action(action), _fraction(probability) > 0)
            return
        actions = tuple(state.legal_actions())
        key = state.information_state_key(acting)
        if acting == player:
            try:
                selected = response_tape[key]
            except KeyError as exc:
                raise ValueError("reachable response tape is incomplete") from exc
            if selected not in actions:
                raise ValueError("reachable response tape contains an illegal action")
            reached[key] = selected
            walk(state.apply_action(selected), True)
            return
        distribution = _row(policy, key, actions)
        for action, probability in distribution.items():
            walk(state.apply_action(action), probability > 0)

    walk(game.initial_state(), True)
    return tuple(sorted(reached.items()))


def _trace_by_key(
    trace: ExactBestResponseTrace,
) -> dict[str, object]:
    return {row.key: row for row in trace.information_sets}


def _optimal_cell(
    game: ExtensiveFormGame,
    source_policy: ExactPolicy,
    endpoint_policy: ExactPolicy,
    *,
    acting_player: int,
    target_player: int,
    tape: ResponseTape,
) -> ExactTapeCell:
    selected = dict(tape)
    left = exact_fixed_response_trace(game, source_policy, target_player, selected)
    endpoint = realization_interpolated_policy(
        game,
        source_policy,
        endpoint_policy,
        acting_player=acting_player,
        scale=Fraction(1),
    )
    right = exact_fixed_response_trace(game, endpoint, target_player, selected)
    left_rows = _trace_by_key(left)
    right_rows = _trace_by_key(right)
    if set(left_rows) != set(right_rows) or set(left_rows) != set(selected):
        raise ValueError("exact fan fixed-tape schemas differ")
    lower = Fraction(0)
    upper = Fraction(1)
    for key in sorted(left_rows):
        left_row = left_rows[key]
        right_row = right_rows[key]
        if left_row.actions != right_row.actions:  # type: ignore[attr-defined]
            raise ValueError("exact fan action schema changed along a direction")
        left_values = dict(left_row.action_values)  # type: ignore[attr-defined]
        right_values = dict(right_row.action_values)  # type: ignore[attr-defined]
        chosen = selected[key]
        for action in left_row.actions:  # type: ignore[attr-defined]
            if action == chosen:
                continue
            intercept = left_values[chosen] - left_values[action]
            slope = (
                right_values[chosen]
                - right_values[action]
                - intercept
            )
            if slope == 0:
                if intercept < 0:
                    return ExactTapeCell(tape, Fraction(1), Fraction(0))
                continue
            boundary = -intercept / slope
            if slope > 0:
                lower = max(lower, boundary)
            else:
                upper = min(upper, boundary)
    return ExactTapeCell(tape, max(Fraction(0), lower), min(Fraction(1), upper))


def _legacy_source_breakpoint(
    game: ExtensiveFormGame,
    source_policy: ExactPolicy,
    endpoint_policy: ExactPolicy,
    *,
    acting_player: int,
    target_player: int,
    source_tape: ResponseTape,
) -> Fraction:
    """Apply the original margin/closing-slope rule with exact arithmetic."""

    selected = dict(source_tape)
    left = exact_fixed_response_trace(game, source_policy, target_player, selected)
    endpoint = realization_interpolated_policy(
        game,
        source_policy,
        endpoint_policy,
        acting_player=acting_player,
        scale=Fraction(1),
    )
    right = exact_fixed_response_trace(game, endpoint, target_player, selected)
    right_rows = _trace_by_key(right)
    limit = Fraction(1)
    for left_row in left.information_sets:
        right_row = right_rows[left_row.key]
        left_values = dict(left_row.action_values)
        right_values = dict(right_row.action_values)  # type: ignore[attr-defined]
        chosen = selected[left_row.key]
        for action in left_row.actions:
            if action == chosen:
                continue
            margin = left_values[chosen] - left_values[action]
            if margin < 0:
                raise ArithmeticError("legacy exact source selector is not maximal")
            selected_slope = right_values[chosen] - left_values[chosen]
            competitor_slope = right_values[action] - left_values[action]
            closing_slope = competitor_slope - selected_slope
            if closing_slope > 0:
                limit = min(limit, margin / closing_slope)
    return min(Fraction(1), max(Fraction(0), limit))


def _coverage_gap(cells: tuple[ExactTapeCell, ...]) -> tuple[Fraction, Fraction] | None:
    intervals = sorted(
        (cell.lower, cell.upper)
        for cell in cells
        if cell.lower <= cell.upper
    )
    cursor = Fraction(0)
    for lower, upper in intervals:
        if lower > cursor:
            return cursor, lower
        cursor = max(cursor, upper)
    if cursor < 1:
        return cursor, Fraction(1)
    return None


def _tie_keys(trace: ExactBestResponseTrace) -> tuple[str, ...]:
    return tuple(
        row.key for row in trace.information_sets if len(row.maximizing_actions) > 1
    )


def _states(
    trace: ExactBestResponseTrace,
    reachable: ResponseTape,
    source_tape: ResponseTape,
    source_reachable: ResponseTape,
) -> tuple[str, str, tuple[str, ...], tuple[str, ...]]:
    total_ties = _tie_keys(trace)
    reachable_keys = {key for key, _ in reachable}
    reachable_ties = tuple(key for key in total_ties if key in reachable_keys)
    total_state = (
        "tie_unresolved"
        if total_ties
        else ("fixed" if _tape(trace) == source_tape else "switched")
    )
    reachable_state = (
        "tie_unresolved"
        if reachable_ties
        else ("fixed" if reachable == source_reachable else "switched")
    )
    return total_state, reachable_state, total_ties, reachable_ties


def map_exact_selector_fan_section(
    game: ExtensiveFormGame,
    source_policy: ExactPolicy,
    endpoint_policy: ExactPolicy,
    *,
    acting_player: int,
    target_player: int,
    maximum_tapes: int = 256,
) -> ExactSelectorFanSection:
    """Chart every fixed/tied/switched cell along one realization segment."""

    if maximum_tapes <= 0:
        raise ValueError("exact fan tape bound must be positive")
    source_trace = exact_best_response_trace(game, source_policy, target_player)
    source_tape = _tape(source_trace)
    cells_by_tape: dict[ResponseTape, ExactTapeCell] = {}

    def add_at(scale: Fraction) -> None:
        policy = realization_interpolated_policy(
            game,
            source_policy,
            endpoint_policy,
            acting_player=acting_player,
            scale=scale,
        )
        trace = exact_best_response_trace(game, policy, target_player)
        tape = _tape(trace)
        if tape in cells_by_tape:
            return
        if len(cells_by_tape) >= maximum_tapes:
            raise RuntimeError("exact selector fan exceeded its frozen tape bound")
        cell = _optimal_cell(
            game,
            source_policy,
            endpoint_policy,
            acting_player=acting_player,
            target_player=target_player,
            tape=tape,
        )
        if not cell.lower <= scale <= cell.upper:
            raise ArithmeticError("exact selected response lies outside its fan cell")
        cells_by_tape[tape] = cell

    add_at(Fraction(0))
    add_at(Fraction(1))
    while True:
        gap = _coverage_gap(tuple(cells_by_tape.values()))
        if gap is None:
            break
        lower, upper = gap
        if lower == upper:
            add_at(lower)
        else:
            before = len(cells_by_tape)
            add_at((lower + upper) / 2)
            if len(cells_by_tape) == before:
                raise ArithmeticError("exact fan gap did not expose a new tape")

    cells = tuple(
        sorted(
            cells_by_tape.values(),
            key=lambda cell: (cell.lower, cell.upper, repr(cell.response_tape)),
        )
    )
    source_cell = cells_by_tape[source_tape]
    legacy_breakpoint = _legacy_source_breakpoint(
        game,
        source_policy,
        endpoint_policy,
        acting_player=acting_player,
        target_player=target_player,
        source_tape=source_tape,
    )
    if source_cell.upper != legacy_breakpoint:
        raise ArithmeticError("exact fan and legacy breakpoint directions differ")
    boundaries = tuple(
        sorted(
            {
                Fraction(0),
                Fraction(1),
                *(cell.lower for cell in cells),
                *(cell.upper for cell in cells),
            }
        )
    )
    segments: list[ExactFanSegment] = []
    measures_total = {name: Fraction(0) for name in ("fixed", "tie_unresolved", "switched")}
    measures_reachable = dict(measures_total)
    for lower, upper in zip(boundaries, boundaries[1:]):
        if lower == upper:
            continue
        witness = (lower + upper) / 2
        policy = realization_interpolated_policy(
            game,
            source_policy,
            endpoint_policy,
            acting_player=acting_player,
            scale=witness,
        )
        trace = exact_best_response_trace(game, policy, target_player)
        reachable = reachable_response_tape(
            game,
            policy,
            target_player,
            trace.selected_actions,
        )
        source_reachable = reachable_response_tape(
            game,
            policy,
            target_player,
            dict(source_tape),
        )
        total_state, reachable_state, total_ties, reachable_ties = _states(
            trace,
            reachable,
            source_tape,
            source_reachable,
        )
        width = upper - lower
        measures_total[total_state] += width
        measures_reachable[reachable_state] += width
        segments.append(
            ExactFanSegment(
                lower,
                upper,
                witness,
                _tape(trace),
                reachable,
                total_state,
                reachable_state,
                total_ties,
                reachable_ties,
            )
        )

    points: list[ExactFanPoint] = []
    for scale in boundaries:
        policy = realization_interpolated_policy(
            game,
            source_policy,
            endpoint_policy,
            acting_player=acting_player,
            scale=scale,
        )
        trace = exact_best_response_trace(game, policy, target_player)
        reachable = reachable_response_tape(
            game,
            policy,
            target_player,
            trace.selected_actions,
        )
        source_reachable = reachable_response_tape(
            game,
            policy,
            target_player,
            dict(source_tape),
        )
        total_state, reachable_state, total_ties, reachable_ties = _states(
            trace,
            reachable,
            source_tape,
            source_reachable,
        )
        points.append(
            ExactFanPoint(
                scale,
                _tape(trace),
                reachable,
                total_state,
                reachable_state,
                total_ties,
                reachable_ties,
            )
        )

    if sum(measures_total.values(), Fraction(0)) != 1 or sum(
        measures_reachable.values(), Fraction(0)
    ) != 1:
        raise ArithmeticError("exact fan classifications do not partition the section")
    return ExactSelectorFanSection(
        acting_player=acting_player,
        target_player=target_player,
        source_tape=source_tape,
        source_cell_upper=source_cell.upper,
        legacy_source_breakpoint=legacy_breakpoint,
        cells=cells,
        segments=tuple(segments),
        points=tuple(points),
        total_fixed_measure=measures_total["fixed"],
        total_tie_unresolved_measure=measures_total["tie_unresolved"],
        total_switched_measure=measures_total["switched"],
        reachable_fixed_measure=measures_reachable["fixed"],
        reachable_tie_unresolved_measure=measures_reachable["tie_unresolved"],
        reachable_switched_measure=measures_reachable["switched"],
        total_tie_points=tuple(
            point.scale for point in points if point.total_state == "tie_unresolved"
        ),
        reachable_tie_points=tuple(
            point.scale
            for point in points
            if point.reachable_state == "tie_unresolved"
        ),
    )


__all__ = [
    "ExactFanPoint",
    "ExactFanSegment",
    "ExactSelectorFanSection",
    "ExactTapeCell",
    "map_exact_selector_fan_section",
    "reachable_response_tape",
    "realization_interpolated_policy",
]
