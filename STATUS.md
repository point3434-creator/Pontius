# Project Status

## Active checkpoint

Checkpoint 3: reduced hold'em, exact heads-up river/cache subcheckpoint.

## Verified state

- Workspace initialized as a clean Git repository.
- Initial project scope, measurement contract, architecture, risks, and roadmap
  are recorded.
- Bundled Python runtime is available; system Python and CMake are not currently
  on `PATH`.
- The generic finite-game interface and exact two-player Kuhn rules are
  implemented.
- Exact expected utility, pure information-set best response, deviation gain,
  NashConv, and exploitability are implemented.
- Full-tree alternating CFR and LCFR share one traversal and pass 14 automated
  tests in the initial commit.
- At 20,000 sequential reference iterations, CFR reached NashConv `0.00014427`
  in 3.911 seconds and LCFR reached `0.00000859` in 3.917 seconds. Both matched
  Kuhn's analytical player-0 value of `-1/18` within numerical tolerance.
- Configurable two-to-six-player Kuhn implements the explicit rules in
  `ADR-0005` and now passes a total of 23 automated tests.
- The exact dynamic perfect-recall best response matches exhaustive policy
  enumeration in two-player tests and is locally undominated in a three-player
  cross-check.
- At 5,000 three-player iterations, CFR reached NashConv `0.00077954`; LCFR
  reached `0.00001229`. This advances LCFR as the control without establishing
  multiplayer convergence.
- Uniform-profile exact evaluation took approximately 0.001, 0.014, 0.249,
  4.940, and 106.623 seconds for two through six players respectively.
- CFR+, with RM+ and quadratic averaging, and default DCFR(1.5, 0, 2) now share
  the same buffered-regret traversal as CFR and LCFR.
- EXP-0004 found CFR+ strongest at 500-1,000 three-player iterations and DCFR
  strongest at 5,000. LCFR and CFR+ were effectively tied at 20,000 two-player
  iterations. Solver selection is therefore budget- and regime-dependent.
- Depth-limited games now substitute cached blueprint continuation values after
  a stated number of strategic actions without modifying the full-game
  evaluator. Deterministic zero-sum leaf perturbations report realized errors.
- Paired exact-control/treatment experiments and a replicated matrix runner map
  leaf error to full-game NashConv and policy change.
- EXP-0005 rejected naïve unanchored shallow replacement: with exact leaves it
  worsened a strong two-player blueprint by about 0.087 NashConv. A mass-10
  pseudo-regret prior attenuated the effect but behaved very differently across
  update rules and never improved the blueprint.
- A solver-level affine blueprint anchor and an independent output trust region
  now have explicit no-op and total-variation invariants. Prepared blueprints
  are reused across matrix runs. Sixty-two automated tests pass.
- EXP-0006 found that depth-two anchored average policies can improve weak,
  medium, and strong two-player blueprints. Anchored LCFR was best with exact
  leaves in the tested strong-blueprint slice; moderate noise changed the
  ranking, and every current policy failed.
- A CFR+ 0.995 anchor improved all ten independent-error seeds through realized
  RMSE `1.38657e-4`, failed one seed at RMSE `4.62190e-4`, and lost to no-op on
  mean at RMSE `1.38657e-3`. This is a provisional error envelope, not a neural
  target or multiplayer claim.
- Cutoff traversal now propagates chance reach and every player's behavior
  reach separately. Reports include joint-reach conditional and root L2 error,
  per-player counterfactual RMSE/root L2, active reach mass, and uniform error.
- Random leaf error can be grouped by concrete or public history, localized by
  blueprint reach or public actions, combined with explicit bias, and calibrated
  to equal realized on-policy root L2 for controlled comparisons.
- EXP-0007 showed raw error scale is not transferable across correlation
  structures. At equal on-policy root L2, errors localized to the low-reach
  half failed all 40 tested LCFR/0.99 runs across two groupings while the
  high-reach half improved 39/40. Counterfactual error exposed the difference.
- Joint reach alone is rejected as a scheduler safety signal. Local uncertainty,
  per-player counterfactual sensitivity, provenance/correlation, and minimum
  rare-branch coverage advance as required allocator inputs.
- Counterfactual-risk rule v1 is preregistered as a fixed LCFR/0.99 average
  candidate gated at maximum player-specific counterfactual root L2 `2.0e-4`.
  Its machine-readable document, held-out seeds/configs, and kill criteria are
  frozen before any two- or three-player holdout is run.
- EXP-0008 rejected that rule unchanged. It selected harm in 434/788 searched
  two-player holdouts and 104/208 searched three-player holdouts; mean selected
  NashConv deltas were `+3.03543e-5` and `+4.24468e-5`. Permanent no-op won.
- Near-exact leaves did not rescue v1. Search harmed every depth-one two-player
  case and both depths of the strong three-player blueprint, while improving
  the corresponding weak-blueprint cases. Risk may veto search but cannot
  establish positive resolver value.
- A fixed-policy one-step counterfactual-regret evaluator and exact-leaf
  resolver-benefit laboratory now separate local signals from untouched
  full-game targets. Progressive probes are analyzed without fitting a rule.
- EXP-0009 evaluated 72 distinct candidates in each of two- and three-player
  Kuhn across five probe checkpoints. Full search improved only 32/72 and
  26/72 respectively despite exact continuation leaves.
- Full local gain per mean policy TV was the strongest observed ranking signal
  (AUC 0.968 in Kuhn2, 0.686 in Kuhn3, 0.855 combined), but local gain sign made
  38 and 40 false-positive deployments. Probe slopes and extrapolations did not
  transfer between games, so no v2 selector is frozen.
- Exact leaf values preserve fixed-policy expected utility but not full-game
  deviations below the frontier. Prefix-only resolving is therefore a
  compositional bottleneck that must be tested before neural leaf scaling.
- A Bayesian continual-resolving control now reconstructs card-sensitive joint
  posteriors, resolves every public history, deploys each information set once,
  and retains the blueprint on zero-reach histories. Posterior and no-op
  invariants are tested.
- EXP-0010 rejects that control. It improved 21/72 Kuhn2 and 2/24 Kuhn3 cases;
  mean NashConv improvement and quality per millisecond were negative. An
  optimistic exact local-model gate reached only 29/72 and 4/24.
- A coherent global anchored solve improved 68/72 paired Kuhn2 rows and all
  24 Kuhn3 rows. At terminal depth, prefix/global improved all six audit cases
  while independent continual replacement harmed all six. Counterfactual
  frontier consistency, not tree depth or leaf error, is the next bottleneck.
- An exact two-player terminate/follow resolving gadget now samples public-root
  states by chance and resolver reach while excluding opponent reach. It
  computes exact blueprint opponent counterfactual-best-response frontiers and
  deploys only the resolver's subgame component.
- The gadget's one-sided security residual equals the sum of positive frontier
  violations. Single and nested replacements satisfy a tested exploitability
  bound equal to half that residual, additive across nested solves.
- EXP-0011 found zero bound failures across 128 single-boundary candidates and
  all 32 composed profiles. Raw finite-residual Resolve improved only 9/32 and
  had mean NashConv improvement `-7.05082e-3`.
- An exact strict-frontier gate deployed 18/128 searched public histories,
  improved 9/32 profiles, never worsened a blueprint, and had mean improvement
  `+1.27000e-3`. It is a correctness control, not a scalable runtime gate.
- A dependency-free normal-form oracle now independently solves the safe
  frontier with a matrix-game LP, a general two-phase simplex, and verified
  mixed-to-behavioral conversion.
- EXP-0012 rejects max-min margin as the primary objective. Target-free
  constrained sum-margin improved all eight paired Kuhn2 profiles, achieved
  mean NashConv improvement `3.56692e-3`, and beat max-min in every case at
  essentially identical exact-oracle cost.
- Sum-margin captured 96.9916% of the hidden best-response greedy control's
  improvement in aggregate, with 94.9296% worst-case capture and zero
  residual-adjusted bound failures. The hidden control remains diagnostic and
  its root-forward composition is not a global optimum claim.
- Progressive CFR trajectories now report exact feasibility, target-free
  sum-margin regret, hidden conditional BR regret, average/current outputs, and
  a monotone certified incumbent at every checkpoint.
- EXP-0013 screening rejects cold gadget solving at online-scale budgets. Even
  after 1,000 iterations, cold average policies are exactly safe at only 5/16
  CFR, 6/16 LCFR, 7/16 CFR+, and 8/16 DCFR public boundaries.
- The target-free screen winner is DCFR with blueprint pseudo-regret mass 10
  and three iterations. It captures 34.0688% of exact sum-margin headroom at
  2.839 mean reference milliseconds and is frozen as
  `safe-solver-incumbent-v1` before holdout evaluation.
- The frozen v1 holdout rejects transfer: only 1/16 boundaries improve,
  aggregate sum-margin capture falls to 2.51385%, and target-free quality per
  millisecond falls by 130.72 times. The rule is not retuned.
- Blueprint initialization and monotone certified retention still prevent
  harm: all rejected holdout snapshots fall back to no-op. Fixed raw
  pseudo-regret mass is rejected as a transferable trust parameter.
- The dependency-free simplex now returns and independently verifies dual
  variables, enabling reduced-cost pricing rather than normal-form scanning.
- A blueprint-started restricted master now generates opponent response rows
  and prices resolver columns with a dual-weighted dynamic best response. It
  matches the exact normal-form sum-margin teacher at every tested boundary.
- On the 16-boundary held-in screen, five updates capture 84.1691% of exact
  sum-margin and 71.5120% of hidden BR improvement at 7.270 mean milliseconds.
  Its target-free rate is 3.52% below frozen CFR v1 on that screen, so it has
  not yet passed the quality-per-millisecond gate.
- `constrained-generation-v1` and a fresh 24-boundary CFR/DCFR holdout are
  frozen in commit `58f2e66`. Response separation and pricing, not simplex
  solve, dominate current reference latency.
- Frozen generation v1 passes safety, exact-convergence, minimum-capture, and
  rate-transfer gates on the fresh holdout. It captures 63.0223% of exact
  sum-margin at 7.328 mean milliseconds, selecting 21/24 boundaries.
- It fails the decisive rate comparison: `2.50896e-4` sum-margin/ms versus
  frozen CFR checkpoint three's `3.03383e-4`. Generation gets 2.10 times the
  objective capture at 2.54 times the latency. V1 is rejected without retuning.
- The post-reveal update-six jump is diagnostic only. A column priced after
  update-five scoring is not consumed until update six; two weak CFR cases
  account for 96.13% of the gain. Phase-aware cancellation and immediate cheap
  re-solves are now the next efficiency hypothesis.
- Candidate-ready timing and terminal pricing cancellation are now explicit.
  One-pass response generation and optional realization auditing preserve the
  exact strategy sequence while removing duplicate charged traversal.
- Across all 40 revealed development boundaries, six candidate-ready solves
  capture 92.3114% of exact sum-margin at 5.440 mean milliseconds and
  `4.63568e-4` margin/ms. The weaker subset still beats its corresponding frozen
  CFR rate by about 35%.
- `constrained-generation-phase-v2` is frozen before a new 48-boundary holdout
  crossing all four blueprint solvers at unseen iterations 75, 700, and 5,000.
- Phase v2 captures 81.2623% of exact sum-margin on that fresh holdout and beats
  the better frozen CFR checkpoint by 5.1845 times in target-free margin/ms,
  with selected frontier violation at most `1.11e-16`.
- It nevertheless fails its preregistered absolute rate-transfer gate: only
  32.7363% of development rate remains versus a required 50%. The fixed rule is
  rejected without changing the gate.
- Exact improvement headroom per boundary is only 37.28% of development, while
  opportunity-normalized capture/ms retains 87.82%. This separates conditional
  solver efficiency from the scheduler's job of finding worthwhile decisions.
- Candidate-ready timing is now explicitly labeled counterfactual when it
  subtracts pricing already used to establish earlier convergence. Executable
  fixed-loop accounting yields the same gate verdict and a 5.0552x CFR win.
- A causal opportunity dataset now separates boundary-start, candidate-ready,
  and post-pricing decisions. Its 412 revealed-development records use explicit
  online feature allowlists; oracle and current-pricing mutation tests prevent
  target and phase leakage.
- At an average 5 ms budget within each fixed blueprint regime, a perfect
  state-adaptive pool captures 83.2072% of exact sum-margin versus 67.635% for
  that regime's best oracle fixed checkpoint and 47.7146% under independent
  hard deadlines. A serial timing replicate preserves the adaptive result and
  moves fixed capture only to 67.323%.
- Cross-blueprint pooling reaches 99.919% but is rejected as a deployment
  interpretation. Within fixed blueprints, the largest one of four public
  boundaries holds a headroom-weighted 41.04% of opportunity and the largest
  two hold 70.20%.
- Myopic phase rewards are rejected: the first two candidate checkpoints
  improve 0/40 boundaries although 37/40 improve later. First gain requires
  3.51 candidates and 4.29 ms from boundary start on average, with a maximum
  horizon of six candidates.
- Existing early scalar features do not justify fitting a scheduler. Their
  strongest univariate rank correlation with best future gain/ms is only about
  0.15 at boundary start, 0.11 after candidate one, and 0.11 after its pricing.
- A full-deck exact river microgame now represents joint combo ranges, card
  removal, best-five-of-seven showdowns, one fixed no-limit bet, and separate
  structural versus full-range provenance digests.
- Approximate range matches cannot produce deployable strategy-cache hits.
  Exact provenance is required; same-structure results are warm starts only
  until recertified under the current joint range. A fixed-policy TV value
  bound is implemented but explicitly does not certify equilibrium reuse.
- A 1% adversarial joint-range change has root TV `0.01`, conditional TV `1.0`
  at a rare shared private hand, and flips its exact response from fold to call.
- An independent normal-form LP recovers the analytical fixed-bet bluffing
  equilibrium and verifies every generated teacher by behavioral NashConv.
- The river generator groups balanced, polarized, blocker-stress, and correlated
  ranges by board so no related variants cross development/validation/test.
  Reserved splits can be omitted before any oracle or trace is run.
- The 128-context pilot generated 512 solver runs and 6,656 causal records. LP
  duality gap and behavioral NashConv stayed below `1.28e-13`.
- The first average-strategy iteration improves nothing. First gain appears at
  iterations two to four, and 33%-55% of solver runs regress at least once
  between later checkpoints despite strong mean convergence.
- DCFR has the best checkpoint-64 mean exploitability (`0.00587`), followed by
  CFR+ (`0.00757`), LCFR (`0.01855`), and CFR (`0.08251`). Solver choice is still
  context- and budget-dependent at the earliest checkpoints.
- At an average two-iteration budget, a perfect pooled allocator beats fixed
  checkpoint two by 40.1%-75.6% depending on solver. The advantage falls below
  6% by four iterations. This is an optimistic shared-compute ceiling, not a
  deployable scheduler.
- Normalized positive regret mass at checkpoint two has pilot Spearman
  correlation `0.923`-`0.963` with normalized future opportunity. No rule has
  been fitted or frozen.
- The clean production trace confirms the pilot across 256 development boards,
  1,024 contexts, 4,096 solver runs, and 53,248 records. No validation or test
  board was materialized; maximum teacher NashConv is `1.09e-12`.
- Production checkpoint-64 mean exploitability is `0.07283`, `0.01697`,
  `0.00834`, and `0.00670` for CFR, LCFR, CFR+, and DCFR. Depending on solver,
  31.4%-63.1% of runs regress between at least two recorded checkpoints.
- The production pooled budget-two uplift is 51.1%-75.9% on the fixed
  128-context allocation sample, falling to 8.15%-9.34% at budget four and
  2.19%-2.98% at budget eight.
- Production checkpoint-two normalized accumulated regret correlation remains
  `0.904`-`0.943`; every board-group-preserving fold remains above `0.885`.
- In this one-decision binary tree, freshly computed positive counterfactual
  regret equals NashConv exactly. The recorded accumulated-regret feature is
  causal but benefits from that structural confound, so scheduler fitting is
  deferred until a sequential-decision game.
- A compact analyzer reproduces first-improvement, nonmonotonicity, feature-rank,
  exactness, and allocation diagnostics without fitting a rule.
- The exact river now supports one fixed legal raise-to action and a final
  opener fold/call response. Exact sunk-cost payoffs, perfect recall, and
  independent mixed-plan-to-behavioral realization are tested.
- On the analytical sequential control, uniform-policy NashConv is `35/6` while
  one-step positive regret is `20/3`; the shallow identity is broken.
- The clean sequential production trace contains the same 256 development
  boards and 1,024 joint ranges, 4,096 solver trajectories, and 53,248 records.
  No validation or test range was constructed; maximum teacher NashConv is
  `1.0413e-11`.
- Local one-step regret differs from NashConv in 91.99% of sequential records.
  Normalized accumulated regret ranks total headroom at `0.771`-`0.895`, but
  the relevant state-work efficiency target at only `0.390`-`0.594`.
- Every group-preserving state-efficiency fold remains positive. State-visit
  and measured-millisecond target rankings agree at `0.9946`-`0.9991`.
- After charging every context for the checkpoint-two feature probe, a perfect
  future allocator beats fixed checkpoint four by only 4.15%-6.00%. This is an
  optimistic ceiling, not achieved scheduling.
- Exactly paired one-bet features fail cross-tree transfer: their correlation
  with sequential state efficiency is `-0.191` to `0.009`, and feature-rank
  stability is only `0.183`-`0.293`. Static hardness reuse is rejected.
- ADR-0022 authorizes one transparent development-only post-probe screen with a
  fixed fallback. Neural scheduling and reserved-board evaluation remain
  unauthorized until a rule is preregistered and frozen.
- CFR+ shadow regret now consumes the active DCFR traversal's instantaneous
  deltas without changing its strategy or launching another tree walk. It is a
  DCFR-path statistic, not an equivalent standalone CFR+ solve.
- The 1,024-context shadow probe reproduces every provenance digest and active
  checkpoint-two feature exactly. Conservative update-plus-feature charging is
  7.905% of the plain two-iteration probe.
- Raw shadow regret ranks raw gain per state visit better than active regret
  (`0.670` versus `0.618` Spearman), but their ranks are `0.978` correlated.
  Every shadow-bearing top candidate loses measured quality per millisecond
  after charging its probe cost.
- The preregistered development screen passes all gates. Its fold-selected
  rules improve fixed checkpoint-four DCFR in all five held-out development
  folds, capture 44.335% of perfect post-probe uplift, and improve charged raw
  reduction per millisecond by 2.330% without exceeding state work.
- All-development selection freezes `active_raw::shallow_12_5`: 128 contexts at
  checkpoint two, 768 at four, and 128 at six. It lowers aggregate final
  exploitability by 148.969 and improves charged reduction/ms by 2.509% while
  using 512 fewer deterministic state visits than fixed checkpoint four.
- ADR-0024 and `river-post-probe-scheduler-v1` freeze that active-only rule
  before any reserved board is constructed. This is a development result, not
  a transfer claim.
- A selection-free holdout evaluator now hard-checks the frozen rule hash,
  charges an independently timed one-pass active-regret summary, applies the
  rule within five disjoint board-group folds, and prevents test evaluation
  unless the unchanged validation verdict passes.
- A bounded packing-simplex fast path plus verified two-phase fallback solves
  every reserved exact matrix teacher. The validation teacher-only audit covers
  all 296 contexts; 295 use packing and one uses fallback, with maximum duality
  gap and behavioral NashConv `8.65e-11`.
- The frozen scheduler passes validation without selection or retuning. Across
  74 unseen groups and 296 contexts, every fold improves fixed checkpoint-four
  DCFR; aggregate perfect-uplift capture is 42.484% and charged reduction/ms
  improves 2.630%.
- Commit `c38fa4b` records that validation pass before test construction. The
  then-opened sealed test also passes unchanged across 70 groups and 280
  contexts: every fold improves, aggregate capture is 35.156%, and charged
  reduction/ms improves 2.499%.
- Test fold-local final exploitability is 263.548 versus 301.273 fixed, a
  12.522% decrease, while using 1,118 versus 1,120 iterations and 252,412
  versus 253,120 deterministic state visits. This is exact heads-up river
  transfer, not a six-player claim.
- Exact-provenance cache lookup is now mechanically distinct from structural
  topology/policy hints. Range distance never authorizes a direct strategy hit;
  cached information-set schemas can initialize CFR without rediscovering the
  tree.
- A two-player zero-sum TV certificate bounds one fixed cached policy's target
  exploitability by source exploitability plus twice payoff span times joint
  TV. It is verified against exact target best responses and explicitly does
  not transfer to multiplayer.
- The 152-pair blocker-sensitive development screen passes every frozen warm-
  start gate. Fold-selected checkpoint-four warm DCFR removes 94.574% of cold
  residual and improves charged reduction/ms 18.628% at identical state work.
- The stronger finding is negative for further solving: exact current-range
  recertification of the cached source policy before any DCFR step has aggregate
  exploitability 10.409 versus 11.441 after selected warm solving and 210.844
  cold. Lookup plus full recertification improves rate 190.46% over cold.
- The 0.0227 ms mean TV certificate is safe but loose; full exact recertification
  costs 2.526 ms. At a normalized 0.5% ceiling, the bound certifies only 3/152
  pairs while exact evaluation accepts all 152. Delta-aware recertification is
  now the bottleneck.
- Exact source teachers cost 106.493 ms on average and are an optimistic sunk-
  cache assumption. No warm prior advances until finite source policies and
  explicit amortization are tested.
- A provenance-bound `RiverRangeDelta` and compiled finite-policy evaluator now
  update only changed deal coefficients and affected private-hand best-response
  maxima. Support additions compile unseen hands under the target game; no
  distance threshold or unchecked chained update exists.
- Differential tests cover no-raise and sequential-raise trees, all four river
  families, finite DCFR policies, blocker reweights, deal removal, and unseen-
  hand addition. Worst production disagreement with full exact evaluation is
  `2.31e-14`.
- The frozen 896-record finite-policy development benchmark passes every gate.
  Exact incremental application averages 0.1996 ms versus 11.1061 ms full,
  yielding 55.652x hot, 37.315x shared-delta, and 18.766x pessimistic unshared-
  delta speedups. Every individual record is faster.
- Compiled-cache construction averages 1.9132 ms and pays back in an estimated
  0.175 recertifications. Charging it leaves a 14.313x aggregate speedup;
  charging the entire finite source solve to one batch instead yields 0.640x,
  so policy construction and reuse economics remain explicit.
- At finite DCFR checkpoint 64, mean normalized source exploitability is
  `0.000118`; targets average `0.000484` after larger blocker reweights and
  `0.000153` after smaller unseen-hand support swaps. Cheap recertification
  measures this damage but does not repair it.
- The TV bound is 5.92 times faster than incremental application. A post-hoc
  bound-first cascade is counterproductive at a 0.1% quality ceiling but would
  reduce recorded exact-path cost at 0.5%-2% ceilings. No threshold rule is
  frozen from this development inspection.
- A generic root-chance dependency compiler now emits topologically ordered
  Float64 input, constant, affine, product, argmax, and history-select nodes in
  flat arrays with reverse-CSR invalidation and source-relative epoch overlays.
  It is independent of river action constants and supports declared source-zero
  outcomes for unseen-hand additions.
- The frozen generic-tape matrix passes all 840 finite-policy target checks with
  worst error `7.11e-15`, zero best-response action mismatches, zero replay
  drift, and 529 observed selector changes. Both sparse and dense execution
  match the generic full and specialized river controls.
- Two-deal blocker and unseen-support updates dirty only 17.233% and 15.374% of
  nodes on average. Factorized likelihood updates change 99.286% of deals and
  dirty 81.858%, confirming that the runtime needs both sparse compaction and a
  dense bottom-up path.
- The automatic `0.35` threshold separates this frozen workload perfectly: the
  maximum sparse dirty fraction is 22.523%, versus a 61.818% minimum for the
  factorized-dense family. This large unsampled middle means the threshold is a
  control, not a learned or optimized crossover.
- Adding the current fixed raise increases mean numeric topology from 362.10 to
  539.35 nodes without materially increasing sparse dirty fractions. This is
  encouraging but remains too shallow to establish branching-factor transfer.
- `MultiSizeRiverHoldem` now provides exact sized actions, three configurable
  opening bets, per-bet minimum-raise filtering, multiple raise-to sizes, exact
  stack/contribution accounting, and range-separated provenance without
  changing the fixed-size river controls.
- An independent contribution-based audit matches all 68,514 terminal histories
  in the frozen multi-size artifact bit-for-bit. Dynamic best responses also
  match exhaustive pure-response values on the tractable deterministic control.
- The unchanged dependency tape passes 840 matched multi-size transfer checks
  with maximum error `1.42e-14`, zero frozen action mismatches, exact replay,
  and perfect sparse/dense routing.
- Widening from one bet/one raise to three bets/two raises multiplies mean tree
  states `3.625x`, numeric nodes `2.896x`, selectors `3.333x`, and flat bytes
  `2.985x`.
- Sparse locality survives: wide blocker and support changes dirty only 16.493%
  and 14.833% of nodes. The crucial counterweight is absolute work, which grows
  `2.686x` and `2.734x` versus the matched fixed tree despite lower percentages.
- Factorized likelihood updates remain dense at 80.314% of wide nodes. Support-
  change selector flips increase from 1.042 to 3.935 on average, so action
  instability grows faster than the dependency fraction.
- Full-action selective expansion now keeps every 3x2 parent action selectable,
  substitutes exact blueprint continuation values only below unexpanded
  branches, and preserves the blueprint exactly at untouched information sets.
  Full expansion follows the ordinary DCFR trajectory bit-for-bit in tests.
- The first development pilot spans one board, four range families, twelve
  support-preserving targets, four nested masks, three warm strengths, five
  equal-work budgets, and 720 full-universe candidate evaluations. Every
  structural and policy-completion gate passes.
- Partial masks use 38.081%, 58.721%, and 79.360% of full deterministic tree
  states. At `0.1 * payoff_span` warm mass and sixteen full-tree-equivalent
  iterations, however, only the 3x1 partial mask is positive on mean, and the
  full 3x2 mask is decisively best: mean NashConv reduction `0.104489` and
  `7.8824` reduction per million state visits.
- Blind deployment remains unsafe. The best fixed pilot arm harms 4/12 targets,
  and the weakest warm prior permits a maximum NashConv increase of `19.1732`.
  No exact-label no-op gate or warm parameter is promoted.
- Holding warm strength and work fixed, every mask wins at least one target.
  The exact best-mask/no-op ceiling totals `1.86440` NashConv reduction versus
  `1.67320` for full-mask/no-op, an 11.43% optimistic uplift. It justifies a
  causal opportunity dataset, not a scheduler claim.
- The 512-iteration blueprint is not uniformly strong: source NashConv reaches
  `0.0158651` in the correlated family. The next matrix must stop at a declared
  exact source-quality threshold rather than assuming one iteration count is
  comparable across range families.
- The preregistered group-separated matrix contains eleven development board
  groups, 44 contexts, 132 targets, and 2,640 exact candidate evaluations. All
  44 blueprints pass normalized source NashConv `<=1e-5`; none needs the final
  4,096-iteration checkpoint. No validation or test context/range is
  materialized.
- At the primary 32-iteration-equivalent budget, best-mask/no-op reduction is
  `16.82102` versus `14.80649` for full-mask/no-op: a `13.6057%` uplift. All
  eleven groups are positive, although one is effectively zero; the median
  group opportunity is `0.12924`.
- Adaptive opportunity is largest under tight work: relative uplift is 103.55%,
  68.49%, 17.91%, 13.61%, and 3.56% at budgets 4 through 64. This is an exact
  future ceiling, not achieved scheduling.
- Fixed pruning fails. Full `b3r2` wins every leave-one-group-out fixed-mask
  fold and captures none of the adaptive oracle. At budget 32, raw `b1r1` and
  `b2r1` aggregate NashConv reductions are `-72.7261` and `-65.3365`, harming
  59.85% of targets despite exact blueprint continuation leaves.
- The strongest boundary opportunity rank is range-delta L2 probability at
  Spearman `0.37555`, with the same sign in every group audit. The paid shallow
  probe is weaker (`-0.27811` best absolute rank) and costs 27.75 ms end-to-end
  in the serial Python control versus 2.00 ms for boundary features.
- Exact no-op plus near-full `b3r1` and full `b3r2` retains 85.03% of the
  four-mask oracle in a post-result diagnostic. This informs the next compact
  screen but is not a selected rule.
- The compact causal screen freezes 18 depth-one/two tree specifications before
  fitting and evaluates each by leave-one-board-group-out training. Fixed full
  search wins the declared normalized-quality objective; no adaptive rule is
  frozen and no fresh replication or reserved context is authorized.
- The closest normalized tree gains 16.10% raw reduction, 77.39% raw
  reduction/ms, uses 38.11% less state work, and lowers worst target harm, but
  loses 1.740% normalized quality and improves only 4/11 groups. The raw-best
  tree gains 25.94% raw chips while losing 5.690% normalized quality.
- This is a real objective conflict, not a timing-only rejection. The causal
  features identify high-pot efficiency trades but do not transfer stable
  strategy-quality improvement across board groups. ADR-0044 stops adaptive
  width on the current workload without retuning.
- Exact-label acceptance of full candidates remains an optimistic clue: it
  raises raw reduction from `8.81632` to `14.80649` while adding 6.44% Python
  time, improving raw reduction/ms 57.79%. It is a teacher, not a deployable
  gate.
- Payoff-scale and selector property audits now guard the measurement path.
  DCFR strategy, exact river strategy, payoff-normalized NashConv, and causal
  selector decisions remain invariant at 0.5x, 1x, 2x, and 4x utility scales.
  The real 132-target artifact also retains fixed `b3r2`, normalized reduction
  `0.39752103705623065`, and its failed-screen status after every scale transform
  and a seeded input permutation. This ruled out unit and order artifacts, but
  the later denominator-semantic finding below supersedes the stronger claim
  that it fully validated the rejection.
- Exact behavioral-policy inputs now share one Float64 dependency at every
  information-set/action pair. Policy-only, range-plus-policy, multiplayer
  unilateral BR, source-relative replay, invalid-profile, tie, and payoff-scale
  controls all pass; 276 automated tests pass in 49.573 seconds.
- The frozen 264-candidate policy-delta matrix reproduces every prior label
  exactly, agrees with full evaluation within `8.88e-15`, and has zero action or
  acceptance mismatches. Hot evaluation is `5.96x` faster than the object-tree
  evaluator.
- Exact acceptance improves payoff-normalized quality/ms by 31.47% over blind
  full search. Compilation charged once still improves 24.01%, but is 0.66%
  slower than simply using the ordinary exact evaluator. Policy-tape value
  therefore requires precompilation or reuse.
- Realistic policy deltas are mostly dense: the full candidate has median dirty
  fraction 81.42% and automatic sparse execution on only 16.67% of targets.
  Dense flat evaluation, not sparse invalidation, is the demonstrated win.
- Interpreting the new artifact exposed a measurement bug in the prior width
  screen: it normalized by the narrow range game's payoff span, while the
  searched 3x2 game has a different span. Their ratio varies from 1.25x to
  3.33x, so ADR-0044's normalized selector result requires a frozen correction
  audit. Scale invariance could not detect selection of the wrong denominator.
- The frozen correction audit mutates exactly those 132 denominator fields,
  matches independently regenerated wide-game spans exactly, and reproduces
  the original screen with zero error. Corrected-to-old span ratios take four
  values from 1.25x through 3.33x.
- With the corrected objective, the unchanged grouped screen selects a single
  split on `range_delta_changed_deal_fraction`: no-op at or below
  `0.14835164835164835`, otherwise full `b3r2`. It selects 63 no-ops and 69 full
  searches and passes every original gate.
- Out of fold, the fixed procedure improves normalized reduction 9.47%, raw
  reduction 41.31%, and raw quality/ms 172.55%; uses 49.49% fewer state visits;
  lowers maximum target harm 91.87%; and improves seven of eleven groups. These
  are revealed-development results, so fixed full remains incumbent until a
  fresh replication passes.
- The fixed threshold then fails its preregistered fresh replication across 23
  new development groups, 92 contexts, and 276 targets. It loses 1.11% raw and
  2.28% normalized quality and improves only 6/23 groups, despite halving work
  and increasing raw quality/ms 84.21%. It is rejected without retuning.
- Changed-deal fraction separates all dense factorized updates from sparse
  blocker updates but cannot rank the sparse slice: the 125 skipped fresh
  candidates contain 83 improvements and 42 harms with net positive value.
- Exact post-solve acceptance does transfer. It raises fresh raw reduction
  18.09% and, even with ordinary exact-label cost, raises raw quality/ms 10.75%.
  Full search plus exact verification is now the conservative heads-up control.
- The ADR-0052 exact multiway river contract is implemented for two through six
  players, with three players as the primary teacher workload. It includes
  exact joint ranges/card removal, cyclic one-bet response order, multiway ties,
  per-player unilateral metrics, shared-private-information pair-coalition
  responses, and separate unilateral-Pareto and coalition-stress labels.
- Twenty-four new contract tests cover every three-player terminal history,
  independent payoff and pure-policy oracles, singleton-team equivalence,
  pair-team enumeration, information hiding, payoff scaling, and unchanged
  generic range/policy dependency tapes. The complete suite passes 313 tests in
  50.440 seconds.
- A reproducible revealed cost calibration passes at `9.33e-15` maximum exact
  error with zero best-response action mismatches. At three hands per seat (27
  joint deals), full unilateral evaluation costs 35.80 ms, all pair coalitions
  36.57 ms, one DCFR iteration 13.00 ms, tape compilation 25.43 ms, and hot
  dense candidate evaluation 5.75 ms.
- Hot dense policy evaluation is 5.79x-6.57x faster across one to 216 joint
  deals. But states, memory, and latency are linear in explicit joint deals;
  independent three-player support grows cubically in hands per seat. Explicit
  joint enumeration is now classified as an exact teacher, not a scalable
  six-player representation.
- The frozen first multiplayer strategy matrix completed from clean commit
  `896f82a`: six development groups, 24 contexts, 96 range shifts, and 1,728
  full-search candidates. All 24 source blueprints passed at iteration 128,
  maximum normalized NashConv was `0.000644255`, and no reserved context was
  materialized.
- Ordinary and compiled evaluations agree within `1.95e-14`, with zero
  best-response action mismatches. Hot candidate evaluation is `6.02x` faster,
  and compile plus two hot candidates is `1.77x` faster than two ordinary
  evaluations. The complete suite now passes 325 tests in 57.855 seconds.
- Primary DCFR-32 aggregate acceptance removes 18 harmful deployments and
  raises raw reduction 4.82%, but its fresh-compile one-shot rate falls 3.30%
  below blind search. This sole failed primary hypothesis keeps the overall
  frozen gate false. Precompiled and amortized diagnostics improve rate 3.30%
  and 2.91% respectively but cannot rescue the preregistered failure.
- Per-player and pair constraints are active rather than ceremonial. Only
  36/96 primary candidates pass unilateral Pareto and 10/96 pass coalition
  stress, both above their frozen acceptance thresholds and with positive
  retained quality. Forty-two of 78 aggregate improvements worsen at least one
  seat; 26 of 36 unilateral-Pareto candidates worsen at least one pair.
- Strict-arm value is concentrated in three-way correlation shifts: they
  supply 97.80% of unilateral-Pareto and 93.73% of coalition-stress raw
  reduction. Single-seat blocker reweights rarely improve without shifting
  vulnerability elsewhere. Aggregate NashConv alone is rejected as the
  multiplayer deployment constraint.
- Post-label diagnostics put the best pooled one-shot accepted rate at LCFR-4,
  while DCFR-8 beats its blind rate in five of six groups. No checkpoint is
  selected: group behavior is inconsistent and DCFR-32 remains the failed
  frozen primary. The early rate peak becomes opportunity-trace evidence only.
- Exact source-compiled range-plus-policy reuse now reproduces all 1,728 frozen
  candidates at `1.95e-14` maximum error, zero action mismatches, zero
  acceptance-label mismatches, and zero call-order replay error after
  intervening range and policy calls. All 329 tests pass.
- Compiling 24 source tapes instead of 96 target tapes cuts the complete
  evaluator path from 9,356.704 ms to 8,504.023 ms, a `1.1003x` speedup, and
  reduces persisted contiguous tape bytes exactly fourfold. It wins 23/24
  individual context paths, not all 24.
- The gain is compilation reuse, not sparse propagation. Combined range/policy
  updates are 3.04% slower than policy-only target updates; their median dirty
  fraction is 94.46%. Dense evaluation remains the reference mechanism.
- Precompiled source verification raises primary DCFR-32 raw quality/ms 2.06%
  over blind. Fresh compilation reaches pooled break-even after four reuses,
  but the margin is only 0.29%; four-reuse rate wins just 2/6 groups. Source
  reuse is adopted as an exact scaling primitive, not a deployable timing rule.
- The exact public-tree quotient passes all frozen gates across 19 revealed
  games and 57 profiles. Maximum error is `2.13e-14`, with zero unilateral
  response-action, schema, public-topology, or numeric-layout failures.
- On the 343-deal row, one 25-node public tree evaluates the full three-player
  profile in `0.5028` ms: `173.07x` faster than the generic compiled tape and
  `1180.46x` faster than ordinary traversal. Compilation is `56.03x` faster.
- Persistent quotient tensors use 114,276 bytes, `1.639%` of the tape's
  6,970,924 runtime bytes. Including estimated hot scratch raises the quotient
  numeric footprint to `5.54%` of that tape control.
- The result is structural reuse, not belief compression. A revealed
  six-player/three-hand diagnostic still has 385 public nodes, 729 joint deals,
  22.5 MB of persistent-plus-scratch numeric tensors, and a 24.177 ms Python
  full-profile cost. Explicit joint support remains the active blocker.
- Exact factorized-card beliefs now pass 40 closure cases. One- and three-
  component nonnegative mixtures remain exact through repeated public action
  likelihoods and hero-hand conditioning: full-distribution error is at most
  `2.22e-16`, with zero support mismatches or impossible-card mass.
- Six-player meet-in-the-middle partition-plus-marginal contraction beats
  recursive enumeration `3.666x` at ten hands per seat, but loses at four hands
  and is roughly tied on the seven-hand blocker case. A cost crossover is real.
- At 32 hands per seat, the exact factor belief uses 6,168 numeric bytes versus
  8.59 GB for a dense `32^6` probability tensor. It contracts 158-275 million
  compatible assignments through at most 50,535 half-records, but still costs
  4.23-4.89 seconds per Python split and builds 309k-372k incidence entries.
- Routine poker belief storage and Bayesian updates therefore do not require a
  neural or signed low-rank model. The active combinatorial target is the
  showdown/counterfactual value operator, plus a native cached contraction.
- The frozen signed showdown-operator screen now passes. Sixty-four terminal
  payoff types are gathered into the literal public tree with zero error; the
  untruncated TT control has `6.91e-11` operator error, `6.66e-14` root error,
  and zero response-action mismatches.
- Rank 8 is the sole safe arm across both hand geometries, one- and three-
  component exact beliefs, and uniform/dense/pure policies. It has zero action
  mismatches and `2.23e-15` maximum normalized root error.
- Rank 8 uses `19.531%` of four-hand dense grouped-operator bytes (`5.12x`
  smaller) and `6.976%` at five hands (`14.33x` smaller). Its cap exceeds all
  observed numerical ranks, whose maximum bond rank is seven.
- Rank 4 is decisively unsafe despite using only `7.031%` of dense storage: it
  flips seven responses and reaches `0.9702%` normalized root error. Tensor MSE
  again fails as a sufficient representation selector.
- Direct factor–TT contraction passes all frozen gates. It matches reconstructed
  TT expectations within `3.38e-14`, compatible partitions within `2.22e-15`,
  and synthetic enumerated-joint controls within `1.39e-16`.
- The cached hot pass is `247.12x` faster than explicit joint enumeration at ten
  hands per seat (`6.300` versus `1556.741` ms pooled median). The exact card
  topology, belief partition, and signed operator table are separately reusable.
- At 32 hands, one rank-8/three-component operator costs `274-312` ms and peaks
  at `68.4-78.2` MB, or at most `0.91045%` of one dense 8.59 GB operator. This
  passes but is too costly to repeat naively across 64 payoff groups.
- Rank 8 ceases to be exact on the preregistered seven-hand extension: maximum
  literal scalar expectation error is `6.64e-05`, versus Float64 noise at four
  and five hands. Wider rank selection remains open and must use root/actions.
- Bottom-up fixed-policy root TT composition is implementation-exact: terminal
  error is at most `7.31e-10`, exact root tensor error `3.30e-11`, exact utility
  error `3.09e-13`, and quotient disagreement `2.66e-15`.
- Its compressed-arm hypothesis fails. Rank 8/16/32 maximum normalized utility
  errors are `1.0478%`, `0.3047%`, and `0.06342%`, versus the frozen `0.01%`
  gate. Rank 16/32 also exceed the `25%` small-axis storage ceiling.
- Public-policy elimination, not terminal payoff, causes rank growth. Maximum
  terminal rank is ten, while exact root middle ranks reach 26 for uniform, 75
  for hashed-pure, and 202 for hashed-dense policies.
- Incremental policy-delta TT recomposition is exact. Across 120 candidate/player
  rows it matches cold roots bit-for-bit, stays within `2.84e-13` of dense
  utilities, has zero propagated-bound or six-seat zero-sum violations, and
  produces zero wrong signs for 120 guarded fixed-policy utility deltas.
- Seat-3 profile edits change 32 strategic nodes and dirty the union of 63
  public nodes. Raw recomposition is `2.54x-2.68x` faster at four hands but only
  about `1.20x` at seven, despite skipping 129 of 192 strategic nodes. Upper-
  tree TT rounding, not dirty discovery or memory, dominates the wider axis.
- The frozen four-reuse unilateral economics gate fails: pooled charged
  incremental time is `4825.328 ms` versus `4785.817 ms` cold, or `0.99181x`.
  Both seven-hand rows are about 8% slower after the charge. Every case breaks
  even by seven reuses and passes the reported eight-reuse point, but the
  frozen four-reuse result is not promoted.
- Six baseline player caches peak at 48.20 MB of numeric storage and a live
  baseline/candidate pair at 94.55 MB. Cache capacity is not the current wall.
  Fixed-policy sign guards remain explicitly unauthorized for best-response,
  Pareto, coalition, NashConv, or equilibrium claims.
- At seven hands, recomputing only the root costs 17.09%-19.75% of cold, while
  one 11-node root-to-leaf closure costs 69.13%-72.01%. Cost-weighted dirty
  closure, not node fraction, becomes a required statistic. Recorded root
  middle ranks grow from 53-64 at four hands to 106-244 at seven.
- The policy-delta successor moves candidate evaluation to a no-rounding scalar
  read path over cached clean-fringe TTs. Candidate and baseline reaches are
  compared on one public cutset; its simple shared-fringe error bound is at most
  twice the largest used cache bound. Rounding occurs only after acceptance on
  the baseline write path. Fringe contraction count remains an unmeasured cost.
- Exact structured showdown automata now pass all twelve frozen gates across
  4,608 builds. Complete four/seven-hand automaton, direct-TT, and zero-sum
  errors are exactly zero; deterministic transition mismatches are zero.
- The added wide literal-assignment oracle independently agrees within
  `4.44e-16` on every six-seat payoff over 4,096 assignments per terminal
  group. Wide sampled zero sum is `1.78e-15`; no wrong-winner bug is hidden by
  conservation alone.
- At 32 hands, the largest sparse automaton is only 97,048 bytes and all 384
  group/target objects total at most 10.39 MB, versus one 8.59 GB dense payoff
  tensor. Maximum reachable state rank is 187. Building 384 objects takes
  499-552 ms in Python, or 1.30-1.44 ms each on average.
- Strength sorting preserves every unfolding spectrum within `9.83e-14` and
  never increases transition runs. Balanced axes were already strength-
  monotone; blocker-heavy 32-hand sorting reduces transition runs 13.08% but
  does not reduce uncompressed bytes or reliably improve build time.
- The 384 logical objects collapse to 193 executable winner topologies, but
  sharing saves only about 6.9% of numeric bytes at 32 hands because distinct
  active-target tables dominate. Sparse construction, not deduplication, is the
  primary terminal win.
- The automaton is scoped to the equal-stack, one-bet no-side-pot tree. It
  removes the selected-32-hand dense terminal blocker, not public-policy rank,
  full-board hole-card width, conditional actions, or best-response cost.
- Exact public-tree tensor CFR now matches the recursive solver's current and
  average policies, every regret, and every average accumulator for CFR, LCFR,
  CFR+, and DCFR, including a six-player control. The complete suite passes 398
  tests.
- The canonical own-axis real-policy artifact passes all seven frozen gates
  from clean commit `40c4205`. Its SHA-256 is
  `cdcae48dcca5fd1447fd5ad33426a4b20f04e098c88897d8f0f6eddb797ef36e`;
  46 policy tables replay bit-identically, maximum BR target-value error is
  `1.09e-14`, and maximum zero-sum residual is `1.96e-14`.
- Finite source quality improves from uniform NashConv `13.69-14.38` to
  `0.0119-0.0148` at h4 checkpoint 256 and `0.124-0.149` at h7 checkpoint 64.
  This is metadata, not a convergence or checkpoint-selection gate.
- Real average policies remain structurally rich: last-checkpoint objects have
  744-757 distinct action distributions at h4 and 1,318-1,329 at h7, with no
  exactly pure information sets. Whether poker-aligned variation compresses is
  now an open measurement rather than an assumed average-policy advantage.
- ADR-0076 freezes the combined real-policy representation and clean-fringe
  audit against the immutable source SHA before observing any canonical-policy
  rank or evaluator result. It covers 126 rank rows, all ten 3/3 partitions,
  134 whole-seat candidates, and compile/marginal/reuse bills for three
  evaluators without a small-axis speed gate.
- The clean-fringe successor evaluates fixed-policy utility deltas with no
  candidate-time TT rounding. Its certificate is `2 * max(frontier bound)`
  plus a separate Float64 allowance; candidate reach above overlapping edits
  is verified against dense and scalar oracles.
- Historical source modules are again byte-identical to their frozen hashes.
  Batched weighted contraction and per-node profiling live in additive modules,
  and the complete pre-freeze suite passes 405 tests.
- ADR-0076's first run stopped in 0.331 seconds before any root composition or
  rank because the regenerated factor axes used generator order while the
  source artifact serialized each seat's hands in canonical layout order. No
  v1 result artifact was written and no representation result was revealed.
- ADR-0077 freezes an additive order-only correction. Sorting within each seat
  while carrying every unary column preserves exact game provenance and the
  compatible-deal counts on all four geometries; the ADR-0076 workload and
  gates remain byte-frozen.

## In progress

- ADR-0073 was superseded before execution: no three-hand source, lifted policy,
  rank, utility, or result was produced.
- ADR-0074's canonical source passed; ADR-0075 freezes its artifact SHA and
  interpretation without observing any policy TT rank.
- The exact public-tree tensor solver matches `TabularCFR` policies, regrets,
  and average accumulators for all four update rules and a six-player control.
  Revealed source-only calibration costs 23-29 ms per h4 iteration and 194-350
  ms per h7 iteration, removing the premise for coarse-axis policy lifting.
- ADR-0077's corrected ADR-0076 runner is frozen and ready to run. It will
  compare crown rank versus
  checkpoint and charge clean-fringe, TT recomposition, and flat compatible-
  deal evaluation with compile, marginal, and break-even bills.
- Treating response actions and per-player deviation vectors, rather than
  probability reconstruction or leaf MSE alone, as representation gates.
- Separating online value/action contraction from offline all-player response
  certification so the latter is not charged to every decision.
- Preserving per-player deviation vectors through contraction; coalition gains
  remain offline stress labels with separately visible cost.
- Keeping the early-checkpoint opportunity as a causal-trace target, not a
  post-hoc solver or stopping-rule selection.

## Next three tasks

1. Run the axis-corrected frozen representation/read-path screen, record rank-versus-checkpoint
   before interpreting evaluator speed, and accept or reject each product on
   its own declared gates.
2. If the scalar path has credible scaling, expose conditional hand/action
   values and exact response-action gates without charging all-player BR work to
   every online decision.
3. If no transferable representation passes, retain an explicit public-state
   bond; then expose conditional action values and exact response-action gates.

## Current blockers

None.

## Required reading before continuation

1. `PROJECT.md`
2. `STATUS.md`
3. `ROADMAP.md`
4. Relevant records under `docs/decisions/`

## Last updated

2026-08-20, after ADR-0077 corrected a pre-rank source-axis ordering mismatch
without changing ADR-0076's workload, gates, or accounting.
