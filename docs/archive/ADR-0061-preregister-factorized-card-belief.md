# ADR-0061: Preregister exact factorized-card belief audit

**Status:** Accepted before factor-belief implementation or timing

**Date:** 2026-08-19

## Decision

Before fitting a generic low-rank tensor to a poker range, test the exact
representation implied by the game. Represent a joint private-card belief as

\[
  w(h_1,\ldots,h_n)
  = \mathbf 1[\text{all cards disjoint}]
    \sum_{z=1}^{R} \alpha_z \prod_{i=1}^{n} u_{z,i}(h_i),
\]

where every coefficient and unary factor is nonnegative. Rank `R=1` is the
ordinary independent deal prior conditioned on card removal. `R>1` is an
explicit latent mixture for opponent-model uncertainty or other declared
correlation. Card compatibility remains an exact constraint outside the
mixture; it is never learned or softened.

Prove the implementation against explicit joint enumeration, then benchmark an
exact meet-in-the-middle partition and marginal contraction based on card-mask
inclusion-exclusion. Only if this exact family is insufficient should the next
screen spend time on truncated tensor trains or fitted nonnegative CP models.

The frozen configuration is
`experiments/configs/factorized-card-belief-audit-v1.json`. The result target is
`experiments/results/factorized-card-belief-audit-v1.json`.

This is revealed representation engineering. It cannot select a poker
strategy, solver, scheduler, neural model, approximation rank, or deployment
threshold. No validation or test data is authorized.

## Exact closure under public actions

For a fixed behavioral profile, the likelihood of a public action by player
`i` depends only on that player's private hand and the public history:

\[
  \Pr(a\mid h_1,\ldots,h_n,H)
  = \sigma_i(a\mid h_i,H).
\]

Bayesian conditioning therefore multiplies every mixture component's unary
factor for player `i` by the same likelihood vector. Products of later public
actions can be folded into their respective seat factors. Public-board
conditioning is an exact hand-validity mask; known hero cards are a delta unary
factor. The representation is closed without approximating the blocker-induced
correlation.

This statement assumes ordinary perfect-recall behavioral policies. A policy
controlled by shared private information, a colluding team, or an unrepresented
shared latent variable need not factor by seat. Such a model must add an
explicit component or higher-order factor; it must not be smuggled into a
"nearby range" cache.

## Why generic tensor truncation waits

Tensor trains can reduce storage when unfolding ranks remain small, but
ordinary TT-SVD uses signed cores and a truncated reconstruction need not be a
nonnegative normalized distribution. Nonnegative tensor models exist, but add
optimization and representation tradeoffs. The first question is therefore
not whether an arbitrary dense range has a small numerical rank. It is whether
standard poker inference already supplies a smaller exact object.

Relevant primary references include the original
[tensor-train decomposition](https://epubs.siam.org/doi/10.1137/090752286),
[nonnegative tensor approximation as a latent mixture](https://arxiv.org/abs/0903.4530),
and [TT inference for graphical models](https://proceedings.mlr.press/v32/novikov14.html).
They motivate later alternatives but do not establish poker-specific strategic
safety.

## Frozen workload

Generate deterministic hand axes on the fixed board `2c 7d 9h Js Qc`.
`balanced` ranges spread each seat across the available hand-strength order.
`blocker_heavy` ranges deliberately reuse a small set of private cards across
seats and therefore create many incompatible Cartesian assignments. Every
selected hand must occur in at least one compatible full assignment.

### Exact closure matrix

Cross:

- two through six players;
- two and four hands per player;
- balanced and blocker-heavy axes; and
- one and three nonnegative mixture components.

This yields 40 cases. For every case:

1. materialize the initial normalized joint distribution two ways;
2. apply two deterministic positive SHA-256 likelihood updates per player to
   both the factor object and the explicit joint oracle;
3. condition player zero on its first supported hand in both paths;
4. compare the complete normalized support and probability vector;
5. compare the partition function and all per-seat marginals from recursive
   enumeration and meet-in-the-middle contraction; and
6. verify exactly zero probability on every card-incompatible assignment.

The likelihood rule maps the frozen digest to one of 31 values in `(0, 1]`.
It is an observed-action likelihood over hands, not a range normalization.

### Six-player contraction timing

At four, seven, and ten hands per seat, in both range families, use exactly
three mixture components. Time recursive enumeration and balanced contiguous
meet-in-the-middle partition-plus-all-marginal contraction after one warmup;
report median and minimum over three repeats. At ten hands, meet-in-the-middle
must be strictly faster than recursive enumeration in the pooled two-family
median sum.

### Wider nonmaterialized slice

At 16, 24, and 32 hands per seat, use six players, both range families, and
three components. Do not materialize the `h^6` joint tensor. Contract once with
the contiguous `3+3` split and once with alternating seats. Require normalized
partition and marginal agreement within the frozen relative tolerance.

The exact contraction uses a colored-matching identity. Enumerate compatible
assignments inside each half. For every right-half assignment, accumulate its
weight under every subset of its used cards. For a left mask `L`, the compatible
right weight is

\[
  \sum_{S\subseteq L} (-1)^{|S|}
  \sum_{r:\,S\subseteq\operatorname{cards}(r)} w(r).
\]

Each half contains at most three hands and therefore six cards, so every query
has at most 64 inclusion-exclusion terms. Use Float64 storage and `math.fsum`
for the signed sum. Marginals are obtained by repeating the contraction with
the halves exchanged; no approximate message passing is permitted.

## Frozen gates

Require:

- initial and post-update complete-distribution error at most `1e-12`;
- partition and marginal error at most `1e-10` against explicit enumeration;
- wide split replay relative error at most `1e-10`;
- exactly zero incompatible-assignment probability and zero support mismatches;
- contiguous Float64 weights and unsigned 64-bit card masks;
- pooled ten-hand meet-in-the-middle time strictly below recursive time;
- at 32 hands per seat, persistent factor bytes at most `1e-6` of an explicit
  dense `32^6` Float64 joint tensor; and
- fewer materialized compatible half-records than `32^6` Cartesian full
  assignments.

Report persistent factor bytes, half-record numeric bytes, incidence-table
entry counts, candidate Cartesian assignments, compatible assignments, and all
timings separately. Python dictionary overhead must not be hidden inside the
numeric-byte count; report entry counts so its omitted cost remains visible.

## Branching interpretation

- If closure or exactness fails, stop. A low-rank approximation cannot build on
  an incorrect poker prior/update model.
- If closure passes but meet-in-the-middle loses at ten hands, retain the
  factor representation and profile contraction ordering before widening it.
- If every gate passes, integrate factor beliefs with public-tree value
  contraction. Separate online value/action cost from offline unilateral
  certification.
- Only introduce TT, nonnegative CP fitting, sampling, or neural compression
  for a measured residual: high-order correlation factors or payoff/value
  contractions that the exact unary-plus-compatibility representation does not
  make cheap.

## Dissent protocol

**Confidence:** very high in closure under ordinary behavioral policies; high
in exact small-case reproducibility; moderate that inclusion-exclusion beats a
well-vectorized dense native kernel at realistic supports.

**Opposing evidence:** exact factor storage can be tiny while exact contraction
remains exponential in player count or factor-graph treewidth. This experiment
does not yet contract showdown payoff or a neural leaf.

**Largest risk:** solving belief storage but leaving the expensive value
operator untouched, then reporting the storage ratio as decision speed.

**Cheapest falsification:** any mismatch after a public likelihood update, any
nonzero incompatible mass, or a ten-hand contraction that cannot beat direct
enumeration.
