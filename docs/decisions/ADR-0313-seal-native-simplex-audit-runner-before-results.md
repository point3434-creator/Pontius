# ADR-0313: Seal the native-simplex audit runner before results

- Status: accepted source-only audit runner, typed observations, and invocation seal before any sealed exact optimum or backend result
- Date: 2026-08-23
- Follows: ADR-0312
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0313
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Invoke the complete sealed ADR-0311 audit exactly once through the source-sealed entry point, retain all 2,655 scheduled observations and every exact/reconstruction/certificate record despite individual failures, and apply the frozen conjunctive gate; do not edit the runner, native simplex, certificate, corpus, representation, backend option, allowance, environment identity, or gate; do not open any representative or v3/v4 candidate value or reopen v4
- Front-Door-Blockers: no sealed micro optimum, native/HiGHS observation, sizing value, certificate interval, backend timing, or gate result exists; the native simplex remains rejected for this workload; HiGHS dual simplex is not eligible for any consumer; v1-v4 and every action-abstraction integration path remain parked

## Decision

Accept and seal ADR-0311's owned audit runner and typed result schemas before
the first invocation on any of ADR-0312's 885 representations. The source now
owns exact rational micro enumeration, all three frozen backend adapters,
variant-to-original primal and dual reconstruction, unit-specific semantic
checks, exact behavioral sizing lower bounds, outward-rounded objective upper
bounds, exception-complete observations, the fixed 2,655-invocation schedule,
and the conjunctive interpretation gate.

This checkpoint imported the optional NumPy/SciPy environment to bind version
identities and exercised native mechanics only on hand-authored unsealed toys.
It did not enumerate a sealed micro vertex, invoke native or HiGHS on a sealed
base or variant, open a sealed objective or sizing value, construct a sealed
certificate interval, or inspect a fresh candidate. The ADR-0312 corpus and
all earlier source identities remain unchanged. Capacity-filling v4 remains
permanently parked.

## Source and dependency seal

The new `pontius.native_simplex_audit_runner` source SHA-256 is
`cfb127960e3d501a156f14d22244ecd122874b74fefb668685f9a721503ade16`.
The separate invocation seal is
`pontius.native_simplex_audit_seal`, SHA-256
`a0305de4af43366f6e2ed2a1d5bcd4fafba01f94d5e7103201bcaa9385ff05e3`.
The sealed entry point hashes its own source and refuses execution if that
digest or the committed runtime identity differs.

The load-bearing unchanged dependencies remain:

- native simplex:
  `6069dac31bb2915284319d0d5551d5773f4b4cac294d07c440f4b4d9ee4c83f8`;
- outward LP certificate:
  `0ca8b0443eb8a0279247fad659694d88b723b15bf0b2d3e5f7c7ef2c2ddfa910`;
- unit-tagged sizing compiler:
  `3a3ed588e90b84cdbc8186829fc7dac57d9ec40603f29dd5ddc70549748bd346`;
- audit structures:
  `ea945d3ce76b38c893029884bcbda2280fc22ce66fdac30fdb09508929d39801`;
- audit corpus:
  `b65c301b9f0443b9f25da4da22fa7f8c15017cd63b4abe2670c5d98c32085918`;
- complete value-free corpus identity:
  `4be6dcc311bc2f885ce9ad312cee8294f38231180ab78bbbfb6497184b1597a3`.

The runner imports no action candidate, v4 owner, replay, blueprint, convex
master, resolver, or strategy path. It never writes an evidence artifact; the
successor invocation owner must retain the returned immutable campaign before
interpreting it.

## Frozen runtime, options, and schedule

The source binds this exact diagnostic environment:

| Component | Identity |
|---|---|
| Python implementation | CPython |
| Python | 3.14.6 |
| NumPy | 2.5.2 |
| SciPy | 1.18.0 |
| embedded HiGHS | 1.12.0 |

The three arms remain in variant-major order for every representation:

1. native maximization, tolerance `1e-11`, maximum 4,096 pivots;
2. `highs-ds`, presolve enabled, primal and dual feasibility tolerances
   `1e-10`, maximum 4,096 iterations; and
3. `highs-ipm`, the same presolve/feasibility/iteration settings plus IPM
   optimality tolerance `1e-12`.

HiGHS receives only the negated objective, transformed `A_ub`/`b_ub`, and
implicit nonnegative bounds. The adapters add no equality, finite upper bound,
integrality, scaling, presolve hint, or unfrozen option. Five representations
for each of 177 bases give 885 ordered tasks and exactly 2,655 backend
invocations. The immutable protocol identity also carries every distinct
nominal allowance type; equal `1e-9` numbers cannot substitute for one another.

## Exact work and coordinate reconstruction

The micro enumerator treats every original inequality and every
nonnegativity boundary as a possible active boundary, enumerates every square
active set, solves nonsingular systems with `fractions.Fraction` Gaussian
elimination, retains exactly feasible vertices, deduplicates degeneracy, and
records the active-set, nonsingular-system, feasible-system, distinct-vertex,
and maximizer counts. It binds the exact optimum fraction and the
lexicographically smallest maximizing vertex. It performs no filtering on an
opened optimum.

For every backend return, the runner records transformed-representation row
residuals and independently maps the primal point to canonical variable
coordinates. Native nonnegative maximization duals and HiGHS nonpositive
minimization marginals are normalized explicitly. Every wrong-sign variant
row is recorded and clipped before positive dyadic scale factors and duplicate
rows are aggregated into an original-coordinate minimization hint. Thus a
row permutation, variable permutation, scaled row, duplicate row, or zero
redundancy row cannot silently change the certificate's game.

The outward certificate is evaluated against the original matrix and the
original trusted box. For micro LPs, its upper bound and every backend
objective are compared with the exact rational optimum. For sizing LPs, the
runner recompiles and byte-compares the semantic base, separates
dimensionless policy residuals from chip-valued envelope residuals, and maps
only policy values within the frozen allowance to zero or one. It then
renormalizes each opener row with exact `Fraction.from_float` arithmetic and
computes an independently feasible behavioral value against exact joint
weights and responder fold/call best actions. That value is the primal lower
bound. The negative outward lower bound for the negated LP, plus the separately
stored objective shift, is the sizing upper bound; upper minus behavioral
lower is the only optimality gap.

## Complete failure capture and interpretation

Every scheduled arm produces one immutable observation even when exact work,
an adapter, a backend status, coordinate mapping, semantic verification, or
certificate fails. Backend exceptions retain class, message, arguments, and
stable traceback-frame coordinates. The native adapter calls the public
frozen solver once and, on a verification exception, reads the failed call's
traceback locals instead of rerunning a private tableau. This preserves its
returned point, dual hint, pivots, row residuals, and verification allowance
when available. The canonical known-regression gate requires the disclosed
375 pivots, exact assertion, original row 215, maximum residual
`4.049601922810204`, and allowance `4.199999999999999e-8` under the frozen
native options.

Before policy-level interpretation, each parseable point and dual separately
retains transformed residuals, original-coordinate residuals, unit-specific
box violations, reconstructed objective, sign clips, and outward certificate
bounds. Thus a later semantic failure cannot erase the numerical return that
caused it. The complete immutable campaign exposes canonical JSON bytes with
every float encoded by `float.hex()` and a SHA-256 digest, so the successor can
persist exactly the object it interprets without inventing a post-outcome
schema.

The gate does not pool or average failures. Both HiGHS arms must return and
verify on all 885 representations; every micro result must match its exact
optimum; every sizing interval must meet its chip-width bound; all ten DS/IPM
intervals for a base must retain an allowed common intersection; and each
corresponding DS/IPM behavioral reconstruction must agree within its distinct
cross-backend allowance. A clean result can authorize only a later prospective
replacement-adapter ADR.

## Verification

Nine focused tests use one hand-authored degenerate micro LP and one separately
seeded, unsealed width-four sizing toy. They cover nonunique exact optima,
every metamorphic representation, both map directions, dyadic dual scaling,
duplicate aggregation, per-row sign clips, exact HiGHS call arguments, native
failure-local capture without a second solve, complete continuation after
backend/schema failures, exact behavioral normalization, outward intervals,
distinct nominal types, runtime identities, candidate-free imports, and the
unchanged native/certificate sources. The actual SciPy solver is not invoked;
its adapters are stopped at a fake `linprog` boundary.

The nine focused runner tests pass. The repository-wide suite passes 1,225
tests with two skips in 324.703 seconds. Generated-status, maintained-Markdown-
link, Ruff lint/format, and whitespace checks also pass. No sealed corpus,
backend invocation, optimum, or audit result is part of those tests.

## Next boundary

Invoke `execute_sealed_adr0311_audit` once on the exact ADR-0312 corpus. Do not
run a prefix, sample, development probe, or one backend alone. Retain all
2,655 observations even after the already-known native failure, then apply the
frozen conjunctive gate and record the complete pass or rejection in one
successor ADR. A rejected invocation must retain its full schedule and failure
records. No source or option repair is allowed inside that result boundary.

## Claims boundary

This checkpoint establishes only committed audit mechanics and toy-validated
schema behavior. It does not establish one sealed optimum, one new poker
value, native or HiGHS robustness, replacement eligibility, runtime fitness,
or decision quality. It does not revive v4 or authorize any solver migration.
It establishes no production range width, earlier-street quality, multiplayer
safety, replay, blueprint, convex-master, resolver, NashConv, AIVAT,
league-strength, 15-second feasibility, marginal decision quality per
millisecond, C5 completion, or complete-bot result. No revoked experiment,
external publication, or research-thesis change is authorized.
