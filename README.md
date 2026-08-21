# Pontius

Pontius is a research project for building an adaptive successor to a
Pluribus-style six-player no-limit Texas hold'em agent. The objective is useful,
certified strategy improvement under a hard wall-clock boundary, not iteration
count.

The current research spine is an exact six-player river control at 32 hands per
seat (`h32`). It combines factorized beliefs, shared public topology, resident
GPU solving, unilateral-deviation certificates, and an immutable-blueprint
fallback. On two frozen prepared contexts, one resident warm step and two exact
atomic certificates fit inside a 15-second ledger with a one-second emission
reserve. That is a systems-capacity result, not a deployment or broad strategy-
quality claim.

## Current checkpoint

See the generated [STATUS.md](STATUS.md) for the current decision and immediate
work. [PROJECT.md](PROJECT.md) defines the contract, [ROADMAP.md](ROADMAP.md)
defines checkpoint gates, and [RUNBOOK.md](RUNBOOK.md) records the supported
verification environments.

## Quick start

The original exact CPU laboratory still uses only Python's standard library.
Set `PYTHONPATH` to `src`, then run its smoke test:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m pontius.experiment --game kuhn2 --solver lcfr --iterations 20000 --report-every 2000
```

The current wide GPU evidence path additionally requires the pinned SciPy,
CuPy, and CUDA runtime described in [RUNBOOK.md](RUNBOOK.md). Use that path for
the complete regression suite and never treat a reproduction of an already
opened result as fresh evidence.
