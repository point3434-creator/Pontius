from pathlib import Path
import tempfile
import unittest
import experiment as e
from fractions import Fraction as Q


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(getattr(e, 'make_plan', None)), 'runner is absent')

    def test_complete_synthetic_path_and_duplicate_refusal(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = e.make_plan(root/'out', synthetic=True)
            e.write(root/'plan.json', plan)
            e.run(root/'plan.json', e.digest(root/'plan.json'))
            self.assertEqual(e.read(root/'out/receipt.json')['exit'], 0)
            self.assertTrue(e.read(root/'out/audit.json')['passed'])
            for name, h in e.read(root/'out/results-manifest.json').items():
                self.assertEqual(e.digest(root/'out'/name), h)
            with self.assertRaises(FileExistsError):
                e.run(root/'plan.json', e.digest(root/'plan.json'))

    def test_changed_pin_refuses_before_claim(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = e.make_plan(root/'out', synthetic=True)
            source = root/'source.txt'
            source.write_text('before')
            plan['pins'][str(source)] = e.digest(source)
            e.write(root/'plan.json', plan)
            source.write_text('after')
            with self.assertRaises(ValueError):
                e.run(root/'plan.json', e.digest(root/'plan.json'))
            self.assertFalse((root/'out').exists())

    def test_missing_row_and_corrupt_operation_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = e.make_plan(root, synthetic=True)
            e.worker(plan, root)
            path = root/'case-000.json'
            raw = path.read_bytes()
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                e.verify(plan, root)
            path.write_bytes(raw)
            row = e.read(path)
            row['proposal']['seats'][0]['net_witness_gain_exact'] = '999'
            e.write(path, row)
            with self.assertRaises(ValueError):
                e.verify(plan, root)

    def test_summary_keeps_certified_bounds_and_long_control_separate(self):
        def row(lo, hi, fixed, longer, repaired):
            def floor(a, b):
                return dict(minimum_exploitability=dict(lower_exact=str(a), upper_exact=str(b)))
            def score(value):
                return dict(exact_exploitability=str(value))
            return dict(baseline=floor(lo, hi), solution=floor(lo-1, hi-1),
                proposal=dict(seats=[dict(changed=True), dict(changed=False)]),
                records=dict(control=[score(fixed), score(longer)],
                             repaired=[score(repaired+1), score(repaired)]))
        actual = e.statistics([row(1, 2, 3, Q(5, 2), 2), row(2, 3, 4, 3, 3)])
        self.assertEqual(Q(actual['floor_delta']['lower_exact']), -2)
        self.assertEqual(Q(actual['floor_delta']['upper_exact']), 0)
        self.assertEqual(Q(actual['actual_delta_exact']), -1)
        self.assertEqual(Q(actual['versus_50k_exact']), -Q(1, 4))
        self.assertEqual(actual['changed_seats'], 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
