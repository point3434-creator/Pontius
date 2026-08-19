# ADR-0034: Preregister the generic dependency-tape differential matrix

**Status:** Accepted before the frozen development run; passed in ADR-0035

**Date:** 2026-08-19

## Decision

Run one development-only differential matrix to decide whether the generic flat
dependency tape satisfies ADR-0033's correctness and execution-mode contract.
Commit the runner, tests, configuration, and this record before producing the
result artifact. Do not use this run to select a deployment acceptance budget,
claim an optimized latency, or expose validation/test contexts.

The frozen configuration is
`experiments/configs/dependency-tape-differential-development-v1.json`, SHA-256
`b6c474d269fa86f0aa8512195ad9f842d9ed219ae1fe56c1f4504729de49ceb5`.
The result target is
`experiments/results/dependency-tape-differential-development-v1.json`.

## Frozen matrix

Use deterministic seed `20260907`, request 12 board groups, materialize only
groups assigned to the development split, and cross all four existing joint-
range families with both current river shapes: one bet with no raise and one
fixed sequential raise. Each range has five private hands per player.

At finite DCFR checkpoints 1, 4, and 16, compile a new source-policy tape over
the union of five target supports:

1. a two-deal blocker reweight for player zero;
2. a two-deal blocker reweight for player one;
3. an unseen-hand support swap for player zero;
4. an unseen-hand support swap for player one; and
5. a support-preserving factorized likelihood update over player zero's hand.

The blocker updates have root-TV budget `0.01` and may move at most `0.75` of a
donor deal. The factorized likelihood multipliers span `0.5` through `1.5`.
Automatic execution switches from sparse compaction to a dense topological
sweep at dirty-node fraction `0.35`.

The earlier seed-`7331` matrix was an implementation pilot and is not evidence
for these gates. It fixed the measurements worth retaining but cannot be
counted as the frozen replication.

## Independent controls

Every source and target fixed policy is evaluated by the generic object-tree
evaluator. Every target is also evaluated by the separately implemented,
river-specific incremental recertifier. For every target, the generic tape is
run explicitly in sparse, dense, and automatic modes. Exact full best-response
actions are reconstructed separately for every player.

After evaluating all five targets, the first target is evaluated again from the
immutable source epoch. This makes accidental target-to-target chaining or
call-order drift observable.

## Frozen gates

The run passes only if all of the following hold:

1. maximum absolute error is at most `1e-10` across source and target utilities,
   best-response values, deviation gains, NashConv, and exploitability;
2. source, sparse, dense, and automatic best-response actions match the exact
   full evaluator on every information set reached by the corresponding game;
3. sparse, dense, and automatic tape actions are mutually identical, including
   compiled zero-source support entries;
4. every dependency points from a lower topological index to a higher one;
5. repeating the first target after intervening targets preserves values and
   complete selector maps;
6. automatic mode chooses sparse execution on at least 95% of the four sparse
   target families; and
7. automatic mode chooses dense execution on 100% of factorized-dense targets.

The last two gates validate the declared hybrid policy on this workload; they
do not establish the optimized crossover. A failure of an exactness, action,
topology, or source-relative gate blocks wider-tree work. A failure of only an
automatic-mode gate changes the threshold or mode-selection design but does not
invalidate the arithmetic tape.

## Recorded diagnostics

Record node and edge counts, contiguous runtime bytes, changed-root fraction,
dirty-node fraction, sparse and dense recomputation fractions, selector flips,
tree shape, range family, checkpoint, and perturbation provenance. Summaries
must keep sparse reweight, sparse support, and factorized-dense updates separate.

Wall time is provenance only. Python compilation, full evaluation, duplicated
control calls, and JSON construction are intentionally mixed in this runner, so
no latency or quality-per-millisecond conclusion may be drawn from it.

## Limits and next decision

This remains two-player river hold'em with root-only chance, at most one fixed
raise size, and an explicitly enumerated outcome universe. It does not test
multiple bet sizes, multiple raises, action-conditioned belief updates, a
six-player joint range, C++ layout, SIMD, or online repair.

If the gates pass, widen the legal betting tree while keeping this tape and the
full evaluator as controls. Cross at least three initial bet sizes and two raise
sizes before optimizing the kernel. If dirty cones become effectively dense,
retain the flat tape as an exact dense evaluator and shift the efficiency attack
from sparse invalidation to factorized belief algebra and topology sharing.

## Dissent protocol

**Confidence:** high in exact identity on the frozen river shapes; moderate in
the sparse/dense classifier; low in transfer to a branching six-player tree.

**Opposing evidence:** best-response selector changes may invalidate large
ancestor cones, explicit support unions can multiply memory, and a factorized
Bayesian update can be dense despite having a compact parameterization.

**Largest unknown:** whether wider action trees preserve enough localized
dependency structure to beat an optimized dense bottom-up pass.

**Cheapest falsification:** fail any exact-control or topological gate on the
fresh seed, or observe that sparse two-deal changes already trigger dense mode
on more than 5% of records.
