# ADR-0308: Install the action clock and preparation bank

- Status: accepted runtime engineering control; no strategy-quality, preparation-utility, complete-hand, or deployment result
- Date: 2026-08-23
- Follows: ADR-0307
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0308
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Construct and seal only ADR-0305's value-free 48-context representative, 96-context qualified-A, and 96-context qualified-B streams from their frozen seeds; keep every qualification and candidate value unopened and do not reinterpret historical timing under ADR-0307
- Front-Door-Blockers: all three v4 structures and every v4 value remain unopened; action-clock v2 is not connected to the complete-hand replay or a live host; no prepared artifact has demonstrated useful hit rate or decision-quality gain; no credible blueprint, integrated resolver, or complete bot exists

## Decision

Accept the additive ADR-0307 timing successor. Pontius now has an executable
15-second continuous response wall for each controlled action, separately
measured online preparation, exact one-use artifact credit, and an exact legal-
decision-spine v2. The superseded cumulative-street ledger and controller remain
unchanged for historical reproduction.

This is the resource-accounting foundation for the governing objective:
maximize marginal chip-valued decision quality per additional millisecond of
attributable online workstation compute, subject to a hard 15-second response
deadline on every controlled turn. It does not yet measure a decision-quality
curve or show that preparation is useful.

## Implementation

`pontius.action_clock.ActionClockLedger` owns:

- one fixed 15,000 ms continuous response wall per controlled action and a
  fixed 1,000 ms synchronization/emission reserve;
- an immutable action identity carrying street, hand/street action indices,
  and the exact public betting-state SHA-256;
- distinct continuously elapsed response wall, explicitly timed response work,
  uninstrumented on-clock wall, and preparation totals;
- an event boundary captured before state construction or action application,
  so work is classified as response work when the event yields the controlled
  actor and as preparation otherwise; and
- immutable completed-action and completed-street archives.

The ledger exposes no transition reset. A street can advance only while an
owned event boundary is active, and an action cannot pause, overlap another
interval, start in the future, or survive a reversed monotonic clock. Credited
preparation is reported on the action snapshot but is never added to
`remaining_seconds` or `work_remaining_seconds`.

`pontius.preparation_bank.PreparationBank` owns each work interval and hashes
the immutable artifact bytes itself. A sealed credit binds the artifact bytes
and SHA-256, target public state, consumer-defined semantic context, source,
creation street, and exact internally measured interval. Claims require an
active controlled action, validate the credit against that action's public-
state identity, attach once, and reject absent, invalidated, stale, duplicate,
mutable, or already-used artifacts. Aborted and duplicate work remains charged
and visible. The supported attachment path is the bank claim; the ledger's
attachment hook is private.

`pontius.legal_decision_spine_v2.LegalDecisionSpineV2` composes those controls
with `NoLimitBettingState`. Its production hand factory captures the external
boundary before exact state construction. Opponent actions and street advances
capture a boundary before applying the transition. The spine derives the
public-state digest from the complete exact betting state and does not accept a
caller-supplied current-state digest during a bank claim. A prebuilt state in
which the controlled seat is already acting is rejected unless it arrives with
the matching boundary-started action clock; this prevents a constructor from
starting the live timer late.

Legality, candidate validation, and fallback application remain exact. A
candidate ready after the 14-second work cutoff is discarded, and crossing the
15-second final wall forces the supplied legal immutable fallback. The new
modules import only exact betting and timing dependencies; no action
abstraction, sizing value, blueprint, convex master, resolver, or GPU primitive
entered this checkpoint.

The accepted source files have SHA-256:

- `pontius.action_clock`: `d1540ec3ce25b8247cf990b8649e3af0ebe9f3d25a98322aaf141afddf9a55bb`;
- `pontius.preparation_bank`: `4fb996a0988c74efecbe00574fd9c9d6601950e4cf74faea8d6d21d127f769ef`;
- `pontius.legal_decision_spine_v2`: `a480918d5c6e5d06e2076ef64f7cccf14b63f61162b7b9d24dd7cae35825fca9`.

## Verification

Twenty-two focused deterministic tests pass. They cover independent same-
street response walls, the reserve and final deadline under uninstrumented
elapsed time, first-actor construction, later-actor event processing, exact
street archives, prior- and same-street preparation hits, stale public state,
stale semantic context and source, double claim, invalidation, absence,
duplicate and aborted work, wrong phases, immutable bytes, malformed state
identity, late-constructor rejection, exact fallback legality, all-in runout,
clock reversal, and static dependency closure.

The unchanged ADR-0282/0286 ledger, legal spine, exact betting engine,
exhaustive small-stack traversal, and complete-hand replay pass their 41-test
compatibility slice. The repository-wide suite passes 1,183 tests with two
intentional skips. Ruff lint and format checks pass on every changed Python
file. A tracked diff against ADR-0307's parent confirms that the historical
`street_deadline` and `legal_decision_spine` sources and tests were not edited.

## Consequences

- Every controlled turn now receives its own real 15-second response wall;
  repeated actions on one street no longer share the governing allowance.
- Late position may use actual opponent-turn compute and early position may use
  prior-street conditional compute, but only exact artifact hits contribute to
  a later decision.
- A decision may embody more than 15 seconds of attributable online compute
  without pretending that its live response lasted longer than 15 seconds.
- Future quality comparisons must report the marginal chip-valued quality
  curve over response work and preparation spent, including preparation misses
  and invalidation waste. Equal response latency with unequal hidden
  preparation is not an equal-compute comparison.
- A literal host-granted time bank remains absent. If one exists in a future
  deployment, it needs a separate exact adapter and prospective contract.

## Claims boundary

This checkpoint proves deterministic timing, attribution, provenance, and
fallback mechanics only at the exact betting-controller boundary. It does not
show OS-level deadline enforcement, cancellation of an uncooperative solver,
transport/emission success, useful speculative hit rate, strategy improvement,
full-hand v2 integration, a trained blueprint, scalable ranges, action-
abstraction quality, a resolver, GPU performance, or bot strength. The complete
suite is regression evidence, not certification of live behavior.

## Next boundary

Resume only the already-preregistered ADR-0305 value-free structure build in
its frozen order. Seal the 48-context representative stream, then qualified-A,
then qualified-B, recording exact seeds, attempt counts, identities,
within/across-family uniqueness, and absence of frozen-panel counterparts.
Open no value during construction. Any later timing or quality experiment must
use ADR-0307/0308, report both response and preparation compute, and measure a
quality curve rather than one systems-capacity point.
