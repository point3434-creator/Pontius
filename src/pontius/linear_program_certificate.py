"""Outward-rounded certificates for bounded linear-program objectives.

The solver multipliers supplied here are hints, not trusted certificates.  A
wrong-sign inequality multiplier is projected onto its valid sign cone, and
any remaining stationarity residual is minimized over the caller's proven
variable box.  The resulting scalar is therefore a lower bound even when a
Float64 solver's reported dual point is only approximately feasible.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from math import fsum, inf, isfinite, nextafter
from typing import Any


@dataclass(frozen=True, slots=True)
class BoundedMinimizationCertificate:
    """Diagnostics for a bounded-minimization Lagrangian lower bound."""

    lower_bound: float
    nominal_lagrangian_value: float
    lagrangian_constant_lower_bound: float
    box_residual_correction_lower_bound: float
    nominal_minus_certified: float
    maximum_absolute_residual_upper_bound: float
    maximum_residual_interval_width: float
    inequality_multiplier_sign_clips: int


def _product_interval(left: float, right: float) -> tuple[float, float]:
    if left == 0.0 or right == 0.0:
        return 0.0, 0.0
    product = left * right
    if not isfinite(product):
        raise FloatingPointError("certificate arithmetic overflowed")
    return nextafter(product, -inf), nextafter(product, inf)


def _add_lower(left: float, right: float) -> float:
    if left == 0.0:
        return right
    if right == 0.0:
        return left
    value = left + right
    if not isfinite(value):
        raise FloatingPointError("certificate arithmetic overflowed")
    return nextafter(value, -inf)


def _add_upper(left: float, right: float) -> float:
    if left == 0.0:
        return right
    if right == 0.0:
        return left
    value = left + right
    if not isfinite(value):
        raise FloatingPointError("certificate arithmetic overflowed")
    return nextafter(value, inf)


def _matrix_rows(
    matrix: Any,
    row_count: int,
    width: int,
) -> Iterator[Iterator[tuple[int, float]]]:
    shape = getattr(matrix, "shape", None)
    if shape is not None and tuple(shape) != (row_count, width):
        raise ValueError("certificate matrix has the wrong shape")
    if shape is None and len(matrix) != row_count:
        raise ValueError("certificate matrix has the wrong row count")

    if all(hasattr(matrix, field) for field in ("indptr", "indices", "data")):
        if getattr(matrix, "format", "csr") != "csr":
            matrix = matrix.tocsr()
        for row_index in range(row_count):
            start = int(matrix.indptr[row_index])
            stop = int(matrix.indptr[row_index + 1])
            yield (
                (int(matrix.indices[position]), float(matrix.data[position]))
                for position in range(start, stop)
            )
        return

    for row_index in range(row_count):
        row = matrix[row_index]
        if len(row) != width:
            raise ValueError("certificate matrix has the wrong width")
        yield (
            (column, float(value))
            for column, value in enumerate(row)
            if float(value) != 0.0
        )


def _certify_with_signed_multipliers(
    objective: Sequence[float],
    inequality_coefficients: Any,
    inequality_bounds: Sequence[float],
    inequality_multipliers: Sequence[float],
    equality_coefficients: Any,
    equality_bounds: Sequence[float],
    equality_multipliers: Sequence[float],
    variable_lower_bounds: Sequence[float],
    variable_upper_bounds: Sequence[float],
    *,
    inequality_multiplier_sign_clips: int,
) -> BoundedMinimizationCertificate:
    c = tuple(float(value) for value in objective)
    lower = tuple(float(value) for value in variable_lower_bounds)
    upper = tuple(float(value) for value in variable_upper_bounds)
    if not c:
        raise ValueError("certificate requires at least one variable")
    if len(lower) != len(c) or len(upper) != len(c):
        raise ValueError("certificate variable-bound width differs from objective")
    if any(not isfinite(value) for value in c + lower + upper):
        raise ValueError("certificate values must be finite")
    if any(left > right for left, right in zip(lower, upper, strict=True)):
        raise ValueError("certificate variable bounds are reversed")

    inequality_rhs = tuple(float(value) for value in inequality_bounds)
    inequality_dual = tuple(float(value) for value in inequality_multipliers)
    equality_rhs = tuple(float(value) for value in equality_bounds)
    equality_dual = tuple(float(value) for value in equality_multipliers)
    if len(inequality_rhs) != len(inequality_dual):
        raise ValueError("certificate inequality multiplier count differs from rows")
    if len(equality_rhs) != len(equality_dual):
        raise ValueError("certificate equality multiplier count differs from rows")
    if any(
        not isfinite(value)
        for value in inequality_rhs
        + inequality_dual
        + equality_rhs
        + equality_dual
    ):
        raise ValueError("certificate values must be finite")

    residual_lower = list(c)
    residual_upper = list(c)
    nominal_residual_terms = [[value] for value in c]
    constant_lower = 0.0
    nominal_constant_terms: list[float] = []

    def apply_rows(
        matrix: Any,
        rhs: tuple[float, ...],
        multipliers: tuple[float, ...],
    ) -> None:
        nonlocal constant_lower
        for row_index, entries in enumerate(_matrix_rows(matrix, len(rhs), len(c))):
            multiplier = multipliers[row_index]
            product_lower, _ = _product_interval(
                rhs[row_index], multiplier
            )
            constant_lower = _add_lower(constant_lower, product_lower)
            nominal_product = rhs[row_index] * multiplier
            if not isfinite(nominal_product):
                raise FloatingPointError("certificate arithmetic overflowed")
            nominal_constant_terms.append(nominal_product)
            for column, coefficient in entries:
                if column not in range(len(c)):
                    raise ValueError("certificate matrix column is outside objective")
                if not isfinite(coefficient):
                    raise ValueError("certificate values must be finite")
                term_lower, term_upper = _product_interval(-coefficient, multiplier)
                residual_lower[column] = _add_lower(
                    residual_lower[column], term_lower
                )
                residual_upper[column] = _add_upper(
                    residual_upper[column], term_upper
                )
                nominal_term = -coefficient * multiplier
                if not isfinite(nominal_term):
                    raise FloatingPointError("certificate arithmetic overflowed")
                nominal_residual_terms[column].append(nominal_term)

    apply_rows(
        inequality_coefficients,
        inequality_rhs,
        inequality_dual,
    )
    apply_rows(
        equality_coefficients,
        equality_rhs,
        equality_dual,
    )

    nominal_residual = tuple(fsum(terms) for terms in nominal_residual_terms)
    correction_lower = 0.0
    nominal_correction_terms = []
    maximum_absolute_residual = 0.0
    maximum_residual_width = 0.0
    for residual_left, residual_right, nominal, bound_left, bound_right in zip(
        residual_lower,
        residual_upper,
        nominal_residual,
        lower,
        upper,
        strict=True,
    ):
        corner_lowers = []
        for bound in (bound_left, bound_right):
            for residual in (residual_left, residual_right):
                corner_lowers.append(_product_interval(bound, residual)[0])
        contribution = min(corner_lowers)
        correction_lower = _add_lower(correction_lower, contribution)
        nominal_contribution = min(bound_left * nominal, bound_right * nominal)
        if not isfinite(nominal_contribution):
            raise FloatingPointError("certificate arithmetic overflowed")
        nominal_correction_terms.append(nominal_contribution)
        maximum_absolute_residual = max(
            maximum_absolute_residual,
            abs(residual_left),
            abs(residual_right),
        )
        width = residual_right - residual_left
        if not isfinite(width):
            raise FloatingPointError("certificate arithmetic overflowed")
        maximum_residual_width = max(maximum_residual_width, width)

    nominal_constant = fsum(nominal_constant_terms)
    nominal_correction = fsum(nominal_correction_terms)
    nominal_lagrangian = fsum((nominal_constant, nominal_correction))
    lower_bound = _add_lower(constant_lower, correction_lower)
    if not isfinite(nominal_lagrangian) or not isfinite(lower_bound):
        raise FloatingPointError("certificate arithmetic overflowed")
    return BoundedMinimizationCertificate(
        lower_bound=lower_bound,
        nominal_lagrangian_value=nominal_lagrangian,
        lagrangian_constant_lower_bound=constant_lower,
        box_residual_correction_lower_bound=correction_lower,
        nominal_minus_certified=nominal_lagrangian - lower_bound,
        maximum_absolute_residual_upper_bound=maximum_absolute_residual,
        maximum_residual_interval_width=maximum_residual_width,
        inequality_multiplier_sign_clips=inequality_multiplier_sign_clips,
    )


def certify_bounded_minimization_lower_bound(
    objective: Sequence[float],
    inequality_coefficients: Any,
    inequality_bounds: Sequence[float],
    inequality_multipliers: Sequence[float],
    *,
    equality_coefficients: Any = (),
    equality_bounds: Sequence[float] = (),
    equality_multipliers: Sequence[float] = (),
    variable_lower_bounds: Sequence[float],
    variable_upper_bounds: Sequence[float],
) -> BoundedMinimizationCertificate:
    """Certify a lower bound for ``min c@x`` with ``A@x<=b, E@x=d``.

    Inequality multipliers follow SciPy's minimization convention and must be
    nonpositive.  Positive entries are clipped to zero before certification.
    Equality multipliers are unrestricted.
    """

    raw = tuple(float(value) for value in inequality_multipliers)
    if any(not isfinite(value) for value in raw):
        raise ValueError("certificate values must be finite")
    signed = tuple(min(value, 0.0) for value in raw)
    return _certify_with_signed_multipliers(
        objective,
        inequality_coefficients,
        inequality_bounds,
        signed,
        equality_coefficients,
        equality_bounds,
        equality_multipliers,
        variable_lower_bounds,
        variable_upper_bounds,
        inequality_multiplier_sign_clips=sum(value > 0.0 for value in raw),
    )


def certify_negated_bounded_maximization_lower_bound(
    objective: Sequence[float],
    coefficients: Any,
    bounds: Sequence[float],
    dual_multipliers: Sequence[float],
    *,
    variable_lower_bounds: Sequence[float],
    variable_upper_bounds: Sequence[float],
) -> BoundedMinimizationCertificate:
    """Certify a lower bound for the negation of ``max c@x, A@x<=b``.

    The in-house simplex uses nonnegative dual multipliers.  Negative entries
    are clipped to zero, then the problem is mapped to bounded minimization.
    """

    raw = tuple(float(value) for value in dual_multipliers)
    if any(not isfinite(value) for value in raw):
        raise ValueError("certificate values must be finite")
    nonnegative = tuple(max(value, 0.0) for value in raw)
    return _certify_with_signed_multipliers(
        tuple(-float(value) for value in objective),
        coefficients,
        bounds,
        tuple(-value for value in nonnegative),
        (),
        (),
        (),
        variable_lower_bounds,
        variable_upper_bounds,
        inequality_multiplier_sign_clips=sum(value < 0.0 for value in raw),
    )
