"""New-board admission checks, before any evaluation of the frozen panel."""
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import subprocess
import confirmation as c


class AdmissionTests(unittest.TestCase):
    def test_selection_is_balanced_repeatable_and_fresh(self):
        first, receipt = c.select_boards([], per_texture=2)
        blocked = [c.canonical_board(b) for b in first]
        second, _ = c.select_boards(blocked, per_texture=2)
        self.assertEqual(c.select_boards([], per_texture=2), (first, receipt))
        self.assertEqual(len(second), 8)
        self.assertEqual({t: sum(c.texture(b) == t for b in second)
                          for t in c.TEXTURES}, {t: 2 for t in c.TEXTURES})
        self.assertTrue(set(map(c.canonical_board, second)).isdisjoint(blocked))
        self.assertEqual(len(set(map(c.canonical_board, second))), 8)

    def test_recursive_history_includes_training_and_exclusions(self):
        boards = [[0, 5, 10, 15, 20], [1, 4, 11, 14, 21]]
        payload = dict(training_cases=[dict(board=boards[0])], excluded_boards=[boards[1]])
        self.assertEqual(c.board_values(payload), boards)

    def test_suit_relabels_do_not_make_a_fresh_board(self):
        board = [0, 5, 10, 15, 20]
        relabeled = [4*(x//4)+(x%4+1)%4 for x in board]
        self.assertEqual(c.canonical_board(board), c.canonical_board(relabeled))

    def test_panel_has_exactly_the_declared_cells(self):
        boards, _ = c.select_boards([], per_texture=4)
        entries = c.entries_for(boards)
        self.assertEqual(len(entries), 64)
        self.assertEqual(len({(e['case']['id'], e['bet']) for e in entries}), 64)
        self.assertTrue(all(e['case']['pool'] == 0 for e in entries))
        self.assertEqual({e['bet'] for e in entries}, {5, 10})

    def test_run_refuses_bad_plan_digest_without_output(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'plan.json'
            c.write(path, dict(output=str(Path(td)/'out')))
            with self.assertRaises(ValueError):
                c.run(path, '0'*64)
            self.assertFalse((Path(td)/'out').exists())

    def test_failed_child_is_retained_and_cannot_be_relaunched(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            c.write(root/'plan.json', dict(output=str(root/'out'), phase_timeout_seconds=60))
            with patch.object(c, 'bindings'), patch.object(c.subprocess, 'run',
                    return_value=subprocess.CompletedProcess([], 9)) as launch:
                with self.assertRaises(ValueError):
                    c.run(root/'plan.json', c.digest(root/'plan.json'))
                self.assertTrue((root/'out/failed.json').exists())
                self.assertEqual(c.read(root/'out/worker-receipt.json')['exit'], 9)
                self.assertFalse((root/'out/receipt.json').exists())
                with self.assertRaises(FileExistsError):
                    c.run(root/'plan.json', c.digest(root/'plan.json'))
                self.assertEqual(launch.call_count, 1)


if __name__ == '__main__':
    unittest.main()
