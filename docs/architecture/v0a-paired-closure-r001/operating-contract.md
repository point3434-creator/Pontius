# Single measured descriptive paired comparison

Normative only upon ADR-0511's exact adoption. One subsequent exact launch approval
is required. This closes the ADR-0510 planning target without altering its lineups,
strategies, population size or forbidden claims after any poker outcome.

## Frozen source, request and schedule

Execution source is bd71f4b11dcc0177283431a4ec468fdc152e7686, tree
54a257f4f2957696b9d33e7338ce140206a3f578. Use a fresh D-local --no-hardlinks
detached clone with core.autocrlf=false, no overlay, and complete tracked raw-blob
verification before launch and again before artifact consumption. Preserve the
source snapshot. ADR-0509's source acceptance is inherited, not rerun or relabeled.
The wrapper/contract and all source pins in ADR-0510 remain unchanged.

The exact companion request has 351 canonical ASCII/LF bytes; SHA256:
d772691d85a903b4ac6e734b9aa4eac4f75e6ae0096def7c3c0481807729017e.
Its fresh seed is
9916a26666b26d44a65dd7f6542b34729b33b24421f38cd05544955143eae942.
Derive it once as SHA256 of these ASCII bytes: the line
pontius-paired-evaluation-001, LF, dfd5a5c6a9d8aae6cbbae667f9b0716c59362eed, LF.
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
PONTIUS_GIT=C:\Program Files\Git\cmd\git.exe. Retain only SystemRoot, WINDIR,
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
assert result['source_commit'] == 'bd71f4b11dcc0177283431a4ec468fdc152e7686'
assert result['request_sha256'] == (
    'd772691d85a903b4ac6e734b9aa4eac4f75e6ae0096def7c3c0481807729017e')
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
