# Task 2 fix round 5 — corrected-candidate rereview findings

The narrow correction patch
`task-2-fix5-final-rereview-correction-review.patch` is rejected at SHA-256
`a022a11d2503f418f7c400f1c34670704bac80504a667ac1d73ecf035a24aa12`
(90,938 bytes). The complete candidate patch `task-2-fix5-final2-review.patch`
is rejected at SHA-256
`8edda6c89f37955e557ccfe847c7c5143f5587566a95210ad5807e6d1504f8ab`
(412,097 bytes).

No scientific/GPU payload, capability operation, OneDrive access, commit,
merge, or push is authorized. Every correction below requires a deterministic
RED reproduction against the frozen rejected generator before production edits
and an integrated production-path GREEN test afterward.

## Binding production corrections

1. **Eliminate the arbitrary governance callback boundary.** Supplying explicit
   destination paths beside `action(revalidate)` is not structural: the action
   can call `revalidate()` (Git work) and only then attempt an undeclared write.
   Remove the target-taking/unrestricted callback API. Replace it with a closed
   publication/session operation whose immutable destination slots are built
   and lexically normalized before locks; optional repository enforcement may
   disable Git/attribute validation but never destination coordination. The
   coordinator alone publishes to pre-bound slots; derivation returns payloads
   or typed results, never paths, and receives no callable that can trigger Git
   before operation-shape validation. The exact legacy callback form must be
   rejected or absent before cleanup/Git/source work.
2. **Make raw parent ownership nonfallible and prior to every probe.** The
   current provisional `_PosixDescriptorOwner` constructor performs `fstat`
   before registration. Create a persistent close-once slot before `os.open`,
   adopt the returned fd immediately, and register that already-existing owner
   before `fstat`, identity, type, or wrapper construction. Constructor/probe
   failures must close or truthfully retain the fd exactly once.
3. **Model exact nested throw-site state in the independent preclassifier.** Do
   not use pre/post whole-statement snapshots or `ast.walk` to approximate
   raises/calls. Add independent recursive control successors at least for
   normal/raise (and preserve return/break/continue where applicable), evaluate
   expressions and compound headers in source order, and feed handlers every
   exact reachable exceptional snapshot. Lock safe and protected nested `if`
   throw branches, multiple throw sites, and handler calls; census and primary
   resolver must reconcile without a missing disposition.
4. **Register POSIX staging namespace ownership immediately after exclusive
   creation.** `staging_name`/path ownership begins when `os.open(O_CREAT |
   O_EXCL)` returns, before descriptor identity or any second `fstat`. Probe
   failure must leave the `.tmp` name in rollback/artifact ownership until a
   real unlink consumes it. Remove or integrate the unused
   `_PosixNamespaceOwner`; helper-only tests do not satisfy this contract.
5. **Make POSIX restoration/sync retry monotonic and integrated.** If publish
   `fsync` and the first rollback-entry `fsync` both fail, later retry must still
   restore the original destination and finish; cleanup must not clear the only
   descriptor/state used by restoration. Update namespace/publication state
   immediately after each successful syscall and before `fsync`. Report
   `recovery` whenever a recovery name remains. Add real writer tests for
   exchange/replace/link restoration, repeated sync failure, staging/recovery
   unlink failure, and the absent-target link-success/staging-unlink failure.
6. **Make Windows absent-target rollback monotonic after ambiguous close.** Do
   not clear the only temporary/publication state before the published
   destination disposition/close outcome is reconciled. A close exception may
   never lose the local handle or leave `published=True` with no retry state.
   Drive the real Windows writer path; remove early returns that bypass the
   production writer in persistent-close tests.

## Binding integrated test corrections

7. Exercise same-inode/same-number close-once semantics through each distinct
   production owner family (Git lease/acquisition, deterministic lock, POSIX
   writer roles, Windows writer/lock roles), not six labels on one generic
   owner. Assert exactly one consuming close attempt and no closure of the
   reopened same-file descriptor/handle.
8. Exercise partial **multi-component** Git acquisition through the real
   acquisition path: at least a leaf descriptor plus ancestor component, one
   successful close and one retained pre-close failure, exact bounded-manager
   transfer, independent cleanup, and eventual empty state. A finished fake
   lease or one-component POSIX case is insufficient.
9. Exercise requested/acquired/outstanding lock truth through production
   acquisition: fail the first relative sidecar open after parent acquisition,
   force a retryable pre-close parent cleanup failure, verify zero held/released
   lock keys and zero lock artifacts, then retry without inventing a lock.
10. Replace helper/state-shape namespace tests with real
    `_write_posix_governance` and `_write_windows_governance` failure schedules.
    Assert exact bytes, extant names, roles, artifacts, pending state, retry
    operations, and eventual zero-artifact/zero-manager cleanup.

## Preservation and final acceptance

- Preserve the already-correct match exhaustion, generation-bound cleanup
  waiter outcomes, exact-True retain validation, lock-first default/opt-out
  entry behavior, canonical destination ordering, pair-owned CAS, irreversible
  group commit, and all prior analyzer semantics.
- Generated inventory/profile bytes and all substantive reconciliation,
  capability, H32, configuration, artifact, and manager outcomes remain fixed;
  only explained test-line receipt movement is permitted.
- Final acceptance requires a new immutable narrow/full package, direct scoped
  and adversarial CLEAN verdicts, full integration CLEAN, and CodeRabbit with
  `--include-untracked` on the exact final bytes.
