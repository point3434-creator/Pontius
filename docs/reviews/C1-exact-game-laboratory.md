# C1 Review: Exact-game laboratory

**Date:** 2026-08-18

**Verdict:** Proceed to C2.

**Confidence:** High that the laboratory is adequate for solver development;
moderate that every multiplayer best-response edge case is independently
validated.

## Supporting evidence

- Twenty-three automated tests pass.
- Two-player CFR and LCFR match the analytical Kuhn value.
- Exact dynamic best response matches complete pure-policy enumeration on two
  materially different two-player profiles.
- Three-player terminal contributions, response order, information-set counts,
  zero-sum utilities, and single-information-set response deviations are tested.
- Reproducible CFR/LCFR experiments report exact NashConv rather than self-play
  utility alone.

## Opposing evidence and limitations

- The dynamic multiplayer best response lacks a second sequence-form
  implementation as an independent three-player oracle.
- Python full-tree traversal is already about 5.4 ms per three-player CFR
  iteration and will not scale to routine six-player training.
- Exact uniform-profile six-player evaluation takes about 106.6 seconds even in
  this tiny game.
- Low three-player NashConv is empirical and does not provide a general CFR
  convergence guarantee.

## Largest unknown

How CFR update variants rank when values are noisy, the tree changes, and the
solver is warm-started under a short wall-clock budget.

## Cheapest falsifying experiment

Implement CFR+ and DCFR as update policies, then inject deterministic leaf
perturbations in two- and three-player Kuhn. If algorithm rankings are unstable
across repeated exact evaluations, the current comparison protocol is
insufficient.

## Kill criterion

Stop optimized or neural work if a second best-response implementation later
disagrees with the current evaluator or if known two-player values cease to be
reproduced after solver refactoring.

## Recommendation

Proceed to C2 while retaining exhaustive two-player best response in regression
tests and scheduling an independent multiplayer sequence-form oracle before
reduced hold'em becomes the primary benchmark.
