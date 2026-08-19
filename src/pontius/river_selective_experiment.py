"""Development-only full-universe quality/work experiments for selective trees."""

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
from .evaluation import EvaluationResult, Policy, evaluate_profile, policy_distribution
from .game import CHANCE_PLAYER, TERMINAL_PLAYER, Action, GameState
from .reporting import environment_metadata
from .river import CALL, CHECK, FOLD, RiverHoldem
from .river_context import (
    CONTEXT_FAMILIES,
    RiverContext,
    generate_river_contexts,
    river_context_features,
)
from .river_incremental import RiverRangeDelta
from .river_multi_size import (
    BetAction,
    MultiSizeRiverHoldem,
    MultiSizeRiverState,
    RaiseToAction,
)
from .river_multi_size_experiment import _factorized_likelihood_target
from .river_range_reuse import make_blocker_perturbation
from .river_selective import (
    MultiSizeExpansionMask,
    complete_information_schema,
    compose_selective_policy,
    multi_size_state_cache_key,
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
_EVIDENCE_STAGES = ("pilot", "group_separated_development")
_BOUNDARY_FEATURE_FAMILIES = (
    "source_context",
    "target_context",
    "context_delta",
    "range_delta",
    "target_blueprint_public_policy",
)
_FORBIDDEN_FEATURE_FRAGMENTS = (
    "nash",
    "exploit",
    "best_response",
    "future",
    "gain",
    "label",
    "reduction",
    "oracle",
)


def _positive_finite(value: float) -> bool:
    return math.isfinite(value) and value > 0.0


def _validate_config(config: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "evidence_stage",
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
        "blueprint_quality_checkpoints",
        "online_solver",
        "warm_start_multipliers_by_payoff_span",
        "full_tree_equivalent_iteration_budgets",
        "target_names",
        "root_tv_budget",
        "maximum_donor_fraction",
        "factorized_likelihood_minimum",
        "factorized_likelihood_maximum",
        "boundary_feature_families",
        "record_solver_probe_features",
        "expected_selective_tree_sha256",
        "expected_river_selective_sha256",
        "gates",
    }
    unknown = set(config) - allowed
    if unknown:
        raise ValueError(f"unknown selective-expansion fields: {sorted(unknown)!r}")

    evidence_stage = str(config.get("evidence_stage", "pilot"))
    groups = int(config.get("groups", 3))
    seed = int(config.get("seed", 0))
    hands = int(config.get("hands_per_player", 4))
    families = tuple(str(value) for value in config.get("families", CONTEXT_FAMILIES))
    splits = tuple(str(value) for value in config.get("included_splits", ("development",)))
    bets = tuple(float(value) for value in config.get("bet_pot_fractions", (0.25, 0.5, 0.75)))
    raises = tuple(float(value) for value in config.get("raise_to_pot_fractions", (1.5, 2.0)))
    blueprint_solver = str(config.get("blueprint_solver", "dcfr"))
    raw_blueprint_iterations = config.get("blueprint_iterations")
    blueprint_iterations = (
        None if raw_blueprint_iterations is None else int(raw_blueprint_iterations)
    )
    raw_quality_checkpoints = config.get("blueprint_quality_checkpoints")
    quality_checkpoints = (
        ()
        if raw_quality_checkpoints is None
        else tuple(int(value) for value in raw_quality_checkpoints)
    )
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
    feature_families = tuple(
        str(value)
        for value in config.get("boundary_feature_families", ())
    )
    record_probe_features = config.get("record_solver_probe_features", False)
    expected_selective_sha = str(config.get("expected_selective_tree_sha256", ""))
    expected_river_selective_sha = str(
        config.get("expected_river_selective_sha256", "")
    )
    raw_gates = config.get("gates")

    if evidence_stage not in _EVIDENCE_STAGES:
        raise ValueError(f"unsupported evidence_stage {evidence_stage!r}")
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
    if evidence_stage == "pilot":
        if blueprint_iterations is None or blueprint_iterations <= 0:
            raise ValueError("blueprint_iterations must be positive")
        if quality_checkpoints:
            raise ValueError("pilot cannot select blueprint quality checkpoints")
        normalized_gates: dict[str, float | int] = {}
        if any(
            (
                feature_families,
                bool(record_probe_features),
                expected_selective_sha,
                expected_river_selective_sha,
                raw_gates is not None,
            )
        ):
            raise ValueError("pilot cannot contain development-matrix controls")
    else:
        if blueprint_iterations is not None:
            raise ValueError("development matrix must use blueprint quality checkpoints")
        if (
            not quality_checkpoints
            or quality_checkpoints != tuple(sorted(set(quality_checkpoints)))
            or quality_checkpoints[0] <= 0
        ):
            raise ValueError("blueprint quality checkpoints must be sorted and positive")
        if len(warm_multipliers) != 1:
            raise ValueError("development matrix must freeze one warm-start multiplier")
        if feature_families != _BOUNDARY_FEATURE_FAMILIES:
            raise ValueError("development boundary feature families must match ADR-0041")
        if not isinstance(record_probe_features, bool) or not record_probe_features:
            raise ValueError("development matrix must record solver probe features")
        for label, digest in (
            ("expected_selective_tree_sha256", expected_selective_sha),
            ("expected_river_selective_sha256", expected_river_selective_sha),
        ):
            if len(digest) != 64 or any(
                character not in "0123456789abcdef" for character in digest
            ):
                raise ValueError(f"{label} must be lowercase SHA-256")
        gate_names = {
            "minimum_development_board_groups",
            "maximum_source_normalized_nash_conv",
            "primary_full_tree_equivalent_iteration_budget",
            "minimum_mask_no_op_oracle_relative_uplift",
            "minimum_positive_group_uplift_fraction",
        }
        if not isinstance(raw_gates, dict) or set(raw_gates) != gate_names:
            raise ValueError("development gates must match ADR-0041 exactly")
        normalized_gates = {
            "minimum_development_board_groups": int(
                raw_gates["minimum_development_board_groups"]
            ),
            "maximum_source_normalized_nash_conv": float(
                raw_gates["maximum_source_normalized_nash_conv"]
            ),
            "primary_full_tree_equivalent_iteration_budget": int(
                raw_gates["primary_full_tree_equivalent_iteration_budget"]
            ),
            "minimum_mask_no_op_oracle_relative_uplift": float(
                raw_gates["minimum_mask_no_op_oracle_relative_uplift"]
            ),
            "minimum_positive_group_uplift_fraction": float(
                raw_gates["minimum_positive_group_uplift_fraction"]
            ),
        }
        if normalized_gates["minimum_development_board_groups"] <= 0:
            raise ValueError("minimum development board groups must be positive")
        if not _positive_finite(
            float(normalized_gates["maximum_source_normalized_nash_conv"])
        ):
            raise ValueError("maximum source normalized NashConv must be positive")
        primary_budget = int(
            normalized_gates["primary_full_tree_equivalent_iteration_budget"]
        )
        if primary_budget not in budgets:
            raise ValueError("primary opportunity budget must be one recorded budget")
        relative_gate = float(
            normalized_gates["minimum_mask_no_op_oracle_relative_uplift"]
        )
        group_gate = float(
            normalized_gates["minimum_positive_group_uplift_fraction"]
        )
        if not 0.0 <= relative_gate <= 1.0 or not 0.0 <= group_gate <= 1.0:
            raise ValueError("opportunity gates must lie between zero and one")
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
        "evidence_stage": evidence_stage,
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
        "blueprint_quality_checkpoints": quality_checkpoints,
        "online_solver": online_solver,
        "warm_start_multipliers_by_payoff_span": warm_multipliers,
        "full_tree_equivalent_iteration_budgets": budgets,
        "target_names": target_names,
        "root_tv_budget": root_tv,
        "maximum_donor_fraction": donor_fraction,
        "factorized_likelihood_minimum": likelihood_minimum,
        "factorized_likelihood_maximum": likelihood_maximum,
        "boundary_feature_families": feature_families,
        "record_solver_probe_features": bool(record_probe_features),
        "expected_selective_tree_sha256": expected_selective_sha,
        "expected_river_selective_sha256": expected_river_selective_sha,
        "gates": normalized_gates,
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


def _source_file_sha256(filename: str) -> str:
    return hashlib.sha256(Path(__file__).with_name(filename).read_bytes()).hexdigest()


def _action_feature_token(game: MultiSizeRiverHoldem, action: Action) -> str:
    if action in (CHECK, FOLD, CALL):
        return str(action)
    if isinstance(action, BetAction):
        return f"bet_{game.bet_actions.index(action)}"
    if isinstance(action, RaiseToAction):
        return f"raise_{game.raise_actions.index(action)}"
    raise TypeError(f"unsupported public action {action!r}")


def _public_node_feature_token(state: MultiSizeRiverState) -> str:
    if not state.history:
        return "root"
    first = state.history[0][1]
    if not isinstance(first, BetAction):
        raise ValueError("nonterminal multi-size history must begin with a bet")
    bet_index = state.game.bet_actions.index(first)
    if len(state.history) == 1:
        return f"facing_bet_{bet_index}"
    second = state.history[1][1]
    if not isinstance(second, RaiseToAction):
        raise ValueError("three-action multi-size history must contain a raise")
    raise_index = state.game.raise_actions.index(second)
    return f"facing_bet_{bet_index}_raise_{raise_index}"


def _blueprint_public_policy_features(
    game: MultiSizeRiverHoldem,
    blueprint: Policy,
) -> dict[str, float]:
    node_reach: dict[str, float] = defaultdict(float)
    action_mass: dict[tuple[str, str], float] = defaultdict(float)
    weighted_entropy = 0.0
    weighted_max_probability = 0.0
    total_decision_reach = 0.0

    def walk(state: GameState, reach: float) -> None:
        nonlocal weighted_entropy, weighted_max_probability, total_decision_reach
        acting = state.current_player
        if acting == TERMINAL_PLAYER:
            return
        if acting == CHANCE_PLAYER:
            for action, probability in state.chance_outcomes():
                walk(state.apply_action(action), reach * probability)
            return
        if not isinstance(state, MultiSizeRiverState):
            raise TypeError("public policy features require MultiSizeRiverState")
        actions = tuple(state.legal_actions())
        distribution = policy_distribution(
            blueprint,
            state.information_state_key(acting),
            actions,
        )
        node = _public_node_feature_token(state)
        node_reach[node] += reach
        entropy = -sum(
            probability * math.log(probability)
            for probability in distribution.values()
            if probability > 0.0
        )
        weighted_entropy += reach * entropy
        weighted_max_probability += reach * max(distribution.values())
        total_decision_reach += reach
        for action, probability in distribution.items():
            token = _action_feature_token(game, action)
            action_mass[(node, token)] += reach * probability
            walk(state.apply_action(action), reach * probability)

    walk(game.initial_state(), 1.0)
    result: dict[str, float] = {
        "blueprint_weighted_information_entropy": (
            weighted_entropy / total_decision_reach
            if total_decision_reach > 0.0
            else 0.0
        ),
        "blueprint_weighted_max_action_probability": (
            weighted_max_probability / total_decision_reach
            if total_decision_reach > 0.0
            else 0.0
        ),
        "blueprint_total_decision_reach": total_decision_reach,
    }
    for node, reach in sorted(node_reach.items()):
        result[f"blueprint_{node}_reach_mass"] = reach
        for (action_node, action), mass in sorted(action_mass.items()):
            if action_node == node:
                result[f"blueprint_{node}_{action}_conditional_mass"] = (
                    mass / reach if reach > 0.0 else 0.0
                )
    return result


def _validate_online_features(features: dict[str, float]) -> None:
    if not features:
        raise ValueError("online feature map must be nonempty")
    for name, value in features.items():
        lowered = name.lower()
        if any(fragment in lowered for fragment in _FORBIDDEN_FEATURE_FRAGMENTS):
            raise ValueError(f"online feature {name!r} contains a forbidden label fragment")
        if not math.isfinite(float(value)):
            raise ValueError(f"online feature {name!r} is nonfinite")


def _boundary_online_features(
    context: RiverContext,
    target_range: RiverHoldem,
    target_game: MultiSizeRiverHoldem,
    blueprint: Policy,
    range_delta: RiverRangeDelta,
) -> dict[str, float]:
    source_context = river_context_features(context)
    target_context = river_context_features(
        RiverContext(
            context_id=context.context_id,
            group_id=context.group_id,
            split=context.split,
            family=context.family,
            seed=context.seed,
            game=target_range,
        )
    )
    features: dict[str, float] = {}
    shared_numeric = []
    for key, value in source_context.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        target_value = target_context[key]
        if isinstance(target_value, bool) or not isinstance(target_value, (int, float)):
            raise AssertionError("source and target context feature types differ")
        source_float = float(value)
        target_float = float(target_value)
        features[f"source_{key}"] = source_float
        features[f"target_{key}"] = target_float
        shared_numeric.append((key, source_float, target_float))
    for key, source_value, target_value in shared_numeric:
        features[f"change_{key}"] = target_value - source_value

    deltas = [change.probability_delta for change in range_delta.changes]
    absolute = [abs(value) for value in deltas]
    absolute_mass = sum(absolute)
    support_changes = sum(
        change.source_probability == 0.0 or change.target_probability == 0.0
        for change in range_delta.changes
    )
    joint_support = len(
        set(context.game.joint_distribution()) | set(target_range.joint_distribution())
    )
    features.update(
        {
            "range_delta_changed_deals": float(len(deltas)),
            "range_delta_changed_deal_fraction": len(deltas) / joint_support,
            "range_delta_total_variation": range_delta.total_variation,
            "range_delta_maximum_absolute_probability": max(absolute, default=0.0),
            "range_delta_l2_probability": math.sqrt(sum(value * value for value in deltas)),
            "range_delta_absolute_concentration": (
                sum(value * value for value in absolute) / (absolute_mass * absolute_mass)
                if absolute_mass > 0.0
                else 0.0
            ),
            "range_delta_support_change_fraction": (
                support_changes / len(deltas) if deltas else 0.0
            ),
        }
    )
    features.update(_blueprint_public_policy_features(target_game, blueprint))
    _validate_online_features(features)
    return dict(sorted(features.items()))


def _solver_probe_features(
    solver: TabularCFR,
    blueprint: Policy,
    average_policy: Policy,
    information_sets: dict[str, tuple[Action, ...]],
    payoff_span: float,
) -> dict[str, float]:
    regrets = [
        regret
        for data in solver.information_sets.values()
        for regret in data.regrets.values()
    ]
    positive = [max(0.0, regret) for regret in regrets]
    negative = [max(0.0, -regret) for regret in regrets]
    positive_mass = sum(positive)
    negative_mass = sum(negative)
    mean_tv, max_tv, changed = _policy_tv(
        blueprint,
        average_policy,
        information_sets,
    )
    features = {
        "probe_solver_iterations": float(solver.iteration),
        "probe_regret_entries": float(len(regrets)),
        "probe_positive_entry_fraction": (
            sum(value > 0.0 for value in regrets) / len(regrets)
            if regrets
            else 0.0
        ),
        "probe_normalized_positive_regret_mass": positive_mass / payoff_span,
        "probe_normalized_negative_regret_mass": negative_mass / payoff_span,
        "probe_normalized_maximum_positive_regret": (
            max(positive, default=0.0) / payoff_span
        ),
        "probe_positive_regret_concentration": (
            sum(value * value for value in positive) / (positive_mass * positive_mass)
            if positive_mass > 0.0
            else 0.0
        ),
        "probe_mean_policy_total_variation": mean_tv,
        "probe_maximum_policy_total_variation": max_tv,
        "probe_changed_information_set_fraction": (
            changed / len(information_sets) if information_sets else 0.0
        ),
    }
    _validate_online_features(features)
    return features


def _build_blueprint(
    source: MultiSizeRiverHoldem,
    parsed: dict[str, Any],
) -> tuple[Policy, EvaluationResult, dict[str, object]]:
    solver = TabularCFR(source, variant=parsed["blueprint_solver"])
    checkpoints = (
        (int(parsed["blueprint_iterations"]),)
        if parsed["evidence_stage"] == "pilot"
        else parsed["blueprint_quality_checkpoints"]
    )
    threshold = (
        None
        if parsed["evidence_stage"] == "pilot"
        else float(parsed["gates"]["maximum_source_normalized_nash_conv"])
    )
    previous = 0
    solve_seconds = 0.0
    evaluation_seconds = 0.0
    trajectory: list[dict[str, float | int]] = []
    selected_policy: Policy | None = None
    selected_evaluation: EvaluationResult | None = None
    quality_passed = threshold is None

    for checkpoint in checkpoints:
        solve_start = time.perf_counter()
        solver.run(checkpoint - previous)
        solve_seconds += time.perf_counter() - solve_start
        previous = checkpoint
        policy = solver.average_strategy()
        evaluation_start = time.perf_counter()
        evaluation = evaluate_profile(source, policy)
        checkpoint_evaluation_seconds = time.perf_counter() - evaluation_start
        evaluation_seconds += checkpoint_evaluation_seconds
        normalized = evaluation.nash_conv / source.payoff_span
        trajectory.append(
            {
                "iterations": checkpoint,
                "source_nash_conv": evaluation.nash_conv,
                "source_normalized_nash_conv": normalized,
                "exact_evaluation_seconds": checkpoint_evaluation_seconds,
            }
        )
        selected_policy = policy
        selected_evaluation = evaluation
        if threshold is None or normalized <= threshold:
            quality_passed = True
            break

    assert selected_policy is not None and selected_evaluation is not None
    return (
        selected_policy,
        selected_evaluation,
        {
            "iterations": previous,
            "solve_seconds": solve_seconds,
            "exact_evaluation_seconds": evaluation_seconds,
            "source_nash_conv": selected_evaluation.nash_conv,
            "source_exploitability": selected_evaluation.exploitability,
            "source_normalized_nash_conv": (
                selected_evaluation.nash_conv / source.payoff_span
            ),
            "quality_threshold_passed": quality_passed,
            "quality_trajectory": trajectory,
        },
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


def _fixed_warm_mask_oracle(
    records: list[dict[str, Any]],
    *,
    full_mask_name: str,
) -> list[dict[str, object]]:
    """Measure mask-selection headroom without also selecting warm strength."""

    result = []
    regimes = sorted(
        {
            (
                float(row["warm_start_multiplier_by_payoff_span"]),
                int(row["full_tree_equivalent_iteration_budget"]),
            )
            for row in records
        }
    )
    for warm_multiplier, budget in regimes:
        regime_rows = [
            row
            for row in records
            if float(row["warm_start_multiplier_by_payoff_span"])
            == warm_multiplier
            and int(row["full_tree_equivalent_iteration_budget"]) == budget
        ]
        instances: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in regime_rows:
            instances[(str(row["context_id"]), str(row["target_name"]))].append(row)

        mask_oracle_total = 0.0
        mask_oracle_with_no_op_total = 0.0
        full_mask_total = 0.0
        full_mask_with_no_op_total = 0.0
        oracle_no_ops = 0
        full_mask_no_ops = 0
        winning_masks: dict[str, int] = defaultdict(int)
        for rows in instances.values():
            best = max(
                rows,
                key=lambda row: float(row["nash_conv_reduction_from_blueprint"]),
            )
            best_reduction = float(best["nash_conv_reduction_from_blueprint"])
            winning_masks[str(best["mask_name"])] += 1
            mask_oracle_total += best_reduction
            if best_reduction > 0.0:
                mask_oracle_with_no_op_total += best_reduction
            else:
                oracle_no_ops += 1

            full_rows = [row for row in rows if row["mask_name"] == full_mask_name]
            if len(full_rows) != 1:
                raise AssertionError("fixed-warm oracle requires one full-mask row per instance")
            full_reduction = float(
                full_rows[0]["nash_conv_reduction_from_blueprint"]
            )
            full_mask_total += full_reduction
            if full_reduction > 0.0:
                full_mask_with_no_op_total += full_reduction
            else:
                full_mask_no_ops += 1

        result.append(
            {
                "warm_start_multiplier_by_payoff_span": warm_multiplier,
                "full_tree_equivalent_iteration_budget": budget,
                "instances": len(instances),
                "mask_oracle_total_reduction": mask_oracle_total,
                "full_mask_total_reduction": full_mask_total,
                "mask_oracle_minus_full_mask_reduction": (
                    mask_oracle_total - full_mask_total
                ),
                "mask_oracle_with_no_op_total_reduction": (
                    mask_oracle_with_no_op_total
                ),
                "full_mask_with_no_op_total_reduction": (
                    full_mask_with_no_op_total
                ),
                "mask_oracle_with_no_op_uplift": (
                    mask_oracle_with_no_op_total - full_mask_with_no_op_total
                ),
                "mask_oracle_no_op_instances": oracle_no_ops,
                "full_mask_no_op_instances": full_mask_no_ops,
                "winning_mask_counts": dict(sorted(winning_masks.items())),
                "selection_authorized": False,
            }
        )
    return result


def _primary_opportunity_summary(
    records: list[dict[str, Any]],
    *,
    warm_multiplier: float,
    budget: int,
    full_mask_name: str,
) -> dict[str, object]:
    selected = [
        row
        for row in records
        if float(row["warm_start_multiplier_by_payoff_span"]) == warm_multiplier
        and int(row["full_tree_equivalent_iteration_budget"]) == budget
    ]
    instances: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in selected:
        instances[(str(row["context_id"]), str(row["target_name"]))].append(row)

    group_values: dict[str, dict[str, float | int]] = {}
    winning_masks: dict[str, int] = defaultdict(int)
    for rows in instances.values():
        group_id = str(rows[0]["group_id"])
        group = group_values.setdefault(
            group_id,
            {
                "instances": 0,
                "mask_oracle_with_no_op_reduction": 0.0,
                "full_mask_with_no_op_reduction": 0.0,
            },
        )
        group["instances"] = int(group["instances"]) + 1
        best = max(
            rows,
            key=lambda row: float(row["nash_conv_reduction_from_blueprint"]),
        )
        best_reduction = float(best["nash_conv_reduction_from_blueprint"])
        winning_masks[str(best["mask_name"])] += 1
        group["mask_oracle_with_no_op_reduction"] = float(
            group["mask_oracle_with_no_op_reduction"]
        ) + max(0.0, best_reduction)

        full = [row for row in rows if row["mask_name"] == full_mask_name]
        if len(full) != 1:
            raise AssertionError("primary opportunity requires one full-mask row")
        full_reduction = float(full[0]["nash_conv_reduction_from_blueprint"])
        group["full_mask_with_no_op_reduction"] = float(
            group["full_mask_with_no_op_reduction"]
        ) + max(0.0, full_reduction)

    group_records = []
    for group_id, values in sorted(group_values.items()):
        mask_value = float(values["mask_oracle_with_no_op_reduction"])
        full_value = float(values["full_mask_with_no_op_reduction"])
        uplift = mask_value - full_value
        group_records.append(
            {
                "group_id": group_id,
                "instances": int(values["instances"]),
                "mask_oracle_with_no_op_reduction": mask_value,
                "full_mask_with_no_op_reduction": full_value,
                "opportunity_uplift": uplift,
                "positive_opportunity": uplift > 1e-12,
            }
        )

    mask_total = sum(
        float(row["mask_oracle_with_no_op_reduction"])
        for row in group_records
    )
    full_total = sum(
        float(row["full_mask_with_no_op_reduction"])
        for row in group_records
    )
    uplift = mask_total - full_total
    return {
        "warm_start_multiplier_by_payoff_span": warm_multiplier,
        "full_tree_equivalent_iteration_budget": budget,
        "instances": len(instances),
        "groups": len(group_records),
        "mask_oracle_with_no_op_total_reduction": mask_total,
        "full_mask_with_no_op_total_reduction": full_total,
        "opportunity_uplift": uplift,
        "relative_opportunity_uplift": uplift / full_total if full_total > 0.0 else None,
        "positive_group_fraction": mean(
            bool(row["positive_opportunity"]) for row in group_records
        ),
        "winning_mask_counts": dict(sorted(winning_masks.items())),
        "group_records": group_records,
        "selection_authorized": False,
    }


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
        blueprint, source_evaluation, blueprint_metrics = _build_blueprint(
            source,
            parsed,
        )
        if set(blueprint) != set(source_schema):
            raise AssertionError("full blueprint did not materialize the full source schema")
        blueprint_records.append(
            {
                "context_id": context.context_id,
                "group_id": context.group_id,
                "family": context.family,
                "deals": len(source.deals),
                "information_sets": len(source_schema),
                "tree_states_per_traversal": source_tree_states,
                "state_visits": (
                    int(blueprint_metrics["iterations"])
                    * source.num_players
                    * source_tree_states
                ),
                **blueprint_metrics,
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
            range_delta = RiverRangeDelta.between(context.game, range_target)
            boundary_feature_start = time.perf_counter()
            boundary_features = (
                _boundary_online_features(
                    context,
                    range_target,
                    target,
                    blueprint,
                    range_delta,
                )
                if parsed["evidence_stage"] == "group_separated_development"
                else {}
            )
            boundary_feature_seconds = time.perf_counter() - boundary_feature_start
            baseline_evaluation_start = time.perf_counter()
            baseline_evaluation = evaluate_profile(target, blueprint)
            baseline_evaluation_seconds = time.perf_counter() - baseline_evaluation_start
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
                    "boundary_online_features": boundary_features,
                    "boundary_feature_seconds": boundary_feature_seconds,
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
                leaf_values = PolicyContinuationValues(
                    target.num_players,
                    blueprint,
                    key=multi_size_state_cache_key,
                )
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
                    cumulative_probe_feature_seconds = 0.0

                    for budget in parsed["full_tree_equivalent_iteration_budgets"]:
                        checkpoint = budget_checkpoints[budget]
                        solve_start = time.perf_counter()
                        solver.run(checkpoint - completed_iterations)
                        cumulative_solve_seconds += time.perf_counter() - solve_start
                        completed_iterations = checkpoint
                        candidate = solver.average_strategy()
                        probe_feature_start = time.perf_counter()
                        probe_features = (
                            _solver_probe_features(
                                solver,
                                blueprint,
                                candidate,
                                selective_schema,
                                target.payoff_span,
                            )
                            if parsed["record_solver_probe_features"]
                            else {}
                        )
                        probe_feature_seconds = (
                            time.perf_counter() - probe_feature_start
                        )
                        cumulative_probe_feature_seconds += probe_feature_seconds
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
                                "solver_probe_features": probe_features,
                                "solver_probe_feature_seconds": probe_feature_seconds,
                                "cumulative_solver_probe_feature_seconds": (
                                    cumulative_probe_feature_seconds
                                ),
                                "hot_with_probe_feature_seconds": (
                                    hot_seconds + cumulative_probe_feature_seconds
                                ),
                                "cold_exact_leaf_online_seconds": cold_seconds,
                                "cold_exact_leaf_with_probe_feature_seconds": (
                                    cold_seconds + cumulative_probe_feature_seconds
                                ),
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
    fixed_warm_mask_oracle = _fixed_warm_mask_oracle(
        records,
        full_mask_name=str(parsed["masks"][-1]["name"]),
    )
    current_selective_sha = _source_file_sha256("selective_tree.py")
    current_river_selective_sha = _source_file_sha256("river_selective.py")
    primary_opportunity = None
    if parsed["evidence_stage"] == "group_separated_development":
        primary_opportunity = _primary_opportunity_summary(
            records,
            warm_multiplier=float(
                parsed["warm_start_multipliers_by_payoff_span"][0]
            ),
            budget=int(
                parsed["gates"]["primary_full_tree_equivalent_iteration_budget"]
            ),
            full_mask_name=str(parsed["masks"][-1]["name"]),
        )
    config_payload = json.dumps(config, sort_keys=True, separators=(",", ":"))
    gates = {
        "development_contexts_only": all(context.split == "development" for context in contexts),
        "source_target_information_schema_identity": all_schema_identity,
        "nested_mask_tree_counts_strictly_increase": all_mask_counts_strictly_increase,
        "full_mask_has_no_cutoffs": all_full_masks_have_no_cutoffs,
        "full_mask_state_count_matches_full_game": all_full_mask_state_counts_match,
    }
    if parsed["evidence_stage"] == "group_separated_development":
        assert primary_opportunity is not None
        relative_uplift = primary_opportunity["relative_opportunity_uplift"]
        gates.update(
            {
                "minimum_development_board_groups": (
                    len({context.group_id for context in contexts})
                    >= int(parsed["gates"]["minimum_development_board_groups"])
                ),
                "source_blueprint_quality": all(
                    bool(row["quality_threshold_passed"])
                    and float(row["source_normalized_nash_conv"])
                    <= float(
                        parsed["gates"]["maximum_source_normalized_nash_conv"]
                    )
                    for row in blueprint_records
                ),
                "selective_tree_source_is_frozen": (
                    current_selective_sha
                    == parsed["expected_selective_tree_sha256"]
                ),
                "river_selective_source_is_frozen": (
                    current_river_selective_sha
                    == parsed["expected_river_selective_sha256"]
                ),
                "boundary_features_are_present": all(
                    bool(row["boundary_online_features"])
                    for row in target_records
                ),
                "solver_probe_features_are_present": all(
                    bool(row["solver_probe_features"])
                    for row in records
                ),
                "mask_no_op_oracle_relative_uplift": (
                    relative_uplift is not None
                    and float(relative_uplift)
                    >= float(
                        parsed["gates"][
                            "minimum_mask_no_op_oracle_relative_uplift"
                        ]
                    )
                ),
                "positive_group_uplift_fraction": (
                    float(primary_opportunity["positive_group_fraction"])
                    >= float(
                        parsed["gates"]["minimum_positive_group_uplift_fraction"]
                    )
                ),
            }
        )
    is_pilot = parsed["evidence_stage"] == "pilot"
    return {
        "experiment_type": (
            "river_selective_expansion_pilot"
            if is_pilot
            else "river_selective_expansion_development_matrix"
        ),
        "evidence_stage": parsed["evidence_stage"],
        "pilot": is_pilot,
        "selection_authorized": False,
        "native_latency_claim_authorized": False,
        "neural_leaf_claim_authorized": False,
        "config_sha256": hashlib.sha256(config_payload.encode("utf-8")).hexdigest(),
        "config": config,
        "environment": environment_metadata(),
        "frozen_source_hashes": {
            "selective_tree_sha256": current_selective_sha,
            "river_selective_sha256": current_river_selective_sha,
        },
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
            "maximum_source_blueprint_normalized_nash_conv": max(
                float(row["source_normalized_nash_conv"])
                for row in blueprint_records
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
                max(0.0, -float(row["nash_conv_reduction_from_blueprint"]))
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
        "fixed_warm_mask_oracle": fixed_warm_mask_oracle,
        "primary_opportunity": primary_opportunity,
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
