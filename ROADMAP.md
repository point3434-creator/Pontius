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

**Status:** In progress. CFR, LCFR, CFR+, and DCFR share one traversal and the
initial fixed-game comparison is recorded in EXP-0004. Paired leaf perturbation
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
mass-10 incumbent rule is frozen before its declared holdout; that transfer
test is the next gate before objective-aware solvers, approximate frontiers, or
multiplayer.

**Target:** months 2-4.

**Build:** CFR+, DCFR, external-sampling MCCFR, current/average/snapshot output,
leaf-error injection, and tree-mutation experiments.

**Gate:** solver rankings are repeatable under equal iterations, nodes, time,
and memory; provisional algorithms are selected by workload regime.

## C3: Reduced multiplayer hold'em

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
