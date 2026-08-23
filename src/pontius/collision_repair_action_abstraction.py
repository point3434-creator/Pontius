"""Immutable exact-legal collision-repair v3 source preregistered by ADR-0300."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256

from .legal_action_abstraction import (
    COLLISION_REPAIR_CORE_POT_FRACTIONS,
    AbstractRaiseSize,
    ClipDirection,
    LegalActionAbstraction,
    RaiseSizeOrigin,
    RaiseSizeOriginKind,
    _action_for_kind,
    _project_to_bounds,
    _round_half_up,
    select_collision_repair_overbet,
)
from .no_limit_betting import (
    BettingActionKind,
    LegalBettingDecision,
    NoLimitBettingState,
    raise_to,
)

COLLISION_REPAIR_V3_ALGORITHM_VERSION = "exact-legal-overbet-collision-repair-v3"
ADR0300_COLLISION_REPAIR_SOURCE_ID = "adr-0300-collision-repair-v3"
ADR0300_COLLISION_REPAIR_SOURCE_SHA256 = (
    "ebae17f69c4f37377edf0fb0c55a99049c8688c8517dcbc525230d8e418a811a"
)


@dataclass(frozen=True, slots=True)
class CollisionRepairActionAbstractionSource:
    """Digest-bound v3 source with no mutable table or value-dependent input."""

    source_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("collision-repair source id must be nonempty")

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
            "adaptive_overbet": {
                "collision_anchors": (
                    "minimum",
                    "maximum_contestable",
                    "all_in",
                ),
                "fallback_fraction": (3, 2),
                "primary_fraction": (2, 1),
                "rule": "fallback_only_when_clipped_primary_equals_anchor",
            },
            "adaptive_provenance": (
                "chosen_fraction",
                "collision_repair_triggered",
            ),
            "algorithm_version": COLLISION_REPAIR_V3_ALGORITHM_VERSION,
            "anchors": ("minimum", "maximum_contestable", "all_in"),
            "core_fractions": tuple(
                (value.numerator, value.denominator)
                for value in COLLISION_REPAIR_CORE_POT_FRACTIONS
            ),
            "fraction_base": "pot_after_call",
            "integer_rounding": "nearest_ties_up",
            "maximum_actions": 9,
            "maximum_raises": 7,
            "projection": "adjacent_raise_to_exact_barycentric",
            "source_id": self.source_id,
            "v2_action_set_relation": "superset",
        }
        return json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")

    @property
    def digest(self) -> str:
        return sha256(self.canonical_bytes).hexdigest()

    def build(
        self,
        *,
        betting: NoLimitBettingState,
        decision: LegalBettingDecision,
    ) -> LegalActionAbstraction:
        if not isinstance(betting, NoLimitBettingState):
            raise TypeError("collision-repair source requires exact betting state")
        if not isinstance(decision, LegalBettingDecision):
            raise TypeError("collision-repair source requires exact legal decision")
        if decision != betting.legal_decision():
            raise ValueError("collision-repair source received a stale decision")

        nonraises = tuple(
            _action_for_kind(kind)
            for kind in decision.action_kinds
            if kind is not BettingActionKind.RAISE
        )
        bounds = decision.raise_bounds
        raise_sizes: tuple[AbstractRaiseSize, ...] = ()
        if bounds is not None:
            raw_origins = [
                RaiseSizeOrigin(
                    kind=RaiseSizeOriginKind.MINIMUM,
                    raw_raise_to=bounds.minimum_raise_to,
                    projected_raise_to=bounds.minimum_raise_to,
                    clip=ClipDirection.NONE,
                )
            ]
            base_raise_to = decision.street_contribution + decision.call_amount
            pot_after_call = betting.pot + decision.call_amount
            for fraction in COLLISION_REPAIR_CORE_POT_FRACTIONS:
                raw = base_raise_to + _round_half_up(
                    fraction.fraction * pot_after_call
                )
                projected, clip = _project_to_bounds(
                    raw,
                    bounds.minimum_raise_to,
                    bounds.maximum_raise_to,
                )
                raw_origins.append(
                    RaiseSizeOrigin(
                        kind=RaiseSizeOriginKind.POT_FRACTION,
                        raw_raise_to=raw,
                        projected_raise_to=projected,
                        clip=clip,
                        pot_fraction=fraction,
                    )
                )

            adaptive_fraction, collided = select_collision_repair_overbet(
                betting=betting,
                decision=decision,
            )
            adaptive_raw = base_raise_to + _round_half_up(
                adaptive_fraction.fraction * pot_after_call
            )
            adaptive_projected, adaptive_clip = _project_to_bounds(
                adaptive_raw,
                bounds.minimum_raise_to,
                bounds.maximum_raise_to,
            )
            raw_origins.append(
                RaiseSizeOrigin(
                    kind=RaiseSizeOriginKind.COLLISION_REPAIR_OVERBET,
                    raw_raise_to=adaptive_raw,
                    projected_raise_to=adaptive_projected,
                    clip=adaptive_clip,
                    pot_fraction=adaptive_fraction,
                    collision_repair_triggered=collided,
                )
            )

            contestable, contestable_clip = _project_to_bounds(
                bounds.maximum_contestable_raise_to,
                bounds.minimum_raise_to,
                bounds.maximum_raise_to,
            )
            raw_origins.extend(
                (
                    RaiseSizeOrigin(
                        kind=RaiseSizeOriginKind.MAXIMUM_CONTESTABLE,
                        raw_raise_to=bounds.maximum_contestable_raise_to,
                        projected_raise_to=contestable,
                        clip=contestable_clip,
                    ),
                    RaiseSizeOrigin(
                        kind=RaiseSizeOriginKind.ALL_IN,
                        raw_raise_to=bounds.maximum_raise_to,
                        projected_raise_to=bounds.maximum_raise_to,
                        clip=ClipDirection.NONE,
                    ),
                )
            )
            grouped: dict[int, list[RaiseSizeOrigin]] = {}
            for origin in raw_origins:
                grouped.setdefault(origin.projected_raise_to, []).append(origin)
            raise_sizes = tuple(
                AbstractRaiseSize(
                    action=raise_to(amount),
                    origins=tuple(grouped[amount]),
                )
                for amount in sorted(grouped)
            )

        return LegalActionAbstraction(
            betting=betting,
            decision=decision,
            source_digest=self.digest,
            pot_fractions=COLLISION_REPAIR_CORE_POT_FRACTIONS,
            actions=(*nonraises, *(value.action for value in raise_sizes)),
            raise_sizes=raise_sizes,
        )


__all__ = [
    "ADR0300_COLLISION_REPAIR_SOURCE_ID",
    "ADR0300_COLLISION_REPAIR_SOURCE_SHA256",
    "COLLISION_REPAIR_V3_ALGORITHM_VERSION",
    "CollisionRepairActionAbstractionSource",
]
