# ADR-0118: Resident CFR wins mechanically but byte identity fails

## Status

ADR-0117 executed.  The frozen audit failed one gate and therefore is not
relabeled as a pass.

## Result

The artifact is
`h32-resident-cfr-audit-v1.json`, SHA-256
`e4b55f1e1ead00dcb29963c9aa513e3fb730927aff394bd2ea7bfa7d0ded867a`.
It completed in `295.168 s`.  Twenty-one of twenty-two named gates passed.

The sole failure was exact state-digest identity between the newly rerun
transferred trajectory and the stored ADR-0113 teacher: zero of eight checkpoint
digests were byte-identical.  This is a formal protocol failure.  It is not
silently weakened after the result.

The associated numerical errors localize the failure.  Maximum transferred
teacher regret error was `7.772e-16`; maximum strategy-sum error was `2.220e-16`.
Resident versus transferred maximum regret and strategy-sum errors were
`6.384e-16` and `2.220e-16`.  Maximum policy-probability error was `5.551e-16`
and maximum mean information-set TV was `1.890e-18`.  Four of eight resident
average-policy digests matched, while no nontrivial current-policy digest did.
The mismatches are therefore Float64 accumulation-order differences in a
re-derived GPU trajectory, not evidence of a different update rule.

The h7 control repeated the disclosed boundary: `455.292 ms` transferred versus
`473.215 ms` resident, or `0.962x` marginal and `0.908x` cache-charged.  Its
regret error was `2.220e-16` and its strategy sums were identical.

## Economics

All frozen economics gates passed on every h32 target:

- pooled two-step marginal speedup: `3.341x`;
- pooled two-step cache-charged speedup: `2.783x`;
- weakest target one-step cache-charged speedup: `2.340x`;
- weakest target two-step cache-charged speedup: `2.767x`;
- target marginal two-step speedups: `3.319x` to `3.384x`;
- static cache compilation: `2.842 s` to `3.482 s` per target;
- maximum observed GPU pool: `7.408 GB`.

The resident steps reduced the transferred-equivalent marginal traffic from
`351.705 GB` to `3.476 GB`, a `101.19x` reduction (`99.012%`).  Terminal
contraction remained `99.37%` of resident step time, so the result does not move
the bottleneck elsewhere; it makes the same dominant operation cheaper.

## Interpretation

The mechanistic hypothesis survived every numerical and economic test, but the
artifact as a whole failed its frozen contract.  ADR-0117 therefore does not by
itself promote the implementation.

The failed contract also taught a real reproducibility boundary.  A SHA-256
digest remains correct for the identity of a serialized checkpoint object and
for exact restart from that object.  It is too strict as a cross-run semantic
identity test for a floating GPU trajectory recreated in a different execution
context.  Cross-run validation needs pinned accumulator and policy tolerances;
stored-object and restart validation should retain digests.

## Decision

Preserve the v1 artifact and its failed status.  Authorize one additive
successor rerun with the workload and all speed thresholds unchanged.  The only
semantic correction is to replace cross-run byte identity with the already
standard `1e-12` accumulator ceiling while continuing to report every digest.
No result from v1 is relabeled, no strategy-quality label is added, and no
selector is authorized from the h7/h32 boundary.

## Limitations

The result remains one board, one public tree, two generated families, four
target beliefs, and two warm DCFR steps.  It establishes neither long-run
training speedup nor wider NLHE transfer.  The 4.23 GB balanced-family resident
cache also shows that this exact implementation spends substantial GPU memory
to buy latency; memory and concurrency remain deployment constraints.
