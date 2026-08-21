"""Memory-schema corrected wrapper for the retained affine selector replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from . import h32_retained_affine_selector_cascade_replay as v1


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments/configs/h32-retained-affine-selector-cascade-replay-v2.json"
)
_OUTPUT = (
    _ROOT
    / "experiments/results/h32-retained-affine-selector-cascade-replay-v2.json"
)
_V1_ADR = (
    _ROOT
    / "docs/decisions/ADR-0199-preregister-retained-affine-selector-cascade-replay.md"
)
_REJECTION_ADR = (
    _ROOT
    / "docs/decisions/ADR-0200-selector-replay-v1-rejects-on-final-memory-schema-key.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_retained_affine_selector_cascade_replay_v2.py"

_PATHS = {
    "expected_v1_config_sha256": v1._CONFIG,
    "expected_v1_implementation_sha256": v1._IMPLEMENTATION,
    "expected_v1_control_test_sha256": v1._TEST,
    "expected_v1_decision_sha256": _V1_ADR,
    "expected_rejection_decision_sha256": _REJECTION_ADR,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required corrected selector-replay input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_retained_affine_selector_cascade_v2_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate ADR-0201's sole memory-snapshot schema correction."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "correction_scope",
        "replay_scope",
        "outcome_policy",
    }
    if set(config) != fields:
        raise ValueError("corrected selector replay fields differ from ADR-0201")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0200_before_corrected_selector_replay"
        ),
        "correction_scope": (
            "add_gpu_physical_free_bytes_as_in_memory_alias_of_the_existing_"
            "gpu_free_bytes_snapshot_field_only"
        ),
        "replay_scope": (
            "reuse_adr0199_targets_features_label_barrier_candidate_strata_"
            "capacity_scoring_controls_gates_and_blueprint_emission_unchanged"
        ),
        "outcome_policy": (
            "no_partial_v1_state_or_metric_is_reused_and_every_feature_is_"
            "recomputed_before_the_single_semantic_label_join"
        ),
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("corrected selector replay workload differs from ADR-0201")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"corrected selector replay source mismatch: {field}")
    v1_config = json.loads(v1._CONFIG.read_text(encoding="utf-8"))
    base = v1.parse_h32_retained_affine_selector_cascade_config(v1_config)
    return {**config, "v1_base": base}


def _memory_snapshot_alias(
    original: Callable[[Any], dict[str, int]],
) -> Callable[[Any], dict[str, int]]:
    """Add only the physical-free spelling expected by the frozen v1 reader."""

    def corrected(cp: Any) -> dict[str, int]:
        source = original(cp)
        if set(source) != {"gpu_pool_total_bytes", "gpu_free_bytes"}:
            raise ValueError("corrected selector replay received the wrong memory schema")
        return {**source, "gpu_physical_free_bytes": int(source["gpu_free_bytes"])}

    return corrected


def run_h32_retained_affine_selector_cascade_v2_replay(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Rerun ADR-0199 with only the exact in-memory snapshot alias."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    parse_h32_retained_affine_selector_cascade_v2_config(config)
    original_snapshot = v1._memory_snapshot
    v1._memory_snapshot = _memory_snapshot_alias(original_snapshot)
    try:
        result = v1.run_h32_retained_affine_selector_cascade_replay(
            v1._CONFIG,
            output_path,
        )
    finally:
        v1._memory_snapshot = original_snapshot

    result["schema_version"] = 2
    result["status"] = (
        "corrected_h32_retained_affine_selector_cascade_replay_executed"
    )
    result["config_sha256"] = _sha256(config_path)
    result["implementation_sha256"] = _sha256(_IMPLEMENTATION)
    result["correction"] = {
        "failed_v1_result_artifact_absent": True,
        "v1_config_sha256": _sha256(v1._CONFIG),
        "v1_implementation_sha256": _sha256(v1._IMPLEMENTATION),
        "v1_control_test_sha256": _sha256(v1._TEST),
        "memory_schema_before": ["gpu_pool_total_bytes", "gpu_free_bytes"],
        "memory_schema_alias": (
            "gpu_physical_free_bytes_equals_gpu_free_bytes"
        ),
        "scientific_protocol_changed": False,
        "feature_or_label_field_changed": False,
        "capacity_or_scoring_rule_changed": False,
        "outcome_gate_changed": False,
    }
    result["methodology"]["corrected_memory_schema_alias_only"] = True
    result["decision"] = (
        "accept_corrected_retained_affine_selector_cascade_replay"
        if result["passed"]
        else "reject_corrected_retained_affine_selector_cascade_replay"
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
    result = run_h32_retained_affine_selector_cascade_v2_replay(
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
