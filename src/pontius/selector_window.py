"""Additive Float64 selector-window primitive over immutable response tapes."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import fsum, isfinite
from typing import Mapping

from .evaluation import Policy, policy_distribution
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState


@dataclass(frozen=True, slots=True)
class FixedSelectorInformationSetScores:
    key: str
    actions: tuple[Action, ...]
    player_depth: int
    action_values: tuple[tuple[Action, float], ...]
    selected_action: Action


@dataclass(frozen=True, slots=True)
class FixedResponseSelectorScores:
    player: int
    value: float
    information_sets: tuple[FixedSelectorInformationSetScores, ...]


@dataclass(frozen=True, slots=True)
class ConservativeSelectorWindow:
    scale_limit: float
    first_switch_information_key: str | None
    first_switch_source_action: Action | None
    first_switch_competing_action: Action | None
    selector_comparisons: int
    exact_source_action_ties: int


@dataclass(slots=True)
class _InformationSet:
    actions: tuple[Action, ...]
    player_depth: int
    states: list[tuple[GameState, float]] = field(default_factory=list)


def fixed_response_selector_scores(
    game: ExtensiveFormGame,
    policy: Policy,
    player: int,
    response_tape: Mapping[str, Action],
) -> FixedResponseSelectorScores:
    """Score every local action while following one complete total tape."""

    if isinstance(player, bool) or player not in range(game.num_players):
        raise ValueError("selector-score player is outside the game")
    information_sets: dict[str, _InformationSet] = {}

    def collect(state: GameState, reach: float, player_depth: int) -> None:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            outcomes = tuple(state.chance_outcomes())
            if not outcomes or abs(fsum(value for _, value in outcomes) - 1.0) > 1e-12:
                raise ValueError("selector-score chance mass differs from one")
            for action, probability in outcomes:
                collect(state.apply_action(action), reach * probability, player_depth)
            return
        actions = tuple(state.legal_actions())
        key = state.information_state_key(acting)
        if acting == player:
            entry = information_sets.get(key)
            if entry is None:
                entry = _InformationSet(actions, player_depth)
                information_sets[key] = entry
            elif entry.actions != actions or entry.player_depth != player_depth:
                raise ValueError("selector-score action schema or recall drifted")
            entry.states.append((state, reach))
            for action in actions:
                collect(state.apply_action(action), reach, player_depth + 1)
            return
        distribution = policy_distribution(policy, key, actions)
        for action, probability in distribution.items():
            collect(state.apply_action(action), reach * probability, player_depth)

    collect(game.initial_state(), 1.0, 0)
    if set(response_tape) != set(information_sets):
        raise ValueError("selector-score response tape is incomplete")
    selected = dict(response_tape)

    def continuation(state: GameState) -> float:
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return float(state.returns()[player])
        if acting == CHANCE_PLAYER:
            return fsum(
                probability * continuation(state.apply_action(action))
                for action, probability in state.chance_outcomes()
            )
        actions = tuple(state.legal_actions())
        key = state.information_state_key(acting)
        if acting == player:
            action = selected.get(key)
            if action not in actions:
                raise ValueError("selector-score response tape contains an illegal action")
            return continuation(state.apply_action(action))
        distribution = policy_distribution(policy, key, actions)
        return fsum(
            probability * continuation(state.apply_action(action))
            for action, probability in distribution.items()
        )

    rows = []
    for key, entry in sorted(
        information_sets.items(),
        key=lambda item: (item[1].player_depth, item[0]),
    ):
        action_values = tuple(
            (
                action,
                fsum(
                    reach * continuation(state.apply_action(action))
                    for state, reach in entry.states
                ),
            )
            for action in entry.actions
        )
        if any(not isfinite(value) for _, value in action_values):
            raise ArithmeticError("selector-score action value is not finite")
        rows.append(
            FixedSelectorInformationSetScores(
                key,
                entry.actions,
                entry.player_depth,
                action_values,
                selected[key],
            )
        )
    value = continuation(game.initial_state())
    if not isfinite(value):
        raise ArithmeticError("selector-score response value is not finite")
    return FixedResponseSelectorScores(player, value, tuple(rows))


def conservative_affine_selector_window(
    source: FixedResponseSelectorScores,
    endpoint: FixedResponseSelectorScores,
    *,
    selector_margin_allowance: float,
) -> ConservativeSelectorWindow:
    """Stop strictly before the first conservative fixed-tape action tie."""

    if source.player != endpoint.player:
        raise ValueError("selector-window players differ")
    if not isfinite(selector_margin_allowance) or selector_margin_allowance < 0.0:
        raise ValueError("selector-window allowance must be finite and nonnegative")
    endpoint_rows = {row.key: row for row in endpoint.information_sets}
    if set(endpoint_rows) != {row.key for row in source.information_sets}:
        raise ValueError("selector-window information schemas differ")
    limit = 1.0
    first: tuple[str, Action, Action] | None = None
    comparisons = 0
    exact_ties = 0
    for source_row in source.information_sets:
        endpoint_row = endpoint_rows[source_row.key]
        if (
            source_row.actions != endpoint_row.actions
            or source_row.selected_action != endpoint_row.selected_action
        ):
            raise ValueError("selector-window fixed-tape schemas differ")
        source_values = dict(source_row.action_values)
        endpoint_values = dict(endpoint_row.action_values)
        selected = source_row.selected_action
        for action in source_row.actions:
            if action == selected:
                continue
            comparisons += 1
            margin = source_values[selected] - source_values[action]
            if margin < -selector_margin_allowance:
                raise ArithmeticError("selector-window source action is not maximal")
            if margin == 0.0:
                exact_ties += 1
            closing_slope = (
                endpoint_values[action]
                - source_values[action]
                - endpoint_values[selected]
                + source_values[selected]
            )
            if closing_slope <= 0.0:
                continue
            breakpoint = max(0.0, margin - selector_margin_allowance) / closing_slope
            if breakpoint < limit:
                limit = max(0.0, breakpoint)
                first = (source_row.key, selected, action)
    return ConservativeSelectorWindow(
        scale_limit=min(1.0, max(0.0, limit)),
        first_switch_information_key=None if first is None else first[0],
        first_switch_source_action=None if first is None else first[1],
        first_switch_competing_action=None if first is None else first[2],
        selector_comparisons=comparisons,
        exact_source_action_ties=exact_ties,
    )


__all__ = [
    "ConservativeSelectorWindow",
    "FixedResponseSelectorScores",
    "FixedSelectorInformationSetScores",
    "conservative_affine_selector_window",
    "fixed_response_selector_scores",
]
