"""Independent exact oracle for one open sequence-form policy axis.

This deliberately small-game implementation uses ``Fraction`` throughout.
It neither imports nor calls the production Float64 open-axis traversal.  The
oracle is intended for coefficient differentials, not runtime solving.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping, TypeAlias

from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState


ExactSequenceToken = tuple[str, Action]
Policy: TypeAlias = dict[str, dict[Action, float]]


@dataclass(frozen=True, slots=True)
class ExactSequenceInformationSet:
    key: str
    actions: tuple[Action, ...]
    parent: ExactSequenceToken | None


@dataclass(frozen=True, slots=True)
class ExactSequenceAxis:
    player: int
    information_sets: tuple[ExactSequenceInformationSet, ...]
    variables: tuple[ExactSequenceToken, ...]

    def realization(self, policy: Policy) -> Mapping[ExactSequenceToken, Fraction]:
        values: dict[ExactSequenceToken, Fraction] = {}
        for information_set in self.information_sets:
            parent_mass = (
                Fraction(1)
                if information_set.parent is None
                else values[information_set.parent]
            )
            distribution = _exact_policy_distribution(
                policy,
                information_set.key,
                information_set.actions,
            )
            for action in information_set.actions:
                values[(information_set.key, action)] = (
                    parent_mass * distribution[action]
                )
        if set(values) != set(self.variables):
            raise AssertionError("exact realization did not cover its sequence axis")
        return MappingProxyType(values)


@dataclass(frozen=True, slots=True)
class ExactAffinePayoff:
    constant: Fraction
    coefficients: Mapping[ExactSequenceToken, Fraction]

    def value(
        self,
        realization: Mapping[ExactSequenceToken, Fraction],
    ) -> Fraction:
        if set(realization) != set(self.coefficients):
            raise ValueError("exact realization and affine coefficient axes differ")
        return self.constant + sum(
            (
                coefficient * realization[token]
                for token, coefficient in self.coefficients.items()
            ),
            Fraction(0),
        )

    def subtract(self, other: ExactAffinePayoff) -> ExactAffinePayoff:
        if set(self.coefficients) != set(other.coefficients):
            raise ValueError("exact affine coefficient axes differ")
        return ExactAffinePayoff(
            self.constant - other.constant,
            MappingProxyType(
                {
                    token: value - other.coefficients[token]
                    for token, value in self.coefficients.items()
                }
            ),
        )


def _fraction(value: float) -> Fraction:
    if isinstance(value, bool):
        raise TypeError("Boolean is not an exact probability or payoff")
    return Fraction.from_float(float(value))


def _exact_policy_distribution(
    policy: Policy,
    information_key: str,
    actions: tuple[Action, ...],
) -> Mapping[Action, Fraction]:
    if not actions:
        raise ValueError("exact policy distribution has no actions")
    supplied = policy.get(information_key)
    if supplied is None:
        probability = Fraction(1, len(actions))
        return MappingProxyType({action: probability for action in actions})
    unknown = set(supplied) - set(actions)
    if unknown:
        raise ValueError("exact policy contains an unavailable action")
    weights = {
        action: _fraction(float(supplied.get(action, 0.0))) for action in actions
    }
    if any(value < 0 for value in weights.values()):
        raise ValueError("exact policy contains a negative probability")
    total = sum(weights.values(), Fraction(0))
    if total <= 0:
        raise ValueError("exact policy has zero probability mass")
    return MappingProxyType(
        {action: value / total for action, value in weights.items()}
    )


def exact_sequence_axis(
    game: ExtensiveFormGame,
    player: int,
) -> ExactSequenceAxis:
    """Enumerate one player's perfect-recall sequence axis independently."""

    if isinstance(player, bool) or player not in range(game.num_players):
        raise ValueError("exact sequence-axis player is outside the game")
    schemas: dict[
        str,
        tuple[tuple[Action, ...], ExactSequenceToken | None],
    ] = {}

    def walk(state: GameState, parent: ExactSequenceToken | None) -> None:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            outcomes = tuple(state.chance_outcomes())
            if not outcomes:
                raise ValueError("exact sequence-axis chance node has no outcomes")
            for action, _ in outcomes:
                walk(state.apply_action(action), parent)
            return
        actions = tuple(state.legal_actions())
        if not actions:
            raise ValueError("exact sequence-axis strategic node has no actions")
        if acting == player:
            key = state.information_state_key(player)
            previous = schemas.setdefault(key, (actions, parent))
            if previous != (actions, parent):
                raise ValueError(
                    "exact sequence axis found imperfect recall or action drift"
                )
            for action in actions:
                walk(state.apply_action(action), (key, action))
            return
        for action in actions:
            walk(state.apply_action(action), parent)

    walk(game.initial_state(), None)
    depths: dict[str, int] = {}
    visiting: set[str] = set()

    def depth(key: str) -> int:
        cached = depths.get(key)
        if cached is not None:
            return cached
        if key in visiting:
            raise ValueError("exact sequence-axis parent relation contains a cycle")
        visiting.add(key)
        parent = schemas[key][1]
        result = 0 if parent is None else depth(parent[0]) + 1
        visiting.remove(key)
        depths[key] = result
        return result

    information_sets = tuple(
        ExactSequenceInformationSet(key, schemas[key][0], schemas[key][1])
        for key in sorted(schemas, key=lambda item: (depth(item), item))
    )
    variables = tuple(
        (information_set.key, action)
        for information_set in information_sets
        for action in information_set.actions
    )
    if len(variables) != len(set(variables)):
        raise AssertionError("exact sequence axis contains duplicate variables")
    return ExactSequenceAxis(player, information_sets, variables)


def exact_expected_utilities(
    game: ExtensiveFormGame,
    policy: Policy,
) -> tuple[Fraction, ...]:
    """Enumerate exact utilities under the stored chance and policy floats."""

    def walk(state: GameState) -> tuple[Fraction, ...]:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            returns = tuple(_fraction(value) for value in state.returns())
            if len(returns) != game.num_players:
                raise ValueError("exact terminal utility count differs from game")
            return returns
        if acting == CHANCE_PLAYER:
            outcomes = tuple(state.chance_outcomes())
            probabilities = tuple(_fraction(value) for _, value in outcomes)
            if not outcomes or sum(probabilities, Fraction(0)) != 1:
                raise ValueError("exact chance probabilities do not sum to one")
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
        distribution = _exact_policy_distribution(
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


def exact_open_axis_payoff_coefficients(
    game: ExtensiveFormGame,
    fixed_policy: Policy,
    *,
    acting_player: int,
    payoff_player: int,
) -> ExactAffinePayoff:
    """Accumulate exact terminal mass on each last acting-player sequence."""

    if isinstance(payoff_player, bool) or payoff_player not in range(
        game.num_players
    ):
        raise ValueError("exact open-axis payoff player is outside the game")
    axis = exact_sequence_axis(game, acting_player)
    coefficients = {token: Fraction(0) for token in axis.variables}
    constant = Fraction(0)

    def walk(
        state: GameState,
        fixed_reach: Fraction,
        last_sequence: ExactSequenceToken | None,
    ) -> None:
        nonlocal constant
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            contribution = fixed_reach * _fraction(
                state.returns()[payoff_player]
            )
            if last_sequence is None:
                constant += contribution
            else:
                coefficients[last_sequence] += contribution
            return
        if acting == CHANCE_PLAYER:
            outcomes = tuple(state.chance_outcomes())
            probabilities = tuple(_fraction(value) for _, value in outcomes)
            if not outcomes or sum(probabilities, Fraction(0)) != 1:
                raise ValueError("exact open-axis chance mass differs from one")
            for (action, _), probability in zip(
                outcomes,
                probabilities,
                strict=True,
            ):
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
                if token not in coefficients:
                    raise AssertionError("exact open-axis sequence is off-axis")
                walk(state.apply_action(action), fixed_reach, token)
            return
        distribution = _exact_policy_distribution(
            fixed_policy,
            state.information_state_key(acting),
            actions,
        )
        for action, probability in distribution.items():
            walk(
                state.apply_action(action),
                fixed_reach * probability,
                last_sequence,
            )

    walk(game.initial_state(), Fraction(1), None)
    return ExactAffinePayoff(constant, MappingProxyType(coefficients))


__all__ = [
    "ExactAffinePayoff",
    "ExactSequenceAxis",
    "ExactSequenceInformationSet",
    "ExactSequenceToken",
    "exact_expected_utilities",
    "exact_open_axis_payoff_coefficients",
    "exact_sequence_axis",
]
