"""Frozen search-versus-blueprint rules and holdout evaluation."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from hashlib import sha256
from math import isfinite
from pathlib import Path
from typing import Any

from .leaf_matrix import run_leaf_matrix


@dataclass(frozen=True, slots=True)
class FrozenSelectionRule:
    """Auditable threshold rule over one declared uncertainty proxy."""

    name: str
    risk_metric: str
    maximum_risk: float
    candidate_config: dict[str, Any]
    candidate_policy: str

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> FrozenSelectionRule:
        if document.get("schema_version") != 1:
            raise ValueError("unsupported selection-rule schema")
        if document.get("status") != "frozen":
            raise ValueError("selection rule must have frozen status")
        rule = document.get("rule")
        if not isinstance(rule, dict):
            raise ValueError("selection rule document must contain a rule object")
        candidate_config = rule.get("candidate_config")
        if not isinstance(candidate_config, dict) or not candidate_config:
            raise ValueError("candidate_config must be a nonempty object")
        maximum_risk = float(rule.get("maximum_risk"))
        if not isfinite(maximum_risk) or maximum_risk < 0.0:
            raise ValueError("maximum_risk must be finite and nonnegative")
        candidate_policy = str(rule.get("candidate_policy"))
        if candidate_policy != "average":
            raise ValueError("only average-policy selection is currently supported")
        risk_metric = str(rule.get("risk_metric"))
        if not risk_metric:
            raise ValueError("risk_metric cannot be empty")
        return cls(
            name=str(document.get("name")),
            risk_metric=risk_metric,
            maximum_risk=maximum_risk,
            candidate_config=dict(candidate_config),
            candidate_policy=candidate_policy,
        )

    def selects_search(self, metrics: dict[str, Any]) -> bool:
        if self.risk_metric not in metrics:
            raise ValueError(f"run is missing risk metric {self.risk_metric!r}")
        risk = float(metrics[self.risk_metric])
        if not isfinite(risk) or risk < 0.0:
            raise ValueError("selection risk must be finite and nonnegative")
        return risk <= self.maximum_risk

    def validate_candidate(self, config: dict[str, Any]) -> None:
        mismatches = {
            key: {"expected": expected, "actual": config.get(key)}
            for key, expected in self.candidate_config.items()
            if config.get(key) != expected
        }
        if mismatches:
            raise ValueError(f"matrix run does not match frozen candidate: {mismatches}")


def rule_digest(document: dict[str, Any]) -> str:
    """Return a stable digest covering the complete preregistration document."""

    canonical = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def _safe_rate(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0.0 else None


def _subgroup_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    searched_cases = [case for case in cases if case["selected"] == "search"]
    return {
        "cases": len(cases),
        "searched": len(searched_cases),
        "search_rate": len(searched_cases) / len(cases),
        "harmful_searches": sum(
            case["selected"] == "search"
            and case["candidate_nash_conv_delta_from_blueprint"] >= 0.0
            for case in cases
        ),
        "missed_beneficial_searches": sum(
            case["selected"] != "search"
            and case["candidate_nash_conv_delta_from_blueprint"] < 0.0
            for case in cases
        ),
        "selected_mean_nash_conv_delta_from_blueprint": sum(
            case["selected_nash_conv_delta_from_blueprint"] for case in cases
        )
        / len(cases),
        "selected_worst_nash_conv_delta_from_blueprint": max(
            (
                case["selected_nash_conv_delta_from_blueprint"]
                for case in searched_cases
            ),
            default=0.0,
        ),
        "mean_oracle_regret": sum(case["oracle_regret"] for case in cases)
        / len(cases),
    }


def _selection_subgroups(cases: list[dict[str, Any]]) -> dict[str, Any]:
    fields = (
        "game",
        "blueprint_iterations",
        "depth_limit",
        "leaf_error_grouping",
        "leaf_error_scope",
        "leaf_error_target_on_policy_root_l2",
    )
    result: dict[str, Any] = {}
    for field in fields:
        values = {case["config"].get(field) for case in cases}
        result[field] = [
            {
                "value": value,
                "summary": _subgroup_summary(
                    [case for case in cases if case["config"].get(field) == value]
                ),
            }
            for value in sorted(values, key=lambda item: (item is None, repr(item)))
        ]
    joint_fields = ("game", "blueprint_iterations", "depth_limit")
    joint_values = {
        tuple(case["config"].get(field) for field in joint_fields)
        for case in cases
    }
    result["game_blueprint_depth"] = [
        {
            "value": dict(zip(joint_fields, value, strict=True)),
            "summary": _subgroup_summary(
                [
                    case
                    for case in cases
                    if tuple(case["config"].get(field) for field in joint_fields)
                    == value
                ]
            ),
        }
        for value in sorted(joint_values, key=repr)
    ]
    return result


def evaluate_frozen_selection(
    matrix_result: dict[str, Any],
    rule_document: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate a frozen rule against completed paired-leaf matrix runs."""

    if matrix_result.get("experiment_type") != "paired_leaf_error_matrix":
        raise ValueError("selection evaluation requires a paired leaf-error matrix")
    runs = matrix_result.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("matrix result must contain at least one compact run")
    rule = FrozenSelectionRule.from_document(rule_document)

    cases: list[dict[str, Any]] = []
    total_selected_delta = 0.0
    total_unconditional_delta = 0.0
    total_oracle_delta = 0.0
    total_oracle_regret = 0.0
    selected_search_seconds = 0.0
    unconditional_search_seconds = 0.0
    searched = 0
    harmful_searches = 0
    missed_beneficial_searches = 0
    correct_no_ops = 0
    selected_deltas: list[float] = []

    for run in runs:
        config = run.get("config")
        metrics = run.get("metrics")
        if not isinstance(config, dict) or not isinstance(metrics, dict):
            raise ValueError("each compact run requires config and metrics objects")
        rule.validate_candidate(config)
        search = rule.selects_search(metrics)
        risk = float(metrics[rule.risk_metric])
        candidate_delta = float(
            metrics["perturbed_average_nash_conv_delta_from_blueprint"]
        )
        search_seconds = float(metrics["perturbed_search_seconds"])
        if not isfinite(candidate_delta):
            raise ValueError("candidate NashConv delta must be finite")
        if not isfinite(search_seconds) or search_seconds < 0.0:
            raise ValueError("candidate search time must be finite and nonnegative")

        selected_delta = candidate_delta if search else 0.0
        oracle_delta = min(candidate_delta, 0.0)
        oracle_regret = selected_delta - oracle_delta
        if oracle_regret < -1e-15:
            raise AssertionError("selection cannot outperform the diagnostic oracle")

        searched += int(search)
        harmful_searches += int(search and candidate_delta >= 0.0)
        missed_beneficial_searches += int(not search and candidate_delta < 0.0)
        correct_no_ops += int(not search and candidate_delta >= 0.0)
        total_selected_delta += selected_delta
        total_unconditional_delta += candidate_delta
        total_oracle_delta += oracle_delta
        total_oracle_regret += max(0.0, oracle_regret)
        unconditional_search_seconds += search_seconds
        if search:
            selected_search_seconds += search_seconds
            selected_deltas.append(selected_delta)

        cases.append(
            {
                "config": config,
                "risk": risk,
                "selected": "search" if search else "blueprint_no_op",
                "candidate_nash_conv_delta_from_blueprint": candidate_delta,
                "selected_nash_conv_delta_from_blueprint": selected_delta,
                "oracle_nash_conv_delta_from_blueprint": oracle_delta,
                "oracle_regret": max(0.0, oracle_regret),
                "estimated_search_seconds": search_seconds if search else 0.0,
            }
        )

    count = len(cases)
    no_ops = count - searched
    beneficial_searches = sum(
        case["candidate_nash_conv_delta_from_blueprint"] < 0.0 for case in cases
    )
    unconditional_harmful = count - beneficial_searches
    selected_improvement = -total_selected_delta
    unconditional_improvement = -total_unconditional_delta

    return {
        "schema_version": 1,
        "experiment_type": "frozen_selection_evaluation",
        "rule": {
            "name": rule.name,
            "sha256": rule_digest(rule_document),
            "risk_metric": rule.risk_metric,
            "maximum_risk": rule.maximum_risk,
            "candidate_config": rule.candidate_config,
            "candidate_policy": rule.candidate_policy,
        },
        "matrix": {
            "config": matrix_result.get("matrix_config"),
            "environment": matrix_result.get("environment"),
            "run_count": matrix_result.get("run_count"),
            "wall_seconds": matrix_result.get("wall_seconds"),
        },
        "summary": {
            "cases": count,
            "searched": searched,
            "no_ops": no_ops,
            "search_rate": searched / count,
            "harmful_searches": harmful_searches,
            "missed_beneficial_searches": missed_beneficial_searches,
            "correct_no_ops": correct_no_ops,
            "selected_mean_nash_conv_delta_from_blueprint": (
                total_selected_delta / count
            ),
            "selected_worst_nash_conv_delta_from_blueprint": (
                max(selected_deltas) if selected_deltas else 0.0
            ),
            "selected_total_nash_conv_improvement": selected_improvement,
            "selected_estimated_search_seconds": selected_search_seconds,
            "selected_improvement_per_search_millisecond": _safe_rate(
                selected_improvement,
                selected_search_seconds * 1_000.0,
            ),
            "mean_oracle_regret": total_oracle_regret / count,
            "total_oracle_regret": total_oracle_regret,
        },
        "baselines": {
            "permanent_no_op": {
                "mean_nash_conv_delta_from_blueprint": 0.0,
                "harmful_searches": 0,
                "estimated_search_seconds": 0.0,
                "mean_oracle_regret": -total_oracle_delta / count,
            },
            "unconditional_search": {
                "mean_nash_conv_delta_from_blueprint": (
                    total_unconditional_delta / count
                ),
                "harmful_searches": unconditional_harmful,
                "estimated_search_seconds": unconditional_search_seconds,
                "improvement_per_search_millisecond": _safe_rate(
                    unconditional_improvement,
                    unconditional_search_seconds * 1_000.0,
                ),
                "mean_oracle_regret": (
                    (total_unconditional_delta - total_oracle_delta) / count
                ),
            },
            "full_game_oracle": {
                "warning": "diagnostic only; online NashConv is unavailable",
                "mean_nash_conv_delta_from_blueprint": total_oracle_delta / count,
                "estimated_search_seconds": None,
                "mean_oracle_regret": 0.0,
            },
        },
        "subgroups": _selection_subgroups(cases),
        "cases": cases,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rule", required=True, type=Path)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--matrix-config", type=Path)
    source.add_argument("--matrix-result", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    rule_document = json.loads(args.rule.read_text(encoding="utf-8"))
    if args.matrix_config is not None:
        matrix_config = json.loads(args.matrix_config.read_text(encoding="utf-8"))
        matrix_result = run_leaf_matrix(matrix_config)
    else:
        matrix_result = json.loads(args.matrix_result.read_text(encoding="utf-8"))
    result = evaluate_frozen_selection(matrix_result, rule_document)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    summary = result["summary"]
    print(
        f"frozen selection: cases={summary['cases']}, "
        f"searched={summary['searched']}, "
        f"harmful={summary['harmful_searches']}, "
        f"mean_delta={summary['selected_mean_nash_conv_delta_from_blueprint']:.8g}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
