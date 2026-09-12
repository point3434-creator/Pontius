"""Public/private separation, payoff semantics, and native evaluator ordering."""
import ast
import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import inputs as i
from support import m, np, c, EXTERNAL
from exact_kernel import Kernel


class Assigner:
    def bucket(self, hole, board):
        return (hole[0]+3*hole[1]) % 7


class Policy:
    config = dict(num_players=6, stack=200, sb=1, bb=2,
                  menu=[[[1.0], [.5], [.5], [.5]], 3, 1.0])

    def probabilities_with_status(self, game, bucket=None):
        v = np.arange(1, len(game.legal_actions())+1, dtype=float)
        v[1] += bucket
        return (v/v.sum()).tolist(), 'trained'


def example():
    p = Policy()
    g = i.engine(p)
    deck = random.Random(571).sample(range(52), 17)
    g.reset(deck=deck)
    actions = []
    while g.street < 3:
        a = 0 if g.street == 0 and g.current >= 2 else 1
        actions.append(a)
        g.step(a)
    return p, dict(hand_index=0, deck=deck, actions=actions, seats=g.active_players(),
        current=g.current, board=g.board, pot=g.pot, stacks=g.stacks[:],
        committed=g.committed[:], history=g.history[:])


class Inputs(unittest.TestCase):
    def test_private_cards_do_not_enter_ranges(self):
        p, row = example()
        a = i.reconstruct(p, Assigner(), row)
        deck = [v for v in range(52) if v not in row['board']][-12:]+row['board']
        b = i.reconstruct(p, Assigner(), dict(row, deck=deck))
        self.assertEqual(a['ranges'], b['ranges'])
        self.assertEqual(len(a['hands']), 1081)
        self.assertTrue(all(not set(h) & set(row['board']) for h in a['hands']))
        self.assertEqual(a['role_seats'][0], row['current'])

    def test_unchanged_state_required_and_no_target_replacement(self):
        p, row = example()
        with self.assertRaises(AssertionError):
            i.reconstruct(p, Assigner(), dict(row, pot=row['pot']+1))
        p.act, p.statuses = lambda g: 0, {}
        with patch.object(i, 'MAX_HANDS', 3):
            result = i.capture(p)
        self.assertFalse(result['complete'])
        self.assertEqual(result['census']['hands'], 3)
        self.assertEqual(result['rows'], [])

    def test_literal_payoffs_on_full_game_subset(self):
        p, row = example()
        record = i.reconstruct(p, Assigner(), row)
        game, groups, _ = i.build(record)
        h = record['hands']
        for a, b in ((0, 1), (7, 254), (560, 1077), (900, 14)):
            if set(h[a]) & set(h[b]):
                self.assertEqual(game.fold[0, a, b], 0)
            else:
                sign = np.sign(i.evaluator.hand_rank(h[a]+row['board'])-
                               i.evaluator.hand_rank(h[b]+row['board']))
                w = game.fold[0, a, b]/5
                self.assertEqual(game.check[a, b], w*sign*5)
                self.assertEqual(game.call[0, a, b], w*sign*10)
                self.assertEqual(game.call[1, a, b], w*sign*15)
        take = [0, 7, 254, 560, 900, 1077]
        sub = m.Game(game.check[np.ix_(take, take)],
                     game.fold[:, take][:, :, take], game.call[:, take][:, :, take])
        x, y = [[.1, .3, .6]]*6, [[.1]*6, [.75]*6]
        self.assertEqual(Kernel(sub).bounds(sub, x, y, [list(range(6))]*2),
                         m.bounds(sub, x, y, [list(range(6))]*2))

    def test_native_order_and_exact_ties_against_python_reference(self):
        tree = ast.parse((EXTERNAL/'pluribus_lite/evaluator.py').read_text())
        body = [v for v in tree.body if isinstance(v, ast.If)][-1]
        functions = [v for v in body.body if isinstance(v, ast.FunctionDef)]
        from itertools import combinations
        ns = dict(combinations=combinations)
        exec(compile(ast.Module(body=functions, type_ignores=[]), 'reference', 'exec'), ns)
        rng = random.Random(1517)
        cards = [rng.sample(range(52), 7) for _ in range(300)]
        cards += [[32, 36, 40, 44, 48, 1, 6], [32, 36, 40, 44, 48, 9, 14]]
        native = [i.evaluator.hand_rank(h) for h in cards]
        literal = [ns['hand_rank'](h) for h in cards]
        self.assertEqual(sorted(range(len(cards)), key=native.__getitem__),
                         sorted(range(len(cards)), key=literal.__getitem__))
        self.assertEqual(native[-1], native[-2])
        self.assertEqual(literal[-1], literal[-2])


if __name__ == '__main__':
    unittest.main()
