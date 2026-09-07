# First paired evaluation: rehearsal and subsequent closure

This contract becomes normative only with ADR-0510's exact adoption. No launch
authority exists until the single rehearsal is explicitly authorized. Source base
is bd71f4b11dcc0177283431a4ec468fdc152e7686; no source change is requested.

## Purpose and dependency

Obtain bounded cost provenance for the first descriptive paired comparison while
keeping all rehearsal poker outcomes unusable for claims or selection. Ground truth
for execution is the unchanged public wrapper/session/source contract. Ground truth
for measurements is retained native parent observations, raw unit records and actual
closed-file sizes, with each interval's limits disclosed. Source correctness remains
established by ADR-0509's independent reviews and accepted tests, not this rehearsal.

Only the first actual paired comparison's operating closure waits on this report.
No H32, training, resolver, analyzer or historical experiment dependency is introduced.
Preparation is a four-path Tier C documentation increment. It needs two independent
cold reviews and four status gates; it does not spend another poker correctness suite.

## Selected shape and alternatives

Use one synthetic deal and two five-opponent scripts across all six controlled seats,
with both accepted strategies. Lineup 0 is passive in every opponent position;
lineup 1 is fold_to_bet/min_raise_once/passive/shove_once/passive in clockwise order.
The latter exercises all four existing script kinds without a new opponent model.
This makes 12 pairs and 24 sessions. The zero seed is a disclosed reused synthetic
vector, not a hidden evaluation panel. Fix all choices before any rehearsal outcome.

Rejected alternatives: treating the source tests as an operational rehearsal would
change their authorized standing; inventing a runtime limit from intuition would
violate measure-before-freeze; immediately using the maximum four-deal/four-lineup
matrix would spend extra preparatory work without addressing the missing provenance.
No strategy, table, source or opponent is selected by observed chip outcomes.

The intended evaluation shape is two fresh deals x these same two lineups x six
positions x two arms = 48 trials, a twofold expansion of this rehearsal. A later
append-only closure must identify the real measurement records, freeze a fresh seed
and canonical request, supply justified operating limits and the lane budget, and
name any still-missing resource/ownership gates. This planning shape carries no
execution authority and is not represented as a measured population bound today.
Do not silently thin it or change lineups after opening values. No final cards are
generated or previewed while preparing or conducting this rehearsal.

## Invariants and coverage map

| Boundary | Fixed requirement | Observation or retained evidence |
| --- | --- | --- |
| Proposal | Four paths only; source tree unchanged | Raw Git tree/manifest and source pins |
| Reservation | New disjoint run root, no retry | Preflight absence and exclusive intent |
| Source | Exact sealed commit, clean raw blobs | Detached clone plus full tracked comparison |
| Input | 352 canonical bytes, fixed zero seed/two lineups | Raw request hash from ADR-0510 |
| Planning | 12 ordered pairs, 24 units, six seat rotations | Public saved plan and pair input hashes |
| Policy | baseline-rules-v1/blueprint-v1; empty blueprint | Unchanged argv and public admitted records |
| Measurement | Scoped real elapsed/byte observations | Parent interval, unit prefixes, file inventory |
| Publication | Stable bound files and absent guard | Unchanged read_completed after process exit |
| Failure | Stop once, later units unstarted; retain all | Raw intents, captures, states and causes |
| Standing | Costs only; no scores enter decisions | Cost-only report and later closure review |

No exact payout, winner, action count, runtime, peak memory or complete-output size is
predicted. Randomness quality, all OS failure schedules and worst-case scaling are
outside this finite coverage claim. Unobserved branches remain unobserved.

## Measurement contract

The supervisor records the interpreter and native Git file identities, source commit,
request hash, full command and scrubbed environment before the one launch. It records
monotonic times in integer nanoseconds immediately before Popen and after wait returns,
with UTC wall-clock timestamps only as correlation metadata. The interval includes
parent-observed source admission through CLI return; it is not an action-clock metric.
Do not subtract child timing from it to claim disjoint attribution not actually observed.

After termination, invoke the unchanged public read_completed exactly once from the
same pinned source in an isolated reader process, with -B -P and the same environment
discipline. Load only the exact wrapper file through the standard documented local
module-loading mechanism; call the public reader, never execute/main or a private
publication helper. Record reader identity, argv, timing, exit and bounded diagnostics.
It may emit only success/refusal and source/request/plan identities plus completion
counts. It must not emit private cards, net chips, deltas or strategy rankings. This
is structural consumption of a rehearsal artifact, not a second comparison or test.
The reader argv is -B, -P, -c, followed by this entire literal Python program as one
argument, from the same source cwd. It executes no main, dealer or poker function:

```python
import json, runpy
from pathlib import Path
module = runpy.run_path('tools/v0a_evaluation.py', run_name='paired_rehearsal_reader')
result = module['read_completed'](
    Path('D:/Pontius/tmp/v0a-paired-rehearsal-run-001/output'))
assert result['source_commit'] == 'bd71f4b11dcc0177283431a4ec468fdc152e7686'
assert result['request_sha256'] == (
    '67af9c6fb677af40937c7640e391bdabcf7f0c27a0a261ac9efdbbf98ddf8359')
fields = ('source_commit', 'request_sha256', 'plan_sha256', 'planned_pairs',
          'completed_pairs', 'planned_trials', 'completed_trials')
print(json.dumps({key: result[key] for key in fields}, sort_keys=True))
```

The external reader uses the exact raw-verified source, and its name/purpose grant
no source exemption or execution authority beyond this one public artifact read.

For each unit whose retained result.json exists, record ordinal, strategy, state,
elapsed_ns, capture byte lengths, cleanup state and record hash. That elapsed_ns is
a prefix ending before that result file's publication; report it as such. Do not use
it as full per-trial wall or final publication time. Wrapper total_elapsed_ns also
precedes final publication and is diagnostic only. Parent whole-run and reader
durations remain separate. Missing records/unknown launch are null, not zero.

Record counts and sums of regular-file bytes under output/ after termination, plus
the maximum stdout/stderr capture lengths and hashes. Do not follow links or change
files. Separate source-checkout bytes and supervisor diagnostics from output storage.
This is retained post-run storage, not peak disk occupancy. No process-tree memory,
GPU memory, p95 action latency or hard resident limit is inferred from these data.
If later operation needs those measurements, their absence remains an explicit gate.

The report preserves complete, refused, failed, interrupted and unknown outcomes,
and all raw artifact locations. The per-unit cost maximum and whole-run duration are
finite observations for this source/host/request only. A later scaling calculation
must show its multiplier, margin and unsupported assumptions, including new-deal
behavior and publication work. It cannot claim a mathematical worst-case bound or
silently turn these observations into a strategy-quality gate. No operating budget
or permission follows automatically from a complete rehearsal.

## Ownership, supervision and stops

The sole root is D:/Pontius/tmp/v0a-paired-rehearsal-run-001, reserved only after exact
adoption/launch approval. The one wrapper evaluation ID is
pontius-v0a-evaluation-v1-correctness-rehearsal-001; the suffix rehearsal-001 produces
the standard public v1/v2 session IDs ending eval-rehearsal-001-u001 through -u024.
The unchanged host/event children derive their usual IDs; no historical ID is reused.
source/, request.json, process-temp/ and output/ are siblings as specified in the ADR.

The operator remains present, relays progress without exposing poker outcomes, and
stops on lost supervision, capture overflow, source/request drift, resource pressure,
interruption or a stuck process. Use the existing native containment and external
process-tree stop facilities; any ambiguous cleanup is incomplete, never repaired
into success. Do not stop early because a strategy appears ahead or behind. The
request's 150-minute internal safety allowance is not an unattended-work permission
or a guarantee that a blocked OS operation returns by that time.

Only source/metadata identity checks, the one named wrapper launch, one public reader
and read-only cost extraction are within the future single launch authorization.
No test, warm-up, additional seed, second interpreter, second wrapper invocation,
resumption, alteration or root deletion is allowed. Proposal acceptance executes only
the four metadata gates. No run-root creation or dealer call occurs in preparation.

One bootstrap attempt ends at its report. An infrastructure death is retained and
diagnosed; a second consecutive owner death in the lane triggers the existing
stand-down. There is no automatically authorized successor. Source fixes require
new source review/seal; authority expansion or exhausted proposal corrections require
a controller ruling. All costs and failures remain inspectable; no favorable run is
substituted for this one. The result can support only a later measured closure.
