# ADR-0117: Preregister device-resident h32 CFR

## Status

Frozen before any h32 resident-CFR step timing or trajectory label.

## Context

ADR-0113 localized 87.98% of its wide strategic-transfer wall time to source
training and warm target search.  ADR-0116 then showed diagnostically that all
eight corpus selections were available by search step two.  The existing CFR
solver, however, still rebuilds terminal features on the CPU and transfers the
wide batches every traverser.  ADR-0110 already proved that static belief and
showdown data can remain resident for exact evaluation.

The additive resident CFR implementation changes only that contraction
boundary.  Own-reach averaging, the public-tree reverse adjoint, alternating
regret updates, DCFR discounting, and checkpoint semantics remain the existing
code path.

Development screens are disclosed before the wide run.  On the existing h4
fixture, both incidence directions and a complete warm-started DCFR step agreed
with the transferred solver within `2e-12`.  On a disclosed h7 balanced control,
regret error was `2.22e-16` and strategy-sum error was zero, but residency lost:
`452.261 ms` transferred versus `476.080 ms` resident, or `0.950x` marginal and
`0.898x` with `27.800 ms` cache compilation charged.  Therefore this is
explicitly an h32-customer audit, not a universal replacement or a size selector.

## Decision

Freeze `h32-resident-cfr-audit-v1.json` and run the actual one/two-step warm
search customer on all four fresh-board target beliefs from ADR-0113:

- balanced and blocker-heavy source families;
- local blocker and dense all-seat strength shifts;
- the exact average-64 source blueprint and the original `0.1 * payoff span`
  warm regret mass;
- legacy transferred and resident trajectories through steps one and two;
- alternating engine order across targets to expose gross timing-order bias;
- one complete resident belief plus six-seat automaton cache charged separately
  to both the one-step and two-step bills.

The stored ADR-0113 checkpoints are the strategic teacher.  The transferred
trajectory must reproduce all eight state digests exactly.  The resident path
must agree in regrets, strategy sums, and current/average policies within frozen
Float64 tolerances.  The h7 negative control is rerun inside the audit but its
speed sign is a report, not a gate.

Economics pass only if every target clears `1.5x` marginal over two steps,
`1.2x` cache-charged at one step, and `1.5x` cache-charged at two steps.  This is
deliberately stricter than a pooled win: a workload selector is not authorized.

## Interpretation

A pass promotes resident contraction to the default wide warm-search engine and
justifies measuring longer training trajectories with the same kernel.  A clean
failure keeps the transferred CFR solver despite the resident evaluator win and
localizes the missing economics inside iterative state production.  Either
outcome is useful; no new strategy-quality claim is made.

## Scope

The audit remains one river board, one bet size, equal stacks, two generated
range families, four target beliefs, and exact unilateral DCFR updates.  It does
not establish a hand-count dispatch, neural approximation, broader NLHE
coverage, or strategy improvement beyond the already frozen ADR-0113 labels.
