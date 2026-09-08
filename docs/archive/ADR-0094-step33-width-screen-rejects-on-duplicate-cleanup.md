# ADR-0094: Step-33 width screen rejects on duplicate cleanup

**Status:** Frozen ADR-0093 execution rejected after the balanced schedule;
no result artifact or width decision exists

**Date:** 2026-08-20

## Result

The frozen ADR-0093 run from clean commit `0455750` rejected with:

```text
UnboundLocalError: cannot access local variable 'warmup' where it is not associated with a value
```

No `leaf-adjoint-batch-width-audit-v1.json` result artifact was written. Do not
infer a selected width, speedup, numerical agreement, or gate result from this
execution.

## Localization

The runner summarized the warmup row, then deliberately released its large
private accumulator/policy tables:

```python
del warmup
```

After completing the six measured balanced rows, the family cleanup repeated
the same deletion:

```python
del warmup, reference, gpu, automata, workspace, sparse, topology, belief
```

Because `warmup` was already unbound, Python raised before garbage collection,
before blocker-heavy construction, before width summaries, before selection,
and before all frozen gates.

This is a control-flow/bookkeeping defect, not evidence for or against wider
batches. The mathematical primitives, source state, solver, and CuPy operator
were not modified.

## Evidence boundary

The execution reached the cleanup line after:

- validating and restoring the balanced iteration-32 source;
- running the balanced width-384 warmup; and
- executing the six balanced measured arms in the frozen mirrored order.

Those rows remained only in terminated process memory. Their timings, output
states, errors, phase traces, and memory peaks were never serialized or printed
and have not been observed. The aggregate exactness/economic gates were never
computed. Blocker-heavy did not start.

The failure therefore reveals only that the workload reached the end of one
family without an earlier exception. It does not authorize treating any
unseen row as passing.

## Why the full test suite missed it

The h4 development control exercised `_run_restored_step` and numerical
comparison directly. Parser and selector tests exercised their pure helpers.
All 458 tests passed, but none executed the expensive top-level two-family
orchestration through post-family cleanup.

The successor must make family scope independently testable so this class of
orchestration failure has a cheap complete-path control. A source-text assertion
is insufficient.

## Decision

1. Reject ADR-0093 v1 as executed.
2. Preserve its implementation and config hashes unchanged.
3. Create an additive successor; do not edit the frozen v1 file.
4. Keep the board, source states, widths, mirrored order, repetitions,
   selection rule, exactness gates, economic gates, and resource ceilings
   unchanged.
5. Make family execution a scoped helper that returns compact warmup/measured
   rows; let local objects expire naturally rather than naming already-deleted
   temporaries in outer cleanup.
6. Add a cheap mocked complete-family test that crosses warmup, every width,
   reference comparison, compact return, and cleanup.

## Successor evidence stage

The corrected successor is preregistered after the v1 balanced workload was
executed but before any balanced row value was observed, before any
blocker-heavy arm, and before any summary, selector, or gate result.

This is not as pristine as ADR-0093's original holdout because elapsed failure
position is known. It still seals every scientific output the screen was
designed to measure.

## Dissent protocol

**Confidence:** certain in the exception localization; very high that removing
the stale cleanup target is sufficient; no updated confidence in the economic
result.

**Opposing evidence:** reaching post-balanced cleanup implies no earlier hard
exception, but thresholds are applied only after both families. It cannot be
counted as a pass.

**Largest risk:** treating repeated reruns as harmless and gradually leaking
timing information. The v1 row values were not emitted; freeze one additive
correction and rerun once.

**Cheapest falsification:** the mocked complete-family control, followed by the
same frozen two-family workload.
