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

ADR-0210 now closes that selector engineering gate. Packing 30 scalar opponent
reads into six responding-seat calls is exact but yields only `1.0059x` median
speedup; terminal-contraction time remains `99.48%` of the scalar bill and the
full six-block B-to-C ledger fits only three of six contexts. The accepted
ADR-0158 overlay was already active and reused `94.47%` of possible terminal
rows, so repeating it cannot supply the missing multiplier. K remains bound.
A later fresh panel should prefer action-conditioned in-tree posterior shifts
with a genuinely widened single-family block library, but it remains sealed
until the engineering ledger can price its candidate set honestly.

The subsequent systems and strategy line changes that assessment materially.
The resident device fold speeds both the warm-step and Tier-B customers
([ADR-0212](docs/decisions/ADR-0212-device-record-fold-materially-speeds-both-resident-customers.md)),
while the isolated profile identifies sparse FP64 compute pressure rather than
a hidden transfer or host barrier
([ADR-0218](docs/decisions/ADR-0218-resident-sparse-profile-identifies-compute-pressure.md)).
Action-conditioned posteriors contain exact value but the widened live selector
still misses the wall boundary
([ADR-0222](docs/decisions/ADR-0222-widened-range-transfer-finds-value-but-live-selection-is-infeasible.md)).

Continuation rooting is the first strategy-positive correction to that
failure. It is exact, cuts five sixths of strategic nodes, prices all 31 legal
blocks, and delivers exact certified value on all 12 opened targets before the
deadline ([ADR-0224](docs/decisions/ADR-0224-continuation-root-is-exact-and-removes-five-sixths-of-strategic-nodes.md),
[ADR-0226](docs/decisions/ADR-0226-continuation-root-unbinds-the-complete-31-block-library.md),
[ADR-0228](docs/decisions/ADR-0228-continuation-root-delivers-exact-safe-value-on-all-twelve-targets.md)).
Two independent steps fit every conservative ledger
([ADR-0230](docs/decisions/ADR-0230-two-continuation-steps-fit-the-conservative-street-ledger.md)),
and the disjoint 12-target Latin-C/D posterior panel is sealed
([ADR-0232](docs/decisions/ADR-0232-heldout-continuation-posterior-panel-is-fresh-and-nondegenerate.md)).

The held-out depth gate is now closed. Two steps consume 14.00% more charged
time, deliver 1.10% less pooled exact value, and reduce value rate by 13.24%.
Eleven of twelve targets reproduce the exact same winner; the sole material
switch is harmful
([ADR-0235](docs/decisions/ADR-0235-one-step-retained-after-heldout-depth-value-trial.md)).

The first direction-diversity capacity gate is closed. A complete second
soft/regret bisector family is structurally distinct but exceeds the street
boundary on 4 of 12 targets, reaching 19.42 seconds
([ADR-0237](docs/decisions/ADR-0237-full-bisector-library-does-not-fit-every-street.md)).
No direction labels were opened.

ADR-0239 rejects the first label-free cross-payoff implementation before any
coefficient matrix completed: its fixed-response splice used embedded layout
hand keys instead of the continuation's external posterior axes. The algebra
remains open, but a mechanical rerun is deferred in favor of the stronger
one-seat convex-program question.

ADR-0241 closes the finite keystone. The sequence-form row solver matches both
complete 64-by-64 normal-form teachers to at most `3.47e-17`, preserves the
safe-incumbent and `U - L` timeout contract, rejects the behavioral shortcut on
a repeated-actor path, and passes realization-retreat identities below
`1.1e-16`. It uses five opponent rows for acting seat 0 and three for seat 1;
those sparse control counts are not an h32 prediction.

ADR-0243 closes the h4 open-axis identity gate. The repeated-actor sequence-
form row and post-bet behavioral row match independent dense teachers below
`8.0e-15`; the corrected explicit-axis response splice is exact while the old
embedded-key splice fails all 256 mutation entries. The measured CPU h4 costs
are controls, not h32 predictions.

ADR-0244 freezes the narrow h32 successor on the tight Latin-D target and its
widest acting seat. Eleven initial resident passes build all six epigraph rows;
16 frozen regret vertices are projection teachers only. The self-priced ledger
charges a measured full response oracle and all five possible new response
rows per cut round, plus a separate measured-or-floor final proof reserve.

ADR-0245 closes that preflight. All 96 projections agree below `4.2e-15`; six
gain rows occupy 49.2 KB, the pool peaks at 5.66 GB, and physical free memory
stays above 9.62 GB. The measured conservative ledger fits exactly one complete
cut round at 13.47 seconds. A second does not fit.

ADR-0246 freezes the label-free one-round h32 master prototype on the identical
target and acting seat. It corrects the conservative ledger by charging the
previously omitted initial master reserve: the complete one-round path is now
`13,967.616 ms`, not `13,467.616 ms`. The runner solves the source restricted
master, runs one exact all-seat multi-cut oracle, resolves at most once, and
stops. It reports verified `L`, independent `U`, `U - L`, response signatures,
rows, active caps, retreat, timings, memory, and both complete ledgers while
emitting only the immutable blueprint.

ADR-0247 closes the optimizer gate. The initial master needs two new opponent
facets; one all-opponent multi-cut round then closes exact `U - L` to
`3.84e-15`. The final exact cap violation is only `1.03e-15`, the measured live
ledger is 8.72 seconds, and the corrected conservative ledger is 13.97
seconds. A result audit caught that the frozen runner reused the looser
epigraph tolerance for its cap-feasible Boolean; independently applying the
preregistered `2e-11` cap allowance leaves the branch unchanged by nearly four
orders of magnitude. The endpoint and diagnostic retreat remain un-emitted,
and no strategy-quality claim is open.

ADR-0250 records that ADR-0249's first invocation stopped at its pre-label
barrier: source, cuts, row counts, and both LP bounds reproduced, but three
GPU-derived policy byte digests did not. No retreat or fallback label opened
and no artifact was written. This is the ADR-0179 reassociation class, not a
changed optimizer branch.

**Open gate:** ADR-0251 inherits the narrow quality trial while correcting only
candidate identity. The algorithm, exact response signatures, cut set, row
counts, bounds, and numerical optimizer witnesses are authoritative; policy
digests are diagnostics. The two-oracle schedule, sealed comparator, distinct
cap/epigraph allowances, full `13,967.616 ms` conservative charge, immutable
external blueprint, and strict fresh-replication promotion rule are unchanged.

ADR-0198 closes the first compute-attribution subgate. The resident GPU
pipeline consumes 67.87% of pooled step time, host record-to-hand folding
30.56%, and transfer only 0.63%. The primary C4 screen must distinguish FP64
arithmetic from memory/sparse-pipeline pressure on the exact workload; a
resident hand-fold differential is the next concrete software lever now that
ADR-0210 rejects opponent-call packing. The fold differential must charge host
milliseconds removed and device milliseconds added separately, cover both the
warm step and Tier B, and reprice the complete ledger. If the sparse pipeline
still controls K afterward, separate arithmetic from memory pressure before a
kernel rewrite. Neither screen is a license to change the frozen live rule.

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
