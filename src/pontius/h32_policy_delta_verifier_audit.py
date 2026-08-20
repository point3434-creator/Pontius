"""Audit exact policy-delta width and acceptance-aware h32 verification."""

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

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fixed_envelope_verifier import (
    leaf_policy_delta_width_screen,
    simulate_fixed_envelope_verifier,
    verify_leaf_adjoint_candidate,
)
from .h32_acceptance_semantics_replay import (
    _order_rows,
    select_fixed_blueprint_envelope,
)
from .h32_current_interpolation_audit import (
    _acceptance_state,
    interpolate_behavioral_policy,
)
from .h32_warm_candidate_stream_audit import _descriptor_digest, _source_target
from .h32_warm_search_acceptance_audit import (
    _average_policy_from_state,
    _current_policy_from_state,
    _source_policies,
    build_target_belief,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .river import parse_cards


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-policy-delta-verifier-audit-v1.json"
)
_OUTPUT = (
    _ROOT / "experiments" / "results" / "h32-policy-delta-verifier-audit-v1.json"
)
_REPLAY_SOURCE = (
    _ROOT / "experiments" / "results" / "h32-acceptance-semantics-replay-v1.json"
)
_ACCEPTANCE_SOURCE = (
    _ROOT / "experiments" / "results" / "h32-warm-search-acceptance-v1.json"
)
_CANDIDATE_SOURCE = (
    _ROOT / "experiments" / "results" / "h32-warm-candidate-stream-v1.json"
)
_INTERPOLATION_SOURCE = (
    _ROOT / "experiments" / "results" / "h32-current-interpolation-audit-v1.json"
)
_LADDER_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-checkpoint-ladder-v2.json"
)
_EXTENSION_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-checkpoint-extension-v1.json"
)
_WIDTH_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-batch-width-audit-v2.json"
)
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "axis_seed",
    "expected_replay_source_sha256",
    "expected_acceptance_source_sha256",
    "expected_candidate_source_sha256",
    "expected_interpolation_source_sha256",
    "expected_ladder_source_sha256",
    "expected_extension_source_sha256",
    "expected_width_source_sha256",
    "expected_requirements_sha256",
    "expected_fixed_envelope_verifier_sha256",
    "expected_acceptance_replay_implementation_sha256",
    "expected_interpolation_implementation_sha256",
    "expected_candidate_implementation_sha256",
    "expected_acceptance_implementation_sha256",
    "expected_ladder_implementation_sha256",
    "expected_leaf_adjoint_evaluation_sha256",
    "expected_leaf_adjoint_cfr_sha256",
    "expected_heterogeneous_contraction_sha256",
    "expected_cupy_sparse_incidence_sha256",
    "expected_factor_tt_contraction_sha256",
    "expected_open_mode_factor_tt_sha256",
    "expected_sparse_open_mode_factor_tt_sha256",
    "expected_sparse_incidence_sha256",
    "expected_structured_showdown_sha256",
    "expected_audit_implementation_sha256",
    "board",
    "pot",
    "stack",
    "bet_size",
    "players",
    "wide_hands_per_player",
    "range_families",
    "target_shifts",
    "local_blocker_target_seat",
    "candidate_order",
    "seat_order",
    "acceptance_guard_normalized",
    "delta_comparison_tolerance",
    "seeded_permutation_count",
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
_GATE_FIELDS = {
    "expected_target_rows",
    "expected_candidate_rows_per_target",
    "expected_live_candidate_rows",
    "expected_live_seat_evaluations",
    "expected_complete_candidate_rows",
    "expected_order_variants_per_target",
    "expected_information_sets",
    "expected_hand_action_entries",
    "expected_new_strategy_quality_labels",
    "require_source_identity",
    "require_target_descriptor_identity",
    "require_teacher_union_identity",
    "require_policy_digest_identity",
    "maximum_seat_utility_error",
    "maximum_seat_best_response_error",
    "maximum_seat_deviation_gain_error",
    "maximum_complete_nash_conv_error",
    "maximum_complete_zero_sum_residual",
    "require_live_stop_simulation_identity",
    "require_stop_soundness",
    "require_live_selection_identity",
    "require_order_screen_selection_identity",
    "require_delta_width_finite",
    "minimum_pooled_calibrated_speedup",
    "minimum_family_calibrated_speedup",
    "minimum_structural_seat_call_speedup",
    "minimum_calibration_ratio",
    "maximum_calibration_ratio",
    "maximum_candidate_seat_evaluation_ms",
    "maximum_target_workspace_compile_ms",
    "maximum_host_peak_numeric_bytes",
    "maximum_gpu_pool_bytes",
    "maximum_total_audit_seconds",
}

_SOURCE_PATHS = {
    "expected_replay_source_sha256": _REPLAY_SOURCE,
    "expected_acceptance_source_sha256": _ACCEPTANCE_SOURCE,
    "expected_candidate_source_sha256": _CANDIDATE_SOURCE,
    "expected_interpolation_source_sha256": _INTERPOLATION_SOURCE,
    "expected_ladder_source_sha256": _LADDER_SOURCE,
    "expected_extension_source_sha256": _EXTENSION_SOURCE,
    "expected_width_source_sha256": _WIDTH_SOURCE,
    "expected_requirements_sha256": (
        _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
    ),
    "expected_fixed_envelope_verifier_sha256": (
        _ROOT / "src" / "pontius" / "fixed_envelope_verifier.py"
    ),
    "expected_acceptance_replay_implementation_sha256": (
        _ROOT / "src" / "pontius" / "h32_acceptance_semantics_replay.py"
    ),
    "expected_interpolation_implementation_sha256": (
        _ROOT / "src" / "pontius" / "h32_current_interpolation_audit.py"
    ),
    "expected_candidate_implementation_sha256": (
        _ROOT / "src" / "pontius" / "h32_warm_candidate_stream_audit.py"
    ),
    "expected_acceptance_implementation_sha256": (
        _ROOT / "src" / "pontius" / "h32_warm_search_acceptance_audit.py"
    ),
    "expected_ladder_implementation_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_checkpoint_ladder_audit.py"
    ),
    "expected_leaf_adjoint_evaluation_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_evaluation.py"
    ),
    "expected_leaf_adjoint_cfr_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_cfr.py"
    ),
    "expected_heterogeneous_contraction_sha256": (
        _ROOT / "src" / "pontius" / "heterogeneous_leaf_contraction.py"
    ),
    "expected_cupy_sparse_incidence_sha256": (
        _ROOT / "src" / "pontius" / "cupy_sparse_incidence.py"
    ),
    "expected_factor_tt_contraction_sha256": (
        _ROOT / "src" / "pontius" / "factor_tt_contraction.py"
    ),
    "expected_open_mode_factor_tt_sha256": (
        _ROOT / "src" / "pontius" / "open_mode_factor_tt.py"
    ),
    "expected_sparse_open_mode_factor_tt_sha256": (
        _ROOT / "src" / "pontius" / "sparse_open_mode_factor_tt.py"
    ),
    "expected_sparse_incidence_sha256": (
        _ROOT / "src" / "pontius" / "sparse_incidence_open_mode.py"
    ),
    "expected_structured_showdown_sha256": (
        _ROOT / "src" / "pontius" / "structured_showdown_automaton.py"
    ),
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def parse_h32_policy_delta_verifier_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the immutable ADR-0107 policy-verifier protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "policy-verifier fields differ from ADR-0107: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    frozen = {
        "evidence_stage": (
            "post_label_mechanism_audit_after_adr0106_before_any_live_partial_"
            "h32_verifier_timing"
        ),
        "seed": 20260820,
        "axis_seed": 20260819,
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "wide_hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "target_shifts": [
            "local_blocker_seat3_x2",
            "all_seat_strength_1_to2",
        ],
        "local_blocker_target_seat": 3,
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
        "acceptance_guard_normalized": 1e-10,
        "delta_comparison_tolerance": 1e-15,
        "seeded_permutation_count": 64,
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
        raise ValueError("policy-verifier workload differs from ADR-0107")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")

    expected_gates = {
        "expected_target_rows": 4,
        "expected_candidate_rows_per_target": 13,
        "expected_live_candidate_rows": 52,
        "expected_live_seat_evaluations": 133,
        "expected_complete_candidate_rows": 13,
        "expected_order_variants_per_target": 67,
        "expected_information_sets": 6144,
        "expected_hand_action_entries": 12288,
        "expected_new_strategy_quality_labels": 0,
        "require_source_identity": True,
        "require_target_descriptor_identity": True,
        "require_teacher_union_identity": True,
        "require_policy_digest_identity": True,
        "maximum_seat_utility_error": 1e-9,
        "maximum_seat_best_response_error": 1e-9,
        "maximum_seat_deviation_gain_error": 1e-9,
        "maximum_complete_nash_conv_error": 1e-9,
        "maximum_complete_zero_sum_residual": 1e-9,
        "require_live_stop_simulation_identity": True,
        "require_stop_soundness": True,
        "require_live_selection_identity": True,
        "require_order_screen_selection_identity": True,
        "require_delta_width_finite": True,
        "minimum_pooled_calibrated_speedup": 1.5,
        "minimum_family_calibrated_speedup": 1.5,
        "minimum_structural_seat_call_speedup": 1.5,
        "minimum_calibration_ratio": 0.5,
        "maximum_calibration_ratio": 2.0,
        "maximum_candidate_seat_evaluation_ms": 60_000.0,
        "maximum_target_workspace_compile_ms": 30_000.0,
        "maximum_host_peak_numeric_bytes": 3_000_000_000,
        "maximum_gpu_pool_bytes": 4_000_000_000,
        "maximum_total_audit_seconds": 1_200.0,
    }
    gates = config["gates"]
    if (
        not isinstance(gates, dict)
        or set(gates) != _GATE_FIELDS
        or gates != expected_gates
    ):
        raise ValueError("policy-verifier gates differ from ADR-0107")
    return {
        **config,
        "range_families": tuple(config["range_families"]),
        "target_shifts": tuple(config["target_shifts"]),
        "candidate_order": tuple(config["candidate_order"]),
        "seat_order": tuple(config["seat_order"]),
        "gates": dict(gates),
    }


def _quality_error(first: dict[str, Any], second: dict[str, Any]) -> float:
    if first["policy_sha256"] != second["policy_sha256"]:
        return math.inf
    errors = [
        abs(float(first["nash_conv"]) - float(second["nash_conv"])),
        abs(
            float(first["normalized_nash_conv"])
            - float(second["normalized_nash_conv"])
        ),
    ]
    for field in ("utilities", "best_response_values", "deviation_gains"):
        errors.extend(
            abs(float(left) - float(right))
            for left, right in zip(first[field], second[field], strict=True)
        )
    return max(errors)


def _teacher_union(
    targets: tuple[tuple[str, dict[str, Any]], ...],
    *,
    maximum_duplicate_error: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    duplicates = 0
    maximum_error = 0.0
    for source_id, target in targets:
        for candidate in target["candidates"]:
            digest = candidate["quality"]["policy_sha256"]
            if digest not in merged:
                merged[digest] = {
                    "candidate_id": candidate["candidate_id"],
                    "quality": dict(candidate["quality"]),
                    "source_refs": [f"{source_id}:{candidate['candidate_id']}"],
                }
                continue
            duplicates += 1
            error = _quality_error(merged[digest]["quality"], candidate["quality"])
            maximum_error = max(maximum_error, error)
            if error > maximum_duplicate_error:
                raise ValueError("teacher duplicate policy quality differs")
            merged[digest]["source_refs"].append(
                f"{source_id}:{candidate['candidate_id']}"
            )
    return list(merged.values()), {
        "input_rows": len(merged) + duplicates,
        "unique_policies": len(merged),
        "duplicate_rows": duplicates,
        "maximum_duplicate_quality_error": maximum_error,
    }


def reconstruct_candidate_policies(
    *,
    family: str,
    acceptance_target: dict[str, Any],
    candidate_target: dict[str, Any],
    ladder_source: dict[str, Any],
    extension_source: dict[str, Any],
    candidate_order: tuple[str, ...],
) -> tuple[
    dict[str, dict[str, float]],
    list[dict[str, Any]],
    bool,
]:
    """Rebuild all 13 union policies without rerunning search."""

    average32, current48, blueprint, source_identity = _source_policies(
        ladder_source,
        extension_source,
        family=family,
    )
    states = {
        iteration: _acceptance_state(acceptance_target, iteration=iteration)
        for iteration in (1, 2, 4)
    }
    state8 = candidate_target["final_state"]
    if (
        axis_cfr_checkpoint_digest(state8) != state8["state_sha256"]
        or int(state8["iteration"]) != 8
    ):
        raise ValueError("candidate-stream final state identity rejected")
    currents = {
        iteration: _current_policy_from_state(state)
        for iteration, state in (*states.items(), (8, state8))
    }
    averages = {
        iteration: _average_policy_from_state(state)
        for iteration, state in (*states.items(), (8, state8))
    }
    policies = {
        "control_average32": average32,
        "control_current48": current48,
        "search_average1": averages[1],
        "search_average2": averages[2],
        "search_average4": averages[4],
        "search_current1": currents[1],
        "search_current2": currents[2],
        "search_current4": currents[4],
        "search_current8": currents[8],
        "search_average8": averages[8],
        "interpolate_current1_to2_alpha025": interpolate_behavioral_policy(
            currents[1], currents[2], 0.25
        ),
        "interpolate_current1_to2_alpha050": interpolate_behavioral_policy(
            currents[1], currents[2], 0.50
        ),
        "interpolate_current1_to2_alpha075": interpolate_behavioral_policy(
            currents[1], currents[2], 0.75
        ),
    }
    if tuple(policies) != candidate_order:
        raise AssertionError("reconstructed candidate order differs from ADR-0107")
    rows = [
        {
            "candidate_id": candidate_id,
            "policy": policies[candidate_id],
            "policy_sha256": policy_digest(policies[candidate_id]),
        }
        for candidate_id in candidate_order
    ]
    return blueprint, rows, source_identity


def _replay_target(
    replay: dict[str, Any],
    *,
    family: str,
    shift: str,
) -> dict[str, Any]:
    return next(
        target
        for target in replay["targets"]
        if target["range_family"] == family and target["target_shift"] == shift
    )


def _blueprint_candidate(quality: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": "blueprint_average64",
        "aliases": ["blueprint_average64"],
        "source_refs": ["source:blueprint"],
        "quality": {
            "policy_sha256": quality["policy_sha256"],
            "nash_conv": float(quality["nash_conv"]),
            "normalized_nash_conv": float(quality["normalized_nash_conv"]),
            "deviation_gains": [float(value) for value in quality["deviation_gains"]],
        },
    }


def _selector_candidate(candidate_id: str, quality: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "aliases": [candidate_id],
        "source_refs": [f"live:{candidate_id}"],
        "quality": {
            "policy_sha256": quality["policy_sha256"],
            "nash_conv": float(quality["nash_conv"]),
            "normalized_nash_conv": float(quality["normalized_nash_conv"]),
            "deviation_gains": [float(value) for value in quality["deviation_gains"]],
        },
    }


def _live_teacher_errors(
    live: dict[str, Any],
    teacher: dict[str, Any],
) -> dict[str, float]:
    utility_error = 0.0
    response_error = 0.0
    gain_error = 0.0
    for row in live["seat_rows"]:
        seat = int(row["target_player"])
        utility_error = max(
            utility_error,
            abs(float(row["profile_utility"]) - float(teacher["utilities"][seat])),
        )
        response_error = max(
            response_error,
            abs(
                float(row["best_response_value"])
                - float(teacher["best_response_values"][seat])
            ),
        )
        gain_error = max(
            gain_error,
            abs(float(row["deviation_gain"]) - float(teacher["deviation_gains"][seat])),
        )
    nash_error = 0.0
    if live["complete"]:
        nash_error = abs(
            float(live["quality"]["nash_conv"]) - float(teacher["nash_conv"])
        )
    return {
        "maximum_utility_error": utility_error,
        "maximum_best_response_error": response_error,
        "maximum_deviation_gain_error": gain_error,
        "complete_nash_conv_error": nash_error,
    }


def _target_core_descriptor(descriptor: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in descriptor.items()
        if key
        not in {
            "source_partition",
            "target_partition",
            "target_to_source_partition_ratio",
            "marginal_total_variations",
            "mean_marginal_total_variation",
            "maximum_marginal_total_variation",
            "marginal_measurement_ms",
        }
    }


def _run_target(
    *,
    parsed: dict[str, Any],
    family: str,
    shift: str,
    target_index: int,
    board: tuple[int, ...],
    source_belief: Any,
    source_workspace: OpenModeFactorTTWorkspace,
    topology: Any,
    sparse: Any,
    automata: Any,
    gpu: Any,
    replay: dict[str, Any],
    acceptance: dict[str, Any],
    candidate_source: dict[str, Any],
    interpolation: dict[str, Any],
    ladder: dict[str, Any],
    extension: dict[str, Any],
) -> dict[str, Any]:
    acceptance_target = _source_target(acceptance, family=family, shift=shift)
    candidate_target = _source_target(candidate_source, family=family, shift=shift)
    interpolation_target = _source_target(interpolation, family=family, shift=shift)
    replay_target = _replay_target(replay, family=family, shift=shift)
    target_belief, live_descriptor = build_target_belief(
        source_belief,
        board=board,
        shift=shift,
        local_blocker_target_seat=parsed["local_blocker_target_seat"],
    )
    target_compile_started = time.perf_counter()
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        target_belief,
        query_chunk_records=parsed["query_chunk_records"],
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    target_compile_ms = (time.perf_counter() - target_compile_started) * 1000.0

    descriptor_identity = all(
        _target_core_descriptor(source["target_descriptor"])
        == _target_core_descriptor(live_descriptor)
        for source in (acceptance_target, candidate_target, interpolation_target)
    )
    descriptor_identity = descriptor_identity and (
        _descriptor_digest(acceptance_target["target_descriptor"])
        == replay_target["target_descriptor_sha256"]
    )

    teacher, merge = _teacher_union(
        (
            ("adr0099", acceptance_target),
            ("adr0101", candidate_target),
            ("adr0103", interpolation_target),
        ),
        maximum_duplicate_error=1e-15,
    )
    teacher_by_id = {row["candidate_id"]: row for row in teacher}
    teacher_union_identity = (
        tuple(teacher_by_id) == parsed["candidate_order"]
        and len(teacher) == parsed["gates"]["expected_candidate_rows_per_target"]
        and [row["quality"]["policy_sha256"] for row in teacher]
        == [
            row["policy_sha256"]
            for row in replay_target["pools"]["full_measured_union"][
                "candidate_rows"
            ]
        ]
    )
    blueprint_policy, policies, source_policy_identity = reconstruct_candidate_policies(
        family=family,
        acceptance_target=acceptance_target,
        candidate_target=candidate_target,
        ladder_source=ladder,
        extension_source=extension,
        candidate_order=parsed["candidate_order"],
    )
    blueprint_quality = dict(acceptance_target["blueprint_quality"])
    blueprint = _blueprint_candidate(blueprint_quality)
    policy_digest_identity = (
        source_policy_identity
        and policy_digest(blueprint_policy) == blueprint_quality["policy_sha256"]
        and all(
            row["policy_sha256"]
            == teacher_by_id[row["candidate_id"]]["quality"]["policy_sha256"]
            for row in policies
        )
    )

    raw_guard = parsed["acceptance_guard_normalized"] * parsed["stack"]
    teacher_candidates = [
        {
            "candidate_id": row["candidate_id"],
            "quality": {
                "policy_sha256": row["quality"]["policy_sha256"],
                "nash_conv": float(row["quality"]["nash_conv"]),
                "normalized_nash_conv": float(row["quality"]["normalized_nash_conv"]),
                "deviation_gains": [
                    float(value) for value in row["quality"]["deviation_gains"]
                ],
            },
        }
        for row in teacher
    ]
    canonical_simulation = simulate_fixed_envelope_verifier(
        blueprint,
        teacher_candidates,
        seat_order=parsed["seat_order"],
        raw_guard=raw_guard,
    )
    simulated_by_id = {
        row["candidate_id"]: row for row in canonical_simulation["candidate_rows"]
    }

    live_rows = []
    delta_rows = []
    completed = []
    best_complete = float(blueprint_quality["nash_conv"])
    blueprint_gains = tuple(float(value) for value in blueprint_quality["deviation_gains"])
    maximum_utility_error = 0.0
    maximum_response_error = 0.0
    maximum_gain_error = 0.0
    maximum_nash_error = 0.0
    maximum_zero_sum = 0.0
    stop_soundness = True
    stop_simulation_identity = True
    for policy_row in policies:
        candidate_id = policy_row["candidate_id"]
        teacher_row = teacher_by_id[candidate_id]
        delta_started = time.perf_counter()
        delta = leaf_policy_delta_width_screen(
            layout=topology,
            workspace=workspace,
            baseline_policy=blueprint_policy,
            candidate_policy=policy_row["policy"],
            terminal_automata=automata,
            hands_by_player=target_belief.hands_by_player,
            comparison_tolerance=parsed["delta_comparison_tolerance"],
        )
        delta["candidate_id"] = candidate_id
        delta["planning_ms"] = (time.perf_counter() - delta_started) * 1000.0
        delta_rows.append(delta)

        live = verify_leaf_adjoint_candidate(
            candidate_id=candidate_id,
            layout=topology,
            workspace=workspace,
            sparse=sparse,
            policy=policy_row["policy"],
            terminal_automata=automata,
            hands_by_player=target_belief.hands_by_player,
            blueprint_deviation_gains=blueprint_gains,
            best_complete_nash_conv=best_complete,
            payoff_span=parsed["stack"],
            raw_guard=raw_guard,
            seat_order=parsed["seat_order"],
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
            cupy_sparse=gpu,
        )
        errors = _live_teacher_errors(live, teacher_row["quality"])
        live["teacher_errors"] = errors
        expected = simulated_by_id[candidate_id]
        live["simulation_identity"] = (
            live["evaluated_seats"] == expected["evaluated_seats"]
            and live["stop_reason"] == expected["stop_reason"]
            and live["stop_seat"] == expected["stop_seat"]
            and live["complete"] == expected["complete"]
        )
        stop_simulation_identity = (
            stop_simulation_identity and live["simulation_identity"]
        )
        if live["stop_reason"] == "blueprint_cap":
            seat = int(live["stop_seat"])
            stop_soundness = stop_soundness and (
                float(live["seat_rows"][-1]["deviation_gain"])
                > blueprint_gains[seat] + raw_guard
            )
        elif live["stop_reason"] == "objective_lower_bound":
            stop_soundness = stop_soundness and (
                float(live["partial_nash_conv"]) > best_complete + raw_guard
            )
        if live["complete"]:
            selector_row = _selector_candidate(candidate_id, live["quality"])
            completed.append(selector_row)
            best_complete = min(best_complete, float(live["quality"]["nash_conv"]))
            maximum_zero_sum = max(
                maximum_zero_sum,
                float(live["quality"]["zero_sum_residual"]),
            )
        maximum_utility_error = max(
            maximum_utility_error, errors["maximum_utility_error"]
        )
        maximum_response_error = max(
            maximum_response_error, errors["maximum_best_response_error"]
        )
        maximum_gain_error = max(
            maximum_gain_error, errors["maximum_deviation_gain_error"]
        )
        maximum_nash_error = max(
            maximum_nash_error, errors["complete_nash_conv_error"]
        )
        live_rows.append(live)

    live_selection = select_fixed_blueprint_envelope(
        blueprint,
        completed,
        raw_guard=raw_guard,
    )
    recorded_selection = replay_target["pools"]["full_measured_union"][
        "fixed_envelope"
    ]["canonical"]
    live_selection_identity = (
        live_selection["selected_policy_sha256"]
        == recorded_selection["selected_policy_sha256"]
        == canonical_simulation["selection"]["selected_policy_sha256"]
    )

    order_rows = []
    for order_id, ordered in _order_rows(
        teacher_candidates,
        seed=parsed["seed"] + 1000 * target_index,
        seeded_permutation_count=parsed["seeded_permutation_count"],
    ):
        simulated = simulate_fixed_envelope_verifier(
            blueprint,
            ordered,
            seat_order=parsed["seat_order"],
            raw_guard=raw_guard,
        )
        order_rows.append(
            {
                "order_id": order_id,
                "evaluated_seat_count": simulated["evaluated_seat_count"],
                "complete_candidate_count": simulated["complete_candidate_count"],
                "selected_policy_sha256": simulated["selection"][
                    "selected_policy_sha256"
                ],
                "selected_candidate_id": simulated["selection"][
                    "selected_candidate_id"
                ],
            }
        )
    order_selection_identity = all(
        row["selected_policy_sha256"] == recorded_selection["selected_policy_sha256"]
        for row in order_rows
    )

    source_full_bill_ms = math.fsum(
        float(row["quality"]["wall_ms"]) for row in teacher
    )
    live_bill_ms = math.fsum(float(row["wall_ms"]) for row in live_rows)
    calibration_live = next(
        row for row in live_rows if row["candidate_id"] == "search_average1"
    )
    calibration_source = float(
        teacher_by_id["search_average1"]["quality"]["wall_ms"]
    )
    calibration_ratio = float(calibration_live["wall_ms"]) / calibration_source
    calibrated_full_bill_ms = source_full_bill_ms * calibration_ratio
    structural_seat_speedup = (
        len(teacher) * parsed["players"]
        / sum(int(row["evaluated_seat_count"]) for row in live_rows)
    )
    information_sets = sum(
        parsed["wide_hands_per_player"]
        for node in topology.nodes
        if node.player >= 0
    )
    hand_action_entries = sum(
        len(node.actions) * parsed["wide_hands_per_player"]
        for node in topology.nodes
        if node.player >= 0
    )
    return {
        "range_family": family,
        "target_shift": shift,
        "target_descriptor_identity": descriptor_identity,
        "target_partition": workspace.base.partition,
        "target_workspace_compile_ms": target_compile_ms,
        "information_sets": information_sets,
        "hand_action_entries": hand_action_entries,
        "teacher_merge": merge,
        "teacher_union_identity": teacher_union_identity,
        "policy_digest_identity": policy_digest_identity,
        "blueprint_policy_sha256": blueprint_quality["policy_sha256"],
        "recorded_selected_policy_sha256": recorded_selection[
            "selected_policy_sha256"
        ],
        "recorded_selected_candidate_id": recorded_selection[
            "selected_candidate_id"
        ],
        "live_selection": live_selection,
        "live_selection_identity": live_selection_identity,
        "live_candidate_rows": live_rows,
        "delta_width_rows": delta_rows,
        "canonical_simulation": canonical_simulation,
        "live_stop_simulation_identity": stop_simulation_identity,
        "stop_soundness": stop_soundness,
        "order_screen": {
            "rows": order_rows,
            "selection_identity": order_selection_identity,
            "minimum_evaluated_seats": min(
                row["evaluated_seat_count"] for row in order_rows
            ),
            "median_evaluated_seats": statistics.median(
                row["evaluated_seat_count"] for row in order_rows
            ),
            "maximum_evaluated_seats": max(
                row["evaluated_seat_count"] for row in order_rows
            ),
        },
        "correctness": {
            "maximum_utility_error": maximum_utility_error,
            "maximum_best_response_error": maximum_response_error,
            "maximum_deviation_gain_error": maximum_gain_error,
            "maximum_complete_nash_conv_error": maximum_nash_error,
            "maximum_complete_zero_sum_residual": maximum_zero_sum,
        },
        "economics": {
            "source_full_candidate_bill_ms": source_full_bill_ms,
            "live_partial_verifier_bill_ms": live_bill_ms,
            "calibration_candidate_id": "search_average1",
            "calibration_source_full_ms": calibration_source,
            "calibration_live_full_ms": float(calibration_live["wall_ms"]),
            "calibration_ratio": calibration_ratio,
            "calibrated_full_candidate_bill_ms": calibrated_full_bill_ms,
            "raw_historical_speedup": source_full_bill_ms / live_bill_ms,
            "calibrated_speedup": calibrated_full_bill_ms / live_bill_ms,
            "structural_seat_call_speedup": structural_seat_speedup,
            "live_seat_evaluations": sum(
                int(row["evaluated_seat_count"]) for row in live_rows
            ),
            "full_seat_evaluations": len(teacher) * parsed["players"],
            "complete_candidate_rows": sum(bool(row["complete"]) for row in live_rows),
        },
    }


def _run_family(
    *,
    parsed: dict[str, Any],
    family: str,
    family_index: int,
    board: tuple[int, ...],
    replay: dict[str, Any],
    acceptance: dict[str, Any],
    candidate_source: dict[str, Any],
    interpolation: dict[str, Any],
    ladder: dict[str, Any],
    extension: dict[str, Any],
) -> dict[str, Any]:
    source_belief, topology, sparse, retained = _build_case(
        parsed=parsed,
        board=board,
        hand_count=parsed["wide_hands_per_player"],
        family=family,
    )
    source_workspace, workspace_timing, automata = retained
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    targets = []
    for shift_index, shift in enumerate(parsed["target_shifts"]):
        targets.append(
            _run_target(
                parsed=parsed,
                family=family,
                shift=shift,
                target_index=family_index * len(parsed["target_shifts"]) + shift_index,
                board=board,
                source_belief=source_belief,
                source_workspace=source_workspace,
                topology=topology,
                sparse=sparse,
                automata=automata,
                gpu=gpu,
                replay=replay,
                acceptance=acceptance,
                candidate_source=candidate_source,
                interpolation=interpolation,
                ladder=ladder,
                extension=extension,
            )
        )
        gc.collect()
    return {
        "range_family": family,
        "source_workspace_timing": workspace_timing,
        "gpu_operator_upload_ms": gpu.upload_ms,
        "targets": targets,
    }


def run_h32_policy_delta_verifier_audit(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Execute the frozen ADR-0107 h32 verifier audit."""

    parsed = parse_h32_policy_delta_verifier_config(config)
    import scipy

    cp, _ = _cupy_modules()
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0107")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0107")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0107")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0107")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0107 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed["required_compute_capability"]:
        raise ValueError("GPU compute capability differs from ADR-0107")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")

    replay = json.loads(_REPLAY_SOURCE.read_text(encoding="utf-8"))
    acceptance = json.loads(_ACCEPTANCE_SOURCE.read_text(encoding="utf-8"))
    candidate_source = json.loads(_CANDIDATE_SOURCE.read_text(encoding="utf-8"))
    interpolation = json.loads(_INTERPOLATION_SOURCE.read_text(encoding="utf-8"))
    ladder = json.loads(_LADDER_SOURCE.read_text(encoding="utf-8"))
    extension = json.loads(_EXTENSION_SOURCE.read_text(encoding="utf-8"))
    width = json.loads(_WIDTH_SOURCE.read_text(encoding="utf-8"))
    source_identity = (
        replay["status"] == "frozen_semantics_audit_executed"
        and bool(replay["gates"]["passed"])
        and acceptance["status"] == "frozen_audit_executed"
        and bool(acceptance["gates"]["passed"])
        and candidate_source["status"] == "frozen_audit_executed"
        and bool(candidate_source["gates"]["passed"])
        and interpolation["status"] == "frozen_audit_executed"
        and bool(interpolation["gates"]["passed"])
        and int(width["aggregate"]["selected_width"])
        == parsed["maximum_feature_width_per_batch"]
    )
    if not source_identity:
        raise ValueError("ADR-0107 source identity rejected")

    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    family_rows = []
    for family_index, family in enumerate(parsed["range_families"]):
        release_cupy_memory_pool()
        gc.collect()
        family_rows.append(
            _run_family(
                parsed=parsed,
                family=family,
                family_index=family_index,
                board=board,
                replay=replay,
                acceptance=acceptance,
                candidate_source=candidate_source,
                interpolation=interpolation,
                ladder=ladder,
                extension=extension,
            )
        )
    targets = [target for family in family_rows for target in family["targets"]]
    live_rows = [row for target in targets for row in target["live_candidate_rows"]]
    delta_rows = [row for target in targets for row in target["delta_width_rows"]]
    total_seconds = time.perf_counter() - started
    gates_config = parsed["gates"]
    family_speedups = {
        family_row["range_family"]: (
            math.fsum(
                target["economics"]["calibrated_full_candidate_bill_ms"]
                for target in family_row["targets"]
            )
            / math.fsum(
                target["economics"]["live_partial_verifier_bill_ms"]
                for target in family_row["targets"]
            )
        )
        for family_row in family_rows
    }
    pooled_calibrated_speedup = (
        math.fsum(
            target["economics"]["calibrated_full_candidate_bill_ms"]
            for target in targets
        )
        / math.fsum(
            target["economics"]["live_partial_verifier_bill_ms"]
            for target in targets
        )
    )
    structural_speedup = (
        len(live_rows) * parsed["players"]
        / sum(int(row["evaluated_seat_count"]) for row in live_rows)
    )
    calibration_ratios = [
        target["economics"]["calibration_ratio"] for target in targets
    ]
    delta_finite = all(
        math.isfinite(float(row[key]))
        for row in delta_rows
        for key in (
            "optimistic_delta_to_value_width_ratio",
            "optimistic_delta_to_existing_width_ratio",
            "planning_ms",
        )
    )
    maximum_seat_wall = max(
        float(seat["wall_ms"])
        for row in live_rows
        for seat in row["seat_rows"]
    )
    maximum_host = max(int(row["maximum_host_peak_numeric_bytes"]) for row in live_rows)
    maximum_gpu = max(int(row["maximum_gpu_pool_bytes"]) for row in live_rows)
    gates = {
        "source_identity": source_identity == gates_config["require_source_identity"],
        "target_rows": len(targets) == gates_config["expected_target_rows"],
        "candidate_rows": all(
            len(target["live_candidate_rows"])
            == gates_config["expected_candidate_rows_per_target"]
            for target in targets
        )
        and len(live_rows) == gates_config["expected_live_candidate_rows"],
        "live_seat_evaluations": sum(
            int(row["evaluated_seat_count"]) for row in live_rows
        )
        == gates_config["expected_live_seat_evaluations"],
        "complete_candidate_rows": sum(bool(row["complete"]) for row in live_rows)
        == gates_config["expected_complete_candidate_rows"],
        "order_variant_rows": all(
            len(target["order_screen"]["rows"])
            == gates_config["expected_order_variants_per_target"]
            for target in targets
        ),
        "information_schema": all(
            target["information_sets"] == gates_config["expected_information_sets"]
            and target["hand_action_entries"]
            == gates_config["expected_hand_action_entries"]
            for target in targets
        ),
        "zero_new_strategy_quality_labels": gates_config[
            "expected_new_strategy_quality_labels"
        ]
        == 0,
        "target_descriptor_identity": all(
            target["target_descriptor_identity"] for target in targets
        )
        == gates_config["require_target_descriptor_identity"],
        "teacher_union_identity": all(
            target["teacher_union_identity"] for target in targets
        )
        == gates_config["require_teacher_union_identity"],
        "policy_digest_identity": all(
            target["policy_digest_identity"] for target in targets
        )
        == gates_config["require_policy_digest_identity"],
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
        "live_stop_simulation_identity": all(
            target["live_stop_simulation_identity"] for target in targets
        )
        == gates_config["require_live_stop_simulation_identity"],
        "stop_soundness": all(target["stop_soundness"] for target in targets)
        == gates_config["require_stop_soundness"],
        "live_selection_identity": all(
            target["live_selection_identity"] for target in targets
        )
        == gates_config["require_live_selection_identity"],
        "order_screen_selection_identity": all(
            target["order_screen"]["selection_identity"] for target in targets
        )
        == gates_config["require_order_screen_selection_identity"],
        "delta_width_finite": delta_finite
        == gates_config["require_delta_width_finite"],
        "pooled_calibrated_speedup": pooled_calibrated_speedup
        >= gates_config["minimum_pooled_calibrated_speedup"],
        "family_calibrated_speedup": all(
            value >= gates_config["minimum_family_calibrated_speedup"]
            for value in family_speedups.values()
        ),
        "structural_seat_call_speedup": structural_speedup
        >= gates_config["minimum_structural_seat_call_speedup"],
        "calibration_ratio": min(calibration_ratios)
        >= gates_config["minimum_calibration_ratio"]
        and max(calibration_ratios) <= gates_config["maximum_calibration_ratio"],
        "candidate_seat_evaluation_ms": maximum_seat_wall
        <= gates_config["maximum_candidate_seat_evaluation_ms"],
        "target_workspace_compile_ms": max(
            target["target_workspace_compile_ms"] for target in targets
        )
        <= gates_config["maximum_target_workspace_compile_ms"],
        "host_peak_numeric_bytes": maximum_host
        <= gates_config["maximum_host_peak_numeric_bytes"],
        "gpu_pool_bytes": maximum_gpu <= gates_config["maximum_gpu_pool_bytes"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    delta_ratios = [
        float(row["optimistic_delta_to_existing_width_ratio"])
        for row in delta_rows
    ]
    return {
        "schema_version": 1,
        "status": "frozen_audit_executed",
        "experiment_type": "h32_policy_delta_width_and_partial_vector_verifier",
        "config": config,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {
            field: _sha256(path) for field, path in _SOURCE_PATHS.items()
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
        "family_rows": family_rows,
        "counts": {
            "target_rows": len(targets),
            "candidate_rows": len(live_rows),
            "delta_width_rows": len(delta_rows),
            "live_seat_evaluations": sum(
                int(row["evaluated_seat_count"]) for row in live_rows
            ),
            "complete_candidate_rows": sum(bool(row["complete"]) for row in live_rows),
            "new_strategy_quality_labels": 0,
        },
        "aggregate": {
            "pooled_calibrated_speedup": pooled_calibrated_speedup,
            "family_calibrated_speedups": family_speedups,
            "structural_seat_call_speedup": structural_speedup,
            "calibration_ratio_minimum": min(calibration_ratios),
            "calibration_ratio_median": statistics.median(calibration_ratios),
            "calibration_ratio_maximum": max(calibration_ratios),
            "source_full_candidate_bill_ms": math.fsum(
                target["economics"]["source_full_candidate_bill_ms"]
                for target in targets
            ),
            "calibrated_full_candidate_bill_ms": math.fsum(
                target["economics"]["calibrated_full_candidate_bill_ms"]
                for target in targets
            ),
            "live_partial_verifier_bill_ms": math.fsum(
                target["economics"]["live_partial_verifier_bill_ms"]
                for target in targets
            ),
            "delta_optimistic_existing_width_ratio_minimum": min(delta_ratios),
            "delta_optimistic_existing_width_ratio_median": statistics.median(
                delta_ratios
            ),
            "delta_optimistic_existing_width_ratio_maximum": max(delta_ratios),
            "delta_rows_narrower_than_existing_full": sum(
                ratio < 1.0 for ratio in delta_ratios
            ),
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
            "maximum_candidate_seat_evaluation_ms": maximum_seat_wall,
            "maximum_host_peak_numeric_bytes": maximum_host,
            "maximum_gpu_pool_bytes": maximum_gpu,
        },
        "gates": gates,
        "timing": {"total_audit_seconds": total_seconds},
        "limitations": [
            "This post-label mechanism audit creates no new strategy-quality labels.",
            (
                "The live speed comparison calibrates historical full-profile bills "
                "with one complete average-one control per target rather than "
                "rerunning every omitted seat."
            ),
            (
                "Early stopping accelerates a candidate portfolio; every selected "
                "cap-feasible policy still requires all six exact seats."
            ),
            (
                "The delta screen counts an exact ordered-seat representation but "
                "does not time a signed h32 delta contraction."
            ),
            "Blueprint caps certify unilateral deviations, not coalition safety.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_h32_policy_delta_verifier_audit(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "h32 policy-delta verifier audit: "
        f"passed={result['gates']['passed']} "
        f"seat_calls={result['counts']['live_seat_evaluations']} "
        f"speedup={result['aggregate']['pooled_calibrated_speedup']:.3f} "
        f"seconds={result['timing']['total_audit_seconds']:.3f}"
    )
    return 0 if result["gates"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
