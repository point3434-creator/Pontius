# ADR-0051: Reject the density gate; retain full search plus exact verification

**Status:** Accepted

**Date:** 2026-08-19

## Decision

Reject `river-noop-full-gate-v1` unchanged. Retain always-full `b3r2` as the
causal pre-search control. Do not retune the changed-deal-fraction threshold,
fit another tree, add a rescue feature, or inspect reserved contexts on the
fresh artifact.

Retain exact post-solve accept/no-op as the stronger demonstrated mechanism.
On the fresh workload, even the ordinary full evaluator improves both strategy
quality and quality per millisecond by rejecting harmful completed candidates.
The policy-parameterized tape from ADR-0047 remains the intended cheaper
verification path when compilation can be reused.

The failure rejects one scalar density gate, not computation scheduling in
general. Future causal scheduling must distinguish strategically important
sparse blocker changes from harmless ones; changed support fraction alone does
not do that.

## Frozen evidence

ADR-0050 and the exact rule were committed in `2ae9d3f` before new contexts
were constructed. The runner was committed as
`b131f1bd54a0fc51981fbae4fdfbbd91168d68e9`; all 286 tests passed in 50.400
seconds before the fresh seed ran.

The result artifact is
`experiments/results/river-noop-full-gate-replication-v1.json`, SHA-256
`cfd7aa75ee892167a599361cead39887e622457e2bffa23c1cfae44e03d56448`.
Its canonical config SHA-256 is
`b0d1896fbc51a86382eff24f95cf9ceff328d1f2f2029beaf7395b624c77d7d5`.

The run contains 23 fresh development board groups, 92 contexts, 276 targets,
and 552 `b3r1`/`b3r2` candidates. There is zero board or full-range overlap with
discovery and no reserved context. All 92 source blueprints pass; maximum
searched-game-normalized source NashConv is `9.85493e-6`.

## Result

Always-full `b3r2` achieves raw reduction `44.44799992`, normalized reduction
`0.56861647`, 7,211,520 state visits, `50.313954` seconds, raw rate
`8.83413e-4` per millisecond, and maximum target harm `0.93862094`.

The frozen rule chooses full search 151 times and no-op 125 times. It uses
3,795,904 state visits and `27.011515` charged seconds, but achieves raw
reduction only `43.95622873` and normalized reduction `0.55566767`.

Relative to fixed full, it:

- loses `0.49177119` raw reduction, or `1.10640%`;
- loses `0.01294879` normalized reduction, or `2.27725%`;
- improves raw reduction per millisecond by `84.2077%`;
- reduces state visits by `47.3633%` and time by `46.3141%`;
- leaves maximum target harm unchanged; and
- improves only six of 23 board groups, or `26.0870%`.

Its compact-oracle opportunity capture is `-4.68497%`. The raw,
searched-game-normalized, positive-group, and opportunity-capture gates fail.
Freshness, blueprint quality, arm balance, work, rate, and no-worse-maximum-harm
gates pass. The joint verdict is failure.

## What failed

All 92 factorized-dense targets exceed the threshold and are searched; they
contribute `43.28` raw reduction. The decision error is concentrated in the 184
sparse blocker-reweight targets. The rule searches 59 and skips 125. Those
skipped candidates contain 83 positive and 42 negative outcomes: positive mass
`5.62`, negative mass `-5.13`, and net value about `+0.492` that the rule
forfeits.

Discovery happened to make the analogous skipped slice strongly negative.
Fresh data make it slightly positive. Deal-change fraction separates dense from
sparse updates, but it does not rank strategic value within the sparse slice.
Family diagnostics reinforce the instability: skipping helps blocker-stress
and polarized aggregates but harms balanced and correlated aggregates.

This is the exact failure mode warned about in the range-cache discussion: two
equally sparse changes can differ radically because one moves strategically
critical blockers or nut combinations.

## What survives

The compact oracle reaches raw reduction `54.94478241`, leaving
`10.49678249` over fixed full. Scheduling opportunity remains; this fixed rule
captures it with the wrong sign.

More importantly, exact full-candidate acceptance transfers. Rejecting negative
full candidates raises raw reduction from `44.44799992` to `52.48861773`, an
`18.0899%` quality gain. With the ordinary evaluator's `3.33536` seconds of
extra labels, raw quality per millisecond still rises `10.7483%`. This is a
post-solve verifier: it prevents strategy harm but does not recover candidate
solve time.

ADR-0047 already proves the policy tape exact within `8.88e-15` and hot updates
`5.96x` faster on the discovery topology. The combined conservative control is
therefore full search followed by exact acceptance, with ordinary evaluation as
the fallback and a reused dense policy tape as the optimization.

## Next direction

Stop threshold work on this artifact. Use discovery plus this failed fresh
replication only as revealed diagnostic data for defining the next workload and
measurement fields.

For any later pre-search scheduler, record causal blocker-sensitive features:
conditional range shifts at affected private hands, nut/blocker identities or
strategic embeddings, blueprint reach and action entropy at affected nodes,
payoff-normalized uncertainty, and an explicit cost model. Train only after a
larger grouped dataset exists, use asymmetric loss against false skips, and
retain full search as the fallback. A proposal may be cheap, but exact
verification remains separate.

The higher-value engineering step is now to carry the measurement system,
dense compiled verifier, and exact-accept control into a reduced multiplayer
game. Another scalar or shallow tree on this two-player artifact has lower
expected learning value than exposing player-count, coalition, and action-
conditioning failures.

## Dissent protocol

**Confidence:** high that the frozen rule fails transfer; high that exact
post-solve acceptance remains useful; moderate that reduced multiplayer is the
best next workload.

**Opposing evidence:** the rule nearly halves work, raises rate 84%, and loses
only 1.11% raw quality. A latency-constrained product might prefer that trade.
It nevertheless fails the project's declared requirement that strategy quality
not be traded away silently.

**Largest unknown:** which causal representation can distinguish valuable from
harmful sparse blocker updates before paying for a solve.

**Cheapest falsification:** already completed. On 23 fresh groups, the exact
frozen threshold loses aggregate raw and normalized quality and improves only
26.09% of groups.
