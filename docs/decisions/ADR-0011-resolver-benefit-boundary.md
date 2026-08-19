# ADR-0011: Resolver benefit requires compositional evidence

**Status:** Accepted 2026-08-19.

## Decision

Do not freeze a v2 search selector from the current local-model benefit
signals. Treat blueprint local regret, progressive probe behavior, local-model
gain, and policy movement as diagnostics until the exact laboratory evaluates a
complete continual-resolving policy rather than one searched prefix merged into
blueprint continuation.

Keep the selector decomposition from ADR-0010:

```text
deploy only if
  conservative resolver-benefit estimate
  - leaf/root-harm upper bound
  - latency opportunity cost
  > 0
```

Policy displacement may enter the benefit estimate as a compositional-risk
penalty. It is not itself evidence of improvement. A post-search acceptance
gate may use candidate diagnostics to prevent deployment, but those diagnostics
cannot recover computation already spent. Progressive probes must be snapshots
of one preemptible solve, not independently recomputed searches.

## Evidence

EXP-0009 used exact blueprint continuation leaves, so leaf error was zero. Full
local-model gain nevertheless authorized 70/72 two-player candidates, 38 of
which harmed the full game. In three-player Kuhn it authorized 63/72, including
40 harmful candidates, and rejected three beneficial candidates.

Local gain divided by mean information-set total variation ranked candidates
well in Kuhn2 (AUC 0.968) and moderately in Kuhn3 (AUC 0.686), with combined AUC
0.855. This is useful evidence that magnitude of policy departure matters, but
not enough evidence for a threshold. Short-probe slopes and extrapolations
changed direction between the two games.

Exact continuation values preserved the expected utilities of every tested
merged policy between the depth-limited model and full game. The mismatch came
from deviations: the full-game best responder could change play beneath the
frontier, while the local responder inherited a fixed continuation value.

## Opposing evidence

- Gain per policy movement is substantially better than random ranking and may
  become adequate after conditioning on public state, depth, player count, and
  calibrated uncertainty.
- A complete continual resolver is more expensive to implement and evaluate
  than a root-only merge.
- Kuhn poker is too small to establish how severe the same composition gap will
  be in reduced or full hold'em.
- A conservative post-search rejection gate could still reduce harm before the
  complete resolver exists, even though it cannot improve current-decision
  compute efficiency.

## Consequences

The next architecture experiment implements a complete small-game resolver and
compares it with the current prefix-only merge under exact leaves. Benefit
signals are then rerun against that policy. Full neural leaf training remains
behind this gate: reducing value error cannot repair a resolver whose local
objective is compositionally misaligned.

The trajectory analyzer remains in the measurement system, but no selected
feature, fitted classifier, or threshold is promoted. Any later v2 rule must be
preregistered on development games and tested on hidden player counts,
blueprint strengths, depths, and resolver variants.

## Cheapest falsifying experiment

In two- and three-player Kuhn, resolve every reached public decision with exact
blueprint continuation values, compose the resulting policy consistently, and
compare local predicted gain with exact full-game NashConv. If harmful sign
reversals remain common, add safe subgame/frontier constraints or opponent
counterfactual-value ranges before revisiting scheduling.

## Kill criterion

Do not invest in learned benefit scheduling if complete-resolver candidates do
not produce a stable benefit target or if their deployable features fail to
rank positive outcomes above 0.7 AUC on held-out exact games where both outcome
classes occur. Passing that screen still requires a preregistered improvement
in strategy quality per millisecond over no-op, unconditional search, and the
best heuristic. Retain the blueprint/no-op fallback.
