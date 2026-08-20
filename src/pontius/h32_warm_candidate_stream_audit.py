"""Evaluate current policies and extend ADR-0099 warm search through iteration 8."""

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
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .h32_warm_search_acceptance_audit import (
    _average_policy_from_state,
    _current_policy_from_state,
    _root_marginals,
    build_sequential_incumbents,
    build_target_belief,
    compare_acceptance,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case, _quality_row, _solver
from .leaf_adjoint_evaluation import evaluate_leaf_adjoint_profile
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest, policy_statistics
from .reporting import environment_metadata
from .river import parse_cards


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-warm-candidate-stream-v1.json"
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
    "expected_acceptance_source_sha256",
    "expected_shifted_h4_control_sha256",
    "expected_width_source_sha256",
    "expected_requirements_sha256",
    "expected_axis_checkpoint_sha256",
    "expected_base_ladder_implementation_sha256",
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
    "solver_variant",
    "target_shifts",
    "local_blocker_target_seat",
    "source_search_iterations",
    "extension_source_iteration",
    "final_search_iteration",
    "candidate_order",
    "portfolio_kinds",
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
    "expected_source_states_per_target",
    "expected_new_quality_evaluations_per_target",
    "expected_candidate_stream_rows_per_target",
    "expected_extension_steps_per_target",
    "expected_final_search_iteration",
    "expected_wide_information_sets",
    "expected_wide_hand_action_entries",
    "expected_sparse_batches_by_family",
    "require_acceptance_source_identity",
    "require_target_descriptor_identity",
    "require_source_state_digest_identity",
    "require_source_policy_digest_identity",
    "require_extension_restore_identity",
    "require_extension_checkpoint_identity",
    "require_portfolio_nonworsening",
    "require_portfolio_guard_semantics",
    "maximum_training_step_ms",
    "maximum_quality_evaluation_ms",
    "maximum_target_workspace_compile_ms",
    "maximum_host_peak_numeric_bytes",
    "maximum_gpu_pool_bytes",
    "maximum_quality_zero_sum_residual",
    "require_finite_states_policies_and_quality",
    "maximum_total_audit_seconds",
}
_SOURCE_PATHS = {
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


def parse_h32_warm_candidate_stream_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the immutable ADR-0101 candidate-stream protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "candidate-stream fields differ from ADR-0101: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0100_before_any_h32_warm_current1_2_4_"
            "or_iteration8_quality"
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
        "target_shifts": [
            "local_blocker_seat3_x2",
            "all_seat_strength_1_to2",
        ],
        "local_blocker_target_seat": 3,
        "source_search_iterations": [1, 2, 4],
        "extension_source_iteration": 4,
        "final_search_iteration": 8,
        "candidate_order": [
            "search_current1",
            "search_average1",
            "search_current2",
            "search_average2",
            "search_current4",
            "search_average4",
            "search_current8",
            "search_average8",
        ],
        "portfolio_kinds": [
            "full_interleaved",
            "current_only",
            "average_only",
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
        raise ValueError("candidate-stream workload differs from ADR-0101")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")
    expected_gates = {
        "expected_target_rows": 4,
        "expected_target_rows_per_family": 2,
        "expected_source_states_per_target": 3,
        "expected_new_quality_evaluations_per_target": 5,
        "expected_candidate_stream_rows_per_target": 8,
        "expected_extension_steps_per_target": 4,
        "expected_final_search_iteration": 8,
        "expected_wide_information_sets": 6144,
        "expected_wide_hand_action_entries": 12288,
        "expected_sparse_batches_by_family": {
            "balanced": 435,
            "blocker_heavy": 311,
        },
        "require_acceptance_source_identity": True,
        "require_target_descriptor_identity": True,
        "require_source_state_digest_identity": True,
        "require_source_policy_digest_identity": True,
        "require_extension_restore_identity": True,
        "require_extension_checkpoint_identity": True,
        "require_portfolio_nonworsening": True,
        "require_portfolio_guard_semantics": True,
        "maximum_training_step_ms": 60_000.0,
        "maximum_quality_evaluation_ms": 60_000.0,
        "maximum_target_workspace_compile_ms": 30_000.0,
        "maximum_host_peak_numeric_bytes": 3_000_000_000,
        "maximum_gpu_pool_bytes": 4_000_000_000,
        "maximum_quality_zero_sum_residual": 1e-9,
        "require_finite_states_policies_and_quality": True,
        "maximum_total_audit_seconds": 1_800.0,
    }
    gates = config["gates"]
    if (
        not isinstance(gates, dict)
        or set(gates) != _GATE_FIELDS
        or gates != expected_gates
    ):
        raise ValueError("candidate-stream gates differ from ADR-0101")
    return {
        **config,
        "range_families": tuple(config["range_families"]),
        "target_shifts": tuple(config["target_shifts"]),
        "source_search_iterations": tuple(config["source_search_iterations"]),
        "candidate_order": tuple(config["candidate_order"]),
        "portfolio_kinds": tuple(config["portfolio_kinds"]),
        "gates": {
            **gates,
            "expected_sparse_batches_by_family": dict(
                gates["expected_sparse_batches_by_family"]
            ),
        },
    }


def _source_target(
    source: dict[str, Any],
    *,
    family: str,
    shift: str,
) -> dict[str, Any]:
    family_row = next(
        row for row in source["family_rows"] if row["range_family"] == family
    )
    return next(row for row in family_row["targets"] if row["target_shift"] == shift)


def _source_search_candidate(
    target: dict[str, Any],
    *,
    iteration: int,
) -> dict[str, Any]:
    return next(
        row
        for row in target["candidates"]
        if row["candidate_id"] == f"search_average{iteration}"
    )


def _descriptor_digest(descriptor: dict[str, Any]) -> str:
    retained = {
        key: value
        for key, value in descriptor.items()
        if key != "marginal_measurement_ms"
    }
    rendered = json.dumps(
        retained,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _state_finite(state: dict[str, Any]) -> bool:
    return all(
        math.isfinite(float(value))
        for table_name in ("regrets", "strategy_sums")
        for row in state[table_name].values()
        for value in row.values()
    )


def _quality_finite(quality: dict[str, Any]) -> bool:
    return bool(quality["finite"]) and all(
        math.isfinite(float(value))
        for field in (
            "utilities",
            "best_response_values",
            "deviation_gains",
        )
        for value in quality[field]
    )


def _evaluate_policy(
    *,
    topology: Any,
    workspace: OpenModeFactorTTWorkspace,
    sparse: Any,
    automata: Any,
    gpu: Any,
    hands_by_player: Any,
    policy: dict[str, dict[str, float]],
    label: str,
    payoff_span: float,
    maximum_feature_width_per_batch: int,
) -> dict[str, Any]:
    digest = policy_digest(policy)
    evaluated = evaluate_leaf_adjoint_profile(
        topology,
        workspace,
        sparse,
        policy,
        automata,
        hands_by_player=hands_by_player,
        maximum_feature_width_per_batch=maximum_feature_width_per_batch,
        cupy_sparse=gpu,
    )
    return _quality_row(
        policy_kind=label,
        digest=digest,
        result=evaluated,
        payoff_span=payoff_span,
        source="ADR-0101-live",
    )


def _guard_semantics(
    baseline: dict[str, Any],
    candidates: list[dict[str, Any]],
    portfolio: dict[str, Any],
    *,
    payoff_span: float,
    guard: float,
) -> bool:
    aggregate_id = "blueprint_average64"
    aggregate = baseline
    unilateral_id = "blueprint_average64"
    unilateral = baseline
    for candidate, trace in zip(candidates, portfolio["trace"], strict=True):
        expected_aggregate = compare_acceptance(
            aggregate,
            candidate["quality"],
            payoff_span=payoff_span,
            normalized_guard=guard,
        )
        expected_unilateral = compare_acceptance(
            unilateral,
            candidate["quality"],
            payoff_span=payoff_span,
            normalized_guard=guard,
        )
        if expected_aggregate != trace["aggregate_comparison"]:
            return False
        if expected_unilateral != trace["unilateral_comparison"]:
            return False
        if expected_aggregate["aggregate_accept"]:
            aggregate = candidate["quality"]
            aggregate_id = candidate["candidate_id"]
        if expected_unilateral["unilateral_accept"]:
            unilateral = candidate["quality"]
            unilateral_id = candidate["candidate_id"]
        if trace["resulting_aggregate_incumbent"] != aggregate_id:
            return False
        if trace["resulting_unilateral_incumbent"] != unilateral_id:
            return False
    return (
        portfolio["final_aggregate_incumbent"] == aggregate_id
        and portfolio["final_unilateral_incumbent"] == unilateral_id
    )


def _portfolio_row(
    *,
    name: str,
    baseline: dict[str, Any],
    candidates: list[dict[str, Any]],
    payoff_span: float,
    guard: float,
    target_compile_ms: float,
) -> dict[str, Any]:
    result = build_sequential_incumbents(
        baseline,
        candidates,
        payoff_span=payoff_span,
        normalized_guard=guard,
    )
    baseline_value = float(baseline["normalized_nash_conv"])
    final_aggregate = float(result["final_aggregate_normalized_nash_conv"])
    final_unilateral = float(result["final_unilateral_normalized_nash_conv"])
    search_ms = max(float(row["cumulative_search_ms"]) for row in candidates)
    evaluation_ms = math.fsum(float(row["quality"]["wall_ms"]) for row in candidates)
    precompiled_ms = search_ms + evaluation_ms
    one_shot_ms = target_compile_ms + float(baseline["wall_ms"]) + precompiled_ms
    nonworsening = (
        final_aggregate <= baseline_value + guard
        and final_unilateral <= baseline_value + guard
    )
    return {
        "portfolio_kind": name,
        "candidate_ids": [row["candidate_id"] for row in candidates],
        "candidate_rows": len(candidates),
        **result,
        "aggregate_normalized_reduction": baseline_value - final_aggregate,
        "unilateral_normalized_reduction": baseline_value - final_unilateral,
        "search_ms": search_ms,
        "candidate_evaluation_ms": evaluation_ms,
        "verified_precompiled_ms": precompiled_ms,
        "verified_one_shot_ms": one_shot_ms,
        "unilateral_precompiled_reduction_per_ms": (
            (baseline_value - final_unilateral) / precompiled_ms
        ),
        "nonworsening": nonworsening,
        "guard_semantics": _guard_semantics(
            baseline,
            candidates,
            result,
            payoff_span=payoff_span,
            guard=guard,
        ),
    }


def _source_state_rows(
    target: dict[str, Any],
    *,
    iterations: tuple[int, ...],
) -> tuple[
    list[dict[str, Any]],
    dict[int, dict[str, dict[str, float]]],
    dict[int, dict[str, dict[str, float]]],
]:
    rows = []
    currents = {}
    averages = {}
    for iteration in iterations:
        candidate = _source_search_candidate(target, iteration=iteration)
        state = candidate["state"]
        current = _current_policy_from_state(state)
        average = _average_policy_from_state(state)
        state_identity = (
            axis_cfr_checkpoint_digest(state) == state["state_sha256"]
            and candidate["state_sha256"] == state["state_sha256"]
            and int(state["iteration"]) == iteration
        )
        policy_identity = (
            policy_digest(current) == state["current_policy_sha256"]
            and policy_digest(average) == state["average_policy_sha256"]
            and candidate["quality"]["policy_sha256"]
            == state["average_policy_sha256"]
        )
        rows.append(
            {
                "iteration": iteration,
                "state_sha256": state["state_sha256"],
                "current_policy_sha256": state["current_policy_sha256"],
                "average_policy_sha256": state["average_policy_sha256"],
                "state_digest_identity": state_identity,
                "policy_digest_identity": policy_identity,
            }
        )
        currents[iteration] = current
        averages[iteration] = average
    return rows, currents, averages


def _run_target(
    *,
    parsed: dict[str, Any],
    source: dict[str, Any],
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
    source_target = _source_target(source, family=family, shift=shift)
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

    state_rows, current_policies, average_policies = _source_state_rows(
        source_target,
        iterations=parsed["source_search_iterations"],
    )
    baseline = dict(source_target["blueprint_quality"])
    payoff_span = float(topology.game.payoff_span)
    new_quality_rows = []
    candidates_by_id = {}
    for iteration in parsed["source_search_iterations"]:
        source_average = _source_search_candidate(
            source_target,
            iteration=iteration,
        )
        current_policy = current_policies[iteration]
        current_id = f"search_current{iteration}"
        current_quality = _evaluate_policy(
            topology=topology,
            workspace=target_workspace,
            sparse=sparse,
            automata=automata,
            gpu=gpu,
            hands_by_player=target_belief.hands_by_player,
            policy=current_policy,
            label=current_id,
            payoff_span=payoff_span,
            maximum_feature_width_per_batch=parsed[
                "maximum_feature_width_per_batch"
            ],
        )
        new_quality_rows.append(current_quality)
        candidates_by_id[current_id] = {
            "candidate_id": current_id,
            "policy_kind": "current",
            "search_iteration": iteration,
            "measurement_source": "ADR-0101-live",
            "cumulative_search_ms": float(source_average["cumulative_search_ms"]),
            "policy_statistics": policy_statistics(current_policy),
            "quality": current_quality,
            "state_sha256": source_average["state_sha256"],
        }
        average_id = f"search_average{iteration}"
        candidates_by_id[average_id] = {
            "candidate_id": average_id,
            "policy_kind": "average",
            "search_iteration": iteration,
            "measurement_source": "ADR-0099-source",
            "cumulative_search_ms": float(source_average["cumulative_search_ms"]),
            "policy_statistics": dict(source_average["policy_statistics"]),
            "quality": dict(source_average["quality"]),
            "state_sha256": source_average["state_sha256"],
        }
        if policy_digest(average_policies[iteration]) != candidates_by_id[
            average_id
        ]["quality"]["policy_sha256"]:
            raise AssertionError("source average policy differs from source quality")

    source_state4 = _source_search_candidate(
        source_target,
        iteration=parsed["extension_source_iteration"],
    )["state"]
    solver = _solver(
        parsed=parsed,
        belief=target_belief,
        topology=topology,
        workspace=target_workspace,
        sparse=sparse,
        automata=automata,
        cupy_sparse=gpu,
    )
    restore_axis_cfr_checkpoint(solver, source_state4)
    immediate = export_axis_cfr_checkpoint(
        solver,
        context=source_state4["context"],
        provenance=source_state4["provenance"],
    )
    restore_identity = immediate["state_sha256"] == source_state4["state_sha256"]
    unique_automata = {
        id(automaton): automaton
        for library in automata
        for automaton in library.values()
    }
    automaton_bytes = sum(value.numeric_bytes for value in unique_automata.values())
    extension_steps = []
    extension_ms = 0.0
    for iteration in range(
        parsed["extension_source_iteration"] + 1,
        parsed["final_search_iteration"] + 1,
    ):
        started = time.perf_counter()
        solver.step()
        step_ms = (time.perf_counter() - started) * 1000.0
        extension_ms += step_ms
        work = solver.last_step_work
        if work is None:
            raise AssertionError("candidate-stream extension step has no telemetry")
        extension_steps.append(
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

    context = {
        **dict(source_state4["context"]),
        "continuation_source_state_sha256": source_state4["state_sha256"],
    }
    provenance = {
        "audit": "ADR-0101",
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "acceptance_source_sha256": _sha256(_ACCEPTANCE_SOURCE),
    }
    state8 = export_axis_cfr_checkpoint(
        solver,
        context=context,
        provenance=provenance,
    )
    rendered_state8 = json.dumps(
        state8,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    checkpoint_identity = (
        int(state8["iteration"]) == parsed["final_search_iteration"]
        and axis_cfr_checkpoint_digest(json.loads(rendered_state8))
        == state8["state_sha256"]
    )
    replay_solver = _solver(
        parsed=parsed,
        belief=target_belief,
        topology=topology,
        workspace=target_workspace,
        sparse=sparse,
        automata=automata,
        cupy_sparse=gpu,
    )
    restore_axis_cfr_checkpoint(replay_solver, json.loads(rendered_state8))
    replay = export_axis_cfr_checkpoint(
        replay_solver,
        context=context,
        provenance=provenance,
    )
    checkpoint_identity = checkpoint_identity and (
        replay["state_sha256"] == state8["state_sha256"]
    )
    cumulative8 = (
        float(
            _source_search_candidate(
                source_target,
                iteration=parsed["extension_source_iteration"],
            )["cumulative_search_ms"]
        )
        + extension_ms
    )
    for kind, policy in (
        ("current", solver.current_strategy()),
        ("average", solver.average_strategy()),
    ):
        candidate_id = f"search_{kind}{parsed['final_search_iteration']}"
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
        if quality["policy_sha256"] != state8[f"{kind}_policy_sha256"]:
            raise AssertionError("iteration-8 policy differs from checkpoint")
        new_quality_rows.append(quality)
        candidates_by_id[candidate_id] = {
            "candidate_id": candidate_id,
            "policy_kind": kind,
            "search_iteration": parsed["final_search_iteration"],
            "measurement_source": "ADR-0101-live",
            "cumulative_search_ms": cumulative8,
            "policy_statistics": policy_statistics(policy),
            "quality": quality,
            "state_sha256": state8["state_sha256"],
        }

    candidates = [candidates_by_id[key] for key in parsed["candidate_order"]]
    for candidate in candidates:
        candidate["baseline_comparison"] = compare_acceptance(
            baseline,
            candidate["quality"],
            payoff_span=payoff_span,
            normalized_guard=parsed["acceptance_guard_normalized"],
        )
    portfolio_candidates = {
        "full_interleaved": candidates,
        "current_only": [row for row in candidates if row["policy_kind"] == "current"],
        "average_only": [row for row in candidates if row["policy_kind"] == "average"],
    }
    portfolios = {
        name: _portfolio_row(
            name=name,
            baseline=baseline,
            candidates=portfolio_candidates[name],
            payoff_span=payoff_span,
            guard=parsed["acceptance_guard_normalized"],
            target_compile_ms=target_compile_ms,
        )
        for name in parsed["portfolio_kinds"]
    }
    source_unilateral = float(
        source_target["sequential_incumbents"][
            "final_unilateral_normalized_nash_conv"
        ]
    )
    full_unilateral = float(
        portfolios["full_interleaved"][
            "final_unilateral_normalized_nash_conv"
        ]
    )
    source_state_identity = all(row["state_digest_identity"] for row in state_rows)
    source_policy_identity = all(row["policy_digest_identity"] for row in state_rows)
    finite = (
        _quality_finite(baseline)
        and all(_quality_finite(row["quality"]) for row in candidates)
        and all(_state_finite(row) for row in (source_state4, state8))
    )
    return {
        "range_family": family,
        "target_shift": shift,
        "target_descriptor": descriptor,
        "source_target_descriptor_sha256": _descriptor_digest(
            source_target["target_descriptor"]
        ),
        "rebuilt_target_descriptor_sha256": _descriptor_digest(descriptor),
        "target_descriptor_identity": descriptor_identity,
        "target_workspace_compile_ms": target_compile_ms,
        "information_sets": len(solver.information_schema()),
        "hand_action_entries": sum(
            len(actions) for actions in solver.information_schema().values()
        ),
        "blueprint_quality": baseline,
        "source_state_rows": state_rows,
        "source_state_digest_identity": source_state_identity,
        "source_policy_digest_identity": source_policy_identity,
        "extension_source_state_sha256": source_state4["state_sha256"],
        "extension_restore_identity": restore_identity,
        "extension_steps": extension_steps,
        "extension_training_ms": extension_ms,
        "final_iteration": state8["iteration"],
        "final_state_sha256": state8["state_sha256"],
        "final_state_json_bytes": len(rendered_state8.encode("utf-8")),
        "extension_checkpoint_identity": checkpoint_identity,
        "final_state": state8,
        "new_quality_evaluations": len(new_quality_rows),
        "candidates": candidates,
        "portfolios": portfolios,
        "source_average_only_through4_unilateral_normalized_nash_conv": (
            source_unilateral
        ),
        "full_stream_incremental_unilateral_reduction_over_source": (
            source_unilateral - full_unilateral
        ),
        "finite_states_policies_and_quality": finite,
    }


def _run_family(
    *,
    parsed: dict[str, Any],
    source: dict[str, Any],
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
                source=source,
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


def run_h32_warm_candidate_stream_audit(
    config: dict[str, Any],
) -> dict[str, Any]:
    parsed = parse_h32_warm_candidate_stream_config(config)
    import scipy

    cupy_started = time.perf_counter()
    cp, _ = _cupy_modules()
    cupy_import_ms = (time.perf_counter() - cupy_started) * 1000.0
    if np.__version__ != parsed["required_numpy_version"]:
        raise ValueError("NumPy version differs from ADR-0101")
    if scipy.__version__ != parsed["required_scipy_version"]:
        raise ValueError("SciPy version differs from ADR-0101")
    if cp.__version__ != parsed["required_cupy_version"]:
        raise ValueError("CuPy version differs from ADR-0101")
    if cp.cuda.runtime.runtimeGetVersion() != parsed["required_cuda_runtime_version"]:
        raise ValueError("CUDA runtime differs from ADR-0101")
    if cp.cuda.runtime.driverGetVersion() < parsed["minimum_cuda_driver_version"]:
        raise ValueError("CUDA driver is older than the ADR-0101 floor")
    if str(cp.cuda.Device(0).compute_capability) != parsed["required_compute_capability"]:
        raise ValueError("GPU compute capability differs from ADR-0101")
    if not os.environ.get(parsed["cuda_dll_environment_variable"]):
        raise ValueError("optional CUDA DLL directory is not configured")

    width_source = json.loads(_WIDTH_SOURCE.read_text(encoding="utf-8"))
    if (
        int(width_source["aggregate"]["selected_width"])
        != parsed["maximum_feature_width_per_batch"]
    ):
        raise ValueError("ADR-0096 selected width differs from candidate-stream width")
    shifted_control = json.loads(_SHIFTED_H4_CONTROL.read_text(encoding="utf-8"))
    if not bool(shifted_control["passed_existing_1e_10_identity_standard"]):
        raise ValueError("shifted h4 dense control is not accepted")
    source = json.loads(_ACCEPTANCE_SOURCE.read_text(encoding="utf-8"))
    acceptance_source_identity = (
        source["status"] == "frozen_audit_executed"
        and bool(source["gates"]["passed"])
        and source["config_sha256"]
        == "b5cbc538d51f09aad5aa6dca6c860865afd849196b65560ea3338d83293d7f8d"
        and source["implementation_sha256"]
        == parsed["expected_acceptance_implementation_sha256"]
    )
    if not acceptance_source_identity:
        raise ValueError("ADR-0099 acceptance source identity rejected")

    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    family_rows = []
    for family in parsed["range_families"]:
        release_cupy_memory_pool()
        gc.collect()
        family_rows.append(
            _run_family(
                parsed=parsed,
                source=source,
                board=board,
                family=family,
            )
        )
    targets = [target for family in family_rows for target in family["targets"]]
    candidates = [candidate for target in targets for candidate in target["candidates"]]
    new_quality_rows = [
        candidate["quality"]
        for candidate in candidates
        if candidate["measurement_source"] == "ADR-0101-live"
    ]
    all_quality_rows = [target["blueprint_quality"] for target in targets] + [
        candidate["quality"] for candidate in candidates
    ]
    steps = [step for target in targets for step in target["extension_steps"]]
    full_portfolios = [target["portfolios"]["full_interleaved"] for target in targets]
    source_unilateral = math.fsum(
        float(target["source_average_only_through4_unilateral_normalized_nash_conv"])
        for target in targets
    )
    full_unilateral = math.fsum(
        float(row["final_unilateral_normalized_nash_conv"])
        for row in full_portfolios
    )
    baseline_total = math.fsum(
        float(target["blueprint_quality"]["normalized_nash_conv"])
        for target in targets
    )
    accepted_current_rows = [
        (target, trace)
        for target in targets
        for trace in target["portfolios"]["full_interleaved"]["trace"]
        if "_current" in trace["candidate_id"]
        and bool(trace["unilateral_comparison"]["unilateral_accept"])
    ]
    strength_current_accepts = [
        row
        for row in accepted_current_rows
        if row[0]["target_shift"] == "all_seat_strength_1_to2"
    ]
    average8_strength_accepts = [
        candidate
        for target in targets
        if target["target_shift"] == "all_seat_strength_1_to2"
        for candidate in target["candidates"]
        if candidate["candidate_id"] == "search_average8"
        and bool(candidate["baseline_comparison"]["unilateral_accept"])
    ]
    current_only_total = math.fsum(
        float(target["portfolios"]["current_only"]["final_unilateral_normalized_nash_conv"])
        for target in targets
    )
    average_only_total = math.fsum(
        float(target["portfolios"]["average_only"]["final_unilateral_normalized_nash_conv"])
        for target in targets
    )
    gates = parsed["gates"]
    aggregate = {
        "maximum_training_step_ms": max(float(row["wall_ms"]) for row in steps),
        "maximum_quality_evaluation_ms": max(
            float(row["wall_ms"]) for row in new_quality_rows
        ),
        "maximum_target_workspace_compile_ms": max(
            float(row["target_workspace_compile_ms"]) for row in targets
        ),
        "maximum_host_peak_numeric_bytes": max(
            max(int(row["maximum_host_peak_numeric_bytes"]) for row in steps),
            max(
                int(row["maximum_host_peak_numeric_bytes"])
                for row in new_quality_rows
            ),
        ),
        "maximum_gpu_pool_bytes": max(
            max(int(row["maximum_gpu_pool_bytes"]) for row in steps),
            max(int(row["maximum_gpu_pool_bytes"]) for row in new_quality_rows),
        ),
        "maximum_quality_zero_sum_residual": max(
            float(row["zero_sum_residual"]) for row in all_quality_rows
        ),
        "source_average_only_through4_total_unilateral_normalized_nash_conv": (
            source_unilateral
        ),
        "full_stream_total_unilateral_normalized_nash_conv": full_unilateral,
        "full_stream_incremental_unilateral_reduction_over_source": (
            source_unilateral - full_unilateral
        ),
        "full_stream_total_unilateral_reduction_from_blueprints": (
            baseline_total - full_unilateral
        ),
        "accepted_current_candidates": len(accepted_current_rows),
        "accepted_strength_current_candidates": len(strength_current_accepts),
        "accepted_strength_average8_candidates": len(average8_strength_accepts),
        "current_only_total_unilateral_normalized_nash_conv": current_only_total,
        "average_only_total_unilateral_normalized_nash_conv": average_only_total,
        "wall_seconds_before_result_serialization": time.perf_counter() - started,
    }
    gate_results = {
        "target_row_count": len(targets) == gates["expected_target_rows"],
        "target_rows_per_family": all(
            len(row["targets"]) == gates["expected_target_rows_per_family"]
            for row in family_rows
        ),
        "source_state_count": all(
            len(row["source_state_rows"])
            == gates["expected_source_states_per_target"]
            for row in targets
        ),
        "new_quality_evaluation_count": all(
            int(row["new_quality_evaluations"])
            == gates["expected_new_quality_evaluations_per_target"]
            for row in targets
        ),
        "candidate_stream_count": all(
            len(row["candidates"])
            == gates["expected_candidate_stream_rows_per_target"]
            for row in targets
        ),
        "extension_step_count": all(
            len(row["extension_steps"])
            == gates["expected_extension_steps_per_target"]
            for row in targets
        ),
        "final_iteration": all(
            int(row["final_iteration"]) == gates["expected_final_search_iteration"]
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
                int(step["terminal_sparse_batches"])
                == int(gates["expected_sparse_batches_by_family"][row["range_family"]])
                for step in row["extension_steps"]
            )
            and all(
                int(candidate["quality"]["terminal_sparse_batches"])
                == int(gates["expected_sparse_batches_by_family"][row["range_family"]])
                for candidate in row["candidates"]
            )
            for row in targets
        ),
        "acceptance_source_identity": acceptance_source_identity
        == gates["require_acceptance_source_identity"],
        "target_descriptor_identity": all(
            bool(row["target_descriptor_identity"]) for row in targets
        )
        == gates["require_target_descriptor_identity"],
        "source_state_digest_identity": all(
            bool(row["source_state_digest_identity"]) for row in targets
        )
        == gates["require_source_state_digest_identity"],
        "source_policy_digest_identity": all(
            bool(row["source_policy_digest_identity"]) for row in targets
        )
        == gates["require_source_policy_digest_identity"],
        "extension_restore_identity": all(
            bool(row["extension_restore_identity"]) for row in targets
        )
        == gates["require_extension_restore_identity"],
        "extension_checkpoint_identity": all(
            bool(row["extension_checkpoint_identity"]) for row in targets
        )
        == gates["require_extension_checkpoint_identity"],
        "portfolio_nonworsening": all(
            bool(portfolio["nonworsening"])
            for row in targets
            for portfolio in row["portfolios"].values()
        )
        == gates["require_portfolio_nonworsening"],
        "portfolio_guard_semantics": all(
            bool(portfolio["guard_semantics"])
            for row in targets
            for portfolio in row["portfolios"].values()
        )
        == gates["require_portfolio_guard_semantics"],
        "training_latency": aggregate["maximum_training_step_ms"]
        <= gates["maximum_training_step_ms"],
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
        "finite_states_policies_and_quality": all(
            bool(row["finite_states_policies_and_quality"]) for row in targets
        )
        == gates["require_finite_states_policies_and_quality"],
        "total_wall": aggregate["wall_seconds_before_result_serialization"]
        <= gates["maximum_total_audit_seconds"],
    }
    gate_results["passed"] = all(gate_results.values())
    hypotheses = {
        "any_current_candidate_unilateral_safe": bool(accepted_current_rows),
        "any_strength_current_candidate_unilateral_safe": bool(
            strength_current_accepts
        ),
        "any_strength_average8_candidate_unilateral_safe_vs_blueprint": bool(
            average8_strength_accepts
        ),
        "full_stream_improves_over_source_average_only_through4": (
            full_unilateral < source_unilateral - parsed["acceptance_guard_normalized"]
        ),
        "full_stream_unilateral_reduction_positive": (
            full_unilateral < baseline_total - parsed["acceptance_guard_normalized"]
        ),
        "current_only_beats_average_only": (
            current_only_total
            < average_only_total - parsed["acceptance_guard_normalized"]
        ),
    }
    properties = cp.cuda.runtime.getDeviceProperties(0)
    name = properties["name"]
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    return {
        "schema_version": 1,
        "experiment_type": "h32_warm_current_and_average_candidate_stream_through8",
        "status": "frozen_audit_executed",
        "config": parsed,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
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
            "new_quality_rows": len(new_quality_rows),
            "extension_steps": len(steps),
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
            "The matrix remains one river board, one bet size, equal stacks, two generated beliefs, and two deterministic shifts.",
            "Current policies and iteration-8 policies are evaluated after ADR-0099; no strategic outcome is a mechanism gate.",
            "The exact leaf-adjoint evaluator remains an offline teacher, not an online verifier.",
            "Candidate order is one declared current-then-average stream; no order selector is fitted.",
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
    result = run_h32_warm_candidate_stream_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "h32 warm candidate stream: "
        f"targets={result['counts']['target_rows']}, "
        f"new_quality={result['counts']['new_quality_rows']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
