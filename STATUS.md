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
  are reused across matrix runs. Fifty-eight automated tests pass.
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

## In progress

- Defining a conservative uncertainty/benefit-to-anchor-or-no-op rule without
  fitting it to the held-out multiplayer cases.
- Extending the structured protocol to heteroscedastic and time-varying errors.
- Distinguishing prefix-policy improvement from a complete resolver applied at
  every public state, before interpreting full-game strength.
- Reducing evaluation overhead through configurable cadence and future
  restricted responders.

## Next three tasks

1. Freeze an uncertainty-to-anchor/no-op rule on two-player cases and falsify it
   on three-player Kuhn, different depths, and held-out blueprint strengths.
2. Define and evaluate a complete small-game continual-resolving policy rather
   than only a searched prefix merged into blueprint continuation.
3. Add heteroscedastic/time-varying errors and adversarial branch targeting;
   compare the frozen rule with unconditional search and permanent no-op.

## Current blockers

None.

## Required reading before continuation

1. `PROJECT.md`
2. `STATUS.md`
3. `ROADMAP.md`
4. Relevant records under `docs/decisions/`

## Last updated

2026-08-19, after EXP-0007 established structured reach-weighted error controls.
