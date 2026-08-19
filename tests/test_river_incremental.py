from __future__ import annotations

import unittest

from pontius.cfr import TabularCFR
from pontius.evaluation import EvaluationResult, evaluate_profile
from pontius.river import RiverDeal, RiverHoldem, make_hole, parse_cards
from pontius.river_context import CONTEXT_FAMILIES, generate_river_contexts
from pontius.river_incremental import (
    RiverPolicyEvaluationCache,
    RiverRangeDelta,
    make_support_swap_perturbation,
)
from pontius.river_range_reuse import make_blocker_perturbation


def _assert_evaluations_equal(
    test: unittest.TestCase,
    actual: EvaluationResult,
    expected: EvaluationResult,
) -> None:
    for actual_values, expected_values in (
        (actual.utilities, expected.utilities),
        (actual.best_response_values, expected.best_response_values),
        (actual.deviation_gains, expected.deviation_gains),
    ):
        for actual_value, expected_value in zip(
            actual_values, expected_values, strict=True
        ):
            test.assertAlmostEqual(actual_value, expected_value, places=10)
    test.assertAlmostEqual(actual.nash_conv, expected.nash_conv, places=10)
    test.assertIsNotNone(actual.exploitability)
    test.assertIsNotNone(expected.exploitability)
    test.assertAlmostEqual(
        actual.exploitability or 0.0,
        expected.exploitability or 0.0,
        places=10,
    )


def _support_change_pair(*, raise_to: float | None) -> tuple[RiverHoldem, RiverHoldem]:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    common = RiverDeal(make_hole("Ac", "Ad"), make_hole("Kh", "Kd"))
    removed = RiverDeal(make_hole("Ts", "Ks"), make_hole("Ah", "3h"))
    added = RiverDeal(make_hole("4s", "5s"), make_hole("6c", "6d"))
    arguments = {
        "board": board,
        "pot": 10.0,
        "stacks": (30.0, 30.0),
        "bet_size": 5.0,
        "raise_to": raise_to,
    }
    source = RiverHoldem.from_joint_weights(
        **arguments,
        joint_weights={common: 0.7, removed: 0.3},
    )
    target = RiverHoldem.from_joint_weights(
        **arguments,
        joint_weights={common: 0.6, added: 0.4},
    )
    return source, target


class RiverIncrementalEvaluationTests(unittest.TestCase):
    def test_compiled_source_and_identity_recertification_match_full_tree(self) -> None:
        for raise_to in (None, 15.0):
            with self.subTest(raise_to=raise_to):
                source, _ = _support_change_pair(raise_to=raise_to)
                solver = TabularCFR(source, variant="dcfr")
                for _ in range(7):
                    solver.step()
                policy = solver.average_strategy()
                cache = RiverPolicyEvaluationCache(source, policy)
                full = evaluate_profile(source, policy)

                _assert_evaluations_equal(self, cache.source_evaluation, full)
                identity = cache.recertify(source)
                _assert_evaluations_equal(self, identity.evaluation, full)
                self.assertEqual(identity.diagnostics.changed_deals, 0)
                self.assertEqual(identity.diagnostics.newly_compiled_deals, 0)

    def test_support_preserving_blocker_reweight_is_exact(self) -> None:
        context = generate_river_contexts(
            groups=1,
            seed=17,
            hands_per_player=4,
            families=("polarized",),
            splits=("development",),
            sequential_raise=True,
        )[0]
        source = context.game
        target, metadata = make_blocker_perturbation(
            source,
            player=0,
            root_tv_budget=0.01,
            maximum_donor_fraction=0.75,
        )
        solver = TabularCFR(source, variant="dcfr")
        for _ in range(11):
            solver.step()
        policy = solver.average_strategy()

        delta = RiverRangeDelta.between(source, target)
        result = RiverPolicyEvaluationCache(source, policy).recertify(target, delta)

        _assert_evaluations_equal(self, result.evaluation, evaluate_profile(target, policy))
        self.assertAlmostEqual(delta.total_variation, source.total_variation(target))
        self.assertAlmostEqual(
            result.diagnostics.total_variation,
            metadata["actual_root_joint_total_variation"],
        )
        self.assertEqual(result.diagnostics.added_deals, 0)
        self.assertEqual(result.diagnostics.removed_deals, 0)
        self.assertEqual(result.diagnostics.reweighted_deals, 2)
        self.assertEqual(result.diagnostics.newly_compiled_deals, 0)

    def test_support_addition_and_removal_compile_only_new_deal(self) -> None:
        for raise_to in (None, 15.0):
            with self.subTest(raise_to=raise_to):
                source, target = _support_change_pair(raise_to=raise_to)
                solver = TabularCFR(source, variant="dcfr")
                for _ in range(5):
                    solver.step()
                policy = solver.average_strategy()
                delta = RiverRangeDelta.between(source, target)
                result = RiverPolicyEvaluationCache(source, policy).recertify(
                    target, delta
                )

                _assert_evaluations_equal(
                    self,
                    result.evaluation,
                    evaluate_profile(target, policy),
                )
                self.assertEqual(result.diagnostics.added_deals, 1)
                self.assertEqual(result.diagnostics.removed_deals, 1)
                self.assertEqual(result.diagnostics.reweighted_deals, 1)
                self.assertEqual(result.diagnostics.newly_compiled_deals, 1)
                self.assertLessEqual(result.diagnostics.affected_player0_hands, 3)
                self.assertLessEqual(result.diagnostics.affected_player1_hands, 3)

    def test_generated_family_differential_matches_full_tree(self) -> None:
        comparisons = 0
        for sequential_raise in (False, True):
            contexts = generate_river_contexts(
                groups=2,
                seed=913,
                hands_per_player=4,
                families=CONTEXT_FAMILIES,
                splits=("development", "validation", "test"),
                sequential_raise=sequential_raise,
            )
            for index, context in enumerate(contexts):
                source = context.game
                solver = TabularCFR(source, variant="dcfr")
                for _ in range(1 + index):
                    solver.step()
                policy = solver.average_strategy()
                cache = RiverPolicyEvaluationCache(source, policy)
                for player in (0, 1):
                    target, _ = make_blocker_perturbation(
                        source,
                        player=player,
                        root_tv_budget=0.01,
                        maximum_donor_fraction=0.75,
                    )
                    result = cache.recertify(
                        target,
                        RiverRangeDelta.between(source, target),
                    )
                    _assert_evaluations_equal(
                        self,
                        result.evaluation,
                        evaluate_profile(target, policy),
                    )
                    comparisons += 1
        self.assertEqual(comparisons, 32)

    def test_empty_policy_uses_uniform_behavior_on_added_information_sets(self) -> None:
        source, target = _support_change_pair(raise_to=15.0)
        result = RiverPolicyEvaluationCache(source, {}).recertify(target)
        _assert_evaluations_equal(self, result.evaluation, evaluate_profile(target, {}))

    def test_generated_support_swap_is_an_exact_two_deal_delta(self) -> None:
        context = generate_river_contexts(
            groups=1,
            seed=29,
            hands_per_player=5,
            families=("blocker_stress",),
            splits=("development", "validation", "test"),
            sequential_raise=True,
        )[0]
        for player in (0, 1):
            target, metadata = make_support_swap_perturbation(
                context.game,
                player=player,
            )
            delta = RiverRangeDelta.between(context.game, target)
            self.assertEqual(len(delta.changes), 2)
            self.assertEqual(delta.added_deals, 1)
            self.assertEqual(delta.removed_deals, 1)
            self.assertEqual(delta.reweighted_deals, 0)
            self.assertTrue(metadata["new_private_hand_was_absent"])
            self.assertEqual(metadata["delta_deals"], 2)
            self.assertAlmostEqual(
                delta.total_variation,
                metadata["moved_probability_mass"],
            )

    def test_delta_is_bound_to_exact_structure_source_and_target(self) -> None:
        source, target = _support_change_pair(raise_to=15.0)
        delta = RiverRangeDelta.between(source, target)
        alternate = RiverHoldem.from_joint_weights(
            board=source.board,
            pot=source.pot,
            stacks=source.stacks,
            bet_size=source.bet_size,
            raise_to=source.raise_to,
            joint_weights={deal: 1.0 for deal, _ in target.deals},
        )
        different_structure = RiverHoldem.from_joint_weights(
            board=source.board,
            pot=source.pot + 1.0,
            stacks=source.stacks,
            bet_size=source.bet_size,
            raise_to=source.raise_to,
            joint_weights=source.joint_distribution(),
        )

        with self.assertRaisesRegex(ValueError, "target provenance"):
            RiverPolicyEvaluationCache(source, {}).recertify(alternate, delta)
        with self.assertRaisesRegex(ValueError, "identical game structure"):
            RiverRangeDelta.between(source, different_structure)
        with self.assertRaisesRegex(ValueError, "structure"):
            RiverPolicyEvaluationCache(source, {}).recertify(different_structure)


if __name__ == "__main__":
    unittest.main()
