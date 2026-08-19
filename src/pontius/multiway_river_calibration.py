"""Revealed engineering calibration for the exact multiway river contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from math import isfinite
from pathlib import Path
from statistics import median
from typing import Any, Callable, TypeVar

from .cfr import TabularCFR
from .coalition import evaluate_coalition_threats
from .dependency_tape import CompiledPolicyDeltaTape
from .evaluation import (
    EvaluationResult,
    best_response,
    collect_information_sets,
    evaluate_profile,
)
from .game import Action
from .reporting import environment_metadata
from .river import HoleCards, parse_cards
from .river_multiway import MultiwayRiverHoldem

_T = TypeVar("_T")
_ALLOWED_FIELDS = {
    "evidence_stage",
    "board",
    "pot",
    "stack",
    "bet_size",
    "hands_per_player",
    "range_weight_rule",
    "solver",
    "candidate_iterations",
    "timing_repeats",
    "warmup_repeats",
    "frozen_contract_sha256",
    "maximum_exact_error",
}
_CONTRACT_PATH = (
    Path(__file__).parents[2]
    / "experiments"
    / "configs"
    / "multiway-river-contract-v1.json"
)


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    unknown = set(config) - _ALLOWED_FIELDS
    missing = _ALLOWED_FIELDS - set(config)
    if unknown or missing:
        raise ValueError(
            f"calibration fields differ: missing={sorted(missing)!r}, "
            f"unknown={sorted(unknown)!r}"
        )
    if config["evidence_stage"] != "revealed_engineering_calibration":
        raise ValueError("calibration must remain explicitly revealed")
    board = tuple(config["board"])
    if len(board) != 5 or any(not isinstance(card, str) for card in board):
        raise ValueError("board must contain five card strings")
    hands = tuple(config["hands_per_player"])
    if (
        not hands
        or any(isinstance(value, bool) or not isinstance(value, int) for value in hands)
        or any(value < 1 or value > 7 for value in hands)
        or tuple(sorted(set(hands))) != hands
    ):
        raise ValueError("hands_per_player must be unique increasing integers in [1, 7]")
    if config["range_weight_rule"] != "disjoint_linear_index":
        raise ValueError("range weight rule changed")
    if config["solver"] not in ("cfr", "lcfr", "cfr_plus", "dcfr"):
        raise ValueError("unsupported solver")
    for field in ("candidate_iterations", "timing_repeats", "warmup_repeats"):
        value = config[field]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field} must be a positive integer")
    for field in ("pot", "stack", "bet_size", "maximum_exact_error"):
        value = float(config[field])
        if not isfinite(value) or value <= 0.0:
            raise ValueError(f"{field} must be positive and finite")
    if float(config["bet_size"]) > float(config["stack"]):
        raise ValueError("bet size cannot exceed stack")
    digest = config["frozen_contract_sha256"]
    if not _CONTRACT_PATH.is_file():
        raise ValueError("frozen multiway contract is unavailable")
    actual_digest = hashlib.sha256(_CONTRACT_PATH.read_bytes()).hexdigest()
    if digest != actual_digest:
        raise ValueError("frozen multiway contract SHA-256 changed")
    return {
        **config,
        "board": board,
        "hands_per_player": hands,
        "pot": float(config["pot"]),
        "stack": float(config["stack"]),
        "bet_size": float(config["bet_size"]),
        "maximum_exact_error": float(config["maximum_exact_error"]),
    }


def _build_disjoint_game(config: dict[str, Any], hand_count: int) -> MultiwayRiverHoldem:
    board = parse_cards(*config["board"])
    available = tuple(card for card in range(52) if card not in set(board))
    required = 3 * hand_count * 2
    if required > len(available):
        raise ValueError("not enough disjoint private cards for calibration")
    cursor = 0
    ranges: list[dict[HoleCards, float]] = []
    for _ in range(3):
        weights: dict[HoleCards, float] = {}
        for index in range(hand_count):
            hand = tuple(sorted((available[cursor], available[cursor + 1])))
            cursor += 2
            weights[hand] = float(index + 1)
        ranges.append(weights)
    return MultiwayRiverHoldem.from_independent_ranges(
        board=board,
        pot=config["pot"],
        stacks=(config["stack"],) * 3,
        bet_size=config["bet_size"],
        player_weights=tuple(ranges),
    )


def _timed(
    operation: Callable[[], _T],
    *,
    repeats: int,
    warmups: int,
) -> tuple[float, float, _T]:
    result: _T
    for _ in range(warmups):
        result = operation()
    milliseconds = []
    for _ in range(repeats):
        start = time.perf_counter()
        result = operation()
        milliseconds.append((time.perf_counter() - start) * 1000.0)
    return median(milliseconds), min(milliseconds), result


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
    first: tuple[dict[str, Action], ...],
    second: tuple[dict[str, Action], ...],
) -> int:
    return sum(
        first[player].get(key) != action
        for player, actions in enumerate(second)
        for key, action in actions.items()
    )


def run_multiway_river_calibration(config: dict[str, Any]) -> dict[str, Any]:
    """Measure exact reference costs without making a strategy-selection claim."""

    parsed = _parse_config(config)
    experiment_start = time.perf_counter()
    rows: list[dict[str, Any]] = []
    maximum_error = 0.0
    action_mismatches = 0

    for hand_count in parsed["hands_per_player"]:
        game = _build_disjoint_game(parsed, hand_count)
        repeats = parsed["timing_repeats"]
        warmups = parsed["warmup_repeats"]

        full_uniform_ms, full_uniform_min_ms, uniform = _timed(
            lambda: evaluate_profile(game, {}),
            repeats=repeats,
            warmups=warmups,
        )
        coalition_ms, coalition_min_ms, coalition = _timed(
            lambda: evaluate_coalition_threats(game, {}),
            repeats=repeats,
            warmups=warmups,
        )

        def first_iteration() -> None:
            TabularCFR(game, variant=parsed["solver"]).run(1)

        iteration_ms, iteration_min_ms, _ = _timed(
            first_iteration,
            repeats=repeats,
            warmups=warmups,
        )

        candidate_solver = TabularCFR(game, variant=parsed["solver"])
        candidate_solver.run(parsed["candidate_iterations"])
        candidate = candidate_solver.average_strategy()
        full_candidate_ms, full_candidate_min_ms, full_candidate = _timed(
            lambda: evaluate_profile(game, candidate),
            repeats=repeats,
            warmups=warmups,
        )

        compile_ms, compile_min_ms, tape = _timed(
            lambda: CompiledPolicyDeltaTape(game, {}),
            repeats=repeats,
            warmups=warmups,
        )
        hot_ms, hot_min_ms, hot_candidate = _timed(
            lambda: tape.evaluate_policy(candidate, mode="dense"),
            repeats=repeats,
            warmups=warmups,
        )
        detailed = tape.recertify_policy(candidate, mode="dense")
        reference_actions = tuple(
            best_response(game, candidate, player)[1]
            for player in range(game.num_players)
        )
        row_error = max(
            _evaluation_error(tape.source_result.evaluation, uniform),
            _evaluation_error(hot_candidate, full_candidate),
            _evaluation_error(detailed.evaluation, full_candidate),
        )
        row_mismatches = _action_mismatches(
            detailed.best_response_actions,
            reference_actions,
        )
        maximum_error = max(maximum_error, row_error)
        action_mismatches += row_mismatches
        topology = tape.topology_summary()

        rows.append(
            {
                "hands_per_player": hand_count,
                "joint_deals": len(game.deals),
                "expected_cartesian_deals": hand_count**3,
                "information_sets": sum(
                    len(collect_information_sets(game, player))
                    for player in range(game.num_players)
                ),
                "compiled_tree_states": topology["compiled_tree_states"],
                "numeric_nodes": topology["numeric_nodes"],
                "dependency_edges": topology["dependency_edges"],
                "tape_runtime_bytes": topology["contiguous_runtime_bytes"],
                "uniform_normalized_nash_conv": uniform.nash_conv / game.payoff_span,
                "uniform_max_pair_coalition_gain_normalized": (
                    coalition.maximum_deviation_gain / game.payoff_span
                ),
                "full_unilateral_evaluation_median_ms": full_uniform_ms,
                "full_unilateral_evaluation_min_ms": full_uniform_min_ms,
                "all_pair_coalitions_median_ms": coalition_ms,
                "all_pair_coalitions_min_ms": coalition_min_ms,
                "first_solver_iteration_median_ms": iteration_ms,
                "first_solver_iteration_min_ms": iteration_min_ms,
                "full_candidate_evaluation_median_ms": full_candidate_ms,
                "full_candidate_evaluation_min_ms": full_candidate_min_ms,
                "policy_tape_compile_median_ms": compile_ms,
                "policy_tape_compile_min_ms": compile_min_ms,
                "hot_dense_candidate_evaluation_median_ms": hot_ms,
                "hot_dense_candidate_evaluation_min_ms": hot_min_ms,
                "hot_dense_speedup_over_full_candidate": full_candidate_ms / hot_ms,
                "maximum_exact_evaluation_error": row_error,
                "best_response_action_mismatches": row_mismatches,
                "dependencies_are_topological": topology["dependencies_are_topological"],
            }
        )

    gate_results = {
        "joint_deal_count_identity": all(
            row["joint_deals"] == row["expected_cartesian_deals"] for row in rows
        ),
        "exact_evaluation_identity": maximum_error <= parsed["maximum_exact_error"],
        "best_response_action_identity": action_mismatches == 0,
        "dependencies_are_topological": all(
            row["dependencies_are_topological"] for row in rows
        ),
    }
    return {
        "schema_version": 1,
        "experiment_type": "multiway_river_revealed_cost_calibration",
        "status": "revealed_engineering_calibration_only",
        "config": {
            **parsed,
            "board": list(parsed["board"]),
            "hands_per_player": list(parsed["hands_per_player"]),
        },
        "environment": environment_metadata(),
        "counts": {"rows": len(rows)},
        "aggregate": {
            "maximum_absolute_evaluation_error": maximum_error,
            "best_response_action_mismatches": action_mismatches,
            "minimum_hot_dense_speedup": min(
                row["hot_dense_speedup_over_full_candidate"] for row in rows
            ),
            "maximum_hot_dense_speedup": max(
                row["hot_dense_speedup_over_full_candidate"] for row in rows
            ),
        },
        "gates": {"results": gate_results, "passed": all(gate_results.values())},
        "timing": {"wall_seconds": time.perf_counter() - experiment_start},
        "rows": rows,
        "limitations": [
            "Ranges use disjoint private-card pools, so deal count is exactly cubic.",
            "Timing is a revealed hot-cache Python calibration, not a frozen strategy gate.",
            "Coalition responses are not compiled into the policy dependency tape.",
            "No online, six-player, or safety claim follows.",
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
    result = run_multiway_river_calibration(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "multiway river calibration: "
        f"rows={result['counts']['rows']}, "
        f"max_error={result['aggregate']['maximum_absolute_evaluation_error']:.3e}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
