# Development Runbook

## Runtime

The original CPU reference laboratory uses Python 3.11+ and the standard
library. The wide h32 GPU path additionally uses pinned SciPy, CuPy, and CUDA
runtime directories. The accepted ADR-0186 evidence used the repository-local
environment:

```text
.venv\Scripts\python.exe
.venv\Lib\site-packages
.venv\Lib\site-packages\nvidia\cu13\bin\x86_64
```

The local environment is workspace-specific. If it disappears, restore the
pinned package/runtime versions and rerun the complete numerical regression
suite before producing evidence. Do not silently fall back to a different
backend.

## Current GPU verification environment

From the repository root, use the pinned interpreter. On Windows, importing
`pontius` now discovers a complete CUDA 13 DLL bundle under the active
repository `.venv`, sets the process-local DLL environment, and prepends that
directory to the child-process `PATH`. No per-shell CUDA initialization is
required:

```powershell
$python = (Resolve-Path ".\.venv\Scripts\python.exe").Path
$env:PYTHONPATH = "src"
& $python -m unittest discover -s tests -v
```

An explicitly supplied `PONTIUS_CUDA_DLL_DIRECTORY` still takes precedence for
controlled reproduction on a nonstandard environment. Automatic discovery is
deliberately limited to the active or repository-local Python environment and
requires the complete loader DLL set; Pontius never silently selects an
arbitrary system CUDA installation. Frozen experiment runtime/version gates
remain authoritative after discovery.

GPU or parallel Float64 recomputation uses the frozen numerical-identity
protocol in [ADR-0179](docs/decisions/ADR-0179-numerical-identity-is-the-default-gpu-evidence-gate.md).
Digests remain provenance diagnostics unless the gate is explicitly about
immutable bytes, immediate re-export, or bitwise determinism.

## Documentation freshness

`STATUS.md` is generated from ADR metadata and must not be edited manually:

```powershell
$env:PYTHONPATH = "src"
& $python -m pontius.status_generation --check
```

After adding or changing an accepted ADR, regenerate with the same command
without `--check`. Every new latest ADR must carry the complete front-door
snapshot: research, process, runtime-contract, cumulative revocations, active
next, and blockers. Omission is a hard generation failure. Documentation
integrity tests verify the generated artifact and maintained local links.

## Legal decision spine verification

The reference full-hand foundation is `pontius.no_limit_betting`, wrapped for
one controlled seat by `pontius.legal_decision_spine`. It uses integer chips and
raise-to totals. Do not feed the simplified `river_multiway` or
`river_multiway_multi_size` action semantics into this boundary; those modules
remain intentionally restricted sealed workloads.

Create a live hand with `LegalDecisionSpine.new_hand` or `six_max_100bb`; those
factories charge initial betting-state construction and validation to preflop.
The direct constructor is for a replay state paired with its already-owned
ledger, not a way to move live initialization off-clock.

Run the focused rules, one-seat, timing, card, blueprint, replay, randomized,
and exhaustive checks with:

```powershell
$env:PYTHONPATH = "src"
& $python -B -m unittest tests.test_no_limit_betting tests.test_no_limit_betting_exhaustive tests.test_legal_decision_spine tests.test_street_deadline tests.test_holdem_cards tests.test_immutable_blueprint tests.test_reference_hand_replay -v
```

For every controlled decision, open the ticket once, place all resolver work
inside `charge_compute()`, and call `emit_controlled_action` with both the
candidate and a legal immutable-blueprint fallback. Apply opponent actions only
through `observe_opponent_action`; the method charges event processing while
excluding preceding opponent/transport idle. Any useful background work during
that idle must still be inside `charge_compute()`. Stop every charged interval
before applying an event or transitioning streets. Call `advance_street` only
after the betting state reports round completion and the actual next public
street has arrived. The method charges betting-transition work, archives the
closing snapshot in `completed_street_deadlines`, and is the only ledger-reset
path. Fold and showdown terminals likewise archive and freeze the final street.

For complete reference hands, construct one `SixSeatHoldemDeal` only inside the
replay/oracle boundary and pass decisions through `replay_reference_hand`. The
controlled `OneSeatCardState` may contain only its private pair and the board
revealed for its current street. Never pass the explicit deal, opponent cards,
or future runout into `BlueprintDecisionKey`. Use
`ImmutableBlueprintActionSource` for the reference fallback: source construction
is off-clock, but key construction, lookup, legality, and controlled emission
are charged. Missing entries use its deliberately weak passive total rule;
illegal entries abort. Do not describe that source as a trained blueprint.

The replay result must retain one closing snapshot for every reached street and
one named `ReplayChargedOperation` for every ledger interval. Post-terminal
showdown and settlement verification are harness time, not decision time. Keep
the independent chip-depth pot/payout oracle in tests; production pot assembly
cannot certify itself.

## Bounded campaign admission

Every new bounded evidence runner uses
`pontius.campaign_deadline.MonotonicCampaignDeadline`. Construct it once at the
campaign boundary from the frozen global ceiling, then wrap every target or
arm in `bounded_unit`. The unit maximum must be frozen before execution and
must cover the complete indivisible unit; an observed duration is not a lawful
substitute.

The callback passed to `bounded_unit` must write the current byte-truth atomic
checkpoint. Admission occurs only after that callback completes and only when
the whole unit bound still fits in the remaining `monotonic_ns` allowance. The
post-unit check stops on either a unit-bound overrun or the global campaign
wall. Catch `CampaignDeadlineStop` only to persist its `as_record()` telemetry,
release resources, and retain the preregistered fallback. Execute no later
target, candidate evaluation, certificate, strategy label, or emission.

The campaign deadline never replaces the one shared per-street live ledger or
its emission reserve; that 15,000 ms ledger carries across every agent action
on the street and never resets per decision. A successor config must freeze
both independently. The
ADR-0277 runner is sealed historical code and must not be invoked again; any
successor must import the shared deadline and test its stop path before GPU
work.

## Current h32 evidence reproduction

The latest accepted prospective engineering result is the fixed-seat-5
replication recorded in
[ADR-0194](docs/decisions/ADR-0194-affine-street-mechanism-transfers-to-seat5-but-value-remains-concentrated.md).
Reproduce its frozen invocation with:

```powershell
& $python -m pontius.h32_fresh_selector_stable_affine_street_seat5_audit --config experiments/configs/h32-fresh-selector-stable-affine-street-seat5-v1.json --output experiments/results/h32-fresh-selector-stable-affine-street-seat5-v1.json
```

The run reconstructs four frozen fresh seat-4 blocker shifts and reuses the
complete seat-0 live core with fixed acting seat 5. Its accepted artifact has
SHA-256
`a36e3b6181e412ccf339ab42fe694b0f3b04b0aa60872c498e29bf9e41bfb3cf`.
All four simulated emissions are non-blueprint candidates and all post-emission
exact teachers pass. Rerunning either extreme-seat panel is reproduction, not
new transfer evidence. Neither result is a population, deployment, or general
strategy-quality claim.

New research must start with a committed preregistration and clean tracked
worktree, keep the immutable blueprint anchor, use outcome-neutral gates,
charge the complete street ledger, report memory and wall-clock evidence, and
preserve blueprint fallback. ADR-0195's first profile invocation rejected
before replay on a source-schema lookup. ADR-0197 authorizes its schema-only
successor over the same two already exposed ADR-0194 targets. It may attribute
the resident step but may not evaluate strategy quality or count as new
transfer evidence. Run it only from its clean preregistration commit:

```powershell
& $python -m pontius.h32_resident_step_bottleneck_profile_v2 --config experiments/configs/h32-resident-step-bottleneck-profile-v2.json --output experiments/results/h32-resident-step-bottleneck-profile-v2.json
```

ADR-0191's one-time fresh invocation is already spent. Do not rerun it with
altered guards or inspect another seat-0 shift as a rescue. ADR-0193's
acting-seat-5 replication is also complete; its two timing-extreme targets may
be replayed only under ADR-0195's no-label profiling boundary.

ADR-0193's one-time invocation is also spent. Do not rerun it with a threshold
or rescue direction. No broader fresh panel is currently preregistered; freeze
its board/belief construction, position coverage, and materiality rule before
any new target policy step.

ADR-0199's first invocation rejected before result serialization on the final
memory-field spelling. ADR-0201 then rejected before its warm step because its
guard omitted two legitimate source telemetry fields. ADR-0203 passed that
guard but rejected on the reporting helper's API during result assembly.
ADR-0205 closed the wrapper line with a reviewed direct retained-label replay.
That invocation is complete; the command below is now reproduction only:

```powershell
& $python -m pontius.h32_retained_affine_selector_cascade_direct_replay --config experiments/configs/h32-retained-affine-selector-cascade-direct-v1.json --output experiments/results/h32-retained-affine-selector-cascade-direct-v1.json
```

Config validation reads the retained-label artifact only as opaque bytes for
SHA-256 provenance. The runner computes all 108 feature rows and every
clock-derived K before deserializing or joining label content. It consumes the
exact four-field memory snapshot without an alias, uses the zero-argument
environment API, and may not reuse any failed process state.

ADR-0206 accepts the resulting artifact at SHA-256
`7b251d25b3befcdf2bb5b66dfd6c4ed78818da43f53d5a70e7cdf220d4b6cd93`.
The Tier-B slope-times-radius composite selects every primary retained winner
and survives the soft-excluded control, but Tier A is a poor prefilter. Do not
deploy or tune against these opened labels.

ADR-0207's first invocation rejected before h32 work on the source pass field;
ADR-0209 authorizes the schema-only corrected invocation. It is now complete,
so this command is reproduction only:

```powershell
& $python -m pontius.h32_tier_b_opponent_batch_differential_v2 --config experiments/configs/h32-tier-b-opponent-batch-v2.json --output experiments/results/h32-tier-b-opponent-batch-v2.json
```

ADR-0210 accepts the resulting artifact at SHA-256
`84ed32019afeaa4a18695436c74e41722fc146044a2150de92323833cb8d42fd`.
The batch is numerically exact but its median target speedup is only `1.0059x`,
and the complete six-block ledger fits three of six retained contexts. The
terminal-numerator overlay is already active and reuses `94.47%` of potential
rows; do not schedule it again as a new optimization. The next engineering
customer is a separately preregistered resident record-to-hand fold
differential covering both the warm step and Tier B. The fresh widened,
action-conditioned single-family corpus remains sealed until K is repriced.

ADR-0198 accepts ADR-0197's corrected compute profile. Its result artifact has
SHA-256
`a8f5ed0e2b0866af4b5df0d62ddf1351ca7e8a4e9ace71223602031c1f2ae796`.
The resident GPU pipeline is the primary bucket and host hand folding is the
secondary bucket. Reproduction is not a latency distribution. Before any
hardware recommendation, separate arithmetic from bandwidth pressure on the
same workload; before changing the fold, preregister a numerical differential.

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

The recorded one-time validation and test both pass. Their trace/result
SHA-256 pairs are respectively
`315637393122ef2c47a7d3fddd3000e62d1e66b5adbf138e2a1ac5e92338eae8` /
`5e32a455a394b98dc8ca54ad6d849263ca0899f78900b01deda4051719a30223`
and
`a0e51f653987a1fa6f532ae9e56ea5013823e9a961fd6c0525392a775b53ac2e` /
`47fea9294ff28f37a0dc2e41706267d3fb25f379a01943c575448f36a0221c89`.
Re-running the commands is a reproducibility check, not a new untouched test.
ADR-0028 is the durable verdict.

The blocker-sensitive range-reuse development screen is frozen in ADR-0029.
It is development-only and must not be changed after reading its production
result:

```powershell
& $python -m pontius.river_range_reuse --config experiments/configs/river-range-reuse-development-v1.json --output experiments/results/river-range-reuse-development-v1.json
```

Only identical provenance is a direct strategy hit. A structural-only match
may supply cached information-set topology and a numerical policy prior, but
the resulting policy remains nondeployable until current-range recertification.
The experiment reports lookup, initialization, solving, and recertification
cost separately.

The recorded development artifact passes the warm checkpoint-four gates and
has SHA-256
`470d54d8f10bdd7e02c2f607da7dbe50ee03c91248e05558ac30042a096b78a1`.
ADR-0030 records why no warm prior is promoted: the exact-recertified cached
policy at checkpoint zero dominates additional warm solving. Re-running this
configuration is reproduction, not fresh development evidence.

Only an identical `provenance_digest` authorizes an exact strategy-cache hit.
`structural_digest` authorizes topology and board-work reuse, not strategy
deployment. Raw total variation bounds one fixed policy's value, not equilibrium
reuse. With a certified source exploitability, ADR-0030's stronger bound covers
that same fixed policy's target exploitability only in the two-player zero-sum
game; it still does not certify range identity or policy similarity.

The finite-policy exact incremental-recertification screen is frozen in
ADR-0031 and reproduced with:

```powershell
& $python -m pontius.river_incremental_experiment --config experiments/configs/river-incremental-recertification-development-v1.json --output experiments/results/river-incremental-recertification-development-v1.json
```

The recorded development artifact passes every correctness, perturbation, and
latency gate and has SHA-256
`0daafbc3c241c00befc51f05fa14aaa705a51a880d7b9ae4a5fa2722906b9b9e`.
It uses finite checkpoint-1/4/16/64 DCFR policies, not exact source teachers.
The runner reports hot application, delta discovery, TV bound, compiled-cache
construction, and finite source solving separately. Re-running it is a timing
replicate, not fresh evidence, and the post-hoc bound-first threshold analysis
in ADR-0032 is not a frozen deployment rule.

The generic flat dependency-tape matrix is frozen in ADR-0034 and reproduced
with:

```powershell
& $python -m pontius.dependency_tape_experiment --config experiments/configs/dependency-tape-differential-development-v1.json --output experiments/results/dependency-tape-differential-development-v1.json
```

The recorded development artifact passes every exactness, action-identity,
topology, source-relative replay, support-change, and sparse/dense routing gate.
Its SHA-256 is
`91c007dcf91a4ba7fc3d72cb4603752ba0f59543d144251633c7c13f64404aa2`.
The runner intentionally mixes solver, compiler, redundant controls, and JSON
cost; use its work counts and dirty cones, not its wall time, as architecture
evidence. Re-running it is reproduction rather than a fresh threshold screen.
ADR-0035 is the durable verdict.

The exact multi-size branching transfer is frozen in ADR-0037 and reproduced
with:

```powershell
& $python -m pontius.river_multi_size_experiment --config experiments/configs/river-multi-size-dependency-development-v1.json --output experiments/results/river-multi-size-dependency-development-v1.json
```

The recorded artifact has SHA-256
`8198e6b0f013b1d1fe92a2fa0fcbbf1119cc0e6a22ab360aeae23c6c55c89d08`.
It verifies the pre-widening dependency-tape source hash, audits all 19 terminal
paths per deal independently, and compares matched fixed and 3x2 topologies.
Use absolute dirty-node ratios as well as dirty fractions: wide sparse work rises
about 2.7x despite slightly better relative sparsity. The runner's total wall
time includes redundant correctness controls and is not an online latency
benchmark. ADR-0038 is the durable verdict.

The full-action selective-expansion pilot is reproduced with:

```powershell
& $python -m pontius.river_selective_experiment experiments/configs/river-selective-expansion-pilot-v1.json --output experiments/results/river-selective-expansion-pilot-v1.json
```

The recorded 1,404,427-byte artifact has SHA-256
`c334724e380bca370cc691917a780f4857a41ff34fd724ff0dce2ffee996a15e`.
It contains one development board group only and explicitly authorizes no mask,
warm strength, scheduler, native latency claim, or neural-leaf claim. Exact
continuation construction is charged separately from hot cached lookup; every
candidate is scored only in the unwrapped full 3x2 game. Use the fixed-warm
mask oracle to measure branching opportunity without also selecting warm-start
strength. Re-running this pilot is calibration reproduction, not new transfer
evidence. ADR-0040 is the durable interpretation.

The preregistered group-separated development matrix and selection-free
analysis are reproduced with:

```powershell
& $python -m pontius.river_selective_experiment experiments/configs/river-selective-expansion-development-v1.json --output experiments/results/river-selective-expansion-development-v1.json
& $python -m pontius.river_selective_analysis experiments/results/river-selective-expansion-development-v1.json --output experiments/results/river-selective-expansion-development-v1-analysis.json
```

The matrix and analysis SHA-256 values are respectively
`7571a8a2f3c08034b53982b4ac122106fbe3d1cc7b216d3ee4ba58cf01fdd2ff`
and
`c1fc2962399d2f8f588504b418ffba8d274ec1d73978af516e48f58075a4e392`.
The runner stops each source at the first declared DCFR checkpoint satisfying
normalized NashConv `<=1e-5`, enforces frozen selective-source hashes, and
records one fixed warm regime. Boundary features are constructed before target
best responses; solver probes are constructed before candidate labels, and
their cumulative timing is charged. The analyzer fits no selector. Treat all
mask/no-op values as exact-future ceilings and ADR-0042 as the durable verdict.

The frozen compact causal screen is reproduced with:

```powershell
& $python -m pontius.river_selective_screen --source experiments/results/river-selective-expansion-development-v1.json --rule experiments/rules/river-selective-width-screen-v1.json --output experiments/results/river-selective-width-screen-v1.json
```

The screen artifact SHA-256 is
`ee7df32361a08236603e4b2d8d3e6f26d1a209f98b86bb5ffce53fcf14be2794`.
It selects fixed `b3r2` and fails the frozen gates. Do not change a feature,
objective, arm, depth, uncertainty multiplier, or threshold and rerun it as new
evidence. Do not generate the proposed fresh adaptive-width replication or any
reserved context from this branch. ADR-0044 is the durable rejection.

## Continuation protocol

1. Read `PROJECT.md`, `STATUS.md`, and the relevant decision records.
2. Confirm the active checkpoint and working-tree status.
3. Run the fast test suite before modifying correctness-critical code.
4. Make one measurable change.
5. Verify against the reference and record the experiment configuration.
6. Add the immutable decision record, regenerate `STATUS.md`, and run the
   documentation freshness and link checks.
7. In every new evidence runner, use `pontius.runner_harness_v2` to read one
   bounded byte snapshot, require a complete schema, and retain its digest.
   Never accept duplicate/nonfinite JSON, a shallow mutable artifact, or a pass
   bit without all fields needed by its consumer. Historical pinned runners
   retain `pontius.runner_harness` only for reproduction.
8. Convert normalized guards and raw quality only through
   `pontius.payoff_semantics`. The payoff span comes from
   `layout.game.payoff_span`; stack, pot, and action sizes are not substitutes.
9. Route new GPU record-fold customers transitively through the v2 contraction,
   CFR or selector modules backed by `pontius.resident_record_to_hand_fold_v2`.
   Supply distinct typed reach allowances and derive payoff span from the game;
   the predecessor is retained only to reproduce hash-pinned evidence.
10. Carry `pontius.street_deadline.StreetDeadlineLedger` across all controlled
    actions on one street. Charge every interval of event processing,
    foreground/background agent work, legality, selection, and emission;
    exclude only opponent/transport idle. Reset only on the exact next street.
11. Publish successor evidence through `pontius.deadline_owned_result` and load
    it only through its verified loader. A canonical file with no completion
    seal, or with a publishing lock, is diagnostic state rather than evidence.
12. Route full-hand reference actions through `pontius.no_limit_betting` and
    `pontius.legal_decision_spine`, cards through `pontius.holdem_cards`, and
    fallback lookup through `pontius.immutable_blueprint`. Never infer a legal
    raise from a simplified river workload or enumerate all full-stack integer
    sizes as a deployable action abstraction.
13. Keep ADR-0292's v1 and ADR-0294's v2 sizing lattices outside
    `reference_hand_replay`, the convex master, and resolver paths. Treat both
    opened river panels as development evidence only. Before v3, freeze a
    candidate-blind sizing-power diagnostic; structural showdown diversity is
    not a substitute for measured full-over-narrow opportunity.
14. Open sizing-power values only through
    `pontius.sizing_power_diagnostic.run_candidate_blind_sizing_power_qualification`.
    Its batch-bound result owns the contiguous prefix and stop reason. Do not
    use scratch loops, open contexts after target/ambiguity, enlarge ADR-0295's
    pools, or open batch 2.
15. For ADR-0297, commit the preregistration before constructing width-four
    pools and commit all three structural pool digests before invoking its
    value-owning runner. Preserve the one-bet tree and exact frozen thresholds;
    do not use width-four yield or local diagnostic time as a runtime-quality
    claim.
16. Reconstruct ADR-0298's width-four structures only through
    `pontius.width_four_sizing_power.build_adr0297_width_four_pool`. Keep that
    module free of sizing-solver imports. Open values only through the separate
    ADR-0297 owned runner after the structural commit, in batch order, and stop
    the campaign at the first failed batch.
17. Reproduce ADR-0299 values only through
    `pontius.width_four_sizing_power_evaluation.run_adr0297_width_four_campaign`.
    Gate probability-simplex and chip-valued envelope residuals separately;
    never use the reduced oracle's legacy mixed-coordinate maximum as a
    semantic allowance. Treat every ADR-0297 panel as development-only. Freeze
    v3 before deriving fresh representative and qualified-panel seeds.
18. ADR-0300 permits exactly one v3 rule: preserve a distinct two-pot origin;
    substitute three-halves pot only when clipped two-pot equals a mandatory
    minimum, maximum-contestable, or all-in anchor. Commit the source digest and
    exact fresh seeds before panel construction, then commit candidate-blind
    representative/qualified panel identities before opening any v3 value.
19. ADR-0301 freezes source digest
    `ebae17f69c4f37377edf0fb0c55a99049c8688c8517dcbc525230d8e418a811a`
    and the two exact ASCII streams. Construct only the value-free 48-context
    representative structure and separate 96-context qualified pool first;
    commit their identities and finite-inventory disjointness checks before
    opening full/narrow qualification values. Keep the v3 source absent from
    structural and qualification modules until both final panels are sealed.
