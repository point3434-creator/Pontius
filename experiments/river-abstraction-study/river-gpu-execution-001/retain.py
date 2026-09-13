"""Preserve this exploratory result and narrowly update the current research index."""
from pathlib import Path
from datetime import datetime, timezone
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

assert read(HERE/'assessment.json')['exploratory_continuation_pass']
assert not TARGET.exists()
prior={str(p):sha(p) for p in sorted(HISTORY.glob('*/milestone-manifest.json'))}
count=0
for raw in prior:
    p=Path(raw)
    for name,expected in read(p).items():
        assert sha(p.parent/name)==expected,(raw,name)
        count+=1
write(HERE/'preservation.json',dict(prior_milestones=len(prior),verified_members=count,
                                   prior_manifests=prior))
deps=HERE/'dependencies'
deps.mkdir()
mapping={}
for name,expected in read(HERE/'plan.json')['pins'].items():
    p=Path(name)
    assert sha(p)==expected,name
    if p.is_relative_to(HERE): continue
    dst=deps/(expected+p.suffix)
    if not dst.exists(): shutil.copyfile(p,dst)
    mapping[name]=dict(sha256=expected,retained=dst.relative_to(HERE).as_posix())
write(deps/'index.json',mapping)
shutil.copytree(HERE,TARGET)
manifest={p.relative_to(TARGET).as_posix():sha(p)
          for p in sorted(TARGET.rglob('*')) if p.is_file()}
write(TARGET/'milestone-manifest.json',manifest)
report=ROOT/'docs/research/river-gpu-execution-001.md'
assert not report.exists()
report.write_bytes((HERE/'report.md').read_bytes())

def replace(p,before,after):
    data=p.read_text(encoding='utf-8')
    assert data.count(before)==1,(p,before)
    p.write_text(data.replace(before,after),encoding='utf-8',newline='\n')

brief=('The [GPU execution assessment](../docs/research/river-gpu-execution-001.md)\n'
       'measured 1.31x / 1.56x faster fixed-work solves on the two expanded trees,\n'
       'with essentially unchanged independently audited error. Including fresh\n'
       'solve processes and separate exact audits reduces the gain to 1.11x / 1.31x.\n'
       'This was an exploratory continuation after a retained trajectory-parity\n'
       'refusal, not an original-plan pass. Host GPU-process memory also increased.\n')
replace(ROOT/'experiments/RESULTS.md',
        'now links 42 retained river milestones through river-cfr-expanded-001.',
        'now links 43 retained river milestones through river-gpu-execution-001.\n\n'+brief)
replace(ROOT/'experiments/solver-foundations.md',
        '## Expanded-tree capacity: river-cfr-expanded-001',
        '## GPU execution: river-gpu-execution-001\n\n'+brief+'\n'
        'Next proposed test: bounded static graph replay, charging setup and audit.\n\n'
        '## Expanded-tree capacity: river-cfr-expanded-001')
replace(ROOT/'experiments/solver-foundations.md',
        'GPU-CFR execution assessment is next in the queue. Neural approximation remains',
        'The subsequent GPU execution assessment is recorded above. Neural approximation remains')
replace(ROOT/'experiments/gpu-representation.md',
        '**Current conclusion:**',
        '## Latest fixed-game execution test\n\n'+brief+'\n'
        'The direct eager port uses full 1,081-hand ranges in two restricted heads-up\n'
        'river trees. It does not implement GPU-CFR static compilation or graph replay.\n\n'
        '**Earlier consolidated conclusion:**')
replace(ROOT/'docs/research/README.md',
        'The latest milestone is **river-cfr-expanded-001**.',
        'The latest milestone is **river-gpu-execution-001**. The '
        '[GPU result](river-gpu-execution-001.md)\n'
        'retains 12 timing runs, four exact audits, and the original numerical\n'
        'parity refusal with its diagnosis. The exploratory continuation found\n'
        'modest speed gains at unchanged quality and greater host memory cost.\n\n'
        'The preceding milestone is **river-cfr-expanded-001**.')
replace(ROOT/'docs/research/README.md',
        'GPU-CFR assessment follows; no GPU run or neural training is authorized.',
        'GPU execution assessment has since completed above; neural training remains deferred.')
replace(ROOT/'docs/research/README.md','\n## Designs and frozen controls',
        '| river-gpu-execution-001 | [Result](river-gpu-execution-001.md) | '
        '[Milestone](../../experiments/river-abstraction-study/river-gpu-execution-001/) |\n\n'
        '## Designs and frozen controls')
replace(ROOT/'experiments/research-roadmap.md',
        '   GPU work remains contingent on measured CPU cost and representation capacity.',
        '   The [eager GPU test](../docs/research/river-gpu-execution-001.md) found modest\n'
        '   net speed gains with unchanged audited error. Next proposed: a bounded\n'
        '   static graph replay comparison including setup, reset and exact-audit costs.')
replace(ROOT/'experiments/research-roadmap.md',
        'Next assess [GPU-CFR](https://arxiv.org/html/2609.11923v1),\n'
        'as requested, with preparation/reuse costs included.',
        'The [GPU-CFR](https://arxiv.org/html/2609.11923v1)-motivated eager execution\n'
        'assessment is complete: see [retained result](../docs/research/river-gpu-execution-001.md).\n'
        'Next proposed question: static graph replay versus eager execution, with\n'
        'capture/reset costs and reuse break-even measured. Stop if the net gain is small.')
entry=dict(timestamp=datetime.now(timezone.utc).isoformat(),
    command='river-gpu-execution-001 original gate refusal plus frozen exploratory continuation',
    status='complete_exploratory_not_original_plan_pass',
    summary='12 timing runs; 4 exact audits; unchanged quality; modest GPU speed gain; see report',
    source_commit=read(Path('D:/Pontius/experiments/river-cfr-expanded-001/checkback/plan.json'))['source_commit'],
    output=str(TARGET.relative_to(ROOT)/'milestone-manifest.json'),
    output_sha256=sha(TARGET/'milestone-manifest.json'))
with (ROOT/'execution_journal.jsonl').open('a',encoding='utf-8',newline='\n') as f:
    f.write(json.dumps(entry,sort_keys=True)+'\n')
for name,expected in manifest.items(): assert sha(TARGET/name)==expected
for p,expected in prior.items(): assert sha(Path(p))==expected
print(json.dumps(dict(target=str(TARGET),members=len(manifest),
                     preserved_milestones=len(prior),preserved_members=count,
                     manifest_sha256=entry['output_sha256'])))
