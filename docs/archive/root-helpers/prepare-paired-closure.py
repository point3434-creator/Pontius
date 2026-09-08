"""Prepare the bounded measured comparison decision; no game module is loaded."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

base = 'dfd5a5c6a9d8aae6cbbae667f9b0716c59362eed'
source_base = 'bd71f4b11dcc0177283431a4ec468fdc152e7686'
root = Path('D:/Pontius/tmp/v0a-paired-closure-r001')
work = root/'authoring'
evidence = Path('D:/Pontius/tmp/v0a-paired-rehearsal-run-001')
git_exe = 'C:/Program Files/Git/cmd/git.exe'
prefix = 'docs/architecture/v0a-paired-closure-r001/'
adr_path = 'docs/decisions/ADR-0511-close-the-measured-paired-comparison-contract.md'
paths = [adr_path, prefix+'operating-contract.md', prefix+'cost-basis.json',
         prefix+'evaluation-request.json', 'STATUS.md']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw.encode() if isinstance(raw, str) else raw)


def git(repo, *args):
    return subprocess.run([git_exe, '--no-replace-objects', '-c',
        f'safe.directory={repo.as_posix()}', '-C', str(repo), *args],
        check=True, capture_output=True).stdout


assert git(Path('D:/Pontius'), 'rev-parse', 'HEAD').decode().strip() == base
assert not git(Path('D:/Pontius'), 'status', '--porcelain', '--untracked-files=no')
assert not root.exists()
root.mkdir()
git(Path('D:/Pontius'), 'clone', '--quiet', '--no-hardlinks', '--no-checkout', 'D:/Pontius', str(work))
git(work, '-c', 'core.autocrlf=false', 'checkout', '--quiet', '-b', 'codex/paired-measured-closure', base)
report_raw = (evidence/'cost-report.json').read_bytes()
assert sha(report_raw) == 'b5ea6a530713d94a23c6670b8881c094e896c76dc8d5f17ece2f47d230ea5d1e'
report = json.loads(report_raw)
assert report['wrapper']['parent_elapsed_ns'] == 184531000000
assert report['reader']['parent_elapsed_ns'] == 1016000000
assert max(u['elapsed_ns_prefix'] for u in report['units']) == 7891000000
assert report['output_retained_bytes'] == 466940
inventory_raw = (evidence/'output-file-inventory.json').read_bytes()
assert sha(inventory_raw) == '9bec9a2d2d6c8fc54462030832a39c8b543c07a8f1d694f80d5f672ac4e85bd0'
for row in json.loads(inventory_raw):
    raw = (evidence/'output'/row['path']).read_bytes()
    assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
def round_up(n, step):
    return ((n+step-1)//step)*step
trial_ns = round_up(4*(7891000000+1016000000), 10000000000)
total_ns = round_up(48*(trial_ns+5000000000)+4*(184531000000+1016000000),60000000000)
reader_ns = round_up(2*4*1016000000,5000000000)
storage = round_up(2*4*466940,1048576)
assert (trial_ns,total_ns,reader_ns,storage) == (40000000000,2940000000000,10000000000,4194304)
seed_input = 'pontius-paired-evaluation-001\n'+base+'\n'
seed = sha(seed_input.encode('ascii'))
request = dict(version='pontius-v0a-evaluation-request-v1', seed=seed,
    deal_count=2, lineups=[['passive']*5,
        ['fold_to_bet','min_raise_once','passive','shove_once','passive']],
    seat_start=0, initial_button=0, trial_budget_ms=trial_ns//1000000,
    total_budget_ms=total_ns//1000000)
request_raw = (json.dumps(request,sort_keys=True,separators=(',',':'))+'\n').encode()
save(work/paths[3], request_raw)
record_names = ['cost-report.json','cost-verification.json','output-file-inventory.json',
    'source-identity.json','wrapper-intent.json','wrapper-launch.json','wrapper-receipt.json',
    'reader-intent.json','reader-launch.json','reader-receipt.json','reader-stdout.bin',
    'approval.json','request.json']
basis = dict(rehearsal_root=evidence.as_posix(), source_commit=source_base,
    records={n:sha((evidence/n).read_bytes()) for n in record_names},
    wrapper_ns=184531000000, reader_ns=1016000000, max_unit_prefix_ns=7891000000,
    output_bytes=466940, output_files=137, source_tracked_bytes=352068715,
    rehearsal_pairs=12, rehearsal_trials=24, comparison_pairs=24, comparison_trials=48,
    population_multiplier=2, discretionary_margin=4, trial_budget_ms=40000,
    total_budget_ms=2940000, reader_budget_ms=10000, retained_output_cap_bytes=4194304,
    lane_lifecycle_budget=1, seed_derivation_input=seed_input, seed=seed,
    request_bytes=len(request_raw), request_sha256=sha(request_raw),
    missing_measurements=['peak process-tree memory','peak disk','action latency distribution'],
    standing='Cost provenance only; no rehearsal poker outcomes used or reproduced')
save(work/paths[2], json.dumps(basis,sort_keys=True,indent=2)+'\n')
save(root/'preparation-facts.json',json.dumps(dict(base=base,paths=paths,basis=basis),indent=2)+'\n')
adr = f'''# ADR-0511: Close the measured paired comparison contract

- Status: accepted bounded descriptive comparison contract upon its authorized decision commit
- Date: 2026-09-07
- Follows: ADR-0510
- Base-Commit: {base}
- Invocation-Authority: none until exact single comparison launch authorization
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0511
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Authorize the single 48-trial descriptive paired comparison
- Front-Door-Blockers: comparison unrun; strength and full-evaluation resource evidence absent

## Decision and exact boundary

Retain ADR-0510's completed, non-evidentiary cost rehearsal and close only the
measured operating contract for one descriptive paired comparison. The controller
asked to proceed to this measured decision after the completed rehearsal. The
companion operating-contract.md, cost-basis.json and evaluation-request.json under
docs/architecture/v0a-paired-closure-r001/ are normative with this decision.
No candidate bytes take effect until exact review, acceptance and decision adoption.
Commit approval and launch approval are distinct; exact approval may bundle both.

Prospectively supersede ADR-0489's deferred operational opening and ADR-0508/0509's
source-only prohibition solely for this named comparison under separate launch
authority. ADR-0510's consumed rehearsal stays closed. This is a descriptive local
engineering comparison of two fixed existing policies, not research/strength,
league, real play, training, tuning or an operational opening of other v0a owners.
The unchanged correctness namespace and evidentiary=false remain literal. External
authority permits only the descriptive arithmetic below; no machine-enforced
authorization or research evidentiary status is claimed.

## Retained cost provenance

The sole rehearsal remains at D:/Pontius/tmp/v0a-paired-rehearsal-run-001.
Its cost-report.json SHA256 is
b5ea6a530713d94a23c6670b8881c094e896c76dc8d5f17ece2f47d230ea5d1e;
output-file-inventory.json SHA256 is
9bec9a2d2d6c8fc54462030832a39c8b543c07a8f1d694f80d5f672ac4e85bd0.
The companion cost-basis.json pins thirteen original provenance records. All raw
evidence stays at its retained local paths; no off-machine backup is asserted here.

Observed: 24/24 trials and 12/12 pairs completed; the one public reader passed;
all 24 unit cleanup records report complete. Parent launch-through-exit time was
184.531 seconds, the separate reader 1.016 seconds, and the maximum unit elapsed
prefix 7.891 seconds. Retained output was 137 regular files totaling 466940 bytes.
Parent intervals include supervisor scheduling and up to one second of polling.
Unit elapsed_ns ends before unit result publication. Whole result total_elapsed_ns
also precedes final publication; neither is a complete per-trial or total wall.
No timing subtraction is used to invent disjoint cost attribution.

Rehearsal poker values were not printed, ranked or used for any decision. Costs
alone supply provenance. The earlier source tests retain their correctness standing.
This decision never turns rehearsal completion into correctness or quality evidence.

## Measured choices and their limits

Let T=7.891 s (maximum unit prefix), R=1.016 s (reader interval), W=184.531 s
(whole parent interval), and S=466940 bytes (retained output). Use population
multiplier two and discretionary margin four. The margin is engineering judgment,
not a fitted coefficient, confidence bound or measured worst-case multiplier.

- Trial allowance: round up 4*(T+R) to 10 s = 40 s = 40000 ms. Adding the
  whole reader interval is a conservative proxy allowance for unmeasured unit
  publication; it does not identify or upper-bound that publication interval.
- Shared internal allowance: round up [48*(40+5)+4*(W+R)] to 60 s = 2940 s,
  or 2940000 ms (49 minutes). The inherited 5 s reserve is unchanged. The
  additional term is conservative slack, not a decomposition of measured work.
- External single-reader allowance: round up 2*4*R to 5 s = 10 s.
- Post-termination retained-output acceptance cap: round up 2*4*S to 1 MiB
  = 4194304 bytes. This bounds accepted retained output, not peak disk use.

The comparison population is the already planned twofold expansion: two fresh
deals, the same two lineups, six positions and two arms = 24 pairs/48 trials.
Unpadded linear projections 2*W=369.062 s and 2*S=933880 bytes are planning
estimates only. Different cards can change action counts, runtime and output.
No new-deal worst-case, success probability or complete host-resource guarantee
follows. If these prospective allowances fail, retain the failure; do not enlarge
them to make this owner pass, thin the population or replace a failed arm.

The wrapper enforces its unchanged trial/shared deadline and prelaunch admission.
Shared time starts before deal generation, after source admission. Publication
commits within that deadline; postcommit guard release and CLI return can be later.
No total-source-admission, visibility-by-deadline or hard OS wall is claimed. The
40 s trial can expire before the inherited 300 s hand limit; that is a retained
whole-comparison failure, not permission to censor a long hand and average survivors.
The 15000 ms action wall, 1000 ms emission reserve and native containment are unchanged.

## Resource applicability and lane breakers

ADR-0489 requires naming a missing limit's consumer and protected property. This
fixed CPU-only serial comparison has no model load, training, GPU, concurrency
expansion or resource-performance hypothesis. It preserves the source's finite
input/action/capture limits, native child containment, one-trial-at-a-time launch,
active operator supervision and immediate stop for resource pressure.
No aggregate peak-memory or peak-disk ceiling is asserted or waived: neither is
an acceptance claim of this bounded descriptive operation. Peak process-tree memory,
peak disk and action-latency distributions remain unknown and block any later
consumer that requires them, including the applicable full-evaluation profiles.
If preflight discovers a required host safety limit that this contract cannot
establish, refuse this opportunity; do not treat absence of measurement as zero.

Existing 4 MiB child stdout, 64 KiB child stderr, 2 MiB decoded stdout and other
source schema limits stay unchanged. Observed maximum unit stdout was 26374 bytes
and stderr zero; this is finite coverage, not proof these limits suffice on new cards.
The separate output cap is checked by regular-file inventory after termination,
before descriptive consumption. It neither monitors nor certifies peak occupancy.
Source checkout tracked bytes were 352068715 and stay separate from output and
supervisor diagnostics. All limits and failures retain their actual scope.

Open a lane budget of exactly one operational invocation: the smallest nonzero
allocation, grounded in one completed 24-trial rehearsal and the fixed twofold
work expansion above. This is a policy cap, not an inferred population statistic.
Reservation collision, failed preflight, unknown launch, interruption or failure
spends the opportunity. Completion also exhausts it and requires a written
architecture checkpoint with an explicit park-or-continue ruling before any
successor source seal or owner. There is no automatic second invocation. The
two-consecutive infrastructure/lifecycle/authorization-deaths stand-down remains;
every later admitted owner including failed owners counts and cannot reset history.

## Acceptance and next action

Five paths only: this ADR, operating-contract.md, cost-basis.json,
evaluation-request.json and generated STATUS.md. No source, test, old fixture,
policy, registration, earlier decision or retained artifact changes. Tier C:
measured authority, consumption gates, population, identity and outcome meaning.
Ground truth is the governing contract, raw retained measurements and sealed public
source; calculations and margin choices are explicitly the author's design.
Finalizer: Codex coordinator. Only this comparison waits on this closure.

Freeze one immutable candidate. Obtain two fresh independent CLEAN reviews, then
status --check and twelve status tests on actual 3.11.15 first, then 3.14.6,
each from a fresh exact-candidate D-local snapshot with scrubbed -B -P, cwd/src,
actual version/module-origin probe and absolute native Git. Independently verify
all cost pins, formulas, literal request, source identity and reserved-root absence.
No source or poker correctness tests, dealer, reader, rehearsal or comparison runs
during proposal acceptance. One initial plus at most three within-scope correction
rounds; ordinary residual/root-cause rules apply. Scope expansion needs a ruling.

After acceptance, request exact commit/push and single comparison launch authority.
Retain failure or complete descriptive report afterward; do not issue a favorable
quality verdict. Research ADR-0280 and runtime ADR-0307 stay authoritative. No
strength, full league, real play, H32, neural, GPU, compiled, analyzer, cleanup,
ref retirement, training or historically consumed owner is opened.
'''
save(work/adr_path, adr)
contract = f'''# Single measured descriptive paired comparison

Normative only upon ADR-0511's exact adoption. One subsequent exact launch approval
is required. This closes the ADR-0510 planning target without altering its lineups,
strategies, population size or forbidden claims after any poker outcome.

## Frozen source, request and schedule

Execution source is {source_base}, tree
54a257f4f2957696b9d33e7338ce140206a3f578. Use a fresh D-local --no-hardlinks
detached clone with core.autocrlf=false, no overlay, and complete tracked raw-blob
verification before launch and again before artifact consumption. Preserve the
source snapshot. ADR-0509's source acceptance is inherited, not rerun or relabeled.
The wrapper/contract and all source pins in ADR-0510 remain unchanged.

The exact companion request has {len(request_raw)} canonical ASCII/LF bytes; SHA256:
{sha(request_raw)}.
Its fresh seed is
{seed}.
Derive it once as SHA256 of these ASCII bytes: the line
pontius-paired-evaluation-001, LF, {base}, LF.
No seed search, entropy selection, generator call or card preview occurs in this
preparation. This deterministic fresh seed differs from the synthetic zero seed;
no unique-card or probabilistic-independence guarantee is claimed. No favorable
seed replacement, overlap-driven redraw or preview is allowed after it is frozen.

Two deals d=0,1; button d; seat_start=0; controlled seats 0..5. For each deal,
lineup 0 is five passive opponents; lineup 1 clockwise from the controlled seat
is fold_to_bet/min_raise_once/passive/shove_once/passive. Physical cards remain
fixed within a deal across rotations. Stacks reset to 200 each, blinds 1/2.
Pair index p=6*(2*d+lineup)+rotation. For even p baseline-rules-v1 runs first,
for odd p blueprint-v1 runs first. Both arms use the exact same saved pair input
and unchanged empty blueprint. There are 24 pairs and 48 sequential session units.
The wrapper creates the full fixed plan before the first session; no adaptive order.

## Ownership and exact public commands

Reserve D:/Pontius/tmp/v0a-paired-evaluation-run-001 only after adoption and launch
approval; it stays absent throughout preparation. source/, process-temp/,
request.json and output/ are disjoint siblings. output/ stays absent until the
public wrapper exclusively creates it. Evaluation ID:
pontius-v0a-evaluation-v1-correctness-comparison-001.
Its 14-character suffix comparison-001 produces standard session suffixes
eval-comparison-001-u001 through -u048, with unchanged host/event descendants.

Actual interpreter D:/Pontius-tools/py311/Scripts/python.exe, CPython 3.11.15;
verify executable/version/-B/-P/source cwd first. Set PYTHONPATH=<source>/src,
PYTHONNOUSERSITE=1, PYTHONIOENCODING=utf-8, TEMP/TMP=<root>/process-temp,
PONTIUS_GIT=C:\\Program Files\\Git\\cmd\\git.exe. Retain only SystemRoot, WINDIR,
SystemDrive, COMSPEC, USERPROFILE, APPDATA, LOCALAPPDATA plus these explicit values.
Record raw native executable hashes, exact source/request and full argv/environment.
Create-new approval, reservation and intent before Popen. The sole payload is:

```text
-B -P tools/v0a_evaluation.py
--request D:/Pontius/tmp/v0a-paired-evaluation-run-001/request.json
--output-root D:/Pontius/tmp/v0a-paired-evaluation-run-001/output
--evaluation-id pontius-v0a-evaluation-v1-correctness-comparison-001
```

The operator stays active, preserves raw captures and monotonic parent start before
Popen through observed exit, and stops on source/request drift, resource pressure,
capture overflow, interruption, lost supervision or stuck process. Retain UTC only
for correlation. Use the existing native containment and external process-tree stop
facilities. Unknown cleanup is incomplete. Parent stdout/stderr caps are 64 KiB each;
overflow stops and retains the attempt, never truncates into accepted success.
No poker-score-based early stop. No retry, resumed root, alternative interpreter,
warm-up, test, seed change, extra dealer call, private execution path or deletion.

## Consumer and descriptive report

After exit, inventory regular files under output/ without following links. Retain
their paths, lengths and hashes. An unsafe path or sum above 4194304 bytes refuses
descriptive consumption and consumes the owner; it is a post-run output gate,
not an assertion that execution never used more disk. Source and operator files
are excluded from this explicitly scoped cap and reported separately.

If source/request identity and output cap hold, call the unchanged public reader
at most once from the same exact source/cwd/environment. Its entire -c program is:

```python
import json, runpy
from pathlib import Path
module = runpy.run_path('tools/v0a_evaluation.py', run_name='paired_comparison_reader')
result = module['read_completed'](
    Path('D:/Pontius/tmp/v0a-paired-evaluation-run-001/output'))
assert result['source_commit'] == '{source_base}'
assert result['request_sha256'] == (
    '{sha(request_raw)}')
assert result['planned_pairs'] == result['completed_pairs'] == 24
assert result['planned_trials'] == result['completed_trials'] == 48
print(json.dumps(result, sort_keys=True, separators=(',', ':')))
```

Reader argv is -B, -P, -c, that literal program as one argument. No main, execute,
private loader, dealer or poker method is called. Capture stdout/stderr up to 64 KiB
each. Measure the external parent interval separately; if exit is not observed
within 10000 ms, stop the reader process tree and refuse descriptive consumption.
Overflow, nonzero exit, unknown cleanup, late observation or reader refusal also
refuses it, even if partial output exists. Do not display partial score output.
One bounded reader refusal cannot authorize a second read or repair. Its predicate,
not CLI exit or marker presence, establishes consumability of the complete matrix.

Only after every consumer gate passes may the retained full reader JSON be used
for a descriptive report. Report exact baseline and blueprint chip sums, baseline
minus blueprint delta, and rational mean numerator/denominator=24. Report all
two lineup rows (12 pairs each) and all six seat rows (4 pairs each), regardless
of sign. Do not average already averaged subgroup values or select favorable rows.
Retain all 24 pairs and all 48 trial summaries, including separate baseline fallback
selections/applied, legacy choices, unattributed actions, work-cutoff and deadline
flags, action failures, hand/session causes and capture deficiencies. Preserve null
and prefix meanings from the accepted source contract; missing is never zero.

On any incomplete run or consumer failure, publish only identities, completion
counts, scoped costs and failure causes; aggregate and subgroup scores are unusable.
Raw diagnostics stay retained, including scores already emitted into raw captures.
No survivor-only score, replacement arm, repaired artifact or favorable-sign gate.
This is finite arithmetic about this one matrix; two deals and their rotations do
not provide 24 independent samples, significance, a win-rate estimate, statistical
superiority or playing strength. No confidence interval, policy selection or tuning.
The empty blueprint remains a control, not a trained strategy or a solved-game model.

Retain a local report, exact raw artifact hashes and receipt paths, source/request
pins, observed parent/reader intervals, correctly labeled unit timing prefixes,
file totals and cleanup/failure status. No new peak-memory, peak-disk or action-p95
inference. Resource-pressure interruption keeps unknown values unknown. Complete or
failed, this owner exhausts the lane budget and leads to the explicit checkpoint.

## Design coverage and limits

Protected boundaries are source/adoption/launch identity; fixed unopened request;
whole-matrix ownership; trial/shared deadline; consumer resource/deadline gates;
public publication predicate; failure retention; descriptive denominator and standing.
The ADR and literal request set expectations; raw cost records support calculations;
sealed public source establishes executable semantics. The discretionary margin,
single-lifecycle budget and output cap are prospective policy choices, never claims
that observed maxima prove universal limits. Every boundary has an explicit refusal.

Rejected alternatives: inventing peak memory from launcher RSS; copying the
rehearsal's safety settings as measured ceilings; using source test times as cost
provenance; treating a partial matrix as an aggregate; or adding an instrumented
successor merely to manufacture a full-evaluation profile for this smaller consumer.
If this small operation needs a concrete missing safety limit, refuse and prepare
that bounded work separately. This contract does not waive it or reopen a rehearsal.
The largest uncertainty is new-deal runtime/output. The cheapest falsifier after
adoption is this exact single run; a failure is retained, not tuned away.
'''
save(work/paths[1], contract)
for old_name,new_name in [('run-prereg-snapshot.ps1','run-closure-snapshot.ps1'),
                          ('freeze-prereg.ps1','freeze-closure.ps1')]:
    script = (Path('D:/Pontius/tmp/v0a-paired-prereg-r001')/old_name).read_text()
    script = script.replace('v0a-paired-prereg','v0a-paired-closure').replace(source_base,base)
    script = script.replace('snapshots/paired-prereg/', 'snapshots/paired-closure/')
    script,count = re.subn(r'\$allowed\s*=\s*@\(.*?\)',
        '$allowed = @('+','.join("'"+p+"'" for p in paths)+')',script,count=1,flags=re.S)
    assert count == 1
    save(root/new_name,script)
print(json.dumps(dict(base=base,paths=paths,seed=seed,request_sha256=sha(request_raw),
    request_bytes=len(request_raw),trial_ms=40000,total_ms=2940000,reader_ms=10000,output_cap=4194304)))
