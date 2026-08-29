# Task 3b report — postapproval evidence manifest lock/write

## Status and authorization

Task 3b is complete on branch `codex/evidence-test-stabilization` at
`c4d158e4601c61ce445be5f57894ccef61cddbf0`
(`build(evidence): lock retained and historical identities`). No push, merge,
publish, primary-checkout mutation, or lifecycle invocation occurred.

The only approved historical seed was the retained external artifact:

- path: `C:\Users\point\AppData\Local\Temp\pontius-task3-seed-review-fix4-766f4d73bb4143e1afa7ae87d2068757.txt`
- bytes: 44,301
- ordered unique rows: 167
- normalized/approved digest: `812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89`
- artifact SHA-256: `92e538f7d88ec7bb632d380525b61c0a5c35630f37f4aeb6a55ee4b051bd55c2`

No other row table or digest was used.

## Canonical write snapshot and candidate gate

The write snapshot was a fresh `--no-local --no-checkout` clone made with the
absolute Git executable, system/global configuration disabled, a dedicated Git
home, `GIT_NO_REPLACE_OBJECTS=1`, and `core.autocrlf=false`:

- snapshot: `C:\Users\point\AppData\Local\Temp\pontius-task3b-write-85b432610fb24c809911ea4312e8ad7f`
- Git home: `C:\Users\point\AppData\Local\Temp\pontius-task3b-git-home-85b432610fb24c809911ea4312e8ad7f`
- base: `e0d29dd86bafcea21dbd99336914ee5197572af4`
- canonical protected v9: 482 bytes, SHA-256
  `57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535`

An independent standard-library TSV/JSON verifier read all seven fields, proved
167 rows, 167 unique `(commit, relative_path)` identities, exact sorted order,
and reconstructed normalized digest `812ce6b5...99c89`. It separately verified
the 44,301-byte length and artifact SHA-256 `92e538f...55c2`.

Before any manifest write, the generator re-emitted to
`C:\Users\point\AppData\Local\Temp\pontius-task3b-reemit-330914e903084aff899069f50e390ba1.txt`.
A byte-by-byte loop proved it identical to the approved artifact; size and
artifact hash also matched exactly.

## Exact-oracle RED

`tests/test_evidence_manifest_generation.py` now contains a test-local literal
fixture for every one of the 167 ordered seven-field rows. Runtime expectations
do not read the external artifact and do not derive expected rows from generator
code. The oracle independently locks count, ordered rows, `entries_sha256`, and
`approved_seed_sha256`.

Before any manifest or destination directory existed, this command used the
approved copied venv Python, `-B -P`, snapshot cwd, and `PYTHONPATH=H/src`:

~~~powershell
& $python -B -P tests/test_evidence_manifest_generation.py EvidenceManifestGenerationTests.test_approved_historical_manifest_is_the_exact_ordered_oracle -v
~~~

Result: exit 1 after 17.944 seconds. The exact literal rows and freshly derived
state matched, then the test raised the intended `FileNotFoundError` for
`docs/architecture/historical-blobs.toml`. Two earlier authoring runs caught and
corrected a test-local escaped-tab/leading-newline fixture bug before the
intended RED; neither reached production behavior and no manifest existed.

## First approved invocation and controller ruling

The exact approved command was first invoked once after the intended RED:

~~~powershell
& $python -B -P tools/generate_evidence_manifests.py --write --approved-seed-sha256 812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89
~~~

It exited 1 before derivation, directory creation, temporary-file creation, or
manifest write. `_verified_destinations()` called
`(root / "docs" / "architecture").resolve(strict=True)`, but the clean base had
no `docs/architecture` directory. Immediately afterward the directory and all
four manifest destinations were absent; Git showed only the uncommitted oracle.

The controller ruled that this fail-closed pre-write outcome consumed no
approved write and explicitly authorized one guarded retry after a narrow
destination-bootstrap fix. The ruling did not authorize any historical row,
digest, parser, derivation, constant, or rendering change.

## Destination-bootstrap TDD

Focused bootstrap RED command:

~~~powershell
& $python -B -P tests/test_evidence_manifest_generation.py EvidenceManifestGenerationTests.test_write_securely_bootstraps_only_the_four_manifest_destinations EvidenceManifestGenerationTests.test_manifest_directory_rejects_non_directory_link_and_reparse_targets EvidenceManifestGenerationTests.test_manifest_directory_identity_race_rejects_before_any_temp_file -v
~~~

Result: exit 1; three tests ran with one failure and two errors. The base tool
errored on a missing directory and accepted an existing non-directory target.

The minimal production change was confined to destination verification and
bootstrap in `tools/generate_evidence_manifests.py`. It validates the repository
root and `docs` ancestor as directories without links/reparse points, creates
only the missing `docs/architecture` child after digest approval, checks ancestor
and created-directory identity, rechecks the full destination surface before
any temporary file, and preserves the existing four atomic replacements.
Derivation, parsers, constants, rendering, and approval digest semantics were
not changed.

The focused GREEN command above then ran three tests in 0.017 seconds and exited
0. Two intermediate runs had only test-double construction errors in the race
fixture (`Mock.st_mode`, then missing Windows stat attributes); correcting the
test double to expose explicit integer stat fields made the same production code
green.

The tests prove missing-directory creation, exactly four output names and bytes,
non-directory rejection, symlink/reparse rejection, and identity-race rejection
before any temporary file remains.

## Post-fix approval revalidation and authorized retry

The post-fix re-emission was
`C:\Users\point\AppData\Local\Temp\pontius-task3b-reemit-bootstrap-fa9e37cfbd35458db21b7aea983f2f0d.txt`.
It was byte-identical to the approved artifact: 44,301 bytes, 167 rows,
normalized digest `812ce6b5...99c89`, artifact SHA-256 `92e538f...55c2`.
At that point `docs/architecture` and all four destinations were still absent,
proving the first invocation had created nothing.

The controller-authorized retry used the exact command above once and exited 0
in 18.5 seconds. No further `--write` invocation occurred.

## Generated diff and metadata inspection

The complete four-file addition was inspected. A separate standard-library
TOML/TSV/JSON verifier compared all 167 generated `[[blobs]]` mappings to the
approved candidate, in order, and recomputed the digest. It proved:

- six current entries and eighteen absence entries;
- eleven snapshot entries and 167 unique historical entries;
- `entries_sha256` and `approved_seed_sha256` both exactly
  `812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89`;
- no unapproved historical row;
- the architecture directory contained only the four named manifests and no
  temporary file.

Canonical file identities:

| Manifest | Bytes | SHA-256 |
| --- | ---: | --- |
| `sealed-current-files.toml` | 2,191 | `4147b3f066642ba1e4d2ab6b2028c4d17ab3922141c0edff8c7312545dd75580` |
| `sealed-current-absences.toml` | 4,772 | `592b3916ee32c5ab9b212e29f2b1f163651da4bd0abb7c885a2cddb83e48be63` |
| `historical-blobs.toml` | 64,840 | `baa6a485717360a990120dfce6d8461a046e64470741cbf914e8daa1937ad8f9` |
| `retained-v7.toml` | 2,883 | `e2ff5371bdf01ea5a15f2b38eda057fc6a0947f83a55faf46a47dfd0cf67ff83` |

## First-snapshot GREEN and no-write proof

Commands used the required interpreter, `-B -P`, snapshot cwd, and
`PYTHONPATH=H/src`:

~~~powershell
& $python -B -P tools/generate_evidence_manifests.py --check
& $python -B -P tests/test_evidence_manifest_generation.py -v
& $python -B -P tests/test_evidence_manifests.py -v
& $python -B -P tests/test_evidence_errors_and_model.py -v
~~~

Final results: `--check` exit 0; 35 generator/oracle tests passed in 36.709
seconds; 11 manifest/parser tests passed in 0.037 seconds; 7 Task 1 model/error
regressions passed in 0.001 seconds. The first full generator-suite run found one
test-state assumption: the preapproval short-circuit test expected the real
historical manifest to remain absent. It was corrected to inject an absent read
while still proving no derivation occurs; the focused test and full suite then
passed. No production change resulted from that test-state correction.

Independent measurements immediately before the first invocation and after all
first-snapshot tests matched all six approved byte lengths/SHA-256 identities.
All eighteen protected lifecycle paths were absent both times. The v9 canonical
identity stayed 482 bytes/SHA-256 `57c869...a535`. The only paths created by the
authorized write were the four manifests. `git diff --check` exited 0.

## Commit and cherry-pick provenance

The canonical snapshot commit was
`9221dce82830938b62c67324884d959c00d9ce09` with the required message. It
contains exactly the four manifests, exact oracle/destination tests, and the
controller-authorized narrow destination bootstrap.

Because the canonical clone was `--no-local`, the development object database
did not initially know `9221dce`; the first cherry-pick command failed with
`bad object` and changed nothing. The commit was then fetched from the canonical
snapshot. The first post-fetch cherry-pick applied the index but could not
commit under the scrubbed config because no committer identity was present; it
left a normal `CHERRY_PICK_HEAD`. Continuing with the existing repository author
identity completed the single cherry-pick as
`c4d158e4601c61ce445be5f57894ccef61cddbf0`. The development branch is clean.

The protected development-worktree v9 representation was unchanged across the
cherry-pick: 494 bytes, SHA-256
`98493b5047ab04267c8b8ab41adccd30a63a53ef6aa441a02d92ece52985f0d6`.
It was never checked out, normalized, added, staged, or otherwise touched.

## Fresh post-integration snapshot

A second fresh scrubbed `--no-local --no-checkout` clone was created from the
resulting branch:

- snapshot: `C:\Users\point\AppData\Local\Temp\pontius-task3b-final-bec89f6d15694e7e95e4fffc1ed9d968`
- Git home: `C:\Users\point\AppData\Local\Temp\pontius-task3b-final-git-home-bec89f6d15694e7e95e4fffc1ed9d968`
- HEAD: `c4d158e4601c61ce445be5f57894ccef61cddbf0`
- canonical v9: 482 bytes, SHA-256 `57c869...a535`

Fresh final results:

- generator `--check`: exit 0;
- `tests/test_evidence_manifest_generation.py`: 35 passed in 35.605 seconds;
- `tests/test_evidence_manifests.py`: 11 passed in 0.037 seconds;
- `tests/test_evidence_errors_and_model.py`: 7 passed in 0.001 seconds;
- independent metadata audit: exact 167 approved rows/digests, six current
  identities, eighteen absences, and the four hashes above;
- `git diff --check`: exit 0;
- `git diff --exit-code HEAD --`: exit 0;
- final snapshot status: clean detached HEAD.

Both disposable canonical snapshots, Git homes, and re-emission artifacts are
intentionally retained for controller cleanup. Ruff was not provisioned at a
required absolute path; no Ruff result is claimed.

## Fix round 1 — explicit CLI bootstrap and held write transaction

Review identified two Important gaps after `c4d158e`: the write/check CLI
policy was not expressed by distinct validators, and temporary-file creation
and replacement remained path-based after the last directory identity check.
The fix was developed only in the disposable canonical snapshot
`C:\Users\point\AppData\Local\Temp\pontius-task3b-fix1-5d522d7887a74043bff248bed6be647b`.
No approved `--write` invocation was made on the development branch or during
this fix round, and none of the four manifest bytes changed.

The execution-history description above needs this precision: the first
approved invocation really did fail before any destination or temporary-file
write, and the controller-authorized retry really did run through `main()` and
succeed. It was not replaced by a direct helper call. In the subsequently
committed bootstrap implementation, however, `_verified_destinations()` passed
an absent architecture directory through as a `None` identity even when called
with `create_missing=False`. Thus the retry was CLI-reachable, but the strict
non-write verifier's semantics were accidentally permissive and the path was
not protected by a true CLI-boundary regression test. The fix makes this policy
explicit: `--write` validates a missing-directory destination intent, while
`--check` and non-write validation remain read-only and reject absence.

Two focused tests were added first. The RED command was:

~~~powershell
& $python -B -P tests/test_evidence_manifest_generation.py EvidenceManifestGenerationTests.test_main_write_bootstraps_missing_directory_while_check_remains_read_only EvidenceManifestGenerationTests.test_bound_manifest_transaction_defeats_post_validation_directory_swap -v
~~~

It exited 1 with two tests and two failures. The CLI test showed that the real
`main(--write)` bootstrap was reachable but the supposedly strict verifier did
not reject absence. The deterministic post-validation swap succeeded against
the old implementation, redirected its path-based writes, and produced no
`GenerationError`.

The production change remains confined to destination bootstrap/verification
and the write transaction. Derivation, parsers, evidence constants, rendering,
approval validation, approved rows, and digest semantics were not changed. On
Windows, repository, `docs`, and `architecture` are opened as non-reparse
directory handles for the complete transaction with delete sharing omitted;
held-handle and current-path identities are rechecked before staging, before
each replacement, and afterward. On POSIX the transaction fails closed unless
`O_DIRECTORY`, `O_NOFOLLOW`, and directory-relative open/mkdir/replace/unlink
are available, then performs those operations through held `dir_fd` values.
All four temporary files are staged before any atomic per-file replacement,
and the held directory identity is used for cleanup.

The focused GREEN included the two new tests and the three earlier destination
tests. It ran 5 tests in 0.035 seconds and exited 0. On this Windows host the
deterministic rename of the held architecture directory was permitted by the
filesystem despite delete sharing being omitted; the immediate identity
recheck rejected the substitution before any temporary file was created. Both
the displaced directory and the replacement path remained empty. If the host
denies the rename, the same test requires the normal four-file transaction to
succeed. Symlink/reparse/non-directory rejection and missing-directory
bootstrap remain covered by the focused set.

The canonical fix commit was
`010a4ec49ac7a22a46e761817788a9355df774ae`
(`fix(evidence): bind manifest write transaction`). It contains only
`tools/generate_evidence_manifests.py` and
`tests/test_evidence_manifest_generation.py`. Cherry-picking it once onto the
clean development branch produced
`ba1e665c3337a8bbdda96ba2cc6fa5c6e52dd163`. The development v9 representation
was unchanged before and after: 494 bytes and SHA-256
`98493b5047ab04267c8b8ab41adccd30a63a53ef6aa441a02d92ece52985f0d6`.

Fresh post-integration verification used the canonical scrubbed snapshot
`C:\Users\point\AppData\Local\Temp\pontius-task3b-fix1-final-3fd4139c85fb4a8e98c828e4e80a47d9`
at `ba1e665`, the approved copied venv Python, `-B -P`, snapshot cwd, and
`PYTHONPATH=H/src`:

- generator `--check`: exit 0;
- generation/oracle suite: 37 tests passed in 36.013 seconds;
- manifest/parser suite: 11 tests passed in 0.037 seconds;
- Task 1 model/error suite: 7 tests passed in 0.001 seconds;
- `git diff --check`, `git diff --exit-code HEAD --`, and status: clean.

An independent standard-library artifact/TOML comparison reverified the exact
44,301-byte approved candidate, artifact SHA-256 `92e538f...55c2`, all 167
ordered unique rows, normalized and approved digest `812ce6b5...99c89`, six
current identities, and eighteen absences. The four manifest identities remain
2,191/`4147b3f...5580`, 4,772/`592b391...be63`,
64,840/`baa6a48...8f9`, and 2,883/`e2ff537...ff83`. The final canonical v9 is
482 bytes/`57c869...a535`. No lifecycle path or manifest was written in the fix
round. The POSIX branch is deliberately fail-closed but was not executable on
this Windows verification host.

## Fix round 2 — handle-relative Windows mutations and immediate ownership

Review of `ba1e665` found that the Windows implementation still performed its
actual mutations through newly resolved paths after revalidation, and that a
failure inside `stage()` occurred before the candidate reached the caller's
cleanup map. The second fix round was developed only in the fresh canonical
snapshot
`C:\Users\point\AppData\Local\Temp\pontius-task3b-fix2-6c62e69261094bfbb0af8e163ca4ffbd`
from `ba1e665`. No approved `--write`, lifecycle invocation, manifest rewrite,
or development-v9 operation occurred.

Five focused tests were added before the production change. Three inject a
directory-swap attempt at the native stage, replace, and failed-candidate
disposal boundaries, after the last pathname revalidation. Two inject an
`os.write` or `os.fsync` failure after candidate creation and require all four
pre-existing destinations to remain byte-identical with no `.tmp` residue.
The first RED run exited 1: four assertions failed and the fsync case initially
surfaced the raw injected `OSError`; after making that test accept either the
old raw error or the intended wrapped error, it failed specifically because the
old path-based stage leaked its temporary file. A sixth capability test was
then RED with `OSError('unavailable')` instead of the required fail-closed
`GenerationError` when the native DLL/API surface could not load.

The Windows mutation layer now uses `NtCreateFile` with an
`OBJECT_ATTRIBUTES.RootDirectory` equal to the held verified architecture
handle. The returned native handle is transferred to a CRT descriptor and
owned by the transaction immediately after creation, before revalidation,
write, or fsync. Replacement uses `NtSetInformationFile` with
`FileRenameInformation`, a relative single-component destination name, the
same held architecture handle, and replace-if-exists. Failed candidate disposal
uses `NtSetInformationFile` with `FileDispositionInformation` on the candidate
handle itself; it never resolves a pathname. The native functions, structure
layout inputs, exact success `NTSTATUS`, I/O status, create disposition, handle
presence, and relative component names are all validated and fail closed.
Unavailable functions are converted to `GenerationError`.

The root/docs/architecture handle chain remains open for the entire
transaction and now requests traversal, attribute, and synchronization access
while continuing to omit delete sharing. Each mutation remains bracketed by
identity checks. The POSIX `dir_fd`/`O_NOFOLLOW` branch was preserved; it now
also registers ownership immediately after `os.open` so write/fsync failures
are cleaned through the held directory descriptor. All four candidates are
still completely staged before the first per-file atomic replacement.

Focused GREEN ran the five race/failure tests, native-capability test, and
bootstrap success test: 7 tests passed in 0.057 seconds. All three late swap
attempts executed; this Windows filesystem denied each rename while the held
chain was open. The tests also accept a filesystem that permits the swap, but
then require the replacement path to receive no write or deletion and require
the operation to remain bound or fail closed. A separate synthetic two-pass
write proved the native rename replaces all four existing destinations with
the exact rendered bytes and leaves no temporary residue.

The canonical fix commit is
`1f33c7b2131bbbd17a2a8a9c29aaf429f10be248`
(`fix(evidence): bind Windows manifest mutations`). It changes only
`tools/generate_evidence_manifests.py` and
`tests/test_evidence_manifest_generation.py`. The single clean cherry-pick onto
the development branch is
`a16d1acb9570986fcd6f0442a7e38758aaa6b7d5`. Development v9 remained exactly
494 bytes/SHA-256 `98493b...f0d6` before and after.

The fresh scrubbed post-integration snapshot is
`C:\Users\point\AppData\Local\Temp\pontius-task3b-fix2-final-fd528cd6e92642c3bdd583f2bb8113f5`
at `a16d1ac`. With the approved copied venv Python, `-B -P`, snapshot cwd, and
`PYTHONPATH=H/src`, generator `--check` exited 0; 43 generation/oracle tests
passed in 36.498 seconds; 11 manifest/parser tests passed in 0.037 seconds; and
7 Task 1 model/error tests passed in 0.001 seconds. `git diff --check`, full
`git diff --exit-code HEAD --`, and status were clean.

Independent standard-library parsing again proved the candidate is exactly
44,301 bytes/SHA-256 `92e538f...55c2`, with 167 ordered unique rows and both
digests `812ce6b5...99c89`. The unchanged manifest identities are
2,191/`4147b3f...5580`, 4,772/`592b391...be63`,
64,840/`baa6a48...8f9`, and 2,883/`e2ff537...ff83`; canonical v9 remains
482/`57c869...a535`. The fresh snapshot is retained for controller cleanup.
The POSIX branch remains unexecuted on this Windows host.

## Fix round 3 — exclusive raw-handle ownership and exhaustive cleanup

Review of `a16d1ac` identified three remaining native lifecycle gaps: staged
handles allowed write sharing, successful rename removed transaction ownership
before CRT descriptor closure succeeded, and cleanup did not consistently
validate or aggregate every candidate/component close and native failure. The
round was developed only in
`C:\Users\point\AppData\Local\Temp\pontius-task3b-fix3-dc13dc065c064de6ae69ffc61235bfbb`
from `a16d1ac`. No approved `--write`, lifecycle invocation, manifest rewrite,
or development-v9 operation occurred.

RED tests were written before the native redesign. The first focused run
reported eight failure records: rename-close injection was never reached,
failed disposition left residue, the first directory-close failure skipped the
remaining two handles, an invalid native handle leaked raw `OSError`, native
create/set exceptions were not translated, and there was no tracked native
file-close seam. The first exclusivity probe initially passed for the wrong
reason because its second open omitted delete sharing; adding delete sharing
isolated the intended write-share question and produced the required separate
RED (`rejected` was false). The fsync/flush assertion was tightened to require
`GenerationError` exclusively.

The implementation removes the CRT ownership transfer entirely. `NtCreateFile`
now returns a raw handle with `ShareAccess=0`; the transaction registers that
handle before revalidation, write, or flush. Content is written with
`WriteFile`, flushed with `FlushFileBuffers`, renamed relative to the held
architecture handle with `NtSetInformationFile`, and closed with validated
`CloseHandle`. A successful rename sets explicit renamed state but leaves the
candidate in the ownership registry until close succeeds. Cleanup never applies
disposition to a renamed destination.

Unrenamed cleanup uses handle-bound `FileDispositionInformation`, retries a
failed disposition before close, records the first failure even when recovery
succeeds, and then attempts closure. A failed close leaves the raw handle and
candidate tracked. Transaction close visits every owned candidate, every POSIX
descriptor, and every Windows root/docs/architecture handle, collecting all
failures into one typed `GenerationError` with the first nested cause rather
than short-circuiting. Native DLL symbols, `NtCreateFile` return/I/O status,
expected create information, null and invalid handles, `NtSetInformationFile`
status, write length, flush result, disposition, and both file/directory close
results are validated. Native `OSError`/`ValueError` translations preserve a
cause.

One implementation experiment used `FILE_DELETE_ON_CLOSE`; the focused
bootstrap test proved that this flag persisted through rename and deleted the
four final files on handle close. It was removed. The final design uses
explicit disposition only for unrenamed candidates and passed the original
positive bootstrap/replacement behavior.

Focused GREEN ran 11 exclusivity, lifetime, multi-candidate cleanup,
directory-handle cleanup, malformed-status, API-unavailability, late-swap,
write/flush-failure, and bootstrap tests in 0.068 seconds. The live second
writer was rejected while the staged handle remained owned. Rename-success /
first-close-failure retried closure through transaction cleanup with no temp
residue; first-disposition failure still cleaned both candidates and reported a
typed aggregate; first-directory-close failure did not skip the other two
handles. Nonzero/malformed create, rename, disposition, and close results plus
missing symbols all failed closed as typed errors.

The canonical commit is
`8d881db34453723e64fe06f6b4bf3ea760c3feed`
(`fix(evidence): close native transaction gaps`). It changes only
`tools/generate_evidence_manifests.py` and
`tests/test_evidence_manifest_generation.py`; all production hunks are in the
native destination transaction/cleanup region. Its single clean cherry-pick is
development commit `75caae4bc0e723f7f2bbe7d0fb596c4213ab53b7`.
Development v9 was unchanged before and after at 494 bytes/SHA-256
`98493b...f0d6`.

Fresh post-integration verification used the scrubbed canonical snapshot
`C:\Users\point\AppData\Local\Temp\pontius-task3b-fix3-final-cbe849e9c8264f4c9b4aad6ef8302247`
at `75caae4`, the approved copied venv Python, `-B -P`, snapshot cwd, and
`PYTHONPATH=H/src`. Generator `--check` exited 0; 49 generation/oracle tests
passed in 36.599 seconds; 11 manifest/parser tests passed in 0.037 seconds; and
7 Task 1 model/error tests passed in 0.001 seconds. `git diff --check`, full
`git diff --exit-code HEAD --`, and status were clean.

Independent standard-library parsing again proved the candidate is exactly
44,301 bytes/SHA-256 `92e538f...55c2`, with 167 ordered unique rows and both
digests `812ce6b5...99c89`. The unchanged manifest identities remain
2,191/`4147b3f...5580`, 4,772/`592b391...be63`,
64,840/`baa6a48...8f9`, and 2,883/`e2ff537...ff83`; canonical v9 remains
482/`57c869...a535`. The fresh snapshots are retained for controller cleanup.
The POSIX branch remains unexecuted on this Windows host.

## Fix round 4 — retry-safe native ownership and independent fault matrix

Review of `75caae4` found that the native cleanup sequence could report
success after closing an unrenamed handle whose deletion had never been
confirmed, could repeat disposition after a confirmed disposition followed by
close failure, and could lose a valid `NtCreateFile` handle when its return
metadata was malformed. The same review found that body errors could be
replaced by cleanup aggregates and that the native fault tests conflated
several independent return channels. This round was developed only in
disposable canonical snapshots from exact base
`75caae4bc0e723f7f2bbe7d0fb596c4213ab53b7`. No approved repository
`--write`, seed reapproval, manifest rewrite, evidence lifecycle operation, or
v9 operation occurred.

The retained initial RED snapshot is
`C:\Users\point\AppData\Local\Temp\pontius-task3b-fix4-red-7275bf9ad31d4992843b55349409fc9e`
with its dedicated Git home beside it. After two test-harness-only corrections,
the following eleven-test command exited 1 with 15 assertion-failure records,
zero errors, and a 0.012-second runtime:

~~~powershell
& $python -B -P tests/test_evidence_manifest_generation.py `
  EvidenceManifestGenerationTests.test_windows_file_api_fault_matrix_is_typed_one_variable_at_a_time `
  EvidenceManifestGenerationTests.test_windows_directory_api_fault_matrix_is_typed_one_variable_at_a_time `
  EvidenceManifestGenerationTests.test_windows_directory_native_calls_and_close_failures_are_typed `
  EvidenceManifestGenerationTests.test_windows_create_fault_matrix_varies_one_result_at_a_time `
  EvidenceManifestGenerationTests.test_windows_rename_and_disposition_status_channels_are_independent `
  EvidenceManifestGenerationTests.test_windows_write_fault_matrix_and_partial_progress `
  EvidenceManifestGenerationTests.test_windows_flush_and_file_close_faults_are_typed `
  EvidenceManifestGenerationTests.test_windows_cleanup_never_closes_an_unarmed_candidate `
  EvidenceManifestGenerationTests.test_windows_cleanup_does_not_rearm_deletion_after_close_failure `
  EvidenceManifestGenerationTests.test_windows_malformed_create_is_registered_before_validation_cleanup `
  EvidenceManifestGenerationTests.test_transaction_exit_preserves_body_and_every_cleanup_failure -v
~~~

Those failures isolated missing typed DLL/symbol/native translations, the
conflated status channels, partial-write handling, invalid cleanup transitions,
lost malformed-create ownership, and loss of the initiating body error. Three
later self-review regressions were also RED before their production changes:
the body/cleanup aggregate exposed two nested errors instead of five ordered
leaf errors; a valid component-directory handle disappeared when identity
inspection and close both failed (the ownership list was empty instead of
`[(root, 101, None)]`); and a completely recovered transient disposition
failure incorrectly retained the transaction as an owner.

The implementation gives each Windows candidate the explicit transition set
`unacquired -> open -> deletion_armed|renamed -> closed`. The transaction
registers the candidate before `NtCreateFile` and claims every non-null,
non-invalid handle before validating the native return status,
`IO_STATUS_BLOCK.Status`, or `Information`, including when the native callable
raises after populating the handle. A malformed success therefore remains
owned and follows the same cleanup state machine. The POSIX candidate state is
still path-owned and its `dir_fd` mutation behavior was not changed.

Cleanup issues at most two disposition calls while the state is `open`. A
confirmed disposition immediately persists `deletion_armed`; a subsequent
close failure retains that state and handle, so a retry calls only
`CloseHandle`. A successful rename likewise persists `renamed` before close,
and a retry never applies disposition to the destination. If both disposition
attempts fail, `CloseHandle` is deliberately not called: the exact terminal
state is an `open` candidate with its raw handle still present in the
transaction ownership list, and the raised typed aggregate retains both the
candidate and transaction for an explicit later retry. This is the fail-closed
choice when residue-free deletion cannot be proved. A transient first
disposition failure that recovers is still reported, but successful close
transitions to `closed`, removes ownership, and exposes no retained owner.

Valid root/docs/architecture handles are now also inserted into transaction
ownership with an unverified identity before their first component identity
call. Identity failure is therefore cleaned through the normal exhaustive
transaction path; close failure leaves the provisional `(path, handle, None)`
entry available for retry. Transaction close visits every candidate, every
POSIX descriptor, and every Windows component handle even after earlier
failures. Typed aggregates recursively flatten their ordered leaf failures,
preserve their native causes, carry only owners that still hold resources, and
place an initiating body/setup error before every cleanup failure.

The independent one-variable-at-a-time Windows matrix covers both relevant
DLL load failures; missing `NtCreateFile`, `NtSetInformationFile`, `WriteFile`,
`FlushFileBuffers`, and `CloseHandle`; missing `CreateFileW`,
`GetFileInformationByHandle`, and directory `CloseHandle`; directory create
exception/null/invalid results, identity exception/false, and close
exception/false; `NtCreateFile` return status, I/O status, information, null
handle, invalid handle, and exception; rename return status versus I/O status
versus exception; disposition return status versus I/O status versus
exception; `WriteFile` false, exception, zero, oversized, and multi-iteration
partial progress; flush false/exception; file close false/exception; two
disposition failures; disposition success followed by close failure; valid
malformed-create ownership; and body plus every candidate cleanup failure.
The pre-existing exhaustive component-close and real exclusive raw-handle,
late-swap, bootstrap, and handle-relative mutation tests remain active.

The retained GREEN development snapshot is
`C:\Users\point\AppData\Local\Temp\pontius-task3b-fix4-green-e6f71ea915114523b90528dc1f610381`.
Its final focused native/state set passed 13 tests in 0.056 seconds, and its
full generation/oracle suite passed 61 tests in 37.649 seconds. Generator
`--check`, 11 manifest/parser tests, 7 model/error tests, and
`git diff --check` also exited 0. The canonical commit is
`b6add2a18cef7d4d79eb3e5b49f88df5e8ea00a4`
(`fix(evidence): make native cleanup retry-safe`) and changes only
`tools/generate_evidence_manifests.py` and
`tests/test_evidence_manifest_generation.py`. Its single clean cherry-pick is
development commit `89303d1e7bdda4f3aec74b131d8a8cc8d1afcc09` on parent
`75caae4`.

Fresh post-integration verification used the detached scrubbed snapshot
`C:\Users\point\AppData\Local\Temp\pontius-task3b-fix4-final-f45fb7a1d48e4a40a8e2424f959acb6d`
at `89303d1`. The focused native/state matrix passed 13 tests in 0.028
seconds; the full generation/oracle suite passed 61 tests in 38.622 seconds;
generator `--check` exited 0; the manifest/parser suite passed 11 tests in
0.040 seconds; and the model/error suite passed 7 tests in 0.001 seconds.
`git diff --check`, `git diff --exit-code HEAD --`, and status were clean.

An independent standard-library audit in that final snapshot proved that the
approved artifact remains exactly 44,301 bytes/SHA-256
`92e538f7d88ec7bb632d380525b61c0a5c35630f37f4aeb6a55ee4b051bd55c2`;
its 167 ordered unique rows exactly equal the historical TOML rows; and the
independently reconstructed semantic digest is
`812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89`.
The four frozen manifest identities remain 64,840/
`baa6a485717360a990120dfce6d8461a046e64470741cbf914e8daa1937ad8f9`,
2,883/`e2ff5371bdf01ea5a15f2b38eda057fc6a0947f83a55faf46a47dfd0cf67ff83`,
4,772/`592b3916ee32c5ab9b212e29f2b1f163651da4bd0abb7c885a2cddb83e48be63`,
and 2,191/`4147b3f066642ba1e4d2ab6b2028c4d17ab3922141c0edff8c7312545dd75580`.
All six current file identities and all eighteen absences were exact. The
canonical v9 stayed 482 bytes/
`57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535`;
the development representation stayed 494 bytes/
`98493b5047ab04267c8b8ab41adccd30a63a53ef6aa441a02d92ece52985f0d6`
before and after integration. The RED, GREEN, final snapshots and their Git
homes are intentionally retained for controller cleanup. The POSIX branch was
preserved but was not executable on this Windows verification host.
