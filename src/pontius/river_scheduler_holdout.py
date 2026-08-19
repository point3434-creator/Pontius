"""Evaluate one frozen river scheduler without selecting or retuning it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .river_opportunity import _pooled_iteration_oracle
from .river_scheduler_screen import (
    FIXED_CANDIDATE_ID,
    TOLERANCE,
    _evaluate_candidate,
    _fold,
)

FROZEN_RULE_ID = "river-post-probe-scheduler-v1"
FROZEN_RULE_SHA256 = (
    "74d6c3d68dbb7363af9927b72f83dce7769613656df8253ace36a1ff0cc598bd"
)


def _validate_source_config(
    source: dict[str, Any],
    rule: dict[str, Any],
    split: str,
) -> None:
    if source.get("experiment_type") != "exact_river_early_opportunity_trace":
        raise ValueError("source is not an exact river opportunity trace")
    expected = rule["reserved_generation"]
    config = source["config"]
    for name in (
        "allocation_average_iteration_budgets",
        "checkpoints",
        "families",
        "groups",
        "hands_per_player",
        "seed",
        "sequential_raise",
        "solvers",
        "store_policies",
    ):
        if config.get(name) != expected[name]:
            raise ValueError(f"reserved source differs from the frozen {name!r}")
    if config.get("included_splits") != [split]:
        raise ValueError("reserved source must contain exactly the requested split")
    if config.get("measure_active_regret_summary_cost") is not True:
        raise ValueError("reserved source must measure active regret summary cost")
    if config.get("shadow_regret_variants", {}) != {}:
        raise ValueError("the frozen reserved rule disables shadow regret")
    if split not in expected["split_order"]:
        raise ValueError(f"unsupported reserved split {split!r}")


def _authorize_split(
    split: str,
    rule: dict[str, Any],
    validation_result: dict[str, Any] | None,
    rule_provenance: dict[str, Any] | None,
) -> None:
    split_order = rule["reserved_generation"]["split_order"]
    if split == split_order[0]:
        if validation_result is not None:
            raise ValueError("validation evaluation cannot consume a prior result")
        return
    if split != split_order[1]:
        raise ValueError(f"unsupported reserved split {split!r}")
    if validation_result is None:
        raise ValueError("test remains sealed without a passing validation result")
    if validation_result.get("experiment_type") != "exact_river_scheduler_holdout":
        raise ValueError("test authorization is not a scheduler holdout result")
    if validation_result.get("reserved_split") != split_order[0]:
        raise ValueError("test authorization did not evaluate validation")
    if validation_result.get("status") != "validation_passed_test_authorized":
        raise ValueError("test remains sealed because validation did not pass")
    if validation_result.get("rule_id") != rule["rule_id"]:
        raise ValueError("validation used a different frozen rule")
    validation_rule_provenance = validation_result.get("rule_provenance")
    if (
        rule_provenance is not None
        and validation_rule_provenance is not None
        and validation_rule_provenance.get("sha256")
        != rule_provenance.get("sha256")
    ):
        raise ValueError("validation used a different frozen rule artifact")


def _build_contexts(
    source: dict[str, Any],
    *,
    split: str,
    probe_checkpoint: int,
    required_checkpoints: set[int],
) -> dict[str, dict[str, Any]]:
    source_contexts = {
        str(context["context_id"]): context for context in source["contexts"]
    }
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in source["records"]:
        if record["solver"] != "dcfr":
            raise ValueError("reserved trace contains a non-DCFR solver record")
        grouped.setdefault(str(record["context_id"]), []).append(record)
    if set(source_contexts) != set(grouped):
        raise ValueError("reserved context and trace identities differ")

    contexts = {}
    for context_id, source_context in source_contexts.items():
        if source_context["split"] != split:
            raise ValueError("reserved artifact contains another split")
        rows = sorted(grouped[context_id], key=lambda row: int(row["checkpoint"]))
        if any(row["split"] != split for row in rows):
            raise ValueError("reserved trace row contains another split")
        by_checkpoint = {int(row["checkpoint"]): row for row in rows}
        if len(by_checkpoint) != len(rows):
            raise ValueError(f"duplicate checkpoint for {context_id!r}")
        if not required_checkpoints <= set(by_checkpoint):
            raise ValueError(f"required checkpoints are missing for {context_id!r}")
        probe_row = by_checkpoint[probe_checkpoint]
        feature_milliseconds = probe_row["online_features"].get(
            "active_regret_summary_milliseconds"
        )
        if feature_milliseconds is None:
            raise ValueError("active regret summary timing is unavailable")
        contexts[context_id] = {
            "group_id": str(source_context["group_id"]),
            "features": dict(probe_row["online_features"]),
            "rows": rows,
            "checkpoints": {
                checkpoint: {
                    "exploitability": float(row["labels"]["exploitability"]),
                    "state_visits": int(
                        row["online_features"][
                            "cumulative_alternating_state_visits"
                        ]
                    ),
                    "solver_milliseconds": float(
                        row["online_features"]["cumulative_solver_milliseconds"]
                    ),
                }
                for checkpoint, row in by_checkpoint.items()
            },
            "active_feature_overhead_milliseconds": float(feature_milliseconds),
        }
    return contexts


def _candidate(rule: dict[str, Any]) -> dict[str, Any]:
    score = rule["score"]
    macro = rule["macro"]
    if rule["solver"].get("shadow_regret_enabled") is not False:
        raise ValueError("frozen holdout evaluator supports active-only regret")
    if score.get("feature") != "positive_regret_mass":
        raise ValueError("frozen holdout evaluator supports raw positive regret")
    return {
        "candidate_id": f"{score['name']}::{macro['name']}",
        "fixed": False,
        "score": {
            "name": score["name"],
            "terms": [
                {
                    "feature": score["feature"],
                    "direction": score["direction"],
                    "weight": 1.0,
                }
            ],
        },
        "macro": macro,
    }


def _evaluate_pool(
    contexts: dict[str, dict[str, Any]],
    candidate: dict[str, Any],
    *,
    probe_checkpoint: int,
    fixed_checkpoint: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate_metrics = _evaluate_candidate(
        contexts,
        candidate,
        probe_checkpoint=probe_checkpoint,
        fixed_checkpoint=fixed_checkpoint,
    )
    fixed_metrics = _evaluate_candidate(
        contexts,
        {"candidate_id": FIXED_CANDIDATE_ID, "fixed": True},
        probe_checkpoint=probe_checkpoint,
        fixed_checkpoint=fixed_checkpoint,
    )
    oracle = _pooled_iteration_oracle(
        [context["rows"] for context in contexts.values()],
        average_budget=fixed_checkpoint,
        minimum_checkpoint=probe_checkpoint,
    )
    perfect_uplift = (
        float(oracle["pooled_perfect_information_total_reduction"])
        - float(oracle["fixed_checkpoint_total_reduction"])
    )
    actual_uplift = float(
        candidate_metrics["raw_exploitability_uplift_over_fixed"]
    )
    return (
        candidate_metrics,
        {
            "fixed_metrics": fixed_metrics,
            "perfect_post_probe_uplift": perfect_uplift,
            "fraction_of_perfect_post_probe_uplift": (
                actual_uplift / perfect_uplift
                if perfect_uplift > TOLERANCE
                else None
            ),
            "perfect_oracle_selection_counts": oracle["pooled_selection_counts"],
        },
    )


def run_river_scheduler_holdout(
    source: dict[str, Any],
    rule: dict[str, Any],
    *,
    split: str,
    validation_result: dict[str, Any] | None = None,
    source_provenance: dict[str, Any] | None = None,
    rule_provenance: dict[str, Any] | None = None,
    validation_provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate one committed rule; candidate selection is intentionally absent."""

    if rule.get("status") != "frozen_before_reserved":
        raise ValueError("rule is not frozen before reserved evaluation")
    if rule.get("rule_id") == FROZEN_RULE_ID and (
        rule_provenance is None
        or rule_provenance.get("sha256") != FROZEN_RULE_SHA256
    ):
        raise ValueError("production rule SHA-256 does not match the frozen artifact")
    _authorize_split(split, rule, validation_result, rule_provenance)
    _validate_source_config(source, rule, split)

    solver = rule["solver"]
    if solver.get("active_variant") != "dcfr":
        raise ValueError("reserved evaluator requires frozen DCFR")
    probe_checkpoint = int(solver["probe_checkpoint"])
    fixed_checkpoint = int(solver["fixed_checkpoint"])
    recipient_checkpoint = int(rule["macro"]["recipient_checkpoint"])
    required_checkpoints = {
        0,
        probe_checkpoint,
        fixed_checkpoint,
        recipient_checkpoint,
    }
    contexts = _build_contexts(
        source,
        split=split,
        probe_checkpoint=probe_checkpoint,
        required_checkpoints=required_checkpoints,
    )
    folds = int(rule["reserved_evaluation"]["folds"])
    fold_by_context = {
        context_id: _fold(context["group_id"], folds)
        for context_id, context in contexts.items()
    }
    if set(fold_by_context.values()) != set(range(folds)):
        raise ValueError("one or more reserved group folds are empty")

    candidate = _candidate(rule)
    fold_results = []
    for fold in range(folds):
        fold_contexts = {
            context_id: context
            for context_id, context in contexts.items()
            if fold_by_context[context_id] == fold
        }
        candidate_metrics, controls = _evaluate_pool(
            fold_contexts,
            candidate,
            probe_checkpoint=probe_checkpoint,
            fixed_checkpoint=fixed_checkpoint,
        )
        fold_results.append(
            {
                "fold": fold,
                "groups": len(
                    {context["group_id"] for context in fold_contexts.values()}
                ),
                "contexts": len(fold_contexts),
                "candidate": candidate_metrics,
                **controls,
            }
        )

    full_pool_metrics, full_pool_controls = _evaluate_pool(
        contexts,
        candidate,
        probe_checkpoint=probe_checkpoint,
        fixed_checkpoint=fixed_checkpoint,
    )
    candidate_reduction = sum(
        float(fold["candidate"]["candidate_reduction_from_checkpoint_zero"])
        for fold in fold_results
    )
    fixed_reduction = sum(
        float(fold["candidate"]["fixed_reduction_from_checkpoint_zero"])
        for fold in fold_results
    )
    candidate_milliseconds = sum(
        float(fold["candidate"]["candidate_total_milliseconds"])
        for fold in fold_results
    )
    fixed_milliseconds = sum(
        float(fold["candidate"]["fixed_solver_milliseconds"])
        for fold in fold_results
    )
    actual_uplift = sum(
        float(fold["candidate"]["raw_exploitability_uplift_over_fixed"])
        for fold in fold_results
    )
    perfect_uplift = sum(
        float(fold["perfect_post_probe_uplift"]) for fold in fold_results
    )
    candidate_rate = candidate_reduction / candidate_milliseconds
    fixed_rate = fixed_reduction / fixed_milliseconds
    threshold = float(
        rule["reserved_evaluation"]["validation_gates"][
            "aggregate_fraction_of_perfect_post_probe_uplift_at_least"
        ]
    )
    gates = {
        "strict_raw_improvement_in_every_group_fold": all(
            float(fold["candidate"]["raw_exploitability_uplift_over_fixed"])
            > TOLERANCE
            for fold in fold_results
        ),
        "aggregate_perfect_uplift_capture_at_least_threshold": (
            perfect_uplift > TOLERANCE
            and actual_uplift / perfect_uplift >= threshold
        ),
        "candidate_iterations_not_above_fixed_in_every_fold": all(
            int(fold["candidate"]["candidate_iterations"])
            <= int(fold["candidate"]["fixed_iterations"])
            for fold in fold_results
        ),
        "candidate_state_visits_not_above_fixed_in_every_fold": all(
            int(fold["candidate"]["candidate_state_visits"])
            <= int(fold["candidate"]["fixed_state_visits"])
            for fold in fold_results
        ),
        "aggregate_measured_reduction_per_millisecond_beats_fixed": (
            candidate_rate > fixed_rate
        ),
    }
    passed = all(gates.values())
    if split == rule["reserved_generation"]["split_order"][0]:
        status = (
            "validation_passed_test_authorized"
            if passed
            else "validation_failed_keep_fixed_test_sealed"
        )
    else:
        status = "test_passed" if passed else "test_failed_keep_fixed"

    teacher_labels = [context["oracle_labels"] for context in source["contexts"]]
    return {
        "schema_version": 1,
        "experiment_type": "exact_river_scheduler_holdout",
        "status": status,
        "reserved_split": split,
        "rule_id": rule["rule_id"],
        "source_provenance": source_provenance,
        "rule_provenance": rule_provenance,
        "validation_provenance": validation_provenance,
        "counts": {
            "groups": len({context["group_id"] for context in contexts.values()}),
            "contexts": len(contexts),
            "folds": folds,
        },
        "candidate_id": candidate["candidate_id"],
        "candidate_selection_performed": False,
        "shadow_regret_enabled": False,
        "teacher_exactness": {
            "maximum_duality_gap": max(
                float(labels["duality_gap"]) for labels in teacher_labels
            ),
            "maximum_behavioral_nash_conv": max(
                float(labels["nash_conv"]) for labels in teacher_labels
            ),
        },
        "folds": fold_results,
        "aggregate": {
            "raw_exploitability_uplift_over_fixed": actual_uplift,
            "perfect_post_probe_uplift": perfect_uplift,
            "fraction_of_perfect_post_probe_uplift": (
                actual_uplift / perfect_uplift
                if perfect_uplift > TOLERANCE
                else None
            ),
            "fixed_reduction_from_checkpoint_zero": fixed_reduction,
            "candidate_reduction_from_checkpoint_zero": candidate_reduction,
            "fixed_solver_milliseconds": fixed_milliseconds,
            "candidate_charged_milliseconds": candidate_milliseconds,
            "fixed_reduction_per_millisecond": fixed_rate,
            "candidate_reduction_per_millisecond": candidate_rate,
            "rate_uplift_fraction": candidate_rate / fixed_rate - 1.0,
        },
        "full_pool_diagnostic": {
            "candidate": full_pool_metrics,
            **full_pool_controls,
        },
        "gates": gates,
        "passed": passed,
        "test_authorized": split == "validation" and passed,
        "interpretation_warnings": [
            "The evaluator applies one frozen rule and performs no candidate selection.",
            "Exact exploitability and perfect allocation are post-construction diagnostics only.",
            "The pool models shared or speculative jobs, not transfers between "
            "completed decisions.",
            "A river holdout cannot establish multiplayer or earlier-street transfer.",
        ],
    }


def _read_with_provenance(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = path.read_bytes()
    return (
        json.loads(raw),
        {
            "path": str(path.resolve()),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        },
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--rule", required=True, type=Path)
    parser.add_argument("--split", required=True, choices=("validation", "test"))
    parser.add_argument("--validation-result", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    source, source_provenance = _read_with_provenance(args.source)
    rule, rule_provenance = _read_with_provenance(args.rule)
    validation_result = None
    validation_provenance = None
    if args.validation_result is not None:
        validation_result, validation_provenance = _read_with_provenance(
            args.validation_result
        )
    result = run_river_scheduler_holdout(
        source,
        rule,
        split=args.split,
        validation_result=validation_result,
        source_provenance=source_provenance,
        rule_provenance=rule_provenance,
        validation_provenance=validation_provenance,
    )
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "river scheduler holdout: "
        f"split={result['reserved_split']}, "
        f"passed={result['passed']}, "
        f"status={result['status']}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
