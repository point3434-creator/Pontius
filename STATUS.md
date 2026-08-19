# Project Status

## Active checkpoint

Checkpoint 2: solver comparison laboratory.

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
- One hundred sixty-seven automated tests pass.

## In progress

- Designing the smallest exact sequential river raise game that makes one
  player act twice without making its independent normal-form teacher
  intractable; validation and test boards remain unsolved.
- Extending the structured protocol to heteroscedastic and time-varying errors.
- Reducing evaluation overhead through configurable cadence and future
  restricted responders.

## Next three tasks

1. Add one fixed raise response and a final fold/call decision to the exact
   river tree; verify the normal-form teacher on two-to-four-hand ranges.
2. Re-run causal opportunity traces and test whether accumulated-regret ranking
   survives after local one-step regret no longer equals complete NashConv.
3. Add paired near-range blocker perturbations and measure exact-hit,
   structural-only, warm-start, and recertification costs separately.

## Current blockers

None.

## Required reading before continuation

1. `PROJECT.md`
2. `STATUS.md`
3. `ROADMAP.md`
4. Relevant records under `docs/decisions/`

## Last updated

2026-08-19, after the 1,024-context production trace replicated the regret
signal but exposed its shallow-tree exact-regret confound.
