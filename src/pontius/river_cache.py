"""Strict range-aware cache semantics for exact river games."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Literal

from .evaluation import Policy
from .game import Action
from .river import HoleCards, RiverHoldem, distribution_total_variation

RiverCacheMatch = Literal["exact_strategy_hit", "structural_only", "miss"]


@dataclass(frozen=True, slots=True)
class RiverRangeReuseAssessment:
    """Exact identity and belief-distance diagnostics for one cache lookup."""

    match: RiverCacheMatch
    topology_reusable: bool
    direct_strategy_deployable: bool
    root_joint_total_variation: float | None
    expected_conditional_total_variation: tuple[float, float] | None
    maximum_conditional_total_variation: tuple[float, float] | None
    fixed_policy_value_bound: float | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExploitabilityTransferCertificate:
    """Two-player zero-sum exploitability bound under a chance-belief shift."""

    source_exploitability: float
    root_joint_total_variation: float
    additive_bound: float
    raw_target_upper_bound: float
    capped_target_upper_bound: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def river_cache_match(cached: RiverHoldem, current: RiverHoldem) -> RiverCacheMatch:
    """Classify identity without treating approximate distance as a cache hit."""

    if not isinstance(cached, RiverHoldem) or not isinstance(current, RiverHoldem):
        raise TypeError("river cache matching requires two RiverHoldem games")
    if cached.structural_digest != current.structural_digest:
        return "miss"
    if cached.provenance_digest == current.provenance_digest:
        return "exact_strategy_hit"
    return "structural_only"


def exact_strategy_cache_lookup(
    cached: RiverHoldem,
    current: RiverHoldem,
    cached_policy: Policy,
) -> Policy | None:
    """Return a defensive strategy copy only for exact range provenance."""

    if river_cache_match(cached, current) != "exact_strategy_hit":
        return None
    return {key: dict(distribution) for key, distribution in cached_policy.items()}


def structural_warm_start_hint(
    cached: RiverHoldem,
    current: RiverHoldem,
    cached_policy: Policy,
) -> Policy | None:
    """Return a nondeployable policy hint when immutable topology matches."""

    if river_cache_match(cached, current) == "miss":
        return None
    return {key: dict(distribution) for key, distribution in cached_policy.items()}


def structural_information_schema_lookup(
    cached: RiverHoldem,
    current: RiverHoldem,
    cached_schema: dict[str, tuple[Action, ...]],
) -> dict[str, tuple[Action, ...]] | None:
    """Return immutable topology metadata only when structure is identical."""

    if river_cache_match(cached, current) == "miss":
        return None
    return {key: tuple(actions) for key, actions in cached_schema.items()}


def _conditional_distributions(
    game: RiverHoldem,
    player: int,
) -> tuple[
    dict[HoleCards, float],
    dict[HoleCards, dict[HoleCards, float]],
]:
    marginal: dict[HoleCards, float] = {}
    joint_by_hand: dict[HoleCards, dict[HoleCards, float]] = {}
    for deal, probability in game.deals:
        own_hand = deal.hand(player)
        opponent_hand = deal.hand(1 - player)
        marginal[own_hand] = marginal.get(own_hand, 0.0) + probability
        opponent_weights = joint_by_hand.setdefault(own_hand, {})
        opponent_weights[opponent_hand] = (
            opponent_weights.get(opponent_hand, 0.0) + probability
        )
    conditional = {
        own_hand: {
            opponent_hand: probability / marginal[own_hand]
            for opponent_hand, probability in opponent_weights.items()
        }
        for own_hand, opponent_weights in joint_by_hand.items()
    }
    return marginal, conditional


def _conditional_tv_summary(
    cached: RiverHoldem,
    current: RiverHoldem,
    player: int,
) -> tuple[float, float]:
    cached_marginal, cached_conditionals = _conditional_distributions(cached, player)
    current_marginal, current_conditionals = _conditional_distributions(current, player)
    hands = set(cached_marginal) | set(current_marginal)
    expected = 0.0
    maximum = 0.0
    for hand in hands:
        cached_mass = cached_marginal.get(hand, 0.0)
        current_mass = current_marginal.get(hand, 0.0)
        if cached_mass <= 0.0 or current_mass <= 0.0:
            distance = 1.0
        else:
            distance = distribution_total_variation(
                cached_conditionals[hand],
                current_conditionals[hand],
            )
        expected += 0.5 * (cached_mass + current_mass) * distance
        maximum = max(maximum, distance)
    return expected, maximum


def assess_river_range_reuse(
    cached: RiverHoldem,
    current: RiverHoldem,
) -> RiverRangeReuseAssessment:
    """Measure a belief shift while keeping deployment identity categorical."""

    match = river_cache_match(cached, current)
    if match == "miss":
        return RiverRangeReuseAssessment(
            match=match,
            topology_reusable=False,
            direct_strategy_deployable=False,
            root_joint_total_variation=None,
            expected_conditional_total_variation=None,
            maximum_conditional_total_variation=None,
            fixed_policy_value_bound=None,
        )

    root_tv = cached.total_variation(current)
    summaries = tuple(
        _conditional_tv_summary(cached, current, player)
        for player in range(2)
    )
    return RiverRangeReuseAssessment(
        match=match,
        topology_reusable=True,
        direct_strategy_deployable=(match == "exact_strategy_hit"),
        root_joint_total_variation=root_tv,
        expected_conditional_total_variation=(summaries[0][0], summaries[1][0]),
        maximum_conditional_total_variation=(summaries[0][1], summaries[1][1]),
        fixed_policy_value_bound=cached.fixed_policy_value_bound(current),
    )


def transferred_exploitability_certificate(
    cached: RiverHoldem,
    current: RiverHoldem,
    *,
    source_exploitability: float,
) -> ExploitabilityTransferCertificate:
    """Bound one fixed cached policy's exploitability in the current range.

    For each player, both the fixed-profile value and the best-response value
    can move by at most ``payoff_span * TV``.  In a two-player zero-sum game,
    target exploitability is therefore at most source exploitability plus
    ``2 * payoff_span * TV``.  This certifies a quality ceiling for one fixed
    policy; it neither makes the ranges identical nor certifies strategy
    closeness.  Structural identity is required.
    """

    if not isfinite(source_exploitability) or source_exploitability < 0.0:
        raise ValueError("source_exploitability must be finite and nonnegative")
    if cached.structural_digest != current.structural_digest:
        raise ValueError("exploitability transfer requires identical game structure")
    root_tv = cached.total_variation(current)
    additive = 2.0 * cached.payoff_span * root_tv
    raw_upper = source_exploitability + additive
    return ExploitabilityTransferCertificate(
        source_exploitability=source_exploitability,
        root_joint_total_variation=root_tv,
        additive_bound=additive,
        raw_target_upper_bound=raw_upper,
        capped_target_upper_bound=min(cached.payoff_span, raw_upper),
    )
