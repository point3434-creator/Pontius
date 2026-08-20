# ADR-0080: Signed immediate passes; rank-cut optimization is a no-op

**Status:** Exact signed immediate reader and reach-weighted certificate
accepted; current rank-cost cut optimizer rejected from the hot path

**Date:** 2026-08-20

## Result

The frozen ADR-0079 audit completed from clean commit
`363e4ca` in 1,395.745 seconds. The canonical result is
`experiments/results/signed-clean-fringe-audit-v1.json`. Its SHA-256 is
`f3930aaa8fb7d11f3140613a53bdb2a32a2010d385371c7fadae802dda0ef833`,
and its size is 2,168,925 bytes.

All frozen hashes, 134 candidate rows, 24 target-customer rows, 24 terminal
rows, and 938 reuse-bill rows reproduce. Every result gate passes.

This is a real read-path win, but it is not the win originally attributed to
both proposed mechanisms. The exact signed telescope creates essentially all
the gain. The dynamic-program cut optimizer expands zero nodes and only adds
planning latency.

## Exactness and certification pass

All mathematical controls remain clean:

- maximum structured-terminal error: `4.44e-16`;
- maximum two-sided delta error: `4.03e-14`;
- maximum signed-immediate delta error: `4.03e-14`;
- maximum signed-optimized delta error: `4.03e-14`;
- maximum recomposed utility error: `2.80e-13`;
- zero immediate or optimized bound violations;
- zero immediate or optimized six-seat zero-sum-envelope violations; and
- 654 nonzero fixed-policy sign certificates with zero wrong signs.

The `1e-12` interpolation abstains for all six values. The `1e-6`
interpolation certifies all six. Thus both sides of the guard threshold remain
exercised under the new candidate-dependent bound.

The certificate continues to cover fixed-policy utility deltas only. Nothing
in this result certifies a best response, Pareto or coalition comparison,
NashConv, equilibrium quality, or exploitability.

## Signed algebra produces the measured win

Every one of the 110 nonzero candidates has exactly 384 signed terms across six
value seats, versus 768 two-sided terms. All-six component-rank width is exactly
halved on every candidate, as preregistered:

- signed width range: 3,612 to 10,485;
- two-sided width range: 7,224 to 20,970; and
- target median signed width: 9,621.

On the 24 predeclared h7 mature-average rows:

- median two-sided value core: 1,755.1 ms;
- median signed-immediate value core: 887.3 ms;
- pooled core speedup: `1.974x`;
- median reach-bound core: 71.5 ms;
- median complete signed-immediate certified marginal: 979.6 ms; and
- pooled two-sided/signed-immediate certified marginal ratio: `1.803x`.

The core result follows the algebra almost perfectly: halving feature width
nearly halves contraction time. Term preparation rises from about 0.9 ms to
7.7 ms because the signed path constructs and validates delta factors, but this
is below one percent of the target bill. The certificate, not term preparation,
is the material non-value overhead.

Peak bounded-batch scratch does not halve because the feature-width cap fixes
the largest individual batch. Signed value scratch remains about 19-94 MB,
while the rank-one bound pass uses about 3.6-17 MB. Total streamed work falls;
peak batch allocation does not.

## The reach-weighted bound is materially tighter and honestly priced

Across 660 positive player/candidate bound comparisons, the new bound divided
by the ADR-0078 legacy bound has:

- minimum `8.91e-15`;
- 25th percentile `0.0242`;
- median `0.0611`;
- 75th percentile `0.0994`; and
- maximum `0.3170`.

The median bound is therefore about `16.4x` tighter, and no observed weighted
bound is even one-third of its legacy counterpart. The candidate dependence is
real rather than cosmetic: on the `1e-12` guard interpolation the ratio is
about `2e-14`, and on the `1e-6` interpolation it is about `2e-8`.

Absolute positive weighted bounds have median `2.00e-13` and maximum
`1.75e-10`, versus legacy median `6.84e-12` and maximum `2.41e-9`.

The current Python bound pass consumes roughly 6-19% of a nonzero certified
marginal, with a median near 15% across all axes and roughly 7% on the h7 target
rows. It is worth fusing with value contraction in a future native kernel, but
it must not be omitted from latency accounting.

The optimized six-seat zero-sum residual has median `1.09e-15` and maximum
`7.08e-14`. Its envelope has median `1.13e-10`; at these tiny truncation bounds,
the frozen Float64 allowance dominates. A later production-scale envelope may
need a measured dimension-sensitive noise term, as already noted in ADR-0069.

## Rank-cost cut optimization does nothing on this tree

The dynamic program expands zero clean nodes in all 110 nonzero candidates.
Every optimized frontier, support, term count, rank histogram, and feature
width is identical to its immediate counterpart. Median optimized/immediate
width ratio is exactly 1.0, with minimum and maximum also 1.0.

The reason is structural: after policy folding and tolerance rounding, stopping
at each immediate cached node is never wider than the sum of the independently
available child ranks. The rank-93 tail does not imply that its children have a
cheaper summed representation.

Because no alternative cut is selected, this audit cannot validate a paired
predicted-versus-measured cut saving. It does validate the broader work proxy:
across nonzero candidates, log feature width versus signed core time has Pearson
correlation about `0.97` and Spearman correlation about `0.96`. Term count is
constant and provides no ranking signal.

The optimized core fluctuates around immediate due timing noise, while the
optimizer adds about 12.5 ms of target planning versus about 0.65 ms for the
immediate plan. Target pooled recomposition/signed ratios are:

- signed immediate certified: `3.279x`; and
- signed optimized certified: `3.259x`.

The frozen optimized-arm gate passes, but the optimizer itself is rejected from
the hot path. A per-term constant would only make expansion still less likely
on this workload. Do not fit one without a new tree where the DP actually
selects competing cuts.

## Customer-specific economics

For the frozen target customer, pooled recomposition/signed-optimized certified
speedup is `3.259x`, well above the `1.5x` gate. Signed immediate is slightly
better at `3.279x`.

The two target transitions agree:

| h7 transition | Median signed optimized | Median recomposition | Pooled speedup |
|---|---:|---:|---:|
| checkpoint 4 to 16 | 985.2 ms | 3,180.6 ms | 3.231x |
| checkpoint 16 to 64 | 993.3 ms | 3,231.9 ms | 3.286x |

Both range families pass separately: recomposition/signed-immediate is
`3.078x` for balanced and `3.507x` for blocker-heavy.

The provenance split remains necessary, but the boundary moves favorably:

- h7 checkpoint 1 to 4: recomposition/signed optimized is `0.458x`, so
  recomposition is still about 2.18x faster;
- h7 mature checkpoint updates: signed wins by about 3.2-3.3x;
- h7 literal unilateral responses: signed now wins by `1.482x`, where the old
  two-sided reader lost; and
- h7 checkpoint 0 to 1 no-change controls are handled in roughly 17 ms without
  any value contraction, while recomposition still contracts six roots.

At h4, signed beats recomposition modestly on mature updates but the flat
evaluator is roughly 15-19x faster raw. This is not a contradiction: h4 is a
correctness/economics control, not the dense-free customer.

## Flat incumbent and reuse remain explicit

On target h7 rows, signed optimized is still `4.76x` slower than flat on raw
marginal latency. Compile economics reverse the first-use result. The target
signed-optimized/flat charged ratios are:

| Reuse | Ratio |
|---:|---:|
| 1 | 0.657 |
| 2 | 0.778 |
| 4 | 1.000 |
| 8 | 1.377 |
| 16 | 1.942 |
| 32 | 2.647 |
| 64 | 3.353 |

Thus the target crossover is almost exactly reuse four. Across the complete
mixed-axis workload, signed optimized is cheaper than flat through reuse four
and loses from reuse eight onward. Flat wins the raw marginal on 116/134 rows;
the remaining 18 are zero/no-change reads won by the no-term two-sided control.

This does not authorize replacing flat where a literal compatible-deal table
exists. It does support a dense-free successor at axis widths where flat's
Cartesian construction is unavailable.

## Decision

1. Accept the exact signed immediate telescope as the fixed-policy candidate
   read representation.
2. Accept the reach-mass-weighted truncation bound and charge it on every
   certified read.
3. Reject the current rank-cost cut optimizer from the hot path; it selects no
   expansion and adds latency.
4. Retain recomposition for early uniform-near updates and retain flat
   evaluation on small axes where its literal state exists.
5. Treat provenance and baseline crown cost as declared dispatch inputs, not as
   fitted future-label selectors.
6. Do not move directly to a native 32-hand claim. First build a dense-free
   open-mode conditional contraction primitive so actual wider-axis policy
   checkpoints and action comparisons can be generated without `h^6`
   enumeration.

## Next enabling system

The current reader certifies six scalar fixed-policy changes. A realistic
32-hand source and the acceptance vector need per-hand conditional values and
action comparisons. The next audit should therefore leave one private-hand
mode open while contracting the other five under the factor belief and card
compatibility constraints.

The primitive should:

- reproduce flat per-hand/action numerators and denominators at four and seven
  hands;
- batch public children and target seats over one compiled card topology;
- retain Float64 and explicit zero-reach behavior;
- consume structured automaton terminals without a dense intermediate;
- report compile, marginal, feature width, memory, and conditional-value error;
  and
- demonstrate a 32-hand dense-free structural arm before it is used to produce
  real DCFR checkpoints.

That system unlocks two currently blocked customers: a genuine wider-axis
policy source rather than an optimistic policy lift, and unilateral-response or
action-value comparisons rather than scalar-only fixed-policy certification.
Only after its structural economics pass should the signed value-plus-bound
reader be fused into a C++ kernel.

## Limitations

- Four/seven-hand timing does not establish 32-hand rank, memory, or latency.
- All kernels here are Python/NumPy and process six value seats separately.
- The factor-belief source has three components on one board and two range
  families.
- Real policies remain finite selected-axis six-player DCFR averages without a
  multiplayer convergence guarantee.
- The weighted bound proof transfers, but the constant Float64 allowance has
  not yet been validated at 32-hand intermediate widths.
- No measured result here improves the global blueprint, neural leaf model, or
  equilibrium quality; it improves exact candidate-reading quality per unit
  time.
