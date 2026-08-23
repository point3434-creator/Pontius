# ADR-0290: Full-width belief and rational policy cross the reference hand

- Status: accepted full-width interface result; no normalized full-width marginal, trained-blueprint, action-abstraction, strategy-quality, or deployment result
- Date: 2026-08-23
- Follows: ADR-0289
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0290
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Preregister an exact-legality action-abstraction boundary with fixed bet-size generation, deduplication, all-in preservation, off-tree projection, and reduced exact quality controls before any abstract action set, convex master, or resolver enters the complete-hand loop
- Front-Door-Blockers: no fixed action abstraction or off-tree projection oracle exists, the rational reference policy is deliberately weak and untrained, scalable five-opponent value contraction and joint sampling remain unvalidated, and no full-game blueprint or strategy-producing resolver is connected

## Question

Does ADR-0289's frozen five-opponent full-combo belief, immutable rational
policy, collision oracle, and charged complete-hand trace pass without reducing
an axis, enumerating the legal raise interval, changing fixture A, or opening a
strategy claim?

## Decision

Accept the ADR-0289 correctness and interface gate as passed. Retain the new
full-width belief and rational policy as additive reference boundaries over the
ADR-0288 replay. Keep the deterministic passive source as the atomic fallback,
and require a separately preregistered exact-legality action-abstraction gate
before any convex master or resolver may propose actions in the complete-hand
loop.

## Result

Pass, within the preregistered claims boundary.

`pontius.full_width_belief` carries one complete canonical hand axis for each of
the five opponents while conditioning on the controlled private pair outside
the factor. The exact axis widths are 1,225 preflop, 1,081 on the flop, 1,035 on
the turn, and 990 on the river. The initial rank-one prior is uniform subject to
the existing exact hard card-disjointness factor. An observed public action
multiplies only its actor's exact rational unary weights; a board reveal filters
all five axes and retains ordered likelihood provenance. The belief digest binds
the visible one-seat state, exact axes and rational weights, opponent order,
actual normalized Float64 factor bytes, and ordered likelihood digests.

Structural full-width counts remain explicitly distinct:

| Street | Hands per opponent | Cartesian assignments | Card-compatible labeled assignments | Persistent numeric bytes |
|---|---:|---:|---:|---:|
| Preflop | 1,225 | 2,758,547,353,515,625 | 1,164,876,344,478,000 | 98,008 |
| Flop | 1,081 | 1,476,143,130,389,401 | 587,192,769,563,400 | 86,488 |
| Turn | 1,035 | 1,187,686,305,646,875 | 462,258,137,741,400 | 82,808 |
| River | 990 | 950,990,049,900,000 | 361,767,238,232,400 | 79,208 |

These are representation and support counts. No full Cartesian tensor was
created, and no normalized full-width marginal or contraction-time result was
opened.

`pontius.full_width_reference_policy` implements the frozen integer weights
from ADR-0289. It retains reduced numerator/denominator pairs and sums the
entire consecutive legal raise-to interval with a five-residue closed form. A
one-billion-chip interval control completes without enumerating its action set.
Arbitrary minimum, interior, and maximum legal raise amounts receive their exact
positive weights. Check or call remains the unique modal action. Opponent
likelihood keys are rebuilt for the hypothetical actor hand and current public
history; the API has no deal, opponent-hand, future-board, model, or mutable
table input. The maintained source digest is
`a8faad1f7ce61f974196884cf028e219486b4ec76d2c8f53a68627e9de851499`.

`pontius.exact_collision_oracle` is independent of the production factorized
belief. It enumerates bounded reduced products in exact `Fraction` arithmetic,
removes overlaps, and returns the exact partition, support, probabilities, and
per-player marginals. A blocker-stress case proves that independently normalized
unary marginals differ positively from collision-aware marginals. Sixty seeded
projections drawn from the maintained full axis, spanning two through five
players and two through five hands each, match production support exactly and
partition/probabilities/marginals within the frozen `1e-12` ceiling. Over-bound,
mutable, non-rational, zero-joint, and numerical-boolean requests reject.

### Complete-hand trace

Fixture A is unchanged. The policy proposes `call/check/check/check`; all four
actions enter through the timely candidate path while ADR-0288's immutable
passive selection remains the exact legal fallback. Before each of the same 20
opponent call/check events is applied, the replay builds the actor's complete
current likelihood and updates only that actor. Each reveal filters all five
axes. The hand still ends with one 12-chip pot and the entire payout to seat 3's
K-high straight.

Initial belief construction, four snapshot/digest audits, 20 likelihood builds,
20 unary updates, four controlled policy selections, and three board filters
each own a named charged interval. Together with the inherited operations, one
ordinary-monotonic smoke trace recorded:

| Street | Charged wall seconds | Named intervals |
|---|---:|---:|
| Preflop | 0.310403 | 30 |
| Flop | 0.346516 | 29 |
| Turn | 0.404363 | 29 |
| River | 0.458494 | 28 |

This is one warm Python reference invocation on fixture A, not a latency
distribution, cold/warm comparison, resolver timing, quality prior, or p95
claim. Every closing ledger is below the authoritative cumulative 15-second
street wall. The four street-start belief digests are
`2a1dfd8e41f39afb8fbe3eb36faf94d9cd2711a3b5e9add24d32e6632abee4d2`,
`d5e5b5b94f0b45ad368206edc8969a4f8f3ed7b834033141305c50b5e5491ec2`,
`eaddb9aa5617014b5968136c230254790543a30adcd17bb800c0b403a82734d7`,
and `6e480497d9d90d87d95f980f6ffb16ecc8b74bcfe204ffb3f60d948308ac661a`.
The terminal belief after all 20 updates has digest
`30ce4dbf08eceea0d0cc7a6b0cb4c0d1b73a1d49d30380b7768474953ea5f2c4`.

## Validation

- Sixteen new maintained tests cover exact full-axis membership and analytic
  support, pairwise blocker counts, actor-only rational updates, board filtering,
  provenance/digests, every exact raise amount on a finite interval, the closed
  billion-chip interval, the independent rational oracle, seeded two-to-five-
  player projections, and the unchanged complete-hand trace.
- Wrong actors, stale/partial axes, stale legal decisions, illegal actions,
  all-zero likelihoods, zero compatible support, board regression, mutable
  aliases, positive Float64 underflow, invalid semantic types, and oracle
  overwork fail closed.
- Sixty-eight related card, betting, deadline, blueprint, belief, oracle, and
  replay tests pass. The complete repository suite passes 1,103 tests with two
  expected revoked-runner skips and no failures. Changed-file Ruff, Python 3.11
  syntax parsing, generated-status freshness, documentation integrity,
  whitespace, and baseline-preservation checks pass.

Before the result was accepted, one diagnostic search used a PowerShell glob
that `rg` did not accept, one direct Python interpreter lacked Ruff, and one
focused test command omitted the runbook's `PYTHONPATH=src` boundary and stopped
with two import-loader errors. The first new-test pass then exposed two expected-
message regex mismatches while production correctly rejected both mutations;
only the assertions were aligned to the existing fail-closed messages. The
first changed-file Ruff pass found four local lint issues, which were fixed
before acceptance. None of these invocations opened a hand result, changed a
formula, relaxed a gate, altered fixture A, or consumed a research label.

## Consequences

Pontius now has an exact symbolic five-opponent range and immutable public-action
likelihood interface across a complete one-seat hand. It demonstrates compact
collision-aware representation and legal amount provenance, not scalable value
evaluation or a credible poker policy.

The next narrow bottleneck is action width. The legal kernel exposes every
integer raise-to amount, but enumerating that interval in a solver would violate
the project boundary. The successor should preregister a small fixed action-set
generator and off-tree projector, preserve exact call and all-in semantics,
deduplicate amounts after integer projection, and compare its decisions and
regret against the exact legal kernel in reduced games. Any hidden clipping,
illegal amount, unstable projection, or material reduced-game loss must kill
that candidate abstraction. No particular sizing scheme is authorized by this
result.

## Claims boundary

This result does not establish calibrated opponent ranges, normalized
five-opponent full-width marginals, scalable joint sampling or contraction,
payoff/value evaluation, a trained or strategically credible blueprint, a
chosen bet-size abstraction, off-tree translation, convex-master integration,
resolving, multiplayer safety, exploitability, NashConv improvement, AIVAT,
league strength, optimized latency, live dealing, or a complete C5 bot. Compact
storage and a passing systems trace are not decision-quality evidence. No
revoked experiment, h32 strategy label, or external publication was opened.
