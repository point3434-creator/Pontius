"""Actual engine menu, odd-chip ties, and no duplicate size-repair opportunities."""
import unittest
import stack_bridge as b


class StackTransfer(unittest.TestCase):
    def test_actual_menu_census(self):
        expected = [(279, 76, [76, 76]), (29, 186, [14, 29]),
                    (368, 44, [44, 44]), (318, 45, [45, 45])]
        for j, (pot, stack, sizes) in enumerate(expected):
            meta = b.admission(b.read(b.PRIOR/f'input-{j:03d}.json'))
            self.assertEqual((meta['pot'], meta['effective_stack'], meta['sizes']),
                             (pot, stack, sizes))
            self.assertEqual(meta['applicable'], len(set(sizes)) == 2)
            self.assertTrue(all(a in meta['legal_actions'] for a in meta['action_ids']))

    def test_literal_engine_settlement_and_ties(self):
        for j in range(4):
            record = b.read(b.PRIOR/f'input-{j:03d}.json')
            evidence = b.engine_audit(record)
            self.assertEqual(evidence['checks'], 15)
            self.assertEqual(evidence['outcomes'], [-1, 0, 1])
            self.assertEqual(evidence['tie_centered_chips'], .5 if j < 2 else 0.)

    def test_collapsed_sizes_refuse_solver_entry(self):
        for j in (0, 2, 3):
            with self.assertRaisesRegex(ValueError, 'one distinct'):
                b.build(b.read(b.PRIOR/f'input-{j:03d}.json'))

    def test_unchanged_ranges_and_groups(self):
        record = b.read(b.PRIOR/'input-001.json')
        game, groups, details = b.build(record)
        before = b.read(b.PRIOR/'case-001.json')
        self.assertEqual(groups, before['groups'])
        self.assertEqual(details['normalization'], '10/pot')
        self.assertEqual(game.check.shape, (1081, 1081))
        self.assertEqual(details['menu']['sizes'], [14, 29])
        self.assertEqual(details['joint_sha256'], before['inputs']['matrix_hashes']['joint'])


if __name__ == '__main__':
    unittest.main()
