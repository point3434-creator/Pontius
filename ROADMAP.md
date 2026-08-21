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

The active strategy result identifies generator direction as the weak link.
Regret vertices expose about 20.54 times the value of one-step soft DCFR, while
the regret-mass proxy fails to rank that opportunity
([ADR-0178](docs/decisions/ADR-0178-regret-vertices-expose-soft-generator-weakness-but-not-a-live-selector.md)).
The subsequent 8/32/64 ladder rejects ordinary depth as the next architecture:
the best deep endpoint rises only 1.256x over step 8 and captures 2.97% of the
retained two-direction oracle. Purification adds 4.99x over raw average-64 but
is concentrated in one target and still trails the regret vertex
([ADR-0184](docs/decisions/ADR-0184-ordinary-deep-dcfr-plateaus-while-purification-remains-direction-sensitive.md)).

The fresh causal direction/opportunity screen replicates the generator
diagnosis: soft DCFR captures only 5.47% of its bounded three-family oracle,
while the regret vertex captures 99.20%. An immutable-blueprint best-response
vertex is directionally redundant and adds no material value. Regret mass and
minimum action gap both fail as free opportunity selectors. A charged
cap-radius probe captures 95.41% of the target-best denominator but is unstable
across targets and unavailable before certificate work
([ADR-0186](docs/decisions/ADR-0186-fresh-vertices-replicate-generator-weakness-but-no-free-selector-transfers.md)).

**Open gate:** preregister a narrow online-feasible opportunity-acquisition
rule on fresh contexts. Keep the regret vertex fixed, charge every probe and
final certificate, preserve the one-second emission reserve, and emit the
immutable blueprint whenever evidence or time is incomplete. The observed
order-extreme concentration and cap-radius signal may motivate the hypothesis,
but neither is a live rule until it transfers prospectively. Modern DCFR
variants remain deferred because changing the soft trajectory does not yet
solve opportunity location.

The first engineering subgate is frozen in
[ADR-0187](docs/decisions/ADR-0187-preregister-selector-stable-affine-certificate-differential.md):
before any fresh trial, one additive selector-stable affine certificate must
match the accepted exact verifier across all 36 retained regret-vertex blocks.
Only an exact primitive whose conservative seat-0 ledger fits may advance to
the prospective street rule.

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
