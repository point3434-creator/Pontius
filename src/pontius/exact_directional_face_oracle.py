"""Exact directional sensitivity over a best-response face without tapes.

The oracle solves two independent lexicographic best responses over the same
explicit finite tree.  Both first maximize the exact response value at one
point on a sequence-form realization segment; one then minimizes and the
other maximizes the exact directional slope.  The active face is represented
as per-information-set maximizing-action factors.  No Cartesian response-tape
product is constructed.

The companion composition keeps responsibilities separate: the retained exact
selector fan locates cells and facets along the full ray, while this oracle
describes the complete active face at each critical point or cell witness.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Any, Mapping, TypeAlias

from .exact_selector_fan import (
    ExactSelectorFanSection,
    ResponseTape,
    map_exact_selector_fan_section,
    realization_interpolated_policy,
)
from .exact_selector_window_oracle import (
    exact_best_response_trace,
    exact_fixed_response_trace,
    exact_policy_utilities,
)
from .exact_sequence_form_coefficient_oracle import exact_sequence_axis
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, ExtensiveFormGame, GameState


ExactPolicy: TypeAlias = Mapping[str, Mapping[Action, Fraction | float]]


@dataclass(frozen=True, slots=True)
class ExactDirectionalFaceInformationSet:
    """One factor in the exact value-optimal response face."""

    key: str
    actions: tuple[Action, ...]
    parent: tuple[str, Action] | None
    maximizing_actions: tuple[Action, ...]
    positive_counterfactual_support: bool
    minimum_slope_action: Action
    maximum_slope_action: Action
    minimum_local_slope: Fraction
    maximum_local_slope: Fraction
    state_count: int


@dataclass(frozen=True, slots=True)
class ExactDirectionalFaceWorkLedger:
    """Logical work whose ceiling is independent of face cardinality."""

    tree_nodes: int
    tree_edges: int
    target_action_edges: int
    information_sets: int
    sequence_variables: int
    lexicographic_passes: int
    minimum_continuation_node_evaluations: int
    maximum_continuation_node_evaluations: int
    minimum_action_score_terms: int
    maximum_action_score_terms: int
    minimum_action_choice_inspections: int
    maximum_action_choice_inspections: int
    per_pass_linear_work_ceiling: int
    total_cardinality_multiplications: int
    reachable_cardinality_additions: int
    reachable_cardinality_multiplications: int
    cardinality_linear_work_ceiling: int
    total_cardinality_bit_length: int
    reachable_cardinality_bit_length: int
    total_logical_work_units: int
    materialized_response_tapes: int


@dataclass(frozen=True, slots=True)
class ExactDirectionalFace:
    """Exact value, slope interval, identities, and cardinalities at one point."""

    acting_player: int
    target_player: int
    scale: Fraction
    response_value: Fraction
    profile_utility: Fraction
    deviation_gain: Fraction
    minimum_response_slope: Fraction
    maximum_response_slope: Fraction
    profile_utility_slope: Fraction
    minimum_gain_slope: Fraction
    maximum_gain_slope: Fraction
    minimum_slope_tape: ResponseTape
    maximum_slope_tape: ResponseTape
    total_function_cardinality: int
    reachable_support_cardinality: int
    information_sets: tuple[ExactDirectionalFaceInformationSet, ...]
    work: ExactDirectionalFaceWorkLedger


@dataclass(frozen=True, slots=True)
class ExactFanCellGainRow:
    """One representative affine gain row retained by the normal fan."""

    response_tape: ResponseTape
    lower: Fraction
    upper: Fraction
    intercept: Fraction
    slope: Fraction

    def value(self, scale: Fraction) -> Fraction:
        return self.intercept + scale * self.slope


@dataclass(frozen=True, slots=True)
class ExactDirectionalFaceFanSample:
    """One composed fan-location and active-face observation."""

    scale: Fraction
    sample_kind: str
    total_state: str
    reachable_state: str
    maximum_cell_gain: Fraction
    active_cell_rows: int
    face: ExactDirectionalFace


@dataclass(frozen=True, slots=True)
class ExactDirectionalFaceFanSection:
    """A full ray partition composed with exact face sensitivity."""

    fan: ExactSelectorFanSection
    cell_rows: tuple[ExactFanCellGainRow, ...]
    samples: tuple[ExactDirectionalFaceFanSample, ...]
    crossing_scales: tuple[Fraction, ...]


@dataclass(frozen=True, slots=True)
class _TreeNode:
    ordinal: int
    current_player: int
    target_depth: int
    information_key: str | None
    actions: tuple[Action, ...]
    children: tuple[int, ...]
    source_weights: tuple[Fraction, ...]
    endpoint_weights: tuple[Fraction, ...]
    terminal_payoff: Fraction | None


@dataclass(slots=True)
class _InformationSet:
    actions: tuple[Action, ...]
    target_depth: int
    states: list[tuple[int, Fraction, Fraction]]


@dataclass(frozen=True, slots=True)
class _PassInformationSet:
    current_values: tuple[Fraction, ...]
    slopes: tuple[Fraction, ...]
    maximizing_actions: tuple[Action, ...]
    selected_action: Action


@dataclass(frozen=True, slots=True)
class _LexicographicPass:
    selected_actions: Mapping[str, Action]
    information_sets: Mapping[str, _PassInformationSet]
    root_source_value: Fraction
    root_endpoint_value: Fraction
    continuation_node_evaluations: int
    action_score_terms: int
    action_choice_inspections: int


def _fraction(value: Fraction | float) -> Fraction:
    if isinstance(value, bool):
        raise TypeError("Boolean is not an exact directional-face scalar")
    return value if isinstance(value, Fraction) else Fraction.from_float(float(value))


def _distribution(
    policy: ExactPolicy,
    key: str,
    actions: tuple[Action, ...],
) -> tuple[Fraction, ...]:
    supplied = policy.get(key)
    if supplied is None:
        return (Fraction(1, len(actions)),) * len(actions)
    if set(supplied) - set(actions):
        raise ValueError("directional-face policy contains an unavailable action")
    weights = tuple(_fraction(supplied.get(action, 0.0)) for action in actions)
    if any(value < 0 for value in weights):
        raise ValueError("directional-face policy contains a negative probability")
    total = sum(weights, Fraction(0))
    if total <= 0:
        raise ValueError("directional-face policy has zero probability mass")
    return tuple(value / total for value in weights)


def _build_tree(
    game: ExtensiveFormGame,
    source_policy: ExactPolicy,
    endpoint_policy: ExactPolicy,
    *,
    target_player: int,
    maximum_tree_nodes: int,
) -> tuple[tuple[_TreeNode, ...], int]:
    nodes: list[_TreeNode | None] = []

    def build(state: GameState, target_depth: int) -> int:
        if len(nodes) >= maximum_tree_nodes:
            raise RuntimeError("exact directional face exceeds compact-state bound")
        ordinal = len(nodes)
        nodes.append(None)
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            returns = tuple(_fraction(value) for value in state.returns())
            if len(returns) != game.num_players:
                raise ValueError("directional-face terminal utility width differs")
            node = _TreeNode(
                ordinal,
                acting,
                target_depth,
                None,
                (),
                (),
                (),
                (),
                returns[target_player],
            )
            nodes[ordinal] = node
            return ordinal

        if acting == CHANCE_PLAYER:
            outcomes = tuple(state.chance_outcomes())
            actions = tuple(action for action, _ in outcomes)
            weights = tuple(_fraction(probability) for _, probability in outcomes)
            if not outcomes or sum(weights, Fraction(0)) != 1:
                raise ValueError("directional-face chance mass differs from one")
            children = tuple(
                build(state.apply_action(action), target_depth) for action in actions
            )
            node = _TreeNode(
                ordinal,
                acting,
                target_depth,
                None,
                actions,
                children,
                weights,
                weights,
                None,
            )
            nodes[ordinal] = node
            return ordinal

        actions = tuple(state.legal_actions())
        if not actions:
            raise ValueError("directional-face strategic node has no actions")
        key = state.information_state_key(acting)
        next_depth = target_depth + 1 if acting == target_player else target_depth
        children = tuple(
            build(state.apply_action(action), next_depth) for action in actions
        )
        if acting == target_player:
            source_weights: tuple[Fraction, ...] = ()
            endpoint_weights: tuple[Fraction, ...] = ()
        else:
            source_weights = _distribution(source_policy, key, actions)
            endpoint_weights = _distribution(endpoint_policy, key, actions)
        node = _TreeNode(
            ordinal,
            acting,
            target_depth,
            key,
            actions,
            children,
            source_weights,
            endpoint_weights,
            None,
        )
        nodes[ordinal] = node
        return ordinal

    root = build(game.initial_state(), 0)
    if any(node is None for node in nodes):
        raise AssertionError("directional-face tree construction left a hole")
    return tuple(node for node in nodes if node is not None), root


def _collect_information_sets(
    nodes: tuple[_TreeNode, ...],
    root: int,
    *,
    target_player: int,
) -> dict[str, _InformationSet]:
    information_sets: dict[str, _InformationSet] = {}

    def collect(index: int, source_reach: Fraction, endpoint_reach: Fraction) -> None:
        node = nodes[index]
        if node.current_player == TERMINAL_PLAYER:
            return
        if node.current_player == target_player:
            if node.information_key is None:
                raise AssertionError("target node has no information key")
            entry = information_sets.get(node.information_key)
            if entry is None:
                entry = _InformationSet(node.actions, node.target_depth, [])
                information_sets[node.information_key] = entry
            elif (
                entry.actions != node.actions
                or entry.target_depth != node.target_depth
            ):
                raise ValueError(
                    "directional face found imperfect recall or action drift"
                )
            entry.states.append((index, source_reach, endpoint_reach))
            for child in node.children:
                collect(child, source_reach, endpoint_reach)
            return
        for offset, child in enumerate(node.children):
            collect(
                child,
                source_reach * node.source_weights[offset],
                endpoint_reach * node.endpoint_weights[offset],
            )

    collect(root, Fraction(1), Fraction(1))
    return information_sets


def _solve_lexicographic_pass(
    nodes: tuple[_TreeNode, ...],
    root: int,
    information_sets: Mapping[str, _InformationSet],
    *,
    target_player: int,
    scale: Fraction,
    maximize_slope: bool,
) -> _LexicographicPass:
    selected: dict[str, Action] = {}
    traces: dict[str, _PassInformationSet] = {}
    cache: list[tuple[Fraction, Fraction] | None] = [None] * len(nodes)
    continuation_evaluations = 0
    score_terms = 0
    choice_inspections = 0

    def continuation(index: int) -> tuple[Fraction, Fraction]:
        nonlocal continuation_evaluations
        cached = cache[index]
        if cached is not None:
            return cached
        continuation_evaluations += 1
        node = nodes[index]
        if node.current_player == TERMINAL_PLAYER:
            if node.terminal_payoff is None:
                raise AssertionError("terminal node has no payoff")
            result = (node.terminal_payoff, node.terminal_payoff)
        elif node.current_player == target_player:
            if node.information_key is None:
                raise AssertionError("target node has no information key")
            try:
                action = selected[node.information_key]
            except KeyError as exc:
                raise ArithmeticError(
                    "directional-face dependency was not solved bottom-up"
                ) from exc
            result = continuation(node.children[node.actions.index(action)])
        else:
            source = Fraction(0)
            endpoint = Fraction(0)
            for offset, child in enumerate(node.children):
                child_source, child_endpoint = continuation(child)
                source += node.source_weights[offset] * child_source
                endpoint += node.endpoint_weights[offset] * child_endpoint
            result = (source, endpoint)
        cache[index] = result
        return result

    ordered = sorted(
        information_sets.items(),
        key=lambda item: (item[1].target_depth, item[0]),
        reverse=True,
    )
    for key, entry in ordered:
        action_pairs: list[tuple[Fraction, Fraction]] = []
        for offset, _action in enumerate(entry.actions):
            source = Fraction(0)
            endpoint = Fraction(0)
            for state_index, source_reach, endpoint_reach in entry.states:
                child = nodes[state_index].children[offset]
                child_source, child_endpoint = continuation(child)
                source += source_reach * child_source
                endpoint += endpoint_reach * child_endpoint
                score_terms += 1
            action_pairs.append((source, endpoint))
        current_values = tuple(
            (Fraction(1) - scale) * source + scale * endpoint
            for source, endpoint in action_pairs
        )
        slopes = tuple(endpoint - source for source, endpoint in action_pairs)
        maximum = max(current_values)
        maximizing_offsets = tuple(
            offset
            for offset, value in enumerate(current_values)
            if value == maximum
        )
        choice_inspections += len(entry.actions)
        slope_extreme = (
            max(slopes[offset] for offset in maximizing_offsets)
            if maximize_slope
            else min(slopes[offset] for offset in maximizing_offsets)
        )
        selected_offset = next(
            offset
            for offset in maximizing_offsets
            if slopes[offset] == slope_extreme
        )
        selected[key] = entry.actions[selected_offset]
        traces[key] = _PassInformationSet(
            current_values=current_values,
            slopes=slopes,
            maximizing_actions=tuple(
                entry.actions[offset] for offset in maximizing_offsets
            ),
            selected_action=entry.actions[selected_offset],
        )

    root_source, root_endpoint = continuation(root)
    return _LexicographicPass(
        selected_actions=MappingProxyType(dict(sorted(selected.items()))),
        information_sets=MappingProxyType(dict(sorted(traces.items()))),
        root_source_value=root_source,
        root_endpoint_value=root_endpoint,
        continuation_node_evaluations=continuation_evaluations,
        action_score_terms=score_terms,
        action_choice_inspections=choice_inspections,
    )


def _reachable_support_cardinality(
    axis: Any,
    maximizing: Mapping[str, tuple[Action, ...]],
    support: Mapping[str, bool],
) -> tuple[int, int, int]:
    children: dict[tuple[str, Action], list[str]] = {}
    roots: list[str] = []
    for information_set in axis.information_sets:
        if information_set.parent is None:
            roots.append(information_set.key)
        else:
            children.setdefault(information_set.parent, []).append(
                information_set.key
            )
    counts: dict[str, int] = {}
    additions = 0
    multiplications = 0
    for information_set in reversed(axis.information_sets):
        key = information_set.key
        if not support[key]:
            counts[key] = 1
            continue
        count = 0
        for action in maximizing[key]:
            branch = 1
            for child in children.get((key, action), ()):
                branch *= counts[child]
                multiplications += 1
            count += branch
            additions += 1
        counts[key] = count
    result = 1
    for key in roots:
        result *= counts[key]
        multiplications += 1
    return result, additions, multiplications


def exact_directional_best_response_face(
    game: ExtensiveFormGame,
    source_policy: ExactPolicy,
    endpoint_policy: ExactPolicy,
    *,
    acting_player: int,
    target_player: int,
    scale: Fraction,
    maximum_tree_nodes: int = 100_000,
) -> ExactDirectionalFace:
    """Compute exact active-face slope extrema in two cardinality-free passes."""

    if isinstance(acting_player, bool) or acting_player not in range(game.num_players):
        raise ValueError("directional-face acting player is outside the game")
    if isinstance(target_player, bool) or target_player not in range(game.num_players):
        raise ValueError("directional-face target player is outside the game")
    if not isinstance(scale, Fraction) or scale < 0 or scale > 1:
        raise ValueError("directional-face scale must be a Fraction inside [0, 1]")
    if (
        isinstance(maximum_tree_nodes, bool)
        or not isinstance(maximum_tree_nodes, int)
        or maximum_tree_nodes <= 0
    ):
        raise ValueError("directional-face compact-state bound must be positive")

    source = realization_interpolated_policy(
        game,
        source_policy,
        endpoint_policy,
        acting_player=acting_player,
        scale=Fraction(0),
    )
    endpoint = realization_interpolated_policy(
        game,
        source_policy,
        endpoint_policy,
        acting_player=acting_player,
        scale=Fraction(1),
    )
    current = realization_interpolated_policy(
        game,
        source_policy,
        endpoint_policy,
        acting_player=acting_player,
        scale=scale,
    )
    nodes, root = _build_tree(
        game,
        source,
        endpoint,
        target_player=target_player,
        maximum_tree_nodes=maximum_tree_nodes,
    )
    information_sets = _collect_information_sets(
        nodes,
        root,
        target_player=target_player,
    )
    minimum = _solve_lexicographic_pass(
        nodes,
        root,
        information_sets,
        target_player=target_player,
        scale=scale,
        maximize_slope=False,
    )
    maximum = _solve_lexicographic_pass(
        nodes,
        root,
        information_sets,
        target_player=target_player,
        scale=scale,
        maximize_slope=True,
    )

    axis = exact_sequence_axis(game, target_player)
    axis_by_key = {row.key: row for row in axis.information_sets}
    if set(axis_by_key) != set(information_sets):
        raise ArithmeticError("directional-face sequence axis differs from tree")
    current_trace = exact_best_response_trace(game, current, target_player)
    trace_by_key = {row.key: row for row in current_trace.information_sets}
    if set(trace_by_key) != set(information_sets):
        raise ArithmeticError("directional-face independent trace schema differs")

    factors: list[ExactDirectionalFaceInformationSet] = []
    maximizing_by_key: dict[str, tuple[Action, ...]] = {}
    support_by_key: dict[str, bool] = {}
    for axis_row in axis.information_sets:
        key = axis_row.key
        entry = information_sets[key]
        minimum_row = minimum.information_sets[key]
        maximum_row = maximum.information_sets[key]
        independent = trace_by_key[key]
        if (
            entry.actions != axis_row.actions
            or entry.actions != independent.actions
            or minimum_row.current_values != maximum_row.current_values
            or minimum_row.maximizing_actions != maximum_row.maximizing_actions
            or minimum_row.maximizing_actions != independent.maximizing_actions
        ):
            raise ArithmeticError("directional-face factor identities differ")
        minimum_offset = entry.actions.index(minimum_row.selected_action)
        maximum_offset = entry.actions.index(maximum_row.selected_action)
        positive = any(
            (Fraction(1) - scale) * source_reach + scale * endpoint_reach > 0
            for _, source_reach, endpoint_reach in entry.states
        )
        if minimum_row.slopes[minimum_offset] > maximum_row.slopes[maximum_offset]:
            raise ArithmeticError("directional-face local slope interval is reversed")
        maximizing_by_key[key] = minimum_row.maximizing_actions
        support_by_key[key] = positive
        factors.append(
            ExactDirectionalFaceInformationSet(
                key=key,
                actions=entry.actions,
                parent=axis_row.parent,
                maximizing_actions=minimum_row.maximizing_actions,
                positive_counterfactual_support=positive,
                minimum_slope_action=minimum_row.selected_action,
                maximum_slope_action=maximum_row.selected_action,
                minimum_local_slope=minimum_row.slopes[minimum_offset],
                maximum_local_slope=maximum_row.slopes[maximum_offset],
                state_count=len(entry.states),
            )
        )

    minimum_current = (
        (Fraction(1) - scale) * minimum.root_source_value
        + scale * minimum.root_endpoint_value
    )
    maximum_current = (
        (Fraction(1) - scale) * maximum.root_source_value
        + scale * maximum.root_endpoint_value
    )
    if minimum_current != maximum_current or minimum_current != current_trace.value:
        raise ArithmeticError("directional-face root value differs from exact BR")
    minimum_slope = minimum.root_endpoint_value - minimum.root_source_value
    maximum_slope = maximum.root_endpoint_value - maximum.root_source_value
    if minimum_slope > maximum_slope:
        raise ArithmeticError("directional-face root slope interval is reversed")

    source_profile = exact_policy_utilities(game, source)[target_player]
    endpoint_profile = exact_policy_utilities(game, endpoint)[target_player]
    profile = exact_policy_utilities(game, current)[target_player]
    profile_line = (
        (Fraction(1) - scale) * source_profile + scale * endpoint_profile
    )
    if profile != profile_line:
        raise ArithmeticError("directional-face profile utility is not affine")
    profile_slope = endpoint_profile - source_profile

    total_cardinality = 1
    total_cardinality_multiplications = 0
    for row in factors:
        total_cardinality *= len(row.maximizing_actions)
        total_cardinality_multiplications += 1
    (
        reachable_cardinality,
        reachable_cardinality_additions,
        reachable_cardinality_multiplications,
    ) = _reachable_support_cardinality(
        axis,
        maximizing_by_key,
        support_by_key,
    )
    tree_edges = sum(len(node.children) for node in nodes)
    target_edges = sum(
        len(node.children)
        for node in nodes
        if node.current_player == target_player
    )
    sequence_variables = len(axis.variables)
    expected_per_pass = len(nodes) + target_edges + sequence_variables
    for pass_result in (minimum, maximum):
        if (
            pass_result.continuation_node_evaluations != len(nodes)
            or pass_result.action_score_terms != target_edges
            or pass_result.action_choice_inspections != sequence_variables
        ):
            raise ArithmeticError("directional-face work departed from linear ledger")
    cardinality_ceiling = sequence_variables + 2 * len(axis.information_sets)
    cardinality_work = (
        total_cardinality_multiplications
        + reachable_cardinality_additions
        + reachable_cardinality_multiplications
    )
    if cardinality_work > cardinality_ceiling:
        raise ArithmeticError("directional-face cardinality work is not linear")
    total_work = 2 * expected_per_pass + cardinality_work
    ledger = ExactDirectionalFaceWorkLedger(
        tree_nodes=len(nodes),
        tree_edges=tree_edges,
        target_action_edges=target_edges,
        information_sets=len(axis.information_sets),
        sequence_variables=sequence_variables,
        lexicographic_passes=2,
        minimum_continuation_node_evaluations=(
            minimum.continuation_node_evaluations
        ),
        maximum_continuation_node_evaluations=(
            maximum.continuation_node_evaluations
        ),
        minimum_action_score_terms=minimum.action_score_terms,
        maximum_action_score_terms=maximum.action_score_terms,
        minimum_action_choice_inspections=minimum.action_choice_inspections,
        maximum_action_choice_inspections=maximum.action_choice_inspections,
        per_pass_linear_work_ceiling=expected_per_pass,
        total_cardinality_multiplications=total_cardinality_multiplications,
        reachable_cardinality_additions=reachable_cardinality_additions,
        reachable_cardinality_multiplications=(
            reachable_cardinality_multiplications
        ),
        cardinality_linear_work_ceiling=cardinality_ceiling,
        total_cardinality_bit_length=total_cardinality.bit_length(),
        reachable_cardinality_bit_length=reachable_cardinality.bit_length(),
        total_logical_work_units=total_work,
        materialized_response_tapes=0,
    )
    return ExactDirectionalFace(
        acting_player=acting_player,
        target_player=target_player,
        scale=scale,
        response_value=minimum_current,
        profile_utility=profile,
        deviation_gain=minimum_current - profile,
        minimum_response_slope=minimum_slope,
        maximum_response_slope=maximum_slope,
        profile_utility_slope=profile_slope,
        minimum_gain_slope=minimum_slope - profile_slope,
        maximum_gain_slope=maximum_slope - profile_slope,
        minimum_slope_tape=tuple(sorted(minimum.selected_actions.items())),
        maximum_slope_tape=tuple(sorted(maximum.selected_actions.items())),
        total_function_cardinality=total_cardinality,
        reachable_support_cardinality=reachable_cardinality,
        information_sets=tuple(factors),
        work=ledger,
    )


def compose_exact_directional_face_fan_section(
    game: ExtensiveFormGame,
    source_policy: ExactPolicy,
    endpoint_policy: ExactPolicy,
    *,
    acting_player: int,
    target_player: int,
    maximum_fan_tapes: int = 256,
    maximum_tree_nodes: int = 100_000,
) -> ExactDirectionalFaceFanSection:
    """Compose full-ray fan locations with exact active-face sensitivity."""

    fan = map_exact_selector_fan_section(
        game,
        source_policy,
        endpoint_policy,
        acting_player=acting_player,
        target_player=target_player,
        maximum_tapes=maximum_fan_tapes,
    )
    source = realization_interpolated_policy(
        game,
        source_policy,
        endpoint_policy,
        acting_player=acting_player,
        scale=Fraction(0),
    )
    endpoint = realization_interpolated_policy(
        game,
        source_policy,
        endpoint_policy,
        acting_player=acting_player,
        scale=Fraction(1),
    )
    source_profile = exact_policy_utilities(game, source)[target_player]
    endpoint_profile = exact_policy_utilities(game, endpoint)[target_player]
    profile_slope = endpoint_profile - source_profile
    cell_rows = []
    for cell in fan.cells:
        selected = dict(cell.response_tape)
        left = exact_fixed_response_trace(game, source, target_player, selected)
        right = exact_fixed_response_trace(game, endpoint, target_player, selected)
        cell_rows.append(
            ExactFanCellGainRow(
                response_tape=cell.response_tape,
                lower=cell.lower,
                upper=cell.upper,
                intercept=left.value - source_profile,
                slope=(right.value - left.value) - profile_slope,
            )
        )

    specs: list[tuple[Fraction, str, str, str]] = []
    specs.extend(
        (point.scale, "fan_boundary", point.total_state, point.reachable_state)
        for point in fan.points
    )
    specs.extend(
        (
            segment.witness,
            "open_segment",
            segment.total_state,
            segment.reachable_state,
        )
        for segment in fan.segments
    )
    samples = []
    for scale, kind, total_state, reachable_state in sorted(
        specs,
        key=lambda item: (item[0], item[1]),
    ):
        face = exact_directional_best_response_face(
            game,
            source_policy,
            endpoint_policy,
            acting_player=acting_player,
            target_player=target_player,
            scale=scale,
            maximum_tree_nodes=maximum_tree_nodes,
        )
        values = tuple(row.value(scale) for row in cell_rows)
        maximum_gain = max(values)
        active_rows = sum(value == maximum_gain for value in values)
        if maximum_gain != face.deviation_gain:
            raise ArithmeticError("directional face and fan envelope values differ")
        if (total_state == "tie_unresolved") != (
            face.total_function_cardinality > 1
        ):
            raise ArithmeticError("directional face and total fan tie states differ")
        if (reachable_state == "tie_unresolved") != (
            face.reachable_support_cardinality > 1
        ):
            raise ArithmeticError(
                "directional face and reachable fan tie states differ"
            )
        samples.append(
            ExactDirectionalFaceFanSample(
                scale=scale,
                sample_kind=kind,
                total_state=total_state,
                reachable_state=reachable_state,
                maximum_cell_gain=maximum_gain,
                active_cell_rows=active_rows,
                face=face,
            )
        )

    for segment in fan.segments:
        row = next(
            (
                item
                for item in cell_rows
                if item.response_tape == segment.response_tape
            ),
            None,
        )
        if row is None or row.lower > segment.lower or row.upper < segment.upper:
            raise ArithmeticError("directional face/fan seam dropped an open cell")
    crossings = tuple(
        left.upper
        for left, right in zip(fan.segments, fan.segments[1:])
        if left.response_tape != right.response_tape
    )
    point_samples = {
        sample.scale: sample
        for sample in samples
        if sample.sample_kind == "fan_boundary"
    }
    for scale in crossings:
        sample = point_samples[scale]
        if (
            sample.face.total_function_cardinality <= 1
            or sample.face.minimum_gain_slope
            >= sample.face.maximum_gain_slope
        ):
            raise ArithmeticError("directional face/fan seam lost a crossing")
    return ExactDirectionalFaceFanSection(
        fan=fan,
        cell_rows=tuple(cell_rows),
        samples=tuple(samples),
        crossing_scales=crossings,
    )


__all__ = [
    "ExactDirectionalFace",
    "ExactDirectionalFaceFanSample",
    "ExactDirectionalFaceFanSection",
    "ExactDirectionalFaceInformationSet",
    "ExactDirectionalFaceWorkLedger",
    "ExactFanCellGainRow",
    "compose_exact_directional_face_fan_section",
    "exact_directional_best_response_face",
]
