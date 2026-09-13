# River GPU execution assessment 001

The eager float64 GPU port reduced median fixed-work solve time by 1.31x on
checkback and 1.56x on the raise tree. Final independently checked strategy error
was effectively unchanged. Including fresh process startup and a separate exact
audit reduces the observed advantage to 1.11x and 1.31x. This is useful execution
evidence, not a stronger strategy or an adopted bot component.

Status: exploratory continuation completed. The original raise trajectory-parity
gate FAILED and remains failed. The numerical diagnosis and continuation plan
were retained before any timing comparison ran. No tolerance was rewritten.

## Fixed experiment

- Same two expanded case-001 river games as river-cfr-expanded-001; one board and
  range pair, two nested public trees, not independent board samples.
- 1,081 private hands per player, complete compatibility matrices, float64
  chance-weighted payoffs. Checkback: 15 nodes / 9 terminals. Raise: 27 / 17.
- Alternating player 0 then 1, released-code DCFR+ alpha 1.5, denominator 1.5,
  averaging exponent 4. Same reach-weighted averaging and initial uniform policy.
- 2,048 iterations; CPU and eager CuPy; three fresh processes per game/arm.
  Alternating arm order across repeats. One CPU BLAS thread; no algorithm tuning.
- CPython 3.14.6, NumPy 2.5.2, CuPy 14.2.0, RTX 5080, driver 610.88.
  Full library/build/runtime observations are in environment.txt.
- 180-second timeout per monitored worker; private memory sampled every 50 ms
  with a 3,072 MiB stop. This is not a hard instantaneous memory cap.
  CuPy's allocation pool is limited to 1,024 MiB; CUDA context/library allocations
  outside that pool are not covered by this allocator limit.

Original plan SHA-256:
`f98da640f302a1afe7f8ee60a85eaa99e8e4328050c0b5ef3b0e9f6b941384c8`.

Exploratory continuation plan SHA-256:
`c3ba5ff1c9a074cb2322a0d48d2d28177cbf0196bad4e0c94bcf1c5c4357f411`.

The reference solver is copied byte-for-byte. The small adapter rebinds its
array operations to CuPy and expresses masked normalization with a safe positive
denominator because CuPy divide lacks the NumPy out/where behavior used here.
All state and payoff arrays stay float64. No production module was changed.

## Numerical refusal and diagnosis

Checkback passed the original 32-iteration all-state comparison with atol 1e-10,
rtol 1e-8. Raise refused on four policy entries; the largest reported violating
difference was 2.054e-10. No timing run launched before that refusal.

The subsequent diagnostic retained all 32 iterations. Independently evolving
raise trajectories differed by at most 2.389e-10 in policy, 1.609e-11 in regret,
and 1.675e-10 in averaging state. When each GPU step instead started from the
same CPU state, maximum differences were 9.582e-14 in policy, 2.152e-16 in
regret, and zero in averaging state. This supports reduction-rounding amplified
by normalization as the explanation; it is not a proof of universal equivalence.

The continuation is explicitly exploratory and post-diagnosis. It preserves
the failed original gate and requires the original final-quality rule:
GPU gap <= 1.01 * CPU gap + 1e-10. Each final repeat-zero policy was quantized
with the retained evaluator's 2^48 grid and independently evaluated using exact
rational best-response bounds over the original stored binary64 payoffs.
All repeat policies within each game/arm were byte-identical, so these four
audits cover all 12 final policies. CPU and GPU policy bytes are not identical.

## Measured results

Times are seconds; solve figures are medians of three synchronized fixed-work
runs. The final column is median fresh solve-process wall plus one separately
measured fresh exact-audit process. It is an accounting sum, not a single
integrated end-to-end invocation.

| Game | Device | Solve median [min, max] | Fresh solve process | Process plus audit |
|---|---|---:|---:|---:|
| Checkback | CPU | 7.397 [7.266, 7.404] | 8.019 | 10.647 |
| Checkback | GPU | 5.643 [5.532, 5.668] | 6.996 | 9.551 |
| Raise | CPU | 14.939 [14.802, 15.587] | 15.684 | 19.726 |
| Raise | GPU | 9.568 [9.560, 9.680] | 11.069 | 15.041 |

| Game | CPU exact exploitability | GPU exact exploitability | Absolute difference |
|---|---:|---:|---:|
| Checkback | 1.347959429715e-5 | 1.347959429700e-5 | 1.49e-16 |
| Raise | 1.320771803259e-4 | 1.320771803222e-4 | 3.70e-15 |

Exploitability is half the best-response gap. Units are ten per starting pot;
divide by ten for a fraction of pot. All four independent audits agreed with
the float evaluator within 1e-10. Neither device reached the unchanged strict
gap <= 1e-8 threshold on either game. This is checked approximate solving.

GPU setup, including import/context and payoff transfer, had medians 0.397 s
and 0.373 s. The 32-step warmup cost 0.459 s and 0.527 s; warmup is excluded
from the solve clock but included in the fresh-process totals. Fresh state
is constructed after warmup. Averaging plus download took about 0.8 and 1.1 ms.
Exact audit computation took about 1.44 and 2.80 s for the GPU policies.

The dedicated CuPy kernel cache was shared across sequential benchmark workers.
The first checkback parity process paid 2.992 s for import, compilation,
transfer and verification together. This diagnostic cost is retained separately;
it cannot be attributed solely to compilation. Fresh-process timings therefore
do not mean an empty filesystem kernel cache. There is no CUDA graph capture.

| Game | CPU peak private MiB | GPU process peak private MiB | CuPy pool reserved MiB |
|---|---:|---:|---:|
| Checkback | 190.9 | 1,162.6 | 45.4 |
| Raise | 236.5 | 1,256.3 | 90.5 |

Private memory is the maximum sampled across the three solve workers. Device
pool figures are allocator-reserved bytes, not total attributable GPU memory.
Whole-device observations include desktop/other activity and are not a per-job
peak. Exact audits ran in separate CPU processes; their maximum sampled private
memory was about 395 MiB and 734 MiB respectively. All monitored continuation
workers exited zero with no stop reason; the earlier parity refusal is retained.

## What this supports next

Separate 128-iteration CPU profiles attribute 84.7% and 86.5% of elapsed time
to payoff matrix-vector products. These instrumented timings are excluded from
the speed comparisons. GPU execution helps this workload, but startup and the
CPU audit materially reduce its net benefit, and GPU process memory is higher.

[GPU-CFR](https://arxiv.org/html/2609.11923v1) motivates compiling a fixed game
to reusable static dataflow and CUDA graph replay. This experiment implements
neither that compiler nor graph replay, and does not test its reported speedup.
The [released repository](https://github.com/lbn187/GPU-CFR) was inspected,
not executed or installed.

The next bounded question is whether replaying a fixed execution graph reduces
dispatch overhead enough to improve the complete measured cost. Preserve the
same float64 algorithm, correct iteration-dependent discount counter, fresh
reset after capture/warmup, and the independent audit. Include capture cost and
break-even reuse. If the gain remains small, stop this optimization lane rather
than build a general game compiler. Neural approximation remains a later,
separate capacity/generalization question.

Three local repeats characterize timing stability, not cross-machine confidence
or poker sampling variance. These are restricted heads-up river subgames, not
six-max play, a complete hand, or a validated live action deadline. No strategy
adoption, commit, push, or bot integration occurred.
