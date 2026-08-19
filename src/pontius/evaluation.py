"""Exact policy evaluation and brute-force best responses for small games."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import prod
from typing import TypeAlias

from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState

Policy: TypeAlias = dict[str, dict[Action, float]]


def _distribution(
    policy: Policy,
    information_key: str,
    actions: tuple[Action, ...],
) -> dict[Action, float]:
    """Return a validated normalized distribution, defaulting to uniform."""

    supplied = policy.get(information_key)
    if supplied is None:
        probability = 1.0 / len(actions)
        return {action: probability for action in actions}

    unknown = set(supplied) - set(actions)
    if unknown:
        raise ValueError(f"policy for {information_key!r} contains illegal actions: {unknown!r}")
    weights = {action: float(supplied.get(action, 0.0)) for action in actions}
    if any(weight < 0.0 for weight in weights.values()):
        raise ValueError(f"policy for {information_key!r} contains a negative probability")
    total = sum(weights.values())
    if total <= 0.0:
        raise ValueError(f"policy for {information_key!r} has zero probability mass")
    return {action: weight / total for action, weight in weights.items()}


def expected_utilities(game: ExtensiveFormGame, policy: Policy) -> tuple[float, ...]:
    """Enumerate the complete tree and return expected utilities."""

    def walk(state: GameState) -> tuple[float, ...]:
        player = state.current_player
        if player == TERMINAL_PLAYER:
            result = state.returns()
            if len(result) != game.num_players:
                raise ValueError("terminal utility count does not match game.num_players")
            return result

        if player == CHANCE_PLAYER:
            outcomes = tuple(state.chance_outcomes())
            probability_sum = sum(probability for _, probability in outcomes)
            if not outcomes or abs(probability_sum - 1.0) > 1e-12:
                raise ValueError(f"invalid chance distribution with mass {probability_sum}")
            values = [0.0] * game.num_players
            for action, probability in outcomes:
                if probability < 0.0:
                    raise ValueError("chance probability cannot be negative")
                child_values = walk(state.apply_action(action))
                for index, value in enumerate(child_values):
                    values[index] += probability * value
            return tuple(values)

        actions = tuple(state.legal_actions())
        if not actions:
            raise ValueError("nonterminal player state has no legal actions")
        key = state.information_state_key(player)
        distribution = _distribution(policy, key, actions)
        values = [0.0] * game.num_players
        for action, probability in distribution.items():
            child_values = walk(state.apply_action(action))
            for index, value in enumerate(child_values):
                values[index] += probability * value
        return tuple(values)

    return walk(game.initial_state())


def collect_information_sets(
    game: ExtensiveFormGame,
    target_player: int,
) -> dict[str, tuple[Action, ...]]:
    """Collect a player's information sets and verify action consistency."""

    if target_player not in range(game.num_players):
        raise ValueError(f"invalid player index {target_player}")
    information_sets: dict[str, tuple[Action, ...]] = {}

    def walk(state: GameState) -> None:
        player = state.current_player
        if player == TERMINAL_PLAYER:
            return
        if player == CHANCE_PLAYER:
            for action, _ in state.chance_outcomes():
                walk(state.apply_action(action))
            return

        actions = tuple(state.legal_actions())
        if player == target_player:
            key = state.information_state_key(player)
            previous = information_sets.setdefault(key, actions)
            if previous != actions:
                raise ValueError(f"inconsistent legal actions in information set {key!r}")
        for action in actions:
            walk(state.apply_action(action))

    walk(game.initial_state())
    return dict(sorted(information_sets.items()))


def best_response(
    game: ExtensiveFormGame,
    policy: Policy,
    player: int,
    *,
    max_pure_policies: int = 1_000_000,
) -> tuple[float, dict[str, Action]]:
    """Compute an exact pure best response by information-set policy enumeration.

    A best response to fixed opponents can be chosen deterministically. This
    deliberately slow algorithm is transparent and exact for the small games in
    the reference laboratory. Larger games will require sequence-form or dynamic
    best-response implementations checked against this result.
    """

    information_sets = collect_information_sets(game, player)
    policy_count = prod(len(actions) for actions in information_sets.values())
    if policy_count > max_pure_policies:
        raise ValueError(
            f"exact best response requires {policy_count} pure policies; "
            f"limit is {max_pure_policies}"
        )

    keys = tuple(information_sets)
    action_spaces = tuple(information_sets[key] for key in keys)
    best_value = float("-inf")
    best_actions: dict[str, Action] = {}

    for selected_actions in product(*action_spaces):
        candidate: Policy = {key: dict(distribution) for key, distribution in policy.items()}
        deterministic = dict(zip(keys, selected_actions, strict=True))
        for key, action in deterministic.items():
            candidate[key] = {candidate_action: float(candidate_action == action) for candidate_action in information_sets[key]}
        value = expected_utilities(game, candidate)[player]
        if value > best_value:
            best_value = value
            best_actions = deterministic

    return best_value, best_actions


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    utilities: tuple[float, ...]
    best_response_values: tuple[float, ...]
    deviation_gains: tuple[float, ...]
    nash_conv: float
    exploitability: float | None


def evaluate_profile(game: ExtensiveFormGame, policy: Policy) -> EvaluationResult:
    """Return exact utilities and unilateral-deviation metrics."""

    utilities = expected_utilities(game, policy)
    best_response_values = tuple(
        best_response(game, policy, player)[0] for player in range(game.num_players)
    )
    deviation_gains = tuple(
        max(0.0, best - utility)
        for best, utility in zip(best_response_values, utilities, strict=True)
    )
    nash_conv = sum(deviation_gains)
    exploitability = nash_conv / 2.0 if game.num_players == 2 else None
    return EvaluationResult(
        utilities=utilities,
        best_response_values=best_response_values,
        deviation_gains=deviation_gains,
        nash_conv=nash_conv,
        exploitability=exploitability,
    )

