"""Source-only exact global-separation topologies for ADR-0455.

The module implements reduced-domain algebra and logical work receipts only.
It contains no result owner, NumPy, CuPy, CUDA, timing, literal-45 numerical
input, resolver, or action path.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from hashlib import sha256
import heapq
from math import comb, factorial
from pathlib import Path
import json
from typing import Literal

from pontius import legal_river_quotient_base_provenance as base
from pontius import legal_river_quotient_selective_certified_separation as prefix


ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-global-separation-topology-bakeoff-v1.json"
)
CONFIG_SHA256 = "3d023b59a5e28e20e1af16ff3c809e9ed8a2a1c23a5c56dcca81fd6181a64da7"
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_global_separation_topology_bakeoff_v1.jsonl"
)
PREREGISTRATION_COMMIT = "eca94fdba71b3c820b09255cd4aa4579d624972a"
SOURCE_WIDTH = 6
SUBSET_MAXIMUM = 4
FEATURE_WIDTH = 176
OUTPUT_SCALE = 24
PRICE_COEFFICIENTS = (30, -120, 360, -720, 720)
H_SEED_WEIGHTS = (1, -24, 360, -2880, 8640)
DOMAINS = (10, 12)
LEGACY_FAMILIES = prefix.FAMILIES
BASE_FAMILIES = (
    "exact_lattice_base",
    "opaque_per_source_base",
    "lattice_plus_exact_sparse_master_support_correction",
)
ARM_NAMES = (
    "contract_first_direct_57_scan",
    "rank_truncated_zeta",
    "adr0454_prefix_branch_and_bound",
    "frozen_prefix_then_zeta_hybrid",
)
Mode = Literal["positive_witness", "prove_none", "exact_argmax_full_ties"]


def _canonical_lf(raw: bytes) -> bytes:
    output = bytearray()
    cursor = 0
    while cursor < len(raw):
        if raw[cursor : cursor + 2] == bytes((13, 10)):
            output.append(10)
            cursor += 2
        else:
            output.append(raw[cursor])
            cursor += 1
    return bytes(output)


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise FileNotFoundError("topology dependency is absent")
    return sha256(_canonical_lf(path.read_bytes())).hexdigest()


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(f"duplicate topology JSON key: {key}")
        output[key] = value
    return output


def _object(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"topology {label} must be an object")
    return value


def load_preregistered_config() -> dict[str, object]:
    path = ROOT / CONFIG_RELATIVE_PATH
    raw = path.read_bytes()
    if len(raw) > 1_048_576 or sha256(_canonical_lf(raw)).hexdigest() != CONFIG_SHA256:
        raise ValueError("topology config identity differs")
    parsed = json.loads(raw, object_pairs_hook=_unique_object)
    if (
        not isinstance(parsed, dict)
        or parsed.get("schema_version")
        != "legal-river-quotient-global-separation-topology-bakeoff-config-v1"
        or parsed.get("evidence_stage")
        != "preregistered_after_adr0454_before_base_producer_source_topology_source_result_or_value"
    ):
        raise ValueError("topology config schema differs")
    return parsed


def verify_preregistered_contract() -> None:
    parsed = load_preregistered_config()
    parents = _object(parsed.get("parents"), label="parents")
    for path_key, digest_key in (
        ("adr0454_relative_path", "adr0454_canonical_lf_sha256"),
        ("selective_config_relative_path", "selective_config_canonical_lf_sha256"),
        ("selective_source_relative_path", "selective_source_canonical_lf_sha256"),
        ("exact_integer_operator_relative_path", "exact_integer_operator_canonical_lf_sha256"),
        ("fixed_width_work_relative_path", "fixed_width_work_canonical_lf_sha256"),
        ("actual_context_bridge_relative_path", "actual_context_bridge_canonical_lf_sha256"),
    ):
        relative = parents.get(path_key)
        if (
            not isinstance(relative, str)
            or canonical_lf_sha256(ROOT / relative) != parents.get(digest_key)
        ):
            raise ValueError(f"topology parent differs: {path_key}")
    if parents.get("adr0454_source_commit") != "6d38772210fb54a67cad8c04441fbbdcec3a29f6":
        raise ValueError("topology ADR-0454 commit differs")
    price = _object(parsed.get("exact_price_contract"), label="price")
    zeta = _object(parsed.get("zeta_circuit"), label="zeta")
    scope = _object(parsed.get("scope"), label="scope")
    literal_sources = comb(45, SOURCE_WIDTH)
    literal_subsets = sum(comb(45, rank) for rank in range(SUBSET_MAXIMUM + 1))
    if (
        price.get("level_coefficients_zero_through_four") != list(PRICE_COEFFICIENTS)
        or price.get("h_scalar_contractions_at_literal_45")
        != literal_subsets * FEATURE_WIDTH
        or zeta.get("seed_weights_zero_through_four") != list(H_SEED_WEIGHTS)
        or zeta.get("common_output_scale") != OUTPUT_SCALE
        or scope.get("source_card_width") != SOURCE_WIDTH
        or scope.get("subset_level_maximum") != SUBSET_MAXIMUM
        or scope.get("feature_width") != FEATURE_WIDTH
        or scope.get("source_domain_at_literal_45") != literal_sources
        or scope.get("subset_scalar_domain_at_literal_45") != literal_subsets
    ):
        raise ValueError("topology exact constants differ")
    if any(
        H_SEED_WEIGHTS[level] * factorial(SOURCE_WIDTH - level)
        != OUTPUT_SCALE * PRICE_COEFFICIENTS[level]
        for level in range(SUBSET_MAXIMUM + 1)
    ):
        raise ArithmeticError("topology seed identity differs")
    expected_edges = tuple(level * comb(45, level) for level in range(1, 7))
    if (
        tuple(zeta.get("literal_45_cover_edges_by_child_rank_one_through_six", ()))
        != expected_edges
        or zeta.get("literal_45_total_cover_edges") != sum(expected_edges)
        or zeta.get("literal_45_direct_57_subset_incidences") != literal_sources * 57
    ):
        raise ValueError("topology literal-45 work identities differ")
    arms = tuple(
        row.get("arm")
        for row in parsed.get("topology_arms", ())
        if isinstance(row, Mapping)
    )
    if arms != ARM_NAMES:
        raise ValueError("topology arm order differs")
    audit = _object(parsed.get("base_producer_audit"), label="base audit")
    if (
        audit.get("current_repository_state") != "producer_absent"
        or tuple(audit.get("exclusive_classifications", ()))
        != (
            "lattice_decomposable",
            "genuinely_opaque",
            "lattice_plus_sparse_correction",
            "producer_absent",
        )
    ):
        raise ValueError("topology base answer type differs")
    frequency = _object(parsed.get("certificate_frequency"), label="frequency")
    if (
        frequency.get("global_closures_per_action") is not None
        or frequency.get("positive_witness_calls_per_action") is not None
    ):
        raise ValueError("topology action denominator was invented")
    identity = _object(parsed.get("prospective_identity"), label="identity")
    expected = {
        "base_audit_source_relative_path": "src/pontius/legal_river_quotient_base_provenance.py",
        "topology_source_relative_path": (
            "src/pontius/legal_river_quotient_global_separation_topologies.py"
        ),
        "controls_relative_path": "tests/test_legal_river_quotient_global_separation_topologies.py",
        "result_relative_path": RESULT_RELATIVE_PATH,
    }
    if any(identity.get(key) != value for key, value in expected.items()):
        raise ValueError("topology prospective identity differs")


def _epoch(label: str, cls: type[object]) -> object:
    digest = sha256(("adr0455|" + label).encode("ascii")).hexdigest()
    return cls(digest)


def _legacy_opaque_producer(instance: prefix.PriceInstance) -> base.OpaqueBaseProducer:
    label = f"legacy|{instance.available_cards}|{instance.family}"
    identity = base.ProducerIdentity(
        source_relative_path="synthetic/adr0453-family-control-only",
        source_sha256=sha256((label + "|source").encode("ascii")).hexdigest(),
        semantic_sha256=sha256((label + "|semantics").encode("ascii")).hexdigest(),
        refresh_cadence="per_master_epoch",
        scope="synthetic_control",
        admission=None,
    )
    structural = _epoch(label + "|base", base.BaseStructuralEpoch)
    assert isinstance(structural, base.BaseStructuralEpoch)
    return base.OpaqueBaseProducer(
        identity,
        instance.available_cards,
        instance.source_bases,
        structural,
    )


@dataclass(frozen=True, slots=True)
class ExactPriceInput:
    available_cards: int
    family: str
    h_scalars: tuple[tuple[int, int], ...]
    base_producer: base.BaseProducer
    h_epoch: base.HSeedEpoch
    pricing_epoch: base.PricingVectorEpoch

    def __post_init__(self) -> None:
        if self.available_cards not in DOMAINS:
            raise ValueError("topology input is outside the reduced domains")
        if not isinstance(self.family, str) or not self.family:
            raise ValueError("topology input family differs")
        expected = tuple(
            mask
            for level in range(SUBSET_MAXIMUM + 1)
            for mask in prefix.complete_masks(self.available_cards, level)
        )
        rows = dict(self.h_scalars)
        if (
            len(rows) != len(self.h_scalars)
            or tuple(rows) != expected
            or any(isinstance(value, bool) or not isinstance(value, int) for value in rows.values())
        ):
            raise ValueError("topology H scalar domain is incomplete or reordered")
        producer_values = base.base_values(self.base_producer)
        if tuple(mask for mask, _ in producer_values) != prefix.complete_masks(
            self.available_cards, SOURCE_WIDTH
        ):
            raise ValueError("topology base producer domain differs")
        producer_cards = (
            self.base_producer.component.available_cards
            if isinstance(
                self.base_producer,
                (base.LatticeBaseProducer, base.LatticeSparseBaseProducer),
            )
            else self.base_producer.available_cards
        )
        if producer_cards != self.available_cards:
            raise ValueError("topology base and H card domains differ")
        if not isinstance(self.h_epoch, base.HSeedEpoch):
            raise TypeError("topology H epoch has the wrong semantic type")
        if not isinstance(self.pricing_epoch, base.PricingVectorEpoch):
            raise TypeError("topology pricing epoch has the wrong semantic type")


def _ordered_pairs_sha256(rows: Sequence[tuple[int, int]]) -> str:
    return _json_sha256(rows)


def _json_sha256(value: object) -> str:
    return sha256(
        json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class PreparedHArtifact:
    available_cards: int
    scalar_sha256: str
    h_epoch: base.HSeedEpoch
    pricing_epoch: base.PricingVectorEpoch

    def assert_fresh(self, value: ExactPriceInput) -> None:
        if not isinstance(value, ExactPriceInput):
            raise TypeError("prepared H artifact received an untyped input")
        if (
            self.available_cards != value.available_cards
            or self.scalar_sha256 != _ordered_pairs_sha256(value.h_scalars)
            or self.h_epoch != value.h_epoch
            or self.pricing_epoch != value.pricing_epoch
        ):
            raise ValueError("stale prepared H artifact")


@dataclass(frozen=True, slots=True)
class PreparedBaseArtifact:
    classification: base.BaseClassification
    producer_identity: base.ProducerIdentity
    structural_payload_sha256: str
    structural_epoch: base.BaseStructuralEpoch
    correction_payload_sha256: str | None
    correction_epoch: base.BaseCorrectionEpoch | None
    support_payload_sha256: str | None
    master_support_epoch: base.MasterSupportEpoch | None

    def assert_structural_fresh(self, producer: base.BaseProducer) -> None:
        observed = prepare_base_artifact(producer)
        if (
            self.classification != observed.classification
            or self.producer_identity != observed.producer_identity
            or self.structural_payload_sha256 != observed.structural_payload_sha256
            or self.structural_epoch != observed.structural_epoch
        ):
            raise ValueError("stale prepared structural-base artifact")

    def assert_correction_fresh(self, producer: base.BaseProducer) -> None:
        observed = prepare_base_artifact(producer)
        if (
            self.correction_payload_sha256 != observed.correction_payload_sha256
            or self.correction_epoch != observed.correction_epoch
            or self.support_payload_sha256 != observed.support_payload_sha256
            or self.master_support_epoch != observed.master_support_epoch
        ):
            raise ValueError("stale prepared base-correction artifact")

    def assert_fresh(self, producer: base.BaseProducer) -> None:
        self.assert_structural_fresh(producer)
        self.assert_correction_fresh(producer)


def prepare_h_artifact(value: ExactPriceInput) -> PreparedHArtifact:
    if not isinstance(value, ExactPriceInput):
        raise TypeError("prepared H artifact requires a typed price input")
    return PreparedHArtifact(
        value.available_cards,
        _ordered_pairs_sha256(value.h_scalars),
        value.h_epoch,
        value.pricing_epoch,
    )


def prepare_base_artifact(producer: base.BaseProducer) -> PreparedBaseArtifact:
    audit = base.audit_base_producer(producer)
    if audit.producer_identity is None or audit.structural_epoch is None:
        raise ValueError("a producer-absent audit cannot prepare a base artifact")
    if isinstance(producer, base.LatticeBaseProducer):
        structural_payload: object = {
            "available_cards": producer.component.available_cards,
            "maximum_seed_rank": producer.component.maximum_seed_rank,
            "output_scale": producer.component.output_scale,
            "seed_weights": producer.component.seed_weights,
            "seed_values": producer.component.seed_values,
        }
        correction_rows: tuple[tuple[int, int], ...] | None = None
        support_rows: tuple[int, ...] | None = None
    elif isinstance(producer, base.OpaqueBaseProducer):
        structural_payload = {
            "available_cards": producer.available_cards,
            "source_values": producer.source_values,
        }
        correction_rows = None
        support_rows = None
    else:
        structural_payload = {
            "available_cards": producer.component.available_cards,
            "maximum_seed_rank": producer.component.maximum_seed_rank,
            "output_scale": producer.component.output_scale,
            "seed_weights": producer.component.seed_weights,
            "seed_values": producer.component.seed_values,
        }
        correction_rows = producer.corrections
        support_rows = producer.master_support
    return PreparedBaseArtifact(
        audit.classification,
        audit.producer_identity,
        _json_sha256(structural_payload),
        audit.structural_epoch,
        None if correction_rows is None else _ordered_pairs_sha256(correction_rows),
        audit.correction_epoch,
        None if support_rows is None else _json_sha256(support_rows),
        audit.master_support_epoch,
    )


@dataclass(frozen=True, slots=True)
class PreparedPrefixArtifact:
    compiled: prefix.CompiledSeparation
    h: PreparedHArtifact
    base: PreparedBaseArtifact

    def assert_fresh(self, value: ExactPriceInput) -> None:
        self.h.assert_fresh(value)
        self.base.assert_fresh(value.base_producer)
        if self.compiled.instance != as_prefix_instance(value):
            raise ValueError("stale prepared prefix artifact")


def prepare_prefix_artifact(value: ExactPriceInput) -> PreparedPrefixArtifact:
    if not isinstance(value, ExactPriceInput):
        raise TypeError("prepared prefix artifact requires a typed price input")
    return PreparedPrefixArtifact(
        prefix.compile_separation(as_prefix_instance(value)),
        prepare_h_artifact(value),
        prepare_base_artifact(value.base_producer),
    )


def make_control_input(available_cards: int, family: str) -> ExactPriceInput:
    if available_cards not in DOMAINS:
        raise ValueError("topology control domain differs")
    if family in LEGACY_FAMILIES:
        instance = prefix.make_instance(available_cards, family)
        producer: base.BaseProducer = _legacy_opaque_producer(instance)
        scalars = instance.subset_scalars
    elif family in BASE_FAMILIES:
        producer = base.make_synthetic_base(available_cards, family)  # type: ignore[arg-type]
        scalars = prefix.make_instance(
            available_cards, "deterministic_mixed_hash"
        ).subset_scalars
    else:
        raise ValueError("topology control family differs")
    h_epoch = _epoch(
        f"{available_cards}|{family}|H", base.HSeedEpoch
    )
    pricing_epoch = _epoch(
        f"{available_cards}|{family}|pricing", base.PricingVectorEpoch
    )
    assert isinstance(h_epoch, base.HSeedEpoch)
    assert isinstance(pricing_epoch, base.PricingVectorEpoch)
    return ExactPriceInput(
        available_cards,
        family,
        scalars,
        producer,
        h_epoch,
        pricing_epoch,
    )


def as_prefix_instance(value: ExactPriceInput) -> prefix.PriceInstance:
    if not isinstance(value, ExactPriceInput):
        raise TypeError("topology price input differs")
    return prefix.PriceInstance(
        value.available_cards,
        value.family,
        base.base_values(value.base_producer),
        value.h_scalars,
    )


def exact_price(value: ExactPriceInput, source_mask: int) -> int:
    return prefix.selective_price(as_prefix_instance(value), source_mask)[0]


def direct_price_map(value: ExactPriceInput) -> tuple[tuple[int, int], ...]:
    instance = as_prefix_instance(value)
    return tuple(
        (source, prefix.selective_price(instance, source)[0])
        for source in prefix.complete_masks(value.available_cards, SOURCE_WIDTH)
    )


def _required_width(bound: int) -> tuple[int, int, int]:
    if isinstance(bound, bool) or not isinstance(bound, int) or bound < 0:
        raise ValueError("topology width bound must be a nonnegative integer")
    bits = 1 if bound == 0 else bound.bit_length() + 1
    mathematical = (bits + 63) // 64
    return bits, mathematical, mathematical + 1


def _rank_component_bound(
    rank: int,
    maximum_seed_rank: int,
    seed_weights: Sequence[int],
    seed_maxima: Sequence[int],
) -> int:
    return sum(
        comb(rank, level)
        * factorial(rank - level)
        * abs(seed_weights[level])
        * seed_maxima[level]
        for level in range(min(rank, maximum_seed_rank) + 1)
    )


@dataclass(frozen=True, slots=True)
class RankWidthReceipt:
    rank: int
    nodes: int
    cover_edges: int
    h_seed_reads: int
    base_seed_reads: int
    h_absolute_bound: int
    base_absolute_bound: int
    combined_absolute_bound: int
    observed_maximum_absolute: int
    h_required_signed_bits: int
    h_mathematical_limbs: int
    h_guard_inclusive_limbs: int
    base_required_signed_bits: int
    base_mathematical_limbs: int
    base_guard_inclusive_limbs: int
    required_signed_bits: int
    mathematical_limbs: int
    guard_inclusive_limbs: int


@dataclass(frozen=True, slots=True)
class ZetaWorkReceipt:
    rank_receipts: tuple[RankWidthReceipt, ...]
    cover_edges: int
    rank_barriers: int
    h_seed_reads: int
    base_seed_reads: int
    opaque_base_reads: int
    sparse_patch_reads: int
    rank_six_output_reads: int
    h_rank_six_absolute_bound: int
    structural_base_rank_six_absolute_bound: int
    opaque_base_scaled_absolute_bound: int
    sparse_patch_scaled_absolute_bound: int
    output_scaled_absolute_bound: int
    output_required_signed_bits: int
    output_mathematical_limbs: int
    output_guard_inclusive_limbs: int
    h_epoch: str
    pricing_epoch: str
    base_producer_source_sha256: str
    base_producer_semantic_sha256: str
    base_refresh_cadence: base.RefreshCadence
    base_structural_epoch: str
    base_correction_epoch: str | None
    master_support_epoch: str | None


@dataclass(frozen=True, slots=True)
class ZetaEvaluation:
    prices: tuple[tuple[int, int], ...]
    scaled_prices: tuple[tuple[int, int], ...]
    levels: tuple[tuple[tuple[int, int], ...], ...]
    work: ZetaWorkReceipt


def _structural_component(
    producer: base.BaseProducer,
) -> base.LatticeComponent | None:
    if isinstance(producer, base.LatticeBaseProducer):
        return producer.component
    if isinstance(producer, base.LatticeSparseBaseProducer):
        return producer.component
    return None


def evaluate_rank_truncated_zeta(
    value: ExactPriceInput,
    *,
    prepared_h: PreparedHArtifact | None = None,
    prepared_base: PreparedBaseArtifact | None = None,
) -> ZetaEvaluation:
    if prepared_h is not None:
        prepared_h.assert_fresh(value)
    if prepared_base is not None:
        prepared_base.assert_fresh(value.base_producer)
    h = dict(value.h_scalars)
    producer = value.base_producer
    audit = base.audit_base_producer(producer)
    component = _structural_component(producer)
    if component is not None and component.output_scale != OUTPUT_SCALE:
        raise ValueError("topology shared circuit lacks an exact common scale")
    structural = {} if component is None else dict(component.seed_values)
    h_maxima = tuple(
        max(
            (
                abs(h[mask])
                for mask in prefix.complete_masks(value.available_cards, level)
            ),
            default=0,
        )
        for level in range(SUBSET_MAXIMUM + 1)
    )
    if component is None:
        base_maxima: tuple[int, ...] = ()
    else:
        base_maxima = tuple(
            max(
                (
                    abs(structural[mask])
                    for mask in prefix.complete_masks(value.available_cards, level)
                ),
                default=0,
            )
            for level in range(component.maximum_seed_rank + 1)
        )
    levels: list[dict[int, int]] = []
    receipts = []
    total_edges = 0
    total_h_reads = 0
    total_base_reads = 0
    for rank in range(SOURCE_WIDTH + 1):
        rows: dict[int, int] = {}
        h_reads = 0
        base_reads = 0
        for mask in prefix.complete_masks(value.available_cards, rank):
            seed = 0
            if rank <= SUBSET_MAXIMUM:
                seed += H_SEED_WEIGHTS[rank] * h[mask]
                h_reads += 1
            if component is not None and rank <= component.maximum_seed_rank:
                seed += component.seed_weights[rank] * structural[mask]
                base_reads += 1
            total = seed
            if rank:
                parent = mask
                while parent:
                    bit = parent & -parent
                    total += levels[rank - 1][mask ^ bit]
                    parent ^= bit
            rows[mask] = total
        h_bound = _rank_component_bound(
            rank,
            SUBSET_MAXIMUM,
            H_SEED_WEIGHTS,
            h_maxima,
        )
        base_bound = (
            0
            if component is None
            else _rank_component_bound(
                rank,
                component.maximum_seed_rank,
                component.seed_weights,
                base_maxima,
            )
        )
        combined_bound = h_bound + base_bound
        observed = max((abs(item) for item in rows.values()), default=0)
        if observed > combined_bound:
            raise ArithmeticError("topology per-rank bound is not conservative")
        h_bits, h_mathematical, h_guard = _required_width(h_bound)
        base_bits, base_mathematical, base_guard = _required_width(base_bound)
        bits, mathematical, guard = _required_width(combined_bound)
        edges = 0 if rank == 0 else rank * comb(value.available_cards, rank)
        receipts.append(
            RankWidthReceipt(
                rank,
                comb(value.available_cards, rank),
                edges,
                h_reads,
                base_reads,
                h_bound,
                base_bound,
                combined_bound,
                observed,
                h_bits,
                h_mathematical,
                h_guard,
                base_bits,
                base_mathematical,
                base_guard,
                bits,
                mathematical,
                guard,
            )
        )
        total_edges += edges
        total_h_reads += h_reads
        total_base_reads += base_reads
        levels.append(rows)
    opaque_values: dict[int, int] = {}
    corrections: dict[int, int] = {}
    if isinstance(producer, base.OpaqueBaseProducer):
        opaque_values = dict(producer.source_values)
    elif isinstance(producer, base.LatticeSparseBaseProducer):
        corrections = dict(producer.corrections)
    scaled_rows = []
    prices = []
    opaque_bound = (
        0
        if not opaque_values
        else OUTPUT_SCALE * max(abs(item) for item in opaque_values.values())
    )
    patch_bound = (
        0
        if not corrections
        else OUTPUT_SCALE * max(abs(item) for item in corrections.values())
    )
    output_bound = receipts[-1].combined_absolute_bound + opaque_bound + patch_bound
    output_bits, output_mathematical, output_guard = _required_width(output_bound)
    for source in prefix.complete_masks(value.available_cards, SOURCE_WIDTH):
        scaled = levels[SOURCE_WIDTH][source]
        if opaque_values:
            scaled += OUTPUT_SCALE * opaque_values[source]
        if source in corrections:
            scaled += OUTPUT_SCALE * corrections[source]
        if abs(scaled) > output_bound:
            raise ArithmeticError("topology output bound is not conservative")
        if scaled % OUTPUT_SCALE:
            raise ArithmeticError("topology rank-six price is not divisible by 24")
        price = scaled // OUTPUT_SCALE
        scaled_rows.append((source, scaled))
        prices.append((source, price))
    if tuple(prices) != direct_price_map(value):
        raise ArithmeticError("topology zeta prices differ from direct authority")
    structural_epoch = audit.structural_epoch
    identity = audit.producer_identity
    refresh_cadence = audit.refresh_cadence
    if structural_epoch is None or identity is None or refresh_cadence is None:
        raise AssertionError("typed base producer omitted its structural epoch")
    work = ZetaWorkReceipt(
        tuple(receipts),
        total_edges,
        SOURCE_WIDTH,
        total_h_reads,
        total_base_reads,
        len(opaque_values),
        len(corrections),
        len(prices),
        receipts[-1].h_absolute_bound,
        receipts[-1].base_absolute_bound,
        opaque_bound,
        patch_bound,
        output_bound,
        output_bits,
        output_mathematical,
        output_guard,
        value.h_epoch.digest,
        value.pricing_epoch.digest,
        identity.source_sha256,
        identity.semantic_sha256,
        refresh_cadence,
        structural_epoch.digest,
        None if audit.correction_epoch is None else audit.correction_epoch.digest,
        None if audit.master_support_epoch is None else audit.master_support_epoch.digest,
    )
    return ZetaEvaluation(
        tuple(prices),
        tuple(scaled_rows),
        tuple(tuple(rows.items()) for rows in levels),
        work,
    )


@dataclass(frozen=True, slots=True)
class ReverseReceipt:
    scaled_h_transpose: tuple[tuple[int, int], ...]
    cover_edges: int
    rank_barriers: int


def reverse_h_transpose_scaled(
    available_cards: int,
    source_weights: Sequence[tuple[int, int]],
) -> ReverseReceipt:
    if available_cards not in DOMAINS:
        raise ValueError("reverse topology domain differs")
    expected_sources = prefix.complete_masks(available_cards, SOURCE_WIDTH)
    weights = dict(source_weights)
    if (
        len(weights) != len(source_weights)
        or tuple(weights) != expected_sources
        or any(isinstance(item, bool) or not isinstance(item, int) for item in weights.values())
    ):
        raise ValueError("reverse topology source domain is incomplete or reordered")
    levels: dict[int, dict[int, int]] = {SOURCE_WIDTH: dict(weights)}
    edges = 0
    full_mask = (1 << available_cards) - 1
    for rank in range(SOURCE_WIDTH - 1, -1, -1):
        rows = {}
        for mask in prefix.complete_masks(available_cards, rank):
            total = 0
            remaining = full_mask ^ mask
            while remaining:
                bit = remaining & -remaining
                total += levels[rank + 1][mask | bit]
                remaining ^= bit
                edges += 1
            rows[mask] = total
        levels[rank] = rows
    output = []
    for rank in range(SUBSET_MAXIMUM + 1):
        for mask in prefix.complete_masks(available_cards, rank):
            output.append((mask, H_SEED_WEIGHTS[rank] * levels[rank][mask]))
    expected_edges = sum(level * comb(available_cards, level) for level in range(1, 7))
    if edges != expected_edges:
        raise AssertionError("reverse topology cover-edge count differs")
    return ReverseReceipt(tuple(output), edges, SOURCE_WIDTH)


def direct_h_transpose_scaled(
    available_cards: int,
    source_weights: Sequence[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    weights = dict(source_weights)
    if tuple(weights) != prefix.complete_masks(available_cards, SOURCE_WIDTH):
        raise ValueError("direct transpose source domain differs")
    output = []
    for rank in range(SUBSET_MAXIMUM + 1):
        for subset in prefix.complete_masks(available_cards, rank):
            total = sum(weight for source, weight in weights.items() if subset & source == subset)
            output.append((subset, OUTPUT_SCALE * PRICE_COEFFICIENTS[rank] * total))
    return tuple(output)


@dataclass(frozen=True, slots=True)
class ArmWorkReceipt:
    h_feature_contractions: int
    source_prices_read: int
    direct_subset_reads: int
    zeta_cover_edges: int
    zeta_rank_barriers: int
    opaque_base_reads: int
    sparse_patch_reads: int
    prefix_base_reads: int
    prefix_nodes_bound: int
    prefix_possible_terms: int
    prefix_nodes_popped: int
    prefix_exact_leaves: int
    prefix_pruned_sources: int
    maximum_frontier_nodes: int


@dataclass(frozen=True, slots=True)
class ArmReceipt:
    arm: str
    mode: str
    maximum_price: int | None
    maximizers: tuple[int, ...]
    positive_coordinates: tuple[int, ...]
    witness_coordinate: int | None
    witness_price: int | None
    complete_domain_covered: bool
    closed_no_positive: bool
    hybrid_switched: bool
    hybrid_switch_reason: str | None
    certified_source_count: int
    work: ArmWorkReceipt


def _empty_work(value: ExactPriceInput) -> ArmWorkReceipt:
    return ArmWorkReceipt(
        len(value.h_scalars) * FEATURE_WIDTH,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )


def _summarize_ordered_prices(
    arm: str,
    mode: Mode,
    ordered_prices: Iterable[tuple[int, int]],
    total_sources: int,
    work: ArmWorkReceipt,
    *,
    hybrid_switched: bool = False,
    hybrid_switch_reason: str | None = None,
) -> ArmReceipt:
    rows = []
    positives = []
    witness: tuple[int, int] | None = None
    for source, price in ordered_prices:
        rows.append((source, price))
        if price > 0:
            positives.append(source)
            if witness is None:
                witness = (source, price)
                if mode in ("positive_witness", "prove_none"):
                    break
    covered = len(rows) == total_sources
    if mode == "exact_argmax_full_ties":
        if not covered:
            raise AssertionError("argmax topology did not cover the complete domain")
        maximum = max(price for _, price in rows)
        maximizers = tuple(source for source, price in rows if price == maximum)
    else:
        maximum = None
        maximizers = ()
    if mode == "prove_none" and witness is None and not covered:
        raise AssertionError("prove-none topology stopped without proof or witness")
    return ArmReceipt(
        arm,
        mode,
        maximum,
        maximizers,
        tuple(positives),
        None if witness is None else witness[0],
        None if witness is None else witness[1],
        covered,
        mode == "prove_none" and covered and not positives,
        hybrid_switched,
        hybrid_switch_reason,
        len(rows),
        replace(work, source_prices_read=work.source_prices_read + len(rows)),
    )


def run_direct(value: ExactPriceInput, mode: Mode) -> ArmReceipt:
    prices = direct_price_map(value)
    work = replace(
        _empty_work(value),
        direct_subset_reads=57 * len(prices),
        opaque_base_reads=(
            len(prices) if isinstance(value.base_producer, base.OpaqueBaseProducer) else 0
        ),
        sparse_patch_reads=(
            len(value.base_producer.corrections)
            if isinstance(value.base_producer, base.LatticeSparseBaseProducer)
            else 0
        ),
    )
    return _summarize_ordered_prices(
        ARM_NAMES[0], mode, prices, len(prices), work
    )


def run_zeta(value: ExactPriceInput, mode: Mode) -> ArmReceipt:
    evaluated = evaluate_rank_truncated_zeta(value)
    work = replace(
        _empty_work(value),
        zeta_cover_edges=evaluated.work.cover_edges,
        zeta_rank_barriers=evaluated.work.rank_barriers,
        opaque_base_reads=evaluated.work.opaque_base_reads,
        sparse_patch_reads=evaluated.work.sparse_patch_reads,
    )
    return _summarize_ordered_prices(
        ARM_NAMES[1], mode, evaluated.prices, len(evaluated.prices), work
    )


def _prefix_work(
    value: ExactPriceInput,
    compiled: prefix.CompiledSeparation,
    receipt: prefix.SearchReceipt,
) -> ArmWorkReceipt:
    return replace(
        _empty_work(value),
        prefix_base_reads=compiled.ledger.source_base_values_read,
        prefix_nodes_bound=compiled.ledger.prefix_nodes_bound,
        prefix_possible_terms=compiled.ledger.possible_subset_terms_examined_for_bounds,
        prefix_nodes_popped=receipt.prefix_nodes_popped,
        prefix_exact_leaves=receipt.exact_leaf_prices,
        prefix_pruned_sources=receipt.pruned_source_leaves,
        maximum_frontier_nodes=receipt.maximum_frontier_nodes,
        direct_subset_reads=receipt.selective_subset_scalar_reads,
        source_prices_read=receipt.exact_leaf_prices,
    )


def _combine_same_compile_search_work(
    first: ArmWorkReceipt,
    second: ArmWorkReceipt,
) -> ArmWorkReceipt:
    """Charge two searches while charging their one shared compile exactly once."""

    return ArmWorkReceipt(
        h_feature_contractions=max(
            first.h_feature_contractions, second.h_feature_contractions
        ),
        source_prices_read=first.source_prices_read + second.source_prices_read,
        direct_subset_reads=first.direct_subset_reads + second.direct_subset_reads,
        zeta_cover_edges=0,
        zeta_rank_barriers=0,
        opaque_base_reads=0,
        sparse_patch_reads=0,
        prefix_base_reads=max(first.prefix_base_reads, second.prefix_base_reads),
        prefix_nodes_bound=max(first.prefix_nodes_bound, second.prefix_nodes_bound),
        prefix_possible_terms=max(
            first.prefix_possible_terms, second.prefix_possible_terms
        ),
        prefix_nodes_popped=first.prefix_nodes_popped + second.prefix_nodes_popped,
        prefix_exact_leaves=first.prefix_exact_leaves + second.prefix_exact_leaves,
        prefix_pruned_sources=(
            first.prefix_pruned_sources + second.prefix_pruned_sources
        ),
        maximum_frontier_nodes=max(
            first.maximum_frontier_nodes, second.maximum_frontier_nodes
        ),
    )


def _validated_compiled(
    value: ExactPriceInput,
    prepared: PreparedPrefixArtifact | None,
) -> prefix.CompiledSeparation:
    if prepared is None:
        return prefix.compile_separation(as_prefix_instance(value))
    if not isinstance(prepared, PreparedPrefixArtifact):
        raise TypeError("prepared prefix artifact has the wrong semantic type")
    prepared.assert_fresh(value)
    return prepared.compiled


def run_prefix(
    value: ExactPriceInput,
    mode: Mode,
    *,
    prepared: PreparedPrefixArtifact | None = None,
) -> ArmReceipt:
    compiled = _validated_compiled(value, prepared)
    if mode == "exact_argmax_full_ties":
        argmax = prefix.search(compiled, "exact_argmax")
        closure = prefix.search(compiled, "final_global_closure")
        if not argmax.complete_domain_covered or not closure.complete_domain_covered:
            raise AssertionError("prefix validation searches did not close the domain")
        return ArmReceipt(
            ARM_NAMES[2],
            mode,
            argmax.maximum_price,
            argmax.maximizers,
            closure.positive_coordinates,
            None,
            None,
            True,
            False,
            False,
            None,
            comb(value.available_cards, SOURCE_WIDTH),
            _combine_same_compile_search_work(
                _prefix_work(value, compiled, argmax),
                _prefix_work(value, compiled, closure),
            ),
        )
    prefix_mode: prefix.SearchMode = {
        "positive_witness": "proposal_separation",
        "prove_none": "final_global_closure",
    }[mode]  # type: ignore[assignment]
    receipt = prefix.search(compiled, prefix_mode)
    witness_coordinate = receipt.proposal_coordinate
    witness_price = receipt.proposal_price
    if mode == "prove_none" and receipt.positive_coordinates:
        witness_coordinate = receipt.positive_coordinates[0]
        witness_price = exact_price(value, witness_coordinate)
    return ArmReceipt(
        ARM_NAMES[2],
        mode,
        receipt.maximum_price if mode == "exact_argmax_full_ties" else None,
        receipt.maximizers if mode == "exact_argmax_full_ties" else (),
        receipt.positive_coordinates,
        witness_coordinate,
        witness_price,
        receipt.complete_domain_covered,
        mode == "prove_none"
        and receipt.complete_domain_covered
        and not receipt.positive_coordinates,
        False,
        None,
        receipt.visited_source_leaves + receipt.pruned_source_leaves,
        _prefix_work(value, compiled, receipt),
    )


@dataclass(frozen=True, slots=True)
class HybridSwitchDecision:
    switch: bool
    reason: str | None
    early_exact_leaf_checkpoint: int
    early_required_certified_coverage: int
    hard_exact_leaf_checkpoint: int


def hybrid_switch_decision(
    source_population: int,
    exact_leaves: int,
    certified_coverage: int,
    *,
    positive_witness: bool,
    globally_closed: bool,
) -> HybridSwitchDecision:
    if any(
        isinstance(item, bool) or not isinstance(item, int)
        for item in (source_population, exact_leaves, certified_coverage)
    ):
        raise TypeError("hybrid switch counts must be plain integers")
    if (
        source_population <= 0
        or exact_leaves < 0
        or certified_coverage < 0
        or exact_leaves > source_population
        or certified_coverage > source_population
        or exact_leaves > certified_coverage
    ):
        raise ValueError("hybrid switch counts differ")
    early = (source_population + 63) // 64
    required = (source_population + 1) // 2
    hard = (source_population + 7) // 8
    if positive_witness or globally_closed:
        return HybridSwitchDecision(False, None, early, required, hard)
    if exact_leaves >= hard:
        return HybridSwitchDecision(True, "hard_exact_leaf_checkpoint", early, required, hard)
    if exact_leaves >= early and certified_coverage < required:
        return HybridSwitchDecision(True, "early_insufficient_coverage", early, required, hard)
    return HybridSwitchDecision(False, None, early, required, hard)


def _combine_work(prefix_work: ArmWorkReceipt, zeta_work: ArmWorkReceipt) -> ArmWorkReceipt:
    return ArmWorkReceipt(
        h_feature_contractions=max(
            prefix_work.h_feature_contractions, zeta_work.h_feature_contractions
        ),
        source_prices_read=prefix_work.source_prices_read + zeta_work.source_prices_read,
        direct_subset_reads=prefix_work.direct_subset_reads + zeta_work.direct_subset_reads,
        zeta_cover_edges=prefix_work.zeta_cover_edges + zeta_work.zeta_cover_edges,
        zeta_rank_barriers=prefix_work.zeta_rank_barriers + zeta_work.zeta_rank_barriers,
        opaque_base_reads=prefix_work.opaque_base_reads + zeta_work.opaque_base_reads,
        sparse_patch_reads=prefix_work.sparse_patch_reads + zeta_work.sparse_patch_reads,
        prefix_base_reads=prefix_work.prefix_base_reads + zeta_work.prefix_base_reads,
        prefix_nodes_bound=prefix_work.prefix_nodes_bound + zeta_work.prefix_nodes_bound,
        prefix_possible_terms=prefix_work.prefix_possible_terms + zeta_work.prefix_possible_terms,
        prefix_nodes_popped=prefix_work.prefix_nodes_popped + zeta_work.prefix_nodes_popped,
        prefix_exact_leaves=prefix_work.prefix_exact_leaves + zeta_work.prefix_exact_leaves,
        prefix_pruned_sources=prefix_work.prefix_pruned_sources + zeta_work.prefix_pruned_sources,
        maximum_frontier_nodes=max(
            prefix_work.maximum_frontier_nodes, zeta_work.maximum_frontier_nodes
        ),
    )


def run_hybrid(
    value: ExactPriceInput,
    mode: Mode,
    *,
    prepared: PreparedPrefixArtifact | None = None,
) -> ArmReceipt:
    if mode == "exact_argmax_full_ties":
        controlled = run_prefix(value, mode, prepared=prepared)
        return replace(controlled, arm=ARM_NAMES[3])
    compiled = _validated_compiled(value, prepared)
    node_map = {node.prefix: node for node in compiled.nodes}
    root = node_map[()]
    frontier: list[tuple[int, int, tuple[int, ...]]] = [
        (-root.upper, root.first_colex_rank, root.prefix)
    ]
    total_sources = comb(value.available_cards, SOURCE_WIDTH)
    popped = leaves = pruned = reads = 0
    maximum_frontier = 1
    witness: tuple[int, int] | None = None
    while frontier:
        _, _, selected = heapq.heappop(frontier)
        popped += 1
        node = node_map[selected]
        if not node.children:
            source_mask = prefix.mask_from_cards(selected)
            price = exact_price(value, source_mask)
            if price != node.upper:
                raise AssertionError("hybrid exact leaf differs from its sealed bound")
            leaves += 1
            reads += 57
            if price > 0:
                witness = (source_mask, price)
                break
            decision = hybrid_switch_decision(
                total_sources,
                leaves,
                leaves + pruned,
                positive_witness=False,
                globally_closed=not frontier and leaves + pruned == total_sources,
            )
            if decision.switch:
                prefix_receipt = prefix.SearchReceipt(
                    "hybrid_prefix",
                    True,
                    None,
                    (),
                    (),
                    None,
                    None,
                    popped,
                    leaves,
                    reads,
                    pruned,
                    leaves,
                    maximum_frontier,
                    False,
                )
                before = _prefix_work(value, compiled, prefix_receipt)
                after = run_zeta(value, mode)
                return replace(
                    after,
                    arm=ARM_NAMES[3],
                    hybrid_switched=True,
                    hybrid_switch_reason=decision.reason,
                    work=_combine_work(before, after.work),
                )
            continue
        if node.upper <= 0:
            pruned += node.descendant_count
            continue
        for child_prefix in node.children:
            child = node_map[child_prefix]
            heapq.heappush(
                frontier,
                (-child.upper, child.first_colex_rank, child.prefix),
            )
        maximum_frontier = max(maximum_frontier, len(frontier))
    covered = witness is None and leaves + pruned == total_sources
    prefix_receipt = prefix.SearchReceipt(
        "hybrid_prefix",
        True,
        None,
        (),
        () if witness is None else (witness[0],),
        None if witness is None else witness[0],
        None if witness is None else witness[1],
        popped,
        leaves,
        reads,
        pruned,
        leaves,
        maximum_frontier,
        covered,
    )
    return ArmReceipt(
        ARM_NAMES[3],
        mode,
        None,
        (),
        prefix_receipt.positive_coordinates,
        prefix_receipt.proposal_coordinate,
        prefix_receipt.proposal_price,
        covered,
        mode == "prove_none" and covered,
        False,
        None,
        leaves + pruned,
        _prefix_work(value, compiled, prefix_receipt),
    )


def run_arm(value: ExactPriceInput, arm: str, mode: Mode) -> ArmReceipt:
    if mode not in ("positive_witness", "prove_none", "exact_argmax_full_ties"):
        raise ValueError("topology runtime mode differs")
    functions = {
        ARM_NAMES[0]: run_direct,
        ARM_NAMES[1]: run_zeta,
        ARM_NAMES[2]: run_prefix,
        ARM_NAMES[3]: run_hybrid,
    }
    try:
        function = functions[arm]
    except KeyError as error:
        raise ValueError("topology arm differs") from error
    return function(value, mode)


def source_boundary_claims() -> dict[str, object]:
    return {
        "base_producer_classification": "producer_absent",
        "base_refresh_cadence": None,
        "production_base_exponent_admission": None,
        "source_seal": True,
        "bakeoff_result": None,
        "topology_selected": None,
        "literal_45_fit": None,
        "resolver_iteration_result": None,
        "action_clock_result": None,
        "decision_quality_result": None,
        "truncation_authorized": False,
        "blueprint_result": None,
        "poker_strength_result": None,
    }


__all__ = [
    "ARM_NAMES",
    "BASE_FAMILIES",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "DOMAINS",
    "ExactPriceInput",
    "FEATURE_WIDTH",
    "H_SEED_WEIGHTS",
    "HybridSwitchDecision",
    "LEGACY_FAMILIES",
    "OUTPUT_SCALE",
    "PRICE_COEFFICIENTS",
    "PREREGISTRATION_COMMIT",
    "PreparedBaseArtifact",
    "PreparedHArtifact",
    "PreparedPrefixArtifact",
    "RESULT_RELATIVE_PATH",
    "SOURCE_WIDTH",
    "SUBSET_MAXIMUM",
    "ArmReceipt",
    "RankWidthReceipt",
    "ZetaEvaluation",
    "as_prefix_instance",
    "canonical_lf_sha256",
    "direct_h_transpose_scaled",
    "direct_price_map",
    "evaluate_rank_truncated_zeta",
    "exact_price",
    "hybrid_switch_decision",
    "load_preregistered_config",
    "make_control_input",
    "prepare_base_artifact",
    "prepare_h_artifact",
    "prepare_prefix_artifact",
    "reverse_h_transpose_scaled",
    "run_arm",
    "run_direct",
    "run_hybrid",
    "run_prefix",
    "run_zeta",
    "source_boundary_claims",
    "verify_preregistered_contract",
]
