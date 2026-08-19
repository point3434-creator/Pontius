"""Exact normal-form max-margin oracle for two-player Kuhn subgames."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from itertools import product
from math import isfinite, prod

from .continual import PublicHistory, public_belief, public_histories
from .evaluation import (
    Policy,
    best_response,
    collect_information_sets,
    expected_utilities,
    expected_utilities_from_state,
    policy_distribution,
)
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState
from .kuhn import KuhnPoker
from .linear_program import maximize_linear_program
from .matrix_game import MatrixGameSolution, solve_zero_sum_matrix_game
from .safe_resolving import (
    CounterfactualFrontier,
    CounterfactualSubgameGame,
    ZeroCounterfactualReachError,
    build_counterfactual_frontier,
    counterfactual_best_response_values,
)


@dataclass(frozen=True, slots=True)
class _EnumeratedPlan:
    actions: tuple[tuple[str, Action], ...]
    legal_actions: tuple[tuple[str, tuple[Action, ...]], ...]

    @property
    def action_map(self) -> dict[str, Action]:
        return dict(self.actions)

    @property
    def policy(self) -> Policy:
        selected = self.action_map
        return {
            key: {action: float(action == selected[key]) for action in actions}
            for key, actions in self.legal_actions
        }


@dataclass(frozen=True, slots=True)
class MaxMarginFrontierRecord:
    key: str
    blueprint_cbr_value: float
    candidate_cbr_value: float
    margin: float
    positive_violation: float


@dataclass(frozen=True, slots=True)
class MaxMarginOracleResult:
    """Exact max-min frontier strategy and independent verification metrics."""

    policy: Policy = field(compare=False, repr=False)
    frontier: CounterfactualFrontier
    frontier_records: tuple[MaxMarginFrontierRecord, ...]
    max_margin: float
    verified_min_margin: float
    total_positive_frontier_violation: float
    resolver_information_sets: int
    opponent_information_sets: int
    resolver_pure_plans: int
    opponent_pure_plans: int
    response_constraints: int
    unique_response_constraints: int
    resolver_support_size: int
    matrix_duality_gap: float
    realization_equivalence_max_error: float
    simplex_pivots: int
    matrix_build_seconds: float
    matrix_solve_seconds: float
    policy_conversion_seconds: float

    @property
    def oracle_seconds(self) -> float:
        return (
            self.matrix_build_seconds
            + self.matrix_solve_seconds
            + self.policy_conversion_seconds
        )


@dataclass(frozen=True, slots=True)
class MaxMarginPublicResolveRecord:
    history: PublicHistory
    resolver_player: int
    public_reach_probability: float
    opponent_counterfactual_reach: float
    frontier_information_sets: int
    resolver_information_sets: int
    max_margin: float
    total_positive_frontier_violation: float
    oracle_seconds: float
    resolver_pure_plans: int
    opponent_pure_plans: int
    unique_response_constraints: int
    resolver_support_size: int


@dataclass(frozen=True, slots=True)
class MaxMarginContinualResolveResult:
    policy: Policy = field(compare=False, repr=False)
    records: tuple[MaxMarginPublicResolveRecord, ...]
    structural_public_histories: int
    searched_public_histories: int
    skipped_zero_counterfactual_reach_histories: tuple[PublicHistory, ...]
    total_oracle_seconds: float
    expected_oracle_seconds_per_hand: float
    expected_public_decisions_per_hand: float
    cumulative_exploitability_increase_bound: float
    reach_weighted_max_margin: float


@dataclass(frozen=True, slots=True)
class ConstrainedOracleResult:
    """Safe frontier strategy under a declared secondary LP objective."""

    policy: Policy = field(compare=False, repr=False)
    frontier: CounterfactualFrontier
    frontier_records: tuple[MaxMarginFrontierRecord, ...]
    objective_name: str
    objective_value: float
    verified_objective_value: float
    full_game_target_used: bool
    verified_min_margin: float
    verified_sum_margin: float
    total_positive_frontier_violation: float
    resolver_pure_plans: int
    opponent_pure_plans: int
    response_constraints: int
    unique_response_constraints: int
    objective_response_constraints: int
    resolver_support_size: int
    simplex_pivots: int
    max_constraint_violation: float
    realization_equivalence_max_error: float
    blueprint_opponent_best_response_value: float | None
    candidate_opponent_best_response_value: float | None
    problem_build_seconds: float
    solve_seconds: float
    policy_conversion_seconds: float

    @property
    def oracle_seconds(self) -> float:
        return (
            self.problem_build_seconds
            + self.solve_seconds
            + self.policy_conversion_seconds
        )


@dataclass(frozen=True, slots=True)
class ConstrainedPublicResolveRecord:
    history: PublicHistory
    resolver_player: int
    public_reach_probability: float
    opponent_counterfactual_reach: float
    frontier_information_sets: int
    objective_name: str
    objective_value: float
    verified_objective_value: float
    verified_min_margin: float
    verified_sum_margin: float
    total_positive_frontier_violation: float
    oracle_seconds: float
    resolver_pure_plans: int
    opponent_pure_plans: int
    response_constraints: int
    objective_response_constraints: int
    resolver_support_size: int


@dataclass(frozen=True, slots=True)
class ConstrainedContinualResolveResult:
    policy: Policy = field(compare=False, repr=False)
    objective_name: str
    full_game_target_used: bool
    records: tuple[ConstrainedPublicResolveRecord, ...]
    structural_public_histories: int
    searched_public_histories: int
    skipped_zero_counterfactual_reach_histories: tuple[PublicHistory, ...]
    total_oracle_seconds: float
    expected_oracle_seconds_per_hand: float
    expected_public_decisions_per_hand: float
    cumulative_exploitability_increase_bound: float
    total_verified_objective_value: float
    reach_weighted_objective_value: float


@dataclass(frozen=True, slots=True)
class _ResponseConstraint:
    frontier_key: str
    opponent_plan: _EnumeratedPlan = field(compare=False, repr=False)
    margins_by_resolver_plan: tuple[float, ...]


def _enumerate_plans(
    game: ExtensiveFormGame,
    player: int,
    max_pure_plans: int,
) -> tuple[_EnumeratedPlan, ...]:
    information_sets = collect_information_sets(game, player)
    count = prod(len(actions) for actions in information_sets.values())
    if count > max_pure_plans:
        raise ValueError(
            f"player {player} requires {count} pure plans; "
            f"limit is {max_pure_plans}"
        )
    keys = tuple(information_sets)
    legal = tuple((key, information_sets[key]) for key in keys)
    return tuple(
        _EnumeratedPlan(
            actions=tuple(zip(keys, selected, strict=True)),
            legal_actions=legal,
        )
        for selected in product(*(information_sets[key] for key in keys))
    )


def _deterministic_value(
    state: GameState,
    player: int,
    actions: dict[str, Action],
) -> float:
    acting = state.current_player
    if acting == TERMINAL_PLAYER:
        return state.returns()[player]
    if acting == CHANCE_PLAYER:
        return sum(
            probability
            * _deterministic_value(state.apply_action(action), player, actions)
            for action, probability in state.chance_outcomes()
        )
    key = state.information_state_key(acting)
    return _deterministic_value(state.apply_action(actions[key]), player, actions)


def _frontier_values_for_pure_profile(
    frontier: CounterfactualFrontier,
    resolver_plan: _EnumeratedPlan,
    opponent_plan: _EnumeratedPlan,
) -> dict[str, float]:
    actions = resolver_plan.action_map
    overlap = set(actions) & set(opponent_plan.action_map)
    if overlap:
        raise ValueError(f"information-set keys are shared by players: {overlap!r}")
    actions.update(opponent_plan.action_map)
    values: dict[str, float] = {}
    for root in frontier.roots:
        continuation = _deterministic_value(
            root.state,
            frontier.opponent_player,
            actions,
        )
        key = root.opponent_augmented_key
        values[key] = values.get(key, 0.0) + (
            root.counterfactual_reach * continuation
        )
    return values


def _reachable_resolver_information_sets(
    game: ExtensiveFormGame,
    resolver_player: int,
    plan: _EnumeratedPlan,
) -> frozenset[str]:
    selected = plan.action_map
    reached: set[str] = set()

    def walk(state: GameState) -> None:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            for action, _ in state.chance_outcomes():
                walk(state.apply_action(action))
            return
        actions = tuple(state.legal_actions())
        if acting == resolver_player:
            key = state.information_state_key(acting)
            reached.add(key)
            walk(state.apply_action(selected[key]))
            return
        for action in actions:
            walk(state.apply_action(action))

    walk(game.initial_state())
    return frozenset(reached)


def _mixture_to_behavioral_policy(
    game: ExtensiveFormGame,
    resolver_player: int,
    plans: tuple[_EnumeratedPlan, ...],
    weights: tuple[float, ...],
    fallback: Policy,
    tolerance: float,
) -> Policy:
    information_sets = collect_information_sets(game, resolver_player)
    reachable = tuple(
        _reachable_resolver_information_sets(game, resolver_player, plan)
        for plan in plans
    )
    result: Policy = {key: dict(distribution) for key, distribution in fallback.items()}
    for key, actions in information_sets.items():
        mass = sum(
            weight
            for weight, plan_reach in zip(weights, reachable, strict=True)
            if key in plan_reach
        )
        if mass <= tolerance:
            result[key] = policy_distribution(fallback, key, actions)
            continue
        action_mass = {action: 0.0 for action in actions}
        for weight, plan, plan_reach in zip(
            weights,
            plans,
            reachable,
            strict=True,
        ):
            if key in plan_reach:
                action_mass[plan.action_map[key]] += weight
        result[key] = {
            action: action_mass[action] / mass for action in actions
        }
    return result


def _build_constraints(
    frontier: CounterfactualFrontier,
    resolver_plans: tuple[_EnumeratedPlan, ...],
    opponent_plans: tuple[_EnumeratedPlan, ...],
) -> tuple[_ResponseConstraint, ...]:
    blueprint_values = frontier.blueprint_values
    rows: list[_ResponseConstraint] = []
    for opponent_plan in opponent_plans:
        values_by_resolver = [
            _frontier_values_for_pure_profile(
                frontier,
                resolver_plan,
                opponent_plan,
            )
            for resolver_plan in resolver_plans
        ]
        for entry in frontier.entries:
            rows.append(
                _ResponseConstraint(
                    frontier_key=entry.key,
                    opponent_plan=opponent_plan,
                    margins_by_resolver_plan=tuple(
                        blueprint_values[entry.key] - values[entry.key]
                        for values in values_by_resolver
                    ),
                )
            )
    return tuple(rows)


def _deduplicate_constraints(
    constraints: tuple[_ResponseConstraint, ...],
) -> tuple[_ResponseConstraint, ...]:
    unique: dict[tuple[float, ...], _ResponseConstraint] = {}
    for constraint in constraints:
        unique.setdefault(constraint.margins_by_resolver_plan, constraint)
    return tuple(unique.values())


def _deduplicate_entry_constraints(
    constraints: tuple[_ResponseConstraint, ...],
) -> tuple[_ResponseConstraint, ...]:
    unique: dict[tuple[str, tuple[float, ...]], _ResponseConstraint] = {}
    for constraint in constraints:
        unique.setdefault(
            (constraint.frontier_key, constraint.margins_by_resolver_plan),
            constraint,
        )
    return tuple(unique.values())


def _verify_realization_equivalence(
    frontier: CounterfactualFrontier,
    constraints: tuple[_ResponseConstraint, ...],
    weights: tuple[float, ...],
    behavioral_policy: Policy,
) -> float:
    max_error = 0.0
    blueprint_values = frontier.blueprint_values
    cached_values: dict[tuple[tuple[str, Action], ...], dict[str, float]] = {}
    for constraint in constraints:
        opponent_plan = constraint.opponent_plan
        values = cached_values.get(opponent_plan.actions)
        if values is None:
            profile = {
                key: dict(distribution)
                for key, distribution in behavioral_policy.items()
            }
            profile.update(opponent_plan.policy)
            values = {}
            for root in frontier.roots:
                continuation = expected_utilities_from_state(
                    2,
                    root.state,
                    profile,
                )[frontier.opponent_player]
                key = root.opponent_augmented_key
                values[key] = values.get(key, 0.0) + (
                    root.counterfactual_reach * continuation
                )
            cached_values[opponent_plan.actions] = values
        normal_margin = sum(
            weight * margin
            for weight, margin in zip(
                weights,
                constraint.margins_by_resolver_plan,
                strict=True,
            )
        )
        behavioral_margin = (
            blueprint_values[constraint.frontier_key]
            - values[constraint.frontier_key]
        )
        max_error = max(max_error, abs(normal_margin - behavioral_margin))
    return max_error


def _frontier_records(
    frontier: CounterfactualFrontier,
    policy: Policy,
) -> tuple[MaxMarginFrontierRecord, ...]:
    candidate_values = counterfactual_best_response_values(frontier, policy)
    return tuple(
        MaxMarginFrontierRecord(
            key=entry.key,
            blueprint_cbr_value=entry.blueprint_cbr_value,
            candidate_cbr_value=candidate_values[entry.key],
            margin=entry.blueprint_cbr_value - candidate_values[entry.key],
            positive_violation=max(
                0.0,
                candidate_values[entry.key] - entry.blueprint_cbr_value,
            ),
        )
        for entry in frontier.entries
    )


def _simplex_constraints(
    resolver_plans: int,
    extra_variables: int,
) -> tuple[list[list[float]], list[float]]:
    width = resolver_plans + extra_variables
    coefficients: list[list[float]] = []
    bounds: list[float] = []
    probability_sum = [0.0] * width
    for plan in range(resolver_plans):
        probability_sum[plan] = 1.0
    coefficients.append(probability_sum)
    bounds.append(1.0)
    coefficients.append([-value for value in probability_sum])
    bounds.append(-1.0)
    return coefficients, bounds


def _normalize_plan_weights(
    weights: tuple[float, ...],
    tolerance: float,
) -> tuple[float, ...]:
    mass = sum(weights)
    if mass <= tolerance:
        raise AssertionError("oracle returned zero resolver strategy mass")
    return tuple(max(0.0, weight) / mass for weight in weights)


def _build_frontier_problem(
    game: KuhnPoker,
    blueprint: Policy,
    history: PublicHistory,
    resolver_player: int,
    max_pure_plans: int,
) -> tuple[
    CounterfactualFrontier,
    CounterfactualSubgameGame,
    tuple[_EnumeratedPlan, ...],
    tuple[_EnumeratedPlan, ...],
    tuple[_ResponseConstraint, ...],
]:
    frontier = build_counterfactual_frontier(
        game,
        blueprint,
        history,
        resolver_player,
    )
    subgame = CounterfactualSubgameGame(
        frontier.roots,
        frontier.total_counterfactual_reach,
    )
    resolver_plans = _enumerate_plans(
        subgame,
        resolver_player,
        max_pure_plans,
    )
    opponent_plans = _enumerate_plans(
        subgame,
        frontier.opponent_player,
        max_pure_plans,
    )
    constraints = _build_constraints(frontier, resolver_plans, opponent_plans)
    return frontier, subgame, resolver_plans, opponent_plans, constraints


def _validate_oracle_arguments(
    max_pure_plans: int,
    tolerance: float,
) -> None:
    if max_pure_plans <= 0:
        raise ValueError("max_pure_plans must be positive")
    if not isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")


def _verified_oracle_policy(
    subgame: CounterfactualSubgameGame,
    resolver_player: int,
    resolver_plans: tuple[_EnumeratedPlan, ...],
    raw_weights: tuple[float, ...],
    blueprint: Policy,
    frontier: CounterfactualFrontier,
    constraints: tuple[_ResponseConstraint, ...],
    tolerance: float,
) -> tuple[
    tuple[float, ...],
    Policy,
    tuple[MaxMarginFrontierRecord, ...],
    float,
]:
    weights = _normalize_plan_weights(raw_weights, tolerance)
    policy = _mixture_to_behavioral_policy(
        subgame,
        resolver_player,
        resolver_plans,
        weights,
        blueprint,
        tolerance,
    )
    equivalence_error = _verify_realization_equivalence(
        frontier,
        constraints,
        weights,
        policy,
    )
    return weights, policy, _frontier_records(frontier, policy), equivalence_error


def solve_safe_sum_margin_subgame(
    game: KuhnPoker,
    blueprint: Policy,
    history: PublicHistory,
    resolver_player: int,
    *,
    max_pure_plans: int = 1_000_000,
    tolerance: float = 1e-10,
) -> ConstrainedOracleResult:
    """Maximize summed per-frontier worst-case margins subject to safety.

    A nonnegative auxiliary margin is assigned to each opponent augmented
    information set.  Every pure opponent continuation constrains that margin,
    so maximizing their sum remains target-free and frontier safe.
    """

    _validate_oracle_arguments(max_pure_plans, tolerance)
    build_start = time.perf_counter()
    (
        frontier,
        subgame,
        resolver_plans,
        opponent_plans,
        constraints,
    ) = _build_frontier_problem(
        game,
        blueprint,
        history,
        resolver_player,
        max_pure_plans,
    )
    unique_constraints = _deduplicate_entry_constraints(constraints)
    entry_indices = {
        entry.key: index for index, entry in enumerate(frontier.entries)
    }
    plan_count = len(resolver_plans)
    entry_count = len(frontier.entries)
    coefficients, bounds = _simplex_constraints(plan_count, entry_count)
    for constraint in unique_constraints:
        row = [-margin for margin in constraint.margins_by_resolver_plan]
        row.extend([0.0] * entry_count)
        row[plan_count + entry_indices[constraint.frontier_key]] = 1.0
        coefficients.append(row)
        bounds.append(0.0)
    objective = [0.0] * plan_count + [1.0] * entry_count
    problem_build_seconds = time.perf_counter() - build_start

    solve_start = time.perf_counter()
    solution = maximize_linear_program(
        objective,
        coefficients,
        bounds,
        tolerance=min(tolerance / 10.0, 1e-11),
    )
    solve_seconds = time.perf_counter() - solve_start

    conversion_start = time.perf_counter()
    weights, policy, records, equivalence_error = _verified_oracle_policy(
        subgame,
        resolver_player,
        resolver_plans,
        solution.variables[:plan_count],
        blueprint,
        frontier,
        constraints,
        tolerance,
    )
    verified_min_margin = min(record.margin for record in records)
    verified_sum_margin = sum(record.margin for record in records)
    total_violation = sum(record.positive_violation for record in records)
    policy_conversion_seconds = time.perf_counter() - conversion_start

    scale = max(
        1.0,
        max(abs(record.blueprint_cbr_value) for record in records),
    )
    allowed = 100.0 * tolerance * scale
    if verified_min_margin < -allowed or total_violation > allowed:
        raise AssertionError("sum-margin oracle returned an unsafe policy")
    if abs(verified_sum_margin - solution.objective) > allowed:
        raise AssertionError(
            "verified frontier improvement disagrees with LP objective: "
            f"{verified_sum_margin} versus {solution.objective}"
        )
    if equivalence_error > allowed:
        raise AssertionError(
            f"mixed-to-behavioral realization error {equivalence_error}"
        )

    return ConstrainedOracleResult(
        policy=policy,
        frontier=frontier,
        frontier_records=records,
        objective_name="sum_frontier_margin",
        objective_value=solution.objective,
        verified_objective_value=verified_sum_margin,
        full_game_target_used=False,
        verified_min_margin=verified_min_margin,
        verified_sum_margin=verified_sum_margin,
        total_positive_frontier_violation=total_violation,
        resolver_pure_plans=plan_count,
        opponent_pure_plans=len(opponent_plans),
        response_constraints=len(constraints),
        unique_response_constraints=len(unique_constraints),
        objective_response_constraints=0,
        resolver_support_size=sum(weight > tolerance for weight in weights),
        simplex_pivots=solution.pivots,
        max_constraint_violation=solution.max_constraint_violation,
        realization_equivalence_max_error=equivalence_error,
        blueprint_opponent_best_response_value=None,
        candidate_opponent_best_response_value=None,
        problem_build_seconds=problem_build_seconds,
        solve_seconds=solve_seconds,
        policy_conversion_seconds=policy_conversion_seconds,
    )


def solve_safe_best_response_subgame(
    game: KuhnPoker,
    blueprint: Policy,
    history: PublicHistory,
    resolver_player: int,
    *,
    max_pure_plans: int = 1_000_000,
    tolerance: float = 1e-10,
) -> ConstrainedOracleResult:
    """Maximize full-game opponent-BR reduction under frontier safety.

    This oracle deliberately uses a hidden full-game target.  It is a ceiling
    for measurement and objective diagnosis, not a candidate online resolver.
    """

    _validate_oracle_arguments(max_pure_plans, tolerance)
    build_start = time.perf_counter()
    (
        frontier,
        subgame,
        resolver_plans,
        opponent_plans,
        constraints,
    ) = _build_frontier_problem(
        game,
        blueprint,
        history,
        resolver_player,
        max_pure_plans,
    )
    unique_constraints = _deduplicate_entry_constraints(constraints)
    full_opponent_plans = _enumerate_plans(
        game,
        frontier.opponent_player,
        max_pure_plans,
    )
    blueprint_best_response = best_response(
        game,
        blueprint,
        frontier.opponent_player,
    )[0]
    plan_count = len(resolver_plans)
    coefficients, bounds = _simplex_constraints(plan_count, 1)

    for constraint in unique_constraints:
        coefficients.append(
            [-margin for margin in constraint.margins_by_resolver_plan] + [0.0]
        )
        bounds.append(0.0)

    full_response_rows: dict[tuple[float, ...], list[float]] = {}
    for opponent_plan in full_opponent_plans:
        payoffs: list[float] = []
        for resolver_plan in resolver_plans:
            profile = {
                key: dict(distribution)
                for key, distribution in blueprint.items()
            }
            profile.update(resolver_plan.policy)
            profile.update(opponent_plan.policy)
            payoffs.append(
                expected_utilities(game, profile)[frontier.opponent_player]
            )
        full_response_rows.setdefault(tuple(payoffs), payoffs)
    for payoffs in full_response_rows.values():
        coefficients.append(payoffs + [1.0])
        bounds.append(blueprint_best_response)
    objective = [0.0] * plan_count + [1.0]
    problem_build_seconds = time.perf_counter() - build_start

    solve_start = time.perf_counter()
    solution = maximize_linear_program(
        objective,
        coefficients,
        bounds,
        tolerance=min(tolerance / 10.0, 1e-11),
    )
    solve_seconds = time.perf_counter() - solve_start

    conversion_start = time.perf_counter()
    weights, policy, records, equivalence_error = _verified_oracle_policy(
        subgame,
        resolver_player,
        resolver_plans,
        solution.variables[:plan_count],
        blueprint,
        frontier,
        constraints,
        tolerance,
    )
    full_game_equivalence_error = 0.0
    for opponent_plan in full_opponent_plans:
        pure_payoffs: list[float] = []
        for resolver_plan in resolver_plans:
            profile = {
                key: dict(distribution)
                for key, distribution in blueprint.items()
            }
            profile.update(resolver_plan.policy)
            profile.update(opponent_plan.policy)
            pure_payoffs.append(
                expected_utilities(game, profile)[frontier.opponent_player]
            )
        normal_value = sum(
            weight * payoff
            for weight, payoff in zip(weights, pure_payoffs, strict=True)
        )
        behavioral_profile = {
            key: dict(distribution) for key, distribution in policy.items()
        }
        behavioral_profile.update(opponent_plan.policy)
        behavioral_value = expected_utilities(
            game,
            behavioral_profile,
        )[frontier.opponent_player]
        full_game_equivalence_error = max(
            full_game_equivalence_error,
            abs(normal_value - behavioral_value),
        )
    equivalence_error = max(equivalence_error, full_game_equivalence_error)
    candidate_best_response = best_response(
        game,
        policy,
        frontier.opponent_player,
    )[0]
    verified_gain = blueprint_best_response - candidate_best_response
    verified_min_margin = min(record.margin for record in records)
    verified_sum_margin = sum(record.margin for record in records)
    total_violation = sum(record.positive_violation for record in records)
    policy_conversion_seconds = time.perf_counter() - conversion_start

    scale = max(1.0, abs(blueprint_best_response))
    allowed = 100.0 * tolerance * scale
    if verified_min_margin < -allowed or total_violation > allowed:
        raise AssertionError("best-response oracle returned an unsafe policy")
    if abs(verified_gain - solution.objective) > allowed:
        raise AssertionError(
            "verified best-response reduction disagrees with LP objective: "
            f"{verified_gain} versus {solution.objective}"
        )
    if equivalence_error > allowed:
        raise AssertionError(
            f"mixed-to-behavioral realization error {equivalence_error}"
        )

    return ConstrainedOracleResult(
        policy=policy,
        frontier=frontier,
        frontier_records=records,
        objective_name="full_game_opponent_br_reduction",
        objective_value=solution.objective,
        verified_objective_value=verified_gain,
        full_game_target_used=True,
        verified_min_margin=verified_min_margin,
        verified_sum_margin=verified_sum_margin,
        total_positive_frontier_violation=total_violation,
        resolver_pure_plans=plan_count,
        opponent_pure_plans=len(opponent_plans),
        response_constraints=len(constraints),
        unique_response_constraints=len(unique_constraints),
        objective_response_constraints=len(full_response_rows),
        resolver_support_size=sum(weight > tolerance for weight in weights),
        simplex_pivots=solution.pivots,
        max_constraint_violation=solution.max_constraint_violation,
        realization_equivalence_max_error=equivalence_error,
        blueprint_opponent_best_response_value=blueprint_best_response,
        candidate_opponent_best_response_value=candidate_best_response,
        problem_build_seconds=problem_build_seconds,
        solve_seconds=solve_seconds,
        policy_conversion_seconds=policy_conversion_seconds,
    )


def _resolve_all_public_histories_constrained(
    game: KuhnPoker,
    blueprint: Policy,
    objective: str,
    *,
    max_pure_plans: int,
    tolerance: float,
) -> ConstrainedContinualResolveResult:
    if game.num_players != 2:
        raise ValueError("constrained continual resolving requires two players")
    solvers = {
        "sum_frontier_margin": solve_safe_sum_margin_subgame,
        "full_game_opponent_br_reduction": solve_safe_best_response_subgame,
    }
    try:
        solver = solvers[objective]
    except KeyError as error:
        raise ValueError(f"unknown constrained objective {objective!r}") from error

    composed: Policy = {
        key: dict(distribution) for key, distribution in blueprint.items()
    }
    histories = public_histories(game)
    records: list[ConstrainedPublicResolveRecord] = []
    skipped: list[PublicHistory] = []
    full_game_target_used: bool | None = None
    for history in histories:
        belief = public_belief(game, composed, history)
        public_reach = 0.0 if belief is None else belief.public_reach_probability
        if belief is None:
            structural = public_belief(game, {}, history)
            if structural is None:
                raise AssertionError("uniform policy cannot reach a legal history")
            resolver_player = structural.acting_player
        else:
            resolver_player = belief.acting_player
        try:
            result = solver(
                game,
                composed,
                history,
                resolver_player,
                max_pure_plans=max_pure_plans,
                tolerance=tolerance,
            )
        except ZeroCounterfactualReachError:
            skipped.append(history)
            continue
        if full_game_target_used is None:
            full_game_target_used = result.full_game_target_used
        elif full_game_target_used != result.full_game_target_used:
            raise AssertionError("constrained objective changed target semantics")
        records.append(
            ConstrainedPublicResolveRecord(
                history=history,
                resolver_player=resolver_player,
                public_reach_probability=public_reach,
                opponent_counterfactual_reach=(
                    result.frontier.total_counterfactual_reach
                ),
                frontier_information_sets=len(result.frontier.entries),
                objective_name=result.objective_name,
                objective_value=result.objective_value,
                verified_objective_value=result.verified_objective_value,
                verified_min_margin=result.verified_min_margin,
                verified_sum_margin=result.verified_sum_margin,
                total_positive_frontier_violation=(
                    result.total_positive_frontier_violation
                ),
                oracle_seconds=result.oracle_seconds,
                resolver_pure_plans=result.resolver_pure_plans,
                opponent_pure_plans=result.opponent_pure_plans,
                response_constraints=result.response_constraints,
                objective_response_constraints=(
                    result.objective_response_constraints
                ),
                resolver_support_size=result.resolver_support_size,
            )
        )
        composed = result.policy

    if full_game_target_used is None:
        full_game_target_used = objective == "full_game_opponent_br_reduction"
    return ConstrainedContinualResolveResult(
        policy=composed,
        objective_name=objective,
        full_game_target_used=full_game_target_used,
        records=tuple(records),
        structural_public_histories=len(histories),
        searched_public_histories=len(records),
        skipped_zero_counterfactual_reach_histories=tuple(skipped),
        total_oracle_seconds=sum(record.oracle_seconds for record in records),
        expected_oracle_seconds_per_hand=sum(
            record.public_reach_probability * record.oracle_seconds
            for record in records
        ),
        expected_public_decisions_per_hand=sum(
            record.public_reach_probability for record in records
        ),
        cumulative_exploitability_increase_bound=sum(
            record.total_positive_frontier_violation / 2.0
            for record in records
        ),
        total_verified_objective_value=sum(
            record.verified_objective_value for record in records
        ),
        reach_weighted_objective_value=sum(
            record.public_reach_probability * record.verified_objective_value
            for record in records
        ),
    )


def resolve_all_public_histories_sum_margin(
    game: KuhnPoker,
    blueprint: Policy,
    *,
    max_pure_plans: int = 1_000_000,
    tolerance: float = 1e-10,
) -> ConstrainedContinualResolveResult:
    """Compose target-free safe sum-margin replacements root-forward."""

    return _resolve_all_public_histories_constrained(
        game,
        blueprint,
        "sum_frontier_margin",
        max_pure_plans=max_pure_plans,
        tolerance=tolerance,
    )


def resolve_all_public_histories_best_response(
    game: KuhnPoker,
    blueprint: Policy,
    *,
    max_pure_plans: int = 1_000_000,
    tolerance: float = 1e-10,
) -> ConstrainedContinualResolveResult:
    """Compose hidden-target safe best-response-optimal replacements."""

    return _resolve_all_public_histories_constrained(
        game,
        blueprint,
        "full_game_opponent_br_reduction",
        max_pure_plans=max_pure_plans,
        tolerance=tolerance,
    )


def solve_maxmargin_subgame(
    game: KuhnPoker,
    blueprint: Policy,
    history: PublicHistory,
    resolver_player: int,
    *,
    max_pure_plans: int = 1_000_000,
    tolerance: float = 1e-10,
) -> MaxMarginOracleResult:
    """Maximize the minimum blueprint-minus-candidate opponent CBR margin."""

    if max_pure_plans <= 0:
        raise ValueError("max_pure_plans must be positive")
    if not isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")

    build_start = time.perf_counter()
    frontier = build_counterfactual_frontier(
        game,
        blueprint,
        history,
        resolver_player,
    )
    subgame = CounterfactualSubgameGame(
        frontier.roots,
        frontier.total_counterfactual_reach,
    )
    resolver_plans = _enumerate_plans(
        subgame,
        resolver_player,
        max_pure_plans,
    )
    opponent_plans = _enumerate_plans(
        subgame,
        frontier.opponent_player,
        max_pure_plans,
    )
    constraints = _build_constraints(frontier, resolver_plans, opponent_plans)
    unique_constraints = _deduplicate_constraints(constraints)
    matrix_build_seconds = time.perf_counter() - build_start

    solve_start = time.perf_counter()
    matrix_solution: MatrixGameSolution = solve_zero_sum_matrix_game(
        tuple(
            constraint.margins_by_resolver_plan
            for constraint in unique_constraints
        ),
        tolerance=min(tolerance / 10.0, 1e-11),
    )
    matrix_solve_seconds = time.perf_counter() - solve_start

    conversion_start = time.perf_counter()
    policy = _mixture_to_behavioral_policy(
        subgame,
        resolver_player,
        resolver_plans,
        matrix_solution.column_strategy,
        blueprint,
        tolerance,
    )
    equivalence_error = _verify_realization_equivalence(
        frontier,
        constraints,
        matrix_solution.column_strategy,
        policy,
    )
    candidate_values = counterfactual_best_response_values(frontier, policy)
    frontier_records = tuple(
        MaxMarginFrontierRecord(
            key=entry.key,
            blueprint_cbr_value=entry.blueprint_cbr_value,
            candidate_cbr_value=candidate_values[entry.key],
            margin=entry.blueprint_cbr_value - candidate_values[entry.key],
            positive_violation=max(
                0.0,
                candidate_values[entry.key] - entry.blueprint_cbr_value,
            ),
        )
        for entry in frontier.entries
    )
    verified_min_margin = min(record.margin for record in frontier_records)
    total_violation = sum(record.positive_violation for record in frontier_records)
    policy_conversion_seconds = time.perf_counter() - conversion_start

    scale = max(
        1.0,
        max(abs(record.blueprint_cbr_value) for record in frontier_records),
    )
    allowed = 100.0 * tolerance * scale
    if matrix_solution.value < -allowed:
        raise AssertionError("blueprint-feasible max-margin value is negative")
    if abs(verified_min_margin - matrix_solution.value) > allowed:
        raise AssertionError(
            "behavioral policy margin disagrees with normal-form oracle: "
            f"{verified_min_margin} versus {matrix_solution.value}"
        )
    if equivalence_error > allowed:
        raise AssertionError(
            f"mixed-to-behavioral realization error {equivalence_error}"
        )

    return MaxMarginOracleResult(
        policy=policy,
        frontier=frontier,
        frontier_records=frontier_records,
        max_margin=matrix_solution.value,
        verified_min_margin=verified_min_margin,
        total_positive_frontier_violation=total_violation,
        resolver_information_sets=len(
            collect_information_sets(subgame, resolver_player)
        ),
        opponent_information_sets=len(
            collect_information_sets(subgame, frontier.opponent_player)
        ),
        resolver_pure_plans=len(resolver_plans),
        opponent_pure_plans=len(opponent_plans),
        response_constraints=len(constraints),
        unique_response_constraints=len(unique_constraints),
        resolver_support_size=sum(
            weight > tolerance for weight in matrix_solution.column_strategy
        ),
        matrix_duality_gap=matrix_solution.duality_gap,
        realization_equivalence_max_error=equivalence_error,
        simplex_pivots=matrix_solution.simplex_pivots,
        matrix_build_seconds=matrix_build_seconds,
        matrix_solve_seconds=matrix_solve_seconds,
        policy_conversion_seconds=policy_conversion_seconds,
    )


def resolve_all_public_histories_maxmargin(
    game: KuhnPoker,
    blueprint: Policy,
    *,
    max_pure_plans: int = 1_000_000,
    tolerance: float = 1e-10,
) -> MaxMarginContinualResolveResult:
    """Compose exact max-margin replacements from public roots downward."""

    if game.num_players != 2:
        raise ValueError("max-margin continual resolving requires two players")
    composed: Policy = {
        key: dict(distribution) for key, distribution in blueprint.items()
    }
    histories = public_histories(game)
    records: list[MaxMarginPublicResolveRecord] = []
    skipped: list[PublicHistory] = []
    for history in histories:
        belief = public_belief(game, composed, history)
        public_reach = 0.0 if belief is None else belief.public_reach_probability
        if belief is None:
            structural = public_belief(game, {}, history)
            if structural is None:
                raise AssertionError("uniform policy cannot reach a legal history")
            resolver_player = structural.acting_player
        else:
            resolver_player = belief.acting_player
        try:
            result = solve_maxmargin_subgame(
                game,
                composed,
                history,
                resolver_player,
                max_pure_plans=max_pure_plans,
                tolerance=tolerance,
            )
        except ZeroCounterfactualReachError:
            skipped.append(history)
            continue
        records.append(
            MaxMarginPublicResolveRecord(
                history=history,
                resolver_player=resolver_player,
                public_reach_probability=public_reach,
                opponent_counterfactual_reach=(
                    result.frontier.total_counterfactual_reach
                ),
                frontier_information_sets=len(result.frontier.entries),
                resolver_information_sets=result.resolver_information_sets,
                max_margin=result.max_margin,
                total_positive_frontier_violation=(
                    result.total_positive_frontier_violation
                ),
                oracle_seconds=result.oracle_seconds,
                resolver_pure_plans=result.resolver_pure_plans,
                opponent_pure_plans=result.opponent_pure_plans,
                unique_response_constraints=(
                    result.unique_response_constraints
                ),
                resolver_support_size=result.resolver_support_size,
            )
        )
        composed = result.policy

    return MaxMarginContinualResolveResult(
        policy=composed,
        records=tuple(records),
        structural_public_histories=len(histories),
        searched_public_histories=len(records),
        skipped_zero_counterfactual_reach_histories=tuple(skipped),
        total_oracle_seconds=sum(record.oracle_seconds for record in records),
        expected_oracle_seconds_per_hand=sum(
            record.public_reach_probability * record.oracle_seconds
            for record in records
        ),
        expected_public_decisions_per_hand=sum(
            record.public_reach_probability for record in records
        ),
        cumulative_exploitability_increase_bound=sum(
            record.total_positive_frontier_violation / 2.0
            for record in records
        ),
        reach_weighted_max_margin=sum(
            record.public_reach_probability * record.max_margin
            for record in records
        ),
    )
