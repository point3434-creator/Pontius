# ADR-0083: Preregister sparse-incidence open-mode backend audit

**Status:** Accepted after generic CSR development on balanced 32-hand axes,
but before any blocker-heavy 32-hand speed result

**Date:** 2026-08-20

## Decision

Run one additive audit of the fixed sparse-linear operators identified by
ADR-0082. The frozen configuration is
`experiments/configs/sparse-incidence-open-mode-audit-v1.json`; its SHA-256 is
`0ccdfd5de188cf02d9f2a491b418aa05aafaedf936223f73730244c479e8ed1d`.
The result target is
`experiments/results/sparse-incidence-open-mode-audit-v1.json`.

The audit compares the immutable NumPy incidence teacher with an optional
SciPy CSR backend on the same direct structured-showdown automata. It is an
engineering successor, not a new value representation. It changes the
execution of the two incidence maps only:

- source subset accumulation becomes `A @ features`; and
- signed compatible-query reconstruction becomes `Q @ incidence`.

Belief construction, direct int32 automaton transitions, rank slicing,
per-hand folding, normalization, action comparison, and zero-sum accounting
remain shared with ADR-0081. SciPy is a pinned optional dependency; importing
the core package does not require it.

## Workload and held-out boundary

Use the canonical six-seat one-bet river geometry, three mixture components,
3/3 card split, and identical balanced/blocker-heavy range families at 7, 16,
and 32 hands per seat. Each row evaluates six all-check showdown automata in
two directional batches, seats 0-2 and seats 3-5.

The balanced 32-hand row is development evidence. It was used to choose CSR
and the fixed maximum batch feature width of 96. The blocker-heavy 32-hand row
is the untouched validation speed family. Small-axis rows test scaling and
identity; they are not substitutes for the held-out h32 result.

Timing uses one warmup followed by three paired repetitions. Order alternates
CSR-first, NumPy-first, CSR-first. Report every sample and compare medians.
Compilation and lazy SciPy import are excluded from marginal latency but added
to a separate charged first-use bill. Both h32 rows must remain faster under
that charged bill.

## Exact sparse maps

For each direction, compile two Float64 CSR matrices from the already frozen
card topology:

1. `A` has one source-record column and one incidence-ID row. Every source
   record contributes `+1` to all 64 used-card subsets. Its nonzero count must
   equal `source_records * source_subset_count` exactly.
2. `Q` has one query-record row and one incidence-ID column. Each valid entry
   carries the frozen inclusion-exclusion sign. Duplicate coordinates, if any,
   are summed and indices sorted by the library constructor.

The operator is compiled once per belief topology and reused for all terminal
automata and both identity and weighted-reach reads. Numeric bytes include CSR
data, indices, and indptr arrays in both directions.

Sparse matrix multiplication may sum terms in a different order from the
NumPy teacher. Exact intermediate-bit identity is therefore not claimed. The
customer-facing hand vectors, decisions, and game invariant are the gates.

## Correctness and semantic gates

Across all six rows, require:

- maximum root-normalized reach, numerator, and conditional-value error at
  most `1e-10`;
- the same three errors at most `1e-10` after deterministic, nontrivial unary
  factors are applied to every seat's hands;
- zero selected-action mismatches against a fixed losing shortcut;
- maximum NumPy-or-CSR six-seat zero-sum residual at most `1e-9`;
- finite CSR reaches, numerators, and conditional values; and
- exact source-matrix nonzero counts.

The weighted arm is necessary because the all-identity denominator may reuse
precompiled incidence arrays. It forces the new operator to construct both
denominator and numerator paths under policy-like unary hand factors.

## Economic gates

Require all of the following:

- at least `5.0x` marginal speedup on the untouched blocker-heavy h32 row;
- at least `5.0x` marginal speedup on every h32 row;
- at most 4,000 ms median CSR latency for six h32 terminal values;
- at most 600 MB estimated peak numeric storage at h32;
- at most 100 MB of compiled sparse-operator numeric storage at h32; and
- a charged first use—lazy import plus operator compile plus marginal
  evaluation—faster than the NumPy marginal on both h32 rows.

These are screen gates, not online production targets. A multi-second pass
still does not authorize multiplying the reader naively across all public
nodes or calling the Python backend sub-millisecond.

## Pre-freeze engineering disclosure

The following was observed before this freeze and is not held-out evidence:

- profiling the canonical balanced h32 NumPy read attributed about 7.16 s to
  subset accumulation, 2.02 s to signed queries, and only 0.09 s to direct
  automaton replay;
- replacing repeated NumPy scatter/gather work with CSR reduced one isolated
  rank-104 block from about 3.26 s to 0.30 s;
- the complete balanced h32 six-value workload improved from about 15.29 s to
  1.84 s (`8.31x`), with final conditional error about `3.6e-15`;
- the balanced h32 sparse operators occupied about 69.0 MB;
- fixed caps 96, 192, 384, 768, and 1024 produced similar 1.80-1.86 s
  medians, while cap 96 reduced estimated peak storage to about 422 MB and was
  therefore selected without a speed claim; and
- a balanced h7 smoke test improved about `4.93x`, had zero action
  mismatches, and agreed within approximately `1e-15`.

A NumPy sorted-segment alternative improved only `1.31x` and changed an
intermediate by `6.1e-10`; it was rejected before freeze. No blocker-heavy h32
CSR time, speedup, peak, operator size, or final error was observed.

The pinned optional environment is NumPy 2.5.2 and SciPy 1.18.0. This keeps
historical source and environment contracts intact while making the screened
library versions reproducible.

## Interpretation branches

- Any hand-vector, action, or zero-sum failure rejects the CSR backend even if
  timing passes.
- A validation speedup below `5x` rejects generic CSR as the wide engine and
  sends the fixed maps to a custom segmented/SIMD kernel; it does not invite
  retuning on the revealed family.
- A memory failure rejects the generic sparse format or current batching,
  regardless of latency.
- A complete pass accepts CSR as a substantially better exact-teacher kernel,
  not as the eventual online evaluator.
- After a complete pass, implement one full dense-free quotient-CFR step and
  match its h4/h7 regret and average-policy trajectory to the existing solver
  before generating genuine h32 checkpoints.

The full-step audit, rather than another isolated contraction benchmark, is
the next strategy-facing unknown. It must expose policy-conditioned cache
construction, every action read, regret update, averaging, and complete
iteration wall time.

## Dissent protocol

**Confidence:** very high in the fixed sparse-map algebra; high that the
balanced speed mechanism transfers; moderate in the held-out h32 factor
because middle rank and record sparsity differ by range family; low that a
generic CPU sparse library is the final quality-per-millisecond kernel.

**Opposing evidence:** h7 gains were below the `5x` wide gate, sparse matrices
add roughly 69 MB at balanced h32, and a full CFR iteration may be dominated by
public-policy composition rather than terminal incidence.

**Largest risk:** converting a useful offline-teacher acceleration into a
premature production architecture. Even a clean pass remains approximately
three orders of magnitude away from a one-millisecond decision budget.

**Cheapest falsification:** the sealed blocker-heavy h32 median. A result below
`5x`, above 4 seconds, above 600 MB, or slower on charged first use rejects the
screen at its intended boundary without further implementation.
