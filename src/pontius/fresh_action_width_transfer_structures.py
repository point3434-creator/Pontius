"""Value-free untouched transfer population for ADR-0323 action-width research.

The transfer seed is derived only from the committed pre-value ADR-0337
mechanism source boundary.  This module constructs deterministic h4 river
contexts, rederives every legal raise from the betting kernel, and rejects the
entire pool if it has a semantic counterpart in either development population.
It imports no qualification, teacher, greedy result, solver, preparation, or
action-emission owner and opens no transfer value.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from math import comb
from types import MappingProxyType

from .fresh_action_width_nonreplay import build_adr0331_nonreplay_pool
from .fresh_action_width_nonreplay_seal import ADR0331_POPULATION_POOL_SHA256
from .fresh_action_width_structures import (
    ADR0323_DEVELOPMENT_CONTEXT_COUNT,
    ADR0323_GENERATOR_VERSION,
    ADR0323_MINIMUM_FULL_RAISE,
    ADR0323_POTS,
    ADR0323_PRIVATE_RANGE_WIDTH,
    ADR0323_RAISE_WIDTHS,
    ADR0323_STACKS,
    ADR0323_STRUCTURAL_FILTER_VERSION,
    ActionWidthSubsetWorkLedger,
    FreshActionWidthContext,
    _DigestStream,
    _kernel_raise_universe,
    _private_pairs,
    _river_opening_state,
    _showdown_signs,
    _shuffled_deck,
    _structurally_admissible,
    build_adr0323_development_pool,
    transfer_seed_from_mechanism_commit,
)
from .fresh_action_width_structures_seal import ADR0323_DEVELOPMENT_POOL_SHA256


ADR0339_MECHANISM_SOURCE_COMMIT = "b4339f33dec768052208b102ad8a9f510666f40d"
ADR0339_TRANSFER_SEED = transfer_seed_from_mechanism_commit(
    ADR0339_MECHANISM_SOURCE_COMMIT
)
ADR0339_TRANSFER_SEED_SHA256 = (
    "3256cfab86ce902ccaa8acc010c1e8292e832b1eb4526d8d505e7bb0f108df22"
)
ADR0339_TRANSFER_CONTEXT_COUNT = ADR0323_DEVELOPMENT_CONTEXT_COUNT

# ADR-0312's exhaustive finite-inventory control is the maintained historical
# authority.  Its 64 then-fresh audit contexts are kept separate so neither
# population can disappear behind an updated aggregate count.
ADR0339_MAINTAINED_PRIOR_CONTEXT_COUNT = 988
ADR0339_MAINTAINED_PRIOR_INVENTORY_SHA256 = (
    "8109c680918c689ca603a26cc19c846f3933cfd448f6c019da4755d08ae6155b"
)
ADR0339_ADR0311_AUDIT_CONTEXT_COUNT = 64
ADR0339_ADR0311_AUDIT_INVENTORY_SHA256 = (
    "2553bbc6023eaebdf296d83b5ee130755934b433af3138c5239c7e8f9f26cbb5"
)

_PRIVATE_RANGE_WIDTH = ADR0323_PRIVATE_RANGE_WIDTH.count
_POOL_VERSION = "adr0339-fresh-action-width-transfer-pool-v1"
_SEMANTIC_INVENTORY_VERSION = "reduced-river-context-semantic-inventory-v1"

_ADR0339_TRANSFER_PROTOCOL_PAYLOAD = {
    "adr0311_audit_context_count": ADR0339_ADR0311_AUDIT_CONTEXT_COUNT,
    "adr0311_audit_inventory_sha256": (
        ADR0339_ADR0311_AUDIT_INVENTORY_SHA256
    ),
    "development_pool_sha256": ADR0323_DEVELOPMENT_POOL_SHA256,
    "generator_version": ADR0323_GENERATOR_VERSION,
    "inventory_raise_to_conversion": (
        "raise-to-total-minus-street-contribution-minus-call-amount"
    ),
    "maintained_prior_context_count": ADR0339_MAINTAINED_PRIOR_CONTEXT_COUNT,
    "maintained_prior_inventory_sha256": (
        ADR0339_MAINTAINED_PRIOR_INVENTORY_SHA256
    ),
    "mechanism_source_commit": ADR0339_MECHANISM_SOURCE_COMMIT,
    "minimum_full_raise": ADR0323_MINIMUM_FULL_RAISE,
    "nonreplay_pool_sha256": ADR0331_POPULATION_POOL_SHA256,
    "pool_version": _POOL_VERSION,
    "pots": ADR0323_POTS,
    "private_range_width": ADR0323_PRIVATE_RANGE_WIDTH.count,
    "raise_widths": tuple(width.count for width in ADR0323_RAISE_WIDTHS),
    "semantic_inventory_version": _SEMANTIC_INVENTORY_VERSION,
    "stacks": ADR0323_STACKS,
    "structural_filter_version": ADR0323_STRUCTURAL_FILTER_VERSION,
    "transfer_context_count": ADR0339_TRANSFER_CONTEXT_COUNT,
    "transfer_seed": ADR0339_TRANSFER_SEED,
    "transfer_seed_sha256": ADR0339_TRANSFER_SEED_SHA256,
    "version": "adr0339-value-free-transfer-structure-protocol-v1",
}
ADR0339_TRANSFER_PROTOCOL = MappingProxyType(_ADR0339_TRANSFER_PROTOCOL_PAYLOAD)
ADR0339_TRANSFER_PROTOCOL_SHA256 = sha256(
    json.dumps(
        _ADR0339_TRANSFER_PROTOCOL_PAYLOAD,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
).hexdigest()


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_nonnegative_chips(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer chip count")
    if value < 0:
        raise ValueError(f"{label} must be nonnegative")
    return value


@dataclass(frozen=True, slots=True)
class SemanticInventoryBetIncrement:
    """Historical reduced wager, never a raise-to total by coincidence."""

    chips: int

    def __post_init__(self) -> None:
        chips = _require_nonnegative_chips(
            self.chips,
            label="semantic-inventory bet increment",
        )
        if chips <= 0:
            raise ValueError("semantic-inventory bet increment must be positive")
        object.__setattr__(self, "chips", chips)


def semantic_inventory_bet_increment(
    *,
    raise_to_total_chips: int,
    street_contribution_chips: int,
    call_amount_chips: int,
) -> SemanticInventoryBetIncrement:
    """Convert one nominal raise-to total to the historical reduced wager."""

    raise_to = _require_nonnegative_chips(
        raise_to_total_chips,
        label="semantic-inventory raise-to total",
    )
    street_contribution = _require_nonnegative_chips(
        street_contribution_chips,
        label="semantic-inventory street contribution",
    )
    call_amount = _require_nonnegative_chips(
        call_amount_chips,
        label="semantic-inventory call amount",
    )
    return SemanticInventoryBetIncrement(
        raise_to - street_contribution - call_amount
    )


def _fraction_payload(value: Fraction) -> tuple[int, int]:
    if not isinstance(value, Fraction):
        raise TypeError("semantic inventory requires exact fractions")
    return value.numerator, value.denominator


def action_width_context_semantic_inventory_key(
    context: FreshActionWidthContext,
) -> str:
    """Return the historical label-free river-context inventory key."""

    if not isinstance(context, FreshActionWidthContext):
        raise TypeError("semantic inventory key requires an action-width context")
    decision = context.betting.legal_decision()
    minimum_bet_increment = semantic_inventory_bet_increment(
        raise_to_total_chips=context.complete_raise_to_totals[0].chips,
        street_contribution_chips=decision.street_contribution,
        call_amount_chips=decision.call_amount,
    )
    payload = {
        "board": context.board,
        "joint_probabilities": tuple(
            tuple(_fraction_payload(value) for value in row)
            for row in context.joint_probabilities
        ),
        "minimum_bet": minimum_bet_increment.chips,
        "opener_hands": context.opener_hands,
        "pot": context.betting.pot,
        "responder_hands": context.responder_hands,
        "stack": context.betting.stacks[0],
    }
    return json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def action_width_context_semantic_inventory_sha256(
    contexts: tuple[FreshActionWidthContext, ...],
) -> str:
    """Hash a finite label-free context inventory in canonical sorted order."""

    if not isinstance(contexts, tuple) or any(
        not isinstance(context, FreshActionWidthContext) for context in contexts
    ):
        raise TypeError("semantic inventory requires immutable action-width contexts")
    encoded = json.dumps(
        sorted(action_width_context_semantic_inventory_key(context) for context in contexts),
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class FreshActionWidthTransferPool:
    """One exact, unopened transfer population and its development exclusions."""

    seed: str
    mechanism_source_commit: str
    generator_version: str
    structural_filter_version: str
    candidate_attempts: int
    development_pool_sha256: str
    development_context_semantic_digests: tuple[str, ...]
    nonreplay_pool_sha256: str
    nonreplay_context_semantic_digests: tuple[str, ...]
    contexts: tuple[FreshActionWidthContext, ...]

    def __post_init__(self) -> None:
        if self.mechanism_source_commit != ADR0339_MECHANISM_SOURCE_COMMIT:
            raise ValueError("transfer mechanism source commit drifted")
        if self.seed != ADR0339_TRANSFER_SEED:
            raise ValueError("transfer seed differs from the preregistered derivation")
        if sha256(self.seed.encode("ascii")).hexdigest() != ADR0339_TRANSFER_SEED_SHA256:
            raise AssertionError("transfer seed digest drifted")
        if self.generator_version != ADR0323_GENERATOR_VERSION:
            raise ValueError("transfer generator differs from ADR-0323")
        if self.structural_filter_version != ADR0323_STRUCTURAL_FILTER_VERSION:
            raise ValueError("transfer structural filter differs from ADR-0323")
        if (
            isinstance(self.candidate_attempts, bool)
            or not isinstance(self.candidate_attempts, int)
            or self.candidate_attempts < ADR0339_TRANSFER_CONTEXT_COUNT
        ):
            raise ValueError("transfer candidate-attempt count is invalid")

        if self.development_pool_sha256 != ADR0323_DEVELOPMENT_POOL_SHA256:
            raise ValueError("transfer development-pool identity drifted")
        if self.nonreplay_pool_sha256 != ADR0331_POPULATION_POOL_SHA256:
            raise ValueError("transfer non-replay-pool identity drifted")
        for label, digests in (
            ("development", self.development_context_semantic_digests),
            ("non-replay", self.nonreplay_context_semantic_digests),
        ):
            if not isinstance(digests, tuple) or len(digests) != 96:
                raise TypeError(f"transfer must bind all 96 {label} contexts")
            for digest in digests:
                _require_digest(digest, label=f"{label} context semantic identity")
            if len(set(digests)) != len(digests):
                raise ValueError(f"transfer {label} exclusion repeats an identity")

        development = build_adr0323_development_pool()
        nonreplay = build_adr0331_nonreplay_pool()
        if (
            development.digest != self.development_pool_sha256
            or tuple(context.semantic_digest for context in development.contexts)
            != self.development_context_semantic_digests
        ):
            raise ValueError("transfer does not bind the complete development pool")
        if (
            nonreplay.digest != self.nonreplay_pool_sha256
            or tuple(context.semantic_digest for context in nonreplay.contexts)
            != self.nonreplay_context_semantic_digests
        ):
            raise ValueError("transfer does not bind the complete non-replay pool")

        if (
            not isinstance(self.contexts, tuple)
            or len(self.contexts) != ADR0339_TRANSFER_CONTEXT_COUNT
            or any(
                not isinstance(context, FreshActionWidthContext)
                for context in self.contexts
            )
        ):
            raise TypeError("transfer pool must contain 96 semantic contexts")
        expected_ids = tuple(
            f"adr0339-transfer-{index:03d}"
            for index in range(ADR0339_TRANSFER_CONTEXT_COUNT)
        )
        if tuple(context.context_id for context in self.contexts) != expected_ids:
            raise ValueError("transfer context ids or ordering drifted")

        semantic_digests = tuple(context.semantic_digest for context in self.contexts)
        if len(set(semantic_digests)) != len(semantic_digests):
            raise ValueError("transfer pool repeats a semantic context")
        if not set(semantic_digests).isdisjoint(
            self.development_context_semantic_digests
        ):
            raise ValueError("transfer pool overlaps the ADR-0323 development pool")
        if not set(semantic_digests).isdisjoint(
            self.nonreplay_context_semantic_digests
        ):
            raise ValueError("transfer pool overlaps the ADR-0331 development pool")

        inventory_keys = tuple(
            action_width_context_semantic_inventory_key(context)
            for context in self.contexts
        )
        if len(set(inventory_keys)) != len(inventory_keys):
            raise ValueError("transfer pool repeats a label-free inventory context")
        excluded_inventory_keys = {
            action_width_context_semantic_inventory_key(context)
            for context in (*development.contexts, *nonreplay.contexts)
        }
        if not set(inventory_keys).isdisjoint(excluded_inventory_keys):
            raise ValueError("transfer pool has a development semantic counterpart")

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
            "candidate_attempts": self.candidate_attempts,
            "context_ids": tuple(context.context_id for context in self.contexts),
            "context_inventory_sha256": (
                action_width_context_semantic_inventory_sha256(self.contexts)
            ),
            "context_semantic_digests": tuple(
                context.semantic_digest for context in self.contexts
            ),
            "development_context_semantic_digests": (
                self.development_context_semantic_digests
            ),
            "development_pool_sha256": self.development_pool_sha256,
            "generator_version": self.generator_version,
            "mechanism_source_commit": self.mechanism_source_commit,
            "nonreplay_context_semantic_digests": (
                self.nonreplay_context_semantic_digests
            ),
            "nonreplay_pool_sha256": self.nonreplay_pool_sha256,
            "protocol_sha256": ADR0339_TRANSFER_PROTOCOL_SHA256,
            "seed": self.seed,
            "structural_filter_version": self.structural_filter_version,
            "version": _POOL_VERSION,
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

    @property
    def subset_work_ledger(self) -> ActionWidthSubsetWorkLedger:
        counts = tuple(
            (
                width,
                sum(
                    comb(
                        len(context.complete_raise_to_totals) - 2,
                        width.count - 2,
                    )
                    for context in self.contexts
                ),
            )
            for width in ADR0323_RAISE_WIDTHS
        )
        return ActionWidthSubsetWorkLedger(
            context_count=len(self.contexts),
            subset_counts_by_raise_width=counts,
            total_subset_count=sum(count for _, count in counts),
        )


def build_adr0339_transfer_pool() -> FreshActionWidthTransferPool:
    """Construct the first 96 admissible contexts, then fail on any overlap."""

    development = build_adr0323_development_pool()
    nonreplay = build_adr0331_nonreplay_pool()
    if development.digest != ADR0323_DEVELOPMENT_POOL_SHA256:
        raise RuntimeError("sealed ADR-0323 development population did not reproduce")
    if nonreplay.digest != ADR0331_POPULATION_POOL_SHA256:
        raise RuntimeError("sealed ADR-0331 development population did not reproduce")

    stream = _DigestStream(ADR0339_TRANSFER_SEED)
    contexts: list[FreshActionWidthContext] = []
    attempts = 0
    while len(contexts) < ADR0339_TRANSFER_CONTEXT_COUNT:
        attempts += 1
        deck = _shuffled_deck(stream)
        board = deck[:5]
        opener_hands = _private_pairs(deck[5:13])
        responder_hands = _private_pairs(deck[13:21])
        signs = _showdown_signs(board, opener_hands, responder_hands)
        if not _structurally_admissible(signs):
            continue
        pot = ADR0323_POTS[stream.randbelow(len(ADR0323_POTS))]
        effective_stack = ADR0323_STACKS[stream.randbelow(len(ADR0323_STACKS))]
        weights = tuple(
            1 + stream.randbelow(9)
            for _ in range(_PRIVATE_RANGE_WIDTH * _PRIVATE_RANGE_WIDTH)
        )
        denominator = sum(weights)
        probabilities = tuple(
            tuple(
                Fraction(
                    weights[row * _PRIVATE_RANGE_WIDTH + column],
                    denominator,
                )
                for column in range(_PRIVATE_RANGE_WIDTH)
            )
            for row in range(_PRIVATE_RANGE_WIDTH)
        )
        state = _river_opening_state(pot=pot, effective_stack=effective_stack)
        contexts.append(
            FreshActionWidthContext(
                context_id=f"adr0339-transfer-{len(contexts):03d}",
                betting=state,
                board=board,
                opener_hands=opener_hands,
                responder_hands=responder_hands,
                joint_probabilities=probabilities,
                showdown_signs=signs,
                complete_raise_to_totals=_kernel_raise_universe(state),
            )
        )

    return FreshActionWidthTransferPool(
        seed=ADR0339_TRANSFER_SEED,
        mechanism_source_commit=ADR0339_MECHANISM_SOURCE_COMMIT,
        generator_version=ADR0323_GENERATOR_VERSION,
        structural_filter_version=ADR0323_STRUCTURAL_FILTER_VERSION,
        candidate_attempts=attempts,
        development_pool_sha256=ADR0323_DEVELOPMENT_POOL_SHA256,
        development_context_semantic_digests=tuple(
            context.semantic_digest for context in development.contexts
        ),
        nonreplay_pool_sha256=ADR0331_POPULATION_POOL_SHA256,
        nonreplay_context_semantic_digests=tuple(
            context.semantic_digest for context in nonreplay.contexts
        ),
        contexts=tuple(contexts),
    )


__all__ = [
    "ADR0339_ADR0311_AUDIT_CONTEXT_COUNT",
    "ADR0339_ADR0311_AUDIT_INVENTORY_SHA256",
    "ADR0339_MAINTAINED_PRIOR_CONTEXT_COUNT",
    "ADR0339_MAINTAINED_PRIOR_INVENTORY_SHA256",
    "ADR0339_MECHANISM_SOURCE_COMMIT",
    "ADR0339_TRANSFER_CONTEXT_COUNT",
    "ADR0339_TRANSFER_PROTOCOL",
    "ADR0339_TRANSFER_PROTOCOL_SHA256",
    "ADR0339_TRANSFER_SEED",
    "ADR0339_TRANSFER_SEED_SHA256",
    "FreshActionWidthTransferPool",
    "SemanticInventoryBetIncrement",
    "action_width_context_semantic_inventory_key",
    "action_width_context_semantic_inventory_sha256",
    "build_adr0339_transfer_pool",
    "semantic_inventory_bet_increment",
]
