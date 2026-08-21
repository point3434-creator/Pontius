# ADR-0200: Selector replay v1 rejects on its final memory-schema key

- Status: rejected result
- Date: 2026-08-21
- Implements: ADR-0199
- Clean preregistration commit: `972fb56`
- Intended result: `experiments/results/h32-retained-affine-selector-cascade-replay-v1.json`
- Result artifact: absent

## Failure

The one authorized ADR-0199 invocation reconstructed all six targets and
printed one progress line for each feature-extraction phase. It then raised:

```text
KeyError: 'gpu_physical_free_bytes'
```

The exception occurred in the final aggregate memory read after the feature
loop, semantic retained-label join, and in-memory scoring, but before gates,
stdout metrics, or result serialization. No result file exists and no selector
score, feature coefficient, K, timing aggregate, or value metric was printed or
persisted.

## Cause

ADR-0199 imports `_memory_snapshot` unchanged from
`h32_fresh_union_value_audit.py`. That frozen helper returns:

```text
gpu_pool_total_bytes
gpu_free_bytes
```

The new runner correctly read `gpu_pool_total_bytes` but incorrectly requested
`gpu_physical_free_bytes` for the second field. Every retained h32 consumer of
this helper uses `gpu_free_bytes`; the failure is a result-assembly schema bug,
not a missing measurement.

## Evidence boundary

Reject v1. The completed in-memory work is not evidence because the artifact
and validity gates were never produced. Do not infer any selector outcome from
the six progress lines or from knowledge that execution reached the final
aggregation.

The only admissible successor is a hash-bound additive alias for the exact
snapshot schema:

```text
gpu_physical_free_bytes := gpu_free_bytes
```

It may not change a target, candidate, feature, label, K rule, timing charge,
threshold, control, scoring function, or outcome gate. The original v1 runner
must remain byte-identical for provenance.

## Decision

Record the failed invocation with no result. Preregister a thin corrected
wrapper before rerunning. If the wrapper cannot preserve the complete ADR-0199
protocol and only add the in-memory alias, stop rather than recover partial
state or copy unseen values from process memory.
