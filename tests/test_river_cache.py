from __future__ import annotations

import unittest

from pontius.evaluation import evaluate_profile
from pontius.evaluation import collect_information_sets
from pontius.river import RiverDeal, RiverHoldem, make_hole, parse_cards
from pontius.river_cache import (
    assess_river_range_reuse,
    exact_strategy_cache_lookup,
    river_cache_match,
    structural_information_schema_lookup,
    structural_warm_start_hint,
    transferred_exploitability_certificate,
)
from pontius.river_oracle import solve_river_game


def _range_pair() -> tuple[RiverHoldem, RiverHoldem]:
    board = parse_cards("2c", "7d", "9h", "Js", "Qc")
    common = RiverDeal(make_hole("Ac", "Ad"), make_hole("Kh", "Kd"))
    target_hand = make_hole("Ah", "3h")
    nuts = RiverDeal(make_hole("Ts", "Ks"), target_hand)
    bluff = RiverDeal(make_hole("4s", "5s"), target_hand)
    arguments = {
        "board": board,
        "pot": 10.0,
        "stacks": (30.0, 30.0),
        "bet_size": 5.0,
        "raise_to": 15.0,
    }
    source = RiverHoldem.from_joint_weights(
        **arguments,
        joint_weights={common: 0.99, nuts: 0.01},
    )
    current = RiverHoldem.from_joint_weights(
        **arguments,
        joint_weights={common: 0.99, bluff: 0.01},
    )
    return source, current


class RiverCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source, cls.current = _range_pair()
        cls.source_solution = solve_river_game(cls.source)

    def test_only_exact_provenance_returns_a_deployable_strategy(self) -> None:
        exact = exact_strategy_cache_lookup(
            self.source,
            self.source,
            self.source_solution.policy,
        )
        approximate = exact_strategy_cache_lookup(
            self.source,
            self.current,
            self.source_solution.policy,
        )

        self.assertEqual(river_cache_match(self.source, self.source), "exact_strategy_hit")
        self.assertEqual(river_cache_match(self.source, self.current), "structural_only")
        self.assertIsNotNone(exact)
        self.assertIsNone(approximate)
        assert exact is not None
        key = next(iter(exact))
        action = next(iter(exact[key]))
        exact[key][action] = -1.0
        self.assertNotEqual(self.source_solution.policy[key][action], -1.0)

    def test_structural_match_returns_only_a_warm_start_hint(self) -> None:
        hint = structural_warm_start_hint(
            self.source,
            self.current,
            self.source_solution.policy,
        )
        different_structure = RiverHoldem.from_joint_weights(
            board=self.source.board,
            pot=12.0,
            stacks=(30.0, 30.0),
            bet_size=5.0,
            raise_to=15.0,
            joint_weights=self.source.joint_distribution(),
        )

        self.assertIsNotNone(hint)
        schema = {}
        for player in range(self.source.num_players):
            schema.update(collect_information_sets(self.source, player))
        self.assertEqual(
            structural_information_schema_lookup(
                self.source,
                self.current,
                schema,
            ),
            schema,
        )
        self.assertIsNone(
            structural_warm_start_hint(
                self.source,
                different_structure,
                self.source_solution.policy,
            )
        )
        self.assertIsNone(
            structural_information_schema_lookup(
                self.source,
                different_structure,
                schema,
            )
        )
        self.assertEqual(river_cache_match(self.source, different_structure), "miss")

    def test_range_assessment_exposes_conditional_shock_without_hit(self) -> None:
        assessment = assess_river_range_reuse(self.source, self.current)

        self.assertEqual(assessment.match, "structural_only")
        self.assertTrue(assessment.topology_reusable)
        self.assertFalse(assessment.direct_strategy_deployable)
        self.assertAlmostEqual(assessment.root_joint_total_variation or 0.0, 0.01)
        assert assessment.maximum_conditional_total_variation is not None
        self.assertEqual(max(assessment.maximum_conditional_total_variation), 1.0)

    def test_tv_certificate_bounds_fixed_policy_target_exploitability(self) -> None:
        source_exploitability = self.source_solution.nash_conv / 2.0
        certificate = transferred_exploitability_certificate(
            self.source,
            self.current,
            source_exploitability=source_exploitability,
        )
        target = evaluate_profile(self.current, self.source_solution.policy)

        self.assertAlmostEqual(certificate.root_joint_total_variation, 0.01)
        self.assertAlmostEqual(certificate.additive_bound, 0.8)
        self.assertLessEqual(
            target.exploitability or 0.0,
            certificate.capped_target_upper_bound + 1e-12,
        )
        with self.assertRaises(ValueError):
            transferred_exploitability_certificate(
                self.source,
                self.current,
                source_exploitability=-1.0,
            )


if __name__ == "__main__":
    unittest.main()
