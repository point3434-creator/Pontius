from __future__ import annotations

import unittest
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from pontius.cfr import TabularCFR
from pontius.evaluation import evaluate_profile
from pontius.river import RiverHoldem, evaluate_seven, make_hole, parse_cards
from pontius.river_abstraction_study import (
    CFR, DEVELOPMENT_BOARDS, PayoffGame, anchored_clusters, development_case,
    range_features, representations, uniform_equities,
)
from pontius.river_oracle import solve_river_game


def fixture(raise_to=None):
    return RiverHoldem.from_independent_ranges(
        board=parse_cards('2c', '7d', '9h', 'Js', 'Qc'),
        pot=10, stacks=(20, 20), bet_size=5, raise_to=raise_to,
        player0_weights={make_hole('Ts', 'Ks'): 2, make_hole('Ah', '3h'): 1,
                         make_hole('4s', '5s'): 3},
        player1_weights={make_hole('Ac', 'Ad'): 3, make_hole('Ah', '3h'): 2,
                         make_hole('Ts', 'Ks'): 1},
    )


class PayoffTests(unittest.TestCase):
    def test_values_and_individual_best_responses(self):
        game = fixture()
        matrix = PayoffGame.from_river(game)
        for x, y in [(np.array([0.2, 0.7, 0.9]), np.array([0.4, 0.1, 0.8])),
                     (np.zeros(3), np.ones(3)), (np.ones(3), np.zeros(3))]:
            expected = evaluate_profile(game, matrix.lift_policy(game, x, y))
            actual = matrix.evaluate(x, y)
            self.assertAlmostEqual(actual['value'], expected.utilities[0], places=12)
            self.assertAlmostEqual(actual['upper'], expected.best_response_values[0], places=12)
            self.assertAlmostEqual(actual['lower'], -expected.best_response_values[1], places=12)
            self.assertAlmostEqual(actual['exploitability'], expected.exploitability, places=12)

    def test_cfr_trajectory_matches_existing_full_tree(self):
        game = fixture()
        matrix = PayoffGame.from_river(game)
        compact, reference = CFR(matrix), TabularCFR(game, 'cfr')
        for iteration in range(1, 51):
            compact.step()
            reference.step()
            if iteration in (1, 2, 10, 50):
                for actual, expected in [
                    (matrix.lift_policy(game, *compact.average()), reference.average_strategy()),
                    (matrix.lift_policy(game, *compact.current()), reference.current_strategy()),
                ]:
                    self.assertEqual(actual.keys(), expected.keys())
                    for key in actual:
                        for action in actual[key]:
                            self.assertAlmostEqual(actual[key][action], expected[key][action],
                                                   places=11)

    def test_aggregation_preserves_lifted_value_and_limits_br(self):
        matrix = PayoffGame.from_river(fixture())
        groups = (np.array([0, 0, 1]), np.array([0, 1, 1]))
        reduced = matrix.aggregate(groups)
        x, y = np.array([0.2, 0.8]), np.array([0.6, 0.3])
        exact = matrix.evaluate(x[groups[0]], y[groups[1]])
        restricted = reduced.evaluate(x, y)
        self.assertAlmostEqual(exact['value'], restricted['value'], places=12)
        self.assertGreaterEqual(exact['upper'] + 1e-12, restricted['upper'])
        self.assertLessEqual(exact['lower'], restricted['lower'] + 1e-12)

    def test_normal_form_oracle_in_bounds(self):
        game = fixture()
        matrix = PayoffGame.from_river(game)
        oracle = solve_river_game(game)
        solver = CFR(matrix)
        for _ in range(100):
            solver.step()
        result = matrix.evaluate(*solver.average())
        self.assertLessEqual(result['lower'], oracle.value_player0 + 1e-10)
        self.assertGreaterEqual(result['upper'] + 1e-10, oracle.value_player0)

    def test_rejects_unsupported_and_invalid_policies(self):
        with self.assertRaises(ValueError):
            PayoffGame.from_river(fixture(10))
        matrix = PayoffGame.from_river(fixture())
        for x in ([0.5], [0.5, float('nan'), 0.2], [-0.1, 0.2, 0.3]):
            with self.assertRaises(ValueError):
                matrix.evaluate(x, [0.5] * 3)
        with self.assertRaises(ValueError):
            matrix.aggregate(([0, 2, 2], [0, 0, 0]))
        with self.assertRaises(ValueError):
            CFR(matrix).average()

    def test_all_showdowns_tie(self):
        game = RiverHoldem.from_independent_ranges(
            board=parse_cards('Tc', 'Jc', 'Qc', 'Kc', 'Ac'), pot=10,
            stacks=(20, 20), bet_size=5,
            player0_weights={make_hole('2h', '3h'): 1},
            player1_weights={make_hole('4s', '5s'): 1})
        matrix = PayoffGame.from_river(game)
        np.testing.assert_array_equal(matrix.check, [[0]])
        np.testing.assert_array_equal(matrix.call, [[0]])
        self.assertEqual(matrix.evaluate([1], [1])['value'], 0)
        self.assertEqual(matrix.evaluate([1], [0])['value'], 5)
        self.assertEqual(matrix.evaluate([0], [0])['exploitability'], 2.5)

    def test_grouped_cfr_matches_generic_grouped_information_sets(self):
        game = fixture()
        matrix = PayoffGame.from_river(game)
        groups = (np.array([0, 0, 1]), np.array([0, 1, 1]))
        maps = [{hand: int(g) for hand, g in zip(hands, labels, strict=True)}
                for hands, labels in zip(matrix.hands, groups, strict=True)]

        class State:
            def __init__(self, state):
                self.state = state

            def __getattr__(self, name):
                return getattr(self.state, name)

            def apply_action(self, action):
                return State(self.state.apply_action(action))

            def information_state_key(self, player):
                return f'p{player}:g{maps[player][self.state.deal.hand(player)]}'

        class GroupedGame:
            num_players = 2

            def initial_state(self):
                return State(game.initial_state())

        compact, generic = CFR(matrix.aggregate(groups)), TabularCFR(GroupedGame(), 'cfr')
        for _ in range(50):
            compact.step()
            generic.step()
        for player, probabilities in enumerate(compact.average()):
            for group, p in enumerate(probabilities):
                action = 'bet' if player == 0 else 'call'
                self.assertAlmostEqual(p, generic.average_strategy()[f'p{player}:g{group}'][action],
                                       places=11)


class RepresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.equities = uniform_equities(DEVELOPMENT_BOARDS[0])

    def test_uniform_equity_against_independent_opponent_enumeration(self):
        from itertools import combinations
        board = DEVELOPMENT_BOARDS[0]
        for hand in [make_hole('Ts', 'Ks'), make_hole('Ah', '3h'), make_hole('4s', '5s')]:
            rank = evaluate_seven((*board, *hand))
            scores = []
            deck = set(range(52)) - set(board) - set(hand)
            for opponent in combinations(sorted(deck), 2):
                other = evaluate_seven((*board, *opponent))
                scores.append(1 if rank > other else 0.5 if rank == other else 0)
            self.assertEqual(len(scores), 990)
            self.assertEqual(self.equities[hand], sum(scores) / 990)

    def test_features_against_direct_conditional_range(self):
        game = fixture()
        matrix = PayoffGame.from_river(game)
        for player in (0, 1):
            features, equity = range_features(matrix, self.equities, player)
            for i, hand in enumerate(matrix.hands[player]):
                expected = np.zeros(9)
                eq = 0
                rank = evaluate_seven((*game.board, *hand))
                for opponent, mass in game.conditional_opponent_distribution(player, hand).items():
                    other = evaluate_seven((*game.board, *opponent))
                    band = min(int(self.equities[opponent] * 3), 2)
                    expected[3 * band] += mass
                    expected[3 * band + 1] += mass * (rank > other)
                    expected[3 * band + 2] += mass * (rank == other)
                    eq += mass * ((rank > other) + 0.5 * (rank == other))
                np.testing.assert_allclose(features[i], expected, atol=1e-14, rtol=0)
                self.assertAlmostEqual(equity[i], eq, places=14)
                self.assertAlmostEqual(sum(features[i, ::3]), 1, places=14)

    def test_clustering_duplicate_vectors_still_has_exact_capacity(self):
        labels = anchored_clusters(np.zeros((8, 3)), np.ones(8), 4)
        np.testing.assert_array_equal(np.unique(labels), np.arange(4))
        np.testing.assert_array_equal(labels, anchored_clusters(np.zeros((8, 3)), np.ones(8), 4))
        for k in (0, 9, True):
            with self.assertRaises(ValueError):
                anchored_clusters(np.zeros((8, 3)), np.ones(8), k)

    def test_representations_have_equal_occupied_capacity(self):
        matrix = PayoffGame.from_river(fixture())
        methods = representations(matrix, self.equities)
        for player, hands in enumerate(matrix.hands):
            bins = [min(int(self.equities[h] * 200), 199) for h in hands]
            for method in ('uniform_equity_200', 'range_equity', 'range_response'):
                self.assertEqual(len(np.unique(methods[method][player])), len(set(bins)))
            for i in range(len(hands)):
                for j in range(len(hands)):
                    self.assertEqual(bins[i] == bins[j],
                                     methods['uniform_equity_200'][player][i] ==
                                     methods['uniform_equity_200'][player][j])

    def test_development_boundary(self):
        for board, count, regime in [(parse_cards('3c', '3d', '8h', 'Ts', 'Ad'), 16, 'uniform'),
                                     (DEVELOPMENT_BOARDS[0], 97, 'uniform'),
                                     (DEVELOPMENT_BOARDS[0], 16, 'unknown')]:
            with self.assertRaises(ValueError):
                development_case(board, count, regime)


class DriverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'tools/river_abstraction_study.py'
        spec = importlib.util.spec_from_file_location('river_study_driver_test', path)
        cls.driver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.driver)

    def test_success_retains_recomputable_policies_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'run'
            args = SimpleNamespace(output=output, board=0, hands=2, regime='uniform', iterations=10)
            self.driver.run(args)
            manifest = json.loads((output / 'manifest.json').read_text())
            before = {p.name: sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}
            for name, digest in manifest.items():
                self.assertEqual(before[name], digest)
            inputs = json.loads((output / 'inputs.json').read_text())
            ranges = [{tuple(h): w for h, w in rows} for rows in inputs['ranges']]
            game = RiverHoldem.from_independent_ranges(
                board=inputs['board'], pot=inputs['pot'], stacks=inputs['stacks'],
                bet_size=inputs['bet'], player0_weights=ranges[0], player1_weights=ranges[1])
            matrix = PayoffGame.from_river(game)
            result = json.loads((output / 'result.json').read_text())
            self.assertTrue(result['complete'])
            self.assertEqual(len(result['records']), 4)
            for record in result['records']:
                recomputed = matrix.evaluate(record['hand_bet'], record['hand_call'])
                self.assertEqual(recomputed, record['full_game'])
            with self.assertRaises(FileExistsError):
                self.driver.run(args)
            self.assertEqual(before, {p.name: sha256(p.read_bytes()).hexdigest()
                                      for p in output.iterdir()})

    def test_failure_record_and_tracing_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'failure'
            args = SimpleNamespace(output=output, board=0, hands=2, regime='uniform', iterations=10)
            with patch.object(self.driver.tracemalloc, 'is_tracing', return_value=True):
                with self.assertRaisesRegex(RuntimeError, 'allocation tracing'):
                    self.driver.run(args)
            self.assertFalse(output.exists())
            injected = RuntimeError('injected')
            with patch.object(self.driver, 'development_case', side_effect=injected):
                with self.assertRaisesRegex(RuntimeError, 'injected'):
                    self.driver.run(args)
            self.assertFalse(json.loads((output / 'failed.json').read_text())['complete'])
            self.assertFalse((output / 'result.json').exists())


if __name__ == '__main__':
    unittest.main()
