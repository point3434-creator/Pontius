"""Real request/publication boundary controls for the bounded seeded dealer."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('seeded_test_helpers',
                                            Path(__file__).with_name('test_seeded_deals.py'))
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


class FaultFile:
    """Control one I/O failure after the real stream has performed its resource effect."""
    def __init__(self, stream, fault):
        self.stream, self.fault = stream, fault

    def __getattr__(self, name):
        return getattr(self.stream, name)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stream.close()
        if self.fault == 'close':
            raise OSError('controlled close completion failure')

    def write(self, raw):
        if self.fault == 'short':
            return self.stream.write(raw[:7])
        return self.stream.write(raw)

    def flush(self):
        self.stream.flush()
        if self.fault == 'flush':
            raise OSError('controlled flush completion failure')

    def read(self, size):
        raw = self.stream.read(size)
        if self.fault == 'read':
            raise OSError('controlled read completion failure')
        return raw


class SeededBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(helpers.TOOL.is_file(), 'approved seeded dealer is absent')
        self.m = helpers.load_tool()
        self.assertTrue(hasattr(self.m, 'main'), 'approved file CLI is absent')
        local_temp = Path(os.environ['TEMP'])
        self.folder = Path(tempfile.mkdtemp(prefix='seeded-boundary-',
                           dir=local_temp if local_temp.drive.upper() == 'D:' else 'D:/'))
        self.request = self.folder / 'request.json'
        self.output = self.folder / 'session.json'
        self.raw = (helpers.FIXTURES / 'request.json').read_bytes()
        self.expected = (helpers.FIXTURES / 'expected_session.json').read_bytes()
        self.request.write_bytes(self.raw)

    def arguments(self):
        return ['--request', str(self.request), '--output', str(self.output)]

    def run_main(self, *, short_stdout=False, args=None):
        # Real finite files capture the os.write seam; short writes really retain a prefix.
        real_write = os.write
        writes = []
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            def write(fd, raw):
                writes.append((fd, raw))
                target = stdout if fd == 1 else stderr
                return real_write(target.fileno(), raw[:7] if fd == 1 and short_stdout else raw)
            with patch.object(self.m.os, 'write', side_effect=write):
                code = self.m.main(self.arguments() if args is None else args)
            stdout.seek(0)
            stderr.seek(0)
            return code, stdout.read(), stderr.read(), writes

    def refused(self, result, code):
        self.assertEqual(result[0], 1)
        self.assertEqual(result[1], b'')
        self.assertEqual(result[2], ('REFUSED '+code+'\n').encode('ascii'))
        self.assertEqual([fd for fd, _ in result[3]], [2])

    def test_success_exclusively_publishes_exact_bytes_and_bound_receipt(self):
        result = self.run_main()
        self.assertEqual(result[0], 0, result[2])
        self.assertEqual(result[2], b'')
        self.assertEqual([fd for fd, _ in result[3]], [1])
        self.assertEqual(self.output.read_bytes(), self.expected)
        expected = {'version': 'pontius-v0a-seeded-deals-result-v1', 'status': 'generated',
                    'algorithm': 'sha256-counter-fisher-yates-v1', 'seed': helpers.SEED,
                    'hand_count': 3, 'request_sha256': hashlib.sha256(self.raw).hexdigest(),
                    'session_sha256': hashlib.sha256(self.expected).hexdigest(),
                    'session_bytes': len(self.expected)}
        self.assertEqual(result[1], helpers.encoded(expected))
        self.assertEqual(self.request.read_bytes(), self.raw)

    def test_strict_request_schema_encoding_numeric_and_byte_limits(self):
        value = json.loads(self.raw)
        malformed = [b'', b' '*1025, b'\xef\xbb\xbf'+self.raw, self.raw+b'\r', b'\xff',
                     b'[]', b'null', self.raw.rstrip()+b'{}', b'{',
                     self.raw.replace(b'"hand_count":3', b'"hand_count":3,"hand_count":3'),
                     self.raw.replace(b'"hand_count":3', b'"hand_count":'+b'9'*700)]
        for field, values in (('hand_count', (True, False, 0, 17, -1, 3.0, '3', None)),
                              ('seed', (None, 1, 'A'*64, '\ud800', '0'*63, helpers.SEED+' ')),
                              ('version', ('other', None, 1))):
            for bad in values:
                malformed.append(helpers.encoded(dict(value, **{field: bad})))
        malformed.extend(self.raw.replace(b':3,', token) for token in
                         (b':NaN,', b':Infinity,', b':-Infinity,', b':3e0,', b':003,'))
        malformed += [helpers.encoded(dict(value, extra=1)),
                      helpers.encoded({k: v for k, v in value.items() if k != 'seed'})]
        for raw in malformed:
            with self.subTest(raw=raw[:80]):
                with self.assertRaises(self.m.Refusal) as caught:
                    self.m.decode_request(raw)
                self.assertEqual(caught.exception.code, 'input_invalid')
        padded = self.raw + b' '*(1024-len(self.raw))
        self.assertEqual(self.m.decode_request(padded), value)
        escaped = self.raw.replace(b'"seed"', b'"s\\u0065ed"')
        self.assertEqual(self.m.decode_request(escaped), value)
        with patch.object(self.m, 'int', create=True, side_effect=AssertionError('conversion')):
            with self.assertRaises(self.m.Refusal) as caught:
                self.m.decode_request(self.raw.replace(b':3,', b':123,'))
            self.assertEqual(caught.exception.code, 'input_invalid')

    def test_invalid_request_never_publishes_and_changed_raw_hash_is_preserved(self):
        self.request.write_bytes(b'{}')
        self.refused(self.run_main(), 'input_invalid')
        self.assertFalse(self.output.exists())
        escaped = self.raw.replace(b'"seed"', b'"s\\u0065ed"')
        self.request.write_bytes(escaped)
        result = self.run_main()
        self.assertEqual(result[0], 0)
        self.assertEqual(self.output.read_bytes(), self.expected)
        self.assertEqual(json.loads(result[1])['request_sha256'],
                         hashlib.sha256(escaped).hexdigest())

    def test_existing_files_directories_and_missing_parent_are_not_changed(self):
        for name, directory in (('existing-file', False), ('existing-dir', True)):
            self.output = self.folder/name
            if directory:
                self.output.mkdir()
            else:
                self.output.write_bytes(b'prior')
            self.refused(self.run_main(), 'output_failed')
            if not directory:
                self.assertEqual(self.output.read_bytes(), b'prior')
        self.output = self.folder/'absent'/'session.json'
        self.refused(self.run_main(), 'output_failed')
        self.assertFalse(self.output.parent.exists())

    def test_wrong_root_relative_traversal_and_missing_request_refuse(self):
        for request in ('relative.json', 'C:\\request.json', str(self.folder/'..'/'request.json'),
                        str(self.folder/'missing.json'), str(self.folder)):
            self.refused(self.run_main(args=['--request', request, '--output', str(self.output)]),
                         'input_invalid')
        for output in ('relative.json', 'C:\\session.json', str(self.folder/'..'/'session.json')):
            self.refused(self.run_main(args=['--request', str(self.request), '--output', output]),
                         'output_failed')
        self.assertFalse(self.output.exists())

    def test_static_junction_ancestor_refuses_without_touching_target(self):
        # A real directory junction needs no symlink privilege and exercises lstat attributes.
        target, link = self.folder/'target', self.folder/'junction'
        target.mkdir()
        (target/'request.json').write_bytes(self.raw)
        process = subprocess.run([os.environ['COMSPEC'], '/d', '/c', 'mklink', '/J',
                                  str(link), str(target)], capture_output=True, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.request = link/'request.json'
        self.refused(self.run_main(), 'input_invalid')
        self.request = self.folder/'request.json'
        self.output = link/'session.json'
        self.refused(self.run_main(), 'output_failed')
        self.assertFalse((target/'session.json').exists())

    def test_request_drift_before_and_after_publication_refuses(self):
        original = self.m._revalidate
        for stage in (1, 2):
            self.output = self.folder/('drift-%d.json' % stage)
            self.request.write_bytes(self.raw)
            calls = []
            def revalidate(path, snapshot):
                calls.append(path)
                if len(calls) == stage:
                    path.write_bytes(self.raw+b' ')
                return original(path, snapshot)
            with patch.object(self.m, '_revalidate', side_effect=revalidate):
                self.refused(self.run_main(), 'input_invalid')
            self.assertEqual(self.output.exists(), stage == 2)
            if stage == 2:
                self.assertEqual(self.output.read_bytes(), self.expected)

    def test_owned_request_detects_read_time_identity_change(self):
        original = Path.open
        request = self.request
        class DriftingRead(FaultFile):
            def read(inner, size):
                raw = inner.stream.read(size)
                with original(request, 'ab') as changed:
                    changed.write(b' ')
                return raw
        def opening(path, mode='r', *args, **kwargs):
            stream = original(path, mode, *args, **kwargs)
            return DriftingRead(stream, '') if path == request and mode == 'rb' else stream
        with patch.object(Path, 'open', new=opening):
            self.refused(self.run_main(), 'input_invalid')
        self.assertFalse(self.output.exists())

    def test_same_size_request_edit_with_restored_timestamp_still_refuses(self):
        original = self.m._revalidate
        before = self.request.stat()
        def revalidate(path, snapshot):
            path.write_bytes(self.raw.replace(b'"hand_count":3', b'"hand_count":1'))
            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
            return original(path, snapshot)
        with patch.object(self.m, '_revalidate', side_effect=revalidate):
            self.refused(self.run_main(), 'input_invalid')
        self.assertFalse(self.output.exists())

    def test_real_short_write_flush_close_and_read_failures_retain_output(self):
        original = Path.open
        for fault in ('short', 'flush', 'close', 'read'):
            self.output = self.folder/(fault+'.json')
            def opening(path, mode='r', *args, **kwargs):
                stream = original(path, mode, *args, **kwargs)
                controlled = mode == ('rb' if fault == 'read' else 'xb')
                return FaultFile(stream, fault) if path == self.output and controlled else stream
            with patch.object(Path, 'open', new=opening):
                self.refused(self.run_main(), 'output_failed')
            self.assertEqual(self.output.read_bytes(),
                             self.expected[:7] if fault == 'short' else self.expected)

    def test_real_fsync_failure_and_output_readback_drift_retain_created_file(self):
        original_sync = os.fsync
        def fsync(fd):
            original_sync(fd)
            raise OSError('controlled fsync completion failure')
        with patch.object(self.m.os, 'fsync', side_effect=fsync):
            self.refused(self.run_main(), 'output_failed')
        self.assertEqual(self.output.read_bytes(), self.expected)
        self.output = self.folder/'readback-drift.json'
        original_read = self.m._read
        def read(path, limit, code):
            if path == self.output:
                path.write_bytes(b'changed')
            return original_read(path, limit, code)
        with patch.object(self.m, '_read', side_effect=read):
            self.refused(self.run_main(), 'output_failed')
        self.assertEqual(self.output.read_bytes(), b'changed')

    def test_stdout_short_write_is_not_retried_and_complete_file_survives(self):
        result = self.run_main(short_stdout=True)
        self.assertEqual(result[0], 1)
        self.assertEqual(len(result[1]), 7)
        self.assertEqual(result[2], b'REFUSED output_failed\n')
        self.assertEqual([fd for fd, _ in result[3]], [1, 2])
        self.assertEqual(self.output.read_bytes(), self.expected)

    def test_interrupt_generation_limit_internal_and_reporting_failures(self):
        for error, status, line in ((KeyboardInterrupt(), 130, b'REFUSED interrupted\n'),
                                    (RuntimeError(), 1, b'REFUSED internal_error\n'),
                                    (self.m.Refusal('generation_limit'), 1,
                                     b'REFUSED generation_limit\n')):
            with patch.object(self.m, 'generate_session', side_effect=error):
                result = self.run_main()
            self.assertEqual((result[0], result[1], result[2]), (status, b'', line))
            self.assertFalse(self.output.exists())
        writes = []
        def failed_write(fd, raw):
            writes.append(fd)
            raise OSError('closed diagnostic sink')
        self.request.write_bytes(b'{}')
        with patch.object(self.m.os, 'write', side_effect=failed_write):
            self.assertEqual(self.m.main(self.arguments()), 1)
        self.assertEqual(writes, [2])

    def test_interrupt_during_argument_parsing_is_reported(self):
        with patch.object(self.m.argparse.ArgumentParser, 'parse_args',
                          side_effect=KeyboardInterrupt()):
            try:
                result = self.run_main()
            except KeyboardInterrupt:
                self.fail('argument parsing bypassed the CLI interruption handler')
        self.assertEqual((result[0], result[1], result[2]), (130, b'', b'REFUSED interrupted\n'))
        self.assertFalse(self.output.exists())

    def test_generated_size_bound_and_unsupported_environment_refuse(self):
        with patch.object(self.m, 'generate_session', return_value={'oversized': 'x'*16384}):
            self.refused(self.run_main(), 'generation_limit')
        with patch.object(self.m.sys.implementation, 'name', 'pypy'):
            self.refused(self.run_main(), 'environment_invalid')
        self.assertFalse(self.output.exists())

    def test_interrupt_after_real_write_keeps_the_partial_file(self):
        original = Path.open
        class InterruptedWrite(FaultFile):
            def write(inner, raw):
                inner.stream.write(raw[:9])
                raise KeyboardInterrupt()
        def opening(path, mode='r', *args, **kwargs):
            stream = original(path, mode, *args, **kwargs)
            return InterruptedWrite(stream, '') if mode == 'xb' else stream
        with patch.object(Path, 'open', new=opening):
            result = self.run_main()
        self.assertEqual((result[0], result[1], result[2]), (130, b'', b'REFUSED interrupted\n'))
        self.assertEqual(self.output.read_bytes(), self.expected[:9])

    def test_cli_help_syntax_environment_and_minimum_integer_limit(self):
        for flags, args, code in ((['-B', '-P'], ['--help'], 0),
                                  (['-B', '-P'], [], 2),
                                  (['-B', '-P'], ['--req', str(self.request)], 2),
                                  (['-B'], self.arguments(), 1),
                                  (['-P'], self.arguments(), 1)):
            env = {k: v for k, v in os.environ.items() if not k.startswith('PYTHON')}
            p = subprocess.run([sys.executable, *flags, str(helpers.TOOL), *args],
                               cwd=helpers.ROOT, env=env, capture_output=True, timeout=20)
            self.assertEqual(p.returncode, code, p.stderr)
            if code == 1:
                self.assertEqual(p.stderr, b'REFUSED environment_invalid\n')
            self.assertFalse(self.output.exists())
        p = subprocess.run([sys.executable, '-B', '-P', '-X', 'int_max_str_digits=640',
                            str(helpers.TOOL), *self.arguments()], capture_output=True,
                           cwd=helpers.ROOT, env=os.environ.copy(), timeout=20)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.output.read_bytes(), self.expected)

    def test_import_and_pure_calls_have_no_explicit_io_process_or_environment_effect(self):
        before = dict(os.environ)
        with (patch('builtins.open', side_effect=AssertionError('file I/O')),
              patch.object(Path, 'open', side_effect=AssertionError('path I/O'))):
            module = helpers.load_tool()
            self.assertEqual(helpers.encoded(module.generate_session(helpers.SEED, 3)),
                             self.expected)
        self.assertEqual(dict(os.environ), before)

    def test_cli_outputs_admit_real_schedule_and_card_contract_for_each_count(self):
        for count in (1, 3, 16):
            self.output = self.folder/('admit-%d.json' % count)
            request = json.loads(self.raw)
            request['hand_count'] = count
            self.request.write_bytes(helpers.encoded(request))
            self.assertEqual(self.run_main()[0], 0)
            result = helpers.admit(self.output.read_bytes())
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(result.stdout)), count)


if __name__ == '__main__':
    unittest.main()
