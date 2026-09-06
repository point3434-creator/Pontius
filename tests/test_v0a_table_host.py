"""Finite independently expected table controls; no operating population."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / 'tools/v0a_table_host.py'
FIXTURES = REPO / 'tests/fixtures/table_host'
SESSION = 'pontius-v0a-event-interface-v1-correctness-table-declared'


def wire(value):
    return (json.dumps(value, separators=(',', ':')) + '\n').encode()


def load_tool():
    spec = importlib.util.spec_from_file_location('table_host_under_test', TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def modules(host):
    import pontius.blueprint_artifact.codec as codec
    import pontius.no_limit_betting as betting
    import pontius.holdem_cards as cards
    import pontius.legal_decision_spine_v2 as spine
    import pontius.v0a.model as model
    import pontius.v0a.trace as trace
    return host.Modules(codec, betting, cards, spine, model, trace)


class ExternalHandTests(unittest.TestCase):
    def test_policy_change_from_raise_to_call_changes_actual_opponent_choices(self):
        # A scripted opponent trace would keep seat 2 folding after a bot call.
        reports = []
        with tempfile.TemporaryDirectory() as directory:
            table_path = Path(directory) / 'declared_policy_change.json'
            table_path.write_bytes((FIXTURES / 'fold_table.json').read_bytes())
            for label, blueprint in (
                ('raise', REPO / 'tests/fixtures/event_adapter/fold_blueprint.json'),
                ('call', FIXTURES / 'empty_blueprint.json'),
            ):
                environment = {k: v for k, v in os.environ.items()
                               if not k.upper().startswith(('PYTHON', 'GIT_'))}
                result = subprocess.run([sys.executable, '-B', '-P', str(TOOL),
                    '--table', str(table_path), '--blueprint', str(blueprint), '--session-id',
                    'pontius-v0a-table-host-v1-correctness-policy-' + label],
                    cwd=REPO, env=environment, capture_output=True, timeout=90)
                self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
                report = json.loads(result.stdout)
                self.assertEqual(report['status'], 'completed')
                self.assertEqual(report['child_exit_code'], 0)
                reports.append(report)
        raised, called = reports
        self.assertEqual(raised['applied_actions'][0]['action'], {'kind': 'raise', 'raise_to': 8})
        self.assertEqual(called['applied_actions'][0]['action'], {'kind': 'call', 'raise_to': None})
        self.assertEqual([(r['seat'], r['action']['kind']) for r in raised['applied_actions'][1:]],
                         [(4, 'fold'), (5, 'fold'), (0, 'fold'), (1, 'fold'), (2, 'fold')])
        self.assertEqual([(r['seat'], r['action']['kind']) for r in called['applied_actions'][1:]],
                         [(4, 'fold'), (5, 'fold'), (0, 'fold'), (1, 'fold'), (2, 'check')]
                         + [(2, 'check'), (3, 'check')] * 3)
        self.assertEqual(called['settlement'], dict(payouts=[0, 0, 0, 5, 0, 0],
            final_stacks=[200, 199, 198, 203, 200, 200], pots=[dict(amount=5, seats=[2, 3])]))
        self.assertEqual(raised['input_sha256'], called['input_sha256'])
        self.assertNotEqual(raised['blueprint_sha256'], called['blueprint_sha256'])

    def test_real_child_actions_complete_three_independently_expected_hands(self):
        # These literals detect skipped/reordered/doubled actions and wrong claimant pots.
        expected_actions = {
            'fold': [(3, 'raise', 8), (4, 'fold', None), (5, 'fold', None),
                     (0, 'fold', None), (1, 'fold', None), (2, 'fold', None)],
            'showdown': [(3, 'call', None), (4, 'call', None), (5, 'call', None),
                         (0, 'call', None), (1, 'call', None), (2, 'check', None)]
                        + [(s, 'check', None) for s in (1, 2, 3, 4, 5, 0)] * 3,
            'sidepot': [(3, 'call', None), (4, 'raise', 12), (5, 'call', None),
                        (0, 'call', None), (1, 'call', None), (2, 'call', None),
                        (3, 'call', None)],
        }
        payouts = {'fold': [0, 0, 0, 5, 0, 0], 'showdown': [12, 0, 0, 0, 0, 0],
                   'sidepot': [24, 20, 16, 0, 0, 0]}
        eligible = {'fold': [[3]], 'showdown': [[0, 1, 2, 3, 4, 5]],
                    'sidepot': [[0, 1, 2, 3, 4, 5], [1, 2, 3, 4, 5], [2, 3, 4, 5]]}
        cases = [('fold', [200, 199, 198, 203, 200, 200], [5], 6),
                 ('showdown', [210, 198, 198, 198, 198, 198], [12], 24),
                 ('sidepot', [24, 20, 16, 0, 0, 0], [24, 20, 16], 7)]
        for name, stacks, pots, count in cases:
            with self.subTest(name=name):
                blueprint = (REPO / 'tests/fixtures/event_adapter/fold_blueprint.json'
                             if name == 'fold' else FIXTURES / 'empty_blueprint.json')
                environment = {k: v for k, v in os.environ.items()
                               if not k.upper().startswith(('PYTHON', 'GIT_'))}
                result = subprocess.run([sys.executable, '-B', '-P', str(TOOL),
                    '--table', str(FIXTURES / (name + '_table.json')),
                    '--blueprint', str(blueprint), '--session-id',
                    'pontius-v0a-table-host-v1-correctness-' + name],
                    cwd=REPO, env=environment, capture_output=True, timeout=90)
                self.assertTrue(result.stdout.endswith(b'\n'), result.stderr)
                self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
                self.assertNotIn(b'\r', result.stdout)
                report = json.loads(result.stdout)
                self.assertEqual(report['status'], 'completed')
                self.assertIsNone(report['failure_reason'])
                self.assertEqual(report['secondary_failures'], [])
                self.assertEqual(report['settlement']['final_stacks'], stacks)
                self.assertEqual(report['settlement']['payouts'], payouts[name])
                self.assertEqual(sum(report['settlement']['final_stacks']),
                                 60 if name == 'sidepot' else 1200)
                self.assertEqual([p['amount'] for p in report['settlement']['pots']], pots)
                self.assertEqual([p['seats'] for p in report['settlement']['pots']], eligible[name])
                self.assertEqual(len(report['applied_actions']), count)
                self.assertEqual([a['index'] for a in report['applied_actions']],
                                 list(range(count)))
                self.assertEqual([(a['seat'], a['action']['kind'], a['action']['raise_to'])
                                  for a in report['applied_actions']], expected_actions[name])
                self.assertTrue(all(a['origin'] == ('bot' if a['seat'] == 3 else 'opponent')
                                    for a in report['applied_actions']))
                self.assertEqual(report['child_exit_code'], 0)
                self.assertIs(report['capture_truncated'], False)


class TableTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(TOOL.is_file(), 'the approved reactive table host is absent')
        self.host = load_tool()
        self.modules = modules(self.host)

    def table(self, name='showdown'):
        config = self.host.TableInput.decode((FIXTURES / (name + '_table.json')).read_bytes(),
                                            self.modules)
        return self.host.Table(config, self.modules, SESSION)

    def varied_table(self, **changes):
        value = json.loads((FIXTURES / 'showdown_table.json').read_bytes())
        value.update(changes)
        config = self.host.TableInput.decode(wire(value), self.modules)
        return self.host.Table(config, self.modules, SESSION)

    def play(self, name, first_raise=None):
        table = self.table(name)
        return self.finish(table, first_raise)

    def finish(self, table, first_raise=None):
        events = [table.start_event()]
        while True:
            if table.expects_action():
                legal = table.state.legal_decision()
                action = (self.modules.model.HandAction('raise', first_raise)
                          if first_raise is not None and not table.applied_actions
                          else self.modules.model.HandAction(
                              'check' if legal.can_check else 'call', None))
                table.apply_bot(action)
            event = table.next_event()
            if event is None:
                break
            events.append(event)
        return table, events

    def select(self, table, rule):
        seat = table.state.acting_seat
        result = self.host.select_opponent(rule, table.views[seat], table.state,
                                           table.state.legal_decision(), self.modules)
        return result.kind, result.raise_to

    def test_minimum_raise_is_once_per_own_street_not_once_per_hand_or_orbit(self):
        # Two raisers force seat 4 to act twice each street: only its first may raise.
        table = self.varied_table(opponents=['passive', 'passive', 'passive', None,
                                            'min_raise_once', 'min_raise_once'])
        table, unused = self.finish(table)
        self.assertEqual([(r['street'], r['action']) for r in table.applied_actions
                          if r['seat'] == 4],
            [('preflop', {'kind': 'raise', 'raise_to': 4}),
             ('preflop', {'kind': 'call', 'raise_to': None}),
             ('flop', {'kind': 'raise', 'raise_to': 2}),
             ('flop', {'kind': 'call', 'raise_to': None}),
             ('turn', {'kind': 'raise', 'raise_to': 2}),
             ('turn', {'kind': 'call', 'raise_to': None}),
             ('river', {'kind': 'raise', 'raise_to': 2}),
             ('river', {'kind': 'call', 'raise_to': None})])

    def test_posted_blind_is_not_an_action_and_shove_does_not_reset_on_new_street(self):
        table = self.table()
        table.start_event()
        table.apply_bot(self.modules.model.HandAction('call', None))
        for seat in (4, 5, 0):
            self.assertEqual(table.next_event()['seat'], seat)
        self.assertEqual(table.state.acting_seat, 1)
        self.assertEqual(self.select(table, 'shove_once'), ('raise', 200))
        self.assertEqual(self.select(table, 'min_raise_once'), ('raise', 4))
        self.assertEqual(self.select(table, 'passive'), ('call', None))
        self.assertEqual(self.select(table, 'fold_to_bet'), ('fold', None))
        for seat in (1, 2):
            self.assertEqual(table.next_event()['seat'], seat)
        self.assertEqual(table.next_event()['kind'], 'street_revealed')
        self.assertEqual(table.state.acting_seat, 1)
        # A prior own call consumes the hand's first action even without a shove.
        self.assertEqual(self.select(table, 'shove_once'), ('check', None))
        self.assertEqual(self.select(table, 'min_raise_once'), ('raise', 2))
        self.assertEqual(self.select(table, 'passive'), ('check', None))
        self.assertEqual(self.select(table, 'fold_to_bet'), ('check', None))

    def test_all_rules_fall_back_when_raising_unavailable(self):
        # Seat 5 can only match its entire 12-chip stack after seat 4 shoves.
        table = self.table('sidepot')
        table.start_event()
        table.apply_bot(self.modules.model.HandAction('call', None))
        self.assertEqual(table.next_event()['action'], {'kind': 'raise', 'raise_to': 12})
        self.assertFalse(table.state.legal_decision().can_raise)
        for rule, expected in [('passive', 'call'), ('fold_to_bet', 'fold'),
                               ('min_raise_once', 'call'), ('shove_once', 'call')]:
            with self.subTest(rule=rule, context='facing-all-in'):
                self.assertEqual(self.select(table, rule), (expected, None))

    def assert_bot_event_visibility(self, events):
        # Exact whitelists catch a complete-deal leak even when observations otherwise match.
        common = {'kind', 'schema_version', 'hand_id', 'event_index'}
        fields = {'hand_started': {'button', 'controlled_seat', 'starting_stacks',
                                  'small_blind', 'big_blind', 'private_cards'},
                  'opponent_action': {'seat', 'street', 'action'},
                  'street_revealed': {'street', 'cards'}, 'showdown_result': {'strengths'}}
        for event in events:
            self.assertEqual(set(event), common | fields[event['kind']])
        self.assertEqual(events[0]['private_cards'], [36, 37])
        self.assertEqual([e['cards'] for e in events if e['kind'] == 'street_revealed'],
                         [[0, 5, 10], [19], [24]])
        self.assertEqual([i for i, e in enumerate(events) if e['kind'] == 'showdown_result'],
                         [len(events) - 1])

    def test_hidden_opponent_pair_permutation_does_not_change_bot_observation(self):
        original, first = self.finish(self.table())
        swapped, second = self.finish(self.varied_table(private_hands=[
            [44, 45], [48, 49], [40, 41], [36, 37], [32, 33], [28, 29]]))
        self.assert_bot_event_visibility(first)
        self.assert_bot_event_visibility(second)
        self.assertEqual(first[:-1], second[:-1])
        self.assertEqual(original.applied_actions, swapped.applied_actions)
        self.assertEqual(original.settlement()['payouts'], [12, 0, 0, 0, 0, 0])
        self.assertEqual(swapped.settlement()['payouts'], [0, 12, 0, 0, 0, 0])
        self.assertNotEqual(first[-1]['strengths'], second[-1]['strengths'])

    def test_independent_tie_odd_chip_goes_left_of_button_not_lowest_seat(self):
        # Seats 0/3 have AA; dead SB=1 plus their 2+2 and BB=2 makes 7.
        # BB's QQ loses; tied winners get 3 each, with the extra chip to seat 3.
        table = self.varied_table(private_hands=[
            [48, 49], [44, 45], [40, 41], [50, 51], [32, 33], [28, 29]],
            opponents=['passive', 'fold_to_bet', 'fold_to_bet', None,
                       'fold_to_bet', 'fold_to_bet'])
        table, events = self.finish(table)
        self.assertEqual(table.settlement(), dict(payouts=[3, 0, 0, 4, 0, 0],
            final_stacks=[201, 199, 198, 202, 200, 200], pots=[dict(amount=7, seats=[0, 2, 3])]))
        self.assertEqual(sum(table.settlement()['final_stacks']), 1200)
        self.assertEqual(events[-1]['strengths'][0], events[-1]['strengths'][3])

    def test_independent_controls_falsify_double_apply_deal_leak_and_wrong_payout(self):
        # Deliberately wrong table consumers still execute the real public game kernel.
        base = self.host.Table

        class DoubleApply(base):
            def apply_bot(self, action):
                super().apply_bot(action)
                self.apply(action, 'bot')  # Wrong: consumes the next opponent's turn.

        class LeaksDeal(base):
            def start_event(self):
                return dict(super().start_event(), private_hands=self.config.deal.private_hands)

        class WrongPayout(base):
            def settlement(self):
                value = super().settlement()
                value['payouts'] = [0, 12, 0, 0, 0, 0]
                value['final_stacks'] = [198, 210, 198, 198, 198, 198]
                return value

        for consumer in (base, DoubleApply):
            table = consumer(self.table().config, self.modules, SESSION)
            table, events = self.finish(table)
            def check_actions():
                self.assertEqual([(r['seat'], r['origin']) for r in table.applied_actions[:6]],
                    [(3, 'bot'), (4, 'opponent'), (5, 'opponent'),
                     (0, 'opponent'), (1, 'opponent'), (2, 'opponent')])
            if consumer is base:
                check_actions()
            else:
                with self.assertRaises(AssertionError):
                    check_actions()
        for consumer in (base, LeaksDeal, WrongPayout):
            table = consumer(self.table().config, self.modules, SESSION)
            table, events = self.finish(table)
            def check_result():
                self.assert_bot_event_visibility(events)
                self.assertEqual(table.settlement(), dict(payouts=[12, 0, 0, 0, 0, 0],
                    final_stacks=[210, 198, 198, 198, 198, 198],
                    pots=[dict(amount=12, seats=[0, 1, 2, 3, 4, 5])]))
            if consumer is base:
                check_result()
            else:
                with self.assertRaises(AssertionError):
                    check_result()

    def test_fold_returns_uncalled_excess_and_never_reveals(self):
        table, events = self.play('fold', 8)
        self.assertEqual(table.settlement(), dict(payouts=[0, 0, 0, 5, 0, 0],
                         final_stacks=[200, 199, 198, 203, 200, 200],
                         pots=[dict(amount=5, seats=[3])]))
        self.assertEqual([e['kind'] for e in events], ['hand_started'] + ['opponent_action'] * 5)
        self.assertEqual([a['seat'] for a in table.applied_actions], [3, 4, 5, 0, 1, 2])

    def test_passive_showdown_awards_twelve_to_aces(self):
        table, events = self.play('showdown')
        self.assertEqual(table.settlement()['final_stacks'], [210, 198, 198, 198, 198, 198])
        self.assertEqual(table.settlement()['pots'], [dict(amount=12, seats=list(range(6)))])
        self.assertEqual([e['cards'] for e in events if e['kind'] == 'street_revealed'],
                         [[0, 5, 10], [19], [24]])
        self.assertEqual(events[-1]['kind'], 'showdown_result')

    def test_all_in_side_pots_reveal_without_synthetic_actions(self):
        table, events = self.play('sidepot')
        self.assertEqual(table.settlement()['final_stacks'], [24, 20, 16, 0, 0, 0])
        self.assertEqual(table.settlement()['pots'], [dict(amount=24, seats=list(range(6))),
                         dict(amount=20, seats=list(range(1, 6))),
                         dict(amount=16, seats=list(range(2, 6)))])
        self.assertEqual(len(table.applied_actions), 7)
        self.assertTrue(all(a['street'] == 'preflop' for a in table.applied_actions))
        self.assertEqual(sum(a['origin'] == 'bot' for a in table.applied_actions), 2)
        self.assertEqual(events[-1]['kind'], 'showdown_result')

    def test_strict_input_rejects_wrong_types_domains_and_unknown_members(self):
        good = json.loads((FIXTURES / 'showdown_table.json').read_bytes())
        variants = [dict(good, button=True), dict(good, starting_stacks=[1] * 6),
                    dict(good, small_blind=2), dict(good, board_runout=[0] * 5),
                    dict(good, opponents=['passive'] * 6), dict(good, future_actions=[]),
                    dict(good, starting_stacks=[1000000] * 6)]
        raw_variants = [wire(v) for v in variants]
        raw_variants += [b'\xef\xbb\xbf' + wire(good), wire(good).replace(b'\n', b'\r\n'),
                         wire(good).replace(b'"button":0', b'"button":0.0'),
                         wire(good).replace(b'"button":0', b'"button":0,"button":1'),
                         b'[' * 100 + b']' * 100]
        for raw in raw_variants:
            with self.subTest(raw=raw[:100]), self.assertRaises(self.host.HostRefusal) as error:
                self.host.TableInput.decode(raw, self.modules)
            self.assertEqual(error.exception.code, 'input_invalid')

    def test_integer_decoder_rejects_before_python_conversion_limit(self):
        for width in (8, 640, 641):
            with self.subTest(width=width), self.assertRaises(self.host.HostRefusal):
                self.host.TableInput.decode(b'{"button":' + b'9' * width + b'}', self.modules)


if __name__ == '__main__':
    unittest.main()
