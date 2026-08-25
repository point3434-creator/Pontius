"""Mechanical registry for exact-tie semantic consumers.

Every live or retained computational consumer named here must be exercised by
all of its registered controls in the shared conformance test.  Adding a new
consumer without adding its control observations fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping


PARALLEL_SOURCE_TIE = "parallel_source_tie"
SEPARATING_SOURCE_TIE = "separating_source_tie"
POSITIVE_MEASURE_TIE = "positive_measure_tie"
FUTURE_CROSSING_SEAM = "future_crossing_seam"
REPEATED_ACTOR_IDENTITY = "repeated_actor_total_reachable_identity"
HIGH_CARDINALITY_FACE = "high_cardinality_face_without_materialization"


@dataclass(frozen=True, slots=True)
class TieSemanticsConsumer:
    name: str
    authority: str
    required_controls: frozenset[str]


TIE_SEMANTICS_CONSUMERS = MappingProxyType(
    {
        "selector_window_v2": TieSemanticsConsumer(
            "selector_window_v2",
            "fail_closed_single_tape_certificate",
            frozenset({PARALLEL_SOURCE_TIE, SEPARATING_SOURCE_TIE}),
        ),
        "exact_selector_fan": TieSemanticsConsumer(
            "exact_selector_fan",
            "three_valued_ray_partition",
            frozenset({POSITIVE_MEASURE_TIE, FUTURE_CROSSING_SEAM}),
        ),
        "exact_tie_aware_affine_envelope": TieSemanticsConsumer(
            "exact_tie_aware_affine_envelope",
            "closed_bounded_synthetic_reference",
            frozenset({POSITIVE_MEASURE_TIE, FUTURE_CROSSING_SEAM}),
        ),
        "tie_aware_affine_adapter": TieSemanticsConsumer(
            "tie_aware_affine_adapter",
            "typed_tied_face_dispatch",
            frozenset({PARALLEL_SOURCE_TIE, POSITIVE_MEASURE_TIE}),
        ),
        "exact_directional_face_oracle": TieSemanticsConsumer(
            "exact_directional_face_oracle",
            "factorized_point_face_sensitivity",
            frozenset(
                {
                    POSITIVE_MEASURE_TIE,
                    FUTURE_CROSSING_SEAM,
                    REPEATED_ACTOR_IDENTITY,
                    HIGH_CARDINALITY_FACE,
                }
            ),
        ),
        "compose_exact_directional_face_fan_section": TieSemanticsConsumer(
            "compose_exact_directional_face_fan_section",
            "complete_ray_and_face_composition",
            frozenset({POSITIVE_MEASURE_TIE, FUTURE_CROSSING_SEAM}),
        ),
    }
)


def validate_tie_semantics_conformance(
    observed: Mapping[str, Iterable[str]],
) -> None:
    """Require every registered consumer to expose every required control."""

    if set(observed) != set(TIE_SEMANTICS_CONSUMERS):
        raise ValueError("tie-semantics consumer registry and observations differ")
    for name, specification in TIE_SEMANTICS_CONSUMERS.items():
        actual = frozenset(observed[name])
        missing = specification.required_controls - actual
        if missing:
            raise ValueError(
                f"tie-semantics consumer {name} lacks controls: {sorted(missing)}"
            )


__all__ = [
    "FUTURE_CROSSING_SEAM",
    "HIGH_CARDINALITY_FACE",
    "PARALLEL_SOURCE_TIE",
    "POSITIVE_MEASURE_TIE",
    "REPEATED_ACTOR_IDENTITY",
    "SEPARATING_SOURCE_TIE",
    "TIE_SEMANTICS_CONSUMERS",
    "TieSemanticsConsumer",
    "validate_tie_semantics_conformance",
]
