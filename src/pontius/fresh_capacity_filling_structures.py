"""Value-free fresh width-four structures frozen by ADR-0305."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from hashlib import sha256
from math import gcd

from .river import evaluate_seven

ADR0305_V4_SOURCE_COMMIT = "a6f7d4b20a67f00b67be40bf412a5e9ff32fc84d"
ADR0305_V4_SOURCE_ID = "adr-0305-capacity-filling-pot-odds-v4"
ADR0305_V4_SOURCE_SHA256 = "37824e44b7793b10b081957fc8be387bdca5c565b4bfe2386ca13f7e1c785c8b"
ADR0305_V4_STRUCTURE_GENERATOR_VERSION = "fresh-capacity-filling-pot-odds-v4-structure-v1"
ADR0305_V4_DEPENDENCY_GENERATOR_VERSION = "sha256-fisher-yates-structural-river-panel-v1"
ADR0305_V4_STRUCTURAL_FILTER_VERSION = "width4-both-signs-three-rows-three-columns-v1"
ADR0305_V4_POTS = (6, 8, 10, 12, 14, 16, 20, 24, 30, 40)
ADR0305_V4_STACKS = (10, 12, 16, 20, 24, 30)
ADR0305_V4_REPRESENTATIVE_SEED = (
    "pontius:adr-0305:capacity-filling-pot-odds-v4:representative:sha256-stream:v1"
)
ADR0305_V4_QUALIFIED_A_SEED = (
    "pontius:adr-0305:capacity-filling-pot-odds-v4:qualified-a:sha256-stream:v1"
)
ADR0305_V4_QUALIFIED_B_SEED = (
    "pontius:adr-0305:capacity-filling-pot-odds-v4:qualified-b:sha256-stream:v1"
)
ADR0305_V4_REPRESENTATIVE_CONTEXT_COUNT = 48
ADR0305_V4_QUALIFIED_CONTEXT_COUNT = 96
ADR0305_V4_REPRESENTATIVE_CANDIDATE_ATTEMPTS = 239
ADR0305_V4_QUALIFIED_A_CANDIDATE_ATTEMPTS = 570
ADR0305_V4_QUALIFIED_B_CANDIDATE_ATTEMPTS = 451
ADR0305_V4_REPRESENTATIVE_SHA256 = (
    "6ab4f7451b008a3a82309473df28384ede65e94da27fccc45a920e6ef4a4ffbc"
)
ADR0305_V4_QUALIFIED_A_SHA256 = "54cd7ed77a7c37a67dc050e8155fbbbcad61e4d952316fa2e3eb5c2f602110ed"
ADR0305_V4_QUALIFIED_B_SHA256 = "23c186d3c393c9d233558c8150e9bb1f7c38f75f6e3cf1d7c7685341057f5870"
_UINT64_MODULUS = 1 << 64


def _require_integer(value: object, *, label: str, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < (1 if positive else 0):
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{label} must be {qualifier}")
    return value


class _DigestStream:
    """ADR-0293's SHA-256 counter stream, reproduced without value imports."""

    __slots__ = ("_counter", "_seed", "_word_index", "_words")

    def __init__(self, seed: str) -> None:
        if not isinstance(seed, str) or not seed:
            raise ValueError("capacity-filling digest-stream seed must be nonempty")
        try:
            encoded = seed.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError("capacity-filling digest-stream seed must be ASCII") from error
        self._seed = encoded
        self._counter = 0
        self._words: tuple[int, ...] = ()
        self._word_index = 0

    def _next_uint64(self) -> int:
        if self._word_index == len(self._words):
            if self._counter >= 1 << 64:
                raise OverflowError("capacity-filling digest stream exhausted")
            block = sha256(self._seed + self._counter.to_bytes(8, "big")).digest()
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
            raise TypeError("capacity-filling random bound must be an integer")
        if bound <= 0:
            raise ValueError("capacity-filling random bound must be positive")
        if bound > _UINT64_MODULUS:
            raise ValueError("capacity-filling random bound exceeds word range")
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


def _showdown_signs(
    board: tuple[int, ...],
    opener_hands: tuple[tuple[int, int], ...],
    responder_hands: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, ...], ...]:
    opener_ranks = tuple(evaluate_seven((*board, *hand)) for hand in opener_hands)
    responder_ranks = tuple(evaluate_seven((*board, *hand)) for hand in responder_hands)
    return tuple(
        tuple((left > right) - (left < right) for right in responder_ranks) for left in opener_ranks
    )


def _canonical_board(value: object) -> tuple[int, ...]:
    if not isinstance(value, tuple) or len(value) != 5:
        raise TypeError("capacity-filling board must be an immutable five-card tuple")
    if any(
        isinstance(card, bool) or not isinstance(card, int) or card not in range(52)
        for card in value
    ):
        raise ValueError("capacity-filling board contains an invalid card")
    if len(set(value)) != len(value):
        raise ValueError("capacity-filling board repeats a card")
    return value


def _canonical_hand(value: object, *, label: str) -> tuple[int, int]:
    if not isinstance(value, tuple) or len(value) != 2:
        raise TypeError(f"{label} must be an immutable two-card tuple")
    if any(
        isinstance(card, bool) or not isinstance(card, int) or card not in range(52)
        for card in value
    ):
        raise ValueError(f"{label} contains an invalid card")
    if value[0] >= value[1]:
        raise ValueError(f"{label} must contain two ordered distinct cards")
    return value


@dataclass(frozen=True, slots=True)
class CapacityFillingExactProbability:
    """One exact positive value-free joint-deal probability."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        numerator = _require_integer(
            self.numerator,
            label="capacity-filling probability numerator",
            positive=True,
        )
        denominator = _require_integer(
            self.denominator,
            label="capacity-filling probability denominator",
            positive=True,
        )
        if numerator > denominator:
            raise ValueError("capacity-filling probability must lie in (0, 1]")
        common = gcd(numerator, denominator)
        object.__setattr__(self, "numerator", numerator // common)
        object.__setattr__(self, "denominator", denominator // common)

    @property
    def fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


@dataclass(frozen=True, slots=True)
class CapacityFillingWidthFourContext:
    """One candidate-free exact card/chip/range context."""

    context_id: str
    board: tuple[int, ...]
    pot: int
    stack: int
    minimum_bet: int
    opener_hands: tuple[tuple[int, int], ...]
    responder_hands: tuple[tuple[int, int], ...]
    joint_probabilities: tuple[tuple[CapacityFillingExactProbability, ...], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.context_id, str) or not self.context_id.strip():
            raise ValueError("capacity-filling context id must be nonempty")
        board = _canonical_board(self.board)
        pot = _require_integer(self.pot, label="capacity-filling pot", positive=True)
        stack = _require_integer(
            self.stack,
            label="capacity-filling stack",
            positive=True,
        )
        minimum = _require_integer(
            self.minimum_bet,
            label="capacity-filling minimum bet",
            positive=True,
        )
        if pot not in ADR0305_V4_POTS:
            raise ValueError("capacity-filling pot differs from the frozen set")
        if stack not in ADR0305_V4_STACKS:
            raise ValueError("capacity-filling stack differs from the frozen set")
        if minimum != 2 or minimum > stack:
            raise ValueError("capacity-filling minimum bet differs from ADR-0305")
        if not isinstance(self.opener_hands, tuple) or len(self.opener_hands) != 4:
            raise TypeError("capacity-filling opener axis must contain four hands")
        if not isinstance(self.responder_hands, tuple) or len(self.responder_hands) != 4:
            raise TypeError("capacity-filling responder axis must contain four hands")
        opener = tuple(
            _canonical_hand(hand, label=f"capacity-filling opener hand {index}")
            for index, hand in enumerate(self.opener_hands)
        )
        responder = tuple(
            _canonical_hand(hand, label=f"capacity-filling responder hand {index}")
            for index, hand in enumerate(self.responder_hands)
        )
        physical_cards = (
            *board,
            *(card for hand in opener for card in hand),
            *(card for hand in responder for card in hand),
        )
        if len(physical_cards) != 21 or len(set(physical_cards)) != 21:
            raise ValueError("capacity-filling context must contain 21 distinct cards")

        probabilities = self.joint_probabilities
        if not isinstance(probabilities, tuple) or len(probabilities) != 4:
            raise TypeError("capacity-filling joint range must contain four rows")
        if any(not isinstance(row, tuple) or len(row) != 4 for row in probabilities):
            raise TypeError("capacity-filling joint range rows must contain four values")
        if any(
            not isinstance(probability, CapacityFillingExactProbability)
            for row in probabilities
            for probability in row
        ):
            raise TypeError("capacity-filling joint range contains a wrong value")
        total = sum(
            (probability.fraction for row in probabilities for probability in row),
            start=Fraction(0),
        )
        if total != 1:
            raise ValueError("capacity-filling probabilities must sum exactly to one")
        if not _structurally_admissible_width_four(_showdown_signs(board, opener, responder)):
            raise ValueError("capacity-filling context fails the frozen filter")

        object.__setattr__(self, "board", board)
        object.__setattr__(self, "pot", pot)
        object.__setattr__(self, "stack", stack)
        object.__setattr__(self, "minimum_bet", minimum)
        object.__setattr__(self, "opener_hands", opener)
        object.__setattr__(self, "responder_hands", responder)

    @property
    def payoff_span(self) -> int:
        return self.pot + 2 * self.stack

    @property
    def showdown_signs(self) -> tuple[tuple[int, ...], ...]:
        return _showdown_signs(
            self.board,
            self.opener_hands,
            self.responder_hands,
        )

    @property
    def semantic_key(self) -> tuple[object, ...]:
        return (
            self.board,
            self.pot,
            self.stack,
            self.minimum_bet,
            self.opener_hands,
            self.responder_hands,
            tuple(
                tuple((probability.numerator, probability.denominator) for probability in row)
                for row in self.joint_probabilities
            ),
        )

    @property
    def canonical_payload(self) -> dict[str, object]:
        return {
            "board": self.board,
            "context_id": self.context_id,
            "joint_probabilities": tuple(
                tuple((probability.numerator, probability.denominator) for probability in row)
                for row in self.joint_probabilities
            ),
            "minimum_bet": self.minimum_bet,
            "opener_hands": self.opener_hands,
            "pot": self.pot,
            "responder_hands": self.responder_hands,
            "stack": self.stack,
        }


class CapacityFillingStructureKind(StrEnum):
    REPRESENTATIVE = "representative"
    QUALIFIED_A = "qualified_a"
    QUALIFIED_B = "qualified_b"


def _structure_contract(
    kind: CapacityFillingStructureKind,
) -> tuple[str, int, int, str, str]:
    if not isinstance(kind, CapacityFillingStructureKind):
        raise TypeError("capacity-filling structure kind must be semantic")
    if kind is CapacityFillingStructureKind.REPRESENTATIVE:
        return (
            ADR0305_V4_REPRESENTATIVE_SEED,
            ADR0305_V4_REPRESENTATIVE_CONTEXT_COUNT,
            ADR0305_V4_REPRESENTATIVE_CANDIDATE_ATTEMPTS,
            ADR0305_V4_REPRESENTATIVE_SHA256,
            "adr0305-v4-representative",
        )
    if kind is CapacityFillingStructureKind.QUALIFIED_A:
        return (
            ADR0305_V4_QUALIFIED_A_SEED,
            ADR0305_V4_QUALIFIED_CONTEXT_COUNT,
            ADR0305_V4_QUALIFIED_A_CANDIDATE_ATTEMPTS,
            ADR0305_V4_QUALIFIED_A_SHA256,
            "adr0305-v4-qualified-a",
        )
    return (
        ADR0305_V4_QUALIFIED_B_SEED,
        ADR0305_V4_QUALIFIED_CONTEXT_COUNT,
        ADR0305_V4_QUALIFIED_B_CANDIDATE_ATTEMPTS,
        ADR0305_V4_QUALIFIED_B_SHA256,
        "adr0305-v4-qualified-b",
    )


def _private_pairs_width_four(
    cards: tuple[int, ...],
) -> tuple[tuple[int, int], ...]:
    if len(cards) != 8:
        raise AssertionError("capacity-filling private-card slice must contain eight cards")
    return tuple(tuple(sorted(cards[offset : offset + 2])) for offset in range(0, len(cards), 2))


def _structurally_admissible_width_four(
    signs: tuple[tuple[int, ...], ...],
) -> bool:
    if len(signs) != 4 or any(len(row) != 4 for row in signs):
        return False
    if {value for row in signs for value in row} != {-1, 1}:
        return False
    if len(set(signs)) < 3:
        return False
    columns = tuple(tuple(row[column] for row in signs) for column in range(4))
    return len(set(columns)) >= 3


@dataclass(frozen=True, slots=True)
class FreshCapacityFillingStructure:
    """One sealed candidate-free structure from an ADR-0305 stream."""

    kind: CapacityFillingStructureKind
    seed: str
    generator_version: str
    candidate_attempts: int
    contexts: tuple[CapacityFillingWidthFourContext, ...]

    def __post_init__(self) -> None:
        seed, count, expected_attempts, expected_digest, id_prefix = _structure_contract(self.kind)
        if self.seed != seed:
            raise ValueError("capacity-filling structure seed differs from ADR-0305")
        if self.generator_version != ADR0305_V4_STRUCTURE_GENERATOR_VERSION:
            raise ValueError("capacity-filling structure generator differs from ADR-0305")
        if (
            isinstance(self.candidate_attempts, bool)
            or not isinstance(self.candidate_attempts, int)
            or self.candidate_attempts != expected_attempts
        ):
            raise ValueError("capacity-filling candidate-attempt count differs from ADR-0305")
        if not isinstance(self.contexts, tuple) or len(self.contexts) != count:
            raise TypeError("capacity-filling structure has the wrong immutable context count")
        if any(
            not isinstance(context, CapacityFillingWidthFourContext) for context in self.contexts
        ):
            raise TypeError("capacity-filling structure contains a nonsemantic context")
        expected_ids = tuple(f"{id_prefix}-c{index:02d}" for index in range(count))
        if tuple(context.context_id for context in self.contexts) != expected_ids:
            raise ValueError("capacity-filling structure ids or ordering differ from ADR-0305")
        semantic_keys = tuple(context.semantic_key for context in self.contexts)
        if len(set(semantic_keys)) != len(semantic_keys):
            raise ValueError("capacity-filling structure repeats a semantic context")
        if self.digest != expected_digest:
            raise ValueError("capacity-filling structure digest differs from its sealed identity")

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
            "candidate_attempts": self.candidate_attempts,
            "contexts": tuple(context.canonical_payload for context in self.contexts),
            "dependency_generator_version": ADR0305_V4_DEPENDENCY_GENERATOR_VERSION,
            "generator_version": self.generator_version,
            "kind": self.kind.value,
            "private_width": 4,
            "seed": self.seed,
            "source_commit": ADR0305_V4_SOURCE_COMMIT,
            "source_id": ADR0305_V4_SOURCE_ID,
            "source_sha256": ADR0305_V4_SOURCE_SHA256,
            "structural_filter_version": ADR0305_V4_STRUCTURAL_FILTER_VERSION,
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


def build_adr0305_v4_structure(
    *,
    kind: CapacityFillingStructureKind,
) -> FreshCapacityFillingStructure:
    """Construct one frozen stream without importing a sizing candidate or value."""

    seed, count, _attempts, _digest, id_prefix = _structure_contract(kind)
    stream = _DigestStream(seed)
    contexts: list[CapacityFillingWidthFourContext] = []
    candidate_attempts = 0
    while len(contexts) < count:
        candidate_attempts += 1
        deck = _shuffled_deck(stream)
        board = deck[:5]
        opener_hands = _private_pairs_width_four(deck[5:13])
        responder_hands = _private_pairs_width_four(deck[13:21])
        signs = _showdown_signs(board, opener_hands, responder_hands)
        if not _structurally_admissible_width_four(signs):
            continue

        pot = ADR0305_V4_POTS[stream.randbelow(len(ADR0305_V4_POTS))]
        stack = ADR0305_V4_STACKS[stream.randbelow(len(ADR0305_V4_STACKS))]
        weights = tuple(1 + stream.randbelow(9) for _ in range(16))
        denominator = sum(weights)
        probabilities = tuple(
            tuple(
                CapacityFillingExactProbability(
                    weights[row * 4 + column],
                    denominator,
                )
                for column in range(4)
            )
            for row in range(4)
        )
        contexts.append(
            CapacityFillingWidthFourContext(
                context_id=f"{id_prefix}-c{len(contexts):02d}",
                board=board,
                pot=pot,
                stack=stack,
                minimum_bet=2,
                opener_hands=opener_hands,
                responder_hands=responder_hands,
                joint_probabilities=probabilities,
            )
        )

    return FreshCapacityFillingStructure(
        kind=kind,
        seed=seed,
        generator_version=ADR0305_V4_STRUCTURE_GENERATOR_VERSION,
        candidate_attempts=candidate_attempts,
        contexts=tuple(contexts),
    )


__all__ = [
    "ADR0305_V4_DEPENDENCY_GENERATOR_VERSION",
    "ADR0305_V4_POTS",
    "ADR0305_V4_QUALIFIED_A_CANDIDATE_ATTEMPTS",
    "ADR0305_V4_QUALIFIED_A_SEED",
    "ADR0305_V4_QUALIFIED_A_SHA256",
    "ADR0305_V4_QUALIFIED_B_CANDIDATE_ATTEMPTS",
    "ADR0305_V4_QUALIFIED_B_SEED",
    "ADR0305_V4_QUALIFIED_B_SHA256",
    "ADR0305_V4_QUALIFIED_CONTEXT_COUNT",
    "ADR0305_V4_REPRESENTATIVE_CANDIDATE_ATTEMPTS",
    "ADR0305_V4_REPRESENTATIVE_CONTEXT_COUNT",
    "ADR0305_V4_REPRESENTATIVE_SEED",
    "ADR0305_V4_REPRESENTATIVE_SHA256",
    "ADR0305_V4_SOURCE_COMMIT",
    "ADR0305_V4_SOURCE_ID",
    "ADR0305_V4_SOURCE_SHA256",
    "ADR0305_V4_STACKS",
    "ADR0305_V4_STRUCTURAL_FILTER_VERSION",
    "ADR0305_V4_STRUCTURE_GENERATOR_VERSION",
    "CapacityFillingExactProbability",
    "CapacityFillingStructureKind",
    "CapacityFillingWidthFourContext",
    "FreshCapacityFillingStructure",
    "build_adr0305_v4_structure",
]
