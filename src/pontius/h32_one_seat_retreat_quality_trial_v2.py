"""Numerically identified successor to the rejected bytewise retreat gate."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping

from . import h32_one_seat_retreat_quality_trial as _v1
from .h32_affine_resident_cache_preflight import _strict_git_metadata, _validate_runtime
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    serialize_result,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-one-seat-retreat-quality-v2.json"
_OUTPUT = _ROOT / "experiments/results/h32-one-seat-retreat-quality-v2.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_OPTIMIZER = _ROOT / "experiments/results/h32-one-round-convex-master-v1.json"
_FALLBACK = _ROOT / "experiments/results/h32-heldout-continuation-depth-value-v1.json"
_REJECTED_CONFIG = _ROOT / "experiments/configs/h32-one-seat-retreat-quality-v1.json"
_REJECTED_IMPLEMENTATION = _ROOT / "src/pontius/h32_one_seat_retreat_quality_trial.py"
_REJECTED_TEST = _ROOT / "tests/test_h32_one_seat_retreat_quality_trial.py"
_REJECTED_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0250-reject-bytewise-retreat-reconstruction-before-labels.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_one_seat_retreat_quality_trial_v2.py"

_PATHS = {
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
    "expected_rejected_config_sha256": _REJECTED_CONFIG,
    "expected_rejected_implementation_sha256": _REJECTED_IMPLEMENTATION,
    "expected_rejected_control_test_sha256": _REJECTED_TEST,
    "expected_rejected_decision_sha256": _REJECTED_DECISION,
}

_POLICY_DIGEST_DIAGNOSTICS = frozenset(
    {"first_candidate_policy", "endpoint_policy", "retreat_policy"}
)


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required retreat-quality-v2 input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(slots=True)
class NumericalQualityLabelBarrier:
    """Freeze the algorithmic candidate while retaining policy digests as diagnostics."""

    phase: str = "inputs_pinned"
    events: list[str] = field(default_factory=lambda: ["inputs_pinned"])
    semantic_identity_checks: dict[str, bool] = field(default_factory=dict)
    policy_digest_diagnostics: dict[str, bool] = field(default_factory=dict)

    def freeze_candidate(self, identity_checks: Mapping[str, bool]) -> None:
        if self.phase != "inputs_pinned":
            raise RuntimeError("numerical quality candidate can be frozen only once")
        if not identity_checks or any(
            type(value) is not bool for value in identity_checks.values()
        ):
            raise ValueError("numerical quality identity checks must be Boolean")
        if not _POLICY_DIGEST_DIAGNOSTICS.issubset(identity_checks):
            raise ValueError("numerical quality digest diagnostics are incomplete")
        semantic = {
            key: value
            for key, value in identity_checks.items()
            if key not in _POLICY_DIGEST_DIAGNOSTICS
        }
        diagnostics = {
            key: identity_checks[key] for key in sorted(_POLICY_DIGEST_DIAGNOSTICS)
        }
        if not semantic or not all(semantic.values()):
            raise RuntimeError("numerical quality candidate changed algorithmic branch")
        self.semantic_identity_checks = semantic
        self.policy_digest_diagnostics = diagnostics
        self.phase = "candidate_frozen"
        self.events.append("candidate_frozen")

    def complete_retreat_certificate(self) -> None:
        if self.phase != "candidate_frozen":
            raise RuntimeError("retreat certificate requires a frozen numerical candidate")
        self.phase = "retreat_certificate_complete"
        self.events.append("retreat_certificate_complete")

    def open_sealed_comparator(self) -> None:
        if self.phase != "retreat_certificate_complete":
            raise RuntimeError("sealed comparator cannot open before retreat certification")
        self.phase = "sealed_comparator_opened"
        self.events.append("sealed_comparator_opened")

    def snapshot(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "events": list(self.events),
            "semantic_identity_checks": dict(self.semantic_identity_checks),
            "policy_digest_diagnostics": dict(self.policy_digest_diagnostics),
        }


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    rejected = json.loads(_REJECTED_CONFIG.read_text(encoding="utf-8"))
    expected = {
        "evidence_stage",
        "expected_implementation_sha256",
        "expected_control_test_sha256",
        "expected_rejected_config_sha256",
        "expected_rejected_implementation_sha256",
        "expected_rejected_control_test_sha256",
        "expected_rejected_decision_sha256",
        "rejected_preregistration_commit",
        "policy_digest_identity_rule",
        "expected_first_oracle_objective",
        "expected_first_oracle_maximum_cap_violation",
        "expected_first_oracle_maximum_epigraph_violation",
        "expected_first_oracle_response_signatures",
        "gate_additions",
    }
    if set(config) != expected:
        raise ValueError("retreat-quality-v2 config fields differ from ADR-0251")
    for field_name, path in _PATHS.items():
        if config[field_name] != _sha256(path):
            raise ValueError(f"retreat-quality-v2 provenance mismatch: {field_name}")

    exact = {
        "evidence_stage": (
            "preregistered_after_adr0250_before_any_retreat_certificate_or_"
            "fallback_label_join"
        ),
        "rejected_preregistration_commit": "b1a951280cae56519aa5505b9eb347227e9b88d1",
        "policy_digest_identity_rule": (
            "first_endpoint_and_retreat_policy_digests_recorded_diagnostic_only_"
            "algorithm_cut_rows_bounds_and_float64_witnesses_are_authority"
        ),
        "expected_first_oracle_objective": 0.03699431926539898,
        "expected_first_oracle_maximum_cap_violation": 8.300123213047898e-05,
        "expected_first_oracle_maximum_epigraph_violation": 0.0007270318760673571,
        "expected_first_oracle_response_signatures": [
            "ac6ca61d21f38bf1d96ef1b9fba584092d98695800591876baee6372696d769a",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "66ca0830db3260f69d45a46d8b390a5f889f35e17352ef4ba0746f9bc29a7f3e",
            "6dc6ae44bcabd1ee5b60fd411053126627049f6ca2b4055a1fa9e2027a0b50b6",
            "f18d9a7054304b45daaa92739a4f6afbb4dce10c0c66c05e1e6b961074f78890",
            "78c8486b36c9d5e1d79303093c6f2dec647219b5dd2c923c932d5307d085a83a",
        ],
    }
    for field_name, expected_value in exact.items():
        if config[field_name] != expected_value:
            raise ValueError(f"retreat-quality-v2 field differs from ADR-0251: {field_name}")

    gate_additions = {
        "require_first_oracle_numeric_reproduction": True,
        "require_policy_digests_diagnostic_only": True,
    }
    if config["gate_additions"] != gate_additions:
        raise ValueError("retreat-quality-v2 gates differ from ADR-0251")
    gates = {**rejected["gates"], **gate_additions}
    return {
        **rejected,
        **config,
        "target": dict(rejected["target"]),
        "gates": gates,
    }


def _first_oracle_reproduction(
    parsed: Mapping[str, Any], target: Mapping[str, Any]
) -> dict[str, bool]:
    first = target["first_oracle"]
    allowance = float(parsed["quality_numerical_allowance"])
    return {
        "objective": abs(
            float(first["nash_conv"])
            - float(parsed["expected_first_oracle_objective"])
        )
        <= allowance,
        "maximum_cap_violation": abs(
            float(first["maximum_cap_violation"])
            - float(parsed["expected_first_oracle_maximum_cap_violation"])
        )
        <= allowance,
        "maximum_epigraph_violation": abs(
            float(first["maximum_epigraph_violation"])
            - float(parsed["expected_first_oracle_maximum_epigraph_violation"])
        )
        <= allowance,
        "response_signatures": first["response_signature_sha256"]
        == parsed["expected_first_oracle_response_signatures"],
        "violating_players": first["epigraph_violating_players"]
        == parsed["expected_cut_players"],
        "cap_allowance": first["cap_allowance"]
        == float(parsed["cap_numerical_allowance"]),
        "epigraph_allowance": first["epigraph_allowance"]
        == float(parsed["epigraph_separation_allowance"]),
        "cap_rejection": first["cap_feasible"] is False,
        "epigraph_rejection": first["epigraph_closed"] is False,
    }


def run_h32_one_seat_retreat_quality_trial_v2(
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
    optimizer = load_artifact(
        _OPTIMIZER,
        expected_sha256=parsed["expected_optimizer_result_sha256"],
        require_passed=True,
    ).payload
    barrier = NumericalQualityLabelBarrier()
    target = _v1._run_target(parsed, source, optimizer, cp, barrier)

    barrier.open_sealed_comparator()
    fallback_artifact = load_artifact(
        _FALLBACK,
        expected_sha256=parsed["expected_fallback_result_sha256"],
        require_passed=True,
    ).payload
    fallback, fallback_checks = _v1._extract_fallback_comparator(
        fallback_artifact,
        parsed,
    )
    comparison = _v1.adjudicate_retreat_replication(
        retreat_value=float(target["retreat"]["exact_positive_value"]),
        retreat_conservative_ledger_ms=float(target["ledger"]["conservative_live_ms"]),
        fallback_value=float(fallback["exact_positive_value"]),
        fallback_ledger_ms=float(fallback["charged_ledger_ms"]),
        raw_guard_value=float(target["raw_guard"]),
    )
    first_reproduction = _first_oracle_reproduction(parsed, target)
    total_seconds = time.perf_counter() - started
    strategy_population_claim = None
    gate = parsed["gates"]
    masters = target["masters"]
    retreat = target["retreat"]
    certificate = retreat["exact_certificate"]
    semantic_identity = barrier.semantic_identity_checks
    digest_diagnostics = barrier.policy_digest_diagnostics
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": all(
            artifact_passed(row) for row in (source, optimizer, fallback_artifact)
        )
        == gate["require_parents_passed"],
        "target_identity": bool(
            target["source_checkpoint_identity"] and target["target_identity"]
        )
        == gate["require_target_identity"],
        "blueprint_identity": bool(target["blueprint_identity"])
        == gate["require_blueprint_identity"],
        "warm_start_identity": (
            target["warm_start_distance"]["maximum_probability_error"]
            <= gate["maximum_warm_start_probability_error"]
            and target["warm_start_distance"]["mean_total_variation"]
            <= gate["maximum_warm_start_mean_total_variation"]
        )
        == gate["require_warm_start_identity"],
        "path_single_visit": target["path_single_visit"]
        == gate["require_path_single_visit"],
        "acting_node_count": target["acting_public_nodes"]
        == gate["expected_acting_public_nodes"],
        "information_set_count": target["behavioral_information_sets"]
        == gate["expected_behavioral_information_sets"],
        "policy_variable_count": target["policy_variables"]
        == gate["expected_policy_variables"],
        "epigraph_variable_count": target["epigraph_variables"]
        == gate["expected_epigraph_variables"],
        "initial_profile_pass_count": target["initial_profile_passes"]
        == gate["expected_initial_profile_passes"],
        "initial_response_pass_count": target["initial_response_passes"]
        == gate["expected_initial_response_passes"],
        "initial_gain_row_count": target["initial_gain_rows"]
        == gate["expected_initial_gain_rows"],
        "initial_row_identity": target["maximum_initial_row_error"]
        <= gate["maximum_initial_row_error"],
        "cut_row_count": len(target["cut_rows"]) == gate["expected_cut_rows"],
        "cut_row_identity": target["maximum_cut_row_error"]
        <= gate["maximum_cut_row_error"],
        "profile_equivalence": target["maximum_profile_equivalence_error"]
        <= gate["maximum_profile_equivalence_error"],
        "master_primal": target["maximum_master_primal_error"]
        <= gate["maximum_master_primal_error"],
        "master_dual": target["maximum_master_dual_error"]
        <= gate["maximum_master_dual_error"],
        "candidate_projection": max(
            target["first_candidate_projection_error"],
            target["second_candidate_projection_error"],
        )
        <= gate["maximum_projection_error"],
        "raw_guard": abs(target["raw_guard"] - 3e-9)
        <= gate["maximum_raw_guard_error"],
        "cold_setup_time": target["cold_setup_ms"] <= gate["maximum_cold_setup_ms"],
        "warm_step_time": target["warm_step"]["wall_ms"]
        <= gate["maximum_warm_step_ms"],
        "initial_row_time": target["initial_row_ms"]
        <= gate["maximum_initial_row_ms"],
        "master_time": max(row["solve_ms"] for row in masters)
        <= gate["maximum_master_ms"],
        "oracle_time": max(
            target["first_oracle"]["wall_ms"], certificate["wall_ms"]
        )
        <= gate["maximum_oracle_ms"],
        "cut_extraction_time": target["cut_extraction_ms"]
        <= gate["maximum_cut_extraction_ms"],
        "gpu_pool": target["maximum_gpu_pool_total_bytes"]
        <= gate["maximum_gpu_pool_bytes"],
        "physical_free": target["minimum_gpu_free_bytes"]
        >= gate["minimum_physical_free_bytes"],
        "external_axis_coverage": target["exact_external_axis_coverage"]
        == gate["require_exact_external_axis_coverage"],
        "optimizer_identity": all(semantic_identity.values())
        == gate["require_optimizer_identity"],
        "first_oracle_numeric_reproduction": all(first_reproduction.values())
        == gate["require_first_oracle_numeric_reproduction"],
        "policy_digests_diagnostic_only": (
            set(digest_diagnostics) == _POLICY_DIGEST_DIAGNOSTICS
            and all(type(value) is bool for value in digest_diagnostics.values())
        )
        == gate["require_policy_digests_diagnostic_only"],
        "exact_oracle_count": target["exact_oracles_executed"]
        == gate["expected_exact_oracles"],
        "retreat_exact_certificate": bool(retreat["independently_certified"])
        == gate["require_retreat_exact_certificate"],
        "retreat_cap_feasible": bool(certificate["cap_feasible"])
        == gate["require_retreat_cap_feasible"],
        "retreat_positive_value": (
            retreat["exact_positive_value"]
            > float(parsed["quality_numerical_allowance"])
        )
        == gate["require_retreat_positive_value"],
        "retreat_jensen_bound": bool(retreat["jensen_bound_passed"])
        == gate["require_retreat_jensen_bound"],
        "retreat_interior_slack": bool(retreat["interior_slack_passed"])
        == gate["require_retreat_interior_slack"],
        "fallback_identity": all(fallback_checks.values())
        == gate["require_fallback_identity"],
        "label_barrier": barrier.events
        == [
            "inputs_pinned",
            "candidate_frozen",
            "retreat_certificate_complete",
            "sealed_comparator_opened",
        ]
        and gate["require_label_barrier"],
        "measured_street_fit": bool(target["ledger"]["fits_measured_street"])
        == gate["require_measured_street_fit"],
        "conservative_street_fit": bool(
            target["ledger"]["fits_conservative_street"]
        )
        == gate["require_conservative_street_fit"],
        "blueprint_external_emission": (
            target["actual_emitted_policy_sha256"]
            == target["restricted_blueprint_policy_sha256"]
            and target["candidate_policies_emitted"] == 0
        )
        == gate["require_blueprint_external_emission"],
        "single_new_strategy_label": (
            target["new_strategy_quality_labels_generated"] == 1
        )
        == gate["require_single_new_strategy_label"],
        "no_population_claim": (strategy_population_claim is None)
        == gate["require_no_population_claim"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": bool(
            _v1._finite_tree(target)
            and _v1._finite_tree(fallback)
            and _v1._finite_tree(comparison)
        )
        == gate["require_finite"],
    }
    gate_result = finalize_gates(checks)
    promote = bool(
        gate_result["passed"]
        and retreat["shadow_accepted"]
        and comparison["authorizes_fresh_target_replication"]
    )
    result = {
        "schema_version": 2,
        "status": "h32_one_seat_retreat_quality_trial_v2_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "targets": 1,
            "acting_seats": 1,
            "cut_rounds": 1,
            "exact_oracles": 2,
            "new_strategy_quality_labels": 1,
            "sealed_comparator_labels_reused": 1,
            "candidate_policies_emitted": 0,
            "policy_digests_are_diagnostics": True,
        },
        "feature_label_barrier": {
            **barrier.snapshot(),
            "fallback_bytes_sha256_pinned_before_run": True,
            "fallback_json_deserialized_after_retreat_certificate": True,
        },
        "first_oracle_reproduction_checks": first_reproduction,
        "target": target,
        "fallback_comparator": fallback,
        "fallback_identity_checks": fallback_checks,
        "comparison": comparison,
        "aggregate": {
            "retreat_nash_conv": certificate["nash_conv"],
            "retreat_exact_positive_value": retreat["exact_positive_value"],
            "fallback_nash_conv": fallback["nash_conv"],
            "fallback_exact_positive_value": fallback["exact_positive_value"],
            "value_difference": comparison["value_difference"],
            "value_rate_ratio": comparison["value_rate_ratio"],
            "retreat_minimum_cap_slack": certificate["minimum_cap_slack"],
            "measured_live_ms": target["ledger"]["measured_live_ms"],
            "conservative_live_ms": target["ledger"]["conservative_live_ms"],
            "authorize_fresh_target_replication": promote,
        },
        **gate_result,
        "decision": (
            "authorize_preregistered_fresh_target_retreat_replication"
            if promote
            else "retain_one_step_31_block_fallback_and_reject_fresh_retreat_replication"
            if gate_result["passed"]
            else "reject_retreat_quality_v2_execution"
        ),
        "actual_emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_quality_claim": (
            "single_retained_target_shadow_exact_value_only"
            if gate_result["passed"]
            else None
        ),
        "strategy_population_claim": strategy_population_claim,
        "total_seconds": total_seconds,
        "limitations": [
            (
                "This is one known retained target selected for the preceding optimizer "
                "gate, not fresh transfer evidence."
            ),
            (
                "The candidate is frozen by algorithmic and numerical identity; policy "
                "byte digests are reassociation diagnostics only."
            ),
            (
                "The retreat certificate authorizes shadow comparison only; actual external "
                "emission remains the immutable blueprint."
            ),
            (
                "No safety composition, multi-seat, cross-street, population, deployment, "
                "or broad poker-strength claim is made."
            ),
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_one_seat_retreat_quality_trial_v2(args.config, args.output)
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
