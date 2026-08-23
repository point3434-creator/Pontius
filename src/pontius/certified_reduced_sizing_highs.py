"""Certified HiGHS-DS proposer for canonical reduced river sizing LPs.

This is a successor-only adapter.  HiGHS proposes primal coordinates and row
multipliers; original-unit reconstruction and an outward-rounded bounded-box
certificate decide whether the proposal is usable.  The historical native
simplex consumer is intentionally not imported or modified here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from importlib import import_module
from itertools import pairwise
from math import fsum, isfinite
from numbers import Integral, Real
from pathlib import Path
from time import perf_counter
from typing import Any

from .linear_program_certificate import (
    BoundedMinimizationCertificate,
    certify_bounded_minimization_lower_bound,
)
from .reduced_river_sizing_lp import (
    LinearProgramConstraintUnit,
    ReducedRiverSizingLinearProgram,
    compile_reduced_river_sizing_lp,
)


class CertifiedSizingAdapterError(RuntimeError):
    """A HiGHS proposal failed the successor adapter's semantic gate."""


def _require_positive_finite(value: object, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{label} must be a real number")
    converted = float(value)
    if not isfinite(converted) or converted <= 0.0:
        raise ValueError(f"{label} must be positive and finite")
    return converted


@dataclass(frozen=True, slots=True)
class PolicyNonnegativityAllowance:
    value: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _require_positive_finite(
                self.value,
                label="policy nonnegativity allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class PolicySimplexMassAllowance:
    value: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _require_positive_finite(
                self.value,
                label="policy simplex-mass allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class EnvelopeFeasibilityAllowance:
    chips: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "chips",
            _require_positive_finite(
                self.chips,
                label="envelope feasibility allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class ReportedObjectiveAllowance:
    chips: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "chips",
            _require_positive_finite(
                self.chips,
                label="reported objective allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class BehavioralReconstructionAllowance:
    chips: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "chips",
            _require_positive_finite(
                self.chips,
                label="behavioral reconstruction allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class CertificateReversalAllowance:
    chips: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "chips",
            _require_positive_finite(
                self.chips,
                label="certificate reversal allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class CertificateWidthAllowance:
    chips: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "chips",
            _require_positive_finite(
                self.chips,
                label="certificate width allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class CertifiedSizingVerificationAllowances:
    policy_nonnegativity: PolicyNonnegativityAllowance
    policy_simplex_mass: PolicySimplexMassAllowance
    envelope_feasibility: EnvelopeFeasibilityAllowance
    reported_objective: ReportedObjectiveAllowance
    behavioral_reconstruction: BehavioralReconstructionAllowance
    certificate_reversal: CertificateReversalAllowance
    certificate_width: CertificateWidthAllowance

    def __post_init__(self) -> None:
        expected = (
            (self.policy_nonnegativity, PolicyNonnegativityAllowance),
            (self.policy_simplex_mass, PolicySimplexMassAllowance),
            (self.envelope_feasibility, EnvelopeFeasibilityAllowance),
            (self.reported_objective, ReportedObjectiveAllowance),
            (self.behavioral_reconstruction, BehavioralReconstructionAllowance),
            (self.certificate_reversal, CertificateReversalAllowance),
            (self.certificate_width, CertificateWidthAllowance),
        )
        for value, kind in expected:
            if not isinstance(value, kind):
                raise TypeError(
                    "certified sizing allowance bundle contains a nonsemantic field"
                )


ADR0318_CERTIFIED_SIZING_ALLOWANCES = CertifiedSizingVerificationAllowances(
    policy_nonnegativity=PolicyNonnegativityAllowance(1e-9),
    policy_simplex_mass=PolicySimplexMassAllowance(1e-9),
    envelope_feasibility=EnvelopeFeasibilityAllowance(1e-9),
    reported_objective=ReportedObjectiveAllowance(1e-9),
    behavioral_reconstruction=BehavioralReconstructionAllowance(1e-9),
    certificate_reversal=CertificateReversalAllowance(1e-9),
    certificate_width=CertificateWidthAllowance(1e-9),
)


@dataclass(frozen=True, slots=True)
class HighsDualSimplexSizingOptions:
    method: str
    presolve: bool
    primal_feasibility_tolerance: float
    dual_feasibility_tolerance: float
    maximum_iterations: int

    def __post_init__(self) -> None:
        if self.method != "highs-ds":
            raise ValueError("certified sizing method must be highs-ds")
        if self.presolve is not True:
            raise ValueError("certified sizing presolve must remain enabled")
        object.__setattr__(
            self,
            "primal_feasibility_tolerance",
            _require_positive_finite(
                self.primal_feasibility_tolerance,
                label="HiGHS primal tolerance",
            ),
        )
        object.__setattr__(
            self,
            "dual_feasibility_tolerance",
            _require_positive_finite(
                self.dual_feasibility_tolerance,
                label="HiGHS dual tolerance",
            ),
        )
        if (
            isinstance(self.maximum_iterations, bool)
            or not isinstance(self.maximum_iterations, int)
            or self.maximum_iterations <= 0
        ):
            raise ValueError("HiGHS maximum iterations must be a positive integer")

    @property
    def scipy_options(self) -> dict[str, object]:
        return {
            "presolve": self.presolve,
            "primal_feasibility_tolerance": self.primal_feasibility_tolerance,
            "dual_feasibility_tolerance": self.dual_feasibility_tolerance,
            "maxiter": self.maximum_iterations,
        }


ADR0318_HIGHS_DS_OPTIONS = HighsDualSimplexSizingOptions(
    method="highs-ds",
    presolve=True,
    primal_feasibility_tolerance=1e-10,
    dual_feasibility_tolerance=1e-10,
    maximum_iterations=4_096,
)


@dataclass(frozen=True, slots=True)
class PolicyClip:
    variable_index: int
    raw_value: float
    clipped_value: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.variable_index, bool)
            or not isinstance(self.variable_index, int)
            or self.variable_index < 0
        ):
            raise ValueError("policy clip index must be nonnegative")
        if not all(isinstance(value, float) and isfinite(value) for value in self.values):
            raise ValueError("policy clip values must be finite floats")

    @property
    def values(self) -> tuple[float, float]:
        return self.raw_value, self.clipped_value


@dataclass(frozen=True, slots=True)
class CertifiedReducedSizingSolution:
    linear_program_sha256: str
    bet_sizes: tuple[int, ...]
    raw_primal_variables: tuple[float, ...]
    raw_inequality_multipliers: tuple[float, ...]
    opening_policy: tuple[tuple[float, ...], ...]
    exact_opening_policy: tuple[tuple[Fraction, ...], ...]
    responder_best_actions: tuple[tuple[str, ...], ...]
    policy_clips: tuple[PolicyClip, ...]
    reported_value_chips: float
    canonical_raw_value_chips: float
    feasible_behavioral_lower_bound_chips: float
    certified_upper_bound_chips: float
    signed_certificate_gap_chips: float
    certified_gap_chips: float
    maximum_policy_nonnegativity_violation: float
    maximum_policy_upper_violation: float
    maximum_raw_policy_mass_residual: float
    maximum_postclip_policy_mass_residual: float
    maximum_dimensionless_row_violation: float
    maximum_envelope_nonnegativity_violation_chips: float
    maximum_envelope_upper_violation_chips: float
    maximum_envelope_row_violation_chips: float
    reported_objective_error_chips: float
    behavioral_reconstruction_error_chips: float
    certificate: BoundedMinimizationCertificate
    highs_status_code: int
    highs_message: str
    highs_iterations: int
    solver_wall_seconds: float
    verification_wall_seconds: float

    def __post_init__(self) -> None:
        if (
            len(self.linear_program_sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.linear_program_sha256)
        ):
            raise ValueError("certified sizing LP digest is invalid")
        if not isinstance(self.certificate, BoundedMinimizationCertificate):
            raise TypeError("certified sizing result requires a semantic certificate")
        if (
            not isinstance(self.bet_sizes, tuple)
            or not self.bet_sizes
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
                for value in self.bet_sizes
            )
            or any(left >= right for left, right in pairwise(self.bet_sizes))
        ):
            raise ValueError("certified sizing bet sizes are invalid")
        action_count = 1 + len(self.bet_sizes)
        if not isinstance(self.exact_opening_policy, tuple) or not self.exact_opening_policy:
            raise TypeError("certified sizing exact policy must be nonempty and immutable")
        if any(
            not isinstance(row, tuple)
            or len(row) != action_count
            or any(not isinstance(value, Fraction) or value < 0 for value in row)
            or sum(row, start=Fraction(0)) != 1
            for row in self.exact_opening_policy
        ):
            raise ValueError("certified sizing exact policy is not row-stochastic")
        expected_float_policy = tuple(
            tuple(float(value) for value in row) for row in self.exact_opening_policy
        )
        if self.opening_policy != expected_float_policy:
            raise ValueError("certified sizing float policy differs from exact policy")
        if not isinstance(self.responder_best_actions, tuple) or not self.responder_best_actions:
            raise TypeError("certified sizing response actions must be nonempty and immutable")
        if any(
            not isinstance(row, tuple)
            or len(row) != len(self.bet_sizes)
            or any(action not in {"fold", "call"} for action in row)
            for row in self.responder_best_actions
        ):
            raise ValueError("certified sizing response actions are malformed")
        opener_count = len(self.exact_opening_policy)
        responder_count = len(self.responder_best_actions)
        expected_variable_count = (
            opener_count * action_count + responder_count * len(self.bet_sizes)
        )
        expected_row_count = 2 * opener_count + 2 * responder_count * len(self.bet_sizes)
        if len(self.raw_primal_variables) != expected_variable_count:
            raise ValueError("certified sizing raw primal width is inconsistent")
        if len(self.raw_inequality_multipliers) != expected_row_count:
            raise ValueError("certified sizing multiplier width is inconsistent")
        if not isinstance(self.policy_clips, tuple) or any(
            not isinstance(clip, PolicyClip)
            or clip.variable_index >= opener_count * action_count
            for clip in self.policy_clips
        ):
            raise TypeError("certified sizing policy clips are malformed")
        if self.highs_status_code != 0:
            raise ValueError("certified sizing result must retain optimal HiGHS status")
        if (
            isinstance(self.highs_iterations, bool)
            or not isinstance(self.highs_iterations, int)
            or self.highs_iterations < 0
        ):
            raise ValueError("certified sizing iteration count must be nonnegative")
        if not isinstance(self.highs_message, str) or not self.highs_message:
            raise ValueError("certified sizing HiGHS message must be nonempty")
        numeric = (
            *self.raw_primal_variables,
            *self.raw_inequality_multipliers,
            self.reported_value_chips,
            self.canonical_raw_value_chips,
            self.feasible_behavioral_lower_bound_chips,
            self.certified_upper_bound_chips,
            self.signed_certificate_gap_chips,
            self.certified_gap_chips,
            self.maximum_policy_nonnegativity_violation,
            self.maximum_policy_upper_violation,
            self.maximum_raw_policy_mass_residual,
            self.maximum_postclip_policy_mass_residual,
            self.maximum_dimensionless_row_violation,
            self.maximum_envelope_nonnegativity_violation_chips,
            self.maximum_envelope_upper_violation_chips,
            self.maximum_envelope_row_violation_chips,
            self.reported_objective_error_chips,
            self.behavioral_reconstruction_error_chips,
            self.solver_wall_seconds,
            self.verification_wall_seconds,
        )
        if any(not isinstance(value, float) or not isfinite(value) for value in numeric):
            raise ValueError("certified sizing result contains a nonfinite diagnostic")
        if self.certified_gap_chips < 0.0:
            raise ValueError("certified sizing reported gap must be nonnegative")
        if self.signed_certificate_gap_chips != (
            self.certified_upper_bound_chips
            - self.feasible_behavioral_lower_bound_chips
        ):
            raise ValueError("certified sizing signed gap is inconsistent")
        if self.certified_gap_chips != max(0.0, self.signed_certificate_gap_chips):
            raise ValueError("certified sizing nonnegative gap is inconsistent")
        magnitudes = (
            self.maximum_policy_nonnegativity_violation,
            self.maximum_policy_upper_violation,
            self.maximum_raw_policy_mass_residual,
            self.maximum_postclip_policy_mass_residual,
            self.maximum_dimensionless_row_violation,
            self.maximum_envelope_nonnegativity_violation_chips,
            self.maximum_envelope_upper_violation_chips,
            self.maximum_envelope_row_violation_chips,
            self.reported_objective_error_chips,
            self.behavioral_reconstruction_error_chips,
            self.solver_wall_seconds,
            self.verification_wall_seconds,
        )
        if any(value < 0.0 for value in magnitudes):
            raise ValueError("certified sizing diagnostic magnitude is negative")


def _finite_tuple(value: object, width: int, *, label: str) -> tuple[float, ...]:
    if isinstance(value, (str, bytes)):
        raise CertifiedSizingAdapterError(f"HiGHS {label} is not a numeric vector")
    try:
        materialized = tuple(value)  # type: ignore[arg-type]
    except TypeError as error:
        raise CertifiedSizingAdapterError(f"HiGHS {label} is not iterable") from error
    if len(materialized) != width:
        raise CertifiedSizingAdapterError(f"HiGHS {label} has the wrong width")
    converted: list[float] = []
    for item in materialized:
        if isinstance(item, bool) or not isinstance(item, Real):
            raise CertifiedSizingAdapterError(f"HiGHS {label} contains a non-real value")
        number = float(item)
        if not isfinite(number):
            raise CertifiedSizingAdapterError(f"HiGHS {label} contains a nonfinite value")
        converted.append(number)
    return tuple(converted)


def _required_real(value: object, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise CertifiedSizingAdapterError(f"HiGHS {label} is not real")
    converted = float(value)
    if not isfinite(converted):
        raise CertifiedSizingAdapterError(f"HiGHS {label} is nonfinite")
    return converted


def _required_nonnegative_int(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise CertifiedSizingAdapterError(f"HiGHS {label} is not an integer")
    converted = int(value)
    if converted < 0:
        raise CertifiedSizingAdapterError(f"HiGHS {label} is negative")
    return converted


def _exact_behavioral_value(
    *,
    pot: int,
    joint_probabilities: tuple[tuple[Fraction, ...], ...],
    showdown_signs: tuple[tuple[int, ...], ...],
    bet_sizes: tuple[int, ...],
    policy: tuple[tuple[Fraction, ...], ...],
) -> tuple[Fraction, tuple[tuple[str, ...], ...]]:
    half_pot = Fraction(pot, 2)
    value = Fraction(0)
    opener_count = len(joint_probabilities)
    responder_count = len(joint_probabilities[0])
    for opener in range(opener_count):
        for responder in range(responder_count):
            value += (
                joint_probabilities[opener][responder]
                * policy[opener][0]
                * showdown_signs[opener][responder]
                * half_pot
            )
    best_actions: list[tuple[str, ...]] = []
    for responder in range(responder_count):
        actions: list[str] = []
        for bet_index, bet in enumerate(bet_sizes):
            fold = sum(
                (
                    joint_probabilities[opener][responder]
                    * policy[opener][bet_index + 1]
                    * half_pot
                    for opener in range(opener_count)
                ),
                start=Fraction(0),
            )
            call = sum(
                (
                    joint_probabilities[opener][responder]
                    * policy[opener][bet_index + 1]
                    * showdown_signs[opener][responder]
                    * (half_pot + bet)
                    for opener in range(opener_count)
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


def _clip_and_normalize_policy(
    variables: tuple[float, ...],
    linear_program: ReducedRiverSizingLinearProgram,
    allowance: PolicyNonnegativityAllowance,
) -> tuple[
    tuple[tuple[Fraction, ...], ...],
    tuple[PolicyClip, ...],
    float,
    float,
    float,
    float,
]:
    layout = linear_program.layout
    clipped = list(variables[: layout.policy_variable_count])
    maximum_negative = max((max(0.0, -value) for value in clipped), default=0.0)
    maximum_upper = max((max(0.0, value - 1.0) for value in clipped), default=0.0)
    if max(maximum_negative, maximum_upper) > allowance.value:
        raise CertifiedSizingAdapterError("HiGHS policy exceeds its nonnegativity allowance")
    clips: list[PolicyClip] = []
    for index, value in enumerate(clipped):
        replacement = value
        if value < 0.0:
            replacement = 0.0
        elif value > 1.0:
            replacement = 1.0
        if replacement != value:
            clips.append(PolicyClip(index, value, replacement))
            clipped[index] = replacement

    exact_rows: list[tuple[Fraction, ...]] = []
    maximum_raw_mass = 0.0
    maximum_postclip_mass = 0.0
    for opener in range(layout.opener_count):
        start = opener * layout.action_count
        raw = variables[start : start + layout.action_count]
        row = tuple(clipped[start : start + layout.action_count])
        maximum_raw_mass = max(maximum_raw_mass, abs(fsum(raw) - 1.0))
        maximum_postclip_mass = max(maximum_postclip_mass, abs(fsum(row) - 1.0))
        exact = tuple(Fraction.from_float(value) for value in row)
        total = sum(exact, start=Fraction(0))
        if total <= 0 or any(value < 0 for value in exact):
            raise CertifiedSizingAdapterError("HiGHS policy row cannot be normalized")
        exact_rows.append(tuple(value / total for value in exact))
    return (
        tuple(exact_rows),
        tuple(clips),
        maximum_negative,
        maximum_upper,
        maximum_raw_mass,
        maximum_postclip_mass,
    )


def canonical_lf_source_sha256(path: Path) -> str:
    """Hash source bytes after explicit line-ending canonicalization."""

    raw = path.read_bytes()
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return sha256(normalized).hexdigest()


def verify_adr0318_source_and_dependencies() -> None:
    """Fail before a sealed adapter run when committed source identity drifts."""

    from .certified_reduced_sizing_highs_seal import ADR0318_SOURCE_MANIFEST

    root = Path(__file__).resolve().parents[1]
    actual = {
        "certified_reduced_sizing_highs.py": canonical_lf_source_sha256(Path(__file__)),
        "linear_program_certificate.py": canonical_lf_source_sha256(
            root / "pontius" / "linear_program_certificate.py"
        ),
        "reduced_river_sizing_lp.py": canonical_lf_source_sha256(
            root / "pontius" / "reduced_river_sizing_lp.py"
        ),
    }
    if actual != ADR0318_SOURCE_MANIFEST:
        raise RuntimeError("ADR-0318 source or dependency differs from its committed seal")


def verify_adr0318_runtime_identity() -> None:
    """Fail before sealed work when the frozen public solver runtime drifts."""

    import sys

    import numpy
    import scipy
    from scipy.optimize._highspy._core import (  # type: ignore[attr-defined]
        HIGHS_VERSION_MAJOR,
        HIGHS_VERSION_MINOR,
        HIGHS_VERSION_PATCH,
    )

    from .certified_reduced_sizing_highs_seal import ADR0318_EXPECTED_RUNTIME

    actual = {
        "python": ".".join(str(value) for value in sys.version_info[:3]),
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "highs": f"{HIGHS_VERSION_MAJOR}.{HIGHS_VERSION_MINOR}.{HIGHS_VERSION_PATCH}",
    }
    if actual != ADR0318_EXPECTED_RUNTIME:
        raise RuntimeError("ADR-0318 runtime differs from its committed identity")


def solve_certified_reduced_sizing_highs(
    *,
    pot: int,
    stack: int,
    minimum_bet: int,
    joint_probabilities: tuple[tuple[Fraction, ...], ...],
    showdown_signs: tuple[tuple[int, ...], ...],
    bet_sizes: tuple[int, ...],
    options: HighsDualSimplexSizingOptions = ADR0318_HIGHS_DS_OPTIONS,
    allowances: CertifiedSizingVerificationAllowances = (
        ADR0318_CERTIFIED_SIZING_ALLOWANCES
    ),
    linprog_function: Callable[..., Any] | None = None,
) -> CertifiedReducedSizingSolution:
    """Return one certified canonical sizing solution or fail closed."""

    if not isinstance(options, HighsDualSimplexSizingOptions):
        raise TypeError("certified sizing options must be semantic")
    if not isinstance(allowances, CertifiedSizingVerificationAllowances):
        raise TypeError("certified sizing allowances must be semantic")
    if options != ADR0318_HIGHS_DS_OPTIONS:
        raise ValueError("certified sizing options differ from the frozen contract")
    if allowances != ADR0318_CERTIFIED_SIZING_ALLOWANCES:
        raise ValueError("certified sizing allowances differ from the frozen contract")
    linear_program = compile_reduced_river_sizing_lp(
        pot=pot,
        stack=stack,
        minimum_bet=minimum_bet,
        joint_probabilities=joint_probabilities,
        showdown_signs=showdown_signs,
        bet_sizes=bet_sizes,
    )
    if linprog_function is None:
        linprog_function = import_module("scipy.optimize").linprog

    solver_started = perf_counter()
    try:
        solved = linprog_function(
            tuple(-value for value in linear_program.objective),
            A_ub=linear_program.coefficients,
            b_ub=linear_program.bounds,
            bounds=tuple(
                zip(
                    linear_program.trusted_box_lower_bounds,
                    linear_program.trusted_box_upper_bounds,
                    strict=True,
                )
            ),
            method=options.method,
            options=options.scipy_options,
        )
    except Exception as error:  # noqa: BLE001 - backend failures are adapter rejection
        raise CertifiedSizingAdapterError("HiGHS invocation failed") from error
    solver_wall = float(perf_counter() - solver_started)
    verification_started = perf_counter()

    success = getattr(solved, "success", None)
    if not isinstance(success, bool):
        raise CertifiedSizingAdapterError("HiGHS success field is not boolean")
    status = _required_nonnegative_int(getattr(solved, "status", None), label="status")
    message = getattr(solved, "message", None)
    if not isinstance(message, str) or not message:
        raise CertifiedSizingAdapterError("HiGHS message is missing")
    if not success or status != 0:
        raise CertifiedSizingAdapterError(
            f"HiGHS did not return an optimal solution: status={status}"
        )
    variables = _finite_tuple(
        getattr(solved, "x", None),
        linear_program.layout.variable_count,
        label="primal variables",
    )
    raw_fun = _required_real(getattr(solved, "fun", None), label="objective")
    iterations = _required_nonnegative_int(
        getattr(solved, "nit", None),
        label="iteration count",
    )
    ineqlin = getattr(solved, "ineqlin", None)
    if ineqlin is None:
        raise CertifiedSizingAdapterError("HiGHS inequality result is missing")
    multipliers = _finite_tuple(
        getattr(ineqlin, "marginals", None),
        len(linear_program.rows),
        label="inequality multipliers",
    )

    (
        exact_policy,
        policy_clips,
        maximum_negative,
        maximum_upper,
        maximum_raw_mass,
        maximum_postclip_mass,
    ) = _clip_and_normalize_policy(
        variables,
        linear_program,
        allowances.policy_nonnegativity,
    )
    if (
        max(maximum_raw_mass, maximum_postclip_mass)
        > allowances.policy_simplex_mass.value
    ):
        raise CertifiedSizingAdapterError("HiGHS policy exceeds its simplex-mass allowance")

    residuals = tuple(
        fsum(
            coefficient * value
            for coefficient, value in zip(row.coefficients, variables, strict=True)
        )
        - row.bound
        for row in linear_program.rows
    )
    maximum_dimensionless_row = max(
        (
            max(0.0, residual)
            for residual, row in zip(residuals, linear_program.rows, strict=True)
            if row.unit is LinearProgramConstraintUnit.DIMENSIONLESS
        ),
        default=0.0,
    )
    maximum_envelope_row = max(
        (
            max(0.0, residual)
            for residual, row in zip(residuals, linear_program.rows, strict=True)
            if row.unit is LinearProgramConstraintUnit.CHIPS
        ),
        default=0.0,
    )
    if maximum_dimensionless_row > allowances.policy_simplex_mass.value:
        raise CertifiedSizingAdapterError("HiGHS dimensionless rows exceed their allowance")
    envelope = variables[linear_program.layout.policy_variable_count :]
    maximum_envelope_negative = max(
        (max(0.0, -value) for value in envelope),
        default=0.0,
    )
    maximum_envelope_upper = max(
        (max(0.0, value - linear_program.payoff_span_chips) for value in envelope),
        default=0.0,
    )
    if (
        max(
            maximum_envelope_negative,
            maximum_envelope_upper,
            maximum_envelope_row,
        )
        > allowances.envelope_feasibility.chips
    ):
        raise CertifiedSizingAdapterError("HiGHS chip-envelope rows exceed their allowance")

    canonical_raw_value = (
        fsum(
            coefficient * value
            for coefficient, value in zip(
                linear_program.objective,
                variables,
                strict=True,
            )
        )
        + linear_program.objective_offset_chips
    )
    reported_value = -raw_fun + linear_program.objective_offset_chips
    reported_error = abs(reported_value - canonical_raw_value)
    if reported_error > allowances.reported_objective.chips:
        raise CertifiedSizingAdapterError("HiGHS reported objective differs from reconstruction")

    exact_behavioral, responder_actions = _exact_behavioral_value(
        pot=pot,
        joint_probabilities=joint_probabilities,
        showdown_signs=showdown_signs,
        bet_sizes=linear_program.bet_sizes,
        policy=exact_policy,
    )
    behavioral_lower = float(exact_behavioral)
    behavioral_error = abs(canonical_raw_value - behavioral_lower)
    if behavioral_error > allowances.behavioral_reconstruction.chips:
        raise CertifiedSizingAdapterError("HiGHS policy value differs from exact reconstruction")

    certificate = certify_bounded_minimization_lower_bound(
        tuple(-value for value in linear_program.objective),
        linear_program.coefficients,
        linear_program.bounds,
        multipliers,
        variable_lower_bounds=linear_program.trusted_box_lower_bounds,
        variable_upper_bounds=linear_program.trusted_box_upper_bounds,
    )
    certified_upper = -certificate.lower_bound + linear_program.objective_offset_chips
    signed_gap = certified_upper - behavioral_lower
    if signed_gap < -allowances.certificate_reversal.chips:
        raise CertifiedSizingAdapterError("certified sizing interval is materially reversed")
    if signed_gap > allowances.certificate_width.chips:
        raise CertifiedSizingAdapterError("certified sizing interval exceeds its width allowance")
    verification_wall = float(perf_counter() - verification_started)

    return CertifiedReducedSizingSolution(
        linear_program_sha256=linear_program.digest,
        bet_sizes=linear_program.bet_sizes,
        raw_primal_variables=variables,
        raw_inequality_multipliers=multipliers,
        opening_policy=tuple(
            tuple(float(value) for value in row) for row in exact_policy
        ),
        exact_opening_policy=exact_policy,
        responder_best_actions=responder_actions,
        policy_clips=policy_clips,
        reported_value_chips=reported_value,
        canonical_raw_value_chips=canonical_raw_value,
        feasible_behavioral_lower_bound_chips=behavioral_lower,
        certified_upper_bound_chips=certified_upper,
        signed_certificate_gap_chips=signed_gap,
        certified_gap_chips=max(0.0, signed_gap),
        maximum_policy_nonnegativity_violation=maximum_negative,
        maximum_policy_upper_violation=maximum_upper,
        maximum_raw_policy_mass_residual=maximum_raw_mass,
        maximum_postclip_policy_mass_residual=maximum_postclip_mass,
        maximum_dimensionless_row_violation=maximum_dimensionless_row,
        maximum_envelope_nonnegativity_violation_chips=maximum_envelope_negative,
        maximum_envelope_upper_violation_chips=maximum_envelope_upper,
        maximum_envelope_row_violation_chips=maximum_envelope_row,
        reported_objective_error_chips=reported_error,
        behavioral_reconstruction_error_chips=behavioral_error,
        certificate=certificate,
        highs_status_code=status,
        highs_message=message,
        highs_iterations=iterations,
        solver_wall_seconds=solver_wall,
        verification_wall_seconds=verification_wall,
    )


__all__ = [
    "ADR0318_CERTIFIED_SIZING_ALLOWANCES",
    "ADR0318_HIGHS_DS_OPTIONS",
    "BehavioralReconstructionAllowance",
    "CertificateReversalAllowance",
    "CertificateWidthAllowance",
    "CertifiedReducedSizingSolution",
    "CertifiedSizingAdapterError",
    "CertifiedSizingVerificationAllowances",
    "EnvelopeFeasibilityAllowance",
    "HighsDualSimplexSizingOptions",
    "PolicyClip",
    "PolicyNonnegativityAllowance",
    "PolicySimplexMassAllowance",
    "ReportedObjectiveAllowance",
    "canonical_lf_source_sha256",
    "solve_certified_reduced_sizing_highs",
    "verify_adr0318_runtime_identity",
    "verify_adr0318_source_and_dependencies",
]
