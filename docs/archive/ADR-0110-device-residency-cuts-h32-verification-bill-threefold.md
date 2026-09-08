# ADR-0110: Device residency cuts h32 verification bill threefold

**Status:** Device-resident terminal contraction accepted as the h32 exact
partial-verifier incumbent; transferred feature path retained as oracle and
fallback

**Date:** 2026-08-20

## Result

The sealed ADR-0109 audit completed from clean commit `39d61c7` with every
frozen gate passing. The canonical local artifact is
`experiments/results/h32-resident-verifier-audit-v1.json`:

- SHA-256:
  `29504e25bffac5409a401c3e780d328ef143461eb9b63cd72fb1f790960ef491`;
- size: 327,223 bytes;
- config SHA-256:
  `13eaaa72501514eb51fd6f7734598d316f2724f5b89b26be1e7d860c24a406c4`;
- resident contraction SHA-256:
  `d1680c43b74b6f3b70c2ca9b4cdd41bc96f478102eea18c3dfb07c9866d4f4db`;
- resident evaluation SHA-256:
  `45fc76a9bea2292926c7bff1079172a8abfc27b53cefa41bad24da836e58f470`;
  and
- audit implementation SHA-256:
  `fa5997ba29c096cafaa7f5675e8e043e60c193ec0947ad3cefeb056bedc09555`.

Total audit wall time was 308.089 seconds, including the fresh-board controls,
four complete six-seat legacy calibration reads, four independently charged
resident cache builds, and all 133 exact resident seat reads. The audit
created zero strategy-quality labels.

## Correctness result

The resident verifier reproduced all four ADR-0108 candidate streams:

- 52 policy digests matched;
- all 133 evaluated-seat prefixes matched;
- all 39 early stops matched in reason and seat;
- all 13 completed candidates matched;
- all four final selected policy digests matched; and
- every fixed blueprint-envelope decision remained unchanged.

The maximum errors were:

| Quantity | Maximum | Gate |
|---|---:|---:|
| Seat utility | `3.72e-15` | `1e-9` |
| Seat best response | `3.82e-15` | `1e-9` |
| Seat deviation gain | `1.21e-15` | `1e-9` |
| Completed NashConv | `1.89e-15` | `1e-9` |
| Completed zero-sum residual | `8.47e-15` | `1e-9` |

The largest resident seat read was 1.821 seconds. Same-day legacy calibration
ratios ranged from `0.9902` to `1.0084`, so the parent partial-verifier bills
were stable.

## Charged economics

The resident system was compared against ADR-0108's accepted partial verifier
with the same exact seat prefixes. Each target paid for a fresh belief cache
and all six showdown libraries before candidate timing.

| Family | Shift | Seat reads | Cache | Resident marginal | Resident charged | Calibrated incumbent | Charged speedup |
|---|---|---:|---:|---:|---:|---:|---:|
| balanced | local blocker | 49 | 3.435 s | 76.8 s | 80.2 s | 246.7 s | `3.076x` |
| balanced | strength | 20 | 3.402 s | 34.0 s | 37.4 s | 108.0 s | `2.887x` |
| blocker-heavy | local blocker | 46 | 2.371 s | 55.0 s | 57.4 s | 171.9 s | `2.997x` |
| blocker-heavy | strength | 18 | 2.371 s | 23.1 s | 25.5 s | 70.6 s | `2.767x` |

Pooled charged resident bill was 200.480 seconds versus 597.228 seconds for
the calibrated incumbent: **`2.979x` faster**. Both family gates passed:

- balanced: `3.016x`; and
- blocker-heavy: `2.926x`.

No weak target is hidden by pooling. The slowest relative row still wins by
`2.767x`, well above the frozen `1.5x` gate.

The resident cache cost 11.580 seconds across the four independently charged
targets, only 5.78% of the charged resident bill. Cross-shift sharing could
remove roughly half that construction, but it is no longer a first-order
optimization and remains deliberately unclaimed.

## Transfer result

For the exact 133-seat workload, the old batching geometry would have moved:

- 505.758 GB host to device; and
- 508.013 GB device to host.

The resident path charged 24.507 GB in total, including all four complete
static cache uploads. That is a **`41.37x` byte reduction**.

The residual resident traffic consists principally of 9.891 GB of accumulated
query records returned to the CPU. Candidate unary-factor uploads total only
39.4 MB. Static cache uploads total 14.577 GB.

The measurement validates the intended mechanism. The speedup is not a batch
count artifact: the data path actually stopped round-tripping feature matrices.

## Resource result

The exact pre-freeze static estimates reproduced in operation:

| Family | Six-seat resident cache | Maximum CuPy pool | Host estimate |
|---|---:|---:|---:|
| balanced | 4.327 GB | 7.935 GB | 1.025 GB |
| blocker-heavy | 2.962 GB | 6.960 GB | 0.72 GB |

The maximum CuPy pool stays below the frozen 12 GB gate and leaves useful room
on the 16 GB RTX 5080. The largest temporary batch scratch estimate is 740 MB.
Cache construction itself is mostly CPU automaton-half creation:

- balanced half preparation: about 3.0 seconds per target versus 0.28 seconds
  of upload; and
- blocker-heavy: about 2.08 seconds versus 0.20 seconds of upload.

This work is charged but amortized adequately over even the dense target's 18
seat reads.

## Fresh-board control

The undisclosed h7 board `3s 8c Th Kd Ac` passed external exactness in both
incidence directions. Utility error was at most `2.22e-16`, best-response error
at most `1.11e-16`, and both action maps matched.

Its economics were deliberately mixed:

- seat zero: `1.768x` marginal and `1.692x` cache-charged; and
- seat three: `0.813x` marginal and `0.776x` cache-charged.

This is valuable opposing evidence. Residency is not a universal small-axis
win. For the narrower seat-three feature geometry, GPU construction and launch
cost exceed the transfers removed. The h32 result wins because its feature and
record widths cross the residency boundary, not because “GPU resident” is an
intrinsically superior label.

No runtime selector is authorized from two h7 seats. The transferred path
remains the honest small-axis fallback.

## New phase decomposition

The 188.900-second resident marginal bill decomposes as:

| Phase | Pooled time | Share of marginal bill |
|---|---:|---:|
| Device feature/sparse/fold pipeline | 125.603 s | 66.49% |
| CPU query-record-to-hand fold | 56.861 s | 30.10% |
| Probability compilation | 2.119 s | 1.12% |
| Result download | 1.093 s | 0.58% |
| Public-tree reverse pass | 1.062 s | 0.56% |
| Factor preparation and upload | 0.579 s | 0.31% |
| Device weighted-product generation | 0.371 s | 0.20% |
| Unattributed orchestration | 1.213 s | 0.64% |

Residency removed the old host feature/fold bottleneck and exposed a more
specific one. The CPU hand fold performs `np.bincount`, total `fsum`, and value
normalization over 193 terminal record vectors for every seat. Median seat
hand-fold time is 429.7 ms; median complete resident seat time is 1.307
seconds.

The next bounded systems experiment is therefore not cache sharing or wider
CuPy batches. It is device-side record-to-hand aggregation:

1. precompile the query-record-to-target-hand incidence;
2. reduce numerator and reach records to 193 by 32 hand arrays on-device;
3. compute the two totals on-device with a controlled Float64 error contract;
   and
4. return roughly 100 KB per seat instead of 70-79 MB.

That experiment attacks the measured 30.1% CPU phase and most remaining D2H
bytes. It must compare against this resident incumbent and preserve every h32
stop and selection decision. A custom fused sparse kernel is deferred until
after that simpler boundary is measured.

## Decision

1. Make device-resident terminal contraction the h32 exact partial-verifier
   incumbent for 32-hand six-seat workloads.
2. Retain the transferred CuPy path as a correctness oracle and small-axis
   fallback; do not install a fitted size selector from this audit.
3. Preserve Float64 arithmetic, exact CPU public-tree reversal, blueprint-cap
   stopping, and the set-valued fixed-envelope selector.
4. Continue to charge a complete resident cache per target in one-shot
   economics until a real runtime context demonstrates legitimate board or
   shift reuse.
5. Preregister one device-side hand-aggregation successor against the new
   200.480-second charged incumbent.
6. After that bounded successor, prioritize a wider public-action tree or
   multi-board strategy audit before additional kernel polishing. The project
   must not optimize the one-bet river laboratory indefinitely.

## What this establishes—and what it does not

This result establishes an exact, fully charged `2.979x` systems improvement
for the h32 candidate-verification customer already shown to recover sparse
safe strategy value. Combined with ADR-0108's `2.171x` early-stop gain, the
same 13-policy portfolio now costs roughly one sixth of indiscriminate legacy
full-vector verification.

It does not improve a strategy, establish online latency, validate another
h32 board, handle multiple bet sizes or side pots, or prove coalition safety.
At 25-80 seconds per portfolio target, this remains an offline/laboratory
verifier—not a real-time six-max bot.

## Dissent protocol

**Confidence:** extremely high in exactness and same-board h32 economics; high
in the transfer attribution; moderate in broader h32 board transfer.

**Opposing evidence:** fresh h7 seat three loses 22.4% one-shot. Residency has
a real crossover, and the current audit contains only one h32 board.

**Largest risk:** continued systems wins create false confidence while the
strategic model remains a one-bet, equal-stack river game. The next low-risk
hand-fold win must be followed by structural game widening.

**Cheapest falsification:** run the accepted resident verifier on a fresh h32
board. A selection mismatch rejects correctness transfer; a charged speedup
below one rejects the economic generalization while leaving this artifact
valid.
