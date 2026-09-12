from __future__ import annotations

import importlib.util
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pontius.river_abstraction_study import HOLDOUT_BOARDS, study_case

ROOT = Path(__file__).resolve().parents[1]


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HoldoutAdmissionTests(unittest.TestCase):
    def test_declared_boards_and_default_refusal(self):
        self.assertEqual(HOLDOUT_BOARDS, ((4, 5, 26, 35, 49), (11, 19, 27, 33, 42)))
        with self.assertRaises(ValueError):
            study_case(HOLDOUT_BOARDS[0])
        with self.assertRaises(ValueError):
            study_case((0, 1, 2, 3, 4), split='holdout')
        with self.assertRaises(ValueError):
            study_case(HOLDOUT_BOARDS[0], split='unknown')

    def test_explicit_holdout_routes_to_preparation_without_evaluating_it(self):
        with patch('pontius.river_abstraction_study.uniform_equities',
                   side_effect=RuntimeError('stop before card evaluation')) as preparation:
            with self.assertRaisesRegex(RuntimeError, 'stop before card evaluation'):
                study_case(HOLDOUT_BOARDS[0], split='holdout')
            preparation.assert_called_once_with(HOLDOUT_BOARDS[0])

    def test_driver_dispatch_and_complete_normalized_fields(self):
        driver = load_tool('river_abstraction_study')
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'development'
            driver.run(SimpleNamespace(output=output, board=0, hands=2, regime='uniform',
                                       iterations=10, split='development'))
            result = json.loads((output / 'result.json').read_text())
            self.assertEqual(result['split'], 'development')
            for record in result['records']:
                for field in ('full_game', 'restricted_game'):
                    self.assertEqual(record[field + '_fraction_of_pot'],
                                     {k: v / 10 for k, v in record[field].items()})
            holdout = Path(temporary) / 'holdout'
            with patch.object(driver, 'study_case', side_effect=RuntimeError('unopened')) as build:
                with self.assertRaisesRegex(RuntimeError, 'unopened'):
                    driver.run(SimpleNamespace(output=holdout, board=1, hands=96,
                                               regime='polarized', iterations=10000,
                                               split='holdout'))
                self.assertEqual(build.call_args.args[0], HOLDOUT_BOARDS[1])
            self.assertFalse((holdout / 'result.json').exists())

    def test_development_strategy_and_groups_match_saved_prechange_smoke(self):
        driver = load_tool('river_abstraction_study')
        saved = ROOT / 'docs/research/river-abstraction-study-checks/development-smoke'
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'parity'
            driver.run(SimpleNamespace(output=output, board=0, hands=16, regime='uniform',
                                       iterations=100, split='development'))
            self.assertEqual(json.loads((output / 'inputs.json').read_text()),
                             json.loads((saved / 'inputs.json').read_text()))
            actual = json.loads((output / 'result.json').read_text())['records']
            original = json.loads((saved / 'result.json').read_text())['records']
            for a, b in zip(actual, original, strict=True):
                for key in ('method', 'iteration', 'group_bet', 'group_call', 'hand_bet',
                            'hand_call', 'full_game', 'restricted_game', 'occupied_groups'):
                    self.assertEqual(a[key], b[key])


class CampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_tool('river_abstraction_campaign')

    def save_plan(self, path, plan):
        raw = (json.dumps(plan, sort_keys=True) + '\n').encode()
        path.write_bytes(raw)
        return sha256(raw).hexdigest()

    def test_holdout_plan_is_fixed_without_opening_holdout(self):
        plan = self.runner.make_plan(Path('unused-holdout').resolve())
        self.assertEqual(plan['split'], 'holdout')
        self.assertEqual((plan['hands'], plan['iterations']), (96, 10000))
        self.assertEqual(len(plan['cases']), 4)
        for field, value in [('hands', 95), ('iterations', 9999), ('case_timeout_seconds', True),
                             ('cases', plan['cases'][:3]), ('split', 'anything')]:
            with self.assertRaises(ValueError):
                self.runner.validate_plan(dict(plan, **{field: value}))

    def test_duplicate_keys_and_nonfinite_json_refused(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}'):
            with self.assertRaises(ValueError):
                self.runner.parse_json(raw)

    def test_small_development_campaign_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            output = temp / 'trial'
            plan = self.runner.make_plan(output, split='development', hands=2, iterations=10)
            digest = self.save_plan(temp / 'plan.json', plan)
            summary = self.runner.execute_plan(temp / 'plan.json', digest)
            self.assertTrue(summary['complete'])
            self.assertEqual(len(summary['records']), 16)
            self.assertEqual(set(summary['mean_full_exploitability']), {'10'})
            before = (output / 'summary.json').read_bytes()
            with self.assertRaises(FileExistsError):
                self.runner.execute_plan(temp / 'plan.json', digest)
            self.assertEqual(before, (output / 'summary.json').read_bytes())
            case = plan['cases'][0]
            directory = output / case['id']
            result = json.loads((directory / 'result.json').read_text())
            result['records'][0]['full_game']['exploitability'] += 0.1
            (directory / 'result.json').write_text(json.dumps(result))
            manifest = json.loads((directory / 'manifest.json').read_text())
            manifest['result.json'] = sha256((directory / 'result.json').read_bytes()).hexdigest()
            (directory / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                self.runner.verify_case(directory, plan, case)
            result['records'] = result['records'][:-1]
            (directory / 'result.json').write_text(json.dumps(result))
            manifest['result.json'] = sha256((directory / 'result.json').read_bytes()).hexdigest()
            (directory / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                self.runner.verify_case(directory, plan, case)

    def test_plan_digest_and_source_drift_refuse_before_output_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            output = temp / 'run'
            plan = self.runner.make_plan(output, split='development', hands=2, iterations=10)
            self.save_plan(temp / 'plan.json', plan)
            with self.assertRaises(ValueError):
                self.runner.execute_plan(temp / 'plan.json', '0' * 64)
            plan['source_sha256']['src/pontius/river_abstraction_study.py'] = '0' * 64
            digest = self.save_plan(temp / 'plan.json', plan)
            with self.assertRaises(ValueError):
                self.runner.execute_plan(temp / 'plan.json', digest)
            self.assertFalse(output.exists())

    def test_timeout_and_failed_child_stop_the_campaign(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            for label, outcome in [('failed', subprocess.CompletedProcess([], 7, b'out', b'err')),
                                   ('timeout', subprocess.TimeoutExpired([], 60, b'out', b'err'))]:
                plan = self.runner.make_plan(
                    temp / label, split='development', hands=2, iterations=10)
                path = temp / (label + '.json')
                digest = self.save_plan(path, plan)
                kwargs = {'side_effect': outcome} if isinstance(outcome, Exception) else {
                    'return_value': outcome}
                with patch.object(self.runner.subprocess, 'run', **kwargs) as child:
                    with self.assertRaises((RuntimeError, subprocess.TimeoutExpired)):
                        self.runner.execute_plan(path, digest)
                    self.assertEqual(child.call_count, 1)
                self.assertFalse((temp / label / 'summary.json').exists())
                failure = json.loads((temp / label / 'failed.json').read_text())
                self.assertFalse(failure['complete'])


if __name__ == '__main__':
    unittest.main()
