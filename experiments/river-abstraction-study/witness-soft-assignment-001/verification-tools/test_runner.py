"""Exercise the real synthetic runner and refusal/reconstruction boundaries."""
import json
from pathlib import Path
import tempfile
import unittest
import experiment as e
from fractions import Fraction as Q


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(getattr(e, 'make_plan', None)), 'runner is absent')

    def test_full_synthetic_run_and_duplicate_refusal(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = e.make_plan(root/'output', synthetic=True)
            e.write(root/'plan.json', plan)
            e.run(root/'plan.json', e.digest(root/'plan.json'))
            receipt = e.read(root/'output/receipt.json')
            self.assertEqual(receipt['exit'], 0)
            self.assertTrue(e.read(root/'output/audit.json')['passed'])
            manifest = e.read(root/'output/results-manifest.json')
            for name, expected in manifest.items():
                self.assertEqual(e.digest(root/'output'/name), expected)
            with self.assertRaises(FileExistsError):
                e.run(root/'plan.json', e.digest(root/'plan.json'))

    def test_wrong_plan_digest_and_input_pin_refuse_without_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = e.make_plan(root/'output', synthetic=True)
            e.write(root/'plan.json', plan)
            with self.assertRaises(ValueError):
                e.run(root/'plan.json', '0'*64)
            self.assertFalse((root/'output').exists())
            changed = root/'input.txt'
            changed.write_text('a')
            plan['pins'][str(changed)] = e.digest(changed)
            e.write(root/'plan.json', plan)
            changed.write_text('b')
            with self.assertRaises(ValueError):
                e.run(root/'plan.json', e.digest(root/'plan.json'))
            self.assertFalse((root/'output').exists())

    def test_verifier_rejects_missing_case_and_tampered_policy_without_lp(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = e.make_plan(root, synthetic=True)
            e.worker(plan, root)
            path = root/'cell-000.json'
            original = path.read_bytes()
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                e.verify(plan, root)
            path.write_bytes(original)
            row = json.loads(original)
            row['methods']['hard']['records'][0]['coefficients'][0][0] = .123456789
            e.write(path, row)
            with self.assertRaises(ValueError):
                e.verify(plan, root)

    def test_paired_summary_uses_bounds_and_all_timer_repeats(self):
        def method(lo, hi, actual, timed):
            return dict(solution=dict(minimum_exploitability=dict(
                lower_exact=str(lo), upper_exact=str(hi))),
                records=[dict(exact_exploitability=str(actual))],
                timed=[dict(exact_exploitability=str(v)) for v in timed])
        rows = [dict(methods=dict(hard=method(1, 2, 3, [2, 3, 4]),
                                  soft=method(0, 1, 2, [1, 2, 3]))),
                dict(methods=dict(hard=method(2, 3, 4, [3, 4, 5]),
                                  soft=method(1, 2, 2, [1, 1, 1])))]
        result = e.statistics(rows)
        self.assertEqual(Q(result['floor_delta']['lower_exact']), -2)
        self.assertEqual(Q(result['floor_delta']['upper_exact']), 0)
        self.assertEqual(Q(result['actual_delta_exact']), -Q(3, 2))
        self.assertEqual(Q(result['timed_delta_exact']), -2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
