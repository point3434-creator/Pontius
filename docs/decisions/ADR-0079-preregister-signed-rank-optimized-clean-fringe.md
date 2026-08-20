# ADR-0079: Preregister signed, rank-optimized clean-fringe reads

**Status:** Accepted before any canonical-source signed-frontier rank, optimized
cut, reach-weighted bound, or timing result was observed

**Date:** 2026-08-20

## Decision

Run one additive successor audit of the exact clean-fringe read accepted by
ADR-0078. The frozen configuration is
`experiments/configs/signed-clean-fringe-audit-v1.json`; its SHA-256 is
`88ea749b95375a2796be564d25674ddc57517a1369a9747c049fa301af27ba16`.
The result target is
`experiments/results/signed-clean-fringe-audit-v1.json`.

The audit consumes the immutable real-policy source artifact with SHA-256
`cdcae48dcca5fd1447fd5ad33426a4b20f04e098c88897d8f0f6eddb797ef36e`
and the ADR-0078 predecessor result with SHA-256
`ed037fe36a351c286b5a0940537d3b2d39e110028bf8d012f02ba6787a3b3b50`.
It changes neither policy object, hand axis, factor belief, terminal automaton,
public tree, rounding tolerance, candidate workload, nor small-axis incumbent.

This stage asks one narrow product question: after removing the avoidable
two-sided reach representation and choosing a lower-work exact clean cut, does
a fully certified read beat round-and-recompose by enough on its declared
mature-average customer to justify a dense-free 32-hand structural audit?

## Exact signed reach telescope

For baseline public reach factors `b_i(f)` and candidate factors `c_i(f)`, use
the ordered product identity

`product_i c_i - product_i b_i = sum_k (c_k - b_k) product_{i<k} c_i product_{i>k} b_i`.

The order is ascending seat index and only declared changed seats enter the
telescope. Every frozen candidate changes one seat, so each supported frontier
node has one signed term:

`(r'_s(f) - r_s(f)) * product_{j != s} r_j(f)`.

The full candidate reach for seat `s` remains load-bearing. It preserves
stacked edits when the same seat acts more than once on a public line. No SVD,
TT rounding, candidate root, or baseline root is formed on the read path.

For every candidate, the all-six signed immediate feature width must be exactly
half the frozen two-sided immediate width, including the zero-to-zero no-change
control. A generic two-seat unit test is retained so this optimization cannot
silently become a unilateral-only algebra implementation.

## Rank-cost clean-cut dynamic program

The immediate frontier is the first clean child below the dirty ancestor
closure. Every subtree below such a child contains no policy edit, so it may be
represented either by that child's cached value TT or by an exact cut through
its children with the common baseline/candidate policy folded into public
reach.

For every clean node, compare:

- stop cost: active signed-term count times the sum of that node's middle TT
  ranks across all six cached player-value operators; and
- expand cost: the sum of independently optimal child costs.

Multiply the selected cost by the fixed belief-component count for the reported
feature bill. Stop on exact ties. The dynamic program sees current cached ranks,
policy reaches, and public topology only. It sees no utility delta, exact
candidate value, future acceptance label, or measured wall time. Its selected
all-six feature width must never exceed the immediate signed width.

This objective deliberately minimizes the regular streamed-contraction work
proxy, not Python wall time. The audit measures whether lower width actually
pays after extra cut planning, more frontier objects, and term preparation.

## Reach-mass-weighted certificate

For frontier cache error bound `b_f`, the unilateral truncation certificate is

`B = sum_f b_f * E[abs(Delta q_f)]`.

The expectation is evaluated exactly under the compatible factor belief by
contracting a rank-one all-ones TT with the absolute signed reach factors. For
a future multi-seat edit the implementation sums absolute ordered-telescope
terms, retaining a conservative triangle bound.

The complete fixed-policy sign threshold is

`B + eps * 256 * public_depth * payoff_span + 1e-10 * payoff_span`.

The Float64 term remains separate because cached TT bounds cover truncation,
not arithmetic noise. Both immediate and optimized bounds must contain their
literal fixed-policy delta errors. The immediate weighted bound must never
exceed the ADR-0078 `2 * max_f b_f` bound after the same machine allowance.
All six signed deltas are also summed, with the sum of their bounds and six
machine allowances serving as the coherent-error envelope.

These certificates say nothing about unilateral best-response value, Pareto or
coalition acceptance, NashConv, equilibrium quality, or exploitability.

## Frozen source and candidate workload

Reproduce the four canonical geometries: six seats, hand counts `{4, 7}`, and
range families `{balanced, blocker_heavy}` on the ADR-0075 board and exact
three-component factor beliefs. Within-seat hands and matching unary columns
use the ADR-0077 canonical ordering. Every serialized policy digest and game
provenance digest must reproduce.

Reuse all 134 ADR-0076 candidates without selection:

- every single-seat consecutive DCFR checkpoint splice;
- every literal unilateral best-response profile against checkpoint 16; and
- the two h4-balanced seat-3 guard interpolations at `1e-12` and `1e-6`.

The target customer is frozen before execution to the 24 h7 DCFR-average
single-seat transitions `4 -> 16` and `16 -> 64`, across both range families
and all six seats. Early uniform-near updates and literal responses remain in
the complete workload but cannot enter the speed gate.

## Five equal evaluator bills

Compare:

1. frozen two-sided immediate clean fringe;
2. signed immediate clean fringe plus its weighted certificate;
3. signed rank-optimized clean fringe plus its weighted certificate;
4. tolerance-rounded dirty recomposition followed by root contraction; and
5. the exact flat compatible-deal evaluator.

Every marginal charges candidate probability-tape construction and dirty
planning. Each clean arm additionally charges its own cut planning, term
preparation, and value contraction. Both signed arms also charge the new bound
contractions; certification is not a free diagnostic. Recomposing charges all
six dirty cache updates and root contractions. Flat charges all six candidate
utilities.

Report the same one-time compile/cache bill, marginal bill, and charged totals
at reuse counts `{1, 2, 4, 8, 16, 32, 64}`. Exact baseline utilities used to
label audit error remain separately timed and unbilled. Timing uses one warmup
and the median of three repeats.

The pooled target speed ratio is

`sum(target recompose marginal) / sum(target signed-optimized certified marginal)`.

It must be at least `1.5`. This threshold is frozen from the ADR-0078 target
ratios of about `1.29-1.33` for the still-two-sided reader and the exact
one-seat width-halving identity. There is no speed gate against flat at four or
seven hands: enumeration is the honest incumbent on axes where it exists, but
its `32^6` dense state is precisely what the wide-axis path must avoid.

## Frozen gates

Require:

- structured-terminal error at most `1e-12`;
- two-sided, signed-immediate, and signed-optimized fixed-policy delta error at
  most `1e-8`;
- recomposed utility error at most `1e-8`;
- zero positive immediate or optimized reach-bound violation;
- zero positive immediate or optimized six-seat zero-sum-envelope violation;
- zero false optimized fixed-policy sign certificates;
- immediate weighted bounds no looser than legacy bounds after machine noise;
- exact one-half unilateral immediate feature width;
- optimized all-six feature width never above signed immediate width;
- every nonzero candidate declares exactly its source seat as changed;
- exact below-guard abstention and nonzero above-guard certification;
- all 134 candidate rows, all 24 target rows, and all 938 reuse-bill rows; and
- at least `1.5x` pooled certified marginal speedup over recomposition on the
  predeclared target customer.

No gate is relaxed if the optimizer lowers rank but loses wall time, if the
weighted bound is tighter but expensive, or if a non-target policy family is
faster.

## Pre-freeze engineering disclosure

Only exact reduced-game controls were observed before this freeze. They show:

- a unilateral signed telescope reconstructs the dense root delta and scalar
  utility while using exactly half the two-sided terms and feature width;
- an ordered two-seat telescope remains exact;
- the rank-cost cut never widens its objective and preserves the exact delta;
  and
- the weighted bound contains rank-truncated cache error and falls by more than
  four orders of magnitude for a `1e-6` interpolation.

No canonical-source signed width, selected cut, weighted bound, target timing,
or speed-gate result was inspected. The complete pre-freeze suite passes 411
tests in 56.599 seconds.

## Dissent protocol

**Confidence:** high in the signed identity and bound proof; moderate in the
rank-width objective; low-to-moderate that the certified Python product clears
`1.5x` after bound and planning costs.

**Opposing evidence:** ADR-0078 found that small-axis flat evaluation wins most
raw marginals, frontier contraction scratch already reaches roughly 90 MB at
seven hands, and cutting deeper may replace a few wider TTs with too many small
terms. The new bound contraction is mathematically cheap in rank but still
repeats the compatible-card incidence work in the current Python kernel.

**Largest risk:** mistaking width reduction for latency reduction. The dynamic
program does not model Python per-term overhead or cache behavior, and the
audit is designed to reject it if those constants dominate.

**Cheapest falsification:** any signed identity or certificate failure rejects
the primitive; otherwise a target pooled speedup below `1.5x` rejects this
Python read path and sends the next work toward a fused native value-and-bound
kernel or back to recomposition, not toward a 32-hand victory claim.
