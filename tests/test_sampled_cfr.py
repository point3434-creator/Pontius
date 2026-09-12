"""Independent checks of sampled updates, multiplayer averaging and restart state."""

from dataclasses import dataclass
from itertools import product
import json
import random
import unittest

from pontius.evaluation import evaluate_profile
from pontius.game import CHANCE_PLAYER, TERMINAL_PLAYER
from pontius.kuhn import KuhnPoker
from pontius.sampled_cfr import ExternalSamplingCFR, SamplingLimit, average_trajectory


class ScriptedRandom(random.Random):
    def __init__(self, draws):
        super().__init__(0)
        self.draws = iter(draws)

    def random(self):
        return next(self.draws)


@dataclass(frozen=True)
class HiddenChoiceGame:
    """Player 0 remembers Enter but cannot observe chance or player 1's choice."""

    path: tuple = ()

    @property
    def current_player(self):
        if not self.path:
            return CHANCE_PLAYER
        if "exit" in self.path or "stop" in self.path or len(self.path) == 5:
            return TERMINAL_PLAYER
        return (0, 1, 2, 0)[len(self.path) - 1]

    def chance_outcomes(self):
        return (("c0", 0.25), ("c1", 0.75))

    def legal_actions(self):
        return {
            1: ("enter", "exit"),
            2: ("left", "right"),
            3: ("go", "stop"),
            4: ("A", "B"),
        }[len(self.path)]

    def apply_action(self, action):
        return HiddenChoiceGame(self.path + (action,))

    def information_state_key(self, player):
        return "I" if len(self.path) == 4 else f"p{player}-root"

    def returns(self):
        return (0.0, 0.0, 0.0)


class SampledCFRTests(unittest.TestCase):
    def trainer(self, players=2, variant="cfr", **kwargs):
        game = KuhnPoker(players)
        return ExternalSamplingCFR(
            players, lambda rng: game.initial_state(), f"kuhn-{players}",
            variant=variant, seed=17, **kwargs,
        )

    def test_first_average_uses_the_frozen_profile_before_regret_updates(self):
        trainer = self.trainer(players=3)
        trainer.step()
        sampled = [row for row in trainer.rows.values() if row.average_visits]
        self.assertTrue(sampled)
        self.assertTrue(any(any(row.regrets) for row in trainer.rows.values()))
        for row in sampled:
            self.assertEqual(row.strategy_sum[0], row.strategy_sum[1])

    def test_resume_reproduces_the_entire_serial_trajectory_including_rng(self):
        for variant in ("cfr", "linear"):
            with self.subTest(variant=variant):
                trainer = self.trainer(players=3, variant=variant)
                for _ in range(25):
                    trainer.step()
                snapshot = json.loads(json.dumps(trainer.state_dict(), allow_nan=False))
                restored = ExternalSamplingCFR.from_state(
                    snapshot, trainer.root_sampler, expected_game_id="kuhn-3",
                )
                for _ in range(30):
                    trainer.step()
                    restored.step()
                self.assertEqual(trainer.state_dict(), restored.state_dict())

    def test_capacity_stop_leaves_tables_iteration_and_rng_unchanged(self):
        for limits in ({"max_rows": 1}, {"max_nodes": 1}):
            with self.subTest(limits=limits):
                trainer = self.trainer(**limits)
                before = trainer.state_dict()
                with self.assertRaises(SamplingLimit):
                    trainer.step()
                self.assertEqual(before, trainer.state_dict())

    def test_restore_rejects_wrong_game_and_nonfinite_accumulators(self):
        trainer = self.trainer()
        trainer.step()
        state = trainer.state_dict()
        with self.assertRaises(ValueError):
            ExternalSamplingCFR.from_state(state, trainer.root_sampler, "other-game")
        state["rows"][0]["regrets"][0] = float("nan")
        with self.assertRaises(ValueError):
            ExternalSamplingCFR.from_state(state, trainer.root_sampler, "kuhn-2")

    def test_exact_expected_multiplayer_average_includes_own_reach(self):
        # Independent path enumeration: chance 1/4,3/4; fixed opponents 1/2.
        # The target's two own-reach/A-probability pairs are (1/5,9/10),(4/5,1/10).
        # Ordinary normalized A mass is 13/50; linear is 17/90.
        for weights, expected in (((1, 1), 13 / 50), ((1, 2), 17 / 90)):
            accumulated = [0.0, 0.0]
            for enter, probability_a, weight in zip(
                (0.2, 0.8), (0.9, 0.1), weights, strict=True,
            ):
                def policy(state):
                    self.assertEqual(state.current_player, 0)
                    return (enter, 1 - enter) if len(state.path) == 1 else (
                        probability_a, 1 - probability_a,
                    )

                for chance, hidden, selected_a in product(range(2), repeat=3):
                    # Only trajectories reaching I contribute to its expected total.
                    draws = [0.125 if chance == 0 else 0.625, enter / 2,
                             0.25 if hidden == 0 else 0.75, 0.25,
                             probability_a / 2 if selected_a == 0 else
                             probability_a + (1 - probability_a) / 2]
                    chance_probability = 0.25 if chance == 0 else 0.75
                    action_probability = probability_a if selected_a == 0 else 1 - probability_a
                    path_probability = chance_probability * enter * 0.5 * 0.5 * action_probability
                    sample = average_trajectory(
                        HiddenChoiceGame(), 0, policy, ScriptedRandom(draws), weight=weight,
                    )
                    for action in range(2):
                        accumulated[action] += path_probability * sample.updates["I"][action]
            self.assertAlmostEqual(accumulated[0] / sum(accumulated), expected, places=13)

    def test_sampled_cfr_reduces_exact_heads_up_kuhn_nashconv(self):
        # Independent full-tree best responses, not the trainer's own regret metric.
        initial = evaluate_profile(KuhnPoker(2), {}).nash_conv
        for variant in ("cfr", "linear"):
            with self.subTest(variant=variant):
                trainer = self.trainer(variant=variant)
                for _ in range(6000):
                    trainer.step()
                final = evaluate_profile(KuhnPoker(2), trainer.average_policy()).nash_conv
                self.assertLess(final, 0.10)
                self.assertLess(final, initial / 4)


if __name__ == "__main__":
    unittest.main()
