"""Native bounded-read controls; mutation schedules are not race prevalence claims."""
import ast
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path.cwd()
TOOL = ROOT / 'tools/v0a_evaluation_v2.py'
BASE = '5845f32f010a44d924abc2f50ae142d1c6adec1b'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


class SuccessorBoundaryTests(unittest.TestCase):
    def test_exact_source_admission_and_sealed_helper(self):
        runner = load(TOOL, 'successor_source_control')
        for alias in runner.ALIASES:
            sys.modules.pop(alias, None)
        try:
            source = runner.admit_source(ROOT)
            self.assertIn('tools/v0a_evaluation_v2.py', source.raw)
            self.assertNotIn('tools/v0a_evaluation.py', source.raw)
            helper = 'tools/v0a_evaluation_contract.py'
            self.assertEqual(source.raw[helper], source.command('show', BASE+':'+helper))
            rows = [hashlib.sha256(raw).hexdigest().encode()+b'  '+p.encode()+b'\n'
                    for p, raw in source.raw.items()]
            self.assertEqual(source.manifest, hashlib.sha256(b''.join(sorted(rows))).hexdigest())
            source.check()
        finally:
            for alias in runner.ALIASES:
                sys.modules.pop(alias, None)

    def test_import_guard_requires_each_exact_origin_and_loader(self):
        checker = load(ROOT/'tools/check_stabilization_boundaries.py', 'successor_guard_control')
        for wrapper in ('tools/v0a_evaluation.py', 'tools/v0a_evaluation_v2.py'):
            sources = {wrapper: (ROOT/wrapper).read_bytes()}
            checker.enforce_evaluation_import_policy(sources)
            for before, after in (
                (wrapper.encode(), b'tools/wrong_origin.py'),
                (b'import argparse', b'import pontius'),
                (b'(NEW[1], OLD[5], OLD[3])', b'(NEW[1], OLD[4], OLD[3])'),
                (b'compile(s.raw[path],', b'compile(path.read_bytes(),'),
            ):
                with self.subTest(wrapper=wrapper, mutation=before):
                    self.assertIn(before, sources[wrapper])
                    changed = {wrapper: sources[wrapper].replace(before, after)}
                    with self.assertRaises(checker.BoundaryError):
                        checker.enforce_evaluation_import_policy(changed)


if __name__ == '__main__':
    unittest.main()
