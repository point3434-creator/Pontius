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
  leaf error to full-game NashConv and policy change. Forty-four automated tests
  pass.
- EXP-0005 rejected naïve unanchored shallow replacement: with exact leaves it
  worsened a strong two-player blueprint by about 0.087 NashConv. A mass-10
  pseudo-regret prior attenuated the effect but behaved very differently across
  update rules and never improved the blueprint.

## In progress

- Designing a variant-neutral blueprint anchor, residual update, and explicit
  no-op acceptance path before attempting deeper resolving.
- Extending leaf errors from independent concrete histories to reach-weighted,
  correlated, biased, localized, and time-varying regimes.
- Reducing evaluation overhead through configurable cadence and future
  restricted responders.

## Next three tasks

1. Compare output interpolation and in-search anchoring against the blueprint,
   with the no-op action included and exact-leaf safety as the first gate.
2. Add blueprint-reach and counterfactual-reach-weighted error metrics plus
   correlated, biased, and localized perturbations.
3. Repeat paired experiments across blueprint strength, search depth, and
   three-player Kuhn before choosing an online update rule.

## Current blockers

None.

## Required reading before continuation

1. `PROJECT.md`
2. `STATUS.md`
3. `ROADMAP.md`
4. Relevant records under `docs/decisions/`

## Last updated

2026-08-18, after EXP-0005 rejected naïve unanchored shallow replacement.
