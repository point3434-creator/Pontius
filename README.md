# Pontius

Pontius is a research project for building an adaptive neural successor to a
Pluribus-style six-player no-limit Texas hold'em agent. The deployment objective
is strategy quality under a hard wall-clock budget, not iteration count.

The first checkpoint is intentionally small: a reproducible exact-game
laboratory with Kuhn poker, exact best responses, NashConv, vanilla CFR, and
Linear CFR. It is the executable reference against which later C++ and CUDA
implementations will be checked.

## Current checkpoint

See [STATUS.md](STATUS.md) for verified capabilities and immediate work. See
[PROJECT.md](PROJECT.md) for scope and [ROADMAP.md](ROADMAP.md) for checkpoint
gates.

## Quick start

The reference laboratory has no third-party runtime dependencies. Set
`PYTHONPATH` to `src`, then run:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m pontius.experiment --game kuhn2 --solver lcfr --iterations 20000 --report-every 2000
```

If Python is not on `PATH` in Codex, use the bundled interpreter documented in
[RUNBOOK.md](RUNBOOK.md).

