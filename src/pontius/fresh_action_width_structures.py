"""Value-free structures for ADR-0323 finite-block action-width research.

This module owns a fresh deterministic development population, exact
betting-kernel raise universes, and exhaustive anchored-subset schedules.  It
does not import or invoke a sizing solver and constructs no betting action.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
from math import comb
from types import MappingProxyType

from .certified_reduced_sizing_consumer_v2 import KernelRaiseToTotal
from .no_limit_betting import BettingStreet, NoLimitBettingState
from .river import evaluate_seven


ADR0323_BASELINE_COMMIT = "a8f2ce3c0af9282625f13e6f0d8e93ebd57c0fa6"
ADR0323_DEVELOPMENT_SEED = (
    "pontius|adr-0323|certified-finite-block-width|development|"
    f"baseline={ADR0323_BASELINE_COMMIT}"
)
ADR0323_GENERATOR_VERSION = "fresh-certified-finite-block-structures-v1"
ADR0323_STRUCTURAL_FILTER_VERSION = "h4-both-signs-three-rows-three-columns-v1"
ADR0323_DEVELOPMENT_CONTEXT_COUNT = 96
ADR0323_POTS = (6, 10, 14, 20)
ADR0323_STACKS = (8, 10, 12)
ADR0323_MINIMUM_FULL_RAISE = 2
ADR0323_RAISE_WIDTH_VALUES = (2, 3, 4, 5, 6)
ADR0323_TRANSFER_SEED_PREFIX = (
    "pontius|adr-0323|certified-finite-block-width|transfer|mechanism-commit="
)
_ADR0323_STRUCTURE_PROTOCOL_PAYLOAD = {
    "baseline_commit": ADR0323_BASELINE_COMMIT,
    "development_context_count": ADR0323_DEVELOPMENT_CONTEXT_COUNT,
    "development_seed": ADR0323_DEVELOPMENT_SEED,
    "generator_version": ADR0323_GENERATOR_VERSION,
    "minimum_full_raise": ADR0323_MINIMUM_FULL_RAISE,
    "pots": ADR0323_POTS,
    "private_range_width": 4,
    "raise_widths": ADR0323_RAISE_WIDTH_VALUES,
    "stacks": ADR0323_STACKS,
    "structural_filter_version": ADR0323_STRUCTURAL_FILTER_VERSION,
    "transfer_seed_prefix": ADR0323_TRANSFER_SEED_PREFIX,
    "version": "adr0323-value-free-structure-protocol-v1",
}
ADR0323_STRUCTURE_PROTOCOL = MappingProxyType(
    _ADR0323_STRUCTURE_PROTOCOL_PAYLOAD
)
ADR0323_STRUCTURE_PROTOCOL_SHA256 = sha256(
    json.dumps(
        _ADR0323_STRUCTURE_PROTOCOL_PAYLOAD,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
).hexdigest()

_PRIVATE_RANGE_WIDTH = 4
_UINT64_MODULUS = 1 << 64


def _require_positive_count(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer count")
    if value <= 0:
        raise ValueError(f"{label} must be positive")
    return value


def _valid_sha1_commit(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(character in "0123456789abcdef" for character in value)
    )


@dataclass(frozen=True, slots=True)
class PrivateRangeWidth:
    """Number of private types on one reduced-game seat axis."""

    count: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "count",
            _require_positive_count(self.count, label="private-range width"),
        )


@dataclass(frozen=True, slots=True)
class RaiseActionWidth:
    """Number of raise actions; the always-present check is excluded."""

    count: int

    def __post_init__(self) -> None:
        width = _require_positive_count(self.count, label="raise-action width")
        if width < 2:
            raise ValueError("anchored raise-action width must be at least two")
        object.__setattr__(self, "count", width)


ADR0323_PRIVATE_RANGE_WIDTH = PrivateRangeWidth(_PRIVATE_RANGE_WIDTH)
ADR0323_RAISE_WIDTHS = tuple(
    RaiseActionWidth(value) for value in ADR0323_RAISE_WIDTH_VALUES
)


class _DigestStream:
    """Local SHA-256 counter stream with unbiased bounded draws."""

    __slots__ = ("_counter", "_seed", "_word_index", "_words")

    def __init__(self, seed: str) -> None:
        if not isinstance(seed, str) or not seed:
            raise ValueError("action-width digest-stream seed must be nonempty")
        try:
            encoded = seed.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError("action-width digest-stream seed must be ASCII") from error
        self._seed = encoded
        self._counter = 0
        self._words: tuple[int, ...] = ()
        self._word_index = 0

    def _next_uint64(self) -> int:
        if self._word_index == len(self._words):
            if self._counter >= _UINT64_MODULUS:
                raise OverflowError("action-width digest stream exhausted its counter")
            block = sha256(
                self._seed + self._counter.to_bytes(8, "big")
            ).digest()
            self._counter += 1
            self._words = tuple(
                int.from_bytes(block[offset : offset + 8], "big")
                for offset in range(0, len(block), 8)
            )
            self._word_index = 0
        value = self._words[self._word_index]
        self._word_index += 1
        return value

    def randbelow(self, bound: int) -> int:
        if isinstance(bound, bool) or not isinstance(bound, int):
            raise TypeError("action-width random bound must be an integer")
        if bound <= 0:
            raise ValueError("action-width random bound must be positive")
        if bound > _UINT64_MODULUS:
            raise ValueError("action-width random bound exceeds stream word range")
        limit = _UINT64_MODULUS - (_UINT64_MODULUS % bound)
        while True:
            value = self._next_uint64()
            if value < limit:
                return value % bound


def _shuffled_deck(stream: _DigestStream) -> tuple[int, ...]:
    deck = list(range(52))
    for index in range(51, 0, -1):
        other = stream.randbelow(index + 1)
        deck[index], deck[other] = deck[other], deck[index]
    return tuple(deck)


def _private_pairs(cards: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    if len(cards) != 2 * _PRIVATE_RANGE_WIDTH:
        raise AssertionError("action-width private-card slice has the wrong width")
    return tuple(
        tuple(sorted(cards[offset : offset + 2]))
        for offset in range(0, len(cards), 2)
    )


def _showdown_signs(
    board: tuple[int, ...],
    opener_hands: tuple[tuple[int, int], ...],
    responder_hands: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, ...], ...]:
    opener_ranks = tuple(
        evaluate_seven((*board, *hand)) for hand in opener_hands
    )
    responder_ranks = tuple(
        evaluate_seven((*board, *hand)) for hand in responder_hands
    )
    return tuple(
        tuple((left > right) - (left < right) for right in responder_ranks)
        for left in opener_ranks
    )


def _structurally_admissible(
    signs: tuple[tuple[int, ...], ...],
) -> bool:
    if len(signs) != _PRIVATE_RANGE_WIDTH or any(
        len(row) != _PRIVATE_RANGE_WIDTH for row in signs
    ):
        return False
    if {value for row in signs for value in row} != {-1, 1}:
        return False
    if len(set(signs)) < 3:
        return False
    columns = tuple(
        tuple(row[column] for row in signs)
        for column in range(_PRIVATE_RANGE_WIDTH)
    )
    return len(set(columns)) >= 3


def _river_opening_state(*, pot: int, effective_stack: int) -> NoLimitBettingState:
    actor_total = pot // 2
    responder_total = pot - actor_total
    return NoLimitBettingState(
        button=5,
        small_blind=1,
        big_blind=2,
        street=BettingStreet.RIVER,
        starting_stacks=(
            effective_stack + actor_total,
            effective_stack + responder_total,
            2,
            2,
            2,
            2,
        ),
        stacks=(effective_stack, effective_stack, 2, 2, 2, 2),
        total_contributions=(actor_total, responder_total, 0, 0, 0, 0),
        street_contributions=(0, 0, 0, 0, 0, 0),
        folded=(False, False, True, True, True, True),
        pending_seats=(0, 1),
        last_full_raise_size=ADR0323_MINIMUM_FULL_RAISE,
        acted_at_bet=(None, None, None, None, None, None),
    )


def _kernel_raise_universe(
    state: NoLimitBettingState,
) -> tuple[KernelRaiseToTotal, ...]:
    decision = state.legal_decision()
    bounds = decision.raise_bounds
    if bounds is None:
        raise ValueError("action-width context has no legal raise interval")
    return tuple(
        KernelRaiseToTotal(total)
        for total in range(bounds.minimum_raise_to, bounds.maximum_raise_to + 1)
    )


@dataclass(frozen=True, slots=True)
class FreshActionWidthContext:
    context_id: str
    betting: NoLimitBettingState
    board: tuple[int, ...]
    opener_hands: tuple[tuple[int, int], ...]
    responder_hands: tuple[tuple[int, int], ...]
    joint_probabilities: tuple[tuple[Fraction, ...], ...]
    showdown_signs: tuple[tuple[int, ...], ...]
    complete_raise_to_totals: tuple[KernelRaiseToTotal, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.context_id, str) or not self.context_id.strip():
            raise ValueError("fresh action-width context id must be nonempty")
        if not isinstance(self.betting, NoLimitBettingState):
            raise TypeError("fresh action-width context requires an exact betting state")
        state = self.betting
        state.assert_invariants()
        decision = state.legal_decision()
        bounds = decision.raise_bounds
        if (
            state.street is not BettingStreet.RIVER
            or state.live_seats != (0, 1)
            or state.acting_seat != 0
            or state.button != 5
            or state.small_blind != 1
            or state.big_blind != 2
            or state.pot not in ADR0323_POTS
            or state.stacks[0] not in ADR0323_STACKS
            or state.stacks[1] != state.stacks[0]
            or state.stacks[2:] != (2, 2, 2, 2)
            or state.starting_stacks
            != (
                state.stacks[0] + state.pot // 2,
                state.stacks[1] + state.pot // 2,
                2,
                2,
                2,
                2,
            )
            or state.total_contributions
            != (state.pot // 2, state.pot // 2, 0, 0, 0, 0)
            or state.street_contributions != (0, 0, 0, 0, 0, 0)
            or state.folded != (False, False, True, True, True, True)
            or state.pending_seats != (0, 1)
            or state.last_full_raise_size != ADR0323_MINIMUM_FULL_RAISE
            or state.acted_at_bet != (None, None, None, None, None, None)
            or state.history
            or state.round_complete
            or state.terminal_reason is not None
            or decision.to_call != 0
            or not decision.can_check
            or bounds is None
            or bounds.minimum_raise_to != ADR0323_MINIMUM_FULL_RAISE
            or bounds.maximum_raise_to != state.stacks[0]
            or bounds.maximum_contestable_raise_to != bounds.maximum_raise_to
        ):
            raise ValueError("fresh action-width context has the wrong betting shell")
        if (
            not isinstance(self.board, tuple)
            or len(self.board) != 5
            or any(
                isinstance(card, bool)
                or not isinstance(card, int)
                or card not in range(52)
                for card in self.board
            )
            or len(set(self.board)) != 5
        ):
            raise ValueError("fresh action-width board is invalid")
        for label, hands in (
            ("opener", self.opener_hands),
            ("responder", self.responder_hands),
        ):
            if not isinstance(hands, tuple) or len(hands) != _PRIVATE_RANGE_WIDTH:
                raise TypeError(f"fresh action-width {label} axis must have four hands")
            if any(
                not isinstance(hand, tuple)
                or len(hand) != 2
                or tuple(sorted(hand)) != hand
                or any(
                    isinstance(card, bool)
                    or not isinstance(card, int)
                    or card not in range(52)
                    for card in hand
                )
                or hand[0] == hand[1]
                for hand in hands
            ):
                raise ValueError(f"fresh action-width {label} hands are invalid")
        exposed = (
            *self.board,
            *(card for hand in self.opener_hands for card in hand),
            *(card for hand in self.responder_hands for card in hand),
        )
        if len(set(exposed)) != len(exposed):
            raise ValueError("fresh action-width context reuses an exposed card")
        if (
            not isinstance(self.joint_probabilities, tuple)
            or len(self.joint_probabilities) != _PRIVATE_RANGE_WIDTH
            or any(
                not isinstance(row, tuple) or len(row) != _PRIVATE_RANGE_WIDTH
                for row in self.joint_probabilities
            )
            or any(
                not isinstance(value, Fraction) or value <= 0
                for row in self.joint_probabilities
                for value in row
            )
            or sum(
                (value for row in self.joint_probabilities for value in row),
                start=Fraction(0),
            )
            != 1
        ):
            raise ValueError("fresh action-width joint probabilities are invalid")
        expected_signs = _showdown_signs(
            self.board,
            self.opener_hands,
            self.responder_hands,
        )
        if self.showdown_signs != expected_signs or not _structurally_admissible(
            self.showdown_signs
        ):
            raise ValueError("fresh action-width showdown signs are invalid")
        expected_universe = _kernel_raise_universe(state)
        if self.complete_raise_to_totals != expected_universe:
            raise ValueError("fresh action-width legal universe differs from the kernel")
        if len(expected_universe) not in (7, 9, 11):
            raise ValueError("fresh action-width legal universe has the wrong width")

    @property
    def payoff_span_chips(self) -> int:
        return self.betting.pot + 2 * self.betting.stacks[0]

    @property
    def semantic_digest(self) -> str:
        payload = {
            "betting": {
                "acted_at_bet": self.betting.acted_at_bet,
                "big_blind": self.betting.big_blind,
                "button": self.betting.button,
                "folded": self.betting.folded,
                "last_full_raise_size": self.betting.last_full_raise_size,
                "pending_seats": self.betting.pending_seats,
                "round_complete": self.betting.round_complete,
                "small_blind": self.betting.small_blind,
                "stacks": self.betting.stacks,
                "starting_stacks": self.betting.starting_stacks,
                "street": self.betting.street.value,
                "street_contributions": self.betting.street_contributions,
                "terminal_reason": None,
                "total_contributions": self.betting.total_contributions,
            },
            "board": self.board,
            "joint_probabilities": tuple(
                tuple((value.numerator, value.denominator) for value in row)
                for row in self.joint_probabilities
            ),
            "opener_hands": self.opener_hands,
            "raise_to_totals": tuple(
                value.chips for value in self.complete_raise_to_totals
            ),
            "responder_hands": self.responder_hands,
            "showdown_signs": self.showdown_signs,
            "version": "adr0323-fresh-action-width-context-v1",
        }
        return sha256(
            json.dumps(
                payload,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("ascii")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class AnchoredRaiseSubsetFamily:
    complete_raise_to_totals: tuple[KernelRaiseToTotal, ...]
    raise_width: RaiseActionWidth
    subsets: tuple[tuple[KernelRaiseToTotal, ...], ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.complete_raise_to_totals, tuple)
            or len(self.complete_raise_to_totals) < 2
            or any(
                not isinstance(value, KernelRaiseToTotal)
                for value in self.complete_raise_to_totals
            )
        ):
            raise TypeError("anchored family requires a nominal legal universe")
        amounts = tuple(value.chips for value in self.complete_raise_to_totals)
        if amounts != tuple(range(amounts[0], amounts[-1] + 1)):
            raise ValueError("anchored family legal universe must be contiguous")
        if not isinstance(self.raise_width, RaiseActionWidth):
            raise TypeError("anchored family requires a raise-action width")
        width = self.raise_width.count
        if width > len(amounts):
            raise ValueError("anchored subset width exceeds its legal universe")
        expected = tuple(
            (
                self.complete_raise_to_totals[0],
                *interior,
                self.complete_raise_to_totals[-1],
            )
            for interior in combinations(
                self.complete_raise_to_totals[1:-1],
                width - 2,
            )
        )
        if self.subsets != expected:
            raise ValueError("anchored subsets differ from exact lexicographic enumeration")
        if len(self.subsets) != comb(len(amounts) - 2, width - 2):
            raise AssertionError("anchored subset count differs from the combination identity")


def anchored_raise_subset_family(
    complete_raise_to_totals: tuple[KernelRaiseToTotal, ...],
    raise_width: RaiseActionWidth,
) -> AnchoredRaiseSubsetFamily:
    """Enumerate exact min/max-anchored raise subsets without solving."""

    if not isinstance(raise_width, RaiseActionWidth):
        raise TypeError("anchored subset construction requires a raise-action width")
    if not isinstance(complete_raise_to_totals, tuple):
        raise TypeError("anchored subset construction requires an immutable universe")
    if len(complete_raise_to_totals) < 2 or any(
        not isinstance(value, KernelRaiseToTotal)
        for value in complete_raise_to_totals
    ):
        raise TypeError("anchored subset construction requires a nominal legal universe")
    if raise_width.count > len(complete_raise_to_totals):
        raise ValueError("anchored subset width exceeds its legal universe")
    subsets = tuple(
        (
            complete_raise_to_totals[0],
            *interior,
            complete_raise_to_totals[-1],
        )
        for interior in combinations(
            complete_raise_to_totals[1:-1],
            raise_width.count - 2,
        )
    )
    return AnchoredRaiseSubsetFamily(
        complete_raise_to_totals=complete_raise_to_totals,
        raise_width=raise_width,
        subsets=subsets,
    )


@dataclass(frozen=True, slots=True)
class ActionWidthSubsetWorkLedger:
    context_count: int
    subset_counts_by_raise_width: tuple[tuple[RaiseActionWidth, int], ...]
    total_subset_count: int

    def __post_init__(self) -> None:
        context_count = _require_positive_count(
            self.context_count,
            label="subset-work context count",
        )
        if not isinstance(self.subset_counts_by_raise_width, tuple) or any(
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[0], RaiseActionWidth)
            for item in self.subset_counts_by_raise_width
        ):
            raise TypeError("subset-work ledger requires semantic immutable width counts")
        expected_widths = ADR0323_RAISE_WIDTHS
        if tuple(width for width, _ in self.subset_counts_by_raise_width) != expected_widths:
            raise ValueError("subset-work ledger raise widths differ from ADR-0323")
        if any(
            isinstance(count, bool) or not isinstance(count, int) or count <= 0
            for _, count in self.subset_counts_by_raise_width
        ):
            raise ValueError("subset-work ledger counts must be positive integers")
        if self.total_subset_count != sum(
            count for _, count in self.subset_counts_by_raise_width
        ):
            raise ValueError("subset-work total differs from its width counts")
        if context_count != self.context_count:
            raise AssertionError("subset-work context normalization drifted")


@dataclass(frozen=True, slots=True)
class FreshActionWidthDevelopmentPool:
    seed: str
    generator_version: str
    structural_filter_version: str
    candidate_attempts: int
    contexts: tuple[FreshActionWidthContext, ...]

    def __post_init__(self) -> None:
        if self.seed != ADR0323_DEVELOPMENT_SEED:
            raise ValueError("development pool seed differs from ADR-0323")
        if self.generator_version != ADR0323_GENERATOR_VERSION:
            raise ValueError("development pool generator version differs from ADR-0323")
        if self.structural_filter_version != ADR0323_STRUCTURAL_FILTER_VERSION:
            raise ValueError("development pool structural filter differs from ADR-0323")
        if (
            isinstance(self.candidate_attempts, bool)
            or not isinstance(self.candidate_attempts, int)
            or self.candidate_attempts < ADR0323_DEVELOPMENT_CONTEXT_COUNT
        ):
            raise ValueError("development pool candidate-attempt count is invalid")
        if (
            not isinstance(self.contexts, tuple)
            or len(self.contexts) != ADR0323_DEVELOPMENT_CONTEXT_COUNT
            or any(
                not isinstance(context, FreshActionWidthContext)
                for context in self.contexts
            )
        ):
            raise TypeError("development pool must contain 96 semantic contexts")
        expected_ids = tuple(
            f"adr0323-development-{index:03d}"
            for index in range(ADR0323_DEVELOPMENT_CONTEXT_COUNT)
        )
        if tuple(context.context_id for context in self.contexts) != expected_ids:
            raise ValueError("development context ids or ordering differ from ADR-0323")
        semantic_digests = tuple(context.semantic_digest for context in self.contexts)
        if len(set(semantic_digests)) != len(semantic_digests):
            raise ValueError("development pool repeats a semantic context")

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
            "candidate_attempts": self.candidate_attempts,
            "context_ids": tuple(context.context_id for context in self.contexts),
            "context_semantic_digests": tuple(
                context.semantic_digest for context in self.contexts
            ),
            "generator_version": self.generator_version,
            "protocol_sha256": ADR0323_STRUCTURE_PROTOCOL_SHA256,
            "seed": self.seed,
            "structural_filter_version": self.structural_filter_version,
            "version": "adr0323-fresh-action-width-development-pool-v1",
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
                    comb(len(context.complete_raise_to_totals) - 2, width.count - 2)
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


def build_adr0323_development_pool() -> FreshActionWidthDevelopmentPool:
    """Construct the frozen value-free development population."""

    stream = _DigestStream(ADR0323_DEVELOPMENT_SEED)
    contexts: list[FreshActionWidthContext] = []
    attempts = 0
    while len(contexts) < ADR0323_DEVELOPMENT_CONTEXT_COUNT:
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
                context_id=f"adr0323-development-{len(contexts):03d}",
                betting=state,
                board=board,
                opener_hands=opener_hands,
                responder_hands=responder_hands,
                joint_probabilities=probabilities,
                showdown_signs=signs,
                complete_raise_to_totals=_kernel_raise_universe(state),
            )
        )
    return FreshActionWidthDevelopmentPool(
        seed=ADR0323_DEVELOPMENT_SEED,
        generator_version=ADR0323_GENERATOR_VERSION,
        structural_filter_version=ADR0323_STRUCTURAL_FILTER_VERSION,
        candidate_attempts=attempts,
        contexts=tuple(contexts),
    )


def transfer_seed_from_mechanism_commit(mechanism_commit: str) -> str:
    """Derive the reserved transfer seed; this module cannot build its pool."""

    if not _valid_sha1_commit(mechanism_commit):
        raise ValueError("mechanism commit must be 40 lowercase hexadecimal characters")
    return ADR0323_TRANSFER_SEED_PREFIX + mechanism_commit


__all__ = [
    "ADR0323_BASELINE_COMMIT",
    "ADR0323_DEVELOPMENT_CONTEXT_COUNT",
    "ADR0323_DEVELOPMENT_SEED",
    "ADR0323_GENERATOR_VERSION",
    "ADR0323_MINIMUM_FULL_RAISE",
    "ADR0323_POTS",
    "ADR0323_PRIVATE_RANGE_WIDTH",
    "ADR0323_RAISE_WIDTHS",
    "ADR0323_RAISE_WIDTH_VALUES",
    "ADR0323_STACKS",
    "ADR0323_STRUCTURAL_FILTER_VERSION",
    "ADR0323_STRUCTURE_PROTOCOL",
    "ADR0323_STRUCTURE_PROTOCOL_SHA256",
    "ADR0323_TRANSFER_SEED_PREFIX",
    "ActionWidthSubsetWorkLedger",
    "AnchoredRaiseSubsetFamily",
    "FreshActionWidthContext",
    "FreshActionWidthDevelopmentPool",
    "PrivateRangeWidth",
    "RaiseActionWidth",
    "anchored_raise_subset_family",
    "build_adr0323_development_pool",
    "transfer_seed_from_mechanism_commit",
]
