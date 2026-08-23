"""Exact-rational same-ceiling capacity-filling action source from ADR-0305."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256

from .collision_repair_action_abstraction import (
    ADR0300_COLLISION_REPAIR_SOURCE_ID,
    ADR0300_COLLISION_REPAIR_SOURCE_SHA256,
    CollisionRepairActionAbstractionSource,
)
from .legal_action_abstraction import (
    AbstractRaiseSize,
    ClipDirection,
    LegalActionAbstraction,
    LegalActionAbstractionSnapshot,
    OffTreeActionProjection,
    PotFraction,
    RaiseSizeOrigin,
    RaiseSizeOriginKind,
    select_capacity_filling_pot_odds_refill,
)
from .no_limit_betting import (
    BettingAction,
    BettingActionKind,
    LegalBettingDecision,
    NoLimitBettingState,
    raise_to,
)

CAPACITY_FILLING_ALGORITHM_VERSION = (
    "exact-rational-capacity-filling-pot-odds-v4"
)
ADR0305_CAPACITY_FILLING_SOURCE_ID = "adr-0305-capacity-filling-pot-odds-v4"
ADR0305_CAPACITY_FILLING_SOURCE_SHA256 = (
    "37824e44b7793b10b081957fc8be387bdca5c565b4bfe2386ca13f7e1c785c8b"
)
ADR0305_MAXIMUM_RAISES = 7
ADR0305_MAXIMUM_ACTIONS = 9


@dataclass(frozen=True, slots=True)
class CapacityFillingActionAbstraction:
    """A generic legal abstraction with an exact verified v4 parent/refill chain."""

    legal_abstraction: LegalActionAbstraction

    def __post_init__(self) -> None:
        if not isinstance(self.legal_abstraction, LegalActionAbstraction):
            raise TypeError("capacity filling requires a legal abstraction")
        abstraction = self.legal_abstraction
        if abstraction.source_digest != ADR0305_CAPACITY_FILLING_SOURCE_SHA256:
            raise ValueError("capacity-filling abstraction source digest drifted")
        if (
            abstraction.capacity_filling_parent_source_digest
            != ADR0300_COLLISION_REPAIR_SOURCE_SHA256
        ):
            raise ValueError("capacity-filling abstraction names the wrong parent")

        parent = CollisionRepairActionAbstractionSource(
            source_id=ADR0300_COLLISION_REPAIR_SOURCE_ID
        ).build(
            betting=abstraction.betting,
            decision=abstraction.decision,
        )
        if not set(parent.actions).issubset(abstraction.actions):
            raise ValueError("capacity-filling abstraction dropped a parent action")
        parent_by_amount = {
            int(value.action.raise_to): value.origins for value in parent.raise_sizes
        }
        for value in abstraction.raise_sizes:
            amount = int(value.action.raise_to)
            inherited = tuple(
                origin
                for origin in value.origins
                if origin.kind
                is not RaiseSizeOriginKind.CAPACITY_FILLING_POT_ODDS
            )
            if amount in parent_by_amount and inherited != parent_by_amount[amount]:
                raise ValueError("capacity-filling abstraction changed parent provenance")
            if amount not in parent_by_amount and inherited:
                raise ValueError("capacity-filling abstraction invented parent provenance")

        bounds = abstraction.decision.raise_bounds
        exact_raise_count = (
            0
            if bounds is None
            else bounds.maximum_raise_to - bounds.minimum_raise_to + 1
        )
        target_raise_count = min(ADR0305_MAXIMUM_RAISES, exact_raise_count)
        if len(abstraction.raise_sizes) != target_raise_count:
            raise ValueError("capacity-filling abstraction did not fill exact capacity")
        if len(abstraction.actions) > ADR0305_MAXIMUM_ACTIONS:
            raise ValueError("capacity-filling abstraction exceeds its action ceiling")

    @property
    def betting(self) -> NoLimitBettingState:
        return self.legal_abstraction.betting

    @property
    def decision(self) -> LegalBettingDecision:
        return self.legal_abstraction.decision

    @property
    def source_digest(self) -> str:
        return self.legal_abstraction.source_digest

    @property
    def pot_fractions(self) -> tuple[PotFraction, ...]:
        return self.legal_abstraction.pot_fractions

    @property
    def actions(self) -> tuple[BettingAction, ...]:
        return self.legal_abstraction.actions

    @property
    def raise_sizes(self) -> tuple[AbstractRaiseSize, ...]:
        return self.legal_abstraction.raise_sizes

    @property
    def exact_action_count(self) -> int:
        return self.legal_abstraction.exact_action_count

    @property
    def digest(self) -> str:
        return self.legal_abstraction.digest

    @property
    def refill_origins(self) -> tuple[RaiseSizeOrigin, ...]:
        return tuple(
            sorted(
                (
                    origin
                    for value in self.raise_sizes
                    for origin in value.origins
                    if origin.kind
                    is RaiseSizeOriginKind.CAPACITY_FILLING_POT_ODDS
                ),
                key=lambda origin: int(origin.capacity_refill_rank),
            )
        )

    def project(self, action: BettingAction) -> OffTreeActionProjection:
        return self.legal_abstraction.project(action)

    def snapshot(self) -> LegalActionAbstractionSnapshot:
        return self.legal_abstraction.snapshot()


@dataclass(frozen=True, slots=True)
class CapacityFillingActionAbstractionSource:
    """Digest-bound v4 source with no value, panel, or chip-depth scan."""

    source_id: str

    def __post_init__(self) -> None:
        if self.source_id != ADR0305_CAPACITY_FILLING_SOURCE_ID:
            raise ValueError("capacity-filling source id differs from ADR-0305")

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
            "algorithm_version": CAPACITY_FILLING_ALGORITHM_VERSION,
            "anchors": (
                "exact_minimum_raise_to",
                "exact_acting_seat_all_in_raise_to",
            ),
            "construction": {
                "candidate_derivation": (
                    "exact_inverse_midpoint_floor_ceiling_only"
                ),
                "coordinate": "increment/(pot_after_call+2*increment)",
                "global_objective": "maximum_nearest_retained_coordinate_distance",
                "interval_enumeration": False,
                "tie_break": "smaller_raise_to",
            },
            "maximum_actions": ADR0305_MAXIMUM_ACTIONS,
            "maximum_raises": ADR0305_MAXIMUM_RAISES,
            "nonraises": "all_exact_parent_nonraises",
            "parent_source_id": ADR0300_COLLISION_REPAIR_SOURCE_ID,
            "parent_source_sha256": ADR0300_COLLISION_REPAIR_SOURCE_SHA256,
            "projection": "adjacent_raise_to_exact_barycentric",
            "provenance": (
                "refill_rank",
                "left_raise_to",
                "right_raise_to",
                "exact_pot_odds_distance",
            ),
            "source_id": self.source_id,
            "target_raise_count": "min(7,exact_legal_integer_raise_count)",
            "v3_action_set_relation": "superset",
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
    ) -> CapacityFillingActionAbstraction:
        if not isinstance(betting, NoLimitBettingState):
            raise TypeError("capacity-filling source requires exact betting state")
        if not isinstance(decision, LegalBettingDecision):
            raise TypeError("capacity-filling source requires exact legal decision")
        if decision != betting.legal_decision():
            raise ValueError("capacity-filling source received a stale decision")

        parent = CollisionRepairActionAbstractionSource(
            source_id=ADR0300_COLLISION_REPAIR_SOURCE_ID
        ).build(
            betting=betting,
            decision=decision,
        )
        grouped = {
            int(value.action.raise_to): list(value.origins)
            for value in parent.raise_sizes
        }
        bounds = decision.raise_bounds
        if bounds is not None:
            exact_raise_count = (
                bounds.maximum_raise_to - bounds.minimum_raise_to + 1
            )
            target_raise_count = min(ADR0305_MAXIMUM_RAISES, exact_raise_count)
            retained = tuple(sorted(grouped))
            refill_rank = 1
            while len(retained) < target_raise_count:
                selection = select_capacity_filling_pot_odds_refill(
                    betting=betting,
                    decision=decision,
                    retained_raise_to=retained,
                )
                if selection.raise_to in grouped:
                    raise AssertionError("capacity refill repeated a retained raise")
                grouped[selection.raise_to] = [
                    RaiseSizeOrigin(
                        kind=RaiseSizeOriginKind.CAPACITY_FILLING_POT_ODDS,
                        raw_raise_to=selection.raise_to,
                        projected_raise_to=selection.raise_to,
                        clip=ClipDirection.NONE,
                        capacity_refill_rank=refill_rank,
                        capacity_refill=selection,
                    )
                ]
                retained = tuple(sorted(grouped))
                refill_rank += 1

        raise_sizes = tuple(
            AbstractRaiseSize(
                action=raise_to(amount),
                origins=tuple(grouped[amount]),
            )
            for amount in sorted(grouped)
        )
        nonraises = tuple(
            action
            for action in parent.actions
            if action.kind is not BettingActionKind.RAISE
        )
        legal_abstraction = LegalActionAbstraction(
            betting=betting,
            decision=decision,
            source_digest=self.digest,
            pot_fractions=parent.pot_fractions,
            actions=(*nonraises, *(value.action for value in raise_sizes)),
            raise_sizes=raise_sizes,
            capacity_filling_parent_source_digest=parent.source_digest,
        )
        return CapacityFillingActionAbstraction(
            legal_abstraction=legal_abstraction,
        )


__all__ = [
    "ADR0305_CAPACITY_FILLING_SOURCE_ID",
    "ADR0305_CAPACITY_FILLING_SOURCE_SHA256",
    "ADR0305_MAXIMUM_ACTIONS",
    "ADR0305_MAXIMUM_RAISES",
    "CAPACITY_FILLING_ALGORITHM_VERSION",
    "CapacityFillingActionAbstraction",
    "CapacityFillingActionAbstractionSource",
]
