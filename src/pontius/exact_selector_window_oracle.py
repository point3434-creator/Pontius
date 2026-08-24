"""Independent Fraction oracle for best-response selectors and fixed tapes.

The oracle deliberately shares no selector implementation with
``pontius.evaluation``.  It is small-game evidence machinery: chance,
opponent reach, action scores, ties, and the final response value remain exact
``Fraction`` objects derived from the stored Float64 game and policy values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping, TypeAlias

from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState


ExactScalar: TypeAlias = float | Fraction
PolicyLike: TypeAlias = Mapping[str, Mapping[Action, ExactScalar]]


@dataclass(frozen=True, slots=True)
class ExactSelectorInformationSetTrace:
    """Exact counterfactual action scores at one information set."""

    key: str
    actions: tuple[Action, ...]
    player_depth: int
    action_values: tuple[tuple[Action, Fraction], ...]
    selected_action: Action
    maximizing_actions: tuple[Action, ...]

    @property
    def selected_is_maximal(self) -> bool:
        return self.selected_action in self.maximizing_actions


@dataclass(frozen=True, slots=True)
class ExactBestResponseTrace:
    """One complete deterministic tape with exact selector evidence."""

    player: int
    value: Fraction
    selected_actions: Mapping[str, Action]
    information_sets: tuple[ExactSelectorInformationSetTrace, ...]


@dataclass(slots=True)
class _InformationSet:
    actions: tuple[Action, ...]
    player_depth: int
    states: list[tuple[GameState, Fraction]] = field(default_factory=list)


def _fraction(value: ExactScalar) -> Fraction:
    if isinstance(value, bool):
        raise TypeError("Boolean is not an exact probability or payoff")
    if isinstance(value, Fraction):
        return value
    return Fraction.from_float(float(value))


def _distribution(
    policy: PolicyLike,
    key: str,
    actions: tuple[Action, ...],
) -> Mapping[Action, Fraction]:
    supplied = policy.get(key)
    if supplied is None:
        probability = Fraction(1, len(actions))
        return MappingProxyType({action: probability for action in actions})
    unknown = set(supplied) - set(actions)
    if unknown:
        raise ValueError("exact selector policy contains an unavailable action")
    weights = {
        action: _fraction(supplied.get(action, 0.0)) for action in actions
    }
    if any(value < 0 for value in weights.values()):
        raise ValueError("exact selector policy contains a negative probability")
    total = sum(weights.values(), Fraction(0))
    if total <= 0:
        raise ValueError("exact selector policy has zero probability mass")
    return MappingProxyType(
        {action: value / total for action, value in weights.items()}
    )


def _collect_information_sets(
    game: ExtensiveFormGame,
    policy: PolicyLike,
    player: int,
) -> dict[str, _InformationSet]:
    information_sets: dict[str, _InformationSet] = {}

    def collect(state: GameState, reach: Fraction, player_depth: int) -> None:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            outcomes = tuple(state.chance_outcomes())
            probabilities = tuple(_fraction(value) for _, value in outcomes)
            if not outcomes or sum(probabilities, Fraction(0)) != 1:
                raise ValueError("exact selector chance mass differs from one")
            for (action, _), probability in zip(
                outcomes,
                probabilities,
                strict=True,
            ):
                collect(state.apply_action(action), reach * probability, player_depth)
            return

        actions = tuple(state.legal_actions())
        if not actions:
            raise ValueError("exact selector found a strategic node without actions")
        key = state.information_state_key(acting)
        if acting == player:
            entry = information_sets.get(key)
            if entry is None:
                entry = _InformationSet(actions, player_depth)
                information_sets[key] = entry
            elif entry.actions != actions or entry.player_depth != player_depth:
                raise ValueError(
                    "exact selector found action drift or imperfect recall"
                )
            entry.states.append((state, reach))
            for action in actions:
                collect(state.apply_action(action), reach, player_depth + 1)
            return

        distribution = _distribution(policy, key, actions)
        for action, probability in distribution.items():
            collect(
                state.apply_action(action),
                reach * probability,
                player_depth,
            )

    collect(game.initial_state(), Fraction(1), 0)
    return information_sets


def _solve_trace(
    game: ExtensiveFormGame,
    policy: PolicyLike,
    player: int,
    fixed_actions: Mapping[str, Action] | None,
) -> ExactBestResponseTrace:
    if isinstance(player, bool) or player not in range(game.num_players):
        raise ValueError("exact selector player is outside the game")
    information_sets = _collect_information_sets(game, policy, player)
    if fixed_actions is not None and set(fixed_actions) != set(information_sets):
        raise ValueError("fixed exact response tape does not cover its information sets")

    selected: dict[str, Action] = {} if fixed_actions is None else dict(fixed_actions)
    traces: dict[str, ExactSelectorInformationSetTrace] = {}

    def continuation_value(state: GameState) -> Fraction:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return _fraction(state.returns()[player])
        if acting == CHANCE_PLAYER:
            outcomes = tuple(state.chance_outcomes())
            probabilities = tuple(_fraction(value) for _, value in outcomes)
            if not outcomes or sum(probabilities, Fraction(0)) != 1:
                raise ValueError("exact selector chance mass differs from one")
            return sum(
                (
                    probability * continuation_value(state.apply_action(action))
                    for (action, _), probability in zip(
                        outcomes,
                        probabilities,
                        strict=True,
                    )
                ),
                Fraction(0),
            )

        actions = tuple(state.legal_actions())
        key = state.information_state_key(acting)
        if acting == player:
            try:
                action = selected[key]
            except KeyError as exc:
                raise ValueError(
                    "exact selector dependency was not solved bottom-up"
                ) from exc
            if action not in actions:
                raise ValueError("fixed exact response tape contains an illegal action")
            return continuation_value(state.apply_action(action))

        distribution = _distribution(policy, key, actions)
        return sum(
            (
                probability * continuation_value(state.apply_action(action))
                for action, probability in distribution.items()
            ),
            Fraction(0),
        )

    ordered = sorted(
        information_sets.items(),
        key=lambda item: (item[1].player_depth, item[0]),
        reverse=True,
    )
    for key, entry in ordered:
        action_values = tuple(
            (
                action,
                sum(
                    (
                        reach * continuation_value(state.apply_action(action))
                        for state, reach in entry.states
                    ),
                    Fraction(0),
                ),
            )
            for action in entry.actions
        )
        maximum = max(value for _, value in action_values)
        maximizing = tuple(
            action for action, value in action_values if value == maximum
        )
        if fixed_actions is None:
            selected[key] = maximizing[0]
        elif selected[key] not in entry.actions:
            raise ValueError("fixed exact response tape contains an illegal action")
        traces[key] = ExactSelectorInformationSetTrace(
            key=key,
            actions=entry.actions,
            player_depth=entry.player_depth,
            action_values=action_values,
            selected_action=selected[key],
            maximizing_actions=maximizing,
        )

    value = continuation_value(game.initial_state())
    return ExactBestResponseTrace(
        player=player,
        value=value,
        selected_actions=MappingProxyType(dict(sorted(selected.items()))),
        information_sets=tuple(
            traces[key]
            for key in sorted(
                traces,
                key=lambda item: (
                    information_sets[item].player_depth,
                    item,
                ),
            )
        ),
    )


def exact_best_response_trace(
    game: ExtensiveFormGame,
    policy: PolicyLike,
    player: int,
) -> ExactBestResponseTrace:
    """Select the first legal-order maximizer at every exact information set."""

    return _solve_trace(game, policy, player, None)


def exact_fixed_response_trace(
    game: ExtensiveFormGame,
    policy: PolicyLike,
    player: int,
    response_tape: Mapping[str, Action],
) -> ExactBestResponseTrace:
    """Score every action while following one complete immutable response tape."""

    return _solve_trace(game, policy, player, response_tape)


def exact_policy_utilities(
    game: ExtensiveFormGame,
    policy: PolicyLike,
) -> tuple[Fraction, ...]:
    """Enumerate one complete profile under Fraction-aware policy rows."""

    def walk(state: GameState) -> tuple[Fraction, ...]:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            values = tuple(_fraction(value) for value in state.returns())
            if len(values) != game.num_players:
                raise ValueError("exact selector utility width differs from game")
            return values
        if acting == CHANCE_PLAYER:
            outcomes = tuple(state.chance_outcomes())
            probabilities = tuple(_fraction(value) for _, value in outcomes)
            if not outcomes or sum(probabilities, Fraction(0)) != 1:
                raise ValueError("exact selector chance mass differs from one")
            result = [Fraction(0)] * game.num_players
            for (action, _), probability in zip(
                outcomes,
                probabilities,
                strict=True,
            ):
                child = walk(state.apply_action(action))
                for player, value in enumerate(child):
                    result[player] += probability * value
            return tuple(result)
        actions = tuple(state.legal_actions())
        distribution = _distribution(
            policy,
            state.information_state_key(acting),
            actions,
        )
        result = [Fraction(0)] * game.num_players
        for action, probability in distribution.items():
            child = walk(state.apply_action(action))
            for player, value in enumerate(child):
                result[player] += probability * value
        return tuple(result)

    return walk(game.initial_state())


__all__ = [
    "ExactBestResponseTrace",
    "ExactSelectorInformationSetTrace",
    "exact_best_response_trace",
    "exact_fixed_response_trace",
    "exact_policy_utilities",
]
