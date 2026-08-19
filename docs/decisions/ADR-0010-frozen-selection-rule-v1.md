# ADR-0010: Frozen counterfactual-risk selection rule v1

**Status:** Frozen before holdout, 2026-08-19.

## Decision

Pre-register the first search-versus-blueprint rule before inspecting any
outcome in its holdout grids. The only candidate is the average policy from
100 iterations of LCFR with an in-search blueprint weight of 0.99. The rule is:

```text
search if max_player_counterfactual_root_L2 <= 2.0e-4
otherwise use the blueprint unchanged
```

The complete machine-readable rule is
`experiments/rules/counterfactual-risk-v1.json`. Its digest covers the entire
document, including derivation and holdout gate. Candidate configuration is
validated against every evaluated run. The pre-holdout SHA-256 digest is
`c6271e3a00d44ed9777d197914f86ff08e654ad7ead90db9ff3e345d4f96208d`.

## Information boundary

The rule may see only its declared candidate and the largest player-specific
counterfactual root-L2 uncertainty proxy. It may not see full-game NashConv,
best-response utility, the oracle no-op label, or any holdout outcome.

The exact lab currently supplies realized error, which makes this an optimistic
oracle-uncertainty experiment. A deployable rule would require a calibrated
upper bound predicted before search. Search-time savings also exclude future
model inference and uncertainty-estimation cost.

## Derivation

Five EXP-0007 matrices yielded 773 unique LCFR/0.99 development cases after
deduplication by complete configuration. A threshold of `2.0e-4` selected 312
cases and no observed failure. Their mean candidate NashConv change from the
blueprint was `-1.35876e-4`; the worst was `-5.29479e-5`. The first observed
failure occurred at risk `2.55823e-4`, leaving a 21.8% threshold margin.

This is deliberately a one-feature round threshold rather than a fitted model.
It will expose whether the feature and absolute scale transfer at all before we
spend complexity on benefit prediction or learned scheduling.

## Holdouts

The two-player grid changes blueprint strength to 50, 300, and 3,000 LCFR
iterations, includes depths one and two, uses unseen seeds 100-109, and uses
interleaved error targets. The three-player grid uses 300 and 1,500 blueprint
iterations, depths two and three, and unseen seeds 100-104. Both vary concrete
versus public correlation and error location.

The rule advances only if it searches at least 10% of cases, makes no harmful
or tied selection, improves mean NashConv overall, has nonpositive mean harm in
every game/blueprint/depth subgroup, and improves NashConv per reference search
millisecond over unconditional search. Any failure is recorded before a v2 rule
is proposed; v1 is never retuned in place.

## Opposing evidence

- The threshold is fitted to one strong two-player depth-two blueprint.
- Counterfactual root L2 was not monotone with strategy harm in development.
- Absolute uncertainty scale may not transfer across blueprint strengths or
  player counts.
- A risk-only gate cannot detect whether exact-leaf search has negative value.
  Depth-one holdout cases are an intentional test of this weakness.
- Real neural uncertainty may be biased or miscalibrated, making this oracle-
  error result optimistic even if it passes.

## Kill criterion

Reject v1 if it violates any preregistered advance gate. Preserve its rule file
and digest. A successor must explain the failure using only development or
reported holdout analysis and receive a new versioned preregistration.
