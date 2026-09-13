from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import json
import gzip
import importlib.util

HERE=Path(__file__).parent
ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY=ROOT/'experiments/river-abstraction-study'
DEST=HISTORY/'river-lp-memory-001'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
def write(p,s): p.write_text(s,encoding='utf-8',newline='\n')
def data(p,v): write(p,json.dumps(v,indent=2,sort_keys=True)+'\n')
verified=read(HERE/'verification.json')
assert verified['passed']
def preserve():
    for name,h in verified['prior_manifests'].items():
        p=HISTORY/name/'milestone-manifest.json'
        assert digest(p)==h
        for member,v in read(p).items(): assert digest(p.parent/member)==v
preserve()
assert len(list(HISTORY.glob('*/milestone-manifest.json')))==37
DEST.mkdir(exist_ok=False)
encodings={}
def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    payload=source.read_bytes()
    if source.name.endswith('-trace.jsonl'):
        target=target.with_suffix(target.suffix+'.gz')
        encoded=gzip.compress(payload,mtime=0)
        target.write_bytes(encoded)
        assert gzip.decompress(target.read_bytes())==payload
        encodings[target.relative_to(DEST).as_posix()]=dict(codec='gzip',
            uncompressed_bytes=len(payload),uncompressed_sha256=sha256(payload).hexdigest())
    else: target.write_bytes(payload)
for sub in ('run','trace-correction'):
    for p in (HERE/sub).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            copy(p,DEST/sub/p.relative_to(HERE/sub))
for name in ('probe.py','plan.json','monitor-check.json','correct_probe.py','analyze.py',
             'analysis.json','verify.py','verification.json','retain.py'):
    copy(HERE/name,DEST/'author'/name)
for p,h in read(HERE/'trace-correction/plan.json')['pins'].items():
    source=Path(p)
    if source.name in ('_linprog_highs.py','_linprog_util.py','_highs_wrapper.py'):
        assert digest(source)==h
        copy(source,DEST/'observed-scipy-source'/source.name)
data(DEST/'trace-encoding.json',encodings)

report='''# River LP memory diagnostic 001

Both expanded deep-stack cells finished Python matrix assembly, SciPy conversion,
and native model loading below the 3072 MiB sampled limit. Their large memory
increase and stop occurred inside the first HiGHS native run() call. Copies are
measurable overhead, but the larger increase is native solve-time memory. This
locates an API boundary; it does not isolate presolve, simplex, or factorization.

## Frozen comparison

Reuse case 1 from river-tree-expansion-001: pot 29, effective stack 186, 1081 private
holdings per role and 1070190 compatible ordered deals. Run its successful baseline
control, expanded checkback tree, and tree adding one all-in raise layer. Keep all
payoffs, ranges, action menus, value scaling, LP algorithms/options and certification
unchanged. This is a same-case diagnostic, not a fresh-board strategy comparison.

The per-worker envelope is unchanged: 180 seconds and a 3072 MiB private-memory
stop sampled every 50 ms. Each LP retains highs-ds, 10 seconds, 20000 iterations,
and 1e-9 feasibility tolerances. The observer reads OS private memory at Python
source boundaries and the controller verifies the executing PID. No tracemalloc
or allocation tracing is used. Python line tracing and flushed records add work;
these instrumented times are not suitable for solver-speed comparisons.

## Memory result

First-player LP boundaries, in MiB. Each number is whole-worker memory at that
boundary, not exclusive ownership by the named component. The final column is OS
peak worker commit over the complete process, including both LPs for the baseline.

| Tree | Before linprog | After SciPy conversion | Before native run | Worker peak | Outcome |
|---|---:|---:|---:|---:|---|
'''
for row in verified['table']:
    label=row['label'].removeprefix('001-')
    vals=[f"{row[k]:.1f}" for k in ('before_linprog_mib','after_scipy_conversion_mib',
        'before_native_run_mib','whole_worker_peak_mib')]
    report+='| '+ ' | '.join([label,*vals,'Exact prior result' if label=='baseline' else 'Memory stop'])+' |\n'
report+='''
For checkback and raise, the last flushed marker is immediately before
_highs_wrapper.py:206, run_status = highs.run(). Neither call returned before its
worker was stopped. The native model-loading call at line 193 had returned. Every
observed OS high-water mark up to native run entry was below the sampled limit.
The rise from run entry to recorded worker peak was about 2404 and 4540 MiB.

The successful baseline also shows a large increase across the first native run:
about 1445 MiB in private memory from entry to return. Its two returned policies,
realization plans, payoff hashes and exact certificate equal the previous retained
baseline in both diagnostic attempts. Neither stopped cell has a saved policy or
quality result, and neither is credited as a completed solve.

The input path does make copies. In the checkback case, conversion of inequalities
to COO added about 147 MiB; stacking constraints temporarily added another 148 MiB.
The final CSC conversion reduced current memory. Native coefficient-vector copies
then added about 111 MiB, and passModel added another 112 MiB. Corresponding raise
figures were about 278, 279, 209, and 211 MiB. These are adjacent OS observations,
not allocation ownership proofs. Visible sparse buffers may share storage across
frames and must not be added together as if independent.

Removing copies may help, but this evidence does not establish that copy removal
alone would fit either expanded game. It also does not prove that direct solving
is inherently too costly or that a neural representation is required.

## Instrumentation defect and correction

The original frozen probe reproduced both stops and the exact baseline, but captured
only the outer solve() function. Under the isolated worker import, SciPy code filenames
contained mixed slash styles while the allowlist used resolved Windows paths. The
string comparison silently excluded its frames. The original probe, plan and all
outputs remain unchanged in author/ and run/ and are labeled incomplete evidence.

A separate trace-correction/ copy normalizes both lookup sides with normcase. Its
small LP control runs in the exact isolated import environment and checks all four
SciPy boundary functions. All four fail the original raw-path predicate and match
the corrected predicate. The full-run controller now also requires a native boundary
event. The corrected plan pins this control, the original attempt, and the unchanged
underlying experiment. No game, solver or budget change accompanies this correction.

Both monitor controls detected a 128 MiB allocation and checked sparse-buffer byte
accounting. The corrected retained runs captured 55898 baseline boundary events and
317 in each stopped worker, with PID identity checked for every event. The high
baseline count includes post-solve Python loops; it is not 55898 solver invocations.
Fresh post-run verification checked the marked boundaries, both exact control outputs,
all dependency pins, and all 3081 members of the 37 previous milestones.

The sampled stop is not a hard cap: the raise worker reached about 6.1 GiB before
termination despite the 3 GiB threshold. Neither capacity nor timing is guaranteed
by this monitor. No observations inside the native call were recorded, so presolve,
model transformations, simplex workspace and basis factorization remain unresolved.

'''
report+=f'''Original attempt: {verified['original_seconds']:.3f} seconds for three workers.
Corrected attempt: {verified['corrected_seconds']:.3f} seconds for three workers.
These include diagnostic overhead and are retention facts, not performance rankings.
Runtime checked: Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0.

Original plan SHA-256:
9952e44850e5a88a414a3b716929129528cfed54cc0711be87c584164fb89076

Corrected plan SHA-256:
1917df22d83f10350e862a5f8e4bf73b1793f7a35bea23a2214ff6ea560e6fbb

## Next decision and retained evidence

The next focused experiment should compare presolve enabled and disabled on these
same cells, retaining the same LP algorithm, matrix, exact acceptance rule and resource
limits. That is a diagnostic comparison, not a proposal to disable presolve permanently.
It can distinguish whether presolve materially changes this native memory boundary;
it cannot by itself isolate every subsequent native allocation. If that comparison
does not offer a practical improvement, reassess formulation or compression rather
than accumulating unmeasured wrapper micro-optimizations. No new run is implied here.

author/analysis.json contains the selected boundaries and adjacent memory changes;
author/verification.json contains independently recomputed boundary checks and the
prior-manifest preservation inventory. Observed SciPy Python sources are copied into
observed-scipy-source/. Complete traces are losslessly gzip-compressed to avoid adding
53 MiB of repetitive baseline text. trace-encoding.json binds the uncompressed sizes
and SHA-256 values, and decompression equality is checked before sealing. Expand a
trace before using a reader expecting the original .jsonl filename. Scratch scripts
retain their original absolute invocation paths; they are evidence, not new entry points.

This is restricted heads-up river research with factorized reached ranges, a limited
action tree, and no joint folded-card marginalization. No six-max playing-strength,
fresh-board generalization or production adoption claim. All 37 earlier milestones
are preserved. No production source was changed; this milestone is not committed or pushed.
'''
write(DEST/'report.md',report)
data(DEST/'preservation.json',dict(prior_milestones=37,prior_members=verified['prior_members'],
    prior_manifests=verified['prior_manifests'],all_prior_bytes_verified=True))
preserve()
manifest={p.relative_to(DEST).as_posix():digest(p) for p in sorted(DEST.rglob('*')) if p.is_file()}
data(DEST/'milestone-manifest.json',manifest)
for name,h in manifest.items(): assert digest(DEST/name)==h
write(ROOT/'docs/research/river-lp-memory-001.md',report)

def update(name,old,new):
    path=ROOT/name
    text=path.read_text(encoding='utf-8')
    assert old in text,(name,old)
    write(path,text.replace(old,new))

update('docs/research/README.md','The latest milestone is **river-tree-expansion-001**:',
    'The latest milestone is **river-lp-memory-001**. The [memory diagnostic](river-lp-memory-001.md)\n'
    'locates both deep-stack stops inside the native HiGHS run, after assembly and model\n'
    'loading. A presolve-on/off comparison is the next proposed diagnostic.\n\n'
    'The preceding milestone is **river-tree-expansion-001**:')
update('docs/research/README.md','All 37 retained','All 38 retained')
update('docs/research/README.md','37 independent','38 independent')
update('docs/research/README.md','| river-stack-transfer-001',
    '| river-lp-memory-001 | [Result](river-lp-memory-001.md) | '
    '[Milestone](../../experiments/river-abstraction-study/river-lp-memory-001/) |\n| river-stack-transfer-001')
update('experiments/solver-foundations.md','contains 37 retained milestones, from development-001 through\nriver-tree-expansion-001.',
    'contains 38 retained milestones, from development-001 through\nriver-lp-memory-001.')
note='''### Native memory boundary: river-lp-memory-001

The [same-cell memory diagnostic](../docs/research/river-lp-memory-001.md) places both
deep-stack stops inside the first native HiGHS run(), after model loading. Checkback
entered at 929 MiB and peaked at 3334 MiB; raise entered at 1698 MiB and peaked at
6237 MiB. Both controls reproduced the exact prior baseline policy and certificate.
Copies are measurable, but the larger memory increase occurs inside native solving.
The trace cannot yet distinguish presolve from later simplex or factorization work.

The original path filter missed SciPy frames under isolated Windows imports. That
incomplete attempt is preserved; a normalized filter, failing-original/passing-corrected
boundary control and separately frozen rerun supply the actual phase diagnosis.
The next test should vary only presolve, keep the same games and exact certificate,
and retain the same resource stops. This has not yet demonstrated a memory fix.

'''
update('experiments/solver-foundations.md','### Larger action tree:',note+'### Larger action tree:')
update('experiments/solver-foundations.md',
    'The next question is where memory is consumed in assembly/conversion/solver workspace,\nbefore choosing a targeted formulation change or declaring learned compression necessary.',
    'The subsequent memory diagnostic above locates the dominant increase inside native\nsolving, leaving its internal stage as the next controlled question.')
update('experiments/solver-foundations.md',
    '- The larger-tree test now identifies a deep-stack memory boundary. Measure assembly,\n  copies/conversions, and solver workspace before choosing a targeted storage or\n  formulation change. Preserve the same games and exact acceptance criterion.',
    '- The memory diagnostic locates both deep-stack stops inside native HiGHS solving.\n  Compare presolve on/off next with the same games, envelope and exact acceptance rule;\n  no copy optimization or solver-option change has yet earned adoption.')
update('experiments/solver-foundations.md','All 37 milestones','All 38 milestones')
update('experiments/solver-foundations.md','not 37 independent','not 38 independent')
update('experiments/RESULTS.md','all 37 retained river milestones through river-tree-expansion-001.',
    'all 38 retained river milestones through river-lp-memory-001.')
update('experiments/RESULTS.md',
    'of nine distinct cells; both expanded deep-stack games hit the memory stop. The next\nstep is memory accounting in this implementation, not more repair tuning.',
    'of nine distinct cells; both expanded deep-stack games hit the memory stop. The\n'
    '[memory diagnostic](../docs/research/river-lp-memory-001.md) locates both stops inside\n'
    'native HiGHS solving after conversion and model loading. The next controlled question\n'
    'is whether presolve changes that cost; no memory fix is yet demonstrated.')
update('experiments/RESULTS.md','tree has now exposed a memory boundary requiring a focused diagnostic.',
    'tree has now exposed a native-solver memory boundary, with presolve the next diagnostic variable.')
update('experiments/research-roadmap.md','37-milestone','38-milestone')
update('experiments/research-roadmap.md',
    '   seven distinct cells and stopped two expanded deep-stack cells on memory. Next,\n'
    '   separate assembly, copies/conversions, and solver workspace costs, then test one\n'
    '   targeted storage or formulation change against the same exact certificate.\n3. Revisit',
    '   seven distinct cells and stopped two expanded deep-stack cells on memory.\n'
    '3. Completed: [memory accounting](../docs/research/river-lp-memory-001.md) locates both\n'
    '   stops inside the native solve, after conversion and model loading. Next, compare\n'
    '   presolve on/off on the same cells, envelope and exact certificate.\n4. Revisit')
update('experiments/brainstorming.md',
    'seven verified cells and two deep-stack memory stops. Investigate implementation\nmemory before treating compression as necessary.',
    'seven verified cells and two deep-stack memory stops. The [memory diagnostic](../docs/research/river-lp-memory-001.md)\n'
    'locates their dominant increase inside native solving; compare presolve on/off before\n'
    'treating compression as necessary.')

spec=importlib.util.spec_from_file_location('journal',ROOT/'src/pontius/status_generation.py')
journal=importlib.util.module_from_spec(spec)
spec.loader.exec_module(journal)
journal.append_run(ROOT,dict(timestamp=datetime.now(timezone.utc).isoformat(),
    command='river-lp-memory-001 frozen three-cell diagnostic and trace-only correction',
    status='diagnostic_complete_capacity_unchanged',
    summary='Both deep-stack stops inside native HiGHS run; exact control preserved; original trace-filter miss retained',
    duration_seconds=verified['original_seconds']+verified['corrected_seconds'],
    source_commit='6518b9d3af252c93f8a9dbdb13fb28adc2859b4c',
    output='experiments/river-abstraction-study/river-lp-memory-001/milestone-manifest.json',
    output_sha256=digest(DEST/'milestone-manifest.json')))
write(ROOT/'STATUS.md',journal.render_status(ROOT))
print(json.dumps(dict(members=len(manifest),manifest_sha256=digest(DEST/'milestone-manifest.json'),
    compressed_trace_bytes=sum((DEST/p).stat().st_size for p in encodings),
    uncompressed_trace_bytes=sum(v['uncompressed_bytes'] for v in encodings.values())),indent=2))
