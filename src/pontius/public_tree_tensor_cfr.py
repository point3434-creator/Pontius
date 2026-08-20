"""Vectorized alternating CFR on the exact multiway-river public quotient.

The generic :class:`pontius.cfr.TabularCFR` deliberately walks every private
deal and public history.  In ``MultiwayRiverHoldem`` every private deal shares
one public betting tree, so the same equations can instead be evaluated over a
contiguous deal axis.  Regret and average-policy accumulators remain literal at
every ``(public node, own hand, action)`` information set.

This module is a source-policy generator, not an online solver and not a claim
of multiplayer safety.  Its purpose is to produce exactly the same alternating
CFR trajectory as the transparent traversal without paying for Python
recursion once per joint deal.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
from numpy.typing import NDArray

from .evaluation import Policy, policy_distribution
from .game import Action, TERMINAL_PLAYER
from .public_tree_tensor import PublicTreeTensorEvaluator
from .updates import CFRUpdateRule, SolverVariant, update_rule

FloatArray = NDArray[np.float64]


class PublicTreeTensorCFR:
    """Exact alternating CFR over one compiled public-tree deal tensor.

    Only the traversal schedule is changed relative to ``TabularCFR``.  A
    traverser's counterfactual reach and continuation values are dense arrays
    over ``(public node, joint deal)``.  Regrets and strategy sums are much
    smaller arrays over the acting player's marginal hand axis.
    """

    def __init__(
        self,
        layout: PublicTreeTensorEvaluator,
        variant: SolverVariant = "cfr",
    ) -> None:
        if not isinstance(layout, PublicTreeTensorEvaluator):
            raise TypeError("public tensor CFR requires PublicTreeTensorEvaluator")
        if any(
            child <= parent
            for parent, node in enumerate(layout.nodes)
            for child in node.children
        ):
            raise ValueError("public-tree children must follow their parents")

        self.layout = layout
        self.num_players = layout.num_players
        self.update_rule: CFRUpdateRule = update_rule(variant)
        self.variant = self.update_rule.name
        self.iteration = 0
        self._warm_started = False

        regrets: list[FloatArray | None] = []
        strategy_sums: list[FloatArray | None] = []
        key_locations: dict[str, tuple[int, int]] = {}
        nodes_by_player: list[list[int]] = [
            [] for _ in range(self.num_players)
        ]
        for node_index, node in enumerate(layout.nodes):
            if node.player == TERMINAL_PLAYER:
                regrets.append(None)
                strategy_sums.append(None)
                continue
            hand_count = len(layout.hands_by_player[node.player])
            if len(node.information_keys) != hand_count:
                raise ValueError("public node does not cover its complete hand axis")
            shape = (hand_count, len(node.actions))
            regrets.append(np.zeros(shape, dtype=np.float64, order="C"))
            strategy_sums.append(np.zeros(shape, dtype=np.float64, order="C"))
            nodes_by_player[node.player].append(node_index)
            for hand_index, key in enumerate(node.information_keys):
                if key in key_locations:
                    raise ValueError("information set occurs at multiple public nodes")
                key_locations[key] = (node_index, hand_index)

        if set(key_locations) != set(layout.information_schema()):
            raise ValueError("public tensor CFR information schema is incomplete")
        self._regrets = tuple(regrets)
        self._strategy_sums = tuple(strategy_sums)
        self._key_locations = dict(sorted(key_locations.items()))
        self._nodes_by_player = tuple(tuple(rows) for rows in nodes_by_player)

    @staticmethod
    def _regret_matching(regrets: FloatArray) -> FloatArray:
        positive = np.maximum(regrets, 0.0)
        totals = np.sum(positive, axis=1)
        result = np.full_like(positive, 1.0 / positive.shape[1])
        supported = totals > 0.0
        if np.any(supported):
            result[supported] = positive[supported] / totals[supported, None]
        return np.ascontiguousarray(result, dtype=np.float64)

    def _strategies(self) -> tuple[FloatArray | None, ...]:
        return tuple(
            None if regrets is None else self._regret_matching(regrets)
            for regrets in self._regrets
        )

    def warm_start(self, policy: Policy, regret_mass: float) -> None:
        """Set an explicit pseudo-regret prior before the first iteration."""

        if self.iteration != 0 or self._warm_started:
            raise ValueError("warm_start must be called before the first iteration")
        if not np.isfinite(regret_mass) or regret_mass <= 0.0:
            raise ValueError("regret_mass must be finite and positive")

        prepared: list[tuple[FloatArray, FloatArray]] = []
        for node_index, node in enumerate(self.layout.nodes):
            regrets = self._regrets[node_index]
            if regrets is None:
                continue
            values = np.empty_like(regrets)
            for hand_index, key in enumerate(node.information_keys):
                distribution = policy_distribution(policy, key, node.actions)
                values[hand_index] = tuple(
                    distribution[action] for action in node.actions
                )
            prepared.append((regrets, values))
        for regrets, values in prepared:
            regrets[:] = regret_mass * values
        self._warm_started = True

    def step(self) -> None:
        """Run one exact alternating update for every player."""

        self.iteration += 1
        node_count = self.layout.public_node_count
        deal_count = self.layout.deal_count
        counterfactual_reach = np.empty(
            (node_count, deal_count), dtype=np.float64, order="C"
        )
        continuation = np.empty(
            (node_count, deal_count), dtype=np.float64, order="C"
        )

        for traverser in range(self.num_players):
            strategies = self._strategies()
            own_hand_count = len(self.layout.hands_by_player[traverser])
            own_reach = np.empty(
                (node_count, own_hand_count), dtype=np.float64, order="C"
            )
            own_reach[0].fill(1.0)
            counterfactual_reach[0] = self.layout.weights

            # One topological pass supplies both reach notions.  Counterfactual
            # reach omits the traverser's actions; own reach contains only them.
            for node_index, node in enumerate(self.layout.nodes):
                if node.player == TERMINAL_PLAYER:
                    continue
                strategy = strategies[node_index]
                assert strategy is not None
                actor_hand_ids = self.layout.hand_ids[:, node.player]
                if node.player == traverser:
                    strategy_sum = self._strategy_sums[node_index]
                    assert strategy_sum is not None
                    strategy_sum += own_reach[node_index, :, None] * strategy
                    for action_index, child in enumerate(node.children):
                        counterfactual_reach[child] = counterfactual_reach[node_index]
                        own_reach[child] = (
                            own_reach[node_index] * strategy[:, action_index]
                        )
                else:
                    for action_index, child in enumerate(node.children):
                        counterfactual_reach[child] = (
                            counterfactual_reach[node_index]
                            * strategy[actor_hand_ids, action_index]
                        )
                        own_reach[child] = own_reach[node_index]

            regret_deltas: list[tuple[int, FloatArray]] = []
            target_hand_ids = self.layout.hand_ids[:, traverser]
            for node_index in range(node_count - 1, -1, -1):
                node = self.layout.nodes[node_index]
                if node.player == TERMINAL_PLAYER:
                    continuation[node_index] = self.layout.terminal_values[
                        node.terminal_slot, :, traverser
                    ]
                    continue

                strategy = strategies[node_index]
                assert strategy is not None
                actor_hand_ids = self.layout.hand_ids[:, node.player]
                continuation[node_index].fill(0.0)
                for action_index, child in enumerate(node.children):
                    continuation[node_index] += (
                        strategy[actor_hand_ids, action_index]
                        * continuation[child]
                    )

                if node.player != traverser:
                    continue
                delta = np.empty_like(strategy)
                for action_index, child in enumerate(node.children):
                    delta[:, action_index] = np.bincount(
                        target_hand_ids,
                        weights=(
                            counterfactual_reach[node_index]
                            * (continuation[child] - continuation[node_index])
                        ),
                        minlength=own_hand_count,
                    )
                regret_deltas.append((node_index, delta))

            # As in TabularCFR, no regret update can alter the strategies cached
            # for this traverser.  The next traverser sees these updates.
            for node_index, delta in regret_deltas:
                regrets = self._regrets[node_index]
                assert regrets is not None
                regrets += delta
                if self.update_rule.clip_regrets:
                    np.maximum(regrets, 0.0, out=regrets)

        self._discount_accumulators()

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
        callback: Callable[["PublicTreeTensorCFR"], None] | None = None,
    ) -> None:
        if iterations < 0:
            raise ValueError("iterations cannot be negative")
        for _ in range(iterations):
            self.step()
            if callback is not None:
                callback(self)

    def current_strategy(self) -> Policy:
        strategies = self._strategies()
        policy: Policy = {}
        for node_index, node in enumerate(self.layout.nodes):
            strategy = strategies[node_index]
            if strategy is None:
                continue
            for hand_index, key in enumerate(node.information_keys):
                policy[key] = {
                    action: float(strategy[hand_index, action_index])
                    for action_index, action in enumerate(node.actions)
                }
        return dict(sorted(policy.items()))

    def average_strategy(self) -> Policy:
        current = self._strategies()
        policy: Policy = {}
        for node_index, node in enumerate(self.layout.nodes):
            strategy_sum = self._strategy_sums[node_index]
            if strategy_sum is None:
                continue
            fallback = current[node_index]
            assert fallback is not None
            totals = np.sum(strategy_sum, axis=1)
            for hand_index, key in enumerate(node.information_keys):
                values = (
                    fallback[hand_index]
                    if totals[hand_index] <= 0.0
                    else strategy_sum[hand_index] / totals[hand_index]
                )
                policy[key] = {
                    action: float(values[action_index])
                    for action_index, action in enumerate(node.actions)
                }
        return dict(sorted(policy.items()))

    def regret_table(self) -> dict[str, dict[Action, float]]:
        """Return a defensive canonical copy of every regret accumulator."""

        return self._accumulator_table(self._regrets)

    def strategy_sum_table(self) -> dict[str, dict[Action, float]]:
        """Return a defensive canonical copy of every average accumulator."""

        return self._accumulator_table(self._strategy_sums)

    def _accumulator_table(
        self,
        arrays: tuple[FloatArray | None, ...],
    ) -> dict[str, dict[Action, float]]:
        table: dict[str, dict[Action, float]] = {}
        for node_index, node in enumerate(self.layout.nodes):
            values = arrays[node_index]
            if values is None:
                continue
            for hand_index, key in enumerate(node.information_keys):
                table[key] = {
                    action: float(values[hand_index, action_index])
                    for action_index, action in enumerate(node.actions)
                }
        return dict(sorted(table.items()))

    def memory_summary(self) -> dict[str, int]:
        """Report persistent accumulators and peak dense traversal scratch."""

        accumulator_bytes = sum(
            values.nbytes
            for arrays in (self._regrets, self._strategy_sums)
            for values in arrays
            if values is not None
        )
        dense_deal_bytes = (
            2
            * self.layout.public_node_count
            * self.layout.deal_count
            * np.dtype(np.float64).itemsize
        )
        maximum_own_reach_bytes = (
            self.layout.public_node_count
            * max(map(len, self.layout.hands_by_player))
            * np.dtype(np.float64).itemsize
        )
        return {
            "persistent_accumulator_bytes": accumulator_bytes,
            "estimated_peak_step_scratch_bytes": (
                dense_deal_bytes + maximum_own_reach_bytes
            ),
        }
