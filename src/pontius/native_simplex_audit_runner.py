"""Owned execution and result schemas for ADR-0311's sealed LP audit.

This module deliberately separates preparation from execution.  Importing it,
building a schedule, and exercising the helpers on hand-authored toys invokes
no sealed LP.  The sealed entry point verifies the committed source seal,
runtime identities, corpus identity, and complete schedule before the first
backend call.
"""

from __future__ import annotations

import json
import sys
import traceback
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import StrEnum
from fractions import Fraction
from hashlib import sha256
from importlib import import_module
from itertools import combinations
from math import fsum, isfinite
from pathlib import Path
from platform import python_implementation
from time import perf_counter
from typing import Any

from .linear_program import maximize_linear_program
from .linear_program_certificate import (
    BoundedMinimizationCertificate,
    certify_bounded_minimization_lower_bound,
)
from .native_simplex_audit_corpus import (
    ADR0311_COMPLETE_CORPUS_SHA256,
    ADR0311_KNOWN_REGRESSION_BASE_ID,
    ADR0311_VARIANT_COUNT,
    AuditBaseFamily,
    AuditLinearProgramBase,
    AuditVariantDescriptor,
    AuditVariantKind,
    MaterializedAuditLinearProgram,
    NativeSimplexAuditCorpus,
    build_adr0311_known_regression_context,
    materialize_audit_variant,
)
from .native_simplex_audit_structures import (
    AuditWidthFourContext,
    ExactMicroLinearProgram,
)
from .reduced_river_sizing_lp import (
    LinearProgramConstraintUnit,
    LinearProgramVariableUnit,
    compile_reduced_river_sizing_lp,
)

ADR0313_RUNNER_VERSION = "candidate-independent-native-simplex-audit-runner-v1"
ADR0313_EXPECTED_INVOCATION_COUNT = 2_655
ADR0313_EXPECTED_PYTHON_IMPLEMENTATION = "CPython"
ADR0313_EXPECTED_PYTHON_VERSION = "3.14.6"
ADR0313_EXPECTED_NUMPY_VERSION = "2.5.2"
ADR0313_EXPECTED_SCIPY_VERSION = "1.18.0"
ADR0313_EXPECTED_HIGHS_VERSION = "1.12.0"
ADR0311_KNOWN_NATIVE_FAILURE_PIVOTS = 375
ADR0311_KNOWN_NATIVE_FAILURE_ROW = 215
ADR0311_KNOWN_NATIVE_FAILURE_MAXIMUM_RESIDUAL = 4.049601922810204
ADR0311_KNOWN_NATIVE_FAILURE_VERIFICATION_ALLOWANCE = 4.199999999999999e-8


def _require_positive_finite(value: object, *, label: str) -> float:
    if not isinstance(value, float) or not isfinite(value) or value <= 0.0:
        raise ValueError(f"{label} must be a positive finite float")
    return value


def _require_nonnegative_finite(value: object, *, label: str) -> float:
    if not isinstance(value, float) or not isfinite(value) or value < 0.0:
        raise ValueError(f"{label} must be a nonnegative finite float")
    return value


def _require_finite_tuple(
    values: object,
    *,
    label: str,
    allow_empty: bool = True,
) -> tuple[float, ...]:
    if not isinstance(values, tuple) or (not allow_empty and not values):
        raise TypeError(f"{label} must be an immutable float tuple")
    if any(not isinstance(value, float) or not isfinite(value) for value in values):
        raise ValueError(f"{label} must contain finite floats")
    return values


def _canonical_audit_value(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("audit evidence cannot encode a nonfinite float")
        return {"float_hex": value.hex()}
    if isinstance(value, Fraction):
        return {
            "fraction": (value.numerator, value.denominator),
        }
    if isinstance(value, tuple):
        return tuple(_canonical_audit_value(item) for item in value)
    if isinstance(value, list):
        return tuple(_canonical_audit_value(item) for item in value)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("audit evidence mapping keys must be text")
        return {key: _canonical_audit_value(item) for key, item in sorted(value.items())}
    if is_dataclass(value) and not isinstance(value, type):
        return {
            "dataclass": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": {
                field.name: _canonical_audit_value(getattr(value, field.name))
                for field in fields(value)
            },
        }
    raise TypeError(f"audit evidence cannot encode {type(value).__qualname__}")


def canonical_audit_bytes(value: object) -> bytes:
    """Return deterministic exact-float JSON bytes for an audit result schema."""

    return json.dumps(
        _canonical_audit_value(value),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


@dataclass(frozen=True, slots=True)
class MicroPrimalAllowance:
    value: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.value, label="micro primal allowance")


@dataclass(frozen=True, slots=True)
class MicroDualAllowance:
    value: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.value, label="micro dual allowance")


@dataclass(frozen=True, slots=True)
class MicroObjectiveAllowance:
    value: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.value, label="micro objective allowance")


@dataclass(frozen=True, slots=True)
class MicroVariantComparisonAllowance:
    value: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.value, label="micro variant-comparison allowance")


@dataclass(frozen=True, slots=True)
class PolicyNonnegativityAllowance:
    value: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.value, label="policy nonnegativity allowance")


@dataclass(frozen=True, slots=True)
class PolicySimplexMassAllowance:
    value: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.value, label="policy simplex-mass allowance")


@dataclass(frozen=True, slots=True)
class EnvelopeFeasibilityAllowance:
    chips: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.chips, label="envelope feasibility allowance")


@dataclass(frozen=True, slots=True)
class SizingObjectiveAllowance:
    chips: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.chips, label="sizing objective allowance")


@dataclass(frozen=True, slots=True)
class SizingCertificateWidthAllowance:
    chips: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.chips, label="sizing certificate-width allowance")


@dataclass(frozen=True, slots=True)
class CrossBackendSizingComparisonAllowance:
    chips: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.chips, label="cross-backend sizing allowance")


@dataclass(frozen=True, slots=True)
class CrossVariantSizingComparisonAllowance:
    chips: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.chips, label="cross-variant sizing allowance")


ADR0311_MICRO_PRIMAL_ALLOWANCE = MicroPrimalAllowance(1e-9)
ADR0311_MICRO_DUAL_ALLOWANCE = MicroDualAllowance(1e-9)
ADR0311_MICRO_OBJECTIVE_ALLOWANCE = MicroObjectiveAllowance(1e-9)
ADR0311_MICRO_VARIANT_COMPARISON_ALLOWANCE = MicroVariantComparisonAllowance(1e-9)
ADR0311_POLICY_NONNEGATIVITY_ALLOWANCE = PolicyNonnegativityAllowance(1e-9)
ADR0311_POLICY_SIMPLEX_MASS_ALLOWANCE = PolicySimplexMassAllowance(1e-9)
ADR0311_ENVELOPE_FEASIBILITY_ALLOWANCE = EnvelopeFeasibilityAllowance(1e-9)
ADR0311_SIZING_OBJECTIVE_ALLOWANCE = SizingObjectiveAllowance(1e-9)
ADR0311_SIZING_CERTIFICATE_WIDTH_ALLOWANCE = SizingCertificateWidthAllowance(1e-9)
ADR0311_CROSS_BACKEND_SIZING_ALLOWANCE = CrossBackendSizingComparisonAllowance(1e-9)
ADR0311_CROSS_VARIANT_SIZING_ALLOWANCE = CrossVariantSizingComparisonAllowance(1e-9)


class AuditBackend(StrEnum):
    NATIVE = "native"
    HIGHS_DS = "highs-ds"
    HIGHS_IPM = "highs-ipm"


ADR0311_BACKEND_ORDER = (
    AuditBackend.NATIVE,
    AuditBackend.HIGHS_DS,
    AuditBackend.HIGHS_IPM,
)


@dataclass(frozen=True, slots=True)
class NativeBackendOptions:
    tolerance: float
    maximum_pivots: int

    def __post_init__(self) -> None:
        _require_positive_finite(self.tolerance, label="native solver tolerance")
        if (
            isinstance(self.maximum_pivots, bool)
            or not isinstance(self.maximum_pivots, int)
            or self.maximum_pivots <= 0
        ):
            raise ValueError("native maximum pivots must be positive")


@dataclass(frozen=True, slots=True)
class HighsDualSimplexOptions:
    method: str
    presolve: bool
    primal_feasibility_tolerance: float
    dual_feasibility_tolerance: float
    maximum_iterations: int

    def __post_init__(self) -> None:
        if self.method != AuditBackend.HIGHS_DS.value:
            raise ValueError("dual-simplex method differs from the frozen backend")
        if self.presolve is not True:
            raise ValueError("dual-simplex presolve must remain enabled")
        _require_positive_finite(
            self.primal_feasibility_tolerance,
            label="dual-simplex primal tolerance",
        )
        _require_positive_finite(
            self.dual_feasibility_tolerance,
            label="dual-simplex dual tolerance",
        )
        if (
            isinstance(self.maximum_iterations, bool)
            or not isinstance(self.maximum_iterations, int)
            or self.maximum_iterations <= 0
        ):
            raise ValueError("dual-simplex maximum iterations must be positive")

    @property
    def scipy_options(self) -> dict[str, object]:
        return {
            "presolve": self.presolve,
            "primal_feasibility_tolerance": self.primal_feasibility_tolerance,
            "dual_feasibility_tolerance": self.dual_feasibility_tolerance,
            "maxiter": self.maximum_iterations,
        }


@dataclass(frozen=True, slots=True)
class HighsInteriorPointOptions:
    method: str
    presolve: bool
    primal_feasibility_tolerance: float
    dual_feasibility_tolerance: float
    ipm_optimality_tolerance: float
    maximum_iterations: int

    def __post_init__(self) -> None:
        if self.method != AuditBackend.HIGHS_IPM.value:
            raise ValueError("interior-point method differs from the frozen backend")
        if self.presolve is not True:
            raise ValueError("interior-point presolve must remain enabled")
        for label, value in (
            ("interior-point primal tolerance", self.primal_feasibility_tolerance),
            ("interior-point dual tolerance", self.dual_feasibility_tolerance),
            ("interior-point optimality tolerance", self.ipm_optimality_tolerance),
        ):
            _require_positive_finite(value, label=label)
        if (
            isinstance(self.maximum_iterations, bool)
            or not isinstance(self.maximum_iterations, int)
            or self.maximum_iterations <= 0
        ):
            raise ValueError("interior-point maximum iterations must be positive")

    @property
    def scipy_options(self) -> dict[str, object]:
        return {
            "presolve": self.presolve,
            "primal_feasibility_tolerance": self.primal_feasibility_tolerance,
            "dual_feasibility_tolerance": self.dual_feasibility_tolerance,
            "ipm_optimality_tolerance": self.ipm_optimality_tolerance,
            "maxiter": self.maximum_iterations,
        }


ADR0311_NATIVE_OPTIONS = NativeBackendOptions(1e-11, 4_096)
ADR0311_HIGHS_DS_OPTIONS = HighsDualSimplexOptions(
    method="highs-ds",
    presolve=True,
    primal_feasibility_tolerance=1e-10,
    dual_feasibility_tolerance=1e-10,
    maximum_iterations=4_096,
)
ADR0311_HIGHS_IPM_OPTIONS = HighsInteriorPointOptions(
    method="highs-ipm",
    presolve=True,
    primal_feasibility_tolerance=1e-10,
    dual_feasibility_tolerance=1e-10,
    ipm_optimality_tolerance=1e-12,
    maximum_iterations=4_096,
)


@dataclass(frozen=True, slots=True)
class AuditProtocolIdentity:
    backend_order: tuple[AuditBackend, ...]
    native_options: NativeBackendOptions
    highs_ds_options: HighsDualSimplexOptions
    highs_ipm_options: HighsInteriorPointOptions
    micro_primal_allowance: MicroPrimalAllowance
    micro_dual_allowance: MicroDualAllowance
    micro_objective_allowance: MicroObjectiveAllowance
    micro_variant_comparison_allowance: MicroVariantComparisonAllowance
    policy_nonnegativity_allowance: PolicyNonnegativityAllowance
    policy_simplex_mass_allowance: PolicySimplexMassAllowance
    envelope_feasibility_allowance: EnvelopeFeasibilityAllowance
    sizing_objective_allowance: SizingObjectiveAllowance
    sizing_certificate_width_allowance: SizingCertificateWidthAllowance
    cross_backend_sizing_allowance: CrossBackendSizingComparisonAllowance
    cross_variant_sizing_allowance: CrossVariantSizingComparisonAllowance
    expected_invocation_count: int

    def __post_init__(self) -> None:
        if self.backend_order != ADR0311_BACKEND_ORDER:
            raise ValueError("audit protocol backend order drifted")
        semantic_fields = (
            (self.native_options, NativeBackendOptions),
            (self.highs_ds_options, HighsDualSimplexOptions),
            (self.highs_ipm_options, HighsInteriorPointOptions),
            (self.micro_primal_allowance, MicroPrimalAllowance),
            (self.micro_dual_allowance, MicroDualAllowance),
            (self.micro_objective_allowance, MicroObjectiveAllowance),
            (self.micro_variant_comparison_allowance, MicroVariantComparisonAllowance),
            (self.policy_nonnegativity_allowance, PolicyNonnegativityAllowance),
            (self.policy_simplex_mass_allowance, PolicySimplexMassAllowance),
            (self.envelope_feasibility_allowance, EnvelopeFeasibilityAllowance),
            (self.sizing_objective_allowance, SizingObjectiveAllowance),
            (self.sizing_certificate_width_allowance, SizingCertificateWidthAllowance),
            (self.cross_backend_sizing_allowance, CrossBackendSizingComparisonAllowance),
            (self.cross_variant_sizing_allowance, CrossVariantSizingComparisonAllowance),
        )
        if any(not isinstance(value, expected) for value, expected in semantic_fields):
            raise TypeError("audit protocol contains a nonsemantic option or allowance")
        if self.expected_invocation_count != ADR0313_EXPECTED_INVOCATION_COUNT:
            raise ValueError("audit protocol invocation count drifted")


ADR0313_PROTOCOL = AuditProtocolIdentity(
    backend_order=ADR0311_BACKEND_ORDER,
    native_options=ADR0311_NATIVE_OPTIONS,
    highs_ds_options=ADR0311_HIGHS_DS_OPTIONS,
    highs_ipm_options=ADR0311_HIGHS_IPM_OPTIONS,
    micro_primal_allowance=ADR0311_MICRO_PRIMAL_ALLOWANCE,
    micro_dual_allowance=ADR0311_MICRO_DUAL_ALLOWANCE,
    micro_objective_allowance=ADR0311_MICRO_OBJECTIVE_ALLOWANCE,
    micro_variant_comparison_allowance=ADR0311_MICRO_VARIANT_COMPARISON_ALLOWANCE,
    policy_nonnegativity_allowance=ADR0311_POLICY_NONNEGATIVITY_ALLOWANCE,
    policy_simplex_mass_allowance=ADR0311_POLICY_SIMPLEX_MASS_ALLOWANCE,
    envelope_feasibility_allowance=ADR0311_ENVELOPE_FEASIBILITY_ALLOWANCE,
    sizing_objective_allowance=ADR0311_SIZING_OBJECTIVE_ALLOWANCE,
    sizing_certificate_width_allowance=ADR0311_SIZING_CERTIFICATE_WIDTH_ALLOWANCE,
    cross_backend_sizing_allowance=ADR0311_CROSS_BACKEND_SIZING_ALLOWANCE,
    cross_variant_sizing_allowance=ADR0311_CROSS_VARIANT_SIZING_ALLOWANCE,
    expected_invocation_count=ADR0313_EXPECTED_INVOCATION_COUNT,
)


@dataclass(frozen=True, slots=True)
class AuditEnvironmentIdentity:
    python_implementation: str
    python_version: str
    numpy_version: str
    scipy_version: str
    highs_version: str

    def __post_init__(self) -> None:
        for label, value in (
            ("Python implementation", self.python_implementation),
            ("Python version", self.python_version),
            ("NumPy version", self.numpy_version),
            ("SciPy version", self.scipy_version),
            ("HiGHS version", self.highs_version),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} identity must be nonempty")


ADR0313_EXPECTED_ENVIRONMENT = AuditEnvironmentIdentity(
    python_implementation=ADR0313_EXPECTED_PYTHON_IMPLEMENTATION,
    python_version=ADR0313_EXPECTED_PYTHON_VERSION,
    numpy_version=ADR0313_EXPECTED_NUMPY_VERSION,
    scipy_version=ADR0313_EXPECTED_SCIPY_VERSION,
    highs_version=ADR0313_EXPECTED_HIGHS_VERSION,
)


def capture_audit_environment_identity() -> AuditEnvironmentIdentity:
    """Capture the exact optional runtime without opening an LP."""

    numpy = import_module("numpy")
    scipy = import_module("scipy")
    highs_core = import_module("scipy.optimize._highspy._core")
    highs_version = ".".join(
        str(getattr(highs_core, field))
        for field in (
            "HIGHS_VERSION_MAJOR",
            "HIGHS_VERSION_MINOR",
            "HIGHS_VERSION_PATCH",
        )
    )
    return AuditEnvironmentIdentity(
        python_implementation=python_implementation(),
        python_version=".".join(str(value) for value in sys.version_info[:3]),
        numpy_version=str(numpy.__version__),
        scipy_version=str(scipy.__version__),
        highs_version=highs_version,
    )


@dataclass(frozen=True, slots=True)
class ExactRational:
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if isinstance(self.numerator, bool) or not isinstance(self.numerator, int):
            raise TypeError("exact numerator must be an integer")
        if (
            isinstance(self.denominator, bool)
            or not isinstance(self.denominator, int)
            or self.denominator <= 0
        ):
            raise ValueError("exact denominator must be positive")
        canonical = Fraction(self.numerator, self.denominator)
        if (canonical.numerator, canonical.denominator) != (
            self.numerator,
            self.denominator,
        ):
            raise ValueError("exact rational must be reduced with a positive denominator")

    @classmethod
    def from_fraction(cls, value: Fraction) -> ExactRational:
        if not isinstance(value, Fraction):
            raise TypeError("exact rational conversion requires Fraction")
        return cls(value.numerator, value.denominator)

    @property
    def fraction(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)


@dataclass(frozen=True, slots=True)
class ExactMicroEnumeration:
    case_id: str
    active_set_count: int
    nonsingular_system_count: int
    feasible_active_system_count: int
    vertex_count: int
    maximizer_count: int
    optimum: ExactRational
    lexicographically_smallest_maximizer: tuple[ExactRational, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.case_id, str) or not self.case_id:
            raise ValueError("exact enumeration case id must be nonempty")
        for label, value in (
            ("active-set count", self.active_set_count),
            ("nonsingular-system count", self.nonsingular_system_count),
            ("feasible-system count", self.feasible_active_system_count),
            ("vertex count", self.vertex_count),
            ("maximizer count", self.maximizer_count),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"exact {label} must be positive")
        if not isinstance(self.optimum, ExactRational):
            raise TypeError("exact optimum must be rational")
        if (
            not isinstance(self.lexicographically_smallest_maximizer, tuple)
            or not self.lexicographically_smallest_maximizer
            or any(
                not isinstance(value, ExactRational)
                for value in self.lexicographically_smallest_maximizer
            )
        ):
            raise TypeError("exact maximizing vertex must be an immutable rational tuple")
        if self.maximizer_count > self.vertex_count:
            raise ValueError("exact maximizer count exceeds the vertex count")


def _solve_fraction_square_system(
    coefficients: Sequence[Sequence[Fraction]],
    bounds: Sequence[Fraction],
) -> tuple[Fraction, ...] | None:
    width = len(bounds)
    if len(coefficients) != width or any(len(row) != width for row in coefficients):
        raise ValueError("exact Gaussian elimination requires a square system")
    augmented = [list(row) + [bound] for row, bound in zip(coefficients, bounds, strict=True)]
    for column in range(width):
        pivot = next(
            (row for row in range(column, width) if augmented[row][column] != 0),
            None,
        )
        if pivot is None:
            return None
        if pivot != column:
            augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        pivot_value = augmented[column][column]
        augmented[column] = [value / pivot_value for value in augmented[column]]
        for row in range(width):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor == 0:
                continue
            augmented[row] = [
                left - factor * right
                for left, right in zip(augmented[row], augmented[column], strict=True)
            ]
    return tuple(augmented[row][-1] for row in range(width))


def enumerate_exact_micro_vertices(case: ExactMicroLinearProgram) -> ExactMicroEnumeration:
    """Enumerate all distinct vertices of one exact micro LP."""

    if not isinstance(case, ExactMicroLinearProgram):
        raise TypeError("exact micro enumeration requires a sealed-structure input")
    width = case.variable_count
    original_rows = tuple(tuple(Fraction(value) for value in row) for row in case.coefficients)
    original_bounds = tuple(Fraction(value) for value in case.bounds)
    nonnegative_boundaries = tuple(
        tuple(Fraction(column == variable) for column in range(width)) for variable in range(width)
    )
    boundary_rows = (*original_rows, *nonnegative_boundaries)
    boundary_bounds = (*original_bounds, *(Fraction(0) for _ in range(width)))
    vertices: set[tuple[Fraction, ...]] = set()
    active_set_count = 0
    nonsingular_count = 0
    feasible_system_count = 0
    for active in combinations(range(len(boundary_rows)), width):
        active_set_count += 1
        vertex = _solve_fraction_square_system(
            tuple(boundary_rows[index] for index in active),
            tuple(boundary_bounds[index] for index in active),
        )
        if vertex is None:
            continue
        nonsingular_count += 1
        if any(value < 0 for value in vertex):
            continue
        if any(
            sum(
                (coefficient * value for coefficient, value in zip(row, vertex, strict=True)),
                start=Fraction(0),
            )
            > bound
            for row, bound in zip(original_rows, original_bounds, strict=True)
        ):
            continue
        feasible_system_count += 1
        vertices.add(vertex)
    if not vertices:
        raise AssertionError("exact micro enumeration found no feasible vertex")
    exact_objective = tuple(Fraction(value) for value in case.objective)
    values = {
        vertex: sum(
            (
                coefficient * coordinate
                for coefficient, coordinate in zip(exact_objective, vertex, strict=True)
            ),
            start=Fraction(0),
        )
        for vertex in vertices
    }
    optimum = max(values.values())
    maximizers = tuple(sorted(vertex for vertex, value in values.items() if value == optimum))
    return ExactMicroEnumeration(
        case_id=case.case_id,
        active_set_count=active_set_count,
        nonsingular_system_count=nonsingular_count,
        feasible_active_system_count=feasible_system_count,
        vertex_count=len(vertices),
        maximizer_count=len(maximizers),
        optimum=ExactRational.from_fraction(optimum),
        lexicographically_smallest_maximizer=tuple(
            ExactRational.from_fraction(value) for value in maximizers[0]
        ),
    )


class BackendTermination(StrEnum):
    OPTIMAL = "optimal"
    NONOPTIMAL_STATUS = "nonoptimal-status"
    EXCEPTION = "exception"


class DualHintConvention(StrEnum):
    MAXIMIZATION_NONNEGATIVE = "maximization-nonnegative"
    MINIMIZATION_NONPOSITIVE = "minimization-nonpositive"


class AuditFailureStage(StrEnum):
    INDEPENDENT_EXACT_ENUMERATION = "independent-exact-enumeration"
    BACKEND_INVOCATION = "backend-invocation"
    BACKEND_SCHEMA = "backend-schema"
    COORDINATE_RECONSTRUCTION = "coordinate-reconstruction"
    SEMANTIC_VERIFICATION = "semantic-verification"
    CERTIFICATE = "certificate"


@dataclass(frozen=True, slots=True)
class AuditExceptionRecord:
    stage: AuditFailureStage
    module: str
    qualname: str
    message: str
    arguments: tuple[str, ...]
    traceback_frames: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.stage, AuditFailureStage):
            raise TypeError("audit exception stage must be semantic")
        for label, value in (
            ("module", self.module),
            ("qualified name", self.qualname),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"audit exception {label} must be nonempty")
        if not isinstance(self.message, str):
            raise TypeError("audit exception message must be text")
        if not isinstance(self.arguments, tuple) or any(
            not isinstance(value, str) for value in self.arguments
        ):
            raise TypeError("audit exception arguments must be immutable text")
        if not isinstance(self.traceback_frames, tuple) or any(
            not isinstance(value, str) or not value for value in self.traceback_frames
        ):
            raise TypeError("audit exception traceback frames must be immutable text")

    @classmethod
    def from_exception(
        cls,
        error: Exception,
        *,
        stage: AuditFailureStage,
    ) -> AuditExceptionRecord:
        frames = traceback.extract_tb(error.__traceback__)
        return cls(
            stage=stage,
            module=type(error).__module__,
            qualname=type(error).__qualname__,
            message=str(error),
            arguments=tuple(repr(value) for value in error.args),
            traceback_frames=tuple(
                f"{Path(frame.filename).name}:{frame.lineno}:{frame.name}" for frame in frames
            ),
        )


@dataclass(frozen=True, slots=True)
class NativeVerificationTrace:
    primal_variant_coordinates: tuple[float, ...] | None
    raw_maximization_objective: float | None
    dual_hint_variant_rows: tuple[float, ...] | None
    pivots: int | None
    constraint_residuals_variant_rows: tuple[float, ...] | None
    verification_allowance: float | None

    def __post_init__(self) -> None:
        for label, values in (
            ("native traced primal", self.primal_variant_coordinates),
            ("native traced dual", self.dual_hint_variant_rows),
            ("native traced residuals", self.constraint_residuals_variant_rows),
        ):
            if values is not None:
                _require_finite_tuple(values, label=label)
        for label, value in (
            ("native traced objective", self.raw_maximization_objective),
            ("native traced allowance", self.verification_allowance),
        ):
            if value is not None and (not isinstance(value, float) or not isfinite(value)):
                raise ValueError(f"{label} must be finite when present")
        if self.verification_allowance is not None and self.verification_allowance < 0.0:
            raise ValueError("native traced allowance must be nonnegative")
        if self.pivots is not None and (
            isinstance(self.pivots, bool) or not isinstance(self.pivots, int) or self.pivots < 0
        ):
            raise ValueError("native traced pivot count must be nonnegative")


def _extract_native_verification_trace(error: Exception) -> NativeVerificationTrace | None:
    current = error.__traceback__
    locals_found: Mapping[str, object] | None = None
    while current is not None:
        if current.tb_frame.f_code.co_name == "maximize_linear_program":
            locals_found = dict(current.tb_frame.f_locals)
        current = current.tb_next
    if locals_found is None:
        return None

    def finite_tuple(name: str) -> tuple[float, ...] | None:
        raw = locals_found.get(name)
        if not isinstance(raw, (tuple, list)):
            return None
        values = tuple(float(value) for value in raw)
        return values if all(isfinite(value) for value in values) else None

    def finite_float(name: str) -> float | None:
        raw = locals_found.get(name)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            return None
        value = float(raw)
        return value if isfinite(value) else None

    pivots_raw = locals_found.get("pivots")
    pivots = (
        pivots_raw
        if isinstance(pivots_raw, int) and not isinstance(pivots_raw, bool) and pivots_raw >= 0
        else None
    )
    trace = NativeVerificationTrace(
        primal_variant_coordinates=finite_tuple("variables"),
        raw_maximization_objective=finite_float("objective_value"),
        dual_hint_variant_rows=finite_tuple("dual_variables"),
        pivots=pivots,
        constraint_residuals_variant_rows=finite_tuple("violations"),
        verification_allowance=finite_float("allowed"),
    )
    return (
        trace
        if any(
            value is not None
            for value in (
                trace.primal_variant_coordinates,
                trace.raw_maximization_objective,
                trace.dual_hint_variant_rows,
                trace.pivots,
                trace.constraint_residuals_variant_rows,
                trace.verification_allowance,
            )
        )
        else None
    )


@dataclass(frozen=True, slots=True)
class BackendRawResult:
    backend: AuditBackend
    termination: BackendTermination
    status_code: int | None
    status_text: str
    message: str
    iterations: int | None
    crossover_iterations: int | None
    primal_variant_coordinates: tuple[float, ...] | None
    reported_maximization_objective: float | None
    dual_hint_variant_rows: tuple[float, ...] | None
    dual_hint_convention: DualHintConvention
    elapsed_seconds: float
    exception: AuditExceptionRecord | None = None
    native_verification_trace: NativeVerificationTrace | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.backend, AuditBackend):
            raise TypeError("raw backend result requires a semantic backend")
        if not isinstance(self.termination, BackendTermination):
            raise TypeError("raw backend termination must be semantic")
        if self.status_code is not None and (
            isinstance(self.status_code, bool) or not isinstance(self.status_code, int)
        ):
            raise TypeError("raw backend status code must be an integer")
        for label, value in (("status", self.status_text), ("message", self.message)):
            if not isinstance(value, str):
                raise TypeError(f"raw backend {label} must be text")
        for label, value in (
            ("iterations", self.iterations),
            ("crossover iterations", self.crossover_iterations),
        ):
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ValueError(f"raw backend {label} must be nonnegative")
        for label, values in (
            ("primal", self.primal_variant_coordinates),
            ("dual hint", self.dual_hint_variant_rows),
        ):
            if values is not None:
                _require_finite_tuple(values, label=f"raw backend {label}")
        if self.reported_maximization_objective is not None and (
            not isinstance(self.reported_maximization_objective, float)
            or not isfinite(self.reported_maximization_objective)
        ):
            raise ValueError("raw backend objective must be finite when present")
        if not isinstance(self.dual_hint_convention, DualHintConvention):
            raise TypeError("raw backend dual convention must be semantic")
        _require_nonnegative_finite(self.elapsed_seconds, label="raw backend elapsed time")
        if self.termination is BackendTermination.OPTIMAL:
            if self.exception is not None:
                raise ValueError("optimal backend result cannot carry an exception")
            if (
                self.primal_variant_coordinates is None
                or self.reported_maximization_objective is None
                or self.dual_hint_variant_rows is None
            ):
                raise ValueError("optimal backend result omits primal, objective, or dual hint")
        if self.termination is BackendTermination.EXCEPTION and self.exception is None:
            raise ValueError("exception backend result must bind its exception")
        if self.termination is not BackendTermination.EXCEPTION and self.exception is not None:
            raise ValueError("nonexception backend result cannot carry an exception")
        if self.backend is not AuditBackend.NATIVE and self.native_verification_trace is not None:
            raise ValueError("only the native backend can carry a verification trace")


def invoke_native_backend(
    linear_program: MaterializedAuditLinearProgram,
    *,
    options: NativeBackendOptions = ADR0311_NATIVE_OPTIONS,
) -> BackendRawResult:
    """Invoke the frozen public native solver and retain verification locals on failure."""

    if not isinstance(linear_program, MaterializedAuditLinearProgram):
        raise TypeError("native adapter requires a materialized audit LP")
    if not isinstance(options, NativeBackendOptions):
        raise TypeError("native adapter options must be semantic")
    started = perf_counter()
    try:
        solved = maximize_linear_program(
            linear_program.objective,
            linear_program.coefficients,
            linear_program.bounds,
            tolerance=options.tolerance,
            max_pivots=options.maximum_pivots,
        )
    except Exception as error:  # noqa: BLE001 - every backend arm must leave a record
        elapsed = float(perf_counter() - started)
        trace = _extract_native_verification_trace(error)
        return BackendRawResult(
            backend=AuditBackend.NATIVE,
            termination=BackendTermination.EXCEPTION,
            status_code=None,
            status_text="exception",
            message=str(error),
            iterations=None if trace is None else trace.pivots,
            crossover_iterations=None,
            primal_variant_coordinates=(
                None if trace is None else trace.primal_variant_coordinates
            ),
            reported_maximization_objective=(
                None if trace is None else trace.raw_maximization_objective
            ),
            dual_hint_variant_rows=(None if trace is None else trace.dual_hint_variant_rows),
            dual_hint_convention=DualHintConvention.MAXIMIZATION_NONNEGATIVE,
            elapsed_seconds=elapsed,
            exception=AuditExceptionRecord.from_exception(
                error,
                stage=AuditFailureStage.BACKEND_INVOCATION,
            ),
            native_verification_trace=trace,
        )
    return BackendRawResult(
        backend=AuditBackend.NATIVE,
        termination=BackendTermination.OPTIMAL,
        status_code=0,
        status_text="optimal",
        message="native simplex returned a verified optimum",
        iterations=solved.pivots,
        crossover_iterations=None,
        primal_variant_coordinates=solved.variables,
        reported_maximization_objective=solved.objective,
        dual_hint_variant_rows=solved.dual_variables,
        dual_hint_convention=DualHintConvention.MAXIMIZATION_NONNEGATIVE,
        elapsed_seconds=float(perf_counter() - started),
    )


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def invoke_highs_backend(
    backend: AuditBackend,
    linear_program: MaterializedAuditLinearProgram,
    *,
    linprog_function: Callable[..., Any] | None = None,
) -> BackendRawResult:
    """Invoke one frozen SciPy HiGHS arm without adding unregistered hints."""

    if backend not in {AuditBackend.HIGHS_DS, AuditBackend.HIGHS_IPM}:
        raise ValueError("HiGHS adapter requires the DS or IPM backend")
    if not isinstance(linear_program, MaterializedAuditLinearProgram):
        raise TypeError("HiGHS adapter requires a materialized audit LP")
    if linprog_function is None:
        linprog_function = import_module("scipy.optimize").linprog
    options = (
        ADR0311_HIGHS_DS_OPTIONS if backend is AuditBackend.HIGHS_DS else ADR0311_HIGHS_IPM_OPTIONS
    )
    started = perf_counter()
    try:
        solved = linprog_function(
            tuple(-value for value in linear_program.objective),
            A_ub=linear_program.coefficients,
            b_ub=linear_program.bounds,
            bounds=[(0.0, None)] * len(linear_program.objective),
            method=options.method,
            options=options.scipy_options,
        )
        success = bool(solved.success)
        status_code = int(solved.status)
        status_text = "optimal" if success else f"status-{status_code}"
        primal = None if solved.x is None else tuple(float(value) for value in solved.x)
        raw_fun = None if solved.fun is None else float(solved.fun)
        ineqlin = getattr(solved, "ineqlin", None)
        marginals = None if ineqlin is None else getattr(ineqlin, "marginals", None)
        dual = None if marginals is None else tuple(float(value) for value in marginals)
        termination = (
            BackendTermination.OPTIMAL if success else BackendTermination.NONOPTIMAL_STATUS
        )
        return BackendRawResult(
            backend=backend,
            termination=termination,
            status_code=status_code,
            status_text=status_text,
            message=str(solved.message),
            iterations=_optional_int(getattr(solved, "nit", None)),
            crossover_iterations=_optional_int(getattr(solved, "crossover_nit", None)),
            primal_variant_coordinates=primal,
            reported_maximization_objective=None if raw_fun is None else -raw_fun,
            dual_hint_variant_rows=dual,
            dual_hint_convention=DualHintConvention.MINIMIZATION_NONPOSITIVE,
            elapsed_seconds=float(perf_counter() - started),
        )
    except Exception as error:  # noqa: BLE001 - every backend arm must leave a record
        return BackendRawResult(
            backend=backend,
            termination=BackendTermination.EXCEPTION,
            status_code=None,
            status_text="exception",
            message=str(error),
            iterations=None,
            crossover_iterations=None,
            primal_variant_coordinates=None,
            reported_maximization_objective=None,
            dual_hint_variant_rows=None,
            dual_hint_convention=DualHintConvention.MINIMIZATION_NONPOSITIVE,
            elapsed_seconds=float(perf_counter() - started),
            exception=AuditExceptionRecord.from_exception(
                error,
                stage=AuditFailureStage.BACKEND_INVOCATION,
            ),
        )


@dataclass(frozen=True, slots=True)
class DualHintReconstruction:
    raw_variant_hint: tuple[float, ...]
    minimization_variant_hint: tuple[float, ...]
    clipped_minimization_variant_hint: tuple[float, ...]
    sign_clip_variant_rows: tuple[int, ...]
    canonical_minimization_hint: tuple[float, ...]

    def __post_init__(self) -> None:
        for label, values in (
            ("raw dual hint", self.raw_variant_hint),
            ("normalized dual hint", self.minimization_variant_hint),
            ("clipped dual hint", self.clipped_minimization_variant_hint),
            ("canonical dual hint", self.canonical_minimization_hint),
        ):
            _require_finite_tuple(values, label=label)
        if not isinstance(self.sign_clip_variant_rows, tuple) or any(
            isinstance(index, bool) or not isinstance(index, int) or index < 0
            for index in self.sign_clip_variant_rows
        ):
            raise TypeError("dual sign-clip rows must be immutable indices")


@dataclass(frozen=True, slots=True)
class BackendCoordinateDiagnostics:
    canonical_primal: tuple[float, ...]
    variant_row_residuals: tuple[float, ...]
    original_row_residuals: tuple[float, ...]
    reconstructed_maximization_objective: float
    reconstructed_value_with_offset: float
    reported_value_with_offset: float | None
    reported_objective_error: float | None
    maximum_dimensionless_row_violation: float
    maximum_chip_row_violation: float
    maximum_dimensionless_lower_box_violation: float
    maximum_dimensionless_upper_box_violation: float
    maximum_chip_lower_box_violation: float
    maximum_chip_upper_box_violation: float

    def __post_init__(self) -> None:
        for label, values in (
            ("canonical diagnostic primal", self.canonical_primal),
            ("variant diagnostic residuals", self.variant_row_residuals),
            ("original diagnostic residuals", self.original_row_residuals),
        ):
            _require_finite_tuple(values, label=label)
        for label, value in (
            ("reconstructed diagnostic objective", self.reconstructed_maximization_objective),
            ("reconstructed diagnostic value", self.reconstructed_value_with_offset),
        ):
            if not isinstance(value, float) or not isfinite(value):
                raise ValueError(f"{label} must be finite")
        if self.reported_value_with_offset is not None and (
            not isinstance(self.reported_value_with_offset, float)
            or not isfinite(self.reported_value_with_offset)
        ):
            raise ValueError("reported diagnostic value must be finite when present")
        if self.reported_objective_error is not None:
            _require_nonnegative_finite(
                self.reported_objective_error,
                label="reported diagnostic objective error",
            )
        for value in (
            self.maximum_dimensionless_row_violation,
            self.maximum_chip_row_violation,
            self.maximum_dimensionless_lower_box_violation,
            self.maximum_dimensionless_upper_box_violation,
            self.maximum_chip_lower_box_violation,
            self.maximum_chip_upper_box_violation,
        ):
            _require_nonnegative_finite(value, label="unit-specific diagnostic violation")


@dataclass(frozen=True, slots=True)
class BackendCertificateDiagnostics:
    dual_hint: DualHintReconstruction
    certificate: BoundedMinimizationCertificate
    certified_maximization_objective_upper_bound: float
    certified_value_upper_bound_with_offset: float

    def __post_init__(self) -> None:
        if not isinstance(self.dual_hint, DualHintReconstruction):
            raise TypeError("backend certificate dual hint must be semantic")
        if not isinstance(self.certificate, BoundedMinimizationCertificate):
            raise TypeError("backend certificate must be semantic")
        for value in (
            self.certified_maximization_objective_upper_bound,
            self.certified_value_upper_bound_with_offset,
        ):
            if not isinstance(value, float) or not isfinite(value):
                raise ValueError("backend certificate upper bound must be finite")


def map_primal_to_canonical(
    primal_variant: tuple[float, ...],
    descriptor: AuditVariantDescriptor,
) -> tuple[float, ...]:
    if not isinstance(descriptor, AuditVariantDescriptor):
        raise TypeError("primal coordinate map must be semantic")
    _require_finite_tuple(primal_variant, label="variant primal", allow_empty=False)
    if len(primal_variant) != len(descriptor.variant_to_canonical_variables):
        raise ValueError("variant primal width differs from the coordinate map")
    canonical = [0.0] * len(primal_variant)
    for variant, canonical_index in enumerate(descriptor.variant_to_canonical_variables):
        canonical[canonical_index] = primal_variant[variant]
    return tuple(canonical)


def reconstruct_dual_hint(
    raw_variant_hint: tuple[float, ...],
    *,
    convention: DualHintConvention,
    descriptor: AuditVariantDescriptor,
) -> DualHintReconstruction:
    if not isinstance(convention, DualHintConvention):
        raise TypeError("dual reconstruction convention must be semantic")
    if not isinstance(descriptor, AuditVariantDescriptor):
        raise TypeError("dual row map must be semantic")
    _require_finite_tuple(raw_variant_hint, label="variant dual hint")
    if len(raw_variant_hint) != len(descriptor.variant_to_canonical_rows):
        raise ValueError("variant dual width differs from the row map")
    normalized = tuple(
        -value if convention is DualHintConvention.MAXIMIZATION_NONNEGATIVE else value
        for value in raw_variant_hint
    )
    clip_rows = tuple(index for index, value in enumerate(normalized) if value > 0.0)
    clipped = tuple(min(value, 0.0) for value in normalized)
    contributions: list[list[float]] = [[] for _ in descriptor.canonical_to_variant_rows]
    for variant, (origin, exponent) in enumerate(
        zip(
            descriptor.variant_to_canonical_rows,
            descriptor.row_scale_exponents,
            strict=True,
        )
    ):
        if origin is not None:
            contributions[origin].append(clipped[variant] * float(2**exponent))
    canonical = tuple(fsum(values) for values in contributions)
    return DualHintReconstruction(
        raw_variant_hint=raw_variant_hint,
        minimization_variant_hint=normalized,
        clipped_minimization_variant_hint=clipped,
        sign_clip_variant_rows=clip_rows,
        canonical_minimization_hint=canonical,
    )


@dataclass(frozen=True, slots=True)
class NativeFailureCoordinates:
    failing_variant_rows: tuple[int, ...]
    failing_canonical_rows: tuple[int, ...]
    maximum_variant_residual: float
    verification_allowance: float

    def __post_init__(self) -> None:
        for label, values in (
            ("failing variant rows", self.failing_variant_rows),
            ("failing canonical rows", self.failing_canonical_rows),
        ):
            if not isinstance(values, tuple) or any(
                isinstance(value, bool) or not isinstance(value, int) or value < 0
                for value in values
            ):
                raise TypeError(f"native {label} must be immutable indices")
        if tuple(sorted(set(self.failing_variant_rows))) != self.failing_variant_rows:
            raise ValueError("native failing variant rows must be sorted and unique")
        if tuple(sorted(set(self.failing_canonical_rows))) != self.failing_canonical_rows:
            raise ValueError("native failing canonical rows must be sorted and unique")
        _require_nonnegative_finite(
            self.maximum_variant_residual,
            label="native maximum residual",
        )
        _require_nonnegative_finite(
            self.verification_allowance,
            label="native verification allowance",
        )


def reconstruct_native_failure_coordinates(
    trace: NativeVerificationTrace,
    descriptor: AuditVariantDescriptor,
) -> NativeFailureCoordinates | None:
    residuals = trace.constraint_residuals_variant_rows
    allowance = trace.verification_allowance
    if residuals is None or allowance is None:
        return None
    if len(residuals) != len(descriptor.variant_to_canonical_rows):
        raise ValueError("native traced residual count differs from the variant map")
    failing_variant = tuple(
        index for index, residual in enumerate(residuals) if residual > allowance
    )
    failing_canonical = tuple(
        sorted(
            {
                origin
                for index in failing_variant
                if (origin := descriptor.variant_to_canonical_rows[index]) is not None
            }
        )
    )
    return NativeFailureCoordinates(
        failing_variant_rows=failing_variant,
        failing_canonical_rows=failing_canonical,
        maximum_variant_residual=max(0.0, max(residuals, default=0.0)),
        verification_allowance=allowance,
    )


class AuditCheckFailure(StrEnum):
    MICRO_PRIMAL = "micro-primal"
    MICRO_DUAL = "micro-dual"
    MICRO_OBJECTIVE = "micro-objective"
    POLICY_NONNEGATIVITY = "policy-nonnegativity"
    POLICY_SIMPLEX_MASS = "policy-simplex-mass"
    ENVELOPE_FEASIBILITY = "envelope-feasibility"
    SIZING_OBJECTIVE = "sizing-objective"
    SIZING_CERTIFICATE_WIDTH = "sizing-certificate-width"


@dataclass(frozen=True, slots=True)
class MicroAuditVerification:
    canonical_primal: tuple[float, ...]
    variant_row_residuals: tuple[float, ...]
    original_row_residuals: tuple[float, ...]
    maximum_primal_violation: float
    reconstructed_objective: float
    reported_objective_error: float
    exact_objective_error: float
    certified_upper_bound: float
    certified_gap_above_exact: float
    dual_hint: DualHintReconstruction
    certificate: BoundedMinimizationCertificate
    failures: tuple[AuditCheckFailure, ...]

    def __post_init__(self) -> None:
        for label, values in (
            ("micro canonical primal", self.canonical_primal),
            ("micro variant residuals", self.variant_row_residuals),
            ("micro original residuals", self.original_row_residuals),
        ):
            _require_finite_tuple(values, label=label)
        for label, value in (
            ("micro primal violation", self.maximum_primal_violation),
            ("micro reported-objective error", self.reported_objective_error),
            ("micro exact-objective error", self.exact_objective_error),
        ):
            _require_nonnegative_finite(value, label=label)
        for label, value in (
            ("micro reconstructed objective", self.reconstructed_objective),
            ("micro certified upper bound", self.certified_upper_bound),
            ("micro certified exact gap", self.certified_gap_above_exact),
        ):
            if not isinstance(value, float) or not isfinite(value):
                raise ValueError(f"{label} must be finite")
        if not isinstance(self.dual_hint, DualHintReconstruction):
            raise TypeError("micro verification dual hint must be semantic")
        if not isinstance(self.certificate, BoundedMinimizationCertificate):
            raise TypeError("micro verification certificate must be semantic")
        if not isinstance(self.failures, tuple) or any(
            not isinstance(value, AuditCheckFailure) for value in self.failures
        ):
            raise TypeError("micro verification failures must be semantic and immutable")

    @property
    def passed(self) -> bool:
        return not self.failures


@dataclass(frozen=True, slots=True)
class PolicyClip:
    canonical_variable: int
    raw_value: float
    clipped_value: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.canonical_variable, bool)
            or not isinstance(self.canonical_variable, int)
            or self.canonical_variable < 0
        ):
            raise ValueError("policy clip variable index must be nonnegative")
        for label, value in (("raw", self.raw_value), ("clipped", self.clipped_value)):
            if not isinstance(value, float) or not isfinite(value):
                raise ValueError(f"policy clip {label} value must be finite")
        if self.raw_value == self.clipped_value:
            raise ValueError("policy clip must change its recorded value")


@dataclass(frozen=True, slots=True)
class SizingAuditVerification:
    canonical_primal: tuple[float, ...]
    variant_row_residuals: tuple[float, ...]
    original_row_residuals: tuple[float, ...]
    maximum_policy_nonnegativity_violation: float
    maximum_policy_upper_violation: float
    maximum_policy_simplex_mass_residual: float
    maximum_postclip_policy_simplex_mass_residual: float
    maximum_envelope_nonnegativity_violation_chips: float
    maximum_envelope_upper_violation_chips: float
    maximum_envelope_row_violation_chips: float
    policy_clips: tuple[PolicyClip, ...]
    exact_normalized_policy: tuple[tuple[ExactRational, ...], ...]
    responder_best_actions: tuple[tuple[str, ...], ...]
    reported_value_chips: float
    canonical_lp_value_chips: float
    reported_objective_error_chips: float
    behavioral_lower_bound_chips: float
    behavioral_objective_error_chips: float
    certified_upper_bound_chips: float
    certified_optimality_gap_chips: float
    dual_hint: DualHintReconstruction
    certificate: BoundedMinimizationCertificate
    failures: tuple[AuditCheckFailure, ...]

    def __post_init__(self) -> None:
        for label, values in (
            ("sizing canonical primal", self.canonical_primal),
            ("sizing variant residuals", self.variant_row_residuals),
            ("sizing original residuals", self.original_row_residuals),
        ):
            _require_finite_tuple(values, label=label)
        nonnegative = (
            self.maximum_policy_nonnegativity_violation,
            self.maximum_policy_upper_violation,
            self.maximum_policy_simplex_mass_residual,
            self.maximum_postclip_policy_simplex_mass_residual,
            self.maximum_envelope_nonnegativity_violation_chips,
            self.maximum_envelope_upper_violation_chips,
            self.maximum_envelope_row_violation_chips,
            self.reported_objective_error_chips,
            self.behavioral_objective_error_chips,
        )
        for value in nonnegative:
            _require_nonnegative_finite(value, label="sizing semantic residual")
        for value in (
            self.reported_value_chips,
            self.canonical_lp_value_chips,
            self.behavioral_lower_bound_chips,
            self.certified_upper_bound_chips,
            self.certified_optimality_gap_chips,
        ):
            if not isinstance(value, float) or not isfinite(value):
                raise ValueError("sizing value or certificate endpoint must be finite")
        if not isinstance(self.policy_clips, tuple) or any(
            not isinstance(value, PolicyClip) for value in self.policy_clips
        ):
            raise TypeError("sizing policy clips must be semantic and immutable")
        if (
            not isinstance(self.exact_normalized_policy, tuple)
            or not self.exact_normalized_policy
            or any(
                not isinstance(row, tuple)
                or not row
                or any(not isinstance(value, ExactRational) for value in row)
                or sum((value.fraction for value in row), start=Fraction(0)) != 1
                for row in self.exact_normalized_policy
            )
        ):
            raise TypeError("sizing exact policy must contain normalized rational rows")
        if (
            not isinstance(self.responder_best_actions, tuple)
            or not self.responder_best_actions
            or any(
                not isinstance(row, tuple) or any(action not in {"fold", "call"} for action in row)
                for row in self.responder_best_actions
            )
        ):
            raise TypeError("sizing responder actions must be immutable fold/call rows")
        if not isinstance(self.dual_hint, DualHintReconstruction):
            raise TypeError("sizing verification dual hint must be semantic")
        if not isinstance(self.certificate, BoundedMinimizationCertificate):
            raise TypeError("sizing verification certificate must be semantic")
        if not isinstance(self.failures, tuple) or any(
            not isinstance(value, AuditCheckFailure) for value in self.failures
        ):
            raise TypeError("sizing verification failures must be semantic and immutable")

    @property
    def passed(self) -> bool:
        return not self.failures


def _original_row_residuals(
    base: AuditLinearProgramBase,
    canonical_primal: tuple[float, ...],
) -> tuple[float, ...]:
    return tuple(
        fsum(coefficient * value for coefficient, value in zip(row, canonical_primal, strict=True))
        - bound
        for row, bound in zip(base.coefficients, base.bounds, strict=True)
    )


def _variant_row_residuals(
    base: AuditLinearProgramBase,
    descriptor: AuditVariantDescriptor,
    primal_variant: tuple[float, ...],
) -> tuple[float, ...]:
    base_width = len(descriptor.variant_to_canonical_variables)
    if len(primal_variant) != base_width:
        raise ValueError("variant primal width differs from its descriptor")
    materialized = materialize_audit_variant(base=base, descriptor=descriptor)
    return tuple(
        fsum(coefficient * value for coefficient, value in zip(row, primal_variant, strict=True))
        - bound
        for row, bound in zip(
            materialized.coefficients,
            materialized.bounds,
            strict=True,
        )
    )


def _certificate_from_original_coordinates(
    base: AuditLinearProgramBase,
    dual: DualHintReconstruction,
) -> BoundedMinimizationCertificate:
    return certify_bounded_minimization_lower_bound(
        tuple(-value for value in base.objective),
        base.coefficients,
        base.bounds,
        dual.canonical_minimization_hint,
        variable_lower_bounds=base.trusted_box_lower_bounds,
        variable_upper_bounds=base.trusted_box_upper_bounds,
    )


def build_backend_coordinate_diagnostics(
    *,
    base: AuditLinearProgramBase,
    descriptor: AuditVariantDescriptor,
    raw: BackendRawResult,
) -> BackendCoordinateDiagnostics:
    if raw.primal_variant_coordinates is None:
        raise ValueError("coordinate diagnostics require a returned primal vector")
    canonical = map_primal_to_canonical(raw.primal_variant_coordinates, descriptor)
    if len(canonical) != base.variable_count:
        raise ValueError("diagnostic canonical primal width differs from its base")
    variant_residuals = _variant_row_residuals(
        base,
        descriptor,
        raw.primal_variant_coordinates,
    )
    original_residuals = _original_row_residuals(base, canonical)
    reconstructed = fsum(
        coefficient * value for coefficient, value in zip(base.objective, canonical, strict=True)
    )
    reconstructed_value = reconstructed + base.objective_offset
    reported_value = (
        None
        if raw.reported_maximization_objective is None
        else raw.reported_maximization_objective + base.objective_offset
    )
    reported_error = None if reported_value is None else abs(reported_value - reconstructed_value)
    dimensionless_rows = tuple(
        max(0.0, residual)
        for residual, unit in zip(original_residuals, base.row_units, strict=True)
        if unit is LinearProgramConstraintUnit.DIMENSIONLESS
    )
    chip_rows = tuple(
        max(0.0, residual)
        for residual, unit in zip(original_residuals, base.row_units, strict=True)
        if unit is LinearProgramConstraintUnit.CHIPS
    )
    dimensionless_lower: list[float] = []
    dimensionless_upper: list[float] = []
    chip_lower: list[float] = []
    chip_upper: list[float] = []
    for value, lower, upper, unit in zip(
        canonical,
        base.trusted_box_lower_bounds,
        base.trusted_box_upper_bounds,
        base.variable_units,
        strict=True,
    ):
        target_lower, target_upper = (
            (chip_lower, chip_upper)
            if unit is LinearProgramVariableUnit.SHIFTED_ENVELOPE_CHIPS
            else (dimensionless_lower, dimensionless_upper)
        )
        target_lower.append(max(0.0, lower - value))
        target_upper.append(max(0.0, value - upper))
    return BackendCoordinateDiagnostics(
        canonical_primal=canonical,
        variant_row_residuals=variant_residuals,
        original_row_residuals=original_residuals,
        reconstructed_maximization_objective=reconstructed,
        reconstructed_value_with_offset=reconstructed_value,
        reported_value_with_offset=reported_value,
        reported_objective_error=reported_error,
        maximum_dimensionless_row_violation=max(dimensionless_rows, default=0.0),
        maximum_chip_row_violation=max(chip_rows, default=0.0),
        maximum_dimensionless_lower_box_violation=max(dimensionless_lower, default=0.0),
        maximum_dimensionless_upper_box_violation=max(dimensionless_upper, default=0.0),
        maximum_chip_lower_box_violation=max(chip_lower, default=0.0),
        maximum_chip_upper_box_violation=max(chip_upper, default=0.0),
    )


def build_backend_certificate_diagnostics(
    *,
    base: AuditLinearProgramBase,
    descriptor: AuditVariantDescriptor,
    raw: BackendRawResult,
) -> BackendCertificateDiagnostics:
    if raw.dual_hint_variant_rows is None:
        raise ValueError("certificate diagnostics require a returned dual hint")
    dual = reconstruct_dual_hint(
        raw.dual_hint_variant_rows,
        convention=raw.dual_hint_convention,
        descriptor=descriptor,
    )
    certificate = _certificate_from_original_coordinates(base, dual)
    objective_upper = -certificate.lower_bound
    return BackendCertificateDiagnostics(
        dual_hint=dual,
        certificate=certificate,
        certified_maximization_objective_upper_bound=objective_upper,
        certified_value_upper_bound_with_offset=(objective_upper + base.objective_offset),
    )


def verify_micro_backend_result(
    *,
    base: AuditLinearProgramBase,
    descriptor: AuditVariantDescriptor,
    raw: BackendRawResult,
    exact: ExactMicroEnumeration,
) -> MicroAuditVerification:
    if base.family is not AuditBaseFamily.EXACT_MICRO:
        raise TypeError("micro verification requires a micro base")
    if raw.termination is not BackendTermination.OPTIMAL:
        raise ValueError("micro verification requires an optimal backend return")
    assert raw.primal_variant_coordinates is not None
    assert raw.reported_maximization_objective is not None
    assert raw.dual_hint_variant_rows is not None
    canonical = map_primal_to_canonical(raw.primal_variant_coordinates, descriptor)
    if len(canonical) != base.variable_count:
        raise ValueError("micro canonical primal width differs from its base")
    variant_residuals = _variant_row_residuals(
        base,
        descriptor,
        raw.primal_variant_coordinates,
    )
    residuals = _original_row_residuals(base, canonical)
    maximum_primal = max(
        max((max(0.0, value) for value in residuals), default=0.0),
        max((max(0.0, -value) for value in canonical), default=0.0),
    )
    reconstructed = fsum(
        coefficient * value for coefficient, value in zip(base.objective, canonical, strict=True)
    )
    reported_error = abs(raw.reported_maximization_objective - reconstructed)
    exact_error = abs(reconstructed - float(exact.optimum.fraction))
    dual = reconstruct_dual_hint(
        raw.dual_hint_variant_rows,
        convention=raw.dual_hint_convention,
        descriptor=descriptor,
    )
    certificate = _certificate_from_original_coordinates(base, dual)
    certified_upper = -certificate.lower_bound
    certified_gap = certified_upper - float(exact.optimum.fraction)
    failures: list[AuditCheckFailure] = []
    if maximum_primal > ADR0311_MICRO_PRIMAL_ALLOWANCE.value:
        failures.append(AuditCheckFailure.MICRO_PRIMAL)
    if (
        certified_gap < -ADR0311_MICRO_DUAL_ALLOWANCE.value
        or certified_gap > ADR0311_MICRO_DUAL_ALLOWANCE.value
    ):
        failures.append(AuditCheckFailure.MICRO_DUAL)
    if max(reported_error, exact_error) > ADR0311_MICRO_OBJECTIVE_ALLOWANCE.value:
        failures.append(AuditCheckFailure.MICRO_OBJECTIVE)
    return MicroAuditVerification(
        canonical_primal=canonical,
        variant_row_residuals=variant_residuals,
        original_row_residuals=residuals,
        maximum_primal_violation=maximum_primal,
        reconstructed_objective=reconstructed,
        reported_objective_error=reported_error,
        exact_objective_error=exact_error,
        certified_upper_bound=certified_upper,
        certified_gap_above_exact=certified_gap,
        dual_hint=dual,
        certificate=certificate,
        failures=tuple(failures),
    )


def _compile_sizing_context(
    base: AuditLinearProgramBase,
    context: AuditWidthFourContext,
):
    if base.bet_sizes is None:
        raise ValueError("sizing base omits its bet sizes")
    compiled = compile_reduced_river_sizing_lp(
        pot=context.pot,
        stack=context.stack,
        minimum_bet=context.minimum_bet,
        joint_probabilities=tuple(
            tuple(probability.fraction for probability in row)
            for row in context.joint_probabilities
        ),
        showdown_signs=context.showdown_signs,
        bet_sizes=base.bet_sizes,
    )
    if (
        compiled.objective != base.objective
        or compiled.coefficients != base.coefficients
        or compiled.bounds != base.bounds
        or compiled.row_units != base.row_units
        or compiled.variable_units != base.variable_units
        or compiled.trusted_box_lower_bounds != base.trusted_box_lower_bounds
        or compiled.trusted_box_upper_bounds != base.trusted_box_upper_bounds
        or compiled.objective_offset_chips != base.objective_offset
    ):
        raise ValueError("sizing context recompilation differs from the sealed base")
    return compiled


def _clip_and_normalize_policy(
    canonical: tuple[float, ...],
    *,
    policy_variable_count: int,
    opener_count: int,
    action_count: int,
) -> tuple[
    tuple[tuple[Fraction, ...], ...],
    tuple[PolicyClip, ...],
    float,
    float,
    float,
    float,
]:
    clipped = list(canonical[:policy_variable_count])
    maximum_raw_mass_residual = max(
        (
            abs(fsum(clipped[opener * action_count : (opener + 1) * action_count]) - 1.0)
            for opener in range(opener_count)
        ),
        default=0.0,
    )
    clips: list[PolicyClip] = []
    maximum_negative = 0.0
    maximum_upper = 0.0
    for index, value in enumerate(clipped):
        maximum_negative = max(maximum_negative, max(0.0, -value))
        maximum_upper = max(maximum_upper, max(0.0, value - 1.0))
        replacement = value
        if -ADR0311_POLICY_NONNEGATIVITY_ALLOWANCE.value <= value < 0.0:
            replacement = 0.0
        elif 1.0 < value <= 1.0 + ADR0311_POLICY_NONNEGATIVITY_ALLOWANCE.value:
            replacement = 1.0
        if replacement != value:
            clips.append(PolicyClip(index, value, replacement))
            clipped[index] = replacement
    rows: list[tuple[Fraction, ...]] = []
    maximum_mass_residual = 0.0
    for opener in range(opener_count):
        start = opener * action_count
        raw_row = tuple(clipped[start : start + action_count])
        maximum_mass_residual = max(maximum_mass_residual, abs(fsum(raw_row) - 1.0))
        exact_row = tuple(Fraction.from_float(value) for value in raw_row)
        total = sum(exact_row, start=Fraction(0))
        if total <= 0:
            raise ValueError("sizing policy row cannot be renormalized")
        if any(value < 0 for value in exact_row):
            raise ValueError("sizing policy remains negative after frozen clipping")
        rows.append(tuple(value / total for value in exact_row))
    return (
        tuple(rows),
        tuple(clips),
        maximum_negative,
        maximum_upper,
        maximum_raw_mass_residual,
        maximum_mass_residual,
    )


def _behavioral_sizing_value(
    *,
    context: AuditWidthFourContext,
    bet_sizes: tuple[int, ...],
    policy: tuple[tuple[Fraction, ...], ...],
) -> tuple[Fraction, tuple[tuple[str, ...], ...]]:
    half_pot = Fraction(context.pot, 2)
    value = Fraction(0)
    signs = context.showdown_signs
    for opener, policy_row in enumerate(policy):
        for responder in range(len(context.responder_hands)):
            value += (
                context.joint_probabilities[opener][responder].fraction
                * policy_row[0]
                * signs[opener][responder]
                * half_pot
            )
    best_actions: list[tuple[str, ...]] = []
    for responder in range(len(context.responder_hands)):
        actions: list[str] = []
        for bet_index, bet in enumerate(bet_sizes):
            fold = sum(
                (
                    context.joint_probabilities[opener][responder].fraction
                    * policy[opener][bet_index + 1]
                    * half_pot
                    for opener in range(len(context.opener_hands))
                ),
                start=Fraction(0),
            )
            call = sum(
                (
                    context.joint_probabilities[opener][responder].fraction
                    * policy[opener][bet_index + 1]
                    * signs[opener][responder]
                    * (half_pot + bet)
                    for opener in range(len(context.opener_hands))
                ),
                start=Fraction(0),
            )
            if fold <= call:
                actions.append("fold")
                value += fold
            else:
                actions.append("call")
                value += call
        best_actions.append(tuple(actions))
    return value, tuple(best_actions)


def verify_sizing_backend_result(
    *,
    base: AuditLinearProgramBase,
    descriptor: AuditVariantDescriptor,
    raw: BackendRawResult,
    context: AuditWidthFourContext,
) -> SizingAuditVerification:
    if base.family is AuditBaseFamily.EXACT_MICRO:
        raise TypeError("sizing verification cannot consume a micro base")
    if raw.termination is not BackendTermination.OPTIMAL:
        raise ValueError("sizing verification requires an optimal backend return")
    if base.context_id != context.context_id:
        raise ValueError("sizing context id differs from its base")
    assert raw.primal_variant_coordinates is not None
    assert raw.reported_maximization_objective is not None
    assert raw.dual_hint_variant_rows is not None
    compiled = _compile_sizing_context(base, context)
    canonical = map_primal_to_canonical(raw.primal_variant_coordinates, descriptor)
    if len(canonical) != compiled.layout.variable_count:
        raise ValueError("sizing canonical primal width differs from its layout")
    variant_residuals = _variant_row_residuals(
        base,
        descriptor,
        raw.primal_variant_coordinates,
    )
    residuals = _original_row_residuals(base, canonical)
    policy, clips, max_negative, max_upper, max_raw_mass, max_postclip_mass = (
        _clip_and_normalize_policy(
            canonical,
            policy_variable_count=compiled.layout.policy_variable_count,
            opener_count=compiled.layout.opener_count,
            action_count=compiled.layout.action_count,
        )
    )
    envelope_values = canonical[compiled.layout.policy_variable_count :]
    max_envelope_negative = max(
        (max(0.0, -value) for value in envelope_values),
        default=0.0,
    )
    max_envelope_upper = max(
        (max(0.0, value - compiled.payoff_span_chips) for value in envelope_values),
        default=0.0,
    )
    max_envelope_row = max(
        (
            max(0.0, residual)
            for residual, unit in zip(residuals, base.row_units, strict=True)
            if unit is LinearProgramConstraintUnit.CHIPS
        ),
        default=0.0,
    )
    canonical_objective = fsum(
        coefficient * value for coefficient, value in zip(base.objective, canonical, strict=True)
    )
    reported_value = raw.reported_maximization_objective + base.objective_offset
    canonical_value = canonical_objective + base.objective_offset
    reported_error = abs(reported_value - canonical_value)
    assert base.bet_sizes is not None
    behavioral_exact, best_actions = _behavioral_sizing_value(
        context=context,
        bet_sizes=base.bet_sizes,
        policy=policy,
    )
    behavioral_value = float(behavioral_exact)
    behavioral_error = abs(canonical_value - behavioral_value)
    dual = reconstruct_dual_hint(
        raw.dual_hint_variant_rows,
        convention=raw.dual_hint_convention,
        descriptor=descriptor,
    )
    certificate = _certificate_from_original_coordinates(base, dual)
    certified_upper = -certificate.lower_bound + base.objective_offset
    certified_gap = certified_upper - behavioral_value
    failures: list[AuditCheckFailure] = []
    if max(max_negative, max_upper) > ADR0311_POLICY_NONNEGATIVITY_ALLOWANCE.value:
        failures.append(AuditCheckFailure.POLICY_NONNEGATIVITY)
    if max(max_raw_mass, max_postclip_mass) > ADR0311_POLICY_SIMPLEX_MASS_ALLOWANCE.value:
        failures.append(AuditCheckFailure.POLICY_SIMPLEX_MASS)
    if (
        max(
            max_envelope_negative,
            max_envelope_upper,
            max_envelope_row,
        )
        > ADR0311_ENVELOPE_FEASIBILITY_ALLOWANCE.chips
    ):
        failures.append(AuditCheckFailure.ENVELOPE_FEASIBILITY)
    if max(reported_error, behavioral_error) > ADR0311_SIZING_OBJECTIVE_ALLOWANCE.chips:
        failures.append(AuditCheckFailure.SIZING_OBJECTIVE)
    if (
        certified_gap < -ADR0311_SIZING_CERTIFICATE_WIDTH_ALLOWANCE.chips
        or certified_gap > ADR0311_SIZING_CERTIFICATE_WIDTH_ALLOWANCE.chips
    ):
        failures.append(AuditCheckFailure.SIZING_CERTIFICATE_WIDTH)
    return SizingAuditVerification(
        canonical_primal=canonical,
        variant_row_residuals=variant_residuals,
        original_row_residuals=residuals,
        maximum_policy_nonnegativity_violation=max_negative,
        maximum_policy_upper_violation=max_upper,
        maximum_policy_simplex_mass_residual=max_raw_mass,
        maximum_postclip_policy_simplex_mass_residual=max_postclip_mass,
        maximum_envelope_nonnegativity_violation_chips=max_envelope_negative,
        maximum_envelope_upper_violation_chips=max_envelope_upper,
        maximum_envelope_row_violation_chips=max_envelope_row,
        policy_clips=clips,
        exact_normalized_policy=tuple(
            tuple(ExactRational.from_fraction(value) for value in row) for row in policy
        ),
        responder_best_actions=best_actions,
        reported_value_chips=reported_value,
        canonical_lp_value_chips=canonical_value,
        reported_objective_error_chips=reported_error,
        behavioral_lower_bound_chips=behavioral_value,
        behavioral_objective_error_chips=behavioral_error,
        certified_upper_bound_chips=certified_upper,
        certified_optimality_gap_chips=certified_gap,
        dual_hint=dual,
        certificate=certificate,
        failures=tuple(failures),
    )


@dataclass(frozen=True, slots=True)
class PreparedAuditTask:
    task_index: int
    base: AuditLinearProgramBase
    descriptor: AuditVariantDescriptor
    materialized: MaterializedAuditLinearProgram
    exact_micro_case: ExactMicroLinearProgram | None
    sizing_context: AuditWidthFourContext | None

    def __post_init__(self) -> None:
        if (
            isinstance(self.task_index, bool)
            or not isinstance(self.task_index, int)
            or self.task_index < 0
        ):
            raise ValueError("audit task index must be nonnegative")
        if not isinstance(self.base, AuditLinearProgramBase):
            raise TypeError("audit task base must be semantic")
        if not isinstance(self.descriptor, AuditVariantDescriptor):
            raise TypeError("audit task descriptor must be semantic")
        if not isinstance(self.materialized, MaterializedAuditLinearProgram):
            raise TypeError("audit task materialization must be semantic")
        if self.descriptor.base_id != self.base.base_id:
            raise ValueError("audit task base and variant ids disagree")
        if self.materialized.digest != self.descriptor.linear_program_sha256:
            raise ValueError("audit task materialization identity drifted")
        if self.base.family is AuditBaseFamily.EXACT_MICRO:
            if self.exact_micro_case is None or self.sizing_context is not None:
                raise ValueError("micro audit task has the wrong independent binding")
            if self.exact_micro_case.case_id != self.base.base_id:
                raise ValueError("micro audit task case id differs from its base")
        elif self.exact_micro_case is not None or self.sizing_context is None:
            raise ValueError("sizing audit task has the wrong independent binding")


@dataclass(frozen=True, slots=True)
class ScheduledAuditInvocation:
    ordinal: int
    task_index: int
    base_id: str
    variant_id: str
    backend: AuditBackend

    def __post_init__(self) -> None:
        for label, value in (("ordinal", self.ordinal), ("task index", self.task_index)):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"audit invocation {label} must be nonnegative")
        if not isinstance(self.base_id, str) or not self.base_id:
            raise ValueError("audit invocation base id must be nonempty")
        if not isinstance(self.variant_id, str) or not self.variant_id:
            raise ValueError("audit invocation variant id must be nonempty")
        if not isinstance(self.backend, AuditBackend):
            raise TypeError("audit invocation backend must be semantic")


@dataclass(frozen=True, slots=True)
class PreparedAuditPlan:
    corpus_sha256: str
    tasks: tuple[PreparedAuditTask, ...]
    schedule: tuple[ScheduledAuditInvocation, ...]
    sealed_adr0311: bool

    def __post_init__(self) -> None:
        if (
            not isinstance(self.corpus_sha256, str)
            or len(self.corpus_sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.corpus_sha256)
        ):
            raise ValueError("prepared audit corpus digest is invalid")
        if not isinstance(self.tasks, tuple) or not self.tasks:
            raise TypeError("prepared audit tasks must be a nonempty immutable tuple")
        if any(not isinstance(task, PreparedAuditTask) for task in self.tasks):
            raise TypeError("prepared audit plan contains a nonsemantic task")
        if not isinstance(self.schedule, tuple) or any(
            not isinstance(invocation, ScheduledAuditInvocation) for invocation in self.schedule
        ):
            raise TypeError("prepared audit schedule must be semantic and immutable")
        if not isinstance(self.sealed_adr0311, bool):
            raise TypeError("prepared audit sealed flag must be boolean")
        if tuple(task.task_index for task in self.tasks) != tuple(range(len(self.tasks))):
            raise ValueError("prepared audit task indices are not contiguous")
        expected = tuple(
            ScheduledAuditInvocation(
                ordinal=task.task_index * len(ADR0311_BACKEND_ORDER) + backend_index,
                task_index=task.task_index,
                base_id=task.base.base_id,
                variant_id=task.descriptor.variant_id,
                backend=backend,
            )
            for task in self.tasks
            for backend_index, backend in enumerate(ADR0311_BACKEND_ORDER)
        )
        if self.schedule != expected:
            raise ValueError("prepared audit schedule differs from variant-major backend order")
        if self.sealed_adr0311:
            if self.corpus_sha256 != ADR0311_COMPLETE_CORPUS_SHA256:
                raise ValueError("sealed audit plan corpus identity drifted")
            if len(self.tasks) != ADR0311_VARIANT_COUNT:
                raise ValueError("sealed audit plan has the wrong variant count")
            if len(self.schedule) != ADR0313_EXPECTED_INVOCATION_COUNT:
                raise ValueError("sealed audit plan has the wrong invocation count")


def build_audit_schedule(
    tasks: tuple[PreparedAuditTask, ...],
) -> tuple[ScheduledAuditInvocation, ...]:
    return tuple(
        ScheduledAuditInvocation(
            ordinal=task.task_index * len(ADR0311_BACKEND_ORDER) + backend_index,
            task_index=task.task_index,
            base_id=task.base.base_id,
            variant_id=task.descriptor.variant_id,
            backend=backend,
        )
        for task in tasks
        for backend_index, backend in enumerate(ADR0311_BACKEND_ORDER)
    )


def prepare_adr0311_audit(corpus: NativeSimplexAuditCorpus) -> PreparedAuditPlan:
    """Bind every sealed variant to exact independent work without solving it."""

    if not isinstance(corpus, NativeSimplexAuditCorpus):
        raise TypeError("ADR-0311 preparation requires the sealed corpus type")
    if corpus.digest != ADR0311_COMPLETE_CORPUS_SHA256:
        raise ValueError("ADR-0311 corpus identity drifted")
    base_by_id = {base.base_id: base for base in corpus.bases}
    micro_by_id = {case.case_id: case for case in corpus.micro_structure.cases}
    contexts = (
        build_adr0311_known_regression_context(),
        *corpus.width_four_structure.contexts,
    )
    context_by_id = {context.context_id: context for context in contexts}
    tasks: list[PreparedAuditTask] = []
    for task_index, descriptor in enumerate(corpus.variants):
        base = base_by_id[descriptor.base_id]
        materialized = materialize_audit_variant(base=base, descriptor=descriptor)
        tasks.append(
            PreparedAuditTask(
                task_index=task_index,
                base=base,
                descriptor=descriptor,
                materialized=materialized,
                exact_micro_case=(
                    micro_by_id[base.base_id]
                    if base.family is AuditBaseFamily.EXACT_MICRO
                    else None
                ),
                sizing_context=(
                    None
                    if base.family is AuditBaseFamily.EXACT_MICRO
                    else context_by_id[base.context_id]
                ),
            )
        )
    immutable_tasks = tuple(tasks)
    return PreparedAuditPlan(
        corpus_sha256=corpus.digest,
        tasks=immutable_tasks,
        schedule=build_audit_schedule(immutable_tasks),
        sealed_adr0311=True,
    )


@dataclass(frozen=True, slots=True)
class AuditInvocationObservation:
    invocation: ScheduledAuditInvocation
    backend_result: BackendRawResult | None
    exact_micro_work: ExactMicroEnumeration | None
    coordinate_diagnostics: BackendCoordinateDiagnostics | None
    certificate_diagnostics: BackendCertificateDiagnostics | None
    micro_verification: MicroAuditVerification | None
    sizing_verification: SizingAuditVerification | None
    native_failure_coordinates: NativeFailureCoordinates | None
    runner_failures: tuple[AuditExceptionRecord, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.invocation, ScheduledAuditInvocation):
            raise TypeError("audit observation invocation must be semantic")
        if self.backend_result is not None:
            if not isinstance(self.backend_result, BackendRawResult):
                raise TypeError("audit observation backend result must be semantic")
            if self.backend_result.backend is not self.invocation.backend:
                raise ValueError("audit observation backend differs from its schedule arm")
        if self.exact_micro_work is not None and not isinstance(
            self.exact_micro_work,
            ExactMicroEnumeration,
        ):
            raise TypeError("audit observation exact work must be semantic")
        if self.coordinate_diagnostics is not None and not isinstance(
            self.coordinate_diagnostics,
            BackendCoordinateDiagnostics,
        ):
            raise TypeError("audit observation coordinate diagnostics must be semantic")
        if self.certificate_diagnostics is not None and not isinstance(
            self.certificate_diagnostics,
            BackendCertificateDiagnostics,
        ):
            raise TypeError("audit observation certificate diagnostics must be semantic")
        if self.micro_verification is not None and not isinstance(
            self.micro_verification,
            MicroAuditVerification,
        ):
            raise TypeError("audit observation micro verification must be semantic")
        if self.sizing_verification is not None and not isinstance(
            self.sizing_verification,
            SizingAuditVerification,
        ):
            raise TypeError("audit observation sizing verification must be semantic")
        if self.micro_verification is not None and self.sizing_verification is not None:
            raise ValueError("audit observation cannot carry both verification families")
        verification = self.micro_verification or self.sizing_verification
        if (
            verification is not None
            and self.coordinate_diagnostics is not None
            and (
                verification.canonical_primal != self.coordinate_diagnostics.canonical_primal
                or verification.variant_row_residuals
                != self.coordinate_diagnostics.variant_row_residuals
                or verification.original_row_residuals
                != self.coordinate_diagnostics.original_row_residuals
            )
        ):
            raise ValueError("audit observation verification and coordinate diagnostics drifted")
        if verification is not None and self.certificate_diagnostics is not None:
            if (
                verification.dual_hint != self.certificate_diagnostics.dual_hint
                or verification.certificate != self.certificate_diagnostics.certificate
            ):
                raise ValueError(
                    "audit observation verification and certificate diagnostics drifted"
                )
            expected_upper = (
                self.certificate_diagnostics.certified_maximization_objective_upper_bound
                if isinstance(verification, MicroAuditVerification)
                else self.certificate_diagnostics.certified_value_upper_bound_with_offset
            )
            actual_upper = (
                verification.certified_upper_bound
                if isinstance(verification, MicroAuditVerification)
                else verification.certified_upper_bound_chips
            )
            if actual_upper != expected_upper:
                raise ValueError("audit observation certified upper-bound directions drifted")
        if self.native_failure_coordinates is not None:
            if not isinstance(self.native_failure_coordinates, NativeFailureCoordinates):
                raise TypeError("audit observation native coordinates must be semantic")
            if self.invocation.backend is not AuditBackend.NATIVE:
                raise ValueError("non-native observation cannot carry native failure coordinates")
        if not isinstance(self.runner_failures, tuple) or any(
            not isinstance(value, AuditExceptionRecord) for value in self.runner_failures
        ):
            raise TypeError("audit observation runner failures must be semantic and immutable")

    @property
    def verified_pass(self) -> bool:
        verification = self.micro_verification or self.sizing_verification
        return (
            self.backend_result is not None
            and self.backend_result.termination is BackendTermination.OPTIMAL
            and not self.runner_failures
            and self.coordinate_diagnostics is not None
            and self.certificate_diagnostics is not None
            and verification is not None
            and verification.passed
        )


BackendAdapter = Callable[[MaterializedAuditLinearProgram], BackendRawResult]


def default_backend_adapters() -> dict[AuditBackend, BackendAdapter]:
    return {
        AuditBackend.NATIVE: invoke_native_backend,
        AuditBackend.HIGHS_DS: lambda linear_program: invoke_highs_backend(
            AuditBackend.HIGHS_DS,
            linear_program,
        ),
        AuditBackend.HIGHS_IPM: lambda linear_program: invoke_highs_backend(
            AuditBackend.HIGHS_IPM,
            linear_program,
        ),
    }


@dataclass(frozen=True, slots=True)
class AuditCampaignResult:
    runner_version: str
    runner_source_sha256: str
    corpus_sha256: str
    environment: AuditEnvironmentIdentity
    protocol: AuditProtocolIdentity
    observations: tuple[AuditInvocationObservation, ...]
    sealed_adr0311: bool

    def __post_init__(self) -> None:
        if self.runner_version != ADR0313_RUNNER_VERSION:
            raise ValueError("audit campaign runner version drifted")
        if (
            not isinstance(self.runner_source_sha256, str)
            or len(self.runner_source_sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.runner_source_sha256)
        ):
            raise ValueError("audit campaign runner source digest is invalid")
        if (
            not isinstance(self.corpus_sha256, str)
            or len(self.corpus_sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.corpus_sha256)
        ):
            raise ValueError("audit campaign corpus digest is invalid")
        if not isinstance(self.environment, AuditEnvironmentIdentity):
            raise TypeError("audit campaign environment must be semantic")
        if not isinstance(self.sealed_adr0311, bool):
            raise TypeError("audit campaign sealed flag must be boolean")
        if self.protocol != ADR0313_PROTOCOL:
            raise ValueError("audit campaign protocol identity drifted")
        if not isinstance(self.observations, tuple) or not self.observations:
            raise TypeError("audit campaign observations must be nonempty and immutable")
        if any(
            not isinstance(observation, AuditInvocationObservation)
            for observation in self.observations
        ):
            raise TypeError("audit campaign contains a nonsemantic observation")
        if tuple(observation.invocation.ordinal for observation in self.observations) != tuple(
            range(len(self.observations))
        ):
            raise ValueError("audit campaign observation ordinals are incomplete")
        if self.sealed_adr0311:
            if self.corpus_sha256 != ADR0311_COMPLETE_CORPUS_SHA256:
                raise ValueError("sealed campaign corpus identity drifted")
            if self.environment != ADR0313_EXPECTED_ENVIRONMENT:
                raise ValueError("sealed campaign environment identity drifted")
            if len(self.observations) != ADR0313_EXPECTED_INVOCATION_COUNT:
                raise ValueError("sealed campaign observation count is incomplete")

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_audit_bytes(self)

    @property
    def digest(self) -> str:
        return sha256(self.canonical_bytes).hexdigest()


def execute_audit_plan(
    plan: PreparedAuditPlan,
    *,
    adapters: Mapping[AuditBackend, BackendAdapter],
    environment: AuditEnvironmentIdentity,
    runner_source_sha256: str,
) -> AuditCampaignResult:
    """Execute every scheduled arm; backend and verification failures never truncate."""

    if not isinstance(plan, PreparedAuditPlan):
        raise TypeError("audit execution requires a prepared plan")
    if set(adapters) != set(ADR0311_BACKEND_ORDER):
        raise ValueError("audit execution requires exactly the three frozen backend arms")
    exact_cache: dict[str, ExactMicroEnumeration | AuditExceptionRecord] = {}
    observations: list[AuditInvocationObservation] = []
    for invocation in plan.schedule:
        task = plan.tasks[invocation.task_index]
        failures: list[AuditExceptionRecord] = []
        exact: ExactMicroEnumeration | None = None
        if task.exact_micro_case is not None:
            cached = exact_cache.get(task.base.base_id)
            if cached is None:
                try:
                    cached = enumerate_exact_micro_vertices(task.exact_micro_case)
                except Exception as error:  # noqa: BLE001 - exact-work failure is evidence
                    cached = AuditExceptionRecord.from_exception(
                        error,
                        stage=AuditFailureStage.INDEPENDENT_EXACT_ENUMERATION,
                    )
                exact_cache[task.base.base_id] = cached
            if isinstance(cached, ExactMicroEnumeration):
                exact = cached
            else:
                failures.append(cached)

        raw: BackendRawResult | None = None
        started = perf_counter()
        try:
            candidate = adapters[invocation.backend](task.materialized)
        except Exception as error:  # noqa: BLE001 - an arm failure cannot truncate the audit
            raw = BackendRawResult(
                backend=invocation.backend,
                termination=BackendTermination.EXCEPTION,
                status_code=None,
                status_text="adapter-exception",
                message=str(error),
                iterations=None,
                crossover_iterations=None,
                primal_variant_coordinates=None,
                reported_maximization_objective=None,
                dual_hint_variant_rows=None,
                dual_hint_convention=(
                    DualHintConvention.MAXIMIZATION_NONNEGATIVE
                    if invocation.backend is AuditBackend.NATIVE
                    else DualHintConvention.MINIMIZATION_NONPOSITIVE
                ),
                elapsed_seconds=float(perf_counter() - started),
                exception=AuditExceptionRecord.from_exception(
                    error,
                    stage=AuditFailureStage.BACKEND_INVOCATION,
                ),
            )
        else:
            if not isinstance(candidate, BackendRawResult):
                error = TypeError("backend adapter returned a nonsemantic result")
                failures.append(
                    AuditExceptionRecord.from_exception(
                        error,
                        stage=AuditFailureStage.BACKEND_SCHEMA,
                    )
                )
            elif candidate.backend is not invocation.backend:
                error = ValueError("backend result identity differs from its schedule arm")
                failures.append(
                    AuditExceptionRecord.from_exception(
                        error,
                        stage=AuditFailureStage.BACKEND_SCHEMA,
                    )
                )
            else:
                raw = candidate

        coordinate_diagnostics: BackendCoordinateDiagnostics | None = None
        certificate_diagnostics: BackendCertificateDiagnostics | None = None
        if raw is not None and raw.primal_variant_coordinates is not None:
            try:
                coordinate_diagnostics = build_backend_coordinate_diagnostics(
                    base=task.base,
                    descriptor=task.descriptor,
                    raw=raw,
                )
            except Exception as error:  # noqa: BLE001 - diagnostics must not truncate later arms
                failures.append(
                    AuditExceptionRecord.from_exception(
                        error,
                        stage=AuditFailureStage.COORDINATE_RECONSTRUCTION,
                    )
                )
        if raw is not None and raw.dual_hint_variant_rows is not None:
            try:
                certificate_diagnostics = build_backend_certificate_diagnostics(
                    base=task.base,
                    descriptor=task.descriptor,
                    raw=raw,
                )
            except Exception as error:  # noqa: BLE001 - diagnostics must not truncate later arms
                failures.append(
                    AuditExceptionRecord.from_exception(
                        error,
                        stage=AuditFailureStage.CERTIFICATE,
                    )
                )

        native_coordinates: NativeFailureCoordinates | None = None
        if raw is not None and raw.native_verification_trace is not None:
            try:
                native_coordinates = reconstruct_native_failure_coordinates(
                    raw.native_verification_trace,
                    task.descriptor,
                )
            except Exception as error:  # noqa: BLE001 - coordinate failure must be retained
                failures.append(
                    AuditExceptionRecord.from_exception(
                        error,
                        stage=AuditFailureStage.COORDINATE_RECONSTRUCTION,
                    )
                )

        micro_verification: MicroAuditVerification | None = None
        sizing_verification: SizingAuditVerification | None = None
        if raw is not None and raw.termination is BackendTermination.OPTIMAL:
            try:
                if task.base.family is AuditBaseFamily.EXACT_MICRO:
                    if exact is None:
                        raise ValueError("micro verification lacks exact independent work")
                    micro_verification = verify_micro_backend_result(
                        base=task.base,
                        descriptor=task.descriptor,
                        raw=raw,
                        exact=exact,
                    )
                else:
                    assert task.sizing_context is not None
                    sizing_verification = verify_sizing_backend_result(
                        base=task.base,
                        descriptor=task.descriptor,
                        raw=raw,
                        context=task.sizing_context,
                    )
            except Exception as error:  # noqa: BLE001 - verification failure must be retained
                failures.append(
                    AuditExceptionRecord.from_exception(
                        error,
                        stage=(
                            AuditFailureStage.CERTIFICATE
                            if isinstance(error, (FloatingPointError, OverflowError))
                            else AuditFailureStage.SEMANTIC_VERIFICATION
                        ),
                    )
                )

        observations.append(
            AuditInvocationObservation(
                invocation=invocation,
                backend_result=raw,
                exact_micro_work=exact,
                coordinate_diagnostics=coordinate_diagnostics,
                certificate_diagnostics=certificate_diagnostics,
                micro_verification=micro_verification,
                sizing_verification=sizing_verification,
                native_failure_coordinates=native_coordinates,
                runner_failures=tuple(failures),
            )
        )
    return AuditCampaignResult(
        runner_version=ADR0313_RUNNER_VERSION,
        runner_source_sha256=runner_source_sha256,
        corpus_sha256=plan.corpus_sha256,
        environment=environment,
        protocol=ADR0313_PROTOCOL,
        observations=tuple(observations),
        sealed_adr0311=plan.sealed_adr0311,
    )


@dataclass(frozen=True, slots=True)
class AuditGateFailure:
    code: str
    base_id: str | None
    variant_id: str | None
    backend: AuditBackend | None
    detail: str


@dataclass(frozen=True, slots=True)
class AuditGateAssessment:
    complete_schedule: bool
    known_native_regression_reproduced: bool
    highs_dual_simplex_eligible: bool
    failures: tuple[AuditGateFailure, ...]


def assess_adr0311_conjunctive_gate(
    campaign: AuditCampaignResult,
) -> AuditGateAssessment:
    """Apply ADR-0311's conjunctive interpretation without pooling failures."""

    complete = (
        campaign.sealed_adr0311
        and len(campaign.observations) == ADR0313_EXPECTED_INVOCATION_COUNT
        and tuple(observation.invocation.ordinal for observation in campaign.observations)
        == tuple(range(ADR0313_EXPECTED_INVOCATION_COUNT))
    )
    failures: list[AuditGateFailure] = []
    if not complete:
        failures.append(AuditGateFailure("incomplete-schedule", None, None, None, "schedule"))

    by_key = {
        (observation.invocation.variant_id, observation.invocation.backend): observation
        for observation in campaign.observations
    }
    known_variant = f"{ADR0311_KNOWN_REGRESSION_BASE_ID}--{AuditVariantKind.CANONICAL.value}"
    known = by_key.get((known_variant, AuditBackend.NATIVE))
    regression_reproduced = bool(
        known is not None
        and known.backend_result is not None
        and known.backend_result.termination is BackendTermination.EXCEPTION
        and known.backend_result.exception is not None
        and known.backend_result.exception.module == "builtins"
        and known.backend_result.exception.qualname == "AssertionError"
        and known.backend_result.exception.message
        == "linear-program solution fails primal verification"
        and known.backend_result.iterations == ADR0311_KNOWN_NATIVE_FAILURE_PIVOTS
        and known.native_failure_coordinates is not None
        and known.native_failure_coordinates.failing_canonical_rows
        == (ADR0311_KNOWN_NATIVE_FAILURE_ROW,)
        and known.native_failure_coordinates.maximum_variant_residual
        == ADR0311_KNOWN_NATIVE_FAILURE_MAXIMUM_RESIDUAL
        and known.native_failure_coordinates.verification_allowance
        == ADR0311_KNOWN_NATIVE_FAILURE_VERIFICATION_ALLOWANCE
    )
    if not regression_reproduced:
        failures.append(
            AuditGateFailure(
                "known-native-regression-mismatch",
                ADR0311_KNOWN_REGRESSION_BASE_ID,
                known_variant,
                AuditBackend.NATIVE,
                "expected exact call, AssertionError, pivot count, residual, and row 215",
            )
        )

    high_backends = (AuditBackend.HIGHS_DS, AuditBackend.HIGHS_IPM)
    high_observations = tuple(
        observation
        for observation in campaign.observations
        if observation.invocation.backend in high_backends
    )
    for observation in high_observations:
        if not observation.verified_pass:
            failures.append(
                AuditGateFailure(
                    "highs-instance-failed",
                    observation.invocation.base_id,
                    observation.invocation.variant_id,
                    observation.invocation.backend,
                    "backend, schema, semantic, or certificate failure",
                )
            )

    grouped: dict[str, list[AuditInvocationObservation]] = {}
    for observation in high_observations:
        grouped.setdefault(observation.invocation.base_id, []).append(observation)
    for base_id, observations in grouped.items():
        micro = tuple(
            observation.micro_verification
            for observation in observations
            if observation.micro_verification is not None
        )
        sizing = tuple(
            observation.sizing_verification
            for observation in observations
            if observation.sizing_verification is not None
        )
        if micro:
            values = tuple(item.reconstructed_objective for item in micro)
            if max(values) - min(values) > ADR0311_MICRO_VARIANT_COMPARISON_ALLOWANCE.value:
                failures.append(
                    AuditGateFailure(
                        "micro-variant-disagreement",
                        base_id,
                        None,
                        None,
                        "reconstructed objectives exceed the frozen allowance",
                    )
                )
        if sizing:
            lower = max(item.behavioral_lower_bound_chips for item in sizing)
            upper = min(item.certified_upper_bound_chips for item in sizing)
            if lower > upper + ADR0311_CROSS_VARIANT_SIZING_ALLOWANCE.chips:
                failures.append(
                    AuditGateFailure(
                        "sizing-interval-intersection-empty",
                        base_id,
                        None,
                        None,
                        "ten DS/IPM intervals have no allowed common intersection",
                    )
                )
            by_variant: dict[str, dict[AuditBackend, SizingAuditVerification]] = {}
            for observation in observations:
                if observation.sizing_verification is not None:
                    by_variant.setdefault(observation.invocation.variant_id, {})[
                        observation.invocation.backend
                    ] = observation.sizing_verification
            for variant_id, values_by_backend in by_variant.items():
                if set(values_by_backend) != set(high_backends):
                    continue
                difference = abs(
                    values_by_backend[AuditBackend.HIGHS_DS].behavioral_lower_bound_chips
                    - values_by_backend[AuditBackend.HIGHS_IPM].behavioral_lower_bound_chips
                )
                if difference > ADR0311_CROSS_BACKEND_SIZING_ALLOWANCE.chips:
                    failures.append(
                        AuditGateFailure(
                            "sizing-cross-backend-disagreement",
                            base_id,
                            variant_id,
                            None,
                            "DS/IPM reconstructed values exceed the frozen allowance",
                        )
                    )

    eligible = complete and regression_reproduced and not failures
    return AuditGateAssessment(
        complete_schedule=complete,
        known_native_regression_reproduced=regression_reproduced,
        highs_dual_simplex_eligible=eligible,
        failures=tuple(failures),
    )


def _runner_source_sha256() -> str:
    return sha256(Path(__file__).read_bytes()).hexdigest()


def execute_sealed_adr0311_audit(
    corpus: NativeSimplexAuditCorpus,
) -> AuditCampaignResult:
    """Execute the complete sealed campaign after all source/runtime gates pass."""

    from .native_simplex_audit_seal import ADR0313_RUNNER_SOURCE_SHA256

    source_sha256 = _runner_source_sha256()
    if source_sha256 != ADR0313_RUNNER_SOURCE_SHA256:
        raise RuntimeError("audit runner source differs from its committed seal")
    environment = capture_audit_environment_identity()
    if environment != ADR0313_EXPECTED_ENVIRONMENT:
        raise RuntimeError("audit runtime differs from its committed environment identity")
    plan = prepare_adr0311_audit(corpus)
    if len(plan.schedule) != ADR0313_EXPECTED_INVOCATION_COUNT:
        raise RuntimeError("audit schedule differs from the committed invocation count")
    return execute_audit_plan(
        plan,
        adapters=default_backend_adapters(),
        environment=environment,
        runner_source_sha256=source_sha256,
    )


__all__ = [
    "ADR0311_BACKEND_ORDER",
    "ADR0311_CROSS_BACKEND_SIZING_ALLOWANCE",
    "ADR0311_CROSS_VARIANT_SIZING_ALLOWANCE",
    "ADR0311_ENVELOPE_FEASIBILITY_ALLOWANCE",
    "ADR0311_HIGHS_DS_OPTIONS",
    "ADR0311_HIGHS_IPM_OPTIONS",
    "ADR0311_KNOWN_NATIVE_FAILURE_MAXIMUM_RESIDUAL",
    "ADR0311_KNOWN_NATIVE_FAILURE_PIVOTS",
    "ADR0311_KNOWN_NATIVE_FAILURE_ROW",
    "ADR0311_KNOWN_NATIVE_FAILURE_VERIFICATION_ALLOWANCE",
    "ADR0311_MICRO_DUAL_ALLOWANCE",
    "ADR0311_MICRO_OBJECTIVE_ALLOWANCE",
    "ADR0311_MICRO_PRIMAL_ALLOWANCE",
    "ADR0311_MICRO_VARIANT_COMPARISON_ALLOWANCE",
    "ADR0311_NATIVE_OPTIONS",
    "ADR0311_POLICY_NONNEGATIVITY_ALLOWANCE",
    "ADR0311_POLICY_SIMPLEX_MASS_ALLOWANCE",
    "ADR0311_SIZING_CERTIFICATE_WIDTH_ALLOWANCE",
    "ADR0311_SIZING_OBJECTIVE_ALLOWANCE",
    "ADR0313_EXPECTED_ENVIRONMENT",
    "ADR0313_EXPECTED_INVOCATION_COUNT",
    "ADR0313_PROTOCOL",
    "ADR0313_RUNNER_VERSION",
    "AuditBackend",
    "AuditCampaignResult",
    "AuditCheckFailure",
    "AuditEnvironmentIdentity",
    "AuditExceptionRecord",
    "AuditGateAssessment",
    "AuditInvocationObservation",
    "AuditProtocolIdentity",
    "BackendCertificateDiagnostics",
    "BackendCoordinateDiagnostics",
    "BackendRawResult",
    "BackendTermination",
    "DualHintConvention",
    "ExactMicroEnumeration",
    "ExactRational",
    "MicroAuditVerification",
    "NativeFailureCoordinates",
    "PreparedAuditPlan",
    "PreparedAuditTask",
    "ScheduledAuditInvocation",
    "SizingAuditVerification",
    "assess_adr0311_conjunctive_gate",
    "build_audit_schedule",
    "build_backend_certificate_diagnostics",
    "build_backend_coordinate_diagnostics",
    "canonical_audit_bytes",
    "capture_audit_environment_identity",
    "default_backend_adapters",
    "enumerate_exact_micro_vertices",
    "execute_audit_plan",
    "execute_sealed_adr0311_audit",
    "invoke_highs_backend",
    "invoke_native_backend",
    "map_primal_to_canonical",
    "prepare_adr0311_audit",
    "reconstruct_dual_hint",
    "reconstruct_native_failure_coordinates",
    "verify_micro_backend_result",
    "verify_sizing_backend_result",
]
