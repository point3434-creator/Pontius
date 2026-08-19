"""Deterministic grouped contexts and range shifts for exact multiway river."""

from __future__ import annotations

import hashlib
import random
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from itertools import combinations, product
from math import fsum, log, prod

from .river import Card, HoleCards, distribution_total_variation, evaluate_seven, format_card
from .river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem

MULTIWAY_CONTEXT_FAMILIES = (
    "balanced",
    "polarized",
    "blocker_stress",
    "correlated",
)
CONTEXT_SPLITS = ("development", "validation", "test")


@dataclass(frozen=True, slots=True)
class MultiwayRiverContext:
    context_id: str
    group_id: str
    split: str
    family: str
    seed: int
    game: MultiwayRiverHoldem


@dataclass(frozen=True, slots=True)
class MultiwayRangeTarget:
    target_id: str
    name: str
    kind: str
    source_context_id: str
    game: MultiwayRiverHoldem
    boundary_features: dict[str, float | int | str]


def _derived_seed(seed: int, *parts: object) -> int:
    payload = "|".join((str(seed), *(str(part) for part in parts)))
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


def group_split(seed: int, group_index: int) -> str:
    bucket = _derived_seed(seed, "split", group_index) % 20
    if bucket < 14:
        return "development"
    if bucket < 17:
        return "validation"
    return "test"


def _quantile_targets(count: int, *, polarized: bool) -> tuple[float, ...]:
    if not polarized:
        return tuple((index + 0.5) / count for index in range(count))
    low_count = count // 2
    high_count = count - low_count
    lows = tuple(
        0.03 + 0.17 * (index + 0.5) / low_count
        for index in range(low_count)
    )
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
    half_window = max(12, len(ranked_hands) // 25)
    for target_index, target in enumerate(targets):
        center = round(target * (len(ranked_hands) - 1))
        lower = max(0, center - half_window)
        upper = min(len(ranked_hands), center + half_window + 1)
        candidates = [
            hand for hand in ranked_hands[lower:upper] if hand not in selected
        ]
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


def _compatible_deals(
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
) -> tuple[MultiwayRiverDeal, ...]:
    deals = []
    for hands in product(*hands_by_player):
        cards = tuple(card for hand in hands for card in hand)
        if len(set(cards)) == len(cards):
            deals.append(MultiwayRiverDeal(tuple(hands)))
    return tuple(deals)


def _all_hands_supported(
    hands_by_player: tuple[tuple[HoleCards, ...], ...],
    deals: tuple[MultiwayRiverDeal, ...],
) -> bool:
    return bool(deals) and all(
        any(deal.hand(player) == hand for deal in deals)
        for player, hands in enumerate(hands_by_player)
        for hand in hands
    )


def _range_weights(
    hands: tuple[HoleCards, ...],
    rng: random.Random,
    options: tuple[float, ...],
) -> dict[HoleCards, float]:
    return {hand: rng.choice(options) for hand in hands}


def _make_family_game(
    *,
    board: tuple[Card, ...],
    pot: float,
    stacks: tuple[float, float, float],
    bet_size: float,
    family: str,
    hands_per_player: int,
    weight_options: tuple[float, ...],
    rng: random.Random,
) -> MultiwayRiverHoldem:
    remaining = tuple(card for card in range(52) if card not in set(board))
    ranked_hands = tuple(
        sorted(
            combinations(remaining, 2),
            key=lambda hand: (evaluate_seven((*board, *hand)), hand),
        )
    )
    balanced = _quantile_targets(hands_per_player, polarized=False)
    polarized = _quantile_targets(hands_per_player, polarized=True)

    for _ in range(200):
        hands0 = _select_quantile_hands(
            ranked_hands,
            polarized if family == "polarized" else balanced,
            rng,
        )
        preferred0 = frozenset(card for hand in hands0 for card in hand)
        hands1 = _select_quantile_hands(
            ranked_hands,
            balanced,
            rng,
            preferred_cards=preferred0,
            preferred_count=(hands_per_player + 1) // 2
            if family == "blocker_stress"
            else 0,
        )
        preferred1 = frozenset(
            card for hand in (*hands0, *hands1) for card in hand
        )
        hands2 = _select_quantile_hands(
            ranked_hands,
            polarized if family == "polarized" else balanced,
            rng,
            preferred_cards=preferred1,
            preferred_count=(hands_per_player + 1) // 2
            if family == "blocker_stress"
            else 0,
        )
        hands_by_player = (hands0, hands1, hands2)
        deals = _compatible_deals(hands_by_player)
        if _all_hands_supported(hands_by_player, deals):
            break
    else:
        raise ValueError("could not generate fully supported multiway ranges")

    weights = tuple(
        _range_weights(hands, rng, weight_options) for hands in hands_by_player
    )
    if family != "correlated":
        return MultiwayRiverHoldem.from_independent_ranges(
            board=board,
            pot=pot,
            stacks=stacks,
            bet_size=bet_size,
            player_weights=weights,
        )

    indices = tuple(
        {hand: index for index, hand in enumerate(hands)}
        for hands in hands_by_player
    )
    joint_weights: dict[MultiwayRiverDeal, float] = {}
    for deal in deals:
        deal_indices = tuple(
            indices[player][deal.hand(player)] for player in range(3)
        )
        if len(set(deal_indices)) == 1:
            assortative = 4.0
        elif len(set(deal_indices)) == 2:
            assortative = 2.0
        else:
            assortative = 0.5
        joint_weights[deal] = assortative
        for player in range(3):
            joint_weights[deal] *= weights[player][deal.hand(player)]
    return MultiwayRiverHoldem.from_joint_weights(
        board=board,
        pot=pot,
        stacks=stacks,
        bet_size=bet_size,
        joint_weights=joint_weights,
    )


def generate_multiway_river_contexts(
    *,
    groups: int,
    seed: int,
    hands_per_player: int,
    families: tuple[str, ...],
    splits: tuple[str, ...],
    pot_options: tuple[float, ...],
    bet_to_pot_options: tuple[float, ...],
    effective_stack_to_pot: float,
    weight_options: tuple[float, ...],
) -> tuple[MultiwayRiverContext, ...]:
    if groups <= 0:
        raise ValueError("groups must be positive")
    if not 2 <= hands_per_player <= 7:
        raise ValueError("hands per player must be between two and seven")
    if not families or len(set(families)) != len(families):
        raise ValueError("families must be nonempty and unique")
    unknown_families = set(families) - set(MULTIWAY_CONTEXT_FAMILIES)
    if unknown_families:
        raise ValueError(f"unsupported multiway families: {sorted(unknown_families)!r}")
    if not splits or len(set(splits)) != len(splits):
        raise ValueError("splits must be nonempty and unique")
    unknown_splits = set(splits) - set(CONTEXT_SPLITS)
    if unknown_splits:
        raise ValueError(f"unsupported context splits: {sorted(unknown_splits)!r}")
    if not pot_options or any(pot <= 0.0 for pot in pot_options):
        raise ValueError("pot options must be positive")
    if not bet_to_pot_options or any(value <= 0.0 for value in bet_to_pot_options):
        raise ValueError("bet-to-pot options must be positive")
    if effective_stack_to_pot <= 0.0:
        raise ValueError("effective stack-to-pot must be positive")
    if max(bet_to_pot_options) > effective_stack_to_pot:
        raise ValueError("every bet must fit the effective stack")
    if not weight_options or any(weight <= 0.0 for weight in weight_options):
        raise ValueError("range weights must be positive")

    contexts = []
    for group_index in range(groups):
        split = group_split(seed, group_index)
        if split not in splits:
            continue
        group_id = f"river3-g{group_index:06d}"
        group_rng = random.Random(_derived_seed(seed, "group", group_index))
        board = tuple(sorted(group_rng.sample(range(52), 5)))
        pot = float(group_rng.choice(pot_options))
        bet_size = pot * group_rng.choice(bet_to_pot_options)
        stack = pot * effective_stack_to_pot
        for family in families:
            family_seed = _derived_seed(seed, group_index, family)
            game = _make_family_game(
                board=board,
                pot=pot,
                stacks=(stack, stack, stack),
                bet_size=bet_size,
                family=family,
                hands_per_player=hands_per_player,
                weight_options=weight_options,
                rng=random.Random(family_seed),
            )
            contexts.append(
                MultiwayRiverContext(
                    context_id=f"{group_id}-{family}",
                    group_id=group_id,
                    split=split,
                    family=family,
                    seed=family_seed,
                    game=game,
                )
            )
    return tuple(contexts)


def _entropy(distribution: Mapping[object, float]) -> float:
    return -fsum(
        probability * log(probability)
        for probability in distribution.values()
        if probability > 0.0
    )


def _unconditional_other_distribution(
    game: MultiwayRiverHoldem,
    player: int,
) -> dict[tuple[HoleCards, ...], float]:
    result: dict[tuple[HoleCards, ...], float] = {}
    for deal, probability in game.deals:
        others = tuple(
            hand for seat, hand in enumerate(deal.hands) if seat != player
        )
        result[others] = result.get(others, 0.0) + probability
    return result


def _conditional_shift_by_hand(
    game: MultiwayRiverHoldem,
    player: int,
) -> dict[HoleCards, float]:
    unconditional = _unconditional_other_distribution(game, player)
    return {
        hand: distribution_total_variation(
            game.conditional_other_hands_distribution(player, hand),
            unconditional,
        )
        for hand in game.marginal_distribution(player)
    }


def multiway_context_features(
    context: MultiwayRiverContext,
) -> dict[str, float | int | str]:
    game = context.game
    joint = game.joint_distribution()
    marginals = tuple(
        game.marginal_distribution(player) for player in range(game.num_players)
    )
    possible_deals = 1
    for marginal in marginals:
        possible_deals *= len(marginal)
    mutual_information = fsum(
        probability
        * log(
            probability
            / prod(
                marginals[player][deal.hand(player)]
                for player in range(game.num_players)
            )
        )
        for deal, probability in joint.items()
    )
    board_ranks = Counter(card // 4 + 2 for card in game.board)
    board_suits = Counter(card % 4 for card in game.board)
    result: dict[str, float | int | str] = {
        "pot": game.pot,
        "bet_size": game.bet_size,
        "bet_to_pot": game.bet_size / game.pot,
        "payoff_span": game.payoff_span,
        "effective_stack_to_pot": min(game.stacks) / game.pot,
        "joint_deals": len(joint),
        "possible_cartesian_deals": possible_deals,
        "compatibility_density": len(joint) / possible_deals,
        "joint_entropy": _entropy(joint),
        "range_multi_information": mutual_information,
        "board_distinct_ranks": len(board_ranks),
        "board_max_rank_multiplicity": max(board_ranks.values()),
        "board_max_suit_count": max(board_suits.values()),
    }
    for player, marginal in enumerate(marginals):
        shifts = _conditional_shift_by_hand(game, player)
        result[f"player{player}_hands"] = len(marginal)
        result[f"player{player}_range_entropy"] = _entropy(marginal)
        result[f"player{player}_minimum_hand_probability"] = min(marginal.values())
        result[f"player{player}_expected_conditional_shift"] = fsum(
            marginal[hand] * shift for hand, shift in shifts.items()
        )
        result[f"player{player}_maximum_conditional_shift"] = max(shifts.values())
    return result


def _format_hole(hand: HoleCards) -> str:
    return "".join(format_card(card) for card in hand)


def _range_shift_features(
    source: MultiwayRiverHoldem,
    target: MultiwayRiverHoldem,
    *,
    likelihoods: Mapping[MultiwayRiverDeal, float],
    selected_seat: int | None,
    selected_hand: HoleCards | None,
) -> dict[str, float | int | str]:
    result: dict[str, float | int | str] = {
        "root_total_variation": source.total_variation(target),
        "likelihood_minimum": min(likelihoods.values()),
        "likelihood_maximum": max(likelihoods.values()),
        "likelihood_changed_deal_fraction": sum(
            likelihood != 1.0 for likelihood in likelihoods.values()
        )
        / len(likelihoods),
        "selected_seat": selected_seat if selected_seat is not None else -1,
        "selected_hand": _format_hole(selected_hand) if selected_hand else "none",
        "selected_hand_strength_percentile": 0.0,
        "joint_entropy_change": (
            _entropy(target.joint_distribution()) - _entropy(source.joint_distribution())
        ),
    }
    for player in range(source.num_players):
        source_marginal = source.marginal_distribution(player)
        target_marginal = target.marginal_distribution(player)
        result[f"player{player}_marginal_total_variation"] = (
            distribution_total_variation(source_marginal, target_marginal)
        )
        conditional_changes = {
            hand: distribution_total_variation(
                source.conditional_other_hands_distribution(player, hand),
                target.conditional_other_hands_distribution(player, hand),
            )
            for hand in source_marginal
        }
        result[f"player{player}_expected_conditional_change"] = fsum(
            source_marginal[hand] * change
            for hand, change in conditional_changes.items()
        )
        result[f"player{player}_maximum_conditional_change"] = max(
            conditional_changes.values()
        )
        if player == selected_seat and selected_hand is not None:
            ranked = tuple(
                sorted(
                    source_marginal,
                    key=lambda hand: (evaluate_seven((*source.board, *hand)), hand),
                )
            )
            result["selected_hand_strength_percentile"] = (
                ranked.index(selected_hand) / max(1, len(ranked) - 1)
            )
    return result


def make_multiway_range_targets(
    context: MultiwayRiverContext,
    target_specs: Iterable[Mapping[str, object]],
) -> tuple[MultiwayRangeTarget, ...]:
    source = context.game
    targets = []
    for spec in target_specs:
        name = str(spec["name"])
        kind = str(spec["kind"])
        selected_seat: int | None = None
        selected_hand: HoleCards | None = None
        likelihoods: dict[MultiwayRiverDeal, float] = {}
        if kind == "seat_max_conditional_reweight":
            selected_seat = int(spec["seat"])
            if selected_seat not in range(source.num_players):
                raise ValueError("range target seat is invalid")
            multiplier = float(spec["likelihood_multiplier"])
            if multiplier <= 0.0 or multiplier == 1.0:
                raise ValueError("seat likelihood multiplier must be positive and nonunit")
            shifts = _conditional_shift_by_hand(source, selected_seat)
            selected_hand = max(
                sorted(shifts),
                key=lambda hand: shifts[hand],
            )
            likelihoods = {
                deal: multiplier if deal.hand(selected_seat) == selected_hand else 1.0
                for deal, _ in source.deals
            }
        elif kind == "three_way_strength_alignment":
            minimum = float(spec["minimum_likelihood"])
            maximum = float(spec["maximum_likelihood"])
            if minimum <= 0.0 or maximum <= minimum:
                raise ValueError("alignment likelihood interval is invalid")
            ranked_indices = []
            for player in range(source.num_players):
                hands = tuple(
                    sorted(
                        source.marginal_distribution(player),
                        key=lambda hand: (
                            evaluate_seven((*source.board, *hand)),
                            hand,
                        ),
                    )
                )
                ranked_indices.append(
                    {hand: index for index, hand in enumerate(hands)}
                )
            denominator = max(1, max(len(indices) for indices in ranked_indices) - 1)
            for deal, _ in source.deals:
                indices = tuple(
                    ranked_indices[player][deal.hand(player)]
                    for player in range(source.num_players)
                )
                spread = max(indices) - min(indices)
                likelihoods[deal] = maximum - (maximum - minimum) * (
                    spread / denominator
                )
        else:
            raise ValueError(f"unsupported multiway target kind {kind!r}")

        target = source.with_joint_weights(
            {
                deal: probability * likelihoods[deal]
                for deal, probability in source.deals
            }
        )
        if set(target.joint_distribution()) != set(source.joint_distribution()):
            raise AssertionError("support-preserving target changed deal support")
        if source.total_variation(target) <= 0.0:
            raise ValueError(f"range target {name!r} did not change the distribution")
        targets.append(
            MultiwayRangeTarget(
                target_id=f"{context.context_id}-{name}",
                name=name,
                kind=kind,
                source_context_id=context.context_id,
                game=target,
                boundary_features=_range_shift_features(
                    source,
                    target,
                    likelihoods=likelihoods,
                    selected_seat=selected_seat,
                    selected_hand=selected_hand,
                ),
            )
        )
    return tuple(targets)


def serialize_multiway_context(context: MultiwayRiverContext) -> dict[str, object]:
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
        "joint_range": [
            {
                "hands": [
                    [format_card(card) for card in hand] for hand in deal.hands
                ],
                "probability": probability,
            }
            for deal, probability in game.deals
        ],
        "features": multiway_context_features(context),
    }
