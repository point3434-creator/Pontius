"""Fixed historical tests execute real native children; no old test is retargeted."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path.cwd()
TOOL = ROOT/'tools/run_evaluation_history.py'
BASE = '363c9fb669e19a30375537ee5e92ea338a840a2d'
TREE = '10cc82ff78a84ef901242b2f69540f6a74ec498b'


def load():
    spec = importlib.util.spec_from_file_location('history_control', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvaluationHistoryTests(unittest.TestCase):
    def setUp(self):
        self.h = load()
        self.root = Path(tempfile.mkdtemp(prefix='evaluation-history-'))

    def test_real_all_suites_bind_exact_history_and_preserve_current_source(self):
        process = subprocess.run([sys.executable, '-B', '-P', str(TOOL),
            '--source-root', str(ROOT), '--run-root', str(self.root/'positive'),
            '--suite', 'all'], cwd=ROOT, env=os.environ.copy(), capture_output=True, timeout=1200)
        self.assertEqual(process.returncode, 0, (process.stdout, process.stderr))
        report = json.loads(process.stdout)
        self.assertEqual(report['commit'], BASE)
        self.assertEqual(report['tree'], TREE)
        self.assertTrue(report['complete'])
        self.assertEqual([row['suite'] for row in report['results']], ['runner', 'boundary', 'v2'])
        self.assertEqual([row['tests'] for row in report['results']], [28, 19, 8])
        self.assertTrue(all(row['passed'] and row['skips'] == 0 for row in report['results']))
        self.assertEqual(json.loads((self.root/'positive'/'summary.json').read_bytes()), report)
        for row in report['results']:
            self.assertEqual(row['argv'][:3], [sys.executable, '-B', '-P'])
            self.assertTrue(Path(row['cwd']).is_relative_to(self.root/'positive'))
            self.assertEqual(row['exit_code'], 0)
            self.assertTrue(Path(row['stderr']).read_bytes().strip().endswith(b'OK'))
        snapshot = self.root/'positive'/'snapshot'
        self.assertFalse((snapshot/'src/pontius/blueprint_preparation').exists())
        self.assertEqual(self.h.checked_history(snapshot, self.h.environment(snapshot,
            self.root/'positive'/'temp')), TREE)

    def test_existing_root_wrong_identity_and_non_native_git_refuse(self):
        for name, value in (('BASE_COMMIT', '0'*40), ('BASE_TREE', '0'*40)):
            with self.subTest(name=name), patch.object(self.h, name, value):
                with self.assertRaises(self.h.HistoryRefusal):
                    self.h.run_history(ROOT, self.root/name, 'v2')
        existing = self.root/'existing'
        existing.mkdir()
        marker = existing/'keep'
        marker.write_bytes(b'unchanged')
        with self.assertRaises(self.h.HistoryRefusal):
            self.h.run_history(ROOT, existing, 'v2')
        self.assertEqual(marker.read_bytes(), b'unchanged')
        bad_git = self.root/'git.cmd'
        bad_git.write_bytes(b'@exit /b 0\r\n')
        with patch.dict(os.environ, {'PONTIUS_GIT': str(bad_git)}):
            with self.assertRaises(self.h.HistoryRefusal):
                self.h.run_history(ROOT, self.root/'bad-git', 'v2')

    def test_bad_suite_and_extra_ref_argument_never_create_a_run(self):
        for extra in (['--suite', 'other'], ['--suite', 'v2', '--ref', BASE], ['--sui', 'v2']):
            process = subprocess.run([sys.executable, '-B', '-P', str(TOOL),
                '--source-root', str(ROOT), '--run-root', str(self.root/'rejected'), *extra],
                cwd=ROOT, env=os.environ.copy(), capture_output=True, timeout=30)
            self.assertEqual(process.returncode, 2)
            self.assertFalse((self.root/'rejected').exists())

    def test_actual_nonzero_child_is_retained_and_cannot_pass(self):
        original = self.h.launch_suite
        def fail_one(source, target, suite, env):
            # Controlled exit seam: alter the disposable selected script only during its
            # real launch. The production launcher still observes native exit/output.
            if suite == 'boundary':
                return original(source, target, suite, env)
            path = source/self.h.SUITES[suite][0]
            raw = path.read_bytes()
            if suite == 'runner':
                path.write_bytes(b'raise SystemExit(7)\n'+raw)
            else:
                marker = b'    def test_'
                self.assertIn(marker, raw)
                path.write_bytes(raw.replace(marker,
                    b"    @unittest.skip('controlled historical skip')\n"+marker, 1))
            try:
                return original(source, target, suite, env)
            finally:
                path.write_bytes(raw)
        with patch.object(self.h, 'launch_suite', fail_one):
            report = self.h.run_history(ROOT, self.root/'nonzero', 'all')
        self.assertFalse(report['complete'])
        self.assertEqual(report['results'][0]['exit_code'], 7)
        self.assertFalse(report['results'][0]['passed'])
        self.assertEqual(report['results'][0]['tests'], 0)
        self.assertEqual([row['suite'] for row in report['results']], ['runner', 'boundary', 'v2'])
        self.assertTrue(report['results'][1]['passed'])
        self.assertEqual(report['results'][1]['tests'], 19)
        self.assertEqual(report['results'][2]['exit_code'], 0)
        self.assertEqual(report['results'][2]['tests'], 8)
        self.assertEqual(report['results'][2]['skips'], 1)
        self.assertFalse(report['results'][2]['passed'])

    def test_result_contract_refuses_empty_short_skipped_and_nonzero(self):
        # Format validation is separate from the real-native launch controls above.
        success = b'........\nRan 8 tests in 0.123s\n\nOK\n'
        self.assertEqual(self.h.test_outcome(0, success, 8), (8, 0, True))
        failed = success.replace(b'OK\n', b'FAILED (failures=1, skipped=2)\n')
        self.assertEqual(self.h.test_outcome(1, failed, 8), (8, 2, False))
        for code, raw in ((1, success), (0, b''), (0, success.replace(b'8 tests', b'7 tests')),
                          (0, success.replace(b'OK\n', b'OK (skipped=1)\n')),
                          (0, success+b'late failure\n')):
            with self.subTest(code=code, raw=raw):
                self.assertFalse(self.h.test_outcome(code, raw, 8)[2])

    def test_full_checkout_binding_refuses_changed_and_missing_tracked_bytes(self):
        # A fresh raw clone is verified by production, then material tracked mutations
        # are refused. Whole-tree comparison must reach files outside the three suites.
        target = self.root/'source'
        env = self.h.environment(target, self.root)
        self.h.clone_history(ROOT, target, env)
        path = target/'tools/check_stabilization_boundaries.py'
        raw = path.read_bytes()
        path.write_bytes(raw+b'\n# controlled byte drift\n')
        with self.assertRaises(self.h.HistoryRefusal):
            self.h.checked_history(target, env)
        path.write_bytes(raw)
        path.unlink()
        with self.assertRaises(self.h.HistoryRefusal):
            self.h.checked_history(target, env)
        path.write_bytes(raw)
        extra = target/'src/pontius/unexpected.py'
        extra.write_bytes(b'')
        with self.assertRaises(self.h.HistoryRefusal):
            self.h.checked_history(target, env)


if __name__ == '__main__':
    unittest.main()
