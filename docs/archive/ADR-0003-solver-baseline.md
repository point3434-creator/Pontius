# ADR-0003: Solver baseline order

**Status:** Accepted, 2026-08-18.

## Decision

Implement full-tree vanilla CFR first, then LCFR over the same traversal. Add
CFR+, DCFR, and external sampling only after exact evaluation verifies the
reference. LCFR is the initial Pluribus-style control, not a presumed final
winner.

## Rejected shortcut

Beginning with sampled or predictive CFR would make traversal, sampling, update
weighting, and evaluation errors difficult to distinguish.

## Revisit condition

Algorithm selection changes only after equal-time, equal-node, and equal-memory
experiments on held-out exact games.

