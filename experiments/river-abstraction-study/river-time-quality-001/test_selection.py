import unittest
from selection import select


class SelectionTests(unittest.TestCase):
    def test_no_affordable_checkpoint_is_missing(self):
        self.assertIsNone(select([dict(iterations=2048, charged_seconds=3.01)], 3))

    def test_boundary_counts_and_selection_ignores_error(self):
        rows = [dict(iterations=2048, charged_seconds=2, error=.01),
                dict(iterations=4096, charged_seconds=3, error=.02)]
        self.assertEqual(select(rows, 3)['iterations'], 4096)

    def test_reordered_rows_and_costs(self):
        rows = [dict(iterations=8192, charged_seconds=5.1),
                dict(iterations=2048, charged_seconds=2),
                dict(iterations=4096, charged_seconds=4)]
        self.assertEqual(select(rows, 5)['iterations'], 4096)

    def test_no_checkpoint_and_invalid_budget(self):
        self.assertIsNone(select([], 3))
        with self.assertRaises(ValueError):
            select([], 0)

    def test_malformed_cost_or_iteration_fails_closed(self):
        for cost in (-1, float('nan'), float('inf'), True):
            with self.subTest(cost=cost), self.assertRaises(ValueError):
                select([dict(iterations=2048, charged_seconds=cost)], 3)
        for iteration in (True, 0, 2.5):
            with self.subTest(iteration=iteration), self.assertRaises(ValueError):
                select([dict(iterations=iteration, charged_seconds=1)], 3)

    def test_duplicate_iteration_is_ambiguous(self):
        with self.assertRaises(ValueError):
            select([dict(iterations=2048, charged_seconds=1)] * 2, 3)


if __name__ == '__main__':
    unittest.main()
