"""Record this controller approval and execute the frozen development plan once."""
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
PACKET = ROOT/'docs/research/river-witness-groups-r001'
PLAN = PACKET/'plan.json'
DIGEST = '9581a2a8e8d74d9d66e31abed59a61cff7625b769be4521a303b0c343f0ed855'
EVIDENCE = PACKET/'invocation-001'
def digest(path):
    return sha256(path.read_bytes()).hexdigest()
def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True)+'\n')

assert digest(PLAN) == DIGEST
identity = json.loads((PACKET/'identity.json').read_bytes())
for name,h in identity['sha256'].items():
    assert digest(ROOT/name) == h, name
for name,h in json.loads((PACKET/'delivery-manifest.json').read_bytes()).items():
    assert digest(PACKET/name) == h, name
spec = importlib.util.spec_from_file_location('bound_screen', ROOT/'tools/river_witness_groups.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
_, plan = tool.read_plan(PLAN, DIGEST)
assert not Path(plan['output_directory']).exists(), 'output already exists'
git = ['C:/Program Files/Git/cmd/git.exe','-c',f'safe.directory={ROOT}','-C',str(ROOT)]
assert subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip() == identity['base_commit']
assert subprocess.check_output(git+['branch','--show-current'],text=True).strip() == identity['branch']
EVIDENCE.mkdir(exist_ok=False)
write(EVIDENCE/'authorization.json', dict(user_words_verbatim='I approve',
    context='Reply to the explicit request for one execution of the reviewed bound development plan.',
    plan_path=str(PLAN), plan_sha256=DIGEST,
    scope='One development invocation only; no retry, commit, push or later experiment.',
    recorded_at_utc=datetime.now(timezone.utc).isoformat()))
command = [sys.executable,'-B',str(ROOT/'tools/river_witness_groups.py'),
           'run','--plan',str(PLAN),'--sha256',DIGEST]
write(EVIDENCE/'launch.json', dict(command=command, cwd=str(ROOT), preflight_verified=True,
    delivery_manifest_sha256=digest(PACKET/'delivery-manifest.json'),
    recorded_at_utc=datetime.now(timezone.utc).isoformat()))
environment = os.environ.copy()
environment['PYTHONDONTWRITEBYTECODE'] = '1'
environment.pop('PYTHONTRACEMALLOC', None)
started = perf_counter()
with (EVIDENCE/'stdout.txt').open('xb') as stdout, (EVIDENCE/'stderr.txt').open('xb') as stderr:
    child = subprocess.run(command,cwd=ROOT,env=environment,stdout=stdout,stderr=stderr)
write(EVIDENCE/'receipt.json', dict(exit=child.returncode, seconds=perf_counter()-started,
    ended_at_utc=datetime.now(timezone.utc).isoformat(), plan_sha256=DIGEST,
    output_directory=plan['output_directory']))
print((EVIDENCE/'receipt.json').read_text())
print((EVIDENCE/'stdout.txt').read_text())
print((EVIDENCE/'stderr.txt').read_text())
sys.exit(child.returncode)
