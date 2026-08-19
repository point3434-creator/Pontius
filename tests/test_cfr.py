from __future__ import annotations

import unittest

from pontius.cfr import TabularCFR
from pontius.evaluation import collect_information_sets, evaluate_profile, policy_distribution
from pontius.kuhn import KuhnPoker


class CFRTests(unittest.TestCase):
    def test_vanilla_cfr_approaches_kuhn_value(self) -> None:
        game = KuhnPoker()
        solver = TabularCFR(game, "cfr")
        solver.run(10_000)
        evaluation = evaluate_profile(game, solver.average_strategy())
        self.assertAlmostEqual(evaluation.utilities[0], -1.0 / 18.0, delta=0.01)
        self.assertLess(evaluation.nash_conv, 0.04)
        self.assertEqual(len(solver.information_sets), 12)

    def test_linear_cfr_approaches_kuhn_value(self) -> None:
        game = KuhnPoker()
        solver = TabularCFR(game, "lcfr")
        solver.run(10_000)
        evaluation = evaluate_profile(game, solver.average_strategy())
        self.assertAlmostEqual(evaluation.utilities[0], -1.0 / 18.0, delta=0.01)
        self.assertLess(evaluation.nash_conv, 0.04)

    def test_cfr_plus_approaches_kuhn_value(self) -> None:
        game = KuhnPoker()
        solver = TabularCFR(game, "cfr_plus")
        solver.run(5_000)
        evaluation = evaluate_profile(game, solver.average_strategy())
        self.assertAlmostEqual(evaluation.utilities[0], -1.0 / 18.0, delta=0.01)
        self.assertLess(evaluation.nash_conv, 0.04)
        self.assertTrue(
            all(
                regret >= 0.0
                for data in solver.information_sets.values()
                for regret in data.regrets.values()
            )
        )

    def test_dcfr_approaches_kuhn_value(self) -> None:
        game = KuhnPoker()
        solver = TabularCFR(game, "dcfr")
        solver.run(5_000)
        evaluation = evaluate_profile(game, solver.average_strategy())
        self.assertAlmostEqual(evaluation.utilities[0], -1.0 / 18.0, delta=0.01)
        self.assertLess(evaluation.nash_conv, 0.04)

    def test_unknown_variant_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TabularCFR(KuhnPoker(), "not-cfr")  # type: ignore[arg-type]

    def test_shadow_regret_uses_active_deltas_without_changing_strategy(self) -> None:
        game = KuhnPoker()
        plain = TabularCFR(game, "dcfr")
        shadowed = TabularCFR(
            game,
            "dcfr",
            shadow_regret_variants=("cfr_plus",),
        )

        plain.run(7)
        shadowed.run(7)

        self.assertEqual(plain.current_strategy(), shadowed.current_strategy())
        self.assertEqual(plain.average_strategy(), shadowed.average_strategy())
        self.assertEqual(plain.information_sets, shadowed.information_sets)
        self.assertEqual(shadowed.shadow_regret_variants, ("cfr_plus",))
        self.assertTrue(shadowed.shadow_regret_table("cfr_plus"))
        summary = shadowed.shadow_regret_summary("cfr_plus")
        self.assertEqual(summary["materialized_information_sets"], 12)
        self.assertEqual(summary["regret_entries"], 24)
        self.assertGreater(summary["instantaneous_regret_updates"], 0)
        self.assertGreater(summary["regret_discount_updates"], 0)

    def test_dcfr_cfr_plus_shadow_matches_standalone_only_before_paths_diverge(
        self,
    ) -> None:
        game = KuhnPoker()
        shadowed = TabularCFR(
            game,
            "dcfr",
            shadow_regret_variants=("cfr_plus",),
        )
        standalone = TabularCFR(game, "cfr_plus")

        shadowed.run(1)
        standalone.run(1)

        first_expected = {
            key: dict(data.regrets)
            for key, data in standalone.information_sets.items()
        }
        first_actual = shadowed.shadow_regret_table("cfr_plus")
        self.assertEqual(first_actual.keys(), first_expected.keys())
        for key, action_regrets in first_expected.items():
            for action, regret in action_regrets.items():
                self.assertAlmostEqual(first_actual[key][action], regret)

        shadowed.run(1)
        standalone.run(1)
        second_expected = {
            key: dict(data.regrets)
            for key, data in standalone.information_sets.items()
        }
        second_actual = shadowed.shadow_regret_table("cfr_plus")
        self.assertTrue(
            any(
                abs(second_actual[key][action] - regret) > 1e-12
                for key, action_regrets in second_expected.items()
                for action, regret in action_regrets.items()
            )
        )

    def test_shadow_regret_configuration_is_strict_and_defensive(self) -> None:
        game = KuhnPoker()
        with self.assertRaises(ValueError):
            TabularCFR(game, "dcfr", shadow_regret_variants=("dcfr",))
        with self.assertRaises(ValueError):
            TabularCFR(
                game,
                "dcfr",
                shadow_regret_variants=("cfr_plus", "cfr_plus"),
            )

        solver = TabularCFR(
            game,
            "dcfr",
            shadow_regret_variants=("cfr_plus",),
        )
        solver.run(1)
        copied = solver.shadow_regret_table("cfr_plus")
        key = next(iter(copied))
        action = next(iter(copied[key]))
        copied[key][action] = 123.0
        self.assertNotEqual(
            solver.shadow_regret_table("cfr_plus")[key][action],
            123.0,
        )
        with self.assertRaises(ValueError):
            solver.shadow_regret_table("cfr")

    def test_blueprint_warm_start_sets_the_initial_behavior_policy(self) -> None:
        game = KuhnPoker()
        blueprint_solver = TabularCFR(game, "lcfr")
        blueprint_solver.run(100)
        blueprint = blueprint_solver.average_strategy()

        solver = TabularCFR(game, "dcfr")
        solver.warm_start(blueprint, regret_mass=7.0)
        current = solver.current_strategy()

        for player in range(game.num_players):
            for key, actions in collect_information_sets(game, player).items():
                expected = policy_distribution(blueprint, key, actions)
                for action in actions:
                    self.assertAlmostEqual(current[key][action], expected[action])
        self.assertEqual(solver.iteration, 0)
        self.assertTrue(
            all(
                total == 0.0
                for data in solver.information_sets.values()
                for total in data.strategy_sum.values()
            )
        )

    def test_warm_start_requires_positive_mass_and_pristine_solver(self) -> None:
        solver = TabularCFR(KuhnPoker(), "cfr")
        with self.assertRaises(ValueError):
            solver.warm_start({}, regret_mass=0.0)

        solver.warm_start({}, regret_mass=1.0)
        with self.assertRaises(ValueError):
            solver.warm_start({}, regret_mass=1.0)

    def test_cached_schema_warm_start_matches_traversal_initialization(self) -> None:
        game = KuhnPoker()
        blueprint_solver = TabularCFR(game, "lcfr")
        blueprint_solver.run(20)
        blueprint = blueprint_solver.average_strategy()
        schema = {}
        for player in range(game.num_players):
            schema.update(collect_information_sets(game, player))

        traversed = TabularCFR(game, "dcfr")
        cached = TabularCFR(game, "dcfr")
        traversed.warm_start(blueprint, regret_mass=3.0)
        cached.warm_start_from_schema(blueprint, regret_mass=3.0, information_sets=schema)

        self.assertEqual(cached.current_strategy(), traversed.current_strategy())
        cached.step()
        traversed.step()
        self.assertEqual(cached.current_strategy(), traversed.current_strategy())
        self.assertEqual(cached.average_strategy(), traversed.average_strategy())

    def test_cached_schema_warm_start_is_defensive(self) -> None:
        solver = TabularCFR(KuhnPoker(), "cfr")
        with self.assertRaisesRegex(ValueError, "nonempty"):
            solver.warm_start_from_schema({}, 1.0, {})
        with self.assertRaisesRegex(ValueError, "cached action schema"):
            solver.warm_start_from_schema({}, 1.0, {"bad": ()})

    def test_full_blueprint_anchor_never_leaves_the_blueprint(self) -> None:
        game = KuhnPoker()
        blueprint_solver = TabularCFR(game, "lcfr")
        blueprint_solver.run(50)
        blueprint = blueprint_solver.average_strategy()
        solver = TabularCFR(
            game,
            "cfr_plus",
            blueprint_policy=blueprint,
            blueprint_weight=1.0,
        )
        solver.run(20)

        for policy in (solver.current_strategy(), solver.average_strategy()):
            for player in range(game.num_players):
                for key, actions in collect_information_sets(game, player).items():
                    expected = policy_distribution(blueprint, key, actions)
                    for action in actions:
                        self.assertAlmostEqual(policy[key][action], expected[action])

    def test_partial_anchor_bounds_current_and_average_policy_distance(self) -> None:
        game = KuhnPoker()
        blueprint_solver = TabularCFR(game, "lcfr")
        blueprint_solver.run(50)
        blueprint = blueprint_solver.average_strategy()
        blueprint_weight = 0.75
        solver = TabularCFR(
            game,
            "dcfr",
            blueprint_policy=blueprint,
            blueprint_weight=blueprint_weight,
        )
        solver.run(50)

        for policy in (solver.current_strategy(), solver.average_strategy()):
            for player in range(game.num_players):
                for key, actions in collect_information_sets(game, player).items():
                    expected = policy_distribution(blueprint, key, actions)
                    distance = 0.5 * sum(
                        abs(policy[key][action] - expected[action])
                        for action in actions
                    )
                    self.assertLessEqual(distance, 1.0 - blueprint_weight + 1e-12)

    def test_invalid_blueprint_anchor_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TabularCFR(KuhnPoker(), blueprint_policy={}, blueprint_weight=-0.1)
        with self.assertRaises(ValueError):
            TabularCFR(KuhnPoker(), blueprint_policy={}, blueprint_weight=1.1)
        with self.assertRaises(ValueError):
            TabularCFR(KuhnPoker(), blueprint_weight=0.5)

    def test_three_player_cfr_produces_a_zero_sum_profile(self) -> None:
        game = KuhnPoker(3)
        solver = TabularCFR(game, "lcfr")
        solver.run(100)
        evaluation = evaluate_profile(game, solver.average_strategy())
        self.assertAlmostEqual(sum(evaluation.utilities), 0.0)
        self.assertGreater(len(solver.information_sets), 12)
        self.assertGreaterEqual(evaluation.nash_conv, 0.0)


if __name__ == "__main__":
    unittest.main()
