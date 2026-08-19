"""Flat exact dependency tapes for range and behavioral-policy recertification.

The base compiler turns an immutable extensive-form tree and one fixed policy
into contiguous arithmetic arrays whose root chance probabilities are mutable.
``CompiledPolicyDeltaTape`` additionally materializes one mutable input per
information-set/action probability.  Fixed-policy utilities and perfect-recall
best responses are expressed as a topologically ordered circuit with global
information-set selectors.

This is a correctness and layout reference.  It deliberately keeps Python game
objects in compilation only; recertification reads flat integer and Float64
arrays and an epoch-stamped source-relative overlay.
"""

from __future__ import annotations

from array import array
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from math import fsum, isfinite
from typing import Literal

from .evaluation import EvaluationResult, Policy, policy_distribution
from .game import (
    Action,
    CHANCE_PLAYER,
    TERMINAL_PLAYER,
    ExtensiveFormGame,
    GameState,
)

ExecutionMode = Literal["auto", "sparse", "dense"]

_INPUT = 0
_CONSTANT = 1
_AFFINE = 2
_PRODUCT = 3
_ARGMAX = 4
_SELECT = 5
_OPERATION_NAMES = (
    "input",
    "constant",
    "affine",
    "product",
    "argmax",
    "select",
)
_MAX_NUMERICAL_GUARD = 1e-10


@dataclass(frozen=True, slots=True)
class DependencyTapeDiagnostics:
    execution_mode: str
    changed_root_outcomes: int
    dirty_nodes: int
    dirty_node_fraction: float
    recomputed_nodes: int
    selector_nodes: int
    best_response_action_flips: int
    numeric_nodes: int
    dependency_edges: int
    contiguous_runtime_bytes: int
    changed_policy_entries: int = 0
    changed_policy_information_sets: int = 0
    policy_input_entries: int = 0


@dataclass(frozen=True, slots=True)
class DependencyTapeResult:
    evaluation: EvaluationResult
    best_response_actions: tuple[dict[str, Action], ...]
    diagnostics: DependencyTapeDiagnostics


@dataclass(frozen=True, slots=True)
class FinitePolicyReuseAssessment:
    source_exploitability: float
    target_exploitability: float
    signed_transfer_damage: float
    absolute_quality_budget: float
    transfer_damage_budget: float
    numerical_guard: float
    absolute_quality_passes: bool
    transfer_damage_passes: bool
    accepted: bool


def assess_finite_policy_reuse(
    source: EvaluationResult,
    target: EvaluationResult,
    *,
    absolute_quality_budget: float,
    transfer_damage_budget: float,
    numerical_guard: float = 1e-12,
) -> FinitePolicyReuseAssessment:
    """Apply separate absolute-quality and range-transfer budgets.

    The evaluator's literal exploitability is never modified.  This policy
    layer merely distinguishes target quality from paired source-to-target
    damage.  It is defined only for the two-player exploitability metric.
    """

    if source.exploitability is None or target.exploitability is None:
        raise ValueError("finite-policy exploitability budgets require two players")
    values = (absolute_quality_budget, transfer_damage_budget, numerical_guard)
    if any(not isfinite(value) or value < 0.0 for value in values):
        raise ValueError("reuse budgets and numerical guard must be finite and nonnegative")
    if numerical_guard > _MAX_NUMERICAL_GUARD:
        raise ValueError("numerical guard exceeds the validated evaluation envelope")

    source_exploitability = source.exploitability
    target_exploitability = target.exploitability
    transfer_damage = target_exploitability - source_exploitability
    absolute_passes = target_exploitability <= absolute_quality_budget + numerical_guard
    transfer_passes = transfer_damage <= transfer_damage_budget + numerical_guard
    return FinitePolicyReuseAssessment(
        source_exploitability=source_exploitability,
        target_exploitability=target_exploitability,
        signed_transfer_damage=transfer_damage,
        absolute_quality_budget=absolute_quality_budget,
        transfer_damage_budget=transfer_damage_budget,
        numerical_guard=numerical_guard,
        absolute_quality_passes=absolute_passes,
        transfer_damage_passes=transfer_passes,
        accepted=absolute_passes and transfer_passes,
    )


@dataclass(slots=True)
class _TreeNode:
    player: int
    root_outcome: int
    actions: tuple[Action, ...]
    children: tuple[int, ...]
    probabilities: tuple[float, ...]
    information_key: str | None
    returns: tuple[float, ...] | None


@dataclass(slots=True)
class _InformationSet:
    actions: tuple[Action, ...]
    player_depth: int
    members: list[tuple[int, float]]


@dataclass(frozen=True, slots=True)
class _SelectorMetadata:
    player: int
    information_key: str
    actions: tuple[Action, ...]
    node: int


@dataclass(frozen=True, slots=True)
class _PolicyInputMetadata:
    player: int
    information_key: str
    actions: tuple[Action, ...]
    nodes: tuple[int, ...]
    source_probabilities: tuple[float, ...]


def _normalized_root_distribution(game: ExtensiveFormGame) -> dict[Action, float]:
    root = game.initial_state()
    if root.current_player != CHANCE_PLAYER:
        raise ValueError("dependency tape requires chance at the game root")
    outcomes = tuple(root.chance_outcomes())
    if not outcomes:
        raise ValueError("root chance must contain at least one outcome")
    result: dict[Action, float] = {}
    for action, supplied_probability in outcomes:
        probability = float(supplied_probability)
        if not isfinite(probability) or probability < 0.0:
            raise ValueError("root chance probabilities must be finite and nonnegative")
        if action in result:
            raise ValueError(f"duplicate root chance outcome {action!r}")
        if probability > 0.0:
            result[action] = probability
    if abs(fsum(result.values()) - 1.0) > 1e-12:
        raise ValueError("root chance probabilities must sum to one")
    return result


def _structure_token(game: ExtensiveFormGame) -> tuple[object, ...]:
    digest = getattr(game, "structural_digest", None)
    if digest is not None:
        if not isinstance(digest, str) or not digest:
            raise ValueError("structural_digest must be a nonempty string")
        return ("structural_digest", digest, game.num_players)
    game_type = type(game)
    return (
        "game_type",
        game_type.__module__,
        game_type.__qualname__,
        game.num_players,
    )


class _TreeCompiler:
    def __init__(
        self,
        source: ExtensiveFormGame,
        policy: Policy,
        universe_games: Sequence[ExtensiveFormGame],
    ) -> None:
        games = (source, *universe_games)
        if source.num_players <= 0:
            raise ValueError("game must contain at least one player")
        token = _structure_token(source)
        if any(game.num_players != source.num_players for game in games):
            raise ValueError("all outcome-universe games must have the same player count")
        if any(_structure_token(game) != token for game in games):
            raise ValueError("all outcome-universe games must have identical structure")

        self.num_players = source.num_players
        self.structure_token = token
        self.policy: Policy = {
            key: dict(distribution) for key, distribution in policy.items()
        }
        self.games = games
        self.game_ids = frozenset(id(game) for game in games)
        self.game_distributions: dict[int, dict[Action, float]] = {}
        self.outcomes: list[Action] = []
        providers: dict[Action, GameState] = {}

        for game in games:
            distribution = _normalized_root_distribution(game)
            self.game_distributions[id(game)] = distribution
            root = game.initial_state()
            for action in distribution:
                if action not in providers:
                    providers[action] = root.apply_action(action)
                    self.outcomes.append(action)

        self.outcome_index = {
            outcome: index for index, outcome in enumerate(self.outcomes)
        }
        source_distribution = self.game_distributions[id(source)]
        self.source_probabilities = tuple(
            source_distribution.get(outcome, 0.0) for outcome in self.outcomes
        )
        self.nodes: list[_TreeNode] = []
        self.root_nodes = tuple(
            self._compile_state(providers[outcome], index)
            for index, outcome in enumerate(self.outcomes)
        )

    def _compile_state(self, state: GameState, root_outcome: int) -> int:
        node_index = len(self.nodes)
        self.nodes.append(
            _TreeNode(
                player=TERMINAL_PLAYER,
                root_outcome=root_outcome,
                actions=(),
                children=(),
                probabilities=(),
                information_key=None,
                returns=None,
            )
        )
        player = state.current_player
        if player == TERMINAL_PLAYER:
            returns = tuple(float(value) for value in state.returns())
            if len(returns) != self.num_players or any(
                not isfinite(value) for value in returns
            ):
                raise ValueError("terminal returns must be finite and match player count")
            self.nodes[node_index] = _TreeNode(
                player=player,
                root_outcome=root_outcome,
                actions=(),
                children=(),
                probabilities=(),
                information_key=None,
                returns=returns,
            )
            return node_index

        if player == CHANCE_PLAYER:
            outcomes = tuple(state.chance_outcomes())
            actions = tuple(action for action, _ in outcomes)
            probabilities = tuple(float(probability) for _, probability in outcomes)
            if not outcomes or any(
                not isfinite(probability) or probability < 0.0
                for probability in probabilities
            ):
                raise ValueError("non-root chance distribution is invalid")
            if abs(fsum(probabilities) - 1.0) > 1e-12:
                raise ValueError("non-root chance probabilities must sum to one")
            children = tuple(
                self._compile_state(state.apply_action(action), root_outcome)
                for action in actions
            )
            information_key = None
        else:
            if player not in range(self.num_players):
                raise ValueError(f"invalid acting player {player}")
            actions = tuple(state.legal_actions())
            if not actions or len(set(actions)) != len(actions):
                raise ValueError("strategic state actions must be nonempty and unique")
            information_key = state.information_state_key(player)
            distribution = policy_distribution(self.policy, information_key, actions)
            probabilities = tuple(distribution[action] for action in actions)
            children = tuple(
                self._compile_state(state.apply_action(action), root_outcome)
                for action in actions
            )

        self.nodes[node_index] = _TreeNode(
            player=player,
            root_outcome=root_outcome,
            actions=actions,
            children=children,
            probabilities=probabilities,
            information_key=information_key,
            returns=None,
        )
        return node_index

    def distribution_for_game(self, game: ExtensiveFormGame) -> dict[Action, float]:
        if _structure_token(game) != self.structure_token:
            raise ValueError("target game structure does not match the compiled tape")
        distribution = (
            self.game_distributions[id(game)]
            if id(game) in self.game_ids
            else _normalized_root_distribution(game)
        )
        unknown = set(distribution) - set(self.outcome_index)
        if unknown:
            raise ValueError(
                f"target contains outcomes outside the compiled topology epoch: {unknown!r}"
            )
        return distribution


class _TapeBuilder:
    def __init__(self) -> None:
        self.kinds: list[int] = []
        self.input_offsets: list[int] = []
        self.input_counts: list[int] = []
        self.edge_inputs: list[int] = []
        self.edge_weights: list[float] = []
        self.seed_values: list[float] = []
        self.constant_cache: dict[str, int] = {}

    def _add(
        self,
        kind: int,
        inputs: Sequence[int] = (),
        weights: Sequence[float] = (),
        *,
        seed_value: float = 0.0,
    ) -> int:
        if kind not in range(len(_OPERATION_NAMES)):
            raise ValueError(f"invalid tape operation {kind}")
        if weights and len(weights) != len(inputs):
            raise ValueError("edge weights must match inputs")
        node = len(self.kinds)
        if any(input_node >= node or input_node < 0 for input_node in inputs):
            raise ValueError("tape dependencies must precede their consumer")
        self.kinds.append(kind)
        self.input_offsets.append(len(self.edge_inputs))
        self.input_counts.append(len(inputs))
        self.edge_inputs.extend(inputs)
        self.edge_weights.extend(weights or (1.0,) * len(inputs))
        self.seed_values.append(float(seed_value))
        return node

    def input(self, value: float) -> int:
        return self._add(_INPUT, seed_value=value)

    def constant(self, value: float) -> int:
        value = float(value)
        key = value.hex()
        cached = self.constant_cache.get(key)
        if cached is not None:
            return cached
        node = self._add(_CONSTANT, seed_value=value)
        self.constant_cache[key] = node
        return node

    def constant_value(self, node: int) -> float | None:
        return self.seed_values[node] if self.kinds[node] == _CONSTANT else None

    def affine(self, terms: Sequence[tuple[int, float]]) -> int:
        combined: dict[int, list[float]] = {}
        for node, weight in terms:
            weight = float(weight)
            if weight == 0.0:
                continue
            combined.setdefault(node, []).append(weight)
        prepared = [
            (node, fsum(weights)) for node, weights in combined.items()
        ]
        prepared = [(node, weight) for node, weight in prepared if weight != 0.0]
        if not prepared:
            return self.constant(0.0)
        constants = [self.constant_value(node) for node, _ in prepared]
        if all(value is not None for value in constants):
            return self.constant(
                fsum(
                    weight * float(value)
                    for (_, weight), value in zip(prepared, constants, strict=True)
                )
            )
        if len(prepared) == 1 and prepared[0][1] == 1.0:
            return prepared[0][0]
        return self._add(
            _AFFINE,
            inputs=tuple(node for node, _ in prepared),
            weights=tuple(weight for _, weight in prepared),
        )

    def product(self, left: int, right: int) -> int:
        left_constant = self.constant_value(left)
        right_constant = self.constant_value(right)
        if left_constant is not None and right_constant is not None:
            return self.constant(left_constant * right_constant)
        if left_constant is not None:
            return self.affine(((right, left_constant),))
        if right_constant is not None:
            return self.affine(((left, right_constant),))
        return self._add(_PRODUCT, inputs=(left, right))

    def argmax(self, action_values: Sequence[int]) -> int:
        if not action_values:
            raise ValueError("argmax requires at least one action")
        return self._add(_ARGMAX, inputs=tuple(action_values))

    def select(self, selector: int, action_values: Sequence[int]) -> int:
        if not action_values:
            raise ValueError("selector requires at least one action value")
        return self._add(_SELECT, inputs=(selector, *action_values))


class CompiledPolicyDependencyTape:
    """Compiled exact fixed-policy evaluator with incremental root probabilities."""

    def __init__(
        self,
        source_game: ExtensiveFormGame,
        policy: Policy,
        *,
        universe_games: Sequence[ExtensiveFormGame] = (),
        dense_threshold: float = 0.35,
        _parameterize_policy: bool = False,
        _changed_policy_tolerance: float = 0.0,
    ) -> None:
        if not isfinite(dense_threshold) or not 0.0 <= dense_threshold <= 1.0:
            raise ValueError("dense_threshold must be finite and between zero and one")
        if (
            not isfinite(_changed_policy_tolerance)
            or _changed_policy_tolerance < 0.0
            or _changed_policy_tolerance > _MAX_NUMERICAL_GUARD
        ):
            raise ValueError(
                "changed policy tolerance must be finite and within the numerical guard"
            )
        self._tree = _TreeCompiler(source_game, policy, tuple(universe_games))
        self._dense_threshold = dense_threshold
        self._parameterize_policy = _parameterize_policy
        self._changed_policy_tolerance = _changed_policy_tolerance
        builder = _TapeBuilder()
        self._root_inputs = tuple(
            builder.input(probability)
            for probability in self._tree.source_probabilities
        )
        self._policy_inputs_by_key: dict[str, dict[Action, int]] = {}
        self._policy_metadata = self._compile_policy_inputs(builder)

        fixed_cache: list[dict[int, int]] = [
            {} for _ in range(self._tree.num_players)
        ]

        def fixed_continuation(player: int, state_node: int) -> int:
            cached = fixed_cache[player].get(state_node)
            if cached is not None:
                return cached
            state = self._tree.nodes[state_node]
            if state.player == TERMINAL_PLAYER:
                assert state.returns is not None
                result = builder.constant(state.returns[player])
            elif self._parameterize_policy and state.player != CHANCE_PLAYER:
                assert state.information_key is not None
                inputs = self._policy_inputs_by_key[state.information_key]
                result = builder.affine(
                    tuple(
                        (
                            builder.product(
                                inputs[action],
                                fixed_continuation(player, child),
                            ),
                            1.0,
                        )
                        for action, child in zip(
                            state.actions,
                            state.children,
                            strict=True,
                        )
                    )
                )
            else:
                result = builder.affine(
                    tuple(
                        (fixed_continuation(player, child), probability)
                        for child, probability in zip(
                            state.children,
                            state.probabilities,
                            strict=True,
                        )
                    )
                )
            fixed_cache[player][state_node] = result
            return result

        self._utility_outputs = tuple(
            builder.affine(
                tuple(
                    (
                        builder.product(
                            self._root_inputs[outcome],
                            fixed_continuation(player, root_node),
                        ),
                        1.0,
                    )
                    for outcome, root_node in enumerate(self._tree.root_nodes)
                )
            )
            for player in range(self._tree.num_players)
        )

        selectors: list[_SelectorMetadata] = []
        best_response_outputs = []
        for target_player in range(self._tree.num_players):
            if self._parameterize_policy:
                output, player_selectors = self._compile_parameterized_best_response(
                    builder,
                    target_player,
                )
            else:
                output, player_selectors = self._compile_best_response(
                    builder,
                    target_player,
                )
            best_response_outputs.append(output)
            selectors.extend(player_selectors)
        self._best_response_outputs = tuple(best_response_outputs)
        self._selectors = tuple(selectors)

        self._kinds = array("B", builder.kinds)
        self._input_offsets = array("I", builder.input_offsets)
        self._input_counts = array("I", builder.input_counts)
        self._edge_inputs = array("I", builder.edge_inputs)
        self._edge_weights = array("d", builder.edge_weights)
        self._base_values = array("d", builder.seed_values)
        self._base_selections = array("i", (-1 for _ in builder.kinds))
        self._evaluate_base()
        self._dependent_offsets, self._dependents = self._build_reverse_dependencies()

        node_count = len(self._kinds)
        self._overlay_values = array("d", (0.0 for _ in range(node_count)))
        self._overlay_selections = array("i", (-1 for _ in range(node_count)))
        self._value_epochs = array("I", (0 for _ in range(node_count)))
        self._dirty_epochs = array("I", (0 for _ in range(node_count)))
        self._epoch = 0
        self._operation_nodes = tuple(
            node
            for node, kind in enumerate(self._kinds)
            if kind not in (_INPUT, _CONSTANT)
        )
        self._source_result = DependencyTapeResult(
            evaluation=self._base_evaluation(),
            best_response_actions=self._actions_from_base(),
            diagnostics=self._diagnostics(
                execution_mode="identity",
                changed=0,
                dirty=0,
                recomputed=0,
                action_flips=0,
                changed_policy_entries=0,
                changed_policy_information_sets=0,
            ),
        )

    def _compile_policy_inputs(
        self,
        builder: _TapeBuilder,
    ) -> tuple[_PolicyInputMetadata, ...]:
        if not self._parameterize_policy:
            return ()

        entries: dict[
            str,
            tuple[int, tuple[Action, ...], tuple[float, ...]],
        ] = {}
        for state in self._tree.nodes:
            if state.player in (CHANCE_PLAYER, TERMINAL_PLAYER):
                continue
            assert state.information_key is not None
            candidate = (state.player, state.actions, state.probabilities)
            previous = entries.get(state.information_key)
            if previous is None:
                entries[state.information_key] = candidate
            elif previous != candidate:
                raise ValueError(
                    "policy input schema is inconsistent at information set "
                    f"{state.information_key!r}"
                )

        metadata = []
        for information_key in sorted(entries):
            player, actions, probabilities = entries[information_key]
            nodes = tuple(builder.input(probability) for probability in probabilities)
            self._policy_inputs_by_key[information_key] = dict(
                zip(actions, nodes, strict=True)
            )
            metadata.append(
                _PolicyInputMetadata(
                    player=player,
                    information_key=information_key,
                    actions=actions,
                    nodes=nodes,
                    source_probabilities=probabilities,
                )
            )
        return tuple(metadata)

    def _compile_best_response(
        self,
        builder: _TapeBuilder,
        target_player: int,
    ) -> tuple[int, tuple[_SelectorMetadata, ...]]:
        information_sets: dict[str, _InformationSet] = {}

        def collect(state_node: int, reach: float, player_depth: int) -> None:
            state = self._tree.nodes[state_node]
            if state.player == TERMINAL_PLAYER:
                return
            if state.player == CHANCE_PLAYER:
                for child, probability in zip(
                    state.children, state.probabilities, strict=True
                ):
                    collect(child, reach * probability, player_depth)
                return
            assert state.information_key is not None
            if state.player == target_player:
                entry = information_sets.get(state.information_key)
                if entry is None:
                    entry = _InformationSet(
                        actions=state.actions,
                        player_depth=player_depth,
                        members=[],
                    )
                    information_sets[state.information_key] = entry
                elif (
                    entry.actions != state.actions
                    or entry.player_depth != player_depth
                ):
                    raise ValueError(
                        "game violates action consistency or perfect recall at "
                        f"{state.information_key!r}"
                    )
                entry.members.append((state_node, reach))
                for child in state.children:
                    collect(child, reach, player_depth + 1)
                return
            for child, probability in zip(
                state.children, state.probabilities, strict=True
            ):
                collect(child, reach * probability, player_depth)

        for root_node in self._tree.root_nodes:
            collect(root_node, 1.0, 0)

        selector_by_key: dict[str, int] = {}
        selector_metadata: list[_SelectorMetadata] = []
        continuation_cache: dict[int, int] = {}

        def continuation(state_node: int) -> int:
            cached = continuation_cache.get(state_node)
            if cached is not None:
                return cached
            state = self._tree.nodes[state_node]
            if state.player == TERMINAL_PLAYER:
                assert state.returns is not None
                result = builder.constant(state.returns[target_player])
            elif state.player == target_player:
                assert state.information_key is not None
                selector = selector_by_key.get(state.information_key)
                if selector is None:
                    raise ValueError(
                        "best-response dependency was not compiled bottom-up at "
                        f"{state.information_key!r}"
                    )
                result = builder.select(
                    selector,
                    tuple(continuation(child) for child in state.children),
                )
            else:
                result = builder.affine(
                    tuple(
                        (continuation(child), probability)
                        for child, probability in zip(
                            state.children,
                            state.probabilities,
                            strict=True,
                        )
                    )
                )
            continuation_cache[state_node] = result
            return result

        ordered = sorted(
            information_sets.items(),
            key=lambda item: (item[1].player_depth, item[0]),
            reverse=True,
        )
        for information_key, entry in ordered:
            action_values = []
            for action_index in range(len(entry.actions)):
                terms = []
                for state_node, counterfactual_reach in entry.members:
                    if counterfactual_reach == 0.0:
                        continue
                    state = self._tree.nodes[state_node]
                    continuation_node = continuation(state.children[action_index])
                    weighted = builder.product(
                        self._root_inputs[state.root_outcome],
                        continuation_node,
                    )
                    terms.append((weighted, counterfactual_reach))
                action_values.append(builder.affine(tuple(terms)))
            selector = builder.argmax(tuple(action_values))
            selector_by_key[information_key] = selector
            selector_metadata.append(
                _SelectorMetadata(
                    player=target_player,
                    information_key=information_key,
                    actions=entry.actions,
                    node=selector,
                )
            )

        root_terms = []
        for outcome, root_node in enumerate(self._tree.root_nodes):
            root_terms.append(
                (
                    builder.product(
                        self._root_inputs[outcome],
                        continuation(root_node),
                    ),
                    1.0,
                )
            )
        return builder.affine(tuple(root_terms)), tuple(selector_metadata)

    def _compile_parameterized_best_response(
        self,
        builder: _TapeBuilder,
        target_player: int,
    ) -> tuple[int, tuple[_SelectorMetadata, ...]]:
        """Compile a BR whose counterfactual reach follows mutable opponents.

        The target player's own behavioral inputs are deliberately absent from
        this circuit. Opponent reach and continuations share the same policy
        input at every concrete member of an information set.
        """

        information_sets: dict[str, _InformationSet] = {}
        reach_nodes: dict[str, list[tuple[int, int]]] = {}

        def scaled_reach(reach: int, probability: float) -> int:
            return builder.affine(((reach, probability),))

        def collect(state_node: int, reach: int, player_depth: int) -> None:
            state = self._tree.nodes[state_node]
            if state.player == TERMINAL_PLAYER:
                return
            if state.player == CHANCE_PLAYER:
                for child, probability in zip(
                    state.children,
                    state.probabilities,
                    strict=True,
                ):
                    collect(child, scaled_reach(reach, probability), player_depth)
                return

            assert state.information_key is not None
            if state.player == target_player:
                entry = information_sets.get(state.information_key)
                if entry is None:
                    entry = _InformationSet(
                        actions=state.actions,
                        player_depth=player_depth,
                        members=[],
                    )
                    information_sets[state.information_key] = entry
                    reach_nodes[state.information_key] = []
                elif (
                    entry.actions != state.actions
                    or entry.player_depth != player_depth
                ):
                    raise ValueError(
                        "game violates action consistency or perfect recall at "
                        f"{state.information_key!r}"
                    )
                # The legacy member reach is not used in this path; retaining
                # the state list keeps the shared information-set structure.
                entry.members.append((state_node, 1.0))
                reach_nodes[state.information_key].append((state_node, reach))
                for child in state.children:
                    collect(child, reach, player_depth + 1)
                return

            policy_inputs = self._policy_inputs_by_key[state.information_key]
            for action, child in zip(state.actions, state.children, strict=True):
                collect(
                    child,
                    builder.product(reach, policy_inputs[action]),
                    player_depth,
                )

        for outcome, root_node in enumerate(self._tree.root_nodes):
            collect(root_node, self._root_inputs[outcome], 0)

        selector_by_key: dict[str, int] = {}
        selector_metadata: list[_SelectorMetadata] = []
        continuation_cache: dict[int, int] = {}

        def continuation(state_node: int) -> int:
            cached = continuation_cache.get(state_node)
            if cached is not None:
                return cached
            state = self._tree.nodes[state_node]
            if state.player == TERMINAL_PLAYER:
                assert state.returns is not None
                result = builder.constant(state.returns[target_player])
            elif state.player == target_player:
                assert state.information_key is not None
                selector = selector_by_key.get(state.information_key)
                if selector is None:
                    raise ValueError(
                        "best-response dependency was not compiled bottom-up at "
                        f"{state.information_key!r}"
                    )
                result = builder.select(
                    selector,
                    tuple(continuation(child) for child in state.children),
                )
            elif state.player == CHANCE_PLAYER:
                result = builder.affine(
                    tuple(
                        (continuation(child), probability)
                        for child, probability in zip(
                            state.children,
                            state.probabilities,
                            strict=True,
                        )
                    )
                )
            else:
                assert state.information_key is not None
                policy_inputs = self._policy_inputs_by_key[state.information_key]
                result = builder.affine(
                    tuple(
                        (
                            builder.product(
                                policy_inputs[action],
                                continuation(child),
                            ),
                            1.0,
                        )
                        for action, child in zip(
                            state.actions,
                            state.children,
                            strict=True,
                        )
                    )
                )
            continuation_cache[state_node] = result
            return result

        ordered = sorted(
            information_sets.items(),
            key=lambda item: (item[1].player_depth, item[0]),
            reverse=True,
        )
        for information_key, entry in ordered:
            action_values = []
            members = reach_nodes[information_key]
            for action_index in range(len(entry.actions)):
                terms = []
                for state_node, counterfactual_reach in members:
                    state = self._tree.nodes[state_node]
                    continuation_node = continuation(state.children[action_index])
                    terms.append(
                        (
                            builder.product(
                                counterfactual_reach,
                                continuation_node,
                            ),
                            1.0,
                        )
                    )
                action_values.append(builder.affine(tuple(terms)))
            selector = builder.argmax(tuple(action_values))
            selector_by_key[information_key] = selector
            selector_metadata.append(
                _SelectorMetadata(
                    player=target_player,
                    information_key=information_key,
                    actions=entry.actions,
                    node=selector,
                )
            )

        return (
            builder.affine(
                tuple(
                    (
                        builder.product(
                            self._root_inputs[outcome],
                            continuation(root_node),
                        ),
                        1.0,
                    )
                    for outcome, root_node in enumerate(self._tree.root_nodes)
                )
            ),
            tuple(selector_metadata),
        )

    def _node_inputs(self, node: int) -> range:
        offset = self._input_offsets[node]
        return range(offset, offset + self._input_counts[node])

    def _compute_node(
        self,
        node: int,
        read_value: Callable[[int], float],
        read_selection: Callable[[int], int],
    ) -> tuple[float, int]:
        kind = self._kinds[node]
        edges = self._node_inputs(node)
        value_at = read_value  # Local aliases keep the operation equations compact.
        selection_at = read_selection
        if kind == _AFFINE:
            value = fsum(
                self._edge_weights[edge] * value_at(self._edge_inputs[edge])
                for edge in edges
            )
            selection = -1
        elif kind == _PRODUCT:
            edge_list = tuple(edges)
            if len(edge_list) != 2:
                raise AssertionError("product node must have two inputs")
            value = value_at(self._edge_inputs[edge_list[0]]) * value_at(
                self._edge_inputs[edge_list[1]]
            )
            selection = -1
        elif kind == _ARGMAX:
            edge_list = tuple(edges)
            first_value = value_at(self._edge_inputs[edge_list[0]])
            value = first_value
            selection = 0
            for action_index, edge in enumerate(edge_list[1:], start=1):
                candidate = value_at(self._edge_inputs[edge])
                if candidate > value:
                    value = candidate
                    selection = action_index
        elif kind == _SELECT:
            edge_list = tuple(edges)
            selector = self._edge_inputs[edge_list[0]]
            selected = selection_at(selector)
            if selected < 0 or selected >= len(edge_list) - 1:
                raise AssertionError("selector action is outside continuation inputs")
            value = value_at(self._edge_inputs[edge_list[1 + selected]])
            selection = -1
        else:
            raise AssertionError(f"node {node} is not a computed operation")
        if not isfinite(value):
            raise FloatingPointError(f"nonfinite value at tape node {node}")
        return value, selection

    def _evaluate_base(self) -> None:
        def read_value(node: int) -> float:
            return self._base_values[node]

        def read_selection(node: int) -> int:
            return self._base_selections[node]

        for node, kind in enumerate(self._kinds):
            if kind in (_INPUT, _CONSTANT):
                continue
            value, selection = self._compute_node(
                node,
                read_value,
                read_selection,
            )
            self._base_values[node] = value
            self._base_selections[node] = selection

    def _build_reverse_dependencies(self) -> tuple[array[int], array[int]]:
        dependents: list[list[int]] = [[] for _ in self._kinds]
        for consumer in range(len(self._kinds)):
            seen = set()
            for edge in self._node_inputs(consumer):
                dependency = self._edge_inputs[edge]
                if dependency not in seen:
                    dependents[dependency].append(consumer)
                    seen.add(dependency)
        offsets = array("I", [0])
        flat = array("I")
        for entries in dependents:
            flat.extend(entries)
            offsets.append(len(flat))
        return offsets, flat

    def _base_evaluation(self) -> EvaluationResult:
        utilities = tuple(self._base_values[node] for node in self._utility_outputs)
        best_responses = tuple(
            self._base_values[node] for node in self._best_response_outputs
        )
        deviation_gains = tuple(
            max(0.0, best - utility)
            for best, utility in zip(best_responses, utilities, strict=True)
        )
        nash_conv = fsum(deviation_gains)
        return EvaluationResult(
            utilities=utilities,
            best_response_values=best_responses,
            deviation_gains=deviation_gains,
            nash_conv=nash_conv,
            exploitability=(nash_conv / 2.0 if len(utilities) == 2 else None),
        )

    def _actions_from_base(self) -> tuple[dict[str, Action], ...]:
        result = [dict() for _ in range(self._tree.num_players)]
        for metadata in self._selectors:
            selected = self._base_selections[metadata.node]
            result[metadata.player][metadata.information_key] = metadata.actions[selected]
        return tuple(result)

    def _current_value(self, node: int) -> float:
        return (
            self._overlay_values[node]
            if self._value_epochs[node] == self._epoch
            else self._base_values[node]
        )

    def _current_selection(self, node: int) -> int:
        return (
            self._overlay_selections[node]
            if self._value_epochs[node] == self._epoch
            else self._base_selections[node]
        )

    def _current_evaluation(self) -> EvaluationResult:
        utilities = tuple(self._current_value(node) for node in self._utility_outputs)
        best_responses = tuple(
            self._current_value(node) for node in self._best_response_outputs
        )
        deviation_gains = tuple(
            max(0.0, best - utility)
            for best, utility in zip(best_responses, utilities, strict=True)
        )
        nash_conv = fsum(deviation_gains)
        return EvaluationResult(
            utilities=utilities,
            best_response_values=best_responses,
            deviation_gains=deviation_gains,
            nash_conv=nash_conv,
            exploitability=(nash_conv / 2.0 if len(utilities) == 2 else None),
        )

    def _current_actions(self) -> tuple[dict[str, Action], ...]:
        result = [dict() for _ in range(self._tree.num_players)]
        for metadata in self._selectors:
            selected = self._current_selection(metadata.node)
            result[metadata.player][metadata.information_key] = metadata.actions[selected]
        return tuple(result)

    def _next_epoch(self) -> None:
        if self._epoch >= 0xFFFFFFFE:
            self._value_epochs = array("I", (0 for _ in self._value_epochs))
            self._dirty_epochs = array("I", (0 for _ in self._dirty_epochs))
            self._epoch = 1
        else:
            self._epoch += 1

    def _validated_probabilities(
        self,
        probabilities: Mapping[Action, float],
    ) -> tuple[float, ...]:
        unknown = set(probabilities) - set(self._tree.outcome_index)
        if unknown:
            raise ValueError(
                f"probabilities contain outcomes outside the topology epoch: {unknown!r}"
            )
        prepared = []
        for outcome in self._tree.outcomes:
            value = float(probabilities.get(outcome, 0.0))
            if not isfinite(value) or value < 0.0:
                raise ValueError("root probabilities must be finite and nonnegative")
            prepared.append(value)
        if abs(fsum(prepared) - 1.0) > 1e-12:
            raise ValueError("root probabilities must sum to one")
        return tuple(prepared)

    def _validated_policy(
        self,
        policy: Mapping[str, Mapping[Action, float]],
    ) -> tuple[tuple[float, ...], ...]:
        if not self._parameterize_policy:
            raise ValueError("this tape was compiled without mutable policy inputs")
        expected = {entry.information_key for entry in self._policy_metadata}
        missing = expected - set(policy)
        unknown = set(policy) - expected
        if missing or unknown:
            raise ValueError(
                "policy must contain exactly the compiled information schema: "
                f"missing={sorted(missing)!r}, unknown={sorted(unknown)!r}"
            )

        prepared = []
        for entry in self._policy_metadata:
            distribution = policy[entry.information_key]
            missing_actions = set(entry.actions) - set(distribution)
            unknown_actions = set(distribution) - set(entry.actions)
            if missing_actions or unknown_actions:
                raise ValueError(
                    "policy action schema mismatch at "
                    f"{entry.information_key!r}: missing={sorted(missing_actions, key=repr)!r}, "
                    f"unknown={sorted(unknown_actions, key=repr)!r}"
                )
            values = tuple(float(distribution[action]) for action in entry.actions)
            if any(not isfinite(value) or value < 0.0 for value in values):
                raise ValueError(
                    "policy probabilities must be finite and nonnegative at "
                    f"{entry.information_key!r}"
                )
            if abs(fsum(values) - 1.0) > 1e-12:
                raise ValueError(
                    f"policy probabilities must sum to one at {entry.information_key!r}"
                )
            prepared.append(values)
        return tuple(prepared)

    def _recertify_changed_inputs(
        self,
        changed_inputs: Sequence[tuple[int, float]],
        *,
        mode: ExecutionMode,
        changed_root_outcomes: int,
        changed_policy_entries: int,
        changed_policy_information_sets: int,
        collect_actions: bool = True,
    ) -> DependencyTapeResult:
        if mode not in ("auto", "sparse", "dense"):
            raise ValueError(f"unsupported execution mode {mode!r}")
        if not changed_inputs:
            return self._source_result

        self._next_epoch()
        dirty_nodes: list[int] = []
        stack = []
        for node, value in changed_inputs:
            self._overlay_values[node] = value
            self._value_epochs[node] = self._epoch
            if self._dirty_epochs[node] != self._epoch:
                self._dirty_epochs[node] = self._epoch
                dirty_nodes.append(node)
                stack.append(node)

        while stack:
            dependency = stack.pop()
            start = self._dependent_offsets[dependency]
            end = self._dependent_offsets[dependency + 1]
            for position in range(start, end):
                consumer = self._dependents[position]
                if self._dirty_epochs[consumer] == self._epoch:
                    continue
                self._dirty_epochs[consumer] = self._epoch
                dirty_nodes.append(consumer)
                stack.append(consumer)

        dirty_fraction = len(dirty_nodes) / len(self._kinds)
        selected_mode = (
            "dense"
            if mode == "dense"
            or (mode == "auto" and dirty_fraction >= self._dense_threshold)
            else "sparse"
        )
        if selected_mode == "dense":
            recompute = self._operation_nodes
        else:
            recompute = tuple(
                node
                for node in sorted(dirty_nodes)
                if self._kinds[node] not in (_INPUT, _CONSTANT)
            )

        for node in recompute:
            value, selection = self._compute_node(
                node,
                self._current_value,
                self._current_selection,
            )
            self._overlay_values[node] = value
            self._overlay_selections[node] = selection
            self._value_epochs[node] = self._epoch

        action_flips = (
            sum(
                self._current_selection(metadata.node)
                != self._base_selections[metadata.node]
                for metadata in self._selectors
            )
            if collect_actions
            else 0
        )
        return DependencyTapeResult(
            evaluation=self._current_evaluation(),
            best_response_actions=(
                self._current_actions()
                if collect_actions
                else tuple({} for _ in range(self._tree.num_players))
            ),
            diagnostics=self._diagnostics(
                execution_mode=selected_mode,
                changed=changed_root_outcomes,
                dirty=len(dirty_nodes),
                recomputed=len(recompute),
                action_flips=action_flips,
                changed_policy_entries=changed_policy_entries,
                changed_policy_information_sets=changed_policy_information_sets,
            ),
        )

    def recertify(
        self,
        probabilities: Mapping[Action, float],
        *,
        mode: ExecutionMode = "auto",
    ) -> DependencyTapeResult:
        """Evaluate a target distribution from immutable source tape values."""

        target = self._validated_probabilities(probabilities)
        changed = [
            index
            for index, (source, current) in enumerate(
                zip(self._tree.source_probabilities, target, strict=True)
            )
            if source != current
        ]
        return self._recertify_changed_inputs(
            tuple((self._root_inputs[index], target[index]) for index in changed),
            mode=mode,
            changed_root_outcomes=len(changed),
            changed_policy_entries=0,
            changed_policy_information_sets=0,
        )

    def recertify_policy(
        self,
        policy: Mapping[str, Mapping[Action, float]],
        *,
        mode: ExecutionMode = "auto",
    ) -> DependencyTapeResult:
        """Evaluate a complete target policy from immutable source values."""

        target = self._validated_policy(policy)
        changed_inputs = []
        changed_information_sets = 0
        for entry, values in zip(self._policy_metadata, target, strict=True):
            entry_changed = False
            for node, source, current in zip(
                entry.nodes,
                entry.source_probabilities,
                values,
                strict=True,
            ):
                if abs(source - current) <= self._changed_policy_tolerance:
                    continue
                changed_inputs.append((node, current))
                entry_changed = True
            changed_information_sets += entry_changed
        return self._recertify_changed_inputs(
            tuple(changed_inputs),
            mode=mode,
            changed_root_outcomes=0,
            changed_policy_entries=len(changed_inputs),
            changed_policy_information_sets=changed_information_sets,
        )

    def evaluate_policy(
        self,
        policy: Mapping[str, Mapping[Action, float]],
        *,
        mode: ExecutionMode = "auto",
    ) -> EvaluationResult:
        """Evaluate a policy without materializing best-response action maps."""

        target = self._validated_policy(policy)
        changed_inputs = []
        changed_information_sets = 0
        for entry, values in zip(self._policy_metadata, target, strict=True):
            entry_changed = False
            for node, source, current in zip(
                entry.nodes,
                entry.source_probabilities,
                values,
                strict=True,
            ):
                if abs(source - current) <= self._changed_policy_tolerance:
                    continue
                changed_inputs.append((node, current))
                entry_changed = True
            changed_information_sets += entry_changed
        return self._recertify_changed_inputs(
            tuple(changed_inputs),
            mode=mode,
            changed_root_outcomes=0,
            changed_policy_entries=len(changed_inputs),
            changed_policy_information_sets=changed_information_sets,
            collect_actions=False,
        ).evaluation

    def recertify_profile(
        self,
        probabilities: Mapping[Action, float],
        policy: Mapping[str, Mapping[Action, float]],
        *,
        mode: ExecutionMode = "auto",
    ) -> DependencyTapeResult:
        """Evaluate simultaneous root-range and behavioral-policy changes."""

        target_probabilities = self._validated_probabilities(probabilities)
        target_policy = self._validated_policy(policy)
        changed_inputs: list[tuple[int, float]] = []
        changed_roots = 0
        for node, source, current in zip(
            self._root_inputs,
            self._tree.source_probabilities,
            target_probabilities,
            strict=True,
        ):
            if source != current:
                changed_inputs.append((node, current))
                changed_roots += 1
        changed_policy_entries = 0
        changed_information_sets = 0
        for entry, values in zip(self._policy_metadata, target_policy, strict=True):
            entry_changed = False
            for node, source, current in zip(
                entry.nodes,
                entry.source_probabilities,
                values,
                strict=True,
            ):
                if abs(source - current) <= self._changed_policy_tolerance:
                    continue
                changed_inputs.append((node, current))
                changed_policy_entries += 1
                entry_changed = True
            changed_information_sets += entry_changed
        return self._recertify_changed_inputs(
            tuple(changed_inputs),
            mode=mode,
            changed_root_outcomes=changed_roots,
            changed_policy_entries=changed_policy_entries,
            changed_policy_information_sets=changed_information_sets,
        )

    def recertify_game(
        self,
        game: ExtensiveFormGame,
        *,
        mode: ExecutionMode = "auto",
    ) -> DependencyTapeResult:
        distribution = self._tree.distribution_for_game(game)
        return self.recertify(distribution, mode=mode)

    def _diagnostics(
        self,
        *,
        execution_mode: str,
        changed: int,
        dirty: int,
        recomputed: int,
        action_flips: int,
        changed_policy_entries: int,
        changed_policy_information_sets: int,
    ) -> DependencyTapeDiagnostics:
        return DependencyTapeDiagnostics(
            execution_mode=execution_mode,
            changed_root_outcomes=changed,
            dirty_nodes=dirty,
            dirty_node_fraction=(dirty / len(self._kinds) if self._kinds else 0.0),
            recomputed_nodes=recomputed,
            selector_nodes=len(self._selectors),
            best_response_action_flips=action_flips,
            numeric_nodes=len(self._kinds),
            dependency_edges=len(self._edge_inputs),
            contiguous_runtime_bytes=self.contiguous_runtime_bytes,
            changed_policy_entries=changed_policy_entries,
            changed_policy_information_sets=changed_policy_information_sets,
            policy_input_entries=sum(
                len(entry.nodes) for entry in self._policy_metadata
            ),
        )

    @property
    def source_result(self) -> DependencyTapeResult:
        return self._source_result

    @property
    def root_outcomes(self) -> tuple[Action, ...]:
        return tuple(self._tree.outcomes)

    @property
    def policy_input_schema(self) -> dict[str, tuple[Action, ...]]:
        return {
            entry.information_key: entry.actions
            for entry in self._policy_metadata
        }

    @property
    def source_policy(self) -> Policy:
        return {
            entry.information_key: dict(
                zip(entry.actions, entry.source_probabilities, strict=True)
            )
            for entry in self._policy_metadata
        }

    @property
    def node_kinds(self) -> memoryview:
        return memoryview(self._kinds).toreadonly()

    @property
    def input_offsets(self) -> memoryview:
        return memoryview(self._input_offsets).toreadonly()

    @property
    def input_counts(self) -> memoryview:
        return memoryview(self._input_counts).toreadonly()

    @property
    def edge_inputs(self) -> memoryview:
        return memoryview(self._edge_inputs).toreadonly()

    @property
    def contiguous_runtime_bytes(self) -> int:
        arrays = (
            self._kinds,
            self._input_offsets,
            self._input_counts,
            self._edge_inputs,
            self._edge_weights,
            self._base_values,
            self._base_selections,
            self._dependent_offsets,
            self._dependents,
            self._overlay_values,
            self._overlay_selections,
            self._value_epochs,
            self._dirty_epochs,
        )
        return sum(values.itemsize * len(values) for values in arrays)

    def topology_summary(self) -> dict[str, object]:
        operation_counts = {
            name: sum(kind == index for kind in self._kinds)
            for index, name in enumerate(_OPERATION_NAMES)
        }
        return {
            "root_outcomes": len(self._tree.outcomes),
            "policy_information_sets": len(self._policy_metadata),
            "policy_input_entries": sum(
                len(entry.nodes) for entry in self._policy_metadata
            ),
            "compiled_tree_states": len(self._tree.nodes),
            "numeric_nodes": len(self._kinds),
            "dependency_edges": len(self._edge_inputs),
            "selector_nodes": len(self._selectors),
            "contiguous_runtime_bytes": self.contiguous_runtime_bytes,
            "operation_counts": operation_counts,
            "dependencies_are_topological": all(
                self._edge_inputs[edge] < node
                for node in range(len(self._kinds))
                for edge in self._node_inputs(node)
            ),
        }


class CompiledPolicyDeltaTape(CompiledPolicyDependencyTape):
    """Exact source-relative tape with mutable range and policy inputs.

    ``recertify_policy`` is the primary policy-delta entry point.
    ``recertify_profile`` can change both root probabilities and policy in one
    source-relative epoch. The original ``recertify`` and ``recertify_game``
    methods remain available for range-only controls.
    """

    def __init__(
        self,
        source_game: ExtensiveFormGame,
        policy: Policy,
        *,
        universe_games: Sequence[ExtensiveFormGame] = (),
        dense_threshold: float = 0.35,
        changed_policy_tolerance: float = 0.0,
    ) -> None:
        super().__init__(
            source_game,
            policy,
            universe_games=universe_games,
            dense_threshold=dense_threshold,
            _parameterize_policy=True,
            _changed_policy_tolerance=changed_policy_tolerance,
        )
