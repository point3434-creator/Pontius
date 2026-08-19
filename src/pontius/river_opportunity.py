"""Generate exact early-solve opportunity traces on range-sensitive rivers."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from math import log
from pathlib import Path
from statistics import mean, median
from typing import Any

from .cfr import TabularCFR
from .evaluation import (
    Policy,
    collect_information_sets,
    counterfactual_regret_profile,
    evaluate_profile,
    policy_distribution,
)
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, GameState
from .reporting import environment_metadata, json_policy
from .river_context import (
    CONTEXT_FAMILIES,
    CONTEXT_SPLITS,
    generate_river_contexts,
    river_context_features,
    serialize_river_context,
)
from .river_oracle import solve_river_game
from .updates import UPDATE_RULES

DEFAULT_CHECKPOINTS = (0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64)
FORBIDDEN_ONLINE_FEATURE_FRAGMENTS = (
    "exploit",
    "nash",
    "oracle",
    "best_response",
    "future",
    "gain",
    "label",
)
TOLERANCE = 1e-12


def _full_tree_state_count(state: GameState) -> int:
    """Count states visited by one exhaustive traversal, including terminals."""

    player = state.current_player
    if player == TERMINAL_PLAYER:
        return 1
    actions = (
        tuple(action for action, _ in state.chance_outcomes())
        if player == CHANCE_PLAYER
        else tuple(state.legal_actions())
    )
    return 1 + sum(
        _full_tree_state_count(state.apply_action(action))
        for action in actions
    )


def _policy_entropy(
    policy: Policy,
    information_sets: dict[str, tuple[Action, ...]],
) -> float:
    entropies = []
    for key, actions in information_sets.items():
        distribution = policy_distribution(policy, key, actions)
        entropies.append(
            -sum(
                probability * log(probability)
                for probability in distribution.values()
                if probability > 0.0
            )
        )
    return mean(entropies) if entropies else 0.0


def _policy_tv_summary(
    first: Policy,
    second: Policy,
    information_sets: dict[str, tuple[Action, ...]],
) -> tuple[float, float]:
    distances = []
    for key, actions in information_sets.items():
        left = policy_distribution(first, key, actions)
        right = policy_distribution(second, key, actions)
        distances.append(
            0.5 * sum(abs(left[action] - right[action]) for action in actions)
        )
    return (
        mean(distances) if distances else 0.0,
        max(distances, default=0.0),
    )


def _solver_online_features(
    solver: TabularCFR,
    information_sets: dict[str, tuple[Action, ...]],
    previous_average_policy: Policy,
    payoff_span: float,
) -> tuple[dict[str, float | int], Policy]:
    average_policy = solver.average_strategy()
    current_policy = solver.current_strategy()
    regrets = [
        regret
        for data in solver.information_sets.values()
        for regret in data.regrets.values()
    ]
    positives = [max(0.0, regret) for regret in regrets]
    positive_mass = sum(positives)
    negative_mass = sum(max(0.0, -regret) for regret in regrets)
    previous_mean_tv, previous_max_tv = _policy_tv_summary(
        average_policy,
        previous_average_policy,
        information_sets,
    )
    current_mean_tv, current_max_tv = _policy_tv_summary(
        average_policy,
        current_policy,
        information_sets,
    )
    return (
        {
            "materialized_information_sets": len(solver.information_sets),
            "positive_regret_mass": positive_mass,
            "negative_regret_mass": negative_mass,
            "normalized_positive_regret_mass": positive_mass / payoff_span,
            "normalized_negative_regret_mass": negative_mass / payoff_span,
            "maximum_positive_regret": max(positives, default=0.0),
            "positive_regret_concentration": (
                sum((regret / positive_mass) ** 2 for regret in positives)
                if positive_mass > 0.0
                else 0.0
            ),
            "average_policy_entropy": _policy_entropy(
                average_policy, information_sets
            ),
            "current_policy_entropy": _policy_entropy(
                current_policy, information_sets
            ),
            "mean_average_policy_movement_from_previous_checkpoint": previous_mean_tv,
            "max_average_policy_movement_from_previous_checkpoint": previous_max_tv,
            "mean_current_to_average_policy_tv": current_mean_tv,
            "max_current_to_average_policy_tv": current_max_tv,
        },
        average_policy,
    )


def _validate_online_features(features: dict[str, object]) -> None:
    forbidden = [
        name
        for name in features
        if any(fragment in name for fragment in FORBIDDEN_ONLINE_FEATURE_FRAGMENTS)
    ]
    if forbidden:
        raise AssertionError(f"diagnostic labels leaked into online features: {forbidden!r}")


def _annotate_future_labels(records: list[dict[str, Any]]) -> None:
    start_exploitability = float(records[0]["labels"]["exploitability"])
    for index, record in enumerate(records):
        current = float(record["labels"]["exploitability"])
        current_features = record["online_features"]
        payoff_span = float(current_features["payoff_span"])
        current_state_visits = int(
            current_features["cumulative_alternating_state_visits"]
        )
        current_milliseconds = float(
            current_features["cumulative_solver_milliseconds"]
        )
        future = records[index + 1 :]
        labels = record["labels"]
        labels["reduction_from_start"] = start_exploitability - current
        labels["fraction_of_start_exploitability_removed"] = (
            (start_exploitability - current) / start_exploitability
            if start_exploitability > TOLERANCE
            else 0.0
        )
        if not future:
            labels.update(
                {
                    "next_checkpoint_reduction": None,
                    "future_best_additional_reduction": 0.0,
                    "future_best_checkpoint": record["checkpoint"],
                    "first_future_improvement_checkpoint": None,
                    "future_improvement_positive": False,
                    "next_checkpoint_additional_state_visits": None,
                    "next_checkpoint_additional_solver_milliseconds": None,
                    "next_checkpoint_normalized_reduction_per_thousand_state_visits": None,
                    "next_checkpoint_normalized_reduction_per_solver_millisecond": None,
                    "best_future_normalized_reduction_per_thousand_state_visits": 0.0,
                    "best_state_rate_future_checkpoint": record["checkpoint"],
                    "best_future_normalized_reduction_per_solver_millisecond": 0.0,
                    "best_millisecond_rate_future_checkpoint": record["checkpoint"],
                }
            )
            continue
        next_exploitability = float(future[0]["labels"]["exploitability"])
        next_features = future[0]["online_features"]
        next_state_cost = (
            int(next_features["cumulative_alternating_state_visits"])
            - current_state_visits
        )
        next_millisecond_cost = (
            float(next_features["cumulative_solver_milliseconds"])
            - current_milliseconds
        )
        if next_state_cost <= 0 or next_millisecond_cost < 0.0:
            raise AssertionError("future solver costs must increase monotonically")
        signed_next_normalized_reduction = (
            current - next_exploitability
        ) / payoff_span
        best_future = min(
            future,
            key=lambda candidate: float(candidate["labels"]["exploitability"]),
        )
        first_improvement = next(
            (
                candidate
                for candidate in future
                if float(candidate["labels"]["exploitability"])
                < current - TOLERANCE
            ),
            None,
        )
        additional = max(
            0.0,
            current - float(best_future["labels"]["exploitability"]),
        )
        best_state_rate = 0.0
        best_state_rate_checkpoint = int(record["checkpoint"])
        best_millisecond_rate = 0.0
        best_millisecond_rate_checkpoint = int(record["checkpoint"])
        for candidate in future:
            candidate_features = candidate["online_features"]
            normalized_gain = max(
                0.0,
                current - float(candidate["labels"]["exploitability"]),
            ) / payoff_span
            state_cost = (
                int(candidate_features["cumulative_alternating_state_visits"])
                - current_state_visits
            )
            millisecond_cost = (
                float(candidate_features["cumulative_solver_milliseconds"])
                - current_milliseconds
            )
            if state_cost <= 0 or millisecond_cost < 0.0:
                raise AssertionError("future solver costs must increase monotonically")
            state_rate = normalized_gain / (state_cost / 1_000.0)
            if state_rate > best_state_rate + TOLERANCE:
                best_state_rate = state_rate
                best_state_rate_checkpoint = int(candidate["checkpoint"])
            if millisecond_cost > 0.0:
                millisecond_rate = normalized_gain / millisecond_cost
                if millisecond_rate > best_millisecond_rate + TOLERANCE:
                    best_millisecond_rate = millisecond_rate
                    best_millisecond_rate_checkpoint = int(candidate["checkpoint"])
        labels.update(
            {
                "next_checkpoint_reduction": current - next_exploitability,
                "future_best_additional_reduction": additional,
                "future_best_checkpoint": best_future["checkpoint"],
                "first_future_improvement_checkpoint": (
                    None if first_improvement is None else first_improvement["checkpoint"]
                ),
                "future_improvement_positive": first_improvement is not None,
                "next_checkpoint_additional_state_visits": next_state_cost,
                "next_checkpoint_additional_solver_milliseconds": (
                    next_millisecond_cost
                ),
                "next_checkpoint_normalized_reduction_per_thousand_state_visits": (
                    signed_next_normalized_reduction
                    / (next_state_cost / 1_000.0)
                ),
                "next_checkpoint_normalized_reduction_per_solver_millisecond": (
                    signed_next_normalized_reduction / next_millisecond_cost
                    if next_millisecond_cost > 0.0
                    else None
                ),
                "best_future_normalized_reduction_per_thousand_state_visits": (
                    best_state_rate
                ),
                "best_state_rate_future_checkpoint": best_state_rate_checkpoint,
                "best_future_normalized_reduction_per_solver_millisecond": (
                    best_millisecond_rate
                ),
                "best_millisecond_rate_future_checkpoint": (
                    best_millisecond_rate_checkpoint
                ),
            }
        )


def _summarize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = sorted({(record["solver"], record["checkpoint"]) for record in records})
    summary = []
    for solver, checkpoint in keys:
        rows = [
            record
            for record in records
            if record["solver"] == solver and record["checkpoint"] == checkpoint
        ]
        exploitabilities = [float(row["labels"]["exploitability"]) for row in rows]
        reductions = [float(row["labels"]["reduction_from_start"]) for row in rows]
        solver_milliseconds = [
            float(row["online_features"]["cumulative_solver_milliseconds"])
            for row in rows
        ]
        total_milliseconds = sum(solver_milliseconds)
        summary.append(
            {
                "solver": solver,
                "checkpoint": checkpoint,
                "contexts": len(rows),
                "mean_exploitability": mean(exploitabilities),
                "median_exploitability": median(exploitabilities),
                "mean_reduction_from_start": mean(reductions),
                "improvement_rate_from_start": sum(
                    reduction > TOLERANCE for reduction in reductions
                )
                / len(rows),
                "mean_cumulative_solver_milliseconds": mean(solver_milliseconds),
                "aggregate_reduction_per_solver_millisecond": (
                    sum(reductions) / total_milliseconds
                    if total_milliseconds > 0.0
                    else None
                ),
            }
        )
    return summary


def _pooled_iteration_oracle(
    runs: list[list[dict[str, Any]]],
    average_budget: int,
) -> dict[str, Any]:
    """Exact multiple-choice allocation using iterations as deterministic cost."""

    total_budget = average_budget * len(runs)
    negative_infinity = float("-inf")
    values = [negative_infinity] * (total_budget + 1)
    values[0] = 0.0
    backpointers: list[bytearray] = []
    maximum_available = 0.0
    fixed_total = 0.0
    independent_total = 0.0
    fixed_checkpoint = max(
        row["checkpoint"]
        for row in runs[0]
        if row["checkpoint"] <= average_budget
    )

    for run_index, rows in enumerate(runs):
        start = float(rows[0]["labels"]["exploitability"])
        raw_options = [
            (
                int(row["checkpoint"]),
                start - float(row["labels"]["exploitability"]),
            )
            for row in rows
        ]
        maximum_available += max(gain for _, gain in raw_options)
        fixed_total += next(
            gain for checkpoint, gain in raw_options if checkpoint == fixed_checkpoint
        )
        independent_total += max(
            gain for checkpoint, gain in raw_options if checkpoint <= average_budget
        )

        options = []
        best_gain = negative_infinity
        for checkpoint, gain in raw_options:
            if gain > best_gain + TOLERANCE:
                options.append((checkpoint, gain))
                best_gain = gain
        next_values = [negative_infinity] * (total_budget + 1)
        selected = bytearray([255]) * (total_budget + 1)
        previous_limit = min(total_budget, run_index * rows[-1]["checkpoint"])
        for used in range(previous_limit + 1):
            previous_value = values[used]
            if previous_value == negative_infinity:
                continue
            for option_index, (cost, gain) in enumerate(options):
                new_cost = used + cost
                if new_cost > total_budget:
                    continue
                candidate = previous_value + gain
                if candidate > next_values[new_cost] + TOLERANCE:
                    next_values[new_cost] = candidate
                    selected[new_cost] = option_index
        values = next_values
        backpointers.append(selected)

    selected_cost = max(range(total_budget + 1), key=values.__getitem__)
    pooled_total = values[selected_cost]
    selection_counts: dict[int, int] = {}
    for run_index in range(len(runs) - 1, -1, -1):
        rows = runs[run_index]
        start = float(rows[0]["labels"]["exploitability"])
        raw_options = [
            (
                int(row["checkpoint"]),
                start - float(row["labels"]["exploitability"]),
            )
            for row in rows
        ]
        options = []
        best_gain = negative_infinity
        for checkpoint, gain in raw_options:
            if gain > best_gain + TOLERANCE:
                options.append((checkpoint, gain))
                best_gain = gain
        option_index = backpointers[run_index][selected_cost]
        if option_index == 255:
            raise AssertionError("pooled allocation backpointer is missing")
        checkpoint = options[option_index][0]
        selection_counts[checkpoint] = selection_counts.get(checkpoint, 0) + 1
        selected_cost -= checkpoint
    if selected_cost != 0:
        raise AssertionError("pooled allocation backtracking did not reach zero")

    return {
        "average_iteration_budget": average_budget,
        "aggregate_iteration_budget": total_budget,
        "fixed_checkpoint": fixed_checkpoint,
        "fixed_checkpoint_total_reduction": fixed_total,
        "independent_hard_cap_oracle_total_reduction": independent_total,
        "pooled_perfect_information_total_reduction": pooled_total,
        "pooled_iterations_used": sum(
            checkpoint * count for checkpoint, count in selection_counts.items()
        ),
        "pooled_selection_counts": {
            str(checkpoint): count
            for checkpoint, count in sorted(selection_counts.items())
        },
        "pooled_uplift_over_fixed_fraction": (
            pooled_total / fixed_total - 1.0 if fixed_total > 0.0 else None
        ),
        "maximum_horizon_total_reduction": maximum_available,
        "pooled_fraction_of_horizon_reduction": (
            pooled_total / maximum_available if maximum_available > 0.0 else 0.0
        ),
    }


def _allocation_oracles(
    records: list[dict[str, Any]],
    solvers: tuple[str, ...],
    budgets: tuple[int, ...],
    context_limit: int,
    seed: int,
) -> dict[str, Any]:
    context_ids = sorted({str(record["context_id"]) for record in records})
    ranked_ids = sorted(
        context_ids,
        key=lambda context_id: hashlib.sha256(
            f"{seed}|allocation|{context_id}".encode("utf-8")
        ).digest(),
    )
    selected_ids = set(ranked_ids[:context_limit])
    solver_results = []
    for solver in solvers:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            context_id = str(record["context_id"])
            if record["solver"] == solver and context_id in selected_ids:
                grouped.setdefault(context_id, []).append(record)
        runs = []
        for context_id in sorted(grouped):
            rows = sorted(grouped[context_id], key=lambda row: row["checkpoint"])
            runs.append(rows)
        solver_results.append(
            {
                "solver": solver,
                "budgets": [
                    _pooled_iteration_oracle(runs, budget) for budget in budgets
                ],
            }
        )
    return {
        "contexts": len(selected_ids),
        "context_limit": context_limit,
        "selection": "deterministic SHA-256 sample when contexts exceed limit",
        "cost_unit": "full alternating CFR iterations",
        "perfect_future_information": True,
        "deployable": False,
        "interpretation": (
            "Optimistic ceiling for a shared or speculative compute pool; it is "
            "not achievable by transferring wall-clock time between unrelated "
            "already-completed decisions."
        ),
        "solvers": solver_results,
    }


def run_river_opportunity_experiment(config: dict[str, Any]) -> dict[str, Any]:
    """Generate contexts, solve exact teachers, and collect causal CFR traces."""

    groups = int(config.get("groups", 8))
    seed = int(config.get("seed", 0))
    hands_per_player = int(config.get("hands_per_player", 4))
    sequential_raise_value = config.get("sequential_raise", False)
    if not isinstance(sequential_raise_value, bool):
        raise TypeError("sequential_raise must be a boolean")
    sequential_raise = sequential_raise_value
    families = tuple(str(family) for family in config.get("families", CONTEXT_FAMILIES))
    included_splits = tuple(
        str(split) for split in config.get("included_splits", CONTEXT_SPLITS)
    )
    solvers = tuple(
        str(solver)
        for solver in config.get("solvers", ("cfr", "lcfr", "cfr_plus", "dcfr"))
    )
    checkpoints = tuple(
        int(checkpoint)
        for checkpoint in config.get("checkpoints", DEFAULT_CHECKPOINTS)
    )
    store_policies = bool(config.get("store_policies", False))
    default_allocation_budgets = tuple(
        budget
        for budget in (2, 4, 8, 16, 32)
        if checkpoints and budget <= checkpoints[-1]
    )
    allocation_budgets = tuple(
        int(budget)
        for budget in config.get(
            "allocation_average_iteration_budgets",
            default_allocation_budgets,
        )
    )
    allocation_context_limit = int(config.get("allocation_context_limit", 128))
    if not solvers or len(set(solvers)) != len(solvers):
        raise ValueError("solvers must be nonempty and unique")
    unknown_solvers = set(solvers) - set(UPDATE_RULES)
    if unknown_solvers:
        raise ValueError(f"unsupported solvers: {sorted(unknown_solvers)!r}")
    if (
        not included_splits
        or len(set(included_splits)) != len(included_splits)
        or set(included_splits) - set(CONTEXT_SPLITS)
    ):
        raise ValueError("included_splits must be unique supported split names")
    if (
        not checkpoints
        or checkpoints[0] != 0
        or checkpoints != tuple(sorted(set(checkpoints)))
    ):
        raise ValueError("checkpoints must be sorted, unique, nonnegative, and begin at zero")
    if (
        not allocation_budgets
        or allocation_budgets != tuple(sorted(set(allocation_budgets)))
        or any(budget <= 0 or budget > checkpoints[-1] for budget in allocation_budgets)
    ):
        raise ValueError("allocation budgets must be sorted, unique, positive checkpoints")
    if allocation_context_limit <= 0:
        raise ValueError("allocation_context_limit must be positive")
    if sequential_raise and hands_per_player > 5:
        raise ValueError(
            "sequential exact oracle supports at most five hands per player"
        )

    experiment_start = time.perf_counter()
    generation_start = time.perf_counter()
    contexts = generate_river_contexts(
        groups=groups,
        seed=seed,
        hands_per_player=hands_per_player,
        families=families,
        splits=included_splits,
        sequential_raise=sequential_raise,
    )
    generation_seconds = time.perf_counter() - generation_start
    if not contexts:
        raise ValueError("the requested groups contain no contexts in included_splits")
    context_records = []
    records: list[dict[str, Any]] = []
    oracle_seconds = 0.0
    solver_seconds_total = 0.0
    evaluation_seconds_total = 0.0

    for context in contexts:
        oracle_start = time.perf_counter()
        oracle = solve_river_game(context.game)
        context_oracle_seconds = time.perf_counter() - oracle_start
        oracle_seconds += context_oracle_seconds
        serialized_context = serialize_river_context(context)
        serialized_context["oracle_labels"] = {
            "value_player0": oracle.value_player0,
            "nash_conv": oracle.nash_conv,
            "duality_gap": oracle.matrix_solution.duality_gap,
            "player0_pure_policies": oracle.player0_pure_policies,
            "player1_pure_policies": oracle.player1_pure_policies,
            "player0_support_size": oracle.player0_support_size,
            "player1_support_size": oracle.player1_support_size,
            "solve_milliseconds": context_oracle_seconds * 1_000.0,
        }
        if store_policies:
            serialized_context["oracle_labels"]["policy"] = json_policy(oracle.policy)
        context_records.append(serialized_context)

        information_sets = {}
        for player in range(context.game.num_players):
            player_sets = collect_information_sets(context.game, player)
            overlap = set(information_sets) & set(player_sets)
            if overlap:
                raise ValueError(f"information keys shared across players: {overlap!r}")
            information_sets.update(player_sets)
        tree_states = _full_tree_state_count(context.game.initial_state())
        context_features = river_context_features(context)

        for variant in solvers:
            solver = TabularCFR(context.game, variant=variant)  # type: ignore[arg-type]
            cumulative_solver_seconds = 0.0
            previous_average_policy: Policy = {}
            run_records = []
            previous_checkpoint = 0
            for checkpoint in checkpoints:
                interval_seconds = 0.0
                if checkpoint > previous_checkpoint:
                    solve_start = time.perf_counter()
                    solver.run(checkpoint - previous_checkpoint)
                    interval_seconds = time.perf_counter() - solve_start
                    cumulative_solver_seconds += interval_seconds
                    solver_seconds_total += interval_seconds

                solver_features, average_policy = _solver_online_features(
                    solver,
                    information_sets,
                    previous_average_policy,
                    context.game.payoff_span,
                )
                online_features: dict[str, object] = {
                    **context_features,
                    "solver": variant,
                    "checkpoint": checkpoint,
                    "known_information_sets": len(information_sets),
                    "tree_states_per_full_traversal": tree_states,
                    "cumulative_alternating_state_visits": (
                        checkpoint * context.game.num_players * tree_states
                    ),
                    "interval_solver_milliseconds": interval_seconds * 1_000.0,
                    "cumulative_solver_milliseconds": cumulative_solver_seconds * 1_000.0,
                    **solver_features,
                }
                _validate_online_features(online_features)

                evaluation_start = time.perf_counter()
                evaluation = evaluate_profile(context.game, average_policy)
                local_regret = counterfactual_regret_profile(
                    context.game,
                    average_policy,
                )
                evaluation_seconds = time.perf_counter() - evaluation_start
                evaluation_seconds_total += evaluation_seconds
                record: dict[str, Any] = {
                    "context_id": context.context_id,
                    "group_id": context.group_id,
                    "split": context.split,
                    "family": context.family,
                    "solver": variant,
                    "checkpoint": checkpoint,
                    "online_features": online_features,
                    "diagnostic_evaluation_milliseconds": evaluation_seconds * 1_000.0,
                    "labels": {
                        "exploitability": evaluation.exploitability,
                        "nash_conv": evaluation.nash_conv,
                        "local_one_step_positive_regret": (
                            local_regret.total_positive_regret
                        ),
                        "utility_player0": evaluation.utilities[0],
                        "absolute_value_error": abs(
                            evaluation.utilities[0] - oracle.value_player0
                        ),
                    },
                }
                if store_policies:
                    record["average_policy"] = json_policy(average_policy)
                run_records.append(record)
                previous_average_policy = average_policy
                previous_checkpoint = checkpoint

            _annotate_future_labels(run_records)
            records.extend(run_records)

    postprocessing_start = time.perf_counter()
    summary = _summarize_records(records)
    allocation_oracles = _allocation_oracles(
        records,
        solvers,
        allocation_budgets,
        min(allocation_context_limit, len(contexts)),
        seed,
    )
    postprocessing_seconds = time.perf_counter() - postprocessing_start
    wall_seconds = time.perf_counter() - experiment_start
    return {
        "schema_version": 2,
        "experiment_type": "exact_river_early_opportunity_trace",
        "status": "measurement_only_no_scheduler_fit",
        "config": {
            "groups": groups,
            "seed": seed,
            "hands_per_player": hands_per_player,
            "sequential_raise": sequential_raise,
            "families": list(families),
            "included_splits": list(included_splits),
            "solvers": list(solvers),
            "checkpoints": list(checkpoints),
            "store_policies": store_policies,
            "allocation_average_iteration_budgets": list(allocation_budgets),
            "allocation_context_limit": allocation_context_limit,
        },
        "environment": environment_metadata(),
        "timing": {
            "context_generation_seconds": generation_seconds,
            "oracle_seconds": oracle_seconds,
            "solver_seconds": solver_seconds_total,
            "diagnostic_evaluation_seconds": evaluation_seconds_total,
            "postprocessing_seconds": postprocessing_seconds,
            "wall_seconds": wall_seconds,
        },
        "counts": {
            "groups": len({context.group_id for context in contexts}),
            "contexts": len(contexts),
            "solver_runs": len(contexts) * len(solvers),
            "trace_records": len(records),
        },
        "feature_contract": {
            "causal_online_only": True,
            "forbidden_name_fragments": list(FORBIDDEN_ONLINE_FEATURE_FRAGMENTS),
            "exact_evaluations_and_future_outcomes_are_labels_only": True,
            "range_features_are_computed_from_the_supplied_joint_belief": True,
        },
        "split_contract": {
            "unit": "board_group",
            "all_range_families_for_one_board_share_a_split": True,
            "splits": ["development", "validation", "test"],
        },
        "contexts": context_records,
        "summary": summary,
        "allocation_oracles": allocation_oracles,
        "records": records,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_river_opportunity_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "exact river opportunity trace: "
        f"contexts={result['counts']['contexts']}, "
        f"runs={result['counts']['solver_runs']}, "
        f"records={result['counts']['trace_records']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
