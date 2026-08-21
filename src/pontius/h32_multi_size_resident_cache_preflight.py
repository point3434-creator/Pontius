"""Frozen h32 preflight for one-size and two-size resident terminal caches."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any, Mapping

import numpy as np

from .axis_public_cfr import AxisPublicCFRState
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .factorized_belief import FactorizedCardBelief
from .fresh_h32_strategy_transfer_audit import (
    _belief_digest,
    _build_target_belief,
    parse_fresh_h32_strategy_transfer_config,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .multi_size_leaf_adjoint import (
    build_multi_size_leaf_adjoint_terminal_automata,
    multi_size_leaf_adjoint_cfr_traverser,
    multi_size_terminal_groups,
)
from .multi_size_public_tree_tensor import MultiSizePublicTreeTensorEvaluator
from .multi_size_resident_leaf_adjoint_cfr import (
    MultiSizeResidentLeafAdjointPublicTreeCFR,
)
from .open_mode_audit import _open_workspace
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .public_policy_tt import _first_compatible_assignment
from .reporting import environment_metadata
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
from .river import HoleCards, parse_cards
from .river_multiway import MultiwayRiverDeal
from .river_multiway_multi_size import MultiwayMultiSizeRiverHoldem
from .showdown_value_rank_screen import _rank_codes
from .sparse_incidence_open_mode import SparseBidirectionalIncidence


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "h32-multi-size-resident-cache-preflight-v1.json"
)
_OUTPUT = (
    _ROOT
    / "experiments"
    / "results"
    / "h32-multi-size-resident-cache-preflight-v1.json"
)
_RESIDENT_PARENT = _ROOT / "experiments" / "results" / "h32-resident-cfr-audit-v2.json"
_RESIDENT_PARENT_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-resident-cfr-audit-v2.json"
)
_H32_CONFIG = (
    _ROOT / "experiments" / "configs" / "fresh-h32-strategy-transfer-audit-v1.json"
)
_MULTI_SIZE_PARENT = (
    _ROOT / "experiments" / "results" / "multi-size-leaf-adjoint-audit-v1.json"
)
_MULTI_SIZE_PARENT_CONFIG = (
    _ROOT / "experiments" / "configs" / "multi-size-leaf-adjoint-audit-v1.json"
)
_REQUIREMENTS = (
    _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
)
_IMPLEMENTATION = Path(__file__)
_SIZED_RESIDENT = (
    _ROOT / "src" / "pontius" / "multi_size_resident_leaf_adjoint_cfr.py"
)
_SIZED_LEAF = _ROOT / "src" / "pontius" / "multi_size_leaf_adjoint.py"
_SIZED_LAYOUT = _ROOT / "src" / "pontius" / "multi_size_public_tree_tensor.py"
_SIZED_GAME = _ROOT / "src" / "pontius" / "river_multiway_multi_size.py"
_RESIDENT_CONTRACTION = (
    _ROOT / "src" / "pontius" / "resident_heterogeneous_leaf_contraction.py"
)
_CUPY_INCIDENCE = _ROOT / "src" / "pontius" / "cupy_sparse_incidence.py"
_FRESH_H32_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "fresh_h32_strategy_transfer_audit.py"
)
_LADDER_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "leaf_adjoint_checkpoint_ladder_audit.py"
)

_CONFIG_FIELDS = {
    "evidence_stage",
    "expected_resident_parent_sha256",
    "expected_resident_parent_config_sha256",
    "expected_h32_config_sha256",
    "expected_multi_size_parent_sha256",
    "expected_multi_size_parent_config_sha256",
    "expected_requirements_sha256",
    "expected_audit_implementation_sha256",
    "expected_sized_resident_sha256",
    "expected_sized_leaf_sha256",
    "expected_sized_layout_sha256",
    "expected_sized_game_sha256",
    "expected_resident_contraction_sha256",
    "expected_cupy_incidence_sha256",
    "expected_fresh_h32_implementation_sha256",
    "expected_ladder_implementation_sha256",
    "board",
    "pot",
    "stack",
    "bet_sizes",
    "players",
    "hands_per_player",
    "range_families",
    "target_shifts",
    "target_order",
    "cache_arm_order_by_target",
    "warm_step_target",
    "warm_initialization",
    "warm_regret_mass_payoff_fraction",
    "solver_variant",
    "mixture_components",
    "split_index",
    "query_chunk_records",
    "maximum_feature_width_per_batch",
    "resident_lineage_maximum_pool_bytes",
    "resident_lineage_largest_persistent_bytes",
    "minimum_warm_noncache_reserve_bytes",
    "safe_headroom_rule",
    "unsafe_branch",
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


def parse_h32_multi_size_resident_cache_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the frozen action-width cache preflight."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("h32 multi-size cache config fields differ from ADR-0127")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0126_before_any_h32_two_size_resident_"
            "cache_byte_timing_pool_or_middle_rank_measurement"
        ),
        "board": ["4h", "6s", "Td", "Qh", "As"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_sizes": [3.0, 6.0],
        "players": 6,
        "hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "target_shifts": ["local_blocker_seat5_x2", "all_seat_strength_1_to2"],
        "target_order": [
            "balanced/local_blocker_seat5_x2",
            "balanced/all_seat_strength_1_to2",
            "blocker_heavy/local_blocker_seat5_x2",
            "blocker_heavy/all_seat_strength_1_to2",
        ],
        "cache_arm_order_by_target": [
            "one_then_two",
            "two_then_one",
            "two_then_one",
            "one_then_two",
        ],
        "warm_step_target": "balanced/local_blocker_seat5_x2",
        "warm_initialization": "uniform_positive_regret_mass_without_quality_read",
        "warm_regret_mass_payoff_fraction": 0.1,
        "solver_variant": "dcfr",
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 384,
        "resident_lineage_maximum_pool_bytes": 9_416_577_536,
        "resident_lineage_largest_persistent_bytes": 4_232_121_372,
        "minimum_warm_noncache_reserve_bytes": 5_184_456_164,
        "safe_headroom_rule": (
            "all_four_two_size_post_cache_pool_and_physical_headrooms_at_least_"
            "the_frozen_resident_lineage_noncache_reserve"
        ),
        "unsafe_branch": (
            "stop_before_any_h32_two_size_step_and_build_affine_shared_topology_cache"
        ),
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("h32 multi-size cache workload differs from ADR-0127")
    if (
        config["minimum_warm_noncache_reserve_bytes"]
        != config["resident_lineage_maximum_pool_bytes"]
        - config["resident_lineage_largest_persistent_bytes"]
    ):
        raise ValueError("h32 multi-size cache reserve arithmetic differs from ADR-0127")

    sources = {
        "expected_resident_parent_sha256": _RESIDENT_PARENT,
        "expected_resident_parent_config_sha256": _RESIDENT_PARENT_CONFIG,
        "expected_h32_config_sha256": _H32_CONFIG,
        "expected_multi_size_parent_sha256": _MULTI_SIZE_PARENT,
        "expected_multi_size_parent_config_sha256": _MULTI_SIZE_PARENT_CONFIG,
        "expected_requirements_sha256": _REQUIREMENTS,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
        "expected_sized_resident_sha256": _SIZED_RESIDENT,
        "expected_sized_leaf_sha256": _SIZED_LEAF,
        "expected_sized_layout_sha256": _SIZED_LAYOUT,
        "expected_sized_game_sha256": _SIZED_GAME,
        "expected_resident_contraction_sha256": _RESIDENT_CONTRACTION,
        "expected_cupy_incidence_sha256": _CUPY_INCIDENCE,
        "expected_fresh_h32_implementation_sha256": _FRESH_H32_IMPLEMENTATION,
        "expected_ladder_implementation_sha256": _LADDER_IMPLEMENTATION,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"h32 multi-size cache source hash mismatch: {field}")

    expected_gates = {
        "expected_small_control_regret_error": 2e-12,
        "expected_small_control_strategy_sum_error": 2e-12,
        "expected_target_rows": 4,
        "expected_one_size_public_nodes": 385,
        "expected_two_size_public_nodes": 763,
        "expected_one_size_terminal_groups": 64,
        "expected_two_size_terminal_groups": 127,
        "expected_one_size_automata": 384,
        "expected_two_size_automata": 762,
        "expected_distinct_transition_topologies_each": 378,
        "maximum_cache_compile_ms": 120000.0,
        "maximum_widened_step_ms": 120000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_total_audit_seconds": 1200.0,
        "require_clean_git_state": True,
        "require_target_identity": True,
        "require_maximum_middle_rank_identity": True,
        "require_conditional_single_widened_step": True,
        "require_no_strategy_quality_evaluation": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("h32 multi-size cache gates differ from ADR-0127")
    return {
        **config,
        "bet_sizes": tuple(config["bet_sizes"]),
        "range_families": tuple(config["range_families"]),
        "target_shifts": tuple(config["target_shifts"]),
        "target_order": tuple(config["target_order"]),
        "cache_arm_order_by_target": tuple(config["cache_arm_order_by_target"]),
        "gates": dict(config["gates"]),
    }


def _validate_runtime(parsed: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    import scipy

    cp, _ = _cupy_modules()
    runtime = int(cp.cuda.runtime.runtimeGetVersion())
    driver = int(cp.cuda.runtime.driverGetVersion())
    capability = str(cp.cuda.Device(0).compute_capability)
    if np.__version__ != parsed["required_numpy_version"]:
        raise RuntimeError("NumPy version differs from frozen cache preflight")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise RuntimeError("SciPy version differs from frozen cache preflight")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise RuntimeError("CuPy version differs from frozen cache preflight")
    if runtime != parsed["required_cuda_runtime_version"]:
        raise RuntimeError("CUDA runtime differs from frozen cache preflight")
    if driver < parsed["minimum_cuda_driver_version"]:
        raise RuntimeError("CUDA driver is below the frozen cache preflight floor")
    if capability != parsed["required_compute_capability"]:
        raise RuntimeError("GPU capability differs from frozen cache preflight")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise RuntimeError("frozen CUDA DLL directory is not configured")
    free, total = cp.cuda.runtime.memGetInfo()
    return cp, {
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "cupy": cp.__version__,
        "cuda_runtime": runtime,
        "cuda_driver": driver,
        "compute_capability": capability,
        "device_free_bytes_at_start": int(free),
        "device_total_bytes": int(total),
    }


def _representative_sized_tree(
    belief: FactorizedCardBelief,
    *,
    pot: float,
    stack: float,
    bet_sizes: tuple[float, ...],
) -> MultiSizePublicTreeTensorEvaluator:
    assignment = _first_compatible_assignment(belief)
    deal = MultiwayRiverDeal(
        tuple(
            belief.hands_by_player[seat][assignment[seat]]
            for seat in range(belief.num_players)
        )
    )
    game = MultiwayMultiSizeRiverHoldem.from_joint_weights(
        board=belief.board,
        pot=pot,
        stacks=(stack,) * belief.num_players,
        bet_sizes=bet_sizes,
        joint_weights={deal: 1.0},
    )
    return MultiSizePublicTreeTensorEvaluator(game)


def _table_error(
    left: Mapping[str, Mapping[Any, float]],
    right: Mapping[str, Mapping[Any, float]],
) -> float:
    if set(left) != set(right):
        raise ValueError("cache preflight accumulator schemas differ")
    maximum = 0.0
    for key in left:
        if set(left[key]) != set(right[key]):
            raise ValueError("cache preflight action schemas differ")
        maximum = max(
            maximum,
            *(abs(float(left[key][action]) - float(right[key][action])) for action in left[key]),
        )
    return maximum


def _small_control() -> dict[str, Any]:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    available = [card for card in range(52) if card not in set(board)]
    axes: list[tuple[HoleCards, ...]] = []
    cursor = 0
    for _ in range(6):
        cards = available[cursor : cursor + 4]
        cursor += 4
        axes.append(
            (
                tuple(sorted((cards[0], cards[1]))),
                tuple(sorted((cards[2], cards[3]))),
            )
        )
    hands = tuple(axes)
    belief = FactorizedCardBelief(
        hands_by_player=hands,
        mixture_weights=np.ones(1),
        unary_weights=tuple(np.ones((1, 2)) for _ in range(6)),
        board=board,
    )
    layout = _representative_sized_tree(
        belief, pot=12.0, stack=30.0, bet_sizes=(3.0, 6.0)
    )
    workspace, _ = _open_workspace(belief, split_index=3, query_chunk_records=256)
    sparse = SparseBidirectionalIncidence.compile(workspace)
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, hands)
    )
    automata = build_multi_size_leaf_adjoint_terminal_automata(
        layout, codes, pot=12.0
    )
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    belief_cache = CuPyResidentBeliefCache.compile(workspace)
    automaton_caches = tuple(
        CuPyResidentAutomatonCache.compile(
            workspace, automata[seat], target_seat=seat
        )
        for seat in range(6)
    )

    reference = AxisPublicCFRState(layout, hands, "dcfr")
    resident = MultiSizeResidentLeafAdjointPublicTreeCFR(
        layout,
        workspace,
        sparse,
        automata,
        "dcfr",
        belief_cache=belief_cache,
        automaton_caches=automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=96,
        hands_by_player=hands,
    )
    reference.warm_start({}, 2.5)
    resident.warm_start({}, 2.5)
    reference.iteration += 1
    for traverser in range(6):
        probabilities = reference.immutable_strategies()
        reference.accumulate_average_for_traverser(traverser, probabilities)
        result = multi_size_leaf_adjoint_cfr_traverser(
            layout,
            workspace,
            sparse,
            probabilities,
            automata[traverser],
            traverser=traverser,
            maximum_feature_width_per_batch=96,
            cupy_sparse=gpu,
        )
        reference.apply_regret_deltas(
            tuple((row.node_index, row.regret_deltas) for row in result.reads)
        )
    reference._discount_accumulators()
    resident.step()
    result = {
        "hands_per_player": 2,
        "public_nodes": layout.public_node_count,
        "terminal_groups": len(multi_size_terminal_groups(layout)),
        "regret_error": _table_error(reference.regret_table(), resident.regret_table()),
        "strategy_sum_error": _table_error(
            reference.strategy_sum_table(), resident.strategy_sum_table()
        ),
        "resident_iteration": resident.iteration,
        "resident_traversers": len(resident.last_step_work.traversers)
        if resident.last_step_work is not None
        else 0,
    }
    del resident, reference, automaton_caches, belief_cache, gpu
    gc.collect()
    release_cupy_memory_pool()
    return result


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


def _library_geometry(libraries: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    automata = tuple(value for library in libraries for value in library.values())
    return {
        "automata": len(automata),
        "distinct_transition_topologies": len(
            {_transition_digest(value) for value in automata}
        ),
        "maximum_state_rank": max(value.maximum_state_rank for value in automata),
        "numeric_bytes": sum(value.numeric_bytes for value in automata),
    }


def _compile_cache_arm(
    cp: Any,
    workspace: OpenModeFactorTTWorkspace,
    libraries: tuple[Mapping[str, Any], ...],
    *,
    pool_cap: int,
    reserve: int,
) -> tuple[dict[str, Any], Any, tuple[Any, ...]]:
    pool = cp.get_default_memory_pool()
    cp.cuda.runtime.deviceSynchronize()
    baseline_used = int(pool.used_bytes())
    baseline_total = int(pool.total_bytes())
    started = time.perf_counter()
    belief_cache = CuPyResidentBeliefCache.compile(workspace)
    automaton_caches = tuple(
        CuPyResidentAutomatonCache.compile(
            workspace, libraries[seat], target_seat=seat
        )
        for seat in range(len(libraries))
    )
    cp.cuda.runtime.deviceSynchronize()
    wall_ms = (time.perf_counter() - started) * 1000.0
    pool_used = int(pool.used_bytes())
    pool_total = int(pool.total_bytes())
    device_free, device_total = cp.cuda.runtime.memGetInfo()
    automaton_bytes = sum(cache.numeric_bytes for cache in automaton_caches)
    persistent_bytes = belief_cache.numeric_bytes + automaton_bytes
    row = {
        "compiled": True,
        "belief_numeric_bytes": belief_cache.numeric_bytes,
        "automaton_numeric_bytes": automaton_bytes,
        "persistent_numeric_bytes": persistent_bytes,
        "total_middle_rank": sum(cache.total_middle_rank for cache in automaton_caches),
        "maximum_middle_rank": max(
            cache.maximum_middle_rank for cache in automaton_caches
        ),
        "unique_automata": sum(cache.unique_automata for cache in automaton_caches),
        "belief_upload_ms": belief_cache.upload_ms,
        "automaton_half_prepare_ms": math.fsum(
            cache.half_prepare_ms for cache in automaton_caches
        ),
        "automaton_upload_ms": math.fsum(
            cache.upload_ms for cache in automaton_caches
        ),
        "cold_construction_ms": wall_ms,
        "pool_baseline_used_bytes": baseline_used,
        "pool_baseline_total_bytes": baseline_total,
        "pool_used_bytes": pool_used,
        "pool_total_bytes": pool_total,
        "pool_used_increase_bytes": pool_used - baseline_used,
        "pool_total_increase_bytes": pool_total - baseline_total,
        "pool_cap_headroom_bytes": pool_cap - pool_total,
        "physical_device_free_bytes": int(device_free),
        "physical_device_total_bytes": int(device_total),
        "physical_device_headroom_over_reserve_bytes": int(device_free) - reserve,
        "safe_for_warm_step": (
            pool_total <= pool_cap
            and pool_cap - pool_total >= reserve
            and int(device_free) >= reserve
        ),
        "per_seat": [
            {
                "seat": seat,
                "numeric_bytes": cache.numeric_bytes,
                "total_middle_rank": cache.total_middle_rank,
                "maximum_middle_rank": cache.maximum_middle_rank,
                "unique_automata": cache.unique_automata,
                "wall_ms": cache.wall_ms,
            }
            for seat, cache in enumerate(automaton_caches)
        ],
    }
    return row, belief_cache, automaton_caches


def _release_cache_objects(*objects: Any) -> None:
    del objects
    gc.collect()
    release_cupy_memory_pool()


def _parent_target(
    parent: dict[str, Any], family: str, shift: str
) -> dict[str, Any]:
    return next(
        row
        for row in parent["rerun"]["targets"]
        if row["range_family"] == family and row["target_shift"] == shift
    )


def _measure_target(
    *,
    parsed: dict[str, Any],
    cp: Any,
    parent: dict[str, Any],
    parent_config: dict[str, Any],
    board: tuple[int, ...],
    source_belief: Any,
    source_workspace: Any,
    sparse: SparseBidirectionalIncidence,
    gpu: CuPyBidirectionalIncidence,
    one_layout: Any,
    one_libraries: tuple[Mapping[str, Any], ...],
    sized_layout: MultiSizePublicTreeTensorEvaluator,
    sized_libraries: tuple[Mapping[str, Any], ...],
    family: str,
    shift: str,
    arm_order: str,
) -> dict[str, Any]:
    target_belief, descriptor = _build_target_belief(
        source_belief,
        board=board,
        shift=shift,
        local_blocker_target_seat=parent_config["local_blocker_target_seat"],
    )
    compile_started = time.perf_counter()
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        target_belief,
        query_chunk_records=parsed["query_chunk_records"],
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    workspace_ms = (time.perf_counter() - compile_started) * 1000.0
    expected = _parent_target(parent, family, shift)
    target_identity = (
        descriptor == expected["target_descriptor"]
        and _belief_digest(target_belief) == expected["target_belief_sha256"]
        and target_belief.hands_by_player == source_belief.hands_by_player
    )

    order = ("one_size", "two_size") if arm_order == "one_then_two" else (
        "two_size",
        "one_size",
    )
    libraries_by_arm = {
        "one_size": one_libraries,
        "two_size": sized_libraries,
    }
    rows: dict[str, dict[str, Any]] = {}
    for arm in order:
        gc.collect()
        release_cupy_memory_pool()
        row, belief_cache, automaton_caches = _compile_cache_arm(
            cp,
            workspace,
            libraries_by_arm[arm],
            pool_cap=parsed["gates"]["maximum_gpu_pool_bytes"],
            reserve=parsed["minimum_warm_noncache_reserve_bytes"],
        )
        rows[arm] = row
        del automaton_caches, belief_cache
        gc.collect()
        release_cupy_memory_pool()

    one = rows["one_size"]
    two = rows["two_size"]
    return {
        "range_family": family,
        "target_shift": shift,
        "arm_order": arm_order,
        "target_descriptor": descriptor,
        "target_belief_sha256": _belief_digest(target_belief),
        "target_identity": target_identity,
        "target_workspace_compile_ms": workspace_ms,
        "one_size": one,
        "two_size": two,
        "ratios": {
            "persistent_numeric_bytes": (
                two["persistent_numeric_bytes"] / one["persistent_numeric_bytes"]
            ),
            "automaton_numeric_bytes": (
                two["automaton_numeric_bytes"] / one["automaton_numeric_bytes"]
            ),
            "total_middle_rank": two["total_middle_rank"] / one["total_middle_rank"],
            "cold_construction_ms": (
                two["cold_construction_ms"] / one["cold_construction_ms"]
            ),
        },
        "one_size_incumbent_step_ms": expected["resident"]["steps"][0]["wall_ms"],
    }


def _run_conditional_warm_step(
    *,
    parsed: dict[str, Any],
    parent_config: dict[str, Any],
    board: tuple[int, ...],
) -> dict[str, Any]:
    family, shift = parsed["warm_step_target"].split("/", maxsplit=1)
    source_belief, _, sparse, retained = _build_case(
        parsed=parent_config,
        board=board,
        hand_count=parsed["hands_per_player"],
        family=family,
    )
    source_workspace, _, _ = retained
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, source_belief.hands_by_player)
    )
    layout = _representative_sized_tree(
        source_belief,
        pot=parsed["pot"],
        stack=parsed["stack"],
        bet_sizes=parsed["bet_sizes"],
    )
    libraries = build_multi_size_leaf_adjoint_terminal_automata(
        layout, codes, pot=parsed["pot"]
    )
    target_belief, _ = _build_target_belief(
        source_belief,
        board=board,
        shift=shift,
        local_blocker_target_seat=parent_config["local_blocker_target_seat"],
    )
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        target_belief,
        query_chunk_records=parsed["query_chunk_records"],
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    cp, _ = _cupy_modules()
    cache, belief_cache, automaton_caches = _compile_cache_arm(
        cp,
        workspace,
        libraries,
        pool_cap=parsed["gates"]["maximum_gpu_pool_bytes"],
        reserve=parsed["minimum_warm_noncache_reserve_bytes"],
    )
    solver = MultiSizeResidentLeafAdjointPublicTreeCFR(
        layout,
        workspace,
        sparse,
        libraries,
        parsed["solver_variant"],
        belief_cache=belief_cache,
        automaton_caches=automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
        hands_by_player=target_belief.hands_by_player,
    )
    mass = parsed["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span)
    solver.warm_start({}, mass)
    started = time.perf_counter()
    solver.step()
    wall_ms = (time.perf_counter() - started) * 1000.0
    if solver.last_step_work is None:
        raise AssertionError("conditional widened step has no work telemetry")
    work = solver.last_step_work
    row = {
        "target": parsed["warm_step_target"],
        "initialization": parsed["warm_initialization"],
        "regret_mass": mass,
        "iteration": solver.iteration,
        "wall_ms": wall_ms,
        "reported_wall_ms": work.wall_ms,
        "terminal_contraction_ms": work.terminal_contraction_ms,
        "traversers": len(work.traversers),
        "terminal_contractions": sum(
            item.terminal_contractions for item in work.traversers
        ),
        "terminal_sparse_batches": sum(
            item.terminal_sparse_batches for item in work.traversers
        ),
        "maximum_gpu_pool_bytes": max(
            item.maximum_gpu_pool_total_bytes for item in work.traversers
        ),
        "maximum_middle_rank": max(
            item.maximum_terminal_middle_rank for item in work.traversers
        ),
        "cache_rebuild": cache,
        "strategy_quality_evaluations": 0,
    }
    del solver, automaton_caches, belief_cache, gpu
    gc.collect()
    release_cupy_memory_pool()
    return row


def run_h32_multi_size_resident_cache_preflight(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the frozen cache-only comparison and its conditional branch."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_multi_size_resident_cache_config(config)
    cp, runtime = _validate_runtime(parsed)
    environment = environment_metadata()
    started = time.perf_counter()

    parent_config = parse_fresh_h32_strategy_transfer_config(
        json.loads(_H32_CONFIG.read_text(encoding="utf-8"))
    )
    parent = json.loads(_RESIDENT_PARENT.read_text(encoding="utf-8"))
    sized_parent = json.loads(_MULTI_SIZE_PARENT.read_text(encoding="utf-8"))
    parent_identity = (
        parent.get("status") == "frozen_successor_audit_executed"
        and bool(parent.get("gates", {}).get("passed"))
        and parent.get("config_sha256") == _sha256(_RESIDENT_PARENT_CONFIG)
        and bool(sized_parent.get("passed"))
        and sized_parent.get("config_sha256") == _sha256(_MULTI_SIZE_PARENT_CONFIG)
    )
    if not parent_identity:
        raise ValueError("h32 multi-size cache parent identity rejected")

    small = _small_control()
    small_passed = (
        small["regret_error"]
        <= parsed["gates"]["expected_small_control_regret_error"]
        and small["strategy_sum_error"]
        <= parsed["gates"]["expected_small_control_strategy_sum_error"]
        and small["public_nodes"] == parsed["gates"]["expected_two_size_public_nodes"]
        and small["terminal_groups"]
        == parsed["gates"]["expected_two_size_terminal_groups"]
        and small["resident_iteration"] == 1
        and small["resident_traversers"] == parsed["players"]
    )
    if not small_passed:
        raise ValueError("small resident action-width control failed before h32")

    board = parse_cards(*parsed["board"])
    targets = []
    family_geometry = []
    target_index = 0
    for family in parsed["range_families"]:
        gc.collect()
        release_cupy_memory_pool()
        source_belief, one_layout, sparse, retained = _build_case(
            parsed=parent_config,
            board=board,
            hand_count=parsed["hands_per_player"],
            family=family,
        )
        source_workspace, _, one_libraries = retained
        codes = tuple(
            np.ascontiguousarray(values, dtype=np.int32)
            for values in _rank_codes(board, source_belief.hands_by_player)
        )
        sized_layout = _representative_sized_tree(
            source_belief,
            pot=parsed["pot"],
            stack=parsed["stack"],
            bet_sizes=parsed["bet_sizes"],
        )
        automata_started = time.perf_counter()
        sized_libraries = build_multi_size_leaf_adjoint_terminal_automata(
            sized_layout, codes, pot=parsed["pot"]
        )
        sized_automata_ms = (time.perf_counter() - automata_started) * 1000.0
        one_geometry = _library_geometry(one_libraries)
        sized_geometry = _library_geometry(sized_libraries)
        family_geometry.append(
            {
                "range_family": family,
                "one_size_public_nodes": one_layout.public_node_count,
                "two_size_public_nodes": sized_layout.public_node_count,
                "one_size_terminal_groups": 64,
                "two_size_terminal_groups": len(multi_size_terminal_groups(sized_layout)),
                "one_size_automata": one_geometry,
                "two_size_automata": sized_geometry,
                "two_size_automata_compile_ms": sized_automata_ms,
            }
        )
        gpu = CuPyBidirectionalIncidence.compile(sparse)
        for shift in parsed["target_shifts"]:
            targets.append(
                _measure_target(
                    parsed=parsed,
                    cp=cp,
                    parent=parent,
                    parent_config=parent_config,
                    board=board,
                    source_belief=source_belief,
                    source_workspace=source_workspace,
                    sparse=sparse,
                    gpu=gpu,
                    one_layout=one_layout,
                    one_libraries=one_libraries,
                    sized_layout=sized_layout,
                    sized_libraries=sized_libraries,
                    family=family,
                    shift=shift,
                    arm_order=parsed["cache_arm_order_by_target"][target_index],
                )
            )
            target_index += 1
        del gpu
        gc.collect()
        release_cupy_memory_pool()

    actual_order = tuple(
        f"{row['range_family']}/{row['target_shift']}" for row in targets
    )
    raw_headroom_safe = all(row["two_size"]["safe_for_warm_step"] for row in targets)
    warm_step = (
        _run_conditional_warm_step(
            parsed=parsed, parent_config=parent_config, board=board
        )
        if raw_headroom_safe
        else None
    )
    decision = (
        "one_widened_resident_warm_step_executed"
        if raw_headroom_safe
        else parsed["unsafe_branch"]
    )
    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    geometry_rows = family_geometry
    gate_results = {
        "parent_identity": parent_identity,
        "clean_git_state": (not bool(environment["git"]["dirty"]))
        == gates["require_clean_git_state"],
        "small_control": small_passed,
        "target_count_and_order": (
            len(targets) == gates["expected_target_rows"]
            and actual_order == parsed["target_order"]
        ),
        "target_identity": all(row["target_identity"] for row in targets)
        == gates["require_target_identity"],
        "public_topology": all(
            row["one_size_public_nodes"] == gates["expected_one_size_public_nodes"]
            and row["two_size_public_nodes"] == gates["expected_two_size_public_nodes"]
            and row["one_size_terminal_groups"]
            == gates["expected_one_size_terminal_groups"]
            and row["two_size_terminal_groups"]
            == gates["expected_two_size_terminal_groups"]
            for row in geometry_rows
        ),
        "automaton_counts": all(
            row["one_size_automata"]["automata"] == gates["expected_one_size_automata"]
            and row["two_size_automata"]["automata"]
            == gates["expected_two_size_automata"]
            for row in geometry_rows
        ),
        "transition_topology_identity": all(
            row["one_size_automata"]["distinct_transition_topologies"]
            == gates["expected_distinct_transition_topologies_each"]
            and row["two_size_automata"]["distinct_transition_topologies"]
            == gates["expected_distinct_transition_topologies_each"]
            for row in geometry_rows
        ),
        "maximum_middle_rank_identity": all(
            row["one_size"]["maximum_middle_rank"]
            == row["two_size"]["maximum_middle_rank"]
            for row in targets
        )
        == gates["require_maximum_middle_rank_identity"],
        "cache_construction": all(
            row[arm]["compiled"]
            and row[arm]["cold_construction_ms"] <= gates["maximum_cache_compile_ms"]
            for row in targets
            for arm in ("one_size", "two_size")
        ),
        "cache_pool_ceiling": all(
            row[arm]["pool_total_bytes"] <= gates["maximum_gpu_pool_bytes"]
            for row in targets
            for arm in ("one_size", "two_size")
        ),
        "conditional_single_widened_step": (
            (warm_step is not None) == raw_headroom_safe
            and (warm_step is None or warm_step["iteration"] == 1)
        )
        == gates["require_conditional_single_widened_step"],
        "widened_step_resources": (
            warm_step is None
            or (
                warm_step["wall_ms"] <= gates["maximum_widened_step_ms"]
                and warm_step["maximum_gpu_pool_bytes"]
                <= gates["maximum_gpu_pool_bytes"]
                and warm_step["traversers"] == parsed["players"]
                and warm_step["terminal_contractions"]
                == parsed["players"] * 385
            )
        ),
        "no_strategy_quality_evaluation": (
            (0 if warm_step is None else warm_step["strategy_quality_evaluations"])
            == 0
        )
        == gates["require_no_strategy_quality_evaluation"],
        "wall_time": total_seconds <= gates["maximum_total_audit_seconds"],
    }
    passed = all(gate_results.values())
    result = {
        "schema_version": 1,
        "status": "frozen_preflight_executed",
        "experiment_type": "h32_one_vs_two_size_resident_cache_preflight",
        "config": config,
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {
            field.removeprefix("expected_"): config[field]
            for field in config
            if field.startswith("expected_") and field.endswith("_sha256")
        },
        "environment": {**environment, **runtime},
        "small_control": small,
        "family_geometry": family_geometry,
        "targets": targets,
        "headroom": {
            "pool_ceiling_bytes": gates["maximum_gpu_pool_bytes"],
            "frozen_noncache_reserve_bytes": parsed[
                "minimum_warm_noncache_reserve_bytes"
            ],
            "minimum_two_size_pool_cap_headroom_bytes": min(
                row["two_size"]["pool_cap_headroom_bytes"] for row in targets
            ),
            "minimum_two_size_physical_device_free_bytes": min(
                row["two_size"]["physical_device_free_bytes"] for row in targets
            ),
            "raw_cache_headroom_safe": raw_headroom_safe,
            "rule": parsed["safe_headroom_rule"],
        },
        "warm_step": warm_step,
        "decision": decision,
        "gate_results": gate_results,
        "passed": passed,
        "timing": {"total_seconds": total_seconds},
        "strategy_quality_claim": None,
        "limitations": [
            "This is a systems preflight on one board and four constructed h32 target beliefs.",
            "Persistent numeric bytes exclude Python objects and allocator metadata.",
            "Cold construction includes belief and six target-seat caches but excludes shared sparse-operator compilation.",
            "The conditional widened step uses a uniform positive-mass warm start and produces no quality evaluation.",
            "No result selects a bet size, blueprint, solver horizon, or deployment strategy.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    arguments = parser.parse_args()
    result = run_h32_multi_size_resident_cache_preflight(
        arguments.config, arguments.output
    )
    print(
        "h32 multi-size resident cache preflight: "
        f"passed={result['passed']}, decision={result['decision']}, "
        f"wall={result['timing']['total_seconds']:.3f}s"
    )


if __name__ == "__main__":
    main()
