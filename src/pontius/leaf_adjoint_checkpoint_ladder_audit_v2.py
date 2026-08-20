"""Run the corrected restartable h32 DCFR checkpoint learning-curve audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any

import numpy as np

from .axis_cfr_checkpoint import (
    axis_cfr_checkpoint_digest,
    export_axis_cfr_checkpoint,
    restore_axis_cfr_checkpoint,
)
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .incremental_policy_tt import compile_policy_probability_tape
from .leaf_adjoint_checkpoint_ladder_audit import (
    _build_case,
    _copied_quality_row,
    _finite_quality,
    _quality_row,
    _small_restart_case,
    _solver,
    _source_policy_digests,
    _source_quality_rows,
)
from .leaf_adjoint_evaluation import (
    LeafAdjointProfileEvaluation,
    evaluate_leaf_adjoint_profile,
    evaluate_leaf_adjoint_seat,
)
from .open_mode_audit import _policy_from_json
from .real_policy import (
    mean_policy_total_variation,
    policy_digest,
    policy_statistics,
)
from .reporting import environment_metadata
from .river import parse_cards

_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "leaf-adjoint-checkpoint-ladder-v2.json"
)
_POLICY_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-cfr-gpu-audit-v1.json"
)
_QUALITY_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-evaluation-audit-v1.json"
)
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "axis_seed",
    "expected_policy_source_sha256",
    "expected_quality_source_sha256",
    "expected_requirements_sha256",
    "expected_axis_checkpoint_sha256",
    "expected_base_ladder_implementation_sha256",
    "expected_cupy_sparse_incidence_sha256",
    "expected_heterogeneous_leaf_sha256",
    "expected_leaf_adjoint_cfr_sha256",
    "expected_leaf_adjoint_evaluation_sha256",
    "expected_sparse_incidence_sha256",
    "expected_structured_showdown_sha256",
    "expected_audit_implementation_sha256",
    "board",
    "pot",
    "stack",
    "bet_size",
    "players",
    "small_hands_per_player",
    "small_restart_split_iteration",
    "small_restart_final_iteration",
    "wide_hands_per_player",
    "range_families",
    "validation_family",
    "solver_variant",
    "checkpoint_iterations",
    "live_evaluation_points",
    "declared_source_reuse_points",
    "wide_restart_iteration",
    "mixture_components",
    "split_index",
    "query_chunk_records",
    "maximum_feature_width_per_batch",
    "cpu_crosscheck_target",
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
    "expected_small_restart_rows",
    "maximum_small_restart_accumulator_error",
    "require_small_restart_state_digest_identity",
    "expected_wide_rows",
    "expected_checkpoints_per_family",
    "expected_live_quality_profiles_per_family",
    "expected_reused_quality_profiles_per_family",
    "maximum_training_step_ms",
    "maximum_quality_evaluation_ms",
    "maximum_host_peak_numeric_bytes",
    "maximum_gpu_pool_bytes",
    "maximum_final_cpu_gpu_profile_utility_error",
    "maximum_final_cpu_gpu_best_response_error",
    "maximum_final_cpu_gpu_deviation_gain_error",
    "minimum_validation_final_charged_gpu_speedup",
    "minimum_all_final_charged_gpu_speedup",
    "maximum_quality_zero_sum_residual",
    "minimum_final_average_normalized_improvement_over_step2",
    "expected_wide_information_sets",
    "expected_wide_hand_action_entries",
    "require_declared_source_reuse_digest_identity",
    "require_wide_restart_state_digest_identity",
    "require_finite_states_and_quality",
    "maximum_total_audit_seconds",
}
_SOURCE_PATHS = {
    "expected_policy_source_sha256": _POLICY_SOURCE,
    "expected_quality_source_sha256": _QUALITY_SOURCE,
    "expected_requirements_sha256": (
        _ROOT / "experiments" / "requirements" / "leaf-adjoint-gpu-screen-v1.txt"
    ),
    "expected_axis_checkpoint_sha256": (
        _ROOT / "src" / "pontius" / "axis_cfr_checkpoint.py"
    ),
    "expected_base_ladder_implementation_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_checkpoint_ladder_audit.py"
    ),
    "expected_cupy_sparse_incidence_sha256": (
        _ROOT / "src" / "pontius" / "cupy_sparse_incidence.py"
    ),
    "expected_heterogeneous_leaf_sha256": (
        _ROOT / "src" / "pontius" / "heterogeneous_leaf_contraction.py"
    ),
    "expected_leaf_adjoint_cfr_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_cfr.py"
    ),
    "expected_leaf_adjoint_evaluation_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_evaluation.py"
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_checkpoint_ladder_v2_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "corrected checkpoint ladder fields differ from ADR-0091: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0089_source_reuse_rejection_and_balanced_"
            "iteration2_distance_before_any_h32_quality_above2"
        ),
        "seed": 20260820,
        "axis_seed": 20260819,
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "small_hands_per_player": [4, 7],
        "small_restart_split_iteration": 2,
        "small_restart_final_iteration": 4,
        "wide_hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "validation_family": "blocker_heavy",
        "solver_variant": "dcfr",
        "checkpoint_iterations": [1, 2, 4, 8, 16, 32],
        "live_evaluation_points": [
            "2:current",
            "4:current",
            "4:average",
            "8:current",
            "8:average",
            "16:current",
            "16:average",
            "32:current",
            "32:average",
        ],
        "declared_source_reuse_points": [
            "1:current",
            "1:average",
            "2:average",
        ],
        "wide_restart_iteration": 16,
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 384,
        "cpu_crosscheck_target": 0,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("corrected checkpoint ladder workload differs from ADR-0091")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")
    expected_gates = {
        "expected_small_restart_rows": 4,
        "maximum_small_restart_accumulator_error": 0.0,
        "require_small_restart_state_digest_identity": True,
        "expected_wide_rows": 2,
        "expected_checkpoints_per_family": 6,
        "expected_live_quality_profiles_per_family": 9,
        "expected_reused_quality_profiles_per_family": 3,
        "maximum_training_step_ms": 60_000.0,
        "maximum_quality_evaluation_ms": 60_000.0,
        "maximum_host_peak_numeric_bytes": 3_000_000_000,
        "maximum_gpu_pool_bytes": 4_000_000_000,
        "maximum_final_cpu_gpu_profile_utility_error": 1e-9,
        "maximum_final_cpu_gpu_best_response_error": 1e-9,
        "maximum_final_cpu_gpu_deviation_gain_error": 1e-9,
        "minimum_validation_final_charged_gpu_speedup": 3.0,
        "minimum_all_final_charged_gpu_speedup": 3.0,
        "maximum_quality_zero_sum_residual": 1e-9,
        "minimum_final_average_normalized_improvement_over_step2": 1e-4,
        "expected_wide_information_sets": 6_144,
        "expected_wide_hand_action_entries": 12_288,
        "require_declared_source_reuse_digest_identity": True,
        "require_wide_restart_state_digest_identity": True,
        "require_finite_states_and_quality": True,
        "maximum_total_audit_seconds": 3_600.0,
    }
    gates = config["gates"]
    if (
        not isinstance(gates, dict)
        or set(gates) != _GATE_FIELDS
        or gates != expected_gates
    ):
        raise ValueError("corrected checkpoint ladder gates differ from ADR-0091")
    return {
        **config,
        "small_hands_per_player": tuple(config["small_hands_per_player"]),
        "range_families": tuple(config["range_families"]),
        "checkpoint_iterations": tuple(config["checkpoint_iterations"]),
        "live_evaluation_points": tuple(config["live_evaluation_points"]),
        "declared_source_reuse_points": tuple(config["declared_source_reuse_points"]),
        "gates": dict(gates),
    }


def _current_policy_from_state(state: dict[str, Any]) -> dict[str, dict[str, float]]:
    policy = {}
    for key, regrets in state["regrets"].items():
        actions = tuple(regrets)
        positive = tuple(max(0.0, float(regrets[action])) for action in actions)
        total = math.fsum(positive)
        if total <= 0.0:
            values = tuple(1.0 / len(actions) for _ in actions)
        else:
            values = tuple(value / total for value in positive)
        policy[key] = dict(zip(actions, values, strict=True))
    result = dict(sorted(policy.items()))
    if policy_digest(result) != state["current_policy_sha256"]:
        raise AssertionError("state-derived current policy digest differs")
    return result


def _policy_distance(
    first: dict[str, dict[str, float]],
    second: dict[str, dict[str, float]],
) -> dict[str, float | int]:
    if set(first) != set(second):
        raise ValueError("policy distance schemas differ")
    differences = [
        abs(first[key][action] - second[key][action])
        for key in first
        for action in first[key]
    ]
    return {
        "maximum_probability_error": max(differences),
        "nonzero_entries": sum(value != 0.0 for value in differences),
        "entries_above_1e15": sum(value > 1e-15 for value in differences),
        "entries_above_1e12": sum(value > 1e-12 for value in differences),
        "differing_information_rows": sum(
            any(first[key][action] != second[key][action] for action in first[key])
            for key in first
        ),
        "mean_total_variation": mean_policy_total_variation(first, second),
    }


def _iteration2_current_distance(
    row: dict[str, Any], source: dict[str, Any]
) -> dict[str, float | int | str]:
    live_checkpoint = next(
        value for value in row["checkpoints"] if int(value["iteration"]) == 2
    )
    live_policy = _current_policy_from_state(live_checkpoint["state"])
    source_row = next(
        value for value in source["wide_rows"] if value["range_family"] == row["range_family"]
    )
    source_checkpoint = next(
        value for value in source_row["checkpoints"] if int(value["iteration"]) == 2
    )
    source_policy = _policy_from_json(source_checkpoint["current_policy"])
    return {
        "live_policy_sha256": policy_digest(live_policy),
        "source_policy_sha256": source_checkpoint["current_policy_sha256"],
        **_policy_distance(live_policy, source_policy),
    }


def _wide_case_v2(
    *,
    parsed: dict[str, Any],
    policy_source: dict[str, Any],
    quality_source: dict[str, Any],
    board: tuple[int, ...],
    family: str,
) -> dict[str, object]:
    """Run one trajectory with the per-policy measurement matrix from ADR-0091."""

    belief, topology, sparse, retained = _build_case(
        parsed=parsed,
        board=board,
        hand_count=parsed["wide_hands_per_player"],
        family=family,
    )
    workspace, workspace_timing, automata = retained
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    solver = _solver(
        parsed=parsed,
        belief=belief,
        topology=topology,
        workspace=workspace,
        sparse=sparse,
        automata=automata,
        cupy_sparse=gpu,
    )
    source_digests = _source_policy_digests(policy_source, family)
    source_quality = _source_quality_rows(quality_source, family)
    live_points = set(parsed["live_evaluation_points"])
    reused_points = set(parsed["declared_source_reuse_points"])
    all_points = {
        f"{iteration}:{kind}"
        for iteration in parsed["checkpoint_iterations"]
        for kind in ("current", "average")
    }
    if live_points & reused_points or live_points | reused_points != all_points:
        raise AssertionError("ADR-0091 measurement matrix is not a partition")

    payoff_span = float(topology.game.payoff_span)
    information_sets = len(solver.information_schema())
    expected_entries = sum(
        len(actions) for actions in solver.information_schema().values()
    )
    unique_automata = {
        id(automaton): automaton
        for library in automata
        for automaton in library.values()
    }
    automaton_bytes = sum(value.numeric_bytes for value in unique_automata.values())
    context = {
        "board": parsed["board"],
        "pot": parsed["pot"],
        "stack": parsed["stack"],
        "bet_size": parsed["bet_size"],
        "hands_per_player": parsed["wide_hands_per_player"],
        "range_family": family,
    }
    provenance = {
        "audit": "ADR-0091",
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "solver_variant": parsed["solver_variant"],
    }

    checkpoint_rows = []
    step_rows = []
    cumulative_training_ms = 0.0
    declared_reuse_identity = True
    restart_identity = False
    final_average_policy = None
    final_average_result: LeafAdjointProfileEvaluation | None = None
    final_checkpoint_state = None
    for iteration in range(1, parsed["checkpoint_iterations"][-1] + 1):
        step_started = time.perf_counter()
        solver.step()
        step_ms = (time.perf_counter() - step_started) * 1000.0
        cumulative_training_ms += step_ms
        work = solver.last_step_work
        if work is None:
            raise AssertionError("checkpoint ladder training step has no telemetry")
        step_rows.append(
            {
                "iteration": iteration,
                "wall_ms": step_ms,
                "terminal_contraction_ms": work.terminal_contraction_ms,
                "terminal_sparse_batches": sum(
                    row.terminal_sparse_batches for row in work.traversers
                ),
                "maximum_host_peak_numeric_bytes": (
                    max(
                        row.maximum_terminal_peak_numeric_bytes
                        for row in work.traversers
                    )
                    + solver.accumulator_numeric_bytes()
                    + automaton_bytes
                ),
                "maximum_gpu_pool_bytes": max(
                    row.maximum_gpu_pool_total_bytes for row in work.traversers
                ),
            }
        )
        if iteration not in parsed["checkpoint_iterations"]:
            continue

        current = solver.current_strategy()
        average = solver.average_strategy()
        current_digest = policy_digest(current)
        average_digest = policy_digest(average)
        state = export_axis_cfr_checkpoint(
            solver,
            context=context,
            provenance=provenance,
        )
        rendered_state = json.dumps(
            state,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        if axis_cfr_checkpoint_digest(json.loads(rendered_state)) != state[
            "state_sha256"
        ]:
            raise AssertionError("checkpoint ladder serialized state digest differs")

        live_results: dict[str, LeafAdjointProfileEvaluation] = {}
        quality_rows = {}
        for kind, policy, digest in (
            ("current", current, current_digest),
            ("average", average, average_digest),
        ):
            point = f"{iteration}:{kind}"
            if point in live_points:
                evaluated = evaluate_leaf_adjoint_profile(
                    topology,
                    workspace,
                    sparse,
                    policy,
                    automata,
                    hands_by_player=belief.hands_by_player,
                    maximum_feature_width_per_batch=parsed[
                        "maximum_feature_width_per_batch"
                    ],
                    cupy_sparse=gpu,
                )
                live_results[kind] = evaluated
                quality_rows[kind] = _quality_row(
                    policy_kind=kind,
                    digest=digest,
                    result=evaluated,
                    payoff_span=payoff_span,
                    source="ADR-0091-live",
                )
            elif point in reused_points:
                declared_reuse_identity = declared_reuse_identity and (
                    digest == source_digests[iteration][kind]
                )
                quality_rows[kind] = _copied_quality_row(
                    policy_kind=kind,
                    digest=digest,
                    source=source_quality[(iteration, kind)],
                )
            else:
                raise AssertionError(f"unassigned quality measurement point {point}")

        checkpoint_rows.append(
            {
                "iteration": iteration,
                "cumulative_training_ms": cumulative_training_ms,
                "current_policy_sha256": current_digest,
                "average_policy_sha256": average_digest,
                "current_policy_statistics": policy_statistics(current),
                "average_policy_statistics": policy_statistics(average),
                "quality": quality_rows,
                "state_sha256": state["state_sha256"],
                "state_json_bytes": len(rendered_state.encode("utf-8")),
                "state": state,
            }
        )
        if iteration == parsed["wide_restart_iteration"]:
            resumed = _solver(
                parsed=parsed,
                belief=belief,
                topology=topology,
                workspace=workspace,
                sparse=sparse,
                automata=automata,
                cupy_sparse=gpu,
            )
            restore_axis_cfr_checkpoint(resumed, json.loads(rendered_state))
            replay = export_axis_cfr_checkpoint(
                resumed,
                context=context,
                provenance=provenance,
            )
            restart_identity = replay["state_sha256"] == state["state_sha256"]
            solver = resumed
        if iteration == parsed["checkpoint_iterations"][-1]:
            final_average_policy = average
            final_average_result = live_results["average"]
            final_checkpoint_state = state

    if final_average_policy is None or final_average_result is None:
        raise AssertionError("checkpoint ladder final quality was not evaluated")
    if final_checkpoint_state is None:
        raise AssertionError("checkpoint ladder final state is absent")
    probabilities = compile_policy_probability_tape(
        topology,
        belief.hands_by_player,
        final_average_policy,
    )
    target = parsed["cpu_crosscheck_target"]
    cpu = evaluate_leaf_adjoint_seat(
        topology,
        workspace,
        sparse,
        probabilities,
        automata[target],
        target_player=target,
        hands_by_player=belief.hands_by_player,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    gpu_seat = final_average_result.seats[target]
    crosscheck = {
        "target_player": target,
        "cpu_ms": cpu.wall_ms,
        "gpu_ms": gpu_seat.wall_ms,
        "gpu_operator_upload_ms": gpu.upload_ms,
        "charged_gpu_speedup": cpu.wall_ms / (gpu_seat.wall_ms + gpu.upload_ms),
        "profile_utility_error": abs(cpu.profile_utility - gpu_seat.profile_utility),
        "best_response_error": abs(
            cpu.best_response_value - gpu_seat.best_response_value
        ),
        "deviation_gain_error": abs(cpu.deviation_gain - gpu_seat.deviation_gain),
        "raw_action_mismatches": sum(
            action != gpu_seat.best_response_actions[key]
            for key, action in cpu.best_response_actions.items()
        ),
    }

    uniform_normalized = float(
        checkpoint_rows[0]["quality"]["average"]["normalized_nash_conv"]
    )
    previous_average = None
    previous_training_ms = 0.0
    for row in checkpoint_rows:
        training_seconds = float(row["cumulative_training_ms"]) / 1000.0
        for kind in ("current", "average"):
            quality = row["quality"][kind]
            improvement = uniform_normalized - float(
                quality["normalized_nash_conv"]
            )
            quality["normalized_improvement_from_uniform"] = improvement
            quality["improvement_per_training_second"] = (
                improvement / training_seconds
            )
        average_quality = row["quality"]["average"]
        if previous_average is None:
            average_quality[
                "marginal_normalized_improvement_per_training_second"
            ] = None
        else:
            delta_quality = float(previous_average["normalized_nash_conv"]) - float(
                average_quality["normalized_nash_conv"]
            )
            delta_seconds = (
                float(row["cumulative_training_ms"]) - previous_training_ms
            ) / 1000.0
            average_quality[
                "marginal_normalized_improvement_per_training_second"
            ] = delta_quality / delta_seconds
        previous_average = average_quality
        previous_training_ms = float(row["cumulative_training_ms"])

    by_iteration = {int(row["iteration"]): row for row in checkpoint_rows}
    step2_average = float(
        by_iteration[2]["quality"]["average"]["normalized_nash_conv"]
    )
    final_average = float(
        by_iteration[32]["quality"]["average"]["normalized_nash_conv"]
    )
    best_current_row = min(
        checkpoint_rows,
        key=lambda row: float(row["quality"]["current"]["normalized_nash_conv"]),
    )
    best_average_row = min(
        checkpoint_rows,
        key=lambda row: float(row["quality"]["average"]["normalized_nash_conv"]),
    )
    finite = all(
        math.isfinite(float(value))
        for state_row in checkpoint_rows
        for table_name in ("regrets", "strategy_sums")
        for action_row in state_row["state"][table_name].values()
        for value in action_row.values()
    ) and all(
        bool(row["quality"][kind]["finite"])
        for row in checkpoint_rows
        for kind in ("current", "average")
    )
    return {
        "hands_per_player": parsed["wide_hands_per_player"],
        "range_family": family,
        "information_sets": information_sets,
        "hand_action_entries": expected_entries,
        "payoff_span": payoff_span,
        "workspace_timing": workspace_timing,
        "gpu_operator_upload_ms": gpu.upload_ms,
        "step_rows": step_rows,
        "checkpoints": checkpoint_rows,
        "declared_source_reuse_digest_identity": declared_reuse_identity,
        "restart_iteration": parsed["wide_restart_iteration"],
        "restart_state_digest_identity": restart_identity,
        "final_state_sha256": final_checkpoint_state["state_sha256"],
        "final_cpu_gpu_crosscheck": crosscheck,
        "final_average_normalized_improvement_over_step2": (
            step2_average - final_average
        ),
        "best_current_iteration": int(best_current_row["iteration"]),
        "best_current_normalized_nash_conv": float(
            best_current_row["quality"]["current"]["normalized_nash_conv"]
        ),
        "best_average_iteration": int(best_average_row["iteration"]),
        "best_average_normalized_nash_conv": float(
            best_average_row["quality"]["average"]["normalized_nash_conv"]
        ),
        "live_quality_profiles": sum(
            row["quality"][kind]["measurement_source"] == "ADR-0091-live"
            for row in checkpoint_rows
            for kind in ("current", "average")
        ),
        "reused_quality_profiles": sum(
            row["quality"][kind]["measurement_source"] == "ADR-0087"
            for row in checkpoint_rows
            for kind in ("current", "average")
        ),
        "finite_states_and_quality": finite,
    }


def run_checkpoint_ladder_v2_audit(config: dict[str, Any]) -> dict[str, object]:
    parsed = parse_checkpoint_ladder_v2_config(config)
    import scipy

    cupy_started = time.perf_counter()
    cp, _ = _cupy_modules()
    cupy_import_ms = (time.perf_counter() - cupy_started) * 1000.0
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0091")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0091")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0091")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0091")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0091 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed["required_compute_capability"]:
        raise ValueError("GPU compute capability differs from ADR-0091")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")

    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    small_rows = [
        _small_restart_case(
            parsed=parsed,
            board=board,
            hand_count=hand_count,
            family=family,
        )
        for hand_count in parsed["small_hands_per_player"]
        for family in parsed["range_families"]
    ]
    gates = parsed["gates"]
    maximum_small_error = max(
        max(
            float(row["maximum_regret_error"]),
            float(row["maximum_strategy_sum_error"]),
        )
        for row in small_rows
    )
    gate_results = {
        "small_restart_row_count": len(small_rows)
        == gates["expected_small_restart_rows"],
        "small_restart_accumulator_identity": maximum_small_error
        <= gates["maximum_small_restart_accumulator_error"],
        "small_restart_policy_identity": all(
            bool(row["current_policy_identity"])
            and bool(row["average_policy_identity"])
            for row in small_rows
        ),
        "small_restart_state_identity": all(
            bool(row["final_state_digest_identity"]) for row in small_rows
        )
        == gates["require_small_restart_state_digest_identity"],
    }
    if not all(gate_results.values()):
        gate_results["passed"] = False
        return _result(
            parsed=parsed,
            small_rows=small_rows,
            wide_rows=[],
            aggregate={"wide_skipped_after_small_restart_rejection": True},
            gate_results=gate_results,
            started=started,
            cupy_import_ms=cupy_import_ms,
            cp=cp,
            scipy=scipy,
            status="small_restart_rejected_before_wide_execution",
        )

    policy_source = json.loads(_POLICY_SOURCE.read_text(encoding="utf-8"))
    quality_source = json.loads(_QUALITY_SOURCE.read_text(encoding="utf-8"))
    wide_rows = []
    for family in parsed["range_families"]:
        release_cupy_memory_pool()
        row = _wide_case_v2(
            parsed=parsed,
            policy_source=policy_source,
            quality_source=quality_source,
            board=board,
            family=family,
        )
        row["iteration2_current_source_distance"] = _iteration2_current_distance(
            row, policy_source
        )
        wide_rows.append(row)

    step_rows = [step for row in wide_rows for step in row["step_rows"]]
    live_quality = [
        checkpoint["quality"][kind]
        for row in wide_rows
        for checkpoint in row["checkpoints"]
        for kind in ("current", "average")
        if checkpoint["quality"][kind]["measurement_source"] == "ADR-0091-live"
    ]
    all_quality = [
        checkpoint["quality"][kind]
        for row in wide_rows
        for checkpoint in row["checkpoints"]
        for kind in ("current", "average")
    ]
    crosschecks = [row["final_cpu_gpu_crosscheck"] for row in wide_rows]
    distances = [row["iteration2_current_source_distance"] for row in wide_rows]
    aggregate = {
        "maximum_small_restart_accumulator_error": maximum_small_error,
        "maximum_training_step_ms": max(float(row["wall_ms"]) for row in step_rows),
        "maximum_live_quality_evaluation_ms": max(
            float(row["wall_ms"]) for row in live_quality
        ),
        "maximum_host_peak_numeric_bytes": max(
            max(int(step["maximum_host_peak_numeric_bytes"]) for step in step_rows),
            max(int(row["maximum_host_peak_numeric_bytes"]) for row in live_quality),
        ),
        "maximum_gpu_pool_bytes": max(
            max(int(step["maximum_gpu_pool_bytes"]) for step in step_rows),
            max(int(row["maximum_gpu_pool_bytes"]) for row in live_quality),
        ),
        "maximum_final_cpu_gpu_profile_utility_error": max(
            float(row["profile_utility_error"]) for row in crosschecks
        ),
        "maximum_final_cpu_gpu_best_response_error": max(
            float(row["best_response_error"]) for row in crosschecks
        ),
        "maximum_final_cpu_gpu_deviation_gain_error": max(
            float(row["deviation_gain_error"]) for row in crosschecks
        ),
        "minimum_final_charged_gpu_speedup": min(
            float(row["charged_gpu_speedup"]) for row in crosschecks
        ),
        "validation_final_charged_gpu_speedup": next(
            float(row["final_cpu_gpu_crosscheck"]["charged_gpu_speedup"])
            for row in wide_rows
            if row["range_family"] == parsed["validation_family"]
        ),
        "maximum_quality_zero_sum_residual": max(
            float(row["zero_sum_residual"]) for row in all_quality
        ),
        "minimum_final_average_normalized_improvement_over_step2": min(
            float(row["final_average_normalized_improvement_over_step2"])
            for row in wide_rows
        ),
        "maximum_iteration2_current_source_probability_error_diagnostic": max(
            float(row["maximum_probability_error"]) for row in distances
        ),
        "maximum_iteration2_current_source_mean_tv_diagnostic": max(
            float(row["mean_total_variation"]) for row in distances
        ),
        "wall_seconds_before_result_serialization": time.perf_counter() - started,
    }
    gate_results.update(
        {
            "wide_row_count": len(wide_rows) == gates["expected_wide_rows"],
            "checkpoint_count": all(
                len(row["checkpoints"]) == gates["expected_checkpoints_per_family"]
                for row in wide_rows
            ),
            "live_quality_profile_count": all(
                int(row["live_quality_profiles"])
                == gates["expected_live_quality_profiles_per_family"]
                for row in wide_rows
            ),
            "reused_quality_profile_count": all(
                int(row["reused_quality_profiles"])
                == gates["expected_reused_quality_profiles_per_family"]
                for row in wide_rows
            ),
            "training_latency": aggregate["maximum_training_step_ms"]
            <= gates["maximum_training_step_ms"],
            "quality_latency": aggregate["maximum_live_quality_evaluation_ms"]
            <= gates["maximum_quality_evaluation_ms"],
            "host_peak": aggregate["maximum_host_peak_numeric_bytes"]
            <= gates["maximum_host_peak_numeric_bytes"],
            "gpu_peak": aggregate["maximum_gpu_pool_bytes"]
            <= gates["maximum_gpu_pool_bytes"],
            "final_profile_utility_identity": aggregate[
                "maximum_final_cpu_gpu_profile_utility_error"
            ]
            <= gates["maximum_final_cpu_gpu_profile_utility_error"],
            "final_best_response_identity": aggregate[
                "maximum_final_cpu_gpu_best_response_error"
            ]
            <= gates["maximum_final_cpu_gpu_best_response_error"],
            "final_deviation_gain_identity": aggregate[
                "maximum_final_cpu_gpu_deviation_gain_error"
            ]
            <= gates["maximum_final_cpu_gpu_deviation_gain_error"],
            "validation_final_gpu_speedup": aggregate[
                "validation_final_charged_gpu_speedup"
            ]
            >= gates["minimum_validation_final_charged_gpu_speedup"],
            "all_final_gpu_speedup": aggregate["minimum_final_charged_gpu_speedup"]
            >= gates["minimum_all_final_charged_gpu_speedup"],
            "quality_zero_sum": aggregate["maximum_quality_zero_sum_residual"]
            <= gates["maximum_quality_zero_sum_residual"],
            "final_average_improves_step2": aggregate[
                "minimum_final_average_normalized_improvement_over_step2"
            ]
            >= gates["minimum_final_average_normalized_improvement_over_step2"],
            "wide_schema": all(
                int(row["information_sets"])
                == gates["expected_wide_information_sets"]
                and int(row["hand_action_entries"])
                == gates["expected_wide_hand_action_entries"]
                for row in wide_rows
            ),
            "declared_source_reuse_digest_identity": all(
                bool(row["declared_source_reuse_digest_identity"])
                for row in wide_rows
            )
            == gates["require_declared_source_reuse_digest_identity"],
            "wide_restart_state_identity": all(
                bool(row["restart_state_digest_identity"]) for row in wide_rows
            )
            == gates["require_wide_restart_state_digest_identity"],
            "finite_states_and_quality": all(
                bool(row["finite_states_and_quality"]) for row in wide_rows
            )
            == gates["require_finite_states_and_quality"],
            "total_wall": aggregate["wall_seconds_before_result_serialization"]
            <= gates["maximum_total_audit_seconds"],
        }
    )
    gate_results["passed"] = all(gate_results.values())
    return _result(
        parsed=parsed,
        small_rows=small_rows,
        wide_rows=wide_rows,
        aggregate=aggregate,
        gate_results=gate_results,
        started=started,
        cupy_import_ms=cupy_import_ms,
        cp=cp,
        scipy=scipy,
        status="frozen_corrected_audit_executed",
    )


def _result(
    *,
    parsed: dict[str, Any],
    small_rows: list[dict[str, object]],
    wide_rows: list[dict[str, object]],
    aggregate: dict[str, object],
    gate_results: dict[str, bool],
    started: float,
    cupy_import_ms: float,
    cp: Any,
    scipy: Any,
    status: str,
) -> dict[str, object]:
    properties = cp.cuda.runtime.getDeviceProperties(0)
    name = properties["name"]
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    return {
        "schema_version": 2,
        "experiment_type": (
            "corrected_restartable_leaf_adjoint_h32_dcfr_checkpoint_ladder"
        ),
        "status": status,
        "config": parsed,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "base_ladder_implementation_sha256": _sha256(
            _SOURCE_PATHS["expected_base_ladder_implementation_sha256"]
        ),
        "policy_source_sha256": _sha256(_POLICY_SOURCE),
        "quality_source_sha256": _sha256(_QUALITY_SOURCE),
        "small_rows": small_rows,
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
            "The curve is one board and two constructed range families in the equal-stack one-bet river abstraction.",
            "NashConv measures unilateral reduced-game deviations, not coalition safety or full-NLHE strength.",
            "Only iteration-one current/average and iteration-two average reuse ADR-0087 rows, each under exact policy digest identity.",
            "Iteration-two current and every later quality row are evaluated live.",
            "The run crosses a serialized restart at iteration sixteen but does not duplicate the final sixteen h32 iterations in an uninterrupted control.",
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
    result = run_checkpoint_ladder_v2_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    improvement = result.get("aggregate", {}).get(
        "minimum_final_average_normalized_improvement_over_step2"
    )
    improvement_text = "unmeasured" if improvement is None else f"{improvement:.6g}"
    print(
        "corrected checkpoint ladder audit: "
        f"small={result['counts']['small_rows']}, "
        f"wide={result['counts']['wide_rows']}, "
        f"min_final_average_improvement={improvement_text}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
