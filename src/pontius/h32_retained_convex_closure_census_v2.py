"""Target-isolated wrapper for the sealed retained h32 closure census."""

from __future__ import annotations

import argparse
from collections import Counter
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping

from . import h32_retained_convex_closure_census as v1
from .cupy_sparse_incidence import release_cupy_memory_pool
from .h32_fresh_union_value_audit import _memory_snapshot
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    serialize_result,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-retained-convex-closure-census-v2.json"
_BASE_CONFIG = (
    _ROOT / "experiments/configs/h32-retained-convex-closure-census-v1.json"
)
_OUTPUT = _ROOT / "experiments/results/h32-retained-convex-closure-census-v2.json"
_CHECKPOINT = (
    _ROOT / "experiments/results/h32-retained-convex-closure-census-v2.partial.json"
)
_REJECTION = (
    _ROOT
    / "docs/decisions/ADR-0268-reject-partial-closure-census-on-master-verification-failure.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_retained_convex_closure_census_v2.py"
_PATHS = {
    "expected_base_config_sha256": _BASE_CONFIG,
    "expected_base_runner_sha256": v1._IMPLEMENTATION,
    "expected_base_control_test_sha256": v1._TEST,
    "expected_rejection_decision_sha256": _REJECTION,
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required isolated-census input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_retained_convex_closure_census_v2_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "base_preregistration_commit",
        "rejected_invocation_commit",
        "scope",
        "inheritance_rule",
        "partial_label_disclosure",
        "target_isolation_rule",
        "checkpoint_rule",
        "allowed_target_error",
        "diagnostic_rule",
        "decision_rule",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("isolated closure-census fields differ from ADR-0269")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"isolated closure-census provenance mismatch: {field}")
    exact = {
        "evidence_stage": (
            "corrective_preregistration_after_adr0268_before_any_recomputed_"
            "retrospective_oracle"
        ),
        "base_preregistration_commit": "f35ee5113df2643563b4865d41305c7c37baaea6",
        "rejected_invocation_commit": "f35ee5113df2643563b4865d41305c7c37baaea6",
        "scope": "same_42_targets_same_order_same_math_as_adr0267",
        "inheritance_rule": (
            "load_and_parse_the_byte_pinned_adr0267_config_without_changing_"
            "any_target_tolerance_round_time_memory_or_decision_field"
        ),
        "partial_label_disclosure": (
            "targets_1_to_5_printed_target_6_master_state_opened_by_rejected_"
            "invocation_all_recomputed_without_adaptation"
        ),
        "target_isolation_rule": (
            "catch_checkpoint_and_continue_only_the_known_master_primal_dual_"
            "verification_arithmetic_error_other_errors_checkpoint_but_fail_process"
        ),
        "checkpoint_rule": (
            "atomically_rewrite_a_complete_partial_json_after_every_target_"
            "outcome_before_starting_the_next_target"
        ),
        "allowed_target_error": (
            "ArithmeticError:behavioral master primal/dual verification failed"
        ),
        "diagnostic_rule": (
            "record_exception_type_message_target_and_post_cleanup_memory_no_"
            "tolerance_change_no_candidate_no_authority"
        ),
        "decision_rule": (
            "inherit_adr0267_universal_one_round_and_full_closure_branches_"
            "with_any_target_error_or_stall_forcing_the_censored_fallback_branch"
        ),
    }
    for field, expected_value in exact.items():
        if config[field] != expected_value:
            raise ValueError(f"isolated closure field differs from ADR-0269: {field}")
    gates = {
        "expected_targets": 42,
        "expected_recomputed_printed_targets": 5,
        "expected_recomputed_failed_target": (
            "panel_3/blocker_heavy/checks_then_bet_seat5"
        ),
        "require_clean_git_state": True,
        "require_base_config_identity": True,
        "require_inventory_identity": True,
        "require_all_targets_attempted_in_order": True,
        "require_checkpoint_after_every_outcome": True,
        "require_known_errors_only": True,
        "require_failed_target_censored": True,
        "require_completed_target_validity": True,
        "require_keystone_replay_when_completed": True,
        "require_post_fold_labels_zero": True,
        "require_blueprint_emission": True,
        "require_partial_label_disclosure": True,
        "require_strategy_population_claim_null": True,
        "require_finite": True,
    }
    if config["gates"] != gates:
        raise ValueError("isolated closure-census gates differ from ADR-0269")
    base = v1.parse_h32_retained_convex_closure_census_config(
        json.loads(_BASE_CONFIG.read_text(encoding="utf-8"))
    )
    return {**config, "base": base, "gates": gates}


def _finite_tree(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return True


def _completed_target_checks(
    row: Mapping[str, Any],
    base: Mapping[str, Any],
) -> dict[str, bool]:
    gate = base["gates"]
    if row["setup_mode"] == "checks_then_bet_wide_last_responder":
        shape = (
            row["acting_public_nodes_measured"]
            == gate["expected_wide_acting_public_nodes"]
            and row["behavioral_information_sets_measured"]
            == gate["expected_wide_information_sets"]
            and row["policy_variables_measured"]
            == gate["expected_wide_policy_variables"]
        )
    else:
        shape = (
            row["acting_public_nodes_measured"]
            == gate["expected_current_acting_public_nodes"]
            and row["behavioral_information_sets_measured"]
            == gate["expected_current_information_sets"]
            and row["policy_variables_measured"]
            == gate["expected_current_policy_variables"]
        )
    iterations = row["iterations"]
    cut_rows = [cut for iteration in iterations for cut in iteration["cut_rows"]]
    checks = {
        "identity": bool(
            row["source_checkpoint_identity"]
            and row["target_identity"]
            and row["blueprint_identity"]
        ),
        "warm_start": (
            row["warm_start_distance"]["maximum_probability_error"]
            <= gate["maximum_warm_start_probability_error"]
            and row["warm_start_distance"]["mean_total_variation"]
            <= gate["maximum_warm_start_mean_total_variation"]
        ),
        "shape": shape and row["epigraph_variables"] == 6,
        "topology": bool(row["path_single_visit"]),
        "initial_counts": (
            row["initial_profile_passes"] == gate["expected_initial_profile_passes"]
            and row["initial_response_passes"]
            == gate["expected_initial_response_passes"]
            and row["initial_gain_rows"] == gate["expected_initial_gain_rows"]
        ),
        "numeric_identity": (
            row["maximum_initial_row_error"] <= gate["maximum_initial_row_error"]
            and row["maximum_cut_row_error"] <= gate["maximum_cut_row_error"]
            and row["maximum_profile_equivalence_error"]
            <= gate["maximum_profile_equivalence_error"]
            and row["maximum_projection_error"] <= gate["maximum_projection_error"]
            and row["maximum_master_primal_error"]
            <= gate["maximum_master_primal_error"]
            and row["maximum_master_dual_error"]
            <= gate["maximum_master_dual_error"]
        ),
        "raw_guard": abs(row["raw_guard"] - 3e-9)
        <= gate["maximum_raw_guard_error"],
        "bounds": bool(row["lower_bound_nondecreasing"]),
        "response_accounting": bool(
            row["exact_external_axis_coverage"]
            and row["all_violators_accounted"]
        ),
        "work_counts": (
            row["masters_solved"] == row["exact_oracles_executed"]
            == row["retrospective_optimizer_labels_generated"]
            and row["cut_rounds"] <= int(base["maximum_cut_rounds"])
        ),
        "timing": (
            row["cold_setup_ms"] <= gate["maximum_cold_setup_ms"]
            and row["warm_step"]["wall_ms"] <= gate["maximum_warm_step_ms"]
            and row["initial_row_ms"] <= gate["maximum_initial_row_ms"]
            and all(
                iteration["master"]["solve_ms"] <= gate["maximum_master_ms"]
                and iteration["oracle"]["wall_ms"] <= gate["maximum_oracle_ms"]
                for iteration in iterations
            )
            and all(cut["wall_ms"] <= gate["maximum_cut_row_ms"] for cut in cut_rows)
        ),
        "memory": (
            row["maximum_gpu_pool_total_bytes"] <= gate["maximum_gpu_pool_bytes"]
            and row["minimum_gpu_free_bytes"] >= gate["minimum_physical_free_bytes"]
        ),
        "emission": (
            row["actual_emitted_policy_sha256"]
            == row["restricted_blueprint_policy_sha256"]
            and row["candidate_policies_emitted"] == 0
            and row["fresh_post_fold_strategy_labels_generated"] == 0
        ),
        "finite": _finite_tree(row),
    }
    return checks


def _checkpoint_payload(
    *,
    config_sha256: str,
    inventory_sha256: str,
    outcomes: list[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "h32_retained_convex_closure_census_v2_partial",
        "config_sha256": config_sha256,
        "inventory_sha256": inventory_sha256,
        "attempted_targets": len(outcomes),
        "outcomes": outcomes,
    }


def _write_checkpoint(payload: Mapping[str, Any], path: Path) -> str:
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(serialize_result(dict(payload)), encoding="utf-8")
    temporary.replace(path)
    return _sha256(path)


def run_h32_retained_convex_closure_census_v2(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
    checkpoint_path: Path = _CHECKPOINT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = parse_h32_retained_convex_closure_census_v2_config(
        json.loads(config_path.read_text(encoding="utf-8"))
    )
    base = parsed["base"]
    git = v1._strict_git_metadata()
    if git["dirty"]:
        raise RuntimeError("isolated closure census requires a clean Git state")
    cp, runtime = v1._validate_runtime(base)
    source_parent = load_artifact(
        v1._SOURCE,
        expected_sha256=base["expected_source_result_sha256"],
        require_passed=True,
    ).payload
    keystone = load_artifact(
        v1._KEYSTONE,
        expected_sha256=base["expected_keystone_result_sha256"],
        require_passed=True,
    ).payload
    config_sha256 = _sha256(config_path)
    outcomes: list[dict[str, Any]] = []
    checkpoint_hashes = []
    for spec in base["inventory"]:
        if time.perf_counter() - started >= float(base["maximum_total_seconds"]):
            raise RuntimeError(
                "isolated closure-census total resource cap reached before target"
            )
        target_started = time.perf_counter()
        try:
            target = v1._run_target(base, source_parent, spec, cp)
            outcome = {
                "inventory_index": spec["inventory_index"],
                "target_id": spec["target_id"],
                "status": "completed",
                "target": target,
            }
        except Exception as error:  # target isolation is the corrective contract
            gc.collect()
            release_cupy_memory_pool()
            cleanup_memory = _memory_snapshot(cp)
            outcome = {
                "inventory_index": spec["inventory_index"],
                "target_id": spec["target_id"],
                "status": "target_error_censored",
                "spec": dict(spec),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "allowed_known_error": (
                    type(error).__name__ == "ArithmeticError"
                    and str(error) == "behavioral master primal/dual verification failed"
                ),
                "target_seconds_before_error": time.perf_counter() - target_started,
                "post_cleanup_memory": cleanup_memory,
                "candidate_policies_emitted": 0,
                "fresh_post_fold_strategy_labels_generated": 0,
                "retrospective_optimizer_label_count": "unknown_fail_closed",
            }
        outcomes.append(outcome)
        checkpoint_hashes.append(
            _write_checkpoint(
                _checkpoint_payload(
                    config_sha256=config_sha256,
                    inventory_sha256=base["expected_inventory_sha256"],
                    outcomes=outcomes,
                ),
                checkpoint_path,
            )
        )
        progress = {
            "completed_target": len(outcomes),
            "total_targets": len(base["inventory"]),
            "target_id": outcome["target_id"],
            "status": outcome["status"],
        }
        if outcome["status"] == "completed":
            progress.update(
                {
                    "converged": outcome["target"]["converged"],
                    "rounds_to_closure": outcome["target"]["rounds_to_closure"],
                    "stop_reason": outcome["target"]["stop_reason"],
                    "target_seconds": outcome["target"]["total_seconds"],
                }
            )
        else:
            progress.update(
                {
                    "error_type": outcome["error_type"],
                    "error_message": outcome["error_message"],
                    "target_seconds": outcome["target_seconds_before_error"],
                }
            )
        print(json.dumps(progress, sort_keys=True), flush=True)

    total_seconds = time.perf_counter() - started
    completed = [outcome["target"] for outcome in outcomes if outcome["status"] == "completed"]
    errors = [outcome for outcome in outcomes if outcome["status"] != "completed"]
    completed_checks = [
        _completed_target_checks(row, base) for row in completed
    ]
    keystone_replay = (
        v1._keystone_replay_error(completed, keystone)
        if any(row["target_id"] == keystone["target"]["target_id"] for row in completed)
        else None
    )
    gate = parsed["gates"]
    attempted_ids = [outcome["target_id"] for outcome in outcomes]
    expected_ids = [row["target_id"] for row in base["inventory"]]
    failed_target = gate["expected_recomputed_failed_target"]
    partial_ids = expected_ids[: gate["expected_recomputed_printed_targets"]]
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "base_config_identity": (
            _sha256(_BASE_CONFIG) == parsed["expected_base_config_sha256"]
        )
        == gate["require_base_config_identity"],
        "inventory_identity": (
            v1.retained_inventory_sha256() == base["expected_inventory_sha256"]
        )
        == gate["require_inventory_identity"],
        "all_targets_attempted_in_order": (
            len(outcomes) == gate["expected_targets"] and attempted_ids == expected_ids
        )
        == gate["require_all_targets_attempted_in_order"],
        "checkpoint_after_every_outcome": (
            len(checkpoint_hashes) == len(outcomes)
            and all(checkpoint_hashes)
            and json.loads(checkpoint_path.read_text(encoding="utf-8"))[
                "attempted_targets"
            ]
            == len(outcomes)
        )
        == gate["require_checkpoint_after_every_outcome"],
        "known_errors_only": all(row["allowed_known_error"] for row in errors)
        == gate["require_known_errors_only"],
        "failed_target_censored": all(
            row["status"] == "target_error_censored"
            and row["candidate_policies_emitted"] == 0
            for row in errors
        )
        == gate["require_failed_target_censored"],
        "error_cleanup_memory": all(
            row["post_cleanup_memory"]["gpu_pool_total_bytes"]
            <= base["gates"]["maximum_gpu_pool_bytes"]
            and row["post_cleanup_memory"]["gpu_free_bytes"]
            >= base["gates"]["minimum_physical_free_bytes"]
            for row in errors
        ),
        "completed_target_validity": all(
            all(row.values()) for row in completed_checks
        )
        == gate["require_completed_target_validity"],
        "keystone_replay_when_completed": (
            keystone_replay is not None
            and keystone_replay["discrete_identity"]
            and keystone_replay["maximum_absolute_error"]
            <= base["gates"]["maximum_keystone_replay_error"]
        )
        == gate["require_keystone_replay_when_completed"],
        "post_fold_labels_zero": all(
            (
                outcome["target"]["fresh_post_fold_strategy_labels_generated"]
                if outcome["status"] == "completed"
                else outcome["fresh_post_fold_strategy_labels_generated"]
            )
            == 0
            for outcome in outcomes
        )
        == gate["require_post_fold_labels_zero"],
        "blueprint_emission": all(
            (
                outcome["target"]["candidate_policies_emitted"] == 0
                and outcome["target"]["actual_emitted_policy_sha256"]
                == outcome["target"]["restricted_blueprint_policy_sha256"]
                if outcome["status"] == "completed"
                else outcome["candidate_policies_emitted"] == 0
            )
            for outcome in outcomes
        )
        == gate["require_blueprint_emission"],
        "partial_label_disclosure": (
            attempted_ids[: len(partial_ids)] == partial_ids
            and failed_target in attempted_ids
            and "targets_1_to_5" in parsed["partial_label_disclosure"]
            and "target_6" in parsed["partial_label_disclosure"]
        )
        == gate["require_partial_label_disclosure"],
        "total_time": total_seconds <= float(base["maximum_total_seconds"]),
        "strategy_population_claim_null": True
        == gate["require_strategy_population_claim_null"],
        "finite": _finite_tree(outcomes) == gate["require_finite"],
    }
    gate_result = finalize_gates(checks)
    converged = [row for row in completed if row["converged"]]
    one_round = [
        row
        for row in converged
        if row["rounds_to_closure"] is not None
        and int(row["rounds_to_closure"]) <= 1
    ]
    stalls = [
        row
        for row in completed
        if not row["converged"]
    ]
    histogram = Counter(
        str(row["rounds_to_closure"])
        if row["converged"]
        else f"censored:{row['stop_reason']}"
        for row in completed
    )
    histogram.update(f"censored:error:{row['error_type']}" for row in errors)
    universal_full = len(converged) == len(outcomes) and not errors
    universal_one_round = len(one_round) == len(outcomes) and not errors
    result = {
        "schema_version": 1,
        "status": "h32_retained_convex_closure_census_v2_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": config_sha256,
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "base_config_sha256": _sha256(_BASE_CONFIG),
        "inventory_sha256": base["expected_inventory_sha256"],
        "partial_checkpoint_sha256": checkpoint_hashes[-1],
        "methodology": {
            "targets_attempted": len(outcomes),
            "targets_completed": len(completed),
            "target_errors_censored": len(errors),
            "retrospective_optimizer_labels_from_completed_targets": sum(
                row["retrospective_optimizer_labels_generated"] for row in completed
            ),
            "failed_target_optimizer_label_count": "unknown_fail_closed",
            "fresh_post_fold_strategy_labels": 0,
            "candidate_policies_emitted": 0,
        },
        "target_outcomes": outcomes,
        "target_rows": completed,
        "target_errors": errors,
        "completed_target_checks": completed_checks,
        "keystone_replay": keystone_replay,
        "aggregate": {
            "attempted_targets": len(outcomes),
            "completed_targets": len(completed),
            "converged_targets": len(converged),
            "one_round_closed_targets": len(one_round),
            "stalled_or_resource_censored_targets": len(stalls),
            "target_error_count": len(errors),
            "rounds_to_closure_histogram": dict(sorted(histogram.items())),
            "universal_full_closure": universal_full,
            "universal_one_round_closure": universal_one_round,
            "maximum_rounds_to_closure": max(
                (int(row["rounds_to_closure"]) for row in converged),
                default=None,
            ),
            "total_cut_rounds": sum(row["cut_rounds"] for row in completed),
            "total_new_response_rows": sum(
                row["total_cut_rows"] for row in completed
            ),
            "maximum_optimality_gap_completed": max(
                (row["optimality_gap"] for row in completed),
                default=None,
            ),
        },
        **gate_result,
        "decision": (
            "retained_corpus_supports_universal_one_round_global_closure_"
            "authorize_fresh_confirmation"
            if gate_result["passed"] and universal_one_round
            else "full_closure_teacher_succeeds_but_one_round_is_not_universal_"
            "retain_live_direction_fallback"
            if gate_result["passed"] and universal_full
            else "closure_census_is_censored_or_stalled_retain_live_direction_"
            "fallback"
            if gate_result["passed"]
            else "reject_target_isolated_closure_census_execution"
        ),
        "actual_emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            (
                "Targets 1-5 and target 6 are recomputed after the disclosed "
                "rejected invocation without adapting the roster or method."
            ),
            (
                "A known target-local master verification error is "
                "right-censored and never accepted as closure."
            ),
            (
                "All optimizer labels are retrospective on contexts whose "
                "strategy evidence was already open."
            ),
            "The fixed corpus is balanced but non-IID; counts are not deployment rates.",
            (
                "The post-fold panel remains strategy-label blind and every "
                "external policy remains the blueprint."
            ),
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, default=_CHECKPOINT)
    args = parser.parse_args()
    result = run_h32_retained_convex_closure_census_v2(
        args.config,
        args.output,
        args.checkpoint,
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "decision": result["decision"],
                "aggregate": result["aggregate"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
