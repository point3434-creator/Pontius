# ADR-0178: Regret vertices expose soft-generator weakness but not a live selector

- Status: accepted prospective result
- Date: 2026-08-21
- Implements: ADR-0177
- Clean preregistration commit: `a9f2030`
- Result: `experiments/results/h32-fresh-regret-vertex-opportunity-v1.json`
- Result SHA-256: `9606df6dc2356bd045e8f6667b82062ae04f5904672795246d204dc8e9a48070`

## Result

Every frozen gate passed. The audit covered six fresh seat-1 blocker targets,
36 public-node blocks, and 72 paired soft-DCFR/regret-vertex directions. The
adaptive exact search used 858 certificates instead of the full grid's 2,448,
a 64.95% reduction, and finished in `849.42 s`.

All 72 directions had a complete grid scale. The regret vertex won the bounded
two-direction oracle on 30 of 36 blocks and exceeded soft DCFR by more than the
raw certificate guard on 24. Aggregate positive certified value was:

| Measurement | Value |
|---|---:|
| Soft DCFR | `6.8172e-7` |
| Paired bounded oracle | `1.4002e-5` |
| Soft capture fraction | `4.8688%` |

Thus this frozen alternative library contains about 20.54 times the aggregate
value captured by the soft direction. This is positive identification of soft-
generator weakness within the library, not merely evidence that the envelope
cone is narrow.

## Where the missed value sits

The alternative's advantage is strongly seat-structured:

| Acting seat | Soft value sum | Vertex value sum | Vertex wins |
|---:|---:|---:|---:|
| 0 | `1.3961e-10` | `9.9936e-6` | 6/6 |
| 1 | `1.5386e-7` | `1.9494e-7` | 4/6 |
| 2 | `3.2172e-7` | `2.2228e-7` | 3/6 |
| 3 | `1.8900e-7` | `6.0186e-7` | 5/6 |
| 4 | `1.6810e-8` | `3.8203e-7` | 6/6 |
| 5 | `1.8169e-10` | `2.4467e-6` | 6/6 |

Soft regret matching barely moves at seats 0 and 5, while a pure direction
chosen from the same regret ordering exposes substantially more exact value.
The largest single block captured `7.309e-6`, or `1.4302e-4` of that target's
blueprint NashConv. That is far above ADR-0176's values but still small relative
to total blueprint opportunity.

## Opportunity proxy failure

The preregistered causal proxy behaved consistently but measured the wrong
thing for scheduling the alternative:

| Correlation across 36 blocks | Spearman rho |
|---|---:|
| Regret proxy vs. soft value | `0.8008` |
| Regret proxy vs. bounded-oracle value | `-0.1223` |
| Regret proxy vs. vertex uplift | `-0.4013` |

Positive one-step regret mass predicts the magnitude of the soft regret-
matching update. It does not rank the decisive pure directions, whose largest
gains often occur where the regret sign exists but its mass is tiny. Therefore
the proxy is not authorized as a vertex-opportunity scheduler feature.

This also raises a stability issue: a pure vertex can amplify a very small
regret ordering into a large policy move. Exact same-target certification makes
the measured candidate safe, but does not establish that the direction rule
transfers across fresh targets or small numerical perturbations.

## Geometry and wall clock

The convex-scope search controls held on every direction and never used more
than 15 queries. Across 858 queried certificates, 728 completed and 130 stopped
at a blueprint cap; none was objective-bound. Intermediate queries recorded 42
response-action flips, with at most 15 in one certificate, but every selected
best row had zero flips. Convexity therefore survived selector kinks as
expected.

Certificate time ranged from `106.80` to `2,201.69 ms`. Combining the observed
warm step, best-row construction, one best-row certificate, and one-second
emission reserve produced descriptive ledgers below 15 seconds for all 36
vertex rows. Soft rows fit 35 of 36, with one `15,020.56 ms` overrun. Peak GPU-
pool total was `8,214,049,792` bytes and physical free memory remained at least
`7,032,799,232` bytes.

These are same-target retrospective ledgers. The adaptive search that revealed
the scale and direction is not available live.

## Interpretation

Hypothesis A now has direct support: the one-step soft generator leaves exact
certifiable value on the table relative to a frozen alternative derived from
the same causal calculation. Hypothesis B also remains relevant because many
vertex directions require severe scaling, and even the best bounded-oracle
fraction is only `1.43e-4` of blueprint NashConv. Hypothesis C remains
substantially disfavored by the constituent-block and radius results.

The paired library cannot identify opportunity exhaustion. Its oracle is a
lower bound and the failure of its regret-mass proxy prevents a live selection
rule. No population, deployment, or global strategy-quality claim follows.

## Decision

Accept the prospective mechanism and generator diagnosis. Do not launch a live
regret-vertex holdout yet: the rule magnifies small regret signs, lacks a causal
ranking feature, and learned its best scale off-clock.

The next decisive diagnostic is a small deep-horizon arm on preregistered panel
targets. Run the immutable envelope against policy checkpoints from a 32-64
step off-clock solve. If deeper search produces materially larger exact
Pareto-safe value, horizon and amortized deep solving become the next
architecture. If it remains microscopic, evidence shifts toward the six-seat
contract geometry, although even that result must be stated as evidence rather
than proof that no other generator can succeed.

Before that run, codify numerical identity as the default GPU evidence gate and
repair the stale repository status front door so the repeated protocol lesson
and the closed 15-second spine are visible.
