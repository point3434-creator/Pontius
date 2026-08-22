"""Sparse Float64 master LP for path-single-visit one-seat gain rows."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Mapping, Sequence

import numpy as np

from .one_seat_convex_generation import require_compiled_behavioral_affine_shortcut
from .public_policy_tt import _information_key
from .sequence_form_open_axis import SequenceFormAffineRow


@dataclass(frozen=True, slots=True)
class BehavioralInformationSet:
    node_index: int
    hand_index: int
    key: str
    actions: tuple[Any, ...]
    variable_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class BehavioralOneSeatAxis:
    acting_player: int
    information_sets: tuple[BehavioralInformationSet, ...]
    acting_nodes: tuple[int, ...]
    variable_count: int

    @classmethod
    def compile(
        cls,
        layout: Any,
        hands_by_player: tuple[tuple[Any, ...], ...],
        blueprint: Mapping[str, Mapping[Any, float]],
        *,
        acting_player: int,
    ) -> "BehavioralOneSeatAxis":
        require_compiled_behavioral_affine_shortcut(layout)
        if (
            isinstance(acting_player, bool)
            or acting_player not in range(layout.num_players)
        ):
            raise ValueError("behavioral master acting player is outside the layout")
        if len(hands_by_player) != layout.num_players:
            raise ValueError("behavioral master requires one external hand axis per seat")
        rows = []
        nodes = []
        cursor = 0
        for node_index, node in enumerate(layout.nodes):
            if node.player != acting_player:
                continue
            nodes.append(node_index)
            actions = tuple(node.actions)
            for hand_index, hand in enumerate(hands_by_player[acting_player]):
                key = _information_key(layout, acting_player, hand, node.history)
                if key not in blueprint or set(blueprint[key]) != set(actions):
                    raise ValueError("behavioral master blueprint axis is incomplete")
                indices = tuple(range(cursor, cursor + len(actions)))
                cursor += len(actions)
                rows.append(
                    BehavioralInformationSet(
                        node_index=node_index,
                        hand_index=hand_index,
                        key=key,
                        actions=actions,
                        variable_indices=indices,
                    )
                )
        if not rows:
            raise ValueError("behavioral master acting seat has no information sets")
        if len({row.key for row in rows}) != len(rows):
            raise ValueError("behavioral master external information keys are not unique")
        return cls(
            acting_player=acting_player,
            information_sets=tuple(rows),
            acting_nodes=tuple(nodes),
            variable_count=cursor,
        )

    def coefficients(self, row: SequenceFormAffineRow) -> np.ndarray:
        """Flatten one exact affine row into this behavioral coordinate order."""

        if row.acting_player != self.acting_player:
            raise ValueError("behavioral master row belongs to another acting player")
        by_node = {node.node_index: node.values for node in row.nodes}
        if tuple(sorted(by_node)) != self.acting_nodes:
            raise ValueError("behavioral master row does not cover the exact acting axis")
        result = np.empty(self.variable_count, dtype=np.float64)
        hands_by_node = {
            node_index: sum(
                information_set.node_index == node_index
                for information_set in self.information_sets
            )
            for node_index in self.acting_nodes
        }
        for information_set in self.information_sets:
            values = by_node[information_set.node_index]
            expected = (
                hands_by_node[information_set.node_index],
                len(information_set.actions),
            )
            if values.shape != expected:
                raise ValueError("behavioral master row has the wrong action shape")
            for action_index, variable in enumerate(
                information_set.variable_indices
            ):
                result[variable] = values[information_set.hand_index, action_index]
        if not np.all(np.isfinite(result)):
            raise FloatingPointError("behavioral master row coefficient is invalid")
        return result

    def policy_from_variables(
        self,
        variables: Sequence[float],
        blueprint: Mapping[str, Mapping[Any, float]],
        *,
        tolerance: float,
    ) -> tuple[dict[str, dict[Any, float]], float]:
        """Project sub-tolerance HiGHS noise back onto exact behavioral simplices."""

        values = np.asarray(variables, dtype=np.float64)
        if values.shape != (self.variable_count,) or not np.all(np.isfinite(values)):
            raise ValueError("behavioral master solution has the wrong variable axis")
        if tolerance <= 0.0 or not np.isfinite(tolerance):
            raise ValueError("behavioral master projection tolerance must be positive")
        result = {key: dict(row) for key, row in blueprint.items()}
        maximum_error = 0.0
        for information_set in self.information_sets:
            raw = values[list(information_set.variable_indices)]
            clipped = np.clip(raw, 0.0, 1.0)
            mass = float(np.sum(clipped))
            if mass <= tolerance:
                raise ArithmeticError("behavioral master solution loses simplex mass")
            projected = clipped / mass
            maximum_error = max(
                maximum_error,
                float(np.max(np.abs(projected - raw))),
            )
            result[information_set.key] = {
                action: float(projected[action_index])
                for action_index, action in enumerate(information_set.actions)
            }
        if maximum_error > tolerance:
            raise ArithmeticError(
                "behavioral master projection exceeds its frozen tolerance"
            )
        return result, maximum_error


@dataclass(frozen=True, slots=True)
class BehavioralMasterSolution:
    variables: tuple[float, ...]
    epigraph: tuple[float, ...]
    lower_bound: float
    active_cap_players: tuple[int, ...]
    row_counts_by_player: tuple[int, ...]
    equality_rows: int
    inequality_rows: int
    highs_iterations: int
    solve_ms: float
    maximum_equality_error: float
    maximum_inequality_violation: float
    maximum_bound_violation: float
    maximum_stationarity_error: float
    maximum_complementarity_error: float
    dual_objective: float
    duality_gap: float


def solve_behavioral_one_seat_master(
    axis: BehavioralOneSeatAxis,
    rows_by_player: tuple[tuple[SequenceFormAffineRow, ...], ...],
    caps: tuple[float, ...],
    *,
    tolerance: float,
) -> BehavioralMasterSolution:
    """Minimize the restricted gain epigraph and verify primal/dual KKT data."""

    from scipy.optimize import linprog
    from scipy.sparse import coo_matrix, csr_matrix

    players = len(caps)
    if players == 0 or len(rows_by_player) != players:
        raise ValueError("behavioral master requires one row library per player")
    if any(not rows for rows in rows_by_player):
        raise ValueError("behavioral master row libraries must be nonempty")
    if any(not np.isfinite(cap) or cap < 0.0 for cap in caps):
        raise ValueError("behavioral master caps must be finite and nonnegative")
    if not np.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("behavioral master tolerance must be finite and positive")

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
            values[:policy_width] = axis.coefficients(gain)
            values[policy_width + player] = -1.0
            inequality_rows.append(values)
            inequality_bounds.append(-float(gain.constant))
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
            "dual_feasibility_tolerance": tolerance,
            "primal_feasibility_tolerance": tolerance,
        },
    )
    solve_ms = (time.perf_counter() - started) * 1000.0
    if not solved.success or solved.status != 0:
        raise ValueError(f"behavioral master did not solve: {solved.message}")

    variables = np.asarray(solved.x, dtype=np.float64)
    equality_residual = np.asarray(a_eq @ variables - b_eq, dtype=np.float64)
    inequality_residual = np.asarray(a_ub @ variables - b_ub, dtype=np.float64)
    lower = np.asarray([bound[0] for bound in bounds], dtype=np.float64)
    upper = np.asarray([bound[1] for bound in bounds], dtype=np.float64)
    lower_violation = np.maximum(lower - variables, 0.0)
    upper_violation = np.maximum(variables - upper, 0.0)

    inequality_dual = np.asarray(solved.ineqlin.marginals, dtype=np.float64)
    equality_dual = np.asarray(solved.eqlin.marginals, dtype=np.float64)
    lower_dual = np.asarray(solved.lower.marginals, dtype=np.float64)
    upper_dual = np.asarray(solved.upper.marginals, dtype=np.float64)
    stationarity = (
        objective
        - np.asarray(a_ub.T @ inequality_dual, dtype=np.float64)
        - np.asarray(a_eq.T @ equality_dual, dtype=np.float64)
        - lower_dual
        - upper_dual
    )
    dual_objective = float(
        b_ub @ inequality_dual
        + b_eq @ equality_dual
        + lower @ lower_dual
        + upper @ upper_dual
    )
    primal_objective = float(objective @ variables)
    complementarity = np.concatenate(
        (
            np.abs(np.asarray(solved.ineqlin.residual) * inequality_dual),
            np.abs(np.asarray(solved.lower.residual) * lower_dual),
            np.abs(np.asarray(solved.upper.residual) * upper_dual),
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
    maximum_stationarity = float(np.max(np.abs(stationarity), initial=0.0))
    maximum_complementarity = float(np.max(complementarity, initial=0.0))
    duality_gap = primal_objective - dual_objective
    scale = max(1.0, abs(primal_objective), abs(dual_objective), max(caps))
    allowance = 100.0 * tolerance * scale
    if (
        maximum_equality > allowance
        or maximum_inequality > allowance
        or maximum_bound > allowance
        or maximum_stationarity > allowance
        or maximum_complementarity > allowance
        or np.any(inequality_dual > allowance)
        or np.any(lower_dual < -allowance)
        or np.any(upper_dual > allowance)
        or abs(duality_gap) > allowance
    ):
        raise ArithmeticError("behavioral master primal/dual verification failed")

    epigraph = tuple(float(value) for value in variables[policy_width:])
    active_allowance = 100.0 * tolerance * max(1.0, max(caps))
    return BehavioralMasterSolution(
        variables=tuple(float(value) for value in variables[:policy_width]),
        epigraph=epigraph,
        lower_bound=max(0.0, primal_objective),
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
        maximum_stationarity_error=maximum_stationarity,
        maximum_complementarity_error=maximum_complementarity,
        dual_objective=dual_objective,
        duality_gap=max(0.0, duality_gap),
    )
