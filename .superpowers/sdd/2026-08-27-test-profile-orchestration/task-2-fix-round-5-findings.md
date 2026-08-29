# Task 2 fix round 5 — final independent-review findings

Round 4 is rejected. This is the fifth and final correction round. Work remains
uncommitted in `D:\Pontius-worktrees\orch-task2`; the immutable round-4 delta is
`task-2-fix4-review.patch` with SHA-256
`6053f7c81db5ca67736d77e8de317b927ba06ff4c0d1a4ac6c2be40fc98f0c6b`.

No scientific/GPU payload, capability emit/approve/write operation, OneDrive
access, commit, merge, or push is authorized. Add deterministic RED tests for
every item before changing production code. A GREEN result is not sufficient:
the final candidate must be frozen and independently rereviewed by both scoped
reviewers and CodeRabbit with untracked files included.

## Analyzer and discovery contract

1. Source-order-evaluate helper return expressions against helper-local state.
   Exact protected aliases must propagate. Divergent or possibly protected
   returns become sensitive unknowns and deterministic blockers. Literal-child
   analysis must suppress the parent row when a nested protected sink is not
   resolved.
2. Unsupported expressions must preserve the union of child sensitivity.
   Unsupported attribute/subscript stores receiving protected provenance must
   poison the reachable root or emit a stable store-site blocker. Unary and
   other unsupported composites may never turn a protected value into a safe
   value. Apply the same rule inside literal children.
3. Match analysis must retain the no-match path unless an unguarded irrefutable
   case proves exhaustion. Guard-failure state proceeds to later cases; possibly
   sequential guard calls add, while mutually exclusive bodies take their exact
   maximum. Ambiguous residual state blocks.
4. Propagate exceptional state from every reachable mutation/throw site through
   nested compound statements. Handlers may not fall back to the incoming
   pre-try environment. Join exact exceptional states or block ambiguity.
5. While tests use statement-point flow, never the final module assignment map.
   A loop containing a protected sink either has an exact finite bound or a
   dynamic-repetition blocker. Add a reconciliation invariant requiring every
   sensitive census site to map to a review row, blocker, or explicit proved
   unreachable record.
6. Expression evaluation returns value plus state effects. Join walrus effects
   from conditional expressions and propagate comprehension walrus bindings
   according to Python scope rules; otherwise poison later bounds.
7. Conditional-decorator provenance tracks every Python binder at its definition
   point. Function/class definitions, imports, from-imports, assignment targets,
   loop/with/exception/match bindings, and unsupported rebindings of a retained
   `skipIf`/`skipUnless` alias must replace it with the unresolved sentinel.
8. All analyzer traversal uses the one shared per-item/child budget. Deep ASTs
   must produce stable `InventoryError`/blocker outcomes rather than raw
   `RecursionError`. Use checked addition and multiplication at every cardinality
   merge/scale/normalization; any result above 2,147,483,647 blocks or errors.
9. Detect literal `unittest.skip(<literal>)` across class and method decorator
   lists. The only accepted form remains exactly one method-level literal skip in
   outermost position for a registered `DECLARED_SKIPS` stable ID. Inner,
   multiple, class-level, or otherwise unapproved unconditional skips fail closed;
   do not broaden the approved skip contract.

Required locked reproductions include local helper alias return, divergent
protected return, dynamic attribute/subscript store, unary protected value,
no-match and guard-failure match paths, sequential protected guards, mutated
exception environments, final-global while reassignment, IfExp/comprehension
walrus effects, decorator function/import rebindings, a 900-term expression, and
cardinality overflow from 2,147,483,647 plus a later call.

## Transaction and I/O contract

10. The complete explicit destination set is acquired before source, Git, or
    destination observation for a write operation. Capture authoritative
    destination snapshots only inside the locked scope; caller pre-snapshots are
    not the pair-write API. A losing cooperative writer is refused before reads
    or expensive derivation.
11. Remove closure inference and function-attribute destination metadata from the
    governance boundary. `_with_governance_attribute_lease` receives the immutable
    destination set explicitly. Every active-group write normalizes its target
    and asserts membership before path observation; an undeclared path fails with
    unchanged bytes and no Git/source work.
12. Native alias rejection runs after all locks are acquired and before the first
    participant is added, for direct and active-group pair paths. Hardlinks and
    other same-file aliases fail deterministically with unchanged bytes and no
    artifacts.
13. Cleanup-manager entries have an exclusive retry state/generation. Only one
    thread may invoke a pending owner at a time; concurrent callers wait for or
    reuse that result. Owner callbacks remain outside the registry mutex.
14. Writer entry retries existing cleanup before reserving capacity. A full queue
    of recoverable entries must clean and then admit the writer; persistent
    entries still fail before destination observation.
15. `_GitLaunchLease` cleanup is component-idempotent. Its descriptor and every
    ancestor handle have independent monotonic ownership state; a successful
    component close is never replayed after another component fails.
16. Do not start a fallible multi-owner lock release before cleanup-pending
    ownership can be retained. Pending descriptors report exact currently-held
    lock keys, released keys if exposed, exact lock sidecar artifacts, and exact
    remaining owner roles—not the original destination set as though all locks
    remain.
17. POSIX deterministic locks are created/unlinked by basename through one
    securely opened, retained parent directory descriptor using `dir_fd`,
    `O_EXCL`, `O_NOFOLLOW` when available, and verified parent identity. Reuse the
    anchored parent for publication or deterministically refuse drift. Descriptor
    state must probe/verify identity after close exceptions so a
    close-succeeded-then-raised path never retries a reused numeric descriptor.
    Apply the same safe ownership rule to staging, published, recovery, directory,
    and Git descriptors.
18. Validate `_retain_transaction is True` before any directory-chain work or
    platform writer dispatch. Invalid internal modes must have zero publication
    or cleanup side effects.

Required locked reproductions include operation-entry read/lock ordering, a
dict-captured undeclared target, active-group write outside the declared set,
active-group hardlink pair, concurrent retry of one pending owner, recoverable
full-capacity entry, partially failing real Git lease, per-position partial lock
release truth, POSIX parent exchange, close-succeeded-then-raised descriptor roles,
and invalid retained-transaction dispatch.

## Final acceptance

- All new RED cases must fail on the frozen round-4 files and pass after the fix.
- Existing inventory, configuration, and exact H32 focused suites remain green.
- Ordinary all-zero `--write`/`--check` remains byte-stable; capability definitions
  and bindings remain `0/0/0`, both capability digests remain all-zero, and the
  cleanup manager is empty.
- Regenerated inventory/profile counts, canonical row/blocker reconciliation,
  hashes, LF/BOM/whitespace/static gates, status, and zero-artifact census are
  recorded in `task-2-report.md`.
- No commit or integration occurs before a clean frozen direct rereview and a
  CodeRabbit review using `--include-untracked`.
