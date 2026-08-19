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

## Continuation protocol

1. Read `PROJECT.md`, `STATUS.md`, and the relevant decision records.
2. Confirm the active checkpoint and working-tree status.
3. Run the fast test suite before modifying correctness-critical code.
4. Make one measurable change.
5. Verify against the reference and record the experiment configuration.
6. Update `STATUS.md` and any decision whose evidence changed.
