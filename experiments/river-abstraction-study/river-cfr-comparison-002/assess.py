"""Post-run assessment; no solver invocation or parameter selection."""
from pathlib import Path
from fractions import Fraction
from statistics import median
import hashlib
import json
import subprocess
import sys
import csv

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, obj):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n')


plan = read(HERE/'plan.json')
receipt = read(HERE/'run/receipt.json')
assert receipt['complete'] and receipt['workers'] == 18 and receipt['certificates'] == 6
assert receipt['plan_sha256'] == digest(HERE/'plan.json')
for path, expected in plan['pins'].items():
    assert digest(Path(path)) == expected, path
cmd = [sys.executable, '-I', '-S', '-B', '-W', 'error::ResourceWarning',
       str(HERE/'launch.py'), 'test_solver.py']
test = subprocess.run(cmd, capture_output=True, timeout=30)
(HERE/'tests-stdout.txt').write_bytes(test.stdout)
(HERE/'tests-stderr.txt').write_bytes(test.stderr)
assert test.returncode == 0
rows, curves = [], []
for arm in plan['arms']:
    name = arm['name']
    reps = [read(HERE/'run'/f'{r}-{name}.json') for r in range(3)]
    cert = read(HERE/'run'/f'0-{name}-certificate.json')
    assert cert['float_agreement'] and cert['retained_reference_overlap']
    assert len({r['policy_sha256'] for r in reps}) == 1
    exact = float(Fraction(cert['certificate']['gap'])/2)
    times = [r['checkpoints'][-1]['training_seconds'] for r in reps]
    process = [read(HERE/'run'/f'{r}-{name}-receipt.json') for r in range(3)]
    rows.append(dict(name=name, exploitability=exact, fraction_of_pot=exact/10,
                training_median=median(times), training_min=min(times), training_max=max(times),
                worker_wall_median=median(p['seconds'] for p in process),
                worker_peak_mib=max(p['os_peak_commit_bytes'] for p in process)/1024**2,
                certificate_seconds=cert['certificate_seconds'],
                certificate_peak_mib=read(HERE/'run'/f'0-{name}-verify-receipt.json')[
                    'os_peak_commit_bytes']/1024**2,
                strict_gap_pass=cert['certificate']['strict_pass']))
    for c in reps[0]['checkpoints']:
        curves.append(dict(arm=name, **c))
with (HERE/'curves.csv').open('x', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(curves[0]))
    writer.writeheader()
    writer.writerows(curves)
assessment = dict(complete=True, rows=rows, tests_exit=test.returncode,
                 matched_dcfr_improvement=rows[0]['exploitability']/rows[1]['exploitability'],
                 matched_prediction_error_ratio=rows[2]['exploitability']/rows[1]['exploitability'],
                 code_vs_linear_improvement=rows[3]['exploitability']/rows[4]['exploitability'],
                 source_pins_verified=len(plan['pins']),
                 decision='Report confirmation; expanded-tree capacity next; no adoption')
write(HERE/'assessment.json', assessment)
