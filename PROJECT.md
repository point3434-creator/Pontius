# Project Charter

## Objective

Build and measure a six-player no-limit Texas hold'em research agent that uses
an offline blueprint, public-belief search, neural continuation values, adaptive
actions and trees, and deadline-aware allocation of computation. The primary
deployment objective is maximum marginal chip-valued decision quality per
additional millisecond of attributable online workstation compute, subject to
one hard 15,000 ms wall-clock response deadline whenever the controlled seat
acts on a Ryzen 9 9900X, 64 GB host-memory, RTX 5080 workstation.

## Game contract

- Six-player cash-game no-limit Texas hold'em.
- 100 big-blind starting stacks.
- No rake and no ante in the first full-game implementation.
- Exact legal betting, all-in, side-pot, and card-removal rules.
- Each controlled action has one continuous 15,000 ms wall-clock response
  deadline, including a fixed 1,000 ms synchronization and emission reserve.
  It starts when an observed event makes the controlled seat the actor and
  includes every pause and work interval through emission. A later controlled
  action receives a new response wall.
- Opponent think and transport idle before that clock starts do not consume the
  response wall. Agent work during that opportunity, including prior-street and
  opponent-turn speculation, is online preparation rather than free time. It
  may benefit a decision only through an exact provenance-bound artifact hit.
  Report all preparation spent, credited, missed, invalidated, and aborted
  separately; concurrent CPU/GPU work is elapsed wall time rather than summed
  device time.
- Pontius banks computed artifacts, not unused milliseconds. Preparation never
  extends the live 15-second response deadline unless a future host exposes a
  separate rules-defined time bank. Offline training cost remains separate.
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
  source digest and two exact fresh seeds. ADR-0302 seals the resulting
  value-free 48-context representative family and separate 96-context
  qualification pool with zero counterpart among 604 maintained prior
  contexts. ADR-0303's candidate-blind runner reaches 24 qualifiers after a
  contiguous 60-context prefix and seals the final qualified panel. ADR-0304
  rejects v3 at the frozen qualified aggregate-recovery gate: both families
  pass maximum and mean normalized-loss limits, but the qualified family
  recovers only 80.05% of the available raw-chip sizing gain versus the 90%
  floor. ADR-0305 prospectively freezes capacity-filling pot-odds v4: retain
  every v3 action under the same seven-raise ceiling, then fill every unused
  slot by exact-rational farthest-point coverage rather than another fitted
  fraction. ADR-0306 now freezes its exhaustively validated, bounded-work
  source at SHA-256
  `37824e44b7793b10b081957fc8be387bdca5c565b4bfe2386ca13f7e1c785c8b`.
  ADR-0309 now seals its 48-context representative and separate 96-context
  qualified-A and qualified-B structures before every value. They are mutually
  unique and have no counterpart in the finite 748-context ADR-0291--0304
  inventory. ADR-0310 rejects the ordered qualification before candidate
  evaluation: A reaches 24 qualifiers after 73 contexts and passes its teacher
  controls, but B's full-integer LP at context 21 fails native primal
  verification. A is provisional, no final A/B panels exist, and every
  representative and candidate value remains unopened. V1-v4 are parked and
  no action abstraction is integrated. The next eligible work is a separately
  preregistered candidate-independent native-simplex robustness audit, not a
  v4 retry. ADR-0311 now freezes that audit before corpus or compiler source:
  one known regression, 48 exact micro LPs, 128 fresh candidate-free sizing
  LPs, five exact representations, and native/HiGHS-DS/HiGHS-IPM arms with
  unit-specific independent bounds. ADR-0312 now seals the pure compiler, 48
  micro inputs, 64 fresh contexts, 177 bases, and 885 exact representations.
  The fresh contexts have zero counterpart in the finite 988-context inventory
  through ADR-0310. ADR-0313 now seals the runner and result-schema source at SHA-256
  `cfb127960e3d501a156f14d22244ecd122874b74fefb668685f9a721503ade16`
  with exact micro enumeration, original-coordinate primal/dual mapping,
  feasible behavioral sizing reconstruction, outward certificates, complete
  failure observations, frozen runtime/options, and the 2,655-call schedule.
  ADR-0313's one-shot complete audit invocation is now retained by ADR-0314:
  all 2,655 arms completed, all 885 HiGHS dual-simplex and all 885 IPM arms
  passed, and native recorded 36 failures. The literal conjunction still
  rejects because its known-regression predicate confused unique maximum row
  215 with the complete above-allowance row set. HiGHS remains ineligible.
  ADR-0315 source-sealed the separate artifact-only correction and synthetic
  multi-row/unique-maximum controls before retained-evidence access. ADR-0316's
  temporally separated exact-digest reanalysis now passes with zero failures
  and makes HiGHS dual simplex eligible only for a later prospective adapter
  evaluation. No adapter, runtime latency, quality result, specialized solver,
  consumer migration, or v4 revival is authorized.
- ADR-0317 separates the compact reduced-sizing LP from the one-seat behavioral
  master. The former still invokes rejected native simplex and is next eligible
  only for a prospectively source-sealed, semantically certified HiGHS
  dual-simplex adapter. The latter already uses HiGHS and accounts for only
  0.063%-0.151% of complete measured time in the two retained six-target
  ledgers; persistent or specialized master work remains parked until a fresh
  certified v2 ledger crosses a 5% perfect-solver materiality trigger. This is
  a scheduling boundary, not an adapter, speedup, or candidate result.
- ADR-0318 implements and canonical-LF source-seals the reduced-sizing
  HiGHS-DS adapter behind exact normalized behavioral reconstruction and an
  outward-rounded trusted-box certificate. Its 11 controls are analytic or
  bounded toys only. A failure-complete, source-sealed 177-canonical-base
  runner must be committed before any retained adapter result; no v1 consumer,
  v1-v4 candidate owner, or action value is connected.
- ADR-0307 supersedes ADR-0282's cumulative-street allowance. The authoritative
  hard boundary is 15,000 ms of continuous wall-clock time per controlled
  action, including a fixed 1,000 ms reserve. Older 5-250 ms targets remain
  superseded historical context.
- Belief/topology preparation and speculation before the action clock are
  measured online work. Only an exact semantic artifact hit may be credited to
  a decision, and credited preparation never enlarges its live remainder.
- ADR-0308 implements that contract in the additive `ActionClockLedger`,
  `PreparationBank`, and `LegalDecisionSpineV2`. The exact spine derives the
  current public-state identity, rejects late construction after our turn has
  begun, and forces a legal fallback at the work or wall boundary. The older
  cumulative-street spine remains a historical reproduction control. V2 is not
  yet connected to the complete-hand replay or a live host, and no preparation
  hit has established decision-quality value.
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
  This campaign ceiling is separate from the 15-second action-response wall and
  from online preparation accounting.
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
