"""Additive semantic-identity successor to the frozen resident-CFR audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from .h32_resident_cfr_audit import run_h32_resident_cfr_audit


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-resident-cfr-audit-v2.json"
_OUTPUT = _ROOT / "experiments" / "results" / "h32-resident-cfr-audit-v2.json"
_V1_RESULT = _ROOT / "experiments" / "results" / "h32-resident-cfr-audit-v1.json"
_V1_CONFIG = _ROOT / "experiments" / "configs" / "h32-resident-cfr-audit-v1.json"
_V1_IMPLEMENTATION = _ROOT / "src" / "pontius" / "h32_resident_cfr_audit.py"
_V1_DECISION = (
    _ROOT
    / "docs"
    / "decisions"
    / "ADR-0118-resident-cfr-wins-mechanically-but-byte-identity-fails.md"
)
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "expected_v1_result_sha256",
    "expected_v1_config_sha256",
    "expected_v1_implementation_sha256",
    "expected_v1_decision_sha256",
    "expected_audit_implementation_sha256",
    "rerun_protocol",
    "cross_run_identity_contract",
    "preserved_digest_semantics",
    "gates",
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def parse_h32_resident_cfr_v2_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the one-correction successor protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("resident-CFR v2 config fields differ from ADR-0119")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0118_formal_failure_before_the_single_v2_"
            "rerun"
        ),
        "rerun_protocol": "execute_immutable_v1_workload_and_all_v1_speed_gates",
        "cross_run_identity_contract": (
            "numerical_accumulator_and_policy_identity_at_frozen_tolerances"
        ),
        "preserved_digest_semantics": (
            "report_cross_run_digests_but_require_digests_only_for_stored_object_"
            "and_exact_restart_identity"
        ),
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("resident-CFR v2 protocol differs from ADR-0119")
    sources = {
        "expected_v1_result_sha256": _V1_RESULT,
        "expected_v1_config_sha256": _V1_CONFIG,
        "expected_v1_implementation_sha256": _V1_IMPLEMENTATION,
        "expected_v1_decision_sha256": _V1_DECISION,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"resident-CFR v2 source hash mismatch for {field}")
    expected_gates = {
        "require_v1_formal_failure": True,
        "require_v1_only_cross_run_digest_gate_failed": True,
        "expected_target_rows": 4,
        "expected_checkpoint_comparisons": 8,
        "maximum_legacy_teacher_regret_error": 1e-12,
        "maximum_legacy_teacher_strategy_sum_error": 1e-12,
        "maximum_resident_legacy_regret_error": 1e-9,
        "maximum_resident_legacy_strategy_sum_error": 1e-9,
        "maximum_resident_legacy_policy_probability_error": 1e-9,
        "maximum_resident_legacy_policy_mean_tv": 1e-10,
        "minimum_each_target_two_step_marginal_speedup": 1.5,
        "minimum_each_target_one_step_cache_charged_speedup": 1.2,
        "minimum_each_target_two_step_cache_charged_speedup": 1.5,
        "maximum_total_audit_seconds": 1200.0,
    }
    if config["gates"] != expected_gates:
        raise ValueError("resident-CFR v2 gates differ from ADR-0119")
    return {**config, "gates": dict(config["gates"])}


def run_h32_resident_cfr_v2_audit(config: dict[str, Any]) -> dict[str, Any]:
    """Rerun v1 unchanged and apply only the frozen semantic correction."""

    parsed = parse_h32_resident_cfr_v2_config(config)
    v1_result = json.loads(_V1_RESULT.read_text(encoding="utf-8"))
    v1_config = json.loads(_V1_CONFIG.read_text(encoding="utf-8"))
    failed_v1 = tuple(
        key
        for key, value in v1_result["gates"].items()
        if key != "passed" and not bool(value)
    )
    started = time.perf_counter()
    rerun = run_h32_resident_cfr_audit(v1_config)
    total_seconds = time.perf_counter() - started

    comparisons = [
        row
        for target in rerun["targets"]
        for row in target["correctness"]["checkpoint_rows"]
    ]
    old_relevant_gates = tuple(
        value
        for key, value in rerun["gates"].items()
        if key not in ("passed", "legacy_teacher_state_digest_identity")
    )
    gates_config = parsed["gates"]
    gates = {
        "v1_formal_failure": (not bool(v1_result["gates"]["passed"]))
        == gates_config["require_v1_formal_failure"],
        "v1_only_cross_run_digest_gate_failed": (
            failed_v1 == ("legacy_teacher_state_digest_identity",)
        )
        == gates_config["require_v1_only_cross_run_digest_gate_failed"],
        "immutable_v1_relevant_gates": all(old_relevant_gates),
        "target_rows": len(rerun["targets"]) == gates_config["expected_target_rows"],
        "checkpoint_comparisons": len(comparisons)
        == gates_config["expected_checkpoint_comparisons"],
        "legacy_teacher_regret_error": rerun["correctness"][
            "maximum_legacy_teacher_regret_error"
        ]
        <= gates_config["maximum_legacy_teacher_regret_error"],
        "legacy_teacher_strategy_sum_error": rerun["correctness"][
            "maximum_legacy_teacher_strategy_sum_error"
        ]
        <= gates_config["maximum_legacy_teacher_strategy_sum_error"],
        "resident_legacy_regret_error": rerun["correctness"][
            "maximum_resident_legacy_regret_error"
        ]
        <= gates_config["maximum_resident_legacy_regret_error"],
        "resident_legacy_strategy_sum_error": rerun["correctness"][
            "maximum_resident_legacy_strategy_sum_error"
        ]
        <= gates_config["maximum_resident_legacy_strategy_sum_error"],
        "resident_legacy_policy_probability_error": rerun["correctness"][
            "maximum_resident_legacy_policy_probability_error"
        ]
        <= gates_config["maximum_resident_legacy_policy_probability_error"],
        "resident_legacy_policy_mean_tv": rerun["correctness"][
            "maximum_resident_legacy_policy_mean_tv"
        ]
        <= gates_config["maximum_resident_legacy_policy_mean_tv"],
        "each_target_two_step_marginal_speedup": min(
            target["economics"]["two_step_marginal_speedup"]
            for target in rerun["targets"]
        )
        >= gates_config["minimum_each_target_two_step_marginal_speedup"],
        "each_target_one_step_cache_charged_speedup": min(
            target["economics"]["one_step_cache_charged_speedup"]
            for target in rerun["targets"]
        )
        >= gates_config["minimum_each_target_one_step_cache_charged_speedup"],
        "each_target_two_step_cache_charged_speedup": min(
            target["economics"]["two_step_cache_charged_speedup"]
            for target in rerun["targets"]
        )
        >= gates_config["minimum_each_target_two_step_cache_charged_speedup"],
        "total_audit_seconds": total_seconds
        <= gates_config["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())
    return {
        "schema_version": 2,
        "status": "frozen_successor_audit_executed",
        "experiment_type": "h32_resident_leaf_adjoint_cfr_semantic_identity",
        "config": config,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {
            "v1_result": _sha256(_V1_RESULT),
            "v1_config": _sha256(_V1_CONFIG),
            "v1_implementation": _sha256(_V1_IMPLEMENTATION),
            "v1_decision": _sha256(_V1_DECISION),
        },
        "v1_failed_gates": failed_v1,
        "cross_run_digest_diagnostic": {
            "matching_state_digests": rerun["correctness"][
                "legacy_teacher_state_digest_identities"
            ],
            "checkpoint_comparisons": len(comparisons),
        },
        "correctness": rerun["correctness"],
        "economics": rerun["economics"],
        "small_axis_negative_control": rerun["small_axis_negative_control"],
        "rerun": rerun,
        "timing": {"total_seconds": total_seconds},
        "gates": gates,
        "limitations": [
            "The v2 protocol was frozen after observing v1's digest-only formal failure.",
            "All workload, numerical, resource, and speed gates execute through immutable v1 code.",
            "Cross-run digests remain reported but are not treated as floating semantic identity.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    arguments = parser.parse_args()
    config = json.loads(arguments.config.read_text(encoding="utf-8"))
    result = run_h32_resident_cfr_v2_audit(config)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(arguments.output), "gates": result["gates"]}))


if __name__ == "__main__":
    main()
