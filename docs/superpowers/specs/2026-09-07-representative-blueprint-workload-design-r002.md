# Representative blueprint workload: revised design r002

Base: `7242891bc8020d33737c3a027ef88d1b65bb2ace` (ADR-0514).
Status: prospective design, revised in response to the controller's workload review.
No benchmark has run under this design. It creates no accepted ADR, source opening,
experiment owner, decision commit or remote publication.

The [original design](2026-09-07-representative-blueprint-workload-design.md) remains
unchanged, with SHA-256
`0a9eaa65c6d5b21552846b156e1642e142884b4117973ef66379f7046ca9d1b5`.
Both documents are local files in the C: worktree, not published handoff artifacts.
The [review response](2026-09-07-representative-blueprint-workload-review-response-r002.md)
maps the review to this revision and records the numerical qualifications.

## Brief and priority

Answer four questions in this order: what useful test population fits through the
current artifact interface; what retaining preparation could save; where a full
hand's elapsed time goes; and whether larger research tables violate the predicted
scaling model. Miss latency and key cost versus history support the first question.
Concentrated repeated-key access is removed from this pass.

The target is an engineering decision, not playing-strength evidence. The proposed
source/protocol round is Tier C: source identity, accounting, prototype semantics,
population definition and complete result denominators must survive the benchmark.
Ground truth is the accepted kernel, codecs, legacy lookup/provider and independent
host validation, supplemented by literal controls. Agreement between consumers of
the same kernel is not a new proof of poker correctness.

Only the next capacity claim and optimization choice depend on this work. Training
design and unrelated research can proceed independently. Use one initial source
proposal and at most two bounded corrections, with the workflow's earlier stop for
a repeated residual or wrong design. Estimate 500-900 new tool lines plus focused
controls; this is a planning estimate, not an invented line-count acceptance gate.
Reconsider the design before building a general profiling or evaluation framework.

The changed seams are population recipe to artifact/query manifests, direct table
lifetime to measured cost, observational profiling to exclusive phase totals,
existing ledger records to latency summaries, and retained raw records to decisions.
The production game, strategy, admission and deadline boundaries remain unchanged.

## Existing evidence and predictions

The adopted [performance report](../../architecture/v0a-blueprint-preparation-r001/performance-report.md)
gives these 3.11 measurements at 1,024 entries:

| Boundary | Published median | Interpretation |
|---|---:|---|
| Construct source/keys from existing observations | 11.4711 ms | Synthetic source construction, not runtime admission |
| Construct prepared lookup from an existing source | 24.7091 ms | Closest measured component to hand-start preparation |
| Construct prepared provider from an existing source | 24.4737 ms | Direct provider ownership and setup |
| Warm prepared provider miss | 0.0659 ms | Median batch mean on one fixed preflop context |
| Source plus provider retained allocations | 1,832,951 bytes | Python-tracked graph; excludes interpreter/native memory |

Adding source and lookup medians gives 36.1802 ms; adding source and provider
medians gives 35.9448 ms. Neither sum is a measured complete runtime interval.
The roughly 545 warm-call equivalents of the latter are a work ratio, not the
break-even against the old provider, which also has setup and much slower calls.

Linear component predictions at 8,192/65,536 entries are 0.198/1.581 seconds for
lookup preparation alone, or 0.289/2.316 seconds for source plus lookup. Retained
source-plus-provider memory predicts 14,663,608/117,308,864 bytes. These estimates
assume the old population's composition and cannot be transferred silently to
longer histories. The new scaling checks below test explicitly defined models.

The old three-hand sessions average roughly 1.44-1.51 seconds per hand, including
source checks, startup, game work, transport and cleanup. That total is not a
measured decomposition into fixed overhead. New unprofiled wall measurements and
separate phase diagnostics will establish the relevant boundaries.

## Frozen population recipe

The seeded dealer supplies cards, not betting histories. Use the accepted
`tools/v0a_seeded_deals.py:deal_for_hand` algorithm with hand index zero. Histories
come from real legal transitions, accepted host opponent rules and, where named,
the existing baseline provider. Do not generate arbitrary action strings or edit
history atoms to make a target length. Give policy only its one-seat visible state.

Every seed is SHA-256 of an ASCII domain label followed by an eight-digit zero-based
ordinal. Use `pontius-v0a-workload-r002/table/` for the table corpus and
`pontius-v0a-workload-r002/query/` for the independent query corpus. Artifact IDs,
seed lists, recipe source hashes, case order, full deals, traces, keys and expected
actions must be frozen before the measurement invocation. These identities do not
reuse any earlier workload owner.

Table corpus: exactly 8,192 value-free reference trajectories. For ordinal i, use
button `i % 6`, stack profile `floor(i / 6) % 2`, and opponent rule
`floor(i / 12) % 2`. Stack profiles are `[200] * 6` and
`[40, 80, 120, 160, 200, 240]`; rules are all-passive and all-`min_raise_once`.
Apply the selected rule at every acting seat. Collect every pre-action visible
context using that actor's actual private cards and current board. Store its legal
passive action. The resulting table is deliberately weak and is not trained.

Deduplicate complete canonical keys, retaining the first trajectory/action witness.
Within each street, order by trajectory ordinal then action ordinal; interleave
the four street streams in preflop/flop/turn/river order. This produces nested
1,024-, 8,192- and 65,536-entry tables with equal street counts. Empty and 128-entry
prefixes supply setup/scaling controls. Actual public-history distributions remain
visible; equal street counts do not make these empirical poker traffic.

Query corpus: 16 fresh deals x 6 controlled seats x 2 stack profiles x 3 lineups x
2 strategies = 1,152 value-free reference trajectories. Button is zero. The lineups
are all passive and, clockwise after the controlled seat,
`min_raise_once, passive, fold_to_bet, shove_once, passive`, followed by a third
all-`min_raise_once` lineup. The third lineup supplies longer reachable histories
for the 31-33-atom diagnostic; the bot matrix below uses the first two lineups.
The strategies are blueprint-v1 with an empty table and baseline-rules-v1. Record all controlled
decisions in their original within-hand order. None of these keys is added to the
table to improve its hit rate. Their intersection with the table determines the
observed hit/miss rate for this declared traffic; it does not establish a future
learned policy's rate.

Population qualification is structural and precedes timing. Require all four
streets and six controlled seats, both stack profiles/rules, sufficient unique
entries for the largest table, and legal contexts in each diagnostic history bin:
exactly 0, 3-5, 7-9, 15-17 and 31-33 public actions. Histories outside those bins
remain in the natural traffic report. Stop a trajectory after 256 legal actions
without termination. Missing required coverage is an explicit qualification
refusal, never a reason to search further seeds after seeing performance.

The 8,192 table trajectories and 1,152 query trajectories are offline reference
population construction, separate from the CLI session counts below. Retain their
construction costs, refusals and output sizes as population preparation costs.

## Part 1: interface capacity, misses and history cost

The session's existing byte limit is **1,048,576 bytes**. Use the largest prefix of
the prescribed table whose exact encoded artifact fits that limit, called N_fit.
Require the next prefix to exceed the limit. This is maximum prefix capacity for
this recipe, not maximum capacity over every possible key distribution. Use the
fixed source ID `workload-r002-passive`. Unlike r001, there is no 960 KiB headroom
target and no forced all-hit coverage in the loaded bot artifact.

Report exact wire bytes, internal cached canonical bytes, total per-key canonical
bytes, and retained/peak memory separately. The internal canonical table consists
of key digests and actions; it is not the portable artifact's full key encoding.
Report serialized row bytes by street and history bin: count, mean, median, p95
and maximum. Account separately for root metadata, delimiters and final LF, and
reconcile the row census to the actual encoded byte count. Retained bytes per
entry must never be used as serialized bytes per entry.

The headline requested capacity is **8,192 entries**, a modest engineering target,
not a claim about sufficient blueprint strength. `N_fit < 8192` is a permitted
primary result: the interface cap binds this requested population. Report the
exact retained fraction and the largest admissible first-decision measurements.
At this stage run the five fresh construction and traced/untraced memory
observations for 0 and N_fit, using Part 4's measurement definitions. Freeze the
unique union of requested table sizes so a coincident size shares one declared
control cell instead of causing an undeclared repeat. Part 4 runs the remaining
sizes only. This supplies the N_fit resource and setup evidence before larger
research tables.

For N_fit, report actual hit/miss counts on the full query corpus, preserving
trajectory and action IDs. Headline direct latency is the miss path. Hits remain
separate correctness/cost controls. Do not enforce a fabricated 90% hit rate.

For history diagnostics, choose the first 100 unique eligible misses per bin from
the query corpus and the first 100 hits per bin from table witnesses, in frozen
case order. Reconstruct equal-valued hit query keys as fresh objects, rather than
passing the dictionary's own key object back to it. If fewer than 100 exist, keep
all of them and disclose the count; zero is an uncovered diagnostic, not a zero
latency. Cycle the declared list only for repeated timing blocks. Interleave hit
and miss blocks in an ABBA order to reduce drift; this is a diagnostic schedule,
not the empirical hit-rate population.

Measure five distinct operations on the same contexts: complete key construction,
`hash(key)`, lookup in the actual prepared mapping with a prebuilt query key,
decision-identity calculation, and the full prepared provider call. A mapping
lookup still includes complete-key hashing/equality. Do not describe it as pure constant dictionary overhead or add
these separately timed operations as if they partitioned the provider call. All
five diagnostics run as declared, without an extra operation selected after
observing a slow case.

Use five blocks of 20 warmups, 20 outer-timed batches of 100 calls and 2,000
individually timed calls per operation/bin/hit-or-miss cell on 3.11. This supplies
100 batch means and 10,000 individual observations per complete cell. Batch means
are the primary throughput comparison; individual median/p95/p99/max are empirical
latency diagnostics. Retain per-block values. All result validation/serialization
is outside the measured call/batch, using retained results and frozen reference
values. Record loop/result-retention overhead separately and do not subtract it.

Record `get_clock_info('perf_counter')`, 10,000 empty timer brackets and five empty
100-call batch controls before these measurements. Mark individual results as
instrumentation-sensitive if the empty-bracket median exceeds 5% of that cell's
individual median; keep the observations but use the batch result for decisions.
An unresolved instrumentation-sensitive 1 ms threshold is inconclusive, not a
pass. Normal GC remains enabled; allocation tracing/profiling is off.
Timer definitions: [Python time](https://docs.python.org/3.11/library/time.html).

## Part 2: prepare every hand versus retain preparation

Include a direct-Python cost prototype now in the proposed measurement. Keep the
sealed runtime's construction and process lifetime unchanged. Compare the existing
`PreparedBlueprint` rebuilt for each hand with one retained prepared object, using
the same admitted source, exact query/action stream and no training or new policy.

The retained arm prepares once and, before each hand, hashes its retained canonical
bytes and compares the result with an independently frozen expected source digest.
Both arms validate full action/key/hit/digest parity outside the measured block.
Use N_fit and two query trajectories per each of the 16 query deals: for deal d,
choose seats `d % 6` and `(d + 3) % 6`, 200-chip stacks, lineup `d % 3` and
strategy `d % 2` (blueprint then baseline). Order by deal and seat-choice ordinal.
This supplies 32 different hand/seat contexts; report actual distinct query keys.
These are frozen fallback-query sequences, not a new live replay driven by returned
actions. Measure fresh process groups of H = 1, 2, 8 and 32 hands, with four paired
repetitions ordered fresh/retained, retained/fresh, retained/fresh, fresh/retained.
Charge the retained arm's initial construction in every group; report
per-hand hash time, complete group time, actual controlled-decision counts, memory
and per-hand savings. Reading/decoding the source is common setup reported outside
both groups, not a cost claimed to disappear.

This arm asks what removing repeated preparation could save under persistent
ownership. Hashing cached bytes does not establish freshness of an external file,
reconstruct the current live index, or prove index-to-byte agreement. The accepted
ownership boundary protects caller/result aliases and explicitly does not treat
private reflection as a security boundary. Do not invent a stronger threat model,
but do not promote a cached-byte check into a replacement for source admission.

Retain ordinary parity and caller/result-isolation controls and a cached-byte
digest mismatch refusal. A later deployment design must specify table ownership,
source replacement/invalidation, accounting and worker lifetime. The present
session starts a fresh child each hand, so this prototype does not directly save
its process-launch costs and is not a runtime adoption candidate.

Report both the complete H-hand observations and a labeled amortization model.
Never call setup divided by a warm call cost the old-versus-new break-even.

## Part 3: process costs and authoritative action accounting

The primary full-session deliverable is a decomposition of elapsed time, with
behavioral coverage and pooled individual-action timings alongside it.

3.11 unprofiled matrix: the first 2 query deals x 6 controlled seats x the first
2 lineups x 2 artifacts (empty/N_fit) x 2 strategies = **96 one-hand trials**. Use 200-chip
stacks, blinds 1/2 and button zero, resetting stacks every trial. Loaded entries
store passive actions, so expected actions/settlements match the corresponding
empty arm; hit labels and artifact/config identities may differ. Freeze full
reference transcripts, including the natural hit/miss labels, before timing.

Add **12 diagnostic counterparts**: query deal zero, controlled seats 0/2/3,
all-passive lineup, both artifacts and both strategies. Counterbalance the order
of instrumented and corresponding uninstrumented cases by frozen ordinal. These
diagnostics replace the previous two incidental profiles; their timing stays out
of unprofiled summaries.

Use an observational call/return profiler in the parent main thread, without
replacing production functions or changing the child command. Capture wall spans
for these fixed entry points, with every selected span assigned to its most deeply
nested active category:

| Category | Existing entry points |
|---|---|
| Parent setup/admission | `Session.prepare`, session/host `Admission`/`Source` initialization |
| Repeated source/input validation | `Session.validate`, `Admission.check`, `Source.check`, `OwnedInput.check` |
| Native launch/containment | `ChildConnection.__init__` |
| Child ready handshake | `WireConsumer.ready` |
| Host reference policy/decision validation | `WireConsumer.provider_expected`, `decision`, `settlement` |
| Exchange/transport and child wait | `WireConsumer.exchange`, `ChildConnection.send`, `receive`, excluding nested named work |
| Game/session progression | `Schedule.derive`, `Table.start_event`, `next_event`, remaining `Session.play_hand` |
| Completion/cleanup | `WireConsumer.complete`, `ChildConnection.finish` |

Remaining `Session.run` work and anything outside these spans are separately
reported orchestration/residual time. Initialization takes precedence over the
repeated-check category while inside an admission
constructor. Pin the exact filenames/qualified function names to the base in the
source-opening manifest. Record raw span events, counts and closure status. Missing
or unclosed spans invalidate attribution; they are not assigned a guessed duration.

These are exclusive elapsed phases of the parent's critical path, not CPU self-time
across all threads. Child computation overlaps parent waiting; present the child's
ledger as a separate view and never sum it into the parent's phases. The ready
phase includes child startup/admission waiting, not just OS process creation.
Profile overhead remains visible: compare every diagnostic with its matching
unprofiled case. An inflation above 25% marks its quantitative phase shares as
perturbed and ineligible for the dominance rule below. Thread/context-switch limits
of profiling are documented in [Python sys](https://docs.python.org/3.11/library/sys.html#sys.setprofile).

For unprofiled trials, retain launch-to-verified-exit wall time and raw existing
ledger records. Pool individual action durations by interpreter, strategy, artifact,
hit/miss and first/later decision; retain trial, street and history IDs. Report the
actual naturally weighted all-action distribution as well as strata. Do not pool
the two interpreters or interpret correlated actions as independent statistical
replications. Use nearest-rank percentiles, with p95 only for n >= 20 and p99 only
for n >= 1,000; otherwise show raw observations/count/maximum. One observation per
matrix cell supplies coverage, not a per-cell latency distribution.

For seat 3 with button zero, the hand-start transition immediately starts the
controlled action: preparation is inside that first response's authoritative
`timing.elapsed_ns`. For other seats it is charged as preparation, not added again
to a later action's response wall. The existing controlled-clock test explicitly
distinguishes seats 0 and 3. Report first-response elapsed, response compute and
uninstrumented portions, complete preparation totals, first-action event identity,
cutoff/deadline flags and missing/failed measurements. Keep aggregate preparation
totals at their original scope; do not relabel a whole-session preparation total
as hand-start-only.

The **14,000 ms work cutoff and 15,000 ms continuous action wall** stay authoritative.
Report exact observed margins, especially first-to-act at N_fit. Do not add ledger
components twice, grant a new preparation-bank credit, or claim a finite maximum
proves a worst-case wall guarantee.

## Part 4: research scaling and memory, lowest priority

Run the larger research table controls only after the cap, miss/history, reuse and
full-session measurements on 3.11. The complete size set is
0/128/1,024/8,192/65,536 plus N_fit; reuse Part 1's 0/N_fit control records and run
the remaining unique sizes here. Take five fresh observations of decode/admission, preparation, canonical serialization,
hashing of retained canonical bytes and first full provider call. Publish every
component boundary; independent diagnostic times are not an additive partition of
preparation. Include artifact read and load-to-first-proposal totals separately.
Fresh processes/objects do not establish a cold filesystem cache.

For 1,024/8,192/65,536 entries, compare legacy and prepared full-provider calls on
the same spread-out contexts: five blocks of 20/10/2 hits and the same number of
misses, respectively, interleaved and preceded by 20 declared warmups per block.
Do not repeat the full history microbenchmark or concentrated-reuse experiment at
these sizes. Publish the shrinking reference denominators; no legacy tail claims.

Use separate traced/untraced memory workers, five fresh observations per size, to
record source plus prepared provider with raw artifact buffer and first observation
ownership explicitly listed. Tracemalloc retained/peak allocations and process
private commit/working set are different boundaries. Report untraced process idle,
stage values and lifetime peaks. Never subtract lifetime peaks as an exact memory
increment, add peaks from different processes, or claim simultaneous full-session
RAM from a single direct worker. See [tracemalloc](https://docs.python.org/3.11/library/tracemalloc.html)
and [Windows counters](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex).

Preregister the scaling check. For each construction component, let T0 and T1024
be its medians at 0 and 1,024 entries. Let W_N be that component's byte-work proxy,
after subtracting its empty-table bytes: wire bytes for decode; total canonical key
bytes plus internal canonical table bytes for preparation/canonical serialization;
and internal canonical table bytes alone for hashing retained bytes. Predict
`T_linear(N) = T0 + (T1024 - T0) * W_N / W_1024`.
Do not refit this prediction after opening 8,192 or 65,536 results. Also show the
sorting proxy with the incremental term multiplied by `log2(N) / log2(1024)`.
Sorting by per-key digest can introduce N log N work; the proxy is not a proof
of what dominates preparation.

Report `R = (T_N - T0) / (T_linear(N) - T0)`. R <= 1.25 is no material excess
over this linear model; R > 1.25 is a superlinear flag relative to modeled bytes.
For preparation/canonical serialization, if R also exceeds
`1.25 * log2(N) / log2(1024)`, flag excess beyond the declared
sorting proxy. Faster results remain visible. A nonpositive baseline increment
or a five-observation range greater than 30% of its median makes that component's
classification inconclusive. Do not request extra sizes or samples to clear it.
Apply the same empty-adjusted ratio to retained allocations using the preparation
byte proxy, and show raw bytes/entry and history composition alongside it. For
components without sorting, the sorting proxy is descriptive only; it does not
excuse a superlinear hash/decode result.

## Prospective decision rules

These numbers are proposed engineering priorities fixed before this run, not new
product limits, universal performance standards or retrospective acceptance gates.
Report every triggered rule and its measurements. Correctness, missing evidence
and budget failures outrank speed. Within eligible performance results, priority
is response safety, cap, attributed session cost, reuse, key cost, then scaling.

| Question | Fixed trigger | Consequence |
|---|---|---|
| Response margin | Any first-to-act N_fit response >= 1,400 ms (10% of work cutoff), or any work-cutoff/deadline event | Investigate startup/preparation/response accounting before expanding deployment capacity; report actual contract failure separately |
| Interface cap | N_fit < 8,192 | Report that the cap binds the requested corpus; scope an artifact/lifecycle capacity design before claiming 8,192-entry deployment |
| Dominant session phase | Eligible exclusive phase >= 50% of profiled session wall AND >= 100 ms, in at least two diagnostic cases | Name that phase as a target for a separate source-opening investigation; phase shares remain diagnostic, not exact unprofiled CPU attribution |
| Useful preparation reuse | At H=8 and N_fit, median per-hand saving >= 10 ms AND >= 20% of the fresh direct group's per-hand time, with all four paired savings positive | Justify a persistent-ownership research design; do not automatically adopt cached hashing or claim the same end-to-end saving |
| Material miss path | History-bin full-provider miss p95 >= 1 ms, with eligible instrumentation | Investigate this bin; if separately measured key-construction median is >= 50% of provider median, prioritize key construction as a diagnostic lead |
| Excess scaling | Construction or retained-allocation R > 1.25; mark additional sorting-proxy excess as specified above | Name the exceeded model and relevant bytes/history counts; no automatic native rewrite or additional size search |
| Current process resource concern | N_fit untraced direct-worker peak private commit >= 512 MiB | Investigate process representation/ownership before a capacity expansion |

The key/provider ratio is a separately timed diagnostic comparison, not an exclusive
percentage of a call. If none of the timing/resource rules triggers, retain the
cap result and proceed with the next research component rather than further lookup
optimization. A missing relevant measurement yields an unresolved decision, not
permission to choose whichever branch seems plausible afterward.

## Interpreter subset, execution bounds and next checkpoint

Run the full performance design on actual CPython 3.11.15 first. The confirming
3.14.6 subset is fixed: N_fit history bins 0 and 31-33 with the same five-block
schedule; N_fit H=1/H=8 reuse groups; 0/N_fit/8,192 construction and memory controls;
and query deal zero x seats 0/3 x passive lineup x two artifacts x two strategies
= **8 unprofiled one-hand trials**, plus their four loaded-artifact diagnostic
counterparts. Total CLI sessions: **104 unprofiled plus 16 diagnostics = 120**.
No 65,536-entry or full traffic-matrix doubling on 3.14. Source correctness and
release gates still run their prescribed populations on both supported versions.

Keep the 60-minute measured-payload envelope across both versions; offline population
qualification and snapshot/review preparation are separate bounded stages. Use
fresh D-local snapshots, snapshot cwd/PYTHONPATH, `-B -P`, scrubbed environment and
absolute native PONTIUS_GIT. Freeze interpreter identities and every invocation,
capture limit and order in the source-opening protocol before execution. Run one
worker at a time. Complete the four 3.11 parts in order, then the fixed 3.14 subset.

Research artifacts above 128 MiB refuse qualification. Observe direct-worker private
commit at least every 100 ms; over 3 GiB requests owned termination. This is an
observed threshold with possible overshoot, not a hard allocation guarantee. Keep
existing shorter host bounds. On budget/resource interruption, stop admission,
terminate owned descendants through real native containment, retain partial data
and mark later cells unattempted. Report cleanup separately. No retries, enlarged
budgets, replacement successes or dropped failed denominators follow from a result.

Implement later as additive planning/measurement tools outside `src/pontius`, with
named new controls and exact prospective registration exceptions. The sealed
runtime, host, session, providers, codecs and evaluators remain byte-identical.
Prototype or profiler output does not confer production authority. The next
checkpoint is the exact source-opening/protocol proposal, source review and gates,
then separate authorization of the frozen finite measurement. No old owner or
ADR-0514 measurement command is invoked by this revision.
