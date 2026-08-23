# Pontius

Pontius is a research project for building an adaptive successor to a
Pluribus-style six-player no-limit Texas hold'em agent. The objective is useful,
certified strategy improvement under a hard wall-clock boundary, not iteration
count.

The current research spine is an exact six-player river control at 32 hands per
seat (`h32`). It combines factorized beliefs, shared public topology, resident
GPU solving, unilateral-deviation certificates, and an immutable-blueprint
fallback. The authoritative target is one shared 15-second wall-clock budget
of charged agent work per street, including a one-second emission reserve; it
pauses during opponent/transport idle and does not reset for another agent
action on the same street. On two frozen prepared contexts, one
resident warm step and two exact atomic certificates fit that ledger. This is a
systems-capacity result, not a complete-street, deployment, or broad strategy-
quality claim.

ADR-0290 carries ADR-0288's explicit-deal reference loop, built on ADR-0286,
across five complete 1,225/1,081/1,035/990 opponent axes on every street. Exact
rational public-action likelihoods update only their actor, hard card
disjointness is retained, board reveals filter every axis, and the unchanged
four-street hand remains inside its cumulative 15-second ledgers. The immutable
policy is deliberately passive and untrained; normalized full-width marginals,
scalable value contraction, action abstraction, a credible full-game blueprint,
resolver candidates, and strength evidence remain unconnected.

ADR-0292 rejects the first fixed action-sizing lattice before it reaches that
loop. Its exact legal lattice and rational off-tree projector pass all 45,456
three-chip states and 60,732 transitions, but the frozen reduced river panel
has only one informative context and v1 recovers none of that context's
full-over-minimum/all-in gain. The code remains a parked oracle and baseline;
any successor requires a fresh development/confirmation preregistration.

ADR-0294 rejects the dyadic successor on confirmation-panel power before
replay integration. V2 conditionally recovers 94.51% of the available gain and
halves v1's aggregate normalized loss, but only five of 24 deterministic
contexts are informative versus the frozen minimum of eight. Both candidates
remain parked; the next work is candidate-blind sizing-power diagnostics, not
another post-outcome fraction adjustment.

ADR-0296 rejects the subsequent candidate-blind pool qualifier: its first seed
reaches 12 material contexts, but the second reaches only 11 within the frozen
96-context cap. No candidate was evaluated and the third batch remains value-
unopened. A follow-up over-open incident is recorded explicitly; the maintained
successor now owns batch identity and stop state rather than trusting a caller
loop. The next work must test a richer reduced sizing game before v3.

ADR-0297 now freezes that next test without opening a pool or value. It changes
only the private-type width from three-by-three to four-by-four, retains the
candidate-blind full-versus-minimum/all-in comparison, and adds exact LP-work
ceilings. ADR-0298 seals three structural pools and their digests in a separate
value-free module before the owned runner invocation.

ADR-0299 records a clean pass: the three batches reach 12 qualifiers after 23,
24, and 32 openings, with numerical, diversity, teacher, and pivot gates clean.
The result authorizes only preregistration of one v3 mechanism and fresh dual-
panel evaluation; none of these development panels may fit or confirm v3.

ADR-0300 now freezes collision-repair v3 before source implementation. It
retains v2's two-pot action whenever distinct and substitutes three-halves pot
only when two-pot collides with a mandatory legal anchor. Source, seeds, and
fresh panels remain unopened and unimplemented at this boundary.

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
CuPy, and CUDA runtime described in [RUNBOOK.md](RUNBOOK.md). The repository-
local Windows CUDA DLL bundle is discovered automatically when Pontius is
imported; the environment variable is now an explicit override, not a required
shell ritual. Use the pinned path for the complete regression suite and never
treat a reproduction of an already opened result as fresh evidence.
