# SDD ledger — plan: C:/Users/point/OneDrive/Documents/ChatGPT/Pontius/docs/superpowers/plans/2026-08-27-evidence-integrity-and-authorization.md

## Setup

- Worktree: `C:/Users/point/AppData/Local/Temp/pontius-evidence-test-stabilization`
- Branch: `codex/evidence-test-stabilization`
- Merge base: `a842c4b6a73a2991a63a481f4107580b72750582`
- Approved spec: `C:/Users/point/OneDrive/Documents/ChatGPT/Pontius/docs/superpowers/specs/2026-08-27-evidence-test-stabilization-design.md`
- Ruling: The legacy one-process full suite is not a valid setup baseline — the approved spec identifies phase conflicts and import contamination — each task establishes its baseline through the prescribed disposable-snapshot RED/GREEN checks — cost if wrong: a pre-existing unrelated failure may surface later during the canonical matrix instead of before Task 1.
- Ruling: Use the explicitly approved temporary linked worktree because the primary checkout is `master`, project-local worktree directories are not ignored, and committing a `.gitignore` change was not authorized — cost if wrong: the temporary worktree must be retained until branch integration is decided.

## Preflight

| Scope | Producer / consumer or self-check | Finding |
| --- | --- | --- |
| Task 1 | errors/models/tests | Consistent; public subpackage initializer stays separate from protected package initializer. |
| Task 2 | pure manifest parsers/tests | Consistent; filesystem I/O remains deferred to Task 4. |
| Task 3 | deterministic generator/manifests/tests | Consistent; exact user seed approval remains a hard gate. |
| Task 4 | secure filesystem/Git adapters/loaders | Consistent; tests cover declared fail-closed behavior. |
| Task 5 | typed authorization reader/tests | Consistent; one-read state machine replaces the legacy `KeyError`. |
| Task 6 | retained assessor/tests | Consistent; verifies identities before semantics and invokes no owner. |
| Task 7 | retained semantic hardening | Consistent; preserves generated manifest and negative-only API. |
| Task 8 | AST/diff boundary enforcement | Consistent; checks are read-only. |
| Task 9 | evidence verification/reviews | Consistent; release tools and interpreter slots remain explicit gates. |
| 1 → 2 | models/errors → parsers | Compatible. |
| 1 → 4 | identity/Git models → adapters | Compatible. |
| 1 → 5 | authorization state/errors → reader | Compatible. |
| 1 → 6 | retained models → assessor | Compatible. |
| 1 → 7 | assessment model → semantic hardening | Compatible; public shape unchanged. |
| 1 → 8 | evidence modules → boundary test | Compatible with import allowlist. |
| 1 → 9 | focused tests → final evidence suite | Included. |
| 2 → 3 | schemas/canonicalization → generator | Compatible through conformance vectors without production import. |
| 2 → 4 | pure parsers → secure path loaders | Compatible. |
| 2 → 5 | test support → authorization tests | Compatible with file-local `-B -P` loading. |
| 2 → 6 | manifests/test support → assessor | Compatible. |
| 2 → 7 | retained manifest/model → hardening | Compatible. |
| 2 → 8 | manifest module → boundary test | Compatible. |
| 2 → 9 | manifest tests → final suite | Included. |
| 3 → 4 | reader behavior/manifests → adapters | Compatible; Task 4 strengthens shared conformance. |
| 3 → 6 | generated manifests → assessor | Compatible; assessor verifies without modification. |
| 3 → 7 | retained manifest lock → hardening | Compatible; byte identity preserved. |
| 3 → 8 | generator/tests → boundary enforcement | Compatible. |
| 3 → 9 | manifests/`--check` → gate | Included. |
| 4 → 5 | filesystem/Git protocols → reader | Compatible; dependencies remain injected. |
| 4 → 6 | secure loaders/adapters → assessor | Compatible. |
| 4 → 8 | adapters/loaders → boundary test | Compatible. |
| 4 → 9 | adapter tests → gate | Included. |
| 5 → 6 | test support extension → assessor tests | Compatible. |
| 5 → 8 | authorization module → boundary test | Compatible. |
| 5 → 9 | authorization regression → gate | Included. |
| 6 → 7 | assessor/pure seam → hardening | Compatible; public signature preserved. |
| 6 → 8 | assessor → boundary test | Compatible with journal-only seam. |
| 6 → 9 | assessment evidence → gate | Included. |
| 7 → 8 | hardened assessor → boundary test | Compatible. |
| 7 → 9 | repeatable negative assessment → gate | Included. |
| 8 → 9 | boundary checks → review gate | Included. |

Preflight verdict: PASS; no evidence-plan contradiction found.

- Ruling: Use an ignored copied development venv inside the isolated temporary worktree because the original OneDrive venv executable carries `ReparsePoint`; retain exact CPython 3.14.6 and declared dependencies, but do not install Pontius into site-packages — cost if wrong: environment fingerprints differ from the user's original venv and require explicit accounting at the final interpreter gate.
- Ruling: Task 3 locks the generator's tool-local secure-reader contract and reusable factory seam; Task 4 adds the not-yet-existing active reader as the second conformance factory — cost if wrong: drift could remain temporarily undetected until Task 4 completes, but creating the active adapter early would violate the approved dependency order.
- Ruling: Do not normalize the Git-clean protected v9 authorization file in the development worktree even though system `core.autocrlf=true` changed its checked-out byte identity (494 bytes versus the approved 482); Task 3a seed emission is bound to a scrubbed disposable snapshot that independently passed all six present identities and eighteen absences, while direct worktree use must fail closed — cost if wrong: routine Windows checkout use remains blocked until line-ending materialization is addressed without mutating governed bytes.

## Tasks

- Task 1: fix round 1/5 (2 addressed, 0 open — package export narrowed; cause-preservation requirement correctly scoped to real translation sites; commits bbf98f8..54de860)
- Task 1: complete (commits a842c4b..54de860, review clean)
- Task 1 cleanup: all seven reported disposable snapshot roots were identity/prefix validated and removed from the OS temporary directory; the development worktree remains intact.
- Task 2: fix round 1/5 (initial all-schema malformed-input coverage finding remained partially open after representative cases; commits 135f8e3..bf8d7f4)
- Task 2: fix round 2/5 (all applicable wrong-type, boolean, digest/Git-ID, path-form, and count-disagreement cases covered; commits bf8d7f4..4da92eb)
- Task 2: complete (commits 54de860..4da92eb, review clean)
- Task 2 cleanup: all four remaining fix-round disposable snapshot roots were identity/prefix validated and removed from the OS temporary directory; the development worktree remains intact.
- Task 3a: fix round 1/5 (4 addressed, 1 open — exact selected-class closure, bounded Git, full parser/reader oracles, and ~10x runtime improvement landed; lexical fixed-`-c` resolution remained; commits c24fd4f..49f6b81)
- Task 3a: fix round 2/5 (0 fully addressed, 1 open — lexical program/argv resolution improved, but a symbolic f-string import-target sentinel bypass remained; commits 49f6b81..4b72588)
- Task 3a: fix round 3/5 (0 fully addressed, 1 open — direct symbolic targets were rejected, but keyword/auxiliary `import_module` and `__import__` arguments remained unmodeled; commits 4b72588..9041ba5)
- Task 3a: fix round 4/5 (1 addressed, 0 open — fresh-agent contract-level signature binding now covers relative/package/fromlist/level/taint semantics and rejects wildcard fromlists fail-closed; commits 9041ba5..e0d29dd)
- Task 3a: complete (commits 4da92eb..e0d29dd, preapproval review clean; hard seed approval still pending)
- Task 3a approval candidate: 167 ordered unique rows; normalized digest `812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89`; artifact SHA-256 `92e538f7d88ec7bb632d380525b61c0a5c35630f37f4aeb6a55ee4b051bd55c2`; 44,301 bytes; artifact `C:/Users/point/AppData/Local/Temp/pontius-task3-seed-review-fix4-766f4d73bb4143e1afa7ae87d2068757.txt`.
- Task 3a cleanup: six identity/prefix-validated disposable snapshot/Git-home roots and four rejected regenerable seed-review files were permanently removed from the OS temporary directory; the final fix4 candidate artifact was retained.
- Task 3 hard gate: APPROVED by the user on 2026-08-27 for exactly the retained 44,301-byte artifact above, its 167 ordered rows, normalized digest `812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89`, and artifact SHA-256 `92e538f7d88ec7bb632d380525b61c0a5c35630f37f4aeb6a55ee4b051bd55c2`; no other table or digest is authorized.
- Task 3b: in progress — exact ordered-row/count/digest oracle, canonical-snapshot guarded write, generated diff inspection, and post-write verification; base `e0d29dd86bafcea21dbd99336914ee5197572af4`
- Task 3b ruling: the first exact approved `--write` invocation failed closed before creating any directory, temp file, or manifest because `_verified_destinations()` incorrectly required the new `docs/architecture` directory to preexist; the approval token remains valid because zero governed state changed. Permit a narrow TDD destination-bootstrap fix and one retry only after byte-for-byte re-emission of the approved seed; any row/digest change requires renewed user approval.
- Task 3b: fix round 1/5 (1 addressed, 2 open — real CLI bootstrap fixed; Windows post-check path mutations and staging-failure temp leakage remained; commits c4d158e..ba1e665; no reapproval impact)
- Task 3b: fix round 2/5 (1 addressed, 1 open — immediate candidate ownership and handle-relative Windows mutation landed; exclusive staging, close/error lifecycle, and malformed native-status coverage remained; commits ba1e665..a16d1ac; no reapproval impact)
- Task 3b: fix round 3/5 (1 addressed, 2 open — exclusive raw-handle staging landed; retry-safe cleanup ownership and independent native fault coverage remained; commits a16d1ac..75caae4; no reapproval impact)
- Task 3b: fix round 4/5 (2 addressed, 0 open — fresh `gpt-5.6-sol`/ultra implementation made native cleanup ownership retry-safe and locked every native boundary with an independent one-variable fault matrix; commits `75caae4..89303d1`; no reapproval impact)
- Task 3b: complete (commits `e0d29dd..89303d1`, review clean; four approved manifests remain byte-identical, with the historical 167-row digest still `812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89`)
- Task 3 cleanup: all 37 remaining identity/prefix-validated disposable snapshot and Git-home roots were permanently removed from the OS temporary directory; the isolated development worktree and exact user-approved seed artifact were retained.
- Task 4: pending
- Task 5: pending
- Task 6: pending
- Task 7: pending
- Task 8: pending
- Task 9: pending
