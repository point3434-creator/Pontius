"""Run the frozen leaf-adjoint dense-free CFR and GPU audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from statistics import median
import time
from typing import Any

import numpy as np

from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .game import TERMINAL_PLAYER
from .incremental_policy_tt import compile_policy_probability_tape
from .leaf_adjoint_cfr import (
    LeafAdjointPublicTreeCFR,
    build_leaf_adjoint_terminal_automata,
    leaf_adjoint_cfr_traverser,
)
from .open_mode_audit import (
    _canonical_belief,
    _open_workspace,
    _policy_from_json,
    _terminal_library,
)
from .open_mode_cfr_bridge import dense_cfr_action_comparisons
from .public_policy_tt import _information_key, representative_public_tree
from .public_tree_tensor import PublicTreeTensorEvaluator
from .public_tree_tensor_cfr import PublicTreeTensorCFR
from .real_policy import mean_policy_total_variation, policy_digest, policy_statistics
from .reporting import environment_metadata
from .river import format_card, parse_cards
from .showdown_value_rank_screen import _game_from_belief, _rank_codes
from .sparse_incidence_open_mode import SparseBidirectionalIncidence
from .sparse_open_mode_cfr import SparseOpenModePublicTreeCFR

_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "leaf-adjoint-cfr-gpu-audit-v1.json"
_SOURCE = _ROOT / "experiments" / "results" / "real-policy-source-v1.json"
_IMPLEMENTATION = Path(__file__)
_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "axis_seed",
    "expected_source_artifact_sha256",
    "expected_requirements_sha256",
    "expected_axis_public_cfr_sha256",
    "expected_cupy_sparse_incidence_sha256",
    "expected_heterogeneous_leaf_sha256",
    "expected_leaf_adjoint_cfr_sha256",
    "expected_sparse_incidence_sha256",
    "expected_sparse_open_mode_cfr_sha256",
    "expected_sparse_open_mode_factor_tt_sha256",
    "expected_structured_showdown_sha256",
    "expected_unrounded_policy_tt_sha256",
    "expected_audit_implementation_sha256",
    "board",
    "pot",
    "stack",
    "bet_size",
    "players",
    "small_hands_per_player",
    "wide_hands_per_player",
    "range_families",
    "validation_speed_family",
    "mixture_components",
    "split_index",
    "query_chunk_records",
    "source_checkpoint",
    "solver_variant",
    "warm_regret_mass",
    "small_iterations",
    "wide_iterations",
    "maximum_feature_width_per_batch",
    "cpu_crosscheck_traverser",
    "required_numpy_version",
    "required_scipy_version",
    "required_cupy_version",
    "required_cuda_runtime_version",
    "minimum_cuda_driver_version",
    "required_compute_capability",
    "cuda_dll_environment_variable",
    "gates",
}
_GATE_FIELDS = {
    "expected_small_rows",
    "expected_wide_rows",
    "maximum_small_regret_error",
    "maximum_small_strategy_sum_error",
    "maximum_small_current_policy_error",
    "maximum_small_average_policy_error",
    "maximum_small_rounded_control_regret_error",
    "minimum_small_rounded_to_leaf_speedup",
    "minimum_zero_reach_rows",
    "maximum_zero_reach_regret_error",
    "maximum_zero_reach_regret_magnitude",
    "maximum_wide_reach_error",
    "maximum_wide_numerator_error",
    "maximum_wide_regret_error",
    "maximum_wide_conditional_error",
    "maximum_wide_child_reach_disagreement",
    "minimum_validation_wide_gpu_speedup",
    "minimum_all_wide_gpu_speedup",
    "maximum_wide_step_ms",
    "maximum_wide_host_peak_numeric_bytes",
    "maximum_wide_gpu_pool_bytes",
    "minimum_wide_current_policy_tv_after_first_step",
    "minimum_wide_average_policy_tv_after_second_step",
    "expected_wide_information_sets",
    "expected_wide_hand_action_entries",
    "require_finite_normalized_wide_policies",
}
_SOURCE_PATHS = {
    "expected_source_artifact_sha256": _SOURCE,
    "expected_requirements_sha256": (
        _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
    ),
    "expected_axis_public_cfr_sha256": _ROOT / "src" / "pontius" / "axis_public_cfr.py",
    "expected_cupy_sparse_incidence_sha256": (
        _ROOT / "src" / "pontius" / "cupy_sparse_incidence.py"
    ),
    "expected_heterogeneous_leaf_sha256": (
        _ROOT / "src" / "pontius" / "heterogeneous_leaf_contraction.py"
    ),
    "expected_leaf_adjoint_cfr_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_cfr.py"
    ),
    "expected_sparse_incidence_sha256": (
        _ROOT / "src" / "pontius" / "sparse_incidence_open_mode.py"
    ),
    "expected_sparse_open_mode_cfr_sha256": (
        _ROOT / "src" / "pontius" / "sparse_open_mode_cfr.py"
    ),
    "expected_sparse_open_mode_factor_tt_sha256": (
        _ROOT / "src" / "pontius" / "sparse_open_mode_factor_tt.py"
    ),
    "expected_structured_showdown_sha256": (
        _ROOT / "src" / "pontius" / "structured_showdown_automaton.py"
    ),
    "expected_unrounded_policy_tt_sha256": (
        _ROOT / "src" / "pontius" / "unrounded_policy_tt.py"
    ),
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_leaf_adjoint_cfr_audit_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "leaf-adjoint audit fields differ from ADR-0085: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    frozen = {
        "evidence_stage": (
            "preregistered_after_balanced_h32_target_development_before_"
            "blocker_h32_leaf_or_gpu_results"
        ),
        "seed": 20260820,
        "axis_seed": 20260819,
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "small_hands_per_player": [4, 7],
        "wide_hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "validation_speed_family": "blocker_heavy",
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "source_checkpoint": 16,
        "solver_variant": "dcfr",
        "warm_regret_mass": 1.0,
        "small_iterations": 2,
        "wide_iterations": 2,
        "maximum_feature_width_per_batch": 384,
        "cpu_crosscheck_traverser": 0,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("leaf-adjoint execution contract differs from ADR-0085")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")
    gates = config["gates"]
    expected_gates = {
        "expected_small_rows": 4,
        "expected_wide_rows": 2,
        "maximum_small_regret_error": 1e-10,
        "maximum_small_strategy_sum_error": 1e-10,
        "maximum_small_current_policy_error": 1e-10,
        "maximum_small_average_policy_error": 1e-10,
        "maximum_small_rounded_control_regret_error": 1e-10,
        "minimum_small_rounded_to_leaf_speedup": 5.0,
        "minimum_zero_reach_rows": 1,
        "maximum_zero_reach_regret_error": 1e-10,
        "maximum_zero_reach_regret_magnitude": 0.0,
        "maximum_wide_reach_error": 1e-10,
        "maximum_wide_numerator_error": 1e-9,
        "maximum_wide_regret_error": 1e-9,
        "maximum_wide_conditional_error": 1e-8,
        "maximum_wide_child_reach_disagreement": 1e-9,
        "minimum_validation_wide_gpu_speedup": 3.0,
        "minimum_all_wide_gpu_speedup": 3.0,
        "maximum_wide_step_ms": 60_000.0,
        "maximum_wide_host_peak_numeric_bytes": 3_000_000_000,
        "maximum_wide_gpu_pool_bytes": 4_000_000_000,
        "minimum_wide_current_policy_tv_after_first_step": 1e-8,
        "minimum_wide_average_policy_tv_after_second_step": 1e-8,
        "expected_wide_information_sets": 6_144,
        "expected_wide_hand_action_entries": 12_288,
        "require_finite_normalized_wide_policies": True,
    }
    if not isinstance(gates, dict) or set(gates) != _GATE_FIELDS or gates != expected_gates:
        raise ValueError("leaf-adjoint gates differ from ADR-0085")
    return {
        **config,
        "small_hands_per_player": tuple(config["small_hands_per_player"]),
        "range_families": tuple(config["range_families"]),
        "gates": dict(gates),
    }


def _source_profile(
    source: dict[str, Any],
    *,
    hand_count: int,
    family: str,
    checkpoint: int,
) -> tuple[dict[str, Any], dict[str, dict[str, float]]]:
    geometry = next(
        row
        for row in source["geometries"]
        if int(row["hands_per_player"]) == hand_count
        and row["range_family"] == family
    )
    profile = next(
        row
        for row in geometry["profiles"]
        if row["provenance"]["kind"] == "dcfr_average"
        and int(row["provenance"]["checkpoint"]) == checkpoint
    )
    return geometry, _policy_from_json(profile["policy"])


def _topology_signature(layout: PublicTreeTensorEvaluator) -> tuple[object, ...]:
    return tuple(
        (node.player, node.actions, node.children, node.terminal_slot, node.history)
        for node in layout.nodes
    )


def _table_error(
    first: dict[str, dict[str, float]],
    second: dict[str, dict[str, float]],
) -> float:
    if first.keys() != second.keys():
        raise AssertionError("CFR table schemas differ")
    return max(
        abs(first[key][action] - second[key][action])
        for key in first
        for action in first[key]
    )


def _small_case(
    *,
    parsed: dict[str, Any],
    source: dict[str, Any],
    board: tuple[int, ...],
    hand_count: int,
    family: str,
    run_rounded_control: bool,
) -> tuple[dict[str, object], dict[str, object] | None]:
    source_geometry, policy = _source_profile(
        source,
        hand_count=hand_count,
        family=family,
        checkpoint=parsed["source_checkpoint"],
    )
    belief = _canonical_belief(
        board=board,
        hand_count=hand_count,
        family=family,
        components=parsed["mixture_components"],
        seed=parsed["axis_seed"],
    )
    axes = [
        [[format_card(hand[0]), format_card(hand[1])] for hand in hands]
        for hands in belief.hands_by_player
    ]
    if axes != source_geometry["hand_axes"]:
        raise ValueError("small leaf-adjoint axes differ from source artifact")
    game = _game_from_belief(
        belief=belief,
        pot=parsed["pot"],
        stack=parsed["stack"],
        bet_size=parsed["bet_size"],
    )
    dense_layout = PublicTreeTensorEvaluator(game)
    topology = representative_public_tree(
        belief,
        pot=parsed["pot"],
        stack=parsed["stack"],
        bet_size=parsed["bet_size"],
    )
    if _topology_signature(topology) != _topology_signature(dense_layout):
        raise AssertionError("representative public topology differs from dense layout")
    workspace, workspace_timing = _open_workspace(
        belief,
        split_index=parsed["split_index"],
        query_chunk_records=parsed["query_chunk_records"],
    )
    sparse = SparseBidirectionalIncidence.compile(workspace)
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, belief.hands_by_player)
    )
    automata = build_leaf_adjoint_terminal_automata(
        topology,
        codes,
        pot=parsed["pot"],
        bet_size=parsed["bet_size"],
    )
    dense = PublicTreeTensorCFR(dense_layout, parsed["solver_variant"])
    leaf = LeafAdjointPublicTreeCFR(
        topology,
        workspace,
        sparse,
        automata,
        parsed["solver_variant"],
        maximum_feature_width_per_batch=parsed[
            "maximum_feature_width_per_batch"
        ],
        hands_by_player=belief.hands_by_player,
    )
    if set(policy) != set(leaf.information_schema()):
        raise ValueError("real source policy differs from external-axis schema")
    dense.warm_start(policy, parsed["warm_regret_mass"])
    leaf.warm_start(policy, parsed["warm_regret_mass"])
    iteration_rows = []
    maximum_regret = 0.0
    maximum_sum = 0.0
    maximum_current = 0.0
    maximum_average = 0.0
    first_dense_regrets = None
    for iteration in range(1, parsed["small_iterations"] + 1):
        started = time.perf_counter()
        dense.step()
        dense_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        leaf.step()
        leaf_ms = (time.perf_counter() - started) * 1000.0
        regret_error = _table_error(leaf.regret_table(), dense.regret_table())
        sum_error = _table_error(
            leaf.strategy_sum_table(), dense.strategy_sum_table()
        )
        current_error = _table_error(
            leaf.current_strategy(), dense.current_strategy()
        )
        average_error = _table_error(
            leaf.average_strategy(), dense.average_strategy()
        )
        if iteration == 1:
            first_dense_regrets = dense.regret_table()
        maximum_regret = max(maximum_regret, regret_error)
        maximum_sum = max(maximum_sum, sum_error)
        maximum_current = max(maximum_current, current_error)
        maximum_average = max(maximum_average, average_error)
        work = leaf.last_step_work
        if work is None:
            raise AssertionError("small leaf step produced no telemetry")
        iteration_rows.append(
            {
                "iteration": iteration,
                "dense_ms": dense_ms,
                "leaf_ms": leaf_ms,
                "dense_to_leaf_speed_ratio": dense_ms / leaf_ms,
                "regret_error": regret_error,
                "strategy_sum_error": sum_error,
                "current_policy_error": current_error,
                "average_policy_error": average_error,
                "terminal_contraction_ms": work.terminal_contraction_ms,
                "terminal_sparse_batches": sum(
                    row.terminal_sparse_batches for row in work.traversers
                ),
                "maximum_child_reach_disagreement": max(
                    row.maximum_child_reach_disagreement for row in work.traversers
                ),
            }
        )

    rounded_control = None
    if run_rounded_control:
        if first_dense_regrets is None:
            raise AssertionError("small dense control produced no first iteration")
        terminal_libraries = tuple(
            _terminal_library(
                layout=dense_layout,
                belief=belief,
                board=board,
                target=target,
                pot=parsed["pot"],
                bet_size=parsed["bet_size"],
            )[:2]
            for target in range(parsed["players"])
        )
        rounded = SparseOpenModePublicTreeCFR(
            dense_layout,
            workspace,
            sparse,
            terminal_libraries,
            parsed["solver_variant"],
            node_relative_tolerance=0.0,
            maximum_feature_width_per_batch=96,
            policy_cache_mode="rounded",
        )
        rounded.warm_start(policy, parsed["warm_regret_mass"])
        started = time.perf_counter()
        rounded.step()
        rounded_ms = (time.perf_counter() - started) * 1000.0
        first_leaf_ms = float(iteration_rows[0]["leaf_ms"])
        rounded_control = {
            "hands_per_player": hand_count,
            "range_family": family,
            "rounded_ms": rounded_ms,
            "leaf_ms": first_leaf_ms,
            "rounded_to_leaf_speedup": rounded_ms / first_leaf_ms,
            "regret_error_vs_dense": _table_error(
                rounded.regret_table(),
                first_dense_regrets,
            ),
        }

    return (
        {
            "hands_per_player": hand_count,
            "range_family": family,
            "deals": dense_layout.deal_count,
            "public_nodes": dense_layout.public_node_count,
            "information_sets": len(leaf.information_schema()),
            "maximum_regret_error": maximum_regret,
            "maximum_strategy_sum_error": maximum_sum,
            "maximum_current_policy_error": maximum_current,
            "maximum_average_policy_error": maximum_average,
            "iterations": iteration_rows,
            "workspace_timing": workspace_timing,
            "leaf_memory": leaf.memory_summary(),
            "dense_memory": dense.memory_summary(),
        },
        rounded_control,
    )


def _zero_reach_case(
    *,
    parsed: dict[str, Any],
    source: dict[str, Any],
    board: tuple[int, ...],
) -> dict[str, object]:
    _, policy = _source_profile(
        source,
        hand_count=4,
        family="balanced",
        checkpoint=parsed["source_checkpoint"],
    )
    belief = _canonical_belief(
        board=board,
        hand_count=4,
        family="balanced",
        components=parsed["mixture_components"],
        seed=parsed["axis_seed"],
    )
    game = _game_from_belief(
        belief=belief,
        pot=parsed["pot"],
        stack=parsed["stack"],
        bet_size=parsed["bet_size"],
    )
    dense_layout = PublicTreeTensorEvaluator(game)
    topology = representative_public_tree(
        belief,
        pot=parsed["pot"],
        stack=parsed["stack"],
        bet_size=parsed["bet_size"],
    )
    root = topology.nodes[0]
    edited = {key: dict(values) for key, values in policy.items()}
    for hand in belief.hands_by_player[root.player]:
        key = _information_key(topology, root.player, hand, root.history)
        edited[key] = {
            action: (0.0 if index == 0 else 1.0 / (len(root.actions) - 1))
            for index, action in enumerate(root.actions)
        }
    probabilities = compile_policy_probability_tape(
        topology,
        belief.hands_by_player,
        edited,
    )
    target_node = next(
        node_index
        for node_index, node in enumerate(topology.nodes)
        if node.history[:1] == ((root.player, root.actions[0]),)
        and node.player not in (root.player, TERMINAL_PLAYER)
    )
    target = topology.nodes[target_node].player
    workspace, _ = _open_workspace(
        belief,
        split_index=parsed["split_index"],
        query_chunk_records=parsed["query_chunk_records"],
    )
    sparse = SparseBidirectionalIncidence.compile(workspace)
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, belief.hands_by_player)
    )
    automata = build_leaf_adjoint_terminal_automata(
        topology,
        codes,
        pot=parsed["pot"],
        bet_size=parsed["bet_size"],
    )
    actual = {
        row.node_index: row
        for row in leaf_adjoint_cfr_traverser(
            topology,
            workspace,
            sparse,
            probabilities,
            automata[target],
            traverser=target,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
            terminal_batch_mode="heterogeneous",
        ).reads
    }
    expected = {
        row.node_index: row
        for row in dense_cfr_action_comparisons(
            dense_layout,
            probabilities,
            traverser=target,
        )
    }
    zero_nodes = tuple(
        node_index
        for node_index, row in expected.items()
        if not np.any(row.positive_reach)
    )
    if not zero_nodes:
        raise AssertionError("forced zero-reach control produced no zero-reach infosets")
    return {
        "target": target,
        "zero_reach_rows": len(zero_nodes),
        "maximum_zero_reach_regret_magnitude": max(
            float(np.max(np.abs(actual[node].regret_deltas))) for node in zero_nodes
        ),
        "maximum_zero_reach_regret_error": max(
            float(
                np.max(
                    np.abs(actual[node].regret_deltas - expected[node].regret_deltas)
                )
            )
            for node in zero_nodes
        ),
    }


def _gpu_read_errors(first: Any, second: Any) -> dict[str, float]:
    reach = numerator = regret = conditional = 0.0
    if len(first.reads) != len(second.reads):
        raise AssertionError("wide CPU/GPU CFR read counts differ")
    for cpu, gpu in zip(first.reads, second.reads, strict=True):
        if cpu.node_index != gpu.node_index:
            raise AssertionError("wide CPU/GPU CFR nodes differ")
        reach = max(
            reach,
            float(np.max(np.abs(cpu.counterfactual_reaches - gpu.counterfactual_reaches))),
        )
        numerator = max(
            numerator,
            float(np.max(np.abs(cpu.action_numerators - gpu.action_numerators))),
        )
        regret = max(
            regret,
            float(np.max(np.abs(cpu.regret_deltas - gpu.regret_deltas))),
        )
        conditional = max(
            conditional,
            float(
                np.max(
                    np.abs(
                        cpu.conditional_action_values
                        - gpu.conditional_action_values
                    )
                )
            ),
        )
    return {
        "reach": reach,
        "numerator": numerator,
        "regret": regret,
        "conditional": conditional,
    }


def _policy_is_finite_normalized(policy: dict[str, dict[str, float]]) -> bool:
    return bool(policy) and all(
        values
        and all(math.isfinite(value) and value >= 0.0 for value in values.values())
        and abs(math.fsum(values.values()) - 1.0) <= 1e-12
        for values in policy.values()
    )


def _wide_case(
    *,
    parsed: dict[str, Any],
    board: tuple[int, ...],
    family: str,
) -> dict[str, object]:
    belief = _canonical_belief(
        board=board,
        hand_count=parsed["wide_hands_per_player"],
        family=family,
        components=parsed["mixture_components"],
        seed=parsed["axis_seed"],
    )
    topology = representative_public_tree(
        belief,
        pot=parsed["pot"],
        stack=parsed["stack"],
        bet_size=parsed["bet_size"],
    )
    workspace, workspace_timing = _open_workspace(
        belief,
        split_index=parsed["split_index"],
        query_chunk_records=parsed["query_chunk_records"],
    )
    sparse = SparseBidirectionalIncidence.compile(workspace)
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, belief.hands_by_player)
    )
    automata = build_leaf_adjoint_terminal_automata(
        topology,
        codes,
        pot=parsed["pot"],
        bet_size=parsed["bet_size"],
    )
    solver = LeafAdjointPublicTreeCFR(
        topology,
        workspace,
        sparse,
        automata,
        parsed["solver_variant"],
        maximum_feature_width_per_batch=parsed[
            "maximum_feature_width_per_batch"
        ],
        hands_by_player=belief.hands_by_player,
        cupy_sparse=gpu,
    )
    uniform = solver.current_strategy()
    probabilities = solver.immutable_strategies()
    target = parsed["cpu_crosscheck_traverser"]
    started = time.perf_counter()
    cpu_read = leaf_adjoint_cfr_traverser(
        topology,
        workspace,
        sparse,
        probabilities,
        automata[target],
        traverser=target,
        maximum_feature_width_per_batch=parsed[
            "maximum_feature_width_per_batch"
        ],
        terminal_batch_mode="heterogeneous",
    )
    cpu_ms = (time.perf_counter() - started) * 1000.0
    release_cupy_memory_pool()
    started = time.perf_counter()
    gpu_read = leaf_adjoint_cfr_traverser(
        topology,
        workspace,
        sparse,
        probabilities,
        automata[target],
        traverser=target,
        maximum_feature_width_per_batch=parsed[
            "maximum_feature_width_per_batch"
        ],
        terminal_batch_mode="heterogeneous",
        cupy_sparse=gpu,
    )
    gpu_ms = (time.perf_counter() - started) * 1000.0
    errors = _gpu_read_errors(cpu_read, gpu_read)

    release_cupy_memory_pool()
    checkpoints = []
    step_rows = []
    for iteration in range(1, parsed["wide_iterations"] + 1):
        started = time.perf_counter()
        solver.step()
        step_ms = (time.perf_counter() - started) * 1000.0
        work = solver.last_step_work
        if work is None:
            raise AssertionError("wide leaf-adjoint step produced no telemetry")
        current = solver.current_strategy()
        average = solver.average_strategy()
        checkpoints.append(
            {
                "iteration": iteration,
                "current_policy_sha256": policy_digest(current),
                "average_policy_sha256": policy_digest(average),
                "current_statistics": policy_statistics(current),
                "average_statistics": policy_statistics(average),
                "current_tv_from_uniform": mean_policy_total_variation(
                    uniform, current
                ),
                "average_tv_from_uniform": mean_policy_total_variation(
                    uniform, average
                ),
                "current_policy": current,
                "average_policy": average,
            }
        )
        step_rows.append(
            {
                "iteration": iteration,
                "wall_ms": step_ms,
                "terminal_contraction_ms": work.terminal_contraction_ms,
                "terminal_contractions": sum(
                    row.terminal_contractions for row in work.traversers
                ),
                "terminal_sparse_batches": sum(
                    row.terminal_sparse_batches for row in work.traversers
                ),
                "strategic_reads": sum(
                    row.strategic_reads for row in work.traversers
                ),
                "hand_action_entries": sum(
                    row.hand_action_entries for row in work.traversers
                ),
                "maximum_child_reach_disagreement": max(
                    row.maximum_child_reach_disagreement for row in work.traversers
                ),
                "maximum_host_peak_numeric_bytes": (
                    max(
                        row.maximum_terminal_peak_numeric_bytes
                        for row in work.traversers
                    )
                    + solver.accumulator_numeric_bytes()
                    + solver.memory_summary()["terminal_automaton_numeric_bytes"]
                ),
                "maximum_gpu_pool_bytes": max(
                    row.maximum_gpu_pool_total_bytes for row in work.traversers
                ),
            }
        )

    finite = (
        _policy_is_finite_normalized(solver.current_strategy())
        and _policy_is_finite_normalized(solver.average_strategy())
        and all(
            math.isfinite(value)
            for row in solver.regret_table().values()
            for value in row.values()
        )
    )
    return {
        "hands_per_player": parsed["wide_hands_per_player"],
        "range_family": family,
        "public_nodes": topology.public_node_count,
        "information_sets": len(solver.information_schema()),
        "hand_action_entries": sum(
            len(actions) for actions in solver.information_schema().values()
        ),
        "cpu_crosscheck_traverser": target,
        "cpu_crosscheck_ms": cpu_ms,
        "gpu_crosscheck_ms": gpu_ms,
        "gpu_operator_upload_ms": gpu.upload_ms,
        "gpu_crosscheck_speedup": cpu_ms / gpu_ms,
        "charged_gpu_crosscheck_speedup": cpu_ms / (gpu_ms + gpu.upload_ms),
        "maximum_reach_error": errors["reach"],
        "maximum_numerator_error": errors["numerator"],
        "maximum_regret_error": errors["regret"],
        "maximum_conditional_error": errors["conditional"],
        "crosscheck_cpu_child_reach_disagreement": (
            cpu_read.maximum_child_reach_disagreement
        ),
        "crosscheck_gpu_child_reach_disagreement": (
            gpu_read.maximum_child_reach_disagreement
        ),
        "workspace_timing": workspace_timing,
        "step_rows": step_rows,
        "checkpoints": checkpoints,
        "finite_normalized_policies": finite,
        "memory": solver.memory_summary(),
        "gpu": {
            "cupy_version": gpu.cupy_version,
            "cuda_runtime_version": gpu.cuda_runtime_version,
            "cuda_driver_version": gpu.cuda_driver_version,
            "compute_capability": gpu.compute_capability,
        },
    }


def run_leaf_adjoint_cfr_audit(config: dict[str, Any]) -> dict[str, object]:
    parsed = parse_leaf_adjoint_cfr_audit_config(config)
    import scipy

    cupy_started = time.perf_counter()
    cp, _ = _cupy_modules()
    cupy_import_ms = (time.perf_counter() - cupy_started) * 1000.0
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from leaf-adjoint freeze")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from leaf-adjoint freeze")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from leaf-adjoint freeze")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from leaf-adjoint freeze")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the leaf-adjoint floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed["required_compute_capability"]:
        raise ValueError("GPU compute capability differs from leaf-adjoint freeze")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("frozen optional CUDA DLL directory is not configured")

    source = json.loads(_SOURCE.read_text(encoding="utf-8"))
    board = parse_cards(*parsed["board"])
    started = time.perf_counter()
    small_rows = []
    rounded_control = None
    for hand_count in parsed["small_hands_per_player"]:
        for family in parsed["range_families"]:
            row, control = _small_case(
                parsed=parsed,
                source=source,
                board=board,
                hand_count=hand_count,
                family=family,
                run_rounded_control=(hand_count == 7 and family == "balanced"),
            )
            small_rows.append(row)
            if control is not None:
                rounded_control = control
    if rounded_control is None:
        raise AssertionError("rounded cache control was not executed")
    zero_reach = _zero_reach_case(parsed=parsed, source=source, board=board)
    wide_rows = [
        _wide_case(parsed=parsed, board=board, family=family)
        for family in parsed["range_families"]
    ]

    aggregate = {
        "maximum_small_regret_error": max(
            float(row["maximum_regret_error"]) for row in small_rows
        ),
        "maximum_small_strategy_sum_error": max(
            float(row["maximum_strategy_sum_error"]) for row in small_rows
        ),
        "maximum_small_current_policy_error": max(
            float(row["maximum_current_policy_error"]) for row in small_rows
        ),
        "maximum_small_average_policy_error": max(
            float(row["maximum_average_policy_error"]) for row in small_rows
        ),
        "small_rounded_to_leaf_speedup": float(
            rounded_control["rounded_to_leaf_speedup"]
        ),
        "maximum_wide_reach_error": max(
            float(row["maximum_reach_error"]) for row in wide_rows
        ),
        "maximum_wide_numerator_error": max(
            float(row["maximum_numerator_error"]) for row in wide_rows
        ),
        "maximum_wide_regret_error": max(
            float(row["maximum_regret_error"]) for row in wide_rows
        ),
        "maximum_wide_conditional_error": max(
            float(row["maximum_conditional_error"]) for row in wide_rows
        ),
        "minimum_raw_wide_gpu_speedup": min(
            float(row["gpu_crosscheck_speedup"]) for row in wide_rows
        ),
        "minimum_charged_wide_gpu_speedup": min(
            float(row["charged_gpu_crosscheck_speedup"]) for row in wide_rows
        ),
        "validation_raw_wide_gpu_speedup": next(
            float(row["gpu_crosscheck_speedup"])
            for row in wide_rows
            if row["range_family"] == parsed["validation_speed_family"]
        ),
        "validation_charged_wide_gpu_speedup": next(
            float(row["charged_gpu_crosscheck_speedup"])
            for row in wide_rows
            if row["range_family"] == parsed["validation_speed_family"]
        ),
        "maximum_wide_step_ms": max(
            float(step["wall_ms"])
            for row in wide_rows
            for step in row["step_rows"]
        ),
        "maximum_wide_host_peak_numeric_bytes": max(
            int(step["maximum_host_peak_numeric_bytes"])
            for row in wide_rows
            for step in row["step_rows"]
        ),
        "maximum_wide_gpu_pool_bytes": max(
            int(step["maximum_gpu_pool_bytes"])
            for row in wide_rows
            for step in row["step_rows"]
        ),
        "maximum_wide_child_reach_disagreement": max(
            float(step["maximum_child_reach_disagreement"])
            for row in wide_rows
            for step in row["step_rows"]
        ),
        "minimum_current_tv_after_first_step": min(
            float(row["checkpoints"][0]["current_tv_from_uniform"])
            for row in wide_rows
        ),
        "minimum_average_tv_after_second_step": min(
            float(row["checkpoints"][1]["average_tv_from_uniform"])
            for row in wide_rows
        ),
    }
    gates = parsed["gates"]
    gate_results = {
        "small_row_count": len(small_rows) == gates["expected_small_rows"],
        "wide_row_count": len(wide_rows) == gates["expected_wide_rows"],
        "small_regret_identity": aggregate["maximum_small_regret_error"]
        <= gates["maximum_small_regret_error"],
        "small_strategy_sum_identity": aggregate[
            "maximum_small_strategy_sum_error"
        ]
        <= gates["maximum_small_strategy_sum_error"],
        "small_current_policy_identity": aggregate[
            "maximum_small_current_policy_error"
        ]
        <= gates["maximum_small_current_policy_error"],
        "small_average_policy_identity": aggregate[
            "maximum_small_average_policy_error"
        ]
        <= gates["maximum_small_average_policy_error"],
        "rounded_cache_speedup": aggregate["small_rounded_to_leaf_speedup"]
        >= gates["minimum_small_rounded_to_leaf_speedup"],
        "rounded_cache_identity": float(rounded_control["regret_error_vs_dense"])
        <= gates["maximum_small_rounded_control_regret_error"],
        "zero_reach_rows": int(zero_reach["zero_reach_rows"])
        >= gates["minimum_zero_reach_rows"],
        "zero_reach_regret_identity": float(
            zero_reach["maximum_zero_reach_regret_error"]
        )
        <= gates["maximum_zero_reach_regret_error"],
        "zero_reach_exact_zero": float(
            zero_reach["maximum_zero_reach_regret_magnitude"]
        )
        <= gates["maximum_zero_reach_regret_magnitude"],
        "wide_reach_identity": aggregate["maximum_wide_reach_error"]
        <= gates["maximum_wide_reach_error"],
        "wide_numerator_identity": aggregate["maximum_wide_numerator_error"]
        <= gates["maximum_wide_numerator_error"],
        "wide_regret_identity": aggregate["maximum_wide_regret_error"]
        <= gates["maximum_wide_regret_error"],
        "wide_conditional_identity": aggregate["maximum_wide_conditional_error"]
        <= gates["maximum_wide_conditional_error"],
        "wide_child_reach_identity": aggregate[
            "maximum_wide_child_reach_disagreement"
        ]
        <= gates["maximum_wide_child_reach_disagreement"],
        "validation_gpu_speedup": aggregate[
            "validation_charged_wide_gpu_speedup"
        ]
        >= gates["minimum_validation_wide_gpu_speedup"],
        "all_wide_gpu_speedup": aggregate["minimum_charged_wide_gpu_speedup"]
        >= gates["minimum_all_wide_gpu_speedup"],
        "wide_step_latency": aggregate["maximum_wide_step_ms"]
        <= gates["maximum_wide_step_ms"],
        "wide_host_peak": aggregate["maximum_wide_host_peak_numeric_bytes"]
        <= gates["maximum_wide_host_peak_numeric_bytes"],
        "wide_gpu_peak": aggregate["maximum_wide_gpu_pool_bytes"]
        <= gates["maximum_wide_gpu_pool_bytes"],
        "wide_current_moves": aggregate["minimum_current_tv_after_first_step"]
        >= gates["minimum_wide_current_policy_tv_after_first_step"],
        "wide_average_moves": aggregate["minimum_average_tv_after_second_step"]
        >= gates["minimum_wide_average_policy_tv_after_second_step"],
        "wide_schema": all(
            int(row["information_sets"]) == gates["expected_wide_information_sets"]
            and int(row["hand_action_entries"])
            == gates["expected_wide_hand_action_entries"]
            for row in wide_rows
        ),
        "wide_finite_normalized": all(
            bool(row["finite_normalized_policies"]) for row in wide_rows
        )
        == gates["require_finite_normalized_wide_policies"],
    }
    gate_results["passed"] = all(gate_results.values())
    properties = cp.cuda.runtime.getDeviceProperties(0)
    name = properties["name"]
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    return {
        "schema_version": 1,
        "experiment_type": "leaf_adjoint_dense_free_cfr_gpu_audit",
        "status": "frozen_audit_executed",
        "config": parsed,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_artifact_sha256": _sha256(_SOURCE),
        "small_rows": small_rows,
        "rounded_control": rounded_control,
        "zero_reach": zero_reach,
        "wide_rows": wide_rows,
        "aggregate": aggregate,
        "gates": gate_results,
        "counts": {"small_rows": len(small_rows), "wide_rows": len(wide_rows)},
        "timing": {
            "wall_seconds": time.perf_counter() - started,
            "cupy_import_ms": cupy_import_ms,
        },
        "environment": {
            **environment_metadata(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "cupy_version": cp.__version__,
            "cuda_runtime_version": cp.cuda.runtime.runtimeGetVersion(),
            "cuda_driver_version": cp.cuda.runtime.driverGetVersion(),
            "gpu_name": str(name),
            "compute_capability": str(cp.cuda.Device(0).compute_capability),
        },
        "limitations": [
            "The wide checkpoints contain only two cold DCFR iterations and carry no equilibrium-quality claim.",
            "Balanced h32 target-0 CPU/GPU performance and cap 384 were disclosed development evidence; blocker-heavy h32 remained sealed.",
            "CuPy keeps the CSR operators resident but transfers each dense feature batch and result; fusion remains unfinished.",
            "The audit evaluates the one-bet equal-stack river game, not full-street six-max NLHE.",
            "No raw floating argmax is used; best-response action certification remains a separate guarded primitive.",
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
    result = run_leaf_adjoint_cfr_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "leaf-adjoint CFR audit: "
        f"small={result['counts']['small_rows']}, "
        f"wide={result['counts']['wide_rows']}, "
        "validation_gpu_charged="
        f"{result['aggregate']['validation_charged_wide_gpu_speedup']:.3f}x, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
