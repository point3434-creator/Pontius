from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import unittest

from pontius.exact_directional_face_oracle import (
    compose_exact_directional_face_fan_section,
    exact_directional_best_response_face,
)
from pontius.exact_selector_fan import map_exact_selector_fan_section
from pontius.exact_tie_aware_affine_envelope import (
    build_exact_tie_aware_affine_section,
)
from pontius.selector_window import (
    FixedResponseSelectorScores,
    FixedSelectorInformationSetScores,
    fixed_response_selector_scores,
)
from pontius.selector_window_v2 import fail_closed_affine_selector_window
from pontius.tie_aware_affine_adapter import choose_tie_aware_affine_mode
from pontius.tie_semantics_conformance import (
    FUTURE_CROSSING_SEAM,
    HIGH_CARDINALITY_FACE,
    PARALLEL_SOURCE_TIE,
    POSITIVE_MEASURE_TIE,
    REPEATED_ACTOR_IDENTITY,
    SEPARATING_SOURCE_TIE,
    TIE_SEMANTICS_CONSUMERS,
    validate_tie_semantics_conformance,
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


def _scores(selected: float, competitor: float) -> FixedResponseSelectorScores:
    return FixedResponseSelectorScores(
        player=0,
        value=selected,
        information_sets=(
            FixedSelectorInformationSetScores(
                key="shared-tie-conformance",
                actions=("selected", "competitor"),
                player_depth=0,
                action_values=(
                    ("selected", selected),
                    ("competitor", competitor),
                ),
                selected_action="selected",
            ),
        ),
    )


class TieSemanticsConformanceTests(unittest.TestCase):
    def test_every_registered_consumer_passes_its_tie_controls(self) -> None:
        observed = {name: set() for name in TIE_SEMANTICS_CONSUMERS}

        parallel = fail_closed_affine_selector_window(
            _scores(0.0, 0.0),
            _scores(0.0, 0.0),
            selector_margin_allowance=0.0,
        )
        separating = fail_closed_affine_selector_window(
            _scores(0.0, 0.0),
            _scores(1.0, 0.0),
            selector_margin_allowance=0.0,
        )
        self.assertEqual(parallel.scale_limit, 0.0)
        self.assertEqual(separating.scale_limit, 0.0)
        observed["selector_window_v2"].update(
            {PARALLEL_SOURCE_TIE, SEPARATING_SOURCE_TIE}
        )

        source, endpoint = _policies()
        fan_crossing = map_exact_selector_fan_section(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        fan_tied = map_exact_selector_fan_section(
            _CrossingGame(tied=True),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        self.assertIn(Fraction(1, 2), fan_crossing.total_tie_points)
        self.assertEqual(fan_tied.total_tie_unresolved_measure, 1)
        observed["exact_selector_fan"].update(
            {FUTURE_CROSSING_SEAM, POSITIVE_MEASURE_TIE}
        )

        envelope_crossing = build_exact_tie_aware_affine_section(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        envelope_tied = build_exact_tie_aware_affine_section(
            _CrossingGame(tied=True),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        boundary = next(
            sample
            for sample in envelope_crossing.samples
            if sample.scale == Fraction(1, 2)
        )
        self.assertEqual(len(boundary.active_tapes), 2)
        self.assertEqual(len(envelope_tied.source_active_tapes), 2)
        observed["exact_tie_aware_affine_envelope"].update(
            {FUTURE_CROSSING_SEAM, POSITIVE_MEASURE_TIE}
        )

        source_float = {
            key: {action: float(value) for action, value in row.items()}
            for key, row in source.items()
        }
        endpoint_float = {
            key: {action: float(value) for action, value in row.items()}
            for key, row in endpoint.items()
        }
        score_endpoints = {
            tape: (
                fixed_response_selector_scores(
                    _CrossingGame(tied=True),
                    source_float,
                    1,
                    dict(tape),
                ),
                fixed_response_selector_scores(
                    _CrossingGame(tied=True),
                    endpoint_float,
                    1,
                    dict(tape),
                ),
            )
            for tape in envelope_tied.source_active_tapes
        }
        adapter = choose_tie_aware_affine_mode(
            envelope_tied,
            score_endpoints,
            selector_margin_allowance=0.0,
        )
        self.assertEqual(adapter.mode, "tie_aware_maximum_envelope")
        self.assertTrue(
            all(window.scale_limit == 0.0 for _, window in adapter.v2_windows)
        )
        observed["tie_aware_affine_adapter"].update(
            {PARALLEL_SOURCE_TIE, POSITIVE_MEASURE_TIE}
        )

        direct_tied = exact_directional_best_response_face(
            _CrossingGame(tied=True),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
            scale=Fraction(0),
        )
        direct_crossing = exact_directional_best_response_face(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
            scale=Fraction(1, 2),
        )
        chain_policy = _chain_policy(10)
        high_cardinality = exact_directional_best_response_face(
            _ChainGame(10),
            chain_policy,
            chain_policy,
            acting_player=0,
            target_player=0,
            scale=Fraction(0),
        )
        repeated_source = {
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
        repeated_endpoint = {
            **repeated_source,
            "repeated-slope-p0": {
                "left": Fraction(3, 4),
                "right": Fraction(1, 4),
            },
        }
        repeated = exact_directional_best_response_face(
            _RepeatedSlopeGame(),
            repeated_source,
            repeated_endpoint,
            acting_player=0,
            target_player=1,
            scale=Fraction(0),
        )
        self.assertEqual(direct_tied.total_function_cardinality, 2)
        self.assertLess(
            direct_crossing.minimum_gain_slope,
            direct_crossing.maximum_gain_slope,
        )
        self.assertEqual(high_cardinality.total_function_cardinality, 1024)
        self.assertEqual(high_cardinality.work.materialized_response_tapes, 0)
        self.assertEqual(repeated.total_function_cardinality, 4)
        self.assertEqual(repeated.reachable_support_cardinality, 3)
        observed["exact_directional_face_oracle"].update(
            {
                POSITIVE_MEASURE_TIE,
                FUTURE_CROSSING_SEAM,
                HIGH_CARDINALITY_FACE,
                REPEATED_ACTOR_IDENTITY,
            }
        )

        composed_crossing = compose_exact_directional_face_fan_section(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        composed_tied = compose_exact_directional_face_fan_section(
            _CrossingGame(tied=True),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        self.assertEqual(composed_crossing.crossing_scales, (Fraction(1, 2),))
        self.assertEqual(composed_tied.fan.total_tie_unresolved_measure, 1)
        observed["compose_exact_directional_face_fan_section"].update(
            {FUTURE_CROSSING_SEAM, POSITIVE_MEASURE_TIE}
        )

        validate_tie_semantics_conformance(observed)

    def test_missing_consumer_or_control_fails_closed(self) -> None:
        complete = {
            name: set(specification.required_controls)
            for name, specification in TIE_SEMANTICS_CONSUMERS.items()
        }
        missing_consumer = deepcopy(complete)
        missing_consumer.pop("selector_window_v2")
        with self.assertRaises(ValueError):
            validate_tie_semantics_conformance(missing_consumer)
        missing_control = deepcopy(complete)
        missing_control["exact_directional_face_oracle"].remove(
            HIGH_CARDINALITY_FACE
        )
        with self.assertRaises(ValueError):
            validate_tie_semantics_conformance(missing_control)


if __name__ == "__main__":
    unittest.main()
