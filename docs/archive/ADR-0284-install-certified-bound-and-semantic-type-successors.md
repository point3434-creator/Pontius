# ADR-0284: Install certified-bound and semantic-type successors

- Status: accepted corrective engineering controls; historical result labels are preserved but numerical-bound claims are qualified
- Date: 2026-08-22
- Follows: ADR-0283
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0284
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Preregister a replacement v2 h32 seed only after its complete GPU primitive, deadline-owned finalization bound, and frozen manifests pass review
- Front-Door-Blockers: h32 cache seeding and replay are unauthorized pending a clean v2 preregistration

## Question

How should the independent review's remaining semantic-category defects be
retired without rewriting hash-pinned runners, configs, artifacts, or the
research record they produced?

ADR-0285 supersedes the implementation inventory below where the final repair
added full affine provenance, a seventh tolerance type, finite/reach guards and
a transitive v2 device path. The historical bound qualification is unchanged.

## Restricted-master bound direction

The historical behavioral master labels its feasible Float64 primal objective
as `lower_bound`. For a minimization LP, a feasible primal objective is an
upper bound, not a lower bound. Small primal and projection residuals do not
reverse that mathematical direction. The historical sequence-form generator
similarly negates the in-house maximizer's primal objective.

The retained closure census contains 104 unique master solves and 41 top-level
target rows. Eighteen target rows record `incumbent_upper_bound - lower_bound`
below zero; the worst reversal is `-6.676663499849411e-09`. Those reversals are
inside the historical `1e-8` numerical allowance, so this inventory alone does
not establish a changed acceptance label. It does establish that the old field
was not a certified mathematical lower bound. The sealed JSON lacks the full
dual vectors and LP matrices needed for post-hoc recertification.

`linear_program_certificate` now treats solver multipliers only as hints. For
a bounded minimization it clips inequality multipliers to the valid sign,
forms the stationarity residual, minimizes that residual over independently
proved variable bounds, and performs every product and accumulation with
outward Float64 rounding. Its sequence-form sign adapter certifies the
negation of a bounded maximization using realization upper bounds of one and
the explicit epigraph caps. Exact-rational mutation tests confirm that the
reported Float64 value never exceeds the exact Lagrangian bound in the tested
random controls.

`behavioral_one_seat_master_v2` preserves the historical LP and candidate but
reports `lower_bound` only from that certificate plus the independent analytic
zero floor. Raw primal, raw dual, their signed difference, residual correction,
rounding width and downshift, and sign clips remain separate diagnostics. A
finite perturbed dual can make the raw dual exceed the primal while the v2
certificate still stays below the known optimum. The historical behavioral
and sequence masters remain byte-identical; a successor must consume the v2
master or the certified sequence adapter before making an `L`, `U-L`, or
global-closure claim.

## Public-node row semantics

The historical public-node helper accepted any public node while its
target-omitted adjoint omits every upstream factor of the acting seat. At a
nonroot repeated-actor node, the coefficient therefore lacks upstream own
realization reach. The raw traverser result also carried the acting role but
not the payoff role, allowing coefficients for one payoff seat to be paired
accidentally with another seat's source scalar.

The maintained helper now fails closed unless `public_node == 0`, where the
missing upstream factor is exactly one. It accepts only a factory-built source
context binding the live layout, complete source tape, full numeric-layout
digest and a typed result that durably identifies both acting and payoff roles.
It independently checks every coefficient against the dense root oracle.
Nonroot, stale, crossed-role, relabelled and raw-untyped adversaries all reject
before row assembly. The sealed ADR-0277 runner is retained byte-for-byte and
its old config now fails provenance rather than being refreshed or rerun.

## Semantic tolerances

Historical successors reused equal numerical values for two pairs of different
meanings: a relative bound reversal versus an absolute `U-L` closure gap, and
a selector margin versus an affine intercept identity. The device path also
carried generically typed epigraph-separation and already-resident primal
residual allowances; those values were distinct (`1e-9` and `1e-8`) but their
APIs did not prevent cross-wiring. `convex_retreat_tolerances` provides six
nominally distinct semantics plus a separate absolute-reversal allowance: seven
types in an exact seven-field config parser, with gate APIs that
reject cross-use even where values coincide. Frozen-equivalent values reproduce
the old outcomes, but numerical coincidence no longer aliases semantics and
the distinct GPU residuals cannot trade places. Historical v1 runners are
unchanged; every successor preregistration must expose and consume all seven
fields explicitly.

## Parked device-fold v2

The parked non-consuming GPU fold formerly accepted both host and device hand
index arrays, checked only the device shape/cast, and launched a raw-pointer
kernel without proving equality or bounds. Its v2 interface now accepts only
the contiguous Int32 host topology mapping, validates the target seat and each
index against the target hand axis, constructs the device copy internally,
rejects nonfinite accumulators, separates absolute and relative negative-reach
allowances without a unit floor, and bounds numerator mass using the actual
payoff span. Tolerated negative reach discards numerator and reach together.
The additive contraction, resident CFR, cross-payoff and selector-affine v2
paths now route through this fold and pass a reduced live-CUDA differential.
Production v1 customers remain unchanged; migration requires a separately
named successor.

## Decision

Adopt these four controls for successor work. Do not refresh any sealed v1
hash, reinterpret a historical primal objective as certified, generalize the
root-only row to nonroot play, collapse distinct tolerance fields because
their current values happen to match, or let a device caller supply topology
indices already owned by the host layout.

Historical artifacts remain evidence of their literal executions. Their
systems timing, exact-oracle values, and candidate policies are not erased,
but every lower-bound, `U-L`, and global-closure statement remains qualified
until a prospective v2 replay emits enough data to verify the new certificate.

## Claims boundary

These are CPU, fake-solver, exact-rational, and optional-GPU controls. They do
not recertify a sealed h32 artifact, change an old strategy label, establish a
nonroot affine formula, migrate a production fold, or authorize any seed,
replay, candidate, certificate, action-width, deployment, or poker-strength
claim.
