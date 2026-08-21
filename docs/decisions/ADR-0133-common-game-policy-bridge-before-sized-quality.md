# ADR-0133: Score both action-width arms in one complete sized game

## Status

Implemented and checked only on the existing two-hand-per-seat control.  No h32
sized policy, best response, NashConv, or action-width quality label has been
constructed.

## Context

ADR-0132 closed the h32 residency question and left action value per wall-clock
second unmeasured.  Comparing one-size NashConv in a one-size game with
two-size NashConv in a two-size game would not answer that question: the
deviation universes differ.  Deleting the added action also leaves behavior
below that action undefined.

The comparison therefore needs an explicit full-universe completion and an
exact sized evaluator before its h32 budget or outcome gates are frozen.

## Decision

Every arm will be deployed and evaluated in the same two-size game with opening
bets of `3` and `6` chips and game-derived payoff span `48`.

Complete a one-size policy as follows:

1. preserve its check probability;
2. map its unsized bet probability to the `3`-chip bet;
3. assign exactly zero opening probability to the added `6`-chip bet; and
4. below both sized bets, copy the one-size fold/call distribution from the
   history obtained by erasing the amount.

The fourth rule is load-bearing.  A missing row would silently default to a
uniform response, while deleting the branch would change the best-response
universe.  The copied continuation is complete, fixed before labels, and uses
no sized-game value.

Because sized policies use typed `BetAction` keys, their evidence identity may
not rely on JSON object-key coercion.  Serialize each action as a type-bound
token and digest the ordered row representation.  Deserialization must recover
the exact live layout schema and reproduce the digest.

Add an exact profile evaluator using the accepted scale-canonical affine cache,
the contribution-aware terminal keys, and the same target-omitted reverse pass
as the frozen one-size resident evaluator.  This evaluator is the common-game
teacher and later fixed-envelope verifier; it is not a selector feature.

## Development controls

Only the pre-existing h2 sized fixture was used.

- The completion contains every sized information set and exact action schema.
- Every added opening action has zero probability.
- Embedded and one-size profile utilities agree within `2e-13`.
- Typed policy serialization round-trips exactly and changes digest when added
  bet mass changes.
- Canonical-affine resident evaluation agrees with the dense sized teacher
  within `2e-12` for all six utilities, best responses, deviation gains, and
  NashConv.
- The resident evaluation has zero-sum residual below `2e-12` and uses the
  expected 378 semantic bases.

These are implementation controls, not evidence that either width improves
strategy.

## Consequences

The next preregistration may compare wall-clock-matched one-size and two-size
planning from one immutable incumbent without crossing game definitions.  Its
primary quality numerator must be exact two-size NashConv reduction from this
same completed incumbent.  Fixed-envelope acceptance must remain anchored to
the incumbent's six-seat sized-game deviation vector.

Construction, planning, and exact verification bills must be separated and
reported.  Exact labels may verify or reject a completed candidate but may not
change the planning deadline, candidate generator, or off-tree completion.

## Dissent

**Confidence:** high in the completion and exact evaluator after the dense h2
control; moderate that copying the small-bet response is the most useful
off-tree convention; low in any strategy value for the added action.

**Opposing evidence:** a zero-probability added action can expose poor copied
responses to a unilateral bettor.  That is not a verifier defect; it is the
actual vulnerability of the declared one-size deployment completion.

**Largest unknown:** whether sized planning can repair that vulnerability and
still beat the faster one-size arm after cold construction and verification are
charged.

**Cheapest falsification:** a preregistered h32 comparison on the four frozen
fresh-board targets, with no outcome gate and both arms scored through this
common teacher.
