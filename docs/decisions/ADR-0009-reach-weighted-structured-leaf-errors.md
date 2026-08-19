# ADR-0009: Reach-weighted structured leaf errors

**Status:** Accepted for C2 measurement, 2026-08-19.

## Decision

Every exact-game leaf intervention reports three distinct error views:

1. uniform error over concrete cutoff histories;
2. error weighted by joint blueprint reach, including both conditional RMSE
   and its root-scaled L2 contribution;
3. per-player error weighted by counterfactual reach, plus an aggregate and the
   largest player-specific root L2.

The experiment can independently vary random-error grouping and location.
`concrete` grouping gives each private history an independent draw;
`public_history` shares a draw across all private histories at one public
boundary. Scopes may include all leaves, either half ranked by joint blueprint
reach, or an exact public action sequence. Explicit player bias is separate
from random error and its effective value after zero-sum projection is reported.

Raw perturbation scale remains available, but matched-structure comparisons
may instead calibrate each realized draw to a requested on-policy root L2. The
report retains the resulting effective raw scale. Calibration is an analysis
control, not a claim that online model error can be rescaled after the fact.

No scheduler may use joint on-policy reach as its only priority or safety
signal. Candidate inputs must preserve at least local uncertainty, per-player
counterfactual reach or sensitivity, error correlation/provenance, and a
minimum-coverage term for rare leaves.

## Reason

Uniform leaf RMSE confounds model accuracy with where an error occurs. Raw
perturbation scale additionally confounds error structure with how much
independent noise averages across a frontier. Separating realized root energy,
correlation, and location makes algorithm comparisons interpretable.

The calibrated depth-two Kuhn experiment also falsified a tempting shortcut.
At equal joint-reach-weighted root L2, concentrating error in the low-reach
half produced much larger counterfactual error and much worse full-game
strategies than concentrating it in the high-reach half. Reach is useful for
cost allocation, but it is not a safety certificate.

## Invariants

- Chance reach and every player's behavior reach are propagated separately.
- Joint reach is their product; player counterfactual reach excludes only that
  player's behavior factor.
- Conditional RMSE is never presented as root contribution without the
  frontier reach mass.
- A calibrated run must realize its requested on-policy root L2 within numeric
  tolerance and report the effective scale used to do so.
- Exact-control and treatment searches still share blueprint, topology,
  solver, budget, and policy constraints.

## Limitations

- The current values remain attached to concrete private histories rather than
  public-belief ranges.
- Depth-two two-player Kuhn has only six cutoff histories and one continuing
  public history. Public-history normalization therefore has very few unique
  error directions.
- Joint and counterfactual reach are measured under a frozen blueprint. Search
  can change reach, and an adversarial responder can target a cold branch.
- These diagnostics describe error; they do not yet provide an online no-op
  rule or uncertainty estimator.

## Revisit condition

Replace concrete-history diagnostics with range-indexed public-belief metrics
when the reduced poker environment exists. Retain the factored-reach,
matched-root-error, and paired full-game evaluation controls.
