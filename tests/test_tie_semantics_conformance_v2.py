from __future__ import annotations

from fractions import Fraction
import unittest

from pontius.factorized_tie_aware_affine import (
    FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE,
    V2_SINGLE_TAPE,
    build_factorized_tie_aware_affine_section,
)
from pontius.tie_semantics_conformance import (
    FUTURE_CROSSING_SEAM,
    HIGH_CARDINALITY_FACE,
    PARALLEL_SOURCE_TIE,
    POSITIVE_MEASURE_TIE,
    REPEATED_ACTOR_IDENTITY,
    SEPARATING_SOURCE_TIE,
    TIE_SEMANTICS_CONSUMERS,
)
from pontius.tie_semantics_conformance_v2 import (
    FAN_FACE_SLOPE_SEAM,
    MAXIMUM_EPIGRAPH_ORIENTATION,
    SINGLETON_V2_DISPATCH,
    TIE_SEMANTICS_CONSUMERS_V2,
    validate_tie_semantics_conformance_v2,
)
from tests.test_exact_directional_face_oracle import (
    _ChainGame,
    _RepeatedSlopeGame,
    _chain_policy,
)
from tests.test_exact_tie_aware_affine_envelope import (
    _CrossingGame,
    _policies,
)


def _repeated_policies() -> tuple[
    dict[str, dict[str, Fraction]],
    dict[str, dict[str, Fraction]],
]:
    source = {
        "repeated-slope-p0": {
            "left": Fraction(1, 2),
            "right": Fraction(1, 2),
        },
        "repeated-slope-root": {
            "stop": Fraction(1, 2),
            "go": Fraction(1, 2),
        },
        "repeated-slope-child": {
            "first": Fraction(1, 2),
            "second": Fraction(1, 2),
        },
    }
    endpoint = {
        **source,
        "repeated-slope-p0": {
            "left": Fraction(3, 4),
            "right": Fraction(1, 4),
        },
    }
    return source, endpoint


class TieSemanticsConformanceV2Tests(unittest.TestCase):
    def test_factorized_consumer_passes_every_registered_control(self) -> None:
        # The source-sealed v1 conformance test remains the executable owner of
        # every inherited observation.  V2 inherits those exact obligations and
        # executes the complete new consumer matrix here.
        observed = {
            name: set(specification.required_controls)
            for name, specification in TIE_SEMANTICS_CONSUMERS.items()
        }

        source, endpoint = _policies()
        crossing = build_factorized_tie_aware_affine_section(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
            selector_margin_allowance=0.0,
        )
        self.assertEqual(crossing.mode, V2_SINGLE_TAPE)
        self.assertEqual(crossing.section.crossing_scales, (Fraction(1, 2),))
        boundary = next(
            sample
            for sample in crossing.section.samples
            if sample.sample_kind == "fan_boundary"
            and sample.scale == Fraction(1, 2)
        )
        self.assertLess(
            boundary.face.minimum_gain_slope,
            boundary.face.maximum_gain_slope,
        )
        self.assertEqual(
            crossing.epigraph_orientation,
            "z_greater_than_or_equal_to_every_row",
        )

        parallel = build_factorized_tie_aware_affine_section(
            _CrossingGame(tied=True),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
            selector_margin_allowance=0.0,
        )
        self.assertEqual(parallel.mode, FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE)
        self.assertEqual(parallel.source_face.total_function_cardinality, 2)
        self.assertEqual(
            parallel.source_face.minimum_gain_slope,
            parallel.source_face.maximum_gain_slope,
        )
        self.assertEqual(parallel.section.fan.total_tie_unresolved_measure, 1)

        repeated_source, repeated_endpoint = _repeated_policies()
        separating = build_factorized_tie_aware_affine_section(
            _RepeatedSlopeGame(),
            repeated_source,
            repeated_endpoint,
            acting_player=0,
            target_player=1,
            selector_margin_allowance=0.0,
        )
        self.assertEqual(separating.mode, FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE)
        self.assertLess(
            separating.source_face.minimum_gain_slope,
            separating.source_face.maximum_gain_slope,
        )
        self.assertEqual(separating.source_face.total_function_cardinality, 4)
        self.assertEqual(separating.source_face.reachable_support_cardinality, 3)

        chain_policy = _chain_policy(10)
        high = build_factorized_tie_aware_affine_section(
            _ChainGame(10),
            chain_policy,
            chain_policy,
            acting_player=0,
            target_player=0,
            selector_margin_allowance=0.0,
        )
        self.assertEqual(high.source_face.total_function_cardinality, 1024)
        self.assertEqual(high.work.materialized_response_tapes, 0)

        observed["factorized_tie_aware_affine"] = {
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
        validate_tie_semantics_conformance_v2(observed)

    def test_registry_is_a_strict_versioned_extension(self) -> None:
        self.assertEqual(
            set(TIE_SEMANTICS_CONSUMERS_V2) - set(TIE_SEMANTICS_CONSUMERS),
            {"factorized_tie_aware_affine"},
        )
        observed = {
            name: set(specification.required_controls)
            for name, specification in TIE_SEMANTICS_CONSUMERS_V2.items()
        }
        observed["factorized_tie_aware_affine"].remove(FAN_FACE_SLOPE_SEAM)
        with self.assertRaisesRegex(ValueError, "lacks controls"):
            validate_tie_semantics_conformance_v2(observed)

        complete = {
            name: set(specification.required_controls)
            for name, specification in TIE_SEMANTICS_CONSUMERS_V2.items()
        }
        complete["unregistered"] = set()
        with self.assertRaisesRegex(ValueError, "registry and observations differ"):
            validate_tie_semantics_conformance_v2(complete)


if __name__ == "__main__":
    unittest.main()
