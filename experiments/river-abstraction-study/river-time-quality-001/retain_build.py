"""Retain a validated build without adding a completed research milestone."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
TARGET = HISTORY/HERE.name
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, value):
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')

assert not TARGET.exists() and not (HERE/'run').exists()
plan = read(HERE/'plan.json')
receipt = read(HERE/'preflight/receipt.json')
assert receipt['complete'] and not receipt['campaign_invoked']
assert receipt['plan_sha256'] == sha(HERE/'plan.json')
for p in HERE.glob('*.py'):
    ast.parse(p.read_text(encoding='utf-8'))
for case in plan['variants']:
    row = read(HERE/'preflight'/f'{case}-0.json')
    process = read(HERE/'preflight'/f'{case}-0-receipt.json')
    audit = read(HERE/'preflight'/f'{case}-0-2048-audit.json')
    ar = read(HERE/'preflight'/f'{case}-0-2048-audit-receipt.json')
    assert row['executing_pid'] == process['observed_pid'] and process['exit'] == 0
    assert audit['executing_pid'] == ar['observed_pid'] and ar['exit'] == 0
    assert row['checkpoints'][0]['policy_sha256'] == audit['policy_sha256']
prior = {str(p): sha(p) for p in HISTORY.glob('*/milestone-manifest.json')}
count = 0
for raw in prior:
    p = Path(raw)
    for name, h in read(p).items():
        assert sha(p.parent/name) == h
        count += 1
write(HERE/'preservation.json', dict(prior_manifests=prior, verified_members=count))
deps = HERE/'dependencies'
deps.mkdir()
mapping = {}
for raw, h in plan['pins'].items():
    p = Path(raw)
    assert sha(p) == h, raw
    if p.is_relative_to(HERE):
        continue
    if p.suffix == '.dll':
        mapping[raw] = dict(sha256=h, external_runtime_not_redistributed=True)
        continue
    dst = deps/(h+p.suffix)
    if not dst.exists():
        shutil.copyfile(p, dst)
    mapping[raw] = dict(sha256=h, retained=dst.relative_to(HERE).as_posix())
write(deps/'index.json', mapping)
write(HERE/'ready.json', dict(status='built_and_preflight_verified',
    campaign_invoked=False, completed_research_milestones=len(prior),
    selector_test_methods=6, anchor_solves=2, independent_audits=2,
    plan_sha256=sha(HERE/'plan.json')))
ready = '''# River time-quality experiment: ready build

The next study is built and validated; the full campaign has not run.
It asks whether additional graph-solver iterations improve exact audited error
within accounted budgets of 3, 5, 10 and 15 seconds.

The design fixes 2,048 / 4,096 / 8,192 / 16,384 iterations, both expanded river
games and three repeats. Select the latest affordable checkpoint without
consulting error. Preserve budget misses and any worsening at later checkpoints.
Preparation, observed process overhead and an independent audit are charged.
This is an accounting comparison, not a live action-clock guarantee.

Validation completed on Python 3.14.6: six selector test methods passed; two
2,048-iteration solves using the 16,384 horizon matched retained policy bytes;
two independent rational audits reproduced their previous exact errors.
These are runner-validation facts, not a new research result. The main campaign
will produce six trajectories and 24 checkpoint audits, under the bound plan.

Source and input identities, the design, validation receipts and dependency copies
are retained in the build. The native cuBLAS runtime is pinned but not redistributed.
The full campaign must start from the author directory because frozen imports and
input paths are bound there. No solver implementation was duplicated or changed.

Launch command, after the user requests the full comparison:

```powershell
& 'C:/Users/point/AppData/Local/Python/pythoncore-3.14-64/python.exe' `
  -I -S -B -W error::ResourceWarning `
  'D:/Pontius/experiments/river-time-quality-001/launch.py' campaign.py execute `
  6da2525fc78e836b6d7fd412ec08c415636ea1c21bf4074a87ea14657971bc5a run
```

Preflight results remain in preflight/; the campaign creates a new run/ directory.
No commit, push, strategy adoption or bot integration occurred.
'''
with (HERE/'ready.md').open('x', encoding='utf-8', newline='\n') as f:
    f.write(ready)
shutil.copytree(HERE, TARGET)
manifest = {p.relative_to(TARGET).as_posix(): sha(p)
            for p in sorted(TARGET.rglob('*')) if p.is_file()}
write(TARGET/'build-manifest.json', manifest)
doc = ROOT/'docs/research/river-time-quality-001-design.md'
assert not doc.exists()
doc.write_bytes((HERE/'ready.md').read_bytes())
def replace(p, before, after):
    data = p.read_text(encoding='utf-8')
    assert data.count(before) == 1, (p, before)
    p.write_text(data.replace(before, after), encoding='utf-8', newline='\n')
replace(ROOT/'docs/research/README.md', 'The latest milestone is **river-gpu-graph-001**.',
    'Prepared next: [river-time-quality-001](river-time-quality-001-design.md).\n'
    'The build and two anchor audits passed; the full time-budget campaign is not run.\n\n'
    'The latest completed milestone is **river-gpu-graph-001**.')
replace(ROOT/'experiments/research-roadmap.md',
    '   Next proposed: measure audited quality under fixed total-time budgets.',
    '   Next [study built and preflight-verified](../docs/research/river-time-quality-001-design.md):\n'
    '   measure audited quality under fixed accounted budgets. Full campaign not yet run.')
entry = dict(timestamp=datetime.now(timezone.utc).isoformat(),
    command='river-time-quality-001 build and anchor validation',
    status='ready_not_campaign_executed',
    summary='Six selector tests; two retained-policy matches; two independent audits',
    output=(TARGET.relative_to(ROOT)/'build-manifest.json').as_posix(),
    output_sha256=sha(TARGET/'build-manifest.json'))
with (ROOT/'execution_journal.jsonl').open('a', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(entry, sort_keys=True)+'\n')
for name, h in manifest.items():
    assert sha(TARGET/name) == h
for p, h in prior.items():
    assert sha(Path(p)) == h
print(json.dumps(dict(status='ready', campaign_invoked=False, build_members=len(manifest),
    preserved_milestones=len(prior), verified_prior_members=count,
    build_manifest_sha256=entry['output_sha256'])))
