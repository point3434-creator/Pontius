# Task 2 fix round 5 — transaction/I/O acceptance map

This read-only map was produced against the analyzer-clean, pre-transaction
`tools/generate_test_inventory.py` snapshot with SHA-256
`2b2fada9631b1514840dc773aea70e50f6459fc0f0055579a18a77fc7b6bd062`.

## Required checks

1. Acquire the complete explicit destination set before any source, Git,
   derivation, or destination observation. Pair snapshots are captured inside
   that locked scope; a losing writer performs no observation or derivation.
2. Remove closure/function-attribute destination inference. Every active-group
   write normalizes its target and proves membership before path observation.
3. Reject native aliases only after all declared locks are acquired and before
   any participant is added, for direct and active-group pair writes.
4. Serialize retries by entry generation: one owner callback runs outside the
   registry mutex, while concurrent callers wait for or reuse that result.
5. Retry existing cleanup before capacity reservation. Recoverable full queues
   admit the writer after cleanup; persistent queues reject before observation.
6. Make Git descriptor and ancestor ownership component-idempotent. A component
   successfully closed once is never replayed after another component fails.
7. Retain cleanup ownership before fallible multi-lock release and report only
   currently held keys, extant lock artifacts, and remaining owner roles.
8. On POSIX, create and unlink lock basenames through one retained, verified
   parent `dir_fd` with exclusive/no-follow flags. Publication must reuse that
   anchor or refuse parent drift. Every descriptor role must treat
   close-succeeded-then-raised as final ownership loss and must not close a
   subsequently reused numeric descriptor.
9. Reject every `_retain_transaction` value other than exact `True` before
   directory-chain work or platform dispatch.

## Principal implementation regions

- Git launch lease/owner: `_GitLaunchLease.close`, acquisition cleanup, and
  `_GitLaunchLeaseOwner`.
- Governance lease/destination boundary:
  `_governance_action_destinations`, `_with_governance_attribute_lease`,
  `_GovernanceDestinationSet`, `write_atomic_lf`, and
  `_write_governance_pair`.
- Cleanup/ownership state: `_GovernanceCleanupManager`, POSIX descriptor and
  lock owners, `_GovernanceLockSetLease`, `_GovernanceWriteGroup`, and pending
  descriptor creation.
- POSIX anchoring/publication: directory binding, staging/published/recovery
  acquisition, POSIX writer, and deterministic lock acquisition/unlink.
- Entry points: ordinary write, capability write, and emit paths.

## Final-diff invariants

- Preserve canonical destination ordering, CAS identity/raw validation, pair
  rollback, irreversible group commit, and committed-cleanup semantics.
- Cleanup callbacks execute outside the manager mutex; ordinary success leaves
  zero pending entries and zero artifacts.
- Released resources are never replayed. Pending recovery descriptions are
  exact, not conservative copies of the original lock set.
- Canonical LF/BOM/size checks, Git identity binding, and attribute-lease
  lifetime checks remain unchanged.
- Capability definitions/bindings, inventory partitions, H32 ownership, and
  all-zero digest behavior remain unchanged.

## Material adjacent risks

- Critical: undeclared or hardlinked active-group writes can mutate bytes
  outside the locked namespace.
- Critical: POSIX parent exchange or numeric-descriptor reuse can redirect
  publication/cleanup or close an unrelated resource.
- Important: invalid retain mode currently reaches platform I/O; concurrent
  retries can double-run owner effects; a recoverable full queue rejects useful
  work; and pending descriptors overstate held locks while omitting artifacts.
