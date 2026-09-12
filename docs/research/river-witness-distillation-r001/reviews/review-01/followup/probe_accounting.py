"""Retain inert-process accounting evidence; never call the research entry."""
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

SCRATCH = Path('D:/Pontius/tmp/witness-distill-review-01/followup')
MODULE = Path('D:/Pontius-worktrees/eval-runner-consolidation/docs/research/'
              'river-witness-distillation-r001/accounting/measure_invocation.py')
spec = importlib.util.spec_from_file_location('f1_accounting_probe', MODULE)
recorder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recorder)

# Public main must refuse missing authorization before starting anything.
with patch.object(recorder.subprocess, 'run', side_effect=AssertionError('no child permitted')):
    try:
        recorder.main()
    except FileNotFoundError as error:
        assert Path(error.filename).name == 'controller-authorization.json'
    else:
        raise AssertionError('missing authorization did not stop entry')

binding = {'purpose': 'inert same-reviewer F1 follow-up; not research authorization',
           'test_identity': 'late-parent-phase-v1'}
command = [sys.executable, '-B', '-W', 'error::ResourceWarning', '-c',
           "import sys,time; print('worker-finished',flush=True); time.sleep(.08); "
           "print('parent-finished',flush=True); print('captured-stderr',file=sys.stderr)"]
assert recorder.measure(command, SCRATCH / 'inert-success', binding, SCRATCH) == 0
receipt = json.loads((SCRATCH / 'inert-success/receipt.json').read_bytes())
assert receipt['whole_command_seconds'] >= .08
assert receipt['command'] == command and receipt['binding'] == binding
assert (SCRATCH / 'inert-success/stdout.txt').read_text().split() == [
    'worker-finished', 'parent-finished']
assert (SCRATCH / 'inert-success/stderr.txt').read_text().strip() == 'captured-stderr'

failure_command = [sys.executable, '-B', '-W', 'error::ResourceWarning', '-c',
                   "import sys; print('failure retained',file=sys.stderr); sys.exit(7)"]
assert recorder.measure(failure_command, SCRATCH / 'inert-exit7', binding, SCRATCH) == 7
failure_receipt = json.loads((SCRATCH / 'inert-exit7/receipt.json').read_bytes())
assert failure_receipt['exit'] == 7

try:
    recorder.measure([str(SCRATCH / 'absent-inert-executable.exe')],
                     SCRATCH / 'inert-start-failure', binding, SCRATCH)
except FileNotFoundError:
    pass
else:
    raise AssertionError('missing executable became success')
assert (SCRATCH / 'inert-start-failure/failed.json').exists()
assert not (SCRATCH / 'inert-start-failure/receipt.json').exists()

observations = dict(passed=True, research_invocations=0,
                    missing_approval_stopped_before_subprocess=True,
                    inert_success_seconds=receipt['whole_command_seconds'],
                    late_phase_seconds_minimum=.08,
                    nonzero_child_exit=failure_receipt['exit'],
                    start_failure_record_retained=True,
                    binding_and_both_captures_retained=True)
(SCRATCH / 'probe-receipt.json').write_text(json.dumps(observations, indent=2) + '\n')
print(json.dumps(observations))
