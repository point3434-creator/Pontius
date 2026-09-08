# ADR-0297: Preregister width-four sizing-power replications

- Status: accepted executable preregistration before any width-four pool construction or value
- Date: 2026-08-23
- Follows: ADR-0296
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0297
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Construct and seal three width-four structural pools, then execute only the frozen candidate-blind full-versus-minimum/all-in replications through an owned runner; keep ADR-0295 batch 2 value-unopened and keep v1, v2, v3, replay, blueprint, convex-master, resolver, and strategy labels closed
- Front-Door-Blockers: no width-four pool digest or value exists, the replicated yield and exact-work gates have not run, and no v3 mechanism is authorized

## Question

Does increasing each private-hand axis from three to four types make materially
sizing-informative contexts reproducible, without changing the one-bet river
tree or admitting any action-abstraction candidate?

## Decision

Run the smallest richer-game successor to ADR-0295: retain the opener
check/bet and responder fold/call tree, exact integer full arm, and
minimum/all-in narrow arm, but expand the exact joint private range from three
by three to four by four. This isolates private-type width. It does not test a
responder-raise branch, production range width, multiplayer play, or a proposed
bet lattice.

Preregistration and structural construction are temporally separated from
value opening. Commit this ADR before constructing a pool. After construction,
record and commit all structural digests before any full or narrow LP is run.

## Frozen structural generator

Use the SHA-256 counter stream, unbiased `randbelow`, and Fisher-Yates shuffle
implementation already sealed by ADR-0293, without changing that source. The
three ASCII seed texts are exactly:

```text
pontius|adr-0297|width4-power-v1|baseline=91449e42997938e72961976dcd8b4fda989e258b|batch=0
pontius|adr-0297|width4-power-v1|baseline=91449e42997938e72961976dcd8b4fda989e258b|batch=1
pontius|adr-0297|width4-power-v1|baseline=91449e42997938e72961976dcd8b4fda989e258b|batch=2
```

For each complete shuffled card candidate:

- take cards 0 through 4 as the river board;
- canonicalize cards 5 through 12 into four opener pairs and cards 13 through
  20 into four responder pairs;
- reject any cross-seat showdown tie, require both showdown signs, and require
  at least three distinct four-entry row patterns and three distinct four-entry
  column patterns;
- after structural acceptance, draw pot and stack from ADR-0293's frozen sets;
  set the exact minimum bet to two chips; and
- draw 16 integer joint weights independently from one through nine and
  normalize them as positive exact rational probabilities.

Accept exactly 96 contexts per batch in stream order. Name them
`adr0297-width4-b{batch}-c{index:02d}`. Bind the seed, baseline, generator and
dependency versions, width, filter, raw card-candidate attempt count, and every
ordered context field to canonical ASCII JSON and SHA-256. Pool construction
may reveal only structural data and digests. It may not call a sizing oracle.

## Frozen value protocol

For each batch, process its pool in order through one value-owning function.
For each opened context solve only:

1. check plus every exact integer bet from two through the effective stack;
   and
2. check plus the exact minimum bet and all-in.

Use the existing compact behavioral maximin oracle with solver tolerance
`1e-11`, `ProbabilitySimplexAllowance(1e-9)`, and
`ChipObjectiveAllowance(1e-9)`. Reuse the nominally distinct
`NormalizedSizingOpportunityFloor(1e-4)` and
`ChipClassificationGuard(1e-8)` semantics. Let `gap = full - narrow` and
`threshold = 1e-4 * (pot + 2*stack)`. Qualify only when
`gap > threshold + 1e-8 chips`; stop and reject at the first ambiguity where
`abs(gap - threshold) <= 1e-8 chips`.

Stop a batch inside the runner immediately on its twelfth qualifier or after
all 96 contexts. The immutable result must bind the exact protocol constants,
batch, pool digest, contiguous pool-bound observation prefix, classifications,
values, numerical residuals, LP dimensions, full/narrow simplex pivots, stop
reason, and result digest. A panel may be extracted only from a target-reached
result after rebinding the complete prefix to its pool.

ADR-0295 batch 2 remains value-unopened. Neither it nor any earlier opened or
tainted context may enter this checkpoint.

## Yield, exact-work, and oracle gates

The diagnostic passes only if all three batches independently:

- reach 12 qualifiers within 96 contexts without ambiguity or any post-stop
  opening;
- produce unique pool, result, and qualified-panel digests;
- retain at least three pot values, three stack values, and eight distinct
  four-by-four showdown-sign matrices among the 12 qualifiers; and
- pass exact cards, positive rational range, order, width, structural filter,
  static candidate-blind inventory, and numerical controls.

For every LP require probability-simplex residual, chip-objective
reconstruction error, LP duality gap, and maximum constraint violation at most
`1e-9`; require `full >= narrow` within `1e-9` chips; and cap each full or
narrow solve at 4,096 simplex pivots. The width-four formulation must retain
its exact analytic dimensions: for stack `S`, the full arm has `8*S - 4`
variables and `8*S` inequalities; the narrow arm has 20 variables and 24
inequalities. Thus its static LP width is exactly four-thirds of ADR-0295 for
the same action count, with maxima 236 variables and 240 inequalities over the
frozen stack set.

On the leading two-by-two projection of every retained context, compare the
minimum/all-in compact value to the independently enumerated normal-form
teacher within `1e-9` chips and require teacher duality gap at most `1e-9`.
Record one serial Python 3.11 wall-time observation for the complete frozen
invocation on the named workstation, but treat it only as a local campaign-cost
diagnostic. It is not a real-time solver benchmark or a pass gate.

## Successor authority

A pass authorizes only a new preregistration for one v3 mechanism and fresh
dual-panel evaluation seeds. It does not authorize choosing v3 from any
width-four value or reusing these pools for candidate confirmation. A failure
parks this width-only game without retuning and makes a separately
preregistered responder-raise reduced game the next eligible diagnostic.

## Gates

Run changed-file Ruff, Python 3.11 parsing, generated-front-door and
documentation integrity checks, staged whitespace checks, all structural and
value tests, preservation of ADR-0293 and ADR-0295 structural digests, and the
complete repository suite. The structural checkpoint must be committed before
the value test is first invoked.

## Kill criterion

Any pre-structural ADR drift, candidate import or value, old batch-2 opening,
changed sealed dependency, repeated/manual context, pool drift, wrong width or
filter, ambiguity, insufficient replicated yield, diversity failure,
post-target value, numerical failure, pivot-cap breach, analytic-dimension
mismatch, threshold/unit change, or value opening before the structural commit
rejects the checkpoint. Do not lower the floor, enlarge the pools, loosen a
cost or numerical cap, replace a seed, or add a response branch after outcome.

## Claims boundary

A pass would establish only that this deterministic four-by-four one-bet game
can build candidate-blind sizing-informative development panels within frozen
exact-work limits. It would not establish representative poker frequency,
production range width, runtime action quality, optimized latency,
strategically exact translation, a valid action abstraction, replay or
convex-master integration, a trained blueprint, street resolving, multiplayer
safety, NashConv, AIVAT, league strength, C5 completion, or a complete bot. No
revoked experiment, external publication, or thesis change is authorized.
