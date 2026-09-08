# ADR-0042: Group-separated action-width opportunity survives; fixed pruning fails

**Status:** Accepted

**Date:** 2026-08-19

## Decision

Retain adaptive full-action selective expansion for one separately frozen,
transparent selector screen. Reject every fixed partial mask and reject blind
shallow re-solving as runtime policies on this workload.

The preregistered opportunity gates in ADR-0041 pass without retuning. This
authorizes development of a causal selector; it does not authorize a selector,
an exact-label no-op decision, native specialization, validation/test access,
neural leaves, or any multiplayer claim.

## Frozen evidence

The development matrix is
`experiments/results/river-selective-expansion-development-v1.json`, SHA-256
`7571a8a2f3c08034b53982b4ac122106fbe3d1cc7b216d3ee4ba58cf01fdd2ff`,
8,836,235 bytes. It embeds clean implementation commit
`e0ff3a6621449d5e06060395516c037e676ce6df` and the preregistered config hash
`3740d5a9ae9293eb71bdc3a6491cf6b5e22d40289918534755c0a414ce46e3d9`.

The selection-free analysis is
`experiments/results/river-selective-expansion-development-v1-analysis.json`,
SHA-256
`c1fc2962399d2f8f588504b418ffba8d274ec1d73978af516e48f58075a4e392`,
408,103 bytes. It fits no rule and explicitly leaves selection unauthorized.

The frozen split produces eleven development board groups, 44 four-family
contexts, 132 support-preserving target ranges, 528 target/mask structures, and
2,640 candidate records. The one validation-assigned candidate group produces
no context, range, or oracle record, and no test context is generated.

All 44 source blueprints pass normalized NashConv/payoff-span `<= 1e-5` at the
first declared checkpoint: 32 at 512 DCFR iterations, seven at 1,024, and five
at 2,048. None requires 4,096. The maximum selected normalized source NashConv
is `9.60633e-6`. Every structural, schema, full-mask, frozen-source, feature,
and development-split gate passes.

## Primary opportunity result

At fixed warm pseudo-regret mass `0.1 * payoff_span` and work equal to 32 full
tree iterations:

- full-mask plus exact-label no-op totals `14.80649` NashConv reduction;
- best-mask plus exact-label no-op totals `16.82102`;
- the difference is `2.01453`, or `13.6057%` of the full/no-op baseline; and
- all eleven board groups have positive opportunity, exceeding the frozen 60%
  requirement.

The smallest group uplift is only `3.76e-6`, so “all groups” must not be read as
uniform effect size. The median is `0.12924`, the maximum is `0.53895`, and ten
of eleven groups exceed `0.01`.

At the instance level, the deployable choice implied by the exact oracle would
be no-op 23 times, `b1r1` 25 times, `b2r1` three times, `b3r1` 50 times, and
full `b3r2` 31 times. Opportunity is therefore not simply “use the narrower
tree.”

| Equal-work budget | Full/no-op | Mask/no-op | Uplift | Relative uplift |
|---:|---:|---:|---:|---:|
| 4 | 1.67712 | 3.41372 | 1.73660 | 103.55% |
| 8 | 5.03891 | 8.48986 | 3.45095 | 68.49% |
| 16 | 10.40237 | 12.26539 | 1.86302 | 17.91% |
| 32 | 14.80649 | 16.82102 | 2.01453 | 13.61% |
| 64 | 19.99927 | 20.71192 | 0.71265 | 3.56% |

The relative value of width adaptation is largest under tight compute and
shrinks as full search converges. That is the desired scheduling regime, but
the table remains an exact-future oracle ceiling.

## Fixed-mask failure and shallow-search risk

At the primary budget, raw fixed-mask results are:

| Mask | Aggregate reduction | With exact no-op | Improve | Harm |
|---|---:|---:|---:|---:|
| `b1r1` | -72.72615 | 0.95479 | 40.15% | 59.85% |
| `b2r1` | -65.33652 | 1.83041 | 40.15% | 59.85% |
| `b3r1` | +3.32641 | 13.99576 | 75.00% | 25.00% |
| `b3r2` | +8.81632 | 14.80649 | 72.73% | 27.27% |

The two shallowest masks become more negative as their selective games are
solved longer. Exact blueprint continuation values do not make their
materialized policy changes safe in the full game. This behavior is consistent
with a selective-objective mismatch rather than mere early CFR noise, although
the matrix does not prove that mechanism.

The full mask remains the best fixed arm. In every leave-one-board-group-out
fold, training data selects `b3r2`; held-out capture of the `2.01453` oracle
opportunity is exactly zero. Static pruning is therefore rejected.

## Where the opportunity lives

At budget 32, correlated ranges contribute `0.97146` opportunity, a `45.06%`
relative uplift. Polarized and blocker-stress ranges contribute `0.58103` and
`0.43949`; balanced ranges contribute only `0.02255` (`1.22%`). Sparse
reweights have `43.15%` relative uplift on a small full-search baseline, while
factorized-dense updates have `7.42%` relative uplift but larger absolute
baseline reduction.

This stratification is diagnostic. Synthetic range-family names are not valid
runtime features.

The strongest univariate boundary rank for no-op search opportunity is the
range-delta L2 probability norm: Spearman `0.37555`, with leave-one-group-out
values from `0.34374` to `0.42570` and unchanged sign in every fold. Raw mask
advantage is ranked best by a blueprint public raise mass at `-0.38664`, again
with stable sign. These are moderate associations, not an arm-selection rule.

The fixed paid `b1r1` budget-four probe is weaker. Its best opportunity rank is
maximum normalized positive regret at `-0.27811`. In the serial Python control,
boundary features average `2.004 ms`; the cold paid probe including exact leaf
construction averages `25.744 ms`, and boundary plus paid probe averages
`27.748 ms`. This timing is not a native claim, but it argues for testing cheap
pre-search range geometry before paying for a shallow solve.

## Post-result arm-compression diagnostic

After seeing the result, an explicitly exploratory calculation finds that
exact no-op plus `{b3r1, b3r2}` retains `85.03%` of the four-mask oracle
opportunity. Adding `b1r1` retains `94.86%`; adding `b2r1` reaches 100%.

This calculation was not preregistered. It may simplify the next screen's
candidate set, but it cannot select or validate a policy from this artifact.

## Next gate

Before any branch-major C++ layout:

1. preregister one development-only transparent selector screen with complete
   board-group separation;
2. distinguish cheap pre-search range features, blueprint-public features, and
   paid probe features in the cost model;
3. compare no-op, near-full `b3r1`, and full `b3r2` as the primary compact arm
   set, with all four masks reported only as a secondary ceiling;
4. keep exact full-game NashConv strictly in labels or an explicitly timed
   recertification control, never in selector inputs;
5. report raw harm as well as no-op-filtered quality, because the oracle no-op
   masks catastrophic shallow candidates; and
6. freeze any selected rule before constructing validation. If development
   group transfer cannot beat always-full at matched work and charged feature
   cost, stop this branch without neural fitting or native specialization.

## Dissent protocol

**Confidence:** high that action-width opportunity exists in this exact
heads-up river workload; moderate that causal boundary features can recover a
useful fraction; low that it transfers to earlier streets or six players.

**Opposing evidence:** full expansion wins every fixed-mask fold, blind search
still harms 27%-60% of targets, the oracle relies on exact future no-op labels,
univariate correlations are modest, and only eleven independent board groups
were observed.

**Cheapest falsification:** freeze a compact transparent rule family and run
board-group cross-validation on this development artifact with every feature
and recertification cost charged. Failure to beat always-full ends adaptive
mask scheduling on the current exact river workload.
