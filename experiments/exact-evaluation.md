# Exact evaluation, certification, and reuse

[Results index](RESULTS.md) · Consolidated 2026-09-08 · Reduced-game research

**Conclusion:** exact evaluation is a reusable research capability worth keeping.
Compiled dependencies and source-relative reuse can substantially reduce its
cost without changing the measured values or decisions. Whether that improves
a complete decision depends on setup cost, how long the cache remains valid,
and which strategic checks are included. A fast evaluator is not by itself a
stronger or safer poker policy.

This summary covers the river evaluation chain in ADR-0030–0062. Later
representation work is summarized in [GPU representations](gpu-representation.md),
and the value of the proposed policies in [Safe search](safe-search.md).

**Terms:** *recertification* checks a retained policy under the current ranges;
a *dependency tape* records which computations depend on changed inputs;
*hot* timing excludes compilation. A *best response* maximizes one player's
value against the fixed others. NashConv sums unilateral improvement opportunities;
coalition checks allow a different, coordinated opponent model and cost extra.

## What the experiments established

| Question | Recorded finding | Interpretation and limits |
|---|---|---|
| Is additional warm solving always needed after a small range change? | In the initial range-reuse screen, checkpoint-zero recertification was stronger and cheaper than the proposed checkpoint-four warm prior. All 152 changed-range lookups were structural hints, not exact strategy hits. [ADR-0030](../docs/archive/ADR-0030-recertification-not-warm-solving-is-the-range-reuse-bottleneck.md) | The source was an optimistic exact policy. It motivated testing finite-policy recertification, not accepting nearby ranges as interchangeable. |
| Can sparse range changes be evaluated exactly and cheaply? | Across 896 records, maximum disagreement was **2.31e-14**; hot incremental work averaged **0.1996 ms**, versus **11.1061 ms** for full evaluation. The report's speedup fell from **55.652× hot** to **14.313×** when it charged discovery and cache construction under its stated accounting. [ADR-0032](../docs/archive/ADR-0032-exact-sparse-recertification-passes.md) | Strong development evidence for this sparse workload, including unseen-hand support changes. Setup-inclusive and hot ratios describe different boundaries. |
| Does the mechanism survive a wider betting tree? | The unchanged generic tape passed 840 target recertifications across fixed and wider trees. All **68,514** independent terminal-payoff checks matched; maximum evaluation error was **1.42109e-14**. [ADR-0038](../docs/archive/ADR-0038-multi-size-transfer-passes.md) | Three bet sizes and two raise sizes preserved locality, but absolute sparse work grew about **2.7×**. A smaller dirty percentage does not mean less work. |
| Are candidate policy updates also sparse? | For 264 realistic selective candidates, policy-delta evaluation matched values within **8.88178e-15**, with no response-action or accept/no-op mismatches. Most changes favored a dense flat pass. [ADR-0047](../docs/archive/ADR-0047-policy-delta-passes-dense-reuse-required.md) | Keep both exact paths. Compiling for a single candidate was marginally less efficient than ordinary evaluation; reuse changed the economics. |
| Can an input-density threshold decide whether to search? | A fresh 276-target replication saved **46.31%** of time but lost **1.106%** of raw improvement and passed in only six of 23 board groups. [ADR-0051](../docs/archive/ADR-0051-reject-density-gate-retain-exact-verification.md) | The fixed threshold failed. Equally sparse changes can have different strategic importance. Exact post-search accept/no-op remained useful. |
| Does stricter multiway verification pay for itself? | On 96 three-player targets, aggregate exact acceptance improved raw reduction by **4.8219%**, but fresh one-shot quality per millisecond fell **3.3018%**. Unilateral-Pareto and coalition-stress acceptance retained **36/96** and **10/96** candidates respectively. [ADR-0056](../docs/archive/ADR-0056-multiway-search-survives-strict-labels-one-shot-rate-misses.md) | The overall gate failed. Aggregate improvement, per-player protection, and coalition robustness are different objectives. A hot speedup did not pay the entire first-use bill. |
| Does reusing one source tape help? | Replaying the same 1,728 candidates with 24 source compilations instead of 96 target compilations reduced complete evaluator-path time from **9,356.704 to 8,504.023 ms**, and retained tape storage to one quarter. [ADR-0058](../docs/archive/ADR-0058-source-tape-reuse-passes-factorized-belief-advances.md) | Setup reuse worked, but one of 24 context paths slowed down. At four reuses the pooled complete quality-rate margin over blind search was only **0.29%** and won in two of six groups. This is a fragile break-even, not a deployment rule. |
| Can structural sharing solve full multiway scaling? | Public-tree sharing passed 57 exact profiles over 19 games; exact factorized belief passed 40 closure cases spanning two through six players. [ADR-0060](../docs/archive/ADR-0060-public-tree-quotient-passes.md), [ADR-0062](../docs/archive/ADR-0062-factorized-belief-passes-value-operator-next.md) | These establish useful primitives. Shared public structure still leaves joint private-card growth; correct belief conditioning does not establish a scalable value operator. |

## Conclusions across the family

**Reuse must follow exact structure and support.** A source tape can process
different ranges and policies within its supported topology. A changed public
structure or an outcome outside that support requires invalidation. This is a
different claim from choosing a cached strategy because two ranges look close.

**Measure the complete decision before choosing the fastest primitive.** The
three-player calibration found roughly sixfold hot evaluation gains, yet the
subsequent strategy experiment lost one-shot rate after compilation. Its later
reuse audit improved that cost but produced only a small complete-rate margin.
Those are successive answers, not conflicting measurements to average together.

**The exact enumerated game remains an oracle, not the full-range architecture.**
The [multiway calibration](../docs/archive/ADR-0053-multiway-contract-passes-joint-enumeration-is-teacher-only.md)
explicitly enumerated h³ joint deals for three disjoint private-hand axes. It
reached 306.148 ms for full evaluation at six hands per seat. Sharing computation
helps, but cannot remove the underlying Cartesian growth by itself. Preserve
this control to validate scalable representations on manageable cases.

## What remains to establish

| Needed answer | Useful next evidence |
|---|---|
| When will reuse pay in actual play? | A workload-derived lifetime for each cache, including invalidation, setup, updates, fallback, and complete decision timing. |
| Which checks belong in the live budget? | Explicit per-player acceptance semantics and separately charged coalition stress evaluation; do not silently equate aggregate NashConv with multiplayer safety. |
| Can a compact representation replace enumeration? | Compare values, each player's response, action choices, acceptance labels, memory, and time against the exact oracle; probability reconstruction error alone is insufficient. |

## Evidence and recovery

This is a synthesis of the cited historical reports, not a rerun. Those reports
identify the configuration and result artifacts, including
`river-incremental-recertification-development-v1.json`,
`river-multi-size-dependency-development-v1.json`,
`policy-delta-recertification-development-v1.json`, and
`multiway-source-tape-reuse-audit-v1.json` under `experiments/results/`.
Treat those as recorded raw locations until their availability is checked;
Git history alone may not contain ignored outputs.

Recorded run/source references include `4866d56e6feef7aec7930d7e8b28f1cca1acab97`
(wider-tree run), `d430f4abe1db8a5dc5efb2d3254e1fc32fa0fcd9`
(policy-delta implementation before timing),
`896f82ab7548d7f9dc5c1a036c8f00c3252456f4` (three-player acceptance run), and
`72ca072cd9af4a556ab2d0cc66bd507dcbf28aff` (source-tape reuse run).
The linked reports retain the full provenance and limitations. Archived
procedural requirements are historical context, not current working rules.

The isolated public-tree quotient audit driver and its fixed-workload tests
were retired on September 8 after the question, method, result, and source SHA
were harvested in [RESULTS](RESULTS.md#harvests-before-retiring-isolated-audit-drivers--2026-09-08).
The reusable `PublicTreeTensorEvaluator` and its ordinary-traversal, zero-reach,
correlated-support, and schema tests remain. That existing behavioral suite is
now included in the normal test manifest; the historical 57-profile experiment
was not rerun.
