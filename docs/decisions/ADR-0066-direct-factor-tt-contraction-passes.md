# ADR-0066: Direct factor–TT contraction passes, but rank and batching remain open

**Status:** Implemented; every frozen ADR-0065 gate passed

**Date:** 2026-08-19

## Result and provenance

The direct kernel contracts an exact nonnegative factorized card belief with a
signed tensor-train value operator without materializing either dense six-seat
tensor. Card topology, belief normalization, and operator work are separately
compiled and measured.

The frozen configuration SHA-256 is
`bdda6399408032672b29767bc2c577648036d44ac7e090bfb71cf37c60100c6f`.
The result is
`experiments/results/factor-tt-direct-contraction-audit-v1.json`, SHA-256
`b497a87236697288b412047b5eac95ffa971762d913153c85b068b29e11bc7bd`.
It ran from clean commit
`2001743a64132768ff4f7cc454c08cfebaf8127e` in 22.701 seconds. All 364
tests passed in 59.038 seconds before the frozen run.

## Exactness result

All frozen controls passed:

- maximum belief-partition relative error: `2.22e-15`;
- maximum direct versus reconstructed-TT expectation error: `3.38e-14`;
- maximum untruncated-TT versus literal-payoff expectation error: `1.20e-12`;
- maximum synthetic direct versus enumerated-joint error: `1.39e-16`;
- contiguous fixed-dtype topology failures: `0`; and
- topology/belief-workspace reuse failures: `0`.

The direct/reconstructed comparison is the kernel identity test. It includes
signed operators and one- and three-component beliefs. The worst observed
outer numerator cancellation ratio is `181.25`; Float64 plus `fsum` outer
accumulation still remains more than three orders of magnitude inside the
frozen error gate.

## Crossover result

| Hands/seat | Family | Hot operator | Enumerated joint | Speedup |
|---:|---|---:|---:|---:|
| 4 | balanced | `0.48 ms` | `6.64 ms` | `13.76x` |
| 4 | blocker-heavy | `0.46 ms` | `3.60 ms` | `7.85x` |
| 7 | balanced | `2.71 ms` | `208.21 ms` | `76.80x` |
| 7 | blocker-heavy | `1.97 ms` | `139.13 ms` | `70.49x` |
| 10 | balanced | `6.76 ms` | `1991.53 ms` | `294.42x` |
| 10 | blocker-heavy | `5.96 ms` | `1095.43 ms` | `183.95x` |

The pooled ten-hand medians are `6.300 ms` direct and `1556.741 ms`
enumerated, a `247.12x` speedup. The crossover is not marginal: the compiled
card topology converts exponential joint enumeration into approximately two
streams of compatible three-seat records, each widened by 24 features.

These timings include TT half contraction, signed incidence accumulation,
inclusion–exclusion queries, and normalized expectation. They exclude the
explicitly separated topology and belief compilation costs, exactly as frozen.

## Wide scaling and memory

| Hands/seat | Family | Topology compile | Belief compile | Hot operator | Peak numeric bytes |
|---:|---|---:|---:|---:|---:|
| 16 | balanced | `101.72 ms` | `7.08 ms` | `35.39 ms` | `17.03 MB` |
| 16 | blocker-heavy | `76.50 ms` | `6.38 ms` | `30.35 ms` | `14.07 MB` |
| 24 | balanced | `325.72 ms` | `23.42 ms` | `131.73 ms` | `41.42 MB` |
| 24 | blocker-heavy | `269.97 ms` | `19.97 ms` | `112.24 ms` | `33.52 MB` |
| 32 | balanced | `805.67 ms` | `56.46 ms` | `312.12 ms` | `78.21 MB` |
| 32 | blocker-heavy | `674.81 ms` | `50.69 ms` | `274.00 ms` | `68.40 MB` |

The maximum 32-hand peak ratio is `0.0091045` of one 8.59 GB dense Float64
operator, inside the frozen 1% gate. It is nevertheless close to that gate. The
balanced row contains 25,611 left and 24,749 right records, 181,885 incidence
entries, 38.0 million incidence-feature updates, and 39.3 million query-feature
terms. Its topology alone is 15.54 MB and its operator-static workspace is
42.90 MB.

At ten hands, peak workspace is still 86–92% of a dense operator. At four
hands, topology overhead is about 29 times the tiny dense tensor. Compression
becomes economically meaningful only after the joint axis is moderately wide.

## Rank-eight extension result

Rank 8 remains at Float64 noise on the four- and five-hand literal payoff
expectations (`1.30e-13` and `1.79e-13` maxima), but it is no longer exact on
the preregistered seven-hand extension. Maximum literal expectation error is
`6.64054e-05`, on the balanced one-component all-check/player-0 case. The
balanced all-contender/player-4 case reaches `5.28512e-05`.

This does not fail ADR-0065: direct contraction exactly evaluates the supplied
rank-8 TT, and seven-hand representation error was frozen as a diagnostic. It
does overturn the strongest interpretation of ADR-0064. Rank 8 was exactly
sufficient on the revealed four/five-hand axes, not a universal exact showdown
rank. A later rank must be selected by root/action damage on wider axes, not by
this scalar expectation alone.

## Architecture decision

Adopt the compiled card topology and direct factor–TT contraction as exact
laboratory primitives. Do **not** allocate or run one independent 24-feature
incidence table for each of the 64 payoff groups. At 32 hands, 64 sequential
hot passes would already cost roughly 18–20 seconds in Python; simultaneous
tables would exceed the intended memory budget.

The next representation must fold a fixed behavioral policy into the public
tree before belief contraction:

1. multiply a child TT core on the acting player's mode by that action's unary
   hand-probability vector;
2. sum action-weighted child TTs bottom-up at each public node;
3. recompress with a frozen cap/tolerance while preserving zero sum; and
4. contract the resulting policy-conditioned root TT once per player/value
   target.

This uses the same exact separation discovered for beliefs: behavioral action
reach is a unary hand factor. It tests whether public-tree composition, rather
than card support, is the next rank bottleneck.

After fixed-policy root utilities pass, extend the network to leave one target
seat's hand mode uncontracted. That produces conditional counterfactual value
vectors for action comparison. Only literal best-response action identity can
approve that lift for search or certification.

## Dissent protocol

**Confidence:** very high in direct scalar correctness; high in the measured
NumPy crossover; moderate in the peak-byte accounting; low that independent
operator TT ranks or timings extrapolate to full ranges.

**Opposing evidence:** the 32-hand pass is hundreds of milliseconds, its memory
is near the frozen ceiling, and rank 8 already loses exactness at seven hands.
Scalar expectation is much easier than conditional action values.

**Largest risk:** treating a `247x` win over an intentionally expensive joint
baseline as evidence of sub-millisecond deployability.

**Cheapest falsification:** bottom-up fixed-policy TT composition whose root
rank or compression damage grows enough that one root contraction is slower or
less accurate than a structured public-tree alternative.
