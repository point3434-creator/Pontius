"""Full-closure timing diagnostic for the two fresh post-fold failures."""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Iterator, Mapping

from . import h32_retained_convex_closure_census as census
from .cupy_sparse_incidence import release_cupy_memory_pool
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_decision_aligned_live_shadow_trial import _manifest_target_specs
from .h32_post_fold_current_decision_setup import (
    build_post_fold_current_decision_setup,
)
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    serialize_result,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments/configs/h32-post-fold-failure-closure-diagnostic-v1.json"
)
_OUTPUT = (
    _ROOT / "experiments/results/h32-post-fold-failure-closure-diagnostic-v1.json"
)
_CHECKPOINT = (
    _ROOT
    / "experiments/results/h32-post-fold-failure-closure-diagnostic-v1.partial.json"
)
_BASE_CONFIG = (
    _ROOT / "experiments/configs/h32-retained-convex-closure-census-v1.json"
)
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_MANIFEST = _ROOT / "experiments/results/h32-post-fold-posterior-manifest-v1.json"
_FRESH_RESULT = (
    _ROOT / "experiments/results/h32-post-fold-closure-value-confirmation-v1.json"
)
_FRESH_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0274-post-fold-confirms-safe-value-but-not-universal-one-round-closure.md"
)
_BASE_IMPLEMENTATION = (
    _ROOT / "src/pontius/h32_retained_convex_closure_census.py"
)
_SETUP_IMPLEMENTATION = (
    _ROOT / "src/pontius/h32_post_fold_current_decision_setup.py"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_post_fold_failure_closure_diagnostic.py"

_PATHS = {
    "expected_base_config_sha256": _BASE_CONFIG,
    "expected_source_parent_sha256": _SOURCE,
    "expected_post_fold_manifest_sha256": _MANIFEST,
    "expected_fresh_result_sha256": _FRESH_RESULT,
    "expected_fresh_decision_sha256": _FRESH_DECISION,
    "expected_base_implementation_sha256": _BASE_IMPLEMENTATION,
    "expected_setup_implementation_sha256": _SETUP_IMPLEMENTATION,
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required post-fold diagnostic input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _failure_inventory(
    manifest: Mapping[str, Any],
    failure_ids: tuple[str, ...],
) -> tuple[dict[str, Any], ...]:
    by_id = {
        str(row["target_id"]): row for row in _manifest_target_specs(manifest)
    }
    if set(by_id).issuperset(failure_ids) is False:
        raise ValueError("post-fold diagnostic failure ID is absent from manifest")
    return tuple(
        {
            **by_id[target_id],
            "panel": "post_fold_failure",
            "setup_mode": "post_fold_current_decision",
            "acting_public_nodes": 1,
            "behavioral_information_sets": 32,
            "policy_variables": 64,
        }
        for target_id in failure_ids
    )


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "failure_target_ids",
        "target_selection_rule",
        "inventory",
        "inheritance_rule",
        "setup_rule",
        "target_isolation_rule",
        "checkpoint_rule",
        "reproduction_rule",
        "marginal_cost_rule",
        "maximum_campaign_seconds",
        "label_policy",
        "decision_rule",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("post-fold closure diagnostic fields differ from ADR-0275")
    for field_name, path in _PATHS.items():
        if config[field_name] != _sha256(path):
            raise ValueError(f"post-fold diagnostic provenance mismatch: {field_name}")
    base = census.parse_h32_retained_convex_closure_census_config(
        json.loads(_BASE_CONFIG.read_text(encoding="utf-8"))
    )
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    failure_ids = (
        "panel_1/blocker_heavy/checks_then_bet_seat1_then_fold_seat2",
        "panel_3/balanced/checks_then_bet_seat4_then_fold_seat5",
    )
    inventory = _failure_inventory(manifest, failure_ids)
    exact = {
        "evidence_stage": (
            "retrospective_preregistered_after_adr0274_before_any_additional_"
            "post_fold_optimizer_label"
        ),
        "seed": 20260822,
        "failure_target_ids": list(failure_ids),
        "target_selection_rule": (
            "exactly_the_two_adr0274_fresh_one_round_closure_failures_in_"
            "original_manifest_order_no_other_target"
        ),
        "inventory": [dict(row) for row in inventory],
        "inheritance_rule": (
            "byte_pinned_adr0267_full_closure_target_math_tolerances_round_and_"
            "resource_caps_with_only_post_fold_setup_and_two_target_roster"
        ),
        "setup_rule": (
            "scoped_post_fold_setup_replacement_restored_on_success_or_failure"
        ),
        "target_isolation_rule": (
            "catch_record_checkpoint_cleanup_and_continue_any_target_exception_"
            "with_every_exception_failing_the_process_gate"
        ),
        "checkpoint_rule": (
            "atomically_replace_complete_partial_json_after_every_target_outcome"
        ),
        "reproduction_rule": (
            "reproduce_fresh_first_and_post_cut_master_oracle_cut_and_violator_"
            "rows_within_2e_11_before_interpreting_later_rounds"
        ),
        "marginal_cost_rule": (
            "after_failed_round_one_charge_its_new_cut_extraction_then_next_"
            "master_and_endpoint_oracle_no_retreat_or_live_admission_claim"
        ),
        "maximum_campaign_seconds": 600.0,
        "label_policy": (
            "retrospective_optimizer_labels_on_two_opened_failures_only_zero_"
            "new_retreat_labels_zero_candidate_emission"
        ),
        "decision_rule": (
            "report_exact_closure_depth_and_marginal_cost_if_both_close_at_"
            "round_two_authorize_only_a_separate_deadline_admission_study"
        ),
    }
    for field_name, expected_value in exact.items():
        if config[field_name] != expected_value:
            raise ValueError(
                f"post-fold diagnostic field differs from ADR-0275: {field_name}"
            )
    gates = {
        "expected_targets": 2,
        "expected_failure_target_ids": list(failure_ids),
        "expected_acting_public_nodes": 1,
        "expected_behavioral_information_sets": 32,
        "expected_policy_variables": 64,
        "maximum_reproduction_error": 2e-11,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_fresh_negative_decision": True,
        "require_inventory_identity": True,
        "require_setup_adapter_active": True,
        "require_setup_adapter_restored": True,
        "require_all_targets_attempted": True,
        "require_checkpoint_after_every_outcome": True,
        "require_zero_target_errors": True,
        "require_reproduction": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_warm_start_identity": True,
        "require_path_single_visit": True,
        "require_lower_bound_monotonicity": True,
        "require_exact_external_axis_coverage": True,
        "require_all_violators_accounted": True,
        "require_blueprint_emission": True,
        "require_retrospective_label_disclosure": True,
        "require_strategy_population_claim_null": True,
        "require_finite": True,
    }
    if config["gates"] != gates:
        raise ValueError("post-fold diagnostic gates differ from ADR-0275")
    return {
        **base,
        **{field_name: config[field_name] for field_name in _PATHS},
        **exact,
        "inventory": inventory,
        "gates": gates,
        "base_gates": base["gates"],
    }


@contextmanager
def post_fold_census_setup_adapter() -> Iterator[None]:
    """Route the byte-pinned census target through the post-fold setup."""

    original = census._setup_target
    if original.__module__ != census.__name__:
        raise RuntimeError("closure-census setup was already replaced")

    def setup(parsed, source_parent, spec):
        return build_post_fold_current_decision_setup(parsed, source_parent, spec)

    census._setup_target = setup
    try:
        yield
    finally:
        census._setup_target = original


def _write_checkpoint(payload: Mapping[str, Any], path: Path) -> str:
    rendered = serialize_result(payload)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(path)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _reproduction_row(
    row: Mapping[str, Any],
    fresh: Mapping[str, Any],
) -> dict[str, Any]:
    first = row["iterations"][0]
    post_cut = row["iterations"][1]
    errors = {
        "source_nash_conv": abs(
            float(row["source_nash_conv"]) - float(fresh["source_nash_conv"])
        ),
        "first_master_lower_bound": abs(
            float(first["master"]["lower_bound"])
            - float(fresh["masters"][0]["lower_bound"])
        ),
        "first_oracle_objective": abs(
            float(first["oracle"]["objective"])
            - float(fresh["first_oracle"]["nash_conv"])
        ),
        "post_cut_master_lower_bound": abs(
            float(post_cut["master"]["lower_bound"])
            - float(fresh["masters"][-1]["lower_bound"])
        ),
        "post_cut_oracle_objective": abs(
            float(post_cut["oracle"]["objective"])
            - float(fresh["endpoint_certificate"]["exact_summary"]["nash_conv"])
        ),
        "post_cut_gap": abs(
            float(post_cut["optimality_gap"])
            - float(fresh["endpoint_certificate"]["optimality_gap"])
        ),
    }
    first_cut_players = [item["target_player"] for item in first["cut_rows"]]
    fresh_cut_players = [item["target_player"] for item in fresh["cut_rows"]]
    post_cut_violators = list(post_cut["oracle"]["epigraph_violating_players"])
    fresh_post_cut_violators = list(
        fresh["endpoint_certificate"]["exact_summary"][
            "epigraph_violating_players"
        ]
    )
    return {
        "target_id": row["target_id"],
        "maximum_absolute_error": max(errors.values()),
        "absolute_errors": errors,
        "first_cut_players": first_cut_players,
        "fresh_first_cut_players": fresh_cut_players,
        "post_cut_violating_players": post_cut_violators,
        "fresh_post_cut_violating_players": fresh_post_cut_violators,
        "discrete_identity": (
            first_cut_players == fresh_cut_players
            and post_cut_violators == fresh_post_cut_violators
        ),
    }


def _marginal_round_rows(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    rounds = []
    for index in range(1, len(row["iterations"]) - 1):
        source = row["iterations"][index]
        endpoint = row["iterations"][index + 1]
        rounds.append(
            {
                "round_completed": index + 1,
                "cut_extraction_ms": float(source["cut_extraction_ms"]),
                "new_cut_players": [
                    cut["target_player"] for cut in source["cut_rows"]
                ],
                "next_master_ms": float(endpoint["master"]["solve_ms"]),
                "next_endpoint_oracle_ms": float(endpoint["oracle"]["wall_ms"]),
                "incremental_ms": math.fsum(
                    (
                        float(source["cut_extraction_ms"]),
                        float(endpoint["master"]["solve_ms"]),
                        float(endpoint["oracle"]["wall_ms"]),
                    )
                ),
                "endpoint_globally_closed": bool(
                    row["converged"] and index + 1 == len(row["iterations"]) - 1
                ),
            }
        )
    return rounds


def run_h32_post_fold_failure_closure_diagnostic(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
    checkpoint_path: Path = _CHECKPOINT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    if git["dirty"]:
        raise RuntimeError("post-fold closure diagnostic requires a clean Git state")
    cp, runtime = _validate_runtime(parsed)
    source = load_artifact(
        _SOURCE,
        expected_sha256=parsed["expected_source_parent_sha256"],
        require_passed=True,
    ).payload
    manifest = load_artifact(
        _MANIFEST,
        expected_sha256=parsed["expected_post_fold_manifest_sha256"],
        require_passed=True,
    ).payload
    fresh_result = load_artifact(
        _FRESH_RESULT,
        expected_sha256=parsed["expected_fresh_result_sha256"],
        require_passed=True,
    ).payload
    fresh_by_id = {
        str(row["target_id"]): row for row in fresh_result["target_rows"]
    }

    outcomes = []
    checkpoint_hashes = []
    adapter_active = False
    with post_fold_census_setup_adapter():
        adapter_active = census._setup_target.__module__ == __name__
        for spec in parsed["inventory"]:
            target_started = time.perf_counter()
            try:
                row = census._run_target(parsed, source, spec, cp)
                outcome = {"status": "completed", "target_row": row}
            except Exception as error:
                outcome = {
                    "status": "target_error_censored",
                    "target_id": spec["target_id"],
                    "exception_type": type(error).__name__,
                    "exception_message": str(error),
                    "elapsed_seconds": time.perf_counter() - target_started,
                }
            outcomes.append(outcome)
            gc.collect()
            release_cupy_memory_pool()
            checkpoint_hashes.append(
                _write_checkpoint(
                    {
                        "schema_version": 1,
                        "status": "h32_post_fold_failure_closure_partial",
                        "config_sha256": _sha256(config_path),
                        "attempted_targets": len(outcomes),
                        "outcomes": outcomes,
                    },
                    checkpoint_path,
                )
            )
    adapter_restored = census._setup_target.__module__ == census.__name__

    target_rows = [
        outcome["target_row"]
        for outcome in outcomes
        if outcome["status"] == "completed"
    ]
    target_errors = [
        outcome for outcome in outcomes if outcome["status"] != "completed"
    ]
    reproduction_rows = [
        _reproduction_row(row, fresh_by_id[row["target_id"]]) for row in target_rows
    ]
    for row in target_rows:
        row["marginal_rounds_after_failed_round_one"] = _marginal_round_rows(row)
    total_seconds = time.perf_counter() - started
    base_gate = parsed["base_gates"]
    gate = parsed["gates"]
    all_iterations = [
        iteration for row in target_rows for iteration in row["iterations"]
    ]
    all_cut_rows = [
        cut for iteration in all_iterations for cut in iteration["cut_rows"]
    ]
    attempted_ids = [
        outcome.get("target_id", outcome.get("target_row", {}).get("target_id"))
        for outcome in outcomes
    ]
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": all(
            artifact_passed(parent) for parent in (source, manifest, fresh_result)
        )
        == gate["require_parents_passed"],
        "fresh_negative_decision": (
            fresh_result["decision"]
            == "accept_execution_retain_direction_fallback_on_fresh_closure_failure"
        )
        == gate["require_fresh_negative_decision"],
        "inventory_identity": [row["target_id"] for row in parsed["inventory"]]
        == gate["expected_failure_target_ids"]
        == [
            row["target_id"]
            for row in manifest["target_rows"]
            if row["target_id"] in gate["expected_failure_target_ids"]
        ]
        and gate["require_inventory_identity"],
        "setup_adapter_active": adapter_active
        == gate["require_setup_adapter_active"],
        "setup_adapter_restored": adapter_restored
        == gate["require_setup_adapter_restored"],
        "all_targets_attempted": attempted_ids == gate["expected_failure_target_ids"]
        == [row["target_id"] for row in parsed["inventory"]]
        and len(outcomes) == gate["expected_targets"]
        and gate["require_all_targets_attempted"],
        "checkpoint_after_every_outcome": (
            len(checkpoint_hashes) == len(outcomes)
            and json.loads(checkpoint_path.read_text(encoding="utf-8"))[
                "attempted_targets"
            ]
            == len(outcomes)
        )
        == gate["require_checkpoint_after_every_outcome"],
        "zero_target_errors": (not target_errors)
        == gate["require_zero_target_errors"],
        "target_count": len(target_rows) == gate["expected_targets"],
        "reproduction": (
            len(reproduction_rows) == gate["expected_targets"]
            and all(row["discrete_identity"] for row in reproduction_rows)
            and max(
                (row["maximum_absolute_error"] for row in reproduction_rows),
                default=math.inf,
            )
            <= gate["maximum_reproduction_error"]
        )
        == gate["require_reproduction"],
        "source_checkpoint_identity": all(
            row["source_checkpoint_identity"] for row in target_rows
        )
        == gate["require_source_checkpoint_identity"],
        "target_identity": all(row["target_identity"] for row in target_rows)
        == gate["require_target_identity"],
        "blueprint_identity": all(row["blueprint_identity"] for row in target_rows)
        == gate["require_blueprint_identity"],
        "warm_start_identity": all(
            row["warm_start_distance"]["maximum_probability_error"]
            <= base_gate["maximum_warm_start_probability_error"]
            and row["warm_start_distance"]["mean_total_variation"]
            <= base_gate["maximum_warm_start_mean_total_variation"]
            for row in target_rows
        )
        == gate["require_warm_start_identity"],
        "path_single_visit": all(row["path_single_visit"] for row in target_rows)
        == gate["require_path_single_visit"],
        "axis_shape": all(
            row["acting_public_nodes_measured"]
            == gate["expected_acting_public_nodes"]
            and row["behavioral_information_sets_measured"]
            == gate["expected_behavioral_information_sets"]
            and row["policy_variables_measured"] == gate["expected_policy_variables"]
            for row in target_rows
        ),
        "initial_pass_counts": all(
            row["initial_profile_passes"]
            == base_gate["expected_initial_profile_passes"]
            and row["initial_response_passes"]
            == base_gate["expected_initial_response_passes"]
            and row["initial_gain_rows"] == base_gate["expected_initial_gain_rows"]
            for row in target_rows
        ),
        "row_identity": all(
            row["maximum_initial_row_error"] <= base_gate["maximum_initial_row_error"]
            and row["maximum_cut_row_error"] <= base_gate["maximum_cut_row_error"]
            and row["maximum_profile_equivalence_error"]
            <= base_gate["maximum_profile_equivalence_error"]
            for row in target_rows
        ),
        "master_numerics": all(
            row["maximum_master_primal_error"]
            <= base_gate["maximum_master_primal_error"]
            and row["maximum_master_dual_error"]
            <= base_gate["maximum_master_dual_error"]
            for row in target_rows
        ),
        "projection": all(
            row["maximum_projection_error"] <= base_gate["maximum_projection_error"]
            for row in target_rows
        ),
        "raw_guard": all(
            abs(row["raw_guard"] - 3e-9) <= base_gate["maximum_raw_guard_error"]
            for row in target_rows
        ),
        "lower_bound_monotonicity": all(
            row["lower_bound_nondecreasing"] for row in target_rows
        )
        == gate["require_lower_bound_monotonicity"],
        "external_axis_coverage": all(
            row["exact_external_axis_coverage"] for row in target_rows
        )
        == gate["require_exact_external_axis_coverage"],
        "all_violators_accounted": all(
            row["all_violators_accounted"] for row in target_rows
        )
        == gate["require_all_violators_accounted"],
        "resource_caps": (
            all(
                row["cold_setup_ms"] <= base_gate["maximum_cold_setup_ms"]
                and row["warm_step"]["wall_ms"] <= base_gate["maximum_warm_step_ms"]
                and row["initial_row_ms"] <= base_gate["maximum_initial_row_ms"]
                and row["maximum_gpu_pool_total_bytes"]
                <= base_gate["maximum_gpu_pool_bytes"]
                and row["minimum_gpu_free_bytes"]
                >= base_gate["minimum_physical_free_bytes"]
                and row["total_seconds"]
                <= float(parsed["maximum_target_seconds"])
                + base_gate["maximum_oracle_ms"] / 1000.0
                for row in target_rows
            )
            and all(
                iteration["master"]["solve_ms"] <= base_gate["maximum_master_ms"]
                and iteration["oracle"]["wall_ms"] <= base_gate["maximum_oracle_ms"]
                for iteration in all_iterations
            )
            and all(
                cut["wall_ms"] <= base_gate["maximum_cut_row_ms"]
                for cut in all_cut_rows
            )
            and total_seconds <= float(parsed["maximum_campaign_seconds"])
        ),
        "blueprint_emission": all(
            row["actual_emitted_policy_sha256"]
            == row["restricted_blueprint_policy_sha256"]
            and row["candidate_policies_emitted"] == 0
            for row in target_rows
        )
        == gate["require_blueprint_emission"],
        "retrospective_label_disclosure": all(
            row["retrospective_optimizer_labels_generated"]
            == row["exact_oracles_executed"]
            and row["fresh_post_fold_strategy_labels_generated"] == 0
            for row in target_rows
        )
        == gate["require_retrospective_label_disclosure"],
        "strategy_population_claim_null": True
        == gate["require_strategy_population_claim_null"],
        "finite": census._finite_tree(outcomes)
        == gate["require_finite"],
    }
    gate_result = finalize_gates(checks)
    converged = [row for row in target_rows if row["converged"]]
    both_round_two = bool(
        len(converged) == gate["expected_targets"]
        and all(row["rounds_to_closure"] == 2 for row in converged)
    )
    result = {
        "schema_version": 1,
        "status": "h32_post_fold_failure_closure_diagnostic_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "checkpoint_sha256": checkpoint_hashes[-1] if checkpoint_hashes else None,
        "methodology": {
            "attempted_targets": len(outcomes),
            "completed_targets": len(target_rows),
            "target_errors": len(target_errors),
            "warm_steps": len(target_rows),
            "retrospective_optimizer_labels": sum(
                row["retrospective_optimizer_labels_generated"]
                for row in target_rows
            ),
            "new_retreat_labels": 0,
            "candidate_policies_emitted": 0,
        },
        "outcomes": outcomes,
        "target_rows": target_rows,
        "target_errors": target_errors,
        "reproduction_rows": reproduction_rows,
        "aggregate": {
            "converged_targets": len(converged),
            "rounds_to_closure_histogram": dict(
                sorted(
                    Counter(
                        str(row["rounds_to_closure"])
                        if row["rounds_to_closure"] is not None
                        else f"censored:{row['stop_reason']}"
                        for row in target_rows
                    ).items()
                )
            ),
            "both_close_at_round_two": both_round_two,
            "maximum_marginal_second_round_ms": max(
                (
                    row["marginal_rounds_after_failed_round_one"][0][
                        "incremental_ms"
                    ]
                    for row in target_rows
                    if row["marginal_rounds_after_failed_round_one"]
                ),
                default=None,
            ),
            "maximum_rounds_to_closure": max(
                (row["rounds_to_closure"] for row in converged),
                default=None,
            ),
            "maximum_gpu_pool_total_bytes": max(
                (row["maximum_gpu_pool_total_bytes"] for row in target_rows),
                default=0,
            ),
            "minimum_gpu_free_bytes": min(
                (row["minimum_gpu_free_bytes"] for row in target_rows),
                default=0,
            ),
        },
        **gate_result,
        "decision": (
            "both_fresh_failures_close_at_round_two_authorize_separate_"
            "deadline_admission_study"
            if gate_result["passed"] and both_round_two
            else "fresh_failures_require_deeper_or_censored_closure_keep_"
            "global_solver_off_clock"
            if gate_result["passed"]
            else "reject_post_fold_failure_closure_diagnostic_execution"
        ),
        "actual_emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            (
                "The two targets were selected because they failed fresh "
                "one-round closure; this is retrospective conditional evidence."
            ),
            (
                "Marginal closure cost excludes construction of a new retreat "
                "and grants no live deadline admission."
            ),
            (
                "No candidate or new retreat is evaluated or emitted and no "
                "direction-obsolescence or poker-strength claim is made."
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
    result = run_h32_post_fold_failure_closure_diagnostic(
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
