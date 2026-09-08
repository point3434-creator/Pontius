# ADR-0036: Exact multi-size river betting contract

**Status:** Implemented; frozen transfer passed in ADR-0038

**Date:** 2026-08-19

## Decision

Add a separate `MultiSizeRiverHoldem` game rather than widening
`RiverHoldem` in place. The existing class, normal-form oracle, specialized
incremental evaluator, and frozen artifacts depend on one fixed bet and at most
one fixed raise. They remain immutable controls. The new game implements the
branching-factor workload through the generic game interface so CFR, exact full
evaluation, and `CompiledPolicyDependencyTape` consume it without special cases.

The first measured shape has three opening bet amounts and two raise-to amounts
available after every bet. It still ends after the opener folds or calls the
raise. This isolates action branching before adding re-raises, earlier streets,
more players, all-in side pots, or neural leaves.

## Betting semantics

The game begins on the river with an existing pot `P`, two remaining stacks,
and a normalized joint distribution over compatible private deals. Player zero
may check or choose one configured opening bet amount `b`.

- Check ends betting and goes to showdown.
- Facing `b`, player one may fold, call, or choose a configured raise-to amount
  `r` satisfying `r >= 2b`.
- Facing `r`, player zero may fold or call. There is no re-raise in this game.
- Every configured contribution must be positive, finite, and no larger than
  either remaining stack. Consequently every call is fully matched and this
  checkpoint has no side pot.
- Bet and raise lists are strictly increasing. Legal actions retain this order,
  preceded by check or fold/call as applicable.
- A global raise-to amount may be configured even if it is illegal over a large
  bet; each facing-bet state filters it by the `2b` minimum. The frozen
  branching workload chooses amounts for which both raises are legal after all
  three bets.

Opening bets and raise-to amounts are distinct immutable action types carrying
their exact Float64 amount. They are not the old unsized `BET` and `RAISE`
strings. Check, fold, and call retain the existing string constants.

## Payoff semantics

Utilities are zero-sum net values relative to equal ownership of the pot at the
decision boundary. Let `s` be `+1`, `0`, or `-1` according to player zero's
showdown result.

| Terminal path | Player-zero utility |
|---|---:|
| check | `s * P/2` |
| bet `b`, opponent folds | `P/2` |
| bet `b`, opponent calls | `s * (P/2 + b)` |
| bet `b`, raise to `r`, opener folds | `-(P/2 + b)` |
| bet `b`, raise to `r`, opener calls | `s * (P/2 + r)` |

The raise-fold result charges only player zero's sunk opening bet; unmatched
raise chips are returned. A tied showdown returns `(0, 0)`. `payoff_span` is
`P + 2 * max(max bet, max raise-to)`.

## Information and identity

An information-state key contains the game structural digest, acting player,
that player's private hand, and the exact sized public action history. It omits
the opponent hand and every range probability. Thus two joint ranges on the
same board and betting structure share information-set identity while retaining
different provenance digests.

The structural digest includes a new version tag, board, pot, both stacks, and
the ordered Float64 hex encodings of every bet and raise-to amount. The
provenance digest additionally includes the complete normalized joint range.
Direct cache identity continues to require provenance equality.

## Construction and controls

The class supports explicit joint weights, independent marginal ranges with
card removal, and conversion from an existing `RiverHoldem` context while
preserving its board, stacks, pot, and normalized deal distribution.

Before any measurement, require:

1. every terminal path to match an independently implemented contribution-based
   payoff audit;
2. action legality and minimum-raise filtering at every decision layer;
3. information keys to hide the opponent, remember exact sizes, and distinguish
   different own action sequences;
4. structure/provenance and total-variation invariants;
5. dynamic best responses to match exhaustive pure-policy enumeration on a
   tractable deterministic-deal instance;
6. sparse, dense, and automatic dependency-tape results to match full exact
   evaluation and exact best-response actions on finite DCFR policies; and
7. no modification to `dependency_tape.py` to accommodate sized actions.

The independent payoff audit may enumerate terminal histories, but the existing
fixed-size normal-form equilibrium oracle is not generalized. Its pure-policy
Cartesian product grows exponentially across size-specific information sets
and would be the wrong control for the workload. Full evaluation, exhaustive
single-deal best response, and direct terminal-payoff audit provide independent
correctness boundaries without pretending the wide normal form is scalable.

## Dissent protocol

**Confidence:** high in the one-raise betting and payoff contract; moderate
that this is enough branching to expose dependency-cone growth; low that its
range representation resembles six-player public belief.

**Opposing evidence:** all actions occur on one street, both stacks are
effectively capped to avoid side pots, and no re-raise joins distant action
subtrees. Exact root-deal enumeration still dominates the topology.

**Largest unknown:** whether multiple size-specific information sets make a
two-deal root perturbation dirty most of the best-response selector graph.

**Cheapest falsification:** build one deterministic deal with three bets and two
raises, enumerate every terminal path and pure best response, then compile a
small finite-policy range pair through the unchanged generic tape. Any payoff,
action, or value disagreement blocks the development matrix.
