"""Run the frozen exact public-tree quotient engineering audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from statistics import median
from typing import Any, Callable, TypeVar

from .dependency_tape import CompiledPolicyDeltaTape, DependencyTapeResult
from .evaluation import (
    EvaluationResult,
    Policy,
    best_response,
    collect_information_sets,
    evaluate_profile,
)
from .game import Action
from .multiway_river_context import (
    MULTIWAY_CONTEXT_FAMILIES,
    generate_multiway_river_contexts,
    group_split,
)
from .public_tree_tensor import PublicTreeTensorEvaluator, PublicTreeTensorResult
from .reporting import environment_metadata
from .river import HoleCards, parse_cards
from .river_multiway import MultiwayRiverHoldem

_T = TypeVar("_T")
_ROOT = Path(__file__).parents[2]
_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_multiway_game_sha256",
    "expected_evaluation_sha256",
    "expected_context_generator_sha256",
    "expected_dependency_tape_sha256",
    "expected_calibration_sha256",
    "disjoint_board",
    "pot",
    "stack",
    "bet_size",
    "disjoint_hands_per_player",
    "stress_hands_per_player",
    "stress_families",
    "stress_groups",
    "stress_splits",
    "stress_pot_options",
    "stress_bet_to_pot_options",
    "stress_effective_stack_to_pot",
    "stress_range_weight_options",
    "policy_families",
    "primary_timing_policy",
    "timing_repeats",
    "warmup_repeats",
    "gates",
}
_GATE_FIELDS = {
    "maximum_evaluation_error",
    "maximum_best_response_action_mismatches",
    "maximum_information_schema_mismatches",
    "require_deal_invariant_public_topology",
    "require_float64_contiguous_numeric_tensors",
    "maximum_largest_disjoint_persistent_byte_ratio_to_tape",
    "largest_disjoint_compile_strictly_faster_than_tape",
    "largest_disjoint_hot_strictly_faster_than_tape",
    "largest_disjoint_hot_strictly_faster_than_ordinary",
}
_SOURCE_PATHS = {
    "expected_multiway_game_sha256": _ROOT / "src" / "pontius" / "river_multiway.py",
    "expected_evaluation_sha256": _ROOT / "src" / "pontius" / "evaluation.py",
    "expected_context_generator_sha256": (
        _ROOT / "src" / "pontius" / "multiway_river_context.py"
    ),
    "expected_dependency_tape_sha256": (
        _ROOT / "src" / "pontius" / "dependency_tape.py"
    ),
    "expected_calibration_sha256": (
        _ROOT / "src" / "pontius" / "multiway_river_calibration.py"
    ),
}
_POLICY_FAMILIES = ("uniform", "hashed_dense", "hashed_pure")


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen source is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite_positive(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be finite and positive")
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be finite and positive") from error
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{label} must be finite and positive")
    return result


def parse_public_tree_quotient_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "public-tree quotient fields differ from ADR-0059: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    if config["evidence_stage"] != "revealed_engineering_audit":
        raise ValueError("public-tree quotient audit must remain revealed engineering")
    if config["seed"] != 20260819:
        raise ValueError("public-tree quotient seed differs from ADR-0059")
    for field, path in _SOURCE_PATHS.items():
        digest = config[field]
        if not isinstance(digest, str) or digest != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")

    if tuple(config["disjoint_board"]) != ("2c", "7d", "9h", "Js", "Qc"):
        raise ValueError("disjoint board differs from ADR-0059")
    numeric = {
        field: _finite_positive(config[field], field)
        for field in (
            "pot",
            "stack",
            "bet_size",
            "stress_effective_stack_to_pot",
        )
    }
    if (numeric["pot"], numeric["stack"], numeric["bet_size"]) != (
        12.0,
        30.0,
        3.0,
    ):
        raise ValueError("disjoint game economics differ from ADR-0059")
    if numeric["bet_size"] > numeric["stack"]:
        raise ValueError("bet size cannot exceed stack")
    if numeric["stress_effective_stack_to_pot"] != 2.5:
        raise ValueError("stress stack-to-pot differs from ADR-0059")

    frozen_sequences = {
        "disjoint_hands_per_player": (1, 2, 3, 4, 5, 6, 7),
        "stress_hands_per_player": (3, 5, 7),
        "stress_families": MULTIWAY_CONTEXT_FAMILIES,
        "stress_splits": ("development",),
        "stress_pot_options": (12.0,),
        "stress_bet_to_pot_options": (0.25,),
        "stress_range_weight_options": (1.0, 2.0, 4.0),
        "policy_families": _POLICY_FAMILIES,
    }
    parsed_sequences: dict[str, tuple[object, ...]] = {}
    for field, expected in frozen_sequences.items():
        values = tuple(config[field])
        if values != expected:
            raise ValueError(f"{field} differs from ADR-0059")
        parsed_sequences[field] = values
    if config["stress_groups"] != 1 or group_split(config["seed"], 0) != "development":
        raise ValueError("stress group zero must remain the sole development group")
    if config["primary_timing_policy"] != "hashed_dense":
        raise ValueError("primary timing policy differs from ADR-0059")
    if config["timing_repeats"] != 3 or config["warmup_repeats"] != 1:
        raise ValueError("timing schedule differs from ADR-0059")

    gates = config["gates"]
    if not isinstance(gates, dict) or set(gates) != _GATE_FIELDS:
        raise ValueError("public-tree quotient gates differ from ADR-0059")
    maximum_error = _finite_positive(
        gates["maximum_evaluation_error"],
        "maximum evaluation error",
    )
    if maximum_error > 1e-10:
        raise ValueError("exactness tolerance exceeds ADR-0059")
    byte_ratio = _finite_positive(
        gates["maximum_largest_disjoint_persistent_byte_ratio_to_tape"],
        "maximum persistent byte ratio",
    )
    if byte_ratio != 0.05:
        raise ValueError("persistent-byte gate differs from ADR-0059")
    for field in (
        "maximum_best_response_action_mismatches",
        "maximum_information_schema_mismatches",
    ):
        if isinstance(gates[field], bool) or gates[field] != 0:
            raise ValueError(f"{field} must remain zero")
    boolean_gates = _GATE_FIELDS - {
        "maximum_evaluation_error",
        "maximum_best_response_action_mismatches",
        "maximum_information_schema_mismatches",
        "maximum_largest_disjoint_persistent_byte_ratio_to_tape",
    }
    if any(gates[field] is not True for field in boolean_gates):
        raise ValueError("all ADR-0059 boolean gates must remain true")

    return {
        **config,
        **numeric,
        **parsed_sequences,
        "disjoint_board": tuple(config["disjoint_board"]),
        "gates": {
            **gates,
            "maximum_evaluation_error": maximum_error,
            "maximum_largest_disjoint_persistent_byte_ratio_to_tape": byte_ratio,
        },
    }


def _build_disjoint_game(config: dict[str, Any], hand_count: int) -> MultiwayRiverHoldem:
    board = parse_cards(*config["disjoint_board"])
    available = tuple(card for card in range(52) if card not in set(board))
    cursor = 0
    ranges: list[dict[HoleCards, float]] = []
    for _ in range(3):
        weights = {}
        for hand_index in range(hand_count):
            hand = tuple(sorted((available[cursor], available[cursor + 1])))
            cursor += 2
            weights[hand] = float(hand_index + 1)
        ranges.append(weights)
    return MultiwayRiverHoldem.from_independent_ranges(
        board=board,
        pot=config["pot"],
        stacks=(config["stack"],) * 3,
        bet_size=config["bet_size"],
        player_weights=tuple(ranges),
    )


def _ordinary_schema(game: MultiwayRiverHoldem) -> dict[str, tuple[Action, ...]]:
    result = {}
    for player in range(game.num_players):
        player_schema = collect_information_sets(game, player)
        overlap = set(result) & set(player_schema)
        if overlap:
            raise ValueError(f"information keys overlap across players: {sorted(overlap)!r}")
        result.update(player_schema)
    return dict(sorted(result.items()))


def _hashed_policy(
    schema: dict[str, tuple[Action, ...]],
    *,
    seed: int,
    pure: bool,
) -> Policy:
    result: Policy = {}
    for key, actions in schema.items():
        scores = tuple(
            int.from_bytes(
                hashlib.sha256(
                    f"{seed}|{key}|{action!r}".encode("utf-8")
                ).digest()[:8],
                "big",
            )
            for action in actions
        )
        if pure:
            selected = max(range(len(actions)), key=scores.__getitem__)
            result[key] = {
                action: float(index == selected)
                for index, action in enumerate(actions)
            }
        else:
            weights = tuple(float(1 + score % 31) for score in scores)
            total = sum(weights)
            result[key] = {
                action: weight / total
                for action, weight in zip(actions, weights, strict=True)
            }
    return result


def _policies(
    schema: dict[str, tuple[Action, ...]],
    seed: int,
) -> dict[str, Policy]:
    return {
        "uniform": {},
        "hashed_dense": _hashed_policy(schema, seed=seed, pure=False),
        "hashed_pure": _hashed_policy(schema, seed=seed, pure=True),
    }


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


def _evaluation_values(evaluation: EvaluationResult) -> tuple[float, ...]:
    return (
        *evaluation.utilities,
        *evaluation.best_response_values,
        *evaluation.deviation_gains,
        evaluation.nash_conv,
    )


def _evaluation_error(first: EvaluationResult, second: EvaluationResult) -> float:
    return max(
        abs(left - right)
        for left, right in zip(
            _evaluation_values(first),
            _evaluation_values(second),
            strict=True,
        )
    )


def _action_mismatches(
    first: tuple[dict[str, Action], ...],
    second: tuple[dict[str, Action], ...],
) -> int:
    if len(first) != len(second):
        return sum(len(actions) for actions in first) + sum(
            len(actions) for actions in second
        )
    return sum(
        first[player].get(key) != second[player].get(key)
        for player in range(len(first))
        for key in set(first[player]) | set(second[player])
    )


def _schema_mismatches(
    first: dict[str, tuple[Action, ...]],
    second: dict[str, tuple[Action, ...]],
) -> int:
    return sum(
        first.get(key) != second.get(key)
        for key in set(first) | set(second)
    )


def _reference_actions(
    game: MultiwayRiverHoldem,
    policy: Policy,
) -> tuple[dict[str, Action], ...]:
    return tuple(
        best_response(game, policy, player)[1]
        for player in range(game.num_players)
    )


def _tape_result(
    tape: CompiledPolicyDeltaTape,
    name: str,
    policy: Policy,
) -> DependencyTapeResult:
    if name == "uniform":
        return tape.source_result
    return tape.recertify_policy(policy, mode="dense")


def _game_rows(config: dict[str, Any]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for hand_count in config["disjoint_hands_per_player"]:
        rows.append(
            {
                "slice": "disjoint",
                "family": "disjoint_linear_index",
                "hands_per_player": hand_count,
                "game": _build_disjoint_game(config, hand_count),
            }
        )
    for hand_count in config["stress_hands_per_player"]:
        contexts = generate_multiway_river_contexts(
            groups=config["stress_groups"],
            seed=config["seed"],
            hands_per_player=hand_count,
            families=config["stress_families"],
            splits=config["stress_splits"],
            pot_options=config["stress_pot_options"],
            bet_to_pot_options=config["stress_bet_to_pot_options"],
            effective_stack_to_pot=config["stress_effective_stack_to_pot"],
            weight_options=config["stress_range_weight_options"],
        )
        if len(contexts) != 4:
            raise ValueError("ADR-0059 requires four stress families per support")
        for context in contexts:
            rows.append(
                {
                    "slice": "stress",
                    "family": context.family,
                    "hands_per_player": hand_count,
                    "context_id": context.context_id,
                    "game": context.game,
                }
            )
    return rows


def run_public_tree_quotient_audit(config: dict[str, Any]) -> dict[str, Any]:
    """Execute the exact frozen ADR-0059 workload."""

    parsed = parse_public_tree_quotient_config(config)
    started = time.perf_counter()
    rows = []
    maximum_error = 0.0
    quotient_action_mismatches = 0
    tape_action_mismatches = 0
    schema_mismatches = 0
    topology_mismatches = 0
    layout_failures = 0

    for row_spec in _game_rows(parsed):
        game = row_spec["game"]
        assert isinstance(game, MultiwayRiverHoldem)
        repeats = parsed["timing_repeats"]
        warmups = parsed["warmup_repeats"]

        quotient_compile_ms, quotient_compile_min_ms, quotient = _timed(
            lambda: PublicTreeTensorEvaluator(game),
            repeats=repeats,
            warmups=warmups,
        )
        tape_compile_ms, tape_compile_min_ms, tape = _timed(
            lambda: CompiledPolicyDeltaTape(game, {}),
            repeats=repeats,
            warmups=warmups,
        )
        ordinary_schema = _ordinary_schema(game)
        row_schema_mismatches = _schema_mismatches(
            ordinary_schema,
            quotient.information_schema(),
        ) + _schema_mismatches(ordinary_schema, tape.policy_input_schema)
        schema_mismatches += row_schema_mismatches

        policies = _policies(ordinary_schema, parsed["seed"])
        policy_rows = []
        row_maximum_error = 0.0
        row_quotient_action_mismatches = 0
        row_tape_action_mismatches = 0
        for policy_name in parsed["policy_families"]:
            policy = policies[policy_name]
            ordinary = evaluate_profile(game, policy)
            reference_actions = _reference_actions(game, policy)
            quotient_result = quotient.evaluate(policy)
            tape_result = _tape_result(tape, policy_name, policy)
            quotient_error = _evaluation_error(
                quotient_result.evaluation,
                ordinary,
            )
            tape_error = _evaluation_error(tape_result.evaluation, ordinary)
            quotient_mismatches = _action_mismatches(
                quotient_result.best_response_actions,
                reference_actions,
            )
            tape_mismatches = _action_mismatches(
                tape_result.best_response_actions,
                reference_actions,
            )
            row_maximum_error = max(
                row_maximum_error,
                quotient_error,
                tape_error,
            )
            row_quotient_action_mismatches += quotient_mismatches
            row_tape_action_mismatches += tape_mismatches
            policy_rows.append(
                {
                    "policy": policy_name,
                    "quotient_evaluation_error": quotient_error,
                    "tape_evaluation_error": tape_error,
                    "quotient_best_response_action_mismatches": quotient_mismatches,
                    "tape_best_response_action_mismatches": tape_mismatches,
                    "ordinary_nash_conv": ordinary.nash_conv,
                }
            )

        primary_policy = policies[parsed["primary_timing_policy"]]
        ordinary_ms, ordinary_min_ms, _ = _timed(
            lambda: evaluate_profile(game, primary_policy),
            repeats=repeats,
            warmups=warmups,
        )
        tape_ms, tape_min_ms, timed_tape = _timed(
            lambda: tape.recertify_policy(primary_policy, mode="dense"),
            repeats=repeats,
            warmups=warmups,
        )
        quotient_ms, quotient_min_ms, timed_quotient = _timed(
            lambda: quotient.evaluate(primary_policy),
            repeats=repeats,
            warmups=warmups,
        )
        timed_error = _evaluation_error(
            timed_quotient.evaluation,
            timed_tape.evaluation,
        )
        row_maximum_error = max(row_maximum_error, timed_error)
        row_topology_mismatches = quotient.topology_mismatch_count()
        row_layout_failure = int(
            not quotient.numeric_tensors_are_float64_contiguous()
            or not quotient.policy_tensors_are_float64_contiguous(primary_policy)
        )
        memory = quotient.memory_summary()
        tape_topology = tape.topology_summary()
        tape_bytes = int(tape_topology["contiguous_runtime_bytes"])
        persistent_byte_ratio = memory["persistent_numeric_bytes"] / tape_bytes

        maximum_error = max(maximum_error, row_maximum_error)
        quotient_action_mismatches += row_quotient_action_mismatches
        tape_action_mismatches += row_tape_action_mismatches
        topology_mismatches += row_topology_mismatches
        layout_failures += row_layout_failure
        rows.append(
            {
                **{key: value for key, value in row_spec.items() if key != "game"},
                "joint_deals": len(game.deals),
                "expected_disjoint_joint_deals": (
                    int(row_spec["hands_per_player"]) ** 3
                    if row_spec["slice"] == "disjoint"
                    else None
                ),
                "ordinary_information_sets": len(ordinary_schema),
                "information_schema_mismatches": row_schema_mismatches,
                "public_topology_mismatched_deals": row_topology_mismatches,
                "numeric_layout_failures": row_layout_failure,
                "maximum_evaluation_error": row_maximum_error,
                "quotient_best_response_action_mismatches": (
                    row_quotient_action_mismatches
                ),
                "tape_best_response_action_mismatches": row_tape_action_mismatches,
                "quotient_topology": quotient.topology_summary(),
                "tape_topology": tape_topology,
                "memory": {
                    **memory,
                    "tape_contiguous_runtime_bytes": tape_bytes,
                    "quotient_persistent_byte_ratio_to_tape": persistent_byte_ratio,
                },
                "timing": {
                    "ordinary_profile_median_ms": ordinary_ms,
                    "ordinary_profile_min_ms": ordinary_min_ms,
                    "tape_compile_median_ms": tape_compile_ms,
                    "tape_compile_min_ms": tape_compile_min_ms,
                    "tape_hot_dense_median_ms": tape_ms,
                    "tape_hot_dense_min_ms": tape_min_ms,
                    "quotient_compile_median_ms": quotient_compile_ms,
                    "quotient_compile_min_ms": quotient_compile_min_ms,
                    "quotient_hot_median_ms": quotient_ms,
                    "quotient_hot_min_ms": quotient_min_ms,
                    "quotient_compile_speedup_over_tape": (
                        tape_compile_ms / quotient_compile_ms
                    ),
                    "quotient_hot_speedup_over_tape": tape_ms / quotient_ms,
                    "quotient_hot_speedup_over_ordinary": ordinary_ms / quotient_ms,
                },
                "policies": policy_rows,
            }
        )

    if len(rows) != 19:
        raise AssertionError("ADR-0059 must produce exactly nineteen game rows")
    largest = next(
        row
        for row in rows
        if row["slice"] == "disjoint" and row["hands_per_player"] == 7
    )
    largest_memory = largest["memory"]
    largest_timing = largest["timing"]
    assert isinstance(largest_memory, dict) and isinstance(largest_timing, dict)
    gates = parsed["gates"]
    gate_results = {
        "maximum_evaluation_error": (
            maximum_error <= gates["maximum_evaluation_error"]
        ),
        "maximum_best_response_action_mismatches": (
            quotient_action_mismatches
            <= gates["maximum_best_response_action_mismatches"]
        ),
        "maximum_information_schema_mismatches": (
            schema_mismatches <= gates["maximum_information_schema_mismatches"]
        ),
        "deal_invariant_public_topology": (
            topology_mismatches == 0
            and gates["require_deal_invariant_public_topology"]
        ),
        "float64_contiguous_numeric_tensors": (
            layout_failures == 0
            and gates["require_float64_contiguous_numeric_tensors"]
        ),
        "largest_disjoint_persistent_byte_ratio_to_tape": (
            largest_memory["quotient_persistent_byte_ratio_to_tape"]
            <= gates["maximum_largest_disjoint_persistent_byte_ratio_to_tape"]
        ),
        "largest_disjoint_compile_strictly_faster_than_tape": (
            largest_timing["quotient_compile_median_ms"]
            < largest_timing["tape_compile_median_ms"]
        ),
        "largest_disjoint_hot_strictly_faster_than_tape": (
            largest_timing["quotient_hot_median_ms"]
            < largest_timing["tape_hot_dense_median_ms"]
        ),
        "largest_disjoint_hot_strictly_faster_than_ordinary": (
            largest_timing["quotient_hot_median_ms"]
            < largest_timing["ordinary_profile_median_ms"]
        ),
        "disjoint_joint_deal_count_identity": all(
            row["joint_deals"] == row["expected_disjoint_joint_deals"]
            for row in rows
            if row["slice"] == "disjoint"
        ),
        "tape_control_action_identity": tape_action_mismatches == 0,
    }

    return {
        "schema_version": 1,
        "experiment_type": "exact_multiway_public_tree_quotient_audit",
        "status": "revealed_engineering_audit_only",
        "config": parsed,
        "config_sha256": _sha256(
            _ROOT
            / "experiments"
            / "configs"
            / "multiway-public-tree-quotient-audit-v1.json"
        ),
        "environment": environment_metadata(),
        "counts": {
            "game_rows": len(rows),
            "policy_evaluations": len(rows) * len(parsed["policy_families"]),
            "disjoint_rows": sum(row["slice"] == "disjoint" for row in rows),
            "stress_rows": sum(row["slice"] == "stress" for row in rows),
        },
        "aggregate": {
            "maximum_absolute_evaluation_error": maximum_error,
            "quotient_best_response_action_mismatches": quotient_action_mismatches,
            "tape_best_response_action_mismatches": tape_action_mismatches,
            "information_schema_mismatches": schema_mismatches,
            "public_topology_mismatched_deals": topology_mismatches,
            "numeric_layout_failures": layout_failures,
            "largest_disjoint": {
                "joint_deals": largest["joint_deals"],
                "persistent_byte_ratio_to_tape": largest_memory[
                    "quotient_persistent_byte_ratio_to_tape"
                ],
                "compile_speedup_over_tape": largest_timing[
                    "quotient_compile_speedup_over_tape"
                ],
                "hot_speedup_over_tape": largest_timing[
                    "quotient_hot_speedup_over_tape"
                ],
                "hot_speedup_over_ordinary": largest_timing[
                    "quotient_hot_speedup_over_ordinary"
                ],
            },
        },
        "gates": {"results": gate_results, "passed": all(gate_results.values())},
        "timing": {"wall_seconds": time.perf_counter() - started},
        "rows": rows,
        "limitations": [
            "The joint deal axis remains explicit; no belief factorization occurred.",
            "This is a Python/NumPy river audit, not a native six-player benchmark.",
            "Only unilateral best responses are quotiented; pair coalitions remain offline.",
            "All contexts are revealed development engineering data.",
            "Persistent numeric bytes exclude Python object and allocator overhead.",
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
    result = run_public_tree_quotient_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "public-tree quotient audit: "
        f"rows={result['counts']['game_rows']}, "
        f"max_error={result['aggregate']['maximum_absolute_evaluation_error']:.3e}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
