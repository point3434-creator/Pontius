import unittest
from analysis import crossing


class Metrics(unittest.TestCase):
    def test_censoring_and_sampled_reversal(self):
        records = [dict(iteration=i, residual_interval=['0', v], solver_seconds=[i, i],
                        scoring_seconds=.1) for i, v in enumerate(['.1', '.01', '.1', '.005'], 1)]
        self.assertIsNone(crossing(records, '.001', False))
        self.assertEqual(crossing(records, '.02', False)['iteration'], 2)
        self.assertEqual(crossing(records, '.02', True)['iteration'], 4)
        self.assertAlmostEqual(crossing(records, '.02', True)['monitored_seconds'], 4.4)


if __name__ == '__main__':
    unittest.main()
