"""Matched branching-factor experiment for fixed- and multi-size river trees."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from dataclasses import asdict
from pathlib import Path
from statistics import mean, median
from typing import Any, TypeAlias

from .cfr import TabularCFR
from .dependency_tape import CompiledPolicyDependencyTape
from .evaluation import (
    EvaluationResult,
    Policy,
    best_response,
    collect_information_sets,
    evaluate_profile,
    expected_utilities,
)
from .game import Action
from .reporting import environment_metadata
from .river import RiverHoldem
from .river_context import CONTEXT_FAMILIES, generate_river_contexts
from .river_incremental import (
    RiverPolicyEvaluationCache,
    RiverRangeDelta,
    make_support_swap_perturbation,
)
from .river_multi_size import MultiSizeRiverHoldem
from .river_multi_size_audit import audit_multi_size_payoffs
from .river_range_reuse import make_blocker_perturbation
from .updates import UPDATE_RULES

RiverShapeGame: TypeAlias = RiverHoldem | MultiSizeRiverHoldem
_SHAPES = ("fixed_single", "multi_size_3x2")


def _evaluation_error(first: EvaluationResult, second: EvaluationResult) -> float:
    first_values = (
        *first.utilities,
        *first.best_response_values,
        *first.deviation_gains,
        first.nash_conv,
        first.exploitability or 0.0,
    )
    second_values = (
        *second.utilities,
        *second.best_response_values,
        *second.deviation_gains,
        second.nash_conv,
        second.exploitability or 0.0,
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


def _action_comparison(
    game: RiverShapeGame,
    policy: Policy,
    candidate: tuple[dict[str, Action], ...],
    reference: tuple[dict[str, Action], ...],
    best_response_values: tuple[float, ...],
) -> tuple[int, float]:
    """Report literal disagreements and their exact pure-response value loss."""

    mismatches = _action_mismatches(candidate, reference)
    if mismatches == 0:
        return 0, 0.0

    maximum_loss = 0.0
    for player, reference_actions in enumerate(reference):
        if not any(
            candidate[player].get(key) != action
            for key, action in reference_actions.items()
        ):
            continue
        information_sets = collect_information_sets(game, player)
        candidate_policy: Policy = {
            key: dict(distribution) for key, distribution in policy.items()
        }
        for key, actions in information_sets.items():
            selected = candidate[player].get(key)
            if selected not in actions:
                raise AssertionError("tape best response omitted a target information set")
            candidate_policy[key] = {
                action: float(action == selected) for action in actions
            }
        candidate_value = expected_utilities(game, candidate_policy)[player]
        maximum_loss = max(
            maximum_loss,
            max(0.0, best_response_values[player] - candidate_value),
        )
    return mismatches, maximum_loss


def _factorized_likelihood_target(
    source: RiverHoldem,
    *,
    player: int,
    minimum: float,
    maximum: float,
) -> tuple[RiverHoldem, dict[str, object]]:
    hands = tuple(source.marginal_distribution(player))
    if len(hands) < 2:
        raise ValueError("factorized likelihood update requires two private hands")
    likelihoods = {
        hand: minimum + (maximum - minimum) * index / (len(hands) - 1)
        for index, hand in enumerate(hands)
    }
    target = RiverHoldem.from_joint_weights(
        board=source.board,
        pot=source.pot,
        stacks=source.stacks,
        bet_size=source.bet_size,
        raise_to=source.raise_to,
        joint_weights={
            deal: probability * likelihoods[deal.hand(player)]
            for deal, probability in source.deals
        },
    )
    delta = RiverRangeDelta.between(source, target)
    return target, {
        "player": player,
        "minimum_likelihood": minimum,
        "maximum_likelihood": maximum,
        "changed_deals": len(delta.changes),
        "root_joint_total_variation": delta.total_variation,
        "support_preserved": set(source.joint_distribution())
        == set(target.joint_distribution()),
    }


def _targets(
    source: RiverHoldem,
    *,
    root_tv_budget: float,
    maximum_donor_fraction: float,
    likelihood_minimum: float,
    likelihood_maximum: float,
) -> tuple[tuple[str, str, RiverHoldem, dict[str, object]], ...]:
    result = []
    for player in (0, 1):
        target, metadata = make_blocker_perturbation(
            source,
            player=player,
            root_tv_budget=root_tv_budget,
            maximum_donor_fraction=maximum_donor_fraction,
        )
        result.append((f"blocker_reweight_p{player}", "sparse_reweight", target, metadata))
    for player in (0, 1):
        target, metadata = make_support_swap_perturbation(source, player=player)
        result.append((f"support_swap_p{player}", "sparse_support", target, metadata))
    target, metadata = _factorized_likelihood_target(
        source,
        player=0,
        minimum=likelihood_minimum,
        maximum=likelihood_maximum,
    )
    result.append(("factorized_likelihood_p0", "factorized_dense", target, metadata))
    return tuple(result)


def _shape_game(
    range_game: RiverHoldem,
    shape: str,
    parsed: dict[str, Any],
) -> RiverShapeGame:
    pot = range_game.pot
    joint = range_game.joint_distribution()
    if shape == "fixed_single":
        return RiverHoldem.from_joint_weights(
            board=range_game.board,
            pot=pot,
            stacks=range_game.stacks,
            bet_size=pot * parsed["baseline_bet_pot_fraction"],
            raise_to=pot * parsed["baseline_raise_to_pot_fraction"],
            joint_weights=joint,
        )
    if shape == "multi_size_3x2":
        return MultiSizeRiverHoldem.from_joint_weights(
            board=range_game.board,
            pot=pot,
            stacks=range_game.stacks,
            bet_sizes=tuple(
                pot * fraction for fraction in parsed["bet_pot_fractions"]
            ),
            raise_to_sizes=tuple(
                pot * fraction for fraction in parsed["raise_to_pot_fractions"]
            ),
            joint_weights=joint,
        )
    raise AssertionError(f"unvalidated tree shape {shape!r}")


def _dependency_tape_sha256() -> str:
    path = Path(__file__).with_name("dependency_tape.py")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _positive_finite(value: float) -> bool:
    return math.isfinite(value) and value > 0.0


def _validate_config(config: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "groups",
        "seed",
        "hands_per_player",
        "families",
        "included_splits",
        "tree_shapes",
        "baseline_bet_pot_fraction",
        "baseline_raise_to_pot_fraction",
        "bet_pot_fractions",
        "raise_to_pot_fractions",
        "solver",
        "source_policy_checkpoints",
        "root_tv_budget",
        "maximum_donor_fraction",
        "factorized_likelihood_minimum",
        "factorized_likelihood_maximum",
        "dense_threshold",
        "expected_dependency_tape_sha256",
        "gates",
    }
    unknown = set(config) - allowed
    if unknown:
        raise ValueError(f"unknown multi-size experiment fields: {sorted(unknown)!r}")

    groups = int(config.get("groups", 8))
    seed = int(config.get("seed", 0))
    hands = int(config.get("hands_per_player", 5))
    families = tuple(str(value) for value in config.get("families", CONTEXT_FAMILIES))
    splits = tuple(str(value) for value in config.get("included_splits", ("development",)))
    shapes = tuple(str(value) for value in config.get("tree_shapes", _SHAPES))
    baseline_bet = float(config.get("baseline_bet_pot_fraction", 0.5))
    baseline_raise = float(config.get("baseline_raise_to_pot_fraction", 1.5))
    bets = tuple(float(value) for value in config.get("bet_pot_fractions", (0.25, 0.5, 0.75)))
    raises = tuple(float(value) for value in config.get("raise_to_pot_fractions", (1.5, 2.0)))
    solver = str(config.get("solver", "dcfr"))
    checkpoints = tuple(
        int(value) for value in config.get("source_policy_checkpoints", (1, 4, 16))
    )
    root_tv = float(config.get("root_tv_budget", 0.01))
    donor_fraction = float(config.get("maximum_donor_fraction", 0.75))
    likelihood_minimum = float(config.get("factorized_likelihood_minimum", 0.5))
    likelihood_maximum = float(config.get("factorized_likelihood_maximum", 1.5))
    dense_threshold = float(config.get("dense_threshold", 0.35))
    expected_tape_sha = str(config.get("expected_dependency_tape_sha256", ""))
    gates = config.get("gates")

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
        raise ValueError("multi-size branching evidence is development-only")
    if shapes != _SHAPES:
        raise ValueError(f"tree_shapes must be exactly {list(_SHAPES)!r}")
    if not _positive_finite(baseline_bet) or not _positive_finite(baseline_raise):
        raise ValueError("baseline size fractions must be finite and positive")
    if baseline_raise < 2.0 * baseline_bet:
        raise ValueError("baseline raise-to must be at least twice its bet")
    if len(bets) != 3 or not all(_positive_finite(value) for value in bets):
        raise ValueError("bet_pot_fractions must contain exactly three positive values")
    if len(raises) != 2 or not all(_positive_finite(value) for value in raises):
        raise ValueError("raise_to_pot_fractions must contain exactly two positive values")
    if bets != tuple(sorted(set(bets))) or raises != tuple(sorted(set(raises))):
        raise ValueError("multi-size fractions must be strictly increasing")
    if min(raises) < 2.0 * max(bets):
        raise ValueError("both raises must be legal after every opening bet")
    if baseline_bet not in bets or baseline_raise not in raises:
        raise ValueError("the fixed baseline must be nested inside the multi-size actions")
    if max((*bets, *raises)) > 2.0:
        raise ValueError("size fractions must fit the generated two-pot effective stack")
    if solver not in UPDATE_RULES:
        raise ValueError(f"unsupported solver {solver!r}")
    if not checkpoints or checkpoints != tuple(sorted(set(checkpoints))) or checkpoints[0] <= 0:
        raise ValueError("source checkpoints must be sorted unique positive integers")
    if not 0.0 < root_tv < 0.5 or not 0.0 < donor_fraction < 1.0:
        raise ValueError("sparse perturbation controls are outside their open ranges")
    if (
        not _positive_finite(likelihood_minimum)
        or not _positive_finite(likelihood_maximum)
        or likelihood_minimum >= likelihood_maximum
    ):
        raise ValueError("factorized likelihood bounds must be finite and increasing")
    if not math.isfinite(dense_threshold) or not 0.0 < dense_threshold < 1.0:
        raise ValueError("dense_threshold must lie strictly between zero and one")
    if len(expected_tape_sha) != 64 or any(
        character not in "0123456789abcdef" for character in expected_tape_sha
    ):
        raise ValueError("expected dependency-tape SHA-256 must be lowercase hexadecimal")

    gate_fields = {
        "maximum_absolute_evaluation_error",
        "maximum_best_response_action_value_loss",
        "maximum_payoff_audit_error",
        "maximum_sparse_dirty_fraction",
        "minimum_sparse_auto_fraction",
        "minimum_dense_auto_fraction",
    }
    if not isinstance(gates, dict) or set(gates) != gate_fields:
        raise ValueError("gates must contain exactly the frozen branching controls")
    normalized_gates = {key: float(value) for key, value in gates.items()}
    if any(not math.isfinite(value) or value < 0.0 for value in normalized_gates.values()):
        raise ValueError("gate values must be finite and nonnegative")
    if any(
        normalized_gates[key] > 1.0
        for key in (
            "maximum_sparse_dirty_fraction",
            "minimum_sparse_auto_fraction",
            "minimum_dense_auto_fraction",
        )
    ):
        raise ValueError("dirty and execution-mode fractions cannot exceed one")

    return {
        "groups": groups,
        "seed": seed,
        "hands_per_player": hands,
        "families": families,
        "included_splits": splits,
        "tree_shapes": shapes,
        "baseline_bet_pot_fraction": baseline_bet,
        "baseline_raise_to_pot_fraction": baseline_raise,
        "bet_pot_fractions": bets,
        "raise_to_pot_fractions": raises,
        "solver": solver,
        "source_policy_checkpoints": checkpoints,
        "root_tv_budget": root_tv,
        "maximum_donor_fraction": donor_fraction,
        "factorized_likelihood_minimum": likelihood_minimum,
        "factorized_likelihood_maximum": likelihood_maximum,
        "dense_threshold": dense_threshold,
        "expected_dependency_tape_sha256": expected_tape_sha,
        "gates": normalized_gates,
    }


def _changed_deals(source: RiverShapeGame, target: RiverShapeGame) -> int:
    source_distribution = source.joint_distribution()
    target_distribution = target.joint_distribution()
    return sum(
        source_distribution.get(deal, 0.0) != target_distribution.get(deal, 0.0)
        for deal in set(source_distribution) | set(target_distribution)
    )


def _summaries(records: list[dict[str, Any]]) -> list[dict[str, object]]:
    summaries = []
    for shape in _SHAPES:
        for target_kind in ("sparse_reweight", "sparse_support", "factorized_dense"):
            rows = [
                row
                for row in records
                if row["shape"] == shape and row["target_kind"] == target_kind
            ]
            summaries.append(
                {
                    "shape": shape,
                    "target_kind": target_kind,
                    "records": len(rows),
                    "mean_changed_deals": mean(float(row["changed_deals"]) for row in rows),
                    "mean_changed_deal_fraction": mean(
                        float(row["changed_deal_fraction"]) for row in rows
                    ),
                    "mean_dirty_nodes": mean(
                        float(row["sparse_diagnostics"]["dirty_nodes"])
                        for row in rows
                    ),
                    "mean_dirty_node_fraction": mean(
                        float(row["sparse_diagnostics"]["dirty_node_fraction"])
                        for row in rows
                    ),
                    "median_dirty_node_fraction": median(
                        float(row["sparse_diagnostics"]["dirty_node_fraction"])
                        for row in rows
                    ),
                    "maximum_dirty_node_fraction": max(
                        float(row["sparse_diagnostics"]["dirty_node_fraction"])
                        for row in rows
                    ),
                    "mean_sparse_recomputed_nodes": mean(
                        float(row["sparse_diagnostics"]["recomputed_nodes"])
                        for row in rows
                    ),
                    "mean_best_response_action_flips": mean(
                        float(row["sparse_diagnostics"]["best_response_action_flips"])
                        for row in rows
                    ),
                    "automatic_sparse_fraction": mean(
                        row["automatic_diagnostics"]["execution_mode"] == "sparse"
                        for row in rows
                    ),
                }
            )
    return summaries


def _paired_transfer(
    source_records: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> dict[str, object]:
    source_by_key = {
        (row["context_id"], row["checkpoint"], row["shape"]): row
        for row in source_records
    }
    topology_pairs = []
    for context_id, checkpoint, shape in source_by_key:
        if shape != "fixed_single":
            continue
        fixed = source_by_key[(context_id, checkpoint, "fixed_single")]["topology"]
        wide = source_by_key[(context_id, checkpoint, "multi_size_3x2")]["topology"]
        topology_pairs.append(
            {
                "numeric_node_ratio": wide["numeric_nodes"] / fixed["numeric_nodes"],
                "tree_state_ratio": wide["compiled_tree_states"] / fixed["compiled_tree_states"],
                "dependency_edge_ratio": wide["dependency_edges"] / fixed["dependency_edges"],
                "runtime_byte_ratio": wide["contiguous_runtime_bytes"]
                / fixed["contiguous_runtime_bytes"],
                "selector_ratio": wide["selector_nodes"] / fixed["selector_nodes"],
            }
        )

    target_by_key = {
        (
            row["context_id"],
            row["checkpoint"],
            row["target_name"],
            row["shape"],
        ): row
        for row in records
    }
    dirty_summaries = []
    for target_kind in ("sparse_reweight", "sparse_support", "factorized_dense"):
        pairs = []
        for key, fixed in target_by_key.items():
            context_id, checkpoint, target_name, shape = key
            if shape != "fixed_single" or fixed["target_kind"] != target_kind:
                continue
            wide = target_by_key[
                (context_id, checkpoint, target_name, "multi_size_3x2")
            ]
            pairs.append(
                {
                    "dirty_node_ratio": wide["sparse_diagnostics"]["dirty_nodes"]
                    / fixed["sparse_diagnostics"]["dirty_nodes"],
                    "dirty_fraction_change": (
                        wide["sparse_diagnostics"]["dirty_node_fraction"]
                        - fixed["sparse_diagnostics"]["dirty_node_fraction"]
                    ),
                    "recomputed_node_ratio": (
                        wide["sparse_diagnostics"]["recomputed_nodes"]
                        / fixed["sparse_diagnostics"]["recomputed_nodes"]
                    ),
                }
            )
        dirty_summaries.append(
            {
                "target_kind": target_kind,
                "pairs": len(pairs),
                "mean_dirty_node_ratio": mean(row["dirty_node_ratio"] for row in pairs),
                "mean_dirty_fraction_change": mean(
                    row["dirty_fraction_change"] for row in pairs
                ),
                "mean_recomputed_node_ratio": mean(
                    row["recomputed_node_ratio"] for row in pairs
                ),
            }
        )

    return {
        "topology_pairs": len(topology_pairs),
        "mean_numeric_node_ratio": mean(
            row["numeric_node_ratio"] for row in topology_pairs
        ),
        "mean_tree_state_ratio": mean(
            row["tree_state_ratio"] for row in topology_pairs
        ),
        "mean_dependency_edge_ratio": mean(
            row["dependency_edge_ratio"] for row in topology_pairs
        ),
        "mean_runtime_byte_ratio": mean(
            row["runtime_byte_ratio"] for row in topology_pairs
        ),
        "mean_selector_ratio": mean(row["selector_ratio"] for row in topology_pairs),
        "dirty_transfer": dirty_summaries,
    }


def run_multi_size_river_experiment(config: dict[str, Any]) -> dict[str, Any]:
    parsed = _validate_config(config)
    experiment_start = time.perf_counter()
    dependency_sha = _dependency_tape_sha256()
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
    source_records: list[dict[str, Any]] = []
    payoff_audits: list[dict[str, Any]] = []

    for context in contexts:
        range_source = context.game
        range_targets = _targets(
            range_source,
            root_tv_budget=parsed["root_tv_budget"],
            maximum_donor_fraction=parsed["maximum_donor_fraction"],
            likelihood_minimum=parsed["factorized_likelihood_minimum"],
            likelihood_maximum=parsed["factorized_likelihood_maximum"],
        )
        wide_audit_games = (("source", range_source), *(
            (name, target) for name, _, target, _ in range_targets
        ))
        for range_name, range_game in wide_audit_games:
            wide = _shape_game(range_game, "multi_size_3x2", parsed)
            assert isinstance(wide, MultiSizeRiverHoldem)
            audit = audit_multi_size_payoffs(wide)
            payoff_audits.append(
                {
                    "context_id": context.context_id,
                    "range_name": range_name,
                    **asdict(audit),
                    "expected_terminal_histories": len(wide.deals) * 19,
                }
            )

        for shape in parsed["tree_shapes"]:
            source = _shape_game(range_source, shape, parsed)
            targets = tuple(
                (
                    name,
                    kind,
                    _shape_game(target, shape, parsed),
                    metadata,
                )
                for name, kind, target, metadata in range_targets
            )
            solver = TabularCFR(source, variant=parsed["solver"])  # type: ignore[arg-type]
            previous_checkpoint = 0
            for checkpoint in parsed["source_policy_checkpoints"]:
                solver.run(checkpoint - previous_checkpoint)
                previous_checkpoint = checkpoint
                policy = solver.average_strategy()
                tape = CompiledPolicyDependencyTape(
                    source,
                    policy,
                    universe_games=tuple(target for _, _, target, _ in targets),
                    dense_threshold=parsed["dense_threshold"],
                )
                source_full = evaluate_profile(source, policy)
                source_actions = tuple(
                    best_response(source, policy, player)[1]
                    for player in range(source.num_players)
                )
                source_action_mismatches, source_action_value_loss = (
                    _action_comparison(
                        source,
                        policy,
                        tape.source_result.best_response_actions,
                        source_actions,
                        source_full.best_response_values,
                    )
                )
                source_records.append(
                    {
                        "context_id": context.context_id,
                        "group_id": context.group_id,
                        "family": context.family,
                        "shape": shape,
                        "checkpoint": checkpoint,
                        "source_evaluation_error": _evaluation_error(
                            tape.source_result.evaluation,
                            source_full,
                        ),
                        "source_best_response_action_mismatches": (
                            source_action_mismatches
                        ),
                        "source_best_response_action_value_loss": (
                            source_action_value_loss
                        ),
                        "topology": tape.topology_summary(),
                    }
                )
                specialized = (
                    RiverPolicyEvaluationCache(source, policy)
                    if isinstance(source, RiverHoldem)
                    else None
                )
                first_result = None
                for target_name, target_kind, target, metadata in targets:
                    full = evaluate_profile(target, policy)
                    sparse = tape.recertify_game(target, mode="sparse")
                    dense = tape.recertify_game(target, mode="dense")
                    automatic = tape.recertify_game(target, mode="auto")
                    exact_actions = tuple(
                        best_response(target, policy, player)[1]
                        for player in range(target.num_players)
                    )
                    if first_result is None:
                        first_result = (target, sparse)
                    changed = _changed_deals(source, target)
                    specialized_error = None
                    if specialized is not None:
                        specialized_error = _evaluation_error(
                            sparse.evaluation,
                            specialized.recertify(target).evaluation,
                        )
                    sparse_action_mismatches, sparse_action_value_loss = (
                        _action_comparison(
                            target,
                            policy,
                            sparse.best_response_actions,
                            exact_actions,
                            full.best_response_values,
                        )
                    )
                    dense_action_mismatches, dense_action_value_loss = (
                        _action_comparison(
                            target,
                            policy,
                            dense.best_response_actions,
                            exact_actions,
                            full.best_response_values,
                        )
                    )
                    automatic_action_mismatches, automatic_action_value_loss = (
                        _action_comparison(
                            target,
                            policy,
                            automatic.best_response_actions,
                            exact_actions,
                            full.best_response_values,
                        )
                    )
                    records.append(
                        {
                            "context_id": context.context_id,
                            "group_id": context.group_id,
                            "family": context.family,
                            "shape": shape,
                            "checkpoint": checkpoint,
                            "target_name": target_name,
                            "target_kind": target_kind,
                            "target_metadata": metadata,
                            "source_deals": len(source.deals),
                            "target_deals": len(target.deals),
                            "changed_deals": changed,
                            "changed_deal_fraction": changed / len(source.deals),
                            "root_joint_total_variation": source.total_variation(target),
                            "full_evaluation_error": _evaluation_error(
                                sparse.evaluation,
                                full,
                            ),
                            "specialized_evaluation_error": specialized_error,
                            "dense_sparse_evaluation_error": _evaluation_error(
                                dense.evaluation,
                                sparse.evaluation,
                            ),
                            "automatic_sparse_evaluation_error": _evaluation_error(
                                automatic.evaluation,
                                sparse.evaluation,
                            ),
                            "exact_sparse_action_mismatches": (
                                sparse_action_mismatches
                            ),
                            "exact_sparse_action_value_loss": (
                                sparse_action_value_loss
                            ),
                            "exact_dense_action_mismatches": dense_action_mismatches,
                            "exact_dense_action_value_loss": dense_action_value_loss,
                            "exact_automatic_action_mismatches": (
                                automatic_action_mismatches
                            ),
                            "exact_automatic_action_value_loss": (
                                automatic_action_value_loss
                            ),
                            "sparse_dense_action_identity": (
                                sparse.best_response_actions
                                == dense.best_response_actions
                            ),
                            "automatic_sparse_action_identity": (
                                automatic.best_response_actions
                                == sparse.best_response_actions
                            ),
                            "sparse_diagnostics": asdict(sparse.diagnostics),
                            "dense_diagnostics": asdict(dense.diagnostics),
                            "automatic_diagnostics": asdict(automatic.diagnostics),
                        }
                    )

                assert first_result is not None
                repeat_target, original = first_result
                repeated = tape.recertify_game(repeat_target, mode="sparse")
                source_records[-1]["source_relative_repeat_evaluation_error"] = (
                    _evaluation_error(original.evaluation, repeated.evaluation)
                )
                source_records[-1]["source_relative_repeat_action_identity"] = (
                    original.best_response_actions == repeated.best_response_actions
                )

    errors = [
        *(float(row["source_evaluation_error"]) for row in source_records),
        *(
            float(row[field])
            for row in records
            for field in (
                "full_evaluation_error",
                "dense_sparse_evaluation_error",
                "automatic_sparse_evaluation_error",
            )
        ),
        *(
            float(row["specialized_evaluation_error"])
            for row in records
            if row["specialized_evaluation_error"] is not None
        ),
        *(
            float(row["source_relative_repeat_evaluation_error"])
            for row in source_records
        ),
    ]
    action_mismatches = sum(
        int(row[field])
        for row in records
        for field in (
            "exact_sparse_action_mismatches",
            "exact_dense_action_mismatches",
            "exact_automatic_action_mismatches",
        )
    ) + sum(
        int(row["source_best_response_action_mismatches"])
        for row in source_records
    )
    maximum_action_value_loss = max(
        *(
            float(row[field])
            for row in records
            for field in (
                "exact_sparse_action_value_loss",
                "exact_dense_action_value_loss",
                "exact_automatic_action_value_loss",
            )
        ),
        *(
            float(row["source_best_response_action_value_loss"])
            for row in source_records
        ),
    )
    sparse_rows = [row for row in records if row["target_kind"] != "factorized_dense"]
    dense_rows = [row for row in records if row["target_kind"] == "factorized_dense"]
    sparse_auto_fraction = mean(
        row["automatic_diagnostics"]["execution_mode"] == "sparse"
        for row in sparse_rows
    )
    dense_auto_fraction = mean(
        row["automatic_diagnostics"]["execution_mode"] == "dense"
        for row in dense_rows
    )
    maximum_sparse_dirty = max(
        float(row["sparse_diagnostics"]["dirty_node_fraction"])
        for row in sparse_rows
    )
    maximum_payoff_error = max(
        float(row["maximum_absolute_error"]) for row in payoff_audits
    )
    requirements = parsed["gates"]
    gate_results = {
        "dependency_tape_is_unchanged": dependency_sha
        == parsed["expected_dependency_tape_sha256"],
        "exact_evaluation_identity": max(errors)
        <= requirements["maximum_absolute_evaluation_error"],
        "best_response_actions_are_value_equivalent": maximum_action_value_loss
        <= requirements["maximum_best_response_action_value_loss"]
        and all(
            row["sparse_dense_action_identity"]
            and row["automatic_sparse_action_identity"]
            for row in records
        ),
        "payoff_audit_identity": maximum_payoff_error
        <= requirements["maximum_payoff_audit_error"]
        and all(
            row["terminal_histories"] == row["expected_terminal_histories"]
            for row in payoff_audits
        ),
        "dependencies_are_topological": all(
            row["topology"]["dependencies_are_topological"]
            for row in source_records
        ),
        "source_relative_call_order_identity": all(
            row["source_relative_repeat_action_identity"]
            and row["source_relative_repeat_evaluation_error"] == 0.0
            for row in source_records
        ),
        "sparse_cones_remain_below_threshold": maximum_sparse_dirty
        <= requirements["maximum_sparse_dirty_fraction"],
        "sparse_auto_fraction": sparse_auto_fraction
        >= requirements["minimum_sparse_auto_fraction"],
        "dense_auto_fraction": dense_auto_fraction
        >= requirements["minimum_dense_auto_fraction"],
    }

    serialized_config = {
        **parsed,
        "families": list(parsed["families"]),
        "included_splits": list(parsed["included_splits"]),
        "tree_shapes": list(parsed["tree_shapes"]),
        "bet_pot_fractions": list(parsed["bet_pot_fractions"]),
        "raise_to_pot_fractions": list(parsed["raise_to_pot_fractions"]),
        "source_policy_checkpoints": list(parsed["source_policy_checkpoints"]),
    }
    return {
        "schema_version": 1,
        "experiment_type": "multi_size_river_dependency_tape_transfer",
        "status": "development_measurement_only",
        "config": serialized_config,
        "environment": environment_metadata(),
        "dependency_tape_sha256": dependency_sha,
        "counts": {
            "groups": len({context.group_id for context in contexts}),
            "contexts": len(contexts),
            "source_policy_tapes": len(source_records),
            "target_records": len(records),
            "payoff_audits": len(payoff_audits),
        },
        "aggregate": {
            "maximum_absolute_evaluation_error": max(errors),
            "literal_best_response_action_mismatches": action_mismatches,
            "maximum_best_response_action_value_loss": maximum_action_value_loss,
            "maximum_payoff_audit_error": maximum_payoff_error,
            "maximum_sparse_dirty_fraction": maximum_sparse_dirty,
            "sparse_target_auto_sparse_fraction": sparse_auto_fraction,
            "factorized_target_auto_dense_fraction": dense_auto_fraction,
        },
        "gates": {
            "requirements": requirements,
            "results": gate_results,
            "passed": all(gate_results.values()),
        },
        "summaries": _summaries(records),
        "paired_transfer": _paired_transfer(source_records, records),
        "timing": {"wall_seconds": time.perf_counter() - experiment_start},
        "payoff_audits": payoff_audits,
        "sources": source_records,
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
    result = run_multi_size_river_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "multi-size dependency transfer: "
        f"records={result['counts']['target_records']}, "
        f"max_error={result['aggregate']['maximum_absolute_evaluation_error']:.3e}, "
        f"max_sparse_dirty={result['aggregate']['maximum_sparse_dirty_fraction']:.3f}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
