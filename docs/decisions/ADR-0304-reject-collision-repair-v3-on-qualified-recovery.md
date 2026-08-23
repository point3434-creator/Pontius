# ADR-0304: Reject collision-repair v3 on qualified recovery

- Status: accepted negative result; collision-repair v3 is rejected and parked before every integration path
- Date: 2026-08-23
- Follows: ADR-0303
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0304
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Formulate and commit a separate preregistration for one materially new action-width mechanism and wholly fresh value-unopened representative and qualified panels before source code or values; do not retune collision-repair v3, reuse any opened panel for confirmation, widen its frozen candidate, or connect any parked lattice to replay, blueprint, convex-master, resolver, or strategy paths
- Front-Door-Blockers: collision-repair v1, v2, and v3 are parked; no action abstraction has passed reduced quality and power gates; action width remains absent from the reference hand, convex master, blueprint, and resolver; any successor mechanism, source, fresh seeds, panels, values, and integration require new prospective authority

## Verdict

Reject collision-repair v3 at its frozen qualified raw-chip aggregate-recovery
gate and park it before integration. The representative family passes both
normalized-loss limits. The qualified family also passes both normalized-loss
limits, but recovers only `0.800547544995807` of the available full-over-
minimum/all-in chip gain versus the preregistered `0.90` floor. This is a
substantive negative result, not ambiguity, numerical failure, panel drift, or
a reason to relax the gate.

No source, fraction, seed, panel member, threshold, allowance, solver, arm,
stop rule, or unit changed after the first v3 value. Qualified values opened
only after the complete representative result passed. No replay, blueprint,
convex-master, resolver, or strategy path was imported or connected.

## Frozen result

| Family | Contexts | Maximum normalized full-v3 loss | Mean normalized full-v3 loss | Raw-chip recovery | Verdict |
|---|---:|---:|---:|---:|---|
| Representative | 48 | `0.0006146721799333525` | `7.113215970853139e-05` | `0.9119521751305644` diagnostic only | pass |
| Qualified | 24 | `0.0010646792653687953` | `0.00025946068709217334` | `0.800547544995807` | reject |

The qualified recovery numerator is `1.299630985953442` chips and its
denominator is `1.623427607863377` chips. They are direct panel sums of
`v3 - minimum/all-in` and `full integer - minimum/all-in`, respectively; no
mean of context ratios or payoff-span surrogate enters that conjunct. Both
qualified normalized-loss limits remain comfortably inside `0.005` maximum
and `0.001` mean. Their pass does not override the failed recovery conjunct.

Deterministic SHA-256 identities are:

- representative result:
  `37217f9b4b1dab282dd0c0a998559d10714de6e593b73d2209b45033a75f8c30`;
- qualified result:
  `fdf2261940947020d38ad518ab37c2a8031dc2b8a161157f1e26e862ed0c83c2`;
- stopped campaign:
  `5e27d5767b35ef43d2a75a9c97aca3d46a3ee966037220299d82c8d571a6dbdf`.

Elapsed time is excluded from those hashes. One first serial invocation on
this workstation took `22.9252` seconds. That is an offline 72-context
campaign diagnostic, not per-solve, per-iteration, real-game, or 15-second
street latency.

## Exact work and numerical controls

The campaign owns 216 candidate-comparison compact LPs: three arms on 48
representative contexts and three arms on 24 qualified contexts. All 72
contexts also own one independently enumerated bounded normal-form teacher and
its matching compact leading-two-by-two solve. Thus the invocation executes
288 compact LPs plus 72 teachers.

| Diagnostic | Representative maximum | Qualified maximum | Frozen ceiling |
|---|---:|---:|---:|
| Probability-simplex residual | `1.728e-13` | `5.351e-14` | `1e-9` |
| Chip-objective reconstruction error | `1.376e-12` chips | `2.672e-12` chips | `1e-9` chips |
| Compact LP primal-dual gap | `4.547e-13` chips | `4.547e-13` chips | `1e-9` chips |
| Lower-envelope violation | `8.527e-14` chips | `1.066e-13` chips | `1e-9` chips |
| Candidate-arm simplex pivots | 375 | 336 | 4,096 |
| Teacher compact/value difference | `3.908e-14` chips | `2.842e-14` chips | `1e-9` chips |
| Teacher primal-dual gap | `3.020e-14` chips | `1.743e-14` chips | `1e-9` chips |
| Teacher compact pivots | 18 | 19 | 4,096 |

Every full, v3, and minimum/all-in arm retains its exact size tuple, LP
dimensions, value, residual coordinates, and pivot count. Every teacher binds
the structural context, exact semantic conversion, derived bounded context,
minimum/all-in sizes, nine opener pure plans, and sixteen responder pure plans.
No arm reverses `full >= v3 >= minimum/all-in` within the `1e-9`-chip ordering
allowance.

## Independent and adversarial verification

An independent exact-rational reconstruction applied ADR-0300's pot fractions,
ties-up integer rounding, clipping, mandatory anchors, collision test, and
deduplication to all 72 public chip states. It reproduces every candidate size
tuple without importing the production sizing helpers. The two-pot target
collides with an anchor in 40 of 48 representative contexts and 20 of 24
qualified contexts, selecting the frozen three-halves fallback exactly there.

The maintained controls additionally:

- reconstruct every structural-to-oracle binding, panel index, source digest,
  abstraction digest, exact width, arm dimension, and teacher certificate;
- reject changed normalized-loss arithmetic, reversed arm values, wrong panel
  membership, invalid nominal gate quantities, and numerical excesses;
- prove campaign hashes ignore only elapsed diagnostic time; and
- inject a representative loss failure and prove the runner invokes one family
  only, returns `representative_rejected`, and never opens qualified values.

A separate unchanged rerun reproduces the three frozen result hashes and raw-
chip sums. This is deterministic reproduction and adversarial spot-checking,
not certification of the complete solver or poker model. The complete
repository regression boundary passes 1,153 tests with two intentional skips.

## Decision

The v3 hypothesis is false on its prospectively sealed qualified panel. Keep
the source and evaluator as a parked, hash-pinned negative control. Do not
adjust its three-halves/two-pot branch, append a size, relax `0.90`, select a
friendlier subset, or reuse either opened family as confirmation.

The result sharpens the next mechanism question: small payoff-span-normalized
loss can coexist with materially incomplete recovery of the available sizing
gain. A successor must state which mechanism should recover that missing gain
under bounded action width, and must commit its source rule and wholly fresh
panel protocol before code or values. This ADR authorizes writing that
prospective preregistration only; it does not authorize a specific v4 source,
new values, a wider lattice, or integration.

## Evidence classification

- **Known:** exact source and panel identities, family order, arms, widths,
  units, result bytes, stop state, raw-chip arithmetic, and numerical records.
- **Reproduced:** candidate tuples, collision branches, values, loss and
  recovery summaries, teacher agreement, pivots, deterministic hashes, and
  representative-first fail-closed stopping.
- **Rejected:** collision-repair v3 as the passed reduced sizing candidate.
- **Unopened:** any successor source, fresh successor panel, successor value,
  reference-hand compatibility, and every integration path.
- **Hypothesis:** a materially different bounded-width mechanism can recover
  the missing qualified sizing gain on new prospective panels.

## Claims boundary

This result establishes only that collision-repair v3 fails one preregistered
reduced one-bet quality conjunct on two fresh four-by-four families. It does not
show that v3 is weak in production poker, that another abstraction is stronger,
that more actions improve end-to-end quality, or that the reduced games are
representative of six-max play. It establishes no strategically exact
translation, production range width, earlier-street quality, multiplayer
safety, runtime decision quality, 15-second feasibility, blueprint or resolver
strength, NashConv, AIVAT, league strength, C5 completion, or complete bot.
No revoked experiment, external publication, or thesis change is authorized.
