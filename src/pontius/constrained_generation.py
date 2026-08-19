"""Restricted-master row/column generation for safe sum-margin resolving."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from math import isfinite, prod

from .continual import PublicHistory
from .evaluation import (
    Policy,
    best_response,
    collect_information_sets,
    expected_utilities_from_state,
    policy_distribution,
)
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState
from .kuhn import KuhnPoker
from .linear_program import maximize_linear_program
from .maxmargin import (
    solve_safe_best_response_subgame,
    solve_safe_sum_margin_subgame,
)
from .safe_resolving import (
    CounterfactualFrontier,
    CounterfactualSubgameGame,
    build_counterfactual_frontier,
    counterfactual_best_response_values,
)


@dataclass(slots=True)
class _StrategyColumn:
    label: str
    policy: Policy = field(repr=False)
    own_reach: dict[str, float] = field(repr=False)
    pure_signature: tuple[tuple[str, Action], ...] | None = None


@dataclass(frozen=True, slots=True)
class _ResponsePlan:
    signature: tuple[tuple[str, Action], ...]
    policy: Policy = field(compare=False, hash=False, repr=False)


@dataclass(frozen=True, slots=True)
class _ActiveConstraint:
    frontier_key: str
    response_signature: tuple[tuple[str, Action], ...]


@dataclass(frozen=True, slots=True)
class GenerationUpdateRecord:
    update: int
    columns_before_update: int
    response_constraints_before_update: int
    restricted_master_objective: float
    restricted_auxiliary_margin_sum: float
    actual_sum_margin: float
    actual_min_margin: float
    total_positive_frontier_violation: float
    safe_candidate: bool
    candidate_support_size: int
    incumbent_updated: bool
    incumbent_sum_margin: float
    incumbent_hidden_br_reduction: float
    exact_sum_margin_regret: float
    exact_sum_margin_capture: float | None
    incumbent_exact_sum_margin_regret: float
    incumbent_exact_sum_margin_capture: float | None
    candidate_hidden_br_reduction: float
    candidate_hidden_br_regret: float
    incumbent_hidden_br_regret: float
    master_duality_gap: float
    realization_equivalence_max_error: float | None
    effective_column_dual: float
    best_pricing_score: float | None
    best_reduced_cost: float | None
    added_column: str | None
    added_response_constraints: int
    converged: bool
    pricing_performed: bool
    master_build_seconds: float
    master_solve_seconds: float
    policy_conversion_seconds: float
    separation_seconds: float
    pricing_seconds: float
    hidden_diagnostic_seconds: float
    cumulative_candidate_compute_seconds: float
    cumulative_decision_compute_seconds: float
    candidate_incumbent_sum_margin_per_millisecond: float | None
    candidate_incumbent_hidden_br_reduction_per_millisecond: float | None
    incumbent_sum_margin_per_millisecond: float | None
    incumbent_hidden_br_reduction_per_millisecond: float | None


@dataclass(frozen=True, slots=True)
class ConstraintGenerationResult:
    policy: Policy = field(compare=False, repr=False)
    frontier: CounterfactualFrontier
    updates: tuple[GenerationUpdateRecord, ...]
    converged: bool
    max_updates: int
    final_columns: int
    final_response_constraints: int
    resolver_normal_form_plans: int
    incumbent_sum_margin: float
    incumbent_hidden_br_reduction: float
    exact_sum_margin_optimum: float
    exact_hidden_br_optimum: float
    exact_oracle_seconds: float
    setup_seconds: float
    total_master_build_seconds: float
    total_master_solve_seconds: float
    total_policy_conversion_seconds: float
    total_separation_seconds: float
    total_pricing_seconds: float
    total_hidden_diagnostic_seconds: float

    @property
    def decision_compute_seconds(self) -> float:
        return (
            self.setup_seconds
            + self.total_master_build_seconds
            + self.total_master_solve_seconds
            + self.total_policy_conversion_seconds
            + self.total_separation_seconds
            + self.total_pricing_seconds
        )


def _copy_policy(policy: Policy) -> Policy:
    return {key: dict(distribution) for key, distribution in policy.items()}


def _own_reaches(
    game: ExtensiveFormGame,
    player: int,
    policy: Policy,
    tolerance: float,
) -> dict[str, float]:
    reaches: dict[str, float] = {}

    def walk(state: GameState, own_reach: float) -> None:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            for action, _ in state.chance_outcomes():
                walk(state.apply_action(action), own_reach)
            return
        actions = tuple(state.legal_actions())
        if acting != player:
            for action in actions:
                walk(state.apply_action(action), own_reach)
            return
        key = state.information_state_key(player)
        previous = reaches.setdefault(key, own_reach)
        if abs(previous - own_reach) > 100.0 * tolerance:
            raise ValueError(f"game violates perfect recall at {key!r}")
        distribution = policy_distribution(policy, key, actions)
        for action, probability in distribution.items():
            walk(state.apply_action(action), own_reach * probability)

    walk(game.initial_state(), 1.0)
    expected = set(collect_information_sets(game, player))
    if set(reaches) != expected:
        raise AssertionError("own-reach traversal omitted information sets")
    return reaches


def _mixture_to_behavioral_policy(
    game: ExtensiveFormGame,
    resolver_player: int,
    columns: list[_StrategyColumn],
    weights: tuple[float, ...],
    fallback: Policy,
    tolerance: float,
) -> Policy:
    information_sets = collect_information_sets(game, resolver_player)
    result = _copy_policy(fallback)
    for key, actions in information_sets.items():
        mass = sum(
            weight * column.own_reach[key]
            for weight, column in zip(weights, columns, strict=True)
        )
        if mass <= tolerance:
            result[key] = policy_distribution(fallback, key, actions)
            continue
        action_mass = {action: 0.0 for action in actions}
        for weight, column in zip(weights, columns, strict=True):
            reach_weight = weight * column.own_reach[key]
            distribution = policy_distribution(column.policy, key, actions)
            for action in actions:
                action_mass[action] += reach_weight * distribution[action]
        result[key] = {
            action: action_mass[action] / mass for action in actions
        }
    return result


def _frontier_values(
    frontier: CounterfactualFrontier,
    resolver_policy: Policy,
    opponent_policy: Policy,
) -> dict[str, float]:
    profile = _copy_policy(resolver_policy)
    profile.update(opponent_policy)
    values: dict[str, float] = {}
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
    return values


def _best_response_plan(
    subgame: CounterfactualSubgameGame,
    frontier: CounterfactualFrontier,
    resolver_policy: Policy,
    tolerance: float,
    verify_entrywise: bool,
) -> tuple[_ResponsePlan, dict[str, float]]:
    _, selected = best_response(
        subgame,
        resolver_policy,
        frontier.opponent_player,
    )
    information_sets = collect_information_sets(
        subgame,
        frontier.opponent_player,
    )
    signature = tuple(sorted(selected.items()))
    if set(selected) != set(information_sets):
        raise AssertionError("best response omitted opponent information sets")
    policy = {
        key: {
            action: float(action == selected[key])
            for action in information_sets[key]
        }
        for key in information_sets
    }
    plan = _ResponsePlan(signature=signature, policy=policy)
    values = _frontier_values(frontier, resolver_policy, policy)
    if verify_entrywise:
        independently_verified = counterfactual_best_response_values(
            frontier,
            resolver_policy,
        )
        error = max(
            abs(values[key] - independently_verified[key])
            for key in frontier.blueprint_values
        )
        if error > 100.0 * tolerance:
            raise AssertionError("generated response is not entry-wise optimal")
    return plan, values


class _MarginCache:
    def __init__(self, frontier: CounterfactualFrontier) -> None:
        self.frontier = frontier
        self.values: dict[
            tuple[str, tuple[tuple[str, Action], ...]],
            dict[str, float],
        ] = {}

    def margins(
        self,
        column: _StrategyColumn,
        response: _ResponsePlan,
    ) -> dict[str, float]:
        cache_key = (column.label, response.signature)
        cached = self.values.get(cache_key)
        if cached is not None:
            return cached
        candidate_values = _frontier_values(
            self.frontier,
            column.policy,
            response.policy,
        )
        blueprint_values = self.frontier.blueprint_values
        margins = {
            key: blueprint_values[key] - candidate_values[key]
            for key in blueprint_values
        }
        self.values[cache_key] = margins
        return margins


def _simplex_rows(
    columns: int,
    entries: int,
) -> tuple[list[list[float]], list[float]]:
    width = columns + entries
    probability_sum = [0.0] * width
    for column in range(columns):
        probability_sum[column] = 1.0
    return (
        [probability_sum, [-value for value in probability_sum]],
        [1.0, -1.0],
    )


def _build_master(
    frontier: CounterfactualFrontier,
    columns: list[_StrategyColumn],
    responses: dict[tuple[tuple[str, Action], ...], _ResponsePlan],
    active_constraints: list[_ActiveConstraint],
    cache: _MarginCache,
) -> tuple[list[float], list[list[float]], list[float], tuple[str, ...]]:
    entry_keys = tuple(entry.key for entry in frontier.entries)
    entry_indices = {key: index for index, key in enumerate(entry_keys)}
    coefficients, bounds = _simplex_rows(len(columns), len(entry_keys))
    for constraint in active_constraints:
        response = responses[constraint.response_signature]
        row = [
            -cache.margins(column, response)[constraint.frontier_key]
            for column in columns
        ]
        row.extend([0.0] * len(entry_keys))
        row[len(columns) + entry_indices[constraint.frontier_key]] = 1.0
        coefficients.append(row)
        bounds.append(0.0)
    objective = [0.0] * len(columns) + [1.0] * len(entry_keys)
    return objective, coefficients, bounds, entry_keys


def _normalized_weights(
    raw: tuple[float, ...],
    tolerance: float,
) -> tuple[float, ...]:
    mass = sum(raw)
    if mass <= tolerance:
        raise AssertionError("restricted master returned zero strategy mass")
    return tuple(max(0.0, value) / mass for value in raw)


def _realization_equivalence_error(
    frontier: CounterfactualFrontier,
    columns: list[_StrategyColumn],
    weights: tuple[float, ...],
    policy: Policy,
    responses: dict[tuple[tuple[str, Action], ...], _ResponsePlan],
    active_constraints: list[_ActiveConstraint],
    cache: _MarginCache,
) -> float:
    behavioral_cache: dict[tuple[tuple[str, Action], ...], dict[str, float]] = {}
    max_error = 0.0
    for constraint in active_constraints:
        response = responses[constraint.response_signature]
        normal_margin = sum(
            weight * cache.margins(column, response)[constraint.frontier_key]
            for weight, column in zip(weights, columns, strict=True)
        )
        values = behavioral_cache.get(response.signature)
        if values is None:
            values = _frontier_values(frontier, policy, response.policy)
            behavioral_cache[response.signature] = values
        behavioral_margin = (
            frontier.blueprint_values[constraint.frontier_key]
            - values[constraint.frontier_key]
        )
        max_error = max(max_error, abs(normal_margin - behavioral_margin))
    return max_error


def _pricing_opponent_key(scenario: int, information_key: str) -> str:
    return f"__pricing_response_{scenario}__::{information_key}"


@dataclass(frozen=True, slots=True)
class _PricingContinuationState:
    base: GameState = field(compare=False, hash=False, repr=False)
    scenario: int
    resolver_player: int
    opponent_player: int

    @property
    def current_player(self) -> int:
        return self.base.current_player

    def legal_actions(self) -> tuple[Action, ...]:
        return tuple(self.base.legal_actions())

    def chance_outcomes(self) -> tuple[tuple[Action, float], ...]:
        return tuple(self.base.chance_outcomes())

    def apply_action(self, action: Action) -> GameState:
        return _PricingContinuationState(
            self.base.apply_action(action),
            self.scenario,
            self.resolver_player,
            self.opponent_player,
        )

    def information_state_key(self, player: int) -> str:
        key = self.base.information_state_key(player)
        if player == self.resolver_player:
            return key
        if player == self.opponent_player:
            return _pricing_opponent_key(self.scenario, key)
        raise ValueError(f"invalid pricing player {player}")

    def returns(self) -> tuple[float, ...]:
        return self.base.returns()


@dataclass(frozen=True, slots=True)
class _PricingRootState:
    frontier: CounterfactualFrontier = field(compare=False, hash=False, repr=False)
    weighted_roots: tuple[tuple[int, int, float], ...]
    total_weight: float

    @property
    def current_player(self) -> int:
        return CHANCE_PLAYER

    def legal_actions(self) -> tuple[Action, ...]:
        return ()

    def chance_outcomes(self) -> tuple[tuple[Action, float], ...]:
        return tuple(
            ((scenario, root_index), weight / self.total_weight)
            for scenario, root_index, weight in self.weighted_roots
        )

    def apply_action(self, action: Action) -> GameState:
        matches = [
            (scenario, root_index)
            for scenario, root_index, _ in self.weighted_roots
            if action == (scenario, root_index)
        ]
        if len(matches) != 1:
            raise ValueError(f"invalid pricing-root outcome {action!r}")
        scenario, root_index = matches[0]
        return _PricingContinuationState(
            self.frontier.roots[root_index].state,
            scenario,
            self.frontier.resolver_player,
            self.frontier.opponent_player,
        )

    def information_state_key(self, player: int) -> str:
        raise ValueError("pricing-root chance state has no information set")

    def returns(self) -> tuple[float, ...]:
        raise ValueError("pricing-root chance state is not terminal")


@dataclass(frozen=True, slots=True)
class _PricingGame:
    frontier: CounterfactualFrontier = field(compare=False, repr=False)
    weighted_roots: tuple[tuple[int, int, float], ...]
    total_weight: float
    num_players: int = 2

    def initial_state(self) -> GameState:
        return _PricingRootState(
            self.frontier,
            self.weighted_roots,
            self.total_weight,
        )


def _price_column(
    subgame: CounterfactualSubgameGame,
    frontier: CounterfactualFrontier,
    active_pure_signatures: set[tuple[tuple[str, Action], ...]],
    next_column_index: int,
    active_constraints: list[_ActiveConstraint],
    responses: dict[tuple[tuple[str, Action], ...], _ResponsePlan],
    response_duals: tuple[float, ...],
    effective_column_dual: float,
    tolerance: float,
) -> tuple[_StrategyColumn | None, float | None, float | None]:
    weighted_roots: list[tuple[int, int, float]] = []
    pricing_policy: Policy = {}
    blueprint_constant = 0.0
    for scenario, (dual, constraint) in enumerate(
        zip(response_duals, active_constraints, strict=True)
    ):
        if dual <= 0.0:
            continue
        blueprint_constant += dual * frontier.blueprint_values[
            constraint.frontier_key
        ]
        for root_index, root in enumerate(frontier.roots):
            if root.opponent_augmented_key == constraint.frontier_key:
                weighted_roots.append(
                    (scenario, root_index, dual * root.counterfactual_reach)
                )
        response = responses[constraint.response_signature]
        pricing_policy.update(
            {
                _pricing_opponent_key(scenario, key): dict(distribution)
                for key, distribution in response.policy.items()
            }
        )
    total_weight = sum(weight for _, _, weight in weighted_roots)
    if total_weight <= tolerance:
        raise AssertionError("restricted-master dual has no pricing mass")
    pricing_game = _PricingGame(
        frontier,
        tuple(weighted_roots),
        total_weight,
    )
    resolver_value, selected = best_response(
        pricing_game,
        pricing_policy,
        frontier.resolver_player,
    )
    information_sets = collect_information_sets(subgame, frontier.resolver_player)
    if set(selected) != set(information_sets):
        raise AssertionError("pricing best response omitted resolver information sets")
    signature = tuple(sorted(selected.items()))
    best_score = blueprint_constant + total_weight * resolver_value
    reduced_cost = best_score - effective_column_dual
    if reduced_cost <= tolerance:
        return None, best_score, reduced_cost
    if signature in active_pure_signatures:
        raise AssertionError("active resolver column has positive reduced cost")
    policy = {
        key: {
            action: float(action == selected[key])
            for action in information_sets[key]
        }
        for key in information_sets
    }
    return (
        _StrategyColumn(
            label=f"pure:{next_column_index}",
            policy=policy,
            own_reach=_own_reaches(
                subgame,
                frontier.resolver_player,
                policy,
                tolerance,
            ),
            pure_signature=signature,
        ),
        best_score,
        reduced_cost,
    )


def solve_sum_margin_with_generation(
    game: KuhnPoker,
    blueprint: Policy,
    history: PublicHistory,
    resolver_player: int,
    *,
    max_updates: int = 100,
    max_pure_plans: int = 1_000_000,
    tolerance: float = 1e-10,
    verify_generated_responses: bool = True,
    verify_realization_equivalence: bool = True,
    price_after_last_update: bool = True,
) -> ConstraintGenerationResult:
    """Solve safe sum-margin by generating response rows and strategy columns.

    Exact normal-form and full-game targets are computed only for diagnostics.
    Construction begins with one behavioral blueprint column and its opponent
    best response. Every later row comes from response separation; every later
    resolver column must have positive reduced cost under the restricted LP dual.
    """

    if max_updates <= 0:
        raise ValueError("max_updates must be positive")
    if max_pure_plans <= 0:
        raise ValueError("max_pure_plans must be positive")
    if not isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")

    oracle_start = time.perf_counter()
    exact_sum = solve_safe_sum_margin_subgame(
        game,
        blueprint,
        history,
        resolver_player,
        max_pure_plans=max_pure_plans,
        tolerance=tolerance,
    )
    exact_hidden = solve_safe_best_response_subgame(
        game,
        blueprint,
        history,
        resolver_player,
        max_pure_plans=max_pure_plans,
        tolerance=tolerance,
    )
    exact_oracle_seconds = time.perf_counter() - oracle_start

    setup_start = time.perf_counter()
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
    resolver_information_sets = collect_information_sets(
        subgame,
        resolver_player,
    )
    resolver_normal_form_plans = prod(
        len(actions) for actions in resolver_information_sets.values()
    )
    blueprint_column = _StrategyColumn(
        label="blueprint",
        policy=blueprint,
        own_reach=_own_reaches(
            subgame,
            resolver_player,
            blueprint,
            tolerance,
        ),
    )
    columns = [blueprint_column]
    active_pure_signatures: set[tuple[tuple[str, Action], ...]] = set()
    initial_response, _ = _best_response_plan(
        subgame,
        frontier,
        blueprint,
        tolerance,
        verify_generated_responses,
    )
    responses = {initial_response.signature: initial_response}
    active_constraints = [
        _ActiveConstraint(entry.key, initial_response.signature)
        for entry in frontier.entries
    ]
    active_constraint_keys = {
        (constraint.frontier_key, constraint.response_signature)
        for constraint in active_constraints
    }
    cache = _MarginCache(frontier)
    setup_seconds = time.perf_counter() - setup_start

    incumbent_policy = _copy_policy(blueprint)
    incumbent_sum_margin = 0.0
    incumbent_hidden_gain = 0.0
    updates: list[GenerationUpdateRecord] = []
    total_master_build = 0.0
    total_master_solve = 0.0
    total_conversion = 0.0
    total_separation = 0.0
    total_pricing = 0.0
    total_hidden = 0.0
    converged = False

    for update in range(1, max_updates + 1):
        columns_before = len(columns)
        constraints_before = len(active_constraints)
        build_start = time.perf_counter()
        objective, coefficients, bounds, entry_keys = _build_master(
            frontier,
            columns,
            responses,
            active_constraints,
            cache,
        )
        master_build_seconds = time.perf_counter() - build_start
        total_master_build += master_build_seconds
        solve_start = time.perf_counter()
        solution = maximize_linear_program(
            objective,
            coefficients,
            bounds,
            tolerance=min(tolerance / 10.0, 1e-11),
        )
        master_solve_seconds = time.perf_counter() - solve_start
        total_master_solve += master_solve_seconds

        conversion_start = time.perf_counter()
        weights = _normalized_weights(
            solution.variables[:columns_before],
            tolerance,
        )
        candidate_policy = _mixture_to_behavioral_policy(
            subgame,
            resolver_player,
            columns,
            weights,
            blueprint,
            tolerance,
        )
        equivalence_error = (
            _realization_equivalence_error(
                frontier,
                columns,
                weights,
                candidate_policy,
                responses,
                active_constraints,
                cache,
            )
            if verify_realization_equivalence
            else None
        )
        policy_conversion_seconds = time.perf_counter() - conversion_start
        total_conversion += policy_conversion_seconds

        separation_start = time.perf_counter()
        separating_response, candidate_values = _best_response_plan(
            subgame,
            frontier,
            candidate_policy,
            tolerance,
            verify_generated_responses,
        )
        blueprint_values = frontier.blueprint_values
        actual_margins = {
            key: blueprint_values[key] - candidate_values[key]
            for key in entry_keys
        }
        actual_sum_margin = sum(actual_margins.values())
        actual_min_margin = min(actual_margins.values())
        total_violation = sum(
            max(0.0, -margin) for margin in actual_margins.values()
        )
        auxiliary_margins = solution.variables[
            columns_before : columns_before + len(entry_keys)
        ]
        missing_constraints: list[_ActiveConstraint] = []
        responses.setdefault(separating_response.signature, separating_response)
        for entry_key, auxiliary_margin in zip(
            entry_keys,
            auxiliary_margins,
            strict=True,
        ):
            constraint_key = (entry_key, separating_response.signature)
            if auxiliary_margin > actual_margins[entry_key] + tolerance:
                if constraint_key in active_constraint_keys:
                    if auxiliary_margin > actual_margins[entry_key] + 1e-8:
                        raise AssertionError("active response constraint was violated")
                else:
                    missing_constraints.append(
                        _ActiveConstraint(entry_key, separating_response.signature)
                    )
        separation_seconds = time.perf_counter() - separation_start
        total_separation += separation_seconds

        safe_candidate = total_violation <= tolerance
        incumbent_updated = (
            safe_candidate
            and actual_sum_margin > incumbent_sum_margin + tolerance
        )
        hidden_start = time.perf_counter()
        blueprint_opponent_br = exact_hidden.blueprint_opponent_best_response_value
        if blueprint_opponent_br is None:
            raise AssertionError("hidden oracle omitted blueprint best response")
        candidate_opponent_br = best_response(
            game,
            candidate_policy,
            frontier.opponent_player,
        )[0]
        candidate_hidden_gain = blueprint_opponent_br - candidate_opponent_br
        hidden_diagnostic_seconds = time.perf_counter() - hidden_start
        total_hidden += hidden_diagnostic_seconds
        if incumbent_updated:
            incumbent_policy = _copy_policy(candidate_policy)
            incumbent_sum_margin = actual_sum_margin
            incumbent_hidden_gain = candidate_hidden_gain

        cumulative_candidate_seconds = (
            setup_seconds
            + total_master_build
            + total_master_solve
            + total_conversion
            + total_separation
            + total_pricing
        )
        pricing_performed = price_after_last_update or update < max_updates
        equality_duals = solution.dual_variables[:2]
        effective_column_dual = equality_duals[0] - equality_duals[1]
        response_duals = solution.dual_variables[2:]
        if len(response_duals) != len(active_constraints):
            raise AssertionError("master dual count does not match response rows")
        if pricing_performed:
            pricing_start = time.perf_counter()
            priced_column, best_pricing_score, best_reduced_cost = _price_column(
                subgame,
                frontier,
                active_pure_signatures,
                len(columns) - 1,
                active_constraints,
                responses,
                response_duals,
                effective_column_dual,
                tolerance,
            )
            pricing_seconds = time.perf_counter() - pricing_start
        else:
            priced_column = None
            best_pricing_score = None
            best_reduced_cost = None
            pricing_seconds = 0.0
        add_column = (
            priced_column
            if best_reduced_cost is not None and best_reduced_cost > tolerance
            else None
        )
        total_pricing += pricing_seconds

        for constraint in missing_constraints:
            active_constraints.append(constraint)
            active_constraint_keys.add(
                (constraint.frontier_key, constraint.response_signature)
            )
        if add_column is not None:
            columns.append(add_column)
            if add_column.pure_signature is None:
                raise AssertionError("generated pure column omitted its signature")
            active_pure_signatures.add(add_column.pure_signature)
        converged = (
            pricing_performed
            and not missing_constraints
            and add_column is None
        )

        cumulative_decision_seconds = (
            setup_seconds
            + total_master_build
            + total_master_solve
            + total_conversion
            + total_separation
            + total_pricing
        )
        exact_sum_optimum = exact_sum.verified_sum_margin
        exact_hidden_optimum = exact_hidden.verified_objective_value
        updates.append(
            GenerationUpdateRecord(
                update=update,
                columns_before_update=columns_before,
                response_constraints_before_update=constraints_before,
                restricted_master_objective=solution.objective,
                restricted_auxiliary_margin_sum=sum(auxiliary_margins),
                actual_sum_margin=actual_sum_margin,
                actual_min_margin=actual_min_margin,
                total_positive_frontier_violation=total_violation,
                safe_candidate=safe_candidate,
                candidate_support_size=sum(weight > tolerance for weight in weights),
                incumbent_updated=incumbent_updated,
                incumbent_sum_margin=incumbent_sum_margin,
                incumbent_hidden_br_reduction=incumbent_hidden_gain,
                exact_sum_margin_regret=exact_sum_optimum - actual_sum_margin,
                exact_sum_margin_capture=(
                    actual_sum_margin / exact_sum_optimum
                    if exact_sum_optimum > tolerance
                    else None
                ),
                incumbent_exact_sum_margin_regret=(
                    exact_sum_optimum - incumbent_sum_margin
                ),
                incumbent_exact_sum_margin_capture=(
                    incumbent_sum_margin / exact_sum_optimum
                    if exact_sum_optimum > tolerance
                    else None
                ),
                candidate_hidden_br_reduction=candidate_hidden_gain,
                candidate_hidden_br_regret=(
                    exact_hidden_optimum - candidate_hidden_gain
                ),
                incumbent_hidden_br_regret=(
                    exact_hidden_optimum - incumbent_hidden_gain
                ),
                master_duality_gap=solution.duality_gap,
                realization_equivalence_max_error=equivalence_error,
                effective_column_dual=effective_column_dual,
                best_pricing_score=best_pricing_score,
                best_reduced_cost=best_reduced_cost,
                added_column=None if add_column is None else add_column.label,
                added_response_constraints=len(missing_constraints),
                converged=converged,
                pricing_performed=pricing_performed,
                master_build_seconds=master_build_seconds,
                master_solve_seconds=master_solve_seconds,
                policy_conversion_seconds=policy_conversion_seconds,
                separation_seconds=separation_seconds,
                pricing_seconds=pricing_seconds,
                hidden_diagnostic_seconds=hidden_diagnostic_seconds,
                cumulative_candidate_compute_seconds=(
                    cumulative_candidate_seconds
                ),
                cumulative_decision_compute_seconds=cumulative_decision_seconds,
                candidate_incumbent_sum_margin_per_millisecond=(
                    incumbent_sum_margin
                    / (1_000.0 * cumulative_candidate_seconds)
                    if cumulative_candidate_seconds > 0.0
                    else None
                ),
                candidate_incumbent_hidden_br_reduction_per_millisecond=(
                    incumbent_hidden_gain
                    / (1_000.0 * cumulative_candidate_seconds)
                    if cumulative_candidate_seconds > 0.0
                    else None
                ),
                incumbent_sum_margin_per_millisecond=(
                    incumbent_sum_margin / (1_000.0 * cumulative_decision_seconds)
                    if cumulative_decision_seconds > 0.0
                    else None
                ),
                incumbent_hidden_br_reduction_per_millisecond=(
                    incumbent_hidden_gain / (1_000.0 * cumulative_decision_seconds)
                    if cumulative_decision_seconds > 0.0
                    else None
                ),
            )
        )
        if converged:
            allowed = 1e-8 * max(1.0, abs(exact_sum_optimum))
            if abs(actual_sum_margin - exact_sum_optimum) > allowed:
                raise AssertionError(
                    "generated optimum disagrees with exact normal-form oracle"
                )
            if equivalence_error is not None and equivalence_error > allowed:
                raise AssertionError("generated mixture realization error is too large")
            break

    return ConstraintGenerationResult(
        policy=incumbent_policy,
        frontier=frontier,
        updates=tuple(updates),
        converged=converged,
        max_updates=max_updates,
        final_columns=len(columns),
        final_response_constraints=len(active_constraints),
        resolver_normal_form_plans=resolver_normal_form_plans,
        incumbent_sum_margin=incumbent_sum_margin,
        incumbent_hidden_br_reduction=incumbent_hidden_gain,
        exact_sum_margin_optimum=exact_sum.verified_sum_margin,
        exact_hidden_br_optimum=exact_hidden.verified_objective_value,
        exact_oracle_seconds=exact_oracle_seconds,
        setup_seconds=setup_seconds,
        total_master_build_seconds=total_master_build,
        total_master_solve_seconds=total_master_solve,
        total_policy_conversion_seconds=total_conversion,
        total_separation_seconds=total_separation,
        total_pricing_seconds=total_pricing,
        total_hidden_diagnostic_seconds=total_hidden,
    )
