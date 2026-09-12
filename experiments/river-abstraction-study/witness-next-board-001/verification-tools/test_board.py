"""Selection and novelty refusal checks, with no game evaluation."""
import unittest
import experiment as e


class BoardChecks(unittest.TestCase):
    def test_first_selection_and_exclusion(self):
        first = e.select([])
        self.assertEqual(first['attempt'], 0)
        second = e.select([first['board']])
        self.assertGreater(second['attempt'], first['attempt'])
        self.assertNotEqual(e.c.canonical_board(first['board']),
                            e.c.canonical_board(second['board']))

    def test_suit_relabel_is_refused(self):
        board = [0, 5, 10, 15, 20]
        relabeled = [4*(v//4)+(v%4+1)%4 for v in board]
        with self.assertRaises(AssertionError):
            e.novelty(dict(selection=dict(board=board), excluded_boards=[relabeled]))
        e.novelty(dict(selection=dict(board=board), excluded_boards=[[0, 4, 8, 12, 24]]))


if __name__ == '__main__':
    unittest.main()
