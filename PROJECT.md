# Project Charter

## Objective

Build and measure a six-player no-limit Texas hold'em research agent that uses
an offline blueprint, public-belief search, neural continuation values, adaptive
actions and trees, and deadline-aware allocation of computation. The primary
deployment objective is the best attainable strategy quality at each wall-clock
decision budget on one Ryzen 9 9900X, 64 GB host-memory, RTX 5080 workstation.

## Initial game contract

This is the original charter contract. Its 5-250 ms budgets remain useful for
the early exact laboratories, but they are not the active h32 decision ledger.

- Six-player cash-game no-limit Texas hold'em.
- 100 big-blind starting stacks.
- No rake and no ante in the first full-game implementation.
- Exact legal betting, all-in, side-pot, and card-removal rules.
- Initial online budgets: 5, 20, 50, 100, and 250 milliseconds.
- Cold-cache and warm-cache results are reported separately.

## Current decision-boundary contract

- The active systems control is a prepared six-player h32 river decision.
- The hard boundary is 15,000 ms, including a fixed 1,000 ms reserve for
  synchronization and action emission.
- Belief/topology preparation and immutable-blueprint construction occur before
  the decision clock and are reported separately from charged work.
- The frozen measured schedule permits one resident warm step, deterministic
  candidate construction, and only certificates that the deadline guard can
  finish before the reserve.
- Every candidate is compared with the same immutable blueprint anchor. Safety
  does not compose across atomic candidates; any union requires exact
  recertification.
- If no independently certified candidate completes in time, emit the immutable
  blueprint. A late result is unusable.
- Cold construction, warm work, certificate work, persistent GPU-pool bytes,
  physical-free memory, and the emission reserve stay separate in every ledger.
- Every bounded multi-target campaign carries one shared monotonic deadline.
  The runner atomically checkpoints before each frozen target or arm, admits
  the unit only when its complete preregistered bound still fits, and stops
  before any later work or label if either the unit or campaign wall is crossed.
  This campaign ceiling is separate from the 15-second decision ledger.
- A speculative cache cannot trust a byte hash first produced by the same
  invocation that consumes it. Population, external hash sealing, and live
  replay are separate prospective stages. Until a later clean config pins the
  complete seed-manifest bytes, every generated entry is unavailable and the
  immutable blueprint remains the completed fallback.

[ADR-0166](docs/decisions/ADR-0166-prepared-street-fits-two-atomic-certificates-after-one-warm-step.md)
records the current capacity evidence. It does not authorize deployment, claim
a population latency distribution, or establish that the certifiable edits
capture material strategy value.

## Primary measurements

- Exact NashConv and unilateral deviation gains in tractable games.
- Root-strategy harm relative to an exact or dense reference.
- Quality improvement over the blueprint versus wall-clock latency.
- Median and p95 decision latency.
- Nodes touched, peak host/GPU memory, model calls, and data movement.
- Full-game restricted-best-response gain and seat-adjusted cross-play EV.

Iteration count and value-function mean-squared error are diagnostic metrics,
not final success metrics.

## Initial non-goals

- Claiming that the project has solved six-player hold'em.
- Claiming superiority to Pluribus without credible direct evidence.
- Opponent exploitation before a robust baseline exists.
- Distributed training, a graphical interface, or live-site integration.
- Neural models or GPU kernels before exact reference workloads are verified.

## Evidence and dissent protocol

Consequential reviews use: verdict, confidence, supporting evidence, opposing
evidence, largest unknown, cheapest falsifying experiment, kill criterion, and
recommendation. Claims are labeled Known, Reproduced, Observed, Hypothesis, or
Rejected. Tests and measurements outrank either collaborator's preference.

Every ambitious component retains a fallback:

```text
learned scheduler -> heuristic scheduler
adaptive tree     -> fixed tree
neural leaves     -> blueprint continuation
predictive/DCFR   -> LCFR
GPU traversal     -> CPU reference
online resolving  -> blueprint strategy
```

### GPU numerical-identity default

For a Float64 artifact re-derived through GPU or parallel sparse reductions,
semantic identity is numerical by default. Freeze the applicable ceilings
before execution and report digests as diagnostics. The repository defaults
are maximum accumulator and policy-probability error `1e-12`, mean
information-set policy total variation `1e-13`, and maximum quality-vector
error `1e-10`; stricter experiment-specific tolerances may be preregistered.
No tolerance may be introduced or relaxed after observing a result.

A SHA-256 or other bitwise gate remains authoritative for immutable input and
configuration provenance, literal serialized-object identity, immediate
restore/re-export, or an experiment explicitly testing deterministic future
execution. It is not the default semantic-equivalence gate for an independently
recomputed GPU trajectory. Exact discrete fields, schemas, action identities,
and combinatorial work counts remain exact gates unless a preregistration says
otherwise. The executable constants and fail-closed purpose check live in
`pontius.evidence_protocol`.

The project is for offline research, simulation, and environments that
explicitly permit automated agents.
