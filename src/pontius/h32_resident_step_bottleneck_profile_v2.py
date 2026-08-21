"""Schema-only successor to the rejected ADR-0195 bottleneck profile."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from . import h32_resident_step_bottleneck_profile as v1


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments/configs/h32-resident-step-bottleneck-profile-v2.json"
)
_OUTPUT = (
    _ROOT / "experiments/results/h32-resident-step-bottleneck-profile-v2.json"
)
_V1_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0195-preregister-read-only-h32-resident-step-bottleneck-profile.md"
)
_REJECTION = (
    _ROOT
    / "docs/decisions/ADR-0196-resident-step-profile-v1-rejects-before-replay-on-parent-pass-key.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_resident_step_bottleneck_profile_v2.py"

_PATHS = {
    "expected_v1_config_sha256": v1._CONFIG,
    "expected_v1_implementation_sha256": v1._IMPLEMENTATION,
    "expected_v1_control_test_sha256": v1._TEST,
    "expected_v1_decision_sha256": _V1_DECISION,
    "expected_rejection_decision_sha256": _REJECTION,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required bottleneck-profile-v2 input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_resident_step_bottleneck_v2_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate ADR-0197's parent-schema-only correction."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "correction_scope",
        "replay_scope",
        "outcome_policy",
    }
    if set(config) != fields:
        raise ValueError("resident-step bottleneck v2 fields differ from ADR-0197")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0196_before_any_resident_step_timing_"
            "with_all_v1_measurements_still_unobserved"
        ),
        "correction_scope": (
            "add_top_level_source_passed_as_in_memory_gates_passed_alias_"
            "for_the_exact_source_blueprint_artifact_only"
        ),
        "replay_scope": (
            "reuse_adr0195_config_runner_helpers_targets_restarts_timing_buckets_"
            "counterfactuals_numerical_gates_and_resource_gates_unchanged"
        ),
        "outcome_policy": (
            "classification_remains_report_only_and_no_strategy_quality_label_is_run"
        ),
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("resident-step bottleneck v2 workload differs from ADR-0197")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"resident-step bottleneck v2 source mismatch: {field}")
    base_config = json.loads(v1._CONFIG.read_text(encoding="utf-8"))
    base = v1.parse_h32_resident_step_bottleneck_config(base_config)
    return {**base, "v1_base": base, "v2": dict(config)}


def _source_pass_alias(payload: dict[str, Any]) -> dict[str, Any]:
    """Add exactly the key v1 expected without mutating the retained artifact."""

    expected_status = "frozen_h32_fresh_panel_source_blueprints_executed"
    if payload.get("status") != expected_status or "source_rows" not in payload:
        raise ValueError("source pass alias was requested for the wrong artifact")
    if "passed" not in payload or not isinstance(payload["passed"], bool):
        raise ValueError("source pass alias requires the top-level boolean")
    if "gates" in payload:
        raise ValueError("source pass alias refuses an already nested gate schema")
    return {**payload, "gates": {"passed": payload["passed"]}}


def _corrected_loads(
    original: Callable[..., Any],
) -> Callable[..., Any]:
    def loads(value: Any, *args: Any, **kwargs: Any) -> Any:
        payload = original(value, *args, **kwargs)
        if (
            isinstance(payload, dict)
            and payload.get("status")
            == "frozen_h32_fresh_panel_source_blueprints_executed"
            and "source_rows" in payload
        ):
            return _source_pass_alias(payload)
        return payload

    return loads


def run_h32_resident_step_bottleneck_profile_v2(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Run v1 unchanged except for the exact source pass-field alias."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_resident_step_bottleneck_v2_config(config)
    original_loads = v1.json.loads
    v1.json.loads = _corrected_loads(original_loads)
    try:
        result = v1.run_h32_resident_step_bottleneck_profile(
            v1._CONFIG,
            output_path,
        )
    finally:
        v1.json.loads = original_loads

    result["schema_version"] = 2
    result["status"] = "h32_resident_step_bottleneck_profile_v2_executed"
    result["config_sha256"] = _sha256(config_path)
    result["implementation_sha256"] = _sha256(_IMPLEMENTATION)
    result["methodology"]["source_pass_field"] = "top_level_passed"
    result["methodology"]["v1_scientific_protocol_reused_unchanged"] = True
    result["correction"] = {
        "v1_config_sha256": _sha256(v1._CONFIG),
        "v1_implementation_sha256": _sha256(v1._IMPLEMENTATION),
        "v1_control_test_sha256": _sha256(v1._TEST),
        "v1_decision_sha256": _sha256(_V1_DECISION),
        "rejection_decision_sha256": _sha256(_REJECTION),
        "source_artifact_mutated": False,
        "targets_changed": False,
        "restarts_changed": False,
        "timing_buckets_changed": False,
        "gates_changed": False,
        "outcome_branches_changed": False,
    }
    result["decision"] = (
        "accept_corrected_stage_attribution_and_use_dominant_bucket_for_next_engineering_screen"
        if result["passed"]
        else "reject_corrected_stage_attribution"
    )
    result["limitations"].append(
        "The additive v2 wrapper changes only the retained source pass-field schema alias."
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
    arguments = parser.parse_args()
    result = run_h32_resident_step_bottleneck_profile_v2(
        arguments.config,
        arguments.output,
    )
    print(
        json.dumps(
            {
                "output": str(arguments.output),
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
