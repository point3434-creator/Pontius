"""Typed tolerance semantics for successor convex-retreat experiments.

Historical experiments sometimes reused one numerical value for distinct gates.
The wrappers in this module are deliberately nominal: equal floating-point values
remain non-interchangeable when they mean different things.  Frozen v1 runners
retain their original APIs; successor preregistrations should parse their tolerance
block here and pass the resulting types to the matching gate functions.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypeVar

_TOLERANCE_KEYS = frozenset(
    {
        "relative_reversal_allowance",
        "absolute_reversal_allowance",
        "absolute_u_l_gap_allowance",
        "selector_margin_allowance",
        "intercept_identity_allowance",
        "epigraph_separation_allowance",
        "resident_primal_residual_allowance",
    }
)


def _finite_nonnegative(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a plain JSON number")
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0.0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return parsed


@dataclass(frozen=True, slots=True)
class RelativeReversalAllowance:
    """Dimensionless allowance for a numerical lower-over-upper reversal."""

    relative_fraction: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "relative_fraction",
            _finite_nonnegative(
                self.relative_fraction,
                label="relative reversal allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class AbsoluteReversalAllowance:
    """Absolute floor for lower-over-upper reversal in payoff units."""

    absolute_error: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "absolute_error",
            _finite_nonnegative(
                self.absolute_error,
                label="absolute reversal allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class AbsoluteULGapAllowance:
    """Absolute acceptance allowance for the minimization gap U-L."""

    absolute_gap: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "absolute_gap",
            _finite_nonnegative(
                self.absolute_gap,
                label="absolute U-L gap allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class SelectorMarginAllowance:
    """Allowance used only when conservatively locating selector switches."""

    absolute_margin: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "absolute_margin",
            _finite_nonnegative(
                self.absolute_margin,
                label="selector margin allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class InterceptIdentityAllowance:
    """Absolute error allowed in the affine source-intercept identity."""

    absolute_error: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "absolute_error",
            _finite_nonnegative(
                self.absolute_error,
                label="intercept identity allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class EpigraphSeparationAllowance:
    """Positive residual required before requesting epigraph separation."""

    absolute_residual: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "absolute_residual",
            _finite_nonnegative(
                self.absolute_residual,
                label="epigraph separation allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class ResidentPrimalResidualAllowance:
    """Absolute primal residual tolerated for an already-resident epigraph row."""

    absolute_residual: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "absolute_residual",
            _finite_nonnegative(
                self.absolute_residual,
                label="resident primal residual allowance",
            ),
        )


@dataclass(frozen=True, slots=True)
class ConvexRetreatTolerances:
    """Complete successor tolerance contract with non-interchangeable fields."""

    relative_reversal: RelativeReversalAllowance
    absolute_reversal: AbsoluteReversalAllowance
    absolute_u_l_gap: AbsoluteULGapAllowance
    selector_margin: SelectorMarginAllowance
    intercept_identity: InterceptIdentityAllowance
    epigraph_separation: EpigraphSeparationAllowance
    resident_primal_residual: ResidentPrimalResidualAllowance

    def __post_init__(self) -> None:
        expected = (
            ("relative_reversal", self.relative_reversal, RelativeReversalAllowance),
            ("absolute_reversal", self.absolute_reversal, AbsoluteReversalAllowance),
            ("absolute_u_l_gap", self.absolute_u_l_gap, AbsoluteULGapAllowance),
            ("selector_margin", self.selector_margin, SelectorMarginAllowance),
            (
                "intercept_identity",
                self.intercept_identity,
                InterceptIdentityAllowance,
            ),
            (
                "epigraph_separation",
                self.epigraph_separation,
                EpigraphSeparationAllowance,
            ),
            (
                "resident_primal_residual",
                self.resident_primal_residual,
                ResidentPrimalResidualAllowance,
            ),
        )
        for label, value, kind in expected:
            if type(value) is not kind:
                raise TypeError(f"{label} requires {kind.__name__}")


def parse_convex_retreat_tolerances(
    config: Mapping[str, Any],
) -> ConvexRetreatTolerances:
    """Parse an exact successor config block; legacy alias keys fail closed."""

    if not isinstance(config, Mapping):
        raise TypeError("convex-retreat tolerances must be a mapping")
    supplied = set(config)
    if supplied != _TOLERANCE_KEYS:
        missing = sorted(_TOLERANCE_KEYS - supplied)
        extra = sorted(supplied - _TOLERANCE_KEYS)
        raise ValueError(
            "convex-retreat tolerance schema mismatch: "
            f"missing={missing}, extra={extra}"
        )
    return ConvexRetreatTolerances(
        relative_reversal=RelativeReversalAllowance(
            config["relative_reversal_allowance"]
        ),
        absolute_reversal=AbsoluteReversalAllowance(
            config["absolute_reversal_allowance"]
        ),
        absolute_u_l_gap=AbsoluteULGapAllowance(
            config["absolute_u_l_gap_allowance"]
        ),
        selector_margin=SelectorMarginAllowance(
            config["selector_margin_allowance"]
        ),
        intercept_identity=InterceptIdentityAllowance(
            config["intercept_identity_allowance"]
        ),
        epigraph_separation=EpigraphSeparationAllowance(
            config["epigraph_separation_allowance"]
        ),
        resident_primal_residual=ResidentPrimalResidualAllowance(
            config["resident_primal_residual_allowance"]
        ),
    )


_Allowance = TypeVar("_Allowance")


def _require_exact_allowance(
    allowance: Any,
    kind: type[_Allowance],
    *,
    gate: str,
) -> _Allowance:
    if type(allowance) is not kind:
        raise TypeError(f"{gate} requires {kind.__name__}")
    return allowance


def bounded_minimization_gap(
    upper: float,
    lower: float,
    *,
    reversal_allowance: RelativeReversalAllowance,
    absolute_reversal_allowance: AbsoluteReversalAllowance,
) -> float:
    """Return max(0, U-L) under explicit relative and absolute semantics."""

    typed = _require_exact_allowance(
        reversal_allowance,
        RelativeReversalAllowance,
        gate="minimization-bound reversal gate",
    )
    absolute = _require_exact_allowance(
        absolute_reversal_allowance,
        AbsoluteReversalAllowance,
        gate="minimization-bound reversal gate",
    )
    values = (float(upper), float(lower))
    if any(not math.isfinite(value) for value in values):
        raise ValueError("minimization bounds must be finite")
    if any(value < 0.0 for value in values):
        raise ValueError("minimization bounds must be nonnegative")
    gap = values[0] - values[1]
    scaled_allowance = max(
        absolute.absolute_error,
        typed.relative_fraction * max(abs(value) for value in values),
    )
    if gap < -scaled_allowance:
        raise ArithmeticError("restricted lower bound exceeds incumbent")
    return max(0.0, gap)


def absolute_u_l_gap_is_accepted(
    gap: float,
    *,
    gap_allowance: AbsoluteULGapAllowance,
) -> bool:
    """Apply the absolute U-L closure gate, independently of reversal logic."""

    typed = _require_exact_allowance(
        gap_allowance,
        AbsoluteULGapAllowance,
        gate="absolute U-L gap gate",
    )
    parsed = float(gap)
    if not math.isfinite(parsed) or parsed < 0.0:
        raise ValueError("U-L gap must be finite and nonnegative")
    return parsed <= typed.absolute_gap


def selector_margin_is_conservative(
    margin: float,
    *,
    margin_allowance: SelectorMarginAllowance,
) -> bool:
    """Return whether a selector comparison remains conservatively admissible."""

    typed = _require_exact_allowance(
        margin_allowance,
        SelectorMarginAllowance,
        gate="selector margin gate",
    )
    parsed = float(margin)
    if not math.isfinite(parsed):
        raise ValueError("selector margin must be finite")
    return parsed >= -typed.absolute_margin


def intercept_identity_is_accepted(
    identity_error: float,
    *,
    identity_allowance: InterceptIdentityAllowance,
) -> bool:
    """Apply the affine source-intercept identity gate only."""

    typed = _require_exact_allowance(
        identity_allowance,
        InterceptIdentityAllowance,
        gate="intercept identity gate",
    )
    parsed = float(identity_error)
    if not math.isfinite(parsed) or parsed < 0.0:
        raise ValueError("intercept identity error must be finite and nonnegative")
    return parsed <= typed.absolute_error


def epigraph_separation_is_required(
    residual: float,
    *,
    separation_allowance: EpigraphSeparationAllowance,
) -> bool:
    """Return whether raw_gain-epigraph is large enough to request a cut."""

    typed = _require_exact_allowance(
        separation_allowance,
        EpigraphSeparationAllowance,
        gate="epigraph separation gate",
    )
    parsed = float(residual)
    if not math.isfinite(parsed):
        raise ValueError("epigraph residual must be finite")
    return parsed > typed.absolute_residual


def resident_primal_residual_is_accepted(
    residual: float,
    *,
    residual_allowance: ResidentPrimalResidualAllowance,
) -> bool:
    """Apply the resident-row master-primal residual gate only."""

    typed = _require_exact_allowance(
        residual_allowance,
        ResidentPrimalResidualAllowance,
        gate="resident primal residual gate",
    )
    parsed = float(residual)
    if not math.isfinite(parsed):
        raise ValueError("resident primal residual must be finite")
    return parsed <= typed.absolute_residual


# These values reproduce the currently frozen h32 numerical choices, while the
# nominal types prevent their equality from becoming a semantic alias in v2.
H32_V1_NUMERICALLY_EQUIVALENT_TOLERANCES = ConvexRetreatTolerances(
    relative_reversal=RelativeReversalAllowance(1e-8),
    absolute_reversal=AbsoluteReversalAllowance(1e-8),
    absolute_u_l_gap=AbsoluteULGapAllowance(1e-8),
    selector_margin=SelectorMarginAllowance(2e-11),
    intercept_identity=InterceptIdentityAllowance(2e-11),
    epigraph_separation=EpigraphSeparationAllowance(1e-9),
    resident_primal_residual=ResidentPrimalResidualAllowance(1e-8),
)
