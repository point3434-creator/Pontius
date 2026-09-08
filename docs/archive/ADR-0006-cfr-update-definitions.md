# ADR-0006: CFR update definitions

**Status:** Accepted, 2026-08-18.

## Decision

All variants share one alternating full-tree traversal and aggregate an
information set's instantaneous regret before applying its update rule.

- `cfr`: unweighted cumulative regret and average strategy.
- `lcfr`: DCFR(1, 1, 1), equivalent to linearly weighting iteration `t` by `t`.
- `cfr_plus`: RM+ regret flooring with quadratic average-strategy weighting.
- `dcfr`: DCFR(1.5, 0, 2), the default recommended parameters in Brown and
  Sandholm (2019).

CFR+'s quadratic averaging is the stronger benchmark used in the DCFR paper,
rather than the original linear-average definition. Experiment reports must
state this convention.

## Evidence

The definitions and discount factors follow Brown and Sandholm, *Solving
Imperfect-Information Games via Discounted Regret Minimization* (2019):
<https://arxiv.org/abs/1809.04040>. CFR+ originates in Tammelin (2014):
<https://arxiv.org/abs/1407.5042>. Regret deltas are buffered because applying
RM+ clipping separately to individual histories inside one information set
would implement a different algorithm.

## Revisit condition

Expose delay or averaging exponents as configuration only after the fixed
definitions pass exact regression tests and the initial comparison matrix.
