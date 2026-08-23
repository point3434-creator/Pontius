"""Continuous per-action response wall and separate online-work accounting.

ADR-0307 supersedes the cumulative-street live contract without mutating its
historical implementation.  This module measures the hard response wall from
the exact turn boundary, whether or not every interval is instrumented, while
keeping pre-action workstation work in a separate preparation ledger.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .street_deadline import STREET_ORDER, StreetName

if TYPE_CHECKING:
    from .preparation_bank import PreparationUse

ACTION_RESPONSE_WALL_SECONDS = 15.0
ACTION_EMISSION_RESERVE_SECONDS = 1.0
_NANOSECONDS_PER_SECOND = 1_000_000_000


def _validate_street(street: str) -> StreetName:
    if street not in STREET_ORDER:
        raise ValueError("action clock requires a canonical poker street")
    return street  # type: ignore[return-value]


def _require_positive_integer(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value <= 0:
        raise ValueError(f"{label} must be positive")
    return value


def _require_digest(value: object, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise TypeError(f"{label} must be one lowercase SHA-256 digest")
    if value != value.lower() or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be one lowercase SHA-256 digest")
    return value


@dataclass(frozen=True, slots=True)
class ActionClockIdentity:
    """One unambiguous controlled-action position inside a hand ledger."""

    street: StreetName
    hand_action_index: int
    street_action_index: int
    public_state_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "street", _validate_street(self.street))
        object.__setattr__(
            self,
            "hand_action_index",
            _require_positive_integer(
                self.hand_action_index,
                label="hand action index",
            ),
        )
        object.__setattr__(
            self,
            "street_action_index",
            _require_positive_integer(
                self.street_action_index,
                label="street action index",
            ),
        )
        object.__setattr__(
            self,
            "public_state_sha256",
            _require_digest(
                self.public_state_sha256,
                label="action public state digest",
            ),
        )


@dataclass(frozen=True, slots=True)
class PreparationWorkInterval:
    """One internally timed pre-action workstation interval."""

    street: StreetName
    hand_interval_index: int
    street_interval_index: int
    compute_seconds: float


@dataclass(frozen=True, slots=True)
class ActionClockSnapshot:
    """Immutable observation of one active or just-completed response wall."""

    action: ActionClockIdentity
    maximum_seconds: float
    action_emission_reserve_seconds: float
    action_wall_elapsed_seconds: float
    response_compute_seconds: float
    response_uninstrumented_seconds: float
    remaining_seconds: float
    work_remaining_seconds: float
    reserve_remaining_seconds: float
    deadline_crossed: bool
    credited_preparation_seconds: float
    preparation_artifact_sha256s: tuple[str, ...]
    response_charge_intervals: int
    charging: bool


@dataclass(frozen=True, slots=True)
class CompletedStreetActionTiming:
    """One archived street with every controlled response and preparation total."""

    street: StreetName
    street_wall_elapsed_seconds: float
    preparation_compute_seconds: float
    preparation_intervals: int
    actions: tuple[ActionClockSnapshot, ...]
    deadline_crossed: bool


@dataclass(frozen=True, slots=True)
class _TransitionBoundary:
    token: int
    street: StreetName
    started_ns: int


class ActionClockStop(RuntimeError):
    def __init__(self, snapshot: ActionClockSnapshot) -> None:
        self.snapshot = snapshot
        super().__init__(
            f"action response wall exhausted on {snapshot.action.street}: "
            f"remaining={snapshot.remaining_seconds:.9f}s"
        )


class ActionClockLedger:
    """Own continuous response walls and separately measured preparation work."""

    def __init__(
        self,
        street: StreetName,
        *,
        clock_ns: Callable[[], int] | None = None,
    ) -> None:
        self._clock_ns = time.monotonic_ns if clock_ns is None else clock_ns
        if not callable(self._clock_ns):
            raise TypeError("action clock must be callable")
        self._street = _validate_street(street)
        started = self._read_clock()
        self._street_started_ns = started
        self._last_observed_ns = started
        self._hand_action_index = 0
        self._street_action_index = 0
        self._action: ActionClockIdentity | None = None
        self._action_started_ns: int | None = None
        self._response_compute_ns = 0
        self._response_charge_intervals = 0
        self._preparation_uses: list[PreparationUse] = []
        self._charge_started_ns: int | None = None
        self._charge_kind: str | None = None
        self._street_preparation_ns = 0
        self._street_preparation_intervals = 0
        self._hand_preparation_ns = 0
        self._hand_preparation_intervals = 0
        self._current_street_actions: list[ActionClockSnapshot] = []
        self._completed_actions: list[ActionClockSnapshot] = []
        self._completed_streets: list[CompletedStreetActionTiming] = []
        self._boundary: _TransitionBoundary | None = None
        self._boundary_counter = 0
        self._finalized_ns: int | None = None

    def _read_clock(self) -> int:
        value = self._clock_ns()
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise RuntimeError("action monotonic clock returned an invalid value")
        return value

    def _observe(self) -> int:
        observed = self._read_clock()
        if observed < self._last_observed_ns:
            raise RuntimeError("action monotonic clock moved backwards")
        self._last_observed_ns = observed
        return observed

    @property
    def street(self) -> StreetName:
        return self._street

    @property
    def action_active(self) -> bool:
        return self._action is not None

    @property
    def current_action(self) -> ActionClockIdentity | None:
        return self._action

    @property
    def charging(self) -> bool:
        return self._charge_started_ns is not None

    @property
    def transition_active(self) -> bool:
        return self._boundary is not None

    @property
    def finalized(self) -> bool:
        return self._finalized_ns is not None

    @property
    def completed_actions(self) -> tuple[ActionClockSnapshot, ...]:
        return tuple(self._completed_actions)

    @property
    def completed_streets(self) -> tuple[CompletedStreetActionTiming, ...]:
        return tuple(self._completed_streets)

    @property
    def hand_preparation_compute_seconds(self) -> float:
        active_ns = 0
        if self._charge_kind == "preparation":
            active_ns = self._observe() - int(self._charge_started_ns)
        return (self._hand_preparation_ns + active_ns) / _NANOSECONDS_PER_SECOND

    def _action_snapshot_at(self, observed: int) -> ActionClockSnapshot:
        if self._action is None or self._action_started_ns is None:
            raise RuntimeError("no controlled action response is active")
        active_ns = 0
        if self._charge_kind == "response":
            active_ns = observed - int(self._charge_started_ns)
        response_compute_ns = self._response_compute_ns + active_ns
        elapsed_ns = observed - self._action_started_ns
        if response_compute_ns > elapsed_ns:
            raise RuntimeError("instrumented response compute exceeds action wall")
        elapsed = elapsed_ns / _NANOSECONDS_PER_SECOND
        response_compute = response_compute_ns / _NANOSECONDS_PER_SECOND
        remaining = ACTION_RESPONSE_WALL_SECONDS - elapsed
        positive_remaining = max(0.0, remaining)
        work_remaining = max(
            0.0,
            positive_remaining - ACTION_EMISSION_RESERVE_SECONDS,
        )
        credited = sum(use.credit.preparation_compute_seconds for use in self._preparation_uses)
        return ActionClockSnapshot(
            action=self._action,
            maximum_seconds=ACTION_RESPONSE_WALL_SECONDS,
            action_emission_reserve_seconds=ACTION_EMISSION_RESERVE_SECONDS,
            action_wall_elapsed_seconds=elapsed,
            response_compute_seconds=response_compute,
            response_uninstrumented_seconds=(elapsed_ns - response_compute_ns)
            / _NANOSECONDS_PER_SECOND,
            remaining_seconds=remaining,
            work_remaining_seconds=work_remaining,
            reserve_remaining_seconds=positive_remaining - work_remaining,
            deadline_crossed=elapsed > ACTION_RESPONSE_WALL_SECONDS,
            credited_preparation_seconds=credited,
            preparation_artifact_sha256s=tuple(
                use.credit.artifact_sha256 for use in self._preparation_uses
            ),
            response_charge_intervals=self._response_charge_intervals,
            charging=self._charge_kind == "response",
        )

    def snapshot(self) -> ActionClockSnapshot:
        """Observe the active response; the continuous wall always advances."""

        return self._action_snapshot_at(self._observe())

    def _begin_action_at(
        self,
        started_ns: int,
        *,
        public_state_sha256: str,
        initial_response_compute_ns: int = 0,
        initial_response_charge_intervals: int = 0,
    ) -> ActionClockSnapshot:
        if self.finalized:
            raise RuntimeError("a finalized action ledger cannot begin a response")
        if self.action_active:
            raise RuntimeError("a controlled action response is already active")
        if self.charging or self.transition_active:
            raise RuntimeError("finish pending timing work before beginning a response")
        if started_ns > self._last_observed_ns:
            raise RuntimeError("action response cannot start in the future")
        self._hand_action_index += 1
        self._street_action_index += 1
        self._action = ActionClockIdentity(
            street=self._street,
            hand_action_index=self._hand_action_index,
            street_action_index=self._street_action_index,
            public_state_sha256=_require_digest(
                public_state_sha256,
                label="action public state digest",
            ),
        )
        self._action_started_ns = started_ns
        self._response_compute_ns = initial_response_compute_ns
        self._response_charge_intervals = initial_response_charge_intervals
        self._preparation_uses = []
        return self._action_snapshot_at(self._last_observed_ns)

    def begin_action(self, *, public_state_sha256: str) -> ActionClockSnapshot:
        """Start one fresh response wall at the current exact turn boundary."""

        observed = self._observe()
        return self._begin_action_at(
            observed,
            public_state_sha256=public_state_sha256,
        )

    def start_response_work(self) -> ActionClockSnapshot:
        if not self.action_active:
            raise RuntimeError("response work requires an active controlled action")
        if self.charging:
            raise RuntimeError("work is already being timed")
        if self.transition_active:
            raise RuntimeError("a turn transition is already being timed")
        observed = self._observe()
        self._charge_started_ns = observed
        self._charge_kind = "response"
        self._response_charge_intervals += 1
        return self._action_snapshot_at(observed)

    def stop_response_work(self) -> ActionClockSnapshot:
        if self._charge_kind != "response" or self._charge_started_ns is None:
            raise RuntimeError("response work is not currently being timed")
        observed = self._observe()
        self._response_compute_ns += observed - self._charge_started_ns
        self._charge_started_ns = None
        self._charge_kind = None
        return self._action_snapshot_at(observed)

    @contextmanager
    def response_work(self) -> Iterator[ActionClockLedger]:
        self.start_response_work()
        try:
            yield self
        finally:
            self.stop_response_work()

    def _record_preparation_interval(
        self,
        *,
        started_ns: int,
        stopped_ns: int,
    ) -> PreparationWorkInterval:
        duration_ns = stopped_ns - started_ns
        if duration_ns < 0:
            raise RuntimeError("preparation interval has negative duration")
        self._street_preparation_ns += duration_ns
        self._hand_preparation_ns += duration_ns
        self._street_preparation_intervals += 1
        self._hand_preparation_intervals += 1
        return PreparationWorkInterval(
            street=self._street,
            hand_interval_index=self._hand_preparation_intervals,
            street_interval_index=self._street_preparation_intervals,
            compute_seconds=duration_ns / _NANOSECONDS_PER_SECOND,
        )

    def start_preparation_work(self) -> None:
        if self.finalized:
            raise RuntimeError("a finalized action ledger cannot prepare more work")
        if self.action_active:
            raise RuntimeError("on-clock work cannot be labeled as preparation")
        if self.charging:
            raise RuntimeError("work is already being timed")
        if self.transition_active:
            raise RuntimeError("a turn transition is already being timed")
        self._charge_started_ns = self._observe()
        self._charge_kind = "preparation"

    def stop_preparation_work(self) -> PreparationWorkInterval:
        if self._charge_kind != "preparation" or self._charge_started_ns is None:
            raise RuntimeError("preparation work is not currently being timed")
        observed = self._observe()
        started = self._charge_started_ns
        self._charge_started_ns = None
        self._charge_kind = None
        return self._record_preparation_interval(
            started_ns=started,
            stopped_ns=observed,
        )

    @contextmanager
    def preparation_work(self) -> Iterator[ActionClockLedger]:
        self.start_preparation_work()
        try:
            yield self
        finally:
            self.stop_preparation_work()

    def start_transition_boundary(self) -> _TransitionBoundary:
        """Capture event arrival before knowing whether it yields our action."""

        if self.finalized:
            raise RuntimeError("a finalized action ledger cannot observe an event")
        if self.action_active:
            raise RuntimeError("finish the controlled action before another event")
        if self.charging or self.transition_active:
            raise RuntimeError("finish pending timing work before another event")
        observed = self._observe()
        self._boundary_counter += 1
        boundary = _TransitionBoundary(
            token=self._boundary_counter,
            street=self._street,
            started_ns=observed,
        )
        self._boundary = boundary
        return boundary

    def _validate_next_street(self, street: StreetName) -> StreetName:
        next_street = _validate_street(street)
        current_index = STREET_ORDER.index(self._street)
        if current_index + 1 >= len(STREET_ORDER) or STREET_ORDER[current_index + 1] != next_street:
            raise ValueError("action timing must advance exactly one street")
        return next_street

    def _archive_street_at(self, observed: int) -> CompletedStreetActionTiming:
        wall_elapsed = (observed - self._street_started_ns) / _NANOSECONDS_PER_SECOND
        if wall_elapsed < 0.0:
            raise RuntimeError("street archive predates its start")
        actions = tuple(self._current_street_actions)
        snapshot = CompletedStreetActionTiming(
            street=self._street,
            street_wall_elapsed_seconds=wall_elapsed,
            preparation_compute_seconds=(self._street_preparation_ns / _NANOSECONDS_PER_SECOND),
            preparation_intervals=self._street_preparation_intervals,
            actions=actions,
            deadline_crossed=any(action.deadline_crossed for action in actions),
        )
        self._completed_streets.append(snapshot)
        return snapshot

    def finish_transition_boundary(
        self,
        boundary: _TransitionBoundary,
        *,
        starts_controlled_action: bool,
        controlled_action_public_state_sha256: str | None = None,
        next_street: StreetName | None = None,
    ) -> ActionClockSnapshot | PreparationWorkInterval:
        if boundary is not self._boundary:
            raise ValueError("turn boundary is stale or belongs elsewhere")
        if not isinstance(starts_controlled_action, bool):
            raise TypeError("controlled-action boundary flag must be boolean")
        if starts_controlled_action:
            public_state = _require_digest(
                controlled_action_public_state_sha256,
                label="controlled-action public state digest",
            )
        elif controlled_action_public_state_sha256 is not None:
            raise ValueError("a non-action boundary cannot carry an action state")
        else:
            public_state = None
        resolved_next = None if next_street is None else self._validate_next_street(next_street)
        observed = self._observe()
        started = boundary.started_ns
        self._boundary = None
        if resolved_next is not None:
            self._archive_street_at(started)
            self._street = resolved_next
            self._street_started_ns = started
            self._street_action_index = 0
            self._street_preparation_ns = 0
            self._street_preparation_intervals = 0
            self._current_street_actions = []
        if starts_controlled_action:
            assert public_state is not None
            return self._begin_action_at(
                started,
                public_state_sha256=public_state,
                initial_response_compute_ns=observed - started,
                initial_response_charge_intervals=1,
            )
        return self._record_preparation_interval(
            started_ns=started,
            stopped_ns=observed,
        )

    def abort_transition_boundary(
        self,
        boundary: _TransitionBoundary,
    ) -> PreparationWorkInterval:
        if boundary is not self._boundary:
            raise ValueError("turn boundary is stale or belongs elsewhere")
        observed = self._observe()
        self._boundary = None
        return self._record_preparation_interval(
            started_ns=boundary.started_ns,
            stopped_ns=observed,
        )

    def _attach_preparation(self, use: PreparationUse) -> ActionClockSnapshot:
        """Attach a bank-validated use; callers must claim through a bank."""

        from .preparation_bank import PreparationUse

        if not isinstance(use, PreparationUse):
            raise TypeError("action clock requires an exact preparation use")
        if self._action is None or use.action != self._action:
            raise ValueError("preparation use names a different controlled action")
        if any(
            prior.credit.artifact_sha256 == use.credit.artifact_sha256
            for prior in self._preparation_uses
        ):
            raise ValueError("controlled action repeats a preparation artifact")
        self._preparation_uses.append(use)
        return self.snapshot()

    def admitted_work_seconds(self, requested_seconds: float) -> float:
        if (
            isinstance(requested_seconds, bool)
            or not isinstance(requested_seconds, (int, float))
            or requested_seconds < 0.0
        ):
            raise ValueError("requested action work must be finite and nonnegative")
        requested = float(requested_seconds)
        if not math.isfinite(requested):
            raise ValueError("requested action work must be finite and nonnegative")
        if not self.action_active or self.finalized:
            return 0.0
        return min(requested, self.snapshot().work_remaining_seconds)

    def require_work_time(self) -> ActionClockSnapshot:
        snapshot = self.snapshot()
        if snapshot.work_remaining_seconds <= 0.0:
            raise ActionClockStop(snapshot)
        return snapshot

    def finish_action(self) -> ActionClockSnapshot:
        if not self.action_active:
            raise RuntimeError("no controlled action response is active")
        if self.charging:
            raise RuntimeError("stop timed work before finishing the response")
        if self.transition_active:
            raise RuntimeError("a turn transition cannot overlap a response")
        snapshot = self._action_snapshot_at(self._observe())
        self._completed_actions.append(snapshot)
        self._current_street_actions.append(snapshot)
        self._action = None
        self._action_started_ns = None
        self._response_compute_ns = 0
        self._response_charge_intervals = 0
        self._preparation_uses = []
        return snapshot

    def finalize(self) -> CompletedStreetActionTiming:
        if self.finalized:
            raise RuntimeError("action clock ledger is already finalized")
        if self.action_active or self.charging or self.transition_active:
            raise RuntimeError("finish active timing before finalizing the hand")
        observed = self._observe()
        archived = self._archive_street_at(observed)
        self._finalized_ns = observed
        return archived


__all__ = [
    "ACTION_EMISSION_RESERVE_SECONDS",
    "ACTION_RESPONSE_WALL_SECONDS",
    "ActionClockIdentity",
    "ActionClockLedger",
    "ActionClockSnapshot",
    "ActionClockStop",
    "CompletedStreetActionTiming",
    "PreparationWorkInterval",
]
