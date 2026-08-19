"""Selective-expansion masks and full-policy completion for multi-size rivers."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .evaluation import Policy, collect_information_sets
from .game import Action, ExtensiveFormGame, GameState
from .river_multi_size import (
    BetAction,
    MultiSizeRiverHoldem,
    MultiSizeRiverState,
    RaiseToAction,
)


def multi_size_state_cache_key(state: GameState) -> str:
    """Return a compact concrete-history key for one fixed multi-size game.

    A continuation provider is scoped to one immutable game, so repeating the
    board, full joint range, and structural metadata in ``repr(state)`` is both
    unnecessary and expensive on every hot leaf lookup.
    """

    if not isinstance(state, MultiSizeRiverState):
        raise TypeError("multi-size cache keys require MultiSizeRiverState")
    return repr((state.deal, state.history, state.terminal))


@dataclass(frozen=True, slots=True)
class MultiSizeExpansionMask:
    """Select bet and raise branches to expand without removing any action."""

    structural_digest: str
    expanded_bets: frozenset[BetAction]
    expanded_raises: frozenset[RaiseToAction]

    @classmethod
    def from_amounts(
        cls,
        game: MultiSizeRiverHoldem,
        *,
        bet_amounts: tuple[float, ...],
        raise_to_amounts: tuple[float, ...],
    ) -> MultiSizeExpansionMask:
        bets = frozenset(BetAction(amount) for amount in bet_amounts)
        raises = frozenset(RaiseToAction(amount) for amount in raise_to_amounts)
        unknown_bets = bets - set(game.bet_actions)
        unknown_raises = raises - set(game.raise_actions)
        if unknown_bets or unknown_raises:
            raise ValueError(
                "expansion mask contains actions outside the full game: "
                f"bets={sorted(unknown_bets)!r}, raises={sorted(unknown_raises)!r}"
            )
        return cls(
            structural_digest=game.structural_digest,
            expanded_bets=bets,
            expanded_raises=raises,
        )

    @property
    def expanded_action_count(self) -> int:
        return len(self.expanded_bets) + len(self.expanded_raises)

    def __call__(self, state: GameState, action: Action) -> bool:
        if not isinstance(state, MultiSizeRiverState):
            raise TypeError("multi-size expansion masks require MultiSizeRiverState")
        if state.game.structural_digest != self.structural_digest:
            raise ValueError("expansion mask and game structure do not match")
        if isinstance(action, BetAction):
            return action in self.expanded_bets
        if isinstance(action, RaiseToAction):
            return action in self.expanded_raises
        return True


def complete_information_schema(
    game: ExtensiveFormGame,
) -> dict[str, tuple[Action, ...]]:
    """Collect one complete, player-disjoint information-set schema."""

    schema: dict[str, tuple[Action, ...]] = {}
    for player in range(game.num_players):
        player_schema = collect_information_sets(game, player)
        overlap = set(schema) & set(player_schema)
        if overlap:
            raise ValueError(f"information-set keys are shared across players: {overlap!r}")
        schema.update(player_schema)
    return dict(sorted(schema.items()))


def _validate_complete_distribution(
    *,
    label: str,
    key: str,
    actions: tuple[Action, ...],
    distribution: dict[Action, float],
) -> None:
    if set(distribution) != set(actions):
        raise ValueError(f"{label} policy has an incomplete action schema at {key!r}")
    values = tuple(float(distribution[action]) for action in actions)
    if any(not isfinite(value) or value < 0.0 for value in values):
        raise ValueError(f"{label} policy has invalid probability at {key!r}")
    if abs(sum(values) - 1.0) > 1e-12:
        raise ValueError(f"{label} policy is not normalized at {key!r}")


def compose_selective_policy(
    blueprint: Policy,
    candidate: Policy,
    information_sets: dict[str, tuple[Action, ...]],
) -> Policy:
    """Overlay reached full-action candidate sets and preserve all others exactly."""

    if set(blueprint) != set(information_sets):
        missing = set(information_sets) - set(blueprint)
        unknown = set(blueprint) - set(information_sets)
        raise ValueError(
            "blueprint must be complete in the full game: "
            f"missing={sorted(missing)!r}, unknown={sorted(unknown)!r}"
        )
    unknown_candidate = set(candidate) - set(information_sets)
    if unknown_candidate:
        raise ValueError(
            f"candidate contains unknown information sets: {sorted(unknown_candidate)!r}"
        )

    for key, actions in information_sets.items():
        _validate_complete_distribution(
            label="blueprint",
            key=key,
            actions=actions,
            distribution=blueprint[key],
        )
    for key, distribution in candidate.items():
        _validate_complete_distribution(
            label="candidate",
            key=key,
            actions=information_sets[key],
            distribution=distribution,
        )

    completed = {key: dict(distribution) for key, distribution in blueprint.items()}
    for key, distribution in candidate.items():
        completed[key] = dict(distribution)
    return completed
