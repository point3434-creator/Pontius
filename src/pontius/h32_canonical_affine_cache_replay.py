"""Frozen zero-step h32 replay for scale-canonical affine cache identity."""

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

from .canonical_affine_resident_automaton_cache import (
    CuPyCanonicalAffineResidentAutomatonCache,
    canonical_affine_basis_digest,
)
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
from .h32_affine_resident_cache_preflight import (
    _representative_sized_tree,
    _strict_git_metadata,
    _table_error,
    _validate_runtime,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .multi_size_affine_resident_leaf_adjoint_cfr import (
    MultiSizeAffineResidentLeafAdjointPublicTreeCFR,
)
from .multi_size_leaf_adjoint import (
    build_multi_size_leaf_adjoint_terminal_automata,
    multi_size_terminal_groups,
)
from .multi_size_resident_leaf_adjoint_cfr import (
    MultiSizeResidentLeafAdjointPublicTreeCFR,
)
from .open_mode_audit import _open_workspace
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .reporting import environment_metadata
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
from .river import HoleCards, parse_cards
from .showdown_value_rank_screen import _rank_codes
from .sparse_incidence_open_mode import SparseBidirectionalIncidence
from .structured_showdown_automaton import build_structured_showdown_automaton


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "h32-canonical-affine-cache-replay-v1.json"
)
_OUTPUT = (
    _ROOT
    / "experiments"
    / "results"
    / "h32-canonical-affine-cache-replay-v1.json"
)
_FAILED_PARENT = (
    _ROOT
    / "experiments"
    / "results"
    / "h32-affine-resident-cache-preflight-v1.json"
)
_FAILED_PARENT_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "h32-affine-resident-cache-preflight-v1.json"
)
_H32_CONFIG = (
    _ROOT / "experiments" / "configs" / "fresh-h32-strategy-transfer-audit-v1.json"
)
_REQUIREMENTS = (
    _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
)
_IMPLEMENTATION = Path(__file__)
_CANONICAL_CACHE = (
    _ROOT / "src" / "pontius" / "canonical_affine_resident_automaton_cache.py"
)
_AFFINE_CONTRACTION = (
    _ROOT / "src" / "pontius" / "affine_resident_heterogeneous_leaf_contraction.py"
)
_AFFINE_CFR = (
    _ROOT / "src" / "pontius" / "multi_size_affine_resident_leaf_adjoint_cfr.py"
)
_RAW_SIZED_RESIDENT = (
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
_FAILED_PREFLIGHT_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "h32_affine_resident_cache_preflight.py"
)

_CONFIG_FIELDS = {
    "evidence_stage",
    "expected_failed_parent_sha256",
    "expected_failed_parent_config_sha256",
    "expected_h32_config_sha256",
    "expected_requirements_sha256",
    "expected_audit_implementation_sha256",
    "expected_canonical_cache_sha256",
    "expected_affine_contraction_sha256",
    "expected_affine_cfr_sha256",
    "expected_raw_sized_resident_sha256",
    "expected_sized_leaf_sha256",
    "expected_sized_layout_sha256",
    "expected_sized_game_sha256",
    "expected_resident_contraction_sha256",
    "expected_cupy_incidence_sha256",
    "expected_fresh_h32_implementation_sha256",
    "expected_ladder_implementation_sha256",
    "expected_failed_preflight_implementation_sha256",
    "board",
    "pot",
    "stack",
    "bet_sizes",
    "expected_two_size_payoff_span",
    "players",
    "hands_per_player",
    "range_families",
    "target_shifts",
    "target_order",
    "mixture_components",
    "split_index",
    "query_chunk_records",
    "maximum_feature_width_per_batch",
    "resident_lineage_maximum_pool_bytes",
    "resident_lineage_largest_persistent_bytes",
    "minimum_warm_noncache_reserve_bytes",
    "headroom_rule",
    "zero_step_rule",
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


def parse_h32_canonical_affine_cache_replay_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the frozen scale-canonical cache-only replay."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("h32 canonical affine config fields differ from ADR-0131")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0130_before_any_h32_scale_canonical_affine_"
            "cache_byte_timing_pool_or_stored_rank_measurement"
        ),
        "board": ["4h", "6s", "Td", "Qh", "As"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_sizes": [3.0, 6.0],
        "expected_two_size_payoff_span": 48.0,
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
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 384,
        "resident_lineage_maximum_pool_bytes": 9_416_577_536,
        "resident_lineage_largest_persistent_bytes": 4_232_121_372,
        "minimum_warm_noncache_reserve_bytes": 5_184_456_164,
        "headroom_rule": (
            "report_the_unchanged_all_four_pool_and_physical_reserve_rule_"
            "without_authorizing_arithmetic"
        ),
        "zero_step_rule": (
            "execute_zero_h32_steps_under_every_outcome_because_the_single_"
            "widened_step_allowance_was_spent_in_adr0130"
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
        raise ValueError("h32 canonical affine workload differs from ADR-0131")
    if (
        config["minimum_warm_noncache_reserve_bytes"]
        != config["resident_lineage_maximum_pool_bytes"]
        - config["resident_lineage_largest_persistent_bytes"]
    ):
        raise ValueError("h32 canonical affine reserve differs from ADR-0131")

    sources = {
        "expected_failed_parent_sha256": _FAILED_PARENT,
        "expected_failed_parent_config_sha256": _FAILED_PARENT_CONFIG,
        "expected_h32_config_sha256": _H32_CONFIG,
        "expected_requirements_sha256": _REQUIREMENTS,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
        "expected_canonical_cache_sha256": _CANONICAL_CACHE,
        "expected_affine_contraction_sha256": _AFFINE_CONTRACTION,
        "expected_affine_cfr_sha256": _AFFINE_CFR,
        "expected_raw_sized_resident_sha256": _RAW_SIZED_RESIDENT,
        "expected_sized_leaf_sha256": _SIZED_LEAF,
        "expected_sized_layout_sha256": _SIZED_LAYOUT,
        "expected_sized_game_sha256": _SIZED_GAME,
        "expected_resident_contraction_sha256": _RESIDENT_CONTRACTION,
        "expected_cupy_incidence_sha256": _CUPY_INCIDENCE,
        "expected_fresh_h32_implementation_sha256": _FRESH_H32_IMPLEMENTATION,
        "expected_ladder_implementation_sha256": _LADDER_IMPLEMENTATION,
        "expected_failed_preflight_implementation_sha256": (
            _FAILED_PREFLIGHT_IMPLEMENTATION
        ),
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"h32 canonical affine source hash mismatch: {field}")

    expected_gates = {
        "expected_small_control_regret_error": 2e-12,
        "expected_small_control_strategy_sum_error": 2e-12,
        "expected_target_rows": 4,
        "expected_two_size_public_nodes": 763,
        "expected_two_size_terminal_groups": 127,
        "expected_two_size_automata": 762,
        "expected_shared_affine_bases": 378,
        "expected_failed_parent_affine_bases": 384,
        "maximum_cache_compile_ms": 120000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_total_audit_seconds": 1200.0,
        "require_clean_git_state": True,
        "require_target_identity": True,
        "require_payoff_span_identity": True,
        "require_raw_equivalent_byte_identity": True,
        "require_storage_below_failed_parent": True,
        "require_zero_h32_steps": True,
        "require_no_strategy_quality_evaluation": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("h32 canonical affine gates differ from ADR-0131")
    return {
        **config,
        "bet_sizes": tuple(config["bet_sizes"]),
        "range_families": tuple(config["range_families"]),
        "target_shifts": tuple(config["target_shifts"]),
        "target_order": tuple(config["target_order"]),
        "gates": dict(config["gates"]),
    }


def _five_way_scale_control() -> dict[str, Any]:
    strengths = (
        *(np.asarray([1, 2], dtype=np.int32) for _ in range(5)),
        np.asarray([0, 2], dtype=np.int32),
    )
    common = {
        "strength_codes": strengths,
        "contenders": (0, 1, 2, 3, 4, 5),
        "target_player": 0,
        "pot": 12.0,
    }
    family = (
        build_structured_showdown_automaton(
            **common,
            contributed=False,
            bet_size=0.0,
        ),
        build_structured_showdown_automaton(
            **common,
            contributed=True,
            bet_size=3.0,
        ),
        build_structured_showdown_automaton(
            **common,
            contributed=True,
            bet_size=6.0,
        ),
    )
    changed = build_structured_showdown_automaton(
        strength_codes=(*strengths[:-1], np.asarray([2, 0], dtype=np.int32)),
        contenders=(0, 1, 2, 3, 4, 5),
        target_player=0,
        contributed=True,
        pot=12.0,
        bet_size=6.0,
    )
    digests = tuple(canonical_affine_basis_digest(row) for row in family)
    return {
        "final_pots": tuple(row.final_pot for row in family),
        "scale_family_digest_count": len(set(digests)),
        "changed_final_mode_is_distinct": (
            canonical_affine_basis_digest(changed) != digests[-1]
        ),
    }


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
        belief,
        pot=12.0,
        stack=30.0,
        bet_sizes=(3.0, 6.0),
    )
    workspace, _ = _open_workspace(
        belief,
        split_index=3,
        query_chunk_records=256,
    )
    sparse = SparseBidirectionalIncidence.compile(workspace)
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, hands)
    )
    automata = build_multi_size_leaf_adjoint_terminal_automata(
        layout,
        codes,
        pot=12.0,
    )
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    belief_cache = CuPyResidentBeliefCache.compile(workspace)
    raw_caches = tuple(
        CuPyResidentAutomatonCache.compile(
            workspace,
            automata[seat],
            target_seat=seat,
        )
        for seat in range(6)
    )
    canonical_caches = tuple(
        CuPyCanonicalAffineResidentAutomatonCache.compile(
            workspace,
            automata[seat],
            target_seat=seat,
        )
        for seat in range(6)
    )
    raw = MultiSizeResidentLeafAdjointPublicTreeCFR(
        layout,
        workspace,
        sparse,
        automata,
        "dcfr",
        belief_cache=belief_cache,
        automaton_caches=raw_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=96,
        hands_by_player=hands,
    )
    canonical = MultiSizeAffineResidentLeafAdjointPublicTreeCFR(
        layout,
        workspace,
        sparse,
        automata,
        "dcfr",
        belief_cache=belief_cache,
        automaton_caches=canonical_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=96,
        hands_by_player=hands,
    )
    raw.warm_start({}, 2.5)
    canonical.warm_start({}, 2.5)
    raw.step()
    canonical.step()
    result = {
        "hands_per_player": 2,
        "public_nodes": layout.public_node_count,
        "terminal_groups": len(multi_size_terminal_groups(layout)),
        "game_payoff_span": float(layout.game.payoff_span),
        "regret_error": _table_error(raw.regret_table(), canonical.regret_table()),
        "strategy_sum_error": _table_error(
            raw.strategy_sum_table(),
            canonical.strategy_sum_table(),
        ),
        "raw_automaton_numeric_bytes": sum(
            cache.numeric_bytes for cache in raw_caches
        ),
        "canonical_automaton_numeric_bytes": sum(
            cache.numeric_bytes for cache in canonical_caches
        ),
        "raw_equivalent_numeric_bytes": sum(
            cache.raw_equivalent_numeric_bytes for cache in canonical_caches
        ),
        "logical_automata": sum(
            cache.unique_automata for cache in canonical_caches
        ),
        "shared_affine_bases": sum(
            cache.shared_topologies for cache in canonical_caches
        ),
        "raw_iteration": raw.iteration,
        "canonical_iteration": canonical.iteration,
        "five_way_scale_control": _five_way_scale_control(),
    }
    del canonical, raw, canonical_caches, raw_caches, belief_cache, gpu
    gc.collect()
    release_cupy_memory_pool()
    return result


def _failed_target(
    parent: dict[str, Any],
    family: str,
    shift: str,
) -> dict[str, Any]:
    return next(
        row
        for row in parent["targets"]
        if row["range_family"] == family and row["target_shift"] == shift
    )


def _compile_canonical_cache(
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
    caches = tuple(
        CuPyCanonicalAffineResidentAutomatonCache.compile(
            workspace,
            libraries[seat],
            target_seat=seat,
        )
        for seat in range(len(libraries))
    )
    cp.cuda.runtime.deviceSynchronize()
    wall_ms = (time.perf_counter() - started) * 1000.0
    pool_used = int(pool.used_bytes())
    pool_total = int(pool.total_bytes())
    device_free, device_total = cp.cuda.runtime.memGetInfo()
    basis_bytes = sum(cache.basis_numeric_bytes for cache in caches)
    coefficient_bytes = sum(cache.coefficient_numeric_bytes for cache in caches)
    automaton_bytes = sum(cache.numeric_bytes for cache in caches)
    raw_equivalent_bytes = sum(cache.raw_equivalent_numeric_bytes for cache in caches)
    return (
        {
            "compiled": True,
            "belief_numeric_bytes": belief_cache.numeric_bytes,
            "basis_numeric_bytes": basis_bytes,
            "coefficient_numeric_bytes": coefficient_bytes,
            "automaton_numeric_bytes": automaton_bytes,
            "raw_equivalent_automaton_numeric_bytes": raw_equivalent_bytes,
            "persistent_numeric_bytes": belief_cache.numeric_bytes + automaton_bytes,
            "total_logical_middle_rank": sum(cache.total_middle_rank for cache in caches),
            "stored_topology_middle_rank": sum(
                cache.stored_topology_middle_rank for cache in caches
            ),
            "maximum_middle_rank": max(cache.maximum_middle_rank for cache in caches),
            "logical_automata": sum(cache.unique_automata for cache in caches),
            "shared_affine_bases": sum(cache.shared_topologies for cache in caches),
            "belief_upload_ms": belief_cache.upload_ms,
            "automaton_half_prepare_ms": math.fsum(
                cache.half_prepare_ms for cache in caches
            ),
            "automaton_upload_ms": math.fsum(cache.upload_ms for cache in caches),
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
            "safe_under_prior_rule": (
                pool_total <= pool_cap
                and pool_cap - pool_total >= reserve
                and int(device_free) >= reserve
            ),
            "per_seat": [
                {
                    "seat": seat,
                    "basis_numeric_bytes": cache.basis_numeric_bytes,
                    "coefficient_numeric_bytes": cache.coefficient_numeric_bytes,
                    "numeric_bytes": cache.numeric_bytes,
                    "raw_equivalent_numeric_bytes": cache.raw_equivalent_numeric_bytes,
                    "total_logical_middle_rank": cache.total_middle_rank,
                    "stored_topology_middle_rank": cache.stored_topology_middle_rank,
                    "maximum_middle_rank": cache.maximum_middle_rank,
                    "logical_automata": cache.unique_automata,
                    "shared_affine_bases": cache.shared_topologies,
                    "wall_ms": cache.wall_ms,
                }
                for seat, cache in enumerate(caches)
            ],
        },
        belief_cache,
        caches,
    )


def _measure_target(
    *,
    parsed: dict[str, Any],
    cp: Any,
    parent: dict[str, Any],
    parent_config: dict[str, Any],
    board: tuple[int, ...],
    source_belief: FactorizedCardBelief,
    source_workspace: OpenModeFactorTTWorkspace,
    libraries: tuple[Mapping[str, Any], ...],
    family: str,
    shift: str,
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
    failed = _failed_target(parent, family, shift)
    identity = (
        descriptor == failed["target_descriptor"]
        and _belief_digest(target_belief) == failed["target_belief_sha256"]
        and target_belief.hands_by_player == source_belief.hands_by_player
    )
    gc.collect()
    release_cupy_memory_pool()
    cache, belief_cache, caches = _compile_canonical_cache(
        cp,
        workspace,
        libraries,
        pool_cap=parsed["gates"]["maximum_gpu_pool_bytes"],
        reserve=parsed["minimum_warm_noncache_reserve_bytes"],
    )
    raw = failed["raw_two_size_reference"]
    prior = failed["affine"]
    result = {
        "range_family": family,
        "target_shift": shift,
        "target_descriptor": descriptor,
        "target_belief_sha256": _belief_digest(target_belief),
        "target_identity": identity,
        "target_workspace_compile_ms": workspace_ms,
        "canonical": cache,
        "raw_two_size_reference": raw,
        "failed_float_digest_reference": {
            "persistent_numeric_bytes": prior["persistent_numeric_bytes"],
            "automaton_numeric_bytes": prior["automaton_numeric_bytes"],
            "basis_numeric_bytes": prior["basis_numeric_bytes"],
            "stored_topology_middle_rank": prior["stored_topology_middle_rank"],
            "shared_affine_bases": prior["shared_affine_bases"],
            "cold_construction_ms": prior["cold_construction_ms"],
        },
        "ratios": {
            "persistent_to_raw_two_size": (
                cache["persistent_numeric_bytes"] / raw["persistent_numeric_bytes"]
            ),
            "persistent_to_failed_float_digest": (
                cache["persistent_numeric_bytes"] / prior["persistent_numeric_bytes"]
            ),
            "stored_to_logical_middle_rank": (
                cache["stored_topology_middle_rank"]
                / cache["total_logical_middle_rank"]
            ),
            "cold_to_failed_float_digest": (
                cache["cold_construction_ms"] / prior["cold_construction_ms"]
            ),
        },
    }
    del caches, belief_cache
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_canonical_affine_cache_replay(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Run the frozen canonical cache-only h32 replay with zero steps."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_canonical_affine_cache_replay_config(config)
    cp, runtime = _validate_runtime(parsed)
    environment = environment_metadata()
    environment["git"] = _strict_git_metadata()
    started = time.perf_counter()

    parent = json.loads(_FAILED_PARENT.read_text(encoding="utf-8"))
    parent_config = parse_fresh_h32_strategy_transfer_config(
        json.loads(_H32_CONFIG.read_text(encoding="utf-8"))
    )
    failed_gates = tuple(
        key for key, value in parent.get("gate_results", {}).items() if not value
    )
    parent_identity = (
        parent.get("passed") is False
        and parent.get("config_sha256") == _sha256(_FAILED_PARENT_CONFIG)
        and failed_gates == ("automaton_and_basis_counts",)
        and parent.get("warm_step", {}).get("executed") is True
        and parent.get("warm_step", {}).get("iteration") == 1
        and parent.get("strategy_quality_claim") is None
    )
    if not parent_identity:
        raise ValueError("h32 canonical affine failed-parent identity rejected")

    small = _small_control()
    scale = small["five_way_scale_control"]
    small_passed = (
        small["regret_error"]
        <= parsed["gates"]["expected_small_control_regret_error"]
        and small["strategy_sum_error"]
        <= parsed["gates"]["expected_small_control_strategy_sum_error"]
        and small["public_nodes"]
        == parsed["gates"]["expected_two_size_public_nodes"]
        and small["terminal_groups"]
        == parsed["gates"]["expected_two_size_terminal_groups"]
        and small["game_payoff_span"] == parsed["expected_two_size_payoff_span"]
        and small["logical_automata"]
        == parsed["gates"]["expected_two_size_automata"]
        and small["shared_affine_bases"]
        == parsed["gates"]["expected_shared_affine_bases"]
        and small["raw_equivalent_numeric_bytes"]
        == small["raw_automaton_numeric_bytes"]
        and small["canonical_automaton_numeric_bytes"]
        < small["raw_automaton_numeric_bytes"]
        and small["raw_iteration"] == 1
        and small["canonical_iteration"] == 1
        and scale == {
            "final_pots": (12.0, 30.0, 48.0),
            "scale_family_digest_count": 1,
            "changed_final_mode_is_distinct": True,
        }
    )
    if not small_passed:
        raise ValueError("small canonical affine control failed before h32")

    board = parse_cards(*parsed["board"])
    targets = []
    family_geometry = []
    for family in parsed["range_families"]:
        gc.collect()
        release_cupy_memory_pool()
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
        payoff_span = float(layout.game.payoff_span)
        automata_started = time.perf_counter()
        libraries = build_multi_size_leaf_adjoint_terminal_automata(
            layout,
            codes,
            pot=parsed["pot"],
        )
        automata_ms = (time.perf_counter() - automata_started) * 1000.0
        automata = tuple(value for library in libraries for value in library.values())
        family_geometry.append(
            {
                "range_family": family,
                "two_size_public_nodes": layout.public_node_count,
                "two_size_terminal_groups": len(multi_size_terminal_groups(layout)),
                "two_size_payoff_span": payoff_span,
                "payoff_span_source": "layout.game.payoff_span",
                "two_size_automata": len(automata),
                "distinct_canonical_affine_identities": len(
                    {canonical_affine_basis_digest(value) for value in automata}
                ),
                "automata_compile_ms": automata_ms,
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
                    libraries=libraries,
                    family=family,
                    shift=shift,
                )
            )
        del gpu
        gc.collect()
        release_cupy_memory_pool()

    actual_order = tuple(
        f"{row['range_family']}/{row['target_shift']}" for row in targets
    )
    prior_rule_safe = all(row["canonical"]["safe_under_prior_rule"] for row in targets)
    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    h32_steps_executed = 0
    strategy_quality_evaluations = 0
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
            row["two_size_public_nodes"] == gates["expected_two_size_public_nodes"]
            and row["two_size_terminal_groups"]
            == gates["expected_two_size_terminal_groups"]
            for row in family_geometry
        ),
        "payoff_span_identity": all(
            row["two_size_payoff_span"] == parsed["expected_two_size_payoff_span"]
            for row in family_geometry
        )
        == gates["require_payoff_span_identity"],
        "automaton_and_basis_counts": all(
            row["two_size_automata"] == gates["expected_two_size_automata"]
            and row["distinct_canonical_affine_identities"]
            == gates["expected_shared_affine_bases"]
            for row in family_geometry
        )
        and all(
            row["canonical"]["logical_automata"]
            == gates["expected_two_size_automata"]
            and row["canonical"]["shared_affine_bases"]
            == gates["expected_shared_affine_bases"]
            and row["failed_float_digest_reference"]["shared_affine_bases"]
            == gates["expected_failed_parent_affine_bases"]
            for row in targets
        ),
        "logical_middle_rank_identity": all(
            row["canonical"]["total_logical_middle_rank"]
            == row["raw_two_size_reference"]["total_middle_rank"]
            and row["canonical"]["maximum_middle_rank"]
            == row["raw_two_size_reference"]["maximum_middle_rank"]
            for row in targets
        ),
        "raw_equivalent_byte_identity": all(
            row["canonical"]["raw_equivalent_automaton_numeric_bytes"]
            == row["raw_two_size_reference"]["automaton_numeric_bytes"]
            for row in targets
        )
        == gates["require_raw_equivalent_byte_identity"],
        "storage_below_failed_parent": all(
            row["canonical"]["persistent_numeric_bytes"]
            < row["failed_float_digest_reference"]["persistent_numeric_bytes"]
            and row["canonical"]["stored_topology_middle_rank"]
            < row["failed_float_digest_reference"]["stored_topology_middle_rank"]
            for row in targets
        )
        == gates["require_storage_below_failed_parent"],
        "cache_construction": all(
            row["canonical"]["compiled"]
            and row["canonical"]["cold_construction_ms"]
            <= gates["maximum_cache_compile_ms"]
            for row in targets
        ),
        "cache_pool_ceiling": all(
            row["canonical"]["pool_total_bytes"] <= gates["maximum_gpu_pool_bytes"]
            for row in targets
        ),
        "zero_h32_steps": (h32_steps_executed == 0)
        == gates["require_zero_h32_steps"],
        "no_strategy_quality_evaluation": (strategy_quality_evaluations == 0)
        == gates["require_no_strategy_quality_evaluation"],
        "wall_time": total_seconds <= gates["maximum_total_audit_seconds"],
    }
    passed = all(gate_results.values())
    result = {
        "schema_version": 1,
        "status": "frozen_canonical_affine_cache_replay_executed",
        "experiment_type": "h32_scale_canonical_affine_cache_only_replay",
        "config": config,
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {
            field.removeprefix("expected_"): config[field]
            for field in config
            if field.startswith("expected_") and field.endswith("_sha256")
        },
        "environment": {**environment, **runtime},
        "parent_identity": parent_identity,
        "small_control": small,
        "family_geometry": family_geometry,
        "targets": targets,
        "headroom": {
            "pool_ceiling_bytes": gates["maximum_gpu_pool_bytes"],
            "frozen_noncache_reserve_bytes": parsed[
                "minimum_warm_noncache_reserve_bytes"
            ],
            "minimum_canonical_pool_cap_headroom_bytes": min(
                row["canonical"]["pool_cap_headroom_bytes"] for row in targets
            ),
            "minimum_canonical_physical_device_free_bytes": min(
                row["canonical"]["physical_device_free_bytes"] for row in targets
            ),
            "safe_under_prior_rule": prior_rule_safe,
            "rule": parsed["headroom_rule"],
        },
        "h32_steps_executed": h32_steps_executed,
        "strategy_quality_evaluations": strategy_quality_evaluations,
        "decision": (
            "accept_scale_canonical_affine_cache_geometry_without_another_step"
            if passed
            else "reject_scale_canonical_affine_cache_replay"
        ),
        "gate_results": gate_results,
        "passed": passed,
        "timing": {"total_seconds": total_seconds},
        "strategy_quality_claim": None,
        "limitations": [
            "This is a zero-step cache-only replay on one board and four constructed h32 beliefs.",
            "Persistent numeric bytes exclude Python objects and allocator metadata.",
            "Cold construction includes one belief and six canonical caches but excludes shared sparse operators.",
            "Prior-rule headroom is reported but cannot authorize another widened step.",
            "No policy is constructed, serialized, inspected, or evaluated.",
        ],
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
    result = run_h32_canonical_affine_cache_replay(
        arguments.config,
        arguments.output,
    )
    print(
        "h32 canonical affine cache replay: "
        f"passed={result['passed']}, decision={result['decision']}, "
        f"wall={result['timing']['total_seconds']:.3f}s"
    )


if __name__ == "__main__":
    main()
