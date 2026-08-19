# Development Runbook

## Runtime

The reference laboratory uses Python 3.11+ and the standard library only. In
the Codex desktop environment, the bundled interpreter is currently:

```text
C:\Users\point\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

## Tests

From the repository root:

```powershell
$python = "C:\Users\point\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = "src"
& $python -m unittest discover -s tests -v
```

## Reference experiment

```powershell
$python = "C:\Users\point\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = "src"
& $python -m pontius.experiment --game kuhn2 --solver lcfr --iterations 20000 --report-every 2000 --output experiments/results/lcfr-kuhn2.json
```

The output contains the complete configuration, platform metadata, elapsed
times, expected utilities, best-response values, NashConv, exploitability, and
the convergence trace.

## Paired leaf-error matrix

```powershell
$python = "C:\Users\point\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = "src"
& $python -m pontius.leaf_matrix --config experiments/configs/leaf-kuhn2-initial-matrix.json --output experiments/results/leaf-kuhn2-initial-matrix.json
```

The compact matrix artifact contains every run's causal metrics and summaries
over configured replicate axes. Leaves are precomputed, so reported search
times are warm-leaf-cache traversal times. Raw JSON under `experiments/results`
is intentionally ignored until promoted as a checkpoint artifact.

Anchored-search reproduction configs are:

- `experiments/configs/leaf-kuhn2-depth2-output-matrix.json`
- `experiments/configs/leaf-kuhn2-depth2-anchor-matrix.json`
- `experiments/configs/leaf-kuhn2-depth2-fine-anchor-matrix.json`
- `experiments/configs/leaf-kuhn2-depth2-anchored-solvers-matrix.json`

Structured-error reproduction configs are:

- `experiments/configs/leaf-kuhn2-depth2-structured-noise-matrix.json`
- `experiments/configs/leaf-kuhn2-depth2-structured-bias-matrix.json`
- `experiments/configs/leaf-kuhn2-depth2-correlation-focus-matrix.json`
- `experiments/configs/leaf-kuhn2-depth2-correlation-calibrated-matrix.json`
- `experiments/configs/leaf-kuhn2-depth2-calibrated-structure-matrix.json`

`leaf_error_target_on_policy_root_l2` rescales each deterministic random draw
to a matched realized root contribution and records the effective raw scale.
It is an experimental control for comparing error structure, not an online
post-hoc correction. It cannot be combined with explicit bias.

## Frozen selection holdout

Run a preregistered rule directly from a matrix configuration with:

```powershell
$python = "C:\Users\point\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = "src"
& $python -m pontius.selection --rule experiments/rules/counterfactual-risk-v1.json --matrix-config experiments/configs/selection-v1-kuhn2-holdout-matrix.json --output experiments/results/selection-v1-kuhn2-holdout.json
```

The evaluator validates the candidate configuration in every run and embeds a
SHA-256 digest of the complete frozen rule document. It compares the gate with
permanent no-op, unconditional search, and the unavailable full-game oracle,
and reports game/blueprint/depth subgroups. Commit a frozen rule before running
its holdout; never edit a versioned rule after observing outcomes.

The matrix runner trains and exactly evaluates each distinct blueprint once,
then reuses it across perturbation and solver axes. `prepared_blueprints` in the
artifact records the number of cached blueprints.

## Resolver-benefit trajectories

Generate exact-leaf benefit matrices, then analyze deterministic probe prefixes
without fitting a selector:

```powershell
$python = "C:\Users\point\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = "src"
& $python -m pontius.benefit_matrix --config experiments/configs/benefit-kuhn2-regimes-matrix.json --output experiments/results/benefit-kuhn2-regimes-matrix.json
& $python -m pontius.benefit_matrix --config experiments/configs/benefit-kuhn3-trajectory-matrix.json --output experiments/results/benefit-kuhn3-trajectory-matrix.json
& $python -m pontius.benefit_trajectory --matrix kuhn2 experiments/results/benefit-kuhn2-regimes-matrix.json --matrix kuhn3 experiments/results/benefit-kuhn3-trajectory-matrix.json --output experiments/results/benefit-probe-trajectories.json
```

The trajectory analyzer requires checkpoints 1, 3, 5, 10, and 25 for every
otherwise identical configuration. Probe features see only the depth-limited
model. The full-game exact outcome is a hidden diagnostic target and never
enters a feature. Current matrices recompute each deterministic prefix for
measurement simplicity; a runtime implementation must snapshot one progressive
solve instead.

## Policy-composition controls

Compare prefix deployment, Bayesian continual composition, exact local gating,
and a coherent global control with:

```powershell
$python = "C:\Users\point\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = "src"
& $python -m pontius.composition_matrix --config experiments/configs/composition-kuhn2-matrix.json --output experiments/results/composition-kuhn2-matrix.json
& $python -m pontius.composition_matrix --config experiments/configs/composition-kuhn3-focus-matrix.json --output experiments/results/composition-kuhn3-focus-matrix.json
& $python -m pontius.composition_matrix --config experiments/configs/composition-kuhn2-full-depth-audit.json --output experiments/results/composition-kuhn2-full-depth-audit.json
```

The continual policy is built root-forward. Each posterior sees the already
composed ancestor policy, and tests verify that recorded reach, entropy, and
effective state count match the final composed prefix. Its decision cost is
expected search time per hand. The local-gated arm additionally includes the
exact local evaluations required by its veto; optional diagnostic evaluation
is reported separately and excluded from decision latency.

## Safe-resolving control

Run the exact two-player opponent-frontier convergence matrix with:

```powershell
$python = "C:\Users\point\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = "src"
& $python -m pontius.safe_composition_matrix --config experiments/configs/safe-composition-kuhn2-convergence-matrix.json --output experiments/results/safe-composition-kuhn2-convergence-matrix.json
```

The raw arm deploys every finite-CFR candidate and reports its additive
residual-adjusted exploitability bound. The strict arm pays for an exact
opponent-CBR certificate and keeps the current policy unless total positive
frontier violation is within the configured tolerance. Certificate evaluation
is included in decision compute. Full-game exploitability is evaluated only
after construction and is never used by either arm.

## Exact safe-strategy objectives

Compare max-min frontier margin, target-free constrained sum-margin, and the
hidden full-game best-response greedy control with:

```powershell
$python = "C:\Users\point\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = "src"
& $python -m pontius.safe_oracle_matrix --config experiments/configs/safe-oracle-kuhn2-objectives-matrix.json --output experiments/results/safe-oracle-kuhn2-objectives-matrix.json
```

All three arms enumerate exact normal-form plans and independently verify the
converted behavioral strategy. Sum-margin never sees a full-game target. The
hidden arm does and is diagnostic only; its root-forward result is a greedy
control, not a deployable resolver or a global continual optimum. Raw JSON is
ignored until promoted as a checkpoint artifact.

## CFR-to-oracle solver gaps

Run the held-in solver/prior/checkpoint screen with:

```powershell
$python = "C:\Users\point\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = "src"
& $python -m pontius.safe_solver_gap_matrix --config experiments/configs/safe-solver-gap-kuhn2-screen-matrix.json --output experiments/results/safe-solver-gap-kuhn2-screen-matrix.json
```

The progressive incumbent begins at the blueprint and retains only an exactly
frontier-safe snapshot with a larger target-free sum margin. Candidate timing
includes frontier construction, cumulative solver work, and the certificate
used for selection. Complete-game best responses are hidden diagnostics and
excluded from candidate timing.

`experiments/rules/safe-solver-incumbent-v1.json` freezes the screen winner.
After that rule is committed, its untouched holdout is run with:

```powershell
& $python -m pontius.safe_solver_gap_matrix --config experiments/configs/safe-solver-gap-kuhn2-v1-holdout-matrix.json --output experiments/results/safe-solver-gap-kuhn2-v1-holdout-matrix.json
```

## Direct constrained generation

Run the dynamic row/column-generation screen with:

```powershell
$python = "C:\Users\point\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$env:PYTHONPATH = "src"
& $python -m pontius.constrained_generation_matrix --config experiments/configs/constrained-generation-kuhn2-screen-matrix.json --output experiments/results/constrained-generation-kuhn2-screen-matrix.json
```

`experiments/rules/constrained-generation-v1.json` freezes the five-update
screen winner and its fresh CFR/DCFR holdout. Only after that rule is committed,
run both paired holdout arms:

```powershell
& $python -m pontius.constrained_generation_matrix --config experiments/configs/constrained-generation-kuhn2-v1-holdout-matrix.json --output experiments/results/constrained-generation-kuhn2-v1-holdout-matrix.json
& $python -m pontius.safe_solver_gap_matrix --config experiments/configs/safe-solver-gap-kuhn2-constrained-v1-holdout-matrix.json --output experiments/results/safe-solver-gap-kuhn2-constrained-v1-holdout-matrix.json
```

Decision timing excludes the exact normal-form regret teacher and hidden
complete-game diagnostic. It includes frontier setup, master construction and
solve, behavioral conversion, response separation, and dynamic resolver
pricing.

Phase-v2 development and its frozen fresh holdout use:

```powershell
& $python -m pontius.constrained_generation_matrix --config experiments/configs/constrained-generation-kuhn2-phase-v2-screen-development.json --output experiments/results/constrained-generation-kuhn2-phase-v2-screen-development.json
& $python -m pontius.constrained_generation_matrix --config experiments/configs/constrained-generation-kuhn2-phase-v2-revealed-development.json --output experiments/results/constrained-generation-kuhn2-phase-v2-revealed-development.json
& $python -m pontius.constrained_generation_matrix --config experiments/configs/constrained-generation-kuhn2-phase-v2-holdout.json --output experiments/results/constrained-generation-kuhn2-phase-v2-holdout.json
& $python -m pontius.safe_solver_gap_matrix --config experiments/configs/safe-solver-gap-kuhn2-phase-v2-holdout.json --output experiments/results/safe-solver-gap-kuhn2-phase-v2-holdout.json
```

The frozen v2 checkpoint uses `cumulative_candidate_compute_seconds`: it stops
after safety separation and before current pricing. The matrix also reports an
explicitly optimistic deadline upper bound using realized phase times; do not
describe that oracle phase-fit diagnostic as a deployable scheduler.

Build the revealed-development causal opportunity dataset and allocation
controls with:

```powershell
& $python -m pontius.opportunity_trace --config experiments/configs/opportunity-trace-v1-development.json --output experiments/results/opportunity-trace-v1-development.json
```

Regenerate both phase-v2 development matrices first whenever trace fields or
timing instrumentation change. `candidate_ready` features intentionally omit
the current pricing score, reduced cost, generated column, and pricing time.
Exact sum-margin and all future outcomes are labels only. Treat
`blueprint_regime_allocation` as the primary speculation ceiling; the looser
cross-regime pool can move compute between different blueprint agents and is
not a deployment interpretation. This analyzer fits no scheduler.

## Exact range-sensitive river traces

Run the small all-split developmental pilot with:

```powershell
& $python -m pontius.river_opportunity --config experiments/configs/river-opportunity-pilot-v1.json --output experiments/results/river-opportunity-pilot-v1.json
```

After committing any generator or feature-contract change, produce the larger
development-only dataset with:

```powershell
& $python -m pontius.river_opportunity --config experiments/configs/river-opportunity-development-v1.json --output experiments/results/river-opportunity-development-v1.json
& $python -m pontius.river_trace_analysis --input experiments/results/river-opportunity-development-v1.json --output experiments/results/river-opportunity-development-v1-analysis.json
```

The development configuration requests 400 deterministic board groups; its
frozen split hash materializes 256 development groups and 1,024 four-family
contexts. Validation and test families are not constructed, solved, or written.
The normal-form LP and exact best responses are diagnostic teachers and are
excluded from solver timing. `online_features` must contain no exploitability,
oracle, future, or gain field. `allocation_oracles` use solver iterations as a
deterministic work unit and perfect future labels; they are optimistic shared
or speculative compute ceilings, not deployable schedulers.

The compact analyzer reports group-preserving Spearman folds,
first-improvement counts, checkpoint regressions, and teacher exactness without
fitting a model. Its primary feature is variant-discounted accumulated positive
regret, not a fresh exact counterfactual-regret calculation. In this one-bet
game a fresh one-step positive-regret profile equals NashConv exactly; this is a
known shallow-tree confound and must not be presented as transfer evidence.

Run the fixed-raise sequential pilot and development-only replication with:

```powershell
& $python -m pontius.river_opportunity --config experiments/configs/river-opportunity-sequential-pilot-v1.json --output experiments/results/river-opportunity-sequential-pilot-v1.json
& $python -m pontius.river_opportunity --config experiments/configs/river-opportunity-sequential-development-v1.json --output experiments/results/river-opportunity-sequential-development-v1.json
& $python -m pontius.river_trace_analysis --input experiments/results/river-opportunity-sequential-development-v1.json --output experiments/results/river-opportunity-sequential-development-v1-state-efficiency-analysis.json --primary-target state_visit_efficiency --allocation-probe-checkpoint 2
& $python -m pontius.river_trace_analysis --input experiments/results/river-opportunity-sequential-development-v1.json --output experiments/results/river-opportunity-sequential-development-v1-millisecond-efficiency-analysis.json --primary-target millisecond_efficiency
& $python -m pontius.river_trace_comparison --baseline experiments/results/river-opportunity-development-v1.json --target experiments/results/river-opportunity-sequential-development-v1.json --output experiments/results/river-opportunity-sequential-development-v1-paired-comparison.json
```

`state_visit_efficiency` is payoff-normalized best future reduction per thousand
deterministic full-tree state visits. Use it for stable development ranking and
require `millisecond_efficiency` as the serial runtime replicate. Total future
reduction measures headroom, not quality per millisecond, and must not be the
primary scheduler target.

`--allocation-probe-checkpoint 2` forces every selected context to pay for the
checkpoint-two feature before the perfect-information allocator can redistribute
remaining iterations. Report this post-probe ceiling for any rule using those
features. The unconditioned budget-two allocator gets the feature for free and
is not a causal deployable comparison.

The sequential production configuration is development-only and creates the
same 256 boards and 1,024 complete joint ranges as the one-bet production trace.
The paired comparator verifies those fields exactly before reporting cross-tree
rank stability. Do not substitute merely similar ranges or compare unmatched
context IDs.

The preregistered shadow and scheduler screen is reproduced with:

```powershell
& $python -m pontius.river_shadow_probe --source experiments/results/river-opportunity-sequential-development-v1.json --output experiments/results/river-opportunity-sequential-development-v1-shadow-probe.json
& $python -m pontius.river_scheduler_screen --source experiments/results/river-opportunity-sequential-development-v1.json --shadow experiments/results/river-opportunity-sequential-development-v1-shadow-probe.json --rule experiments/rules/river-post-probe-scheduler-screen-v1.json --output experiments/results/river-opportunity-sequential-development-v1-scheduler-screen.json
```

The shadow must reproduce every context and active DCFR feature and report zero
extra tree traversals. It is not a standalone CFR+ solve. The scheduler screen
must use the committed rule family; do not add a feature, weight, or macro after
reading its result. Raw JSON is ignored, so record its digest in the frozen
selected rule and decision record.

`experiments/rules/river-post-probe-scheduler-v1.json` is the selected rule.
It disables shadow regret and freezes `active_raw::shallow_12_5`. Do not
construct validation until the fixed-rule evaluator is committed. Generate
validation before test, apply the rule once without selection, and stop without
test or retuning if any ADR-0024 validation gate fails.

After committing `river_scheduler_holdout`, ADR-0025, and both reserved configs,
generate and evaluate validation only:

```powershell
& $python -m pontius.river_opportunity --config experiments/configs/river-opportunity-sequential-validation-v1.json --output experiments/results/river-opportunity-sequential-validation-v1.json
& $python -m pontius.river_scheduler_holdout --source experiments/results/river-opportunity-sequential-validation-v1.json --rule experiments/rules/river-post-probe-scheduler-v1.json --split validation --output experiments/results/river-opportunity-sequential-validation-v1-scheduler-holdout.json
```

The holdout evaluator enforces the frozen rule SHA and performs no candidate
selection. Only when the validation artifact says
`validation_passed_test_authorized` may test be generated and evaluated:

```powershell
& $python -m pontius.river_opportunity --config experiments/configs/river-opportunity-sequential-test-v1.json --output experiments/results/river-opportunity-sequential-test-v1.json
& $python -m pontius.river_scheduler_holdout --source experiments/results/river-opportunity-sequential-test-v1.json --rule experiments/rules/river-post-probe-scheduler-v1.json --split test --validation-result experiments/results/river-opportunity-sequential-validation-v1-scheduler-holdout.json --output experiments/results/river-opportunity-sequential-test-v1-scheduler-holdout.json
```

Only an identical `provenance_digest` authorizes an exact strategy-cache hit.
`structural_digest` authorizes topology and board-work reuse, not strategy
deployment. Total-variation bounds in this laboratory cover one fixed policy's
value and must not be described as equilibrium reuse certificates.

## Continuation protocol

1. Read `PROJECT.md`, `STATUS.md`, and the relevant decision records.
2. Confirm the active checkpoint and working-tree status.
3. Run the fast test suite before modifying correctness-critical code.
4. Make one measurable change.
5. Verify against the reference and record the experiment configuration.
6. Update `STATUS.md` and any decision whose evidence changed.
