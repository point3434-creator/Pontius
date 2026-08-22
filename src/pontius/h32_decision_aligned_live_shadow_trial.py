"""Prospective live-shadow trial at six fresh current-decision roots."""

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

from . import h32_fresh_convex_retreat_replication as core
from .cupy_sparse_incidence import release_cupy_memory_pool
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .h32_decision_aligned_continuation_setup import (
    build_decision_aligned_continuation_setup,
    decision_aligned_core_setup_adapter,
)
from .h32_continuation_root_ledger import _setup as historical_setup
from .h32_fresh_convex_retreat_replication import (
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
_CONFIG = _ROOT / "experiments/configs/h32-decision-aligned-live-shadow-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-decision-aligned-live-shadow-v1.json"
_BASE_CONFIG = (
    _ROOT / "experiments/configs/h32-fresh-convex-retreat-replication-v2.json"
)
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_MANIFEST = (
    _ROOT / "experiments/results/h32-decision-aligned-posterior-manifest-v1.json"
)
_MANIFEST_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0262-post-call-panel-is-fresh-current-and-nondegenerate.md"
)
_LATIN_F_RESULT = (
    _ROOT / "experiments/results/h32-latin-f-convex-retreat-confirmation-v1.json"
)
_LATIN_F_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0260-latin-f-confirms-convex-breadth-with-two-interior-abstentions.md"
)
_CORE_IMPLEMENTATION = (
    _ROOT / "src/pontius/h32_fresh_convex_retreat_replication.py"
)
_SETUP_IMPLEMENTATION = (
    _ROOT / "src/pontius/h32_decision_aligned_continuation_setup.py"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_decision_aligned_live_shadow_trial.py"

_PATHS = {
    "expected_base_config_sha256": _BASE_CONFIG,
    "expected_manifest_result_sha256": _MANIFEST,
    "expected_manifest_decision_sha256": _MANIFEST_DECISION,
    "expected_latin_f_result_sha256": _LATIN_F_RESULT,
    "expected_latin_f_decision_sha256": _LATIN_F_DECISION,
    "expected_core_implementation_sha256": _CORE_IMPLEMENTATION,
    "expected_setup_implementation_sha256": _SETUP_IMPLEMENTATION,
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required decision-aligned shadow input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decision_aligned_transfer_assessment(
    target_rows: list[Mapping[str, Any]],
    *,
    minimum_material_targets: int,
    minimum_material_exact_value: float,
) -> dict[str, Any]:
    """Apply the unchanged breadth threshold without making it a process gate."""

    assessed = fresh_replication_promotion(
        target_rows,
        minimum_material_targets=minimum_material_targets,
        minimum_material_exact_value=minimum_material_exact_value,
    )
    transfers = bool(assessed.pop("authorizes_latin_f_confirmation"))
    return {**assessed, "decision_aligned_value_transfers": transfers}


def decision_aligned_shadow_decision(*, process_passed: bool, transfers: bool) -> str:
    if not process_passed:
        return "reject_decision_aligned_live_shadow_execution"
    if transfers:
        return "accept_decision_aligned_shadow_transfer_and_authorize_post_fold_preregistration"
    return "accept_decision_aligned_shadow_execution_but_reject_transfer_claim"


def _manifest_target_specs(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
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
    specs = []
    for row in manifest["target_rows"]:
        board, family = source_map[str(row["source"])]
        specs.append(
            {
                "target_id": row["target_id"],
                "source": row["source"],
                "observed_bettor": row["observed_bettor"],
                "observed_responder": row["observed_responder"],
                "observed_response": row["observed_response"],
                "acting_player": row["acting_player"],
                "round": row["round"],
                "public_prefix": row["public_prefix"],
                "source_belief_sha256": row["source_belief_sha256"],
                "target_belief_sha256": row["target_belief_sha256"],
                "target_descriptor_sha256": row["target_descriptor_sha256"],
                "board": board,
                "range_family": family,
            }
        )
    return specs


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "target_selection_rule",
        "target_specs",
        "setup_rule",
        "adapter_rule",
        "campaign_barrier_rule",
        "transfer_rule",
        "success_decision",
        "negative_science_decision",
        "strategy_label_policy",
        "claims_policy",
        "live_shadow_gates",
    }
    if set(config) != expected:
        raise ValueError("decision-aligned shadow fields differ from ADR-0263")
    for field_name, path in _PATHS.items():
        if config[field_name] != _sha256(path):
            raise ValueError(f"decision-aligned shadow provenance mismatch: {field_name}")
    base = _parse_latin_e_config(
        json.loads(_BASE_CONFIG.read_text(encoding="utf-8"))
    )
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    frozen_specs = _manifest_target_specs(manifest)
    exact = {
        "evidence_stage": (
            "preregistered_after_adr0262_before_any_decision_aligned_warm_step_"
            "candidate_or_strategy_label"
        ),
        "seed": 20260822,
        "target_selection_rule": (
            "all_six_adr0262_targets_in_manifest_order_zero_tv_latin_value_"
            "opportunity_or_timing_selection"
        ),
        "target_specs": frozen_specs,
        "setup_rule": (
            "reconstruct_checks_bet_first_call_posterior_and_require_declared_"
            "actor_current_with_three_downstream_responders"
        ),
        "adapter_rule": (
            "temporarily_replace_only_the_sealed_core_setup_function_for_the_"
            "bounded_campaign_and_restore_it_even_on_failure"
        ),
        "campaign_barrier_rule": (
            "construct_and_freeze_all_six_candidates_before_any_final_retreat_oracle"
        ),
        "transfer_rule": (
            "report_process_separately_and_call_value_transfer_only_if_at_least_"
            "four_material_targets_above_0_001_both_families_and_all_schedules_fit"
        ),
        "success_decision": (
            "accept_decision_aligned_shadow_transfer_and_authorize_post_fold_"
            "preregistration"
        ),
        "negative_science_decision": (
            "accept_decision_aligned_shadow_execution_but_reject_transfer_claim"
        ),
        "strategy_label_policy": (
            "six_fixed_first_evaluation_post_call_retreat_labels_global_"
            "prelabel_barrier_no_cross_target_adaptation"
        ),
        "claims_policy": (
            "fresh_decision_aligned_shadow_measurement_only_no_emission_"
            "fallback_population_deployment_or_global_optimality_claim"
        ),
    }
    for field_name, expected_value in exact.items():
        if config[field_name] != expected_value:
            raise ValueError(
                f"decision-aligned shadow field differs from ADR-0263: {field_name}"
            )
    live_shadow_gates = {
        "expected_targets": 6,
        "expected_sources": 6,
        "expected_bettors": 6,
        "expected_observed_responders": 6,
        "expected_acting_players": 6,
        "expected_candidates_frozen_before_labels": 6,
        "expected_exact_oracles": 12,
        "expected_strategy_labels": 6,
        "require_manifest_parent_passed": True,
        "require_manifest_authorized": True,
        "require_manifest_strategy_labels_zero": True,
        "require_latin_f_parent_passed": True,
        "require_latin_f_authorized": True,
        "require_manifest_order": True,
        "require_post_call_only": True,
        "require_current_actor_rule": True,
        "require_first_final_label_evaluation": True,
        "require_setup_adapter_active": True,
        "require_setup_adapter_restored": True,
        "require_campaign_barrier_before_labels": True,
        "require_no_cross_target_adaptation": True,
        "require_blueprint_external_emission": True,
        "require_no_global_optimality_claim": True,
        "require_no_population_claim": True,
        "require_finite": True,
    }
    if config["live_shadow_gates"] != live_shadow_gates:
        raise ValueError("decision-aligned shadow gates differ from ADR-0263")
    gates = {
        key: value
        for key, value in base["gates"].items()
        if key != "require_latin_f_labels_zero"
    }
    gates.update(
        {
            "expected_behavioral_information_sets": 32,
            "expected_policy_variables": 64,
        }
    )
    return {
        **base,
        **{field_name: config[field_name] for field_name in _PATHS},
        "evidence_stage": config["evidence_stage"],
        "seed": config["seed"],
        "prior_label_incident": "none_decision_aligned_final_labels_unopened",
        "target_selection_rule": config["target_selection_rule"],
        "target_specs": tuple(dict(row) for row in config["target_specs"]),
        "acting_player_rule": "manifest_second_responder_is_current_player",
        "scope": (
            "six_fresh_post_call_current_decisions_one_per_source_bettor_"
            "observed_responder_and_acting_player_shadow_only"
        ),
        "campaign_barrier_rule": config["campaign_barrier_rule"],
        "certificate_reconstruction_rule": (
            "rebuild_each_pinned_post_call_context_after_global_barrier_recheck_"
            "identity_and_charge_only_final_oracle_to_live_ledger"
        ),
        "promotion_rule": config["transfer_rule"],
        "strategy_label_policy": config["strategy_label_policy"],
        "setup_rule": config["setup_rule"],
        "adapter_rule": config["adapter_rule"],
        "transfer_rule": config["transfer_rule"],
        "success_decision": config["success_decision"],
        "negative_science_decision": config["negative_science_decision"],
        "claims_policy": config["claims_policy"],
        "live_shadow_gates": live_shadow_gates,
        "gates": gates,
    }


def run_h32_decision_aligned_live_shadow_trial(
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
    latin_f = load_artifact(
        _LATIN_F_RESULT,
        expected_sha256=parsed["expected_latin_f_result_sha256"],
        require_passed=True,
    ).payload

    campaign_events = ["inputs_pinned"]
    candidate_bundles = []
    adapter_active = False
    with decision_aligned_core_setup_adapter():
        adapter_active = core._setup is build_decision_aligned_continuation_setup
        for spec in parsed["target_specs"]:
            candidate_bundles.append(
                core._construct_target_candidate(parsed, source, spec, cp)
            )
            gc.collect()
            release_cupy_memory_pool()
        prelabel_snapshots = [
            bundle["barrier"].snapshot() for bundle in candidate_bundles
        ]
        candidates_frozen_before_labels = sum(
            row["phase"] == "candidate_frozen" for row in prelabel_snapshots
        )
        if candidates_frozen_before_labels != len(parsed["target_specs"]):
            raise RuntimeError(
                "decision-aligned campaign barrier did not freeze every target"
            )
        if any(
            bundle["construction_row"]["new_strategy_quality_labels_generated"]
            != 0
            for bundle in candidate_bundles
        ):
            raise RuntimeError(
                "decision-aligned final label opened before campaign barrier"
            )
        campaign_events.append("all_candidates_frozen")
        target_rows = []
        for spec, bundle in zip(
            parsed["target_specs"], candidate_bundles, strict=True
        ):
            row = core._certify_target_candidate(parsed, source, bundle, cp)
            row.update(
                {
                    "observed_responder": spec["observed_responder"],
                    "observed_response": spec["observed_response"],
                    "public_prefix": spec["public_prefix"],
                    "root_current_player": spec["acting_player"],
                    "downstream_responders_after_actor": 3,
                }
            )
            target_rows.append(row)
            gc.collect()
            release_cupy_memory_pool()
        campaign_events.append("all_retreat_certificates_complete")
    adapter_restored = core._setup is historical_setup

    transfer = decision_aligned_transfer_assessment(
        target_rows,
        minimum_material_targets=int(parsed["minimum_material_targets"]),
        minimum_material_exact_value=float(parsed["minimum_material_exact_value"]),
    )
    total_seconds = time.perf_counter() - started
    gate = parsed["gates"]
    live_gate = parsed["live_shadow_gates"]
    fixed_target_ids = [row["target_id"] for row in parsed["target_specs"]]
    manifest_target_ids = [row["target_id"] for row in manifest["target_rows"]]
    global_optimality_claim = None
    population_claim = None
    cross_target_adaptation = False
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": all(
            artifact_passed(row) for row in (source, manifest, latin_f)
        )
        == gate["require_parents_passed"],
        "manifest_parent_passed": artifact_passed(manifest)
        == live_gate["require_manifest_parent_passed"],
        "manifest_authorized": (
            manifest["decision"]
            == "authorize_preregistered_decision_aligned_live_shadow_trial"
        )
        == live_gate["require_manifest_authorized"],
        "manifest_strategy_labels_zero": (
            manifest["methodology"]["strategy_labels"] == 0
        )
        == live_gate["require_manifest_strategy_labels_zero"],
        "latin_f_parent_passed": artifact_passed(latin_f)
        == live_gate["require_latin_f_parent_passed"],
        "latin_f_authorized": (
            latin_f["decision"]
            == "accept_latin_ef_breadth_and_authorize_live_shadow_preregistration"
        )
        == live_gate["require_latin_f_authorized"],
        "target_count": len(target_rows) == live_gate["expected_targets"],
        "source_count": len({row["source"] for row in target_rows})
        == live_gate["expected_sources"],
        "bettor_count": len({row["observed_bettor"] for row in target_rows})
        == live_gate["expected_bettors"],
        "observed_responder_count": len(
            {row["observed_responder"] for row in target_rows}
        )
        == live_gate["expected_observed_responders"],
        "acting_player_count": len({row["acting_player"] for row in target_rows})
        == live_gate["expected_acting_players"],
        "manifest_order": fixed_target_ids == manifest_target_ids
        == [row["target_id"] for row in target_rows]
        and live_gate["require_manifest_order"],
        "post_call_only": all(
            row["round"] == "decision_aligned_call_v1"
            and row["observed_response"] == "call"
            for row in target_rows
        )
        == live_gate["require_post_call_only"],
        "current_actor_rule": all(
            row["observed_responder"] == (row["observed_bettor"] + 1) % 6
            and row["acting_player"] == (row["observed_bettor"] + 2) % 6
            and row["root_current_player"] == row["acting_player"]
            and row["downstream_responders_after_actor"] == 3
            for row in target_rows
        )
        == live_gate["require_current_actor_rule"],
        "first_final_label_evaluation": all(
            row["new_strategy_quality_labels_generated"] == 1
            for row in target_rows
        )
        == live_gate["require_first_final_label_evaluation"],
        "setup_adapter_active": adapter_active
        == live_gate["require_setup_adapter_active"],
        "setup_adapter_restored": adapter_restored
        == live_gate["require_setup_adapter_restored"],
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
            row["acting_public_nodes"] == 1
            and row["behavioral_information_sets"]
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
            and row["initial_gain_rows"]
            == gate["expected_initial_gain_rows_per_target"]
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
            == live_gate["expected_candidates_frozen_before_labels"]
            and campaign_events[:2] == ["inputs_pinned", "all_candidates_frozen"]
            and all(
                row["phase"] == "candidate_frozen"
                and row["events"] == ["inputs_pinned", "candidate_frozen"]
                for row in prelabel_snapshots
            )
        )
        == live_gate["require_campaign_barrier_before_labels"],
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
        == live_gate["require_no_cross_target_adaptation"],
        "blueprint_external_emission": all(
            row["actual_emitted_policy_sha256"]
            == row["restricted_blueprint_policy_sha256"]
            and row["candidate_policies_emitted"] == 0
            for row in target_rows
        )
        == live_gate["require_blueprint_external_emission"],
        "oracle_count": sum(row["exact_oracles_executed"] for row in target_rows)
        == live_gate["expected_exact_oracles"],
        "strategy_label_count": sum(
            row["new_strategy_quality_labels_generated"] for row in target_rows
        )
        == live_gate["expected_strategy_labels"],
        "no_global_optimality_claim": (global_optimality_claim is None)
        == live_gate["require_no_global_optimality_claim"],
        "no_population_claim": (population_claim is None)
        == live_gate["require_no_population_claim"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": core._finite_tree(target_rows) == live_gate["require_finite"],
    }
    gate_result = finalize_gates(checks)
    transfers = bool(
        gate_result["passed"] and transfer["decision_aligned_value_transfers"]
    )
    delivered_values = [
        float(row["retreat"]["exact_positive_value"])
        if row["retreat"]["shadow_accepted"]
        else 0.0
        for row in target_rows
    ]
    result = {
        "schema_version": 1,
        "status": "h32_decision_aligned_live_shadow_trial_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "fresh_decision_aligned_targets": 6,
            "warm_steps": 6,
            "adaptive_construction_oracles": 6,
            "final_retreat_strategy_labels": 6,
            "candidate_policies_emitted": 0,
            "cross_target_adaptation": cross_target_adaptation,
            "campaign_events": campaign_events,
            "candidates_frozen_before_labels": candidates_frozen_before_labels,
            "setup_adapter_active_during_campaign": adapter_active,
            "setup_adapter_restored_after_campaign": adapter_restored,
        },
        "parents": {
            "manifest_result_sha256": _sha256(_MANIFEST),
            "latin_f_result_sha256": _sha256(_LATIN_F_RESULT),
        },
        "target_rows": target_rows,
        "transfer": transfer,
        "aggregate": {
            "shadow_accepted_targets": sum(
                row["retreat"]["shadow_accepted"] for row in target_rows
            ),
            "material_target_count": transfer["material_target_count"],
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
            "decision_aligned_value_transfers": transfers,
        },
        **gate_result,
        "decision": decision_aligned_shadow_decision(
            process_passed=bool(gate_result["passed"]),
            transfers=transfers,
        ),
        "actual_emitted_policy": "immutable_restricted_blueprint_only_on_all_targets",
        "strategy_quality_claim": (
            "six_fresh_decision_aligned_shadow_measurements_only"
            if gate_result["passed"]
            else None
        ),
        "one_seat_global_optimality_claim": global_optimality_claim,
        "strategy_population_claim": population_claim,
        "total_seconds": total_seconds,
        "limitations": [
            "All six targets observe a call; post-fold transfer remains unopened.",
            "The boards and blueprints are retained and the fixed panel is not an IID sample.",
            "No fresh regret-vertex fallback is evaluated, so no fresh fallback-dominance claim is available.",
            "The bounded one-round endpoint is not globally optimal; only each half-retreat exact oracle has safety authority.",
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
    result = run_h32_decision_aligned_live_shadow_trial(args.config, args.output)
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
