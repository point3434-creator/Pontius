"""Cross-validate the frozen transparent river post-probe scheduler family."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any

from .river_opportunity import _pooled_iteration_oracle

TOLERANCE = 1e-12
FIXED_CANDIDATE_ID = "fixed_checkpoint_4"


def _fold(group_id: str, folds: int) -> int:
    return int.from_bytes(
        hashlib.sha256(group_id.encode("utf-8")).digest()[:8],
        "big",
    ) % folds


def _average_ranks(values: list[float]) -> list[float]:
    if not values:
        return []
    if len(values) == 1:
        return [0.5]
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    start = 0
    while start < len(values):
        stop = start + 1
        while stop < len(values) and values[order[stop]] == values[order[start]]:
            stop += 1
        rank = ((start + stop - 1) / 2.0) / (len(values) - 1)
        for index in range(start, stop):
            ranks[order[index]] = rank
        start = stop
    return ranks


def _scores(
    contexts: dict[str, dict[str, Any]],
    score_rule: dict[str, Any],
) -> tuple[dict[str, float], bool]:
    context_ids = sorted(contexts)
    totals = {context_id: 0.0 for context_id in context_ids}
    total_weight = 0.0
    uses_shadow = False
    terms = score_rule.get("terms")
    if not isinstance(terms, list) or not terms:
        raise ValueError("every score must contain terms")
    for term in terms:
        feature = str(term["feature"])
        direction = str(term["direction"])
        weight = float(term["weight"])
        if direction not in {"high", "low"}:
            raise ValueError(f"unsupported score direction {direction!r}")
        if not math.isfinite(weight) or weight <= 0.0:
            raise ValueError("score weights must be finite and positive")
        try:
            values = [
                float(contexts[context_id]["features"][feature])
                for context_id in context_ids
            ]
        except KeyError as error:
            raise ValueError(f"score feature {feature!r} is unavailable") from error
        if direction == "low":
            values = [-value for value in values]
        ranks = _average_ranks(values)
        for context_id, rank in zip(context_ids, ranks, strict=True):
            totals[context_id] += weight * rank
        total_weight += weight
        uses_shadow = uses_shadow or feature.startswith("shadow_")
    return (
        {context_id: total / total_weight for context_id, total in totals.items()},
        uses_shadow,
    )


def _allocate(
    contexts: dict[str, dict[str, Any]],
    scores: dict[str, float],
    macro: dict[str, Any],
    *,
    probe_checkpoint: int,
    fixed_checkpoint: int,
) -> dict[str, int]:
    """Fund high-score promotions without exceeding iterations or state work."""

    recipient_checkpoint = int(macro["recipient_checkpoint"])
    fraction = float(macro["maximum_recipient_fraction"])
    if not 0.0 < fraction <= 0.5:
        raise ValueError("recipient fraction must be in (0, 0.5]")
    if recipient_checkpoint <= fixed_checkpoint:
        raise ValueError("recipient checkpoint must exceed the fixed checkpoint")
    context_ids = sorted(contexts)
    recipient_count = math.floor(len(context_ids) * fraction)
    ranked_high = sorted(context_ids, key=lambda item: (-scores[item], item))
    recipient_candidates = ranked_high[:recipient_count]
    recipient_set = set(recipient_candidates)
    donors = sorted(
        (context_id for context_id in context_ids if context_id not in recipient_set),
        key=lambda item: (scores[item], item),
    )

    selected = {context_id: fixed_checkpoint for context_id in context_ids}
    iteration_credit = 0
    state_credit = 0
    demoted: list[str] = []
    donor_index = 0
    for recipient in recipient_candidates:
        iteration_cost = recipient_checkpoint - fixed_checkpoint
        state_cost = (
            contexts[recipient]["checkpoints"][recipient_checkpoint]["state_visits"]
            - contexts[recipient]["checkpoints"][fixed_checkpoint]["state_visits"]
        )
        while (
            iteration_credit < iteration_cost or state_credit < state_cost
        ) and donor_index < len(donors):
            donor = donors[donor_index]
            donor_index += 1
            selected[donor] = probe_checkpoint
            demoted.append(donor)
            iteration_credit += fixed_checkpoint - probe_checkpoint
            state_credit += (
                contexts[donor]["checkpoints"][fixed_checkpoint]["state_visits"]
                - contexts[donor]["checkpoints"][probe_checkpoint]["state_visits"]
            )
        if iteration_credit < iteration_cost or state_credit < state_cost:
            break
        selected[recipient] = recipient_checkpoint
        iteration_credit -= iteration_cost
        state_credit -= state_cost

    # Remove needless demotions, preferring to restore the stronger donors.
    for donor in sorted(demoted, key=lambda item: (-scores[item], item)):
        iteration_cost = fixed_checkpoint - probe_checkpoint
        state_cost = (
            contexts[donor]["checkpoints"][fixed_checkpoint]["state_visits"]
            - contexts[donor]["checkpoints"][probe_checkpoint]["state_visits"]
        )
        if iteration_credit >= iteration_cost and state_credit >= state_cost:
            selected[donor] = fixed_checkpoint
            iteration_credit -= iteration_cost
            state_credit -= state_cost

    fixed_iterations = fixed_checkpoint * len(context_ids)
    fixed_states = sum(
        context["checkpoints"][fixed_checkpoint]["state_visits"]
        for context in contexts.values()
    )
    if sum(selected.values()) > fixed_iterations:
        raise AssertionError("adaptive allocation exceeded the fixed iteration budget")
    selected_states = sum(
        contexts[context_id]["checkpoints"][checkpoint]["state_visits"]
        for context_id, checkpoint in selected.items()
    )
    if selected_states > fixed_states:
        raise AssertionError("adaptive allocation exceeded the fixed state-work budget")
    return selected


def _candidate_specs(rule: dict[str, Any]) -> list[dict[str, Any]]:
    scores = rule.get("scores")
    macros = rule.get("macro_options")
    if not isinstance(scores, list) or not scores:
        raise ValueError("rule must contain scores")
    if not isinstance(macros, list) or not macros:
        raise ValueError("rule must contain macro options")
    score_names = [str(score["name"]) for score in scores]
    macro_names = [str(macro["name"]) for macro in macros]
    if len(set(score_names)) != len(score_names):
        raise ValueError("score names must be unique")
    if len(set(macro_names)) != len(macro_names):
        raise ValueError("macro names must be unique")
    result = [{"candidate_id": FIXED_CANDIDATE_ID, "fixed": True}]
    for score in scores:
        for macro in macros:
            result.append(
                {
                    "candidate_id": f"{score['name']}::{macro['name']}",
                    "fixed": False,
                    "score": score,
                    "macro": macro,
                }
            )
    return result


def _evaluate_candidate(
    contexts: dict[str, dict[str, Any]],
    candidate: dict[str, Any],
    *,
    probe_checkpoint: int,
    fixed_checkpoint: int,
) -> dict[str, Any]:
    decision_start = time.perf_counter()
    if candidate["fixed"]:
        selected = {context_id: fixed_checkpoint for context_id in contexts}
        uses_shadow = False
        feature_milliseconds = 0.0
    else:
        scores, uses_shadow = _scores(contexts, candidate["score"])
        selected = _allocate(
            contexts,
            scores,
            candidate["macro"],
            probe_checkpoint=probe_checkpoint,
            fixed_checkpoint=fixed_checkpoint,
        )
        feature_key = (
            "shadow_feature_overhead_milliseconds"
            if uses_shadow
            else "active_feature_overhead_milliseconds"
        )
        feature_milliseconds = sum(
            float(context[feature_key]) for context in contexts.values()
        )
    decision_milliseconds = (time.perf_counter() - decision_start) * 1_000.0
    if candidate["fixed"]:
        decision_milliseconds = 0.0

    initial_exploitability = sum(
        float(context["checkpoints"][0]["exploitability"])
        for context in contexts.values()
    )
    fixed_final_exploitability = sum(
        float(context["checkpoints"][fixed_checkpoint]["exploitability"])
        for context in contexts.values()
    )
    candidate_final_exploitability = sum(
        float(contexts[context_id]["checkpoints"][checkpoint]["exploitability"])
        for context_id, checkpoint in selected.items()
    )
    fixed_solver_milliseconds = sum(
        float(context["checkpoints"][fixed_checkpoint]["solver_milliseconds"])
        for context in contexts.values()
    )
    candidate_solver_milliseconds = sum(
        float(contexts[context_id]["checkpoints"][checkpoint]["solver_milliseconds"])
        for context_id, checkpoint in selected.items()
    )
    fixed_reduction = initial_exploitability - fixed_final_exploitability
    candidate_reduction = initial_exploitability - candidate_final_exploitability
    candidate_total_milliseconds = (
        candidate_solver_milliseconds
        + feature_milliseconds
        + decision_milliseconds
    )
    selection_counts: dict[str, int] = {}
    for checkpoint in selected.values():
        key = str(checkpoint)
        selection_counts[key] = selection_counts.get(key, 0) + 1
    fixed_states = sum(
        int(context["checkpoints"][fixed_checkpoint]["state_visits"])
        for context in contexts.values()
    )
    candidate_states = sum(
        int(contexts[context_id]["checkpoints"][checkpoint]["state_visits"])
        for context_id, checkpoint in selected.items()
    )
    return {
        "candidate_id": candidate["candidate_id"],
        "contexts": len(contexts),
        "uses_shadow": uses_shadow,
        "selection_counts": dict(sorted(selection_counts.items())),
        "fixed_final_exploitability": fixed_final_exploitability,
        "candidate_final_exploitability": candidate_final_exploitability,
        "raw_exploitability_uplift_over_fixed": (
            fixed_final_exploitability - candidate_final_exploitability
        ),
        "fixed_reduction_from_checkpoint_zero": fixed_reduction,
        "candidate_reduction_from_checkpoint_zero": candidate_reduction,
        "fixed_iterations": fixed_checkpoint * len(contexts),
        "candidate_iterations": sum(selected.values()),
        "fixed_state_visits": fixed_states,
        "candidate_state_visits": candidate_states,
        "fixed_solver_milliseconds": fixed_solver_milliseconds,
        "candidate_solver_milliseconds": candidate_solver_milliseconds,
        "charged_feature_milliseconds": feature_milliseconds,
        "charged_decision_milliseconds": decision_milliseconds,
        "candidate_total_milliseconds": candidate_total_milliseconds,
        "fixed_reduction_per_millisecond": (
            fixed_reduction / fixed_solver_milliseconds
            if fixed_solver_milliseconds > 0.0
            else None
        ),
        "candidate_reduction_per_millisecond": (
            candidate_reduction / candidate_total_milliseconds
            if candidate_total_milliseconds > 0.0
            else None
        ),
    }


def _choose_candidate(leaderboard: list[dict[str, Any]]) -> dict[str, Any]:
    fixed = next(
        row for row in leaderboard if row["candidate_id"] == FIXED_CANDIDATE_ID
    )
    best = fixed
    for row in sorted(leaderboard, key=lambda item: str(item["candidate_id"])):
        uplift = float(row["raw_exploitability_uplift_over_fixed"])
        best_uplift = float(best["raw_exploitability_uplift_over_fixed"])
        if uplift > best_uplift + TOLERANCE:
            best = row
        elif (
            abs(uplift - best_uplift) <= TOLERANCE
            and best["candidate_id"] != FIXED_CANDIDATE_ID
            and row["candidate_id"] != FIXED_CANDIDATE_ID
            and str(row["candidate_id"]) < str(best["candidate_id"])
        ):
            best = row
    return best


def _build_contexts(
    source: dict[str, Any],
    shadow: dict[str, Any],
    required_checkpoints: set[int],
) -> dict[str, dict[str, Any]]:
    source_contexts = {
        str(context["context_id"]): context for context in source["contexts"]
    }
    shadow_rows = {
        str(row["context_id"]): row for row in shadow["records"]
    }
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in source["records"]:
        if record["solver"] == "dcfr":
            grouped.setdefault(str(record["context_id"]), []).append(record)
    if set(source_contexts) != set(grouped) or set(source_contexts) != set(shadow_rows):
        raise ValueError("source, DCFR, and shadow context identities differ")

    contexts = {}
    for context_id, source_context in source_contexts.items():
        shadow_row = shadow_rows[context_id]
        if source_context["split"] != "development" or shadow_row["split"] != "development":
            raise ValueError("scheduler screen is restricted to development contexts")
        if source_context["provenance_digest"] != shadow_row["provenance_digest"]:
            raise ValueError(f"shadow provenance mismatch for {context_id!r}")
        rows = sorted(grouped[context_id], key=lambda row: int(row["checkpoint"]))
        by_checkpoint = {int(row["checkpoint"]): row for row in rows}
        if not required_checkpoints <= set(by_checkpoint):
            raise ValueError(f"required checkpoints are missing for {context_id!r}")
        probe_checkpoint = int(shadow_row["checkpoint"])
        probe_row = by_checkpoint[probe_checkpoint]
        source_active = float(
            probe_row["online_features"]["normalized_positive_regret_mass"]
        )
        shadow_active = float(
            shadow_row["online_features"]["normalized_positive_regret_mass"]
        )
        if abs(source_active - shadow_active) > TOLERANCE:
            raise ValueError(f"shadow active feature mismatch for {context_id!r}")
        features = dict(probe_row["online_features"])
        features.update(
            {
                name: value
                for name, value in shadow_row["online_features"].items()
                if name.startswith("shadow_")
            }
        )
        contexts[context_id] = {
            "group_id": str(source_context["group_id"]),
            "features": features,
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
            "active_feature_overhead_milliseconds": float(
                shadow_row["timing"][
                    "plain_active_feature_summary_milliseconds"
                ]
            ),
            "shadow_feature_overhead_milliseconds": float(
                shadow_row["timing"][
                    "conservative_instrumentation_overhead_milliseconds"
                ]
            ),
        }
    return contexts


def run_river_scheduler_screen(
    source: dict[str, Any],
    shadow: dict[str, Any],
    rule: dict[str, Any],
    *,
    source_provenance: dict[str, Any] | None = None,
    shadow_provenance: dict[str, Any] | None = None,
    rule_provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run only the preregistered development cross-validation procedure."""

    if source.get("experiment_type") != "exact_river_early_opportunity_trace":
        raise ValueError("source is not an exact river opportunity trace")
    if shadow.get("experiment_type") != "exact_river_shadow_regret_probe":
        raise ValueError("shadow input is not an exact river shadow probe")
    if rule.get("status") != "preregistered_development_only":
        raise ValueError("scheduler rule is not preregistered for development")
    frozen_source = rule["frozen_source"]
    if source_provenance is not None and frozen_source.get("sha256"):
        if source_provenance.get("sha256") != frozen_source["sha256"]:
            raise ValueError("source SHA-256 does not match the frozen rule")
    embedded_source = shadow.get("source_provenance")
    if (
        source_provenance is not None
        and embedded_source is not None
        and embedded_source.get("sha256") != source_provenance.get("sha256")
    ):
        raise ValueError("shadow probe was generated from another source artifact")

    solver_rule = rule["solver"]
    if solver_rule != {
        "active_variant": "dcfr",
        "fixed_checkpoint": 4,
        "probe_checkpoint": 2,
        "shadow_regret_variant": "cfr_plus",
    }:
        raise ValueError("this screen implements the frozen DCFR/CFR+ checkpoint rule")
    fixed_checkpoint = int(solver_rule["fixed_checkpoint"])
    probe_checkpoint = int(solver_rule["probe_checkpoint"])
    required_checkpoints = {
        int(checkpoint) for checkpoint in rule["allocator"]["required_checkpoints"]
    }
    contexts = _build_contexts(source, shadow, required_checkpoints)
    expected_contexts = frozen_source.get("contexts")
    if expected_contexts is not None and len(contexts) != int(expected_contexts):
        raise ValueError("context count does not match the frozen rule")

    folds = int(rule["folds"]["count"])
    if folds <= 1:
        raise ValueError("fold count must exceed one")
    fold_by_context = {
        context_id: _fold(context["group_id"], folds)
        for context_id, context in contexts.items()
    }
    if set(fold_by_context.values()) != set(range(folds)):
        raise ValueError("one or more group-preserving folds are empty")

    specs = _candidate_specs(rule)
    spec_by_id = {str(spec["candidate_id"]): spec for spec in specs}
    fold_results = []
    for held_out_fold in range(folds):
        training = {
            context_id: context
            for context_id, context in contexts.items()
            if fold_by_context[context_id] != held_out_fold
        }
        held_out = {
            context_id: context
            for context_id, context in contexts.items()
            if fold_by_context[context_id] == held_out_fold
        }
        training_leaderboard = [
            _evaluate_candidate(
                training,
                spec,
                probe_checkpoint=probe_checkpoint,
                fixed_checkpoint=fixed_checkpoint,
            )
            for spec in specs
        ]
        chosen_training = _choose_candidate(training_leaderboard)
        selected_spec = spec_by_id[str(chosen_training["candidate_id"])]
        held_out_metrics = _evaluate_candidate(
            held_out,
            selected_spec,
            probe_checkpoint=probe_checkpoint,
            fixed_checkpoint=fixed_checkpoint,
        )
        oracle = _pooled_iteration_oracle(
            [context["rows"] for context in held_out.values()],
            average_budget=fixed_checkpoint,
            minimum_checkpoint=probe_checkpoint,
        )
        perfect_uplift = (
            float(oracle["pooled_perfect_information_total_reduction"])
            - float(oracle["fixed_checkpoint_total_reduction"])
        )
        actual_uplift = float(
            held_out_metrics["raw_exploitability_uplift_over_fixed"]
        )
        fold_results.append(
            {
                "held_out_fold": held_out_fold,
                "training_contexts": len(training),
                "held_out_contexts": len(held_out),
                "selected_candidate_id": selected_spec["candidate_id"],
                "training_raw_uplift": chosen_training[
                    "raw_exploitability_uplift_over_fixed"
                ],
                "held_out": held_out_metrics,
                "perfect_post_probe_uplift": perfect_uplift,
                "fraction_of_perfect_post_probe_uplift": (
                    actual_uplift / perfect_uplift
                    if perfect_uplift > TOLERANCE
                    else None
                ),
            }
        )

    all_development_leaderboard = [
        _evaluate_candidate(
            contexts,
            spec,
            probe_checkpoint=probe_checkpoint,
            fixed_checkpoint=fixed_checkpoint,
        )
        for spec in specs
    ]
    all_development_choice = _choose_candidate(all_development_leaderboard)

    aggregate_actual_uplift = sum(
        float(fold["held_out"]["raw_exploitability_uplift_over_fixed"])
        for fold in fold_results
    )
    aggregate_perfect_uplift = sum(
        float(fold["perfect_post_probe_uplift"]) for fold in fold_results
    )
    candidate_reduction = sum(
        float(fold["held_out"]["candidate_reduction_from_checkpoint_zero"])
        for fold in fold_results
    )
    fixed_reduction = sum(
        float(fold["held_out"]["fixed_reduction_from_checkpoint_zero"])
        for fold in fold_results
    )
    candidate_milliseconds = sum(
        float(fold["held_out"]["candidate_total_milliseconds"])
        for fold in fold_results
    )
    fixed_milliseconds = sum(
        float(fold["held_out"]["fixed_solver_milliseconds"])
        for fold in fold_results
    )
    candidate_rate = candidate_reduction / candidate_milliseconds
    fixed_rate = fixed_reduction / fixed_milliseconds
    gates = {
        "strict_raw_improvement_in_every_fold": all(
            float(fold["held_out"]["raw_exploitability_uplift_over_fixed"])
            > TOLERANCE
            for fold in fold_results
        ),
        "aggregate_perfect_uplift_capture_at_least_25_percent": (
            aggregate_perfect_uplift > TOLERANCE
            and aggregate_actual_uplift / aggregate_perfect_uplift >= 0.25
        ),
        "aggregate_iterations_not_above_fixed": sum(
            int(fold["held_out"]["candidate_iterations"])
            for fold in fold_results
        )
        <= sum(
            int(fold["held_out"]["fixed_iterations"]) for fold in fold_results
        ),
        "aggregate_state_visits_not_above_fixed": sum(
            int(fold["held_out"]["candidate_state_visits"])
            for fold in fold_results
        )
        <= sum(
            int(fold["held_out"]["fixed_state_visits"]) for fold in fold_results
        ),
        "aggregate_measured_reduction_per_millisecond_beats_fixed": (
            candidate_rate > fixed_rate
        ),
    }
    passed = all(gates.values())
    return {
        "schema_version": 1,
        "experiment_type": "exact_river_post_probe_scheduler_screen",
        "status": (
            "development_gate_passed_freeze_before_reserved"
            if passed
            else "development_gate_failed_keep_fixed_checkpoint"
        ),
        "source_provenance": source_provenance,
        "shadow_provenance": shadow_provenance,
        "rule_provenance": rule_provenance,
        "rule_id": rule["rule_id"],
        "counts": {
            "contexts": len(contexts),
            "groups": len({context["group_id"] for context in contexts.values()}),
            "folds": folds,
            "adaptive_candidates": len(specs) - 1,
        },
        "cross_validation": fold_results,
        "aggregate_cross_validation": {
            "raw_exploitability_uplift_over_fixed": aggregate_actual_uplift,
            "perfect_post_probe_uplift": aggregate_perfect_uplift,
            "fraction_of_perfect_post_probe_uplift": (
                aggregate_actual_uplift / aggregate_perfect_uplift
                if aggregate_perfect_uplift > TOLERANCE
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
        "development_gates": gates,
        "development_gate_passed": passed,
        "all_development_selection": {
            "selected_candidate_id": all_development_choice["candidate_id"],
            "selected_metrics": all_development_choice,
            "leaderboard": sorted(
                all_development_leaderboard,
                key=lambda row: (
                    -float(row["raw_exploitability_uplift_over_fixed"]),
                    str(row["candidate_id"]),
                ),
            ),
        },
        "reserved_contexts_constructed": False,
        "interpretation_warnings": [
            "Candidate selection and all reported outcomes use development board groups only.",
            "The perfect post-probe denominator sees exact future labels and is not deployable.",
            "Measured timing combines source solver intervals with conservatively "
            "charged paired probe overhead.",
            "A development pass authorizes freezing one rule, not inspecting "
            "reserved contexts in this run.",
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
    parser.add_argument("--shadow", required=True, type=Path)
    parser.add_argument("--rule", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    source, source_provenance = _read_with_provenance(args.source)
    shadow, shadow_provenance = _read_with_provenance(args.shadow)
    rule, rule_provenance = _read_with_provenance(args.rule)
    result = run_river_scheduler_screen(
        source,
        shadow,
        rule,
        source_provenance=source_provenance,
        shadow_provenance=shadow_provenance,
        rule_provenance=rule_provenance,
    )
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "river scheduler screen: "
        f"passed={result['development_gate_passed']}, "
        f"selected={result['all_development_selection']['selected_candidate_id']}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
