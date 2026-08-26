"""CPU-only fixed-width comparison for the exact occupied-card quotient.

This module implements ADR-0436 under ADR-0437's nonvacuous provenance
overlay.  It is deliberately standard-library only.  It neither imports a
device stack nor constructs the unopened population-25 or literal-45 numeric
fixtures.  Literal-45 entry points below return geometry and symbolic ledgers
only.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from hashlib import sha256
import ast
import importlib.util
import json
import math
from math import comb, gcd
from pathlib import Path
import sys
from typing import Callable, Iterable, Mapping, Sequence

_ROOT = Path(__file__).parents[2]
_EXACT_MODULE_NAME = "pontius.legal_river_quotient_exact_integer_operator"
if _EXACT_MODULE_NAME in sys.modules:
    exact = sys.modules[_EXACT_MODULE_NAME]
else:
    _exact_path = _ROOT / "src/pontius/legal_river_quotient_exact_integer_operator.py"
    _exact_spec = importlib.util.spec_from_file_location(
        _EXACT_MODULE_NAME, _exact_path
    )
    if _exact_spec is None or _exact_spec.loader is None:
        raise ImportError("exact integer authority cannot be loaded")
    exact = importlib.util.module_from_spec(_exact_spec)
    sys.modules[_exact_spec.name] = exact
    _exact_spec.loader.exec_module(exact)
_CONFIG_V1 = (
    _ROOT
    / "experiments/configs/"
    "legal-river-quotient-fixed-width-work-comparison-v1.json"
)
_CONFIG_V2 = (
    _ROOT
    / "experiments/configs/"
    "legal-river-quotient-fixed-width-work-comparison-v2-provenance.json"
)
_ADR0436 = (
    _ROOT
    / "docs/decisions/"
    "ADR-0436-preregister-the-fixed-width-and-certificate-work-comparison.md"
)
_ADR0437 = (
    _ROOT
    / "docs/decisions/"
    "ADR-0437-require-armed-literal-escape-mutations-before-source-seal.md"
)

PREREGISTERED_CONFIG_SHA256 = (
    "89a8e4d8561f97f79cdb5447add02cf130d0e535dd1e3e6da3e49d80d7802ffc"
)
CORRECTION_CONFIG_SHA256 = (
    "b29598d9755767aceedca497f0aaf3b66fd0901a98f9a084b64034e072e52da1"
)
ADR0436_SHA256 = (
    "ae874339b98b65fb77825763eaf9bd31f49d361b3ae2adf3c3ec2e2d3da23e9e"
)
ADR0437_SHA256 = (
    "25214d249945f1f88b82836575442805465f90bcf262df0e371ed4ef20e305af"
)

WORD_BITS = 64
WORD_BASE = 1 << WORD_BITS
WORD_MASK = WORD_BASE - 1
MONTGOMERY_R = WORD_BASE
COMMON_SCALE = exact.COMMON_SCALE
SOURCE_CARDS = exact.SOURCE_CARDS
QUERY_CARDS = exact.QUERY_CARDS
QUERY_LABELS = exact.QUERY_LABELS


class RRNSChannelFaultDetected(ArithmeticError):
    """Typed fail-closed terminal for the frozen single-channel check."""


class IncompleteGlobalClosure(ArithmeticError):
    """Typed rejection for a scan that omits or reorders the frozen domain."""


def canonical_lf_bytes(data: bytes) -> bytes:
    """Production CRLF-only normalizer bound by ADR-0437."""

    if type(data) is not bytes:
        raise TypeError("canonical input must be bytes")
    return data.replace(b"\r\n", b"\n")


def independent_canonical_lf_bytes(data: bytes) -> bytes:
    """Independently normalize CRLF with a forward byte state machine."""

    if type(data) is not bytes:
        raise TypeError("independent canonical input must be bytes")
    output = bytearray()
    index = 0
    while index < len(data):
        current = data[index]
        if current == 13 and index + 1 < len(data) and data[index + 1] == 10:
            output.append(10)
            index += 2
        else:
            output.append(current)
            index += 1
    return bytes(output)


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"fixed-width provenance path is absent: {path}")
    return sha256(canonical_lf_bytes(path.read_bytes())).hexdigest()


def independent_canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"independent provenance path is absent: {path}")
    return sha256(independent_canonical_lf_bytes(path.read_bytes())).hexdigest()


@dataclass(frozen=True, slots=True)
class ArmedMutationReceipt:
    relative_path: str
    occurrence_count: int
    canonical_lf_sha256: str
    forbidden_mutation_sha256: str


def literal_escape_mutation_receipt(
    path: Path,
    *,
    expected_occurrences: int,
    require_armed: bool,
) -> ArmedMutationReceipt:
    """Count the literal trigger before evaluating its forbidden rewrite."""

    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"literal-mutation target is absent: {path}")
    if isinstance(expected_occurrences, bool) or not isinstance(
        expected_occurrences, int
    ):
        raise TypeError("expected occurrence count must be an integer")
    raw = path.read_bytes()
    token = bytes((92, 114, 92, 110))
    replacement = bytes((92, 110))
    count = raw.count(token)
    if count != expected_occurrences:
        raise ValueError("literal-mutation occurrence count differs")
    if require_armed and count == 0:
        raise ValueError("unarmed_literal_escape_mutation")
    production = canonical_lf_bytes(raw)
    independent = independent_canonical_lf_bytes(raw)
    if production != independent:
        raise ValueError("correct canonical-LF normalizers differ")
    mutated_raw = raw.replace(token, replacement)
    mutated = canonical_lf_bytes(mutated_raw)
    canonical_digest = sha256(production).hexdigest()
    mutation_digest = sha256(mutated).hexdigest()
    if count:
        if mutated_raw == raw or mutated == production:
            raise ValueError("armed literal mutation did not change bytes")
        if mutation_digest == canonical_digest:
            raise ValueError("armed literal mutation did not change digest")
    elif mutated_raw != raw or mutation_digest != canonical_digest:
        raise ValueError("token-free literal mutation was not the identity")
    try:
        relative = path.relative_to(_ROOT).as_posix()
    except ValueError:
        relative = str(path)
    return ArmedMutationReceipt(
        relative_path=relative,
        occurrence_count=count,
        canonical_lf_sha256=canonical_digest,
        forbidden_mutation_sha256=mutation_digest,
    )


def _load_json_config(path: Path, expected_hash: str, schema: str) -> dict[str, object]:
    if not path.is_file():
        raise ValueError("fixed-width comparison config is absent")
    raw = path.read_bytes()
    if len(raw) > 1_048_576:
        raise ValueError("fixed-width comparison config exceeds byte ceiling")
    production = canonical_lf_bytes(raw)
    independent = independent_canonical_lf_bytes(raw)
    if production != independent or sha256(production).hexdigest() != expected_hash:
        raise ValueError("fixed-width comparison config digest differs")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict) or parsed.get("schema_version") != schema:
        raise ValueError("fixed-width comparison config schema differs")
    return parsed


def load_preregistered_config() -> dict[str, object]:
    return _load_json_config(
        _CONFIG_V1,
        PREREGISTERED_CONFIG_SHA256,
        "legal-river-quotient-fixed-width-work-comparison-v1",
    )


def load_correction_config() -> dict[str, object]:
    return _load_json_config(
        _CONFIG_V2,
        CORRECTION_CONFIG_SHA256,
        "legal-river-quotient-fixed-width-work-comparison-v2-provenance",
    )


def verify_preregistered_contract(*, require_self_seal_targets: bool = True) -> None:
    """Rebind both configs, both ADRs, and the complete transitive scan."""

    base = load_preregistered_config()
    correction = load_correction_config()
    if canonical_lf_sha256(_ADR0436) != ADR0436_SHA256:
        raise ValueError("ADR-0436 digest differs")
    if canonical_lf_sha256(_ADR0437) != ADR0437_SHA256:
        raise ValueError("ADR-0437 digest differs")
    if correction.get("parent_v1_config", {}).get("canonical_lf_sha256") != (
        PREREGISTERED_CONFIG_SHA256
    ):
        raise ValueError("correction does not bind comparison V1")
    if correction.get("parent_adr", {}).get("canonical_lf_sha256") != (
        ADR0436_SHA256
    ):
        raise ValueError("correction does not bind ADR-0436")
    expected_parents = base.get("expected_parents")
    if not isinstance(expected_parents, Mapping):
        raise ValueError("comparison parent map differs")
    for label, row in expected_parents.items():
        if not isinstance(row, Mapping):
            raise ValueError(f"comparison parent row differs: {label}")
        path = _ROOT / str(row.get("relative_path"))
        if canonical_lf_sha256(path) != row.get("canonical_lf_sha256"):
            raise ValueError(f"comparison parent differs: {label}")
        if independent_canonical_lf_sha256(path) != row.get("canonical_lf_sha256"):
            raise ValueError(f"independent comparison parent differs: {label}")
    scan = correction.get("frozen_existing_transitive_bound_file_scan")
    if not isinstance(scan, Mapping) or len(scan) != 17:
        raise ValueError("corrected transitive scan differs")
    armed = set()
    for label, row in scan.items():
        if not isinstance(row, Mapping):
            raise ValueError(f"corrected scan row differs: {label}")
        count = row.get("required_occurrences")
        if isinstance(count, bool) or not isinstance(count, int):
            raise ValueError(f"corrected scan count differs: {label}")
        receipt = literal_escape_mutation_receipt(
            _ROOT / str(row.get("relative_path")),
            expected_occurrences=count,
            require_armed=False,
        )
        if (
            receipt.canonical_lf_sha256 != row.get("canonical_lf_sha256")
            or receipt.forbidden_mutation_sha256
            != row.get("forbidden_mutation_sha256")
        ):
            raise ValueError(f"corrected scan digest differs: {label}")
        if count:
            armed.add(label)
    if armed != {
        "legal_river_quotient_bridge",
        "legal_river_quotient_cuda_consumer",
        "legal_river_quotient_cuda_compensated_tiles",
        "exact_integer_source",
        "exact_integer_controls",
    }:
        raise ValueError("corrected armed parent set differs")
    if require_self_seal_targets:
        targets = correction.get("armed_self_seal_targets")
        if not isinstance(targets, Mapping):
            raise ValueError("corrected self-seal target map differs")
        for label in ("comparison_source", "comparison_controls"):
            row = targets.get(label)
            if not isinstance(row, Mapping):
                raise ValueError(f"corrected self-seal row differs: {label}")
            literal_escape_mutation_receipt(
                _ROOT / str(row.get("relative_path")),
                expected_occurrences=int(row.get("required_raw_token_occurrences", -1)),
                require_armed=True,
            )
    claims = base.get("claims")
    correction_claims = correction.get("claims")
    if not isinstance(claims, Mapping) or not all(
        value is None or value is False for value in claims.values()
    ):
        raise ValueError("comparison preregistered claims are open")
    if not isinstance(correction_claims, Mapping) or not all(
        key == "provenance_completeness_correction_recorded"
        or value is None
        or value is False
        for key, value in correction_claims.items()
    ):
        raise ValueError("comparison correction claims are open")
    if correction_claims.get("provenance_completeness_correction_recorded") is not True:
        raise ValueError("comparison correction is not recorded")
    validate_no_scale_inverse_constants(base)
    validate_no_scale_inverse_constants(correction)
    exact.verify_preregistered_contract()
    verify_frozen_bound_profile(base)
    validate_frozen_rrns(base)
    verify_literal_45_formulas(base)


def _require_plain_integer(value: object, *, label: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    return value


@dataclass(frozen=True, slots=True)
class SignedLimbPlan:
    absolute_bound: int
    required_signed_bits: int
    mathematical_limbs: int
    allocated_limbs: int

    def __post_init__(self) -> None:
        bound = _require_plain_integer(
            self.absolute_bound, label="signed-limb plan bound", minimum=0
        )
        bits = 1 if bound == 0 else bound.bit_length() + 1
        mathematical = (bits + WORD_BITS - 1) // WORD_BITS
        if self.required_signed_bits != bits:
            raise ValueError("signed-limb required-bit count differs")
        if self.mathematical_limbs != mathematical:
            raise ValueError("signed-limb mathematical width differs")
        if self.allocated_limbs != mathematical + 1:
            raise OverflowError("fixed-width allocation omits the required guard limb")

    @classmethod
    def from_bound(cls, absolute_bound: int) -> "SignedLimbPlan":
        bound = _require_plain_integer(
            absolute_bound, label="signed-limb absolute bound", minimum=0
        )
        bits = 1 if bound == 0 else bound.bit_length() + 1
        mathematical = (bits + WORD_BITS - 1) // WORD_BITS
        return cls(bound, bits, mathematical, mathematical + 1)


@dataclass(frozen=True, slots=True)
class LimbWork:
    word_add_steps: int = 0
    word_subtract_steps: int = 0
    word_negate_steps: int = 0
    wide_products: int = 0
    carry_steps: int = 0

    def plus(self, other: "LimbWork") -> "LimbWork":
        return LimbWork(
            *(getattr(self, field.name) + getattr(other, field.name) for field in fields(self))
        )


@dataclass(frozen=True, slots=True)
class SignedLimbs:
    """One fixed-width signed value with one exact sign-extension guard."""

    words: tuple[int, ...]
    plan: SignedLimbPlan

    def __post_init__(self) -> None:
        if len(self.words) != self.plan.allocated_limbs:
            raise OverflowError("fixed-width allocation omits the required guard limb")
        if any(isinstance(word, bool) or not isinstance(word, int) for word in self.words):
            raise TypeError("limb words must be integers")
        if any(word < 0 or word > WORD_MASK for word in self.words):
            raise OverflowError("limb word lies outside uint64")
        sign = WORD_MASK if self.words[self.plan.mathematical_limbs - 1] >> 63 else 0
        if self.words[-1] != sign:
            raise OverflowError("guard limb is not exact sign extension")
        unsigned = 0
        for index in range(len(self.words) - 1, -1, -1):
            unsigned = (unsigned << WORD_BITS) | self.words[index]
        if self.words[-1] >> 63:
            unsigned -= 1 << (WORD_BITS * len(self.words))
        if abs(unsigned) > self.plan.absolute_bound:
            raise OverflowError("stored limb value exceeds its semantic bound")

    @classmethod
    def encode(cls, value: int, plan: SignedLimbPlan) -> "SignedLimbs":
        item = _require_plain_integer(value, label="signed limb input")
        if abs(item) > plan.absolute_bound:
            raise OverflowError("signed limb input exceeds its semantic bound")
        bits = WORD_BITS * plan.allocated_limbs
        encoded = item & ((1 << bits) - 1)
        words = tuple((encoded >> (WORD_BITS * index)) & WORD_MASK for index in range(plan.allocated_limbs))
        result = cls(words, plan)
        if result.decode() != item:
            raise AssertionError("signed limb encoding changed an admitted integer")
        return result

    def decode(self) -> int:
        unsigned = 0
        for index in range(len(self.words) - 1, -1, -1):
            unsigned = (unsigned << WORD_BITS) | self.words[index]
        bits = WORD_BITS * len(self.words)
        if self.words[-1] >> 63:
            unsigned -= 1 << bits
        if abs(unsigned) > self.plan.absolute_bound:
            raise OverflowError("decoded limb value exceeds its semantic bound")
        return unsigned


def _finish_limb_operation(
    words: Sequence[int], plan: SignedLimbPlan
) -> SignedLimbs:
    result = SignedLimbs(tuple(words), plan)
    result.decode()
    return result


def limb_add(left: SignedLimbs, right: SignedLimbs) -> tuple[SignedLimbs, LimbWork]:
    if left.plan != right.plan:
        raise ValueError("limb addition plans differ")
    output = []
    carry = 0
    for a, b in zip(left.words, right.words, strict=True):
        total = a + b + carry
        output.append(total & WORD_MASK)
        carry = total >> WORD_BITS
    result = _finish_limb_operation(output, left.plan)
    return result, LimbWork(word_add_steps=len(output), carry_steps=len(output))


def limb_subtract(
    left: SignedLimbs, right: SignedLimbs
) -> tuple[SignedLimbs, LimbWork]:
    if left.plan != right.plan:
        raise ValueError("limb subtraction plans differ")
    output = []
    borrow = 0
    for a, b in zip(left.words, right.words, strict=True):
        difference = a - b - borrow
        if difference < 0:
            difference += WORD_BASE
            borrow = 1
        else:
            borrow = 0
        output.append(difference)
    result = _finish_limb_operation(output, left.plan)
    return result, LimbWork(word_subtract_steps=len(output), carry_steps=len(output))


def _twos_complement_words(words: Sequence[int]) -> tuple[tuple[int, ...], LimbWork]:
    output = []
    carry = 1
    for word in words:
        total = (word ^ WORD_MASK) + carry
        output.append(total & WORD_MASK)
        carry = total >> WORD_BITS
    return tuple(output), LimbWork(word_negate_steps=len(output), carry_steps=len(output))


def limb_negate(value: SignedLimbs) -> tuple[SignedLimbs, LimbWork]:
    words, work = _twos_complement_words(value.words)
    return _finish_limb_operation(words, value.plan), work


def _unsigned_multiply_small(
    words: Sequence[int], factor: int
) -> tuple[tuple[int, ...], LimbWork]:
    multiplier = _require_plain_integer(factor, label="unsigned small factor", minimum=0)
    output = []
    carry = 0
    wide = 0
    for word in words:
        product = word * multiplier + carry
        output.append(product & WORD_MASK)
        carry = product >> WORD_BITS
        wide += 1
    if carry:
        raise OverflowError("small product exceeds its fixed-width allocation")
    return tuple(output), LimbWork(wide_products=wide, carry_steps=len(output))


def _unsigned_magnitude(value: SignedLimbs) -> tuple[tuple[int, ...], bool, LimbWork]:
    negative = bool(value.words[-1] >> 63)
    if not negative:
        return value.words, False, LimbWork()
    magnitude, work = _twos_complement_words(value.words)
    return magnitude, True, work


def limb_multiply_small(
    value: SignedLimbs, factor: int
) -> tuple[SignedLimbs, LimbWork]:
    signed_factor = _require_plain_integer(factor, label="signed small factor")
    magnitude, negative, work = _unsigned_magnitude(value)
    words, multiply_work = _unsigned_multiply_small(magnitude, abs(signed_factor))
    work = work.plus(multiply_work)
    if negative ^ (signed_factor < 0):
        words, negate_work = _twos_complement_words(words)
        work = work.plus(negate_work)
    return _finish_limb_operation(words, value.plan), work


def _unsigned_schoolbook_product(
    left: Sequence[int], right: Sequence[int], destination_words: int
) -> tuple[tuple[int, ...], LimbWork]:
    length = _require_plain_integer(
        destination_words, label="schoolbook destination words", minimum=1
    )
    output = [0] * length
    wide_products = 0
    carry_steps = 0
    for left_index, left_word in enumerate(left):
        carry = 0
        for right_index, right_word in enumerate(right):
            position = left_index + right_index
            product = left_word * right_word
            wide_products += 1
            if position >= length:
                if product or carry:
                    raise OverflowError("schoolbook product exceeds destination")
                continue
            total = output[position] + product + carry
            output[position] = total & WORD_MASK
            carry = total >> WORD_BITS
            carry_steps += 1
        position = left_index + len(right)
        while carry:
            if position >= length:
                raise OverflowError("schoolbook carry exceeds destination")
            total = output[position] + carry
            output[position] = total & WORD_MASK
            carry = total >> WORD_BITS
            position += 1
            carry_steps += 1
    return tuple(output), LimbWork(
        wide_products=wide_products,
        carry_steps=carry_steps,
    )


def limb_full_product(
    left: SignedLimbs,
    right: SignedLimbs,
    destination: SignedLimbPlan,
) -> tuple[SignedLimbs, LimbWork]:
    left_magnitude, left_negative, left_work = _unsigned_magnitude(left)
    right_magnitude, right_negative, right_work = _unsigned_magnitude(right)
    words, product_work = _unsigned_schoolbook_product(
        left_magnitude,
        right_magnitude,
        destination.allocated_limbs,
    )
    work = left_work.plus(right_work).plus(product_work)
    if left_negative ^ right_negative:
        words, negate_work = _twos_complement_words(words)
        work = work.plus(negate_work)
    return _finish_limb_operation(words, destination), work


def limb_accumulate(
    accumulator: SignedLimbs, term: SignedLimbs
) -> tuple[SignedLimbs, LimbWork]:
    return limb_add(accumulator, term)


MILLER_RABIN_BASES = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
SMALL_PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def is_prime_u64(value: int) -> bool:
    candidate = _require_plain_integer(value, label="prime candidate", minimum=2)
    if candidate >= 1 << 64:
        raise ValueError("prime candidate exceeds unsigned 64-bit range")
    if candidate in SMALL_PRIMES:
        return True
    if any(candidate % prime == 0 for prime in SMALL_PRIMES):
        return False
    odd = candidate - 1
    shifts = 0
    while odd % 2 == 0:
        odd //= 2
        shifts += 1
    for base in MILLER_RABIN_BASES:
        witness = base % candidate
        if witness in (0, 1):
            continue
        result = pow(witness, odd, candidate)
        if result in (1, candidate - 1):
            continue
        for _ in range(shifts - 1):
            result = (result * result) % candidate
            if result == candidate - 1:
                break
        else:
            return False
    return True


@dataclass(frozen=True, slots=True)
class RRNSParameters:
    working_primes: tuple[int, ...]
    redundant_prime: int
    absolute_bound: int

    @property
    def working_product(self) -> int:
        return math.prod(self.working_primes)

    @property
    def all_moduli(self) -> tuple[int, ...]:
        return self.working_primes + (self.redundant_prime,)

    def validate(self) -> None:
        if not self.working_primes:
            raise ValueError("RRNS working-prime set is empty")
        if tuple(sorted(self.working_primes)) != self.working_primes:
            raise ValueError("RRNS working primes are not strictly ascending")
        if len(set(self.all_moduli)) != len(self.all_moduli):
            raise ValueError("RRNS modulus is duplicated")
        for modulus in self.all_moduli:
            if modulus >= 1 << 62 or not is_prime_u64(modulus):
                raise ValueError("RRNS modulus is not a frozen 62-bit prime")
            if gcd(modulus, COMMON_SCALE) != 1:
                raise ValueError("RRNS modulus is not coprime to common scale")
        for index, modulus in enumerate(self.all_moduli):
            for other in self.all_moduli[index + 1 :]:
                if gcd(modulus, other) != 1:
                    raise ValueError("RRNS moduli are not pairwise coprime")
        if self.redundant_prime <= self.working_primes[-1]:
            raise ValueError("RRNS redundant modulus is not strictly largest")
        bound = _require_plain_integer(
            self.absolute_bound, label="RRNS absolute bound", minimum=0
        )
        if self.working_product < 2 * bound + 1:
            raise ValueError("RRNS working product is below two-B-plus-one")


@dataclass(frozen=True, slots=True)
class RRNSValue:
    residues: tuple[int, ...]
    parameters: RRNSParameters

    def __post_init__(self) -> None:
        self.parameters.validate()
        if len(self.residues) != len(self.parameters.all_moduli):
            raise ValueError("RRNS residue count differs from modulus count")
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            or value >= modulus
            for value, modulus in zip(
                self.residues, self.parameters.all_moduli, strict=True
            )
        ):
            raise ValueError("RRNS residue is outside its canonical interval")

    @classmethod
    def encode(cls, value: int, parameters: RRNSParameters) -> "RRNSValue":
        item = _require_plain_integer(value, label="RRNS input")
        parameters.validate()
        if abs(item) > parameters.absolute_bound:
            raise OverflowError("RRNS input exceeds its semantic bound")
        return cls(tuple(item % modulus for modulus in parameters.all_moduli), parameters)


def rrns_add(left: RRNSValue, right: RRNSValue) -> RRNSValue:
    if left.parameters != right.parameters:
        raise ValueError("RRNS addition parameters differ")
    return RRNSValue(
        tuple(
            (a + b) % modulus
            for a, b, modulus in zip(
                left.residues,
                right.residues,
                left.parameters.all_moduli,
                strict=True,
            )
        ),
        left.parameters,
    )


def rrns_subtract(left: RRNSValue, right: RRNSValue) -> RRNSValue:
    if left.parameters != right.parameters:
        raise ValueError("RRNS subtraction parameters differ")
    return RRNSValue(
        tuple(
            (a - b) % modulus
            for a, b, modulus in zip(
                left.residues,
                right.residues,
                left.parameters.all_moduli,
                strict=True,
            )
        ),
        left.parameters,
    )


def rrns_multiply(left: RRNSValue, right: RRNSValue) -> RRNSValue:
    if left.parameters != right.parameters:
        raise ValueError("RRNS multiplication parameters differ")
    return RRNSValue(
        tuple(
            (a * b) % modulus
            for a, b, modulus in zip(
                left.residues,
                right.residues,
                left.parameters.all_moduli,
                strict=True,
            )
        ),
        left.parameters,
    )


def rrns_multiply_small(value: RRNSValue, factor: int) -> RRNSValue:
    multiplier = _require_plain_integer(factor, label="RRNS small factor")
    return RRNSValue(
        tuple(
            (residue * multiplier) % modulus
            for residue, modulus in zip(
                value.residues, value.parameters.all_moduli, strict=True
            )
        ),
        value.parameters,
    )


def _unsigned_crt(residues: Sequence[int], moduli: Sequence[int]) -> tuple[int, int]:
    if len(residues) != len(moduli) or not moduli:
        raise ValueError("CRT residue and modulus counts differ")
    product = math.prod(moduli)
    total = 0
    for residue, modulus in zip(residues, moduli, strict=True):
        partial = product // modulus
        total += residue * partial * pow(partial, -1, modulus)
    return total % product, product


def _signed_representative(unsigned: int, modulus_product: int) -> int:
    if unsigned > (modulus_product - 1) // 2:
        return unsigned - modulus_product
    return unsigned


def rrns_reconstruct_full(value: RRNSValue) -> int:
    """Full-codeword CRT followed by the frozen semantic range check."""

    unsigned, product = _unsigned_crt(value.residues, value.parameters.all_moduli)
    decoded = _signed_representative(unsigned, product)
    if abs(decoded) > value.parameters.absolute_bound:
        raise RRNSChannelFaultDetected("rrns_channel_fault_detected")
    return decoded


def rrns_reconstruct_base_extension(value: RRNSValue) -> int:
    """Working CRT, semantic range check, then redundant base extension."""

    working = value.parameters.working_primes
    unsigned, product = _unsigned_crt(value.residues[:-1], working)
    decoded = _signed_representative(unsigned, product)
    if abs(decoded) > value.parameters.absolute_bound:
        raise RRNSChannelFaultDetected("rrns_channel_fault_detected")
    if decoded % value.parameters.redundant_prime != value.residues[-1]:
        raise RRNSChannelFaultDetected("rrns_channel_fault_detected")
    return decoded


def rrns_reconstruct_both(value: RRNSValue) -> int:
    full = rrns_reconstruct_full(value)
    extended = rrns_reconstruct_base_extension(value)
    if full != extended:
        raise RRNSChannelFaultDetected("rrns_channel_fault_detected")
    return full


def reconstruct_scaled_rrns(value: RRNSValue) -> int:
    decoded = rrns_reconstruct_both(value)
    if decoded % COMMON_SCALE:
        raise ArithmeticError("RRNS reconstruction is not divisible by 720")
    return decoded


def require_unbounded_match(decoded: int, authority: int) -> None:
    if decoded != authority:
        raise ArithmeticError("RRNS result differs from unbounded authority")


@dataclass(frozen=True, slots=True)
class RRNSFaultObservation:
    changed_channels: tuple[int, ...]
    full_CRT_detected: bool
    base_extension_detected: bool
    eligible_for_single_channel_claim: bool


def observe_rrns_fault(
    value: RRNSValue,
    changed_channels: Sequence[int],
) -> RRNSFaultObservation:
    """Report multi-channel controls without widening the one-channel theorem."""

    indices = tuple(changed_channels)
    if not indices or len(set(indices)) != len(indices):
        raise ValueError("fault-control channel set is empty or duplicated")
    if any(
        isinstance(index, bool)
        or not isinstance(index, int)
        or index < 0
        or index >= len(value.residues)
        for index in indices
    ):
        raise ValueError("fault-control channel index is outside the codeword")
    residues = list(value.residues)
    for index in indices:
        modulus = value.parameters.all_moduli[index]
        residues[index] = (residues[index] + 1) % modulus
    mutated = RRNSValue(tuple(residues), value.parameters)

    def detected(check: Callable[[RRNSValue], int]) -> bool:
        try:
            check(mutated)
        except RRNSChannelFaultDetected:
            return True
        return False

    return RRNSFaultObservation(
        changed_channels=indices,
        full_CRT_detected=detected(rrns_reconstruct_full),
        base_extension_detected=detected(rrns_reconstruct_base_extension),
        eligible_for_single_channel_claim=len(indices) == 1,
    )


@dataclass(frozen=True, slots=True)
class MontgomeryConstants:
    modulus: int
    negative_inverse: int
    r_modulus: int
    r_squared_modulus: int


def montgomery_constants(modulus: int) -> MontgomeryConstants:
    prime = _require_plain_integer(modulus, label="Montgomery modulus", minimum=3)
    if prime % 2 == 0 or prime >= 1 << 63:
        raise ValueError("Montgomery modulus must be odd and below two-to-63")
    negative_inverse = (-pow(prime, -1, MONTGOMERY_R)) & WORD_MASK
    return MontgomeryConstants(
        modulus=prime,
        negative_inverse=negative_inverse,
        r_modulus=MONTGOMERY_R % prime,
        r_squared_modulus=(MONTGOMERY_R * MONTGOMERY_R) % prime,
    )


def montgomery_reduce(product: int, constants: MontgomeryConstants) -> int:
    value = _require_plain_integer(product, label="Montgomery product", minimum=0)
    if value >= constants.modulus * MONTGOMERY_R:
        raise OverflowError("Montgomery product exceeds its reduction precondition")
    low_multiplier = ((value & WORD_MASK) * constants.negative_inverse) & WORD_MASK
    reduced = (value + low_multiplier * constants.modulus) >> WORD_BITS
    if reduced >= constants.modulus:
        reduced -= constants.modulus
    if reduced < 0 or reduced >= constants.modulus:
        raise AssertionError("Montgomery reduction is not canonical")
    return reduced


def montgomery_encode(value: int, constants: MontgomeryConstants) -> int:
    item = _require_plain_integer(value, label="Montgomery input")
    return (item % constants.modulus) * constants.r_modulus % constants.modulus


def montgomery_multiply(
    left_encoded: int, right_encoded: int, constants: MontgomeryConstants
) -> int:
    left = _require_plain_integer(left_encoded, label="left Montgomery residue", minimum=0)
    right = _require_plain_integer(right_encoded, label="right Montgomery residue", minimum=0)
    if left >= constants.modulus or right >= constants.modulus:
        raise ValueError("Montgomery residue is outside its modulus")
    return montgomery_reduce(left * right, constants)


def montgomery_decode(encoded: int, constants: MontgomeryConstants) -> int:
    item = _require_plain_integer(encoded, label="Montgomery encoded value", minimum=0)
    if item >= constants.modulus:
        raise ValueError("Montgomery encoded value is outside its modulus")
    return montgomery_reduce(item, constants)


def _rrns_parameters_from_config(
    base: Mapping[str, object], *, scalar: bool
) -> RRNSParameters:
    candidate = base.get("rrns_candidate")
    profile = base.get("source_seal_bound_profile_from_frozen_windows")
    if not isinstance(candidate, Mapping) or not isinstance(profile, Mapping):
        raise ValueError("RRNS config sections differ")
    primes = tuple(int(value) for value in candidate.get("working_primes_ascending", ()))
    code = candidate.get("scalar_code" if scalar else "table_code")
    if not isinstance(code, Mapping):
        raise ValueError("RRNS code config differs")
    indices = tuple(int(value) for value in code.get("working_prime_indices", ()))
    bound = int(profile.get("scalar_abs_bound_B" if scalar else "table_abs_bound_B", -1))
    return RRNSParameters(
        tuple(primes[index] for index in indices),
        int(candidate.get("redundant_prime", -1)),
        bound,
    )


def validate_frozen_rrns(base: Mapping[str, object] | None = None) -> tuple[RRNSParameters, RRNSParameters]:
    parsed = load_preregistered_config() if base is None else base
    candidate = parsed.get("rrns_candidate")
    if not isinstance(candidate, Mapping):
        raise ValueError("RRNS candidate config differs")
    primes = tuple(int(value) for value in candidate.get("working_primes_ascending", ()))
    if len(primes) != 8 or tuple(sorted(primes)) != primes:
        raise ValueError("RRNS frozen working-prime list differs")
    if tuple(candidate.get("primality_authority", {}).get("bases", ())) != MILLER_RABIN_BASES:
        raise ValueError("RRNS Miller-Rabin bases differ")
    if tuple(candidate.get("primality_authority", {}).get("exact_small_prime_division_precheck", ())) != SMALL_PRIMES:
        raise ValueError("RRNS small-prime precheck differs")
    table = _rrns_parameters_from_config(parsed, scalar=False)
    scalar = _rrns_parameters_from_config(parsed, scalar=True)
    table.validate()
    scalar.validate()
    for parameters, label in ((table, "table_code"), (scalar, "scalar_code")):
        row = candidate.get(label)
        assert isinstance(row, Mapping)
        if parameters.working_product != int(row.get("working_product", -1)):
            raise ValueError(f"RRNS {label} working product differs")
        if parameters.working_product * parameters.redundant_prime != int(
            row.get("working_product_times_redundant", -1)
        ):
            raise ValueError(f"RRNS {label} full product differs")
    return table, scalar


@dataclass(frozen=True, slots=True)
class FrozenBoundProfile:
    source_maximum: int
    covector_maximum: int
    weight_maximum: int
    forward_table_bound: int
    adjoint_table_bound: int
    scalar_bound: int
    reach_bound: int
    forward_table_plan: SignedLimbPlan
    adjoint_table_plan: SignedLimbPlan
    scalar_plan: SignedLimbPlan
    reach_plan: SignedLimbPlan


def derive_frozen_bound_profile(
    base: Mapping[str, object] | None = None,
) -> FrozenBoundProfile:
    """Derive the source-seal widths from frozen windows, never telemetry."""

    parsed = load_preregistered_config() if base is None else base
    admission = parsed.get("fixed_width_admission")
    profile = parsed.get("source_seal_bound_profile_from_frozen_windows")
    if not isinstance(admission, Mapping) or not isinstance(profile, Mapping):
        raise ValueError("fixed-width bound config sections differ")
    windows = admission.get("known_control_only_windows")
    if not isinstance(windows, Mapping):
        raise ValueError("fixed-width windows differ")

    def maximum_for(family: str) -> int:
        raw = windows.get(family)
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or len(raw) != 2:
            raise ValueError(f"fixed-width window differs: {family}")
        low, high = (int(raw[0]), int(raw[1]))
        if low > high:
            raise ValueError(f"fixed-width window is reversed: {family}")
        return 2 * ((1 << 53) - 1) * (1 << (high - low))

    source = maximum_for("source_rows")
    covector = maximum_for("labeled_query_covectors")
    weight = maximum_for("labeled_query_weights")
    report = exact.operator_bound_report(
        available_cards=int(profile.get("joint_control_geometry_available_cards", -1)),
        feature_width=int(profile.get("joint_control_geometry_feature_width", -1)),
        source_maximum=source,
        covector_maximum=covector,
        weight_maximum=weight,
    )
    return FrozenBoundProfile(
        source_maximum=source,
        covector_maximum=covector,
        weight_maximum=weight,
        forward_table_bound=max(
            *report.forward_table_bounds, report.forward_signed_partial_bound
        ),
        adjoint_table_bound=max(
            *report.adjoint_table_bounds, report.adjoint_signed_partial_bound
        ),
        scalar_bound=report.forward_scalar_bound,
        reach_bound=report.reach_scalar_bound,
        forward_table_plan=SignedLimbPlan.from_bound(
            max(*report.forward_table_bounds, report.forward_signed_partial_bound)
        ),
        adjoint_table_plan=SignedLimbPlan.from_bound(
            max(*report.adjoint_table_bounds, report.adjoint_signed_partial_bound)
        ),
        scalar_plan=SignedLimbPlan.from_bound(report.forward_scalar_bound),
        reach_plan=SignedLimbPlan.from_bound(report.reach_scalar_bound),
    )


def verify_frozen_bound_profile(base: Mapping[str, object] | None = None) -> FrozenBoundProfile:
    parsed = load_preregistered_config() if base is None else base
    row = parsed.get("source_seal_bound_profile_from_frozen_windows")
    if not isinstance(row, Mapping):
        raise ValueError("source-seal bound profile differs")
    derived = derive_frozen_bound_profile(parsed)
    expected_inputs = row.get("input_maxima")
    expected_bits = row.get("required_signed_bits")
    expected_limbs = row.get("guard_inclusive_positional_limbs")
    if not all(isinstance(value, Mapping) for value in (expected_inputs, expected_bits, expected_limbs)):
        raise ValueError("source-seal bound detail differs")
    assert isinstance(expected_inputs, Mapping)
    assert isinstance(expected_bits, Mapping)
    assert isinstance(expected_limbs, Mapping)
    checks = {
        "source_rows": derived.source_maximum,
        "labeled_query_covectors": derived.covector_maximum,
        "labeled_query_weights": derived.weight_maximum,
    }
    if any(int(expected_inputs.get(key, -1)) != value for key, value in checks.items()):
        raise ValueError("source-seal input maximum differs")
    scalar_checks = {
        "forward_table_or_signed_partial_abs_bound": derived.forward_table_bound,
        "adjoint_table_or_signed_partial_abs_bound": derived.adjoint_table_bound,
        "table_abs_bound_B": derived.forward_table_bound,
        "numerator_abs_bound": derived.scalar_bound,
        "reach_abs_bound": derived.reach_bound,
        "scalar_abs_bound_B": derived.scalar_bound,
    }
    if any(int(row.get(key, -1)) != value for key, value in scalar_checks.items()):
        raise ValueError("source-seal semantic bound differs")
    bit_checks = {
        "forward_table_or_partial": derived.forward_table_plan.required_signed_bits,
        "adjoint_table_or_partial": derived.adjoint_table_plan.required_signed_bits,
        "numerator": derived.scalar_plan.required_signed_bits,
        "reach": derived.reach_plan.required_signed_bits,
    }
    limb_checks = {
        "forward_table_or_partial": derived.forward_table_plan.allocated_limbs,
        "adjoint_table_or_partial": derived.adjoint_table_plan.allocated_limbs,
        "numerator": derived.scalar_plan.allocated_limbs,
        "reach": derived.reach_plan.allocated_limbs,
    }
    if any(int(expected_bits.get(key, -1)) != value for key, value in bit_checks.items()):
        raise ValueError("source-seal signed-bit derivation differs")
    if any(int(expected_limbs.get(key, -1)) != value for key, value in limb_checks.items()):
        raise ValueError("source-seal limb derivation differs")
    table, scalar = validate_frozen_rrns(parsed)
    if table.working_product < 2 * derived.forward_table_bound + 1:
        raise ValueError("RRNS table uniqueness inequality differs")
    if scalar.working_product < 2 * derived.scalar_bound + 1:
        raise ValueError("RRNS scalar uniqueness inequality differs")
    return derived


@dataclass(frozen=True, slots=True)
class ComponentTelemetry:
    total_components: int
    finite_nonzero_components: int
    positive_zero_components: int
    negative_zero_components: int
    subnormal_nonzero_components: int
    positive_nonzero_components: int
    negative_nonzero_components: int
    stored_component_frexp_minimum: int | None
    stored_component_frexp_maximum: int | None
    canonical_odd_mantissa_exponent_minimum: int | None
    canonical_odd_mantissa_exponent_maximum: int | None


@dataclass(frozen=True, slots=True)
class FamilyTelemetry:
    family: str
    high: ComponentTelemetry
    low: ComponentTelemetry
    combined: ComponentTelemetry
    family_fixed_point_exponent: int
    maximum_absolute_encoded_pair: int


def _component_telemetry(values: Iterable[float]) -> ComponentTelemetry:
    total = nonzero = positive_zero = negative_zero = subnormal = positive = negative = 0
    frexp_values: list[int] = []
    canonical_values: list[int] = []
    for value in values:
        if type(value) is not float or not math.isfinite(value):
            raise ValueError("nonfinite component rejects before telemetry")
        total += 1
        if value == 0.0:
            if math.copysign(1.0, value) < 0:
                negative_zero += 1
            else:
                positive_zero += 1
            continue
        nonzero += 1
        if value > 0:
            positive += 1
        else:
            negative += 1
        if abs(value) < sys.float_info.min:
            subnormal += 1
        frexp_values.append(math.frexp(value)[1])
        component = exact.canonical_float_component(value)
        if component is None:
            raise AssertionError("nonzero component lost its canonical exponent")
        canonical_values.append(component[1])
    return ComponentTelemetry(
        total_components=total,
        finite_nonzero_components=nonzero,
        positive_zero_components=positive_zero,
        negative_zero_components=negative_zero,
        subnormal_nonzero_components=subnormal,
        positive_nonzero_components=positive,
        negative_nonzero_components=negative,
        stored_component_frexp_minimum=min(frexp_values, default=None),
        stored_component_frexp_maximum=max(frexp_values, default=None),
        canonical_odd_mantissa_exponent_minimum=min(canonical_values, default=None),
        canonical_odd_mantissa_exponent_maximum=max(canonical_values, default=None),
    )


def _merge_component_telemetry(
    left: ComponentTelemetry, right: ComponentTelemetry
) -> ComponentTelemetry:
    def minimum(name: str) -> int | None:
        values = [value for value in (getattr(left, name), getattr(right, name)) if value is not None]
        return min(values, default=None)

    def maximum(name: str) -> int | None:
        values = [value for value in (getattr(left, name), getattr(right, name)) if value is not None]
        return max(values, default=None)

    return ComponentTelemetry(
        total_components=left.total_components + right.total_components,
        finite_nonzero_components=left.finite_nonzero_components + right.finite_nonzero_components,
        positive_zero_components=left.positive_zero_components + right.positive_zero_components,
        negative_zero_components=left.negative_zero_components + right.negative_zero_components,
        subnormal_nonzero_components=left.subnormal_nonzero_components + right.subnormal_nonzero_components,
        positive_nonzero_components=left.positive_nonzero_components + right.positive_nonzero_components,
        negative_nonzero_components=left.negative_nonzero_components + right.negative_nonzero_components,
        stored_component_frexp_minimum=minimum("stored_component_frexp_minimum"),
        stored_component_frexp_maximum=maximum("stored_component_frexp_maximum"),
        canonical_odd_mantissa_exponent_minimum=minimum(
            "canonical_odd_mantissa_exponent_minimum"
        ),
        canonical_odd_mantissa_exponent_maximum=maximum(
            "canonical_odd_mantissa_exponent_maximum"
        ),
    )


def family_telemetry(
    family: str,
    rows: Sequence[Sequence[exact.CapturedPair]],
    *,
    admitted_window: exact.FrozenExponentWindow,
) -> FamilyTelemetry:
    matrix = tuple(tuple(row) for row in rows)
    if not matrix or not matrix[0] or any(len(row) != len(matrix[0]) for row in matrix):
        raise ValueError("telemetry pair family is empty or ragged")
    high = _component_telemetry(pair.high for row in matrix for pair in row)
    low = _component_telemetry(pair.low for row in matrix for pair in row)
    combined = _merge_component_telemetry(high, low)
    if combined.canonical_odd_mantissa_exponent_minimum is not None:
        admitted_window.admit(combined.canonical_odd_mantissa_exponent_minimum)
        assert combined.canonical_odd_mantissa_exponent_maximum is not None
        admitted_window.admit(combined.canonical_odd_mantissa_exponent_maximum)
    encoded = exact.encode_pair_matrix(
        matrix,
        label=family,
        admitted_window=admitted_window,
    )
    return FamilyTelemetry(
        family=family,
        high=high,
        low=low,
        combined=combined,
        family_fixed_point_exponent=encoded.family_exponent,
        maximum_absolute_encoded_pair=encoded.maximum_absolute_entry,
    )


def captured_operator_telemetry(
    captured: exact.CapturedOperatorInput,
) -> tuple[FamilyTelemetry, FamilyTelemetry, FamilyTelemetry]:
    base = load_preregistered_config()
    admission = base.get("fixed_width_admission")
    if not isinstance(admission, Mapping) or not isinstance(
        admission.get("known_control_only_windows"), Mapping
    ):
        raise ValueError("fixed-width telemetry windows differ")
    windows = admission["known_control_only_windows"]

    def window(family: str) -> exact.FrozenExponentWindow:
        raw = windows.get(family)
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or len(raw) != 2:
            raise ValueError(f"fixed-width telemetry window differs: {family}")
        return exact.FrozenExponentWindow(int(raw[0]), int(raw[1]))

    return (
        family_telemetry(
            "source_rows",
            captured.source_rows,
            admitted_window=window("source_rows"),
        ),
        family_telemetry(
            "labeled_query_covectors",
            captured.query_covectors,
            admitted_window=window("labeled_query_covectors"),
        ),
        family_telemetry(
            "labeled_query_weights",
            tuple((value,) for value in captured.query_weights),
            admitted_window=window("labeled_query_weights"),
        ),
    )


def verify_known_telemetry(
    label: str,
    telemetry: Sequence[FamilyTelemetry],
    base: Mapping[str, object] | None = None,
) -> None:
    parsed = load_preregistered_config() if base is None else base
    controls = parsed.get("known_control_population_telemetry")
    if not isinstance(controls, Mapping) or label not in controls:
        raise ValueError("known telemetry population differs")
    expected = controls[label]
    if not isinstance(expected, Mapping):
        raise ValueError("known telemetry row differs")
    by_family = {row.family: row for row in telemetry}
    if set(by_family) != {
        "source_rows",
        "labeled_query_covectors",
        "labeled_query_weights",
    }:
        raise ValueError("telemetry family set differs")
    for family, row in expected.items():
        if not isinstance(row, Mapping) or family not in by_family:
            raise ValueError(f"known telemetry family differs: {family}")
        observed = by_family[family].combined
        if [
            observed.canonical_odd_mantissa_exponent_minimum,
            observed.canonical_odd_mantissa_exponent_maximum,
        ] != row.get("canonical_exponent_min_max"):
            raise ValueError(f"canonical telemetry differs: {family}")
        if [
            observed.stored_component_frexp_minimum,
            observed.stored_component_frexp_maximum,
        ] != row.get("frexp_exponent_min_max"):
            raise ValueError(f"frexp telemetry differs: {family}")
        if observed.finite_nonzero_components != row.get("nonzero_components"):
            raise ValueError(f"nonzero telemetry differs: {family}")
        if observed.positive_zero_components + observed.negative_zero_components != row.get(
            "zero_components"
        ):
            raise ValueError(f"zero telemetry differs: {family}")


def _submasks(mask: int) -> Iterable[int]:
    subset = mask
    while True:
        yield subset
        if subset == 0:
            return
        subset = (subset - 1) & mask


def _limb_zero(plan: SignedLimbPlan) -> SignedLimbs:
    return SignedLimbs.encode(0, plan)


def _limb_row(values: Sequence[int], plan: SignedLimbPlan) -> tuple[SignedLimbs, ...]:
    return tuple(SignedLimbs.encode(int(value), plan) for value in values)


def _frozen_control_windows() -> tuple[
    exact.FrozenExponentWindow,
    exact.FrozenExponentWindow,
    exact.FrozenExponentWindow,
]:
    base = load_preregistered_config()
    admission = base.get("fixed_width_admission")
    if not isinstance(admission, Mapping) or not isinstance(
        admission.get("known_control_only_windows"), Mapping
    ):
        raise ValueError("fixed-width control windows differ")
    rows = admission["known_control_only_windows"]

    def make(name: str) -> exact.FrozenExponentWindow:
        value = rows.get(name)
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 2:
            raise ValueError(f"fixed-width control window differs: {name}")
        return exact.FrozenExponentWindow(int(value[0]), int(value[1]))

    return (
        make("source_rows"),
        make("labeled_query_covectors"),
        make("labeled_query_weights"),
    )


def _encode_control_families(
    captured: exact.CapturedOperatorInput,
) -> tuple[exact.EncodedPairMatrix, exact.EncodedPairMatrix, exact.EncodedPairMatrix]:
    source_window, covector_window, weight_window = _frozen_control_windows()
    return (
        exact.encode_pair_matrix(
            captured.source_rows,
            label="fixed-width source rows",
            admitted_window=source_window,
        ),
        exact.encode_pair_matrix(
            captured.query_covectors,
            label="fixed-width labeled query covectors",
            admitted_window=covector_window,
        ),
        exact.encode_pair_vector(
            captured.query_weights,
            label="fixed-width labeled query weights",
            admitted_window=weight_window,
        ),
    )


def _aggregate_labeled_positional(
    captured: exact.CapturedOperatorInput,
    covectors: Sequence[Sequence[int]],
    weights: Sequence[int],
    *,
    plan: SignedLimbPlan,
) -> tuple[dict[int, tuple[int, ...]], dict[int, int], LimbWork]:
    masks = exact.complete_masks(captured.available_cards, QUERY_CARDS)
    width = len(covectors[0])
    rows = {mask: tuple(_limb_zero(plan) for _ in range(width)) for mask in masks}
    scalar_weights = {mask: _limb_zero(plan) for mask in masks}
    labels = {mask: set() for mask in masks}
    work = LimbWork()
    for mask, label, row, weight in zip(
        captured.query_masks,
        captured.query_labels,
        covectors,
        weights,
        strict=True,
    ):
        if mask not in rows or isinstance(label, bool) or not isinstance(label, int):
            raise ValueError("positional labeled query coordinate differs")
        if label not in range(QUERY_LABELS) or label in labels[mask]:
            raise ValueError("positional query labels differ")
        encoded_row = _limb_row(row, plan)
        rows[mask], item_work = _add_limb_rows(rows[mask], encoded_row)
        work = work.plus(item_work)
        scalar_weights[mask], item_work = limb_add(
            scalar_weights[mask], SignedLimbs.encode(weight, plan)
        )
        work = work.plus(item_work)
        labels[mask].add(label)
    expected_labels = set(range(QUERY_LABELS))
    if any(value != expected_labels for value in labels.values()):
        raise ValueError("positional labels do not close every query occupancy")
    return (
        {mask: tuple(value.decode() for value in row) for mask, row in rows.items()},
        {mask: value.decode() for mask, value in scalar_weights.items()},
        work,
    )


def _aggregate_labeled_modular(
    captured: exact.CapturedOperatorInput,
    covectors: Sequence[Sequence[int]],
    weights: Sequence[int],
    *,
    modulus: int,
) -> tuple[dict[int, tuple[int, ...]], dict[int, int]]:
    masks = exact.complete_masks(captured.available_cards, QUERY_CARDS)
    width = len(covectors[0])
    rows = {mask: [0] * width for mask in masks}
    scalar_weights = {mask: 0 for mask in masks}
    labels = {mask: set() for mask in masks}
    for mask, label, row, weight in zip(
        captured.query_masks,
        captured.query_labels,
        covectors,
        weights,
        strict=True,
    ):
        if mask not in rows or isinstance(label, bool) or not isinstance(label, int):
            raise ValueError("RRNS labeled query coordinate differs")
        if label not in range(QUERY_LABELS) or label in labels[mask]:
            raise ValueError("RRNS query labels differ")
        for feature, value in enumerate(row):
            rows[mask][feature] = (rows[mask][feature] + value) % modulus
        scalar_weights[mask] = (scalar_weights[mask] + weight) % modulus
        labels[mask].add(label)
    expected_labels = set(range(QUERY_LABELS))
    if any(value != expected_labels for value in labels.values()):
        raise ValueError("RRNS labels do not close every query occupancy")
    return (
        {mask: tuple(row) for mask, row in rows.items()},
        scalar_weights,
    )


def _add_limb_rows(
    left: Sequence[SignedLimbs], right: Sequence[SignedLimbs]
) -> tuple[tuple[SignedLimbs, ...], LimbWork]:
    if len(left) != len(right):
        raise ValueError("fixed-width recurrence row widths differ")
    output = []
    work = LimbWork()
    for a, b in zip(left, right, strict=True):
        value, item_work = limb_add(a, b)
        output.append(value)
        work = work.plus(item_work)
    return tuple(output), work


def _build_limb_levels(
    cards: int,
    base_rows: Mapping[int, Sequence[int]],
    *,
    maximum_level: int,
    plan: SignedLimbPlan,
) -> tuple[dict[int, dict[int, tuple[SignedLimbs, ...]]], LimbWork]:
    width = len(next(iter(base_rows.values())))
    levels = {
        maximum_level: {
            mask: _limb_row(row, plan) for mask, row in base_rows.items()
        }
    }
    work = LimbWork()
    for level in range(maximum_level - 1, -1, -1):
        current = {}
        for mask in exact.complete_masks(cards, level):
            accumulator = tuple(_limb_zero(plan) for _ in range(width))
            for card in range(cards):
                if mask & (1 << card):
                    continue
                accumulator, item_work = _add_limb_rows(
                    accumulator, levels[level + 1][mask | (1 << card)]
                )
                work = work.plus(item_work)
            current[mask] = accumulator
        levels[level] = current
    return levels, work


def _limb_signed_subset_row(
    mask: int,
    levels: Mapping[int, Mapping[int, Sequence[SignedLimbs]]],
    weights: Sequence[int],
    plan: SignedLimbPlan,
    *,
    maximum_level: int,
) -> tuple[tuple[SignedLimbs, ...], LimbWork, int]:
    width = len(next(iter(levels[0].values())))
    accumulator = tuple(_limb_zero(plan) for _ in range(width))
    work = LimbWork()
    rows_read = 0
    for subset in _submasks(mask):
        level = subset.bit_count()
        if level > maximum_level:
            continue
        rows_read += 1
        coefficient = weights[level] * (-1 if level & 1 else 1)
        terms = []
        for value in levels[level][subset]:
            term, item_work = limb_multiply_small(value, coefficient)
            terms.append(term)
            work = work.plus(item_work)
        accumulator, item_work = _add_limb_rows(accumulator, terms)
        work = work.plus(item_work)
    for value in accumulator:
        if value.decode() % COMMON_SCALE:
            raise ArithmeticError("fixed-width scaled row is not divisible by 720")
    return accumulator, work, rows_read


@dataclass(frozen=True, slots=True)
class CandidateOperatorResult:
    representation: str
    schedule: str | None
    forward_integer_numerator: int
    adjoint_integer_numerator: int
    forward_integer_reach: int
    conditional_value_bits: int
    checked_forward_rows: int
    checked_adjoint_rows: int
    recomputed_vector_edges: int
    limb_work: LimbWork | None


def evaluate_positional_operator(
    captured: exact.CapturedOperatorInput,
) -> CandidateOperatorResult:
    """Recompute both reduced operators through limbwise arithmetic."""

    authority = exact.execute_exact_integer_operator(captured)
    profile = verify_frozen_bound_profile()
    encoded_source, encoded_covectors, encoded_weights = _encode_control_families(
        captured
    )
    source = {
        mask: row
        for mask, row in zip(
            captured.source_masks, encoded_source.rows, strict=True
        )
    }
    covectors, weights, aggregation_work = _aggregate_labeled_positional(
        captured,
        encoded_covectors.rows,
        tuple(row[0] for row in encoded_weights.rows),
        plan=profile.adjoint_table_plan,
    )
    if source != dict(authority.source_rows):
        raise ArithmeticError("positional source encoding differs from authority")
    if covectors != dict(authority.aggregated_query_covectors):
        raise ArithmeticError("positional covector aggregation differs from authority")
    if weights != dict(authority.aggregated_query_weights):
        raise ArithmeticError("positional weight aggregation differs from authority")
    forward_levels, forward_work = _build_limb_levels(
        authority.available_cards,
        source,
        maximum_level=SOURCE_CARDS,
        plan=profile.forward_table_plan,
    )
    work = aggregation_work.plus(forward_work)
    adjoint_levels, item_work = _build_limb_levels(
        authority.available_cards,
        covectors,
        maximum_level=QUERY_CARDS,
        plan=profile.adjoint_table_plan,
    )
    work = work.plus(item_work)
    forward_rows: dict[int, tuple[SignedLimbs, ...]] = {}
    for mask, expected in authority.forward_scaled_rows:
        row, item_work, rows_read = _limb_signed_subset_row(
            mask,
            forward_levels,
            exact.FORWARD_LEVEL_WEIGHTS,
            profile.forward_table_plan,
            maximum_level=QUERY_CARDS,
        )
        if rows_read != 16 or tuple(value.decode() for value in row) != expected:
            raise ArithmeticError("positional forward row differs from authority")
        forward_rows[mask] = row
        work = work.plus(item_work)
    adjoint_rows: dict[int, tuple[SignedLimbs, ...]] = {}
    for mask, expected in authority.adjoint_scaled_rows:
        row, item_work, rows_read = _limb_signed_subset_row(
            mask,
            adjoint_levels,
            exact.ADJOINT_LEVEL_WEIGHTS,
            profile.adjoint_table_plan,
            maximum_level=QUERY_CARDS,
        )
        if rows_read != 57 or tuple(value.decode() for value in row) != expected:
            raise ArithmeticError("positional adjoint row differs from authority")
        adjoint_rows[mask] = row
        work = work.plus(item_work)

    numerator = _limb_zero(profile.scalar_plan)
    reach = _limb_zero(profile.reach_plan)
    for mask in exact.complete_masks(authority.available_cards, QUERY_CARDS):
        for forward, covector in zip(forward_rows[mask], covectors[mask], strict=True):
            term, item_work = limb_full_product(
                forward,
                SignedLimbs.encode(covector, profile.adjoint_table_plan),
                profile.scalar_plan,
            )
            numerator, add_work = limb_accumulate(numerator, term)
            work = work.plus(item_work).plus(add_work)
        reach_term, item_work = limb_full_product(
            forward_rows[mask][captured.reach_feature],
            SignedLimbs.encode(weights[mask], profile.adjoint_table_plan),
            profile.reach_plan,
        )
        reach, add_work = limb_accumulate(reach, reach_term)
        work = work.plus(item_work).plus(add_work)

    adjoint_numerator = _limb_zero(profile.scalar_plan)
    for mask in exact.complete_masks(authority.available_cards, SOURCE_CARDS):
        for source_value, adjoint in zip(source[mask], adjoint_rows[mask], strict=True):
            term, item_work = limb_full_product(
                SignedLimbs.encode(source_value, profile.forward_table_plan),
                adjoint,
                profile.scalar_plan,
            )
            adjoint_numerator, add_work = limb_accumulate(adjoint_numerator, term)
            work = work.plus(item_work).plus(add_work)

    decoded_numerator = numerator.decode()
    decoded_adjoint = adjoint_numerator.decode()
    decoded_reach = reach.decode()
    if (
        decoded_numerator != authority.forward_integer_numerator
        or decoded_adjoint != authority.adjoint_integer_numerator
        or decoded_reach != authority.forward_integer_reach
    ):
        raise ArithmeticError("positional operator differs from unbounded authority")
    bits = exact.binary64_bits(
        exact.correctly_rounded_binary64(
            decoded_numerator,
            decoded_reach,
            authority.covector_family_exponent - authority.weight_family_exponent,
        )
    )
    if bits != authority.conditional_value_bits:
        raise ArithmeticError("positional terminal rounding differs from authority")
    return CandidateOperatorResult(
        representation="signed_twos_complement_little_endian_uint64_limbs",
        schedule=None,
        forward_integer_numerator=decoded_numerator,
        adjoint_integer_numerator=decoded_adjoint,
        forward_integer_reach=decoded_reach,
        conditional_value_bits=bits,
        checked_forward_rows=len(forward_rows),
        checked_adjoint_rows=len(adjoint_rows),
        recomputed_vector_edges=0,
        limb_work=work,
    )


def _build_modular_levels(
    cards: int,
    base_rows: Mapping[int, Sequence[int]],
    *,
    maximum_level: int,
    modulus: int,
) -> dict[int, dict[int, tuple[int, ...]]]:
    width = len(next(iter(base_rows.values())))
    levels = {
        maximum_level: {
            mask: tuple(value % modulus for value in row)
            for mask, row in base_rows.items()
        }
    }
    for level in range(maximum_level - 1, -1, -1):
        current = {}
        for mask in exact.complete_masks(cards, level):
            values = [0] * width
            for card in range(cards):
                if mask & (1 << card):
                    continue
                child = levels[level + 1][mask | (1 << card)]
                for feature, value in enumerate(child):
                    values[feature] = (values[feature] + value) % modulus
            current[mask] = tuple(values)
        levels[level] = current
    return levels


def _modular_signed_subset_row(
    mask: int,
    levels: Mapping[int, Mapping[int, Sequence[int]]],
    weights: Sequence[int],
    modulus: int,
    *,
    maximum_level: int,
) -> tuple[int, ...]:
    width = len(next(iter(levels[0].values())))
    values = [0] * width
    for subset in _submasks(mask):
        level = subset.bit_count()
        if level > maximum_level:
            continue
        coefficient = weights[level] * (-1 if level & 1 else 1)
        for feature, value in enumerate(levels[level][subset]):
            values[feature] = (values[feature] + coefficient * value) % modulus
    return tuple(values)


def evaluate_rrns_operator(
    captured: exact.CapturedOperatorInput,
    *,
    schedule: str,
) -> CandidateOperatorResult:
    """Recompute every channel; batching replays the second four recurrences."""

    if schedule not in {"resident_nine", "batched_five_then_four"}:
        raise ValueError("RRNS schedule differs")
    authority = exact.execute_exact_integer_operator(captured)
    _, scalar_parameters = validate_frozen_rrns()
    encoded_source, encoded_covectors, encoded_weights = _encode_control_families(
        captured
    )
    source = {
        mask: row
        for mask, row in zip(
            captured.source_masks, encoded_source.rows, strict=True
        )
    }
    expected_covectors = dict(authority.aggregated_query_covectors)
    expected_weights = dict(authority.aggregated_query_weights)
    if source != dict(authority.source_rows):
        raise ArithmeticError("RRNS source encoding differs from authority")
    working = scalar_parameters.working_primes
    redundant = scalar_parameters.redundant_prime
    if schedule == "resident_nine":
        groups = (working + (redundant,),)
    else:
        groups = (working[:4] + (redundant,), working[4:])
    residues: dict[int, tuple[int, int, int]] = {}
    checked_forward_rows = checked_adjoint_rows = 0
    for group in groups:
        for modulus in group:
            covectors, weights = _aggregate_labeled_modular(
                captured,
                encoded_covectors.rows,
                tuple(row[0] for row in encoded_weights.rows),
                modulus=modulus,
            )
            if covectors != {
                mask: tuple(value % modulus for value in row)
                for mask, row in expected_covectors.items()
            }:
                raise ArithmeticError("RRNS covector aggregation differs from authority")
            if weights != {
                mask: value % modulus for mask, value in expected_weights.items()
            }:
                raise ArithmeticError("RRNS weight aggregation differs from authority")
            forward_levels = _build_modular_levels(
                authority.available_cards,
                source,
                maximum_level=SOURCE_CARDS,
                modulus=modulus,
            )
            adjoint_levels = _build_modular_levels(
                authority.available_cards,
                covectors,
                maximum_level=QUERY_CARDS,
                modulus=modulus,
            )
            forward_rows = {}
            for mask, expected in authority.forward_scaled_rows:
                row = _modular_signed_subset_row(
                    mask,
                    forward_levels,
                    exact.FORWARD_LEVEL_WEIGHTS,
                    modulus,
                    maximum_level=QUERY_CARDS,
                )
                if row != tuple(value % modulus for value in expected):
                    raise ArithmeticError("RRNS forward row differs from authority")
                forward_rows[mask] = row
                checked_forward_rows += 1
            adjoint_rows = {}
            for mask, expected in authority.adjoint_scaled_rows:
                row = _modular_signed_subset_row(
                    mask,
                    adjoint_levels,
                    exact.ADJOINT_LEVEL_WEIGHTS,
                    modulus,
                    maximum_level=QUERY_CARDS,
                )
                if row != tuple(value % modulus for value in expected):
                    raise ArithmeticError("RRNS adjoint row differs from authority")
                adjoint_rows[mask] = row
                checked_adjoint_rows += 1
            forward_numerator = 0
            reach = 0
            for mask in exact.complete_masks(authority.available_cards, QUERY_CARDS):
                for row_value, covector in zip(
                    forward_rows[mask], covectors[mask], strict=True
                ):
                    forward_numerator = (
                        forward_numerator + row_value * (covector % modulus)
                    ) % modulus
                reach = (
                    reach
                    + forward_rows[mask][captured.reach_feature]
                    * (weights[mask] % modulus)
                ) % modulus
            adjoint_numerator = 0
            for mask in exact.complete_masks(authority.available_cards, SOURCE_CARDS):
                for source_value, row_value in zip(
                    source[mask], adjoint_rows[mask], strict=True
                ):
                    adjoint_numerator = (
                        adjoint_numerator + (source_value % modulus) * row_value
                    ) % modulus
            if forward_numerator != adjoint_numerator:
                raise ArithmeticError("RRNS forward and adjoint residues differ")
            residues[modulus] = (forward_numerator, adjoint_numerator, reach)
    ordered_moduli = scalar_parameters.all_moduli
    numerator_value = RRNSValue(
        tuple(residues[modulus][0] for modulus in ordered_moduli),
        scalar_parameters,
    )
    adjoint_value = RRNSValue(
        tuple(residues[modulus][1] for modulus in ordered_moduli),
        scalar_parameters,
    )
    reach_value = RRNSValue(
        tuple(residues[modulus][2] for modulus in ordered_moduli),
        scalar_parameters,
    )
    decoded_numerator = reconstruct_scaled_rrns(numerator_value)
    decoded_adjoint = reconstruct_scaled_rrns(adjoint_value)
    decoded_reach = reconstruct_scaled_rrns(reach_value)
    require_unbounded_match(decoded_numerator, authority.forward_integer_numerator)
    require_unbounded_match(decoded_adjoint, authority.adjoint_integer_numerator)
    require_unbounded_match(decoded_reach, authority.forward_integer_reach)
    bits = exact.binary64_bits(
        exact.correctly_rounded_binary64(
            decoded_numerator,
            decoded_reach,
            authority.covector_family_exponent - authority.weight_family_exponent,
        )
    )
    if bits != authority.conditional_value_bits:
        raise ArithmeticError("RRNS terminal rounding differs from authority")
    geometry = _reduced_geometry(authority.available_cards, authority.feature_width)
    replay = 0
    if schedule == "batched_five_then_four":
        replay = 4 * (
            geometry.forward_recurrence_vector_edges
            + geometry.adjoint_recurrence_vector_edges
        )
    return CandidateOperatorResult(
        representation="fixed_62_bit_prime_residues_with_one_redundant_channel",
        schedule=schedule,
        forward_integer_numerator=decoded_numerator,
        adjoint_integer_numerator=decoded_adjoint,
        forward_integer_reach=decoded_reach,
        conditional_value_bits=bits,
        checked_forward_rows=checked_forward_rows,
        checked_adjoint_rows=checked_adjoint_rows,
        recomputed_vector_edges=replay,
        limb_work=None,
    )


@dataclass(frozen=True, slots=True)
class ReducedGeometry:
    available_cards: int
    feature_width: int
    source_occupancies: int
    query_occupancies: int
    labeled_query_records: int
    forward_rows_levels_0_through_5: int
    adjoint_rows_levels_0_through_4: int
    forward_recurrence_vector_edges: int
    adjoint_recurrence_vector_edges: int
    forward_signed_subset_row_terms_all_queries: int
    adjoint_signed_subset_row_terms_all_sources: int
    query_label_vector_additions: int
    forward_scalar_products_all_queries: int
    adjoint_scalar_products_all_sources: int


def _reduced_geometry(cards: int, feature_width: int) -> ReducedGeometry:
    available = _require_plain_integer(cards, label="geometry cards", minimum=10)
    width = _require_plain_integer(
        feature_width, label="geometry feature width", minimum=1
    )
    source = comb(available, SOURCE_CARDS)
    query = comb(available, QUERY_CARDS)
    forward_edges = sum(
        comb(available, level) * (available - level) for level in range(6)
    )
    adjoint_edges = sum(
        comb(available, level) * (available - level) for level in range(4)
    )
    return ReducedGeometry(
        available_cards=available,
        feature_width=width,
        source_occupancies=source,
        query_occupancies=query,
        labeled_query_records=query * QUERY_LABELS,
        forward_rows_levels_0_through_5=sum(
            comb(available, level) for level in range(6)
        ),
        adjoint_rows_levels_0_through_4=sum(
            comb(available, level) for level in range(5)
        ),
        forward_recurrence_vector_edges=forward_edges,
        adjoint_recurrence_vector_edges=adjoint_edges,
        forward_signed_subset_row_terms_all_queries=query * (1 << QUERY_CARDS),
        adjoint_signed_subset_row_terms_all_sources=source
        * sum(comb(SOURCE_CARDS, level) for level in range(5)),
        query_label_vector_additions=query * (QUERY_LABELS - 1),
        forward_scalar_products_all_queries=query * width,
        adjoint_scalar_products_all_sources=source * width,
    )


def verify_literal_45_formulas(
    base: Mapping[str, object] | None = None,
) -> ReducedGeometry:
    parsed = load_preregistered_config() if base is None else base
    row = parsed.get("literal_45_geometry")
    selective = parsed.get("selective_oracle_contract")
    ranking = parsed.get("colex_row_owned_candidate")
    memory = parsed.get("memory_ledger")
    if not all(isinstance(value, Mapping) for value in (row, selective, ranking, memory)):
        raise ValueError("literal-45 comparison sections differ")
    assert isinstance(row, Mapping)
    assert isinstance(selective, Mapping)
    assert isinstance(ranking, Mapping)
    assert isinstance(memory, Mapping)
    geometry = _reduced_geometry(
        int(row.get("available_cards", -1)), int(row.get("feature_width", -1))
    )
    mapping = {
        "source_occupancies": geometry.source_occupancies,
        "query_occupancies": geometry.query_occupancies,
        "labeled_query_records": geometry.labeled_query_records,
        "forward_rows_levels_0_through_5": geometry.forward_rows_levels_0_through_5,
        "adjoint_rows_levels_0_through_4": geometry.adjoint_rows_levels_0_through_4,
        "forward_recurrence_vector_edges": geometry.forward_recurrence_vector_edges,
        "adjoint_recurrence_vector_edges": geometry.adjoint_recurrence_vector_edges,
        "forward_signed_subset_row_terms_all_queries": geometry.forward_signed_subset_row_terms_all_queries,
        "adjoint_signed_subset_row_terms_all_sources": geometry.adjoint_signed_subset_row_terms_all_sources,
        "query_label_vector_additions": geometry.query_label_vector_additions,
        "forward_scalar_products_all_queries": geometry.forward_scalar_products_all_queries,
        "adjoint_scalar_products_all_sources": geometry.adjoint_scalar_products_all_sources,
    }
    if any(row.get(key) != value for key, value in mapping.items()):
        raise ValueError("literal-45 geometry differs")
    if row.get("source_pairing_visits_before_the_90_fold_quotient") != (
        geometry.source_occupancies * 90
    ):
        raise ValueError("literal-45 quotient capture count differs")
    forward_selective = selective.get("forward_after_G_is_built")
    adjoint_selective = selective.get("adjoint_after_H_is_built")
    query_scan = selective.get("all_query_forward_scan")
    source_scan = selective.get("all_source_adjoint_scan")
    if not all(
        isinstance(value, Mapping)
        for value in (forward_selective, adjoint_selective, query_scan, source_scan)
    ):
        raise ValueError("literal-45 selective rows differ")
    assert isinstance(forward_selective, Mapping)
    assert isinstance(adjoint_selective, Mapping)
    assert isinstance(query_scan, Mapping)
    assert isinstance(source_scan, Mapping)
    if dict(forward_selective) != {
        "one_query_subset_rows": 16,
        "one_query_subset_feature_entries": 16 * geometry.feature_width,
        "one_query_scalar_products_if_fully_contracted": geometry.feature_width,
    }:
        raise ValueError("literal-45 forward selective formula differs")
    if dict(adjoint_selective) != {
        "one_source_subset_rows": 57,
        "one_source_subset_feature_entries": 57 * geometry.feature_width,
        "one_source_scalar_products_if_fully_contracted": geometry.feature_width,
    }:
        raise ValueError("literal-45 adjoint selective formula differs")
    if query_scan.get("subset_feature_entries") != (
        geometry.forward_signed_subset_row_terms_all_queries * geometry.feature_width
    ) or query_scan.get("scalar_products") != geometry.forward_scalar_products_all_queries:
        raise ValueError("literal-45 complete forward scan differs")
    if source_scan.get("subset_feature_entries") != (
        geometry.adjoint_signed_subset_row_terms_all_sources * geometry.feature_width
    ) or source_scan.get("scalar_products") != geometry.adjoint_scalar_products_all_sources:
        raise ValueError("literal-45 complete adjoint scan differs")
    comparison = ranking.get("compare_against")
    if not isinstance(comparison, Mapping):
        raise ValueError("literal-45 rank-table comparison differs")
    expected_rank_bytes = {
        "rank_to_cards_uint8_bytes_source": geometry.source_occupancies * SOURCE_CARDS,
        "rank_to_mask_uint64_bytes_source": geometry.source_occupancies * 8,
        "rank_to_cards_uint8_bytes_query": geometry.query_occupancies * QUERY_CARDS,
        "rank_to_mask_uint64_bytes_query": geometry.query_occupancies * 8,
        "levels_0_through_5_mask_uint64_bytes": geometry.forward_rows_levels_0_through_5
        * 8,
        "forward_adjacency_uint32_bytes": geometry.forward_recurrence_vector_edges * 4,
        "adjoint_adjacency_uint32_bytes": geometry.adjoint_recurrence_vector_edges * 4,
    }
    if any(comparison.get(key) != value for key, value in expected_rank_bytes.items()):
        raise ValueError("literal-45 rank-table byte formula differs")
    if memory.get("positional_table_bytes_per_feature_cell_under_legacy_diagnostic") != 40:
        raise ValueError("literal-45 positional table bytes differ")
    if memory.get("positional_scalar_bytes_per_accumulator_under_legacy_diagnostic") != 72:
        raise ValueError("literal-45 positional scalar bytes differ")
    if memory.get("rrns_table_code_bytes_per_feature_cell") != 40:
        raise ValueError("literal-45 RRNS table-code bytes differ")
    if memory.get("rrns_resident_nine_bytes_per_feature_cell") != 72:
        raise ValueError("literal-45 resident RRNS bytes differ")
    return geometry


@dataclass(frozen=True, slots=True)
class SelectiveRow:
    mask: int
    values: tuple[int, ...]
    subset_rows_read: int
    subset_feature_entries: int


def selective_forward_row(
    levels: exact.IntegerLevels,
    query_mask: int,
) -> SelectiveRow:
    if levels.maximum_level != SOURCE_CARDS or query_mask.bit_count() != QUERY_CARDS:
        raise ValueError("selective forward input differs")
    maps = tuple(levels.level(level) for level in range(QUERY_CARDS + 1))
    width = len(next(iter(maps[0].values())))
    values = [0] * width
    rows = 0
    for subset in _submasks(query_mask):
        level = subset.bit_count()
        if subset not in maps[level]:
            raise ValueError("selective forward subset is absent")
        rows += 1
        coefficient = exact.FORWARD_LEVEL_WEIGHTS[level] * (-1 if level & 1 else 1)
        for feature, value in enumerate(maps[level][subset]):
            values[feature] += coefficient * value
    if rows != 16:
        raise AssertionError("selective forward did not read exactly 16 rows")
    return SelectiveRow(query_mask, tuple(values), rows, rows * width)


def selective_adjoint_row(
    levels: exact.IntegerLevels,
    source_mask: int,
) -> SelectiveRow:
    if levels.maximum_level != QUERY_CARDS or source_mask.bit_count() != SOURCE_CARDS:
        raise ValueError("selective adjoint input differs")
    maps = tuple(levels.level(level) for level in range(QUERY_CARDS + 1))
    width = len(next(iter(maps[0].values())))
    values = [0] * width
    rows = 0
    for subset in _submasks(source_mask):
        level = subset.bit_count()
        if level > QUERY_CARDS:
            continue
        if subset not in maps[level]:
            raise ValueError("selective adjoint subset is absent")
        rows += 1
        coefficient = exact.ADJOINT_LEVEL_WEIGHTS[level] * (-1 if level & 1 else 1)
        for feature, value in enumerate(maps[level][subset]):
            values[feature] += coefficient * value
    if rows != 57:
        raise AssertionError("selective adjoint did not read exactly 57 rows")
    return SelectiveRow(source_mask, tuple(values), rows, rows * width)


def _framed_integer(value: int) -> bytes:
    encoded = str(_require_plain_integer(value, label="scan integer")).encode("ascii")
    return len(encoded).to_bytes(4, "little") + encoded


@dataclass(frozen=True, slots=True)
class StreamedScanReceipt:
    domain_count: int
    order_sha256: str
    values_sha256: str
    chunk_sha256: str
    chunks: int
    retained_coordinate_rows: int


def stream_complete_domain(
    provided_domain: Iterable[int],
    complete_domain: Iterable[int],
    evaluator: Callable[[int], Sequence[int]],
    *,
    chunk_size: int,
) -> StreamedScanReceipt:
    """Scan the exact ordered domain while retaining no coordinate rows."""

    chunk = _require_plain_integer(chunk_size, label="scan chunk size", minimum=1)
    order_hash = sha256()
    value_hash = sha256()
    chunk_hashes = []
    current = sha256()
    in_chunk = 0
    count = 0
    sentinel = object()
    provided_iterator = iter(provided_domain)
    complete_iterator = iter(complete_domain)
    while True:
        coordinate = next(provided_iterator, sentinel)
        expected = next(complete_iterator, sentinel)
        if coordinate is sentinel and expected is sentinel:
            break
        if coordinate is sentinel or expected is sentinel or coordinate != expected:
            raise IncompleteGlobalClosure(
                "global closure domain is incomplete or reordered"
            )
        item = _require_plain_integer(coordinate, label="scan coordinate", minimum=0)
        count += 1
        order_hash.update(item.to_bytes(8, "little"))
        row = tuple(evaluator(item))
        framed = item.to_bytes(8, "little") + len(row).to_bytes(4, "little")
        for value in row:
            framed += _framed_integer(value)
        value_hash.update(framed)
        current.update(framed)
        in_chunk += 1
        if in_chunk == chunk:
            chunk_hashes.append(current.digest())
            current = sha256()
            in_chunk = 0
    if in_chunk:
        chunk_hashes.append(current.digest())
    aggregate_chunks = sha256()
    for digest in chunk_hashes:
        aggregate_chunks.update(digest)
    return StreamedScanReceipt(
        domain_count=count,
        order_sha256=order_hash.hexdigest(),
        values_sha256=value_hash.hexdigest(),
        chunk_sha256=aggregate_chunks.hexdigest(),
        chunks=len(chunk_hashes),
        retained_coordinate_rows=0,
    )


@dataclass(frozen=True, slots=True)
class ExactClosureReceipt:
    scan: StreamedScanReceipt
    maximum_reduced_cost: int | None
    violating_coordinates: int


def exact_global_closure(
    provided_domain: Iterable[int],
    complete_domain: Iterable[int],
    exact_price: Callable[[int], int],
    *,
    chunk_size: int,
) -> ExactClosureReceipt:
    maximum: int | None = None
    violations = 0

    def evaluate(coordinate: int) -> tuple[int]:
        nonlocal maximum, violations
        price = _require_plain_integer(exact_price(coordinate), label="exact price")
        maximum = price if maximum is None else max(maximum, price)
        violations += int(price > 0)
        return (price,)

    scan = stream_complete_domain(
        provided_domain,
        complete_domain,
        evaluate,
        chunk_size=chunk_size,
    )
    if violations:
        raise ArithmeticError("exact global closure found a positive reduced cost")
    return ExactClosureReceipt(scan, maximum, violations)


def colex_rank(cards: Sequence[int]) -> int:
    values = tuple(cards)
    if any(isinstance(card, bool) or not isinstance(card, int) for card in values):
        raise TypeError("colex cards must be integers")
    if tuple(sorted(values)) != values or len(set(values)) != len(values) or any(card < 0 for card in values):
        raise ValueError("colex cards must be unique sorted nonnegative integers")
    return sum(comb(card, index + 1) for index, card in enumerate(values))


def colex_unrank(rank: int, width: int, available_cards: int) -> tuple[int, ...]:
    value = _require_plain_integer(rank, label="colex rank", minimum=0)
    count = _require_plain_integer(width, label="colex width", minimum=0)
    cards = _require_plain_integer(
        available_cards, label="colex available cards", minimum=1
    )
    if count > cards or value >= comb(cards, count):
        raise ValueError("colex rank lies outside its domain")
    if count == 0:
        return ()
    remaining = value
    output = [0] * count
    ceiling = cards - 1
    for choose in range(count, 0, -1):
        candidate = ceiling
        while candidate >= choose - 1 and comb(candidate, choose) > remaining:
            candidate -= 1
        if candidate < choose - 1:
            raise AssertionError("colex unranking failed")
        output[choose - 1] = candidate
        remaining -= comb(candidate, choose)
        ceiling = candidate - 1
    result = tuple(output)
    if remaining or colex_rank(result) != value:
        raise AssertionError("colex unranking did not invert rank")
    return result


@dataclass(frozen=True, slots=True)
class ColexChildRank:
    inserted_card: int
    insertion_position: int
    child_rank: int


@dataclass(frozen=True, slots=True)
class ColexRowReceipt:
    parent_rank: int
    parent_cards: tuple[int, ...]
    children: tuple[ColexChildRank, ...]
    unrank_calls: int
    insertion_position_advances: int
    child_binomial_lookups: int
    child_rank_additions: int


def row_owned_colex_child_ranks(
    parent_rank: int,
    width: int,
    available_cards: int,
) -> ColexRowReceipt:
    cards = colex_unrank(parent_rank, width, available_cards)
    prefix = [0]
    for index, card in enumerate(cards):
        prefix.append(prefix[-1] + comb(card, index + 1))
    suffix = [0] * (len(cards) + 1)
    for index in range(len(cards) - 1, -1, -1):
        suffix[index] = suffix[index + 1] + comb(cards[index], index + 2)
    occupied = set(cards)
    insertion = 0
    advances = 0
    children = []
    for card in range(available_cards):
        if card in occupied:
            insertion += 1
            advances += 1
            continue
        rank = prefix[insertion] + comb(card, insertion + 1) + suffix[insertion]
        child_cards = cards[:insertion] + (card,) + cards[insertion:]
        if rank != colex_rank(child_cards):
            raise AssertionError("row-owned colex child rank differs")
        children.append(ColexChildRank(card, insertion, rank))
    if advances != width or len(children) != available_cards - width:
        raise AssertionError("row-owned colex traversal count differs")
    if len({row.child_rank for row in children}) != len(children):
        raise AssertionError("row-owned colex traversal duplicated a child")
    return ColexRowReceipt(
        parent_rank=parent_rank,
        parent_cards=cards,
        children=tuple(children),
        unrank_calls=1,
        insertion_position_advances=advances,
        child_binomial_lookups=len(children),
        child_rank_additions=2 * len(children),
    )


def validate_colex_row_receipt(
    receipt: ColexRowReceipt,
    *,
    width: int,
    available_cards: int,
) -> None:
    expected_parent = colex_unrank(receipt.parent_rank, width, available_cards)
    if receipt.parent_cards != expected_parent or receipt.unrank_calls != 1:
        raise ValueError("colex row receipt parent or unrank count differs")
    expected = row_owned_colex_child_ranks(
        receipt.parent_rank, width, available_cards
    )
    if receipt != expected:
        raise ValueError("colex row receipt child ranks or work differ")


@dataclass(frozen=True, slots=True)
class PrimitiveWorkLedger:
    candidate: str
    mode: str
    source_and_query_pair_capture_or_residue_conversion_reads: int
    uint64_load_bytes: int
    uint64_store_bytes: int
    word_adds_and_carry_or_borrow_steps: int
    wide_64x64_low_high_products: int
    small_weight_products: int
    modular_adds: int
    conditional_subtractions: int
    montgomery_reductions: int
    CRT_or_base_extension_steps: int
    colex_unrank_calls: int
    colex_binomial_lookups: int
    colex_child_rank_additions: int
    redundant_residue_checks: int
    recomputed_edges_under_channel_batching: int


def _zero_work(candidate: str, mode: str) -> PrimitiveWorkLedger:
    return PrimitiveWorkLedger(candidate, mode, *(0 for _ in range(15)))


def literal_45_work_ledgers() -> tuple[PrimitiveWorkLedger, ...]:
    """Return incomparable primitive counts; deliberately provide no total."""

    geometry = verify_literal_45_formulas()
    modes = (
        "cold_build_G",
        "cold_build_H",
        "one_selective_forward_query",
        "one_selective_adjoint_query",
        "streamed_all_query_forward_scan",
        "streamed_all_source_adjoint_scan",
        "exact_terminal_decode_and_round",
        "cold_release",
    )
    candidates = (
        ("positional", 5, 0, False),
        ("resident_nine_RRNS", 9, 9, False),
        ("batched_five_then_four_RRNS", 5, 9, True),
    )
    ledgers = []
    for candidate, resident_words, arithmetic_channels, batched in candidates:
        traffic_words = arithmetic_channels or resident_words
        capture_passes = 2 if batched else 1
        for mode in modes:
            row = _zero_work(candidate, mode)
            values = {field.name: getattr(row, field.name) for field in fields(row)}
            if mode == "cold_build_G":
                entries = geometry.forward_recurrence_vector_edges * geometry.feature_width
                values["source_and_query_pair_capture_or_residue_conversion_reads"] = (
                    geometry.source_occupancies
                    * geometry.feature_width
                    * 2
                    * capture_passes
                )
                values["uint64_load_bytes"] = entries * traffic_words * 16
                values["uint64_store_bytes"] = entries * traffic_words * 8
                values["colex_unrank_calls"] = geometry.forward_rows_levels_0_through_5
                values["colex_binomial_lookups"] = geometry.forward_recurrence_vector_edges
                values["colex_child_rank_additions"] = 2 * geometry.forward_recurrence_vector_edges
                if arithmetic_channels:
                    values["modular_adds"] = entries * arithmetic_channels
                    values["conditional_subtractions"] = entries * arithmetic_channels
                else:
                    values["word_adds_and_carry_or_borrow_steps"] = entries * 5
                if batched:
                    values["recomputed_edges_under_channel_batching"] = (
                        4 * geometry.forward_recurrence_vector_edges
                    )
            elif mode == "cold_build_H":
                vector_edges = (
                    geometry.adjoint_recurrence_vector_edges
                    + geometry.query_label_vector_additions
                )
                entries = vector_edges * geometry.feature_width
                values["source_and_query_pair_capture_or_residue_conversion_reads"] = (
                    geometry.labeled_query_records
                    * (geometry.feature_width + 1)
                    * 2
                    * capture_passes
                )
                scalar_label_additions = geometry.query_label_vector_additions
                values["uint64_load_bytes"] = (
                    entries + scalar_label_additions
                ) * traffic_words * 16
                values["uint64_store_bytes"] = (
                    entries + scalar_label_additions
                ) * traffic_words * 8
                values["colex_unrank_calls"] = geometry.adjoint_rows_levels_0_through_4
                values["colex_binomial_lookups"] = geometry.adjoint_recurrence_vector_edges
                values["colex_child_rank_additions"] = 2 * geometry.adjoint_recurrence_vector_edges
                if arithmetic_channels:
                    values["modular_adds"] = (
                        entries + scalar_label_additions
                    ) * arithmetic_channels
                    values["conditional_subtractions"] = (
                        entries + scalar_label_additions
                    ) * arithmetic_channels
                else:
                    values["word_adds_and_carry_or_borrow_steps"] = (
                        entries + scalar_label_additions
                    ) * 5
                if batched:
                    values["recomputed_edges_under_channel_batching"] = (
                        4 * geometry.adjoint_recurrence_vector_edges
                    )
            else:
                terms = 0
                scalar_products = 0
                if mode == "one_selective_forward_query":
                    terms = 16 * geometry.feature_width
                    scalar_products = geometry.feature_width
                    reach_products = 1
                elif mode == "one_selective_adjoint_query":
                    terms = 57 * geometry.feature_width
                    scalar_products = geometry.feature_width
                    reach_products = 0
                elif mode == "streamed_all_query_forward_scan":
                    terms = (
                        geometry.forward_signed_subset_row_terms_all_queries
                        * geometry.feature_width
                    )
                    scalar_products = geometry.forward_scalar_products_all_queries
                    reach_products = geometry.query_occupancies
                elif mode == "streamed_all_source_adjoint_scan":
                    terms = (
                        geometry.adjoint_signed_subset_row_terms_all_sources
                        * geometry.feature_width
                    )
                    scalar_products = geometry.adjoint_scalar_products_all_sources
                    reach_products = 0
                else:
                    reach_products = 0
                if terms:
                    values["uint64_load_bytes"] = terms * traffic_words * 8
                    values["uint64_store_bytes"] = (
                        scalar_products + reach_products
                    ) * traffic_words * 8
                    values["small_weight_products"] = terms * (
                        arithmetic_channels or 1
                    )
                    if arithmetic_channels:
                        values["modular_adds"] = terms * arithmetic_channels
                        values["conditional_subtractions"] = terms * arithmetic_channels
                        values["montgomery_reductions"] = (
                            terms + scalar_products + reach_products
                        ) * arithmetic_channels
                        values["wide_64x64_low_high_products"] = (
                            3 * values["montgomery_reductions"]
                        )
                    else:
                        values["word_adds_and_carry_or_borrow_steps"] = terms * 5
                        values["wide_64x64_low_high_products"] = (
                            terms * 5
                            + (scalar_products + reach_products) * 25
                        )
                elif mode == "exact_terminal_decode_and_round":
                    if arithmetic_channels:
                        values["uint64_load_bytes"] = 3 * 9 * 8
                        values["CRT_or_base_extension_steps"] = 3 * (9 + 8)
                        values["redundant_residue_checks"] = 3
                    else:
                        values["uint64_load_bytes"] = 3 * 9 * 8
            ledgers.append(PrimitiveWorkLedger(**values))
    return tuple(ledgers)


@dataclass(frozen=True, slots=True)
class MemoryLedger:
    candidate: str
    table_bytes_per_feature_cell: int
    scalar_bytes_per_accumulator: int
    captured_pair_level_6_bytes: int
    forward_levels_0_through_5_bytes: int
    adjoint_levels_0_through_4_bytes: int
    streamed_query_output_chunk_bytes: int
    streamed_source_output_chunk_bytes: int
    source_rank_to_cards_bytes: int
    source_rank_to_mask_bytes: int
    forward_adjacency_bytes_if_materialized: int
    adjoint_adjacency_bytes_if_materialized: int
    second_batch_forward_recurrence_scratch_bytes: int
    second_batch_adjoint_recurrence_scratch_bytes: int
    forward_replay_input_bytes: int
    adjoint_replay_input_bytes: int
    complete_dense_output_bytes_charged: int


def literal_45_memory_ledgers(
    *,
    logical_tile_width: int = 64,
    query_chunk: int = 4096,
    source_chunk: int = 4096,
) -> tuple[MemoryLedger, ...]:
    geometry = verify_literal_45_formulas()
    width = _require_plain_integer(
        logical_tile_width, label="memory logical tile width", minimum=1
    )
    q_chunk = _require_plain_integer(query_chunk, label="query chunk", minimum=1)
    s_chunk = _require_plain_integer(source_chunk, label="source chunk", minimum=1)
    if width > geometry.feature_width or q_chunk > geometry.query_occupancies or s_chunk > geometry.source_occupancies:
        raise ValueError("memory ledger dimension exceeds literal-45 geometry")
    captured = geometry.source_occupancies * width * 2 * 8
    common = {
        "scalar_bytes_per_accumulator": 72,
        "captured_pair_level_6_bytes": captured,
        "source_rank_to_cards_bytes": geometry.source_occupancies * SOURCE_CARDS,
        "source_rank_to_mask_bytes": geometry.source_occupancies * 8,
        "forward_adjacency_bytes_if_materialized": geometry.forward_recurrence_vector_edges * 4,
        "adjoint_adjacency_bytes_if_materialized": geometry.adjoint_recurrence_vector_edges * 4,
        "complete_dense_output_bytes_charged": 0,
    }
    output = []
    for candidate, cell_bytes, scratch_channels, replay_inputs in (
        ("positional", 40, 0, False),
        ("resident_nine_RRNS", 72, 0, False),
        ("batched_five_then_four_RRNS", 40, 4, True),
    ):
        output.append(
            MemoryLedger(
                candidate=candidate,
                table_bytes_per_feature_cell=cell_bytes,
                forward_levels_0_through_5_bytes=geometry.forward_rows_levels_0_through_5
                * width
                * cell_bytes,
                adjoint_levels_0_through_4_bytes=geometry.adjoint_rows_levels_0_through_4
                * width
                * cell_bytes,
                streamed_query_output_chunk_bytes=q_chunk * width * cell_bytes,
                streamed_source_output_chunk_bytes=s_chunk * width * cell_bytes,
                second_batch_forward_recurrence_scratch_bytes=geometry.forward_rows_levels_0_through_5
                * width
                * scratch_channels
                * 8,
                second_batch_adjoint_recurrence_scratch_bytes=geometry.adjoint_rows_levels_0_through_4
                * width
                * scratch_channels
                * 8,
                forward_replay_input_bytes=captured if replay_inputs else 0,
                adjoint_replay_input_bytes=geometry.labeled_query_records
                * (width + 1)
                * 2
                * 8
                if replay_inputs
                else 0,
                **common,
            )
        )
    return tuple(output)


def validate_source_semantics(source_text: str) -> None:
    """Reject device imports, semantic scale inverses, and truncated products."""

    if not isinstance(source_text, str):
        raise TypeError("source semantics input must be text")
    tree = ast.parse(source_text)
    forbidden_roots = {"numpy", "cupy", "torch", "numba", "cuda"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = {alias.name.split(".")[0] for alias in node.names}
            if names & forbidden_roots:
                raise ValueError("device or numeric-array import is forbidden")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in forbidden_roots:
                raise ValueError("device or numeric-array import is forbidden")
        elif isinstance(node, ast.Name) and "inverse_720" in node.id.lower():
            raise ValueError("semantic inverse of 720 is forbidden")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "pow":
            if len(node.args) >= 2 and isinstance(node.args[0], ast.Constant) and isinstance(
                node.args[0].value, int
            ):
                first = node.args[0].value
                second = node.args[1]
                is_minus_one = (
                    isinstance(second, ast.UnaryOp)
                    and isinstance(second.op, ast.USub)
                    and isinstance(second.operand, ast.Constant)
                    and second.operand.value == 1
                )
                if is_minus_one and first > 0 and COMMON_SCALE % first == 0:
                    raise ValueError("semantic inverse of 720 or a factor is forbidden")
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitAnd):
            if isinstance(node.left, ast.BinOp) and isinstance(node.left.op, ast.Mult):
                operands = (node.left.left, node.left.right)
                is_montgomery_low_multiplier = any(
                    isinstance(operand, ast.Attribute)
                    and operand.attr == "negative_inverse"
                    for operand in operands
                ) and any(
                    isinstance(operand, ast.BinOp)
                    and isinstance(operand.op, ast.BitAnd)
                    for operand in operands
                )
                if not is_montgomery_low_multiplier:
                    raise ValueError("truncated 64-bit product is forbidden")
    for function in (
        node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ):
        multiplied_names = {
            target.id
            for node in ast.walk(function)
            if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.BinOp)
            and isinstance(node.value.op, ast.Mult)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        masked_names = {
            child.left.id
            for child in ast.walk(function)
            if isinstance(child, ast.BinOp)
            and isinstance(child.op, ast.BitAnd)
            and isinstance(child.left, ast.Name)
        }
        shifted_names = {
            child.left.id
            for child in ast.walk(function)
            if isinstance(child, ast.BinOp)
            and isinstance(child.op, ast.RShift)
            and isinstance(child.left, ast.Name)
        }
        if (multiplied_names & masked_names) - shifted_names:
            raise ValueError("truncated 64-bit product is forbidden")


def validate_no_scale_inverse_constants(value: object) -> None:
    """Reject numeric config constants named as inverses of 720 or its factors."""

    factors = {1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 18, 20, 24, 30, 36,
               40, 45, 48, 60, 72, 80, 90, 120, 144, 180, 240, 360, 720}

    def walk(item: object, path: tuple[str, ...]) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                name = str(key).lower()
                numeric_tokens = {
                    int(token)
                    for token in "".join(
                        character if character.isdigit() else " " for character in name
                    ).split()
                }
                named_scale_inverse = (
                    "inverse_of_" in name
                    or name.startswith("inverse_")
                    or name.startswith("modular_inverse_")
                )
                if (
                    named_scale_inverse
                    and isinstance(child, int)
                    and not isinstance(child, bool)
                    and bool(numeric_tokens & factors)
                ):
                    raise ValueError("config contains a semantic inverse of 720 or a factor")
                walk(child, path + (name,))
        elif isinstance(item, (list, tuple)):
            for index, child in enumerate(item):
                walk(child, path + (str(index),))

    walk(value, ())


def validate_independent_normalizer_structure(source_text: str) -> None:
    tree = ast.parse(source_text)
    functions = {
        node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    node = functions.get("independent_canonical_lf_bytes")
    if node is None:
        raise ValueError("independent canonical normalizer is absent")
    for child in ast.walk(node):
        if isinstance(child, ast.Attribute) and child.attr == "replace":
            raise ValueError("independent normalizer may not use replace")
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "canonical_lf_bytes":
            raise ValueError("independent normalizer may not call production")


def verify_source_surface(path: Path = Path(__file__)) -> None:
    source = path.read_text(encoding="utf-8")
    validate_source_semantics(source)
    validate_independent_normalizer_structure(source)
    literal_escape_mutation_receipt(
        path,
        expected_occurrences=1,
        require_armed=True,
    )


__all__ = [
    "ADR0436_SHA256",
    "ADR0437_SHA256",
    "ArmedMutationReceipt",
    "CORRECTION_CONFIG_SHA256",
    "CandidateOperatorResult",
    "ColexChildRank",
    "ColexRowReceipt",
    "ComponentTelemetry",
    "ExactClosureReceipt",
    "FamilyTelemetry",
    "FrozenBoundProfile",
    "IncompleteGlobalClosure",
    "LimbWork",
    "MILLER_RABIN_BASES",
    "MemoryLedger",
    "MontgomeryConstants",
    "PREREGISTERED_CONFIG_SHA256",
    "PrimitiveWorkLedger",
    "RRNSChannelFaultDetected",
    "RRNSFaultObservation",
    "RRNSParameters",
    "RRNSValue",
    "ReducedGeometry",
    "SMALL_PRIMES",
    "SelectiveRow",
    "SignedLimbPlan",
    "SignedLimbs",
    "StreamedScanReceipt",
    "canonical_lf_bytes",
    "canonical_lf_sha256",
    "captured_operator_telemetry",
    "colex_rank",
    "colex_unrank",
    "derive_frozen_bound_profile",
    "evaluate_positional_operator",
    "evaluate_rrns_operator",
    "exact_global_closure",
    "family_telemetry",
    "independent_canonical_lf_bytes",
    "independent_canonical_lf_sha256",
    "is_prime_u64",
    "limb_accumulate",
    "limb_add",
    "limb_full_product",
    "limb_multiply_small",
    "limb_negate",
    "limb_subtract",
    "literal_45_memory_ledgers",
    "literal_45_work_ledgers",
    "literal_escape_mutation_receipt",
    "load_correction_config",
    "load_preregistered_config",
    "montgomery_constants",
    "montgomery_decode",
    "montgomery_encode",
    "montgomery_multiply",
    "montgomery_reduce",
    "observe_rrns_fault",
    "reconstruct_scaled_rrns",
    "require_unbounded_match",
    "row_owned_colex_child_ranks",
    "rrns_add",
    "rrns_multiply",
    "rrns_multiply_small",
    "rrns_reconstruct_base_extension",
    "rrns_reconstruct_both",
    "rrns_reconstruct_full",
    "rrns_subtract",
    "selective_adjoint_row",
    "selective_forward_row",
    "stream_complete_domain",
    "validate_frozen_rrns",
    "validate_colex_row_receipt",
    "validate_independent_normalizer_structure",
    "validate_no_scale_inverse_constants",
    "validate_source_semantics",
    "verify_frozen_bound_profile",
    "verify_known_telemetry",
    "verify_literal_45_formulas",
    "verify_preregistered_contract",
    "verify_source_surface",
]
