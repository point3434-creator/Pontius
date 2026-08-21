# ADR-0201: Preregister the memory-schema-corrected selector replay

- Status: accepted correction preregistration before corrected replay
- Date: 2026-08-21
- Corrects: ADR-0199 after ADR-0200
- Config: `experiments/configs/h32-retained-affine-selector-cascade-replay-v2.json`
- Config SHA-256: `f911602f5f1cb03e3a4b83271a032bfbf68158d3731a08cf41b52b1960d00b83`
- Runner: `src/pontius/h32_retained_affine_selector_cascade_replay_v2.py`
- Runner SHA-256: `36addb294ca4ecf748b2033cb2c836422d60570b3a532c40289a5b479ee21369`
- Control test: `tests/test_h32_retained_affine_selector_cascade_replay_v2.py`
- Control-test SHA-256: `bf0f7be44eba92ab22b1542d2102925f38cbdd3013f1c2a00933c2c2a1f798c2`

## Correction

ADR-0200 identified one final-aggregation schema mismatch. The imported frozen
memory helper returns `gpu_free_bytes`; ADR-0199's result assembler asks for
`gpu_physical_free_bytes`.

Add one in-memory view around that exact helper:

```text
gpu_physical_free_bytes := gpu_free_bytes
```

The wrapper accepts only the exact two-field source schema
`{gpu_pool_total_bytes, gpu_free_bytes}` and returns those fields unchanged plus
the alias. It rejects a missing, expanded, or already transformed schema. The
v1 implementation remains byte-identical.

The correction pins:

- ADR-0199's config at
  `9f700db8c7ddedf9e3d0e91f982634b41d65483719735b7d6be202294ffec841`;
- its runner at
  `04062b4355d773ee7046995b05f03c927c8ecdae8edf5576819e642f8e948d0e`;
- its control test at
  `31a6d43bb936583d47d54eec3fb5f1758151af5738f890eeb9018ffedf774b29`;
- ADR-0199 at
  `49c06091754f71a9af0aeb036c2a2f99dbcc9d6e2d6162a90d4a3fe2ff2995d7`;
  and
- ADR-0200 at
  `0bc2ab141236de9bc868294f2f2deed7c0a3bfdf01f374e14827d3755c2488b6`.

## Scientific identity

Reuse ADR-0199 without modification for all six retained contexts, 36 blocks,
three direction families, 108 candidate feature rows, 648 responding-seat
rows, frozen features, exact Tier-A identity, five-seat Tier-B charge,
candidate strata, semantic label barrier, capacity arithmetic, K ladders,
random/clairvoyant brackets, cascade scoring, predictions, numerical ceilings,
time/memory gates, and blueprint-only emission.

Discard the failed process state. Reconstruct every context and feature from
the immutable sources, then perform one semantic retained-label join as if v1
had not run. Do not reuse a timing, coefficient, capacity, score, or Python
object from the rejected invocation.

The wrapper changes no feature or label field, target, candidate, cost, tie
break, threshold, result branch, or validity gate. It rewrites only result
provenance and records the additive alias after the unchanged v1 function
returns.

## Evidence boundary and decision

Run once from the clean successor commit. If every inherited ADR-0199 validity
gate passes, accept the retained-context selector and cost diagnosis. If any
gate fails, reject v2; do not perform another unrecorded correction.

The result remains exposed development evidence. It cannot support a strategy-
quality, fresh-transfer, deployment, composition, or population claim, and it
does not authorize the later resident-fold implementation without its own
preregistration.
