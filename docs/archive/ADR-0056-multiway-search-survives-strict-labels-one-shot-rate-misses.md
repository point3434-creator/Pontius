# ADR-0056: Multiway search survives strict labels; one-shot rate misses

**Status:** Completed; four of five primary strategy hypotheses pass

**Date:** 2026-08-19

## Result and provenance

The frozen ADR-0054 grouped three-player experiment completed without a code,
configuration, source, or split change. It produced 24 contexts, 96 target
range shifts, and 1,728 candidate records from six development board groups.
No validation or test context was materialized.

The configuration SHA-256 is
`807d511a920ee1bcb13d5cf54ca61991c30bb63845dabfb9e04d318c1f8ef0a4`.
The result is
`experiments/results/multiway-river-search-acceptance-development-v1.json`,
SHA-256
`27739ba1d66a14a2a9d4a69914ce23ea70f332d6535b82fa7efa99192aba1b74`.
It was generated from clean commit
`896f82ab7548d7f9dc5c1a036c8f00c3252456f4` in 279.833 seconds. The complete
repository passed 325 tests in 57.855 seconds before the run.

All 24 source blueprints passed at the first 128-iteration checkpoint. Their
maximum payoff-normalized NashConv was `0.000644255`, below the frozen `0.001`
limit. Ordinary traversal and the compiled tape agreed within `1.95399e-14`,
with zero best-response action mismatches and exact source-relative replay.

## Frozen verdict

| Gate | Frozen result | Verdict |
|---|---:|---|
| Correctness and source quality | every subgate true | pass |
| Hot tape versus ordinary candidate evaluation | `6.0206x` | pass |
| Compile plus two hot candidates versus two ordinary evaluations | `1.7685x` | pass |
| DCFR-32 aggregate accepted raw reduction versus blind | `+4.8219%` | pass |
| DCFR-32 aggregate one-shot raw rate versus blind | `-3.3018%` | **fail** |
| DCFR-32 unilateral-Pareto acceptance | `36/96 = 37.5%` | pass |
| DCFR-32 coalition-stress acceptance | `10/96 = 10.4167%` | pass |
| Coalition-stress normalized reduction | `+0.156651` | pass |

The overall frozen `passed` field is therefore false. The failure is narrow but
real: the fixed primary one-shot gate did not beat blind search after paying to
compile a fresh tape. Precompiled or amortized diagnostics cannot override that
preregistered verdict.

## Primary arm economics

| DCFR-32 arm | Targets | Raw reduction | Normalized | Charged ms | Raw/ms |
|---|---:|---:|---:|---:|---:|
| Blind | 96 | `58.006238` | `0.940901` | `29,914.143` | `0.00193909` |
| Aggregate exact | 78 | `60.803218` | `0.974487` | `32,427.255` | `0.00187507` |
| Unilateral Pareto | 36 | `24.998692` | `0.395154` | `32,427.255` | `0.00077091` |
| Coalition stress | 10 | `8.383103` | `0.156651` | `37,704.598` | `0.00022234` |

Aggregate acceptance removed 18 harmful blind deployments, whose worst raw
increase in NashConv was `1.597150`. Its quality gain was not large enough to
pay the one-shot compilation charge. The same conclusion holds under the
payoff-normalized diagnostic: normalized reduction/ms falls 4.46%, so the
failure is not solely an artifact of raw pot weighting.

The primary precompiled rate is `0.00200316`, 3.30% above blind, and the
trajectory-amortized rate is `0.00199559`, 2.91% above blind. Across the 96
targets, compilation cost `2,073.592` ms, or 21.600 ms per target on average.
At the observed costs, one-shot DCFR-32 would need compilation to fall by
51.63% to tie blind rate. This is a diagnosed break-even target, not a changed
gate.

Ordinary candidate evaluation cost 46.148 seconds across all records, versus
7.665 seconds hot. Excluding the known warm-start no-op at checkpoint one still
gives a `5.8634x` hot speedup; fixed primary DCFR-32 gives `5.7390x`. The tape
mechanism is therefore genuine rather than an identity-candidate artifact.

## What the multiplayer constraints exposed

Aggregate NashConv is not an adequate multiway acceptance rule. Of the 78
primary aggregate improvements, 42 increased at least one player's unilateral
deviation gain beyond the numerical guard. Of the 36 unilateral-Pareto
candidates, 26 increased at least one pair-coalition gain. Constraint failures
overlap across players and pairs; they are not 42 or 26 independent cases.

The strict-arm value is highly structured. Three-way strength-alignment range
shifts produced 97.80% of unilateral-Pareto raw reduction and 93.73% of
coalition-stress raw reduction. The 72 single-seat blocker-sensitive reweights
produced only `0.5503` unilateral-Pareto and `0.5253` coalition-stress raw
reduction in total. Search often reduced aggregate incentive after a local
range shift by redistributing vulnerability to another seat or pair.

Coalition-stress acceptance occurred in four of six groups and unilateral
acceptance in every group, but the primary aggregate one-shot rate beat blind
in only two of six groups. This is development evidence that useful search
survives explicit constraints; it is not a grouped-transfer result for a fixed
online rule.

## Nonselecting checkpoint diagnostics

The solver/checkpoint comparison was frozen as diagnostic and does not replace
the DCFR-32 primary result.

| Arm | Accepted raw/ms | Ratio to blind | Group wins |
|---|---:|---:|---:|
| LCFR-4 | `0.00441184` | `1.213x` | 3/6 |
| DCFR-4 | `0.00434556` | `1.908x` | 4/6 |
| DCFR-8 | `0.00371032` | `3.964x` | 5/6 |
| DCFR-32 primary | `0.00187507` | `0.967x` | 2/6 |

Quality per millisecond peaks much earlier than total quality, and both LCFR
and DCFR trajectories are nonmonotone across individual targets. This creates
a credible stopping/incumbent opportunity. The inconsistent group wins forbid
choosing a new checkpoint post hoc. A later scheduler must use causal features,
retain a no-op or best-so-far incumbent, and pass a fresh grouped workload.

## Decision

1. Retain the exact enumerated game, ordinary evaluator, coalition evaluator,
   and compiled tape as the three-player oracle. Their correctness gates pass.
2. Reject fresh one-shot DCFR-32 aggregate verification as a demonstrated
   online-rate winner. Exact acceptance remains a teacher and a reusable-
   evaluator candidate.
3. Do not weaken multiplayer quality to aggregate NashConv. Keep the vector of
   per-player deviation gains as an online acceptance target. Keep coalition
   gains as offline stress labels until a much cheaper justified surrogate
   exists.
4. Advance factorized/source-compiled range-and-policy contraction. Useful
   search survives unilateral and coalition constraints often enough to meet
   ADR-0054's branching condition, while compilation and explicit joint deals
   are now the measured representation bottlenecks.
5. First test exact structural reuse: compile once for a source support and
   apply target range and candidate policy inputs source-relatively. This is an
   exact update, not a similarity-based range cache hit. Then compare a
   factorized or low-rank belief representation against the enumerated oracle
   on utility, every unilateral gain, best-response actions, acceptance labels,
   time, and memory.
6. Future mixed-pot experiments must report both raw and payoff-normalized
   quality rates and group-level wins. Neither replaces an explicitly declared
   deployment objective.

No six-player, equilibrium-convergence, collusion-safety, neural-value, action-
width, or deployable-scheduler claim follows.

## Dissent protocol

**Confidence:** high in the exact labels and narrow primary failure; moderate
that exact structural reuse can recover the missing one-shot economics; low
that the observed strict acceptance fractions survive wider action trees.

**Opposing evidence:** the target supports are tiny and the one-bet tree may
make both search and contraction unusually easy. Pair coalitions share private
cards and transferable utility, so their stress condition is intentionally
stronger than ordinary independent-opponent play. Conversely, six-player
coalition enumeration is not a plausible runtime metric.

**Largest unknown:** whether a compact belief representation preserves the
small per-seat and pair differences that determine strict acceptance, not just
root utility or aggregate NashConv.

**Cheapest falsification:** reuse one source-compiled tape across the four
support-preserving target ranges and reproduce every frozen baseline and
candidate label. If exact source-relative range-plus-policy evaluation cannot
amortize compilation or preserve action maps, low-rank approximation should not
advance.
