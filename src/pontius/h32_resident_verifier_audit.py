"""Audit device-resident h32 terminal contraction inside the exact verifier."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time
from typing import Any

import numpy as np

from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fixed_envelope_verifier import verify_leaf_adjoint_candidate
from .h32_acceptance_semantics_replay import select_fixed_blueprint_envelope
from .h32_policy_delta_verifier_audit import (
    _ACCEPTANCE_SOURCE,
    _CANDIDATE_SOURCE,
    _EXTENSION_SOURCE,
    _INTERPOLATION_SOURCE,
    _LADDER_SOURCE,
    _live_teacher_errors,
    _source_target,
    _teacher_union,
    parse_h32_policy_delta_verifier_config,
    reconstruct_candidate_policies,
)
from .h32_warm_search_acceptance_audit import build_target_belief
from .incremental_policy_tt import compile_policy_probability_tape
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .leaf_adjoint_evaluation import evaluate_leaf_adjoint_seat
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
from .resident_leaf_adjoint_evaluation import (
    evaluate_resident_leaf_adjoint_seat,
    verify_resident_leaf_adjoint_candidate,
)
from .river import parse_cards


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-resident-verifier-audit-v1.json"
_OUTPUT = _ROOT / "experiments" / "results" / "h32-resident-verifier-audit-v1.json"
_PARENT = _ROOT / "experiments" / "results" / "h32-policy-delta-verifier-audit-v1.json"
_PARENT_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-policy-delta-verifier-audit-v1.json"
)
_REQUIREMENTS = (
    _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
)
_RESIDENT_CONTRACTION = (
    _ROOT / "src" / "pontius" / "resident_heterogeneous_leaf_contraction.py"
)
_RESIDENT_EVALUATION = (
    _ROOT / "src" / "pontius" / "resident_leaf_adjoint_evaluation.py"
)
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_parent_source_sha256",
    "expected_parent_config_sha256",
    "expected_requirements_sha256",
    "expected_resident_contraction_sha256",
    "expected_resident_evaluation_sha256",
    "expected_audit_implementation_sha256",
    "fresh_board",
    "fresh_hand_count",
    "fresh_family",
    "fresh_target_seats",
    "range_families",
    "target_shifts",
    "candidate_order",
    "seat_order",
    "calibration_candidate_id",
    "maximum_feature_width_per_batch",
    "cache_charge",
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


def parse_h32_resident_verifier_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the immutable resident-verifier protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("resident-verifier config fields differ from ADR-0109")
    frozen = {
        "evidence_stage": (
            "post_label_systems_audit_after_adr0108_before_any_h32_resident_"
            "contraction_timing"
        ),
        "seed": 20260820,
        "fresh_board": ["3s", "8c", "Th", "Kd", "Ac"],
        "fresh_hand_count": 7,
        "fresh_family": "balanced",
        "fresh_target_seats": [0, 3],
        "range_families": ["balanced", "blocker_heavy"],
        "target_shifts": ["local_blocker_seat3_x2", "all_seat_strength_1_to2"],
        "candidate_order": [
            "control_average32",
            "control_current48",
            "search_average1",
            "search_average2",
            "search_average4",
            "search_current1",
            "search_current2",
            "search_current4",
            "search_current8",
            "search_average8",
            "interpolate_current1_to2_alpha025",
            "interpolate_current1_to2_alpha050",
            "interpolate_current1_to2_alpha075",
        ],
        "seat_order": [0, 1, 2, 3, 4, 5],
        "calibration_candidate_id": "search_average1",
        "maximum_feature_width_per_batch": 384,
        "cache_charge": "one_complete_six_seat_cache_per_target",
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("resident-verifier workload differs from ADR-0109")
    sources = {
        "expected_parent_source_sha256": _PARENT,
        "expected_parent_config_sha256": _PARENT_CONFIG,
        "expected_requirements_sha256": _REQUIREMENTS,
        "expected_resident_contraction_sha256": _RESIDENT_CONTRACTION,
        "expected_resident_evaluation_sha256": _RESIDENT_EVALUATION,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"resident-verifier source hash mismatch for {field}")
    expected_gates = {
        "expected_target_rows": 4,
        "expected_candidate_rows": 52,
        "expected_live_seat_evaluations": 133,
        "expected_complete_candidate_rows": 13,
        "expected_transfer_rows": 2,
        "expected_new_strategy_quality_labels": 0,
        "maximum_transfer_utility_error": 1e-9,
        "maximum_transfer_best_response_error": 1e-9,
        "maximum_seat_utility_error": 1e-9,
        "maximum_seat_best_response_error": 1e-9,
        "maximum_seat_deviation_gain_error": 1e-9,
        "maximum_complete_nash_conv_error": 1e-9,
        "maximum_complete_zero_sum_residual": 1e-9,
        "require_stop_identity": True,
        "require_selection_identity": True,
        "require_policy_digest_identity": True,
        "minimum_pooled_calibrated_speedup": 1.5,
        "minimum_family_calibrated_speedup": 1.5,
        "minimum_calibration_ratio": 0.5,
        "maximum_calibration_ratio": 2.0,
        "maximum_candidate_seat_evaluation_ms": 60000.0,
        "maximum_static_cache_compile_ms": 120000.0,
        "maximum_host_peak_numeric_bytes": 3000000000,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_total_audit_seconds": 1200.0,
    }
    if config["gates"] != expected_gates:
        raise ValueError("resident-verifier gates differ from ADR-0109")
    return {
        **config,
        "fresh_target_seats": tuple(config["fresh_target_seats"]),
        "range_families": tuple(config["range_families"]),
        "target_shifts": tuple(config["target_shifts"]),
        "candidate_order": tuple(config["candidate_order"]),
        "seat_order": tuple(config["seat_order"]),
        "gates": dict(config["gates"]),
    }


def _parent_target(parent: dict[str, Any], *, family: str, shift: str) -> dict[str, Any]:
    return next(
        target
        for family_row in parent["family_rows"]
        if family_row["range_family"] == family
        for target in family_row["targets"]
        if target["target_shift"] == shift
    )


def _teacher_by_id(
    acceptance: dict[str, Any],
    candidate_source: dict[str, Any],
    interpolation: dict[str, Any],
    *,
    family: str,
    shift: str,
) -> dict[str, dict[str, Any]]:
    rows, _ = _teacher_union(
        (
            ("adr0099", _source_target(acceptance, family=family, shift=shift)),
            (
                "adr0101",
                _source_target(candidate_source, family=family, shift=shift),
            ),
            (
                "adr0103",
                _source_target(interpolation, family=family, shift=shift),
            ),
        ),
        maximum_duplicate_error=1e-15,
    )
    return {row["candidate_id"]: row for row in rows}


def _fresh_transfer_control(parsed: dict[str, Any]) -> dict[str, Any]:
    """Exercise both incidence directions on an undisclosed fresh h7 board."""

    parent_config = parse_h32_policy_delta_verifier_config(
        json.loads(_PARENT_CONFIG.read_text(encoding="utf-8"))
    )
    board = parse_cards(*parsed["fresh_board"])
    belief, layout, sparse, retained = _build_case(
        parsed=parent_config,
        board=board,
        hand_count=parsed["fresh_hand_count"],
        family=parsed["fresh_family"],
    )
    workspace, _, automata = retained
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    probabilities = compile_policy_probability_tape(
        layout,
        belief.hands_by_player,
        {},
    )
    rows = []
    for seat in parsed["fresh_target_seats"]:
        legacy = evaluate_leaf_adjoint_seat(
            layout,
            workspace,
            sparse,
            probabilities,
            automata[seat],
            target_player=seat,
            hands_by_player=belief.hands_by_player,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
            cupy_sparse=gpu,
        )
        belief_cache = CuPyResidentBeliefCache.compile(workspace)
        automaton_cache = CuPyResidentAutomatonCache.compile(
            workspace,
            automata[seat],
            target_seat=seat,
        )
        resident = evaluate_resident_leaf_adjoint_seat(
            layout,
            workspace,
            sparse,
            probabilities,
            automata[seat],
            target_player=seat,
            belief_cache=belief_cache,
            automaton_cache=automaton_cache,
            cupy_sparse=gpu,
            hands_by_player=belief.hands_by_player,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
        )
        cache_ms = belief_cache.upload_ms + automaton_cache.wall_ms
        rows.append(
            {
                "target_seat": seat,
                "legacy_ms": legacy.wall_ms,
                "resident_marginal_ms": resident.wall_ms,
                "resident_cache_ms": cache_ms,
                "marginal_speedup": legacy.wall_ms / resident.wall_ms,
                "one_shot_speedup": legacy.wall_ms / (resident.wall_ms + cache_ms),
                "utility_error": abs(
                    legacy.profile_utility - resident.profile_utility
                ),
                "best_response_error": abs(
                    legacy.best_response_value - resident.best_response_value
                ),
                "action_identity": (
                    legacy.best_response_actions == resident.best_response_actions
                ),
                "legacy_equivalent_transfer_bytes": (
                    resident.resident_work.legacy_equivalent_host_to_device_bytes
                    + resident.resident_work.legacy_equivalent_device_to_host_bytes
                ),
                "resident_marginal_transfer_bytes": (
                    resident.resident_work.per_call_host_to_device_bytes
                    + resident.resident_work.per_call_device_to_host_bytes
                ),
            }
        )
        del automaton_cache, belief_cache
        gc.collect()
        release_cupy_memory_pool()
    del gpu
    gc.collect()
    release_cupy_memory_pool()
    return {
        "board": parsed["fresh_board"],
        "hands_per_player": parsed["fresh_hand_count"],
        "policy": "uniform",
        "rows": rows,
    }


def _cache_host_estimate(
    workspace: Any,
    sparse: Any,
    automata: tuple[dict[str, Any], ...],
    caches: tuple[CuPyResidentAutomatonCache, ...],
) -> int:
    unique_automata = {
        id(automaton): automaton
        for library in automata
        for automaton in library.values()
    }
    return int(
        workspace.topology.numeric_bytes
        + workspace.numeric_bytes
        + sparse.numeric_bytes
        + sum(automaton.numeric_bytes for automaton in unique_automata.values())
        + max(cache.numeric_bytes for cache in caches)
    )


def _run_target(
    *,
    parsed: dict[str, Any],
    parent_config: dict[str, Any],
    parent: dict[str, Any],
    family: str,
    shift: str,
    board: tuple[int, ...],
    source_belief: Any,
    source_workspace: OpenModeFactorTTWorkspace,
    layout: Any,
    sparse: Any,
    automata: Any,
    gpu: Any,
    acceptance: dict[str, Any],
    candidate_source: dict[str, Any],
    interpolation: dict[str, Any],
    ladder: dict[str, Any],
    extension: dict[str, Any],
) -> dict[str, Any]:
    parent_target = _parent_target(parent, family=family, shift=shift)
    acceptance_target = _source_target(acceptance, family=family, shift=shift)
    candidate_target = _source_target(candidate_source, family=family, shift=shift)
    target_belief, _ = build_target_belief(
        source_belief,
        board=board,
        shift=shift,
        local_blocker_target_seat=parent_config["local_blocker_target_seat"],
    )
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        target_belief,
        query_chunk_records=parent_config["query_chunk_records"],
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    blueprint_policy, policies, source_policy_identity = reconstruct_candidate_policies(
        family=family,
        acceptance_target=acceptance_target,
        candidate_target=candidate_target,
        ladder_source=ladder,
        extension_source=extension,
        candidate_order=parsed["candidate_order"],
    )
    teachers = _teacher_by_id(
        acceptance,
        candidate_source,
        interpolation,
        family=family,
        shift=shift,
    )
    blueprint_quality = acceptance_target["blueprint_quality"]
    policy_identity = source_policy_identity and all(
        row["policy_sha256"]
        == teachers[row["candidate_id"]]["quality"]["policy_sha256"]
        for row in policies
    )
    policy_identity = policy_identity and (
        policy_digest(blueprint_policy) == blueprint_quality["policy_sha256"]
    )

    calibration_row = next(
        row
        for row in policies
        if row["candidate_id"] == parsed["calibration_candidate_id"]
    )
    raw_guard = (
        parent_config["acceptance_guard_normalized"] * parent_config["stack"]
    )
    blueprint_gains = tuple(float(v) for v in blueprint_quality["deviation_gains"])
    legacy_calibration = verify_leaf_adjoint_candidate(
        candidate_id=calibration_row["candidate_id"],
        layout=layout,
        workspace=workspace,
        sparse=sparse,
        policy=calibration_row["policy"],
        terminal_automata=automata,
        hands_by_player=target_belief.hands_by_player,
        blueprint_deviation_gains=blueprint_gains,
        best_complete_nash_conv=float(blueprint_quality["nash_conv"]),
        payoff_span=parent_config["stack"],
        raw_guard=raw_guard,
        seat_order=parsed["seat_order"],
        maximum_feature_width_per_batch=parsed[
            "maximum_feature_width_per_batch"
        ],
        cupy_sparse=gpu,
    )
    if not legacy_calibration["complete"]:
        raise AssertionError("resident calibration candidate did not complete")
    source_calibration = next(
        row
        for row in parent_target["live_candidate_rows"]
        if row["candidate_id"] == parsed["calibration_candidate_id"]
    )
    calibration_ratio = (
        legacy_calibration["wall_ms"] / source_calibration["wall_ms"]
    )
    calibrated_incumbent_ms = (
        parent_target["economics"]["live_partial_verifier_bill_ms"]
        * calibration_ratio
    )

    del legacy_calibration
    gc.collect()
    release_cupy_memory_pool()
    cache_started = time.perf_counter()
    belief_cache = CuPyResidentBeliefCache.compile(workspace)
    automaton_caches = tuple(
        CuPyResidentAutomatonCache.compile(
            workspace,
            automata[seat],
            target_seat=seat,
        )
        for seat in range(layout.num_players)
    )
    static_cache_compile_ms = (time.perf_counter() - cache_started) * 1000.0
    static_cache_numeric_bytes = belief_cache.numeric_bytes + sum(
        cache.numeric_bytes for cache in automaton_caches
    )
    cache_host_estimate = _cache_host_estimate(
        workspace,
        sparse,
        automata,
        automaton_caches,
    )

    live_rows = []
    completed = []
    best_complete = float(blueprint_quality["nash_conv"])
    stop_identity = True
    maximum_utility_error = 0.0
    maximum_response_error = 0.0
    maximum_gain_error = 0.0
    maximum_nash_error = 0.0
    maximum_zero_sum = 0.0
    parent_by_id = {
        row["candidate_id"]: row for row in parent_target["live_candidate_rows"]
    }
    for policy_row in policies:
        candidate_id = policy_row["candidate_id"]
        live = verify_resident_leaf_adjoint_candidate(
            candidate_id=candidate_id,
            layout=layout,
            workspace=workspace,
            sparse=sparse,
            policy=policy_row["policy"],
            terminal_automata=automata,
            hands_by_player=target_belief.hands_by_player,
            blueprint_deviation_gains=blueprint_gains,
            best_complete_nash_conv=best_complete,
            payoff_span=parent_config["stack"],
            raw_guard=raw_guard,
            seat_order=parsed["seat_order"],
            belief_cache=belief_cache,
            automaton_caches=automaton_caches,
            cupy_sparse=gpu,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
        )
        errors = _live_teacher_errors(live, teachers[candidate_id]["quality"])
        live["teacher_errors"] = errors
        expected = parent_by_id[candidate_id]
        identity = all(
            live[field] == expected[field]
            for field in (
                "evaluated_seats",
                "evaluated_seat_count",
                "stop_reason",
                "stop_seat",
                "complete",
            )
        )
        live["parent_stop_identity"] = identity
        stop_identity = stop_identity and identity
        maximum_utility_error = max(
            maximum_utility_error,
            errors["maximum_utility_error"],
        )
        maximum_response_error = max(
            maximum_response_error,
            errors["maximum_best_response_error"],
        )
        maximum_gain_error = max(
            maximum_gain_error,
            errors["maximum_deviation_gain_error"],
        )
        maximum_nash_error = max(
            maximum_nash_error,
            errors["complete_nash_conv_error"],
        )
        if live["complete"]:
            quality = live["quality"]
            assert quality is not None
            maximum_zero_sum = max(
                maximum_zero_sum,
                float(quality["zero_sum_residual"]),
            )
            completed.append(
                {
                    "candidate_id": candidate_id,
                    "aliases": [candidate_id],
                    "source_refs": [f"resident:{candidate_id}"],
                    "quality": {
                        "policy_sha256": quality["policy_sha256"],
                        "nash_conv": quality["nash_conv"],
                        "normalized_nash_conv": quality[
                            "normalized_nash_conv"
                        ],
                        "deviation_gains": quality["deviation_gains"],
                    },
                }
            )
            best_complete = min(best_complete, float(quality["nash_conv"]))
        live_rows.append(live)

    blueprint = {
        "candidate_id": "blueprint_average64",
        "aliases": ["blueprint_average64"],
        "source_refs": ["source:blueprint"],
        "quality": {
            "policy_sha256": blueprint_quality["policy_sha256"],
            "nash_conv": float(blueprint_quality["nash_conv"]),
            "normalized_nash_conv": float(
                blueprint_quality["normalized_nash_conv"]
            ),
            "deviation_gains": [float(v) for v in blueprint_gains],
        },
    }
    selection = select_fixed_blueprint_envelope(
        blueprint,
        completed,
        raw_guard=raw_guard,
    )
    selection_identity = (
        selection["selected_policy_sha256"]
        == parent_target["live_selection"]["selected_policy_sha256"]
        and selection["selected_candidate_id"]
        == parent_target["live_selection"]["selected_candidate_id"]
    )
    marginal_bill_ms = math.fsum(float(row["wall_ms"]) for row in live_rows)
    charged_bill_ms = static_cache_compile_ms + marginal_bill_ms
    seat_rows = [seat for row in live_rows for seat in row["seat_rows"]]
    static_h2d_bytes = static_cache_numeric_bytes
    marginal_h2d_bytes = sum(
        int(seat["per_call_host_to_device_bytes"]) for seat in seat_rows
    )
    marginal_d2h_bytes = sum(
        int(seat["per_call_device_to_host_bytes"]) for seat in seat_rows
    )
    legacy_h2d_bytes = sum(
        int(seat["legacy_equivalent_host_to_device_bytes"])
        for seat in seat_rows
    )
    legacy_d2h_bytes = sum(
        int(seat["legacy_equivalent_device_to_host_bytes"])
        for seat in seat_rows
    )
    pool = _cupy_modules()[0].get_default_memory_pool()
    maximum_gpu = max(
        int(pool.total_bytes()),
        *(int(seat["maximum_gpu_pool_total_bytes"]) for seat in seat_rows),
    )
    maximum_host = max(
        cache_host_estimate,
        *(int(row["maximum_host_peak_numeric_bytes"]) for row in live_rows),
    )
    result = {
        "range_family": family,
        "target_shift": shift,
        "policy_digest_identity": policy_identity,
        "stop_identity": stop_identity,
        "selection_identity": selection_identity,
        "selection": selection,
        "resident_candidate_rows": live_rows,
        "correctness": {
            "maximum_utility_error": maximum_utility_error,
            "maximum_best_response_error": maximum_response_error,
            "maximum_deviation_gain_error": maximum_gain_error,
            "maximum_complete_nash_conv_error": maximum_nash_error,
            "maximum_complete_zero_sum_residual": maximum_zero_sum,
        },
        "static_cache": {
            "charge": parsed["cache_charge"],
            "compile_ms": static_cache_compile_ms,
            "belief_upload_ms": belief_cache.upload_ms,
            "automaton_half_prepare_ms": math.fsum(
                cache.half_prepare_ms for cache in automaton_caches
            ),
            "automaton_upload_ms": math.fsum(
                cache.upload_ms for cache in automaton_caches
            ),
            "numeric_bytes": static_cache_numeric_bytes,
            "per_seat_numeric_bytes": [
                cache.numeric_bytes for cache in automaton_caches
            ],
        },
        "economics": {
            "source_partial_verifier_bill_ms": parent_target["economics"][
                "live_partial_verifier_bill_ms"
            ],
            "source_calibration_ms": source_calibration["wall_ms"],
            "live_legacy_calibration_ms": (
                source_calibration["wall_ms"] * calibration_ratio
            ),
            "calibration_ratio": calibration_ratio,
            "calibrated_incumbent_bill_ms": calibrated_incumbent_ms,
            "resident_marginal_bill_ms": marginal_bill_ms,
            "resident_charged_bill_ms": charged_bill_ms,
            "marginal_speedup": calibrated_incumbent_ms / marginal_bill_ms,
            "charged_speedup": calibrated_incumbent_ms / charged_bill_ms,
            "live_seat_evaluations": len(seat_rows),
            "complete_candidate_rows": sum(
                bool(row["complete"]) for row in live_rows
            ),
        },
        "transfer": {
            "legacy_equivalent_host_to_device_bytes": legacy_h2d_bytes,
            "legacy_equivalent_device_to_host_bytes": legacy_d2h_bytes,
            "resident_static_host_to_device_bytes": static_h2d_bytes,
            "resident_marginal_host_to_device_bytes": marginal_h2d_bytes,
            "resident_marginal_device_to_host_bytes": marginal_d2h_bytes,
            "charged_byte_reduction": (
                (legacy_h2d_bytes + legacy_d2h_bytes)
                / (static_h2d_bytes + marginal_h2d_bytes + marginal_d2h_bytes)
            ),
        },
        "phase_ms": {
            "probability_compile": math.fsum(
                float(row["probability_compile_ms"]) for row in live_rows
            ),
            "factor_prepare": math.fsum(
                float(seat["factor_prepare_ms"]) for seat in seat_rows
            ),
            "factor_upload": math.fsum(
                float(seat["factor_upload_ms"]) for seat in seat_rows
            ),
            "product_generation_gpu": math.fsum(
                float(seat["product_generation_gpu_ms"]) for seat in seat_rows
            ),
            "resident_pipeline_gpu": math.fsum(
                float(seat["resident_pipeline_gpu_ms"]) for seat in seat_rows
            ),
            "device_to_host": math.fsum(
                float(seat["device_to_host_ms"]) for seat in seat_rows
            ),
            "hand_fold": math.fsum(
                float(seat["hand_fold_ms"]) for seat in seat_rows
            ),
            "reverse_evaluation": math.fsum(
                float(seat["reverse_evaluation_ms"]) for seat in seat_rows
            ),
        },
        "resources": {
            "maximum_host_peak_numeric_bytes": maximum_host,
            "maximum_gpu_pool_bytes": maximum_gpu,
        },
    }
    del automaton_caches, belief_cache
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_resident_verifier_audit(config: dict[str, Any]) -> dict[str, Any]:
    """Execute the frozen resident-verifier audit."""

    parsed = parse_h32_resident_verifier_config(config)
    import scipy

    cp, _ = _cupy_modules()
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0109")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0109")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0109")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0109")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0109 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed[
        "required_compute_capability"
    ]:
        raise ValueError("GPU compute capability differs from ADR-0109")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")

    parent = json.loads(_PARENT.read_text(encoding="utf-8"))
    parent_config = parse_h32_policy_delta_verifier_config(
        json.loads(_PARENT_CONFIG.read_text(encoding="utf-8"))
    )
    source_identity = (
        bool(parent["gates"]["passed"])
        and parent["status"] == "frozen_audit_executed"
        and parent["config_sha256"] == _sha256(_PARENT_CONFIG)
        and tuple(parent_config["candidate_order"]) == parsed["candidate_order"]
        and tuple(parent_config["seat_order"]) == parsed["seat_order"]
    )
    if not source_identity:
        raise ValueError("ADR-0109 parent identity rejected")

    acceptance = json.loads(_ACCEPTANCE_SOURCE.read_text(encoding="utf-8"))
    candidate_source = json.loads(_CANDIDATE_SOURCE.read_text(encoding="utf-8"))
    interpolation = json.loads(_INTERPOLATION_SOURCE.read_text(encoding="utf-8"))
    ladder = json.loads(_LADDER_SOURCE.read_text(encoding="utf-8"))
    extension = json.loads(_EXTENSION_SOURCE.read_text(encoding="utf-8"))

    started = time.perf_counter()
    transfer_control = _fresh_transfer_control(parsed)
    board = parse_cards(*parent_config["board"])
    targets = []
    for family in parsed["range_families"]:
        release_cupy_memory_pool()
        gc.collect()
        source_belief, layout, sparse, retained = _build_case(
            parsed=parent_config,
            board=board,
            hand_count=parent_config["wide_hands_per_player"],
            family=family,
        )
        source_workspace, _, automata = retained
        gpu = CuPyBidirectionalIncidence.compile(sparse)
        for shift in parsed["target_shifts"]:
            targets.append(
                _run_target(
                    parsed=parsed,
                    parent_config=parent_config,
                    parent=parent,
                    family=family,
                    shift=shift,
                    board=board,
                    source_belief=source_belief,
                    source_workspace=source_workspace,
                    layout=layout,
                    sparse=sparse,
                    automata=automata,
                    gpu=gpu,
                    acceptance=acceptance,
                    candidate_source=candidate_source,
                    interpolation=interpolation,
                    ladder=ladder,
                    extension=extension,
                )
            )
        del gpu
        gc.collect()
        release_cupy_memory_pool()

    live_rows = [row for target in targets for row in target["resident_candidate_rows"]]
    seat_rows = [seat for row in live_rows for seat in row["seat_rows"]]
    transfer_rows = transfer_control["rows"]
    total_seconds = time.perf_counter() - started
    family_speedups = {
        family: (
            math.fsum(
                target["economics"]["calibrated_incumbent_bill_ms"]
                for target in targets
                if target["range_family"] == family
            )
            / math.fsum(
                target["economics"]["resident_charged_bill_ms"]
                for target in targets
                if target["range_family"] == family
            )
        )
        for family in parsed["range_families"]
    }
    pooled_incumbent = math.fsum(
        target["economics"]["calibrated_incumbent_bill_ms"] for target in targets
    )
    pooled_resident = math.fsum(
        target["economics"]["resident_charged_bill_ms"] for target in targets
    )
    pooled_speedup = pooled_incumbent / pooled_resident
    maximum_host = max(
        target["resources"]["maximum_host_peak_numeric_bytes"] for target in targets
    )
    maximum_gpu = max(
        target["resources"]["maximum_gpu_pool_bytes"] for target in targets
    )
    maximum_seat_ms = max(float(seat["wall_ms"]) for seat in seat_rows)
    maximum_cache_ms = max(
        target["static_cache"]["compile_ms"] for target in targets
    )
    calibration_ratios = [
        target["economics"]["calibration_ratio"] for target in targets
    ]
    gates_config = parsed["gates"]
    gates = {
        "source_identity": source_identity,
        "target_rows": len(targets) == gates_config["expected_target_rows"],
        "candidate_rows": len(live_rows) == gates_config["expected_candidate_rows"],
        "live_seat_evaluations": len(seat_rows)
        == gates_config["expected_live_seat_evaluations"],
        "complete_candidate_rows": sum(bool(row["complete"]) for row in live_rows)
        == gates_config["expected_complete_candidate_rows"],
        "transfer_rows": len(transfer_rows) == gates_config["expected_transfer_rows"],
        "zero_new_strategy_quality_labels": gates_config[
            "expected_new_strategy_quality_labels"
        ]
        == 0,
        "transfer_utility_error": max(row["utility_error"] for row in transfer_rows)
        <= gates_config["maximum_transfer_utility_error"],
        "transfer_best_response_error": max(
            row["best_response_error"] for row in transfer_rows
        )
        <= gates_config["maximum_transfer_best_response_error"],
        "seat_utility_error": max(
            target["correctness"]["maximum_utility_error"] for target in targets
        )
        <= gates_config["maximum_seat_utility_error"],
        "seat_best_response_error": max(
            target["correctness"]["maximum_best_response_error"]
            for target in targets
        )
        <= gates_config["maximum_seat_best_response_error"],
        "seat_deviation_gain_error": max(
            target["correctness"]["maximum_deviation_gain_error"]
            for target in targets
        )
        <= gates_config["maximum_seat_deviation_gain_error"],
        "complete_nash_conv_error": max(
            target["correctness"]["maximum_complete_nash_conv_error"]
            for target in targets
        )
        <= gates_config["maximum_complete_nash_conv_error"],
        "complete_zero_sum_residual": max(
            target["correctness"]["maximum_complete_zero_sum_residual"]
            for target in targets
        )
        <= gates_config["maximum_complete_zero_sum_residual"],
        "stop_identity": all(target["stop_identity"] for target in targets)
        == gates_config["require_stop_identity"],
        "selection_identity": all(target["selection_identity"] for target in targets)
        == gates_config["require_selection_identity"],
        "policy_digest_identity": all(
            target["policy_digest_identity"] for target in targets
        )
        == gates_config["require_policy_digest_identity"],
        "pooled_calibrated_speedup": pooled_speedup
        >= gates_config["minimum_pooled_calibrated_speedup"],
        "family_calibrated_speedup": all(
            value >= gates_config["minimum_family_calibrated_speedup"]
            for value in family_speedups.values()
        ),
        "calibration_ratio": min(calibration_ratios)
        >= gates_config["minimum_calibration_ratio"]
        and max(calibration_ratios) <= gates_config["maximum_calibration_ratio"],
        "candidate_seat_evaluation_ms": maximum_seat_ms
        <= gates_config["maximum_candidate_seat_evaluation_ms"],
        "static_cache_compile_ms": maximum_cache_ms
        <= gates_config["maximum_static_cache_compile_ms"],
        "host_peak_numeric_bytes": maximum_host
        <= gates_config["maximum_host_peak_numeric_bytes"],
        "gpu_pool_bytes": maximum_gpu <= gates_config["maximum_gpu_pool_bytes"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    legacy_bytes = math.fsum(
        target["transfer"]["legacy_equivalent_host_to_device_bytes"]
        + target["transfer"]["legacy_equivalent_device_to_host_bytes"]
        for target in targets
    )
    resident_bytes = math.fsum(
        target["transfer"]["resident_static_host_to_device_bytes"]
        + target["transfer"]["resident_marginal_host_to_device_bytes"]
        + target["transfer"]["resident_marginal_device_to_host_bytes"]
        for target in targets
    )
    return {
        "schema_version": 1,
        "status": "frozen_audit_executed",
        "experiment_type": "h32_resident_fixed_envelope_verifier",
        "config": config,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {
            "parent": _sha256(_PARENT),
            "parent_config": _sha256(_PARENT_CONFIG),
            "requirements": _sha256(_REQUIREMENTS),
            "resident_contraction": _sha256(_RESIDENT_CONTRACTION),
            "resident_evaluation": _sha256(_RESIDENT_EVALUATION),
        },
        "environment": {
            **environment_metadata(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "cupy_version": cp.__version__,
            "cuda_runtime_version": cp.cuda.runtime.runtimeGetVersion(),
            "cuda_driver_version": cp.cuda.runtime.driverGetVersion(),
            "compute_capability": str(cp.cuda.Device(0).compute_capability),
        },
        "fresh_transfer_control": transfer_control,
        "targets": targets,
        "counts": {
            "target_rows": len(targets),
            "candidate_rows": len(live_rows),
            "live_seat_evaluations": len(seat_rows),
            "complete_candidate_rows": sum(bool(row["complete"]) for row in live_rows),
            "new_strategy_quality_labels": 0,
        },
        "aggregate": {
            "pooled_calibrated_speedup": pooled_speedup,
            "family_calibrated_speedups": family_speedups,
            "calibrated_incumbent_bill_ms": pooled_incumbent,
            "resident_charged_bill_ms": pooled_resident,
            "resident_marginal_bill_ms": math.fsum(
                target["economics"]["resident_marginal_bill_ms"]
                for target in targets
            ),
            "static_cache_compile_ms": math.fsum(
                target["static_cache"]["compile_ms"] for target in targets
            ),
            "calibration_ratio_minimum": min(calibration_ratios),
            "calibration_ratio_median": statistics.median(calibration_ratios),
            "calibration_ratio_maximum": max(calibration_ratios),
            "legacy_equivalent_transfer_bytes": legacy_bytes,
            "resident_charged_transfer_bytes": resident_bytes,
            "charged_transfer_byte_reduction": legacy_bytes / resident_bytes,
            "maximum_seat_utility_error": max(
                target["correctness"]["maximum_utility_error"] for target in targets
            ),
            "maximum_seat_best_response_error": max(
                target["correctness"]["maximum_best_response_error"]
                for target in targets
            ),
            "maximum_seat_deviation_gain_error": max(
                target["correctness"]["maximum_deviation_gain_error"]
                for target in targets
            ),
            "maximum_complete_nash_conv_error": max(
                target["correctness"]["maximum_complete_nash_conv_error"]
                for target in targets
            ),
            "maximum_complete_zero_sum_residual": max(
                target["correctness"]["maximum_complete_zero_sum_residual"]
                for target in targets
            ),
            "maximum_candidate_seat_evaluation_ms": maximum_seat_ms,
            "maximum_static_cache_compile_ms": maximum_cache_ms,
            "maximum_host_peak_numeric_bytes": maximum_host,
            "maximum_gpu_pool_bytes": maximum_gpu,
        },
        "gates": gates,
        "timing": {"total_audit_seconds": total_seconds},
        "limitations": [
            "This post-label systems audit creates no new strategy-quality labels.",
            "Static resident caches are conservatively rebuilt and charged once per target.",
            "The incumbent bill is same-day calibrated with one complete legacy candidate per target.",
            "The fresh-board transfer control is h7 uniform policy, not a fresh h32 strategy corpus.",
            "Blueprint caps certify unilateral deviations, not coalition safety.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_h32_resident_verifier_audit(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "h32 resident verifier audit: "
        f"passed={result['gates']['passed']} "
        f"speedup={result['aggregate']['pooled_calibrated_speedup']:.3f} "
        f"seconds={result['timing']['total_audit_seconds']:.3f}"
    )
    return 0 if result["gates"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
