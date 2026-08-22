# ADR-0250: Reject bytewise retreat reconstruction before labels

- Status: rejected preregistered execution before any new strategy-quality label
- Date: 2026-08-22
- Implements: ADR-0249
- Clean preregistration commit: `b1a951280cae56519aa5505b9eb347227e9b88d1`
- Result artifact: none; the label barrier aborted before serialization

## Result

Reject the first ADR-0249 invocation as designed. The runner completed the
already-known source reconstruction, first restricted master, first exact
separation oracle, two exact cut rows, second master, and deterministic retreat
construction. Its label barrier then stopped before the retreat oracle and
before deserializing the sealed fallback artifact because the reconstructed
policy byte digests did not equal the ADR-0247 digests.

No new retreat NashConv, deviation-gain vector, strategy-quality value, or
fallback label was opened. No result artifact was written and no candidate was
emitted. The failed invocation therefore cannot adjudicate retreat quality.

## Diagnostic localization

A read-only diagnostic invocation replaced the barrier action only with a
printer followed by an unconditional stop at the same pre-label boundary. It
repeated no new strategy evaluation and intentionally could not reach the
retreat oracle or comparator load.

The identity split was exact:

| Pre-label witness | Reproduced |
|---|---:|
| immutable blueprint policy digest | yes |
| source NashConv within `1e-10` | yes |
| first restricted-master bound within `1e-12` | yes |
| exact violating players `(4, 5)` | yes |
| both exact response signatures | yes |
| row counts `[1, 1, 1, 1, 2, 2]` | yes |
| second-master bound within `1e-12` | yes |
| first-candidate policy byte digest | no |
| endpoint policy byte digest | no |
| factor-`0.5` retreat policy byte digest | no |

The source/cut/master branch is unchanged. The failure is localized to literal
Float64 policy bytes derived through GPU-reassociated coefficients. That is the
change class for which ADR-0179 makes numerical identity the default. ADR-0249
explicitly elevated digests because it attempted to test deterministic future
reconstruction; this invocation falsifies that attempted determinism cleanly.

## Decision

Preserve the ADR-0249 config, implementation, control, and clean commit without
modification. They are the frozen rejected v1 method.

Authorize a corrected clean preregistration that freezes the candidate
prospectively by algorithm, inputs, topology, exact response signatures, cut
set, row counts, and numerical optimizer witnesses. The old and reconstructed
policy digests must remain recorded as diagnostics but may not gate semantic
identity. Before the retreat label, require both LP bounds within `1e-12`,
source NashConv within `1e-10`, and every non-policy branch identity supplied
to the barrier. The completed artifact must still require the full row,
projection, profile-equivalence, and sparse-master numerical gates. After the
retreat certificate, additionally compare the first-oracle objective and
violation magnitudes with ADR-0247 under the frozen `1e-10` quality ceiling.

Retain every other ADR-0249 rule unchanged: two all-seat oracles total, distinct
`2e-11` cap and `1e-9` epigraph allowances, opaque fallback bytes until after
the retreat certificate, the full `13,967.6157 ms` conservative charge, strict
material-value and value-rate promotion gates, shadow-only evaluation, and
immutable-blueprint external emission.

## Claims boundary

This result identifies a failed bitwise reconstruction gate only. It says
nothing about retreat safety, quality, transfer, value rate, or deployment.
