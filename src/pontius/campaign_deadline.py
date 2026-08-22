"""Fail-closed active deadline admission for bounded campaigns."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CampaignDeadlineSnapshot:
    """One finite observation of a shared monotonic campaign deadline."""

    maximum_seconds: float
    elapsed_seconds: float
    remaining_seconds: float
    deadline_crossed: bool

    def as_record(self) -> dict[str, Any]:
        """Return JSON-safe deadline telemetry for a checkpoint or result."""

        return {
            "clock": "monotonic_ns",
            "maximum_seconds": self.maximum_seconds,
            "elapsed_seconds": self.elapsed_seconds,
            "remaining_seconds": self.remaining_seconds,
            "deadline_crossed": self.deadline_crossed,
        }


class CampaignDeadlineStop(RuntimeError):
    """A fail-closed stop before or immediately after one bounded unit."""

    def __init__(
        self,
        *,
        reason: str,
        unit_name: str,
        maximum_unit_seconds: float,
        snapshot: CampaignDeadlineSnapshot,
        unit_elapsed_seconds: float | None = None,
    ) -> None:
        if reason not in {
            "insufficient_remaining_time",
            "deadline_crossed",
            "unit_bound_crossed",
        }:
            raise ValueError("campaign deadline stop reason is invalid")
        self.reason = reason
        self.unit_name = unit_name
        self.maximum_unit_seconds = maximum_unit_seconds
        self.snapshot = snapshot
        self.unit_elapsed_seconds = unit_elapsed_seconds
        super().__init__(
            f"campaign deadline stop for {unit_name}: {reason}; "
            f"remaining={snapshot.remaining_seconds:.9f}s, "
            f"unit_bound={maximum_unit_seconds:.9f}s"
        )

    def as_record(self) -> dict[str, Any]:
        """Return deterministic stop telemetry suitable for an atomic checkpoint."""

        return {
            "reason": self.reason,
            "unit_name": self.unit_name,
            "maximum_unit_seconds": self.maximum_unit_seconds,
            "unit_elapsed_seconds": self.unit_elapsed_seconds,
            "deadline": self.snapshot.as_record(),
        }


class MonotonicCampaignDeadline:
    """Admit bounded campaign units only while their frozen bound still fits.

    The checkpoint callback runs before every admission decision. Callers use
    :meth:`bounded_unit` around each target or arm so a unit that violates its
    own bound cannot silently continue into another unit or label phase.
    """

    _NANOSECONDS_PER_SECOND = 1_000_000_000

    def __init__(
        self,
        maximum_seconds: float,
        *,
        clock_ns: Callable[[], int] | None = None,
    ) -> None:
        maximum_seconds = self._validate_seconds(
            maximum_seconds,
            label="campaign maximum",
        )
        scaled_duration = maximum_seconds * self._NANOSECONDS_PER_SECOND
        if not math.isfinite(scaled_duration):
            raise ValueError("campaign maximum exceeds clock range")
        duration_ns = math.floor(scaled_duration)
        if duration_ns <= 0:
            raise ValueError("campaign maximum is below clock resolution")
        self._maximum_seconds = maximum_seconds
        self._clock_ns = time.monotonic_ns if clock_ns is None else clock_ns
        if not callable(self._clock_ns):
            raise TypeError("campaign clock must be callable")
        started_ns = self._read_clock_value()
        self._started_ns = started_ns
        self._last_observed_ns = started_ns
        self._deadline_ns = started_ns + duration_ns

    @staticmethod
    def _validate_seconds(value: float, *, label: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{label} must be numeric")
        result = float(value)
        if not math.isfinite(result) or result <= 0.0:
            raise ValueError(f"{label} must be finite and positive")
        return result

    def _read_clock_value(self) -> int:
        value = self._clock_ns()
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise RuntimeError("campaign monotonic clock returned an invalid value")
        return value

    def _observe(self) -> int:
        observed_ns = self._read_clock_value()
        if observed_ns < self._last_observed_ns:
            raise RuntimeError("campaign monotonic clock moved backwards")
        self._last_observed_ns = observed_ns
        return observed_ns

    def _snapshot_at(self, observed_ns: int) -> CampaignDeadlineSnapshot:
        return CampaignDeadlineSnapshot(
            maximum_seconds=self._maximum_seconds,
            elapsed_seconds=(observed_ns - self._started_ns) / self._NANOSECONDS_PER_SECOND,
            remaining_seconds=(self._deadline_ns - observed_ns) / self._NANOSECONDS_PER_SECOND,
            deadline_crossed=observed_ns > self._deadline_ns,
        )

    def snapshot(self) -> CampaignDeadlineSnapshot:
        """Observe the campaign clock without admitting new work."""

        return self._snapshot_at(self._observe())

    def checkpoint_before_unit(
        self,
        unit_name: str,
        maximum_unit_seconds: float,
        *,
        checkpoint: Callable[[], object],
    ) -> CampaignDeadlineSnapshot:
        """Checkpoint, then admit one unit only when its whole bound still fits."""

        if not isinstance(unit_name, str) or not unit_name.strip():
            raise ValueError("campaign unit name must be a nonempty string")
        maximum_unit_seconds = self._validate_seconds(
            maximum_unit_seconds,
            label="campaign unit maximum",
        )
        scaled_unit = maximum_unit_seconds * self._NANOSECONDS_PER_SECOND
        if not math.isfinite(scaled_unit):
            raise ValueError("campaign unit maximum exceeds clock range")
        required_ns = math.ceil(scaled_unit)
        if not callable(checkpoint):
            raise TypeError("campaign unit checkpoint must be callable")
        checkpoint()
        observed_ns = self._observe()
        snapshot = self._snapshot_at(observed_ns)
        remaining_ns = self._deadline_ns - observed_ns
        if remaining_ns < required_ns:
            raise CampaignDeadlineStop(
                reason="insufficient_remaining_time",
                unit_name=unit_name,
                maximum_unit_seconds=maximum_unit_seconds,
                snapshot=snapshot,
            )
        return snapshot

    def check_after_unit(
        self,
        unit_name: str,
        maximum_unit_seconds: float,
        *,
        admitted_ns: int | None = None,
    ) -> CampaignDeadlineSnapshot:
        """Stop immediately after a unit crosses its bound or the campaign wall."""

        if not isinstance(unit_name, str) or not unit_name.strip():
            raise ValueError("campaign unit name must be a nonempty string")
        maximum_unit_seconds = self._validate_seconds(
            maximum_unit_seconds,
            label="campaign unit maximum",
        )
        scaled_unit = maximum_unit_seconds * self._NANOSECONDS_PER_SECOND
        if not math.isfinite(scaled_unit):
            raise ValueError("campaign unit maximum exceeds clock range")
        maximum_unit_ns = math.floor(scaled_unit)
        observed_ns = self._observe()
        snapshot = self._snapshot_at(observed_ns)
        unit_elapsed_seconds = None
        unit_elapsed_ns = None
        if admitted_ns is not None:
            if (
                isinstance(admitted_ns, bool)
                or not isinstance(admitted_ns, int)
                or admitted_ns < self._started_ns
                or admitted_ns > observed_ns
            ):
                raise RuntimeError("campaign unit admission clock is invalid")
            unit_elapsed_ns = observed_ns - admitted_ns
            unit_elapsed_seconds = unit_elapsed_ns / self._NANOSECONDS_PER_SECOND
        if snapshot.deadline_crossed:
            raise CampaignDeadlineStop(
                reason="deadline_crossed",
                unit_name=unit_name,
                maximum_unit_seconds=maximum_unit_seconds,
                snapshot=snapshot,
                unit_elapsed_seconds=unit_elapsed_seconds,
            )
        if unit_elapsed_ns is not None and unit_elapsed_ns > maximum_unit_ns:
            raise CampaignDeadlineStop(
                reason="unit_bound_crossed",
                unit_name=unit_name,
                maximum_unit_seconds=maximum_unit_seconds,
                snapshot=snapshot,
                unit_elapsed_seconds=unit_elapsed_seconds,
            )
        return snapshot

    @contextmanager
    def bounded_unit(
        self,
        unit_name: str,
        maximum_unit_seconds: float,
        *,
        checkpoint: Callable[[], object],
    ) -> Iterator[CampaignDeadlineSnapshot]:
        """Guard one target or arm with pre-checkpoint admission and post-check."""

        admitted = self.checkpoint_before_unit(
            unit_name,
            maximum_unit_seconds,
            checkpoint=checkpoint,
        )
        admitted_ns = self._last_observed_ns
        yield admitted
        self.check_after_unit(
            unit_name,
            maximum_unit_seconds,
            admitted_ns=admitted_ns,
        )
