"""Single-size exact evaluation and full-hand LP identity checks."""
import unittest
import direct as d


class Direct(unittest.TestCase):
    def test_literal_one_and_two_bet_bounds(self):
        rng = d.np.random.default_rng(7291)
        for bets in (1, 2):
            a = rng.normal(size=(9, 11))*.01
            g = d.m.Game(a, d.np.full((bets, 9, 11), .01),
                         d.np.array([(s+2)*a for s in range(bets)]))
            x = rng.random((9, bets+1)).tolist()
            y = rng.random((bets, 11)).tolist()
            for gs in ([list(range(9)), list(range(11))],
                       [[i % 3 for i in range(9)], [j % 4 for j in range(11)]]):
                self.assertEqual(d.Kernel(g).bounds(g, x, y, gs),
                                 d.literal(g, x, y, gs))

    def test_all_four_actual_games_and_unchanged_two_size(self):
        for j, expected in enumerate((1, 2, 1, 1)):
            rec = d.read(d.b.PRIOR/f'input-{j:03d}.json')
            game, gs, meta = d.build(rec)
            self.assertEqual(len(game.fold), expected)
            self.assertEqual(game.check.shape, (1081, 1081))
            self.assertEqual(gs, d.read(d.b.PRIOR/f'case-{j:03d}.json')['groups'])
            if j == 1:
                prior, groups, _ = d.b.build(rec)
                for name in ('check', 'fold', 'call'):
                    self.assertTrue(d.np.array_equal(getattr(prior, name), getattr(game, name)))

    def test_lp_matches_literal_certificate(self):
        rng = d.np.random.default_rng(672)
        for bets in (1, 2):
            a = rng.normal(size=(8, 7))*.02
            game = d.m.Game(a, d.np.full((bets, 8, 7), .01),
                            d.np.array([(s+2)*a for s in range(bets)]))
            groups = [list(range(8)), list(range(7))]
            try:
                d.m.bounds = d.literal
                expected = d.m.pair(game, groups)
                d.m.bounds = d.Kernel(game).bounds
                self.assertEqual(d.m.pair(game, groups), expected)
            finally:
                d.m.bounds = d.literal


if __name__ == '__main__':
    unittest.main()
