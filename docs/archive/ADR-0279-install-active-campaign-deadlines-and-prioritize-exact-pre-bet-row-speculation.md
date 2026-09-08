# ADR-0279: Install active campaign deadlines and prioritize exact pre-bet row speculation

- Status: accepted label-free engineering result; deadline prerequisite closed and CPU/cache differential authorized
- Date: 2026-08-22
- Follows: ADR-0278
- Source result: `experiments/results/h32-pre-bet-action-width-capacity-v1.json`
- Source result SHA-256: `d9b0518d6df8c71afaea573cca8668217fec6ed6490544f74b155ab67956f9d7`
- Deadline primitive SHA-256: `ee0eaa861a4a15e3da53db343d90e1704050c0d927ba146b0b3cd9dda4f87871`
- Deadline control SHA-256: `1d20b0e83f51952d97f58c412c6f5a556d9cf17c81618874297d1e87227e1576`
- Timing analyzer SHA-256: `3f95cad0bd2f7d5b9ba1e0c69c00fd545853bd10e8e7f6704ef700f164252460`
- Timing control SHA-256: `fd4c321125972df43d2e80efe1513f7d4ce42dfd580c72a8294f2c4978f06ea4`

## Question

What shared mechanism prevents another bounded campaign from running past its
frozen global wall, and which lawful pre-bet current-node work reduction is
best supported by the already-sealed ADR-0278 timing matrix?

This is a label-free engineering result. It invokes no h32 runner, evaluates no
candidate endpoint, retreat, certificate, or strategy-quality row, and emits
no policy.

## Repository and evidence boundary

The continuation began from clean detached commit `23283a4`, “Seal rejected
action-width capacity run.” The ADR-0278 result and checkpoint byte hashes
reproduce exactly, and both retain file-specific `-text` attributes. Every
ADR-0277 code/configuration pin matches the corresponding LF Git blob. The
source-blueprint result is the deliberate Windows exception: its frozen hash
matches the retained CRLF working bytes, while Git's unqualified text blob is
LF. No sealed artifact was rewritten.

The shared deadline is a new `campaign_deadline` successor module. The first
implementation attempt changed the historically pinned `runner_harness` hash;
the complete-suite provenance controls rejected all 15 affected frozen configs.
`runner_harness` was therefore restored byte-for-byte before this checkpoint.

The analysis reads only the pinned ADR-0278 result. It first requires the
rejected decision, the sole failed `resource_caps` leaf, the complete 36-target
runtime matrix, immutable one-size emission, and zero candidate endpoints,
retreats, certificates, strategy rows, or policy emissions. It reconstructs
the frozen proxy with maximum error below `1e-9 ms`. Redacted master variables
and values are neither present nor reconstructed.

## Active campaign deadline

`campaign_deadline.MonotonicCampaignDeadline` now owns one `monotonic_ns` start
and deadline for a complete campaign. Before every target or arm, its
`bounded_unit` guard:

1. calls the required byte-truth checkpoint callback;
2. observes the same monotonic clock after checkpointing;
3. admits the unit only if its complete frozen worst-case duration still fits;
4. observes again immediately after the unit; and
5. raises `CampaignDeadlineStop` on insufficient remaining time, a unit-bound
   overrun, or a crossed campaign wall.

The stop carries finite JSON-safe reason, unit, elapsed, remaining, bound, and
actual-unit telemetry. A successor may catch it only to persist the stop,
release resources, and retain its frozen fallback. No later unit or label may
open. Invalid limits, clocks, rollback, names, or callbacks fail closed.

This mechanism does not infer a unit bound from observed timings. Every
successor config must freeze a complete indivisible target/arm bound before
execution. It also does not replace the 15-second street ledger or its
one-second emission reserve. The global campaign wall and live decision wall
remain independent controls.

## Proven dataflow

The warm-step hypothesis is resolved for the ADR-0277 pre-bet restricted
master, not for other Pontius generators. After `solver.step()`, the only
solver-state reads are `last_step_work` timing/work telemetry. The later master
call consumes `axis`, `gain_rows`, `caps`, and the frozen tolerance; it consumes
no solver policy, regret, average, value, or warm-work object. The master rows
come from the immutable embedded blueprint, exact source evaluations, eleven
cross-payoff passes, and the current-node axis. An AST control freezes that
dependency.

The exact initial rows have a wider dependency surface. A lawful speculative
entry must bind:

- the complete immutable policy, including all fixed future own and opponent
  rows;
- the exact target belief, hands, and game provenance;
- the continuation prefix, remapped topology, terminal/payoff structure, and
  current action schema;
- acting player, payoff player, public node, profile versus fixed-response row
  role, and every fixed-response tape;
- the row/contraction primitive and numerical-contract identities; and
- the literal persisted cache-entry bytes.

On lookup, the restored row must still reproduce its exact source value under
the current source probabilities within the unchanged `2e-11` row ceiling.
Any digest, schema, response, byte, finite, or numerical mismatch is a miss and
returns the immutable blueprint path. A cached coefficient row is not a cached
strategy and cannot replace independent final certification.

## Read-only timing counterfactuals

The two-size measured component medians are:

| Component | Median ms | Minimum ms | Maximum ms |
|---|---:|---:|---:|
| Warm step | 9,331.229 | 2,269.646 | 22,983.509 |
| Eleven initial rows | 17,292.335 | 4,130.402 | 41,482.932 |
| Source all-seat oracle | 9,523.977 | 2,351.469 | 23,136.167 |
| Five fixed-response rows | 7,869.172 | 1,813.003 | 18,537.481 |
| First master | 2.086 | 1.910 | 2.357 |

Removing the nonfeeding warm step changes only the successor schedule and the
oracle proxy's `max(source, warm)` term. Its direct counterfactual saves a
median `9,331.229 ms`, but only 3 of 36 two-size arms fit and no complete acting
position fits. It is necessary cleanup, not the capacity solution.

The eleven initial rows are the largest removable measured block. The
following calculations assume zero cache lookup/validation cost and therefore
are ceilings, not passing evidence:

| Two-size proxy | Median ms | Arms fitting | Complete positions | Worst seat-5 ms |
|---|---:|---:|---|---:|
| Frozen ADR-0277 formula | 56,232.770 | 0/36 | none | 23,068.418 |
| Remove warm only | 46,901.542 | 3/36 | none | 19,474.819 |
| Exact initial-row hit only | 38,960.814 | 4/36 | none | 16,560.095 |
| Remove warm + exact initial-row hit | 29,629.585 | 6/36 | seat 5 | 12,966.497 |

The combined conditional path leaves `2,033.503 ms` before the 15-second wall
on the worst seat-5 source. It does not establish a cache hit rate, lookup
latency, validation latency, or fresh position capacity.

## Alternatives not selected

### Incremental bet-6 overlay

Two-size full-layout work is slower than paired one-size work on all 36 targets.
Median two/one ratios are `2.833x` for the eleven rows, `2.863x` for the five
fixed-response rows, and `1.927x` for the source oracle. Those differences are
confounded measurements of two complete implementations; they do not isolate
an added action column or subtree.

For a deliberately optimistic falsifier, assume one-size work is available at
zero live cost and every overlay costs only the observed paired difference.
After removing warm work, initial-row overlay alone fits 3/36 arms; extending
the assumption to future cut rows fits 5/36, but no complete position and the
worst seat-5 proxy remains `15,855.612 ms`. Seat 5 fits only after also assuming
endpoint-oracle contraction falls to the paired difference. No primitive or
measurement supports that third assumption. Do not implement the overlay first.

### Anytime separation

An anytime schedule can safely preserve blueprint fallback, and the new global
deadline supplies its outer stop. But ADR-0277 opened zero master-candidate
endpoints, cuts, retreats, or proofs. Its artifact contains no empirical
sequence from which to price incumbent arrival, separation depth, or certified
value. Scheduling cannot make the frozen complete-round capacity question pass
by definition. Defer it until a separately preregistered label-free mechanism
trace exists.

## Dissent and kill criteria

Supporting evidence is the complete source-crossed timing matrix, exact proxy
reconstruction, and static warm/master dependency control. Opposing evidence
is that the only capacity-looking row-cache result assumes a free hit and still
helps only seat 5; every other position remains above 15 seconds. Speculation
also moves work off-clock rather than reducing total compute and may have a low
real decision-prefix hit rate.

The largest unknown is whether a fully bound row entry can be restored and
validated cheaply enough while preserving Float64 identity and exact response
facets. The cheapest falsifier is a CPU/h2 round-trip and adversarial-key suite,
followed—only after a fresh preregistration—by a label-free timed differential
that charges lookup and validation. Kill the cache path on any key alias,
source-row error above `2e-11`, response-tape mismatch, non-byte-truth entry,
fallback mutation, or conservative worst-seat-5 proxy above `15,000 ms`.

## Decision

Close R41's implementation prerequisite: every future bounded GPU campaign
must use the shared active monotonic deadline, a byte-truth checkpoint before
each frozen unit, and a preregistered complete unit bound. ADR-0277 remains
sealed and must never be rerun.

For the pre-bet current-node successor, remove the nonfeeding warm step and
prioritize an exact, full-provenance source/current-prefix initial-row cache
control. Authorize CPU/h2 implementation and a future separately preregistered
label-free timing differential only. Do not yet authorize h32 execution,
action-width strategy quality, a bet-6 overlay, an anytime separation claim,
or any relaxation of the street ledger, campaign wall, memory caps, Float64
ceilings, independent certificate, or immutable-blueprint fallback.

## Claims boundary

This result establishes a shared fail-fast campaign primitive, a read-only
timing decomposition, and one restricted-master data dependency. It makes no
action-width quality, cache-hit-rate, capacity, optimizer-convergence,
deployment-latency, population, multi-seat, composition, cross-street,
chip-EV, AIVAT, exploitation, or poker-strength claim. The one-size blueprint
remains the only external policy.
