# ADR-0007: Paired leaf-error protocol

**Status:** Accepted, 2026-08-18.

## Decision

Leaf-value quality is measured with a paired intervention:

1. Train one blueprint and freeze its average policy.
2. Replace the game below a stated strategic-action depth with exact blueprint
   continuation values.
3. Run a control search with those values and a treatment search with
   deterministic perturbations. All other inputs are identical.
4. Merge only the searched information sets back into the same blueprint.
5. Evaluate both merged policies in the untouched full game.

The causal leaf effect is treatment minus exact-leaf control. Reports include
signed and absolute NashConv change, full-game utility change, and mean and
maximum information-set total variation. The exact control's change from the
blueprint is reported separately: it tests the resolver, not the leaves.

Perturbation scale is not treated as realized error. Every run reports realized
RMSE, mean absolute error, maximum absolute error, and per-player RMSE. Initial
errors are deterministic by seed and centered to preserve zero-sum utility at
each concrete leaf.

A blueprint warm start is an explicitly named pseudo-regret prior with a stated
mass. It is not a safe-resolving guarantee, and equal mass is not assumed to
have equal persistence under CFR, LCFR, CFR+, and DCFR.

## Gate

A proposed online resolver must first survive exact continuation values. If its
full-game strategy is materially worse than the blueprint, further solver
convergence or lower leaf MSE cannot rescue that design. The deployable action
remains the blueprint/no-op until an anchored or otherwise safe update passes.

## Initial limitations

- Leaf values are conditioned on concrete private histories rather than public
  beliefs and ranges.
- Error is independent across concrete leaves; correlated, biased, localized,
  heteroscedastic, and changing errors remain to be added.
- Error RMSE and policy distance are initially unweighted. Blueprint reach and
  counterfactual-reach-weighted metrics remain required.
- Leaves are precomputed before timed search. This isolates traversal cost and
  is a warm-cache result, not an end-to-end latency claim.
- Multiplayer resolving has no safety claim here.

These limitations make the experiment a mechanism and calibration test, not a
neural-value validation result.

## Reason

Comparing a noisy search only with the blueprint confounds leaf error with
resolver bias, early stopping, update rules, and warm-start behavior. A paired
exact-leaf arm isolates the intervention we intend to study and can falsify the
resolver before expensive neural work.

## Revisit condition

Revise the protocol after public-belief range values exist, but retain the
paired full-game evaluation and exact-control gate wherever an exact oracle is
available.
