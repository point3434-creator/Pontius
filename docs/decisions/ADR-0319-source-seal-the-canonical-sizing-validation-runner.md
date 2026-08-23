# ADR-0319: Source-seal the canonical sizing validation runner

- Status: accepted source-only failure-complete runner, schedule, and result schema before any canonical validation invocation
- Date: 2026-08-23
- Implements: ADR-0318
- Preregistration commit: `509df55`
- Runner canonical-LF SHA-256: `5116c1d4b2632da76cf83e6d7d015b190e061330094d27b3c9719631a89252e1`
- Seal canonical-LF SHA-256: `40c7828e8e3f18843a56ef9c6c89c25785a96b145d31c4a00d413cf0a93993db`
- Control canonical-LF SHA-256: `26398979afd26f8c015c73587a6c115c59b23a698bd9a525ba528efac1a685a1`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0319
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Invoke the source-sealed ADR-0319 entry point exactly once, retain all 177 ordered observations and the immutable campaign bytes despite individual rejection, apply only the frozen correctness gate, and record the result in a successor ADR; edit no runner, adapter, authority, corpus, schedule, option, allowance, runtime identity, legacy consumer, or v1-v4 owner before that invocation
- Front-Door-Blockers: no canonical ADR-0319 proposal, exact-micro result, adapter-specific sizing result, retained campaign, or correctness assessment exists; the adapter remains toy-only and no certified-v2 production consumer is authorized; v1-v4 and behavioral-master specialization remain parked

## Question

Can ADR-0318's canonical reduced-sizing adapter be evaluated over the exact
ADR-0312 inventory without post-outcome schema changes, truncation after a
failure, transformed representations, duplicate backend calls, or contact with
a legacy consumer or candidate owner?

This is a source-only checkpoint. No ADR-0312 base was submitted to HiGHS, no
sealed micro program was enumerated, and no canonical objective, policy,
certificate interval, or backend time was opened.

## Decision

Accept and source-seal `pontius.certified_sizing_validation_runner` before the
first canonical invocation. The runner binds ADR-0312's exact 177-base order
and selects only each base's canonical representation. It owns a fixed typed
observation for every scheduled base, canonical exact-float serialization, an
immutable campaign digest, and a correctness-only conjunctive assessment.

The schedule has SHA-256
`36f34eb820bfaa4b58747201c9b27779553d0f8e250c73786da34542b5d8cba4`.
Its protocol identity has SHA-256
`51d4f188fbf2e5b78b38fca7712294b2001d0d0959a00c575d17a0b0adc0a5df`.
The exact family and path counts are:

| Family or path | Bases |
|---|---:|
| Known ADR-0310 sizing regression | 1 |
| Exact micro LP | 48 |
| Fresh reduced-sizing LP | 128 |
| Generic exact-micro HiGHS-DS path | 48 |
| ADR-0318 certified-sizing adapter path | 129 |
| Total canonical bases and public proposals | 177 |

No row permutation, variable permutation, dyadic scaling, redundancy arm,
native backend, or HiGHS-IPM arm enters this successor campaign. Those broader
representation results remain ADR-0314 evidence; this campaign asks whether
the new canonical consumer boundary itself accepts the canonical distribution.

## Two independent authority paths

The micro and sizing bases cannot share one semantic adapter without inventing
an interface that ADR-0318 does not own.

For each of the 48 exact micro LPs, the runner invokes ADR-0313's public
HiGHS-DS adapter once on the canonical matrix, enumerates all exact rational
vertices independently, reconstructs the returned primal in canonical
coordinates, and derives an outward trusted-box upper certificate from the
returned multiplier hints. The backend objective and certificate must agree
with the exact optimum under the already sealed nominal allowances.

For each of the 129 sizing LPs, the runner invokes ADR-0318 exactly once from
the context's exact chip, probability, showdown, and bet-size fields. It then
bridges the raw primal and multipliers—not the adapter's acceptance label—into
ADR-0313's separately sealed canonical sizing verifier. That verifier
recompiles and byte-compares the base, exactly normalizes the policy, evaluates
the feasible fold/call behavioral lower bound, reconstructs the outward upper
bound in the trusted box, and applies its own existing nominal allowances.
The runner additionally requires exact agreement between the adapter and
independent reconstruction on compiled LP identity, bet sizes, raw primal and
multipliers, exact policy, response actions, clips, reported/canonical/
behavioral/certified values, signed gap, and certificate record.

The two code paths use the same public SciPy `linprog(method="highs-ds")`
runtime but do not call the historical native sizing consumer. The micro path
validates public HiGHS and the exact/certificate authority; only the 129 sizing
bases validate the ADR-0318 adapter interface.

## One-call and failure-completeness contract

Each task wraps the public function with a private per-observation counter.
Zero or multiple public calls reject that observation. Exact enumeration and
backend work are attempted independently for micro tasks, so an enumeration
failure cannot erase a backend record. Adapter exceptions, nonoptimal backend
returns, schema exceptions, semantic verifier failures, adapter-independent
mismatches, and unexpected task failures all produce immutable typed records.
The outer loop always advances to the next scheduled base.

The public development executor rejects a sealed ADR-0312 plan before solver
import or invocation. Only the source/runtime/schedule-preflighted sealed entry
point can set the campaign's sealed bit. The immutable campaign constructor and
the assessment independently require the committed runner hash, canonical
schedule, complete corpus, and frozen runtime identity, so a toy call cannot
manufacture sealed eligibility.

An observation passes only if it records exactly one public proposal, the
family-specific evidence is complete, both relevant semantic gates pass, and
no failure record exists. The campaign gate is conjunctive: all 177
observations, exactly 48 micro passes, and exactly 129 sizing passes are
required. Solver and verification wall times are retained diagnostics but are
not a latency or speed gate.

## Source, dependency, and runtime seal

Before plan construction or public solver import, the sealed entry point
verifies canonical-LF identities for the new runner and these unchanged direct
authorities:

- ADR-0318 adapter and seal;
- outward bounded-minimization certificate;
- ADR-0312 corpus and value-free structures;
- ADR-0313 audit runner and its invocation seal; and
- canonical unit-tagged sizing compiler.

It then runs ADR-0318's source/dependency and runtime verifiers, independently
checks ADR-0313's CPython 3.14.6, NumPy 2.5.2, SciPy 1.18.0, and embedded HiGHS
1.12.0 identity, reconstructs the sealed corpus, and compares the complete
schedule and protocol digests. Any mismatch stops before the first proposal.

The runner imports no native simplex, legacy sizing oracle, capacity-filling
owner, action abstraction, blueprint, resolver, or strategy consumer. It
returns immutable bytes and writes no artifact; the successor invocation owner
must persist the exact returned campaign before interpretation.

## Toy-only controls

Nine focused controls pass. They cover:

- exact 177-base order, family counts, canonical-only representations, and
  schedule identity;
- immutable source and protocol seals;
- an import-graph exclusion for native, legacy, and candidate consumers;
- source failure before plan construction or execution;
- rejection of a sealed plan through the toy executor before any backend call;
- a first-call backend exception followed by a successful second task, proving
  ordered continuation and one counted call per task;
- an unexpected post-call schema failure whose outer exception, chained cause,
  and true public-call count all survive the last-resort guard;
- an unsealed width-four sizing toy accepted by both ADR-0318 and ADR-0313's
  independent verifier; and
- an injected responder-action mutation detected by the adapter-independent
  comparison.

These controls use only hand-authored or deterministic unsealed toys. They do
not invoke any canonical validation task.

The repository-wide suite passes 1,264 tests in 331.577 seconds with two
intentional environment-dependent skips. Generated STATUS, maintained
Markdown links, source/schedule/protocol seals, and whitespace checks pass.
Ruff is unavailable in the pinned environment, so this checkpoint makes no
Ruff claim.

## Next boundary

Commit this source checkpoint, then invoke
`execute_sealed_adr0319_canonical_validation` exactly once with no source or
configuration edit. Persist its exact `canonical_bytes`, calculate its digest,
and apply `assess_adr0319_canonical_validation`. A failure remains a complete
scientific result and does not authorize tuning or a filtered rerun. A pass may
authorize only a separately preregistered certified-v2 sizing consumer; it
does not connect that consumer, revive v1-v4, or answer action-width quality.

## Claims boundary

This checkpoint establishes a source-sealed schedule, typed failure-complete
schema, two explicit authority paths, exact one-call instrumentation, and toy
behavior. It provides no evidence over the 177 canonical solver results,
arbitrary reduced games, transformed matrices, production ranges, future
SciPy versions, consumer fallback rates, persistent bases, action width,
ladder regret, population transfer, or complete-decision quality. It
establishes no latency, marginal chip quality per millisecond, 15-second fit,
blueprint, resolver, full-hand agent, AIVAT, league strength, coalition safety,
or poker strength. No revoked experiment or external publication is
authorized.
