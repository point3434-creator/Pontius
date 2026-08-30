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

    __slots__ = ("_source", "_last_returned_ns", "_failed", "_failure", "_refusal")

    def __init__(self, source: Callable[[], int] | None = None) -> None:
        resolved = time.monotonic_ns if source is None else source
        if not callable(resolved):
            raise TypeError("monotonic witness requires a callable source")
        self._source = resolved
        self._last_returned_ns: int | None = None
        self._failed = False
        self._failure: ClockInvalidError | ClockReversedError | None = None
        self._refusal: ClockInvalidError | None = None

    @property
    def last_returned_ns(self) -> int | None:
        """The last value this witness actually returned, or None before first use."""

        return self._last_returned_ns

    @property
    def failed(self) -> bool:
        return self._failed

    @property
    def failure(self) -> ClockInvalidError | ClockReversedError | None:
        """The trusted original source occurrence, retained independently of refusals."""
        return self._failure

    def owns_failure(self, error: BaseException) -> bool:
        """Whether an exception is this witness's occurrence or its later refusal."""
        return self._failure is not None and (error is self._failure or error is self._refusal)

    def __call__(self) -> int:
        if self._failure is not None:
            assert self._refusal is not None
            raise self._refusal
        observed = None
        try:
            observed = self._source()
        except ClockReversedError:
            self._failure = ClockReversedError("monotonic witness source reversed")
        except BaseException:
            self._failure = ClockInvalidError("monotonic witness source failed")
        else:
            if type(observed) is not int or observed < 0:
                self._failure = ClockInvalidError("monotonic witness returned an invalid value")
            elif self._last_returned_ns is not None and observed < self._last_returned_ns:
                self._failure = ClockReversedError("monotonic witness moved backwards")
        if self._failure is not None:
            self._failed = True
            self._refusal = ClockInvalidError("a failed monotonic witness is never retried")
            # Raise our exact exception outside the source handler. Its identity,
            # not the source's message or exception metadata, denotes occurrence.
            raise self._failure from None
        self._last_returned_ns = observed
        return observed


__all__ = [
    "ClockInvalidError",
    "ClockReversedError",
    "MonotonicWitness",
]
