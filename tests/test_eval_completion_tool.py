"""Bridge-completion admission and real bounded worker integration."""
import copy
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('completion_entry_tests',
                                             ROOT / 'tools/v0a_eval_panel.py')
TOOL = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = TOOL
spec.loader.exec_module(TOOL)
BASE = json.loads((ROOT / 'tests/fixtures/eval_panel/plan-capacity.json').read_bytes())


def plan(phase='solve'):
    value = copy.deepcopy(BASE)
    value.update(version='pontius-eval-panel-completion-plan-v1', phase=phase,
                 coverage='test-subset', pool_count=2, prerequisites={}, inputs={})
    return value


class CompletionAdmissionTests(unittest.TestCase):
    def test_new_solve_phase_is_explicit_and_immutable(self):
        value = plan()
        try:
            admitted = TOOL.validate_plan(value)
        except ValueError as error:
            self.fail('explicit bounded solve phase unavailable: ' + str(error))
        value['pool_count'] = 1081
        self.assertEqual(admitted.document['pool_count'], 2)
        self.assertEqual(admitted.document['phase'], 'solve')

    def test_full_solve_cannot_borrow_subset_or_missing_prerequisites(self):
        for field, value in (('coverage', 'declared-full'), ('pool_count', 0),
                             ('pool_count', True), ('phase', 'solve-export')):
            proposed = plan()
            proposed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                TOOL.validate_plan(proposed)

    def test_witness_scan_retains_twelve_cards_and_finite_bank_failures(self):
        loader = getattr(TOOL, 'load_completion', None)
        self.assertIsNotNone(loader, 'completion witness boundary is missing')
        completion = loader()
        bank = dict(seed_start='0' * 64, seed_count=8, indices=list(range(16)),
                    holdout_seed_start='f' * 64, holdout_seed_count=1,
                    sizing_rationale='Finite correctness subset; no guaranteed coverage.')
        from pontius import eval_bridge as bridge
        board = bridge.board_cards(BASE['board'])
        result = completion.witnesses(board, [BASE['permutation'][0]], bank,
                                      deadline=float('inf'))
        self.assertEqual(len(result['draws']), 128)
        self.assertEqual(sum(result['counts'].values()), 128)
        dealer = completion.load_tool('v0a_seeded_deals')
        for row in result['draws']:
            actual = dealer.deal_for_hand(row['seed'], row['index'])
            collisions = any(card in board for hand in actual['private_hands'] for card in hand)
            self.assertEqual(row['status'] == 'collision', collisions)
            if row['status'] == 'witness':
                self.assertEqual(result['selected'][row['hand']]['private_hands'],
                                 actual['private_hands'])


class CompletionPhaseTests(unittest.TestCase):
    def test_solve_produces_one_census_and_immutable_teacher_without_export(self):
        from pontius import eval_bridge as bridge
        events = []
        with patch.object(bridge, 'hand_totals', wraps=bridge.hand_totals) as compute:
            TOOL.run_plan(TOOL.validate_plan(plan()), events.append, time.perf_counter() + 90)
        self.assertEqual(compute.call_count, 2, 'solve must execute each admitted hero once')
        artifacts = [row for row in events if row.get('kind') == 'artifact']
        self.assertEqual([row['name'] for row in artifacts], ['teacher.json'])
        teacher = base64.b64decode(artifacts[0]['artifact_base64'], validate=True)
        board, hands, actions = bridge.teacher_actions(teacher)
        self.assertEqual([bridge.hand_name(hand) for hand in hands], BASE['permutation'][:2])
        self.assertEqual(set(actions), set(BASE['permutation'][:2]))
        census = [row for row in events if row.get('kind') == 'solve_summary']
        self.assertEqual(len(census), 1)
        self.assertTrue(census[0]['complete'])
        self.assertEqual(census[0]['completed_hands'], 2)
        self.assertEqual(census[0]['coverage'], 'test-subset')

    def test_deadline_cannot_publish_a_complete_teacher(self):
        events = []
        with self.assertRaises(ValueError):
            TOOL.run_plan(TOOL.validate_plan(plan()), events.append, time.perf_counter() - 1)
        self.assertFalse(any(row.get('kind') == 'artifact' for row in events))

    def test_real_host_check_hit_default_and_changed_stack_are_distinct(self):
        completion = TOOL.load_completion()
        self.assertTrue(callable(getattr(completion, 'play', None)), 'real Session path missing')
        from pontius import eval_bridge as bridge
        from pontius.execution import begin_run, child_context, CONTEXT_ENV
        from pontius.immutable_blueprint import BlueprintActionEntry, ImmutableBlueprintActionSource
        from pontius.blueprint_artifact.codec import encode_blueprint
        import os
        bank = dict(seed_start='0' * 64, seed_count=8, indices=list(range(16)),
                    holdout_seed_start='f' * 64, holdout_seed_count=1,
                    sizing_rationale='Real host subset correctness control.')
        board = bridge.board_cards(BASE['board'])
        scan = completion.witnesses(board, BASE['permutation'], bank, deadline=float('inf'))
        name, witness = next(iter(scan['selected'].items()))
        hand = tuple(witness['private_hands'][2])
        row = BlueprintActionEntry(bridge.root_key(bridge.replay_root(), board, hand), bridge.CHECK)
        wire = encode_blueprint(ImmutableBlueprintActionSource('test-check-control', (row,)))
        empty = encode_blueprint(ImmutableBlueprintActionSource('test-empty-control', ()))
        context = begin_run(ROOT, allow_working_tree=True)
        (ROOT / 'tmp').mkdir(exist_ok=True)
        before = Path.cwd()
        try:
            os.chdir(ROOT)
            with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as directory:
                with patch.dict(os.environ, {CONTEXT_ENV: child_context(context)}):
                    hit = completion.play(witness, board, wire, {name: bridge.CHECK},
                                          Path(directory), 0, 'check-control')
                    off = completion.play(witness, board, empty, {}, Path(directory), 1,
                                          'off-control')
                    changed = completion.play(witness, board, wire, {name: bridge.CHECK},
                                              Path(directory), 2, 'stack-control', stacks=6)
                    host = sys.modules[completion.load_tool('v0a_table_session').ALIAS]
                    send = host.ChildConnection.send

                    def fail_after_send(connection, raw, deadline):
                        send(connection, raw, deadline)
                        raise host.HostRefusal('transport_failed')

                    with patch.object(host.ChildConnection, 'send', fail_after_send):
                        failed = completion.play(witness, board, wire, {name: bridge.CHECK},
                                                 Path(directory), 3, 'transport-control')
            self.assertEqual(hit['classification']['classification'], 'hit', hit['classification'])
            self.assertEqual(off['classification']['classification'], 'unsupported',
                             off['classification'])
            self.assertEqual(changed['classification']['observed_table_hits'], 0,
                             changed['classification'])
            self.assertTrue(all(row['classification']['chip_eligible']
                                for row in (hit, off, changed)))
            self.assertEqual(failed['session']['status'], 'failed')
            self.assertEqual(failed['classification']['classification'], 'excluded')
            self.assertFalse(failed['classification']['chip_eligible'])
            from pontius.eval_agreement import classify
            from pontius.blueprint_artifact.codec import decode_blueprint
            relabeled = copy.deepcopy(hit['session'])
            captured = relabeled['hands'][0]['result']
            frames = [json.loads(line) for line in
                      base64.b64decode(captured['child_stdout_base64']).splitlines()]
            changed_reasons = 0
            for frame in frames:
                record = frame.get('decision')
                if record and record['street'] == 'river':
                    self.assertEqual(record['selection_reason'], 'table_hit')
                    record['selection_reason'] = 'passive_default'
                    changed_reasons += 1
            self.assertEqual(changed_reasons, 1)
            captured['child_stdout_base64'] = base64.b64encode(
                b''.join(json.dumps(frame).encode() + b'\n' for frame in frames)).decode()
            altered = classify(relabeled, blueprint=decode_blueprint(wire),
                               teacher_actions={name: bridge.CHECK}, board=board,
                               private_hands=tuple(map(tuple, witness['private_hands'])))
            self.assertTrue(altered['chip_eligible'])
            self.assertEqual(altered['classification'], 'disagreement')
        finally:
            os.chdir(before)

    def test_supervised_three_phase_subset_and_bound_input_failures(self):
        from pontius import eval_bridge as bridge
        from pontius.execution import begin_run
        completion = TOOL.load_completion()
        context = begin_run(ROOT, allow_working_tree=True)
        (ROOT / 'tmp').mkdir(exist_ok=True)

        def bind(path):
            return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())

        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as root:
            directory = Path(root) / 'snapshot'
            git = os.environ['PONTIUS_GIT']
            subprocess.run([git, 'clone', '--shared', '--no-checkout', str(ROOT), str(directory)],
                           check=True, capture_output=True)
            subprocess.run([git, '-C', str(directory), 'checkout', '--detach', context['commit']],
                           check=True, capture_output=True)
            # Dirty correctness also exercises current bytes; frozen runs copy identical blobs.
            for name in ('src/pontius/eval_bridge.py', 'src/pontius/eval_agreement.py',
                         'tools/v0a_eval_panel.py', 'tools/v0a_eval_panel_completion.py'):
                shutil.copyfile(ROOT / name, directory / name)

            def phase(proposed):
                proposed['resource'] = dict(seconds=120, memory_mib=2048)
                proposed_path = directory / 'plan.json'
                proposed_path.write_text(json.dumps(proposed), encoding='utf-8')
                journal = directory / 'execution_journal.jsonl'
                before = journal.read_bytes().splitlines() if journal.exists() else []
                completed = subprocess.run([sys.executable, '-B', '-P', '-W',
                    'error::ResourceWarning', str(directory / 'tools/v0a_eval_panel.py'),
                    'run', '--plan', str(proposed_path), '--development'],
                    cwd=directory, capture_output=True, timeout=150)
                self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
                after = journal.read_bytes().splitlines()
                self.assertEqual(len(after), len(before) + 1, 'exactly one journal row per phase')
                entry = json.loads(after[-1])
                self.assertEqual(entry['source_verified'], context['verified'])
                result_path = directory / entry['output']
                self.assertEqual(bind(result_path)['sha256'], entry['output_sha256'])
                report = json.loads(result_path.read_bytes())
                destination = result_path.parent
                self.assertTrue(report['phase_complete'])
                return report, destination, result_path

            solved, solve_dir, solve_result = phase(plan())
            exported_plan = plan('export')
            exported_plan['inputs'] = dict(teacher=bind(solve_dir / 'teacher.json'),
                                          producer_result=bind(solve_result))
            exported, export_dir, export_result = phase(exported_plan)
            self.assertEqual((solve_dir / 'teacher.json').read_bytes(),
                             (export_dir / 'teacher.json').read_bytes())
            self.assertLess((export_dir / 'blueprint.json').stat().st_size, bridge.ARTIFACT_CAP)
            wrong = copy.deepcopy(exported_plan)
            wrong['inputs']['teacher']['sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                completion.teacher_input(wrong)
            agreed_plan = plan('agreement')
            agreed_plan['inputs'] = dict(teacher=bind(export_dir / 'teacher.json'),
                                         blueprint=bind(export_dir / 'blueprint.json'),
                                         producer_result=bind(export_result))
            agreed_plan['witness_bank'] = dict(seed_start='0' * 64, seed_count=2048,
                indices=list(range(16)), holdout_seed_start='f' * 64, holdout_seed_count=1,
                sizing_rationale='Fixed finite correctness bank; actual census gates acceptance.')
            agreed, _, _ = phase(agreed_plan)
            accounting = agreed['agreement_accounting']
            self.assertEqual(accounting['primary']['hits'], 2)
            self.assertEqual(accounting['scheduled_attempts'], 5)
            self.assertEqual(accounting['missing_outcomes'], 0)
            self.assertEqual(accounting['missing_pool_hands'], [])

    def test_partial_results_and_artifact_publication_keep_their_identity(self):
        completion = TOOL.load_completion()
        events = []
        admitted = TOOL.validate_plan(plan())
        TOOL.run_plan(admitted, events.append, time.perf_counter() + 90)
        self.assertTrue(completion.complete(events, admitted.document))
        teacher_row = next(row for row in events if row.get('kind') == 'teacher_hand')
        self.assertFalse(completion.complete([r for r in events if r is not teacher_row],
                                              admitted.document))
        self.assertFalse(completion.complete(events + [teacher_row], admitted.document))
        artifact = next(row for row in events if row.get('kind') == 'artifact')
        raw = base64.b64decode(artifact['artifact_base64'])
        for after_rename in (False, True):
            with self.subTest(after_rename=after_rename), tempfile.TemporaryDirectory() as folder:
                report = dict(observations=[copy.deepcopy(artifact)])
                replace = os.replace

                def interrupted(source, destination):
                    if after_rename:
                        replace(source, destination)
                    raise KeyboardInterrupt

                with patch.object(completion.os, 'replace', interrupted):
                    with self.assertRaises(KeyboardInterrupt):
                        completion.retain(report, Path(folder))
                row = report['observations'][0]
                self.assertEqual(row['sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(row['path'], 'teacher.json')
                self.assertEqual(row['retention'], 'complete' if after_rename else 'pending')
                if after_rename:
                    self.assertEqual((Path(folder) / row['path']).read_bytes(), raw)
                else:
                    self.assertEqual(base64.b64decode(row['artifact_base64']), raw)

    def test_agreement_accounting_refuses_orphan_and_mismatched_outcomes(self):
        completion = TOOL.load_completion()
        proposed = plan('agreement')
        name = proposed['permutation'][0]
        scheduled = dict(kind='attempt_scheduled', ordinal=0, hand=name,
                         label='primary', witness={})
        outcome = dict(kind='host_attempt', ordinal=0, hand=name,
                       result=dict(label='primary', witness={},
                                   classification=dict(classification='hit', chip_eligible=True,
                                                       agreement_eligible=True)))
        self.assertEqual(completion.accounting([scheduled], proposed)['missing_outcomes'], 1)
        for observations in ([outcome], [scheduled, dict(outcome, ordinal=1)],
                             [scheduled, dict(outcome, hand=proposed['permutation'][1])]):
            with self.subTest(observations=observations), self.assertRaises(ValueError):
                completion.accounting(observations, proposed)


if __name__ == '__main__':
    unittest.main()
