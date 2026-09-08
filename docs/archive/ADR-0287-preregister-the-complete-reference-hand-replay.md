# ADR-0287: Preregister the complete reference-hand replay

- Status: accepted executable correctness preregistration before any reference-hand replay result
- Date: 2026-08-23
- Follows: ADR-0286
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0287
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Execute the two frozen complete reference-hand replays once, record every mismatch, and keep resolver integration closed until every correctness and timing gate passes
- Front-Door-Blockers: the public-card adapter, private one-seat view, immutable reference blueprint source, and complete-hand replay harness do not yet exist, and no end-to-end charged street trace has passed

## Question

What is the narrowest executable gate that can connect ADR-0286's exact legal
betting and timing spine to real hold'em cards without smuggling in a strategy,
an action abstraction, or future private information?

## Decision

Preregister one additive CPU reference integration with three boundaries:

1. an explicit six-seat deal and public-board state using the already validated
   exact card representation and seven-card evaluator;
2. an immutable one-seat blueprint action source that receives only the
   controlled private hand, currently revealed board, exact public betting
   state, and legal-action contract; and
3. a complete-hand replayer that routes the controlled seat only through
   `LegalDecisionSpine` fallback emission while applying frozen opponent
   actions and exact public-card transitions.

This is an engineering correctness gate. It opens no strategy-quality label.

### Frozen card contract

A replay input supplies six canonical two-card private hands and one ordered
five-card board runout. All 17 playable cards must be distinct and in the
52-card deck. The full deal remains inside the replay/oracle boundary. The
agent-visible state contains exactly the controlled two cards and the currently
revealed board: zero cards preflop, three on the flop, four on the turn, and
five on the river. It must not retain opponent cards or unrevealed runout cards.

Exact card removal is discrete. Given only the controlled hand and public
board, the compatible two-card domain for one unknown opponent must contain
exactly 1,225 combinations preflop, 1,081 on the flop, 1,035 on the turn, and
990 on the river. A complete explicit deal must remain pairwise compatible
across all six seats and the board. This gate does not construct a Bayesian
range or enumerate the joint five-opponent range.

The input is an explicit chance outcome, not a physical dealing protocol.
Shuffle entropy, burn cards, muck recovery, exposed-card procedures, and deck
reconstruction remain outside this checkpoint.

### Frozen blueprint contract

The reference blueprint is an immutable, digest-bound lookup table keyed by
the controlled private hand, currently revealed board, button, street, exact
public betting state, and complete public action history. No key contains an
opponent private card or a future board card. A table entry may name any exact
legal `fold`, `check`, `call`, or `raise-to` action, including an exact integer
raise amount. Duplicate keys, mutable aliases, and nonsemantic actions reject.

An absent entry uses the deliberately weak total rule `check`, else `call`,
else `fold`. The source never invents a raise amount. Every selected action is
revalidated against the current `LegalBettingDecision`; an illegal frozen entry
fails closed rather than silently becoming passive. This is a reference
fallback source, not a trained or strategically credible full-game blueprint.

### Frozen replay fixtures

Run exactly these primary fixtures, plus adversarial mutations and randomized
card-removal checks that reveal no strategy result.

**Fixture A: passive four-street showdown.** Button 0, six equal 100-big-blind
stacks, blinds 1/2, controlled seat 3, board `2c 7d 9h Js Qc`, and private
hands `(As Ad) (Kh Kd) (Ts 8s) (Ks Td) (Ah 3h) (4s 5s)`. The empty-table
reference blueprint must call preflop and check flop, turn, and river. Frozen
opponents call/check. The hand must produce four controlled emissions, four
closed street ledgers, a 12-chip single pot, and a seat-3 K-high-straight
showdown win.

**Fixture B: multiway all-in side-pot runout.** Button 0, stacks
`(10, 6, 4, 20, 20, 20)`, blinds 1/2, controlled seat 5, the same board, and
private hands `(As Ad) (Th 8h) (Kc Tc) (Kh Kd) (Ah 3h) (4s 5s)`. Seat 3 raises
to 10 preflop, the remaining opponents call, and the passive controlled seat
calls. On the flop seat 3 raises all-in to 10, seat 4 calls, and the controlled
seat calls. The all-in runout must close all four street ledgers. Independently
constructed actual pots must be `(24, 10, 16, 30)` with payouts
`(16, 10, 24, 30, 0, 0)`.

### Timing and replay accounting

Initial visible-card construction, opponent-event decoding and validation,
blueprint key construction and lookup, legality checks, controlled emission,
betting transitions, and public-card reveal/validation are agent work and must
occur in explicit charged intervals. Opponent think/transport idle remains
paused. Betting-transition work closes the prior street; public-card reveal is
charged to the new street. Post-terminal settlement verification is evaluation
harness work, reported outside the decision ledger and never described as
available decision time.

Each fixture must retain exactly one immutable closing snapshot for preflop,
flop, turn, and river; no street may exceed 15 charged seconds; no action may
reset a street budget; and the final street must be frozen. Tests use a fake
monotonic clock for adversarial accounting and the ordinary monotonic clock for
the maintained replay.

## Gates

The checkpoint passes only if all of the following hold:

- every card, street-reveal, distinctness, visibility, and exact combination-
  count gate passes;
- blueprint keys are future-blind and opponent-private-blind, source bytes are
  immutable/digest-bound, all four action kinds can be represented, and every
  emitted fallback is exactly legal;
- both frozen fixtures reproduce their action order, contributions, pots,
  payouts, four street snapshots, and chip conservation;
- a test-only chip-depth pot/payout oracle and manually fixed showdown ordering
  agree with production settlement without calling production pot assembly;
- wrong actor/street, missing/extra events, duplicate cards, future reveal,
  illegal blueprint entries, and mutable-alias mutations fail closed;
- deterministic randomized explicit deals preserve 17-card uniqueness, public
  visibility, combination counts, and evaluator determinism; and
- the complete repository suite, changed-file lint, Python 3.11 parse, generated
  front door, documentation integrity, and whitespace checks pass.

## Kill criterion

Any mismatch in legal action, public/private visibility, card-removal count,
board transition, pot, payout, chip conservation, or street ledger rejects the
checkpoint. Any opponent or future card reaching a blueprint key, any
semantically material replay operation deliberately left outside a charged
interval, or any attempt to rescue a failure by changing a frozen fixture,
expected result, timer boundary, or rule also rejects it.

On rejection, retain ADR-0286 as the active foundation, record the failed
invocation, and do not connect the convex master, resident resolver, action
abstraction, or h32 strategy path.

## Claims boundary

A pass would establish only a deterministic complete-hand reference loop for
one controlled seat and explicit chance outcomes. It would not establish a
Bayesian six-seat range, a trained blueprint, equilibrium quality, off-tree
handling, action abstraction, real-time cancellation, optimized latency,
league strength, live-site integration, or a complete C5 agent. No h32 GPU work
or strategy label is authorized by this preregistration.
