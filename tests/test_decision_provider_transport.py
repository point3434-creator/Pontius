"""Source admission and real child provider wire controls."""
import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


class ProviderTransportTests(unittest.TestCase):
    def invoke(self, repo=REPO, strategy='baseline-rules-v1', code=None, blueprint_path=None):
        version = 'v2' if strategy == 'baseline-rules-v1' else 'v1'
        identity = 'pontius-v0a-event-interface-' + version + '-correctness-provider-transport'
        event = dict(kind='hand_started', schema_version='pontius-hand-event-v1',
            hand_id=identity, event_index=0, button=0, controlled_seat=3,
            starting_stacks=[200]*6, small_blind=1, big_blind=2, private_cards=[50,51])
        command = ['-c', code] if code else [str(repo / 'tools/v0a_event_adapter.py')]
        event['schema_version'] = 'pontius-v0a-event-v1'
        return subprocess.run([sys.executable, '-B', '-P', *command, '--blueprint',
            str(blueprint_path or REPO/'tests/fixtures/table_host/empty_blueprint.json'),
            '--session-id',
            identity, '--strategy', strategy], cwd=repo, env=os.environ.copy(),
            input=(json.dumps(event)+'\n').encode(), capture_output=True, timeout=90)

    def test_real_child_admits_new_population_then_readies_and_raises(self):
        process = self.invoke()
        rows = [json.loads(row) for row in process.stdout.splitlines()]
        self.assertTrue(rows, process.stderr)
        self.assertEqual(rows[0]['type'], 'ready')
        self.assertEqual(rows[0]['provider'], 'baseline-rules-v1')
        self.assertEqual(rows[0]['protocol'], 'pontius-v0a-event-interface-v2')
        self.assertEqual(rows[1]['action'], {'kind':'raise', 'raise_to':4})
        record = rows[2]['decision']
        self.assertEqual(record['source_manifest_sha256'], rows[0]['source_manifest_sha256'])
        self.assertEqual(record['config_sha256'], rows[0]['config_sha256'])
        self.assertEqual(record['proposal']['reason'], 'premium_raise')

    def test_source_refuses_changed_extra_cached_and_unrelated_committed_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / 'source'
            git = os.environ['PONTIUS_GIT']
            subprocess.run([git, '-c', 'core.autocrlf=false', 'clone', '--quiet',
                '--no-hardlinks', str(REPO), str(repo)], check=True, capture_output=True)
            for relative in ('src/pontius/v0a/model.py',
                             'src/pontius/decision_provider/extra.py',
                             'src/pontius/decision_provider/__pycache__/extra.pyc'):
                target = repo / relative
                previous = target.read_bytes() if target.exists() else None
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    target.write_bytes((previous or b'') + b'\n# corruption\n')
                    result = self.invoke(repo)
                    self.assertNotIn(b'"type":"ready"', result.stdout)
                    self.assertNotEqual(result.returncode, 0)
                finally:
                    target.unlink() if previous is None else target.write_bytes(previous)
                    if '__pycache__' in relative:
                        target.parent.rmdir()
            target = repo / 'src/pontius/v0a/model.py'
            target.write_bytes(target.read_bytes() + b'\n# unrelated committed drift\n')
            subprocess.run([git, '-C', str(repo), 'add', str(target)], check=True)
            subprocess.run([git, '-C', str(repo), '-c', 'user.name=Correctness', '-c',
                'user.email=correctness@localhost', 'commit', '--quiet', '-m',
                'Disposable source refusal control'], check=True)
            self.assertNotIn(b'"type":"ready"', self.invoke(repo).stdout)

    def test_unknown_strategy_refuses_before_readiness(self):
        result = self.invoke(strategy='unknown')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(b'"type":"ready"', result.stdout)

    def test_admitted_source_rejects_late_bytes_head_and_foreign_module_origin(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / 'source'
            git = os.environ['PONTIUS_GIT']
            subprocess.run([git, '-c', 'core.autocrlf=false', 'clone', '--quiet',
                '--no-hardlinks', str(REPO), str(repo)], check=True, capture_output=True)
            prefix = """import runpy,sys,subprocess,os
from pathlib import Path
m = runpy.run_path(str(Path.cwd() / 'tools/v0a_table_host.py'))
s = m['Source'](Path.cwd())
s.load()
print('SOURCE_ADMITTED', flush=True)
"""
            changes = ["""p=Path('src/pontius/v0a/model.py')
raw=p.read_bytes()
try:
    p.write_bytes(raw+b'\\n# late drift\\n')
    s.check()
finally:
    p.write_bytes(raw)
""", """sys.modules['pontius.decision_provider.model'].__file__ = str(Path.cwd() / 'foreign.py')
s.check()
""", """subprocess.run([os.environ['PONTIUS_GIT'], '-c', 'user.name=Correctness',
    '-c', 'user.email=correctness@localhost', 'commit', '--quiet', '--allow-empty',
    '-m', 'Disposable HEAD drift'], check=True)
s.check()
"""]
            for change in changes:
                result = subprocess.run([sys.executable,'-B','-P','-c',prefix+change],
                    cwd=repo,env=os.environ.copy(),capture_output=True,timeout=90)
                self.assertIn(b'SOURCE_ADMITTED',result.stdout,result.stderr)
                self.assertNotEqual(result.returncode,0)
                self.assertIn(b'source_invalid',result.stderr)

    def test_real_partial_pipe_action_retains_raw_prefix_and_fails(self):
        code = """import runpy,os
from pathlib import Path
m=runpy.run_path(str(Path.cwd() / 'tools/v0a_event_adapter.py'))
write=os.write
def partial(fd, raw):
    if b'"type":"action"' in raw:
        return write(fd,raw[:12])
    return write(fd,raw)
os.write=partial
raise SystemExit(m['main']())
"""
        result = self.invoke(code=code)
        self.assertNotEqual(result.returncode,0)
        ready, remainder=result.stdout.split(b'\n',1)
        self.assertEqual(json.loads(ready)['type'],'ready')
        self.assertTrue(remainder.startswith(b'{"action":{"'),remainder)
        with self.assertRaises(json.JSONDecodeError):
            json.loads(remainder.splitlines()[0])
        self.assertIn(b'REFUSED',result.stderr)

    def test_v1_readiness_and_action_keep_old_fields(self):
        process = self.invoke(strategy='blueprint-v1')
        rows = [json.loads(row) for row in process.stdout.splitlines()]
        self.assertTrue(rows, process.stderr)
        self.assertEqual(set(rows[0]), set(('protocol session_id type source_commit '
            'source_manifest_sha256 blueprint_artifact_sha256 blueprint_sha256 '
            'evidentiary').split()))
        self.assertEqual(rows[0]['protocol'], 'pontius-v0a-event-interface-v1')
        self.assertEqual(rows[1]['action'], {'kind':'call', 'raise_to':None})
        self.assertNotIn('provider', rows[2]['decision'])

    def consumer(self, rows, admitted_ready=None, blueprint_path=None):
        admitted_ready = rows[0] if admitted_ready is None else admitted_ready
        spec = importlib.util.spec_from_file_location('provider_transport_host',
            REPO / 'tools/v0a_table_host.py')
        host = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = host
        spec.loader.exec_module(host)
        import pontius.blueprint_artifact.codec as codec
        import pontius.no_limit_betting as betting
        import pontius.holdem_cards as cards
        import pontius.legal_decision_spine_v2 as spine
        import pontius.v0a.model as model
        import pontius.v0a.trace as trace
        import pontius.decision_provider.model as provider_model
        import pontius.decision_provider.providers as providers
        import pontius.decision_provider.codec as provider_codec
        modules = host.Modules(codec, betting, cards, spine, model, trace,
                               provider_model, providers, provider_codec)
        fixture = json.loads((REPO / 'tests/fixtures/decision_provider/session.json').read_bytes())
        value = dict(fixture, **fixture['hands'][0], version=host.INPUT_VERSION)
        del value['hands']
        table = host.Table(host.TableInput.decode(json.dumps(value).encode(), modules),
                           modules, rows[0]['session_id'])
        class Source:
            commit = admitted_ready['source_commit']
            child_manifest = admitted_ready['source_manifest_sha256']
        class Connection:
            startup_deadline = 1
            def __init__(self):
                self.frames = iter(json.dumps(row).encode() + b'\n' for row in rows)
            def receive(self, deadline):
                return next(self.frames)
            def deadline(self):
                return 1
            def send(self, raw, deadline):
                self.sent = raw
        blueprint = codec.decode_blueprint(
            (blueprint_path or REPO/'tests/fixtures/table_host/empty_blueprint.json').read_bytes())
        identity = providers.make_provider('baseline-rules-v1', blueprint).identity
        consumer = host.WireConsumer(Connection(), Source(), table,
            admitted_ready['blueprint_artifact_sha256'], blueprint.digest, identity, blueprint)
        return host, table, consumer

    def test_fallback_authority_binds_action_reason_and_selected_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            hit = Path(directory)/'hit.json'
            hit.write_bytes((REPO/'tests/fixtures/event_adapter/fold_blueprint.json').read_bytes()
                            .replace(b'[48, 49]', b'[50, 51]'))
            for path, amount, reason in ((None, None, 'passive_default'), (hit, 8, 'table_hit')):
                process = self.invoke(blueprint_path=path)
                original = [json.loads(r) for r in process.stdout.splitlines()]
                record = original[2]['decision']
                self.assertEqual(record['fallback_action'],
                                 dict(kind='call' if amount is None else 'raise', raise_to=amount))
                self.assertEqual(record['fallback_reason'], reason)
                host, table, consumer = self.consumer(original, blueprint_path=path)
                consumer.ready()
                consumer.exchange(table.start_event())
                self.assertEqual(len(table.applied_actions), 1)
                changes = [dict(fallback_action=dict(kind='fold', raise_to=None)),
                           dict(fallback_reason=('table_hit' if amount is None
                                                 else 'passive_default'))]
                changes.append(dict(changes[0], **changes[1]))
                for outcome in ('error', 'abstained', 'invalid'):
                    proposal = (None if outcome == 'error' else dict(record['proposal'],
                        **(dict(action=None, reason='abstain') if outcome == 'abstained'
                           else dict(decision_sha256='0'*64))))
                    changes.append(dict(fallback_action=record['selected_action'],
                        proposal=proposal,
                        provider_outcome=outcome, selection_reason='provider_'+outcome,
                        selection_origin='blueprint_fallback'))
                for change in changes:
                    rows = json.loads(json.dumps(original))
                    rows[2]['decision'].update(change)
                    host, table, consumer = self.consumer(rows, blueprint_path=path)
                    consumer.ready()
                    with self.subTest(path=path, change=change), self.assertRaises(
                            host.HostRefusal):
                        consumer.exchange(table.start_event())
                    self.assertEqual(len(table.applied_actions), 1)

    def test_failed_consumer_rejects_completed_cutoff_with_provider_selection(self):
        rows = [json.loads(r) for r in self.invoke().stdout.splitlines()]
        record = rows[2]['decision']
        timing = record['timing']
        end = timing['wall_start_ns'] + 14_000_000_000
        timing.update(last_valid_observation_ns=end, emission_observed_ns=end,
            elapsed_ns=14_000_000_000, response_compute_seconds=0.0,
            response_uninstrumented_seconds=14.0, work_cutoff_crossed=True, deadline_crossed=False)
        record['failure_reason'] = 'work_cutoff_exceeded'
        failure = {k: record[k] for k in ('hand_id','event_index','action_index',
                                         'delivery_status','delivered_action','timing')}
        rows[2].update(status='failed', failure=dict(failure, code='work_cutoff_exceeded'))
        host, table, consumer = self.consumer(rows)
        consumer.ready()
        with self.assertRaises(host.HostRefusal) as error:
            consumer.exchange(table.start_event())
        self.assertEqual(error.exception.code, 'protocol_invalid')
        self.assertEqual(len(table.applied_actions), 1)

    def test_real_exchange_rejects_protocol_identity_digest_action_and_extra_fields(self):
        process = self.invoke()
        original = [json.loads(row) for row in process.stdout.splitlines()][:3]
        self.assertEqual(len(original), 3, process.stderr)
        for phase, key, value in [(0,'protocol','pontius-v0a-event-interface-v1'),
                (0,'provider','blueprint-v1'), (0,'config_sha256','0'*64),
                (0,'blueprint_sha256','0'*64),
                (0,'source_manifest_sha256','0'*64), (0,'extra',True),
                (2,'decision_sha256','0'*64), (2,'source_manifest_sha256','0'*64),
                (2,'config_sha256','0'*64), (2,'extra',True),
                (2,'applied_action',{'kind':'call','raise_to':None})]:
            rows = json.loads(json.dumps(original))
            (rows[phase] if phase == 0 else rows[2]['decision'])[key] = value
            host, table, consumer = self.consumer(rows, original[0])
            with self.subTest(phase=phase,key=key), self.assertRaises(host.HostRefusal):
                consumer.ready()
                consumer.exchange(table.start_event())
            self.assertEqual(len(table.applied_actions), 0 if phase == 0 else 1)
        host, table, consumer = self.consumer(original)
        consumer.ready()
        consumer.exchange(table.start_event())
        self.assertEqual(table.applied_actions[0]['action'], {'kind':'raise','raise_to':4})
        self.assertEqual(consumer.reasons, {1:'premium_raise'})
        rows = json.loads(json.dumps(original))
        rows[2]['decision'].update(provider_outcome='invalid',selection_reason='provider_invalid',
            selection_origin='blueprint_fallback',fallback_action={'kind':'raise','raise_to':4})
        host,table,consumer = self.consumer(rows)
        consumer.ready()
        with self.assertRaises(host.HostRefusal):
            consumer.exchange(table.start_event())
        self.assertEqual(len(table.applied_actions),1)

    def test_duplicate_action_and_failure_preserve_received_application(self):
        process = self.invoke()
        original = [json.loads(row) for row in process.stdout.splitlines()]
        self.assertGreaterEqual(len(original), 4, process.stderr)
        duplicate = original[:2] + [original[1]]
        host, table, consumer = self.consumer(duplicate)
        consumer.ready()
        with self.assertRaises(host.HostRefusal):
            consumer.exchange(table.start_event())
        self.assertEqual(len(table.applied_actions), 1)
        # A real child EOF failure supplies its exact typed payload. Bind the failure
        # to the opening event to control the before/after-action consumer boundary.
        failure = next(row for row in original if row['type']=='event_result'
                       and row['status']=='failed')
        for after in (False, True):
            failed = json.loads(json.dumps(failure))
            failed['event_index'] = 0
            failed['failure']['event_index'] = 0
            rows = original[:2] + [failed] if after else original[:1] + [failed]
            host, table, consumer = self.consumer(rows)
            consumer.ready()
            with self.assertRaises(host.HostRefusal) as error:
                consumer.exchange(table.start_event())
            self.assertEqual(error.exception.code, 'child_failed')
            self.assertEqual(len(table.applied_actions), int(after))

    def test_constructed_failure_record_before_and_after_action_is_truthful(self):
        for before in (False, True):
            code = """import runpy,os
from pathlib import Path
m=runpy.run_path(str(Path.cwd() / 'tools/v0a_event_adapter.py'))
factory=m['runtime_type']
class Clock:
    now=0
    def __call__(self): return self.now
clock=Clock()
def factory_with_clock(model,core,clock_module):
    base=factory(model,core,clock_module)
    class Runtime(base):
        def __init__(self,**kwargs): super().__init__(clock=clock,**kwargs)
    return Runtime
m['main'].__globals__['runtime_type']=factory_with_clock
write=os.write
def controlled(fd,raw):
    if b'"type":"action"' in raw:
        if BEFORE:
            raise OSError('controlled zero-byte action write failure')
        count=write(fd,raw)
        clock.now=15000000001
        return count
    return write(fd,raw)
os.write=controlled
raise SystemExit(m['main']())
""".replace('BEFORE',repr(before))
            result=self.invoke(code=code)
            self.assertNotEqual(result.returncode,0)
            rows=[json.loads(row) for row in result.stdout.splitlines()]
            self.assertTrue(any(row['type']=='event_result' for row in rows),
                            (before,result.stdout,result.stderr))
            failed=next(row for row in rows if row['type']=='event_result')
            self.assertEqual(failed['status'],'failed')
            self.assertIsNotNone(failed['decision'])
            self.assertEqual(failed['decision']['applied_action'],{'kind':'raise','raise_to':4})
            self.assertEqual(failed['decision']['delivery_status'],
                             'unknown' if before else 'accepted')
            self.assertEqual(failed['decision']['delivered_action'],None if before else
                             {'kind':'raise','raise_to':4})
            host,table,consumer=self.consumer(rows)
            consumer.ready()
            with self.assertRaises(host.HostRefusal) as error:
                consumer.exchange(table.start_event())
            self.assertEqual(error.exception.code,'child_failed')
            self.assertEqual(len(table.applied_actions),0 if before else 1)
            for change in (dict(fallback_action=dict(kind='fold',raise_to=None)),
                           dict(fallback_reason='table_hit')):
                corrupt=json.loads(json.dumps(rows))
                next(r for r in corrupt if r['type']=='event_result')['decision'].update(change)
                host,table,consumer=self.consumer(corrupt)
                consumer.ready()
                with self.assertRaises(host.HostRefusal) as mismatch:
                    consumer.exchange(table.start_event())
                self.assertEqual(mismatch.exception.code,'state_mismatch')
                self.assertEqual(len(table.applied_actions),0 if before else 1)
            contradictory=json.loads(json.dumps(rows))
            for row in contradictory:
                if row['type']=='event_result':
                    row['failure']['code']='invalid_event'
            host,table,consumer=self.consumer(contradictory)
            consumer.ready()
            with self.assertRaises(host.HostRefusal) as error:
                consumer.exchange(table.start_event())
            self.assertEqual(error.exception.code,'protocol_invalid')
            self.assertEqual(len(table.applied_actions),0 if before else 1)

    def test_hidden_deal_pair_preserves_actual_propose_observation_and_visible_change_acts(self):
        from unittest.mock import patch
        from pontius.decision_provider.providers import BaselineProvider
        from pontius.immutable_blueprint import ImmutableBlueprintActionSource
        from pontius.holdem_cards import SixSeatHoldemDeal
        from pontius.v0a.model import DeliveryReceipt, HandStartedEvent
        from pontius.v0a.runtime import HandRuntime
        # Three literal controls: two full deals differ only in unseen opponents;
        # the third changes the bot's visible premium pair to a weak holding.
        pairs = [((0,5),(8,13),(16,21),(50,51),(24,29),(32,37)),
                 ((8,13),(0,5),(16,21),(50,51),(24,29),(32,37)),
                 ((0,5),(8,13),(16,21),(1,20),(24,29),(32,37))]
        observed, delivered = [], []
        propose = BaselineProvider.propose
        def capture(provider, observation):
            observed.append(observation)
            return propose(provider, observation)
        class Mailbox:
            def deliver(self, envelope):
                delivered.append(envelope.action)
                return DeliveryReceipt(envelope.hand_id,envelope.action_index)
        for private in pairs:
            deal=SixSeatHoldemDeal(private_hands=private,board_runout=(40,45,2,7,10))
            runtime=HandRuntime(blueprint=ImmutableBlueprintActionSource(source_id='provider-test'),
                mailbox=Mailbox(), strategy='baseline-rules-v1', source_manifest_sha256='1'*64)
            event=HandStartedEvent(hand_id='pontius-v0a-event-interface-v2-correctness-hidden',
                event_index=0,button=0,controlled_seat=3,starting_stacks=(200,)*6,
                small_blind=1,big_blind=2,private_cards=deal.hand(3))
            with patch.object(BaselineProvider,'propose',capture):
                outcome=runtime.dispatch(event)
            self.assertEqual(outcome.status,'decided')
        self.assertEqual(observed[0].decision_sha256,observed[1].decision_sha256)
        self.assertEqual(observed[0].cards,observed[1].cards)
        self.assertEqual(observed[0].betting,observed[1].betting)
        self.assertEqual(delivered[0],delivered[1])
        self.assertEqual((delivered[0].kind,delivered[0].raise_to),('raise',4))
        self.assertEqual(delivered[2].kind,'fold')
        self.assertNotEqual(observed[0].decision_sha256,observed[2].decision_sha256)
        self.assertFalse(hasattr(observed[0],'deal'))


if __name__ == '__main__':
    unittest.main()
