"""Direct orchestration for the retained affine selector-cascade replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

from . import h32_retained_affine_selector_cascade_replay as science
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .reporting import environment_metadata


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments/configs/h32-retained-affine-selector-cascade-direct-v1.json"
)
_OUTPUT = (
    _ROOT
    / "experiments/results/h32-retained-affine-selector-cascade-direct-v1.json"
)
_SCIENCE_ADR = (
    _ROOT
    / "docs/decisions/ADR-0199-preregister-retained-affine-selector-cascade-replay.md"
)
_REJECTION_ADRS = (
    _ROOT
    / "docs/decisions/ADR-0200-selector-replay-v1-rejects-on-final-memory-schema-key.md",
    _ROOT
    / "docs/decisions/ADR-0202-corrected-selector-replay-v2-rejects-on-overstrict-schema-guard.md",
    _ROOT
    / "docs/decisions/ADR-0204-final-selector-wrapper-rejects-on-environment-api-mismatch.md",
)
_WRAPPER_ADRS = (
    _ROOT
    / "docs/decisions/ADR-0201-preregister-memory-schema-corrected-selector-replay.md",
    _ROOT
    / "docs/decisions/ADR-0203-preregister-final-four-field-selector-replay-correction.md",
)
_MEMORY_HELPER = _ROOT / "src/pontius/h32_fresh_union_value_audit.py"
_REPORTING_HELPER = _ROOT / "src/pontius/reporting.py"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_retained_affine_selector_cascade_direct_replay.py"

_PATHS = {
    "expected_science_config_sha256": science._CONFIG,
    "expected_science_implementation_sha256": science._IMPLEMENTATION,
    "expected_science_control_test_sha256": science._TEST,
    "expected_science_decision_sha256": _SCIENCE_ADR,
    "expected_v1_rejection_sha256": _REJECTION_ADRS[0],
    "expected_v2_correction_decision_sha256": _WRAPPER_ADRS[0],
    "expected_v2_rejection_sha256": _REJECTION_ADRS[1],
    "expected_v3_correction_decision_sha256": _WRAPPER_ADRS[1],
    "expected_v3_rejection_sha256": _REJECTION_ADRS[2],
    "expected_memory_helper_sha256": _MEMORY_HELPER,
    "expected_reporting_helper_sha256": _REPORTING_HELPER,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_MEMORY_SCHEMA = {
    "gpu_free_bytes",
    "gpu_total_bytes",
    "gpu_pool_used_bytes",
    "gpu_pool_total_bytes",
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required direct selector-replay input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_retained_affine_selector_cascade_direct_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the direct runner review and unchanged scientific protocol."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "orchestration_rule",
        "memory_rule",
        "environment_rule",
        "serialization_rule",
        "replay_scope",
        "outcome_policy",
    }
    if set(config) != fields:
        raise ValueError("direct selector replay fields differ from ADR-0205")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0204_and_direct_result_assembly_review_"
            "before_any_direct_selector_replay"
        ),
        "orchestration_rule": (
            "call_frozen_adr0199_feature_join_scoring_and_control_helpers_"
            "directly_without_monkeypatch_or_schema_alias"
        ),
        "memory_rule": (
            "consume_the_pinned_four_field_snapshot_directly_using_"
            "gpu_pool_total_bytes_and_gpu_free_bytes"
        ),
        "environment_rule": (
            "call_zero_argument_environment_metadata_then_merge_runtime_and_"
            "strict_git_metadata_by_dictionary_expansion"
        ),
        "serialization_rule": (
            "validate_complete_result_with_json_dumps_sort_keys_allow_nan_false_"
            "before_single_path_write"
        ),
        "replay_scope": (
            "reuse_adr0199_targets_features_label_barrier_candidate_strata_"
            "capacity_scoring_controls_gates_and_blueprint_emission_unchanged"
        ),
        "outcome_policy": (
            "no_partial_state_reuse_no_wrapper_and_stop_on_any_direct_runner_"
            "or_inherited_scientific_failure"
        ),
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("direct selector replay workload differs from ADR-0205")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"direct selector replay source mismatch: {field}")
    science_config = json.loads(science._CONFIG.read_text(encoding="utf-8"))
    base = science.parse_h32_retained_affine_selector_cascade_config(science_config)
    return {**config, "science": base}


def memory_extrema(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Validate and consume the raw pinned four-field memory snapshots."""

    if not rows:
        raise ValueError("direct selector replay has no memory snapshots")
    for row in rows:
        if set(row) != _MEMORY_SCHEMA:
            raise ValueError("direct selector replay memory schema differs")
    return {
        "maximum_gpu_pool_bytes": max(
            int(row["gpu_pool_total_bytes"]) for row in rows
        ),
        "minimum_gpu_free_bytes": min(int(row["gpu_free_bytes"]) for row in rows),
    }


def assemble_environment(
    base: Mapping[str, Any],
    runtime: Mapping[str, Any],
    git: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge the real zero-argument environment payload like accepted h32 audits."""

    return {**base, **runtime, "git": dict(git)}


def serialize_result(result: Mapping[str, Any]) -> str:
    """Exercise the exact final serializer before touching the result path."""

    return json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _scientific_gates(
    *,
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    label_parent: Mapping[str, Any],
    git: Mapping[str, Any],
    feature_targets: Sequence[Mapping[str, Any]],
    join: Mapping[str, Any],
    scoring: Mapping[str, Any],
    negative_control: Mapping[str, Any],
    label_deserialized_after_complete_feature_matrix: bool,
    total_seconds: float,
) -> tuple[dict[str, bool], dict[str, Any]]:
    candidates = [
        row for target in feature_targets for row in target["candidate_rows"]
    ]
    affine_rows = [
        row for candidate in candidates for row in candidate["affine_rows"]
    ]
    memory_rows = [row for target in feature_targets for row in target["memory_rows"]]
    gates_config = parsed["gates"]
    maximum_warm_probability = max(
        target["warm_start_distance"]["maximum_probability_error"]
        for target in feature_targets
    )
    maximum_warm_mean_tv = max(
        target["warm_start_distance"]["mean_total_variation"]
        for target in feature_targets
    )
    maximum_own_br_error = max(
        abs(float(candidate["tier"]["identity"]["own_best_response_value_slope"]))
        for candidate in candidates
    )
    maximum_tier_a_error = max(
        float(candidate["tier"]["identity"]["tier_a_identity_error"])
        for candidate in candidates
    )
    intercept_errors = []
    for target in feature_targets:
        anchor_gains = target["blueprint_quality"]["deviation_gains"]
        for candidate in target["candidate_rows"]:
            intercept_errors.extend(
                abs(
                    float(row["deviation_gain_intercept"])
                    - float(anchor_gains[int(row["target_player"])] )
                )
                for row in candidate["affine_rows"]
            )
    maximum_intercept_error = max(intercept_errors, default=0.0)
    memory = memory_extrema(memory_rows)
    control_five = all(
        int(candidate["tier"]["cost"]["opponent_br_conditioned_calls"])
        == gates_config["expected_opponent_br_calls_per_candidate"]
        for candidate in candidates
    )
    finite_payload = {
        "targets": feature_targets,
        "join": join,
        "scoring": scoring,
        "negative_control": negative_control,
        "total_seconds": total_seconds,
    }
    gates = {
        "clean_git": (not git["dirty"]) == gates_config["require_clean_git_state"],
        "source_parent_passed": bool(source_parent["passed"])
        == gates_config["require_source_parent_passed"],
        "label_parent_passed": bool(label_parent["gates"]["passed"])
        == gates_config["require_label_parent_passed"],
        "target_rows": len(feature_targets) == gates_config["expected_target_rows"],
        "public_blocks": len(candidates) // 3
        == gates_config["expected_public_blocks"],
        "candidate_rows": len(candidates) == gates_config["expected_candidate_rows"],
        "affine_seat_rows": len(affine_rows)
        == gates_config["expected_affine_seat_rows"],
        "candidate_set_cardinality": all(
            sum(
                candidate["direction_family"] in parsed["candidate_sets"][set_name]
                for candidate in target["candidate_rows"]
            )
            == expected
            for target in feature_targets
            for set_name, expected in (
                (
                    "regret_vertex_only",
                    gates_config["expected_primary_candidates_per_target"],
                ),
                (
                    "all_families",
                    gates_config["expected_secondary_candidates_per_target"],
                ),
                (
                    "soft_excluded",
                    gates_config["expected_soft_excluded_candidates_per_target"],
                ),
            )
        ),
        "source_checkpoint_identity": all(
            target["source_checkpoint_identity"] for target in feature_targets
        )
        == gates_config["require_source_checkpoint_identity"],
        "target_identity": all(target["target_identity"] for target in feature_targets)
        == gates_config["require_target_identity"],
        "blueprint_identity": all(
            target["blueprint_identity"] for target in feature_targets
        )
        == gates_config["require_blueprint_identity"],
        "warm_start_probability_error": maximum_warm_probability
        <= parsed["maximum_warm_start_probability_error"],
        "warm_start_mean_total_variation": maximum_warm_mean_tv
        <= parsed["maximum_warm_start_mean_total_variation"],
        "complete_feature_matrix_before_label_join": (
            label_deserialized_after_complete_feature_matrix
            == gates_config["require_complete_feature_matrix_before_label_join"]
        ),
        "direction_family_identity": all(
            tuple(
                candidate["direction_family"]
                for candidate in target["candidate_rows"]
            )
            == tuple(
                family
                for _block in range(6)
                for family in parsed["candidate_families"]
            )
            for target in feature_targets
        )
        == gates_config["require_direction_family_identity"],
        "acting_seat_only_scope": all(
            candidate["tier"]["identity"]["acting_seat_only"]
            for candidate in candidates
        )
        == gates_config["require_acting_seat_only_scope"],
        "own_br_invariance": maximum_own_br_error
        <= gates_config["maximum_own_br_slope_error"],
        "tier_a_identity": maximum_tier_a_error
        <= gates_config["maximum_tier_a_identity_error"],
        "affine_intercepts": maximum_intercept_error
        <= gates_config["maximum_affine_intercept_error"],
        "source_quality": join["maximum_source_quality_error"]
        <= gates_config["maximum_source_quality_error"],
        "tier_a_impure_negative_control": bool(negative_control["passed"])
        == gates_config["require_tier_a_impure_negative_control"],
        "five_not_six_charge_control": control_five
        == gates_config["require_five_not_six_charge_control"],
        "search_step_ms": max(target["search_step_ms"] for target in feature_targets)
        <= gates_config["maximum_search_step_ms"],
        "candidate_feature_ms": max(
            candidate["timing"]["complete_candidate_feature_ms"]
            for candidate in candidates
        )
        <= gates_config["maximum_candidate_feature_ms"],
        "gpu_pool": memory["maximum_gpu_pool_bytes"]
        <= gates_config["maximum_gpu_pool_bytes"],
        "physical_free": memory["minimum_gpu_free_bytes"]
        >= gates_config["minimum_physical_free_bytes"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
        "blueprint_emission": all(
            target["emitted_candidate_id"] == "blueprint_average64"
            and target["emitted_policy_sha256"] == target["blueprint_policy_sha256"]
            for target in feature_targets
        )
        == gates_config["require_blueprint_emission"],
        "finite": science._finite_tree(finite_payload)
        == gates_config["require_finite"],
        "strategy_population_claim_null": True
        == gates_config["require_strategy_population_claim_null"],
    }
    gates["passed"] = all(gates.values())
    diagnostics = {
        "candidates": candidates,
        "affine_rows": affine_rows,
        "memory": memory,
        "maximum_warm_probability": maximum_warm_probability,
        "maximum_warm_mean_tv": maximum_warm_mean_tv,
        "maximum_own_br_error": maximum_own_br_error,
        "maximum_tier_a_error": maximum_tier_a_error,
        "maximum_intercept_error": maximum_intercept_error,
        "control_five": control_five,
    }
    return gates, diagnostics


def run_h32_retained_affine_selector_cascade_direct_replay(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Execute the reviewed direct orchestration without a schema wrapper."""

    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    direct = parse_h32_retained_affine_selector_cascade_direct_config(config)
    parsed = direct["science"]
    source_parent = json.loads(science._SOURCE.read_text(encoding="utf-8"))
    git = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    if git["dirty"]:
        raise RuntimeError("direct retained affine selector replay requires clean Git state")
    if not bool(source_parent["passed"]):
        raise ValueError("direct retained affine selector source parent did not pass")

    feature_targets = []
    for target_spec in parsed["targets"]:
        print(f"direct retained affine selector: {target_spec['target']}", flush=True)
        feature_targets.append(
            science._run_feature_target(parsed, source_parent, target_spec, cp)
        )

    feature_payload = [
        {
            "target": target["target"],
            "candidate_rows": target["candidate_rows"],
            "capacity_before_label_join": target["capacity_before_label_join"],
        }
        for target in feature_targets
    ]
    feature_matrix_sha256_before_label_join = hashlib.sha256(
        json.dumps(feature_payload, sort_keys=True, allow_nan=False).encode("utf-8")
    ).hexdigest()

    label_join_started = time.perf_counter()
    label_parent = json.loads(science._LABEL_RESULT.read_text(encoding="utf-8"))
    label_deserialized_after_complete_feature_matrix = all(
        len(target["candidate_rows"]) == 18 for target in feature_targets
    )
    join = science._join_retained_labels(feature_targets, label_parent)
    label_join_ms = (time.perf_counter() - label_join_started) * 1000.0
    scoring = science._score_replay(feature_targets, parsed)
    negative_control = science.contaminated_tier_a_negative_control()
    total_seconds = time.perf_counter() - started
    gates, diagnostics = _scientific_gates(
        parsed=parsed,
        source_parent=source_parent,
        label_parent=label_parent,
        git=git,
        feature_targets=feature_targets,
        join=join,
        scoring=scoring,
        negative_control=negative_control,
        label_deserialized_after_complete_feature_matrix=(
            label_deserialized_after_complete_feature_matrix
        ),
        total_seconds=total_seconds,
    )
    candidates = diagnostics["candidates"]
    environment = assemble_environment(environment_metadata(), runtime, git)
    result = {
        "schema_version": 1,
        "status": "reviewed_direct_h32_retained_affine_selector_replay_executed",
        "methodology": {
            "direct_orchestration_without_monkeypatch_or_alias": True,
            "opaque_label_sha256_checked_before_feature_extraction": True,
            "feature_rows_computed_before_label_json_deserialization": True,
            "feature_list_frozen_before_extraction": True,
            "labels_retained_from_adr0186": True,
            "fresh_strategy_labels": 0,
            "primary_set": parsed["primary_candidate_set"],
            "secondary_set": parsed["secondary_candidate_set"],
            "family_confound_control": parsed["family_confound_control_set"],
            "capacity_derived_before_label_join": True,
            "raw_four_field_memory_snapshot_consumed_directly": True,
            "zero_argument_environment_metadata_merged_explicitly": True,
            "exact_digests_diagnostic_only_for_reconstructed_floating_policies": True,
        },
        "environment": environment,
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "science_config_sha256": _sha256(science._CONFIG),
        "science_implementation_sha256": _sha256(science._IMPLEMENTATION),
        "feature_matrix_sha256_before_label_join": (
            feature_matrix_sha256_before_label_join
        ),
        "label_join": {
            "deserialized_after_complete_feature_matrix": (
                label_deserialized_after_complete_feature_matrix
            ),
            "label_join_ms": label_join_ms,
            **join,
        },
        "negative_controls": {
            "impure_direction": negative_control,
            "five_not_six_charge_passed": diagnostics["control_five"],
        },
        "target_rows": feature_targets,
        "scoring": scoring,
        "aggregate": {
            "targets": len(feature_targets),
            "public_blocks": len(candidates) // 3,
            "candidate_rows": len(candidates),
            "affine_seat_rows": len(diagnostics["affine_rows"]),
            "opponent_br_conditioned_calls": sum(
                int(candidate["tier"]["cost"]["opponent_br_conditioned_calls"])
                for candidate in candidates
            ),
            "maximum_own_br_slope_error": diagnostics["maximum_own_br_error"],
            "maximum_tier_a_identity_error": diagnostics["maximum_tier_a_error"],
            "maximum_affine_intercept_error": diagnostics[
                "maximum_intercept_error"
            ],
            "maximum_warm_start_probability_error": diagnostics[
                "maximum_warm_probability"
            ],
            "maximum_warm_start_mean_total_variation": diagnostics[
                "maximum_warm_mean_tv"
            ],
            **diagnostics["memory"],
        },
        "gates": gates,
        "passed": gates["passed"],
        "decision": (
            "accept_reviewed_direct_retained_affine_selector_replay"
            if gates["passed"]
            else "reject_reviewed_direct_retained_affine_selector_replay"
        ),
        "strategy_population_claim": None,
        "total_audit_seconds": total_seconds,
        "limitations": [
            "All six targets and every label were exposed before this development replay.",
            "The primary six-set may be library-limited; saturation is not selector evidence.",
            "The raw 18-set can reward family discrimination, so it is weak evidence only.",
            (
                "The soft-excluded 12-set controls that family confound but "
                "retains near-duplicate vertices."
            ),
            (
                "The warm-telemetry-reuse capacity is diagnostic until the "
                "zero-contraction Tier-A coefficient is exposed by the live step."
            ),
            (
                "No new strategy label, policy emission, deployment rule, or "
                "strategy-quality claim is authorized."
            ),
        ],
    }
    serialized = serialize_result(result)
    output_path.write_text(serialized, encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_retained_affine_selector_cascade_direct_replay(
        args.config, args.output
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "aggregate": result["aggregate"],
                "scoring": result["scoring"]["cascade_by_candidate_set"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
