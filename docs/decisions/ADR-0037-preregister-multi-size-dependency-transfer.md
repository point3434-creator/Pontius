# ADR-0037: Preregister multi-size dependency-tape transfer

**Status:** Accepted before the frozen development run

**Date:** 2026-08-19

## Decision

Run one matched development-only experiment to test whether the unchanged flat
dependency tape retains exactness and useful sparse invalidation after widening
the river betting tree from one bet/one raise to three bets/two raises. Commit
the game, payoff audit, runner, tests, configuration, and this record before
generating the result.

The frozen configuration is
`experiments/configs/river-multi-size-dependency-development-v1.json`, SHA-256
`0246924028a0ed572b0cd8dad94112e44f7ad8e4c8266af53ba5323b516bb52c`.
The result target is
`experiments/results/river-multi-size-dependency-development-v1.json`.

## Immutable implementation boundary

The experiment records and gates the SHA-256 of
`src/pontius/dependency_tape.py` as
`5fc1b645bb7aa17d108bf0b817ba13736332bf5b90dac83edeac691a520f8c8f`.
Changing even one byte of that evaluator invalidates the transfer claim. The
multi-size game must adapt to the generic interface; the generic tape is not
allowed a workload-specific branch.

The seed-`5`, three-hand balanced run is an implementation pilot and cannot
count toward the frozen result. It exposed one literal action-label difference
at an unreachable tied information set with zero pure-response value loss. This
observation fixes the tie protocol below before the fresh seed is evaluated.

## Frozen matched workload

Use fresh seed `20260919`, request 12 board groups, materialize only development
groups, and cross all four existing joint-range families with five private hands
per player. Every range is instantiated in two betting structures:

1. `fixed_single`: bet `0.5P`, with one raise to `1.5P`; and
2. `multi_size_3x2`: bets `0.25P`, `0.5P`, and `0.75P`, with raises to `1.5P`
   and `2.0P` after every bet.

The fixed tree is a literal action subset of the wide tree. Both use identical
board, pot, stacks, cards, and joint probabilities. At finite DCFR checkpoints
1, 4, and 16, compile a source-policy tape over the same five target-range
families used by ADR-0034: two player-specific blocker reweights, two unseen-
hand support swaps, and one player-zero factorized likelihood update.

The sparse updates use root-TV budget `0.01` and maximum donor fraction `0.75`.
The dense likelihood multipliers span `0.5` through `1.5`. Automatic execution
uses the existing dirty-node threshold `0.35`.

## Independent controls

For both shapes, compare source and target tape values with the generic
object-tree evaluator and separately reconstruct exact dynamic best-response
actions. Run every target explicitly through sparse, dense, and automatic tape
modes. The fixed shape additionally matches the specialized river incremental
evaluator.

For every wide source and target range, enumerate all 19 legal terminal betting
histories per deal and compare state returns with the independent
contribution-based payoff audit. After all five recertifications, repeat the
first target from the immutable source epoch.

Literal action disagreements are always recorded. They fail only when the
tape-selected complete pure response loses more than `1e-10` against an exact
object-tree evaluation relative to the exact best-response value. This permits
only numerically tied or unreachable choices; it does not accept a merely small
value error silently. Sparse, dense, and automatic selector maps must still be
identical to one another.

## Frozen gates

The run passes only if:

1. the dependency-tape source hash exactly matches the frozen hash;
2. maximum source or target evaluation error is at most `1e-10`;
3. maximum exact value loss from any literal best-response action disagreement
   is at most `1e-10`;
4. every independently audited terminal payoff is bit-identical, all 19 legal
   terminal histories per deal are present, and maximum audit error is zero;
5. every dependency is topological and source-relative replay has exactly zero
   value or selector drift;
6. the maximum dirty fraction over blocker and support-change targets is at most
   `0.35`;
7. automatic mode chooses sparse execution for at least 95% of sparse targets;
   and
8. automatic mode chooses dense execution for every factorized-dense target.

A payoff, evaluation, source-hash, topological, or action-value failure blocks
the architecture. A sparse-cone failure rejects sparse invalidation as the main
branching-tree advantage but may retain the unchanged tape as a dense exact
control. A mode-selection-only failure preserves arithmetic correctness and
requires a new threshold study.

## Measurements, not gates

Report matched wide/fixed ratios for compiled tree states, numeric nodes,
dependency edges, selector nodes, and contiguous bytes. For each update family,
report both dirty fraction and absolute dirty/recomputed node ratios. A falling
dirty percentage can conceal rising absolute work when the whole tree expands;
both are required for an honest quality-per-millisecond architecture decision.

Record selector flips, checkpoint, family, changed deals, total variation, and
complete perturbation provenance. Do not gate a topology ratio: the experiment
is meant to reveal the branching cost rather than reward a predetermined size.

Wall time mixes DCFR, compilation, three tape paths, independent full and
specialized controls, payoff audits, repeated best responses, and JSON. It is
provenance only and cannot support an online latency or speedup claim.

## Dissent protocol

**Confidence:** high in the payoff and differential exactness controls;
moderate that two-deal dirty fractions stay below 35%; low that a one-raise
heads-up result transfers to six-player no-limit trees.

**Opposing evidence:** the pilot's wide tape already tripled numeric nodes and
roughly tripled absolute dirty work even though dirty percentages fell. Multiple
sizes create many more information-set selectors, so localized root changes can
remain sparse in percentage terms while becoming too expensive in milliseconds.

**Largest unknown:** the absolute work multiplier after branching, and whether
that multiplier leaves enough headroom for selective repair versus a dense flat
pass.

**Cheapest falsification:** on the fresh seed, observe any exactness/payoff
failure or a sparse dirty fraction above `0.35`. Either result prevents moving
directly to an optimized kernel.
