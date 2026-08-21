"""One-correction successor to the frozen h32 action-width quality audit."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Mapping

from . import h32_action_width_quality_audit as v1


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-action-width-quality-v2.json"
_OUTPUT = _ROOT / "experiments" / "results" / "h32-action-width-quality-v2.json"
_V1_RESULT = _ROOT / "experiments" / "results" / "h32-action-width-quality-v1.json"
_V1_CONFIG = _ROOT / "experiments" / "configs" / "h32-action-width-quality-v1.json"
_V1_IMPLEMENTATION = _ROOT / "src" / "pontius" / "h32_action_width_quality_audit.py"
_V1_DECISION = (
    _ROOT
    / "docs"
    / "decisions"
    / "ADR-0135-h32-action-width-audit-fails-target-descriptor-gate.md"
)
_PARENT = _ROOT / "experiments" / "results" / "fresh-h32-strategy-transfer-audit-v1.json"
_IMPLEMENTATION = Path(__file__)
_CONTROL_TEST = _ROOT / "tests" / "test_h32_action_width_quality_audit_v2.py"

_COMMON_CONSTRUCTION_FIELDS = frozenset(
    {
        "shift",
        "likelihood_minimum",
        "likelihood_maximum",
        "likelihood_mean",
        "positive_likelihoods",
        "hand_axes_identity",
        "tie_rule",
    }
)
_CONSTRUCTION_FIELDS_BY_SHIFT = {
    "local_blocker_seat5_x2": _COMMON_CONSTRUCTION_FIELDS
    | {
        "selected_seat",
        "selected_hand_index",
        "selected_hand",
        "opponent_axis_card_overlap_count",
    },
    "all_seat_strength_1_to2": _COMMON_CONSTRUCTION_FIELDS
    | {"distinct_strength_levels_by_seat"},
}
_PARENT_MEASUREMENT_FIELDS = frozenset(
    {
        "source_partition",
        "target_partition",
        "target_to_source_partition_ratio",
        "marginal_total_variations",
        "mean_marginal_total_variation",
        "maximum_marginal_total_variation",
        "marginal_measurement_ms",
    }
)

_CONFIG_FIELDS = {
    "evidence_stage",
    "expected_v1_result_sha256",
    "expected_v1_config_sha256",
    "expected_v1_implementation_sha256",
    "expected_v1_decision_sha256",
    "expected_parent_sha256",
    "expected_audit_implementation_sha256",
    "expected_control_test_sha256",
    "rerun_protocol",
    "target_identity_contract",
    "known_v1_outcome",
    "strategy_claim_policy",
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


def parse_h32_action_width_quality_v2_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate the single target-identity correction frozen by ADR-0136."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("h32 action-width v2 config fields differ from ADR-0136")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0135_failure_and_observed_abstentions_"
            "before_the_single_v2_rerun"
        ),
        "rerun_protocol": (
            "execute_immutable_v1_workload_with_only_projected_target_"
            "descriptor_identity"
        ),
        "target_identity_contract": (
            "exact_belief_digest_hand_axes_shift_specific_field_set_and_"
            "parent_core_projection"
        ),
        "known_v1_outcome": (
            "both_arms_abstained_on_all_four_targets_with_zero_selected_"
            "reduction"
        ),
        "strategy_claim_policy": (
            "top_level_claim_remains_null_regardless_of_arm_outcome"
        ),
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("h32 action-width v2 protocol differs from ADR-0136")
    sources = {
        "expected_v1_result_sha256": _V1_RESULT,
        "expected_v1_config_sha256": _V1_CONFIG,
        "expected_v1_implementation_sha256": _V1_IMPLEMENTATION,
        "expected_v1_decision_sha256": _V1_DECISION,
        "expected_parent_sha256": _PARENT,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
        "expected_control_test_sha256": _CONTROL_TEST,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"h32 action-width v2 source hash mismatch: {field}")
    expected_gates = {
        "require_v1_formal_failure": True,
        "expected_v1_failed_gates": ["target_identity"],
        "expected_target_rows": 4,
        "require_v1_other_gates": True,
        "require_exact_construction_field_sets": True,
        "require_exact_parent_measurement_field_sets": True,
        "require_exact_parent_core_projection": True,
        "require_exact_belief_digest": True,
        "require_hand_axes_identity": True,
        "require_immutable_v1_workload": True,
        "require_rerun_v1_all_gates": True,
        "require_outcome_neutrality": True,
        "maximum_total_successor_seconds": 3600.0,
    }
    if config["gates"] != expected_gates:
        raise ValueError("h32 action-width v2 gates differ from ADR-0136")
    return {**config, "gates": dict(config["gates"])}


def _parent_target(
    parent: Mapping[str, Any], family: str, shift: str
) -> Mapping[str, Any]:
    return next(
        row
        for row in parent["targets"]
        if row["range_family"] == family and row["target_shift"] == shift
    )


def project_parent_construction_descriptor(
    expected: Mapping[str, Any],
    *,
    shift: str,
) -> dict[str, Any]:
    """Project an augmented ADR-0113 descriptor onto its frozen core schema."""

    if shift not in _CONSTRUCTION_FIELDS_BY_SHIFT:
        raise ValueError("unknown h32 action-width target shift")
    fields = _CONSTRUCTION_FIELDS_BY_SHIFT[shift]
    descriptor = expected["target_descriptor"]
    missing = fields - set(descriptor)
    if missing:
        raise ValueError(f"parent target descriptor omits core fields: {sorted(missing)}")
    return {field: descriptor[field] for field in sorted(fields)}


def target_identity_diagnostics(
    *,
    descriptor: Mapping[str, Any],
    target_belief_sha256: str,
    hands_by_player_identity: bool,
    expected: Mapping[str, Any],
    shift: str,
) -> dict[str, Any]:
    """Evaluate the exact successor identity contract without measured fields."""

    fields = _CONSTRUCTION_FIELDS_BY_SHIFT.get(shift, frozenset())
    parent_descriptor = expected["target_descriptor"]
    projection = (
        project_parent_construction_descriptor(expected, shift=shift)
        if fields
        else {}
    )
    construction_field_set_identity = set(descriptor) == fields
    parent_field_set_identity = set(parent_descriptor) == (
        fields | _PARENT_MEASUREMENT_FIELDS
    )
    parent_core_projection_identity = dict(descriptor) == projection
    belief_digest_identity = (
        target_belief_sha256 == expected["target_belief_sha256"]
    )
    hand_axes_identity = (
        bool(hands_by_player_identity)
        and descriptor.get("hand_axes_identity") is True
        and projection.get("hand_axes_identity") is True
    )
    passed = all(
        (
            construction_field_set_identity,
            parent_field_set_identity,
            parent_core_projection_identity,
            belief_digest_identity,
            hand_axes_identity,
        )
    )
    return {
        "range_family": expected["range_family"],
        "target_shift": shift,
        "construction_fields": sorted(fields),
        "parent_measurement_fields": sorted(_PARENT_MEASUREMENT_FIELDS),
        "construction_field_set_identity": construction_field_set_identity,
        "parent_field_set_identity": parent_field_set_identity,
        "parent_core_projection_identity": parent_core_projection_identity,
        "belief_digest_identity": belief_digest_identity,
        "hand_axes_identity": hand_axes_identity,
        "passed": passed,
    }


def _projecting_parent_target(
    original: Any,
    parent: Mapping[str, Any],
    family: str,
    shift: str,
) -> dict[str, Any]:
    expected = copy.deepcopy(original(parent, family, shift))
    diagnostics = target_identity_diagnostics(
        descriptor=project_parent_construction_descriptor(expected, shift=shift),
        target_belief_sha256=expected["target_belief_sha256"],
        hands_by_player_identity=True,
        expected=expected,
        shift=shift,
    )
    if not diagnostics["passed"]:
        raise ValueError("frozen parent target does not satisfy v2 identity schema")
    expected["target_descriptor"] = project_parent_construction_descriptor(
        expected,
        shift=shift,
    )
    return expected


def run_h32_action_width_quality_v2_audit(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Rerun immutable v1 with only its false-negative identity predicate repaired."""

    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_action_width_quality_v2_config(config)
    v1_result = json.loads(_V1_RESULT.read_text(encoding="utf-8"))
    parent = json.loads(_PARENT.read_text(encoding="utf-8"))
    v1_failed_gates = tuple(
        key for key, value in v1_result["gate_results"].items() if not bool(value)
    )

    original_parent_target = v1._parent_target

    def corrected_parent_target(
        parent_document: Mapping[str, Any], family: str, shift: str
    ) -> dict[str, Any]:
        return _projecting_parent_target(
            original_parent_target,
            parent_document,
            family,
            shift,
        )

    v1._parent_target = corrected_parent_target
    try:
        rerun = v1.run_h32_action_width_quality_audit(_V1_CONFIG, output_path)
    finally:
        v1._parent_target = original_parent_target

    identity_rows = []
    for target in rerun["targets"]:
        expected = _parent_target(
            parent,
            target["range_family"],
            target["target_shift"],
        )
        identity_rows.append(
            target_identity_diagnostics(
                descriptor=target["target_descriptor"],
                target_belief_sha256=target["target_belief_sha256"],
                hands_by_player_identity=target["target_descriptor"].get(
                    "hand_axes_identity", False
                ),
                expected=expected,
                shift=target["target_shift"],
            )
        )

    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    actual_order = [
        f"{target['range_family']}/{target['target_shift']}"
        for target in rerun["targets"]
    ]
    gate_results = {
        "v1_formal_failure": (not v1_result["passed"])
        == gates["require_v1_formal_failure"],
        "v1_failed_gate_identity": list(v1_failed_gates)
        == gates["expected_v1_failed_gates"],
        "v1_other_gates": all(
            value
            for key, value in v1_result["gate_results"].items()
            if key != "target_identity"
        )
        == gates["require_v1_other_gates"],
        "target_count_and_order": (
            len(identity_rows) == gates["expected_target_rows"]
            and actual_order == list(rerun["config"]["target_order"])
        ),
        "construction_field_sets": all(
            row["construction_field_set_identity"] for row in identity_rows
        )
        == gates["require_exact_construction_field_sets"],
        "parent_measurement_field_sets": all(
            row["parent_field_set_identity"] for row in identity_rows
        )
        == gates["require_exact_parent_measurement_field_sets"],
        "parent_core_projection": all(
            row["parent_core_projection_identity"] for row in identity_rows
        )
        == gates["require_exact_parent_core_projection"],
        "belief_digest_identity": all(
            row["belief_digest_identity"] for row in identity_rows
        )
        == gates["require_exact_belief_digest"],
        "hand_axes_identity": all(row["hand_axes_identity"] for row in identity_rows)
        == gates["require_hand_axes_identity"],
        "immutable_v1_workload": (
            rerun["config_sha256"] == parsed["expected_v1_config_sha256"]
            and rerun["implementation_sha256"]
            == parsed["expected_v1_implementation_sha256"]
        )
        == gates["require_immutable_v1_workload"],
        "rerun_v1_all_gates": (
            rerun["passed"] and all(rerun["gate_results"].values())
        )
        == gates["require_rerun_v1_all_gates"],
        "outcome_neutrality": (
            rerun["aggregate_strategy_outcome"]["outcome_is_not_a_gate"]
            and parsed["strategy_claim_policy"]
            == "top_level_claim_remains_null_regardless_of_arm_outcome"
        )
        == gates["require_outcome_neutrality"],
        "total_successor_wall_time": total_seconds
        <= gates["maximum_total_successor_seconds"],
    }
    passed = all(gate_results.values())
    result = {
        "schema_version": 2,
        "status": "frozen_h32_action_width_target_identity_successor_executed",
        "experiment_type": (
            "h32_common_game_wall_clock_matched_action_width_target_identity_"
            "successor"
        ),
        "config": config,
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {
            "v1_result": _sha256(_V1_RESULT),
            "v1_config": _sha256(_V1_CONFIG),
            "v1_implementation": _sha256(_V1_IMPLEMENTATION),
            "v1_decision": _sha256(_V1_DECISION),
            "parent": _sha256(_PARENT),
            "control_test": _sha256(_CONTROL_TEST),
        },
        "v1_failed_gates": list(v1_failed_gates),
        "known_v1_outcome": parsed["known_v1_outcome"],
        "target_identity_rows": identity_rows,
        "aggregate_strategy_outcome": rerun["aggregate_strategy_outcome"],
        "gate_results": gate_results,
        "passed": passed,
        "decision": (
            "accept_target_identity_repair_without_action_width_ranking"
            if passed
            else "reject_action_width_successor_mechanism"
        ),
        "strategy_quality_claim": None,
        "rerun": rerun,
        "timing": {"total_seconds": total_seconds},
        "limitations": [
            "The v2 protocol was frozen after v1's all-abstention outcome was observed.",
            (
                "Only the structurally false target-descriptor equality predicate "
                "changes; immutable v1 performs every h2 control, h32 arm, deadline, "
                "and exact verification again."
            ),
            (
                "The top-level successor makes no strategy-quality ranking regardless "
                "of the rerun outcome."
            ),
            (
                "One board, two generated range families, and four constructed target "
                "beliefs do not establish population transfer."
            ),
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
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
    result = run_h32_action_width_quality_v2_audit(
        arguments.config,
        arguments.output,
    )
    outcome = result["aggregate_strategy_outcome"]
    print(
        "h32 action-width target-identity successor: "
        f"passed={result['passed']}, "
        f"two_minus_one={outcome['two_minus_one_selected_normalized_reduction']:.12g}, "
        f"wall={result['timing']['total_seconds']:.3f}s"
    )


if __name__ == "__main__":
    main()
