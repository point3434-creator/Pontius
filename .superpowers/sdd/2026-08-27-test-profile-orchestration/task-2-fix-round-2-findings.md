# Task 2 fix round 2 — scoped rereview findings

Read `task-2-brief.md`, `task-2-fix-round-1-findings.md`, and `task-2-report.md` first. Work only in `D:/Pontius-worktrees/orch-task2`. Use TDD, do not spawn subagents, do not run payload tests, and do not write/approve capability rows. Preserve every fix the rereviews marked addressed. Append exact RED/GREEN commands, outputs, hashes, and self-review to `task-2-report.md`; leave the worktree uncommitted for scoped rereview.

## Transactional governance publication

1. Move recovery ownership above the platform writer. A platform publish operation must return a live transaction/lease that can atomically rollback or finalize; it must not delete/arm/finalize recovery before `_with_governance_attribute_lease`, Git identity checks, source lifetime checks, and final output validations all succeed. There must be no fallible validation after the one combined final check and transaction finalization.

2. Late failure for an initially absent target must remove the newly published file when its identity still equals the transaction's published identity. Rollback must not depend on `displaced=True`. Add absent standalone regressions for post-publish source drift, final attribute drift, and recovery-acquisition failure; assert destination absence and zero artifacts.

3. Pair publication must retain both transactions until a combined final loop proves: source snapshot unchanged, attributes/Git unchanged, both exact new output snapshots unchanged, then source/attributes/Git unchanged again. Any mutation during either output revalidation must rollback both outputs. Add mutation during the second final output snapshot and final outer attribute drift; assert both originals restored (or both absent) and zero artifacts.

4. Remove Windows absolute-path `ReplaceFileW` publication and its recovery-open-after-publish window. Publish/recover through retained, non-delete-share directory and file handles with handle-relative replacement/link/rename primitives; keep the staged identity bound through the atomic operation. Add deterministic staging-byte swap, parent-directory swap, and recovery-acquisition failure seams. No unverified bytes may become observable, no substituted directory may receive publication, and every failure must restore/absent the destination with zero artifacts.

5. Preserve addressed behavior: delete-pending recovery cancellation before restore, ordinary POSIX absent publication, continuous existing-target visibility, CAS refusal of concurrent destination edits, body+cleanup error aggregation, pair rollback, and Windows ancestor-bound Git launch.

## Immutable Git execution

6. Keep sealed Linux `memfd` execution. Remove the unsealed named-temp/unlinked-descriptor fallback: if the host cannot create and verify a genuinely immutable executable snapshot, fail closed before launch. A merely chmod/read-only/unlinked inode is insufficient against a retained writable descriptor. Add a forced-no-memfd regression proving zero execution and a stable error; retain digest/seal checks.

## Analyzer completeness and bounds

7. Analyze executable local-class definition bodies, nested named callbacks, and supported callback positions; unresolved callable aliases/callbacks and mixed protected receivers must emit explicit blockers rather than zero rows/zero blockers. Add exact reproductions for local-class definition-time subprocess, nested named callback, and mixed CuPy receiver.

8. Model environment mutation in lexical source order and per subprocess call. A `pop` followed by assignment is an addition, assignment followed by `pop` is a removal, and omitted/inherit versus replacement mappings remain distinct. Lock both orderings and multiple calls in one scope.

9. Generalize runtime upper bounds through compound statements (`with`, `try`/handlers/finally, async forms where parsed), nested loops/comprehensions, helper calls, callbacks, subprocess calls, and literal child `-c` programs. Multiply helper/child rows by caller cardinality, take branch maxima, and block dynamic repetition. Add five-iteration oracles for nested-with, helper, and child-program calls. Preserve the controller-ruled canonical-affine bound of 6.

10. Keep sink-first helper closure and parent/child `-c` linkage, but give every exact scientific registry entry its declared action and return contract rather than collapsing all to `opaque`. Lock registry-specific rows/digests. Genuine Task 12 blockers may remain; silent omissions and false generic classifications may not.

## Discovery and schema exactness

11. Exact-evaluate supported class/method `unittest.skipIf`/`skipUnless` forms including logical negation. Conditional decorator aliases (`u.skipIf`, imported `skipIf`, or any unrecognized callable form) must reject/block explicitly, never silently default to both platforms. Add negation and alias tests while preserving current exact POSIX/Windows rows.

12. Reject duplicate per-test `setUp` and `tearDown` definitions in addition to already rejected module/class fixtures. Analyze only unambiguous unittest-executable fixture definitions. Add duplicate setup and teardown regressions.

13. Enforce role-specific capability combinations, not independent global enums. Subprocess executable role/slot/constraints/expected-return combinations and call kind/action/return-contract combinations must match exact declared registries. Explicitly reject owner + `device_array`, CUDA allocation + `opaque`, and Git + `spawned`; add valid neighboring combinations to prevent over-rejection.

## Required verification

- Focused RED/GREEN tests for every item above, including native Windows writer seams and forced POSIX no-exchange/no-memfd paths where applicable.
- Fresh D:-local snapshots of 44+ inventory tests (count may increase), 53+ configuration tests, and the exact H32 gate.
- Ordinary zero-scope `--write` then `--check`, byte stability, `git diff --check`, static formatting/hash/status checks, and zero residual temp/recovery artifacts.
- No payload execution, capability approval/write, commit, merge, or OneDrive write.
