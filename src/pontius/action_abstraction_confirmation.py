"""Deterministic untouched confirmation panel frozen by ADR-0293."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256

from .reduced_river_sizing_oracle import (
    ExactDealProbability,
    ReducedRiverSizingContext,
)
from .river import evaluate_seven

ADR0293_CONFIRMATION_SEED = (
    "pontius|adr-0293|confirmation-panel-v1|"
    "baseline=4156ce6febe350fa153a3ee32c5130ada897b8a3"
)
ADR0293_GENERATOR_VERSION = "sha256-fisher-yates-structural-river-panel-v1"
ADR0293_CONTEXT_COUNT = 24
ADR0293_POTS = (6, 8, 10, 12, 14, 16, 20, 24, 30, 40)
ADR0293_STACKS = (10, 12, 16, 20, 24, 30)
ADR0293_PANEL_SHA256 = "c3d1f5ca6dea3291e202d73e542caccb05cf61bca775b327fad90c3e62bc5438"
_UINT64_MODULUS = 1 << 64


class _DigestStream:
    """Version-independent SHA-256 counter stream with unbiased bounded draws."""

    __slots__ = ("_counter", "_seed", "_word_index", "_words")

    def __init__(self, seed: str) -> None:
        if not isinstance(seed, str) or not seed:
            raise ValueError("confirmation digest-stream seed must be nonempty")
        try:
            encoded = seed.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError("confirmation digest-stream seed must be ASCII") from error
        self._seed = encoded
        self._counter = 0
        self._words: tuple[int, ...] = ()
        self._word_index = 0

    def _next_uint64(self) -> int:
        if self._word_index == len(self._words):
            if self._counter >= 1 << 64:
                raise OverflowError("confirmation digest stream exhausted its counter")
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
            raise TypeError("confirmation random bound must be an integer")
        if bound <= 0:
            raise ValueError("confirmation random bound must be positive")
        if bound > _UINT64_MODULUS:
            raise ValueError("confirmation random bound exceeds the stream word range")
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
    if len(cards) != 6:
        raise AssertionError("confirmation private-card slice must contain six cards")
    return tuple(
        tuple(sorted(cards[offset : offset + 2]))
        for offset in range(0, len(cards), 2)
    )


def _showdown_signs(
    board: tuple[int, ...],
    opener_hands: tuple[tuple[int, int], ...],
    responder_hands: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, ...], ...]:
    opener_ranks = tuple(evaluate_seven((*board, *hand)) for hand in opener_hands)
    responder_ranks = tuple(
        evaluate_seven((*board, *hand)) for hand in responder_hands
    )
    return tuple(
        tuple((left > right) - (left < right) for right in responder_ranks)
        for left in opener_ranks
    )


def _structurally_admissible(signs: tuple[tuple[int, ...], ...]) -> bool:
    if any(value == 0 for row in signs for value in row):
        return False
    if {value for row in signs for value in row} != {-1, 1}:
        return False
    if len(set(signs)) < 2:
        return False
    columns = tuple(tuple(row[column] for row in signs) for column in range(3))
    return len(set(columns)) >= 2


@dataclass(frozen=True, slots=True)
class ActionAbstractionConfirmationPanel:
    seed: str
    generator_version: str
    candidate_attempts: int
    contexts: tuple[ReducedRiverSizingContext, ...]

    def __post_init__(self) -> None:
        if self.seed != ADR0293_CONFIRMATION_SEED:
            raise ValueError("confirmation panel seed differs from ADR-0293")
        if self.generator_version != ADR0293_GENERATOR_VERSION:
            raise ValueError("confirmation panel generator differs from ADR-0293")
        if (
            isinstance(self.candidate_attempts, bool)
            or not isinstance(self.candidate_attempts, int)
            or self.candidate_attempts < ADR0293_CONTEXT_COUNT
        ):
            raise ValueError("confirmation candidate-attempt count is invalid")
        if not isinstance(self.contexts, tuple) or len(
            self.contexts
        ) != ADR0293_CONTEXT_COUNT:
            raise TypeError("confirmation panel must contain 24 immutable contexts")
        if any(
            not isinstance(context, ReducedRiverSizingContext)
            for context in self.contexts
        ):
            raise TypeError("confirmation panel contains a nonsemantic context")
        expected_ids = tuple(
            f"adr0293-confirmation-{index:02d}"
            for index in range(ADR0293_CONTEXT_COUNT)
        )
        if tuple(context.context_id for context in self.contexts) != expected_ids:
            raise ValueError("confirmation context ids or ordering differ from ADR-0293")
        if len({context.digest for context in self.contexts}) != len(self.contexts):
            raise ValueError("confirmation panel repeats a context")
        if any(
            not _structurally_admissible(context.showdown_signs)
            for context in self.contexts
        ):
            raise ValueError("confirmation panel contains an inadmissible sign matrix")

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
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
            "generator_version": self.generator_version,
            "seed": self.seed,
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


def build_adr0293_confirmation_panel() -> ActionAbstractionConfirmationPanel:
    """Construct the frozen panel without global PRNG or manual intervention."""

    stream = _DigestStream(ADR0293_CONFIRMATION_SEED)
    contexts: list[ReducedRiverSizingContext] = []
    candidate_attempts = 0
    while len(contexts) < ADR0293_CONTEXT_COUNT:
        candidate_attempts += 1
        deck = _shuffled_deck(stream)
        board = deck[:5]
        opener_hands = _private_pairs(deck[5:11])
        responder_hands = _private_pairs(deck[11:17])
        signs = _showdown_signs(board, opener_hands, responder_hands)
        if not _structurally_admissible(signs):
            continue

        pot = ADR0293_POTS[stream.randbelow(len(ADR0293_POTS))]
        stack = ADR0293_STACKS[stream.randbelow(len(ADR0293_STACKS))]
        weights = tuple(1 + stream.randbelow(9) for _ in range(9))
        denominator = sum(weights)
        probabilities = tuple(
            tuple(
                ExactDealProbability(weights[row * 3 + column], denominator)
                for column in range(3)
            )
            for row in range(3)
        )
        contexts.append(
            ReducedRiverSizingContext(
                context_id=f"adr0293-confirmation-{len(contexts):02d}",
                board=board,
                pot=pot,
                stack=stack,
                minimum_bet=2,
                opener_hands=opener_hands,
                responder_hands=responder_hands,
                joint_probabilities=probabilities,
            )
        )

    return ActionAbstractionConfirmationPanel(
        seed=ADR0293_CONFIRMATION_SEED,
        generator_version=ADR0293_GENERATOR_VERSION,
        candidate_attempts=candidate_attempts,
        contexts=tuple(contexts),
    )


__all__ = [
    "ADR0293_CONFIRMATION_SEED",
    "ADR0293_CONTEXT_COUNT",
    "ADR0293_GENERATOR_VERSION",
    "ADR0293_PANEL_SHA256",
    "ADR0293_POTS",
    "ADR0293_STACKS",
    "ActionAbstractionConfirmationPanel",
    "build_adr0293_confirmation_panel",
]
