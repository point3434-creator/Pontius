"""Retain both expanded cells as one milestone and update current summaries."""
from pathlib import Path
from datetime import datetime, timezone
import json
import hashlib
import shutil

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
TARGET = HISTORY/HERE.name


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,indent=2,sort_keys=True)
        f.write('\n')


assert not TARGET.exists()
assessment = read(HERE/'assessment.json')
assert assessment['complete']
prior = {str(p):digest(p) for p in sorted(HISTORY.glob('*/milestone-manifest.json'))}
members = 0
for raw in prior:
    path = Path(raw)
    for name, expected in read(path).items():
        assert digest(path.parent/name) == expected
        members += 1
write(HERE/'preservation.json',dict(prior_milestones=len(prior),verified_members=members,
                                   prior_manifests=prior))
deps = HERE/'dependencies'
deps.mkdir()
mapping = {}
for variant in ('checkback','raise'):
    for name, expected in read(HERE/variant/'plan.json')['pins'].items():
        path = Path(name)
        assert digest(path) == expected
        if path.is_relative_to(HERE):
            continue
        dest = deps/(expected+path.suffix)
        if not dest.exists():
            shutil.copyfile(path,dest)
        mapping[name] = dict(sha256=expected,retained=dest.relative_to(HERE).as_posix())
write(deps/'index.json',mapping)
shutil.copytree(HERE,TARGET)
manifest = {p.relative_to(TARGET).as_posix():digest(p)
            for p in sorted(TARGET.rglob('*')) if p.is_file()}
write(TARGET/'milestone-manifest.json',manifest)
report = ROOT/'docs/research/river-cfr-expanded-001.md'
assert not report.exists()
report.write_bytes((HERE/'report.md').read_bytes())


def replace(path,before,after):
    data = path.read_text(encoding='utf-8')
    assert data.count(before)==1,(path,before)
    path.write_text(data.replace(before,after),encoding='utf-8',newline='\n')


brief = ('The [expanded-tree comparison](../docs/research/river-cfr-expanded-001.md)\n'
         'completed 24 training runs and eight independent rational audits within the\n'
         'original sampled 3,072 MiB budget on both trees where LP stopped on memory.\n'
         'This establishes checked approximate-solution capacity; it does not establish\n'
         'strict equilibrium convergence or a live resolver. The report retains all\n'
         'four fixed configurations, their quality curves, and full cost boundaries.\n')
replace(ROOT/'experiments/RESULTS.md',
        'now links 41 retained river milestones through river-cfr-comparison-002.',
        'now links 42 retained river milestones through river-cfr-expanded-001.\n\n'+brief)
replace(ROOT/'experiments/solver-foundations.md',
        '## CFR confirmation: river-cfr-comparison-002',
        '## Expanded-tree capacity: river-cfr-expanded-001\n\n'+brief+'\n'
        'GPU-CFR execution assessment is next in the queue. Neural approximation remains\n'
        'deferred; this experiment required no new private-hand compression.\n\n'
        '## CFR confirmation: river-cfr-comparison-002')
replace(ROOT/'docs/research/README.md',
        'The latest milestone is **river-cfr-comparison-002**.',
        'The latest milestone is **river-cfr-expanded-001**. The '
        '[expanded-tree result](river-cfr-expanded-001.md)\n'
        'demonstrates approximate-solution capacity on both formerly memory-limited\n'
        'trees: 24 training runs and eight rational audits completed. See the report\n'
        'for all errors, timing, memory and strict-convergence outcomes. The queued\n'
        'GPU-CFR assessment follows; no GPU run or neural training is authorized.\n\n'
        'The preceding milestone is **river-cfr-comparison-002**.')
replace(ROOT/'docs/research/README.md','\n## Designs and frozen controls',
        '| river-cfr-expanded-001 | [Result](river-cfr-expanded-001.md) | '
        '[Milestone](../../experiments/river-abstraction-study/river-cfr-expanded-001/) |\n\n'
        '## Designs and frozen controls')
replace(ROOT/'experiments/research-roadmap.md',
        '   two retained baseline rivers; prediction is mixed. Next compare the expanded\n'
        '   trees against the same independent quality checks;',
        '   two retained baseline rivers; prediction is mixed. The '
        '[expanded-tree test](../docs/research/river-cfr-expanded-001.md)\n'
        '   now completes both previously memory-limited cases with rational quality checks;')
replace(ROOT/'experiments/research-roadmap.md',
        'DCFR+ confirmation on another retained case is complete. Next: expanded-tree\n'
        'capacity and quality. Afterwards assess',
        'DCFR+ confirmation and expanded-tree capacity/quality tests are complete.\n'
        'Next assess')
entry = dict(timestamp=datetime.now(timezone.utc).isoformat(),
             command='river-cfr-expanded-001 frozen two-tree four-arm CPU comparison',
             status='complete_approximate_solutions',
             summary='24 training workers and eight independent audits completed on both '
                     'formerly LP-memory-limited trees; see report for residuals',
             source_commit=read(HERE/'checkback/plan.json')['source_commit'],
             output='experiments/river-abstraction-study/river-cfr-expanded-001/milestone-manifest.json',
             output_sha256=digest(TARGET/'milestone-manifest.json'))
with (ROOT/'execution_journal.jsonl').open('a',encoding='utf-8',newline='\n') as f:
    f.write(json.dumps(entry,sort_keys=True)+'\n')
for name, expected in manifest.items():
    assert digest(TARGET/name)==expected
assert all(digest(Path(p))==expected for p,expected in prior.items())
print(json.dumps(dict(retained=str(TARGET),members=len(manifest),
                     prior_milestones=len(prior),prior_verified_members=members,
                     manifest_sha256=entry['output_sha256'])))
