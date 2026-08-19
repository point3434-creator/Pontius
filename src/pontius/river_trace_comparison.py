"""Paired comparison of one-bet and sequential exact-river traces."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .river_trace_analysis import _normalized_future_target, _spearman

PAIR_FIELDS = ("board", "pot", "bet_size", "joint_range")


def _run_records(
    artifact: dict[str, Any],
) -> dict[tuple[str, str], dict[int, dict[str, Any]]]:
    result: dict[tuple[str, str], dict[int, dict[str, Any]]] = {}
    for record in artifact["records"]:
        key = (str(record["context_id"]), str(record["solver"]))
        checkpoint = int(record["checkpoint"])
        rows = result.setdefault(key, {})
        if checkpoint in rows:
            raise ValueError(f"duplicate trace record for {key!r} at {checkpoint}")
        rows[checkpoint] = record
    return result


def _state_efficiency(
    rows: dict[int, dict[str, Any]],
    checkpoint: int,
) -> float:
    current = rows[checkpoint]
    current_exploitability = float(current["labels"]["exploitability"])
    features = current["online_features"]
    payoff_span = float(
        features.get(
            "payoff_span",
            float(features["pot"]) + 2.0 * float(features["bet_size"]),
        )
    )
    current_visits = int(features["cumulative_alternating_state_visits"])
    best_rate = 0.0
    for future_checkpoint, future in rows.items():
        if future_checkpoint <= checkpoint:
            continue
        gain = max(
            0.0,
            current_exploitability
            - float(future["labels"]["exploitability"]),
        ) / payoff_span
        state_cost = (
            int(
                future["online_features"][
                    "cumulative_alternating_state_visits"
                ]
            )
            - current_visits
        )
        if state_cost <= 0:
            raise ValueError("future trace state cost must be positive")
        best_rate = max(best_rate, gain / (state_cost / 1_000.0))
    return best_rate


def _allocation_uplifts(artifact: dict[str, Any]) -> dict[str, dict[int, float | None]]:
    return {
        str(solver["solver"]): {
            int(row["average_iteration_budget"]): (
                None
                if row["pooled_uplift_over_fixed_fraction"] is None
                else float(row["pooled_uplift_over_fixed_fraction"])
            )
            for row in solver["budgets"]
        }
        for solver in artifact["allocation_oracles"]["solvers"]
    }


def compare_river_traces(
    baseline: dict[str, Any],
    target: dict[str, Any],
    *,
    checkpoint: int = 2,
    feature: str = "normalized_positive_regret_mass",
) -> dict[str, Any]:
    """Compare matched contexts while allowing their betting trees to differ."""

    expected_type = "exact_river_early_opportunity_trace"
    if baseline.get("experiment_type") != expected_type:
        raise ValueError("baseline is not an exact river opportunity trace")
    if target.get("experiment_type") != expected_type:
        raise ValueError("target is not an exact river opportunity trace")

    baseline_contexts = {
        str(context["context_id"]): context for context in baseline["contexts"]
    }
    target_contexts = {
        str(context["context_id"]): context for context in target["contexts"]
    }
    if set(baseline_contexts) != set(target_contexts):
        raise ValueError("paired traces must contain identical context IDs")
    context_ids = tuple(sorted(baseline_contexts))
    for context_id in context_ids:
        left = baseline_contexts[context_id]
        right = target_contexts[context_id]
        if any(left[field] != right[field] for field in PAIR_FIELDS):
            raise ValueError(
                f"paired context {context_id!r} changed cards, bet, or joint range"
            )

    solvers = tuple(str(value) for value in baseline["config"]["solvers"])
    if solvers != tuple(str(value) for value in target["config"]["solvers"]):
        raise ValueError("paired traces must contain the same ordered solvers")
    baseline_runs = _run_records(baseline)
    target_runs = _run_records(target)
    if set(baseline_runs) != set(target_runs):
        raise ValueError("paired traces must contain identical solver runs")
    if any(
        checkpoint not in baseline_runs[key] or checkpoint not in target_runs[key]
        for key in baseline_runs
    ):
        raise ValueError("comparison checkpoint is absent from a paired run")

    solver_results = []
    for solver in solvers:
        baseline_rows = [baseline_runs[(context_id, solver)] for context_id in context_ids]
        target_rows = [target_runs[(context_id, solver)] for context_id in context_ids]
        baseline_checkpoint_rows = [rows[checkpoint] for rows in baseline_rows]
        target_checkpoint_rows = [rows[checkpoint] for rows in target_rows]
        if any(
            feature not in row["online_features"]
            for row in (*baseline_checkpoint_rows, *target_checkpoint_rows)
        ):
            raise ValueError(f"comparison feature {feature!r} is unavailable")

        baseline_features = [
            float(row["online_features"][feature])
            for row in baseline_checkpoint_rows
        ]
        target_features = [
            float(row["online_features"][feature])
            for row in target_checkpoint_rows
        ]
        baseline_total = [
            _normalized_future_target(row) for row in baseline_checkpoint_rows
        ]
        target_total = [
            _normalized_future_target(row) for row in target_checkpoint_rows
        ]
        baseline_efficiency = [
            _state_efficiency(rows, checkpoint) for rows in baseline_rows
        ]
        target_efficiency = [
            _state_efficiency(rows, checkpoint) for rows in target_rows
        ]
        solver_results.append(
            {
                "solver": solver,
                "baseline_feature_vs_baseline_total_opportunity": _spearman(
                    baseline_features,
                    baseline_total,
                ),
                "target_feature_vs_target_total_opportunity": _spearman(
                    target_features,
                    target_total,
                ),
                "baseline_feature_vs_target_total_opportunity": _spearman(
                    baseline_features,
                    target_total,
                ),
                "baseline_feature_vs_target_state_efficiency": _spearman(
                    baseline_features,
                    target_efficiency,
                ),
                "target_feature_vs_target_state_efficiency": _spearman(
                    target_features,
                    target_efficiency,
                ),
                "feature_rank_stability": _spearman(
                    baseline_features,
                    target_features,
                ),
                "total_opportunity_rank_stability": _spearman(
                    baseline_total,
                    target_total,
                ),
                "state_efficiency_rank_stability": _spearman(
                    baseline_efficiency,
                    target_efficiency,
                ),
            }
        )

    baseline_uplifts = _allocation_uplifts(baseline)
    target_uplifts = _allocation_uplifts(target)
    allocation_comparison = []
    for solver in solvers:
        if set(baseline_uplifts[solver]) != set(target_uplifts[solver]):
            raise ValueError("paired allocation budgets differ")
        allocation_comparison.append(
            {
                "solver": solver,
                "budgets": [
                    {
                        "average_iteration_budget": budget,
                        "baseline_pooled_uplift_over_fixed_fraction": (
                            baseline_uplifts[solver][budget]
                        ),
                        "target_pooled_uplift_over_fixed_fraction": (
                            target_uplifts[solver][budget]
                        ),
                    }
                    for budget in sorted(baseline_uplifts[solver])
                ],
            }
        )

    return {
        "schema_version": 1,
        "analysis_type": "paired_exact_river_trace_comparison",
        "status": "paired_diagnostics_only",
        "contexts": len(context_ids),
        "checkpoint": checkpoint,
        "feature": feature,
        "pair_fields": list(PAIR_FIELDS),
        "exact_context_pairing": True,
        "solver_correlations": solver_results,
        "allocation_comparison": allocation_comparison,
        "interpretation_warnings": [
            "Cross-tree rank stability tests transfer; it is not a deployable score.",
            "State efficiency uses exact future exploitability and is diagnostic only.",
            "Both traces must remain development-only until a rule is frozen.",
        ],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--checkpoint", type=int, default=2)
    parser.add_argument("--feature", default="normalized_positive_regret_mass")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    baseline_raw = args.baseline.read_bytes()
    target_raw = args.target.read_bytes()
    result = compare_river_traces(
        json.loads(baseline_raw),
        json.loads(target_raw),
        checkpoint=args.checkpoint,
        feature=args.feature,
    )
    result["source_provenance"] = {
        "baseline_path": str(args.baseline.resolve()),
        "baseline_sha256": hashlib.sha256(baseline_raw).hexdigest(),
        "target_path": str(args.target.resolve()),
        "target_sha256": hashlib.sha256(target_raw).hexdigest(),
    }
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "paired river trace comparison: "
        f"contexts={result['contexts']}, status={result['status']}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
