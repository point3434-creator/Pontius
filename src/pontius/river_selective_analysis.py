"""Selection-free analysis for group-separated selective-expansion matrices."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


TOLERANCE = 1e-12
PAID_PROBE_MASK = "b1r1"
PAID_PROBE_BUDGET = 4
FORBIDDEN_FEATURE_FRAGMENTS = (
    "nash",
    "exploit",
    "best_response",
    "future",
    "gain",
    "label",
    "reduction",
    "oracle",
)


def _ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    result = [0.0] * len(values)
    start = 0
    while start < len(values):
        stop = start + 1
        while stop < len(values) and values[order[stop]] == values[order[start]]:
            stop += 1
        rank = (start + stop - 1) / 2.0
        for position in range(start, stop):
            result[order[position]] = rank
        start = stop
    return result


def _spearman(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    ranked_left = _ranks(left)
    ranked_right = _ranks(right)
    left_mean = mean(ranked_left)
    right_mean = mean(ranked_right)
    centered_left = [value - left_mean for value in ranked_left]
    centered_right = [value - right_mean for value in ranked_right]
    denominator = math.sqrt(
        sum(value * value for value in centered_left)
        * sum(value * value for value in centered_right)
    )
    if denominator == 0.0:
        return None
    return sum(
        first * second
        for first, second in zip(centered_left, centered_right, strict=True)
    ) / denominator


def _feature_map(value: object, *, label: str) -> dict[str, float]:
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{label} must be a nonempty feature map")
    result: dict[str, float] = {}
    for raw_name, raw_value in value.items():
        name = str(raw_name)
        lowered = name.lower()
        if any(fragment in lowered for fragment in FORBIDDEN_FEATURE_FRAGMENTS):
            raise ValueError(f"{label} feature {name!r} contains a forbidden fragment")
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            raise ValueError(f"{label} feature {name!r} must be numeric")
        number = float(raw_value)
        if not math.isfinite(number):
            raise ValueError(f"{label} feature {name!r} must be finite")
        result[name] = number
    return result


def _ordered_masks(config: dict[str, Any]) -> list[str]:
    masks = [str(row["name"]) for row in config.get("masks", [])]
    if len(masks) < 2 or len(masks) != len(set(masks)):
        raise ValueError("development artifact must declare unique selective masks")
    return masks


def _target_index(artifact: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for raw in artifact.get("targets", []):
        row = dict(raw)
        key = (str(row["context_id"]), str(row["target_name"]))
        if key in result:
            raise ValueError(f"duplicate target record {key!r}")
        row["boundary_online_features"] = _feature_map(
            row.get("boundary_online_features"),
            label="boundary",
        )
        result[key] = row
    if not result:
        raise ValueError("development artifact has no target records")
    return result


def _build_instance_rows(
    artifact: dict[str, Any],
    *,
    masks: list[str],
    warm: float,
    targets: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for raw in artifact.get("records", []):
        row = dict(raw)
        if float(row["warm_start_multiplier_by_payoff_span"]) != warm:
            raise ValueError("selection-free development analysis requires one fixed warm start")
        key = (
            str(row["context_id"]),
            str(row["target_name"]),
            int(row["full_tree_equivalent_iteration_budget"]),
        )
        mask = str(row["mask_name"])
        if mask not in masks:
            raise ValueError(f"candidate record has unknown mask {mask!r}")
        if mask in grouped[key]:
            raise ValueError(f"duplicate candidate record for {key!r}, mask {mask!r}")
        grouped[key][mask] = row

    result = []
    full_mask = masks[-1]
    for (context_id, target_name, budget), mask_rows in sorted(grouped.items()):
        if set(mask_rows) != set(masks):
            raise ValueError(
                f"instance {(context_id, target_name, budget)!r} does not contain every mask"
            )
        target = targets.get((context_id, target_name))
        if target is None:
            raise ValueError(f"candidate has no target provenance: {(context_id, target_name)!r}")
        reductions = {
            mask: float(mask_rows[mask]["nash_conv_reduction_from_blueprint"])
            for mask in masks
        }
        best_mask = max(masks, key=lambda mask: reductions[mask])
        best_raw = reductions[best_mask]
        full_raw = reductions[full_mask]
        payoff_span = float(
            target["boundary_online_features"].get("target_payoff_span", 1.0)
        )
        if not math.isfinite(payoff_span) or payoff_span <= 0.0:
            raise ValueError("target payoff span must be finite and positive")
        opportunity = max(0.0, best_raw) - max(0.0, full_raw)
        result.append(
            {
                "context_id": context_id,
                "group_id": str(target["group_id"]),
                "family": str(target["family"]),
                "target_name": target_name,
                "target_kind": str(target["target_kind"]),
                "full_tree_equivalent_iteration_budget": budget,
                "payoff_span": payoff_span,
                "reductions_by_mask": reductions,
                "best_raw_mask_name": best_mask,
                "best_raw_mask_reduction": best_raw,
                "full_mask_reduction": full_raw,
                "raw_mask_advantage": best_raw - full_raw,
                "mask_oracle_with_no_op_reduction": max(0.0, best_raw),
                "full_mask_with_no_op_reduction": max(0.0, full_raw),
                "no_op_search_opportunity": opportunity,
                "normalized_raw_mask_advantage": (best_raw - full_raw) / payoff_span,
                "normalized_no_op_search_opportunity": opportunity / payoff_span,
                "oracle_choice": best_mask if best_raw > 0.0 else "no_op",
            }
        )
    if not result:
        raise ValueError("development artifact has no candidate records")
    return result


def _opportunity_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    materialized = list(rows)
    mask_total = sum(float(row["mask_oracle_with_no_op_reduction"]) for row in materialized)
    full_total = sum(float(row["full_mask_with_no_op_reduction"]) for row in materialized)
    opportunity = mask_total - full_total
    choices = Counter(str(row["oracle_choice"]) for row in materialized)
    return {
        "instances": len(materialized),
        "mask_oracle_with_no_op_total_reduction": mask_total,
        "full_mask_with_no_op_total_reduction": full_total,
        "opportunity_uplift": opportunity,
        "relative_opportunity_uplift": opportunity / full_total if full_total > 0.0 else None,
        "positive_instance_fraction": (
            mean(float(row["no_op_search_opportunity"]) > TOLERANCE for row in materialized)
            if materialized
            else None
        ),
        "oracle_choice_counts": dict(sorted(choices.items())),
    }


def _grouped_opportunity(
    rows: list[dict[str, Any]],
    field: str,
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row[field])].append(row)
    return [
        {field: key, **_opportunity_summary(group)}
        for key, group in sorted(groups.items())
    ]


def _fixed_mask_quality_work(
    records: list[dict[str, Any]],
    *,
    masks: list[str],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        grouped[(int(row["full_tree_equivalent_iteration_budget"]), str(row["mask_name"]))].append(
            row
        )
    result = []
    for (budget, mask), rows in sorted(
        grouped.items(), key=lambda item: (item[0][0], masks.index(item[0][1]))
    ):
        reductions = [float(row["nash_conv_reduction_from_blueprint"]) for row in rows]
        visits = sum(int(row["actual_state_visits"]) for row in rows)
        result.append(
            {
                "full_tree_equivalent_iteration_budget": budget,
                "mask_name": mask,
                "instances": len(rows),
                "total_reduction": sum(reductions),
                "total_reduction_with_no_op": sum(max(0.0, value) for value in reductions),
                "mean_reduction": mean(reductions),
                "improvement_fraction": mean(value > TOLERANCE for value in reductions),
                "harm_fraction": mean(value < -TOLERANCE for value in reductions),
                "actual_state_visits": visits,
                "reduction_per_million_state_visits": (
                    sum(reductions) * 1_000_000.0 / visits if visits else None
                ),
                "mean_hot_with_probe_milliseconds": 1000.0
                * mean(float(row["hot_with_probe_feature_seconds"]) for row in rows),
                "mean_cold_exact_leaf_with_probe_milliseconds": 1000.0
                * mean(
                    float(row["cold_exact_leaf_with_probe_feature_seconds"])
                    for row in rows
                ),
            }
        )
    return result


def _leave_one_group_out_fixed_mask(
    primary_rows: list[dict[str, Any]],
    *,
    masks: list[str],
) -> dict[str, Any]:
    groups = sorted({str(row["group_id"]) for row in primary_rows})
    folds = []
    for held_out_group in groups:
        training = [row for row in primary_rows if row["group_id"] != held_out_group]
        held_out = [row for row in primary_rows if row["group_id"] == held_out_group]
        if not training or not held_out:
            raise ValueError("leave-one-group-out transfer requires at least two nonempty groups")
        training_totals = {
            mask: sum(max(0.0, float(row["reductions_by_mask"][mask])) for row in training)
            for mask in masks
        }
        selected = max(masks, key=lambda mask: training_totals[mask])
        selected_total = sum(
            max(0.0, float(row["reductions_by_mask"][selected])) for row in held_out
        )
        full_total = sum(float(row["full_mask_with_no_op_reduction"]) for row in held_out)
        oracle_total = sum(
            float(row["mask_oracle_with_no_op_reduction"]) for row in held_out
        )
        folds.append(
            {
                "held_out_group_id": held_out_group,
                "training_instances": len(training),
                "held_out_instances": len(held_out),
                "training_no_op_reduction_by_mask": training_totals,
                "selected_mask_name": selected,
                "held_out_selected_with_no_op_reduction": selected_total,
                "held_out_full_with_no_op_reduction": full_total,
                "held_out_oracle_with_no_op_reduction": oracle_total,
                "held_out_selected_minus_full": selected_total - full_total,
                "held_out_oracle_minus_selected": oracle_total - selected_total,
            }
        )
    selected_total = sum(float(row["held_out_selected_with_no_op_reduction"]) for row in folds)
    full_total = sum(float(row["held_out_full_with_no_op_reduction"]) for row in folds)
    oracle_total = sum(float(row["held_out_oracle_with_no_op_reduction"]) for row in folds)
    available = oracle_total - full_total
    captured = selected_total - full_total
    return {
        "folds": folds,
        "selected_mask_counts": dict(
            sorted(Counter(str(row["selected_mask_name"]) for row in folds).items())
        ),
        "held_out_selected_with_no_op_total_reduction": selected_total,
        "held_out_full_with_no_op_total_reduction": full_total,
        "held_out_oracle_with_no_op_total_reduction": oracle_total,
        "held_out_selected_minus_full": captured,
        "relative_uplift_over_full": captured / full_total if full_total > 0.0 else None,
        "available_oracle_opportunity_captured_fraction": (
            captured / available if available > 0.0 else None
        ),
        "selection_authorized": False,
    }


def _feature_rank_table(
    rows: list[dict[str, Any]],
    feature_maps: list[dict[str, float]],
) -> dict[str, Any]:
    if len(rows) != len(feature_maps) or not rows:
        raise ValueError("feature rank table requires one feature map per instance")
    names = set(feature_maps[0])
    if any(set(features) != names for features in feature_maps[1:]):
        raise ValueError("feature maps must have identical schemas")
    target_names = (
        "normalized_no_op_search_opportunity",
        "normalized_raw_mask_advantage",
    )
    diagnostics = []
    groups = sorted({str(row["group_id"]) for row in rows})
    for name in sorted(names):
        values = [features[name] for features in feature_maps]
        target_correlations = {}
        for target_name in target_names:
            targets = [float(row[target_name]) for row in rows]
            overall = _spearman(values, targets)
            leave_one_group_out = []
            for held_out in groups:
                included = [index for index, row in enumerate(rows) if row["group_id"] != held_out]
                correlation = _spearman(
                    [values[index] for index in included],
                    [targets[index] for index in included],
                )
                leave_one_group_out.append(
                    {"held_out_group_id": held_out, "spearman": correlation}
                )
            finite_loo = [
                float(row["spearman"])
                for row in leave_one_group_out
                if row["spearman"] is not None
            ]
            target_correlations[target_name] = {
                "spearman": overall,
                "leave_one_group_out": leave_one_group_out,
                "leave_one_group_out_minimum": min(finite_loo) if finite_loo else None,
                "leave_one_group_out_maximum": max(finite_loo) if finite_loo else None,
                "leave_one_group_out_same_sign_fraction": (
                    mean(value * float(overall) > 0.0 for value in finite_loo)
                    if finite_loo and overall not in (None, 0.0)
                    else None
                ),
            }
        diagnostics.append({"feature": name, "targets": target_correlations})

    rankings = {}
    for target_name in target_names:
        available = [
            row
            for row in diagnostics
            if row["targets"][target_name]["spearman"] is not None
        ]
        rankings[target_name] = [
            {
                "feature": row["feature"],
                **row["targets"][target_name],
            }
            for row in sorted(
                available,
                key=lambda row: (
                    -abs(float(row["targets"][target_name]["spearman"])),
                    str(row["feature"]),
                ),
            )
        ]
    return {
        "instances": len(rows),
        "groups": len(groups),
        "feature_count": len(names),
        "label_definitions": {
            "normalized_no_op_search_opportunity": (
                "(max(0, best_mask_reduction) - max(0, full_mask_reduction)) / payoff_span"
            ),
            "normalized_raw_mask_advantage": (
                "(best_mask_reduction - full_mask_reduction) / payoff_span"
            ),
        },
        "ranked_by_absolute_spearman": rankings,
        "selection_authorized": False,
    }


def _validate_development_artifact(artifact: dict[str, Any]) -> tuple[list[str], float, int]:
    if artifact.get("experiment_type") != "river_selective_expansion_development_matrix":
        raise ValueError("analysis requires a selective-expansion development matrix")
    if artifact.get("evidence_stage") != "group_separated_development":
        raise ValueError("analysis requires group-separated development evidence")
    if artifact.get("selection_authorized") is not False:
        raise ValueError("input artifact must explicitly prohibit selection")
    config = artifact.get("config")
    if not isinstance(config, dict):
        raise ValueError("development artifact has no configuration")
    warms = config.get("warm_start_multipliers_by_payoff_span")
    if not isinstance(warms, list) or len(warms) != 1:
        raise ValueError("development matrix must freeze exactly one warm start")
    masks = _ordered_masks(config)
    primary_budget = int(config["gates"]["primary_full_tree_equivalent_iteration_budget"])
    budgets = {int(value) for value in config["full_tree_equivalent_iteration_budgets"]}
    if PAID_PROBE_BUDGET not in budgets or primary_budget not in budgets:
        raise ValueError("artifact is missing the frozen probe or primary budget")
    if PAID_PROBE_MASK not in masks:
        raise ValueError("artifact is missing the frozen paid-probe mask")
    return masks, float(warms[0]), primary_budget


def analyze_selective_expansion_development(
    artifact: dict[str, Any],
    *,
    input_sha256: str | None = None,
) -> dict[str, Any]:
    """Analyze opportunity and stability without fitting a deployable selector."""

    masks, warm, primary_budget = _validate_development_artifact(artifact)
    targets = _target_index(artifact)
    instances = _build_instance_rows(
        artifact,
        masks=masks,
        warm=warm,
        targets=targets,
    )
    budgets = sorted({int(row["full_tree_equivalent_iteration_budget"]) for row in instances})
    target_keys = set(targets)
    for budget in budgets:
        budget_keys = {
            (str(row["context_id"]), str(row["target_name"]))
            for row in instances
            if int(row["full_tree_equivalent_iteration_budget"]) == budget
        }
        if budget_keys != target_keys:
            raise ValueError(f"budget {budget} does not cover every target exactly once")
    primary_rows = [
        row
        for row in instances
        if int(row["full_tree_equivalent_iteration_budget"]) == primary_budget
    ]
    boundary_maps = [
        targets[(str(row["context_id"]), str(row["target_name"]))][
            "boundary_online_features"
        ]
        for row in primary_rows
    ]

    candidate_records = list(artifact["records"])
    probe_index: dict[tuple[str, str], dict[str, float]] = {}
    paid_probe_records: list[dict[str, Any]] = []
    for raw in candidate_records:
        if (
            str(raw["mask_name"]) == PAID_PROBE_MASK
            and int(raw["full_tree_equivalent_iteration_budget"]) == PAID_PROBE_BUDGET
        ):
            key = (str(raw["context_id"]), str(raw["target_name"]))
            if key in probe_index:
                raise ValueError(f"duplicate paid probe for {key!r}")
            probe_index[key] = _feature_map(
                raw.get("solver_probe_features"),
                label="solver probe",
            )
            paid_probe_records.append(raw)
    if set(probe_index) != target_keys:
        raise ValueError("frozen paid probe does not cover every target exactly once")
    probe_maps = [
        probe_index[(str(row["context_id"]), str(row["target_name"]))]
        for row in primary_rows
    ]

    per_budget = []
    for budget in budgets:
        rows = [
            row
            for row in instances
            if int(row["full_tree_equivalent_iteration_budget"]) == budget
        ]
        per_budget.append(
            {
                "full_tree_equivalent_iteration_budget": budget,
                **_opportunity_summary(rows),
            }
        )

    primary_summary = _opportunity_summary(primary_rows)
    primary_summary.update(
        {
            "warm_start_multiplier_by_payoff_span": warm,
            "full_tree_equivalent_iteration_budget": primary_budget,
            "groups": len({str(row["group_id"]) for row in primary_rows}),
            "positive_group_fraction": mean(
                float(row["opportunity_uplift"]) > TOLERANCE
                for row in _grouped_opportunity(primary_rows, "group_id")
            ),
        }
    )

    boundary_seconds = [float(row["boundary_feature_seconds"]) for row in targets.values()]
    paid_probe_end_to_end_seconds = []
    for row in paid_probe_records:
        target = targets[(str(row["context_id"]), str(row["target_name"]))]
        paid_probe_end_to_end_seconds.append(
            float(target["boundary_feature_seconds"])
            + float(row["cold_exact_leaf_with_probe_feature_seconds"])
        )

    return {
        "analysis_type": "river_selective_expansion_selection_free_analysis",
        "evidence_stage": "group_separated_development",
        "input_sha256": input_sha256,
        "input_config_sha256": artifact.get("config_sha256"),
        "selection_authorized": False,
        "selector_fitted": False,
        "promotion_decision_authorized": False,
        "frozen_probe": {
            "mask_name": PAID_PROBE_MASK,
            "full_tree_equivalent_iteration_budget": PAID_PROBE_BUDGET,
            "feature_cost_is_charged_in_input": True,
        },
        "primary_budget": primary_budget,
        "counts": {
            "groups": len({str(row["group_id"]) for row in primary_rows}),
            "primary_instances": len(primary_rows),
            "all_budget_instances": len(instances),
            "candidate_records": len(artifact["records"]),
        },
        "input_gates": artifact.get("gates"),
        "primary_opportunity": primary_summary,
        "opportunity_by_budget": per_budget,
        "primary_opportunity_by_group": _grouped_opportunity(primary_rows, "group_id"),
        "primary_opportunity_by_family": _grouped_opportunity(primary_rows, "family"),
        "primary_opportunity_by_target_kind": _grouped_opportunity(
            primary_rows, "target_kind"
        ),
        "fixed_mask_quality_work": _fixed_mask_quality_work(
            candidate_records, masks=masks
        ),
        "leave_one_group_out_best_fixed_mask": _leave_one_group_out_fixed_mask(
            primary_rows,
            masks=masks,
        ),
        "boundary_feature_ranks": _feature_rank_table(
            primary_rows,
            boundary_maps,
        ),
        "paid_probe_feature_ranks": _feature_rank_table(
            primary_rows,
            probe_maps,
        ),
        "online_feature_cost_controls": {
            "python_reference_timing_only": True,
            "boundary_feature_instances": len(boundary_seconds),
            "mean_boundary_feature_milliseconds": 1000.0 * mean(boundary_seconds),
            "maximum_boundary_feature_milliseconds": 1000.0 * max(boundary_seconds),
            "paid_probe_instances": len(paid_probe_records),
            "mean_paid_probe_hot_with_features_milliseconds": 1000.0
            * mean(
                float(row["hot_with_probe_feature_seconds"])
                for row in paid_probe_records
            ),
            "mean_paid_probe_cold_leaf_with_features_milliseconds": 1000.0
            * mean(
                float(row["cold_exact_leaf_with_probe_feature_seconds"])
                for row in paid_probe_records
            ),
            "mean_boundary_plus_cold_paid_probe_milliseconds": 1000.0
            * mean(paid_probe_end_to_end_seconds),
        },
        "interpretation_limits": {
            "exact_labels_are_used_only_as_analysis_targets": True,
            "rank_correlations_are_univariate_and_unfitted": True,
            "leave_one_group_out_control_is_not_a_contextual_selector": True,
            "same_artifact_selector_evaluation_is_prohibited": True,
            "development_only": True,
            "multiplayer_claim_authorized": False,
            "native_latency_claim_authorized": False,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    payload = args.artifact.read_bytes()
    artifact = json.loads(payload)
    result = analyze_selective_expansion_development(
        artifact,
        input_sha256=hashlib.sha256(payload).hexdigest(),
    )
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(rendered)
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "selection_authorized": False}))


if __name__ == "__main__":
    main()
