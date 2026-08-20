"""Run the frozen exact factorized-card belief and contraction audit."""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import math
import random
import time
from itertools import combinations, product
from pathlib import Path
from statistics import median
from typing import Any, Callable, TypeVar

import numpy as np

from .factorized_belief import (
    FactorBeliefContraction,
    FactorizedCardBelief,
    MaterializedCardBelief,
)
from .reporting import environment_metadata
from .river import Card, HoleCards, evaluate_seven, parse_cards

_T = TypeVar("_T")
_ROOT = Path(__file__).parents[2]
_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_river_sha256",
    "expected_multiway_game_sha256",
    "expected_evaluation_sha256",
    "expected_public_tree_tensor_sha256",
    "board",
    "player_counts",
    "exact_hands_per_player",
    "range_families",
    "mixture_component_counts",
    "public_updates_per_player",
    "public_likelihood_rule",
    "private_conditioning_rule",
    "performance_player_count",
    "performance_hands_per_player",
    "performance_mixture_components",
    "wide_hands_per_player",
    "wide_mixture_components",
    "meet_in_middle_split_rule",
    "summation_rule",
    "timing_repeats",
    "warmup_repeats",
    "gates",
}
_GATE_FIELDS = {
    "maximum_initial_distribution_error",
    "maximum_updated_distribution_error",
    "maximum_partition_error",
    "maximum_marginal_error",
    "maximum_wide_split_relative_error",
    "maximum_impossible_assignment_mass",
    "maximum_exact_support_mismatches",
    "require_contiguous_float64_and_uint64_storage",
    "ten_hand_mitm_strictly_faster_than_recursive",
    "maximum_32_hand_persistent_byte_ratio_to_dense_joint",
    "require_32_hand_partial_records_less_than_cartesian_assignments",
}
_SOURCE_PATHS = {
    "expected_river_sha256": _ROOT / "src" / "pontius" / "river.py",
    "expected_multiway_game_sha256": (
        _ROOT / "src" / "pontius" / "river_multiway.py"
    ),
    "expected_evaluation_sha256": _ROOT / "src" / "pontius" / "evaluation.py",
    "expected_public_tree_tensor_sha256": (
        _ROOT / "src" / "pontius" / "public_tree_tensor.py"
    ),
}
_FAMILIES = ("balanced", "blocker_heavy")


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


def parse_factorized_belief_audit_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "factorized-belief fields differ from ADR-0061: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    if config["evidence_stage"] != "revealed_engineering_audit":
        raise ValueError("factorized-belief audit must remain revealed engineering")
    if config["seed"] != 20260819:
        raise ValueError("factorized-belief seed differs from ADR-0061")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")

    frozen_sequences = {
        "board": ("2c", "7d", "9h", "Js", "Qc"),
        "player_counts": (2, 3, 4, 5, 6),
        "exact_hands_per_player": (2, 4),
        "range_families": _FAMILIES,
        "mixture_component_counts": (1, 3),
        "performance_hands_per_player": (4, 7, 10),
        "wide_hands_per_player": (16, 24, 32),
    }
    parsed_sequences = {}
    for field, expected in frozen_sequences.items():
        values = tuple(config[field])
        if values != expected:
            raise ValueError(f"{field} differs from ADR-0061")
        parsed_sequences[field] = values
    frozen_scalars = {
        "public_updates_per_player": 2,
        "public_likelihood_rule": "sha256_positive_1_to_31_over_31",
        "private_conditioning_rule": "first_supported_player_zero_hand",
        "performance_player_count": 6,
        "performance_mixture_components": 3,
        "wide_mixture_components": 3,
        "meet_in_middle_split_rule": (
            "balanced_contiguous_then_alternating_replay"
        ),
        "summation_rule": "float64_math_fsum_inclusion_exclusion",
        "timing_repeats": 3,
        "warmup_repeats": 1,
    }
    if any(config[field] != value for field, value in frozen_scalars.items()):
        raise ValueError("factorized-belief execution contract differs from ADR-0061")

    gates = config["gates"]
    if not isinstance(gates, dict) or set(gates) != _GATE_FIELDS:
        raise ValueError("factorized-belief gates differ from ADR-0061")
    parsed_gates = dict(gates)
    for field in (
        "maximum_initial_distribution_error",
        "maximum_updated_distribution_error",
        "maximum_partition_error",
        "maximum_marginal_error",
        "maximum_wide_split_relative_error",
        "maximum_impossible_assignment_mass",
        "maximum_32_hand_persistent_byte_ratio_to_dense_joint",
    ):
        parsed_gates[field] = _finite_nonnegative(gates[field], field)
    if parsed_gates["maximum_initial_distribution_error"] > 1e-12:
        raise ValueError("initial-distribution tolerance exceeds ADR-0061")
    if parsed_gates["maximum_updated_distribution_error"] > 1e-12:
        raise ValueError("updated-distribution tolerance exceeds ADR-0061")
    if parsed_gates["maximum_partition_error"] > 1e-10:
        raise ValueError("partition tolerance exceeds ADR-0061")
    if parsed_gates["maximum_marginal_error"] > 1e-10:
        raise ValueError("marginal tolerance exceeds ADR-0061")
    if parsed_gates["maximum_wide_split_relative_error"] > 1e-10:
        raise ValueError("wide replay tolerance exceeds ADR-0061")
    if parsed_gates["maximum_impossible_assignment_mass"] != 0.0:
        raise ValueError("impossible assignment mass must remain exactly zero")
    if parsed_gates["maximum_32_hand_persistent_byte_ratio_to_dense_joint"] != 1e-6:
        raise ValueError("32-hand byte-ratio gate differs from ADR-0061")
    if (
        isinstance(gates["maximum_exact_support_mismatches"], bool)
        or gates["maximum_exact_support_mismatches"] != 0
    ):
        raise ValueError("exact support mismatches must remain zero")
    for field in (
        "require_contiguous_float64_and_uint64_storage",
        "ten_hand_mitm_strictly_faster_than_recursive",
        "require_32_hand_partial_records_less_than_cartesian_assignments",
    ):
        if gates[field] is not True:
            raise ValueError(f"{field} must remain true")

    return {
        **config,
        **parsed_sequences,
        **frozen_scalars,
        "gates": parsed_gates,
    }


def _derived_seed(seed: int, *parts: object) -> int:
    payload = "|".join((str(seed), *(str(part) for part in parts)))
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


@functools.lru_cache(maxsize=4)
def _ranked_hands(board: tuple[Card, ...]) -> tuple[HoleCards, ...]:
    available = tuple(card for card in range(52) if card not in set(board))
    return tuple(
        sorted(
            combinations(available, 2),
            key=lambda hand: (evaluate_seven((*board, *hand)), hand),
        )
    )


def _stratified_select(
    candidates: tuple[HoleCards, ...],
    count: int,
    rng: random.Random,
) -> tuple[HoleCards, ...]:
    if count <= 0 or count > len(candidates):
        raise ValueError("stratified hand count is outside the candidate range")
    selected = []
    for index in range(count):
        lower = index * len(candidates) // count
        upper = (index + 1) * len(candidates) // count
        if upper <= lower:
            upper = lower + 1
        selected.append(candidates[rng.randrange(lower, upper)])
    if len(set(selected)) != count:
        raise AssertionError("disjoint strength strata produced duplicate hands")
    return tuple(selected)


def _assignment_exists(
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    fixed_player: int,
    fixed_hand: int,
) -> bool:
    masks = tuple(
        tuple((1 << hand[0]) | (1 << hand[1]) for hand in hands)
        for hands in hands_by_player
    )
    selected_mask = masks[fixed_player][fixed_hand]

    def walk(player: int, used_mask: int) -> bool:
        if player == len(hands_by_player):
            return True
        if player == fixed_player:
            return walk(player + 1, used_mask)
        for mask in masks[player]:
            if used_mask & mask == 0 and walk(player + 1, used_mask | mask):
                return True
        return False

    return walk(0, selected_mask)


def _all_hands_supported(
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
) -> bool:
    return all(
        _assignment_exists(hands_by_player, player, hand_index)
        for player, hands in enumerate(hands_by_player)
        for hand_index in range(len(hands))
    )


def generate_hand_axes(
    *,
    board: tuple[Card, ...],
    players: int,
    hands_per_player: int,
    family: str,
    seed: int,
) -> tuple[tuple[HoleCards, ...], ...]:
    if not 2 <= players <= 6 or not 2 <= hands_per_player <= 32:
        raise ValueError("hand-axis dimensions are outside the frozen range")
    if family not in _FAMILIES:
        raise ValueError(f"unsupported hand-axis family {family!r}")
    ranked = _ranked_hands(board)
    available = tuple(card for card in range(52) if card not in set(board))

    for attempt in range(100):
        family_rng = random.Random(
            _derived_seed(seed, "axes", players, hands_per_player, family, attempt)
        )
        if family == "balanced":
            axes = tuple(
                _stratified_select(
                    ranked,
                    hands_per_player,
                    random.Random(family_rng.getrandbits(64)),
                )
                for _ in range(players)
            )
        else:
            blocker_cards = frozenset(family_rng.sample(available, 4))
            blocker_candidates = tuple(
                hand for hand in ranked if set(hand) & blocker_cards
            )
            clean_candidates = tuple(
                hand for hand in ranked if not set(hand) & blocker_cards
            )
            blocker_count = (hands_per_player + 1) // 2
            clean_count = hands_per_player - blocker_count
            axes_list = []
            for _ in range(players):
                seat_rng = random.Random(family_rng.getrandbits(64))
                blocker_hands = _stratified_select(
                    blocker_candidates,
                    blocker_count,
                    seat_rng,
                )
                clean_hands = _stratified_select(
                    clean_candidates,
                    clean_count,
                    seat_rng,
                ) if clean_count else ()
                axes_list.append((*blocker_hands, *clean_hands))
            axes = tuple(axes_list)
        if _all_hands_supported(axes):
            return axes
    raise ValueError("could not generate fully supported factorized hand axes")


def _raw_factors(
    *,
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    components: int,
    seed: int,
    family: str,
) -> tuple[np.ndarray, tuple[np.ndarray, ...]]:
    mixture = np.arange(1, components + 1, dtype=np.float64)
    unaries = []
    for player, hands in enumerate(hands_by_player):
        values = np.empty((components, len(hands)), dtype=np.float64)
        for component in range(components):
            for hand_index, hand in enumerate(hands):
                payload = (
                    f"{seed}|unary|{family}|{components}|{component}|"
                    f"{player}|{hand_index}|{hand!r}"
                )
                score = int.from_bytes(
                    hashlib.sha256(payload.encode("utf-8")).digest()[:8],
                    "big",
                )
                values[component, hand_index] = (1 + score % 31) / 31.0
        unaries.append(values)
    return mixture, tuple(unaries)


def make_factorized_case(
    *,
    board: tuple[Card, ...],
    players: int,
    hands_per_player: int,
    family: str,
    components: int,
    seed: int,
) -> tuple[FactorizedCardBelief, np.ndarray, tuple[np.ndarray, ...]]:
    axes = generate_hand_axes(
        board=board,
        players=players,
        hands_per_player=hands_per_player,
        family=family,
        seed=seed,
    )
    mixture, unaries = _raw_factors(
        hands_by_player=axes,
        components=components,
        seed=seed,
        family=family,
    )
    belief = FactorizedCardBelief(
        hands_by_player=axes,
        mixture_weights=mixture,
        unary_weights=unaries,
        board=board,
    )
    return belief, mixture, unaries


def _explicit_distribution(
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    mixture: np.ndarray,
    unaries: tuple[np.ndarray, ...],
) -> dict[tuple[int, ...], float]:
    masks = tuple(
        tuple((1 << hand[0]) | (1 << hand[1]) for hand in hands)
        for hands in hands_by_player
    )
    weights = {}
    for indices in product(*(range(len(hands)) for hands in hands_by_player)):
        used_mask = 0
        compatible = True
        for player, hand_index in enumerate(indices):
            mask = masks[player][hand_index]
            if used_mask & mask:
                compatible = False
                break
            used_mask |= mask
        if not compatible:
            continue
        component_weights = (
            float(mixture[component])
            * math.prod(
                float(unaries[player][component, hand_index])
                for player, hand_index in enumerate(indices)
            )
            for component in range(len(mixture))
        )
        weight = math.fsum(component_weights)
        if weight > 0.0:
            weights[indices] = weight
    total = math.fsum(weights.values())
    if total <= 0.0:
        raise ValueError("explicit factor oracle found zero compatible mass")
    return {indices: weight / total for indices, weight in weights.items()}


def _materialized_dict(materialized: MaterializedCardBelief) -> dict[tuple[int, ...], float]:
    return materialized.as_dict()


def _distribution_error(
    first: dict[tuple[int, ...], float],
    second: dict[tuple[int, ...], float],
) -> float:
    return float(
        max(
            (
                abs(first.get(key, 0.0) - second.get(key, 0.0))
                for key in set(first) | set(second)
            ),
            default=0.0,
        )
    )


def _support_mismatches(
    first: dict[tuple[int, ...], float],
    second: dict[tuple[int, ...], float],
) -> int:
    return len(set(first) ^ set(second))


def _likelihood(
    *,
    seed: int,
    player: int,
    update: int,
    hands: tuple[HoleCards, ...],
) -> np.ndarray:
    result = np.empty(len(hands), dtype=np.float64)
    for hand_index, hand in enumerate(hands):
        payload = f"{seed}|likelihood|{player}|{update}|{hand_index}|{hand!r}"
        score = int.from_bytes(
            hashlib.sha256(payload.encode("utf-8")).digest()[:8],
            "big",
        )
        result[hand_index] = (1 + score % 31) / 31.0
    return result


def _update_explicit(
    distribution: dict[tuple[int, ...], float],
    player: int,
    likelihood: np.ndarray,
) -> dict[tuple[int, ...], float]:
    weights = {
        assignment: probability * float(likelihood[assignment[player]])
        for assignment, probability in distribution.items()
    }
    total = math.fsum(weights.values())
    if total <= 0.0:
        raise ValueError("explicit likelihood update eliminated all mass")
    return {assignment: weight / total for assignment, weight in weights.items() if weight > 0.0}


def _apply_updates(
    belief: FactorizedCardBelief,
    distribution: dict[tuple[int, ...], float] | None,
    *,
    seed: int,
    updates_per_player: int,
) -> tuple[FactorizedCardBelief, dict[tuple[int, ...], float] | None]:
    result = belief
    explicit = distribution
    for update in range(updates_per_player):
        for player in range(belief.num_players):
            likelihood = _likelihood(
                seed=seed,
                player=player,
                update=update,
                hands=belief.hands_by_player[player],
            )
            result = result.with_likelihood(player, likelihood)
            if explicit is not None:
                explicit = _update_explicit(explicit, player, likelihood)
    return result, explicit


def _condition_first_supported(
    belief: FactorizedCardBelief,
    distribution: dict[tuple[int, ...], float],
) -> tuple[FactorizedCardBelief, dict[tuple[int, ...], float]]:
    selected = min(assignment[0] for assignment in distribution)
    conditioned = belief.condition_on_hand(0, belief.hands_by_player[0][selected])
    filtered = {
        assignment: probability
        for assignment, probability in distribution.items()
        if assignment[0] == selected
    }
    total = math.fsum(filtered.values())
    return conditioned, {
        assignment: probability / total for assignment, probability in filtered.items()
    }


def _explicit_marginals(
    distribution: dict[tuple[int, ...], float],
    hand_counts: tuple[int, ...],
) -> tuple[np.ndarray, ...]:
    marginals = tuple(np.zeros(count, dtype=np.float64) for count in hand_counts)
    for assignment, probability in distribution.items():
        for player, hand_index in enumerate(assignment):
            marginals[player][hand_index] += probability
    return marginals


def _marginal_error(
    first: tuple[np.ndarray, ...],
    second: tuple[np.ndarray, ...],
) -> float:
    return max(
        float(np.max(np.abs(left - right)))
        for left, right in zip(first, second, strict=True)
    )


def _relative_error(first: float, second: float) -> float:
    return abs(first - second) / max(abs(first), abs(second), 1e-300)


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


def _contraction_payload(result: FactorBeliefContraction) -> dict[str, object]:
    return {
        "partition": result.partition,
        "cartesian_assignments": result.cartesian_assignments,
        "card_compatible_assignments": result.card_compatible_assignments,
        "partial_records": result.partial_records,
        "partial_numeric_bytes": result.partial_numeric_bytes,
        "incidence_table_entries": result.incidence_table_entries,
        "maximum_live_incidence_table_entries": (
            result.maximum_live_incidence_table_entries
        ),
        "estimated_incidence_numeric_bytes": result.estimated_incidence_numeric_bytes,
        "split_partition_relative_error": result.split_partition_relative_error,
    }


def run_factorized_belief_audit(config: dict[str, Any]) -> dict[str, Any]:
    """Execute the exact frozen ADR-0061 factor-closure workload."""

    parsed = parse_factorized_belief_audit_config(config)
    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    exact_rows = []
    performance_rows = []
    wide_rows = []
    maximum_initial_error = 0.0
    maximum_updated_error = 0.0
    maximum_partition_error = 0.0
    maximum_marginal_error = 0.0
    maximum_impossible_mass = 0.0
    support_mismatches = 0
    layout_failures = 0

    for players in parsed["player_counts"]:
        for hand_count in parsed["exact_hands_per_player"]:
            for family in parsed["range_families"]:
                for components in parsed["mixture_component_counts"]:
                    case_seed = _derived_seed(
                        parsed["seed"], "exact", players, hand_count, family, components
                    )
                    belief, mixture, unaries = make_factorized_case(
                        board=board,
                        players=players,
                        hands_per_player=hand_count,
                        family=family,
                        components=components,
                        seed=case_seed,
                    )
                    explicit_initial = _explicit_distribution(
                        belief.hands_by_player,
                        mixture,
                        unaries,
                    )
                    factor_initial = _materialized_dict(belief.materialize())
                    initial_error = _distribution_error(
                        factor_initial,
                        explicit_initial,
                    )
                    initial_support_mismatches = _support_mismatches(
                        factor_initial,
                        explicit_initial,
                    )

                    updated, explicit_updated = _apply_updates(
                        belief,
                        explicit_initial,
                        seed=case_seed,
                        updates_per_player=parsed["public_updates_per_player"],
                    )
                    assert explicit_updated is not None
                    conditioned, explicit_conditioned = _condition_first_supported(
                        updated,
                        explicit_updated,
                    )
                    factor_conditioned = _materialized_dict(conditioned.materialize())
                    updated_error = _distribution_error(
                        factor_conditioned,
                        explicit_conditioned,
                    )
                    updated_support_mismatches = _support_mismatches(
                        factor_conditioned,
                        explicit_conditioned,
                    )

                    recursive = conditioned.recursive_contract()
                    mitm = conditioned.meet_in_middle_contract()
                    partition_error = _relative_error(
                        recursive.partition,
                        mitm.partition,
                    )
                    explicit_marginals = _explicit_marginals(
                        explicit_conditioned,
                        conditioned.hand_counts,
                    )
                    marginal_error = max(
                        _marginal_error(recursive.marginals, mitm.marginals),
                        _marginal_error(explicit_marginals, mitm.marginals),
                    )
                    impossible_mass = 0.0
                    for assignment in product(
                        *(range(count) for count in conditioned.hand_counts)
                    ):
                        if assignment not in factor_conditioned:
                            impossible_mass = max(
                                impossible_mass,
                                abs(conditioned.assignment_weight(assignment))
                                if any(
                                    int(conditioned.hand_masks[left][assignment[left]])
                                    & int(conditioned.hand_masks[right][assignment[right]])
                                    for left in range(players)
                                    for right in range(left + 1, players)
                                )
                                else 0.0,
                            )

                    case_support_mismatches = (
                        initial_support_mismatches + updated_support_mismatches
                    )
                    layout_failure = int(
                        not belief.storage_is_contiguous_float64_and_uint64()
                        or not conditioned.storage_is_contiguous_float64_and_uint64()
                    )
                    maximum_initial_error = max(maximum_initial_error, initial_error)
                    maximum_updated_error = max(maximum_updated_error, updated_error)
                    maximum_partition_error = max(
                        maximum_partition_error,
                        partition_error,
                        mitm.split_partition_relative_error,
                    )
                    maximum_marginal_error = max(maximum_marginal_error, marginal_error)
                    maximum_impossible_mass = max(
                        maximum_impossible_mass,
                        impossible_mass,
                    )
                    support_mismatches += case_support_mismatches
                    layout_failures += layout_failure
                    exact_rows.append(
                        {
                            "players": players,
                            "hands_per_player": hand_count,
                            "family": family,
                            "mixture_components": components,
                            "initial_distribution_error": initial_error,
                            "updated_conditioned_distribution_error": updated_error,
                            "support_mismatches": case_support_mismatches,
                            "partition_relative_error": partition_error,
                            "marginal_error": marginal_error,
                            "impossible_assignment_mass": impossible_mass,
                            "layout_failure": layout_failure,
                            "persistent_numeric_bytes": belief.persistent_numeric_bytes,
                            "positive_initial_assignments": len(explicit_initial),
                            "positive_conditioned_assignments": len(explicit_conditioned),
                            "recursive": _contraction_payload(recursive),
                            "meet_in_middle": _contraction_payload(mitm),
                        }
                    )

    for hand_count in parsed["performance_hands_per_player"]:
        for family in parsed["range_families"]:
            case_seed = _derived_seed(parsed["seed"], "performance", hand_count, family)
            belief, _, _ = make_factorized_case(
                board=board,
                players=parsed["performance_player_count"],
                hands_per_player=hand_count,
                family=family,
                components=parsed["performance_mixture_components"],
                seed=case_seed,
            )
            belief, _ = _apply_updates(
                belief,
                None,
                seed=case_seed,
                updates_per_player=parsed["public_updates_per_player"],
            )
            recursive_ms, recursive_min_ms, recursive = _timed(
                belief.recursive_contract,
                repeats=parsed["timing_repeats"],
                warmups=parsed["warmup_repeats"],
            )
            mitm_ms, mitm_min_ms, mitm = _timed(
                belief.meet_in_middle_contract,
                repeats=parsed["timing_repeats"],
                warmups=parsed["warmup_repeats"],
            )
            partition_error = _relative_error(recursive.partition, mitm.partition)
            marginal_error = _marginal_error(recursive.marginals, mitm.marginals)
            maximum_partition_error = max(
                maximum_partition_error,
                partition_error,
                mitm.split_partition_relative_error,
            )
            maximum_marginal_error = max(maximum_marginal_error, marginal_error)
            layout_failure = int(
                not belief.storage_is_contiguous_float64_and_uint64()
            )
            layout_failures += layout_failure
            performance_rows.append(
                {
                    "players": belief.num_players,
                    "hands_per_player": hand_count,
                    "family": family,
                    "mixture_components": belief.component_count,
                    "partition_relative_error": partition_error,
                    "marginal_error": marginal_error,
                    "layout_failure": layout_failure,
                    "persistent_numeric_bytes": belief.persistent_numeric_bytes,
                    "recursive_median_ms": recursive_ms,
                    "recursive_min_ms": recursive_min_ms,
                    "meet_in_middle_median_ms": mitm_ms,
                    "meet_in_middle_min_ms": mitm_min_ms,
                    "meet_in_middle_speedup": recursive_ms / mitm_ms,
                    "recursive": _contraction_payload(recursive),
                    "meet_in_middle": _contraction_payload(mitm),
                }
            )

    maximum_wide_error = 0.0
    for hand_count in parsed["wide_hands_per_player"]:
        for family in parsed["range_families"]:
            case_seed = _derived_seed(parsed["seed"], "wide", hand_count, family)
            belief, _, _ = make_factorized_case(
                board=board,
                players=parsed["performance_player_count"],
                hands_per_player=hand_count,
                family=family,
                components=parsed["wide_mixture_components"],
                seed=case_seed,
            )
            belief, _ = _apply_updates(
                belief,
                None,
                seed=case_seed,
                updates_per_player=parsed["public_updates_per_player"],
            )
            start = time.perf_counter()
            contiguous = belief.meet_in_middle_contract((0, 1, 2))
            contiguous_ms = (time.perf_counter() - start) * 1000.0
            start = time.perf_counter()
            alternating = belief.meet_in_middle_contract((0, 2, 4))
            alternating_ms = (time.perf_counter() - start) * 1000.0
            split_error = max(
                _relative_error(contiguous.partition, alternating.partition),
                _marginal_error(contiguous.marginals, alternating.marginals),
                contiguous.split_partition_relative_error,
                alternating.split_partition_relative_error,
                float(
                    contiguous.card_compatible_assignments
                    != alternating.card_compatible_assignments
                ),
            )
            maximum_wide_error = max(maximum_wide_error, split_error)
            dense_joint_bytes = hand_count**belief.num_players * 8
            byte_ratio = belief.persistent_numeric_bytes / dense_joint_bytes
            layout_failure = int(
                not belief.storage_is_contiguous_float64_and_uint64()
            )
            layout_failures += layout_failure
            wide_rows.append(
                {
                    "players": belief.num_players,
                    "hands_per_player": hand_count,
                    "family": family,
                    "mixture_components": belief.component_count,
                    "split_replay_error": split_error,
                    "layout_failure": layout_failure,
                    "persistent_numeric_bytes": belief.persistent_numeric_bytes,
                    "dense_joint_probability_bytes": dense_joint_bytes,
                    "persistent_byte_ratio_to_dense_joint": byte_ratio,
                    "contiguous_split_ms": contiguous_ms,
                    "alternating_split_ms": alternating_ms,
                    "contiguous": _contraction_payload(contiguous),
                    "alternating": _contraction_payload(alternating),
                }
            )

    if len(exact_rows) != 40 or len(performance_rows) != 6 or len(wide_rows) != 6:
        raise AssertionError("factorized-belief audit row counts differ from ADR-0061")
    ten_hand_rows = [
        row for row in performance_rows if row["hands_per_player"] == 10
    ]
    hand_32_rows = [row for row in wide_rows if row["hands_per_player"] == 32]
    gates = parsed["gates"]
    gate_results = {
        "initial_distribution_identity": bool(
            maximum_initial_error <= gates["maximum_initial_distribution_error"]
        ),
        "updated_distribution_identity": bool(
            maximum_updated_error <= gates["maximum_updated_distribution_error"]
        ),
        "partition_identity": bool(
            maximum_partition_error <= gates["maximum_partition_error"]
        ),
        "marginal_identity": bool(
            maximum_marginal_error <= gates["maximum_marginal_error"]
        ),
        "wide_split_identity": bool(
            maximum_wide_error <= gates["maximum_wide_split_relative_error"]
        ),
        "impossible_assignment_mass_is_zero": bool(
            maximum_impossible_mass <= gates["maximum_impossible_assignment_mass"]
        ),
        "exact_support_identity": bool(
            support_mismatches <= gates["maximum_exact_support_mismatches"]
        ),
        "contiguous_numeric_storage": bool(
            layout_failures == 0
            and gates["require_contiguous_float64_and_uint64_storage"]
        ),
        "ten_hand_mitm_strictly_faster_than_recursive": bool(
            sum(float(row["meet_in_middle_median_ms"]) for row in ten_hand_rows)
            < sum(float(row["recursive_median_ms"]) for row in ten_hand_rows)
        ),
        "32_hand_persistent_byte_ratio": all(
            float(row["persistent_byte_ratio_to_dense_joint"])
            <= gates["maximum_32_hand_persistent_byte_ratio_to_dense_joint"]
            for row in hand_32_rows
        ),
        "32_hand_partial_records_less_than_cartesian_assignments": all(
            max(
                int(row["contiguous"]["partial_records"]),
                int(row["alternating"]["partial_records"]),
            )
            < 32**6
            for row in hand_32_rows
        ),
    }

    return {
        "schema_version": 1,
        "experiment_type": "exact_factorized_card_belief_audit",
        "status": "revealed_engineering_audit_only",
        "config": parsed,
        "config_sha256": _sha256(
            _ROOT / "experiments" / "configs" / "factorized-card-belief-audit-v1.json"
        ),
        "environment": environment_metadata(),
        "counts": {
            "exact_cases": len(exact_rows),
            "performance_cases": len(performance_rows),
            "wide_cases": len(wide_rows),
        },
        "aggregate": {
            "maximum_initial_distribution_error": maximum_initial_error,
            "maximum_updated_distribution_error": maximum_updated_error,
            "maximum_partition_relative_error": maximum_partition_error,
            "maximum_marginal_error": maximum_marginal_error,
            "maximum_wide_split_error": maximum_wide_error,
            "maximum_impossible_assignment_mass": maximum_impossible_mass,
            "exact_support_mismatches": support_mismatches,
            "numeric_layout_failures": layout_failures,
            "ten_hand_pooled_recursive_ms": sum(
                float(row["recursive_median_ms"]) for row in ten_hand_rows
            ),
            "ten_hand_pooled_meet_in_middle_ms": sum(
                float(row["meet_in_middle_median_ms"]) for row in ten_hand_rows
            ),
            "ten_hand_pooled_speedup": (
                sum(float(row["recursive_median_ms"]) for row in ten_hand_rows)
                / sum(
                    float(row["meet_in_middle_median_ms"])
                    for row in ten_hand_rows
                )
            ),
            "maximum_32_hand_persistent_byte_ratio_to_dense_joint": max(
                float(row["persistent_byte_ratio_to_dense_joint"])
                for row in hand_32_rows
            ),
            "maximum_32_hand_partial_records": max(
                max(
                    int(row["contiguous"]["partial_records"]),
                    int(row["alternating"]["partial_records"]),
                )
                for row in hand_32_rows
            ),
        },
        "gates": {"results": gate_results, "passed": all(gate_results.values())},
        "timing": {"wall_seconds": time.perf_counter() - started},
        "exact_rows": exact_rows,
        "performance_rows": performance_rows,
        "wide_rows": wide_rows,
        "limitations": [
            "The exact contraction covers normalization and marginals, not showdown payoff.",
            "The mixture family does not compact every arbitrary correlated joint tensor.",
            "Incidence numeric bytes exclude Python dictionary and object overhead.",
            "All workloads are revealed reduced river beliefs, not online six-max traces.",
            "No neural leaf, CFR update, or strategy-selection result follows.",
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
    result = run_factorized_belief_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "factorized-card belief audit: "
        f"exact={result['counts']['exact_cases']}, "
        f"wide={result['counts']['wide_cases']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
