# ADR-0123: Preregister resident CFR restart semantics

## Status

Frozen after ADR-0122 and before any repeated-restore continuation or exact
quality label.

## Context

ADR-0121 passed every sustained teacher and economics gate but formally failed
its demand that an independently executed GPU continuation end with identical
bits.  The iteration-eight differences were approximately `1e-15` in
accumulators and `1e-18` mean policy TV.  That result does not distinguish three
claims that its restart gate combined:

1. whether serialization restores the exact iteration-four object;
2. whether repeated parallel GPU continuations are numerically equivalent;
3. whether their exact strategic-quality vectors remain equivalent.

The first should be bit-identical.  The second cannot honestly demand a
summation order the CuPy sparse interface does not declare.  The third is the
product-relevant consequence.

## Decision

Run one contained successor on the frozen balanced/local target.  Create an
uninterrupted resident trajectory, serialize its iteration-four checkpoint
through canonical JSON, and restore that same object into two pristine resident
solvers.

Immediately re-export both restored solvers.  State, current-policy, and
average-policy digests must match the serialized checkpoint exactly.  Then
continue the uninterrupted arm and both restored arms to iteration eight.

Compare uninterrupted versus restored-A and restored-A versus restored-B at the
pre-existing numerical ceilings:

- accumulator error at most `1e-10`;
- policy probability error at most `1e-9`;
- mean information-set TV at most `1e-10`.

Finally, evaluate exact six-seat current-8 and average-8 quality for the
uninterrupted and restored-A policies.  Utilities, best responses, deviation
gains, and NashConv must agree within `1e-10`; zero-sum residual stays below
`1e-9`.

The parent failure, its exact failed-gate set, all implementation sources, and
the original teacher are SHA-pinned.  No candidate selection or improvement
claim is made.  This is the only correction authorized for ADR-0121.

## Interpretation

A pass defines the checkpoint contract precisely: exact stored-state recovery
and numerically/strategically equivalent continuation, without promising
bitwise deterministic CUDA reductions.  It authorizes resident iteration-eight
training as the bridge needed for the first wider-action blueprint.

A failure of immediate identity is a serializer defect.  A numerical
continuation failure blocks resident long trajectories.  A quality failure shows
that tiny accumulator noise reaches strategically discontinuous decisions and
also blocks progression.  No second semantic correction follows any of those
outcomes.

## Scope

One target and four continuation steps cannot prove 64-step determinism.  A pass
is sufficient only to begin correctness-scale action widening while retaining
the transferred solver as the long-horizon teacher.
