"""Typed source-local base provenance for ADR-0455.

This source-only module does not discover a production producer by inspecting
values.  A caller must supply an algebraically typed producer, or the audit
returns the honest producer-absent terminal.  Synthetic models exist only for
the reduced exhaustive conformance suite.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
from math import comb, factorial
from pathlib import Path
import re
from typing import Literal, TypeAlias


SOURCE_WIDTH = 6
COMMON_SCALE = 24
BaseClassification = Literal[
    "lattice_decomposable",
    "genuinely_opaque",
    "lattice_plus_sparse_correction",
    "producer_absent",
]
RefreshCadence = Literal[
    "immutable",
    "per_solve_epoch",
    "per_master_epoch",
    "per_pricing_epoch",
]
ProducerScope = Literal["synthetic_control", "production"]


def _plain_integer(value: object, *, label: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be a plain integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} lies below its minimum")
    return value


def _digest(value: str, *, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{label} must be one lowercase SHA-256 digest")
    return value


def _relative_source(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or Path(value).is_absolute()
        or ".." in Path(value).parts
    ):
        raise ValueError("base producer source path must be repository-relative")
    return value


def _mask(cards: tuple[int, ...]) -> int:
    value = 0
    for card in cards:
        value |= 1 << card
    return value


def _colex(mask: int) -> int:
    cards = tuple(card for card in range(mask.bit_length()) if mask & (1 << card))
    return sum(comb(card, index + 1) for index, card in enumerate(cards))


def complete_masks(available_cards: int, width: int) -> tuple[int, ...]:
    cards = _plain_integer(available_cards, label="base available cards", minimum=1)
    rank = _plain_integer(width, label="base mask width", minimum=0)
    if rank > cards:
        raise ValueError("base mask width exceeds available cards")
    return tuple(
        sorted(
            (_mask(row) for row in combinations(range(cards), rank)),
            key=_colex,
        )
    )


@dataclass(frozen=True, slots=True)
class HSeedEpoch:
    digest: str

    def __post_init__(self) -> None:
        _digest(self.digest, label="H seed epoch")


@dataclass(frozen=True, slots=True)
class PricingVectorEpoch:
    digest: str

    def __post_init__(self) -> None:
        _digest(self.digest, label="pricing-vector epoch")


@dataclass(frozen=True, slots=True)
class BaseStructuralEpoch:
    digest: str

    def __post_init__(self) -> None:
        _digest(self.digest, label="base structural epoch")


@dataclass(frozen=True, slots=True)
class BaseCorrectionEpoch:
    digest: str

    def __post_init__(self) -> None:
        _digest(self.digest, label="base correction epoch")


@dataclass(frozen=True, slots=True)
class MasterSupportEpoch:
    digest: str

    def __post_init__(self) -> None:
        _digest(self.digest, label="master-support epoch")


@dataclass(frozen=True, slots=True)
class ProductionBaseAdmission:
    component_exponent_minimum: int
    component_exponent_maximum: int
    semantic_absolute_bound: int
    mathematical_limbs: int
    guard_inclusive_limbs: int

    def __post_init__(self) -> None:
        lower = _plain_integer(
            self.component_exponent_minimum,
            label="base component exponent minimum",
        )
        upper = _plain_integer(
            self.component_exponent_maximum,
            label="base component exponent maximum",
        )
        bound = _plain_integer(
            self.semantic_absolute_bound,
            label="base semantic absolute bound",
            minimum=0,
        )
        mathematical = _plain_integer(
            self.mathematical_limbs,
            label="base mathematical limbs",
            minimum=1,
        )
        guard = _plain_integer(
            self.guard_inclusive_limbs,
            label="base guard-inclusive limbs",
            minimum=2,
        )
        required_bits = 1 if bound == 0 else bound.bit_length() + 1
        expected_mathematical = (required_bits + 63) // 64
        if lower > upper:
            raise ValueError("base component exponent window is reversed")
        if mathematical != expected_mathematical or guard != mathematical + 1:
            raise ValueError("base limb admission differs from its semantic bound")


@dataclass(frozen=True, slots=True)
class ProducerIdentity:
    source_relative_path: str
    source_sha256: str
    semantic_sha256: str
    refresh_cadence: RefreshCadence
    scope: ProducerScope
    admission: ProductionBaseAdmission | None

    def __post_init__(self) -> None:
        _relative_source(self.source_relative_path)
        _digest(self.source_sha256, label="base producer source")
        _digest(self.semantic_sha256, label="base producer semantics")
        if self.refresh_cadence not in (
            "immutable",
            "per_solve_epoch",
            "per_master_epoch",
            "per_pricing_epoch",
        ):
            raise ValueError("base refresh cadence differs")
        if self.scope not in ("synthetic_control", "production"):
            raise ValueError("base producer scope differs")
        if self.scope == "production" and not isinstance(
            self.admission, ProductionBaseAdmission
        ):
            raise ValueError("production base producer lacks numerical admission")
        if self.scope == "synthetic_control" and self.admission is not None:
            raise ValueError("synthetic base envelope cannot become admission")


def _check_production_bound(
    identity: ProducerIdentity,
    values: Iterable[int],
) -> None:
    if identity.scope != "production":
        return
    admission = identity.admission
    if admission is None:
        raise AssertionError("validated production identity omitted its admission")
    if max((abs(value) for value in values), default=0) > admission.semantic_absolute_bound:
        raise ValueError("production base exceeds its admitted semantic bound")


@dataclass(frozen=True, slots=True)
class LatticeComponent:
    available_cards: int
    maximum_seed_rank: int
    output_scale: int
    seed_weights: tuple[int, ...]
    seed_values: tuple[tuple[int, int], ...]
    structural_epoch: BaseStructuralEpoch

    def __post_init__(self) -> None:
        cards = _plain_integer(
            self.available_cards, label="lattice available cards", minimum=SOURCE_WIDTH
        )
        maximum = _plain_integer(
            self.maximum_seed_rank, label="lattice maximum seed rank", minimum=0
        )
        scale = _plain_integer(self.output_scale, label="lattice scale", minimum=1)
        if maximum > SOURCE_WIDTH or len(self.seed_weights) != maximum + 1:
            raise ValueError("lattice seed rank or weight width differs")
        if any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in self.seed_weights
        ):
            raise TypeError("lattice seed weights must be exact integers")
        expected = tuple(
            mask
            for rank in range(maximum + 1)
            for mask in complete_masks(cards, rank)
        )
        values = dict(self.seed_values)
        if (
            len(values) != len(self.seed_values)
            or tuple(values) != expected
            or any(
                isinstance(value, bool) or not isinstance(value, int)
                for value in values.values()
            )
        ):
            raise ValueError("lattice seed domain is incomplete or reordered")
        for rank, weight in enumerate(self.seed_weights):
            if weight * factorial(SOURCE_WIDTH - rank) % scale:
                raise ValueError("lattice seed cannot reconstruct an exact source value")
        if not isinstance(self.structural_epoch, BaseStructuralEpoch):
            raise TypeError("lattice structural epoch has the wrong semantic type")

    def direct_values(self) -> tuple[tuple[int, int], ...]:
        seeds = dict(self.seed_values)
        output = []
        for source in complete_masks(self.available_cards, SOURCE_WIDTH):
            numerator = 0
            subset = source
            while True:
                rank = subset.bit_count()
                if rank <= self.maximum_seed_rank:
                    numerator += (
                        self.seed_weights[rank]
                        * factorial(SOURCE_WIDTH - rank)
                        * seeds[subset]
                    )
                if subset == 0:
                    break
                subset = (subset - 1) & source
            if numerator % self.output_scale:
                raise ArithmeticError("lattice base output is not exactly divisible")
            output.append((source, numerator // self.output_scale))
        return tuple(output)


@dataclass(frozen=True, slots=True)
class LatticeBaseProducer:
    identity: ProducerIdentity
    component: LatticeComponent

    def __post_init__(self) -> None:
        _check_production_bound(
            self.identity,
            (value for _, value in self.component.direct_values()),
        )


@dataclass(frozen=True, slots=True)
class OpaqueBaseProducer:
    identity: ProducerIdentity
    available_cards: int
    source_values: tuple[tuple[int, int], ...]
    structural_epoch: BaseStructuralEpoch

    def __post_init__(self) -> None:
        cards = _plain_integer(
            self.available_cards, label="opaque available cards", minimum=SOURCE_WIDTH
        )
        expected = complete_masks(cards, SOURCE_WIDTH)
        values = dict(self.source_values)
        if (
            len(values) != len(self.source_values)
            or tuple(values) != expected
            or any(
                isinstance(value, bool) or not isinstance(value, int)
                for value in values.values()
            )
        ):
            raise ValueError("opaque source base is incomplete or reordered")
        if not isinstance(self.structural_epoch, BaseStructuralEpoch):
            raise TypeError("opaque base epoch has the wrong semantic type")
        _check_production_bound(self.identity, values.values())


@dataclass(frozen=True, slots=True)
class LatticeSparseBaseProducer:
    identity: ProducerIdentity
    component: LatticeComponent
    corrections: tuple[tuple[int, int], ...]
    master_support: tuple[int, ...]
    correction_epoch: BaseCorrectionEpoch
    master_support_epoch: MasterSupportEpoch

    def __post_init__(self) -> None:
        sources = set(complete_masks(self.component.available_cards, SOURCE_WIDTH))
        support = tuple(self.master_support)
        corrections = dict(self.corrections)
        if (
            not support
            or len(set(support)) != len(support)
            or tuple(sorted(support, key=_colex)) != support
            or any(mask not in sources for mask in support)
        ):
            raise ValueError("mixed base master support differs")
        if (
            len(corrections) != len(self.corrections)
            or tuple(corrections) != support
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value == 0
                for value in corrections.values()
            )
        ):
            raise ValueError("mixed base sparse correction support or value differs")
        if not isinstance(self.correction_epoch, BaseCorrectionEpoch):
            raise TypeError("mixed base correction epoch has the wrong semantic type")
        if not isinstance(self.master_support_epoch, MasterSupportEpoch):
            raise TypeError("mixed base support epoch has the wrong semantic type")
        structural_values = dict(self.component.direct_values())
        for source, correction in self.corrections:
            structural_values[source] += correction
        _check_production_bound(self.identity, structural_values.values())


BaseProducer: TypeAlias = (
    LatticeBaseProducer | OpaqueBaseProducer | LatticeSparseBaseProducer
)


@dataclass(frozen=True, slots=True)
class BaseAudit:
    classification: BaseClassification
    producer_identity: ProducerIdentity | None
    structural_epoch: BaseStructuralEpoch | None
    correction_epoch: BaseCorrectionEpoch | None
    master_support_epoch: MasterSupportEpoch | None
    refresh_cadence: RefreshCadence | None
    production_admission: ProductionBaseAdmission | None
    terminal: str


def audit_base_producer(producer: BaseProducer | None) -> BaseAudit:
    if producer is None:
        return BaseAudit(
            "producer_absent",
            None,
            None,
            None,
            None,
            None,
            None,
            "base_producer_unavailable_no_bakeoff_selection",
        )
    if isinstance(producer, LatticeSparseBaseProducer):
        return BaseAudit(
            "lattice_plus_sparse_correction",
            producer.identity,
            producer.component.structural_epoch,
            producer.correction_epoch,
            producer.master_support_epoch,
            producer.identity.refresh_cadence,
            producer.identity.admission,
            "typed_base_producer",
        )
    if isinstance(producer, LatticeBaseProducer):
        return BaseAudit(
            "lattice_decomposable",
            producer.identity,
            producer.component.structural_epoch,
            None,
            None,
            producer.identity.refresh_cadence,
            producer.identity.admission,
            "typed_base_producer",
        )
    if isinstance(producer, OpaqueBaseProducer):
        return BaseAudit(
            "genuinely_opaque",
            producer.identity,
            producer.structural_epoch,
            None,
            None,
            producer.identity.refresh_cadence,
            producer.identity.admission,
            "typed_base_producer",
        )
    raise TypeError("base producer must use one registered semantic type")


def base_values(producer: BaseProducer) -> tuple[tuple[int, int], ...]:
    audit = audit_base_producer(producer)
    if audit.classification == "lattice_decomposable":
        assert isinstance(producer, LatticeBaseProducer)
        return producer.component.direct_values()
    if audit.classification == "genuinely_opaque":
        assert isinstance(producer, OpaqueBaseProducer)
        return producer.source_values
    assert isinstance(producer, LatticeSparseBaseProducer)
    values = dict(producer.component.direct_values())
    for source, correction in producer.corrections:
        values[source] += correction
    return tuple((source, values[source]) for source in values)


def _synthetic_digest(label: str) -> str:
    return sha256(("adr0455|" + label).encode("ascii")).hexdigest()


def _synthetic_identity(mode: str) -> ProducerIdentity:
    return ProducerIdentity(
        source_relative_path="synthetic/adr0455-control-only",
        source_sha256=_synthetic_digest(mode + "|source"),
        semantic_sha256=_synthetic_digest(mode + "|semantics"),
        refresh_cadence="per_master_epoch",
        scope="synthetic_control",
        admission=None,
    )


def _synthetic_component(available_cards: int, mode: str) -> LatticeComponent:
    values = []
    for rank in range(3):
        for mask in complete_masks(available_cards, rank):
            framed = f"adr0455|{mode}|beta|{available_cards}|{rank}|{mask}".encode("ascii")
            value = int.from_bytes(sha256(framed).digest()[:4], "big") % 97 - 48
            values.append((mask, value))
    return LatticeComponent(
        available_cards=available_cards,
        maximum_seed_rank=2,
        output_scale=COMMON_SCALE,
        seed_weights=(2, -3, 5),
        seed_values=tuple(values),
        structural_epoch=BaseStructuralEpoch(_synthetic_digest(mode + "|base-epoch")),
    )


def make_synthetic_base(
    available_cards: int,
    mode: Literal[
        "exact_lattice_base",
        "opaque_per_source_base",
        "lattice_plus_exact_sparse_master_support_correction",
    ],
) -> BaseProducer:
    cards = _plain_integer(
        available_cards, label="synthetic base cards", minimum=SOURCE_WIDTH
    )
    identity = _synthetic_identity(mode)
    if mode == "exact_lattice_base":
        return LatticeBaseProducer(identity, _synthetic_component(cards, mode))
    sources = complete_masks(cards, SOURCE_WIDTH)
    if mode == "opaque_per_source_base":
        rows = []
        for source in sources:
            framed = f"adr0455|opaque|{cards}|{source}".encode("ascii")
            rows.append((source, int.from_bytes(sha256(framed).digest()[:4], "big") % 401 - 200))
        return OpaqueBaseProducer(
            identity,
            cards,
            tuple(rows),
            BaseStructuralEpoch(_synthetic_digest(mode + "|base-epoch")),
        )
    if mode == "lattice_plus_exact_sparse_master_support_correction":
        support = tuple(sorted((sources[0], sources[len(sources) // 2], sources[-1]), key=_colex))
        corrections = tuple(zip(support, (101, -203, 307), strict=True))
        return LatticeSparseBaseProducer(
            identity,
            _synthetic_component(cards, mode),
            corrections,
            support,
            BaseCorrectionEpoch(_synthetic_digest(mode + "|correction-epoch")),
            MasterSupportEpoch(_synthetic_digest(mode + "|support-epoch")),
        )
    raise ValueError("synthetic base mode differs from the frozen family")


__all__ = [
    "BaseAudit",
    "BaseClassification",
    "BaseCorrectionEpoch",
    "BaseProducer",
    "BaseStructuralEpoch",
    "COMMON_SCALE",
    "HSeedEpoch",
    "LatticeBaseProducer",
    "LatticeComponent",
    "LatticeSparseBaseProducer",
    "MasterSupportEpoch",
    "OpaqueBaseProducer",
    "PricingVectorEpoch",
    "ProducerIdentity",
    "ProductionBaseAdmission",
    "audit_base_producer",
    "base_values",
    "complete_masks",
    "make_synthetic_base",
]
