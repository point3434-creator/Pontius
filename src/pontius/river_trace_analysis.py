"""Compact diagnostics for exact river opportunity trace artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from math import sqrt
from pathlib import Path
from statistics import mean
from typing import Any

from .river_opportunity import _allocation_oracles

TOLERANCE = 1e-12
TARGET_DESCRIPTIONS = {
    "normalized_future_reduction": (
        "future_best_additional_reduction / payoff_span"
    ),
    "state_visit_efficiency": (
        "best future payoff-normalized reduction per thousand state visits"
    ),
    "millisecond_efficiency": (
        "best future payoff-normalized reduction per measured solver millisecond"
    ),
}


def _ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    start = 0
    while start < len(values):
        stop = start + 1
        while stop < len(values) and values[order[stop]] == values[order[start]]:
            stop += 1
        average_rank = (start + stop - 1) / 2.0
        for index in range(start, stop):
            ranks[order[index]] = average_rank
        start = stop
    return ranks


def _pearson(first: list[float], second: list[float]) -> float | None:
    if len(first) != len(second) or len(first) < 2:
        return None
    first_mean = mean(first)
    second_mean = mean(second)
    centered_first = [value - first_mean for value in first]
    centered_second = [value - second_mean for value in second]
    denominator = sqrt(
        sum(value * value for value in centered_first)
        * sum(value * value for value in centered_second)
    )
    if denominator == 0.0:
        return None
    return sum(
        left * right
        for left, right in zip(centered_first, centered_second, strict=True)
    ) / denominator


def _spearman(first: list[float], second: list[float]) -> float | None:
    return _pearson(_ranks(first), _ranks(second))


def _payoff_span(record: dict[str, Any]) -> float:
    features = record["online_features"]
    return float(
        features.get(
            "payoff_span",
            float(features["pot"]) + 2.0 * float(features["bet_size"]),
        )
    )


def _normalized_future_target(record: dict[str, Any]) -> float:
    return (
        float(record["labels"]["future_best_additional_reduction"])
        / _payoff_span(record)
    )


def _target_value(record: dict[str, Any], target: str) -> float:
    if target == "normalized_future_reduction":
        return _normalized_future_target(record)
    label = {
        "state_visit_efficiency": (
            "best_future_normalized_reduction_per_thousand_state_visits"
        ),
        "millisecond_efficiency": (
            "best_future_normalized_reduction_per_solver_millisecond"
        ),
    }.get(target)
    if label is None:
        raise ValueError(f"unknown primary target {target!r}")
    if label not in record["labels"]:
        raise ValueError(
            f"primary target {target!r} is unavailable in this trace artifact"
        )
    return float(record["labels"][label])


def _local_regret_diagnostics(records: list[dict[str, Any]]) -> dict[str, Any]:
    labeled = [
        record
        for record in records
        if "local_one_step_positive_regret" in record["labels"]
    ]
    if not labeled:
        return {
            "available": False,
            "records": 0,
        }
    gaps = [
        float(record["labels"]["local_one_step_positive_regret"])
        - float(record["labels"]["nash_conv"])
        for record in labeled
    ]
    normalized_absolute_gaps = [
        abs(gap) / _payoff_span(record)
        for gap, record in zip(gaps, labeled, strict=True)
    ]
    nonidentity = [
        abs(gap) > 1e-10 * max(1.0, _payoff_span(record))
        for gap, record in zip(gaps, labeled, strict=True)
    ]
    return {
        "available": True,
        "records": len(labeled),
        "nonidentity_records": sum(nonidentity),
        "nonidentity_rate": sum(nonidentity) / len(labeled),
        "minimum_signed_gap": min(gaps),
        "maximum_signed_gap": max(gaps),
        "mean_absolute_normalized_gap": mean(normalized_absolute_gaps),
        "maximum_absolute_normalized_gap": max(normalized_absolute_gaps),
    }


def _solver_path_diagnostics(
    records: list[dict[str, Any]],
    solver: str,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record["solver"] == solver:
            grouped.setdefault(str(record["context_id"]), []).append(record)
    first_improvements: Counter[int | None] = Counter()
    regression_count = 0
    final_not_best_count = 0
    for rows in grouped.values():
        rows.sort(key=lambda row: row["checkpoint"])
        exploitabilities = [float(row["labels"]["exploitability"]) for row in rows]
        first_improvement = next(
            (
                int(row["checkpoint"])
                for row in rows[1:]
                if float(row["labels"]["exploitability"])
                < exploitabilities[0] - TOLERANCE
            ),
            None,
        )
        first_improvements[first_improvement] += 1
        regression_count += any(
            right > left + TOLERANCE
            for left, right in zip(
                exploitabilities[:-1],
                exploitabilities[1:],
                strict=True,
            )
        )
        final_not_best_count += exploitabilities[-1] > min(exploitabilities) + TOLERANCE
    run_count = len(grouped)
    return {
        "solver": solver,
        "runs": run_count,
        "first_improvement_counts": {
            "none" if checkpoint is None else str(checkpoint): count
            for checkpoint, count in sorted(
                first_improvements.items(),
                key=lambda item: (
                    item[0] is None,
                    0 if item[0] is None else item[0],
                ),
            )
        },
        "any_checkpoint_regression_count": regression_count,
        "any_checkpoint_regression_rate": regression_count / run_count,
        "final_not_best_checkpoint_count": final_not_best_count,
        "final_not_best_checkpoint_rate": final_not_best_count / run_count,
    }


def _feature_correlations(
    records: list[dict[str, Any]],
    solver: str,
    checkpoint: int,
    target: str,
) -> dict[str, Any]:
    rows = [
        record
        for record in records
        if record["solver"] == solver and record["checkpoint"] == checkpoint
    ]
    targets = [_target_value(record, target) for record in rows]
    numeric_names = sorted(
        name
        for name, value in rows[0]["online_features"].items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    )
    correlations = []
    for name in numeric_names:
        values = [float(record["online_features"][name]) for record in rows]
        correlation = _spearman(values, targets)
        if correlation is not None:
            correlations.append(
                {
                    "feature": name,
                    "spearman": correlation,
                }
            )
    correlations.sort(
        key=lambda row: (-abs(float(row["spearman"])), str(row["feature"]))
    )
    return {
        "solver": solver,
        "checkpoint": checkpoint,
        "records": len(rows),
        "future_improvement_positive_rate": sum(
            bool(record["labels"]["future_improvement_positive"])
            for record in rows
        )
        / len(rows),
        "target": target,
        "target_description": TARGET_DESCRIPTIONS[target],
        "correlations": correlations,
    }


def _fold_correlations(
    records: list[dict[str, Any]],
    *,
    solver: str,
    checkpoint: int,
    feature: str,
    target: str,
    folds: int,
) -> list[dict[str, Any]]:
    result = []
    for fold in range(folds):
        rows = [
            record
            for record in records
            if record["solver"] == solver
            and record["checkpoint"] == checkpoint
            and int.from_bytes(
                hashlib.sha256(str(record["group_id"]).encode("utf-8")).digest()[:8],
                "big",
            )
            % folds
            == fold
        ]
        values = [float(record["online_features"][feature]) for record in rows]
        targets = [_target_value(record, target) for record in rows]
        result.append(
            {
                "fold": fold,
                "records": len(rows),
                "spearman": _spearman(values, targets),
            }
        )
    return result


def analyze_river_trace(
    artifact: dict[str, Any],
    *,
    primary_feature: str = "normalized_positive_regret_mass",
    primary_checkpoint: int = 2,
    primary_target: str = "normalized_future_reduction",
    allocation_probe_checkpoint: int | None = None,
    folds: int = 5,
) -> dict[str, Any]:
    """Return compact measurement-only diagnostics without fitting a rule."""

    if artifact.get("experiment_type") != "exact_river_early_opportunity_trace":
        raise ValueError("input is not an exact river opportunity trace")
    records = artifact.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("trace artifact must contain records")
    if folds <= 1:
        raise ValueError("folds must exceed one")
    if primary_feature not in records[0]["online_features"]:
        raise ValueError(f"unknown primary feature {primary_feature!r}")
    if primary_target not in TARGET_DESCRIPTIONS:
        raise ValueError(f"unknown primary target {primary_target!r}")
    solvers = tuple(str(solver) for solver in artifact["config"]["solvers"])
    checkpoints = tuple(int(value) for value in artifact["config"]["checkpoints"])
    sequential_raise = artifact["config"].get("sequential_raise", False) is True
    if primary_checkpoint not in checkpoints:
        raise ValueError("primary checkpoint is absent from the trace")
    if (
        allocation_probe_checkpoint is not None
        and allocation_probe_checkpoint not in checkpoints
    ):
        raise ValueError("allocation probe checkpoint is absent from the trace")

    correlations = [
        _feature_correlations(records, solver, checkpoint, primary_target)
        for solver in solvers
        for checkpoint in checkpoints[:-1]
    ]
    teacher_labels = [context["oracle_labels"] for context in artifact["contexts"]]
    post_probe_allocation = None
    if allocation_probe_checkpoint is not None:
        allocation_budgets = tuple(
            int(value)
            for value in artifact["config"][
                "allocation_average_iteration_budgets"
            ]
        )
        post_probe_allocation = _allocation_oracles(
            records,
            solvers,
            allocation_budgets,
            min(
                int(artifact["config"]["allocation_context_limit"]),
                int(artifact["counts"]["contexts"]),
            ),
            int(artifact["config"]["seed"]),
            minimum_checkpoint=allocation_probe_checkpoint,
        )
    return {
        "schema_version": 2,
        "analysis_type": "exact_river_opportunity_measurement",
        "status": "unfitted_diagnostics_only",
        "source_config": artifact["config"],
        "source_counts": artifact["counts"],
        "source_timing": artifact["timing"],
        "teacher_exactness": {
            "maximum_duality_gap": max(
                float(labels["duality_gap"]) for labels in teacher_labels
            ),
            "maximum_behavioral_nash_conv": max(
                float(labels["nash_conv"]) for labels in teacher_labels
            ),
            "mean_oracle_solve_milliseconds": mean(
                float(labels["solve_milliseconds"]) for labels in teacher_labels
            ),
        },
        "local_regret_vs_nash_conv": _local_regret_diagnostics(records),
        "solver_path_diagnostics": [
            _solver_path_diagnostics(records, solver) for solver in solvers
        ],
        "unfitted_feature_correlations": correlations,
        "primary_signal": {
            "feature": primary_feature,
            "checkpoint": primary_checkpoint,
            "target": primary_target,
            "target_description": TARGET_DESCRIPTIONS[primary_target],
            "group_preserving_folds": folds,
            "by_solver": [
                {
                    "solver": solver,
                    "all_records_spearman": next(
                        (
                            row["spearman"]
                            for item in correlations
                            if item["solver"] == solver
                            and item["checkpoint"] == primary_checkpoint
                            for row in item["correlations"]
                            if row["feature"] == primary_feature
                        ),
                        None,
                    ),
                    "folds": _fold_correlations(
                        records,
                        solver=solver,
                        checkpoint=primary_checkpoint,
                        feature=primary_feature,
                        target=primary_target,
                        folds=folds,
                    ),
                }
                for solver in solvers
            ],
        },
        "allocation_oracles": artifact["allocation_oracles"],
        "post_probe_allocation_oracles": post_probe_allocation,
        "interpretation_warnings": [
            "No scheduler or threshold is fitted by this analysis.",
            "Future reduction and exact exploitability are diagnostic labels only.",
            "The primary feature is variant-discounted accumulated solver regret, "
            "not a fresh exact counterfactual-regret calculation.",
            (
                "The opener acts twice on bet-raise paths, so local one-step regret "
                "is no longer identical to complete best-response opportunity; the "
                "tree is still a small fixed-action river abstraction."
                if sequential_raise
                else "Each player acts at most once in this binary-action tree, making "
                "local regret unusually close to complete best-response opportunity."
            ),
            "Pooled allocation sees future labels and can transfer work across "
            "contexts; it is not deployable.",
        ],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--primary-feature", default="normalized_positive_regret_mass")
    parser.add_argument("--primary-checkpoint", type=int, default=2)
    parser.add_argument("--primary-target", default="normalized_future_reduction")
    parser.add_argument("--allocation-probe-checkpoint", type=int)
    parser.add_argument("--folds", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = args.input.read_bytes()
    artifact = json.loads(raw)
    result = analyze_river_trace(
        artifact,
        primary_feature=args.primary_feature,
        primary_checkpoint=args.primary_checkpoint,
        primary_target=args.primary_target,
        allocation_probe_checkpoint=args.allocation_probe_checkpoint,
        folds=args.folds,
    )
    result["source_provenance"] = {
        "path": str(args.input.resolve()),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "river trace analysis: "
        f"contexts={result['source_counts']['contexts']}, "
        f"status={result['status']}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
