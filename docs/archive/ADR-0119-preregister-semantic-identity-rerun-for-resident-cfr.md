# ADR-0119: Preregister semantic-identity rerun for resident CFR

## Status

Frozen after ADR-0118 and before the single successor rerun.

## Context

ADR-0117 failed only because a newly derived transferred GPU trajectory did not
reproduce the stored ADR-0113 checkpoint bytes.  Its maximum regret and
strategy-sum differences were `7.772e-16` and `2.220e-16`.  Every resident-versus-
transferred numerical gate and every per-target economics gate passed.

A checkpoint digest answers whether two serialized objects are identical.  It
does not answer whether two independently accumulated Float64 GPU trajectories
implement the same recurrence.  Treating it as the latter made the v1 contract
stricter than its semantic question.

## Decision

Run one additive v2 audit.  V2 invokes the immutable v1 workload and v1
implementation again.  It retains all four targets, both engine orders, the h7
negative control, all resource ceilings, and the original per-target speed
thresholds.  It does not replay or reinterpret only the favorable v1 timings.

The one correction is cross-run identity:

- transferred versus stored-teacher regret and strategy sums must be within
  `1e-12`;
- resident versus transferred accumulators and policies retain the tighter v1
  gates;
- all state and policy digests remain reported;
- digest identity remains mandatory for a stored object and exact restart from
  that object, but not for separately accumulated GPU executions.

The v1 artifact, configuration, implementation, and ADR-0118 record are pinned
by SHA-256.  V2 also requires that v1 formally failed and that its only failed
named gate was the cross-run state digest.

## Consequences

A v2 pass authorizes the resident solver as the wide one/two-step warm-search
engine within this laboratory scope.  It does not authorize an h7/h32 selector:
h7 remains a negative control and the dispatch boundary is not measured.  A v2
failure ends this line without another correction.

No new strategy-quality labels are produced.  The only question is whether the
3x systems result repeats under a semantically appropriate, preregistered
identity contract.
