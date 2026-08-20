"""Run the frozen exact structured-showdown automaton audit."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
from pathlib import Path
import time
from typing import Any

import numpy as np

from .factorized_belief import FactorizedCardBelief
from .factorized_belief_audit import _derived_seed, _raw_factors, generate_hand_axes
from .public_policy_tt import representative_public_tree
from .reporting import environment_metadata
from .river import HoleCards, parse_cards
from .showdown_value_rank_screen import (
    _payoff_operator,
    _rank_codes,
    _terminal_groups,
)
from .structured_showdown_automaton import (
    StructuredShowdownAutomaton,
    build_structured_showdown_automaton,
)

_ROOT = Path(__file__).parents[2]
_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_river_sha256",
    "expected_multiway_game_sha256",
    "expected_public_tree_tensor_sha256",
    "expected_factorized_audit_sha256",
    "expected_public_policy_tt_sha256",
    "expected_rank_screen_sha256",
    "expected_tensor_train_sha256",
    "expected_tensor_train_algebra_sha256",
    "board",
    "pot",
    "stack",
    "bet_size",
    "players",
    "hands_per_player",
    "dense_control_hands",
    "wide_hands",
    "range_families",
    "expected_terminal_groups",
    "target_players",
    "axis_orders",
    "permutation_control_cases",
    "state_rule",
    "transition_rule",
    "winner_rule",
    "sunk_rule",
    "storage_rule",
    "dense_export_rule",
    "strength_order_rule",
    "wide_sample_assignments",
    "gates",
}
_GATE_FIELDS = {
    "maximum_dense_operator_error",
    "maximum_dense_tt_export_error",
    "maximum_dense_zero_sum_error",
    "maximum_permutation_relative_singular_value_error",
    "maximum_wide_sample_zero_sum_error",
    "maximum_wide_sparse_bytes_per_operator",
    "maximum_wide_all_automata_bytes",
    "maximum_state_transition_mismatches",
    "require_no_svd_or_cartesian_builder_allocation",
    "require_strength_sorted_transition_runs_nonincreasing",
    "require_all_groups_and_target_players",
    "require_deterministic_rebuild_identity",
}
_SOURCE_PATHS = {
    "expected_river_sha256": _ROOT / "src" / "pontius" / "river.py",
    "expected_multiway_game_sha256": _ROOT / "src" / "pontius" / "river_multiway.py",
    "expected_public_tree_tensor_sha256": (
        _ROOT / "src" / "pontius" / "public_tree_tensor.py"
    ),
    "expected_factorized_audit_sha256": (
        _ROOT / "src" / "pontius" / "factorized_belief_audit.py"
    ),
    "expected_public_policy_tt_sha256": (
        _ROOT / "src" / "pontius" / "public_policy_tt.py"
    ),
    "expected_rank_screen_sha256": (
        _ROOT / "src" / "pontius" / "showdown_value_rank_screen.py"
    ),
    "expected_tensor_train_sha256": _ROOT / "src" / "pontius" / "tensor_train.py",
    "expected_tensor_train_algebra_sha256": (
        _ROOT / "src" / "pontius" / "tensor_train_algebra.py"
    ),
}
_FAMILIES = ("balanced", "blocker_heavy")
_ORDERS = ("generated", "within_axis_strength_sorted")
_PERMUTATION_CASES = (
    ("all_check", 0),
    ("contenders_0", 0),
    ("contenders_0_5", 0),
    ("contenders_0_2_5", 2),
    ("contenders_0_1_2_3_4_5", 4),
    ("contenders_1_3_5", 0),
)


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen source is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite_nonnegative(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be finite and nonnegative")
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be finite and nonnegative") from error
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return result


def parse_structured_showdown_config(config: dict[str, Any]) -> dict[str, Any]:
    """Strictly parse the preregistered ADR-0071 configuration."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "structured-showdown fields differ from ADR-0071: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    if config["evidence_stage"] != "preregistered_revealed_engineering_audit":
        raise ValueError("structured-showdown audit must remain preregistered revealed")
    if config["seed"] != 20260819:
        raise ValueError("structured-showdown seed differs from ADR-0071")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")

    frozen_sequences = {
        "board": ("2c", "7d", "9h", "Js", "Qc"),
        "hands_per_player": (4, 7, 32),
        "dense_control_hands": (4, 7),
        "range_families": _FAMILIES,
        "target_players": (0, 1, 2, 3, 4, 5),
        "axis_orders": _ORDERS,
    }
    parsed_sequences: dict[str, tuple[object, ...]] = {}
    for field, expected in frozen_sequences.items():
        values = tuple(config[field])
        if values != expected:
            raise ValueError(f"{field} differs from ADR-0071")
        parsed_sequences[field] = values

    supplied_cases = config["permutation_control_cases"]
    if not isinstance(supplied_cases, list) or any(
        not isinstance(case, dict) or set(case) != {"terminal_group", "player"}
        for case in supplied_cases
    ):
        raise ValueError("permutation controls differ from ADR-0071")
    permutation_cases = tuple(
        (case["terminal_group"], case["player"]) for case in supplied_cases
    )
    if permutation_cases != _PERMUTATION_CASES:
        raise ValueError("permutation controls differ from ADR-0071")

    frozen_scalars = {
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "wide_hands": 32,
        "expected_terminal_groups": 64,
        "state_rule": (
            "empty_or_running_maximum_strength_maximum_multiplicity_"
            "target_in_argmax"
        ),
        "transition_rule": (
            "deterministic_one_next_state_per_previous_state_and_hand"
        ),
        "winner_rule": (
            "final_pot_times_target_in_argmax_divided_by_maximum_multiplicity"
        ),
        "sunk_rule": "separate_exact_rank_one_constant_tensor",
        "storage_rule": (
            "int32_sparse_transition_tables_and_float64_terminal_weights"
        ),
        "dense_export_rule": (
            "direct_one_hot_tt_cores_without_svd_dense_cartesian_or_rounding"
        ),
        "strength_order_rule": "stable_per_seat_sort_by_strength_then_hole_cards",
        "wide_sample_assignments": 4096,
    }
    if any(config[field] != value for field, value in frozen_scalars.items()):
        raise ValueError("structured-showdown execution contract differs from ADR-0071")

    gates = config["gates"]
    if not isinstance(gates, dict) or set(gates) != _GATE_FIELDS:
        raise ValueError("structured-showdown gates differ from ADR-0071")
    parsed_gates = dict(gates)
    frozen_tolerances = {
        "maximum_dense_operator_error": 1e-12,
        "maximum_dense_tt_export_error": 1e-12,
        "maximum_dense_zero_sum_error": 1e-12,
        "maximum_permutation_relative_singular_value_error": 1e-12,
        "maximum_wide_sample_zero_sum_error": 1e-12,
    }
    for field, expected in frozen_tolerances.items():
        parsed_gates[field] = _finite_nonnegative(gates[field], field)
        if parsed_gates[field] != expected:
            raise ValueError(f"{field} differs from ADR-0071")
    frozen_integers = {
        "maximum_wide_sparse_bytes_per_operator": 9_000_000,
        "maximum_wide_all_automata_bytes": 536_870_912,
        "maximum_state_transition_mismatches": 0,
    }
    for field, expected in frozen_integers.items():
        if isinstance(gates[field], bool) or gates[field] != expected:
            raise ValueError(f"{field} differs from ADR-0071")
    for field in (
        "require_no_svd_or_cartesian_builder_allocation",
        "require_strength_sorted_transition_runs_nonincreasing",
        "require_all_groups_and_target_players",
        "require_deterministic_rebuild_identity",
    ):
        if gates[field] is not True:
            raise ValueError(f"{field} must remain true")
    return {
        **config,
        **parsed_sequences,
        **frozen_scalars,
        "permutation_control_cases": permutation_cases,
        "gates": parsed_gates,
    }


def _strength_sorted_axes(
    axes: tuple[tuple[HoleCards, ...], ...],
    rank_codes: np.ndarray,
) -> tuple[tuple[np.ndarray, ...], tuple[np.ndarray, ...]]:
    permutations = tuple(
        np.asarray(
            sorted(
                range(len(hands)),
                key=lambda index: (int(rank_codes[player, index]), hands[index]),
            ),
            dtype=np.int32,
        )
        for player, hands in enumerate(axes)
    )
    strengths = tuple(
        np.ascontiguousarray(rank_codes[player, permutation], dtype=np.int32)
        for player, permutation in enumerate(permutations)
    )
    return strengths, permutations


def _permute_tensor(
    tensor: np.ndarray,
    permutations: tuple[np.ndarray, ...],
) -> np.ndarray:
    result = tensor
    for mode, permutation in enumerate(permutations):
        result = np.take(result, permutation, axis=mode)
    return np.ascontiguousarray(result, dtype=np.float64)


def _relative_spectrum_error(first: np.ndarray, second: np.ndarray) -> float:
    if first.shape != second.shape:
        raise ValueError("permutation spectrum tensors must have equal shape")
    maximum = 0.0
    for split in range(1, first.ndim):
        left = np.linalg.svd(
            first.reshape(math.prod(first.shape[:split]), -1),
            compute_uv=False,
        )
        right = np.linalg.svd(
            second.reshape(math.prod(second.shape[:split]), -1),
            compute_uv=False,
        )
        denominator = max(1.0, float(left[0]) if len(left) else 0.0)
        maximum = max(maximum, float(np.max(np.abs(left - right))) / denominator)
    return maximum


def _sample_assignments(
    *,
    hand_count: int,
    players: int,
    count: int,
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    result = rng.integers(
        0,
        hand_count,
        size=(count, players),
        dtype=np.int32,
    )
    result[0] = 0
    result[1] = hand_count - 1
    for index in range(2, min(count, 2 + hand_count)):
        result[index] = (index - 2) % hand_count
    return result


def _literal_assignment_payoffs(
    *,
    strength_codes: tuple[np.ndarray, ...],
    assignments: np.ndarray,
    contenders: tuple[int, ...],
    contributed: bool,
    pot: float,
    bet_size: float,
) -> np.ndarray:
    """Evaluate sampled showdowns directly, independently of the automaton state."""

    players = len(strength_codes)
    indices = np.ascontiguousarray(assignments, dtype=np.int32)
    if indices.ndim != 2 or indices.shape[1] != players:
        raise ValueError("literal assignments must have one column per player")
    selected = np.stack(
        [
            strength_codes[player][indices[:, player]]
            for player in range(players)
        ]
    )
    contender_indices = np.asarray(contenders, dtype=np.int32)
    contender_strengths = selected[contender_indices]
    maximum = np.max(contender_strengths, axis=0)
    winner_mask = contender_strengths == maximum
    winner_count = np.sum(winner_mask, axis=0)
    contributions = np.zeros(players, dtype=np.float64)
    if contributed:
        contributions[contender_indices] = bet_size
    final_pot = pot + float(np.sum(contributions))
    utilities = np.broadcast_to(
        -pot / players - contributions[:, None],
        (players, len(indices)),
    ).copy()
    for contender_slot, player in enumerate(contenders):
        utilities[player] += winner_mask[contender_slot] * (
            final_pot / winner_count
        )
    return np.ascontiguousarray(utilities, dtype=np.float64)


def _builder_source_contract() -> bool:
    source = inspect.getsource(build_structured_showdown_automaton)
    forbidden = (
        "linalg.svd",
        "from_dense",
        "round_tensor_train",
        "np.indices",
        "np.meshgrid",
    )
    return not any(token in source for token in forbidden)


def _build(
    *,
    strengths: tuple[np.ndarray, ...],
    group: object,
    player: int,
    parsed: dict[str, Any],
) -> tuple[StructuredShowdownAutomaton, float, bool]:
    started = time.perf_counter()
    automaton = build_structured_showdown_automaton(
        strength_codes=strengths,
        contenders=group.contenders,
        target_player=player,
        contributed=group.contributed,
        pot=parsed["pot"],
        bet_size=parsed["bet_size"],
    )
    build_ms = (time.perf_counter() - started) * 1000.0
    rebuilt = build_structured_showdown_automaton(
        strength_codes=strengths,
        contenders=group.contenders,
        target_player=player,
        contributed=group.contributed,
        pot=parsed["pot"],
        bet_size=parsed["bet_size"],
    )
    return automaton, build_ms, automaton.digest == rebuilt.digest


def run_structured_showdown_audit(config: dict[str, Any]) -> dict[str, Any]:
    """Execute the frozen ADR-0071 workload."""

    parsed = parse_structured_showdown_config(config)
    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    automaton_rows: list[dict[str, object]] = []
    zero_sum_rows: list[dict[str, object]] = []
    geometry_rows: list[dict[str, object]] = []
    permutation_rows: list[dict[str, object]] = []
    run_counts: dict[tuple[int, str, str, int, str], int] = {}
    group_keys_seen: set[str] = set()

    for hand_count in parsed["hands_per_player"]:
        for family in parsed["range_families"]:
            axis_seed = _derived_seed(
                parsed["seed"],
                "structured-showdown-axis",
                hand_count,
                family,
            )
            axes = generate_hand_axes(
                board=board,
                players=parsed["players"],
                hands_per_player=hand_count,
                family=family,
                seed=axis_seed,
            )
            mixture, unaries = _raw_factors(
                hands_by_player=axes,
                components=1,
                seed=axis_seed,
                family=family,
            )
            belief = FactorizedCardBelief(
                hands_by_player=axes,
                mixture_weights=mixture,
                unary_weights=unaries,
                board=board,
            )
            layout = representative_public_tree(
                belief,
                pot=parsed["pot"],
                stack=parsed["stack"],
                bet_size=parsed["bet_size"],
            )
            groups = _terminal_groups(layout)
            if len(groups) != parsed["expected_terminal_groups"]:
                raise ValueError("terminal group count differs from ADR-0071")
            group_by_key = {group.key: group for group in groups}
            group_keys_seen.update(group_by_key)
            generated_codes = _rank_codes(board, axes)
            sorted_strengths, permutations = _strength_sorted_axes(
                axes,
                generated_codes,
            )
            order_strengths = {
                "generated": tuple(
                    np.ascontiguousarray(generated_codes[player], dtype=np.int32)
                    for player in range(parsed["players"])
                ),
                "within_axis_strength_sorted": sorted_strengths,
            }
            sample_assignments = None
            if hand_count == parsed["wide_hands"]:
                sample_assignments = _sample_assignments(
                    hand_count=hand_count,
                    players=parsed["players"],
                    count=parsed["wide_sample_assignments"],
                    seed=_derived_seed(axis_seed, "wide-samples"),
                )

            for order in parsed["axis_orders"]:
                strengths = order_strengths[order]
                rank_matrix = np.ascontiguousarray(strengths, dtype=np.int32)
                geometry_bytes = 0
                maximum_operator_bytes = 0
                maximum_dense_export_bytes = 0
                maximum_state_rank = 1
                total_build_ms = 0.0
                contender_target_pairs: set[tuple[tuple[int, ...], int]] = set()
                winner_topology_bytes: dict[object, int] = {}
                for group in groups:
                    literal = None
                    if hand_count in parsed["dense_control_hands"]:
                        literal = _payoff_operator(
                            group=group,
                            rank_codes=rank_matrix,
                            pot=parsed["pot"],
                            bet_size=parsed["bet_size"],
                        )
                    group_values = []
                    for player in parsed["target_players"]:
                        automaton, build_ms, rebuild_identical = _build(
                            strengths=strengths,
                            group=group,
                            player=player,
                            parsed=parsed,
                        )
                        total_build_ms += build_ms
                        geometry_bytes += automaton.numeric_bytes
                        contender_target_pairs.add((group.contenders, player))
                        winner_key: object = (
                            (group.contenders, player)
                            if player in group.contenders
                            else "zero_winner"
                        )
                        winner_bytes = automaton.numeric_bytes - np.dtype(
                            np.float64
                        ).itemsize
                        previous_winner_bytes = winner_topology_bytes.setdefault(
                            winner_key,
                            winner_bytes,
                        )
                        if previous_winner_bytes != winner_bytes:
                            raise AssertionError(
                                "equivalent winner topology has inconsistent storage"
                            )
                        maximum_operator_bytes = max(
                            maximum_operator_bytes,
                            automaton.numeric_bytes,
                        )
                        maximum_dense_export_bytes = max(
                            maximum_dense_export_bytes,
                            automaton.dense_tt_export_bytes,
                        )
                        maximum_state_rank = max(
                            maximum_state_rank,
                            automaton.maximum_state_rank,
                        )
                        transition_mismatches = automaton.transition_mismatches(
                            strengths
                        )
                        dense_error = None
                        tt_error = None
                        actual_tt_bytes = None
                        if literal is not None:
                            dense_values = automaton.to_dense()
                            group_values.append(dense_values)
                            dense_error = float(
                                np.max(np.abs(dense_values - literal[player]))
                            )
                            train = automaton.to_tensor_train()
                            reconstructed = train.to_dense()
                            tt_error = float(
                                np.max(np.abs(reconstructed - literal[player]))
                            )
                            actual_tt_bytes = train.storage_bytes
                            if actual_tt_bytes != automaton.dense_tt_export_bytes:
                                raise AssertionError("direct TT byte estimate is not exact")
                        else:
                            assert sample_assignments is not None
                            group_values.append(
                                automaton.evaluate_assignments(sample_assignments)
                            )

                        key = (hand_count, family, group.key, player, order)
                        run_counts[key] = automaton.transition_run_count
                        automaton_rows.append(
                            {
                                "hands_per_player": hand_count,
                                "family": family,
                                "axis_order": order,
                                "terminal_group": group.key,
                                "player": player,
                                "target_is_contender": player in group.contenders,
                                "constant_winner_shortcut": (
                                    automaton.constant_winner_shortcut
                                ),
                                "state_ranks": automaton.state_ranks,
                                "maximum_state_rank": automaton.maximum_state_rank,
                                "transition_records": automaton.transition_records,
                                "transition_run_count": (
                                    automaton.transition_run_count
                                ),
                                "terminal_weight_run_count": (
                                    automaton.terminal_weight_run_count
                                ),
                                "runtime_numeric_bytes": (
                                    automaton.runtime_numeric_bytes
                                ),
                                "state_metadata_bytes": (
                                    automaton.state_metadata_bytes
                                ),
                                "sparse_numeric_bytes": automaton.numeric_bytes,
                                "dense_tt_export_bytes": (
                                    automaton.dense_tt_export_bytes
                                ),
                                "actual_dense_tt_bytes": actual_tt_bytes,
                                "build_ms": build_ms,
                                "deterministic_rebuild_identical": rebuild_identical,
                                "state_transition_mismatches": transition_mismatches,
                                "maximum_construction_array_ndim": (
                                    automaton.maximum_construction_array_ndim
                                ),
                                "maximum_construction_array_elements": (
                                    automaton.maximum_construction_array_elements
                                ),
                                "cartesian_elements": hand_count ** parsed["players"],
                                "dense_operator_error": dense_error,
                                "dense_tt_export_error": tt_error,
                            }
                        )

                    utilities = np.stack(group_values)
                    zero_sum_error = float(np.max(np.abs(np.sum(utilities, axis=0))))
                    literal_assignment_error = None
                    literal_player_errors = None
                    if hand_count == parsed["wide_hands"]:
                        assert sample_assignments is not None
                        literal = _literal_assignment_payoffs(
                            strength_codes=strengths,
                            assignments=sample_assignments,
                            contenders=group.contenders,
                            contributed=group.contributed,
                            pot=parsed["pot"],
                            bet_size=parsed["bet_size"],
                        )
                        literal_player_errors = tuple(
                            float(value)
                            for value in np.max(
                                np.abs(utilities - literal),
                                axis=1,
                            )
                        )
                        literal_assignment_error = max(literal_player_errors)
                    zero_sum_rows.append(
                        {
                            "hands_per_player": hand_count,
                            "family": family,
                            "axis_order": order,
                            "terminal_group": group.key,
                            "sampled": hand_count == parsed["wide_hands"],
                            "assignments": (
                                parsed["wide_sample_assignments"]
                                if hand_count == parsed["wide_hands"]
                                else hand_count ** parsed["players"]
                            ),
                            "zero_sum_error": zero_sum_error,
                            "literal_assignment_error": literal_assignment_error,
                            "literal_player_errors": literal_player_errors,
                        }
                    )
                scalar_bytes = (
                    len(groups)
                    * parsed["players"]
                    * 2
                    * np.dtype(np.float64).itemsize
                )
                geometry_rows.append(
                    {
                        "hands_per_player": hand_count,
                        "family": family,
                        "axis_order": order,
                        "automata": len(groups) * parsed["players"],
                        "all_automata_sparse_numeric_bytes": geometry_bytes,
                        "maximum_sparse_numeric_bytes_per_operator": (
                            maximum_operator_bytes
                        ),
                        "maximum_dense_tt_export_bytes": maximum_dense_export_bytes,
                        "maximum_state_rank": maximum_state_rank,
                        "total_build_ms": total_build_ms,
                        "distinct_contender_target_pairs": len(
                            contender_target_pairs
                        ),
                        "distinct_executable_winner_topologies": len(
                            winner_topology_bytes
                        ),
                        "winner_topology_reuse_ratio": (
                            len(groups)
                            * parsed["players"]
                            / len(winner_topology_bytes)
                        ),
                        "projected_shared_winner_numeric_bytes": (
                            sum(winner_topology_bytes.values()) + scalar_bytes
                        ),
                        "dense_operator_bytes": (
                            hand_count ** parsed["players"]
                            * np.dtype(np.float64).itemsize
                        ),
                    }
                )

            if hand_count in parsed["dense_control_hands"]:
                for group_key, player in parsed["permutation_control_cases"]:
                    group = group_by_key[group_key]
                    original = _payoff_operator(
                        group=group,
                        rank_codes=generated_codes,
                        pot=parsed["pot"],
                        bet_size=parsed["bet_size"],
                    )[player]
                    sorted_values = _payoff_operator(
                        group=group,
                        rank_codes=np.ascontiguousarray(sorted_strengths, dtype=np.int32),
                        pot=parsed["pot"],
                        bet_size=parsed["bet_size"],
                    )[player]
                    permuted = _permute_tensor(original, permutations)
                    permutation_rows.append(
                        {
                            "hands_per_player": hand_count,
                            "family": family,
                            "terminal_group": group_key,
                            "player": player,
                            "permuted_tensor_error": float(
                                np.max(np.abs(permuted - sorted_values))
                            ),
                            "relative_singular_value_error": (
                                _relative_spectrum_error(original, sorted_values)
                            ),
                        }
                    )

    expected_rows = (
        len(parsed["hands_per_player"])
        * len(parsed["range_families"])
        * len(parsed["axis_orders"])
        * parsed["expected_terminal_groups"]
        * parsed["players"]
    )
    expected_zero_rows = expected_rows // parsed["players"]
    expected_geometries = (
        len(parsed["hands_per_player"])
        * len(parsed["range_families"])
        * len(parsed["axis_orders"])
    )
    expected_permutations = (
        len(parsed["dense_control_hands"])
        * len(parsed["range_families"])
        * len(parsed["permutation_control_cases"])
    )
    if (
        len(automaton_rows) != expected_rows
        or len(zero_sum_rows) != expected_zero_rows
        or len(geometry_rows) != expected_geometries
        or len(permutation_rows) != expected_permutations
    ):
        raise AssertionError("structured-showdown row counts differ from ADR-0071")

    dense_rows = [
        row for row in automaton_rows if row["dense_operator_error"] is not None
    ]
    wide_rows = [
        row
        for row in automaton_rows
        if row["hands_per_player"] == parsed["wide_hands"]
    ]
    maximum_dense_error = max(float(row["dense_operator_error"]) for row in dense_rows)
    maximum_tt_error = max(float(row["dense_tt_export_error"]) for row in dense_rows)
    maximum_dense_zero = max(
        float(row["zero_sum_error"])
        for row in zero_sum_rows
        if not row["sampled"]
    )
    maximum_wide_zero = max(
        float(row["zero_sum_error"])
        for row in zero_sum_rows
        if row["sampled"]
    )
    maximum_wide_literal_assignment_error = max(
        float(row["literal_assignment_error"])
        for row in zero_sum_rows
        if row["sampled"]
    )
    maximum_spectrum_error = max(
        float(row["relative_singular_value_error"]) for row in permutation_rows
    )
    maximum_transition_mismatches = max(
        int(row["state_transition_mismatches"]) for row in automaton_rows
    )
    maximum_wide_operator_bytes = max(
        int(row["sparse_numeric_bytes"]) for row in wide_rows
    )
    maximum_wide_all_bytes = max(
        int(row["all_automata_sparse_numeric_bytes"])
        for row in geometry_rows
        if row["hands_per_player"] == parsed["wide_hands"]
    )
    builder_allocation_contract = bool(
        _builder_source_contract()
        and all(
            row["maximum_construction_array_ndim"] <= 2
            and row["maximum_construction_array_elements"] < row["cartesian_elements"]
            for row in automaton_rows
        )
    )
    sorted_run_violations = 0
    for hand_count in parsed["hands_per_player"]:
        for family in parsed["range_families"]:
            for group_key in group_keys_seen:
                for player in parsed["target_players"]:
                    generated = run_counts[
                        (hand_count, family, group_key, player, "generated")
                    ]
                    ordered = run_counts[
                        (
                            hand_count,
                            family,
                            group_key,
                            player,
                            "within_axis_strength_sorted",
                        )
                    ]
                    sorted_run_violations += int(ordered > generated)
    deterministic_identity = all(
        bool(row["deterministic_rebuild_identical"]) for row in automaton_rows
    )
    all_groups_targets = bool(
        len(group_keys_seen) == parsed["expected_terminal_groups"]
        and all(
            sum(
                row["hands_per_player"] == hand_count
                and row["family"] == family
                and row["axis_order"] == order
                and row["terminal_group"] == group_key
                for row in automaton_rows
            )
            == parsed["players"]
            for hand_count in parsed["hands_per_player"]
            for family in parsed["range_families"]
            for order in parsed["axis_orders"]
            for group_key in group_keys_seen
        )
    )
    gates = parsed["gates"]
    gate_results = {
        "dense_operator_identity": (
            maximum_dense_error <= gates["maximum_dense_operator_error"]
        ),
        "direct_dense_tt_export_identity": (
            maximum_tt_error <= gates["maximum_dense_tt_export_error"]
        ),
        "dense_zero_sum_identity": (
            maximum_dense_zero <= gates["maximum_dense_zero_sum_error"]
        ),
        "permutation_spectrum_invariant": (
            maximum_spectrum_error
            <= gates["maximum_permutation_relative_singular_value_error"]
        ),
        "wide_sample_zero_sum_identity": (
            maximum_wide_zero <= gates["maximum_wide_sample_zero_sum_error"]
        ),
        "wide_sparse_operator_storage": (
            maximum_wide_operator_bytes
            <= gates["maximum_wide_sparse_bytes_per_operator"]
        ),
        "wide_all_automata_storage": (
            maximum_wide_all_bytes <= gates["maximum_wide_all_automata_bytes"]
        ),
        "state_transition_identity": (
            maximum_transition_mismatches
            <= gates["maximum_state_transition_mismatches"]
        ),
        "no_svd_or_cartesian_builder_allocation": (
            builder_allocation_contract
            if gates["require_no_svd_or_cartesian_builder_allocation"]
            else True
        ),
        "strength_sorted_runs_nonincreasing": (
            sorted_run_violations == 0
            if gates["require_strength_sorted_transition_runs_nonincreasing"]
            else True
        ),
        "all_groups_and_target_players": (
            all_groups_targets
            if gates["require_all_groups_and_target_players"]
            else True
        ),
        "deterministic_rebuild_identity": (
            deterministic_identity
            if gates["require_deterministic_rebuild_identity"]
            else True
        ),
    }
    return {
        "schema_version": 1,
        "experiment_type": "exact_structured_showdown_automaton_audit",
        "status": "preregistered_revealed_engineering_audit_only",
        "config": parsed,
        "config_sha256": _sha256(
            _ROOT
            / "experiments"
            / "configs"
            / "structured-showdown-automaton-audit-v1.json"
        ),
        "implementation_sha256": _sha256(
            _ROOT / "src" / "pontius" / "structured_showdown_automaton.py"
        ),
        "environment": environment_metadata(),
        "counts": {
            "automaton_rows": len(automaton_rows),
            "zero_sum_rows": len(zero_sum_rows),
            "geometry_rows": len(geometry_rows),
            "permutation_rows": len(permutation_rows),
            "terminal_groups": len(group_keys_seen),
            "target_players": parsed["players"],
        },
        "aggregate": {
            "maximum_dense_operator_error": maximum_dense_error,
            "maximum_dense_tt_export_error": maximum_tt_error,
            "maximum_dense_zero_sum_error": maximum_dense_zero,
            "maximum_permutation_relative_singular_value_error": (
                maximum_spectrum_error
            ),
            "maximum_wide_sample_zero_sum_error": maximum_wide_zero,
            "maximum_wide_literal_assignment_error": (
                maximum_wide_literal_assignment_error
            ),
            "maximum_state_transition_mismatches": maximum_transition_mismatches,
            "maximum_wide_sparse_bytes_per_operator": maximum_wide_operator_bytes,
            "maximum_wide_all_automata_bytes": maximum_wide_all_bytes,
            "strength_sorted_run_violations": sorted_run_violations,
            "maximum_wide_state_rank": max(
                int(row["maximum_state_rank"]) for row in wide_rows
            ),
            "maximum_wide_dense_tt_export_bytes": max(
                int(row["dense_tt_export_bytes"]) for row in wide_rows
            ),
        },
        "added_diagnostics": {
            "wide_literal_assignment_identity_at_dense_tolerance": (
                maximum_wide_literal_assignment_error
                <= gates["maximum_dense_operator_error"]
            ),
            "wide_literal_assignment_check_is_a_postfreeze_diagnostic": True,
            "minimum_distinct_executable_winner_topologies": min(
                int(row["distinct_executable_winner_topologies"])
                for row in geometry_rows
            ),
            "maximum_winner_topology_reuse_ratio": max(
                float(row["winner_topology_reuse_ratio"])
                for row in geometry_rows
            ),
            "minimum_projected_shared_winner_storage_ratio": min(
                int(row["projected_shared_winner_numeric_bytes"])
                / int(row["all_automata_sparse_numeric_bytes"])
                for row in geometry_rows
            ),
        },
        "gates": {"results": gate_results, "passed": all(gate_results.values())},
        "timing": {"wall_seconds": time.perf_counter() - started},
        "geometry_rows": geometry_rows,
        "permutation_rows": permutation_rows,
        "zero_sum_rows": zero_sum_rows,
        "automaton_rows": automaton_rows,
        "limitations": [
            "Sparse exact terminal construction does not solve policy-induced root rank.",
            "Wide zero sum is sampled because a complete 32^6 tensor is prohibited.",
            "Dense direct-TT export is a small-axis oracle path, not the wide representation.",
            "Python construction timing is not a native contraction benchmark.",
            "Reachable automaton state rank is an exact upper representation, not minimal TT rank.",
            "The P/multiplicity terminal rule assumes equal stacks and this one-bet tree; side pots require contribution-class state.",
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
    result = run_structured_showdown_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "structured showdown: "
        f"operators={result['counts']['automaton_rows']}, "
        f"wide_max={result['aggregate']['maximum_wide_sparse_bytes_per_operator']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
