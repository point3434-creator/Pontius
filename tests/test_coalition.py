from __future__ import annotations

import unittest

from pontius.coalition import (
    CoalitionEvaluationResult,
    CoalitionThreat,
    assess_multiplayer_candidate,
    coalition_best_response,
    coalition_best_response_enumerated,
    evaluate_coalition_threats,
)
from pontius.evaluation import EvaluationResult, best_response, evaluate_profile
from pontius.river import make_hole, parse_cards
from pontius.river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem


def game_with_two_deals() -> MultiwayRiverHoldem:
    deals = (
        MultiwayRiverDeal(
            (
                make_hole("As", "Ad"),
                make_hole("Ks", "Kd"),
                make_hole("Ts", "Td"),
            )
        ),
        MultiwayRiverDeal(
            (
                make_hole("Ah", "Ac"),
                make_hole("Kh", "Kc"),
                make_hole("Th", "Tc"),
            )
        ),
    )
    return MultiwayRiverHoldem.from_joint_weights(
        board=parse_cards("2c", "7d", "9h", "Js", "Qc"),
        pot=12.0,
        stacks=(30.0,) * 3,
        bet_size=3.0,
        joint_weights={deals[0]: 2.0, deals[1]: 1.0},
    )


def evaluation(nash_conv: float, gains: tuple[float, float, float]) -> EvaluationResult:
    return EvaluationResult(
        utilities=(0.0, 0.0, 0.0),
        best_response_values=gains,
        deviation_gains=gains,
        nash_conv=nash_conv,
        exploitability=None,
    )


def coalition_result(gains: tuple[float, float, float]) -> CoalitionEvaluationResult:
    coalitions = ((0, 1), (0, 2), (1, 2))
    threats = tuple(
        CoalitionThreat(
            coalition=coalition,
            baseline_value=0.0,
            best_response_value=gain,
            deviation_gain=gain,
        )
        for coalition, gain in zip(coalitions, gains, strict=True)
    )
    return CoalitionEvaluationResult(
        threats=threats,
        maximum_deviation_gain=max(gains),
        total_deviation_gain=sum(gains),
    )


class CoalitionBestResponseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = game_with_two_deals()

    def test_singleton_team_response_matches_ordinary_best_response(self) -> None:
        for player in range(3):
            ordinary, _ = best_response(self.game, {}, player)
            team, _ = coalition_best_response(self.game, {}, (player,))
            self.assertAlmostEqual(team, ordinary, places=12)

    def test_pair_team_response_matches_independent_pure_policy_enumeration(self) -> None:
        deterministic = self.game.with_joint_weights({self.game.deals[0][0]: 1.0})
        dynamic, _ = coalition_best_response(deterministic, {}, (0, 1))
        enumerated, _ = coalition_best_response_enumerated(
            deterministic,
            {},
            (0, 1),
        )
        self.assertAlmostEqual(dynamic, enumerated, places=12)

    def test_pair_threats_report_baseline_response_and_gain(self) -> None:
        profile = evaluate_profile(self.game, {})
        result = evaluate_coalition_threats(self.game, {})
        self.assertEqual(
            tuple(threat.coalition for threat in result.threats),
            ((0, 1), (0, 2), (1, 2)),
        )
        self.assertEqual(
            result.maximum_deviation_gain,
            max(threat.deviation_gain for threat in result.threats),
        )
        for threat in result.threats:
            baseline = sum(profile.utilities[player] for player in threat.coalition)
            self.assertAlmostEqual(threat.baseline_value, baseline, places=12)
            self.assertGreaterEqual(threat.best_response_value + 1e-12, baseline)
            self.assertAlmostEqual(
                threat.deviation_gain,
                threat.best_response_value - baseline,
                places=12,
            )

    def test_coalition_key_rejects_outsider_actor(self) -> None:
        state = self.game.initial_state().apply_action(self.game.deals[0][0])
        with self.assertRaisesRegex(ValueError, "acting player"):
            state.coalition_information_state_key((1, 2))

    def test_full_player_coalition_is_rejected_as_uninformative(self) -> None:
        with self.assertRaisesRegex(ValueError, "full player set"):
            coalition_best_response(self.game, {}, (0, 1, 2))


class MultiplayerAcceptanceTests(unittest.TestCase):
    def test_aggregate_improvement_cannot_hide_worse_player(self) -> None:
        result = assess_multiplayer_candidate(
            evaluation(0.30, (0.10, 0.10, 0.10)),
            evaluation(0.25, (0.05, 0.05, 0.15)),
            coalition_result((0.20, 0.20, 0.20)),
            coalition_result((0.19, 0.19, 0.19)),
            payoff_span=21.0,
        )
        self.assertTrue(result.aggregate_nash_conv_strictly_decreases)
        self.assertFalse(result.no_player_deviation_gain_increases)
        self.assertFalse(result.unilateral_pareto_accept)
        self.assertFalse(result.coalition_stress_accept)

    def test_coalition_label_can_reject_unilateral_pareto_improvement(self) -> None:
        result = assess_multiplayer_candidate(
            evaluation(0.30, (0.10, 0.10, 0.10)),
            evaluation(0.24, (0.08, 0.08, 0.08)),
            coalition_result((0.20, 0.20, 0.20)),
            coalition_result((0.19, 0.21, 0.19)),
            payoff_span=21.0,
        )
        self.assertTrue(result.unilateral_pareto_accept)
        self.assertFalse(result.no_coalition_deviation_gain_increases)
        self.assertFalse(result.coalition_stress_accept)

    def test_both_frozen_acceptance_labels_can_pass(self) -> None:
        result = assess_multiplayer_candidate(
            evaluation(0.30, (0.10, 0.10, 0.10)),
            evaluation(0.24, (0.08, 0.08, 0.08)),
            coalition_result((0.20, 0.20, 0.20)),
            coalition_result((0.19, 0.18, 0.17)),
            payoff_span=21.0,
        )
        self.assertTrue(result.unilateral_pareto_accept)
        self.assertTrue(result.coalition_stress_accept)


if __name__ == "__main__":
    unittest.main()
