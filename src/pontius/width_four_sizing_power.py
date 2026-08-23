"""Width-four candidate-blind sizing-power structures frozen by ADR-0297."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from itertools import pairwise

from .action_abstraction_confirmation import (
    ADR0293_GENERATOR_VERSION,
    ADR0293_POTS,
    ADR0293_STACKS,
    _DigestStream,
    _showdown_signs,
    _shuffled_deck,
)
from .reduced_river_sizing_oracle import (
    ExactDealProbability,
    ReducedRiverSizingContext,
)

ADR0297_BASELINE_COMMIT = "91449e42997938e72961976dcd8b4fda989e258b"
ADR0297_GENERATOR_VERSION = "candidate-blind-width4-sizing-power-pools-v1"
ADR0297_STRUCTURAL_FILTER_VERSION = "width4-both-signs-three-rows-three-columns-v1"
ADR0297_BATCH_COUNT = 3
ADR0297_PRIVATE_WIDTH = 4
ADR0297_POOL_CONTEXT_COUNT = 96
ADR0297_QUALIFIED_CONTEXT_COUNT = 12
ADR0297_POOL_SHA256 = (
    "ee82577c3820685376af6f988c892df265a68dacb36f0fafdd89095dac2d1603",
    "d2022051f734d1d977055bd1148f6b6e830a41af047e63964ce6a4fc4421a2cf",
    "ebf029eb2930f0a63030096373f7e91dd5b361055754e2497f229fff4f38f049",
)
ADR0297_POOL_CANDIDATE_ATTEMPTS = (459, 471, 493)


def _seed_for_batch(batch_index: int) -> str:
    if (
        isinstance(batch_index, bool)
        or not isinstance(batch_index, int)
        or batch_index not in range(ADR0297_BATCH_COUNT)
    ):
        raise ValueError("width-four batch index must identify one of three batches")
    return (
        "pontius|adr-0297|width4-power-v1|"
        f"baseline={ADR0297_BASELINE_COMMIT}|batch={batch_index}"
    )


def _private_pairs_width_four(
    cards: tuple[int, ...],
) -> tuple[tuple[int, int], ...]:
    if len(cards) != 2 * ADR0297_PRIVATE_WIDTH:
        raise AssertionError("width-four private-card slice must contain eight cards")
    return tuple(
        tuple(sorted(cards[offset : offset + 2]))
        for offset in range(0, len(cards), 2)
    )


def _structurally_admissible_width_four(
    signs: tuple[tuple[int, ...], ...],
) -> bool:
    if len(signs) != ADR0297_PRIVATE_WIDTH or any(
        len(row) != ADR0297_PRIVATE_WIDTH for row in signs
    ):
        return False
    if {value for row in signs for value in row} != {-1, 1}:
        return False
    if len(set(signs)) < 3:
        return False
    columns = tuple(
        tuple(row[column] for row in signs)
        for column in range(ADR0297_PRIVATE_WIDTH)
    )
    return len(set(columns)) >= 3


def _context_semantic_key(context: ReducedRiverSizingContext) -> tuple[object, ...]:
    return (
        context.board,
        context.pot,
        context.stack,
        context.minimum_bet,
        context.opener_hands,
        context.responder_hands,
        tuple(
            tuple((value.numerator, value.denominator) for value in row)
            for row in context.joint_probabilities
        ),
    )


@dataclass(frozen=True, slots=True)
class WidthFourSizingPowerPool:
    batch_index: int
    seed: str
    candidate_attempts: int
    contexts: tuple[ReducedRiverSizingContext, ...]

    def __post_init__(self) -> None:
        expected_seed = _seed_for_batch(self.batch_index)
        if self.seed != expected_seed:
            raise ValueError("width-four pool seed differs from ADR-0297")
        if (
            isinstance(self.candidate_attempts, bool)
            or not isinstance(self.candidate_attempts, int)
            or self.candidate_attempts < ADR0297_POOL_CONTEXT_COUNT
        ):
            raise ValueError("width-four raw candidate-attempt count is invalid")
        if not isinstance(self.contexts, tuple) or len(
            self.contexts
        ) != ADR0297_POOL_CONTEXT_COUNT:
            raise TypeError("width-four pool must contain 96 immutable contexts")
        if any(
            not isinstance(context, ReducedRiverSizingContext)
            for context in self.contexts
        ):
            raise TypeError("width-four pool contains a nonsemantic context")
        expected_ids = tuple(
            f"adr0297-width4-b{self.batch_index}-c{index:02d}"
            for index in range(ADR0297_POOL_CONTEXT_COUNT)
        )
        if tuple(context.context_id for context in self.contexts) != expected_ids:
            raise ValueError("width-four pool ids or ordering differ from ADR-0297")
        if any(
            len(context.opener_hands) != ADR0297_PRIVATE_WIDTH
            or len(context.responder_hands) != ADR0297_PRIVATE_WIDTH
            for context in self.contexts
        ):
            raise ValueError("width-four pool contains a context with the wrong width")
        if any(
            not _structurally_admissible_width_four(context.showdown_signs)
            for context in self.contexts
        ):
            raise ValueError("width-four pool contains an inadmissible sign matrix")
        semantic_keys = tuple(_context_semantic_key(context) for context in self.contexts)
        if len(set(semantic_keys)) != len(semantic_keys):
            raise ValueError("width-four pool repeats a semantic context")

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
            "baseline_commit": ADR0297_BASELINE_COMMIT,
            "batch_index": self.batch_index,
            "candidate_attempts": self.candidate_attempts,
            "contexts": tuple(
                {
                    "board": context.board,
                    "context_id": context.context_id,
                    "joint_probabilities": tuple(
                        tuple(
                            (probability.numerator, probability.denominator)
                            for probability in row
                        )
                        for row in context.joint_probabilities
                    ),
                    "minimum_bet": context.minimum_bet,
                    "opener_hands": context.opener_hands,
                    "pot": context.pot,
                    "responder_hands": context.responder_hands,
                    "stack": context.stack,
                }
                for context in self.contexts
            ),
            "dependency_generator_version": ADR0293_GENERATOR_VERSION,
            "generator_version": ADR0297_GENERATOR_VERSION,
            "private_width": ADR0297_PRIVATE_WIDTH,
            "seed": self.seed,
            "structural_filter_version": ADR0297_STRUCTURAL_FILTER_VERSION,
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


@dataclass(frozen=True, slots=True)
class ReducedSizingLpDimensions:
    variable_count: int
    inequality_count: int

    def __post_init__(self) -> None:
        for label, value in (
            ("variable count", self.variable_count),
            ("inequality count", self.inequality_count),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"reduced sizing LP {label} must be a positive integer")


def width_four_lp_dimensions(
    context: ReducedRiverSizingContext,
    bet_sizes: tuple[int, ...],
) -> ReducedSizingLpDimensions:
    """Return exact compact-LP dimensions without opening a sizing value."""

    if not isinstance(context, ReducedRiverSizingContext):
        raise TypeError("width-four LP dimensions require a semantic context")
    if (
        len(context.opener_hands) != ADR0297_PRIVATE_WIDTH
        or len(context.responder_hands) != ADR0297_PRIVATE_WIDTH
    ):
        raise ValueError("width-four LP dimensions require four types per seat")
    if not isinstance(bet_sizes, tuple) or not bet_sizes:
        raise TypeError("width-four LP dimensions require immutable bet sizes")
    if any(
        isinstance(size, bool) or not isinstance(size, int) for size in bet_sizes
    ):
        raise TypeError("width-four LP dimension sizes must be integers")
    if any(left >= right for left, right in pairwise(bet_sizes)):
        raise ValueError("width-four LP dimension sizes must increase strictly")
    if bet_sizes[0] < context.minimum_bet or bet_sizes[-1] > context.stack:
        raise ValueError("width-four LP dimension size lies outside the legal interval")
    action_size_count = len(bet_sizes)
    opener_count = len(context.opener_hands)
    responder_count = len(context.responder_hands)
    return ReducedSizingLpDimensions(
        variable_count=(
            opener_count * (1 + action_size_count)
            + responder_count * action_size_count
        ),
        inequality_count=(
            2 * opener_count + 2 * responder_count * action_size_count
        ),
    )


def build_adr0297_width_four_pool(*, batch_index: int) -> WidthFourSizingPowerPool:
    """Construct one frozen structural pool without opening a sizing value."""

    seed = _seed_for_batch(batch_index)
    stream = _DigestStream(seed)
    contexts: list[ReducedRiverSizingContext] = []
    candidate_attempts = 0
    while len(contexts) < ADR0297_POOL_CONTEXT_COUNT:
        candidate_attempts += 1
        deck = _shuffled_deck(stream)
        board = deck[:5]
        opener_hands = _private_pairs_width_four(deck[5:13])
        responder_hands = _private_pairs_width_four(deck[13:21])
        signs = _showdown_signs(board, opener_hands, responder_hands)
        if not _structurally_admissible_width_four(signs):
            continue
        pot = ADR0293_POTS[stream.randbelow(len(ADR0293_POTS))]
        stack = ADR0293_STACKS[stream.randbelow(len(ADR0293_STACKS))]
        weights = tuple(
            1 + stream.randbelow(9)
            for _ in range(ADR0297_PRIVATE_WIDTH * ADR0297_PRIVATE_WIDTH)
        )
        denominator = sum(weights)
        probabilities = tuple(
            tuple(
                ExactDealProbability(
                    weights[row * ADR0297_PRIVATE_WIDTH + column],
                    denominator,
                )
                for column in range(ADR0297_PRIVATE_WIDTH)
            )
            for row in range(ADR0297_PRIVATE_WIDTH)
        )
        contexts.append(
            ReducedRiverSizingContext(
                context_id=(
                    f"adr0297-width4-b{batch_index}-c{len(contexts):02d}"
                ),
                board=board,
                pot=pot,
                stack=stack,
                minimum_bet=2,
                opener_hands=opener_hands,
                responder_hands=responder_hands,
                joint_probabilities=probabilities,
            )
        )
    return WidthFourSizingPowerPool(
        batch_index=batch_index,
        seed=seed,
        candidate_attempts=candidate_attempts,
        contexts=tuple(contexts),
    )


__all__ = [
    "ADR0297_BASELINE_COMMIT",
    "ADR0297_BATCH_COUNT",
    "ADR0297_GENERATOR_VERSION",
    "ADR0297_POOL_CANDIDATE_ATTEMPTS",
    "ADR0297_POOL_CONTEXT_COUNT",
    "ADR0297_POOL_SHA256",
    "ADR0297_PRIVATE_WIDTH",
    "ADR0297_QUALIFIED_CONTEXT_COUNT",
    "ADR0297_STRUCTURAL_FILTER_VERSION",
    "ReducedSizingLpDimensions",
    "WidthFourSizingPowerPool",
    "build_adr0297_width_four_pool",
    "width_four_lp_dimensions",
]
