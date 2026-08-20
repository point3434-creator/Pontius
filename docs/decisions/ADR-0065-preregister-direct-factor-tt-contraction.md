# ADR-0065: Preregister direct factor–TT contraction audit

**Status:** Accepted before contraction implementation or labels

**Date:** 2026-08-19

## Decision

Test the missing operation between ADR-0062 and ADR-0064: contract an exact
nonnegative factorized card belief directly with a signed tensor-train payoff
operator, without constructing either the `h^6` probability tensor or the
`h^6` value tensor.

Compile three separately reusable layers:

1. board/hand-axis card-mask topology, independent of probabilities and values;
2. one belief workspace containing half-range products and its exact compatible
   partition; and
3. one signed operator pass containing TT half vectors and a widened incidence
   table.

The frozen configuration is
`experiments/configs/factor-tt-direct-contraction-audit-v1.json`. The result
target is
`experiments/results/factor-tt-direct-contraction-audit-v1.json`.

This is a preregistered revealed-engineering audit. It may advance or reject the
direct contraction kernel. It cannot approve rank 8 on full poker ranges,
approve a strategy, or make an online latency claim from Python timings.

## Exact network

For six hands `h=(h_0,...,h_5)`, mixture component `z`, compatibility `C`, and
TT payoff `V`, evaluate

`E[V] = sum_h C(h) V(h) sum_z alpha_z product_i u[z,i,h_i] / Z`,

where `Z` is the same sum without `V`.

Split the seats contiguously after seat two. For each compatible three-seat
assignment, contract the corresponding three TT cores to the middle bond. A
right record contributes its right-bond vector multiplied by each mixture
component's right unary product. Accumulate those signed features under every
subset of the record's six-card mask. For a left record, inclusion–exclusion
over its card-mask subsets returns exactly the sum of right features with no
shared card. Dot that result with the left TT vector, left unary products, and
mixture weights.

At three mixture components and middle rank eight, the per-operator incidence
width is 24 Float64 values. The component-only incidence table used for `Z` is
compiled once into the belief workspace and is not rebuilt for each operator.

## Data-oriented topology

The topology compiler must produce contiguous integer arrays:

- compatible left and right half-assignment hand indices and card masks;
- right-record-to-incidence-entry IDs for all 64 used-card subsets; and
- left-query incidence IDs and inclusion–exclusion signs.

No Python object graph may be traversed in the numeric hot pass. A dictionary is
allowed while assigning compact incidence IDs during topology compilation, but
not for operator accumulation or query. Numeric accumulation uses Float64. The
audit reports topology bytes, belief-workspace bytes, operator-table bytes,
query scratch, and estimated peak bytes separately.

## Frozen literal-payoff slice

Use the fixed board `2c 7d 9h Js Qc`, six seats, the deterministic balanced and
blocker-heavy axes, four/five/seven hands per seat, and one- and three-component
beliefs. Test these preselected group/player pairs:

1. all-check, player 0;
2. sole contender 0, player 0;
3. contenders 0 and 5, player 0;
4. contenders 0, 2, and 5, player 2;
5. all six contenders, player 4; and
6. contenders 1, 3, and 5, folded player 0.

For rank 8 and untruncated TT-SVD separately:

- compare direct contraction with explicit compatible-deal expectation of the
  reconstructed TT;
- compare the untruncated expectation with the literal dense payoff;
- report rank-8 literal payoff error as a diagnostic; and
- report middle rank, contraction feature width, cancellation ratio, work, and
  memory.

The seven-hand rows are new evidence. Rank-8 literal error there cannot be
turned into a gate or used to retune the rank after labels are visible. The
kernel is correct when it contracts the supplied TT; representation accuracy is
a separate question.

## Frozen scaling slice

At 4, 7, 10, 16, 24, and 32 hands per seat, use deterministic signed rank-8 TT
controls and three-component beliefs for both range families. These controls
test the contraction kernel at known fixed rank without requiring a dense
showdown tensor.

For up to ten hands, compare the cached direct pass with explicit compatible
joint enumeration plus batched TT evaluation. At wider sizes, run only the
direct path and report topology compilation, belief compilation, hot operator
time, feature updates, and peak numeric bytes. Use one warmup, three measured
repeats through ten hands, and one wide measured repeat.

Timing scopes are immutable:

- topology compile: half enumeration plus incidence-ID compilation;
- belief compile: half unary products, component incidence, and partition;
- hot operator: TT half contraction, signed incidence accumulation, queries,
  and normalized expectation; and
- enumerated joint: explicit compatible distribution plus batched TT values.

The hot scope may reuse topology and belief workspace but not an operator table
or result from a prior repeat.

## Frozen gates

Require all of the following:

- maximum compatible-partition relative error at most `1e-10`;
- direct versus explicitly reconstructed-TT expectation error at most `1e-10`;
- untruncated direct versus literal payoff expectation error at most `1e-9`;
- synthetic direct versus enumerated-joint expectation error at most `1e-10`;
- at 32 hands, topology + belief workspace + TT + peak operator workspace at
  most `0.01` of one dense Float64 `32^6` operator;
- pooled ten-hand hot operator time strictly below pooled enumerated-joint time;
- contiguous fixed-dtype numeric topology; and
- demonstrated reuse of the same topology across beliefs/operators and the same
  belief workspace across multiple operators.

The ten-hand speed gate establishes a crossover, not an online target. Report
each family separately even though the gate is pooled.

## Interpretation branches

- If direct/reconstructed identity fails, fix contraction semantics or signed
  summation before interpreting speed.
- If untruncated/literal identity fails, fix payoff construction or TT-SVD
  controls.
- If rank 8 acquires material literal error at seven hands, retain the kernel
  but reopen operator representation: adaptive exact rank, shared structured
  winner operators, or neural residuals.
- If exactness passes but the ten-hand crossover fails, the Python layout has
  not justified a native kernel yet; profile feature accumulation and queries
  before C++ work.
- If memory fails at 32 hands, independent per-operator incidence tables erase
  the compression win; test batched/shared contender structure instead.
- If all gates pass, lift the contraction through fixed public policies before
  attempting conditional hand values or best responses.

## Dissent protocol

**Confidence:** high in the algebra and exact small-axis oracle; moderate in the
NumPy data layout; low that scalar expectation timing predicts full resolving.

**Opposing evidence:** one scalar operator is much cheaper than the many
conditional values required by CFR or unilateral response certification.
Card-subset incidence may dominate even when TT rank is small.

**Largest risk:** celebrating a fast scalar dot product while the later
per-hand/action value lift multiplies its cost beyond usefulness.

**Cheapest falsification:** any direct/reconstruction mismatch above `1e-10`,
or a 32-hand rank-8 operator pass whose peak numeric footprint exceeds 1% of the
dense operator it replaces.
