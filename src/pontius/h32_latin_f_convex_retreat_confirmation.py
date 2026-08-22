"""Untouched Latin-F confirmation of the h32 one-seat convex retreat."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping

import numpy as np

from .cupy_sparse_incidence import release_cupy_memory_pool
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_fresh_convex_retreat_replication import (
    _certify_target_candidate,
    _construct_target_candidate,
    _finite_tree,
    _parse_config as _parse_latin_e_config,
    fresh_replication_promotion,
)
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    serialize_result,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-latin-f-convex-retreat-confirmation-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-latin-f-convex-retreat-confirmation-v1.json"
_BASE_CONFIG = (
    _ROOT / "experiments/configs/h32-fresh-convex-retreat-replication-v2.json"
)
_BASE_RESULT = (
    _ROOT / "experiments/results/h32-fresh-convex-retreat-replication-v2.json"
)
_BASE_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0258-convex-half-retreat-delivers-material-value-on-all-six-latin-e-targets.md"
)
_CORE_IMPLEMENTATION = (
    _ROOT / "src/pontius/h32_fresh_convex_retreat_replication.py"
)
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_MANIFEST = (
    _ROOT / "experiments/results/h32-convex-replication-posterior-manifest-v1.json"
)
_KNOWN_RESULT = _ROOT / "experiments/results/h32-one-seat-retreat-quality-v2.json"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_latin_f_convex_retreat_confirmation.py"

_PATHS = {
    "expected_base_config_sha256": _BASE_CONFIG,
    "expected_latin_e_result_sha256": _BASE_RESULT,
    "expected_latin_e_decision_sha256": _BASE_DECISION,
    "expected_core_implementation_sha256": _CORE_IMPLEMENTATION,
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required Latin-F confirmation input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def latin_f_confirmation_assessment(
    target_rows: list[Mapping[str, Any]],
    *,
    minimum_material_targets: int,
    minimum_material_exact_value: float,
) -> dict[str, Any]:
    """Apply the unchanged breadth threshold as confirmation rather than promotion."""

    assessed = fresh_replication_promotion(
        target_rows,
        minimum_material_targets=minimum_material_targets,
        minimum_material_exact_value=minimum_material_exact_value,
    )
    confirms = bool(assessed.pop("authorizes_latin_f_confirmation"))
    return {
        **assessed,
        "confirms_latin_e_breadth": confirms,
    }


def latin_f_confirmation_decision(*, process_passed: bool, confirms: bool) -> str:
    if not process_passed:
        return "reject_latin_f_confirmation_execution"
    if confirms:
        return "accept_latin_ef_breadth_and_authorize_live_shadow_preregistration"
    return "retain_latin_e_evidence_and_reject_live_shadow_preregistration"


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "target_selection_rule",
        "target_specs",
        "confirmation_rule",
        "success_decision",
        "failure_decision",
        "strategy_label_policy",
        "claims_policy",
        "confirmation_gates",
    }
    if set(config) != expected:
        raise ValueError("Latin-F confirmation config fields differ from ADR-0259")
    for field_name, path in _PATHS.items():
        if config[field_name] != _sha256(path):
            raise ValueError(f"Latin-F confirmation provenance mismatch: {field_name}")

    base = _parse_latin_e_config(
        json.loads(_BASE_CONFIG.read_text(encoding="utf-8"))
    )
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    latin_f = [row for row in manifest["target_rows"] if row["round"] == "latin_f"]
    source_map = {
        "panel_1/balanced": (["5c", "8c", "8d", "Jc", "As"], "balanced"),
        "panel_1/blocker_heavy": (
            ["5c", "8c", "8d", "Jc", "As"],
            "blocker_heavy",
        ),
        "panel_2/blocker_heavy": (
            ["2c", "3s", "5d", "Js", "Qc"],
            "blocker_heavy",
        ),
        "panel_2/balanced": (["2c", "3s", "5d", "Js", "Qc"], "balanced"),
        "panel_3/balanced": (["4h", "7h", "9s", "Jd", "Kc"], "balanced"),
        "panel_3/blocker_heavy": (
            ["4h", "7h", "9s", "Jd", "Kc"],
            "blocker_heavy",
        ),
    }
    frozen_specs = []
    for row in latin_f:
        board, family = source_map[row["source"]]
        frozen_specs.append(
            {
                "target_id": row["target_id"],
                "source": row["source"],
                "observed_bettor": row["observed_bettor"],
                "acting_player": row["acting_player"],
                "round": row["round"],
                "source_belief_sha256": row["source_belief_sha256"],
                "target_belief_sha256": row["target_belief_sha256"],
                "target_descriptor_sha256": row["target_descriptor_sha256"],
                "board": board,
                "range_family": family,
            }
        )
    exact = {
        "evidence_stage": "preregistered_after_adr0258_before_any_latin_f_warm_step_candidate_or_strategy_label",
        "seed": 20260822,
        "target_selection_rule": "all_six_untouched_latin_f_targets_in_manifest_order_zero_tv_opportunity_or_latin_e_value_selection",
        "target_specs": frozen_specs,
        "confirmation_rule": "confirm_only_if_at_least_four_material_targets_above_0_001_both_range_families_and_all_schedules_fit",
        "success_decision": "accept_latin_ef_breadth_and_authorize_live_shadow_preregistration",
        "failure_decision": "retain_latin_e_evidence_and_reject_live_shadow_preregistration",
        "strategy_label_policy": "six_fixed_first_evaluation_latin_f_retreat_labels_campaign_barrier_no_cross_target_adaptation",
        "claims_policy": "fresh_latin_f_confirmation_only_no_fallback_population_global_optimality_or_deployment_claim",
    }
    for field_name, expected_value in exact.items():
        if config[field_name] != expected_value:
            raise ValueError(f"Latin-F confirmation field differs from ADR-0259: {field_name}")
    confirmation_gates = {
        "expected_targets": 6,
        "expected_sources": 6,
        "expected_bettors": 6,
        "expected_acting_players": 6,
        "expected_candidates_frozen_before_labels": 6,
        "expected_exact_oracles": 12,
        "expected_strategy_labels": 6,
        "require_latin_e_parent_passed": True,
        "require_latin_e_promotion_passed": True,
        "require_latin_f_only": True,
        "require_disjoint_from_latin_e": True,
        "require_first_final_label_evaluation": True,
        "require_campaign_barrier_before_labels": True,
        "require_no_cross_target_adaptation": True,
        "require_blueprint_external_emission": True,
        "require_no_global_optimality_claim": True,
        "require_no_population_claim": True,
        "require_finite": True,
    }
    if config["confirmation_gates"] != confirmation_gates:
        raise ValueError("Latin-F confirmation gates differ from ADR-0259")
    return {
        **base,
        **{field_name: config[field_name] for field_name in _PATHS},
        "evidence_stage": config["evidence_stage"],
        "prior_label_incident": "none_latin_f_final_labels_unopened",
        "target_selection_rule": config["target_selection_rule"],
        "target_specs": tuple(dict(row) for row in config["target_specs"]),
        "scope": "six_untouched_latin_f_targets_one_per_source_bettor_and_acting_player_one_seat_shadow_confirmation",
        "strategy_label_policy": config["strategy_label_policy"],
        "confirmation_rule": config["confirmation_rule"],
        "success_decision": config["success_decision"],
        "failure_decision": config["failure_decision"],
        "claims_policy": config["claims_policy"],
        "confirmation_gates": confirmation_gates,
    }


def run_h32_latin_f_convex_retreat_confirmation(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    source = load_artifact(
        _SOURCE,
        expected_sha256=parsed["expected_source_result_sha256"],
        require_passed=True,
    ).payload
    manifest = load_artifact(
        _MANIFEST,
        expected_sha256=parsed["expected_manifest_result_sha256"],
        require_passed=True,
    ).payload
    known = load_artifact(
        _KNOWN_RESULT,
        expected_sha256=parsed["expected_known_result_sha256"],
        require_passed=True,
    ).payload
    latin_e = load_artifact(
        _BASE_RESULT,
        expected_sha256=parsed["expected_latin_e_result_sha256"],
        require_passed=True,
    ).payload

    campaign_events = ["inputs_pinned"]
    candidate_bundles = []
    for spec in parsed["target_specs"]:
        candidate_bundles.append(
            _construct_target_candidate(parsed, source, spec, cp)
        )
        gc.collect()
        release_cupy_memory_pool()
    prelabel_snapshots = [bundle["barrier"].snapshot() for bundle in candidate_bundles]
    candidates_frozen_before_labels = sum(
        row["phase"] == "candidate_frozen" for row in prelabel_snapshots
    )
    if candidates_frozen_before_labels != len(parsed["target_specs"]):
        raise RuntimeError("Latin-F campaign barrier did not freeze every target")
    if any(
        bundle["construction_row"]["new_strategy_quality_labels_generated"] != 0
        for bundle in candidate_bundles
    ):
        raise RuntimeError("Latin-F final label opened before campaign barrier")
    campaign_events.append("all_candidates_frozen")
    target_rows = []
    for bundle in candidate_bundles:
        target_rows.append(_certify_target_candidate(parsed, source, bundle, cp))
        gc.collect()
        release_cupy_memory_pool()
    campaign_events.append("all_retreat_certificates_complete")

    confirmation = latin_f_confirmation_assessment(
        target_rows,
        minimum_material_targets=int(parsed["minimum_material_targets"]),
        minimum_material_exact_value=float(parsed["minimum_material_exact_value"]),
    )
    total_seconds = time.perf_counter() - started
    gate = parsed["gates"]
    confirmation_gate = parsed["confirmation_gates"]
    fixed_target_ids = [row["target_id"] for row in parsed["target_specs"]]
    latin_e_ids = {row["target_id"] for row in latin_e["target_rows"]}
    global_optimality_claim = None
    population_claim = None
    cross_target_adaptation = False
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": all(
            artifact_passed(row) for row in (source, manifest, known, latin_e)
        )
        == gate["require_parents_passed"],
        "latin_e_parent_passed": artifact_passed(latin_e)
        == confirmation_gate["require_latin_e_parent_passed"],
        "latin_e_promotion_passed": bool(
            latin_e["promotion"]["authorizes_latin_f_confirmation"]
        )
        == confirmation_gate["require_latin_e_promotion_passed"],
        "target_count": len(target_rows) == confirmation_gate["expected_targets"],
        "source_count": len({row["source"] for row in target_rows})
        == confirmation_gate["expected_sources"],
        "bettor_count": len({row["observed_bettor"] for row in target_rows})
        == confirmation_gate["expected_bettors"],
        "acting_player_count": len({row["acting_player"] for row in target_rows})
        == confirmation_gate["expected_acting_players"],
        "latin_f_only": all(row["round"] == "latin_f" for row in target_rows)
        == confirmation_gate["require_latin_f_only"],
        "disjoint_from_latin_e": all(
            row["target_id"] not in latin_e_ids for row in target_rows
        )
        == confirmation_gate["require_disjoint_from_latin_e"],
        "first_final_label_evaluation": all(
            row["new_strategy_quality_labels_generated"] == 1
            for row in target_rows
        )
        == confirmation_gate["require_first_final_label_evaluation"],
        "target_identity": all(
            row["source_checkpoint_identity"] and row["target_identity"]
            for row in target_rows
        )
        == gate["require_target_identity"],
        "blueprint_identity": all(row["blueprint_identity"] for row in target_rows)
        == gate["require_blueprint_identity"],
        "warm_start_identity": all(
            row["warm_start_distance"]["maximum_probability_error"]
            <= gate["maximum_warm_start_probability_error"]
            and row["warm_start_distance"]["mean_total_variation"]
            <= gate["maximum_warm_start_mean_total_variation"]
            for row in target_rows
        )
        == gate["require_warm_start_identity"],
        "path_single_visit": all(row["path_single_visit"] for row in target_rows)
        == gate["require_path_single_visit"],
        "axis_counts": all(
            row["behavioral_information_sets"]
            == gate["expected_behavioral_information_sets"]
            and row["policy_variables"] == gate["expected_policy_variables"]
            and row["epigraph_variables"] == gate["expected_epigraph_variables"]
            for row in target_rows
        ),
        "initial_pass_counts": all(
            row["initial_profile_passes"]
            == gate["expected_initial_profile_passes_per_target"]
            and row["initial_response_passes"]
            == gate["expected_initial_response_passes_per_target"]
            and row["initial_gain_rows"] == gate["expected_initial_gain_rows_per_target"]
            for row in target_rows
        ),
        "row_identity": all(
            row["maximum_initial_row_error"] <= gate["maximum_initial_row_error"]
            and row["maximum_cut_row_error"] <= gate["maximum_cut_row_error"]
            and row["maximum_resident_row_identity_error"]
            <= gate["maximum_resident_row_identity_error"]
            and row["maximum_resident_epigraph_residual"]
            <= gate["maximum_resident_epigraph_residual"]
            and row["maximum_profile_equivalence_error"]
            <= gate["maximum_profile_equivalence_error"]
            for row in target_rows
        ),
        "master_numerics": all(
            row["maximum_master_primal_error"] <= gate["maximum_master_primal_error"]
            and row["maximum_master_dual_error"] <= gate["maximum_master_dual_error"]
            for row in target_rows
        ),
        "projection": all(
            max(
                row["first_candidate_projection_error"],
                row["second_candidate_projection_error"],
            )
            <= gate["maximum_projection_error"]
            for row in target_rows
        ),
        "raw_guard": all(
            abs(row["raw_guard"] - 3e-9) <= gate["maximum_raw_guard_error"]
            for row in target_rows
        ),
        "cold_setup_time": max(row["cold_setup_ms"] for row in target_rows)
        <= gate["maximum_cold_setup_ms"],
        "certificate_reconstruction_time": max(
            row["certificate_reconstruction"]["wall_ms"] for row in target_rows
        )
        <= gate["maximum_cold_setup_ms"],
        "warm_step_time": max(row["warm_step"]["wall_ms"] for row in target_rows)
        <= gate["maximum_warm_step_ms"],
        "initial_row_time": max(row["initial_row_ms"] for row in target_rows)
        <= gate["maximum_initial_row_ms"],
        "master_time": max(
            master["solve_ms"] for row in target_rows for master in row["masters"]
        )
        <= gate["maximum_master_ms"],
        "oracle_time": max(
            max(
                row["first_oracle"]["wall_ms"],
                row["retreat"]["exact_certificate"]["wall_ms"],
            )
            for row in target_rows
        )
        <= gate["maximum_oracle_ms"],
        "cut_extraction_time": max(row["cut_extraction_ms"] for row in target_rows)
        <= gate["maximum_cut_extraction_ms"],
        "gpu_pool": max(row["maximum_gpu_pool_total_bytes"] for row in target_rows)
        <= gate["maximum_gpu_pool_bytes"],
        "physical_free": min(row["minimum_gpu_free_bytes"] for row in target_rows)
        >= gate["minimum_physical_free_bytes"],
        "external_axis_coverage": all(
            row["exact_external_axis_coverage"] for row in target_rows
        )
        == gate["require_exact_external_axis_coverage"],
        "all_violators_accounted": all(
            row["all_first_oracle_violators_accounted"] for row in target_rows
        )
        == gate["require_all_first_oracle_violators_accounted"],
        "all_new_violators_cut": all(
            row["all_new_first_oracle_violators_cut"] for row in target_rows
        )
        == gate["require_all_new_first_oracle_violators_cut"],
        "maximum_one_cut_round": all(row["cut_rounds"] <= 1 for row in target_rows)
        == gate["require_maximum_one_cut_round"],
        "campaign_barrier_before_labels": (
            candidates_frozen_before_labels
            == confirmation_gate["expected_candidates_frozen_before_labels"]
            and campaign_events[:2] == ["inputs_pinned", "all_candidates_frozen"]
            and all(
                row["phase"] == "candidate_frozen"
                and row["events"] == ["inputs_pinned", "candidate_frozen"]
                for row in prelabel_snapshots
            )
        )
        == confirmation_gate["require_campaign_barrier_before_labels"],
        "certificate_reconstruction_identity": all(
            all(row["certificate_reconstruction"]["checks"].values())
            for row in target_rows
        )
        == gate["require_certificate_reconstruction_identity"],
        "retreat_certificates_complete": all(
            row["retreat"]["independently_certified"]
            and row["exact_oracles_executed"] == gate["expected_exact_oracles_per_target"]
            for row in target_rows
        )
        == gate["require_every_retreat_certificate_complete"],
        "outcome_neutral_abstention": all(
            row["retreat"]["shadow_accepted"]
            == row["retreat"]["acceptance_predicate_passed"]
            and (
                row["retreat"]["shadow_accepted"]
                or row["actual_emitted_policy_sha256"]
                == row["restricted_blueprint_policy_sha256"]
            )
            for row in target_rows
        )
        == gate["require_outcome_neutral_abstention"],
        "no_cross_target_adaptation": (
            [row["target_id"] for row in target_rows] == fixed_target_ids
            and not cross_target_adaptation
        )
        == confirmation_gate["require_no_cross_target_adaptation"],
        "blueprint_external_emission": all(
            row["actual_emitted_policy_sha256"]
            == row["restricted_blueprint_policy_sha256"]
            and row["candidate_policies_emitted"] == 0
            for row in target_rows
        )
        == confirmation_gate["require_blueprint_external_emission"],
        "oracle_count": sum(row["exact_oracles_executed"] for row in target_rows)
        == confirmation_gate["expected_exact_oracles"],
        "strategy_label_count": sum(
            row["new_strategy_quality_labels_generated"] for row in target_rows
        )
        == confirmation_gate["expected_strategy_labels"],
        "no_global_optimality_claim": (global_optimality_claim is None)
        == confirmation_gate["require_no_global_optimality_claim"],
        "no_population_claim": (population_claim is None)
        == confirmation_gate["require_no_population_claim"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": _finite_tree(target_rows) == confirmation_gate["require_finite"],
    }
    gate_result = finalize_gates(checks)
    confirms = bool(
        gate_result["passed"] and confirmation["confirms_latin_e_breadth"]
    )
    delivered_values = [
        float(row["retreat"]["exact_positive_value"])
        if row["retreat"]["shadow_accepted"]
        else 0.0
        for row in target_rows
    ]
    result = {
        "schema_version": 1,
        "status": "h32_latin_f_convex_retreat_confirmation_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "fresh_latin_f_targets": 6,
            "warm_steps": 6,
            "adaptive_construction_oracles": 6,
            "final_retreat_strategy_labels": 6,
            "candidate_policies_emitted": 0,
            "cross_target_adaptation": cross_target_adaptation,
            "campaign_events": campaign_events,
            "candidates_frozen_before_labels": candidates_frozen_before_labels,
        },
        "latin_e_parent": {
            "result_sha256": _sha256(_BASE_RESULT),
            "material_target_count": latin_e["promotion"]["material_target_count"],
            "pooled_delivered_exact_value": latin_e["aggregate"][
                "pooled_delivered_exact_value"
            ],
        },
        "target_rows": target_rows,
        "confirmation": confirmation,
        "aggregate": {
            "shadow_accepted_targets": sum(
                row["retreat"]["shadow_accepted"] for row in target_rows
            ),
            "material_target_count": confirmation["material_target_count"],
            "pooled_delivered_exact_value": math.fsum(delivered_values),
            "minimum_delivered_exact_value": min(delivered_values),
            "median_delivered_exact_value": float(np.median(delivered_values)),
            "maximum_delivered_exact_value": max(delivered_values),
            "maximum_measured_live_ms": max(
                row["ledger"]["measured_live_ms"] for row in target_rows
            ),
            "maximum_effective_conservative_live_ms": max(
                row["ledger"]["effective_conservative_live_ms"]
                for row in target_rows
            ),
            "confirms_latin_e_breadth": confirms,
        },
        **gate_result,
        "decision": latin_f_confirmation_decision(
            process_passed=bool(gate_result["passed"]),
            confirms=confirms,
        ),
        "actual_emitted_policy": "immutable_restricted_blueprint_only_on_all_targets",
        "strategy_quality_claim": (
            "six_fresh_latin_f_shadow_confirmation_measurement_only"
            if gate_result["passed"]
            else None
        ),
        "one_seat_global_optimality_claim": global_optimality_claim,
        "strategy_population_claim": population_claim,
        "total_seconds": total_seconds,
        "limitations": [
            "Latin-F confirms or rejects the frozen breadth branch; it does not estimate a population success rate.",
            "No fresh one-step fallback is evaluated and no Latin-E quantity selects or tunes a Latin-F candidate.",
            "The bounded one-round endpoint is not a global one-seat optimum; only each half-retreat exact oracle has safety authority.",
            "All policies remain shadow-only immutable-blueprint emissions; no deployment, composition, cross-street, or broad poker claim is made.",
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_latin_f_convex_retreat_confirmation(args.config, args.output)
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
