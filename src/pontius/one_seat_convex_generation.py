"""Exact one-seat safe improvement by sequence-form row generation.

The online-shaped solver uses one player's sequence-form realization plan and
generates fixed best-response rows on demand.  A deliberately separate normal-
form teacher enumerates both sides for small games.  The teacher is a control,
not a scalable implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from math import isfinite, prod
import time

import numpy as np

from .evaluation import (
    EvaluationResult,
    Policy,
    best_response,
    collect_information_sets,
    expected_utilities,
    policy_distribution,
)
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState
from .linear_program import LinearProgramSolution, maximize_linear_program


SequenceToken = tuple[str, Action]
ResponseSignature = tuple[tuple[str, Action], ...]


def _copy_policy(policy: Policy) -> Policy:
    return {key: dict(distribution) for key, distribution in policy.items()}


def _deterministic_policy(
    information_sets: dict[str, tuple[Action, ...]],
    selected: dict[str, Action],
) -> Policy:
    if set(selected) != set(information_sets):
        raise ValueError("pure response does not cover every information set")
    return {
        key: {
            action: float(action == selected[key])
            for action in information_sets[key]
        }
        for key in information_sets
    }


def _merge_policy(base: Policy, replacement: Policy) -> Policy:
    result = _copy_policy(base)
    result.update(_copy_policy(replacement))
    return result


@dataclass(frozen=True, slots=True)
class _SequenceInformationSet:
    key: str
    actions: tuple[Action, ...]
    parent: SequenceToken | None


@dataclass(frozen=True, slots=True)
class _SequenceAxis:
    player: int
    information_sets: tuple[_SequenceInformationSet, ...]
    variables: tuple[SequenceToken, ...]
    indices: dict[SequenceToken, int] = field(compare=False, repr=False)

    def realization_from_policy(self, policy: Policy) -> tuple[float, ...]:
        values = [0.0] * len(self.variables)
        for information_set in self.information_sets:
            parent_mass = (
                1.0
                if information_set.parent is None
                else values[self.indices[information_set.parent]]
            )
            distribution = policy_distribution(
                policy,
                information_set.key,
                information_set.actions,
            )
            for action in information_set.actions:
                values[self.indices[(information_set.key, action)]] = (
                    parent_mass * distribution[action]
                )
        return tuple(values)

    def behavioral_policy(
        self,
        realization: tuple[float, ...],
        fallback: Policy,
        tolerance: float,
    ) -> Policy:
        if len(realization) != len(self.variables):
            raise ValueError("realization vector has the wrong width")
        result = _copy_policy(fallback)
        for information_set in self.information_sets:
            parent_mass = (
                1.0
                if information_set.parent is None
                else max(0.0, realization[self.indices[information_set.parent]])
            )
            if parent_mass <= tolerance:
                result[information_set.key] = policy_distribution(
                    fallback,
                    information_set.key,
                    information_set.actions,
                )
                continue
            raw = {
                action: max(
                    0.0,
                    realization[self.indices[(information_set.key, action)]],
                )
                / parent_mass
                for action in information_set.actions
            }
            mass = sum(raw.values())
            if mass <= tolerance:
                raise AssertionError("positive parent realization has no child mass")
            result[information_set.key] = {
                action: value / mass for action, value in raw.items()
            }
        return result

    def flow_constraints(self, extra_variables: int) -> tuple[list[list[float]], list[float]]:
        width = len(self.variables) + extra_variables
        rows: list[list[float]] = []
        bounds: list[float] = []
        for information_set in self.information_sets:
            row = [0.0] * width
            for action in information_set.actions:
                row[self.indices[(information_set.key, action)]] = 1.0
            bound = 1.0
            if information_set.parent is not None:
                row[self.indices[information_set.parent]] -= 1.0
                bound = 0.0
            rows.extend((row, [-value for value in row]))
            bounds.extend((bound, -bound))
        return rows, bounds


def _sequence_axis(game: ExtensiveFormGame, player: int) -> _SequenceAxis:
    if player not in range(game.num_players):
        raise ValueError(f"invalid player index {player}")
    schemas: dict[str, tuple[tuple[Action, ...], SequenceToken | None]] = {}

    def walk(state: GameState, parent: SequenceToken | None) -> None:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            for action, _ in state.chance_outcomes():
                walk(state.apply_action(action), parent)
            return
        actions = tuple(state.legal_actions())
        if acting == player:
            key = state.information_state_key(player)
            previous = schemas.setdefault(key, (actions, parent))
            if previous != (actions, parent):
                raise ValueError(
                    f"game violates action consistency or perfect recall at {key!r}"
                )
            for action in actions:
                walk(state.apply_action(action), (key, action))
            return
        for action in actions:
            walk(state.apply_action(action), parent)

    walk(game.initial_state(), None)
    depths: dict[str, int] = {}

    def depth(key: str) -> int:
        cached = depths.get(key)
        if cached is not None:
            return cached
        parent = schemas[key][1]
        value = 0 if parent is None else depth(parent[0]) + 1
        depths[key] = value
        return value

    information_sets = tuple(
        _SequenceInformationSet(key, schemas[key][0], schemas[key][1])
        for key in sorted(schemas, key=lambda candidate: (depth(candidate), candidate))
    )
    variables = tuple(
        (information_set.key, action)
        for information_set in information_sets
        for action in information_set.actions
    )
    return _SequenceAxis(
        player=player,
        information_sets=information_sets,
        variables=variables,
        indices={token: index for index, token in enumerate(variables)},
    )


@dataclass(frozen=True, slots=True)
class AffinePayoff:
    """An exact ``constant + coefficients @ realization`` payoff row."""

    constant: float
    coefficients: tuple[float, ...]

    def value(self, realization: tuple[float, ...]) -> float:
        return self.constant + sum(
            coefficient * value
            for coefficient, value in zip(
                self.coefficients,
                realization,
                strict=True,
            )
        )

    def subtract(self, other: AffinePayoff) -> AffinePayoff:
        return AffinePayoff(
            self.constant - other.constant,
            tuple(
                left - right
                for left, right in zip(
                    self.coefficients,
                    other.coefficients,
                    strict=True,
                )
            ),
        )


def open_axis_payoff_coefficients(
    game: ExtensiveFormGame,
    fixed_policy: Policy,
    *,
    acting_player: int,
    payoff_player: int,
) -> AffinePayoff:
    """Contract a fixed profile while leaving one sequence-form axis open."""

    if payoff_player not in range(game.num_players):
        raise ValueError(f"invalid payoff player {payoff_player}")
    axis = _sequence_axis(game, acting_player)
    coefficients = [0.0] * len(axis.variables)
    constant = 0.0

    def walk(
        state: GameState,
        fixed_reach: float,
        last_sequence: SequenceToken | None,
    ) -> None:
        nonlocal constant
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            contribution = fixed_reach * state.returns()[payoff_player]
            if last_sequence is None:
                constant += contribution
            else:
                coefficients[axis.indices[last_sequence]] += contribution
            return
        if acting == CHANCE_PLAYER:
            for action, probability in state.chance_outcomes():
                walk(
                    state.apply_action(action),
                    fixed_reach * probability,
                    last_sequence,
                )
            return
        actions = tuple(state.legal_actions())
        if acting == acting_player:
            key = state.information_state_key(acting_player)
            for action in actions:
                token = (key, action)
                if token not in axis.indices:
                    raise AssertionError("open-axis traversal found an unknown sequence")
                walk(state.apply_action(action), fixed_reach, token)
            return
        key = state.information_state_key(acting)
        distribution = policy_distribution(fixed_policy, key, actions)
        for action, probability in distribution.items():
            walk(
                state.apply_action(action),
                fixed_reach * probability,
                last_sequence,
            )

    walk(game.initial_state(), 1.0, None)
    return AffinePayoff(constant, tuple(coefficients))


@dataclass(frozen=True, slots=True)
class _ResponseRow:
    target_player: int
    signature: ResponseSignature
    gain: AffinePayoff


@dataclass(frozen=True, slots=True)
class RowConditioning:
    rows: int
    numerical_rank: int
    minimum_normalized_separation: float | None
    effective_condition_number: float | None


def _row_conditioning(rows: tuple[_ResponseRow, ...], tolerance: float) -> RowConditioning:
    if not rows:
        return RowConditioning(0, 0, None, None)
    raw = np.asarray(
        [[row.gain.constant, *row.gain.coefficients] for row in rows],
        dtype=np.float64,
    )
    norms = np.linalg.norm(raw, axis=1)
    normalized = raw.copy()
    for index, norm in enumerate(norms):
        if norm > tolerance:
            normalized[index] /= norm
    minimum: float | None = None
    for left in range(len(rows)):
        for right in range(left + 1, len(rows)):
            distance = float(np.linalg.norm(normalized[left] - normalized[right]))
            minimum = distance if minimum is None else min(minimum, distance)
    singular = np.linalg.svd(normalized, compute_uv=False)
    threshold = tolerance * max(normalized.shape) * max(float(singular[0]), 1.0)
    nonzero = singular[singular > threshold]
    condition = None if len(nonzero) == 0 else float(nonzero[0] / nonzero[-1])
    return RowConditioning(
        rows=len(rows),
        numerical_rank=len(nonzero),
        minimum_normalized_separation=minimum,
        effective_condition_number=condition,
    )


def _evaluate_with_response_tapes(
    game: ExtensiveFormGame,
    policy: Policy,
) -> tuple[EvaluationResult, tuple[ResponseSignature, ...]]:
    utilities = expected_utilities(game, policy)
    response_values = []
    signatures = []
    for player in range(game.num_players):
        value, selected = best_response(game, policy, player)
        response_values.append(value)
        signatures.append(tuple(sorted(selected.items())))
    gains = tuple(
        max(0.0, response - utility)
        for response, utility in zip(response_values, utilities, strict=True)
    )
    evaluation = EvaluationResult(
        utilities=utilities,
        best_response_values=tuple(response_values),
        deviation_gains=gains,
        nash_conv=sum(gains),
        exploitability=(sum(gains) / 2.0 if game.num_players == 2 else None),
    )
    return evaluation, tuple(signatures)


def _response_row(
    game: ExtensiveFormGame,
    blueprint: Policy,
    axis: _SequenceAxis,
    profile_payoffs: tuple[AffinePayoff, ...],
    target_player: int,
    signature: ResponseSignature,
) -> _ResponseRow:
    if target_player == axis.player:
        response_value, selected = best_response(game, blueprint, target_player)
        actual_signature = tuple(sorted(selected.items()))
        if actual_signature != signature:
            raise ValueError("acting-seat invariant row has the wrong response tape")
        profile = profile_payoffs[target_player]
        return _ResponseRow(
            target_player,
            signature,
            AffinePayoff(
                response_value - profile.constant,
                tuple(-value for value in profile.coefficients),
            ),
        )
    information_sets = collect_information_sets(game, target_player)
    selected = dict(signature)
    response_policy = _deterministic_policy(information_sets, selected)
    fixed = _merge_policy(blueprint, response_policy)
    response_payoff = open_axis_payoff_coefficients(
        game,
        fixed,
        acting_player=axis.player,
        payoff_player=target_player,
    )
    return _ResponseRow(
        target_player,
        signature,
        response_payoff.subtract(profile_payoffs[target_player]),
    )


def _master(
    axis: _SequenceAxis,
    rows_by_player: tuple[dict[ResponseSignature, _ResponseRow], ...],
    caps: tuple[float, ...],
    tolerance: float,
) -> tuple[LinearProgramSolution, tuple[float, ...], tuple[float, ...]]:
    players = len(caps)
    sequence_width = len(axis.variables)
    width = sequence_width + players
    rows, bounds = axis.flow_constraints(players)
    for player, cap in enumerate(caps):
        row = [0.0] * width
        row[sequence_width + player] = 1.0
        rows.append(row)
        bounds.append(cap)
    for player_rows in rows_by_player:
        for response in player_rows.values():
            row = [*response.gain.coefficients, *([0.0] * players)]
            row[sequence_width + response.target_player] = -1.0
            rows.append(row)
            bounds.append(-response.gain.constant)
    objective = [0.0] * sequence_width + [-1.0] * players
    solution = maximize_linear_program(
        objective,
        rows,
        bounds,
        tolerance=tolerance,
    )
    return (
        solution,
        tuple(solution.variables[:sequence_width]),
        tuple(solution.variables[sequence_width:]),
    )


@dataclass(frozen=True, slots=True)
class OneSeatGenerationIteration:
    iteration: int
    response_rows_before: int
    response_rows_added: int
    added_targets: tuple[int, ...]
    master_lower_bound: float
    incumbent_upper_bound: float
    optimality_gap: float
    candidate_nash_conv: float
    candidate_feasible: bool
    incumbent_updated: bool
    maximum_cap_violation: float
    maximum_epigraph_violation: float
    realization_equivalence_max_error: float
    master_solve_seconds: float
    exact_oracle_seconds: float
    cut_extraction_seconds: float
    converged: bool


@dataclass(frozen=True, slots=True)
class OneSeatGenerationResult:
    policy: Policy = field(compare=False, repr=False)
    acting_player: int
    guard: float
    baseline_nash_conv: float
    caps: tuple[float, ...]
    converged: bool
    lower_bound: float
    upper_bound: float
    optimality_gap: float
    iterations: tuple[OneSeatGenerationIteration, ...]
    response_rows_by_player: tuple[int, ...]
    conditioning_by_player: tuple[RowConditioning, ...]
    exact_duplicate_response_hits: int


def solve_one_seat_with_row_generation(
    game: ExtensiveFormGame,
    blueprint: Policy,
    *,
    acting_player: int,
    guard: float,
    max_iterations: int = 100,
    tolerance: float = 1e-10,
) -> OneSeatGenerationResult:
    """Minimize NashConv over one seat under per-seat blueprint-relative caps."""

    if acting_player not in range(game.num_players):
        raise ValueError(f"invalid acting player {acting_player}")
    if not isfinite(guard) or guard < 0.0:
        raise ValueError("guard must be finite and nonnegative")
    if max_iterations <= 0:
        raise ValueError("max_iterations must be positive")
    if not isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")

    baseline, baseline_signatures = _evaluate_with_response_tapes(game, blueprint)
    caps = tuple(gain + guard for gain in baseline.deviation_gains)
    axis = _sequence_axis(game, acting_player)
    profile_payoffs = tuple(
        open_axis_payoff_coefficients(
            game,
            blueprint,
            acting_player=acting_player,
            payoff_player=player,
        )
        for player in range(game.num_players)
    )
    blueprint_realization = axis.realization_from_policy(blueprint)
    for player, payoff in enumerate(profile_payoffs):
        error = abs(payoff.value(blueprint_realization) - baseline.utilities[player])
        if error > 100.0 * tolerance:
            raise AssertionError("open-axis profile coefficient identity failed")

    rows_by_player: tuple[dict[ResponseSignature, _ResponseRow], ...] = tuple(
        {} for _ in range(game.num_players)
    )
    for player, signature in enumerate(baseline_signatures):
        row = _response_row(
            game,
            blueprint,
            axis,
            profile_payoffs,
            player,
            signature,
        )
        rows_by_player[player][signature] = row

    incumbent_policy = _copy_policy(blueprint)
    incumbent_upper_bound = baseline.nash_conv
    lower_bound = 0.0
    updates: list[OneSeatGenerationIteration] = []
    duplicate_hits = 0
    converged = False

    for iteration in range(1, max_iterations + 1):
        rows_before = sum(len(rows) for rows in rows_by_player)
        master_start = time.perf_counter()
        solution, realization, epigraph = _master(
            axis,
            rows_by_player,
            caps,
            tolerance,
        )
        master_seconds = time.perf_counter() - master_start
        # Added exact rows can only tighten the restricted master.  Preserve the
        # strongest already-verified bound across sub-ulp simplex variation.
        lower_bound = max(lower_bound, 0.0, -solution.objective)
        candidate = axis.behavioral_policy(realization, blueprint, tolerance)

        oracle_start = time.perf_counter()
        evaluation, signatures = _evaluate_with_response_tapes(game, candidate)
        oracle_seconds = time.perf_counter() - oracle_start
        cap_violations = tuple(
            gain - cap
            for gain, cap in zip(evaluation.deviation_gains, caps, strict=True)
        )
        maximum_cap_violation = max(cap_violations, default=0.0)
        candidate_feasible = maximum_cap_violation <= 100.0 * tolerance
        incumbent_updated = False
        if (
            candidate_feasible
            and evaluation.nash_conv < incumbent_upper_bound - tolerance
        ):
            incumbent_policy = _copy_policy(candidate)
            incumbent_upper_bound = evaluation.nash_conv
            incumbent_updated = True

        equivalence_error = 0.0
        for player, payoff in enumerate(profile_payoffs):
            equivalence_error = max(
                equivalence_error,
                abs(payoff.value(realization) - evaluation.utilities[player]),
            )
        for player_rows in rows_by_player:
            for response in player_rows.values():
                fixed = _merge_policy(
                    candidate,
                    _deterministic_policy(
                        collect_information_sets(game, response.target_player),
                        dict(response.signature),
                    ),
                )
                if response.target_player == acting_player:
                    response_value = baseline.best_response_values[acting_player]
                else:
                    response_value = expected_utilities(game, fixed)[
                        response.target_player
                    ]
                exact_gain = response_value - evaluation.utilities[
                    response.target_player
                ]
                equivalence_error = max(
                    equivalence_error,
                    abs(response.gain.value(realization) - exact_gain),
                )
        if equivalence_error > 100.0 * tolerance:
            raise AssertionError("sequence-form realization equivalence failed")

        epigraph_violations = tuple(
            gain - epigraph[player]
            for player, gain in enumerate(evaluation.deviation_gains)
        )
        maximum_epigraph_violation = max(epigraph_violations, default=0.0)
        added_targets: list[int] = []
        extraction_start = time.perf_counter()
        for player, violation in enumerate(epigraph_violations):
            if violation <= 100.0 * tolerance:
                continue
            signature = signatures[player]
            if signature in rows_by_player[player]:
                duplicate_hits += 1
                raise AssertionError(
                    "active exact response row remains epigraph-violated"
                )
            row = _response_row(
                game,
                blueprint,
                axis,
                profile_payoffs,
                player,
                signature,
            )
            rows_by_player[player][signature] = row
            added_targets.append(player)
        extraction_seconds = time.perf_counter() - extraction_start

        converged = maximum_epigraph_violation <= 100.0 * tolerance
        gap = incumbent_upper_bound - lower_bound
        allowed = 100.0 * tolerance * max(1.0, abs(incumbent_upper_bound))
        if gap < -allowed:
            raise AssertionError("restricted-master lower bound exceeds safe incumbent")
        gap = max(0.0, gap)
        updates.append(
            OneSeatGenerationIteration(
                iteration=iteration,
                response_rows_before=rows_before,
                response_rows_added=len(added_targets),
                added_targets=tuple(added_targets),
                master_lower_bound=lower_bound,
                incumbent_upper_bound=incumbent_upper_bound,
                optimality_gap=gap,
                candidate_nash_conv=evaluation.nash_conv,
                candidate_feasible=candidate_feasible,
                incumbent_updated=incumbent_updated,
                maximum_cap_violation=max(0.0, maximum_cap_violation),
                maximum_epigraph_violation=max(0.0, maximum_epigraph_violation),
                realization_equivalence_max_error=equivalence_error,
                master_solve_seconds=master_seconds,
                exact_oracle_seconds=oracle_seconds,
                cut_extraction_seconds=extraction_seconds,
                converged=converged,
            )
        )
        if converged:
            if not candidate_feasible:
                raise AssertionError("epigraph-complete candidate violates a cap")
            if evaluation.nash_conv < incumbent_upper_bound + tolerance:
                incumbent_policy = _copy_policy(candidate)
                incumbent_upper_bound = evaluation.nash_conv
            break
        if not added_targets:
            raise AssertionError("epigraph violation produced no exact cut")

    final_gap = max(0.0, incumbent_upper_bound - lower_bound)
    conditioning = tuple(
        _row_conditioning(tuple(rows.values()), tolerance)
        for rows in rows_by_player
    )
    return OneSeatGenerationResult(
        policy=incumbent_policy,
        acting_player=acting_player,
        guard=guard,
        baseline_nash_conv=baseline.nash_conv,
        caps=caps,
        converged=converged,
        lower_bound=lower_bound,
        upper_bound=incumbent_upper_bound,
        optimality_gap=final_gap,
        iterations=tuple(updates),
        response_rows_by_player=tuple(len(rows) for rows in rows_by_player),
        conditioning_by_player=conditioning,
        exact_duplicate_response_hits=duplicate_hits,
    )


@dataclass(frozen=True, slots=True)
class CompleteTeacherResult:
    policy: Policy = field(compare=False, repr=False)
    objective: float
    exact_nash_conv: float
    acting_pure_plans: int
    response_pure_plans: tuple[int, ...]
    simplex_pivots: int
    maximum_exact_error: float


def _pure_plans(
    game: ExtensiveFormGame,
    player: int,
    max_pure_plans: int,
) -> tuple[tuple[ResponseSignature, Policy], ...]:
    information_sets = collect_information_sets(game, player)
    count = prod(len(actions) for actions in information_sets.values())
    if count > max_pure_plans:
        raise ValueError(
            f"player {player} has {count} pure plans; limit is {max_pure_plans}"
        )
    keys = tuple(information_sets)
    spaces = tuple(information_sets[key] for key in keys)
    plans = []
    for selected_actions in product(*spaces):
        selected = dict(zip(keys, selected_actions, strict=True))
        signature = tuple(sorted(selected.items()))
        plans.append((signature, _deterministic_policy(information_sets, selected)))
    return tuple(plans)


def solve_one_seat_complete_normal_form_teacher(
    game: ExtensiveFormGame,
    blueprint: Policy,
    *,
    acting_player: int,
    guard: float,
    max_pure_plans: int = 100_000,
    tolerance: float = 1e-10,
) -> CompleteTeacherResult:
    """Solve the complete finite teacher without open-axis coefficients."""

    if not isfinite(guard) or guard < 0.0:
        raise ValueError("guard must be finite and nonnegative")
    baseline, _ = _evaluate_with_response_tapes(game, blueprint)
    caps = tuple(gain + guard for gain in baseline.deviation_gains)
    acting_plans = _pure_plans(game, acting_player, max_pure_plans)
    opponent_plans = tuple(
        (() if player == acting_player else _pure_plans(game, player, max_pure_plans))
        for player in range(game.num_players)
    )
    columns = len(acting_plans)
    players = game.num_players
    width = columns + players
    profile_utilities: list[tuple[float, ...]] = []
    acting_profiles: list[Policy] = []
    for _, acting_policy in acting_plans:
        profile = _merge_policy(blueprint, acting_policy)
        acting_profiles.append(profile)
        profile_utilities.append(expected_utilities(game, profile))

    probability = [1.0] * columns + [0.0] * players
    coefficients = [probability, [-value for value in probability]]
    bounds = [1.0, -1.0]
    for player, cap in enumerate(caps):
        row = [0.0] * width
        row[columns + player] = 1.0
        coefficients.append(row)
        bounds.append(cap)

    own_br = baseline.best_response_values[acting_player]
    own_row = [
        own_br - utilities[acting_player]
        for utilities in profile_utilities
    ] + [0.0] * players
    own_row[columns + acting_player] = -1.0
    coefficients.append(own_row)
    bounds.append(0.0)

    for player in range(players):
        if player == acting_player:
            continue
        for _, response_policy in opponent_plans[player]:
            row = []
            for profile, utilities in zip(
                acting_profiles,
                profile_utilities,
                strict=True,
            ):
                fixed = _merge_policy(profile, response_policy)
                response_utility = expected_utilities(game, fixed)[player]
                row.append(response_utility - utilities[player])
            row.extend([0.0] * players)
            row[columns + player] = -1.0
            coefficients.append(row)
            bounds.append(0.0)

    objective = [0.0] * columns + [-1.0] * players
    solution = maximize_linear_program(
        objective,
        coefficients,
        bounds,
        tolerance=tolerance,
    )
    weights = solution.variables[:columns]
    axis = _sequence_axis(game, acting_player)
    realization = [0.0] * len(axis.variables)
    for weight, (_, pure_policy) in zip(weights, acting_plans, strict=True):
        pure_realization = axis.realization_from_policy(pure_policy)
        for index, value in enumerate(pure_realization):
            realization[index] += weight * value
    policy = axis.behavioral_policy(tuple(realization), blueprint, tolerance)
    evaluation, _ = _evaluate_with_response_tapes(game, policy)
    objective_value = max(0.0, -solution.objective)
    error = abs(evaluation.nash_conv - objective_value)
    if error > 100.0 * tolerance:
        raise AssertionError("complete normal-form teacher fails exact evaluation")
    if any(
        gain > cap + 100.0 * tolerance
        for gain, cap in zip(evaluation.deviation_gains, caps, strict=True)
    ):
        raise AssertionError("complete normal-form teacher violates a cap")
    return CompleteTeacherResult(
        policy=policy,
        objective=objective_value,
        exact_nash_conv=evaluation.nash_conv,
        acting_pure_plans=len(acting_plans),
        response_pure_plans=tuple(
            0 if player == acting_player else len(opponent_plans[player])
            for player in range(players)
        ),
        simplex_pivots=solution.pivots,
        maximum_exact_error=error,
    )


@dataclass(frozen=True, slots=True)
class PathSingleVisitReport:
    passed: bool
    repeated_player: int | None
    witness_actions: tuple[Action, ...]


def path_single_visit_report(game: ExtensiveFormGame) -> PathSingleVisitReport:
    """Check the sufficient topology gate for behavioral-coordinate affinity."""

    failure: tuple[int, tuple[Action, ...]] | None = None

    def walk(
        state: GameState,
        seen_players: frozenset[int],
        actions_taken: tuple[Action, ...],
    ) -> None:
        nonlocal failure
        if failure is not None:
            return
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            for action, _ in state.chance_outcomes():
                walk(state.apply_action(action), seen_players, actions_taken + (action,))
            return
        if acting in seen_players:
            failure = (acting, actions_taken)
            return
        updated = seen_players | {acting}
        for action in state.legal_actions():
            walk(state.apply_action(action), updated, actions_taken + (action,))

    walk(game.initial_state(), frozenset(), ())
    return PathSingleVisitReport(
        passed=failure is None,
        repeated_player=None if failure is None else failure[0],
        witness_actions=() if failure is None else failure[1],
    )


def require_behavioral_affine_shortcut(game: ExtensiveFormGame) -> None:
    """Fail closed unless behavioral probabilities are pathwise first degree."""

    report = path_single_visit_report(game)
    if not report.passed:
        raise ValueError(
            "behavioral affine shortcut requires at most one decision per player "
            f"on every path; player {report.repeated_player} repeats"
        )


def compiled_layout_path_single_visit_report(layout: object) -> PathSingleVisitReport:
    """Apply the behavioral-affinity topology gate to an already-compiled layout."""

    nodes = getattr(layout, "nodes", None)
    if not isinstance(nodes, tuple) or not nodes:
        raise ValueError("compiled layout must expose a nonempty node tuple")
    failure: tuple[int, tuple[Action, ...]] | None = None

    def walk(node_index: int, seen_players: frozenset[int]) -> None:
        nonlocal failure
        if failure is not None:
            return
        if node_index not in range(len(nodes)):
            raise ValueError("compiled layout contains an invalid child index")
        node = nodes[node_index]
        player = getattr(node, "player", None)
        children = getattr(node, "children", None)
        history = getattr(node, "history", None)
        if not isinstance(player, int) or not isinstance(children, tuple):
            raise ValueError("compiled layout node schema is invalid")
        if player == TERMINAL_PLAYER:
            if children:
                raise ValueError("compiled terminal layout node has children")
            return
        if player < 0:
            raise ValueError("compiled public layout contains a nonterminal sentinel")
        if player in seen_players:
            witness = (
                tuple(action for _, action in history)
                if isinstance(history, tuple)
                else ()
            )
            failure = (player, witness)
            return
        updated = seen_players | {player}
        for child in children:
            if not isinstance(child, int):
                raise ValueError("compiled layout child index is not an integer")
            walk(child, updated)

    walk(0, frozenset())
    return PathSingleVisitReport(
        passed=failure is None,
        repeated_player=None if failure is None else failure[0],
        witness_actions=() if failure is None else failure[1],
    )


def require_compiled_behavioral_affine_shortcut(layout: object) -> None:
    """Fail closed on a compiled public layout with any repeated acting seat."""

    report = compiled_layout_path_single_visit_report(layout)
    if not report.passed:
        raise ValueError(
            "behavioral affine shortcut requires at most one decision per player "
            f"on every compiled public path; player {report.repeated_player} repeats"
        )


def retreat_one_seat_policy(
    game: ExtensiveFormGame,
    blueprint: Policy,
    candidate: Policy,
    *,
    acting_player: int,
    factor: float,
    tolerance: float = 1e-10,
) -> Policy:
    """Convexly retreat a one-seat realization plan toward its blueprint."""

    if not isfinite(factor) or not 0.0 <= factor <= 1.0:
        raise ValueError("retreat factor must lie in [0, 1]")
    if not isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")
    axis = _sequence_axis(game, acting_player)
    source = axis.realization_from_policy(blueprint)
    endpoint = axis.realization_from_policy(candidate)
    realization = tuple(
        (1.0 - factor) * left + factor * right
        for left, right in zip(source, endpoint, strict=True)
    )
    return axis.behavioral_policy(realization, blueprint, tolerance)
