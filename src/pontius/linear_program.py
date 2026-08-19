"""Small dependency-free two-phase simplex for exact-lab oracles."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class LinearProgramSolution:
    variables: tuple[float, ...]
    objective: float
    pivots: int
    max_constraint_violation: float


class _SimplexTableau:
    def __init__(
        self,
        coefficients: list[list[float]],
        bounds: list[float],
        objective: list[float],
        tolerance: float,
        max_pivots: int,
    ) -> None:
        self.constraints = len(bounds)
        self.variables = len(objective)
        self.tolerance = tolerance
        self.max_pivots = max_pivots
        self.pivots = 0
        m = self.constraints
        n = self.variables
        self.basic = [n + index for index in range(m)]
        self.nonbasic = list(range(n)) + [-1]
        self.tableau = [[0.0] * (n + 2) for _ in range(m + 2)]
        for row in range(m):
            for column in range(n):
                self.tableau[row][column] = coefficients[row][column]
            self.tableau[row][n] = -1.0
            self.tableau[row][n + 1] = bounds[row]
        for column in range(n):
            self.tableau[m][column] = -objective[column]
        self.tableau[m + 1][n] = 1.0

    def pivot(self, row: int, column: int) -> None:
        table = self.tableau
        inverse = 1.0 / table[row][column]
        for other_row in range(self.constraints + 2):
            if other_row == row:
                continue
            for other_column in range(self.variables + 2):
                if other_column == column:
                    continue
                table[other_row][other_column] -= (
                    table[row][other_column]
                    * table[other_row][column]
                    * inverse
                )
        for other_column in range(self.variables + 2):
            if other_column != column:
                table[row][other_column] *= inverse
        for other_row in range(self.constraints + 2):
            if other_row != row:
                table[other_row][column] *= -inverse
        table[row][column] = inverse
        self.basic[row], self.nonbasic[column] = (
            self.nonbasic[column],
            self.basic[row],
        )
        self.pivots += 1
        if self.pivots > self.max_pivots:
            raise ValueError("linear-program simplex exceeded max_pivots")

    def simplex(self, phase: int) -> bool:
        objective_row = self.constraints + 1 if phase == 1 else self.constraints
        while True:
            entering: int | None = None
            for column in range(self.variables + 1):
                if phase == 2 and self.nonbasic[column] == -1:
                    continue
                if entering is None or (
                    self.tableau[objective_row][column]
                    < self.tableau[objective_row][entering] - self.tolerance
                    or (
                        abs(
                            self.tableau[objective_row][column]
                            - self.tableau[objective_row][entering]
                        )
                        <= self.tolerance
                        and self.nonbasic[column] < self.nonbasic[entering]
                    )
                ):
                    entering = column
            assert entering is not None
            if self.tableau[objective_row][entering] >= -self.tolerance:
                return True

            leaving: int | None = None
            for row in range(self.constraints):
                coefficient = self.tableau[row][entering]
                if coefficient <= self.tolerance:
                    continue
                if leaving is None:
                    leaving = row
                    continue
                ratio = self.tableau[row][self.variables + 1] / coefficient
                prior_ratio = (
                    self.tableau[leaving][self.variables + 1]
                    / self.tableau[leaving][entering]
                )
                if ratio < prior_ratio - self.tolerance or (
                    abs(ratio - prior_ratio) <= self.tolerance
                    and self.basic[row] < self.basic[leaving]
                ):
                    leaving = row
            if leaving is None:
                return False
            self.pivot(leaving, entering)

    def solve(self) -> tuple[tuple[float, ...], float, int]:
        if self.constraints:
            row = min(
                range(self.constraints),
                key=lambda index: self.tableau[index][self.variables + 1],
            )
            if self.tableau[row][self.variables + 1] < -self.tolerance:
                self.pivot(row, self.variables)
                if (
                    not self.simplex(1)
                    or self.tableau[self.constraints + 1][self.variables + 1]
                    < -self.tolerance
                ):
                    raise ValueError("linear program is infeasible")
                if abs(
                    self.tableau[self.constraints + 1][self.variables + 1]
                ) > self.tolerance:
                    raise ValueError("linear program is infeasible")
                for basic_row, variable in enumerate(self.basic):
                    if variable != -1:
                        continue
                    entering = min(
                        range(self.variables + 1),
                        key=lambda column: (
                            abs(self.tableau[basic_row][column])
                            <= self.tolerance,
                            self.nonbasic[column],
                        ),
                    )
                    if abs(self.tableau[basic_row][entering]) > self.tolerance:
                        self.pivot(basic_row, entering)
                    break

        if not self.simplex(2):
            raise ValueError("linear program is unbounded")
        values = [0.0] * self.variables
        for row, variable in enumerate(self.basic):
            if variable < self.variables:
                values[variable] = self.tableau[row][self.variables + 1]
        return (
            tuple(values),
            self.tableau[self.constraints][self.variables + 1],
            self.pivots,
        )


def maximize_linear_program(
    objective: Sequence[float],
    coefficients: Sequence[Sequence[float]],
    bounds: Sequence[float],
    *,
    tolerance: float = 1e-10,
    max_pivots: int = 100_000,
) -> LinearProgramSolution:
    """Maximize ``objective @ x`` subject to ``A @ x <= b`` and ``x >= 0``."""

    c = [float(value) for value in objective]
    matrix = [[float(value) for value in row] for row in coefficients]
    rhs = [float(value) for value in bounds]
    if not c:
        raise ValueError("linear program requires at least one variable")
    if len(matrix) != len(rhs):
        raise ValueError("constraint row and bound counts differ")
    if any(len(row) != len(c) for row in matrix):
        raise ValueError("constraint matrix width does not match objective")
    if any(not isfinite(value) for value in c + rhs):
        raise ValueError("linear program values must be finite")
    if any(not isfinite(value) for row in matrix for value in row):
        raise ValueError("linear program values must be finite")
    if not isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")
    if max_pivots <= 0:
        raise ValueError("max_pivots must be positive")

    tableau = _SimplexTableau(
        matrix,
        rhs,
        c,
        tolerance,
        max_pivots,
    )
    variables, objective_value, pivots = tableau.solve()
    violations = [
        sum(coefficient * value for coefficient, value in zip(row, variables))
        - bound
        for row, bound in zip(matrix, rhs, strict=True)
    ]
    max_violation = max(violations, default=0.0)
    allowed = 100.0 * tolerance * max(
        1.0,
        max((abs(value) for value in rhs), default=0.0),
    )
    if max_violation > allowed or any(value < -allowed for value in variables):
        raise AssertionError("linear-program solution fails primal verification")
    verified_objective = sum(
        coefficient * value for coefficient, value in zip(c, variables, strict=True)
    )
    if abs(verified_objective - objective_value) > allowed:
        raise AssertionError("linear-program objective verification failed")
    return LinearProgramSolution(
        variables=tuple(0.0 if abs(value) <= tolerance else value for value in variables),
        objective=objective_value,
        pivots=pivots,
        max_constraint_violation=max(0.0, max_violation),
    )
