"""Versioned tie-semantics registry for factorized affine integration.

ADR-0354's registry is historically source-sealed by the retained ADR-0356
artifact.  This successor extends it without mutating that evidence boundary.
The v1 consumers and controls remain mandatory; the new consumer adds the
fan/face seam, epigraph, dispatch, and no-materialization controls required by
the factorized integration path.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Iterable, Mapping

from .tie_semantics_conformance import (
    FUTURE_CROSSING_SEAM,
    HIGH_CARDINALITY_FACE,
    PARALLEL_SOURCE_TIE,
    POSITIVE_MEASURE_TIE,
    REPEATED_ACTOR_IDENTITY,
    SEPARATING_SOURCE_TIE,
    TIE_SEMANTICS_CONSUMERS,
    TieSemanticsConsumer,
)


FAN_FACE_SLOPE_SEAM = "fan_face_slope_seam"
MAXIMUM_EPIGRAPH_ORIENTATION = "maximum_envelope_z_greater_equal_row"
SINGLETON_V2_DISPATCH = "exact_singleton_selector_window_v2_dispatch"


TIE_SEMANTICS_CONSUMERS_V2 = MappingProxyType(
    {
        **TIE_SEMANTICS_CONSUMERS,
        "factorized_tie_aware_affine": TieSemanticsConsumer(
            "factorized_tie_aware_affine",
            "fan_ray_face_point_typed_affine_integration",
            frozenset(
                {
                    PARALLEL_SOURCE_TIE,
                    SEPARATING_SOURCE_TIE,
                    POSITIVE_MEASURE_TIE,
                    FUTURE_CROSSING_SEAM,
                    REPEATED_ACTOR_IDENTITY,
                    HIGH_CARDINALITY_FACE,
                    FAN_FACE_SLOPE_SEAM,
                    MAXIMUM_EPIGRAPH_ORIENTATION,
                    SINGLETON_V2_DISPATCH,
                }
            ),
        ),
    }
)


def validate_tie_semantics_conformance_v2(
    observed: Mapping[str, Iterable[str]],
) -> None:
    """Require the complete inherited-and-successor consumer registry."""

    if set(observed) != set(TIE_SEMANTICS_CONSUMERS_V2):
        raise ValueError("tie-semantics-v2 registry and observations differ")
    for name, specification in TIE_SEMANTICS_CONSUMERS_V2.items():
        actual = frozenset(observed[name])
        missing = specification.required_controls - actual
        if missing:
            raise ValueError(
                f"tie-semantics-v2 consumer {name} lacks controls: {sorted(missing)}"
            )


__all__ = [
    "FAN_FACE_SLOPE_SEAM",
    "MAXIMUM_EPIGRAPH_ORIENTATION",
    "SINGLETON_V2_DISPATCH",
    "TIE_SEMANTICS_CONSUMERS_V2",
    "validate_tie_semantics_conformance_v2",
]
