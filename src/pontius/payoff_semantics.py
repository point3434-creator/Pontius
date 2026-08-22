"""Shared payoff-span semantics for quality and acceptance calculations."""

from __future__ import annotations

import math
from typing import Any


def payoff_span(layout: Any) -> float:
    """Return the game-derived payoff span and fail closed on bad layouts."""

    try:
        span = float(layout.game.payoff_span)
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError("layout must expose a finite positive game payoff span") from error
    if not math.isfinite(span) or span <= 0.0:
        raise ValueError("layout game payoff span must be finite and positive")
    return span


def raw_guard(layout: Any, normalized: float) -> float:
    """Convert a normalized acceptance guard using the game payoff span."""

    value = float(normalized)
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("normalized acceptance guard must be finite and nonnegative")
    return value * payoff_span(layout)


def normalized_quality(layout: Any, raw_quality: float) -> float:
    """Normalize a raw quality quantity using the game payoff span."""

    value = float(raw_quality)
    if not math.isfinite(value):
        raise ValueError("raw quality must be finite")
    return value / payoff_span(layout)
