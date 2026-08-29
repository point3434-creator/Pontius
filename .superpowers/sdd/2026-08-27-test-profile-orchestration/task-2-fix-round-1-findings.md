# Task 2 fix round 1 — binding findings

Read `task-2-brief.md` first. The approved specification and brief remain authoritative. All implementation and tests run only in `D:/Pontius-worktrees/orch-task2`; the old C: worktree is read-only. Use test-driven development, do not spawn subagents, do not run payload tests, and do not write or approve a capability table. Append the full command/output evidence and self-review to `task-2-report.md` and return only status, commit(s) if explicitly authorized, a one-line test summary, and concerns.

## Critical / blocking

1. Analyzer completeness and subprocess semantics (`tools/generate_test_inventory.py` around prior lines 3070–3115, 3182–3234, 3411–3441, 3462–3565, 3619–3905): invoked lambdas, callable aliases, local-class runtime bodies, per-test `setUp`/`tearDown`, callbacks, and unknown/mixed receivers must either resolve exactly or emit explicit blockers. Enforce an exact keyword schema for every supported subprocess API. Distinguish omitted/inherited environment from full replacement, model removals correctly, and reject unsupported `executable`, `preexec_fn`, descriptor/session, stdio/input, and related semantics. Add RED tests for the reproduced zero-row/zero-blocker lambda and alias cases plus keyword/environment cases.

2. Runtime call bounds (`tools/generate_test_inventory.py` around prior lines 3077–3079, 3903–3918, 4000–4065): `maximum_calls` must be a path-sensitive runtime upper bound, multiplying statically bounded loops/comprehensions and taking branch maxima rather than syntactic node counts or branch sums. Dynamic repetition must block. Add real-corpus loop oracles, including the five-element/two-call case whose maximum is 10.

3. Publication source-snapshot lifetime (`tools/generate_test_inventory.py` around prior lines 5027–5073, 5181–5197): compose source/helper, inventory/profile, Git/attribute, and destination CAS revalidation into every pre/post replacement callback and the final pair/standalone validation. Keep recoveries until the combined final check succeeds. Add mutation seams immediately before publication and after the first pair replacement.

4. Windows recovery correctness (`tools/generate_test_inventory.py` around prior lines 2461–2518): a close failure on an old recovery must never cause rollback/cleanup to delete the restored governance file. Never restore a delete-pending handle without cancelling and verifying disposition; preferably do not arm recovery deletion until all fallible validation and pair finalization succeeds. Add standalone and pair regressions at the exact old-recovery close boundary.

5. Required H32 gate: make the prescribed fresh `-B -P` execution of `tests/test_h32_pre_bet_initial_row_cache_seed.py` resolve its dependency without adding the repository root to `sys.path`, while preserving the approved per-test `setUp` semantics and stable-ID partition. Record the exact command and green output.

## Important

6. Standalone post-publication rollback: `write_atomic_lf` must restore prior bytes when any post-publish snapshot/final validation fails; design-capability publication may not report failure while leaving new content committed.

7. POSIX absent-destination success: do not unlink a nonexistent recovery when publishing a new file. Add a fresh-destination POSIX regression.

8. Atomic visibility: the destination pathname must not have an observable missing-file window. Use a true same-directory atomic replacement strategy while retaining verified rollback/CAS behavior on Windows and POSIX. Add a seam asserting the target remains visible.

9. Attribute lifetime: perform a final `.gitattributes` validation while recovery is still available; a mutation after the action's last callback must reject and restore.

10. Git executable integrity: on POSIX execute an immutable/sealed snapshot so in-place mutation cannot run changed bytes before detection. On Windows bind/revalidate the ancestor directory chain through process creation or independently verify the created process image, and test an ancestor swap at the launch boundary.

11. Approval-generator usefulness: replace broad dynamic-helper false blockers with sink-first helper summaries, classify the exact scientific registry into action/return contracts, and link literal Python `-c` child capabilities to their parent subprocess row. Silent omissions remain forbidden; genuine unresolved behavior remains an explicit blocker.

12. Platform expectations: exact-evaluate supported class- and method-level `skipIf`/`skipUnless` AST forms, including negation; reject unrecognized conditional decorators. Lock the POSIX-only stabilization test and all five class-level Windows methods.

13. Lifecycle ambiguity: reject duplicate local setup/teardown definitions, inherited or mixin fixtures, and unowned module fixtures. Add duplicate and inheritance regressions.

14. Schema strictness and vector coherence (`tools/test_orchestration/model.py`, `tools/test_orchestration/configuration.py`): phases are exactly `setup`, `body`, or `probe`; enforce role-specific capability actions, return contracts, cwd/root labels, and constraint keys. Reconcile aggregate historical vectors with item-level counts, phase, body-entry, and counters. Replace the invalid synthetic phase `source` in tests with a valid value.

15. Exclusions: `_item_universe` must branch on assignment versus full exclusion and include exclusions in deny-all derivation without indexing a missing assignment. Add schema-valid excluded-item coverage.

16. Test isolation: move the `.gitattributes` mutation test into a temporary repository so a crash cannot dirty the real worktree. Strengthen analyzer-output tests to lock expected rows, blocker reasons/counts, and useful approval derivation rather than ordering/subset checks alone.

## Already accepted strengths to preserve

- Exact baseline counts/digests, ownership partitions, overlays, v4/v6 negative semantics, the H32 per-test setup correction, and both declared unconditional skips.
- Canonical LF/BOM-free inventory/profile documents, zero-scope preapproval refusal, two-token receipts, explicit deny-all rows, absolute measured `PONTIUS_GIT`, framed Git-object verification, secure configuration reads, and current identity checks.
- Previously fixed destination-CAS overwrite, ordinary pair rollback, external pair rollback, commit/tree/blob binding, Git pathname ABA protection, and final pair snapshot validation must not regress.

## Required verification

- Focused RED/GREEN tests for every amended behavior.
- Fresh D:-local snapshot runs of `tests/test_inventory_and_profiles.py` and `tests/test_test_orchestration_configuration.py`.
- The exact H32 `-B -P` gate.
- `tools/generate_test_inventory.py --check` with absolute `PONTIUS_GIT`.
- `git diff --check`, hash/status evidence, and no payload test execution or repository capability write.
