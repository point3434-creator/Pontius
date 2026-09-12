"""Record controller authority and invoke the already reviewed command once."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
PACKET = ROOT / 'docs/research/river-group-optimality-r001'
PLAN = PACKET / 'plan.json'
DIGEST = 'de07461ea9364a4fb40d0bce72a506549bc30ac609761bb0bc57ff4600c3b11c'
EVIDENCE = PACKET / 'invocation-001'

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + '\n')

assert digest(PLAN) == DIGEST
plan = json.loads(PLAN.read_bytes())
identity = json.loads((PACKET / 'identity.json').read_bytes())
for name, expected in identity['sha256'].items():
    assert digest(ROOT / name) == expected, name
delivery = json.loads((PACKET / 'delivery-manifest.json').read_bytes())
for name, expected in delivery.items():
    assert digest(PACKET / name) == expected, name
for name, expected in plan['sources'].items():
    assert digest(ROOT / name) == expected, name
for case in plan['cases']:
    for name, expected in case['files'].items():
        assert digest(Path(case['directory']) / name) == expected, (case['id'], name)
assert not Path(plan['output_directory']).exists(), 'output already exists'
assert sys.executable == plan['executable'], (sys.executable, plan['executable'])
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={ROOT}', '-C', str(ROOT)]
assert subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip() == identity['base_commit']
assert subprocess.check_output(git + ['branch', '--show-current'], text=True).strip() == identity['branch']
EVIDENCE.mkdir(exist_ok=False)
write(EVIDENCE / 'authorization.json', {
    'user_words_verbatim': 'I approve',
    'context': 'Reply to explicit request for one execution of the reviewed fixed-group diagnostic plan.',
    'plan_path': str(PLAN), 'plan_sha256': DIGEST,
    'scope': 'One bound diagnostic invocation only; no retry, commit, push or later experiment.',
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
})
command = [sys.executable, '-B', str(ROOT / 'tools/river_group_optimality.py'),
           'run', '--plan', str(PLAN), '--sha256', DIGEST]
write(EVIDENCE / 'launch.json', {'command': command, 'cwd': str(ROOT),
    'delivery_manifest_sha256': digest(PACKET / 'delivery-manifest.json'),
    'preflight_verified': True, 'recorded_at_utc': datetime.now(timezone.utc).isoformat()})
environment = os.environ.copy()
environment['PYTHONDONTWRITEBYTECODE'] = '1'
environment.pop('PYTHONTRACEMALLOC', None)
started = perf_counter()
with (EVIDENCE / 'stdout.txt').open('xb') as stdout, (EVIDENCE / 'stderr.txt').open('xb') as stderr:
    child = subprocess.run(command, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr)
write(EVIDENCE / 'receipt.json', {'exit': child.returncode, 'seconds': perf_counter()-started,
    'ended_at_utc': datetime.now(timezone.utc).isoformat(), 'plan_sha256': DIGEST,
    'output_directory': plan['output_directory']})
print((EVIDENCE / 'receipt.json').read_text())
print((EVIDENCE / 'stdout.txt').read_text())
print((EVIDENCE / 'stderr.txt').read_text())
sys.exit(child.returncode)
