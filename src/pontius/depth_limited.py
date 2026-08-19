"""Depth-limited games and deterministic continuation-value perturbations."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from math import sqrt
from typing import Protocol

from .evaluation import Policy, expected_utilities_from_state
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState


class LeafValueProvider(Protocol):
    def __call__(self, state: GameState) -> tuple[float, ...]:
        """Return continuation utilities for one concrete leaf history."""


@dataclass(slots=True)
class PolicyContinuationValues:
    """Exact continuation values under a fixed policy, cached by state key."""

    num_players: int
    policy: Policy
    key: Callable[[GameState], str] = repr
    _cache: dict[str, tuple[float, ...]] = field(default_factory=dict, init=False)

    def __call__(self, state: GameState) -> tuple[float, ...]:
        state_key = self.key(state)
        if state_key not in self._cache:
            self._cache[state_key] = expected_utilities_from_state(
                self.num_players,
                state,
                self.policy,
            )
        return self._cache[state_key]

    @property
    def cache_size(self) -> int:
        return len(self._cache)


@dataclass(frozen=True, slots=True)
class LeafErrorStats:
    leaf_states: int
    scalar_values: int
    rmse: float
    mean_absolute_error: float
    max_absolute_error: float
    per_player_rmse: tuple[float, ...]


@dataclass(slots=True)
class DeterministicPerturbedValues:
    """Add stable bounded pseudo-random error to a leaf-value provider.

    Raw errors are uniform in ``[-scale, scale]``. With ``zero_sum=True`` their
    per-state mean is removed, preserving constant-sum utilities. Realized error
    statistics must be reported because the post-centering maximum can exceed
    ``scale``.
    """

    base: LeafValueProvider
    num_players: int
    scale: float
    seed: int = 0
    zero_sum: bool = True
    key: Callable[[GameState], str] = repr
    _cache: dict[str, tuple[float, ...]] = field(default_factory=dict, init=False)
    _errors: dict[str, tuple[float, ...]] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.num_players < 2:
            raise ValueError("num_players must be at least two")
        if self.scale < 0.0:
            raise ValueError("perturbation scale cannot be negative")

    def _uniform_error(self, state_key: str, player: int) -> float:
        payload = f"{self.seed}|{state_key}|{player}".encode("utf-8")
        integer = int.from_bytes(sha256(payload).digest()[:8], "big")
        unit = (integer + 0.5) / 2**64
        return self.scale * (2.0 * unit - 1.0)

    def __call__(self, state: GameState) -> tuple[float, ...]:
        state_key = self.key(state)
        if state_key in self._cache:
            return self._cache[state_key]

        exact = self.base(state)
        if len(exact) != self.num_players:
            raise ValueError("base leaf value count does not match num_players")
        errors = [self._uniform_error(state_key, player) for player in range(self.num_players)]
        if self.zero_sum:
            mean = sum(errors) / self.num_players
            errors = [error - mean for error in errors]
        error_tuple = tuple(errors)
        perturbed = tuple(value + error for value, error in zip(exact, errors, strict=True))
        self._errors[state_key] = error_tuple
        self._cache[state_key] = perturbed
        return perturbed

    def error_stats(self, states: Sequence[GameState]) -> LeafErrorStats:
        unique: dict[str, GameState] = {self.key(state): state for state in states}
        for state in unique.values():
            self(state)
        errors = [self._errors[state_key] for state_key in unique]
        flat = [error for state_errors in errors for error in state_errors]
        if not flat:
            raise ValueError("cannot calculate error statistics without leaf states")
        per_player = tuple(
            sqrt(sum(values[player] ** 2 for values in errors) / len(errors))
            for player in range(self.num_players)
        )
        return LeafErrorStats(
            leaf_states=len(errors),
            scalar_values=len(flat),
            rmse=sqrt(sum(error * error for error in flat) / len(flat)),
            mean_absolute_error=sum(abs(error) for error in flat) / len(flat),
            max_absolute_error=max(abs(error) for error in flat),
            per_player_rmse=per_player,
        )


@dataclass(frozen=True, slots=True)
class DepthLimitedState:
    """State wrapper that substitutes continuation values at an action depth."""

    base: GameState
    action_depth: int
    depth_limit: int
    leaf_values: LeafValueProvider = field(compare=False, hash=False, repr=False)

    @property
    def is_cutoff(self) -> bool:
        return (
            self.base.current_player != TERMINAL_PLAYER
            and self.action_depth >= self.depth_limit
        )

    @property
    def current_player(self) -> int:
        return TERMINAL_PLAYER if self.is_cutoff else self.base.current_player

    def legal_actions(self) -> Sequence[Action]:
        return () if self.current_player < 0 else self.base.legal_actions()

    def chance_outcomes(self) -> Sequence[tuple[Action, float]]:
        return self.base.chance_outcomes() if self.current_player == CHANCE_PLAYER else ()

    def apply_action(self, action: Action) -> DepthLimitedState:
        acting = self.current_player
        if acting == TERMINAL_PLAYER:
            raise ValueError("cannot act in a terminal depth-limited state")
        increment = 0 if acting == CHANCE_PLAYER else 1
        return DepthLimitedState(
            base=self.base.apply_action(action),
            action_depth=self.action_depth + increment,
            depth_limit=self.depth_limit,
            leaf_values=self.leaf_values,
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
class DepthLimitedGame:
    """Game wrapper that cuts after a fixed number of strategic actions."""

    base_game: ExtensiveFormGame
    depth_limit: int
    leaf_values: LeafValueProvider = field(compare=False, hash=False, repr=False)

    def __post_init__(self) -> None:
        if self.depth_limit < 1:
            raise ValueError("depth_limit must be at least one")

    @property
    def num_players(self) -> int:
        return self.base_game.num_players

    def initial_state(self) -> DepthLimitedState:
        return DepthLimitedState(
            base=self.base_game.initial_state(),
            action_depth=0,
            depth_limit=self.depth_limit,
            leaf_values=self.leaf_values,
        )


def collect_cutoff_states(game: DepthLimitedGame) -> list[GameState]:
    """Enumerate concrete base states at the depth boundary."""

    states: list[GameState] = []

    def walk(state: DepthLimitedState) -> None:
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
    return states

