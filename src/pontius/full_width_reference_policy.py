"""Immutable full-width reference policy with exact rational likelihoods.

The policy is intentionally weak: check or call is always its unique modal
action.  Its purpose is to make every exact legal integer raise amount and
every public-action likelihood explicit without consulting a deal, future
board, opponent cards, a model, or an action abstraction.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from math import gcd

import numpy as np
from numpy.typing import NDArray

from .holdem_cards import HoleCards, OneSeatCardState, make_hole
from .immutable_blueprint import (
    BlueprintDecisionKey,
    passive_blueprint_action,
    require_legal_blueprint_action,
)
from .no_limit_betting import (
    SEAT_COUNT,
    BettingAction,
    BettingActionKind,
    BettingStreet,
    LegalBettingDecision,
    NoLimitBettingState,
)

_ALGORITHM_VERSION = "full-width-passive-rational-policy-v1"


def _require_digest(value: object, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True, slots=True)
class RationalActionProbability:
    """One exact action probability with a reduced integer representation."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        for name, value in (
            ("probability numerator", self.numerator),
            ("probability denominator", self.denominator),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
        if self.denominator <= 0:
            raise ValueError("probability denominator must be positive")
        if self.numerator < 0 or self.numerator > self.denominator:
            raise ValueError("action probability must lie in [0, 1]")
        common = gcd(self.numerator, self.denominator)
        object.__setattr__(self, "numerator", self.numerator // common)
        object.__setattr__(self, "denominator", self.denominator // common)

    @property
    def as_float(self) -> float:
        return self.numerator / self.denominator


@dataclass(frozen=True, slots=True)
class _PrivateHandFeatures:
    rank_sum: int
    paired: bool
    suited: bool

    @classmethod
    def from_hand(cls, hand: HoleCards) -> _PrivateHandFeatures:
        first, second = make_hole(*hand)
        first_rank = first // 4 + 2
        second_rank = second // 4 + 2
        return cls(
            rank_sum=first_rank + second_rank,
            paired=first_rank == second_rank,
            suited=first % 4 == second % 4,
        )

    @property
    def pair_bonus(self) -> int:
        return 8 if self.paired else 0

    @property
    def suited_bonus(self) -> int:
        return 2 if self.suited else 0


@dataclass(frozen=True, slots=True)
class FullWidthPolicyDistribution:
    """Implicit exact distribution over every legal integer betting action."""

    key: BlueprintDecisionKey
    decision: LegalBettingDecision
    source_digest: str
    features: _PrivateHandFeatures

    def __post_init__(self) -> None:
        if not isinstance(self.key, BlueprintDecisionKey):
            raise TypeError("policy distribution requires an exact blueprint key")
        if not isinstance(self.decision, LegalBettingDecision):
            raise TypeError("policy distribution requires an exact legal decision")
        _require_digest(self.source_digest, label="policy source digest")
        if not isinstance(self.features, _PrivateHandFeatures):
            raise TypeError("policy distribution requires semantic hand features")
        if self.key.controlled_seat != self.decision.acting_seat:
            raise ValueError("policy key and legal decision name different actors")
        if self.key.street is not self.decision.street:
            raise ValueError("policy key and legal decision name different streets")

    @property
    def passive_weight(self) -> int:
        return (
            64
            + self.features.rank_sum
            + self.features.pair_bonus
            + self.features.suited_bonus
        )

    @property
    def fold_weight(self) -> int:
        return 33 - min(self.features.rank_sum, 28)

    @property
    def raise_base_weight(self) -> int:
        return (
            1
            + self.features.rank_sum
            + self.features.pair_bonus
            + self.features.suited_bonus
        )

    @property
    def raise_support_count(self) -> int:
        bounds = self.decision.raise_bounds
        if bounds is None:
            return 0
        return bounds.maximum_raise_to - bounds.minimum_raise_to + 1

    @property
    def total_raise_weight(self) -> int:
        count = self.raise_support_count
        if count == 0:
            return 0
        cycles, remainder = divmod(count, 5)
        residue_sum = cycles * 10 + remainder * (remainder - 1) // 2
        return count * self.raise_base_weight + residue_sum

    @property
    def total_weight(self) -> int:
        total = self.passive_weight + self.total_raise_weight
        if self.decision.can_fold:
            total += self.fold_weight
        return total

    @property
    def exact_action_count(self) -> int:
        nonraise = len(
            tuple(
                kind
                for kind in self.decision.action_kinds
                if kind is not BettingActionKind.RAISE
            )
        )
        return nonraise + self.raise_support_count

    def weight(self, action: BettingAction) -> int:
        require_legal_blueprint_action(action, self.decision)
        if action.kind is BettingActionKind.FOLD:
            return self.fold_weight
        if action.kind in (BettingActionKind.CHECK, BettingActionKind.CALL):
            return self.passive_weight
        bounds = self.decision.raise_bounds
        assert bounds is not None
        assert action.raise_to is not None
        return self.raise_base_weight + (
            (action.raise_to - bounds.minimum_raise_to) % 5
        )

    def probability(self, action: BettingAction) -> RationalActionProbability:
        return RationalActionProbability(self.weight(action), self.total_weight)

    @property
    def selected_action(self) -> BettingAction:
        passive = passive_blueprint_action(self.decision)
        passive_weight = self.weight(passive)
        if self.decision.can_fold and passive_weight <= self.fold_weight:
            raise AssertionError("reference policy passive action is not modal")
        if self.raise_support_count and passive_weight <= self.raise_base_weight + 4:
            raise AssertionError("reference policy raise unexpectedly defeats passive")
        return passive

    @property
    def digest(self) -> str:
        payload = {
            "exact_action_count": self.exact_action_count,
            "features": {
                "paired": self.features.paired,
                "rank_sum": self.features.rank_sum,
                "suited": self.features.suited,
            },
            "key_digest": self.key.digest,
            "source_digest": self.source_digest,
            "total_weight": self.total_weight,
            "version": "full-width-policy-distribution-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class BlueprintActionLikelihood:
    """Exact action likelihood across one canonical full private-hand axis."""

    actor_seat: int
    street: BettingStreet
    observed_action: BettingAction
    hand_axis: tuple[HoleCards, ...]
    probabilities: tuple[RationalActionProbability, ...]
    key_digests: tuple[str, ...]
    source_digest: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.actor_seat, bool)
            or not isinstance(self.actor_seat, int)
            or self.actor_seat not in range(SEAT_COUNT)
        ):
            raise ValueError("likelihood actor must identify one of six seats")
        if not isinstance(self.street, BettingStreet):
            raise TypeError("likelihood street must be canonical")
        if not isinstance(self.observed_action, BettingAction):
            raise TypeError("likelihood observed action must be semantic")
        if not isinstance(self.hand_axis, tuple) or not self.hand_axis:
            raise TypeError("likelihood hand axis must be a nonempty immutable tuple")
        canonical = tuple(make_hole(*hand) for hand in self.hand_axis)
        if canonical != self.hand_axis or len(set(canonical)) != len(canonical):
            raise ValueError("likelihood hand axis must be canonical and unique")
        if not isinstance(self.probabilities, tuple) or len(self.probabilities) != len(
            self.hand_axis
        ):
            raise ValueError("likelihood probabilities have the wrong hand width")
        if any(
            not isinstance(probability, RationalActionProbability)
            for probability in self.probabilities
        ):
            raise TypeError("likelihood contains a non-rational probability")
        if not any(probability.numerator > 0 for probability in self.probabilities):
            raise ValueError("observed action has zero probability on the hand axis")
        if not isinstance(self.key_digests, tuple) or len(self.key_digests) != len(
            self.hand_axis
        ):
            raise ValueError("likelihood key provenance has the wrong hand width")
        for digest in self.key_digests:
            _require_digest(digest, label="likelihood key digest")
        _require_digest(self.source_digest, label="likelihood source digest")

    def as_float64(self) -> NDArray[np.float64]:
        values = np.ascontiguousarray(
            [probability.as_float for probability in self.probabilities],
            dtype=np.float64,
        )
        if not np.all(np.isfinite(values)) or np.any(values < 0.0) or np.any(
            values > 1.0
        ):
            raise ArithmeticError("rational likelihood did not convert to probability")
        if any(
            probability.numerator > 0 and value == 0.0
            for probability, value in zip(self.probabilities, values, strict=True)
        ):
            raise ArithmeticError("positive rational likelihood underflowed to zero")
        values.flags.writeable = False
        return values

    @property
    def digest(self) -> str:
        payload = {
            "actor_seat": self.actor_seat,
            "hand_axis": self.hand_axis,
            "key_digests": self.key_digests,
            "observed_action": {
                "kind": self.observed_action.kind.value,
                "raise_to": self.observed_action.raise_to,
            },
            "probabilities": tuple(
                (probability.numerator, probability.denominator)
                for probability in self.probabilities
            ),
            "source_digest": self.source_digest,
            "street": self.street.value,
            "version": "blueprint-action-likelihood-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class ImmutableFullWidthReferencePolicy:
    """Digest-bound total reference policy with no private source state."""

    source_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("full-width policy source id must be nonempty")

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
            "algorithm_version": _ALGORITHM_VERSION,
            "fold_weight": "33-min(rank_sum,28)",
            "passive_weight": "64+rank_sum+8*pair+2*suited",
            "raise_weight": (
                "1+rank_sum+8*pair+2*suited+"
                "((raise_to-minimum_raise_to)%5)"
            ),
            "source_id": self.source_id,
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

    def distribution_for(
        self,
        *,
        cards: OneSeatCardState,
        betting: NoLimitBettingState,
        decision: LegalBettingDecision,
    ) -> FullWidthPolicyDistribution:
        key = BlueprintDecisionKey.from_state(
            cards=cards,
            betting=betting,
            decision=decision,
        )
        return FullWidthPolicyDistribution(
            key=key,
            decision=decision,
            source_digest=self.digest,
            features=_PrivateHandFeatures.from_hand(cards.private_hand),
        )

    def likelihood_for_axis(
        self,
        *,
        visible_cards: OneSeatCardState,
        actor_seat: int,
        hand_axis: tuple[HoleCards, ...],
        betting: NoLimitBettingState,
        decision: LegalBettingDecision,
        observed_action: BettingAction,
    ) -> BlueprintActionLikelihood:
        if betting.acting_seat != actor_seat or decision.acting_seat != actor_seat:
            raise ValueError("likelihood actor is not the public acting seat")
        require_legal_blueprint_action(observed_action, decision)
        probabilities = []
        key_digests = []
        for hand in hand_axis:
            hypothetical_cards = OneSeatCardState(
                controlled_seat=actor_seat,
                private_hand=hand,
                street=visible_cards.street,
                board=visible_cards.board,
            )
            distribution = self.distribution_for(
                cards=hypothetical_cards,
                betting=betting,
                decision=decision,
            )
            probabilities.append(distribution.probability(observed_action))
            key_digests.append(distribution.key.digest)
        return BlueprintActionLikelihood(
            actor_seat=actor_seat,
            street=decision.street,
            observed_action=observed_action,
            hand_axis=hand_axis,
            probabilities=tuple(probabilities),
            key_digests=tuple(key_digests),
            source_digest=self.digest,
        )


__all__ = [
    "BlueprintActionLikelihood",
    "FullWidthPolicyDistribution",
    "ImmutableFullWidthReferencePolicy",
    "RationalActionProbability",
]
