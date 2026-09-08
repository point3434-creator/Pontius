# ADR-0294: Reject dyadic v2 on confirmation power

- Status: accepted untouched-confirmation result; dyadic v2 is promising but rejected on the frozen panel-power gate before replay integration
- Date: 2026-08-23
- Follows: ADR-0293
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0294
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Preregister a candidate-blind sizing-power diagnostic before choosing any v3 mechanism; keep v1 and v2 parked and unintegrated, and keep blueprint training, convex-master integration, resolving, and strategy labels closed
- Front-Door-Blockers: structural showdown diversity produced only five informative contexts rather than eight; no candidate-blind power qualification or richer reduced sizing game is frozen

## Verdict

Reject ADR-0293's dyadic v2 candidate before complete-hand integration. The
candidate passes the opened development control and every observed
confirmation quality, numerical, width, and v1-comparison threshold, but the
deterministically generated confirmation panel has only five informative
contexts rather than the preregistered minimum of eight. Insufficient panel
power is an explicit kill criterion; no favorable conditional result can waive
it.

## Decision

Park the dyadic source, deterministic confirmation generator, sealed panel,
and expected-rejection test as research controls. Do not connect v2 to
`reference_hand_replay`, the convex master, blueprint selection, or resolving.
ADR-0290 remains the active exact fallback loop.

The next checkpoint must diagnose evaluation power before proposing another
sizing mechanism. It may study why structurally diverse showdown matrices
often make full integer and minimum/all-in values identical, and may
preregister a candidate-blind full-versus-narrow qualification rule or a richer
reduced sizing game. It may not rerun v2 on a replacement panel, reduce the
eight-context threshold, or describe the five-context conditional result as a
confirmation pass.

## Development result

On ADR-0291's already-open four-context panel, v2 uses source digest
`c09e69eeb1020c6ec33597a51f11f503696737e393139024c9c5b70e51f07153`.
It recovers `99.9999999997%` of the sole positive full-over-minimum/all-in
gap. Maximum normalized full-v2 loss is below `5e-15`, and mean loss is below
`2e-15`. This passes ADR-0293's development fit condition and authorizes panel
construction only; it is not held-out evidence.

## Sealed confirmation panel

The preregistered SHA-256 stream accepted 24 contexts after 45 complete card
candidates. The canonical panel digest is
`c3d1f5ca6dea3291e202d73e542caccb05cf61bca775b327fad90c3e62bc5438`.
The generator test reconstructs the same bytes and digest, exact chip fields,
positive rational probabilities, context order, and structural showdown
filters without global PRNG state.

No context was manually added, removed, reordered, or replaced. The first
quality invocation used that sealed panel once.

## Confirmation result

All values use the same exact cards, probabilities, zero-sum chip payoffs, and
compact LP contract. The five informative contexts are
`adr0293-confirmation-10`, `-15`, `-18`, `-19`, and `-21`.

| Measure | Frozen requirement | Observed |
|---|---:|---:|
| Informative contexts | at least 8 of 24 | **5 of 24 — fail** |
| Aggregate v2 recovery on informative contexts | at least 80% | 94.5146608124% |
| Maximum normalized full-v2 loss | at most 1% | 0.0281744672% |
| Mean normalized full-v2 loss | at most 0.5% | 0.0024195872% |
| Aggregate normalized full loss, v2 | no greater than v1 | 0.000580700929 |
| Aggregate normalized full loss, v1 | control | 0.001002545073 |
| V2 vs v1 by context at `1e-9` chips | diagnostic | 3 wins / 20 ties / 1 loss |
| Maximum v2 total actions | at most 9 and below full | 7 |

V2 conditional recovery exceeds the threshold, loses less aggregate normalized
value than v1, and satisfies `full >= v2 >= minimum/all-in` within `1e-9` in
all contexts. These facts are opposing evidence to rejection, not authority to
ignore the failed power conjunct.

The maximum probability-simplex residual is `8.771e-15`; maximum chip-objective
reconstruction error is `4.583e-13`; maximum compact-versus-normal-form value
difference is `3.908e-14` chips; and maximum normal-form duality gap is
`2.843e-14` chips. All are below `1e-9`. The failure is not numerical.

## Failure diagnosis

Nineteen contexts have full-over-minimum/all-in gaps below
`1e-6 * payoff_span`. Requiring both signs plus two distinct rows and columns
proved private-information structure, but it did not prove that intermediate
bet sizes change the opener's security value. Structural showdown diversity
and sizing informativeness are different semantic quantities. R59 has
materialized: a low-powered panel can make action-abstraction comparisons look
better while contributing almost no discriminating evidence.

## Evidence classification

- **Known:** the sealed panel and all compact/normal-form numerical checks are
  deterministic and reproducible.
- **Reproduced:** development fit, five informative contexts, and all reported
  conditional confirmation diagnostics.
- **Observed:** v2 is better than v1 on aggregate normalized loss in this panel.
- **Rejected:** v2 as the accepted C5 action abstraction, replay integration,
  and any lower post-outcome power threshold or replacement-panel rerun.
- **Hypothesis:** candidate-blind qualification using only full and narrow
  controls, or a richer reduced game, can create a powered future gate without
  selecting for a particular candidate.

## Dissent

Supporting rejection: panel power was frozen as a conjunctive prerequisite,
only five contexts pass it, and the exact generator's structural filter failed
to predict sizing opportunity.

Opposing evidence: all five informative contexts aggregate to 94.51% recovery;
v2 halves v1's aggregate normalized loss; every numerical and width control
passes; and the worst normalized loss is only 0.0282%.

Largest unknown: whether candidate-blind power qualification can avoid both
degeneracy and selection bias, especially when the eventual candidate is
designed with knowledge of the qualification rule.

Cheapest falsifying next experiment: preregister a diagnostic pool and open
only full-versus-minimum/all-in gaps—never v1, v2, or a new candidate—to test
whether a deterministic qualification rule yields enough stable informative
contexts across disjoint card/chip batches.

## Claims boundary

This is a clean negative checkpoint with promising conditional diagnostics.
It does not accept v2, prove a production abstraction, authorize replay hooks,
establish strategically exact translation, open action width through the
convex master, train a blueprint, normalize full-width beliefs, resolve a
street, establish multiplayer safety, report NashConv, AIVAT, league strength,
optimized latency, or complete C5. No revoked experiment, external publication,
or thesis change is authorized.
