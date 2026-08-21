# ADR-0179: Numerical identity is the default GPU evidence gate

- Status: accepted process decision
- Date: 2026-08-21
- Depends on: ADR-0118, ADR-0120, ADR-0122, ADR-0123, ADR-0147, ADR-0170

## Context

Three GPU-adjacent experiment lines paid the same avoidable correction cycle.
An initial preregistration treated a freshly recomputed Float64 policy or state
digest as semantic identity; the run failed despite errors near machine
precision; a successor retained the failure and replaced the cross-run digest
gate with frozen numerical tolerances.

Digests correctly answer whether bytes are identical. GPU sparse reductions do
not promise the same reduction order across independent executions, so byte
identity is stronger than strategic or numerical identity unless deterministic
execution is itself the feature under test.

## Decision

Make numerical identity the repository default for independently re-derived
Float64 GPU artifacts. Add executable default ceilings:

- accumulator maximum absolute error: `1e-12`;
- policy maximum probability error: `1e-12`;
- policy mean information-set total variation: `1e-13`; and
- exact-quality-vector maximum absolute error: `1e-10`.

Experiments may preregister stricter values. They may not add or loosen a
tolerance after reveal. Digests must still be recorded as diagnostics.

Bitwise identity remains a valid gate only for:

1. immutable input, configuration, source, and provenance identity;
2. a literal serialized object's identity;
3. immediate restore and re-export of that object; or
4. an explicit experiment whose subject is deterministic future execution.

Exact schemas, discrete action identities, topology, dimensions, and
combinatorial work counts remain exact. This ADR changes the default evidence
contract, not the numerical implementation or any historical verdict.

## Implementation

`src/pontius/evidence_protocol.py` owns the default constants, validates the
four numerical error classes, and rejects undeclared digest-gate purposes.
`PROJECT.md` states the same rule in the canonical evidence and dissent
protocol. Unit tests pin both the constants and the fail-closed digest-purpose
allowlist.

Future GPU preregistrations should import the constants when using the defaults
or explicitly state why another frozen tolerance is required.

## Consequences

ADR-0118, ADR-0122, ADR-0147, and ADR-0170 remain formal failures. Their
corrected successors remain the accepted evidence. This rule prevents the same
known reduction-order property from being rediscovered as an experimental
failure while preserving bitwise tests where byte identity is genuinely the
contract.
