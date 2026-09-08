# ADR-0276: Post-fold failures close in two and three rounds

- Status: accepted retrospective diagnostic; exact global closure remains off-clock
- Date: 2026-08-22
- Implements: ADR-0275
- Clean preregistration commit: `abc88c5deca9cc4e9202f1ab7bd7db4f4b51f551`
- Result: `experiments/results/h32-post-fold-failure-closure-diagnostic-v1.json`
- Result SHA-256: `dc20dcfbaaa3b861af2976f91bd8d1ce43f6e327e7f765dc97c98b333ff56802`
- Checkpoint: `experiments/results/h32-post-fold-failure-closure-diagnostic-v1.partial.json`
- Actual checkpoint SHA-256: `aa7df3ac4a9f31ec52ce5c64014584d13fa782a3f4a0593a12d4495f02bb3eb6`

## Process result

The single clean execution passes every frozen parent, inventory, setup,
restoration, identity, reproduction, row, master, projection, response-
accounting, timing, memory, label, emission, finite, and null-claim gate. Both
targets complete without error in `15.945 s` offline. The run opens seven
retrospective optimizer endpoints, zero new retreat labels, and zero candidate
emissions. The immutable restricted blueprint remains the only external
policy.

Both ADR-0274 prefixes reproduce discretely and numerically before later-round
interpretation. First-cut and post-cut player lists are identical. Maximum
absolute reproduction error is `3.06e-15`, more than three orders of magnitude
inside the frozen `2e-11` ceiling.

## Closure-depth result

Both selected failures eventually close, but they do not both close in the
next round.

- `panel_1/blocker_heavy/checks_then_bet_seat1_then_fold_seat2` closes after
  three cut rounds. Round two extracts new response signatures for seats 0 and
  5 and costs `556.269 ms`, but leaves exact `U - L = 0.000267369891`.
  Round three extracts another pair of distinct response signatures for the
  same seats, costs `555.105 ms`, and closes at `9.10e-15`.
- `panel_3/balanced/checks_then_bet_seat4_then_fold_seat5` closes after two
  cut rounds. The added seat-2 and seat-3 rows plus the next master and exact
  oracle cost `764.960 ms`; the verified final gap is zero.

The histogram is therefore one target at depth two and one at depth three.
The repeated seat-0/seat-5 cuts are not duplicates: the exact response tapes
change again after the second master. Player identity alone cannot bound facet
depth.

Target wall times are `6.746 s` and `7.994 s`. GPU-pool allocation remains at
or below `5,044,957,696` bytes and physical free memory remains at or above
`10,465,837,056` bytes. The later rounds are cheap in this selected pair, but
the existing conservative live ledger has only `32.384 ms` of headroom and
the diagnostic intentionally omits a new retreat construction and proof.

## Checkpoint-hash defect

The durable checkpoint is valid JSON with both ordered outcomes, and the
runtime gate reread it and verified two attempts. Its recorded
`checkpoint_sha256` field is nevertheless wrong for the persisted Windows
bytes. The frozen helper hashes the canonical `LF` string before
`Path.write_text`; Windows then writes `CRLF` bytes. The field records
`ae90841ef4a1145e2fcfce0e5209c24c0fad02b6b3180d8eab2833c32c1ad9e4`,
while the actual file digest is
`aa7df3ac4a9f31ec52ce5c64014584d13fa782a3f4a0593a12d4495f02bb3eb6`.

This is a non-gating artifact-telemetry defect, not an optimizer, label,
checkpoint-completeness, or numerical defect. Preserve the raw result and
checkpoint rather than rewriting or rerunning them. Future checkpointed
runners must use `atomic_json_checkpoint.write_atomic_json_checkpoint`, which
writes bytes directly, rereads them, and returns the digest of the persisted
bytes. R40 records the general defect family.

## Decision

Reject the optimistic hypothesis that every fresh one-round failure is exactly
one additional round from closure. Under ADR-0275's frozen branch, keep exact
global closure off-clock. Do not open a deadline-admission or conservative-
repricing study from this selected pair, and do not spend measured slack
against the unchanged `13,967.616 ms` floor.

The one-round multidimensional master remains a bounded, exact-certified safe
candidate generator; full convergence remains an off-clock global one-seat
teacher. Thus direction guessing is obsolete for the converged teacher but is
not retired from the deadline-bounded live system. Preserve the existing
direction fallback and immutable no-op.

Return next to the still-open action-width branch with a separately
preregistered, label-free continuation-root one-size versus two-size capacity
preflight. Price the widened one-seat master shape, resident caches, warm step,
exact oracle, and complete deadline reserve before opening any widened strategy
label. This is a capacity question, not a one-size/two-size quality claim.

## Claims boundary

These are two outcome-selected failures on retained boards and source
blueprints. They estimate neither deployment closure rates nor unconditional
runtime. No new retreat or strategy candidate was evaluated. No live
admission, direction-obsolescence, multi-seat, composition, cross-street,
chip-EV, AIVAT, full-width, exploitation, or broad poker-strength claim is
authorized.
