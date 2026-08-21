"""Numerically corrected warm-start gate for the fresh h32 union audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from . import h32_fresh_union_value_audit as v1
from .h32_warm_search_acceptance_audit import _policy_distance
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-union-value-v2.json"
_OUTPUT = _ROOT / "experiments/results/h32-fresh-union-value-v2.json"
_FAILED = _ROOT / "experiments/results/h32-fresh-union-value-v1.json"
_FAILED_ADR = (
    _ROOT
    / "docs/decisions/ADR-0170-fresh-union-v1-rejected-by-overstrict-warm-digest-gate.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_fresh_union_value_audit_v2.py"

_PATHS = {
    "expected_v1_config_sha256": v1._CONFIG,
    "expected_v1_implementation_sha256": v1._IMPLEMENTATION,
    "expected_v1_control_test_sha256": v1._TEST,
    "expected_failed_result_sha256": _FAILED,
    "expected_failed_decision_sha256": _FAILED_ADR,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required corrected-union input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_fresh_union_value_v2_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate ADR-0171's sole numerical-gate correction."""

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
        raise ValueError("corrected fresh-union fields differ from ADR-0171")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0170_before_corrected_fresh_union_rerun"
        ),
        "correction_scope": (
            "replace_only_exact_warm_policy_digest_gate_with_established_"
            "numerical_probability_and_mean_tv_gates"
        ),
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "require_warm_start_digest_identity": False,
        "rerun_scope": (
            "repeat_complete_v1_two_target_live_union_and_post_ledger_atom_matrix"
        ),
        "outcome_policy": (
            "retain_every_v1_outcome_neutral_gate_and_add_no_outcome_identity_gate"
        ),
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("corrected fresh-union workload differs from ADR-0171")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"corrected fresh-union source mismatch: {field}")
    base_config = json.loads(v1._CONFIG.read_text(encoding="utf-8"))
    base = v1.parse_h32_fresh_union_value_config(base_config)
    return {**config, "base": base}


_WARM_DISTANCES: list[dict[str, float]] = []


class _TrackedResidentSolver(ResidentLeafAdjointPublicTreeCFR):
    def warm_start(
        self,
        blueprint: dict[str, dict[str, float]],
        regret_mass: float,
    ) -> None:
        super().warm_start(blueprint, regret_mass)
        _WARM_DISTANCES.append(_policy_distance(blueprint, self.current_strategy()))


def _target_outcome_signature(target: dict[str, Any]) -> dict[str, Any]:
    """Return decision-level outcomes for diagnostic rerun comparison."""

    return {
        "target": target["target"],
        "deadline_reason": target["deadline_reason"],
        "shadow_selected_candidate_id": target["shadow_selected_candidate_id"],
        "union_outcomes": [
            {
                "candidate_id": row["candidate_id"],
                "complete": row["certificate"]["complete"],
                "stop_reason": row["certificate"]["stop_reason"],
                "stop_seat": row["certificate"]["stop_seat"],
                "usable": row["usable_before_emission_cutoff"],
            }
            for row in target["live_union_rows"]
        ],
        "atomic_outcomes": [
            {
                "acting_seat": row["acting_seat"],
                "complete": row["certificate"]["complete"],
                "stop_reason": row["certificate"]["stop_reason"],
                "stop_seat": row["certificate"]["stop_seat"],
            }
            for row in target["post_ledger_atomic_rows"]
        ],
    }


def _maximum_common_nash_difference(
    first: dict[str, Any], second: dict[str, Any]
) -> float:
    values = []
    first_by_target = {row["target"]: row for row in first["target_rows"]}
    for second_target in second["target_rows"]:
        first_target = first_by_target[second_target["target"]]
        values.append(
            abs(
                float(first_target["blueprint_quality"]["nash_conv"])
                - float(second_target["blueprint_quality"]["nash_conv"])
            )
        )
        for field in ("live_union_rows", "post_ledger_atomic_rows"):
            first_rows = {row["candidate_id"]: row for row in first_target[field]}
            for second_row in second_target[field]:
                first_row = first_rows.get(second_row["candidate_id"])
                if (
                    first_row is None
                    or not first_row["certificate"]["complete"]
                    or not second_row["certificate"]["complete"]
                ):
                    continue
                values.append(
                    abs(
                        float(first_row["certificate"]["quality"]["nash_conv"])
                        - float(
                            second_row["certificate"]["quality"]["nash_conv"]
                        )
                    )
                )
    return max(values, default=0.0)


def run_h32_fresh_union_value_v2_audit(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Rerun v1 exactly while recording accepted numerical warm distances."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_fresh_union_value_v2_config(config)
    failed = json.loads(_FAILED.read_text(encoding="utf-8"))
    _WARM_DISTANCES.clear()
    original_solver = v1.ResidentLeafAdjointPublicTreeCFR
    v1.ResidentLeafAdjointPublicTreeCFR = _TrackedResidentSolver
    try:
        result = v1.run_h32_fresh_union_value_audit(v1._CONFIG, output_path)
    finally:
        v1.ResidentLeafAdjointPublicTreeCFR = original_solver
    if len(_WARM_DISTANCES) != len(result["target_rows"]):
        raise AssertionError("corrected warm-start instrumentation count differs")

    for target, distance in zip(result["target_rows"], _WARM_DISTANCES, strict=True):
        target["warm_start_digest_identity"] = target.pop("warm_start_identity")
        target["warm_start_distance"] = distance
    maximum_probability = max(
        row["maximum_probability_error"] for row in _WARM_DISTANCES
    )
    maximum_mean_tv = max(row["mean_total_variation"] for row in _WARM_DISTANCES)
    result["gates"].pop("warm_start_identity")
    result["gates"]["warm_start_probability_error"] = (
        maximum_probability <= parsed["maximum_warm_start_probability_error"]
    )
    result["gates"]["warm_start_mean_total_variation"] = (
        maximum_mean_tv <= parsed["maximum_warm_start_mean_total_variation"]
    )
    result["gates"]["passed"] = all(
        value for key, value in result["gates"].items() if key != "passed"
    )

    failed_signatures = [
        _target_outcome_signature(row) for row in failed["target_rows"]
    ]
    rerun_signatures = [
        _target_outcome_signature(row) for row in result["target_rows"]
    ]
    result["schema_version"] = 2
    result["status"] = "corrected_h32_fresh_union_value_audit_executed"
    result["config_sha256"] = _sha256(config_path)
    result["implementation_sha256"] = _sha256(_IMPLEMENTATION)
    result["correction"] = {
        "failed_v1_result_sha256": _sha256(_FAILED),
        "reused_v1_config_sha256": _sha256(v1._CONFIG),
        "reused_v1_implementation_sha256": _sha256(v1._IMPLEMENTATION),
        "maximum_warm_start_probability_error": maximum_probability,
        "maximum_warm_start_mean_total_variation": maximum_mean_tv,
        "warm_start_digest_identities": [
            target["warm_start_digest_identity"] for target in result["target_rows"]
        ],
        "scientific_matrix_changed": False,
        "outcome_gates_changed": False,
        "failed_run_decision_signature_identity": (
            failed_signatures == rerun_signatures
        ),
        "maximum_common_complete_nash_conv_difference": (
            _maximum_common_nash_difference(failed, result)
        ),
    }
    result["methodology"]["preregistered"] = True
    result["methodology"]["corrected_gate_only"] = True
    result["decision"] = (
        "accept_corrected_prospective_holdout_measurement"
        if result["gates"]["passed"]
        else "reject_corrected_fresh_union_audit"
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
    result = run_h32_fresh_union_value_v2_audit(args.config, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["gates"]["passed"],
                "aggregate": result["aggregate"],
                "correction": result["correction"],
            },
            indent=2,
        )
    )
    if not result["gates"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
