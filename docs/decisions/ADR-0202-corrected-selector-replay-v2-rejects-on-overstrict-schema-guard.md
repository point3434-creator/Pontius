# ADR-0202: Corrected selector replay v2 rejects on its overstrict schema guard

- Status: rejected corrected replay
- Date: 2026-08-21
- Implements: ADR-0201
- Clean preregistration commit: `f881e79`
- Intended result: `experiments/results/h32-retained-affine-selector-cascade-replay-v2.json`
- Result artifact: absent

## Failure

The one authorized ADR-0201 invocation printed the first target progress line,
then the corrected wrapper raised:

```text
ValueError: corrected selector replay received the wrong memory schema
```

The guard ran at the target's first memory snapshot, before the warm step,
feature extraction, capacity derivation, semantic label load, scoring, gates,
or result serialization. No v2 result file exists.

## Cause

ADR-0201 correctly identified the needed alias but incorrectly froze the source
snapshot as a two-field object. The pinned helper actually returns four fields:

```text
gpu_free_bytes
gpu_total_bytes
gpu_pool_used_bytes
gpu_pool_total_bytes
```

The guard therefore rejected two legitimate untouched telemetry fields,
`gpu_total_bytes` and `gpu_pool_used_bytes`. The v1 failure remains exactly as
ADR-0200 diagnosed: its final reader asks for a fifth spelling,
`gpu_physical_free_bytes`, that is absent from this four-field snapshot.

## Evidence boundary

Reject v2. It failed before any strategy or selector work and reveals no metric.
Do not weaken the schema guard to accept arbitrary mappings.

A successor may replace only the mistaken two-field set with the exact pinned
four-field set and add:

```text
gpu_physical_free_bytes := gpu_free_bytes
```

It must preserve all four original fields and values, reject any other key set,
leave v1 and v2 byte-identical, and rerun the complete ADR-0199 workload from
scratch.

## Decision

Record the rejected corrected invocation. If a four-field literal successor is
preregistered, treat it as the final schema correction: any further mismatch
ends this replay line for a direct runner review rather than another wrapper.
