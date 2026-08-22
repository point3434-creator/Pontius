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

ADR-0252 closes the corrected quality gate. The independently certified half-
retreat delivers exact value `0.00795681`, `3.14x` the accepted fallback's
value, and retains `1.50e-9` minimum cap slack. Its conservative value rate is
`2.37x` the fallback rate while the full `13,967.616 ms` ledger still fits.
All numerical/discrete reconstruction gates pass while the three policy byte
digests remain non-gating reassociation diagnostics.

ADR-0254 accepts the final label-free panel. All 12 target IDs and digests are
fresh, every source/bettor/acting seat appears twice, and the three panels now
cover all 36 source-bettor combinations exactly once. Acting-player marginal
TV is nonzero on every target (`0.044–0.194`); no quality label was opened.

ADR-0255 freezes that strategy replication before any Latin-E warm step or
final label. All six Latin-E targets run in manifest order with no opportunity
selection or cross-target adaptation. Each target pays one warm step, one
source master, one exact multi-cut construction oracle, at most one resolve,
and one independent exact factor-`0.5` retreat certificate. The cap and
epigraph allowances remain separate, the effective ledger is at least
`13,967.616 ms`, all external policies remain the blueprint, and the bounded
one-round master makes no global-optimality claim.

ADR-0256 rejects the partial v1 invocation without a strategy result. Target 1
completed in memory but its label was never printed, persisted, or inspected;
target 2 stopped before its final label. Its first oracle found three apparent
epigraph violations whose response signatures were already resident and whose
rows matched exact gains within `4.98e-16`. The largest `3.073e-9` discrepancy
matched the master's recorded inequality residual, identifying a response-
classification defect rather than a missing facet. No artifact was written and
Latin-F remains untouched.

ADR-0257 freezes the label-blind correction. Already-resident response rows are
accepted only when they reproduce the exact oracle within `2e-11` and remain
inside the unchanged `1e-8` master primal ceiling; genuinely new opponent
signatures are still cut. It also requires all six candidates to freeze before
any v2 final retreat label. Certificate contexts are then reconstructed one at
a time, with identities and reconstruction time recorded separately from the
unchanged resident live ledger.

ADR-0258 closes the corrected campaign. All six candidates freeze before the
first v2 label; all six exact half-retreats are cap-safe, material, and on time.
Pooled delivered value is `0.0649285`, with target values from `0.0017020` to
`0.0323617`; all three balanced and all three blocker-heavy targets pass. The
four verified resident residual rows match exact gains within `4.72e-16`, ten
new facets are cut, measured live time stays below 8.98 seconds, and the full
13.97-second conservative ledger fits every target. Target 1 remains explicitly
label-blind reconstructed under ADR-0256; no candidate was emitted.

**Immediate gate:** preregister the unchanged algorithm and thresholds on the
six untouched Latin-F targets. Preserve the campaign-wide barrier, factor
`0.5`, exact final proof, resident-row classification, full conservative
ledger, immutable blueprint emission, and null global/population claims. Treat
Latin-F as confirmation of the breadth branch, not as a license to retune or
introduce a fresh fallback comparison.

ADR-0259 freezes that confirmation before any Latin-F GPU work. All six targets
run in manifest order as first final-label evaluations. The algorithm,
tolerances, factor, campaign barrier, exact proof, `0.001` materiality floor,
four-of-six breadth rule, family requirement, and complete ledgers are inherited
unchanged from ADR-0257/0258. No Latin-E value enters a Latin-F threshold.

**Immediate gate:** execute ADR-0259 once and seal the fixed confirmation
branch. A pass authorizes only a separately preregistered prospective live-
shadow integration test with immutable blueprint fallback; a clean failure
retains Latin-E evidence but rejects that integration step. Neither branch
licenses deployment or a population claim.

ADR-0260 accepts the untouched confirmation at the exact frozen floor. Four of
six Latin-F targets materially pass, with both families represented and every
schedule inside the full ledger. All six raw half-retreats are positive and
exact-cap-feasible; two abstain solely because minimum slack (`1.374e-9` and
`1.246e-9`) misses the stronger `1.48e-9` interior requirement. Latin-E/F now
deliver accepted pooled value `0.1104383` across ten contract-passing targets,
while every actual policy remains the blueprint.

ADR-0261 freezes the first deployment-aligned identity panel without opening a
strategy label. Each retained source observes checks, a bet, and exactly the
first responder's call; the second responder is then the player actually on
the clock, with three opponents still acting downstream. Source, bettor,
observed responder, and acting player are each balanced exactly once. The
manifest must prove the legal prefix, current-player identity, one-node h32
axis, path-single-visit topology, fresh posterior identity, and nondegenerate
belief shifts before GPU work.

ADR-0262 accepts the label-blind manifest. All six posterior identities are
fresh and nondegenerate; every declared actor is the current fold/call player,
with three downstream responders, one acting public node, 32 h32 information
sets, and 64 behavioral variables. Current-actor marginal TV is
`0.062778–0.152469`. The manifest generated zero strategy labels.

ADR-0263 freezes that strategy trial before any decision-aligned label. A scoped
adapter changes only posterior/continuation setup and must restore the sealed
Latin setup after the bounded campaign. The one-round core, factor `0.5`, exact
certificate, `1.48e-9` interior floor, full measured and conservative ledgers,
global prelabel barrier, and immutable-blueprint external emission remain
unchanged. Process validity is separate from the inherited four-of-six material
value-transfer threshold.

ADR-0264 accepts the prospective current-decision result. All six half-retreats
are exact-cap-safe, interior, positive, and shadow-accepted; four exceed
`0.001`, both range families are present, and measured live time tops out at
5.081 seconds while the 13.968-second conservative floor remains binding. The
scoped setup adapter restores correctly and every actual emission is still the
blueprint.

ADR-0265 freezes the label-blind post-fold differential. It reuses the six
sources and positional schedule, changes only the first observed response from
call to fold, and requires fresh disjoint identities, legal current-player
roots, three downstream responders, one-node h32 axes, and zero strategy
labels. A pass seals identities but deliberately does not authorize their GPU
strategy evaluation.

ADR-0266 accepts and seals the post-fold manifest. All 36 gates pass, the six
identities are fresh and disjoint from the post-call panel, every actor is
current with one h32 public node and three downstream opponents, and actor TV
is nonzero at `0.037662–0.130666`. The CPU-only run generates zero strategy
labels; those identities remain closed.

**Immediate gate:** inventory the already-opened retained convex contexts and
preregister an off-clock full-convergence closure census before opening any
post-fold strategy label. The census is retrospective but not label-free: it
may generate optimizer labels only on contexts whose strategy evidence is
already open. Measure rounds to exact closure, unique new response facets,
oracle work, incumbent certified value, and verified master-upper-bound minus
incumbent-lower-bound gap. Use that distribution—not the single ADR-0247
keystone—to decide whether the live one-seat direction-library branch can be
demoted. Preserve the ray library as a cheap incumbent/fallback until that
evidence closes.

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
