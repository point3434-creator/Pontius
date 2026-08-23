# Pontius

Pontius is a research project for building an adaptive successor to a
Pluribus-style six-player no-limit Texas hold'em agent. The objective is useful,
certified strategy improvement under a hard wall-clock boundary, not iteration
count.

The current research spine is an exact six-player river control at 32 hands per
seat (`h32`). It combines factorized beliefs, shared public topology, resident
GPU solving, unilateral-deviation certificates, and an immutable-blueprint
fallback. The authoritative target is maximum marginal chip-valued decision
quality per millisecond of attributable online compute, subject to one hard
15-second continuous response wall whenever the controlled seat acts and a
one-second emission reserve. Prior-street and opponent-turn computation may be
credited only through an exact matching prepared artifact; it never extends
the live response deadline. Earlier cumulative-street results remain historical
systems controls, not deployment or broad strategy-quality claims.

ADR-0308 installs that contract as `ActionClockLedger`, `PreparationBank`, and
`LegalDecisionSpineV2`. Exact event boundaries now start each action wall before
state-transition work, preparation claims are one-use and bound to the exact
public state plus semantic/source provenance, and late candidates fail closed
to a legal fallback. This is verified resource accounting, not evidence that
speculation improves play or that a complete decision fits the live host.

ADR-0290 carries ADR-0288's explicit-deal reference loop, built on ADR-0286,
across five complete 1,225/1,081/1,035/990 opponent axes on every street. Exact
rational public-action likelihoods update only their actor, hard card
disjointness is retained, board reveals filter every axis, and the unchanged
four-street hand remains inside its historical cumulative-street ledgers. The
immutable policy is deliberately passive and untrained; normalized full-width
marginals, scalable value contraction, action abstraction, a credible full-game
blueprint, resolver candidates, and strength evidence remain unconnected.

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

ADR-0300 freezes collision-repair v3 before source implementation. ADR-0301
now records its exhaustively validated exact-legal source and immutable digest:
v2's two-pot action remains whenever distinct, and three-halves pot substitutes
only on a mandatory-anchor collision. Two exact fresh stream seeds are sealed;
ADR-0302 now seals their value-free 48-context representative family and
separate 96-context qualification pool. ADR-0303's candidate-blind full/narrow
screen reaches 24 unambiguous qualifiers after 60 contexts and seals the final
panel before candidate values. ADR-0304 now rejects v3 before integration: its
normalized-loss gates pass on both families, but the qualified panel recovers
only 80.05% of the available raw-chip full-over-minimum/all-in gain versus the
frozen 90% floor. V1, v2, and v3 remain parked; a successor requires a new
prospective mechanism and wholly fresh panels. ADR-0305 now freezes that
successor before code: v4 retains v3's set and uses exact-rational maximin
pot-odds filling to spend otherwise unused slots under the same seven-raise
ceiling. Three exact fresh streams and two separately gated qualified
replications are committed prospectively. ADR-0306 now freezes the value-free
v4 source after exhaustive legality, v3-inclusion, exact-capacity, projection,
and bounded-work checks. ADR-0309 now seals the value-free 48/96/96 fresh
structures, their raw attempt counts, and zero overlap with the finite prior
inventory. ADR-0310 rejects v4's ordered qualification: A reaches 24
qualifiers after 73 contexts, but B's full-integer LP at context 21 fails the
native solver's primal verification. No final panel or candidate value is
accepted, and the source remains disconnected from replay, blueprint, the
convex master, and resolving. The next gate is a prospectively preregistered
candidate-independent native-simplex robustness audit, not a v4 retry.
ADR-0311 now freezes that audit's exact micro and fresh sizing corpora,
metamorphic representations, backend options, independent bounds, and kill
criteria before any corpus source or new LP value. ADR-0312 now seals the pure
  unit-tagged compiler, 48 micro inputs, 64 fresh contexts, 177 bases, and 885
  exact representations without invoking a backend or opening an optimum. The
  ADR-0313 runner is now source-sealed with typed failure-complete observations,
  exact micro enumeration, original-coordinate sizing reconstruction, outward
  certificate plumbing, frozen environment/options, and the exact 2,655-call
  schedule. ADR-0314 now retains the complete 2,655-observation result. Every
  HiGHS dual-simplex and IPM arm passes, while native records 36 failures. The
  literal gate rejects because it over-specified the known regression's entire
  failing-row set instead of its recorded unique maximum row 215. ADR-0315 now
  source-seals the artifact-only correction and synthetic controls before any
  authoritative retained-evidence read. ADR-0316's temporally separated
  exact-digest reanalysis passes every corrected conjunct and makes HiGHS dual
  simplex eligible only for a later prospective replacement-adapter
  evaluation. No adapter, runtime or quality result, v4 revival, or consumer
  migration is authorized.

ADR-0317 separates two solver classes that ADR-0316's direction had blurred.
The rejected native simplex remains in the compact reduced-sizing oracle, so
the active source boundary is a certified canonical HiGHS dual-simplex adapter
for that oracle. The one-seat behavioral master already uses HiGHS; its
retained solve calls consume only 0.063%-0.151% of complete measured ledgers,
so persistence and specialization are parked under a prospective 5%
perfect-solver materiality trigger. No solver source, result, consumer, or
candidate is changed by ADR-0317.

ADR-0318 now source-seals that canonical sizing adapter. HiGHS-DS is an
untrusted proposer: exact normalized policy evaluation supplies a feasible
behavioral lower bound, and an outward-rounded trusted-box certificate supplies
the upper bound. Eleven analytic, bounded-teacher, corruption, source, and
runtime controls pass. No sealed 177-base validation, legacy consumer change,
candidate value, or production replacement exists yet.

ADR-0319 now source-seals the failure-complete canonical validation runner
without opening a retained base result. Its immutable schedule counts exactly
one public HiGHS-DS proposal for each of 177 canonical bases: 48 exact micro
LPs use exact vertex/certificate authority, while 129 sizing LPs use ADR-0318
and a second ADR-0313 reconstruction. Nine unsealed controls pass; the next
boundary is the single sealed invocation, not a consumer or action-width claim.

ADR-0320 retains that one authorized invocation. All 177 observations pass
with exactly one public proposal each, including 48/48 micro and 129/129 sizing
gates; the largest sizing certificate interval is `8.50e-11` chips. This opens
only a separately preregistered certified-v2 reduced-sizing consumer. No
consumer, six-player action-width mechanism, complete-decision latency, or
poker-strength result exists yet.

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
