from __future__ import annotations

import unittest

from pontius.continuation_public_tree_tensor import (
    ContinuationPublicTreeTensorEvaluator,
)
from pontius.evaluation import (
    best_response,
    collect_information_sets,
    evaluate_profile,
    expected_utilities,
)
from pontius.kuhn import KuhnPoker
from pontius.one_seat_convex_generation import (
    _deterministic_policy,
    _merge_policy,
    _sequence_axis,
    compiled_layout_path_single_visit_report,
    open_axis_payoff_coefficients,
    path_single_visit_report,
    require_behavioral_affine_shortcut,
    require_compiled_behavioral_affine_shortcut,
    retreat_one_seat_policy,
    solve_one_seat_complete_normal_form_teacher,
    solve_one_seat_with_row_generation,
)
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.river import parse_cards
from pontius.river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem


def _layout_game() -> MultiwayRiverHoldem:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    deal = MultiwayRiverDeal(
        (
            parse_cards("As", "Ad"),
            parse_cards("Ks", "Kd"),
            parse_cards("Ts", "Td"),
        )
    )
    return MultiwayRiverHoldem.from_joint_weights(
        board=board,
        pot=12.0,
        stacks=(30.0, 30.0, 30.0),
        bet_size=3.0,
        joint_weights={deal: 1.0},
    )


class OneSeatConvexGenerationTests(unittest.TestCase):
    def test_open_axis_coefficients_match_repeated_action_game(self) -> None:
        game = KuhnPoker(2)
        blueprint = {}
        axis = _sequence_axis(game, 0)
        realization = axis.realization_from_policy(blueprint)
        exact = expected_utilities(game, blueprint)
        for payoff_player in range(game.num_players):
            with self.subTest(payoff_player=payoff_player):
                affine = open_axis_payoff_coefficients(
                    game,
                    blueprint,
                    acting_player=0,
                    payoff_player=payoff_player,
                )
                self.assertAlmostEqual(affine.value(realization), exact[payoff_player])

        _, selected = best_response(game, blueprint, 1)
        response = _deterministic_policy(
            collect_information_sets(game, 1),
            selected,
        )
        fixed = _merge_policy(blueprint, response)
        affine = open_axis_payoff_coefficients(
            game,
            fixed,
            acting_player=0,
            payoff_player=1,
        )
        self.assertAlmostEqual(
            affine.value(realization),
            expected_utilities(game, fixed)[1],
        )

    def test_sequence_form_generation_matches_independent_complete_teacher(self) -> None:
        game = KuhnPoker(2)
        generated = solve_one_seat_with_row_generation(
            game,
            {},
            acting_player=0,
            guard=0.25,
        )
        teacher = solve_one_seat_complete_normal_form_teacher(
            game,
            {},
            acting_player=0,
            guard=0.25,
        )

        self.assertTrue(generated.converged)
        self.assertAlmostEqual(generated.lower_bound, teacher.objective)
        self.assertAlmostEqual(generated.upper_bound, teacher.objective)
        self.assertLessEqual(generated.optimality_gap, 1e-10)
        self.assertEqual(teacher.acting_pure_plans, 64)
        self.assertEqual(teacher.response_pure_plans, (0, 64))
        self.assertLess(generated.response_rows_by_player[1], 64)
        lower_bounds = [update.master_lower_bound for update in generated.iterations]
        upper_bounds = [update.incumbent_upper_bound for update in generated.iterations]
        self.assertEqual(lower_bounds, sorted(lower_bounds))
        self.assertEqual(upper_bounds, sorted(upper_bounds, reverse=True))
        for update in generated.iterations:
            self.assertAlmostEqual(
                update.optimality_gap,
                update.incumbent_upper_bound - update.master_lower_bound,
            )

        baseline = evaluate_profile(game, {})
        endpoint = evaluate_profile(game, generated.policy)
        factor = 0.8
        retreated_policy = retreat_one_seat_policy(
            game,
            {},
            generated.policy,
            acting_player=0,
            factor=factor,
        )
        retreated = evaluate_profile(game, retreated_policy)
        for mixed_gain, source_gain, endpoint_gain in zip(
            retreated.deviation_gains,
            baseline.deviation_gains,
            endpoint.deviation_gains,
            strict=True,
        ):
            self.assertLessEqual(
                mixed_gain,
                (1.0 - factor) * source_gain + factor * endpoint_gain + 1e-10,
            )
        self.assertGreaterEqual(
            baseline.nash_conv - retreated.nash_conv,
            factor * (baseline.nash_conv - endpoint.nash_conv) - 1e-10,
        )

    def test_truncation_preserves_safe_incumbent_and_valid_gap(self) -> None:
        result = solve_one_seat_with_row_generation(
            KuhnPoker(2),
            {},
            acting_player=0,
            guard=0.25,
            max_iterations=1,
        )

        self.assertFalse(result.converged)
        self.assertGreater(result.optimality_gap, 0.0)
        self.assertAlmostEqual(
            result.optimality_gap,
            result.upper_bound - result.lower_bound,
        )
        evaluation = evaluate_profile(KuhnPoker(2), result.policy)
        self.assertAlmostEqual(evaluation.nash_conv, result.upper_bound)
        self.assertTrue(
            all(
                gain <= cap + 1e-10
                for gain, cap in zip(
                    evaluation.deviation_gains,
                    result.caps,
                    strict=True,
                )
            )
        )

    def test_one_iteration_adds_all_violated_opponent_rows(self) -> None:
        result = solve_one_seat_with_row_generation(
            KuhnPoker(3),
            {},
            acting_player=0,
            guard=1.0,
            max_iterations=1,
        )

        self.assertEqual(result.iterations[0].added_targets, (1, 2))
        self.assertEqual(result.iterations[0].response_rows_added, 2)

    def test_behavioral_shortcut_rejects_repeated_actor_path(self) -> None:
        report = path_single_visit_report(KuhnPoker(2))
        self.assertFalse(report.passed)
        self.assertEqual(report.repeated_player, 0)
        with self.assertRaisesRegex(ValueError, "at most one decision"):
            require_behavioral_affine_shortcut(KuhnPoker(2))

    def test_compiled_layout_gate_rejects_full_and_accepts_post_bet_tree(self) -> None:
        game = _layout_game()
        full = PublicTreeTensorEvaluator(game)
        continuation = ContinuationPublicTreeTensorEvaluator(
            game,
            public_prefix=((0, "check"), (1, "bet")),
        )

        self.assertFalse(compiled_layout_path_single_visit_report(full).passed)
        self.assertTrue(compiled_layout_path_single_visit_report(continuation).passed)
        with self.assertRaisesRegex(ValueError, "compiled public path"):
            require_compiled_behavioral_affine_shortcut(full)
        require_compiled_behavioral_affine_shortcut(continuation)

    def test_invalid_controls_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "guard"):
            solve_one_seat_with_row_generation(
                KuhnPoker(2),
                {},
                acting_player=0,
                guard=-1.0,
            )
        with self.assertRaisesRegex(ValueError, "max_iterations"):
            solve_one_seat_with_row_generation(
                KuhnPoker(2),
                {},
                acting_player=0,
                guard=0.0,
                max_iterations=0,
            )


if __name__ == "__main__":
    unittest.main()
    compiled_layout_path_single_visit_report,
