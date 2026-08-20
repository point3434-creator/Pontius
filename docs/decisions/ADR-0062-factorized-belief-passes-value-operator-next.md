# ADR-0062: Exact factorized belief passes; value operator is next

**Status:** Implemented; every frozen gate passed

**Date:** 2026-08-19

## Result and provenance

The ADR-0061 audit completed 40 exact closure cases, six recursive-versus-
meet-in-the-middle timing cases, and six nonmaterialized wide cases. It covered
two through six players, balanced and blocker-heavy hand axes, one- and three-
component nonnegative beliefs, repeated public likelihood updates, and known
private-hand conditioning.

The frozen configuration SHA-256 is
`18691aed87e4f5d7d8ad56eafbd18bdab70bd66e227c4b5cb746003b7e2baa14`.
The result is
`experiments/results/factorized-card-belief-audit-v1.json`, SHA-256
`c204011ea3596f102f088d3796ffa01fc33a35bd6be9e70f58043b619ad729c3`.
It ran from clean commit
`0c06e6a6db91747a1ad4d309fbe0dd9fbe038948` in 34.202 seconds.
Before implementation timing, all 346 tests passed in 59.046 seconds.

The first full invocation completed its computation but wrote no artifact
because a NumPy Boolean in the gate map was not JSON serializable. Commit
`0c06e6a` converted result gates and distribution errors to built-in JSON
scalars and added a type invariant. No game, factor, update, contraction,
timing, or gate changed; the clean audit was rerun in full.

## Exact closure verdict

Every correctness gate passed:

- maximum initial full-distribution error: `1.11022e-16`;
- maximum error after two likelihood updates per seat and hero conditioning:
  `2.22045e-16`;
- maximum recursive/meet-in-the-middle partition error: `4.19181e-15`;
- maximum marginal error: `2.05391e-15`;
- maximum wide split replay error: `2.69336e-14`;
- exact support mismatches: `0`;
- impossible-card assignment mass: exactly `0.0`; and
- numeric layout failures: `0`.

This validates an architectural fact, not merely a compression fit. Under an
ordinary behavioral policy, every observed public action multiplies one seat's
hand likelihood. The public belief remains exact as card compatibility times
per-seat unary factors. A declared nonnegative mixture remains closed the same
way. Blocker correlation is not lost: it lives in the exact disjoint-card
constraint.

## Contraction crossover

The Float64 meet-in-the-middle algorithm enumerates compatible assignments
inside balanced seat halves and joins them with at most 64 signed
inclusion-exclusion terms per used-card mask.

| Hands/seat | Family | Cartesian | Compatible | Recursive ms | MITM ms | Speedup |
|---:|---|---:|---:|---:|---:|---:|
| 4 | balanced | 4,096 | 1,008 | `2.664` | `6.093` | `0.437x` |
| 4 | blocker-heavy | 4,096 | 578 | `1.605` | `6.265` | `0.256x` |
| 7 | balanced | 117,649 | 27,892 | `59.761` | `42.606` | `1.403x` |
| 7 | blocker-heavy | 117,649 | 15,419 | `33.325` | `34.834` | `0.957x` |
| 10 | balanced | 1,000,000 | 279,683 | `565.632` | `136.771` | `4.136x` |
| 10 | blocker-heavy | 1,000,000 | 154,802 | `353.023` | `113.815` | `3.102x` |

The frozen pooled ten-hand result is `918.656` ms recursive versus `250.586`
ms meet-in-the-middle, a `3.666x` speedup. The small rows matter just as much:
building incidence tables is a loss when direct compatible enumeration is
cheap. Runtime selection should use declared support and partial-record cost,
not a universal MITM rule.

## Billion-assignment result

At six players and 32 hands per seat, the Cartesian axis contains
`32^6 = 1,073,741,824` assignments and an explicit Float64 probability tensor
would occupy 8,589,934,592 bytes. The exact three-component factor belief uses
6,168 persistent numeric bytes, a ratio of `7.1805e-7`, or about 1.39 million
times less storage.

The balanced case has 274,912,001 compatible full assignments but contracts
through at most 50,535 compatible half-records. The blocker-heavy case has
158,131,060 compatible full assignments and at most 45,405 half-records.
Contiguous and alternating splits agree on counts, partitions, and marginals.

This does not make the Python contraction free:

| Family | Contiguous ms | Alternating ms | Partial numeric bytes | Incidence entries | Estimated incidence numeric bytes |
|---|---:|---:|---:|---:|---:|
| balanced | `4,894.3` | `4,837.4` | `2,192,344` | `370,964` | `14,838,560` |
| blocker-heavy | `4,227.6` | `4,403.1` | `1,986,864` | `309,271` | `12,370,840` |

Those byte estimates deliberately exclude Python dictionary/object overhead.
The factor itself is tiny, but the exact query workspace is material. A native
flat subset table, cached mask topology, and vector component updates should be
tested before interpreting these Python milliseconds.

## Architectural decision

Use a nonnegative factorized-card belief as the default poker range state:

1. rank one for the ordinary independent deal prior plus card removal;
2. a small explicit mixture only for a measured latent-model need; and
3. a higher-order factor only when shared private information or empirical
   correlation falsifies the mixture.

Do not train a generic neural range encoder or apply signed TT-SVD to routine
Bayesian updates. That would approximate an object already represented exactly
and cheaply. It could still be useful for arbitrary population correlations,
but must beat the nonnegative mixture control on strategic labels.

Cache the structural contraction topology by board, hand axes, and seat split.
Public actions change unary weights, not card masks or subset-incidence links.
Spare compute can therefore prepare alternative split topologies, partial
assignment tables, and future public-history likelihood products without
contaminating the current belief. Numeric weights must still be updated from the
current epoch.

## What remains hard

This audit contracts normalization and all hand marginals. It does not contract
showdown payoffs, counterfactual continuation values, or neural leaves. Those
operators couple several seats through winner comparison and may retain high
rank even when the belief is rank one.

The next compression screen should therefore target the signed value operator,
not the probability distribution. On small exact six-player tensors:

- measure TT ranks and truncation spectra of card-compatible terminal payoff
  operators;
- contract those operators against exact unary/mixture beliefs;
- propagate approximations through the public tree; and
- gate on root utilities, every unilateral response value and literal action,
  not tensor Frobenius error alone.

Sampling and neural counterfactual-value models remain alternatives if exact
operator ranks are too high. The exact quotient and factor contraction supply
teachers for both.

## Dissent protocol

**Confidence:** very high in belief closure and small-case exactness; high that
factor storage is the correct default; moderate that native cached incidence
contraction will remain useful once showdown values are included.

**Opposing evidence:** four-hand MITM is 2.3x to 3.9x slower than recursion, and
32-hand Python contraction still takes over four seconds. Small factor storage
does not imply online latency.

**Largest risk:** declaring the joint-belief problem solved while the actual
value operator still requires near-Cartesian work.

**Cheapest falsification:** find a standard public-action update whose
likelihood cannot be written by acting hand and public history, or show that
card-compatible payoff/value tensors require essentially full rank before
response actions stabilize.
