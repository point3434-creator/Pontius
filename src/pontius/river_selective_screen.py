"""Grouped transparent screen for causal selective-width decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, stdev
from typing import Any, Iterable


TOLERANCE = 1e-12
NO_OP = "no_op"
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


@dataclass
class _FitNode:
    rows: list[dict[str, Any]]
    depth: int
    arm: str
    arm_score: float
    objective: float
    feature: str | None = None
    threshold: float | None = None
    left: _FitNode | None = None
    right: _FitNode | None = None

    @property
    def is_leaf(self) -> bool:
        return self.feature is None


@dataclass(frozen=True)
class _CandidateSpec:
    candidate_id: str
    tier_index: int
    tier_name: str
    features: tuple[str, ...]
    maximum_depth: int
    risk_multiplier: float


def _read_with_provenance(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = path.read_bytes()
    return (
        json.loads(payload),
        {
            "path": str(path.resolve()),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        },
    )


def _validate_feature_name(name: str) -> None:
    lowered = name.lower()
    if any(fragment in lowered for fragment in FORBIDDEN_FEATURE_FRAGMENTS):
        raise ValueError(f"selector feature {name!r} contains a forbidden fragment")


def _validate_rule(rule: dict[str, Any]) -> dict[str, Any]:
    if rule.get("status") != "preregistered_discovery_only":
        raise ValueError("selective-width rule is not preregistered for discovery")
    frozen = rule.get("frozen_source")
    if not isinstance(frozen, dict):
        raise ValueError("rule must freeze a source artifact")
    regime = rule.get("solver_regime")
    if not isinstance(regime, dict):
        raise ValueError("rule must declare a solver regime")
    arms = tuple(str(value) for value in regime.get("candidate_arms", ()))
    if arms != (NO_OP, "b3r1", "b3r2"):
        raise ValueError("primary compact arms must be no_op, b3r1, and b3r2")
    if str(regime.get("fallback_mask")) != "b3r2":
        raise ValueError("fixed fallback must be b3r2")
    budget = int(regime["full_tree_equivalent_iteration_budget"])
    warm = float(regime["warm_start_multiplier_by_payoff_span"])
    if budget <= 0 or not math.isfinite(warm) or warm <= 0.0:
        raise ValueError("solver budget and warm strength must be positive")

    raw_tiers = rule.get("feature_tiers")
    if not isinstance(raw_tiers, list) or not raw_tiers:
        raise ValueError("rule must declare feature tiers")
    tiers = []
    prior: set[str] = set()
    tier_names: set[str] = set()
    for raw in raw_tiers:
        name = str(raw["name"])
        features = tuple(str(value) for value in raw.get("features", ()))
        if not features or len(features) != len(set(features)):
            raise ValueError("every feature tier must be nonempty and unique")
        if name in tier_names:
            raise ValueError("feature tier names must be unique")
        for feature in features:
            _validate_feature_name(feature)
        current = set(features)
        if prior and not prior < current:
            raise ValueError("feature tiers must be strictly cumulative")
        prior = current
        tier_names.add(name)
        tiers.append({"name": name, "features": features})

    family = rule.get("tree_family")
    if not isinstance(family, dict):
        raise ValueError("rule must declare a tree family")
    depths = tuple(int(value) for value in family.get("maximum_depths", ()))
    risks = tuple(float(value) for value in family.get("risk_standard_error_multipliers", ()))
    if not depths or any(depth not in (1, 2) for depth in depths):
        raise ValueError("tree depths must be one or two")
    if depths != tuple(sorted(set(depths))):
        raise ValueError("tree depths must be sorted and unique")
    if (
        not risks
        or risks != tuple(sorted(set(risks)))
        or any(not math.isfinite(value) or value < 0.0 for value in risks)
    ):
        raise ValueError("risk multipliers must be sorted, unique, and nonnegative")
    minimum_instances = int(family["minimum_leaf_instances"])
    minimum_groups = int(family["minimum_leaf_board_groups"])
    arm_priority = tuple(str(value) for value in family.get("leaf_tie_order", ()))
    if arm_priority != (NO_OP, "b3r2", "b3r1"):
        raise ValueError("leaf tie order must prefer no-op, full, then near-full")
    if minimum_instances <= 0 or minimum_groups < 2:
        raise ValueError("minimum leaf support is too small")

    gates = rule.get("selection_gates")
    if not isinstance(gates, dict):
        raise ValueError("rule must declare selection gates")
    required_gates = {
        "minimum_board_groups",
        "aggregate_raw_reduction_strictly_beats_fixed_b3r2",
        "aggregate_normalized_reduction_strictly_beats_fixed_b3r2",
        "minimum_positive_raw_uplift_group_fraction",
        "minimum_compact_oracle_opportunity_capture_fraction",
        "aggregate_state_visits_not_above_fixed_b3r2",
        "charged_raw_reduction_per_millisecond_strictly_beats_fixed_b3r2",
        "maximum_selected_target_harm_not_above_fixed_b3r2",
    }
    if set(gates) != required_gates:
        raise ValueError("selection gates do not match the frozen contract")
    for name in (
        "aggregate_raw_reduction_strictly_beats_fixed_b3r2",
        "aggregate_normalized_reduction_strictly_beats_fixed_b3r2",
        "aggregate_state_visits_not_above_fixed_b3r2",
        "charged_raw_reduction_per_millisecond_strictly_beats_fixed_b3r2",
        "maximum_selected_target_harm_not_above_fixed_b3r2",
    ):
        if gates[name] is not True:
            raise ValueError(f"gate {name!r} must remain enabled")
    group_fraction = float(gates["minimum_positive_raw_uplift_group_fraction"])
    capture_fraction = float(
        gates["minimum_compact_oracle_opportunity_capture_fraction"]
    )
    if not 0.0 <= group_fraction <= 1.0 or not 0.0 <= capture_fraction <= 1.0:
        raise ValueError("fractional gates must lie in [0, 1]")

    return {
        "arms": arms,
        "budget": budget,
        "warm": warm,
        "fallback": "b3r2",
        "tiers": tuple(tiers),
        "depths": depths,
        "risks": risks,
        "minimum_leaf_instances": minimum_instances,
        "minimum_leaf_groups": minimum_groups,
        "arm_priority": arm_priority,
        "gates": gates,
        "frozen_source": frozen,
    }


def _candidate_specs(parsed: dict[str, Any]) -> list[_CandidateSpec]:
    result = []
    for tier_index, tier in enumerate(parsed["tiers"]):
        for depth in parsed["depths"]:
            for risk in parsed["risks"]:
                risk_token = format(risk, "g").replace(".", "p")
                result.append(
                    _CandidateSpec(
                        candidate_id=(
                            f"{tier['name']}__depth_{depth}__risk_{risk_token}"
                        ),
                        tier_index=tier_index,
                        tier_name=str(tier["name"]),
                        features=tuple(tier["features"]),
                        maximum_depth=depth,
                        risk_multiplier=risk,
                    )
                )
    return result


def _build_examples(
    artifact: dict[str, Any],
    parsed: dict[str, Any],
) -> list[dict[str, Any]]:
    if artifact.get("experiment_type") != "river_selective_expansion_development_matrix":
        raise ValueError("source is not a selective-expansion development matrix")
    if artifact.get("evidence_stage") != "group_separated_development":
        raise ValueError("source is not group-separated development evidence")
    if artifact.get("selection_authorized") is not False:
        raise ValueError("source must explicitly prohibit prior selection")

    targets: dict[tuple[str, str], dict[str, Any]] = {}
    required_features = set(parsed["tiers"][-1]["features"])
    for raw in artifact.get("targets", []):
        key = (str(raw["context_id"]), str(raw["target_name"]))
        if key in targets:
            raise ValueError(f"duplicate target {key!r}")
        features = raw.get("boundary_online_features")
        if not isinstance(features, dict) or not required_features <= set(features):
            raise ValueError(f"target {key!r} is missing a frozen online feature")
        normalized_features = {}
        for name in required_features:
            _validate_feature_name(name)
            value = float(features[name])
            if not math.isfinite(value):
                raise ValueError(f"target {key!r} has a nonfinite feature")
            normalized_features[name] = value
        payoff_span = float(features["target_payoff_span"])
        boundary_seconds = float(raw["boundary_feature_seconds"])
        if (
            not math.isfinite(payoff_span)
            or not math.isfinite(boundary_seconds)
            or payoff_span <= 0.0
            or boundary_seconds < 0.0
        ):
            raise ValueError("payoff span and feature time are invalid")
        targets[key] = {
            "context_id": key[0],
            "target_name": key[1],
            "group_id": str(raw["group_id"]),
            "features": normalized_features,
            "payoff_span": payoff_span,
            "boundary_feature_seconds": boundary_seconds,
        }
    if not targets:
        raise ValueError("source has no targets")

    records: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for raw in artifact.get("records", []):
        if (
            int(raw["full_tree_equivalent_iteration_budget"]) != parsed["budget"]
            or abs(
                float(raw["warm_start_multiplier_by_payoff_span"])
                - parsed["warm"]
            )
            > 1e-15
        ):
            continue
        mask = str(raw["mask_name"])
        if mask not in parsed["arms"]:
            continue
        key = (str(raw["context_id"]), str(raw["target_name"]))
        if mask in records[key]:
            raise ValueError(f"duplicate {mask!r} record for {key!r}")
        records[key][mask] = raw

    examples = []
    searched_arms = tuple(arm for arm in parsed["arms"] if arm != NO_OP)
    for key, target in sorted(targets.items()):
        arm_records = records.get(key, {})
        if set(arm_records) != set(searched_arms):
            raise ValueError(f"target {key!r} does not contain every compact arm")
        arms: dict[str, dict[str, float | int]] = {
            NO_OP: {
                "raw_reduction": 0.0,
                "normalized_reduction": 0.0,
                "state_visits": 0,
                "solve_seconds": 0.0,
                "exact_label_seconds": 0.0,
            }
        }
        for arm in searched_arms:
            row = arm_records[arm]
            reduction = float(row["nash_conv_reduction_from_blueprint"])
            state_visits = int(row["actual_state_visits"])
            solve_seconds = float(row["cold_exact_leaf_online_seconds"])
            label_seconds = float(row["full_evaluation_label_seconds"])
            if (
                not math.isfinite(reduction)
                or not math.isfinite(solve_seconds)
                or not math.isfinite(label_seconds)
                or state_visits <= 0
                or solve_seconds <= 0.0
                or label_seconds < 0.0
            ):
                raise ValueError(f"target {key!r} has invalid arm metrics")
            arms[arm] = {
                "raw_reduction": reduction,
                "normalized_reduction": reduction / float(target["payoff_span"]),
                "state_visits": state_visits,
                "solve_seconds": solve_seconds,
                "exact_label_seconds": label_seconds,
            }
        examples.append({**target, "arms": arms})
    return examples


def _group_arm_means(rows: list[dict[str, Any]], arm: str) -> list[float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[str(row["group_id"])].append(
            float(row["arms"][arm]["normalized_reduction"])
        )
    return [mean(values) for _, values in sorted(grouped.items())]


def _risk_adjusted_arm_score(
    rows: list[dict[str, Any]],
    arm: str,
    risk_multiplier: float,
) -> float:
    group_means = _group_arm_means(rows, arm)
    center = mean(group_means)
    standard_error = (
        stdev(group_means) / math.sqrt(len(group_means))
        if len(group_means) > 1
        else 0.0
    )
    return center - risk_multiplier * standard_error


def _make_leaf(
    rows: list[dict[str, Any]],
    *,
    depth: int,
    arms: tuple[str, ...],
    risk_multiplier: float,
) -> _FitNode:
    best_arm = arms[0]
    best_score = _risk_adjusted_arm_score(rows, best_arm, risk_multiplier)
    for arm in arms[1:]:
        score = _risk_adjusted_arm_score(rows, arm, risk_multiplier)
        if score > best_score + TOLERANCE:
            best_arm = arm
            best_score = score
    return _FitNode(
        rows=rows,
        depth=depth,
        arm=best_arm,
        arm_score=best_score,
        objective=len(rows) * best_score,
    )


def _groups(rows: Iterable[dict[str, Any]]) -> set[str]:
    return {str(row["group_id"]) for row in rows}


def _best_split(
    node: _FitNode,
    *,
    features: tuple[str, ...],
    arms: tuple[str, ...],
    risk_multiplier: float,
    minimum_instances: int,
    minimum_groups: int,
) -> tuple[float, str, float, _FitNode, _FitNode] | None:
    best: tuple[float, str, float, _FitNode, _FitNode] | None = None
    for feature in features:
        values = sorted({float(row["features"][feature]) for row in node.rows})
        for lower, upper in zip(values, values[1:]):
            threshold = lower + (upper - lower) / 2.0
            if threshold <= lower or threshold >= upper:
                continue
            left_rows = [
                row for row in node.rows if float(row["features"][feature]) <= threshold
            ]
            right_rows = [
                row for row in node.rows if float(row["features"][feature]) > threshold
            ]
            if (
                len(left_rows) < minimum_instances
                or len(right_rows) < minimum_instances
                or len(_groups(left_rows)) < minimum_groups
                or len(_groups(right_rows)) < minimum_groups
            ):
                continue
            left = _make_leaf(
                left_rows,
                depth=node.depth + 1,
                arms=arms,
                risk_multiplier=risk_multiplier,
            )
            right = _make_leaf(
                right_rows,
                depth=node.depth + 1,
                arms=arms,
                risk_multiplier=risk_multiplier,
            )
            gain = left.objective + right.objective - node.objective
            candidate = (gain, feature, threshold, left, right)
            if best is None:
                best = candidate
                continue
            if gain > best[0] + TOLERANCE or (
                abs(gain - best[0]) <= TOLERANCE
                and (feature, threshold) < (best[1], best[2])
            ):
                best = candidate
    return best


def _leaf_paths(root: _FitNode) -> list[tuple[tuple[int, ...], _FitNode]]:
    result: list[tuple[tuple[int, ...], _FitNode]] = []

    def walk(node: _FitNode, path: tuple[int, ...]) -> None:
        if node.is_leaf:
            result.append((path, node))
            return
        assert node.left is not None and node.right is not None
        walk(node.left, (*path, 0))
        walk(node.right, (*path, 1))

    walk(root, ())
    return result


def _fit_tree(
    rows: list[dict[str, Any]],
    spec: _CandidateSpec,
    parsed: dict[str, Any],
) -> _FitNode:
    root = _make_leaf(
        rows,
        depth=0,
        arms=parsed["arm_priority"],
        risk_multiplier=spec.risk_multiplier,
    )
    maximum_leaves = 2**spec.maximum_depth
    while len(_leaf_paths(root)) < maximum_leaves:
        candidates = []
        for path, leaf in _leaf_paths(root):
            if leaf.depth >= spec.maximum_depth:
                continue
            split = _best_split(
                leaf,
                features=spec.features,
                arms=parsed["arm_priority"],
                risk_multiplier=spec.risk_multiplier,
                minimum_instances=parsed["minimum_leaf_instances"],
                minimum_groups=parsed["minimum_leaf_groups"],
            )
            if split is not None:
                candidates.append((split[0], path, *split[1:]))
        if not candidates:
            break
        candidates.sort(key=lambda value: (-value[0], value[1], value[2], value[3]))
        gain, _path, feature, threshold, left, right = candidates[0]
        if gain <= TOLERANCE:
            break
        target = dict(_leaf_paths(root))[_path]
        target.feature = feature
        target.threshold = threshold
        target.left = left
        target.right = right
    return root


def _serialize_tree(node: _FitNode) -> dict[str, Any]:
    if node.is_leaf:
        return {"type": "leaf", "arm": node.arm}
    assert node.feature is not None and node.threshold is not None
    assert node.left is not None and node.right is not None
    return {
        "type": "split",
        "feature": node.feature,
        "threshold": node.threshold,
        "left_if": "feature <= threshold",
        "left": _serialize_tree(node.left),
        "right": _serialize_tree(node.right),
    }


def _tree_stats(node: _FitNode) -> dict[str, int]:
    leaves = _leaf_paths(node)
    return {
        "depth": max((leaf.depth for _, leaf in leaves), default=0),
        "leaves": len(leaves),
        "splits": max(0, len(leaves) - 1),
    }


def _predict(tree: dict[str, Any], features: dict[str, float]) -> str:
    node = tree
    while node["type"] == "split":
        value = float(features[str(node["feature"])])
        node = node["left"] if value <= float(node["threshold"]) else node["right"]
    if node["type"] != "leaf":
        raise ValueError("serialized tree contains an unknown node type")
    return str(node["arm"])


def _evaluate_selections(
    rows: list[dict[str, Any]],
    selections: list[str],
    *,
    feature_seconds: float,
    decision_seconds: float,
) -> dict[str, Any]:
    if len(rows) != len(selections):
        raise ValueError("selection count differs from target count")
    raw = 0.0
    normalized = 0.0
    visits = 0
    solve_seconds = 0.0
    maximum_harm = 0.0
    exact_accept_raw = 0.0
    exact_accept_label_seconds = 0.0
    counts: Counter[str] = Counter()
    group_raw: dict[str, float] = defaultdict(float)
    for row, arm in zip(rows, selections, strict=True):
        if arm not in row["arms"]:
            raise ValueError(f"tree selected unknown arm {arm!r}")
        metrics = row["arms"][arm]
        reduction = float(metrics["raw_reduction"])
        raw += reduction
        normalized += float(metrics["normalized_reduction"])
        visits += int(metrics["state_visits"])
        solve_seconds += float(metrics["solve_seconds"])
        maximum_harm = max(maximum_harm, max(0.0, -reduction))
        counts[arm] += 1
        group_raw[str(row["group_id"])] += reduction
        if arm != NO_OP:
            exact_accept_raw += max(0.0, reduction)
            exact_accept_label_seconds += float(metrics["exact_label_seconds"])
    total_seconds = feature_seconds + decision_seconds + solve_seconds
    return {
        "targets": len(rows),
        "selection_counts": dict(sorted(counts.items())),
        "raw_reduction": raw,
        "normalized_reduction": normalized,
        "maximum_target_harm": maximum_harm,
        "state_visits": visits,
        "feature_seconds": feature_seconds,
        "decision_seconds": decision_seconds,
        "solve_seconds": solve_seconds,
        "total_seconds": total_seconds,
        "raw_reduction_per_millisecond": (
            raw / (total_seconds * 1000.0) if total_seconds > 0.0 else None
        ),
        "group_raw_reduction": dict(sorted(group_raw.items())),
        "exact_accept_diagnostic": {
            "uses_future_labels": True,
            "raw_reduction": exact_accept_raw,
            "additional_exact_label_seconds": exact_accept_label_seconds,
            "total_seconds": total_seconds + exact_accept_label_seconds,
            "raw_reduction_per_millisecond": (
                exact_accept_raw
                / ((total_seconds + exact_accept_label_seconds) * 1000.0)
                if total_seconds + exact_accept_label_seconds > 0.0
                else None
            ),
        },
    }


def _evaluate_tree(
    rows: list[dict[str, Any]],
    tree: dict[str, Any],
) -> dict[str, Any]:
    decision_start = time.perf_counter()
    selections = [_predict(tree, row["features"]) for row in rows]
    decision_seconds = time.perf_counter() - decision_start
    return _evaluate_selections(
        rows,
        selections,
        feature_seconds=sum(float(row["boundary_feature_seconds"]) for row in rows),
        decision_seconds=decision_seconds,
    )


def _evaluate_fixed(rows: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    return _evaluate_selections(
        rows,
        [arm] * len(rows),
        feature_seconds=0.0,
        decision_seconds=0.0,
    )


def _compact_oracle(rows: list[dict[str, Any]], arms: tuple[str, ...]) -> dict[str, Any]:
    raw = 0.0
    normalized = 0.0
    counts: Counter[str] = Counter()
    for row in rows:
        arm = max(
            arms,
            key=lambda candidate: float(row["arms"][candidate]["raw_reduction"]),
        )
        raw += float(row["arms"][arm]["raw_reduction"])
        normalized += float(row["arms"][arm]["normalized_reduction"])
        counts[arm] += 1
    return {
        "uses_future_labels": True,
        "raw_reduction": raw,
        "normalized_reduction": normalized,
        "selection_counts": dict(sorted(counts.items())),
    }


def _aggregate_fold_metrics(folds: list[dict[str, Any]]) -> dict[str, Any]:
    additive = (
        "targets",
        "raw_reduction",
        "normalized_reduction",
        "state_visits",
        "feature_seconds",
        "decision_seconds",
        "solve_seconds",
        "total_seconds",
    )
    result: dict[str, Any] = {
        name: sum(float(fold["metrics"][name]) for fold in folds)
        for name in additive
    }
    result["targets"] = int(result["targets"])
    result["state_visits"] = int(result["state_visits"])
    result["maximum_target_harm"] = max(
        float(fold["metrics"]["maximum_target_harm"]) for fold in folds
    )
    counts: Counter[str] = Counter()
    for fold in folds:
        counts.update(fold["metrics"]["selection_counts"])
    result["selection_counts"] = dict(sorted(counts.items()))
    total_seconds = float(result["total_seconds"])
    result["raw_reduction_per_millisecond"] = (
        float(result["raw_reduction"]) / (total_seconds * 1000.0)
        if total_seconds > 0.0
        else None
    )
    return result


def _spec_sort_key(spec: _CandidateSpec) -> tuple[int, int, float, str]:
    return (
        spec.tier_index,
        spec.maximum_depth,
        spec.risk_multiplier,
        spec.candidate_id,
    )


def run_selective_width_screen(
    artifact: dict[str, Any],
    rule: dict[str, Any],
    *,
    source_provenance: dict[str, Any] | None = None,
    rule_provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fit and evaluate only the preregistered grouped discovery screen."""

    parsed = _validate_rule(rule)
    frozen = parsed["frozen_source"]
    if source_provenance is not None and frozen.get("sha256"):
        if str(source_provenance.get("sha256")) != str(frozen["sha256"]):
            raise ValueError("source SHA-256 does not match the frozen rule")
    if artifact.get("config_sha256") != frozen.get("config_sha256"):
        raise ValueError("source config SHA-256 does not match the frozen rule")
    examples = _build_examples(artifact, parsed)
    groups = sorted(_groups(examples))
    if len(groups) != int(frozen["groups"]) or len(examples) != int(frozen["targets"]):
        raise ValueError("source counts do not match the frozen rule")

    fixed = _evaluate_fixed(examples, parsed["fallback"])
    compact_oracle = _compact_oracle(examples, parsed["arm_priority"])
    specs = _candidate_specs(parsed)
    summaries = []
    selected_fold_details: dict[str, list[dict[str, Any]]] = {}
    for spec in specs:
        folds = []
        for held_out in groups:
            training = [row for row in examples if row["group_id"] != held_out]
            evaluation = [row for row in examples if row["group_id"] == held_out]
            fitted = _fit_tree(training, spec, parsed)
            tree = _serialize_tree(fitted)
            metrics = _evaluate_tree(evaluation, tree)
            fixed_fold = _evaluate_fixed(evaluation, parsed["fallback"])
            folds.append(
                {
                    "held_out_group_id": held_out,
                    "training_groups": len(_groups(training)),
                    "training_targets": len(training),
                    "tree": tree,
                    "tree_stats": _tree_stats(fitted),
                    "metrics": metrics,
                    "fixed_metrics": fixed_fold,
                    "raw_uplift_over_fixed": (
                        float(metrics["raw_reduction"])
                        - float(fixed_fold["raw_reduction"])
                    ),
                    "normalized_uplift_over_fixed": (
                        float(metrics["normalized_reduction"])
                        - float(fixed_fold["normalized_reduction"])
                    ),
                }
            )
        aggregate = _aggregate_fold_metrics(folds)
        summaries.append(
            {
                "candidate_id": spec.candidate_id,
                "tier_index": spec.tier_index,
                "tier_name": spec.tier_name,
                "maximum_depth": spec.maximum_depth,
                "risk_multiplier": spec.risk_multiplier,
                "aggregate": aggregate,
                "positive_raw_uplift_group_fraction": mean(
                    float(fold["raw_uplift_over_fixed"]) > TOLERANCE for fold in folds
                ),
            }
        )
        selected_fold_details[spec.candidate_id] = folds

    fixed_normalized = float(fixed["normalized_reduction"])
    selected_spec: _CandidateSpec | None = None
    selected_summary: dict[str, Any] | None = None
    ordered_candidates = sorted(
        zip(specs, summaries, strict=True),
        key=lambda pair: _spec_sort_key(pair[0]),
    )
    for spec, summary in ordered_candidates:
        value = float(summary["aggregate"]["normalized_reduction"])
        if value <= fixed_normalized + TOLERANCE:
            continue
        if selected_summary is None:
            selected_spec = spec
            selected_summary = summary
            continue
        best_value = float(selected_summary["aggregate"]["normalized_reduction"])
        if value > best_value + TOLERANCE:
            selected_spec = spec
            selected_summary = summary

    if selected_spec is None or selected_summary is None:
        selected_candidate_id = "fixed_b3r2"
        selected_metrics = fixed
        selected_folds: list[dict[str, Any]] = []
        positive_group_fraction = 0.0
    else:
        selected_candidate_id = selected_spec.candidate_id
        selected_metrics = selected_summary["aggregate"]
        selected_folds = selected_fold_details[selected_candidate_id]
        positive_group_fraction = float(
            selected_summary["positive_raw_uplift_group_fraction"]
        )

    fixed_raw = float(fixed["raw_reduction"])
    fixed_normalized = float(fixed["normalized_reduction"])
    candidate_raw = float(selected_metrics["raw_reduction"])
    candidate_normalized = float(selected_metrics["normalized_reduction"])
    oracle_opportunity = float(compact_oracle["raw_reduction"]) - fixed_raw
    actual_uplift = candidate_raw - fixed_raw
    capture = actual_uplift / oracle_opportunity if oracle_opportunity > 0.0 else None
    gates_config = parsed["gates"]
    gate_results = {
        "minimum_board_groups": len(groups) >= int(gates_config["minimum_board_groups"]),
        "aggregate_raw_reduction_strictly_beats_fixed_b3r2": (
            candidate_raw > fixed_raw + TOLERANCE
        ),
        "aggregate_normalized_reduction_strictly_beats_fixed_b3r2": (
            candidate_normalized > fixed_normalized + TOLERANCE
        ),
        "minimum_positive_raw_uplift_group_fraction": (
            positive_group_fraction
            >= float(gates_config["minimum_positive_raw_uplift_group_fraction"])
        ),
        "minimum_compact_oracle_opportunity_capture_fraction": (
            capture is not None
            and capture
            >= float(
                gates_config["minimum_compact_oracle_opportunity_capture_fraction"]
            )
        ),
        "aggregate_state_visits_not_above_fixed_b3r2": (
            int(selected_metrics["state_visits"]) <= int(fixed["state_visits"])
        ),
        "charged_raw_reduction_per_millisecond_strictly_beats_fixed_b3r2": (
            float(selected_metrics["raw_reduction_per_millisecond"])
            > float(fixed["raw_reduction_per_millisecond"])
        ),
        "maximum_selected_target_harm_not_above_fixed_b3r2": (
            float(selected_metrics["maximum_target_harm"])
            <= float(fixed["maximum_target_harm"]) + TOLERANCE
        ),
    }
    passed = all(gate_results.values())

    all_development = None
    if selected_spec is not None:
        fitted = _fit_tree(examples, selected_spec, parsed)
        tree = _serialize_tree(fitted)
        all_development = {
            "candidate_id": selected_spec.candidate_id,
            "specification": {
                "tier_index": selected_spec.tier_index,
                "tier_name": selected_spec.tier_name,
                "features": list(selected_spec.features),
                "maximum_depth": selected_spec.maximum_depth,
                "risk_multiplier": selected_spec.risk_multiplier,
            },
            "tree": tree,
            "tree_stats": _tree_stats(fitted),
            "in_sample_metrics": _evaluate_tree(examples, tree),
        }

    leaderboard = sorted(
        summaries,
        key=lambda row: (
            -float(row["aggregate"]["normalized_reduction"]),
            int(row["tier_index"]),
            int(row["maximum_depth"]),
            float(row["risk_multiplier"]),
            str(row["candidate_id"]),
        ),
    )
    return {
        "schema_version": 1,
        "experiment_type": "river_selective_width_discovery_screen",
        "status": (
            "development_screen_passed_freeze_rule_before_replication"
            if passed
            else "development_screen_failed_retain_full_b3r2"
        ),
        "source_provenance": source_provenance,
        "rule_provenance": rule_provenance,
        "rule_id": rule["rule_id"],
        "selection_authorized": False,
        "replication_authorized": passed,
        "reserved_validation_or_test_authorized": False,
        "native_specialization_authorized": False,
        "counts": {
            "groups": len(groups),
            "targets": len(examples),
            "adaptive_candidate_specifications": len(specs),
            "leave_one_group_out_folds": len(groups),
        },
        "fixed_b3r2": fixed,
        "compact_oracle": compact_oracle,
        "compact_oracle_raw_opportunity_over_fixed": oracle_opportunity,
        "cross_validated_selection": {
            "selected_candidate_id": selected_candidate_id,
            "selected_metrics": selected_metrics,
            "raw_uplift_over_fixed": actual_uplift,
            "normalized_uplift_over_fixed": candidate_normalized - fixed_normalized,
            "positive_raw_uplift_group_fraction": positive_group_fraction,
            "compact_oracle_opportunity_capture_fraction": capture,
            "selected_fold_details": selected_folds,
        },
        "leaderboard": leaderboard,
        "all_development_fit": all_development,
        "selection_gates": {"passed": passed, "results": gate_results},
        "interpretation_limits": {
            "discovery_source_was_previously_revealed": True,
            "feature_family_was_designed_from_discovery_diagnostics": True,
            "exact_labels_used_only_for_offline_training_and_evaluation": True,
            "solver_probe_features_used": False,
            "exact_accept_diagnostic_is_not_causal": True,
            "fresh_replication_required_before_transfer_claim": True,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--rule", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    source, source_provenance = _read_with_provenance(args.source)
    rule, rule_provenance = _read_with_provenance(args.rule)
    result = run_selective_width_screen(
        source,
        rule,
        source_provenance=source_provenance,
        rule_provenance=rule_provenance,
    )
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "selective width screen: "
        f"passed={result['selection_gates']['passed']}, "
        f"selected={result['cross_validated_selection']['selected_candidate_id']}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
