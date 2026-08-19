"""Transparent full-tree alternating CFR and Linear CFR baselines."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import prod
from typing import Callable, Literal, TypeAlias

from .evaluation import Policy
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState

SolverVariant: TypeAlias = Literal["cfr", "lcfr"]


@dataclass(slots=True)
class InformationSetData:
    actions: tuple[Action, ...]
    regrets: dict[Action, float] = field(default_factory=dict)
    strategy_sum: dict[Action, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.regrets:
            self.regrets = {action: 0.0 for action in self.actions}
        if not self.strategy_sum:
            self.strategy_sum = {action: 0.0 for action in self.actions}


class TabularCFR:
    """Full-tree alternating CFR for finite perfect-recall games.

    The implementation favors auditable equations over speed. During one
    traverser's update, strategies are cached per information set so every
    underlying history uses the same behavioral strategy. Regret updates are
    weighted by chance and opponents' reach; average policies are weighted by
    the acting player's own reach.
    """

    def __init__(self, game: ExtensiveFormGame, variant: SolverVariant = "cfr") -> None:
        if variant not in {"cfr", "lcfr"}:
            raise ValueError(f"unsupported CFR variant: {variant!r}")
        self.game = game
        self.variant = variant
        self.iteration = 0
        self.information_sets: dict[str, InformationSetData] = {}

    def _data(self, key: str, actions: tuple[Action, ...]) -> InformationSetData:
        data = self.information_sets.get(key)
        if data is None:
            data = InformationSetData(actions)
            self.information_sets[key] = data
        elif data.actions != actions:
            raise ValueError(f"inconsistent actions for information set {key!r}")
        return data

    @staticmethod
    def _regret_matching(data: InformationSetData) -> dict[Action, float]:
        positive = {action: max(0.0, regret) for action, regret in data.regrets.items()}
        total = sum(positive.values())
        if total <= 0.0:
            probability = 1.0 / len(data.actions)
            return {action: probability for action in data.actions}
        return {action: positive[action] / total for action in data.actions}

    def _weight(self) -> float:
        return float(self.iteration) if self.variant == "lcfr" else 1.0

    def step(self) -> None:
        """Run one alternating update for every player."""

        self.iteration += 1
        for traverser in range(self.game.num_players):
            strategy_cache: dict[str, dict[Action, float]] = {}
            average_seen: set[str] = set()
            self._traverse(
                self.game.initial_state(),
                traverser,
                reach=(1.0,) * self.game.num_players,
                chance_reach=1.0,
                strategy_cache=strategy_cache,
                average_seen=average_seen,
            )

    def run(
        self,
        iterations: int,
        callback: Callable[[TabularCFR], None] | None = None,
    ) -> None:
        if iterations < 0:
            raise ValueError("iterations cannot be negative")
        for _ in range(iterations):
            self.step()
            if callback is not None:
                callback(self)

    def _traverse(
        self,
        state: GameState,
        traverser: int,
        reach: tuple[float, ...],
        chance_reach: float,
        strategy_cache: dict[str, dict[Action, float]],
        average_seen: set[str],
    ) -> float:
        player = state.current_player
        if player == TERMINAL_PLAYER:
            return state.returns()[traverser]

        if player == CHANCE_PLAYER:
            value = 0.0
            outcomes = tuple(state.chance_outcomes())
            if abs(sum(probability for _, probability in outcomes) - 1.0) > 1e-12:
                raise ValueError("chance probabilities must sum to one")
            for action, probability in outcomes:
                value += probability * self._traverse(
                    state.apply_action(action),
                    traverser,
                    reach,
                    chance_reach * probability,
                    strategy_cache,
                    average_seen,
                )
            return value

        actions = tuple(state.legal_actions())
        key = state.information_state_key(player)
        data = self._data(key, actions)
        strategy = strategy_cache.setdefault(key, self._regret_matching(data))

        if player == traverser and key not in average_seen:
            average_seen.add(key)
            strategy_weight = self._weight() * reach[player]
            for action in actions:
                data.strategy_sum[action] += strategy_weight * strategy[action]

        action_values: dict[Action, float] = {}
        node_value = 0.0
        for action in actions:
            child_reach = list(reach)
            child_reach[player] *= strategy[action]
            action_value = self._traverse(
                state.apply_action(action),
                traverser,
                tuple(child_reach),
                chance_reach,
                strategy_cache,
                average_seen,
            )
            action_values[action] = action_value
            node_value += strategy[action] * action_value

        if player == traverser:
            counterfactual_reach = chance_reach * prod(
                reach[opponent]
                for opponent in range(self.game.num_players)
                if opponent != traverser
            )
            regret_weight = self._weight() * counterfactual_reach
            for action in actions:
                data.regrets[action] += regret_weight * (action_values[action] - node_value)

        return node_value

    def current_strategy(self) -> Policy:
        return {
            key: self._regret_matching(data)
            for key, data in sorted(self.information_sets.items())
        }

    def average_strategy(self) -> Policy:
        policy: Policy = {}
        for key, data in sorted(self.information_sets.items()):
            total = sum(data.strategy_sum.values())
            if total <= 0.0:
                policy[key] = self._regret_matching(data)
            else:
                policy[key] = {
                    action: data.strategy_sum[action] / total for action in data.actions
                }
        return policy

