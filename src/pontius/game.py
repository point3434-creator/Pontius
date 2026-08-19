"""Minimal interfaces for finite extensive-form games with perfect recall."""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from typing import Protocol, TypeAlias

Action: TypeAlias = Hashable
CHANCE_PLAYER = -1
TERMINAL_PLAYER = -2


class GameState(Protocol):
    """Immutable state used by exact traversal algorithms."""

    @property
    def current_player(self) -> int:
        """Player index, ``CHANCE_PLAYER``, or ``TERMINAL_PLAYER``."""

    def legal_actions(self) -> Sequence[Action]:
        """Return legal player actions at a nonterminal decision state."""

    def chance_outcomes(self) -> Sequence[tuple[Action, float]]:
        """Return ``(outcome, probability)`` pairs at a chance state."""

    def apply_action(self, action: Action) -> GameState:
        """Return the immutable child state reached by ``action``."""

    def information_state_key(self, player: int) -> str:
        """Return a stable perfect-recall information-set key."""

    def returns(self) -> tuple[float, ...]:
        """Return terminal utilities for every player."""


class ExtensiveFormGame(Protocol):
    """Factory and metadata for a finite extensive-form game."""

    @property
    def num_players(self) -> int:
        """Number of strategic players."""

    def initial_state(self) -> GameState:
        """Return the root state."""

