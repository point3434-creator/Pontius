# Roadmap and Checkpoint Gates

This file is the compact forward map. The generated [STATUS.md](STATUS.md)
names the latest accepted decision; the immutable records under
[`docs/decisions`](docs/decisions) retain the complete experimental history.

## C0-C2: Research contract and exact solver laboratory

**Status:** Passed as foundations.

The repository has reproducible extensive-form controls, exact utilities and
best responses, NashConv, CFR-family solvers, frozen configurations, causal
holdout discipline, and explicit fallbacks. These checkpoints remain the
reference layer; they are not evidence that full hold'em is solved.

## C3: Reduced multiplayer hold'em

**Status:** Active at the six-player h32 river boundary.

Completed subgates include:

- exact two-to-six-player river controls with per-seat unilateral deviation
  gains and separate coalition-stress diagnostics;
- public-tree quotienting, factorized compatible-card beliefs, low-rank
  showdown structure, clean-fringe deltas, and shared-topology GPU residency;
- exact incremental response certification against an immutable blueprint;
- allocator lifecycle control for two resident h32 belief contexts; and
- a prepared 15-second street ledger: one resident warm step plus two exact
  atomic certificates and a one-second emission reserve on two frozen trials
  ([ADR-0166](docs/decisions/ADR-0166-prepared-street-fits-two-atomic-certificates-after-one-warm-step.md)).

The current strategy-identification result is narrower. Public-node admissible
radii exist, but one-step soft DCFR captures only 4.87% of the positive value in
a frozen two-direction library. Regret vertices expose about 20.54 times as much
aggregate certified value, while the available regret-mass proxy fails to rank
that opportunity ([ADR-0178](docs/decisions/ADR-0178-regret-vertices-expose-soft-generator-weakness-but-not-a-live-selector.md)).
This supports “generator, at least”; it does not authorize a live selector or a
global strategy-quality claim.

**Next gate:** preregister a small deep-horizon diagnostic on frozen panel
targets. Compare immutable-envelope certification at off-clock 32-64-step
checkpoints. Material certified value would support amortized deep solving;
another microscopic result would add evidence about contract geometry without
proving opportunity exhaustion. The experiment must preserve immutable anchors,
frozen outcome-neutral gates, numerical GPU identity, explicit memory ceilings,
and the blueprint fallback.

**C3 exit gate:** on fresh reduced multiplayer regimes, a precommitted online
rule must improve certified value under the complete wall-clock and memory
contract without weakening any per-seat cap. Exact offline opportunity alone
does not pass.

## C4: Optimized runtime

**Status:** Partly explored inside C3; not passed as a checkpoint.

Build the production-oriented flat/native runtime, cancellation and emission
path, latency distributions, and memory accounting. Optimized results must
match the reference numerically under the frozen protocol and improve real
decision traces without strategy regression.

## C5: Pluribus-style control agent

Build a complete legal six-max control agent with a fixed abstraction,
blueprint, ranges, fixed-depth resolving, off-tree handling, and fail-closed
fallbacks. The resolver must improve the blueprint in reduced exact games and
against a frozen evaluation league.

## C6: Neural blueprint and leaves

Add river-to-flop teachers and policy/value/action/uncertainty models only after
the exact runtime and decision contract are stable. Pass on root-strategy harm
at equal latency, not value-function mean-squared error alone.

## C7: Adaptive public-belief search

Add dynamic width/depth, continuous action proposals, residual solving, and
street/player specialization. Adaptive search must Pareto-dominate fixed search
at multiple budgets with no material rare-branch vulnerability.

## C8: Cache and speculation

Add range-aware caches, topology/embedding reuse, pondering, and preemptible
future-state work. Future decisions must improve without degrading current-
decision p95 latency or reusing a strategy across incompatible beliefs.

## C9: Learned value-of-computation scheduler

Train only after a richer workload demonstrates enough attainable value to pay
for inference and training. A learned scheduler must beat the best transparent
heuristic on hidden games and full traces; otherwise retain the heuristic.

## C10: Full evaluation

Require exact reduced-game results, adversarial responders, complete cross-play
matrices, paired-deal confidence intervals, latency and memory profiles, and all
major ablations before a defensible final report.
