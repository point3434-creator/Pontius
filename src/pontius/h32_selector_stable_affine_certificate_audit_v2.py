"""Numerically corrected gate for the selector-stable affine h32 audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .evidence_protocol import DEFAULT_GPU_NUMERICAL_IDENTITY
from . import h32_selector_stable_affine_certificate_audit as v1


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments/configs/h32-selector-stable-affine-certificate-v2.json"
)
_OUTPUT = (
    _ROOT / "experiments/results/h32-selector-stable-affine-certificate-v2.json"
)
_FAILED = (
    _ROOT / "experiments/results/h32-selector-stable-affine-certificate-v1.json"
)
_FAILED_ADR = (
    _ROOT
    / "docs/decisions/ADR-0188-selector-stable-affine-v1-rejected-by-forbidden-warm-digest-gate.md"
)
_EVIDENCE_PROTOCOL = _ROOT / "src/pontius/evidence_protocol.py"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_selector_stable_affine_certificate_audit_v2.py"

_PATHS = {
    "expected_v1_config_sha256": v1._CONFIG,
    "expected_v1_implementation_sha256": v1._IMPLEMENTATION,
    "expected_v1_control_test_sha256": v1._TEST,
    "expected_failed_result_sha256": _FAILED,
    "expected_failed_decision_sha256": _FAILED_ADR,
    "expected_evidence_protocol_sha256": _EVIDENCE_PROTOCOL,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required corrected-affine input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_selector_stable_affine_certificate_v2_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate ADR-0189's sole numerical-gate correction."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "correction_scope",
        "maximum_warm_start_probability_error",
        "maximum_warm_start_mean_total_variation",
        "require_warm_start_digest_identity",
        "rerun_scope",
        "outcome_policy",
    }
    if set(config) != fields:
        raise ValueError("corrected selector-stable affine fields differ from ADR-0189")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0188_before_corrected_selector_stable_affine_rerun"
        ),
        "correction_scope": (
            "replace_only_cross_run_warm_policy_digest_gate_with_adr0179_"
            "numerical_probability_and_mean_tv_gates"
        ),
        "maximum_warm_start_probability_error": (
            DEFAULT_GPU_NUMERICAL_IDENTITY.maximum_policy_probability_error
        ),
        "maximum_warm_start_mean_total_variation": (
            DEFAULT_GPU_NUMERICAL_IDENTITY.maximum_policy_mean_information_set_total_variation
        ),
        "require_warm_start_digest_identity": False,
        "rerun_scope": (
            "repeat_complete_v1_six_target_selector_stable_affine_differential"
        ),
        "outcome_policy": (
            "retain_every_v1_outcome_neutral_gate_and_add_no_outcome_identity_gate"
        ),
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("corrected selector-stable affine workload differs from ADR-0189")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"corrected selector-stable affine source mismatch: {field}")
    base_config = json.loads(v1._CONFIG.read_text(encoding="utf-8"))
    base = v1.parse_h32_selector_stable_affine_certificate_config(base_config)
    return {**config, "base": base}


def _decision_signature(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Return discrete scientific outcomes without timing or value labels."""

    signatures = []
    for target in result["target_rows"]:
        signatures.append(
            {
                "target": target["target"],
                "blocks": [
                    {
                        "acting_seat": block["acting_seat"],
                        "public_history": block["public_history"],
                        "direction_policy_sha256": block["direction_policy_sha256"],
                        "complete": block["envelope"]["complete"],
                        "stop_reason": block["envelope"]["stop_reason"],
                        "selected_scale": block["envelope"]["selected_scale"],
                        "selected_direct_complete": (
                            None
                            if block["selected_validation"] is None
                            else block["selected_validation"]["direct"]["complete"]
                        ),
                    }
                    for block in target["block_rows"]
                ],
            }
        )
    return signatures


def _maximum_common_selected_value_difference(
    first: dict[str, Any], second: dict[str, Any]
) -> float:
    """Compare common block values as an ungated reproduction diagnostic."""

    differences = []
    first_targets = {target["target"]: target for target in first["target_rows"]}
    for second_target in second["target_rows"]:
        first_target = first_targets[second_target["target"]]
        first_blocks = {
            (block["acting_seat"], block["public_history"]): block
            for block in first_target["block_rows"]
        }
        for second_block in second_target["block_rows"]:
            key = (second_block["acting_seat"], second_block["public_history"])
            first_block = first_blocks[key]
            differences.append(
                abs(
                    float(first_block["selected_positive_certified_value"])
                    - float(second_block["selected_positive_certified_value"])
                )
            )
    return max(differences, default=0.0)


def run_h32_selector_stable_affine_certificate_v2_audit(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Rerun v1 exactly and replace only its forbidden warm digest gate."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_selector_stable_affine_certificate_v2_config(config)
    failed = json.loads(_FAILED.read_text(encoding="utf-8"))
    result = v1.run_h32_selector_stable_affine_certificate_audit(
        v1._CONFIG,
        output_path,
    )

    distances = [target["warm_start_distance"] for target in result["target_rows"]]
    maximum_probability = max(
        row["maximum_probability_error"] for row in distances
    )
    maximum_mean_tv = max(row["mean_total_variation"] for row in distances)
    digest_identities = [
        target["soft_candidate_policy_sha256"]
        == target["parent_soft_candidate_policy_sha256"]
        for target in result["target_rows"]
    ]

    result["gates"].pop("numerical_warm_start_identity")
    result["gates"]["warm_start_probability_error"] = (
        maximum_probability <= parsed["maximum_warm_start_probability_error"]
    )
    result["gates"]["warm_start_mean_total_variation"] = (
        maximum_mean_tv <= parsed["maximum_warm_start_mean_total_variation"]
    )
    result["gates"]["passed"] = all(
        value for key, value in result["gates"].items() if key != "passed"
    )

    result["schema_version"] = 2
    result["status"] = (
        "corrected_h32_selector_stable_affine_certificate_audit_executed"
    )
    result["config_sha256"] = _sha256(config_path)
    result["implementation_sha256"] = _sha256(_IMPLEMENTATION)
    result["correction"] = {
        "failed_v1_result_sha256": _sha256(_FAILED),
        "reused_v1_config_sha256": _sha256(v1._CONFIG),
        "reused_v1_implementation_sha256": _sha256(v1._IMPLEMENTATION),
        "maximum_warm_start_probability_error": maximum_probability,
        "maximum_warm_start_mean_total_variation": maximum_mean_tv,
        "warm_start_digest_identities": digest_identities,
        "scientific_matrix_changed": False,
        "outcome_gates_changed": False,
        "failed_run_decision_signature_identity": (
            _decision_signature(failed) == _decision_signature(result)
        ),
        "maximum_common_selected_positive_value_difference": (
            _maximum_common_selected_value_difference(failed, result)
        ),
    }
    result["methodology"]["corrected_gate_only"] = True
    result["methodology"]["exact_warm_policy_digests_diagnostic_only"] = True
    result["passed"] = result["gates"]["passed"]
    result["decision"] = (
        "accept_corrected_selector_stable_affine_certificate_differential"
        if result["passed"]
        else "reject_corrected_selector_stable_affine_certificate_differential"
    )
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_selector_stable_affine_certificate_v2_audit(
        args.config,
        args.output,
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "aggregate": result["aggregate"],
                "correction": result["correction"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
