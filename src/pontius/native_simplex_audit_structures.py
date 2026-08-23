"""Value-free LP and river-context structures frozen by ADR-0311.

The module owns deterministic inputs only.  It imports the exact card
evaluator, but no sizing oracle, LP backend, certificate, action candidate,
qualification owner, replay path, blueprint, resolver, or strategy module.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from math import gcd

from .river import evaluate_seven

ADR0311_MICRO_SEED = "pontius:adr-0311:native-simplex-robustness:micro-lp:sha256-stream:v1"
ADR0311_WIDTH4_SEED = "pontius:adr-0311:native-simplex-robustness:fresh-width-four:sha256-stream:v1"
ADR0311_MICRO_GENERATOR_VERSION = "candidate-independent-native-simplex-micro-lp-structure-v1"
ADR0311_WIDTH4_GENERATOR_VERSION = "candidate-independent-native-simplex-width-four-structure-v1"
ADR0311_DEPENDENCY_GENERATOR_VERSION = "sha256-fisher-yates-structural-river-panel-v1"
ADR0311_STRUCTURAL_FILTER_VERSION = "width4-both-signs-three-rows-three-columns-v1"
ADR0311_MICRO_CASE_COUNT = 48
ADR0311_WIDTH4_CONTEXT_COUNT = 64
ADR0311_WIDTH4_POTS = (6, 8, 10, 12, 14, 16, 20, 24, 30, 40)
ADR0311_WIDTH4_STACKS = (10, 12, 16, 20, 24, 30)

ADR0311_MICRO_RANDOM_ROW_CANDIDATE_ATTEMPTS = 312
ADR0311_MICRO_OBJECTIVE_CANDIDATE_ATTEMPTS = 48
ADR0311_MICRO_STRUCTURE_SHA256 = "4a6d0a021ead74aa37f9379dc15184a259c51a205033f1f405d84605af970e14"
ADR0311_WIDTH4_RAW_CARD_CANDIDATE_COUNT = 300
ADR0311_WIDTH4_STRUCTURE_SHA256 = "4bfde2a9937ceec206a40aa6c78c97335799413e6e8ef7de0fca6feef16dfcdc"

_UINT64_MODULUS = 1 << 64


def _require_integer(value: object, *, label: str, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < (1 if positive else 0):
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{label} must be {qualifier}")
    return value


class Sha256CounterStream:
    """Exact ADR-0293 SHA-256 counter words and unbiased bounded draws."""

    __slots__ = ("_counter", "_seed", "_word_index", "_words")

    def __init__(self, seed: str) -> None:
        if not isinstance(seed, str) or not seed:
            raise ValueError("ADR-0311 digest-stream seed must be nonempty")
        try:
            encoded = seed.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError("ADR-0311 digest-stream seed must be ASCII") from error
        self._seed = encoded
        self._counter = 0
        self._words: tuple[int, ...] = ()
        self._word_index = 0

    def _next_uint64(self) -> int:
        if self._word_index == len(self._words):
            if self._counter >= 1 << 64:
                raise OverflowError("ADR-0311 digest stream exhausted")
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
            raise TypeError("ADR-0311 random bound must be an integer")
        if bound <= 0:
            raise ValueError("ADR-0311 random bound must be positive")
        if bound > _UINT64_MODULUS:
            raise ValueError("ADR-0311 random bound exceeds word range")
        limit = _UINT64_MODULUS - (_UINT64_MODULUS % bound)
        while True:
            value = self._next_uint64()
            if value < limit:
                return value % bound


def fisher_yates_order(stream: Sha256CounterStream, count: int) -> tuple[int, ...]:
    """Return one exact stream-derived permutation of ``range(count)``."""

    length = _require_integer(count, label="Fisher-Yates item count")
    order = list(range(length))
    for index in range(length - 1, 0, -1):
        other = stream.randbelow(index + 1)
        order[index], order[other] = order[other], order[index]
    return tuple(order)


def _shuffled_deck(stream: Sha256CounterStream) -> tuple[int, ...]:
    deck = list(range(52))
    order = fisher_yates_order(stream, len(deck))
    return tuple(deck[index] for index in order)


def _private_pairs_width_four(cards: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    if len(cards) != 8:
        raise AssertionError("ADR-0311 private-card slice must contain eight cards")
    return tuple(tuple(sorted(cards[offset : offset + 2])) for offset in range(0, 8, 2))


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


def _structurally_admissible_width_four(signs: tuple[tuple[int, ...], ...]) -> bool:
    if len(signs) != 4 or any(len(row) != 4 for row in signs):
        return False
    if {value for row in signs for value in row} != {-1, 1}:
        return False
    if len(set(signs)) < 3:
        return False
    columns = tuple(tuple(row[column] for row in signs) for column in range(4))
    return len(set(columns)) >= 3


def _canonical_board(value: object) -> tuple[int, ...]:
    if not isinstance(value, tuple) or len(value) != 5:
        raise TypeError("ADR-0311 board must be an immutable five-card tuple")
    if any(
        isinstance(card, bool) or not isinstance(card, int) or card not in range(52)
        for card in value
    ):
        raise ValueError("ADR-0311 board contains an invalid card")
    if len(set(value)) != 5:
        raise ValueError("ADR-0311 board repeats a card")
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
class ExactMicroLinearProgram:
    """One bounded feasible exact-integer maximization input, without an optimum."""

    case_id: str
    objective: tuple[int, ...]
    coefficients: tuple[tuple[int, ...], ...]
    bounds: tuple[int, ...]
    feasible_witness: tuple[int, ...]
    lower_bounds: tuple[int, ...]
    upper_bounds: tuple[int, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            raise ValueError("micro-LP case id must be nonempty")
        if not isinstance(self.objective, tuple) or not self.objective:
            raise TypeError("micro-LP objective must be a nonempty immutable tuple")
        width = len(self.objective)
        if width not in range(2, 6):
            raise ValueError("micro-LP width must lie in the frozen two-through-five range")
        for label, values in (
            ("objective", self.objective),
            ("witness", self.feasible_witness),
            ("lower bounds", self.lower_bounds),
            ("upper bounds", self.upper_bounds),
            ("bounds", self.bounds),
        ):
            if not isinstance(values, tuple) or any(
                isinstance(value, bool) or not isinstance(value, int) for value in values
            ):
                raise TypeError(f"micro-LP {label} must contain exact integers")
        if len(self.feasible_witness) != width:
            raise ValueError("micro-LP witness width differs from its objective")
        if len(self.lower_bounds) != width or len(self.upper_bounds) != width:
            raise ValueError("micro-LP trusted bounds differ from its objective width")
        if any(value not in range(5) for value in self.feasible_witness):
            raise ValueError("micro-LP witness lies outside the frozen range")
        if any(
            lower < 0 or lower > witness
            for lower, witness in zip(
                self.lower_bounds,
                self.feasible_witness,
                strict=True,
            )
        ):
            raise ValueError("micro-LP lower bound does not contain its witness")
        if any(
            upper - witness not in range(1, 6)
            for upper, witness in zip(
                self.upper_bounds,
                self.feasible_witness,
                strict=True,
            )
        ):
            raise ValueError("micro-LP upper bound differs from the frozen witness offset")
        if not any(self.objective):
            raise ValueError("micro-LP objective must be nonzero")
        if any(value not in range(-5, 6) for value in self.objective):
            raise ValueError("micro-LP objective coefficient lies outside the frozen range")
        expected_row_count = 3 * width + 3
        if not isinstance(self.coefficients, tuple) or len(self.coefficients) != expected_row_count:
            raise TypeError("micro-LP has the wrong immutable row count")
        if len(self.bounds) != expected_row_count:
            raise TypeError("micro-LP row bounds do not align")
        if any(
            not isinstance(row, tuple)
            or len(row) != width
            or any(isinstance(value, bool) or not isinstance(value, int) for value in row)
            for row in self.coefficients
        ):
            raise TypeError("micro-LP rows must contain exact integers at the frozen width")

        for variable in range(width):
            upper_row = tuple(1 if index == variable else 0 for index in range(width))
            lower_row = tuple(-1 if index == variable else 0 for index in range(width))
            if (
                self.coefficients[variable] != upper_row
                or self.bounds[variable] != self.upper_bounds[variable]
            ):
                raise ValueError("micro-LP explicit upper row differs from its trusted bound")
            lower_index = width + variable
            if (
                self.coefficients[lower_index] != lower_row
                or self.bounds[lower_index] != -self.lower_bounds[variable]
            ):
                raise ValueError("micro-LP explicit lower row differs from its trusted bound")
        for row, bound in zip(
            self.coefficients[2 * width :],
            self.bounds[2 * width :],
            strict=True,
        ):
            if not any(row) or any(value not in range(-5, 6) for value in row):
                raise ValueError("micro-LP random row differs from the frozen coefficient rule")
            witness_value = sum(
                coefficient * value
                for coefficient, value in zip(row, self.feasible_witness, strict=True)
            )
            if bound - witness_value not in range(6):
                raise ValueError("micro-LP random-row slack differs from the frozen range")
        if any(
            sum(
                coefficient * value
                for coefficient, value in zip(row, self.feasible_witness, strict=True)
            )
            > bound
            for row, bound in zip(self.coefficients, self.bounds, strict=True)
        ):
            raise ValueError("micro-LP stored witness is not feasible")

    @property
    def variable_count(self) -> int:
        return len(self.objective)

    @property
    def trusted_box_bounds(self) -> tuple[tuple[int, int], ...]:
        return tuple((0, upper) for upper in self.upper_bounds)

    @property
    def semantic_payload(self) -> dict[str, object]:
        return {
            "bounds": self.bounds,
            "coefficients": self.coefficients,
            "feasible_witness": self.feasible_witness,
            "lower_bounds": self.lower_bounds,
            "objective": self.objective,
            "trusted_box_bounds": self.trusted_box_bounds,
            "upper_bounds": self.upper_bounds,
            "version": "adr0311-exact-micro-lp-input-v1",
        }

    @property
    def semantic_digest(self) -> str:
        encoded = json.dumps(
            self.semantic_payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()

    @property
    def canonical_payload(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "input": self.semantic_payload,
            "version": "adr0311-exact-micro-lp-record-v1",
        }

    @property
    def digest(self) -> str:
        encoded = json.dumps(
            self.canonical_payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class ExactMicroLpStructure:
    seed: str
    generator_version: str
    random_row_candidate_attempts: int
    objective_candidate_attempts: int
    cases: tuple[ExactMicroLinearProgram, ...]

    def __post_init__(self) -> None:
        if self.seed != ADR0311_MICRO_SEED:
            raise ValueError("micro-LP structure seed differs from ADR-0311")
        if self.generator_version != ADR0311_MICRO_GENERATOR_VERSION:
            raise ValueError("micro-LP structure generator differs from ADR-0311")
        for label, value in (
            ("random-row attempts", self.random_row_candidate_attempts),
            ("objective attempts", self.objective_candidate_attempts),
        ):
            _require_integer(value, label=f"micro-LP {label}", positive=True)
        if not isinstance(self.cases, tuple) or len(self.cases) != ADR0311_MICRO_CASE_COUNT:
            raise TypeError("micro-LP structure has the wrong immutable case count")
        if any(not isinstance(case, ExactMicroLinearProgram) for case in self.cases):
            raise TypeError("micro-LP structure contains a nonsemantic case")
        expected_ids = tuple(
            f"adr0311-simplex-micro-c{index:02d}" for index in range(ADR0311_MICRO_CASE_COUNT)
        )
        if tuple(case.case_id for case in self.cases) != expected_ids:
            raise ValueError("micro-LP case ids or ordering differ from ADR-0311")
        if tuple(case.variable_count for case in self.cases) != tuple(
            2 + index % 4 for index in range(ADR0311_MICRO_CASE_COUNT)
        ):
            raise ValueError("micro-LP widths or ordering differ from ADR-0311")
        if len({case.semantic_digest for case in self.cases}) != len(self.cases):
            raise ValueError("micro-LP structure repeats an exact input")
        if self.random_row_candidate_attempts != ADR0311_MICRO_RANDOM_ROW_CANDIDATE_ATTEMPTS:
            raise ValueError("micro-LP random-row attempt count differs from its sealed identity")
        if self.objective_candidate_attempts != ADR0311_MICRO_OBJECTIVE_CANDIDATE_ATTEMPTS:
            raise ValueError("micro-LP objective attempt count differs from its sealed identity")
        if self.digest != ADR0311_MICRO_STRUCTURE_SHA256:
            raise ValueError("micro-LP structure digest differs from its sealed identity")

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
            "cases": tuple(case.canonical_payload for case in self.cases),
            "generator_version": self.generator_version,
            "objective_candidate_attempts": self.objective_candidate_attempts,
            "random_row_candidate_attempts": self.random_row_candidate_attempts,
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


@dataclass(frozen=True, slots=True)
class AuditExactProbability:
    """One exact positive value-free joint-deal probability."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        numerator = _require_integer(
            self.numerator,
            label="ADR-0311 probability numerator",
            positive=True,
        )
        denominator = _require_integer(
            self.denominator,
            label="ADR-0311 probability denominator",
            positive=True,
        )
        if numerator > denominator:
            raise ValueError("ADR-0311 probability must lie in (0, 1]")
        common = gcd(numerator, denominator)
        object.__setattr__(self, "numerator", numerator // common)
        object.__setattr__(self, "denominator", denominator // common)

    @property
    def fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


@dataclass(frozen=True, slots=True)
class AuditWidthFourContext:
    """One candidate-free exact card/chip/range context."""

    context_id: str
    board: tuple[int, ...]
    pot: int
    stack: int
    minimum_bet: int
    opener_hands: tuple[tuple[int, int], ...]
    responder_hands: tuple[tuple[int, int], ...]
    joint_probabilities: tuple[tuple[AuditExactProbability, ...], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.context_id, str) or not self.context_id.strip():
            raise ValueError("ADR-0311 context id must be nonempty")
        board = _canonical_board(self.board)
        pot = _require_integer(self.pot, label="ADR-0311 pot", positive=True)
        stack = _require_integer(self.stack, label="ADR-0311 stack", positive=True)
        minimum = _require_integer(
            self.minimum_bet,
            label="ADR-0311 minimum bet",
            positive=True,
        )
        if pot not in ADR0311_WIDTH4_POTS:
            raise ValueError("ADR-0311 pot differs from the frozen set")
        if stack not in ADR0311_WIDTH4_STACKS:
            raise ValueError("ADR-0311 stack differs from the frozen set")
        if minimum != 2 or minimum > stack:
            raise ValueError("ADR-0311 minimum bet differs from the frozen contract")
        if not isinstance(self.opener_hands, tuple) or len(self.opener_hands) != 4:
            raise TypeError("ADR-0311 opener axis must contain four hands")
        if not isinstance(self.responder_hands, tuple) or len(self.responder_hands) != 4:
            raise TypeError("ADR-0311 responder axis must contain four hands")
        opener = tuple(
            _canonical_hand(hand, label=f"ADR-0311 opener hand {index}")
            for index, hand in enumerate(self.opener_hands)
        )
        responder = tuple(
            _canonical_hand(hand, label=f"ADR-0311 responder hand {index}")
            for index, hand in enumerate(self.responder_hands)
        )
        physical_cards = (
            *board,
            *(card for hand in opener for card in hand),
            *(card for hand in responder for card in hand),
        )
        if len(physical_cards) != 21 or len(set(physical_cards)) != 21:
            raise ValueError("ADR-0311 context must contain 21 distinct cards")
        probabilities = self.joint_probabilities
        if not isinstance(probabilities, tuple) or len(probabilities) != 4:
            raise TypeError("ADR-0311 joint range must contain four rows")
        if any(not isinstance(row, tuple) or len(row) != 4 for row in probabilities):
            raise TypeError("ADR-0311 joint range rows must contain four values")
        if any(
            not isinstance(probability, AuditExactProbability)
            for row in probabilities
            for probability in row
        ):
            raise TypeError("ADR-0311 joint range contains a nonsemantic probability")
        total = sum(
            (probability.fraction for row in probabilities for probability in row),
            start=Fraction(0),
        )
        if total != 1:
            raise ValueError("ADR-0311 probabilities must sum exactly to one")
        if not _structurally_admissible_width_four(_showdown_signs(board, opener, responder)):
            raise ValueError("ADR-0311 context fails the frozen showdown filter")
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
        return _showdown_signs(self.board, self.opener_hands, self.responder_hands)

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

    @property
    def digest(self) -> str:
        payload = {
            "context": self.canonical_payload,
            "version": "adr0311-width-four-structural-context-v1",
        }
        encoded = json.dumps(
            payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class FreshWidthFourAuditStructure:
    seed: str
    generator_version: str
    raw_card_candidate_count: int
    contexts: tuple[AuditWidthFourContext, ...]

    def __post_init__(self) -> None:
        if self.seed != ADR0311_WIDTH4_SEED:
            raise ValueError("width-four audit seed differs from ADR-0311")
        if self.generator_version != ADR0311_WIDTH4_GENERATOR_VERSION:
            raise ValueError("width-four audit generator differs from ADR-0311")
        _require_integer(
            self.raw_card_candidate_count,
            label="width-four raw card candidate count",
            positive=True,
        )
        if (
            not isinstance(self.contexts, tuple)
            or len(self.contexts) != ADR0311_WIDTH4_CONTEXT_COUNT
        ):
            raise TypeError("width-four audit structure has the wrong immutable context count")
        if any(not isinstance(context, AuditWidthFourContext) for context in self.contexts):
            raise TypeError("width-four audit structure contains a nonsemantic context")
        expected_ids = tuple(
            f"adr0311-simplex-width4-c{index:02d}" for index in range(ADR0311_WIDTH4_CONTEXT_COUNT)
        )
        if tuple(context.context_id for context in self.contexts) != expected_ids:
            raise ValueError("width-four audit ids or ordering differ from ADR-0311")
        expected_chips = tuple(
            (
                ADR0311_WIDTH4_POTS[index % len(ADR0311_WIDTH4_POTS)],
                ADR0311_WIDTH4_STACKS[
                    (index // len(ADR0311_WIDTH4_POTS)) % len(ADR0311_WIDTH4_STACKS)
                ],
            )
            for index in range(ADR0311_WIDTH4_CONTEXT_COUNT)
        )
        if tuple((context.pot, context.stack) for context in self.contexts) != expected_chips:
            raise ValueError("width-four audit chip grid differs from ADR-0311")
        semantic_keys = tuple(context.semantic_key for context in self.contexts)
        if len(set(semantic_keys)) != len(semantic_keys):
            raise ValueError("width-four audit structure repeats a semantic context")
        if self.raw_card_candidate_count != ADR0311_WIDTH4_RAW_CARD_CANDIDATE_COUNT:
            raise ValueError("width-four raw card count differs from its sealed identity")
        if self.digest != ADR0311_WIDTH4_STRUCTURE_SHA256:
            raise ValueError("width-four audit digest differs from its sealed identity")

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
            "chip_assignment_version": "pot-fast-stack-slow-cartesian-plus-four-v1",
            "contexts": tuple(context.canonical_payload for context in self.contexts),
            "dependency_generator_version": ADR0311_DEPENDENCY_GENERATOR_VERSION,
            "generator_version": self.generator_version,
            "minimum_bet": 2,
            "pots": ADR0311_WIDTH4_POTS,
            "private_width": 4,
            "raw_card_candidate_count": self.raw_card_candidate_count,
            "seed": self.seed,
            "stacks": ADR0311_WIDTH4_STACKS,
            "structural_filter_version": ADR0311_STRUCTURAL_FILTER_VERSION,
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


def build_adr0311_micro_lp_structure() -> ExactMicroLpStructure:
    """Construct the frozen exact inputs without enumerating any optimum."""

    stream = Sha256CounterStream(ADR0311_MICRO_SEED)
    cases: list[ExactMicroLinearProgram] = []
    random_row_candidate_attempts = 0
    objective_candidate_attempts = 0
    for record_index in range(ADR0311_MICRO_CASE_COUNT):
        variable_count = 2 + record_index % 4
        witness = tuple(stream.randbelow(5) for _ in range(variable_count))
        upper_bounds = tuple(value + 1 + stream.randbelow(5) for value in witness)
        lower_bounds = tuple(stream.randbelow(value + 1) for value in witness)
        coefficients: list[tuple[int, ...]] = []
        bounds: list[int] = []
        for variable in range(variable_count):
            coefficients.append(
                tuple(1 if index == variable else 0 for index in range(variable_count))
            )
            bounds.append(upper_bounds[variable])
        for variable in range(variable_count):
            coefficients.append(
                tuple(-1 if index == variable else 0 for index in range(variable_count))
            )
            bounds.append(-lower_bounds[variable])
        for _ in range(variable_count + 3):
            while True:
                random_row_candidate_attempts += 1
                row = tuple(stream.randbelow(11) - 5 for _ in range(variable_count))
                if any(row):
                    break
            slack = stream.randbelow(6)
            coefficients.append(row)
            bounds.append(
                sum(coefficient * value for coefficient, value in zip(row, witness, strict=True))
                + slack
            )
        while True:
            objective_candidate_attempts += 1
            objective = tuple(stream.randbelow(11) - 5 for _ in range(variable_count))
            if any(objective):
                break
        cases.append(
            ExactMicroLinearProgram(
                case_id=f"adr0311-simplex-micro-c{record_index:02d}",
                objective=objective,
                coefficients=tuple(coefficients),
                bounds=tuple(bounds),
                feasible_witness=witness,
                lower_bounds=lower_bounds,
                upper_bounds=upper_bounds,
            )
        )
    return ExactMicroLpStructure(
        seed=ADR0311_MICRO_SEED,
        generator_version=ADR0311_MICRO_GENERATOR_VERSION,
        random_row_candidate_attempts=random_row_candidate_attempts,
        objective_candidate_attempts=objective_candidate_attempts,
        cases=tuple(cases),
    )


def build_adr0311_width_four_structure() -> FreshWidthFourAuditStructure:
    """Construct the frozen fresh contexts without importing a value owner."""

    stream = Sha256CounterStream(ADR0311_WIDTH4_SEED)
    contexts: list[AuditWidthFourContext] = []
    raw_card_candidate_count = 0
    while len(contexts) < ADR0311_WIDTH4_CONTEXT_COUNT:
        raw_card_candidate_count += 1
        deck = _shuffled_deck(stream)
        board = deck[:5]
        opener_hands = _private_pairs_width_four(deck[5:13])
        responder_hands = _private_pairs_width_four(deck[13:21])
        if not _structurally_admissible_width_four(
            _showdown_signs(board, opener_hands, responder_hands)
        ):
            continue
        weights = tuple(1 + stream.randbelow(9) for _ in range(16))
        denominator = sum(weights)
        probabilities = tuple(
            tuple(
                AuditExactProbability(weights[row * 4 + column], denominator) for column in range(4)
            )
            for row in range(4)
        )
        context_index = len(contexts)
        contexts.append(
            AuditWidthFourContext(
                context_id=f"adr0311-simplex-width4-c{context_index:02d}",
                board=board,
                pot=ADR0311_WIDTH4_POTS[context_index % len(ADR0311_WIDTH4_POTS)],
                stack=ADR0311_WIDTH4_STACKS[
                    (context_index // len(ADR0311_WIDTH4_POTS)) % len(ADR0311_WIDTH4_STACKS)
                ],
                minimum_bet=2,
                opener_hands=opener_hands,
                responder_hands=responder_hands,
                joint_probabilities=probabilities,
            )
        )
    return FreshWidthFourAuditStructure(
        seed=ADR0311_WIDTH4_SEED,
        generator_version=ADR0311_WIDTH4_GENERATOR_VERSION,
        raw_card_candidate_count=raw_card_candidate_count,
        contexts=tuple(contexts),
    )


__all__ = [
    "ADR0311_DEPENDENCY_GENERATOR_VERSION",
    "ADR0311_MICRO_CASE_COUNT",
    "ADR0311_MICRO_GENERATOR_VERSION",
    "ADR0311_MICRO_OBJECTIVE_CANDIDATE_ATTEMPTS",
    "ADR0311_MICRO_RANDOM_ROW_CANDIDATE_ATTEMPTS",
    "ADR0311_MICRO_SEED",
    "ADR0311_MICRO_STRUCTURE_SHA256",
    "ADR0311_STRUCTURAL_FILTER_VERSION",
    "ADR0311_WIDTH4_CONTEXT_COUNT",
    "ADR0311_WIDTH4_GENERATOR_VERSION",
    "ADR0311_WIDTH4_POTS",
    "ADR0311_WIDTH4_RAW_CARD_CANDIDATE_COUNT",
    "ADR0311_WIDTH4_SEED",
    "ADR0311_WIDTH4_STACKS",
    "ADR0311_WIDTH4_STRUCTURE_SHA256",
    "AuditExactProbability",
    "AuditWidthFourContext",
    "ExactMicroLinearProgram",
    "ExactMicroLpStructure",
    "FreshWidthFourAuditStructure",
    "Sha256CounterStream",
    "build_adr0311_micro_lp_structure",
    "build_adr0311_width_four_structure",
    "fisher_yates_order",
]
