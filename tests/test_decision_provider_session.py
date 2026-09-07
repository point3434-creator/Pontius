"""Three literal deals and independently calculated session accounting."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
PREFIX = 'pontius-v0a-table-session-v2-correctness-'


def invoke(*extra, commands=b''):
    process = subprocess.run([sys.executable, '-B', '-P',
        str(REPO / 'tools/v0a_table_session.py'), '--session',
        str(REPO / 'tests/fixtures/decision_provider/session.json'), '--blueprint',
        str(REPO / 'tests/fixtures/table_host/empty_blueprint.json'), '--strategy',
        'baseline-rules-v1', '--session-id', PREFIX + 'provider-fixture', *extra],
        cwd=REPO, env=os.environ.copy(), input=commands, capture_output=True, timeout=150)
    with tempfile.TemporaryDirectory() as capture:
        Path(capture, 'stdout').write_bytes(process.stdout)
        Path(capture, 'stderr').write_bytes(process.stderr)
    return process


class ProviderSessionTests(unittest.TestCase):
    def test_legacy_omission_and_explicit_blueprint_preserve_results_and_fields(self):
        reports = []
        for extra in ([], ['--strategy','blueprint-v1']):
            process = subprocess.run([sys.executable, '-B', '-P',
                str(REPO/'tools/v0a_table_session.py'), '--session',
                str(REPO/'tests/fixtures/table_session/two_hands.json'), '--blueprint',
                str(REPO/'tests/fixtures/table_host/empty_blueprint.json'), '--session-id',
                'pontius-v0a-table-session-v1-correctness-provider-legacy', '--auto',
                '--format','json', *extra], cwd=REPO, env=os.environ.copy(),
                capture_output=True, timeout=150)
            self.assertEqual(process.returncode,0,(process.stdout,process.stderr))
            report=json.loads(process.stdout)
            self.assertEqual(report['version'],'pontius-v0a-table-session-result-v1')
            self.assertNotIn('provider',report)
            self.assertNotIn('config_sha256',report)
            reports.append(report)
        self.assertEqual(set(reports[0]),set(reports[1]))
        self.assertEqual(reports[0]['carried_stacks'],reports[1]['carried_stacks'])
        for left,right in zip(reports[0]['hands'],reports[1]['hands']):
            self.assertEqual(set(left['result']),set(right['result']))
            self.assertEqual(left['result']['applied_actions'],right['result']['applied_actions'])
            self.assertEqual(left['result']['settlement'],right['result']['settlement'])

    def test_three_hands_carry_independent_blind_profits_and_fixed_identity(self):
        process = invoke('--auto', '--format', 'json')
        self.assertEqual(process.returncode, 0, (process.stdout, process.stderr))
        report = json.loads(process.stdout)
        self.assertEqual(report['version'], 'pontius-v0a-table-session-result-v2')
        self.assertEqual(report['completed_hands'], 3)
        self.assertEqual(report['carried_stacks'], [200, 199, 197, 206, 198, 200])
        self.assertEqual([hand['button'] for hand in report['hands']], [0, 1, 2])
        stacks = [[200,199,198,203,200,200], [200,199,197,204,200,200],
                  [200,199,197,206,198,200]]
        reasons = []
        for entry, final in zip(report['hands'], stacks):
            hand = entry['result']
            self.assertEqual(hand['version'], 'pontius-v0a-table-session-hand-result-v2')
            self.assertEqual(hand['settlement']['final_stacks'], final)
            self.assertEqual(hand['provider'], 'baseline-rules-v1')
            self.assertEqual(hand['config_sha256'], report['config_sha256'])
            self.assertEqual(hand['child_exit_code'], 0)
            frames = [json.loads(row) for row in
                      base64.b64decode(hand['child_stdout_base64']).splitlines()]
            self.assertEqual(frames[0]['provider'], report['provider'])
            self.assertEqual(frames[0]['config_sha256'], report['config_sha256'])
            for frame in frames:
                if frame['type'] == 'event_result' and frame['decision']:
                    decision = frame['decision']
                    self.assertEqual(decision['config_sha256'], report['config_sha256'])
                    self.assertEqual(decision['selected_action'], decision['applied_action'])
                    reasons.append(decision['proposal']['reason'])
        self.assertEqual(reasons, ['premium_raise', 'premium_raise'])

    def test_text_has_verified_reason_and_quit_keeps_first_settlement(self):
        process = invoke('--format', 'text', commands=b'q\n')
        self.assertEqual(process.returncode, 0, (process.stdout, process.stderr))
        text = process.stdout.decode('ascii')
        self.assertIn('Strategy: baseline-rules-v1', text)
        self.assertIn('premium_raise', text)
        self.assertIn('completed hands 1', text)
        self.assertIn('Final stacks: 200 199 198 203 200 200', text)
        self.assertNotIn('Hand 2/', text)
        self.assertNotIn('Qc Kd', text)


if __name__ == '__main__':
    unittest.main()
