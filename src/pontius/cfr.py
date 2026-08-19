"""Transparent full-tree alternating CFR and Linear CFR baselines."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import prod
from typing import Callable

from .evaluation import Policy, collect_information_sets, policy_distribution
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState
from .updates import CFRUpdateRule, SolverVariant, update_rule


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

    def __init__(
        self,
        game: ExtensiveFormGame,
        variant: SolverVariant = "cfr",
        *,
        blueprint_policy: Policy | None = None,
        blueprint_weight: float = 0.0,
        shadow_regret_variants: tuple[SolverVariant, ...] = (),
    ) -> None:
        if not 0.0 <= blueprint_weight <= 1.0:
            raise ValueError("blueprint_weight must be between zero and one")
        if blueprint_weight > 0.0 and blueprint_policy is None:
            raise ValueError("a positive blueprint_weight requires blueprint_policy")
        self.game = game
        self.update_rule = update_rule(variant)
        self.variant = self.update_rule.name
        if len(set(shadow_regret_variants)) != len(shadow_regret_variants):
            raise ValueError("shadow regret variants must be unique")
        if self.variant in shadow_regret_variants:
            raise ValueError("the active variant cannot also be a shadow variant")
        self._shadow_update_rules: dict[SolverVariant, CFRUpdateRule] = {
            shadow_variant: update_rule(shadow_variant)
            for shadow_variant in shadow_regret_variants
        }
        self._shadow_regrets: dict[
            SolverVariant,
            dict[str, dict[Action, float]],
        ] = {shadow_variant: {} for shadow_variant in shadow_regret_variants}
        self._shadow_regret_additions = {
            shadow_variant: 0 for shadow_variant in shadow_regret_variants
        }
        self._shadow_regret_discounts = {
            shadow_variant: 0 for shadow_variant in shadow_regret_variants
        }
        self.blueprint_policy = (
            None
            if blueprint_policy is None
            else {
                key: dict(distribution)
                for key, distribution in blueprint_policy.items()
            }
        )
        self.blueprint_weight = blueprint_weight
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

    def warm_start(self, policy: Policy, regret_mass: float) -> None:
        """Initialize regret matching to a policy with explicit prior strength.

        This is a pseudo-regret prior, not a theoretical CFR guarantee. The
        scalar ``regret_mass`` controls how much new counterfactual regret is
        required to move away from the blueprint. It must therefore be swept and
        reported rather than hidden inside solver initialization.
        """

        if self.iteration != 0 or self.information_sets:
            raise ValueError("warm_start must be called before the first iteration")
        if regret_mass <= 0.0:
            raise ValueError("regret_mass must be positive")
        information_sets: dict[str, tuple[Action, ...]] = {}
        for player in range(self.game.num_players):
            player_sets = collect_information_sets(self.game, player)
            overlap = set(information_sets) & set(player_sets)
            if overlap:
                raise ValueError(
                    f"information-set keys are shared across players: {overlap!r}"
                )
            information_sets.update(player_sets)
        self.warm_start_from_schema(policy, regret_mass, information_sets)

    def warm_start_from_schema(
        self,
        policy: Policy,
        regret_mass: float,
        information_sets: dict[str, tuple[Action, ...]],
    ) -> None:
        """Warm start from an already verified compatible information schema.

        This avoids a full game traversal when immutable tree topology is
        reused.  The caller must establish structural identity before passing a
        cached schema.  A later traversal still rejects any action mismatch.
        The method initializes numerical state only; it does not authorize the
        supplied policy for direct deployment in the current game.
        """

        if self.iteration != 0 or self.information_sets:
            raise ValueError("warm_start must be called before the first iteration")
        if regret_mass <= 0.0:
            raise ValueError("regret_mass must be positive")
        if not information_sets:
            raise ValueError("information_sets must be nonempty")

        prepared: list[
            tuple[str, tuple[Action, ...], dict[Action, float]]
        ] = []
        for key, actions in sorted(information_sets.items()):
            if not actions or len(set(actions)) != len(actions):
                raise ValueError(
                    f"invalid cached action schema for information set {key!r}"
                )
            prepared.append(
                (key, actions, policy_distribution(policy, key, actions))
            )

        for key, actions, distribution in prepared:
            data = self._data(key, actions)
            for action in actions:
                data.regrets[action] = regret_mass * distribution[action]
            for shadow_table in self._shadow_regrets.values():
                shadow_table[key] = {
                    action: regret_mass * distribution[action]
                    for action in actions
                }

    @staticmethod
    def _regret_matching(data: InformationSetData) -> dict[Action, float]:
        positive = {action: max(0.0, regret) for action, regret in data.regrets.items()}
        total = sum(positive.values())
        if total <= 0.0:
            probability = 1.0 / len(data.actions)
            return {action: probability for action in data.actions}
        return {action: positive[action] / total for action in data.actions}

    def _strategies(
        self,
        key: str,
        data: InformationSetData,
    ) -> tuple[dict[Action, float], dict[Action, float]]:
        """Return the candidate and deployed behavior at an information set.

        With blueprint weight ``b``, CFR optimizes the candidate component
        ``q`` while traversal uses ``b * blueprint + (1-b) * q``. This is a
        fixed affine trust region around the blueprint. It is an experimental
        restriction, not a multiplayer safety guarantee.
        """

        candidate = self._regret_matching(data)
        if self.blueprint_weight == 0.0:
            return candidate, candidate
        assert self.blueprint_policy is not None
        blueprint = policy_distribution(self.blueprint_policy, key, data.actions)
        candidate_weight = 1.0 - self.blueprint_weight
        behavior = {
            action: (
                self.blueprint_weight * blueprint[action]
                + candidate_weight * candidate[action]
            )
            for action in data.actions
        }
        return candidate, behavior

    def step(self) -> None:
        """Run one alternating update for every player."""

        self.iteration += 1
        for traverser in range(self.game.num_players):
            strategy_cache: dict[
                str,
                tuple[dict[Action, float], dict[Action, float]],
            ] = {}
            average_seen: set[str] = set()
            regret_deltas: dict[str, dict[Action, float]] = {}
            self._traverse(
                self.game.initial_state(),
                traverser,
                reach=(1.0,) * self.game.num_players,
                chance_reach=1.0,
                strategy_cache=strategy_cache,
                average_seen=average_seen,
                regret_deltas=regret_deltas,
            )
            self._apply_regret_deltas(regret_deltas)
        self._discount_accumulators()

    def _apply_regret_deltas(
        self,
        regret_deltas: dict[str, dict[Action, float]],
    ) -> None:
        for key, action_deltas in regret_deltas.items():
            data = self.information_sets[key]
            for action, delta in action_deltas.items():
                data.regrets[action] = self.update_rule.add_regret(data.regrets[action], delta)
            for shadow_variant, shadow_table in self._shadow_regrets.items():
                shadow_data = shadow_table.setdefault(
                    key,
                    {action: 0.0 for action in data.actions},
                )
                shadow_rule = self._shadow_update_rules[shadow_variant]
                for action, delta in action_deltas.items():
                    shadow_data[action] = shadow_rule.add_regret(
                        shadow_data[action],
                        delta,
                    )
                    self._shadow_regret_additions[shadow_variant] += 1

    def _discount_accumulators(self) -> None:
        for data in self.information_sets.values():
            for action in data.actions:
                data.regrets[action] = self.update_rule.discount_regret(
                    data.regrets[action], self.iteration
                )
                data.strategy_sum[action] = self.update_rule.discount_strategy(
                    data.strategy_sum[action], self.iteration
                )
        for shadow_variant, shadow_table in self._shadow_regrets.items():
            shadow_rule = self._shadow_update_rules[shadow_variant]
            for action_regrets in shadow_table.values():
                for action, regret in action_regrets.items():
                    action_regrets[action] = shadow_rule.discount_regret(
                        regret,
                        self.iteration,
                    )
                    self._shadow_regret_discounts[shadow_variant] += 1

    @property
    def shadow_regret_variants(self) -> tuple[SolverVariant, ...]:
        """Alternate accumulator rules fed by the active traversal's deltas."""

        return tuple(self._shadow_regrets)

    def shadow_regret_table(
        self,
        variant: SolverVariant,
    ) -> dict[str, dict[Action, float]]:
        """Return a defensive copy of one diagnostic shadow accumulator.

        A shadow applies another numerical regret-update rule to the active
        solver's already-computed instantaneous deltas. It does not influence
        traversal strategies, collect an average policy, or perform extra tree
        walks. After active and shadow trajectories diverge, it must not be
        interpreted as a standalone solve with the shadow variant.
        """

        try:
            table = self._shadow_regrets[variant]
        except KeyError as error:
            raise ValueError(
                f"shadow regret variant {variant!r} was not configured"
            ) from error
        return {
            key: dict(action_regrets)
            for key, action_regrets in table.items()
        }

    def shadow_regret_summary(
        self,
        variant: SolverVariant,
    ) -> dict[str, float | int]:
        """Summarize a shadow table in one pass without copying it."""

        try:
            table = self._shadow_regrets[variant]
        except KeyError as error:
            raise ValueError(
                f"shadow regret variant {variant!r} was not configured"
            ) from error
        positive_mass = 0.0
        positive_squared_mass = 0.0
        negative_mass = 0.0
        maximum_positive = 0.0
        entries = 0
        for action_regrets in table.values():
            for regret in action_regrets.values():
                entries += 1
                if regret > 0.0:
                    positive_mass += regret
                    positive_squared_mass += regret * regret
                    maximum_positive = max(maximum_positive, regret)
                elif regret < 0.0:
                    negative_mass -= regret
        return {
            "materialized_information_sets": len(table),
            "regret_entries": entries,
            "positive_regret_mass": positive_mass,
            "negative_regret_mass": negative_mass,
            "maximum_positive_regret": maximum_positive,
            "positive_regret_concentration": (
                positive_squared_mass / (positive_mass * positive_mass)
                if positive_mass > 0.0
                else 0.0
            ),
            "instantaneous_regret_updates": self._shadow_regret_additions[variant],
            "regret_discount_updates": self._shadow_regret_discounts[variant],
        }

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
        strategy_cache: dict[
            str,
            tuple[dict[Action, float], dict[Action, float]],
        ],
        average_seen: set[str],
        regret_deltas: dict[str, dict[Action, float]],
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
                    regret_deltas,
                )
            return value

        actions = tuple(state.legal_actions())
        key = state.information_state_key(player)
        data = self._data(key, actions)
        candidate_strategy, strategy = strategy_cache.setdefault(
            key,
            self._strategies(key, data),
        )

        if player == traverser and key not in average_seen:
            average_seen.add(key)
            strategy_weight = reach[player]
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
                regret_deltas,
            )
            action_values[action] = action_value
            node_value += strategy[action] * action_value

        if player == traverser:
            counterfactual_reach = chance_reach * prod(
                reach[opponent]
                for opponent in range(self.game.num_players)
                if opponent != traverser
            )
            action_deltas = regret_deltas.setdefault(
                key, {action: 0.0 for action in actions}
            )
            candidate_node_value = sum(
                candidate_strategy[action] * action_values[action]
                for action in actions
            )
            candidate_weight = 1.0 - self.blueprint_weight
            for action in actions:
                action_deltas[action] += counterfactual_reach * candidate_weight * (
                    action_values[action] - candidate_node_value
                )

        return node_value

    def current_strategy(self) -> Policy:
        return {
            key: self._strategies(key, data)[1]
            for key, data in sorted(self.information_sets.items())
        }

    def average_strategy(self) -> Policy:
        policy: Policy = {}
        for key, data in sorted(self.information_sets.items()):
            total = sum(data.strategy_sum.values())
            if total <= 0.0:
                policy[key] = self._strategies(key, data)[1]
            else:
                policy[key] = {
                    action: data.strategy_sum[action] / total for action in data.actions
                }
        return policy
