"""Compile and identity-bind ADR-0311's value-free LP corpus.

This is structural code, not the audit runner.  It materializes no optimum,
invokes no backend or certificate, and owns no pass/fail interpretation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from math import ceil, isfinite

from .native_simplex_audit_structures import (
    ADR0311_MICRO_STRUCTURE_SHA256,
    ADR0311_WIDTH4_STRUCTURE_SHA256,
    AuditExactProbability,
    AuditWidthFourContext,
    ExactMicroLinearProgram,
    ExactMicroLpStructure,
    FreshWidthFourAuditStructure,
    Sha256CounterStream,
    build_adr0311_micro_lp_structure,
    build_adr0311_width_four_structure,
    fisher_yates_order,
)
from .reduced_river_sizing_lp import (
    LinearProgramConstraintUnit,
    LinearProgramObjectiveUnit,
    LinearProgramVariableUnit,
    ReducedRiverSizingLinearProgram,
    compile_reduced_river_sizing_lp,
)

ADR0311_TRANSFORM_VERSION = "exact-lp-metamorphic-variants-v1"
ADR0311_TRANSFORM_SEED_PREFIX = (
    "pontius:adr-0311:native-simplex-robustness:transform:sha256-stream:v1"
)
ADR0311_BASE_COUNT = 177
ADR0311_VARIANTS_PER_BASE = 5
ADR0311_VARIANT_COUNT = 885
ADR0311_KNOWN_REGRESSION_BASE_ID = "adr0311-simplex-known-adr0310-qualified-b-c21-full"
ADR0311_KNOWN_STRUCTURAL_CONTEXT_SHA256 = (
    "9ebc519357c17b7ac100b4eaf40996ca774484b974f6bfe0145cc060b99dd440"
)
ADR0311_KNOWN_ORACLE_CONTEXT_SHA256 = (
    "df0e8a00d5b0816a4a8b99a7f9fc7d1b000b38e9fb009f88e70ffa47827336e2"
)
ADR0311_KNOWN_BINDING_SHA256 = "a3dc51f7fb5fff0a1794e1fa477f1d959204db616d1d320fea15773b1215a022"
ADR0311_KNOWN_FAILURE_SHA256 = "03c5dc4f00c0429d3c615352a1d52f9c64dec0d3b4c4cf72f6d7cc171e3a26fe"

ADR0311_KNOWN_REGRESSION_INPUT_SHA256 = (
    "4a08dde49bc006bf38b8b8b86763055570219aca3b520f56a9319a5c99ee35dc"
)
ADR0311_BASE_CORPUS_SHA256 = "8201b331a0bb936f1bd3e2dd78acf46278ff063d6b86cf045df7e56f2141019d"
ADR0311_VARIANT_CORPUS_SHA256 = "5c024f281afe348578018ffa321edd7b276316a3da27f163e1f50cd7f3eb76fe"
ADR0311_COMPLETE_CORPUS_SHA256 = "4be6dcc311bc2f885ce9ad312cee8294f38231180ab78bbbfb6497184b1597a3"

_DYADIC_SCALE_EXPONENTS = (-8, -4, 0, 4, 8)


def _valid_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _digest_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return sha256(encoded).hexdigest()


def _linear_program_payload(
    *,
    objective: tuple[float, ...],
    coefficients: tuple[tuple[float, ...], ...],
    bounds: tuple[float, ...],
    row_units: tuple[LinearProgramConstraintUnit, ...],
    variable_units: tuple[LinearProgramVariableUnit, ...],
    trusted_box_lower_bounds: tuple[float, ...],
    trusted_box_upper_bounds: tuple[float, ...],
    objective_unit: LinearProgramObjectiveUnit,
    objective_offset: float,
) -> dict[str, object]:
    return {
        "bounds_hex": tuple(value.hex() for value in bounds),
        "coefficient_hex": tuple(tuple(value.hex() for value in row) for row in coefficients),
        "objective_hex": tuple(value.hex() for value in objective),
        "objective_offset_hex": objective_offset.hex(),
        "objective_unit": objective_unit.value,
        "row_units": tuple(unit.value for unit in row_units),
        "trusted_box_lower_hex": tuple(value.hex() for value in trusted_box_lower_bounds),
        "trusted_box_upper_hex": tuple(value.hex() for value in trusted_box_upper_bounds),
        "variable_units": tuple(unit.value for unit in variable_units),
        "version": "adr0311-audit-linear-program-v1",
    }


class AuditBaseFamily(StrEnum):
    KNOWN_REGRESSION = "known-regression"
    EXACT_MICRO = "exact-micro"
    FRESH_REDUCED_SIZING = "fresh-reduced-sizing"


class AuditSizingArm(StrEnum):
    MINIMUM_ALL_IN = "minimum-all-in"
    FULL_INTEGER = "full-integer"


class AuditVariantKind(StrEnum):
    CANONICAL = "canonical"
    ROW_PERMUTATION = "row-permutation"
    VARIABLE_PERMUTATION = "variable-permutation"
    DYADIC_ROW_SCALING = "dyadic-row-scaling"
    REDUNDANCY = "redundancy"


class AuditRowRole(StrEnum):
    ORIGINAL = "original"
    DUPLICATE = "duplicate"
    ZERO_REDUNDANCY = "zero-redundancy"


@dataclass(frozen=True, slots=True)
class AuditLinearProgramBase:
    base_id: str
    family: AuditBaseFamily
    source_input_sha256: str
    context_id: str | None
    bet_sizes: tuple[int, ...] | None
    objective: tuple[float, ...]
    coefficients: tuple[tuple[float, ...], ...]
    bounds: tuple[float, ...]
    row_units: tuple[LinearProgramConstraintUnit, ...]
    variable_units: tuple[LinearProgramVariableUnit, ...]
    trusted_box_lower_bounds: tuple[float, ...]
    trusted_box_upper_bounds: tuple[float, ...]
    objective_unit: LinearProgramObjectiveUnit
    objective_offset: float

    def __post_init__(self) -> None:
        if not isinstance(self.base_id, str) or not self.base_id.strip():
            raise ValueError("audit base id must be nonempty")
        if not isinstance(self.family, AuditBaseFamily):
            raise TypeError("audit base family must be semantic")
        if not _valid_digest(self.source_input_sha256):
            raise ValueError("audit base source-input digest is invalid")
        if self.family is AuditBaseFamily.EXACT_MICRO:
            if self.context_id is not None or self.bet_sizes is not None:
                raise ValueError("micro audit base cannot carry sizing coordinates")
            if self.objective_unit is not LinearProgramObjectiveUnit.DIMENSIONLESS:
                raise ValueError("micro audit objective must be dimensionless")
            if self.objective_offset != 0.0:
                raise ValueError("micro audit objective cannot carry a chip offset")
        else:
            if not isinstance(self.context_id, str) or not self.context_id.strip():
                raise ValueError("sizing audit base requires a context id")
            if (
                not isinstance(self.bet_sizes, tuple)
                or not self.bet_sizes
                or any(
                    isinstance(value, bool) or not isinstance(value, int) or value <= 0
                    for value in self.bet_sizes
                )
            ):
                raise TypeError("sizing audit base requires immutable bet sizes")
            if any(
                left >= right
                for left, right in zip(
                    self.bet_sizes,
                    self.bet_sizes[1:],
                    strict=False,
                )
            ):
                raise ValueError("sizing audit base bet sizes must increase strictly")
            if self.objective_unit is not LinearProgramObjectiveUnit.CHIPS:
                raise ValueError("sizing audit objective must be chip-valued")
        if not isinstance(self.objective, tuple) or not self.objective:
            raise TypeError("audit base objective must be a nonempty immutable tuple")
        width = len(self.objective)
        if any(not isinstance(value, float) or not isfinite(value) for value in self.objective):
            raise ValueError("audit base objective must contain finite floats")
        if not isinstance(self.coefficients, tuple) or not self.coefficients:
            raise TypeError("audit base coefficients must contain immutable rows")
        if any(
            not isinstance(row, tuple)
            or len(row) != width
            or any(not isinstance(value, float) or not isfinite(value) for value in row)
            for row in self.coefficients
        ):
            raise ValueError("audit base coefficient rows must be finite at the objective width")
        row_count = len(self.coefficients)
        if (
            not isinstance(self.bounds, tuple)
            or len(self.bounds) != row_count
            or any(not isinstance(value, float) or not isfinite(value) for value in self.bounds)
        ):
            raise ValueError("audit base bounds must be finite and align with its rows")
        if (
            not isinstance(self.row_units, tuple)
            or len(self.row_units) != row_count
            or any(not isinstance(unit, LinearProgramConstraintUnit) for unit in self.row_units)
        ):
            raise TypeError("audit base row units must be semantic and aligned")
        if (
            not isinstance(self.variable_units, tuple)
            or len(self.variable_units) != width
            or any(not isinstance(unit, LinearProgramVariableUnit) for unit in self.variable_units)
        ):
            raise TypeError("audit base variable units must be semantic and aligned")
        for label, values in (
            ("trusted lower", self.trusted_box_lower_bounds),
            ("trusted upper", self.trusted_box_upper_bounds),
        ):
            if (
                not isinstance(values, tuple)
                or len(values) != width
                or any(not isinstance(value, float) or not isfinite(value) for value in values)
            ):
                raise ValueError(f"audit base {label} box must be finite and aligned")
        if any(
            lower > upper
            for lower, upper in zip(
                self.trusted_box_lower_bounds,
                self.trusted_box_upper_bounds,
                strict=True,
            )
        ):
            raise ValueError("audit base trusted box is inverted")
        if not isinstance(self.objective_unit, LinearProgramObjectiveUnit):
            raise TypeError("audit base objective unit must be semantic")
        if not isinstance(self.objective_offset, float) or not isfinite(self.objective_offset):
            raise ValueError("audit base objective offset must be a finite float")

    @property
    def row_count(self) -> int:
        return len(self.coefficients)

    @property
    def variable_count(self) -> int:
        return len(self.objective)

    @property
    def linear_program_digest(self) -> str:
        return _digest_payload(
            _linear_program_payload(
                objective=self.objective,
                coefficients=self.coefficients,
                bounds=self.bounds,
                row_units=self.row_units,
                variable_units=self.variable_units,
                trusted_box_lower_bounds=self.trusted_box_lower_bounds,
                trusted_box_upper_bounds=self.trusted_box_upper_bounds,
                objective_unit=self.objective_unit,
                objective_offset=self.objective_offset,
            )
        )

    @property
    def digest(self) -> str:
        return _digest_payload(
            {
                "base_id": self.base_id,
                "bet_sizes": self.bet_sizes,
                "context_id": self.context_id,
                "family": self.family.value,
                "linear_program_sha256": self.linear_program_digest,
                "source_input_sha256": self.source_input_sha256,
                "version": "adr0311-audit-base-identity-v1",
            }
        )


@dataclass(frozen=True, slots=True)
class AuditVariantDescriptor:
    variant_id: str
    base_id: str
    base_sha256: str
    kind: AuditVariantKind
    seed: str
    variant_to_canonical_variables: tuple[int, ...]
    canonical_to_variant_variables: tuple[int, ...]
    variant_to_canonical_rows: tuple[int | None, ...]
    canonical_to_variant_rows: tuple[tuple[int, ...], ...]
    row_roles: tuple[AuditRowRole, ...]
    row_scale_exponents: tuple[int, ...]
    row_units: tuple[LinearProgramConstraintUnit, ...]
    variable_units: tuple[LinearProgramVariableUnit, ...]
    linear_program_sha256: str

    def __post_init__(self) -> None:
        for label, value in (
            ("variant id", self.variant_id),
            ("base id", self.base_id),
            ("seed", self.seed),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"audit {label} must be nonempty")
        if not _valid_digest(self.base_sha256) or not _valid_digest(self.linear_program_sha256):
            raise ValueError("audit variant digest is invalid")
        if not isinstance(self.kind, AuditVariantKind):
            raise TypeError("audit variant kind must be semantic")
        variable_count = len(self.variant_to_canonical_variables)
        if any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in self.variant_to_canonical_variables
        ):
            raise TypeError("audit variant variable map must contain exact indices")
        if set(self.variant_to_canonical_variables) != set(range(variable_count)):
            raise ValueError("audit variant-to-canonical variable map is not a permutation")
        if len(self.canonical_to_variant_variables) != variable_count or any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in self.canonical_to_variant_variables
        ):
            raise ValueError("audit canonical-to-variant variable map has the wrong width")
        if any(
            self.canonical_to_variant_variables[canonical] != variant
            for variant, canonical in enumerate(self.variant_to_canonical_variables)
        ):
            raise ValueError("audit variable maps are not inverses")
        row_count = len(self.variant_to_canonical_rows)
        for label, values in (
            ("row roles", self.row_roles),
            ("row scale exponents", self.row_scale_exponents),
            ("row units", self.row_units),
        ):
            if not isinstance(values, tuple) or len(values) != row_count:
                raise TypeError(f"audit variant {label} must align with rows")
        if any(not isinstance(role, AuditRowRole) for role in self.row_roles):
            raise TypeError("audit variant row role must be semantic")
        if any(
            isinstance(exponent, bool)
            or not isinstance(exponent, int)
            or exponent not in _DYADIC_SCALE_EXPONENTS
            for exponent in self.row_scale_exponents
        ):
            raise ValueError("audit variant row scale lies outside the frozen dyadic set")
        if any(not isinstance(unit, LinearProgramConstraintUnit) for unit in self.row_units):
            raise TypeError("audit variant row unit must be semantic")
        if (
            not isinstance(self.variable_units, tuple)
            or len(self.variable_units) != variable_count
            or any(not isinstance(unit, LinearProgramVariableUnit) for unit in self.variable_units)
        ):
            raise TypeError("audit variant variable units must be semantic and aligned")
        if any(
            (origin is None) != (role is AuditRowRole.ZERO_REDUNDANCY)
            for origin, role in zip(
                self.variant_to_canonical_rows,
                self.row_roles,
                strict=True,
            )
        ):
            raise ValueError("audit zero-row origins and roles disagree")
        canonical_row_count = len(self.canonical_to_variant_rows)
        if any(
            origin is not None
            and (
                isinstance(origin, bool)
                or not isinstance(origin, int)
                or origin not in range(canonical_row_count)
            )
            for origin in self.variant_to_canonical_rows
        ):
            raise ValueError("audit row origin lies outside the canonical LP")
        for canonical, positions in enumerate(self.canonical_to_variant_rows):
            if not isinstance(positions, tuple) or not positions:
                raise TypeError("every canonical audit row must retain a variant position")
            if any(
                position not in range(row_count)
                or self.variant_to_canonical_rows[position] != canonical
                for position in positions
            ):
                raise ValueError("audit row maps are not inverses")
            expected_positions = tuple(
                variant
                for variant, origin in enumerate(self.variant_to_canonical_rows)
                if origin == canonical
            )
            if positions != expected_positions:
                raise ValueError("audit canonical row map omits a variant counterpart")
        if self.variant_id != f"{self.base_id}--{self.kind.value}":
            raise ValueError("audit variant id differs from its base and kind")
        identity_variables = tuple(range(variable_count))
        identity_rows = tuple(range(canonical_row_count))
        if self.kind is AuditVariantKind.CANONICAL:
            if (
                self.variant_to_canonical_variables != identity_variables
                or self.variant_to_canonical_rows != identity_rows
                or any(role is not AuditRowRole.ORIGINAL for role in self.row_roles)
                or any(self.row_scale_exponents)
            ):
                raise ValueError("canonical audit variant is not the exact identity")
        elif self.kind is AuditVariantKind.ROW_PERMUTATION:
            if (
                self.variant_to_canonical_variables != identity_variables
                or set(self.variant_to_canonical_rows) != set(identity_rows)
                or any(role is not AuditRowRole.ORIGINAL for role in self.row_roles)
                or any(self.row_scale_exponents)
            ):
                raise ValueError("row-permutation audit variant changed another axis")
        elif self.kind is AuditVariantKind.VARIABLE_PERMUTATION:
            if (
                self.variant_to_canonical_rows != identity_rows
                or any(role is not AuditRowRole.ORIGINAL for role in self.row_roles)
                or any(self.row_scale_exponents)
            ):
                raise ValueError("variable-permutation audit variant changed row semantics")
        elif self.kind is AuditVariantKind.DYADIC_ROW_SCALING:
            if (
                self.variant_to_canonical_variables != identity_variables
                or set(self.variant_to_canonical_rows) != set(identity_rows)
                or any(role is not AuditRowRole.ORIGINAL for role in self.row_roles)
            ):
                raise ValueError("dyadic-scaling audit variant changed another axis")
        else:
            duplicate_count = max(1, ceil(canonical_row_count / 8))
            if (
                self.variant_to_canonical_variables != identity_variables
                or self.row_roles.count(AuditRowRole.ORIGINAL) != canonical_row_count
                or self.row_roles.count(AuditRowRole.DUPLICATE) != duplicate_count
                or self.row_roles.count(AuditRowRole.ZERO_REDUNDANCY) != 1
                or any(self.row_scale_exponents)
            ):
                raise ValueError("redundancy audit variant differs from the frozen rule")

    @property
    def digest(self) -> str:
        return _digest_payload(
            {
                "base_id": self.base_id,
                "base_sha256": self.base_sha256,
                "canonical_to_variant_rows": self.canonical_to_variant_rows,
                "canonical_to_variant_variables": self.canonical_to_variant_variables,
                "kind": self.kind.value,
                "linear_program_sha256": self.linear_program_sha256,
                "row_roles": tuple(role.value for role in self.row_roles),
                "row_scale_exponents": self.row_scale_exponents,
                "row_units": tuple(unit.value for unit in self.row_units),
                "seed": self.seed,
                "transform_version": ADR0311_TRANSFORM_VERSION,
                "variable_units": tuple(unit.value for unit in self.variable_units),
                "variant_id": self.variant_id,
                "variant_to_canonical_rows": self.variant_to_canonical_rows,
                "variant_to_canonical_variables": self.variant_to_canonical_variables,
            }
        )


@dataclass(frozen=True, slots=True)
class MaterializedAuditLinearProgram:
    objective: tuple[float, ...]
    coefficients: tuple[tuple[float, ...], ...]
    bounds: tuple[float, ...]
    row_units: tuple[LinearProgramConstraintUnit, ...]
    variable_units: tuple[LinearProgramVariableUnit, ...]
    trusted_box_lower_bounds: tuple[float, ...]
    trusted_box_upper_bounds: tuple[float, ...]
    objective_unit: LinearProgramObjectiveUnit
    objective_offset: float

    @property
    def digest(self) -> str:
        return _digest_payload(
            _linear_program_payload(
                objective=self.objective,
                coefficients=self.coefficients,
                bounds=self.bounds,
                row_units=self.row_units,
                variable_units=self.variable_units,
                trusted_box_lower_bounds=self.trusted_box_lower_bounds,
                trusted_box_upper_bounds=self.trusted_box_upper_bounds,
                objective_unit=self.objective_unit,
                objective_offset=self.objective_offset,
            )
        )


def _inverse_permutation(variant_to_canonical: tuple[int, ...]) -> tuple[int, ...]:
    inverse = [0] * len(variant_to_canonical)
    for variant, canonical in enumerate(variant_to_canonical):
        inverse[canonical] = variant
    return tuple(inverse)


def _canonical_to_variant_rows(
    variant_to_canonical: tuple[int | None, ...],
    canonical_row_count: int,
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(variant for variant, origin in enumerate(variant_to_canonical) if origin == canonical)
        for canonical in range(canonical_row_count)
    )


def materialize_audit_variant(
    *,
    base: AuditLinearProgramBase,
    descriptor: AuditVariantDescriptor,
) -> MaterializedAuditLinearProgram:
    """Apply one sealed exact representation without invoking a backend."""

    if not isinstance(base, AuditLinearProgramBase):
        raise TypeError("audit variant materialization requires a semantic base")
    if not isinstance(descriptor, AuditVariantDescriptor):
        raise TypeError("audit variant materialization requires a semantic descriptor")
    if descriptor.base_id != base.base_id or descriptor.base_sha256 != base.digest:
        raise ValueError("audit variant descriptor does not bind the supplied base")
    objective = tuple(
        base.objective[canonical] for canonical in descriptor.variant_to_canonical_variables
    )
    lower_bounds = tuple(
        base.trusted_box_lower_bounds[canonical]
        for canonical in descriptor.variant_to_canonical_variables
    )
    upper_bounds = tuple(
        base.trusted_box_upper_bounds[canonical]
        for canonical in descriptor.variant_to_canonical_variables
    )
    coefficients: list[tuple[float, ...]] = []
    bounds: list[float] = []
    for origin, exponent in zip(
        descriptor.variant_to_canonical_rows,
        descriptor.row_scale_exponents,
        strict=True,
    ):
        if origin is None:
            coefficients.append((0.0,) * base.variable_count)
            bounds.append(0.0)
            continue
        scale = float(2**exponent)
        coefficients.append(
            tuple(
                base.coefficients[origin][canonical] * scale
                for canonical in descriptor.variant_to_canonical_variables
            )
        )
        bounds.append(base.bounds[origin] * scale)
    materialized = MaterializedAuditLinearProgram(
        objective=objective,
        coefficients=tuple(coefficients),
        bounds=tuple(bounds),
        row_units=descriptor.row_units,
        variable_units=descriptor.variable_units,
        trusted_box_lower_bounds=lower_bounds,
        trusted_box_upper_bounds=upper_bounds,
        objective_unit=base.objective_unit,
        objective_offset=base.objective_offset,
    )
    if materialized.digest != descriptor.linear_program_sha256:
        raise ValueError("audit variant materialization differs from its sealed identity")
    return materialized


def _descriptor(
    *,
    base: AuditLinearProgramBase,
    kind: AuditVariantKind,
    seed: str,
    variant_to_canonical_variables: tuple[int, ...],
    variant_to_canonical_rows: tuple[int | None, ...],
    row_roles: tuple[AuditRowRole, ...],
    row_scale_exponents: tuple[int, ...],
) -> AuditVariantDescriptor:
    row_units = tuple(
        LinearProgramConstraintUnit.DIMENSIONLESS if origin is None else base.row_units[origin]
        for origin in variant_to_canonical_rows
    )
    variable_units = tuple(
        base.variable_units[canonical] for canonical in variant_to_canonical_variables
    )
    provisional = AuditVariantDescriptor(
        variant_id=f"{base.base_id}--{kind.value}",
        base_id=base.base_id,
        base_sha256=base.digest,
        kind=kind,
        seed=seed,
        variant_to_canonical_variables=variant_to_canonical_variables,
        canonical_to_variant_variables=_inverse_permutation(variant_to_canonical_variables),
        variant_to_canonical_rows=variant_to_canonical_rows,
        canonical_to_variant_rows=_canonical_to_variant_rows(
            variant_to_canonical_rows,
            base.row_count,
        ),
        row_roles=row_roles,
        row_scale_exponents=row_scale_exponents,
        row_units=row_units,
        variable_units=variable_units,
        linear_program_sha256="0" * 64,
    )
    materialized = MaterializedAuditLinearProgram(
        objective=tuple(
            base.objective[canonical] for canonical in provisional.variant_to_canonical_variables
        ),
        coefficients=tuple(
            (0.0,) * base.variable_count
            if origin is None
            else tuple(
                base.coefficients[origin][canonical] * float(2**exponent)
                for canonical in provisional.variant_to_canonical_variables
            )
            for origin, exponent in zip(
                provisional.variant_to_canonical_rows,
                provisional.row_scale_exponents,
                strict=True,
            )
        ),
        bounds=tuple(
            0.0 if origin is None else base.bounds[origin] * float(2**exponent)
            for origin, exponent in zip(
                provisional.variant_to_canonical_rows,
                provisional.row_scale_exponents,
                strict=True,
            )
        ),
        row_units=provisional.row_units,
        variable_units=provisional.variable_units,
        trusted_box_lower_bounds=tuple(
            base.trusted_box_lower_bounds[canonical]
            for canonical in provisional.variant_to_canonical_variables
        ),
        trusted_box_upper_bounds=tuple(
            base.trusted_box_upper_bounds[canonical]
            for canonical in provisional.variant_to_canonical_variables
        ),
        objective_unit=base.objective_unit,
        objective_offset=base.objective_offset,
    )
    return AuditVariantDescriptor(
        variant_id=provisional.variant_id,
        base_id=provisional.base_id,
        base_sha256=provisional.base_sha256,
        kind=provisional.kind,
        seed=provisional.seed,
        variant_to_canonical_variables=provisional.variant_to_canonical_variables,
        canonical_to_variant_variables=provisional.canonical_to_variant_variables,
        variant_to_canonical_rows=provisional.variant_to_canonical_rows,
        canonical_to_variant_rows=provisional.canonical_to_variant_rows,
        row_roles=provisional.row_roles,
        row_scale_exponents=provisional.row_scale_exponents,
        row_units=provisional.row_units,
        variable_units=provisional.variable_units,
        linear_program_sha256=materialized.digest,
    )


def build_audit_variant_descriptors(
    base: AuditLinearProgramBase,
) -> tuple[AuditVariantDescriptor, ...]:
    """Build the five frozen exact representations for one base."""

    if not isinstance(base, AuditLinearProgramBase):
        raise TypeError("audit variants require a semantic LP base")
    seed = f"{ADR0311_TRANSFORM_SEED_PREFIX}:{base.digest}"
    stream = Sha256CounterStream(seed)
    identity_variables = tuple(range(base.variable_count))
    identity_rows: tuple[int | None, ...] = tuple(range(base.row_count))
    original_roles = (AuditRowRole.ORIGINAL,) * base.row_count
    zero_scales = (0,) * base.row_count
    canonical = _descriptor(
        base=base,
        kind=AuditVariantKind.CANONICAL,
        seed=seed,
        variant_to_canonical_variables=identity_variables,
        variant_to_canonical_rows=identity_rows,
        row_roles=original_roles,
        row_scale_exponents=zero_scales,
    )
    row_permutation = tuple(fisher_yates_order(stream, base.row_count))
    permuted_rows = _descriptor(
        base=base,
        kind=AuditVariantKind.ROW_PERMUTATION,
        seed=seed,
        variant_to_canonical_variables=identity_variables,
        variant_to_canonical_rows=row_permutation,
        row_roles=original_roles,
        row_scale_exponents=zero_scales,
    )
    variable_permutation = fisher_yates_order(stream, base.variable_count)
    permuted_variables = _descriptor(
        base=base,
        kind=AuditVariantKind.VARIABLE_PERMUTATION,
        seed=seed,
        variant_to_canonical_variables=variable_permutation,
        variant_to_canonical_rows=identity_rows,
        row_roles=original_roles,
        row_scale_exponents=zero_scales,
    )
    scaled_row_order = fisher_yates_order(stream, base.row_count)
    scale_exponents = tuple(
        _DYADIC_SCALE_EXPONENTS[stream.randbelow(len(_DYADIC_SCALE_EXPONENTS))]
        for _ in range(base.row_count)
    )
    scaled_rows = _descriptor(
        base=base,
        kind=AuditVariantKind.DYADIC_ROW_SCALING,
        seed=seed,
        variant_to_canonical_variables=identity_variables,
        variant_to_canonical_rows=scaled_row_order,
        row_roles=original_roles,
        row_scale_exponents=scale_exponents,
    )
    duplicate_count = max(1, ceil(base.row_count / 8))
    duplicate_sources = fisher_yates_order(stream, base.row_count)[:duplicate_count]
    pre_origins: tuple[int | None, ...] = (
        *range(base.row_count),
        *duplicate_sources,
        None,
    )
    pre_roles = (
        *(AuditRowRole.ORIGINAL for _ in range(base.row_count)),
        *(AuditRowRole.DUPLICATE for _ in range(duplicate_count)),
        AuditRowRole.ZERO_REDUNDANCY,
    )
    final_row_order = fisher_yates_order(stream, len(pre_origins))
    redundancy_origins = tuple(pre_origins[index] for index in final_row_order)
    redundancy_roles = tuple(pre_roles[index] for index in final_row_order)
    redundancy = _descriptor(
        base=base,
        kind=AuditVariantKind.REDUNDANCY,
        seed=seed,
        variant_to_canonical_variables=identity_variables,
        variant_to_canonical_rows=redundancy_origins,
        row_roles=redundancy_roles,
        row_scale_exponents=(0,) * len(redundancy_origins),
    )
    return canonical, permuted_rows, permuted_variables, scaled_rows, redundancy


def _base_from_micro(case: ExactMicroLinearProgram) -> AuditLinearProgramBase:
    return AuditLinearProgramBase(
        base_id=case.case_id,
        family=AuditBaseFamily.EXACT_MICRO,
        source_input_sha256=case.digest,
        context_id=None,
        bet_sizes=None,
        objective=tuple(float(value) for value in case.objective),
        coefficients=tuple(tuple(float(value) for value in row) for row in case.coefficients),
        bounds=tuple(float(value) for value in case.bounds),
        row_units=(LinearProgramConstraintUnit.DIMENSIONLESS,) * len(case.coefficients),
        variable_units=(LinearProgramVariableUnit.DIMENSIONLESS_GENERIC,) * case.variable_count,
        trusted_box_lower_bounds=(0.0,) * case.variable_count,
        trusted_box_upper_bounds=tuple(float(value) for value in case.upper_bounds),
        objective_unit=LinearProgramObjectiveUnit.DIMENSIONLESS,
        objective_offset=0.0,
    )


def _sizing_input_digest(
    *,
    context: AuditWidthFourContext,
    arm: AuditSizingArm,
    bet_sizes: tuple[int, ...],
    compiled: ReducedRiverSizingLinearProgram,
    known_regression: bool,
) -> str:
    payload: dict[str, object] = {
        "arm": arm.value,
        "bet_sizes": bet_sizes,
        "compiled_lp_sha256": compiled.digest,
        "context": context.canonical_payload,
        "context_sha256": context.digest,
        "known_regression": known_regression,
        "version": "adr0311-reduced-sizing-audit-input-v1",
    }
    if known_regression:
        payload["adr0310_binding_sha256"] = ADR0311_KNOWN_BINDING_SHA256
        payload["adr0310_failure_sha256"] = ADR0311_KNOWN_FAILURE_SHA256
        payload["adr0310_oracle_context_sha256"] = ADR0311_KNOWN_ORACLE_CONTEXT_SHA256
        payload["adr0310_structural_context_sha256"] = ADR0311_KNOWN_STRUCTURAL_CONTEXT_SHA256
    return _digest_payload(payload)


def _base_from_sizing(
    *,
    context: AuditWidthFourContext,
    arm: AuditSizingArm,
    base_id: str,
    known_regression: bool = False,
) -> AuditLinearProgramBase:
    bet_sizes = (
        (context.minimum_bet, context.stack)
        if arm is AuditSizingArm.MINIMUM_ALL_IN
        else tuple(range(context.minimum_bet, context.stack + 1))
    )
    compiled = compile_reduced_river_sizing_lp(
        pot=context.pot,
        stack=context.stack,
        minimum_bet=context.minimum_bet,
        joint_probabilities=tuple(
            tuple(probability.fraction for probability in row)
            for row in context.joint_probabilities
        ),
        showdown_signs=context.showdown_signs,
        bet_sizes=bet_sizes,
    )
    return AuditLinearProgramBase(
        base_id=base_id,
        family=(
            AuditBaseFamily.KNOWN_REGRESSION
            if known_regression
            else AuditBaseFamily.FRESH_REDUCED_SIZING
        ),
        source_input_sha256=_sizing_input_digest(
            context=context,
            arm=arm,
            bet_sizes=bet_sizes,
            compiled=compiled,
            known_regression=known_regression,
        ),
        context_id=context.context_id,
        bet_sizes=bet_sizes,
        objective=compiled.objective,
        coefficients=compiled.coefficients,
        bounds=compiled.bounds,
        row_units=compiled.row_units,
        variable_units=compiled.variable_units,
        trusted_box_lower_bounds=compiled.trusted_box_lower_bounds,
        trusted_box_upper_bounds=compiled.trusted_box_upper_bounds,
        objective_unit=compiled.objective_unit,
        objective_offset=compiled.objective_offset_chips,
    )


def build_adr0311_known_regression_context() -> AuditWidthFourContext:
    """Reconstruct only ADR-0310's already-disclosed failing input context."""

    weights = (
        (8, 8, 4, 8),
        (5, 8, 7, 5),
        (7, 8, 6, 1),
        (9, 4, 6, 3),
    )
    return AuditWidthFourContext(
        context_id="adr0305-v4-qualified-b-c21",
        board=(17, 10, 49, 50, 38),
        pot=24,
        stack=30,
        minimum_bet=2,
        opener_hands=((24, 46), (34, 39), (11, 27), (3, 14)),
        responder_hands=((28, 35), (30, 45), (19, 25), (41, 48)),
        joint_probabilities=tuple(
            tuple(AuditExactProbability(value, 97) for value in row) for row in weights
        ),
    )


@dataclass(frozen=True, slots=True)
class NativeSimplexAuditCorpus:
    micro_structure: ExactMicroLpStructure
    width_four_structure: FreshWidthFourAuditStructure
    bases: tuple[AuditLinearProgramBase, ...]
    variants: tuple[AuditVariantDescriptor, ...]

    def __post_init__(self) -> None:
        if self.micro_structure.digest != ADR0311_MICRO_STRUCTURE_SHA256:
            raise ValueError("audit corpus micro structure identity drifted")
        if self.width_four_structure.digest != ADR0311_WIDTH4_STRUCTURE_SHA256:
            raise ValueError("audit corpus width-four structure identity drifted")
        if not isinstance(self.bases, tuple) or len(self.bases) != ADR0311_BASE_COUNT:
            raise TypeError("audit corpus has the wrong immutable base count")
        if any(not isinstance(base, AuditLinearProgramBase) for base in self.bases):
            raise TypeError("audit corpus contains a nonsemantic base")
        expected_base_ids = (
            ADR0311_KNOWN_REGRESSION_BASE_ID,
            *(case.case_id for case in self.micro_structure.cases),
            *(
                f"{context.context_id}-{arm.value}"
                for context in self.width_four_structure.contexts
                for arm in AuditSizingArm
            ),
        )
        if tuple(base.base_id for base in self.bases) != expected_base_ids:
            raise ValueError("audit base ids or ordering differ from ADR-0311")
        if len({base.digest for base in self.bases}) != len(self.bases):
            raise ValueError("audit corpus repeats a base identity")
        if not isinstance(self.variants, tuple) or len(self.variants) != ADR0311_VARIANT_COUNT:
            raise TypeError("audit corpus has the wrong immutable variant count")
        if any(not isinstance(variant, AuditVariantDescriptor) for variant in self.variants):
            raise TypeError("audit corpus contains a nonsemantic variant")
        expected_variant_ids = tuple(
            f"{base.base_id}--{kind.value}" for base in self.bases for kind in AuditVariantKind
        )
        if tuple(variant.variant_id for variant in self.variants) != expected_variant_ids:
            raise ValueError("audit variant ids or ordering differ from ADR-0311")
        if len({variant.digest for variant in self.variants}) != len(self.variants):
            raise ValueError("audit corpus repeats a variant identity")
        by_id = {base.base_id: base for base in self.bases}
        for variant in self.variants:
            base = by_id[variant.base_id]
            if variant.base_sha256 != base.digest:
                raise ValueError("audit variant base identity drifted")
            if variant.seed != f"{ADR0311_TRANSFORM_SEED_PREFIX}:{base.digest}":
                raise ValueError("audit variant seed differs from its base identity")
            if variant.variable_units != tuple(
                base.variable_units[canonical]
                for canonical in variant.variant_to_canonical_variables
            ):
                raise ValueError("audit variant variable units drifted under permutation")
            if variant.row_units != tuple(
                LinearProgramConstraintUnit.DIMENSIONLESS
                if origin is None
                else base.row_units[origin]
                for origin in variant.variant_to_canonical_rows
            ):
                raise ValueError("audit variant row units drifted under transformation")
            materialize_audit_variant(base=base, descriptor=variant)
        if self.bases[0].source_input_sha256 != ADR0311_KNOWN_REGRESSION_INPUT_SHA256:
            raise ValueError("known regression input identity drifted")
        if self.base_corpus_digest != ADR0311_BASE_CORPUS_SHA256:
            raise ValueError("audit base corpus identity drifted")
        if self.variant_corpus_digest != ADR0311_VARIANT_CORPUS_SHA256:
            raise ValueError("audit variant corpus identity drifted")
        if self.digest != ADR0311_COMPLETE_CORPUS_SHA256:
            raise ValueError("complete audit corpus identity drifted")

    @property
    def base_corpus_digest(self) -> str:
        return _digest_payload(
            {
                "base_sha256": tuple(base.digest for base in self.bases),
                "known_regression_input_sha256": self.bases[0].source_input_sha256,
                "micro_structure_sha256": self.micro_structure.digest,
                "version": "adr0311-audit-base-corpus-v1",
                "width_four_structure_sha256": self.width_four_structure.digest,
            }
        )

    @property
    def variant_corpus_digest(self) -> str:
        return _digest_payload(
            {
                "transform_seed_prefix": ADR0311_TRANSFORM_SEED_PREFIX,
                "transform_version": ADR0311_TRANSFORM_VERSION,
                "variant_sha256": tuple(variant.digest for variant in self.variants),
                "version": "adr0311-audit-variant-corpus-v1",
            }
        )

    @property
    def digest(self) -> str:
        return _digest_payload(
            {
                "base_corpus_sha256": self.base_corpus_digest,
                "base_count": len(self.bases),
                "variant_corpus_sha256": self.variant_corpus_digest,
                "variant_count": len(self.variants),
                "version": "adr0311-complete-value-free-audit-corpus-v1",
            }
        )


def build_adr0311_native_simplex_audit_corpus() -> NativeSimplexAuditCorpus:
    """Build all sealed inputs and exact representations, but open no result."""

    micro = build_adr0311_micro_lp_structure()
    width_four = build_adr0311_width_four_structure()
    known = _base_from_sizing(
        context=build_adr0311_known_regression_context(),
        arm=AuditSizingArm.FULL_INTEGER,
        base_id=ADR0311_KNOWN_REGRESSION_BASE_ID,
        known_regression=True,
    )
    bases = (
        known,
        *(_base_from_micro(case) for case in micro.cases),
        *(
            _base_from_sizing(
                context=context,
                arm=arm,
                base_id=f"{context.context_id}-{arm.value}",
            )
            for context in width_four.contexts
            for arm in AuditSizingArm
        ),
    )
    variants = tuple(variant for base in bases for variant in build_audit_variant_descriptors(base))
    return NativeSimplexAuditCorpus(
        micro_structure=micro,
        width_four_structure=width_four,
        bases=bases,
        variants=variants,
    )


__all__ = [
    "ADR0311_BASE_CORPUS_SHA256",
    "ADR0311_BASE_COUNT",
    "ADR0311_COMPLETE_CORPUS_SHA256",
    "ADR0311_KNOWN_BINDING_SHA256",
    "ADR0311_KNOWN_FAILURE_SHA256",
    "ADR0311_KNOWN_ORACLE_CONTEXT_SHA256",
    "ADR0311_KNOWN_REGRESSION_BASE_ID",
    "ADR0311_KNOWN_REGRESSION_INPUT_SHA256",
    "ADR0311_KNOWN_STRUCTURAL_CONTEXT_SHA256",
    "ADR0311_TRANSFORM_SEED_PREFIX",
    "ADR0311_TRANSFORM_VERSION",
    "ADR0311_VARIANTS_PER_BASE",
    "ADR0311_VARIANT_CORPUS_SHA256",
    "ADR0311_VARIANT_COUNT",
    "AuditBaseFamily",
    "AuditLinearProgramBase",
    "AuditRowRole",
    "AuditSizingArm",
    "AuditVariantDescriptor",
    "AuditVariantKind",
    "MaterializedAuditLinearProgram",
    "NativeSimplexAuditCorpus",
    "build_adr0311_known_regression_context",
    "build_adr0311_native_simplex_audit_corpus",
    "build_audit_variant_descriptors",
    "materialize_audit_variant",
]
