# ADR-0224: Continuation rooting is exact and removes five sixths of strategic nodes

- Status: accepted label-free engineering result
- Date: 2026-08-22
- Implements: ADR-0223
- Clean preregistration commit: `6717e4e`
- Result: `experiments/results/h32-continuation-root-preflight-v1.json`
- Result SHA-256: `5f11d5bed81273eaf54a9d7ded18535df93476299841be90c8d92d9c8cc86066`

## Formal result

Every frozen semantic, provenance, source, target, blueprint, topology, policy-
restriction, fixed-policy utility, terminal-payoff, showdown-automaton,
mutation, finite, and no-label gate passes across all 12 action-conditioned
targets. The clean invocation completed in `30.005 s`.

All 12 source checkpoints, target beliefs, and average-64 blueprints reproduce
their frozen digests. Wrong actor order and a terminal all-check prefix both
fail closed. The historically hash-pinned `PublicTreeTensorEvaluator` remains
byte-identical; continuation behavior lives only in the additive subclass.

## Exact subtree identity

For every target and observed bettor, continuation rooting produces:

- 63 public nodes;
- 31 strategic nodes;
- 32 terminal nodes;
- 992 h32 information sets; and
- 32 terminal payoff groups.

Every node maps to the same-history node in the complete tree with identical
actor, actions, child histories, and information keys. Maximum terminal-payoff
error is zero. Restricting the immutable blueprint to the continuation schema
loses no information set, changes no action schema, and produces zero fixed-
policy utility error against direct complete-tree subtree evaluation.

Every continuation leaf-adjoint automaton exists in the complete-tree library.
Contenders, target seat, contribution flag, final pot, sunk value, and terminal
winner tensors agree exactly. The continuation automata use at most
`0.671582` of the complete library's numeric bytes; this is a measured storage
descriptor, not a warm-step speedup.

## Structural reduction

The complete river tree has 385 public nodes, 192 strategic nodes, and 193
terminal nodes. Post-bet continuation rooting retains only 31 strategic nodes,
an `83.8542%` reduction. Equivalently, the maximum coherent changed-node
library falls structurally from 192 to 31 before any search result is observed.

This addresses ADR-0222's causal-scope problem: every retained decision occurs
after the observed bet and remains legally available to the bot. It also gives
the compute path a plausible reduction, but node count alone does not establish
wall-clock scaling because terminal contraction ranks, group shapes, sparse
widths, and GPU occupancy can scale differently.

## Decision

Authorize preregistration of one label-free continuation-root device-fold warm
step per frozen target, followed by complete changed-block enumeration and
Tier-B cost measurement. That experiment must:

- retain all 12 targets and immutable restricted blueprints;
- generate no exact strategy certificate or quality label;
- measure warm-step wall time and resident work, changed-block count, per-block
  Tier-B cost distribution, memory, and a cumulative deadline ledger;
- preserve the 15-second budget and one-second emission reserve;
- compare against the complete-tree ADR-0222 timing only as a structural
  engineering baseline; and
- freeze any cost-aware stopping rule before a continuation strategy label is
  opened.

The fixed worst-case K from ADR-0221 may be reported for continuity, but the
preflight should also price a deterministic cumulative deadline rule because
ADR-0222 measured per-block Tier-B costs from about `119 ms` to `7.14 s`. The
rule must consume candidates in a label-independent order and stop before the
reserve; it may not use retained ADR-0222 values to reorder continuation rows.

No strategy has been populated. This result makes no warm-step speed, strategy-
quality, selector-transfer, continual-resolving, deployment, composition, or
population claim.
