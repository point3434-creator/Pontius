from __future__ import annotations

from fractions import Fraction
import importlib
import importlib.util
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np

from pontius.river_abstraction_study import PayoffGame
from pontius.river import RiverHoldem, make_hole, parse_cards


def fixture():
    # V(x,y) = x0*(1/2 + y0/2) + x1*(1/2 - 3*y1/2).
    # Full value is 1/2. Restricting x0=x1 lowers maximin to 0;
    # restricting y0=y1 raises minimax to 2/3 (at y=1/3).
    return PayoffGame(np.eye(2) / 2, np.zeros((2, 2)), np.eye(2) / 2,
                      np.diag([1.0, -1.0]), None, 'synthetic')


RESEARCH_ENV = sys.version_info[:3] == (3, 14, 6) and importlib.util.find_spec('scipy') is not None


@unittest.skipUnless(RESEARCH_ENV, 'requires the pinned Python 3.14 research LP environment')
class OptimalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.import_module('pontius.river_group_optimality')

    def test_known_restriction_cost_for_each_seat(self):
        for groups, expected in [(([0, 1], [0, 1]), Fraction(0)),
                                 (([0, 0], [0, 1]), Fraction(1, 4)),
                                 (([0, 1], [0, 0]), Fraction(1, 12)),
                                 (([0, 0], [0, 0]), Fraction(1, 3))]:
            result = self.module.solve_groups(fixture(), groups)
            lower = Fraction(result['minimum_exploitability']['lower_exact'])
            upper = Fraction(result['minimum_exploitability']['upper_exact'])
            self.assertLessEqual(lower, expected)
            self.assertGreaterEqual(upper, expected)
            self.assertLessEqual(upper - lower, Fraction(1, 10**8))
            self.assertEqual(self.module.verify_solution(fixture(), groups, result),
                             result['minimum_exploitability'])

    def test_certificate_matches_enumerated_pure_responses(self):
        matrix = fixture()
        x, y = [0.7, 0.2], [0.4, 0.8]
        for groups in [([0, 1], [0, 1]), ([0, 0], [0, 1])]:
            if groups[0] == [0, 0]:
                x = [0.7, 0.7]
            lower, upper = self.module.saddle_bounds(matrix, x, y, groups)
            def value(bet, call):
                a, b = map(Fraction, bet)
                c, d = map(Fraction, call)
                return a * (Fraction(1, 2) + c / 2) + b * (Fraction(1, 2) - 3 * d / 2)
            xs = [[p[g] for g in groups[0]] for p in product((0, 1), repeat=max(groups[0])+1)]
            ys = [[p[g] for g in groups[1]] for p in product((0, 1), repeat=max(groups[1])+1)]
            self.assertEqual(lower, min(value(x, p) for p in ys))
            self.assertEqual(upper, max(value(p, y) for p in xs))

    def test_certificate_refuses_infeasible_or_non_grouped_policy(self):
        for x in ([0.2, 0.3], [-1e-12, -1e-12], [float('nan'), 0], [True, True], ['0.2', '0.2']):
            with self.assertRaises(ValueError):
                self.module.saddle_bounds(fixture(), x, [0.5, 0.5], ([0, 0], [0, 1]))

    def test_saved_policy_gap_and_tampered_certificate(self):
        matrix, groups = fixture(), ([0, 0], [0, 0])
        result = self.module.solve_groups(matrix, groups)
        comparison = self.module.compare_saved(matrix, groups, result, [0, 0], [0, 0])
        self.assertEqual(Fraction(comparison['saved_exploitability_exact']), Fraction(1, 2))
        self.assertLessEqual(Fraction(comparison['avoidable_gap']['lower_exact']), Fraction(1, 6))
        self.assertGreaterEqual(Fraction(comparison['avoidable_gap']['upper_exact']),
                                Fraction(1, 6))
        result['seat0']['bet'][0] = 0.5
        with self.assertRaises(ValueError):
            self.module.verify_solution(matrix, groups, result)

    def test_degenerate_game_and_invalid_groups(self):
        zero = np.zeros((2, 2))
        matrix = PayoffGame(np.eye(2)/2, zero, zero, zero, None, 'zero')
        result = self.module.solve_groups(matrix, ([0, 0], [0, 0]))
        self.assertEqual(result['minimum_exploitability']['upper_exact'], '0')
        for groups in [([0, 2], [0, 1]), ([0, 1], [0]), ([0.0, 1.0], [0, 1])]:
            with self.assertRaises(ValueError):
                self.module.solve_groups(matrix, groups)

    def test_unsuccessful_solver_and_uncertified_witness_are_refused(self):
        with patch.object(self.module, 'linprog', return_value=SimpleNamespace(success=False)):
            with self.assertRaisesRegex(ValueError, 'LP did not terminate'):
                self.module.solve_groups(fixture(), ([0, 1], [0, 1]))
        result = self.module.solve_groups(fixture(), ([0, 1], [0, 1]))
        result['seat0']['bet'] = [0, 0]
        with self.assertRaises(ValueError):
            self.module.verify_solution(fixture(), ([0, 1], [0, 1]), result)


@unittest.skipUnless(RESEARCH_ENV, 'requires the pinned Python 3.14 research LP environment')
class DiagnosticToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'tools/river_group_optimality.py'
        spec = importlib.util.spec_from_file_location('group_tool', path)
        cls.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.tool)

    def fixture_files(self, directory):
        directory.mkdir()
        ranges = ({make_hole('Ts', 'Ks'): 1, make_hole('Ah', '3h'): 1},
                  {make_hole('Ac', 'Ad'): 1, make_hole('4s', '5s'): 1})
        game = RiverHoldem.from_independent_ranges(
            board=parse_cards('2c', '7d', '9h', 'Js', 'Qc'), pot=10, stacks=(20, 20),
            bet_size=5, player0_weights=ranges[0], player1_weights=ranges[1])
        matrix = PayoffGame.from_river(game)
        groups = {m: [[0, 1], [0, 1]] for m in self.tool.METHODS}
        inputs = dict(board=list(game.board), pot=10, bet=5, stacks=[20, 20],
                      provenance_digest=game.provenance_digest,
                      ranges=[[[list(h), w] for h, w in sorted(r.items())] for r in ranges],
                      hands=[[list(h) for h in pool] for pool in matrix.hands],
                      joint=matrix.joint.tolist(), groups=groups)
        records = [dict(method=m, iteration=10, occupied_groups=[2, 2],
                        group_bet=[0.5, 0.5], group_call=[0.5, 0.5],
                        hand_bet=[0.5, 0.5], hand_call=[0.5, 0.5],
                        full_game=matrix.evaluate([0.5, 0.5], [0.5, 0.5]))
                   for m in self.tool.METHODS]
        values = {'inputs.json': inputs, 'result.json': dict(complete=True, records=records,
                  accepted_joint_deals=len(game.deals)),
                  'started.json': dict(board=list(game.board), regime='uniform',
                                       hands_per_player=2, iterations=10)}
        for name, value in values.items():
            self.tool.write_json(directory / name, value)
        self.tool.write_json(directory / 'manifest.json', {
            name: sha256((directory / name).read_bytes()).hexdigest() for name in values})

    def test_bound_smoke_and_saved_policy_reconciliation(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            self.fixture_files(temp / 'input')
            plan = self.tool.make_plan(temp / 'output', smoke_directory=temp / 'input')
            self.tool.write_json(temp / 'plan.json', plan)
            digest = sha256((temp / 'plan.json').read_bytes()).hexdigest()
            summary = self.tool.execute_plan(temp / 'plan.json', digest)
            self.assertTrue(summary['complete'])
            self.assertEqual(summary['verified_method_cases'], 4)
            self.assertEqual(summary['verified_saved_profiles'], 4)
            self.assertEqual(set(summary['cohorts']['smoke']), set(self.tool.METHODS))
            self.assertTrue((temp / 'output/manifest.json').exists())
            with self.assertRaises(FileExistsError):
                self.tool.execute_plan(temp / 'plan.json', digest)
            records = json.loads((temp / 'input/result.json').read_bytes())
            records['records'][0]['hand_bet'] = [0.9, 0.5]
            (temp / 'input/result.json').write_text(json.dumps(records))
            case = self.tool.bind_case('smoke', temp / 'input')
            with self.assertRaises(ValueError):
                self.tool.load_case(case, hands=2, steps=[10])

    def test_failed_worker_timeout_and_missing_results_never_complete(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            self.fixture_files(temp / 'input')
            outcomes = [subprocess.CompletedProcess([], 9, b'o', b'e'),
                        subprocess.TimeoutExpired([], 300, b'o', b'e'),
                        subprocess.CompletedProcess([], 0, b'o', b'e')]
            for index, outcome in enumerate(outcomes):
                output = temp / f'output-{index}'
                plan = self.tool.make_plan(output, smoke_directory=temp / 'input')
                path = temp / f'plan-{index}.json'
                self.tool.write_json(path, plan)
                digest = sha256(path.read_bytes()).hexdigest()
                options = {'side_effect': outcome} if isinstance(outcome, Exception) else {
                    'return_value': outcome}
                with patch.object(self.tool.subprocess, 'run', **options):
                    errors = (ValueError, subprocess.TimeoutExpired, FileNotFoundError)
                    with self.assertRaises(errors):
                        self.tool.execute_plan(path, digest)
                self.assertFalse((output / 'summary.json').exists())
                self.assertFalse((output / 'manifest.json').exists())
                self.assertFalse(json.loads((output / 'failed.json').read_bytes())['complete'])
                self.assertEqual((output / 'stderr.txt').read_bytes(), b'e')

    def test_reports_cohorts_and_checkpoints_without_pooling(self):
        results = []
        for index, label in enumerate(self.tool.IDS, 1):
            floor = self.tool.interval(Fraction(index, 100), Fraction(index, 100))
            rows = [dict(method=m, solution={'minimum_exploitability': floor}, saved=[
                dict(iteration=n, saved_exploitability_exact=str(Fraction(index, 100) + n),
                     avoidable_gap=self.tool.interval(Fraction(n), Fraction(n)))
                for n in (100, 1000, 10000)]) for m in self.tool.METHODS]
            results.append(dict(case=label, methods=rows))
        result = self.tool.summarize(dict(mode='observed', steps=[100, 1000, 10000]), results)
        self.assertEqual(result['verified_saved_profiles'], 96)
        self.assertEqual(result['headline_iteration'], 10000)
        for cohort, expected in [('development', Fraction(1, 40)), ('holdout', Fraction(13, 200))]:
            for record in result['cohorts'][cohort].values():
                self.assertEqual(Fraction(record['minimum_exploitability']['lower_exact']),
                                 expected)
                for n in (100, 1000, 10000):
                    self.assertEqual(Fraction(record['checkpoints'][str(n)]['saved_exact']),
                                     expected+n)

    def test_admission_refuses_changed_sources_and_input_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            self.fixture_files(temp / 'input')
            plan = self.tool.make_plan(temp / 'output', smoke_directory=temp / 'input')
            plan['sources']['src/pontius/river.py'] = '0'*64
            self.tool.write_json(temp / 'plan.json', plan)
            digest = sha256((temp / 'plan.json').read_bytes()).hexdigest()
            with self.assertRaises(ValueError):
                self.tool.execute_plan(temp / 'plan.json', digest)
            self.assertFalse((temp / 'output').exists())
            case = self.tool.bind_case('smoke', temp / 'input')
            (temp / 'input/inputs.json').write_bytes(b'{}')
            with self.assertRaises(ValueError):
                self.tool.load_case(case, hands=2, steps=[10])


if __name__ == '__main__':
    unittest.main()
