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
- Ninety-eight automated tests pass.

## In progress

- Designing an exact constrained/max-margin oracle to separate safe-strategy
  quality from finite-CFR convergence error.
- Extending the structured protocol to heteroscedastic and time-varying errors.
- Reducing evaluation overhead through configurable cadence and future
  restricted responders.

## Next three tasks

1. Build an exact small-game constrained/max-margin strategy oracle for the
   same opponent frontiers and use it to measure achievable safe improvement.
2. Compare CFR gadget convergence and one-sided stopping against that oracle;
   test whether warm starts or margin objectives improve quality per millisecond.
3. Inject controlled frontier-value error and uncertainty bounds before
   declaring any multiplayer relaxation or neural frontier target.

## Current blockers

None.

## Required reading before continuation

1. `PROJECT.md`
2. `STATUS.md`
3. `ROADMAP.md`
4. Relevant records under `docs/decisions/`

## Last updated

2026-08-19, after EXP-0011 verified the safe-resolving control and rejected
unguarded finite-residual deployment.
