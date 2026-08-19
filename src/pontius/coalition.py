"""Exact coordinated best responses for finite shared-information coalitions.

This module is a diagnostic, not a multiplayer safety theorem.  Coalition
members share their private observations, coordinate all member actions, and
maximize transferable team utility while outsider policies remain fixed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, product
from math import fsum, isfinite, prod

from .evaluation import EvaluationResult, Policy, expected_utilities, policy_distribution
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState


@dataclass(slots=True)
class _CoalitionInformationSet:
    actions: tuple[Action, ...]
    team_depth: int
    states: list[tuple[GameState, float]] = field(default_factory=list)


def _validated_coalition(
    game: ExtensiveFormGame,
    coalition: tuple[int, ...],
) -> tuple[int, ...]:
    members = tuple(sorted(coalition))
    if not members or len(set(members)) != len(members):
        raise ValueError("coalition members must be unique and nonempty")
    if any(player not in range(game.num_players) for player in members):
        raise ValueError("coalition contains an invalid player")
    if len(members) == game.num_players:
        raise ValueError("the full player set is not an informative coalition threat")
    return members


def _coalition_key(state: GameState, coalition: tuple[int, ...]) -> str:
    method = getattr(state, "coalition_information_state_key", None)
    if method is None or not callable(method):
        raise TypeError(
            "coalition evaluation requires coalition_information_state_key on game states"
        )
    key = method(coalition)
    if not isinstance(key, str) or not key:
        raise ValueError("coalition information key must be a nonempty string")
    return key


def _team_terminal_value(state: GameState, coalition: tuple[int, ...]) -> float:
    returns = state.returns()
    return fsum(returns[player] for player in coalition)


def coalition_best_response(
    game: ExtensiveFormGame,
    policy: Policy,
    coalition: tuple[int, ...],
) -> tuple[float, dict[str, Action]]:
    """Compute an exact perfect-recall shared-information team response."""

    members = _validated_coalition(game, coalition)
    member_set = frozenset(members)
    information_sets: dict[str, _CoalitionInformationSet] = {}

    def collect(state: GameState, counterfactual_reach: float, team_depth: int) -> None:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            for action, probability in state.chance_outcomes():
                collect(
                    state.apply_action(action),
                    counterfactual_reach * probability,
                    team_depth,
                )
            return

        actions = tuple(state.legal_actions())
        if not actions:
            raise ValueError("nonterminal player state has no legal actions")
        if acting in member_set:
            key = _coalition_key(state, members)
            entry = information_sets.get(key)
            if entry is None:
                entry = _CoalitionInformationSet(actions, team_depth)
                information_sets[key] = entry
            elif entry.actions != actions or entry.team_depth != team_depth:
                raise ValueError(
                    f"game violates team action consistency or perfect recall at {key!r}"
                )
            entry.states.append((state, counterfactual_reach))
            for action in actions:
                collect(state.apply_action(action), counterfactual_reach, team_depth + 1)
            return

        key = state.information_state_key(acting)
        distribution = policy_distribution(policy, key, actions)
        for action, probability in distribution.items():
            collect(
                state.apply_action(action),
                counterfactual_reach * probability,
                team_depth,
            )

    collect(game.initial_state(), 1.0, 0)
    selected_actions: dict[str, Action] = {}

    def continuation_value(state: GameState) -> float:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return _team_terminal_value(state, members)
        if acting == CHANCE_PLAYER:
            return fsum(
                probability * continuation_value(state.apply_action(action))
                for action, probability in state.chance_outcomes()
            )

        actions = tuple(state.legal_actions())
        if acting in member_set:
            key = _coalition_key(state, members)
            if key not in selected_actions:
                raise ValueError(
                    f"coalition-response dependency {key!r} was not solved bottom-up"
                )
            return continuation_value(state.apply_action(selected_actions[key]))

        key = state.information_state_key(acting)
        distribution = policy_distribution(policy, key, actions)
        return fsum(
            probability * continuation_value(state.apply_action(action))
            for action, probability in distribution.items()
        )

    ordered = sorted(
        information_sets.items(),
        key=lambda item: (item[1].team_depth, item[0]),
        reverse=True,
    )
    for key, entry in ordered:
        action_values = {
            action: fsum(
                reach * continuation_value(state.apply_action(action))
                for state, reach in entry.states
            )
            for action in entry.actions
        }
        selected_actions[key] = max(entry.actions, key=action_values.__getitem__)

    return continuation_value(game.initial_state()), selected_actions


def coalition_best_response_enumerated(
    game: ExtensiveFormGame,
    policy: Policy,
    coalition: tuple[int, ...],
    *,
    max_pure_policies: int = 1_000_000,
) -> tuple[float, dict[str, Action]]:
    """Independently enumerate pure shared-information team policies."""

    members = _validated_coalition(game, coalition)
    member_set = frozenset(members)
    information_sets: dict[str, tuple[Action, ...]] = {}

    def collect(state: GameState) -> None:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            for action, _ in state.chance_outcomes():
                collect(state.apply_action(action))
            return
        actions = tuple(state.legal_actions())
        if acting in member_set:
            key = _coalition_key(state, members)
            previous = information_sets.setdefault(key, actions)
            if previous != actions:
                raise ValueError(f"inconsistent coalition actions at {key!r}")
        for action in actions:
            collect(state.apply_action(action))

    collect(game.initial_state())
    policy_count = prod(len(actions) for actions in information_sets.values())
    if policy_count > max_pure_policies:
        raise ValueError(
            f"exact coalition response requires {policy_count} pure policies; "
            f"limit is {max_pure_policies}"
        )

    keys = tuple(sorted(information_sets))
    action_spaces = tuple(information_sets[key] for key in keys)

    def value(state: GameState, selected: dict[str, Action]) -> float:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return _team_terminal_value(state, members)
        if acting == CHANCE_PLAYER:
            return fsum(
                probability * value(state.apply_action(action), selected)
                for action, probability in state.chance_outcomes()
            )
        actions = tuple(state.legal_actions())
        if acting in member_set:
            return value(
                state.apply_action(selected[_coalition_key(state, members)]),
                selected,
            )
        distribution = policy_distribution(
            policy,
            state.information_state_key(acting),
            actions,
        )
        return fsum(
            probability * value(state.apply_action(action), selected)
            for action, probability in distribution.items()
        )

    best_value = float("-inf")
    best_actions: dict[str, Action] = {}
    for selected_actions in product(*action_spaces):
        selected = dict(zip(keys, selected_actions, strict=True))
        candidate_value = value(game.initial_state(), selected)
        if candidate_value > best_value:
            best_value = candidate_value
            best_actions = selected
    return best_value, best_actions


@dataclass(frozen=True, slots=True)
class CoalitionThreat:
    coalition: tuple[int, ...]
    baseline_value: float
    best_response_value: float
    deviation_gain: float


@dataclass(frozen=True, slots=True)
class CoalitionEvaluationResult:
    threats: tuple[CoalitionThreat, ...]
    maximum_deviation_gain: float
    total_deviation_gain: float

    def by_coalition(self) -> dict[tuple[int, ...], CoalitionThreat]:
        return {threat.coalition: threat for threat in self.threats}


def evaluate_coalition_threats(
    game: ExtensiveFormGame,
    policy: Policy,
    coalitions: tuple[tuple[int, ...], ...] | None = None,
) -> CoalitionEvaluationResult:
    """Evaluate declared coalitions, defaulting to every proper player pair."""

    if coalitions is None:
        coalitions = tuple(combinations(range(game.num_players), 2))
        if game.num_players == 2:
            coalitions = ()
    normalized = tuple(_validated_coalition(game, coalition) for coalition in coalitions)
    if len(set(normalized)) != len(normalized):
        raise ValueError("coalition list contains duplicates")
    utilities = expected_utilities(game, policy)
    threats: list[CoalitionThreat] = []
    for coalition in normalized:
        baseline = fsum(utilities[player] for player in coalition)
        response, _ = coalition_best_response(game, policy, coalition)
        threats.append(
            CoalitionThreat(
                coalition=coalition,
                baseline_value=baseline,
                best_response_value=response,
                deviation_gain=max(0.0, response - baseline),
            )
        )
    result = tuple(threats)
    return CoalitionEvaluationResult(
        threats=result,
        maximum_deviation_gain=max(
            (threat.deviation_gain for threat in result),
            default=0.0,
        ),
        total_deviation_gain=fsum(threat.deviation_gain for threat in result),
    )


@dataclass(frozen=True, slots=True)
class MultiplayerAcceptanceAssessment:
    numerical_guard: float
    aggregate_nash_conv_strictly_decreases: bool
    no_player_deviation_gain_increases: bool
    no_coalition_deviation_gain_increases: bool
    unilateral_pareto_accept: bool
    coalition_stress_accept: bool


def assess_multiplayer_candidate(
    source: EvaluationResult,
    candidate: EvaluationResult,
    source_coalitions: CoalitionEvaluationResult,
    candidate_coalitions: CoalitionEvaluationResult,
    *,
    payoff_span: float,
    numerical_guard_fraction: float = 1e-10,
) -> MultiplayerAcceptanceAssessment:
    """Apply the frozen unilateral-Pareto and coalition-stress labels."""

    if not isfinite(payoff_span) or payoff_span <= 0.0:
        raise ValueError("payoff span must be positive and finite")
    if (
        not isfinite(numerical_guard_fraction)
        or numerical_guard_fraction < 0.0
        or numerical_guard_fraction > 1e-10
    ):
        raise ValueError("numerical guard fraction must be in [0, 1e-10]")
    if len(source.deviation_gains) != len(candidate.deviation_gains):
        raise ValueError("source and candidate must have the same player count")

    guard = numerical_guard_fraction * payoff_span
    aggregate_improves = candidate.nash_conv < source.nash_conv - guard
    per_player_passes = all(
        candidate_gain <= source_gain + guard
        for source_gain, candidate_gain in zip(
            source.deviation_gains,
            candidate.deviation_gains,
            strict=True,
        )
    )

    source_by_coalition = source_coalitions.by_coalition()
    candidate_by_coalition = candidate_coalitions.by_coalition()
    if source_by_coalition.keys() != candidate_by_coalition.keys():
        raise ValueError("source and candidate coalition sets must match")
    coalition_passes = all(
        candidate_by_coalition[coalition].deviation_gain
        <= source_threat.deviation_gain + guard
        for coalition, source_threat in source_by_coalition.items()
    )
    unilateral_accept = aggregate_improves and per_player_passes
    return MultiplayerAcceptanceAssessment(
        numerical_guard=guard,
        aggregate_nash_conv_strictly_decreases=aggregate_improves,
        no_player_deviation_gain_increases=per_player_passes,
        no_coalition_deviation_gain_increases=coalition_passes,
        unilateral_pareto_accept=unilateral_accept,
        coalition_stress_accept=unilateral_accept and coalition_passes,
    )
