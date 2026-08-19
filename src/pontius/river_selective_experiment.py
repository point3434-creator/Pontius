"""Development-only full-universe quality/work pilot for selective river trees."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

from .cfr import TabularCFR
from .depth_limited import PolicyContinuationValues
from .evaluation import EvaluationResult, Policy, evaluate_profile
from .reporting import environment_metadata
from .river import RiverHoldem
from .river_context import CONTEXT_FAMILIES, generate_river_contexts
from .river_incremental import RiverRangeDelta
from .river_multi_size import MultiSizeRiverHoldem
from .river_multi_size_experiment import _factorized_likelihood_target
from .river_range_reuse import make_blocker_perturbation
from .river_selective import (
    MultiSizeExpansionMask,
    complete_information_schema,
    compose_selective_policy,
)
from .selective_tree import (
    SelectiveExpansionGame,
    collect_selective_cutoff_states,
    full_tree_state_count,
)
from .updates import UPDATE_RULES

_TARGET_NAMES = (
    "blocker_reweight_p0",
    "blocker_reweight_p1",
    "factorized_likelihood_p0",
)


def _positive_finite(value: float) -> bool:
    return math.isfinite(value) and value > 0.0


def _validate_config(config: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "groups",
        "seed",
        "hands_per_player",
        "families",
        "included_splits",
        "bet_pot_fractions",
        "raise_to_pot_fractions",
        "masks",
        "blueprint_solver",
        "blueprint_iterations",
        "online_solver",
        "warm_start_multipliers_by_payoff_span",
        "full_tree_equivalent_iteration_budgets",
        "target_names",
        "root_tv_budget",
        "maximum_donor_fraction",
        "factorized_likelihood_minimum",
        "factorized_likelihood_maximum",
    }
    unknown = set(config) - allowed
    if unknown:
        raise ValueError(f"unknown selective-expansion fields: {sorted(unknown)!r}")

    groups = int(config.get("groups", 3))
    seed = int(config.get("seed", 0))
    hands = int(config.get("hands_per_player", 4))
    families = tuple(str(value) for value in config.get("families", CONTEXT_FAMILIES))
    splits = tuple(str(value) for value in config.get("included_splits", ("development",)))
    bets = tuple(float(value) for value in config.get("bet_pot_fractions", (0.25, 0.5, 0.75)))
    raises = tuple(float(value) for value in config.get("raise_to_pot_fractions", (1.5, 2.0)))
    blueprint_solver = str(config.get("blueprint_solver", "dcfr"))
    blueprint_iterations = int(config.get("blueprint_iterations", 512))
    online_solver = str(config.get("online_solver", "dcfr"))
    warm_multipliers = tuple(
        float(value)
        for value in config.get("warm_start_multipliers_by_payoff_span", (0.01, 0.1, 1.0))
    )
    budgets = tuple(
        int(value)
        for value in config.get("full_tree_equivalent_iteration_budgets", (1, 2, 4, 8, 16))
    )
    target_names = tuple(str(value) for value in config.get("target_names", _TARGET_NAMES))
    root_tv = float(config.get("root_tv_budget", 0.01))
    donor_fraction = float(config.get("maximum_donor_fraction", 0.75))
    likelihood_minimum = float(config.get("factorized_likelihood_minimum", 0.5))
    likelihood_maximum = float(config.get("factorized_likelihood_maximum", 1.5))

    if groups <= 0:
        raise ValueError("groups must be positive")
    if not 2 <= hands <= 8:
        raise ValueError("hands_per_player must be between two and eight")
    if (
        not families
        or len(set(families)) != len(families)
        or set(families) - set(CONTEXT_FAMILIES)
    ):
        raise ValueError("families must be unique supported context families")
    if splits != ("development",):
        raise ValueError("selective-expansion pilot is development-only")
    if bets != (0.25, 0.5, 0.75) or raises != (1.5, 2.0):
        raise ValueError("the pilot full universe must be the frozen 3x2 lattice")
    if blueprint_solver not in UPDATE_RULES or online_solver not in UPDATE_RULES:
        raise ValueError("blueprint_solver and online_solver must be supported")
    if blueprint_iterations <= 0:
        raise ValueError("blueprint_iterations must be positive")
    if (
        not warm_multipliers
        or warm_multipliers != tuple(sorted(set(warm_multipliers)))
        or not all(_positive_finite(value) for value in warm_multipliers)
    ):
        raise ValueError("warm-start multipliers must be sorted unique and positive")
    if not budgets or budgets != tuple(sorted(set(budgets))) or budgets[0] <= 0:
        raise ValueError("work budgets must be sorted unique positive integers")
    if (
        not target_names
        or len(set(target_names)) != len(target_names)
        or set(target_names) - set(_TARGET_NAMES)
    ):
        raise ValueError("target_names must be unique support-preserving targets")
    if not 0.0 < root_tv < 0.5 or not 0.0 < donor_fraction < 1.0:
        raise ValueError("blocker perturbation controls are outside their open ranges")
    if (
        not _positive_finite(likelihood_minimum)
        or not _positive_finite(likelihood_maximum)
        or likelihood_minimum >= likelihood_maximum
    ):
        raise ValueError("factorized likelihood bounds must be finite and increasing")

    raw_masks = config.get("masks")
    if not isinstance(raw_masks, list) or not raw_masks:
        raise ValueError("masks must be a nonempty explicit list")
    masks: list[dict[str, object]] = []
    previous_bets: set[float] = set()
    previous_raises: set[float] = set()
    names: set[str] = set()
    for raw in raw_masks:
        if not isinstance(raw, dict) or set(raw) != {
            "name",
            "expanded_bet_pot_fractions",
            "expanded_raise_to_pot_fractions",
        }:
            raise ValueError("every mask must contain exactly name, bets, and raises")
        name = str(raw["name"])
        mask_bets = tuple(float(value) for value in raw["expanded_bet_pot_fractions"])
        mask_raises = tuple(
            float(value) for value in raw["expanded_raise_to_pot_fractions"]
        )
        if not name or name in names:
            raise ValueError("mask names must be nonempty and unique")
        if (
            mask_bets != tuple(sorted(set(mask_bets)))
            or mask_raises != tuple(sorted(set(mask_raises)))
            or set(mask_bets) - set(bets)
            or set(mask_raises) - set(raises)
        ):
            raise ValueError("mask actions must be sorted unique subsets of the universe")
        if not previous_bets.issubset(mask_bets) or not previous_raises.issubset(mask_raises):
            raise ValueError("masks must form one nested expansion chain")
        names.add(name)
        previous_bets = set(mask_bets)
        previous_raises = set(mask_raises)
        masks.append(
            {
                "name": name,
                "expanded_bet_pot_fractions": mask_bets,
                "expanded_raise_to_pot_fractions": mask_raises,
            }
        )
    if previous_bets != set(bets) or previous_raises != set(raises):
        raise ValueError("the final mask must fully expand the 3x2 universe")

    return {
        "groups": groups,
        "seed": seed,
        "hands_per_player": hands,
        "families": families,
        "included_splits": splits,
        "bet_pot_fractions": bets,
        "raise_to_pot_fractions": raises,
        "masks": tuple(masks),
        "blueprint_solver": blueprint_solver,
        "blueprint_iterations": blueprint_iterations,
        "online_solver": online_solver,
        "warm_start_multipliers_by_payoff_span": warm_multipliers,
        "full_tree_equivalent_iteration_budgets": budgets,
        "target_names": target_names,
        "root_tv_budget": root_tv,
        "maximum_donor_fraction": donor_fraction,
        "factorized_likelihood_minimum": likelihood_minimum,
        "factorized_likelihood_maximum": likelihood_maximum,
    }


def _wide_game(range_game: RiverHoldem, parsed: dict[str, Any]) -> MultiSizeRiverHoldem:
    return MultiSizeRiverHoldem.from_joint_weights(
        board=range_game.board,
        pot=range_game.pot,
        stacks=range_game.stacks,
        bet_sizes=tuple(range_game.pot * value for value in parsed["bet_pot_fractions"]),
        raise_to_sizes=tuple(
            range_game.pot * value for value in parsed["raise_to_pot_fractions"]
        ),
        joint_weights=range_game.joint_distribution(),
    )


def _range_targets(
    source: RiverHoldem,
    parsed: dict[str, Any],
) -> tuple[tuple[str, str, RiverHoldem, dict[str, object]], ...]:
    targets: dict[str, tuple[str, RiverHoldem, dict[str, object]]] = {}
    for player in (0, 1):
        name = f"blocker_reweight_p{player}"
        if name not in parsed["target_names"]:
            continue
        target, metadata = make_blocker_perturbation(
            source,
            player=player,
            root_tv_budget=parsed["root_tv_budget"],
            maximum_donor_fraction=parsed["maximum_donor_fraction"],
        )
        targets[name] = (
            "sparse_reweight",
            target,
            metadata,
        )
    if "factorized_likelihood_p0" in parsed["target_names"]:
        target, metadata = _factorized_likelihood_target(
            source,
            player=0,
            minimum=parsed["factorized_likelihood_minimum"],
            maximum=parsed["factorized_likelihood_maximum"],
        )
        targets["factorized_likelihood_p0"] = (
            "factorized_dense",
            target,
            metadata,
        )
    return tuple(
        (name, *targets[name])
        for name in parsed["target_names"]
    )


def _policy_tv(
    first: Policy,
    second: Policy,
    schema: dict[str, tuple[object, ...]],
) -> tuple[float, float, int]:
    distances = []
    changed = 0
    for key, actions in schema.items():
        distance = 0.5 * sum(
            abs(first[key][action] - second[key][action])
            for action in actions
        )
        distances.append(distance)
        changed += distance > 1e-15
    return mean(distances), max(distances, default=0.0), changed


def _quality_fields(
    baseline: EvaluationResult,
    candidate: EvaluationResult,
    *,
    state_visits: int,
    hot_seconds: float,
    cold_seconds: float,
) -> dict[str, object]:
    reduction = baseline.nash_conv - candidate.nash_conv
    return {
        "full_universe_nash_conv": candidate.nash_conv,
        "full_universe_exploitability": candidate.exploitability,
        "nash_conv_reduction_from_blueprint": reduction,
        "maximum_player_deviation_gain_increase": max(
            candidate_gain - baseline_gain
            for candidate_gain, baseline_gain in zip(
                candidate.deviation_gains,
                baseline.deviation_gains,
                strict=True,
            )
        ),
        "player_utility_changes": [
            candidate_utility - baseline_utility
            for candidate_utility, baseline_utility in zip(
                candidate.utilities,
                baseline.utilities,
                strict=True,
            )
        ],
        "reduction_per_million_state_visits": (
            reduction * 1_000_000.0 / state_visits
        ),
        "hot_reduction_per_millisecond": reduction / (hot_seconds * 1000.0),
        "cold_exact_leaf_reduction_per_millisecond": (
            reduction / (cold_seconds * 1000.0)
        ),
        "improved": reduction > 1e-12,
        "harmed": reduction < -1e-12,
    }


def _summaries(records: list[dict[str, Any]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, float, int], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        grouped[
            (
                str(row["mask_name"]),
                float(row["warm_start_multiplier_by_payoff_span"]),
                int(row["full_tree_equivalent_iteration_budget"]),
            )
        ].append(row)

    summaries = []
    for (mask, warm, budget), rows in sorted(grouped.items()):
        reductions = [float(row["nash_conv_reduction_from_blueprint"]) for row in rows]
        total_visits = sum(int(row["actual_state_visits"]) for row in rows)
        summaries.append(
            {
                "mask_name": mask,
                "warm_start_multiplier_by_payoff_span": warm,
                "full_tree_equivalent_iteration_budget": budget,
                "records": len(rows),
                "mean_nash_conv_reduction": mean(reductions),
                "median_nash_conv_reduction": median(reductions),
                "aggregate_reduction_per_million_state_visits": (
                    sum(reductions) * 1_000_000.0 / total_visits
                ),
                "improvement_fraction": mean(bool(row["improved"]) for row in rows),
                "harm_fraction": mean(bool(row["harmed"]) for row in rows),
                "mean_hot_milliseconds": 1000.0
                * mean(float(row["hot_online_seconds"]) for row in rows),
                "mean_cold_exact_leaf_milliseconds": 1000.0
                * mean(float(row["cold_exact_leaf_online_seconds"]) for row in rows),
                "mean_budget_utilization": mean(
                    float(row["budget_utilization"]) for row in rows
                ),
            }
        )
    return summaries


def _oracle_ceiling(
    records: list[dict[str, Any]],
    summaries: list[dict[str, object]],
) -> list[dict[str, object]]:
    result = []
    budgets = sorted(
        {int(row["full_tree_equivalent_iteration_budget"]) for row in records}
    )
    for budget in budgets:
        budget_rows = [
            row
            for row in records
            if int(row["full_tree_equivalent_iteration_budget"]) == budget
        ]
        instances: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in budget_rows:
            instances[(str(row["context_id"]), str(row["target_name"]))].append(row)
        oracle_total = sum(
            max(float(row["nash_conv_reduction_from_blueprint"]) for row in rows)
            for rows in instances.values()
        )
        matching_summaries = [
            row
            for row in summaries
            if int(row["full_tree_equivalent_iteration_budget"]) == budget
        ]
        best_fixed = max(
            matching_summaries,
            key=lambda row: float(row["mean_nash_conv_reduction"]),
        )
        fixed_total = float(best_fixed["mean_nash_conv_reduction"]) * len(instances)
        result.append(
            {
                "full_tree_equivalent_iteration_budget": budget,
                "instances": len(instances),
                "oracle_total_reduction": oracle_total,
                "best_fixed_mask_name": best_fixed["mask_name"],
                "best_fixed_warm_start_multiplier_by_payoff_span": best_fixed[
                    "warm_start_multiplier_by_payoff_span"
                ],
                "best_fixed_total_reduction": fixed_total,
                "oracle_minus_best_fixed_reduction": oracle_total - fixed_total,
                "selection_authorized": False,
            }
        )
    return result


def run_selective_expansion_pilot(config: dict[str, Any]) -> dict[str, Any]:
    parsed = _validate_config(config)
    experiment_start = time.perf_counter()
    contexts = generate_river_contexts(
        groups=parsed["groups"],
        seed=parsed["seed"],
        hands_per_player=parsed["hands_per_player"],
        families=parsed["families"],
        splits=parsed["included_splits"],
        sequential_raise=False,
    )
    if not contexts:
        raise ValueError("configuration generated no development contexts")

    records: list[dict[str, Any]] = []
    blueprint_records: list[dict[str, object]] = []
    target_records: list[dict[str, object]] = []
    structure_records: list[dict[str, object]] = []
    all_schema_identity = True
    all_full_masks_have_no_cutoffs = True
    all_full_mask_state_counts_match = True
    all_mask_counts_strictly_increase = True

    for context in contexts:
        source = _wide_game(context.game, parsed)
        source_schema = complete_information_schema(source)
        source_tree_states = full_tree_state_count(source.initial_state())
        blueprint_solver = TabularCFR(source, variant=parsed["blueprint_solver"])
        blueprint_start = time.perf_counter()
        blueprint_solver.run(parsed["blueprint_iterations"])
        blueprint_seconds = time.perf_counter() - blueprint_start
        blueprint = blueprint_solver.average_strategy()
        if set(blueprint) != set(source_schema):
            raise AssertionError("full blueprint did not materialize the full source schema")
        source_evaluation_start = time.perf_counter()
        source_evaluation = evaluate_profile(source, blueprint)
        source_evaluation_seconds = time.perf_counter() - source_evaluation_start
        blueprint_records.append(
            {
                "context_id": context.context_id,
                "group_id": context.group_id,
                "family": context.family,
                "deals": len(source.deals),
                "information_sets": len(source_schema),
                "tree_states_per_traversal": source_tree_states,
                "iterations": parsed["blueprint_iterations"],
                "state_visits": (
                    parsed["blueprint_iterations"]
                    * source.num_players
                    * source_tree_states
                ),
                "solve_seconds": blueprint_seconds,
                "exact_evaluation_seconds": source_evaluation_seconds,
                "source_nash_conv": source_evaluation.nash_conv,
                "source_exploitability": source_evaluation.exploitability,
            }
        )

        for target_name, target_kind, range_target, target_metadata in _range_targets(
            context.game,
            parsed,
        ):
            target = _wide_game(range_target, parsed)
            target_schema = complete_information_schema(target)
            schema_identity = target_schema == source_schema
            all_schema_identity &= schema_identity
            if not schema_identity:
                raise AssertionError("support-preserving target changed the information schema")
            target_tree_states = full_tree_state_count(target.initial_state())
            baseline_evaluation_start = time.perf_counter()
            baseline_evaluation = evaluate_profile(target, blueprint)
            baseline_evaluation_seconds = time.perf_counter() - baseline_evaluation_start
            range_delta = RiverRangeDelta.between(context.game, range_target)
            target_records.append(
                {
                    "context_id": context.context_id,
                    "group_id": context.group_id,
                    "family": context.family,
                    "target_name": target_name,
                    "target_kind": target_kind,
                    "target_metadata": target_metadata,
                    "changed_deals": len(range_delta.changes),
                    "root_joint_total_variation": range_delta.total_variation,
                    "information_schema_identical": schema_identity,
                    "blueprint_full_universe_nash_conv": baseline_evaluation.nash_conv,
                    "blueprint_full_universe_exploitability": (
                        baseline_evaluation.exploitability
                    ),
                    "blueprint_target_exact_evaluation_seconds": (
                        baseline_evaluation_seconds
                    ),
                }
            )

            target_structures: list[dict[str, object]] = []
            for mask_index, mask_config in enumerate(parsed["masks"]):
                mask_name = str(mask_config["name"])
                mask = MultiSizeExpansionMask.from_amounts(
                    target,
                    bet_amounts=tuple(
                        target.pot * value
                        for value in mask_config["expanded_bet_pot_fractions"]
                    ),
                    raise_to_amounts=tuple(
                        target.pot * value
                        for value in mask_config["expanded_raise_to_pot_fractions"]
                    ),
                )
                leaf_values = PolicyContinuationValues(target.num_players, blueprint)
                selective = SelectiveExpansionGame(target, leaf_values, mask)
                selective_states = full_tree_state_count(selective.initial_state())
                cutoff_states = collect_selective_cutoff_states(selective)
                leaf_start = time.perf_counter()
                for state in cutoff_states:
                    leaf_values(state)
                exact_leaf_build_seconds = time.perf_counter() - leaf_start
                if leaf_values.cache_size != len(cutoff_states):
                    raise AssertionError("selective cutoff states were not uniquely cached")
                schema_start = time.perf_counter()
                selective_schema = complete_information_schema(selective)
                schema_seconds = time.perf_counter() - schema_start
                is_full_mask = mask_index == len(parsed["masks"]) - 1
                all_full_masks_have_no_cutoffs &= not is_full_mask or not cutoff_states
                all_full_mask_state_counts_match &= (
                    not is_full_mask or selective_states == target_tree_states
                )
                structure = {
                    "context_id": context.context_id,
                    "target_name": target_name,
                    "mask_name": mask_name,
                    "expanded_bets": len(mask.expanded_bets),
                    "expanded_raises": len(mask.expanded_raises),
                    "tree_states_per_traversal": selective_states,
                    "full_tree_state_fraction": selective_states / target_tree_states,
                    "materialized_information_sets": len(selective_schema),
                    "full_information_set_fraction": len(selective_schema)
                    / len(target_schema),
                    "cutoff_states": len(cutoff_states),
                    "exact_leaf_cache_entries": leaf_values.cache_size,
                    "exact_leaf_build_seconds": exact_leaf_build_seconds,
                    "offline_schema_compile_seconds": schema_seconds,
                    "is_full_mask": is_full_mask,
                }
                structure_records.append(structure)
                target_structures.append(structure)

                full_iteration_state_visits = target.num_players * target_tree_states
                selective_iteration_state_visits = target.num_players * selective_states
                budget_checkpoints = {
                    budget: max(
                        1,
                        (budget * full_iteration_state_visits)
                        // selective_iteration_state_visits,
                    )
                    for budget in parsed["full_tree_equivalent_iteration_budgets"]
                }

                for warm_multiplier in parsed[
                    "warm_start_multipliers_by_payoff_span"
                ]:
                    solver = TabularCFR(selective, variant=parsed["online_solver"])
                    initialization_start = time.perf_counter()
                    solver.warm_start_from_schema(
                        blueprint,
                        regret_mass=warm_multiplier * target.payoff_span,
                        information_sets=selective_schema,
                    )
                    initialization_seconds = time.perf_counter() - initialization_start
                    completed_iterations = 0
                    cumulative_solve_seconds = 0.0

                    for budget in parsed["full_tree_equivalent_iteration_budgets"]:
                        checkpoint = budget_checkpoints[budget]
                        solve_start = time.perf_counter()
                        solver.run(checkpoint - completed_iterations)
                        cumulative_solve_seconds += time.perf_counter() - solve_start
                        completed_iterations = checkpoint
                        candidate = solver.average_strategy()
                        completed = compose_selective_policy(
                            blueprint,
                            candidate,
                            target_schema,
                        )
                        evaluation_start = time.perf_counter()
                        candidate_evaluation = evaluate_profile(target, completed)
                        label_seconds = time.perf_counter() - evaluation_start
                        mean_tv, max_tv, changed_information_sets = _policy_tv(
                            blueprint,
                            completed,
                            target_schema,
                        )
                        actual_state_visits = (
                            checkpoint * selective_iteration_state_visits
                        )
                        state_visit_budget = budget * full_iteration_state_visits
                        hot_seconds = initialization_seconds + cumulative_solve_seconds
                        cold_seconds = exact_leaf_build_seconds + hot_seconds
                        records.append(
                            {
                                "context_id": context.context_id,
                                "group_id": context.group_id,
                                "family": context.family,
                                "target_name": target_name,
                                "target_kind": target_kind,
                                "mask_name": mask_name,
                                "warm_start_multiplier_by_payoff_span": warm_multiplier,
                                "warm_start_regret_mass": (
                                    warm_multiplier * target.payoff_span
                                ),
                                "full_tree_equivalent_iteration_budget": budget,
                                "solver_iterations": checkpoint,
                                "tree_states_per_traversal": selective_states,
                                "state_visit_budget": state_visit_budget,
                                "actual_state_visits": actual_state_visits,
                                "budget_utilization": actual_state_visits
                                / state_visit_budget,
                                "materialized_information_sets": len(selective_schema),
                                "full_information_sets": len(target_schema),
                                "cutoff_states": len(cutoff_states),
                                "exact_leaf_build_seconds": exact_leaf_build_seconds,
                                "initialization_seconds": initialization_seconds,
                                "cumulative_solve_seconds": cumulative_solve_seconds,
                                "hot_online_seconds": hot_seconds,
                                "cold_exact_leaf_online_seconds": cold_seconds,
                                "full_evaluation_label_seconds": label_seconds,
                                "mean_full_policy_total_variation": mean_tv,
                                "maximum_full_policy_total_variation": max_tv,
                                "changed_full_information_sets": changed_information_sets,
                                **_quality_fields(
                                    baseline_evaluation,
                                    candidate_evaluation,
                                    state_visits=actual_state_visits,
                                    hot_seconds=hot_seconds,
                                    cold_seconds=cold_seconds,
                                ),
                            }
                        )

            state_counts = [
                int(row["tree_states_per_traversal"])
                for row in target_structures
            ]
            all_mask_counts_strictly_increase &= (
                state_counts == sorted(set(state_counts))
            )

    summaries = _summaries(records)
    oracle = _oracle_ceiling(records, summaries)
    config_payload = json.dumps(config, sort_keys=True, separators=(",", ":"))
    gates = {
        "development_contexts_only": all(context.split == "development" for context in contexts),
        "source_target_information_schema_identity": all_schema_identity,
        "nested_mask_tree_counts_strictly_increase": all_mask_counts_strictly_increase,
        "full_mask_has_no_cutoffs": all_full_masks_have_no_cutoffs,
        "full_mask_state_count_matches_full_game": all_full_mask_state_counts_match,
    }
    return {
        "experiment_type": "river_selective_expansion_pilot",
        "pilot": True,
        "selection_authorized": False,
        "native_latency_claim_authorized": False,
        "neural_leaf_claim_authorized": False,
        "config_sha256": hashlib.sha256(config_payload.encode("utf-8")).hexdigest(),
        "config": config,
        "environment": environment_metadata(),
        "counts": {
            "groups": len({context.group_id for context in contexts}),
            "contexts": len(contexts),
            "blueprints": len(blueprint_records),
            "targets": len(target_records),
            "structures": len(structure_records),
            "candidate_records": len(records),
        },
        "gates": {"passed": all(gates.values()), "results": gates},
        "aggregate": {
            "mean_source_blueprint_nash_conv": mean(
                float(row["source_nash_conv"]) for row in blueprint_records
            ),
            "maximum_source_blueprint_nash_conv": max(
                float(row["source_nash_conv"]) for row in blueprint_records
            ),
            "mean_stale_target_nash_conv": mean(
                float(row["blueprint_full_universe_nash_conv"])
                for row in target_records
            ),
            "maximum_stale_target_nash_conv": max(
                float(row["blueprint_full_universe_nash_conv"])
                for row in target_records
            ),
            "maximum_candidate_nash_conv_harm": max(
                -float(row["nash_conv_reduction_from_blueprint"])
                for row in records
            ),
            "overall_improvement_fraction": mean(
                bool(row["improved"]) for row in records
            ),
            "overall_harm_fraction": mean(bool(row["harmed"]) for row in records),
            "experiment_seconds": time.perf_counter() - experiment_start,
        },
        "blueprints": blueprint_records,
        "targets": target_records,
        "structures": structure_records,
        "records": records,
        "summaries": summaries,
        "oracle_ceiling": oracle,
        "interpretation_limits": {
            "development_only": True,
            "exact_continuation_values_are_oracle_control": True,
            "cold_exact_leaf_cost_is_charged": True,
            "hot_timing_is_optimistic_cached_leaf_control": True,
            "full_game_evaluation_is_label_only": True,
            "support_changing_ranges_are_excluded": True,
            "best_per_context_mask_is_not_deployable": True,
            "python_timing_is_not_native_kernel_timing": True,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_selective_expansion_pilot(config)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(rendered)
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "gates": result["gates"]}))


if __name__ == "__main__":
    main()
