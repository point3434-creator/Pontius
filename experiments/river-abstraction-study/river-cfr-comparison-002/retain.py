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

report = ROOT/'docs/research/river-cfr-comparison-002.md'
assert not report.exists()
report.write_bytes((HERE/'report.md').read_bytes())


def replace(path, before, after):
    text = path.read_text(encoding='utf-8')
    assert text.count(before) == 1, (path, before)
    path.write_text(text.replace(before, after), encoding='utf-8', newline='\n')


replace(ROOT/'docs/research/README.md',
        'The latest milestone is **river-cfr-comparison-001**.',
        'The latest milestone is **river-cfr-comparison-002**. The '
        '[different-position confirmation](river-cfr-comparison-002.md)\n'
        'again favors DCFR+: paper DCFR+ had 6.56x less error than matched CFR+,\n'
        'and released-code DCFR+ remained best. Matched prediction improved error\n'
        'about 11% here, unlike its loss on the first case. All 18 runs and six\n'
        'rational audits passed, but no arm reached the strict LP gap threshold.\n'
        'Next: test iterative solving on the expanded memory-limited trees.\n\n'
        'The preceding milestone is **river-cfr-comparison-001**.')
replace(ROOT/'docs/research/README.md', '\n## Designs and frozen controls',
        '| river-cfr-comparison-002 | [Result](river-cfr-comparison-002.md) | '
        '[Milestone](../../experiments/river-abstraction-study/river-cfr-comparison-002/) |\n\n'
        '## Designs and frozen controls')
replace(ROOT/'experiments/RESULTS.md',
        'now links 40 retained river milestones through river-cfr-comparison-001.',
        'now links 41 retained river milestones through river-cfr-comparison-002.\n\n'
        'The [second-position confirmation](../docs/research/river-cfr-comparison-002.md)\n'
        'again favored DCFR+ at the frozen 2,048 iterations: paper DCFR+ reduced error\n'
        '6.56x against matched CFR+, with released-code DCFR+ lowest. Prediction under\n'
        'matched parameters helped about 11% here after hurting on the first case.\n'
        'Two previously studied positions support discounting but do not settle prediction\n'
        'or universal algorithm rankings. All runs and independent audits completed;\n'
        'none reached the strict LP gap threshold. Expanded-tree capacity is next.')
replace(ROOT/'experiments/solver-foundations.md',
        '## New CFR comparison: river-cfr-comparison-001',
        '## CFR confirmation: river-cfr-comparison-002\n\n'
        'The [second position](../docs/research/river-cfr-comparison-002.md) adds milestone 41.\n'
        'Unchanged solver and six parameter sets: paper DCFR+ has 6.56x less error than\n'
        'matched CFR+; released-code DCFR+ again leads. Matched prediction improves\n'
        'error about 11%, versus a 5.99x increase on the first case. Its effect is mixed.\n'
        'All 18 repeats and six independent final rational audits completed. No strict\n'
        'LP-threshold pass. This shorter-stack case has one distinct opening bet and\n'
        'cannot establish capacity on the expanded trees. That test is now next.\n\n'
        '## New CFR comparison: river-cfr-comparison-001')
replace(ROOT/'experiments/research-roadmap.md',
        '   now favors DCFR+ on one full-range baseline river. Confirm a different case,\n'
        '   then compare the expanded trees against the same independent quality checks;',
        '   and [confirmation](../docs/research/river-cfr-comparison-002.md) favor DCFR+ on\n'
        '   two retained baseline rivers; prediction is mixed. Next compare the expanded\n'
        '   trees against the same independent quality checks;')
replace(ROOT/'experiments/research-roadmap.md',
        'Current order: DCFR+ confirmation on another retained case, then expanded-tree\n'
        'capacity and quality.',
        'DCFR+ confirmation on another retained case is complete. Next: expanded-tree\n'
        'capacity and quality.')
entry = dict(timestamp=datetime.now(timezone.utc).isoformat(),
             command='river-cfr-comparison-002 fixed-parameter second-position confirmation',
             status='complete_approximate_solutions',
             summary='18 workers and six rational audits; DCFR+ leads again; prediction mixed; '
                     'no strict LP gap pass',
             source_commit=read(HERE/'plan.json')['source_commit'],
             plan_sha256=digest(HERE/'plan.json'),
             output='experiments/river-abstraction-study/river-cfr-comparison-002/milestone-manifest.json',
             output_sha256=digest(TARGET/'milestone-manifest.json'))
with (ROOT/'execution_journal.jsonl').open('a', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(entry, sort_keys=True)+'\n')
assert all(digest(Path(p)) == expected for p, expected in prior.items())
print(json.dumps(dict(retained=str(TARGET), members=len(manifest),
                     prior_milestones=len(prior), prior_members_verified=members,
                     manifest_sha256=entry['output_sha256']), indent=2))
