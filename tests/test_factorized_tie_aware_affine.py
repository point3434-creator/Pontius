from __future__ import annotations

import ast
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
import unittest
from unittest.mock import patch

from pontius.exact_directional_face_oracle import (
    compose_exact_directional_face_fan_section,
)
from pontius.exact_selector_fan import realization_interpolated_policy
from pontius.exact_selector_window_oracle import (
    exact_fixed_response_trace,
    exact_policy_utilities,
)
from pontius.factorized_tie_aware_affine import (
    FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE,
    FAIL_CLOSED_SINGLE_TAPE,
    V2_SINGLE_TAPE,
    build_factorized_tie_aware_affine_section,
    integrate_factorized_tie_aware_affine_section,
)
from pontius.selector_window import ConservativeSelectorWindow
from tests.test_exact_directional_face_oracle import (
    _ChainGame,
    _RepeatedSlopeGame,
    _all_response_tapes,
    _chain_policy,
)
from tests.test_exact_tie_aware_affine_envelope import (
    _CrossingGame,
    _policies,
)


ROOT = Path(__file__).resolve().parents[1]


def _zero_window() -> ConservativeSelectorWindow:
    return ConservativeSelectorWindow(
        scale_limit=0.0,
        first_switch_information_key="control",
        first_switch_source_action="first",
        first_switch_competing_action="second",
        selector_comparisons=1,
        exact_source_action_ties=0,
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


class FactorizedTieAwareAffineTests(unittest.TestCase):
    def test_future_crossing_builds_convex_exact_envelope_and_v2_dispatch(self) -> None:
        source, endpoint = _policies()
        result = build_factorized_tie_aware_affine_section(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
            selector_margin_allowance=0.0,
        )

        self.assertEqual(result.mode, V2_SINGLE_TAPE)
        self.assertEqual(result.exact_envelope_domain, (Fraction(0), Fraction(1)))
        self.assertEqual(result.certificate_identity_authority, "total_function_only")
        self.assertEqual(result.reachable_identity_role, "reporting_only")
        self.assertEqual(result.ray_authority, "exact_selector_normal_fan")
        self.assertEqual(
            result.point_authority,
            "two_pass_factorized_directional_face",
        )
        self.assertEqual(
            result.epigraph_orientation,
            "z_greater_than_or_equal_to_every_row",
        )
        self.assertEqual(
            tuple((piece.lower, piece.upper, piece.slope) for piece in result.pieces),
            (
                (Fraction(0), Fraction(1, 2), Fraction(-1, 2)),
                (Fraction(1, 2), Fraction(1), Fraction(1, 2)),
            ),
        )
        self.assertEqual(result.pieces[0].value(Fraction(1, 2)), Fraction(0))
        self.assertEqual(result.pieces[1].value(Fraction(1, 2)), Fraction(0))
        self.assertIsNotNone(result.single_tape_window)
        assert result.single_tape_window is not None
        self.assertEqual(result.single_tape_window.scale_limit, 0.5)
        self.assertEqual(result.work.selector_window_v2_calls, 1)
        self.assertEqual(result.work.float_selector_score_calls, 2)
        self.assertEqual(result.work.materialized_response_tapes, 0)

    def test_positive_measure_source_tie_uses_face_without_single_tape_work(self) -> None:
        source, endpoint = _policies()
        with patch(
            "pontius.factorized_tie_aware_affine.fixed_response_selector_scores",
            side_effect=AssertionError("source tie must not score an elected tape"),
        ), patch(
            "pontius.factorized_tie_aware_affine.fail_closed_affine_selector_window",
            side_effect=AssertionError("source tie must not invoke selector-window v2"),
        ):
            result = build_factorized_tie_aware_affine_section(
                _CrossingGame(tied=True),
                source,
                endpoint,
                acting_player=0,
                target_player=1,
                selector_margin_allowance=0.0,
            )

        self.assertEqual(result.mode, FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE)
        self.assertEqual(result.source_face.total_function_cardinality, 2)
        self.assertEqual(result.source_face.reachable_support_cardinality, 2)
        self.assertIsNone(result.single_tape_window)
        self.assertEqual(len(result.pieces), 1)
        self.assertEqual(result.pieces[0].total_state, "tie_unresolved")
        self.assertEqual(result.pieces[0].slope, 0)
        self.assertEqual(result.work.selector_window_v2_calls, 0)
        self.assertEqual(result.work.float_selector_score_calls, 0)
        self.assertEqual(result.work.materialized_response_tapes, 0)

    def test_small_envelope_matches_exhaustive_pure_response_maximum(self) -> None:
        source, endpoint = _policies()
        game = _CrossingGame()
        result = build_factorized_tie_aware_affine_section(
            game,
            source,
            endpoint,
            acting_player=0,
            target_player=1,
            selector_margin_allowance=0.0,
        )
        tapes = _all_response_tapes(game, source, 1)
        for scale in (
            Fraction(0),
            Fraction(1, 4),
            Fraction(1, 2),
            Fraction(3, 4),
            Fraction(1),
        ):
            with self.subTest(scale=scale):
                policy = realization_interpolated_policy(
                    game,
                    source,
                    endpoint,
                    acting_player=0,
                    scale=scale,
                )
                profile = exact_policy_utilities(game, policy)[1]
                exhaustive = max(
                    exact_fixed_response_trace(game, policy, 1, dict(tape)).value
                    - profile
                    for tape in tapes
                )
                envelope = max(
                    row.value(scale) for row in result.section.cell_rows
                )
                self.assertEqual(envelope, exhaustive)

    def test_high_cardinality_face_is_integrated_without_product_materialization(self) -> None:
        policy = _chain_policy(12)
        result = build_factorized_tie_aware_affine_section(
            _ChainGame(12),
            policy,
            policy,
            acting_player=0,
            target_player=0,
            selector_margin_allowance=0.0,
        )

        self.assertEqual(result.mode, FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE)
        self.assertEqual(result.source_face.total_function_cardinality, 4096)
        self.assertEqual(result.source_face.reachable_support_cardinality, 13)
        self.assertGreater(result.source_face.total_function_cardinality, 256)
        self.assertEqual(result.source_face.work.materialized_response_tapes, 0)
        self.assertEqual(result.work.materialized_response_tapes, 0)
        self.assertEqual(len(result.pieces), 1)

    def test_repeated_actor_keeps_total_and_reachable_cardinalities_distinct(self) -> None:
        source, endpoint = _repeated_policies()
        result = build_factorized_tie_aware_affine_section(
            _RepeatedSlopeGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
            selector_margin_allowance=0.0,
        )

        self.assertEqual(result.mode, FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE)
        self.assertEqual(result.source_face.total_function_cardinality, 4)
        self.assertEqual(result.source_face.reachable_support_cardinality, 3)
        self.assertEqual(result.certificate_identity_authority, "total_function_only")
        self.assertEqual(result.reachable_identity_role, "reporting_only")

    def test_singleton_zero_window_has_a_distinct_fail_closed_mode(self) -> None:
        source, endpoint = _policies()
        section = compose_exact_directional_face_fan_section(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        result = integrate_factorized_tie_aware_affine_section(
            section,
            single_tape_window=_zero_window(),
            selector_window_v2_calls=1,
            float_selector_score_calls=2,
        )
        self.assertEqual(result.mode, FAIL_CLOSED_SINGLE_TAPE)

    def test_exact_source_tie_rejects_any_v2_window_or_call_ledger(self) -> None:
        source, endpoint = _policies()
        section = compose_exact_directional_face_fan_section(
            _CrossingGame(tied=True),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        with self.assertRaisesRegex(ArithmeticError, "source tie received"):
            integrate_factorized_tie_aware_affine_section(
                section,
                single_tape_window=_zero_window(),
                selector_window_v2_calls=1,
                float_selector_score_calls=2,
            )

    def test_singleton_rejects_v2_window_outside_exact_fan_cell(self) -> None:
        source, endpoint = _policies()
        section = compose_exact_directional_face_fan_section(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        too_wide = replace(_zero_window(), scale_limit=0.75)
        with self.assertRaisesRegex(ArithmeticError, "exceeds exact source cell"):
            integrate_factorized_tie_aware_affine_section(
                section,
                single_tape_window=too_wide,
                selector_window_v2_calls=1,
                float_selector_score_calls=2,
            )

    def test_mutated_factor_cardinality_fails_closed(self) -> None:
        source, endpoint = _policies()
        section = compose_exact_directional_face_fan_section(
            _CrossingGame(tied=True),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        sample = section.samples[0]
        mutated_face = replace(
            sample.face,
            total_function_cardinality=sample.face.total_function_cardinality + 1,
        )
        mutated = replace(
            section,
            samples=(replace(sample, face=mutated_face), *section.samples[1:]),
        )
        with self.assertRaisesRegex(ArithmeticError, "total cardinality"):
            integrate_factorized_tie_aware_affine_section(
                mutated,
                single_tape_window=None,
                selector_window_v2_calls=0,
                float_selector_score_calls=0,
            )

    def test_mutated_interior_face_slope_fails_at_fan_face_seam(self) -> None:
        source, endpoint = _policies()
        section = compose_exact_directional_face_fan_section(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        samples = []
        for sample in section.samples:
            if sample.sample_kind == "fan_boundary" and sample.scale == Fraction(1, 2):
                face = replace(
                    sample.face,
                    maximum_response_slope=sample.face.maximum_response_slope + 1,
                    maximum_gain_slope=sample.face.maximum_gain_slope + 1,
                )
                sample = replace(sample, face=face)
            samples.append(sample)
        mutated = replace(section, samples=tuple(samples))
        with self.assertRaisesRegex(ArithmeticError, "slope seam"):
            integrate_factorized_tie_aware_affine_section(
                mutated,
                single_tape_window=_zero_window(),
                selector_window_v2_calls=1,
                float_selector_score_calls=2,
            )

    def test_mutated_row_cannot_reverse_the_maximum_epigraph(self) -> None:
        source, endpoint = _policies()
        section = compose_exact_directional_face_fan_section(
            _CrossingGame(),
            source,
            endpoint,
            acting_player=0,
            target_player=1,
        )
        first = section.cell_rows[0]
        mutated = replace(
            section,
            cell_rows=(replace(first, intercept=first.intercept + 1), *section.cell_rows[1:]),
        )
        with self.assertRaisesRegex(ArithmeticError, "maximum envelope"):
            integrate_factorized_tie_aware_affine_section(
                mutated,
                single_tape_window=_zero_window(),
                selector_window_v2_calls=1,
                float_selector_score_calls=2,
            )

    def test_source_has_no_cartesian_enumerator_or_closed_adapter_dependency(self) -> None:
        path = ROOT / "src" / "pontius" / "factorized_tie_aware_affine.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("product", imports | calls)
        self.assertNotIn("exact_tie_aware_affine_envelope", imports)
        self.assertNotIn("tie_aware_affine_adapter", imports)
        self.assertNotIn("enumerate_exact_local_maximizer_tapes", calls)


if __name__ == "__main__":
    unittest.main()
