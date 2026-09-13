from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import json
import shutil
import importlib.util

HERE=Path(__file__).parent
ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY=ROOT/'experiments/river-abstraction-study'
DEST=HISTORY/'river-lp-presolve-001'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
def write(p,s): p.write_text(s,encoding='utf-8',newline='\n')
def data(p,v): write(p,json.dumps(v,indent=2,sort_keys=True)+'\n')
a=read(HERE/'assessment.json')
assert a['passed']
def preserve():
    for name,h in a['prior_manifests'].items():
        p=HISTORY/name/'milestone-manifest.json'
        assert digest(p)==h
        for member,v in read(p).items(): assert digest(p.parent/member)==v
preserve()
assert len(list(HISTORY.glob('*/milestone-manifest.json')))==38
DEST.mkdir(exist_ok=False)
shutil.copytree(HERE/'run',DEST/'run')
(DEST/'author').mkdir()
for name in ('experiment.py','preflight.json','plan.json','assess.py','assessment.json','retain.py'):
    shutil.copyfile(HERE/name,DEST/'author'/name)
report='''# River LP presolve comparison 001

Disabling HiGHS presolve did not recover either expanded deep-stack game within the
unchanged sampled memory envelope. Both baseline arms passed exact verification.
The off baseline used less peak memory but took longer in this single fresh pair.
No solver-option change earns adoption from this result.

## Question and frozen design

Does presolve account for enough of the native memory increase that turning it off
makes either stopped game affordable? Reuse the same pot-29, stack-186 case from
river-tree-expansion-001, with 1081 holdings per role and 1070190 compatible ordered
deals. Keep the original baseline, betting after check, and one-all-in-raise trees.

Run six fresh workers, one per tree/setting. Order is baseline on/off, checkback
off/on, raise on/off. This balances ordering direction somewhat; it is not random
assignment or statistical replication. Presolve is the sole solver-option change.
Each LP retains highs-ds, 10 seconds, 20000 iterations, 1e-9 feasibility tolerances,
2^20 value scaling, and the exact original-payoff gap threshold <=1e-8. Each worker
retains 180 seconds and the 3072 MiB private-memory stop sampled every 50 ms.

The adapter records the effective options, executing PID, and hashes of objective,
constraints, bounds and right-hand sides before every LP. Corresponding entered
calls received identical matrices and bounds in each pair. Both expanded workers
stop in call 0, so there is no executed second-call equivalence claim for those cells.
No full Python line trace or allocation tracer runs here. Hashing and compact call
records add the same measurement operations to both arms; compute timing includes them.

## Results

Compute includes game setup, assembly, both LP calls, policy extraction and exact
certification. Whole worker additionally includes startup, binding checks and output.
Peak is OS whole-worker commit, not exclusive LP memory. One observation per cell.

| Tree | Presolve | Compute s | Worker s | Peak MiB | Outcome |
|---|---|---:|---:|---:|---|
'''
rows={r['label']:r for r in a['table']}
for variant in ('baseline','checkback','raise'):
    for setting in ('on','off'):
        row=rows[f'001-{variant}-{setting}']
        compute='not completed' if row['compute_seconds'] is None else f"{row['compute_seconds']:.3f}"
        outcome='Exact certificate passed' if row['strict_pass'] else 'Memory stop'
        report+=f"| {variant} | {setting} | {compute} | {row['worker_seconds']:.3f} | {row['peak_mib']:.1f} | {outcome} |\n"
report+='''
The baseline off arm used about 178 MiB less peak memory, with compute increasing
from 6.34 to 7.95 seconds. This is a descriptive paired observation, not an established
speed or memory ranking. Its exploitability was 1.0192e-15 versus 8.3749e-16 for on;
both are far below the unchanged acceptance limit of 5e-9 (half the gap limit).
Different numerical solutions are allowed; their certified equilibrium intervals overlap.
The on control also reproduced the earlier baseline policy, realization vectors,
payoff hashes and certificate exactly.

Both expanded off arms still reached the sampled stop. Lower recorded peaks or
shorter time-to-kill in these censored runs are not completed-solve improvements.
Neither has a saved policy, quality score, full-solve time or full-solve memory peak.
The monitor permits large overshoot: raise reached about 6 GiB under either setting.
The 3 GiB threshold is unchanged and is not a hard cap.

This establishes that disabling presolve alone is insufficient for these matrices
under this envelope. It does not establish that presolve is harmless, identify the
remaining native allocation, or rule out a better LP formulation. There is no fresh
board, independent replication panel, six-max strength result or compression result.

## Verification and retention

Preflight solved a tiny public-tree game under both settings, checked forwarded
options and identical LP inputs, required exact certificates and overlapping bounds,
and exercised the memory observer with a 128 MiB allocation. Four tiny LPs completed.

The main campaign completed four LP calls across the two baseline arms. Four expanded
workers were stopped during their first call. Each completed policy was checked in
a separate process with optimization forbidden, rebuilding its original payoff hashes,
behavior and exact certificate. The already-retained zero-payoff verifier correction
was used only for verification; the worker uses the original frozen tree implementation.
Thirty engine terminal checks and six literal rational subgames passed; the baseline
bounds overlap the older independently computed reference. All observed PIDs match.

The post-run assessment checked all six outcomes, option records, entered pairwise
matrix identities, exact control equality, and preservation of all 3130 members in
the 38 prior milestones. The unchanged source dependency pins were checked before
and after the campaign. All four stops remain retained with no score imputation.

'''
report+=f'''Campaign wall time: {a['campaign_seconds']:.3f} seconds, including separate verification.
Runtime: Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0, one BLAS/OpenMP thread.
Frozen plan SHA-256:
1215eb9a264712154212cf5ba57cbf62d15afe3dd523ba1651d8a309951bb5ea

## Next research decision

Close this presolve toggle as a capacity non-improvement and keep the LP references.
The next useful comparison is a full-hand iterative method that computes payoff
products directly without constructing the large LP. Start on these same nested
river trees; measure memory and original-game exploitability against compute, with
the certified baseline as a control. Preserve private-hand detail and action menus
so representation and solver changes are not confused. Approximate progress must
not be relabeled as passing the strict exact threshold. This is a proposed research
comparison, not an already implemented solver or authorization for another run.

If that comparison also has no useful quality/cost tradeoff, revisit formulation or
compression as an explicit new direction. Do not continue an open-ended sequence
of option toggles. The restricted heads-up model and factorized public ranges remain
limitations; joint folded-card marginalization and multiway strength are untested.

Raw call records, worker/verification receipts and policies are under run/. The
frozen adapter, plan, preflight and assessment are under author/. No production
source changed. All previous milestones remain intact. Saved locally, not committed
or pushed.
'''
write(DEST/'report.md',report)
data(DEST/'preservation.json',dict(prior_milestones=38,prior_members=3130,
    prior_manifests=a['prior_manifests'],all_prior_bytes_verified=True))
preserve()
manifest={p.relative_to(DEST).as_posix():digest(p) for p in sorted(DEST.rglob('*')) if p.is_file()}
data(DEST/'milestone-manifest.json',manifest)
for name,h in manifest.items(): assert digest(DEST/name)==h
write(ROOT/'docs/research/river-lp-presolve-001.md',report)
def update(name,old,new):
    p=ROOT/name
    text=p.read_text(encoding='utf-8')
    assert old in text,(name,old)
    write(p,text.replace(old,new))
update('docs/research/README.md','The latest milestone is **river-lp-memory-001**.',
    'The latest milestone is **river-lp-presolve-001**. The [presolve comparison](river-lp-presolve-001.md)\n'
    'did not recover either expanded game: both settings hit memory stops. The proposed\n'
    'next comparison is full-hand iterative solving without the large LP.\n\n'
    'The preceding milestone is **river-lp-memory-001**.')
update('docs/research/README.md','loading. A presolve-on/off comparison is the next proposed diagnostic.',
    'loading. The subsequent presolve comparison above tests that hypothesis.')
update('docs/research/README.md','All 38 retained','All 39 retained')
update('docs/research/README.md','38 independent','39 independent')
update('docs/research/README.md','| river-stack-transfer-001',
    '| river-lp-presolve-001 | [Result](river-lp-presolve-001.md) | '
    '[Milestone](../../experiments/river-abstraction-study/river-lp-presolve-001/) |\n| river-stack-transfer-001')
update('experiments/solver-foundations.md','contains 38 retained milestones, from development-001 through\nriver-lp-memory-001.',
    'contains 39 retained milestones, from development-001 through\nriver-lp-presolve-001.')
note='''### Presolve capacity non-improvement: river-lp-presolve-001

The [six-worker comparison](../docs/research/river-lp-presolve-001.md) varied only
presolve on/off on the same three deep-stack trees. Both expanded trees hit memory
stops under both settings. The two baseline arms passed separate exact verification;
turning presolve off reduced peak memory from 2082 to 1904 MiB but increased compute
from 6.34 to 7.95 seconds in this single pair. Entered paired LP matrices were identical.

Disabling presolve alone is insufficient. Censored stop times and peaks do not rank
completed solves. Close the toggle here; next compare a full-hand iterative method
using direct payoff products with the LP reference, measuring memory and original-game
exploitability against compute. Keep private-hand detail, menus and strict acceptance
claims fixed. No iterative implementation or capacity improvement is established yet.

'''
update('experiments/solver-foundations.md','### Native memory boundary:',note+'### Native memory boundary:')
update('experiments/solver-foundations.md',
    'The next test should vary only presolve, keep the same games and exact certificate,\nand retain the same resource stops. This has not yet demonstrated a memory fix.',
    'The subsequent presolve comparison above follows this proposal and finds no capacity\nrecovery. The remaining native allocation is not isolated by these measurements.')
update('experiments/solver-foundations.md',
    '- The memory diagnostic locates both deep-stack stops inside native HiGHS solving.\n'
    '  Compare presolve on/off next with the same games, envelope and exact acceptance rule;\n'
    '  no copy optimization or solver-option change has yet earned adoption.',
    '- The native-memory diagnostic and presolve comparison did not recover the deep-stack\n'
    '  trees. Next compare full-hand iterative payoff-product solving against the LP\n'
    '  references on the same games, measuring quality, complete cost and memory.')
update('experiments/solver-foundations.md','All 38 milestones','All 39 milestones')
update('experiments/solver-foundations.md','not 38 independent','not 39 independent')
update('experiments/RESULTS.md','all 38 retained river milestones through river-lp-memory-001.',
    'all 39 retained river milestones through river-lp-presolve-001.')
update('experiments/RESULTS.md',
    'native HiGHS solving after conversion and model loading. The next controlled question\nis whether presolve changes that cost; no memory fix is yet demonstrated.',
    'native HiGHS solving after conversion and model loading. The [presolve comparison](../docs/research/river-lp-presolve-001.md)\n'
    'then failed to recover either expanded game. The next proposed comparison is a\n'
    'full-hand iterative method that avoids the large LP, evaluated on the same games.')
update('experiments/RESULTS.md',
    'tree has now exposed a native-solver memory boundary, with presolve the next diagnostic variable.',
    'tree has exposed a native-solver memory boundary that disabling presolve did not resolve.')
update('experiments/research-roadmap.md','38-milestone','39-milestone')
update('experiments/research-roadmap.md',
    '   stops inside the native solve, after conversion and model loading. Next, compare\n'
    '   presolve on/off on the same cells, envelope and exact certificate.\n4. Revisit',
    '   stops inside the native solve, after conversion and model loading.\n'
    '4. Completed: [presolve on/off](../docs/research/river-lp-presolve-001.md) did not recover\n'
    '   either expanded game. Next, compare full-hand iterative payoff-product solving\n'
    '   against the LP references, retaining games and original-game quality checks.\n5. Revisit')
update('experiments/brainstorming.md',
    'locates their dominant increase inside native solving; compare presolve on/off before\ntreating compression as necessary.',
    'locates their dominant increase inside native solving. [Disabling presolve](../docs/research/river-lp-presolve-001.md)\n'
    'did not recover capacity. Next compare full-hand iterative payoff products with\n'
    'the LP reference before treating private-hand compression as necessary.')
spec=importlib.util.spec_from_file_location('journal',ROOT/'src/pontius/status_generation.py')
journal=importlib.util.module_from_spec(spec)
spec.loader.exec_module(journal)
journal.append_run(ROOT,dict(timestamp=datetime.now(timezone.utc).isoformat(),
    command='river-lp-presolve-001 frozen six-worker on/off comparison',status='capacity_non_improvement',
    summary='Both expanded trees stopped on memory with presolve on and off; two baseline arms certified',
    duration_seconds=a['campaign_seconds'],source_commit='6518b9d3af252c93f8a9dbdb13fb28adc2859b4c',
    output='experiments/river-abstraction-study/river-lp-presolve-001/milestone-manifest.json',
    output_sha256=digest(DEST/'milestone-manifest.json')))
write(ROOT/'STATUS.md',journal.render_status(ROOT))
print(json.dumps(dict(members=len(manifest),manifest_sha256=digest(DEST/'milestone-manifest.json'))))
