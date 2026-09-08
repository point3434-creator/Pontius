# ADR-0092: Corrected h32 DCFR ladder passes; quality continues through 32

**Status:** Accepted; restartable reduced-game strategy artifact retained,
terminal-kernel optimization authorized before extending the ladder

**Date:** 2026-08-20

## Result

The frozen ADR-0091 audit passed all 25 gates from clean commit
`922ca8067ddaba8c007e0caf08fc449d13e7475b`.

The canonical local artifact is
`experiments/results/leaf-adjoint-checkpoint-ladder-v2.json`:

- SHA-256:
  `242de5f0a42693248f98cc8f127f4fc892606df58e94d28c107d542b1276736b`;
- size: 43,176,026 bytes; and
- measured wall time: 2,117.692 seconds.

The frozen config and implementation hashes reproduce ADR-0091 exactly:

- config:
  `b8332fe1de5a9701bc268ebf47dcdebfc1f3e62fdc045dd401866b17c7232e8a`;
- corrected runner:
  `5562abf4fad803a12a794c31e3e057b679546480a8f2cd8f23f65d0d931b01b3`;
  and
- rejected v1 runner retained as an immutable dependency:
  `4c24a7784057aa40a35f1743c81bf347f42ef22e9d3bedcfc8e096c60965da51`.

## Strategy-quality curve

Normalized NashConv is NashConv divided by the 30-chip payoff span.

### Balanced factor belief

| Iteration | Train s | Current | Average | Marginal average gain/s |
|---:|---:|---:|---:|---:|
| 1 | 28.813 | 0.078328 | 0.489604 | n/a |
| 2 | 57.699 | 0.070121 | 0.138690 | 1.21484e-2 |
| 4 | 115.260 | 0.064739 | 0.072266 | 1.15397e-3 |
| 8 | 230.735 | 0.044831 | 0.042626 | 2.56681e-4 |
| 16 | 463.681 | 0.068962 | 0.029790 | 5.51044e-5 |
| 32 | 918.077 | **0.006640** | **0.007913** | 4.81450e-5 |

### Blocker-heavy factor belief

| Iteration | Train s | Current | Average | Marginal average gain/s |
|---:|---:|---:|---:|---:|
| 1 | 21.348 | 0.079736 | 0.487627 | n/a |
| 2 | 42.570 | 0.075664 | 0.139019 | 1.64270e-2 |
| 4 | 85.201 | 0.074909 | 0.070144 | 1.61560e-3 |
| 8 | 170.367 | 0.043909 | 0.057467 | 1.48850e-4 |
| 16 | 340.482 | 0.037601 | 0.027612 | 1.75496e-4 |
| 32 | 678.597 | **0.008694** | **0.007902** | 5.82939e-5 |

Both current and average policies attain their best measured NashConv at
iteration 32 in both families. There are no negative average-policy intervals.
Balanced current quality cycles upward from iteration 8 to 16, then improves
sharply at 32; this is why the ADR correctly did not require monotonic current
strategies.

Final average raw NashConv is `0.237383` balanced and `0.237059`
blocker-heavy. Relative to uniform, normalized NashConv falls by 98.384% and
98.380%. Relative to iteration two, it falls by 94.295% and 94.316%.

Most importantly for the next decision, iterations 17-32 remove 73.438% and
71.382% of the iteration-16 average NashConv. Their marginal gain is still
`4.81e-5` and `5.83e-5` normalized quality per training second. The curve has
not established a plateau.

The relative convergence factor improves in the final doubling: residual
average NashConv falls by about 3.5-3.8x. Absolute quality gained per second
does not accelerate, however. Balanced falls slightly from `5.51e-5` to
`4.81e-5` normalized gain/s, while blocker-heavy falls from `1.75e-4` to
`5.83e-5`. Under the quality-per-millisecond objective, the defensible claim is
"still materially improving," not "accelerating."

The average first beats current at iteration four for blocker-heavy and
iteration eight for balanced. Current retakes blocker-heavy at iteration eight,
but average is permanently ahead in both families by iteration 16. At 32 the
two policies are close: current is marginally better balanced and average is
marginally better blocker-heavy.

The two final average normalized values differ by only 0.14%. This is useful
evidence that one cost/quality model may serve these two range families, but
two generated beliefs on one board are nowhere near enough to fit that rule.

For context only, the independent h7 checkpoint-64 averages in the ADR-0075
source normalize to `0.004971` balanced and `0.004140` blocker-heavy. Extending
h32 to 64 can test whether width changes the convergence rate rather than
assuming that the apparent similarity transfers.

## Per-seat result

Final average deviation gains are:

- balanced: `[0.046432, 0.045710, 0.040572, 0.035518, 0.035737,
  0.033415]`; and
- blocker-heavy: `[0.040176, 0.040473, 0.038719, 0.041019, 0.043128,
  0.033545]`.

The largest-to-smallest ratios are 1.390 and 1.286. At iteration two, seat zero
had been the dominant residual in both families. The much flatter final
vectors show that the aggregate gain is not hiding one chronically weak seat
or simply preserving the alternating-order transient.

This remains unilateral reduced-game NashConv. It is not coalition safety.

## Restart and source-reuse correctness

All four small controls passed exactly:

- h4 and h7;
- balanced and blocker-heavy;
- maximum regret or strategy-sum error `0.0`;
- current and average policy identity; and
- final state-digest identity.

Both wide iteration-16 serialize/restore boundaries passed exact immediate
state-digest identity and the restored solvers produced the final trajectories.
The final state digests are:

- balanced:
  `9a49d1e394a08c94b05a6c9f07c0bce90910c43801640625f72ad92d28f77644`;
  and
- blocker-heavy:
  `b2d9c4e489cbc39a40f038a764d2e459a9c7b6ddb4a22827369d69b5d6433ac1`.

Independent post-run validation rehashed every one of the 12 wide checkpoint
payloads. Reconstructing current policies from regrets and average policies
from strategy sums reproduced every checkpoint and quality-policy digest.

The corrected measurement matrix executed exactly nine live and three reused
profiles per family. All three reuse points matched both source lineages
exactly.

The live iteration-two current policies again differ bitwise from ADR-0085:

- balanced maximum probability error `2.25e-14`, mean TV `8.36e-17`;
- blocker-heavy maximum probability error `3.52e-14`, mean TV `1.32e-16`;
  and
- no action probability differs by more than `1e-12`.

Their independently measured NashConv differs from ADR-0087 by only
`4.44e-16` in each family. The v1 value was strategically accurate but was not
a literal label for the live policy. Rejecting reuse and measuring live was the
right semantic choice.

## Exactness and resource result

Final seat-zero CPU/GPU comparisons returned:

- maximum profile-utility error `9.66e-15`;
- maximum best-response error `1.46e-14`;
- maximum deviation-gain error `4.97e-15`;
- zero raw best-response action mismatches; and
- charged speedups `4.818x` balanced and `4.536x` blocker-heavy.

Across all quality rows, maximum zero-sum residual was `2.19e-14`.

Measured peaks were:

- host numeric bytes: 1,497,068,624;
- CuPy pool bytes: 2,126,605,824;
- maximum training step: 31.099 seconds; and
- maximum live six-seat quality evaluation: 29.908 seconds.

All are inside their frozen gates.

Checkpoint JSON states stabilize near 2.77 MB apiece. The verbose transparent
format is already practical for laboratory restart and branch experiments,
though it is not a production checkpoint encoding.

## Tie geometry and the training incumbent

Sharp current policies retain exactly the difficult geometry that motivated
the interval/tie semantics:

- balanced current has 1,984 exact action ties at iteration eight and a
  minimum nonzero action gap of `1.29e-23` at iteration 16;
- final current still has 32 exact ties balanced and five blocker-heavy; and
- every measured average has zero exact ties.

The final averages remain non-pure at every information set. They contain
2,212 and 2,236 distinct action distributions with mean entropy `0.0874` and
`0.0791`. The average is therefore not merely smoothing a mostly literal pure
table; it is the strategically stable customer the representation work must
serve.

Balanced current's 54% raw-NashConv regression from iteration 8 to 16 also
turns the certified-incumbent pattern into a training requirement. A product
that deployed "current after N iterations" would have shipped a large quality
regression at N=16. An exact-evaluated best-so-far incumbent would retain the
iteration-eight profile until a later candidate passed its guard. Extend the
ladder with both literal current/average curves and an acceptance-gated
best-so-far trace; do not add a seat selector, since the final per-seat data
shows the early seat asymmetry was transient.

## The decisive efficiency diagnosis

Training itself cost 918.1 seconds balanced and 678.6 seconds blocker-heavy.
Every step used a fixed 435 or 311 sparse terminal batches. Terminal
contraction consumed median 99.831% and 99.776% of full step wall time.

The remaining CFR work—policy compilation, average accumulation, reverse
public-tree adjoint, regret application, discounting, and checkpoint logic—is
collectively below one percent. Changing CFR variants or optimizing the Python
public-tree loop cannot materially improve strategy quality per millisecond at
this point.

The current CuPy path nevertheless crosses the PCIe/runtime boundary for every
batch:

1. build source features on the CPU;
2. copy one batch to the GPU;
3. run two CSR-dense products;
4. copy the compatible records back to the CPU; and
5. fold rank/components on the CPU.

This repeats hundreds of times per CFR step. The result therefore authorizes
optimizing the terminal contraction, not a general native rewrite.

## Decision

1. Accept the iteration-32 current and average policies and exact restart
   states as the strongest strategy artifacts produced so far in this reduced
   game.
2. Do not call them a six-max NLHE bot or a solved game.
3. Do not stop the learning curve at 32; the last interval still buys material
   quality.
4. Before paying for iterations 33-64, run a frozen step-33 batch-width and
   phase-attribution screen from both exact iteration-32 states.
5. Compare the existing width 384 with wider fixed batches under identical
   restored states. Trace host-to-device, sparse-kernel, device-to-host, and
   non-operator residual bills, and compare the resulting accumulator/policy
   states numerically.
6. If widening gives a clean material win, use it immediately and then extend
   the ladder. If transfers and host folds dominate after widening, build the
   transfer-resident GPU contraction that keeps features, intermediate records,
   reductions, and accumulators on device and returns only per-hand leaf values.

This order gets a cheap parameter win if one exists and produces the phase
evidence needed to scope a custom CUDA kernel. It does not confuse a profiling
screen with strategy improvement.

## What this establishes—and what it does not

This is the first artifact chain in the project that closes the loop from a
dense-free h32 CFR trajectory through exact dense-free best responses,
restartable learning curves, and a policy that keeps improving well beyond the
two-step pilot. The architecture now produces and measures strategy, not only
evaluators.

It remains one board, one bet size, equal stacks, 32 constructed hands per
seat, and two factor-belief families. Generalization across boards, ranges,
betting trees, and stack configurations remains completely unproven. Exact
multiway Nash equilibrium convergence is also not guaranteed by multiplayer
DCFR.

## Dissent protocol

**Confidence:** very high in exactness, restartability, and the measured local
curve; high that terminal contraction is the correct kernel customer;
moderate that the curve continues improving through 64; low that this quality
transfers across boards without replication.

**Opposing evidence:** current strategies are non-monotone, average-policy
entropy changes non-monotonically around iteration 16, and a single public
board can make a smooth curve look more general than it is.

**Largest risk:** optimizing a sophisticated exact river kernel before proving
that the broader abstraction and neural/global policy can supply realistic
states. The counterweight is that the same contraction is already the measured
99.8% bottleneck for both training and exact acceptance evaluation.

**Cheapest falsification:** restored step 33 at wider batch widths. It costs one
step per arm, preserves the exact strategy source, and directly reveals
whether hundreds of synchronized transfer calls are avoidable without a new
kernel.
