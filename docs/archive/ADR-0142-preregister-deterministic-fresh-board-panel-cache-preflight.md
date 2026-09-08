# ADR-0142: Preregister deterministic fresh-board panel cache preflight

## Status

Frozen after ADR-0141 and before any panel h32 two-size tree, resident cache,
policy, strategy step, or quality measurement.

## Context

Two sized boards now pass the common-game mechanism and show the same deployed
outcome: both one-size and two-size arms abstain on every frozen target because
no non-blueprint candidate completes the immutable unilateral certificate.
ADR-0141 correctly leaves the strategy-quality claim null.  Reworking the
acceptance contract again would not answer whether that outcome transfers
beyond the two already studied boards.

The next useful unit is therefore a genuinely fresh board panel selected
without strategy labels.  Before generating source policies on that panel, the
one-size raw and two-size scale-canonical caches must demonstrate memory safety
under the existing conservative reserve.  This ADR freezes that cache-only
preflight.  It does not authorize a strategy step by itself.

## Label-free board derivation

Use full commit
`3f7a0f7db3571381236dcd3f87e91730f9a29865` as the immutable seed.  This is
the clean commit supplied at the start of the current continuation and predates
the action-width outcomes being replicated.

For each of the 52 canonical card strings, compute SHA-256 of:

`pontius-h32-fresh-board-panel-v1|<full-seed-commit>|<card>`.

Sort by digest and then card string, take the first 15 cards, split consecutive
groups of five, and sort each board by integer card identity.  No range,
showdown rank, cache size, policy, quality label, or prior action-width outcome
enters the sampler.

The exact panel is:

| Board | Cards | Board SHA-256 |
|---|---|---|
| panel 1 | `5c 8c 8d Jc As` | `713e515d802e3f1fbd4fbfb34342c1b55c2f71a76ee506ac3927ed1cc78f6868` |
| panel 2 | `2c 3s 5d Js Qc` | `4cf870db7287e5c9dfe5a2f8e138d55527df7a6c23ad4b22b5f8e3ba806bd9d1` |
| panel 3 | `4h 7h 9s Jd Kc` | `261479623ddcd026fc02b55d773c392f0cecd39c3634592bb88da93f92758418` |

The boards are pairwise distinct, use 15 distinct cards, and are not either of
the two disclosed prior h32 strategy boards.  Repository search before this
freeze found no exact prior board artifact for any panel member.

## Frozen source and target identities

For each board, rebuild the existing deterministic h32 balanced and blocker-
heavy source beliefs with 32 hands per seat.  Apply the same two positive,
support-preserving target shifts:

- double the selected local-blocker hand likelihood at seat 3; and
- scale all-seat likelihoods from 1 to 2 by showdown-strength level.

This gives six source beliefs and twelve target beliefs.  Before any two-size
tree or cache existed, the label-free path froze:

- six exact source-belief SHA-256 digests;
- twelve exact target-belief SHA-256 digests;
- twelve exact canonical target-descriptor SHA-256 digests; and
- unchanged private-hand axes for every target.

All identities are literal in
`experiments/configs/h32-fresh-board-panel-cache-v1.json`.  They cannot be
reselected after seeing cache geometry or strategy behavior.

## Frozen source identities

The machine-readable contract is
`experiments/configs/h32-fresh-board-panel-cache-v1.json`, SHA-256
`a0a23a739098f5286e3df1fd0f4e1ec85cd2ad723551382fe51b57a7be9a4b4d`.
The additive runner is
`src/pontius/h32_fresh_board_panel_cache_preflight.py`, SHA-256
`6dffdb09f105f0159c3216a6ae360111027840c68cbff59189ad6b4a43aac425`.
Its direct control is
`tests/test_h32_fresh_board_panel_cache_preflight.py`, SHA-256
`a4983fcc3eae23607a370d85b71badc53d8f6b9d14e2ec4e03137a4c02475cb8`.
The result target is
`experiments/results/h32-fresh-board-panel-cache-v1.json`.

The contract pins ADR-0141's result and decision, ADR-0139's cache result and
contract, the warm target-construction contract, source-belief constructor,
action-width cache machinery, belief digest implementation, and the new runner
and control by exact SHA-256.  All referenced strict configs are reparsed.

## Frozen cache workload

For every board, range family, and target shift, construct in alternating
order:

1. the one-size resident belief plus six raw automaton caches for bet `3`; and
2. the two-size resident belief plus six scale-canonical caches for bets
   `(3, 6)`.

This produces twelve target rows and 24 cache rows.  Target order is panel,
then range family, then local/strength shift.  Arm order alternates globally as
`one/two, two/one` six times.

Report for every arm:

- belief, automaton, and combined persistent numeric bytes;
- logical automata, canonical bases, total and maximum middle rank;
- cold construction time;
- CuPy pool used and total before and after construction;
- headroom below the 12 GB pool ceiling and physical device free bytes; and
- two-size/one-size ratios for storage, logical width, and construction.

The one-size and two-size layouts must derive payoff spans `30` and `48`.
No panel h32 policy may be initialized, embedded, serialized, trained, or
evaluated.  The runner records zero panel h32 steps, policies, and strategy-
quality evaluations regardless of the memory outcome.

## Headroom decision

Retain the established non-cache reserve of `5,184,456,164` bytes.  A later
panel source-policy preregistration is memory-authorized only if every one of
the 24 cache rows leaves at least that reserve both below the 12 GB CuPy-pool
ceiling and in physical free device memory.

The rule is conjunctive and cannot be narrowed to a favorable board, family,
target, or action width after seeing bytes.  Headroom safety is a decision
outcome, not a mechanism gate: a coherent unsafe measurement passes this
preflight and requires a stop before strategy work.

## Frozen gates

The preflight passes only if:

1. all source hashes and strict parent semantics reproduce from a clean Git
   state on the frozen numerical and CUDA stack;
2. the full seed commit resolves exactly and deterministically derives the
   three frozen, pairwise-disjoint boards;
3. all six source and twelve target identities reproduce before sized h32
   work;
4. the h2 common-game bridge, exact evaluator, zero-sum, compact policy,
   385/763-node, 127-terminal-group, payoff-span, and 378-basis controls remain
   within their frozen bounds;
5. all twelve targets and 24 caches execute in frozen order;
6. topology remains 385/763 public nodes, 64/127 terminal groups, and 384/762
   logical automata;
7. every two-size cache stores exactly 378 canonical bases and matches the
   corresponding one-size maximum middle rank;
8. every cold construction is at most 120 seconds and every pool total is at
   most 12 GB;
9. panel h32 steps, policies, and quality evaluations are exactly zero;
10. the top-level strategy-quality claim is null; and
11. total preflight wall time is at most 1,800 seconds.

There is no gate on byte ratio, cold-speed ratio, total logical rank, headroom-
safe outcome, or any strategy direction.

## Pre-freeze controls

Six direct controls pass.  They reproduce the exact board sampler, separate
generic seed variation from the frozen config seed, prove pairwise freshness,
reject source, board, target, resource, and gate mutations, reproduce all six
source and twelve target identities, and execute the h2 canonical common-game
cache oracle.

The complete repository passed 577 tests in `115.917 s`.  No panel h32 two-
size tree, GPU cache, policy, strategy step, or quality label was constructed
during validation.

## Decision branches

- **Mechanism pass and all-24 headroom safe:** record the cache evidence, then
  separately preregister construction of immutable one-size source blueprints
  on all six board/family sources before any target quality work.
- **Mechanism pass but unsafe:** stop before panel strategy construction and
  revisit residency or the concurrency boundary under a new ADR.
- **Identity, topology, basis, or rank failure:** reject the panel preflight and
  return to the representation without interpreting cache economics.
- **Mechanism failure:** preserve the artifact and make no panel conclusion.

No branch makes a strategy-quality or action-width claim.

## Dissent

**Confidence:** extremely high in deterministic board derivation and label-
free identity; high that the canonical cache remains resident; low that three
boards are enough for population-level action-width inference.

**Opposing evidence:** deterministic disjoint sampling prevents cherry-picking
but does not guarantee representative board textures.  Panel 1 is paired,
panel 2 is relatively disconnected, and panel 3 is moderately connected; that
variety is incidental rather than stratified.

**Largest risk:** source-policy generation becomes the next hidden selection
stage.  A later ADR must freeze identical training schedules and checkpoint
choice across all six sources before looking at target or action-width labels.

**Cheapest falsification:** execute the 24-row cache preflight once.  Any row
below the established reserve halts the strategy branch without spending a
single panel h32 step.
