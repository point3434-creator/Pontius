# ADR-0183: Preregister the read-only deep-horizon descriptor correction

- Status: accepted correction preregistration
- Date: 2026-08-21
- Depends on: ADR-0178, ADR-0181, ADR-0182
- Config: `experiments/configs/h32-deep-horizon-correction-v1.json`

## Question

Can the rejected ADR-0182 artifact be repaired as a closed metadata replay, or
did the failed target-identity gate conceal a changed workload that requires a
new GPU execution?

## Frozen correction

Read the rejected v1 result, its immutable config and implementation, and the
authoritative ADR-0178 parent. Perform no solver step, policy construction,
certificate, or strategy-quality evaluation.

Require all of the following:

1. the source artifact SHA-256 is
   `692c76d863a94c7a399ba21da18d1551f94c0d6e43519999059879accec2fe4f`;
2. after excluding the summary `passed` field, `target_identity` is the only
   false source gate;
3. every other v1 outcome-neutral gate is true;
4. both actual target belief hashes equal the v1 config and ADR-0178;
5. hashing each stored target descriptor reproduces the actual descriptor hash;
6. each actual descriptor hash equals ADR-0178 for the same target;
7. each v1 expected descriptor equals exactly the corresponding incorrect hash
   recorded by ADR-0182;
8. there are exactly two corrections and no unresolved target;
9. the aggregate survives a canonical JSON round trip identically; and
10. the strategy-population claim remains null.

If and only if all gates pass, replay `target_identity` as corrected and accept
the copied aggregate as metadata-corrected evidence. The original v1 artifact
remains rejected and immutable.

## Outcome-neutral boundary

The replay may not change, recompute, select, filter, or omit a target, block,
direction, scale, certificate, timing, memory observation, aggregate value, or
interpretation threshold. Any additional false gate, belief mismatch,
descriptor mismatch, provenance mismatch, or aggregate change rejects the
correction and requires a new prospective GPU run.

## Decision

Commit this replay, config, mutation controls, ADR-0182, and generated status
before executing it. A passing replay authorizes one result ADR interpreting
the unchanged aggregate under ADR-0181's frozen material-lift rule. It does not
authorize deployment or a population claim.
