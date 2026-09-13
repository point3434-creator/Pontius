"""Seal this milestone, preserve prior evidence, and update current summaries."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import shutil
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY=ROOT/'experiments/river-abstraction-study'
TARGET=HISTORY/HERE.name
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,indent=2,sort_keys=True)
        f.write('\n')
assert read(HERE/'assessment.json')['complete'] and not TARGET.exists()
prior={str(p):sha(p) for p in sorted(HISTORY.glob('*/milestone-manifest.json'))}
count=0
for raw in prior:
    p=Path(raw)
    for name,h in read(p).items():
        assert sha(p.parent/name)==h,(raw,name)
        count+=1
write(HERE/'preservation.json',dict(prior_manifests=prior,verified_members=count))
deps=HERE/'dependencies'
deps.mkdir()
mapping={}
for raw,h in read(HERE/'plan.json')['pins'].items():
    p=Path(raw)
    assert sha(p)==h,raw
    if p.is_relative_to(HERE): continue
    if p.suffix=='.dll':
        mapping[raw]=dict(sha256=h,external_runtime_not_redistributed=True)
        continue
    dst=deps/(h+p.suffix)
    if not dst.exists(): shutil.copyfile(p,dst)
    mapping[raw]=dict(sha256=h,retained=dst.relative_to(HERE).as_posix())
write(deps/'index.json',mapping)
shutil.copytree(HERE,TARGET)
manifest={p.relative_to(TARGET).as_posix():sha(p) for p in sorted(TARGET.rglob('*')) if p.is_file()}
write(TARGET/'milestone-manifest.json',manifest)
report=ROOT/'docs/research/river-gpu-graph-001.md'
assert not report.exists()
report.write_bytes((HERE/'report.md').read_bytes())
def replace(p,before,after):
    data=p.read_text(encoding='utf-8')
    assert data.count(before)==1,(p,before)
    p.write_text(data.replace(before,after),encoding='utf-8',newline='\n')
a=read(HERE/'assessment.json')
c=a['comparisons']
brief=('The [graph replay test](../docs/research/river-gpu-graph-001.md) completed\n'
       '36 solves across 18 fresh workers and six independent rational audits.\n'
       f"Replay accelerated the fixed solve {c[0]['graph_vs_eager']:.2f}x / "
       f"{c[1]['graph_vs_eager']:.2f}x versus eager GPU execution,\n"
       'with bitwise-identical final policies across all arms, repeats and resets.\n'
       'Preparation and audit costs reduce the gain but do not erase it.\n'
       'Next proposed: convert the saved compute time into measured strategy quality.\n')
replace(ROOT/'experiments/RESULTS.md',
    'now links 43 retained river milestones through river-gpu-execution-001.',
    'now links 44 retained river milestones through river-gpu-graph-001.\n\n'+brief)
replace(ROOT/'experiments/solver-foundations.md','## GPU execution: river-gpu-execution-001',
    '## Graph replay: river-gpu-graph-001\n\n'+brief+'\n## GPU execution: river-gpu-execution-001')
replace(ROOT/'experiments/solver-foundations.md',
    'Next proposed test: bounded static graph replay, charging setup and audit.',
    'The subsequent graph replay result is recorded above, with setup and audit charged.')
replace(ROOT/'experiments/gpu-representation.md','## Latest fixed-game execution test',
    '## Latest graph replay test\n\n'+brief+'\n## Earlier fixed-game execution test')
replace(ROOT/'docs/research/README.md','The latest milestone is **river-gpu-execution-001**.',
    'The latest milestone is **river-gpu-graph-001**. The '
    '[graph replay result](river-gpu-graph-001.md)\n'
    'retains all 36 solves, six independent audits, exact policy-byte parity,\n'
    'capture/reset checks and full preparation/reuse accounting. No strategy adoption.\n\n'
    'The preceding milestone is **river-gpu-execution-001**.')
replace(ROOT/'docs/research/README.md','\n## Designs and frozen controls',
    '| river-gpu-graph-001 | [Result](river-gpu-graph-001.md) | '
    '[Milestone](../../experiments/river-abstraction-study/river-gpu-graph-001/) |\n\n'
    '## Designs and frozen controls')
replace(ROOT/'experiments/research-roadmap.md',
    '   net speed gains with unchanged audited error. Next proposed: a bounded\n'
    '   static graph replay comparison including setup, reset and exact-audit costs.',
    '   net speed gains with unchanged audited error. The '
    '[graph replay test](../docs/research/river-gpu-graph-001.md)\n'
    '   now establishes a larger execution gain with identical policy bytes.\n'
    '   Next proposed: measure audited quality under fixed total-time budgets.')
replace(ROOT/'experiments/research-roadmap.md',
    'Next proposed question: static graph replay versus eager execution, with\n'
    'capture/reset costs and reuse break-even measured. Stop if the net gain is small.',
    'The [graph replay comparison](../docs/research/river-gpu-graph-001.md) is complete,\n'
    'including capture, reset and independent audits. Freeze this execution result.\n'
    'Next proposed: use the saved time for more iterations and measure actual\n'
    'error under declared total-time budgets; do not assume monotone improvement.')
entry=dict(timestamp=datetime.now(timezone.utc).isoformat(),
    command='river-gpu-graph-001 frozen three-arm execution and reset comparison',
    status='complete_policy_identical',summary='36 solves, six exact audits; see graph report',
    source_commit=read(HERE/'plan.json')['source_commit'],
    output=(TARGET.relative_to(ROOT)/'milestone-manifest.json').as_posix(),
    output_sha256=sha(TARGET/'milestone-manifest.json'))
with (ROOT/'execution_journal.jsonl').open('a',encoding='utf-8',newline='\n') as f:
    f.write(json.dumps(entry,sort_keys=True)+'\n')
for name,h in manifest.items(): assert sha(TARGET/name)==h
for p,h in prior.items(): assert sha(Path(p))==h
print(json.dumps(dict(retained=str(TARGET),members=len(manifest),
    preserved_milestones=len(prior),preserved_members=count,manifest_sha256=entry['output_sha256'])))
