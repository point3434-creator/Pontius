# ADR-0044: Reject the causal width screen and retain full search

**Status:** Superseded for normalized selection by ADR-0049; fixed full remains incumbent pending replication

**Date:** 2026-08-19

## Decision

Reject the preregistered compact causal width screen. Retain fixed full `b3r2`
search as the current selective-expansion control. Do not freeze an adaptive
tree, generate the planned fresh replication, open validation/test, or begin
native action-width specialization from this workload.

The failure is not rescued by changing the selection objective, feature tier,
tree depth, uncertainty penalty, group threshold, or arm set after inspection.
Adaptive width may be reconsidered only after a materially different workload
or a new causal information source, not by retuning this artifact.

## Frozen evidence

ADR-0043 froze the rule family before fitting. Its rule-file SHA-256 is
`3a8c26ee23eefaeec87f42e23257d591734cd90abb997734e9a1761f7b385e93`.
The implementation was committed as
`1f672c0be398c33566883bf0624c3967c7a31710` after all tests passed and before
the real discovery labels were processed.

The one-time screen artifact is
`experiments/results/river-selective-width-screen-v1.json`, SHA-256
`ee7df32361a08236603e4b2d8d3e6f26d1a209f98b86bb5ffce53fcf14be2794`,
20,840 bytes. It reads the frozen 11-group, 132-target matrix with exact source
and config hashes. No reserved context is constructed.

The screen evaluates eighteen preregistered tree specifications: three
cumulative feature tiers, depths one and two, and risk multipliers zero, one,
and two. Each specification is fitted ten groups at a time and applied once to
the held-out board group. Family and target identifiers are absent from the
fitter. Runtime trees contain only causal feature thresholds and arm names.

## Result

The selection objective is aggregate held-out payoff-normalized raw NashConv
reduction. Fixed `b3r2` totals:

- raw reduction `8.81632`;
- normalized reduction `0.397521`;
- 3,488,448 state visits;
- 24.7540 serial Python seconds; and
- raw reduction rate `3.56157e-4` per millisecond.

No adaptive specification exceeds its normalized reduction. Fixed full search
therefore wins the frozen tolerance rule, captures zero compact-oracle
opportunity, and makes all strict improvement gates fail. The work and
maximum-harm gates pass only because the selected fallback is itself the fixed
control.

The closest normalized candidate is
`delta_context_public__depth_2__risk_2`. Out of fold it chooses no-op 50 times,
`b3r1` 39 times, and `b3r2` 43 times. Relative to fixed full search it:

- improves raw reduction by `1.41987` or `16.10%`;
- improves raw reduction per millisecond by `77.39%`;
- uses `38.11%` fewer state visits;
- lowers maximum target harm from `2.41898` to `0.595659`; but
- reduces payoff-normalized quality by `1.740%` and improves raw quality in
  only four of eleven board groups.

The raw-best tree gains `25.94%` raw reduction and `30.26%` raw rate, but loses
`5.690%` normalized quality and also improves only four groups. The rate-best
tree nearly doubles raw rate and uses `46.18%` less work, but loses `4.076%`
normalized quality and improves only six groups, below the frozen 60% gate.

Thus the feature family can identify pot-weighted efficiency trades. It cannot
produce stable improvement across normalized strategy quality, pot scales, and
board groups. Selecting one of those attractive raw-chip candidates after the
fact would change the declared objective and conceal the transfer failure.

## What remains valuable

The compact exact future oracle totals `16.51943` raw reduction, leaving
`7.70311` over blind full search. The opportunity still exists, but this causal
tree family cannot attain it reliably.

A separate exact-label diagnostic is more informative. Evaluating every full
candidate and rejecting negative reductions raises the full-search total from
`8.81632` to `14.80649`, a `67.94%` quality increase. Exact evaluation adds
1.59351 seconds to 24.7540 seconds of solving, or `6.44%`, and improves raw
reduction per millisecond by `57.79%` in the Python control.

This is not a deployable no-op rule: it observes the exact full-game teacher.
It does identify candidate acceptance/recertification as a higher-value next
bottleneck than predicting tree width. The existing dependency tape currently
updates ranges for one fixed policy; it does not incrementally propagate a
candidate's changed policy probabilities.

## Next gate

The next narrow experiment should parameterize the exact dependency tape by
policy probabilities as well as range probabilities. For selective candidates,
update only changed materialized information-set/action entries and propagate
their affected cones in Float64. Compare exact candidate NashConv against the
ordinary evaluator, charge compilation and hot updates separately, and measure
whether exact accept/reject can beat blind full search in quality per
millisecond.

This remains a heads-up exact control. In multiplayer, recertification measures
unilateral deviation incentives but supplies no coalition-safe theorem. No
six-player safety claim follows.

## Dissent protocol

**Confidence:** high that the frozen compact screen failed; moderate that exact
candidate recertification is the right next local bottleneck; low that exact
acceptance will scale directly to six players.

**Opposing evidence:** the best adaptive candidates materially improve raw
chips, rate, work, and tail harm. If raw chips alone were the frozen objective,
one would pass several useful metrics. The rejection rests on the intentionally
joint requirement that normalized quality and board-group transfer also
improve.

**Largest unknown:** whether policy-delta invalidation is sparse enough after a
solver changes many action probabilities, especially in wider and multiplayer
trees.

**Cheapest falsification:** compile a parameterized candidate-policy tape for
the existing exact river and compare its hot affected cone with full candidate
evaluation. If policy deltas are dense or compilation dominates reuse, stop
exact online acceptance and move the lesson into learned uncertainty or richer
reduced multiplayer evaluation.

## Subsequent correction boundary

ADR-0047 found that this screen divided candidate reductions by the narrow
range-context payoff span rather than the payoff span of the searched 3x2
multi-size game. The ratio between those denominators varies across targets, so
the reported normalized ranking is not merely expressed in different global
units. Fixed `b3r2` remains the incumbent because no corrected alternative has
been validated, but the normalized rejection is pending a frozen mechanical
correction audit. Raw outcomes and timings remain unchanged, and no adaptive
rule is retroactively authorized.

ADR-0049 completed the frozen correction. The unchanged grouped screen then
selected `delta_only__depth_1__risk_1` and passed every original gate. This
invalidates the normalized rejection in this record, but only on revealed
development data. Fixed full remains the incumbent until the corrected fixed
rule passes a fresh preregistered replication.
