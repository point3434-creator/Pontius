"""One shared authoritative 15-second charged-compute ledger per poker street."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Literal

StreetName = Literal["preflop", "flop", "turn", "river"]
STREET_ORDER: tuple[StreetName, ...] = ("preflop", "flop", "turn", "river")
STREET_WALL_SECONDS = 15.0
ACTION_EMISSION_RESERVE_SECONDS = 1.0
_NANOSECONDS_PER_SECOND = 1_000_000_000


@dataclass(frozen=True, slots=True)
class StreetDeadlineSnapshot:
    street: StreetName
    maximum_seconds: float
    action_emission_reserve_seconds: float
    street_wall_elapsed_seconds: float
    charged_compute_seconds: float
    idle_wall_seconds: float
    remaining_seconds: float
    work_remaining_seconds: float
    reserve_remaining_seconds: float
    deadline_crossed: bool
    action_observations: int
    charge_intervals: int
    charging: bool


class StreetDeadlineStop(RuntimeError):
    def __init__(self, snapshot: StreetDeadlineSnapshot) -> None:
        self.snapshot = snapshot
        super().__init__(
            f"street wall exhausted on {snapshot.street}: "
            f"remaining={snapshot.remaining_seconds:.9f}s"
        )


class StreetDeadlineLedger:
    """Accumulate charged agent work across every action on one street.

    Opponent/transport idle time is not charged.  Any foreground or background
    agent work must therefore be enclosed by :meth:`start_charge` and
    :meth:`stop_charge` (or :meth:`charge`).
    """

    def __init__(
        self,
        street: StreetName,
        *,
        clock_ns: Callable[[], int] | None = None,
    ) -> None:
        self._clock_ns = time.monotonic_ns if clock_ns is None else clock_ns
        if not callable(self._clock_ns):
            raise TypeError("street deadline clock must be callable")
        self._street = self._validate_street(street)
        started = self._read_clock()
        self._street_started_ns = started
        self._last_observed_ns = started
        self._charged_ns = 0
        self._charge_started_ns: int | None = None
        self._charge_intervals = 0
        self._action_observations = 0
        self._completed_streets: list[StreetDeadlineSnapshot] = []
        self._finalized_ns: int | None = None

    @staticmethod
    def _validate_street(street: str) -> StreetName:
        if street not in STREET_ORDER:
            raise ValueError("street deadline requires a canonical poker street")
        return street  # type: ignore[return-value]

    def _read_clock(self) -> int:
        value = self._clock_ns()
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise RuntimeError("street monotonic clock returned an invalid value")
        return value

    def _observe(self) -> int:
        observed = self._read_clock()
        if observed < self._last_observed_ns:
            raise RuntimeError("street monotonic clock moved backwards")
        self._last_observed_ns = observed
        return observed

    @property
    def street(self) -> StreetName:
        return self._street

    @property
    def charging(self) -> bool:
        return self._charge_started_ns is not None

    @property
    def finalized(self) -> bool:
        return self._finalized_ns is not None

    @property
    def completed_streets(self) -> tuple[StreetDeadlineSnapshot, ...]:
        """Return immutable closing snapshots for every completed street."""

        return tuple(self._completed_streets)

    def _snapshot_at(self, observed: int) -> StreetDeadlineSnapshot:
        if self._finalized_ns is not None:
            observed = self._finalized_ns
        active_ns = (
            0
            if self._charge_started_ns is None
            else observed - self._charge_started_ns
        )
        charged = (self._charged_ns + active_ns) / _NANOSECONDS_PER_SECOND
        wall_elapsed = (observed - self._street_started_ns) / _NANOSECONDS_PER_SECOND
        idle = wall_elapsed - charged
        if idle < -1e-12:
            raise RuntimeError("charged compute exceeds elapsed street wall time")
        remaining = STREET_WALL_SECONDS - charged
        positive_remaining = max(0.0, remaining)
        work_remaining = max(
            0.0,
            positive_remaining - ACTION_EMISSION_RESERVE_SECONDS,
        )
        return StreetDeadlineSnapshot(
            street=self._street,
            maximum_seconds=STREET_WALL_SECONDS,
            action_emission_reserve_seconds=ACTION_EMISSION_RESERVE_SECONDS,
            street_wall_elapsed_seconds=wall_elapsed,
            charged_compute_seconds=charged,
            idle_wall_seconds=max(0.0, idle),
            remaining_seconds=remaining,
            work_remaining_seconds=work_remaining,
            reserve_remaining_seconds=positive_remaining - work_remaining,
            deadline_crossed=charged > STREET_WALL_SECONDS,
            action_observations=self._action_observations,
            charge_intervals=self._charge_intervals,
            charging=self.charging,
        )

    def snapshot(self) -> StreetDeadlineSnapshot:
        return self._snapshot_at(self._observe())

    def begin_action(self) -> StreetDeadlineSnapshot:
        """Observe an agent action without resetting or implicitly charging."""

        if self.finalized:
            raise RuntimeError("a finalized street ledger cannot begin an action")
        observed = self._observe()
        self._action_observations += 1
        return self._snapshot_at(observed)

    def start_charge(self) -> StreetDeadlineSnapshot:
        """Begin one explicit interval of foreground or background agent work."""

        if self.finalized:
            raise RuntimeError("a finalized street ledger cannot charge more work")
        if self.charging:
            raise RuntimeError("street compute is already being charged")
        observed = self._observe()
        self._charge_started_ns = observed
        self._charge_intervals += 1
        return self._snapshot_at(observed)

    def stop_charge(self) -> StreetDeadlineSnapshot:
        """End the current charged interval and retain it in the street total."""

        if self._charge_started_ns is None:
            raise RuntimeError("street compute is not currently being charged")
        observed = self._observe()
        self._charged_ns += observed - self._charge_started_ns
        self._charge_started_ns = None
        return self._snapshot_at(observed)

    @contextmanager
    def charge(self) -> Iterator[StreetDeadlineLedger]:
        """Charge one exception-safe interval to the current street."""

        self.start_charge()
        try:
            yield self
        finally:
            self.stop_charge()

    def admitted_work_seconds(self, requested_seconds: float) -> float:
        """Cap requested resolver work at the shared street work remainder."""

        if (
            isinstance(requested_seconds, bool)
            or not isinstance(requested_seconds, (int, float))
            or requested_seconds < 0.0
        ):
            raise ValueError("requested street work must be finite and nonnegative")
        requested = float(requested_seconds)
        if not math.isfinite(requested):
            raise ValueError("requested street work must be finite and nonnegative")
        if self.finalized:
            return 0.0
        return min(requested, self.snapshot().work_remaining_seconds)

    def require_work_time(self) -> StreetDeadlineSnapshot:
        """Fail closed once only the emission reserve (or less) remains."""

        if self.finalized:
            raise RuntimeError("a finalized street ledger has no work time")
        snapshot = self.snapshot()
        if snapshot.work_remaining_seconds <= 0.0:
            raise StreetDeadlineStop(snapshot)
        return snapshot

    def transition_to(self, street: StreetName) -> StreetDeadlineSnapshot:
        """Reset the wall only on the next actual street transition."""

        if self.finalized:
            raise RuntimeError("a finalized street ledger cannot transition")
        if self.charging:
            raise RuntimeError("stop charged compute before transitioning streets")
        next_street = self._validate_street(street)
        current_index = STREET_ORDER.index(self._street)
        if current_index + 1 >= len(STREET_ORDER) or STREET_ORDER[
            current_index + 1
        ] != next_street:
            raise ValueError("street deadline transitions must advance exactly one street")
        observed = self._observe()
        self._completed_streets.append(self._snapshot_at(observed))
        self._street = next_street
        self._street_started_ns = observed
        self._charged_ns = 0
        self._charge_started_ns = None
        self._charge_intervals = 0
        self._action_observations = 0
        return self._snapshot_at(observed)

    def finalize(self) -> StreetDeadlineSnapshot:
        """Close the terminal betting street and freeze its auditable snapshot."""

        if self.finalized:
            raise RuntimeError("street deadline ledger is already finalized")
        if self.charging:
            raise RuntimeError("stop charged compute before finalizing the street")
        observed = self._observe()
        final = self._snapshot_at(observed)
        self._completed_streets.append(final)
        self._finalized_ns = observed
        return final


__all__ = [
    "ACTION_EMISSION_RESERVE_SECONDS",
    "STREET_ORDER",
    "STREET_WALL_SECONDS",
    "StreetDeadlineLedger",
    "StreetDeadlineSnapshot",
    "StreetDeadlineStop",
    "StreetName",
]
