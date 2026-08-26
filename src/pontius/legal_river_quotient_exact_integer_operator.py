"""CPU-only exact-integer occupied-card operator over captured Float64 pairs.

The exactness boundary is deliberately narrow: source rows, labeled query
covectors, and query weights have already been captured as ``(high, low)``
binary64 pairs.  This module treats each pair as its exact dyadic sum.  It does
not claim that the capture reproduced unrounded upstream factor products.

No function in this module imports NumPy, CuPy, a device runtime, or an owner.
The only literal-45 entry points return integer geometry, work, and byte
formulas; they never construct a 45-card numerical population.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
from math import comb, factorial, isfinite
from pathlib import Path
import struct
from typing import Iterable, Mapping, Sequence


_ROOT = Path(__file__).parents[2]
_CONFIG_V1 = (
    _ROOT
    / "experiments/configs/"
    "legal-river-quotient-exact-integer-operator-keystone-v1.json"
)
_CONFIG_V2 = (
    _ROOT
    / "experiments/configs/"
    "legal-river-quotient-exact-integer-operator-keystone-v2-provenance.json"
)
PREREGISTERED_CONFIG_SHA256 = (
    "64b545b17b67f2828e3f58bfc4518dc2615b5fe7cc3dcbd921a3c36477e32fc6"
)
CORRECTION_CONFIG_SHA256 = (
    "cf652a2c4e36001081e38aa37e3f306fa5aeb805d67788ff1028a672bab03467"
)

SOURCE_CARDS = 6
QUERY_CARDS = 4
QUERY_LABELS = 6
COMMON_SCALE = 720
FORWARD_LEVEL_WEIGHTS = (1, 6, 30, 120, 360)
ADJOINT_LEVEL_WEIGHTS = (30, 120, 360, 720, 720)


_EXPECTED_SOURCE_PATHS = {
    "adr0368": "docs/decisions/ADR-0368-seal-the-exact-occupied-card-quotient-keystone.md",
    "adr0393": "docs/decisions/ADR-0393-retain-the-paired-tile-wall-rejection.md",
    "adr0432": "docs/decisions/ADR-0432-retain-the-shared-direct-artifact-capacity-rejection.md",
    "occupied_card_quotient": "src/pontius/occupied_card_quotient.py",
    "gpu_occupied_card_quotient": "src/pontius/gpu_occupied_card_quotient.py",
    "legal_river_quotient_bridge": "src/pontius/legal_river_quotient_bridge.py",
    "legal_river_quotient_bridge_config": "experiments/configs/legal-river-quotient-bridge-v1.json",
    "legal_river_quotient_cuda_consumer": "src/pontius/legal_river_quotient_cuda_consumer.py",
    "legal_river_quotient_cuda_compensated_tiles": "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "legal_river_quotient_cuda_compensated_tiles_v2_config": "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v2.json",
}


def canonical_lf_sha256(path: Path) -> str:
    """Hash one required repository file after CRLF-to-LF normalization."""

    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"exact-integer provenance path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistered_config(path: Path = _CONFIG_V1) -> dict[str, object]:
    """Load ADR-0433's immutable prospective config without side effects."""

    if not isinstance(path, Path) or not path.is_file():
        raise ValueError("exact-integer config path is absent")
    raw = path.read_bytes()
    if len(raw) > 1_048_576:
        raise ValueError("exact-integer config exceeds its byte ceiling")
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != (
        PREREGISTERED_CONFIG_SHA256
    ):
        raise ValueError("exact-integer config differs from ADR-0433")
    parsed = json.loads(raw)
    if (
        not isinstance(parsed, dict)
        or parsed.get("schema_version")
        != "legal-river-quotient-exact-integer-operator-keystone-v1"
        or parsed.get("evidence_stage")
        != "preregistered_after_adr0432_before_exact_integer_source_or_values"
    ):
        raise ValueError("exact-integer config schema or stage differs")
    return parsed


def load_correction_config(path: Path = _CONFIG_V2) -> dict[str, object]:
    """Load ADR-0434's provenance-only overlay without side effects."""

    if not isinstance(path, Path) or not path.is_file():
        raise ValueError("exact-integer correction config path is absent")
    raw = path.read_bytes()
    if len(raw) > 1_048_576:
        raise ValueError("exact-integer correction config exceeds its byte ceiling")
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != (
        CORRECTION_CONFIG_SHA256
    ):
        raise ValueError("exact-integer correction config differs from ADR-0434")
    parsed = json.loads(raw)
    if (
        not isinstance(parsed, dict)
        or parsed.get("schema_version")
        != "legal-river-quotient-exact-integer-operator-keystone-v2-provenance"
        or parsed.get("evidence_stage")
        != "corrected_after_uncommitted_cpu_source_and_bounded_controls_before_source_seal"
    ):
        raise ValueError("exact-integer correction schema or stage differs")
    return parsed


def load_preregistered_configs() -> tuple[dict[str, object], dict[str, object]]:
    """Load the immutable scientific base and provenance correction."""

    return load_preregistered_config(), load_correction_config()


def _literal_escape_rewrite_sha256(path: Path) -> tuple[str, int]:
    """Return ADR-0434's forbidden transform as mutation evidence only."""

    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"exact-integer provenance mutation path is absent: {path}")
    raw = path.read_bytes()
    token = bytes((92, 114, 92, 110))
    replacement = bytes((92, 110))
    return sha256(raw.replace(token, replacement)).hexdigest(), raw.count(token)


def verify_preregistered_contract(
    configs: tuple[Mapping[str, object], Mapping[str, object]] | None = None,
) -> None:
    """Rebind every frozen parent and the critical algebra/work constants."""

    parsed, correction = load_preregistered_configs() if configs is None else configs
    sources = parsed.get("expected_sources")
    claims = parsed.get("claims")
    division = parsed.get("division_free_operator")
    geometry = parsed.get("literal_45_geometry_work_model_only")
    corrected_sources = correction.get("corrected_expected_sources")
    defect = correction.get("defect")
    correction_claims = correction.get("claims")
    controls = correction.get("source_seal_hash_controls")
    unchanged = correction.get("unchanged_science")
    if not all(
        isinstance(value, Mapping)
        for value in (
            sources,
            claims,
            division,
            geometry,
            corrected_sources,
            defect,
            correction_claims,
            controls,
            unchanged,
        )
    ):
        raise ValueError("exact-integer typed config sections differ")
    assert isinstance(sources, Mapping)
    assert isinstance(claims, Mapping)
    assert isinstance(division, Mapping)
    assert isinstance(geometry, Mapping)
    assert isinstance(corrected_sources, Mapping)
    assert isinstance(defect, Mapping)
    assert isinstance(correction_claims, Mapping)
    assert isinstance(controls, Mapping)
    assert isinstance(unchanged, Mapping)
    if set(sources) != set(_EXPECTED_SOURCE_PATHS):
        raise ValueError("exact-integer dependency set differs")
    if set(corrected_sources) != set(_EXPECTED_SOURCE_PATHS):
        raise ValueError("exact-integer corrected dependency set differs")
    if correction.get("parent_v1_config_canonical_lf_sha256") != (
        PREREGISTERED_CONFIG_SHA256
    ):
        raise ValueError("exact-integer correction does not bind V1")
    for label, relative in _EXPECTED_SOURCE_PATHS.items():
        if corrected_sources[label] != canonical_lf_sha256(_ROOT / relative):
            raise ValueError(f"exact-integer dependency differs: {label}")
    affected = defect.get("affected_sources")
    expected_affected = {
        "legal_river_quotient_bridge",
        "legal_river_quotient_cuda_consumer",
        "legal_river_quotient_cuda_compensated_tiles",
    }
    if not isinstance(affected, Mapping) or set(affected) != expected_affected:
        raise ValueError("exact-integer affected provenance set differs")
    for label in expected_affected:
        row = affected[label]
        if not isinstance(row, Mapping):
            raise ValueError(f"exact-integer affected provenance row differs: {label}")
        relative = _EXPECTED_SOURCE_PATHS[label]
        mutation_hash, mutation_count = _literal_escape_rewrite_sha256(
            _ROOT / relative
        )
        if (
            row.get("relative_path") != relative
            or row.get("v1_false_sha256") != sources[label]
            or row.get("canonical_lf_sha256") != corrected_sources[label]
            or row.get("literal_escape_token_occurrences") != mutation_count
            or mutation_hash != sources[label]
            or sources[label] == corrected_sources[label]
        ):
            raise ValueError(f"exact-integer false-hash mutation differs: {label}")
    for label in set(_EXPECTED_SOURCE_PATHS) - expected_affected:
        if sources[label] != corrected_sources[label]:
            raise ValueError(f"exact-integer unaffected provenance differs: {label}")
    if (
        division.get("common_integer_scale") != COMMON_SCALE
        or division.get("forward_level_weights_k_0_through_4")
        != list(FORWARD_LEVEL_WEIGHTS)
        or division.get("adjoint_level_weights_k_0_through_4")
        != list(ADJOINT_LEVEL_WEIGHTS)
    ):
        raise ValueError("exact-integer factorial scale contract differs")
    expected_work = literal_45_work_model()
    for field in (
        "source_occupancies",
        "query_occupancies",
        "labeled_query_records",
        "forward_rows_levels_0_through_5",
        "adjoint_rows_levels_0_through_4",
        "forward_recurrence_vector_edges",
        "adjoint_recurrence_vector_edges",
        "forward_signed_subset_vector_terms_by_query_occupancy",
        "adjoint_signed_subset_vector_terms_by_source_occupancy",
        "query_label_vector_additions",
        "forward_aggregated_scalar_products",
        "adjoint_dense_scalar_products",
        "source_pairing_visits_per_full_capture",
    ):
        if geometry.get(field) != getattr(expected_work, field):
            raise ValueError(f"exact-integer literal-45 work differs: {field}")
    if not all(value is None or value is False for value in claims.values()):
        raise ValueError("exact-integer preregistered claims are open")
    if correction_claims.get("provenance_correction_recorded") is not True or not all(
        key == "provenance_correction_recorded" or value is None or value is False
        for key, value in correction_claims.items()
    ):
        raise ValueError("exact-integer correction claims are open")
    if not controls or not all(value is True for value in controls.values()):
        raise ValueError("exact-integer correction hash controls differ")
    if not unchanged or not all(value is True for value in unchanged.values()):
        raise ValueError("exact-integer correction changed science")


def _integer(value: object, *, label: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    return value


@dataclass(frozen=True, slots=True)
class CapturedPair:
    """One captured high/low binary64 pair."""

    high: float
    low: float

    def __post_init__(self) -> None:
        if type(self.high) is not float or type(self.low) is not float:
            raise TypeError("captured pair components must be Python binary64 floats")
        if not isfinite(self.high) or not isfinite(self.low):
            raise ValueError("captured pair components must be finite")

    @property
    def exact(self) -> Fraction:
        return Fraction.from_float(self.high) + Fraction.from_float(self.low)


@dataclass(frozen=True, slots=True)
class FrozenExponentWindow:
    """Inclusive canonical-component exponent admission for one future epoch."""

    minimum: int
    maximum: int

    def __post_init__(self) -> None:
        low = _integer(self.minimum, label="minimum exponent")
        high = _integer(self.maximum, label="maximum exponent")
        if low > high:
            raise ValueError("exponent window minimum exceeds maximum")

    def admit(self, exponent: int) -> None:
        value = _integer(exponent, label="component exponent")
        if value < self.minimum or value > self.maximum:
            raise OverflowError("captured component lies outside the frozen exponent window")


def canonical_float_component(value: float) -> tuple[int, int] | None:
    """Return odd signed mantissa and power-of-two exponent for one binary64."""

    if type(value) is not float:
        raise TypeError("binary component must be a Python float")
    if not isfinite(value):
        raise ValueError("binary component must be finite")
    if value == 0.0:
        return None
    numerator, denominator = value.as_integer_ratio()
    exponent = -(denominator.bit_length() - 1)
    while numerator % 2 == 0:
        numerator //= 2
        exponent += 1
    return numerator, exponent


def _normalize_pair_matrix(
    rows: Sequence[Sequence[CapturedPair]],
    *,
    label: str,
) -> tuple[tuple[CapturedPair, ...], ...]:
    try:
        normalized = tuple(tuple(row) for row in rows)
    except TypeError as exc:
        raise TypeError(f"{label} must be a rectangular pair matrix") from exc
    if not normalized or not normalized[0]:
        raise ValueError(f"{label} must be nonempty")
    width = len(normalized[0])
    if any(len(row) != width for row in normalized):
        raise ValueError(f"{label} must be rectangular")
    if any(not isinstance(pair, CapturedPair) for row in normalized for pair in row):
        raise TypeError(f"{label} contains a non-pair value")
    return normalized


@dataclass(frozen=True, slots=True)
class EncodedPairMatrix:
    """One exact fixed-point matrix with a family-wide dyadic exponent."""

    family_exponent: int
    rows: tuple[tuple[int, ...], ...]
    maximum_absolute_entry: int

    @property
    def shape(self) -> tuple[int, int]:
        return (len(self.rows), len(self.rows[0]))


def encode_pair_matrix(
    rows: Sequence[Sequence[CapturedPair]],
    *,
    label: str = "captured pair matrix",
    admitted_window: FrozenExponentWindow | None = None,
) -> EncodedPairMatrix:
    """Encode a complete captured family without any rounding."""

    matrix = _normalize_pair_matrix(rows, label=label)
    decomposed: list[list[tuple[tuple[int, int] | None, tuple[int, int] | None]]] = []
    exponents: list[int] = []
    for row in matrix:
        decoded_row = []
        for pair in row:
            high = canonical_float_component(pair.high)
            low = canonical_float_component(pair.low)
            for component in (high, low):
                if component is not None:
                    if admitted_window is not None:
                        admitted_window.admit(component[1])
                    exponents.append(component[1])
            decoded_row.append((high, low))
        decomposed.append(decoded_row)
    family_exponent = min(exponents, default=0)
    encoded_rows = []
    maximum = 0
    for row in decomposed:
        encoded_row = []
        for high, low in row:
            value = 0
            for component in (high, low):
                if component is not None:
                    mantissa, exponent = component
                    shift = exponent - family_exponent
                    if shift < 0:
                        raise AssertionError("family exponent did not bound a component")
                    value += mantissa << shift
            encoded_row.append(value)
            maximum = max(maximum, abs(value))
        encoded_rows.append(tuple(encoded_row))
    result = EncodedPairMatrix(
        family_exponent=family_exponent,
        rows=tuple(encoded_rows),
        maximum_absolute_entry=maximum,
    )
    for captured_row, encoded_row in zip(matrix, result.rows, strict=True):
        for pair, integer_value in zip(captured_row, encoded_row, strict=True):
            exact = _dyadic_fraction(integer_value, family_exponent)
            if exact != pair.exact:
                raise AssertionError("captured pair encoding rounded a dyadic value")
    return result


def encode_pair_vector(
    values: Sequence[CapturedPair],
    *,
    label: str = "captured pair vector",
    admitted_window: FrozenExponentWindow | None = None,
) -> EncodedPairMatrix:
    """Encode a vector as a one-column fixed-point family."""

    return encode_pair_matrix(
        tuple((value,) for value in values),
        label=label,
        admitted_window=admitted_window,
    )


def _dyadic_fraction(integer_value: int, exponent: int) -> Fraction:
    if exponent >= 0:
        return Fraction(integer_value << exponent, 1)
    return Fraction(integer_value, 1 << -exponent)


def _mask(cards: Iterable[int]) -> int:
    return sum(1 << card for card in cards)


def complete_masks(available_cards: int, width: int) -> tuple[int, ...]:
    cards = _integer(available_cards, label="available cards", minimum=1)
    count = _integer(width, label="mask width", minimum=0)
    if count > cards:
        raise ValueError("mask width exceeds available cards")
    return tuple(_mask(values) for values in combinations(range(cards), count))


def _validate_mask(value: object, *, available_cards: int, width: int, label: str) -> int:
    mask = _integer(value, label=label, minimum=0)
    if mask >> available_cards or mask.bit_count() != width:
        raise ValueError(f"{label} has the wrong card population or width")
    return mask


def _submasks(mask: int) -> Iterable[int]:
    subset = mask
    while True:
        yield subset
        if subset == 0:
            return
        subset = (subset - 1) & mask


def validate_factorial_weights(
    *,
    common_scale: int = COMMON_SCALE,
    forward: Sequence[int] = FORWARD_LEVEL_WEIGHTS,
    adjoint: Sequence[int] = ADJOINT_LEVEL_WEIGHTS,
) -> None:
    """Reject any scale or level vector not implied by the two recurrences."""

    scale = _integer(common_scale, label="common scale", minimum=1)
    expected_forward = tuple(scale // factorial(SOURCE_CARDS - k) for k in range(5))
    expected_adjoint = tuple(scale // factorial(QUERY_CARDS - k) for k in range(5))
    if any(scale % factorial(SOURCE_CARDS - k) for k in range(5)):
        raise ValueError("common scale does not clear the forward recurrence")
    if any(scale % factorial(QUERY_CARDS - k) for k in range(5)):
        raise ValueError("common scale does not clear the adjoint recurrence")
    if scale != COMMON_SCALE:
        raise ValueError("common scale differs from ADR-0433")
    if tuple(forward) != expected_forward or tuple(adjoint) != expected_adjoint:
        raise ValueError("forward or adjoint factorial weights differ")
    if tuple(forward) == tuple(adjoint):
        raise ValueError("forward and adjoint factorial weights were conflated")


@dataclass(frozen=True, slots=True)
class CapturedOperatorInput:
    """One complete bounded captured-pair operator population."""

    available_cards: int
    source_masks: tuple[int, ...]
    source_rows: tuple[tuple[CapturedPair, ...], ...]
    query_masks: tuple[int, ...]
    query_labels: tuple[int, ...]
    query_covectors: tuple[tuple[CapturedPair, ...], ...]
    query_weights: tuple[CapturedPair, ...]
    reach_feature: int
    source_window: FrozenExponentWindow | None = None
    covector_window: FrozenExponentWindow | None = None
    weight_window: FrozenExponentWindow | None = None


@dataclass(frozen=True, slots=True)
class IntegerLevels:
    """Canonical mask-keyed levels for one factorial-scaled recurrence."""

    maximum_level: int
    rows: tuple[tuple[tuple[int, tuple[int, ...]], ...], ...]

    def level(self, width: int) -> dict[int, tuple[int, ...]]:
        if width not in range(self.maximum_level + 1):
            raise ValueError("requested recurrence level is absent")
        return dict(self.rows[width])


def _sum_rows(rows: Iterable[Sequence[int]], width: int) -> tuple[int, ...]:
    result = [0] * width
    for row in rows:
        if len(row) != width:
            raise ValueError("integer recurrence row width differs")
        for feature, value in enumerate(row):
            result[feature] += int(value)
    return tuple(result)


def build_forward_levels(
    available_cards: int,
    source_rows: Mapping[int, Sequence[int]],
) -> IntegerLevels:
    """Build ``G_k=(6-k)! Z_k`` with additions only."""

    cards = _integer(available_cards, label="available cards", minimum=10)
    expected = set(complete_masks(cards, SOURCE_CARDS))
    if set(source_rows) != expected:
        raise ValueError("forward source occupancy set is incomplete")
    first = next(iter(source_rows.values()))
    width = len(first)
    if width <= 0 or any(len(row) != width for row in source_rows.values()):
        raise ValueError("forward source rows are empty or ragged")
    levels: dict[int, dict[int, tuple[int, ...]]] = {
        SOURCE_CARDS: {
            mask: tuple(int(value) for value in source_rows[mask])
            for mask in expected
        }
    }
    for level in range(SOURCE_CARDS - 1, -1, -1):
        current: dict[int, tuple[int, ...]] = {}
        children = levels[level + 1]
        for mask in complete_masks(cards, level):
            current[mask] = _sum_rows(
                (
                    children[mask | (1 << card)]
                    for card in range(cards)
                    if not mask & (1 << card)
                ),
                width,
            )
        levels[level] = current
    return IntegerLevels(
        maximum_level=SOURCE_CARDS,
        rows=tuple(tuple(sorted(levels[level].items())) for level in range(7)),
    )


def build_adjoint_levels(
    available_cards: int,
    aggregated_query_rows: Mapping[int, Sequence[int]],
) -> IntegerLevels:
    """Build ``H_k=(4-k)! Z_k`` with additions only."""

    cards = _integer(available_cards, label="available cards", minimum=10)
    expected = set(complete_masks(cards, QUERY_CARDS))
    if set(aggregated_query_rows) != expected:
        raise ValueError("adjoint query occupancy set is incomplete")
    first = next(iter(aggregated_query_rows.values()))
    width = len(first)
    if width <= 0 or any(
        len(row) != width for row in aggregated_query_rows.values()
    ):
        raise ValueError("adjoint query rows are empty or ragged")
    levels: dict[int, dict[int, tuple[int, ...]]] = {
        QUERY_CARDS: {
            mask: tuple(int(value) for value in aggregated_query_rows[mask])
            for mask in expected
        }
    }
    for level in range(QUERY_CARDS - 1, -1, -1):
        current: dict[int, tuple[int, ...]] = {}
        children = levels[level + 1]
        for mask in complete_masks(cards, level):
            current[mask] = _sum_rows(
                (
                    children[mask | (1 << card)]
                    for card in range(cards)
                    if not mask & (1 << card)
                ),
                width,
            )
        levels[level] = current
    return IntegerLevels(
        maximum_level=QUERY_CARDS,
        rows=tuple(tuple(sorted(levels[level].items())) for level in range(5)),
    )


@dataclass(frozen=True, slots=True)
class LimbPlan:
    absolute_bound: int
    required_signed_bits: int
    mathematical_limbs: int
    guard_inclusive_limbs: int


def limb_plan(absolute_bound: int) -> LimbPlan:
    bound = _integer(absolute_bound, label="absolute bound", minimum=0)
    bits = 1 if bound == 0 else bound.bit_length() + 1
    mathematical = (bits + 63) // 64
    return LimbPlan(
        absolute_bound=bound,
        required_signed_bits=bits,
        mathematical_limbs=mathematical,
        guard_inclusive_limbs=mathematical + 1,
    )


def require_guard_inclusive_limbs(plan: LimbPlan, allocated_limbs: int) -> None:
    supplied = _integer(allocated_limbs, label="allocated limbs", minimum=1)
    if supplied < plan.guard_inclusive_limbs:
        raise OverflowError("fixed-width allocation omits the required guard limb")


def emulate_signed_integer(value: int, allocated_limbs: int) -> int:
    """Round-trip one signed integer through a fixed two's-complement width."""

    item = _integer(value, label="signed integer")
    limbs = _integer(allocated_limbs, label="allocated limbs", minimum=1)
    bits = 64 * limbs
    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1
    if item < minimum or item > maximum:
        raise OverflowError("signed integer exceeds its fixed-width allocation")
    encoded = item & ((1 << bits) - 1)
    decoded = encoded - (1 << bits) if encoded & (1 << (bits - 1)) else encoded
    if decoded != item:
        raise AssertionError("two's-complement emulation changed an admitted integer")
    return decoded


@dataclass(frozen=True, slots=True)
class OperatorBoundReport:
    available_cards: int
    feature_width: int
    source_maximum: int
    covector_maximum: int
    weight_maximum: int
    forward_table_bounds: tuple[int, ...]
    forward_final_bound: int
    forward_signed_partial_bound: int
    adjoint_table_bounds: tuple[int, ...]
    adjoint_final_bound: int
    adjoint_signed_partial_bound: int
    forward_scalar_bound: int
    adjoint_scalar_bound: int
    reach_scalar_bound: int
    forward_table_plan: LimbPlan
    adjoint_table_plan: LimbPlan
    numerator_plan: LimbPlan
    reach_plan: LimbPlan


def operator_bound_report(
    *,
    available_cards: int,
    feature_width: int,
    source_maximum: int,
    covector_maximum: int,
    weight_maximum: int,
) -> OperatorBoundReport:
    cards = _integer(available_cards, label="available cards", minimum=10)
    width = _integer(feature_width, label="feature width", minimum=1)
    source = _integer(source_maximum, label="source maximum", minimum=0)
    covector = _integer(covector_maximum, label="covector maximum", minimum=0)
    weight = _integer(weight_maximum, label="weight maximum", minimum=0)
    forward_tables = tuple(
        factorial(SOURCE_CARDS - level)
        * comb(cards - level, SOURCE_CARDS - level)
        * source
        for level in range(SOURCE_CARDS + 1)
    )
    forward_final = COMMON_SCALE * comb(cards - QUERY_CARDS, SOURCE_CARDS) * source
    forward_partial = sum(
        comb(QUERY_CARDS, level)
        * FORWARD_LEVEL_WEIGHTS[level]
        * forward_tables[level]
        for level in range(QUERY_CARDS + 1)
    )
    adjoint_tables = tuple(
        QUERY_LABELS
        * factorial(QUERY_CARDS - level)
        * comb(cards - level, QUERY_CARDS - level)
        * covector
        for level in range(QUERY_CARDS + 1)
    )
    adjoint_final = (
        COMMON_SCALE
        * QUERY_LABELS
        * comb(cards - SOURCE_CARDS, QUERY_CARDS)
        * covector
    )
    adjoint_partial = sum(
        comb(SOURCE_CARDS, level)
        * ADJOINT_LEVEL_WEIGHTS[level]
        * adjoint_tables[level]
        for level in range(QUERY_CARDS + 1)
    )
    forward_scalar = (
        comb(cards, QUERY_CARDS)
        * width
        * forward_final
        * QUERY_LABELS
        * covector
    )
    adjoint_scalar = (
        comb(cards, SOURCE_CARDS)
        * width
        * source
        * adjoint_final
    )
    if forward_scalar != adjoint_scalar:
        raise AssertionError("forward and adjoint scalar bounds are not identical")
    reach_scalar = (
        comb(cards, QUERY_CARDS)
        * forward_final
        * QUERY_LABELS
        * weight
    )
    return OperatorBoundReport(
        available_cards=cards,
        feature_width=width,
        source_maximum=source,
        covector_maximum=covector,
        weight_maximum=weight,
        forward_table_bounds=forward_tables,
        forward_final_bound=forward_final,
        forward_signed_partial_bound=forward_partial,
        adjoint_table_bounds=adjoint_tables,
        adjoint_final_bound=adjoint_final,
        adjoint_signed_partial_bound=adjoint_partial,
        forward_scalar_bound=forward_scalar,
        adjoint_scalar_bound=adjoint_scalar,
        reach_scalar_bound=reach_scalar,
        forward_table_plan=limb_plan(max((*forward_tables, forward_partial))),
        adjoint_table_plan=limb_plan(max((*adjoint_tables, adjoint_partial))),
        numerator_plan=limb_plan(forward_scalar),
        reach_plan=limb_plan(reach_scalar),
    )


def _round_nonnegative_ratio(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    comparison = 2 * remainder - denominator
    if comparison > 0 or (comparison == 0 and quotient & 1):
        quotient += 1
    return quotient


def _ratio_floor_binary_exponent(numerator: int, denominator: int) -> int:
    exponent = numerator.bit_length() - denominator.bit_length()
    if exponent >= 0:
        if numerator < (denominator << exponent):
            exponent -= 1
    elif (numerator << -exponent) < denominator:
        exponent -= 1
    return exponent


def _binary64_from_bits(bits: int) -> float:
    return struct.unpack(">d", struct.pack(">Q", bits))[0]


def binary64_bits(value: float) -> int:
    if type(value) is not float:
        raise TypeError("binary64 bit conversion requires a Python float")
    return struct.unpack(">Q", struct.pack(">d", value))[0]


def correctly_rounded_binary64(
    numerator: int,
    denominator: int,
    binary_exponent_shift: int = 0,
) -> float:
    """Round ``numerator/denominator * 2**shift`` to binary64, ties to even."""

    signed = _integer(numerator, label="rounding numerator")
    divisor = _integer(denominator, label="rounding denominator", minimum=1)
    shift = _integer(binary_exponent_shift, label="binary exponent shift")
    if signed == 0:
        return 0.0
    negative = signed < 0
    top = abs(signed)
    bottom = divisor
    if shift >= 0:
        top <<= shift
    else:
        bottom <<= -shift
    exponent = _ratio_floor_binary_exponent(top, bottom)
    sign_bit = int(negative) << 63
    if exponent >= -1022:
        if exponent > 1023:
            raise OverflowError("exact conditional value exceeds finite binary64")
        scale = 52 - exponent
        if scale >= 0:
            significand = _round_nonnegative_ratio(top << scale, bottom)
        else:
            significand = _round_nonnegative_ratio(top, bottom << -scale)
        if significand == 1 << 53:
            significand >>= 1
            exponent += 1
        if exponent > 1023:
            raise OverflowError("rounded conditional value exceeds finite binary64")
        if significand < 1 << 52 or significand >= 1 << 53:
            raise AssertionError("normal binary64 significand is outside its binade")
        exponent_field = exponent + 1023
        fraction_field = significand - (1 << 52)
        return _binary64_from_bits(
            sign_bit | (exponent_field << 52) | fraction_field
        )

    significand = _round_nonnegative_ratio(top << 1074, bottom)
    if significand == 0:
        return _binary64_from_bits(sign_bit)
    if significand > 1 << 52:
        raise AssertionError("subnormal rounding exceeded minimum normal")
    if significand == 1 << 52:
        return _binary64_from_bits(sign_bit | (1 << 52))
    return _binary64_from_bits(sign_bit | significand)


@dataclass(frozen=True, slots=True)
class ObservedOperatorMaxima:
    forward_levels: tuple[int, ...]
    forward_signed_partial: int
    adjoint_levels: tuple[int, ...]
    adjoint_signed_partial: int
    numerator_partial: int
    adjoint_partial: int
    reach_partial: int


@dataclass(frozen=True, slots=True)
class ExactIntegerOperatorResult:
    available_cards: int
    feature_width: int
    source_family_exponent: int
    covector_family_exponent: int
    weight_family_exponent: int
    source_rows: tuple[tuple[int, tuple[int, ...]], ...]
    aggregated_query_covectors: tuple[tuple[int, tuple[int, ...]], ...]
    aggregated_query_weights: tuple[tuple[int, int], ...]
    forward_scaled_rows: tuple[tuple[int, tuple[int, ...]], ...]
    adjoint_scaled_rows: tuple[tuple[int, tuple[int, ...]], ...]
    forward_integer_numerator: int
    adjoint_integer_numerator: int
    literal_scaled_integer_numerator: int
    forward_integer_reach: int
    literal_scaled_integer_reach: int
    conditional_value: float
    conditional_value_bits: int
    exact_conditional_value: Fraction
    bounds: OperatorBoundReport
    observed: ObservedOperatorMaxima


def _aggregate_query_rows(
    query_masks: Sequence[int],
    query_labels: Sequence[int],
    rows: Sequence[Sequence[int]],
    weights: Sequence[int],
    *,
    expected_masks: Sequence[int],
    feature_width: int,
) -> tuple[dict[int, tuple[int, ...]], dict[int, int]]:
    aggregate_rows = {mask: [0] * feature_width for mask in expected_masks}
    aggregate_weights = {mask: 0 for mask in expected_masks}
    labels = {mask: set() for mask in expected_masks}
    for mask, label, row, weight in zip(
        query_masks, query_labels, rows, weights, strict=True
    ):
        if mask not in aggregate_rows:
            raise ValueError("query mask is outside the complete population")
        label_value = _integer(label, label="query label", minimum=0)
        if label_value >= QUERY_LABELS or label_value in labels[mask]:
            raise ValueError("query labels must be unique integers zero through five")
        if len(row) != feature_width:
            raise ValueError("query covector feature width differs")
        for feature, value in enumerate(row):
            aggregate_rows[mask][feature] += int(value)
        aggregate_weights[mask] += int(weight)
        labels[mask].add(label_value)
    expected_labels = set(range(QUERY_LABELS))
    if any(values != expected_labels for values in labels.values()):
        raise ValueError(
            "every query occupancy must contain labels zero through five exactly once"
        )
    return (
        {mask: tuple(values) for mask, values in aggregate_rows.items()},
        aggregate_weights,
    )


def _forward_scaled_rows(
    query_masks: Sequence[int],
    levels: IntegerLevels,
    feature_width: int,
) -> tuple[dict[int, tuple[int, ...]], int]:
    level_maps = tuple(levels.level(level) for level in range(5))
    output: dict[int, tuple[int, ...]] = {}
    maximum_partial = 0
    for query_mask in query_masks:
        values = [0] * feature_width
        for subset in _submasks(query_mask):
            level = subset.bit_count()
            coefficient = FORWARD_LEVEL_WEIGHTS[level]
            sign = -1 if level & 1 else 1
            row = level_maps[level][subset]
            for feature, item in enumerate(row):
                values[feature] += sign * coefficient * item
                maximum_partial = max(maximum_partial, abs(values[feature]))
        if any(value % COMMON_SCALE for value in values):
            raise ArithmeticError("forward scaled output is not divisible by 720")
        output[query_mask] = tuple(values)
    return output, maximum_partial


def _adjoint_scaled_rows(
    source_masks: Sequence[int],
    levels: IntegerLevels,
    feature_width: int,
) -> tuple[dict[int, tuple[int, ...]], int]:
    level_maps = tuple(levels.level(level) for level in range(5))
    output: dict[int, tuple[int, ...]] = {}
    maximum_partial = 0
    for source_mask in source_masks:
        values = [0] * feature_width
        for subset in _submasks(source_mask):
            level = subset.bit_count()
            if level > QUERY_CARDS:
                continue
            coefficient = ADJOINT_LEVEL_WEIGHTS[level]
            sign = -1 if level & 1 else 1
            row = level_maps[level][subset]
            for feature, item in enumerate(row):
                values[feature] += sign * coefficient * item
                maximum_partial = max(maximum_partial, abs(values[feature]))
        if any(value % COMMON_SCALE for value in values):
            raise ArithmeticError("adjoint scaled output is not divisible by 720")
        output[source_mask] = tuple(values)
    return output, maximum_partial


def _maximum_level_value(levels: IntegerLevels) -> tuple[int, ...]:
    result = []
    for level in range(levels.maximum_level + 1):
        maximum = 0
        for _, row in levels.rows[level]:
            maximum = max(maximum, *(abs(value) for value in row))
        result.append(maximum)
    return tuple(result)


def execute_exact_integer_operator(
    captured: CapturedOperatorInput,
) -> ExactIntegerOperatorResult:
    """Evaluate both exact directions, literal authority, bounds, and rounding."""

    validate_factorial_weights()
    cards = _integer(captured.available_cards, label="available cards", minimum=10)
    source_pairs = _normalize_pair_matrix(captured.source_rows, label="source rows")
    covector_pairs = _normalize_pair_matrix(
        captured.query_covectors, label="query covectors"
    )
    feature_width = len(source_pairs[0])
    if len(covector_pairs[0]) != feature_width:
        raise ValueError("source and covector feature widths differ")
    reach_feature = _integer(captured.reach_feature, label="reach feature", minimum=0)
    if reach_feature >= feature_width:
        raise ValueError("reach feature is outside the captured width")
    expected_source_masks = complete_masks(cards, SOURCE_CARDS)
    expected_query_masks = complete_masks(cards, QUERY_CARDS)
    source_masks = tuple(
        _validate_mask(
            value,
            available_cards=cards,
            width=SOURCE_CARDS,
            label="source mask",
        )
        for value in captured.source_masks
    )
    query_masks = tuple(
        _validate_mask(
            value,
            available_cards=cards,
            width=QUERY_CARDS,
            label="query mask",
        )
        for value in captured.query_masks
    )
    if len(source_masks) != len(source_pairs):
        raise ValueError("source mask and row counts differ")
    if len(query_masks) != len(covector_pairs):
        raise ValueError("query mask and covector counts differ")
    if len(captured.query_labels) != len(query_masks):
        raise ValueError("query label count differs")
    if len(captured.query_weights) != len(query_masks):
        raise ValueError("query weight count differs")
    if len(set(source_masks)) != len(source_masks) or set(source_masks) != set(
        expected_source_masks
    ):
        raise ValueError("source masks must contain each complete occupancy once")

    encoded_source = encode_pair_matrix(
        source_pairs,
        label="source rows",
        admitted_window=captured.source_window,
    )
    encoded_covectors = encode_pair_matrix(
        covector_pairs,
        label="query covectors",
        admitted_window=captured.covector_window,
    )
    encoded_weights = encode_pair_vector(
        captured.query_weights,
        label="query weights",
        admitted_window=captured.weight_window,
    )
    source_map = {
        mask: row for mask, row in zip(source_masks, encoded_source.rows, strict=True)
    }
    aggregated_covectors, aggregated_weights = _aggregate_query_rows(
        query_masks,
        captured.query_labels,
        encoded_covectors.rows,
        tuple(row[0] for row in encoded_weights.rows),
        expected_masks=expected_query_masks,
        feature_width=feature_width,
    )

    forward_levels = build_forward_levels(cards, source_map)
    forward_rows, maximum_forward_partial = _forward_scaled_rows(
        expected_query_masks, forward_levels, feature_width
    )
    adjoint_levels = build_adjoint_levels(cards, aggregated_covectors)
    adjoint_rows, maximum_adjoint_partial = _adjoint_scaled_rows(
        expected_source_masks, adjoint_levels, feature_width
    )

    forward_numerator = 0
    maximum_forward_scalar_partial = 0
    forward_reach = 0
    maximum_reach_partial = 0
    for query_mask in expected_query_masks:
        forward = forward_rows[query_mask]
        covector = aggregated_covectors[query_mask]
        for feature in range(feature_width):
            forward_numerator += forward[feature] * covector[feature]
            maximum_forward_scalar_partial = max(
                maximum_forward_scalar_partial, abs(forward_numerator)
            )
        forward_reach += (
            forward[reach_feature] * aggregated_weights[query_mask]
        )
        maximum_reach_partial = max(maximum_reach_partial, abs(forward_reach))

    adjoint_numerator = 0
    maximum_adjoint_scalar_partial = 0
    for source_mask in expected_source_masks:
        source = source_map[source_mask]
        adjoint = adjoint_rows[source_mask]
        for feature in range(feature_width):
            adjoint_numerator += source[feature] * adjoint[feature]
            maximum_adjoint_scalar_partial = max(
                maximum_adjoint_scalar_partial, abs(adjoint_numerator)
            )

    literal_numerator = 0
    literal_reach = 0
    for query_mask in expected_query_masks:
        covector = aggregated_covectors[query_mask]
        weight = aggregated_weights[query_mask]
        for source_mask in expected_source_masks:
            if source_mask & query_mask:
                continue
            source = source_map[source_mask]
            for feature in range(feature_width):
                literal_numerator += source[feature] * covector[feature]
            literal_reach += source[reach_feature] * weight
    literal_scaled_numerator = COMMON_SCALE * literal_numerator
    literal_scaled_reach = COMMON_SCALE * literal_reach
    if not (
        forward_numerator
        == adjoint_numerator
        == literal_scaled_numerator
    ):
        raise ArithmeticError("exact forward, adjoint, or literal numerator differs")
    if forward_reach != literal_scaled_reach:
        raise ArithmeticError("exact forward and literal reach differs")
    if forward_reach <= 0:
        raise ArithmeticError("exact captured reach is not positive")

    bounds = operator_bound_report(
        available_cards=cards,
        feature_width=feature_width,
        source_maximum=encoded_source.maximum_absolute_entry,
        covector_maximum=encoded_covectors.maximum_absolute_entry,
        weight_maximum=encoded_weights.maximum_absolute_entry,
    )
    observed_forward_levels = _maximum_level_value(forward_levels)
    observed_adjoint_levels = _maximum_level_value(adjoint_levels)
    if any(
        observed > bound
        for observed, bound in zip(
            observed_forward_levels, bounds.forward_table_bounds, strict=True
        )
    ):
        raise AssertionError("observed forward recurrence exceeded its bound")
    if any(
        observed > bound
        for observed, bound in zip(
            observed_adjoint_levels, bounds.adjoint_table_bounds, strict=True
        )
    ):
        raise AssertionError("observed adjoint recurrence exceeded its bound")
    if maximum_forward_partial > bounds.forward_signed_partial_bound:
        raise AssertionError("observed forward signed partial exceeded its bound")
    if maximum_adjoint_partial > bounds.adjoint_signed_partial_bound:
        raise AssertionError("observed adjoint signed partial exceeded its bound")
    if (
        maximum_forward_scalar_partial > bounds.forward_scalar_bound
        or maximum_adjoint_scalar_partial > bounds.adjoint_scalar_bound
        or maximum_reach_partial > bounds.reach_scalar_bound
    ):
        raise AssertionError("observed scalar partial exceeded its bound")

    exponent_shift = (
        encoded_covectors.family_exponent - encoded_weights.family_exponent
    )
    conditional = correctly_rounded_binary64(
        forward_numerator,
        forward_reach,
        exponent_shift,
    )
    exact_conditional = Fraction(forward_numerator, forward_reach)
    if exponent_shift >= 0:
        exact_conditional *= 1 << exponent_shift
    else:
        exact_conditional /= 1 << -exponent_shift

    return ExactIntegerOperatorResult(
        available_cards=cards,
        feature_width=feature_width,
        source_family_exponent=encoded_source.family_exponent,
        covector_family_exponent=encoded_covectors.family_exponent,
        weight_family_exponent=encoded_weights.family_exponent,
        source_rows=tuple(sorted(source_map.items())),
        aggregated_query_covectors=tuple(sorted(aggregated_covectors.items())),
        aggregated_query_weights=tuple(sorted(aggregated_weights.items())),
        forward_scaled_rows=tuple(sorted(forward_rows.items())),
        adjoint_scaled_rows=tuple(sorted(adjoint_rows.items())),
        forward_integer_numerator=forward_numerator,
        adjoint_integer_numerator=adjoint_numerator,
        literal_scaled_integer_numerator=literal_scaled_numerator,
        forward_integer_reach=forward_reach,
        literal_scaled_integer_reach=literal_scaled_reach,
        conditional_value=conditional,
        conditional_value_bits=binary64_bits(conditional),
        exact_conditional_value=exact_conditional,
        bounds=bounds,
        observed=ObservedOperatorMaxima(
            forward_levels=observed_forward_levels,
            forward_signed_partial=maximum_forward_partial,
            adjoint_levels=observed_adjoint_levels,
            adjoint_signed_partial=maximum_adjoint_partial,
            numerator_partial=maximum_forward_scalar_partial,
            adjoint_partial=maximum_adjoint_scalar_partial,
            reach_partial=maximum_reach_partial,
        ),
    )


@dataclass(frozen=True, slots=True)
class Literal45WorkModel:
    source_occupancies: int
    query_occupancies: int
    labeled_query_records: int
    forward_rows_levels_0_through_5: int
    adjoint_rows_levels_0_through_4: int
    forward_recurrence_vector_edges: int
    adjoint_recurrence_vector_edges: int
    forward_signed_subset_vector_terms_by_query_occupancy: int
    adjoint_signed_subset_vector_terms_by_source_occupancy: int
    query_label_vector_additions: int
    forward_aggregated_scalar_products: int
    adjoint_dense_scalar_products: int
    source_pairing_visits_per_full_capture: int
    source_rank_to_six_uint8_bytes: int
    source_rank_to_mask_uint64_bytes: int
    query_rank_to_four_uint8_bytes: int
    query_rank_to_mask_uint64_bytes: int
    levels_0_through_5_mask_uint64_bytes: int
    forward_adjacency_uint32_bytes_if_materialized: int
    adjoint_adjacency_uint32_bytes_if_materialized: int


def literal_45_work_model() -> Literal45WorkModel:
    """Return ADR-0433's geometry-only 45-card work ledger."""

    cards = 45
    source = comb(cards, SOURCE_CARDS)
    query = comb(cards, QUERY_CARDS)
    forward_edges = sum(comb(cards, level) * (cards - level) for level in range(6))
    adjoint_edges = sum(comb(cards, level) * (cards - level) for level in range(4))
    return Literal45WorkModel(
        source_occupancies=source,
        query_occupancies=query,
        labeled_query_records=query * QUERY_LABELS,
        forward_rows_levels_0_through_5=sum(comb(cards, level) for level in range(6)),
        adjoint_rows_levels_0_through_4=sum(comb(cards, level) for level in range(5)),
        forward_recurrence_vector_edges=forward_edges,
        adjoint_recurrence_vector_edges=adjoint_edges,
        forward_signed_subset_vector_terms_by_query_occupancy=query * (1 << QUERY_CARDS),
        adjoint_signed_subset_vector_terms_by_source_occupancy=source
        * sum(comb(SOURCE_CARDS, level) for level in range(5)),
        query_label_vector_additions=query * (QUERY_LABELS - 1),
        forward_aggregated_scalar_products=query * 176,
        adjoint_dense_scalar_products=source * 176,
        source_pairing_visits_per_full_capture=source * 90,
        source_rank_to_six_uint8_bytes=source * SOURCE_CARDS,
        source_rank_to_mask_uint64_bytes=source * 8,
        query_rank_to_four_uint8_bytes=query * QUERY_CARDS,
        query_rank_to_mask_uint64_bytes=query * 8,
        levels_0_through_5_mask_uint64_bytes=sum(
            comb(cards, level) for level in range(6)
        )
        * 8,
        forward_adjacency_uint32_bytes_if_materialized=forward_edges * 4,
        adjoint_adjacency_uint32_bytes_if_materialized=adjoint_edges * 4,
    )


@dataclass(frozen=True, slots=True)
class Literal45MemoryModel:
    logical_tile_width: int
    forward_guard_inclusive_limbs: int
    adjoint_guard_inclusive_limbs: int
    query_occupancy_chunk: int
    source_occupancy_chunk: int
    repacked_pair_level_6_bytes: int
    forward_level_5_integer_bytes: int
    forward_pair_plus_level_5_peak_floor_bytes: int
    forward_levels_0_through_5_integer_bytes: int
    forward_query_output_chunk_bytes: int
    adjoint_levels_0_through_4_integer_bytes: int
    streamed_query_pair_chunk_bytes: int
    streamed_adjoint_source_output_bytes: int


def literal_45_memory_model(
    *,
    logical_tile_width: int,
    forward_guard_inclusive_limbs: int,
    adjoint_guard_inclusive_limbs: int,
    query_occupancy_chunk: int,
    source_occupancy_chunk: int,
) -> Literal45MemoryModel:
    """Price only the named representation terms, never a complete fit."""

    width = _integer(logical_tile_width, label="logical tile width", minimum=1)
    if width > 176:
        raise ValueError("logical tile width exceeds the complete feature width")
    forward_limbs = _integer(
        forward_guard_inclusive_limbs, label="forward limbs", minimum=2
    )
    adjoint_limbs = _integer(
        adjoint_guard_inclusive_limbs, label="adjoint limbs", minimum=2
    )
    query_chunk = _integer(
        query_occupancy_chunk, label="query occupancy chunk", minimum=1
    )
    source_chunk = _integer(
        source_occupancy_chunk, label="source occupancy chunk", minimum=1
    )
    if query_chunk > comb(45, QUERY_CARDS) or source_chunk > comb(45, SOURCE_CARDS):
        raise ValueError("literal-45 memory chunk exceeds its occupancy axis")
    pair_level = comb(45, SOURCE_CARDS) * width * 2 * 8
    level_five = comb(45, 5) * width * forward_limbs * 8
    return Literal45MemoryModel(
        logical_tile_width=width,
        forward_guard_inclusive_limbs=forward_limbs,
        adjoint_guard_inclusive_limbs=adjoint_limbs,
        query_occupancy_chunk=query_chunk,
        source_occupancy_chunk=source_chunk,
        repacked_pair_level_6_bytes=pair_level,
        forward_level_5_integer_bytes=level_five,
        forward_pair_plus_level_5_peak_floor_bytes=pair_level + level_five,
        forward_levels_0_through_5_integer_bytes=sum(
            comb(45, level) for level in range(6)
        )
        * width
        * forward_limbs
        * 8,
        forward_query_output_chunk_bytes=query_chunk
        * width
        * forward_limbs
        * 8,
        adjoint_levels_0_through_4_integer_bytes=sum(
            comb(45, level) for level in range(5)
        )
        * width
        * adjoint_limbs
        * 8,
        streamed_query_pair_chunk_bytes=QUERY_LABELS
        * query_chunk
        * width
        * 2
        * 8,
        streamed_adjoint_source_output_bytes=source_chunk
        * width
        * adjoint_limbs
        * 8,
    )


def source_delta_contributions(
    source_mask: int,
    delta_row: Sequence[int],
    *,
    available_cards: int,
) -> tuple[tuple[int, int, tuple[int, ...]], ...]:
    """Return the 57 exact changes to forward levels zero through four."""

    cards = _integer(available_cards, label="available cards", minimum=10)
    mask = _validate_mask(
        source_mask,
        available_cards=cards,
        width=SOURCE_CARDS,
        label="source delta mask",
    )
    row = tuple(int(value) for value in delta_row)
    if not row:
        raise ValueError("source delta row is empty")
    result = []
    for subset in _submasks(mask):
        level = subset.bit_count()
        if level <= QUERY_CARDS:
            multiplier = factorial(SOURCE_CARDS - level)
            result.append(
                (level, subset, tuple(multiplier * value for value in row))
            )
    result.sort(key=lambda item: (item[0], item[1]))
    if len(result) != 57:
        raise AssertionError("source delta did not touch exactly 57 cells")
    return tuple(result)


def query_delta_contributions(
    query_mask: int,
    delta_row: Sequence[int],
    *,
    available_cards: int,
) -> tuple[tuple[int, int, tuple[int, ...]], ...]:
    """Return the 16 exact changes to adjoint levels zero through four."""

    cards = _integer(available_cards, label="available cards", minimum=10)
    mask = _validate_mask(
        query_mask,
        available_cards=cards,
        width=QUERY_CARDS,
        label="query delta mask",
    )
    row = tuple(int(value) for value in delta_row)
    if not row:
        raise ValueError("query delta row is empty")
    result = []
    for subset in _submasks(mask):
        level = subset.bit_count()
        multiplier = factorial(QUERY_CARDS - level)
        result.append((level, subset, tuple(multiplier * value for value in row)))
    result.sort(key=lambda item: (item[0], item[1]))
    if len(result) != 16:
        raise AssertionError("query delta did not touch exactly 16 cells")
    return tuple(result)


@dataclass(frozen=True, slots=True)
class DeltaEpoch:
    topology_digest: str
    opposite_side_digest: str
    family_exponent: int
    guard_inclusive_limbs: int

    def __post_init__(self) -> None:
        for value, label in (
            (self.topology_digest, "topology"),
            (self.opposite_side_digest, "opposite side"),
        ):
            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise ValueError(f"delta {label} digest differs")
        _integer(self.family_exponent, label="delta family exponent")
        _integer(
            self.guard_inclusive_limbs,
            label="delta guard-inclusive limbs",
            minimum=2,
        )


def require_same_delta_epoch(prior: DeltaEpoch, current: DeltaEpoch) -> None:
    if prior != current:
        raise ValueError("exact delta epoch changed; a cold rebuild is required")


__all__ = [
    "ADJOINT_LEVEL_WEIGHTS",
    "COMMON_SCALE",
    "CORRECTION_CONFIG_SHA256",
    "CapturedOperatorInput",
    "CapturedPair",
    "DeltaEpoch",
    "EncodedPairMatrix",
    "ExactIntegerOperatorResult",
    "FORWARD_LEVEL_WEIGHTS",
    "FrozenExponentWindow",
    "IntegerLevels",
    "LimbPlan",
    "Literal45MemoryModel",
    "Literal45WorkModel",
    "OperatorBoundReport",
    "PREREGISTERED_CONFIG_SHA256",
    "binary64_bits",
    "build_adjoint_levels",
    "build_forward_levels",
    "canonical_float_component",
    "canonical_lf_sha256",
    "complete_masks",
    "correctly_rounded_binary64",
    "emulate_signed_integer",
    "encode_pair_matrix",
    "encode_pair_vector",
    "execute_exact_integer_operator",
    "limb_plan",
    "literal_45_memory_model",
    "literal_45_work_model",
    "load_correction_config",
    "load_preregistered_config",
    "load_preregistered_configs",
    "operator_bound_report",
    "query_delta_contributions",
    "require_guard_inclusive_limbs",
    "require_same_delta_epoch",
    "source_delta_contributions",
    "validate_factorial_weights",
    "verify_preregistered_contract",
]
