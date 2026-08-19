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

## Continuation protocol

1. Read `PROJECT.md`, `STATUS.md`, and the relevant decision records.
2. Confirm the active checkpoint and working-tree status.
3. Run the fast test suite before modifying correctness-critical code.
4. Make one measurable change.
5. Verify against the reference and record the experiment configuration.
6. Update `STATUS.md` and any decision whose evidence changed.
