# ADR-0285: Close second- and third-round review defects

- Status: accepted corrective engineering validation; no research invocation or h32 result authorized
- Date: 2026-08-23
- Follows: ADR-0284
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0285
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Measure a scalable independent v2 row oracle and complete finalization bound before reviewing any replacement h32 seed preregistration
- Front-Door-Blockers: no h32-scale v2 cache population or replay measurement, no externally sealed seed manifest, and no integrated full-hand street controller

## Question

Which second- and third-round review defects remain after ADR-0283 and ADR-0284,
and what successor-only controls close them without changing sealed historical
code or opening a new research label?

## Decision

Adopt the following additive controls. They supersede the implementation
descriptions in ADR-0283 and ADR-0284 where those descriptions were narrower
than the final reviewed interfaces.

### Immutable evidence and cache authority

`runner_harness_v2` reads a bounded regular file once, computes the digest from
that exact byte snapshot, rejects invalid UTF-8, duplicate JSON keys and
nonfinite JSON constants, requires a caller-supplied complete schema validator,
and deep-freezes nested mappings and sequences. A pass bit alone is not an
artifact-completeness schema.

`pre_bet_initial_row_cache_v2` no longer accepts a caller identity, row bundle,
source scalar, source tape, or acting best-response scalar at its write or
consume boundaries. Factory-only live contexts derive the complete numeric
layout, game, belief, action schema, policy tapes, source payoffs and acting
best response. Population accepts only provenance-bound affine contexts and
generates each row internally after checking every coefficient against the
independent dense root oracle. The writer returns an explicitly unsealed record
that lookup cannot consume. Replay authority exists only after a separately
persisted seal manifest is loaded under an already expected seal SHA-256. All
reads are size-bounded before allocation and publication is exclusive and
no-clobber.

The scalable h32 form of the independent coefficient oracle has not been
established. This fail-closed CPU implementation is therefore a semantic
control, not an h32 seed primitive or timing result.

### Affine provenance and role identity

`CrossPayoffAdjointResult` and `PublicNodeAffineSourceContext` are factory-only
successor types. Their context identity covers the complete numeric layout,
action schema, game digests, probability tape and both acting and payoff roles.
The root affine builder snapshots and validates the complete source tape,
rederives the typed-result identity, independently evaluates the source payoff,
and compares the entire coefficient row with the dense root oracle. Stale
off-node tapes, crossed roles, caller-relabelled wrappers and coefficient
mutations that preserve only the source intercept all fail before a row is
returned. Nonroot extraction remains deliberately unavailable.

### Deadline-owned publication and the street wall

`deadline_owned_result` uses a durable three-state consumer protocol: canonical
data, a completion seal, and an exclusive publishing lock. Data construction,
serialization, bounded staging, no-clobber publication, readback and hashing
are one admitted unit. Seal construction and verification are a second admitted
unit while the lock keeps the pair unconsumable. Removing the lock is the
publication event; the helper then rechecks data, seal and campaign wall. A
failure preserves an unsealed or lock-marked diagnostic rather than deleting a
possibly raced path, and the loader accepts only data plus a matching seal with
no lock. It also validates the embedded admission arithmetic and rechecks the
lock after reading. Live publication rejects symlink or reparse-point ancestors.

`street_deadline` makes ADR-0282 executable: one monotonic 15-second ledger,
including the one-second emission reserve, survives every action on a street
and resets only on the exact next street transition. This is an isolated
control; no full-hand loop yet consumes it.

### Optimization and device-fold semantics

The behavioral one-seat master successor validates all input rows and solver
outputs as finite and separates dimensionless probability feasibility from
chip-valued epigraph, inequality, complementarity and objective tolerances.
Probability gates never scale by a payoff cap. The certified lower-bound path
from ADR-0284 remains the only successor authority for `L`.

The retreat schema contains seven, not six, independent nominal types: relative
reversal, absolute reversal, absolute `U-L` gap, selector margin, affine
intercept identity, epigraph separation and resident primal residual. The
absolute reversal field removes the hidden unit floor from the relative test.

The device-fold successor validates finite Float64 records before raw-kernel
use, derives its hand mapping only from validated host topology, separates
absolute and relative negative-reach allowances without a unit floor, derives
the numerator guard from the layout payoff span, and discards numerator and
reach together when a tolerated negative reach is clamped. The v2 contraction,
resident CFR evaluator, cross-payoff wrapper and selector-stable affine path all
route transitively through that fold. Selector margin and intercept identity
are distinct required nominal types.

## Validation

- Adversarial CPU tests cover duplicate/nonfinite evidence, stale and relabelled
  affine contexts, false source scalars, coefficient-preserving-intercept
  mutations, self-authored cache hashes, oversize reads, no-clobber races,
  nonfinite solver vectors, probability/chip unit separation, near-zero
  reversal scaling, negative-reach numerator mass, deadline overruns, crashes,
  unlock mutation and forged admission arithmetic.
- A reduced live-CUDA differential passes through the v2 contraction and one
  complete resident CFR step. Reaches agree with the host oracle within
  `2e-13`; numerators and regret/state tables agree within `2e-12`.
- The complete suite passes: 1,035 tests ran with two expected revoked-runner
  skips and no failures. Generated-status freshness and maintained
  documentation-link checks pass in that run.

These checks are targeted regression evidence, not certification of arbitrary
layouts, filesystems, GPU executions or h32 scalability.

## Consequences

ADR-0283's statement that a failing publisher removes its canonical path is
superseded. Preserving a lock-marked diagnostic is safer under races; consumers
must use the loader and must never infer trust from data-path existence.

ADR-0284's six-tolerance count and parked leaf-only device-fold description are
superseded by the seven-field schema and the tested transitive v2 path. This
does not migrate or reinterpret any hash-pinned v1 runner.

The next permissible work is a preregistered scalability diagnostic for the
independent row oracle and finalization envelope. A replacement h32 seed may be
reviewed only after that diagnostic supplies a complete import/config manifest,
an external seal plan and measured worst-case bounds. ADR-0281 remains revoked.

## Claims boundary

No h32 cache was populated or replayed. No revoked experiment ran. No master,
candidate endpoint, certificate, strategy label or poker-strength result was
opened. The work closes implementation defects and narrows future authority; it
does not establish action-width capacity, complete-street latency, a full-hand
loop, or deployment readiness.
