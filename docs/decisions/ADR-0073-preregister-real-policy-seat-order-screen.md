# ADR-0073: Preregister real-policy provenance and seat-order screen

**Status:** Accepted before source solves, lifted policies, ranks, utilities, or timing

**Date:** 2026-08-19

## Decision

Run the missing representation screen before implementing the clean-fringe
candidate reader. Replace the pseudo-random-policy-only evidence with actual
six-player DCFR average policies and one literal unilateral best response, while
retaining uniform, hashed-dense, and hashed-pure controls. Test every unordered
3-versus-3 seat partition and every within-half order.

The frozen configuration is
`experiments/configs/real-policy-seat-order-screen-v1.json`. The result target
is `experiments/results/real-policy-seat-order-screen-v1.json`. The frozen
configuration SHA-256 is
`8298c3c9e8700c65cb393d99059e2d821aa3d4652c98656926155690ecb8d904`.

This screen selects neither an online solver nor a deployable policy. It asks
which value representation serves each declared policy provenance and supplies
the actual crown/frontier geometry needed by the following read-path audit.

## Genuine but deliberately small solver source

An engineering calibration found that one exact tabular six-player DCFR
iteration costs about 28.9 seconds on the four-hand balanced game. Multiplying
that cost through two families and multiple checkpoints would spend minutes on
teacher generation before testing representation.

Freeze a three-hand-per-seat exact source game instead. For each range family:

1. generate one exact factor belief and materialized compatible-deal game;
2. run the repository's ordinary alternating six-player DCFR once through
   checkpoint 16;
3. retain average strategies at checkpoints 4 and 16;
4. evaluate and report their exact source utilities, unilateral gains, and
   NashConv without imposing a strategy-quality gate; and
5. compute seat 3's exact unilateral best response to the checkpoint-16 average
   with the flat public-tree evaluator, then replace only seat 3 by that pure
   response.

These are real solver and best-response policies, not threshold or hash
surrogates. They are also coarse three-hand textures and may be strategically
weak. The screen may use them to study representation structure, not to claim a
blueprint-quality result or multiplayer CFR convergence.

## Frozen policy lift

Lift each real source policy separately into the four- and seven-hand target
schemas. Within each seat, stably order source and target hands by exact river
showdown strength and hole cards. Map a target ordinal to the nearest source
strength quantile with deterministic half-up rounding. Copy the mapped source
distribution at the identical public history.

The lift preserves seat, public history, action schema, normalization, and
policy provenance. It does not use target utilities, root ranks, singular
values, card-belief weights, or later labels. Report policy entropy, pure-action
fraction, number of distinct hand distributions, and total variation between
the two lifted DCFR checkpoints.

Uniform, hashed-dense, and hashed-pure policies are generated directly on each
target schema using the ADR-0067 seed rule. Their original-order ranks can
therefore be compared with the frozen ADR-0068 artifact.

## Exact terminal and root controls

Use the ADR-0072 structured showdown automaton for every terminal. At four and
seven hands only, export its direct one-hot TT, apply tolerance-only rounding,
and compare with the literal dense payoff operator. This keeps the validated
automaton as the terminal source while retaining a complete small-axis oracle.

For each policy, target value seat 0/3/5, hand width, and range family:

1. recursively construct the exact dense Cartesian root value tensor;
2. compose and cache every public-node tolerance-only TT in original seat order;
3. report root, depth-one, and full depth/rank histograms, raw/output ranks,
   storage, and propagated bounds; and
4. retain the dense tensor for the seat-order screen.

Card-incompatible Cartesian assignments remain an algebraic extension of the
operator. Exact factor-belief contraction supplies target utilities and assigns
zero probability to incompatible hands.

## Complete six-seat ordering screen

There are ten unordered 3-versus-3 partitions. Represent each by the half that
contains seat zero. For every partition, enumerate all `3! * 3! = 36` orders
inside the fixed halves, for 360 orders total.

For a chosen order, exact TT storage is determined by the numerical unfolding
ranks at its five cuts. Compute each unique seat-subset unfolding once, using a
`1e-12` relative numerical-rank threshold. Select the order with:

1. minimum exact TT numeric storage;
2. then minimum middle rank; and
3. then lexicographically smallest seat order.

This selection sees the fixed root operator but no belief weights, expected
utilities, action labels, or compressed-arm errors. Within-half permutations
must leave each partition's middle singular spectrum invariant; the audit
compares them explicitly.

Transpose the dense root into the selected order, build one tolerance-only TT,
and apply caps 8, 16, and 32. Reorder the exact factor belief and card topology
the same way, contract each arm, and compare with the original-order literal
utility.

## Two representation products

DCFR average policies are the customer that could justify a compact root value
product. Require every checkpoint-16 DCFR row to have at least one selected-
order cap no larger than 32 with:

- payoff-normalized utility error at most `1e-4`; and
- root TT numeric storage at most 25% of the dense root tensor.

This capped product remains authorized only for fixed-policy value estimation,
scheduling, and approximate search. It cannot feed the `1e-10 * span`
acceptance comparator.

Hashed-pure and literal-BR profiles are deliberately not required to compress.
Their declared product is an explicit public-state/tape representation. This is
a legal provenance selector: average versus BR/hash control is known when the
policy is constructed, not inferred from future utility labels. Report their
ranks and cap errors anyway; do not delete difficult rows.

## Frozen gates

Require:

- zero source and lifted schema mismatches;
- structured-terminal error at most `1e-10`;
- selected-order tolerance-only root reconstruction error at most `1e-8`;
- reordered exact utility disagreement at most `1e-8`;
- within-partition singular-spectrum disagreement at most `1e-10`;
- every checkpoint-16 DCFR row has a safe selected-order capped arm;
- every policy/partition row and every original-order crown profile is present;
  and
- the declared provenance-to-product dispatch is unchanged.

Failure of the DCFR cap gate rejects compact-root service for this real average
policy source. It does not reject the sparse terminal automaton or explicit
public-state representation. Hash/BR compression failure is expected evidence,
not a failed gate.

## Successor read-path audit

Regardless of whether the compact DCFR product passes, the next frozen audit
must evaluate whole-seat fixed-belief candidates through a common clean
frontier without candidate-time SVD. It will compare against:

1. recompose, round, then factor-contract;
2. the dense Cartesian public-root evaluator; and
3. the flat compatible-deal public evaluator where the small axis permits it.

It must report frontier size, delta-support frontier, frontier-rank histogram,
total batched feature width, cost-weighted dirty closure, and all-six-player
bill. The gate is exactness, conservative bounds, and correct
abstain/certify behavior on frozen near-guard controls. There will be no
small-axis speed-win gate. A 32-hand runtime path advances only if measured work
scales credibly in those structural quantities.

## Dissent protocol

**Confidence:** high in provenance and lift reproducibility; high in complete
partition coverage; moderate that a three-hand DCFR texture predicts a stronger
blueprint's rank; low that one root TT serves all future average policies.

**Opposing evidence:** the lift creates only three strength bands per seat and
can make a real average artificially step-like. Conversely, average policies
may be much smoother than checkpoint 16 and compress better later.

**Largest risk:** treating a representation screen on a weak lifted policy as a
strategy-quality result, or using a per-root best order without charging its
compile and topology costs downstream.

**Cheapest falsification:** every lifted DCFR checkpoint-16 row misses the same
rank-32 value/storage gates that hashes missed, even under its best exact-
storage seat order.
