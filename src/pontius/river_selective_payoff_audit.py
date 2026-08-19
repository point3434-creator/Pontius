"""Audit the narrow-versus-searched payoff-span selector denominator."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .reporting import environment_metadata
from .river_selective_screen import run_selective_width_screen

_CONFIG_FIELDS = {
    "evidence_stage",
    "source_artifact",
    "source_artifact_sha256",
    "source_config_sha256",
    "selector_rule",
    "selector_rule_sha256",
    "original_screen_artifact",
    "original_screen_artifact_sha256",
    "independent_wide_span_artifact",
    "independent_wide_span_artifact_sha256",
    "expected_groups",
    "expected_contexts",
    "expected_targets",
    "old_span_field",
    "pot_field",
    "correction_formula",
    "mutated_fields",
    "gates",
}
_GATE_FIELDS = {
    "maximum_independent_span_error",
    "maximum_original_quality_reproduction_error",
    "maximum_nonspan_field_mutations",
    "minimum_distinct_old_to_corrected_ratios",
}
_FORMULA = (
    "pot + 2 * max(pot * maximum_bet_fraction, "
    "pot * maximum_raise_to_fraction)"
)


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _validate_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "payoff-span audit fields do not match the frozen schema: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    if config["evidence_stage"] != "revealed_development_measurement_bug_audit":
        raise ValueError("payoff-span audit must remain a revealed development diagnostic")

    paths = {}
    for name in (
        "source_artifact",
        "selector_rule",
        "original_screen_artifact",
        "independent_wide_span_artifact",
    ):
        value = str(config[name])
        if not value or Path(value).is_absolute():
            raise ValueError(f"{name} must be a workspace-relative path")
        paths[name] = value
    hashes = {}
    for name in (
        "source_artifact_sha256",
        "source_config_sha256",
        "selector_rule_sha256",
        "original_screen_artifact_sha256",
        "independent_wide_span_artifact_sha256",
    ):
        value = str(config[name])
        if not _is_sha256(value):
            raise ValueError(f"{name} must be a lowercase SHA-256")
        hashes[name] = value

    expected_groups = int(config["expected_groups"])
    expected_contexts = int(config["expected_contexts"])
    expected_targets = int(config["expected_targets"])
    if min(expected_groups, expected_contexts, expected_targets) <= 0:
        raise ValueError("expected audit counts must be positive")
    old_span_field = str(config["old_span_field"])
    pot_field = str(config["pot_field"])
    formula = str(config["correction_formula"])
    mutated_fields = tuple(str(value) for value in config["mutated_fields"])
    if (
        old_span_field != "target_payoff_span"
        or pot_field != "target_pot"
        or formula != _FORMULA
        or mutated_fields
        != ("targets[*].boundary_online_features.target_payoff_span",)
    ):
        raise ValueError("payoff-span correction scope is frozen by ADR-0048")

    raw_gates = config["gates"]
    if not isinstance(raw_gates, dict) or set(raw_gates) != _GATE_FIELDS:
        raise ValueError("payoff-span audit gates do not match ADR-0048")
    gates = {name: float(value) for name, value in raw_gates.items()}
    if any(not math.isfinite(value) or value < 0.0 for value in gates.values()):
        raise ValueError("payoff-span audit gates must be finite and nonnegative")
    if gates["maximum_independent_span_error"] > 1e-12:
        raise ValueError("independent span error exceeds the frozen exactness contract")
    if gates["maximum_original_quality_reproduction_error"] > 1e-12:
        raise ValueError("quality reproduction error exceeds the frozen contract")
    if gates["maximum_nonspan_field_mutations"] != 0.0:
        raise ValueError("the correction cannot authorize nonspan mutations")
    if gates["minimum_distinct_old_to_corrected_ratios"] < 2.0:
        raise ValueError("the audit must prove the ratio is not globally constant")

    return {
        "evidence_stage": str(config["evidence_stage"]),
        **paths,
        **hashes,
        "expected_groups": expected_groups,
        "expected_contexts": expected_contexts,
        "expected_targets": expected_targets,
        "old_span_field": old_span_field,
        "pot_field": pot_field,
        "correction_formula": formula,
        "mutated_fields": mutated_fields,
        "gates": gates,
    }


def searched_payoff_span(
    pot: float,
    bet_pot_fractions: tuple[float, ...],
    raise_to_pot_fractions: tuple[float, ...],
) -> float:
    if not math.isfinite(pot) or pot <= 0.0:
        raise ValueError("pot must be finite and positive")
    fractions = (*bet_pot_fractions, *raise_to_pot_fractions)
    if not fractions or any(not math.isfinite(value) or value <= 0.0 for value in fractions):
        raise ValueError("action fractions must be finite, positive, and nonempty")
    maximum = pot * max(fractions)
    return pot + 2.0 * maximum


def _read_frozen(
    root: Path,
    relative: str,
    expected_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = (root / relative).resolve()
    if root.resolve() not in path.parents:
        raise ValueError("frozen artifact resolves outside the workspace")
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_sha256:
        raise ValueError(f"frozen artifact hash mismatch for {relative}")
    return json.loads(payload), {
        "path": str(path),
        "sha256": digest,
        "bytes": len(payload),
    }


def _wide_span_index(artifact: dict[str, Any]) -> dict[tuple[str, str], float]:
    by_target: dict[tuple[str, str], list[float]] = {}
    for row in artifact.get("records", []):
        key = (str(row["context_id"]), str(row["target_name"]))
        by_target.setdefault(key, []).append(float(row["payoff_span"]))
    result = {}
    for key, values in by_target.items():
        if len(values) != 2 or max(values) - min(values) > 1e-12:
            raise ValueError(f"independent wide spans disagree for {key!r}")
        result[key] = values[0]
    return result


def _difference_paths(
    first: object,
    second: object,
    path: str = "",
) -> list[str]:
    if type(first) is not type(second):
        return [path]
    if isinstance(first, dict):
        first_dict = first
        second_dict = second
        assert isinstance(second_dict, dict)
        if set(first_dict) != set(second_dict):
            return [path]
        result = []
        for key in sorted(first_dict):
            child = f"{path}.{key}" if path else str(key)
            result.extend(_difference_paths(first_dict[key], second_dict[key], child))
        return result
    if isinstance(first, list):
        second_list = second
        assert isinstance(second_list, list)
        if len(first) != len(second_list):
            return [path]
        result = []
        for index, (left, right) in enumerate(zip(first, second_list, strict=True)):
            result.extend(_difference_paths(left, right, f"{path}[{index}]"))
        return result
    return [] if first == second else [path]


def _quality_signature(screen: dict[str, Any]) -> dict[str, Any]:
    fixed = screen["fixed_b3r2"]
    selected = screen["cross_validated_selection"]
    selected_metrics = selected["selected_metrics"]
    leaderboard = {
        str(row["candidate_id"]): {
            "raw_reduction": float(row["aggregate"]["raw_reduction"]),
            "normalized_reduction": float(row["aggregate"]["normalized_reduction"]),
            "selection_counts": dict(row["aggregate"]["selection_counts"]),
            "state_visits": int(row["aggregate"]["state_visits"]),
        }
        for row in screen["leaderboard"]
    }
    return {
        "fixed": {
            "raw_reduction": float(fixed["raw_reduction"]),
            "normalized_reduction": float(fixed["normalized_reduction"]),
            "selection_counts": dict(fixed["selection_counts"]),
            "state_visits": int(fixed["state_visits"]),
        },
        "selected": {
            "candidate_id": str(selected["selected_candidate_id"]),
            "raw_reduction": float(selected_metrics["raw_reduction"]),
            "normalized_reduction": float(selected_metrics["normalized_reduction"]),
            "selection_counts": dict(selected_metrics["selection_counts"]),
            "state_visits": int(selected_metrics["state_visits"]),
        },
        "leaderboard": leaderboard,
        "gates": dict(screen["selection_gates"]["results"]),
    }


def _signature_error(first: dict[str, Any], second: dict[str, Any]) -> tuple[float, bool]:
    errors = []
    for section in ("fixed", "selected"):
        for field in ("raw_reduction", "normalized_reduction"):
            errors.append(abs(float(first[section][field]) - float(second[section][field])))
    for candidate_id in set(first["leaderboard"]) | set(second["leaderboard"]):
        if candidate_id not in first["leaderboard"] or candidate_id not in second["leaderboard"]:
            return math.inf, False
        for field in ("raw_reduction", "normalized_reduction"):
            errors.append(
                abs(
                    float(first["leaderboard"][candidate_id][field])
                    - float(second["leaderboard"][candidate_id][field])
                )
            )
    structural_identity = (
        first["fixed"]["selection_counts"] == second["fixed"]["selection_counts"]
        and first["fixed"]["state_visits"] == second["fixed"]["state_visits"]
        and first["selected"]["candidate_id"] == second["selected"]["candidate_id"]
        and first["selected"]["selection_counts"]
        == second["selected"]["selection_counts"]
        and first["selected"]["state_visits"] == second["selected"]["state_visits"]
        and first["gates"] == second["gates"]
        and all(
            first["leaderboard"][candidate_id]["selection_counts"]
            == second["leaderboard"][candidate_id]["selection_counts"]
            and first["leaderboard"][candidate_id]["state_visits"]
            == second["leaderboard"][candidate_id]["state_visits"]
            for candidate_id in first["leaderboard"]
        )
    )
    return max(errors, default=0.0), structural_identity


def run_payoff_span_correction_audit(
    config: dict[str, Any],
    *,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    parsed = _validate_config(config)
    root = Path.cwd() if workspace_root is None else workspace_root
    source, source_provenance = _read_frozen(
        root,
        parsed["source_artifact"],
        parsed["source_artifact_sha256"],
    )
    rule, rule_provenance = _read_frozen(
        root,
        parsed["selector_rule"],
        parsed["selector_rule_sha256"],
    )
    original_screen, original_provenance = _read_frozen(
        root,
        parsed["original_screen_artifact"],
        parsed["original_screen_artifact_sha256"],
    )
    independent, independent_provenance = _read_frozen(
        root,
        parsed["independent_wide_span_artifact"],
        parsed["independent_wide_span_artifact_sha256"],
    )
    if source.get("config_sha256") != parsed["source_config_sha256"]:
        raise ValueError("selective source config SHA-256 does not match")
    counts = source.get("counts", {})
    if (
        int(counts.get("groups", -1)) != parsed["expected_groups"]
        or int(counts.get("contexts", -1)) != parsed["expected_contexts"]
        or int(counts.get("targets", -1)) != parsed["expected_targets"]
    ):
        raise ValueError("selective source counts do not match the frozen audit")

    original_rerun = run_selective_width_screen(source, rule)
    reproduced_signature = _quality_signature(original_rerun)
    frozen_signature = _quality_signature(original_screen)
    reproduction_error, reproduction_structure_identity = _signature_error(
        reproduced_signature,
        frozen_signature,
    )

    config_record = source["config"]
    bets = tuple(float(value) for value in config_record["bet_pot_fractions"])
    raises = tuple(float(value) for value in config_record["raise_to_pot_fractions"])
    wide_spans = _wide_span_index(independent)
    if len(wide_spans) != parsed["expected_targets"]:
        raise ValueError("independent artifact has the wrong target count")

    corrected = copy.deepcopy(source)
    span_records = []
    independent_errors = []
    for target in corrected["targets"]:
        key = (str(target["context_id"]), str(target["target_name"]))
        features = target["boundary_online_features"]
        old_span = float(features[parsed["old_span_field"]])
        derived_span = searched_payoff_span(
            float(features[parsed["pot_field"]]),
            bets,
            raises,
        )
        independent_span = wide_spans[key]
        independent_error = abs(derived_span - independent_span)
        independent_errors.append(independent_error)
        features[parsed["old_span_field"]] = derived_span
        span_records.append(
            {
                "context_id": key[0],
                "target_name": key[1],
                "old_narrow_payoff_span": old_span,
                "corrected_searched_payoff_span": derived_span,
                "independent_wide_payoff_span": independent_span,
                "independent_span_error": independent_error,
                "corrected_to_old_ratio": derived_span / old_span,
            }
        )

    differences = _difference_paths(source, corrected)
    expected_paths = {
        f"targets[{index}].boundary_online_features.{parsed['old_span_field']}"
        for index in range(len(source["targets"]))
    }
    unexpected_differences = sorted(set(differences) - expected_paths)
    missing_differences = sorted(expected_paths - set(differences))
    corrected_screen = run_selective_width_screen(corrected, rule)

    ratios = sorted({round(float(row["corrected_to_old_ratio"]), 12) for row in span_records})
    requirements = parsed["gates"]
    integrity_results = {
        "independent_wide_span_identity": max(independent_errors, default=0.0)
        <= requirements["maximum_independent_span_error"],
        "original_quality_reproduction": reproduction_error
        <= requirements["maximum_original_quality_reproduction_error"]
        and reproduction_structure_identity,
        "only_declared_span_field_mutated": len(unexpected_differences)
        <= requirements["maximum_nonspan_field_mutations"]
        and not missing_differences,
        "old_to_corrected_ratio_is_not_global": len(ratios)
        >= requirements["minimum_distinct_old_to_corrected_ratios"],
        "schema_counts_unchanged": (
            corrected_screen["counts"] == original_rerun["counts"]
            and corrected_screen["counts"]["groups"] == parsed["expected_groups"]
            and corrected_screen["counts"]["targets"] == parsed["expected_targets"]
        ),
    }
    selected = str(
        corrected_screen["cross_validated_selection"]["selected_candidate_id"]
    )
    corrected_passed = bool(corrected_screen["selection_gates"]["passed"])
    fresh_replication_warranted = selected != "fixed_b3r2" and corrected_passed
    next_decision = (
        "preregister_fresh_group_separated_development_replication"
        if fresh_replication_warranted
        else "retain_full_b3r2_and_close_current_adaptive_width_family"
    )

    return {
        "schema_version": 1,
        "experiment_type": "river_selective_payoff_span_correction_audit",
        "status": "revealed_development_measurement_bug_audit",
        "config": config,
        "config_sha256": hashlib.sha256(
            json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "environment": environment_metadata(),
        "provenance": {
            "source": source_provenance,
            "selector_rule": rule_provenance,
            "original_screen": original_provenance,
            "independent_wide_span": independent_provenance,
        },
        "counts": {
            "groups": parsed["expected_groups"],
            "contexts": parsed["expected_contexts"],
            "targets": parsed["expected_targets"],
            "mutated_paths": len(differences),
            "unexpected_mutated_paths": len(unexpected_differences),
            "distinct_old_to_corrected_ratios": len(ratios),
        },
        "correction": {
            "formula": parsed["correction_formula"],
            "bet_pot_fractions": list(bets),
            "raise_to_pot_fractions": list(raises),
            "maximum_independent_span_error": max(independent_errors, default=0.0),
            "old_to_corrected_ratios": ratios,
            "minimum_ratio": min(ratios),
            "maximum_ratio": max(ratios),
            "unexpected_difference_paths": unexpected_differences,
            "missing_expected_difference_paths": missing_differences,
        },
        "original_reproduction": {
            "maximum_quality_error": reproduction_error,
            "structure_identity": reproduction_structure_identity,
            "signature": reproduced_signature,
        },
        "integrity_gates": {
            "requirements": requirements,
            "results": integrity_results,
            "passed": all(integrity_results.values()),
        },
        "corrected_screen": corrected_screen,
        "decision": {
            "corrected_selected_candidate_id": selected,
            "corrected_original_gates_passed": corrected_passed,
            "fresh_replication_warranted": fresh_replication_warranted,
            "next_decision": next_decision,
            "selection_or_deployment_authorized": False,
        },
        "span_records": span_records,
        "interpretation_limits": {
            "source_labels_were_revealed": True,
            "selector_family_was_not_retuned": True,
            "fresh_replication_required_for_any_adaptive_rule": True,
            "reserved_validation_or_test_authorized": False,
            "native_specialization_authorized": False,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_payoff_span_correction_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "payoff-span correction audit: "
        f"integrity={result['integrity_gates']['passed']}, "
        f"selected={result['decision']['corrected_selected_candidate_id']}, "
        f"screen_passed={result['decision']['corrected_original_gates_passed']}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
