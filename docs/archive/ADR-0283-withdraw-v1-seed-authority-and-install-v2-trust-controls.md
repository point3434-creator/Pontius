# ADR-0283: Withdraw v1 seed authority and install v2 trust controls

- Status: accepted corrective process and engineering control; no h32 invocation authorized
- Date: 2026-08-22
- Follows: ADR-0282
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0283
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Preregister a replacement v2 h32 seed only after its complete GPU primitive, deadline-owned finalization bound, and frozen manifests pass review
- Front-Door-Blockers: h32 cache seeding and replay are unauthorized pending a clean v2 preregistration

## Question

What must change after an independent review found that the accepted v1 cache
successor could assemble a finite but false acting-seat gain and that the
preregistered seed runner did not place result assembly and publication inside
an admitted finalization unit?

ADR-0285 supersedes the implementation description below with the final
factory-only cache context, separately trusted seal, and lock-marked completion
protocol. The revocation and claims correction in this decision are unchanged.

## Falsifier and claim correction

The v1 cache file binds the `2N - 1` affine payoff rows but not the acting
seat's invariant best-response scalar. Its successor accepts that scalar from
the caller after cache validation. A caller can therefore provide a different
finite value, retain an exact cache hit, and shift the acting gain row without
tripping any persisted-byte, source-intercept, or provenance check. The
nonfinite-input test in ADR-0280 did not cover this finite substitution.

ADR-0280's literal CPU/h2 row round trip and its measured endpoint identities
remain observations of the tested input. Its broader fail-closed gain-assembly
claim is withdrawn: v1 is historical protocol memory, not an authorized cache
interface for a successor or replay.

ADR-0281 also left the final gate assembly, input rehashing, canonical result
serialization, write, and readback after the last separately bounded seed
unit. The campaign could cross its wall in that tail and create a pass-looking
canonical result before the late deadline check rejected the invocation. The
large nominal slack is not a semantic substitute for an admitted bound.

## Corrective controls

`pre_bet_initial_row_cache_v2` stores the finite acting best-response value and
all rows under one persisted-file hash. Its final factory-only context derives
the identity, source tapes, source payoffs and acting best response from live
objects; population generates rows only from provenance-bound affine contexts.
The writer returns no replay authority. A v2 lookup exposes the rows and scalar
atomically only when a separately persisted seal is loaded under an already
expected seal hash. The successor has no caller-supplied identity, row bundle,
source scalar or acting scalar, explicitly rejects v1 bytes, and preserves the
defensive caller policy with no rows on every miss.

`deadline_owned_result` is the required publication primitive for a successor
runner. Its final protocol uses canonical data, a completion seal and an
exclusive publishing lock. Data and seal phases are separately admitted and
verified; consumers accept only a matching data/seal pair after the lock is
removed. Failures preserve an unsealed or lock-marked diagnostic. Canonical
path existence is never evidence of successful completion.

Revocation is also a generated-front-door invariant. Every latest ADR must
carry one complete snapshot naming the research, process, and runtime-contract
heads, the cumulative revoked set, active next step, and blockers. The
generator validates every historical snapshot, a contiguous ADR chain, and
filename/title number agreement; an omitted latest snapshot, forgotten
revocation, revoked head, or unavailable reference fails closed. Runtime
authority and revoked authorities render outside the bounded recent ledger, so
neither ADR-0282 nor this revocation can disappear merely by aging out.

The historical v1 module, runner, config, and ADR remain unchanged so their
record is reproducible. Preservation is not authorization.

## Decision

Revoke ADR-0281 before its first h32 invocation. Do not populate or replay its
v1 cache files, refresh its pinned hashes, or reinterpret its clean-tree
authority. Keep ADR-0280 as the latest completed research observation with the
claim qualification above; this decision is the current process controller.

Any replacement seed preregistration must use a complete arm-specific v2 GPU
row primitive, persist the acting scalar under the same trusted byte hash as
the row bundle, freeze a separately measured maximum finalization duration,
and publish only through the deadline-owned atomic helper. It must retain
temporal separation between population, external sealing, and replay. No h32
work is authorized merely because the CPU v2 and fake-clock controls pass.

## Claims boundary

This decision repairs two computational trust boundaries, hardens the durable
front-door authority, and withdraws one prospective execution authority. It is
not an h32 cache result, latency result, capacity
result, action-width result, strategy-quality result, or poker-strength result.
No cache has been populated and no candidate, certificate, label, or policy
has been opened.
