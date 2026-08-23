# ADR-0286: Install the exact six-seat legal decision spine

- Status: accepted reference-game and runtime engineering control; no strategy-quality or deployment result
- Date: 2026-08-23
- Follows: ADR-0285
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0286
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Connect public-card state and an immutable-blueprint action source to the legal decision spine, then preregister a full-hand reference replay before optimizing it
- Front-Door-Blockers: no public-card or card-removal adapter consumes the betting spine, no full-game blueprint supplies its fallback actions, and no end-to-end charged 15-second street trace has been measured

## Question

What exact public betting and timing boundary should connect Pontius's reduced
six-player river controls to a future full-hand one-seat agent?

## Decision

Adopt `pontius.no_limit_betting.NoLimitBettingState` as the additive reference
betting kernel and `pontius.legal_decision_spine.LegalDecisionSpine` as its
one-seat runtime boundary. The simplified historical river games remain
unchanged because they are sealed research workloads, not full-game rules.

### Named rule profile

The reference kernel uses the Poker TDA 2024 no-limit full-bet profile. A raise
must add at least the largest prior full bet or raise on the street; an all-in
may be shorter; multiple short all-ins reopen a previously acted seat only when
the cumulative amount that seat now faces reaches a full increment. The last
full increment remains the minimum raise unit. These choices match
[Poker TDA Rules 43 and 47](https://www.pokertda.com/view-poker-tda-rules/).

This is a named deterministic research profile, not a claim that every cash
room has identical house procedures. The first implementation is exactly six
dealt-in seats, integer chips, small and big blinds, no ante, and no rake. The
charter factory uses equal 100-big-blind stacks. Empty-seat, heads-up blind,
straddle, missed-blind, rake, and live-dealer gesture rules remain outside v1.

### Betting state and legal actions

Opening bets and raises use one `raise-to` action whose amount is the player's
total contribution on the current street. Every on-clock decision reports the
exact fold/check/call alternatives, the short all-in call amount, the minimum
full raise-to, the player's maximum raise-to, and the maximum amount another
live stack can contest. A short all-in is the only legal raise below the full
minimum. A player cannot raise when betting has not reopened or no opponent can
answer any increment.

The immutable state carries stacks, per-street and per-hand contributions,
folds, last-action wager levels, the last full raise increment, exact cyclic
pending order, action records, and terminal reason. Preflop begins left of the
big blind; later streets begin at the first live, non-all-in seat left of the
button. A transition advances exactly preflop to flop to turn to river to
showdown and resets only street-local betting state.

### All-ins, uncalled chips, side pots, and settlement

Round closure returns the unique unmatched top wager before another street or
settlement. Contribution thresholds are first represented as exact layers.
Adjacent layers with the same eligible live seats are then merged into one
actual pot, so a folded-only threshold cannot create a second odd-chip award.
Each actual side pot is awarded independently; ties split in integer chips and
the first tied winner left of the button receives the first odd chip, matching
[Poker TDA Rules 20 and 21](https://www.pokertda.com/view-poker-tda-rules/).
Payouts, net chip returns, and final stacks must each conserve the table total.
Showdown strengths are supplied by the card/game layer; this kernel does not
pretend that betting state alone evaluates a hand.

### One-seat charged-time boundary

The successor `StreetDeadlineLedger` measures cumulative monotonic wall time
only while agent work is explicitly charged. Opponent think or transport idle
does not consume the 15-second street allowance. The production factories
construct and validate the initial hand state inside the first charged
interval. Observed-action processing, legality work, foreground resolving,
useful background computation, candidate selection, and fallback preparation
also consume it. Overlapping CPU/GPU work is one wall interval, not the sum of
device times. The ledger persists across all controlled-seat actions on a
street. Betting transition processing is charged to the closing street. An
exact next-street transition archives the immutable closing snapshot before
reset; fold and showdown archive and freeze the final street, so reset cannot
erase the audit trail.

The fixed one-second synchronization and emission reserve remains inside the
15 seconds. The one-seat controller accepts a candidate only if it is legal and
completed before that reserve; otherwise it atomically applies the caller's
legal immutable-blueprint fallback. A result that crosses the full street wall
also falls back. The controller does not manufacture a passive fallback or
claim that one exists when the blueprint has not supplied it.

## Validation

- Focused tests cover all four action kinds, raise-to bounds, full and short
  raises, an unacted big-blind option, seat-specific and cumulative reopening,
  unmatched refunds, four all-in layers, folded-only thresholds, independent
  pot splits, odd chips, all streets, invalid actions, idle/charged timing,
  repeated controlled actions, late/illegal candidate fallback, and exact
  ledger reset, closing-snapshot retention, and fold/showdown finalization.
- Two hundred deterministic randomized full-hand walks preserve per-seat and
  table chip conservation, pending-order eligibility, pot coverage, and
  zero-sum settlement.
- A maintained independent chip-depth oracle exhausts every integer action in
  the three-chip six-seat game for all six button positions: 45,456 distinct
  semantic states, 60,732 transitions, and 7,830 terminals. Its separately
  constructed pots and two showdown profiles agree at every terminal.
- The complete suite passes 1,065 tests with two expected revoked-runner skips
  and no failures. Ruff and Python 3.11 syntax checks pass on the changed code.

These are reference-state and regression checks, not certification of every
casino procedure, arbitrary hand reconstruction, or optimized implementation.

## Consequences

The project now has a legal action/chip/timing spine that can carry one seat
through an entire betting hand. This discharges the betting, side-pot, all-in,
reopening, and street-ledger foundation of C5, but not C5 itself.

The next gate must attach public cards, exact card removal, and a deliberately
weak immutable-blueprint action source, then replay complete hands through the
same one-seat boundary. Only after that reference loop is correct may action
abstraction, the convex master, or the resident resolver propose candidates.
Latency optimization must compare against the reference trace and may not
weaken legal semantics.

## Claims boundary

No card deck, private/public card state, Bayesian range update, full-range
blueprint, action abstraction, convex solve, GPU solve, strength league, or
external poker action ran. The existing h32 research head and every sealed
strategy label are unchanged. This ADR establishes an exact reference betting
and charged-time control, not a complete poker bot, a complete extensive-form
hold'em game, a 15-second end-to-end pass, or evidence of decision strength.
