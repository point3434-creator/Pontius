# ADR-0045: Adopt payoff-scale and selector invariance guardrails

**Status:** Accepted

**Date:** 2026-08-19

## Decision

Require positive payoff rescaling and data-order invariance checks around the
measurement path before optimizing policy-delta recertification. Keep these as
measurement guardrails; they do not reopen the adaptive-width selection made in
ADR-0044.

The automated checks cover utility scales `0.5`, `1`, `2`, and `4`. For a
strategically identical game they require:

- identical DCFR behavioral strategies at equal iterations;
- raw utilities and NashConv to scale with the payoff multiplier;
- NashConv divided by payoff span to remain invariant;
- the exact river oracle's equilibrium strategy to remain invariant when pot,
  stack, bet, and raise amounts scale together; and
- the causal selector's fitted trees, arm choices, normalized quality, and gate
  decisions to remain invariant when raw labels and payoff spans scale together.

Selector property checks additionally cover repeat execution, target and record
permutation, arbitrary board-group renaming, ignored future-label fields,
explicit tie behavior, and rejection of an actively requested forbidden
feature.

## Evidence

All 266 automated tests pass in 48.598 seconds on the development machine.

The DCFR scale test runs 256 iterations at each scale. Action probabilities
match the scale-one control within `1e-14`; raw NashConv scales within `1e-12`,
and payoff-normalized NashConv matches within `1e-14`.

The exact raised-river control scales pot, both stacks, bet size, and raise-to
together. Its equilibrium value scales and its behavioral policy matches the
scale-one solution within `1e-11`. A deliberately non-equilibrium uniform
profile's raw NashConv scales within `1e-11`, while NashConv divided by the
game's payoff span matches within `1e-13`.

A one-time audit also refit all eighteen frozen selector specifications across
the real 11-group, 132-target development artifact at all four payoff scales,
then once more after a seeded permutation of targets and records. Every run
retained `fixed_b3r2`, retained status
`development_screen_failed_retain_full_b3r2`, and retained fixed normalized
reduction `0.39752103705623065`. Every candidate's normalized result and arm
counts were unchanged within `1e-12`.

## Interpretation

The attractive raw-versus-normalized conflict in ADR-0044 is not an artifact of
chip units, target ordering, group names, or an unspecified tie. The compact
selector still fails. This increases confidence in the measurement system, not
in adaptive width.

Measured tree-evaluation wall time is intentionally excluded from numerical
equality assertions because operating-system timing noise is not invariant.
The tests preserve the declared timing inputs and require the resulting gate
decision to remain unchanged. Positive scaling is the strategic symmetry under
test; additive utility shifts, negative scaling, and arbitrary changes to only
one stake parameter are not equivalent games.

## Next gate

Proceed with the preregistered policy-delta tape experiment. Apply these same
scale, order, and tie checks to its full-versus-incremental acceptance decisions,
with Float64 error and false-accept/false-reject gates taking precedence over
speed.

## Subsequent correction

ADR-0047 found that the selector's `target_payoff_span` came from the narrow
range-context game rather than the searched 3x2 multi-size game. Positive scale
invariance did not and could not detect that semantic mismatch because both
denominators scale linearly. The invariance tests remain valid guardrails, but
the claim above that they validate ADR-0044's normalized selector comparison is
superseded pending a frozen denominator-correction audit.

ADR-0049 completed that audit: the corrected denominator changes the selected
procedure and makes the unchanged screen pass. Scale and order invariance remain
required guardrails, but they are not evidence that a metric refers to the
right underlying game.
