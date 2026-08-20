# ADR-0059: Preregister exact public-tree quotient control

**Status:** Accepted before quotient implementation or timing

**Date:** 2026-08-19

## Decision

Compile the deal-invariant public betting tree once, store private deals on one
contiguous axis, and evaluate fixed policies plus every unilateral best response
with Float64 tensor operations. Compare this exact public-tree quotient with
ordinary object traversal and the source-compiled dependency tape before trying
any factorized or low-rank belief approximation.

The frozen configuration is
`experiments/configs/multiway-public-tree-quotient-audit-v1.json`. The result
target is
`experiments/results/multiway-public-tree-quotient-audit-v1.json`.

This is a revealed representation-engineering audit. It may select an exact
evaluator primitive. It may not select a solver, strategy, scheduler,
approximation rank, acceptance rule, or online deployment threshold, and it may
not materialize validation or test groups.

## Why this control comes first

The current dependency tape repeats the same public betting subtree for every
joint private deal. Source-tape reuse removes repeated compilation across range
updates, but it does not remove this within-tape structural duplication. A
factorized experiment performed directly against that tape would confound two
effects:

1. quotienting identical public nodes; and
2. approximating the joint belief.

The first effect can be exact. It must be measured and retained as the control
so a later compression method receives credit only for work it actually saves.

## Frozen semantics

For each game, enumerate the normalized positive joint support in its canonical
order. Compile exactly one post-chance public tree. At every public decision
node, gather the acting player's behavioral probabilities by `(own hand,
public history)`; do not merge hands or histories. Terminal tensors contain the
literal multiway payoff for every deal.

For player `i`'s best response:

- propagate chance and every opponent's reach forward while excluding player
  `i`'s own behavioral reach;
- solve target information sets bottom-up;
- sum each action's continuation over deals sharing the same private hand,
  weighted by that counterfactual reach;
- use legal-action order for exact ties; and
- return the same literal information keys and actions as the ordinary perfect-
  recall evaluator.

All numeric probability, reach, payoff, and value tensors must be C-contiguous
Float64 arrays. Integer hand indices may use a contiguous integer dtype. No
Float32, approximate summation, range-distance cache hit, hand bucket, policy
interpolation, truncated factor, or changed acceptance tolerance is authorized.

## Frozen workload

Use two complementary revealed slices.

First, reproduce the disjoint three-player calibration game on the fixed board
`2c 7d 9h Js Qc`, pot `12`, stacks `30`, and bet `3`, with one through seven
hands per seat. The exact joint-deal counts must be `h^3`. This clean slice
isolates scaling without card-conflict sparsity.

Second, for each of three, five, and seven hands per seat, generate group zero
at seed `20260819` in all four existing range families: balanced, polarized,
blocker-stress, and explicitly correlated. Only the development split is
allowed. These twelve games test card removal, uneven support, blocker overlap,
and non-product joint weights.

Evaluate three deterministic policy families in every game:

1. missing-table uniform policy;
2. positive dense weights derived from SHA-256 of the complete information key
   and action; and
3. a pure action selected by the same digest.

The pure arm deliberately creates zero opponent reach and unreachable target
information sets. It is an exactness stressor, not a strategy candidate.
`hashed_dense` is the sole timing policy. Time ordinary profile evaluation,
dependency-tape compilation and hot dense recertification, quotient
compilation, and hot quotient evaluation separately after one warmup; report
the median and minimum of three repeats. Action-map checks are outside the
timed ordinary call because ordinary `evaluate_profile` already computes the
same best responses internally and discards only their maps.

## Frozen correctness gates

Across all games and policies require:

- maximum error over utilities, best-response values, deviation gains, and
  NashConv at most `1e-10` against ordinary traversal;
- zero literal best-response action mismatches;
- zero information-key/action-schema mismatches;
- identical public topology for every deal in a game; and
- C-contiguous Float64 numeric tensors.

The quotient must expose enough topology and memory metadata for these claims
to be tested rather than inferred.

## Frozen engineering gates

On the seven-hand disjoint row require:

- persistent quotient numeric bytes at most `0.05` times dependency-tape
  contiguous runtime bytes;
- quotient compilation strictly faster than dependency-tape compilation;
- hot quotient evaluation strictly faster than hot dense tape
  recertification; and
- hot quotient evaluation strictly faster than ordinary traversal.

Report every row even if an aggregate gate fails. Small rows are allowed to
lose because fixed NumPy dispatch cost can dominate there. Do not change the
gate to a crossover selected after timing.

Persistent bytes and hot scratch bytes must be reported separately. The
persistent-byte comparison is a numeric-layout comparison, not a claim about
Python object overhead or native allocator residency.

## Branching interpretation

- Any numerical, action, schema, or topology mismatch stops the factorization
  branch until corrected.
- If exactness passes but the largest-row timing or memory gates fail, retain
  the dependency tape and profile the quotient implementation before testing
  approximation.
- If every gate passes, make the quotient the enumerated oracle for a separately
  frozen structured-belief screen. That screen must compare exact factor-graph
  contraction and approximate representations against root utilities, every
  unilateral response value, literal response actions, memory, and time.
- Coalition response remains an offline teacher. It is not part of this first
  quotient because a shared-private pair controller groups by two hands rather
  than one; its cost and representation require a separately visible extension.

## Dissent protocol

**Confidence:** very high that public topology is deal-invariant in this river
game; high that memory falls sharply; moderate that a Python/NumPy timing win
predicts a native kernel.

**Opposing evidence:** the deal axis remains explicit, so this can improve a
three-player oracle while doing nothing to cure six-player exponential support.
Earlier streets also change public cards and legal topology, requiring a new
compiled epoch.

**Largest risk:** celebrating a public-tree layout win as belief
factorization. This ADR explicitly forbids that interpretation.

**Cheapest falsification:** a zero-reach pure-policy action mismatch, a public
signature that differs across deals, or a seven-hand row that remains slower or
larger than the dependency tape.
