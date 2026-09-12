import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parent


class AccountingTests(unittest.TestCase):
    def module(self):
        path = ROOT/'measure_invocation.py'
        self.assertTrue(path.exists(),'bound outer timing recorder is not implemented')
        spec = importlib.util.spec_from_file_location('accounting',path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def test_retained_duration_includes_phase_after_worker_and_binds_command(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)/'receipt'
            command = [sys.executable,'-B','-c',
                "import time; time.sleep(.02); print('worker'); time.sleep(.06); print('parent')"]
            self.assertEqual(m.measure(command,output,{'test_binding':'fixed'},ROOT),0)
            receipt = json.loads((output/'receipt.json').read_bytes())
            self.assertGreaterEqual(receipt['whole_command_seconds'],.08)
            self.assertEqual(receipt['exit'],0)
            self.assertEqual(receipt['binding'],{'test_binding':'fixed'})
            self.assertEqual(receipt['command'],command)
            self.assertEqual((output/'stdout.txt').read_text().split(),['worker','parent'])
            with self.assertRaises(FileExistsError):
                m.measure(command,output,{},ROOT)

    def test_child_failure_and_evidence_write_error_do_not_become_success(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            command = [sys.executable,'-B','-c','raise SystemExit(7)']
            self.assertEqual(m.measure(command,root/'failed',{},ROOT),7)
            self.assertEqual(json.loads((root/'failed/receipt.json').read_bytes())['exit'],7)
            original = m.write
            def fail_receipt(path,value):
                if path.name == 'receipt.json':
                    raise OSError('cannot retain elapsed time')
                original(path,value)
            with patch.object(m,'write',side_effect=fail_receipt):
                with self.assertRaises(OSError):
                    m.measure([sys.executable,'-B','-c','pass'],root/'write-failed',{},ROOT)
            self.assertTrue((root/'write-failed/failed.json').exists())

    def test_approval_must_bind_plan_and_recorder(self):
        m = self.module()
        valid = {'user_words_verbatim':'I approve','plan_sha256':'p','recorder_sha256':'r'}
        m.validate_approval(valid,'p','r')
        for key,value in [('user_words_verbatim',''),('plan_sha256','x'),('recorder_sha256','x')]:
            with self.assertRaises(ValueError):
                m.validate_approval(dict(valid,**{key:value}),'p','r')
