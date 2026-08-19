"""Dependency-free zero-sum matrix-game oracle for small exact controls."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite

from .linear_program import maximize_linear_program


@dataclass(frozen=True, slots=True)
class MatrixGameSolution:
    """Minimax strategies for a row minimizer and column maximizer."""

    row_strategy: tuple[float, ...]
    column_strategy: tuple[float, ...]
    value: float
    verified_lower_value: float
    verified_upper_value: float
    duality_gap: float
    payoff_shift: float
    simplex_pivots: int
    simplex_backend: str


class _PackingSimplexStalled(ValueError):
    """The fast tableau cycled or exceeded its bounded pivot attempt."""


def _pivot(
    tableau: list[list[float]],
    pivot_row: int,
    pivot_column: int,
) -> None:
    pivot_value = tableau[pivot_row][pivot_column]
    tableau[pivot_row] = [value / pivot_value for value in tableau[pivot_row]]
    normalized = tableau[pivot_row]
    for row_index, row in enumerate(tableau):
        if row_index == pivot_row:
            continue
        factor = row[pivot_column]
        if factor == 0.0:
            continue
        tableau[row_index] = [
            value - factor * pivot_entry
            for value, pivot_entry in zip(row, normalized, strict=True)
        ]


def _packing_simplex(
    coefficients: list[list[float]],
    *,
    tolerance: float,
    max_pivots: int,
) -> tuple[tuple[float, ...], tuple[float, ...], float, int]:
    """Maximize sum(x) subject to ``coefficients @ x <= 1``."""

    constraints = len(coefficients)
    variables = len(coefficients[0])
    width = variables + constraints + 1
    tableau: list[list[float]] = []
    basis: list[int] = []
    for constraint, row in enumerate(coefficients):
        tableau.append(
            list(row)
            + [float(index == constraint) for index in range(constraints)]
            + [1.0]
        )
        basis.append(variables + constraint)
    tableau.append([-1.0] * variables + [0.0] * constraints + [0.0])

    pivots = 0
    seen_bases: set[tuple[int, ...]] = set()
    while True:
        signature = tuple(basis)
        if signature in seen_bases:
            raise _PackingSimplexStalled("matrix-game packing simplex cycled")
        seen_bases.add(signature)
        objective = tableau[-1]
        entering = next(
            (
                column
                for column in range(width - 1)
                if objective[column] < -tolerance
            ),
            None,
        )
        if entering is None:
            break
        candidates = [
            (
                tableau[row][-1] / tableau[row][entering],
                basis[row],
                row,
            )
            for row in range(constraints)
            if tableau[row][entering] > tolerance
        ]
        if not candidates:
            raise ValueError("matrix-game packing program is unbounded")
        _, _, leaving = min(candidates)
        _pivot(tableau, leaving, entering)
        basis[leaving] = entering
        pivots += 1
        if pivots > max_pivots:
            raise _PackingSimplexStalled(
                "matrix-game packing simplex exceeded its fast pivot budget"
            )

    packing = [0.0] * variables
    for row, basic_variable in enumerate(basis):
        if basic_variable < variables:
            packing[basic_variable] = tableau[row][-1]
    dual = [tableau[-1][variables + index] for index in range(constraints)]
    packing = [0.0 if abs(value) <= tolerance else value for value in packing]
    dual = [0.0 if abs(value) <= tolerance else value for value in dual]
    if any(value < -tolerance for value in packing + dual):
        raise AssertionError("simplex returned a negative primal or dual variable")
    objective_value = tableau[-1][-1]
    return tuple(packing), tuple(dual), objective_value, pivots


def solve_zero_sum_matrix_game(
    payoffs: Sequence[Sequence[float]],
    *,
    tolerance: float = 1e-11,
    max_pivots: int = 100_000,
) -> MatrixGameSolution:
    """Solve a finite zero-sum game by a shifted packing LP.

    ``payoffs[row][column]`` is paid to the column maximizer. The row player
    minimizes. A positive shift turns the game into the standard pair
    ``max 1^T y: B^T y <= 1`` and ``min 1^T z: B z >= 1``. The primal simplex
    solves the packing problem; final slack reduced costs recover its covering
    dual, which is the column strategy after normalization.
    """

    if not isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")
    if max_pivots <= 0:
        raise ValueError("max_pivots must be positive")
    rows = [tuple(float(value) for value in row) for row in payoffs]
    if not rows or not rows[0]:
        raise ValueError("payoff matrix cannot be empty")
    columns = len(rows[0])
    if any(len(row) != columns for row in rows):
        raise ValueError("payoff matrix must be rectangular")
    if any(not isfinite(value) for row in rows for value in row):
        raise ValueError("payoff matrix entries must be finite")

    minimum = min(value for row in rows for value in row)
    shift = 1.0 - minimum
    shifted = [[value + shift for value in row] for row in rows]
    packing_coefficients = [
        [shifted[row][column] for row in range(len(rows))]
        for column in range(columns)
    ]
    fast_pivot_budget = min(
        max_pivots,
        max(1_000, 2 * (len(rows) + columns)),
    )
    try:
        row_weights, column_weights, objective, pivots = _packing_simplex(
            packing_coefficients,
            tolerance=tolerance,
            max_pivots=fast_pivot_budget,
        )
        simplex_backend = "packing"
    except _PackingSimplexStalled:
        packing = maximize_linear_program(
            (1.0,) * len(rows),
            packing_coefficients,
            (1.0,) * columns,
            tolerance=tolerance,
            max_pivots=max_pivots,
        )
        row_weights = packing.variables
        column_weights = packing.dual_variables
        objective = packing.objective
        pivots = packing.pivots
        simplex_backend = "two_phase_fallback"
    row_mass = sum(row_weights)
    column_mass = sum(column_weights)
    if row_mass <= tolerance or column_mass <= tolerance or objective <= tolerance:
        raise AssertionError("matrix-game simplex returned zero strategy mass")
    if abs(row_mass - column_mass) > 100.0 * tolerance * max(1.0, objective):
        raise AssertionError("matrix-game primal and dual objectives disagree")

    row_strategy = tuple(weight / row_mass for weight in row_weights)
    column_strategy = tuple(weight / column_mass for weight in column_weights)
    lower = min(
        sum(row[column] * column_strategy[column] for column in range(columns))
        for row in rows
    )
    upper = max(
        sum(
            row_strategy[row_index] * rows[row_index][column]
            for row_index in range(len(rows))
        )
        for column in range(columns)
    )
    gap = upper - lower
    allowed_gap = 500.0 * tolerance * max(
        1.0,
        max(abs(value) for row in rows for value in row),
    )
    if gap < -allowed_gap or gap > allowed_gap:
        raise AssertionError(
            f"matrix-game verification gap {gap} exceeds {allowed_gap}"
        )
    value = 1.0 / ((row_mass + column_mass) / 2.0) - shift
    if not lower - allowed_gap <= value <= upper + allowed_gap:
        raise AssertionError("matrix-game LP value lies outside verified bounds")
    return MatrixGameSolution(
        row_strategy=row_strategy,
        column_strategy=column_strategy,
        value=value,
        verified_lower_value=lower,
        verified_upper_value=upper,
        duality_gap=max(0.0, gap),
        payoff_shift=shift,
        simplex_pivots=pivots,
        simplex_backend=simplex_backend,
    )
