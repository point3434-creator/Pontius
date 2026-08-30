"""One validated monotonic witness shared by both ledgers (ADR-0485).

The witness invokes ``time.monotonic_ns`` in ordinary runs, returns an exact
nonnegative integer, rejects reversal, and retains its last returned sample.
A failed witness stays failed: no retry can repair it, and no caller may
latch, replay, or reconstruct a sample from a rounded duration.
"""

from __future__ import annotations

import time
from collections.abc import Callable


class ClockInvalidError(RuntimeError):
    """The witness returned a value that is not an exact nonnegative integer."""


class ClockReversedError(RuntimeError):
    """The witness moved backwards; monotonicity is unrecoverable."""


class MonotonicWitness:
    """Validated monotonic-nanosecond source with a retained last sample."""

    __slots__ = ("_source", "_last_returned_ns", "_failed")

    def __init__(self, source: Callable[[], int] | None = None) -> None:
        resolved = time.monotonic_ns if source is None else source
        if not callable(resolved):
            raise TypeError("monotonic witness requires a callable source")
        self._source = resolved
        self._last_returned_ns: int | None = None
        self._failed = False

    @property
    def last_returned_ns(self) -> int | None:
        """The last value this witness actually returned, or None before first use."""

        return self._last_returned_ns

    @property
    def failed(self) -> bool:
        return self._failed

    def __call__(self) -> int:
        if self._failed:
            raise ClockInvalidError("a failed monotonic witness is never retried")
        try:
            observed = self._source()
        except BaseException:
            self._failed = True
            raise
        if type(observed) is not int or observed < 0:
            self._failed = True
            raise ClockInvalidError("monotonic witness returned an invalid value")
        last = self._last_returned_ns
        if last is not None and observed < last:
            self._failed = True
            raise ClockReversedError("monotonic witness moved backwards")
        self._last_returned_ns = observed
        return observed


__all__ = [
    "ClockInvalidError",
    "ClockReversedError",
    "MonotonicWitness",
]
