"""Four-field memory-schema correction for the retained affine selector replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from . import h32_retained_affine_selector_cascade_replay as v1
from . import h32_retained_affine_selector_cascade_replay_v2 as v2


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments/configs/h32-retained-affine-selector-cascade-replay-v3.json"
)
_OUTPUT = (
    _ROOT
    / "experiments/results/h32-retained-affine-selector-cascade-replay-v3.json"
)
_V1_ADR = (
    _ROOT
    / "docs/decisions/ADR-0199-preregister-retained-affine-selector-cascade-replay.md"
)
_V1_REJECTION_ADR = (
    _ROOT
    / "docs/decisions/ADR-0200-selector-replay-v1-rejects-on-final-memory-schema-key.md"
)
_V2_ADR = (
    _ROOT
    / "docs/decisions/ADR-0201-preregister-memory-schema-corrected-selector-replay.md"
)
_V2_REJECTION_ADR = (
    _ROOT
    / "docs/decisions/ADR-0202-corrected-selector-replay-v2-rejects-on-overstrict-schema-guard.md"
)
_MEMORY_HELPER = _ROOT / "src/pontius/h32_fresh_union_value_audit.py"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_retained_affine_selector_cascade_replay_v3.py"

_PATHS = {
    "expected_v1_config_sha256": v1._CONFIG,
    "expected_v1_implementation_sha256": v1._IMPLEMENTATION,
    "expected_v1_control_test_sha256": v1._TEST,
    "expected_v1_decision_sha256": _V1_ADR,
    "expected_v1_rejection_decision_sha256": _V1_REJECTION_ADR,
    "expected_v2_config_sha256": v2._CONFIG,
    "expected_v2_implementation_sha256": v2._IMPLEMENTATION,
    "expected_v2_control_test_sha256": v2._TEST,
    "expected_v2_decision_sha256": _V2_ADR,
    "expected_v2_rejection_decision_sha256": _V2_REJECTION_ADR,
    "expected_memory_helper_sha256": _MEMORY_HELPER,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_SOURCE_SCHEMA = {
    "gpu_free_bytes",
    "gpu_total_bytes",
    "gpu_pool_used_bytes",
    "gpu_pool_total_bytes",
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required final selector-replay input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_retained_affine_selector_cascade_v3_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate ADR-0203's literal four-field schema correction."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "source_memory_schema",
        "correction_scope",
        "replay_scope",
        "outcome_policy",
    }
    if set(config) != fields:
        raise ValueError("final corrected selector replay fields differ from ADR-0203")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0202_before_final_corrected_selector_replay"
        ),
        "source_memory_schema": sorted(_SOURCE_SCHEMA),
        "correction_scope": (
            "preserve_the_exact_four_field_memory_snapshot_and_add_only_"
            "gpu_physical_free_bytes_as_an_alias_of_gpu_free_bytes"
        ),
        "replay_scope": (
            "reuse_adr0199_targets_features_label_barrier_candidate_strata_"
            "capacity_scoring_controls_gates_and_blueprint_emission_unchanged"
        ),
        "outcome_policy": (
            "final_schema_correction_with_no_partial_state_reuse_and_no_"
            "further_wrapper_if_any_schema_or_scientific_gate_fails"
        ),
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("final corrected selector replay workload differs from ADR-0203")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"final corrected selector replay source mismatch: {field}")
    v1_config = json.loads(v1._CONFIG.read_text(encoding="utf-8"))
    base = v1.parse_h32_retained_affine_selector_cascade_config(v1_config)
    return {**config, "v1_base": base}


def _memory_snapshot_alias(
    original: Callable[[Any], dict[str, int]],
) -> Callable[[Any], dict[str, int]]:
    """Preserve the exact four fields and add the one frozen alias."""

    def corrected(cp: Any) -> dict[str, int]:
        source = original(cp)
        if set(source) != _SOURCE_SCHEMA:
            raise ValueError("final selector replay received the wrong memory schema")
        return {**source, "gpu_physical_free_bytes": int(source["gpu_free_bytes"])}

    return corrected


def run_h32_retained_affine_selector_cascade_v3_replay(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Rerun ADR-0199 with only the exact four-field snapshot alias."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    parse_h32_retained_affine_selector_cascade_v3_config(config)
    original_snapshot = v1._memory_snapshot
    v1._memory_snapshot = _memory_snapshot_alias(original_snapshot)
    try:
        result = v1.run_h32_retained_affine_selector_cascade_replay(
            v1._CONFIG,
            output_path,
        )
    finally:
        v1._memory_snapshot = original_snapshot

    result["schema_version"] = 3
    result["status"] = (
        "final_corrected_h32_retained_affine_selector_cascade_replay_executed"
    )
    result["config_sha256"] = _sha256(config_path)
    result["implementation_sha256"] = _sha256(_IMPLEMENTATION)
    result["correction"] = {
        "v1_result_artifact_absent": True,
        "v2_result_artifact_absent": True,
        "v1_config_sha256": _sha256(v1._CONFIG),
        "v1_implementation_sha256": _sha256(v1._IMPLEMENTATION),
        "v2_config_sha256": _sha256(v2._CONFIG),
        "v2_implementation_sha256": _sha256(v2._IMPLEMENTATION),
        "source_memory_schema": sorted(_SOURCE_SCHEMA),
        "memory_schema_alias": "gpu_physical_free_bytes_equals_gpu_free_bytes",
        "original_fields_and_values_preserved": True,
        "scientific_protocol_changed": False,
        "feature_or_label_field_changed": False,
        "capacity_or_scoring_rule_changed": False,
        "outcome_gate_changed": False,
    }
    result["methodology"]["final_four_field_memory_schema_alias_only"] = True
    result["decision"] = (
        "accept_final_corrected_retained_affine_selector_cascade_replay"
        if result["passed"]
        else "reject_final_corrected_retained_affine_selector_cascade_replay"
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
    result = run_h32_retained_affine_selector_cascade_v3_replay(
        args.config, args.output
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "aggregate": result["aggregate"],
                "scoring": result["scoring"]["cascade_by_candidate_set"],
                "correction": result["correction"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
