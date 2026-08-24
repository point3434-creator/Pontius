"""Read-only instrumentation for one-seat response-row generation.

The production generator is source-sealed by earlier evidence, so this module
does not add callbacks to it.  Instead, one single-threaded laboratory call is
observed at its existing module boundaries.  The returned transcript is an
audit witness; it is not a second solver and it must never sit on an action
path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from unittest.mock import patch

from .evaluation import EvaluationResult, Policy
from .game import ExtensiveFormGame
from .linear_program import LinearProgramSolution
from . import one_seat_convex_generation as _generation
from .one_seat_convex_generation import (
    AffinePayoff,
    OneSeatGenerationResult,
    ResponseSignature,
)


_AUDIT_LOCK = Lock()


def _copy_policy(policy: Policy) -> Policy:
    return {key: dict(row) for key, row in policy.items()}


@dataclass(frozen=True, slots=True)
class AuditedEvaluation:
    ordinal: int
    policy: Policy = field(compare=False, repr=False)
    evaluation: EvaluationResult
    response_signatures: tuple[ResponseSignature, ...]


@dataclass(frozen=True, slots=True)
class AuditedMaster:
    iteration: int
    solution: LinearProgramSolution
    realization: tuple[float, ...]
    epigraph: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class AuditedResponseRow:
    ordinal: int
    phase: str
    after_iteration: int | None
    target_player: int
    signature: ResponseSignature
    gain: AffinePayoff


@dataclass(frozen=True, slots=True)
class OneSeatRowGrowthAudit:
    result: OneSeatGenerationResult = field(compare=False, repr=False)
    evaluations: tuple[AuditedEvaluation, ...]
    masters: tuple[AuditedMaster, ...]
    response_rows: tuple[AuditedResponseRow, ...]
    best_response_calls: int
    expected_utilities_calls: int
    open_axis_coefficient_calls: int


def audit_one_seat_row_growth(
    game: ExtensiveFormGame,
    blueprint: Policy,
    *,
    acting_player: int,
    guard: float,
    max_iterations: int = 100,
    tolerance: float = 1e-10,
) -> OneSeatRowGrowthAudit:
    """Run the production generator once and retain its internal transcript.

    Patching is deliberately confined by a process-local lock.  The wrapped
    functions call the original production objects, so the returned policy and
    bounds are those of ``solve_one_seat_with_row_generation`` itself.
    """

    evaluations: list[AuditedEvaluation] = []
    masters: list[AuditedMaster] = []
    response_rows: list[AuditedResponseRow] = []
    counters = {
        "best_response": 0,
        "expected_utilities": 0,
        "open_axis": 0,
    }

    original_best_response = _generation.best_response
    original_expected_utilities = _generation.expected_utilities
    original_open_axis = _generation.open_axis_payoff_coefficients
    original_evaluate = _generation._evaluate_with_response_tapes
    original_master = _generation._master
    original_response_row = _generation._response_row

    def counted_best_response(*args: object, **kwargs: object) -> object:
        counters["best_response"] += 1
        return original_best_response(*args, **kwargs)

    def counted_expected_utilities(*args: object, **kwargs: object) -> object:
        counters["expected_utilities"] += 1
        return original_expected_utilities(*args, **kwargs)

    def counted_open_axis(*args: object, **kwargs: object) -> object:
        counters["open_axis"] += 1
        return original_open_axis(*args, **kwargs)

    def observed_evaluate(
        observed_game: ExtensiveFormGame,
        policy: Policy,
    ) -> tuple[EvaluationResult, tuple[ResponseSignature, ...]]:
        evaluation, signatures = original_evaluate(observed_game, policy)
        evaluations.append(
            AuditedEvaluation(
                ordinal=len(evaluations),
                policy=_copy_policy(policy),
                evaluation=evaluation,
                response_signatures=signatures,
            )
        )
        return evaluation, signatures

    def observed_master(*args: object, **kwargs: object) -> object:
        solution, realization, epigraph = original_master(*args, **kwargs)
        masters.append(
            AuditedMaster(
                iteration=len(masters) + 1,
                solution=solution,
                realization=realization,
                epigraph=epigraph,
            )
        )
        return solution, realization, epigraph

    def observed_response_row(*args: object, **kwargs: object) -> object:
        row = original_response_row(*args, **kwargs)
        initial = not masters
        response_rows.append(
            AuditedResponseRow(
                ordinal=len(response_rows),
                phase="initial" if initial else "generated",
                after_iteration=None if initial else len(masters),
                target_player=row.target_player,
                signature=row.signature,
                gain=row.gain,
            )
        )
        return row

    with _AUDIT_LOCK:
        with (
            patch.object(_generation, "best_response", counted_best_response),
            patch.object(
                _generation,
                "expected_utilities",
                counted_expected_utilities,
            ),
            patch.object(
                _generation,
                "open_axis_payoff_coefficients",
                counted_open_axis,
            ),
            patch.object(
                _generation,
                "_evaluate_with_response_tapes",
                observed_evaluate,
            ),
            patch.object(_generation, "_master", observed_master),
            patch.object(
                _generation,
                "_response_row",
                observed_response_row,
            ),
        ):
            result = _generation.solve_one_seat_with_row_generation(
                game,
                blueprint,
                acting_player=acting_player,
                guard=guard,
                max_iterations=max_iterations,
                tolerance=tolerance,
            )

    if len(evaluations) != len(result.iterations) + 1:
        raise AssertionError("row-growth audit evaluation count drifted")
    if len(masters) != len(result.iterations):
        raise AssertionError("row-growth audit master count drifted")
    if len(response_rows) != sum(result.response_rows_by_player):
        raise AssertionError("row-growth audit response-row count drifted")
    initial = tuple(row for row in response_rows if row.phase == "initial")
    if (
        len(initial) != game.num_players
        or tuple(row.target_player for row in initial)
        != tuple(range(game.num_players))
    ):
        raise AssertionError("row-growth audit initial-row order drifted")
    generated = tuple(row for row in response_rows if row.phase == "generated")
    expected_generated = tuple(
        (update.iteration, target)
        for update in result.iterations
        for target in update.added_targets
    )
    actual_generated = tuple(
        (row.after_iteration, row.target_player) for row in generated
    )
    if actual_generated != expected_generated:
        raise AssertionError("row-growth audit generated-row order drifted")
    for update, master in zip(result.iterations, masters, strict=True):
        if (
            update.iteration != master.iteration
            or update.response_rows_before
            != sum(
                1
                for row in response_rows
                if row.phase == "initial"
                or (
                    row.after_iteration is not None
                    and row.after_iteration < update.iteration
                )
            )
        ):
            raise AssertionError("row-growth audit iteration binding drifted")

    return OneSeatRowGrowthAudit(
        result=result,
        evaluations=tuple(evaluations),
        masters=tuple(masters),
        response_rows=tuple(response_rows),
        best_response_calls=counters["best_response"],
        expected_utilities_calls=counters["expected_utilities"],
        open_axis_coefficient_calls=counters["open_axis"],
    )


__all__ = [
    "AuditedEvaluation",
    "AuditedMaster",
    "AuditedResponseRow",
    "OneSeatRowGrowthAudit",
    "audit_one_seat_row_growth",
]
