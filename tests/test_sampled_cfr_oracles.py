"""Exact three-player regret oracles and late transactional failure checks."""

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
import random
import unittest

from pontius.game import CHANCE_PLAYER, TERMINAL_PLAYER
from pontius.sampled_cfr import ExternalSamplingCFR, RegretRow, SamplingLimit


@dataclass(frozen=True)
class ThreePlayerOracleGame:
    """Hidden chance/opponents; player zero remembers its own Enter action."""

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
        return {1: ("enter", "exit"), 2: ("left", "right"),
                3: ("go", "stop"), 4: ("A", "B")}[len(self.path)]

    def apply_action(self, action):
        return ThreePlayerOracleGame(self.path + (action,))

    def information_state_key(self, player):
        return "I" if len(self.path) == 4 else f"p{player}-root"

    def returns(self):
        if len(self.path) != 5 or self.path[-1] == "B":
            return (0.0, 0.0, 0.0)
        payoff = {("c0", "left"): 8.0, ("c0", "right"): 4.0,
                  ("c1", "left"): -4.0, ("c1", "right"): 12.0}[
                      self.path[0], self.path[2]]
        return (payoff, -payoff / 2, -payoff / 2)


class PrefixRandom(random.Random):
    """Enumerate the first traverser's external draws; finish other paths normally."""

    def __init__(self, prefix):
        super().__init__(17)
        self.prefix = tuple(prefix)
        self.cursor = 0

    def random(self):
        if self.cursor < len(self.prefix):
            draw = self.prefix[self.cursor]
            self.cursor += 1
            return draw
        return super().random()

    def getstate(self):
        return super().getstate(), self.cursor

    def setstate(self, state):
        underlying, self.cursor = state
        super().setstate(underlying)


def oracle_trainer(variant="cfr"):
    trainer = ExternalSamplingCFR(
        3, lambda rng: ThreePlayerOracleGame(), "three-player-exact-oracle-v1",
        variant=variant, seed=2,
    )
    # All probabilities are exactly representable binary fractions. Enter 1/4,
    # left 1/4, go 3/4 and A 1/4 are independent frozen policies.
    trainer.rows = {
        "p0-root": RegretRow(0, ("enter", "exit"), [1.0, 3.0], [4.0, 12.0], 1),
        "p1-root": RegretRow(1, ("left", "right"), [1.0, 3.0], [4.0, 12.0], 1),
        "p2-root": RegretRow(2, ("go", "stop"), [3.0, 1.0], [12.0, 4.0], 1),
        "I": RegretRow(0, ("A", "B"), [1.0, 3.0], [4.0, 12.0], 1),
    }
    trainer.iterations = 1
    return trainer


class SampledCFROracleTests(unittest.TestCase):
    def test_eight_samples_have_unit_weight_and_one_distinct_iteration(self):
        @dataclass(frozen=True)
        class OneDecision:
            action: str = ""

            @property
            def current_player(self):
                return TERMINAL_PLAYER if self.action else 0

            def legal_actions(self):
                return ("A", "B")

            def information_state_key(self, player):
                return "root"

            def apply_action(self, action):
                return OneDecision(action)

            def returns(self):
                return (1.0, -1.0) if self.action == "A" else (-1.0, 1.0)

        trainer = ExternalSamplingCFR(2, lambda rng: OneDecision(), "one-decision-v1",
                                      averaging_trajectories=8)
        trainer.step()
        row = trainer.rows["root"]
        self.assertEqual(row.strategy_sum, [0.5, 0.5])
        self.assertEqual((row.average_samples, row.average_visits,
                          row.average_regret_samples, row.regret_visits), (8, 1, 0, 1))
        trainer.step()
        self.assertEqual(row.strategy_sum, [1.5, 0.5])
        self.assertEqual((row.average_samples, row.average_visits,
                          row.average_regret_samples, row.regret_visits), (16, 2, 8, 2))
        self.assertEqual(trainer.total_nodes,
                         trainer.total_regret_nodes + trainer.total_average_nodes)
        trainer.max_nodes = 36  # 5 regret nodes plus 32 average nodes are required.
        before = trainer.state_dict()
        with self.assertRaises(SamplingLimit):
            trainer.step()
        self.assertEqual(trainer.state_dict(), before)

    def test_exact_three_player_counterfactual_regrets_exclude_own_reach(self):
        # E[A | external reach] = (3/4)*[(1/4)*(8/4+3*4/4)
        #                                     +(3/4)*(-4/4+3*12/4)] = 87/16.
        # At I, sigma=(1/4,3/4), so unnormalized counterfactual regrets are
        # (3/4,-1/4)*(87/16) = (261/64,-87/64). The player's earlier Enter
        # probability 1/4 MUST NOT multiply these counterfactual values.
        expected = [Fraction(0), Fraction(0)]
        for chance, opponent_one, opponent_two in product(range(2), repeat=3):
            probabilities = ((Fraction(1, 4), Fraction(3, 4)),
                             (Fraction(1, 4), Fraction(3, 4)),
                             (Fraction(3, 4), Fraction(1, 4)))
            selected = (chance, opponent_one, opponent_two)
            mass = probabilities[0][chance] * probabilities[1][opponent_one]
            mass *= probabilities[2][opponent_two]
            draws = [float(pair[0] / 2 if choice == 0 else pair[0] + pair[1] / 2)
                     for pair, choice in zip(probabilities, selected, strict=True)]
            trainer = oracle_trainer()
            trainer.rng = PrefixRandom(draws)
            before = trainer.rows["I"].regrets.copy()
            trainer.step()
            for action in range(2):
                expected[action] += mass * Fraction(trainer.rows["I"].regrets[action]
                                                     - before[action])
        self.assertEqual(expected, [Fraction(261, 64), Fraction(-87, 64)])
        self.assertNotEqual(expected, [Fraction(261, 256), Fraction(-87, 256)])

    def test_iteration_two_scales_both_frozen_regret_and_average_increments(self):
        ordinary = oracle_trainer("cfr")
        linear = oracle_trainer("linear")
        initial = ordinary.state_dict()
        self.assertEqual(ordinary.rng.getstate(), linear.rng.getstate())
        ordinary.step()
        linear.step()
        for attribute in ("regrets", "strategy_sum"):
            nonzero = False
            for row in initial["rows"]:
                key = row["key"]
                for index, previous in enumerate(row[attribute]):
                    increment = getattr(ordinary.rows[key], attribute)[index] - previous
                    weighted = getattr(linear.rows[key], attribute)[index] - previous
                    self.assertEqual(weighted, 2 * increment, (key, attribute, index))
                    nonzero |= increment != 0
            self.assertTrue(nonzero, attribute)
        self.assertEqual(ordinary.rng.getstate(), linear.rng.getstate())
        self.assertEqual(ordinary.total_nodes, linear.total_nodes)

    def test_late_averaging_capacity_failure_rolls_back_existing_rows_and_rng(self):
        control = oracle_trainer()
        initial = control.state_dict()
        visited = control.step()
        # The successful control establishes this concrete path's last-node
        # boundary. A one-node-short budget must fail in the final average path.
        for attribute in ("regrets", "strategy_sum"):
            self.assertTrue(any(row[attribute] != getattr(control.rows[row["key"]], attribute)
                                for row in initial["rows"]), attribute)
        trainer = oracle_trainer()
        trainer.max_nodes = visited - 1
        root_calls = []

        def root_sampler(rng):
            root_calls.append(len(root_calls))
            return ThreePlayerOracleGame()

        trainer.root_sampler = root_sampler
        before = trainer.state_dict()
        with self.assertRaisesRegex(SamplingLimit, "averaging trajectory"):
            trainer.step()
        # Three regret traversals and two averaging paths completed before the
        # sixth root failed: existing-row candidates existed but never committed.
        self.assertEqual(root_calls, list(range(6)))
        self.assertEqual(trainer.state_dict(), before)


if __name__ == "__main__":
    unittest.main()
