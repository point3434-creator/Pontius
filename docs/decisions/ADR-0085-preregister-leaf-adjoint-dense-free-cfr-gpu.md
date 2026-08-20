# ADR-0085: Preregister leaf-adjoint dense-free CFR and GPU audit

**Status:** Accepted after balanced h32 target-read and GPU engineering, but
before any blocker-heavy h32 leaf-adjoint or GPU result

**Date:** 2026-08-20

## Decision

Run one frozen audit of an exact dense-free DCFR step built from terminal-leaf
adjoints rather than policy-conditioned public-node tensor trains. The frozen
configuration is
`experiments/configs/leaf-adjoint-cfr-gpu-audit-v1.json`; its SHA-256 is
`f4083477db0d09124cc84831bcf6f86fc8492e83c217c9144cff2e4e2b46cce6`.
The result target is
`experiments/results/leaf-adjoint-cfr-gpu-audit-v1.json`.

This audit reconnects the exact open-mode stack to strategy generation. It
must establish three things in one artifact:

1. the new solver reproduces the existing dense `PublicTreeTensorCFR`
   trajectory at four and seven hands;
2. CPU and GPU leaf-adjoint reads agree at 32 hands; and
3. two complete six-traverser DCFR iterations execute on both 32-hand range
   families without a Cartesian deal table, producing reproducible current
   and average-policy checkpoints.

The audit does not claim that two iterations produce a strong policy, that
generic CuPy is an online kernel, or that multiplayer DCFR converges to a
unique equilibrium.

## Why public-node TT composition is not the full-step engine

The direct successor to ADR-0082 compiled a policy-conditioned TT at every
public node and read all action values through the ADR-0084 CSR maps. It is
exact, but the economic mechanism fails:

- at h7, one rounded full step took about 9.36 seconds versus 0.352 seconds
  for the dense solver;
- about 8.53 seconds was cache compilation and 0.81 seconds was action
  reading;
- 1,152 per-node SVDs dominated the step, with maximum rank 343 and maximum
  feature width 2,058; and
- the exact unrounded direct-sum alternative was worse: about 16.23 seconds,
  maximum rank 1,414, and approximately 2.1 GB of cached numeric storage.

These are mechanism rejections, not optimization invitations. The rounded
and unrounded modules remain as controls, but neither is the wide solver.

## Leaf-adjoint identity

For traverser `t`, attach every opponent action probability on a terminal
root-to-leaf path as a unary private-hand factor. Omit every action probability
belonging to `t`, and contract the terminal payoff and compatible-deal reach
once. This produces one numerator and reach vector per terminal leaf.

A reverse public-tree pass then applies `t`'s policies only below the
information set currently being read:

- at an opponent node, child vectors sum because the opponent policy was
  already absorbed into each terminal contraction;
- at a traverser node, each child vector is the exact counterfactual action
  numerator, and the node vector is their hand-wise policy fold; and
- zero counterfactual reach gives a declared conditional value of zero and an
  exactly zero regret update.

The asymmetry is essential. Omitting the traverser's entire path policy makes
all of its action alternatives visible in one reverse pass. No public-node TT,
dirty-closure recomposition, SVD, or raw floating `argmax` appears in the
read path.

Differently weighted terminal leaves share the same fixed card-incidence
operators. The implementation packs heterogeneous payoff/state features into
CSR batches capped at width 384. This cap was selected before the validation
family was opened.

## Small-axis solver bridge

Use the canonical six-seat, equal-stack, one-bet river tree at four and seven
hands for both balanced and blocker-heavy range families. Warm start every
solver from the immutable checkpoint-16 DCFR average policy in
`real-policy-source-v1.json` with regret mass 1.0.

For each of the four geometries, run two alternating DCFR iterations through:

- the dense joint-deal reference solver; and
- the external-axis leaf-adjoint solver on the identical representative
  public topology.

After every iteration compare the complete regret table, strategy-sum table,
current policy, and average policy. Each maximum absolute error must be at
most `1e-10`. The representative topology signature, source hand-axis order,
information schema, and legal actions must match before timing is interpreted.

On balanced h7, also run one exact tolerance-zero rounded-cache step from the
same initial policy. Its regret table must match the dense first step within
`1e-10`, and its wall time divided by the leaf-adjoint first-step wall time
must be at least `5x`. This is a mechanism control: it asks whether removing
public-node SVDs, rather than an unrelated workload change, caused the gain.

## Zero-reach identity is an accumulator gate

On balanced h4, force the root's first action probability to zero for every
root hand and inspect a later traverser below that branch. At least one fully
unreachable information set must exist. For every such action row:

- leaf-adjoint and dense regret deltas must agree within `1e-10`; and
- the leaf-adjoint regret-delta magnitude must be exactly zero.

This is an action-level identity gate, not a conditional-value norm. It closes
the division-convention gap highlighted in ADR-0081 without reintroducing the
raw best-action comparison rejected by ADR-0084.

## Wide dense-free workload

Construct balanced and blocker-heavy h32 factor beliefs directly on external
hand axes. Build a representative one-deal public topology only for the 385
public nodes; no policy, regret, reach, or payoff object may have a `32^6`
deal axis. Terminal values come from the exact int32 structured-showdown
automata accepted by ADR-0072.

For each range family:

1. compile the CPU SciPy CSR maps and upload both directions once to the GPU;
2. from the cold uniform policy, compare one complete traverser-0 CPU
   leaf-adjoint read with the GPU read;
3. run two complete alternating GPU DCFR iterations across all six
   traversers; and
4. serialize the full current and average policy after each iteration,
   together with SHA-256 digests, policy statistics, and mean total variation
   from the initial uniform policy.

The expected schema is 6,144 information sets and 12,288 hand-action entries
per complete step. Every saved policy and regret table must be finite; each
policy row must be nonnegative and sum to one within `1e-12`.

The blocker-heavy h32 family is the untouched validation family. No
blocker-heavy h32 leaf-adjoint CPU time, GPU time, accuracy, batch count,
memory peak, or full-step result was observed before this freeze.

## GPU execution and honest charging

The optional CuPy backend keeps both compiled CSR operators resident. Each
feature batch is still copied host-to-device and each result copied back. GPU
kernel timing is diagnostic only; marginal reader wall time includes both
transfers and synchronization.

The speed gate is stricter still: it compares CPU marginal time with GPU
marginal time plus the one-time CSR upload bill. Require charged speedup of at
least `3x` on the sealed blocker-heavy family and on both h32 families. Also
require every complete six-traverser step to finish within 60 seconds.

The pinned optional environment is:

- NumPy 2.5.2;
- SciPy 1.18.0;
- CuPy CUDA 13x 14.2.0;
- CUDA runtime 13.2 (`13020`);
- driver API at least 13.0 (`13000`); and
- compute capability 12.0 on the RTX 5080.

These packages remain outside the core project dependency list. Their exact
screen requirements are frozen in
`experiments/requirements/leaf-adjoint-gpu-screen-v1.txt`. On Windows, the
optional packaged CUDA DLL directory must be explicitly supplied through
`PONTIUS_CUDA_DLL_DIRECTORY`.

## Correctness and resource gates

Across both h32 CPU/GPU crosschecks, require maximum errors of:

- root-normalized reach: `1e-10`;
- action numerator: `1e-9`;
- regret delta: `1e-9`;
- positive-reach conditional action value: `1e-8`; and
- child-action counterfactual reach disagreement: `1e-9`.

The wider tolerances relative to the small exact bridge acknowledge changed
GPU reduction order; they do not authorize a semantic mismatch.

Require conservative peak numeric storage of at most 3.0 GB on the host and
4.0 GB in the CuPy memory pool. Host peak includes the contraction estimate,
persistent CFR accumulators, and all terminal automata, even though this
slightly double-counts the active automaton library. Python-object and JSON
serialization overhead remains separately disclosed rather than hidden in a
numeric-array estimate.

Finally require the current policy after iteration one and the average policy
after iteration two to each move at least `1e-8` mean TV from uniform in both
families. This is not a quality threshold. It only rejects a solver that
serializes normalized but inert checkpoints.

## Pre-freeze engineering disclosure

All of the following was observed before this preregistration and is therefore
development evidence, not held-out confirmation:

- the generic rounded public-cache step reproduced h7 regret tables within
  about `5e-15` but took roughly 9.4-11.4 seconds; its cache construction was
  the dominant cost;
- the unrounded public cache eliminated SVDs but grew to rank 1,414 and about
  2.1 GB at h7, taking roughly 16.2 seconds;
- literal leaf-adjoint h7 took about 770 ms with regret error `6.4e-16`; its
  terminal contractions cost about 723 ms and reverse public propagation only
  about 14 ms;
- heterogeneous batching reduced the h7 leaf path to about 635 ms at cap 384;
  caps 96, 192, 384, and 768 were screened, with 384 fastest in that run;
- two warm-start h7 leaf-adjoint DCFR steps reproduced the dense regret,
  strategy-sum, current-policy, and average-policy trajectories with maximum
  error about `2.0e-15`;
- a forced balanced-h4 control produced 31 zero-reach information rows, with
  exact-zero leaf regrets and zero error against the dense action tables;
- one balanced h32 traverser-0 CPU leaf read took about 26.97 seconds; the
  CuPy path took about 5.78 seconds, a `4.664x` marginal and `4.600x`
  upload-charged gain;
- that balanced h32 CPU/GPU comparison had reach error `6.4e-16`, numerator
  error `4.0e-15`, regret error `1.6e-15`, and conditional error `1.4e-12`;
- an isolated h32 CSR chain improved `13.7-14.7x` in kernel time and
  `5.8-6.9x` after feature/result transfers;
- the balanced h32 cap screen measured approximately 5.74, 5.97, 6.63, and
  20.22 seconds at caps 384, 768, 1,536, and 3,072, with CuPy pool totals of
  about 0.97, 2.98, 9.83, and 20.80 GB; and
- the first balanced h32 CPU read used about 2.07 GB estimated host numeric
  storage; the GPU path reduced that estimate to about 1.49 GB because its
  batched sparse intermediates live on device.

Local hardware discovery reported an RTX 5080 with 16 GB VRAM, driver 610.88,
driver API 13.3, and compute capability 12.0. Small h7 GPU execution was exact
but slower than CPU at about 3.0 seconds because transfers dominated tiny
batches. GPU use is therefore gated at h32 rather than declared universally.

Before freeze, the additive CPU suite passed ten tests, the optional GPU suite
passed two tests, and the repository regression passed 436 tests with two
optional skips. The strict audit-config parser adds two tests and nine
mutation subtests. A final full regression is required before the sealed run.

## Interpretation branches

- Any small-axis trajectory or zero-reach failure rejects the leaf-adjoint
  algebra before h32 timing matters.
- A rounded-cache speedup below `5x` rejects the claimed SVD-elimination
  mechanism on its own control.
- Any h32 CPU/GPU identity failure rejects CuPy for solver updates, regardless
  of speed.
- A charged validation speedup below `3x` rejects the current transfer-heavy
  GPU wrapper as the wide checkpoint engine. It does not invite cap tuning on
  the revealed family.
- A latency or memory failure rejects the current batching/runtime form.
- A complete pass accepts an exact dense-free offline h32 checkpoint
  generator. It does not accept a production poker bot or an online resolver.
- After a complete pass, the next strategy-facing experiment is to use genuine
  h32 checkpoints as warm starts and candidate policies in the guarded
  acceptance experiment, replacing extrapolated crown ranks with measured
  ones.

## Dissent protocol

**Confidence:** very high in the leaf-adjoint algebra after dense two-step
identity; high that GPU reduction remains inside the frozen tolerances;
moderate that the balanced `4.6x` gain transfers to blocker-heavy axes; low
that the generic Python/CuPy implementation is remotely close to online
latency.

**Opposing evidence:** a complete h32 step repeats the roughly 5.8-second
target read six times; host/device transfers are still charged on every
batch; and no measured policy from this path has yet improved an acceptance
metric.

**Largest risk:** mistaking the first dense-free policy artifact for strategy
quality. Two cold iterations demonstrate plumbing and movement only. In a
six-player non-zero-sum game, lower local regret is not by itself a safety or
exploitability certificate against a field.

**Cheapest falsification:** the sealed blocker-heavy traverser-0 crosscheck.
An identity violation, charged speed below `3x`, or resource overflow rejects
the current GPU path before its two full iterations can be celebrated. If it
passes, the next cheapest falsification is whether the saved h32 policy can
warm-start search and improve a guarded decision under a fixed compute bill.
