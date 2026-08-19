# Roadmap and Checkpoint Gates

## C0: Research contract and durable memory

**Status:** Passed 2026-08-18.

**Target:** weeks 1-2.

**Gate:** rules, metrics, non-goals, risks, reproduction requirements, and the
evidence protocol are unambiguous and version controlled.

## C1: Exact-game laboratory

**Status:** Passed 2026-08-18 for the initial Kuhn laboratory. Independent
sequence-form validation of multiplayer best response remains a recorded
strengthening task, not a blocker for C2.

**Target:** months 0.5-2.

**Build:** generic extensive-form interface, Kuhn variants, exact evaluation,
best response, NashConv, vanilla CFR, and LCFR.

**Gate:** analytical game values are matched within numerical tolerance; an
intentionally weak policy produces positive deviation gain; all experiments are
reproducible from configuration and code revision.

## C2: Solver comparison laboratory

**Status:** Control established; remaining external-sampling and generic tree-
mutation gates are deferred until C3 supplies a more representative workload.
CFR, LCFR, CFR+, and DCFR share one traversal and the initial fixed-game
comparison is recorded in EXP-0004. Paired leaf perturbation
and explicit pseudo-regret warm starts are implemented; EXP-0005 rejected naïve
unanchored shallow replacement. EXP-0006 provisionally advanced an affine
blueprint anchor for average policies. EXP-0007 added structured, localized,
joint-reach, counterfactual-reach, and matched-root-error controls and rejected
joint reach as a standalone safety signal. EXP-0008 rejected a frozen risk-only
selection rule on held-out strengths, depths, and three-player Kuhn: a separate
resolver-benefit signal is required. Benefit-gate validation, tree mutation,
and external-sampling gates remain. EXP-0009 then rejected blueprint local
regret, scalar probe gain, probe extrapolation, and local-model gain sign as
transferable authorization signals even with exact leaves. A complete
continual-resolving composition gate now precedes v2 selection and neural
scaling. EXP-0010 implemented that Bayesian composition control and rejected
it: even terminal-depth independent public-root solves violate full-game
strategy consistency. A two-player counterfactual-value safe-resolving gadget
was the required control before any multiplayer relaxation. EXP-0011 now
verifies its exact opponent-frontier and residual-adjusted exploitability
certificates at every Kuhn2 public boundary. Raw finite-CFR Resolve is too
unsafe and inefficient to deploy without a residual constraint; an exact
strict gate is safe but conservative and unscalable. EXP-0012 independently
solves the frontier-constrained normal form and rejects max-min degeneracy.
Target-free sum-margin captures 96.99% of the hidden best-response greedy
control's improvement in aggregate on the eight-case Kuhn2 matrix. Measuring
finite-CFR regret shows that cold gadget policies remain unsafe at many
boundaries even after 1,000 iterations. Blueprint warm starts and monotone
certified retention are now the control architecture. A three-iteration DCFR,
mass-10 incumbent rule then failed its declared holdout: sum-margin capture fell
from 34.07% to 2.51% and quality per millisecond fell 130.72-fold. Fixed raw
regret mass is rejected without retuning. A direct constrained
response-generation solver is the next gate before approximate frontiers or
multiplayer.

A dynamic row/column-generation implementation now reaches the exact
sum-margin optimum without resolver normal-form enumeration. Its held-in
five-update point captures 84.17% of the exact objective, but is 3.52% behind
the frozen CFR rule's unusually strong screen quality per millisecond. The rule
then captures 63.02% on a fresh CFR/DCFR holdout without a transfer collapse,
but its rate is 17.30% below frozen CFR. V1 is rejected. Phase-aware deadlines,
immediate column consumption, and shared traversal are the next direct-solver
gate before frontier approximation.

The nonduplicated candidate-ready phase now preserves identical strategies
while raising pooled revealed-development quality per millisecond materially.
A six-candidate v2 rule is frozen on new solver/strength combinations; it must
beat the better of one- and three-iteration CFR controls before phase-aware
generation advances.

Phase v2 then beats the better CFR checkpoint by about 5.18 times on the fresh
paired holdout and remains exactly safe, but fails its preregistered absolute
rate-transfer gate because mean objective headroom is only 37% of development.
The fixed rule is rejected. A target-free opportunity-and-phase-cost estimator
is now required before approximation or kernel specialization.

Causal phase traces now expose a real but narrow scheduler opportunity. At 5
ms, perfect allocation restricted to public states sharing one fixed blueprint
captures 83.21% of exact headroom versus 67.64% for that regime's best fixed
checkpoint. At 20-50 ms Kuhn2 saturates and cannot discriminate schedulers.
Immediate phase reward is the wrong label: no boundary improves at either of
the first two candidate checkpoints although 37/40 improve later. Current early
features rank multi-phase gain/ms too weakly to fit honestly. Rather than fit on
that toy workload, ADR-0021 moves the residual experiment into a full-deck
range-sensitive river microgame. Its 128-context pilot finds normalized
positive regret mass strongly associated with future opportunity and a
40%-76% perfect-allocation uplift at a two-iteration budget. The 1,024-context
development-only replication preserves both results, but also proves that
fresh one-step counterfactual regret equals NashConv in this one-decision binary
tree. Accumulated regret is still causal, yet this is an overly favorable
transfer test. A sequential raise response must break that identity before any
macro-option rule is fitted or frozen.

The fixed-raise sequential gate now passes exactness and breaks that identity in
91.99% of 53,248 production records. It also corrects the target: accumulated
regret ranks total remaining reduction at `0.771`-`0.895`, but reduction per
deterministic unit of work at only `0.390`-`0.594`. All group-preserving
efficiency folds remain positive and measured milliseconds replicate the state-
work ranking. A paid checkpoint-two probe leaves a 4.15%-6.00% perfect
allocation ceiling at average checkpoint four. ADR-0022 therefore authorizes
one transparent post-probe heuristic screen, not a learned scheduler. Static
one-bet hardness transfer is rejected by the exactly paired trace.

That screen now passes its development gate. Five-fold selected rules improve
fixed checkpoint-four DCFR in every held-out development fold, capture 44.34%
of perfect post-probe uplift, and improve conservatively charged reduction/ms
by 2.33%. A CFR+ shadow accumulator is traversal-free and predicts raw future
efficiency slightly better, but is nearly redundant with active regret and
loses after cost. ADR-0024 freezes the simpler active-regret top/bottom 12.5%
checkpoint-two/six allocator. The selection-free validation and subsequent
sealed test both pass unchanged. Test capture is 35.16% of perfect post-probe
uplift, charged reduction/ms improves 2.50%, and every board-group fold strictly
improves final exploitability without exceeding fixed work. ADR-0028 accepts
the rule as an exact sequential-river control, not a wider-tree or multiplayer
scheduler. Neural scheduling remains deferred until a richer workload proves
that its attainable value exceeds this transparent baseline by enough to pay
for inference and training complexity.

**Target:** months 2-4.

**Build:** CFR+, DCFR, external-sampling MCCFR, current/average/snapshot output,
leaf-error injection, and tree-mutation experiments.

**Gate:** solver rankings are repeatable under equal iterations, nodes, time,
and memory; provisional algorithms are selected by workload regime.

## C3: Reduced multiplayer hold'em

**Status:** Started narrowly. The exact full-deck heads-up river control now
supports joint combo ranges, card removal, correlated beliefs, configurable
pot/stacks/bet size, an exact three-bet/two-raise extension, final response, and
an independent normal-form equilibrium oracle for the fixed-size control. This
is the two-player river edge of C3, not completion of reduced multiplayer play.
Re-raises, earlier streets, more players, scalable unilateral NashConv, and
coalition threat models remain. Its frozen post-probe allocator has passed
reserved board/range transfer and is now the compute-allocation control. The next C3
subcheckpoint now separates paired blocker-sensitive cache paths. Exact-source
warm DCFR passes its development gate, but the recertified cached policy before
any new solve is both stronger and cheaper. The global TV certificate is about
111 times faster than a full exact best response but has a median 40x bound-to-
actual ratio on nonzero cases. Delta-aware exact recertification with finite
source policies now passes its development gate: it matches full evaluation
within `2.31e-14` and is 55.65x faster hot, 18.77x faster even with an unshared
full delta scan, and faster in every one of 896 records. The next gate
has now generalized dependency invalidation beyond hard-coded river equations.
The flat generic tape matches all exact controls within `7.11e-15`; sparse
two-deal updates dirty 15%-17% of nodes while factorized-dense updates dirty
82%. The unchanged tape also passes the three-bet/two-raise transfer gate within
`1.42e-14`. Sparse percentages remain 15%-16%, but absolute work grows about
2.7x. C3 now measures whether the added actions earn that cost in exact full-
universe strategy quality before optimizing branch lanes or comparing cached
acceptance and selective repair against warm and cold traversal.

**Target:** months 4-6.5.

**Build:** reduced decks, 2-6 players, dense bet lattice, exact belief handling,
and tractable best responses.

**Gate:** root costs of action omission, card merging, range corruption, and
early stopping are measurable; adaptive branching beats a fixed abstraction on
at least one held-out regime.

## C4: Optimized runtime

**Target:** months 6.5-9.

**Build:** flat C++ tree, CPU vectorization, batched GPU prototype, asynchronous
leaf interface, profiling, cancellation, and memory accounting.

**Gate:** optimized results match the reference numerically and improve real
search traces by several-fold without strategy-quality regression.

## C5: Pluribus-style control agent

**Target:** months 9-11.

**Build:** fixed abstraction, sparse external-sampling LCFR blueprint, cautious
negative-regret pruning, ranges, fixed-depth resolving, and off-tree handling.

**Gate:** complete legal 6-max play; resolver reliably improves the blueprint in
reduced exact games and against a frozen evaluation league.

## C6: Neural blueprint and leaves

**Target:** months 11-15.

**Build:** backward river-to-flop teachers, policy/value/action/uncertainty
models, active data generation, and root-aware validation.

**Gate:** neural leaves reduce held-out root harm at equal latency relative to
blueprint continuation. Lower value MSE alone does not pass the gate.

## C7: Adaptive public-belief search

**Target:** months 15-18.

**Build:** dynamic width/depth, continuous bet proposals, action insertion,
residual solving, street/player specialization, and heuristic computation
allocation.

**Gate:** adaptive search Pareto-dominates fixed search at multiple budgets with
no material rare-branch vulnerability.

## C8: Cache and speculation

**Target:** months 18-20.

**Build:** range-aware caches, topology/embedding reuse, continuous pondering,
future-state forests, and preemptible background work.

**Gate:** future decisions improve without degrading current-decision p95
latency or corrupting strategies when beliefs differ.

## C9: Learned value-of-computation scheduler

**Target:** months 20-23.

**Build:** oracle labels, operation-cost model, conservative learned ranking,
minimum coverage, and heuristic fallback.

**Gate:** learned scheduling beats the best tuned heuristic on hidden games and
full-game traces. Otherwise the heuristic remains production default.

## C10: Full evaluation

**Target:** month 23 onward.

**Gate:** exact reduced-game results, adversarial responders, complete cross-play
matrices, paired-deal confidence intervals, latency/memory profiles, and all
major ablations are available for a defensible report.
