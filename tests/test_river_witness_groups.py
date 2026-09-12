from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import importlib
import importlib.util
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from pontius.river_abstraction_study import PayoffGame

ENV = sys.version_info[:3] == (3, 14, 6) and importlib.util.find_spec('scipy') is not None
METHODS = ('exact', 'uniform_equity_200', 'range_equity', 'range_response')


def small_game():
    return PayoffGame(np.eye(3)/3, np.zeros((3, 3)), np.eye(3)/3,
                      np.diag([2/3, -2/3, 2/3]), None, 'three-hands')


def controls(matrix):
    from pontius.river_group_optimality import solve_groups
    groups = {m: ([0, 1, 2], [0, 1, 2]) if m == 'exact' else ([0, 0, 1], [0, 0, 1])
              for m in METHODS}
    bank = {'case': 'synthetic', 'methods': [
        dict(method=m, solution=solve_groups(matrix, groups[m]), saved=[]) for m in METHODS]}
    return groups, bank


@unittest.skipUnless(ENV, 'requires Python 3.14.6 and the research SciPy environment')
class WitnessGroupsTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('pontius.river_witness_groups'),
                             'witness action-value regrouping has not been implemented')
        return importlib.import_module('pontius.river_witness_groups')

    def test_hand_derived_action_advantages_and_reach_weighting(self):
        module = self.module()
        game = PayoffGame(np.eye(2)/2, np.zeros((2, 2)), np.eye(2)/2,
                          np.diag([1., -1.]), None, 'two-hands')
        np.testing.assert_array_equal(module.action_advantages(game, [[0, 1], [.5, .5]], 0),
                                      [[1, 1.5], [-2, -.5]])
        np.testing.assert_array_equal(module.action_advantages(game, [[1, .5], [0, 0]], 1),
                                      [[-1, 0], [1.5, 0]])
        scaled = PayoffGame(*(3*a for a in (game.joint, game.check, game.fold, game.call)),
                            None, 'scaled')
        np.testing.assert_array_equal(module.action_advantages(scaled, [[1, .5]], 1),
                                      [[-1], [1.5]])

    def test_dense_rectangular_game_includes_check_cost_and_both_players_signs(self):
        module = self.module()
        game = PayoffGame(np.array([[.1, .2, .2], [.2, .1, .2]]),
            np.array([[.1, -.2, .3], [-.4, .2, -.1]]),
            np.array([[.2, .4, .4], [.4, .2, .4]]),
            np.array([[.3, -.6, .6], [-.8, .3, -.6]]), None, 'rectangular')
        np.testing.assert_allclose(module.action_advantages(game, [[0, .5, 1]], 0),
                                   [[1], [.7]], atol=1e-14, rtol=0)
        np.testing.assert_allclose(module.action_advantages(game, [[1, .25]], 1),
                                   [[2/3], [3.25], [.125]], atol=1e-14, rtol=0)

    def test_regrouping_keeps_capacity_and_improves_known_synthetic_floor(self):
        module = self.module()
        matrix = small_game()
        groups, bank = controls(matrix)
        original = deepcopy(bank)
        proposal = module.propose(matrix, groups, bank)
        self.assertEqual(proposal['groups'][0][0], proposal['groups'][0][2])
        self.assertNotEqual(proposal['groups'][0][0], proposal['groups'][0][1])
        self.assertEqual([len(set(g)) for g in proposal['groups']], [2, 2])
        self.assertEqual(bank, original)
        from pontius.river_group_optimality import solve_groups
        solution = solve_groups(matrix, proposal['groups'])
        result = module.result_record(matrix, groups, bank, solution)
        self.assertLess(Q(result['comparisons']['range_equity']['upper_exact']), 0)
        self.assertEqual(result['comparisons']['range_equity']['classification'], 'lower')
        module.verify_record(matrix, groups, bank, result)

    def test_proposal_is_deterministic_without_optimizer_and_refuses_corrupt_bank(self):
        module = self.module()
        matrix = small_game()
        groups, bank = controls(matrix)
        with patch('pontius.river_group_optimality.linprog',
                   side_effect=AssertionError('LP forbidden')):
            first = module.propose(matrix, groups, bank)
            self.assertEqual(first, module.propose(matrix, groups, bank))
        for mutate in ('policy', 'duplicate', 'capacity'):
            broken, changed = deepcopy(bank), deepcopy(groups)
            if mutate == 'policy':
                broken['methods'][0]['solution']['seat0']['bet'][0] = -1
            elif mutate == 'duplicate':
                broken['methods'][1]['method'] = 'exact'
            else:
                changed['range_equity'] = ([0, 0, 0], [0, 0, 1])
            with self.assertRaises(ValueError):
                module.propose(matrix, changed, broken)

    def test_tied_features_keep_all_groups_and_zero_reach_is_valid(self):
        module = self.module()
        matrix = small_game()
        zero = np.zeros_like(matrix.joint)
        matrix = PayoffGame(matrix.joint, zero, zero, zero, None, 'zero')
        groups, bank = controls(matrix)
        proposal = module.propose(matrix, groups, bank)
        self.assertEqual([len(set(g)) for g in proposal['groups']], [2, 2])
        self.assertEqual(proposal['features'], [[[0.]*4]*3, [[0.]*4]*3])

    def test_bad_policy_zero_marginal_and_wrong_player_refused(self):
        module = self.module()
        matrix = small_game()
        for opponent in ([True, 0, 0], ['0', 0, 0], [float('nan'), 0, 0], [1.1, 0, 0], [0, 0]):
            with self.assertRaises((ValueError, TypeError)):
                module.action_advantages(matrix, [opponent], 0)
        with self.assertRaises(ValueError):
            module.action_advantages(matrix, [[0, 0, 0]], True)
        joint = matrix.joint.copy()
        joint[1] = 0
        invalid = PayoffGame(joint, matrix.check, matrix.fold, matrix.call, None, 'invalid')
        with self.assertRaises(ValueError):
            module.action_advantages(invalid, [[0, 0, 0]], 0)

    def test_parent_refuses_modified_features_groups_and_score(self):
        module = self.module()
        matrix = small_game()
        groups, bank = controls(matrix)
        proposal = module.propose(matrix, groups, bank)
        from pontius.river_group_optimality import solve_groups
        solution = solve_groups(matrix, proposal['groups'])
        result = module.result_record(matrix, groups, bank, solution)
        for field in ('features', 'groups', 'comparisons'):
            broken = deepcopy(result)
            if field == 'features':
                broken['proposal']['features'][0][0][0] += .1
            elif field == 'groups':
                broken['proposal']['groups'][0][0] = 9
            else:
                broken['comparisons']['range_equity']['upper_exact'] = '0'
            with self.assertRaises(ValueError):
                module.verify_record(matrix, groups, bank, broken)


@unittest.skipUnless(ENV, 'requires Python 3.14.6 and the research SciPy environment')
class WitnessToolTests(unittest.TestCase):
    def tool(self):
        path = Path(__file__).resolve().parents[1]/'tools/river_witness_groups.py'
        self.assertTrue(path.exists(), 'bounded witness grouping runner has not been implemented')
        spec = importlib.util.spec_from_file_location('witness_tool', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def prepare(self, tool, temp):
        # Reuse the existing two-hand fixture and its genuine retained producer.
        from test_river_group_optimality import DiagnosticToolTests
        helper = DiagnosticToolTests()
        helper.tool = tool.base
        helper.fixture_files(temp/'input')
        old_plan = tool.base.make_plan(temp/'bank', smoke_directory=temp/'input')
        tool.base.write_json(temp/'bank-plan.json', old_plan)
        digest = sha256((temp/'bank-plan.json').read_bytes()).hexdigest()
        tool.base.execute_plan(temp/'bank-plan.json', digest)
        return tool.make_plan(temp/'output', smoke_directory=temp/'input',
                              witness_directory=temp/'bank')

    def run_plan(self, tool, temp, plan, name='plan.json'):
        path = temp/name
        tool.base.write_json(path, plan)
        return tool.execute_plan(path, sha256(path.read_bytes()).hexdigest())

    def test_genuine_producer_to_regrouping_subprocess_and_parent(self):
        tool = self.tool()
        with tempfile.TemporaryDirectory() as d:
            temp = Path(d)
            plan = self.prepare(tool, temp)
            result = self.run_plan(tool, temp, plan)
            self.assertTrue(result['complete'])
            self.assertEqual(result['candidate_method_cases'], 1)
            self.assertEqual(result['lp_calls_planned'], 2)
            self.assertEqual(result['primary_control'], 'range_equity')
            self.assertTrue((temp/'output/manifest.json').exists())
            path = temp/'plan.json'
            with self.assertRaises(FileExistsError):
                tool.execute_plan(path, sha256(path.read_bytes()).hexdigest())

    def test_plan_admission_and_bank_drift_refuse_before_output(self):
        tool = self.tool()
        with tempfile.TemporaryDirectory() as d:
            temp = Path(d)
            plan = self.prepare(tool, temp)
            for field, value in [('mode', 'holdout'), ('hands', True), ('timeout_seconds', 999),
                                 ('unexpected', 1)]:
                broken = deepcopy(plan)
                broken[field] = value
                with self.assertRaises(ValueError):
                    self.run_plan(tool, temp, broken, field+'.json')
                self.assertFalse((temp/'output').exists())
            broken = deepcopy(plan)
            broken['sources']['src/pontius/river_witness_groups.py'] = '0'*64
            with self.assertRaises(ValueError):
                self.run_plan(tool, temp, broken, 'source.json')
            bank = Path(plan['cases'][0]['witness_file'])
            bank.write_bytes(bank.read_bytes()+b' ')
            with self.assertRaises(ValueError):
                self.run_plan(tool, temp, plan, 'drift.json')
            self.assertFalse((temp/'output').exists())

    def test_worker_failure_timeout_missing_result_and_parent_rejection(self):
        tool = self.tool()
        with tempfile.TemporaryDirectory() as d:
            temp = Path(d)
            plan = self.prepare(tool, temp)
            good = self.run_plan(tool, temp, plan)
            outcomes = [subprocess.CompletedProcess([], 9, b'o', b'e'),
                        subprocess.TimeoutExpired([], 120, b'o', b'e'),
                        subprocess.CompletedProcess([], 0, b'o', b'e')]
            for index, outcome in enumerate(outcomes):
                broken = deepcopy(plan)
                output = temp/f'failed-{index}'
                broken['output_directory'] = str(output)
                options = {'side_effect': outcome} if isinstance(outcome, Exception) else {
                    'return_value': outcome}
                with patch.object(tool.subprocess, 'run', **options):
                    errors = (ValueError, FileNotFoundError, subprocess.TimeoutExpired)
                    with self.assertRaises(errors):
                        self.run_plan(tool, temp, broken, f'failed-{index}.json')
                self.assertTrue((output/'failed.json').exists())
                self.assertFalse((output/'manifest.json').exists())
            broken = deepcopy(plan)
            broken['output_directory'] = str(temp/'tampered')
            def fake_worker(*args, **kwargs):
                record = deepcopy(good['cases'][0])
                record['proposal']['groups'][0][0] = 9
                tool.base.write_json(temp/'tampered/smoke.json', record)
                return subprocess.CompletedProcess([], 0, b'', b'')
            with patch.object(tool.subprocess, 'run', side_effect=fake_worker):
                with self.assertRaises(ValueError):
                    self.run_plan(tool, temp, broken, 'tampered.json')
            self.assertFalse((temp/'tampered/manifest.json').exists())
            self.assertTrue((temp/'tampered/failed.json').exists())

    def test_summary_uses_all_cases_exact_signed_intervals_and_no_selected_winner(self):
        tool = self.tool()
        results = []
        values = [Q(1, 10), Q(-2, 10), Q(3, 10), Q(-4, 10)]
        for label, value in zip(tool.IDS, values):
            results.append(dict(case=label, solution={'minimum_exploitability':
                tool.base.interval(Q(1), Q(1))}, comparisons={m:
                dict(**tool.base.interval(value, value), classification='lower' if value < 0
                     else 'higher') for m in METHODS}))
        summary = tool.summarize({'mode': 'development'}, results)
        self.assertEqual(Q(summary['comparisons']['range_equity']['lower_exact']), Q(-1, 20))
        self.assertEqual(summary['comparisons']['range_equity']['case_counts'],
                         {'lower': 2, 'higher': 2, 'overlapping': 0})
        with self.assertRaises(ValueError):
            tool.summarize({'mode': 'development'}, results[:-1])

    def test_summary_and_manifest_write_failures_are_not_complete(self):
        tool = self.tool()
        with tempfile.TemporaryDirectory() as d:
            temp = Path(d)
            plan = self.prepare(tool, temp)
            original = tool.base.write_json
            for name in ('summary.json', 'manifest.json'):
                output = temp/name.replace('.json', '')
                changed = deepcopy(plan)
                changed['output_directory'] = str(output)
                def write(path, value):
                    if path == output/name:
                        raise OSError('injected record failure')
                    return original(path, value)
                with patch.object(tool.base, 'write_json', side_effect=write):
                    with self.assertRaisesRegex(OSError, 'injected record failure'):
                        self.run_plan(tool, temp, changed, 'plan-'+name)
                self.assertFalse((output/'manifest.json').exists())
                self.assertTrue((output/'failed.json').exists())


if __name__ == '__main__':
    unittest.main()
