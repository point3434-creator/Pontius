# Representative blueprint workload: design proposal

Date: 2026-09-07. Base: `7242891bc8020d33737c3a027ef88d1b65bb2ace` (ADR-0514).
Status: draft for controller review; no source opening, accepted preregistration,
measurement invocation, decision commit or publication follows from this file.

## Brief

Measure whether prepared blueprints remain useful when tables and visible decision
contexts grow, and how much of the current bot's total cost remains outside lookup.
Balance research throughput and deadline-constrained bot operation. This checkpoint
produces an engineering capacity report and a ranked next optimization, with exact
behavioral compatibility as a prerequisite. It does not measure playing strength.

The future source/protocol round is Tier C because population selection, accounting,
failure retention and result denominators affect evidence meaning. Its protected
invariants are unchanged actions and identity, unchanged clock boundaries, immutable
inputs, and complete reporting of attempted and unattempted work.

Ground truth: the accepted betting kernel, artifact codec, legacy blueprint/provider
and independent host validator; plus literal action/history controls fixed before
measurements. Comparing two providers proves agreement with the reference, not
independent poker correctness. Existing literal controls remain necessary.

Seams: public trajectory to visible key; artifact bytes to owned source; source to
prepared lookup/provider; query stream to timed call; child ledger to host receipt;
raw captures to report; and frozen manifest to one finite measurement invocation.
Only the next capacity claim and resulting optimization choice depend on this pass.
Blueprint-training design and other unrelated research need not wait for it.

Acceptance requires the frozen population to meet its structural coverage, all
measured actions/identities to match their reference, and complete raw accounting.
Favorable speed is not a correctness gate. A slow or resource-limited case is a
result to retain. A correctness mismatch ends comparison and makes later cells
explicitly unattempted; it is never repaired by changing the measured population.

Use one initial proposal and up to two bounded correction rounds, subject to the
workflow's earlier stop for a repeated residual or wrong design. Implementation
size is a planning estimate of 400-700 new tool lines plus focused controls and
registration. It is not an invented line-count acceptance gate. Reconsider the
design before introducing a general benchmark framework or changing runtime policy.

## What current source permits

| Fact at the pinned base | Consequence for this design |
|---|---|
| `tools/v0a_table_session.py` admits blueprint bytes through `OwnedInput(..., 1048576)`. | Full session artifacts must fit the existing 1 MiB boundary. Entry count alone cannot establish that. |
| `HandRuntime._process_hand_started` constructs `PreparedBlueprint`; the session creates a new child connection for every hand. | Amortization in the current bot is per hand. Cross-hand reuse is only a separate hypothetical model. |
| `tools/v0a_evaluation_v3.py` fixes `BLUEPRINT` to the empty fixture. | This evaluator cannot supply the proposed loaded-table comparison unchanged. |
| The legacy `BlueprintProvider` and new `PreparedBlueprintProvider` coexist at this base. | Direct A/B can use identical source, interpreter, observations and artifacts. It need not compare different source generations. |
| Keys include visible cards, complete public betting state and public history. | A one-state private-card sweep cannot represent larger or longer-history tables. |
| The table host preserves its legacy reference computation and source checks. | End-to-end cost includes that validation; removing it would require another integrity design. |

The codec itself does not impose the session's 1 MiB limit. Larger in-process cases
therefore measure the direct Python interface and cannot establish that those same
tables are deployable through the current session interface.

ADR-0514 observed approximately 0.065-0.067 ms per warm prepared provider call on its
1,024-entry, fixed-preflop probe. Its small full-session controls did not establish
an end-to-end speedup. These are motivation and historical context, not this
proposal's expected timings or thresholds. See the accepted
[performance report](../../architecture/v0a-blueprint-preparation-r001/performance-report.md).

## Approach

| Approach | Useful result | Limitation |
|---|---|---|
| Lookup-only expansion | Cheap scaling and memory diagnosis | Omits runtime, setup repetition and transport |
| Full-session-only expansion | Actual pipeline cost | The byte cap restricts table size, and validation/startup can mask lookup work |
| Direct research lane plus current-interface bot lane | Scaling and real boundary costs, with separate denominators | Requires two explicitly named populations |

Select the two-lane approach. Use CPU-only existing dependencies and actual CPython
3.11.15 first, then 3.14.6, with executable identities frozen before invocation.
Use fresh D-local snapshots, snapshot cwd and `PYTHONPATH=<snapshot>/src`, `-B -P`,
the scrubbed environment and absolute native `PONTIUS_GIT` required by CLAUDE.md.
Keep the prepared implementation fixed while collecting this workload. Optimizing
against these opened timings would be a new
development step with a fresh confirmation population.

## Lane A: direct Python research workload

Measure exact table sizes **1,024, 8,192 and 65,536 entries**. These are engineering
scale points, not forecasts of a trained blueprint's eventual size.

Build candidates from reachable public trajectories using the accepted betting
kernel. Traverse all six buttons, two starting-stack profiles (`[200] * 6` and
`[40, 80, 120, 160, 200, 240]`), and two fixed action procedures: passive check/call,
and the accepted host's `min_raise_once` rule applied at every seat.
Record the public state immediately before every legal decision, with its acting
seat as the controlled seat. Stop each trajectory at terminal state; 256 actions
without termination is a structural refusal. Do not synthesize histories by editing
key fields. Short-stack states and short all-ins are retained when this recipe
produces them; this pass does not claim exhaustive all-in coverage.

Use fresh deterministic card seeds derived as SHA-256 of ASCII labels under
`pontius-v0a-workload-r001/research/`, followed by the zero-based trajectory ordinal
as eight decimal digits. Use the accepted dealer's hand index zero. Its board
prefix supplies only the currently visible board. Enumerate unordered private-card
pairs disjoint from that visible board; future board cards and opponent cards are
not part of key construction or query selection.

Deduplicate by complete canonical key bytes. Within each street, order contexts by
trajectory ordinal then action ordinal and interleave their private-card pairs
round-robin. Interleave the four street streams equally, in preflop/flop/turn/river
order, before taking each table prefix. Thus every table has exactly 25% of its
entries from each street. The prefixes are nested. A structural check must also
show all six controlled seats, both stack profiles, both action procedures and at
least one queryable state with 24 or more public actions. Failure to construct that
coverage stops population preparation before any timing; there is no replacement
recipe selected after performance is observed.

Assign legal actions by zero-based ordinal within each street stream modulo four:
passive action, fold, minimum raise, maximum legal raise. This avoids confounding
action kind with the four-street interleaving. If the requested kind is unavailable, use the
passive legal action. Freeze the resulting action-kind census. Fold/check/call/raise
must each have a positive literal control, independently of this recipe.

Freeze two ordered query streams for every size:

- **Spread:** 90% table hits, traversing a deterministic permutation of the whole
  table, and 10% misses from a separately reserved, disjoint complete-key stream.
- **Locality:** 80% requests from 64 fixed hot keys (16 per street), 10% other
  table hits and 10% misses. Keep the hot keys distributed through canonical table
  order so their location does not accidentally favor the legacy linear scan.

Reserve the next 1,024 candidates after the 65,536-entry table as misses. Select
hot keys at indices `floor(j * street_entry_count / 16)`, j = 0 through 15, within
each street's canonically ordered table entries. Use SHA-256 ordering under distinct
`query-order` and `miss-order` labels, with canonical bytes as a tie breaker, for
the hit/miss streams and the slot order in each aligned ten-query segment. Each
such segment has exactly the stated hit/miss counts. Cycle through each ordered
stream on exhaustion. Miss keys are absent from all three tables. Publish query
digests, actual distinct-key counts, action mixes and history-length ranges.
These are intentionally balanced synthetic
engineering workloads; they do not estimate real poker traffic or a learned policy's
hit rate. Small tables necessarily reuse keys in the longer timing stream.

For each size and stream, use five fresh-process blocks. In every block, prepare
the call contexts before timing, perform 20 declared warm-up calls per compared
implementation, then compare the same ordered subset with legacy and prepared
providers. The measured subset sizes per block are 100, 50 and 10 calls for the
three table sizes respectively: **500, 250 and 50 paired calls in total**. Alternate
legacy/prepared order by block. Block b uses the subset starting at query 2,000 * b,
with b zero-based. The smaller large-table reference sample bounds the old
implementation's cost prospectively; its denominator must stay visible.

Then collect 2,000 individual prepared-provider call timings per block, or **10,000
per size/stream/interpreter**. These are a separate series, not the prepared half
of the shorter A/B comparison. Preserve per-call values and block IDs. Report
count, median, p95, p99 and observed maximum for the prepared series, using nearest
rank on sorted individual durations. Report all five block medians as well. For
the shorter paired series report count, total time, mean cost per call, and each
block's time ratio; do not manufacture legacy p99 from 50 observations or pool
different table sizes/interpreters into one speedup.

Constructors, artifact I/O, observation construction, identity verification and
full parity comparison stay outside this warm-call timer and receive separate
measurements. Consume every result and compare its full proposal with the frozen
reference after the timed call. Add small direct `action_for` controls to bind
key/action/hit/digest equality; do not duplicate the whole provider timing matrix.
Leave normal garbage collection enabled and record its configuration. Profiling
and allocation tracing are disabled during all reported timing series.

## Construction, memory and amortization

Use five independent constructions per table size and provider, outside the warm
series. Record file read, strict decode/admission, provider construction, first
proposal and total load-to-first-proposal times as distinct intervals. Measure
observation creation separately and include it in the load-to-first-proposal
definition. Hash/encoding verification after that boundary is an additional cost,
not silently folded into or subtracted from a constituent interval. A fresh
process and fresh object graph do not imply a cold filesystem cache.

Use separate memory workers so tracing cannot inflate the reported timings or
untraced process counters. One cohort records Python-tracked retained and peak
allocations from immediately before artifact read through decoded source plus
owned provider and first proposal. Release intermediates according to the normal
construction path and document what remains alive. A second, untraced cohort
records idle and stage-boundary private commit and working set, plus process-lifetime
peak private commit and peak working set. Include interpreter and harness memory
in those absolute process values. Never sum peaks from different stages or
processes, or label a subtraction of lifetime peaks as exact incremental usage.

Python's allocation tracer covers Python-tracked blocks; the Windows process
counters describe a different resource boundary. The official definitions are in
[Python tracemalloc](https://docs.python.org/3.11/library/tracemalloc.html) and
[PROCESS_MEMORY_COUNTERS_EX](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex).
These measurements establish direct-worker memory, not simultaneous total memory
of the host, adapter and every descendant in a full session.

For each paired query mix, report the model `T(n) = C + n * L`, where `C` is measured
provider construction from an admitted source and `L` is that implementation's
mean on the common paired calls. Show n = 1, 2, 4, 8, 16, 64 and 1,000. Report the
smallest integer n >= 1 for which the prepared model is no slower, or explicitly
report that no finite break-even follows when it does not. Equal call costs and
negative/zero setup differences must be handled explicitly. This model describes
the direct-provider boundary; it does not replace measured runtime setup or turn
all preparation into action-clock credit.
Show the actual number of controlled decisions per bot hand alongside this model;
the 64- and 1,000-call points primarily describe reuse by direct research callers.

## Lane B: current bot interface

Run one-hand sessions through the unchanged public table-session CLI. Use two new
full deals, all six controlled seats, starting button zero, fresh `[200] * 6`
stacks and blinds 1/2. Derive the deals from SHA-256 ASCII labels
`pontius-v0a-workload-r001/bot/00000000` and
`pontius-v0a-workload-r001/bot/00000001`, dealer hand index zero.
Both strategy arms receive the same literal deal and opponent assignment.

Use two lineups: all passive opponents; and, clockwise after the controlled seat,
`min_raise_once, passive, fold_to_bet, shove_once, passive`. Compare both existing
strategies, `blueprint-v1` and `baseline-rules-v1`, with empty and loaded artifacts.
Each one-hand trial resets stacks; no policy-dependent dropout changes the matrix.

The loaded artifact has a **960 KiB (983,040 byte) serialized ceiling**, leaving
64 KiB below the existing session cap. This is a workload choice, not a new product
limit. Its mandatory entries cover every controlled decision in independently
replayed empty-artifact trajectories for both strategies and all 24 deal/seat/lineup
cases, each storing its legal passive fallback. Add the longest deterministic
prefix of Lane A entries that fits the ceiling, excluding duplicate mandatory
keys. Use a fixed source ID and exact encoded size, including JSON overhead and LF.
If mandatory entries alone exceed the ceiling, population qualification fails.
Freeze actual entry count, bytes, digests and reference transcripts before timing.

The passive mandatory actions make table-hit coverage observable while preserving
the corresponding empty-artifact actions and settlements. Compare expected changes
in hit/miss labels explicitly. Blueprint identity/configuration changes caused by
different artifacts are expected, not suppressed. Non-passive action correctness
is exercised by Lane A's literal controls; the bot lane does not claim trained
policy realism.

Use two complete repetition blocks per interpreter:
**2 deals x 6 seats x 2 lineups x 2 artifacts x 2 strategies x 2 blocks = 192
one-hand trials per interpreter, 384 overall.** Block two reverses block one's
frozen case/arm order. Derive the first block's case order with a separately labeled
SHA-256 ordering. This balances ordering effects without claiming independent
random samples of poker traffic. There are no silent retries or extra successful
replacements for failed trials.

Retain session wall time from process launch through verified exit, every action's
existing ledger interval, preparation and post-terminal accounting, failures and
complete raw wire captures. Report counts by street and action position, first
decision versus subsequent decisions, median/p95 and observed maximum action
latency, work-cutoff/deadline events, hands/second, and actions/second. Use nearest
rank for reported percentiles; strata with fewer than 20 observations get counts,
individual values and observed maximum rather than a p95 claim. Label missing
measurements explicitly. Account for startup, host validation and transport in
total session time; the difference from ledger totals is an unattributed residual,
not a fabricated decomposition into those components.

After each interpreter's unprofiled bot matrix, run one separately identified
profile diagnostic: deal zero, controlled seat three, all-passive opponents, loaded
artifact, blueprint-v1. Profile the parent session with the standard-library
profiler, retain its complete output and behavioral checks, and keep its timings
out of all unprofiled summaries. This is two additional one-hand sessions, or
**386 full-hand sessions overall**, of which 384 belong to the timing matrix.
The parent profile cannot establish child self-time, and nested cumulative times
must not be added. It can help distinguish source validation from other parent
work before recommending a targeted optimization.

The 14,000 ms work cutoff, 15,000 ms continuous action wall and preparation-bank
rules remain those of ADR-0307. Show observed remaining margin against each
applicable boundary. A finite maximum or percentile cannot prove worst-case
compliance. The two strategies perform different decisions, so their timing
comparison is descriptive; it is not a semantics-preserving optimization A/B.
Empty versus loaded comparisons likewise measure artifact overhead and hit coverage,
not a new end-to-end speedup over the old runtime.

## Execution bounds and failure meaning

The proposed finite measurement envelope is 60 minutes of payload wall time across
both interpreters, including construction, memory, bot lanes and the two separate
profile diagnostics; snapshot creation
and code review are outside it. No worker starts after expiry. Terminate owned
descendants through the accepted native containment contract on expiry, retain
partial outputs, and report bounded cleanup separately. The existing shorter host
transport/hand bounds continue to apply. This is a run budget, not a claimed
algorithmic latency bound or permission to rerun a consumed invocation. Execute
one worker/trial at a time; complete the 3.11 direct, construction/memory, bot and
profile cells in that order before the same 3.14 sequence. Within a lane, the
source-opening manifest fixes every case and repetition order before execution.

Reject serialized research artifacts above 128 MiB during population qualification.
For direct workers, observe private commit at least every 100 ms and request owned
termination if it exceeds 3 GiB. This is an observed abort threshold, not a strict
allocation ceiling: overshoot and monitoring cost must be reported. Memory-cap or
deadline interruption makes that cell resource-limited and later cells unattempted;
it does not establish that they would fail too. Do not shrink a table or increase
a budget after seeing its result. The full workload receives a fresh identity and
source/parameter/input manifests before its separately authorized invocation.

## Implementation boundary and next decision

Propose additive measurement/planning tools outside `src/pontius`, using the current
session CLI and native containment. This avoids adding a package to the host's
closed package inventory or weakening its source admission. Keep v1/v2/v3 evaluators
and the accepted runtime, host, codec, providers and old evidence byte-for-byte
unchanged. Any necessary test-registration exceptions must be enumerated in the
source-opening proposal before they are edited. Do not clone the evaluator into a
fourth general evaluator just to accept a blueprint argument for this finite pass.

The next deliverable is the exact source-opening/protocol proposal for these two
lanes, with named new tool/test paths, focused correctness controls and acceptance
commands. Qualification freezes the generated population before any performance
payload. Source review and snapshot gates precede a separate finite measurement
authorization; the accepted ADR-0514 controls and consumed owners are not rerun.
This draft itself creates no ADR or active owner.

The final report should choose the next work from observed costs: investigate
repeated preparation if it dominates short hands; compact representation if memory
is the limiting factor; inspect long-history key/observation work if warm calls
grow; or design a separate integrity-preserving validation optimization if the host
dominates total session time. If those costs are comfortably small for this
workload, proceed to the next blueprint/research component. A C/Rust rewrite or a
new training system needs evidence of its own relevant bottleneck.
