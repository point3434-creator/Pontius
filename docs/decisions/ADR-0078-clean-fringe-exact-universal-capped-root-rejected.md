# ADR-0078: Clean fringe is exact; universal capped root is rejected

**Status:** Exact delta primitive accepted; universal capped-root product and
current Python clean-fringe hot path rejected

**Date:** 2026-08-20

## Result

The axis-corrected ADR-0076 audit completed from clean commit
`f707e9dace47f22ba65d1e64279563f8727f1907` in 879.109 seconds. The canonical
result is `experiments/results/real-policy-representation-audit-v2.json`. Its
SHA-256 is
`ed037fe36a351c286b5a0940537d3b2d39e110028bf8d012f02ba6787a3b3b50`
and its size is 2,225,393 bytes.

The artifact verifies the v2 config and implementation, the immutable v1
config and implementation, and the ADR-0075 source artifact by their complete
SHA-256 digests. It contains all 126 rank rows, 1,260 partition rows, 378 cap
rows, 134 candidate rows, and 938 reuse-bill rows.

Overall `passed = false`. Thirteen of fourteen result gates pass. The sole
failure is `latest_average_has_safe_capped_product`.

## Exactness and certification pass

Every mathematical and implementation-control gate passes:

- maximum structured-terminal error: `4.44e-16`;
- maximum cached-root error: `2.58e-10`;
- maximum selected-order exact reconstruction error: `2.06e-10`;
- maximum clean-fringe fixed-policy delta error: `4.03e-14`;
- maximum recompose-then-contract utility error: `2.80e-13`;
- zero positive frontier-bound violations;
- zero positive six-seat delta zero-sum-envelope violations;
- zero false fixed-policy sign certificates;
- exact below-guard abstention; and
- nonzero above-guard certification.

The clean reader produces 654 nonzero sign certificates across 804 seat
deltas, with zero wrong signs. Every one of the 24 literal-BR profile rows has
at least one certificate; the synthetic `1e-12` interpolation abstains for all
six seats and the `1e-6` interpolation certifies all six.

The bound is safe but conservative. Median six-seat zero-sum envelopes are
about `1.21e-10` at h4 and `1.73e-10` at h7, while actual nonzero residuals are
roughly ninety thousand times smaller at the median. Maximum envelopes reach
`1.68e-9` and `4.12e-9`. This does not break the frozen guard, but a
reach-mass-weighted bound has meaningful room to improve.

The exact clean-fringe identity therefore advances as a reference primitive.
It certifies fixed-policy utility changes only. Nothing here certifies
best-response, Pareto, coalition, NashConv, or equilibrium changes.

## Real-policy rank curve

The rank-versus-checkpoint curve answers the primary representation question.
Selected middle ranks across target value seats 0/3/5 are:

| Geometry | cp0/cp1 | cp4 | cp16 | final checkpoint |
|---|---:|---:|---:|---:|
| h4 balanced | 9-10 | 51-54 | 54-57 | 43-46 at cp256 |
| h4 blocker-heavy | 6-9 | 40-55 | 43-64 | 36-50 at cp256 |
| h7 balanced | 19-23 | 158-169 | 186-194 | 163-172 at cp64 |
| h7 blocker-heavy | 15-22 | 136-161 | 164-196 | 137-164 at cp64 |

Real averages do not plateau near uniform. They jump toward generic dense-policy
rank by checkpoint four, peak near checkpoint 16, then decline somewhat at the
late checkpoint. The h7 hashed-dense controls select ranks 174-198, so the late
real averages remain structurally close to that difficult customer.

Literal response profiles are different: selected target-seat ranks are 10-35
at h4 and 34-70 at h7. Making the target seat pure collapses much of its own
policy fold. Average and literal-BR provenance genuinely serve different
representations, but the observed direction is more nuanced than “pure is
always harder.”

Complete seat-order selection helps modestly rather than changing the result.
For average profiles, selected exact storage is 95.10% of original-order
storage at the median; 56/66 rows improve and none worsen. Across all objects
the median is 89.99%. Seat order is worth retaining as an offline compiler
choice, not as the missing compression mechanism.

## Universal capped-root gate fails narrowly

Eleven of twelve late-average target rows have a safe capped product under the
frozen error-and-storage conjunction.

At h7, rank 16 passes all six late rows with normalized utility error
`1.07e-5` to `5.15e-5` and storage equal to 4.462% of dense. Rank 32 reduces
those errors to `2.32e-7` to `1.86e-6` at 14.934% of dense.

At h4, rank 8 passes five of six late rows at 19.531% of dense. The sole failed
row is h4 blocker-heavy, value seat 3:

- rank 8 error is `4.654958e-4`, above the `1e-4` limit;
- rank 16 error is `7.779868e-9`, but storage is 63.281% of dense; and
- rank 32 error is `6.276646e-12`, but storage is 113.281% of dense.

The frozen all-row product is rejected. We do not rewrite it as an 11/12 gate.
The result also shows why exact rank alone is not the value product: exact h7
middle ranks reach 137-172 while rank 16 still preserves the measured scalar
utilities. A future size-aware/adaptive-rank product may be worth a fresh
dense-free test, but this artifact does not authorize it.

## Three-evaluator economics

The flat compatible-deal evaluator remains the decisive small-axis incumbent.
It wins the raw marginal bill on 115/134 candidates. Clean fringe wins 18
mostly no-change rows; recomposition wins one. On changed candidates:

- h4 clean medians are 228-287 ms, recomposition 189-204 ms, and flat 7-12 ms;
- h7 clean medians are 1,600-1,786 ms, recomposition 1,745-1,867 ms, and flat
  117-289 ms.

Compile cost reverses the first-use picture at h7. Flat construction costs
4.58-8.46 seconds, versus typical six-seat TT cache bills around 2.40-2.52
seconds. Pooled h7 charged flat/clean ratios are `2.120`, `1.526`, `1.009`, and
`0.640` at reuse 1/2/4/8. Thus clean is cheaper for a single h7 candidate,
essentially tied at four, and loses beyond that. At h4, flat wins even after
the compile charge.

Across all 134 rows, clean versus flat charged totals move from a `1.722x`
advantage at reuse one to a `0.854x` ratio at reuse four and `0.193x` at reuse
64. This is why no one reuse count can summarize the product.

The current clean stream also loses to recomposition in pooled totals at every
reuse: recompose costs 94.2% of clean at reuse one and 85.8% at reuse 64. That
aggregate hides a useful phase split:

- on h7 average-to-average checkpoint 4→16 and 16→64 edits, median
  recompose/clean marginal ratios are `1.293` and `1.326`, so clean is already
  faster;
- on h7 uniform-near checkpoint 1→4 edits, the ratio is `0.212`, because the
  baseline crown is cheap to recompose; and
- on literal-BR candidates it is `0.617`, because the pure target policy
  collapses candidate crown rank.

This is a legal structural/provenance observation, not a fitted runtime
selector. Average updates on an expensive crown are the clean reader's actual
customer. Uniform-near and pure-response objects remain recomposition/tape
customers unless a future cost model passes separately.

## What the work counters reveal

Every nonzero whole-seat edit dirties 63 of 385 public nodes (16.36%) and has a
64-node delta-support frontier. Node fraction is again misleading:
cost-weighted dirty fraction is about 39% at h4 and about 80.5% for mature h7
baselines.

All-six streamed feature width has medians around 8,370-10,809 at h4 and
18,672-18,753 at h7. Peak bounded-batch scratch grows from roughly 19.6-20.5 MB
to 85.2-93.9 MB. Median frontier rank remains seven at h7, but tail ranks reach
93; total width, not median rank, predicts the bill.

The two-sided representation performs identical structural work for a
`2e-14`-TV synthetic edit and a material checkpoint edit. It encodes
`q_candidate` and `-q_baseline` as separate terms even though every frozen
candidate changes exactly one seat. That is the next algebraic inefficiency,
not a reason to jump directly to C++.

## Decision

1. Accept the exact clean-fringe delta identity, its candidate-reach direction,
   and the conservative certificate as reference primitives.
2. Reject the universal capped-root product under its frozen all-row gate.
3. Reject the current two-sided Python clean stream as a general hot path; keep
   the flat evaluator as the small-axis incumbent.
4. Preserve the mature-average h7 win over recomposition as the target customer,
   not as a deployable selector.
5. Before native specialization, replace the two full frontier terms by an
   exact signed single-seat reach delta and optimize the clean cutset by measured
   rank/work. Then remeasure against all three incumbents.

For a single changed seat `s`, the exact identity is

`q_candidate(f) - q_baseline(f) = (r'_s(f) - r_s(f)) * product_{j != s} r_j(f)`.

This uses one frontier term instead of two, preserves stacked same-seat edits,
and should halve component-rank width before any low-level optimization. A
multi-seat successor can use an ordered telescoping product. The frontier bound
can also tighten from `2 * max b_f` to
`sum_f E[abs(Delta q_f)] * b_f` without using future strategy labels.

## Limitations

- Four/seven-hand flat timing does not authorize 32-hand enumeration.
- The clean implementation is Python/NumPy and evaluates six value seats in
  separate calls.
- The cap test measures scalar utilities, not conditional action values or
  response identity.
- All policies come from one board and two generated range families.
- Cost-based provenance dispatch remains a hypothesis until frozen and tested.
