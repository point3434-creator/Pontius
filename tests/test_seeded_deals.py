"""Fixed seed correctness vectors; no generated poker hands are executed."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'tools/v0a_seeded_deals.py'
FIXTURES = ROOT / 'tests/fixtures/seeded_deals'
SEED = '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f'


def load_tool():
    spec = importlib.util.spec_from_file_location('seeded_under_test', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
            + '\n').encode('utf-8')


def admit(raw):
    # An ordinary public Admission loads the unchanged host and actual card contract.
    root = ROOT
    if root.drive.upper() != 'D:':
        # Hosted CI checks out on C:; the sealed Admission requires a D-local clone.
        root = Path(tempfile.mkdtemp(prefix='seeded-admission-', dir='D:/'))/'source'
        git = Path(os.environ['PONTIUS_GIT'])
        if not git.is_absolute() or not git.is_file():
            raise AssertionError('admission clone requires absolute Git')
        head = subprocess.run([str(git), '--no-replace-objects', '-C', str(ROOT),
                               'rev-parse', 'HEAD'], capture_output=True, check=True).stdout.strip()
        subprocess.run([str(git), '--no-replace-objects', 'clone', '--quiet', '--no-hardlinks',
                        '--no-checkout', str(ROOT), str(root)], capture_output=True, check=True)
        subprocess.run([str(git), '--no-replace-objects', '-C', str(root), '-c',
                        'core.autocrlf=false', 'checkout', '--quiet', '--detach', head.decode()],
                       capture_output=True, check=True)
    environment = os.environ.copy()
    environment['PYTHONPATH'] = str(root/'src')
    script = '''
import importlib.util, json, sys
from pathlib import Path
root = Path.cwd()
spec = importlib.util.spec_from_file_location('session_check', root/'tools/v0a_table_session.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
admission = m.Admission(root)
schedule = m.Schedule(sys.stdin.buffer.read(16385), admission.host, admission.modules)
rows = []
for h in range(len(schedule.hands)):
    config, raw = schedule.derive(h, [200]*6, h % 6)
    rows.append(json.loads(raw))
admission.check()
print(json.dumps(rows))
'''
    return subprocess.run([sys.executable, '-B', '-P', '-c', script], input=raw,
                          cwd=root, env=environment, capture_output=True, timeout=120)


class SeededDealsTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(TOOL.is_file(), 'approved seeded dealer is absent')
        self.m = load_tool()

    def test_literal_three_hand_vector_and_canonical_bytes(self):
        # Wrong digest packing, shuffle direction or seat mapping changes literal bytes.
        expected = (FIXTURES / 'expected_session.json').read_bytes()
        self.assertEqual(encoded(self.m.generate_session(SEED, 3)), expected)
        hands = json.loads(expected)['hands']
        for h in range(3):
            self.assertEqual(self.m.deal_for_hand(SEED, h), hands[h])

    def test_full_permutation_projection_and_rotating_deal_order(self):
        for h in range(16):
            deck = self.m._deck(bytes.fromhex(SEED), h)
            self.assertEqual(sorted(deck), list(range(52)))
            hand = self.m.deal_for_hand(SEED, h)
            self.assertEqual(set(hand), {'private_hands', 'board_runout'})
            flat = sum(hand['private_hands'], []) + hand['board_runout']
            self.assertEqual(len(flat), 17)
            self.assertEqual(len(set(flat)), 17)
            self.assertTrue(all(type(c) is int and 0 <= c < 52 for c in flat))
            self.assertEqual(hand['board_runout'], deck[12:17])
            for offset in range(6):
                self.assertEqual(hand['private_hands'][(h + 1 + offset) % 6],
                                 sorted([deck[offset], deck[offset + 6]]))

    def test_prefix_independence_and_fresh_mutable_containers(self):
        expected = self.m.generate_session(SEED, 16)
        for count in (1, 3, 16):
            self.assertEqual(self.m.generate_session(SEED, count)['hands'],
                             expected['hands'][:count])
        for h in reversed(range(16)):
            self.assertEqual(self.m.deal_for_hand(SEED, h), expected['hands'][h])
        first = self.m.generate_session(SEED, 3)
        first['hands'][0]['private_hands'][0][0] = -1
        first['hands'][1]['board_runout'].clear()
        first['starting_stacks'][0] = 0
        first['opponents'][0] = 'changed'
        self.assertEqual(self.m.generate_session(SEED, 3)['hands'], expected['hands'][:3])
        self.assertEqual(self.m.generate_session(SEED, 1)['starting_stacks'], [200]*6)
        self.assertEqual(self.m.generate_session(SEED, 1)['opponents'][0], 'passive')

    def test_no_ambient_rng_state_and_cross_hand_cards_may_repeat(self):
        state = random.getstate()
        try:
            random.seed(2)
            before = random.getstate()
            first = self.m.generate_session(SEED, 3)
            self.assertEqual(random.getstate(), before)
            random.seed(900)
            self.assertEqual(self.m.generate_session(SEED, 3), first)
        finally:
            random.setstate(state)
        cards = [set(sum(h['private_hands'], []) + h['board_runout']) for h in first['hands']]
        self.assertTrue(cards[0] & cards[1])

    def test_exact_public_types_seed_and_index_bounds(self):
        for seed in (None, True, 1, b'0'*64, '', '0'*63, '0'*65, 'G'*64, 'A'*64, SEED+'\n'):
            for function in (self.m.deal_for_hand, self.m.generate_session):
                with self.subTest(seed=seed), self.assertRaises(self.m.Refusal) as caught:
                    function(seed, 1)
                self.assertEqual(caught.exception.code, 'input_invalid')
        for function, bad in ((self.m.deal_for_hand, (-1, 16, True, 1.0, '1', None)),
                              (self.m.generate_session, (0, 17, True, 1.0, '1', None))):
            for value in bad:
                with self.subTest(value=value), self.assertRaises(self.m.Refusal) as caught:
                    function(SEED, value)
                self.assertEqual(caught.exception.code, 'input_invalid')

    def test_rejection_threshold_consumption_and_exhaustion(self):
        # For b=52, L=4294967248. Accept L-1, reject L and UINT32_MAX.
        self.assertEqual(self.m._index(iter([4294967247]), 52), 51)
        words = iter([4294967248, 4294967295, 4294967248, 53, 17])
        self.assertEqual(self.m._index(words, 52), 1)
        self.assertEqual(next(words), 17)
        with self.assertRaises(self.m.Refusal) as caught:
            self.m._index(iter([4294967295]*1024), 52)
        self.assertEqual(caught.exception.code, 'generation_limit')
        words = list(self.m._words(bytes.fromhex(SEED), 0))
        self.assertEqual(len(words), 1024)
        with patch.object(self.m, '_words', return_value=iter([4294967295]*1024)):
            with self.assertRaises(self.m.Refusal) as caught:
                self.m.deal_for_hand(SEED, 0)
        self.assertEqual(caught.exception.code, 'generation_limit')

    def test_known_answer_rejects_semantically_shifted_hand_index(self):
        original = self.m._words
        with patch.object(self.m, '_words', side_effect=lambda seed, h: original(seed, h+1)):
            with self.assertRaises(AssertionError):
                self.assertEqual(encoded(self.m.generate_session(SEED, 3)),
                                 (FIXTURES / 'expected_session.json').read_bytes())

    def test_real_session_and_table_input_admit_each_bounded_count(self):
        for count in (1, 3, 16):
            generated = self.m.generate_session(SEED, count)
            result = admit(encoded(generated))
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = json.loads(result.stdout)
            self.assertEqual(len(rows), count)
            for h, row in enumerate(rows):
                self.assertEqual(row['button'], h % 6)
                self.assertEqual(row['private_hands'], generated['hands'][h]['private_hands'])
                self.assertEqual(row['board_runout'], generated['hands'][h]['board_runout'])
                self.assertNotIn('seed', row)


if __name__ == '__main__':
    unittest.main()
