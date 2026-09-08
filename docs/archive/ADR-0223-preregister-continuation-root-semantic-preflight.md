# ADR-0223: Preregister the continuation-root semantic preflight

- Status: accepted label-free preregistration
- Date: 2026-08-22
- Follows: ADR-0222
- Experiment: `experiments/configs/h32-continuation-root-preflight-v1.json`

## Context

ADR-0222 found abundant realized B-to-C value in the widened complete-tree
range-transfer corpus, but rejected its live path. The conditioned belief was
post-action while the strategy tree still began before the observed action.
That admitted decisions the bot could no longer make and left 192 candidate
nodes competing for at most two on-clock Tier-B rows.

The existing immutable river state already records full public history,
bettor, callers, folds, pending responders, and terminal contributions. The
smallest semantic change is therefore to replay the observed public prefix on
that state and compile the existing tensor evaluator from the resulting node.
No second game or payoff convention is needed.

## Additive implementation

The additive `ContinuationPublicTreeTensorEvaluator` subclasses the immutable,
historically hash-pinned `PublicTreeTensorEvaluator`, compiles its exact full
layout, and retains only the subtree beneath an actor-labelled public prefix.
The original evaluator remains byte-identical for every existing caller. The
prefix is replayed through `MultiwayRiverState.apply_action`; wrong actor order,
illegal actions, and terminal prefixes fail closed. The continuation retains:

- the original game structural digest;
- the complete original public history in every information key;
- the original pot, stacks, bet size, bettor contribution, callers, folds,
  response order, and terminal utility convention; and
- the same private-deal and h32 hand axes.

The change compiles a subtree; it does not rewrite payoffs by subtracting sunk
costs or renumber seats. That is essential because exact equality with the
full-tree conditional node is the teacher.

## Frozen preflight

Run all 12 ADR-0220 targets without a warm step, quality evaluation, affine
feature, certificate, or strategy label. For each target:

1. reproduce the source belief, average-64 blueprint, and exact target belief;
2. replay every observed check and the final bet;
3. compile only the descendants of that post-bet state;
4. compare every continuation node to the same-history node in the complete
   tree;
5. restrict the immutable blueprint to the continuation information schema;
6. compare fixed-policy root utility with direct evaluation of the complete-
   tree subtree; and
7. rebuild all leaf-adjoint showdown automata and compare each retained group
   with its complete-tree teacher.

The exact six-player one-bet continuation is frozen at 63 public nodes, 31
strategic nodes, 32 terminal nodes, 992 h32 information sets, and 32 terminal
payoff groups. The complete tree has 385 public nodes, 192 strategic nodes,
and 193 terminals. Continuation rooting therefore removes `83.85%` of
strategic nodes before any performance claim.

Require exact topology, information-key, terminal-payoff, terminal-group, and
automaton identity. Permit at most `1e-12` fixed-policy utility error. Include
required negative controls for wrong actor order and an all-check prefix that
ends terminal. All 12 source, target, and blueprint digests must reproduce.

## Decision rule

If every gate passes, authorize a separate prospective continuation-root warm-
step and wall-ledger preregistration. Do not infer speedup from node counts and
do not reuse any ADR-0222 strategy label. The next experiment must remeasure
warm cost, changed-block count, Tier-B cost distribution, safe deadline
capacity, and immutable fallback on the continuation topology before opening
new continuation strategy labels.

If any semantic gate fails, stop. Do not schedule a continuation warm step or
repair the discrepancy inside the same evidence artifact.

No strategy is populated. This preflight makes no strategy-quality, speed,
selector-transfer, continual-resolving, deployment, composition, or population
claim.
