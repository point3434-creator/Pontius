# ADR-0113: Fresh-board transfer is real, conditional, and available by step two

**Status:** Accepted; all frozen mechanism gates passed, strategic and ordering
outcomes recorded without changing the preregistration

**Date:** 2026-08-20

## Result

ADR-0112 passed every gate on a genuinely fresh h32 river board.

The fixed-envelope architecture transferred strategically, but not
universally. One of four targets selected a non-blueprint policy: the
blocker-heavy local shift chose the `0.50` behavioral interpolation between
warm current iterations one and two. It reduced normalized NashConv by
`1.3784127929423461e-4`, or 6.089% of the target-belief blueprint residual.

The balanced local target and both dense strength targets retained their
blueprints. That is a useful conditional result, not a failed transfer: the
same generator/verifier/selector stack found one exact six-seat Pareto
improvement and rejected multiple aggregate improvements that breached a
single seat's blueprint cap.

The result artifact is
`experiments/results/fresh-h32-strategy-transfer-audit-v1.json`, SHA-256
`af0a725f89d18eaf98e924fa0423176a8a8be6f6e477234fa492304101db3cf9`,
140,295,654 bytes. The preregistration commit is `7953408`.

## Gate closure

All frozen counts reproduced:

- two independently trained source families;
- 128 source DCFR steps and six full source checkpoints;
- four target beliefs, 32 warm-search steps, and 16 target checkpoints;
- 52 candidate rows;
- 56 complete resident profiles and 336 resident seat rows; and
- one six-seat transferred/resident cross-check.

Every source and target checkpoint digest reproduced. Both games contained
6,144 information sets and 12,288 hand-action entries. Target axes and support
were unchanged, all likelihoods stayed in `[1,2]`, every policy and state was
finite, and every certificate carried the ADR-0111 immutable-anchor scope.

The maximum exactness errors were:

| Check | Maximum |
|---|---:|
| transferred/resident utility | `2.470e-15` |
| transferred/resident best response | `2.456e-15` |
| transferred/resident deviation gain | `5.274e-16` |
| quality-vector sum | `0` |
| six-seat zero-sum residual | `8.441e-15` |

All six literal best-response action maps matched. Both partial-verifier orders
selected the same digest as complete full-pool evaluation, and every selected
policy remained inside all six immutable blueprint caps.

## Fresh source quality

The two new average-64 blueprints were strong but board variation was material:

| Family | Normalized source NashConv | Training wall | Median step |
|---|---:|---:|---:|
| balanced | `0.0016967331` | 1,770.51 s | 27.55 s |
| blocker-heavy | `0.0023188798` | 1,469.87 s | 22.93 s |

Relative to the original board's iteration-64 values, balanced improved by
9.45% while blocker-heavy worsened by 25.29%. The old observation that the two
generated families converge almost identically does not transfer to this
board. A single board cannot support one universal source-quality curve.

## Strategy outcomes

| Family / target | Mean marginal TV | Blueprint normalized NashConv | Selected | Normalized reduction | Feasible non-blueprint candidates |
|---|---:|---:|---|---:|---:|
| balanced / local seat 5 | `0.0067973` | `0.00219255` | blueprint | `0` | 0 |
| balanced / dense strength | `0.0674954` | `0.01157030` | blueprint | `0` | 0 |
| blocker / local seat 5 | `0.0056209` | `0.00226362` | interpolation `0.50` | `1.37841e-4` | 4 |
| blocker / dense strength | `0.0724498` | `0.01380798` | blueprint | `0` | 0 |

Each target also contained the warm-average-one identity candidate, so the
full feasible counts were `1,1,5,1`. On the three null targets it exercised the
natural abstention path: normalized reductions were at Float64 noise scale and
the blueprint remained inside the raw guard.

### The positive target is robust

For blocker-heavy local adaptation, the selected candidate reduced all six
deviation gains. Raw seat deltas ranged from `-3.4861e-5` to `-1.4581e-3`;
the tightest seat remained more than eleven thousand raw guards inside its
cap. The result is not a boundary-tolerance accident.

The useful candidate ladder was:

| Candidate | Available after warm step | Normalized reduction | Feasible |
|---|---:|---:|---|
| current 1 | 1 | `1.16614e-4` | yes |
| average 2 | 2 | `9.93718e-5` | yes |
| interpolation `0.25` | 2 | `1.31453e-4` | yes |
| interpolation `0.50` | 2 | `1.37841e-4` | yes |
| interpolation `0.75` | 2 | `1.22009e-4` | no; seat 2 |

Current one was available after 23.376 seconds of target search. Both useful
interpolations were available after step two at 46.378 seconds. Continuing to
step eight cost 184.332 seconds and produced no better feasible policy.

The original board's two local fixed-envelope selections were interpolation
`0.75` and interpolation `0.50`; those were also constructible after step two.
This cross-board observation motivates an exact zero-evaluation availability
replay before any more search iterations are optimized.

### The verifier prevented false progress

The balanced local target contained small aggregate improvements that were not
unilaterally safe. Warm average two improved normalized NashConv by
`4.0600e-5` but exceeded seat 4's raw cap by `1.073e-4`; current one improved
by `3.7761e-5` but exceeded that cap by `2.267e-4`.

On the balanced dense target, source current-48 appeared better in aggregate by
`3.4246e-4` normalized, yet breached seat 1's raw cap by `0.003567`. Blind
aggregate acceptance would have shipped both classes of false progress. The
fixed six-seat vector is doing strategic work, not merely auditing code.

## Predecessor hypothesis

Moving the local perturbation from seat 3 to seat 5 produced a split result:

- balanced: seat 4 was the modal maximum-cap-excess seat and dominated seven
  infeasible candidates, matching the frozen predecessor prediction; and
- blocker-heavy: seat 2 was modal, while seat 4 dominated only one infeasible
  candidate.

The mechanism transfers through one range family, not both. Public acting order
matters, but range structure can move the binding seat away from the cyclic
predecessor. A hard predecessor selector is rejected.

## Seat-order result

The frozen ascending-absolute-cap comparison produced:

| Family / target | Fixed seats | Cap-order seats | Charged speedup |
|---|---:|---:|---:|
| balanced / local | 20 | 25 | `0.916x` |
| balanced / dense | 18 | 21 | `1.022x` |
| blocker / local | 48 | 40 | `1.285x` |
| blocker / dense | 19 | 18 | `1.254x` |
| pooled | 105 | 104 | `1.123x` |

The pooled speedup is real but not robust enough to adopt. Only one seat read
was removed; most of the wall advantage came from moving expensive upstream
seats earlier or later. Balanced/local exposes the proxy error cleanly: seat 4
had the largest excess most often, but its large absolute blueprint cap placed
it last. Absolute cap magnitude and candidate violation probability are
different objects.

One explicitly post-freeze diagnostic used the already preregistered
predecessor seat first on local shifts and absolute-cap order for the remaining
seats. It would have produced 97 reads and `1.220x` pooled speedup. This rule was
not frozen, is not part of the artifact gates, and is not adopted. It is the
candidate to preregister on a second unseen board.

## Economics and resources

Total wall time was 4,605.148 seconds, decomposed as:

| Phase | Share |
|---|---:|
| source training | 70.36% |
| target warm search | 17.61% |
| complete resident teacher profiles | 9.82% |
| source quality evaluation | 1.12% |
| transferred/resident cross-check | 0.61% |
| resident cache compilation | 0.27% |
| compilation, marginals, serialization, and residual | 0.21% |

The architectural conclusion is now different from ADR-0110's starting point:
verifier-cache work is not the development bottleneck. Training plus online
warm search consumes 87.98% of the complete experiment.

Frozen resource ceilings all passed:

- maximum training step: 30.444 s;
- maximum complete profile: 28.144 s;
- maximum resident seat read: 1.779 s;
- maximum static cache compile: 3.334 s;
- maximum host numeric estimate: 1.475 GB; and
- maximum CuPy pool: 9.416 GB of the 12 GB ceiling.

The 9.416 GB fresh-board pool is higher than ADR-0110's 7.935 GB maximum.
Resident correctness transfers, but GPU headroom is board-dependent and has
not been proved for wider public trees.

Early verification still matters. Against complete six-seat candidate reads,
the fixed order saved between `1.529x` and `3.875x` per target; the cap order
saved between `1.990x` and `4.706x` on the three targets where it won. But
further verifier micro-optimization cannot materially shorten a run dominated
by CFR terminal contractions.

## Decision

Accept the fresh-board result and retain:

- average-64 as immutable blueprint anchor;
- current-one plus step-two interpolation as the highest-value measured
  candidate family;
- resident exact full-vector evaluation as teacher;
- fixed-envelope, order-independent selection; and
- fixed seat order as the production default until an unseen-board order rule
  passes.

Do not claim universal local adaptation. The measured rate is one useful target
of four on this board, two of four on the original board. The positive result
is enough to justify accelerating the search engine, not enough to declare the
generator solved.

## Next actions

1. Run a zero-new-evaluation availability replay across both h32 boards. Test
   whether stopping after warm step two reproduces every full-pool selected
   digest and quantify avoided search/evaluation work.
2. If it does, make the two-step candidate ladder the systems customer and
   integrate the existing resident terminal contraction into the CFR
   traverser. Training and search, not verification, now own 87.98% of wall.
3. Gate resident-CFR one-step regret/action numerators against the transferred
   solver at h4, h7, and frozen h32 checkpoints before any long trajectory.
4. Preregister predecessor-first-then-cap ordering on a second unseen board;
   do not fit or adopt it from this result.
5. After search latency is reduced, widen public actions before multiplying
   boards. One bet size remains the largest strategic scope gap.

## Dissent protocol

**Confidence:** extremely high in exactness and fixed-envelope semantics; high
that local adaptation transferred at least once; moderate that step two is the
right stopping point; low that either seat-order proxy transfers universally.

**Opposing evidence:** three of four fresh targets retained the blueprint, and
one of two local range families failed completely. The generator's recall is
still narrow. The positive target does not prove useful adaptation on a board
distribution, multi-bet tree, earlier street, or real 1,326-combo ranges.

**Largest risk:** optimizing the two-step reduced-game search before verifying
that the same candidate geometry survives wider public actions. The proposed
resident-CFR work is justified as an enabling exact primitive, not as evidence
that the current reduced strategy is deployable NLHE.

**Cheapest falsification:** the zero-evaluation availability replay. If any
accepted full-pool policy needs iterations four or eight, the proposed
two-step customer is wrong before a solver backend is changed.
