"""Run the frozen six-player showdown value-operator TT rank screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np

from .evaluation import EvaluationResult, Policy
from .factorized_belief import FactorizedCardBelief
from .factorized_belief_audit import (
    _derived_seed,
    _raw_factors,
    generate_hand_axes,
)
from .game import Action, TERMINAL_PLAYER
from .public_tree_tensor import PublicTreeTensorEvaluator, PublicTreeTensorResult
from .reporting import environment_metadata
from .river import BET, CALL, HoleCards, evaluate_seven, parse_cards
from .river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem
from .tensor_train import TensorTrain, tensor_errors, unfolding_numerical_ranks
from .terminal_tensor_evaluation import evaluate_with_terminal_values

_ROOT = Path(__file__).parents[2]
_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_river_sha256",
    "expected_multiway_game_sha256",
    "expected_public_tree_tensor_sha256",
    "expected_factorized_belief_sha256",
    "expected_factorized_audit_sha256",
    "board",
    "pot",
    "stack",
    "bet_size",
    "players",
    "strategic_hands_per_player",
    "spectral_hands_per_player",
    "range_families",
    "mixture_component_counts",
    "policy_families",
    "rank_caps",
    "exact_arm",
    "terminal_group_rule",
    "expected_terminal_groups",
    "operator_domain",
    "card_compatibility_location",
    "zero_sum_storage_rule",
    "numerical_rank_relative_threshold",
    "gates",
}
_GATE_FIELDS = {
    "maximum_exact_arm_operator_error",
    "maximum_exact_arm_strategic_error",
    "maximum_exact_arm_action_mismatches",
    "maximum_zero_sum_error",
    "maximum_safe_normalized_strategic_error",
    "maximum_safe_action_mismatches",
    "maximum_safe_operator_storage_ratio",
    "maximum_safe_rank_cap",
    "require_strategically_safe_compressed_arm",
}
_SOURCE_PATHS = {
    "expected_river_sha256": _ROOT / "src" / "pontius" / "river.py",
    "expected_multiway_game_sha256": (
        _ROOT / "src" / "pontius" / "river_multiway.py"
    ),
    "expected_public_tree_tensor_sha256": (
        _ROOT / "src" / "pontius" / "public_tree_tensor.py"
    ),
    "expected_factorized_belief_sha256": (
        _ROOT / "src" / "pontius" / "factorized_belief.py"
    ),
    "expected_factorized_audit_sha256": (
        _ROOT / "src" / "pontius" / "factorized_belief_audit.py"
    ),
}
_FAMILIES = ("balanced", "blocker_heavy")
_POLICIES = ("uniform", "hashed_dense", "hashed_pure")
_EXACT_ARM = "untruncated_tt_svd"


@dataclass(frozen=True, slots=True)
class _TerminalGroup:
    key: str
    contenders: tuple[int, ...]
    contributed: bool
    terminal_slots: tuple[int, ...]


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


def parse_showdown_value_rank_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "showdown-rank fields differ from ADR-0063: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    if config["evidence_stage"] != "revealed_engineering_screen":
        raise ValueError("showdown rank screen must remain revealed engineering")
    if config["seed"] != 20260819:
        raise ValueError("showdown rank seed differs from ADR-0063")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")

    frozen_sequences = {
        "board": ("2c", "7d", "9h", "Js", "Qc"),
        "spectral_hands_per_player": (4, 5),
        "range_families": _FAMILIES,
        "mixture_component_counts": (1, 3),
        "policy_families": _POLICIES,
        "rank_caps": (1, 2, 4, 8, 16, 32),
    }
    parsed_sequences = {}
    for field, expected in frozen_sequences.items():
        values = tuple(config[field])
        if values != expected:
            raise ValueError(f"{field} differs from ADR-0063")
        parsed_sequences[field] = values
    frozen_scalars = {
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "strategic_hands_per_player": 4,
        "exact_arm": _EXACT_ARM,
        "terminal_group_rule": "all_check_plus_nonempty_contender_set",
        "expected_terminal_groups": 64,
        "operator_domain": "full_cartesian_with_overlap_payoff_extension",
        "card_compatibility_location": "exact_factor_graph_outside_value_operator",
        "zero_sum_storage_rule": "store_first_five_derive_sixth",
        "numerical_rank_relative_threshold": 1e-12,
    }
    if any(config[field] != value for field, value in frozen_scalars.items()):
        raise ValueError("showdown value-operator contract differs from ADR-0063")

    gates = config["gates"]
    if not isinstance(gates, dict) or set(gates) != _GATE_FIELDS:
        raise ValueError("showdown value-operator gates differ from ADR-0063")
    parsed_gates = dict(gates)
    for field in (
        "maximum_exact_arm_operator_error",
        "maximum_exact_arm_strategic_error",
        "maximum_zero_sum_error",
        "maximum_safe_normalized_strategic_error",
        "maximum_safe_operator_storage_ratio",
    ):
        parsed_gates[field] = _finite_nonnegative(gates[field], field)
    if parsed_gates["maximum_exact_arm_operator_error"] > 1e-10:
        raise ValueError("exact operator tolerance exceeds ADR-0063")
    if parsed_gates["maximum_exact_arm_strategic_error"] > 1e-10:
        raise ValueError("exact strategic tolerance exceeds ADR-0063")
    if parsed_gates["maximum_zero_sum_error"] > 1e-10:
        raise ValueError("zero-sum tolerance exceeds ADR-0063")
    if parsed_gates["maximum_safe_normalized_strategic_error"] != 1e-4:
        raise ValueError("safe strategic tolerance differs from ADR-0063")
    if parsed_gates["maximum_safe_operator_storage_ratio"] != 0.25:
        raise ValueError("safe storage ratio differs from ADR-0063")
    for field in (
        "maximum_exact_arm_action_mismatches",
        "maximum_safe_action_mismatches",
    ):
        if isinstance(gates[field], bool) or gates[field] != 0:
            raise ValueError(f"{field} must remain zero")
    if gates["maximum_safe_rank_cap"] != 16:
        raise ValueError("maximum safe rank differs from ADR-0063")
    if gates["require_strategically_safe_compressed_arm"] is not True:
        raise ValueError("compressed-arm hypothesis must remain required")
    return {
        **config,
        **parsed_sequences,
        **frozen_scalars,
        "gates": parsed_gates,
    }


def _terminal_groups(layout: PublicTreeTensorEvaluator) -> tuple[_TerminalGroup, ...]:
    grouped: dict[tuple[str, tuple[int, ...]], list[int]] = defaultdict(list)
    for node in layout.nodes:
        if node.player != TERMINAL_PLAYER:
            continue
        bet_actions = tuple(
            (player, action) for player, action in node.history if action == BET
        )
        if not bet_actions:
            group_key = ("all_check", tuple(range(layout.num_players)))
        else:
            if len(bet_actions) != 1:
                raise ValueError("one-bet river terminal contains multiple bets")
            bettor = bet_actions[0][0]
            callers = tuple(
                player for player, action in node.history if action == CALL
            )
            group_key = ("contributed", tuple(sorted((bettor, *callers))))
        grouped[group_key].append(node.terminal_slot)
    groups = []
    for (kind, contenders), slots in sorted(grouped.items()):
        key = (
            "all_check"
            if kind == "all_check"
            else "contenders_" + "_".join(map(str, contenders))
        )
        groups.append(
            _TerminalGroup(
                key=key,
                contenders=contenders,
                contributed=kind == "contributed",
                terminal_slots=tuple(sorted(slots)),
            )
        )
    return tuple(groups)


def _rank_codes(
    board: tuple[int, ...],
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
) -> np.ndarray:
    ranks = tuple(
        tuple(evaluate_seven((*board, *hand)) for hand in hands)
        for hands in hands_by_player
    )
    ordered = tuple(sorted({rank for player_ranks in ranks for rank in player_ranks}))
    code = {rank: index for index, rank in enumerate(ordered)}
    return np.ascontiguousarray(
        [[code[rank] for rank in player_ranks] for player_ranks in ranks],
        dtype=np.int32,
    )


def _payoff_operator(
    *,
    group: _TerminalGroup,
    rank_codes: np.ndarray,
    pot: float,
    bet_size: float,
) -> np.ndarray:
    players, hand_count = rank_codes.shape
    shape = (hand_count,) * players
    grids = tuple(
        rank_codes[player].reshape(
            (1,) * player + (hand_count,) + (1,) * (players - player - 1)
        )
        for player in range(players)
    )
    contender_grids = tuple(grids[player] for player in group.contenders)
    maximum = contender_grids[0]
    for values in contender_grids[1:]:
        maximum = np.maximum(maximum, values)
    winner_count = np.zeros(shape, dtype=np.float64)
    for player in group.contenders:
        winner_count += grids[player] == maximum

    contributions = tuple(
        bet_size if group.contributed and player in group.contenders else 0.0
        for player in range(players)
    )
    final_pot = pot + sum(contributions)
    sunk_share = pot / players
    values = np.empty((players, *shape), dtype=np.float64, order="C")
    for player in range(players):
        base = -sunk_share - contributions[player]
        if player in group.contenders:
            values[player] = base + (grids[player] == maximum) * (
                final_pot / winner_count
            )
        else:
            values[player].fill(base)
    return values


def _operator_groups(
    *,
    groups: tuple[_TerminalGroup, ...],
    board: tuple[int, ...],
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    pot: float,
    bet_size: float,
) -> dict[str, np.ndarray]:
    ranks = _rank_codes(board, hands_by_player)
    return {
        group.key: _payoff_operator(
            group=group,
            rank_codes=ranks,
            pot=pot,
            bet_size=bet_size,
        )
        for group in groups
    }


def _arm_names(config: dict[str, Any]) -> tuple[str, ...]:
    return (
        *(f"rank_{rank}" for rank in config["rank_caps"]),
        config["exact_arm"],
    )


def _maximum_rank(arm: str) -> int | None:
    return None if arm == _EXACT_ARM else int(arm.removeprefix("rank_"))


def _decompose_operators(
    *,
    operators: dict[str, np.ndarray],
    arms: tuple[str, ...],
    numerical_rank_threshold: float,
    retain_reconstructions: bool,
) -> tuple[list[dict[str, object]], dict[str, dict[str, np.ndarray]]]:
    players = next(iter(operators.values())).shape[0]
    first = next(iter(operators.values()))
    dense_bytes = len(operators) * (players - 1) * first[0].nbytes
    rows = []
    retained: dict[str, dict[str, np.ndarray]] = {}
    numerical_ranks = [
        unfolding_numerical_ranks(
            values[player],
            relative_threshold=numerical_rank_threshold,
        )
        for values in operators.values()
        for player in range(players - 1)
    ]
    maximum_numerical_ranks = tuple(
        max(ranks[bond] for ranks in numerical_ranks)
        for bond in range(len(numerical_ranks[0]))
    )
    median_numerical_ranks = tuple(
        median(ranks[bond] for ranks in numerical_ranks)
        for bond in range(len(numerical_ranks[0]))
    )

    for arm in arms:
        maximum_rank = _maximum_rank(arm)
        storage_bytes = 0
        decomposition_ms = 0.0
        reconstruction_ms = 0.0
        maximum_absolute_error = 0.0
        sum_squared_error = 0.0
        sum_squared_reference = 0.0
        maximum_zero_sum_error = 0.0
        arm_reconstructions = {}
        maximum_actual_ranks = [1] * len(first.shape)
        for key, exact in operators.items():
            approximate = np.empty_like(exact)
            for player in range(players - 1):
                start = time.perf_counter()
                train = TensorTrain.from_dense(
                    exact[player],
                    maximum_rank=maximum_rank,
                )
                decomposition_ms += (time.perf_counter() - start) * 1000.0
                start = time.perf_counter()
                approximate[player] = train.to_dense()
                reconstruction_ms += (time.perf_counter() - start) * 1000.0
                storage_bytes += train.storage_bytes
                for bond, rank in enumerate(train.ranks):
                    maximum_actual_ranks[bond] = max(
                        maximum_actual_ranks[bond],
                        rank,
                    )
            approximate[-1] = -np.sum(approximate[:-1], axis=0)
            difference = exact - approximate
            maximum_absolute_error = max(
                maximum_absolute_error,
                float(np.max(np.abs(difference))),
            )
            sum_squared_error += float(np.sum(difference * difference))
            sum_squared_reference += float(np.sum(exact * exact))
            maximum_zero_sum_error = max(
                maximum_zero_sum_error,
                float(np.max(np.abs(np.sum(approximate, axis=0)))),
            )
            if retain_reconstructions:
                arm_reconstructions[key] = approximate
        if retain_reconstructions:
            retained[arm] = arm_reconstructions
        rows.append(
            {
                "arm": arm,
                "declared_rank_cap": maximum_rank,
                "maximum_actual_ranks": maximum_actual_ranks,
                "maximum_numerical_ranks": maximum_numerical_ranks,
                "median_numerical_ranks": median_numerical_ranks,
                "dense_first_five_operator_bytes": dense_bytes,
                "tt_storage_bytes": storage_bytes,
                "storage_ratio": storage_bytes / dense_bytes,
                "maximum_absolute_operator_error": maximum_absolute_error,
                "relative_frobenius_operator_error": math.sqrt(
                    sum_squared_error / sum_squared_reference
                ),
                "maximum_zero_sum_error": maximum_zero_sum_error,
                "decomposition_ms": decomposition_ms,
                "reconstruction_ms": reconstruction_ms,
            }
        )
    return rows, retained


def _game_from_belief(
    *,
    belief: FactorizedCardBelief,
    pot: float,
    stack: float,
    bet_size: float,
) -> MultiwayRiverHoldem:
    materialized = belief.materialize()
    joint = {
        MultiwayRiverDeal(
            tuple(
                belief.hands_by_player[player][assignment[player]]
                for player in range(belief.num_players)
            )
        ): float(probability)
        for assignment, probability in zip(
            materialized.assignments,
            materialized.probabilities,
            strict=True,
        )
    }
    return MultiwayRiverHoldem.from_joint_weights(
        board=belief.board,
        pot=pot,
        stacks=(stack,) * belief.num_players,
        bet_size=bet_size,
        joint_weights=joint,
    )


def _policies(
    schema: dict[str, tuple[Action, ...]],
    seed: int,
) -> dict[str, Policy]:
    dense: Policy = {}
    pure: Policy = {}
    for key, actions in schema.items():
        scores = tuple(
            int.from_bytes(
                hashlib.sha256(
                    f"{seed}|operator-policy|{key}|{action!r}".encode("utf-8")
                ).digest()[:8],
                "big",
            )
            for action in actions
        )
        weights = tuple(float(1 + score % 31) for score in scores)
        total = sum(weights)
        dense[key] = {
            action: weight / total
            for action, weight in zip(actions, weights, strict=True)
        }
        selected = max(range(len(actions)), key=scores.__getitem__)
        pure[key] = {
            action: float(index == selected)
            for index, action in enumerate(actions)
        }
    return {"uniform": {}, "hashed_dense": dense, "hashed_pure": pure}


def _deal_axis_indices(
    layout: PublicTreeTensorEvaluator,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
) -> np.ndarray:
    maps = tuple(
        {hand: index for index, hand in enumerate(hands)}
        for hands in hands_by_player
    )
    return np.ascontiguousarray(
        [
            [maps[player][deal.hand(player)] for player in range(layout.num_players)]
            for deal in layout.deals
        ],
        dtype=np.int32,
    )


def _terminal_tensor_for_layout(
    *,
    layout: PublicTreeTensorEvaluator,
    groups: tuple[_TerminalGroup, ...],
    reconstructed: dict[str, np.ndarray],
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
) -> np.ndarray:
    indices = _deal_axis_indices(layout, hands_by_player)
    gather = tuple(indices[:, player] for player in range(layout.num_players))
    terminal = np.empty_like(layout.terminal_values)
    for group in groups:
        values = reconstructed[group.key][(slice(None), *gather)].T
        for slot in group.terminal_slots:
            terminal[slot] = values
    return terminal


def _evaluation_values(result: EvaluationResult) -> tuple[float, ...]:
    return (
        *result.utilities,
        *result.best_response_values,
        *result.deviation_gains,
        result.nash_conv,
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
    return sum(
        first[player].get(key) != second[player].get(key)
        for player in range(len(first))
        for key in set(first[player]) | set(second[player])
    )


def run_showdown_value_rank_screen(config: dict[str, Any]) -> dict[str, Any]:
    """Execute the frozen ADR-0063 operator and root-strategy screen."""

    parsed = parse_showdown_value_rank_config(config)
    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    arms = _arm_names(parsed)
    spectral_rows = []
    strategic_rows = []
    retained_by_family: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    exact_operators_by_family: dict[str, dict[str, np.ndarray]] = {}
    groups_by_family: dict[str, tuple[_TerminalGroup, ...]] = {}
    maximum_literal_terminal_error = 0.0

    for hand_count in parsed["spectral_hands_per_player"]:
        for family in parsed["range_families"]:
            axis_seed = _derived_seed(parsed["seed"], "operator-axis", hand_count, family)
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
            control_belief = FactorizedCardBelief(
                hands_by_player=axes,
                mixture_weights=mixture,
                unary_weights=unaries,
                board=board,
            )
            control_layout = PublicTreeTensorEvaluator(
                _game_from_belief(
                    belief=control_belief,
                    pot=parsed["pot"],
                    stack=parsed["stack"],
                    bet_size=parsed["bet_size"],
                )
            )
            groups = _terminal_groups(control_layout)
            if len(groups) != parsed["expected_terminal_groups"]:
                raise ValueError("terminal payoff group count differs from ADR-0063")
            operators = _operator_groups(
                groups=groups,
                board=board,
                hands_by_player=axes,
                pot=parsed["pot"],
                bet_size=parsed["bet_size"],
            )
            rows, retained = _decompose_operators(
                operators=operators,
                arms=arms,
                numerical_rank_threshold=parsed[
                    "numerical_rank_relative_threshold"
                ],
                retain_reconstructions=(
                    hand_count == parsed["strategic_hands_per_player"]
                ),
            )
            for row in rows:
                spectral_rows.append(
                    {
                        "hands_per_player": hand_count,
                        "family": family,
                        "terminal_groups": len(groups),
                        **row,
                    }
                )
            if hand_count == parsed["strategic_hands_per_player"]:
                retained_by_family[family] = retained
                exact_operators_by_family[family] = operators
                groups_by_family[family] = groups

    for family in parsed["range_families"]:
        hand_count = parsed["strategic_hands_per_player"]
        axis_seed = _derived_seed(parsed["seed"], "operator-axis", hand_count, family)
        axes = generate_hand_axes(
            board=board,
            players=parsed["players"],
            hands_per_player=hand_count,
            family=family,
            seed=axis_seed,
        )
        groups = groups_by_family[family]
        exact_operators = exact_operators_by_family[family]
        for components in parsed["mixture_component_counts"]:
            mixture, unaries = _raw_factors(
                hands_by_player=axes,
                components=components,
                seed=axis_seed,
                family=family,
            )
            belief = FactorizedCardBelief(
                hands_by_player=axes,
                mixture_weights=mixture,
                unary_weights=unaries,
                board=board,
            )
            layout = PublicTreeTensorEvaluator(
                _game_from_belief(
                    belief=belief,
                    pot=parsed["pot"],
                    stack=parsed["stack"],
                    bet_size=parsed["bet_size"],
                )
            )
            literal_terminal = _terminal_tensor_for_layout(
                layout=layout,
                groups=groups,
                reconstructed=exact_operators,
                hands_by_player=axes,
            )
            maximum_literal_terminal_error = max(
                maximum_literal_terminal_error,
                float(np.max(np.abs(literal_terminal - layout.terminal_values))),
            )
            policies = _policies(layout.information_schema(), axis_seed)
            arm_terminals = {
                arm: _terminal_tensor_for_layout(
                    layout=layout,
                    groups=groups,
                    reconstructed=retained_by_family[family][arm],
                    hands_by_player=axes,
                )
                for arm in arms
            }
            spectral_index = {
                row["arm"]: row
                for row in spectral_rows
                if row["hands_per_player"] == hand_count and row["family"] == family
            }
            for policy_name in parsed["policy_families"]:
                policy = policies[policy_name]
                reference = layout.evaluate(policy)
                literal_override = evaluate_with_terminal_values(
                    layout,
                    policy,
                    literal_terminal,
                )
                literal_error = _evaluation_error(
                    literal_override.evaluation,
                    reference.evaluation,
                )
                literal_mismatches = _action_mismatches(
                    literal_override.best_response_actions,
                    reference.best_response_actions,
                )
                for arm in arms:
                    start = time.perf_counter()
                    candidate = evaluate_with_terminal_values(
                        layout,
                        policy,
                        arm_terminals[arm],
                    )
                    evaluation_ms = (time.perf_counter() - start) * 1000.0
                    strategic_error = _evaluation_error(
                        candidate.evaluation,
                        reference.evaluation,
                    )
                    action_mismatches = _action_mismatches(
                        candidate.best_response_actions,
                        reference.best_response_actions,
                    )
                    spectral = spectral_index[arm]
                    strategic_rows.append(
                        {
                            "family": family,
                            "mixture_components": components,
                            "policy": policy_name,
                            "arm": arm,
                            "declared_rank_cap": _maximum_rank(arm),
                            "joint_deals": layout.deal_count,
                            "literal_terminal_error": (
                                maximum_literal_terminal_error
                            ),
                            "literal_override_strategic_error": literal_error,
                            "literal_override_action_mismatches": literal_mismatches,
                            "strategic_error": strategic_error,
                            "normalized_strategic_error": (
                                strategic_error / layout.game.payoff_span
                            ),
                            "best_response_action_mismatches": action_mismatches,
                            "operator_storage_ratio": spectral["storage_ratio"],
                            "maximum_operator_error": spectral[
                                "maximum_absolute_operator_error"
                            ],
                            "maximum_zero_sum_error": spectral[
                                "maximum_zero_sum_error"
                            ],
                            "override_evaluation_ms": evaluation_ms,
                        }
                    )

    if len(spectral_rows) != 28 or len(strategic_rows) != 84:
        raise AssertionError("showdown rank-screen row counts differ from ADR-0063")
    arm_summaries = []
    for arm in arms:
        spectral_arm = [row for row in spectral_rows if row["arm"] == arm]
        strategic_arm = [row for row in strategic_rows if row["arm"] == arm]
        maximum_rank = _maximum_rank(arm)
        summary = {
            "arm": arm,
            "declared_rank_cap": maximum_rank,
            "maximum_operator_error": max(
                float(row["maximum_absolute_operator_error"])
                for row in spectral_arm
            ),
            "maximum_four_hand_operator_error": max(
                float(row["maximum_absolute_operator_error"])
                for row in spectral_arm
                if row["hands_per_player"] == 4
            ),
            "maximum_zero_sum_error": max(
                float(row["maximum_zero_sum_error"]) for row in spectral_arm
            ),
            "maximum_storage_ratio": max(
                float(row["storage_ratio"]) for row in spectral_arm
            ),
            "maximum_four_hand_storage_ratio": max(
                float(row["storage_ratio"])
                for row in spectral_arm
                if row["hands_per_player"] == 4
            ),
            "maximum_strategic_error": max(
                float(row["strategic_error"]) for row in strategic_arm
            ),
            "maximum_normalized_strategic_error": max(
                float(row["normalized_strategic_error"])
                for row in strategic_arm
            ),
            "best_response_action_mismatches": sum(
                int(row["best_response_action_mismatches"])
                for row in strategic_arm
            ),
            "total_decomposition_ms": sum(
                float(row["decomposition_ms"]) for row in spectral_arm
            ),
            "total_reconstruction_ms": sum(
                float(row["reconstruction_ms"]) for row in spectral_arm
            ),
        }
        gates = parsed["gates"]
        summary["strategically_safe_compressed_arm"] = bool(
            maximum_rank is not None
            and maximum_rank <= gates["maximum_safe_rank_cap"]
            and summary["maximum_normalized_strategic_error"]
            <= gates["maximum_safe_normalized_strategic_error"]
            and summary["best_response_action_mismatches"]
            <= gates["maximum_safe_action_mismatches"]
            and summary["maximum_zero_sum_error"]
            <= gates["maximum_zero_sum_error"]
            and summary["maximum_four_hand_storage_ratio"]
            <= gates["maximum_safe_operator_storage_ratio"]
        )
        arm_summaries.append(summary)

    summary_by_arm = {row["arm"]: row for row in arm_summaries}
    exact = summary_by_arm[parsed["exact_arm"]]
    safe_arms = tuple(
        row["arm"]
        for row in arm_summaries
        if row["strategically_safe_compressed_arm"]
    )
    maximum_literal_override_error = max(
        float(row["literal_override_strategic_error"])
        for row in strategic_rows
    )
    literal_action_mismatches = max(
        int(row["literal_override_action_mismatches"])
        for row in strategic_rows
    )
    gates = parsed["gates"]
    gate_results = {
        "literal_terminal_group_identity": (
            maximum_literal_terminal_error <= gates["maximum_exact_arm_operator_error"]
            and maximum_literal_override_error
            <= gates["maximum_exact_arm_strategic_error"]
            and literal_action_mismatches == 0
        ),
        "exact_arm_operator_identity": (
            exact["maximum_operator_error"]
            <= gates["maximum_exact_arm_operator_error"]
        ),
        "exact_arm_strategic_identity": (
            exact["maximum_strategic_error"]
            <= gates["maximum_exact_arm_strategic_error"]
        ),
        "exact_arm_action_identity": (
            exact["best_response_action_mismatches"]
            <= gates["maximum_exact_arm_action_mismatches"]
        ),
        "zero_sum_identity": (
            max(float(row["maximum_zero_sum_error"]) for row in arm_summaries)
            <= gates["maximum_zero_sum_error"]
        ),
        "strategically_safe_compressed_arm_exists": (
            bool(safe_arms)
            if gates["require_strategically_safe_compressed_arm"]
            else True
        ),
    }

    return {
        "schema_version": 1,
        "experiment_type": "showdown_value_operator_tensor_train_rank_screen",
        "status": "revealed_engineering_screen_only",
        "config": parsed,
        "config_sha256": _sha256(
            _ROOT
            / "experiments"
            / "configs"
            / "showdown-value-operator-rank-screen-v1.json"
        ),
        "environment": environment_metadata(),
        "counts": {
            "spectral_rows": len(spectral_rows),
            "strategic_rows": len(strategic_rows),
            "terminal_groups": parsed["expected_terminal_groups"],
            "arms": len(arms),
        },
        "aggregate": {
            "maximum_literal_terminal_error": maximum_literal_terminal_error,
            "maximum_literal_override_strategic_error": (
                maximum_literal_override_error
            ),
            "literal_override_action_mismatches": literal_action_mismatches,
            "strategically_safe_compressed_arms": safe_arms,
        },
        "arm_summaries": arm_summaries,
        "gates": {"results": gate_results, "passed": all(gate_results.values())},
        "timing": {"wall_seconds": time.perf_counter() - started},
        "spectral_rows": spectral_rows,
        "strategic_rows": strategic_rows,
        "limitations": [
            "Dense reconstruction is used for labels; no direct TT contraction is timed.",
            "Only one board and four-to-five-hand axes are screened.",
            "Independent terminal-group TTs do not exploit sharing across contender sets.",
            "Card compatibility remains exact outside the value operator by design.",
            "This revealed screen cannot select a poker strategy or neural model.",
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
    result = run_showdown_value_rank_screen(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "showdown value rank screen: "
        f"spectral={result['counts']['spectral_rows']}, "
        f"safe={result['aggregate']['strategically_safe_compressed_arms']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
