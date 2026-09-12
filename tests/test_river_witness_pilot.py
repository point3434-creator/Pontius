from collections import Counter
from copy import deepcopy
from fractions import Fraction as Q
import importlib
import importlib.util
from hashlib import sha256
from itertools import permutations
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pontius.river import parse_cards
from pontius.river_abstraction_study import DEVELOPMENT_BOARDS, HOLDOUT_BOARDS, uniform_equities

ENV = sys.version_info[:3] == (3, 14, 6) and importlib.util.find_spec('scipy') is not None


@unittest.skipUnless(ENV, 'requires pinned Python 3.14.6 research environment')
class PilotTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('pontius.river_witness_pilot'),
                             'fresh-board and hand-pool pilot is not implemented')
        return importlib.import_module('pontius.river_witness_pilot')

    def test_panel_has_eight_fresh_suit_classes_and_two_per_texture(self):
        module = self.module()
        boards = module.select_boards()
        self.assertEqual(boards, module.select_boards())
        self.assertEqual(len(boards), 8)
        self.assertEqual(Counter(module.texture(b) for b in boards),
                         {name: 2 for name in module.TEXTURES})
        old = {module.canonical_board(b) for b in (*DEVELOPMENT_BOARDS, *HOLDOUT_BOARDS)}
        fresh = {module.canonical_board(b) for b in boards}
        self.assertEqual(len(fresh), 8)
        self.assertTrue(fresh.isdisjoint(old))
        for b in boards:
            for permutation in permutations(range(4)):
                changed = [4*(c//4)+permutation[c%4] for c in b]
                self.assertEqual(module.canonical_board(changed), module.canonical_board(b))

    def test_texture_partition_and_invalid_cards(self):
        module = self.module()
        examples = [('2c 4d 6h 8s Tc', 'unpaired-no-flush'),
                    ('2c 4c 6c 8s Td', 'unpaired-flush-possible'),
                    ('2c 2d 6h 8s Tc', 'one-pair'),
                    ('2c 2d 6h 6s Tc', 'multiple-pairs-or-trips')]
        for cards, category in examples:
            self.assertEqual(module.texture(parse_cards(*cards.split())), category)
        for board in ([0]*5, [0, 1, 2, 3, 52], [False, 1, 2, 3, 4], [0, 1]):
            with self.assertRaises(ValueError):
                module.canonical_board(board)

    def test_three_pool_draws_are_reproducible_legal_and_shared_between_regimes(self):
        module = self.module()
        board = DEVELOPMENT_BOARDS[0]
        draws = []
        for seed in range(3):
            for player in (0, 1):
                pool = module.hand_pool(board, seed, player, 96)
                self.assertEqual(pool, module.hand_pool(board, seed, player, 96))
                self.assertEqual(len(pool), 96)
                self.assertEqual(len(set(pool)), 96)
                self.assertTrue(all(len(set(h)) == 2 and set(h).isdisjoint(board) for h in pool))
                draws.append(pool)
        self.assertEqual(len(set(draws)), 6)
        cases = module.case_grid(module.select_boards())
        self.assertEqual(len(cases), 48)
        self.assertEqual(len({c['id'] for c in cases}), 48)
        for first, second in zip(cases[::2], cases[1::2]):
            self.assertEqual(first['board'], second['board'])
            self.assertEqual(first['pool'], second['pool'])
            self.assertEqual((first['regime'], second['regime']), ('uniform', 'polarized'))

    def test_two_hand_generation_certification_and_parent_validation(self):
        module = self.module()
        case = module.case_grid([DEVELOPMENT_BOARDS[0]])[0]
        equities = uniform_equities(case['board'])
        record = module.solve_record(case, 2, equities)
        self.assertEqual(record['case'], case)
        with patch('pontius.river_group_optimality.linprog', side_effect=AssertionError('no LP')):
            module.verify_record(case, 2, equities, record)
        polarized = dict(case, regime='polarized')
        _, _, weighted = module.build_inputs(polarized, 2, equities)
        self.assertEqual(record['inputs']['hands'], weighted['hands'])
        for target in ('inputs', 'candidate', 'bank'):
            broken = deepcopy(record)
            if target == 'inputs':
                broken[target]['joint'][0][0] += .01
            elif target == 'candidate':
                broken[target]['proposal']['groups'][0][0] = 99
            else:
                broken[target]['methods'][0]['solution']['seat0']['bet'][0] = -1
            with self.assertRaises(ValueError):
                module.verify_record(case, 2, equities, broken)

    def test_board_level_aggregation_retains_pool_variation_and_missingness_fails(self):
        module = self.module()
        cases = module.case_grid(module.select_boards())
        rows = []
        for case in cases:
            value = Q(case['board_index']+1) + Q(case['pool'], 10)
            candidate = module.interval(value, value)
            controls = [dict(method=m, solution={
                'minimum_exploitability':module.interval(Q(1), Q(1))})
                        for m in module.METHODS]
            comparisons = {m: dict(**module.interval(value-1, value-1),
                                    classification='higher' if value > 1 else 'overlapping')
                           for m in module.METHODS}
            rows.append(dict(case=case, bank={'methods':controls}, candidate={
                'solution':{'minimum_exploitability':candidate}, 'comparisons':comparisons}))
        result = module.summarize(cases, rows)
        self.assertEqual(result['board_units'], 8)
        self.assertEqual(result['case_count'], 48)
        self.assertEqual(Q(result['overall']['comparisons']['range_equity']['lower_exact']),
                         Q(18,5))
        self.assertEqual(len(result['boards']), 8)
        self.assertEqual(len(result['leave_one_board_out']), 8)
        for row in result['boards']:
            self.assertAlmostEqual(row['pool_sd_chips']['range_equity'], .1)
        with self.assertRaises(ValueError):
            module.summarize(cases, rows[:-1])
        with self.assertRaises(ValueError):
            module.summarize(cases, [rows[0]]+rows[:-1])


@unittest.skipUnless(ENV, 'requires pinned Python 3.14.6 research environment')
class PilotToolTests(unittest.TestCase):
    def tool(self):
        path = Path(__file__).resolve().parents[1]/'tools/river_witness_pilot.py'
        self.assertTrue(path.exists(), 'bounded pilot driver is not implemented')
        spec = importlib.util.spec_from_file_location('pilot_tool',path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def invoke(self, tool, directory, plan, name):
        path = directory/(name+'.json')
        tool.base.write_json(path,plan)
        return tool.execute_plan(path,sha256(path.read_bytes()).hexdigest())

    def test_full_plan_is_selection_only_and_refuses_changed_grid_sources_and_limits(self):
        tool = self.tool()
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            with patch.object(tool,'uniform_equities',side_effect=AssertionError('no scoring')):
                plan = tool.make_plan(directory/'output')
                tool.verify_bindings(plan)
            self.assertEqual(len(plan['cases']),48)
            self.assertEqual(plan['lp_calls'],480)
            for label in ('grid','source','timeout','hands'):
                broken = deepcopy(plan)
                if label == 'grid':
                    broken['cases'][0]['pool'] = 1
                elif label == 'source':
                    broken['sources']['src/pontius/river_witness_pilot.py'] = '0'*64
                elif label == 'timeout':
                    broken['timeout_seconds'] += 1
                else:
                    broken['hands'] = True
                with self.assertRaises(ValueError):
                    self.invoke(tool,directory,broken,label)
                self.assertFalse((directory/'output').exists())

    def test_real_two_hand_smoke_and_parent_rejection(self):
        tool = self.tool()
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            plan = tool.make_plan(directory/'output',smoke=True)
            result = self.invoke(tool,directory,plan,'smoke')
            self.assertTrue(result['complete'])
            self.assertEqual((result['case_count'],result['board_units']), (1,1))
            self.assertEqual(result['lp_calls_planned'],10)
            self.assertTrue((directory/'output/manifest.json').exists())
            path = directory/'smoke.json'
            with self.assertRaises(FileExistsError):
                tool.execute_plan(path,sha256(path.read_bytes()).hexdigest())
            output = directory/'corrupt'
            plan['output_directory'] = str(output)
            def fake(*args, **kwargs):
                row = deepcopy(result['cases'][0])
                row['candidate']['proposal']['groups'][0][0] = 100
                tool.base.write_json(output/(plan['cases'][0]['id']+'.json'),row)
                return subprocess.CompletedProcess([],0,b'',b'')
            with patch.object(tool.subprocess,'run',side_effect=fake):
                with self.assertRaises(ValueError):
                    self.invoke(tool,directory,plan,'corrupt')
            self.assertFalse((output/'manifest.json').exists())
            self.assertTrue((output/'failed.json').exists())

    def test_failure_timeout_missing_output_and_evidence_errors_never_succeed(self):
        tool = self.tool()
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            for index,outcome in enumerate([subprocess.CompletedProcess([],1,b'o',b'e'),
                subprocess.TimeoutExpired([],1200,b'o',b'e'),
                subprocess.CompletedProcess([],0,b'o',b'e')]):
                output = directory/f'failed-{index}'
                plan = tool.make_plan(output,smoke=True)
                options = {'side_effect':outcome} if isinstance(outcome,Exception) else {
                    'return_value':outcome}
                with patch.object(tool.subprocess,'run',**options):
                    with self.assertRaises((ValueError,FileNotFoundError,
                                            subprocess.TimeoutExpired)):
                        self.invoke(tool,directory,plan,f'failed-{index}')
                self.assertTrue((output/'failed.json').exists())
                self.assertFalse((output/'manifest.json').exists())
            original = tool.base.write_json
            for name in ('summary.json','manifest.json'):
                output = directory/name.removesuffix('.json')
                plan = tool.make_plan(output,smoke=True)
                def write(path,value):
                    if path == output/name:
                        raise OSError('injected record failure')
                    return original(path,value)
                with patch.object(tool.base,'write_json',side_effect=write):
                    with self.assertRaisesRegex(OSError,'injected record failure'):
                        self.invoke(tool,directory,plan,'plan-'+name)
                self.assertTrue((output/'failed.json').exists())
                self.assertFalse((output/'manifest.json').exists())


if __name__ == '__main__':
    unittest.main()
