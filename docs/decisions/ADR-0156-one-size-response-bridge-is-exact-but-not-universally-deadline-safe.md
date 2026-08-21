# ADR-0156: The one-size response bridge is exact but not universally deadline-safe

## Status

Accepted as the frozen systems result of ADR-0155. It does not authorize online
deployment, a new h32 strategy-quality claim, or a two-size run.

## Evidence identity

The 124,807-byte artifact is
`experiments/results/h32-response-latency-bridge-v1.json`, SHA-256
`b477243f73c9028b2bdeed1b3581a0cb852d9eb0bb4cf033ef1a5437ba629179`.
Its configuration SHA-256 is
`8292669e38f941f8d97e7a3d858f6709b82e40a2d01011bab757402f419558b5`.
The run recorded strict clean Git state at
`2380e0adfa38db7839b1bafd2a5e4703ead4e4c5` and completed in
`243.23396 s` on the frozen NumPy 2.5.2, SciPy 1.18.0, CuPy 14.2.0,
CUDA-runtime 13.2, driver 13.3, SM-120 stack.

All 22 outcome-neutral integrity gates passed.

## Exactness and fail-closed behavior

All twelve retained one-size `search_current1` candidates reproduced the
ADR-0148 teacher prefix. Maximum absolute errors were:

- utility: `2.276e-15`;
- best-response value: `2.554e-15`; and
- deviation gain: `1.443e-15`.

Every candidate stopped for an immutable blueprint-cap violation at the exact
teacher stop seat. The verifier evaluated 33 of 72 possible seats. Stop-prefix
lengths were `2,2,6,1,3,1,5,2,3,1,5,2`. No certificate completed, and every
row deterministically selected the immutable blueprint fallback. There were
zero new strategy-quality labels and zero sized-tree constructions.

GPU policy digests differed from the retained teacher on all twelve targets,
as preregistered. Numerical coordinates and stop decisions, not reduction-order
dependent serialization bytes, were the identity criterion.

## Fifteen-second result

Before any action-emission reserve, the component clocks were:

| Clock | Minimum | Median | Maximum |
|---|---:|---:|---:|
| one resident warm step | 7,224.60 ms | 9,955.63 ms | 12,693.24 ms |
| exact response certificate | 1,641.30 ms | 3,913.03 ms | 10,582.96 ms |
| prepared step + certificate + selection | 9,918.87 ms | 14,054.72 ms | 23,276.20 ms |
| exact-target-cache resident, including solver prepare | 9,978.00 ms | 14,097.50 ms | 23,339.10 ms |
| cold exact target | 12,557.74 ms | 17,431.10 ms | 28,043.33 ms |

Selection itself was negligible. Exact target workspace construction took
56.93--81.87 ms, GPU incidence construction 7.87--34.91 ms, solver preparation
40.02--62.90 ms, and the six-seat resident cache took 2,454.70--4,613.58 ms.
Maximum observed GPU-pool use was 7,706,509,312 bytes, below the frozen 12 GB
ceiling.

Prepared and exact-target-cache-resident paths fit the 15-second boundary on
7/12 targets with reserve scenarios of 0, 250, or 500 ms, and 6/12 with a
1,000 ms reserve. The cold exact-target path fit only 2/12 under every frozen
reserve scenario. These counts are descriptive sensitivity results because
the reserve values were not measured action-emission tails.

The observed maximum, not a p95 or p99 population estimate, is the controlling
diagnostic. Twelve heterogeneous one-shot targets cannot estimate a tail.

## Decision

Accept the measurement and reject the current composition

`one complete resident warm step -> exact resident response prefix`

as a universally deadline-safe 15-second decision path. Cache residency is
necessary but not sufficient: five prepared targets already miss the deadline
with zero emission reserve, and six miss with the 1,000 ms sensitivity reserve.
Cold exact-target construction is plainly not an admissible default path.

Do not enlarge the rejection autopsy yet. The next bounded engineering target
is an incremental source-relative response bridge for localized policy deltas,
with exact equivalence controls against the accepted resident evaluator. Its
preregistered preflight must measure fixed work and conservative wall-clock
maximum separately, retain cap-before-objective stopping, and return the
blueprint whenever the certificate cannot finish before the measured emission
cutoff.

Action emission and state-ingest tails remain unmeasured, so
`deployment_authorized=false`. Strategy quality remains claim-null.

## Dissent

**Confidence:** very high in exact reproduction and stop identity; high that
the present full-step/full-response composition cannot provide a universal
15-second guarantee; moderate that an incremental response bridge is the best
next optimization rather than a smaller candidate-generation unit.

**Opposing evidence:** six prepared rows still fit with a 1,000 ms reserve, so
the incumbent path may be useful under a future deterministic scheduler. That
does not make it safe as an unconditional path.

**Largest unknown:** how much opponent best-response work a localized delta can
reuse without invalidating selector-switch exactness.

**Cheapest falsification:** on an h7 or similarly reduced exact control,
compare a source-relative localized response update with a complete resident
seat evaluation across pass, cap-fail, objective-fail, zero-reach, and
best-response-switch mutations.
