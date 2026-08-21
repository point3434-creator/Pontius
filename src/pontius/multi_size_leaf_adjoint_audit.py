"""Preregistered correctness and geometry audit for two-size six-seat river."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any

import numpy as np

from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .incremental_policy_tt import compile_policy_probability_tape
from .leaf_adjoint_cfr import build_leaf_adjoint_terminal_automata
from .multi_size_leaf_adjoint import (
    build_multi_size_leaf_adjoint_terminal_automata,
    multi_size_leaf_adjoint_cfr_traverser,
    multi_size_terminal_groups,
)
from .multi_size_public_tree_tensor import MultiSizePublicTreeTensorEvaluator
from .open_mode_audit import _canonical_belief, _open_workspace
from .open_mode_cfr_bridge import dense_cfr_action_comparisons
from .public_policy_tt import representative_public_tree
from .reporting import environment_metadata
from .resident_heterogeneous_leaf_contraction import CuPyResidentAutomatonCache
from .river import parse_cards
from .river_multiway import MultiwayRiverDeal
from .river_multiway_multi_size import MultiwayMultiSizeRiverHoldem
from .showdown_value_rank_screen import _rank_codes
from .sparse_incidence_open_mode import SparseBidirectionalIncidence


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "multi-size-leaf-adjoint-audit-v1.json"
_OUTPUT = _ROOT / "experiments" / "results" / "multi-size-leaf-adjoint-audit-v1.json"
_REQUIREMENTS = _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
_IMPLEMENTATION = Path(__file__)
_SIZED_GAME = _ROOT / "src" / "pontius" / "river_multiway_multi_size.py"
_SIZED_LAYOUT = _ROOT / "src" / "pontius" / "multi_size_public_tree_tensor.py"
_SIZED_LEAF = _ROOT / "src" / "pontius" / "multi_size_leaf_adjoint.py"
_ONE_SIZE_GAME = _ROOT / "src" / "pontius" / "river_multiway.py"
_ONE_SIZE_LAYOUT = _ROOT / "src" / "pontius" / "public_tree_tensor.py"
_ONE_SIZE_LEAF = _ROOT / "src" / "pontius" / "leaf_adjoint_cfr.py"
_AUTOMATON = _ROOT / "src" / "pontius" / "structured_showdown_automaton.py"
_DENSE_BRIDGE = _ROOT / "src" / "pontius" / "open_mode_cfr_bridge.py"

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_requirements_sha256",
    "expected_audit_implementation_sha256",
    "expected_sized_game_sha256",
    "expected_sized_layout_sha256",
    "expected_sized_leaf_sha256",
    "expected_one_size_game_sha256",
    "expected_one_size_layout_sha256",
    "expected_one_size_leaf_sha256",
    "expected_automaton_sha256",
    "expected_dense_bridge_sha256",
    "board",
    "pot",
    "stack",
    "bet_sizes",
    "players",
    "hands_per_player",
    "range_families",
    "mixture_components",
    "split_index",
    "query_chunk_records",
    "topology_validation_deals",
    "maximum_feature_width_per_batch",
    "required_numpy_version",
    "required_scipy_version",
    "required_cupy_version",
    "required_cuda_runtime_version",
    "minimum_cuda_driver_version",
    "required_compute_capability",
    "cuda_dll_environment_variable",
    "gates",
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def parse_multi_size_leaf_adjoint_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the frozen two-size correctness and geometry protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("multi-size leaf-adjoint config fields differ from ADR-0125")
    expected = {
        "evidence_stage": (
            "preregistered_after_h2_implementation_controls_before_any_h4_or_h7_"
            "sized_leaf_adjoint_label_or_timing"
        ),
        "seed": 20260820,
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_sizes": [3.0, 6.0],
        "players": 6,
        "hands_per_player": [4, 7],
        "range_families": ["balanced", "blocker_heavy"],
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "topology_validation_deals": 64,
        "maximum_feature_width_per_batch": 384,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in expected.items()):
        raise ValueError("multi-size leaf-adjoint frozen workload differs from ADR-0125")

    source_paths = {
        "expected_requirements_sha256": _REQUIREMENTS,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
        "expected_sized_game_sha256": _SIZED_GAME,
        "expected_sized_layout_sha256": _SIZED_LAYOUT,
        "expected_sized_leaf_sha256": _SIZED_LEAF,
        "expected_one_size_game_sha256": _ONE_SIZE_GAME,
        "expected_one_size_layout_sha256": _ONE_SIZE_LAYOUT,
        "expected_one_size_leaf_sha256": _ONE_SIZE_LEAF,
        "expected_automaton_sha256": _AUTOMATON,
        "expected_dense_bridge_sha256": _DENSE_BRIDGE,
    }
    for field, path in source_paths.items():
        if config[field] != _sha256(path):
            raise ValueError(f"multi-size leaf-adjoint source hash mismatch: {field}")

    expected_gates = {
        "expected_cases": 4,
        "expected_leaf_traversers": 24,
        "expected_leaf_action_reads": 1512,
        "expected_one_size_public_nodes": 385,
        "expected_one_size_strategic_nodes": 192,
        "expected_one_size_terminal_nodes": 193,
        "expected_one_size_terminal_groups": 64,
        "expected_two_size_public_nodes": 763,
        "expected_two_size_strategic_nodes": 378,
        "expected_two_size_terminal_nodes": 385,
        "expected_two_size_terminal_groups": 127,
        "maximum_topology_mismatches": 0,
        "maximum_terminal_transition_mismatches": 0,
        "maximum_terminal_payoff_error": 1e-12,
        "maximum_terminal_zero_sum_error": 1e-10,
        "maximum_counterfactual_reach_error": 5e-10,
        "maximum_action_numerator_error": 5e-9,
        "maximum_conditional_action_value_error": 5e-8,
        "maximum_regret_delta_error": 5e-9,
        "maximum_action_value_loss": 1e-9,
        "maximum_child_reach_disagreement": 5e-10,
        "maximum_host_numeric_bytes": 8000000000,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_total_audit_seconds": 1800.0,
    }
    if config["gates"] != expected_gates:
        raise ValueError("multi-size leaf-adjoint gates differ from ADR-0125")
    return {
        **config,
        "bet_sizes": tuple(config["bet_sizes"]),
        "hands_per_player": tuple(config["hands_per_player"]),
        "range_families": tuple(config["range_families"]),
        "gates": dict(config["gates"]),
    }


def _validate_runtime(parsed: dict[str, Any]) -> dict[str, Any]:
    import scipy

    if np.__version__ != parsed["required_numpy_version"]:
        raise RuntimeError("NumPy version differs from frozen action-width audit")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise RuntimeError("SciPy version differs from frozen action-width audit")
    variable = parsed["cuda_dll_environment_variable"]
    if not os.environ.get(variable):
        raise RuntimeError(f"{variable} is required for the frozen CUDA runtime")
    cp, _ = _cupy_modules()
    runtime = int(cp.cuda.runtime.runtimeGetVersion())
    driver = int(cp.cuda.runtime.driverGetVersion())
    properties = cp.cuda.runtime.getDeviceProperties(0)
    capability = f"{int(properties['major'])}{int(properties['minor'])}"
    if cp.__version__ != parsed["required_cupy_version"]:
        raise RuntimeError("CuPy version differs from frozen action-width audit")
    if runtime != parsed["required_cuda_runtime_version"]:
        raise RuntimeError("CUDA runtime differs from frozen action-width audit")
    if driver < parsed["minimum_cuda_driver_version"]:
        raise RuntimeError("CUDA driver is below the frozen action-width minimum")
    if capability != parsed["required_compute_capability"]:
        raise RuntimeError("GPU compute capability differs from frozen action-width audit")
    return {
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "cupy": cp.__version__,
        "cuda_runtime": runtime,
        "cuda_driver": driver,
        "compute_capability": capability,
    }


def _game_from_belief(
    belief: Any,
    *,
    pot: float,
    stack: float,
    bet_sizes: tuple[float, ...],
) -> MultiwayMultiSizeRiverHoldem:
    materialized = belief.materialize()
    axes = belief.hands_by_player
    joint = {
        MultiwayRiverDeal(
            tuple(axes[seat][indices[seat]] for seat in range(belief.num_players))
        ): float(probability)
        for indices, probability in zip(
            materialized.assignments,
            materialized.probabilities,
            strict=True,
        )
    }
    return MultiwayMultiSizeRiverHoldem.from_joint_weights(
        board=belief.board,
        pot=pot,
        stacks=(stack,) * belief.num_players,
        bet_sizes=bet_sizes,
        joint_weights=joint,
    )


def _hashed_policy(layout: MultiSizePublicTreeTensorEvaluator) -> dict[str, Any]:
    result = {}
    for key, actions in layout.information_schema().items():
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        weights = tuple(float(1 + digest[index] % 29) for index in range(len(actions)))
        total = math.fsum(weights)
        result[key] = {
            action: weights[index] / total
            for index, action in enumerate(actions)
        }
    return result


def _policy_entries(layout: Any, axes: tuple[tuple[Any, ...], ...]) -> int:
    return sum(
        len(axes[node.player]) * len(node.actions)
        for node in layout.nodes
        if node.player >= 0
    )


def _automaton_bytes(libraries: tuple[dict[str, Any], ...]) -> int:
    return sum(automaton.numeric_bytes for library in libraries for automaton in library.values())


def _transition_digest(automaton: Any) -> str:
    digest = hashlib.sha256()
    digest.update(
        repr(
            (
                automaton.shape,
                automaton.contenders,
                automaton.target_player,
                automaton.constant_winner_shortcut,
            )
        ).encode("ascii")
    )
    for values in (*automaton.transitions, *automaton.bond_states):
        digest.update(repr((values.shape, values.dtype.str)).encode("ascii"))
        digest.update(values.tobytes(order="C"))
    return digest.hexdigest()


def _library_geometry(libraries: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    automata = tuple(value for library in libraries for value in library.values())
    transition_digests = {_transition_digest(automaton) for automaton in automata}
    return {
        "automata": len(automata),
        "numeric_bytes": sum(automaton.numeric_bytes for automaton in automata),
        "runtime_numeric_bytes": sum(
            automaton.runtime_numeric_bytes for automaton in automata
        ),
        "state_metadata_bytes": sum(
            automaton.state_metadata_bytes for automaton in automata
        ),
        "transition_records": sum(
            automaton.transition_records for automaton in automata
        ),
        "maximum_state_rank": max(automaton.maximum_state_rank for automaton in automata),
        "distinct_transition_topologies": len(transition_digests),
    }


def _resident_geometry(
    workspace: Any,
    libraries: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    started = time.perf_counter()
    numeric_bytes = 0
    total_middle_rank = 0
    maximum_middle_rank = 0
    maximum_pool = 0
    per_seat = []
    for target, library in enumerate(libraries):
        cache = CuPyResidentAutomatonCache.compile(
            workspace,
            library,
            target_seat=target,
        )
        row = {
            "target": target,
            "unique_automata": cache.unique_automata,
            "total_middle_rank": cache.total_middle_rank,
            "maximum_middle_rank": cache.maximum_middle_rank,
            "numeric_bytes": cache.numeric_bytes,
            "wall_ms": cache.wall_ms,
            "pool_total_bytes": cache.pool_total_bytes,
        }
        per_seat.append(row)
        numeric_bytes += cache.numeric_bytes
        total_middle_rank += cache.total_middle_rank
        maximum_middle_rank = max(maximum_middle_rank, cache.maximum_middle_rank)
        maximum_pool = max(maximum_pool, cache.pool_total_bytes)
        del cache
    wall_ms = (time.perf_counter() - started) * 1000.0
    release_cupy_memory_pool()
    return {
        "numeric_bytes": numeric_bytes,
        "total_middle_rank": total_middle_rank,
        "maximum_middle_rank": maximum_middle_rank,
        "maximum_pool_total_bytes": maximum_pool,
        "compile_ms": wall_ms,
        "per_seat": per_seat,
    }


def _terminal_errors(
    layout: MultiSizePublicTreeTensorEvaluator,
    libraries: tuple[dict[str, Any], ...],
    strength_codes: tuple[np.ndarray, ...],
) -> dict[str, Any]:
    slot_by_key = {
        group.key: group.terminal_slots[0]
        for group in multi_size_terminal_groups(layout)
    }
    assignments = np.ascontiguousarray(layout.hand_ids, dtype=np.int32)
    maximum_payoff_error = 0.0
    transition_mismatches = 0
    for target, library in enumerate(libraries):
        for key, automaton in library.items():
            actual = automaton.evaluate_assignments(assignments)
            expected = layout.terminal_values[slot_by_key[key], :, target]
            maximum_payoff_error = max(
                maximum_payoff_error,
                float(np.max(np.abs(actual - expected))),
            )
            transition_mismatches += automaton.transition_mismatches(strength_codes)
    return {
        "maximum_payoff_error": maximum_payoff_error,
        "transition_mismatches": transition_mismatches,
        "maximum_zero_sum_error": float(
            np.max(np.abs(np.sum(layout.terminal_values, axis=2)))
        ),
    }


def _comparison_errors(actual: Any, expected: Any) -> dict[str, float | int]:
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
    selected = np.argmax(actual.action_numerators, axis=1).astype(np.int32)
    selected[~actual.positive_reach] = 0
    mismatches = int(np.count_nonzero(selected != expected.selected_action_indices))
    rows = np.arange(len(selected), dtype=np.int32)
    expected_best = expected.action_numerators[
        rows,
        expected.selected_action_indices,
    ]
    selected_values = expected.action_numerators[rows, selected]
    loss = np.maximum(0.0, expected_best - selected_values)
    loss[~positive] = 0.0
    return {
        "counterfactual_reach_error": float(
            np.max(
                np.abs(
                    actual.counterfactual_reaches - expected.counterfactual_reaches
                )
            )
        ),
        "action_numerator_error": float(
            np.max(np.abs(actual.action_numerators - expected.action_numerators))
        ),
        "conditional_action_value_error": conditional_error,
        "regret_delta_error": float(
            np.max(np.abs(actual.regret_deltas - expected.regret_deltas))
        ),
        "action_identity_mismatches": mismatches,
        "action_value_loss": float(np.max(loss)),
    }


def _case(
    parsed: dict[str, Any],
    *,
    board: tuple[int, ...],
    hand_count: int,
    family: str,
) -> dict[str, Any]:
    case_started = time.perf_counter()
    belief = _canonical_belief(
        board=board,
        hand_count=hand_count,
        family=family,
        components=parsed["mixture_components"],
        seed=parsed["seed"],
    )
    game = _game_from_belief(
        belief,
        pot=parsed["pot"],
        stack=parsed["stack"],
        bet_sizes=parsed["bet_sizes"],
    )
    layout_started = time.perf_counter()
    layout = MultiSizePublicTreeTensorEvaluator(game)
    layout_ms = (time.perf_counter() - layout_started) * 1000.0
    workspace, workspace_work = _open_workspace(
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

    automata_started = time.perf_counter()
    sized_libraries = build_multi_size_leaf_adjoint_terminal_automata(
        layout,
        codes,
        pot=parsed["pot"],
    )
    sized_automata_ms = (time.perf_counter() - automata_started) * 1000.0
    terminal_errors = _terminal_errors(layout, sized_libraries, codes)

    one_layout = representative_public_tree(
        belief,
        pot=parsed["pot"],
        stack=parsed["stack"],
        bet_size=parsed["bet_sizes"][0],
    )
    one_libraries = build_leaf_adjoint_terminal_automata(
        one_layout,
        codes,
        pot=parsed["pot"],
        bet_size=parsed["bet_sizes"][0],
    )
    one_geometry = _library_geometry(one_libraries)
    sized_geometry = _library_geometry(sized_libraries)
    one_resident = _resident_geometry(workspace, one_libraries)
    sized_resident = _resident_geometry(workspace, sized_libraries)

    policy = _hashed_policy(layout)
    probabilities = compile_policy_probability_tape(
        layout,
        belief.hands_by_player,
        policy,
    )
    traverser_rows = []
    for traverser in range(parsed["players"]):
        dense_started = time.perf_counter()
        expected = dense_cfr_action_comparisons(
            layout,
            probabilities,
            traverser=traverser,
        )
        dense_ms = (time.perf_counter() - dense_started) * 1000.0
        leaf_started = time.perf_counter()
        actual = multi_size_leaf_adjoint_cfr_traverser(
            layout,
            workspace,
            sparse,
            probabilities,
            sized_libraries[traverser],
            traverser=traverser,
            maximum_feature_width_per_batch=(
                parsed["maximum_feature_width_per_batch"]
            ),
            cupy_sparse=gpu,
        )
        leaf_ms = (time.perf_counter() - leaf_started) * 1000.0
        expected_by_node = {row.node_index: row for row in expected}
        errors = [
            _comparison_errors(row, expected_by_node[row.node_index])
            for row in actual.reads
        ]
        traverser_rows.append(
            {
                "traverser": traverser,
                "action_reads": len(actual.reads),
                "terminal_contractions": actual.terminal_contractions,
                "terminal_sparse_batches": actual.terminal_sparse_batches,
                "dense_ms": dense_ms,
                "leaf_ms": leaf_ms,
                "terminal_contraction_ms": actual.terminal_contraction_ms,
                "reverse_adjoint_ms": actual.reverse_adjoint_ms,
                "maximum_child_reach_disagreement": (
                    actual.maximum_child_reach_disagreement
                ),
                "maximum_terminal_middle_rank": (
                    actual.maximum_terminal_middle_rank
                ),
                "maximum_terminal_peak_numeric_bytes": (
                    actual.maximum_terminal_peak_numeric_bytes
                ),
                "maximum_gpu_pool_total_bytes": (
                    actual.maximum_gpu_pool_total_bytes
                ),
                "maximum_counterfactual_reach_error": max(
                    row["counterfactual_reach_error"] for row in errors
                ),
                "maximum_action_numerator_error": max(
                    row["action_numerator_error"] for row in errors
                ),
                "maximum_conditional_action_value_error": max(
                    row["conditional_action_value_error"] for row in errors
                ),
                "maximum_regret_delta_error": max(
                    row["regret_delta_error"] for row in errors
                ),
                "action_identity_mismatches": sum(
                    int(row["action_identity_mismatches"]) for row in errors
                ),
                "maximum_action_value_loss": max(
                    row["action_value_loss"] for row in errors
                ),
            }
        )
        del actual, expected, expected_by_node, errors
        gc.collect()

    memory = layout.memory_summary()
    topology = layout.topology_summary()
    topology["topology_mismatches"] = layout.topology_mismatch_count(
        parsed["topology_validation_deals"]
    )
    topology["validated_deals"] = min(
        layout.deal_count,
        parsed["topology_validation_deals"],
    )
    one_topology = one_layout.topology_summary()
    result = {
        "hands_per_player": hand_count,
        "range_family": family,
        "joint_deals": layout.deal_count,
        "layout_compile_ms": layout_ms,
        "workspace_work": workspace_work,
        "sized_automata_compile_ms": sized_automata_ms,
        "topology": topology,
        "one_size_topology": one_topology,
        "one_size_terminal_groups": 64,
        "two_size_terminal_groups": len(multi_size_terminal_groups(layout)),
        "one_size_policy_entries": _policy_entries(
            one_layout,
            belief.hands_by_player,
        ),
        "two_size_policy_entries": _policy_entries(
            layout,
            belief.hands_by_player,
        ),
        "terminal_errors": terminal_errors,
        "one_size_automata": one_geometry,
        "two_size_automata": sized_geometry,
        "one_size_resident_cache": one_resident,
        "two_size_resident_cache": sized_resident,
        "layout_memory": memory,
        "traversers": traverser_rows,
        "case_wall_seconds": time.perf_counter() - case_started,
    }
    del (
        probabilities,
        policy,
        one_libraries,
        sized_libraries,
        one_layout,
        gpu,
        sparse,
        workspace,
        layout,
        game,
        belief,
    )
    gc.collect()
    release_cupy_memory_pool()
    return result


def _gate_results(
    parsed: dict[str, Any],
    cases: list[dict[str, Any]],
    wall_seconds: float,
) -> dict[str, bool]:
    gates = parsed["gates"]
    traversers = [row for case in cases for row in case["traversers"]]
    return {
        "case_count": len(cases) == gates["expected_cases"],
        "leaf_traverser_count": (
            len(traversers) == gates["expected_leaf_traversers"]
        ),
        "leaf_action_read_count": (
            sum(row["action_reads"] for row in traversers)
            == gates["expected_leaf_action_reads"]
        ),
        "one_size_topology": all(
            case["one_size_topology"]["public_nodes"]
            == gates["expected_one_size_public_nodes"]
            and case["one_size_topology"]["strategic_public_nodes"]
            == gates["expected_one_size_strategic_nodes"]
            and case["one_size_topology"]["terminal_public_nodes"]
            == gates["expected_one_size_terminal_nodes"]
            and case["one_size_terminal_groups"]
            == gates["expected_one_size_terminal_groups"]
            for case in cases
        ),
        "two_size_topology": all(
            case["topology"]["public_nodes"]
            == gates["expected_two_size_public_nodes"]
            and case["topology"]["strategic_public_nodes"]
            == gates["expected_two_size_strategic_nodes"]
            and case["topology"]["terminal_public_nodes"]
            == gates["expected_two_size_terminal_nodes"]
            and case["two_size_terminal_groups"]
            == gates["expected_two_size_terminal_groups"]
            for case in cases
        ),
        "topology_identity": all(
            case["topology"]["children_are_topological"]
            and case["topology"]["numeric_tensors_are_float64_contiguous"]
            and case["topology"].get("unique_terminal_descriptors") == 127
            for case in cases
        ),
        "topology_mismatches": all(
            case["topology"].get("topology_mismatches", 0)
            <= gates["maximum_topology_mismatches"]
            for case in cases
        ),
        "terminal_transitions": max(
            case["terminal_errors"]["transition_mismatches"] for case in cases
        )
        <= gates["maximum_terminal_transition_mismatches"],
        "terminal_payoffs": max(
            case["terminal_errors"]["maximum_payoff_error"] for case in cases
        )
        <= gates["maximum_terminal_payoff_error"],
        "terminal_zero_sum": max(
            case["terminal_errors"]["maximum_zero_sum_error"] for case in cases
        )
        <= gates["maximum_terminal_zero_sum_error"],
        "counterfactual_reaches": max(
            row["maximum_counterfactual_reach_error"] for row in traversers
        )
        <= gates["maximum_counterfactual_reach_error"],
        "action_numerators": max(
            row["maximum_action_numerator_error"] for row in traversers
        )
        <= gates["maximum_action_numerator_error"],
        "conditional_action_values": max(
            row["maximum_conditional_action_value_error"] for row in traversers
        )
        <= gates["maximum_conditional_action_value_error"],
        "regret_deltas": max(
            row["maximum_regret_delta_error"] for row in traversers
        )
        <= gates["maximum_regret_delta_error"],
        "action_value_loss": max(
            row["maximum_action_value_loss"] for row in traversers
        )
        <= gates["maximum_action_value_loss"],
        "child_reach_identity": max(
            row["maximum_child_reach_disagreement"] for row in traversers
        )
        <= gates["maximum_child_reach_disagreement"],
        "host_memory": max(
            case["layout_memory"]["persistent_numeric_bytes"]
            + case["layout_memory"]["estimated_hot_scratch_bytes"]
            for case in cases
        )
        <= gates["maximum_host_numeric_bytes"],
        "gpu_memory": max(
            max(row["maximum_gpu_pool_total_bytes"] for row in case["traversers"])
            for case in cases
        )
        <= gates["maximum_gpu_pool_bytes"],
        "wall_time": wall_seconds <= gates["maximum_total_audit_seconds"],
    }


def run_multi_size_leaf_adjoint_audit(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_multi_size_leaf_adjoint_config(config)
    runtime = _validate_runtime(parsed)
    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    cases = []
    for hand_count in parsed["hands_per_player"]:
        for family in parsed["range_families"]:
            cases.append(
                _case(
                    parsed,
                    board=board,
                    hand_count=hand_count,
                    family=family,
                )
            )
    wall_seconds = time.perf_counter() - started
    gate_results = _gate_results(parsed, cases, wall_seconds)
    result = {
        "experiment": "multi-size-leaf-adjoint-audit-v1",
        "config_sha256": _sha256(config_path),
        "runtime": runtime,
        "environment": environment_metadata(),
        "cases": cases,
        "wall_seconds": wall_seconds,
        "gate_results": gate_results,
        "passed": all(gate_results.values()),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    arguments = parser.parse_args()
    result = run_multi_size_leaf_adjoint_audit(arguments.config, arguments.output)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
