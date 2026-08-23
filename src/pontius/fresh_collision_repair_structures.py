"""Value-free fresh width-four structures frozen by ADR-0301."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from hashlib import sha256
from math import gcd

from .action_abstraction_confirmation import (
    ADR0293_GENERATOR_VERSION,
    ADR0293_POTS,
    ADR0293_STACKS,
    _DigestStream,
    _showdown_signs,
    _shuffled_deck,
)

ADR0301_BASELINE_COMMIT = "c6f5f676354f3bc08ede23820746d978bbb97f15"
ADR0301_COLLISION_REPAIR_SOURCE_SHA256 = (
    "ebae17f69c4f37377edf0fb0c55a99049c8688c8517dcbc525230d8e418a811a"
)
ADR0301_REPRESENTATIVE_SEED = (
    "pontius|adr-0301|collision-repair-v3-representative-v1|"
    f"baseline={ADR0301_BASELINE_COMMIT}|"
    f"source={ADR0301_COLLISION_REPAIR_SOURCE_SHA256}"
)
ADR0301_QUALIFIED_POOL_SEED = (
    "pontius|adr-0301|collision-repair-v3-qualified-v1|"
    f"baseline={ADR0301_BASELINE_COMMIT}|"
    f"source={ADR0301_COLLISION_REPAIR_SOURCE_SHA256}"
)
ADR0301_REPRESENTATIVE_GENERATOR_VERSION = (
    "collision-repair-v3-representative-width4-v1"
)
ADR0301_QUALIFIED_POOL_GENERATOR_VERSION = (
    "collision-repair-v3-qualified-width4-pool-v1"
)
ADR0301_STRUCTURAL_FILTER_VERSION = (
    "width4-both-signs-three-rows-three-columns-v1"
)
ADR0301_PRIVATE_WIDTH = 4
ADR0301_REPRESENTATIVE_CONTEXT_COUNT = 48
ADR0301_QUALIFIED_POOL_CONTEXT_COUNT = 96
ADR0301_REPRESENTATIVE_CANDIDATE_ATTEMPTS = 172
ADR0301_QUALIFIED_POOL_CANDIDATE_ATTEMPTS = 496
ADR0301_REPRESENTATIVE_SHA256 = (
    "b678f1140dd7ba75f5315abf58392d42b42a1a633c3249ec36991846a1bbab69"
)
ADR0301_QUALIFIED_POOL_SHA256 = (
    "fb26a8cfd2f82fd56896e22f6d006495f1148669dd6db3f56dcf2e79deeb4146"
)


def _require_integer(value: object, *, label: str, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < (1 if positive else 0):
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{label} must be {qualifier}")
    return value


def _canonical_board(value: object) -> tuple[int, ...]:
    if not isinstance(value, tuple) or len(value) != 5:
        raise TypeError("fresh structural board must be an immutable five-card tuple")
    if any(
        isinstance(card, bool) or not isinstance(card, int) or card not in range(52)
        for card in value
    ):
        raise ValueError("fresh structural board contains an invalid card")
    if len(set(value)) != len(value):
        raise ValueError("fresh structural board repeats a card")
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
        raise ValueError(f"{label} must contain two distinct canonically ordered cards")
    return value


@dataclass(frozen=True, slots=True)
class FreshExactProbability:
    """One exact positive structural joint-deal probability."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        numerator = _require_integer(
            self.numerator,
            label="fresh probability numerator",
            positive=True,
        )
        denominator = _require_integer(
            self.denominator,
            label="fresh probability denominator",
            positive=True,
        )
        if numerator > denominator:
            raise ValueError("fresh probability must lie in (0, 1]")
        common = gcd(numerator, denominator)
        object.__setattr__(self, "numerator", numerator // common)
        object.__setattr__(self, "denominator", denominator // common)

    @property
    def fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


def _structurally_admissible_width_four(
    signs: tuple[tuple[int, ...], ...],
) -> bool:
    if len(signs) != ADR0301_PRIVATE_WIDTH or any(
        len(row) != ADR0301_PRIVATE_WIDTH for row in signs
    ):
        return False
    if {value for row in signs for value in row} != {-1, 1}:
        return False
    if len(set(signs)) < 3:
        return False
    columns = tuple(
        tuple(row[column] for row in signs)
        for column in range(ADR0301_PRIVATE_WIDTH)
    )
    return len(set(columns)) >= 3


@dataclass(frozen=True, slots=True)
class FreshWidthFourContext:
    """One value-free exact card/chip/range context."""

    context_id: str
    board: tuple[int, ...]
    pot: int
    stack: int
    minimum_bet: int
    opener_hands: tuple[tuple[int, int], ...]
    responder_hands: tuple[tuple[int, int], ...]
    joint_probabilities: tuple[tuple[FreshExactProbability, ...], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.context_id, str) or not self.context_id.strip():
            raise ValueError("fresh structural context id must be nonempty")
        board = _canonical_board(self.board)
        pot = _require_integer(self.pot, label="fresh structural pot", positive=True)
        stack = _require_integer(
            self.stack,
            label="fresh structural stack",
            positive=True,
        )
        minimum = _require_integer(
            self.minimum_bet,
            label="fresh structural minimum bet",
            positive=True,
        )
        if pot not in ADR0293_POTS:
            raise ValueError("fresh structural pot differs from the frozen set")
        if stack not in ADR0293_STACKS:
            raise ValueError("fresh structural stack differs from the frozen set")
        if minimum != 2 or minimum > stack:
            raise ValueError("fresh structural minimum bet differs from ADR-0301")
        if not isinstance(self.opener_hands, tuple) or len(
            self.opener_hands
        ) != ADR0301_PRIVATE_WIDTH:
            raise TypeError("fresh opener axis must contain four immutable hands")
        if not isinstance(self.responder_hands, tuple) or len(
            self.responder_hands
        ) != ADR0301_PRIVATE_WIDTH:
            raise TypeError("fresh responder axis must contain four immutable hands")
        opener = tuple(
            _canonical_hand(hand, label=f"fresh opener hand {index}")
            for index, hand in enumerate(self.opener_hands)
        )
        responder = tuple(
            _canonical_hand(hand, label=f"fresh responder hand {index}")
            for index, hand in enumerate(self.responder_hands)
        )
        physical_cards = (*board, *(card for hand in opener for card in hand))
        physical_cards = (
            *physical_cards,
            *(card for hand in responder for card in hand),
        )
        if len(physical_cards) != 21 or len(set(physical_cards)) != 21:
            raise ValueError("fresh structural context must contain 21 distinct cards")

        probabilities = self.joint_probabilities
        if not isinstance(probabilities, tuple) or len(
            probabilities
        ) != ADR0301_PRIVATE_WIDTH:
            raise TypeError("fresh joint range must contain four immutable rows")
        if any(
            not isinstance(row, tuple) or len(row) != ADR0301_PRIVATE_WIDTH
            for row in probabilities
        ):
            raise TypeError("fresh joint range rows must contain four probabilities")
        if any(
            not isinstance(probability, FreshExactProbability)
            for row in probabilities
            for probability in row
        ):
            raise TypeError("fresh joint range contains a nonsemantic probability")
        total = sum(
            (probability.fraction for row in probabilities for probability in row),
            start=Fraction(0),
        )
        if total != 1:
            raise ValueError("fresh joint probabilities must sum exactly to one")
        if not _structurally_admissible_width_four(self.showdown_signs):
            raise ValueError("fresh context fails the frozen width-four filter")

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
        """Identity excluding only the family-specific context id."""

        return (
            self.board,
            self.pot,
            self.stack,
            self.minimum_bet,
            self.opener_hands,
            self.responder_hands,
            tuple(
                tuple(
                    (probability.numerator, probability.denominator)
                    for probability in row
                )
                for row in self.joint_probabilities
            ),
        )

    @property
    def canonical_payload(self) -> dict[str, object]:
        return {
            "board": self.board,
            "context_id": self.context_id,
            "joint_probabilities": tuple(
                tuple(
                    (probability.numerator, probability.denominator)
                    for probability in row
                )
                for row in self.joint_probabilities
            ),
            "minimum_bet": self.minimum_bet,
            "opener_hands": self.opener_hands,
            "pot": self.pot,
            "responder_hands": self.responder_hands,
            "stack": self.stack,
        }

    @property
    def digest(self) -> str:
        payload = {
            **self.canonical_payload,
            "version": "fresh-width-four-structural-context-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


class FreshStructureKind(StrEnum):
    REPRESENTATIVE = "representative"
    QUALIFIED_POOL = "qualified_pool"


def _structure_contract(
    kind: FreshStructureKind,
) -> tuple[str, str, int, int, str, str]:
    if not isinstance(kind, FreshStructureKind):
        raise TypeError("fresh structure kind must be semantic")
    if kind is FreshStructureKind.REPRESENTATIVE:
        return (
            ADR0301_REPRESENTATIVE_SEED,
            ADR0301_REPRESENTATIVE_GENERATOR_VERSION,
            ADR0301_REPRESENTATIVE_CONTEXT_COUNT,
            ADR0301_REPRESENTATIVE_CANDIDATE_ATTEMPTS,
            ADR0301_REPRESENTATIVE_SHA256,
            "adr0301-v3-representative",
        )
    return (
        ADR0301_QUALIFIED_POOL_SEED,
        ADR0301_QUALIFIED_POOL_GENERATOR_VERSION,
        ADR0301_QUALIFIED_POOL_CONTEXT_COUNT,
        ADR0301_QUALIFIED_POOL_CANDIDATE_ATTEMPTS,
        ADR0301_QUALIFIED_POOL_SHA256,
        "adr0301-v3-qualified-pool",
    )


@dataclass(frozen=True, slots=True)
class FreshWidthFourStructure:
    kind: FreshStructureKind
    seed: str
    generator_version: str
    candidate_attempts: int
    contexts: tuple[FreshWidthFourContext, ...]

    def __post_init__(self) -> None:
        seed, version, count, expected_attempts, expected_digest, id_prefix = (
            _structure_contract(self.kind)
        )
        if self.seed != seed:
            raise ValueError("fresh structure seed differs from ADR-0301")
        if self.generator_version != version:
            raise ValueError("fresh structure generator differs from ADR-0301")
        attempts = _require_integer(
            self.candidate_attempts,
            label="fresh structural candidate-attempt count",
            positive=True,
        )
        if attempts != expected_attempts:
            raise ValueError("fresh structural attempt count differs from ADR-0301")
        if not isinstance(self.contexts, tuple) or len(self.contexts) != count:
            raise TypeError("fresh structure has the wrong immutable context count")
        if any(
            not isinstance(context, FreshWidthFourContext)
            for context in self.contexts
        ):
            raise TypeError("fresh structure contains a nonsemantic context")
        expected_ids = tuple(
            f"{id_prefix}-c{index:02d}" for index in range(count)
        )
        if tuple(context.context_id for context in self.contexts) != expected_ids:
            raise ValueError("fresh structure ids or ordering differ from ADR-0301")
        semantic_keys = tuple(context.semantic_key for context in self.contexts)
        if len(set(semantic_keys)) != len(semantic_keys):
            raise ValueError("fresh structure repeats a semantic context")
        if self.digest != expected_digest:
            raise ValueError("fresh structure digest differs from its sealed identity")

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
            "baseline_commit": ADR0301_BASELINE_COMMIT,
            "candidate_attempts": self.candidate_attempts,
            "contexts": tuple(context.canonical_payload for context in self.contexts),
            "dependency_generator_version": ADR0293_GENERATOR_VERSION,
            "generator_version": self.generator_version,
            "kind": self.kind.value,
            "private_width": ADR0301_PRIVATE_WIDTH,
            "seed": self.seed,
            "source_sha256": ADR0301_COLLISION_REPAIR_SOURCE_SHA256,
            "structural_filter_version": ADR0301_STRUCTURAL_FILTER_VERSION,
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


def _private_pairs_width_four(
    cards: tuple[int, ...],
) -> tuple[tuple[int, int], ...]:
    if len(cards) != 2 * ADR0301_PRIVATE_WIDTH:
        raise AssertionError("fresh private-card slice must contain eight cards")
    return tuple(
        tuple(sorted(cards[offset : offset + 2]))
        for offset in range(0, len(cards), 2)
    )


def build_adr0301_fresh_structure(
    *,
    kind: FreshStructureKind,
) -> FreshWidthFourStructure:
    """Construct one frozen structure without importing or calling an oracle."""

    seed, version, count, _attempts, _digest, id_prefix = _structure_contract(kind)
    stream = _DigestStream(seed)
    contexts: list[FreshWidthFourContext] = []
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

        pot = ADR0293_POTS[stream.randbelow(len(ADR0293_POTS))]
        stack = ADR0293_STACKS[stream.randbelow(len(ADR0293_STACKS))]
        weights = tuple(
            1 + stream.randbelow(9)
            for _ in range(ADR0301_PRIVATE_WIDTH * ADR0301_PRIVATE_WIDTH)
        )
        denominator = sum(weights)
        probabilities = tuple(
            tuple(
                FreshExactProbability(
                    weights[row * ADR0301_PRIVATE_WIDTH + column],
                    denominator,
                )
                for column in range(ADR0301_PRIVATE_WIDTH)
            )
            for row in range(ADR0301_PRIVATE_WIDTH)
        )
        contexts.append(
            FreshWidthFourContext(
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

    return FreshWidthFourStructure(
        kind=kind,
        seed=seed,
        generator_version=version,
        candidate_attempts=candidate_attempts,
        contexts=tuple(contexts),
    )


__all__ = [
    "ADR0301_BASELINE_COMMIT",
    "ADR0301_COLLISION_REPAIR_SOURCE_SHA256",
    "ADR0301_PRIVATE_WIDTH",
    "ADR0301_QUALIFIED_POOL_CANDIDATE_ATTEMPTS",
    "ADR0301_QUALIFIED_POOL_CONTEXT_COUNT",
    "ADR0301_QUALIFIED_POOL_GENERATOR_VERSION",
    "ADR0301_QUALIFIED_POOL_SEED",
    "ADR0301_QUALIFIED_POOL_SHA256",
    "ADR0301_REPRESENTATIVE_CANDIDATE_ATTEMPTS",
    "ADR0301_REPRESENTATIVE_CONTEXT_COUNT",
    "ADR0301_REPRESENTATIVE_GENERATOR_VERSION",
    "ADR0301_REPRESENTATIVE_SEED",
    "ADR0301_REPRESENTATIVE_SHA256",
    "ADR0301_STRUCTURAL_FILTER_VERSION",
    "FreshExactProbability",
    "FreshStructureKind",
    "FreshWidthFourContext",
    "FreshWidthFourStructure",
    "build_adr0301_fresh_structure",
]
