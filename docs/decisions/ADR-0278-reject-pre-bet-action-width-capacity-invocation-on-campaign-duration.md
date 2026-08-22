# ADR-0278: Reject pre-bet action-width capacity invocation on campaign duration

- Status: accepted rejection record; ADR-0277 invocation and widened authorization rejected
- Date: 2026-08-22
- Implements: ADR-0277
- Clean preregistration commit: `db1b933bf718a4863f2cd4248ca279b3d8e804dd`
- Result: `experiments/results/h32-pre-bet-action-width-capacity-v1.json`
- Result SHA-256: `d9b0518d6df8c71afaea573cca8668217fec6ed6490544f74b155ab67956f9d7`
- Checkpoint: `experiments/results/h32-pre-bet-action-width-capacity-v1.partial.json`
- Checkpoint SHA-256: `a94e66fda42258cc4494cd3d026de7b9c97b8757da40f4e560e5ab5e232360e0`

## Formal result

Reject the single authorized ADR-0277 invocation. The frozen runner completed
the entire 36-target, 72-arm cache and runtime matrix in `3,844.795 s`, which
exceeds the preregistered `3,600 s` campaign ceiling by `244.795 s`. The final
result therefore records `passed = false`, fails `resource_caps`, and selects
`reject_pre_bet_action_width_capacity_execution`.

Do not override the ceiling after observing the matrix, reinterpret the result
as a passing capacity screen, or rerun it under ADR-0277. The complete artifact
and byte-identical checkpoint are retained so that the failure and all opened
capacity measurements remain auditable.

## Failure localization

Campaign duration is the only failed resource component and the only failed
leaf gate. Every cache build is below its `120 s` ceiling; the maximum is
`31.960 s`. Every warm step is below `120 s`; the maximum is `22.984 s`.
Every eleven-row construction is below `120 s`; the maximum is `41.483 s`.
All cache, identity, geometry, conditional-barrier, warm-identity, row,
master-numerics, current-node, immutability, checkpoint-byte, evaluation-count,
finite, and immutable-emission gates pass.

The runner checks the global wall ceiling only during final gate assembly. It
therefore completed another `244.795 s` of work instead of stopping at the
deadline. This fail-late behavior is a process defect even though it produced
a complete diagnostic matrix. R41 records the general risk; a successor GPU
runner must carry a monotonic deadline and checkpoint before beginning another
bounded unit when insufficient campaign time remains.

## Diagnostic cache observations

The following measurements are retained as engineering diagnostics, not as a
passing ADR-0277 conclusion.

All 72 caches satisfy the global memory barrier. Peak GPU-pool total is
`5,169,158,656` bytes, leaving `6,830,841,344` bytes below the frozen 12 GB
pool cap. Minimum physical free memory is `9,960,423,424` bytes, or
`4,775,967,260` bytes beyond the frozen non-cache reserve.

The canonical affine/shared-topology representation removes widening's
persistent-memory penalty:

| Quantity across 36 paired targets | One size, median | Two sizes, median | Paired two/one median |
|---|---:|---:|---:|
| Persistent numeric bytes | 2,967,972,552 | 2,799,341,656 | 0.948x |
| Raw-equivalent automaton bytes | 2,966,172,672 | 5,742,938,688 | 1.948x |
| Logical middle-rank total | 7,902.5 | 15,393 | 1.948x |
| Stored topology middle-rank total | 7,902.5 | 7,490.5 | 0.948x |
| Cold construction | 3,068.674 ms | 19,156.660 ms | 6.278x |

Maximum per-automaton middle rank has the same `73–119` range and median `93`
in both arms. The two-size arm nearly doubles logical topology but shares it
down to slightly less stored device state than the raw one-size cache. Cold
construction, which remains prepared/off-clock work, is the representation's
clear cost.

## Diagnostic runtime observations

The complete conservative proxy is compute-bound, not memory-bound. Median
warm-step time is `3,407.457 ms` for one size and `9,331.229 ms` for two;
median eleven-row construction is `6,287.374 ms` and `17,292.335 ms`; median
source all-seat oracle time is `4,938.555 ms` and `9,523.977 ms`. The resulting
median complete-round proxies are `25,260.974 ms` and `56,232.770 ms`.

No two-size arm fits 15 seconds. The closest is
`panel_3/blocker_heavy/checks_to_seat5` at `15,811.629 ms`, while the maximum
is `132,078.285 ms`. No acting position therefore fits across all six sources.
Nine one-size arms fit: all six seat-5 targets and three seat-4 targets. Only
seat 5 fits one size across every source.

These rows do not authorize a population rate or a post-hoc position policy.
They identify the engineering wall: the shared cache has already made action
width memory-safe, while resident warm and exact coefficient/oracle work still
scale beyond the street ledger.

## Frozen-label integrity

The checkpoint contains all 36 cache rows and all 36 runtime rows and its
recorded digest matches the persisted bytes. The run executes exactly 72 warm
steps and 432 embedded-blueprint seat evaluations. Maximum source-row error is
`3.18e-16`; maximum master primal and dual errors are `7.54e-14` and
`2.67e-15`. Every projected change is confined to public node zero and every
later own-policy row remains immutable.

File-specific Git attributes disable newline normalization for both artifacts;
their committed blobs therefore retain the exact persisted-byte digests above.

All 72 redacted master candidates are constructed but none is evaluated.
There are zero master-candidate endpoints, retreats, certificates, serialized
strategy-quality rows, or candidate emissions. The immutable one-size
blueprint is the only external policy. No one-size-versus-two-size strategy
quality label was opened.

## Decision

Retain the one-size system and keep widened strategy quality closed. Do not
spend another GPU campaign merely to replace the observed one-hour ceiling
with a post-hoc larger value. The complete timing matrix may guide a separately
preregistered engineering differential, but it cannot authorize widening.

Before any further bounded campaign, install an active monotonic campaign
deadline in the shared runner path. For action width, stop pursuing further
cache compression: the affine/shared topology has already discharged memory.
Any successor must reduce resident contraction/oracle work enough to fit a
complete source-crossed position under 15 seconds, then pass on a fresh frozen
capacity question before any widened strategy label is evaluated.

## Claims boundary

This is a rejected label-free capacity invocation on a fixed retained source ×
position matrix. It makes no action-width quality, optimizer-convergence,
direction-obsolescence, deployment-latency, population, multi-seat,
composition, cross-street, chip-EV, AIVAT, full-width, exploitation, or poker-
strength claim. The independent exact certificate remains the only future
emission authority.
