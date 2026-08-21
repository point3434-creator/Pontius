"""Frozen one-size response-certificate latency bridge for the fresh h32 panel."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import statistics
import time
from typing import Any

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .cupy_sparse_incidence import CuPyBidirectionalIncidence, release_cupy_memory_pool
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_fresh_board_panel_cache_preflight import _json_digest
from .h32_fresh_panel_target_transfer_audit import _solver
from .h32_resident_cfr_audit import _resident_caches, _step_row
from .h32_warm_search_acceptance_audit import _average_policy_from_state, build_target_belief
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .real_policy import policy_digest
from .reporting import environment_metadata
from .resident_leaf_adjoint_evaluation import verify_resident_leaf_adjoint_candidate
from .river import parse_cards


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-response-latency-bridge-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-response-latency-bridge-v1.json"
_BASE_CONFIG = _ROOT / "experiments/configs/h32-fresh-panel-target-transfer-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_TEACHER = _ROOT / "experiments/results/h32-fresh-panel-target-transfer-v2.json"
_DELTA_CONTRACT = _ROOT / "src/pontius/delta_certificate_contract.py"
_RESIDENT_EVALUATION = _ROOT / "src/pontius/resident_leaf_adjoint_evaluation.py"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_response_latency_bridge_audit.py"

_PATHS = {
    "expected_base_config_sha256": _BASE_CONFIG,
    "expected_source_result_sha256": _SOURCE,
    "expected_teacher_result_sha256": _TEACHER,
    "expected_delta_contract_sha256": _DELTA_CONTRACT,
    "expected_resident_evaluation_sha256": _RESIDENT_EVALUATION,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required response-bridge input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_response_latency_bridge_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the immutable, outcome-neutral response-bridge protocol."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "candidate_id",
        "target_order",
        "seat_order",
        "decision_budget_ms",
        "unmeasured_emission_reserve_scenarios_ms",
        "cache_residency_precondition",
        "deadline_interpretation",
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
    if set(config) != fields:
        raise ValueError("response-latency bridge fields differ from ADR-0155")
    target_order = [
        f"{source}/{shift}"
        for source in (
            "panel_1/balanced",
            "panel_1/blocker_heavy",
            "panel_2/blocker_heavy",
            "panel_2/balanced",
            "panel_3/balanced",
            "panel_3/blocker_heavy",
        )
        for shift in ("local_blocker_seat3_x2", "all_seat_strength_1_to2")
    ]
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0154_before_any_fresh_panel_response_bridge_rerun"
        ),
        "candidate_id": "search_current1",
        "target_order": target_order,
        "seat_order": [0, 1, 2, 3, 4, 5],
        "decision_budget_ms": 15000.0,
        "unmeasured_emission_reserve_scenarios_ms": [0.0, 250.0, 500.0, 1000.0],
        "cache_residency_precondition": (
            "exact_target_belief_workspace_gpu_incidence_and_six_seat_caches_complete"
        ),
        "deadline_interpretation": (
            "descriptive_sensitivity_only_until_state_ingest_and_action_emission_tails_are_measured"
        ),
        "maximum_feature_width_per_batch": 384,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("response-latency bridge workload differs from ADR-0155")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"response-latency bridge source mismatch: {field}")
    gates = {
        "expected_target_rows": 12,
        "expected_search_steps": 12,
        "expected_candidate_profiles": 12,
        "expected_new_strategy_quality_labels": 0,
        "maximum_teacher_utility_error": 1e-9,
        "maximum_teacher_best_response_error": 1e-9,
        "maximum_teacher_deviation_gain_error": 1e-9,
        "maximum_target_workspace_compile_ms": 30000.0,
        "maximum_gpu_incidence_compile_ms": 30000.0,
        "maximum_cache_compile_ms": 120000.0,
        "maximum_solver_prepare_ms": 30000.0,
        "maximum_search_step_ms": 60000.0,
        "maximum_response_certificate_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_total_audit_seconds": 900.0,
        "require_clean_git_state": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_stop_identity": True,
        "require_finite": True,
        "require_blueprint_fallback_on_incomplete_certificate": True,
        "require_zero_new_strategy_quality_labels": True,
        "require_strategy_quality_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("response-latency bridge gates differ from ADR-0155")
    return {
        **config,
        "target_order": tuple(target_order),
        "seat_order": tuple(config["seat_order"]),
        "unmeasured_emission_reserve_scenarios_ms": tuple(
            config["unmeasured_emission_reserve_scenarios_ms"]
        ),
        "gates": dict(gates),
    }


def _teacher_target(teacher: dict[str, Any], target: str) -> dict[str, Any]:
    return next(row for row in teacher["targets"] if row["target"] == target)


def _teacher_candidate(target: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    return next(row for row in target["candidates"] if row["candidate_id"] == candidate_id)


def _expected_stop(
    *,
    gains: tuple[float, ...],
    blueprint_gains: tuple[float, ...],
    best_complete_nash_conv: float,
    raw_guard: float,
    seat_order: tuple[int, ...],
) -> tuple[str, int]:
    partial = 0.0
    for seat in seat_order:
        gain = gains[seat]
        partial += gain
        if gain > blueprint_gains[seat] + raw_guard:
            return "blueprint_cap", seat
        if partial > best_complete_nash_conv + raw_guard:
            return "objective_lower_bound", seat
    return "complete", -1


def _quantiles(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "minimum_ms": ordered[0],
        "median_ms": statistics.median(ordered),
        "maximum_ms": ordered[-1],
    }


def _run_target(
    *,
    parsed: dict[str, Any],
    base: dict[str, Any],
    source: dict[str, Any],
    teacher: dict[str, Any],
    target_key: str,
) -> dict[str, Any]:
    board_id, family, shift = target_key.split("/", 2)
    panel = next(row for row in base["panels"] if row["board_id"] == board_id)
    board = parse_cards(*panel["cards"])
    source_belief, layout, sparse, retained = _build_case(
        parsed=base,
        board=board,
        hand_count=base["hands_per_player"],
        family=family,
    )
    source_workspace, _source_timing, automata = retained
    source_row = next(
        row for row in source["source_rows"] if row["source"] == f"{board_id}/{family}"
    )
    state = source_row["final_checkpoint"]
    source_identity = (
        axis_cfr_checkpoint_digest(state) == state["state_sha256"]
        and _belief_digest(source_belief)
        == base["source_belief_sha256_by_source"][f"{board_id}/{family}"]
    )
    blueprint = _average_policy_from_state(state)
    target_belief, descriptor = build_target_belief(
        source_belief,
        board=board,
        shift=shift,
        local_blocker_target_seat=base["local_blocker_target_seat"],
    )
    target_digest = _belief_digest(target_belief)
    descriptor_digest = _json_digest(descriptor)
    target_identity = (
        target_digest == base["target_belief_sha256_by_target"][target_key]
        and descriptor_digest == base["target_descriptor_sha256_by_target"][target_key]
    )

    tick = time.perf_counter()
    target_base = FactorTTBeliefWorkspace.compile(
        source_workspace.topology.base,
        target_belief,
        query_chunk_records=base["query_chunk_records"],
    )
    workspace = OpenModeFactorTTWorkspace.compile(source_workspace.topology, target_base)
    target_workspace_compile_ms = (time.perf_counter() - tick) * 1000.0

    tick = time.perf_counter()
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    gpu_incidence_compile_ms = (time.perf_counter() - tick) * 1000.0
    belief_cache, automaton_caches, cache_compile_ms = _resident_caches(workspace, automata)

    tick = time.perf_counter()
    solver = _solver(
        base,
        target_belief,
        layout,
        workspace,
        sparse,
        automata,
        gpu,
        belief_cache,
        automaton_caches,
    )
    solver.warm_start(
        blueprint,
        base["warm_regret_mass_payoff_fraction"] * float(layout.game.payoff_span),
    )
    solver_prepare_ms = (time.perf_counter() - tick) * 1000.0

    tick = time.perf_counter()
    solver.step()
    search_step_ms = (time.perf_counter() - tick) * 1000.0
    if solver.last_step_work is None:
        raise AssertionError("response bridge search telemetry absent")
    candidate = solver.current_strategy()

    teacher_row = _teacher_target(teacher, target_key)
    teacher_candidate = _teacher_candidate(teacher_row, parsed["candidate_id"])
    blueprint_gains = tuple(float(v) for v in teacher_row["blueprint_quality"]["deviation_gains"])
    teacher_gains = tuple(float(v) for v in teacher_candidate["quality"]["deviation_gains"])
    raw_guard = float(teacher_row["certificate"]["raw_guard"])
    expected_reason, expected_seat = _expected_stop(
        gains=teacher_gains,
        blueprint_gains=blueprint_gains,
        best_complete_nash_conv=float(teacher_row["blueprint_quality"]["nash_conv"]),
        raw_guard=raw_guard,
        seat_order=parsed["seat_order"],
    )
    verified = verify_resident_leaf_adjoint_candidate(
        candidate_id=parsed["candidate_id"],
        layout=layout,
        workspace=workspace,
        sparse=sparse,
        policy=candidate,
        terminal_automata=automata,
        hands_by_player=target_belief.hands_by_player,
        blueprint_deviation_gains=blueprint_gains,
        best_complete_nash_conv=float(teacher_row["blueprint_quality"]["nash_conv"]),
        payoff_span=float(layout.game.payoff_span),
        raw_guard=raw_guard,
        seat_order=parsed["seat_order"],
        belief_cache=belief_cache,
        automaton_caches=automaton_caches,
        cupy_sparse=gpu,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
    )
    errors = []
    teacher_seats = {int(row["target_player"]): row for row in teacher_candidate["quality"]["seat_rows"]}
    for row in verified["seat_rows"]:
        expected = teacher_seats[int(row["target_player"])]
        errors.append(
            {
                "target_player": int(row["target_player"]),
                "utility_error": abs(float(row["profile_utility"]) - float(expected["profile_utility"])),
                "best_response_error": abs(
                    float(row["best_response_value"]) - float(expected["best_response_value"])
                ),
                "deviation_gain_error": abs(
                    float(row["deviation_gain"]) - float(expected["deviation_gain"])
                ),
            }
        )

    stop_identity = (
        verified["stop_reason"] == expected_reason
        and (verified["stop_seat"] if verified["stop_seat"] is not None else -1)
        == expected_seat
    )
    selection_started = time.perf_counter()
    selected_candidate_id = (
        parsed["candidate_id"] if verified["complete"] else "blueprint_average64"
    )
    selection_ms = (time.perf_counter() - selection_started) * 1000.0
    prepared_ms = search_step_ms + float(verified["wall_ms"]) + selection_ms
    target_cache_resident_ms = solver_prepare_ms + prepared_ms
    cold_target_ms = (
        target_workspace_compile_ms
        + gpu_incidence_compile_ms
        + cache_compile_ms
        + target_cache_resident_ms
    )
    ledgers = []
    for reserve in parsed["unmeasured_emission_reserve_scenarios_ms"]:
        ledgers.append(
            {
                "unmeasured_emission_reserve_ms": reserve,
                "prepared_total_ms": prepared_ms + reserve,
                "target_cache_resident_total_ms": target_cache_resident_ms + reserve,
                "cold_target_total_ms": cold_target_ms + reserve,
                "prepared_within_15s": prepared_ms + reserve <= parsed["decision_budget_ms"],
                "target_cache_resident_within_15s": (
                    target_cache_resident_ms + reserve <= parsed["decision_budget_ms"]
                ),
                "cold_target_within_15s": (
                    cold_target_ms + reserve <= parsed["decision_budget_ms"]
                ),
            }
        )
    result = {
        "target": target_key,
        "source_checkpoint_identity": source_identity,
        "target_identity": target_identity,
        "target_belief_sha256": target_digest,
        "target_descriptor_sha256": descriptor_digest,
        "blueprint_policy_sha256": policy_digest(blueprint),
        "candidate_policy_sha256": policy_digest(candidate),
        "teacher_candidate_policy_sha256": teacher_candidate["policy_sha256"],
        "policy_digest_identity_expected": False,
        "target_workspace_compile_ms": target_workspace_compile_ms,
        "gpu_incidence_compile_ms": gpu_incidence_compile_ms,
        "cache_compile_ms": cache_compile_ms,
        "solver_prepare_ms": solver_prepare_ms,
        "search_step": _step_row(solver.last_step_work, wall_ms=search_step_ms),
        "response_certificate": verified,
        "teacher_errors": errors,
        "expected_stop_reason": expected_reason,
        "expected_stop_seat": expected_seat,
        "stop_identity": stop_identity,
        "selection_ms": selection_ms,
        "selected_candidate_id": selected_candidate_id,
        "blueprint_fallback": selected_candidate_id == "blueprint_average64",
        "prepared_ms_before_unmeasured_emission": prepared_ms,
        "target_cache_resident_ms_before_unmeasured_emission": target_cache_resident_ms,
        "cold_target_ms_before_unmeasured_emission": cold_target_ms,
        "deadline_ledgers": ledgers,
    }
    del solver, automaton_caches, belief_cache, gpu, workspace, target_base
    del automata, source_workspace, sparse, layout, target_belief, source_belief
    gc.collect()
    release_cupy_memory_pool()
    return result


def run_h32_response_latency_bridge_audit(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_response_latency_bridge_config(config)
    base = json.loads(_BASE_CONFIG.read_text(encoding="utf-8"))
    source = json.loads(_SOURCE.read_text(encoding="utf-8"))
    teacher = json.loads(_TEACHER.read_text(encoding="utf-8"))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    if git["dirty"]:
        raise RuntimeError("response-latency bridge requires a clean Git state")
    rows = []
    for target in parsed["target_order"]:
        print(f"bridging {target}", flush=True)
        rows.append(
            _run_target(
                parsed=parsed,
                base=base,
                source=source,
                teacher=teacher,
                target_key=target,
            )
        )
    elapsed = time.perf_counter() - started
    gates = parsed["gates"]
    errors = [error for row in rows for error in row["teacher_errors"]]
    certificates = [row["response_certificate"] for row in rows]
    gate_results = {
        "clean_git": (not git["dirty"]) == gates["require_clean_git_state"],
        "target_count": len(rows) == gates["expected_target_rows"],
        "step_count": len(rows) == gates["expected_search_steps"],
        "candidate_count": len(rows) == gates["expected_candidate_profiles"],
        "source_identity": all(row["source_checkpoint_identity"] for row in rows)
        == gates["require_source_checkpoint_identity"],
        "target_identity": all(row["target_identity"] for row in rows)
        == gates["require_target_identity"],
        "stop_identity": all(row["stop_identity"] for row in rows)
        == gates["require_stop_identity"],
        "utility_error": max(error["utility_error"] for error in errors)
        <= gates["maximum_teacher_utility_error"],
        "best_response_error": max(error["best_response_error"] for error in errors)
        <= gates["maximum_teacher_best_response_error"],
        "deviation_gain_error": max(error["deviation_gain_error"] for error in errors)
        <= gates["maximum_teacher_deviation_gain_error"],
        "target_workspace_time": all(
            row["target_workspace_compile_ms"] <= gates["maximum_target_workspace_compile_ms"]
            for row in rows
        ),
        "gpu_incidence_time": all(
            row["gpu_incidence_compile_ms"] <= gates["maximum_gpu_incidence_compile_ms"]
            for row in rows
        ),
        "cache_time": all(
            row["cache_compile_ms"] <= gates["maximum_cache_compile_ms"] for row in rows
        ),
        "solver_prepare_time": all(
            row["solver_prepare_ms"] <= gates["maximum_solver_prepare_ms"] for row in rows
        ),
        "search_step_time": all(
            row["search_step"]["wall_ms"] <= gates["maximum_search_step_ms"] for row in rows
        ),
        "certificate_time": all(
            row["response_certificate"]["wall_ms"]
            <= gates["maximum_response_certificate_ms"]
            for row in rows
        ),
        "gpu_pool": all(
            max(
                int(row["search_step"]["maximum_gpu_pool_bytes"]),
                int(row["response_certificate"]["maximum_gpu_pool_bytes"]),
            )
            <= gates["maximum_gpu_pool_bytes"]
            for row in rows
        ),
        "finite": all(
            math.isfinite(float(value))
            for row in rows
            for value in (
                row["target_workspace_compile_ms"],
                row["gpu_incidence_compile_ms"],
                row["cache_compile_ms"],
                row["solver_prepare_ms"],
                row["search_step"]["wall_ms"],
                row["response_certificate"]["wall_ms"],
            )
        )
        == gates["require_finite"],
        "fail_closed": all(
            row["response_certificate"]["complete"] or row["blueprint_fallback"]
            for row in rows
        )
        == gates["require_blueprint_fallback_on_incomplete_certificate"],
        "zero_new_quality_labels": (0 == gates["expected_new_strategy_quality_labels"])
        == gates["require_zero_new_strategy_quality_labels"],
        "strategy_quality_claim_null": True == gates["require_strategy_quality_claim_null"],
        "wall_time": elapsed <= gates["maximum_total_audit_seconds"],
    }
    deadline = []
    for reserve in parsed["unmeasured_emission_reserve_scenarios_ms"]:
        ledgers = [
            next(
                item
                for item in row["deadline_ledgers"]
                if item["unmeasured_emission_reserve_ms"] == reserve
            )
            for row in rows
        ]
        deadline.append(
            {
                "unmeasured_emission_reserve_ms": reserve,
                "prepared_within_15s_count": sum(item["prepared_within_15s"] for item in ledgers),
                "target_cache_resident_within_15s_count": sum(
                    item["target_cache_resident_within_15s"] for item in ledgers
                ),
                "cold_target_within_15s_count": sum(item["cold_target_within_15s"] for item in ledgers),
            }
        )
    passed = all(gate_results.values())
    result = {
        "schema_version": 1,
        "status": "frozen_h32_response_latency_bridge_executed",
        "config": config,
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "environment": {**environment_metadata(), **runtime, "git": git},
        "rows": rows,
        "gate_results": gate_results,
        "passed": passed,
        "decision": (
            "accept_response_latency_measurement"
            if passed
            else "reject_response_latency_measurement"
        ),
        "timing_summary": {
            "search_step": _quantiles([float(row["search_step"]["wall_ms"]) for row in rows]),
            "response_certificate": _quantiles(
                [float(row["response_certificate"]["wall_ms"]) for row in rows]
            ),
            "prepared_before_unmeasured_emission": _quantiles(
                [float(row["prepared_ms_before_unmeasured_emission"]) for row in rows]
            ),
            "target_cache_resident_before_unmeasured_emission": _quantiles(
                [float(row["target_cache_resident_ms_before_unmeasured_emission"]) for row in rows]
            ),
            "cold_target_before_unmeasured_emission": _quantiles(
                [float(row["cold_target_ms_before_unmeasured_emission"]) for row in rows]
            ),
            "total_audit_seconds": elapsed,
        },
        "deadline_sensitivity": deadline,
        "counts": {
            "targets": len(rows),
            "search_steps": len(rows),
            "candidate_profiles": len(rows),
            "evaluated_seats": sum(
                int(row["response_certificate"]["evaluated_seat_count"]) for row in rows
            ),
            "complete_certificates": sum(row["response_certificate"]["complete"] for row in rows),
            "blueprint_fallbacks": sum(row["blueprint_fallback"] for row in rows),
            "new_strategy_quality_labels": 0,
            "sized_trees_constructed": 0,
        },
        "deployment_authorized": False,
        "strategy_quality_claim": None,
        "limitations": [
            "The response bridge replays an already labeled one-size candidate class.",
            "The prepared clock requires the exact target cache and solver warm state before the clock.",
            "Emission reserves are sensitivity scenarios, not measured action-emission tails.",
            "No p95 or p99 population claim is made from twelve heterogeneous one-shot targets.",
            "No two-size tree or new strategy-quality profile was evaluated.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    cp.get_default_memory_pool().free_all_blocks()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_response_latency_bridge_audit(args.config, args.output)
    print(
        "h32 response latency bridge: "
        f"passed={result['passed']}, "
        f"fallbacks={result['counts']['blueprint_fallbacks']}, "
        f"wall={result['timing_summary']['total_audit_seconds']:.3f}s"
    )


if __name__ == "__main__":
    main()
