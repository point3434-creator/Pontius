"""Retain this completed experiment and update only the current research indexes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
TARGET = HISTORY/HERE.name


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def write(p, obj):
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')


assert not TARGET.exists()
assert read(HERE/'assessment.json')['complete']
manifests = sorted(HISTORY.glob('*/milestone-manifest.json'))
prior = {str(p):digest(p) for p in manifests}
members = 0
for manifest in manifests:
    for name, expected in read(manifest).items():
        assert digest(manifest.parent/name) == expected, (manifest, name)
        members += 1
write(HERE/'preservation.json', dict(prior_milestones=len(prior), verified_members=members,
                                    prior_manifests=prior))
# Preserve the exact external source/input closure for audit and future recovery.
dependencies = HERE/'dependencies'
dependencies.mkdir()
mapping = {}
for raw, expected in read(HERE/'plan.json')['pins'].items():
    path = Path(raw)
    assert digest(path) == expected
    if path.is_relative_to(HERE):
        continue
    dest = dependencies/(expected+path.suffix)
    if not dest.exists():
        shutil.copyfile(path, dest)
    mapping[raw] = dict(sha256=expected, retained=str(dest.relative_to(HERE)))
write(dependencies/'index.json', mapping)
shutil.copytree(HERE, TARGET)
manifest = {p.relative_to(TARGET).as_posix():digest(p)
            for p in sorted(TARGET.rglob('*')) if p.is_file()}
write(TARGET/'milestone-manifest.json', manifest)
for name, expected in manifest.items():
    assert digest(TARGET/name) == expected

report = ROOT/'docs/research/river-cfr-comparison-001.md'
assert not report.exists()
report.write_bytes((HERE/'report.md').read_bytes())


def replace(path, before, after):
    data = path.read_text(encoding='utf-8')
    assert data.count(before) == 1, (path, before)
    path.write_text(data.replace(before, after), encoding='utf-8', newline='\n')


replace(ROOT/'docs/research/README.md',
        'The latest milestone is **river-lp-presolve-001**.',
        'The latest milestone is **river-cfr-comparison-001**. The '
        '[six-arm comparison](river-cfr-comparison-001.md)\n'
        'ran 18 fresh workers on one full-range baseline river. DCFR+ led at 2,048\n'
        'iterations; matched prediction increased error. All six final errors were\n'
        'independently verified, but none met the strict LP convergence threshold.\n'
        'Next: confirm another case, then test the expanded memory-limited trees.\n\n'
        'The preceding milestone is **river-lp-presolve-001**.')
replace(ROOT/'docs/research/README.md', '## Designs and frozen controls',
        '| river-cfr-comparison-001 | [Result](river-cfr-comparison-001.md) | '
        '[Milestone](../../experiments/river-abstraction-study/river-cfr-comparison-001/) |\n\n'
        '## Designs and frozen controls')
replace(ROOT/'experiments/RESULTS.md',
        'now consolidates all 39 retained river milestones through river-lp-presolve-001.',
        'now links 40 retained river milestones through river-cfr-comparison-001.\n\n'
        'The [new CFR comparison](../docs/research/river-cfr-comparison-001.md) tested\n'
        'six configurations at 2,048 iterations on one retained full-range river. With\n'
        'averaging fixed, paper DCFR+ reduced error 8.10x versus CFR+; adding prediction\n'
        'under matched parameters increased error 5.99x. Released-code DCFR+ was the\n'
        'lowest-error arm. All 18 runs completed with repeat-identical policy bytes and\n'
        'six independent final rational checks. No arm reached the older strict LP\n'
        'threshold. Transfer and expanded-tree memory remain untested for this method.')
replace(ROOT/'experiments/solver-foundations.md',
        '## Which results support those conclusions?',
        '## New CFR comparison: river-cfr-comparison-001\n\n'
        'The [six-arm result](../docs/research/river-cfr-comparison-001.md) adds the 40th\n'
        'milestone. On one retained full-range baseline river, paper DCFR+ reduced final\n'
        'error 8.10x versus CFR+ with averaging held fixed. Matched prediction increased\n'
        'error 5.99x relative to DCFR+. Released-code DCFR+ was best, but its denominator\n'
        'differs from the paper and is separately labeled. Three repeats per arm matched\n'
        'policy bytes exactly; six rational audits confirm residuals, not strict convergence.\n'
        'Training took about 3.4 s per arm with roughly 129-131 MiB worker peak commit;\n'
        'independent audits needed about 337 MiB. Confirm another case and expanded-tree\n'
        'capacity before selecting a solver. The 39-milestone synthesis above remains\n'
        'the historical boundary; this addendum supplies the newly measured evidence.\n\n'
        '## Which results support those conclusions?')
replace(ROOT/'experiments/research-roadmap.md',
        '   either expanded game. Next, compare full-hand iterative payoff-product solving\n'
        '   against the LP references, retaining games and original-game quality checks.',
        '   either expanded game. The [initial CFR comparison](../docs/research/river-cfr-comparison-001.md)\n'
        '   now favors DCFR+ on one full-range baseline river. Confirm a different case,\n'
        '   then compare the expanded trees against the same independent quality checks;\n'
        '   GPU work remains contingent on measured CPU cost and representation capacity.')
entry = dict(timestamp=datetime.now(timezone.utc).isoformat(),
             command='river-cfr-comparison-001 frozen six-arm alternating CPU comparison',
             status='complete_approximate_solutions',
             summary='18 workers; six independent rational audits; DCFR+ led one retained board; '
                     'no arm meets strict LP gap threshold',
             source_commit=read(HERE/'plan.json')['source_commit'],
             plan_sha256=digest(HERE/'plan.json'),
             output='experiments/river-abstraction-study/river-cfr-comparison-001/milestone-manifest.json',
             output_sha256=digest(TARGET/'milestone-manifest.json'))
with (ROOT/'execution_journal.jsonl').open('a', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(entry, sort_keys=True)+'\n')
assert all(digest(Path(p)) == expected for p,expected in prior.items())
print(json.dumps(dict(retained=str(TARGET), members=len(manifest),
                     prior_milestones=len(prior), prior_members_verified=members,
                     manifest_sha256=entry['output_sha256']), indent=2))
