"""Deterministic families of exact river contexts for scheduler datasets."""

from __future__ import annotations

import hashlib
import random
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from math import log

from .river import (
    Card,
    HoleCards,
    RiverDeal,
    RiverHoldem,
    distribution_total_variation,
    evaluate_seven,
    format_card,
)

CONTEXT_FAMILIES = ("balanced", "polarized", "blocker_stress", "correlated")
CONTEXT_SPLITS = ("development", "validation", "test")


@dataclass(frozen=True, slots=True)
class RiverContext:
    """One generated range instance and its leakage-safe group identity."""

    context_id: str
    group_id: str
    split: str
    family: str
    seed: int
    game: RiverHoldem


def _derived_seed(seed: int, *parts: object) -> int:
    payload = "|".join((str(seed), *(str(part) for part in parts)))
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


def _group_split(seed: int, group_index: int) -> str:
    bucket = _derived_seed(seed, "split", group_index) % 20
    if bucket < 14:
        return "development"
    if bucket < 17:
        return "validation"
    return "test"


def _quantile_targets(count: int, polarized: bool) -> tuple[float, ...]:
    if not polarized:
        return tuple((index + 0.5) / count for index in range(count))
    low_count = count // 2
    high_count = count - low_count
    lows = tuple(0.03 + 0.17 * (index + 0.5) / low_count for index in range(low_count))
    highs = tuple(
        0.80 + 0.17 * (index + 0.5) / high_count
        for index in range(high_count)
    )
    return lows + highs


def _select_quantile_hands(
    ranked_hands: tuple[HoleCards, ...],
    targets: tuple[float, ...],
    rng: random.Random,
    *,
    preferred_cards: frozenset[Card] = frozenset(),
    preferred_count: int = 0,
) -> tuple[HoleCards, ...]:
    selected: list[HoleCards] = []
    hand_count = len(ranked_hands)
    half_window = max(12, hand_count // 25)
    for target_index, target in enumerate(targets):
        center = round(target * (hand_count - 1))
        lower = max(0, center - half_window)
        upper = min(hand_count, center + half_window + 1)
        candidates = [hand for hand in ranked_hands[lower:upper] if hand not in selected]
        if target_index < preferred_count:
            preferred = [
                hand for hand in candidates if set(hand) & set(preferred_cards)
            ]
            if preferred:
                candidates = preferred
        if not candidates:
            raise AssertionError("quantile hand selection exhausted its window")
        selected.append(rng.choice(candidates))
    return tuple(selected)


def _all_supported(
    hands0: tuple[HoleCards, ...],
    hands1: tuple[HoleCards, ...],
) -> bool:
    return all(any(not set(hand0) & set(hand1) for hand1 in hands1) for hand0 in hands0) and all(
        any(not set(hand0) & set(hand1) for hand0 in hands0) for hand1 in hands1
    )


def _range_weights(hands: tuple[HoleCards, ...], rng: random.Random) -> dict[HoleCards, float]:
    choices = (0.25, 0.5, 1.0, 2.0, 4.0)
    return {hand: rng.choice(choices) for hand in hands}


def _make_family_game(
    *,
    board: tuple[Card, ...],
    pot: float,
    stacks: tuple[float, float],
    bet_size: float,
    raise_to: float | None,
    family: str,
    hands_per_player: int,
    rng: random.Random,
) -> RiverHoldem:
    remaining = tuple(card for card in range(52) if card not in set(board))
    ranked_hands = tuple(
        sorted(
            combinations(remaining, 2),
            key=lambda hand: (evaluate_seven((*board, *hand)), hand),
        )
    )
    balanced_targets = _quantile_targets(hands_per_player, False)
    polarized_targets = _quantile_targets(hands_per_player, True)

    for _ in range(100):
        targets0 = polarized_targets if family == "polarized" else balanced_targets
        hands0 = _select_quantile_hands(ranked_hands, targets0, rng)
        preferred_cards = frozenset(card for hand in hands0 for card in hand)
        hands1 = _select_quantile_hands(
            ranked_hands,
            balanced_targets,
            rng,
            preferred_cards=preferred_cards,
            preferred_count=(hands_per_player + 1) // 2 if family == "blocker_stress" else 0,
        )
        if _all_supported(hands0, hands1):
            break
    else:
        raise ValueError("could not generate ranges with supported private hands")

    weights0 = _range_weights(hands0, rng)
    weights1 = _range_weights(hands1, rng)
    if family != "correlated":
        return RiverHoldem.from_independent_ranges(
            board=board,
            pot=pot,
            stacks=stacks,
            bet_size=bet_size,
            raise_to=raise_to,
            player0_weights=weights0,
            player1_weights=weights1,
        )

    joint_weights = {}
    for index0, hand0 in enumerate(hands0):
        for index1, hand1 in enumerate(hands1):
            if set(hand0) & set(hand1):
                continue
            assortative_factor = 4.0 if index0 == index1 else 0.5
            joint_weights[RiverDeal(hand0, hand1)] = (
                weights0[hand0] * weights1[hand1] * assortative_factor
            )
    return RiverHoldem.from_joint_weights(
        board=board,
        pot=pot,
        stacks=stacks,
        bet_size=bet_size,
        raise_to=raise_to,
        joint_weights=joint_weights,
    )


def generate_river_contexts(
    *,
    groups: int,
    seed: int = 0,
    hands_per_player: int = 4,
    families: tuple[str, ...] = CONTEXT_FAMILIES,
    splits: tuple[str, ...] = CONTEXT_SPLITS,
    sequential_raise: bool = False,
) -> tuple[RiverContext, ...]:
    """Generate grouped contexts; all variants of a board share one split."""

    if groups <= 0:
        raise ValueError("groups must be positive")
    if not isinstance(sequential_raise, bool):
        raise TypeError("sequential_raise must be a boolean")
    if not 2 <= hands_per_player <= 8:
        raise ValueError("hands_per_player must be between two and eight")
    if not families or len(set(families)) != len(families):
        raise ValueError("families must be nonempty and unique")
    unknown = set(families) - set(CONTEXT_FAMILIES)
    if unknown:
        raise ValueError(f"unsupported context families: {sorted(unknown)!r}")
    if not splits or len(set(splits)) != len(splits):
        raise ValueError("splits must be nonempty and unique")
    unknown_splits = set(splits) - set(CONTEXT_SPLITS)
    if unknown_splits:
        raise ValueError(f"unsupported context splits: {sorted(unknown_splits)!r}")

    contexts = []
    for group_index in range(groups):
        group_id = f"river-g{group_index:06d}"
        group_rng = random.Random(_derived_seed(seed, "group", group_index))
        board = tuple(sorted(group_rng.sample(range(52), 5)))
        pot = float(group_rng.choice((8, 12, 20, 32)))
        bet_fraction = group_rng.choice((0.25, 0.5, 0.75, 1.0, 1.5))
        bet_size = pot * bet_fraction
        raise_to = (
            bet_size * group_rng.choice((2.0, 3.0))
            if sequential_raise
            else None
        )
        effective_stack = max(2.0 * pot, raise_to or bet_size)
        stacks = (effective_stack, effective_stack)
        split = _group_split(seed, group_index)
        if split not in splits:
            continue
        for family in families:
            family_seed = _derived_seed(seed, group_index, family)
            game = _make_family_game(
                board=board,
                pot=pot,
                stacks=stacks,
                bet_size=bet_size,
                raise_to=raise_to,
                family=family,
                hands_per_player=hands_per_player,
                rng=random.Random(family_seed),
            )
            contexts.append(
                RiverContext(
                    context_id=f"{group_id}-{family}",
                    group_id=group_id,
                    split=split,
                    family=family,
                    seed=family_seed,
                    game=game,
                )
            )
    return tuple(contexts)


def _entropy(distribution: dict[object, float]) -> float:
    return -sum(probability * log(probability) for probability in distribution.values())


def _conditional_shift_features(game: RiverHoldem, player: int) -> tuple[float, float]:
    own_marginal = game.marginal_distribution(player)
    opponent_marginal = game.marginal_distribution(1 - player)
    shifts = {
        hand: distribution_total_variation(
            game.conditional_opponent_distribution(player, hand),
            opponent_marginal,
        )
        for hand in own_marginal
    }
    expected = sum(own_marginal[hand] * shift for hand, shift in shifts.items())
    return expected, max(shifts.values())


def river_context_features(context: RiverContext) -> dict[str, float | int | str]:
    """Return range-available features with no equilibrium-oracle labels."""

    game = context.game
    marginal0 = game.marginal_distribution(0)
    marginal1 = game.marginal_distribution(1)
    joint = game.joint_distribution()
    compatible_edges = len(joint)
    possible_edges = len(marginal0) * len(marginal1)
    expected_shift0, max_shift0 = _conditional_shift_features(game, 0)
    expected_shift1, max_shift1 = _conditional_shift_features(game, 1)
    mutual_information = sum(
        probability
        * log(
            probability
            / (marginal0[deal.player0] * marginal1[deal.player1])
        )
        for deal, probability in joint.items()
    )
    board_ranks = Counter(card // 4 + 2 for card in game.board)
    board_suits = Counter(card % 4 for card in game.board)
    return {
        "family": context.family,
        "pot": game.pot,
        "bet_size": game.bet_size,
        "bet_to_pot": game.bet_size / game.pot,
        "has_raise": int(game.raise_to is not None),
        "raise_to": game.raise_to or 0.0,
        "raise_to_pot": (game.raise_to or 0.0) / game.pot,
        "payoff_span": game.payoff_span,
        "effective_stack_to_pot": min(game.stacks) / game.pot,
        "joint_deals": len(joint),
        "player0_hands": len(marginal0),
        "player1_hands": len(marginal1),
        "compatibility_density": compatible_edges / possible_edges,
        "joint_entropy": _entropy(joint),
        "player0_range_entropy": _entropy(marginal0),
        "player1_range_entropy": _entropy(marginal1),
        "minimum_player0_hand_probability": min(marginal0.values()),
        "minimum_player1_hand_probability": min(marginal1.values()),
        "range_mutual_information": mutual_information,
        "player0_expected_conditional_shift": expected_shift0,
        "player0_max_conditional_shift": max_shift0,
        "player1_expected_conditional_shift": expected_shift1,
        "player1_max_conditional_shift": max_shift1,
        "board_distinct_ranks": len(board_ranks),
        "board_max_rank_multiplicity": max(board_ranks.values()),
        "board_max_suit_count": max(board_suits.values()),
    }


def serialize_river_context(context: RiverContext) -> dict[str, object]:
    """Serialize complete context provenance, including its joint range."""

    game = context.game
    return {
        "context_id": context.context_id,
        "group_id": context.group_id,
        "split": context.split,
        "family": context.family,
        "seed": context.seed,
        "structural_digest": game.structural_digest,
        "provenance_digest": game.provenance_digest,
        "board": [format_card(card) for card in game.board],
        "pot": game.pot,
        "stacks": list(game.stacks),
        "bet_size": game.bet_size,
        "raise_to": game.raise_to,
        "joint_range": [
            {
                "player0": [format_card(card) for card in deal.player0],
                "player1": [format_card(card) for card in deal.player1],
                "probability": probability,
            }
            for deal, probability in game.deals
        ],
        "features": river_context_features(context),
    }
