# ADR-0288: Complete reference hands pass the exact one-seat loop

- Status: accepted complete-reference correctness result; no strategy-quality, scalability, latency-distribution, or deployment result
- Date: 2026-08-23
- Follows: ADR-0287
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0288
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Preregister a full-width one-seat belief and immutable-blueprint boundary with an exact collision-aware joint-card oracle before any factorized approximation, action abstraction, convex master, or resident resolver may feed the complete-hand loop
- Front-Door-Blockers: no Bayesian opponent-range update or collision-aware five-opponent belief exists, the reference action source is passive and untrained, and no fixed action abstraction, trained full-game blueprint, or strategy-producing resolver is connected

## Question

Does ADR-0287's frozen public/private-card, immutable-source, replay, settlement,
and charged-time contract pass without changing either primary fixture or
opening a strategy result?

## Decision

Accept the ADR-0287 complete-reference checkpoint as passed and retain its
explicit-deal replay as the required exact oracle beneath the next full-width
belief/blueprint gate. Keep the passive reference source as the only complete-
hand fallback until that successor is separately preregistered and validated.

## Result

Pass, within the preregistered engineering claims boundary.

`pontius.holdem_cards` now separates the complete six-seat explicit-deal oracle
from `OneSeatCardState`. The latter carries only the controlled private pair and
the currently revealed board. Exact compatible domains for one unknown
opponent contain 1,225 combinations preflop, 1,081 on the flop, 1,035 on the
turn, and 990 on the river. Two deals that differ only in opponent cards and
future runout produce identical preflop and shared-flop decision views.

`pontius.immutable_blueprint` now supplies a frozen, canonical-byte,
SHA-256-bound lookup keyed by the visible cards and complete public betting
state/history. Its entries cover semantic fold, check, call, and exact integer
raise-to actions. Duplicate keys and mutable outer aliases reject. Every table
hit is revalidated against the current `LegalBettingDecision`; an illegal stale
entry aborts. A miss uses only the frozen total rule check, else call, else fold.

`pontius.reference_hand_replay` joins the card and action source to the existing
`LegalDecisionSpine`. Betting initialization, visible-card construction,
card-domain audit, opponent-event validation, opponent-action application,
controlled-decision opening, blueprint selection, controlled emission,
betting-street transition, and public-card reveal each have a named charged
operation. Every operation owns exactly one ledger interval. Transition work
belongs to the street it closes; reveal work belongs to the new street.
Post-terminal hand evaluation and settlement verification remain separately
reported harness work.

### Frozen primary fixtures

Fixture A emits controlled actions `call/check/check/check`, consumes all 20
opponent events in exact cyclic order, closes preflop/flop/turn/river, and
settles one 12-chip pot entirely to seat 3's manually fixed K-high straight.

Fixture B emits controlled actions `call/call`, consumes all seven opponent
events, closes all four streets through the all-in runout, and finishes with
contributions `(10, 6, 4, 20, 20, 20)`. The test-only chip-depth oracle builds
actual pots `(24, 10, 16, 30)` without calling production pot assembly. Its
manually fixed showdown ordering independently yields payouts
`(16, 10, 24, 30, 0, 0)`, matching production settlement and conserving all 80
chips.

The immutable fixture digests are:

- Fixture A deal
  `ed0c0a2f2b52b84242ebae19e24c1f0e82569de4d279bd3ded55815fc976fab8`
  and empty-source digest
  `ad15637ba8e7a1de8fc2bc5423c4c547df0f12964406841d407d491073385202`.
- Fixture B deal
  `2f9532f4d8513a904d9ccba508c400a35a301e3003e69ddae01dee288fab2abf`
  and empty-source digest
  `65b36176375e65a3822a1a9c06cfc2260f00c10f280a1aa5c6bc1743779016d6`.

### Timing trace

One ordinary-monotonic maintained smoke invocation recorded:

| Fixture | Preflop | Flop | Turn | River | Named intervals |
|---|---:|---:|---:|---:|---:|
| A | 0.5368 ms | 0.2594 ms | 0.2301 ms | 0.2222 ms | 64 |
| B | 0.2820 ms | 0.1617 ms | 0.0351 ms | 0.0341 ms | 33 |

These values measure only the small Python reference replay on the two explicit
fixtures. They are not a resolver latency, per-iteration measurement, cold/warm
distribution, p95 estimate, or quality prior. The gate is that every closing
snapshot stays under 15 charged seconds and that its interval count is exactly
the number of named replay operations for that street. A deterministic stepping
clock independently exercises positive interval ownership and exact
preflop-to-river reset/finalization order.

## Validation

- Twenty-two new maintained tests cover explicit-deal distinctness and future
  blindness, exact card-removal counts and enumeration, 200 deterministic
  random deals, evaluator determinism, all four blueprint actions and raise
  bounds, canonical digest behavior, semantic-type mutations, both primary
  replays, independent pots/payouts, manually fixed rank order, interval-ledger
  bijection, and ordinary-monotonic execution.
- Wrong actor, wrong street, missing/extra events, controlled-seat script
  injection, illegal table actions, duplicate/overlapping cards, early future
  reveals, mutable aliases, numeric booleans in semantic fields, and key/context
  mismatches fail closed.
- The new tests pass together with the existing betting, exhaustive pot,
  one-seat, and deadline controls: 55 tests, including 45,456 exhaustive
  three-chip semantic betting states and 60,732 transitions.
- The complete repository suite passes 1,087 tests with two
  expected revoked-runner skips and no failures. Changed-file Ruff, Python 3.11
  syntax parsing, generated-status freshness, maintained-link/documentation
  integrity, and whitespace checks pass.

Two invocations were rejected by existing plumbing controls. The first focused
command omitted the documented `PYTHONPATH=src` boundary and stopped at import
with three loader errors; no test or replay code ran. The first front-door
generation attempt then rejected this ADR because its accepted controller
snapshot had a `Result` section but no required nonempty `Decision` section.
Using the shared runbook invocation passed the focused suite, now 22 tests, and
adding the required heading let the unchanged result generate normally. This is a two-
invocation plumbing tax, not a fixture mismatch; no fixture, expected result,
timer boundary, or gate changed after either rejection.

## Consequences

Pontius now has the first complete deterministic hand loop for one controlled
seat across all four streets, explicit chance outcomes, exact legal betting,
exact card removal for each individual unknown opponent, immutable fallback
selection, showdown, settlement, and cumulative charged-time ledgers. This
discharges the ADR-0287 reference integration gate and makes ADR-0286's legal
spine executable against real hold'em cards.

The next checkpoint must not connect the reduced h32 convex master directly.
It should first preregister a full-width observation-to-belief-to-blueprint
boundary: exact per-opponent combo supports, a collision-aware joint-card oracle
against which factorized representations are measured, immutable policy and
action-size provenance, and exact projection back through
`LegalBettingDecision`. Any normalization, blocker, likelihood, provenance, or
legal-projection mismatch kills that gate and retains the passive reference
source.

## Claims boundary

This result does not establish a joint five-opponent Bayesian belief, action-
conditioned range update, trained or strategically credible blueprint, chosen
bet-size abstraction, off-tree translation, resolver integration, real-time
cancellation, optimized latency, live hand-history/dealing adapter, shuffle or
burn procedure, league strength, AIVAT, exploitability, NashConv improvement,
or a complete C5 bot. It exposes all legal integer raise amounts through the
reference contract but does not enumerate them as a deployable action set. No
h32 GPU experiment, strategy label, revoked runner, or external publication was
opened.
