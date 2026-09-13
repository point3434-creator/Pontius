# River research: results and evidence

Updated 2026-09-13. The [project-wide consolidation](../../experiments/RESULTS.md)
is the main research reference. Its [solver family summary](../../experiments/solver-foundations.md#river-representation-and-solver-findings-through-2026-09-12)
explains the full chain, including non-improvements, transfer limits, and stopping points.
The [research roadmap](../../experiments/research-roadmap.md) holds the proposed next steps.

Current priority: [build the playable bot](../plans/pontius-playable-build-2026-09-13.md)
using the existing research, with a configurable 33-second complete-decision ceiling.
Further research campaigns and neural-network work are paused behind that objective.

The latest completed milestone is **river-time-quality-001**. The [result](river-time-quality-001.md)
records six trajectories, 24 audits, every budget miss, and the quality gained
from additional iterations. The [earlier build snapshot](river-time-quality-001-design.md)
remains available; the full campaign is now complete.

The preceding milestone is **river-gpu-graph-001**. The [graph replay result](river-gpu-graph-001.md)
retains all 36 solves, six independent audits, exact policy-byte parity,
capture/reset checks and full preparation/reuse accounting. No strategy adoption.

The preceding milestone is **river-gpu-execution-001**. The [GPU result](river-gpu-execution-001.md)
retains 12 timing runs, four exact audits, and the original numerical
parity refusal with its diagnosis. The exploratory continuation found
modest speed gains at unchanged quality and greater host memory cost.

The preceding milestone is **river-cfr-expanded-001**. The [expanded-tree result](river-cfr-expanded-001.md)
demonstrates approximate-solution capacity on both formerly memory-limited
trees: 24 training runs and eight rational audits completed. See the report
for all errors, timing, memory and strict-convergence outcomes. The queued
GPU execution assessment has since completed above; neural training remains deferred.

The preceding milestone is **river-cfr-comparison-002**. The [different-position confirmation](river-cfr-comparison-002.md)
again favors DCFR+: paper DCFR+ had 6.56x less error than matched CFR+,
and released-code DCFR+ remained best. Matched prediction improved error
about 11% here, unlike its loss on the first case. All 18 runs and six
rational audits passed, but no arm reached the strict LP gap threshold.
Next: test iterative solving on the expanded memory-limited trees.

The preceding milestone is **river-cfr-comparison-001**. The [six-arm comparison](river-cfr-comparison-001.md)
ran 18 fresh workers on one full-range baseline river. DCFR+ led at 2,048
iterations; matched prediction increased error. All six final errors were
independently verified, but none met the strict LP convergence threshold.
Next: confirm another case, then test the expanded memory-limited trees.

The preceding milestone is **river-lp-presolve-001**. The [presolve comparison](river-lp-presolve-001.md)
did not recover either expanded game: both settings hit memory stops. The initial iterative comparison above follows that result.

The preceding milestone is **river-lp-memory-001**. The [memory diagnostic](river-lp-memory-001.md)
locates both deep-stack stops inside the native HiGHS run, after assembly and model
loading. The subsequent presolve comparison above tests that hypothesis.

The preceding milestone is **river-tree-expansion-001**: seven of nine distinct full-range
trees have verified solutions; both expanded deep-stack cells hit the memory stop.
See the [tree-expansion result](river-tree-expansion-001.md).

The preceding milestone is **lp-numerical-scaling-001**. Its fixed LP unit change closed
both earlier numerical misses: four of four original-matrix certificates pass.
See the [numerical diagnostic](river-lp-numerical-scaling-001.md).

The preceding milestone is **full-combo-direct-002**, comparing all 1,081 private holdings
per role with the K=16 learner on four actual-pot restricted river games. Direct solving
had lower measured error and shorter measured solve time in all four; only two passed
the strict exact gap threshold. Full private-hand detail does not mean a full betting tree.
See the [report](river-full-combo-direct-002.md) and
[assessment with four per-hand tables](../../experiments/river-abstraction-study/full-combo-direct-002/assessment.md).

## All 45 retained milestones

This is an evidence index, not a claim of 45 independent replications.
Reports distinguish fresh-board confirmations from diagnostics on previously seen data.

| Milestone | Report | Frozen evidence |
|---|---|---|
| blueprint-range-transfer-001 | [Result](river-blueprint-range-transfer-001.md) | [Milestone](../../experiments/river-abstraction-study/blueprint-range-transfer-001/) |
| development-001 | [Result](river-abstraction-study-development-001.md) | [Milestone](../../experiments/river-abstraction-study/development-001/) |
| full-combo-direct-002 | [Result](river-full-combo-direct-002.md) | [Milestone](../../experiments/river-abstraction-study/full-combo-direct-002/) |
| group-optimality-001 | [Result](river-group-optimality-001.md) | [Milestone](../../experiments/river-abstraction-study/group-optimality-001/) |
| holdout-001 | [Result](river-abstraction-holdout-001.md) | [Milestone](../../experiments/river-abstraction-study/holdout-001/) |
| lp-numerical-scaling-001 | [Result](river-lp-numerical-scaling-001.md) | [Milestone](../../experiments/river-abstraction-study/lp-numerical-scaling-001/) |
| multibet-group-diagnostic-001 | [Result](river-multibet-group-diagnostic-001.md) | [Milestone](../../experiments/river-abstraction-study/multibet-group-diagnostic-001/) |
| multibet-size-confirmation-001 | [Result](river-multibet-size-confirmation-001.md) | [Milestone](../../experiments/river-abstraction-study/multibet-size-confirmation-001/) |
| multibet-size-repair-001 | [Result](river-multibet-size-repair-001.md) | [Milestone](../../experiments/river-abstraction-study/multibet-size-repair-001/) |
| regret-variants-001 | [Result](river-regret-variants-001.md) | [Milestone](../../experiments/river-abstraction-study/regret-variants-001/) |
| river-lp-memory-001 | [Result](river-lp-memory-001.md) | [Milestone](../../experiments/river-abstraction-study/river-lp-memory-001/) |
| river-lp-presolve-001 | [Result](river-lp-presolve-001.md) | [Milestone](../../experiments/river-abstraction-study/river-lp-presolve-001/) |
| river-stack-transfer-001 | [Result](river-stack-transfer-001.md) | [Milestone](../../experiments/river-abstraction-study/river-stack-transfer-001/) |
| river-tree-expansion-001 | [Result](river-tree-expansion-001.md) | [Milestone](../../experiments/river-abstraction-study/river-tree-expansion-001/) |
| witness-bet-conditioned-001 | [Result](river-witness-bet-conditioned-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-bet-conditioned-001/) |
| witness-bet-transfer-001 | [Result](river-witness-bet-transfer-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-bet-transfer-001/) |
| witness-boundary-001 | [Result](river-witness-boundary-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-boundary-001/) |
| witness-clipped-target-001 | [Result](river-witness-clipped-target-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-clipped-target-001/) |
| witness-compute-matched-continuation-001 | [Result](river-witness-compute-matched-continuation-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-compute-matched-continuation-001/) |
| witness-distillation-001 | [Result](river-witness-distillation-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-distillation-001/) |
| witness-fit-diagnostic-001 | [Result](river-witness-fit-diagnostic-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-fit-diagnostic-001/) |
| witness-group-repair-001 | [Result](river-witness-group-repair-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-group-repair-001/) |
| witness-group-repair-confirmation-001 | [Result](river-witness-group-repair-confirmation-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-group-repair-confirmation-001/) |
| witness-groups-development-001 | [Result](river-witness-groups-development-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-groups-development-001/) |
| witness-guarded-repair-confirmation-001 | [Result](river-witness-guarded-repair-confirmation-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-guarded-repair-confirmation-001/) |
| witness-hybrid-001 | [Result](river-witness-hybrid-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-hybrid-001/) |
| witness-next-board-001 | [Result](river-witness-next-board-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-next-board-001/) |
| witness-next-board-002 | [Result](river-witness-next-board-002.md) | [Milestone](../../experiments/river-abstraction-study/witness-next-board-002/) |
| witness-order-diagnostic-001 | [Result](river-witness-order-diagnostic-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-order-diagnostic-001/) |
| witness-ordinal-001 | [Result](river-witness-ordinal-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-ordinal-001/) |
| witness-pilot-001 | [Result](river-witness-pilot-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-pilot-001/) |
| witness-pot-diagnostic-001 | [Result](river-witness-pot-diagnostic-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-pot-diagnostic-001/) |
| witness-preference-001 | [Result](river-witness-preference-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-preference-001/) |
| witness-preference-confirmation-001 | [Result](river-witness-preference-confirmation-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-preference-confirmation-001/) |
| witness-repair-regression-diagnostic-001 | [Result](river-witness-repair-regression-diagnostic-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-repair-regression-diagnostic-001/) |
| witness-seat-crossover-001 | [Result](river-witness-seat-crossover-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-seat-crossover-001/) |
| witness-second-guarded-repair-001 | [Result](river-witness-second-guarded-repair-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-second-guarded-repair-001/) |
| witness-soft-assignment-001 | [Result](river-witness-soft-assignment-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-soft-assignment-001/) |
| witness-solver-budget-001 | [Result](river-witness-solver-budget-001.md) | [Milestone](../../experiments/river-abstraction-study/witness-solver-budget-001/) |
| river-cfr-comparison-001 | [Result](river-cfr-comparison-001.md) | [Milestone](../../experiments/river-abstraction-study/river-cfr-comparison-001/) |
| river-cfr-comparison-002 | [Result](river-cfr-comparison-002.md) | [Milestone](../../experiments/river-abstraction-study/river-cfr-comparison-002/) |
| river-cfr-expanded-001 | [Result](river-cfr-expanded-001.md) | [Milestone](../../experiments/river-abstraction-study/river-cfr-expanded-001/) |
| river-gpu-execution-001 | [Result](river-gpu-execution-001.md) | [Milestone](../../experiments/river-abstraction-study/river-gpu-execution-001/) |
| river-gpu-graph-001 | [Result](river-gpu-graph-001.md) | [Milestone](../../experiments/river-abstraction-study/river-gpu-graph-001/) |
| river-time-quality-001 | [Result](river-time-quality-001.md) | [Milestone](../../experiments/river-abstraction-study/river-time-quality-001/) |

## Designs and frozen controls

- [Original study](river-abstraction-study.md) and [holdout](river-abstraction-holdout.md).
- [Grouping-floor diagnostic](river-group-optimality.md).
- [Witness grouping](river-witness-groups.md), [fresh-board pilot](river-witness-pilot.md),
  and [distillation](river-witness-distillation.md).
- [Frozen size-aware repair baseline](river-multibet-size-repair-baseline.md).

Use Python 3.14.6; optional numerical suites use NumPy 2.5.2 and SciPy 1.18.0.
Historical pending-review, uninvoked, or unpublished statements describe the time each
record was written. Frozen reports, failed attempts, manifests, and review evidence are
preserved unchanged. Retained scripts and old authorizations do not authorize another run.
This consolidation makes no new adoption, live-latency, or six-max playing-strength claim.
