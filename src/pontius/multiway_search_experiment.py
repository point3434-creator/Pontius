"""Grouped exact full-search and acceptance experiment for multiway river."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .cfr import TabularCFR
from .coalition import (
    CoalitionEvaluationResult,
    assess_multiplayer_candidate,
    evaluate_coalition_threats,
)
from .dependency_tape import CompiledPolicyDeltaTape
from .evaluation import EvaluationResult, Policy, best_response, evaluate_profile
from .game import Action, CHANCE_PLAYER, TERMINAL_PLAYER, GameState
from .multiway_river_context import (
    MULTIWAY_CONTEXT_FAMILIES,
    MultiwayRangeTarget,
    MultiwayRiverContext,
    generate_multiway_river_contexts,
    make_multiway_range_targets,
    multiway_context_features,
    serialize_multiway_context,
)
from .reporting import environment_metadata
from .updates import UPDATE_RULES

_ROOT = Path(__file__).parents[2]
_SOURCE_PATHS = {
    "expected_context_generator_sha256": (
        _ROOT / "src" / "pontius" / "multiway_river_context.py"
    ),
    "expected_multiway_game_sha256": (
        _ROOT / "src" / "pontius" / "river_multiway.py"
    ),
    "expected_coalition_evaluator_sha256": (
        _ROOT / "src" / "pontius" / "coalition.py"
    ),
    "expected_dependency_tape_sha256": (
        _ROOT / "src" / "pontius" / "dependency_tape.py"
    ),
    "frozen_contract_sha256": (
        _ROOT / "experiments" / "configs" / "multiway-river-contract-v1.json"
    ),
    "calibration_artifact_sha256": (
        _ROOT / "experiments" / "results" / "multiway-river-cost-calibration-v1.json"
    ),
}
_ALLOWED_FIELDS = {
    "evidence_stage",
    "requested_groups",
    "seed",
    "num_players",
    "hands_per_player",
    "families",
    "included_splits",
    "pot_options",
    "bet_to_pot_options",
    "effective_stack_to_pot",
    "range_weight_options",
    "target_specs",
    "blueprint_solver",
    "blueprint_quality_checkpoints",
    "maximum_source_normalized_nash_conv",
    "candidate_solvers",
    "candidate_checkpoints",
    "warm_start_multiplier_by_payoff_span",
    "candidate_output",
    "primary_solver",
    "primary_checkpoint",
    "numerical_guard_by_payoff_span",
    "tape_execution_mode",
    "timing_repeats",
    *_SOURCE_PATHS,
    "gates",
}
_GATE_FIELDS = {
    "minimum_development_groups",
    "maximum_exact_evaluation_error",
    "maximum_best_response_action_mismatches",
    "require_all_unilateral_acceptance_invariants",
    "require_all_coalition_acceptance_invariants",
    "hot_tape_strictly_faster_than_ordinary_evaluation",
    "two_candidate_reuse_strictly_faster_than_two_ordinary_evaluations",
    "primary_aggregate_acceptance_strictly_beats_blind_raw_reduction",
    "primary_aggregate_acceptance_hot_rate_strictly_beats_blind",
    "minimum_primary_unilateral_accept_target_fraction",
    "minimum_primary_coalition_accept_target_fraction",
    "primary_coalition_acceptance_has_positive_normalized_reduction",
}
_TARGET_KINDS = {
    "seat_max_conditional_reweight",
    "three_way_strength_alignment",
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen source is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _positive_finite(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be positive and finite")
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be positive and finite") from error
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{label} must be positive and finite")
    return result


def _integer_tuple(value: object, label: str) -> tuple[int, ...]:
    try:
        result = tuple(value)  # type: ignore[arg-type]
    except TypeError as error:
        raise ValueError(f"{label} must be an increasing integer list") from error
    if (
        not result
        or any(isinstance(item, bool) or not isinstance(item, int) for item in result)
        or tuple(sorted(set(result))) != result
        or result[0] <= 0
    ):
        raise ValueError(f"{label} must be an increasing positive integer list")
    return result


def parse_multiway_search_config(config: dict[str, Any]) -> dict[str, Any]:
    unknown = set(config) - _ALLOWED_FIELDS
    missing = _ALLOWED_FIELDS - set(config)
    if unknown or missing:
        raise ValueError(
            f"multiway experiment fields differ: missing={sorted(missing)!r}, "
            f"unknown={sorted(unknown)!r}"
        )
    if config["evidence_stage"] != "group_separated_development_only":
        raise ValueError("experiment must remain group-separated development-only")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen hash mismatch for {field}")

    requested_groups = config["requested_groups"]
    seed = config["seed"]
    hands_per_player = config["hands_per_player"]
    if (
        isinstance(requested_groups, bool)
        or not isinstance(requested_groups, int)
        or requested_groups <= 0
    ):
        raise ValueError("requested groups must be a positive integer")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if config["num_players"] != 3:
        raise ValueError("the frozen primary workload requires three players")
    if (
        isinstance(hands_per_player, bool)
        or not isinstance(hands_per_player, int)
        or not 2 <= hands_per_player <= 7
    ):
        raise ValueError("hands per player must be in [2, 7]")

    families = tuple(config["families"])
    if not families or len(set(families)) != len(families):
        raise ValueError("families must be nonempty and unique")
    if set(families) - set(MULTIWAY_CONTEXT_FAMILIES):
        raise ValueError("unsupported multiway context family")
    included_splits = tuple(config["included_splits"])
    if included_splits != ("development",):
        raise ValueError("only development may be materialized")

    pot_options = tuple(_positive_finite(value, "pot option") for value in config["pot_options"])
    bet_options = tuple(
        _positive_finite(value, "bet-to-pot option")
        for value in config["bet_to_pot_options"]
    )
    stack_ratio = _positive_finite(
        config["effective_stack_to_pot"],
        "effective stack-to-pot",
    )
    if max(bet_options) > stack_ratio:
        raise ValueError("every configured bet must fit the effective stack")
    weight_options = tuple(
        _positive_finite(value, "range weight")
        for value in config["range_weight_options"]
    )

    target_specs = tuple(dict(spec) for spec in config["target_specs"])
    names = tuple(str(spec.get("name")) for spec in target_specs)
    if not target_specs or len(set(names)) != len(names):
        raise ValueError("target specifications must be nonempty and uniquely named")
    for spec in target_specs:
        if spec.get("kind") not in _TARGET_KINDS:
            raise ValueError("unsupported multiway target specification")

    blueprint_solver = str(config["blueprint_solver"])
    candidate_solvers = tuple(str(value) for value in config["candidate_solvers"])
    if blueprint_solver not in UPDATE_RULES:
        raise ValueError("unsupported blueprint solver")
    if (
        not candidate_solvers
        or len(set(candidate_solvers)) != len(candidate_solvers)
        or any(solver not in UPDATE_RULES for solver in candidate_solvers)
    ):
        raise ValueError("candidate solvers must be unique supported variants")
    blueprint_checkpoints = _integer_tuple(
        config["blueprint_quality_checkpoints"],
        "blueprint checkpoints",
    )
    candidate_checkpoints = _integer_tuple(
        config["candidate_checkpoints"],
        "candidate checkpoints",
    )
    primary_solver = str(config["primary_solver"])
    primary_checkpoint = config["primary_checkpoint"]
    if primary_solver not in candidate_solvers or primary_checkpoint not in candidate_checkpoints:
        raise ValueError("primary solver/checkpoint must be a candidate arm")
    if config["candidate_output"] != "average_strategy":
        raise ValueError("candidate output must remain average strategy")
    if config["tape_execution_mode"] != "dense":
        raise ValueError("the frozen tape execution mode is dense")
    if config["timing_repeats"] != 1:
        raise ValueError("stateful experiment requires exactly one timing repeat")

    maximum_source = _positive_finite(
        config["maximum_source_normalized_nash_conv"],
        "maximum source normalized NashConv",
    )
    warm_multiplier = _positive_finite(
        config["warm_start_multiplier_by_payoff_span"],
        "warm-start multiplier",
    )
    guard_fraction = _positive_finite(
        config["numerical_guard_by_payoff_span"],
        "numerical guard fraction",
    )
    if guard_fraction > 1e-10:
        raise ValueError("numerical guard exceeds the validated envelope")

    gates = dict(config["gates"])
    if set(gates) != _GATE_FIELDS:
        raise ValueError("multiway gate fields differ from the frozen contract")
    if (
        isinstance(gates["minimum_development_groups"], bool)
        or not isinstance(gates["minimum_development_groups"], int)
        or gates["minimum_development_groups"] <= 0
    ):
        raise ValueError("minimum development groups must be a positive integer")
    gates["maximum_exact_evaluation_error"] = _positive_finite(
        gates["maximum_exact_evaluation_error"],
        "maximum exact evaluation error",
    )
    mismatch_limit = gates["maximum_best_response_action_mismatches"]
    if (
        isinstance(mismatch_limit, bool)
        or not isinstance(mismatch_limit, int)
        or mismatch_limit < 0
    ):
        raise ValueError("action mismatch limit must be a nonnegative integer")
    boolean_gates = _GATE_FIELDS - {
        "minimum_development_groups",
        "maximum_exact_evaluation_error",
        "maximum_best_response_action_mismatches",
        "minimum_primary_unilateral_accept_target_fraction",
        "minimum_primary_coalition_accept_target_fraction",
    }
    if any(not isinstance(gates[field], bool) for field in boolean_gates):
        raise ValueError("boolean gate requirements must be booleans")
    for field in (
        "minimum_primary_unilateral_accept_target_fraction",
        "minimum_primary_coalition_accept_target_fraction",
    ):
        value = float(gates[field])
        if not 0.0 <= value <= 1.0:
            raise ValueError("minimum acceptance fractions must be in [0, 1]")
        gates[field] = value

    return {
        **config,
        "families": families,
        "included_splits": included_splits,
        "pot_options": pot_options,
        "bet_to_pot_options": bet_options,
        "effective_stack_to_pot": stack_ratio,
        "range_weight_options": weight_options,
        "target_specs": target_specs,
        "blueprint_solver": blueprint_solver,
        "blueprint_quality_checkpoints": blueprint_checkpoints,
        "maximum_source_normalized_nash_conv": maximum_source,
        "candidate_solvers": candidate_solvers,
        "candidate_checkpoints": candidate_checkpoints,
        "warm_start_multiplier_by_payoff_span": warm_multiplier,
        "primary_solver": primary_solver,
        "primary_checkpoint": int(primary_checkpoint),
        "numerical_guard_by_payoff_span": guard_fraction,
        "gates": gates,
    }


def _timed(operation: Any) -> tuple[Any, float]:
    start = time.perf_counter()
    result = operation()
    return result, (time.perf_counter() - start) * 1000.0


def _tree_states(state: GameState) -> int:
    player = state.current_player
    if player == TERMINAL_PLAYER:
        return 1
    if player == CHANCE_PLAYER:
        return 1 + sum(
            _tree_states(state.apply_action(action))
            for action, _ in state.chance_outcomes()
        )
    return 1 + sum(
        _tree_states(state.apply_action(action)) for action in state.legal_actions()
    )


def _evaluation_error(first: EvaluationResult, second: EvaluationResult) -> float:
    first_values = (
        *first.utilities,
        *first.best_response_values,
        *first.deviation_gains,
        first.nash_conv,
    )
    second_values = (
        *second.utilities,
        *second.best_response_values,
        *second.deviation_gains,
        second.nash_conv,
    )
    return max(
        abs(left - right)
        for left, right in zip(first_values, second_values, strict=True)
    )


def _action_mismatches(
    candidate: tuple[dict[str, Action], ...],
    reference: tuple[dict[str, Action], ...],
) -> int:
    return sum(
        candidate[player].get(key) != action
        for player, actions in enumerate(reference)
        for key, action in actions.items()
    )


def _coalition_payload(result: CoalitionEvaluationResult) -> list[dict[str, object]]:
    return [
        {
            "coalition": list(threat.coalition),
            "baseline_value": threat.baseline_value,
            "best_response_value": threat.best_response_value,
            "deviation_gain": threat.deviation_gain,
        }
        for threat in result.threats
    ]


def _policy_features(
    solver: TabularCFR,
    policy: Policy,
    baseline: Policy,
) -> dict[str, float | int]:
    positive = 0.0
    negative = 0.0
    positive_squared = 0.0
    maximum_positive = 0.0
    entries = 0
    for data in solver.information_sets.values():
        for regret in data.regrets.values():
            entries += 1
            if regret > 0.0:
                positive += regret
                positive_squared += regret * regret
                maximum_positive = max(maximum_positive, regret)
            elif regret < 0.0:
                negative -= regret

    total_variations = []
    entropies = []
    for key, distribution in policy.items():
        baseline_distribution = baseline[key]
        total_variations.append(
            0.5
            * sum(
                abs(probability - baseline_distribution[action])
                for action, probability in distribution.items()
            )
        )
        entropies.append(
            -sum(
                probability * math.log(probability)
                for probability in distribution.values()
                if probability > 0.0
            )
        )
    return {
        "materialized_information_sets": len(solver.information_sets),
        "regret_entries": entries,
        "positive_regret_mass": positive,
        "negative_regret_mass": negative,
        "maximum_positive_regret": maximum_positive,
        "positive_regret_concentration": (
            positive_squared / (positive * positive) if positive > 0.0 else 0.0
        ),
        "mean_policy_total_variation_from_blueprint": (
            sum(total_variations) / len(total_variations)
        ),
        "maximum_policy_total_variation_from_blueprint": max(total_variations),
        "mean_policy_entropy": sum(entropies) / len(entropies),
    }


def _solve_source_blueprint(
    context: MultiwayRiverContext,
    parsed: dict[str, Any],
) -> tuple[Policy, dict[str, object]]:
    game = context.game
    solver = TabularCFR(game, variant=parsed["blueprint_solver"])
    cumulative_ms = 0.0
    previous = 0
    trajectory = []
    selected_policy: Policy = {}
    selected_evaluation: EvaluationResult | None = None
    selected_checkpoint = parsed["blueprint_quality_checkpoints"][-1]
    for checkpoint in parsed["blueprint_quality_checkpoints"]:
        _, run_ms = _timed(lambda: solver.run(checkpoint - previous))
        cumulative_ms += run_ms
        previous = checkpoint
        selected_policy, output_ms = _timed(solver.average_strategy)
        selected_evaluation, evaluation_ms = _timed(
            lambda: evaluate_profile(game, selected_policy)
        )
        normalized = selected_evaluation.nash_conv / game.payoff_span
        trajectory.append(
            {
                "checkpoint": checkpoint,
                "normalized_nash_conv": normalized,
                "raw_nash_conv": selected_evaluation.nash_conv,
                "cumulative_solver_ms": cumulative_ms + output_ms,
                "exact_evaluation_ms": evaluation_ms,
            }
        )
        selected_checkpoint = checkpoint
        if normalized <= parsed["maximum_source_normalized_nash_conv"]:
            break
    assert selected_evaluation is not None
    return selected_policy, {
        "context_id": context.context_id,
        "group_id": context.group_id,
        "family": context.family,
        "selected_checkpoint": selected_checkpoint,
        "selected_nash_conv": selected_evaluation.nash_conv,
        "selected_normalized_nash_conv": (
            selected_evaluation.nash_conv / game.payoff_span
        ),
        "quality_gate_passes": (
            selected_evaluation.nash_conv / game.payoff_span
            <= parsed["maximum_source_normalized_nash_conv"]
        ),
        "tree_states": _tree_states(game.initial_state()),
        "trajectory": trajectory,
    }


def _candidate_record(
    *,
    context: MultiwayRiverContext,
    target: MultiwayRangeTarget,
    solver_name: str,
    checkpoint: int,
    solver: TabularCFR,
    policy: Policy,
    baseline_policy: Policy,
    baseline_evaluation: EvaluationResult,
    baseline_coalitions: CoalitionEvaluationResult,
    baseline_ordinary_ms: float,
    baseline_coalition_ms: float,
    tape: CompiledPolicyDeltaTape,
    tape_compile_ms: float,
    cumulative_solver_ms: float,
    output_policy_ms: float,
    tree_states: int,
    parsed: dict[str, Any],
) -> tuple[dict[str, object], float, int]:
    game = target.game
    candidate_evaluation, ordinary_ms = _timed(lambda: evaluate_profile(game, policy))
    hot_evaluation, hot_ms = _timed(
        lambda: tape.evaluate_policy(policy, mode=parsed["tape_execution_mode"])
    )
    detailed = tape.recertify_policy(policy, mode=parsed["tape_execution_mode"])
    reference_actions = tuple(
        best_response(game, policy, player)[1] for player in range(game.num_players)
    )
    exact_error = max(
        _evaluation_error(candidate_evaluation, hot_evaluation),
        _evaluation_error(candidate_evaluation, detailed.evaluation),
    )
    action_mismatches = _action_mismatches(
        detailed.best_response_actions,
        reference_actions,
    )
    candidate_coalitions, coalition_ms = _timed(
        lambda: evaluate_coalition_threats(game, policy)
    )
    assessment = assess_multiplayer_candidate(
        baseline_evaluation,
        candidate_evaluation,
        baseline_coalitions,
        candidate_coalitions,
        payoff_span=game.payoff_span,
        numerical_guard_fraction=parsed["numerical_guard_by_payoff_span"],
    )
    guard = assessment.numerical_guard
    raw_reduction = baseline_evaluation.nash_conv - candidate_evaluation.nash_conv
    aggregate_accept = raw_reduction > guard
    if aggregate_accept != assessment.aggregate_nash_conv_strictly_decreases:
        raise AssertionError("aggregate acceptance definitions diverged")

    source_coalitions = baseline_coalitions.by_coalition()
    candidate_coalition_map = candidate_coalitions.by_coalition()
    player_gain_changes = tuple(
        candidate - source
        for source, candidate in zip(
            baseline_evaluation.deviation_gains,
            candidate_evaluation.deviation_gains,
            strict=True,
        )
    )
    coalition_gain_changes = {
        coalition: candidate_coalition_map[coalition].deviation_gain
        - source.deviation_gain
        for coalition, source in source_coalitions.items()
    }

    solve_ms = cumulative_solver_ms + output_policy_ms
    total_candidates_per_target = (
        len(parsed["candidate_solvers"]) * len(parsed["candidate_checkpoints"])
    )
    arm_reductions = {
        "blind": raw_reduction,
        "aggregate_exact": raw_reduction if aggregate_accept else 0.0,
        "unilateral_pareto": (
            raw_reduction if assessment.unilateral_pareto_accept else 0.0
        ),
        "coalition_stress": (
            raw_reduction if assessment.coalition_stress_accept else 0.0
        ),
    }
    charged_ms = {
        "blind": solve_ms,
        "ordinary_exact_one_shot": (
            solve_ms + baseline_ordinary_ms + ordinary_ms
        ),
        "ordinary_exact_cached_baseline": solve_ms + ordinary_ms,
        "tape_exact_one_shot": solve_ms + tape_compile_ms + hot_ms,
        "tape_exact_precompiled": solve_ms + hot_ms,
        "tape_exact_trajectory_amortized": (
            solve_ms + hot_ms + tape_compile_ms / total_candidates_per_target
        ),
        "coalition_stress_one_shot": (
            solve_ms
            + tape_compile_ms
            + hot_ms
            + baseline_coalition_ms
            + coalition_ms
        ),
        "coalition_stress_cached_baseline": solve_ms + hot_ms + coalition_ms,
    }
    return (
        {
            "context_id": context.context_id,
            "group_id": context.group_id,
            "family": context.family,
            "target_id": target.target_id,
            "target_name": target.name,
            "target_kind": target.kind,
            "solver": solver_name,
            "checkpoint": checkpoint,
            "payoff_span": game.payoff_span,
            "baseline_nash_conv": baseline_evaluation.nash_conv,
            "candidate_nash_conv": candidate_evaluation.nash_conv,
            "raw_nash_conv_reduction": raw_reduction,
            "normalized_nash_conv_reduction": raw_reduction / game.payoff_span,
            "baseline_deviation_gains": list(baseline_evaluation.deviation_gains),
            "candidate_deviation_gains": list(candidate_evaluation.deviation_gains),
            "player_deviation_gain_changes": list(player_gain_changes),
            "maximum_player_deviation_gain_increase": max(player_gain_changes),
            "baseline_coalitions": _coalition_payload(baseline_coalitions),
            "candidate_coalitions": _coalition_payload(candidate_coalitions),
            "coalition_deviation_gain_changes": [
                {
                    "coalition": list(coalition),
                    "change": change,
                }
                for coalition, change in sorted(coalition_gain_changes.items())
            ],
            "maximum_coalition_deviation_gain_increase": max(
                coalition_gain_changes.values()
            ),
            "acceptance": {
                "aggregate_exact": aggregate_accept,
                "unilateral_pareto": assessment.unilateral_pareto_accept,
                "coalition_stress": assessment.coalition_stress_accept,
                "aggregate_nash_conv_strictly_decreases": (
                    assessment.aggregate_nash_conv_strictly_decreases
                ),
                "no_player_deviation_gain_increases": (
                    assessment.no_player_deviation_gain_increases
                ),
                "no_coalition_deviation_gain_increases": (
                    assessment.no_coalition_deviation_gain_increases
                ),
                "numerical_guard": guard,
            },
            "arm_raw_reductions": arm_reductions,
            "arm_normalized_reductions": {
                arm: reduction / game.payoff_span
                for arm, reduction in arm_reductions.items()
            },
            "timing_ms": {
                "warm_start_and_cumulative_steps": cumulative_solver_ms,
                "output_policy": output_policy_ms,
                "ordinary_candidate_evaluation": ordinary_ms,
                "hot_tape_candidate_evaluation": hot_ms,
                "candidate_coalition_evaluation": coalition_ms,
                "tape_compile": tape_compile_ms,
                "ordinary_baseline_evaluation": baseline_ordinary_ms,
                "baseline_coalition_evaluation": baseline_coalition_ms,
                "charged": charged_ms,
            },
            "state_work": {
                "tree_states": tree_states,
                "solver_state_visits": checkpoint * game.num_players * tree_states,
            },
            "causal_solver_features": _policy_features(
                solver,
                policy,
                baseline_policy,
            ),
            "exact_evaluation_error": exact_error,
            "best_response_action_mismatches": action_mismatches,
        },
        exact_error,
        action_mismatches,
    )


def _evaluate_target(
    context: MultiwayRiverContext,
    target: MultiwayRangeTarget,
    baseline_policy: Policy,
    parsed: dict[str, Any],
) -> tuple[dict[str, object], list[dict[str, object]], float, int, float]:
    game = target.game
    baseline_evaluation, baseline_ordinary_ms = _timed(
        lambda: evaluate_profile(game, baseline_policy)
    )
    tape, tape_compile_ms = _timed(
        lambda: CompiledPolicyDeltaTape(game, baseline_policy)
    )
    tape_baseline = tape.source_result.evaluation
    replay = tape.recertify_policy(
        tape.source_policy,
        mode=parsed["tape_execution_mode"],
    )
    baseline_reference_actions = tuple(
        best_response(game, baseline_policy, player)[1]
        for player in range(game.num_players)
    )
    baseline_error = max(
        _evaluation_error(baseline_evaluation, tape_baseline),
        _evaluation_error(baseline_evaluation, replay.evaluation),
    )
    baseline_action_mismatches = max(
        _action_mismatches(
            tape.source_result.best_response_actions,
            baseline_reference_actions,
        ),
        _action_mismatches(replay.best_response_actions, baseline_reference_actions),
    )
    baseline_coalitions, baseline_coalition_ms = _timed(
        lambda: evaluate_coalition_threats(game, baseline_policy)
    )
    topology = tape.topology_summary()
    tree_states = int(topology["compiled_tree_states"])
    rows = []
    maximum_error = baseline_error
    action_mismatches = baseline_action_mismatches

    for solver_name in parsed["candidate_solvers"]:
        solver = TabularCFR(game, variant=solver_name)
        _, warm_start_ms = _timed(
            lambda: solver.warm_start_from_schema(
                baseline_policy,
                parsed["warm_start_multiplier_by_payoff_span"] * game.payoff_span,
                tape.policy_input_schema,
            )
        )
        cumulative_solver_ms = warm_start_ms
        previous = 0
        for checkpoint in parsed["candidate_checkpoints"]:
            _, run_ms = _timed(lambda: solver.run(checkpoint - previous))
            cumulative_solver_ms += run_ms
            previous = checkpoint
            policy, output_ms = _timed(solver.average_strategy)
            row, error, mismatches = _candidate_record(
                context=context,
                target=target,
                solver_name=solver_name,
                checkpoint=checkpoint,
                solver=solver,
                policy=policy,
                baseline_policy=tape.source_policy,
                baseline_evaluation=baseline_evaluation,
                baseline_coalitions=baseline_coalitions,
                baseline_ordinary_ms=baseline_ordinary_ms,
                baseline_coalition_ms=baseline_coalition_ms,
                tape=tape,
                tape_compile_ms=tape_compile_ms,
                cumulative_solver_ms=cumulative_solver_ms,
                output_policy_ms=output_ms,
                tree_states=tree_states,
                parsed=parsed,
            )
            rows.append(row)
            maximum_error = max(maximum_error, error)
            action_mismatches += mismatches

    return (
        {
            "context_id": context.context_id,
            "group_id": context.group_id,
            "family": context.family,
            "target_id": target.target_id,
            "target_name": target.name,
            "target_kind": target.kind,
            "source_provenance_digest": context.game.provenance_digest,
            "target_provenance_digest": game.provenance_digest,
            "structural_digest": game.structural_digest,
            "boundary_features": target.boundary_features,
            "baseline_evaluation": {
                "utilities": list(baseline_evaluation.utilities),
                "best_response_values": list(baseline_evaluation.best_response_values),
                "deviation_gains": list(baseline_evaluation.deviation_gains),
                "nash_conv": baseline_evaluation.nash_conv,
                "normalized_nash_conv": baseline_evaluation.nash_conv / game.payoff_span,
                "exploitability": baseline_evaluation.exploitability,
            },
            "baseline_coalitions": _coalition_payload(baseline_coalitions),
            "timing_ms": {
                "ordinary_baseline_evaluation": baseline_ordinary_ms,
                "tape_compile": tape_compile_ms,
                "baseline_coalition_evaluation": baseline_coalition_ms,
            },
            "topology": topology,
            "baseline_exact_evaluation_error": baseline_error,
            "baseline_best_response_action_mismatches": (
                baseline_action_mismatches
            ),
            "source_relative_replay_exact": (
                _evaluation_error(tape_baseline, replay.evaluation) == 0.0
                and replay.best_response_actions
                == tape.source_result.best_response_actions
            ),
        },
        rows,
        maximum_error,
        action_mismatches,
        tape_compile_ms,
    )


def _summaries(records: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, int], list[dict[str, object]]] = defaultdict(list)
    for row in records:
        grouped[(str(row["solver"]), int(row["checkpoint"]))].append(row)
    result = []
    for (solver, checkpoint), rows in sorted(grouped.items()):
        arm_raw = {
            arm: sum(float(row["arm_raw_reductions"][arm]) for row in rows)  # type: ignore[index]
            for arm in ("blind", "aggregate_exact", "unilateral_pareto", "coalition_stress")
        }
        arm_normalized = {
            arm: sum(
                float(row["arm_normalized_reductions"][arm])  # type: ignore[index]
                for row in rows
            )
            for arm in arm_raw
        }
        timing_fields = (
            "blind",
            "ordinary_exact_one_shot",
            "ordinary_exact_cached_baseline",
            "tape_exact_one_shot",
            "tape_exact_precompiled",
            "tape_exact_trajectory_amortized",
            "coalition_stress_one_shot",
            "coalition_stress_cached_baseline",
        )
        charged = {
            field: sum(
                float(row["timing_ms"]["charged"][field])  # type: ignore[index]
                for row in rows
            )
            for field in timing_fields
        }
        acceptance = {
            arm: sum(
                bool(row["acceptance"][arm])  # type: ignore[index]
                for row in rows
            )
            for arm in ("aggregate_exact", "unilateral_pareto", "coalition_stress")
        }
        result.append(
            {
                "solver": solver,
                "checkpoint": checkpoint,
                "targets": len(rows),
                "arm_raw_reduction": arm_raw,
                "arm_normalized_reduction": arm_normalized,
                "acceptance_counts": acceptance,
                "acceptance_fractions": {
                    arm: count / len(rows) for arm, count in acceptance.items()
                },
                "blind_harm_count": sum(
                    float(row["raw_nash_conv_reduction"]) < 0.0 for row in rows
                ),
                "maximum_blind_harm": max(
                    max(0.0, -float(row["raw_nash_conv_reduction"]))
                    for row in rows
                ),
                "charged_milliseconds": charged,
                "raw_reduction_per_millisecond": {
                    "blind": arm_raw["blind"] / charged["blind"],
                    "aggregate_ordinary_one_shot": (
                        arm_raw["aggregate_exact"]
                        / charged["ordinary_exact_one_shot"]
                    ),
                    "aggregate_tape_one_shot": (
                        arm_raw["aggregate_exact"] / charged["tape_exact_one_shot"]
                    ),
                    "aggregate_tape_precompiled": (
                        arm_raw["aggregate_exact"] / charged["tape_exact_precompiled"]
                    ),
                    "aggregate_tape_amortized": (
                        arm_raw["aggregate_exact"]
                        / charged["tape_exact_trajectory_amortized"]
                    ),
                    "coalition_one_shot": (
                        arm_raw["coalition_stress"]
                        / charged["coalition_stress_one_shot"]
                    ),
                },
            }
        )
    return result


def _serialized_config(parsed: dict[str, Any]) -> dict[str, Any]:
    return {
        **parsed,
        "families": list(parsed["families"]),
        "included_splits": list(parsed["included_splits"]),
        "pot_options": list(parsed["pot_options"]),
        "bet_to_pot_options": list(parsed["bet_to_pot_options"]),
        "range_weight_options": list(parsed["range_weight_options"]),
        "target_specs": list(parsed["target_specs"]),
        "blueprint_quality_checkpoints": list(
            parsed["blueprint_quality_checkpoints"]
        ),
        "candidate_solvers": list(parsed["candidate_solvers"]),
        "candidate_checkpoints": list(parsed["candidate_checkpoints"]),
    }


def run_multiway_search_experiment(config: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_multiway_search_config(config)
    experiment_start = time.perf_counter()
    contexts = generate_multiway_river_contexts(
        groups=parsed["requested_groups"],
        seed=parsed["seed"],
        hands_per_player=parsed["hands_per_player"],
        families=parsed["families"],
        splits=parsed["included_splits"],
        pot_options=parsed["pot_options"],
        bet_to_pot_options=parsed["bet_to_pot_options"],
        effective_stack_to_pot=parsed["effective_stack_to_pot"],
        weight_options=parsed["range_weight_options"],
    )

    source_records = []
    target_records = []
    candidate_records = []
    serialized_contexts = []
    maximum_error = 0.0
    action_mismatches = 0
    compile_by_target: dict[str, float] = {}
    for context in contexts:
        serialized_contexts.append(serialize_multiway_context(context))
        blueprint, source_record = _solve_source_blueprint(context, parsed)
        source_record["boundary_features"] = multiway_context_features(context)
        source_records.append(source_record)
        for target in make_multiway_range_targets(context, parsed["target_specs"]):
            target_record, rows, error, mismatches, compile_ms = _evaluate_target(
                context,
                target,
                blueprint,
                parsed,
            )
            target_records.append(target_record)
            candidate_records.extend(rows)
            maximum_error = max(maximum_error, error)
            action_mismatches += mismatches
            compile_by_target[target.target_id] = compile_ms

    summaries = _summaries(candidate_records)
    primary = next(
        row
        for row in summaries
        if row["solver"] == parsed["primary_solver"]
        and row["checkpoint"] == parsed["primary_checkpoint"]
    )
    primary_rows = [
        row
        for row in candidate_records
        if row["solver"] == parsed["primary_solver"]
        and row["checkpoint"] == parsed["primary_checkpoint"]
    ]

    total_hot_ms = sum(
        float(row["timing_ms"]["hot_tape_candidate_evaluation"])  # type: ignore[index]
        for row in candidate_records
    )
    total_ordinary_candidate_ms = sum(
        float(row["timing_ms"]["ordinary_candidate_evaluation"])  # type: ignore[index]
        for row in candidate_records
    )
    two_hot_ms = 0.0
    two_ordinary_ms = 0.0
    first_two = parsed["candidate_checkpoints"][:2]
    for target_id, compile_ms in compile_by_target.items():
        selected = [
            row
            for row in candidate_records
            if row["target_id"] == target_id
            and row["solver"] == parsed["primary_solver"]
            and row["checkpoint"] in first_two
        ]
        two_hot_ms += compile_ms + sum(
            float(row["timing_ms"]["hot_tape_candidate_evaluation"])  # type: ignore[index]
            for row in selected
        )
        two_ordinary_ms += sum(
            float(row["timing_ms"]["ordinary_candidate_evaluation"])  # type: ignore[index]
            for row in selected
        )

    unilateral_invariants = all(
        not bool(row["acceptance"]["unilateral_pareto"])  # type: ignore[index]
        or float(row["maximum_player_deviation_gain_increase"])
        <= float(row["acceptance"]["numerical_guard"])  # type: ignore[index]
        for row in candidate_records
    )
    coalition_invariants = all(
        not bool(row["acceptance"]["coalition_stress"])  # type: ignore[index]
        or float(row["maximum_coalition_deviation_gain_increase"])
        <= float(row["acceptance"]["numerical_guard"])  # type: ignore[index]
        for row in candidate_records
    )
    gates = parsed["gates"]

    def required(field: str, condition: bool) -> bool:
        return condition if gates[field] else True

    correctness_results = {
        "minimum_development_groups": (
            len({context.group_id for context in contexts})
            >= gates["minimum_development_groups"]
        ),
        "source_quality": max(
            float(row["selected_normalized_nash_conv"])
            for row in source_records
        )
        <= parsed["maximum_source_normalized_nash_conv"],
        "exact_evaluation_identity": (
            maximum_error <= gates["maximum_exact_evaluation_error"]
        ),
        "best_response_action_identity": (
            action_mismatches
            <= gates["maximum_best_response_action_mismatches"]
        ),
        "source_relative_replay_identity": all(
            bool(row["source_relative_replay_exact"]) for row in target_records
        ),
        "unilateral_acceptance_invariants": required(
            "require_all_unilateral_acceptance_invariants",
            unilateral_invariants,
        ),
        "coalition_acceptance_invariants": required(
            "require_all_coalition_acceptance_invariants",
            coalition_invariants,
        ),
    }
    mechanism_results = {
        "hot_tape_strictly_faster": required(
            "hot_tape_strictly_faster_than_ordinary_evaluation",
            total_hot_ms < total_ordinary_candidate_ms,
        ),
        "two_candidate_reuse_strictly_faster": required(
            "two_candidate_reuse_strictly_faster_than_two_ordinary_evaluations",
            two_hot_ms < two_ordinary_ms,
        ),
    }
    primary_acceptance = primary["acceptance_fractions"]
    primary_raw = primary["arm_raw_reduction"]
    primary_rates = primary["raw_reduction_per_millisecond"]
    strategic_results = {
        "aggregate_acceptance_beats_blind_raw": required(
            "primary_aggregate_acceptance_strictly_beats_blind_raw_reduction",
            float(primary_raw["aggregate_exact"]) > float(primary_raw["blind"]),
        ),
        "aggregate_one_shot_hot_rate_beats_blind": required(
            "primary_aggregate_acceptance_hot_rate_strictly_beats_blind",
            float(primary_rates["aggregate_tape_one_shot"])
            > float(primary_rates["blind"]),
        ),
        "unilateral_acceptance_fraction": (
            float(primary_acceptance["unilateral_pareto"])
            >= gates["minimum_primary_unilateral_accept_target_fraction"]
        ),
        "coalition_acceptance_fraction": (
            float(primary_acceptance["coalition_stress"])
            >= gates["minimum_primary_coalition_accept_target_fraction"]
        ),
        "coalition_acceptance_positive_normalized_reduction": required(
            "primary_coalition_acceptance_has_positive_normalized_reduction",
            float(primary["arm_normalized_reduction"]["coalition_stress"]) > 0.0,
        ),
    }

    serialized = _serialized_config(parsed)
    canonical_config_sha = hashlib.sha256(
        json.dumps(serialized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": 1,
        "experiment_type": "multiway_river_full_search_acceptance_development",
        "status": "group_separated_development_only",
        "config": serialized,
        "canonical_config_sha256": canonical_config_sha,
        "environment": environment_metadata(),
        "counts": {
            "groups": len({context.group_id for context in contexts}),
            "contexts": len(contexts),
            "targets": len(target_records),
            "candidate_records": len(candidate_records),
            "reserved_contexts_materialized": sum(
                context.split != "development" for context in contexts
            ),
        },
        "aggregate": {
            "maximum_source_normalized_nash_conv": max(
                float(row["selected_normalized_nash_conv"])
                for row in source_records
            ),
            "maximum_absolute_evaluation_error": maximum_error,
            "best_response_action_mismatches": action_mismatches,
            "ordinary_candidate_evaluation_ms": total_ordinary_candidate_ms,
            "hot_tape_candidate_evaluation_ms": total_hot_ms,
            "hot_tape_speedup": total_ordinary_candidate_ms / total_hot_ms,
            "two_candidate_ordinary_ms": two_ordinary_ms,
            "two_candidate_compile_plus_hot_ms": two_hot_ms,
            "two_candidate_reuse_speedup": two_ordinary_ms / two_hot_ms,
        },
        "gates": {
            "requirements": gates,
            "correctness": correctness_results,
            "mechanism": mechanism_results,
            "primary_strategy": strategic_results,
            "correctness_passed": all(correctness_results.values()),
            "mechanism_passed": all(mechanism_results.values()),
            "primary_strategy_passed": all(strategic_results.values()),
            "passed": all(
                (
                    *correctness_results.values(),
                    *mechanism_results.values(),
                    *strategic_results.values(),
                )
            ),
        },
        "primary_summary": primary,
        "summaries": summaries,
        "timing": {"wall_seconds": time.perf_counter() - experiment_start},
        "contexts": serialized_contexts,
        "sources": source_records,
        "targets": target_records,
        "records": candidate_records,
        "limitations": [
            "Development groups only; no validation or test context was constructed.",
            "NashConv is unilateral incentive, not two-player exploitability.",
            "Coalitions share cards and transferable utility as a strong stress model.",
            "The explicit joint range and Python timings are teacher-only.",
            "No scheduler, action-pruning, earlier-street, or six-player claim follows.",
        ],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_multiway_search_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "multiway search acceptance: "
        f"contexts={result['counts']['contexts']}, "
        f"targets={result['counts']['targets']}, "
        f"records={result['counts']['candidate_records']}, "
        f"max_error={result['aggregate']['maximum_absolute_evaluation_error']:.3e}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
