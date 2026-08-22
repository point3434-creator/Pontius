# ADR-0258: Convex half-retreat delivers material value on all six Latin-E targets

- Status: accepted label-blind six-target result; Latin-F confirmation authorized
- Date: 2026-08-22
- Implements: ADR-0257
- Clean preregistration commit: `2c353a93ca0fd9575e6c76fabbde893cc786a7c2`
- Result: `experiments/results/h32-fresh-convex-retreat-replication-v2.json`
- Result SHA-256: `daaad3080637284d5413f156bad5df19256f8e7a36829026076ea38aeae1355e`

## Formal result

Every provenance, parent, target, source checkpoint, posterior, blueprint,
warm-start, path-single-visit, behavioral-axis, initial-row, resident-row,
new-cut, projection, master primal/dual, campaign-barrier, certificate-
reconstruction, exact-oracle, cap, interior-slack, timing, memory, finite,
immutable-emission, no-global-optimality, and no-population gate passes. The
clean recorded campaign completed in `112.918 s`.

All six candidates froze before the first v2 final retreat label. Every
certificate reconstruction reproduced its pinned checkpoint, posterior,
blueprint, retreat policy, payoff span, source-gain vector, and cap vector. All
six final label barriers then closed in the frozen manifest order. No candidate
was emitted and Latin-F received zero labels.

ADR-0256's caveat remains attached: target 1 is a deterministic label-blind
reconstruction after its final label had been computed but never observed by
the failed v1 invocations. Targets 2–6 opened their final retreat labels for the
first time in this result. No target-1 value or status informed v2.

## The response-classification correction is identified

The v2 classification did real work rather than merely permitting the run.
Target 2 reproduced the three resident response residuals that stopped v1;
their maximum row-to-oracle identity error is `4.72e-16`, and the maximum
epigraph residual `3.07327477e-9` matches the master primal residual within
`2.46e-16`. No duplicate cut was generated.

Target 4 contains one additional verified resident residual and two genuinely
new opponent facets. Across the six targets, the construction records four
resident residual rows and extracts ten new exact response facets. New-cut
counts in manifest order are `2, 0, 2, 2, 3, 1`; five targets use the one
allowed resolve and one needs none. Every first-oracle violator is accounted
for, every new signature is cut, and no target exceeds one round.

This confirms ADR-0256's diagnosis: the v1 stop was a row-classification defect,
not evidence of a missing response direction or an invalid affine row.

## Exact safe value

Every half-retreat is independently cap-feasible with zero recorded maximum cap
violation, passes the `1.48e-9` interior floor, and improves immutable-blueprint
NashConv by more than the frozen `0.001` materiality threshold:

| Target | Family | Actor | Exact value | Minimum cap slack |
|---|---|---:|---:|---:|
| `panel_1/balanced/checks_then_bet_seat2` | balanced | 1 | `0.0084867589` | `1.49999965e-9` |
| `panel_1/blocker_heavy/checks_then_bet_seat3` | blocker-heavy | 2 | `0.0017020214` | `3.0e-9` |
| `panel_2/blocker_heavy/checks_then_bet_seat4` | blocker-heavy | 3 | `0.0056532027` | `1.49999988e-9` |
| `panel_2/balanced/checks_then_bet_seat5` | balanced | 4 | `0.0041009056` | `3.0e-9` |
| `panel_3/balanced/checks_then_bet_seat0` | balanced | 5 | `0.0323617378` | `3.0e-9` |
| `panel_3/blocker_heavy/checks_then_bet_seat1` | blocker-heavy | 0 | `0.0126238918` | `1.49999976e-9` |

Pooled delivered exact value is `0.0649285181`; the median is `0.0070699808`.
The maximum target contributes `49.84%` of the pool, so value is still
heterogeneous, but the positive result is not carried by a single range family
or by one barely passing target. All three balanced and all three blocker-heavy
contexts clear the material floor.

This is the first fresh-panel breadth result for the full one-seat convex
direction space. It establishes that the known-target gain in ADR-0252 was not
an isolated target accident within this frozen Latin-E panel. It does not yet
establish a population rate or superiority to a fresh regret-vertex fallback,
which this campaign deliberately did not label.

## Wall clock and memory

Measured live ledgers range from `4,957.443` to `8,978.541 ms`, including the
warm step, eleven initial passes, master work, first exact oracle, all generated
cuts, final exact oracle, 50-ms retreat/envelope floor, and 1,000-ms emission
reserve. Every component sum reproduces its recorded total exactly.

The effective conservative ledger remains `13,967.6157 ms` for every target,
leaving `1,032.3843 ms` under the hard street boundary. Certificate-context
reconstruction costs `4,668.079–7,578.587 ms`; it is reported and gated but is
correctly excluded from live work because it exists only to release contexts
between the campaign-wide construction and label phases. Its reconstructed
source gains match within `4.45e-16`.

The maximum GPU-pool total is `6,788,487,680` bytes and the minimum recorded
physical free memory is `8,498,708,480` bytes. Both retain wide margins to the
12-GB and 1-GB gates.

## Promotion and claims boundary

The preregistered branch passes at full breadth: six of six targets are
material, both range families are represented, and all measured and effective
conservative schedules fit. Authorize a separate, hash-pinned Latin-F
confirmation using the untouched six-target reserve.

Do not reinterpret that authorization as deployment. Actual external policy
remains the immutable restricted blueprint on all six targets. This result
makes no fresh-fallback dominance, population, full-game, multiplayer-safe,
multi-seat composition, cross-street, exploitation, global one-seat-optimality,
or broad poker-strength claim.

## Decision

Accept the six-target label-blind shadow result and the resident-row
classification correction. Preserve the factor-`0.5` retreat, exact final
certificate, campaign-wide barrier, complete conservative ledger, and
outcome-neutral blueprint fallback. Preregister Latin-F without changing any
scientific threshold or algorithm; use it as the untouched confirmatory test
of the same six-target breadth branch.
