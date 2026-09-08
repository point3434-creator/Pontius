# ADR-0225: Preregister the continuation-root wall ledger

- Status: accepted label-free preregistration
- Date: 2026-08-22
- Follows: ADR-0224
- Experiment: `experiments/configs/h32-continuation-root-ledger-v1.json`

## Context

ADR-0224 established exact post-action continuation semantics and reduced the
maximum coherent public-node library from 192 blocks to 31. Node counts do not
price the live path. The warm step, opponent-best-response directional rows,
terminal middle ranks, resident memory, and candidate-to-candidate cost spread
must be measured on the continuation topology before any fresh continuation
strategy label is opened.

This is a wall-ledger experiment, not an opportunity experiment. It may build
one-step regret-vertex endpoints and affine response rows to expose their work,
but it may not serialize a quality vector, affine opportunity coefficient,
certificate, or strategy label. The only policy eligible for emission is the
immutable restricted blueprint.

## Frozen experiment

Run all 12 action-conditioned targets from ADR-0224. For each target:

1. reproduce the source checkpoint, exact posterior, continuation topology,
   restricted average-64 blueprint, resident belief cache, and 32 continuation
   showdown automata;
2. warm-start one device-fold resident DCFR solver from that blueprint and run
   exactly one synchronized step;
3. recover its iteration-one regret deltas and partition all 992 information
   sets into the exact 31 continuation public-node blocks;
4. consume the blocks in continuation public-tree preorder, with actor and full
   public history as deterministic tie-breakers;
5. build one regret-vertex endpoint per block and compile its probability tape;
6. evaluate the acting seat's exact zero-terminal-contraction affine row and
   exactly five charged opponent-best-response affine rows; and
7. record only endpoint digests, structural counts, contraction work, terminal
   middle rank, memory, and synchronized timing.

The complete per-candidate Tier-B time starts before endpoint construction and
ends after all six response rows have synchronized. It therefore includes
endpoint construction, tape construction, the free own-seat semantic row, the
five opponent-BR-conditioned directional contractions, and reverse work. The
acting-seat identity must use zero affected terminal contractions. All six
affine intercepts must reproduce their source deviation gains within `2e-11`,
but neither gains nor slopes are written to the result.

Require 12 warm steps, 31 blocks and 992 information sets per target, 372 own
rows, 1,860 opponent rows, exact source/target/blueprint identities, convex
single-node scope, five opponent calls per candidate, safe memory, finite
telemetry, and the frozen numerical ceilings. No exact certificate call is
permitted.

## Frozen deadline ledger

Keep the 15-second street boundary, one-second immutable-emission reserve, and
a conservative 10 ms Tier-C reserve. For each target compute two capacities
from label-independent measured costs:

- **Worst-case safe K:** the remaining candidate budget divided by that
  target's maximum complete candidate cost, capped at 31.
- **Profiled cumulative prefix K:** consume measured complete costs in the
  frozen public-tree order and stop at the first candidate whose addition
  crosses the reserve.

Worst-case K is the conservative deadline descriptor. The cumulative prefix is
a development capacity diagnostic under this run's timing; it is explicitly
not a live hard-deadline guarantee and may not be used to reorder candidates.
Both capacities are computed before any strategy label exists.

## Decision rule

If every validity gate passes and the minimum across all 12 targets is at least
six for worst-case K and at least eight for cumulative prefix K, authorize a
separate fresh continuation-root strategy preregistration. Those thresholds
show that the old six-block library fits even under the conservative rule and
that the widened continuation library offers additional measured room under
the deterministic prefix rule.

If the experiment is valid but either capacity threshold misses, retain the
immutable restricted blueprint and reprice the scheduler before opening fresh
labels. If any semantic, provenance, identity, memory, numerical, or no-label
gate fails, reject the ledger and stop.

No strategy is populated. This preregistration makes no strategy-quality,
opportunity, selector-transfer, deployment, continual-resolving, composition,
or population claim.
