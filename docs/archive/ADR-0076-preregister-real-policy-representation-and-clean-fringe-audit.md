# ADR-0076: Preregister real-policy representation and clean-fringe audit

**Status:** Accepted before any canonical-source policy rank, seat-order result,
cap error, frontier bill, or candidate comparison was observed

**Date:** 2026-08-20

## Decision

Run one combined representation and fixed-policy candidate-read audit against
the immutable ADR-0075 policy artifact. The frozen configuration is
`experiments/configs/real-policy-representation-audit-v1.json`; its SHA-256 is
`fa13bc219050ca885b176fe024b2af3ce2940c40806626b7be8dcd1eb991c22f`.
The result target is
`experiments/results/real-policy-representation-audit-v1.json`.

The policy source must have SHA-256
`cdcae48dcca5fd1447fd5ad33426a4b20f04e098c88897d8f0f6eddb797ef36e`.
The audit loads its serialized policy tables; it does not regenerate, improve,
or select a source policy.

This stage has two distinct products:

1. a capped root TT may serve approximate fixed-policy value estimation and
   scheduling only if the real late-average cap gate passes; and
2. an exact clean-fringe scalar delta reader may serve guarded fixed-policy
   candidate comparison if its identity and envelope gates pass.

The first product cannot feed the second product's acceptance certificate.
Literal best responses and hash controls remain explicit-state/tape customers
regardless of their observed compression.

## Frozen geometry and policy objects

Reproduce all four source geometries: hands per seat in `{4, 7}` crossed with
range family in `{balanced, blocker_heavy}`. Each has six seats, a
three-component exact nonnegative factor belief, the same board and one-bet
385-node public tree, and the source artifact's exact hand axes and game
provenance.

For each geometry retain uniform, hashed-dense, and hashed-pure controls on the
identical schema and seed used by ADR-0067/0068. Add every own-axis DCFR average
checkpoint and every all-seat literal unilateral-response profile from the
canonical artifact.

Rank seats 0, 3, and 5 for every control and average profile. Rank the target
seat's value operator for every literal response. The frozen workload has 126
root-rank rows:

- 36 control rows;
- 66 DCFR-average rows; and
- 24 literal-response rows.

Source NashConv and checkpoint are metadata. Neither may select or veto a rank
row.

## Dense-free terminal source and small-axis oracle

Build every per-seat terminal through the exact structured showdown automaton
from ADR-0072. Deduplicate exact trains by byte digest and record production
construction separately from audit-control work.

At four and seven hands only, construct the literal Cartesian terminal tensor
and dense public-policy root as independent oracles. This is permitted because
these selected axes contain at most `7^6 = 117,649` assignments. It does not
authorize a dense 32-hand terminal or root.

The structured terminal must agree with the literal payoff operator within
`1e-12`. Tolerance-only cached root composition must agree with the dense root
within `1e-8`.

## Complete seat-order screen and capped value product

For each root row, evaluate all ten unordered 3-versus-3 seat partitions. For
each partition, evaluate all `3! * 3! = 36` within-half orders. Compute each
unique subset unfolding once and select by:

1. minimum exact TT numeric storage;
2. minimum middle rank; then
3. lexicographically smallest complete seat order.

The numerical-rank threshold is `1e-12` relative. Record the best order for
each partition, the global selected order, all five selected unfolding ranks,
the original crown/depth rank profile, and the maximum within-partition
singular-spectrum discrepancy. The selected exact TT must reconstruct within
`1e-8`; partition spectra must agree within `1e-10` relative.

Apply rank caps 8, 16, and 32 only after the exact order is selected. Reorder
the factor belief identically and contract the capped root. For every late
average row—checkpoint 256 at four hands and checkpoint 64 at seven—at least
one cap no larger than 32 must achieve both:

- payoff-normalized utility error at most `1e-4`; and
- TT numeric storage at most 25% of the dense root.

Failure rejects the capped root as the real average-policy value product. It
does not reject the terminal automaton, clean-fringe delta reader, or explicit
public-state representation. Controls and literal responses receive no cap
gate.

## Exact clean-fringe delta identity

For baseline policy `pi`, candidate `pi'`, dirty ancestor closure `D`, and its
clean public cutset `F`, evaluate each player's fixed-policy utility change as

`Delta U = sum_f E[(q_pi'(f) - q_pi(f)) V_pi(f)]`.

`q_pi'` above every changed node is load-bearing when one seat acts more than
once on a line. Baseline reach above a later overlapping edit is invalid. Unit
tests pin the candidate-reach identity against both dense composition and the
literal scalar evaluator.

No SVD or TT rounding occurs on this read path. Each nonzero frontier
contribution is represented as one positive candidate-reach term and one
negative baseline-reach term. A bounded-width stream contracts those weighted
TTs directly against the exact factor belief without materializing their
direct sum.

The fixed-policy delta certificate uses

`2 * max_{f in F_delta} b_f + eps * 256 * public_depth * payoff_span`.

The factor two follows from `sum_f |q_pi'(f)-q_pi(f)| <= 2`; the shared clean
frontier removes the cached crown's accumulated rounding debt. The certificate
does not cover best-response, Pareto, coalition, NashConv, or equilibrium
quantities.

Compose all six player deltas and report their sum as a coherent-error alarm.
Its envelope is the sum of the six frontier bounds plus six machine
allowances.

## Frozen candidate workload

For every geometry, splice each seat independently from every checkpoint into
the next checkpoint. Include the checkpoint-zero to checkpoint-one no-change
control. Against checkpoint 16, include every literal all-seat best-response
profile. These candidates span the source artifact's measured checkpoint-TV
range and the declared pure/off-path endpoint.

Add exactly two h4-balanced seat-3 controls by interpolating checkpoint 16
toward checkpoint 64:

- scale `1e-12`, which must abstain for all six deltas; and
- scale `1e-6`, which must produce at least one nonzero certificate.

The frozen workload has 134 candidate rows: 74 at four hands and 60 at seven.
No candidate is removed because it is slow, rank-heavy, zero-change, or
strategically unfavorable.

## Equal three-part evaluator bills

Compare all six player values or deltas for:

1. clean-fringe read;
2. recompose, tolerance-round, then factor-contract; and
3. the flat compatible-deal public evaluator.

Every evaluator reports a one-time compile/cache bill, a per-candidate
marginal bill, and charged totals at reuse counts
`{1, 2, 4, 8, 16, 32, 64}`. The TT one-time bill includes public layout,
card-topology compilation, structured terminals for all six value seats,
factor-belief workspace, baseline probability tape, and all six baseline node
caches. The flat one-time bill includes construction of its exact compatible-
deal evaluator. Shared hand-axis and belief generation are common setup and
excluded from both.

The clean marginal includes candidate policy-tape compilation, dirty planning,
frontier planning, term preparation, and all-six streamed contractions. The
recomposition marginal includes the same candidate and dirty planning plus
all-six recompositions and root contractions. The flat marginal evaluates all
six candidate utilities.

Exact incumbent utilities are used only to label delta error in the audit.
Their separately reported oracle time is unbilled because the online products
are compared with an already-held incumbent scalar/vector. No evaluator may
silently consume that oracle in its marginal path.

Report changed nodes, raw dirty fraction, cost-weighted dirty fraction,
frontier size, delta-support frontier size, per-seat frontier rank histograms,
total component-times-rank width, streaming batches, referenced cache bytes,
reach-factor bytes, and peak bounded-batch scratch. Per-node timing is a noisy
attribution diagnostic, not a portable CPU cost model.

There is deliberately no small-axis speed gate. The flat evaluator is expected
to be formidable at four and seven hands. A 32-hand path advances only if the
measured frontier ranks and feature widths offer a credible dense-free scaling
argument.

## Frozen gates

Require:

- structured terminal error at most `1e-12`;
- cached exact-root error at most `1e-8`;
- selected-order exact reconstruction error at most `1e-8`;
- within-partition spectrum error at most `1e-10`;
- clean-fringe fixed-policy delta error at most `1e-8`;
- recomposed fixed-policy utility error at most `1e-8`;
- zero positive frontier-bound violation;
- zero positive six-seat delta zero-sum envelope violation;
- zero false nonzero fixed-policy sign certificates;
- the late-average capped-value product described above;
- correct below/above guard behavior; and
- complete partition and reuse-bill row counts.

A failed cap, identity, bound, or guard gate is recorded as a rejection. Gates
are not relaxed after rank or timing is revealed.

## Pre-freeze engineering disclosure

Before loading any canonical-source policy rank, a hashed-policy h4 smoke test
showed that materializing a direct-sum frontier TT was the wrong implementation:
it used about 264 MB and 848 ms versus about 180 ms for recomposition. A
bounded-width feature stream reduced the prototype read to about 272 ms while
remaining slower than recomposition. This observation selected the memory-safe
streaming form and the frozen feature-width cap of 512; it did not select a
real policy, gate, seat order, rank cap, or speed threshold.

Historically frozen source modules were restored byte-for-byte after an early
instrumentation attempt triggered provenance tests. Profiling and batching now
live only in additive successor modules. The complete pre-freeze suite passes
405 tests in 55.591 seconds.

## Dissent protocol

**Confidence:** high in the delta identity and small-axis exact oracles;
moderate in the accounting decomposition; low that a capped root or fringe
stream will beat the flat incumbent on these small axes.

**Opposing evidence:** ADR-0068 found root ranks up to 202 for hashed-dense
policies, ADR-0070 found crown rounding dominates wider recomposition, and the
pre-freeze streamed hash control still lost on latency. Poker-aligned DCFR
averages may compress materially better, or their nearly unique information-
set distributions may remain effectively generic.

**Largest risk:** interpreting a favorable small-axis time as a production
win, or allowing the approximate capped product's `1e-4` error budget to leak
into a `1e-10 * span` fixed-policy acceptance decision.

**Cheapest falsification:** late real averages miss every cap-32 value/storage
gate, or whole-seat clean-fringe feature width grows enough at seven hands that
the dense-free extrapolation has no plausible advantage.
