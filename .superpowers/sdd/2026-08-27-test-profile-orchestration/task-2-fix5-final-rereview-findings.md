# Task 2 fix round 5 — final frozen rereview findings

The transaction patch `task-2-fix5-transaction-review.patch` is rejected at
SHA-256 `4b545883089aa36ec497add94ca1bbd05001360b959ed8d270cdd8d2bbdc4d02`
(107,589 bytes). The full eight-file patch
`task-2-fix5-final-review.patch` is rejected at SHA-256
`273ff252879e7843ce8329a5b0a7ce3eaa8b7a84d5b579030a4e4c8f310eb52e`
(297,834 bytes).

No scientific/GPU payload, capability operation, OneDrive access, commit,
merge, or push is authorized. Add deterministic RED tests for every item before
changing production code, then rerun the complete focused, direct, isolated,
generation, static, artifact, and review gates on the final bytes.

## Binding corrections

1. **Critical — never retry a numeric descriptor after a close attempt can
   have transferred ownership.** The current `(st_dev, st_ino, st_mode)` probe
   cannot distinguish a reopened descriptor for the same inode. Reproduce by
   closing the original, reopening the same file onto the same numeric fd, and
   raising from the close action; retry must never close the new owner. Use a
   monotonic ownership rule that is safe for every descriptor/handle role and
   does not rely on same-file identity to authorize a replay.
2. **Write-entry ordering remains incomplete.** Default/opt-out
   `emit_design_review` and `write_design_capabilities` still capture/derive
   before the destination lock. The generic attribute-lease callback can also
   attempt an undeclared active-group target only after Git work has run.
   Redesign the callable boundary so every possible target is structurally
   declared and membership-validated before Git/source/derivation/destination
   observation; a losing or undeclared writer performs none of that work.
3. **Cleanup waiters must observe their captured generation's exact result.**
   A barging caller can currently begin generation N+1 before a waiter for N
   reads `last_error`, causing that waiter to reuse the wrong success/failure.
   Store completion/result by generation (including success after registry
   removal) so one callback runs per generation and every waiter receives the
   generation it joined.
4. **Git acquisition failure must retain partial component ownership.** During
   `_acquire_git_launch_lease`, a validation or ownership-probe failure can
   leave a descriptor/ancestor open after another component closes. Put every
   acquired component under a cleanup owner immediately, close components
   independently even if one probe/close fails, and transfer any remainder to
   the bounded cleanup manager. Add the required partially failing real
   acquisition reproduction; constructing a finished fake lease is not enough.
5. **POSIX parent descriptors need provisional ownership immediately after
   `os.open`.** `fstat`, type, identity, or owner-construction failure before
   registration currently leaks the fd. A chain-capture/open parent exchange
   must refuse while closing or retaining that fd exactly once.
6. **Pending lock truth must distinguish no acquired locks.** If only the
   retained parent-directory owner exists and the first relative sidecar open
   fails, `outstanding_lock_keys()` currently reports the entire original set.
   It must report zero held destination keys and zero lock artifacts while
   retaining only the actual parent owner; later retry must not invent locks.
7. **POSIX namespace ownership must survive descriptor cleanup.** Track staging
   and recovery filenames independently from descriptor variables. If both
   initial unlink attempts fail, later retries must continue to own/report and
   remove the extant artifact rather than declare cleanup success after the fd
   becomes `None`. If directory `fsync` fails after namespace restoration,
   update state monotonically so retry can finish truthfully without stale
   publication flags or nonexistent recovery paths.
8. **The independent sensitive preclassifier must exhaust irrefutable
   `match`.** Remove the incoming no-match residual once an unguarded
   irrefutable case is reached. Lock the exact case where a protected alias is
   overwritten safely in `case _` and a following attribute call is not a
   sensitive census site.
9. **The independent sensitive preclassifier must use throw-site state.**
   Handler analysis may not restart from the pre-`try` environment. Propagate
   each reachable exceptional successor state through handlers, including a
   protected alias assigned immediately before a reachable raise.
10. **Lock exact retained-mode identity in tests.** The implementation uses
    `is not True`, but the regression currently supplies only `False`. Cover
    `None`, `False`, and integer `1`, proving all reject before directory-chain
    or platform dispatch with zero side effects.

## Required preservation

- Preserve the already-clean round-5 analyzer semantics outside items 8–9,
  canonical destination ordering, pair-owned locked snapshots/CAS, irreversible
  group commit, role-exact cleanup descriptions, and the approved H32 skip.
- Generated inventory/profile bytes, inventory row/blocker counts, analyzer
  behavioral digest, capability counts/digests, and zero-artifact outcome must
  remain unchanged except for explicitly explained test-line receipt movement.
- The final immutable candidate requires fresh scoped direct review, fresh full
  integration review, and a final CodeRabbit pass including untracked files.
