# Project Charter

## Objective

Build and measure a six-player no-limit Texas hold'em research agent that uses
an offline blueprint, public-belief search, neural continuation values, adaptive
actions and trees, and deadline-aware allocation of computation. The primary
deployment objective is the best attainable strategy quality within one hard
15,000 ms wall-clock budget per street on a Ryzen 9 9900X, 64 GB host-memory,
RTX 5080 workstation.

## Game contract

- Six-player cash-game no-limit Texas hold'em.
- 100 big-blind starting stacks.
- No rake and no ante in the first full-game implementation.
- Exact legal betting, all-in, side-pot, and card-removal rules.
- One shared 15,000 ms wall-clock budget for all charged agent work on each
  street. The clock does not reset for another action on the same street.
- Opponent think and transport idle do not consume that allowance. Every
  interval of agent work does: initial hand-state construction,
  observed-action processing, foreground or background computation, legality
  and candidate selection, certification, fallback preparation,
  street-transition processing, and emission. Concurrent CPU/GPU work is
  charged by elapsed wall time rather than summed device time.
- Cold-cache and warm-cache results are reported separately.

## Current decision-boundary contract

- The active systems control is a prepared six-player h32 river decision.
- The additive exact-game control is ADR-0290's complete explicit-deal
  reference loop. It joins ADR-0286's six-seat integer-chip legal decision
  spine to future-blind one-seat cards, five complete opponent axes with hard
  card disjointness, exact rational public-action updates, a digest-bound
  deliberately weak policy and fallback, showdown, and settlement. It does not
  compute normalized full-width marginals and is not a calibrated range,
  trained full-game blueprint, action abstraction, or strategy-producing
  resolver.
- ADR-0292 rejects the first fixed pot-fraction action lattice at its frozen
  reduced sizing-quality gate before complete-hand integration. Its exact
  legality/projector code is a parked control, not the action abstraction of
  the reference loop. A successor must use a preregistered
  development/confirmation split and may not tune to the opened failure.
- ADR-0294 also rejects the dyadic successor before replay integration because
  its untouched panel contains only five informative contexts rather than
  eight. Favorable conditional loss and recovery diagnostics do not waive that
  power gate. Candidate-blind evaluation-power design must precede v3.
- ADR-0296 rejects the first candidate-blind pool qualifier when its second
  replication yields 11 rather than 12 material contexts. Its owned runner now
  makes batch identity and stop-after-target state semantic evidence. Batch 2
  values remain unopened; a richer reduced game must precede v3.
- ADR-0297 preregisters the smallest richer game: four private types per seat
  with the same one-bet tree and candidate-blind controls. Pool construction is
  separated from values. ADR-0298 seals all three structural pools and exact LP
  dimensions. ADR-0299 passes all three replicated width-four yield/work gates
  and authorizes one v3 preregistration on fresh dual panels, not integration.
- ADR-0300 preregisters collision-repair v3 before source code: preserve v2's
  distinct two-pot action and use three-halves pot only when two-pot wastes its
  slot on a mandatory anchor. ADR-0301 now freezes the exhaustively validated
  source digest and two exact fresh seeds. No fresh structure, sizing value,
  v3 value, or integration exists yet.
- The authoritative hard boundary is 15,000 ms of wall-clock time per street,
  including a fixed 1,000 ms reserve for synchronization and action emission.
  Older 5-250 ms targets are superseded historical context and must not govern
  any current or future acceptance gate.
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
  This campaign ceiling is separate from the shared 15-second street ledger.
- A speculative cache cannot trust a byte hash first produced by the same
  invocation that consumes it. Population, external hash sealing, and live
  replay are separate prospective stages. Until a later clean config pins the
  complete seed-manifest bytes, every generated entry is unavailable and the
  immutable blueprint remains the completed fallback.
- Every semantic input used to assemble a cached result must be inside the
  externally trusted byte boundary. A cached-row successor may not accept a
  caller-supplied payoff scalar or another numerically plausible substitute.
- A canonical campaign result becomes trusted only after separately bounded
  data and completion-seal phases have built, serialized, exclusively staged,
  published without clobbering, reread, byte-compared, hashed, and passed the
  shared campaign deadline. An exclusive publishing lock keeps partial or late
  states unconsumable; a failed call preserves an unsealed or lock-marked
  diagnostic. Consumers must use the verified loader and never infer trust from
  canonical-path existence.

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

### Optimization and semantic-type default

A minimization `lower_bound` must come from a dual/Lagrangian certificate with
conservative residual and rounding treatment; a feasible primal objective is
reported as a primal diagnostic or upper bound. Report `U - L` with both
sources and units explicit. Raw solver agreement is not a certificate.

Numerically equal tolerances with different meanings remain separate config
fields and nominal types. Relative reversal, absolute reversal, absolute
optimality gap, selector margin, affine intercept identity, epigraph separation,
resident primal residual, and negative-reach allowances may not share aliases.
Dimensionless probability feasibility may not scale with a chip-valued payoff
cap. Acting and payoff roles are likewise explicit at every cross-payoff
boundary. A root-only affine formula may not be applied to a nonroot public node
merely because the source intercept still matches.

The project is for offline research, simulation, and environments that
explicitly permit automated agents.
