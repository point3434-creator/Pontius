"""Current v3 source, native child, reader and import-boundary engineering controls."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path.cwd()
TOOL = ROOT / 'tools/v0a_evaluation_v3.py'
BASE = '363c9fb669e19a30375537ee5e92ea338a840a2d'
PACKAGE = ('src/pontius/blueprint_preparation/__init__.py',
           'src/pontius/blueprint_preparation/lookup.py')
OLD = tuple('tools/' + name + '.py' for name in ('v0a_rehearsal_driver',
    'v0a_hand_adapter', 'v0a_event_adapter', 'v0a_table_host', 'v0a_table_session',
    'v0a_seeded_deals'))
HELPER = 'tools/v0a_evaluation_contract.py'
BLUEPRINT = 'tests/fixtures/table_host/empty_blueprint.json'
ALIASES = ('_pontius_evaluation_contract', '_pontius_evaluation_dealer',
           '_pontius_evaluation_host')


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clear_aliases():
    for alias in ALIASES:
        sys.modules.pop(alias, None)


def git(repo, *args, content=None):
    result = subprocess.run([os.environ['PONTIUS_GIT'], '--no-replace-objects',
        '--no-optional-locks', '-c', 'core.autocrlf=false', '-c', 'core.longpaths=true',
        '-C', str(repo), *args], input=content, capture_output=True, check=True, timeout=120)
    return result.stdout


def committed_change(repo, path, raw):
    """Change only this disposable clone's index/ref; retain its preceding commit."""
    target = repo/path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    oid = git(repo, 'hash-object', '-w', '--stdin', content=raw).decode().strip()
    git(repo, 'update-index', '--add', '--cacheinfo', '100644', oid, path)
    tree = git(repo, 'write-tree').decode().strip()
    previous = git(repo, 'rev-parse', 'HEAD').decode().strip()
    commit = git(repo, '-c', 'user.name=V3 source control',
        '-c', 'user.email=v3-control@invalid', 'commit-tree', tree, '-p', previous,
        content=b'Finite disposable source-refusal control\n').decode().strip()
    git(repo, 'update-ref', 'HEAD', commit, previous)
    return commit


class SourceAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(TOOL.is_file(), 'The current v3 evaluator is absent')
        self.r = load(TOOL, 'current_v3_source')
        clear_aliases()
        self.addCleanup(clear_aliases)
        self.base = Path(tempfile.mkdtemp(prefix='evaluation-v3-source-'))

    def clone(self):
        target = self.base / ('source-' + str(len(list(self.base.iterdir()))))
        git(ROOT, 'clone', '--quiet', '--shared', '--no-checkout', str(ROOT), str(target))
        commit = git(ROOT, 'rev-parse', 'HEAD').decode().strip()
        git(target, 'checkout', '--quiet', '--detach', commit)
        return target

    def admit(self, repo):
        runner = load(repo/'tools/v0a_evaluation_v3.py', 'current_v3_cloned_source')
        clear_aliases()
        previous = Path.cwd()
        try:
            os.chdir(repo)
            return runner, runner.admit_source(repo)
        finally:
            os.chdir(previous)

    def test_exact_source_population_raw_loading_and_manifest(self):
        source = self.r.admit_source(ROOT)
        self.assertEqual(self.r.BASE, BASE)
        self.assertEqual(self.r.NEW, ('tools/v0a_evaluation_v3.py', HELPER))
        base = {}
        for row in git(ROOT, 'ls-tree', '-r', '-z', BASE, '--', 'src/pontius',
                       *OLD, HELPER, BLUEPRINT).split(b'\0'):
            if row:
                meta, path = row.split(b'\t')
                base[path.decode()] = meta.split()[2].decode()
        self.assertEqual(set(source.raw), set(base) | set(PACKAGE) | {self.r.NEW[0]})
        changed = {'src/pontius/v0a/runtime.py', *OLD[1:5]}
        for path, oid in base.items():
            if path not in changed:
                self.assertEqual(source.raw[path], git(ROOT, 'cat-file', 'blob', oid), path)
        for alias, path in zip(ALIASES, (HELPER, OLD[5], OLD[3])):
            self.assertIs(source.modules[alias], sys.modules[alias])
            self.assertEqual(source.modules[alias].__file__, str(ROOT/path))
        self.assertEqual(source.contract.decode_request.__code__.co_filename, str(ROOT/HELPER))
        self.assertEqual(source.dealer.deal_for_hand.__code__.co_filename, str(ROOT/OLD[5]))
        self.assertEqual(source.host.Job.__init__.__code__.co_filename, str(ROOT/OLD[3]))
        self.assertEqual(source.raw[self.r.NEW[0]], TOOL.read_bytes())
        rows = {path: hashlib.sha256(raw).hexdigest().encode()+b'  '+path.encode()+b'\n'
                for path, raw in source.raw.items()}
        self.assertEqual(source.manifest, hashlib.sha256(b''.join(sorted(rows.values()))).hexdigest())
        child = [row for path, row in rows.items()
                 if path.startswith('src/pontius/') or path in OLD[:3]]
        self.assertEqual(source.child_manifest, hashlib.sha256(b''.join(sorted(child))).hexdigest())
        self.assertFalse(any(name == 'pontius' or name.startswith('pontius.')
                             for name in sys.modules))
        source.check()

    def test_v1_and_v2_stay_closed_to_current_source(self):
        for name in ('v0a_evaluation.py', 'v0a_evaluation_v2.py'):
            with self.subTest(origin=name):
                clear_aliases()
                old = load(ROOT/'tools'/name, 'sealed_evaluator_refusal')
                with self.assertRaisesRegex(ValueError, '^source_invalid$'):
                    old.admit_source(ROOT)

    def test_changed_unexcepted_committed_blobs_refuse(self):
        for path in ('src/pontius/immutable_blueprint.py', HELPER, OLD[5], BLUEPRINT):
            with self.subTest(path=path):
                repo = self.clone()
                before = (repo/path).read_bytes()
                committed_change(repo, path, before+b'\n')
                with self.assertRaisesRegex(ValueError, '^source_invalid$'):
                    self.admit(repo)

    def test_extra_committed_package_sibling_and_flat_module_refuse(self):
        for path in ('src/pontius/blueprint_preparation/extra.py', 'src/pontius/extra.py'):
            with self.subTest(path=path):
                repo = self.clone()
                committed_change(repo, path, b'"""Unadmitted source control."""\n')
                with self.assertRaisesRegex(ValueError, '^source_invalid$'):
                    self.admit(repo)

    def test_captured_self_helper_dealer_and_host_drift_refuse(self):
        for path in ('tools/v0a_evaluation_v3.py', HELPER, OLD[5], OLD[3]):
            with self.subTest(path=path):
                repo = self.clone()
                runner, source = self.admit(repo)
                target = repo/path
                preserved = self.base/('captured-'+str(len(list(self.base.iterdir()))))
                preserved.write_bytes(target.read_bytes())
                with target.open('ab') as stream:
                    stream.write(b'\n# late disposable source drift\n')
                with self.assertRaisesRegex(ValueError, '^source_invalid$'):
                    source.check()
                self.assertNotEqual(target.read_bytes(), preserved.read_bytes())

    def test_untracked_package_addition_after_admission_refuses(self):
        repo = self.clone()
        runner, source = self.admit(repo)
        (repo/'src/pontius/blueprint_preparation/late.py').write_bytes(b'pass\n')
        with self.assertRaisesRegex(ValueError, '^source_invalid$'):
            source.check()

    def test_real_child_source_drift_is_retained_and_refused(self):
        repo = self.clone()
        runner, source = self.admit(repo)
        fixture = json.loads((ROOT/'tests/fixtures/evaluation/controls.json').read_bytes())
        matrix = source.contract.build_matrix(fixture['request'], fixture['deals'], 'v3drift')
        pair, unit = matrix['pairs'][0], matrix['units'][0]
        input_path, target = self.base/'pair.json', repo/'src/pontius/__init__.py'
        input_path.write_bytes(pair['input_bytes'])
        (self.base/'preserved-init.py').write_bytes(target.read_bytes())
        root, temp, marker = self.base/'unit', self.base/'temp', self.base/'executed'
        root.mkdir()
        temp.mkdir()
        binding = dict(fixture['binding'], **unit, source=source,
            source_commit=source.commit, source_manifest_sha256=source.manifest,
            child_source_manifest_sha256=source.child_manifest, request_sha256='0'*64,
            trial_budget_ms=60000, saved={input_path: runner.read_stable(input_path)})
        # Schedule only a source/pipe fault in a real native child. Real containment,
        # capture, revalidation, failure classification and cleanup all execute.
        code = ('from pathlib import Path; import os; f=Path(%r).open("ab"); '
                'f.write(b"\\n# source fault\\n"); f.close(); '
                'Path(%r).write_bytes(b"ran"); os.write(1,b"{v3-source-prefix")') % (
                    str(target), str(marker))
        with patch.object(runner, 'child_argv', return_value=[
                sys.executable, '-B', '-P', '-c', code]):
            outcome = runner.run_trial(binding, dict(root=root, input=input_path, temp=temp),
                                       runner.clock_ns()+120000000000)
        self.assertEqual(marker.read_bytes(), b'ran')
        self.assertEqual((root/'stdout.bin').read_bytes(), b'{v3-source-prefix')
        self.assertEqual(outcome['failure_reason'], 'source_invalid')
        self.assertTrue(outcome['launched'] and outcome['cleanup_complete'])
        self.assertIsNone(outcome['net_chips'])
        self.assertEqual(json.loads((root/'result.json').read_bytes()), outcome)


class CurrentBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.checker = load(ROOT/'tools/check_stabilization_boundaries.py', 'current_v3_guard')

    def test_current_new_origins_are_classified(self):
        self.checker.enforce_origin_classification(
            {path: (ROOT/path).read_bytes() for path in PACKAGE},
            {'tools/v0a_evaluation_v3.py': b'', 'tools/run_evaluation_history.py': b''})
        for path in ('src/pontius/blueprint_preparation.py',
                     'src/pontius/blueprint_preparation/extra.py'):
            with self.subTest(path=path):
                with self.assertRaises(self.checker.BoundaryError):
                    self.checker.enforce_origin_classification({path: b''}, {})

    def test_all_three_current_evaluator_import_and_loader_refusals(self):
        for wrapper in ('tools/v0a_evaluation.py', 'tools/v0a_evaluation_v2.py',
                        'tools/v0a_evaluation_v3.py'):
            raw = (ROOT/wrapper).read_bytes()
            self.checker.enforce_evaluation_import_policy({wrapper: raw})
            for before, after in (
                (wrapper.encode(), b'tools/wrong_origin.py'),
                (b'import argparse', b'import pontius'),
                (b'import argparse', b'import importlib'),
                (b'(NEW[1], OLD[5], OLD[3])', b'(NEW[1], OLD[4], OLD[3])'),
                (b'compile(s.raw[path],', b'compile(path.read_bytes(),'),
                (b'_pontius_evaluation_dealer', b'_different_dealer'),
            ):
                with self.subTest(wrapper=wrapper, mutation=before):
                    self.assertIn(before, raw)
                    with self.assertRaises(self.checker.BoundaryError):
                        self.checker.enforce_evaluation_import_policy(
                            {wrapper: raw.replace(before, after)})
            for extra in (b'\nexec("pass")\n', b'\ns.host.Source()\n',
                          b'\ns.host.Table()\n', b'\ns.host.Session()\n',
                          b'\ns.dealer.main()\n', b'\n__import__("os")\n'):
                with self.subTest(wrapper=wrapper, extra=extra):
                    with self.assertRaises(self.checker.BoundaryError):
                        self.checker.enforce_evaluation_import_policy({wrapper: raw+extra})

    def test_preparation_exact_outgoing_incoming_and_inert_initializer(self):
        policy = getattr(self.checker, 'enforce_blueprint_preparation_import_policy', None)
        self.assertTrue(callable(policy), 'The preparation boundary guard is absent')
        lookup = PACKAGE[1]
        sources = {path: (ROOT/path).read_bytes() for path in PACKAGE}
        sources['src/pontius/v0a/runtime.py'] = (
            b'from pontius.blueprint_preparation.lookup import PreparedBlueprint\n')
        policy(sources)
        self.checker.enforce_v0a_import_policy(sources)
        self.checker.enforce_decision_provider_import_policy(sources)
        for edge in ('os', 'pathlib', 'subprocess', 'pontius.river',
                     'pontius.v0a.replay', 'pontius.holdem_cards',
                     'pontius.decision_provider.providers', 'numpy'):
            with self.subTest(edge=edge):
                with self.assertRaises(self.checker.BoundaryError):
                    policy({lookup: ('import '+edge+'\n').encode()})
        for route in ('open("x")', '__import__("os")', 'compile("pass", "x", "exec")',
                      'value.SixSeatHoldemDeal', 'globals()', 'value.run_path("x")'):
            with self.subTest(route=route):
                with self.assertRaises(self.checker.BoundaryError):
                    policy({lookup: (route+'\n').encode()})
        for origin in ('src/pontius/immutable_blueprint.py', 'tools/v0a_table_host.py',
                       'src/pontius/decision_provider/providers.py'):
            with self.subTest(origin=origin):
                with self.assertRaises(self.checker.BoundaryError):
                    policy({origin: b'from pontius.blueprint_preparation.lookup import X\n'})
        for raw in (b'import hashlib\n', b'VALUE = 1\n'):
            with self.subTest(initializer=raw):
                with self.assertRaises(self.checker.BoundaryError):
                    policy({PACKAGE[0]: raw})

    def test_history_exact_origin_cli_and_standard_library_guard(self):
        policy = getattr(self.checker, 'enforce_evaluation_history_import_policy', None)
        self.assertTrue(callable(policy), 'The fixed historical launcher guard is absent')
        path = 'tools/run_evaluation_history.py'
        raw = (ROOT/path).read_bytes()
        policy({path: raw})
        for extra in (b'\nimport pontius\n', b'\nfrom tools.test_orchestration import model\n',
                      b'\nimport importlib\n', b'\nexec("pass")\n',
                      b'\nparser.add_argument("--ref")\n',
                      b'\nparser.add_argument("--executable")\n',
                      b'\nparser.add_argument("--module")\n'):
            with self.subTest(extra=extra):
                with self.assertRaises(self.checker.BoundaryError):
                    policy({path: raw+extra})
        for before, after in ((BASE.encode(), b'0'*40),
                              (b"'--suite'", b"'--test-path'"),
                              (b"('tests/test_v0a_evaluation_v2.py', 8)",
                               b"('tests/test_v0a_evaluation_v2.py', 0)")):
            with self.subTest(mutation=before):
                self.assertIn(before, raw)
                with self.assertRaises(self.checker.BoundaryError):
                    policy({path: raw.replace(before, after)})


class NativeRoundTripTests(unittest.TestCase):
    def test_current_real_twelve_trial_artifacts_read_with_all_versions(self):
        runner = load(TOOL, 'current_v3_real_roundtrip')
        clear_aliases()
        self.addCleanup(clear_aliases)
        source = runner.admit_source(ROOT)
        base = Path(tempfile.mkdtemp(prefix='evaluation-v3-roundtrip-'))
        fixture = json.loads((ROOT/'tests/fixtures/evaluation/controls.json').read_bytes())
        request, output = base/'request.json', base/'out'
        request.write_bytes(runner.encode(fixture['request']))
        args = types.SimpleNamespace(request=request, output_root=output,
            evaluation_id='pontius-v0a-evaluation-v1-correctness-v3roundtrip')
        # No successful provider, dealer, host, child, publication or result is substituted.
        self.assertEqual(runner.execute(args, source), 0)
        actual = runner.read_completed(output)
        self.assertEqual(actual['source_commit'], source.commit)
        self.assertEqual(actual['source_manifest_sha256'], source.manifest)
        self.assertEqual(actual['completed_pairs'], 6)
        self.assertEqual(actual['completed_trials'], 12)
        self.assertFalse(actual['evidentiary'])
        self.assertFalse((output/'.publication-pending').exists())
        plan = json.loads((output/'plan.json').read_bytes())
        for trial, unit in zip(actual['trials'], plan['units']):
            unit_root = output/('u%03d' % unit['ordinal'])
            native = json.loads((unit_root/'result.json').read_bytes())
            launch = json.loads((unit_root/'launch.json').read_bytes())
            self.assertEqual(trial['state'], 'completed')
            self.assertEqual(trial['exit_code'], 0)
            self.assertTrue(native['launched'] and native['cleanup_complete'])
            self.assertTrue(launch['created_suspended'] and launch['assigned'] and launch['resumed'])
            self.assertGreater(launch['pid'], 0)
            self.assertTrue((unit_root/'stdout.bin').stat().st_size > 0)
            self.assertEqual((unit_root/'stderr.bin').read_bytes(), b'')
        for name in ('v0a_evaluation.py', 'v0a_evaluation_v2.py'):
            with self.subTest(reader=name):
                reader = load(ROOT/'tools'/name, 'sealed_artifact_reader')
                self.assertEqual(reader.read_completed(output), actual)


class BoundedReadTests(unittest.TestCase):
    def setUp(self):
        self.r = load(TOOL, 'bounded_read_control')
        self.base = Path(tempfile.mkdtemp(prefix='bounded-read-'))

    def test_stable_bytes_tokens_and_cap_boundaries(self):
        old = load(ROOT / 'tools/v0a_evaluation.py', 'old_read_control')
        for length in (0, 1, 4096, 65536):
            path = self.base / str(length)
            raw = b'x' * length
            path.write_bytes(raw)
            for cap in (max(0, length-1), length, length+1, 16777216):
                with self.subTest(length=length, cap=cap):
                    if cap < length:
                        with self.assertRaisesRegex(ValueError, '^input_invalid$'):
                            self.r.read_stable(path, cap)
                    else:
                        result = self.r.read_stable(path, cap)
                        self.assertEqual(result, old.read_stable(path, cap))
                        self.assertEqual(result[0], raw)

    def test_read_request_respects_observed_size_ceiling(self):
        native_open = Path.open
        for length in (0, 3, 4096):
            path = self.base / str(length)
            raw = b'a' * length
            path.write_bytes(raw)
            requests = []
            class Stream:
                def __init__(self, file):
                    self.file = file
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    return self.file.__exit__(*args)
                def fileno(self):
                    return self.file.fileno()
                def read(self, amount):
                    requests.append(amount)
                    if amount > length + 1:
                        raise AssertionError('read request exceeds observed size plus one')
                    return self.file.read(amount)
            def opened(target, *args, **kwargs):
                file = native_open(target, *args, **kwargs)
                return Stream(file) if target == path and args == ('rb',) else file
            with patch.object(Path, 'open', opened):
                self.assertEqual(self.r.read_stable(path)[0], raw)
            self.assertEqual(requests, [length+1])

    def scheduled_read(self, function, mode, cap=16777216):
        parent = self.base / ('schedule-' + str(len(list(self.base.iterdir()))))
        parent.mkdir()
        path = parent / 'input'
        path.write_bytes(b'abc')
        before = path.stat()
        native_open, events = Path.open, []
        class Stream:
            def __init__(self, file):
                self.file = file
            def __enter__(self):
                return self
            def __exit__(self, *args):
                result = self.file.__exit__(*args)
                if mode == 'replace':
                    path.rename(parent/'preserved')
                    with native_open(path, 'xb') as writer:
                        writer.write(b'abc')
                    events.append('replaced')
                elif mode == 'ancestor':
                    preserved = parent.with_name(parent.name+'-preserved')
                    parent.rename(preserved)
                    parent.mkdir()
                    os.link(preserved/'input', path)
                    events.append('ancestor-replaced')
                return result
            def fileno(self):
                return self.file.fileno()
            def read(self, amount):
                if mode in ('grow', 'shrink', 'restored'):
                    with native_open(path, 'r+b') as writer:
                        if mode == 'shrink':
                            writer.truncate(1)
                        else:
                            writer.seek(0, 2)
                            writer.write(b'XYZ')
                    events.append('mutated')
                raw = self.file.read(amount)
                events.append(('read', raw))
                if mode == 'restored':
                    with native_open(path, 'r+b') as writer:
                        writer.truncate(3)
                    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
                    events.append('restored')
                return raw
        def opened(target, *args, **kwargs):
            if target == path and args == ('rb',) and mode == 'before-handle':
                path.rename(parent/'preserved')
                with native_open(path, 'xb') as writer:
                    writer.write(b'abc')
                events.append('before-handle-replaced')
            file = native_open(target, *args, **kwargs)
            return Stream(file) if target == path and args == ('rb',) else file
        with patch.object(Path, 'open', opened):
            try:
                result = function(path, cap)
            except ValueError as error:
                self.assertEqual(str(error), 'input_invalid')
                result = None
        self.assertTrue(events, 'The native schedule must actually execute')
        if mode in ('ancestor', 'restored'):
            self.assertEqual(self.r.identity(path.stat()), self.r.identity(before))
        return result, events

    def test_real_growth_shrink_and_named_replacement_refuse(self):
        for mode in ('grow', 'shrink', 'replace', 'before-handle'):
            with self.subTest(mode=mode):
                result, events = self.scheduled_read(self.r.read_stable, mode)
                self.assertIsNone(result)
                if mode in ('grow', 'shrink'):
                    self.assertIn('mutated', events)
                else:
                    self.assertIn('replaced' if mode == 'replace' else
                                  'before-handle-replaced', events)

    def test_ancestor_replacement_refuses_with_same_file_identity(self):
        result, events = self.scheduled_read(self.r.read_stable, 'ancestor')
        self.assertIsNone(result)
        self.assertIn('ancestor-replaced', events)
        self.assertIn(('read', b'abc'), events)

    def test_restored_growth_discriminates_missing_extra_byte(self):
        # Mutate only the production read bound; the injector and oracle stay identical.
        tree = ast.parse(TOOL.read_bytes())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                        and n.name == 'read_stable')
        reads = [n for n in ast.walk(function) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == 'read']
        self.assertEqual(len(reads), 1)
        reads[0].args = [ast.parse('before[2]', mode='eval').body]
        mutant = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
        namespace = {}
        exec(compile(mutant, '<deliberately-wrong-size-only-read>', 'exec'),
             self.r.__dict__, namespace)
        for cap in (3, 16777216):
            with self.subTest(cap=cap):
                result, events = self.scheduled_read(self.r.read_stable, 'restored', cap)
                self.assertIsNone(result)
                self.assertIn(('read', b'abcX'), events)
                self.assertIn('restored', events)
                wrong, controls = self.scheduled_read(namespace['read_stable'], 'restored', cap)
                self.assertEqual(wrong[0], b'abc')
                self.assertIn(('read', b'abc'), controls)
                self.assertIn('restored', controls)

    def test_create_file_round_trip_and_no_overwrite(self):
        path = self.base/'created'
        captured = self.r.create_file(path, b'payload\n')
        self.assertEqual(self.r.read_stable(path), captured)
        with self.assertRaises(FileExistsError):
            self.r.create_file(path, b'different')
        self.assertEqual(path.read_bytes(), b'payload\n')


if __name__ == '__main__':
    unittest.main()
