from __future__ import annotations
import hashlib
import json
from pathlib import Path
import unittest
from pontius.hand_scenario import codec

FIXTURES = Path(__file__).with_name('fixtures') / 'hand_adapter'


def document(name='raise'):
    return json.loads((FIXTURES / f'{name}_scenario.json').read_bytes())


def wire(value):
    return json.dumps(value, ensure_ascii=True).encode('ascii')


class ScenarioTests(unittest.TestCase):
    def test_literal_cards_all_permutations_and_immutable_values(self):
        seen = set()
        for number in range(1000):
            data = document()
            data['case_id'] = f'v0a-hand-adapter-correctness-suits-{number}'
            label = 'pontius-v0a-hand-adapter-v1/' + data['case_id']
            index = int.from_bytes(hashlib.sha256(label.encode()).digest()[:8], 'big') % 24
            if index in seen:
                continue
            seen.add(index)
            data['hands'][0].reverse()
            scenario = codec.decode_scenario(wire(data))
            deal = scenario.fixture.deal()
            self.assertEqual(tuple(deal.hand(s) for s in range(6)),
                             ((49, 51), (45, 46), (27, 35), (0, 12), (6, 50), (11, 19)))
            self.assertEqual(deal.board_runout, (20, 25, 30, 39, 40))
            self.assertEqual(scenario.expected_actions, (('preflop', 'raise', 6, 'table_hit'),))
            self.assertEqual(scenario.fixture.seed_label, label)
            self.assertEqual(scenario.fixture.hand_id, data['case_id'])
            self.assertRaises(AttributeError, setattr, scenario, 'fixture', None)
        self.assertEqual(len(seen), 24)

    def test_closed_schema_each_field_type_and_object_boundary(self):
        def visit(value, path=()):
            if isinstance(value, dict):
                yield path, value
                for key, child in value.items():
                    yield from visit(child, path + (key,))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    yield from visit(child, path + (index,))
        for path, obj in visit(document()):
            changes = [(field, ...) for field in obj] + [(field, {}) for field in obj]
            for field, value in (*changes, ('unknown', 0)):
                data = document()
                target = data
                for part in path:
                    target = target[part]
                if value is ...:
                    del target[field]
                else:
                    target[field] = value
                with self.subTest(path=path, field=field):
                    self.assertRaises(codec.ScenarioError, codec.decode_scenario, wire(data))
            encoded = wire(obj)
            duplicate = encoded[:-1] + b',' + wire(next(iter(obj))) + b':null}'
            raw = wire(document()).replace(encoded, duplicate, 1)
            self.assertNotEqual(raw, wire(document()))
            self.assertRaises(codec.ScenarioError, codec.decode_scenario, raw)

    def test_scalar_card_array_enum_and_wire_refusals(self):
        cases = [('button', True), ('controlled_seat', 6), ('small_blind', 2),
                 ('big_blind', 201), ('case_id', 'v0a-hand-adapter-correctness-'),
                 ('case_id', 'v0a-hand-adapter-correctness-\ud800'), ('version', 'v2'),
                 ('starting_stacks', [200] * 5), ('starting_stacks', [True] * 6),
                 ('hands', [['As', 'As']] * 6), ('hands', [['As']] * 6),
                 ('board', ['7c', '8d', '9h', 'Js', 'As']), ('board', ['xx'] * 5),
                 ('board', ['7c'] * 4), ('small_blind', -1), ('small_blind', 1.0)]
        for key, value in cases:
            data = document()
            data[key] = value
            self.assertRaises(codec.ScenarioError, codec.decode_scenario, wire(data))
        for key, values in {'street': ['fifth', None], 'seat': [3, True, -1],
                            'kind': ['bet', None], 'raise_to': [6, True]}.items():
            for value in values:
                data = document()
                data['opponent_actions'][0][key] = value
                self.assertRaises(codec.ScenarioError, codec.decode_scenario, wire(data))
        raw = wire(document())
        for bad in (bytearray(raw), b'\xff', b'\xef\xbb\xbf' + raw, raw + b'x',
                    b'[' * 1100 + b']' * 1100, raw.replace(b'"button": 0', b'"button": NaN'),
                    raw.replace(b'"button": 0', b'"button": 0,"butt\\u006fn": 0')):
            self.assertRaises(codec.ScenarioError, codec.decode_scenario, bad)

    def test_integer_conversion_boundary_and_aggregate_overflow(self):
        data = document()
        data['starting_stacks'][0] = 10**640 - 1001
        codec.decode_scenario(wire(data))
        start = b'"starting_stacks": ['
        for n in (10**640 - 999, 10**640):
            raw = wire(document()).replace(start + b'200,', start + str(n // 10).encode() + b'0,')
            self.assertRaises(codec.ScenarioError, codec.decode_scenario, raw)
        for field, value in [('pots', []), ('payouts', [0] * 5), ('pots', [1201]),
                             ('payouts', [True] * 6), ('pots', [0])]:
            data = document()
            data['expected'][field] = value
            self.assertRaises(codec.ScenarioError, codec.decode_scenario, wire(data))


if __name__ == '__main__':
    unittest.main()
