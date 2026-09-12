from pathlib import Path
from unittest.mock import patch
import tempfile
import subprocess
import unittest
import experiment as e


class RunnerTests(unittest.TestCase):
    def test_selection_balanced_repeatable_and_suit_fresh(self):
        first, receipt = e.select_boards([])
        self.assertEqual(e.select_boards([]), (first, receipt))
        second, _ = e.select_boards(first)
        self.assertEqual(len(second), 16)
        self.assertEqual(len(set(map(e.c.canonical_board, second))), 16)
        self.assertTrue(set(map(e.c.canonical_board, first)).isdisjoint(
            map(e.c.canonical_board, second)))
        self.assertEqual({t: sum(e.c.texture(b) == t for b in second) for t in e.c.TEXTURES},
                         {t: 4 for t in e.c.TEXTURES})

    def test_bad_plan_digest_refuses_before_claim(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'plan.json'
            e.write(p, dict(output=str(Path(td)/'out')))
            with self.assertRaises(AssertionError):
                e.run(p, '0'*64)
            self.assertFalse((Path(td)/'out').exists())

    def test_failed_child_retained_and_duplicate_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root/'plan.json'
            e.write(p, dict(output=str(root/'out'), phase_timeout_seconds=60))
            with patch.object(e, 'bindings'), patch.object(e.subprocess, 'run',
                    return_value=subprocess.CompletedProcess([], 9)) as launch:
                with self.assertRaises(AssertionError):
                    e.run(p, e.digest(p))
                self.assertTrue((root/'out/failed.json').exists())
                self.assertFalse((root/'out/receipt.json').exists())
                self.assertEqual(e.read(root/'out/worker-receipt.json')['exit'], 9)
                with self.assertRaises(FileExistsError):
                    e.run(p, e.digest(p))
                self.assertEqual(launch.call_count, 1)


if __name__ == '__main__':
    unittest.main()
