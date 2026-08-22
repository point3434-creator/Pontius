"""Threshold-separated assessment of exact one-seat response-oracle gains."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True, slots=True)
class ExactOracleAssessment:
    gains: tuple[float, ...]
    cap_violations: tuple[float, ...]
    maximum_cap_violation: float
    cap_feasible: bool
    epigraph_violations: tuple[float, ...] | None
    maximum_epigraph_violation: float | None
    epigraph_violating_players: tuple[int, ...]
    epigraph_closed: bool | None


def assess_exact_oracle_gains(
    raw_gains: Sequence[float],
    caps: Sequence[float],
    *,
    cap_allowance: float,
    epigraph: Sequence[float] | None = None,
    epigraph_allowance: float | None = None,
) -> ExactOracleAssessment:
    """Assess cap safety and optional separation with distinct tolerances."""

    raw = tuple(float(value) for value in raw_gains)
    cap_values = tuple(float(value) for value in caps)
    if not raw or len(raw) != len(cap_values):
        raise ValueError("exact oracle gains and caps have different player axes")
    if any(not math.isfinite(value) for value in (*raw, *cap_values)):
        raise ValueError("exact oracle gains and caps must be finite")
    if any(value < 0.0 for value in cap_values):
        raise ValueError("exact oracle caps must be nonnegative")
    if not math.isfinite(cap_allowance) or cap_allowance < 0.0:
        raise ValueError("exact oracle cap allowance must be finite and nonnegative")

    gains = tuple(max(0.0, value) for value in raw)
    cap_violations = tuple(
        gain - cap for gain, cap in zip(gains, cap_values, strict=True)
    )
    maximum_cap_violation = max(0.0, max(cap_violations))

    if epigraph is None:
        if epigraph_allowance is not None:
            raise ValueError("epigraph allowance requires epigraph values")
        epigraph_violations = None
        maximum_epigraph_violation = None
        violating_players: tuple[int, ...] = ()
        epigraph_closed: bool | None = None
    else:
        epigraph_values = tuple(float(value) for value in epigraph)
        if len(epigraph_values) != len(raw):
            raise ValueError("exact oracle epigraph has the wrong player axis")
        if any(not math.isfinite(value) for value in epigraph_values):
            raise ValueError("exact oracle epigraph must be finite")
        if (
            epigraph_allowance is None
            or not math.isfinite(epigraph_allowance)
            or epigraph_allowance < 0.0
        ):
            raise ValueError(
                "exact oracle epigraph allowance must be finite and nonnegative"
            )
        epigraph_violations = tuple(
            value - bound
            for value, bound in zip(raw, epigraph_values, strict=True)
        )
        maximum_epigraph_violation = max(0.0, max(epigraph_violations))
        violating_players = tuple(
            player
            for player, violation in enumerate(epigraph_violations)
            if violation > epigraph_allowance
        )
        epigraph_closed = not violating_players

    return ExactOracleAssessment(
        gains=gains,
        cap_violations=cap_violations,
        maximum_cap_violation=maximum_cap_violation,
        cap_feasible=max(cap_violations) <= cap_allowance,
        epigraph_violations=epigraph_violations,
        maximum_epigraph_violation=maximum_epigraph_violation,
        epigraph_violating_players=violating_players,
        epigraph_closed=epigraph_closed,
    )
