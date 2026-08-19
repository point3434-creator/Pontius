# ADR-0052: Freeze the exact multiway river and coalition-stress contract

**Status:** Accepted before implementation

**Date:** 2026-08-19

## Decision

Build a configurable two-to-six-player `MultiwayRiverHoldem` reference game,
with three players as the first measured workload. It retains a full five-card
river board, exact two-card private hands, an explicit normalized joint range,
correlation, and exact card removal. It adds multiplayer betting, payoff, and
response-order effects while deliberately allowing only one fixed bet and no
raises.

The machine-readable contract is
`experiments/configs/multiway-river-contract-v1.json`, SHA-256
`b98ee2c73b7b3c93a686ecc5d783756990fbd06b7c911a2e8f52521368e358f4`.

This is the smallest game that can falsify heads-up assumptions about belief
conditioning, folding externalities, unilateral deviations, and collusion. It
is not a proxy claim that this topology captures six-player no-limit hold'em.

## Betting contract

Player zero acts first. Before a bet, each player acts once in seat order and
may check or make the sole configured bet. If everyone checks, all players show
down. Once player `b` bets, every other player responds exactly once in cyclic
order `b+1, ..., N-1, 0, ..., b-1`, choosing fold or call. The final response
ends betting; raises and re-raises do not exist.

The fixed bet must be positive, finite, and no larger than every remaining
stack. Every call is therefore fully matched and no side pot exists. A bettor
whose opponents all fold wins immediately in payoff terms, although the state
may retain the completed response history for auditing.

## Payoff contract

The pot at the river decision boundary is treated as `N` equal sunk shares.
Let `c_i` be player `i`'s new contribution: zero for a checker or folder and the
fixed bet for the bettor and every caller. Let `W` be the non-folded showdown
winner set, including every player tied for the best seven-card hand. Then

`u_i = final_pot / |W| - pot / N - c_i` for `i in W`, and
`u_i = -pot / N - c_i` otherwise,

where `final_pot = pot + sum(c_i)`. If everyone else folds, the bettor is the
sole winner and receives their unmatched economic contribution back through
the same formula. Terminal utilities must sum to zero within `1e-12`.

The maximum individual payoff span is `pot + N * bet_size`. It is the common
normalization scale for unilateral and primary three-player pair-coalition
diagnostics.

## Range, information, and identity

A deal contains one compatible canonical two-card hand per player. The game
accepts either an explicit joint weight table or independent marginal weights;
the latter are multiplied, filtered for public/private card collisions, and
renormalized. Zero-mass deals disappear. Joint correlation is otherwise
preserved exactly.

An individual information key includes the structural digest, acting seat,
that player's private hand, and the complete sized public action history. It
excludes every opponent hand and every range probability. The structural
digest includes version, board, pot, all stacks, bet size, and player count.
The provenance digest additionally includes every normalized joint deal.

For coalition diagnostics only, a team information key includes the acting
seat, public history, and the private hands of every coalition member in seat
order. It excludes outsider hands. This models explicit private-card sharing;
it is intentionally more powerful than ordinary independent players.

## Exact unilateral metrics

For every finite policy profile, report each player's profile utility, exact
unilateral best-response value, and nonnegative deviation gain. Their sum is
NashConv. `exploitability` remains undefined for `N > 2`; NashConv is not
silently divided by two and is not presented as a multiplayer safety bound.

The first conservative post-solve label, `unilateral_pareto_accept`, requires
strictly lower aggregate NashConv and no individual deviation gain increase
beyond `1e-10 * payoff_span`. This is stricter than aggregate improvement and
prevents one seat's increased vulnerability from being hidden by another
seat's gain. It is an operational incumbent rule, not a theorem about future
opponents or coalitions.

## Coalition stress model

For every player pair in the primary three-player game, compute an exact
coordinated best response against the fixed outsider policy. Coalition members
share their private cards and public history, jointly choose all member
actions, and maximize the sum of their utilities with transferable utility.
Chance and outsider behavior remain fixed. Report baseline team value, best-
response value, and nonnegative coalition gain.

This is a deliberately strong collusion stress upper bound. It can model chip
dumping and card sharing; it is neither standard Nash exploitability nor a
guarantee against arbitrary cooperating fields. A separate
`coalition_stress_accept` label requires unilateral Pareto acceptance and no
declared pair's coalition gain to increase beyond the numerical guard. Both
labels are retained so an overly conservative coalition condition cannot be
quietly dropped after outcomes are seen.

## Correctness gates before measurement

Implementation is blocked unless all of the following pass:

1. every reachable terminal history matches an independent contribution and
   tie-splitting payoff audit, with zero-sum error at most `1e-10`;
2. cyclic response order, legal actions, stack validation, and chance mass are
   exact for two through six supported players;
3. explicit joint and independently constructed ranges preserve card removal,
   marginals, conditionals, structure identity, and provenance distinctions;
4. individual information keys hide all opponent cards, remember own prior
   actions, and remain range-independent;
5. coalition keys expose exactly the declared members' hands and no outsider;
6. dynamic unilateral best responses match exhaustive pure-policy enumeration
   on a tractable stochastic three-player game;
7. every singleton coalition response matches the corresponding ordinary best
   response, and a pair response matches an independent enumeration or
   deterministic full-information oracle;
8. the unchanged generic dependency tape matches complete profile utilities,
   best-response values/actions, deviation gains, and NashConv;
9. multiplying pot, stacks, bet, and all utilities by a positive constant
   scales raw metrics while leaving payoff-normalized metrics and response
   actions unchanged; and
10. the complete existing test suite remains green.

No performance, solver-ranking, cache-reuse, or scheduler claim follows from
passing correctness. A separate preregistration will define the first grouped
three-player solve/acceptance matrix only after tree size and exact evaluator
cost are measured without changing this contract.

## Dissent protocol

**Confidence:** high in the game and unilateral-evaluation contract; moderate
that pairwise shared-information response is the most informative first
coalition diagnostic; low that one fixed bet exposes production branching.

**Opposing evidence:** the betting tree resembles generalized Kuhn with real
cards. It may teach mostly range and payoff behavior while leaving action
branching trivial. Coalition sharing may also be so strong that nearly every
finite policy looks bad.

**Largest unknown:** whether exact three-player best responses and coalition
responses remain cheap enough to label a useful grouped dataset once each seat
has several private combos.

**Cheapest falsification:** implement only the exact contract and time a small
three-player range. Any oracle disagreement, information leak, or evaluator
cost that already precludes tens of development contexts blocks the solve
matrix and forces a smaller representation before solver tuning.
