# Project Status

## Active checkpoint

Checkpoint 1: exact measurement laboratory and reference solvers.

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
  tests.
- At 20,000 sequential reference iterations, CFR reached NashConv `0.00014427`
  in 3.911 seconds and LCFR reached `0.00000859` in 3.917 seconds. Both matched
  Kuhn's analytical player-0 value of `-1/18` within numerical tolerance.

## In progress

- Completing checkpoint C1 with configurable multiplayer Kuhn.
- Designing exact multiplayer best-response tests that remain computationally
  tractable.
- Preparing controlled leaf-error and solver-variant experiments.

## Next three tasks

1. Add three-player and configurable multiplayer Kuhn rules.
2. Verify multiplayer utilities, information sets, and exact deviation gains.
3. Add CFR+, DCFR, and the first controlled leaf-error experiment.

## Current blockers

None.

## Required reading before continuation

1. `PROJECT.md`
2. `STATUS.md`
3. `ROADMAP.md`
4. Relevant records under `docs/decisions/`

## Last updated

2026-08-18, after EXP-0001 and the first verified exact-game baseline.
