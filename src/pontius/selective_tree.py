"""Full-action selective tree expansion with fixed-policy continuation leaves."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TypeAlias

from .depth_limited import LeafValueProvider
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState

ExpansionSelector: TypeAlias = Callable[[GameState, Action], bool]


@dataclass(frozen=True, slots=True)
class SelectiveExpansionState:
    """State wrapper that cuts only unexpanded nonterminal action branches.

    The acting information set always exposes the base game's complete legal
    action tuple. An unexpanded action is therefore still selectable; only its
    descendants are replaced by a fixed continuation value.
    """

    base: GameState
    leaf_values: LeafValueProvider = field(compare=False, hash=False, repr=False)
    expand_action: ExpansionSelector = field(compare=False, hash=False, repr=False)
    is_cutoff: bool = False

    @property
    def current_player(self) -> int:
        return TERMINAL_PLAYER if self.is_cutoff else self.base.current_player

    def legal_actions(self) -> Sequence[Action]:
        return () if self.current_player < 0 else self.base.legal_actions()

    def chance_outcomes(self) -> Sequence[tuple[Action, float]]:
        return self.base.chance_outcomes() if self.current_player == CHANCE_PLAYER else ()

    def apply_action(self, action: Action) -> SelectiveExpansionState:
        acting = self.current_player
        if acting == TERMINAL_PLAYER:
            raise ValueError("cannot act in a terminal selective-expansion state")

        child = self.base.apply_action(action)
        cutoff = False
        if acting != CHANCE_PLAYER and child.current_player != TERMINAL_PLAYER:
            cutoff = not self.expand_action(self.base, action)
        return SelectiveExpansionState(
            base=child,
            leaf_values=self.leaf_values,
            expand_action=self.expand_action,
            is_cutoff=cutoff,
        )

    def information_state_key(self, player: int) -> str:
        return self.base.information_state_key(player)

    def returns(self) -> tuple[float, ...]:
        if self.base.current_player == TERMINAL_PLAYER:
            return self.base.returns()
        if not self.is_cutoff:
            raise ValueError("returns are available only at terminal or cutoff states")
        return self.leaf_values(self.base)


@dataclass(frozen=True, slots=True)
class SelectiveExpansionGame:
    """Game wrapper retaining all actions while selectively expanding branches."""

    base_game: ExtensiveFormGame
    leaf_values: LeafValueProvider = field(compare=False, hash=False, repr=False)
    expand_action: ExpansionSelector = field(compare=False, hash=False, repr=False)

    @property
    def num_players(self) -> int:
        return self.base_game.num_players

    def initial_state(self) -> SelectiveExpansionState:
        return SelectiveExpansionState(
            base=self.base_game.initial_state(),
            leaf_values=self.leaf_values,
            expand_action=self.expand_action,
        )


def collect_selective_cutoff_states(
    game: SelectiveExpansionGame,
) -> tuple[GameState, ...]:
    """Enumerate concrete base states replaced by continuation values."""

    states: list[GameState] = []

    def walk(state: SelectiveExpansionState) -> None:
        if state.is_cutoff:
            states.append(state.base)
            return
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            for action, _ in state.chance_outcomes():
                walk(state.apply_action(action))
            return
        for action in state.legal_actions():
            walk(state.apply_action(action))

    walk(game.initial_state())
    return tuple(states)


def full_tree_state_count(state: GameState) -> int:
    """Count every concrete state visited by one complete tree traversal."""

    acting = state.current_player
    if acting == TERMINAL_PLAYER:
        return 1
    if acting == CHANCE_PLAYER:
        children = (state.apply_action(action) for action, _ in state.chance_outcomes())
    else:
        children = (state.apply_action(action) for action in state.legal_actions())
    return 1 + sum(full_tree_state_count(child) for child in children)

