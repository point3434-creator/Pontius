"""Controls for retaining the accepted state and fair continuation comparison."""
import unittest
from fractions import Fraction as Q
from unittest.mock import patch
import tempfile
from pathlib import Path
import subprocess
import experiment as e


class SecondStepTests(unittest.TestCase):
    def test_use_selected_state_not_unconditionally_repaired_groups(self):
        row = dict(gate=dict(groups=[[0, 1], [1, 0]], coefficients=[[.25, .75], [.6, .4]]),
                   proposal=dict(groups=[[1, 0], [0, 1]]))
        groups, coefficients = e.incumbent(row)
        self.assertEqual(groups, [[0, 1], [1, 0]])
        self.assertEqual(coefficients, [[.25, .75], [.6, .4]])

    def test_iteration_increment_excludes_reconstruction(self):
        records = [dict(iteration=10000, active_seconds=2., setup_seconds=1.),
                   dict(iteration=20000, active_seconds=5., setup_seconds=1.)]
        self.assertEqual(e.continuation_cost(records), 3.)

    def test_iteration_increment_rejects_wrong_budget(self):
        with self.assertRaises(ValueError):
            e.continuation_cost([dict(iteration=10000, active_seconds=2.),
                                 dict(iteration=50000, active_seconds=5.)])

    def test_bad_digest_refuses_before_claim(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'plan.json'
            e.write(path, dict(output=str(Path(td)/'out')))
            with self.assertRaises(AssertionError):
                e.run(path, '0'*64)
            self.assertFalse((Path(td)/'out').exists())

    def test_failed_child_is_preserved_and_never_relaunched(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'plan.json'
            e.write(path, dict(output=str(Path(td)/'out'), phase_timeout_seconds=60))
            with patch.object(e, 'bindings'), patch.object(e.subprocess, 'run',
                    return_value=subprocess.CompletedProcess([], 9)) as launch:
                with self.assertRaises(AssertionError):
                    e.run(path, e.digest(path))
                self.assertTrue((Path(td)/'out/failed.json').exists())
                with self.assertRaises(FileExistsError):
                    e.run(path, e.digest(path))
                self.assertEqual(launch.call_count, 1)


if __name__ == '__main__':
    unittest.main()
