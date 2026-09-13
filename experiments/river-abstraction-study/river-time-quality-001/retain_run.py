"""Append completed evidence while preserving the sealed build and prior milestones."""
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
assessment=read(HERE/'assessment.json')
assert assessment['complete'] and not (TARGET/'milestone-manifest.json').exists()
build=read(TARGET/'build-manifest.json')
for name,h in build.items(): assert sha(TARGET/name)==h,name
prior={str(p):sha(p) for p in HISTORY.glob('*/milestone-manifest.json')}
count=0
for raw in prior:
    p=Path(raw)
    for name,h in read(p).items():
        assert sha(p.parent/name)==h,(raw,name)
        count+=1
write(HERE/'completion-preservation.json',dict(prior_manifests=prior,
    verified_prior_members=count,build_manifest_sha256=sha(TARGET/'build-manifest.json'),
    preserved_build_members=len(build)))
write(HERE/'completion.json',dict(status='complete',campaign_invoked=True,
    authorization="Let's launch it",plan_sha256=sha(HERE/'plan.json'),
    trajectories=6,audits=24,regressions=assessment['regressions'],
    strict_passes=assessment['strict_passes']))
for p in sorted(HERE.rglob('*')):
    if not p.is_file(): continue
    dst=TARGET/p.relative_to(HERE)
    if dst.exists():
        assert sha(dst)==sha(p),str(dst)
    else:
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dst)
manifest={p.relative_to(TARGET).as_posix():sha(p) for p in sorted(TARGET.rglob('*')) if p.is_file()}
write(TARGET/'milestone-manifest.json',manifest)
doc=ROOT/'docs/research/river-time-quality-001.md'
assert not doc.exists()
doc.write_bytes((HERE/'report.md').read_bytes())
def replace(p,before,after):
    data=p.read_text(encoding='utf-8')
    assert data.count(before)==1,(p,before)
    p.write_text(data.replace(before,after),encoding='utf-8',newline='\n')
brief=('The [time-budget quality campaign](../docs/research/river-time-quality-001.md)\n'
       'completed six trajectories and 24 exact audits. All tested iteration increases\n'
       'reduced error; repeat policies were identical. Under the declared accounting,\n'
       '10 seconds fits 19.06x lower checkback error, and 15 seconds fits 9.58x lower\n'
       'raise-tree error, relative to 2,048 iterations. Tight-budget misses remain\n'
       'visible; no strict equilibrium threshold passed. Fresh-board transfer is next.\n')
replace(ROOT/'experiments/RESULTS.md',
    'now links 44 retained river milestones through river-gpu-graph-001.',
    'now links 45 retained river milestones through river-time-quality-001.\n\n'+brief)
replace(ROOT/'experiments/RESULTS.md',
    'Next proposed: convert the saved compute time into measured strategy quality.',
    'The subsequent time-budget campaign above measures that quality improvement.')
replace(ROOT/'experiments/solver-foundations.md','## Graph replay: river-gpu-graph-001',
    '## Time-budget quality: river-time-quality-001\n\n'+brief+'\n## Graph replay: river-gpu-graph-001')
replace(ROOT/'experiments/solver-foundations.md',
    'Next proposed: convert the saved compute time into measured strategy quality.',
    'The subsequent time-budget campaign above measures that quality improvement.')
replace(ROOT/'experiments/gpu-representation.md','## Latest graph replay test',
    '## Latest quality consequence\n\n'+brief+'\n## Earlier graph replay test')
replace(ROOT/'experiments/gpu-representation.md',
    'Next proposed: convert the saved compute time into measured strategy quality.',
    'The subsequent time-budget campaign above measures that quality improvement.')
replace(ROOT/'docs/research/README.md',
    'Prepared next: [river-time-quality-001](river-time-quality-001-design.md).\n'
    'The build and two anchor audits passed; the full time-budget campaign is not run.\n\n'
    'The latest completed milestone is **river-gpu-graph-001**.',
    'The latest completed milestone is **river-time-quality-001**. The '
    '[result](river-time-quality-001.md)\n'
    'records six trajectories, 24 audits, every budget miss, and the quality gained\n'
    'from additional iterations. The [earlier build snapshot](river-time-quality-001-design.md)\n'
    'remains available; the full campaign is now complete.\n\n'
    'The preceding milestone is **river-gpu-graph-001**.')
replace(ROOT/'docs/research/README.md','\n## Designs and frozen controls',
    '| river-time-quality-001 | [Result](river-time-quality-001.md) | '
    '[Milestone](../../experiments/river-abstraction-study/river-time-quality-001/) |\n\n'
    '## Designs and frozen controls')
replace(ROOT/'docs/research/river-time-quality-001-design.md',
    '# River time-quality experiment: ready build',
    '# River time-quality experiment: historical ready build\n\n'
    'The campaign has since completed. See the [result](river-time-quality-001.md).\n'
    'The original build-state account follows; its sealed copy is preserved in the milestone.')
replace(ROOT/'experiments/research-roadmap.md',
    '   Next [study built and preflight-verified](../docs/research/river-time-quality-001-design.md):\n'
    '   measure audited quality under fixed accounted budgets. Full campaign not yet run.',
    '   The [time-budget quality study](../docs/research/river-time-quality-001.md) is complete:\n'
    '   added iterations improved audited error within useful accounted budgets.\n'
    '   Next proposed: fixed-settings transfer to a fresh board/range configuration.')
replace(ROOT/'experiments/research-roadmap.md',
    'Next proposed: use the saved time for more iterations and measure actual\n'
    'error under declared total-time budgets; do not assume monotone improvement.',
    'The [time-budget campaign](../docs/research/river-time-quality-001.md) is complete.\n'
    'Freeze its solver settings and cost definition. Next proposed: fresh-board/range\n'
    'transfer; the two present nested trees share one board and do not establish it.')
entry=dict(timestamp=datetime.now(timezone.utc).isoformat(),
    command='river-time-quality-001 authorized frozen campaign',status='complete_approximate_quality_gain',
    summary='Six trajectories and 24 exact audits; cost-qualified quality gains with budget misses retained',
    source_commit='6518b9d3af252c93f8a9dbdb13fb28adc2859b4c',
    output=(TARGET.relative_to(ROOT)/'milestone-manifest.json').as_posix(),
    output_sha256=sha(TARGET/'milestone-manifest.json'))
with (ROOT/'execution_journal.jsonl').open('a',encoding='utf-8',newline='\n') as f:
    f.write(json.dumps(entry,sort_keys=True)+'\n')
for name,h in manifest.items(): assert sha(TARGET/name)==h,name
for name,h in build.items(): assert sha(TARGET/name)==h,name
for p,h in prior.items(): assert sha(Path(p))==h,p
print(json.dumps(dict(members=len(manifest),prior_milestones=len(prior),
    preserved_build_members=len(build),prior_members=count,manifest_sha256=entry['output_sha256'])))
