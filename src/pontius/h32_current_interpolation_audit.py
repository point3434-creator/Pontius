"""Test fixed behavioral interpolations between h32 warm current 1 and 2."""

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

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .h32_warm_candidate_stream_audit import (
    _descriptor_digest,
    _evaluate_policy,
    _portfolio_row,
    _quality_finite,
    _source_target,
)
from .h32_warm_search_acceptance_audit import (
    _current_policy_from_state,
    _root_marginals,
    build_target_belief,
    compare_acceptance,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import (
    mean_policy_total_variation,
    policy_digest,
    policy_statistics,
)
from .reporting import environment_metadata
from .river import parse_cards


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-current-interpolation-audit-v1.json"
)
_CANDIDATE_SOURCE = (
    _ROOT / "experiments" / "results" / "h32-warm-candidate-stream-v1.json"
)
_ACCEPTANCE_SOURCE = (
    _ROOT / "experiments" / "results" / "h32-warm-search-acceptance-v1.json"
)
_SHIFTED_H4_CONTROL = (
    _ROOT
    / "experiments"
    / "results"
    / "h4-shifted-belief-dense-crosscheck-v1.json"
)
_WIDTH_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-batch-width-audit-v2.json"
)
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "axis_seed",
    "expected_candidate_stream_source_sha256",
    "expected_acceptance_source_sha256",
    "expected_shifted_h4_control_sha256",
    "expected_width_source_sha256",
    "expected_requirements_sha256",
    "expected_axis_checkpoint_sha256",
    "expected_base_ladder_implementation_sha256",
    "expected_candidate_stream_implementation_sha256",
    "expected_acceptance_implementation_sha256",
    "expected_leaf_adjoint_cfr_sha256",
    "expected_leaf_adjoint_evaluation_sha256",
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
    "endpoint_iterations",
    "interpolation_alphas",
    "candidate_order",
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
_GATE_FIELDS = {
    "expected_target_rows",
    "expected_target_rows_per_family",
    "expected_new_quality_evaluations_per_target",
    "expected_candidate_rows_per_target",
    "expected_wide_information_sets",
    "expected_wide_hand_action_entries",
    "expected_sparse_batches_by_family",
    "require_candidate_stream_source_identity",
    "require_acceptance_source_identity",
    "require_target_descriptor_identity",
    "require_endpoint_policy_digest_identity",
    "require_interpolation_normalization",
    "maximum_interpolation_endpoint_error",
    "require_incumbent_nonworsening",
    "require_incumbent_guard_semantics",
    "maximum_quality_evaluation_ms",
    "maximum_target_workspace_compile_ms",
    "maximum_host_peak_numeric_bytes",
    "maximum_gpu_pool_bytes",
    "maximum_quality_zero_sum_residual",
    "require_finite_policies_and_quality",
    "maximum_total_audit_seconds",
}
_SOURCE_PATHS = {
    "expected_candidate_stream_source_sha256": _CANDIDATE_SOURCE,
    "expected_acceptance_source_sha256": _ACCEPTANCE_SOURCE,
    "expected_shifted_h4_control_sha256": _SHIFTED_H4_CONTROL,
    "expected_width_source_sha256": _WIDTH_SOURCE,
    "expected_requirements_sha256": (
        _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
    ),
    "expected_axis_checkpoint_sha256": (
        _ROOT / "src" / "pontius" / "axis_cfr_checkpoint.py"
    ),
    "expected_base_ladder_implementation_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_checkpoint_ladder_audit.py"
    ),
    "expected_candidate_stream_implementation_sha256": (
        _ROOT / "src" / "pontius" / "h32_warm_candidate_stream_audit.py"
    ),
    "expected_acceptance_implementation_sha256": (
        _ROOT / "src" / "pontius" / "h32_warm_search_acceptance_audit.py"
    ),
    "expected_leaf_adjoint_cfr_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_cfr.py"
    ),
    "expected_leaf_adjoint_evaluation_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_evaluation.py"
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


def parse_h32_current_interpolation_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the immutable ADR-0103 interpolation protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "interpolation fields differ from ADR-0103: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0102_before_any_h32_current1_to2_"
            "interior_interpolation_quality"
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
        "endpoint_iterations": [1, 2],
        "interpolation_alphas": [0.25, 0.5, 0.75],
        "candidate_order": [
            "search_current1",
            "interpolate_current1_to2_alpha025",
            "interpolate_current1_to2_alpha050",
            "interpolate_current1_to2_alpha075",
            "search_current2",
        ],
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
        raise ValueError("interpolation workload differs from ADR-0103")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")
    expected_gates = {
        "expected_target_rows": 4,
        "expected_target_rows_per_family": 2,
        "expected_new_quality_evaluations_per_target": 3,
        "expected_candidate_rows_per_target": 5,
        "expected_wide_information_sets": 6144,
        "expected_wide_hand_action_entries": 12288,
        "expected_sparse_batches_by_family": {
            "balanced": 435,
            "blocker_heavy": 311,
        },
        "require_candidate_stream_source_identity": True,
        "require_acceptance_source_identity": True,
        "require_target_descriptor_identity": True,
        "require_endpoint_policy_digest_identity": True,
        "require_interpolation_normalization": True,
        "maximum_interpolation_endpoint_error": 1e-15,
        "require_incumbent_nonworsening": True,
        "require_incumbent_guard_semantics": True,
        "maximum_quality_evaluation_ms": 60_000.0,
        "maximum_target_workspace_compile_ms": 30_000.0,
        "maximum_host_peak_numeric_bytes": 3_000_000_000,
        "maximum_gpu_pool_bytes": 4_000_000_000,
        "maximum_quality_zero_sum_residual": 1e-9,
        "require_finite_policies_and_quality": True,
        "maximum_total_audit_seconds": 900.0,
    }
    gates = config["gates"]
    if (
        not isinstance(gates, dict)
        or set(gates) != _GATE_FIELDS
        or gates != expected_gates
    ):
        raise ValueError("interpolation gates differ from ADR-0103")
    return {
        **config,
        "range_families": tuple(config["range_families"]),
        "target_shifts": tuple(config["target_shifts"]),
        "endpoint_iterations": tuple(config["endpoint_iterations"]),
        "interpolation_alphas": tuple(config["interpolation_alphas"]),
        "candidate_order": tuple(config["candidate_order"]),
        "gates": {
            **gates,
            "expected_sparse_batches_by_family": dict(
                gates["expected_sparse_batches_by_family"]
            ),
        },
    }


def interpolate_behavioral_policy(
    first: dict[str, dict[str, float]],
    second: dict[str, dict[str, float]],
    alpha: float,
) -> dict[str, dict[str, float]]:
    """Pointwise behavioral mixture ``(1-alpha) first + alpha second``."""

    if not math.isfinite(alpha) or not 0.0 <= alpha <= 1.0:
        raise ValueError("behavioral interpolation alpha must lie in [0, 1]")
    if first.keys() != second.keys():
        raise ValueError("behavioral interpolation schemas differ")
    result = {}
    for key in first:
        if first[key].keys() != second[key].keys():
            raise ValueError("behavioral interpolation action schemas differ")
        row = {
            action: (1.0 - alpha) * float(first[key][action])
            + alpha * float(second[key][action])
            for action in first[key]
        }
        if any(not math.isfinite(value) or value < 0.0 for value in row.values()):
            raise ValueError("behavioral interpolation produced an invalid probability")
        total = math.fsum(row.values())
        if abs(total - 1.0) > 1e-12:
            raise ValueError("behavioral interpolation row is not normalized")
        result[key] = row
    return result


def _maximum_policy_error(
    first: dict[str, dict[str, float]],
    second: dict[str, dict[str, float]],
) -> float:
    if first.keys() != second.keys():
        return math.inf
    return max(
        abs(float(first[key][action]) - float(second[key][action]))
        for key in first
        for action in first[key]
    )


def _interpolation_diagnostics(
    policy: dict[str, dict[str, float]],
) -> dict[str, Any]:
    totals = [math.fsum(row.values()) for row in policy.values()]
    probabilities = [value for row in policy.values() for value in row.values()]
    return {
        "maximum_normalization_error": max(abs(value - 1.0) for value in totals),
        "minimum_probability": min(probabilities),
        "maximum_probability": max(probabilities),
        "finite_nonnegative": all(
            math.isfinite(value) and value >= 0.0 for value in probabilities
        ),
    }


def _candidate_source_row(
    source_target: dict[str, Any],
    candidate_id: str,
) -> dict[str, Any]:
    return next(
        row for row in source_target["candidates"] if row["candidate_id"] == candidate_id
    )


def _acceptance_state(
    acceptance_target: dict[str, Any],
    *,
    iteration: int,
) -> dict[str, Any]:
    candidate = next(
        row
        for row in acceptance_target["candidates"]
        if row["candidate_id"] == f"search_average{iteration}"
    )
    state = candidate["state"]
    if axis_cfr_checkpoint_digest(state) != state["state_sha256"]:
        raise ValueError("interpolation endpoint source state digest differs")
    return state


def _run_target(
    *,
    parsed: dict[str, Any],
    candidate_source: dict[str, Any],
    acceptance_source: dict[str, Any],
    family: str,
    shift: str,
    board: tuple[int, ...],
    source_belief: Any,
    topology: Any,
    source_workspace: OpenModeFactorTTWorkspace,
    sparse: Any,
    automata: Any,
    gpu: Any,
    source_marginals: tuple[np.ndarray, ...],
) -> dict[str, Any]:
    source_target = _source_target(candidate_source, family=family, shift=shift)
    acceptance_target = _source_target(
        acceptance_source,
        family=family,
        shift=shift,
    )
    target_belief, descriptor = build_target_belief(
        source_belief,
        board=board,
        shift=shift,
        local_blocker_target_seat=parsed["local_blocker_target_seat"],
    )
    compile_started = time.perf_counter()
    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        target_belief,
        query_chunk_records=parsed["query_chunk_records"],
    )
    target_workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    target_compile_ms = (time.perf_counter() - compile_started) * 1000.0
    target_marginals, marginal_ms = _root_marginals(
        target_workspace,
        sparse,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    marginal_tvs = [
        0.5 * float(np.sum(np.abs(source_value - target_value)))
        for source_value, target_value in zip(
            source_marginals,
            target_marginals,
            strict=True,
        )
    ]
    descriptor.update(
        {
            "source_partition": source_workspace.base.partition,
            "target_partition": target_workspace.base.partition,
            "target_to_source_partition_ratio": (
                target_workspace.base.partition / source_workspace.base.partition
            ),
            "marginal_total_variations": marginal_tvs,
            "mean_marginal_total_variation": math.fsum(marginal_tvs)
            / len(marginal_tvs),
            "maximum_marginal_total_variation": max(marginal_tvs),
            "marginal_measurement_ms": marginal_ms,
        }
    )
    descriptor_identity = _descriptor_digest(descriptor) == _descriptor_digest(
        source_target["target_descriptor"]
    )

    states = {
        iteration: _acceptance_state(acceptance_target, iteration=iteration)
        for iteration in parsed["endpoint_iterations"]
    }
    policies = {
        iteration: _current_policy_from_state(state)
        for iteration, state in states.items()
    }
    endpoint_rows = {
        iteration: _candidate_source_row(
            source_target,
            f"search_current{iteration}",
        )
        for iteration in parsed["endpoint_iterations"]
    }
    endpoint_policy_identity = all(
        policy_digest(policies[iteration])
        == states[iteration]["current_policy_sha256"]
        == endpoint_rows[iteration]["quality"]["policy_sha256"]
        for iteration in parsed["endpoint_iterations"]
    )
    first = policies[parsed["endpoint_iterations"][0]]
    second = policies[parsed["endpoint_iterations"][1]]
    endpoint_error = max(
        _maximum_policy_error(interpolate_behavioral_policy(first, second, 0.0), first),
        _maximum_policy_error(interpolate_behavioral_policy(first, second, 1.0), second),
    )
    baseline = dict(source_target["blueprint_quality"])
    payoff_span = float(topology.game.payoff_span)
    candidates_by_id = {}
    for iteration in parsed["endpoint_iterations"]:
        candidate_id = f"search_current{iteration}"
        source_row = endpoint_rows[iteration]
        candidates_by_id[candidate_id] = {
            "candidate_id": candidate_id,
            "policy_kind": "current_endpoint",
            "alpha": float(iteration - 1),
            "measurement_source": "ADR-0101-source",
            "cumulative_search_ms": float(source_row["cumulative_search_ms"]),
            "policy_statistics": dict(source_row["policy_statistics"]),
            "quality": dict(source_row["quality"]),
            "policy_sha256": source_row["quality"]["policy_sha256"],
            "interpolation_diagnostics": _interpolation_diagnostics(
                policies[iteration]
            ),
        }

    new_quality_rows = []
    interior_policies = {}
    search_ms = float(endpoint_rows[2]["cumulative_search_ms"])
    for alpha in parsed["interpolation_alphas"]:
        policy = interpolate_behavioral_policy(first, second, alpha)
        suffix = f"{int(round(alpha * 100)):03d}"
        candidate_id = f"interpolate_current1_to2_alpha{suffix}"
        quality = _evaluate_policy(
            topology=topology,
            workspace=target_workspace,
            sparse=sparse,
            automata=automata,
            gpu=gpu,
            hands_by_player=target_belief.hands_by_player,
            policy=policy,
            label=candidate_id,
            payoff_span=payoff_span,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
        )
        new_quality_rows.append(quality)
        interior_policies[alpha] = policy
        candidates_by_id[candidate_id] = {
            "candidate_id": candidate_id,
            "policy_kind": "behavioral_interpolation",
            "alpha": alpha,
            "measurement_source": "ADR-0103-live",
            "cumulative_search_ms": search_ms,
            "policy_statistics": policy_statistics(policy),
            "policy_distance_from_current1": mean_policy_total_variation(
                first,
                policy,
            ),
            "policy_distance_to_current2": mean_policy_total_variation(
                policy,
                second,
            ),
            "quality": quality,
            "policy_sha256": policy_digest(policy),
            "interpolation_diagnostics": _interpolation_diagnostics(policy),
        }

    candidates = [candidates_by_id[key] for key in parsed["candidate_order"]]
    for candidate in candidates:
        candidate["baseline_comparison"] = compare_acceptance(
            baseline,
            candidate["quality"],
            payoff_span=payoff_span,
            normalized_guard=parsed["acceptance_guard_normalized"],
        )
    portfolio = _portfolio_row(
        name="current1_to2_interpolation",
        baseline=baseline,
        candidates=candidates,
        payoff_span=payoff_span,
        guard=parsed["acceptance_guard_normalized"],
        target_compile_ms=target_compile_ms,
    )
    source_current1_value = float(
        source_target["portfolios"]["full_interleaved"][
            "final_unilateral_normalized_nash_conv"
        ]
    )
    final_value = float(portfolio["final_unilateral_normalized_nash_conv"])
    normalization = all(
        row["interpolation_diagnostics"]["finite_nonnegative"]
        and row["interpolation_diagnostics"]["maximum_normalization_error"]
        <= 1e-12
        and row["interpolation_diagnostics"]["minimum_probability"] >= 0.0
        and row["interpolation_diagnostics"]["maximum_probability"] <= 1.0 + 1e-12
        for row in candidates
    )
    finite = (
        all(_quality_finite(row["quality"]) for row in candidates)
        and normalization
        and all(
            math.isfinite(value)
            for policy in interior_policies.values()
            for row in policy.values()
            for value in row.values()
        )
    )
    return {
        "range_family": family,
        "target_shift": shift,
        "target_descriptor": descriptor,
        "target_descriptor_identity": descriptor_identity,
        "target_workspace_compile_ms": target_compile_ms,
        "information_sets": len(topology.information_schema())
        * parsed["wide_hands_per_player"],
        "hand_action_entries": sum(
            len(node.actions) * parsed["wide_hands_per_player"]
            for node in topology.nodes
            if node.player >= 0
        ),
        "endpoint_policy_digest_identity": endpoint_policy_identity,
        "maximum_interpolation_endpoint_error": endpoint_error,
        "interpolation_normalization": normalization,
        "blueprint_quality": baseline,
        "new_quality_evaluations": len(new_quality_rows),
        "candidates": candidates,
        "portfolio": portfolio,
        "source_current1_unilateral_normalized_nash_conv": source_current1_value,
        "incremental_unilateral_reduction_over_current1": (
            source_current1_value - final_value
        ),
        "finite_policies_and_quality": finite,
    }


def _run_family(
    *,
    parsed: dict[str, Any],
    candidate_source: dict[str, Any],
    acceptance_source: dict[str, Any],
    board: tuple[int, ...],
    family: str,
) -> dict[str, Any]:
    source_belief, topology, sparse, retained = _build_case(
        parsed=parsed,
        board=board,
        hand_count=parsed["wide_hands_per_player"],
        family=family,
    )
    source_workspace, workspace_timing, automata = retained
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    source_marginals, source_marginal_ms = _root_marginals(
        source_workspace,
        sparse,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    targets = []
    for shift in parsed["target_shifts"]:
        targets.append(
            _run_target(
                parsed=parsed,
                candidate_source=candidate_source,
                acceptance_source=acceptance_source,
                family=family,
                shift=shift,
                board=board,
                source_belief=source_belief,
                topology=topology,
                source_workspace=source_workspace,
                sparse=sparse,
                automata=automata,
                gpu=gpu,
                source_marginals=source_marginals,
            )
        )
        gc.collect()
    return {
        "range_family": family,
        "source_workspace_timing": workspace_timing,
        "source_marginal_measurement_ms": source_marginal_ms,
        "gpu_operator_upload_ms": gpu.upload_ms,
        "targets": targets,
    }


def run_h32_current_interpolation_audit(
    config: dict[str, Any],
) -> dict[str, Any]:
    parsed = parse_h32_current_interpolation_config(config)
    import scipy

    cupy_started = time.perf_counter()
    cp, _ = _cupy_modules()
    cupy_import_ms = (time.perf_counter() - cupy_started) * 1000.0
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0103")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0103")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0103")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0103")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0103 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed["required_compute_capability"]:
        raise ValueError("GPU compute capability differs from ADR-0103")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")

    width_source = json.loads(_WIDTH_SOURCE.read_text(encoding="utf-8"))
    if (
        int(width_source["aggregate"]["selected_width"])
        != parsed["maximum_feature_width_per_batch"]
    ):
        raise ValueError("ADR-0096 selected width differs from interpolation width")
    shifted_control = json.loads(_SHIFTED_H4_CONTROL.read_text(encoding="utf-8"))
    if not bool(shifted_control["passed_existing_1e_10_identity_standard"]):
        raise ValueError("shifted h4 dense control is not accepted")
    candidate_source = json.loads(_CANDIDATE_SOURCE.read_text(encoding="utf-8"))
    acceptance_source = json.loads(_ACCEPTANCE_SOURCE.read_text(encoding="utf-8"))
    candidate_source_identity = (
        candidate_source["status"] == "frozen_audit_executed"
        and bool(candidate_source["gates"]["passed"])
        and candidate_source["implementation_sha256"]
        == parsed["expected_candidate_stream_implementation_sha256"]
    )
    acceptance_source_identity = (
        acceptance_source["status"] == "frozen_audit_executed"
        and bool(acceptance_source["gates"]["passed"])
        and acceptance_source["implementation_sha256"]
        == parsed["expected_acceptance_implementation_sha256"]
    )
    if not candidate_source_identity or not acceptance_source_identity:
        raise ValueError("interpolation source identity rejected")

    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    family_rows = []
    for family in parsed["range_families"]:
        release_cupy_memory_pool()
        gc.collect()
        family_rows.append(
            _run_family(
                parsed=parsed,
                candidate_source=candidate_source,
                acceptance_source=acceptance_source,
                board=board,
                family=family,
            )
        )
    targets = [target for family in family_rows for target in family["targets"]]
    candidates = [candidate for target in targets for candidate in target["candidates"]]
    new_quality = [
        candidate["quality"]
        for candidate in candidates
        if candidate["measurement_source"] == "ADR-0103-live"
    ]
    all_quality = [target["blueprint_quality"] for target in targets] + [
        candidate["quality"] for candidate in candidates
    ]
    local_targets = [
        target for target in targets if target["target_shift"] == "local_blocker_seat3_x2"
    ]
    strength_targets = [
        target
        for target in targets
        if target["target_shift"] == "all_seat_strength_1_to2"
    ]
    alpha050_local = [
        _candidate_source_row(target, "interpolate_current1_to2_alpha050")
        for target in local_targets
    ]
    local_final_ids = [
        target["portfolio"]["final_unilateral_incumbent"] for target in local_targets
    ]
    strength_interior_accepts = [
        candidate
        for target in strength_targets
        for candidate in target["candidates"]
        if candidate["policy_kind"] == "behavioral_interpolation"
        and bool(candidate["baseline_comparison"]["unilateral_accept"])
    ]
    source_total = math.fsum(
        float(target["source_current1_unilateral_normalized_nash_conv"])
        for target in targets
    )
    final_total = math.fsum(
        float(target["portfolio"]["final_unilateral_normalized_nash_conv"])
        for target in targets
    )
    gates = parsed["gates"]
    aggregate = {
        "maximum_quality_evaluation_ms": max(
            float(row["wall_ms"]) for row in new_quality
        ),
        "maximum_target_workspace_compile_ms": max(
            float(row["target_workspace_compile_ms"]) for row in targets
        ),
        "maximum_host_peak_numeric_bytes": max(
            int(row["maximum_host_peak_numeric_bytes"]) for row in new_quality
        ),
        "maximum_gpu_pool_bytes": max(
            int(row["maximum_gpu_pool_bytes"]) for row in new_quality
        ),
        "maximum_quality_zero_sum_residual": max(
            float(row["zero_sum_residual"]) for row in all_quality
        ),
        "maximum_interpolation_endpoint_error": max(
            float(row["maximum_interpolation_endpoint_error"]) for row in targets
        ),
        "source_current1_total_unilateral_normalized_nash_conv": source_total,
        "interpolation_total_unilateral_normalized_nash_conv": final_total,
        "incremental_unilateral_reduction_over_current1": source_total - final_total,
        "strength_interior_unilateral_accepts": len(strength_interior_accepts),
        "wall_seconds_before_result_serialization": time.perf_counter() - started,
    }
    gate_results = {
        "target_row_count": len(targets) == gates["expected_target_rows"],
        "target_rows_per_family": all(
            len(row["targets"]) == gates["expected_target_rows_per_family"]
            for row in family_rows
        ),
        "new_quality_evaluation_count": all(
            int(row["new_quality_evaluations"])
            == gates["expected_new_quality_evaluations_per_target"]
            for row in targets
        ),
        "candidate_row_count": all(
            len(row["candidates"]) == gates["expected_candidate_rows_per_target"]
            for row in targets
        ),
        "wide_schema": all(
            int(row["information_sets"]) == gates["expected_wide_information_sets"]
            and int(row["hand_action_entries"])
            == gates["expected_wide_hand_action_entries"]
            for row in targets
        ),
        "sparse_batch_identity": all(
            all(
                int(candidate["quality"]["terminal_sparse_batches"])
                == int(gates["expected_sparse_batches_by_family"][row["range_family"]])
                for candidate in row["candidates"]
            )
            for row in targets
        ),
        "candidate_stream_source_identity": candidate_source_identity
        == gates["require_candidate_stream_source_identity"],
        "acceptance_source_identity": acceptance_source_identity
        == gates["require_acceptance_source_identity"],
        "target_descriptor_identity": all(
            bool(row["target_descriptor_identity"]) for row in targets
        )
        == gates["require_target_descriptor_identity"],
        "endpoint_policy_digest_identity": all(
            bool(row["endpoint_policy_digest_identity"]) for row in targets
        )
        == gates["require_endpoint_policy_digest_identity"],
        "interpolation_normalization": all(
            bool(row["interpolation_normalization"]) for row in targets
        )
        == gates["require_interpolation_normalization"],
        "interpolation_endpoint_identity": aggregate[
            "maximum_interpolation_endpoint_error"
        ]
        <= gates["maximum_interpolation_endpoint_error"],
        "incumbent_nonworsening": all(
            bool(row["portfolio"]["nonworsening"]) for row in targets
        )
        == gates["require_incumbent_nonworsening"],
        "incumbent_guard_semantics": all(
            bool(row["portfolio"]["guard_semantics"]) for row in targets
        )
        == gates["require_incumbent_guard_semantics"],
        "quality_latency": aggregate["maximum_quality_evaluation_ms"]
        <= gates["maximum_quality_evaluation_ms"],
        "target_workspace_compile_latency": aggregate[
            "maximum_target_workspace_compile_ms"
        ]
        <= gates["maximum_target_workspace_compile_ms"],
        "host_peak": aggregate["maximum_host_peak_numeric_bytes"]
        <= gates["maximum_host_peak_numeric_bytes"],
        "gpu_peak": aggregate["maximum_gpu_pool_bytes"]
        <= gates["maximum_gpu_pool_bytes"],
        "quality_zero_sum": aggregate["maximum_quality_zero_sum_residual"]
        <= gates["maximum_quality_zero_sum_residual"],
        "finite_policies_and_quality": all(
            bool(row["finite_policies_and_quality"]) for row in targets
        )
        == gates["require_finite_policies_and_quality"],
        "total_wall": aggregate["wall_seconds_before_result_serialization"]
        <= gates["maximum_total_audit_seconds"],
    }
    gate_results["passed"] = all(gate_results.values())
    hypotheses = {
        "alpha050_unilateral_safe_on_both_local_targets": all(
            bool(row["baseline_comparison"]["unilateral_accept"])
            for row in alpha050_local
        ),
        "interpolation_improves_current1_on_both_local_targets": all(
            float(row["incremental_unilateral_reduction_over_current1"])
            > parsed["acceptance_guard_normalized"]
            for row in local_targets
        ),
        "no_dense_interior_unilateral_accept": not strength_interior_accepts,
        "same_interior_final_incumbent_on_both_local_targets": (
            len(set(local_final_ids)) == 1
            and local_final_ids[0].startswith("interpolate_")
        ),
        "total_interpolation_stream_improves_current1": (
            final_total < source_total - parsed["acceptance_guard_normalized"]
        ),
        "alpha075_unilateral_unsafe_on_both_local_targets": all(
            not bool(
                _candidate_source_row(
                    target,
                    "interpolate_current1_to2_alpha075",
                )["baseline_comparison"]["unilateral_accept"]
            )
            for target in local_targets
        ),
    }
    properties = cp.cuda.runtime.getDeviceProperties(0)
    name = properties["name"]
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    return {
        "schema_version": 1,
        "experiment_type": "h32_current1_to_current2_behavioral_interpolation",
        "status": "frozen_audit_executed",
        "config": parsed,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "candidate_stream_source_sha256": _sha256(_CANDIDATE_SOURCE),
        "acceptance_source_sha256": _sha256(_ACCEPTANCE_SOURCE),
        "shifted_h4_control_sha256": _sha256(_SHIFTED_H4_CONTROL),
        "width_source_sha256": _sha256(_WIDTH_SOURCE),
        "family_rows": family_rows,
        "aggregate": aggregate,
        "hypotheses": hypotheses,
        "gates": gate_results,
        "counts": {
            "family_rows": len(family_rows),
            "target_rows": len(targets),
            "candidate_rows": len(candidates),
            "new_quality_rows": len(new_quality),
        },
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
            "The interpolation matrix remains one river board, one bet size, equal stacks, and four generated targets.",
            "Behavioral mixing is pointwise at each information set and is not realization-plan interpolation.",
            "Three fixed interior coefficients do not locate the exact unilateral safety boundary.",
            "The exact evaluator remains an offline teacher rather than a deployable policy-delta verifier.",
            "Unilateral non-worsening is not coalition safety or full-game exploitability.",
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
    result = run_h32_current_interpolation_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "h32 current interpolation: "
        f"targets={result['counts']['target_rows']}, "
        f"new_quality={result['counts']['new_quality_rows']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
