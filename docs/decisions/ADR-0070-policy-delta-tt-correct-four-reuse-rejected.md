# ADR-0070: Policy-delta TT is correct, but four-reuse unilateral economics fail

**Status:** Implemented; seven correctness gates pass, frozen speed gate fails

**Date:** 2026-08-19

## Result and provenance

ADR-0069 corrected the reuse axis from fixed policy/varying belief to fixed
belief/varying candidate policy. One immutable policy-probability tape and one
dirty-set plan are shared across all six player-value caches. Every public-node
TT, local discarded norm, propagated bound, parent, and depth is retained.

The frozen configuration SHA-256 is
`089f0d9e7590bd38ce1eaea17e1ae86a6075385390cac6267a63141cb4c135d3`.
The result is
`experiments/results/policy-delta-tt-recomposition-audit-v1.json`, SHA-256
`6ee324e265b018841d3cf16a4ae5e5954a98cb86a9201f05ba2359d63717a27b`.
It ran from clean commit
`a5cbd3696132dd380c91ecdf931b08f78de6dcd6` in 83.991 seconds. All 378
tests passed in 52.868 seconds before the frozen run.

## Correctness and bounds pass

The cache is implementation-correct:

- maximum incremental-versus-cold root error: exactly `0.0`;
- maximum incremental-versus-dense utility error: `2.838e-13`;
- maximum dense-root error: `1.002e-11`;
- positive truncation-plus-machine bound violations: `0`;
- maximum six-seat zero-sum residual: `4.098e-13`;
- positive zero-sum envelope violations: `0`; and
- every one-node mutation dirties exactly its node and ancestor path.

The largest observed root bound is about `1.07e-9`; the frozen per-root
machine allowance is `1.876e-11`. The largest zero-sum envelope is about
`4.97e-9`. The bounds are conservative on this workload but not absurdly large
relative to the fixed `3e-9` comparison tolerance.

All 120 fixed-policy utility deltas clear the guard: 70 positive and 50
negative, with zero wrong signs against dense oracles. This does not exercise
the abstention boundary. It certifies only the sign of a per-seat fixed-policy
expected-utility delta. It does not certify best responses, Pareto constraints,
coalition quantities, NashConv, or multiplayer equilibrium acceptance. An
upper-bound constraint also needs its own sign-flipped inequality audit.

The Float64 allowance is validated only at four and seven hands. At 32 hands it
would be an extrapolation. The all-seat zero-sum residual becomes a mandatory
runtime health alarm at scale, but it is not a certificate: seat errors can
cancel in the sum.

## Dirty locality is real

| Candidate edit | Changed strategic nodes | Dirty nodes | Pooled raw speedup |
|---|---:|---:|---:|
| one root-hand distribution | 1 | 1 | `6.34x` |
| one deepest-hand distribution | 1 | 11 | `1.64x` |
| all hands at one deepest node | 1 | 11 | `1.58x` |
| every seat-3 information set | 32 | 63 | `1.33x` |
| full hashed-dense profile | 192 | 192 | `1.03x` |

There are 192 strategic nodes and 193 terminals in the 385-node public tree.
The seat-3 edit therefore skips 129 of 192 strategic recompositions. It is not
a single path; its 63-node dirty set is the union of 32 ancestor paths.

The result also exposes the remaining bottleneck. At seven hands, skipping
67.2% of strategic nodes yields only a `1.20x` raw speedup. Upper-tree TT sums
and QR/SVD rounds, especially the root, dominate cost. Node locality alone does
not make recomposition proportional to dirty-node count.

The crown localization is sharper:

| Seven-hand family | Root-only / cold | Eleven-node crown path / cold |
|---|---:|---:|
| balanced | `17.09%` | `69.13%` |
| blocker-heavy | `19.75%` | `72.01%` |

Thus 2.86% of all public nodes can consume about 70% of a cold composition.
Every dirty closure contains the expensive crown. Direct-sum ranks add before
rounding and QR/SVD cost is superlinear in those ranks, so raw node count is a
poor work proxy. The recorded root output middle ranks are 53-64 at four hands
and 106-244 at seven: 185-244 on balanced axes and 106-211 on blocker-heavy
axes. This strongly warns against favorable 32-hand reuse extrapolation, but it
does not measure one; real solver policies may have materially smaller crown
ranks than the hashed-dense control.

## Four-reuse gate fails

The frozen amortized cost is

`incremental candidate + baseline cache compilation / reuse_count`.

| Hands | Family | Raw speedup | Amortized speedup at four reuses |
|---:|---|---:|---:|
| 4 | balanced | `2.54x` | `1.53x` |
| 4 | blocker-heavy | `2.68x` | `1.61x` |
| 7 | balanced | `1.20x` | `0.92x` |
| 7 | blocker-heavy | `1.20x` | `0.92x` |

Pooled cold recomposition costs `4785.817 ms`; charged incremental costs
`4825.328 ms`. The frozen speedup is `0.99181x`, so the gate fails by 39.511 ms
or 0.82%. This is a real frozen rejection even if a timing repeat could cross
one. Both seven-hand cases miss by roughly 8%, showing that the underlying
wide-axis issue is not merely the pooled timing margin.

The exact integer break-even is two reuses for both four-hand cases and seven
reuses for both seven-hand cases. All four cases pass at the next frozen report
point, eight reuses. Persistent-cache memory is not the blocker: the maximum
six-player baseline cache is 48.20 MB of numeric storage, and the maximum
simultaneous baseline-plus-candidate footprint is 94.55 MB. Python object
overhead is excluded.

## Read/write split for the successor

Recomposing and rounding a root TT is a cache-write operation. The acceptance
customer initially needs only a scalar fixed-policy utility delta. The
successor must therefore compare the current round-on-every-read path with an
exact clean-fringe contraction that performs no candidate-time TT rounding.

Let `F` be a public cutset at the clean fringe of the dirty induced tree. For a
private hand tuple `h`, candidate public reaches `q'_f(h)` are nonnegative and
sum to one over `f in F`. Each reach is a product of per-seat hand unaries and
can be folded into the exact factor belief. If cached fringe value `V_hat_f`
has sup-norm error at most `b_f`, then

`abs(U_hat_candidate - U_candidate) <= max_f b_f`.

Evaluate the baseline through the same cutset and subtract. The shared-fringe
delta has error at most

`E_b[sum_f abs(q'_f - q_f) b_f] <= 2 * max_f b_f`.

This removes every new crown-rounding term. A tighter reach-weighted bound may
be reported, but the `2 * max` bound is the simple certificate. If a candidate
is accepted and becomes the new baseline, compose and round once on the write
path and amortize that cost over its lifetime.

This algebra does not guarantee a latency win. A naive implementation launches
one factor-TT contraction per fringe term and could merely exchange expensive
SVDs for too many contractions. Prefix reach products, compatible-card
incidence, six player targets, and mutually exclusive public branches must be
batched. The successor gate is read-path scalar delta time versus
recompose-then-contract on identical whole-seat candidates, not composition
time alone.

For unilateral same-seat edits, a hybrid-policy telescoping expansion is also
exact. The one-bet tree limits repeated same-seat action products on one line,
but overlapping ancestor/descendant edits still require their cross terms. Use
either a cutset evaluation or an explicitly verified telescoping order; do not
sum independent single-node effects as though they were additive.

The successor must additionally report:

- dirty-node fraction;
- measured dirty cost divided by measured cold cost;
- a pre-evaluation cost proxy based on cached raw/output ranks and core sizes;
- clean-fringe term count and batched contraction feature work; and
- crown ranks by policy provenance.

It must include deterministic near-guard controls. Interpolate one root-hand
swap to place fixed-policy deltas below and above the guard, then require the
expected abstention/certificate decisions against the dense oracle. ADR-0069's
120 large mutations all cleared the guard and therefore did not exercise
abstention.

## Decision

Accept persistent node caches and shared dirty plans as exact primitives for
local insertion/edit search and for candidate batches with enough reuse. Reject
the current Python tolerance-only cache as a four-reuse unilateral acceptance
evaluator on seven-hand axes. Do not relabel the `0.99181x` result as a pass or
change the reuse gate after seeing it.

Do not optimize the rejected global root TT blindly. First remove the known
wide-axis construction blocker by building exact dense-free showdown terminals.
For one target player and contender set, carry the finite-state bond

`(running maximum strength, maximum multiplicity, target in argmax)`

across seat modes, with an empty-contender sentinel. Close with the target's
winner share and add sunk contributions as a separate rank-one tensor. Check
the automaton against the existing four/seven-hand dense oracle before using it
at 32 hands.

After that control, widen the representation audit with actual policy
provenance: DCFR average checkpoints and literal best responses. Averages and
BRs may deserve different representations. The selector is legal because
policy provenance is declared at construction rather than learned from future
labels.

Within-axis strength sorting is useful for monotone automaton transitions and
possibly construction/cache locality, but it cannot improve ordinary TT-SVD
ranks or optimal cap error. A permutation within each mode only permutes rows
and columns of every unfolding, leaving its singular values invariant. Record
this as an invariant control. Seat elimination order can still change cuts and
remains a legitimate later screen.

## Dissent protocol

**Confidence:** very high in cache identity and dirty semantics; high in the
small-axis bound validation; high that upper-tree rounding dominates the
seven-hand economics; moderate in Python timing transfer.

**Opposing evidence:** raw seat-wide recomposition is already `1.20x` faster at
seven hands and amortizes after seven candidates. Native incremental
factorizations could move the crossover substantially.

**Largest risk:** mistaking fixed-policy sign checks and a zero-sum alarm for
best-response or equilibrium certification.

**Cheapest falsification:** an exact structured-terminal construction that
matches dense payoffs but still makes realistic DCFR-average root policies
incompressible under every seat cut.
