"""Provenance-bound one-use credits for online pre-action computation."""

from __future__ import annotations

import math
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256

from .action_clock import (
    ActionClockIdentity,
    ActionClockLedger,
    PreparationWorkInterval,
)
from .street_deadline import StreetName


def _require_digest(value: object, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise TypeError(f"{label} must be one lowercase SHA-256 digest")
    if value != value.lower() or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be one lowercase SHA-256 digest")
    return value


def _require_artifact_bytes(value: object) -> bytes:
    if not isinstance(value, bytes):
        raise TypeError("prepared artifact must be immutable bytes")
    if not value:
        raise ValueError("prepared artifact bytes must be nonempty")
    return value


@dataclass(frozen=True, slots=True)
class PreparedArtifactCredit:
    """One exact artifact produced by one internally measured interval."""

    artifact_bytes: bytes
    artifact_sha256: str
    public_state_sha256: str
    semantic_context_sha256: str
    source_sha256: str
    created_street: StreetName
    interval: PreparationWorkInterval
    preparation_compute_seconds: float

    def __post_init__(self) -> None:
        artifact = _require_artifact_bytes(self.artifact_bytes)
        artifact_digest = _require_digest(
            self.artifact_sha256,
            label="prepared artifact digest",
        )
        if sha256(artifact).hexdigest() != artifact_digest:
            raise ValueError("prepared artifact bytes differ from their digest")
        _require_digest(self.public_state_sha256, label="prepared public state digest")
        _require_digest(
            self.semantic_context_sha256,
            label="prepared semantic context digest",
        )
        _require_digest(self.source_sha256, label="prepared source digest")
        if not isinstance(self.interval, PreparationWorkInterval):
            raise TypeError("prepared credit requires an exact timed interval")
        if self.created_street != self.interval.street:
            raise ValueError("prepared credit street differs from its timed interval")
        seconds = self.preparation_compute_seconds
        if (
            isinstance(seconds, bool)
            or not isinstance(seconds, (int, float))
            or not math.isfinite(float(seconds))
            or float(seconds) < 0.0
        ):
            raise ValueError("prepared compute seconds must be finite and nonnegative")
        if float(seconds) != self.interval.compute_seconds:
            raise ValueError("prepared compute seconds differ from their owned interval")


@dataclass(frozen=True, slots=True)
class PreparationUse:
    """One preparation credit irreversibly attached to one controlled action."""

    credit: PreparedArtifactCredit
    action: ActionClockIdentity

    def __post_init__(self) -> None:
        if not isinstance(self.credit, PreparedArtifactCredit):
            raise TypeError("preparation use requires an exact artifact credit")
        if not isinstance(self.action, ActionClockIdentity):
            raise TypeError("preparation use requires an exact action identity")


@dataclass(frozen=True, slots=True)
class PreparationBankSnapshot:
    total_spent_compute_seconds: float
    sealed_compute_seconds: float
    claimed_compute_seconds: float
    unclaimed_compute_seconds: float
    invalidated_compute_seconds: float
    aborted_compute_seconds: float
    entries: int
    claimed_entries: int
    invalidated_entries: int
    aborted_intervals: int
    failed_claims: int
    preparing: bool


@dataclass(frozen=True, slots=True)
class _ActivePreparation:
    public_state_sha256: str
    semantic_context_sha256: str
    source_sha256: str
    created_street: StreetName


class PreparationBank:
    """Own exact preparation bytes, timing, invalidation, and one-use claims."""

    def __init__(self, *, action_clock: ActionClockLedger) -> None:
        if not isinstance(action_clock, ActionClockLedger):
            raise TypeError("preparation bank requires an exact action clock")
        self._action_clock = action_clock
        self._active: _ActivePreparation | None = None
        self._entries: dict[str, PreparedArtifactCredit] = {}
        self._claimed: dict[str, PreparationUse] = {}
        self._invalidated: set[str] = set()
        self._aborted_compute_seconds = 0.0
        self._aborted_intervals = 0
        self._failed_claims = 0

    @property
    def action_clock(self) -> ActionClockLedger:
        return self._action_clock

    @property
    def preparing(self) -> bool:
        return self._active is not None

    def start_preparation(
        self,
        *,
        target_public_state_sha256: str,
        semantic_context_sha256: str,
        source_sha256: str,
    ) -> None:
        if self.preparing:
            raise RuntimeError("preparation bank is already building an artifact")
        active = _ActivePreparation(
            public_state_sha256=_require_digest(
                target_public_state_sha256,
                label="target public state digest",
            ),
            semantic_context_sha256=_require_digest(
                semantic_context_sha256,
                label="semantic context digest",
            ),
            source_sha256=_require_digest(
                source_sha256,
                label="preparation source digest",
            ),
            created_street=self._action_clock.street,
        )
        self._action_clock.start_preparation_work()
        self._active = active

    @contextmanager
    def prepare_artifact(
        self,
        *,
        target_public_state_sha256: str,
        semantic_context_sha256: str,
        source_sha256: str,
    ) -> Iterator[PreparationBank]:
        """Abort and account for any artifact work that leaves without sealing."""

        self.start_preparation(
            target_public_state_sha256=target_public_state_sha256,
            semantic_context_sha256=semantic_context_sha256,
            source_sha256=source_sha256,
        )
        try:
            yield self
        finally:
            if self.preparing:
                self.abort_preparation()

    def seal_preparation(self, artifact_bytes: bytes) -> PreparedArtifactCredit:
        if self._active is None:
            raise RuntimeError("preparation bank has no active artifact work")
        artifact = _require_artifact_bytes(artifact_bytes)
        artifact_digest = sha256(artifact).hexdigest()
        active = self._active
        interval = self._action_clock.stop_preparation_work()
        self._active = None
        if artifact_digest in self._entries:
            self._aborted_compute_seconds += interval.compute_seconds
            self._aborted_intervals += 1
            raise ValueError("preparation bank repeats an artifact identity")
        credit = PreparedArtifactCredit(
            artifact_bytes=artifact,
            artifact_sha256=artifact_digest,
            public_state_sha256=active.public_state_sha256,
            semantic_context_sha256=active.semantic_context_sha256,
            source_sha256=active.source_sha256,
            created_street=active.created_street,
            interval=interval,
            preparation_compute_seconds=interval.compute_seconds,
        )
        self._entries[artifact_digest] = credit
        return credit

    def abort_preparation(self) -> PreparationWorkInterval:
        if self._active is None:
            raise RuntimeError("preparation bank has no active artifact work")
        interval = self._action_clock.stop_preparation_work()
        self._active = None
        self._aborted_compute_seconds += interval.compute_seconds
        self._aborted_intervals += 1
        return interval

    def _failed_claim(self, message: str) -> None:
        self._failed_claims += 1
        raise ValueError(message)

    def claim(
        self,
        *,
        artifact_bytes: bytes,
        semantic_context_sha256: str,
        source_sha256: str,
    ) -> PreparationUse:
        artifact = _require_artifact_bytes(artifact_bytes)
        semantic = _require_digest(
            semantic_context_sha256,
            label="consumer semantic context digest",
        )
        source = _require_digest(source_sha256, label="consumer source digest")
        action = self._action_clock.current_action
        if action is None:
            self._failed_claim("preparation claim requires an active controlled action")
        artifact_digest = sha256(artifact).hexdigest()
        credit = self._entries.get(artifact_digest)
        if credit is None:
            self._failed_claim("prepared artifact is absent")
        assert credit is not None
        if artifact_digest in self._invalidated:
            self._failed_claim("prepared artifact is invalidated")
        if artifact_digest in self._claimed:
            self._failed_claim("prepared artifact credit was already used")
        if credit.artifact_bytes != artifact:
            self._failed_claim("prepared artifact bytes differ")
        if credit.public_state_sha256 != action.public_state_sha256:
            self._failed_claim("prepared artifact public state is stale")
        if credit.semantic_context_sha256 != semantic:
            self._failed_claim("prepared artifact semantic context is stale")
        if credit.source_sha256 != source:
            self._failed_claim("prepared artifact source is stale")
        use = PreparationUse(credit=credit, action=action)
        self._action_clock._attach_preparation(use)
        self._claimed[artifact_digest] = use
        return use

    def invalidate(self, *, artifact_bytes: bytes) -> PreparedArtifactCredit:
        artifact = _require_artifact_bytes(artifact_bytes)
        artifact_digest = sha256(artifact).hexdigest()
        credit = self._entries.get(artifact_digest)
        if credit is None:
            raise ValueError("cannot invalidate an absent prepared artifact")
        if artifact_digest in self._claimed:
            raise ValueError("cannot invalidate an already-used preparation credit")
        if artifact_digest in self._invalidated:
            raise ValueError("prepared artifact is already invalidated")
        self._invalidated.add(artifact_digest)
        return credit

    def snapshot(self) -> PreparationBankSnapshot:
        sealed = sum(credit.preparation_compute_seconds for credit in self._entries.values())
        claimed = sum(use.credit.preparation_compute_seconds for use in self._claimed.values())
        invalidated = sum(
            self._entries[digest].preparation_compute_seconds for digest in self._invalidated
        )
        unclaimed = sealed - claimed - invalidated
        return PreparationBankSnapshot(
            total_spent_compute_seconds=sealed + self._aborted_compute_seconds,
            sealed_compute_seconds=sealed,
            claimed_compute_seconds=claimed,
            unclaimed_compute_seconds=unclaimed,
            invalidated_compute_seconds=invalidated,
            aborted_compute_seconds=self._aborted_compute_seconds,
            entries=len(self._entries),
            claimed_entries=len(self._claimed),
            invalidated_entries=len(self._invalidated),
            aborted_intervals=self._aborted_intervals,
            failed_claims=self._failed_claims,
            preparing=self.preparing,
        )


__all__ = [
    "PreparationBank",
    "PreparationBankSnapshot",
    "PreparationUse",
    "PreparedArtifactCredit",
]
