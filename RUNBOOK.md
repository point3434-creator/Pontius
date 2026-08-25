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

The exact betting foundation is `pontius.no_limit_betting`. ADR-0308's
governing one-seat timing wrapper is `pontius.legal_decision_spine_v2`; the
unversioned `pontius.legal_decision_spine` remains the ADR-0286 historical
complete-hand wrapper. Both use integer chips and raise-to totals. Do not feed
the simplified `river_multiway` or `river_multiway_multi_size` action semantics
into either boundary; those modules remain intentionally restricted sealed
workloads.

Create a prospective live hand with `LegalDecisionSpineV2.new_hand` or
`six_max_100bb`. Those factories capture the external boundary before initial
betting-state construction. Invoke `observe_opponent_action` immediately on
event receipt and `advance_street` immediately on the public transition; each
method owns the transition boundary and starts the continuous action wall if
the result makes the controlled seat the actor. A direct v2 constructor must
not receive a prebuilt state where the controlled seat is already acting unless
the exact matching action clock was started at the external boundary; it fails
closed otherwise.

Run the focused rules, one-seat, timing, card, blueprint, replay, randomized,
and exhaustive checks with:

```powershell
$env:PYTHONPATH = "src"
& $python -B -m unittest tests.test_no_limit_betting tests.test_no_limit_betting_exhaustive tests.test_action_clock tests.test_preparation_bank tests.test_legal_decision_spine_v2 tests.test_legal_decision_spine tests.test_street_deadline tests.test_holdem_cards tests.test_immutable_blueprint tests.test_reference_hand_replay -v
```

For ADR-0308, open the exact decision before resolver work and wrap all on-clock
work in `charge_compute()`. Preparation is legal only while no controlled action
is active. Build it through `PreparationBank.start_preparation` and
`seal_preparation`, or its exception-safe context; never supply a duration.
Target the exact future betting-state digest, and bind cards, board, beliefs,
action model, and every other consumer dependency inside the semantic-context
digest. Claim through `LegalDecisionSpineV2.claim_preparation`; the current
public-state digest is derived by the spine and cannot be caller supplied. A hit
adds credited preparation to telemetry only. It does not change the action's
15-second remainder. Stop resolver work before emission and always supply a
legal immutable fallback.

For ADR-0286 historical reproduction, open the ticket once, place all resolver work
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
Do not use this cumulative-street controller as the governing timing path after
ADR-0307.

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

The campaign deadline never replaces ADR-0307's continuous 15-second action-
response wall, its emission reserve, or separate online-preparation accounting.
A successor config must freeze these independently. The
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
10. Retain `pontius.street_deadline.StreetDeadlineLedger` across all controlled
    actions on one street only when reproducing ADR-0282/0286 evidence. ADR-0307
    supersedes it for new live-timing claims; do not silently reinterpret its
    cumulative charged seconds as a per-action response clock.
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
20. Rebuild ADR-0302's value-free families only through
    `pontius.fresh_collision_repair_structures.build_adr0301_fresh_structure`.
    Their digests are `b678f1140dd7ba75f5315abf58392d42b42a1a633c3249ec36991846a1bbab69`
    and `fb26a8cfd2f82fd56896e22f6d006495f1148669dd6db3f56dcf2e79deeb4146`.
    Convert and open only the sealed qualified pool through a separate owned
    runner after this structural commit; keep representative and v3 values
    unopened, bind every semantic field, and stop inside the runner at target,
    ambiguity, or exhaustion.
21. Reproduce ADR-0303 qualification only through
    `pontius.fresh_collision_repair_qualification.run_adr0302_fresh_qualification`.
    The result, qualified panel, teacher, and campaign digests are respectively
    `c5be094e616043644a13ebbd477565ff548593a9d7d1f70dac0ae5340cbe0c23`,
    `05f00a99ccec22bfea07abd405b1089414a89bce9a4c4e704efceb132ea1cf29`,
    `b88b47f2260da31bdb7e49a0d454309327483ded0ff6ea7b17d77bd2cf914ada`,
    and `3ada7c7a68002eb2fa3d0e6ca904f0df771f17e8270fd09ef10cedef1772d8fe`.
    Rebuild panel membership without values through
    `build_adr0302_qualified_panel`. Before any v3 value, preserve the exact
    48-then-24 family order and every ADR-0300 conjunct; stop before qualified
    if representative fails.
22. Reproduce ADR-0304 only through
    `pontius.collision_repair_v3_evaluation.run_adr0300_collision_repair_v3_evaluation`.
    The representative, qualified, and stopped-campaign digests are
    `37217f9b4b1dab282dd0c0a998559d10714de6e593b73d2209b45033a75f8c30`,
    `fdf2261940947020d38ad518ab37c2a8031dc2b8a161157f1e26e862ed0c83c2`,
    and `5e27d5767b35ef43d2a75a9c97aca3d46a3ee966037220299d82c8d571a6dbdf`.
    Preserve the qualified raw-chip recovery failure at
    `0.800547544995807 < 0.90`; do not substitute normalized loss, a mean of
    ratios, or local campaign seconds. Keep v3 parked and every integration
    path closed. Any successor needs a new prospective mechanism and wholly
    fresh panel authority before source code or values.
23. ADR-0305 permits no v4 source except the exact-rational capacity-filling
    pot-odds rule. Start with every v3 raise, fill to the lesser of seven and
    exact legal width by closed-form midpoint inversion plus floor/ceiling
    checks, and tie toward the smaller raise. Never enumerate a chip interval
    or use floats, cards, ranges, values, or opened panels. The three exact
    representative/qualified-A/qualified-B seed texts are already frozen in
    ADR-0305. Commit exhaustive source validation and its digest before
    constructing any stream, then commit all three structures before opening
    candidate-blind qualification values.
24. ADR-0306 freezes that source at SHA-256
    `37824e44b7793b10b081957fc8be387bdca5c565b4bfe2386ca13f7e1c785c8b`.
    Reproduce it only through
    `pontius.capacity_filling_action_abstraction.CapacityFillingActionAbstractionSource`.
    ADR-0309 now seals ADR-0305's 48-context representative, 96-context
    qualified-A, and 96-context qualified-B streams through
    `pontius.fresh_capacity_filling_structures`. Their structure digests are
    `6ab4f7451b008a3a82309473df28384ede65e94da27fccc45a920e6ef4a4ffbc`,
    `54cd7ed77a7c37a67dc050e8155fbbbcad61e4d952316fa2e3eb5c2f602110ed`,
    and `23c186d3c393c9d233558c8150e9bb1f7c38f75f6e3cf1d7c7685341057f5870`.
    Keep v4 out of replay, blueprint, convex-master, resolver, and strategy
    integration.
25. ADR-0307 supersedes the cumulative-street timing contract before those v4
    structures. Preserve the old ledger and spine for reproduction. ADR-0308
    now accepts the additive continuous 15-second action-response ledger, one-
    use provenance-bound online preparation bank, and exact legal-decision-
    spine v2. Preparation records actual work, not unused milliseconds; a valid
    credit never extends the response remainder. Use only this successor for
    prospective timing claims.
26. Resume ADR-0305 only at its three value-free stream constructions, in the
    frozen representative, qualified-A, qualified-B order. ADR-0309 records
    their completed identities and finite disjointness. Any later allocation
    experiment must report the full marginal chip-quality curve over both
    response and preparation milliseconds, plus misses and invalidation waste;
    credited compute or hit rate alone is not a quality result.
27. Reproduce ADR-0310 only through
    `pontius.fresh_capacity_filling_qualification`. Qualified A must stop at
    context 72 with campaign digest
    `c292dd30782d26a43ef71038f7f2fd55cabfa1004f6f049b8476e69df3f7462d`.
    Only that exact pass may construct B. B must stop on solver call 43, the
    full-integer arm at context 21, with failure digest
    `03c5dc4f00c0429d3c615352a1d52f9c64dec0d3b4c4cf72f6d7cc171e3a26fe`.
    Do not run B's minimum/all-in arm at context 21, open context 22 or later,
    accept A's provisional panel, or open representative/v3/v4 candidate
    values. Keep v4 and every integration path parked.
28. Any native-simplex repair begins with a separate prospective,
    candidate-independent robustness preregistration. The known B context-21
    LP may be a development regression, but freeze an additional adversarial
    corpus and independent diagnostic/certificate contract before evaluating
    a replacement. Never use alternate-solver feasibility, looser tolerance,
    or a post-outcome rerun to revive ADR-0305 qualification.
29. ADR-0311 freezes that audit before source or values. Implement only its
    pure unit-tagged reduced-sizing compiler plus the 48-record exact micro-LP
    and 64-context fresh width-four constructors next. Preserve the literal
    three seed texts, five transform rules, 177-base/885-instance counts, and
    finite-inventory collision rejection. Commit source hashes and every
    corpus identity before exact vertex enumeration, native/HiGHS invocation,
    objective reconstruction, or certificate evaluation. Do not edit
    `pontius.linear_program` or write the audit runner in this boundary.
30. ADR-0312 seals the value-free implementation at 48 micro inputs, 64 fresh
    contexts after 300 raw card candidates, 177 bases, and 885 representations.
    Preserve complete-corpus SHA-256
    `4be6dcc311bc2f885ce9ad312cee8294f38231180ab78bbbfb6497184b1597a3`.
    Implement only the owned runner and typed observation/result schemas next,
    including exact micro enumeration, original-coordinate sizing
    reconstruction, outward certificate plumbing, complete failure capture,
    and the fixed 2,655-call schedule. Verify with mocks and frozen toys, then
    commit source/environment/options identities before any sealed native,
    HiGHS, exact-enumeration, reconstruction, or certificate invocation. Do
    not edit `pontius.linear_program`, change an input/transform, or reopen v4.
31. ADR-0313 seals `pontius.native_simplex_audit_runner` at SHA-256
    `cfb127960e3d501a156f14d22244ecd122874b74fefb668685f9a721503ade16`
    and its separate invocation seal at
    `a0305de4af43366f6e2ed2a1d5bcd4fafba01f94d5e7103201bcaa9385ff05e3`.
    The bound runtime is CPython 3.14.6, NumPy 2.5.2, SciPy 1.18.0, and
    embedded HiGHS 1.12.0. Invoke only through
    `execute_sealed_adr0311_audit`, only on complete corpus SHA-256
    `4be6dcc311bc2f885ce9ad312cee8294f38231180ab78bbbfb6497184b1597a3`,
    and only as the full variant-major 2,655-observation campaign. Retain every
    exact-work, backend, residual, reconstruction, certificate, exception, and
    sign-clip record after any individual failure. Do not sample, run a prefix,
    tune an option, change an allowance, edit a sealed source, or interpret a
    partial result. The already-known native failure does not stop later arms.
    Record the frozen conjunctive pass or rejection before any replacement ADR;
    no outcome can revive v4 or authorize a consumer migration directly.
32. ADR-0314 retains the complete one-shot campaign at
    `experiments/results/native-simplex-robustness-audit-v1.json`, 110,068,679
    bytes, SHA-256
    `1f5e49cf1f855135283a0b8794656fc9e4fa6447886cb5fd8fe6dfcdcac8039a`.
    Preserve all 2,655 observations. HiGHS dual simplex and IPM each pass all
    885 arms; native records 849 verified returns and 36 exceptions. The
    literal gate rejects on its sole `known-native-regression-mismatch`: the
    frozen predicate required `(215,)` as the complete failing-row tuple, while
    ADR-0310 had recorded row 215 as the unique maximum-residual row. Do not
    rerun a backend or silently reinterpret this as a pass. A successor may
    source-seal only an artifact-bound semantic correction, with a mocked
    multi-row/unique-maximum control, before authoritative reanalysis. It may
    change no result byte, HiGHS conjunct, option, allowance, native source,
    action candidate, or consumer.
33. ADR-0315 source-seals `pontius.native_simplex_audit_reanalysis` at
    canonical-LF SHA-256
    `0755546e6260708ffb4165ec50ebf4ff88c473354faeb7303e8b84e568fca1be`.
    It is bound to the exact ADR-0314 byte count/digest, runner/corpus identity,
    environment/protocol subtree digests, complete variant-major schedule, and
    unchanged HiGHS gates. It treats required unique maximum row 215 separately
    from an optional complete failing-row set and proves that distinction with
    synthetic multi-row controls. After this source-only boundary is committed,
    invoke only `reanalyze_sealed_adr0314_artifact` once on the retained
    artifact and persist its deterministic canonical assessment before any
    replacement-adapter decision. Do not invoke a solver, exact enumerator,
    reconstruction, or certificate; change an artifact byte or allowance; or
    treat a corrected pass as runtime, quality, or consumer evidence.
34. ADR-0316 records the one temporally separated artifact-only invocation. The
    canonical 1,168-byte assessment has SHA-256
    `f44d518bba0953c064cd04c3015c37ec8abf27a91a96afa9902caf16c8ffe038`;
    the retained terminal-LF file is 1,169 bytes with SHA-256
    `d8ce7c26d935768f8476c183950e96e5be2692fac5e821bf9b674d373ae665c1`.
    It reports a complete 2,655-arm schedule, 885/885 verified HiGHS DS and IPM
    arms, the nonexclusive 21-row known failure set with unique maximum row 215,
    zero corrected-gate failures, and DS replacement eligibility. Interpret
    that eligibility only as authority to preregister a later adapter screen.
    Before source or results, freeze identical real master sequences and compare
    rebuild against persistent modify-in-place HiGHS with warm basis reuse;
    authorize a structure-specialized proposer only behind independent
    certificates and HiGHS fallback and only if complete-ledger marginal chip
    quality per millisecond leaves material headroom. Do not use audit timings
    as runtime evidence or open v1-v4.
35. ADR-0317 separates the compact reduced-sizing solver from the behavioral
    one-seat master. Implement only a separately named canonical HiGHS
    dual-simplex sizing adapter next, using the public SciPy interface,
    original-unit policy/envelope reconstruction, an exactly normalized
    behavioral lower bound, an outward-rounded bounded-variable upper bound,
    and distinct semantic allowances. Source-seal its import closure, runtime,
    options, result schema, and later 177-base schedule before invoking any
    sealed base. Do not edit a v1 consumer, invoke ADR-0310/v4, or open a fresh
    candidate value. The behavioral master already uses HiGHS and remains
    parked until a fresh certified-v2 complete ledger reaches the 5%
    perfect-solver materiality trigger.
36. ADR-0318 source-seals `pontius.certified_reduced_sizing_highs` at
    canonical-LF SHA-256
    `4723a7b153b6285081c67e8e5c20b0f1097c7d8acf9ab4c5482373984947e80f`.
    Its source verifier also binds `linear_program_certificate` and
    `reduced_river_sizing_lp`; its runtime verifier binds CPython 3.14.6,
    NumPy 2.5.2, SciPy 1.18.0, and embedded HiGHS 1.12.0. Only toy controls
    may call the adapter at this boundary. Implement and source-seal a separate
    failure-complete runner next, freezing the exact canonical order of one
    known regression, 48 exact micro bases, and 128 fresh sizing bases before
    any retained call. Do not edit the adapter, invoke a transformed arm, call
    a v1-v4 owner, or connect `reduced_river_sizing_oracle`.
37. ADR-0319 source-seals `pontius.certified_sizing_validation_runner` at
    canonical-LF SHA-256
    `5116c1d4b2632da76cf83e6d7d015b190e061330094d27b3c9719631a89252e1`.
    Its schedule SHA-256 is
    `36f34eb820bfaa4b58747201c9b27779553d0f8e250c73786da34542b5d8cba4`:
    48 canonical exact-micro paths and 129 canonical certified-sizing paths,
    each with exactly one counted public HiGHS-DS call. Invoke only
    `execute_sealed_adr0319_canonical_validation`, exactly once after this
    source commit, and persist its returned `canonical_bytes` before applying
    the frozen correctness assessment. Do not tune or rerun after a rejection,
    use a transformed representation, edit either verifier, connect a legacy
    consumer, or interpret retained wall time as decision latency.
38. ADR-0320 retains the sole sealed ADR-0319 campaign at
    `experiments/results/certified-sizing-canonical-validation-v1.json`,
    5,022,120 bytes and SHA-256
    `5a2a75a9cf0ddaf60795597aa6ff3f788d4bfc7ccf5519813f37856dad02f9f5`.
    The 701-byte assessment SHA-256 is
    `a3c360c61ae6edd28eb2df68b83339a549d6726a151c60fee46bc488dc54bfd9`.
    Interpret it only as 177/177 canonical correctness passes and bounded
    eligibility for a separately preregistered additive v2 reduced-sizing
    consumer. Do not rerun the campaign, edit ADR-0318/0319, quote its compact
    LP timings as complete decisions, connect the historical v1 oracle, or
    infer action-width quality or poker strength.
39. ADR-0321 freezes the next consumer contract before implementation. The
    additive v2 path is research-only: accept only a two-live-seat river
    opening with no wager faced and a fully contestable maximum; bind exact
    joint probabilities, showdown signs, and a caller-supplied ordered subset
    of kernel-legal raise-to totals containing minimum and maximum; convert
    those totals to distinct incremental wagers; verify source/runtime before
    one counted public HiGHS-DS call; and return either certified endpoints,
    policy, and fold/call responses or a typed no-action rejection requiring
    the caller-owned legal fallback. Do not emit/apply an action, import the
    historical native consumer or v1-v4 owners, open a fresh action-width
    value, or call this fold/call-only model a production six-max decision.
40. ADR-0322 source-seals `pontius.certified_reduced_sizing_consumer_v2` at
    canonical-LF SHA-256
    `931d6aa2d919efc3fc39e3d404dfa4bf0f6ced756acc2a918dc6c0cde8b4210a`;
    its protocol SHA-256 is
    `688263741a95eaf8405f3b69fd2cf7361d54ec265593883f2a55d767fca32a3c`.
    Use it only for the exact two-live-seat river fold/call research shell.
    Supply nominal kernel raise-to totals, never raw increments in their place;
    preserve full-versus-restricted scope and minimum/fully-contestable maximum
    anchors. An accepted call returns evidence but no action. A rejection owns
    no fallback action and requires the caller's legal one. Do not edit the
    sealed closure, connect the historical oracle, treat the eleven unsealed
    controls as a sizing result, or open a fresh action-width value without a
    separate preregistration.
41. ADR-0323 provides that separate preregistration but opens no value. The
    next source may construct only a standalone 96-context h4 development pool,
    exact betting-kernel integer raise universes, and lexicographic anchored
    subset schedules for raise widths two through six. Check does not count as
    a raise. Do not import a v1-v4 action owner, prior panel/value, legacy sizing
    oracle, result artifact, replay, resolver, blueprint, clock, preparation,
    or action path. Do not construct the transfer pool: its seed is derived
    only from a later frozen mechanism commit. In later value work, compute
    full-minus-subset intervals as `[L_full-U_subset, U_full-L_subset]`, retain
    distinct chip and normalized controls, and call an added size priced only
    after its exact fold/call response-row set is closed.
42. ADR-0324 source-seals `pontius.fresh_action_width_structures` at
    `429f72fff02de515536db36a4754708e71cf93653ad6574026c1fe3c4de82acf`.
    Its development pool digest is
    `48e084db53941615f3b1e2d13814718a2c833369b0b5e827f3adc7ee1fc799ed`:
    96 contexts after 440 attempts and 12,556 anchored subset records across
    raise widths two through six. These are value-free identities, not solver
    calls or latency. Preserve the adjacent manifest, do not add a transfer
    constructor, and do not call ADR-0322 on this pool until the separate
    ordered qualification owner, interval types, one-call evidence, stop state,
    and panel rebinding are source-sealed.
43. ADR-0325 source-seals `pontius.fresh_action_width_qualification` at
    `95974fee5a3fe056828bdb899986235f7b482d9e3d36ec066c0d85e822cb4ca7`.
    Its 192-task schedule digest is
    `de4b5c39cb973673d51dd9b80be5e47193d6b0ace77c77cd56471dca7eeeb6cc`.
    Invoke `run_adr0323_development_qualification` at most once and retain its
    first terminal result. It must run complete then width two per context,
    subtract `[L_full-U_subset, U_full-L_subset]`, use the context payoff span,
    and stop on qualifier 16, exhaustion, ambiguity, typed consumer rejection,
    or runner rejection. Do not retry, alter source, open intermediate widths,
    construct transfer, or derive a panel unless the result is target-reached.
44. ADR-0326 retains the one authorized qualification invocation at result
    SHA-256
    `d8bcf79a08eed1af6fece257b4917424e71123574c4a99b858c7a7e93cf2a7f5`
    and panel SHA-256
    `7757bfb37bc28f4a23707f9b4dfae9401ffb0afa016e87890d18a18117c66792`.
    The prefix contains 51 contexts and 102 accepted public calls; the
    qualifiers are
    `0,6,11,14,19,20,23,25,27,28,29,32,42,45,49,50`. Verify the committed
    artifact only through
    `verify_adr0323_qualification_result_artifact`; it must make no solver call
    and must reproduce all endpoint, request/legal/LP, result, and panel
    identities. A rendered terminal truncation is not loss authority: recover
    only the original raw command record, never rerun a one-shot campaign to
    reconstruct output. Before any width-three-through-six value, source-seal
    the exact 2,495-task exhaustive teacher and its failure-complete result
    boundary. Greedy pricing, transfer, preparation, and action emission remain
    closed.
45. ADR-0327 source-seals `pontius.fresh_action_width_teacher` at
    `14250c3dbe504318640fc0ca35098c5c014e03eca23d3ea8fee4ec470705b8fd`.
    Its exact schedule digest is
    `0998564a13428bfea300086011a9c5bce649ff3ec1bd00d20a632992dcd43f45`:
    16 complete-universe tasks and 2,479 anchored subsets in width then
    lexicographic order. The source retains interval-max teachers, every
    certified nondominated subset, sole-survivor uniqueness, and reporting-
    only equivalence that may be empty; payoff-span normalization is separate.
    Before the one authorized value run, require a clean worktree and absent
    final plus `.partial` paths. Invoke only the no-clobber retained wrapper:

    ```powershell
    $env:PYTHONPATH = "src"
    $env:PONTIUS_TEACHER_RESULT = [IO.Path]::GetFullPath("experiments/results/fresh-action-width-exhaustive-development-teacher-v1.json")
    & $python -B -c "import os; from pathlib import Path; from pontius.fresh_action_width_teacher import run_and_retain_adr0323_exhaustive_development_teacher as run; result = run(output_path=Path(os.environ['PONTIUS_TEACHER_RESULT'])); print(type(result).__name__, result.digest, result.public_highs_ds_invocation_count)"
    ```

    The staging marker is created and fsynced before the first consumer call.
    Any final or staging file rejects before values; any failure leaves evidence
    that forbids silent retry. Do not invoke the raw runner for terminal output,
    alter a stopped campaign, or substitute a backend. Commit exact artifact
    bytes and a solver-free rebinder before interpreting the curve or opening
    greedy pricing. Runtime cost may later choose only inside retained value
    freedom; it cannot edit the teacher set.
46. ADR-0328 retains the sole teacher invocation at campaign-result SHA-256
    `6da6f43a02c6a0f97237bcdc9c66f845bac5735c290236d0ffdab481b7f82765`.
    The canonical artifact is 4,975,258 bytes with SHA-256
    `f94a76d283c18b681998d1c54e6037a21575b214fe613e0f58221734f4314661`;
    all 2,495 calls completed and the `.partial` witness is absent. Verify it
    only through the solver-free owner:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -c "from pontius.fresh_action_width_teacher_result import verify_adr0323_exhaustive_teacher_result_artifact as verify; result = verify(); print(result.campaign_result_sha256, len(result.contexts), result.public_highs_ds_invocation_count)"
    ```

    The retained curve makes width three the first full-regret-only pass; this
    is not an action-width selection. Before another development value,
    source-seal the direct closed finite-block greedy owner, its exact omitted-
    raise order, incumbent/augmented request and response-row-set identities,
    complete fold/call closure, lower-endpoint/smaller-raise selection rule,
    teacher-excess arithmetic, stop state, and result schema. Do not construct
    transfer, relax a gate, use campaign wall time as decision latency, or let
    cost edit the teacher survivor set.
47. ADR-0329 source-seals `pontius.fresh_action_width_greedy` at
    `6e824b83c8789ae64f1859aa5536769a815aca5dd0480500268e335a3a6244f5`.
    Schedule SHA-256
    `a6811bbd4131f73735e2336bb064443a7d30b07e73d36abbbab2e7ca6c91569a`
    binds 2,479 unique arms and 7,848 possible parent-plus-one-raise
    transitions. One realized branch makes exactly 400 calls. ADR-0330 records
    that the sole authorized invocation was made from clean commit
    `e4735165137eb9b72468439fdf0a23878f7debb0` and failed during final
    width-gate serialization. **Do not execute this campaign again.** Both
    public entry points now reject before I/O or solving. Preserve the exact
    `.json.partial` witness; do not delete it, change the output path, call the
    private executor, or infer a width from the completed-result traceback.
48. For any non-replay successor, first canonicalize and rebind a fully
    populated synthetic completed campaign, including every nested width-gate
    digest. Then crash-inject after every append to an append-and-fsync
    write-ahead evidence journal and prove that all completed observations
    survive process termination. Derive a new population seed from the later
    committed recovery protocol, never from lost values, and seal its teacher,
    schedule, artifact paths, and stops before any solver call. The ADR-0329
    panel, exact output path, and 400 calls are permanently ineligible for a
    replacement run.
49. ADR-0331 freezes the new population seed as
    `pontius|adr-0331|fresh-action-width-nonreplay|population|recovery-commit=49044e58fc3a2a582fda11daba4f641da5b3e646`.
    Its ASCII SHA-256 is
    `a419d1651708dae88c451546dae5639c8d1c2840a4441b93b712802a9b2541ba`.
    The next checkpoint is source-only. Reproduce 96 ordered contexts under the
    ADR-0323 generator distribution and reject any semantic digest shared with
    the complete original 96-context pool. Exercise one synthetic journal with
    one header, exactly 400 observations, and one terminal record. Every record
    hashes a self-free body, chains the prior envelope digest, and returns no
    append receipt until `write`, flush, and `fsync` complete. Prefix recovery
    must preserve a torn or malformed suffix byte-for-byte. Do not import a
    consumer, solver, qualification/teacher/greedy result, transfer, resolver,
    or action path, and open no sizing value.
50. ADR-0332 source-seals `pontius.durable_evidence_journal` at
    `a9f815a41abc8d9977375e0c8e71f66f788dd8d811d016735cb08ffa06bf5c11`
    and `pontius.fresh_action_width_nonreplay` at
    `b870feb17d6e344b130f7b30d8b776be5b40537e3e71b7a14b9b4d2bcbae3e92`.
    The new population digest is
    `441790b2e24fa2187ad7c64b456d75b3ccd8e9d9951ce340eabc16eb4255821c`:
    96 unique contexts after 551 attempts, disjoint from all 96 sealed
    ADR-0323 contexts. The 402-record synthetic journal is 610,098 bytes with
    SHA-256
    `66c9b441fa71597280d4b7ee7a64a70079e212b5594332a8f4e1cc4dc0e9e136`.
    These are value-free source and systems identities. Do not interpret any
    synthetic endpoint, gate, or fixture width as sizing evidence. Do not
    invoke ADR-0322 on the new pool yet. Source-seal the replacement
    complete-universe-then-width-two qualification schedule, conservative
    classifier, receipt-gated call owner, failure-complete reduction, and
    prospective output path before its first consumer call; qualification,
    teacher, direct mechanism, transfer, and action values remain closed.
51. ADR-0333 source-seals
    `pontius.fresh_action_width_nonreplay_qualification` at
    `c4979aa8b84ca30c80a3a4a01f4d345bd312dfef044d57243d723c71ac39cf5d`.
    Protocol SHA-256 is
    `3506b0a33aec61b85b1a0a9ade7e1d86c8a944ad79cecbb1253b611d46c69c61`
    and the exact 192-task schedule SHA-256 is
    `132513efa7cdf32298e5d19cb60afa69fda2580a8e98c9b3e4724781d07a50b2`.
    Before invocation require a clean commit containing ADR-0333, the exact
    sealed source closure, and absence of
    `experiments/results/fresh-action-width-nonreplay-qualification-v1.jsonl`.
    Then invoke only the public no-clobber wrapper once:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -c "from pontius.fresh_action_width_nonreplay_qualification import run_and_retain_adr0331_nonreplay_qualification as run; result = run(); print(type(result).__name__)"
    ```

    The journal, not terminal stdout, is the authority. Every next consumer
    call requires the prior post-`fsync` receipt. Any target, exhaustion,
    ambiguity, nested reversal, typed rejection, unexpected exception, or
    infrastructure failure closes the campaign without resume, deletion,
    overwrite, or retry. Retain the exact artifact bytes and source-seal a
    solver-free result/panel rebinder before opening a teacher value. Do not
    call the private executor, infer values from synthetic controls, or promote
    the h4 heads-up fold/call result into action width, latency, or strength.
52. ADR-0334 records that the command in item 51 ran exactly once from clean
    commit `2d492efb58c849dd63748313624678bc2583d747` and reached
    `target_reached`. **Do not invoke it again.** Retain
    `experiments/results/fresh-action-width-nonreplay-qualification-v1.jsonl`
    byte-for-byte: 391,986 bytes, 100 final-LF records, SHA-256
    `be33cfc4fa5955409ea478552fcdf52de62812ce37fdee94190726537b11f956`.
    The exact terminal SHA-256 is
    `ef824c1ce71c6bb6751b2a89d68aa8dc739bb24b0a519b67cfad2c9093b9f876`
    and the exact target-only panel SHA-256 is
    `4fcdb9927fe7626acdf8752a96c1fb71ab085d61e93ad54bd2c8e72f34dc0b71`.
    Verify retained evidence only with
    `verify_adr0334_nonreplay_qualification_result_artifact`; it is
    solver-free and must succeed when the public qualification wrapper,
    certified consumer, and SciPy solver are forbidden. The result is 98
    accepted one-call arms, 49 complete contexts, 16 qualifiers, 33
    nonqualifiers, and zero ambiguity. It has no elapsed field: do not derive a
    latency or 15-second capacity claim. Before any later value, implement and
    source-seal a new 2,113-task exhaustive teacher over this exact panel. Do
    not reuse ADR-0328's old-panel values, open a scratch teacher, or construct
    direct mechanism, transfer, preparation, or action state.
53. ADR-0335 source-seals
    `pontius.fresh_action_width_nonreplay_teacher` at
    `62598e606be983b9fef60a32933bcbbb113ab75aca5aa326bb05d1b2d8b7071f`.
    Protocol SHA-256 is
    `475866512b9c0d7c12cab51e32fa36efdc7be6922c09ea7d8b2a069f521f2a11`
    and the exact 2,113-task schedule SHA-256 is
    `94da8f2fbcef3f16e74e729442c8c65bdd0c75be0cb400c4ebee66336b4dcb2d`.
    Before invocation require a clean commit containing ADR-0335, the exact
    source closure, the retained ADR-0334 qualification journal, and absence of
    `experiments/results/fresh-action-width-nonreplay-exhaustive-teacher-v1.jsonl`.
    Then invoke only the public no-clobber wrapper once:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -c "from pontius.fresh_action_width_nonreplay_teacher import run_and_retain_adr0334_nonreplay_exhaustive_teacher as run; result = run(); print(type(result).__name__)"
    ```

    The JSONL journal, not terminal stdout, is the authority. Every later arm
    requires the prior post-`fsync` receipt. Any completed, consumer-rejected,
    nested-reversal, unexpected-exception, or infrastructure stop closes the
    campaign without resume, deletion, overwrite, alternate backend, or retry.
    Retain the exact bytes and source-seal a solver-free result owner before a
    direct mechanism or transfer value. Do not call the private executor,
    reinterpret the synthetic 6,616,076-byte control as research, or promote a
    teacher knee directly into production action width.
54. ADR-0336 permanently closes that one-shot owner. Never invoke
    `run_and_retain_adr0334_nonreplay_exhaustive_teacher` again. Preserve
    `experiments/results/fresh-action-width-nonreplay-exhaustive-teacher-v1.jsonl`
    as exactly 8,027,171 bytes and 2,115 LF-terminated records with SHA-256
    `3f20b204bca428c2b9e99266688709b6aba65de2f2bff3d38c6f523828c94444`.
    Rebind only through
    `verify_adr0336_nonreplay_teacher_result_artifact`; its semantic result is
    `e4347dbfc6663a636572199f11dcad517fe715d062dcee022566419382f193b0`.
    Width three is the first inherited maximum-plus-mean gate pass and median
    knee; width four is the first width with no certified-positive lower-regret
    context. Do not use either diagnostic as a direct-mechanism selection,
    divide campaign wall by 2,113 as latency, or rank plateau members. Before
    any new value, source-seal only the additive ADR-0331 direct mechanism with
    its exact 376-call schedule and complete 378-record synthetic journal. Do
    not call the closed ADR-0329 entries or construct transfer/action state.
55. ADR-0337 passes that source-only boundary. Its source SHA-256 is
    `80ba2426399eb3329d33c0d69d58bc71112bdcc5a2608be5a3e8b4b49bfc0c9c`,
    protocol SHA-256 is
    `13a0e96490abe656db545e64491e395855308b5b25fc17dc97457036502c7820`,
    and schedule SHA-256 is
    `887e2b7c5d642adefe9cd2c976eaded3f69a1be204ae517264e8b9d8d4fd20b9`.
    The graph contains 2,097 arms and 6,543 possible transitions; the exact
    adaptive path permits 376 public calls and a completed journal has 378
    records. Before invocation require a clean commit containing ADR-0337,
    verify the exact ADR-0334 panel and ADR-0336 teacher artifact, and require
    absence of
    `experiments/results/fresh-action-width-nonreplay-closed-finite-block-greedy-v1.jsonl`.
    Then invoke only the public no-clobber wrapper once:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -c "from pontius.fresh_action_width_nonreplay_greedy import run_and_retain_adr0336_nonreplay_closed_finite_block_greedy as run; result = run(); print(type(result).__name__)"
    ```

    The JSONL journal, not terminal stdout, is the authority. Every next call
    requires the prior observation's post-`fsync` receipt and the dynamically
    selected incumbent. Any completed, consumer-rejected, numerical-rejected,
    unexpected-exception, or infrastructure stop closes the campaign without
    resume, deletion, overwrite, alternate backend, or retry. Retain the exact
    bytes and source-seal a solver-free result owner before transfer, capacity,
    preparation, action, or production-width evidence. Do not call the real
    wrapper from a dirty tree, invoke either closed ADR-0329 entry, treat the
    synthetic width three as research, or divide command wall by 376 as live
    latency.
56. ADR-0338 permanently closes that one-shot owner. Never invoke
    `run_and_retain_adr0336_nonreplay_closed_finite_block_greedy` again.
    Preserve
    `experiments/results/fresh-action-width-nonreplay-closed-finite-block-greedy-v1.jsonl`
    as exactly 1,437,835 bytes and 378 LF-terminated records with SHA-256
    `8e53b303ddfce361458a725ab1167249b34c5c2321c954ccfa92b7bba07daa4b`.
    Rebind only through
    `verify_adr0338_nonreplay_greedy_result_artifact`; its semantic result is
    `7317ff19c02efe9fa084802120289286c2a6eb1885b816087ba58b710ca27353`.
    All 376 calls were accepted and raise width three is the smallest width
    passing all five development gates. It is not a universal ladder,
    transfer confirmation, production width, capacity result, or action. The
    artifact contains no elapsed field; never derive latency by dividing a
    command wall by 376. Before any new value, derive the exact ADR-0323
    transfer seed only from source commit
    `b4339f33dec768052208b102ad8a9f510666f40d`, then source-seal a value-free
    96-context transfer pool and all-prior semantic non-overlap proof. Do not
    construct a transfer qualifier, invoke a solver, or enter preparation or
    action code at that source checkpoint.
57. ADR-0339 passes that source checkpoint. Preserve
    `fresh_action_width_transfer_structures.py` at canonical-LF SHA-256
    `6704084f2bddfac2d58e3066b9844bc0fc633346bf3b00a7034ccc9b154e622f`
    and its adjacent seal at
    `592287bb426ac17e16bb2bf7666016d8e4fafb616c12d6c283094abc4b8e0f69`.
    The protocol SHA-256 is
    `50ae2d077929f654bbfd386afb60fa7c12b8f45ccafdb9eb562515dda8e2745c`;
    the source-commit-derived stream retains the first 96 admissible contexts
    after 478 raw candidates, with pool SHA-256
    `4b72d0196d31b029c55e64a3425fc610f46e4128d38782b09e45e8643c8da083`.
    The 13,587 prospective subsets are structural work, not calls or latency.
    The exact 1,244-context finite non-overlap evidence hashes to
    `74739a76d3350e7be5a8bf7eb807f577ba7a5bfe7beaaa69536f3f7ffb45c610`.
    Do not construct or invoke a transfer consumer from this source owner.
    Next source-seal a separate candidate-blind qualifier with complete-
    universe then anchored-width-two order, the unchanged ADR-0323 classifier,
    first-16 stop, append-and-fsync receipts, typed terminal failures,
    solver-free target-panel rebinding, and a prospective no-clobber path.
    Before value, freeze that every unchanged conjunct must pass to confirm
    width three; any partial pass rejects unrestricted transfer and cannot be
    rewritten as an abstention policy. The ADR-0337 real wrapper remains
    permanently closed and must never be invoked again.
58. ADR-0340 passes the transfer-qualification source checkpoint without a
    consumer or solver call. Preserve
    `fresh_action_width_transfer_qualification.py` at canonical-LF SHA-256
    `6233c8161084c0bab07f902c8d6033e8aa555d51ace552017ca97f53fe402bd5`,
    its adjacent seal at
    `0fd8a115705772b9a11fc5d3a77f0e0c613bbd966f94dc01cfa6066d22727711`,
    protocol SHA-256
    `d3b39c8cb99825844bbe4210fc235eee12e8f525e69bbd55187007d6361154f8`,
    and schedule SHA-256
    `d54267fc71c165637fbf1ea73c7e29be7a6d0471a01396ca788099625087b680`.
    The schedule is exactly 192 tasks over ADR-0339 pool
    `4b72d0196d31b029c55e64a3425fc610f46e4128d38782b09e45e8643c8da083`.
    The prospective `-text` artifact path is
    `experiments/results/fresh-action-width-transfer-qualification-v1.jsonl`.
    Require a clean commit containing ADR-0340 and exact absence of that path,
    then invoke only the public no-clobber wrapper once:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -c "from pontius.fresh_action_width_transfer_qualification import run_and_retain_adr0339_transfer_qualification as run; result = run(); print(type(result).__name__)"
    ```

    The JSONL bytes, not terminal stdout, are authority. Every next arm requires
    the preceding post-`fsync` receipt. Target, exhaustion, ambiguity, nested
    reversal, consumer rejection, unexpected exception, or infrastructure
    failure closes the campaign without deletion, overwrite, resume, alternate
    backend, or retry. Preserve the exact bytes and source-seal a solver-free
    real result; construct a real target panel only for the exact first-16
    target stop. Do not open a transfer teacher/direct value in the same
    checkpoint. A mean-only, 14-of-16, or other later partial width-three pass
    remains rejection of unrestricted transfer.

59. ADR-0341 retains the sole transfer-qualification invocation from source
    commit `e1c6c14630e3e8cf72be0a40db80b85eed549b58`. Never invoke
    `run_and_retain_adr0339_transfer_qualification` again. Preserve the exact
    `experiments/results/fresh-action-width-transfer-qualification-v1.jsonl`
    bytes: 378,108 bytes, 96 records, SHA-256
    `e6f25068d8362fa2bc9b40fe292506371d6d808b4696bb83c09f75ad3c8d812a`.
    The solver-free terminal has campaign SHA-256
    `444289ef7f1964b194255a03564ae1628ff207e2eff3cff678755978023f8b78`,
    terminal SHA-256
    `3770f8dc40a9edbbac5afc7d5986ceb36e566ce552eb35921ead0b644c5575f8`,
    94 accepted one-call evidences, 47 complete contexts, 16 qualifiers, 31
    nonqualifiers, complete invocation accounting, and exact `target_reached`.
    The identity-only target panel SHA-256 is
    `dd46e2917757ae0ba02e620f6298be8eac7629e92db573cea291bf1160b157bf`.

    Preserve `fresh_action_width_transfer_qualification_result.py` at
    canonical-LF SHA-256
    `ed54b5676073ec019f3b544515f5a89c07b68eff5a7158b771a2d7914d83da55`,
    its adjacent seal at
    `a23559fb20e8e3ea6ff23ebfa20618022f3f7072cdc5e53f30b33eaaa0b08653`,
    focused test at
    `6c79d648fdd88668d826d8ce0c1bb404b337f1294fdaf47ae83b6010b38e13ee`,
    and result protocol at
    `45b8e3ae8cadd93afa9ab60c8b4f18bd977ff35e38130ac0e35def81352fedc7`.
    Reproduce only through the read-only owner:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -c "from pontius.fresh_action_width_transfer_qualification_result import verify_adr0341_transfer_qualification_result_artifact as verify; result = verify(); print(result.journal.stop_reason.value, result.panel.digest)"
    ```

    This result qualifies a panel; it does not confirm width three. Before any
    confirmation value, source-seal a separate owner that applies the frozen
    ADR-0338 context-local width-three mechanism without width reselection and
    preserves the all-conjuncts gate. Do not reinterpret a mean-only, 14-of-16,
    or other partial pass as unrestricted transfer.

60. ADR-0342 passes the source-only transfer-confirmation checkpoint. Preserve
    `fresh_action_width_transfer_confirmation.py` at canonical-LF SHA-256
    `ec24d1710598003e7e76ff9b1062829107e28ba1766e680bec2a1411b736e202`,
    its adjacent seal at
    `06ba1396e3ce826249188d0279266907e716188e0bef07f88cea0fe8de39336c`,
    focused test at
    `35a85de35d8cde7e6ab8504ad0bcb024b5bf2b850697a63874c18c0a7808add4`,
    protocol SHA-256
    `0f1cc9b42a4d4c4a394acca073dee64dcd245f6496d89a3bf708dbdfecad4fa9`,
    and schedule SHA-256
    `53389f770aa3fa0773d003df11a48858a1cb42ee166cb44bba74dda42805d7fe`.
    The 32 ADR-0341 full/width-two arms are retained prior evidence and must not
    be called or counted again. The prospective schedule contains exactly 126
    context-ordered width-three candidate calls. The real `-text` path is
    `experiments/results/fresh-action-width-transfer-confirmation-v1.jsonl`
    and must be absent before launch.

    From one clean commit containing ADR-0342, invoke only the public
    no-clobber wrapper once:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -c "from pontius.fresh_action_width_transfer_confirmation import run_and_retain_adr0341_transfer_confirmation as run; result = run(); print(type(result).__name__)"
    ```

    The JSONL bytes, not stdout, are authority. Every later candidate requires
    the preceding post-`fsync` receipt. A confirmed, all-conjunct rejected,
    typed consumer-rejected, numerical, unexpected, or infrastructure terminal
    is final: preserve it without deletion, overwrite, resume, backend change,
    or retry. Do not invoke any closed qualification, teacher, or direct-
    mechanism wrapper. Source-seal a solver-free real result before interpreting
    the outcome. Only exact passage of all five unchanged conjuncts can confirm
    unrestricted width-three transfer; partial passage remains rejection and
    cannot authorize abstention, width reselection, blueprint training, or
    production integration.

61. ADR-0343 permanently closes that public owner and retains its only real
    invocation. Preserve
    `experiments/results/fresh-action-width-transfer-confirmation-v1.jsonl`
    at exactly 445,731 newline-terminated bytes, 128 records, and SHA-256
    `c7fb4405177d46f751812c957e5a503c3430fb48427456e333a871e486969130`.
    Do not delete, overwrite, resume, or invoke the wrapper again. Preserve
    `fresh_action_width_transfer_confirmation_result.py` at canonical-LF
    SHA-256
    `c1a74d810cc82ec97d2f769e019a2afd5585351377192990ca37c3cb79de5bc6`,
    its adjacent seal at
    `8f7725b4266ade14c1b2ae067b8302475911582ccca9199757260b51f84af544`,
    focused test at
    `1f989e32c79e26fd1b02e23a6456b21af8f7c6dd7277c9724c83e47ba7b7f405`,
    the ADR-0343-closed owner test at
    `6b48a6d872466a98a2616619776f35933fc6998db2c10c2c30387ded6f7f9d71`,
    and result protocol at
    `69a97f9d91f9acbe90a2661c58b397edbee3b79af02a604b07b391c4aa63268c`.

    Rebind the result only through
    `verify_adr0343_transfer_confirmation_result_artifact`. Its exact terminal
    is `completed_confirmed`: 126 accepted one-call arms, 16 complete contexts,
    and all five unchanged conjuncts pass. Report this only as unrestricted
    transfer of the frozen context-local width-three mechanism on the untouched
    reduced panel. Do not report one fixed ladder, derive latency by dividing
    the campaign wall by calls, or claim responder raises, full width, earlier
    streets, production integration, or poker strength. Next preregister the
    responder-raise and full-width capacity gates separately; blueprint
    training still requires its remaining trainer, checkpoint, abstraction,
    and operational slice-audit seals.

62. ADR-0344 source-seals the legal responder-raise sequence-form keystone.
    Preserve `legal_river_continuation.py` at SHA-256
    `4c8f57f259415ece30b12add42243b65a30d3320924b469209e2d94a68064250`,
    `responder_raise_semantics_keystone.py` at SHA-256
    `201b937d351d50e072d4f8f00268b3242855abd8f32c468b3d5870fad1682978`,
    its config at SHA-256
    `5a9899ea0ced855cdb6fa30183ccab9b3235470603d7d45f688355eac15dcafd`,
    and its two controls at SHA-256
    `0c6a6cb7d63aa7c25ec3570605c8886ceaf780dc9fff3433d52091dc5edc396e`
    and
    `06b5eb1a490694adc6b0a61f7590fdb26bf01e6183943bcc4792b59ced0acba6`.
    The prospective result path is
    `experiments/results/responder-raise-semantics-keystone-v1.json` and must
    be absent before launch.

    After committing the complete ADR-0344 source boundary, invoke only:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m pontius.responder_raise_semantics_keystone
    ```

    The exclusive-create artifact is authority. Preserve a pass, semantic or
    numerical rejection, exception, or infrastructure failure without delete,
    overwrite, parameter change, or retry. A pass authorizes only a separately
    preregistered h4 legal responder-raise coefficient differential. It does
    not establish reopening, row capacity, selector stability, multiway
    closure, latency, action quality, or poker strength. The reporting-only
    prediction ledger cannot select or reinterpret the result.

63. ADR-0345 permanently closes the ADR-0344 public runner after its sole
    clean invocation. Never invoke
    `pontius.responder_raise_semantics_keystone` again. Preserve
    `experiments/results/responder-raise-semantics-keystone-v1.json` as exactly
    7,400 bytes with SHA-256
    `a7cbb0efca87ad3bf9e2a2105d10aa137daf68a763b68518d68e893bfc74be11`
    and the path-specific `-text` rule.

    Rebind only through
    `verify_adr0345_responder_raise_semantics_result_artifact`. Preserve its
    source at canonical-LF SHA-256
    `757c593081d78e7823cfa680b782385ddbb33badfe70d8ef907478c1ce8791b7`,
    adjacent seal at
    `58a0fa199904d9cefba553e9788b95e55d23318b2913aa53653566193b9b416f`,
    test at
    `847245475a6a5ae398b8b83c6b25b62fabc5a01c650eb49802c0a2d4e4d2adb0`,
    and protocol at
    `e459d7ea2d2e9ea6f63918fa1fac7985f7411a3d4f07e3935d897a11a45e0793`.

    Report the pass only as one deterministic legal-semantics and finite-
    algebra witness. The complete teacher objective is
    `2.333333333333333`; the generated lower value differs upward by less than
    `1e-15`, inside the frozen tolerance. Never quote the 0.791-second command
    wall as action latency. Next source-seal a separate h4 legal responder-
    raise coefficient differential. Keep row capacity, selector stability,
    multiway closure, off-tree observations, and full-width capacity in their
    own gates. Forecast 2 remains open and unscored.

64. ADR-0346 source-sealed the legal h4 coefficient differential. Preserve the
    config at SHA-256
    `e511be50649a2c1c401948d31c1245f9df890f31aceb4f53a8ef4c63c62803bc`,
    the independent Fraction oracle at
    `8d70297ab80055c5c77bdeefb82ff6cde817f6c57876059783046669b3a6945a`,
    its control at
    `5b0aeba06437386156451a7d66687b0274a14abbb138f96f8b2c1ee2bb84a330`,
    the prospective runner at
    `e800aa343803c27744172404e1351e564e2817ce357c59bb602bbd6cb357caee`,
    and its control at
    `cbf1386a05fe53efbe6db4b7a0b9bdb3681a015980f4bb36b60a89979dd02502`.

    The result path
    `experiments/results/legal-responder-raise-h4-coefficient-differential-v1.json`
    was absent at clean source commit `5164ad7` and was invoked only with:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m pontius.legal_responder_raise_h4_coefficient_differential
    ```

    ADR-0347 now permanently closes that command. Never invoke
    `pontius.legal_responder_raise_h4_coefficient_differential` again. The
    exclusive-create artifact is authority. The
    fixture is h4 on the ADR-0345 public tree, not full private width. The
    Fraction teacher must remain free of subject/evaluator imports. Never
    recompute the responder selector at an endpoint or turn exact chance mass
    into a claim of dyadic structure without the power-of-two denominator
    check. A pass opens only a responder-row-growth preregistration; do not
    report direct traversal wall as response capacity or action latency.

65. ADR-0347 retains the sole clean legal h4 coefficient result. Preserve
    `experiments/results/legal-responder-raise-h4-coefficient-differential-v1.json`
    as exactly 100,710 bytes with SHA-256
    `6dcbf8e44f1c3b2bd54694e0c1f6898082e71373846933bfaa116bc4f2c27255`
    and the path-specific `-text` rule.

    Rebind only through
    `verify_adr0347_legal_h4_coefficient_result_artifact`. Preserve its source
    at canonical-LF SHA-256
    `4c67ce1e724e6196a1fff6d7d6312c7a117fd9ff5ea47c8e82d7a1f21e8e1547`,
    adjacent seal at
    `53e597b3483efc6ba2bbc3ca4a5dace8a6422eebac6ba549bb43017dcc9f3113`,
    test at
    `36794d5ccc17d3d5a18efb9834a6fbfbb2f91d25679a8d0f9fdf98ecc8dc64fe`,
    and protocol at
    `88ff8d65f25d34cd99225d23c5cb3689b72a414e79863e8eb0fccd40565acdd6`.

    Report the pass only as one finite h4 coefficient identity: six rows by 32
    coordinates, 36 endpoint comparisons, and zero retained error. The
    solver-free owner rederives exact zero-sum and gain-row algebra but does
    not replay the legal tree. Never quote the 1.743-second campaign as row
    capacity or action latency. Next preregister responder-row growth on the
    unchanged h4 fixture; keep selector stability, preparation-bank recovery,
    multiway closure, off-tree actions, and full-width capacity separate.

66. ADR-0348 source-seals the legal h4 responder-row growth audit. Preserve
    `experiments/configs/legal-responder-raise-h4-row-growth-v1.json` at
    SHA-256
    `da6c4067cedd71504eb0c5e0c5034ffdf731839d2df71d33f0a07d12bd25cd99`,
    `one_seat_row_growth_audit.py` at SHA-256
    `f5c6f80bc46a6b8887f9241998207bbb8828fff136a6f1a389475b1aead349eb`,
    its control at
    `14d6bb929af5167d336f8abc724558e2710748efc8b1fc905bb8c120f3a2ed1e`,
    the prospective runner at
    `89f425d5bf5ddca7a1e2ef0eb343d0f34b1ce39cc9b7ee31a3fc4364905b9e58`,
    and its control at
    `14c698b38669aeeb624bf844494468856f37eb80c8278ccde6035415f59ac591`.

    The result path
    `experiments/results/legal-responder-raise-h4-row-growth-v1.json` must be
    absent at the clean source commit. After committing the complete ADR-0348
    boundary, invoke only:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m pontius.legal_responder_raise_h4_row_growth
    ```

    Preserve its first exclusive-create terminal without deletion, overwrite,
    parameter change, alternate backend, or retry. The observer must call the
    unchanged production generator once; the Fraction audit consumes only its
    already selected tapes. Report complete response signatures, generated
    rows, conditioning, oracle work, semantic retained bytes, convergence, and
    bounded infrastructure walls. Never call either wall action latency or
    infer strategy quality. A literal pass authorizes only a separately
    preregistered selector-stability successor; preparation-bank recovery,
    multiway closure, off-tree actions, full-width capacity, action emission,
    and strength remain separate gates.

67. ADR-0349 permanently closes the ADR-0348 public runner after its sole
    clean invocation. Never invoke
    `pontius.legal_responder_raise_h4_row_growth` again. Preserve
    `experiments/results/legal-responder-raise-h4-row-growth-v1.json` as
    exactly 50,963 bytes with SHA-256
    `eb35843218741096f214a6c341a0762b8f1cca09a81a1fdce1db21eaa9fc60b8`
    and the path-specific `-text` rule.

    Rebind only through
    `verify_adr0349_legal_h4_row_growth_result_artifact`. Preserve its source
    at canonical-LF SHA-256
    `b300b5b5a022a698c7bce2c77a99212da272ecaa50e1964eac76a21c392add53`,
    adjacent seal at
    `7edb4892fe5ea6130180650927575dfcad86e86ad44336d081e152c94df4b3ac`,
    test at
    `05372ca684bb5deb2a4386cbc948ce4c03d07b3215bd26b9476dc935ef04760d`,
    and protocol at
    `d7184b60f9fd3c46ae761864ed28d59cd9e91af0b03eab950aa74fb67aafbd89`.

    Report the pass only as one finite h4 row-growth and infrastructure result.
    Two inherited rows converge in one master and zero rows are generated. The
    responder tape changes at the candidate but has exact gain zero; never call
    that selector stability. Never quote the 0.686-second subject wall as
    action latency or the exact `27/64` finite objective as poker quality.
    Next preregister a selector-window policy family, tape/tie semantics,
    fixed-tape exact checks, activation/envelope directions, and walls before
    opening values. Keep preparation-bank recovery, multiway closure, off-tree
    actions, full-width capacity, action emission, and strength separate.

68. ADR-0350 source-seals the legal h4 selector normal-fan audit. Preserve
    `experiments/configs/legal-responder-raise-h4-selector-window-v1.json` at
    SHA-256
    `08d8d8d9975edd8147065893ef81f0f597fe1a687a5c5a5905fe36e2fec9f866`,
    the selector-free direction compiler at
    `0542639a491417be78415ee3019e864d256ff460adae5ae1ddc75f9e4dceaf88`,
    the exact selector oracle at
    `5156d8155e017c44587f900a126ddcb67f13b701e643550ad668cee06d5e2e3f`,
    the exact fan mapper at
    `03ddc731c1d866b728d24b999be92df89d203a14e4872da5c88a9298fa20deee`,
    the Float64 window primitive at
    `81189f1e4d3639e44f87fe6234ec8ec3872451de53356ee137cb84bdb860aa4b`,
    the engineered controls at
    `f8d24a6323eec4aeba0a7b72d0f47142dc61a62628a9aac4f6a6786cf253e975`,
    the prospective runner at
    `9a252e13bc51b3f713a05c9b4444ad40c544797b5119c1d97d7bb85dd693f070`,
    and its control at
    `3ce5a2a92b339048ef187a6ec695ee9547b2837627262f09b7ebfe16fa55ae46`.

    The result path
    `experiments/results/legal-responder-raise-h4-selector-window-v1.json`
    must be absent at the clean source commit. After committing the complete
    ADR-0350 boundary, invoke only:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m pontius.legal_responder_raise_h4_selector_window
    ```

    Preserve its first exclusive-create terminal without deletion, overwrite,
    parameter change, alternate backend, schedule repair, or retry. Report
    exact `fixed` / `tie_unresolved` / `switched` measures and tie points;
    never break an exact tie with a tolerance. Total-function identity gates
    certificates; reachable-support identity is reporting-only. Require the
    four old-breakpoint differentials, fixed-tape value identities, maximum
    gain-row envelope with master direction `z >= row`, engineered controls,
    exactly 136 production selector calls, and bounded infrastructure walls.
    Never call those walls action latency. A literal pass authorizes only a
    separately preregistered h4 selector-stable affine integration gate;
    preparation-bank recovery, multiway closure, off-tree actions, full-width
    capacity, action emission, and strength remain separate.

69. ADR-0351 permanently closes the ADR-0350 public runner after its sole
    clean invocation. Never invoke
    `pontius.legal_responder_raise_h4_selector_window` again. Preserve
    `experiments/results/legal-responder-raise-h4-selector-window-v1.json` as
    exactly 1,493,122 bytes with SHA-256
    `7a1d08f1245b93b2a880f92af6c737677b7cd85b5c59a05205a8263adafcbee7`
    and the path-specific `-text` rule.

    Rebind only through
    `verify_adr0351_legal_h4_selector_fan_result_artifact`. Preserve its source
    at canonical-LF SHA-256
    `9ed770a532cb2a665dbe6b01c2385f66b763ab02d86750e9b44642a5df894d9a`,
    adjacent seal at
    `34f02b4c9c80d56c6bd9ea2c78b9599f890110e5fafcea634d41a3e432b2383b`,
    test at
    `780f8686f3e44c52179b04d85b68215fc6a09ae3f67fb003bdb41591179c719b`,
    and protocol at
    `12e95e2ca5adfd14dc5557101a099dbefbffa20062e079bf18d3db14d59c6f0f`.

    Do not repeat the artifact's nominal all-pass decision. Retain the exact
    map but report four reachable source-tie/nonzero-window violations,
    `corrected_certificate_pass: false`, and no successor authority. All four
    acting-player sections have tie-unresolved measure one. The responder
    source endpoints are `15/19`, `139/163`, `1`, and `1`; two switch and two
    end at total-only tie points. Never call either infrastructure wall action
    latency or treat these breakpoints as quality.

    Preserve `selector_window_v2.py` at canonical-LF SHA-256
    `78af151aaaf6dfdc69ce7f2fba141a16fc76edfef4b43be4732380140b03f644`
    and its test at
    `0c801113496a06377a4ce192d0aa3beafb642a7c0040edffc3baa5a114ff7999`.
    The v2 rule requires every source margin to clear its semantic reserve
    before slope is examined; ties and reserve overlaps return zero. The v1
    helper remains byte-preserved only for provenance and is closed to new
    certificate consumers. Next preregister a tie-aware active-row-envelope
    recovery. Keep preparation-bank recovery, multiway closure, off-tree
    actions, full-width capacity, action emission, and strength separate.

70. ADR-0352 source-seals the legal h4 tie-aware affine-envelope recovery.
    Preserve the config at SHA-256
    `9dae1dbe1c93e1952699f7a2bc11f3837bed2e2cf0296e0bafc5c5b87dceff3f`,
    exact active-row oracle at
    `ee922a9cf15be88cc2566a8c0b45496dd0db6cb5856b738f52ecbaf7429c6695`,
    typed adapter at
    `3982179667e185148560b8fb3f2e882f29e6ab185c7295be882beab3f0f364c5`,
    prospective runner at
    `99b7db5e7ee49d35769fb4f41a72ef251469df8439ac52a924b7edefcdf4f28d`,
    oracle/adapter control at
    `00c5f5c736ec5c327f479c715f558560d81707abd15134ac1190b7582b1c4aec`,
    and runner control at
    `dd691d01b271dfabb599a68df338602286e304287f35b7ae6fc1fc0a8709d92e`.

    The result path
    `experiments/results/legal-responder-raise-h4-tie-aware-affine-v1.json`
    must be absent at the clean source commit. After committing the complete
    ADR-0352 boundary, invoke at most once:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m pontius.legal_responder_raise_h4_tie_aware_affine
    ```

    Retain the first exclusive terminal. Never change the active-set
    definition, four inherited directions, dyadic schedule, v2 dispatch,
    identity authority, pruned-tape schema, envelope direction, walls, or
    claims after seeing it. Every tied source must have zero v2 windows and
    retain all exact local-maximizer total tapes. Every identity comparison
    must carry both source and current pruned tapes. Require the exact maximum
    envelope and master direction `z >= row`; reachable identity remains
    reporting-only.

    Pre-seal alternate-tape endpoint equivalence was development
    reconnaissance and is excluded from every gate. A pass is same-fixture
    integration evidence only and may authorize only a fresh untouched
    confirmation preregistration. It is not full-width capacity, action-clock
    latency, action emission, decision quality, or poker strength.

71. ADR-0353 permanently closes that one-shot owner. Never invoke
    `pontius.legal_responder_raise_h4_tie_aware_affine` again. Preserve
    `experiments/results/legal-responder-raise-h4-tie-aware-affine-v1.json`
    as exactly 961 bytes with SHA-256
    `7608abd221114ed6143aa7fbf9af510a09024442f85fd8f4f3f5ed53e036f652`.
    Rebind it only through
    `verify_adr0353_legal_h4_tie_aware_affine_result_artifact`; the retained
    terminal is `reject_legal_h4_tie_aware_affine_integration` after the exact
    local-maximizer Cartesian product exceeded the frozen 256-tape per-sample
    bound. The artifact contains no completed section, exact cardinality, row,
    adapter mode, envelope, or target gate vector. Do not raise the bound,
    retry, infer where it fired, divide the 64.651-second infrastructure wall
    into latency, or treat the rejection as a quality prior. Before any new h4
    value, source-seal a factorized total active-set identity and compact exact
    affine-row quotient with exhaustive-equivalence, product-overflow,
    repeated-actor total/reachable, engineered-tie, legacy-breakpoint, and
    distinct-row fail-closed controls. A separate prospective diagnostic must
    own the next h4 result path.

72. ADR-0354 is a source-only seal. Verify its mechanism boundary with:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m unittest `
      tests.test_exact_directional_face_oracle_seal `
      tests.test_exact_directional_face_oracle `
      tests.test_tie_semantics_conformance `
      tests.test_exact_tie_aware_affine_envelope `
      tests.test_selector_window_v2 `
      tests.test_exact_selector_fan
    ```

    The source-seal SHA-256 is
    `6e7ace7dff1785954905a2f87fde4ff8913559281de9a2a99e987fbb89d2fc3b`
    and its protocol SHA-256 is
    `cfd37e22b4e3e09321b20f6d6f3bef93f4b8fd35af6ecd13d2166ba3aee7dabf`.
    Expect two independent lexicographic passes, separate total-function and
    reachable-support cardinalities, exact integer bit-length telemetry, a
    linear logical-work ledger, and exactly zero materialized response tapes.
    The 100,000 default is an explicit-tree-node bound and 256 is a normal-fan
    piece bound; neither limits active-face cardinality.

    Do not run an h4 target from this checkpoint and never invoke the closed
    ADR-0352 owner. Before the next value, commit a separate preregistration
    with the four inherited directions and schedule, a new exclusive result
    path, both cardinality columns, both extrema, complete work/seam fields,
    typed compact-state and fan-piece failures, bounded infrastructure walls,
    and the source-only claims boundary. Preserve its first terminal without
    retry. The full-width capacity preflight remains a separate lane.

73. ADR-0355 source-seals the legal h4 directional-face diagnostic. The
    prospective result path
    `experiments/results/legal-responder-raise-h4-directional-face-v1.json`
    must be absent at the clean source commit. Verify the source boundary with:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m unittest `
      tests.test_legal_responder_raise_h4_directional_face `
      tests.test_exact_directional_face_oracle `
      tests.test_tie_semantics_conformance `
      tests.test_exact_directional_face_oracle_seal
    ```

    The config SHA-256 is
    `5305d2fa43b386d1a7b58bf2dc96943d581013e80ad5f9966438bf11b3289fa7`,
    the prospective runner canonical-LF SHA-256 is
    `c7196eb26081c136da37b6ef0098c9ad9813bc78205ab4ea2f6b491a93848c5f`,
    and its control canonical-LF SHA-256 is
    `42ce8ff836b0eb6aae57cb87ac4ae113ab85982e3b6a3e6c82edf478867f891f`.
    Confirm the result path is absent, commit all source and documentation,
    and require a clean worktree. Then invoke exactly once:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m pontius.legal_responder_raise_h4_directional_face
    ```

    Retain the first terminal without retry. Do not alter the four inherited
    directions, 17-point schedule, two-pass face semantics, total/reachable
    columns, factor/work/seam schema, 100,000 explicit-tree-node guard, 256
    fan-piece guard, 180-second subject wall, 240-second analysis wall, 16 MiB
    scientific payload ceiling, 32 MiB result ceiling, or claims
    boundary after target work begins. No target cardinality, crossing, tie,
    slope, or cell-count expectation is a gate. Never invoke the closed
    ADR-0352 owner, and do not interpret the result as action-clock, full-width,
    multiway, decision-quality, or strength evidence.

74. ADR-0356 retains the sole ADR-0355 invocation from clean commit
    `5331d0a6e142a97be10678d59e76aa7f1cc9a63e`. **Never invoke that runner
    again.** Preserve
    `experiments/results/legal-responder-raise-h4-directional-face-v1.json`
    byte-for-byte: 3,888,072 bytes, SHA-256
    `5e3473639e67e0a24e21f3c516239c35d4bb7ccb17a6de8d74a5320428af1b49`.
    Its exact `.gitattributes` entry is
    `/experiments/results/legal-responder-raise-h4-directional-face-v1.json -text`;
    never remove that byte-preservation rule.
    Verify the retained result with:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m unittest `
      tests.test_legal_responder_raise_h4_directional_face_result
    ```

    The result owner canonical-LF SHA-256 is
    `2bef9c0130b45010d34729abfb31a2cf634ed46cfbee9eeba90b4b76be251765`
    and its protocol SHA-256 is
    `42d97ff763bed912393cc6a92f9167565637fa46288730ffab1e5f30582a340a`.
    Report the pass only as one finite h4 development diagnostic: eight
    sections, 136 schedule calls, 164 face observations, two crossings,
    104,976 maximum total cardinality, two maximum reachable cardinality,
    147,418 logical work units, and zero materialized tapes. Never divide the
    59-second campaign into action or solve latency. Next preregister a
    separate tie-aware affine integration owner using fan-as-ray and
    face-as-point authority; require untouched confirmation after any
    same-fixture development pass and keep full-width capacity independent.

75. ADR-0357 source-seals the factorized tie-aware affine integration
    mechanism; it is not a legal h4 result. Verify the source boundary with:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m unittest `
      tests.test_factorized_tie_aware_affine `
      tests.test_tie_semantics_conformance_v2 `
      tests.test_factorized_tie_aware_affine_seal
    ```

    The source protocol SHA-256 is
    `8a5b053e1b792ae879f5d10cd8c7614ae69e33fe2033db0d0337388375e83d6a`.
    Do not edit ADR-0354's historical tie registry or directional-face source,
    and never invoke the closed ADR-0352 or ADR-0355 owners. No legal h4 target
    invocation is authorized by this step. First preregister a separate
    exclusive owner with an absent result path, fixed four-direction/eight-
    section workload, typed singleton/tie dispatch, complete integration
    schema, and bounded laboratory walls. Any later same-fixture pass remains
    development evidence and cannot substitute for untouched confirmation,
    full-width capacity, action latency, decision quality, or strength.

76. ADR-0358 preregisters the exclusive legal h4 factorized-affine owner. Its
    config SHA-256 is
    `e77f22b739ac714d952f0575735b5705c0b17913cf7930705dfb1588f307263c`.
    Before invocation, verify the result path is absent, the tree is clean, and
    the source boundary passes:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m unittest `
      tests.test_legal_responder_raise_h4_factorized_affine
    Test-Path experiments/results/legal-responder-raise-h4-factorized-affine-v1.json
    git status --short
    ```

    Then invoke exactly once:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m pontius.legal_responder_raise_h4_factorized_affine
    ```

    Retain the first terminal without retry or gate repair. Never invoke the
    closed ADR-0352 or ADR-0355 owners. Interpret a pass only as inspected
    same-fixture h4 development integration; it is not untouched confirmation,
    full-width capacity, action or solve latency, decision quality, or poker
    strength. The subject wall is the sum of eight live builds and must never
    be divided into a per-solve or action-clock comparison.

77. ADR-0359 permanently closes the ADR-0358 owner and retains its exact
    259,550-byte result, SHA-256
    `301f7c9c865b8ae2cfcc39e6c6ebca32db68d4fd15e8e6255976ace587c35eea`.
    Never invoke `pontius.legal_responder_raise_h4_factorized_affine` again.
    Verify the result authority only through:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m unittest `
      tests.test_legal_responder_raise_h4_factorized_affine_result
    ```

    The read-only result protocol SHA-256 is
    `8d78d45a45e9988950747e40d4ee04c3e71176bdde32ef39c275d54aecb7ebda`.
    Report exactly 22 passing gates, four factorized source ties, four positive
    v2 singletons, 12 fan rows, ten compact envelope pieces, 28 point-face
    observations, and zero tapes/actions. The 18.152-second subject total is
    eight same-fixture h4 builds, not per-solve or 15-second action latency.
    Preserve the authenticated-only limitation for non-source face internals,
    non-quotient fan-row residuals, and the reproduced-section digest. The next
    target requires a fresh value-unopened population and a separately sealed
    complete-schema confirmation owner.

78. ADR-0360 source-seals the fresh population and successor contract without
    opening any confirmation target value. Verify only the structural boundary:

    ```powershell
    $env:PYTHONPATH = "src"
    & $python -B -m unittest `
      tests.test_legal_h4_factorized_affine_confirmation_population
    ```

    The seed SHA-256 is
    `6bae36a91d135a16f8a4484a44a5c5fa775215eebf15e9e74626ef52767eef0e`,
    protocol SHA-256 is
    `c75ef3f8eb5011775049080b98302fec0d3f6c72bf6cf58bacfa1146fe0752fa`,
    and the exact 4,991-byte population SHA-256 is
    `902f714a11df4c861312e782b10e08ccdc62c3254b7515bdb1f73caddef32988`.
    No invocation is authorized here. Preserve the first four contexts, the
    three regret histories plus audited row-growth direction recipe, all 32
    future sections, complete raw fan/face/residual schema, zero tape
    materialization, and all-or-nothing interpretation. Do not import or replay
    ADR-0358, inspect a direction endpoint in scratch, skip or reseed a context,
    or treat the future laboratory wall as action-clock evidence. Next create a
    separate preregistered exclusive owner and absent result path before any
    target call.

79. ADR-0364 permanently closes the ADR-0363 full-width-capacity v1 owner and
    retains its exact 798-byte typed-failure artifact, SHA-256
    `ff1c757fb1c388c239ca3c7fdacad15bffa6ee62e00b882827ffb5626f40a906`.
    Never invoke `pontius.full_width_river_capacity_preflight` again. Verify
    only the retained bytes and bounded interpretation:

    ```powershell
    $env:PYTHONPATH = "src;."
    & $python -B -m unittest `
      tests.test_full_width_river_capacity_preflight_result
    ```

    The terminal says `GetProcessMemoryInfo failed` and contains no control or
    target payload, so it is not a representation, memory, contraction, or
    latency result. The earlier incorrect shell commit check did not enter
    Python; the corrected command invoked the owner exactly once. A successor
    must use explicitly typed Win32 signatures, bind v1's config/runner/result,
    use a new absent exclusive path, and earn a clean source seal before any
    v2 target invocation.

80. ADR-0365 source-seals the additive typed-telemetry v2 owner. The v2 result
    path must remain absent through this commit. Verify the complete source
    boundary without invoking the target:

    ```powershell
    $env:PYTHONPATH = "src;."
    & $python -B -m unittest `
      tests.test_windows_process_memory `
      tests.test_full_width_river_capacity_preflight_v2
    Test-Path experiments/results/full-width-river-capacity-preflight-v2.json
    git status --short
    ```

    The config SHA-256 is
    `23cb6ea4521dc26c5fc1c3962574443b7a1d1b841f9e54c03355f9af9a58ff58`.
    After the source commit is clean and only then, invoke exactly once:

    ```powershell
    $env:PYTHONPATH = "src;."
    & $python -B -m pontius.full_width_river_capacity_preflight_v2
    ```

    Retain the first terminal without retry. Never invoke v1. The typed ABI and
    512 MiB cross-reader sampling allowance supply telemetry confidence only;
    they do not enlarge resource caps, action time, or claims. Any v2 terminal
    remains one representation/warm-leaf diagnostic, not a complete solve,
    action, decision-quality result, or strength claim.
