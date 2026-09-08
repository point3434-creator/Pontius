# ADR-0167: Retrospective single-atom value-capture contract

- Status: accepted retrospective analysis contract; not preregistered
- Date: 2026-08-21
- Sources: ADR-0107, ADR-0159/0160, ADR-0165/0166

## Methodological status

This analysis is deliberately not called a preregistration. The retained atomic NashConv labels were inspected before this contract was written. Its results may describe the frozen four-target corpus and motivate a future prospective experiment, but they cannot support an out-of-sample, causal, or general strategy-quality claim.

No new solver or quality evaluator is called. Every number is replayed from existing immutable artifacts.

## Accounting question

For each canonical h32 target, compare:

1. the retained `search_current1` bundle's envelope status and, only where
   complete, its exact quality label;
2. its six individually evaluated one-infoset atoms;
3. the best envelope-complete retained single atom, used as a bounded lower oracle; and
4. the best admissible atom available inside ADR-0166's fixed two-certificate prefix, acting seats `(0,1)`.

Define positive certified value as `max(0, blueprint NashConv - candidate NashConv)`. A cap- or objective-stopped atom receives zero certified value even if its full teacher has lower NashConv, because it is outside the fixed safety envelope.

The bounded oracle is only the best retained single atom. It is a lower bound on any richer attainable value and says nothing about ungenerated directions. Ties break by acting seat.

## Interaction diagnostics

Report the sum of admissible single-atom values. Where the bundle is envelope-complete and has an exact quality label, also report its fraction of full-bundle value, the best-single fraction of bundle value, and the scalar six-way union interaction residual:

`(bundle NashConv - blueprint NashConv) - Σ(atom NashConv - blueprint NashConv)`.

These are descriptive nonadditivity diagnostics. Single-atom safety and value cannot be composed. No incomplete bundle's partial NashConv is treated as a quality label, and no new union is inferred or certified.

Also report whether an envelope-complete bundle contains an individually cap-bound constituent. That signature means atomic admissibility is not monotone under union and blocks any greedy safety composition rule.

## Integrity gates

Require all source gates, four target rows, 24 atomic rows, four bundle rows, exact blueprint/bundle policy identity, finite accounting, and zero new strategy-quality labels. No value fraction, ranking, binding-constraint count, or interaction sign is a gate.

## Scope

This retrospective result cannot change the scheduler, reorder atoms, select a policy, authorize packing, or claim expected value capture. A prospective ordering or packing rule requires fresh labels or a genuinely untouched holdout and exact union recertification.
