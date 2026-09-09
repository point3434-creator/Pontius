# Blueprint representation and runtime cost

[Results index](RESULTS.md) · Updated 2026-09-08 · Local engineering evidence

**Current conclusion:** prepared decisions are inexpensive in the tested cases.
The immediate opportunities are avoiding repeated preparation across hands and
reducing the space occupied by full-history keys. The benchmark harness now runs
multiple cells in one worker, so those questions are practical to investigate.
The Python 3.14 coverage batch completed 48/48 one-hand sessions in 29.189 s.
A subsequent controlled-hit experiment completed 12 sessions / 144 hands in
68.407 s, covering 8- and 16-hand sessions with 384 hits and 192 control misses.
Preparation dominates charged hand work for the near-cap artifacts. A subsequent
active-action batch completed 48 one-hand sessions in 20.674 s, exercising bets,
re-raises, folds, all-in calls, side pots, refunds and intentional fallback with a
64-entry diagnostic table. Reliable tails, stability beyond sixteen hands,
near-cap non-passive actions and poker strength remain unestablished.

This page consolidates the blueprint cost findings. It covers artifact capacity,
provider preparation, and the harness that measures them. Solver quality and GPU
experiments belong to other families. Detailed reports and raw runs remain
available through the evidence links below.

**Reading the numbers:** an artifact is the serialized blueprint table;
preparation builds the provider used for decisions; a cell is one configured
benchmark case. A warm call uses an already prepared provider. Milliseconds
(`ms`) measure operations; seconds (`s`) usually measure workers or whole runs.

## What we know

The [trained river pilot](bot-validation.md#trained-river-policy-integration-passed-projection-rejected)
also establishes a representation constraint on strategy quality: the current
single-action table cannot retain the teacher's mixed actions. Argmax export
raised NashConv from 0.000686 to 2 chips despite passing 100 direct-runtime
replays. The [weighted follow-up](bot-validation.md#weighted-river-policy-quality-preserved-in-the-research-prototype)
retained NashConv of 0.000687 and passed 772 sampled-table cases plus 48 replays
in 12.408 seconds. The subsequent
[native implementation](bot-validation.md#native-weighted-artifact-and-subprocess-sessions)
passed 100 direct hands and 36 subprocess sessions in 16.851 seconds. Its full-key
artifact is 11,617 bytes / 13 entries; maximum session response was 0.7345 ms and
maximum charged hand compute, including preparation and sampling, was 2.7718 ms.
File decoding and startup remain outside the hand ledger. These are tiny-table
observations, not tail or near-cap bounds. More capacity or faster lookup alone
would not recover the mixture discarded by argmax.

The subsequent [six-board panel](bot-validation.md#six-board-panel-export-passes-coverage-and-priors-remain-limiting)
passed 576 direct hands and 48 subprocess sessions in 37.739 seconds. A shared
55-entry / 48,097-byte table retained four trained policies; maximum observed
session response was 0.8099 ms and maximum charged hand compute was 6.1544 ms.
Two uncovered boards used passive fallback, and changed priors damaged some
covered strategies despite unchanged keys. These observations prioritize coverage
and range modeling for this small panel. They do not remove the separately
measured near-cap preparation or history-key capacity concerns.

The [coverage/robustness comparison](bot-validation.md#coverage-and-robustness-candidates-both-rejected)
subsequently completed 768 direct hands and 96 subprocess sessions in 65.649
seconds. Maximum session response was 0.7477 ms and maximum charged hand compute
5.7355 ms for 12–36-entry artifacts. Both candidate policy methods failed their
quality gates despite correct, inexpensive execution. Feature calculation and
materialization were offline; these clocks do not price a general live fallback.

| Question | Measured finding | What it means and where it stops |
|---|---|---|
| Are prepared decisions fast? | On the fixed 1,024-entry preflop table, the Python 3.11 prepared provider's miss cost was **0.0659 ms**, versus **6.6080 ms** previously: median batch means from five batches of 20 calls. [Preparation report](../docs/architecture/v0a-blueprint-preparation-r001/performance-report.md) | The tested warm miss path improved substantially. Empty-table misses were slightly slower after preparation. These are not individual-call percentiles or realistic history-tail measurements. |
| What does preparation cost? | The same preflop workload measured **11.4711 ms source construction** and **24.4737 ms prepared-provider setup**, each a median of five observations. Retained source plus provider allocation was **1,832,951 bytes**. [Preparation report](../docs/architecture/v0a-blueprint-preparation-r001/performance-report.md) | The earlier approximately 36 ms estimate combined two stages. It was not preparation alone. Allocation was measured with `tracemalloc`; it is not artifact size or whole-process memory. |
| How much fits through the interface? | In the seeded history-rich corpus, **883 entries occupied 1,047,220 bytes**; 884 occupied 1,048,609 bytes, exceeding the **1,048,576-byte (1 MiB)** limit. Keys occupied **95.7%** of the fitting artifact. [Original findings](D:/Pontius-handoffs/v0a-blueprint-workload-as-is/r001/findings.json) | Representation binds for this corpus. **883 is not a universal entry limit**: key histories and serialization determine capacity. |
| Does the history-rich artifact cost more to load? | At 883 entries, median decode/validation was **142.692 ms**, preparation **78.214 ms**, and the first direct prepared decision **0.1555 ms**; three observations each. [Original findings](D:/Pontius-handoffs/v0a-blueprint-workload-as-is/r001/findings.json) | These are different keys and a different workload from the 1,024-entry preflop case. Do not infer a regression from entry count alone. Three samples support descriptive costs, not variance or tails. |
| Is harness startup still the main obstacle? | The old worker reached ready after a median **98.570 s** over 18 observations. The revised three-cell check reached ready in **0.406 s once**, completing in **2.063 s total**, including **0.371 s** of source verification. [New construction run](results/runs/5d1744d5bc9140f19faceada52e8b62b/result.json) | The startup obstruction is removed in this focused check. The historical runs differ in source and execution design; this is not a controlled general throughput ratio. |
| Does preparation reuse help? | Across eight hands, fresh preparation each hand took **670.038 ms**, versus **81.151 ms** for one preparation with per-hand retained-digest checks: four observations per arm. [Reuse run](results/runs/b7e55f19f6434ece899d58e2f98fd3cf/result.json) | About **8.3×** faster for this direct Python group. This is a prototype result; the live runtime still prepares at hand start. See the timing boundary below. |

All headline timings above are local Windows / CPython 3.11.15 observations.
The preparation report also contains Python 3.14.6 measurements. Passing tests on
3.14 does not substitute for repeating the newer performance workload there.

The capacity corpus also explains why entry count alone is misleading:

| Street | Entries sampled | Median serialized row bytes |
|---|---:|---:|
| Preflop | 221 | 661 |
| Flop | 221 | 1,002 |
| Turn | 221 | 1,410 |
| River | 220 | 1,813.5 |

These are complete row sizes, not key-only sizes. Later rows carry longer public
histories. The table is descriptive of this corpus, not a universal growth law.

## What the reuse result actually measures

Both arms start with a decoded source and replayed observations. The clock covers
provider preparation and proposals across the selected hands. The retained arm
also hashes its owned canonical bytes before each hand. It excludes file reads,
artifact decoding, workload replay, parity checks after the measured group, and
session transport. It does not test whether mutations to the original loaded
source are detected by a future live implementation.

| Hands per group | Fresh preparation each hand, median ms | Prepare once + digest checks, median ms | Completed observations per arm |
|---|---:|---:|---:|
| 1 | 80.682 | 72.750 | 4 |
| 2 | 157.946 | 87.766 | 4 |
| 8 | 670.038 | 81.151 | 4 |
| 32 | 2,445.747 | 91.046 | 3 |

The run completed **30 of 32 cells** at its 60-second limit. The next cell was
interrupted and one was unattempted; completed observations were retained and
job cleanup was confirmed. The one-hand difference is not evidence that digest
checking makes preparation faster. The group medians are descriptive and do not
establish confidence intervals or worst-case latency.

## What changed, and what remains open

**Active blueprint actions:** the
[dated experiment](2026-09-08-blueprint-active-sessions.py) completed **48/48
one-hand sessions in 20.674 s** on Python 3.14.6. Six scenarios, two controlled
seats (0 and 3), and two fixed deals per scenario/seat formed 24 matched
empty-table/diagnostic-table pairs. The existing opponent policies supplied
minimum raises, shoves, calls and folds. Each pair starts from the same deal and
stacks; its arms are expected to diverge when the diagnostic action differs.

The [result](results/runs/2f4137c9684040109153814e39135d14/result.json) and
[retained design](results/runs/2f4137c9684040109153814e39135d14/inputs/design.json)
contain inputs, expected trajectories, coverage requirements, ledgers and timing
arrays. The production source was verified against
`b378104cd2934f248a9545d7d482b0db25db813c`. The experiment's SHA-256 is
`d489c5f77bf4902b2d5a7dd9dd1f5a90d0ddd8e1e958b0805d51a8c8e805a136`;
its exact source is also retained as `experiment.py` beside the result.

| Arm | Entries / bytes | Decisions | Hits / misses | Median response compute | Median charged hand compute | Maximum response wall interval |
|---|---:|---:|---:|---:|---:|---:|
| Empty control | 0 / 101 | 124 | 0 / 124 | 0.1507 ms | 3.27685 ms | 0.9076 ms |
| Diagnostic | 64 / 67,647 | 84 | 64 / 20 | 0.16565 ms | 7.88510 ms | 5.5847 ms |

All 48 action trajectories, final stacks and payouts matched their predictions;
20/24 pairs changed trajectory as intended. The four call-shove controls use
the same passive action but exercise table hits. Diagnostic coverage comprised
18 opening bets, 30 raises into an existing bet (including 20 re-raises), four
folds, four all-in raises, two all-in calls and 20 misses after an earlier hit.
Six diagnostic hands exercised side pots and four exercised uncalled refunds.
These coverage categories overlap. All response statuses and accounting checks
passed; no work cutoff or deadline crossing occurred. Worker readiness was
0.341 s, setup was 0.428 s, cumulative worker-job peak memory was 1,538.85 MiB,
and cleanup was verified.

The payout reference awards contribution tiers separately from the engine's
settlement methods. Betting transitions and hand ranking still share the
existing library, so this is not a differential against a wholly independent
poker engine. The table is deliberately constructed for the test states. It is
untrained, has no demonstrated out-of-sample coverage, and supports no strength
or tail-latency claim. Its smaller table and different trajectories prevent
interpreting its timings as a speedup over the near-cap passive batch.

The [first attempt](results/runs/b3b227c5dc144e81adbd04f7e1a518bb/result.json)
stopped in 2.023 s with zero sessions executed: the experiment requested a
seeded-deal index above the helper's 0–15 range. The corrected experiment uses
two deterministically derived seed blocks. Both attempts, including their exact
drivers and generated inputs, are retained locally; they are not yet committed.
No production code changed.

**Controlled hits and multi-hand sessions:** the
[dated experiment](2026-09-08-blueprint-hit-sessions.py) ran 2 controlled seats
(0 and 3) x 2 session lengths (8 and 16) x 3 artifacts, with all opponents passive.
It generated one deterministic sixteen-deal schedule; eight-hand sessions use
its prefix. Button rotation and carried stacks follow the existing session rules.
Actor-visible keys were built along those passive trajectories, with table actions
equal to the fallback actions. This deliberately covers known states to measure
the hit path; it is not training or independent policy-quality evaluation.

All **12/12 sessions, 144/144 hands and 576 decisions completed in 68.407 s**
within the 180 s budget, on Python 3.14.6. The verified production source is
`b378104cd2934f248a9545d7d482b0db25db813c`; the separately recorded experimental
driver SHA-256 is `271c94fe6c5dfe6babcde0ffecea3612b33dc0d2cef5dfc1437f3d1daf820c69`.
The experiment file is outside the production source-verification scope.
The [result](results/runs/2efd6266a9b944f3b85a9ca31de99b45/result.json) retains
generated design, seed, input hashes, predicted trajectories, raw session ledgers,
assessment and per-hand timing arrays. Generated artifacts and sessions remain
beside it under `inputs/`; runtime/clock/driver identities are in
[runtimes.json](results/runs/2efd6266a9b944f3b85a9ca31de99b45/runtimes.json).

| Arm | Entries / serialized bytes | Hands | Hits / misses | Median response compute | Median preparation + response compute per hand | Maximum response wall interval |
|---|---:|---:|---:|---:|---:|---:|
| Empty control | 0 / 98 | 48 | 0 / 192 | 0.1180 ms | 2.0917 ms | 0.7608 ms |
| Small hit table | 128 / 125,234 | 48 | 192 / 0 | 0.1170 ms | 10.5261 ms | 7.9056 ms |
| Near-cap hit table | 888 / 1,047,484 | 48 | 192 / 0 | 0.1170 ms | 75.5988 ms | 65.9231 ms |

The near-cap table contains all 128 target entries plus 760 retained filler
entries. One more filler entry would produce 1,048,769 bytes and exceed the
1,048,576-byte cap. Its 888-entry count differs from the earlier 883-entry prefix
because the key mix differs; the interface cap did not change.

Every hand matched the predicted complete action sequence, starting/button state,
payouts and carried stacks. All intended hit decisions hit, all empty controls
missed, and all hands/sessions reported complete accounting with no cutoff or
deadline crossings. Assessment errors and worker errors were empty; cleanup
passed. The largest observed response wall interval was 65.923 ms. Ordinary
response medians were close across arms; artifact-dependent hand preparation,
not lookup latency, accounts for the large charged-work difference.

| Arm | Eight-hand session seconds (two seats) | Sixteen-hand session seconds (two seats) |
|---|---|---|
| Empty | 2.898, 2.858 | 5.744, 5.760 |
| Small hit | 3.137, 3.082 | 6.197, 6.260 |
| Near-cap hit | 5.024, 5.011 | 9.896, 9.876 |

Near-cap per-hand charged work ranged **74.4505-77.3697 ms** across 48 hands;
the timings show no obvious upward drift in this short panel. Whole-worker-job
peak was **1,559.16 MiB** under the 3,072 MiB limit, but only a cumulative peak is
recorded, so memory growth or leak absence is not established. Input generation
and setup took 1.821 s; worker execution took 66.568 s and reached ready in 0.321 s.
Sixteen hands is the current session-input maximum. A single deterministic deal
schedule, four sessions per arm, passive-only actions and overlapping prefixes
do not establish reliable tails or broad long-run stability. No production code,
clock implementation, provider lifetime or artifact format changed for this test.

**48-session coverage, Python 3.14.6:** all 48 selected cells completed in
**29.189 s** at verified source `b378104cd2934f248a9545d7d482b0db25db813c`,
within the 120 s budget. The existing corpus supplies 2 seeded deals x 6 seats x
2 opponent lineups, each run with an empty and 883-entry artifact. Pair order
reverses according to `(deal + seat + lineup) % 2`; profiling is off and strategy
is `blueprint-v1`. The full retained source-cell coverage is replayed under 3.14
with new labels, as in the smaller confirmation. Exact definitions, input hashes,
order, source identities, limits and raw accounting are in the
[result](results/runs/4d70fdf7dd014227840eef6935e649bc/result.json).

| Measure | Empty artifact (24 sessions) | 883 entries (24 sessions) |
|---|---:|---:|
| Session wall time, median | 0.3611 s | 0.7494 s |
| Session wall time, observed range | 0.3525-0.3795 s | 0.7347-0.8135 s |
| Bot decisions | 64 | 64 |
| Response compute, median | 0.1165 ms | 0.1185 ms |
| Response wall interval, maximum | 0.6437 ms | 66.6355 ms |
| Preparation plus response compute per hand, median | 1.6244 ms | 75.3776 ms |

The median of the 24 paired session-time differences is **0.3894 s**, ranging
0.3735-0.4600 s. Four near-cap sessions include hand-start preparation inside
their first response interval; other hands account for it separately. This is
why median response compute stays small while total charged hand work rises.
These ledger sums and external session times have different boundaries; the
unprofiled batch does not attribute the remaining wall-time difference to a
particular function. Every measured response interval was nonzero.

All 128 decisions were `passive_default` table misses, including all 64 near-cap
decisions. Applied actions, settlements and carried stacks matched in **24/24
pairs**. All 48 hands/sessions reported complete accounting, with no interrupted
responses or reported work-cutoff/deadline crossings. Worker errors were empty
and cleanup passed. Input/setup took 0.363 s; worker execution took 28.823 s and
reached ready in 0.366 s. Whole-worker-job peak memory was **1,578.57 MiB** under
the 3,072 MiB limit; only a cumulative peak is recorded, so this does not establish
memory stability over long sessions.

This batch establishes tractability and observed miss-path behavior across the
retained panel. Its maximum response wall interval, 66.636 ms, is well below the
14,000 ms cutoff in these observations. Two deals, 24 paired contexts and no
independent repeat per cell do not establish reliable tails, general policy
strength, or unseen-state behavior. Hit-path coverage and longer sessions remain
separate missing measurements. Python 3.14 is the user's target going forward;
3.11 figures below are retained historical evidence.

The September 8 small session batch at committed source
`b378104cd2934f248a9545d7d482b0db25db813c` completed **4/4 cells in 6.448 s**
on Python 3.11.15, within its 30 s limit and the prospective 10 s feasibility
threshold. Source verification passed and took 3.483 s once; all input/setup work
took 3.580 s, then the persistent worker took 2.866 s, reaching ready in 0.392 s.
These intervals nest and must not be added indiscriminately. The exact selected
cells are retained in the [result](results/runs/90ec1825cddc4d94aed40135e3169ee2/result.json).
Profiling was disabled, strategy was `blueprint-v1`, and the existing seeded
contexts were fixed before execution. Order was empty/883, then 883/empty.

| Context (deal / seat / lineup) | Artifact entries | Session wall seconds | Bot decisions | Hand preparation ledger ms | First-response ledger ms |
|---|---:|---:|---:|---:|---:|
| 0 / 0 / 0 | 0 | 0.3743 | 4 | 0 | 0 |
| 0 / 0 / 0 | 883 | 0.7877 | 4 | 94 | 0 |
| 1 / 3 / 1 | 883 | 0.7953 | 2 | 16 | 78 |
| 1 / 3 / 1 | 0 | 0.3624 | 2 | 0 | 0 |

All 12 decisions were table misses (`passive_default`), including six with the
near-cap artifact. Applied actions, settlements and carried stacks matched within
each pair. Every hand/session reported complete accounting, no interruption and
no work-cutoff/deadline crossing. Worker cleanup passed with no errors; cumulative
worker-job peak memory was **1,576.36 MiB** against the 3,072 MiB cap. This is a
whole-job peak, not isolated artifact memory or evidence of a leak.

**Precision limit discovered:** 11/12 response intervals were reported as zero.
Local `time.get_clock_info('monotonic')` on 3.11 reports `GetTickCount64()` with
**0.015625 s resolution**; the runtime's `MonotonicWitness` defaults to
`time.monotonic_ns`. Nanosecond-valued fields therefore do not resolve short
decisions on this interpreter. The near-cap hand ledgers each attribute 94 ms
across preparation and responses, but preparation can fall outside the first
response interval; do not describe every first decision as including that total.
The maximum recorded response was 78 ms, well below 14,000 ms in these observations,
but zero readings are not zero-cost decisions and four hands cannot establish tails.
The local 3.14.6 interpreter reports `QueryPerformanceCounter()` and 1e-7 s
resolution. The confirmation below uses that existing interpreter; no clock
source or production code was changed for either run.

**Python 3.14 confirmation:** the same four selections completed **4/4 in 3.149 s**
at the same verified source and with identical input hashes. The retained plan
has only partial 3.14 coverage, so this replay uses the four recorded 3.11 cell
definitions with new runtime/cell/session labels and empty unused legacy argv.
The [result](results/runs/c4a11b3af5424e5e972c379bce9dcae4/result.json) retains
both the original cell IDs and the executed definitions. Order, contexts,
strategies, artifacts, profiling and limits are unchanged.

| Context (deal / seat / lineup) | Artifact entries | Session wall seconds | Hand preparation ledger ms | First-response charged compute ms | First-response wall ms |
|---|---:|---:|---:|---:|---:|
| 0 / 0 / 0 | 0 | 0.3905 | 1.8850 | 0.1253 | 0.4491 |
| 0 / 0 / 0 | 883 | 0.7534 | 76.2349 | 0.1147 | 0.4374 |
| 1 / 3 / 1 | 883 | 0.7523 | 9.5629 | 65.2798 | 65.5936 |
| 1 / 3 / 1 | 0 | 0.3622 | 0.8718 | 0.2910 | 0.5890 |

All 12 response intervals are now nonzero. Apart from the response that includes
hand-start preparation, near-cap response compute ranged **0.0997-0.1329 ms**,
with response wall intervals **0.3907-0.6150 ms**. Compute and wall are different
ledger fields; do not substitute one for the other when comparing cutoffs.
All decisions again missed the table; actions, settlements and carried stacks
matched both artifact pairs and their corresponding 3.11 cells. Accounting was
complete with no work-cutoff/deadline crossings or errors, cleanup passed, and
whole-worker-job peak was **1,576.87 MiB** against 3,072 MiB.

Input/setup time was **0.363 s**, versus 3.580 s in the preceding 3.11 run;
worker times were **2.782 s versus 2.866 s**. Most of the total-batch difference
therefore precedes worker execution. This single ordered pair of batches does
not establish a general interpreter speedup. It establishes useful 3.14 timing
resolution and feasibility for broader coverage. More contexts/repetitions,
hit cases and longer sessions are needed before making tail or stability claims.

The original September 7 read-cost diagnosis at source
`5845f32f010a44d924abc2f50ae142d1c6adec1b` compared four 12-trial runs:
unchanged **88.931 s**, profiled **95.360 s**, bounded-read prototype **47.859 s**,
and unchanged confirmation **95.554 s**. All 48 trials completed with matching
actions, settlements, carried stacks, counters, and chip arithmetic. An ABBA
component probe over the same 500 files returned identical bytes/identity tokens
and reduced median time from **1.300 s to 0.328 s** (about **3.96x**). The parent
profile attributed **41.928 s self time** to 21,635 buffered reads; overlapping
cumulative profile rows must not be added.

That prototype changed the requested read length from `cap + 1` to
`observed_size + 1`; it did not establish that each old request physically read
16 MiB from disk. It was injected in memory, so the unchanged production source
manifest alone does not identify its executed code. The original launcher and
report are retained in the [work-folder archive](../docs/archive/work-folders-2026-09-08.zip)
under `performance-pass-20260907/`. One candidate matrix, two unprofiled controls,
run order, caching, host load, and concurrent filesystem discovery limit the
speedup claim. The later source-bound 12-trial result was **49.2236669 s**;
see the [adopted bounded-read report](../docs/architecture/v0a-bounded-reads-r001/performance-report.md).
These are historical measurements, not a new benchmark of the current harness.

The original representative workload completed only 18 of 341 cells in a
3,604.311-second measured envelope. Worker intervals consumed 1,904.602 seconds
and between-worker gaps another 1,699.709 seconds. It never reached completed
session, reuse, or history measurements. Those missing outcomes remain missing
in that run; the newer reuse observations are separate evidence.

The revised harness checks source once, checks HEAD and selected inputs before
each grant, caches loaded tools, and uses one worker per invoking runtime. Whole
worker-job memory supervision starts at suspended launch. The earlier two
empty-artifact session checks established functional execution. The newer paired
batch above adds near-cap coverage, with the stated clock-resolution limitation.

The retired workload staging records preserve why the earlier source review
failed. At r003 candidate `2e1457046c640045fe0b404bfc3d6f78cd5e4b45`, review found
that qualification could reuse a stale relative time budget after slow grant
preparation, and memory sampling began only after worker readiness. These were
control-flow defects, not observations of an actual overbudget qualification or
3 GiB excursion. The current deadline and suspended-launch supervision controls
address the relevant lifecycle boundaries; the old review remains historical
evidence. Its disposition and failed development checks are in the archive under
`blueprint-workload-source/r003/`.

| Next question | Evidence needed before changing the bot |
|---|---|
| Can the live runtime safely retain preparation across hands? | Specify ownership and mutation behavior, then compare real sessions using the runtime's charged accounting ledger. The current reuse prototype alone does not preserve every live contract. |
| How much deadline margin remains at the largest fitting table? | Charged first-decision and subsequent-decision measurements, including preparation, realistic misses and histories, and enough observations to examine tails against the 14,000 ms work cutoff. |
| Should full-history keys be compressed or represented differently? | Measure bytes and key construction by history length, then compare a candidate representation while preserving exact lookup behavior. No replacement format has been selected. |
| How far can table size grow? | Complete the missing resource/scaling measurements. The earlier projections to 8,192 and 65,536 entries remain untested; extrapolated memory is not a measured bound. |

## Evidence and reproduction

The reports below are supporting records, not instructions to repeat archived
approval procedures. Start with this page; open the originals when checking a
number, reconstructing a method, or planning a comparable experiment.

| Evidence | Source identity | Supporting records |
|---|---|---|
| Prepared-provider comparison, 2026-09-07 | Baseline `363c9fb669e19a30375537ee5e92ea338a840a2d`; prepared candidate `666cb43b097707a54733a51cd7930d55920a5af7` | [Full preparation report](../docs/architecture/v0a-blueprint-preparation-r001/performance-report.md); raw summary at `D:/Pontius/tmp/blueprint-preparation-implementation-20260907-001/r002-measure/measurement-summary.json` |
| Original representative workload, 2026-09-08 | Invocation `91f031e91c957a9b273c2ccc345421f7b286b416`; report source `0801ddc05a800b652457fb06a92a739168c7a4b0` | [Findings](D:/Pontius-handoffs/v0a-blueprint-workload-as-is/r001/findings.json); preserved attempt beside them. Exploratory, incomplete; the ordinary acceptance gates were waived, not passed. |
| Revised construction check, 2026-09-08 | Unreviewed working tree based on `91f031e91c957a9b273c2ccc345421f7b286b416` | [Result](results/runs/5d1744d5bc9140f19faceada52e8b62b/result.json), [runtime](results/runs/5d1744d5bc9140f19faceada52e8b62b/runtimes.json); scoped source digest `9e635364a771d8c16f582759d09bb8243a543d60730115f01b7b8cdbf596622a` |
| Reuse comparison and functional session check, 2026-09-08 | Unreviewed working tree based on the same commit | [Reuse result](results/runs/b7e55f19f6434ece899d58e2f98fd3cf/result.json), [reuse runtime](results/runs/b7e55f19f6434ece899d58e2f98fd3cf/runtimes.json), [session result](results/runs/6cb7f0f8bfb6416d8c7474040e0d7f36/result.json); scoped source digest `fb71bfe664420184e5ff63d28b053c26932bbd91b5f4a19428dd839f071bd253` |

The [execution journal](../execution_journal.jsonl) records run outcomes, source
scope and output hashes. The retained corpus is at `D:/bww515/as-is-run-001/`;
its `plan.json` maps cell IDs to hands, arms, repetitions and seeded trajectories.
The [README](../README.md) documents the current benchmark command. A new run is
new evidence; it does not replace an interrupted or historical result.

**Availability:** the earlier journal-referenced JSON results and their `runtimes.json`
files through cleanup checkpoint `7bdef39` are included in Git with byte-preserving
attributes. The new four-session [result](results/runs/90ec1825cddc4d94aed40135e3169ee2/result.json)
and [runtime record](results/runs/90ec1825cddc4d94aed40135e3169ee2/runtimes.json)
are retained locally under the ignored run-output directory and are not yet committed.
The same applies to the 3.14 [result](results/runs/c4a11b3af5424e5e972c379bce9dcae4/result.json)
and [runtime/clock metadata](results/runs/c4a11b3af5424e5e972c379bce9dcae4/runtimes.json).
The 48-session [result](results/runs/4d70fdf7dd014227840eef6935e649bc/result.json)
and [runtime/clock metadata](results/runs/4d70fdf7dd014227840eef6935e649bc/runtimes.json)
are also retained locally and not yet committed.
The controlled-hit [result](results/runs/2efd6266a9b944f3b85a9ca31de99b45/result.json),
its `runtimes.json`, and the generated `inputs/` beside it are likewise local,
ignored outputs pending retention in a later checkpoint. Regenerating them uses
the experiment's `--filler` input; its original path and hash are recorded in the
design. The generated final hit artifacts themselves are retained with this run.
The `D:/` locations, including the input corpus, remain machine-local and are
not recovered by cloning. Development source digests identify scoped bytes;
the final cleanup checkpoint does not reconstruct every intermediate dirty
checkout used by earlier runs. No new performance claim follows from archiving
these outputs.

The September 8 work-folder cleanup additionally preserves local historical
findings, review packets, helper originals, and development checks in
[one recovery ZIP](../docs/archive/work-folders-2026-09-08.zip). Its `recovery.json`
maps every original path to either a ZIP member or an exact Git blob reachable
from `7bdef39b741c5f9968a1187d3c49d3d05b99e915`. In particular,
`blueprint-workload-as-is/r001/findings.json` and `findings.md` are recoverable
locally. The archive does not contain the full machine-local measured attempt or
input corpus. Archived next-action notes and publication scripts are superseded
reference material, not current commands.

Related background: the [earlier bounded-read report](../docs/architecture/v0a-bounded-reads-r001/performance-report.md)
measured the separate 12-trial evaluation wrapper. Its throughput results should
not be combined with the per-cell or per-decision timings on this page.
