# Blueprint representation and runtime cost

[Results index](RESULTS.md) · Updated 2026-09-08 · Local engineering evidence

**Current conclusion:** prepared decisions are inexpensive in the tested cases.
The immediate opportunities are avoiding repeated preparation across hands and
reducing the space occupied by full-history keys. The benchmark harness now runs
multiple cells in one worker, so those questions are practical to investigate.
Live deadline margins and poker strength remain unestablished.

This page consolidates the blueprint cost findings. It covers artifact capacity,
provider preparation, and the harness that measures them. Solver quality and GPU
experiments belong to other families. Detailed reports and raw runs remain
available through the evidence links below.

**Reading the numbers:** an artifact is the serialized blueprint table;
preparation builds the provider used for decisions; a cell is one configured
benchmark case. A warm call uses an already prepared provider. Milliseconds
(`ms`) measure operations; seconds (`s`) usually measure workers or whole runs.

## What we know

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
worker-job memory supervision starts at suspended launch. Two session cells
also completed with cleanup confirmed, but used an empty artifact and one hand
each; they establish functional execution, not large-table deadline performance.

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

**Availability:** the journal-referenced JSON results and their `runtimes.json`
files are included in the cleanup checkpoint with byte-preserving Git attributes.
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
