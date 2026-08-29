# Task 11a report — legacy dependency baseline and early checker contract

## Status

Task 11a is implemented and committed on the isolated branch
`codex/orch-task11a`. Task 11b was deliberately not implemented or claimed.

- Base commit: `89303d1e7bdda4f3aec74b131d8a8cc8d1afcc09`
- Initial Task 11a commit: `79751648d1c2006bc2ad5d1212786db4e8eb314b`
- Initial commit message: `test(architecture): lock legacy graph baseline`
- Review-hardening commit: `88a553c34f4522439d04e1f49a2c2e88e97c1927`
- Hardening commit message:
  `fix(architecture): harden dependency baseline checks`
- Worktree after commit: clean
- Push/merge/cherry-pick: not performed

## Changed files

- `tools/generate_dependency_baseline.py`
- `tools/check_stabilization_boundaries.py`
- `docs/architecture/dependency-baseline.toml`
- `tests/test_stabilization_boundaries.py`
- `tests/test_test_orchestration_import_boundary.py`

The implementation is standard-library-only. The generator requires an explicit
absolute `PONTIUS_GIT`, defaults to `--check`, and accepts `--write` only when the
argument is the exact absolute
`docs/architecture/dependency-baseline.toml` destination. The checker enforces
the plan-declared evidence/orchestration origin sets, legacy outgoing-edge parity,
the evidence and orchestration allowlists, and no new/expanded cyclic SCC.

## Exact generated baseline

- Schema: `pontius-dependency-baseline-v1`
- Baseline commit: `a842c4b6a73a2991a63a481f4107580b72750582`
- Modules: `470`
- Internal edges: `2577`
- Edge digest: `c178ed92158da1c544abaf39ab14842721658a31f3f9246cbeb3e05e3e3da6ee`
- SCCs: `469`
- SCC digest: `9987fddd06742fc2af87de7b8ebf79bc8b2dda7231260f7cc9efdcca18dff345`
- Grandfathered cyclic SCC: `pontius.action_clock`,
  `pontius.preparation_bank`
- Generated artifact: `373157` bytes, `13602` LF-only lines
- Generated artifact raw SHA-256:
  `b86dd2ba20e4639bc6c0184367a82b01ef3b1960ce863406f30964dd5c8625c6`

The package file is mechanically named `pontius.__init__`; that convention is
required for the two approved row digests above. An independent full-row audit
parsed the complete TOML without importing either Task 11a tool and verified exact
top-level keys, row counts, order/uniqueness, endpoint resolution, one-time SCC
coverage, both canonical TSV digests, the one cyclic SCC, LF-only encoding, and
the raw artifact digest.

## TDD evidence

All payload commands below ran only from disposable canonical OS-temp snapshots,
with the copied regular development interpreter, `-B -P`, cwd equal to the
snapshot harness, and `PYTHONPATH` exactly `<H>/src`. Every named snapshot was
validated and removed after its run.

### Initial RED

Snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-orch11a-red-2e7896c2b8844b46b3af263189246609\harness`

Commands:

```powershell
& $python -B -P tests/test_stabilization_boundaries.py -v
& $python -B -P tests/test_test_orchestration_import_boundary.py -v
```

Both returned exit `1` because the exact-path loads of
`tools/generate_dependency_baseline.py` and
`tools/check_stabilization_boundaries.py` failed with `FileNotFoundError`. This
was the intended missing-feature RED.

### Scanner canonicalization correction

The first implementation run preserved the exact graph counts but exposed two
real contract mismatches: the root package row naming did not reproduce the
approved digests, and a synthetic root-package `from ... import ...` did not
retain its complete target when the target module was absent from the fixture.
The corrected mechanical `pontius.__init__` convention produced both approved
digests and the import fixture then reported the exact forbidden edge.

### Explicit-origin RED/GREEN

RED snapshot:
`pontius-orch11a-class-red-1ca13af9cbfc40a5bf1b1c968f00efcf`.
The focused test returned exit `1` with `AttributeError` because
`enforce_origin_classification` did not exist.

GREEN snapshot:
`pontius-orch11a-class-green-d135008acb3c49159b038e2153f351a5`.
The same focused test passed, proving that accepted plan paths are admitted and
unplanned evidence/tool origins are reported exactly.

### Explicit-Git RED/GREEN

RED snapshot:
`pontius-orch11a-git-red-9b08d40de13a45058a5c5c401ac21b79`.
The focused test returned exit `1` because the strict explicit-Git resolver did
not exist.

GREEN snapshot:
`pontius-orch11a-git-green-4572708664244732a81974ca0b8562e8`.
The focused test passed: absent and relative `PONTIUS_GIT` values reject, while
the supplied absolute executable is accepted for later identity validation.

## Baseline write and final verification

The one branch-local write was explicit:

```powershell
& $python -B -P tools/generate_dependency_baseline.py `
  --write 'C:\Users\point\AppData\Local\Temp\pontius-orch-task11a\docs\architecture\dependency-baseline.toml'
```

Exit status: `0`. The complete generated artifact was then inspected through the
independent row audit described above.

Final fresh snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-orch11a-final2-0016f4b4d4b64a57be08bf76d54dfc72\harness`
(removed after verification).

Commands and results:

```powershell
& $python -B -P tests/test_stabilization_boundaries.py -v
# Ran 10 tests in 1.772s — OK

& $python -B -P tests/test_test_orchestration_import_boundary.py -v
# Ran 3 tests in 0.001s — OK

& $python -B -P tools/generate_dependency_baseline.py
# exit 0; proved default --check

& $python -B -P tools/generate_dependency_baseline.py --check
# exit 0

& $python -B -P tools/check_stabilization_boundaries.py
# exit 0
```

The final snapshot remained at HEAD
`89303d1e7bdda4f3aec74b131d8a8cc8d1afcc09`, emitted no `__pycache__`, `.pyc`, or
`.pyo`, and every file-level overlay SHA-256 matched the isolated implementation
worktree before execution.

Post-verification repository checks:

- `git diff --cached --check`: exit `0`
- `git diff HEAD^ HEAD --check`: exit `0`
- committed blobs equal the verified worktree bytes for all five files
- branch status after commit: clean
- primary checkout remains `master` at
  `a842c4b6a73a2991a63a481f4107580b72750582`, with only its pre-existing
  untracked `docs/superpowers/`
- protected development-worktree v9 file remains the pre-existing CRLF checkout
  identity: `494` bytes / SHA-256
  `98493b5047ab04267c8b8ab41adccd30a63a53ef6aa441a02d92ece52985f0d6`

## Mutation coverage

The focused tests prove failures for:

- wrong row digests, boolean counts, extra keys, and unsorted/invalid module rows;
- absolute, relative, and `TYPE_CHECKING` import resolution;
- missing/relative Git executable configuration;
- changed legacy outgoing edges;
- forbidden evidence imports to compiled-calibration code, tests, and CuPy;
- forbidden parent imports to `pontius`, tests, experiments, CuPy, and a sealed
  compiled-calibration runner;
- unplanned stabilization origins; and
- a new/expanded cyclic SCC.

## Limitations and deliberate exclusions

- Task 11b is not implemented. This task does not claim real
  `tools/run_tests.py` / `tools/test_child.py` integration, current-profile
  pre-spawn refusal, or any parent/child discovery/owner-launch scan.
- No real profile or scientific owner was launched.
- `PONTIUS_RUFF` is unset, so Ruff was not run and no Ruff/static-tool success is
  claimed. The repository line-length check found zero changed Python lines over
  100 characters.
- The initial implementation was subsequently subjected to the completed
  independent hardening review documented below.

## Round 1 review hardening — 2026-08-27

### Status and scope

Round 1 is complete and independently approved. CodeRabbit reported zero issues
on the final candidate, and the independent manual security/correctness rereview
returned **Approved — no actionable findings**. The hardening commit is separate
from the initial Task 11a commit and changes only:

- `tools/generate_dependency_baseline.py`
- `tools/check_stabilization_boundaries.py`
- `tests/test_stabilization_boundaries.py`

`docs/architecture/dependency-baseline.toml` and
`tests/test_test_orchestration_import_boundary.py` are unchanged in this
follow-up. Task 11b remains explicitly excluded. No push, merge, or cherry-pick
was performed.

### Review findings resolved

- The checker now authenticates its own literal approved commit, module/edge/SCC
  counts, and graph digests. A valid, internally self-consistent forged baseline
  and simultaneous generator/TOML commit drift both reject.
- Baseline and source reads are bounded, no-follow, identity-bound snapshots with
  ancestor validation, pre/path/handle/post checks, exact-byte revalidation,
  complete Python inventory revalidation, and a final source/baseline pass.
  Same-size replacement, same-size mutation, concealed-content mutation, and
  cross-file/inventory mutation fixtures reject.
- Explicit `--write` binds the validated directory object through staging and
  atomic replacement. Windows uses handle-relative creation/replacement and a
  full 128-bit `FILE_ID_INFO`; POSIX uses retained directory/file descriptors and
  descriptor-relative operations. Symlink, junction/reparse, bind-time swap,
  pre-stage swap, replace-time swap, staged-entry substitution, staging fault,
  and replacement fault cases are covered.
- Every ambiguous file/directory close is single-attempt and enters terminal
  close-attempted state before the syscall. Provisional POSIX descriptors and
  Windows binding failures retain explicit ownership metadata. Windows directory
  access is least-privilege `FILE_TRAVERSE` plus required attribute/synchronize
  rights, without `FILE_LIST_DIRECTORY`.
- POSIX failure cleanup is intentionally close-only. It never unlinks a
  rebindable pathname after failure, so it cannot delete a concurrently
  substituted entry. A unique `.tmp` can remain for manual inspection/removal;
  Windows safely retains handle-based delete-on-close cleanup.
- Fresh `core.autocrlf=true` checkouts accept only the exact whole-file CRLF
  transformation of the canonical LF artifact. Mixed or otherwise changed line
  endings reject. No `.gitattributes` change was made because checkout-policy
  expansion was outside the approved Task 11a file scope.

### Round 1 RED evidence

Every payload ran only in a fresh disposable canonical OS-temp snapshot using:

```powershell
$env:PYTHONPATH = '<H>/src'
$env:PONTIUS_GIT = 'C:\Program Files\Git\cmd\git.exe'
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P ...
```

The principal final review cycles were:

- `pontius-orch11a-final-red-6a6c11d23fe746b39230a404d55400e8`:
  34 tests ran; five failed for retrying ambiguous Windows/POSIX closes, mutable
  checker commit authentication, and excess Windows listing access.
- `pontius-orch11a-cleanup-red-47049d629e404d0e9789d4b33095324e`:
  39 tests ran; five failed for substituted-entry unlink, POSIX descriptor loss
  before `fstat`, retryable directory closes, and unchecked Windows handle
  cleanup after descriptor-binding failure.
- `pontius-orch11a-final-race-red-3e3c4c6c3ab647b5a774793cc8411d86`:
  41 tests ran; two failed, proving a matching POSIX pathname could still be
  unlinked after a raceable check and a Windows directory API-resolution error
  could lose acquired-handle ownership metadata.

Earlier focused RED snapshots also proved the original checker trusted mutable
baseline metadata, snapshot/inventory final passes were incomplete, exact-case
Python inventory was bypassable, and writer fault/race cleanup lacked retained
ownership. Each failure preceded its implementation change.

### Round 1 GREEN and final acceptance

Focused GREEN snapshots progressed from 34 to 39 to 41 tests. The final
acceptance snapshot was:

`C:\Users\point\AppData\Local\Temp\pontius-orch11a-r1-final-accept-06b55a3c5d8d4597b0dc30151252ffeb\harness`

It was a fresh `core.autocrlf=true` checkout of parent commit
`79751648d1c2006bc2ad5d1212786db4e8eb314b` with only the three candidate files
overlaid. Commands and results:

```powershell
& $python -B -P -m unittest discover -s tests `
  -p test_stabilization_boundaries.py -v
# Ran 41 tests in 16.197s — OK (1 POSIX-runtime-only skip)

& $python -B -P -m unittest discover -s tests `
  -p test_test_orchestration_import_boundary.py -v
# Ran 3 tests in 0.001s — OK

& $python -B -P tools/generate_dependency_baseline.py
& $python -B -P tools/generate_dependency_baseline.py --check
& $python -B -P tools/check_stabilization_boundaries.py
# Exact CRLF checkout: all exit 0

& $python -B -P tools/generate_dependency_baseline.py --write $baseline
& $python -B -P tools/generate_dependency_baseline.py --check
& $python -B -P tools/check_stabilization_boundaries.py
# Secure canonical LF write and both LF checks: all exit 0
```

Fresh-checkout and artifact invariants:

- CRLF checkout: `386759` physical bytes / `13602` CR bytes
- canonical LF artifact: `373157` bytes / zero CR bytes
- raw LF artifact SHA-256:
  `b86dd2ba20e4639bc6c0184367a82b01ef3b1960ce863406f30964dd5c8625c6`
- snapshot HEAD remained
  `79751648d1c2006bc2ad5d1212786db4e8eb314b`
- `PYTHONPATH` was exactly `<H>/src`
- `__pycache__`, `.pyc`, and `.pyo` count: zero
- all three overlaid file SHA-256 values matched the isolated worktree before
  commit

The exact approved graph remained unchanged:

- modules: `470`
- edges: `2577`
- edge digest:
  `c178ed92158da1c544abaf39ab14842721658a31f3f9246cbeb3e05e3e3da6ee`
- SCCs: `469`
- SCC digest:
  `9987fddd06742fc2af87de7b8ebf79bc8b2dda7231260f7cc9efdcca18dff345`
- one grandfathered cyclic SCC: `pontius.action_clock`,
  `pontius.preparation_bank`

### Commit and closeout checks

- Hardening commit: `88a553c34f4522439d04e1f49a2c2e88e97c1927`
- Parent: `79751648d1c2006bc2ad5d1212786db4e8eb314b`
- `git diff --cached --check` before commit: exit `0`
- `git diff HEAD^ HEAD --check` after commit: exit `0`
- committed file whitelist: exactly the three round-1 files named above
- changed-Python line-length scan: zero lines over 100 characters
- post-commit index and worktree diffs: empty
- checked-in baseline diff: empty; raw SHA-256 unchanged

### Limitations and deliberate exclusions

- The real POSIX staged-entry mutation test is skipped on this Windows host.
  Platform-neutral fault mocks cover POSIX identity, close-only cleanup,
  provisional ownership, and terminal close behavior, but no native POSIX
  runtime success is claimed.
- POSIX failure cleanup may retain its uniquely named `.tmp` rather than risk
  unlinking a substituted entry. This is an intentional fail-secure tradeoff.
- Task 11b real parent/child integration, current-profile execution, and
  discovery/owner-launch validation were not created or claimed.
- No `.gitattributes` checkout-policy change, protected v2-v9 artifact change,
  primary-checkout mutation, push, merge, or cherry-pick occurred.

## Round 2 OneDrive compatibility — 2026-08-27

The controller rereview reported that a blanket Windows reparse policy could
reject the supported OneDrive primary checkout. The user explicitly approved a
narrow correction: identity-stable, non-name-surrogate OneDrive cloud tags may
be read only while symlinks, junctions, mount points, unknown tags, and escapes
remain denied. The same approval added exact LF attributes for the three
generated governance files.

Direct host evidence refined the root cause. PowerShell decorates the hydrated
OneDrive tree as `ReparsePoint`, but Python `os.lstat`,
`GetFileInformationByHandle`, `FileAttributeTagInfo`, and
`FSCTL_GET_REPARSE_POINT` expose the hydrated files as ordinary objects. The
actual first-pass failure was a ctime-only transition while OneDrive hydrated a
file during its first read. The fix therefore does both of the following:

- recognizes only the Microsoft cloud tag family `0x9000001A` through
  `0x9000F01A` when such a tag is visible and its name-surrogate bit is clear;
  all other reparse metadata still rejects, and held Windows directory handles
  independently query and validate `FileAttributeTagInfo`;
- discards a read whose handle identity changed only in ctime, then performs
  one complete fresh identity-bound snapshot attempt. A second transition, or
  any device/inode/size/mtime/mode/attribute/tag change, rejects.

RED snapshot
`pontius-orch11a-r2-red-a05df32255bd4ae6be04da5b7ac7214e` ran 44 tests:
the new tag-policy/handle tests errored because the classifier did not exist,
and the metadata-transition test failed at the original identity check.

GREEN snapshot
`pontius-orch11a-r2-green1-d47649ef41a64621b0165c67e41316f9` ran 46 tests:
all passed with the one expected POSIX-runtime-only skip. The three orchestration
import-boundary tests also passed. Default and explicit generator checks, the
real boundary checker, secure `--write`, and post-write LF checks all exited
zero. The written artifact remained exactly 373,157 bytes with SHA-256
`b86dd2ba20e4639bc6c0184367a82b01ef3b1960ce863406f30964dd5c8625c6`.

A separate read-only diagnostic captured and revalidated all 470 Python files
under the real OneDrive primary `src/pontius` in one pass after the fix. No
primary file was written. The approved graph counts and graph digests remain
unchanged. The repository `.gitattributes` now pins
`docs/architecture/dependency-baseline.toml`, `tests/test-inventory.json`, and
`tests/test-profiles.toml` to LF, as explicitly approved by the user.

Round 2 commit: `94c79c7e0b92429aa467e704c27c42dcdbd5c9ea`
(`fix(architecture): support OneDrive snapshots`). Final fresh
`core.autocrlf=true` checkout
`pontius-orch11a-r2-final-50e9e7428bb7447d882efef82101d584`
ran 46 Task 11a tests (one POSIX-only skip) and all three import-boundary tests.
Generator/checker acceptance passed; the LF attribute produced the exact
373,157-byte, zero-CR baseline with SHA-256 `b86dd2ba20e4639bc6c0184367a82b01ef3b1960ce863406f30964dd5c8625c6`.
The snapshot stayed at the round-2 commit, its worktree was clean, and it
contained zero cache artifacts.

### Round 3 executable-boundary correction

Round-2 rereview found that the repository-data cloud classifier had also been
used for `PONTIUS_GIT`. That was too broad: source data may use the narrowly
approved cloud-tag family, but an executable must remain an absolute regular
file with no reparse metadata of any kind. A fresh RED run added a synthetic
cloud-tagged executable and failed because it was accepted. The production
boundary now uses a separate strict any-reparse predicate. The same snapshot
then ran 47 tests GREEN (one POSIX-only skip), and generator/checker acceptance
both exited zero. No graph or artifact byte changed.

### Round 4 regular-file handle metadata binding

Round-3 rereview found that CPython's Windows `fstat` exposes the reparse-point
attribute on an opened regular file but can omit its reparse tag. That made the
path-side cloud decision stronger than the handle-side decision. The reader now
queries `FileAttributeTagInfo` directly on the opened OS handle both before and
after reading, incorporates the exact attribute/tag pair into the snapshot
identity and hydration-transition check, and requires exact path/handle
attribute and tag agreement. Unknown tags, name-surrogate tags, a tag transition
during the read, and an opening-time path/handle mismatch all reject.

The valid RED snapshot was
`pontius-orch11a-r4-red-cada4357c3844c6f98ce3e16da7d2aad`: 48 tests ran and
the two new contract paths errored because the handle query and expanded API
binding were absent. The fresh GREEN snapshot was
`pontius-orch11a-r4-green-3b34506ac6d34f10bb83e08ae1a8e4f1`: all 48 tests
passed with the one expected POSIX-runtime-only skip, all three orchestration
import-boundary tests passed, default/explicit generator checks passed, the
boundary checker passed, and secure `--write` followed by both checks passed.

A separate read-only run used the candidate reader against the real OneDrive
primary checkout and captured plus revalidated all 470 `src/pontius` Python
files. The generated baseline remained exactly 373,157 LF bytes with zero CR
bytes and SHA-256
`b86dd2ba20e4639bc6c0184367a82b01ef3b1960ce863406f30964dd5c8625c6`.
The snapshot stayed at parent `fffef41cc63492c333bbbf6f181ca4e18861aece`
and produced zero `.pyc`/`.pyo` cache files. The approved 470-module,
2,577-edge, 469-SCC graph and its digests are unchanged.

Round 4 commit: `ea9f7cd1622af7cf724d2816fdb0f4f8f307300d`
(`fix(architecture): bind Windows file reparse metadata`). The isolated Task
11a worktree was clean after commit.

The independent round-4 rereview returned CLEAN at `ea9f7cd`: it confirmed the
two handle metadata queries, exact path/handle and transition binding, all five
cloud/reparse acceptance and rejection cases, and that two late nested atomic
findings referred to superseded code (current POSIX failure cleanup is
close-only, and current Windows directory-close failures retain the numeric
handle). CodeRabbit then reviewed the complete Task 11a diff from `89303d1`
through `ea9f7cd` across all six changed files and raised 0 issues.
