"""Frozen common-game h32 quality comparison for one versus two bet sizes."""

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
)
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .factorized_belief import FactorizedCardBelief
from .fixed_envelope_verifier import _stop_reason
from .fresh_h32_strategy_transfer_audit import (
    _belief_digest,
    _build_target_belief,
    parse_fresh_h32_strategy_transfer_config,
)
from .h32_acceptance_semantics_replay import select_fixed_blueprint_envelope
from .h32_affine_resident_cache_preflight import (
    _representative_sized_tree,
    _strict_git_metadata,
    _validate_runtime,
)
from .h32_warm_search_acceptance_audit import _average_policy_from_state
from .incremental_policy_tt import compile_policy_probability_tape
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .multi_size_affine_resident_leaf_adjoint_cfr import (
    MultiSizeAffineResidentLeafAdjointPublicTreeCFR,
)
from .multi_size_affine_resident_leaf_adjoint_evaluation import (
    MultiSizeAffineResidentProfileEvaluation,
    MultiSizeAffineResidentSeatEvaluation,
    evaluate_multi_size_affine_resident_profile,
    evaluate_multi_size_affine_resident_seat,
)
from .multi_size_leaf_adjoint import (
    build_multi_size_leaf_adjoint_terminal_automata,
    multi_size_terminal_groups,
)
from .multi_size_policy_bridge import (
    deserialize_compact_sized_policy,
    embed_one_size_policy,
    serialize_compact_sized_policy,
    sized_action_token,
    sized_policy_digest,
)
from .multi_size_public_tree_tensor import MultiSizePublicTreeTensorEvaluator
from .open_mode_audit import _open_workspace
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .public_policy_tt import _information_key
from .public_tree_tensor import PublicTreeTensorEvaluator
from .real_policy import mean_policy_total_variation, policy_digest
from .reporting import environment_metadata
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .river import BET, CALL, CHECK, FOLD, HoleCards, parse_cards
from .river_multi_size import BetAction
from .river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem
from .river_multiway_multi_size import MultiwayMultiSizeRiverHoldem
from .showdown_value_rank_screen import _rank_codes
from .sparse_incidence_open_mode import SparseBidirectionalIncidence


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-action-width-quality-v1.json"
_OUTPUT = _ROOT / "experiments" / "results" / "h32-action-width-quality-v1.json"
_PARENT = _ROOT / "experiments" / "results" / "fresh-h32-strategy-transfer-audit-v1.json"
_PARENT_CONFIG = _ROOT / "experiments" / "configs" / "fresh-h32-strategy-transfer-audit-v1.json"
_CACHE_PARENT = _ROOT / "experiments" / "results" / "h32-canonical-affine-cache-replay-v1.json"
_CACHE_PARENT_CONFIG = _ROOT / "experiments" / "configs" / "h32-canonical-affine-cache-replay-v1.json"
_REQUIREMENTS = _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
_IMPLEMENTATION = Path(__file__)
_POLICY_BRIDGE = _ROOT / "src" / "pontius" / "multi_size_policy_bridge.py"
_SIZED_EVALUATION = _ROOT / "src" / "pontius" / "multi_size_affine_resident_leaf_adjoint_evaluation.py"
_CANONICAL_CACHE = _ROOT / "src" / "pontius" / "canonical_affine_resident_automaton_cache.py"
_AFFINE_CFR = _ROOT / "src" / "pontius" / "multi_size_affine_resident_leaf_adjoint_cfr.py"
_ONE_SIZE_CFR = _ROOT / "src" / "pontius" / "resident_leaf_adjoint_cfr.py"
_SIZED_LEAF = _ROOT / "src" / "pontius" / "multi_size_leaf_adjoint.py"
_SIZED_LAYOUT = _ROOT / "src" / "pontius" / "multi_size_public_tree_tensor.py"
_SIZED_GAME = _ROOT / "src" / "pontius" / "river_multiway_multi_size.py"
_RESIDENT_CONTRACTION = _ROOT / "src" / "pontius" / "resident_heterogeneous_leaf_contraction.py"
_CUPY_INCIDENCE = _ROOT / "src" / "pontius" / "cupy_sparse_incidence.py"
_FRESH_IMPLEMENTATION = _ROOT / "src" / "pontius" / "fresh_h32_strategy_transfer_audit.py"
_LADDER_IMPLEMENTATION = _ROOT / "src" / "pontius" / "leaf_adjoint_checkpoint_ladder_audit.py"
_FIXED_ENVELOPE = _ROOT / "src" / "pontius" / "h32_acceptance_semantics_replay.py"
_CONTROL_TEST = _ROOT / "tests" / "test_multi_size_policy_bridge_and_evaluation.py"

_CONFIG_FIELDS = {
    "evidence_stage",
    "expected_parent_sha256",
    "expected_parent_config_sha256",
    "expected_cache_parent_sha256",
    "expected_cache_parent_config_sha256",
    "expected_requirements_sha256",
    "expected_audit_implementation_sha256",
    "expected_policy_bridge_sha256",
    "expected_sized_evaluation_sha256",
    "expected_canonical_cache_sha256",
    "expected_affine_cfr_sha256",
    "expected_one_size_cfr_sha256",
    "expected_sized_leaf_sha256",
    "expected_sized_layout_sha256",
    "expected_sized_game_sha256",
    "expected_resident_contraction_sha256",
    "expected_cupy_incidence_sha256",
    "expected_fresh_implementation_sha256",
    "expected_ladder_implementation_sha256",
    "expected_fixed_envelope_sha256",
    "expected_control_test_sha256",
    "board",
    "pot",
    "stack",
    "one_size_bet",
    "two_size_bets",
    "expected_one_size_payoff_span",
    "expected_two_size_payoff_span",
    "players",
    "hands_per_player",
    "range_families",
    "target_shifts",
    "target_order",
    "arm_order_by_target",
    "solver_variant",
    "warm_regret_mass_payoff_fraction",
    "construction_and_planning_budget_ms",
    "reserved_complete_step_ms",
    "maximum_complete_steps",
    "candidate_rule",
    "interpolation_alpha",
    "fixed_seat_order",
    "acceptance_guard_normalized",
    "mixture_components",
    "split_index",
    "query_chunk_records",
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


def parse_h32_action_width_quality_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the complete ADR-0134 strategy-comparison contract."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("h32 action-width quality config fields differ from ADR-0134")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0133_before_any_h32_two_size_policy_"
            "construction_or_common_game_quality_measurement"
        ),
        "board": ["4h", "6s", "Td", "Qh", "As"],
        "pot": 12.0,
        "stack": 30.0,
        "one_size_bet": 3.0,
        "two_size_bets": [3.0, 6.0],
        "expected_one_size_payoff_span": 30.0,
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
        "arm_order_by_target": [
            "one_then_two",
            "two_then_one",
            "two_then_one",
            "one_then_two",
        ],
        "solver_variant": "dcfr",
        "warm_regret_mass_payoff_fraction": 0.1,
        "construction_and_planning_budget_ms": 90000.0,
        "reserved_complete_step_ms": 35000.0,
        "maximum_complete_steps": 8,
        "candidate_rule": (
            "deduplicated_current1_then_current1_current2_alpha050_then_"
            "deadline_current_then_deadline_average"
        ),
        "interpolation_alpha": 0.5,
        "fixed_seat_order": [0, 1, 2, 3, 4, 5],
        "acceptance_guard_normalized": 1e-10,
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 384,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("h32 action-width quality workload differs from ADR-0134")
    if config["reserved_complete_step_ms"] >= config["construction_and_planning_budget_ms"]:
        raise ValueError("h32 action-width step reserve consumes the complete budget")

    sources = {
        "expected_parent_sha256": _PARENT,
        "expected_parent_config_sha256": _PARENT_CONFIG,
        "expected_cache_parent_sha256": _CACHE_PARENT,
        "expected_cache_parent_config_sha256": _CACHE_PARENT_CONFIG,
        "expected_requirements_sha256": _REQUIREMENTS,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
        "expected_policy_bridge_sha256": _POLICY_BRIDGE,
        "expected_sized_evaluation_sha256": _SIZED_EVALUATION,
        "expected_canonical_cache_sha256": _CANONICAL_CACHE,
        "expected_affine_cfr_sha256": _AFFINE_CFR,
        "expected_one_size_cfr_sha256": _ONE_SIZE_CFR,
        "expected_sized_leaf_sha256": _SIZED_LEAF,
        "expected_sized_layout_sha256": _SIZED_LAYOUT,
        "expected_sized_game_sha256": _SIZED_GAME,
        "expected_resident_contraction_sha256": _RESIDENT_CONTRACTION,
        "expected_cupy_incidence_sha256": _CUPY_INCIDENCE,
        "expected_fresh_implementation_sha256": _FRESH_IMPLEMENTATION,
        "expected_ladder_implementation_sha256": _LADDER_IMPLEMENTATION,
        "expected_fixed_envelope_sha256": _FIXED_ENVELOPE,
        "expected_control_test_sha256": _CONTROL_TEST,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"h32 action-width quality source hash mismatch: {field}")

    expected_gates = {
        "expected_target_rows": 4,
        "expected_arm_rows": 8,
        "expected_one_size_public_nodes": 385,
        "expected_two_size_public_nodes": 763,
        "expected_two_size_terminal_groups": 127,
        "expected_one_size_information_sets": 6144,
        "expected_one_size_hand_action_entries": 12288,
        "expected_two_size_information_sets": 12096,
        "expected_two_size_hand_action_entries": 24384,
        "expected_shared_affine_bases": 378,
        "maximum_small_profile_utility_error": 2e-12,
        "maximum_small_quality_error": 2e-11,
        "maximum_small_zero_sum_residual": 2e-11,
        "maximum_complete_step_ms": 35000.0,
        "maximum_arm_construction_and_planning_ms": 90000.0,
        "maximum_cache_compile_ms": 120000.0,
        "maximum_quality_seat_ms": 60000.0,
        "maximum_quality_vector_sum_error": 1e-10,
        "maximum_quality_zero_sum_residual": 1e-9,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_total_audit_seconds": 3600.0,
        "require_clean_git_state": True,
        "require_parent_identity": True,
        "require_target_identity": True,
        "require_common_game_payoff_span": True,
        "require_at_least_one_complete_step_per_arm": True,
        "require_compact_policy_round_trip": True,
        "require_planning_before_quality": True,
        "require_fixed_envelope_cap_compliance": True,
        "require_finite_policies_and_quality": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("h32 action-width quality gates differ from ADR-0134")
    return {
        **config,
        "two_size_bets": tuple(config["two_size_bets"]),
        "range_families": tuple(config["range_families"]),
        "target_shifts": tuple(config["target_shifts"]),
        "target_order": tuple(config["target_order"]),
        "arm_order_by_target": tuple(config["arm_order_by_target"]),
        "fixed_seat_order": tuple(config["fixed_seat_order"]),
        "gates": dict(config["gates"]),
    }


def _policy_finite(policy: Mapping[str, Mapping[Any, float]]) -> bool:
    return bool(policy) and all(
        bool(row)
        and all(math.isfinite(float(value)) and float(value) >= 0.0 for value in row.values())
        and abs(math.fsum(float(value) for value in row.values()) - 1.0) <= 1e-12
        for row in policy.values()
    )


def _table_error(
    left: Mapping[str, Mapping[Any, float]],
    right: Mapping[str, Mapping[Any, float]],
) -> float:
    if set(left) != set(right):
        return math.inf
    maximum = 0.0
    for key in left:
        if set(left[key]) != set(right[key]):
            return math.inf
        maximum = max(
            maximum,
            *(abs(float(left[key][action]) - float(right[key][action])) for action in left[key]),
        )
    return maximum


def _small_control(parsed: dict[str, Any]) -> dict[str, Any]:
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
    materialized = belief.materialize()
    joint = {
        MultiwayRiverDeal(tuple(hands[seat][indices[seat]] for seat in range(6))): mass
        for indices, mass in zip(
            materialized.assignments,
            materialized.probabilities,
            strict=True,
        )
    }
    one_layout = PublicTreeTensorEvaluator(
        MultiwayRiverHoldem.from_joint_weights(
            board=board,
            pot=parsed["pot"],
            stacks=(parsed["stack"],) * 6,
            bet_size=parsed["one_size_bet"],
            joint_weights=joint,
        )
    )
    sized_layout = MultiSizePublicTreeTensorEvaluator(
        MultiwayMultiSizeRiverHoldem.from_joint_weights(
            board=board,
            pot=parsed["pot"],
            stacks=(parsed["stack"],) * 6,
            bet_sizes=parsed["two_size_bets"],
            joint_weights=joint,
        )
    )
    one_policy = {}
    for key, actions in one_layout.information_schema().items():
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        weights = tuple(float(1 + digest[index] % 23) for index in range(len(actions)))
        total = math.fsum(weights)
        one_policy[key] = {
            action: weights[index] / total for index, action in enumerate(actions)
        }
    embedded = embed_one_size_policy(
        one_layout,
        sized_layout,
        hands,
        one_policy,
        retained_bet_size=parsed["one_size_bet"],
    )
    one_dense = one_layout.evaluate(one_policy)
    sized_dense = sized_layout.evaluate(embedded)
    profile_error = max(
        abs(left - right)
        for left, right in zip(
            one_dense.evaluation.utilities,
            sized_dense.evaluation.utilities,
            strict=True,
        )
    )
    compact = serialize_compact_sized_policy(embedded, sized_layout, hands)
    restored = deserialize_compact_sized_policy(compact, sized_layout, hands)

    workspace, _ = _open_workspace(belief, split_index=3, query_chunk_records=256)
    sparse = SparseBidirectionalIncidence.compile(workspace)
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(board, hands)
    )
    libraries = build_multi_size_leaf_adjoint_terminal_automata(
        sized_layout, codes, pot=parsed["pot"]
    )
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    belief_cache = CuPyResidentBeliefCache.compile(workspace)
    caches = tuple(
        CuPyCanonicalAffineResidentAutomatonCache.compile(
            workspace, libraries[seat], target_seat=seat
        )
        for seat in range(6)
    )
    resident = evaluate_multi_size_affine_resident_profile(
        sized_layout,
        workspace,
        sparse,
        embedded,
        libraries,
        belief_cache=belief_cache,
        automaton_caches=caches,
        cupy_sparse=gpu,
        hands_by_player=hands,
        maximum_feature_width_per_batch=96,
    )
    errors = []
    for field in ("utilities", "best_response_values", "deviation_gains"):
        errors.extend(
            abs(float(left) - float(right))
            for left, right in zip(
                getattr(resident.evaluation, field),
                getattr(sized_dense.evaluation, field),
                strict=True,
            )
        )
    errors.append(abs(resident.evaluation.nash_conv - sized_dense.evaluation.nash_conv))
    result = {
        "hands_per_player": 2,
        "one_size_public_nodes": one_layout.public_node_count,
        "two_size_public_nodes": sized_layout.public_node_count,
        "two_size_terminal_groups": len(multi_size_terminal_groups(sized_layout)),
        "profile_utility_error": profile_error,
        "quality_error": max(errors),
        "zero_sum_residual": resident.zero_sum_residual,
        "compact_round_trip": restored == embedded,
        "policy_sha256": sized_policy_digest(embedded),
        "compact_policy_sha256": compact["policy_sha256"],
        "shared_affine_bases": sum(cache.shared_topologies for cache in caches),
        "two_size_payoff_span": float(sized_layout.game.payoff_span),
    }
    del resident, caches, belief_cache, gpu
    gc.collect()
    release_cupy_memory_pool()
    return result


def _target_workspace(
    source_workspace: OpenModeFactorTTWorkspace,
    target_belief: FactorizedCardBelief,
    *,
    query_chunk_records: int,
) -> tuple[OpenModeFactorTTWorkspace, float]:
    started = time.perf_counter()
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        target_belief,
        query_chunk_records=query_chunk_records,
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    return workspace, (time.perf_counter() - started) * 1000.0


def _compile_cache(
    cp: Any,
    workspace: OpenModeFactorTTWorkspace,
    libraries: tuple[Mapping[str, Any], ...],
    *,
    arm: str,
) -> tuple[dict[str, Any], CuPyResidentBeliefCache, tuple[Any, ...]]:
    pool = cp.get_default_memory_pool()
    cp.cuda.runtime.deviceSynchronize()
    baseline_used = int(pool.used_bytes())
    baseline_total = int(pool.total_bytes())
    started = time.perf_counter()
    belief_cache = CuPyResidentBeliefCache.compile(workspace)
    if arm == "one_size":
        caches = tuple(
            CuPyResidentAutomatonCache.compile(
                workspace, libraries[seat], target_seat=seat
            )
            for seat in range(len(libraries))
        )
    elif arm == "two_size":
        caches = tuple(
            CuPyCanonicalAffineResidentAutomatonCache.compile(
                workspace, libraries[seat], target_seat=seat
            )
            for seat in range(len(libraries))
        )
    else:
        raise ValueError("unknown action-width cache arm")
    cp.cuda.runtime.deviceSynchronize()
    wall_ms = (time.perf_counter() - started) * 1000.0
    used = int(pool.used_bytes())
    total = int(pool.total_bytes())
    free, device_total = cp.cuda.runtime.memGetInfo()
    cache_bytes = sum(int(cache.numeric_bytes) for cache in caches)
    row = {
        "arm": arm,
        "belief_numeric_bytes": int(belief_cache.numeric_bytes),
        "automaton_numeric_bytes": cache_bytes,
        "persistent_numeric_bytes": int(belief_cache.numeric_bytes) + cache_bytes,
        "cold_construction_ms": wall_ms,
        "pool_baseline_used_bytes": baseline_used,
        "pool_baseline_total_bytes": baseline_total,
        "pool_used_bytes": used,
        "pool_total_bytes": total,
        "pool_used_increase_bytes": used - baseline_used,
        "pool_total_increase_bytes": total - baseline_total,
        "physical_device_free_bytes": int(free),
        "physical_device_total_bytes": int(device_total),
        "logical_automata": sum(int(cache.unique_automata) for cache in caches),
        "maximum_middle_rank": max(int(cache.maximum_middle_rank) for cache in caches),
        "total_middle_rank": sum(int(cache.total_middle_rank) for cache in caches),
        "shared_affine_bases": (
            sum(int(cache.shared_topologies) for cache in caches)
            if arm == "two_size"
            else None
        ),
    }
    return row, belief_cache, caches


def _interpolate_policy(
    first: Mapping[str, Mapping[Any, float]],
    second: Mapping[str, Mapping[Any, float]],
    alpha: float,
) -> dict[str, dict[Any, float]]:
    if set(first) != set(second):
        raise ValueError("action-width interpolation information schemas differ")
    result = {}
    for key in first:
        if set(first[key]) != set(second[key]):
            raise ValueError("action-width interpolation action schemas differ")
        result[key] = {
            action: (1.0 - alpha) * float(first[key][action])
            + alpha * float(second[key][action])
            for action in first[key]
        }
    return dict(sorted(result.items()))


def _added_bet_diagnostics(
    layout: MultiSizePublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    policy: Mapping[str, Mapping[Any, float]],
    *,
    added_amount: float,
) -> dict[str, Any]:
    values = []
    for node in layout.nodes:
        if CHECK not in node.actions:
            continue
        added = next(
            action
            for action in node.actions
            if isinstance(action, BetAction) and action.amount == added_amount
        )
        for hand in hands_by_player[node.player]:
            key = _information_key(layout, node.player, hand, node.history)
            values.append(float(policy[key][added]))
    return {
        "opening_information_sets": len(values),
        "mean_added_bet_probability": math.fsum(values) / len(values),
        "maximum_added_bet_probability": max(values),
        "positive_added_bet_information_sets": sum(value > 0.0 for value in values),
    }


def _arm_plan(
    *,
    parsed: dict[str, Any],
    cp: Any,
    arm: str,
    source_workspace: OpenModeFactorTTWorkspace,
    target_belief: FactorizedCardBelief,
    sparse: SparseBidirectionalIncidence,
    gpu: CuPyBidirectionalIncidence,
    one_layout: PublicTreeTensorEvaluator,
    one_libraries: tuple[Mapping[str, Any], ...],
    sized_layout: MultiSizePublicTreeTensorEvaluator,
    sized_libraries: tuple[Mapping[str, Any], ...],
    one_blueprint: dict[str, dict[Any, float]],
    sized_blueprint: dict[str, dict[Any, float]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    gc.collect()
    release_cupy_memory_pool()
    started = time.perf_counter()
    workspace, workspace_ms = _target_workspace(
        source_workspace,
        target_belief,
        query_chunk_records=parsed["query_chunk_records"],
    )
    if arm == "one_size":
        layout = one_layout
        libraries = one_libraries
        initial_policy = one_blueprint
    elif arm == "two_size":
        layout = sized_layout
        libraries = sized_libraries
        initial_policy = sized_blueprint
    else:
        raise ValueError("unknown action-width planning arm")
    cache, belief_cache, automaton_caches = _compile_cache(
        cp, workspace, libraries, arm=arm
    )
    initialization_started = time.perf_counter()
    if arm == "one_size":
        solver: Any = ResidentLeafAdjointPublicTreeCFR(
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
    else:
        solver = MultiSizeAffineResidentLeafAdjointPublicTreeCFR(
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
    warm_mass = (
        parsed["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span)
    )
    solver.warm_start(initial_policy, warm_mass)
    initialization_ms = (time.perf_counter() - initialization_started) * 1000.0

    step_rows = []
    current_one = None
    current_two = None
    deadline_current = None
    deadline_average = None
    while solver.iteration < parsed["maximum_complete_steps"]:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if (
            elapsed_ms + parsed["reserved_complete_step_ms"]
            > parsed["construction_and_planning_budget_ms"]
        ):
            break
        step_started = time.perf_counter()
        solver.step()
        step_ms = (time.perf_counter() - step_started) * 1000.0
        capture_started = time.perf_counter()
        deadline_current = solver.current_strategy()
        deadline_average = solver.average_strategy()
        if solver.iteration == 1:
            current_one = deadline_current
        if solver.iteration == 2:
            current_two = deadline_current
        capture_ms = (time.perf_counter() - capture_started) * 1000.0
        if solver.last_step_work is None:
            raise AssertionError("action-width planning step has no telemetry")
        work = solver.last_step_work
        step_rows.append(
            {
                "iteration": solver.iteration,
                "wall_ms": step_ms,
                "reported_wall_ms": work.wall_ms,
                "candidate_capture_ms": capture_ms,
                "terminal_contraction_ms": work.terminal_contraction_ms,
                "terminal_sparse_batches": sum(
                    row.terminal_sparse_batches for row in work.traversers
                ),
                "maximum_gpu_pool_bytes": max(
                    row.maximum_gpu_pool_total_bytes for row in work.traversers
                ),
                "maximum_middle_rank": max(
                    row.maximum_terminal_middle_rank for row in work.traversers
                ),
            }
        )
    if current_one is None or deadline_current is None or deadline_average is None:
        raise RuntimeError("action-width shot clock completed no planning step")

    candidate_sources: list[tuple[str, dict[str, dict[Any, float]]]] = [
        ("warm_current1", current_one),
    ]
    if current_two is not None:
        candidate_sources.append(
            (
                "warm_interpolation_current1_current2_alpha050",
                _interpolate_policy(
                    current_one,
                    current_two,
                    parsed["interpolation_alpha"],
                ),
            )
        )
    candidate_sources.extend(
        (
            (f"deadline_current{solver.iteration}", deadline_current),
            (f"deadline_average{solver.iteration}", deadline_average),
        )
    )
    deduplicated: dict[str, dict[str, Any]] = {}
    live_candidates: list[dict[str, Any]] = []
    for candidate_id, policy in candidate_sources:
        sized_policy = (
            embed_one_size_policy(
                one_layout,
                sized_layout,
                target_belief.hands_by_player,
                policy,
                retained_bet_size=parsed["one_size_bet"],
            )
            if arm == "one_size"
            else policy
        )
        digest = sized_policy_digest(sized_policy)
        if digest in deduplicated:
            deduplicated[digest]["aliases"].append(candidate_id)
            continue
        compact = serialize_compact_sized_policy(
            sized_policy,
            sized_layout,
            target_belief.hands_by_player,
        )
        round_trip = deserialize_compact_sized_policy(
            compact,
            sized_layout,
            target_belief.hands_by_player,
        )
        metadata = {
            "candidate_id": candidate_id,
            "aliases": [candidate_id],
            "policy_sha256": digest,
            "policy_artifact": compact,
            "compact_round_trip": round_trip == sized_policy,
            "finite": _policy_finite(sized_policy),
            "mean_tv_from_incumbent": mean_policy_total_variation(
                sized_blueprint, sized_policy
            ),
            "added_bet": _added_bet_diagnostics(
                sized_layout,
                target_belief.hands_by_player,
                sized_policy,
                added_amount=parsed["two_size_bets"][-1],
            ),
        }
        deduplicated[digest] = metadata
        live_candidates.append({**metadata, "policy": sized_policy})
    total_ms = (time.perf_counter() - started) * 1000.0
    stop_reason = (
        "maximum_complete_steps"
        if solver.iteration == parsed["maximum_complete_steps"]
        else "reserved_complete_step_deadline"
    )
    row = {
        "arm": arm,
        "solver_payoff_span": float(layout.game.payoff_span),
        "warm_regret_mass": warm_mass,
        "target_workspace_compile_ms": workspace_ms,
        "cache": cache,
        "solver_initialization_and_warm_start_ms": initialization_ms,
        "steps": step_rows,
        "completed_steps": solver.iteration,
        "stop_reason": stop_reason,
        "candidate_rule": parsed["candidate_rule"],
        "input_candidate_count": len(candidate_sources),
        "deduplicated_candidate_count": len(live_candidates),
        "candidates": list(deduplicated.values()),
        "construction_and_planning_ms": total_ms,
        "unused_budget_ms": parsed["construction_and_planning_budget_ms"] - total_ms,
        "accumulator_numeric_bytes": solver.accumulator_numeric_bytes(),
        "finite": all(candidate["finite"] for candidate in live_candidates),
    }
    del solver, automaton_caches, belief_cache, workspace
    gc.collect()
    release_cupy_memory_pool()
    return row, live_candidates


def _action_map_digest(actions: Mapping[str, Any]) -> str:
    payload = [
        (key, sized_action_token(actions[key])) for key in sorted(actions)
    ]
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _seat_row(evaluated: MultiSizeAffineResidentSeatEvaluation) -> dict[str, Any]:
    work = evaluated.resident_work
    return {
        "target_player": evaluated.target_player,
        "profile_utility": evaluated.profile_utility,
        "best_response_value": evaluated.best_response_value,
        "deviation_gain": evaluated.deviation_gain,
        "best_response_action_sha256": _action_map_digest(
            evaluated.best_response_actions
        ),
        "exact_action_ties": evaluated.exact_action_ties,
        "minimum_action_gap": evaluated.minimum_action_gap,
        "terminal_contractions": evaluated.terminal_contractions,
        "terminal_sparse_batches": evaluated.terminal_sparse_batches,
        "terminal_contraction_ms": evaluated.terminal_contraction_ms,
        "reverse_evaluation_ms": evaluated.reverse_evaluation_ms,
        "wall_ms": evaluated.wall_ms,
        "maximum_terminal_middle_rank": evaluated.maximum_terminal_middle_rank,
        "maximum_terminal_peak_numeric_bytes": (
            evaluated.maximum_terminal_peak_numeric_bytes
        ),
        "maximum_gpu_pool_total_bytes": evaluated.maximum_gpu_pool_total_bytes,
        "resident_pipeline_gpu_ms": work.resident_pipeline_gpu_ms,
        "per_call_host_to_device_bytes": work.per_call_host_to_device_bytes,
        "per_call_device_to_host_bytes": work.per_call_device_to_host_bytes,
    }


def _quality_from_seats(
    policy_sha256: str,
    seats: tuple[MultiSizeAffineResidentSeatEvaluation, ...],
    *,
    payoff_span: float,
) -> dict[str, Any]:
    by_seat = {row.target_player: row for row in seats}
    players = len(seats)
    utilities = tuple(by_seat[seat].profile_utility for seat in range(players))
    responses = tuple(by_seat[seat].best_response_value for seat in range(players))
    gains = tuple(
        max(0.0, response - utility)
        for response, utility in zip(responses, utilities, strict=True)
    )
    nash_conv = math.fsum(gains)
    return {
        "policy_sha256": policy_sha256,
        "utilities": utilities,
        "best_response_values": responses,
        "deviation_gains": gains,
        "nash_conv": nash_conv,
        "normalized_nash_conv": nash_conv / payoff_span,
        "quality_vector_sum_error": abs(math.fsum(gains) - nash_conv),
        "zero_sum_residual": abs(math.fsum(utilities)),
        "finite": all(
            math.isfinite(value)
            for value in (*utilities, *responses, *gains, nash_conv)
        ),
    }


def _profile_row(
    candidate_id: str,
    profile: MultiSizeAffineResidentProfileEvaluation,
    *,
    payoff_span: float,
) -> dict[str, Any]:
    quality = _quality_from_seats(
        profile.policy_sha256,
        profile.seats,
        payoff_span=payoff_span,
    )
    return {
        "candidate_id": candidate_id,
        "quality": quality,
        "probability_compile_ms": profile.probability_compile_ms,
        "seat_rows": [_seat_row(row) for row in profile.seats],
        "wall_ms": profile.wall_ms,
        "maximum_gpu_pool_bytes": max(
            row.maximum_gpu_pool_total_bytes for row in profile.seats
        ),
    }


def _verify_candidate_stream(
    *,
    parsed: dict[str, Any],
    layout: MultiSizePublicTreeTensorEvaluator,
    workspace: OpenModeFactorTTWorkspace,
    sparse: SparseBidirectionalIncidence,
    libraries: tuple[Mapping[str, Any], ...],
    belief_cache: CuPyResidentBeliefCache,
    automaton_caches: tuple[CuPyCanonicalAffineResidentAutomatonCache, ...],
    gpu: CuPyBidirectionalIncidence,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    incumbent: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    started = time.perf_counter()
    payoff_span = float(layout.game.payoff_span)
    raw_guard = parsed["acceptance_guard_normalized"] * payoff_span
    best_complete = float(incumbent["quality"]["nash_conv"])
    completed = []
    rows = []
    seat_reads = 0
    for candidate in candidates:
        digest = candidate["policy_sha256"]
        if digest == incumbent["quality"]["policy_sha256"]:
            quality = dict(incumbent["quality"])
            completed.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "aliases": candidate["aliases"],
                    "quality": quality,
                }
            )
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "aliases": candidate["aliases"],
                    "policy_sha256": digest,
                    "identity_noop": True,
                    "probability_compile_ms": 0.0,
                    "seat_rows": [],
                    "evaluated_seat_count": 0,
                    "stop_reason": "identity_noop",
                    "complete": True,
                    "quality": quality,
                    "wall_ms": 0.0,
                }
            )
            continue
        candidate_started = time.perf_counter()
        probability_started = time.perf_counter()
        probabilities = compile_policy_probability_tape(
            layout,
            hands_by_player,
            candidate["policy"],
        )
        probability_ms = (time.perf_counter() - probability_started) * 1000.0
        evaluated_seats = []
        partial = 0.0
        stop = None
        stop_seat = None
        for seat in parsed["fixed_seat_order"]:
            evaluated = evaluate_multi_size_affine_resident_seat(
                layout,
                workspace,
                sparse,
                probabilities,
                libraries[seat],
                target_player=seat,
                belief_cache=belief_cache,
                automaton_cache=automaton_caches[seat],
                cupy_sparse=gpu,
                hands_by_player=hands_by_player,
                maximum_feature_width_per_batch=parsed[
                    "maximum_feature_width_per_batch"
                ],
            )
            evaluated_seats.append(evaluated)
            seat_reads += 1
            partial += evaluated.deviation_gain
            stop = _stop_reason(
                seat=seat,
                gain=evaluated.deviation_gain,
                partial_nash_conv=partial,
                blueprint_gain=float(incumbent["quality"]["deviation_gains"][seat]),
                best_complete_nash_conv=best_complete,
                raw_guard=raw_guard,
            )
            if stop is not None:
                stop_seat = seat
                break
        complete = stop is None
        quality = None
        if complete:
            quality = _quality_from_seats(
                digest,
                tuple(evaluated_seats),
                payoff_span=payoff_span,
            )
            completed.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "aliases": candidate["aliases"],
                    "quality": quality,
                }
            )
            best_complete = min(best_complete, float(quality["nash_conv"]))
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "aliases": candidate["aliases"],
                "policy_sha256": digest,
                "identity_noop": False,
                "probability_compile_ms": probability_ms,
                "seat_rows": [_seat_row(row) for row in evaluated_seats],
                "evaluated_seat_count": len(evaluated_seats),
                "partial_nash_conv": partial,
                "stop_reason": "complete" if complete else stop,
                "stop_seat": stop_seat,
                "complete": complete,
                "quality": quality,
                "wall_ms": (time.perf_counter() - candidate_started) * 1000.0,
            }
        )
    selection = select_fixed_blueprint_envelope(
        incumbent,
        completed,
        raw_guard=raw_guard,
    )
    return {
        "raw_guard": raw_guard,
        "payoff_span_source": "layout.game.payoff_span",
        "candidate_rows": rows,
        "candidate_count": len(rows),
        "complete_candidate_count": len(completed),
        "evaluated_seat_count": seat_reads,
        "selection": selection,
        "selected_raw_nash_conv_reduction": (
            float(incumbent["quality"]["nash_conv"])
            - float(selection["selected_nash_conv"])
        ),
        "selected_normalized_nash_conv_reduction": (
            float(incumbent["quality"]["normalized_nash_conv"])
            - float(selection["selected_normalized_nash_conv"])
        ),
        "wall_ms": (time.perf_counter() - started) * 1000.0,
    }


def _source_blueprint(parent: dict[str, Any], family: str) -> dict[str, dict[str, float]]:
    source = next(
        row for row in parent["source_family_rows"] if row["range_family"] == family
    )
    checkpoint = next(row for row in source["checkpoints"] if row["iteration"] == 64)
    policy = _average_policy_from_state(checkpoint["state"])
    if policy_digest(policy) != source["source_policy_digests"]["blueprint_average64"]:
        raise ValueError("frozen source blueprint policy identity rejected")
    return policy


def _parent_target(parent: dict[str, Any], family: str, shift: str) -> dict[str, Any]:
    return next(
        row
        for row in parent["targets"]
        if row["range_family"] == family and row["target_shift"] == shift
    )


def run_h32_action_width_quality_audit(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_action_width_quality_config(config)
    parent = json.loads(_PARENT.read_text(encoding="utf-8"))
    parent_config_raw = json.loads(_PARENT_CONFIG.read_text(encoding="utf-8"))
    parent_config = parse_fresh_h32_strategy_transfer_config(parent_config_raw)
    cache_parent = json.loads(_CACHE_PARENT.read_text(encoding="utf-8"))
    parent_identity = (
        _sha256(_PARENT) == parsed["expected_parent_sha256"]
        and _sha256(_PARENT_CONFIG) == parsed["expected_parent_config_sha256"]
        and parent["config_sha256"] == parsed["expected_parent_config_sha256"]
        and parent["gates"]["passed"]
        and _sha256(_CACHE_PARENT) == parsed["expected_cache_parent_sha256"]
        and _sha256(_CACHE_PARENT_CONFIG)
        == parsed["expected_cache_parent_config_sha256"]
        and cache_parent["passed"]
        and cache_parent["strategy_quality_claim"] is None
        and cache_parent["h32_steps_executed"] == 0
    )
    if not parent_identity:
        raise ValueError("h32 action-width parent identity rejected")

    environment = environment_metadata()
    environment["git"] = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    small = _small_control(parsed)
    small_passed = (
        small["profile_utility_error"]
        <= parsed["gates"]["maximum_small_profile_utility_error"]
        and small["quality_error"] <= parsed["gates"]["maximum_small_quality_error"]
        and small["zero_sum_residual"]
        <= parsed["gates"]["maximum_small_zero_sum_residual"]
        and small["compact_round_trip"]
        and small["shared_affine_bases"]
        == parsed["gates"]["expected_shared_affine_bases"]
        and small["two_size_payoff_span"] == parsed["expected_two_size_payoff_span"]
    )
    if not small_passed:
        raise ValueError("small action-width strategy control failed before h32")

    board = parse_cards(*parsed["board"])
    targets = []
    policy_artifacts: dict[str, dict[str, Any]] = {}
    phase_order_records = []
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
        one_blueprint = _source_blueprint(parent, family)
        codes = tuple(
            np.ascontiguousarray(values, dtype=np.int32)
            for values in _rank_codes(board, source_belief.hands_by_player)
        )
        sized_layout = _representative_sized_tree(
            source_belief,
            pot=parsed["pot"],
            stack=parsed["stack"],
            bet_sizes=parsed["two_size_bets"],
        )
        sized_libraries = build_multi_size_leaf_adjoint_terminal_automata(
            sized_layout,
            codes,
            pot=parsed["pot"],
        )
        sized_blueprint = embed_one_size_policy(
            one_layout,
            sized_layout,
            source_belief.hands_by_player,
            one_blueprint,
            retained_bet_size=parsed["one_size_bet"],
        )
        gpu = CuPyBidirectionalIncidence.compile(sparse)
        for shift in parsed["target_shifts"]:
            expected = _parent_target(parent, family, shift)
            target_belief, descriptor = _build_target_belief(
                source_belief,
                board=board,
                shift=shift,
                local_blocker_target_seat=parent_config[
                    "local_blocker_target_seat"
                ],
            )
            target_identity = (
                descriptor == expected["target_descriptor"]
                and _belief_digest(target_belief) == expected["target_belief_sha256"]
                and target_belief.hands_by_player == source_belief.hands_by_player
            )
            order_name = parsed["arm_order_by_target"][target_index]
            arm_order = (
                ("one_size", "two_size")
                if order_name == "one_then_two"
                else ("two_size", "one_size")
            )
            arm_rows = {}
            live_by_arm = {}
            for arm in arm_order:
                arm_row, live = _arm_plan(
                    parsed=parsed,
                    cp=cp,
                    arm=arm,
                    source_workspace=source_workspace,
                    target_belief=target_belief,
                    sparse=sparse,
                    gpu=gpu,
                    one_layout=one_layout,
                    one_libraries=one_libraries,
                    sized_layout=sized_layout,
                    sized_libraries=sized_libraries,
                    one_blueprint=one_blueprint,
                    sized_blueprint=sized_blueprint,
                )
                for candidate in arm_row["candidates"]:
                    artifact = candidate.pop("policy_artifact")
                    digest = candidate["policy_sha256"]
                    if digest in policy_artifacts and policy_artifacts[digest] != artifact:
                        raise ValueError("duplicate compact policy artifacts differ")
                    policy_artifacts[digest] = artifact
                    candidate["policy_artifact_ref"] = digest
                arm_rows[arm] = arm_row
                live_by_arm[arm] = live
            target_planning_finished_at = time.perf_counter()

            gc.collect()
            release_cupy_memory_pool()
            verifier_workspace, verifier_workspace_ms = _target_workspace(
                source_workspace,
                target_belief,
                query_chunk_records=parsed["query_chunk_records"],
            )
            verifier_cache, verifier_belief, verifier_automata = _compile_cache(
                cp,
                verifier_workspace,
                sized_libraries,
                arm="two_size",
            )
            target_quality_started_at = time.perf_counter()
            phase_order_records.append(
                target_planning_finished_at <= target_quality_started_at
            )
            incumbent_profile = evaluate_multi_size_affine_resident_profile(
                sized_layout,
                verifier_workspace,
                sparse,
                sized_blueprint,
                sized_libraries,
                belief_cache=verifier_belief,
                automaton_caches=verifier_automata,
                cupy_sparse=gpu,
                hands_by_player=target_belief.hands_by_player,
                maximum_feature_width_per_batch=parsed[
                    "maximum_feature_width_per_batch"
                ],
            )
            incumbent = _profile_row(
                "immutable_embedded_blueprint",
                incumbent_profile,
                payoff_span=float(sized_layout.game.payoff_span),
            )
            incumbent_selector_row = {
                "candidate_id": incumbent["candidate_id"],
                "aliases": [incumbent["candidate_id"]],
                "quality": incumbent["quality"],
            }
            verifiers = {}
            for arm in arm_order:
                verified = _verify_candidate_stream(
                    parsed=parsed,
                    layout=sized_layout,
                    workspace=verifier_workspace,
                    sparse=sparse,
                    libraries=sized_libraries,
                    belief_cache=verifier_belief,
                    automaton_caches=verifier_automata,
                    gpu=gpu,
                    hands_by_player=target_belief.hands_by_player,
                    incumbent=incumbent_selector_row,
                    candidates=live_by_arm[arm],
                )
                planning_ms = arm_rows[arm]["construction_and_planning_ms"]
                verified["marginal_decision_ms"] = planning_ms + verified["wall_ms"]
                verified["full_one_shot_decision_ms"] = (
                    planning_ms
                    + verifier_workspace_ms
                    + verifier_cache["cold_construction_ms"]
                    + incumbent["wall_ms"]
                    + verified["wall_ms"]
                )
                reduction = verified["selected_normalized_nash_conv_reduction"]
                verified["selected_normalized_reduction_per_marginal_ms"] = (
                    reduction / verified["marginal_decision_ms"]
                )
                verified["selected_normalized_reduction_per_full_one_shot_ms"] = (
                    reduction / verified["full_one_shot_decision_ms"]
                )
                verifiers[arm] = verified
            target_row = {
                "range_family": family,
                "target_shift": shift,
                "arm_order": order_name,
                "target_descriptor": descriptor,
                "target_belief_sha256": _belief_digest(target_belief),
                "target_identity": target_identity,
                "one_size_payoff_span": float(one_layout.game.payoff_span),
                "two_size_payoff_span": float(sized_layout.game.payoff_span),
                "payoff_span_source": "layout.game.payoff_span",
                "one_size_information_sets": len(one_blueprint),
                "one_size_hand_action_entries": sum(
                    len(row) for row in one_blueprint.values()
                ),
                "two_size_information_sets": len(sized_blueprint),
                "two_size_hand_action_entries": sum(
                    len(row) for row in sized_blueprint.values()
                ),
                "arm_planning": arm_rows,
                "verifier_workspace_compile_ms": verifier_workspace_ms,
                "verifier_cache": verifier_cache,
                "incumbent": incumbent,
                "arm_verification": verifiers,
                "selected_two_minus_one_normalized_reduction": (
                    verifiers["two_size"][
                        "selected_normalized_nash_conv_reduction"
                    ]
                    - verifiers["one_size"][
                        "selected_normalized_nash_conv_reduction"
                    ]
                ),
            }
            targets.append(target_row)
            target_index += 1
            del incumbent_profile, verifier_automata, verifier_belief, verifier_workspace
            gc.collect()
            release_cupy_memory_pool()
        del gpu
        gc.collect()
        release_cupy_memory_pool()

    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    arm_rows = [
        target["arm_planning"][arm]
        for target in targets
        for arm in ("one_size", "two_size")
    ]
    verifier_rows = [
        target["arm_verification"][arm]
        for target in targets
        for arm in ("one_size", "two_size")
    ]
    complete_quality_rows = [
        target["incumbent"]["quality"]
        for target in targets
    ] + [
        row["quality"]
        for verifier in verifier_rows
        for row in verifier["candidate_rows"]
        if row["quality"] is not None
    ]
    actual_order = tuple(
        f"{target['range_family']}/{target['target_shift']}" for target in targets
    )
    planning_before_quality = len(phase_order_records) == len(targets) and all(
        phase_order_records
    ) and all(
        set(target["arm_planning"]) == {"one_size", "two_size"}
        for target in targets
    )
    gate_results = {
        "parent_identity": parent_identity == gates["require_parent_identity"],
        "clean_git_state": (not bool(environment["git"]["dirty"]))
        == gates["require_clean_git_state"],
        "small_control": small_passed,
        "target_count_and_order": (
            len(targets) == gates["expected_target_rows"]
            and actual_order == parsed["target_order"]
        ),
        "arm_count": len(arm_rows) == gates["expected_arm_rows"],
        "target_identity": all(target["target_identity"] for target in targets)
        == gates["require_target_identity"],
        "topology_and_policy_width": all(
            target["one_size_information_sets"]
            == gates["expected_one_size_information_sets"]
            and target["one_size_hand_action_entries"]
            == gates["expected_one_size_hand_action_entries"]
            and target["two_size_information_sets"]
            == gates["expected_two_size_information_sets"]
            and target["two_size_hand_action_entries"]
            == gates["expected_two_size_hand_action_entries"]
            for target in targets
        ),
        "common_game_payoff_span": all(
            target["one_size_payoff_span"] == parsed["expected_one_size_payoff_span"]
            and target["two_size_payoff_span"] == parsed["expected_two_size_payoff_span"]
            for target in targets
        ) == gates["require_common_game_payoff_span"],
        "complete_steps": all(row["completed_steps"] >= 1 for row in arm_rows)
        == gates["require_at_least_one_complete_step_per_arm"],
        "step_ceiling": all(
            step["wall_ms"] <= gates["maximum_complete_step_ms"]
            for row in arm_rows
            for step in row["steps"]
        ),
        "arm_budget": all(
            row["construction_and_planning_ms"]
            <= gates["maximum_arm_construction_and_planning_ms"]
            for row in arm_rows
        ),
        "cache_compile": all(
            row["cache"]["cold_construction_ms"] <= gates["maximum_cache_compile_ms"]
            for row in arm_rows
        ) and all(
            target["verifier_cache"]["cold_construction_ms"]
            <= gates["maximum_cache_compile_ms"]
            for target in targets
        ),
        "canonical_basis_count": all(
            target["arm_planning"]["two_size"]["cache"]["shared_affine_bases"]
            == gates["expected_shared_affine_bases"]
            and target["verifier_cache"]["shared_affine_bases"]
            == gates["expected_shared_affine_bases"]
            for target in targets
        ),
        "compact_policy_round_trip": all(
            candidate["compact_round_trip"]
            for row in arm_rows
            for candidate in row["candidates"]
        ) == gates["require_compact_policy_round_trip"],
        "planning_before_quality": planning_before_quality
        == gates["require_planning_before_quality"],
        "quality_exactness": all(
            row["quality_vector_sum_error"]
            <= gates["maximum_quality_vector_sum_error"]
            and row["zero_sum_residual"]
            <= gates["maximum_quality_zero_sum_residual"]
            for row in complete_quality_rows
        ),
        "quality_seat_ceiling": all(
            seat["wall_ms"] <= gates["maximum_quality_seat_ms"]
            for target in targets
            for seat in target["incumbent"]["seat_rows"]
        ) and all(
            seat["wall_ms"] <= gates["maximum_quality_seat_ms"]
            for verifier in verifier_rows
            for candidate in verifier["candidate_rows"]
            for seat in candidate["seat_rows"]
        ),
        "fixed_envelope_cap_compliance": all(
            not verifier["selection"]["selected_violating_seats"]
            for verifier in verifier_rows
        ) == gates["require_fixed_envelope_cap_compliance"],
        "finite_policies_and_quality": (
            all(row["finite"] for row in arm_rows)
            and all(row["finite"] for row in complete_quality_rows)
        ) == gates["require_finite_policies_and_quality"],
        "gpu_pool_ceiling": max(
            [
                row["cache"]["pool_total_bytes"]
                for row in arm_rows
            ]
            + [
                step["maximum_gpu_pool_bytes"]
                for row in arm_rows
                for step in row["steps"]
            ]
            + [
                target["verifier_cache"]["pool_total_bytes"]
                for target in targets
            ]
            + [
                seat["maximum_gpu_pool_total_bytes"]
                for target in targets
                for seat in target["incumbent"]["seat_rows"]
            ]
            + [
                seat["maximum_gpu_pool_total_bytes"]
                for verifier in verifier_rows
                for candidate in verifier["candidate_rows"]
                for seat in candidate["seat_rows"]
            ]
        ) <= gates["maximum_gpu_pool_bytes"],
        "wall_time": total_seconds <= gates["maximum_total_audit_seconds"],
    }
    passed = all(gate_results.values())
    one_total = math.fsum(
        target["arm_verification"]["one_size"][
            "selected_normalized_nash_conv_reduction"
        ]
        for target in targets
    )
    two_total = math.fsum(
        target["arm_verification"]["two_size"][
            "selected_normalized_nash_conv_reduction"
        ]
        for target in targets
    )
    result = {
        "schema_version": 1,
        "status": "frozen_h32_action_width_quality_audit_executed",
        "experiment_type": "h32_common_game_wall_clock_matched_action_width_quality",
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
        "policy_artifacts": policy_artifacts,
        "targets": targets,
        "aggregate_strategy_outcome": {
            "targets": len(targets),
            "one_size_selected_normalized_reduction": one_total,
            "two_size_selected_normalized_reduction": two_total,
            "two_minus_one_selected_normalized_reduction": two_total - one_total,
            "one_size_blueprint_abstentions": sum(
                target["arm_verification"]["one_size"]["selection"][
                    "blueprint_abstention"
                ]
                for target in targets
            ),
            "two_size_blueprint_abstentions": sum(
                target["arm_verification"]["two_size"]["selection"][
                    "blueprint_abstention"
                ]
                for target in targets
            ),
            "outcome_is_not_a_gate": True,
        },
        "gate_results": gate_results,
        "passed": passed,
        "decision": (
            "record_conditional_common_game_action_width_result"
            if passed
            else "reject_action_width_audit_mechanism"
        ),
        "timing": {"total_seconds": total_seconds},
        "strategy_quality_claim": (
            "conditional_on_one_board_two_range_families_two_target_shifts_"
            "one_fixed_incumbent_completion_and_the_frozen_90_second_contract"
            if passed
            else None
        ),
        "limitations": [
            "Both arms are scored in the same two-size h32 game, but only one board and four constructed target beliefs are measured.",
            "The one-size off-tree response below the added bet copies its small-bet fold/call continuation.",
            "The shot clock admits only complete six-traverser steps and may leave unused time smaller than the frozen reserve.",
            "Exact fixed-envelope verification is charged separately from construction and planning and remains far outside an online 250 ms budget.",
            "No population, production abstraction, earlier-street, full-range, coalition-safety, or universal strategy claim follows.",
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
    result = run_h32_action_width_quality_audit(arguments.config, arguments.output)
    outcome = result["aggregate_strategy_outcome"]
    print(
        "h32 action-width quality audit: "
        f"passed={result['passed']}, "
        f"two_minus_one={outcome['two_minus_one_selected_normalized_reduction']:.12g}, "
        f"wall={result['timing']['total_seconds']:.3f}s"
    )


if __name__ == "__main__":
    main()
