# ADR-0039: Preserve the full action universe while measuring selective expansion

**Status:** Accepted

**Date:** 2026-08-19

## Context

ADR-0038 established that the three-bet/two-raise river tree is an exact
reference universe, but its sparse recomputation performs about 2.7 times as
much absolute work as the nested one-bet/one-raise tree. The missing numerator
is the full-universe strategy quality bought by that work.

A conventional restricted-game wrapper is not an adequate first test. Removing
an action from `legal_actions()` forces its probability to zero. A supposedly
zero-work candidate would therefore differ from the blueprint, and information
sets below the removed action would disappear without a defined deployment
policy. That conflates search improvement, abstraction damage, and off-tree
completion.

## Decision

Represent an action mask as a **selective-expansion mask**, not a legal-action
mask.

At every reached information set:

1. expose the complete action tuple from the full 3x2 game;
2. traverse selected nonterminal actions normally;
3. terminate every unselected nonterminal action at the exact continuation
   value of the unchanged blueprint; and
4. deploy the candidate only at information sets materialized by the selective
   tree, retaining the blueprint exactly at every other full-game information
   set.

Thus an unexpanded action remains selectable, but play below it remains the
blueprint. The initial warm policy can be exactly the full blueprint; omitted
actions never acquire an implicit zero probability.

The first deterministic nested chain is:

| Mask | Expanded opening bets | Expanded raise-to sizes |
|---|---|---|
| `b1r1` | `0.50P` | `1.50P` |
| `b2r1` | `0.25P`, `0.50P` | `1.50P` |
| `b3r1` | `0.25P`, `0.50P`, `0.75P` | `1.50P` |
| `b3r2` | `0.25P`, `0.50P`, `0.75P` | `1.50P`, `2.00P` |

Fold, call, and check branches already terminate and are always evaluated
exactly. `b3r2` must be behaviorally identical to solving the unwrapped full
game.

## Required invariants

Before an opportunity experiment may run:

- zero solver iterations plus blueprint warm initialization composes to the
  blueprint exactly;
- every reached information set exposes the full-game action schema;
- information sets absent from the selective tree remain exactly equal to the
  blueprint after composition;
- the composed policy is complete and normalized in the full game;
- full expansion matches an ordinary full-game solver at every tested
  checkpoint; and
- selective-tree terminal utilities agree with independently evaluated
  blueprint continuations.

## Measurement contract

The source range receives one strong full-3x2 blueprint. Online candidates
adapt that same blueprint to perturbed target ranges. Every candidate is
evaluated in the unmodified target 3x2 game. Restricted-tree NashConv is not a
quality target.

The primary deterministic cost is alternating CFR state visits. The experiment
also records serial wall time, tree states, materialized information sets, leaf
count, and exact-leaf construction cost. Exact continuation values are an
oracle control: their cold cost is charged and their hot cached cost is shown
separately. Neither timing is a neural-latency claim.

The primary quality numerator is target full-universe NashConv reduction from
the unchanged source blueprint. Negative reduction is harm. Quality per work
is reduction per million charged solver-state visits; serial reduction per
millisecond is secondary until a native kernel exists. Blueprint construction
is reported as offline cost and is identical across masks.

Exact target evaluation and future checkpoint labels may score records but may
not select a deployable mask. A per-context best mask is an oracle ceiling only.

## Development sequence

1. Prove the wrapper and composition invariants on tiny deterministic games.
2. Run a small development-only pilot over all four range families and sparse
   versus factorized target changes.
3. Use the pilot only to choose blueprint strength, warm-start scaling, work
   budgets, and falsification thresholds.
4. Freeze those choices before a larger group-separated development matrix.
5. Optimize a native branch layout only if a partial expansion lies on the
   full-universe quality/work Pareto frontier.

Validation and test board groups remain sealed during these steps.

## Consequences

This is a stronger and more realistic control than deleting actions, but it is
not yet continuous bet generation. Every reference action still appears at its
parent information set, and exact leaf construction is far more expensive than
the neural leaf interface it stands in for. A later neural experiment must pay
its real inference and batching cost and must reproduce root-strategy quality,
not merely leaf mean-squared error.

If `b1r1`, `b2r1`, or `b3r1` cannot match `b3r2` quality per work with exact
leaves, selective branching is rejected for this workload before C++
specialization. If exact selective expansion helps but realistic leaf error
erases the advantage, neural leaves rather than traversal become the binding
bottleneck.

