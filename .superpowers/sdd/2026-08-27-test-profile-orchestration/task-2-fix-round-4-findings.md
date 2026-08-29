# Task 2 fix round 4 — binding penultimate correction brief

Read `task-2-brief.md`, all three earlier fix-round finding files, the complete appended `task-2-report.md`, and the round-3 controller rulings before acting. Work only in `D:/Pontius-worktrees/orch-task2`; use one implementation agent, strict RED-before-GREEN tests, and no subagents. Do not execute repository payloads, emit/approve/write capabilities, touch OneDrive, commit, merge, or push. Preserve every previously addressed contract. Append exact evidence to the report and leave the worktree frozen/uncommitted for the same two reviewers.

Binding round-3 review inputs: patch SHA-256 `1b7a3d6375c655253fa73b58202d3b8a5655593f5eb81fcdec4c3cb8f6495c86`; report SHA-256 `0246d849570772bd56108d1885f51fadb13937c95a2a990e5b67078411007f23`. CodeRabbit again returned zero analyzer findings; the direct native/AST reproductions below control.

## Transaction root A — canonical lock-set lease and logical pair commit

1. Introduce one explicit lock-set lease for the complete destination set. Normalize and reject duplicate/aliasing destinations, sort by the platform-canonical absolute identity key, and acquire every deterministic lock in that order **before any destination/source snapshot, identity read, or validation**. Standalone uses a one-member set; pair uses the complete set. A compliant second writer must be refused/wait before it reads a destination. Retain the complete lock set, parent/object handles, and rollback owners until the logical operation reaches a terminal state.

2. Pair children may not independently release locks or other pair-owned resources. Split child operations into prepare/publish, validate, logical commit decision, and cleanup. After validate-all succeeds, classify the entire pair committed once; from then onward no child or outer cleanup failure may cause rollback or split restoration. Release locks only after all children are classified and cleanup is complete or explicitly transferred to cleanup-pending ownership.

3. Add deterministic native concurrency tests: two writers request the same pair in reversed argument order; the loser cannot validate/read/publish either destination. Inject a normal compliant standalone writer between first and second child cleanup; it must remain excluded until the pair releases the whole lock set. Assert coherent exact bytes, terminal status, and zero artifacts after ordinary success.

## Transaction root B — explicit precommit, committed, and cleanup-pending ownership

4. Replace implicit `open/finalized` plus best-effort close swallowing with explicit state/outcome semantics at least distinguishing `precommit`, `committed`, `cleanup_pending`, and `rolled_back`. Never detach a native handle/temporary-directory/Git lease owner until close/cleanup is confirmed. A retry limit may bound synchronous work, but exhaustion must never become ordinary success or an unreachable raw handle.

5. Before logical commit, a persistent cleanup/close failure must preserve the transaction, deterministic lock, and rollback action in an owned cleanup-pending object. After the injected close becomes available, a retry must finish rollback and remove artifacts. After logical commit, cleanup failure must never roll back; raise/return an explicit `committed-with-cleanup-failure` outcome carrying committed destination status, outstanding owners, retry identity/action, and artifact/lock status. Retain pending owners in a bounded process-lifetime cleanup manager, retry on the next writer entry and at process exit, and expose a deterministic test-only retry seam. A persistent OS `CloseHandle` cannot synchronously promise zero artifacts; the truthful contract is explicit cleanup-pending state followed by verified retry/process-exit cleanup.

6. Apply item 5 to staging, published, recovery, deterministic lock, directory, Git lease, and attribute temporary-environment cleanup. A `TemporaryDirectory.__exit__` or Git-lease close failure after logical commit is postcommit cleanup failure and must not enter rollback. Add persistent fail-before-close tests for all four Windows object roles (more failures than the synchronous retry count), then restore the close primitive, invoke the retained retry, and assert exact final bytes plus zero artifacts/owners. Retain the older close-succeeded-then-raised tests to prevent double-close.

7. Keep the ruled Windows boundary honest: deterministic cooperative Pontius serialization is required; arbitrary same-user namespace mutation remains unsupported and is not a rejection criterion. Add the previously missing documentation regression asserting the limitation is explicit rather than pretending the impossible guarantee. Preserve parent anchoring, role-specific no-write sharing, continuous ordinary visibility, sealed POSIX Git execution, and the addressed POSIX exchange/non-exchange ordering.

## Analyzer root C — complete source-order effects or explicit safe blockers

8. Extend protected-value propagation so unsupported call results, Boolean/composite expressions, attribute/subscript stores, and helper returns cannot discard sensitive provenance. Exact supported cases may derive rows; unsupported cases must emit one deterministic blocker with no authorized row. Lock `identity(cp).arange(1)`, `box.backend = cp; box.backend.arange(1)`, `runtime_flag() and cp`, helper-returned `subprocess.run`, and the same forms inside literal child `-c` code. A child may never return a parent-only row when a descendant is unresolved.

9. Bind exact match captures from a known protected subject into the case/guard state. Direct and child `case backend if backend.arange(1)` must derive the exact CuPy row/bound or an explicit blocker—never disappear. Handle unsupported patterns by poisoning protected capture state.

10. Remove final-global `_static_assignments` from runtime cardinality decisions. Each loop/comprehension/range uses its source-ordered value at that statement. Sequential five-then-one and one-then-five loops over the same variable both derive total maximum 6. Conditional-expression alternatives use pointwise maximum, not sum (`cp.arange(1) if flag else cp.arange(1)` => 1). Preserve branch maxima, helper multiplication, dynamic blockers, and the canonical-affine 6 oracle.

11. Preserve exact environment state along deterministic exceptional paths. An unconditional assignment followed by raise must reach its matching handler; uncertain/divergent exceptional states must block rather than fabricate an empty environment. Restore exact inherited semantics for `os.environ.copy()` and all earlier approved inherited forms. Test direct and literal-child variants.

12. Resolve conditional decorators at their actual module/class/method definition point. Later alias reassignment must not retroactively change earlier classes. Any callable with possible retained `skipIf`/`skipUnless` provenance that becomes unknown must reject even when the condition is a literal or an aliased `os.name`. Lock earlier-class alias, reassigned unknown callable, and aliased-OS conditions.

13. Add deterministic termination/error containment. Enforce explicit helper recursion depth, total analyzed-node/site/work, child-depth/container, and maximum-cardinality budgets. A 1,050-deep acyclic helper chain, `range(..., step=0)`, and range cardinality overflow must yield stable `InventoryError` or explicit blockers—never raw `RecursionError`, `ValueError`, or `OverflowError`. Avoid path explosion; immediate structured joins and memoized exact helper summaries are preferred.

14. Preserve explicit scientific contracts, role-specific schemas, lifecycle/exclusion behavior, exact H32 loading, zero-scope capability refusal, and all earlier corpus oracles. Any blocker-count reduction must be exactly reconciled to newly supported sites, with constant sink census and explicit no-silent-site tests.

## Required verification and review

- Freeze one analyzer RED snapshot covering items 8–13 and one transaction RED snapshot covering items 1–7 before production changes.
- Independently review the intended analyzer lattice/effect semantics and transaction state transitions before implementation; record any controller ruling and its cost.
- After GREEN, regenerate only ordinary all-zero governance state. Run fresh full inventory/finalization, 53+ configuration, exact H32, byte-stable write/check, static/format/hash/status/diff/artifact checks, and cleanup-manager empty-state checks.
- Freeze a round-4 delta and dispatch both original scoped reviewers. No integration or commit until both are clean. If a fifth round is required, restrict it to concrete reproduced residuals; do not expand Task 2 architecture again.
