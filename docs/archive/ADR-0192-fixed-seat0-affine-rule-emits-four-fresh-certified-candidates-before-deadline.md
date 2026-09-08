# ADR-0192: The fixed seat-0 affine rule emits four fresh certified candidates before deadline

- Status: accepted prospective engineering result
- Date: 2026-08-21
- Implements: ADR-0191
- Clean preregistration commit: `951cda2d082800072a5fa9e4681a41c45424d318`
- Result: `experiments/results/h32-fresh-selector-stable-affine-street-v1.json`
- Result SHA-256: `7cb3496e754eec2f44083b3c845dea068c7b7cf9af4e382017b4f22c5de178e6`

## Formal result

Every preregistered gate passed. All four target and descriptor digests were
absent from the sealed preconstruction commit, and all reconstructed source,
target, checkpoint, blueprint, block, direction, and one-node affine identities
passed. Cross-run warm-start distances stayed below ADR-0179's numerical
ceilings without an exact digest gate.

The fixed live rule began construction and the affine proof on all four targets.
Every proof selected before the 14,000 ms candidate-ready cutoff, so the
simulated emitted policy was the seat-0 regret-vertex affine candidate four
times. The preloaded immutable blueprint remained the fail-closed alternative,
but neither start guard fired.

All exact teachers began only after each live emitted policy was frozen. The
four fixed witnesses and four selected-scale old-verifier checks completed with
zero response-action flips. Maximum absolute errors were:

| Quantity | Maximum error |
|---|---:|
| profile utility | `1.6653e-16` |
| best-response value | `1.1102e-16` |
| unilateral deviation gain | `1.6653e-16` |

## Fresh value

| Target | Selected scale | Exact positive certified value | Blueprint NashConv fraction |
|---|---:|---:|---:|
| panel 1 balanced | `2^-4` | `1.6322896e-8` | `1.7826e-7` |
| panel 1 blocker-heavy | `2^-1` | `9.7369857e-7` | `1.3296e-5` |
| panel 2 blocker-heavy | `2^-10` | `1.7244240e-9` | `1.9535e-8` |
| panel 3 balanced | `2^-4` | `1.3455895e-7` | `2.2348e-6` |

Total exact positive certified value was `1.1263048407e-6`; the live affine
prediction differed in aggregate by only `6.94e-17`. This is positive
identification that, on these four precommitted contexts, one warm step plus a
fixed regret-vertex direction bought certifiable value rather than policy
motion alone.

The value is not uniform. Panel 1 blocker-heavy supplies `86.45%` of the total,
and the largest target value is `564.65x` the smallest. A four-of-four emission
rate therefore does not imply four equally useful decisions or a stable value
rate. The smallest improvement is still above the frozen numerical allowance,
but it is strategically microscopic.

## Live timing and memory

| Target | Warm step | Construction | Affine proof | Complete street ledger | Boundary headroom |
|---|---:|---:|---:|---:|---:|
| panel 1 balanced | `7,701.14 ms` | `142.75 ms` | `212.54 ms` | `9,094.34 ms` | `5,905.66 ms` |
| panel 1 blocker-heavy | `7,246.19 ms` | `145.92 ms` | `209.91 ms` | `8,641.19 ms` | `6,358.81 ms` |
| panel 2 blocker-heavy | `9,522.84 ms` | `145.77 ms` | `258.72 ms` | `10,965.74 ms` | `4,034.26 ms` |
| panel 3 balanced | `9,769.58 ms` | `141.49 ms` | `249.04 ms` | `11,198.45 ms` | `3,801.55 ms` |

Every ledger includes the fixed one-second synchronization and emission reserve.
The maximum live ledger is `3,462.65 ms` faster than ADR-0190's slowest retained
ledger, but four timings still do not establish a latency distribution.

Maximum GPU-pool allocation was `7,706,509,312` bytes and physical-free memory
did not fall below `7,542,407,168` bytes. The complete audit, including all
off-clock exact teachers, took `95.4517 s`.

## Interpretation

This closes the first online-feasible acquisition loop in the reduced h32
spine:

```text
prepared immutable anchor
-> one resident warm step
-> fixed one-node regret vertex
-> one selector-stable affine proof
-> deadline-eligible certified candidate or blueprint fallback
```

It does not validate an opportunity selector, because acting seat 0 was fixed.
It does not establish poker strategy quality, opponent performance, a latency
distribution, deployment safety, certificate composition, or population
frequency. Exact local NashConv reduction in four constructed river beliefs is
the complete strategy statement.

## Decision

Accept the fixed seat-0 rule as a successful four-context prospective
engineering trial. Preserve the affine proof, two deadline guards, immutable
anchor, and preloaded blueprint fallback unchanged.

The cheapest next falsification is the other order extreme: preregister the
same fixed rule for acting seat 5 on the four remaining previously unlabeled
seat-4 blocker shifts. Do not tune a value threshold, scale rule, guard, target,
or direction from the seat-0 outcomes. If that replication fails exactness or
deadline, stop and repair the primitive/runtime; if it merely finds sparse or
microscopic value, record that outcome rather than rescue it with another
direction.
