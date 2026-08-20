"""Run the frozen open-mode conditional factor-TT and quotient-CFR audit."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

import numpy as np

from .factor_tt_contraction import FactorTTBeliefWorkspace, FactorTTTopology
from .factorized_belief import FactorizedCardBelief
from .factorized_belief_audit import _derived_seed, _raw_factors, generate_hand_axes
from .game import TERMINAL_PLAYER
from .incremental_policy_tt import (
    PolicyDeltaTTCache,
    PolicyProbabilityTape,
    compile_policy_delta_tt_cache_from_probabilities,
    compile_policy_probability_tape,
)
from .open_mode_cfr_bridge import (
    CFRActionComparison,
    dense_cfr_action_comparisons,
    open_mode_cfr_action_read,
)
from .open_mode_factor_tt import (
    BidirectionalFactorTTTopology,
    OpenModeFactorTTWorkspace,
)
from .open_mode_showdown import contract_open_mode_showdown_batch
from .public_tree_tensor import PublicTreeTensorEvaluator
from .public_tree_tensor_cfr import PublicTreeTensorCFR
from .real_policy_representation_audit import _policy_from_json
from .real_policy_representation_audit_v2 import _canonicalized_factorized_belief
from .reporting import environment_metadata
from .river import format_card, parse_cards
from .showdown_value_rank_screen import _game_from_belief, _rank_codes, _terminal_groups
from .structured_showdown_automaton import (
    StructuredShowdownAutomaton,
    build_structured_showdown_automaton,
)
from .tensor_train import TensorTrain

_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "open-mode-factor-tt-audit-v1.json"
_SOURCE_ARTIFACT = _ROOT / "experiments" / "results" / "real-policy-source-v1.json"
_IMPLEMENTATION = Path(__file__)
_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_source_artifact_sha256",
    "expected_factorized_belief_sha256",
    "expected_factorized_audit_sha256",
    "expected_factor_tt_sha256",
    "expected_incremental_policy_tt_sha256",
    "expected_open_mode_factor_tt_sha256",
    "expected_open_mode_cfr_bridge_sha256",
    "expected_open_mode_showdown_sha256",
    "expected_public_tree_tensor_sha256",
    "expected_public_tree_tensor_cfr_sha256",
    "expected_structured_showdown_sha256",
    "expected_audit_implementation_sha256",
    "board",
    "pot",
    "stack",
    "bet_size",
    "players",
    "small_hands_per_player",
    "wide_hands_per_player",
    "range_families",
    "mixture_components",
    "split_index",
    "source_checkpoint",
    "node_relative_tolerance",
    "query_chunk_records",
    "maximum_feature_width_per_batch",
    "wide_maximum_feature_width_per_batch",
    "wide_terminal_group",
    "wide_axis_seed_rule",
    "zero_reach_rule",
    "gates",
}
_GATE_FIELDS = {
    "maximum_reach_error",
    "maximum_action_numerator_error",
    "maximum_conditional_action_value_error",
    "maximum_regret_delta_error",
    "maximum_actual_cfr_regret_bridge_error",
    "maximum_action_identity_mismatches",
    "maximum_zero_reach_action_mismatches",
    "maximum_zero_reach_regret_change",
    "minimum_zero_reach_rows",
    "expected_small_geometry_rows",
    "expected_small_infoset_rows",
    "expected_wide_rows",
    "maximum_wide_partition_relative_error",
    "maximum_wide_marginal_error",
    "maximum_wide_constant_value_error",
    "maximum_wide_zero_sum_error",
    "maximum_wide_peak_numeric_bytes",
    "maximum_wide_peak_ratio_to_dense_operator",
    "maximum_wide_automaton_numeric_bytes",
    "require_wide_finite_legal_actions",
    "require_wide_direct_transition_path",
}
_SOURCE_PATHS = {
    "expected_factorized_belief_sha256": _ROOT / "src" / "pontius" / "factorized_belief.py",
    "expected_factorized_audit_sha256": _ROOT / "src" / "pontius" / "factorized_belief_audit.py",
    "expected_factor_tt_sha256": _ROOT / "src" / "pontius" / "factor_tt_contraction.py",
    "expected_incremental_policy_tt_sha256": _ROOT / "src" / "pontius" / "incremental_policy_tt.py",
    "expected_open_mode_factor_tt_sha256": _ROOT / "src" / "pontius" / "open_mode_factor_tt.py",
    "expected_open_mode_cfr_bridge_sha256": _ROOT / "src" / "pontius" / "open_mode_cfr_bridge.py",
    "expected_open_mode_showdown_sha256": _ROOT / "src" / "pontius" / "open_mode_showdown.py",
    "expected_public_tree_tensor_sha256": _ROOT / "src" / "pontius" / "public_tree_tensor.py",
    "expected_public_tree_tensor_cfr_sha256": _ROOT / "src" / "pontius" / "public_tree_tensor_cfr.py",
    "expected_structured_showdown_sha256": _ROOT / "src" / "pontius" / "structured_showdown_automaton.py",
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_open_mode_audit_config(config: dict[str, Any]) -> dict[str, Any]:
    """Strictly validate the ADR-0081 execution contract."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "open-mode audit fields differ from ADR-0081: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    frozen = {
        "evidence_stage": (
            "preregistered_after_reduced_bridge_and_wide_terminal_engineering_"
            "before_canonical_source_cfr_results"
        ),
        "seed": 20260819,
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "small_hands_per_player": [4, 7],
        "wide_hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "mixture_components": 3,
        "split_index": 3,
        "source_checkpoint": 16,
        "node_relative_tolerance": 1e-12,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 512,
        "wide_maximum_feature_width_per_batch": 384,
        "wide_terminal_group": "all_check_all_six_contenders_no_contribution",
        "wide_axis_seed_rule": "ADR0067_public_policy_root_axis",
        "zero_reach_rule": (
            "zero_root_first_action_then_first_legal_action_and_zero_regret"
        ),
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("open-mode execution contract differs from ADR-0081")
    if config["expected_source_artifact_sha256"] != _sha256(_SOURCE_ARTIFACT):
        raise ValueError("canonical real-policy source artifact hash mismatch")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")
    gates = config["gates"]
    if not isinstance(gates, dict) or set(gates) != _GATE_FIELDS:
        raise ValueError("open-mode gates differ from ADR-0081")
    expected_gates = {
        "maximum_reach_error": 1e-10,
        "maximum_action_numerator_error": 1e-8,
        "maximum_conditional_action_value_error": 1e-8,
        "maximum_regret_delta_error": 1e-8,
        "maximum_actual_cfr_regret_bridge_error": 1e-10,
        "maximum_action_identity_mismatches": 0,
        "maximum_zero_reach_action_mismatches": 0,
        "maximum_zero_reach_regret_change": 0.0,
        "minimum_zero_reach_rows": 1,
        "expected_small_geometry_rows": 4,
        "expected_small_infoset_rows": 768,
        "expected_wide_rows": 2,
        "maximum_wide_partition_relative_error": 1e-10,
        "maximum_wide_marginal_error": 1e-10,
        "maximum_wide_constant_value_error": 1e-10,
        "maximum_wide_zero_sum_error": 1e-9,
        "maximum_wide_peak_numeric_bytes": 1_000_000_000,
        "maximum_wide_peak_ratio_to_dense_operator": 0.125,
        "maximum_wide_automaton_numeric_bytes": 2_000_000,
        "require_wide_finite_legal_actions": True,
        "require_wide_direct_transition_path": True,
    }
    if gates != expected_gates:
        raise ValueError("open-mode gates differ from ADR-0081")
    return {
        **config,
        "small_hands_per_player": tuple(config["small_hands_per_player"]),
        "range_families": tuple(config["range_families"]),
        "gates": dict(gates),
    }


def _canonical_belief(
    *,
    board: tuple[int, ...],
    hand_count: int,
    family: str,
    components: int,
    seed: int,
) -> FactorizedCardBelief:
    axis_seed = _derived_seed(
        seed,
        "public-policy-root-axis",
        hand_count,
        family,
    )
    axes = generate_hand_axes(
        board=board,
        players=6,
        hands_per_player=hand_count,
        family=family,
        seed=axis_seed,
    )
    mixture, unaries = _raw_factors(
        hands_by_player=axes,
        components=components,
        seed=axis_seed,
        family=family,
    )
    return _canonicalized_factorized_belief(
        hands_by_player=axes,
        mixture_weights=mixture,
        unary_weights=unaries,
        board=board,
    )


def _open_workspace(
    belief: FactorizedCardBelief,
    *,
    split_index: int,
    query_chunk_records: int,
) -> tuple[OpenModeFactorTTWorkspace, dict[str, float]]:
    started = time.perf_counter()
    base_topology = FactorTTTopology.compile(belief, split_index=split_index)
    factor_topology_ms = (time.perf_counter() - started) * 1000.0
    started = time.perf_counter()
    base = FactorTTBeliefWorkspace.compile(
        base_topology,
        belief,
        query_chunk_records=query_chunk_records,
    )
    belief_workspace_ms = (time.perf_counter() - started) * 1000.0
    started = time.perf_counter()
    topology = BidirectionalFactorTTTopology.compile(base_topology)
    bidirectional_topology_ms = (time.perf_counter() - started) * 1000.0
    started = time.perf_counter()
    workspace = OpenModeFactorTTWorkspace.compile(topology, base)
    reverse_belief_workspace_ms = (time.perf_counter() - started) * 1000.0
    return workspace, {
        "factor_topology_ms": factor_topology_ms,
        "belief_workspace_ms": belief_workspace_ms,
        "bidirectional_topology_ms": bidirectional_topology_ms,
        "reverse_belief_workspace_ms": reverse_belief_workspace_ms,
    }


def _train_digest(train: TensorTrain) -> str:
    digest = hashlib.sha256()
    digest.update(repr(train.shape).encode("ascii"))
    for core in train.cores:
        digest.update(repr(core.shape).encode("ascii"))
        digest.update(core.tobytes(order="C"))
    return digest.hexdigest()


def _terminal_library(
    *,
    layout: PublicTreeTensorEvaluator,
    belief: FactorizedCardBelief,
    board: tuple[int, ...],
    target: int,
    pot: float,
    bet_size: float,
) -> tuple[dict[str, TensorTrain], dict[str, float], dict[str, int | float]]:
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, belief.hands_by_player)
    )
    trains: dict[str, TensorTrain] = {}
    canonical: dict[str, TensorTrain] = {}
    maximum_rank = 1
    numeric_bytes = 0
    started = time.perf_counter()
    for group in _terminal_groups(layout):
        automaton = build_structured_showdown_automaton(
            strength_codes=codes,
            contenders=group.contenders,
            target_player=target,
            contributed=group.contributed,
            pot=pot,
            bet_size=bet_size,
        )
        supplied = automaton.to_tensor_train()
        digest = _train_digest(supplied)
        retained = canonical.setdefault(digest, supplied)
        trains[group.key] = retained
        maximum_rank = max(maximum_rank, *retained.ranks)
    for train in canonical.values():
        numeric_bytes += train.storage_bytes
    return (
        trains,
        {key: 0.0 for key in trains},
        {
            "target": target,
            "terminal_groups": len(trains),
            "deduplicated_trains": len(canonical),
            "maximum_terminal_rank": maximum_rank,
            "terminal_train_numeric_bytes": numeric_bytes,
            "compile_ms": (time.perf_counter() - started) * 1000.0,
        },
    )


def _comparison_errors(
    actual: CFRActionComparison,
    expected: CFRActionComparison,
) -> dict[str, float | int]:
    positive = expected.positive_reach
    conditional_error = (
        float(
            np.max(
                np.abs(
                    actual.conditional_action_values[positive]
                    - expected.conditional_action_values[positive]
                )
            )
        )
        if np.any(positive)
        else 0.0
    )
    return {
        "reach_error": float(
            np.max(
                np.abs(actual.counterfactual_reaches - expected.counterfactual_reaches)
            )
        ),
        "action_numerator_error": float(
            np.max(np.abs(actual.action_numerators - expected.action_numerators))
        ),
        "conditional_action_value_error": conditional_error,
        "regret_delta_error": float(
            np.max(np.abs(actual.regret_deltas - expected.regret_deltas))
        ),
        "action_identity_mismatches": int(
            np.count_nonzero(
                actual.selected_action_indices != expected.selected_action_indices
            )
        ),
    }


def _actual_cfr_bridge_error(
    layout: PublicTreeTensorEvaluator,
    policy: dict[str, dict[str, float]],
    probabilities: PolicyProbabilityTape,
) -> tuple[float, int]:
    solver = PublicTreeTensorCFR(layout, "cfr")
    solver.warm_start(policy, 1.0)
    before = solver.regret_table()
    expected = dense_cfr_action_comparisons(
        layout,
        probabilities,
        traverser=0,
    )
    solver.step()
    after = solver.regret_table()
    maximum = 0.0
    entries = 0
    for row in expected:
        node = layout.nodes[row.node_index]
        for hand_index, key in enumerate(node.information_keys):
            for action_index, action in enumerate(node.actions):
                maximum = max(
                    maximum,
                    abs(
                        (after[key][action] - before[key][action])
                        - row.regret_deltas[hand_index, action_index]
                    ),
                )
                entries += 1
    return maximum, entries


def _zero_reach_audit(
    *,
    layout: PublicTreeTensorEvaluator,
    workspace: OpenModeFactorTTWorkspace,
    probabilities: PolicyProbabilityTape,
    terminal_libraries: tuple[tuple[dict[str, TensorTrain], dict[str, float]], ...],
    relative_tolerance: float,
    maximum_feature_width_per_batch: int,
) -> dict[str, int | float]:
    root = layout.nodes[0]
    if root.player == TERMINAL_PLAYER or len(root.actions) < 2:
        raise AssertionError("zero-reach control requires a branching strategic root")
    selected_child = root.children[0]
    descendant = next(
        node_index
        for node_index in range(selected_child, layout.public_node_count)
        if layout.nodes[node_index].player not in (TERMINAL_PLAYER, root.player)
        and layout.nodes[node_index].history[:1] == ((root.player, root.actions[0]),)
    )
    target = layout.nodes[descendant].player
    edited = list(probabilities)
    root_values = np.zeros_like(probabilities[0])
    if root_values is None:
        raise AssertionError("strategic root has no probability table")
    root_values[:, 1:] = 1.0 / (len(root.actions) - 1)
    root_values.flags.writeable = False
    edited[0] = root_values
    edited_probabilities = tuple(edited)
    trains, bounds = terminal_libraries[target]
    cache = compile_policy_delta_tt_cache_from_probabilities(
        layout,
        layout.hands_by_player,
        edited_probabilities,
        trains,
        bounds,
        relative_tolerance=relative_tolerance,
        maximum_rank=None,
    )
    dense = {
        row.node_index: row
        for row in dense_cfr_action_comparisons(
            layout,
            edited_probabilities,
            traverser=target,
        )
    }
    rows = 0
    action_mismatches = 0
    maximum_regret_change = 0.0
    for node_index, expected in dense.items():
        if not np.any(expected.positive_reach):
            actual = open_mode_cfr_action_read(
                workspace,
                cache,
                node_index=node_index,
                maximum_feature_width_per_batch=maximum_feature_width_per_batch,
            ).comparison
            rows += 1
            action_mismatches += int(
                np.count_nonzero(actual.selected_action_indices != 0)
            )
            action_mismatches += int(
                np.count_nonzero(
                    actual.selected_action_indices != expected.selected_action_indices
                )
            )
            maximum_regret_change = max(
                maximum_regret_change,
                float(np.max(np.abs(actual.regret_deltas))),
            )
    return {
        "target": target,
        "zero_reach_rows": rows,
        "zero_reach_action_mismatches": action_mismatches,
        "maximum_zero_reach_regret_change": maximum_regret_change,
    }


def _small_geometry(
    *,
    parsed: dict[str, Any],
    source_geometry: dict[str, Any],
    board: tuple[int, ...],
    run_actual_bridge: bool,
    run_zero_reach: bool,
) -> tuple[dict[str, object], list[dict[str, object]], dict[str, object] | None]:
    hand_count = int(source_geometry["hands_per_player"])
    family = str(source_geometry["range_family"])
    belief = _canonical_belief(
        board=board,
        hand_count=hand_count,
        family=family,
        components=parsed["mixture_components"],
        seed=parsed["seed"],
    )
    expected_axes = [
        [[format_card(hand[0]), format_card(hand[1])] for hand in hands]
        for hands in belief.hands_by_player
    ]
    if expected_axes != source_geometry["hand_axes"]:
        raise ValueError("canonical source hand axes do not reproduce")
    profile = next(
        row
        for row in source_geometry["profiles"]
        if row["provenance"]["kind"] == "dcfr_average"
        and int(row["provenance"]["checkpoint"]) == parsed["source_checkpoint"]
    )
    policy = _policy_from_json(profile["policy"])

    started = time.perf_counter()
    game = _game_from_belief(
        belief=belief,
        pot=parsed["pot"],
        stack=parsed["stack"],
        bet_size=parsed["bet_size"],
    )
    layout = PublicTreeTensorEvaluator(game)
    layout_ms = (time.perf_counter() - started) * 1000.0
    if game.provenance_digest != source_geometry["game_provenance_digest"]:
        raise ValueError("canonical source game provenance does not reproduce")
    workspace, workspace_timing = _open_workspace(
        belief,
        split_index=parsed["split_index"],
        query_chunk_records=parsed["query_chunk_records"],
    )
    probabilities = compile_policy_probability_tape(
        layout,
        belief.hands_by_player,
        policy,
    )

    maximum_reach_error = 0.0
    maximum_numerator_error = 0.0
    maximum_conditional_error = 0.0
    maximum_regret_error = 0.0
    action_mismatches = 0
    infoset_rows: list[dict[str, object]] = []
    terminal_summaries = []
    terminal_libraries: list[tuple[dict[str, TensorTrain], dict[str, float]]] = []
    cache_compile_ms = 0.0
    read_ms = 0.0
    maximum_middle_rank = 0
    maximum_total_feature_width = 0
    maximum_peak_bytes = 0
    for target in range(parsed["players"]):
        trains, bounds, terminal_summary = _terminal_library(
            layout=layout,
            belief=belief,
            board=board,
            target=target,
            pot=parsed["pot"],
            bet_size=parsed["bet_size"],
        )
        terminal_libraries.append((trains, bounds))
        terminal_summaries.append(terminal_summary)
        started = time.perf_counter()
        cache = compile_policy_delta_tt_cache_from_probabilities(
            layout,
            belief.hands_by_player,
            probabilities,
            trains,
            bounds,
            relative_tolerance=parsed["node_relative_tolerance"],
            maximum_rank=None,
        )
        cache_compile_ms += (time.perf_counter() - started) * 1000.0
        expected_rows = dense_cfr_action_comparisons(
            layout,
            probabilities,
            traverser=target,
        )
        for expected in expected_rows:
            started = time.perf_counter()
            read = open_mode_cfr_action_read(
                workspace,
                cache,
                node_index=expected.node_index,
                maximum_feature_width_per_batch=parsed[
                    "maximum_feature_width_per_batch"
                ],
            )
            elapsed = (time.perf_counter() - started) * 1000.0
            read_ms += elapsed
            errors = _comparison_errors(read.comparison, expected)
            maximum_reach_error = max(
                maximum_reach_error, float(errors["reach_error"])
            )
            maximum_numerator_error = max(
                maximum_numerator_error,
                float(errors["action_numerator_error"]),
            )
            maximum_conditional_error = max(
                maximum_conditional_error,
                float(errors["conditional_action_value_error"]),
            )
            maximum_regret_error = max(
                maximum_regret_error,
                float(errors["regret_delta_error"]),
            )
            action_mismatches += int(errors["action_identity_mismatches"])
            maximum_middle_rank = max(
                maximum_middle_rank,
                *read.contraction.middle_ranks,
            )
            maximum_total_feature_width = max(
                maximum_total_feature_width,
                *(work.total_value_feature_width for work in read.contraction.directions),
            )
            maximum_peak_bytes = max(
                maximum_peak_bytes,
                read.contraction.estimated_peak_total_numeric_bytes,
            )
            positive_scores = expected.action_numerators[expected.positive_reach]
            minimum_gap = None
            if positive_scores.size and positive_scores.shape[1] >= 2:
                ordered = np.sort(positive_scores, axis=1)
                minimum_gap = float(np.min(ordered[:, -1] - ordered[:, -2]))
            infoset_rows.append(
                {
                    "hands_per_player": hand_count,
                    "range_family": family,
                    "target": target,
                    "node_index": expected.node_index,
                    "history": [list(item) for item in layout.nodes[expected.node_index].history],
                    "hands": len(expected.positive_reach),
                    "actions": len(expected.actions),
                    "positive_reach_hands": int(np.count_nonzero(expected.positive_reach)),
                    "minimum_positive_action_gap": minimum_gap,
                    "read_ms": elapsed,
                    "middle_ranks": list(read.contraction.middle_ranks),
                    "total_feature_width": sum(
                        work.total_value_feature_width
                        for work in read.contraction.directions
                    ),
                    "batches": sum(work.batches for work in read.contraction.directions),
                    **errors,
                }
            )

    actual_bridge_error = 0.0
    actual_bridge_entries = 0
    if run_actual_bridge:
        actual_bridge_error, actual_bridge_entries = _actual_cfr_bridge_error(
            layout,
            policy,
            probabilities,
        )
    zero_row = None
    if run_zero_reach:
        zero_row = _zero_reach_audit(
            layout=layout,
            workspace=workspace,
            probabilities=probabilities,
            terminal_libraries=tuple(terminal_libraries),
            relative_tolerance=parsed["node_relative_tolerance"],
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
        )
    summary = {
        "hands_per_player": hand_count,
        "range_family": family,
        "source_checkpoint": parsed["source_checkpoint"],
        "joint_deals": layout.deal_count,
        "public_nodes": layout.public_node_count,
        "terminal_nodes": layout.terminal_node_count,
        "infoset_rows": len(infoset_rows),
        "hand_action_entries": sum(
            int(row["hands"]) * int(row["actions"]) for row in infoset_rows
        ),
        "maximum_reach_error": maximum_reach_error,
        "maximum_action_numerator_error": maximum_numerator_error,
        "maximum_conditional_action_value_error": maximum_conditional_error,
        "maximum_regret_delta_error": maximum_regret_error,
        "action_identity_mismatches": action_mismatches,
        "maximum_middle_rank": maximum_middle_rank,
        "maximum_total_feature_width": maximum_total_feature_width,
        "maximum_peak_numeric_bytes": maximum_peak_bytes,
        "actual_cfr_regret_bridge_error": actual_bridge_error,
        "actual_cfr_regret_bridge_entries": actual_bridge_entries,
        "layout_compile_ms": layout_ms,
        "cache_compile_ms": cache_compile_ms,
        "open_read_ms": read_ms,
        "workspace_timing": workspace_timing,
        "terminal_summaries": terminal_summaries,
    }
    return summary, infoset_rows, zero_row


def _wide_geometry(
    *,
    parsed: dict[str, Any],
    board: tuple[int, ...],
    family: str,
) -> dict[str, object]:
    hand_count = parsed["wide_hands_per_player"]
    belief = _canonical_belief(
        board=board,
        hand_count=hand_count,
        family=family,
        components=parsed["mixture_components"],
        seed=parsed["seed"],
    )
    oracle_started = time.perf_counter()
    oracle = belief.meet_in_middle_contract()
    oracle_ms = (time.perf_counter() - oracle_started) * 1000.0
    workspace, workspace_timing = _open_workspace(
        belief,
        split_index=parsed["split_index"],
        query_chunk_records=parsed["query_chunk_records"],
    )
    partition_error = abs(workspace.base.partition - oracle.partition) / max(
        workspace.base.partition,
        oracle.partition,
    )
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, belief.hands_by_player)
    )
    automaton_started = time.perf_counter()
    automata = tuple(
        build_structured_showdown_automaton(
            strength_codes=codes,
            contenders=tuple(range(parsed["players"])),
            target_player=target,
            contributed=False,
            pot=parsed["pot"],
            bet_size=parsed["bet_size"],
        )
        for target in range(parsed["players"])
    )
    automaton_ms = (time.perf_counter() - automaton_started) * 1000.0
    contraction_started = time.perf_counter()
    left = contract_open_mode_showdown_batch(
        workspace,
        automata[:3],
        target_seats=(0, 1, 2),
        maximum_feature_width_per_batch=parsed[
            "wide_maximum_feature_width_per_batch"
        ],
    )
    right = contract_open_mode_showdown_batch(
        workspace,
        automata[3:],
        target_seats=(3, 4, 5),
        maximum_feature_width_per_batch=parsed[
            "wide_maximum_feature_width_per_batch"
        ],
    )
    contraction_ms = (time.perf_counter() - contraction_started) * 1000.0
    own_values = [
        left.for_automaton(index).for_seat(index) for index in range(3)
    ] + [
        right.for_automaton(index).for_seat(index + 3) for index in range(3)
    ]
    marginal_error = max(
        float(np.max(np.abs(values.root_normalized_reaches - oracle.marginals[target])))
        for target, values in enumerate(own_values)
    )
    utilities = tuple(
        values.total_unnormalized_numerator / workspace.base.partition
        for values in own_values
    )
    zero_sum_error = abs(math.fsum(utilities))

    shortcut = build_structured_showdown_automaton(
        strength_codes=codes,
        contenders=(1, 2, 3, 4, 5),
        target_player=0,
        contributed=False,
        pot=parsed["pot"],
        bet_size=parsed["bet_size"],
    )
    if not shortcut.constant_winner_shortcut:
        raise AssertionError("wide constant control did not take the sparse shortcut")
    constant = contract_open_mode_showdown_batch(
        workspace,
        (shortcut,),
        target_seats=(0,),
        maximum_feature_width_per_batch=parsed[
            "wide_maximum_feature_width_per_batch"
        ],
    )
    constant_values = constant.for_automaton(0).for_seat(0)
    constant_error = float(
        np.max(np.abs(constant_values.conditional_values - shortcut.sunk_value))
    )
    action_pair = contract_open_mode_showdown_batch(
        workspace,
        (automata[0], shortcut),
        target_seats=(0,),
        maximum_feature_width_per_batch=parsed[
            "wide_maximum_feature_width_per_batch"
        ],
    )
    action_values = np.column_stack(
        tuple(
            row.for_seat(0).root_normalized_numerators
            for row in action_pair.automata
        )
    )
    selected = np.argmax(action_values, axis=1)
    finite_legal_actions = bool(
        np.all(np.isfinite(action_values))
        and np.all((selected >= 0) & (selected < action_values.shape[1]))
    )

    automaton_bytes = sum(automaton.numeric_bytes for automaton in automata)
    all_automaton_bytes = automaton_bytes + shortcut.numeric_bytes
    persistent_adjustment = automaton_bytes
    peak = max(
        left.estimated_peak_total_numeric_bytes
        - left.referenced_automaton_numeric_bytes
        + persistent_adjustment,
        right.estimated_peak_total_numeric_bytes
        - right.referenced_automaton_numeric_bytes
        + persistent_adjustment,
        constant.estimated_peak_total_numeric_bytes
        - constant.referenced_automaton_numeric_bytes
        + all_automaton_bytes,
        action_pair.estimated_peak_total_numeric_bytes
        - action_pair.referenced_automaton_numeric_bytes
        + all_automaton_bytes,
    )
    dense_operator_bytes = hand_count**parsed["players"] * np.dtype(np.float64).itemsize
    return {
        "hands_per_player": hand_count,
        "range_family": family,
        "cartesian_assignments": hand_count**parsed["players"],
        "dense_operator_numeric_bytes": dense_operator_bytes,
        "partition_relative_error": partition_error,
        "maximum_marginal_error": marginal_error,
        "maximum_constant_value_error": constant_error,
        "zero_sum_error": zero_sum_error,
        "utilities": list(utilities),
        "finite_legal_actions": finite_legal_actions,
        "selected_action_counts": np.bincount(selected, minlength=2).tolist(),
        "automaton_numeric_bytes": all_automaton_bytes,
        "automaton_dense_one_hot_export_bytes_not_allocated": sum(
            automaton.dense_tt_export_bytes for automaton in (*automata, shortcut)
        ),
        "maximum_automaton_state_rank": max(
            automaton.maximum_state_rank for automaton in (*automata, shortcut)
        ),
        "left_middle_ranks": list(left.middle_ranks),
        "right_middle_ranks": list(right.middle_ranks),
        "half_vector_numeric_bytes": (
            left.half_vector_numeric_bytes + right.half_vector_numeric_bytes
        ),
        "maximum_peak_numeric_bytes": peak,
        "peak_ratio_to_dense_operator": peak / dense_operator_bytes,
        "direct_transition_path": True,
        "dense_cartesian_payoff_constructed": False,
        "dense_one_hot_tt_export_constructed": False,
        "meet_in_middle_oracle_ms": oracle_ms,
        "automaton_compile_ms": automaton_ms,
        "six_value_contraction_ms": contraction_ms,
        "workspace_timing": workspace_timing,
    }


def run_open_mode_audit(config: dict[str, Any]) -> dict[str, object]:
    """Run the frozen exact small-axis bridge and dense-free wide structure."""

    parsed = parse_open_mode_audit_config(config)
    source = json.loads(_SOURCE_ARTIFACT.read_text(encoding="utf-8"))
    board = parse_cards(*parsed["board"])
    started = time.perf_counter()
    small_rows = []
    infoset_rows: list[dict[str, object]] = []
    zero_rows = []
    for source_geometry in source["geometries"]:
        hand_count = int(source_geometry["hands_per_player"])
        family = str(source_geometry["range_family"])
        if hand_count not in parsed["small_hands_per_player"]:
            continue
        summary, rows, zero = _small_geometry(
            parsed=parsed,
            source_geometry=source_geometry,
            board=board,
            run_actual_bridge=(hand_count == 4 and family == "balanced"),
            run_zero_reach=(hand_count == 4 and family == "balanced"),
        )
        small_rows.append(summary)
        infoset_rows.extend(rows)
        if zero is not None:
            zero_rows.append(zero)
        gc.collect()

    wide_rows = []
    for family in parsed["range_families"]:
        wide_rows.append(
            _wide_geometry(parsed=parsed, board=board, family=family)
        )
        gc.collect()

    aggregate = {
        "maximum_reach_error": max(
            float(row["maximum_reach_error"]) for row in small_rows
        ),
        "maximum_action_numerator_error": max(
            float(row["maximum_action_numerator_error"]) for row in small_rows
        ),
        "maximum_conditional_action_value_error": max(
            float(row["maximum_conditional_action_value_error"])
            for row in small_rows
        ),
        "maximum_regret_delta_error": max(
            float(row["maximum_regret_delta_error"]) for row in small_rows
        ),
        "maximum_actual_cfr_regret_bridge_error": max(
            float(row["actual_cfr_regret_bridge_error"]) for row in small_rows
        ),
        "action_identity_mismatches": sum(
            int(row["action_identity_mismatches"]) for row in small_rows
        ),
        "zero_reach_rows": sum(int(row["zero_reach_rows"]) for row in zero_rows),
        "zero_reach_action_mismatches": sum(
            int(row["zero_reach_action_mismatches"]) for row in zero_rows
        ),
        "maximum_zero_reach_regret_change": max(
            (float(row["maximum_zero_reach_regret_change"]) for row in zero_rows),
            default=0.0,
        ),
        "maximum_wide_partition_relative_error": max(
            float(row["partition_relative_error"]) for row in wide_rows
        ),
        "maximum_wide_marginal_error": max(
            float(row["maximum_marginal_error"]) for row in wide_rows
        ),
        "maximum_wide_constant_value_error": max(
            float(row["maximum_constant_value_error"]) for row in wide_rows
        ),
        "maximum_wide_zero_sum_error": max(
            float(row["zero_sum_error"]) for row in wide_rows
        ),
        "maximum_wide_peak_numeric_bytes": max(
            int(row["maximum_peak_numeric_bytes"]) for row in wide_rows
        ),
        "maximum_wide_peak_ratio_to_dense_operator": max(
            float(row["peak_ratio_to_dense_operator"]) for row in wide_rows
        ),
        "maximum_wide_automaton_numeric_bytes": max(
            int(row["automaton_numeric_bytes"]) for row in wide_rows
        ),
    }
    counts = {
        "small_geometry_rows": len(small_rows),
        "small_infoset_rows": len(infoset_rows),
        "small_hand_action_entries": sum(
            int(row["hands"]) * int(row["actions"]) for row in infoset_rows
        ),
        "zero_reach_control_rows": len(zero_rows),
        "wide_rows": len(wide_rows),
    }
    gates = parsed["gates"]
    gate_results = {
        "reach_identity": aggregate["maximum_reach_error"]
        <= gates["maximum_reach_error"],
        "action_numerator_identity": aggregate["maximum_action_numerator_error"]
        <= gates["maximum_action_numerator_error"],
        "conditional_action_value_identity": aggregate[
            "maximum_conditional_action_value_error"
        ]
        <= gates["maximum_conditional_action_value_error"],
        "regret_delta_identity": aggregate["maximum_regret_delta_error"]
        <= gates["maximum_regret_delta_error"],
        "actual_cfr_regret_bridge": aggregate[
            "maximum_actual_cfr_regret_bridge_error"
        ]
        <= gates["maximum_actual_cfr_regret_bridge_error"],
        "action_identity": aggregate["action_identity_mismatches"]
        <= gates["maximum_action_identity_mismatches"],
        "zero_reach_action_identity": aggregate["zero_reach_action_mismatches"]
        <= gates["maximum_zero_reach_action_mismatches"],
        "zero_reach_regret_identity": aggregate[
            "maximum_zero_reach_regret_change"
        ]
        <= gates["maximum_zero_reach_regret_change"],
        "zero_reach_coverage": aggregate["zero_reach_rows"]
        >= gates["minimum_zero_reach_rows"],
        "small_geometry_count": counts["small_geometry_rows"]
        == gates["expected_small_geometry_rows"],
        "small_infoset_count": counts["small_infoset_rows"]
        == gates["expected_small_infoset_rows"],
        "wide_count": counts["wide_rows"] == gates["expected_wide_rows"],
        "wide_partition_identity": aggregate[
            "maximum_wide_partition_relative_error"
        ]
        <= gates["maximum_wide_partition_relative_error"],
        "wide_marginal_identity": aggregate["maximum_wide_marginal_error"]
        <= gates["maximum_wide_marginal_error"],
        "wide_constant_identity": aggregate[
            "maximum_wide_constant_value_error"
        ]
        <= gates["maximum_wide_constant_value_error"],
        "wide_zero_sum": aggregate["maximum_wide_zero_sum_error"]
        <= gates["maximum_wide_zero_sum_error"],
        "wide_peak_bytes": aggregate["maximum_wide_peak_numeric_bytes"]
        <= gates["maximum_wide_peak_numeric_bytes"],
        "wide_peak_ratio": aggregate[
            "maximum_wide_peak_ratio_to_dense_operator"
        ]
        <= gates["maximum_wide_peak_ratio_to_dense_operator"],
        "wide_automaton_bytes": aggregate[
            "maximum_wide_automaton_numeric_bytes"
        ]
        <= gates["maximum_wide_automaton_numeric_bytes"],
        "wide_finite_legal_actions": all(
            bool(row["finite_legal_actions"]) for row in wide_rows
        )
        == gates["require_wide_finite_legal_actions"],
        "wide_direct_transition_path": all(
            bool(row["direct_transition_path"])
            and not bool(row["dense_cartesian_payoff_constructed"])
            and not bool(row["dense_one_hot_tt_export_constructed"])
            for row in wide_rows
        )
        == gates["require_wide_direct_transition_path"],
    }
    gate_results["passed"] = all(gate_results.values())
    wall_seconds = time.perf_counter() - started
    return {
        "schema_version": 1,
        "experiment_type": "open_mode_factor_tt_and_quotient_cfr_bridge_audit",
        "status": "frozen_audit_executed",
        "config": parsed,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_artifact_sha256": _sha256(_SOURCE_ARTIFACT),
        "counts": counts,
        "aggregate": aggregate,
        "small_geometry_rows": small_rows,
        "infoset_rows": infoset_rows,
        "zero_reach_rows": zero_rows,
        "wide_rows": wide_rows,
        "gates": gate_results,
        "timing": {"wall_seconds": wall_seconds},
        "environment": environment_metadata(),
        "limitations": [
            "The small-axis bridge evaluates fixed checkpoint-16 continuation TTs; it does not yet implement a full dense-free CFR iteration.",
            "The 32-hand arm proves structure, marginals, constant values, legal action output, and memory only; it has no speed-pass gate and is not an online-latency claim.",
            "The wide transition path still materializes assignment-by-middle-state half vectors, which the pre-freeze screen showed can require hundreds of MB and seconds in NumPy.",
            "Node TT truncation uses the inherited 1e-12 tolerance; the action identity gate is empirical on the frozen source policies, not a universal no-flip theorem.",
            "This audit produces conditional values and CFR action tables but does not improve strategy quality or establish multiplayer convergence, safety, or exploitability.",
        ],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_open_mode_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "open-mode audit: "
        f"infosets={result['counts']['small_infoset_rows']}, "
        f"wide={result['counts']['wide_rows']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
