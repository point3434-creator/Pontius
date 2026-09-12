"""Analytic update checks, legacy equivalence, and a tiny zero-sum game."""
import unittest
import numpy as np
from variants import update, Trainer, m


class Updates(unittest.TestCase):
    def test_plain_retains_negative_regret(self):
        np.testing.assert_array_equal(update(np.array([2., -2.]), np.array([-3., 3.]),
                                            1, 'rm'), [-1., 1.])

    def test_plus_clips_after_addition(self):
        np.testing.assert_array_equal(update(np.array([2., 0.]), np.array([-3., 1.]),
                                            1, 'rm_plus'), [0., 1.])

    def test_discount_uses_updated_sign_and_one_based_time(self):
        np.testing.assert_array_equal(update(np.array([-2., 2.]), np.array([3., -3.]),
                                            1, 'discounted'), [.5, -.5])
        np.testing.assert_allclose(update(np.array([0., 0.]), np.array([9., -2.]),
                                          4, 'discounted'), [8., -1.], rtol=0, atol=0)

    def test_reject_unknown_variant(self):
        with self.assertRaises(ValueError):
            update(np.zeros(2), np.zeros(2), 1, 'unknown')

    @staticmethod
    def game():
        return m.Game([[.2, -.3], [-.1, .4]],
                      [[[.5, .2], [.3, .6]], [[.5, .2], [.3, .6]]],
                      [[[.8, -.7], [-.4, .9]], [[1.2, -1.1], [-.8, 1.3]]])

    def test_plain_bit_identical_to_frozen_trainer(self):
        a, b = Trainer(self.game(), [[0, 1], [0, 1]], 'rm'), m.Trainer(
            self.game(), [[0, 1], [0, 1]])
        for _ in range(500):
            a.step()
            b.step()
        self.assertEqual(a.average(), b.average())
        for x, y in zip(a.regrets, b.regrets):
            np.testing.assert_array_equal(x, y)

    def test_quadratic_average(self):
        for mode in ('rm_plus', 'discounted'):
            a = Trainer(self.game(), [[0, 1], [0, 1]], mode)
            history = []
            for _ in range(4):
                history.append([m.match(r) for r in a.regrets])
                a.step()
            x, y = a.average()
            expected = [sum((t*t*h[s] for t, h in enumerate(history, 1))) / 30
                        for s in (0, 1)]
            np.testing.assert_allclose(x, expected[0], rtol=0, atol=1e-15)
            np.testing.assert_allclose(y, expected[1][:, :, 1], rtol=0, atol=1e-15)

    def test_small_game_certificate(self):
        game, groups = self.game(), [[0, 1], [0, 1]]
        for mode in ('rm', 'rm_plus', 'discounted'):
            a = Trainer(game, groups, mode)
            for _ in range(5000):
                a.step()
            x, y = a.average()
            self.assertLess(m.score(game, groups, x, y)['exploitability'], .025)


if __name__ == '__main__':
    unittest.main()
