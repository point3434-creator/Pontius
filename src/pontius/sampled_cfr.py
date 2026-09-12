"""Serial external-sampling CFR reference with multiplayer-safe averaging.

One iteration freezes the joint policy, samples one external traversal per
player, and then takes one averaging trajectory per player. For averaging,
opponents ALWAYS use uniform legal actions; only the target uses its current
policy. Under perfect recall, the expected row contribution is own reach times
policy times an iteration-independent chance/opponent factor, which cancels on
normalization. This avoids the generally incorrect multiplayer shortcut of
adding an opponent's strategy at every visited external-sampling node.

``linear`` weights both regret and average increments by the full iteration
number. It does not also discount stored values. Accumulators use Python binary64
floats, without clipping or pruning. This is a correctness/measurement reference,
not a memory-optimized production trainer or a six-player Nash certificate.
"""

from collections.abc import Callable
from dataclasses import dataclass
import hashlib
import json
import math
import random

from .game import CHANCE_PLAYER, TERMINAL_PLAYER, GameState


class SamplingLimit(RuntimeError):
    """A configured bound stopped an iteration before it could be committed."""


@dataclass(slots=True)
class RegretRow:
    player: int
    actions: tuple[str, ...]
    regrets: list[float]
    strategy_sum: list[float]
    average_visits: int = 0


@dataclass(frozen=True)
class AverageSample:
    updates: dict[str, list[float]]
    visited_nodes: int


def _probabilities(weights):
    values = tuple(float(value) for value in weights)
    if not values or any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("probability weights must be finite, nonnegative and nonempty")
    total = math.fsum(values)
    if not math.isfinite(total) or total <= 0:
        raise ValueError("probability weights need positive finite mass")
    return tuple(value / total for value in values)


def _pick(probabilities, rng):
    draw = rng.random()
    cumulative = 0.0
    last_positive = None
    for index, probability in enumerate(probabilities):
        cumulative += probability
        if probability > 0:
            last_positive = index
        if draw < cumulative:
            return index
    if last_positive is None:
        raise ValueError("cannot sample a distribution with no positive action")
    return last_positive


def _chance_child(state, rng):
    outcomes = tuple(state.chance_outcomes())
    probabilities = _probabilities(probability for _, probability in outcomes)
    if abs(sum(probability for _, probability in outcomes) - 1.0) > 1e-10:
        raise ValueError("chance probabilities must sum to one")
    return state.apply_action(outcomes[_pick(probabilities, rng)][0])


def average_trajectory(
    root: GameState,
    target: int,
    policy: Callable[[GameState], tuple[float, ...]],
    rng: random.Random,
    *,
    weight: float = 1.0,
    node_limit: int = 100_000,
) -> AverageSample:
    """Sample a bounded-update reach-weighted average for one target player.

    Uniform opponent sampling must remain fixed across training. This estimator
    gives unbiased unnormalized sums up to a fixed row factor; normalizing a
    finite sample is not an unbiased operation. Rare rows need coverage evidence.
    ``policy`` is only queried at the target's own information sets.
    """
    if not math.isfinite(weight) or weight <= 0:
        raise ValueError("averaging weight must be positive and finite")
    updates = {}
    state = root
    nodes = 0
    while True:
        nodes += 1
        if nodes > node_limit:
            raise SamplingLimit("averaging trajectory exceeded node limit")
        player = state.current_player
        if player == TERMINAL_PLAYER:
            return AverageSample(updates, nodes)
        if player == CHANCE_PLAYER:
            state = _chance_child(state, rng)
            continue
        actions = tuple(state.legal_actions())
        if not actions:
            raise ValueError("nonterminal node has no legal actions")
        if player == target:
            probabilities = _probabilities(policy(state))
            if len(probabilities) != len(actions):
                raise ValueError("policy/action lengths differ")
            key = state.information_state_key(player)
            if key in updates:
                raise ValueError("repeated target infoset violates perfect recall")
            updates[key] = [weight * value for value in probabilities]
        else:
            probabilities = (1.0 / len(actions),) * len(actions)
        state = state.apply_action(actions[_pick(probabilities, rng)])


class ExternalSamplingCFR:
    """Bounded serial sampled CFR, with complete JSON-compatible restart state."""

    def __init__(
        self,
        num_players: int,
        root_sampler: Callable[[random.Random], GameState],
        game_id: str,
        *,
        variant: str = "cfr",
        seed: int = 0,
        max_rows: int = 100_000,
        max_nodes: int = 200_000,
    ):
        if type(num_players) is not int or num_players < 2:
            raise ValueError("at least two players are required")
        if variant not in ("cfr", "linear"):
            raise ValueError("variant must be cfr or linear")
        if not isinstance(game_id, str) or not game_id:
            raise ValueError("a versioned game identity is required")
        if any(type(limit) is not int or limit < 1 for limit in (max_rows, max_nodes)):
            raise ValueError("capacity bounds must be positive integers")
        self.num_players = num_players
        self.root_sampler = root_sampler
        self.game_id = game_id
        self.variant = variant
        self.max_rows = max_rows
        self.max_nodes = max_nodes
        self.rng = random.Random(seed)
        self.iterations = 0
        self.total_nodes = 0
        self.rows: dict[str, RegretRow] = {}

    @property
    def identity(self):
        description = {
            "algorithm": "external-sampling-frozen-v1",
            "average": "fixed-uniform-opponents-v1",
            "game": self.game_id,
            "players": self.num_players,
            "variant": self.variant,
        }
        return hashlib.sha256(json.dumps(description, sort_keys=True).encode()).hexdigest()

    def step(self):
        """Commit one full round, or leave state/RNG unchanged on a detected error."""
        rng_before = self.rng.getstate()
        pending_rows = {}
        strategies = {}
        regret_updates = {}
        average_updates = {}
        nodes = 0
        weight = float(self.iterations + 1) if self.variant == "linear" else 1.0

        def strategy(state):
            player = state.current_player
            if player not in range(self.num_players):
                raise ValueError("player is out of range")
            key = state.information_state_key(player)
            actions = tuple(state.legal_actions())
            if (not isinstance(key, str) or not actions or
                    any(type(action) is not str for action in actions) or
                    len(set(actions)) != len(actions)):
                raise ValueError("infosets require a string key and unique string actions")
            row = self.rows.get(key) or pending_rows.get(key)
            if row is None:
                if len(self.rows) + len(pending_rows) >= self.max_rows:
                    raise SamplingLimit("information table reached max_rows")
                row = RegretRow(player, actions, [0.0] * len(actions), [0.0] * len(actions))
                pending_rows[key] = row
            if row.actions != actions or row.player != player:
                raise ValueError("an infoset changed owner or legal actions")
            if key not in strategies:
                positive = tuple(max(0.0, regret) for regret in row.regrets)
                strategies[key] = (_probabilities(positive) if any(positive) else
                                   (1.0 / len(actions),) * len(actions))
            return strategies[key]

        def traverse(state, target):
            nonlocal nodes
            nodes += 1
            if nodes > self.max_nodes:
                raise SamplingLimit("regret traversal exceeded max_nodes")
            player = state.current_player
            if player == TERMINAL_PLAYER:
                utilities = state.returns()
                if len(utilities) != self.num_players or any(
                    not math.isfinite(value) for value in utilities
                ):
                    raise ValueError("terminal utilities must be finite and match player count")
                return utilities[target]
            if player == CHANCE_PLAYER:
                return traverse(_chance_child(state, self.rng), target)
            probabilities = strategy(state)
            actions = tuple(state.legal_actions())
            if player != target:
                return traverse(state.apply_action(actions[_pick(probabilities, self.rng)]), target)
            values = [traverse(state.apply_action(action), target) for action in actions]
            node_value = math.fsum(
                probability * value
                for probability, value in zip(probabilities, values, strict=True)
            )
            key = state.information_state_key(player)
            update = regret_updates.setdefault(key, [0.0] * len(actions))
            for index, value in enumerate(values):
                update[index] += weight * (value - node_value)
            return node_value

        try:
            for player in range(self.num_players):
                traverse(self.root_sampler(self.rng), player)
            for player in range(self.num_players):
                sample = average_trajectory(
                    self.root_sampler(self.rng), player, strategy, self.rng,
                    weight=weight, node_limit=self.max_nodes - nodes,
                )
                nodes += sample.visited_nodes
                for key, update in sample.updates.items():
                    if key in average_updates:
                        raise ValueError("players must have distinct infoset identities")
                    average_updates[key] = update
            # Validate every prospective numeric update before mutating persistent rows.
            for updates, attribute in ((regret_updates, "regrets"),
                                       (average_updates, "strategy_sum")):
                for key, update in updates.items():
                    row = self.rows.get(key) or pending_rows[key]
                    if any(not math.isfinite(old + change) for old, change in
                           zip(getattr(row, attribute), update, strict=True)):
                        raise ValueError("non-finite accumulator update")
        except Exception:
            self.rng.setstate(rng_before)
            raise

        self.rows.update(pending_rows)
        for updates, attribute in ((regret_updates, "regrets"),
                                   (average_updates, "strategy_sum")):
            for key, update in updates.items():
                destination = getattr(self.rows[key], attribute)
                for index, change in enumerate(update):
                    destination[index] += change
        for key in average_updates:
            self.rows[key].average_visits += 1
        self.iterations += 1
        self.total_nodes += nodes
        return nodes

    def average_policy(self):
        policy = {}
        for key, row in self.rows.items():
            probabilities = (_probabilities(row.strategy_sum) if any(row.strategy_sum) else
                             (1.0 / len(row.actions),) * len(row.actions))
            policy[key] = dict(zip(row.actions, probabilities, strict=True))
        return policy

    def state_dict(self):
        # Convert tuples in Random's state to JSON-native lists without changing numbers.
        rng_state = json.loads(json.dumps(self.rng.getstate()))
        return {
            "format": "pontius-sampled-cfr-v1", "identity": self.identity,
            "game_id": self.game_id, "num_players": self.num_players,
            "variant": self.variant, "max_rows": self.max_rows, "max_nodes": self.max_nodes,
            "iterations": self.iterations, "total_nodes": self.total_nodes, "rng": rng_state,
            "rows": [
                {"key": key, "player": row.player, "actions": list(row.actions),
                 "regrets": list(row.regrets), "strategy_sum": list(row.strategy_sum),
                 "average_visits": row.average_visits}
                for key, row in sorted(self.rows.items())
            ],
        }

    @classmethod
    def from_state(cls, state, root_sampler, expected_game_id):
        if state.get("format") != "pontius-sampled-cfr-v1":
            raise ValueError("unsupported trainer state")
        if state.get("game_id") != expected_game_id:
            raise ValueError("checkpoint game identity mismatch")
        result = cls(state["num_players"], root_sampler, state["game_id"],
                     variant=state["variant"], max_rows=state["max_rows"],
                     max_nodes=state["max_nodes"])
        if result.identity != state.get("identity"):
            raise ValueError("checkpoint algorithm identity mismatch")
        for name in ("iterations", "total_nodes"):
            if type(state.get(name)) is not int or state[name] < 0:
                raise ValueError("invalid trainer counters")
            setattr(result, name, state[name])
        for record in state["rows"]:
            key, player, actions = record["key"], record["player"], tuple(record["actions"])
            if (type(key) is not str or key in result.rows or not actions or
                    type(player) is not int or player not in range(result.num_players) or
                    any(type(action) is not str for action in actions) or
                    len(set(actions)) != len(actions)):
                raise ValueError("invalid information row")
            regrets = [float(value) for value in record["regrets"]]
            strategy_sum = [float(value) for value in record["strategy_sum"]]
            visits = record["average_visits"]
            if (len(regrets) != len(actions) or len(strategy_sum) != len(actions) or
                    any(not math.isfinite(value) for value in regrets + strategy_sum) or
                    any(value < 0 for value in strategy_sum) or
                    type(visits) is not int or not 0 <= visits <= result.iterations):
                raise ValueError("invalid regret or average accumulators")
            result.rows[key] = RegretRow(player, actions, regrets, strategy_sum, visits)
        if len(result.rows) > result.max_rows:
            raise ValueError("checkpoint exceeds configured row capacity")

        def tuples(value):
            return tuple(tuples(item) for item in value) if isinstance(value, list) else value

        try:
            result.rng.setstate(tuples(state["rng"]))
        except (TypeError, ValueError, IndexError) as error:
            raise ValueError("invalid RNG restart state") from error
        return result
