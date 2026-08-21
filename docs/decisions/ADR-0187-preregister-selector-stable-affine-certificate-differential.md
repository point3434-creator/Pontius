# ADR-0187: Preregister a selector-stable affine certificate differential

- Status: accepted preregistration
- Date: 2026-08-21
- Depends on: ADR-0166, ADR-0179, ADR-0186
- Config: `experiments/configs/h32-selector-stable-affine-certificate-v1.json`

## Question

ADR-0186 found that a charged cap-radius observation can locate substantial
bounded value, but a resident warm step leaves too little conservative street
headroom for exploratory line search plus final recertification. Can one exact
source-relative endpoint sweep prove a useful interpolation scale without
performing that search?

This is an engineering differential over retained policies. It validates a new
certificate primitive before that primitive may see a fresh target. It does
not test a live selector, emit a candidate, or make a strategy-quality claim.

## Affine proof scope

The candidate direction may change one acting seat at one exact public node.
Every terminal trajectory therefore contains at most one changed behavioral
factor. Between the immutable blueprint and the scale-one endpoint, each
affected terminal numerator is affine in the common interpolation scale.

For each responding seat, perform one endpoint contraction and reverse both
the source intercept and endpoint-minus-source slope through the immutable
source best-response action tape. At every response selector, compare the
source action with every competitor. If a competitor's slope closes its source
margin, its conservative tie scale is:

```text
max(0, source margin - 2e-11) / closing slope
```

The proof interval ends at the earliest such tie. It makes no statement at or
beyond that boundary. An exact source tie that can move toward a competitor
therefore produces a zero interval. A direction changing zero or multiple
public nodes, belonging to another actor, or producing a quadratic profile
term is rejected rather than approximated.

Inside the selector-stable interval, each seat's utility and best-response
value are affine and its deviation gain is the positive part of one affine
gap. Intersect that interval with every immutable-blueprint gain cap and the
incumbent-NashConv objective. Subtract the same `2e-11` raw numerical allowance
from cap and objective claims. If a positive objective interval remains,
multiply its upper bound by `0.5` and choose the largest point no greater than
that target on ADR-0175's 34-point geometric-halving grid. Otherwise abstain.

The half-radius and downward grid quantization are conservative by
construction. They are frozen before the h32 differential; neither may be
tuned from its output.

## Additive provenance boundary

Do not edit the accepted incremental verifier. Its SHA-256 remains
`12dbf0e59ba13cba70cbaa81c60fb8ac4cfc16312d9834782d76b750052627dd`,
preserving every historical config that binds it. The new proof lives in the
additive `selector_stable_affine_response` module and calls the old immutable
terminal cache and contraction primitives.

Small-game controls must establish all of the following before the h32 replay:

- affine utility, response value, and gain match direct incremental evaluation
  strictly inside the proof interval;
- an observed endpoint response flip has an earlier computed breakpoint;
- two-public-node scope is rejected;
- a selected envelope scale is directly complete, has zero response flips,
  and matches predicted quality; and
- historical frozen-hash parser controls continue to pass unchanged.

## Retained h32 differential

Reconstruct the six ADR-0186 seat-2 targets and their immutable source
average-64 blueprints. Reproduce one resident warm step and the same six
regret-vertex public blocks per target. Require exact source, target,
checkpoint, block, and direction identities against the retained artifact.

For each of the 36 blocks:

1. evaluate one scale-one endpoint sweep for all six responding seats;
2. compute the selector, cap, objective, and conservative selected scale;
3. directly evaluate one fixed witness no greater than both `2^-16` and half
   the selector interval;
4. if the affine envelope selects a scale, independently run the accepted
   exact incremental verifier at that scale; and
5. compare utility, best-response value, and deviation gain with maximum
   absolute error `1e-9`.

The direct witness and selected-scale validations are off-clock differential
teachers. They are never part of the proposed affine certificate or its street
ledger. A selected candidate must complete the old exact verifier with zero
response flips, but the audit does not require that any candidate exist.

## Descriptive street ledger

For acting seat 0 only, report:

```text
one resident warm step
+ current-policy, regret, all-block, and endpoint construction
+ one six-seat affine endpoint sweep
+ 1,000 ms synchronization/emission reserve
```

This deliberately charges construction of all six blocks even though a later
seat-0 rule could construct less. Direct validations are excluded. Report the
fit on all six retained targets, but do not gate exactness on fit, selected
value, oracle capture, selector radius, acting seat, or speedup.

If the differential is exact and the retained seat-0 ledgers fit, the primitive
may advance to a separately preregistered fresh street trial. If exactness
fails, reject the primitive. If exactness passes but the ledger misses, optimize
the affine sweep or warm step before exposing fresh contexts.

## Outcome-neutral gates

Require six targets, six warm steps, 36 coherent blocks, 216 affine seat rows,
36 fixed direct witnesses, clean committed execution, accepted parents, all
frozen identities, numerical warm identity, parent regret-direction identity,
one-node affine scope, source intercept error at most `2e-11`, direct utility,
response, and gain errors at most `1e-9`, fixed witnesses strictly inside the
selector interval with zero flips, every selected scale directly complete with
zero flips, blueprint emission, finite accounting, 60-second step/sweep/direct
ceilings, the 12 GB pool ceiling, a 1 GB physical-free floor, and a broad
1,800-second audit ceiling.

Do not gate on whether an affine envelope selects, the selected scale or value,
capture fraction, selector/cap/objective radius, street fit, or any latency
ratio.

## Frozen artifacts

- config SHA-256:
  `f62d2e04ad39fb32ca1a51b6ca09952fa880cb32b0bdd30f938a4f81c5345ec5`;
- additive affine verifier SHA-256:
  `9e222242cc0c60d13b02935b48f4f5e5a2a4019492ff1a551cedf64a0b0d0168`;
- audit implementation SHA-256:
  `2306d4b09e7c746fa41ac35f50c9badeaa246d8d9fb5b280f94573924d17644e`;
- affine unit-control SHA-256:
  `275cc6c40ae82f6859c823dd6ae6f122662e4d58e41ef9f9211e78c99198e22c`;
- audit-control SHA-256:
  `fa2289281bc3b79090177c8e0b1833852f1d686f086203d085fae098ab168836`;
- result target:
  `experiments/results/h32-selector-stable-affine-certificate-v1.json`.

The 22 focused affine, historical-hash, and audit controls pass. No retained
h32 affine endpoint sweep or direct validation has run.

## Decision

Commit the additive verifier, audit, config, controls, and this ADR before the
first retained h32 endpoint sweep. Execute once from that clean commit. Keep
all direct validations off clock, emit only the immutable blueprint, and do
not construct fresh targets until this certificate differential closes.
