# Task 2 implementation and fix-round-1 report

Date: 2026-08-28 (America/New_York)

## Scope and state

- Implementation worktree: `D:/Pontius-worktrees/orch-task2`
- Branch: `codex/orch-task2`
- Base / current HEAD: `a2659766319900793d835c9abac8bb0f3cf173ba`
- Python: `D:/Pontius-worktrees/evidence-test-stabilization/.venv/Scripts/python.exe`
- Git: `C:/Program Files/Git/cmd/git.exe`
- Test policy: every Python test payload ran only from a fresh disposable,
  canonical-LF D:-local snapshot with `-B -P`, `cwd=H`,
  `PYTHONPATH=H/src`, and the exact `PONTIUS_GIT` above.
- No production test payload, profile execution, capability approval, design-capability
  write, merge, cherry-pick, push, or primary-checkout write was performed.
- Ordinary inventory/profile regeneration was authorized and remains zero-scope.
- The work is intentionally uncommitted pending the independent rereview.

## Implemented contract

1. Materialized the exact baseline inventory, working discovery, four ownership
   partitions, historical subgroups, two declared unconditional skips, lifecycle
   fixture ownership, interpreter/profile/payload declarations, retained-v7 overlays,
   and canonical LF governance files.
2. Converted `H32PreBetInitialRowCacheSeedTests.setUpClass` to per-test `setUp` and
   added an exact-path loader that works under `-P` without adding the repository root
   to `sys.path`. The locked 51 GPU and 2,129 current baseline partitions are unchanged.
3. Hardened configuration reads against supplied-leaf and ancestor link/reparse races,
   path/handle drift, same-size replacement, oversize growth, and close-error masking.
   Supported Microsoft cloud tags retain exact attribute/tag binding and one narrowly
   bounded ctime-only hydration retry. The Git executable remains strict any-reparse.
4. Corrected equal major/minor interpreter version pairs by using `unique=False` only
   for two-component version tuples.
5. Implemented raw, independently framed SHA-1 Git commit/tree/blob acquisition;
   bounded process input/output/time; exact tree parsing; executable identity leases;
   Windows ancestor handle retention through process creation; and POSIX execution
   from a sealed memfd or unlinked immutable descriptor snapshot.
6. Implemented canonical inventory/profile generation, ordinary check/write
   preservation, two-token design review emission and design-only write support,
   persisted receipt binding, explicit deny-all coverage, and strict zero-scope refusal.
   The real repository was never invoked with capability approval tokens.
7. Implemented same-directory governance publication with destination/source lifetime
   revalidation, CAS checks, retained recovery until final validation, failure rollback,
   body/cleanup error aggregation, and pair consistency. Existing Windows destinations
   use `ReplaceFileW`; absent Windows destinations use a no-replace handle-relative
   rename. POSIX uses `renameat2(RENAME_EXCHANGE)` when available and otherwise a
   verified same-directory recovery hardlink plus atomic `os.replace`; absent POSIX
   destinations use a no-replace link/unlink publication.
8. Implemented exact AST ownership and capability review: platform decorators,
   lifecycle ambiguity rejection, invoked local/lambda/callback closure handling,
   helper registry and exact argument binding, subprocess keyword/environment
   semantics, literal `-c` child linkage, exact protected-call registries, CuPy
   query/allocation contracts, path-sensitive bounded repetition, branch maxima,
   explicit blockers, registered probes, fixture/probe deny-all, and source closure.
9. Enforced the exact historical phase enum (`setup`, `body`, `probe`), capability
   field enums and role constraints, exclusion semantics, and aggregate/item vector
   coherence.
10. Moved the `.gitattributes` mutation regression to an OS-temporary repository and
    locked LF/BOM/final-LF behavior for all governance outputs.

The controller ruled that the canonical-affine loop maximum is 6, not the stale
review prose's 10: the statically returned tuple contains three automata and each
iteration performs two `cupy.asnumpy` calls.

## Exact generated state

Baseline discovery:

- test files: 392
- stable IDs: 2,367
- stable-ID digest:
  `c8e6465527a9b784f4be41947745f6e86d53f45d16fd0d10955009bbb127b37b`
- historical: 137,
  `77ccf22ac1f52ebbeff7311bf2c4c1fb4f83671a5cfe10f84dbbde655ecb58a8`
- GPU: 51,
  `896fb0675371186476df33b13eb7a5d9286dfeb01f53d37daa0f458e72021005`
- core: 50,
  `38166290ad900c24a08c93f08de3376dac92a2c35544a94c3228726b01a02dfc`
- current: 2,129,
  `c32575a47a889e7e324db2abb56ef5c5b37295bb6a5cc3e6006cb04c767c6803`

Working discovery:

- test files: 399
- stable IDs: 2,594
- stable-ID digest:
  `ee6063ea0e1243add287ac286b6b7bda34d2c833fb0db603b8e2e72bc64772fb`
- introduced IDs: 227
- introduced-ID digest:
  `7bbefcf6948462fc9e33769d2e059740462d1ed8479f496fd241fa397f67c784`
- materialized assignments: historical 137, GPU 51, core 50, current 2,356

Design-review census:

- expanded rows: 121
- derived design-row digest:
  `abf4081eea980a203b1641f6692bf0258ed39a73440cb621e7dfdeed44cba6c6`
- explicit unresolved blockers: 95
  - unsupported `capture_output`: 44
  - dynamic helper arguments: 29
  - explicitly out-of-scope CuPy action/view: 11
  - dynamically repeated call with no finite static bound: 5
  - unsupported `stdin`: 5
  - absent future registered GPU probe implementation: 1
- subprocess sites: 42 direct plus 4 reachable helper sites
- cross-file `setUpClass` edges: 27
- CuPy AST nodes: 28
- analyzed-site digest:
  `2d49993a8e19d30707681943505eccad4c2fa8cf270e27d7aaa2e40ccb81db6c`
- string-only sink decoys: 79 = 17 design production + 6 historical
  production + 26 prior stabilization synthetic + 30 Task 2 synthetic
- string-decoy digest:
  `6c2f618b0bf826fd289e341562a38c1985b4dae0841109b89d3dec5ca136aa08`

Checked-in capability state is intentionally absent:

- subprocess definitions: 0
- call definitions: 0
- bindings: 0
- `spec_capabilities_sha256`: 64 zeroes
- `capability_bindings_sha256`: 64 zeroes
- every direct and full profile selection refuses before execution

## TDD evidence

### CodeRabbit reader/version regressions

- RED snapshot:
  `pontius-orch2-coderabbit-red-9423616400ce4f958f35c946d2d4d7e6`.
  The supplied junction/reparse path was accepted and equal version pair rejected.
- GREEN snapshot:
  `pontius-orch2-coderabbit-green2-b9b5195a7abc41aab0993295552b09b4`.
  39/39 focused tests passed after no-follow reader acquisition and narrow
  `unique=False` normalization.

### H32 exact loader and per-test ownership

- RED command: snapshot harness label `fix1-h32-red`, file
  `test_h32_pre_bet_initial_row_cache_seed.py`, expected exit 1.
- RED snapshot:
  `pontius-orch-task2-fix1-h32-red-e07884a48953425db9de0d00851ab3b9`.
  It failed with `ModuleNotFoundError: No module named 'tests'` under the mandated
  `-P` policy.
- First GREEN snapshot:
  `pontius-orch-task2-fix1-h32-green2-22ccff33f08f4497b737c69ecfcefac6`.
  9 methods passed with the exact one approved unconditional skip.
- Final GREEN command:
  `task-2-run-snapshot.ps1 -Label fix1-h32-green-final`
  `-TestFile test_h32_pre_bet_initial_row_cache_seed.py -ExpectedExit 0`.
- Final snapshot:
  `pontius-orch-task2-fix1-h32-green-final-d34f82e2c40b490ba7d0909662e748ee`.
  Result: 9 run, 8 passed, exactly 1 approved skip, exit 0, snapshot cleaned.

### Schema/configuration strictness

- RED snapshot:
  `pontius-orch-task2-fix1-schema-red2-db59ba57c508423ea4dc27e493a918b4`.
  Result: 53 run, exactly 7 expected failures for permissive phase/action/contract/
  cwd/root acceptance.
- First GREEN snapshot:
  `pontius-orch-task2-fix1-schema-green2-37f499e348de48c8898500cbd9303ca2`.
  Result: 53/53 passed.
- Final GREEN command:
  `task-2-run-snapshot.ps1 -Label fix1-config-green-final`
  `-TestFile test_test_orchestration_configuration.py -ExpectedExit 0`.
- Final snapshot:
  `pontius-orch-task2-fix1-config-green-final-ccc1d64def4244458e91d01ebf1c1e9d`.
  Result: 53/53 passed, exit 0, snapshot cleaned.

### Analyzer, Git, and governance publication

- Combined contract RED snapshot:
  `pontius-orch-task2-fix1-contract-red-3f3ea288ef444bb0b8a94df8e5475640`.
  Result: 44 run, 12 failures and 2 errors reproducing fix-round findings.
- Writer checkpoint:
  `pontius-orch-task2-fix1-writer-attempt7-edce3f7c0c4c478a8cab8930ca45a67c`.
  All writer regressions passed; only two stale generated-oracle assertions remained.
- Git/POSIX checkpoint:
  `pontius-orch-task2-fix1-git-posix-attempt2-a156b30bbbc04efd87122f98ecae381b`.
  All Git-launch and writer contracts passed; only two stale generated-oracle
  assertions remained.
- Focused RED snapshot:
  `pontius-orch-task2-fix1-focused-green1-32c165a6695546a0a072b2ab7f760214`.
  Result: 44 run, four test/oracle failures; default CLI check passed.
- Focused RED snapshot:
  `pontius-orch-task2-fix1-focused-green2-0f3fab4d7a5d4d928b31649e4f9b5289`.
  Result: 44 run, one failure and one error. The failure proved an obsolete
  authorization expectation for a `capture_output` subprocess; the error exposed
  lost enclosing-class context in an invoked local helper.
- Focused RED snapshot:
  `pontius-orch-task2-fix1-focused-green3-819fcc25d9c94415b60869deee90ca50`.
  Result: 44 run, one error. The local helper sensitivity prepass still discarded
  its lexical class context.
- Final GREEN command:
  `task-2-run-snapshot.ps1 -Label fix1-focused-green4`
  `-TestFile test_inventory_and_profiles.py -ExpectedExit 0`.
- Final snapshot:
  `pontius-orch-task2-fix1-focused-green4-88d767b7852f48679f7b25d492019e48`.
  Result: 44/44 passed, exit 0, snapshot cleaned.

The final scoped total is 106 test methods: 105 passed and exactly one approved
unconditional skip. No other runtime-conditioned skip exists in Task 2 tests.

## Generator/write verification

Exact environment:

```text
PYTHONPATH=D:/Pontius-worktrees/orch-task2/src
PONTIUS_GIT=C:/Program Files/Git/cmd/git.exe
python -B -P tools/generate_test_inventory.py --write
python -B -P tools/generate_test_inventory.py --check
```

Fresh result on 2026-08-28:

- write exit: 0
- check exit: 0
- inventory before/after SHA-256:
  `4bb3d6d85b901dae7c27da1bee7766cd6c499d41d93e24179cfd348e6cca4749`
- profiles before/after SHA-256:
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`
- both outputs were byte-identical across the ordinary pair transaction
- no capability approval token or design-capability write command was used

The final focused snapshot independently exercised default `main([])` as a read-only
successful check and verified that neither governance file changed.

## Real OneDrive secure-read diagnostic

Candidate code from the D: Task 2 worktree read this actual repository file without
importing it:

`C:/Users/point/OneDrive/Documents/ChatGPT/Pontius/tests/test_cfr.py`

Result:

- bytes: 13,201
- SHA-256:
  `41e6dc19d9dfb9bd81998947e079ff1bf814874b3c289412bca25ae7dd936b70`
- exact Git blob OID: `960f17bacf330d522de9b8e85aaca15ef70b90db`
- candidate bytes equal exact `git cat-file blob` bytes: yes
- bounded-reader invocations: 2
- ctime-only hydration retries: exactly 1
- final snapshot and ancestor revalidation: passed
- full pre/post identity: unchanged
- path and opened-handle attributes after hydration: `0x20`, reparse tag `0x0`

The primary repository currently contains no file or directory with a reparse tag
(a read-only scan excluding `.git`, `.venv`, and caches returned zero). Therefore the
real repository exercised the approved one-retry hydration behavior but did not offer
a live supported-cloud-tag specimen. Exact supported tags, name-surrogate/unknown/tag-
only refusal, path/handle tag drift, and second-transition refusal are covered by the
unskippable 53-test configuration suite; live cloud-tag acceptance remains Partial.

## Static review and hashes

- `git diff --check`: exit 0. Git emitted only the expected `core.autocrlf=true`
  advisory for four tracked Python files; there were no whitespace errors.
- Added Python lines over 100 columns: 0.
- BOM, missing-final-LF, or trailing-whitespace errors across all eight files: 0.
- CR bytes in the two generated governance files: 0.
- Governance files are exact LF and their `.gitattributes` rules are test-locked.
- Source scan found no TODO/FIXME/unimplemented Task 2 capability-writer placeholder.

Final eight-file SHA-256 values:

- `tools/generate_test_inventory.py`:
  `9bd616f18d42de249c160cb2a548fe96f8fbe2f375cb92df158372dd67322693`
- `tests/test_inventory_and_profiles.py`:
  `1fb2a6f72cb0b29c65c28a1437c6d65439de446ae2f77b0c5b102c4d9b416086`
- `tests/test-inventory.json`:
  `4bb3d6d85b901dae7c27da1bee7766cd6c499d41d93e24179cfd348e6cca4749`
- `tests/test-profiles.toml`:
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`
- `tools/test_orchestration/configuration.py`:
  `a1cef160d600b2fe35b67e0931c5227552fc03068be376097f2d6e102780c0d8`
- `tools/test_orchestration/model.py`:
  `500e82ea15bade4d376bfd9d66df7d0bdd0d28a2ecb66d3fed3df943234ae883`
- `tests/test_test_orchestration_configuration.py`:
  `07aa7292e6f9ef4706295879f6a4cbb8e526d0c6331a2d6df7e54195a17878d5`
- `tests/test_h32_pre_bet_initial_row_cache_seed.py`:
  `51305e9f421a5c356e43a0d474393cec05b7431a02a0540603774f7c802d796b`

Worktree status is exactly four modified tracked files and four untracked generated/
test files listed above. No unrelated file changed.

## Self-review and remaining concerns

- Re-read the binding fix-round findings and mapped all 16 findings to focused tests
  in the 44-test inventory suite or 53-test configuration suite. The controller's
  explicit 6-call canonical-affine ruling is locked literally and derived from source.
- Verified that local nested helper analysis retains lexical class context, while
  unsupported `capture_output` remains an explicit blocker rather than a silently
  emitted capability.
- Verified that writer recovery remains available through stage-aware source,
  destination, and `.gitattributes` validation, and that existing/absent Windows and
  POSIX paths have no intentional missing-name publication window.
- Verified that the Git lease separates strict executable reparse policy from the
  cloud-compatible configuration-data policy.
- Real design approval remains intentionally impossible today because 95 reviewed
  blockers remain. Task 12 must resolve/classify them and obtain the user's exact
  capability-table and receipt approval.
- Live supported-cloud-tag reading is Partial because no tagged repository path was
  present. Mocked Windows tag/handle contracts are unskippable and green.
- Full repository payload execution was deliberately not performed. This is a scope
  constraint, not a green claim; later orchestration tasks own guarded execution.
- Independent frozen rereview is still required before commit. The worktree remains
  uncommitted and no release-readiness claim is made here.

# Task 2 fix round 2 final evidence — 2026-08-28

## Scope and resulting design

Fix round 2 was performed only in `D:/Pontius-worktrees/orch-task2` against
`a2659766319900793d835c9abac8bb0f3cf173ba`. No payload suite, capability review
emit, capability approval/write, OneDrive operation, commit, merge, or push was
performed.

The round closes the two frozen rereview clusters and preserves the accepted Task 2
contracts:

1. Governance publication now returns outer-owned standalone/pair transactions.
   Source, Git, attribute, and both output identities remain bound through the final
   combined validation. Existing and absent destinations rollback without clobbering
   concurrent state. Windows publication is handle-relative; POSIX has exchange and
   identity-checked no-exchange paths.
2. A recovery disposal is the explicit irreversible commit point. Every reportable
   cleanup precedes disposal. Pre-disposal failures preserve the primary failure and
   rollback evidence; recovery/directory handle cleanup after disposal is attempted
   once through a non-reporting best-effort seam. No post-commit rollback or
   double-close is attempted.
3. Git execution requires a sealed executable image on POSIX and fails before launch
   without `memfd` sealing. Windows launch holds and revalidates the executable leaf
   and ancestor identities.
4. The analyzer now covers executable local-class bodies, invoked callbacks and
   helpers, exact lexical environment mutation, compound-statement and helper/child
   cardinality, per-test fixtures, platform decorator aliases/negation, and explicit
   dynamic/mixed-receiver blockers.
5. Scientific capabilities use the controller-approved explicit qualified-name to
   `(action, return_contract)` registry. There is no suffix inference and no generic
   `invoke`/`opaque` fallback.
6. Model validation enforces role-specific subprocess return combinations and exact
   call-kind/action/return-contract combinations.

## Strict TDD evidence

All test commands used the D:-local snapshot harness, its fresh canonical-LF clone,
`python -B -P`, cwd `H`, `PYTHONPATH=H/src`, and exact
`PONTIUS_GIT=C:/Program Files/Git/cmd/git.exe`.

### Analyzer, discovery, repetition, and schema RED/GREEN

- RED: `fix2-analyzer-red2-58543b4449e34a97837bd67d7b08d23e`.
  The 47-test inventory suite exposed the intended duplicate per-test fixture,
  negated decorator, executable local-class, nested compound-bound, callback/alias,
  and stale-governance failures (6 failures and 1 error at that checkpoint).
- GREEN checkpoint:
  `fix2-analyzer-green-attempt2-d6b736785714432c834e471932cb0bcf`.
  Every analyzer/discovery/writer regression passed; only two intentionally stale
  generated-governance assertions remained before regeneration.
- RED: `fix2-schema-red1-335b96796a394ff39648d3606d16d220`.
  The 53-test configuration suite produced 3 failures and 2 errors: invalid
  Git+spawned, owner+device-array, and CUDA-allocation+opaque combinations were
  accepted while neighboring valid scientific compile/contract rows were rejected.
- GREEN: `fix2-schema-green1-7670eb4cd1e440fabc606aac68c05228`.
  Result: 53/53 passed.
- RED: `fix2-git-nomemfd-red-c080610ebf524352a5fbec17ae4deb06`.
  The forced no-`memfd` seam proved that the old named temporary fallback remained
  executable.
- GREEN coverage is included in the analyzer and final 47-test snapshots: the same
  seam now fails closed before any executable runs.

### Exact real-corpus oracle

- Initial RED:
  `fix2-full-corpus-red1-3890413a323f4209870dac8b0d24a4c6`.
  Result: 46/47 passed; the old 121-row oracle rejected the correctly derived 139
  rows.
- Diagnostic:
  `fix2-corpus-diagnostic1-2ce5b6e26fde464d82963af230027a55`.
  It established the exact 139 expanded rows, 139 explicit blockers, and design-row
  digest listed below.
- GREEN:
  `fix2-full-corpus-green2-26a99cc870cb422ea3d371c04cb9ec30`.
  Result: 47/47 passed.

### Irreversible finalization RED/GREEN addendum

- RED command:
  `task-2-run-snapshot.ps1 -Label fix2-finalize-commit-red1`
  `-TestFile test_inventory_and_profiles.py -ExpectedExit 1`.
- RED snapshot:
  `pontius-orch-task2-fix2-finalize-commit-red1-a342531778914b2d832e8e67c4aa0e8a`.
  Result: 47 run. The native Windows late directory-close seam raised after deleting
  recovery, then attempted rollback and a second close, producing the intended
  incomplete-state/double-close `ExceptionGroup`; one separate generated census
  assertion was stale.
- Intermediate GREEN-code snapshot:
  `pontius-orch-task2-fix2-finalize-green-code2-9e425647ff5b4d7c8f9c1759e15a9e95`.
  The writer regression passed; the sole remaining failure was the expected stale
  line-bound string-census digest.
- Final GREEN command:
  `task-2-run-snapshot.ps1 -Label fix2-finalize-green-final`
  `-TestFile test_inventory_and_profiles.py -ExpectedExit 0`.
- Final snapshot:
  `pontius-orch-task2-fix2-finalize-green-final-1a4500c1e265412eb7c439206fb12d54`.
  Result: 47/47 passed, exit 0, snapshot cleaned. It proves exact old bytes and zero
  artifacts after a pre-disposal failure; exact new standalone/pair bytes, one close
  attempt, no rollback/double-close, and zero artifacts after post-disposal recovery
  or directory-close failures; plus the platform-neutral best-effort close seam.

### Final configuration and H32 gates

- Configuration command:
  `task-2-run-snapshot.ps1 -Label fix2-config-final2`
  `-TestFile test_test_orchestration_configuration.py -ExpectedExit 0`.
- Snapshot:
  `pontius-orch-task2-fix2-config-final2-c672ae8fe4dc43bbb377117b601d0788`.
  Result: 53/53 passed, exit 0, snapshot cleaned.
- H32 command:
  `task-2-run-snapshot.ps1 -Label fix2-h32-final2`
  `-TestFile test_h32_pre_bet_initial_row_cache_seed.py -ExpectedExit 0`.
- Snapshot:
  `pontius-orch-task2-fix2-h32-final2-0970ef9e6bfc4a1ea27f5a01142ef9dd`.
  Result: 9 run, 8 passed, exactly the one approved unconditional skip, exit 0,
  snapshot cleaned.

Final scoped total: 109 discovered test methods, 108 passed, and exactly 1 approved
unconditional skip.

## Exact generated and review-only state

Baseline locks remain unchanged:

- 392 test files and 2,367 stable IDs,
  `c8e6465527a9b784f4be41947745f6e86d53f45d16fd0d10955009bbb127b37b`
- historical 137,
  `77ccf22ac1f52ebbeff7311bf2c4c1fb4f83671a5cfe10f84dbbde655ecb58a8`
- GPU 51,
  `896fb0675371186476df33b13eb7a5d9286dfeb01f53d37daa0f458e72021005`
- core 50,
  `38166290ad900c24a08c93f08de3376dac92a2c35544a94c3228726b01a02dfc`
- current 2,129,
  `c32575a47a889e7e324db2abb56ef5c5b37295bb6a5cc3e6006cb04c767c6803`

Final working discovery:

- 399 test files
- 2,597 stable IDs,
  `d3d757b5158187b3d97c38270b8386f788171ccc854e86e932a26c653109607b`
- 230 introduced IDs,
  `dbe6d35114aef46b0c6d5427436552a4d240d3da252cb8cda6173c30dfaf0477`
- materialized assignments: historical 137, GPU 51, core 50, current 2,359

Final review-only derivation:

- expanded rows: 139
- design-row digest:
  `17f4532276989bd360cabafceeb3a3b4353c0764a4a61037639c933fdeb94194`
- explicit blockers: 139
  - unsupported `capture_output`: 44
  - exact helper arguments unresolved: 25
  - explicitly out-of-scope CuPy action/view: 11
  - dynamic direct-call repetition: 5
  - dynamic helper repetition: 8
  - mixed protected receiver: 31
  - unresolved callable alias: 9
  - unsupported `stdin`: 5
  - absent registered GPU probe implementation: 1
- subprocess census: 42 direct plus 4 reachable helper sites
- cross-file `setUpClass` edges: 27
- CuPy AST nodes: 28
- analyzed-site digest:
  `2d49993a8e19d30707681943505eccad4c2fa8cf270e27d7aaa2e40ccb81db6c`
- string-only sink decoys: 87 = 17 design production + 6 historical
  production + 26 prior stabilization synthetic + 38 Task 2 synthetic
- final line-bound string-decoy digest:
  `e9f760e02ed9dcdc17954538fc0015ef0024ec3edd299513f6fd28e011f813b6`

These 139 rows were derived for review completeness only. Checked-in subprocess
definitions, call definitions, and bindings are all absent; both capability digests
are exactly 64 zeroes. No approval table was emitted and no design-capability write
was invoked.

## Ordinary regeneration and byte stability

The D: worktree ordinary zero-scope command
`python -B -P tools/generate_test_inventory.py --write` completed with exit 0.
It used exact `PONTIUS_GIT` and did not approve either capability scope. The subsequent
`--check` completed with exit 0 and both outputs were byte-identical before/after:

- `tests/test-inventory.json`:
  `f4d902084001939f6dcb15aaa0e696d42a4f094a595115cdb2f1c4d7442bb170`
- `tests/test-profiles.toml`:
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`

## Final static, formatting, and artifact gates

- AST-only compilation parsed 898 Python files successfully without bytecode.
- Canonical-LF governance checks passed:
  - `docs/architecture/dependency-baseline.toml`: 373,157 bytes,
    `b86dd2ba20e4639bc6c0184367a82b01ef3b1960ce863406f30964dd5c8625c6`
  - `tests/test-inventory.json`: 1,574,306 bytes, hash above
  - `tests/test-profiles.toml`: 453,194 bytes, hash above
- Inventory entries: 2,597; declared unconditional skips: exactly 2.
- Capability definitions/bindings: `0/0/0`; both digests all-zero.
- New Python lines over 100 columns: 0.
- Tracked added Python lines over 100 columns: 0.
- BOMs: 0; missing final LF: 0; trailing-whitespace lines: 0 across all eight
  Task 2 files.
- The four generated/new files are LF-only. The four tracked Python files retain the
  repository's `core.autocrlf=true` CRLF worktree representation; the snapshot harness
  canonicalizes them to LF before testing.
- `git diff --check`: exit 0. Its only output was the expected four `autocrlf`
  advisories; there were no whitespace errors.
- Residual Task 2 `.tmp`, `.recovery`, or `.lock` artifacts: 0.

Final eight-file SHA-256 values:

- `tools/test_orchestration/model.py`:
  `83161fcb39c87008e6cf98f9f0d801abc99103484a2c40a799524e3e2cab0d32`
- `tools/test_orchestration/configuration.py`:
  `a1cef160d600b2fe35b67e0931c5227552fc03068be376097f2d6e102780c0d8`
- `tests/test_test_orchestration_configuration.py`:
  `ff0491e75d8143078305cc85ed47fae5e093e2ee85bf48a8eedff57c539929f2`
- `tools/generate_test_inventory.py`:
  `3d690f7bb83f622186cc03b6fa39a99c49bb6a1f944b69d014d23cb7a54e42fd`
- `tests/test-inventory.json`:
  `f4d902084001939f6dcb15aaa0e696d42a4f094a595115cdb2f1c4d7442bb170`
- `tests/test-profiles.toml`:
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`
- `tests/test_inventory_and_profiles.py`:
  `c5ee82fc121bf3f02588b5be81154ce95e8b67a1e2c76f36004ecfb2cf51d7bd`
- `tests/test_h32_pre_bet_initial_row_cache_seed.py`:
  `51305e9f421a5c356e43a0d474393cec05b7431a02a0540603774f7c802d796b`

Worktree status remains exactly four modified tracked files and four untracked Task 2
files:

```text
 M tests/test_h32_pre_bet_initial_row_cache_seed.py
 M tests/test_test_orchestration_configuration.py
 M tools/test_orchestration/configuration.py
 M tools/test_orchestration/model.py
?? tests/test-inventory.json
?? tests/test-profiles.toml
?? tests/test_inventory_and_profiles.py
?? tools/generate_test_inventory.py
```

## Final self-review and concerns

- Re-read the finalization flow after GREEN. Pre-commit cleanup failures still enter
  the normal rollback/aggregation path. After recovery disposal, state ownership is
  cleared before best-effort close, so no exception can trigger an impossible
  rollback or reuse a closed native handle.
- The exact 139-row/139-blocker real-tree census is complete and fail-closed. It is
  intentionally not approval-capable until Task 12 resolves the blockers and obtains
  exact user approval.
- The prior read-only OneDrive secure-reader result remains the live compatibility
  evidence. It was not rerun because fix round 2 explicitly prohibited touching
  OneDrive. Live supported-cloud-tag acceptance therefore remains Partial; its mocked
  handle/path contracts are unskippable and green.
- Full repository payload execution remains deliberately unverified in Task 2.
- Independent frozen rereview is required before any commit. The D: worktree is
  uncommitted.

## Task 2 fix round 3 — source-ordered analysis and cooperative writer transaction

Fix round 3 was performed only in `D:/Pontius-worktrees/orch-task2` against
`a2659766319900793d835c9abac8bb0f3cf173ba`. The complete binding brief, prior
round findings, and this report were read before implementation. No payload suite,
capability-review emission, capability approval/write, OneDrive operation, commit,
merge, or push was performed.

### Analyzer RED/GREEN evidence

- RED command: snapshot harness label `fix3-analyzer-red2`, file
  `test_inventory_and_profiles.py`, expected exit 1.
- RED snapshot:
  `pontius-orch-task2-fix3-analyzer-red2-23d185823fa14b8091e209828d866c03`.
  Result: 50 run, 10 failures and 4 errors, exit 1, snapshot cleaned. The intended
  failures reproduced sensitive reassignment/container aliases with zero rows,
  missing source-ordered environment update/delete state, incomplete match/handler
  and literal-child handling, and silently accepted module/class/getattr decorator
  aliases or unknown conditional decorators. Four already-supported exact alias
  forms stayed locked. Two checked-in inventory failures were expected from the
  three newly introduced test IDs.
- Exact GREEN checkpoint command: snapshot harness label
  `fix3-analyzer-exact-attempt2`, same test file, expected exit 1 while governance
  was intentionally stale.
- GREEN snapshot:
  `pontius-orch-task2-fix3-analyzer-exact-attempt2-bf70a5b2ea964d168a742a264757acc5`.
  Result: 50 run, 48 passed, with only the two expected stale-governance failures,
  exit 1, 19.519 seconds, snapshot cleaned.

The reviewed scope now uses one source-ordered forward resolver and structural
effect analysis. It resolves exact scalars, qualified names, helpers, objects,
fixed sequences/mappings, inherited environment state, and literal child programs;
branch joins preserve only structurally equal sensitive state. It derives finite
loop/match/helper/child bounds, snapshots subprocess environments at the call site,
and turns ambiguous protected values into explicit blockers. Decorator aliases and
reassignments use the same source-order rule and unknown possible conditionals fail
closed.

### Transaction RED/GREEN evidence

- Superseding combined RED command: snapshot harness label
  `fix3-transaction-red4`, file `test_inventory_and_profiles.py`, expected exit 1.
- RED snapshot:
  `pontius-orch-task2-fix3-transaction-red4-e296fddaf9254e4faa99697a320b6c33`.
  Result: 56 run, 16 failures and 0 errors, exit 1, 20.549 seconds, snapshot cleaned.
  Fourteen failures were the intended transaction gaps and two were stale governance.
  The REDs covered coordinator ordering, direct-pair second lifetime validation,
  deterministic cooperative-writer exclusion, reviewer-exact live staging/recovery/
  published-handle mutation attempts, fail-before-close ownership, and POSIX exchange
  and forced-no-exchange finalization faults.
- Intermediate GREEN command: snapshot harness label
  `fix3-transaction-green-attempt6`, same test file, expected exit 1 while governance
  remained stale.
- GREEN snapshot:
  `pontius-orch-task2-fix3-transaction-green-attempt6-f69bb628960b44faa2f674e942cd997c`.
  Result: 56 run, 54 passed, with exactly the two expected stale-governance failures,
  exit 1, 20.827 seconds, snapshot cleaned. No transaction failure remained.

One coordinator now owns the complete final lifetime -> every output -> lifetime ->
commit sequence and one rollback boundary. Direct standalone, direct pair, and outer
collector publication use that coordinator. A final-validation exception therefore
rolls back while every recovery and bound handle is still live.

On Windows, each destination has a deterministic cooperative Pontius-writer lock.
The parent, staging, recovery, and published objects retain role-specific handles;
staging/recovery/published objects deny conflicting writes. A second compliant writer
cannot pass the lock. The native limitation remains explicit: arbitrary same-user
namespace writers that ignore the Pontius lock are outside this supported boundary.

Native close state is now explicit. A close that fails while the handle is proven
open retains ownership and may be retried; a close that completed before an injected
exception is treated as post-commit and is never double-closed. POSIX finalization
retains rollback authority until recovery disposal succeeds on both exchange and
portable no-exchange paths.

### Ordinary zero-scope regeneration and final focused verification

Ordinary regeneration used exact `PONTIUS_GIT` and only:

```text
python -B -P tools/generate_test_inventory.py --write
python -B -P tools/generate_test_inventory.py --check
```

Both commands exited 0. A repeated final `--check` also exited 0 and left both files
byte-identical:

- `tests/test-inventory.json`:
  `101dcbccfdbfa5caa015d73473161af99ea69415f724923acae5ca2f39787a2d`
- `tests/test-profiles.toml`:
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`

No capability command was invoked. Checked-in subprocess definitions, call
definitions, and bindings remain exactly `0/0/0`; both capability digests remain
64 zeroes.

Fresh final snapshots:

- Inventory/finalization command: label `fix3-inv-green3`, expected exit 0.
  Snapshot
  `pontius-orch-task2-fix3-inv-green3-b06fc8c7306c47909bcbcdca679feac8`:
  56/56 passed, exit 0, 30.753 seconds, cleaned.
- Configuration command: label `fix3-config-green`, expected exit 0. Snapshot
  `pontius-orch-task2-fix3-config-green-637ccf263a9a43458402632f5b6bb756`:
  53/53 passed, exit 0, 0.450 seconds, cleaned.
- H32 command: label `fix3-h32-green`, expected exit 0. Snapshot
  `pontius-orch-task2-fix3-h32-green-8488a883699945a8a141169d7fb3842e`:
  9 run, 8 passed, exactly the one approved unconditional skip, exit 0,
  1.427 seconds, cleaned.

Final scoped total: 118 discovered test methods, 117 passed, and exactly 1 approved
unconditional skip.

### Exact generated and review-only state

The locked baseline remains unchanged at 392 test files and 2,367 stable IDs:

- all IDs:
  `c8e6465527a9b784f4be41947745f6e86d53f45d16fd0d10955009bbb127b37b`
- historical 137:
  `77ccf22ac1f52ebbeff7311bf2c4c1fb4f83671a5cfe10f84dbbde655ecb58a8`
- GPU 51:
  `896fb0675371186476df33b13eb7a5d9286dfeb01f53d37daa0f458e72021005`
- core 50:
  `38166290ad900c24a08c93f08de3376dac92a2c35544a94c3228726b01a02dfc`
- current 2,129:
  `c32575a47a889e7e324db2abb56ef5c5b37295bb6a5cc3e6006cb04c767c6803`

Final working discovery:

- 399 test files
- 2,606 stable IDs,
  `0ec4536d1aef78314e1b32a430aa3b011f149a452e1cc0d521289641bbe6d4e9`
- 239 introduced IDs,
  `dfe5aa104c4739cbac858955ed415bd2f49267191bb51dc7f2f38d8f50cb225c`
- materialized assignments: historical 137, GPU 51, core 50, current 2,368

Final review-only derivation:

- expanded rows: 139
- design-row digest:
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`
- explicit blockers: 98
  - unsupported `capture_output`: 44
  - exact helper arguments unresolved: 14
  - explicitly out-of-scope CuPy action/view: 11
  - dynamic direct-call repetition: 5
  - dynamic helper repetition: 8
  - mixed protected receiver: 10
  - unsupported `stdin`: 5
  - absent registered GPU probe implementation: 1
- subprocess census: 42 direct plus 4 reachable helper sites
- cross-file `setUpClass` edges: 27
- CuPy AST nodes: 28
- analyzed-site digest:
  `2d49993a8e19d30707681943505eccad4c2fa8cf270e27d7aaa2e40ccb81db6c`
- string-only sink decoys: 100 = 17 design production + 6 historical
  production + 26 prior stabilization synthetic + 51 Task 2 synthetic
- line-bound string-decoy digest:
  `0f081f740332d3dcca2ce8a676183e52c0e215044251a92bbc3429e3b32baa21`

The blocker reduction from 139 to 98 is exactly reconciled to newly supported,
source-ordered analysis: 11 formerly dynamic helper-argument cases, 21 formerly
mixed-receiver cases, and 9 callable-alias cases are now resolved (`11 + 21 + 9 =
41`). It is not an omitted-site reduction. Expanded rows remain 139; the real-corpus
42+4 subprocess census, 27 cross-file edges, 28 CuPy nodes, and analyzed-site digest
are unchanged. The exact reaching-definition, environment, match/handler, and child
program regression tests all pass and assert derived rows or explicit blockers with
forbidden-row absence.

### Final static, formatting, hash, and artifact gates

- AST-only parsing: 898 Python files, all successful without bytecode.
- New untracked Python lines over the configured 100-column limit: 0.
- Added tracked Python lines over 100 columns: 0.
- BOM files: 0; missing-final-LF files: 0; trailing-whitespace lines: 0 across
  all eight Task 2 files.
- Canonical binary-LF governance files:
  - `docs/architecture/dependency-baseline.toml`: 373,157 bytes,
    `b86dd2ba20e4639bc6c0184367a82b01ef3b1960ce863406f30964dd5c8625c6`
  - `tests/test-inventory.json`: 1,578,540 bytes, hash above
  - `tests/test-profiles.toml`: 453,194 bytes, hash above
- Inventory entries: 2,606; declared unconditional skips: exactly 2.
- Residual `.tmp`, `.recovery`, or deterministic governance-lock artifacts: 0.
- `git diff --check`: exit 0. Its only output was the expected four
  `core.autocrlf=true` advisories; there were no whitespace errors.
- Ruff is not installed in the approved D: virtual environment (`No module named
  ruff`). The repository's configured 100-column constraint was therefore enforced
  with the direct new/added-line scans above rather than claimed as a Ruff result.

Final eight-file SHA-256 values:

- `tools/test_orchestration/model.py`:
  `83161fcb39c87008e6cf98f9f0d801abc99103484a2c40a799524e3e2cab0d32`
- `tools/test_orchestration/configuration.py`:
  `a1cef160d600b2fe35b67e0931c5227552fc03068be376097f2d6e102780c0d8`
- `tests/test_test_orchestration_configuration.py`:
  `ff0491e75d8143078305cc85ed47fae5e093e2ee85bf48a8eedff57c539929f2`
- `tools/generate_test_inventory.py`:
  `68d1ff017a94a76309d3a3a5762ac9b87ea63a6bc02d3ee8284985cb098889c9`
- `tests/test-inventory.json`:
  `101dcbccfdbfa5caa015d73473161af99ea69415f724923acae5ca2f39787a2d`
- `tests/test-profiles.toml`:
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`
- `tests/test_inventory_and_profiles.py`:
  `e5d9f7c6ced5110a9d354696c386ac32d7bc55444d0f936d1888b9c2254095d1`
- `tests/test_h32_pre_bet_initial_row_cache_seed.py`:
  `51305e9f421a5c356e43a0d474393cec05b7431a02a0540603774f7c802d796b`

The worktree remains uncommitted with exactly four modified tracked files and four
untracked Task 2 files:

```text
 M tests/test_h32_pre_bet_initial_row_cache_seed.py
 M tests/test_test_orchestration_configuration.py
 M tools/test_orchestration/configuration.py
 M tools/test_orchestration/model.py
?? tests/test-inventory.json
?? tests/test-profiles.toml
?? tests/test_inventory_and_profiles.py
?? tools/generate_test_inventory.py
```

### Round-3 self-review and concerns

- Re-read the final coordinator and platform finalizers after GREEN. Final lifetime
  or output validation now sits inside the same rollback boundary as finalization.
  Recovery disposal remains the irreversible commit point; confirmed post-commit
  closes cannot trigger rollback or double-close.
- The cooperative Windows writer guarantee is deliberately narrower than arbitrary
  same-user CAS. The deterministic lock and share-mode tests prove the supported
  Pontius-writer boundary and do not claim protection from a process that ignores it.
- The 98 remaining review blockers are explicit and intentionally keep Task 2
  preapproval at all-zero. The absent future GPU probe and every unresolved/dynamic
  site remain carry-forward items for Task 12 approval work.
- Full repository payload execution remains deliberately unverified. The prior
  read-only OneDrive evidence was not rerun because fix round 3 prohibited touching
  OneDrive.
- Independent frozen round-3 contract and I/O/security rereview is required before
  any commit or integration.

## Fix round 4: source-ordered analyzer and group-owned governance transactions

All work in this round was performed only in `D:\Pontius-worktrees\orch-task2`.
No repository payload was run, no capability review was emitted, no capability
approval or capability write was performed, and no commit, merge, push, or OneDrive
operation was performed. Production changes remain uncommitted for independent
frozen rereview.

### Analyzer RED/GREEN evidence

- Split analyzer RED command:
  `task-2-run-snapshot.ps1 -Label fix4-analyzer-red2`
  `-TestFile test_inventory_and_profiles.py -ExpectedExit 1`.
- RED snapshot:
  `pontius-orch-task2-fix4-analyzer-red2-4ec4a97a98004913bf92db4600b64bbf`.
  Result: 66 tests, 29 failures and 10 errors, exit 1, cleaned. The independent
  failures covered helper-return summaries, match capture and source-point bounds,
  conditional-expression maxima, raised/normal outcomes, definition-point
  decorator state, literal-child recursion, and shared analysis budgets.
- Analyzer implementation checkpoint command used the same snapshot harness and
  test file with label `fix4-analyzer-green-attempt3` while generated governance
  was deliberately stale.
- GREEN checkpoint snapshot:
  `pontius-orch-task2-fix4-analyzer-green-attempt3-619c8450d73242d09c9c41a008f68f80`.
  Result: 83 tests; every analyzer/design-review test passed, with only the then
  expected transaction and stale-governance cases remaining.
- Reconciliation RED command used label `fix4-analyzer-reconcile-red` against
  `test_inventory_and_profiles.py`, expected exit 1.
- RED snapshot:
  `pontius-orch-task2-fix4-analyzer-reconcile-red-f47c1dc3fba141099a1b59ac10c36f8b`.
  Result: 83 tests with exactly two intended failures: the stale generated census
  and false sensitive taint through a safe observer.
- The canonical-affine oracle was not weakened. Exact helper-return summarization
  proves `_five_way_tie_scale_family()` has cardinality three, so its two
  `cupy.asnumpy` sites retain `maximum_calls = 6`. Exact safe observer/mock factory
  registries and qualified-module overlays removed false taint without adding a
  broad allow rule.

The byte-identical dynamic literal-child program has one canonical failure reason:
`subprocess dynamic Python program has unresolved sensitive dataflow`. Its blocker
location is the parent `ast.Call.lineno`, line 19 in the locked fixture; the earlier
line-21 expectation pointed to a keyword rather than the call node and was corrected.

### Governance transaction RED/GREEN evidence

- Initial transaction RED command used the snapshot harness label
  `fix4-transaction-red1`, `test_inventory_and_profiles.py`, expected exit 1.
- RED snapshot:
  `pontius-orch-task2-fix4-transaction-red1-6393d451ecf642188871d0383b349ca2`.
  Result: 83 tests, 34 failures and 33 errors overall; the isolated transaction
  cluster had 5 failures and 23 errors. It reproduced missing group ownership,
  reservation transfer, persistent cleanup, lock lifetime, and commit-decision
  behavior.
- First GREEN attempt snapshot:
  `pontius-orch-task2-fix4-transaction-green-attempt1-89744d2826444effbf0097dc21bb6398`:
  14 failures and 6 errors.
- Second GREEN attempt snapshot:
  `pontius-orch-task2-fix4-transaction-green-attempt2-5fb39a94f7e04e16ae350c87a93ab9cb`:
  6 failures and 5 errors.
- Third GREEN attempt snapshot:
  `pontius-orch-task2-fix4-transaction-green-attempt3-2e20ac6793104bc2bbdc1484c48a1ad2`:
  2 failures and 2 errors.
- Transaction checkpoint snapshot:
  `pontius-orch-task2-fix4-transaction-green-attempt4-4548d1237ebb422c89791e266d00bc64`:
  all transaction tests passed; only two deliberately stale generated-governance
  checks remained.
- Residual transaction RED command used label `fix4-transaction-residual-red`
  against `test_inventory_and_profiles.py`, expected exit 1.
- RED snapshot:
  `pontius-orch-task2-fix4-transaction-residual-red-5e7ac30c7b334336a1ab00f875c5b449`.
  Result: 87 tests, 4 failures and 3 errors; 3 errors plus 2 failures were the
  intended transaction residuals and the remaining two failures were stale
  governance.
- Residual GREEN checkpoint snapshot:
  `pontius-orch-task2-fix4-transaction-residual-green1-38f4ad2626de4e3881b15745e801e09f`.
  Result: 87 tests with every transaction residual green and only two stale
  governance failures.

The resulting coordinator is one `_GovernanceWriteGroup` over the complete,
canonical destination set. It acquires deterministic locks before destination,
source, or Git observations; owns all participants and cleanup resources strongly;
performs one validate-all/commit decision; and has no committed-to-rollback path.
The bounded cleanup manager retains exact pending descriptors and owners across
synchronous retries and process-exit retry. A transient post-commit recovery close
that succeeds inside the retry budget returns ordinary success; a persistent
post-commit cleanup failure reports the committed state and never restores old
bytes.

The final residual fixes additionally lock these invariants:

- cleanup-manager singleton creation is mutex-protected;
- partially acquired deterministic locks transfer to the pre-reserved manager slot
  when cleanup cannot complete;
- POSIX deterministic-lock descriptor close and pathname unlink are separate,
  monotonic phases, with close preceding unlink and no reused-descriptor retry;
- Windows deterministic-lock ownership attaches immediately after creation, before
  disposition, so disposition or close failures remain manager-owned;
- obsolete best-effort swallowing and rollback-after-finalization entry points were
  removed; participants expose committed cleanup, not finalized rollback.

The supported Windows guarantee remains explicitly cooperative: compliant Pontius
writers serialize through the deterministic lock set. The implementation and tests
do not claim impossible protection from an arbitrary same-user process that ignores
that boundary.

### Ordinary regeneration and final focused verification

Ordinary zero-scope regeneration ran with `generate_test_inventory.py --write` and
completed with exit 0. It was immediately followed by `--check`, also exit 0. A
second final `--check` was byte-stable: inventory SHA-256 stayed
`0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`
and profile SHA-256 stayed
`2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.

- Final inventory command:
  `task-2-run-snapshot.ps1 -Label fix4-inventory-final-green`
  `-TestFile test_inventory_and_profiles.py -ExpectedExit 0`.
- Snapshot:
  `pontius-orch-task2-fix4-inventory-final-green-a56633c0d1934187a05315137ced2bcb`.
  Result: 87/87 passed, exit 0, 40.667 seconds, cleaned.
- Final configuration command:
  `task-2-run-snapshot.ps1 -Label fix4-config-final-green`
  `-TestFile test_test_orchestration_configuration.py -ExpectedExit 0`.
- Snapshot:
  `pontius-orch-task2-fix4-config-final-green-e077d7668f2d45c5b99ba76f713f207f`.
  Result: 53/53 passed, exit 0, 0.361 seconds, cleaned.
- Final H32 command:
  `task-2-run-snapshot.ps1 -Label fix4-h32-final`
  `-TestFile test_h32_pre_bet_initial_row_cache_seed.py -ExpectedExit 0`.
- Snapshot:
  `pontius-orch-task2-fix4-h32-final-3192ab8e51e14d79a502f6b8317986c6`.
  Result: 9 run, 8 passed, exactly one approved unconditional skip, exit 0,
  1.477 seconds, cleaned.

Final scoped total: 149 discovered methods, 148 passed, and exactly one approved
unconditional skip.

### Exact inventory, capability, and review-only state

The locked baseline remains byte- and membership-stable:

- 392 test files and 2,367 stable IDs,
  `c8e6465527a9b784f4be41947745f6e86d53f45d16fd0d10955009bbb127b37b`
- historical 137,
  `77ccf22ac1f52ebbeff7311bf2c4c1fb4f83671a5cfe10f84dbbde655ecb58a8`
- GPU 51,
  `896fb0675371186476df33b13eb7a5d9286dfeb01f53d37daa0f458e72021005`
- core 50,
  `38166290ad900c24a08c93f08de3376dac92a2c35544a94c3228726b01a02dfc`
- current 2,129,
  `c32575a47a889e7e324db2abb56ef5c5b37295bb6a5cc3e6006cb04c767c6803`
- exclusions: 0.

Final working discovery and materialization:

- 399 test files
- 2,637 stable IDs,
  `f508e2f29f8f0830cd903aef87627c77c6372b13fa19d6b868bb0c724e9f3f07`
- 270 introduced IDs,
  `262ca134a0eeea7c9458aed44fb1758a81d3b8a5d9bb5982857a9199f07f1224`
- 2,637 entries
- assignments: historical 137, GPU 51, core 50, current 2,399.

Final review-only derivation:

- expanded rows: 139
- design-row digest:
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`
- deny-all rows: 2,578
- explicit blockers: 93
  - unsupported subprocess keyword `capture_output`: 44
  - dynamic helper arguments prevent exact sink derivation: 14
  - CuPy action or view is outside approved call scope: 11
  - mixed protected receiver dynamically unresolved: 10
  - unsupported subprocess keyword `stdin`: 5
  - dynamic repetition prevents a finite call bound: 5
  - unregistered CuPy call dynamically unresolved: 2
  - registered probe implementation is absent: 1
  - dynamic sensitive call result is unresolved: 1
- subprocess census: 42 direct plus 4 reachable helper sites
- cross-file `setUpClass` edges: 27
- CuPy call nodes: 30
- analyzed-site digest:
  `b4006b5928e982c587eda852e53527d0f116952149a129cf08ca233f3a89db10`
- string-only sink decoys: 147 = 17 design production + 6 historical
  production + 26 prior stabilization synthetic + 98 Task 2 synthetic
- line-bound string-decoy digest:
  `93a0665d28b29f0b9c51e15e2337521e75405ec30cb8a7d7cd7f48459940c454`.

The blocker change from 98 to 93 is fully reconciled rather than treated as a lower
number by itself: eight false empty-helper repetition blockers were removed, while
one protected-result blocker and two proven CuPy `.copy()` blockers were added
(`98 - 8 + 1 + 2 = 93`). The sole protected-result residual is
`tests/test_multi_size_affine_cross_payoff.py:134`; the two new CuPy rows are
`tests/test_resident_record_to_hand_fold_v2.py:312` and `:313`. The canonical
six-call affine row is present. The direct/helper subprocess census, fixture-edge
census, full CuPy-node census, source-row digest, and exact per-site tests prevent a
silent-site reduction.

Both approval scopes remain deliberately absent/all-zero:

- `spec_capabilities_sha256` is 64 zeroes;
- `capability_bindings_sha256` is 64 zeroes;
- subprocess capability definitions: 0;
- call capability definitions: 0;
- capability bindings: 0;
- all three capability tables are absent from the TOML;
- cleanup-manager pending entries after final diagnostics: 0.

No review emit, approval, or capability write command was invoked.

### Final static, formatting, hash, and artifact gates

- `git diff --check`: exit 0. Output contained only the four expected
  `core.autocrlf=true` advisories and no whitespace error.
- AST parse: all 6 changed or newly added Python files passed without bytecode.
- Added/untracked Python lines over 100 columns: 0.
- BOM files: 0; missing-final-LF files: 0; trailing-whitespace lines: 0 across all
  nine reviewed files.
- `.gitattributes`, `tests/test-inventory.json`, and `tests/test-profiles.toml` are
  canonical LF-only files.
- Residual governance `.tmp`, `.recovery`, deterministic lock, and attribute-temp
  artifacts: 0.
- Ruff was unavailable in the approved D: virtual environment (`No module named
  ruff`) and no standalone `ruff` executable was installed. This is reported as a
  tooling limitation; AST, added-line, final-LF, trailing-whitespace, and
  `git diff --check` gates were run directly and passed.

Final SHA-256 values:

- `tools/test_orchestration/model.py`:
  `83161fcb39c87008e6cf98f9f0d801abc99103484a2c40a799524e3e2cab0d32`
- `tools/test_orchestration/configuration.py`:
  `a1cef160d600b2fe35b67e0931c5227552fc03068be376097f2d6e102780c0d8`
- `tests/test_test_orchestration_configuration.py`:
  `ff0491e75d8143078305cc85ed47fae5e093e2ee85bf48a8eedff57c539929f2`
- `tools/generate_test_inventory.py`:
  `5f4015d5a81ace581685bf62f8944a8489ba48b1d2f0130966551baf493dc2cf`
- `tests/test-inventory.json`:
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`
- `tests/test-profiles.toml`:
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`
- `tests/test_inventory_and_profiles.py`:
  `10f56c29c45723bbae31cca3d6d44fd294fa4f5659ef596c8ebea1a72a834117`
- `tests/test_h32_pre_bet_initial_row_cache_seed.py`:
  `51305e9f421a5c356e43a0d474393cec05b7431a02a0540603774f7c802d796b`
- `.gitattributes`:
  `706186f67033d1e1c84992544ea7a40006de1b4e438a9d5b3cb28f583d0d985a`.

Final worktree status remains exactly four modified tracked files and four untracked
Task 2 files:

```text
 M tests/test_h32_pre_bet_initial_row_cache_seed.py
 M tests/test_test_orchestration_configuration.py
 M tools/test_orchestration/configuration.py
 M tools/test_orchestration/model.py
?? tests/test-inventory.json
?? tests/test-profiles.toml
?? tests/test_inventory_and_profiles.py
?? tools/generate_test_inventory.py
```

### Round-4 self-review and remaining concerns

- Re-read the analyzer dataflow, helper summarization, child-program recursion,
  transaction-group decision boundary, cleanup-manager retry ownership, and both
  platform lock-owner state machines after the final GREEN snapshots.
- No committed object exposes rollback. Every retry phase is monotonic, and a
  confirmed close is never retried or double-closed.
- The 93 blockers are explicit preapproval results, not silently missed sinks. They
  intentionally keep both capability scopes at all-zero for later Task 12 review.
- The cooperative Windows serialization boundary and the lack of arbitrary
  same-user CAS protection remain explicit architectural constraints.
- Full repository payload execution remains deliberately outside Task 2. The
  approved focused suites are green; no broader payload claim is made.
- OneDrive secure-read evidence from the prior approved round was not rerun because
  round 4 expressly prohibited touching OneDrive.
- Ruff remains unavailable, as recorded above.
- Independent frozen round-4 contract and I/O/security rereview is required before
  any commit or integration.

## Fix round 5 analyzer/discovery implementation

Work was limited to `tools/generate_test_inventory.py` and the analyzer/discovery
portions of `tests/test_inventory_and_profiles.py` in
`D:\Pontius-worktrees\orch-task2`. No scientific/GPU payload, capability
emit/approve/write operation, OneDrive access, commit, merge, or push occurred.

### RED/GREEN evidence

- Initial analyzer RED command:
  `python tests/test_inventory_and_profiles.py AstDiscoveryTests.test_declared_skip_requires_the_exact_outer_literal_and_reason_code DesignReviewTests.test_round4_sensitive_provenance_red_contracts_are_independent DesignReviewTests.test_round4_match_capture_red_contracts_are_independent DesignReviewTests.test_round4_child_and_helper_provenance_red_contracts_are_independent DesignReviewTests.test_round4_source_order_and_branch_bounds_red_contracts_are_independent DesignReviewTests.test_round4_exception_environment_red_contracts_are_independent DesignReviewTests.test_round4_decorator_definition_point_red_contracts_are_independent DesignReviewTests.test_round4_analysis_budget_red_contracts_are_independent`.
  Exit 1; 8 tests reported 12 failures and 5 errors. One error was the mistyped
  discovery class selector; the other four errors and all failures were the
  intended missing-row/blocker, stale exceptional state, raw `RecursionError`,
  and unchecked-cardinality reproductions.
- Corrected discovery RED command:
  `python tests/test_inventory_and_profiles.py MaterializedOwnershipTests.test_declared_skip_requires_the_exact_outer_literal_and_reason_code`.
  Exit 1; one test, three expected failures for inner, class-level, and multiple
  unconditional skips.
- Focused GREEN command used the corrected discovery selector followed by the
  same seven `DesignReviewTests` selectors above. Exit 0; 8/8 passed in 0.230s.
- Complete direct GREEN command:
  `$env:PONTIUS_GIT='C:\Program Files\Git\cmd\git.exe'; python tests/test_inventory_and_profiles.py`.
  Exit 0; 87/87 passed in 42.205s.
- Final isolated Python 3.11 command:
  `task-2-run-snapshot.ps1 -Label fix5-analyzer-final-green -TestFile test_inventory_and_profiles.py -ExpectedExit 0`.
  Snapshot `pontius-orch-task2-fix5-analyzer-final-green-2008a99a0acf4ed58be9417d59fcb9d3`;
  87/87 passed in 49.811s, exit 0, cleaned.

The implementation now source-order-summarizes helper returns; preserves child
sensitivity through unsupported expressions and stores; retains match residual
and sequential guard paths; propagates explicit exceptional state through nested
compound statements; annotates exact finite while bounds; joins conditional and
comprehension walrus effects; invalidates retained conditional-decorator aliases
at Python binders; converts deep recursion and cardinality overflow to stable
`InventoryError`; reconciles every direct sensitive census site to a row, blocker,
or proved-unreachable disposition; and accepts only the exact single outermost
registered method-level unconditional skip.

### Regeneration, reconciliation, and static state

- Ordinary all-zero `--write` and `--check` both exited 0. Inventory SHA-256 was
  byte-stable at `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profile SHA-256 was byte-stable at
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- Working discovery remains 399 files / 2,637 IDs / 270 introduced IDs. The
  review remains 139 expanded rows, digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  2,578 deny-all rows, and 93 blockers. The real-corpus 42+4 subprocess census,
  27 cross-file edges, 30 CuPy nodes, and analyzed-site digest
  `b4006b5928e982c587eda852e53527d0f116952149a129cf08ca233f3a89db10`
  are unchanged.
- New test literals move only the string-decoy census to 156, partitioned
  17 design production + 6 historical production + 26 prior stabilization +
  107 Task 2 synthetic, digest
  `f2b2261f3d69e2cb0b9997c3c0bc30eee5336e229c597add1718b724b4957a21`.
- Both capability digests remain all-zero; subprocess definitions, call
  definitions, bindings, and cleanup-pending entries are all `0/0/0/0`.
- AST parse was 2/2; both changed Python files have no BOM, CR bytes, trailing
  whitespace, missing final LF, or lines over 100 columns. `git diff --check`
  exited 0 with only the four existing `core.autocrlf=true` advisories.
- Final SHA-256: generator
  `3115eae6ef7b9455a6a71617aaba1ee2920020d1289bbdcef19f1e14845c15b5`;
  analyzer/discovery tests
  `739b3304aba63f6ae82a196608fbab2086f93c943f6ee98ed205412cd33b1472`.

Concern: exceptional-state precision is exact for explicit raises through the
covered compound forms and otherwise deliberately fail-closed; full scientific
payload execution remains outside Task 2. Independent frozen analyzer rereview is
still required before integration.

## Fix round 5 analyzer task-review correction

Work remained limited to analyzer/discovery code in
`tools/generate_test_inventory.py` and existing analyzer/discovery methods in
`tests/test_inventory_and_profiles.py`. No transaction/I/O code or tests,
scientific/GPU payload, capability operation, OneDrive path, commit, merge, or
push was touched.

### Exact RED/GREEN evidence

- RED command:
  `python tests/test_inventory_and_profiles.py DesignReviewTests.test_round4_sensitive_provenance_red_contracts_are_independent DesignReviewTests.test_round4_source_order_and_branch_bounds_red_contracts_are_independent DesignReviewTests.test_round4_exception_environment_red_contracts_are_independent DesignReviewTests.test_round4_decorator_definition_point_red_contracts_are_independent DesignReviewTests.test_round4_analysis_budget_red_contracts_are_independent`.
  Exit 1; 5 tests produced 11 intended assertion failures and one raw
  `RecursionError` for the exact rereview reproductions.
- Final focused GREEN used the same five selectors. Exit 0; 5/5 passed in
  0.123s.
- Final complete direct command:
  `$env:PONTIUS_GIT=(Get-Command git).Source; python tests/test_inventory_and_profiles.py`.
  Exit 0; 87/87 passed in 43.453s.
- Final isolated Python 3.11 command:
  `task-2-run-snapshot.ps1 -Label fix5-analyzer-rereview-final3-green -TestFile test_inventory_and_profiles.py -ExpectedExit 0`.
  Snapshot
  `pontius-orch-task2-fix5-analyzer-rereview-final3-green-268667bd1f1a46e8b69261a7451528f8`;
  87/87 passed in 51.718s, exit 0, cleaned.

The correction now evaluates every mapping child before returning an unresolved
result; distinguishes zero, positive, and possibly-zero comprehension effects;
checks dict-comprehension expanded storage before allocation; models outer-loop
terminators conservatively and counts repeated while conditions; propagates
post-statement exceptional states without a pre-try handler fallback; keeps
explicit conditional-skip provenance tombstones across every Python binder,
including `MatchStar` and `MatchMapping.rest`; meters execution-scope and
call-bound traversal through the shared analysis budget; and reconciles the
resolved analyzer against an independent source-ordered sensitive-site census.

### Final regeneration and reconciliation

- Ordinary all-zero `python -B -P tools/generate_test_inventory.py --write` and
  `--check` both exited 0. Inventory remained byte-stable at
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles remained byte-stable at
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- The complete-suite reconciliation remains 139 expanded rows, digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  2,578 deny-all rows, and 93 explicit blockers. The 42+4 subprocess census,
  27 cross-file edges, 30 CuPy nodes, and analyzed-site digest
  `b4006b5928e982c587eda852e53527d0f116952149a129cf08ca233f3a89db10`
  are unchanged.
- Added rereview literals move only the locked string-decoy census to 160:
  17 design production + 6 historical production + 26 prior stabilization +
  111 Task 2 synthetic, digest
  `b30c4d0c4a44c8503ff6b64f38898504e4e6c2c865793b1134016850bb619798`.
- Both capability scopes remain all-zero; subprocess definitions, call
  definitions, bindings, and cleanup-pending entries remain `0/0/0/0`.
- AST parse passed 2/2; `git diff --check` exited 0; both changed files have no
  BOM or CR bytes, end in LF, and have no line over 100 columns. Final SHA-256:
  generator
  `379fcd5ce5225d92f2e348bdc1b3910d65d9203ddc06a7a988cd90b0a09c0b56`;
  analyzer/discovery tests
  `cac4af077e8aa95c1395b3eb5d53d9b03262b4b9a4ec497b8b51bbff2adbfa35`.

Concern: full scientific/GPU payload execution remains intentionally outside
Task 2; no broader payload claim is made.

## Fix round 5 transaction/I/O implementation

Work was limited to transaction/I/O code in
`tools/generate_test_inventory.py`, transaction/I/O coverage in
`AtomicAndGitBoundaryTests` in `tests/test_inventory_and_profiles.py`, the one
unavoidable locked string-decoy line-location digest in that test file, and
this report. Analyzer/discovery behavior, configuration/model/H32 code,
scientific/GPU payloads, capability operations, OneDrive paths, and generated
governance bytes were not changed. No commit, merge, or push was performed.

### Exact RED and focused GREEN evidence

- Before production edits, the exact focused command selected the eleven
  temporary `AtomicAndGitBoundaryTests.test_round5_*` reproductions for:
  operation-entry ordering, dict-captured undeclared destinations,
  active-group membership, active hardlink pairs, exclusive cleanup
  generations, retry-before-capacity, Git component cleanup, exact partial
  lock ownership, POSIX parent exchange, reused POSIX descriptors, and invalid
  retained-transaction dispatch. Exit 1; 11 tests produced 16 intended
  assertion failures on the frozen analyzer-clean source.
- The final inventory-visible test census remains unchanged: those cases were
  consolidated as eleven `_round5_*` helpers under the existing
  `test_lock_set_precedes_all_destination_and_lifetime_observation` ID. The
  exact eleven explicit selectors passed in 1.321s. The discovered 38 Atomic
  tests plus those eleven explicit helpers passed 49/49 in 4.539s.
- The operation-entry reproduction also drives `main(["--write"])` through an
  explicit two-destination lease. Old caller snapshots raise on any second
  revalidation while the pair lifetime runs twice, proving that authoritative
  locked pair snapshots own CAS publication and that participant one is not
  incorrectly revalidated as old after its intentional replacement.

### Implemented transaction and ownership contract

- Every write entry declares one immutable complete destination set, acquires
  its canonical lock set before Git/source/destination observations, proves
  active-group membership before I/O, and rejects native aliases after all
  locks and before participants. Closure/function-attribute destination
  inference and pair caller-snapshot parameters were removed.
- Cleanup retry is exclusive per pending-entry generation, executes callbacks
  outside the manager mutex, and runs before capacity reservation. Git lease
  descriptor and ancestor cleanup is component-idempotent. Partial multi-lock
  failures report only held keys, released keys, extant artifacts, and actual
  remaining roles.
- POSIX lock names are opened and unlinked relative to a retained, verified
  parent directory descriptor. The same anchor is reused for publication and
  cleanup, with deterministic refusal on parent-chain drift. Staging,
  published/recovery, directory, Git, and deterministic-lock descriptor owners
  probe identity after close exceptions and never retry a reused numeric fd.
- `_retain_transaction` must be exact `True` before directory-chain work or
  platform dispatch. Ordinary, design-review, and capability-write entry paths
  now perform capture/derivation inside their explicit leases. CLI repository
  and temp-child path setup is lexical, avoiding pre-lock filesystem
  resolution.

### Final direct, isolated, generation, and review gates

- Final direct command:
  `$env:PONTIUS_GIT=(Get-Command git).Source; python tests/test_inventory_and_profiles.py`.
  Exit 0; 87/87 passed in 49.188s.
- Final isolated Python 3.11 command:
  `task-2-run-snapshot.ps1 -Label fix5-transaction-final3 -TestFile test_inventory_and_profiles.py -ExpectedExit 0`.
  Snapshot
  `pontius-orch-task2-fix5-transaction-final3-b6a9c0a1c5914c0aa2d53fc55df6afbc`;
  87/87 passed in 59.262s, exit 0, cleaned.
- Ordinary all-zero `python -B -P tools/generate_test_inventory.py --write`
  and `--check` both exited 0. Inventory stayed byte-stable at
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles stayed byte-stable at
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- CodeRabbit CLI 0.7.5, authenticated agent mode, ran
  `coderabbit review --agent -t uncommitted --include-untracked`, completed,
  reviewed all eight modified/untracked candidate files, and raised 0 issues.

### Reconciliation, static state, and hashes

- Review reconciliation remains 139 expanded rows, digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  2,578 deny-all rows, and 93 blockers. The 42+4 subprocess census, 27
  cross-file edges, 30 CuPy nodes, and analyzed-site digest
  `8219efd8ef8379ac071b687765eebd783319d15e5343911592ae92966d45cb71`
  are unchanged.
- The string-decoy census remains 167 with partitions 17/6/26/118. Only its
  line-location digest changed, to
  `cbead46c0273de05ad24977b5b20b804468aab0f196453940e07952b0b4c141b`.
- Capability definitions/bindings remain `0/0/0`; both capability digests are
  all-zero; cleanup-manager pending entries are 0; residual governance
  `.tmp`, `.recovery`, deterministic-lock, and attribute-temp artifacts are 0.
- AST parse passed 2/2. Both changed Python files are BOM-free, CR-free,
  LF-terminated, have no trailing whitespace, and have no line over 100
  columns. `git diff --check` exited 0 with only the four existing line-ending
  advisories.
- Final SHA-256: generator
  `da3f5d1f82e9b0b9fe808d00ea88b55c1e7610639a75e09a0a2eb57c7fc4e89f`;
  transaction/analyzer test file
  `b44f9b45d298f36d842e0e0e99679976601de7cb71493b2c2563648a2e3a2265`.

Concern: full scientific/GPU payload execution remains intentionally outside
Task 2; no broader payload claim is made.

## Fix round 5 analyzer scoped rereview 2 correction

Work remained limited to analyzer/discovery code in
`tools/generate_test_inventory.py` and existing analyzer/discovery methods in
`tests/test_inventory_and_profiles.py`. No transaction/I/O section,
scientific/GPU payload, capability operation, OneDrive path, commit, merge, or
push was touched.

### Exact RED/GREEN evidence

- RED command:
  `python tests/test_inventory_and_profiles.py DesignReviewTests.test_round4_source_order_and_branch_bounds_red_contracts_are_independent DesignReviewTests.test_round4_exception_environment_red_contracts_are_independent DesignReviewTests.test_round4_decorator_definition_point_red_contracts_are_independent DesignReviewTests.test_round4_analysis_budget_red_contracts_are_independent`.
  Exit 1; 4 tests produced 14 intended assertion failures: four unreachable
  sensitive calls were counted, six exceptional header paths retained the
  normal-only environment, one missing-provenance decorator was accepted, one
  secondary call-bound pass escaped its shared budget, and two expanded
  cardinalities exceeded the bound without refusal.
- Final focused GREEN used the same four selectors. Exit 0; 4/4 passed in
  0.114s.
- Final complete direct command:
  `$env:PONTIUS_GIT=(Get-Command git).Source; python tests/test_inventory_and_profiles.py`.
  Exit 0; 87/87 passed in 48.696s.
- Final isolated Python 3.11 command:
  `task-2-run-snapshot.ps1 -Label fix5-analyzer-rereview2-final -TestFile test_inventory_and_profiles.py -ExpectedExit 0`.
  Snapshot
  `pontius-orch-task2-fix5-analyzer-rereview2-final-4a81b5ca9d1742c3971a3467c517944a`;
  87/87 passed in 57.171s, exit 0, cleaned.

The correction now carries normal, break, continue, return, raise, and
exceptional successors through nested source-ordered compounds; excludes calls
after all-terminating branches from both flow evaluation and runtime bounds;
captures potentially throwing compound headers at their exact environment
state; requires an observed canonical binding for conditional skip decorators;
meters call-bound expressions, helper closure scans, literal-child scans, and
secondary AST walks against the shared analysis budget with stable recursion
translation; and uses checked, budgeted preclassifier range and product
cardinality.

### Final regeneration, reconciliation, and static state

- Ordinary all-zero `python -B -P tools/generate_test_inventory.py --write` and
  `--check` both exited 0. Inventory remained byte-stable at
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles remained byte-stable at
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- Reconciliation remains 139 expanded rows, digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  2,578 deny-all rows, and 93 explicit blockers. The 42+4 subprocess census,
  27 cross-file edges, and 30 CuPy nodes are unchanged. Added analyzer test
  lines move the line-bound analyzed-site digest to
  `8219efd8ef8379ac071b687765eebd783319d15e5343911592ae92966d45cb71`
  without changing its counts.
- Added reproductions move the string-decoy census to 165: 17 design
  production + 6 historical production + 26 prior stabilization + 116 Task 2
  synthetic, digest
  `c152269a4533fe3f55bb6550fd16a7d6a3d564813165f6dba3bdd1031c3ffd07`.
- Both capability scopes remain all-zero; subprocess definitions, call
  definitions, bindings, and cleanup-pending entries remain `0/0/0/0`.
- AST parse passed 2/2; `git diff --check` exited 0 with only the four existing
  line-ending advisories; both changed Python files have no BOM, CR bytes,
  trailing whitespace, missing final LF, or lines over 100 columns. Static AST
  gates confirmed every call-bound expression traversal receives the shared
  budget and the preclassifier contains no raw repetition multiplication.
- Final SHA-256: generator
  `403d7255ee95e716f88c043caf1270dceb8499b07d2778d789c16f2a659aa2a8`;
  analyzer/discovery tests
  `d577db2acfffd2bca246e57ab2ca0b3f1e738ce72236434d33fe1acec6ec2265`.

Concern: full scientific/GPU payload execution remains intentionally outside
Task 2; no broader payload claim is made.

## Fix round 5 analyzer scoped rereview 3 correction

Work remained limited to analyzer/discovery code in
`tools/generate_test_inventory.py` and the existing analyzer/discovery test
method in `tests/test_inventory_and_profiles.py`. No transaction/I/O section,
scientific/GPU payload, capability operation, OneDrive path, commit, merge, or
push was touched.

### Exact RED/GREEN evidence

- RED command:
  `python tests/test_inventory_and_profiles.py DesignReviewTests.test_round4_source_order_and_branch_bounds_red_contracts_are_independent`.
  Exit 1; the single test produced one intended failing subtest. For
  `with contextlib.suppress(RuntimeError): raise RuntimeError` followed by
  `cupy.arange(1)`, the analyzer produced no call row instead of the required
  `[('cupy.arange', 1)]`.
- Focused GREEN used the same selector. Exit 0; 1/1 passed in 0.031s.
- Final complete direct command:
  `$env:PONTIUS_GIT=(Get-Command git).Source; python tests/test_inventory_and_profiles.py`.
  Exit 0; 87/87 passed in 48.600s.
- Final isolated Python 3.11 command:
  `task-2-run-snapshot.ps1 -Label fix5-analyzer-rereview3-final -TestFile test_inventory_and_profiles.py -ExpectedExit 0`.
  Snapshot
  `pontius-orch-task2-fix5-analyzer-rereview3-final-9c995d1c5b2d49c9866f0e51a470e8c1`;
  87/87 passed in 57.179s, exit 0, cleaned.

The source-ordered flow now retains a conservative normal successor for an
exception raised inside a `with` body because an unresolved context manager may
suppress it, while also retaining the unsuppressed exceptional successor.
Static fallthrough classification no longer treats an enclosing `with` as
terminal merely because its body terminates. Returns, breaks, and continues are
unchanged because context managers cannot suppress those control transfers.

### Final regeneration, reconciliation, and static state

- Ordinary all-zero `python -B -P tools/generate_test_inventory.py --write` and
  `--check` both exited 0. Inventory remained byte-stable at
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles remained byte-stable at
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- Reconciliation remains 139 expanded rows, digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  2,578 deny-all rows, and 93 explicit blockers. The 42+4 subprocess census,
  27 cross-file edges, 30 CuPy nodes, and line-bound analyzed-site digest
  `8219efd8ef8379ac071b687765eebd783319d15e5343911592ae92966d45cb71`
  are unchanged.
- The new reproduction moves the string-decoy census to 167: 17 design
  production + 6 historical production + 26 prior stabilization + 118 Task 2
  synthetic, digest
  `e965ff7b38055074c83ce8bcb4669aaaf4aca8912eefcd7596e63ad3907e8e1a`.
- Both capability scopes remain all-zero; subprocess definitions, call
  definitions, bindings, and cleanup-pending entries remain `0/0/0/0`.
- AST parse passed 2/2; `git diff --check` exited 0 with only the four existing
  line-ending advisories; both changed Python files have no BOM, CR bytes,
  trailing whitespace, missing final LF, or lines over 100 columns.
- Final SHA-256: generator
  `9ccf90e23f68929c39b8be10f128dd958f75834b59afc5b7c71c958e582829c4`;
  analyzer/discovery tests
  `aa1fc835528e09a8ca63f060b210f59ec7f0279355e1a75fc6795a64da1fc083`.

Concern: full scientific/GPU payload execution remains intentionally outside
Task 2; no broader payload claim is made.

## Fix round 5 analyzer scoped rereview 4 correction

Work remained limited to analyzer/discovery code in
`tools/generate_test_inventory.py` and the existing analyzer/discovery test
method in `tests/test_inventory_and_profiles.py`. No transaction/I/O section,
scientific/GPU payload, capability operation, OneDrive path, commit, merge, or
push was touched.

### Exact RED/GREEN evidence

- RED command:
  `python tests/test_inventory_and_profiles.py DesignReviewTests.test_round4_source_order_and_branch_bounds_red_contracts_are_independent`.
  Exit 1; the single test produced four intended failing subtests. Runtime
  counting emitted one unreachable sink after each `with`-body `return`,
  `break`, and `continue`, and helper-return resolution lost the expected
  subprocess row after appending a spurious implicit `None`.
- Focused GREEN used the same selector. Exit 0; 1/1 passed in 0.033s.
- Final complete direct command:
  `$env:PONTIUS_GIT=(Get-Command git).Source; python tests/test_inventory_and_profiles.py`.
  Exit 0; 87/87 passed in 46.625s.
- Final isolated Python 3.11 command:
  `task-2-run-snapshot.ps1 -Label fix5-analyzer-rereview4-final -TestFile test_inventory_and_profiles.py -ExpectedExit 0`.
  Snapshot
  `pontius-orch-task2-fix5-analyzer-rereview4-final-c857e85eeeed4b16b01e8553b97aaa7b`;
  87/87 passed in 57.504s, exit 0, cleaned.

The correction now distinguishes `return` from `raise` in static control
outcomes. A `with` body ending only in `return`, `break`, or `continue` remains
terminal because context managers cannot suppress those transfers. A body that
can raise remains nonterminal because an unresolved manager may suppress the
exception. This preserves the rereview-3 exception-suppression successor while
preventing runtime overcount and spurious helper fallthrough.

### Final regeneration, reconciliation, and static state

- Ordinary all-zero `python -B -P tools/generate_test_inventory.py --write` and
  `--check` both exited 0. Inventory remained byte-stable at
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles remained byte-stable at
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- Reconciliation remains 139 expanded rows, digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  2,578 deny-all rows, and 93 explicit blockers. The 42+4 subprocess census,
  27 cross-file edges, 30 CuPy nodes, and line-bound analyzed-site digest
  `8219efd8ef8379ac071b687765eebd783319d15e5343911592ae92966d45cb71`
  are unchanged.
- The string-decoy census remains 167: 17 design production + 6 historical
  production + 26 prior stabilization + 118 Task 2 synthetic. Added test lines
  move only its line-bound digest to
  `3b0e9eb354a85b8ef5774dfdbee0feaef46db56e25e0ddfd4b24d7662e56bdf8`.
- Both capability scopes remain all-zero; subprocess definitions, call
  definitions, bindings, and cleanup-pending entries remain `0/0/0/0`.
- AST parse passed 2/2; `git diff --check` exited 0 with only the four existing
  line-ending advisories; both changed Python files have no BOM, CR bytes,
  trailing whitespace, missing final LF, or lines over 100 columns.
- Final SHA-256: generator
  `2b2fada9631b1514840dc773aea70e50f6459fc0f0055579a18a77fc7b6bd062`;
  analyzer/discovery tests
  `1143d764ad86b266f94836129b0ed0d5df71532a815fa87b693c469b67a68e3e`.

Concern: full scientific/GPU payload execution remains intentionally outside
Task 2; no broader payload claim is made.

## Fix round 5 final frozen rereview correction

Scope remained limited to transaction/I/O and the two binding preclassifier
corrections in `tools/generate_test_inventory.py`, their existing private tests
in `tests/test_inventory_and_profiles.py`, and this appended report section.
Configuration/model/H32 source, generated bytes, capability tables, and
scientific/GPU payloads were not changed. No review emission, approval,
capability write, OneDrive access, commit, merge, or push occurred.

### RED/GREEN and implementation

- Frozen generator SHA-256 was
  `da3f5d1f82e9b0b9fe808d00ea88b55c1e7610639a75e09a0a2eb57c7fc4e89f`.
  The clean 12-selector RED run produced 16 intended assertion failures and
  zero harness errors. It covered six same-inode same-fd roles, default and
  explicit opt-out entry ordering, undeclared zero-Git ordering, exact cleanup
  generations, partial real Git acquisition, provisional parent ownership,
  parent-only lock truth, namespace and restoration-fsync state, absent-target
  link/unlink state, irrefutable match, throw-site handler state, and exact
  retain values. `None`/`False`/integer-`1` were already green because the
  frozen source already had the required `is not True` guard.
- Final focused result: 12/12 passed in 0.202 seconds. Atomic was 38/38 in
  3.295 seconds; DesignReview was 21/21 in 1.247 seconds.
- Raw descriptor/handle owners now have persistent monotonic close-attempt
  slots and never replay a numeric resource after an ambiguous close. Git
  components are owned immediately, independently cleaned, and unresolved
  remainder is manager-retained. POSIX parents are provisionally owned
  immediately after open.
- Cleanup waiters capture explicit immutable success/failure by generation and
  gate barging generations until joined waiters consume their result. Acquired,
  outstanding, and released lock truth no longer invents destination keys.
- Default/opt-out writes lock before capture. Repository verification is lazy
  inside the locked boundary, so undeclared writes reject before Git, source,
  derivation, destination observation, or participant creation.
- POSIX staging/recovery names are owned separately from descriptors. Namespace
  state updates before directory fsync, including the absent-target link before
  staging unlink and restoration before fsync, preserving truthful retries.
- The independent preclassifier exhausts unguarded irrefutable matches and
  propagates reachable throw-site state into handlers.

### Final verification

- Direct full suite: 87/87 passed in 49.739 seconds.
- Isolated Python 3.11 snapshot
  `pontius-orch-task2-fix5-final-rereview-correction2-ba4b5d4e6c124b54a242b18b0cc6e310`:
  87/87 passed in 57.562 seconds, exit 0, cleaned.
- Configuration snapshot
  `pontius-orch-task2-fix5-final-rereview-config-5ccf417e76d8440f9f0ecee6da343483`:
  53/53 passed in 0.388 seconds, exit 0, cleaned.
- H32 snapshot
  `pontius-orch-task2-fix5-final-rereview-h32-26a21a05ecce4973b2335eaac1be945e`:
  9 run, 8 passed, one approved unconditional skip, exit 0, cleaned.
- Ordinary all-zero `--write` and `--check` both exited 0. Inventory remained
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles remained
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- Reconciliation remains 139 expanded rows, design digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  2,578 deny-all rows, 93 blockers, subprocess census 42+4, 27 cross-file
  edges, 30 CuPy nodes, and analyzed-site digest
  `8219efd8ef8379ac071b687765eebd783319d15e5343911592ae92966d45cb71`.
  String-decoy count remains 167 = 17/6/26/118; only its test-line digest moved
  to `11358e20f1b094bd843f45e58390d97426ffb2b778214e8be4f440586198b594`.
- Capability counts remain `0/0/0`, both capability digests remain all-zero,
  cleanup-manager pending entries are 0, and worktree/attribute-temp artifacts
  are 0. AST parse passed 2/2; both edited Python files have no BOM, CR,
  trailing whitespace, missing LF, or lines over 100 columns. `git diff
  --check` exited 0 with only four existing line-ending advisories.
- Final SHA-256: generator
  `d123fb77baf17fdedf0a1dbbb19353d62289c60aa71c463ab839d80fe5855f18`;
  tests
  `8c8f75bd2164f610d2ffb9977804b9da3450741f11cc9441fd126a9b4ac0af33`.

Concern: full scientific/GPU payload execution remains intentionally outside
Task 2. Ambiguous close failures favor descriptor-reuse safety: the raw numeric
value is never retried even when a test double models a close that did not
complete.

## Fix round 5 corrected-candidate rereview correction

Scope remained limited to the binding transaction/I/O and exact exceptional-
successor preclassifier corrections in `tools/generate_test_inventory.py`, their
integrated private coverage in `tests/test_inventory_and_profiles.py`, and this
report section. Configuration/model/H32 source and generated inventory/profile
bytes were preserved. No scientific/GPU payload, review emission, capability
approval/write, OneDrive access, CodeRabbit run, commit, merge, or push occurred.

### RED and implementation

- The rejected generator was first confirmed at SHA-256
  `d123fb77baf17fdedf0a1dbbb19353d62289c60aa71c463ab839d80fe5855f18`.
  The clean three-selector integrated RED aggregate produced 11 intended
  failures and zero errors or cleanup/harness failures. It exercised the legacy
  callback after revalidation, parent probe failure, nested protected/safe and
  multiple throw sites, post-`O_EXCL` staging probe failure, real POSIX
  exchange/replace/link rollback schedules, real multi-component Git partial
  acquisition, first-sidecar parent-only truth, distinct owner-family numeric
  reuse, and the real Windows absent-target ambiguous-close retry schedule.
- Stage A removed the unrestricted target-taking callback interface. Exact
  typed derivation variants and immutable normalized destination slots are now
  validated before manager, lock, Git, or source work. The coordinator alone
  publishes single/pair payloads to bound slots; prepared test payloads reject
  lifetime callbacks, and repository opt-out skips Git only.
- Stage B added nonfallible precreated descriptor slots, immediate parent and
  staging namespace ownership, component-independent Git cleanup, and monotonic
  POSIX/Windows namespace, disposition, and fsync transitions. In particular,
  Windows recovery ownership is retained until disposition succeeds and is
  detached only before the consuming close.
- Stage C replaced whole-statement exception approximations with recursive,
  source-ordered exact throw-site snapshots consumed by handlers. The exact
  nested throw-site selector passed, and the preserved analyzer census remained
  reconciled.
- Final focused compatibility was Atomic 38/38 and DesignReview 21/21. The
  intentional old four-argument API reproductions are the only remaining legacy
  calls, and they reject before Git/source work.

### Final verification and frozen evidence

- Direct inventory/profile suite:
  `$env:PONTIUS_GIT=(Get-Command git).Source; python tests/test_inventory_and_profiles.py`
  passed 87/87 in 54.586 seconds, exit 0.
- Final isolated Python 3.11 snapshot
  `pontius-orch-task2-fix5-final2-correction-finalbytes-6f0127b2954b4a9f846eb37b7bea9cec`
  passed 87/87 in 66.260 seconds, exit 0, cleaned.
- Final configuration snapshot
  `pontius-orch-task2-fix5-final2-correction-finalbytes-config-109c97bef18b4e1aa896880095b06902`
  passed 53/53 in 0.283 seconds, exit 0, cleaned.
- Final H32 snapshot
  `pontius-orch-task2-fix5-final2-correction-finalbytes-h32-4e6168c02dc24b9ab409a48b20655ed7`
  ran 9: 8 passed and the one approved unconditional skip remained, exit 0,
  cleaned.
- Fresh ordinary `--write` and `--check` both exited 0. Generated SHA-256 values
  remained inventory
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`
  and profiles
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- Reconciliation remained 139 expanded rows, 2,578 deny-all rows, 93 blockers,
  subprocess census 42+4, 27 cross-file edges, 30 CuPy nodes, design digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  and analyzed-site digest
  `8219efd8ef8379ac071b687765eebd783319d15e5343911592ae92966d45cb71`.
  The 167 string-only decoys remained partitioned 17/6/26/118; their explained
  test-line digest moved to
  `7612598f08abb356dba066cebcd3cf7b8fcb9ea0cdeed98523cd6fbb52d2b86c`.
- Both capability digests and all capability-table counts remained zero.
  Cleanup-manager pending entries, worktree governance artifacts, and attribute
  temporary directories were all zero. AST parse passed 2/2; both edited Python
  files had zero BOM, CR, trailing whitespace, missing final LF, or lines over
  100 columns. `git diff --check` exited 0 with only the four existing
  line-ending advisories.
- Final SHA-256: generator
  `898f07a75e5ff493edccc2ca5c9f10ae2d040bf31f17ce427e3e64cc55683778`;
  tests
  `d66377c9842cf5785f9aafbecf7322f75ed4caed774d4156807026c794addaa9`.
- Immutable narrow correction:
  `task-2-fix5-final2-correction-review.patch`, 140,229 bytes, SHA-256
  `fbe26da30009419c13b23203af3c4252127822c006d306152374823e59c44657`,
  with four-file before/after snapshot
  `task-2-fix5-final2-correction-review-snapshot`.
- Immutable corrected full package:
  `task-2-fix5-final2-corrected-full-review.patch`, 486,217 bytes, SHA-256
  `2c10488c9397f556198676321b4b2d1c40bdf0b168868b5830a42c9b33c92d02`,
  with 16-file before/after snapshot
  `task-2-fix5-final2-corrected-full-review-snapshot`.

Concern: full scientific/GPU payload execution and the controller-owned final
CodeRabbit/frozen-candidate review remain intentionally outside this correction.

## Fix round 6 native ownership and analyzer correction

The prior corrected full candidate was rejected by fresh native and analyzer
review. This correction remained limited to the transaction/I/O owner state and
exact exceptional-successor preclassifier in
`tools/generate_test_inventory.py`, integrated private coverage in
`tests/test_inventory_and_profiles.py`, and this appended evidence. The other
six implementation/generated files were preserved byte-for-byte. No
scientific/GPU payload, capability approval/write, OneDrive access, CodeRabbit
run, commit, merge, push, or integration occurred.

### Rejected bytes, RED matrix, and root fixes

- The rejected generator and test SHA-256 values were confirmed as
  `898f07a75e5ff493edccc2ca5c9f10ae2d040bf31f17ce427e3e64cc55683778`
  and
  `d66377c9842cf5785f9aafbecf7322f75ed4caed774d4156807026c794addaa9`.
- The six-selector integrated RED matrix ran six tests with 16 intended
  assertion failures and zero errors. It covered immediate POSIX sealed
  descriptor, Windows ancestor/executable/CRT, and Windows publication-parent
  ownership; checked raw Windows Git close truth; deterministic-lock acquired
  truth; real staging, absent-target, and recovery pre-disposition/fail-before-
  close schedules; nested return/break/continue throw-site state; and actual
  governance-writer same-number owner-family reuse. The already-safe ambiguous
  close reuse schedules remained explicit production-path coverage rather than
  manufactured failures.
- Raw POSIX and Windows resources now adopt nonfallible precreated owner slots
  immediately at their acquisition boundary. Windows raw close results are
  checked, and native handles remain retry-owned after an explicit false result.
  Directory, Git, staging, published, recovery, and deterministic-lock roles no
  longer have a fallible wrapper-construction gap.
- Windows handle, namespace, disposition, renamed, and acquired states are
  independent and monotonic. Reporters and retry logic retain truthful staging,
  published, recovery, directory, and lock ownership without replaying an
  ambiguous numeric handle or inventing an unacquired destination lock.
- The preclassifier remains deliberately rim-scoped: it recursively propagates
  source-ordered normal, raise, return, break, and continue successors so only
  reachable throw-site snapshots enter handlers. It does not introduce a
  general control-flow graph or broaden analyzer authority.

### Fresh verification on final bytes

- Final focused six-selector result: 6/6 passed in 1.866 seconds. Full
  `AtomicAndGitBoundaryTests` plus `DesignReviewTests` passed 59/59 in 5.109
  seconds. The only compatibility update was the legacy recovery-open mock's
  new provisional `owner=` seam.
- Direct inventory/profile suite passed 87/87 in 49.745 seconds. Isolated
  Python 3.11 snapshot
  `pontius-orch-task2-fix6-native-analyzer-correction-finalbytes-b8b072597802425981fb1456b75ca95f`
  passed 87/87 in 59.191 seconds, exit 0, and cleaned.
- Configuration snapshot
  `pontius-orch-task2-fix6-native-analyzer-correction-config-18fb01eeafb746edb55b268bb72e7af3`
  passed 53/53 in 0.263 seconds, exit 0, and cleaned. H32 snapshot
  `pontius-orch-task2-fix6-native-analyzer-correction-h32-89a31037f4ff4449ab2014a14925ec04`
  ran 9 in 1.378 seconds: 8 passed and the one approved unconditional skip
  remained, exit 0, and cleaned.
- Ordinary all-zero `--write` and `--check` both exited 0. Inventory remained
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles remained
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- Reconciliation remains 139 expanded rows, 2,578 deny-all rows, 93 blockers,
  design digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  subprocess census 42+4, 27 cross-file edges, 30 CuPy nodes, and analyzed-site
  digest
  `8219efd8ef8379ac071b687765eebd783319d15e5343911592ae92966d45cb71`.
  The 167 string-only decoys remain partitioned 17/6/26/118; the explained
  test-line digest is
  `9dba7a7856e18c29ed44e97057771fef08b7f871784d1f114439e9ab7f743958`.
- Both capability digests and all three capability-table counts remain zero.
  Cleanup-manager pending entries/reservations, worktree governance artifacts,
  and attribute temporary directories are all zero. AST parse passed 2/2; both
  changed Python files have zero BOM, CR, trailing whitespace, missing final LF,
  or lines over 100 columns. `git diff --check` exited 0 with only the four
  existing line-ending advisories.
- Final eight-file SHA-256 values are: H32 test
  `51305e9f421a5c356e43a0d474393cec05b7431a02a0540603774f7c802d796b`;
  inventory/profile tests
  `7f70513dcf87b2823ac0adee9722f7dedcc5c9b5a55e8251dee7373783e6cc59`;
  configuration tests
  `ff0491e75d8143078305cc85ed47fae5e093e2ee85bf48a8eedff57c539929f2`;
  inventory
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`;
  generator
  `95b9e9a4eecf76abf217f1f6c9b841739f8923b44b04cde79a1bb9f2560afcc0`;
  configuration source
  `a1cef160d600b2fe35b67e0931c5227552fc03068be376097f2d6e102780c0d8`;
  and model source
  `83161fcb39c87008e6cf98f9f0d801abc99103484a2c40a799524e3e2cab0d32`.

Concern: full scientific/GPU payload execution and controller-owned frozen
candidate review remain intentionally outside this correction. Ambiguous close
exceptions still favor numeric reuse safety: the detached raw value is never
replayed; an explicit native false result remains strongly retry-owned.

### Immutable round-6 review packages

- Narrow rejected-to-corrected package:
  `task-2-fix6-native-analyzer-correction-review.patch`, 116,857 bytes,
  SHA-256
  `6e8dace143ba4c6ece8f77057bcb8b984eff854d5e1d92d0042ef1360f04c2bd`,
  with four-file before/after snapshot
  `task-2-fix6-native-analyzer-correction-review-snapshot`.
- Corrected full eight-file package:
  `task-2-fix6-native-analyzer-corrected-full-review.patch`, 575,439 bytes,
  SHA-256
  `2a9c3f63cae42ed1ddcf6adff56c00c14a04c511d98cde0fa3ac160c4494ce5c`,
  with 16-file before/after snapshot
  `task-2-fix6-native-analyzer-corrected-full-review-snapshot`.
- The narrow before snapshot exactly matches the rejected generator/test hashes
  `898f07a75e5ff493edccc2ca5c9f10ae2d040bf31f17ce427e3e64cc55683778`
  and
  `d66377c9842cf5785f9aafbecf7322f75ed4caed774d4156807026c794addaa9`;
  its after snapshot exactly matches the final source/test hashes recorded
  above. All eight full after-snapshot files match the live verified bytes.

## Fix round 7 finally and native ownership correction

Fresh frozen review rejected the round-6 candidate on exact exceptional-flow
and native ownership schedules. This correction remained limited to
`tools/generate_test_inventory.py`, integrated private coverage in
`tests/test_inventory_and_profiles.py`, and this appended evidence. The other
six implementation/generated files remained byte-for-byte unchanged. No
scientific/GPU payload, capability approval/write, OneDrive access, CodeRabbit
run, commit, merge, push, or integration occurred.

### Clean RED matrix and root fixes

- The rejected round-6 generator and test SHA-256 values were
  `95b9e9a4eecf76abf217f1f6c9b841739f8923b44b04cde79a1bb9f2560afcc0`
  and
  `7f70513dcf87b2823ac0adee9722f7dedcc5c9b5a55e8251dee7373783e6cc59`.
- The integrated three-selector RED matrix ran three tests with 24 intended
  assertion failures and zero errors across 28 named schedules. It covered all
  normal/raise/return/break/continue finally rims and override directions;
  call/await/yield exceptional successors under recognized `suppress`; the
  Windows Git-ancestor append and POSIX sidecar post-open gaps; transferred Git
  ancestor false/ambiguous close outcomes; writer-directory probe/final close;
  original/readback false close; and renamed staging, published, and restored
  recovery ambiguous close reconciliation. Four already-safe control schedules
  passed on rejected bytes.
- The preclassifier now transforms every incoming exit through `finally`
  independently. A normally completing final body preserves the transformed
  state on the original exit kind, while a terminal final-body exit replaces
  it. Locally captured call/await/yield exceptional snapshots under recognized
  `contextlib.suppress` join only its normal continuation. The change remains
  rim-scoped rather than introducing a general control-flow graph.
- Windows Git ancestor ownership is adopted before the fallible handle-list
  append. POSIX sidecar owner and namespace state are registered before open;
  the descriptor and lock name are adopted immediately after `O_EXCL` returns,
  before identity probing. Successful Git acquisition transfers owner objects,
  so an explicit native false remains retryable and an ambiguous close is never
  replayed.
- Publication-directory, original, readback, staging, published, and recovery
  handles now use provisional owner slots. Known false closes retain strong
  ownership. Ambiguous numeric handles are detached observation-only values:
  invalid or different-identity observations prove consumption, while same
  identity or probe failure remains explicitly pending with its exact role.
  Directory, file, namespace, disposition, and lock ownership remain monotonic.

### Fresh final-byte verification

- The final three-selector aggregate passed 3/3 in 1.394 seconds. Full
  `AtomicAndGitBoundaryTests` plus `DesignReviewTests`, with the required exact
  `PONTIUS_GIT`, passed 59/59 in 4.492 seconds. Two legacy directory-close mocks
  were updated to intercept the raw checked `CloseHandle` seam so known false
  and ambiguous exceptions remain distinguishable.
- Direct inventory/profile execution passed 87/87 in 51.136 seconds. Isolated
  Python 3.11 snapshot
  `pontius-orch-task2-fix7-finally-native-ownership-finalbytes-bfeefd51bc6c4e4083d7d1b0cd6d3322`
  passed 87/87 in 60.386 seconds, exit 0, and cleaned.
- Configuration snapshot
  `pontius-orch-task2-fix7-finally-native-ownership-config-3e09e3f6c1ba46a686df1cad77df32b9`
  passed 53/53 in 0.261 seconds, exit 0, and cleaned. H32 snapshot
  `pontius-orch-task2-fix7-finally-native-ownership-h32-23d4510f9fc945f2bf0d7a57e70cb947`
  ran 9 in 1.386 seconds: 8 passed and the one approved unconditional skip
  remained, exit 0, and cleaned.
- Ordinary all-zero `python -B -P tools/generate_test_inventory.py --write`
  and `--check` both exited 0. Inventory remained
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles remained
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- Reconciliation remains 139 expanded rows, 2,578 deny-all rows, 93 blockers,
  design digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  subprocess census 42+4, 27 cross-file edges, 30 CuPy nodes, and analyzed-site
  digest
  `8219efd8ef8379ac071b687765eebd783319d15e5343911592ae92966d45cb71`.
  The added regression text moves only the explained string-decoy census to
  168, partitioned 17/6/26/119, with digest
  `5baa919ed761b4a414b3896d294fc7263ac96671b608e4752a366af8d6602abf`.
- Both capability digests and all three capability-table counts remain zero.
  Cleanup-manager pending entries/reservations, worktree governance artifacts,
  and attribute temporary directories are all zero. AST parse passed 2/2; both
  changed Python files have zero BOM, CR, trailing whitespace, missing final
  LF, or lines over 100 columns. `git diff --check` exited 0 with only the four
  existing line-ending advisories.
- Final eight-file SHA-256 values are: H32 test
  `51305e9f421a5c356e43a0d474393cec05b7431a02a0540603774f7c802d796b`;
  inventory/profile tests
  `d19622528ade7ae657a01a7170415690c5769568195f3e5c6733556951ba8c4f`;
  configuration tests
  `ff0491e75d8143078305cc85ed47fae5e093e2ee85bf48a8eedff57c539929f2`;
  inventory
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`;
  generator
  `a71b77de36b0a7fa1a6b8056f1b4a3284379d2c5c2c8a6d2223cd68d37be1917`;
  configuration source
  `a1cef160d600b2fe35b67e0931c5227552fc03068be376097f2d6e102780c0d8`;
  and model source
  `83161fcb39c87008e6cf98f9f0d801abc99103484a2c40a799524e3e2cab0d32`.

Concern: full scientific/GPU payload execution and controller-owned frozen
candidate review remain outside this correction. Ambiguous close reconciliation
intentionally favors reuse safety: a detached numeric value is never closed or
replayed, and a same-identity observation remains pending rather than risking a
later owner.

### Immutable round-7 review packages

- Narrow rejected-to-corrected package:
  `task-2-fix7-finally-native-ownership-correction-review.patch`, 87,217
  bytes, SHA-256
  `191075aa11ee3c083a9dd117f4e35210126696f7516614888fff5db33c375b1d`,
  with four-file before/after snapshot
  `task-2-fix7-finally-native-ownership-correction-review-snapshot`.
- Corrected full eight-file package:
  `task-2-fix7-finally-native-ownership-corrected-full-review.patch`, 687,470
  bytes, SHA-256
  `1037c80a3f1b9b5b72cdf7397c32f030b910cdda46fceff2a5ed038009d4b27e`,
  with 16-file before/after snapshot
  `task-2-fix7-finally-native-ownership-corrected-full-review-snapshot`.
- The narrow before snapshot exactly matches the rejected round-6
  generator/test hashes, and the narrow after snapshot exactly matches the
  final verified generator/test hashes above. The full before snapshot exactly
  matches the prior full-candidate base, and all eight full after-snapshot files
  match the live verified bytes.

## Fix round 8 governed try-suite and Windows owner-identity correction

Fresh frozen review rejected the round-7 candidate on exceptional snapshots
originating in every governed `try` suite and on ambiguous Windows governance
handles whose identity had not yet been bound. This correction remained limited
to `tools/generate_test_inventory.py`, integrated private coverage in
`tests/test_inventory_and_profiles.py`, and this appended evidence. The other
six implementation/generated files remained byte-for-byte unchanged. No
scientific/GPU payload, capability approval/write, OneDrive access, CodeRabbit
run, commit, merge, push, or integration occurred.

### Clean RED matrix and root fixes

- The rejected round-7 generator and test SHA-256 values were
  `a71b77de36b0a7fa1a6b8056f1b4a3284379d2c5c2c8a6d2223cd68d37be1917`
  and
  `d19622528ade7ae657a01a7170415690c5769568195f3e5c6733556951ba8c4f`.
- The two-selector integrated RED matrix ran two tests with 28 intended
  assertion failures and zero errors across 40 named schedules. The analyzer
  table contributed 34 real-AST/reconciliation schedules: call, await, and
  yield-from exceptional snapshots from protected bodies, each handler, else,
  and nested governing final bodies in both disposition directions, plus
  bare/typed/multiple-handler and nested-suppress controls. The Windows table
  contributed six real-writer same-numeric-handle reuse schedules for staging,
  original, recovery, published, readback, and published-disposal owners.
- The preclassifier now captures protected-body, handler, and else implicit
  throws in their own regions. Protected-body throws alone feed this try's
  bounded handler model and are consumed when handlers exist; handler- and
  else-originated throws bypass sibling handlers. Every outgoing normal, raise,
  return, break, and continue state traverses each governing final body exactly
  once, while a final body's own exceptional successor goes directly outward.
  This remains an exact exceptional-rim model rather than a general CFG.
- Every Windows governance file handle binds its native file identity
  immediately after owner adoption, before returning to fallible caller work.
  Ambiguous close reconciliation is identity-first. The only identity-unbound
  fallback is absence of that owner's own disposition-armed namespace; a
  namespace-free role never uses path-only reconciliation. Recovery cleanup
  also resolves an ambiguous disposition close before any reacquisition, so a
  consumed name is not recreated and no reused numeric handle is closed.

### Fresh final-byte verification

- The focused analyzer selector passed its 34 schedules; the Windows selector
  passed its six-family table; and the combined exact two-selector command
  passed 2/2 in 0.316 seconds. Full `AtomicAndGitBoundaryTests` plus
  `DesignReviewTests`, with exact `PONTIUS_GIT`, passed 59/59 in 5.080 seconds.
- Direct inventory/profile execution passed 87/87 in 50.766 seconds. Isolated
  Python 3.11 snapshot
  `pontius-orch-task2-fix8-try-suites-file-identity-finalbytes-a63c7e58-1757f34322b342af93d48bb0e3f2e829`
  passed 87/87 in 60.934 seconds, exit 0, and cleaned.
- Configuration snapshot
  `pontius-orch-task2-fix8-try-suites-file-identity-config-a63c7e58-24a6a9968d3443829d38c380aa1d0cef`
  passed 53/53 in 0.250 seconds, exit 0, and cleaned. H32 snapshot
  `pontius-orch-task2-fix8-try-suites-file-identity-h32-a63c7e58-e1e8f63c2d4e4a748e88a913c2cad057`
  ran 9 in 1.389 seconds: 8 passed and the one approved unconditional skip
  remained, exit 0, and cleaned.
- Ordinary all-zero `python -B -P tools/generate_test_inventory.py --write`
  and `--check` both exited 0. Inventory remained
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles remained
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- Reconciliation remains 139 expanded rows, 2,578 deny-all rows, 93 blockers,
  design digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  subprocess census 42+4, 27 cross-file edges, 30 CuPy nodes, and analyzed-site
  digest
  `8219efd8ef8379ac071b687765eebd783319d15e5343911592ae92966d45cb71`.
  The new integrated regression text moves only the string-decoy census to 170,
  partitioned 17/6/26/121, with digest
  `5f99a466945915d04758c08d29c7455b9bdd154bffa18c57ff988dbf7fe48293`.
- Both capability digests and all three capability-table counts remain zero.
  The in-process ordinary check ended with zero cleanup-manager reservations and
  pending entries. Worktree governance artifacts and attribute temporary
  directories are both zero. AST parse passed 2/2; both changed Python files
  have zero BOM, CR, trailing whitespace, missing final LF, or lines over 100
  columns. `git diff --check` exited 0 with only the four existing line-ending
  advisories.
- Final eight-file SHA-256 values are: H32 test
  `51305e9f421a5c356e43a0d474393cec05b7431a02a0540603774f7c802d796b`;
  inventory/profile tests
  `5d3cd6669acfb82aaf4d09374bdd529f2e9ecf91c41d055ea401c4defd4c26d5`;
  configuration tests
  `ff0491e75d8143078305cc85ed47fae5e093e2ee85bf48a8eedff57c539929f2`;
  inventory
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`;
  generator
  `20a3da863ecfc8d31d5f5935610d0aae7b55c4ed862f94f06fe98f618fe4a5ac`;
  configuration source
  `a1cef160d600b2fe35b67e0931c5227552fc03068be376097f2d6e102780c0d8`;
  and model source
  `83161fcb39c87008e6cf98f9f0d801abc99103484a2c40a799524e3e2cab0d32`.

Concern: full scientific/GPU payload execution and controller-owned frozen
candidate review remain outside this correction. Ambiguous Windows handles stay
pending when identity is unavailable and no owner-specific disposition-armed
namespace absence proves consumption; this deliberately favors reuse safety.

### Immutable round-8 review packages

- Narrow rejected-to-corrected package:
  `task-2-fix8-try-suites-windows-identity-correction-review.patch`, 34,514
  bytes, SHA-256
  `21d67c5f0567d3ae908109fdd330d941cc334074d6c04e1c7ab907fb6ffffb57`,
  with four-file before/after snapshot
  `task-2-fix8-try-suites-windows-identity-correction-review-snapshot` and
  sorted manifest SHA-256
  `e2d2ed5efe3c0c42d14b76572845ad4f8d38aae1b1149396b23d1b2207a3b057`.
- Corrected full eight-file package:
  `task-2-fix8-try-suites-windows-identity-corrected-full-review.patch`, 34,546
  bytes, SHA-256
  `d6a8f4cb7b777f7e319011f68b603ae9fdd8c21d307f14561d70ffa10cfe7307`,
  with 16-file before/after snapshot
  `task-2-fix8-try-suites-windows-identity-corrected-full-review-snapshot` and
  sorted manifest SHA-256
  `aaf2d2c911765b46375a8bf95a0ae7ea4a1f2be81eddb3d3c0200d0f63969712`.
- All four snapshot comparisons are exact: both narrow/full before trees match
  the rejected round-7 full after tree, and both narrow/full after trees match
  the final verified live bytes, with zero mismatches.

### Round-8 cumulative full-package correction

The 34,546-byte round-8 `corrected-full` package above is retained immutably,
but its before tree is the round-7 after tree, so it represents only the final
narrow correction. The cumulative full-review baseline is instead
`task-2-fix4-review-snapshot/after`; all eight of its files exactly match the
round-7 full package's before tree. Its baseline generator/test hashes are
`5f4015d5a81ace581685bf62f8944a8489ba48b1d2f0130966551baf493dc2cf`
and
`10f56c29c45723bbae31cca3d6d44fd294fa4f5659ef596c8ebea1a72a834117`.

The replacement cumulative evidence is
`task-2-fix8-try-suites-windows-identity-corrected-cumulative-full-review.patch`,
731,202 bytes, SHA-256
`034f0b84f33d4df4b30f8f27094ec05234bbc223a51e1d0276a802a1cd15fdb4`,
with sibling 16-file snapshot
`task-2-fix8-try-suites-windows-identity-corrected-cumulative-full-review-snapshot`.
Its before, after, and complete sorted manifest SHA-256 values are respectively
`023dca0ced3414d9951a2ee96d9cc628987dc8453e162e62fa9f364b6d3149bc`,
`1ca1caa2ad5cdbdc0ab1dc03944e0936e9dfdb10684a7f4d6e457845287808ff`,
and
`a23bd4ebcb56a5e66daa324d9ae6a42ed78647f217ddee66f478c4b1916fce46`.

Every before hash matches the fix4 baseline and every after hash matches the
verified live source. The cumulative diff contains only
`tests/test_inventory_and_profiles.py` (8,269 insertions, 2,080 deletions) and
`tools/generate_test_inventory.py` (4,002 insertions, 635 deletions): two files,
12,271 insertions, and 2,715 deletions. H32 test
`51305e9f421a5c356e43a0d474393cec05b7431a02a0540603774f7c802d796b`,
configuration test
`ff0491e75d8143078305cc85ed47fae5e093e2ee85bf48a8eedff57c539929f2`,
inventory
`0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`,
profiles
`2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`,
configuration source
`a1cef160d600b2fe35b67e0931c5227552fc03068be376097f2d6e102780c0d8`,
and model source
`83161fcb39c87008e6cf98f9f0d801abc99103484a2c40a799524e3e2cab0d32`
are byte-identical across the cumulative boundary. The report is evidence
metadata only and is absent from the patch and both snapshot sides.

## Fix round 9 typed-handler and native owner-reconciliation correction

Fresh frozen review rejected the round-8 candidate on typed handler routing,
Windows disposition ownership under same-inode handle reuse, pre-close identity
binding, and two orphaned private regression helpers. This correction remained
limited to `tools/generate_test_inventory.py`, integrated private coverage in
`tests/test_inventory_and_profiles.py`, and this appended evidence. The other
six implementation/generated files remained byte-for-byte unchanged. No
scientific/GPU payload, capability approval/write, OneDrive access, CodeRabbit
run, commit, merge, push, or integration occurred.

### Clean RED matrix and root fixes

- The rejected round-8 generator and test SHA-256 values were
  `20a3da863ecfc8d31d5f5935610d0aae7b55c4ed862f94f06fe98f618fe4a5ac`
  and
  `5d3cd6669acfb82aaf4d09374bdd529f2e9ecf91c41d055ea401c4defd4c26d5`.
- The exact three-selector integrated RED matrix ran three discovered tests
  with 11 intended assertion failures and zero errors. Four analyzer failures
  covered definite nonmatching outer propagation, ordered later matches, tuple
  nonmatches, and unknown explicit raises. Three real Windows writer failures
  covered same-inode exact-handle reuse after staging, published-disposal, and
  recovery dispositions. Four more real writer failures covered identity-probe
  failure before close for original, readback, published, and staging owners.
  The owned-name-present control and the active POSIX/Git replacement schedules
  already passed.
- Explicit syntactic built-in raises now carry a bounded exception tag through
  both analyzers. Bare handlers, tuples, exact built-ins, and a closed literal
  built-in ancestry produce definite match/nonmatch decisions. A definite
  match consumes and stops handler traversal; a definite nonmatch reaches later
  or outer handlers. An unknown explicit relation forks handled and unmatched
  successors so it cannot silently remove a reachable sensitive site. Implicit
  call/await/yield exceptions retain the existing bounded handler model.
- A disposition-armed Windows owner with its own namespace resolves an
  ambiguous close from verified absence of that exact artifact before looking
  at numeric-handle identity. The exact name remaining, or a namespace probe
  failure, stays pending without replay. Namespace-free owners remain strictly
  identity-bound. Every adopted unbound file owner now retries and binds native
  identity before any consuming close; identity failure retains the live handle
  and its exact role.
- The two unreachable `_final*` helpers were removed. Their intended contracts
  are asserted by discovered real POSIX rollback and real multi-component Git
  acquisition schedules. A bytecode reachability guard now requires every
  binding-marked `_final*`/`_round*` helper to be reachable from a discovered
  `test_*` method and rejects direct references to removed generator symbols.

### Fresh final-byte verification

- The focused three-selector aggregate passed 3/3 in 1.832 seconds. Full
  `AtomicAndGitBoundaryTests` plus `DesignReviewTests`, with exact
  `PONTIUS_GIT`, passed 59/59 in 5.160 seconds.
- Direct inventory/profile execution passed 87/87 in 51.660 seconds. Isolated
  Python 3.11 snapshot
  `pontius-orch-task2-fix9-typed-handlers-native-owner-finalbytes-c083eeaecf7f4ffa9cb787b7a7cd4cf0`
  passed 87/87 in 61.626 seconds, exit 0, and cleaned.
- Configuration snapshot
  `pontius-orch-task2-fix9-typed-handlers-native-owner-config-663c6ca063f2460997711fee98fd901a`
  passed 53/53 in 0.399 seconds, exit 0, and cleaned. H32 snapshot
  `pontius-orch-task2-fix9-typed-handlers-native-owner-h32-952a076737804ca7aa787b811c141676`
  ran 9 in 1.403 seconds: 8 passed and the one approved unconditional skip
  remained, exit 0, and cleaned.
- Ordinary all-zero `python -B -P tools/generate_test_inventory.py --write`
  and `--check` both exited 0. Inventory remained
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles remained
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- Reconciliation remains 139 expanded rows, 2,578 deny-all rows, 93 blockers,
  design digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  subprocess census 42+4, 27 cross-file edges, 30 CuPy nodes, and analyzed-site
  digest
  `8219efd8ef8379ac071b687765eebd783319d15e5343911592ae92966d45cb71`.
  Only the explained regression string-decoy census moved to 171, partitioned
  17/6/26/122, with digest
  `c7deab262998630ef0c2073033d887e92aa2e5a3ca08bca9faeda6cd24d17798`.
- Both capability digests and all three capability-table counts remain zero.
  Cleanup-manager pending entries/reservations, worktree governance artifacts,
  and attribute temporary directories are all zero. AST parse passed 2/2; both
  changed Python files have zero BOM, CR, trailing whitespace, missing final
  LF, or lines over 100 columns. `git diff --check` exited 0 with only the four
  existing line-ending advisories.
- Final eight-file SHA-256 values are: H32 test
  `51305e9f421a5c356e43a0d474393cec05b7431a02a0540603774f7c802d796b`;
  inventory/profile tests
  `4a91375315f032e98ca4adc72625e3a166c9e52e71bea37d1dbdaced12f8feca`;
  configuration tests
  `ff0491e75d8143078305cc85ed47fae5e093e2ee85bf48a8eedff57c539929f2`;
  inventory
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`;
  generator
  `e6ce3491b1a5ef69df4856e874af3acc9c0251d0382cf1a37df5a18f8b9bd961`;
  configuration source
  `a1cef160d600b2fe35b67e0931c5227552fc03068be376097f2d6e102780c0d8`;
  and model source
  `83161fcb39c87008e6cf98f9f0d801abc99103484a2c40a799524e3e2cab0d32`.

Concern: full scientific/GPU payload execution and controller-owned frozen
candidate review remain outside this correction. Unknown explicit exception
relations deliberately fork both successors, which can over-approximate but
cannot hide a reachable sensitive site. Namespace-free ambiguous Windows
handles remain pending unless identity proves that the original was consumed.

### Immutable round-9 review packages

- Narrow rejected-to-corrected package:
  `task-2-fix9-typed-handlers-native-owner-correction-review.patch`, 66,860
  bytes, SHA-256
  `17baa6a1fee34c1625f195254269bf5978ab97a5eea89a5ccd94b1dfaae040d5`,
  with four-file before/after snapshot
  `task-2-fix9-typed-handlers-native-owner-correction-review-snapshot`.
  Its before, after, and complete sorted manifest SHA-256 values are
  `960ffd39fe994c6f65cf1e306c89b0b89609d60fb12db2026aad50474b794fd8`,
  `2f90a0080afa0210deabb6acfe42e00c54718ffa696954480948c823482fd686`,
  and
  `81ad273d4d46eb87f4c8d82b8d42131bff170ee737180c236fa4a92cbcb0ca8b`.
  The narrow diff contains only the generator and inventory/profile tests: 926
  insertions and 171 deletions.
- Correct cumulative full package, directly based on
  `task-2-fix4-review-snapshot/after`:
  `task-2-fix9-typed-handlers-native-owner-corrected-cumulative-full-review.patch`,
  771,305 bytes, SHA-256
  `d8d4c04ec8e795e667124fa3b10d8ac292eb4689ec798424e6817ec1cc8fd460`,
  with sibling 16-file snapshot
  `task-2-fix9-typed-handlers-native-owner-corrected-cumulative-full-review-snapshot`.
  Its before, after, and complete sorted manifest SHA-256 values are
  `f1a8e0ffecc1ca5acbd598c47f0d66e9983f2abf5f550784e97e6fb6d9f572c7`,
  `0bebb6df98e2f999d34b0e6cf21b1ed3c2c94b24427f520f5b2a42078ad50d8c`,
  and
  `d2aefdcf63749157240017a4ab72458f1211d2066cf71bcdc77204b57bec3790`.
  Its diff contains only the generator and inventory/profile tests: 13,053
  insertions and 2,742 deletions.
- Every narrow before hash matches the rejected round-8 after tree; every
  cumulative before hash matches the fix4 review baseline; and all narrow/full
  after files exactly match the verified live bytes. Generated, configuration,
  model, and H32 bytes are identical across the cumulative boundary. The report
  is evidence metadata only and is absent from both patches and snapshot sides.

## Fix round 5 round-10 typed-handler provenance correction

The round-9 frozen candidate was rejected because syntactic built-in exception
spellings were treated as built-ins even when lexical bindings shadowed them.
The correction now proves built-in provenance from a bounded function-scope
binding census before tagging either a raised name or a handler tuple element.
Parameters, assignments (including annotated and walrus targets), imports,
loop/with/match/exception targets, function/class bindings, globals, nonlocals,
and enclosing bindings all prevent an unproved spelling from becoming a
definite built-in. Ambiguity remains the existing conservative handled plus
unmatched fork; no exception-class inference engine was added.

Handler-target validation is now an independent successor. A definitely invalid
constant or tuple emits an explicit built-in `TypeError` that bypasses sibling
handlers. A dynamic target forks validation `TypeError` plus the valid
match/nonmatch possibilities. Fresh CPython 3.14.6 runtime evidence overrode an
initial proposed left-to-right tuple rule: both `(RuntimeError, 1)` and
`(1, RuntimeError)` raise `TypeError`, so any definitely invalid tuple element is
decisive regardless of position. Fallible evaluation beneath a proven explicit
raise constructor, or in its cause, now preserves an unknown pre-raise successor;
simple built-in names and constructors retain exact tags. The preclassifier also
joins explicit `flow.raises` from handler, else, and finally regions exactly once,
matching the already-correct body channel and finalbody override semantics.

### Round-10 RED and final-byte verification

- Frozen production
  `e6ce3491b1a5ef69df4856e874af3acc9c0251d0382cf1a37df5a18f8b9bd961`
  ran one discovered public selector containing 24 new real-runtime, real-AST,
  direct-analyzer, and reconciliation schedules: 17 intended assertion failures,
  zero errors, and seven adjacent controls already green. The failures comprised
  eight lexical/raised-side provenance schedules, four validation schedules,
  two pre-raise evaluation schedules, and three missing explicit-exit channels.
- The final focused selector passed 1/1 in 0.121 seconds. The focused selector
  plus full `DesignReviewTests` and `AtomicAndGitBoundaryTests` passed 60/60 in
  11.779 seconds; the nonduplicated two-class gate passed 59/59 in 5.018 seconds.
- Direct inventory/profile execution passed 87/87 in 61.762 seconds. Isolated
  Python 3.11 snapshot
  `pontius-orch-task2-fix10-exception-provenance-validation-finalbytes-e444e6e69b8047a99bf256b19afd0b6d`
  passed 87/87 in 63.901 seconds, exit 0, and cleaned.
- Configuration snapshot
  `pontius-orch-task2-fix10-exception-provenance-validation-config-09212ba9dc2348a783d7ccf9f40208cc`
  passed 53/53 in 0.264 seconds. H32 snapshot
  `pontius-orch-task2-fix10-exception-provenance-validation-h32-6a8f3be24b0942128277874084e04722`
  ran nine in 1.378 seconds: eight passed and the one approved unconditional skip
  remained. Both snapshots exited 0 and cleaned.
- Ordinary all-zero `python -B -P tools/generate_test_inventory.py --write` and
  `--check` exited 0. Inventory remained
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles remained
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- Reconciliation remains 139 expanded rows, 2,578 deny-all rows, 93 blockers,
  design digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  subprocess census 42+4, 27 cross-file edges, 30 CuPy nodes, and analyzed-site
  digest
  `8219efd8ef8379ac071b687765eebd783319d15e5343911592ae92966d45cb71`.
  Only regression string decoys moved to 176, partitioned 17/6/26/127, digest
  `a4f316fe5d98f00d46571b22f958b0eb1e7dcf489563653ad51b6a0e75b1daba`.
- Capability counts remain 0/0/0 and both digests remain all-zero. Cleanup-manager
  reservations/pending entries, bytecode caches, and governance artifacts are
  zero. Both changed Python files parse; BOM, CR, trailing whitespace, missing
  final LF, and over-100-column counts are zero. `git diff --check` exited 0 with
  only the four pre-existing line-ending advisories.
- Final eight-file SHA-256 values are: H32 test
  `51305e9f421a5c356e43a0d474393cec05b7431a02a0540603774f7c802d796b`;
  inventory/profile tests
  `c1dfc581c764a4b502c41d9a1b612ff1be5e365646ad1f0340cc31ced97455a1`;
  configuration tests
  `ff0491e75d8143078305cc85ed47fae5e093e2ee85bf48a8eedff57c539929f2`;
  inventory
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`;
  generator
  `68067254681ff7df1347fd98766f7ebd3bb7cd7d1738e39777f086c5d3ca1ffb`;
  configuration source
  `a1cef160d600b2fe35b67e0931c5227552fc03068be376097f2d6e102780c0d8`;
  and model source
  `83161fcb39c87008e6cf98f9f0d801abc99103484a2c40a799524e3e2cab0d32`.

### Immutable round-10 review packages

- Narrow round-9-to-round-10 package
  `task-2-fix10-exception-provenance-validation-correction-review.patch` is
  49,398 bytes, SHA-256
  `5a03aaa3006c8421ea9df17c438f25d751e16d1f81e6d834ee69296a87f3f356`,
  with four-file sibling snapshot
  `task-2-fix10-exception-provenance-validation-correction-review-snapshot`.
  Before, after, and complete ordinally sorted manifest digests are
  `2f90a0080afa0210deabb6acfe42e00c54718ffa696954480948c823482fd686`,
  `8d7e8dda0d0fdc2121268d4dc82404bbd62206c159316f7a62d852f375b6df0a`,
  and `d5e26add6e22c832d27a2e3113c33bc557f192bc0a3eb739af263eb7436985ea`.
  The two-file diff contains 953 insertions and 37 deletions.
- Correct cumulative package, directly based on
  `task-2-fix4-review-snapshot/after`,
  `task-2-fix10-exception-provenance-validation-corrected-cumulative-full-review.patch`
  is 807,034 bytes, SHA-256
  `c4c29c87c614acdbd54b38ff0ab0a39bd94cc7102a47260244f91a5c85fd528c`,
  with 16-file sibling snapshot
  `task-2-fix10-exception-provenance-validation-corrected-cumulative-full-review-snapshot`.
  Before, after, and complete ordinally sorted manifest digests are
  `f1a8e0ffecc1ca5acbd598c47f0d66e9983f2abf5f550784e97e6fb6d9f572c7`,
  `0409393b90d1c71b002cd630e4da66461601fe451bdee4ca2ef67c49eaa79fe5`,
  and `99469164c0759224e1be36c30f48cacbea6729703fb72eec1365794cbe3299d9`.
  Its two-file diff contains 13,978 insertions and 2,751 deletions.
- Every narrow before file matches the rejected round-9 after tree; every
  cumulative before file matches the fix4 review baseline; every after file
  matches verified live bytes. Generated, configuration, model, and H32 bytes
  are identical across the cumulative boundary. The report remains evidence
  metadata and is not included in either source patch or snapshot side.

Concern: full scientific/GPU payload execution and controller-owned candidate
review remain outside this correction. Dynamic or shadowed exception targets
are intentionally over-approximated; they cannot authorize or hide a reachable
sensitive site, but may retain conservative extra successors.

## Fix round 5 round-11 exception-routing provenance correction

The round-10 frozen candidate was rejected on seven bounded analyzer groups:
incomplete module and enclosing lexical provenance, expression and name-lookup
exceptions around `raise` and handler targets, handler/cause validation, exact
`contextlib.suppress` argument semantics, and implicit call/await/yield residual
routing through typed handlers. Native transaction/I/O review was clean and no
native ownership, lock, publication, or cleanup code was changed in this round.
Work remained limited to the analyzer portions of
`tools/generate_test_inventory.py`, integrated private coverage in
`tests/test_inventory_and_profiles.py`, the locked census digest in that test,
and this evidence append.

### Clean RED matrix and bounded correction

- Frozen round-10 production had generator SHA-256
  `68067254681ff7df1347fd98766f7ebd3bb7cd7d1738e39777f086c5d3ca1ffb`.
  One discovered public selector contained 82 real-runtime, real-AST,
  direct-preclassifier, direct-resolver, and full-reconciliation schedules.
  Before production edits it produced 50 intended assertion failures, zero
  errors, and 32 adjacent controls already green: provenance was 6/25 green,
  evaluation/validation was 15/38 green, and routing/suppress was 11/19 green.
- A complete module binder census now includes assignment variants, imports and
  conservative star imports, loop/with/match/exception targets, named
  expressions including comprehension walrus effects, and function, async
  function, and class names without descending into nested executable scopes.
  Function, async-function, and Lambda identities carry the relevant enclosing
  function binders; class bodies contribute no closure bindings. Relevant
  `global` declarations remain conservative unknowns. Provenance ambiguity is
  never promoted to a built-in spelling.
- Exception evaluation uses a closed proven-nonthrowing whitelist at the
  raise-expression, cause, and handler-target seams. Nontrivial expressions and
  unbound/shadowed name lookups preserve an unknown exceptional successor before
  validation. Successful handler and cause validation independently classify
  proven built-in classes/instances, definite invalid values, and unknowns;
  invalid handlers never make their bodies reachable.
- Implicit call/await/yield exceptions retain typed-handler exclusions as
  distinct successor facts. Exclusions are never union-merged, survive finally
  transformation, and use only the closed built-in hierarchy to prove a later
  nonmatch. Bare handlers and the approved `Exception`/`BaseException` broad
  cases consume; narrower unknown relations retain both handled and unmatched
  alternatives. The real corpus audit found 745 structural sites and 2,830
  implicit nodes repository-wide (139 and 197 in the inventory tests), so this
  constrained representation avoided a materially disruptive generic blocker.
- Recognized `contextlib.suppress` calls now evaluate and match their actual
  arguments. Zero arguments propagate. Explicit match/nonmatch and unknown
  branches use the same lexical provenance, while the suppress tuple is ordered
  and recursive according to the observed CPython 3.14.6 `issubclass` oracle:
  `(RuntimeError, [])` suppresses a `RuntimeError`, but
  `([], RuntimeError)` and `(ValueError, [])` reach invalid `[]` and raise
  `TypeError`. This deliberately differs from `except` tuple validation, where
  either invalid-element order raises `TypeError`.
- The source-ordered review coordinator now requires an authoritative flow
  snapshot before resolving any call. It therefore cannot resurrect a call
  that both the source-ordered flow and independent census proved unreachable.
  The final focused selector passed all 82 schedules; the final-byte
  `DesignReviewTests` plus `AtomicAndGitBoundaryTests` gate passed 59/59 in
  13.471 seconds.

### Fresh final-byte verification

- Direct inventory/profile execution passed 87/87 in 73.918 seconds using a
  same-volume isolated temporary root. Isolated snapshot
  `pontius-orch-task2-fix11-exception-routing-finalbytes-910669cf9a4b4882b61fec966fac5a7a`
  passed 87/87 in 74.594 seconds, exit 0, and cleaned. A discarded first direct
  attempt inherited a cross-volume `C:` temp root and therefore could not create
  the test's real hard link; it also exposed the expected locked census movement.
- Configuration snapshot
  `pontius-orch-task2-fix11-exception-routing-config-aa0215d8bf304c9d89fb9060025cbe50`
  passed 53/53 in 0.283 seconds, exit 0, and cleaned. H32 snapshot
  `pontius-orch-task2-fix11-exception-routing-h32-f8f85d4776a545f8888c59bd4cdcec9a`
  ran nine in 1.384 seconds: eight passed and the one approved unconditional skip
  remained, exit 0, and cleaned.
- Ordinary all-zero `python -B -P tools/generate_test_inventory.py --write` and
  `--check` both exited 0. Inventory remained
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles remained
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`.
- Reconciliation remains 139 expanded rows, 2,578 deny-all rows, 93 blockers,
  design digest
  `1d8bd7458a42e265857e9b8d8f2f3498c511e640ef11a3e7919c181a70a97764`,
  subprocess census 42+4, 27 cross-file edges, and 30 CuPy nodes. The explained
  regression-string census is 178, partitioned 17/6/26/129, with digest
  `1400de4bdcd16f100868eb881801652300243c8a1e1b8e4b68e5e4f3927b4855`;
  analyzed-site digest is
  `2b5b4a125c9be60bbe65478c89b02cf0d5a93104f2c5af5e7e1c05e15ef5fbe7`.
- Capability tables remain 0/0/0 and both capability digests remain all-zero.
  Cleanup-manager reservations/pending entries, bytecode caches, and worktree
  governance artifacts are all zero. Six Python files parse; the changed
  generator and inventory test have zero BOM, CR, trailing whitespace, missing
  final LF, or lines over 100 columns. `git diff --check` exited 0 with only the
  four pre-existing line-ending advisories.
- Final eight-file SHA-256 values are: H32 test
  `51305e9f421a5c356e43a0d474393cec05b7431a02a0540603774f7c802d796b`;
  inventory/profile tests
  `560ea9265eaacab27a9937573b77e992d480958e55843dd19ee7e51ef98673a2`;
  configuration tests
  `ff0491e75d8143078305cc85ed47fae5e093e2ee85bf48a8eedff57c539929f2`;
  inventory
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
  profiles
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`;
  generator
  `416f95a02f8e8240aea3e775ed01369f3d97f6f1a09d23a12dfbf00f5af87c5a`;
  configuration source
  `a1cef160d600b2fe35b67e0931c5227552fc03068be376097f2d6e102780c0d8`;
  and model source
  `83161fcb39c87008e6cf98f9f0d801abc99103484a2c40a799524e3e2cab0d32`.

### Immutable round-11 review packages

- Narrow round-10-to-round-11 package
  `task-2-fix11-exception-routing-correction-review.patch` is 119,078 bytes,
  SHA-256
  `02738111975e2129224393c2651364e00537b0931c9316d2da438a1d5998c245`,
  with four-file sibling snapshot
  `task-2-fix11-exception-routing-correction-review-snapshot`. Before, after,
  and complete ordinally sorted manifest digests are
  `8d7e8dda0d0fdc2121268d4dc82404bbd62206c159316f7a62d852f375b6df0a`,
  `c2fb34445724e33479e0a8695c29b292fe3cdeaa4974d9c036b25e47c1bd70aa`,
  and `2f25b68e338f5a7cb15e244957bb0c2da31619b0b4a73b8e5cc54fe21c75db20`.
  The two-file diff contains 2,445 insertions and 112 deletions.
- Correct cumulative package, directly based on
  `task-2-fix4-review-snapshot/after`,
  `task-2-fix11-exception-routing-corrected-cumulative-full-review.patch` is
  897,514 bytes, SHA-256
  `2549dcee61a1df18558b9f8ae73f073e287768df1a91f3d0f55f6a51f7b8ae70`,
  with 16-file sibling snapshot
  `task-2-fix11-exception-routing-corrected-cumulative-full-review-snapshot`.
  Before, after, and complete manifest digests are
  `f1a8e0ffecc1ca5acbd598c47f0d66e9983f2abf5f550784e97e6fb6d9f572c7`,
  `fbaa347366bff32bfaa9a1a55ac07af59d961134b03985dbe89c65a6f5f62121`,
  and `35d5361e0a6522ce3b8e72234999811a9754387e6fc4092425c3112191a7d202`.
  Its diff contains only the generator and inventory/profile tests: 16,313
  insertions and 2,753 deletions.
- Every narrow before hash matches the rejected round-10 after tree; every
  cumulative before hash matches the fix4 baseline; every after hash matches
  the verified live bytes. Generated inventory/profile, configuration/model,
  configuration-test, and H32 bytes are identical across the cumulative
  boundary. The report is evidence metadata only and is absent from both source
  patches and snapshot sides.

Concern: full scientific/GPU payload execution and controller-owned frozen
candidate review remain outside this correction. Unknown exception relations
remain conservative alternatives, but source-proven negative constraints keep
them from reviving an exception already excluded by an exact typed handler.

## Round-11 frozen verdict and round-12 complete RED matrix

Two independent immutable reviews rejected the exact round-11 candidate. Both
returned OPEN with no Critical findings and six Important Stage-C groups:
direct-`BaseException` residual routing; source-point binding/delete/alias
state; exception-instance identity; ordered expression/no-normal flow;
generator construction versus consumption; and truthful container/exception
metadata. The binding scope and explicit non-goals are recorded in
`task-2-fix12-final-analyzer-review-findings.md` (SHA-256
`058aaf00967af527163b1f502e138264fc068f04d5b1a282609c9bf40b1b6f9e`).

Before any production edit, the complete union test file had SHA-256
`64ec4868f6146042d8ff534949d72506043f01f4c948de1c8f2c386fbfa8a347`;
the generator remained
`416f95a02f8e8240aea3e775ed01369f3d97f6f1a09d23a12dfbf00f5af87c5a`.
The controller independently ran the public selector and reproduced one test
with 54 intended assertion failures, zero errors, and exit 1. Every schedule
uses the real CPython path, independent preclassifier, resolver, and full
census/resolver reconciliation; adjacent controls remain green. The bounded
production correction is now authorized, but no CodeRabbit run, commit, or
integration is authorized until the next exact candidate passes both frozen
direct reviews.

## Round-12 first GREEN rejection and corrected RED union

The first bounded production pass changed analyzer ranges only and produced
generator SHA-256
`d156e5c963d2661b8632d68e0d64fc24bccc5c2db9fea4d90b167e95b6519af8`.
It passed the then-current focused selector, parsed successfully, and left the
native transaction/publication implementation unchanged. It was not frozen for
acceptance: two independent pre-freeze semantic reviews returned OPEN with no
Critical findings and five Important groups each.

The overlapping findings reduce to a finite set of control/state mechanisms:
definition-point and call-shape binding for local must-raise summaries;
source-ordered eager/deferred expression outcomes; fork/join semantics for
optional branches and walrus effects; source-aware deletion and value-less
annotation boundness; canonical built-in exception identity plus bounded
constructor safety; cardinality, filter, alias, and exhaustion state for the
supported direct-`next` generator form; stable fail-closed blockers when a
generator escapes that form; accumulation of every state reaching the same
call AST; and successor-aware evaluation of loop and match control expressions.
No general CFG or generator-protocol expansion is authorized.

Several first-draft regressions did not distinguish the required production
behavior. Those oracles were replaced with real execution schedules: the
value-less annotation case now observes whether an existing handler binding is
preserved; empty/filter/exhausted generators now observe actual state and exact
`StopIteration`; repeated-snapshot paths bind an opaque runtime condition; and
unsupported generator consumers execute a real counting CuPy substitute.
This applies the binding pre-seal rule that a helper double or state-shape test
does not discharge an ownership or flow contract.

The corrected public selector contains 104 schedules/contracts. Its exact test
SHA-256 is
`b95421b61972ff606f400d7b57a78db56de0a37f0a85e40244701deddba4af39`.
Against unchanged generator `d156e5c...6519af8`, the controller independently
ran:

`python -B tests/test_inventory_and_profiles.py -v DesignReviewTests.test_round4_source_order_and_branch_bounds_red_contracts_are_independent`

The result was one test, 43 intended assertion failures, zero errors, and exit
1. Both the generator and test file parse. The second bounded production pass
is authorized against these frozen test bytes. Native transaction/publication
code, generated inventory/profile files, configuration/model files, evidence
artifacts, commits, integration, and CodeRabbit remain outside that pass.

## Round-12 second candidate rejection and fix-13 contract

The second bounded analyzer candidate froze at generator SHA-256
`07e65029beee64706c339449c3687b8a36d118ae1fabf5c4364080119fe3b5b4`;
the 104-contract test file remained byte-identical at
`b95421b61972ff606f400d7b57a78db56de0a37f0a85e40244701deddba4af39`.
The controller independently reproduced focused GREEN. Both direct reviewers
verified the same start and end hashes, found no Critical or Minor issue, and
confirmed that no native transaction, Git, atomic-write, or publication
definition changed.

Broader evidence rejected the candidate. With
`PONTIUS_GIT=C:/Program Files/Git/cmd/git.exe`, the direct inventory/profile
suite ran 87 tests and failed with four failures and two errors. Three failures
were established exceptional-environment reason drift. The remaining failures
and errors exposed bound-unknown deletion incorrectly terminating the
independent census, maybe-unbound sensitivity disappearing from the resolver,
and resulting full-corpus reconciliation/default-check failures.

The primary direct review returned SPEC OPEN and QUALITY OPEN with five
Important groups. The independent adversarial review returned OPEN with nine
Important groups. Their overlap plus the broad-suite regressions is normalized
into 13 correction groups in
`task-2-fix13-analyzer-review-findings.md`, SHA-256
`2c8ce572772a6ed50ce60457aeb1ab6e720bae8c628f9b179c0a4853a292dd93`.
The binding next step is tests-only RED expansion against the exact rejected
candidate. Every new schedule must exercise real CPython plus independent
preclassifier, resolver, and full reconciliation as applicable; analyzer
exceptions are recorded mismatches rather than harness errors. No production,
generated, configuration/model, H32, native, evidence, CodeRabbit, commit, or
integration change is authorized during that RED phase.

## Fix-13 RED-matrix first-draft rejection

The first tests-only expansion froze at test SHA-256
`2c67d6fe1e33a56e39b1d3505490ddb4e8bf66783f5438a8391efc1cff49bdca`
while the rejected generator remained byte-identical at
`07e65029beee64706c339449c3687b8a36d118ae1fabf5c4364080119fe3b5b4`.
It added 53 schedules/contracts, for 157 total, and the controller independently
reproduced 32 assertion failures, zero unittest errors, and exit 1.

Both independent test-oracle reviews returned OPEN with no Critical findings.
The draft did not yet discriminate several required implementations: its
direct analyzer helper treated a function parameter as an imported CuPy
module; its full-review observer could return before simultaneously checking
rows, blockers, and errors; and multiple helper, lexical, exceptional,
generator, comprehension, decorator, and real-runtime inverse branches were
missing or weak. Forty-nine sampled runtime bodies did agree with CPython, and
the dict-unpack, while re-test, refutable-match, single-decorator, and runtime
count mechanisms remain useful.

The complete tests-only correction contract is bound by
`task-2-fix13-red-matrix-review-findings.md`, SHA-256
`9cbe5391a359e894d46d20be3991d54f230c8364d795eea53da738638710b13c`.
Only `tests/test_inventory_and_profiles.py` may change during the repair. The
corrected selector must contain mutation-sensitive REDs and adjacent controls,
finish with intended assertion failures and zero errors, and leave the
generator at its exact frozen hash. Production GREEN remains unauthorized
until the corrected test matrix is independently reproduced and reviewed.

## Fix-13 corrected RED matrix frozen for review

The corrected tests-only candidate has SHA-256
`79e9c5220b4f4b3b9807b406f30ece19146e41d56a864b652421655eb7b96a47`.
The rejected generator remains byte-identical at SHA-256
`07e65029beee64706c339449c3687b8a36d118ae1fabf5c4364080119fe3b5b4`.
The matrix now contains 199 schedules/contracts: 104 retained contracts and
95 fix-13 contracts. Relative to the rejected first draft, only
`tests/test_inventory_and_profiles.py` changed.

The controller independently parsed both files under `python -B` and ran:

`python -B tests/test_inventory_and_profiles.py -v DesignReviewTests.test_round4_source_order_and_branch_bounds_red_contracts_are_independent`

The exact frozen bytes produced one test, 52 intended assertion failures, zero
errors, exit 1. The failures distribute across all 13 production groups:
helper identity/signatures 8; lexical boundness 11; maybe-bound successors 4;
reraises 3; decorator application 1; constructor/raise classification 10;
dict-unpack order 1; bounded generator state 6; comprehension successors 2;
while re-test 1; match residual 2; environment poison 2; reconciliation 1.

The corrected harness analyzes the imported-module review source independently
from its runtime callable, observes rows/blockers/errors simultaneously,
preserves helper identity by scope, exercises both successor and inverse paths,
records direct-generator consumption/closure state, pairs optional
comprehension paths, proves multi-decorator evaluation/application order, and
uses fake-subprocess and dynamic-target runtime companions without launching
an external process. Two independent read-only test-oracle reviews are now in
progress. Production correction remains locked until both reviews are CLEAN;
CodeRabbit, commit, and integration remain unauthorized.

## Fix-13 final RED-matrix review rejection and blocker ruling

Both reviewers verified stable tests
`5a2b4ee5826d55b71eef4cd81022ccf3c6803789ce427ec623d74478028eab67`
and generator
`07e65029beee64706c339449c3687b8a36d118ae1fabf5c4364080119fe3b5b4`,
then returned OPEN with no Critical findings. Their remaining findings plus one
controller-raised policy conflict reduce to five last test mechanisms.

Static invalid helper calls need wrong-handler inverses, and representative
valid calls need inverse `TypeError` controls. Decorator application failure
must exclude a simultaneous bound-name successor. Zero-, keyword-, and
three-argument invalid `next` calls must expose both exact `TypeError` routing
and pre-consumption receiver state. The two-item control must prove the second
body transition and third-call exhaustion in source state, not only through
`maximum_calls` metadata.

The controller also challenged the new body-only unknown-cardinality
expectation. Both reviewers independently confirmed the conflict: the
preclassifier and resolver must retain the possible protected body successor,
but full review cannot manufacture a finite bound for
`runtime_items()`. The correct disposition is zero rows, the sole blocker
`dynamic repetition prevents a finite call bound`, and no error for both
runtime companions. This preserves the established unbounded-repetition
contract.

The binding correction is recorded in
`task-2-fix13-red-matrix-final-review-findings.md`, SHA-256
`48ca64154978cc4f6547e51cc829b94c159e5947e41169596ca63078e2cae74a`.
Only the test file may change. Production, generation, configuration/model,
H32, native code, CodeRabbit, commit, and integration remain unauthorized.

## Fix-13 last RED matrix frozen for dual review

The last tests-only candidate has SHA-256
`92b8ae99757077208aecad24652f1438e0989c589d9bcfd3a4f943eecffaf1b6`;
the rejected generator remains byte-identical at
`07e65029beee64706c339449c3687b8a36d118ae1fabf5c4364080119fe3b5b4`.
The public matrix contains 240 contracts. Relative to the previous reviewed
test bytes, the final correction added 179 lines and removed two.

The controller independently parsed both Python files and reproduced one
focused test with 73 intended assertion failures, zero errors, and exit 1.
The two unknown-cardinality body controls now pass with zero rows and the exact
dynamic-repetition blocker. New mutation-sensitive failures cover helper-call
validity exclusivity, absence of a bound decorator-failure successor, exact
invalid-`next` routing and pre-consumption state, and the second two-item state
transition; the third-call exhaustion and existing maximum-two controls pass.
The cache census remains zero.

Both final test-oracle reviewers are inspecting these exact hashes. Production
remains locked until both verdicts are CLEAN. CodeRabbit, commit, and
integration remain unauthorized.

## Fix-13 RED matrix dual-review acceptance

Both final reviewers verified stable tests
`92b8ae99757077208aecad24652f1438e0989c589d9bcfd3a4f943eecffaf1b6`,
generator
`07e65029beee64706c339449c3687b8a36d118ae1fabf5c4364080119fe3b5b4`,
and final test brief
`48ca64154978cc4f6547e51cc829b94c159e5947e41169596ca63078e2cae74a`.
The primary review returned TEST-SPEC CLEAN and TEST-QUALITY CLEAN; the
independent adversarial review returned ORACLE CLEAN. Neither found a
Critical, Important, or Minor issue.

Fresh reviewer evidence reproduced the controller result: 240 contracts, one
focused test with 73 intended assertion failures, zero errors or skips, clean
parsing, the expected CPython 3.14 `finally: return` warning only, and no cache
directory. Concrete mutation checks covered helper-call validity, decorator
failure binding, invalid-`next` exact routing and pre-consumption state,
second/third two-item transitions, the dynamic-repetition blocker, and every
previously closed family.

The RED oracle is accepted. A bounded production correction may now modify only
`tools/generate_test_inventory.py` to satisfy the 13 fix-13 groups. The test
file and native transaction/Git/publication code are frozen. CodeRabbit,
commit, and integration remain unauthorized until the corrected candidate
passes broad verification and two fresh production reviews.

## Fix-13 corrected RED-matrix rereview rejection

Both independent reviewers verified stable start/end identities for tests
`79e9c5220b4f4b3b9807b406f30ece19146e41d56a864b652421655eb7b96a47`
and generator
`07e65029beee64706c339449c3687b8a36d118ae1fabf5c4364080119fe3b5b4`.
Both returned OPEN with no Critical findings. The controller's 52-failure,
zero-error reproduction remains valid, but production GREEN is not authorized
because several assertions still prove CPython behavior without constraining
the production analyzer.

The overlapping findings reduce to six test mechanisms. A mixed-tag helper is
outside the approved single-tag exact summary and must remain conservative;
ordinary positional, dynamic `**`, argument-error, `finally: return`, and
nonlocal helper identity/boundness seams need adjacent controls. Decorator
expression/application order and failed definition binding must be visible in
analyzer output, not only in a runtime event log. Body/filter exceptions must
close generator state in the analyzer so a second `next` cannot replay the
exception. Unknown cardinality needs a protected body-only successor as well
as the existing skip successor. Finally, zero-argument, keyword-argument, and
two-item `next` cases must prove the complete bounded rim quantitatively.

The binding final tests-only correction set is recorded in
`task-2-fix13-red-matrix-rereview-findings.md`, SHA-256
`6cd5d8024f3df26a2e2ba050d1586be865304e5ed518f60355079c73578b430b`.
Only the inventory/profile test file may change against the frozen rejected
generator. Production, generation, configuration/model/H32, native code,
CodeRabbit, commit, and integration remain outside this correction.

## Fix-13 final RED matrix frozen for review

The final tests-only candidate has SHA-256
`5a2b4ee5826d55b71eef4cd81022ccf3c6803789ce427ec623d74478028eab67`;
the rejected generator remains byte-identical at
`07e65029beee64706c339449c3687b8a36d118ae1fabf5c4364080119fe3b5b4`.
The public matrix now contains 221 contracts. Only
`tests/test_inventory_and_profiles.py` changed from the prior reviewed test
candidate, by 330 insertions and one deletion.

The controller independently parsed both Python files and reran the public
selector. It produced one test with 61 intended assertion failures, zero
errors, and exit 1. No bytecode/cache artifact was created. The only diagnostic
outside assertion output was CPython 3.14's expected `SyntaxWarning` for the
deliberate `finally: return` semantic control.

The added schedules retain mixed-tag helper conservatism, cover the remaining
argument and nonlocal helper seams, expose decorator expression/application
order and failed binding to the analyzer, expose body/filter generator closure
on a second `next`, require both unknown-cardinality comprehension successors,
and quantify invalid and two-item direct-`next` behavior. Both final test-oracle
reviews are now running against these exact hashes. Production remains frozen;
CodeRabbit, commit, and integration remain unauthorized.

## Fix-13 first production candidate rejection

The bounded analyzer implementation froze at generator SHA-256
`f581c3c29b156fab7b4e52737fb323b744a482cff913ffadde82953e6313d0e2`
against the accepted 240-contract test matrix SHA-256
`92b8ae99757077208aecad24652f1438e0989c589d9bcfd3a4f943eecffaf1b6`.
The focused public selector passed with zero failures or errors, successful AST
parsing, the one expected CPython 3.14 `return`-in-`finally` warning, and no
cache artifacts.

The required direct full-suite run used the explicit executable boundary
`PONTIUS_GIT=C:/Program Files/Git/cmd/git.exe`. It ran 87 tests in 71.770
seconds and failed with one failure and three errors. The failure was
`test_default_cli_mode_is_a_read_only_successful_check`, whose exit 2 is
derivative of the census reconciliation errors. The three primary errors were:

- the resolver identified the real CuPy call at
  `tests/test_resident_record_to_hand_fold_v2.py:312`, but the independent
  census omitted it;
- the resolver identified the synthetic protected container-selection call at
  `tests/test_review.py:14`, but the independent census omitted it; and
- the independent census identified the synthetic local-alias helper-return
  call at `tests/test_review.py:10`, but the resolver supplied no disposition.

Two independent read-only diagnostics reduced those failures to two shared
mechanisms. `_SensitivePreclassifier._expression(ast.Attribute)` discarded
the inherited sensitivity of an unknown-but-tainted receiver whenever it also
had a synthetic qualified name. `_SourceOrderedResolver.__init__` then
overwrote an exact source-ordered helper return with a weaker trivial bare-name
summary. Existing focused and integration tests already provide strong RED
coverage for both mechanisms.

A separate exact-hash adversarial review found one additional Important
definition-identity collision. Two different factories that each return a
nested callable named `decorator` are flattened by that bare name. In an outer
`KeyError`/inner `ValueError` decorator stack, the analyzer may route the wrong
exception even though CPython applies the inner decorator first. The preclassifier
and direct resolver must carry definition-point-qualified returned-callable
summaries; full review must preserve the exact caller-supplied helper return.
Ambiguous, conditional, or reassigned definitions remain unknown.

Production is frozen. The only authorized test delta is the minimum paired
same-name decorator schedule plus an inherited-sensitive receiver schedule and
safe counterpart. After that tests-only RED is independently reviewed, one
bounded generator correction may address the three mechanisms. Native
transaction/publication/Git code, CodeRabbit, commit, and integration remain
unauthorized.

## Fix-13 post-GREEN RED matrix acceptance

The corrected tests-only candidate froze at SHA-256
`5f396043fbb4779ea8fd293042abb2c552849061c8e60ba477e4327841905a70`;
the rejected generator remained byte-identical at
`f581c3c29b156fab7b4e52737fb323b744a482cff913ffadde82953e6313d0e2`.
The public selector now contains 246 contracts. It adds positive and inverse
same-named decorator schedules in both factory-definition orders, one inherited
protected-result receiver schedule, and one ordinary receiver control. The
full-review receiver oracle requires exactly one approved `cupy.arange` row
and the exact unregistered-call blocker at `tests/test_review.py:7`.

The controller parsed both Python files and ran the selector under ten hash
seeds. Seeds 0, 1, 2, 5, and 8 produced three intended assertion failures;
seeds 3, 4, 6, 7, and 9 produced five. Every run exited 1 with zero errors.
The variance is the rejected generator's unordered bare-name traversal: the
original pair and receiver fail under every seed, while the reversed pair also
fails under affected seeds. The safe receiver passes throughout. No cache or
bytecode artifact was created.

Both exact-hash reviews returned CLEAN with no Critical, Important, or Minor
finding: the primary reviewer returned TEST-SPEC and TEST-QUALITY CLEAN, and
the independent mutation-oriented reviewer returned ORACLE CLEAN. First-wins,
last-wins, classify-none, classify-both, blanket-attribute, and wrong-blocker-
line mutations are rejected. The binding production correction set is
`task-2-fix13-production-green-rereview-findings.md`, SHA-256
`6d39c6553cf90b5015379151c2a357c44da38e5268ea60809067246adec437f0`.

A bounded analyzer-only correction may now resume. Tests, native transaction,
publication, Git, configuration/model, H32, and generated governance files are
frozen. CodeRabbit, commit, and integration remain unauthorized until broad
verification and two fresh production reviews are CLEAN.

## Fix-13 latent string-decoy layout correction

After the analyzer correction closed the earlier working-source census errors,
the real review reached `_string_decoy_census` and rejected two duplicate
`(path,line)` identities. In each case an existing assertion placed the two
tracked constants `"cupy.arange"` and `"cupy.zeros"` on one physical line.
The only tests-only correction split those two set literals across lines.

Tests changed from
`5f396043fbb4779ea8fd293042abb2c552849061c8e60ba477e4327841905a70`
to `6102c048a86e8f068cc0c3bd8303323115f9697bf29d8d4bfd246da000ec8822`.
Both exact-hash reviews returned CLEAN. Each reconstructed the prior bytes from
exactly those two hunks; AST/unparse semantics match, compiled executable
bytecode matches, the new source locations are unique, and cache counts are
zero. The amendment is bound by `task-2-fix13-decoy-layout-correction.md`,
SHA-256 `44b44dd31195dfce34c7ac7318dae5a9a2b6707b7a939a392127963d0b82832a`.
No row, blocker, census, digest, capability, or runtime expectation changed.

## Fix-13 immediate tuple-generator RED acceptance

Working discovery then reached its exact row oracle and produced 128 rows
instead of 139. Exact comparison found eleven missing and zero added rows. All
eleven are fixture-scoped automaton-cache `compile` capabilities with
`maximum_calls=6`, arising from ten immediate
`tuple(<generator expression over range(6)>)` source sites. Runtime bounds were
already correct; the preclassifier and resolver deferred the generator body and
full review mislabeled those sites unreachable.

The accepted tests-only correction freezes at
`343323119350b1f17523cf64343da46a7c8e3554e821aa606ecacd898fe802fe`
against rejected generator
`7fc84e76febb0a14e237f21473ba2bd7ab84afdf94270e7e9117cbf78369731f`.
The public selector now contains 258 contracts. Seeds 0 and 3 each produce six
intended failures and zero errors. The new family binds the finite direct bare-
builtin `tuple` case and excludes zero, named/escaped, unknown-cardinality,
walrus, direct/named list, resolved alias, rebound name, starred, two-argument,
and keyword shapes.

Both exact-hash reviews returned CLEAN with no finding: TEST-SPEC,
TEST-QUALITY, and adversarial ORACLE. The binding correction is
`task-2-fix13-immediate-tuple-review-findings.md`, SHA-256
`88942964dca6f60755604c1350a392fdb484ad0f8e779d1b428a6608d886d2e3`.
Only the bounded immediate-consumption preclassifier/resolver path may now
change. Tests and all non-analyzer production remain frozen.

## Final winding-down checkpoint: internally clean, CodeRabbit transport pending

The final whole candidate is frozen in `D:/Pontius-worktrees/orch-task2` as an
11-file canonical manifest with SHA-256
`79600d1112e52a37f22b649b5d4d5a2f382cb8daf247082466700729b99e82ef`.
The final generator SHA-256 is
`4e562504156e0f71ce15a15ba4b817df2d97188c6f3d7df02f96151eb7970e14`;
the final inventory/profile test SHA-256 is
`1502e12355bb33984a9807ae2b4a194d9aaa399cd963b8a05fa4ffaa3eb87a8b`.

Fresh broad acceptance passed:

- 87/87 inventory/profile tests in 123.812 seconds;
- 53/53 configuration/model tests in 0.295 seconds;
- H32: 9 run, 8 passed, exactly one approved unconditional skip;
- generator `--check`, authorized `--write`, and post-write `--check`, with
  byte-stable generated hashes `0dd70e...6543d` and `277354...497ea`;
- authenticated dependency-baseline and stabilization-boundary checks;
- Python/JSON/TOML parsing, `git diff --check`, and exact candidate whitespace;
  and
- zero Python cache artifacts and no unexpected working-tree files.

Two fresh independent whole-candidate reviews both returned CLEAN. Each
recomputed the manifest before and after inspection and found no blocking
correctness, security, or established-contract regression. The deliberately
dirty/live V7 checkout remains unsuitable for its clean-artifact harness setup;
the original authorization findings were instead covered by focused tests and
direct source review.

CodeRabbit did not start a review. Three authenticated exact invocations of
`coderabbit review --agent -t uncommitted --include-untracked` reached the
correct repository/branch context and failed during `connecting` with the same
recoverable `WebSocket closed` transport error. No CodeRabbit finding exists,
and no bytes changed. The exact command should be retried once when service
connectivity returns; it is the sole pending external acceptance gate.

Correctness exploration stops at this checkpoint. Additional speculative edge
families are not authorized. Nonblocking maintainability and performance debt
is recorded in `task-2-holistic-architecture-audit.md`, SHA-256
`24dcbf30c023ab785a09f9232e5e0c230df027c7737322f6da1d13f7474ab02d`.
No commit, merge, push, or integration was performed.
