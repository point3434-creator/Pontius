from __future__ import annotations

import math
import unittest

from pontius.cfr import TabularCFR
from pontius.dependency_tape import CompiledPolicyDependencyTape
from pontius.evaluation import (
    EvaluationResult,
    best_response,
    best_response_enumerated,
    collect_information_sets,
    evaluate_profile,
)
from pontius.river import CALL, CHECK, FOLD, RiverDeal, RiverHoldem, make_hole, parse_cards
from pontius.river_context import generate_river_contexts
from pontius.river_incremental import make_support_swap_perturbation
from pontius.river_multi_size import (
    BetAction,
    MultiSizeRiverHoldem,
    RaiseToAction,
)
from pontius.river_multi_size_audit import audit_multi_size_payoffs


def _board() -> tuple[int, ...]:
    return parse_cards("2c", "7d", "9h", "Js", "Qc")


def _winning_deal() -> RiverDeal:
    return RiverDeal(make_hole("Ts", "Ks"), make_hole("Ah", "3h"))


def _game(
    *,
    deals: dict[RiverDeal, float] | None = None,
    bet_sizes: tuple[float, ...] = (2.5, 5.0, 7.5),
    raise_to_sizes: tuple[float, ...] = (15.0, 20.0),
) -> MultiSizeRiverHoldem:
    return MultiSizeRiverHoldem.from_joint_weights(
        board=_board(),
        pot=10.0,
        stacks=(20.0, 20.0),
        bet_sizes=bet_sizes,
        raise_to_sizes=raise_to_sizes,
        joint_weights=deals or {_winning_deal(): 1.0},
    )


def _assert_evaluation_equal(
    test: unittest.TestCase,
    actual: EvaluationResult,
    expected: EvaluationResult,
) -> None:
    for left_values, right_values in (
        (actual.utilities, expected.utilities),
        (actual.best_response_values, expected.best_response_values),
        (actual.deviation_gains, expected.deviation_gains),
    ):
        for left, right in zip(left_values, right_values, strict=True):
            test.assertAlmostEqual(left, right, places=10)
    test.assertAlmostEqual(actual.nash_conv, expected.nash_conv, places=10)
    assert actual.exploitability is not None
    assert expected.exploitability is not None
    test.assertAlmostEqual(actual.exploitability, expected.exploitability, places=10)


class MultiSizeRiverTests(unittest.TestCase):
    def test_three_bets_two_raises_have_exact_zero_sum_payoffs(self) -> None:
        game = _game()
        deal = _winning_deal()
        dealt = game.initial_state().apply_action(deal)
        small, medium, large = game.bet_actions
        first_raise, second_raise = game.raise_actions

        self.assertEqual(dealt.legal_actions(), (CHECK, small, medium, large))
        self.assertEqual(dealt.apply_action(CHECK).returns(), (5.0, -5.0))

        facing_small = dealt.apply_action(small)
        self.assertEqual(
            facing_small.legal_actions(),
            (FOLD, CALL, first_raise, second_raise),
        )
        self.assertEqual(facing_small.apply_action(FOLD).returns(), (5.0, -5.0))
        self.assertEqual(facing_small.apply_action(CALL).returns(), (7.5, -7.5))
        self.assertEqual(
            facing_small.apply_action(second_raise).apply_action(FOLD).returns(),
            (-7.5, 7.5),
        )
        self.assertEqual(
            facing_small.apply_action(second_raise).apply_action(CALL).returns(),
            (25.0, -25.0),
        )

        facing_large = dealt.apply_action(large)
        self.assertEqual(
            facing_large.apply_action(first_raise).apply_action(FOLD).returns(),
            (-12.5, 12.5),
        )
        self.assertEqual(
            facing_large.apply_action(first_raise).apply_action(CALL).returns(),
            (20.0, -20.0),
        )
        self.assertEqual(game.payoff_span, 50.0)

        audit = audit_multi_size_payoffs(game)
        self.assertTrue(audit.passed)
        self.assertEqual(audit.deals, 1)
        self.assertEqual(audit.terminal_histories, 19)
        self.assertEqual(audit.maximum_absolute_error, 0.0)

    def test_minimum_raise_filter_is_specific_to_the_opening_size(self) -> None:
        game = _game(raise_to_sizes=(6.0, 10.0, 15.0))
        dealt = game.initial_state().apply_action(_winning_deal())
        small, medium, large = game.bet_actions
        raise6, raise10, raise15 = game.raise_actions

        self.assertEqual(
            dealt.apply_action(small).legal_actions(),
            (FOLD, CALL, raise6, raise10, raise15),
        )
        self.assertEqual(
            dealt.apply_action(medium).legal_actions(),
            (FOLD, CALL, raise10, raise15),
        )
        self.assertEqual(
            dealt.apply_action(large).legal_actions(),
            (FOLD, CALL, raise15),
        )
        with self.assertRaisesRegex(ValueError, "illegal action"):
            dealt.apply_action(large).apply_action(raise10)
        with self.assertRaisesRegex(ValueError, "unknown opening bet"):
            game.legal_raises(BetAction(3.0))

    def test_information_keys_hide_opponent_and_remember_exact_sizes(self) -> None:
        hand0 = make_hole("Ts", "Ks")
        first = RiverDeal(hand0, make_hole("Ah", "3h"))
        second = RiverDeal(hand0, make_hole("Ac", "Ad"))
        game = _game(deals={first: 0.5, second: 0.5})
        small, _, large = game.bet_actions
        first_raise, second_raise = game.raise_actions

        root_keys = {
            game.initial_state().apply_action(deal).information_state_key(0)
            for deal in (first, second)
        }
        self.assertEqual(len(root_keys), 1)

        small_key = (
            game.initial_state()
            .apply_action(first)
            .apply_action(small)
            .information_state_key(1)
        )
        large_key = (
            game.initial_state()
            .apply_action(first)
            .apply_action(large)
            .information_state_key(1)
        )
        first_raise_key = (
            game.initial_state()
            .apply_action(first)
            .apply_action(small)
            .apply_action(first_raise)
            .information_state_key(0)
        )
        second_raise_key = (
            game.initial_state()
            .apply_action(second)
            .apply_action(small)
            .apply_action(second_raise)
            .information_state_key(0)
        )

        self.assertNotEqual(small_key, large_key)
        self.assertNotEqual(first_raise_key, second_raise_key)
        self.assertIn(str(small), first_raise_key)
        self.assertIn(str(first_raise), first_raise_key)
        self.assertNotIn("Ah3h", first_raise_key)
        self.assertNotIn("AcAd", second_raise_key)

    def test_structure_provenance_conversion_and_range_metrics_are_separate(self) -> None:
        first = _winning_deal()
        second = RiverDeal(make_hole("4s", "5s"), make_hole("Ah", "3h"))
        source = _game(deals={first: 0.75, second: 0.25})
        target = source.with_joint_weights({first: 0.5, second: 0.5})
        different = _game(
            deals={first: 0.75, second: 0.25},
            bet_sizes=(2.5, 5.0, 8.0),
        )

        self.assertEqual(source.structural_digest, target.structural_digest)
        self.assertNotEqual(source.provenance_digest, target.provenance_digest)
        self.assertNotEqual(source.structural_digest, different.structural_digest)
        self.assertAlmostEqual(source.total_variation(target), 0.25)
        self.assertAlmostEqual(source.fixed_policy_value_bound(target), 12.5)
        source_key = (
            source.initial_state().apply_action(first).information_state_key(0)
        )
        target_key = (
            target.initial_state().apply_action(first).information_state_key(0)
        )
        self.assertEqual(source_key, target_key)

        narrow = RiverHoldem.from_joint_weights(
            board=source.board,
            pot=source.pot,
            stacks=source.stacks,
            bet_size=5.0,
            joint_weights=source.joint_distribution(),
        )
        converted = MultiSizeRiverHoldem.from_river_game(
            narrow,
            bet_sizes=source.bet_sizes,
            raise_to_sizes=source.raise_to_sizes,
        )
        self.assertEqual(converted.joint_distribution(), source.joint_distribution())
        self.assertEqual(converted.structural_digest, source.structural_digest)

    def test_dynamic_best_response_matches_exhaustive_pure_enumeration(self) -> None:
        game = _game()
        policy = {}
        for player in range(2):
            dynamic_value, dynamic_actions = best_response(game, policy, player)
            enumerated_value, enumerated_actions = best_response_enumerated(
                game,
                policy,
                player,
            )
            self.assertAlmostEqual(dynamic_value, enumerated_value)
            if player == 1:
                self.assertEqual(dynamic_actions, enumerated_actions)
                continue
            root_key = (
                game.initial_state()
                .apply_action(_winning_deal())
                .information_state_key(0)
            )
            selected_root = dynamic_actions[root_key]
            self.assertEqual(selected_root, enumerated_actions[root_key])
            for key, action in dynamic_actions.items():
                if key == root_key or str(selected_root) in key:
                    self.assertEqual(action, enumerated_actions[key])

        self.assertEqual(len(collect_information_sets(game, 0)), 7)
        self.assertEqual(len(collect_information_sets(game, 1)), 3)

    def test_unchanged_generic_tape_matches_full_wide_tree(self) -> None:
        narrow = generate_river_contexts(
            groups=1,
            seed=53,
            hands_per_player=3,
            families=("blocker_stress",),
            splits=("development", "validation", "test"),
        )[0].game
        narrow_target, metadata = make_support_swap_perturbation(narrow, player=1)
        bet_sizes = tuple(narrow.pot * fraction for fraction in (0.25, 0.5, 0.75))
        raise_sizes = tuple(narrow.pot * fraction for fraction in (1.5, 2.0))
        source = MultiSizeRiverHoldem.from_river_game(
            narrow,
            bet_sizes=bet_sizes,
            raise_to_sizes=raise_sizes,
        )
        target = MultiSizeRiverHoldem.from_river_game(
            narrow_target,
            bet_sizes=bet_sizes,
            raise_to_sizes=raise_sizes,
        )
        solver = TabularCFR(source, variant="dcfr")
        solver.run(3)
        policy = solver.average_strategy()
        tape = CompiledPolicyDependencyTape(
            source,
            policy,
            universe_games=(target,),
        )

        _assert_evaluation_equal(
            self,
            tape.source_result.evaluation,
            evaluate_profile(source, policy),
        )
        results = {
            mode: tape.recertify_game(target, mode=mode)
            for mode in ("sparse", "dense", "auto")
        }
        full = evaluate_profile(target, policy)
        exact_actions = tuple(
            best_response(target, policy, player)[1] for player in range(2)
        )
        for result in results.values():
            _assert_evaluation_equal(self, result.evaluation, full)
            for player, actions in enumerate(exact_actions):
                for key, action in actions.items():
                    self.assertEqual(result.best_response_actions[player][key], action)
        self.assertEqual(
            results["sparse"].best_response_actions,
            results["dense"].best_response_actions,
        )
        self.assertEqual(
            results["sparse"].best_response_actions,
            results["auto"].best_response_actions,
        )
        self.assertEqual(results["auto"].diagnostics.execution_mode, "sparse")
        self.assertTrue(metadata["new_private_hand_was_absent"])
        self.assertTrue(tape.topology_summary()["dependencies_are_topological"])

    def test_invalid_sizes_stacks_and_audit_inputs_are_rejected(self) -> None:
        deal = _winning_deal()
        common = {
            "board": _board(),
            "pot": 10.0,
            "stacks": (20.0, 20.0),
            "raise_to_sizes": (15.0, 20.0),
            "joint_weights": {deal: 1.0},
        }
        with self.assertRaisesRegex(ValueError, "at least one bet"):
            MultiSizeRiverHoldem.from_joint_weights(
                **common,
                bet_sizes=(),
            )
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            MultiSizeRiverHoldem.from_joint_weights(
                **common,
                bet_sizes=(5.0, 2.5),
            )
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            MultiSizeRiverHoldem.from_joint_weights(
                **{**common, "raise_to_sizes": (15.0, 15.0)},
                bet_sizes=(2.5, 5.0),
            )
        with self.assertRaisesRegex(ValueError, "legal after at least one"):
            MultiSizeRiverHoldem.from_joint_weights(
                **{**common, "raise_to_sizes": (4.0,)},
                bet_sizes=(2.5, 5.0),
            )
        with self.assertRaisesRegex(ValueError, "fit both"):
            MultiSizeRiverHoldem.from_joint_weights(
                **{**common, "stacks": (19.0, 20.0)},
                bet_sizes=(2.5, 5.0),
            )
        with self.assertRaisesRegex(ValueError, "positive finite"):
            BetAction(math.nan)
        with self.assertRaisesRegex(ValueError, "positive finite"):
            RaiseToAction(True)
        with self.assertRaisesRegex(ValueError, "tolerance"):
            audit_multi_size_payoffs(_game(), tolerance=-1.0)


if __name__ == "__main__":
    unittest.main()
