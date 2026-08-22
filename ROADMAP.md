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

The first online-feasibility engineering subgate now passes. The additive
selector-stable affine certificate matches the old exact verifier to at most
`1.36e-15` across 36 retained regret-vertex blocks, and all six conservative
seat-0 ledgers fit the 15-second boundary. It captures 48.80% of the frozen
three-family bounded oracle under its preregistered half-radius rule
([ADR-0190](docs/decisions/ADR-0190-selector-stable-affine-certificate-is-exact-and-fits-retained-street-ledgers.md)).
The slowest retained ledger has only 338.90 ms of boundary headroom after the
one-second reserve, so the result validates the primitive but not a latency
distribution.

The first fresh live-rule trial passes on all four precommitted contexts. Fixed
acting seat 0 produces four deadline-eligible affine-certified candidates with
at least 3.80 seconds of boundary headroom, and post-emission exact teachers
agree to `1.67e-16`. Certified value is highly heterogeneous: one target carries
86.45% of the total and the target spread is 565x
([ADR-0192](docs/decisions/ADR-0192-fixed-seat0-affine-rule-emits-four-fresh-certified-candidates-before-deadline.md)).

The unchanged other-extreme replication also passes. Acting seat 5 emits four
fresh, exact, deadline-eligible candidates with at least 2.57 seconds of
headroom. Yet one target supplies 91.50% of seat-5 value and the target spread
is 11,004x. Across both extreme-seat trials, two of eight targets supply 88.78%
of all certified value
([ADR-0194](docs/decisions/ADR-0194-affine-street-mechanism-transfers-to-seat5-but-value-remains-concentrated.md)).

**Open gates:** broaden transfer rather than repeat the exposed blocker family,
and reduce compute time without changing the accepted live semantics. Before
new labels, freeze new board or belief regimes, explicit position coverage,
and a causal materiality/no-op rule. A one-raw-guard threshold is only a
retrospective development candidate even though it retains 99.902% of the
eight observed values. Modern DCFR variants remain deferred: the certificate
and deadline mechanism now work, while opportunity magnitude remains the
strategy weak link.

The retained-label selector replay is now closed by ADR-0206. Across the
primary six regret-vertex blocks per context, the exact Tier-B
slope-times-cap-radius composite selects all six winners and has mean
within-target Spearman `1.0`. It remains nearly perfect after every soft row is
removed, so the result is not merely family discrimination. The exact free
Tier-A own-gain slope is nevertheless a poor ranker and its prefilter discards
winners; the proposed A-to-B-to-C cascade is rejected. Current clock-derived K
is only 1--5 of six blocks and the literal cascade captures 78.17% pooled with
zero or partial capture on three contexts
([ADR-0206](docs/decisions/ADR-0206-opponent-sensitivity-composite-locates-retained-value-but-tier-a-cascade-fails.md)).

The next selector engineering gate is therefore a simplified B-to-C path:
retain the free slope algebra, batch the five opponent-BR directional reads
across coherent blocks, derive K from the measured ledger, and certify only the
winner. Do not assume the full six-set fits. A later fresh panel should prefer
action-conditioned in-tree posterior shifts with a genuinely widened
single-family block library, with construction and thresholds frozen before
labels.

ADR-0198 closes the first compute-attribution subgate. The resident GPU
pipeline consumes 67.87% of pooled step time, host record-to-hand folding
30.56%, and transfer only 0.63%. The primary C4 screen must distinguish FP64
arithmetic from memory/sparse-pipeline pressure on the exact workload; a
resident hand-fold differential is the secondary software lever. ADR-0206
places the opponent-BR batch ahead of that fold for selector capacity; once
Tier B no longer binds, fold savings buy search depth. Neither screen is a
license to change the frozen live rule.

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
