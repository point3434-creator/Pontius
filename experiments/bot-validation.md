# Bot integration, evaluation, and evidence quality

[Results index](RESULTS.md) · Consolidated 2026-09-08 · Engineering and descriptive play

**Conclusion:** Pontius has a functioning bot/runtime and reusable evaluation
plumbing. The retained checks support legal action handling, hidden-information
boundaries, replay, settlement, and finite local execution. They do not yet
establish a strong full-game policy. The current bot's blueprint lookup path
and the research library's reduced-game search successes are separate assets;
connecting them still requires evidence.

Use this page for “what can the bot actually do?” Use [Blueprint cost](blueprint-performance.md)
for timing and artifact limits, and [Safe search](safe-search.md) for research
candidate quality. Source acceptance, completed games, and winning poker are
different claims throughout this summary.

## Capabilities and their demonstrated boundaries

| Area | What is supported | What remains outside the evidence |
|---|---|---|
| Legal complete-hand reference | Explicit-deal six-seat fixtures exercise public/private views, betting order, all-in transitions, independent side-pot arithmetic, and passive fallback. [ADR-0288](../docs/archive/ADR-0288-complete-reference-hands-pass-the-exact-one-seat-loop.md) | The passive reference is untrained. Fixed replay correctness is not opponent adaptation or strategy strength. |
| Belief and policy interface | Full-width card domains and an immutable rational policy crossed the reference-hand interface. [ADR-0290](../docs/archive/ADR-0290-full-width-belief-and-rational-policy-cross-the-reference-hand.md) | This was not validated scalable five-opponent value contraction, full-game training, or a connected strategy-producing resolver. |
| Runnable bot path | The maintained table host and session tool execute blueprint and fixed baseline providers, with action legality checks, clocks, child-process cleanup, and a portable blueprint codec. [Runtime milestone](../docs/archive/ADR-0489-close-the-v0a-engineering-milestone.md), [codec record](../docs/archive/ADR-0491-source-seal-the-portable-blueprint-artifact.md), [README](../README.md) | These are engineering components. A portable artifact format does not supply a trained blueprint. |
| Repeated nonempty sessions | The preparation comparison completed eight three-hand sessions across two strategies, two source versions, and Python 3.11/3.14; actions, settlements and carried stacks matched controls. [Preparation report](../docs/architecture/v0a-blueprint-preparation-r001/performance-report.md) | One table entry and few decisions; these integration controls do not measure large-table throughput or worst-case response latency. |
| Fixed-policy paired evaluation | **48 trials / 24 matched pairs** completed, using two deals, six seats, two opponent lineups, and two fixed policies. All unit cleanups completed. [Retained comparison](D:/Pontius/tmp/v0a-paired-evaluation-run-001/comparison-report.md) | Only two deals; seat and lineup repetitions are not 24 independent deal samples. No general policy ranking follows. |
| Current CPU behavioral coverage | The latest cleanup verification exercised **552 cases** through 44 suites: **541 passed / 11 skipped on Python 3.11**, and **542 passed / 10 skipped on Python 3.14**. Ten skips are optional SciPy cases; Python 3.11 also lacks `math.fma` for one host-pair population check. A separate SciPy-enabled run passed all three affected sparse-contraction cases without skips. [Journal](../execution_journal.jsonl), [manifest](../tests/cases.json) | Fresh CPU verification after driver retirement and the worker stderr classification fix; not every historical test, GPU execution, or a poker-strength result. |
| Current benchmark lifecycle | A persistent worker completed the focused construction and session checks. The larger reuse check retained 30/32 cells at its time limit and confirmed cleanup. [Blueprint summary](blueprint-performance.md) | Whole-job supervision improves observability; it does not establish large-table memory or live latency bounds. |

## What the actual paired poker results say

The retained comparison reported these exact totals:

| Fixed control policy | Net chips across its 24 trials |
|---|---:|
| Baseline rules | -18 |
| Empty-blueprint passive fallback | +101 |
| Baseline minus blueprint | -119, or -119/24 per matched pair |

The sign is stated explicitly because reversing the subtraction reverses the
story. The empty blueprint generated 64 passive-default decisions: 26 calls and
38 checks. It was not a trained policy. Large opposing seat totals and the two
underlying deals prevent treating the overall total as a win-rate estimate or
evidence to choose the passive policy. The result establishes working paired
arithmetic and a descriptive outcome on those fixed controls.

The old run took 382.532 seconds from parent launch through exit and retained
269 output files totaling 917,500 bytes. Those figures belong to that older
evaluation wrapper; they are not the current persistent-worker benchmark's
runtime or storage cost. Raw game results and complete subgroup arithmetic are
in the [descriptive result](D:/Pontius/tmp/v0a-paired-evaluation-run-001/descriptive-result.json).

## What changed in our interpretation

**Interpreter labels needed correction.** An older validation path labeled
Python 3.14.6 executions as isolated Python 3.11 checks. The
[identity correction](../docs/archive/ADR-0481-record-the-release-interpreter-identity-correction.md)
also addressed a Windows identity-width mismatch and recorded fresh checks on
the intended interpreters. Earlier mislabeled runs remain 3.14 evidence. The
obsolete inventory diagnostic was removed during cleanup; the finding survives.

**Repeated verification was a research bottleneck.** The
[bounded-read experiment](../docs/architecture/v0a-bounded-reads-r001/performance-report.md)
reduced a fixed 12-trial wrapper to 49.224 seconds, compared with earlier
88.931/95.554-second controls. Those controls were collected at different times
and paths. The later blueprint harness measurements isolated a much larger
startup problem and justified moving verification to run boundaries. Neither
engineering improvement says the policy plays better.

**Research value is not automatically connected to emitted actions.** Reduced
h32 experiments produced useful certified candidates, while the maintained
bot emits from its blueprint/baseline provider path. A full-game trained policy,
strategy-producing resolver integration, and broad live evaluation are not
established by the results reviewed here.

## Practical next questions

| Question | Evidence needed |
|---|---|
| Is a candidate policy stronger? | A declared objective and independent deal/opponent population, paired controls, uncertainty that respects shared deals, and separation of tuning from final evaluation. |
| Will it act within its budget? | Runtime-ledger preparation and decision measurements on realistic fitting artifacts, misses, long histories, and enough repetitions to examine tails. |
| Can research search safely drive the bot? | An explicit policy/abstraction/ownership contract, full-hand integration controls, and measured candidate acceptance and fallback under the actual clock. |

## Evidence and recovery

The paired execution source was
`bd71f4b11dcc0177283431a4ec468fdc152e7686`; its operating record was adopted at
`5845f32f010a44d924abc2f50ae142d1c6adec1b`. The comparison reports and raw
descriptive result were present at `D:/Pontius/tmp/v0a-paired-evaluation-run-001/`
when this summary was written. The directory is machine-local; a clone does not
recover it. The Windows identity correction is recorded at
`b5df265cf04739cbd051e9de5423bb1e5a66508a`.

The 59 historical evaluation and paired-run coordination scripts were moved
intact from the root to [the helper archive](../docs/archive/root-helpers/).
These previously uncommitted originals are included in the cleanup checkpoint;
`git log -- docs/archive/root-helpers/` locates their recovery commit. The older
source commits above do not establish recovery of those helper bytes.
They are historical reference material with old path and publication
assumptions, not maintained commands. This relocation changes neither the
paired comparison findings nor the raw-result retention limits above.

The September 8 cleanup runs were explicitly unreviewed development work based
on `91f031e91c957a9b273c2ccc345421f7b286b416`; the journal records their scoped
working-byte identities. Follow the current README for workflow. Historical
source seals and one-shot run restrictions in supporting documents are evidence
history, not instructions to reinstate those processes.

The follow-on removal of historical artifact assertions preserved all 34
maintained suites. Fresh Python 3.11 verification exercised 477 cases: 469 passed,
eight optional SciPy cases skipped. Native Windows trace-handle checks failed
under the restricted sandbox and passed when run outside it, including the full
suite. This is CPU behavioral verification of the cleaned working tree, not a
new GPU, Python 3.14, benchmark, or playing-strength result. The execution journal
retains both the initial failures and the successful verification.

The subsequent cleanup batches brought existing projection, public-tree,
policy/cache, sparse-contraction, selective-separation, shared-direct, and
fixed-width controls into the normal manifest while retiring unused
orchestration. Current coverage is 552 cases: Python 3.11 passed 541 with eleven
skips; Python 3.14 passed 542 with ten skips. Both lack optional SciPy in their
isolated environments; Python 3.11 also lacks `math.fma` for one population
control. All fifteen newly included fixed-width controls passed on Python 3.14.
The earlier separate SciPy-enabled run passed all three sparse-contraction cases.
These checks do not rerun the historical experiments whose drivers were removed.

Shared-direct wrapper retirement adds twenty existing sample-plan and synthetic
reader controls to the maintained manifest. Their cubin fixture reads exact
hash-checked retained bytes without re-admitting the old source tree; the
numerical classifier and reader mutation checks still execute. Separately,
the legacy fixed-width outcome suites exposed four existing failures/errors
among ten cases because their readers expected archived ADRs at old paths.
Those legacy read paths remain outside current maintained-suite coverage.
