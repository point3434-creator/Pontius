"""Retrospective value-capture accounting over already-frozen h32 atom labels."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/retrospective-atomic-value-capture-v1.json"
_OUTPUT = _ROOT / "experiments/results/retrospective-atomic-value-capture-v1.json"
_ATOMIC = _ROOT / "experiments/results/h32-atomic-response-preflight-v1.json"
_BUNDLE = _ROOT / "experiments/results/h32-policy-delta-verifier-audit-v1.json"
_ACCEPTANCE = _ROOT / "experiments/results/h32-warm-search-acceptance-v1.json"
_SCHEDULER = _ROOT / "experiments/results/h32-atomic-street-scheduler-v1.json"
_IMPLEMENTATION = Path(__file__)

_FIELDS = {
    "evidence_stage",
    "expected_atomic_source_sha256",
    "expected_bundle_source_sha256",
    "expected_acceptance_source_sha256",
    "expected_scheduler_source_sha256",
    "expected_implementation_sha256",
    "bundle_candidate_id",
    "scheduler_capacity_atoms",
    "scheduler_atom_order",
    "value_definition",
    "bounded_oracle",
    "tie_break",
    "gates",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_retrospective_atomic_value_capture_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the reproducible post-hoc analysis contract."""

    if set(config) != _FIELDS:
        raise ValueError("retrospective value-capture fields differ from ADR-0167")
    frozen = {
        "evidence_stage": "retrospective_after_atomic_labels_were_inspected_not_preregistered",
        "bundle_candidate_id": "search_current1",
        "scheduler_capacity_atoms": 2,
        "scheduler_atom_order": [0, 1, 2, 3, 4, 5],
        "value_definition": "positive_blueprint_minus_candidate_nash_conv",
        "bounded_oracle": "best_single_envelope_complete_retained_atom",
        "tie_break": "maximum_value_then_acting_seat",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("retrospective value-capture workload differs from ADR-0167")
    paths = {
        "expected_atomic_source_sha256": _ATOMIC,
        "expected_bundle_source_sha256": _BUNDLE,
        "expected_acceptance_source_sha256": _ACCEPTANCE,
        "expected_scheduler_source_sha256": _SCHEDULER,
        "expected_implementation_sha256": _IMPLEMENTATION,
    }
    for field, path in paths.items():
        if config[field] != _sha256(path):
            raise ValueError(f"retrospective value-capture source mismatch: {field}")
    gates = {
        "expected_target_rows": 4,
        "expected_atom_rows": 24,
        "expected_bundle_rows": 4,
        "expected_new_strategy_quality_labels": 0,
        "require_source_gates": True,
        "require_policy_identity": True,
        "require_finite_accounting": True,
    }
    if config["gates"] != gates:
        raise ValueError("retrospective value-capture gates differ from ADR-0167")
    return config


def _acceptance_target(source: dict[str, Any], family: str, shift: str) -> dict[str, Any]:
    family_row = next(
        row for row in source["family_rows"] if row["range_family"] == family
    )
    return next(row for row in family_row["targets"] if row["target_shift"] == shift)


def _bundle_target(source: dict[str, Any], family: str, shift: str) -> dict[str, Any]:
    family_row = next(
        row for row in source["family_rows"] if row["range_family"] == family
    )
    return next(row for row in family_row["targets"] if row["target_shift"] == shift)


def _positive_reduction(blueprint: float, candidate: float) -> float:
    return max(0.0, blueprint - candidate)


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    return None if denominator <= 0.0 else numerator / denominator


def analyze_retrospective_atomic_value_capture(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Compute descriptive single-atom capture without new evaluations."""

    parsed = parse_retrospective_atomic_value_capture_config(config)
    atomic = json.loads(_ATOMIC.read_text(encoding="utf-8"))
    bundle_source = json.loads(_BUNDLE.read_text(encoding="utf-8"))
    acceptance = json.loads(_ACCEPTANCE.read_text(encoding="utf-8"))
    scheduler = json.loads(_SCHEDULER.read_text(encoding="utf-8"))
    source_gates = all(
        source["gates"]["passed"]
        for source in (atomic, bundle_source, acceptance, scheduler)
    )

    target_rows = []
    policy_identity = True
    for atomic_target in atomic["targets"]:
        family = atomic_target["range_family"]
        shift = atomic_target["target_shift"]
        acceptance_target = _acceptance_target(acceptance, family, shift)
        bundle_target = _bundle_target(bundle_source, family, shift)
        bundle = next(
            row
            for row in bundle_target["live_candidate_rows"]
            if row["candidate_id"] == parsed["bundle_candidate_id"]
        )
        blueprint_nash = float(acceptance_target["blueprint_quality"]["nash_conv"])
        bundle_quality = bundle["quality"]
        bundle_nash = (
            None if bundle_quality is None else float(bundle_quality["nash_conv"])
        )
        policy_identity = policy_identity and (
            atomic_target["blueprint_policy_sha256"]
            == acceptance_target["blueprint_quality"]["policy_sha256"]
            and atomic_target["bundle_policy_sha256"] == bundle["policy_sha256"]
        )
        atom_rows = []
        for atom in atomic_target["atom_rows"]:
            candidate_nash = float(atom["teacher_quality"]["nash_conv"])
            complete = bool(atom["incremental"]["complete"])
            value = _positive_reduction(blueprint_nash, candidate_nash)
            atom_rows.append(
                {
                    "acting_seat": int(atom["acting_seat"]),
                    "policy_sha256": atom["policy_sha256"],
                    "envelope_complete": complete,
                    "stop_reason": atom["incremental"]["stop_reason"],
                    "stop_seat": atom["incremental"]["stop_seat"],
                    "nash_conv": candidate_nash,
                    "positive_certified_value": value if complete else 0.0,
                    "raw_objective_reduction": blueprint_nash - candidate_nash,
                    "certificate_ms": float(atom["incremental"]["wall_ms"]),
                    "response_action_flips": int(
                        atom["incremental"]["response_action_flips"]
                    ),
                }
            )
        admissible = [row for row in atom_rows if row["envelope_complete"]]
        best_single = min(
            admissible,
            key=lambda row: (-row["positive_certified_value"], row["acting_seat"]),
        )
        scheduled = [
            next(row for row in atom_rows if row["acting_seat"] == seat)
            for seat in parsed["scheduler_atom_order"][: parsed["scheduler_capacity_atoms"]]
        ]
        scheduled_admissible = [row for row in scheduled if row["envelope_complete"]]
        scheduled_best = min(
            scheduled_admissible,
            key=lambda row: (-row["positive_certified_value"], row["acting_seat"]),
        )
        bundle_value = (
            _positive_reduction(blueprint_nash, bundle_nash)
            if bool(bundle["complete"]) and bundle_nash is not None
            else 0.0
        )
        admissible_value_sum = math.fsum(
            row["positive_certified_value"] for row in admissible
        )
        atomic_deltas = [row["nash_conv"] - blueprint_nash for row in atom_rows]
        union_interaction_residual = (
            None
            if bundle_nash is None
            else bundle_nash - blueprint_nash - math.fsum(atomic_deltas)
        )
        target_rows.append(
            {
                "range_family": family,
                "target_shift": shift,
                "blueprint_nash_conv": blueprint_nash,
                "bundle": {
                    "candidate_id": bundle["candidate_id"],
                    "policy_sha256": bundle["policy_sha256"],
                    "envelope_complete": bool(bundle["complete"]),
                    "stop_reason": bundle["stop_reason"],
                    "nash_conv": bundle_nash,
                    "exact_quality_label_present": bundle_nash is not None,
                    "positive_certified_value": bundle_value,
                },
                "atom_rows": atom_rows,
                "admissible_atom_count": len(admissible),
                "cap_bound_atom_count": sum(
                    row["stop_reason"] == "blueprint_cap" for row in atom_rows
                ),
                "objective_bound_atom_count": sum(
                    row["stop_reason"] == "objective_lower_bound" for row in atom_rows
                ),
                "bounded_single_atom_oracle": {
                    "acting_seat": best_single["acting_seat"],
                    "positive_certified_value": best_single[
                        "positive_certified_value"
                    ],
                    "certificate_ms": best_single["certificate_ms"],
                },
                "fixed_two_certificate_prefix": {
                    "acting_seats": [row["acting_seat"] for row in scheduled],
                    "admissible_count": len(scheduled_admissible),
                    "best_available_acting_seat": scheduled_best["acting_seat"],
                    "best_available_positive_certified_value": scheduled_best[
                        "positive_certified_value"
                    ],
                    "captured_fraction_of_bounded_single_oracle": _safe_ratio(
                        scheduled_best["positive_certified_value"],
                        best_single["positive_certified_value"],
                    ),
                },
                "interaction_diagnostics": {
                    "sum_admissible_single_atom_values": admissible_value_sum,
                    "best_single_fraction_of_bundle_value": (
                        _safe_ratio(
                            best_single["positive_certified_value"], bundle_value
                        )
                        if bundle_nash is not None
                        else None
                    ),
                    "sum_single_fraction_of_bundle_value": (
                        _safe_ratio(admissible_value_sum, bundle_value)
                        if bundle_nash is not None
                        else None
                    ),
                    "six_atom_union_nash_interaction_residual": (
                        union_interaction_residual
                    ),
                    "bundle_complete_with_cap_bound_constituent": (
                        bool(bundle["complete"])
                        and any(
                            row["stop_reason"] == "blueprint_cap"
                            for row in atom_rows
                        )
                    ),
                },
            }
        )

    all_atoms = [row for target in target_rows for row in target["atom_rows"]]
    accounting_values = [
        value
        for target in target_rows
        for value in (
            target["blueprint_nash_conv"],
            target["bundle"]["nash_conv"],
            target["bundle"]["positive_certified_value"],
            target["bounded_single_atom_oracle"]["positive_certified_value"],
            target["fixed_two_certificate_prefix"][
                "best_available_positive_certified_value"
            ],
            target["interaction_diagnostics"][
                "six_atom_union_nash_interaction_residual"
            ],
        )
        if value is not None
    ]
    finite_accounting = all(math.isfinite(float(value)) for value in accounting_values)
    gates_config = parsed["gates"]
    gates = {
        "source_gates": source_gates == gates_config["require_source_gates"],
        "target_rows": len(target_rows) == gates_config["expected_target_rows"],
        "atom_rows": len(all_atoms) == gates_config["expected_atom_rows"],
        "bundle_rows": len(target_rows) == gates_config["expected_bundle_rows"],
        "zero_new_strategy_quality_labels": gates_config[
            "expected_new_strategy_quality_labels"
        ]
        == 0,
        "policy_identity": policy_identity
        == gates_config["require_policy_identity"],
        "finite_accounting": finite_accounting
        == gates_config["require_finite_accounting"],
    }
    gates["passed"] = all(gates.values())
    fractions = [
        target["fixed_two_certificate_prefix"][
            "captured_fraction_of_bounded_single_oracle"
        ]
        for target in target_rows
    ]
    bundle_fractions = [
        target["interaction_diagnostics"]["best_single_fraction_of_bundle_value"]
        for target in target_rows
        if target["interaction_diagnostics"][
            "best_single_fraction_of_bundle_value"
        ]
        is not None
    ]
    result = {
        "status": "retrospective_atomic_value_capture_executed",
        "methodology": {
            "preregistered": False,
            "reason": "atomic_labels_were_inspected_before_this_analysis_contract_was_frozen",
            "new_solver_calls": 0,
            "new_strategy_quality_labels": 0,
            "oracle_scope": parsed["bounded_oracle"],
            "composition": "forbidden_no_union_label_created",
            "generalization_claim": "none",
        },
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "target_rows": target_rows,
        "aggregate": {
            "target_rows": len(target_rows),
            "atom_rows": len(all_atoms),
            "complete_bundle_rows": sum(
                target["bundle"]["envelope_complete"] for target in target_rows
            ),
            "exact_bundle_quality_rows": sum(
                target["bundle"]["exact_quality_label_present"]
                for target in target_rows
            ),
            "admissible_atom_rows": sum(
                target["admissible_atom_count"] for target in target_rows
            ),
            "cap_bound_atom_rows": sum(
                target["cap_bound_atom_count"] for target in target_rows
            ),
            "objective_bound_atom_rows": sum(
                target["objective_bound_atom_count"] for target in target_rows
            ),
            "bundle_complete_with_cap_bound_constituent_rows": sum(
                target["interaction_diagnostics"][
                    "bundle_complete_with_cap_bound_constituent"
                ]
                for target in target_rows
            ),
            "fixed_two_prefix_capture_fraction": {
                "minimum": min(fractions),
                "maximum": max(fractions),
            },
            "best_single_fraction_of_bundle_value": {
                "minimum": min(bundle_fractions),
                "maximum": max(bundle_fractions),
                "rows": len(bundle_fractions),
            },
            "new_strategy_quality_labels": 0,
        },
        "gates": gates,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = analyze_retrospective_atomic_value_capture(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "gates": result["gates"]}, indent=2))
    if not result["gates"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
