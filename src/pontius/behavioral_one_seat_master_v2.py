"""Certified successor to the historical behavioral one-seat master.

V1 reports the Float64 primal objective as its lower bound.  This successor
keeps the same LP and candidate policy, but obtains its lower bound only from
an outward-rounded bounded-variable Lagrangian certificate.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np

from .behavioral_one_seat_master import BehavioralOneSeatAxis
from .linear_program_certificate import (
    certify_bounded_minimization_lower_bound,
)
from .sequence_form_open_axis import SequenceFormAffineRow


@dataclass(frozen=True, slots=True)
class BehavioralMasterSolutionV2:
    variables: tuple[float, ...]
    epigraph: tuple[float, ...]
    lower_bound: float
    certified_dual_lower_bound: float
    raw_primal_objective: float
    raw_dual_objective: float
    raw_primal_minus_dual: float
    dual_lagrangian_constant_lower_bound: float
    dual_residual_correction_lower_bound: float
    dual_nominal_minus_certified: float
    dual_maximum_absolute_residual_upper_bound: float
    dual_maximum_residual_interval_width: float
    inequality_dual_sign_clips: int
    active_cap_players: tuple[int, ...]
    row_counts_by_player: tuple[int, ...]
    equality_rows: int
    inequality_rows: int
    highs_iterations: int
    solve_ms: float
    maximum_equality_error: float
    maximum_inequality_violation: float
    maximum_bound_violation: float
    maximum_policy_bound_violation: float
    maximum_epigraph_bound_violation: float
    maximum_stationarity_error: float
    maximum_complementarity_error: float


@dataclass(frozen=True, slots=True)
class BehavioralMasterVerificationTolerances:
    """Explicit non-scaled allowances for semantically distinct LP checks."""

    probability_equality_absolute: float
    probability_bound_absolute: float
    chip_inequality_absolute: float
    chip_epigraph_bound_absolute: float
    stationarity_absolute: float
    chip_complementarity_absolute: float
    chip_objective_gap_absolute: float
    dual_sign_absolute: float

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or float(value) < 0.0
            ):
                raise ValueError(f"{name} must be finite and nonnegative")


def _finite_vector(values: object, size: int, *, label: str) -> np.ndarray:
    result = np.asarray(values, dtype=np.float64)
    if result.shape != (size,) or not np.all(np.isfinite(result)):
        raise FloatingPointError(f"behavioral master {label} is non-finite or malformed")
    return result


def solve_behavioral_one_seat_master_v2(
    axis: BehavioralOneSeatAxis,
    rows_by_player: tuple[tuple[SequenceFormAffineRow, ...], ...],
    caps: tuple[float, ...],
    *,
    solver_feasibility_tolerance: float,
    verification_tolerances: BehavioralMasterVerificationTolerances,
) -> BehavioralMasterSolutionV2:
    """Solve the V1 LP while certifying its restricted-master lower bound."""

    from scipy.optimize import linprog
    from scipy.sparse import coo_matrix, csr_matrix

    players = len(caps)
    if players == 0 or len(rows_by_player) != players:
        raise ValueError("behavioral master requires one row library per player")
    if any(not rows for rows in rows_by_player):
        raise ValueError("behavioral master row libraries must be nonempty")
    if any(not np.isfinite(cap) or cap < 0.0 for cap in caps):
        raise ValueError("behavioral master caps must be finite and nonnegative")
    if (
        isinstance(solver_feasibility_tolerance, bool)
        or not np.isfinite(solver_feasibility_tolerance)
        or solver_feasibility_tolerance <= 0.0
    ):
        raise ValueError("behavioral master tolerance must be finite and positive")
    if type(verification_tolerances) is not BehavioralMasterVerificationTolerances:
        raise TypeError(
            "behavioral master requires BehavioralMasterVerificationTolerances"
        )

    policy_width = axis.variable_count
    width = policy_width + players
    equality_row_indices = []
    equality_columns = []
    equality_values = []
    for row_index, information_set in enumerate(axis.information_sets):
        for variable in information_set.variable_indices:
            equality_row_indices.append(row_index)
            equality_columns.append(variable)
            equality_values.append(1.0)
    a_eq = coo_matrix(
        (equality_values, (equality_row_indices, equality_columns)),
        shape=(len(axis.information_sets), width),
        dtype=np.float64,
    ).tocsr()
    b_eq = np.ones(len(axis.information_sets), dtype=np.float64)

    inequality_rows = []
    inequality_bounds = []
    for player, rows in enumerate(rows_by_player):
        for gain in rows:
            values = np.zeros(width, dtype=np.float64)
            coefficients = np.asarray(axis.coefficients(gain), dtype=np.float64)
            if coefficients.shape != (policy_width,) or not np.all(
                np.isfinite(coefficients)
            ):
                raise ValueError("behavioral master gain coefficients are invalid")
            constant = float(gain.constant)
            if not np.isfinite(constant):
                raise ValueError("behavioral master gain constant is invalid")
            values[:policy_width] = coefficients
            values[policy_width + player] = -1.0
            inequality_rows.append(values)
            inequality_bounds.append(-constant)
    a_ub = csr_matrix(np.stack(inequality_rows, axis=0))
    b_ub = np.asarray(inequality_bounds, dtype=np.float64)
    objective = np.zeros(width, dtype=np.float64)
    objective[policy_width:] = 1.0
    bounds = [(0.0, 1.0)] * policy_width + [
        (0.0, float(cap)) for cap in caps
    ]

    started = time.perf_counter()
    solved = linprog(
        objective,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs-ds",
        options={
            "dual_feasibility_tolerance": solver_feasibility_tolerance,
            "primal_feasibility_tolerance": solver_feasibility_tolerance,
        },
    )
    solve_ms = (time.perf_counter() - started) * 1000.0
    if not solved.success or solved.status != 0:
        raise ValueError(f"behavioral master did not solve: {solved.message}")

    variables = _finite_vector(solved.x, width, label="primal variables")
    equality_residual = np.asarray(a_eq @ variables - b_eq, dtype=np.float64)
    inequality_residual = np.asarray(a_ub @ variables - b_ub, dtype=np.float64)
    lower = np.asarray([bound[0] for bound in bounds], dtype=np.float64)
    upper = np.asarray([bound[1] for bound in bounds], dtype=np.float64)
    lower_violation = np.maximum(lower - variables, 0.0)
    upper_violation = np.maximum(variables - upper, 0.0)

    inequality_count = a_ub.shape[0]
    equality_count = a_eq.shape[0]
    inequality_dual = _finite_vector(
        solved.ineqlin.marginals,
        inequality_count,
        label="inequality multipliers",
    )
    equality_dual = _finite_vector(
        solved.eqlin.marginals,
        equality_count,
        label="equality multipliers",
    )
    lower_dual = _finite_vector(solved.lower.marginals, width, label="lower multipliers")
    upper_dual = _finite_vector(solved.upper.marginals, width, label="upper multipliers")
    inequality_slack = _finite_vector(
        solved.ineqlin.residual,
        inequality_count,
        label="inequality residuals",
    )
    lower_slack = _finite_vector(solved.lower.residual, width, label="lower residuals")
    upper_slack = _finite_vector(solved.upper.residual, width, label="upper residuals")
    stationarity = (
        objective
        - np.asarray(a_ub.T @ inequality_dual, dtype=np.float64)
        - np.asarray(a_eq.T @ equality_dual, dtype=np.float64)
        - lower_dual
        - upper_dual
    )
    if not np.all(np.isfinite(stationarity)):
        raise FloatingPointError("behavioral master stationarity is non-finite")
    raw_dual_objective = float(
        b_ub @ inequality_dual
        + b_eq @ equality_dual
        + lower @ lower_dual
        + upper @ upper_dual
    )
    raw_primal_objective = float(objective @ variables)
    raw_primal_minus_dual = raw_primal_objective - raw_dual_objective
    if not all(
        np.isfinite(value)
        for value in (
            raw_primal_objective,
            raw_dual_objective,
            raw_primal_minus_dual,
        )
    ):
        raise FloatingPointError("behavioral master objective diagnostics are non-finite")
    complementarity = np.concatenate(
        (
            np.abs(inequality_slack * inequality_dual),
            np.abs(lower_slack * lower_dual),
            np.abs(upper_slack * upper_dual),
        )
    )
    maximum_equality = float(np.max(np.abs(equality_residual), initial=0.0))
    maximum_inequality = float(np.max(inequality_residual, initial=0.0))
    maximum_bound = float(
        max(
            np.max(lower_violation, initial=0.0),
            np.max(upper_violation, initial=0.0),
        )
    )
    maximum_policy_bound = float(
        max(
            np.max(lower_violation[:policy_width], initial=0.0),
            np.max(upper_violation[:policy_width], initial=0.0),
        )
    )
    maximum_epigraph_bound = float(
        max(
            np.max(lower_violation[policy_width:], initial=0.0),
            np.max(upper_violation[policy_width:], initial=0.0),
        )
    )
    maximum_stationarity = float(np.max(np.abs(stationarity), initial=0.0))
    maximum_complementarity = float(np.max(complementarity, initial=0.0))
    checks = verification_tolerances
    if (
        maximum_equality > checks.probability_equality_absolute
        or maximum_policy_bound > checks.probability_bound_absolute
        or maximum_inequality > checks.chip_inequality_absolute
        or maximum_epigraph_bound > checks.chip_epigraph_bound_absolute
        or maximum_stationarity > checks.stationarity_absolute
        or maximum_complementarity > checks.chip_complementarity_absolute
        or np.any(inequality_dual > checks.dual_sign_absolute)
        or np.any(lower_dual < -checks.dual_sign_absolute)
        or np.any(upper_dual > checks.dual_sign_absolute)
        or abs(raw_primal_minus_dual) > checks.chip_objective_gap_absolute
    ):
        raise ArithmeticError("behavioral master primal/dual verification failed")

    certificate = certify_bounded_minimization_lower_bound(
        objective,
        a_ub,
        b_ub,
        inequality_dual,
        equality_coefficients=a_eq,
        equality_bounds=b_eq,
        equality_multipliers=equality_dual,
        variable_lower_bounds=lower,
        variable_upper_bounds=upper,
    )
    epigraph = tuple(float(value) for value in variables[policy_width:])
    active_allowance = checks.chip_epigraph_bound_absolute
    if isinstance(solved.nit, bool) or not isinstance(solved.nit, (int, np.integer)):
        raise FloatingPointError("behavioral master iteration count is malformed")
    if int(solved.nit) < 0:
        raise FloatingPointError("behavioral master iteration count is negative")
    return BehavioralMasterSolutionV2(
        variables=tuple(float(value) for value in variables[:policy_width]),
        epigraph=epigraph,
        lower_bound=max(0.0, certificate.lower_bound),
        certified_dual_lower_bound=certificate.lower_bound,
        raw_primal_objective=raw_primal_objective,
        raw_dual_objective=raw_dual_objective,
        raw_primal_minus_dual=raw_primal_minus_dual,
        dual_lagrangian_constant_lower_bound=(
            certificate.lagrangian_constant_lower_bound
        ),
        dual_residual_correction_lower_bound=(
            certificate.box_residual_correction_lower_bound
        ),
        dual_nominal_minus_certified=certificate.nominal_minus_certified,
        dual_maximum_absolute_residual_upper_bound=(
            certificate.maximum_absolute_residual_upper_bound
        ),
        dual_maximum_residual_interval_width=(
            certificate.maximum_residual_interval_width
        ),
        inequality_dual_sign_clips=(
            certificate.inequality_multiplier_sign_clips
        ),
        active_cap_players=tuple(
            player
            for player, (value, cap) in enumerate(zip(epigraph, caps, strict=True))
            if cap - value <= active_allowance
        ),
        row_counts_by_player=tuple(len(rows) for rows in rows_by_player),
        equality_rows=a_eq.shape[0],
        inequality_rows=a_ub.shape[0],
        highs_iterations=int(solved.nit),
        solve_ms=solve_ms,
        maximum_equality_error=maximum_equality,
        maximum_inequality_violation=max(0.0, maximum_inequality),
        maximum_bound_violation=maximum_bound,
        maximum_policy_bound_violation=maximum_policy_bound,
        maximum_epigraph_bound_violation=maximum_epigraph_bound,
        maximum_stationarity_error=maximum_stationarity,
        maximum_complementarity_error=maximum_complementarity,
    )
