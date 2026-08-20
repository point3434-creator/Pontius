# ADR-0084: Sparse incidence transfers, but raw action gate rejects exact ties

**Status:** Frozen audit rejected as specified; value/economic mechanism retained
for a tie-aware successor

**Date:** 2026-08-20

## Result

The frozen ADR-0083 audit completed from commit `59c10b3` in 135.192 seconds.
The canonical result is
`experiments/results/sparse-incidence-open-mode-audit-v1.json`. Its SHA-256 is
`7b37b3c299ccb02279819aba5410a0afe0dc9a10dd0aca1e8719169ae7624ff8`,
and its size is 27,661 bytes.

The held-out speed mechanism transferred. The audit nevertheless fails one of
its frozen gates: 13 raw `argmax` action identities differ. Record the overall
result as failed. Do not rewrite the gate or label the audit a pass because the
failure later proved strategically harmless.

## The performance hypothesis passes its held-out boundary

The untouched blocker-heavy h32 row improves from 10,492.56 ms to 1,216.31 ms,
an `8.627x` speedup. The balanced development row independently reproduces at
`8.469x`, from 15,705.22 ms to 1,854.52 ms.

| Hands | Family | NumPy median | CSR median | Speedup | Operator | Peak |
|---:|---|---:|---:|---:|---:|---:|
| 7 | balanced | 30.23 ms | 5.23 ms | 5.780x | 0.518 MB | 4.944 MB |
| 7 | blocker-heavy | 25.99 ms | 4.88 ms | 5.330x | 0.474 MB | 4.745 MB |
| 16 | balanced | 1,041.02 ms | 128.88 ms | 8.077x | 7.362 MB | 59.324 MB |
| 16 | blocker-heavy | 801.42 ms | 92.30 ms | 8.683x | 6.295 MB | 47.620 MB |
| 32 | balanced | 15,705.22 ms | 1,854.52 ms | 8.469x | 69.036 MB | 421.862 MB |
| 32 | blocker-heavy | 10,492.56 ms | 1,216.31 ms | 8.627x | 61.006 MB | 339.898 MB |

The result is stable across all three paired repetitions. Including lazy
SciPy import and operator compilation, first-use h32 bills are 1,925.06 ms and
1,280.02 ms, still far below their NumPy marginals. All latency, memory,
operator-size, source-nonzero, and finite-output gates pass.

CSR therefore removes most of the avoidable Python incidence tax. It does not
make the reader online: six h32 terminal values still cost 1.2-1.9 seconds.

## Value identities are substantially inside tolerance

Across all rows, the worst errors are:

- root-normalized reach: `5.55e-17`;
- root-normalized numerator: `2.22e-16`;
- conditional value: `5.33e-15`;
- weighted reach: `8.67e-19`;
- weighted numerator: `3.47e-18`;
- weighted conditional value: `3.55e-15`; and
- six-seat zero-sum residual: `1.77e-13`.

Every one is far inside its frozen gate. Sparse multiplication's changed
summation order is not producing material value error.

## Why the action gate fails

The action control compares all-check showdown with a constant losing shortcut
of `-2 * reach`, with showdown placed first. Thirteen private hands have exactly
zero probability of winning at showdown. Their two actions are therefore
mathematically equal and the declared stable tie policy should choose the first
action.

The NumPy teacher instead places showdown below the shortcut by one or a few
Float64 ulps:

- raw normalized action differences range from `-6.94e-18` to `-5.55e-17`;
- its conditional values are `-2.0000000000000004` or
  `-2.0000000000000009`; and
- CSR returns an exact zero action difference and conditional value `-2.0` for
  all 13 rows.

The mismatch counts by geometry are 0, 1, 2, 7, 1, and 2 in frozen row order.
A post-freeze combinatorial diagnostic independently searched for a compatible
joint assignment in which each disputed target hand ties or beats every
opponent. None exists in any of the 13 cases. This is an exact support/strength
statement, not an inference from the two floating implementations. A separate
winner-only nonnegative contraction is zero up to inclusion-exclusion noise of
at most `8.63e-21` on the same rows.

Thus the sparse result has the correct tie direction and the supposed NumPy
action oracle does not. The frozen gate still fails: it asked for literal
identity to that oracle, not strategic-equivalence or independently certified
tie semantics.

## Decision

1. Reject ADR-0083 as an all-gates-pass audit.
2. Accept the fixed CSR maps as a validated value-evaluation acceleration,
   conditional on never feeding raw floating `argmax` into certification or a
   best response.
3. Retain the optional pinned SciPy backend as the exact offline teacher and
   full-step development engine; it is not the final native runtime.
4. Replace raw action identity with an explicit guarded action primitive:
   robustly separated actions must match; overlapping error intervals must
   abstain or apply a declared deterministic tie policy while charging the
   possible value loss.
5. Test that primitive on exact ties and perturbations on both sides before
   using sparse outputs in best-response or acceptance logic.
6. Once that semantic defect is closed, proceed to one dense-free quotient-CFR
   step. CFR regret updates consume action numerators directly and do not need
   an unguarded `argmax`, so no full timing rerun is needed to preserve the
   measured kernel result.

## What this changes

Action identity cannot be a raw equality gate when the oracle and candidate
both use reordered floating reductions. The correct object is an interval
decision:

- certify action `a` only when its lower bound exceeds every competing upper
  bound;
- declare an unresolved tie otherwise; and
- attach at most the interval overlap as decision-value loss if a deterministic
  fallback is required.

For a known exact tie, the canonical first-legal action is harmless and
reproducible. For an unknown near-tie, silently choosing either action is not a
certificate; the reader must abstain or spend more precision/computation.

This is directly relevant to the eventual bot. Neural values will create many
more uncertain near-ties than Float64 contraction. Discovering the comparator
failure here, where exact support proves the truth, is preferable to burying it
inside a learned leaf evaluator.

## Limitations

- The exact tie diagnostic was performed after the frozen audit and is an
  explanation, not a retroactive gate.
- CSR memory accounting covers numeric arrays, not allocator or Python-object
  overhead.
- The speed customer remains six terminal values, not a policy-conditioned
  public-tree iteration.
- No policy improved in this audit.

## Dissent protocol

**Confidence:** very high that all 13 mismatches are exact ties; very high in
the value and speed measurements; high that interval action semantics fixes
this failure class; low that generic CSR approaches final online latency.

**Opposing evidence:** a future non-tied near-boundary action could still flip,
and the current constant `1e-10` identity envelope is an audit tolerance rather
than a production error model.

**Largest risk:** dismissing every small action disagreement as a tie. The
successor must distinguish independently known ties from unresolved intervals
and may not infer equivalence from a small observed delta alone.

**Cheapest falsification:** exact-tie, positive-gap, negative-gap, and
inside-envelope controls through one shared action selector. Any certified
wrong sign or uncharged inside-envelope choice rejects the selector before the
full CFR step.
