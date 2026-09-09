"""Retained-protocol mutations anchored to actual v1 and v2 Session captures."""
import base64
import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_eval_completion_tool import BASE, ROOT, TOOL


class RetainedProtocolTests(unittest.TestCase):
    def test_real_captures_reject_malformed_schema_before_successful_credit(self):
        from pontius import eval_bridge as bridge
        from pontius.blueprint_artifact.codec import decode_blueprint, encode_blueprint
        from pontius.eval_agreement import classify
        from pontius.execution import begin_run, child_context, CONTEXT_ENV
        from pontius.immutable_blueprint import BlueprintActionEntry, ImmutableBlueprintActionSource
        completion = TOOL.load_completion()
        board = bridge.board_cards(BASE['board'])
        dealer = completion.load_tool('v0a_seeded_deals')
        witness = None
        for index in range(512):
            candidate = dealer.deal_for_hand(format(index // 16, '064x'), index % 16)
            low, high = sorted(c // 4 + 2 for c in candidate['private_hands'][2])
            premium = (low == high and low >= 10) or (high == 14 and low in (12, 13))
            if premium and not any(c in board for h in candidate['private_hands'] for c in h):
                witness = candidate
                break
        self.assertIsNotNone(witness, 'finite correctness bank has no premium witness')
        self.assertFalse(any(c in board for h in witness['private_hands'] for c in h))
        hands = tuple(map(tuple, witness['private_hands']))
        name = bridge.hand_name(hands[2])
        row = BlueprintActionEntry(bridge.root_key(bridge.replay_root(), board, hands[2]),
                                   bridge.CHECK)
        wire = encode_blueprint(ImmutableBlueprintActionSource('protocol-control', (row,)))
        kwargs = dict(blueprint=decode_blueprint(wire), teacher_actions={name: bridge.CHECK},
                      board=board, private_hands=hands)
        context = begin_run(ROOT, allow_working_tree=True)
        (ROOT / 'tmp').mkdir(exist_ok=True)
        before = Path.cwd()
        try:
            os.chdir(ROOT)
            with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as directory:
                with patch.dict(os.environ, {CONTEXT_ENV: child_context(context)}):
                    hit = completion.play(witness, board, wire, kwargs['teacher_actions'],
                                          Path(directory), 0, 'protocol')['session']
                    module = completion.load_tool('v0a_table_session')
                    args = SimpleNamespace(session=str(Path(directory) / 'host-input.json'),
                        blueprint=str(Path(directory) / 'host-blueprint.json'), auto=True,
                        strategy='baseline-rules-v1', development=False,
                        reviewed_commit=context['commit'],
                        session_id='pontius-v0a-table-session-v2-correctness-protocol')
                    baseline = module.Session(args).run()
        finally:
            os.chdir(before)

        for strategy, control in (('blueprint-v1', hit), ('baseline-rules-v1', baseline)):
            with self.subTest(control=strategy):
                valid = classify(control, strategy=strategy, **kwargs)
                self.assertTrue(valid['chip_eligible'], valid)
                self.assertEqual(valid['classification'],
                                 'hit' if strategy == 'blueprint-v1' else 'unsupported', valid)
                if strategy == 'baseline-rules-v1':
                    actions = control['hands'][0]['result']['applied_actions']
                    self.assertTrue(any(r['origin'] == 'bot' and r['street'] == 'preflop'
                                        and r['action']['kind'] == 'raise' for r in actions))
                    self.assertEqual(control['version'], 'pontius-v0a-table-session-result-v2')
            cases = [('ready_evidentiary', v) for v in (True, None, 'false')]
            cases += [(key, v) for key in ('interrupted_response_count', 'requested_hands',
                'completed_hands', 'ordinal', 'button', 'index', 'seat', 'action_index')
                for v in ('bool', 'float')]
            cases += [('missing_preparation', key) for key in
                      ('credited_seconds', 'producer_status', 'artifact_sha256s')]
            cases += [('preparation_artifacts', '')]
            cases += [('missing_action', where) for where in ('decision', 'wire', 'replay')]
            cases += [('stack_type', True), ('stack_type', 4.0)]
            cases += [('missing_timing', key) for key in
                      ('interruption_reason', 'deadline_crossed', 'response_compute_seconds')]
            if strategy == 'baseline-rules-v1':
                cases += [('missing_decision', key) for key in
                          ('schema_version', 'provider', 'provider_outcome', 'preparation_use')]
                cases += [('provider_binding', where) for where in ('ready', 'record', 'outer')]
            for kind, value in cases:
                with self.subTest(strategy=strategy, mutation=kind, value=value):
                    report = copy.deepcopy(control)
                    entry = report['hands'][0]
                    hand = entry['result']
                    frames = [json.loads(line) for line in
                              base64.b64decode(hand['child_stdout_base64']).splitlines()]
                    decision = next(f['decision'] for f in frames if f.get('decision'))
                    if kind == 'ready_evidentiary':
                        frames[0]['evidentiary'] = value
                    elif kind == 'missing_preparation':
                        del decision['preparation_use'][value]
                    elif kind == 'preparation_artifacts':
                        decision['preparation_use']['artifact_sha256s'] = value
                    elif kind == 'missing_decision':
                        del decision[value]
                    elif kind == 'missing_timing':
                        del decision['timing'][value]
                    elif kind == 'missing_action':
                        target = (decision['selected_action'] if value == 'decision' else
                                  next(f['action'] for f in frames if f['type'] == 'action')
                                  if value == 'wire' else hand['applied_actions'][0]['action'])
                        del target['raise_to']
                    elif kind == 'stack_type':
                        entry['starting_stacks'][0] = value
                    elif kind == 'provider_binding':
                        target = (frames[0] if value == 'ready' else
                                  decision if value == 'record' else report)
                        target['config_sha256'] = '0' * 64
                    else:
                        target = (frames[-2] if kind == 'interrupted_response_count' else
                                  report if kind in ('requested_hands', 'completed_hands') else
                                  entry if kind in ('ordinal', 'button') else
                                  hand['applied_actions'][0] if kind in ('index', 'seat') else
                                  next(f for f in frames if f['type'] == 'action'))
                        original = target[kind]
                        # Use a value that compares equal, so replay alone cannot reject it.
                        if value == 'bool' and original not in (0, 1):
                            target = next(r for r in hand['applied_actions'] if r[kind] == 0)
                            original = target[kind]
                        target[kind] = bool(original) if value == 'bool' else float(original)
                    hand['child_stdout_base64'] = base64.b64encode(b''.join(
                        json.dumps(f).encode() + b'\n' for f in frames)).decode()
                    result = classify(report, strategy=strategy, **kwargs)
                    self.assertEqual(result['classification'], 'excluded', result)
                    self.assertFalse(result['chip_eligible'], result)
                    self.assertIsNone(result['chips'], result)


if __name__ == '__main__':
    unittest.main()
