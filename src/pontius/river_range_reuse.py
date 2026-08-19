"""Measure strict river cache identity, warm starts, and recertification."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict
from math import isfinite
from pathlib import Path
from statistics import mean
from typing import Any

from .cfr import TabularCFR
from .evaluation import Policy, collect_information_sets, evaluate_profile, policy_distribution
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, GameState
from .reporting import environment_metadata
from .river import RiverDeal, RiverHoldem, evaluate_seven, format_card
from .river_cache import (
    assess_river_range_reuse,
    exact_strategy_cache_lookup,
    structural_information_schema_lookup,
    structural_warm_start_hint,
    transferred_exploitability_certificate,
)
from .river_context import (
    CONTEXT_FAMILIES,
    generate_river_contexts,
    serialize_river_context,
)
from .river_oracle import solve_river_game
from .updates import UPDATE_RULES

DEFAULT_CHECKPOINTS = (0, 1, 2, 3, 4, 6, 8, 12, 16)
TOLERANCE = 1e-12


def _derived_seed(seed: int, *parts: object) -> int:
    payload = "|".join((str(seed), *(str(part) for part in parts)))
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


def _fold(group_id: str, folds: int) -> int:
    digest = hashlib.sha256(group_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % folds


def _deal_text(deal: RiverDeal) -> dict[str, list[str]]:
    return {
        "player0": [format_card(card) for card in deal.player0],
        "player1": [format_card(card) for card in deal.player1],
    }


def _showdown_outcome(game: RiverHoldem, deal: RiverDeal, player: int) -> int:
    own = evaluate_seven((*game.board, *deal.hand(player)))
    opponent = evaluate_seven((*game.board, *deal.hand(1 - player)))
    return (own > opponent) - (own < opponent)


def make_blocker_perturbation(
    game: RiverHoldem,
    *,
    player: int,
    root_tv_budget: float,
    maximum_donor_fraction: float,
) -> tuple[RiverHoldem, dict[str, object]]:
    """Move a small root mass inside one rare private-hand conditional range.

    Support and the selected player's private-hand marginal remain unchanged.
    The selected donor/recipient pair maximizes showdown-outcome contrast within
    the rarest eligible hand, making the perturbation deliberately adversarial
    to range-insensitive strategy reuse.
    """

    if player not in (0, 1):
        raise ValueError("player must be zero or one")
    if not isfinite(root_tv_budget) or not 0.0 < root_tv_budget < 0.5:
        raise ValueError("root_tv_budget must be finite and between zero and 0.5")
    if (
        not isfinite(maximum_donor_fraction)
        or not 0.0 < maximum_donor_fraction < 1.0
    ):
        raise ValueError("maximum_donor_fraction must be finite and between zero and one")

    probabilities = game.joint_distribution()
    by_hand: dict[tuple[int, int], list[RiverDeal]] = defaultdict(list)
    for deal in probabilities:
        by_hand[deal.hand(player)].append(deal)
    candidates = []
    for own_hand, deals in by_hand.items():
        if len(deals) < 2:
            continue
        marginal = sum(probabilities[deal] for deal in deals)
        ordered_pairs = []
        for donor in deals:
            donor_outcome = _showdown_outcome(game, donor, player)
            for recipient in deals:
                if recipient == donor:
                    continue
                recipient_outcome = _showdown_outcome(game, recipient, player)
                ordered_pairs.append(
                    (
                        abs(donor_outcome - recipient_outcome),
                        probabilities[donor],
                        donor,
                        recipient,
                        donor_outcome,
                        recipient_outcome,
                    )
                )
        best = max(
            ordered_pairs,
            key=lambda item: (item[0], item[1], repr(item[2]), repr(item[3])),
        )
        candidates.append((marginal, own_hand, best))
    if not candidates:
        raise ValueError("range has no private hand with two compatible opponent deals")

    marginal, own_hand, selected = min(
        candidates,
        key=lambda item: (item[0], -item[2][0], repr(item[1])),
    )
    (
        outcome_contrast,
        donor_probability,
        donor,
        recipient,
        donor_outcome,
        recipient_outcome,
    ) = selected
    moved_mass = min(
        root_tv_budget,
        maximum_donor_fraction * donor_probability,
    )
    if moved_mass <= 0.0:
        raise AssertionError("blocker perturbation moved no probability mass")

    target_weights = dict(probabilities)
    target_weights[donor] -= moved_mass
    target_weights[recipient] += moved_mass
    target = RiverHoldem.from_joint_weights(
        board=game.board,
        pot=game.pot,
        stacks=game.stacks,
        bet_size=game.bet_size,
        raise_to=game.raise_to,
        joint_weights=target_weights,
    )
    root_tv = game.total_variation(target)
    conditional_tv = game.conditional_opponent_total_variation(
        target,
        player=player,
        own_hand=own_hand,
    )
    if abs(root_tv - moved_mass) > 1e-10:
        raise AssertionError("constructed root TV differs from moved mass")
    if game.provenance_digest == target.provenance_digest:
        raise AssertionError("range perturbation did not change provenance")

    return target, {
        "player": player,
        "root_tv_budget": root_tv_budget,
        "maximum_donor_fraction": maximum_donor_fraction,
        "actual_root_joint_total_variation": root_tv,
        "selected_private_hand": [format_card(card) for card in own_hand],
        "selected_private_hand_probability": marginal,
        "selected_conditional_total_variation": conditional_tv,
        "moved_probability_mass": moved_mass,
        "donor_probability_before": donor_probability,
        "donor_probability_after": target_weights[donor],
        "donor": _deal_text(donor),
        "recipient": _deal_text(recipient),
        "donor_showdown_outcome": donor_outcome,
        "recipient_showdown_outcome": recipient_outcome,
        "showdown_outcome_contrast": outcome_contrast,
        "support_preserved": set(probabilities) == set(target.joint_distribution()),
        "selected_private_hand_marginal_preserved": True,
    }


def _full_tree_state_count(state: GameState) -> int:
    if state.current_player == TERMINAL_PLAYER:
        return 1
    actions = (
        tuple(action for action, _ in state.chance_outcomes())
        if state.current_player == CHANCE_PLAYER
        else tuple(state.legal_actions())
    )
    return 1 + sum(_full_tree_state_count(state.apply_action(action)) for action in actions)


def _information_schema(game: RiverHoldem) -> dict[str, tuple[Action, ...]]:
    result: dict[str, tuple[Action, ...]] = {}
    for player in range(game.num_players):
        player_sets = collect_information_sets(game, player)
        overlap = set(result) & set(player_sets)
        if overlap:
            raise ValueError(f"information keys shared across players: {overlap!r}")
        result.update(player_sets)
    return result


def _policy_tv(
    first: Policy,
    second: Policy,
    schema: dict[str, tuple[Action, ...]],
) -> tuple[float, float]:
    distances = []
    for key, actions in schema.items():
        left = policy_distribution(first, key, actions)
        right = policy_distribution(second, key, actions)
        distances.append(0.5 * sum(abs(left[a] - right[a]) for a in actions))
    return mean(distances), max(distances, default=0.0)


def _arm_name(multiplier: float) -> str:
    rendered = format(multiplier, ".12g").replace(".", "_").replace("-", "m")
    return f"warm_span_{rendered}"


def _summaries(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cold = {
        (record["target_id"], record["checkpoint"]): record
        for record in records
        if record["arm"] == "cold"
    }
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(record["arm"], record["checkpoint"])].append(record)
    result = []
    for (arm, checkpoint), rows in sorted(grouped.items()):
        total_initial = sum(float(row["uniform_exploitability"]) for row in rows)
        total_final = sum(float(row["exploitability"]) for row in rows)
        total_charge = sum(float(row["one_shot_charged_milliseconds"]) for row in rows)
        paired_uplift = sum(
            float(cold[(row["target_id"], checkpoint)]["exploitability"])
            - float(row["exploitability"])
            for row in rows
        )
        result.append(
            {
                "arm": arm,
                "checkpoint": checkpoint,
                "targets": len(rows),
                "mean_exploitability": total_final / len(rows),
                "total_exploitability": total_final,
                "total_reduction_from_uniform": total_initial - total_final,
                "total_one_shot_charged_milliseconds": total_charge,
                "reduction_per_one_shot_charged_millisecond": (
                    (total_initial - total_final) / total_charge
                    if total_charge > 0.0
                    else None
                ),
                "paired_raw_uplift_over_cold": paired_uplift,
                "paired_wins_over_cold": sum(
                    float(row["exploitability"])
                    < float(cold[(row["target_id"], checkpoint)]["exploitability"])
                    - TOLERANCE
                    for row in rows
                ),
                "mean_initialization_milliseconds": mean(
                    float(row["initialization_milliseconds"]) for row in rows
                ),
                "mean_cumulative_solver_milliseconds": mean(
                    float(row["cumulative_solver_milliseconds"]) for row in rows
                ),
                "mean_exact_recertification_milliseconds": mean(
                    float(row["exact_recertification_milliseconds"]) for row in rows
                ),
                "total_state_visits": sum(int(row["state_visits"]) for row in rows),
            }
        )
    return result


def _select_arm(rows: list[dict[str, Any]], arms: tuple[str, ...]) -> str:
    totals = {
        arm: sum(float(row["exploitability"]) for row in rows if row["arm"] == arm)
        for arm in arms
    }
    return min(arms, key=lambda arm: (totals[arm], arm))


def _development_screen(
    records: list[dict[str, Any]],
    *,
    primary_checkpoint: int,
    warm_arms: tuple[str, ...],
    folds: int,
    minimum_residual_capture: float,
) -> dict[str, Any]:
    primary = [row for row in records if row["checkpoint"] == primary_checkpoint]
    fold_rows = []
    for held_out in range(folds):
        training = [row for row in primary if _fold(row["group_id"], folds) != held_out]
        testing = [row for row in primary if _fold(row["group_id"], folds) == held_out]
        if not training or not testing:
            raise ValueError("every development fold must contain training and test targets")
        selected = _select_arm(training, warm_arms)
        candidate = [row for row in testing if row["arm"] == selected]
        cold = [row for row in testing if row["arm"] == "cold"]
        candidate_final = sum(float(row["exploitability"]) for row in candidate)
        cold_final = sum(float(row["exploitability"]) for row in cold)
        oracle_final = sum(float(row["target_oracle_exploitability"]) for row in cold)
        initial = sum(float(row["uniform_exploitability"]) for row in cold)
        candidate_ms = sum(float(row["one_shot_charged_milliseconds"]) for row in candidate)
        cold_ms = sum(float(row["one_shot_charged_milliseconds"]) for row in cold)
        candidate_reduction = initial - candidate_final
        cold_reduction = initial - cold_final
        fold_rows.append(
            {
                "fold": held_out,
                "groups": len({row["group_id"] for row in cold}),
                "targets": len(cold),
                "selected_arm": selected,
                "candidate_final_exploitability": candidate_final,
                "cold_final_exploitability": cold_final,
                "raw_uplift_over_cold": cold_final - candidate_final,
                "cold_residual_removed_fraction": (
                    (cold_final - candidate_final) / (cold_final - oracle_final)
                    if cold_final - oracle_final > 0.0
                    else 0.0
                ),
                "candidate_reduction_per_millisecond": candidate_reduction / candidate_ms,
                "cold_reduction_per_millisecond": cold_reduction / cold_ms,
                "rate_uplift_fraction": (
                    (candidate_reduction / candidate_ms) / (cold_reduction / cold_ms) - 1.0
                ),
                "candidate_state_visits": sum(int(row["state_visits"]) for row in candidate),
                "cold_state_visits": sum(int(row["state_visits"]) for row in cold),
            }
        )

    total_candidate_final = sum(row["candidate_final_exploitability"] for row in fold_rows)
    total_cold_final = sum(row["cold_final_exploitability"] for row in fold_rows)
    total_oracle_final = sum(
        float(row["target_oracle_exploitability"])
        for row in primary
        if row["arm"] == "cold"
    )
    all_development_choice = _select_arm(primary, warm_arms)
    gates = {
        "strict_raw_improvement_in_every_fold": all(
            row["raw_uplift_over_cold"] > TOLERANCE for row in fold_rows
        ),
        "aggregate_cold_residual_capture_at_least_threshold": (
            (total_cold_final - total_candidate_final)
            / (total_cold_final - total_oracle_final)
            >= minimum_residual_capture
        ),
        "charged_rate_improves_in_every_fold": all(
            row["rate_uplift_fraction"] > 0.0 for row in fold_rows
        ),
        "state_visits_not_above_cold_in_every_fold": all(
            row["candidate_state_visits"] <= row["cold_state_visits"]
            for row in fold_rows
        ),
    }
    return {
        "selection_is_development_only": True,
        "selection_objective": "minimum aggregate final exploitability at matched checkpoint and traversal work",
        "primary_checkpoint": primary_checkpoint,
        "folds": fold_rows,
        "aggregate": {
            "candidate_final_exploitability": total_candidate_final,
            "cold_final_exploitability": total_cold_final,
            "target_oracle_exploitability": total_oracle_final,
            "raw_uplift_over_cold": total_cold_final - total_candidate_final,
            "cold_residual_removed_fraction": (
                (total_cold_final - total_candidate_final)
                / (total_cold_final - total_oracle_final)
            ),
        },
        "all_development_selected_arm": all_development_choice,
        "gates": gates,
        "passed": all(gates.values()),
    }


def _validate_config(config: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "groups",
        "seed",
        "hands_per_player",
        "families",
        "included_splits",
        "sequential_raise",
        "perturbations",
        "solver",
        "checkpoints",
        "warm_start_regret_mass_by_payoff_span",
        "certification_normalized_exploitability_thresholds",
        "primary_checkpoint",
        "folds",
        "minimum_cold_residual_capture",
    }
    unknown = set(config) - allowed
    if unknown:
        raise ValueError(f"unknown range-reuse config fields: {sorted(unknown)!r}")
    groups = int(config.get("groups", 8))
    seed = int(config.get("seed", 0))
    hands = int(config.get("hands_per_player", 4))
    families = tuple(str(item) for item in config.get("families", CONTEXT_FAMILIES))
    splits = tuple(str(item) for item in config.get("included_splits", ("development",)))
    sequential = config.get("sequential_raise", True)
    solver = str(config.get("solver", "dcfr"))
    checkpoints = tuple(int(item) for item in config.get("checkpoints", DEFAULT_CHECKPOINTS))
    multipliers = tuple(
        float(item)
        for item in config.get(
            "warm_start_regret_mass_by_payoff_span",
            (0.01, 0.03, 0.1, 0.3),
        )
    )
    thresholds = tuple(
        float(item)
        for item in config.get(
            "certification_normalized_exploitability_thresholds",
            (0.001, 0.005, 0.01, 0.02),
        )
    )
    primary = int(config.get("primary_checkpoint", 4))
    folds = int(config.get("folds", 5))
    minimum_capture = float(config.get("minimum_cold_residual_capture", 0.25))
    perturbations = config.get("perturbations")

    if groups <= 0:
        raise ValueError("groups must be positive")
    if not 2 <= hands <= 5:
        raise ValueError("hands_per_player must be between two and five")
    if not families or len(set(families)) != len(families) or set(families) - set(CONTEXT_FAMILIES):
        raise ValueError("families must be unique supported context families")
    if splits != ("development",):
        raise ValueError("the range-reuse screen is development-only")
    if sequential is not True:
        raise ValueError("sequential_raise must be true")
    if solver not in UPDATE_RULES:
        raise ValueError(f"unsupported solver {solver!r}")
    if not checkpoints or checkpoints[0] != 0 or checkpoints != tuple(sorted(set(checkpoints))):
        raise ValueError("checkpoints must be sorted, unique, and begin at zero")
    if primary not in checkpoints or primary <= 0:
        raise ValueError("primary_checkpoint must be a positive recorded checkpoint")
    if not multipliers or len(set(multipliers)) != len(multipliers) or any(
        not isfinite(value) or value <= 0.0 for value in multipliers
    ):
        raise ValueError("warm-start multipliers must be unique finite positive values")
    if not thresholds or thresholds != tuple(sorted(set(thresholds))) or any(
        not isfinite(value) or value <= 0.0 for value in thresholds
    ):
        raise ValueError("certification thresholds must be sorted unique positive values")
    if folds < 2:
        raise ValueError("folds must be at least two")
    if not 0.0 < minimum_capture <= 1.0:
        raise ValueError("minimum_cold_residual_capture must be in (0, 1]")
    if not isinstance(perturbations, list) or not perturbations:
        raise ValueError("perturbations must be a nonempty array")
    names = []
    normalized_perturbations = []
    for item in perturbations:
        if not isinstance(item, dict) or set(item) != {
            "name", "player", "root_tv_budget", "maximum_donor_fraction"
        }:
            raise ValueError("each perturbation must contain exactly the frozen fields")
        name = str(item["name"])
        if not name:
            raise ValueError("perturbation names must be nonempty")
        names.append(name)
        normalized_perturbations.append(
            {
                "name": name,
                "player": int(item["player"]),
                "root_tv_budget": float(item["root_tv_budget"]),
                "maximum_donor_fraction": float(item["maximum_donor_fraction"]),
            }
        )
    if len(set(names)) != len(names):
        raise ValueError("perturbation names must be unique")

    return {
        "groups": groups,
        "seed": seed,
        "hands_per_player": hands,
        "families": families,
        "included_splits": splits,
        "sequential_raise": True,
        "perturbations": tuple(normalized_perturbations),
        "solver": solver,
        "checkpoints": checkpoints,
        "warm_start_regret_mass_by_payoff_span": multipliers,
        "certification_normalized_exploitability_thresholds": thresholds,
        "primary_checkpoint": primary,
        "folds": folds,
        "minimum_cold_residual_capture": minimum_capture,
    }


def run_river_range_reuse_experiment(config: dict[str, Any]) -> dict[str, Any]:
    parsed = _validate_config(config)
    experiment_start = time.perf_counter()
    contexts = generate_river_contexts(
        groups=parsed["groups"],
        seed=parsed["seed"],
        hands_per_player=parsed["hands_per_player"],
        families=parsed["families"],
        splits=parsed["included_splits"],
        sequential_raise=True,
    )
    if not contexts:
        raise ValueError("configuration generated no development contexts")

    records: list[dict[str, Any]] = []
    pair_records: list[dict[str, Any]] = []
    source_records = []
    oracle_seconds = 0.0
    solver_seconds = 0.0
    recertification_seconds = 0.0
    cache_seconds = 0.0
    initialization_seconds = 0.0
    topology_schema_build_seconds = 0.0

    for context in contexts:
        source_oracle_start = time.perf_counter()
        source_oracle = solve_river_game(context.game)
        source_oracle_seconds = time.perf_counter() - source_oracle_start
        oracle_seconds += source_oracle_seconds
        schema_start = time.perf_counter()
        schema = _information_schema(context.game)
        schema_seconds = time.perf_counter() - schema_start
        topology_schema_build_seconds += schema_seconds
        serialized = serialize_river_context(context)
        serialized["oracle_labels"] = {
            "nash_conv": source_oracle.nash_conv,
            "duality_gap": source_oracle.matrix_solution.duality_gap,
            "solve_milliseconds": source_oracle_seconds * 1_000.0,
            "topology_schema_build_milliseconds": schema_seconds * 1_000.0,
        }
        source_records.append(serialized)

        exact_lookup_start = time.perf_counter()
        exact_hit = exact_strategy_cache_lookup(
            context.game,
            context.game,
            source_oracle.policy,
        )
        exact_lookup_seconds = time.perf_counter() - exact_lookup_start
        cache_seconds += exact_lookup_seconds
        if exact_hit is None:
            raise AssertionError("identical provenance failed exact cache lookup")

        for perturbation in parsed["perturbations"]:
            target, mutation = make_blocker_perturbation(
                context.game,
                player=perturbation["player"],
                root_tv_budget=perturbation["root_tv_budget"],
                maximum_donor_fraction=perturbation["maximum_donor_fraction"],
            )
            target_id = f"{context.context_id}::{perturbation['name']}"

            assessment_start = time.perf_counter()
            assessment = assess_river_range_reuse(context.game, target)
            assessment_seconds = time.perf_counter() - assessment_start
            cache_seconds += assessment_seconds
            if assessment.direct_strategy_deployable or assessment.match != "structural_only":
                raise AssertionError("range-different target was treated as deployable")

            lookup_start = time.perf_counter()
            forbidden_direct = exact_strategy_cache_lookup(
                context.game,
                target,
                source_oracle.policy,
            )
            warm_hint = structural_warm_start_hint(
                context.game,
                target,
                source_oracle.policy,
            )
            warm_schema = structural_information_schema_lookup(
                context.game,
                target,
                schema,
            )
            structural_lookup_seconds = time.perf_counter() - lookup_start
            cache_seconds += structural_lookup_seconds
            if forbidden_direct is not None or warm_hint is None or warm_schema is None:
                raise AssertionError("cache identity boundary was violated")

            certificate_start = time.perf_counter()
            certificate = transferred_exploitability_certificate(
                context.game,
                target,
                source_exploitability=source_oracle.nash_conv / 2.0,
            )
            certificate_seconds = time.perf_counter() - certificate_start
            cache_seconds += certificate_seconds

            target_oracle_start = time.perf_counter()
            target_oracle = solve_river_game(target)
            target_oracle_seconds = time.perf_counter() - target_oracle_start
            oracle_seconds += target_oracle_seconds
            target_schema = _information_schema(target)
            if schema != target_schema:
                raise AssertionError("support-preserving perturbation changed information schema")

            stale_start = time.perf_counter()
            stale_evaluation = evaluate_profile(target, warm_hint)
            stale_seconds = time.perf_counter() - stale_start
            recertification_seconds += stale_seconds
            uniform_start = time.perf_counter()
            uniform_evaluation = evaluate_profile(target, {})
            uniform_seconds = time.perf_counter() - uniform_start
            recertification_seconds += uniform_seconds
            if stale_evaluation.exploitability is None or uniform_evaluation.exploitability is None:
                raise AssertionError("heads-up target must report exploitability")
            if stale_evaluation.exploitability > certificate.capped_target_upper_bound + 1e-9:
                raise AssertionError("TV exploitability certificate was violated")
            mean_policy_tv, maximum_policy_tv = _policy_tv(
                source_oracle.policy,
                target_oracle.policy,
                target_schema,
            )
            threshold_results = []
            for threshold in parsed["certification_normalized_exploitability_thresholds"]:
                threshold_results.append(
                    {
                        "normalized_threshold": threshold,
                        "tv_bound_certifies": (
                            certificate.capped_target_upper_bound / target.payoff_span
                            <= threshold
                        ),
                        "exact_target_recertification_passes": (
                            stale_evaluation.exploitability / target.payoff_span <= threshold
                        ),
                    }
                )

            pair_records.append(
                {
                    "target_id": target_id,
                    "context_id": context.context_id,
                    "group_id": context.group_id,
                    "family": context.family,
                    "perturbation": perturbation["name"],
                    "source_structural_digest": context.game.structural_digest,
                    "source_provenance_digest": context.game.provenance_digest,
                    "target_provenance_digest": target.provenance_digest,
                    "mutation": mutation,
                    "reuse_assessment": assessment.to_dict(),
                    "exploitability_transfer_certificate": certificate.to_dict(),
                    "threshold_results": threshold_results,
                    "source_oracle_exploitability": source_oracle.nash_conv / 2.0,
                    "target_oracle_exploitability": target_oracle.nash_conv / 2.0,
                    "stale_policy_target_exploitability": stale_evaluation.exploitability,
                    "uniform_target_exploitability": uniform_evaluation.exploitability,
                    "source_to_target_oracle_mean_information_set_tv": mean_policy_tv,
                    "source_to_target_oracle_maximum_information_set_tv": maximum_policy_tv,
                    "timing": {
                        "exact_hit_lookup_milliseconds": exact_lookup_seconds * 1_000.0,
                        "range_assessment_milliseconds": assessment_seconds * 1_000.0,
                        "structural_lookup_milliseconds": structural_lookup_seconds * 1_000.0,
                        "tv_certificate_milliseconds": certificate_seconds * 1_000.0,
                        "stale_exact_recertification_milliseconds": stale_seconds * 1_000.0,
                        "uniform_exact_evaluation_milliseconds": uniform_seconds * 1_000.0,
                        "source_oracle_milliseconds": source_oracle_seconds * 1_000.0,
                        "target_oracle_milliseconds": target_oracle_seconds * 1_000.0,
                    },
                }
            )

            arms = [("cold", None)] + [
                (_arm_name(multiplier), multiplier)
                for multiplier in parsed["warm_start_regret_mass_by_payoff_span"]
            ]
            tree_states = _full_tree_state_count(target.initial_state())
            for arm, multiplier in arms:
                construction_start = time.perf_counter()
                solver = TabularCFR(target, variant=parsed["solver"])
                construction_seconds = time.perf_counter() - construction_start
                arm_initialization_seconds = construction_seconds
                if multiplier is not None:
                    warm_start = time.perf_counter()
                    solver.warm_start_from_schema(
                        warm_hint,
                        regret_mass=target.payoff_span * multiplier,
                        information_sets=warm_schema,
                    )
                    arm_initialization_seconds += time.perf_counter() - warm_start
                initialization_seconds += arm_initialization_seconds

                previous_checkpoint = 0
                cumulative_solver_seconds = 0.0
                cumulative_recertification_seconds = 0.0
                for checkpoint in parsed["checkpoints"]:
                    interval_seconds = 0.0
                    if checkpoint > previous_checkpoint:
                        solve_start = time.perf_counter()
                        solver.run(checkpoint - previous_checkpoint)
                        interval_seconds = time.perf_counter() - solve_start
                        cumulative_solver_seconds += interval_seconds
                        solver_seconds += interval_seconds
                    policy = solver.average_strategy()
                    evaluation_start = time.perf_counter()
                    evaluation = evaluate_profile(target, policy)
                    evaluation_seconds = time.perf_counter() - evaluation_start
                    recertification_seconds += evaluation_seconds
                    cumulative_recertification_seconds += evaluation_seconds
                    if evaluation.exploitability is None:
                        raise AssertionError("heads-up target must report exploitability")
                    lookup_milliseconds = (
                        0.0
                        if multiplier is None
                        else structural_lookup_seconds * 1_000.0
                    )
                    one_shot_ms = (
                        lookup_milliseconds
                        + arm_initialization_seconds * 1_000.0
                        + cumulative_solver_seconds * 1_000.0
                        + evaluation_seconds * 1_000.0
                    )
                    records.append(
                        {
                            "target_id": target_id,
                            "context_id": context.context_id,
                            "group_id": context.group_id,
                            "family": context.family,
                            "perturbation": perturbation["name"],
                            "arm": arm,
                            "warm_start_regret_mass_by_payoff_span": multiplier,
                            "checkpoint": checkpoint,
                            "exploitability": evaluation.exploitability,
                            "target_oracle_exploitability": target_oracle.nash_conv / 2.0,
                            "normalized_exploitability": evaluation.exploitability / target.payoff_span,
                            "uniform_exploitability": uniform_evaluation.exploitability,
                            "reduction_from_uniform": uniform_evaluation.exploitability - evaluation.exploitability,
                            "state_visits": checkpoint * target.num_players * tree_states,
                            "cached_schema_entries": len(warm_schema) if multiplier is not None else 0,
                            "initialization_milliseconds": arm_initialization_seconds * 1_000.0,
                            "interval_solver_milliseconds": interval_seconds * 1_000.0,
                            "cumulative_solver_milliseconds": cumulative_solver_seconds * 1_000.0,
                            "exact_recertification_milliseconds": evaluation_seconds * 1_000.0,
                            "cumulative_anytime_recertification_milliseconds": cumulative_recertification_seconds * 1_000.0,
                            "cache_lookup_milliseconds": lookup_milliseconds,
                            "one_shot_charged_milliseconds": one_shot_ms,
                            "reduction_per_one_shot_charged_millisecond": (
                                (uniform_evaluation.exploitability - evaluation.exploitability) / one_shot_ms
                                if one_shot_ms > 0.0
                                else None
                            ),
                        }
                    )
                    previous_checkpoint = checkpoint

    summaries = _summaries(records)
    warm_arms = tuple(_arm_name(value) for value in parsed["warm_start_regret_mass_by_payoff_span"])
    screen = _development_screen(
        records,
        primary_checkpoint=parsed["primary_checkpoint"],
        warm_arms=warm_arms,
        folds=parsed["folds"],
        minimum_residual_capture=parsed["minimum_cold_residual_capture"],
    )
    threshold_summary = []
    for threshold in parsed["certification_normalized_exploitability_thresholds"]:
        entries = [
            item
            for pair in pair_records
            for item in pair["threshold_results"]
            if item["normalized_threshold"] == threshold
        ]
        threshold_summary.append(
            {
                "normalized_threshold": threshold,
                "pairs": len(entries),
                "tv_bound_certified": sum(item["tv_bound_certifies"] for item in entries),
                "exact_stale_policy_passed": sum(
                    item["exact_target_recertification_passes"] for item in entries
                ),
                "bound_false_positives": sum(
                    item["tv_bound_certifies"]
                    and not item["exact_target_recertification_passes"]
                    for item in entries
                ),
                "bound_false_negatives": sum(
                    not item["tv_bound_certifies"]
                    and item["exact_target_recertification_passes"]
                    for item in entries
                ),
            }
        )

    return {
        "schema_version": 1,
        "experiment_type": "exact_river_range_reuse_and_recertification",
        "status": "development_measurement_only",
        "config": {
            **parsed,
            "families": list(parsed["families"]),
            "included_splits": list(parsed["included_splits"]),
            "perturbations": list(parsed["perturbations"]),
            "checkpoints": list(parsed["checkpoints"]),
            "warm_start_regret_mass_by_payoff_span": list(
                parsed["warm_start_regret_mass_by_payoff_span"]
            ),
            "certification_normalized_exploitability_thresholds": list(
                parsed["certification_normalized_exploitability_thresholds"]
            ),
        },
        "environment": environment_metadata(),
        "safety_contract": {
            "exact_provenance_required_for_direct_strategy_deployment": True,
            "root_or_conditional_range_distance_never_creates_a_cache_hit": True,
            "structural_match_reuses_only_schema_and_a_nondeployable_hint": True,
            "range_different_policy_requires_current_range_recertification": True,
            "tv_certificate_is_two_player_zero_sum_only": True,
            "oracle_and_exact_recertification_are_diagnostic_not_solver_inputs": True,
        },
        "counts": {
            "groups": len({context.group_id for context in contexts}),
            "source_contexts": len(contexts),
            "range_pairs": len(pair_records),
            "arms_per_pair": 1 + len(warm_arms),
            "trajectory_records": len(records),
        },
        "timing": {
            "oracle_seconds": oracle_seconds,
            "solver_seconds": solver_seconds,
            "exact_recertification_seconds": recertification_seconds,
            "cache_and_range_assessment_seconds": cache_seconds,
            "solver_initialization_seconds": initialization_seconds,
            "topology_schema_build_seconds": topology_schema_build_seconds,
            "wall_seconds": time.perf_counter() - experiment_start,
        },
        "tv_certificate_summary": threshold_summary,
        "development_screen": screen,
        "summaries": summaries,
        "sources": source_records,
        "pairs": pair_records,
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
    result = run_river_range_reuse_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "exact river range reuse: "
        f"pairs={result['counts']['range_pairs']}, "
        f"records={result['counts']['trajectory_records']}, "
        f"screen_passed={result['development_screen']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
