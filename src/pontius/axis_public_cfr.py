"""CFR accumulator state on external hand axes and a public-tree topology.

``PublicTreeTensorCFR`` derives its hand axes from a materialized joint-deal
table.  Wide factor beliefs intentionally have no such table.  This additive
state container binds the same public nodes to caller-supplied hand axes,
retaining literal per-infoset regret and average-policy accumulators without a
deal-dependent array.
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from .evaluation import Policy, policy_distribution
from .game import Action, TERMINAL_PLAYER
from .incremental_policy_tt import PolicyProbabilityTape
from .public_policy_tt import _information_key
from .public_tree_tensor import PublicTreeTensorEvaluator
from .river import HoleCards
from .updates import CFRUpdateRule, SolverVariant, update_rule


class AxisPublicCFRState:
    """Regrets and average policies for public nodes on external hand axes."""

    def __init__(
        self,
        layout: PublicTreeTensorEvaluator,
        hands_by_player: tuple[tuple[HoleCards, ...], ...],
        variant: SolverVariant = "cfr",
    ) -> None:
        if not isinstance(layout, PublicTreeTensorEvaluator):
            raise TypeError("axis CFR requires a public-tree tensor topology")
        if len(hands_by_player) != layout.num_players or any(
            not hands for hands in hands_by_player
        ):
            raise ValueError("axis CFR requires one nonempty hand axis per player")
        if any(len(set(hands)) != len(hands) for hands in hands_by_player):
            raise ValueError("axis CFR private-hand axes must be unique")
        if any(
            child <= parent
            for parent, node in enumerate(layout.nodes)
            for child in node.children
        ):
            raise ValueError("axis CFR public children must follow their parents")

        self.layout = layout
        self.hands_by_player = tuple(tuple(hands) for hands in hands_by_player)
        self.num_players = layout.num_players
        self.update_rule: CFRUpdateRule = update_rule(variant)
        self.variant = self.update_rule.name
        self.iteration = 0
        self._warm_started = False

        regrets = []
        strategy_sums = []
        keys_by_node = []
        key_locations: dict[str, tuple[int, int]] = {}
        nodes_by_player = [[] for _ in range(self.num_players)]
        for node_index, node in enumerate(layout.nodes):
            if node.player == TERMINAL_PLAYER:
                regrets.append(None)
                strategy_sums.append(None)
                keys_by_node.append(())
                continue
            keys = tuple(
                _information_key(layout, node.player, hand, node.history)
                for hand in self.hands_by_player[node.player]
            )
            shape = (len(keys), len(node.actions))
            regrets.append(np.zeros(shape, dtype=np.float64, order="C"))
            strategy_sums.append(np.zeros(shape, dtype=np.float64, order="C"))
            keys_by_node.append(keys)
            nodes_by_player[node.player].append(node_index)
            for hand_index, key in enumerate(keys):
                if key in key_locations:
                    raise ValueError("axis CFR information set occurs at two nodes")
                key_locations[key] = (node_index, hand_index)

        self._regrets = tuple(regrets)
        self._strategy_sums = tuple(strategy_sums)
        self._keys_by_node = tuple(keys_by_node)
        self._key_locations = dict(sorted(key_locations.items()))
        self._nodes_by_player = tuple(tuple(rows) for rows in nodes_by_player)

    @staticmethod
    def _regret_matching(regrets: np.ndarray) -> np.ndarray:
        positive = np.maximum(regrets, 0.0)
        totals = np.sum(positive, axis=1)
        result = np.full_like(positive, 1.0 / positive.shape[1])
        supported = totals > 0.0
        if np.any(supported):
            result[supported] = positive[supported] / totals[supported, None]
        return np.ascontiguousarray(result, dtype=np.float64)

    def _strategies(self) -> tuple[np.ndarray | None, ...]:
        return tuple(
            None if regrets is None else self._regret_matching(regrets)
            for regrets in self._regrets
        )

    def immutable_strategies(self) -> PolicyProbabilityTape:
        result = []
        for values in self._strategies():
            if values is None:
                result.append(None)
                continue
            retained = np.ascontiguousarray(values, dtype=np.float64)
            retained.flags.writeable = False
            result.append(retained)
        return tuple(result)

    def information_schema(self) -> dict[str, tuple[Action, ...]]:
        return {
            key: self.layout.nodes[node_index].actions
            for key, (node_index, _) in self._key_locations.items()
        }

    def warm_start(self, policy: Policy, regret_mass: float) -> None:
        if self.iteration != 0 or self._warm_started:
            raise ValueError("warm_start must be called before the first iteration")
        if not np.isfinite(regret_mass) or regret_mass <= 0.0:
            raise ValueError("regret_mass must be finite and positive")
        prepared = []
        for node_index, node in enumerate(self.layout.nodes):
            regrets = self._regrets[node_index]
            if regrets is None:
                continue
            values = np.empty_like(regrets)
            for hand_index, key in enumerate(self._keys_by_node[node_index]):
                distribution = policy_distribution(policy, key, node.actions)
                values[hand_index] = tuple(
                    distribution[action] for action in node.actions
                )
            prepared.append((regrets, values))
        for regrets, values in prepared:
            regrets[:] = regret_mass * values
        self._warm_started = True

    def accumulate_average_for_traverser(
        self,
        traverser: int,
        probabilities: PolicyProbabilityTape,
    ) -> None:
        if traverser not in range(self.num_players):
            raise ValueError("axis CFR traverser is outside player seats")
        own_reach = np.empty(
            (self.layout.public_node_count, len(self.hands_by_player[traverser])),
            dtype=np.float64,
            order="C",
        )
        own_reach[0].fill(1.0)
        for node_index, node in enumerate(self.layout.nodes):
            if node.player == TERMINAL_PLAYER:
                continue
            strategy = probabilities[node_index]
            if strategy is None:
                raise ValueError("axis CFR strategic node has no probabilities")
            if node.player == traverser:
                strategy_sum = self._strategy_sums[node_index]
                if strategy_sum is None:
                    raise AssertionError("axis CFR node has no strategy sum")
                strategy_sum += own_reach[node_index, :, None] * strategy
                for action_index, child in enumerate(node.children):
                    own_reach[child] = own_reach[node_index] * strategy[:, action_index]
            else:
                for child in node.children:
                    own_reach[child] = own_reach[node_index]

    def apply_regret_deltas(
        self,
        rows: tuple[tuple[int, np.ndarray], ...],
    ) -> None:
        for node_index, delta in rows:
            regrets = self._regrets[node_index]
            if regrets is None or delta.shape != regrets.shape:
                raise ValueError("axis CFR regret delta shape or node is invalid")
            regrets += delta
            if self.update_rule.clip_regrets:
                np.maximum(regrets, 0.0, out=regrets)

    def _discount_accumulators(self) -> None:
        rule = self.update_rule
        if rule.positive_alpha is not None or rule.negative_beta is not None:
            positive_factor = (
                1.0
                if rule.positive_alpha is None
                else rule._power_discount(self.iteration, rule.positive_alpha)
            )
            negative_factor = (
                1.0
                if rule.negative_beta is None
                else rule._power_discount(self.iteration, rule.negative_beta)
            )
            for regrets in self._regrets:
                if regrets is None:
                    continue
                nonnegative = regrets >= 0.0
                regrets[nonnegative] *= positive_factor
                regrets[~nonnegative] *= negative_factor
        if rule.average_gamma is not None:
            factor = (
                float(self.iteration) / (float(self.iteration) + 1.0)
            ) ** rule.average_gamma
            for strategy_sum in self._strategy_sums:
                if strategy_sum is not None:
                    strategy_sum *= factor

    def run(
        self,
        iterations: int,
        callback: Callable[["AxisPublicCFRState"], None] | None = None,
    ) -> None:
        if iterations < 0:
            raise ValueError("iterations cannot be negative")
        for _ in range(iterations):
            self.step()
            if callback is not None:
                callback(self)

    def step(self) -> None:
        raise NotImplementedError("axis CFR state requires an evaluation engine")

    def current_strategy(self) -> Policy:
        return self._policy_from_arrays(self._strategies())

    def average_strategy(self) -> Policy:
        current = self._strategies()
        policy: Policy = {}
        for node_index, node in enumerate(self.layout.nodes):
            sums = self._strategy_sums[node_index]
            if sums is None:
                continue
            fallback = current[node_index]
            if fallback is None:
                raise AssertionError("axis CFR current strategy is absent")
            totals = np.sum(sums, axis=1)
            for hand_index, key in enumerate(self._keys_by_node[node_index]):
                values = (
                    fallback[hand_index]
                    if totals[hand_index] <= 0.0
                    else sums[hand_index] / totals[hand_index]
                )
                policy[key] = {
                    action: float(values[action_index])
                    for action_index, action in enumerate(node.actions)
                }
        return dict(sorted(policy.items()))

    def regret_table(self) -> dict[str, dict[Action, float]]:
        return self._accumulator_table(self._regrets)

    def strategy_sum_table(self) -> dict[str, dict[Action, float]]:
        return self._accumulator_table(self._strategy_sums)

    def _policy_from_arrays(
        self,
        arrays: tuple[np.ndarray | None, ...],
    ) -> Policy:
        policy: Policy = {}
        for node_index, node in enumerate(self.layout.nodes):
            values = arrays[node_index]
            if values is None:
                continue
            for hand_index, key in enumerate(self._keys_by_node[node_index]):
                policy[key] = {
                    action: float(values[hand_index, action_index])
                    for action_index, action in enumerate(node.actions)
                }
        return dict(sorted(policy.items()))

    def _accumulator_table(
        self,
        arrays: tuple[np.ndarray | None, ...],
    ) -> dict[str, dict[Action, float]]:
        table = {}
        for node_index, node in enumerate(self.layout.nodes):
            values = arrays[node_index]
            if values is None:
                continue
            for hand_index, key in enumerate(self._keys_by_node[node_index]):
                table[key] = {
                    action: float(values[hand_index, action_index])
                    for action_index, action in enumerate(node.actions)
                }
        return dict(sorted(table.items()))

    def accumulator_numeric_bytes(self) -> int:
        return sum(
            values.nbytes
            for arrays in (self._regrets, self._strategy_sums)
            for values in arrays
            if values is not None
        )
