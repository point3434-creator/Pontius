# ADR-0008: Blueprint-anchored search

**Status:** Provisionally accepted as a C2 control, 2026-08-19.

## Decision

Add two explicit, independently measurable policy constraints:

1. **In-search anchor.** At each information set, traversal uses

   ```text
   behavior = b * blueprint + (1 - b) * candidate
   ```

   CFR optimizes the candidate component. Its instantaneous regret compares
   candidate actions with the candidate's own node value and is scaled by
   `1 - b`. The accumulated average is the behavior actually traversed.

2. **Output interpolation.** After search, optionally deploy

   ```text
   output = (1 - c) * blueprint + c * searched_policy
   ```

   `c = 0` is the explicit no-op and `c = 1` is full replacement.

Both coefficients are configuration, never hidden confidence. Full blueprint
anchoring is invariant to leaves and updates. Partial anchoring bounds each
behavior's total-variation distance from the blueprint by its candidate
component. Neither mechanism is called safe multiplayer resolving.

Current, average, and blueprint/no-op policies remain separate outputs. An
oracle selector based on exact full-game NashConv is recorded only as a
diagnostic upper bound; an online agent does not possess that oracle.

## Verdict

Advance the anchored **average** policy as a reference control. Reject current
policy, unanchored replacement, and output interpolation alone as defaults.
Retain no-op as the deployment fallback whenever estimated leaf error or root
benefit is outside a validated region.

**Confidence:** medium for the mechanism in two-player Kuhn; low for transfer
to multiplayer hold'em.

## Supporting evidence

- A depth-two search can improve a weak or medium blueprint where the depth-one
  hybrid policy could not.
- With a 1,000-iteration blueprint at NashConv `1.87060e-4`, anchored LCFR at
  `b = 0.99` reached approximately `1.76116e-5` with exact leaves.
- Anchored CFR+ at `b = 0.995` improved all ten tested perturbation seeds through
  realized leaf RMSE `1.38657e-4`.
- At nearly equal reference runtime, solver rankings changed with leaf error;
  this supports regime selection rather than a universal CFR rule.
- Reusing prepared blueprints reduced a 490-run matrix to about 41 seconds,
  allowing finer falsification sweeps without changing experiment semantics.

## Opposing evidence

- At realized RMSE `4.62190e-4`, no tested solver/anchor improved every seed.
- At RMSE `1.38657e-3`, no-op beat the tested anchored candidates on mean
  NashConv.
- Every tested current policy worsened the strong blueprint even when its
  average improved.
- Anchor coefficients were selected on the same tiny game used for reporting.
- Errors are independent concrete-history noise, not correlated public-belief
  range-value errors. The favorable threshold may be optimistic.
- The experiment composes only a prefix policy with blueprint continuation; it
  is not yet a complete continual-resolving policy evaluated at every public
  state.

## Largest unknown

Whether an anchor chosen from calibrated range-value uncertainty can predict
when search will beat no-op in multiplayer public-belief states.

## Cheapest falsifying experiment

Add reach-weighted correlated and biased errors, freeze anchor selection on
two-player training cases, and test it without retuning on three-player Kuhn
and different blueprint strengths/depths.

## Kill criterion

Do not advance anchoring toward the optimized runtime if no fixed or
uncertainty-conditioned rule beats no-op on held-out exact games, or if its
worst-seed degradation remains material under the target leaf-error envelope.

## Recommendation

Build error structure and reach weighting next. Then test a conservative
uncertainty-to-anchor/no-op rule. Do not spend on a large neural leaf model until
that rule has a credible target envelope.
