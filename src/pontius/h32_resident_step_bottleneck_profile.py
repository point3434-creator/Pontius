"""Read-only stage attribution for the accepted h32 resident warm step.

This audit replays already exposed targets.  It does not construct a fresh
belief, evaluate strategy quality, or alter the accepted live street rule.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import time
from typing import Any, Mapping

import numpy as np

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .cupy_sparse_incidence import CuPyBidirectionalIncidence, release_cupy_memory_pool
from .evidence_protocol import DEFAULT_GPU_NUMERICAL_IDENTITY
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_fresh_board_panel_cache_preflight import _json_digest
from .h32_fresh_selector_stable_affine_street_seat5_audit import (
    build_fresh_seat4_target,
    parse_h32_fresh_selector_stable_affine_street_seat5_config,
)
from .h32_fresh_selector_stable_affine_street_audit import _build_case
from .h32_fresh_union_value_audit import _memory_snapshot
from .h32_resident_cfr_audit import _policy_error
from .h32_warm_search_acceptance_audit import (
    _average_policy_from_state,
    _policy_distance,
)
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR
from .river import parse_cards
from .shared_resident_response_context import (
    SharedResidentAutomatonBundle,
    bind_resident_response_context,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-resident-step-bottleneck-profile-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-resident-step-bottleneck-profile-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_SEAT5_CONFIG = (
    _ROOT / "experiments/configs/h32-fresh-selector-stable-affine-street-seat5-v1.json"
)
_SEAT5_RESULT = (
    _ROOT / "experiments/results/h32-fresh-selector-stable-affine-street-seat5-v1.json"
)
_REQUIREMENTS = _ROOT / "experiments/requirements/leaf-adjoint-gpu-screen-v1.txt"
_RESIDENT_CFR = _ROOT / "src/pontius/resident_leaf_adjoint_cfr.py"
_RESIDENT_CONTRACTION = (
    _ROOT / "src/pontius/resident_heterogeneous_leaf_contraction.py"
)
_SHARED_CONTEXT = _ROOT / "src/pontius/shared_resident_response_context.py"
_TARGET_BUILDER = _ROOT / "src/pontius/h32_fresh_union_value_audit.py"
_EVIDENCE_PROTOCOL = _ROOT / "src/pontius/evidence_protocol.py"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_resident_step_bottleneck_profile.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_seat5_config_sha256": _SEAT5_CONFIG,
    "expected_seat5_result_sha256": _SEAT5_RESULT,
    "expected_requirements_sha256": _REQUIREMENTS,
    "expected_resident_cfr_sha256": _RESIDENT_CFR,
    "expected_resident_contraction_sha256": _RESIDENT_CONTRACTION,
    "expected_shared_context_sha256": _SHARED_CONTEXT,
    "expected_target_builder_sha256": _TARGET_BUILDER,
    "expected_evidence_protocol_sha256": _EVIDENCE_PROTOCOL,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_TARGETS = [
    {
        "target": "panel_1/blocker_heavy/local_blocker_seat4_x2",
        "board_id": "panel_1",
        "board": ["5c", "8c", "8d", "Jc", "As"],
        "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat4_x2",
        "source_belief_sha256": (
            "aa3a5a8abe8dc72fe436134d4b619239a87b002134cdad88a908d833318b5067"
        ),
        "target_belief_sha256": (
            "9cb9f6c30990baab33c710ce5bbef634cd903d5dd11346b26b7037b03d1d5953"
        ),
        "target_descriptor_sha256": (
            "a8dbff19eb77c5e109d31bfb72954ca1fb2dfe28f884e1628e1f9f0c5a51e3a9"
        ),
        "disclosed_timing_stratum": "adr0194_fastest_live_step",
    },
    {
        "target": "panel_2/balanced/local_blocker_seat4_x2",
        "board_id": "panel_2",
        "board": ["2c", "3s", "5d", "Js", "Qc"],
        "range_family": "balanced",
        "target_shift": "local_blocker_seat4_x2",
        "source_belief_sha256": (
            "0662b2cf2436cbc6dcc5669fe75a2c15f03e652fb40a6903703a10dd14cfa289"
        ),
        "target_belief_sha256": (
            "4bf33595af8b344e01b534ea12ad5619fac2e307f06d4e1e1be55ca6d7f4c0de"
        ),
        "target_descriptor_sha256": (
            "41675715d6df5e230d77688dedc7c18c404ab0807ab604f660fd767612068748"
        ),
        "disclosed_timing_stratum": "adr0194_slowest_live_step",
    },
]


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required bottleneck-profile input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_resident_step_bottleneck_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate ADR-0195's read-only replay protocol."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "targets",
        "target_seat",
        "restarts_per_target",
        "restart_rule",
        "timing_boundary",
        "classification_rule",
        "hardware_counterfactuals",
        "maximum_policy_probability_error",
        "maximum_policy_mean_total_variation",
        "required_numpy_version",
        "required_scipy_version",
        "required_cupy_version",
        "required_cuda_runtime_version",
        "minimum_cuda_driver_version",
        "required_compute_capability",
        "required_gpu_name",
        "cuda_dll_environment_variable",
        "gates",
    }
    if set(config) != fields:
        raise ValueError("resident-step bottleneck config fields differ from ADR-0195")
    identity = DEFAULT_GPU_NUMERICAL_IDENTITY
    frozen = {
        "evidence_stage": (
            "preregistered_read_only_replay_after_adr0194_using_only_exposed_targets_"
            "and_no_strategy_quality_labels"
        ),
        "seed": 20260821,
        "targets": _TARGETS,
        "target_seat": 4,
        "restarts_per_target": 3,
        "restart_rule": (
            "fresh_solver_same_blueprint_same_warm_mass_shared_preloaded_context_"
            "release_free_pool_blocks_and_synchronize_before_each_step"
        ),
        "timing_boundary": (
            "one_complete_resident_dcfr_step_after_preloaded_response_context_"
            "excluding_context_compile_and_any_quality_or_affine_work"
        ),
        "classification_rule": (
            "largest_pooled_time_bucket_among_device_gpu_host_hand_fold_transfer_"
            "and_other_host_or_residual_ties_lexicographic"
        ),
        "hardware_counterfactuals": [
            "two_x_device_gpu_only",
            "four_x_device_gpu_only",
            "two_x_host_hand_fold_only",
            "two_x_all_non_device_work",
        ],
        "maximum_policy_probability_error": (
            identity.maximum_policy_probability_error
        ),
        "maximum_policy_mean_total_variation": (
            identity.maximum_policy_mean_information_set_total_variation
        ),
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "required_gpu_name": "NVIDIA GeForce RTX 5080",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("resident-step bottleneck workload differs from ADR-0195")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"resident-step bottleneck source mismatch: {field}")
    expected_gates = {
        "expected_target_rows": 2,
        "expected_restart_steps": 6,
        "expected_traverser_rows": 36,
        "maximum_step_ms": 15000.0,
        "maximum_absolute_stage_residual_fraction": 0.15,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "maximum_total_audit_seconds": 600.0,
        "require_clean_git_state": True,
        "require_source_result_passed": True,
        "require_seat5_result_passed": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_numerical_warm_start_identity": True,
        "require_numerical_restart_policy_identity": True,
        "require_complete_stage_telemetry": True,
        "require_finite": True,
        "require_no_strategy_quality_evaluation": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("resident-step bottleneck gates differ from ADR-0195")
    return {
        **config,
        "targets": tuple(dict(row) for row in config["targets"]),
        "hardware_counterfactuals": tuple(config["hardware_counterfactuals"]),
        "gates": dict(config["gates"]),
    }


def _gpu_name(cp: Any) -> str:
    properties = cp.cuda.runtime.getDeviceProperties(0)
    value = properties["name"]
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)


def _sum_traverser_field(work: Any, field: str) -> float:
    return math.fsum(float(getattr(row, field)) for row in work.traversers)


def _sum_resident_field(work: Any, field: str) -> float:
    return math.fsum(
        float(getattr(row.resident_work, field)) for row in work.traversers
    )


def _profile_step_row(work: Any, *, wall_ms: float, repetition: int) -> dict[str, Any]:
    """Collapse nested solver telemetry into mutually interpretable buckets."""

    probability_ms = _sum_traverser_field(work, "probability_compile_ms")
    own_reach_ms = _sum_traverser_field(work, "own_reach_and_average_ms")
    factor_prepare_ms = _sum_resident_field(work, "factor_prepare_ms")
    factor_upload_ms = _sum_resident_field(work, "factor_upload_ms")
    product_gpu_ms = _sum_resident_field(work, "product_generation_gpu_ms")
    pipeline_gpu_ms = _sum_resident_field(work, "resident_pipeline_gpu_ms")
    device_to_host_ms = _sum_resident_field(work, "device_to_host_ms")
    hand_fold_ms = _sum_resident_field(work, "hand_fold_ms")
    reverse_ms = _sum_traverser_field(work, "reverse_adjoint_ms")
    regret_ms = _sum_traverser_field(work, "regret_apply_ms")
    discount_ms = float(work.discount_ms)
    device_gpu_ms = product_gpu_ms + pipeline_gpu_ms
    transfer_ms = factor_upload_ms + device_to_host_ms
    explicitly_attributed_ms = math.fsum(
        (
            probability_ms,
            own_reach_ms,
            factor_prepare_ms,
            transfer_ms,
            device_gpu_ms,
            hand_fold_ms,
            reverse_ms,
            regret_ms,
            discount_ms,
        )
    )
    residual_ms = wall_ms - explicitly_attributed_ms
    other_host_or_residual_ms = wall_ms - device_gpu_ms - hand_fold_ms - transfer_ms
    traversers = []
    for row in work.traversers:
        resident = row.resident_work
        traversers.append(
            {
                "traverser": int(row.traverser),
                "wall_ms": float(resident.wall_ms),
                "product_generation_gpu_ms": float(
                    resident.product_generation_gpu_ms
                ),
                "resident_pipeline_gpu_ms": float(resident.resident_pipeline_gpu_ms),
                "device_to_host_ms": float(resident.device_to_host_ms),
                "hand_fold_ms": float(resident.hand_fold_ms),
                "batches": int(resident.batches),
                "maximum_batch_feature_width": int(
                    resident.maximum_batch_feature_width
                ),
                "per_call_host_to_device_bytes": int(
                    resident.per_call_host_to_device_bytes
                ),
                "per_call_device_to_host_bytes": int(
                    resident.per_call_device_to_host_bytes
                ),
                "maximum_middle_rank": int(resident.maximum_middle_rank),
            }
        )
    return {
        "repetition": repetition,
        "wall_ms": wall_ms,
        "reported_wall_ms": float(work.wall_ms),
        "terminal_contraction_ms": float(work.terminal_contraction_ms),
        "probability_compile_ms": probability_ms,
        "own_reach_and_average_ms": own_reach_ms,
        "factor_prepare_ms": factor_prepare_ms,
        "factor_upload_ms": factor_upload_ms,
        "product_generation_gpu_ms": product_gpu_ms,
        "resident_pipeline_gpu_ms": pipeline_gpu_ms,
        "device_gpu_ms": device_gpu_ms,
        "device_to_host_ms": device_to_host_ms,
        "transfer_ms": transfer_ms,
        "host_hand_fold_ms": hand_fold_ms,
        "reverse_adjoint_ms": reverse_ms,
        "regret_apply_ms": regret_ms,
        "discount_ms": discount_ms,
        "explicitly_attributed_ms": explicitly_attributed_ms,
        "stage_residual_ms": residual_ms,
        "stage_residual_fraction": residual_ms / wall_ms,
        "other_host_or_residual_ms": other_host_or_residual_ms,
        "device_gpu_share": device_gpu_ms / wall_ms,
        "host_hand_fold_share": hand_fold_ms / wall_ms,
        "transfer_share": transfer_ms / wall_ms,
        "other_host_or_residual_share": other_host_or_residual_ms / wall_ms,
        "terminal_sparse_batches": sum(
            int(row.terminal_sparse_batches) for row in work.traversers
        ),
        "maximum_gpu_pool_bytes": max(
            int(row.maximum_gpu_pool_total_bytes) for row in work.traversers
        ),
        "traversers": traversers,
    }


def _counterfactuals(row: Mapping[str, Any]) -> dict[str, float]:
    wall = float(row["wall_ms"])
    device = float(row["device_gpu_ms"])
    fold = float(row["host_hand_fold_ms"])
    non_device = wall - device
    bills = {
        "two_x_device_gpu_only_ms": wall - device + device / 2.0,
        "four_x_device_gpu_only_ms": wall - device + device / 4.0,
        "two_x_host_hand_fold_only_ms": wall - fold + fold / 2.0,
        "two_x_all_non_device_work_ms": device + non_device / 2.0,
    }
    return {
        **bills,
        **{
            name.removesuffix("_ms") + "_speedup": wall / value
            for name, value in bills.items()
        },
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {
        field: math.fsum(float(row[field]) for row in rows)
        for field in (
            "wall_ms",
            "device_gpu_ms",
            "host_hand_fold_ms",
            "transfer_ms",
            "other_host_or_residual_ms",
        )
    }
    buckets = {
        "device_gpu": totals["device_gpu_ms"],
        "host_hand_fold": totals["host_hand_fold_ms"],
        "transfer": totals["transfer_ms"],
        "other_host_or_residual": totals["other_host_or_residual_ms"],
    }
    dominant = min(
        (name for name, value in buckets.items() if value == max(buckets.values())),
        default="unknown",
    )
    counterfactual_rows = [_counterfactuals(row) for row in rows]
    return {
        "step_count": len(rows),
        "median_step_ms": statistics.median(float(row["wall_ms"]) for row in rows),
        "minimum_step_ms": min(float(row["wall_ms"]) for row in rows),
        "maximum_step_ms": max(float(row["wall_ms"]) for row in rows),
        "pooled_stage_ms": buckets,
        "pooled_stage_share": {
            name: value / totals["wall_ms"] for name, value in buckets.items()
        },
        "dominant_time_bucket": dominant,
        "maximum_absolute_stage_residual_fraction": max(
            abs(float(row["stage_residual_fraction"])) for row in rows
        ),
        "median_counterfactual": {
            field: statistics.median(float(row[field]) for row in counterfactual_rows)
            for field in counterfactual_rows[0]
        },
    }


def _run_target(
    parsed: dict[str, Any],
    live: dict[str, Any],
    source_parent: dict[str, Any],
    target_spec: Mapping[str, Any],
    cp: Any,
) -> dict[str, Any]:
    board = parse_cards(*target_spec["board"])
    family = str(target_spec["range_family"])
    source, layout, sparse, retained = _build_case(
        parsed=live,
        board=board,
        hand_count=live["hands_per_player"],
        family=family,
    )
    source_workspace, _, automata = retained
    source_digest = _belief_digest(source)
    source_row = next(
        row
        for row in source_parent["source_rows"]
        if row["source"] == f"{target_spec['board_id']}/{family}"
    )
    state = source_row["final_checkpoint"]
    source_checkpoint_identity = (
        axis_cfr_checkpoint_digest(state) == state["state_sha256"]
        and source_digest == target_spec["source_belief_sha256"]
        and source_digest == source_row["source_belief_sha256"]
    )
    blueprint = _average_policy_from_state(state)
    blueprint_digest = policy_digest(blueprint)
    blueprint_identity = blueprint_digest == state["average_policy_sha256"]
    belief, descriptor = build_fresh_seat4_target(
        source,
        board=board,
        target_seat=parsed["target_seat"],
    )
    target_digest = _belief_digest(belief)
    descriptor_digest = _json_digest(descriptor)
    target_identity = (
        target_digest == target_spec["target_belief_sha256"]
        and descriptor_digest == target_spec["target_descriptor_sha256"]
        and belief.hands_by_player == source.hands_by_player
    )

    base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        belief,
        query_chunk_records=live["query_chunk_records"],
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, base)
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    shared = SharedResidentAutomatonBundle.compile(workspace, automata)
    context = bind_resident_response_context(
        shared,
        layout=layout,
        workspace=workspace,
        sparse=sparse,
        source_policy=blueprint,
        hands_by_player=belief.hands_by_player,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=live["maximum_feature_width_per_batch"],
    )
    warm_mass = live["warm_regret_mass_payoff_fraction"] * float(
        layout.game.payoff_span
    )
    steps = []
    policies = []
    warm_distances = []
    memory_rows = []
    for repetition in range(1, parsed["restarts_per_target"] + 1):
        solver = ResidentLeafAdjointPublicTreeCFR(
            layout,
            workspace,
            sparse,
            automata,
            live["solver_variant"],
            belief_cache=context.belief_cache,
            automaton_caches=shared.automaton_caches,
            cupy_sparse=gpu,
            maximum_feature_width_per_batch=live[
                "maximum_feature_width_per_batch"
            ],
            hands_by_player=belief.hands_by_player,
        )
        solver.warm_start(blueprint, warm_mass)
        warm_distances.append(_policy_distance(blueprint, solver.current_strategy()))
        release_cupy_memory_pool()
        cp.cuda.runtime.deviceSynchronize()
        memory_rows.append(_memory_snapshot(cp))
        started = time.perf_counter()
        solver.step()
        cp.cuda.runtime.deviceSynchronize()
        wall_ms = (time.perf_counter() - started) * 1000.0
        if solver.last_step_work is None:
            raise AssertionError("resident bottleneck replay produced no step telemetry")
        row = _profile_step_row(
            solver.last_step_work,
            wall_ms=wall_ms,
            repetition=repetition,
        )
        row["counterfactuals"] = _counterfactuals(row)
        steps.append(row)
        policies.append(solver.current_strategy())
        memory_rows.append(_memory_snapshot(cp))
        del solver
        gc.collect()

    restart_errors = []
    for policy in policies[1:]:
        maximum, mean_tv = _policy_error(policies[0], policy)
        restart_errors.append(
            {
                "maximum_policy_probability_error": maximum,
                "policy_mean_total_variation": mean_tv,
                "policy_sha256": policy_digest(policy),
            }
        )
    result = {
        "target": target_spec["target"],
        "timing_stratum": target_spec["disclosed_timing_stratum"],
        "board_id": target_spec["board_id"],
        "range_family": family,
        "source_checkpoint_identity": source_checkpoint_identity,
        "target_identity": target_identity,
        "blueprint_identity": blueprint_identity,
        "blueprint_policy_sha256": blueprint_digest,
        "warm_start_distances": warm_distances,
        "restart_policy_sha256_diagnostic": [
            policy_digest(policy) for policy in policies
        ],
        "restart_policy_errors": restart_errors,
        "steps": steps,
        "summary": _summary(steps),
        "memory_rows": memory_rows,
    }
    del context, shared, gpu, workspace, base, automata, source_workspace
    del sparse, layout, belief, source
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_resident_step_bottleneck_profile(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the frozen no-new-label timing attribution audit."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_resident_step_bottleneck_config(config)
    seat5_config = json.loads(_SEAT5_CONFIG.read_text(encoding="utf-8"))
    live = parse_h32_fresh_selector_stable_affine_street_seat5_config(seat5_config)
    source_parent = json.loads(_SOURCE.read_text(encoding="utf-8"))
    seat5_result = json.loads(_SEAT5_RESULT.read_text(encoding="utf-8"))
    cp, runtime = _validate_runtime(parsed)
    git = _strict_git_metadata()
    gpu_name = _gpu_name(cp)
    if gpu_name != parsed["required_gpu_name"]:
        raise RuntimeError("GPU name differs from ADR-0195")
    source_passed = bool(source_parent["gates"]["passed"])
    seat5_passed = bool(seat5_result["passed"])
    if git["dirty"]:
        raise RuntimeError("resident bottleneck execution requires clean Git state")
    if not source_passed or not seat5_passed:
        raise ValueError("resident bottleneck replay parent did not pass")

    started = time.perf_counter()
    targets = [
        _run_target(parsed, live, source_parent, target, cp)
        for target in parsed["targets"]
    ]
    elapsed_seconds = time.perf_counter() - started
    steps = [step for target in targets for step in target["steps"]]
    traversers = [row for step in steps for row in step["traversers"]]
    memory_rows = [row for target in targets for row in target["memory_rows"]]
    restart_errors = [
        row for target in targets for row in target["restart_policy_errors"]
    ]
    warm_distances = [
        row for target in targets for row in target["warm_start_distances"]
    ]
    gates_config = parsed["gates"]
    finite_values = [
        float(value)
        for step in steps
        for key, value in step.items()
        if key.endswith("_ms") or key.endswith("_share") or key.endswith("_fraction")
    ]
    maximum_restart_error = max(
        float(row["maximum_policy_probability_error"]) for row in restart_errors
    )
    maximum_restart_tv = max(
        float(row["policy_mean_total_variation"]) for row in restart_errors
    )
    gates = {
        "clean_git_state": (not git["dirty"])
        == gates_config["require_clean_git_state"],
        "source_result_passed": source_passed
        == gates_config["require_source_result_passed"],
        "seat5_result_passed": seat5_passed
        == gates_config["require_seat5_result_passed"],
        "target_rows": len(targets) == gates_config["expected_target_rows"],
        "restart_steps": len(steps) == gates_config["expected_restart_steps"],
        "traverser_rows": len(traversers)
        == gates_config["expected_traverser_rows"],
        "source_checkpoint_identity": all(
            target["source_checkpoint_identity"] for target in targets
        )
        == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(target["target_identity"] for target in targets)
        == gates_config["require_target_identity"],
        "blueprint_identity": all(target["blueprint_identity"] for target in targets)
        == gates_config["require_blueprint_identity"],
        "numerical_warm_start_identity": all(
            float(row["maximum_probability_error"])
            <= parsed["maximum_policy_probability_error"]
            and float(row["mean_total_variation"])
            <= parsed["maximum_policy_mean_total_variation"]
            for row in warm_distances
        )
        == gates_config["require_numerical_warm_start_identity"],
        "numerical_restart_policy_identity": (
            maximum_restart_error <= parsed["maximum_policy_probability_error"]
            and maximum_restart_tv <= parsed["maximum_policy_mean_total_variation"]
        )
        == gates_config["require_numerical_restart_policy_identity"],
        "complete_stage_telemetry": all(
            len(step["traversers"]) == 6
            and all(
                float(step[field]) >= 0.0
                for field in (
                    "product_generation_gpu_ms",
                    "resident_pipeline_gpu_ms",
                    "device_to_host_ms",
                    "host_hand_fold_ms",
                )
            )
            for step in steps
        )
        == gates_config["require_complete_stage_telemetry"],
        "step_ms": max(float(step["wall_ms"]) for step in steps)
        <= gates_config["maximum_step_ms"],
        "stage_residual_fraction": max(
            abs(float(step["stage_residual_fraction"])) for step in steps
        )
        <= gates_config["maximum_absolute_stage_residual_fraction"],
        "gpu_pool_bytes": max(
            int(row["gpu_pool_total_bytes"]) for row in memory_rows
        )
        <= gates_config["maximum_gpu_pool_bytes"],
        "physical_free_bytes": min(int(row["gpu_free_bytes"]) for row in memory_rows)
        >= gates_config["minimum_physical_free_bytes"],
        "total_audit_seconds": elapsed_seconds
        <= gates_config["maximum_total_audit_seconds"],
        "finite": all(math.isfinite(value) for value in finite_values)
        == gates_config["require_finite"],
        "no_strategy_quality_evaluation": True
        == gates_config["require_no_strategy_quality_evaluation"],
        "strategy_population_claim_null": True
        == gates_config["require_strategy_population_claim_null"],
    }
    gates["passed"] = all(gates.values())
    aggregate = _summary(steps)
    result = {
        "schema_version": 1,
        "status": "h32_resident_step_bottleneck_profile_executed",
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "environment": {
            **environment_metadata(),
            **runtime,
            "gpu_name": gpu_name,
            "processor_identifier": os.environ.get("PROCESSOR_IDENTIFIER"),
            "git": git,
        },
        "methodology": {
            "fresh_labels_used": False,
            "strategy_quality_evaluated": False,
            "targets_selected_from_disclosed_adr0194_timing_extremes": True,
            "restart_policy_digests_are_diagnostic_only": True,
            "numerical_identity_protocol": "ADR-0179",
            "timing_boundary": parsed["timing_boundary"],
        },
        "target_rows": targets,
        "aggregate": {
            **aggregate,
            "maximum_restart_policy_probability_error": maximum_restart_error,
            "maximum_restart_policy_mean_total_variation": maximum_restart_tv,
            "maximum_gpu_pool_bytes": max(
                int(row["gpu_pool_total_bytes"]) for row in memory_rows
            ),
            "minimum_physical_free_bytes": min(
                int(row["gpu_free_bytes"]) for row in memory_rows
            ),
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": (
            "accept_stage_attribution_and_use_dominant_bucket_for_next_engineering_screen"
            if gates["passed"]
            else "reject_stage_attribution"
        ),
        "total_audit_seconds": elapsed_seconds,
        "strategy_population_claim": None,
        "limitations": [
            "Two already exposed h32 river targets bracket disclosed live-step timing; this is not a latency distribution.",
            "CUDA event time identifies device residency but does not separate FP64 arithmetic from device-memory bandwidth.",
            "Hardware counterfactuals are serial Amdahl estimates, not purchase benchmarks.",
            "No fresh belief, strategy-quality label, deployment action, or composition claim is produced.",
        ],
    }
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    arguments = parser.parse_args()
    result = run_h32_resident_step_bottleneck_profile(
        arguments.config,
        arguments.output,
    )
    print(
        json.dumps(
            {
                "output": str(arguments.output),
                "passed": result["passed"],
                "aggregate": result["aggregate"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
