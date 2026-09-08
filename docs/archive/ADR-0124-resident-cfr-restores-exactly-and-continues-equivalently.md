# ADR-0124: Resident CFR restores exactly and continues equivalently

## Status

ADR-0123 executed and every frozen successor gate passed.

## Result

The artifact is `h32-resident-cfr-restart-semantics-audit-v1.json`, SHA-256
`162bf3e185afab0a41524746099cfd35196ff54e1d31dc346dd7fec2c9072409`.
It completed in `178.243 s`, executing 16 resident training steps and four exact
six-seat quality profiles.

Both pristine solvers restored from the canonical JSON iteration-four object
and immediately re-exported with exact identity:

- state digest identity: 2 of 2;
- current-policy digest identity: 2 of 2;
- average-policy digest identity: 2 of 2.

The serializer and restore operation therefore preserve the literal checkpoint
object.  The failure in ADR-0121 occurs only after new GPU arithmetic.

Independent future executions were not bit-identical.  Uninterrupted versus
restored-A measured:

- regret error `1.193e-15`;
- strategy-sum error `1.776e-15`;
- current-policy error `1.832e-15`, mean TV `3.366e-18`;
- average-policy error `5.551e-16`, mean TV `2.668e-18`.

Restored-A versus restored-B, starting from the same serialized object, also
diverged in bits:

- regret error `8.188e-16`;
- strategy-sum error `2.220e-15`;
- current-policy error `1.252e-15`, mean TV `2.988e-18`;
- average-policy error `6.661e-16`, mean TV `2.859e-18`.

This independently confirms that the source is future parallel floating
execution, not loss in checkpoint serialization or contamination from the
uninterrupted prefix.

## Strategic consequence

Exact resident evaluation found no material quality difference between the
uninterrupted and restored-A policies.

For current-8, maximum utility, best-response, and deviation-gain errors were
`2.609e-15`, `2.998e-15`, and `4.996e-16`; NashConv differed by `7.078e-16`.
For average-8 the corresponding errors were `9.714e-16`, `1.166e-15`,
`1.110e-15`, and `9.853e-16`.  All zero-sum residuals were below `5.3e-15`.

The differing policy digests therefore represent Float64 path variation with no
measurable strategic consequence at this horizon, not a near-tie amplification
into a different quality vector.

## Decision

Define resident checkpoint semantics as:

1. canonical checkpoint serialization and immediate restoration are bit-exact;
2. subsequent GPU continuations are required to satisfy numerical accumulator,
   policy, and strategic-quality gates, not byte identity;
3. digests identify stored objects and exact restoration, never independently
   accumulated future GPU trajectories.

Under that contract, authorize resident CFR through the demonstrated
iteration-eight warm-search horizon.  The next experiment moves to correctness-
scale action widening: two bet sizes, no raises, equal stacks, and no all-ins.
The transferred solver remains the long-horizon teacher until a separately
frozen source-training audit establishes resident behavior beyond eight steps.

A deterministic native reduction remains optional engineering, not a blocker,
unless byte-reproducible future trajectories become a product requirement.

## Scope

The semantic correction is established on one balanced/local target.  It does
not prove 64-step convergence identity, erase ADR-0121's formal failure, or
authorize side pots, raises, earlier streets, full hand axes, or neural leaves.
