# ADR-0251: Preregister numerically identified convex-retreat quality gate

- Status: accepted corrected preregistration before any retreat certificate or fallback label join
- Date: 2026-08-22
- Follows: ADR-0249 and ADR-0250
- Config: `experiments/configs/h32-one-seat-retreat-quality-v2.json`
- Config SHA-256: `56fdaad44905ce31990d7ada92571cf412f9b85db37e9a4e43cb7c5eb7b2c8b1`
- Runner SHA-256: `ca207d64a3cb70d1767ffd2ade4649fb45c682ab9fc92227d013e38f60906979`
- Runner control SHA-256: `dc182d6a071c05e9acd854f90ee43ebcca877c31d5ce953285661cad94a6bc1c`
- Rejected-v1 config SHA-256: `c544bee4687e68a9059c0d6f7a92e5d6b1585a3cd122af4898767d8c9d9a3ca7`
- Rejected-v1 runner SHA-256: `2dfda449fcf8061dd57c26a85b4c113995440118c82ecd2025997e30dccb9e81`

## Correction scope

ADR-0250 rejects only ADR-0249's bytewise policy-reconstruction gate. It opened
no retreat or fallback label. This successor inherits the rejected config by
its complete SHA-256 and changes only candidate identity semantics plus the
controls needed to audit that correction. All target, optimizer, certificate,
tolerance, label-barrier, comparison, ledger, promotion, emission, and claims
rules remain those frozen by ADR-0249.

The rejected v1 implementation and control remain byte-identical and pinned.
The v2 runner calls their already-tested construction and certificate core with
a corrected barrier; it does not rewrite historical evidence code.

## Prospective candidate identity

Freeze the candidate prospectively as the output of this exact algorithm and
input set, not as a promise to reproduce prior Float64 bytes:

1. identical source artifact, posterior target, acting seat, warm-step rule,
   path-single-visit topology, behavioral axis, and six source gain rows;
2. identical first sparse master and all-six exact separation oracle;
3. exact response-signature multi-cut for seats 4 and 5 only;
4. identical second sparse master; and
5. factor-`0.5` behavioral retreat from the immutable blueprint to that
   second-master endpoint.

Before opening the retreat label, require every non-policy branch identity
provided to the barrier: immutable blueprint and parent identities, target and
source NashConv identity, exact cut players and response signatures, exact row
counts, and both master lower bounds within `1e-12`. Any different cut,
response tape, row library, bound, topology, or source aborts at the same
pre-label boundary.

Record equality with the ADR-0247 first-candidate, endpoint, and retreat policy
digests, but never use those three Booleans in a gate or branch. They are
diagnostics of reassociation only. This is ADR-0179's numerical-identity default
applied after the explicit deterministic-digest hypothesis failed.

## Numerical and discrete reproduction

The completed artifact must retain every ADR-0249 row, projection, profile-
equivalence, sparse-master primal/dual, warm-start, topology, memory, timing,
payoff-span, and provenance gate. In addition, compare the reconstructed first
oracle with the sealed ADR-0247 witness:

- NashConv `0.03699431926539898` within `1e-10`;
- maximum cap violation `8.300123213047898e-5` within `1e-10`;
- maximum epigraph violation `7.270318760673571e-4` within `1e-10`;
- all six response signatures exactly; and
- violating players exactly `(4, 5)`.

The first oracle must still reject the candidate under both separately passed
allowances: `2e-11` for caps and `1e-9` for epigraph separation. Policy digests
cannot rescue a failed numerical or discrete gate, and digest disagreement
cannot reject an otherwise passing numerical reconstruction.

## Retained quality method

Run exactly two all-seat exact oracles total: first-master separation, then the
independent factor-`0.5` retreat certificate. The second-master endpoint gets no
new oracle or quality label. Keep the fallback artifact opaque until the
retreat certificate completes; its numeric value, NashConv, and charged time
remain absent from both v1 and v2 configs.

Require the retreat to be exactly cap-feasible under `2e-11`, positive beyond
the `1e-10` quality allowance, below its Jensen ceiling, and inside the frozen
interior-slack floor. Charge the measured full schedule and the unchanged
`13,967.6157 ms` conservative schedule. A later fresh-target replication is
authorized only if the retreat beats the sealed one-step/31-block fallback by
more than one raw guard and also beats its value rate while using the retreat's
conservative denominator.

The run stays shadow-only and externally emits the immutable blueprint.

## Rejection rule

Abort before the retreat label if any algorithmic branch identity fails.
Reject the completed artifact if any numerical, certificate, ledger, barrier,
comparator, immutable-emission, or process gate fails. Do not adopt a digest
from either diagnostic attempt, relax a tolerance, alter the factor, select a
different target, or add another oracle after inspection.

## Claims boundary

A pass can establish only one-known-target exact safe value and authorize a
separate fresh-target preregistration. It makes no fresh-transfer, population,
multi-seat, composition, cross-street, deployment, or broad poker-strength
claim.

## Decision

Commit ADR-0250, this corrected runner and control, compact inherited config,
this ADR, roadmap, and generated status from one clean tree. Run the v2 artifact
once with CUDA variables cleared so ADR-0248 remains the only DLL bootstrap.
