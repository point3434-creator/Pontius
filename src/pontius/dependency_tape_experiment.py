"""Differential matrix for the generic flat dependency tape."""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict
from pathlib import Path
from statistics import mean, median
from typing import Any

from .cfr import TabularCFR
from .dependency_tape import CompiledPolicyDependencyTape
from .evaluation import EvaluationResult, best_response, evaluate_profile
from .game import Action
from .reporting import environment_metadata
from .river import RiverHoldem
from .river_context import CONTEXT_FAMILIES, generate_river_contexts
from .river_incremental import (
    RiverPolicyEvaluationCache,
    RiverRangeDelta,
    make_support_swap_perturbation,
)
from .river_range_reuse import make_blocker_perturbation
from .updates import UPDATE_RULES


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
    """Count disagreements only on information sets reached by the reference game."""

    return sum(
        candidate[player].get(key) != action
        for player, actions in enumerate(reference)
        for key, action in actions.items()
    )


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


def _validate_config(config: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "groups",
        "seed",
        "hands_per_player",
        "families",
        "included_splits",
        "sequential_raise_shapes",
        "solver",
        "source_policy_checkpoints",
        "root_tv_budget",
        "maximum_donor_fraction",
        "factorized_likelihood_minimum",
        "factorized_likelihood_maximum",
        "dense_threshold",
        "gates",
    }
    unknown = set(config) - allowed
    if unknown:
        raise ValueError(f"unknown dependency-tape fields: {sorted(unknown)!r}")

    groups = int(config.get("groups", 8))
    seed = int(config.get("seed", 0))
    hands = int(config.get("hands_per_player", 5))
    families = tuple(str(value) for value in config.get("families", CONTEXT_FAMILIES))
    splits = tuple(str(value) for value in config.get("included_splits", ("development",)))
    shapes = tuple(config.get("sequential_raise_shapes", (False, True)))
    solver = str(config.get("solver", "dcfr"))
    checkpoints = tuple(
        int(value) for value in config.get("source_policy_checkpoints", (1, 4, 16))
    )
    root_tv = float(config.get("root_tv_budget", 0.01))
    donor_fraction = float(config.get("maximum_donor_fraction", 0.75))
    likelihood_minimum = float(config.get("factorized_likelihood_minimum", 0.5))
    likelihood_maximum = float(config.get("factorized_likelihood_maximum", 1.5))
    dense_threshold = float(config.get("dense_threshold", 0.35))
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
        raise ValueError("dependency-tape differential evidence is development-only")
    if shapes != (False, True):
        raise ValueError("sequential_raise_shapes must be exactly [false, true]")
    if solver not in UPDATE_RULES:
        raise ValueError(f"unsupported solver {solver!r}")
    if not checkpoints or checkpoints != tuple(sorted(set(checkpoints))) or checkpoints[0] <= 0:
        raise ValueError("source checkpoints must be sorted unique positive integers")
    if not 0.0 < root_tv < 0.5 or not 0.0 < donor_fraction < 1.0:
        raise ValueError("sparse perturbation controls are outside their open ranges")
    if (
        not _isfinite_positive(likelihood_minimum)
        or not _isfinite_positive(likelihood_maximum)
        or likelihood_minimum >= likelihood_maximum
    ):
        raise ValueError("factorized likelihood bounds must be finite positive and increasing")
    if not math.isfinite(dense_threshold) or not 0.0 < dense_threshold < 1.0:
        raise ValueError("dense_threshold must lie strictly between zero and one")

    gate_fields = {
        "maximum_absolute_evaluation_error",
        "minimum_sparse_auto_fraction",
        "minimum_dense_auto_fraction",
    }
    if not isinstance(gates, dict) or set(gates) != gate_fields:
        raise ValueError("gates must contain exactly the frozen differential controls")
    normalized_gates = {key: float(value) for key, value in gates.items()}
    if any(not math.isfinite(value) or value < 0.0 for value in normalized_gates.values()):
        raise ValueError("gate values must be finite and nonnegative")
    if any(
        normalized_gates[key] > 1.0
        for key in ("minimum_sparse_auto_fraction", "minimum_dense_auto_fraction")
    ):
        raise ValueError("auto-mode fractions cannot exceed one")

    return {
        "groups": groups,
        "seed": seed,
        "hands_per_player": hands,
        "families": families,
        "included_splits": splits,
        "sequential_raise_shapes": shapes,
        "solver": solver,
        "source_policy_checkpoints": checkpoints,
        "root_tv_budget": root_tv,
        "maximum_donor_fraction": donor_fraction,
        "factorized_likelihood_minimum": likelihood_minimum,
        "factorized_likelihood_maximum": likelihood_maximum,
        "dense_threshold": dense_threshold,
        "gates": normalized_gates,
    }


def _isfinite_positive(value: float) -> bool:
    return math.isfinite(value) and value > 0.0


def run_dependency_tape_experiment(config: dict[str, Any]) -> dict[str, Any]:
    parsed = _validate_config(config)
    experiment_start = time.perf_counter()
    records: list[dict[str, Any]] = []
    source_records: list[dict[str, Any]] = []
    contexts_seen = []

    for sequential_raise in parsed["sequential_raise_shapes"]:
        contexts = generate_river_contexts(
            groups=parsed["groups"],
            seed=parsed["seed"],
            hands_per_player=parsed["hands_per_player"],
            families=parsed["families"],
            splits=parsed["included_splits"],
            sequential_raise=sequential_raise,
        )
        contexts_seen.extend((sequential_raise, context) for context in contexts)
        for context in contexts:
            source = context.game
            targets = _targets(
                source,
                root_tv_budget=parsed["root_tv_budget"],
                maximum_donor_fraction=parsed["maximum_donor_fraction"],
                likelihood_minimum=parsed["factorized_likelihood_minimum"],
                likelihood_maximum=parsed["factorized_likelihood_maximum"],
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
                source_full_actions = tuple(
                    best_response(source, policy, player)[1]
                    for player in range(source.num_players)
                )
                source_error = _evaluation_error(
                    tape.source_result.evaluation,
                    source_full,
                )
                topology = tape.topology_summary()
                source_records.append(
                    {
                        "context_id": context.context_id,
                        "group_id": context.group_id,
                        "family": context.family,
                        "sequential_raise": sequential_raise,
                        "checkpoint": checkpoint,
                        "source_evaluation_error": source_error,
                        "source_best_response_action_mismatches": _action_mismatches(
                            tape.source_result.best_response_actions,
                            source_full_actions,
                        ),
                        "topology": topology,
                    }
                )
                specialized = RiverPolicyEvaluationCache(source, policy)
                first_target_result = None
                for target_name, target_kind, target, metadata in targets:
                    delta = RiverRangeDelta.between(source, target)
                    full = evaluate_profile(target, policy)
                    specialized_result = specialized.recertify(target).evaluation
                    sparse = tape.recertify_game(target, mode="sparse")
                    dense = tape.recertify_game(target, mode="dense")
                    automatic = tape.recertify_game(target, mode="auto")
                    full_actions = tuple(
                        best_response(target, policy, player)[1]
                        for player in range(target.num_players)
                    )
                    exact_sparse_action_mismatches = _action_mismatches(
                        sparse.best_response_actions,
                        full_actions,
                    )
                    exact_dense_action_mismatches = _action_mismatches(
                        dense.best_response_actions,
                        full_actions,
                    )
                    exact_automatic_action_mismatches = _action_mismatches(
                        automatic.best_response_actions,
                        full_actions,
                    )
                    if first_target_result is None:
                        first_target_result = (target, sparse)

                    records.append(
                        {
                            "context_id": context.context_id,
                            "group_id": context.group_id,
                            "family": context.family,
                            "sequential_raise": sequential_raise,
                            "checkpoint": checkpoint,
                            "target_name": target_name,
                            "target_kind": target_kind,
                            "target_metadata": metadata,
                            "source_deals": len(source.deals),
                            "target_deals": len(target.deals),
                            "changed_deals": len(delta.changes),
                            "changed_deal_fraction": len(delta.changes) / len(source.deals),
                            "root_joint_total_variation": delta.total_variation,
                            "full_evaluation_error": _evaluation_error(
                                sparse.evaluation,
                                full,
                            ),
                            "specialized_evaluation_error": _evaluation_error(
                                sparse.evaluation,
                                specialized_result,
                            ),
                            "dense_sparse_evaluation_error": _evaluation_error(
                                sparse.evaluation,
                                dense.evaluation,
                            ),
                            "automatic_sparse_evaluation_error": _evaluation_error(
                                automatic.evaluation,
                                sparse.evaluation,
                            ),
                            "exact_sparse_action_mismatches": (
                                exact_sparse_action_mismatches
                            ),
                            "exact_dense_action_mismatches": (
                                exact_dense_action_mismatches
                            ),
                            "exact_automatic_action_mismatches": (
                                exact_automatic_action_mismatches
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

                assert first_target_result is not None
                repeat_target, original = first_target_result
                repeated = tape.recertify_game(repeat_target, mode="sparse")
                source_records[-1]["source_relative_repeat_evaluation_error"] = (
                    _evaluation_error(original.evaluation, repeated.evaluation)
                )
                source_records[-1]["source_relative_repeat_action_identity"] = (
                    original.best_response_actions == repeated.best_response_actions
                )

    if not source_records:
        raise ValueError("configuration generated no development contexts")

    all_errors = [
        *(float(row["source_evaluation_error"]) for row in source_records),
        *(
            float(row[field])
            for row in records
            for field in (
                "full_evaluation_error",
                "specialized_evaluation_error",
                "dense_sparse_evaluation_error",
                "automatic_sparse_evaluation_error",
            )
        ),
        *(
            float(row["source_relative_repeat_evaluation_error"])
            for row in source_records
        ),
    ]
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
    requirements = parsed["gates"]
    gate_results = {
        "exact_evaluation_identity": max(all_errors)
        <= requirements["maximum_absolute_evaluation_error"],
        "best_response_action_identity": sum(
            int(row[field])
            for row in records
            for field in (
                "exact_sparse_action_mismatches",
                "exact_dense_action_mismatches",
                "exact_automatic_action_mismatches",
            )
        )
        == 0
        and all(
            int(row["source_best_response_action_mismatches"]) == 0
            for row in source_records
        )
        and all(
            row["sparse_dense_action_identity"]
            and row["automatic_sparse_action_identity"]
            for row in records
        ),
        "dependencies_are_topological": all(
            row["topology"]["dependencies_are_topological"] for row in source_records
        ),
        "source_relative_call_order_identity": all(
            row["source_relative_repeat_action_identity"] for row in source_records
        ),
        "sparse_auto_fraction": sparse_auto_fraction
        >= requirements["minimum_sparse_auto_fraction"],
        "dense_auto_fraction": dense_auto_fraction
        >= requirements["minimum_dense_auto_fraction"],
    }

    summaries = []
    for target_kind in ("sparse_reweight", "sparse_support", "factorized_dense"):
        rows = [row for row in records if row["target_kind"] == target_kind]
        summaries.append(
            {
                "target_kind": target_kind,
                "records": len(rows),
                "mean_changed_deals": mean(float(row["changed_deals"]) for row in rows),
                "mean_changed_deal_fraction": mean(
                    float(row["changed_deal_fraction"]) for row in rows
                ),
                "mean_dirty_node_fraction": mean(
                    float(row["sparse_diagnostics"]["dirty_node_fraction"])
                    for row in rows
                ),
                "median_dirty_node_fraction": median(
                    float(row["sparse_diagnostics"]["dirty_node_fraction"])
                    for row in rows
                ),
                "mean_sparse_recomputed_fraction": mean(
                    float(row["sparse_diagnostics"]["recomputed_nodes"])
                    / float(row["sparse_diagnostics"]["numeric_nodes"])
                    for row in rows
                ),
                "mean_dense_recomputed_fraction": mean(
                    float(row["dense_diagnostics"]["recomputed_nodes"])
                    / float(row["dense_diagnostics"]["numeric_nodes"])
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

    return {
        "schema_version": 1,
        "experiment_type": "generic_dependency_tape_differential_matrix",
        "status": "development_measurement_only",
        "config": {
            **parsed,
            "families": list(parsed["families"]),
            "included_splits": list(parsed["included_splits"]),
            "sequential_raise_shapes": list(parsed["sequential_raise_shapes"]),
            "source_policy_checkpoints": list(parsed["source_policy_checkpoints"]),
        },
        "environment": environment_metadata(),
        "counts": {
            "groups": len({context.group_id for _, context in contexts_seen}),
            "contexts_across_tree_shapes": len(contexts_seen),
            "source_policy_tapes": len(source_records),
            "target_records": len(records),
        },
        "aggregate": {
            "maximum_absolute_evaluation_error": max(all_errors),
            "best_response_action_mismatches": sum(
                int(row[field])
                for row in records
                for field in (
                    "exact_sparse_action_mismatches",
                    "exact_dense_action_mismatches",
                    "exact_automatic_action_mismatches",
                )
            )
            + sum(
                int(row["source_best_response_action_mismatches"])
                for row in source_records
            ),
            "sparse_target_auto_sparse_fraction": sparse_auto_fraction,
            "factorized_target_auto_dense_fraction": dense_auto_fraction,
            "minimum_numeric_nodes": min(
                int(row["topology"]["numeric_nodes"]) for row in source_records
            ),
            "maximum_numeric_nodes": max(
                int(row["topology"]["numeric_nodes"]) for row in source_records
            ),
            "minimum_contiguous_runtime_bytes": min(
                int(row["topology"]["contiguous_runtime_bytes"])
                for row in source_records
            ),
            "maximum_contiguous_runtime_bytes": max(
                int(row["topology"]["contiguous_runtime_bytes"])
                for row in source_records
            ),
        },
        "gates": {
            "requirements": requirements,
            "results": gate_results,
            "passed": all(gate_results.values()),
        },
        "summaries": summaries,
        "timing": {"wall_seconds": time.perf_counter() - experiment_start},
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
    result = run_dependency_tape_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "generic dependency tape: "
        f"records={result['counts']['target_records']}, "
        f"max_error={result['aggregate']['maximum_absolute_evaluation_error']:.3e}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
