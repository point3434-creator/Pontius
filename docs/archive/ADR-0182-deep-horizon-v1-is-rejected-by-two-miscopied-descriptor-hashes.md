# ADR-0182: Deep-horizon v1 is rejected by two miscopied descriptor hashes

- Status: rejected result
- Date: 2026-08-21
- Implements: ADR-0181
- Clean preregistration commit: `1c94e8d`
- Result: `experiments/results/h32-deep-horizon-opportunity-v1.json`
- Result SHA-256: `692c76d863a94c7a399ba21da18d1551f94c0d6e43519999059879accec2fe4f`

## Result

The one authorized invocation ran from the clean preregistration commit and
completed both 64-step trajectories plus 981 exact certificate queries in
`1691.32 s`. The top-level result is rejected because the frozen
`target_identity` gate failed. No strategy interpretation is accepted from this
artifact yet.

Every other outcome-neutral gate passed. In particular:

- both target belief hashes matched the frozen config and ADR-0178;
- both one-step policies structurally replayed all six ADR-0178 public-node
  blocks;
- 128 resident steps, six checkpoint rows, twelve blocks, and 84 directions
  completed;
- all 84 directions had a complete grid scale;
- every certificate remained independent of the immutable blueprint;
- maximum step time was `8.475 s` and maximum certificate time was `1.394 s`;
- peak GPU-pool total was `6,719,463,936` bytes and minimum physical free
  memory was `8,540,651,520` bytes; and
- the numerical warm-start errors were zero.

## Failure mechanism

ADR-0181's config contains two transcription errors in
`target_descriptor_sha256`:

| Target | Frozen incorrect hash | Reconstructed hash |
|---|---|---|
| panel 1 balanced | `6109b0afb8548629870f64853a960118a842b062b97809e908efbf3ca5f7d9d0d` | `6109b0afb8548629870f6484d5f1050468aad320c0e1c92e8506d841c9dc7f7b` |
| panel 3 blocker-heavy | `de67f2fbba92ea16ad5ede876b9c6451affb06f0b30c4f6baa7def53950f981c26` | `de67f2fbba92ea16ad5ede876b9c6451affb06d103e5f1f6e0b30c4df8b56eeb` |

The reconstructed hashes exactly equal the retained ADR-0178 descriptors for
the same target names and belief hashes. The target builder, target beliefs,
policies, blocks, searches, certificates, and aggregates were not affected.
This is a preregistration metadata error, not a different executed workload.

## Decision

Reject v1 as invoked; do not edit its config, weaken its failed gate, or cite
its strategy measurements as accepted evidence.

Preregister a read-only correction replay. It may accept the existing artifact
only if the failed gate set is exactly `target_identity`, every other frozen
gate is true, both actual descriptor hashes reproduce from the stored
descriptors and equal ADR-0178, both belief hashes equal v1 and ADR-0178, all
provenance hashes match, and no strategy value or aggregate is recomputed or
changed. Any additional mismatch requires a new prospective GPU run.
