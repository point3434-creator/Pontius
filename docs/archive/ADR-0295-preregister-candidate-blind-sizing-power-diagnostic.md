# ADR-0295: Preregister candidate-blind sizing-power diagnostic

- Status: accepted executable diagnostic preregistration before any new pool construction or full-versus-narrow value
- Date: 2026-08-23
- Follows: ADR-0294
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0295
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Execute three frozen candidate-blind full-versus-minimum/all-in power replications without constructing or evaluating v3; keep both rejected lattices parked and all replay, blueprint, convex-master, resolver, and strategy labels closed
- Front-Door-Blockers: no powered candidate-blind panel-construction rule has passed across disjoint seeds, and no v3 mechanism or confirmation panel is authorized

## Question

Can Pontius deterministically construct a materially sizing-informative reduced
panel using only the full-integer and minimum/all-in controls, before and
without evaluating any action-abstraction candidate?

## Decision

Test a candidate-blind qualification protocol across three disjoint frozen
SHA-256 streams. This checkpoint may generate exact cards, probabilities, and
chip contexts and may solve only two arms: the full integer bet universe and
the minimum/all-in control. It may not import, construct, inspect, or evaluate
ADR-0292 v1, ADR-0294 v2, any pot-fraction list, or any proposed v3 source.

This is evaluation-power research, not action-abstraction research. A pass
would authorize preregistration of a future v3 mechanism and dual-panel
protocol using fresh seeds. It would not authorize selection or replay of any
candidate now.

## Frozen pool construction

Use the exact SHA-256 counter stream, unbiased `randbelow`, Fisher-Yates deck
shuffle, card slicing, private-pair canonicalization, structural showdown
filter, pot set, stack set, and positive exact joint-weight construction frozen
by ADR-0293. The implementation may call those sealed primitives but may not
change them; ADR-0293's panel digest must remain unchanged.

The three seed texts are exactly:

```text
pontius|adr-0295|candidate-blind-power-v1|baseline=2a7e5f470ca509e3c6dda1f300251fb8c3e9e4a3|batch=0
pontius|adr-0295|candidate-blind-power-v1|baseline=2a7e5f470ca509e3c6dda1f300251fb8c3e9e4a3|batch=1
pontius|adr-0295|candidate-blind-power-v1|baseline=2a7e5f470ca509e3c6dda1f300251fb8c3e9e4a3|batch=2
```

For each seed, generate exactly 96 structurally admissible contexts before
opening any value. Name them `adr0295-power-b{batch}-c{index:02d}` in accepted
order. Bind seed, generator/dependency versions, raw card-candidate attempt
count, and all 96 ordered context fields to canonical JSON and a pool SHA-256.
The first construction may reveal and record each digest but may not alter a
pool.

## Frozen qualification rule

Process each pool in context order. For a context, solve only:

- check plus every exact integer bet from two through the stack; and
- check plus the exact minimum bet and all-in.

Use `ProbabilitySimplexAllowance(1e-9)` and
`ChipObjectiveAllowance(1e-9)` with the existing compact behavioral maximin
oracle. `payoff_span = pot + 2*stack` remains derived from the reduced game.

Introduce two nominally distinct qualification semantics:

- a dimensionless normalized sizing-opportunity floor of exactly `1e-4`; and
- a chip-valued classification guard of exactly `1e-8` chips.

Let `gap = full_value - narrow_value` and
`threshold = 1e-4 * payoff_span`. A context qualifies only when
`gap > threshold + 1e-8 chips`. A context is numerically ambiguous when
`abs(gap - threshold) <= 1e-8 chips`; ambiguity rejects the diagnostic rather
than being classified. Other contexts are nonqualifying.

Retain the first 12 qualifying contexts in order and stop opening values for
that batch immediately. No value after the twelfth qualification may be
computed. Bind the 12 ordered context digests and their pool indices to a
qualified-panel SHA-256. Full/narrow values are evidence diagnostics, not
panel identity.

## Frozen replications and gates

For every opened full or narrow LP require probability-simplex residual and
chip-objective reconstruction error at most `1e-9`, verified
`full >= narrow` within `1e-9` chips, and no classification ambiguity. On the
leading two-by-two projection of each of the 12 retained contexts, compare the
minimum/all-in compact LP with the complete normal-form teacher within `1e-9`
chips and require its duality gap at most `1e-9`.

The diagnostic passes only if all three batches:

- find 12 qualifying contexts within their 96-context cap;
- open no value after the twelfth qualifier;
- produce unique pool and qualified-panel digests;
- retain at least three distinct pot values, three distinct stack values, and
  six distinct showdown-sign matrices among the 12 qualifiers; and
- pass every numerical, exact-probability, card-compatibility, ordering, and
  candidate-blind static-inventory control.

Also require the existing ADR-0293 panel to reconstruct byte-identically. The
three batches are replications, not train/validation folds; no threshold or
filter is selected from them.

## Prospective dual-panel contract

If this diagnostic passes, the next preregistration may freeze one v3
mechanism. Only after that mechanism is frozen may fresh, commit-derived seeds
construct:

1. an unqualified representative panel for maximum/mean full-candidate harm;
   and
2. a separately qualified panel for aggregate recovery where intermediate
   sizing opportunity is materially present.

The diagnostic pools and ADR-0293 panel are permanently development evidence
and may not serve as v3 confirmation. Candidate-blind qualification avoids
selecting contexts on v3's own value, but its conditioning must remain explicit
in every claim.

## Gates

The checkpoint passes only if all pool, qualification, static blindness,
numerical, normal-form, diversity, preservation, documentation, and complete-
suite gates pass unchanged. Run changed-file Ruff, Python 3.11 parse, generated
front door, documentation integrity, whitespace, and the complete repository
suite.

## Kill criterion

Any candidate import or value, changed sealed primitive, repeated/manual
context, pool drift, ambiguity, insufficient yield, diversity failure,
numerical failure, extra opened value, or threshold/unit change rejects the
diagnostic. On rejection do not tune the pool or choose v3; preregister a
richer reduced sizing game instead.

## Claims boundary

A pass would establish only a reproducible candidate-blind method for creating
materially sizing-informative reduced panels. It would not validate v1, v2, or
v3; choose action sizes; prove representative frequency; eliminate selection
bias; authorize replay; establish strategically exact translation; train a
blueprint; open action width through the convex master; resolve a street;
establish multiplayer safety; report NashConv, AIVAT, league strength, or
optimized latency; or complete C5. No revoked experiment, external
publication, or thesis change is authorized.
