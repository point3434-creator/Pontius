from collections import Counter
from copy import deepcopy
import importlib
import importlib.util
import json
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from pontius.river_abstraction_study import DEVELOPMENT_BOARDS, HOLDOUT_BOARDS, uniform_equities
from pontius import river_witness_pilot as pilot

ENV = sys.version_info[:3] == (3,14,6) and importlib.util.find_spec('scipy') is not None


@unittest.skipUnless(ENV, 'requires pinned Python 3.14.6 research environment')
class DistillationTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('pontius.river_witness_distillation'),
                             'witness feature predictor is not implemented')
        return importlib.import_module('pontius.river_witness_distillation')

    def test_reserved_boards_exclude_all_observed_suit_classes(self):
        m = self.module()
        boards = m.select_boards()
        self.assertEqual(boards,m.select_boards())
        self.assertEqual(Counter(pilot.texture(b) for b in boards),
                         {name:2 for name in pilot.TEXTURES})
        old = {pilot.canonical_board(b) for b in (
            *DEVELOPMENT_BOARDS,*HOLDOUT_BOARDS,*pilot.select_boards())}
        self.assertTrue({pilot.canonical_board(b) for b in boards}.isdisjoint(old))
        self.assertEqual(len({pilot.canonical_board(b) for b in boards}),8)

    def test_polynomial_design_and_weighted_ridge_have_hand_checked_solution(self):
        m = self.module()
        x = np.zeros((2,11))
        x[:,0] = [0,1]
        design = m.design(x)
        self.assertEqual(design.shape,(2,78))
        np.testing.assert_array_equal(design[0],np.r_[1,np.zeros(77)])
        self.assertEqual(np.flatnonzero(design[1]).tolist(),[0,1,12])
        targets = np.tile([[2.],[6.]],(1,4))
        # x and x^2 are identical columns. Weighted Var(x)=3/16.
        # Sum of their fitted coefficients is 4*Var/(Var+lambda/2).
        model = m.fit_model([(x,targets,np.array([.75,.25]))])
        slope = 4*(3/16)/((3/16)+.001/2)
        expected = np.tile([[3-slope/4],[3+3*slope/4]],(1,4))
        np.testing.assert_allclose(m.predict(model,x),expected,rtol=0,atol=1e-11)
        repeated = m.fit_model([(x,targets,np.array([.75,.25]))]*2)
        np.testing.assert_allclose(m.predict(repeated,x),expected,atol=1e-11)
        bad = deepcopy(model)
        bad['coefficients'][0][0] = float('nan')
        with self.assertRaises(ValueError):
            m.predict(bad,x)
        with self.assertRaises(ValueError):
            m.fit_model([(x,targets,np.array([1.,0.]))])

    def test_raw_features_use_only_equity_and_range_context(self):
        m = self.module()
        case = pilot.case_grid([DEVELOPMENT_BOARDS[0]])[0]
        equities = uniform_equities(case['board'])
        matrix,_,_ = pilot.build_inputs(case,2,equities)
        for player in (0,1):
            x = m.raw_features(matrix,equities,player)
            self.assertEqual(x.shape,(2,11))
            joint = matrix.joint if player == 0 else matrix.joint.T
            check = matrix.check if player == 0 else -matrix.check.T
            expected_equity = ((joint*((check > 0)+.5*(check == 0))).sum(axis=1)
                               /joint.sum(axis=1))
            np.testing.assert_allclose(x[:,9],expected_equity)
            np.testing.assert_allclose(x[:,10],[equities[h] for h in matrix.hands[player]])
            np.testing.assert_allclose(x[:,[0,3,6]].sum(axis=1),1)

    def test_proposal_never_needs_teacher_and_parent_rejects_corruption(self):
        m = self.module()
        case = pilot.case_grid([DEVELOPMENT_BOARDS[0]])[0]
        equities = uniform_equities(case['board'])
        matrix,groups,_ = pilot.build_inputs(case,2,equities)
        teacher = pilot.solve_record(case,2,equities)
        models = m.fit_models([(matrix,equities,teacher)])
        with patch('pontius.river_group_optimality.linprog',
                   side_effect=AssertionError('prediction cannot solve')):
            proposal = m.propose(matrix,groups,equities,models)
        self.assertEqual([len(set(g)) for g in proposal['groups']],
                         [len(set(g)) for g in groups['uniform_equity_200']])
        record = m.solve_record(case,2,equities,models)
        with patch('pontius.river_group_optimality.linprog',
                   side_effect=AssertionError('parent cannot solve')):
            m.verify_record(case,2,equities,models,record)
        for field in ('prediction','groups','comparison','teacher','timing'):
            broken = deepcopy(record)
            if field == 'prediction':
                broken['student']['proposal']['features'][0][0][0] += .1
            elif field == 'groups':
                broken['student']['proposal']['groups'][0][0] = 99
            elif field == 'comparison':
                broken['student']['comparisons']['range_equity']['upper_exact'] = '100'
            elif field == 'teacher':
                broken['teacher']['inputs']['joint'][0][0] += .1
            else:
                broken['seconds']['prediction_and_clustering'] = -1
            with self.assertRaises(ValueError):
                m.verify_record(case,2,equities,models,broken)

    def test_summary_reports_student_and_oracle_without_ratio_on_zero_gain(self):
        m = self.module()
        case = pilot.case_grid([DEVELOPMENT_BOARDS[0]])[0]
        equities = uniform_equities(case['board'])
        matrix,_,_ = pilot.build_inputs(case,2,equities)
        teacher = pilot.solve_record(case,2,equities)
        models = m.fit_models([(matrix,equities,teacher)])
        row = m.solve_record(case,2,equities,models)
        summary = m.summarize([case],[row])
        self.assertEqual(summary['lp_calls_planned'],12)
        self.assertEqual(summary['student']['case_count'],1)
        self.assertEqual(summary['oracle']['case_count'],1)
        self.assertEqual(len(summary['prediction_errors']),1)
        self.assertNotIn('gain_capture_percent',summary)
        with self.assertRaises(ValueError):
            m.summarize([case],[])


@unittest.skipUnless(ENV, 'requires pinned Python 3.14.6 research environment')
class DistillationToolTests(unittest.TestCase):
    def tool(self):
        path = Path(__file__).resolve().parents[1]/'tools/river_witness_distillation.py'
        self.assertTrue(path.exists(), 'distillation runner is not implemented')
        spec = importlib.util.spec_from_file_location('distill_tool',path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self, tool, directory):
        training = directory/'training'
        training.mkdir()
        producer = tool.old.make_plan(directory/'unused-producer-output',smoke=True)
        case = producer['cases'][0]
        teacher = pilot.solve_record(case,2,uniform_equities(case['board']))
        tool.base.write_json(training/'plan.json',producer)
        tool.base.write_json(training/(case['id']+'.json'),teacher)
        return tool.make_plan(directory/'output',smoke=True,training=training)

    def invoke(self, tool, directory, plan, name='plan'):
        path = directory/(name+'.json')
        tool.base.write_json(path,plan)
        return tool.execute_plan(path,sha256(path.read_bytes()).hexdigest())

    def test_full_plan_only_hashes_and_selects_without_fitting_or_equities(self):
        tool = self.tool()
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)/'not-created'
            with patch.object(tool.student,'fit_models',side_effect=AssertionError('no fitting')):
                with patch.object(tool.old,'equities_for',side_effect=AssertionError('no scoring')):
                    plan = tool.make_plan(output)
                    tool.verify_bindings(plan)
            self.assertEqual(len(plan['training_cases']),48)
            self.assertEqual(len(plan['cases']),48)
            self.assertEqual(len(plan['training']['files']),65)
            self.assertEqual(plan['lp_calls'],576)
            self.assertFalse(output.exists())

    def test_binding_refuses_recipe_source_training_drift_before_output(self):
        tool = self.tool()
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            plan = self.fixture(tool,directory)
            for index,field in enumerate(('alpha','case','source','training','hands','timeout')):
                bad = deepcopy(plan)
                if field == 'alpha':
                    bad['alpha'] = .01
                elif field == 'case':
                    bad['cases'][0]['board'] = list(DEVELOPMENT_BOARDS[0])
                elif field == 'source':
                    bad['sources']['src/pontius/river_witness_distillation.py'] = '0'*64
                elif field == 'training':
                    bad['training']['files']['plan.json'] = '0'*64
                elif field == 'hands':
                    bad['hands'] = True
                else:
                    bad['timeout_seconds'] += 1
                with self.assertRaises(ValueError):
                    self.invoke(tool,directory,bad,str(index))
                self.assertFalse((directory/'output').exists())
            target = directory/'training'/ (plan['training_cases'][0]['id']+'.json')
            target.write_bytes(target.read_bytes()+b' ')
            with self.assertRaises(ValueError):
                self.invoke(tool,directory,plan)
            self.assertFalse((directory/'output').exists())

    def test_two_hand_full_process_and_parent_refuses_wrong_model(self):
        tool = self.tool()
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            plan = self.fixture(tool,directory)
            result = self.invoke(tool,directory,plan)
            self.assertTrue(result['complete'])
            self.assertEqual(result['lp_calls_planned'],12)
            self.assertTrue((directory/'output/manifest.json').exists())
            with self.assertRaises(FileExistsError):
                tool.execute_plan(directory/'plan.json',
                                  sha256((directory/'plan.json').read_bytes()).hexdigest())
            plan['output_directory'] = str(directory/'corrupt')
            def fake(*args,**kwargs):
                out = Path(plan['output_directory'])
                model = json.loads((directory/'output/models.json').read_bytes())
                model['models'][0]['coefficients'][0][0] += 1
                tool.base.write_json(out/'models.json',model)
                return subprocess.CompletedProcess([],0,b'',b'')
            with patch.object(tool.subprocess,'run',side_effect=fake):
                with self.assertRaises(ValueError):
                    self.invoke(tool,directory,plan,'corrupt-plan')
            self.assertTrue((directory/'corrupt/failed.json').exists())
            self.assertFalse((directory/'corrupt/manifest.json').exists())

    def test_failed_worker_timeout_and_manifest_error_never_complete(self):
        tool = self.tool()
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            plan = self.fixture(tool,directory)
            outcomes = [subprocess.CompletedProcess([],1,b'',b''),
                        subprocess.TimeoutExpired([],1200,b'',b'')]
            for i,outcome in enumerate(outcomes):
                plan['output_directory'] = str(directory/f'failed-{i}')
                options = {'side_effect':outcome} if isinstance(outcome,Exception) else {
                    'return_value':outcome}
                with patch.object(tool.subprocess,'run',**options):
                    with self.assertRaises((ValueError,subprocess.TimeoutExpired)):
                        self.invoke(tool,directory,plan,f'failure-{i}')
                self.assertFalse((directory/f'failed-{i}/manifest.json').exists())
            original = tool.base.write_json
            plan['output_directory'] = str(directory/'write-failed')
            def failed_write(path,value):
                if path.name == 'manifest.json':
                    path.write_bytes(b'{')
                    raise OSError('injected partial manifest write')
                original(path,value)
            with patch.object(tool.base,'write_json',side_effect=failed_write):
                with self.assertRaises(OSError):
                    self.invoke(tool,directory,plan,'write-failed-plan')
            self.assertTrue((directory/'write-failed/failed.json').exists())
            with self.assertRaises(json.JSONDecodeError):
                json.loads((directory/'write-failed/manifest.json').read_bytes())
