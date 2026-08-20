"""Continue the exact h32 DCFR checkpoints through iterations 48 and 64."""

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
from .leaf_adjoint_checkpoint_ladder_audit import (
    _build_case,
    _quality_row,
    _solver,
)
from .leaf_adjoint_evaluation import evaluate_leaf_adjoint_profile
from .real_policy import policy_digest, policy_statistics
from .reporting import environment_metadata
from .river import parse_cards

_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "leaf-adjoint-checkpoint-extension-v1.json"
)
_CHECKPOINT_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-checkpoint-ladder-v2.json"
)
_WIDTH_SOURCE = (
    _ROOT / "experiments" / "results" / "leaf-adjoint-batch-width-audit-v2.json"
)
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "axis_seed",
    "expected_checkpoint_source_sha256",
    "expected_width_source_sha256",
    "expected_requirements_sha256",
    "expected_axis_checkpoint_sha256",
    "expected_base_ladder_implementation_sha256",
    "expected_corrected_ladder_implementation_sha256",
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
    "wide_hands_per_player",
    "range_families",
    "solver_variant",
    "source_iteration",
    "checkpoint_iterations",
    "restart_iteration",
    "incumbent_source_iterations",
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
    "expected_wide_rows",
    "expected_new_checkpoints_per_family",
    "expected_new_quality_profiles_per_family",
    "expected_source_candidates_per_family",
    "expected_new_candidates_per_family",
    "expected_final_iteration",
    "expected_wide_information_sets",
    "expected_wide_hand_action_entries",
    "expected_sparse_batches_by_family",
    "require_exact_source_state_identity",
    "require_restart_state_digest_identity",
    "require_checkpoint_state_digest_identity",
    "require_incumbent_nonworsening",
    "require_incumbent_guard_semantics",
    "maximum_source_incumbent_replay_error",
    "maximum_training_step_ms",
    "maximum_quality_evaluation_ms",
    "maximum_host_peak_numeric_bytes",
    "maximum_gpu_pool_bytes",
    "maximum_quality_zero_sum_residual",
    "require_finite_states_and_quality",
    "maximum_total_audit_seconds",
}
_SOURCE_PATHS = {
    "expected_checkpoint_source_sha256": _CHECKPOINT_SOURCE,
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
    "expected_corrected_ladder_implementation_sha256": (
        _ROOT / "src" / "pontius" / "leaf_adjoint_checkpoint_ladder_audit_v2.py"
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


def parse_checkpoint_extension_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the immutable ADR-0097 continuation protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "checkpoint-extension fields differ from ADR-0097: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0096_width_economics_before_any_h32_"
            "iteration48_or64_policy_or_quality"
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
        "solver_variant": "dcfr",
        "source_iteration": 32,
        "checkpoint_iterations": [48, 64],
        "restart_iteration": 48,
        "incumbent_source_iterations": [1, 2, 4, 8, 16, 32],
        "candidate_order": ["current", "average"],
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
        raise ValueError("checkpoint-extension workload differs from ADR-0097")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")
    expected_gates = {
        "expected_wide_rows": 2,
        "expected_new_checkpoints_per_family": 2,
        "expected_new_quality_profiles_per_family": 4,
        "expected_source_candidates_per_family": 12,
        "expected_new_candidates_per_family": 4,
        "expected_final_iteration": 64,
        "expected_wide_information_sets": 6144,
        "expected_wide_hand_action_entries": 12288,
        "expected_sparse_batches_by_family": {
            "balanced": 435,
            "blocker_heavy": 311,
        },
        "require_exact_source_state_identity": True,
        "require_restart_state_digest_identity": True,
        "require_checkpoint_state_digest_identity": True,
        "require_incumbent_nonworsening": True,
        "require_incumbent_guard_semantics": True,
        "maximum_source_incumbent_replay_error": 1e-10,
        "maximum_training_step_ms": 60000.0,
        "maximum_quality_evaluation_ms": 60000.0,
        "maximum_host_peak_numeric_bytes": 3000000000,
        "maximum_gpu_pool_bytes": 4000000000,
        "maximum_quality_zero_sum_residual": 1e-9,
        "require_finite_states_and_quality": True,
        "maximum_total_audit_seconds": 2700.0,
    }
    gates = config["gates"]
    if (
        not isinstance(gates, dict)
        or set(gates) != _GATE_FIELDS
        or gates != expected_gates
    ):
        raise ValueError("checkpoint-extension gates differ from ADR-0097")
    return {
        **config,
        "range_families": tuple(config["range_families"]),
        "checkpoint_iterations": tuple(config["checkpoint_iterations"]),
        "incumbent_source_iterations": tuple(
            config["incumbent_source_iterations"]
        ),
        "candidate_order": tuple(config["candidate_order"]),
        "gates": {**gates, "expected_sparse_batches_by_family": dict(
            gates["expected_sparse_batches_by_family"]
        )},
    }


def _source_row_and_state(
    source: dict[str, Any],
    *,
    family: str,
    iteration: int,
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    row = next(
        value for value in source["wide_rows"] if value["range_family"] == family
    )
    checkpoint = next(
        value
        for value in row["checkpoints"]
        if int(value["iteration"]) == iteration
    )
    state = checkpoint["state"]
    identity = (
        axis_cfr_checkpoint_digest(state) == checkpoint["state_sha256"]
        and checkpoint["state_sha256"] == row["final_state_sha256"]
        and int(state["iteration"]) == iteration
        and state["current_policy_sha256"] == checkpoint["current_policy_sha256"]
        and state["average_policy_sha256"] == checkpoint["average_policy_sha256"]
    )
    return row, state, identity


def _candidate_rows_from_source(
    row: dict[str, Any],
    parsed: dict[str, Any],
) -> list[dict[str, Any]]:
    checkpoints = {
        int(value["iteration"]): value for value in row["checkpoints"]
    }
    candidates = []
    for iteration in parsed["incumbent_source_iterations"]:
        checkpoint = checkpoints[iteration]
        for kind in parsed["candidate_order"]:
            quality = checkpoint["quality"][kind]
            candidates.append(
                {
                    "phase": "source",
                    "iteration": iteration,
                    "policy_kind": kind,
                    "policy_sha256": checkpoint[f"{kind}_policy_sha256"],
                    "normalized_nash_conv": float(
                        quality["normalized_nash_conv"]
                    ),
                    "measurement_source": quality["measurement_source"],
                }
            )
    return candidates


def build_guarded_incumbent_trace(
    candidates: list[dict[str, Any]],
    *,
    guard: float,
) -> dict[str, Any]:
    """Apply one deterministic quality guard to an ordered candidate stream."""

    if not math.isfinite(guard) or guard < 0.0:
        raise ValueError("incumbent guard must be finite and nonnegative")
    incumbent: dict[str, Any] | None = None
    trace = []
    nonworsening = True
    semantics = True
    for index, candidate in enumerate(candidates):
        value = float(candidate["normalized_nash_conv"])
        if not math.isfinite(value) or value < 0.0:
            raise ValueError("candidate NashConv must be finite and nonnegative")
        prior = None if incumbent is None else float(
            incumbent["normalized_nash_conv"]
        )
        improvement = None if prior is None else prior - value
        if incumbent is None:
            decision = "initialize"
            incumbent = dict(candidate)
        elif improvement is not None and improvement > guard:
            decision = "accept"
            incumbent = dict(candidate)
        elif improvement is not None and improvement < -guard:
            decision = "reject"
        else:
            decision = "abstain"
        result_value = float(incumbent["normalized_nash_conv"])
        if prior is not None:
            nonworsening = nonworsening and result_value <= prior
            semantics = semantics and (
                (decision == "accept" and improvement is not None and improvement > guard)
                or (
                    decision == "reject"
                    and improvement is not None
                    and improvement < -guard
                )
                or (
                    decision == "abstain"
                    and improvement is not None
                    and -guard <= improvement <= guard
                )
            )
        trace.append(
            {
                "candidate_index": index,
                **candidate,
                "prior_incumbent_normalized_nash_conv": prior,
                "candidate_improvement": improvement,
                "guard": guard,
                "decision": decision,
                "resulting_incumbent_iteration": int(incumbent["iteration"]),
                "resulting_incumbent_policy_kind": incumbent["policy_kind"],
                "resulting_incumbent_policy_sha256": incumbent["policy_sha256"],
                "resulting_incumbent_normalized_nash_conv": result_value,
            }
        )
    if incumbent is None:
        raise ValueError("incumbent trace requires at least one candidate")
    return {
        "guard": guard,
        "trace": trace,
        "incumbent": incumbent,
        "accepted_candidates": sum(
            row["decision"] in {"initialize", "accept"} for row in trace
        ),
        "rejected_candidates": sum(row["decision"] == "reject" for row in trace),
        "abstained_candidates": sum(
            row["decision"] == "abstain" for row in trace
        ),
        "nonworsening": nonworsening,
        "guard_semantics": semantics,
    }


def _finite_checkpoint_state(state: dict[str, Any]) -> bool:
    return all(
        math.isfinite(float(value))
        for table_name in ("regrets", "strategy_sums")
        for action_row in state[table_name].values()
        for value in action_row.values()
    )


def _run_family_extension(
    *,
    parsed: dict[str, Any],
    source: dict[str, Any],
    board: tuple[int, ...],
    family: str,
) -> dict[str, Any]:
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
    source_row, source_state, source_identity = _source_row_and_state(
        source,
        family=family,
        iteration=parsed["source_iteration"],
    )
    if not source_identity:
        raise AssertionError("ADR-0097 source checkpoint identity rejected")
    restored_metadata = restore_axis_cfr_checkpoint(solver, source_state)
    source_replay = export_axis_cfr_checkpoint(
        solver,
        context=source_state["context"],
        provenance=source_state["provenance"],
    )
    restore_identity = source_replay["state_sha256"] == source_state["state_sha256"]
    if not restore_identity:
        raise AssertionError("ADR-0097 immediate source restore identity rejected")

    unique_automata = {
        id(automaton): automaton
        for library in automata
        for automaton in library.values()
    }
    automaton_bytes = sum(value.numeric_bytes for value in unique_automata.values())
    information_sets = len(solver.information_schema())
    hand_action_entries = sum(
        len(actions) for actions in solver.information_schema().values()
    )
    payoff_span = float(topology.game.payoff_span)
    source_checkpoint = next(
        value
        for value in source_row["checkpoints"]
        if int(value["iteration"]) == parsed["source_iteration"]
    )
    source_training_ms = float(source_checkpoint["cumulative_training_ms"])
    source_candidates = _candidate_rows_from_source(source_row, parsed)
    source_trace = build_guarded_incumbent_trace(
        source_candidates,
        guard=parsed["acceptance_guard_normalized"],
    )
    source_minimum = min(
        float(row["normalized_nash_conv"]) for row in source_candidates
    )
    source_incumbent_replay_error = abs(
        float(source_trace["incumbent"]["normalized_nash_conv"])
        - source_minimum
    )

    context = {
        **dict(restored_metadata["context"]),
        "continuation_source_state_sha256": source_state["state_sha256"],
    }
    provenance = {
        "audit": "ADR-0097",
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "checkpoint_source_sha256": _sha256(_CHECKPOINT_SOURCE),
        "width_source_sha256": _sha256(_WIDTH_SOURCE),
        "solver_variant": parsed["solver_variant"],
    }

    checkpoint_rows = []
    step_rows = []
    new_candidates = []
    extension_training_ms = 0.0
    checkpoint_identity = True
    restart_identity = False
    for iteration in range(
        parsed["source_iteration"] + 1,
        parsed["checkpoint_iterations"][-1] + 1,
    ):
        started = time.perf_counter()
        solver.step()
        step_ms = (time.perf_counter() - started) * 1000.0
        extension_training_ms += step_ms
        work = solver.last_step_work
        if work is None:
            raise AssertionError("checkpoint extension step has no telemetry")
        terminal_ms = float(work.terminal_contraction_ms)
        step_rows.append(
            {
                "iteration": iteration,
                "wall_ms": step_ms,
                "terminal_contraction_ms": terminal_ms,
                "terminal_fraction": terminal_ms / step_ms,
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
        restored_state = json.loads(rendered_state)
        literal_state_identity = (
            axis_cfr_checkpoint_digest(restored_state) == state["state_sha256"]
        )
        checkpoint_identity = checkpoint_identity and literal_state_identity
        quality = {}
        for kind, policy in (("current", current), ("average", average)):
            digest = policy_digest(policy)
            if digest != state[f"{kind}_policy_sha256"]:
                raise AssertionError("checkpoint policy digest differs from state")
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
            quality[kind] = _quality_row(
                policy_kind=kind,
                digest=digest,
                result=evaluated,
                payoff_span=payoff_span,
                source="ADR-0097-live",
            )
            new_candidates.append(
                {
                    "phase": "extension",
                    "iteration": iteration,
                    "policy_kind": kind,
                    "policy_sha256": digest,
                    "normalized_nash_conv": float(
                        quality[kind]["normalized_nash_conv"]
                    ),
                    "measurement_source": "ADR-0097-live",
                }
            )
        checkpoint_rows.append(
            {
                "iteration": iteration,
                "extension_cumulative_training_ms": extension_training_ms,
                "total_cumulative_training_ms": (
                    source_training_ms + extension_training_ms
                ),
                "current_policy_sha256": state["current_policy_sha256"],
                "average_policy_sha256": state["average_policy_sha256"],
                "current_policy_statistics": policy_statistics(current),
                "average_policy_statistics": policy_statistics(average),
                "quality": quality,
                "state_sha256": state["state_sha256"],
                "state_json_bytes": len(rendered_state.encode("utf-8")),
                "state": state,
            }
        )
        if iteration == parsed["restart_iteration"]:
            resumed = _solver(
                parsed=parsed,
                belief=belief,
                topology=topology,
                workspace=workspace,
                sparse=sparse,
                automata=automata,
                cupy_sparse=gpu,
            )
            restore_axis_cfr_checkpoint(resumed, restored_state)
            replay = export_axis_cfr_checkpoint(
                resumed,
                context=context,
                provenance=provenance,
            )
            restart_identity = replay["state_sha256"] == state["state_sha256"]
            solver = resumed

    previous_average = float(
        source_checkpoint["quality"]["average"]["normalized_nash_conv"]
    )
    previous_training_ms = source_training_ms
    for row in checkpoint_rows:
        average = row["quality"]["average"]
        current = float(average["normalized_nash_conv"])
        elapsed_seconds = (
            float(row["total_cumulative_training_ms"]) - previous_training_ms
        ) / 1000.0
        average["marginal_normalized_improvement_per_training_second"] = (
            previous_average - current
        ) / elapsed_seconds
        average["residual_ratio_from_previous_checkpoint"] = (
            current / previous_average
        )
        previous_average = current
        previous_training_ms = float(row["total_cumulative_training_ms"])

    all_candidates = source_candidates + new_candidates
    incumbent = build_guarded_incumbent_trace(
        all_candidates,
        guard=parsed["acceptance_guard_normalized"],
    )
    quality_rows = [
        row["quality"][kind]
        for row in checkpoint_rows
        for kind in parsed["candidate_order"]
    ]
    finite = (
        all(_finite_checkpoint_state(row["state"]) for row in checkpoint_rows)
        and all(bool(row["finite"]) for row in quality_rows)
    )
    return {
        "hands_per_player": parsed["wide_hands_per_player"],
        "range_family": family,
        "information_sets": information_sets,
        "hand_action_entries": hand_action_entries,
        "payoff_span": payoff_span,
        "workspace_timing": workspace_timing,
        "gpu_operator_upload_ms": gpu.upload_ms,
        "source_iteration": parsed["source_iteration"],
        "source_state_sha256": source_state["state_sha256"],
        "source_state_identity": source_identity and restore_identity,
        "source_cumulative_training_ms": source_training_ms,
        "source_candidates": source_candidates,
        "source_incumbent_replay_error": source_incumbent_replay_error,
        "step_rows": step_rows,
        "checkpoints": checkpoint_rows,
        "checkpoint_state_digest_identity": checkpoint_identity,
        "restart_iteration": parsed["restart_iteration"],
        "restart_state_digest_identity": restart_identity,
        "final_state_sha256": checkpoint_rows[-1]["state_sha256"],
        "new_candidates": new_candidates,
        "incumbent": incumbent,
        "new_accepted_candidates": sum(
            trace["phase"] == "extension"
            and trace["decision"] == "accept"
            for trace in incumbent["trace"]
        ),
        "new_abstained_candidates": sum(
            trace["phase"] == "extension"
            and trace["decision"] == "abstain"
            for trace in incumbent["trace"]
        ),
        "finite_states_and_quality": finite,
    }


def run_checkpoint_extension_audit(config: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_checkpoint_extension_config(config)
    import scipy

    cupy_started = time.perf_counter()
    cp, _ = _cupy_modules()
    cupy_import_ms = (time.perf_counter() - cupy_started) * 1000.0
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0097")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0097")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0097")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0097")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0097 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed["required_compute_capability"]:
        raise ValueError("GPU compute capability differs from ADR-0097")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")

    width_source = json.loads(_WIDTH_SOURCE.read_text(encoding="utf-8"))
    if (
        int(width_source["aggregate"]["selected_width"])
        != parsed["maximum_feature_width_per_batch"]
    ):
        raise ValueError("ADR-0096 selected width differs from continuation width")
    source = json.loads(_CHECKPOINT_SOURCE.read_text(encoding="utf-8"))
    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    wide_rows = []
    for family in parsed["range_families"]:
        release_cupy_memory_pool()
        gc.collect()
        wide_rows.append(
            _run_family_extension(
                parsed=parsed,
                source=source,
                board=board,
                family=family,
            )
        )

    step_rows = [step for row in wide_rows for step in row["step_rows"]]
    quality_rows = [
        checkpoint["quality"][kind]
        for row in wide_rows
        for checkpoint in row["checkpoints"]
        for kind in parsed["candidate_order"]
    ]
    gates = parsed["gates"]
    aggregate = {
        "maximum_source_incumbent_replay_error": max(
            float(row["source_incumbent_replay_error"]) for row in wide_rows
        ),
        "maximum_training_step_ms": max(
            float(row["wall_ms"]) for row in step_rows
        ),
        "maximum_quality_evaluation_ms": max(
            float(row["wall_ms"]) for row in quality_rows
        ),
        "maximum_host_peak_numeric_bytes": max(
            max(int(step["maximum_host_peak_numeric_bytes"]) for step in step_rows),
            max(int(row["maximum_host_peak_numeric_bytes"]) for row in quality_rows),
        ),
        "maximum_gpu_pool_bytes": max(
            max(int(step["maximum_gpu_pool_bytes"]) for step in step_rows),
            max(int(row["maximum_gpu_pool_bytes"]) for row in quality_rows),
        ),
        "maximum_quality_zero_sum_residual": max(
            float(row["zero_sum_residual"]) for row in quality_rows
        ),
        "minimum_terminal_fraction": min(
            float(row["terminal_fraction"]) for row in step_rows
        ),
        "maximum_terminal_fraction": max(
            float(row["terminal_fraction"]) for row in step_rows
        ),
        "new_accepted_candidates": sum(
            int(row["new_accepted_candidates"]) for row in wide_rows
        ),
        "new_abstained_candidates": sum(
            int(row["new_abstained_candidates"]) for row in wide_rows
        ),
        "wall_seconds_before_result_serialization": time.perf_counter() - started,
    }
    gate_results = {
        "wide_row_count": len(wide_rows) == gates["expected_wide_rows"],
        "new_checkpoint_count": all(
            len(row["checkpoints"])
            == gates["expected_new_checkpoints_per_family"]
            for row in wide_rows
        ),
        "new_quality_profile_count": all(
            len(row["new_candidates"])
            == gates["expected_new_quality_profiles_per_family"]
            for row in wide_rows
        ),
        "source_candidate_count": all(
            len(row["source_candidates"])
            == gates["expected_source_candidates_per_family"]
            for row in wide_rows
        ),
        "new_candidate_count": all(
            len(row["new_candidates"])
            == gates["expected_new_candidates_per_family"]
            for row in wide_rows
        ),
        "final_iteration": all(
            int(row["checkpoints"][-1]["iteration"])
            == gates["expected_final_iteration"]
            for row in wide_rows
        ),
        "wide_schema": all(
            int(row["information_sets"])
            == gates["expected_wide_information_sets"]
            and int(row["hand_action_entries"])
            == gates["expected_wide_hand_action_entries"]
            for row in wide_rows
        ),
        "sparse_batch_identity": all(
            all(
                int(step["terminal_sparse_batches"])
                == int(
                    gates["expected_sparse_batches_by_family"][
                        row["range_family"]
                    ]
                )
                for step in row["step_rows"]
            )
            for row in wide_rows
        ),
        "source_state_identity": all(
            bool(row["source_state_identity"]) for row in wide_rows
        )
        == gates["require_exact_source_state_identity"],
        "restart_state_identity": all(
            bool(row["restart_state_digest_identity"]) for row in wide_rows
        )
        == gates["require_restart_state_digest_identity"],
        "checkpoint_state_identity": all(
            bool(row["checkpoint_state_digest_identity"]) for row in wide_rows
        )
        == gates["require_checkpoint_state_digest_identity"],
        "incumbent_nonworsening": all(
            bool(row["incumbent"]["nonworsening"]) for row in wide_rows
        )
        == gates["require_incumbent_nonworsening"],
        "incumbent_guard_semantics": all(
            bool(row["incumbent"]["guard_semantics"]) for row in wide_rows
        )
        == gates["require_incumbent_guard_semantics"],
        "source_incumbent_replay": aggregate[
            "maximum_source_incumbent_replay_error"
        ]
        <= gates["maximum_source_incumbent_replay_error"],
        "training_latency": aggregate["maximum_training_step_ms"]
        <= gates["maximum_training_step_ms"],
        "quality_latency": aggregate["maximum_quality_evaluation_ms"]
        <= gates["maximum_quality_evaluation_ms"],
        "host_peak": aggregate["maximum_host_peak_numeric_bytes"]
        <= gates["maximum_host_peak_numeric_bytes"],
        "gpu_peak": aggregate["maximum_gpu_pool_bytes"]
        <= gates["maximum_gpu_pool_bytes"],
        "quality_zero_sum": aggregate["maximum_quality_zero_sum_residual"]
        <= gates["maximum_quality_zero_sum_residual"],
        "finite_states_and_quality": all(
            bool(row["finite_states_and_quality"]) for row in wide_rows
        )
        == gates["require_finite_states_and_quality"],
        "total_wall": aggregate["wall_seconds_before_result_serialization"]
        <= gates["maximum_total_audit_seconds"],
    }
    gate_results["passed"] = all(gate_results.values())
    properties = cp.cuda.runtime.getDeviceProperties(0)
    name = properties["name"]
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    return {
        "schema_version": 1,
        "experiment_type": "restored_h32_dcfr_checkpoint_extension_through64",
        "status": "frozen_audit_executed",
        "config": parsed,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "checkpoint_source_sha256": _sha256(_CHECKPOINT_SOURCE),
        "width_source_sha256": _sha256(_WIDTH_SOURCE),
        "wide_rows": wide_rows,
        "aggregate": aggregate,
        "gates": gate_results,
        "counts": {"wide_rows": len(wide_rows)},
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
            "The continuation remains one board, one bet size, equal stacks, and two constructed h32 belief families.",
            "NashConv measures unilateral reduced-game deviation gain, not coalition safety or full-NLHE exploitability.",
            "The Float64 acceptance guard is conservative relative to measured evaluator error but is not a formal interval certificate.",
            "No strategy-improvement outcome is a gate; the audit may pass with a flat or worse continuation.",
            "Iteration 128 is deliberately deferred until this staged continuation is read.",
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
    result = run_checkpoint_extension_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "checkpoint extension audit: "
        f"wide={result['counts']['wide_rows']}, "
        f"new_accepts={result['aggregate']['new_accepted_candidates']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
