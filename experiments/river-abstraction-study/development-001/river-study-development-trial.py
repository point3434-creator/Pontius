"""Bounded local development trial over the four predeclared cases."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
OUT = Path('D:/Pontius/tmp/river-study-development-20260910-01')
PYTHON = ROOT / '.venv/Scripts/python.exe'
identity_path = Path('D:/Pontius/tmp/river-study-review-01/identity.json')
identity = json.loads(identity_path.read_text(encoding='utf-8-sig'))
for name, digest in identity['sha256'].items():
    assert sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
assert sys.version_info[:3] == (3, 14, 6)
OUT.mkdir(exist_ok=False)


def save(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


cases = [(board, regime) for board in (0, 1) for regime in ('uniform', 'polarized')]
save('plan.json', {
    'kind': 'local development trial, not formal retained campaign or holdout',
    'user_request': "Let's try it",
    'review_report_sha256': 'e293a723539fb01e8fb87a894c0019fd694d32f49e9f03e79f17590f0445f831',
    'reviewed_identity': identity, 'hands_per_player': 96, 'iterations': 10000,
    'case_timeout_seconds': 60, 'maximum_cases': 4, 'sequential': True,
    'memory_scope': 'No measured RSS cap; fixed 96x96 payoff matrix and 96 maximum groups.',
    'cases': [{'board': b, 'regime': r} for b, r in cases],
    'script_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
})
environment = os.environ.copy()
environment['PYTHONDONTWRITEBYTECODE'] = '1'
environment.pop('PYTHONTRACEMALLOC', None)
for variable in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    environment[variable] = '1'
receipts = []
for board, regime in cases:
    label = f'd{board}-{regime}'
    command = [str(PYTHON), '-B', str(ROOT / 'tools/river_abstraction_study.py'),
               '--output', str(OUT / label), '--board', str(board),
               '--regime', regime, '--hands', '96', '--iterations', '10000']
    started = perf_counter()
    try:
        child = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=60)
    except subprocess.TimeoutExpired as error:
        save(f'{label}-failure.json', {'complete': False, 'reason': '60 second timeout',
                                     'command': command})
        (OUT / f'{label}-stdout.txt').write_bytes(error.stdout or b'')
        (OUT / f'{label}-stderr.txt').write_bytes(error.stderr or b'')
        raise
    (OUT / f'{label}-stdout.txt').write_bytes(child.stdout)
    (OUT / f'{label}-stderr.txt').write_bytes(child.stderr)
    receipt = {'case': label, 'exit': child.returncode, 'wall_seconds': perf_counter() - started}
    receipts.append(receipt)
    save(f'{label}-receipt.json', receipt)
    print(json.dumps(receipt), flush=True)
    if child.returncode:
        save('failed.json', {'complete': False, 'receipts': receipts})
        raise SystemExit(child.returncode)
save('execution.json', {'all_children_exit_zero': True, 'receipts': receipts,
                         'analysis_complete': False})
