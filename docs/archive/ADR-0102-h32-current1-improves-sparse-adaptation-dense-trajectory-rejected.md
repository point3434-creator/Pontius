# ADR-0102: h32 current one improves sparse adaptation; dense trajectory rejected

**Status:** Accepted as evidence for early sharp candidates and an anytime
vector gate; longer warm trajectory rejected; interpolation becomes the next
strategic test

**Date:** 2026-08-20

## Result

The frozen ADR-0101 audit completed from clean commit `728b6bd` with every
mechanism gate passing. The canonical local artifact is
`experiments/results/h32-warm-candidate-stream-v1.json`:

- SHA-256:
  `b432eda21d1978b1dd576a9f4e7451250f1d53dcf9a88a6efa739d681ecb6f33`;
- size: 14,803,058 bytes;
- config SHA-256:
  `154a281bf4ab2c7808b602581f2f68be25095fe9c4a486080f6060172cb78883`;
  and
- implementation SHA-256:
  `2f00b5123439dc3a933728461a927d1997d731c62d265a867d049dcc78ee54a9`.

Measured wall time was 901.421 seconds, or 15.02 minutes. The audit produced
four target rows, twenty new exact profile evaluations, sixteen extension
steps, and four iteration-eight states. All target descriptors, source states,
source policies, iteration-four restores, and iteration-eight checkpoint
round trips reproduce exactly.

The strategic answer has two parts:

1. current one is unilateral-safe and improves upon average two on both local
   blocker shifts; and
2. no current or average candidate through iteration eight improves either
   dense strength shift. Longer search amplifies the harm.

Thus average four was not merely the wrong policy kind. It was also too late
for the sparse customer and part of a fundamentally wrong dense adaptation
trajectory.

## Candidate curves

All values are NashConv divided by the 30-chip payoff span. Positive reduction
means improvement from the target-belief iteration-64 blueprint.

### Balanced local blocker

| Candidate | NashConv | Reduction | Headroom captured | Baseline unilateral-safe |
|---|---:|---:|---:|---|
| current 1 | **0.002077** | **+0.000154** | **6.901%** | **yes** |
| average 2 | 0.002105 | +0.000126 | 5.646% | yes |
| current 2 | 0.002045 | +0.000186 | 8.321% | no: seat 2 |
| average 4 | 0.002102 | +0.000129 | 5.765% | no: seat 2 |
| current 4 | 0.002353 | -0.000123 | -5.498% | no |
| current 8 | 0.002684 | -0.000453 | -20.313% | no |
| average 8 | 0.002436 | -0.000205 | -9.209% | no |

### Blocker-heavy local blocker

| Candidate | NashConv | Reduction | Headroom captured | Baseline unilateral-safe |
|---|---:|---:|---:|---|
| current 1 | **0.001778** | **+0.000110** | **5.839%** | **yes** |
| average 2 | 0.001793 | +0.000095 | 5.054% | yes |
| current 2 | 0.001756 | +0.000132 | 7.002% | no: seat 2 |
| average 4 | 0.001755 | +0.000133 | 7.060% | no: seat 2 |
| current 4 | 0.001796 | +0.000092 | 4.877% | no: seat 2 |
| current 8 | 0.002228 | -0.000340 | -17.984% | no |
| average 8 | 0.001919 | -0.000031 | -1.644% | no |

Current one improves every seat's deviation gain on both local targets. Its
smallest safety margins are seat one balanced at `-0.000217` and seat two
blocker-heavy at `-0.000143`, still about five orders above the `3e-9` guard.

Current two improves aggregate NashConv further in both cases, but seat two's
delta crosses to `+0.000139` balanced and `+0.000105` blocker-heavy. Every
other seat remains below its blueprint deviation gain. The repeated one-seat
boundary is a concrete interpolation opportunity, not a vague selector
signal.

## Dense strength trajectory

Neither policy kind rescues either all-seat strength shift.

| Family | Candidate | Reduction | Headroom captured | Seats worsened |
|---|---|---:|---:|---:|
| Balanced | current 1 | -0.000752 | -6.633% | 6/6 |
| Balanced | current 2 | -0.001826 | -16.098% | 6/6 |
| Balanced | current 4 | -0.004101 | -36.153% | 6/6 |
| Balanced | current 8 | -0.006619 | -58.346% | 6/6 |
| Balanced | average 8 | -0.004868 | -42.914% | 6/6 |
| Blocker-heavy | current 1 | -0.000894 | -6.889% | 6/6 |
| Blocker-heavy | current 2 | -0.002591 | -19.964% | 6/6 |
| Blocker-heavy | current 4 | -0.005550 | -42.759% | 6/6 |
| Blocker-heavy | current 8 | -0.010168 | -78.337% | 6/6 |
| Blocker-heavy | average 8 | -0.007044 | -54.274% | 6/6 |

The current-policy response is already directionally wrong after one
iteration and worsens monotonically at every measured checkpoint. Averaging
reduces the damage but does not reverse it. This rejects the explanation that
ADR-0099 merely stopped before a dense recovery.

The policy moves themselves remain small at current one: mean total variation
from the blueprint is `0.000269` balanced strength and `0.000240`
blocker-heavy strength. Small policy distance is not a safety certificate; all
six deviation gains move adversely.

## Portfolio result

The full interleaved unilateral incumbent accepts current one on each local
target and rejects every subsequent candidate. It keeps the blueprint on both
dense targets.

Combined normalized results across four targets are:

| Portfolio | Final total NashConv | Reduction from blueprints | Increment over ADR-0099 safe stream |
|---|---:|---:|---:|
| ADR-0099 averages through 4 | 0.028221035 | 0.000221360 | baseline |
| Average-only through 8 | 0.028221035 | 0.000221360 | 0 |
| Current-only through 8 | **0.028178213** | **0.000264181** | **+0.000042822** |
| Full interleaved | **0.028178213** | **0.000264181** | **+0.000042822** |

The current-one incumbents add 19.34% more safe reduction than the previous
average-two incumbents. Current-only beats average-only, but this is entirely
an early local-shift result; it does not establish a general current-policy
preference.

Frozen hypotheses resolve as follows:

1. any current candidate unilateral-safe: **true**, two accepts;
2. any strength current candidate unilateral-safe: **false**;
3. any strength average eight unilateral-safe versus blueprint: **false**;
4. full stream improves over average-only through four: **true**;
5. full stream total unilateral reduction positive: **true**; and
6. current-only finishes below average-only: **true**.

## Quality per millisecond

The audit's new work spent:

- 496.946 seconds in twenty exact profile evaluations;
- 396.140 seconds in sixteen extension steps; and
- 8.335 seconds elsewhere.

The frozen full-stream precompiled bill, including all eight candidate reads
and search through eight on every target, is 1,595.261 seconds. It returns the
same unilateral incumbents found by current one. Candidate breadth without an
early stopping mechanism is therefore almost pure waste on this matrix.

A post-run diagnostic charges only the declared current-one search and exact
read on all four targets. It costs 200.121 seconds and produces normalized
safe reduction `0.000264181`, or `1.320e-9` per millisecond. The ADR-0100
average-two path cost 300.967 seconds for reduction `0.000221360`, or about
`7.35e-10` per millisecond. Current one provides:

- 19.34% more safe quality;
- 33.5% lower verified cost; and
- approximately 1.80x the quality per verified millisecond.

This is a post-run diagnostic, not a retroactive frozen portfolio. It uses
only costs and labels already present in the declared stream.

Exact verification is still seconds-scale and not deployable online. The
result identifies a better verifier customer and stopping point; it does not
solve the verifier.

## Correctness and resources

All frozen gates pass:

- maximum quality evaluation: 28.762 seconds;
- maximum extension step: 29.240 seconds;
- maximum target workspace compilation: 66.184 milliseconds;
- maximum zero-sum residual: `7.42e-15`;
- maximum host numeric estimate: 1.497 GB;
- maximum CuPy pool: 2.127 GB; and
- exact 435/311 sparse-batch identity on every source and new policy.

Independent post-run reconstruction validates all four iteration-eight state
digests plus all eight final current/average policy digests.

## Decision

1. Add current one to the reduced game's accepted candidate vocabulary. It is
   the highest measured safe quality-per-millisecond warm candidate.
2. Reject continuation along the same warm trajectory as a response to the
   dense strength shifts. Current and average policies both move monotonically
   away from the blueprint through iteration eight.
3. Reject a fixed iteration-eight endpoint for the local shifts. Both current
   and average have already passed their useful window.
4. Retain the exact all-six-seat incumbent. It converts severe oscillation and
   longer-horizon regression into a non-worsening product stream.
5. Do not fit a local-versus-dense shift selector. The split is replicated but
   remains one board and two generated target rules.
6. Run one cheap, frozen behavioral interpolation audit between current one
   and current two at fixed coefficients on all four targets. Current two
   contains more aggregate local value and violates only seat two; the dense
   targets provide mandatory negative controls.
7. If interpolation expands safe local value, define that candidate portfolio
   as the first h32 policy-delta verifier workload. The verifier is now
   justified in principle, but its required policy-delta magnitudes and number
   of reads should be measured after this cheap candidate-shaping step.
8. For dense belief movement, move to a different generator after the
   interpolation control: proximal/trust-region updates, belief-corrected
   regret initialization, or per-seat sub-iteration checkpoints. More
   iterations of the present update are rejected.
9. Preserve the ADR-0078 peak-then-decline rank question as a separate
   representation audit: compare current and average ranks at matched later
   checkpoints over full tolerance curves. It must not displace the more
   strategy-relevant interpolation test.

## Architectural meaning

The best interface is no longer “blueprint plus N CFR iterations.” It is:

> blueprint plus an ordered portfolio of cheap policy directions, guarded at
> every opportunity by a non-worsening six-seat incumbent.

The earliest sharp direction now dominates the later averages on both quality
and cost. Spare decision compute should explore alternative directions,
interpolations, or likely future states—not continue blindly down a trajectory
whose exact incumbent has already rejected successive candidates.

## What this establishes—and what it does not

Within the reduced h32 game, one warm DCFR update produces a replicated safe
local blocker correction. A second update contains more aggregate value but
crosses one seat's safety boundary. The same solver is directionally wrong for
both dense strength shifts from its first update onward.

This does not establish a production stopping rule, natural-posterior transfer,
coalition safety, or full-game strength. Exact current-one verification still
costs roughly 200 seconds across four laboratory targets.

## Dissent protocol

**Confidence:** very high in the measured candidate curves and state identity;
high that current-one/current-two interpolation is now the cheapest useful
test; moderate that a fixed interpolation coefficient will improve both local
incumbents safely.

**Opposing evidence:** behavioral policy interpolation need not interpolate
NashConv or individual deviation gains linearly. Current two's seat-two
violation may appear immediately for any positive movement from current one,
or other constraints may become active between sampled coefficients.

**Largest risk:** optimizing a tiny safe gain on two synthetic local shifts
while the strategically larger dense shifts remain completely unsolved.

**Cheapest falsification:** freeze three interior coefficients between current
one and current two, evaluate them on all four targets, and retain the same
exact vector gate. No training or new representation is required.
