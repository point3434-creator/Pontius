# Task 3a report — preapproval evidence manifest generator

## Status

Implemented the preapproval-only Task 3 generator and tests. The generator is
standard-library-only, derives the deterministic historical seed, provides
file-local strict TOML/canonical semantic conformance, securely measures current
evidence, binds bounded Git subprocesses to the required executable and scrubbed
environment, refuses unapproved writes before touching destinations, implements
read-only --check, and emits the complete explicit seed-review table outside the
repository.

The hard approval gate remains closed. No postapproval ordered-row/count/digest
oracle was added, --write was never invoked, and none of the four manifest
destinations was created or modified.

Scoped local commit:
c24fd4f4b5f68cecca74f23385b02141fa890ed8
(build(evidence): prepare guarded manifest seed review)

## Changed files

- tools/generate_evidence_manifests.py — deterministic constants, secure
  one-read reader, bounded Git adapter, AST/literal historical closure, local
  TOML/canonical parsers, render/check/review emission, and approval-token gate.
- tests/test_evidence_manifest_generation.py — fixed present/absence/snapshot,
  v7 source-seal and authorization groups, retained facts, generic digest,
  reader/Git, review artifact, check, and invalid-approval/no-write behavior.
- tests/test_evidence_manifests.py — active-parser/tool-local parser and
  canonical encoder conformance vectors.

Task 4's active reader does not yet exist by plan order. Task 3a locks the
tool-local reader contract/factory seam; Task 4 is responsible for adding the
active second factory to the shared conformance surface.

## RED evidence

Snapshot:
C:\Users\point\AppData\Local\Temp\pontius-task3a-red-ee89452031464cf296e65791ffddc08d

Command (cwd was the snapshot and PYTHONPATH was exactly H/src):

~~~powershell
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_manifest_generation.py -v
~~~

Exit status: 1. Expected failure:

~~~text
FileNotFoundError: ...\tools\generate_evidence_manifests.py
~~~

The production generator did not exist.

## GREEN evidence

Snapshot:
C:\Users\point\AppData\Local\Temp\pontius-task3a-green2-d0bcfd5014ca404f83deee9a736c33c1

Commands used the required interpreter with -B -P, snapshot cwd, and PYTHONPATH
exactly H/src:

~~~powershell
& $python -B -P tests/test_evidence_manifest_generation.py -v
& $python -B -P tests/test_evidence_manifests.py -v
& $python -B -P tests/test_evidence_errors_and_model.py -v
~~~

Results:

~~~text
Ran 9 tests in 161.002s
OK

Ran 10 tests in 0.012s
OK

Ran 7 tests in 0.001s
OK
~~~

The first GREEN attempt in
C:\Users\point\AppData\Local\Temp\pontius-task3a-green1-8eec411c437e494a8de38c317956b0f9
failed before collection because Windows lstat and fstat return different
st_ctime_ns values for the same unchanged file. A diagnostic showed all stable
path/handle identity fields agreed. The reader now compares stable cross-API
identity fields at path/handle boundaries while preserving complete
handle-before/handle-after identity verification.

## CLI evidence

Actual default --check was run in the GREEN snapshot without a command flag.
It exited 2 with:

~~~text
evidence manifest generation failed: historical manifest is absent or unreadable; approval and --write are still required
~~~

All four snapshot destinations were absent before and after that command.

Only this permitted preapproval output command was invoked. Its repository/cwd
was the exact GREEN snapshot above:

~~~powershell
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tools/generate_evidence_manifests.py --emit-seed-review 'C:\Users\point\AppData\Local\Temp\pontius-task3-seed-review-dfb8a9ada629471298fde4a2c83aece2.txt'
~~~

Exit status: 0.

## Seed-review artifact

- Absolute path:
  C:\Users\point\AppData\Local\Temp\pontius-task3-seed-review-dfb8a9ada629471298fde4a2c83aece2.txt
- Verified outside repository: true
- Explicit ordered row count: 1515
- Normalized seed SHA-256:
  b1188f35ebade4a51abecc75253667111b0a1037d1ebd44dff50753dfec17cc6
- Artifact byte length: 401891
- Artifact SHA-256:
  c36cafc6cdb8563a777f9042f5e087a5dea3523babdf5be43699d6dfd3484b68

An independent parser reconstructed all 1,515 row mappings from the TSV,
canonicalized them without importing the generator, and reproduced the claimed
normalized digest exactly (exit 0).

## Manifest no-write proof

At base 4da92ebe48231d1b8913bf89d170b410e6bf7163 and immediately before commit:

~~~text
docs/architecture/sealed-current-files.toml    base=absent worktree=absent
docs/architecture/sealed-current-absences.toml base=absent worktree=absent
docs/architecture/historical-blobs.toml        base=absent worktree=absent
docs/architecture/retained-v7.toml              base=absent worktree=absent
~~~

git diff --exit-code 4da92ebe... over the four paths exited 0. The --write
command was not invoked. Invalid approval tests called the internal guarded seam
with missing, malformed, uppercase, and stale digests and proved refusal before
any destination existed.

## Present/absence remeasurement and concern

The canonical GREEN snapshot proved the exact v9 authorization identity:

~~~text
bytes=482
sha256=57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535
Git blob OID=6e7881032bdaaa55a45bf7465e4f94679e4e983c
~~~

Five of six development-worktree present identities match exactly, and all 18
protected absences remain absent. The v9 authorization configuration is a
pre-existing checkout-representation mismatch:

~~~text
approved/snapshot: 482 bytes
  57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535
development worktree: 494 bytes
  98493b5047ab04267c8b8ab41adccd30a63a53ef6aa441a02d92ece52985f0d6
development raw worktree blob OID:
  76cdbb746f6b070fdb9ff3bd2f399635952ec902
filtered/index/HEAD blob OID:
  6e7881032bdaaa55a45bf7465e4f94679e4e983c
~~~

Git reports the path clean because system core.autocrlf=true: its raw worktree
blob OID differs, while Git's filtered OID equals the index/HEAD OID. The
scrubbed disposable snapshot held the approved 482-byte identity and all
generator checks passed there. This task did not normalize, checkout, add, or
otherwise touch the protected file. Direct generator use from the development
worktree correctly fails closed until that checkout representation is resolved
by the controller under separate authority.

Ruff was not provisioned through absolute PONTIUS_RUFF; no Ruff result is
claimed. Disposable snapshots were intentionally left for controller cleanup.

## Fix round 1 — rejected broad historical boundary

The original 1,515-row artifact and its digest are rejected review material and
must never be treated as approval. Fix round 1 constrains each earlier phase to
the exact named selected class, the module-level bindings/fixtures it actually
loads, the directly named owner/reader/runner modules, and existing tracked
configuration/decision literals only. It does not recursively expand imports
from those named modules. Actual fixed `-c` argv programs are parsed, including
named and f-string programs; composed, nonliteral, syntactically invalid, and
unresolved relevant programs fail closed. Package/submodule and relative
package/submodule imports are covered, including pruning unused aliases from a
shared import statement.

The Git adapter now drains stdout and stderr concurrently with in-memory bounds
while the child is running, kills on cap or timeout, closes both pipes, checks
nonzero/malformed output, and revalidates the absolute executable identity
before cache access and after execution. Absolute argv, literal pathspec `--`,
cwd, scrubbed environment, disabled shell, output caps, timeout, nonzero exit,
malformed OID, and executable replacement/cache behavior are locked by tests.

The tool-local secure-reader contract is exposed through
`tool_secure_reader_factory()` for Task 4 to reuse. It rejects symlink/reparse
components and final paths, nonregular files, oversize files, and identity
changes before opening, during the one bounded `os.read`, and after closing.
Task 4 still owns creation of the active second factory; no Task 4 production
code was created here.

Scoped fix commit:
`49f6b8141ad3284c3e33d596a5cfd2155ec8709f`
(`fix(evidence): constrain preapproval seed derivation`)

### Fix-round changed files

- `tools/generate_evidence_manifests.py`
- `tests/test_evidence_manifest_generation.py`
- `tests/test_evidence_manifests.py`

No other path was staged or committed.

### Fix-round RED evidence

Primary RED snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-task3-fix1-red-20260827`

Command, with cwd at the snapshot and `PYTHONPATH=H/src`:

~~~powershell
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P -m unittest discover -s tests -p 'test_evidence_manifest_generation.py' -v
~~~

Result: exit 1; 17 tests ran in 0.034s with 4 failures and 6 errors. The
intended failures identified missing selected-class scoping, relative submodule
resolution, named fixed `-c` parsing, reader factory/component checking,
bounded-process collection, executable revalidation before cache, collision
guarding, and CLI refusal before derivation. The clone also exposed the already
known v9 CRLF checkout mismatch; subsequent evidence used the canonical
snapshot construction documented below.

A focused second RED vector changed the selected/unrelated imports to share one
`from pontius import ...` statement. Before import-alias pruning it failed in
0.001s because `src/pontius/unrelated_owner.py` was incorrectly retained. The
pruned required-binding implementation made that vector green.

### Canonical GREEN snapshot and provenance

Canonical scrubbed snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-task3-fix1-green2-20260827`

It was cloned at pre-fix commit
`c24fd4f4b5f68cecca74f23385b02141fa890ed8`, then the tracked payload was
replaced from this exact no-conversion archive before the three changed files
were overlaid for testing:

~~~powershell
git -c core.autocrlf=false archive --format=zip --output='C:\Users\point\AppData\Local\Temp\pontius-task3-fix1-green2-canonical.zip' c24fd4f4b5f68cecca74f23385b02141fa890ed8
Expand-Archive -LiteralPath 'C:\Users\point\AppData\Local\Temp\pontius-task3-fix1-green2-canonical.zip' -DestinationPath 'C:\Users\point\AppData\Local\Temp\pontius-task3-fix1-green2-20260827' -Force
~~~

The canonical snapshot's protected v9 identity was:

~~~text
bytes=482
sha256=57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535
raw Git blob OID=6e7881032bdaaa55a45bf7465e4f94679e4e983c
~~~

The generation suite remeasured all six present identities and all eighteen
independently locked absence role/decision/owner rows. It passed, proving the
snapshot was canonical and scrubbed for the repository evidence payload.

Exact GREEN commands used the required interpreter, `-B -P`, snapshot cwd, and
`PYTHONPATH` exactly `H/src`:

~~~powershell
& $python -B -P tests/test_evidence_manifest_generation.py
& $python -B -P tests/test_evidence_manifests.py
& $python -B -P tests/test_evidence_errors_and_model.py
~~~

Fresh final results:

~~~text
Ran 19 tests in 17.558s — OK
Ran 11 tests in 0.038s — OK
Ran 7 tests in 0.001s — OK
total command time: 18.507s
~~~

The generation suite has exactly one full historical integration derivation;
focused approval, reader, Git, AST, render, and CLI tests do not repeat it. The
complete Task 2 malformed parser-vector surface is now exercised against both
the active and tool-local parsers, including missing/extra fields, every field's
type, bool/int separation, uppercase/short identities, absolute/drive/traversal
paths, count disagreement, duplicate TOML keys/tables, duplicate historical
identities, and digest disagreement.

Default absent `--check` failed before derivation in 0.152s with exit 2 and:

~~~text
evidence manifest generation failed: historical manifest is absent or unreadable; approval and --write are still required
~~~

All four destinations were absent before and after. Missing/malformed write
approval and invalid seed-review output paths are likewise validated before the
historical walk. The remaining expected bottleneck is the one integration
derivation/emit at about 17.6s, dominated by the required per-final-row Git blob
OID and raw-byte verification; that verification was not weakened.

### Corrected seed-review artifact

The only successful production-style generator command in this fix round was
the permitted review emission below. `--write` was never invoked.

~~~powershell
$env:PYTHONPATH='C:\Users\point\AppData\Local\Temp\pontius-task3-fix1-green2-20260827\src'
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tools/generate_evidence_manifests.py --emit-seed-review 'C:\Users\point\AppData\Local\Temp\pontius-task3-seed-review-fix1-749b2cf8561b4bed8793c379bd6454ee.txt'
~~~

Command cwd/repository was exactly
`C:\Users\point\AppData\Local\Temp\pontius-task3-fix1-green2-20260827`.
Final emission exited 0 in 17.605s.

- Absolute artifact path:
  `C:\Users\point\AppData\Local\Temp\pontius-task3-seed-review-fix1-749b2cf8561b4bed8793c379bd6454ee.txt`
- Verified outside the canonical snapshot/repository: true
- Explicit ordered row count: 167
- Normalized seed SHA-256:
  `812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89`
- Artifact byte length: 44,301
- Artifact SHA-256:
  `92e538f7d88ec7bb632d380525b61c0a5c35630f37f4aeb6a55ee4b051bd55c2`

An independent standard-library parser that did not import the generator read
all 167 TSV rows, reconstructed and sorted the seven-field mappings, serialized
them with the canonical JSON settings, and reproduced the claimed normalized
digest exactly (`MATCH=True`). No exact complete-row count/digest oracle was
added to production or test code.

### Fix-round manifest no-write proof

Immediately before staging, and again after commit, all four destinations were
byte/absence-identical to base `4da92ebe48231d1b8913bf89d170b410e6bf7163`:

~~~text
docs/architecture/sealed-current-files.toml    base=absent worktree=absent
docs/architecture/sealed-current-absences.toml base=absent worktree=absent
docs/architecture/historical-blobs.toml        base=absent worktree=absent
docs/architecture/retained-v7.toml             base=absent worktree=absent
~~~

`git diff --exit-code 4da92ebe... -- <four manifest paths>` exited 0 both before
and after commit. Post-commit `git status --short` was empty. The protected v9
path was not normalized, checked out, added, staged, or otherwise touched in the
implementation worktree. Its unchanged development-worktree representation is:

~~~text
development worktree: 494 bytes
sha256=98493b5047ab04267c8b8ab41adccd30a63a53ef6aa441a02d92ece52985f0d6
raw worktree blob OID=76cdbb746f6b070fdb9ff3bd2f399635952ec902
filtered/index/HEAD blob OID=6e7881032bdaaa55a45bf7465e4f94679e4e983c
canonical snapshot: 482 bytes
sha256=57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535
raw blob OID=6e7881032bdaaa55a45bf7465e4f94679e4e983c
~~~

Consequently, a direct generator invocation from the development worktree must
and does fail closed on that current-evidence mismatch. Disposable RED/GREEN
snapshots and archive files were intentionally left for controller cleanup.
Ruff remains unavailable at the required absolute location, so no Ruff result
is claimed.

## Fix round 2 — lexical fixed `-c` resolution

The fix1 167-row artifact and normalized digest
`812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89`
were explicitly rejected for review and remain unapproved. No approval was
inferred from their values or from the corrected derivation below.

Fix round 2 addresses only the remaining fixed-`-c` review finding. Dynamic
program analysis now inventories assignments independently per function/method,
evaluates bindings in statement order, resolves permitted enclosing constants,
and isolates repeated local `program`/`argv` names across methods. It recognizes
both inline and named fixed argv, resolves the payload after the unique `-c`,
and supports fixed string literals, concatenation, and f-strings. Exact
interpolated import targets are resolved; unresolved targets fail through the
same local-import check instead of being silently omitted. Ambiguous,
reassigned exact, branch-dependent, use-before-assignment, dynamically built,
nonliteral, malformed, and unparseable relevant argv/programs fail closed.
Repeated symbolic context targets such as temporary-directory names remain
usable when their current statement-ordered binding is unique at each use;
they cannot supply or hide a dynamic import target.

All four findings already closed in fix1 were preserved without changing their
tests or contracts.

Scoped fix commit:
`4b72588b9e24dfa934a59fc58cb54c330ed7606f`
(`fix(evidence): resolve dynamic programs lexically`)

Changed files:

- `tools/generate_evidence_manifests.py`
- `tests/test_evidence_manifest_generation.py`

No other file was staged or committed.

### Fix2 RED evidence

Disposable RED snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-task3-fix2-red-20260827`

Snapshot base was fix1 commit
`49f6b8141ad3284c3e33d596a5cfd2155ec8709f`; only the new test payload was
overlaid. With cwd at the snapshot and `PYTHONPATH=H/src`, the exact command was:

~~~powershell
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_manifest_generation.py EvidenceManifestGenerationTests.test_dynamic_dash_c_resolution_is_lexical_and_accepts_named_argv EvidenceManifestGenerationTests.test_dynamic_dash_c_resolves_fixed_fstrings_and_concatenation EvidenceManifestGenerationTests.test_dynamic_dash_c_rejects_ambiguous_dynamic_reassigned_and_branch_values -v
~~~

Result: exit 1; 3 tests ran in 0.003s with 5 failures and 1 error. The old
implementation returned neither method-local import for named argv, raised on
the fixed concatenation/f-string surface, and silently accepted reassigned,
branch-dependent, and unresolved named argv cases.

Two integration-reduced RED vectors were then captured before their minimal
fixes:

- fixed enclosing `ROOT / LAUNCHER` path constants failed with
  `dynamic -c program is not statically fixed`;
- repeated symbolic temporary-directory context targets failed with the same
  error even though statement order uniquely fixed the current context value.

Both now have focused regression tests. The original committed implementation
also failed the new use-before-assignment and reassigned interpolated import
target cases; both are part of the fail-closed table.

### Fix2 canonical GREEN evidence

Canonical snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-task3-fix2-green1-20260827`

It was cloned at fix1 commit
`49f6b8141ad3284c3e33d596a5cfd2155ec8709f`, then reconstructed from an exact
no-conversion archive before the two changed files were overlaid:

~~~powershell
git -c core.autocrlf=false archive --format=zip --output='C:\Users\point\AppData\Local\Temp\pontius-task3-fix2-green1-canonical.zip' 49f6b8141ad3284c3e33d596a5cfd2155ec8709f
Expand-Archive -LiteralPath 'C:\Users\point\AppData\Local\Temp\pontius-task3-fix2-green1-canonical.zip' -DestinationPath 'C:\Users\point\AppData\Local\Temp\pontius-task3-fix2-green1-20260827' -Force
~~~

Canonical v9 identity was reverified as 482 bytes with raw blob OID
`6e7881032bdaaa55a45bf7465e4f94679e4e983c`; the generation suite again proved
all six current identities and all eighteen absences.

The focused lexical command ran 6 tests in 0.002s and passed. Fresh final full
commands used the required interpreter, `-B -P`, snapshot cwd, and
`PYTHONPATH=H/src`:

~~~powershell
& $python -B -P tests/test_evidence_manifest_generation.py
& $python -B -P tests/test_evidence_manifests.py
& $python -B -P tests/test_evidence_errors_and_model.py
~~~

Results:

~~~text
Ran 24 tests in 17.751s — OK
Ran 11 tests in 0.038s — OK
Ran 7 tests in 0.001s — OK
42 tests total; total command time 18.708s
~~~

Default absent `--check` still fails before derivation: exit 2 in 0.158s, with
zero manifests present before and after. The routine-runtime structure and the
single bounded historical integration derivation remain intact.

### Fix2 corrected review artifact

Final emission used cwd/repository exactly
`C:\Users\point\AppData\Local\Temp\pontius-task3-fix2-green1-20260827` and this
permitted command; `--write` was never invoked:

~~~powershell
$env:PYTHONPATH='C:\Users\point\AppData\Local\Temp\pontius-task3-fix2-green1-20260827\src'
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tools/generate_evidence_manifests.py --emit-seed-review 'C:\Users\point\AppData\Local\Temp\pontius-task3-seed-review-fix2-2e39fe4c0afc49a48ec52291113468b8.txt'
~~~

Final emission exited 0 in 17.960s.

- Absolute path:
  `C:\Users\point\AppData\Local\Temp\pontius-task3-seed-review-fix2-2e39fe4c0afc49a48ec52291113468b8.txt`
- Verified outside the repository: true
- Explicit ordered row count: 167
- Normalized SHA-256:
  `812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89`
- Artifact bytes: 44,301
- Artifact SHA-256:
  `92e538f7d88ec7bb632d380525b61c0a5c35630f37f4aeb6a55ee4b051bd55c2`

An independent standard-library parser reconstructed the seven-field mappings,
sorted every row, and reproduced the claimed normalized digest exactly
(`MATCH=True`). No exact complete count/digest oracle was added to source or
tests.

The corrected lexical analysis changes generator trustworthiness but does not
change the final historical row set: all dynamically imported local modules
were already directly present in the selected-class boundary. Therefore the
fix2 artifact is byte-identical to the rejected fix1 artifact. This equality is
not approval; the count and digest remain proposed review material only.

### Fix2 no-write and protected-file proof

Before staging and after commit, all destinations matched base
`4da92ebe48231d1b8913bf89d170b410e6bf7163` exactly:

~~~text
docs/architecture/sealed-current-files.toml    base=absent worktree=absent
docs/architecture/sealed-current-absences.toml base=absent worktree=absent
docs/architecture/historical-blobs.toml        base=absent worktree=absent
docs/architecture/retained-v7.toml             base=absent worktree=absent
git diff exit over all four paths: 0
~~~

Post-commit `git status --short` was empty. The protected v9 path was not
normalized, checked out, added, staged, or otherwise touched. Its unchanged
development-worktree representation remains 494 bytes, SHA-256
`98493b5047ab04267c8b8ab41adccd30a63a53ef6aa441a02d92ece52985f0d6`, raw
OID `76cdbb746f6b070fdb9ff3bd2f399635952ec902`, and filtered/index/HEAD OID
`6e7881032bdaaa55a45bf7465e4f94679e4e983c`. The canonical snapshot retained
the approved current-file representation: 482 bytes, SHA-256
`57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535`, raw
OID `6e7881032bdaaa55a45bf7465e4f94679e4e983c`.

The remaining runtime bottleneck is still the required per-final-row Git OID
and raw-byte verification in the one integration derivation. Ruff remains
unavailable at the required absolute path, so no Ruff result is claimed.
Disposable fix2 snapshots and archives were intentionally left for controller
cleanup.

## Fix round 3 — symbolic import-target taint

The fix2 167-row artifact and normalized digest
`812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89`
were explicitly rejected and remain unapproved. This round did not infer
approval from that value or from the byte-identical regenerated proposal.

Fix round 3 addresses only the symbolic-import-target bypass. Static expression
values now retain two deterministic renderings when an f-string incorporates a
symbolic value. The generated `-c` program is parsed under both renderings and
its import-sensitive AST positions are compared. A symbolic value reaching a
plain `import`, `from ... import`, `importlib.import_module`, or direct builtin
`__import__` target now fails closed. Fixed module strings still resolve their
local closure, including direct builtin `__import__`. Symbolic run-path and
temporary-directory values remain permitted when the two renderings prove they
do not change an import target. Comparing renderings, rather than searching for
a magic sentinel string, also prevents literal sentinel collisions. The
regression surface includes a precision-truncated f-string so the two witness
values differ from their first character.

Scoped fix commit:
`9041ba52f4304fc90b453299d8174fb180162d18`
(`fix(evidence): reject symbolic import targets`)

Changed and committed files only:

- `tools/generate_evidence_manifests.py`
- `tests/test_evidence_manifest_generation.py`

### Fix3 RED evidence

Disposable RED snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-task3-fix3-red-20260827`

It was reconstructed from the fix2 commit with a no-conversion Git archive;
only the new test file was overlaid. With cwd at that snapshot and
`PYTHONPATH=H/src`, the exact first RED command was:

~~~powershell
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_manifest_generation.py EvidenceManifestGenerationTests.test_dynamic_dash_c_rejects_symbolic_import_targets EvidenceManifestGenerationTests.test_dynamic_dash_c_resolves_exact_builtin_import_target EvidenceManifestGenerationTests.test_dynamic_dash_c_symbolic_nonimport_context_cannot_collide_with_marker -v
~~~

Result: exit 1; 3 tests ran in 0.003s with five expected failures. The old
implementation silently accepted symbolic targets in `import`,
`from ... import`, `importlib.import_module`, and direct `__import__`, and it
omitted the local closure for an exact direct builtin `__import__` target. The
literal-sentinel/non-import-context test already passed, demonstrating the
allowed adjacent behavior.

After the initial dual-render slice, a separate focused RED command exercised
precision truncation:

~~~powershell
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_manifest_generation.py EvidenceManifestGenerationTests.test_dynamic_dash_c_rejects_symbolic_import_targets -v
~~~

Result: exit 1; the `program = f"import {MODULE:.1}"` subcase was still silently
accepted because the first witness strings shared a prefix. Making the two
deterministic witness identifiers differ at their first character closed that
specific taint-erasure edge without globally rejecting symbolic context.

### Fix3 focused and full GREEN evidence

The exact focused command covered the three new tests and all six neighboring
fixed-`-c` behaviors:

~~~powershell
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_manifest_generation.py EvidenceManifestGenerationTests.test_dynamic_dash_c_rejects_symbolic_import_targets EvidenceManifestGenerationTests.test_dynamic_dash_c_resolves_exact_builtin_import_target EvidenceManifestGenerationTests.test_dynamic_dash_c_symbolic_nonimport_context_cannot_collide_with_marker EvidenceManifestGenerationTests.test_dynamic_dash_c_programs_are_exact_and_fail_closed EvidenceManifestGenerationTests.test_dynamic_dash_c_resolution_is_lexical_and_accepts_named_argv EvidenceManifestGenerationTests.test_dynamic_dash_c_resolves_fixed_fstrings_and_concatenation EvidenceManifestGenerationTests.test_dynamic_dash_c_allows_fixed_enclosing_path_constants EvidenceManifestGenerationTests.test_dynamic_dash_c_allows_repeated_symbolic_context_targets EvidenceManifestGenerationTests.test_dynamic_dash_c_rejects_ambiguous_dynamic_reassigned_and_branch_values -v
~~~

Result: exit 0; 9 tests passed in 0.003s.

Canonical full snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-task3-fix3-green2-20260827`

The snapshot was created as a no-checkout/no-local clone of the isolated
development worktree, then populated from a `core.autocrlf=false` archive of
fix2 HEAD before the two candidate files were overlaid. The canonical protected
v9 file was 482 bytes, SHA-256
`57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535`,
and raw blob OID `6e7881032bdaaa55a45bf7465e4f94679e4e983c`. After commit,
the overlaid generator and test raw OIDs were independently matched to commit
`9041ba52...`: generator `7d4200e674078cd1933e0ad144970c53a988cd85`,
test `46a164cc4992348bdaabb203a7ae075ac61581bd`.

Fresh full commands used the required interpreter, `-B -P`, snapshot cwd, and
`PYTHONPATH=H/src`:

~~~powershell
& $python -B -P tests/test_evidence_manifest_generation.py
& $python -B -P tests/test_evidence_manifests.py
& $python -B -P tests/test_evidence_errors_and_model.py
~~~

Results:

~~~text
Ran 27 tests in 17.738s — OK
Ran 11 tests in 0.037s — OK
Ran 7 tests in 0.001s — OK
45 tests total; measured total command time 18.731s
~~~

There were no subprocess-resource warnings. The generation suite retained one
bounded historical integration derivation and independently rechecked all six
current identities and eighteen absences. An earlier archive-only candidate
snapshot failed before derivation because it had no `.git`; it was discarded as
invalid environment evidence, and no code or test was changed in response.
Default absent `--check` still refused before derivation: exit 2 in 0.162s, with
all four destinations absent before and after.

### Fix3 regenerated review artifact

The permitted emission used cwd/repository exactly
`C:\Users\point\AppData\Local\Temp\pontius-task3-fix3-green2-20260827`:

~~~powershell
$env:PYTHONPATH='C:\Users\point\AppData\Local\Temp\pontius-task3-fix3-green2-20260827\src'
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tools/generate_evidence_manifests.py --emit-seed-review 'C:\Users\point\AppData\Local\Temp\pontius-task3-seed-review-fix3-aed6f682786a47449bc08a4a4f350de6.txt'
~~~

Emission exited 0 in 18.013s. `--write` was never invoked.

- Absolute external path:
  `C:\Users\point\AppData\Local\Temp\pontius-task3-seed-review-fix3-aed6f682786a47449bc08a4a4f350de6.txt`
- Verified outside the snapshot/repository: true
- Explicit ordered row count: 167
- Normalized SHA-256:
  `812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89`
- Artifact bytes: 44,301
- Artifact SHA-256:
  `92e538f7d88ec7bb632d380525b61c0a5c35630f37f4aeb6a55ee4b051bd55c2`

An independent standard-library TSV/JSON calculation reconstructed all seven
fields of every row, verified exact `(commit, relative_path)` ordering, and
reproduced the claimed normalized digest (`MATCH=True`). The unchanged 167-row
result means the bypass fix changes generator trustworthiness, not this
repository's derived historical set. It remains proposed review material, not
an approved oracle; no exact complete count/digest oracle was added to source
or tests.

### Fix3 no-write and remaining concerns

Before staging and after commit, every manifest destination remained absent in
base `4da92ebe48231d1b8913bf89d170b410e6bf7163`, the implementation worktree,
and the canonical snapshot. `git diff --exit-code 4da92ebe... -- <four paths>`
exited 0. Post-commit `git status --short` was empty. The protected v9 file was
not modified, normalized, checked out, added, or staged; its development
worktree representation remains 494 bytes, SHA-256
`98493b5047ab04267c8b8ab41adccd30a63a53ef6aa441a02d92ece52985f0d6`,
raw worktree OID `76cdbb746f6b070fdb9ff3bd2f399635952ec902`, and
HEAD/index OID `6e7881032bdaaa55a45bf7465e4f94679e4e983c`.

The only remaining performance bottleneck is the required per-final-row Git
OID/raw-byte verification in the single integration derivation and review
emission (about 18 seconds each); it was not weakened. Ruff remains unavailable
at the required absolute location, so no Ruff result is claimed. Disposable
fix3 RED/GREEN snapshots and archives were intentionally left for controller
cleanup.

## Fix round 4 — Python import-call contracts

The fix3 167-row artifact and normalized digest
`812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89`
were explicitly rejected and remain unapproved. This round did not infer
approval from that value or from the byte-identical regenerated proposal. No
approved digest/count oracle was added.

Fix round 4 replaces the positional-first-argument import-call heuristic with
explicit Python call contracts. `importlib.import_module` now binds positional
and keyword `name`/`package`, rejects missing, duplicate, unknown, expanded,
excess, symbolic, and unresolved arguments, and resolves exact relative names
against an exact package without executing imports. Builtin `__import__` now
binds `name`, `globals`, `locals`, `fromlist`, and `level` in positional or
keyword form. It requires exact absolute names, exact non-wildcard fromlists,
and exact nonnegative level zero; relative context and wildcard `fromlist`
remain fail-closed. Exact fromlist names add every matching tracked local
submodule while absent candidates remain possible attributes. The primary and
alternate fixed-program renderings compare the complete normalized call target,
including package, fromlist, and level, so formatted symbolic inputs cannot hide
a dependency. Direct imports/from-imports, exact builtin/importlib calls,
symbolic non-import context, lexical argv resolution, and literal collision
protection remain green.

Scoped fix commit:
`e0d29dd86bafcea21dbd99336914ee5197572af4`
(`fix(evidence): bind dynamic import call contracts`)

Changed and committed files only:

- `tools/generate_evidence_manifests.py`
- `tests/test_evidence_manifest_generation.py`

Committed blob OIDs matched the final canonical GREEN snapshot exactly:

~~~text
tools/generate_evidence_manifests.py
  ff2c85007ff95ad753ba4fc76b2be29e1a5830fc
tests/test_evidence_manifest_generation.py
  25e4c182f77862aae46b963d2d52dd3403a117d2
~~~

### Fix4 RED evidence

Primary canonical RED snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-task3-fix4-red-766f4d73bb4143e1afa7ae87d2068757`

The snapshot was a no-checkout/no-hardlink clone at fix3 commit
`9041ba52f4304fc90b453299d8174fb180162d18`, populated by a
`core.autocrlf=false` archive before only the new test file was overlaid. With
cwd at the snapshot and `PYTHONPATH` exactly `H/src`, the exact command was:

~~~powershell
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_manifest_generation.py EvidenceManifestGenerationTests.test_dynamic_dash_c_import_module_binds_name_and_package EvidenceManifestGenerationTests.test_dynamic_dash_c_import_module_rejects_bad_binding_and_symbolic_resolution EvidenceManifestGenerationTests.test_dynamic_dash_c_builtin_import_binds_fromlist_and_keywords EvidenceManifestGenerationTests.test_dynamic_dash_c_builtin_import_rejects_bad_binding_and_symbolic_context -v
~~~

Result: exit 1; four tests ran in 0.009s with 29 expected subcase
failures and no test errors. The base implementation omitted keyword names,
relative package resolution, exact fromlist submodules, keyword/auxiliary
binding errors, relative context, and tainted package/fromlist/level inputs.
The already-closed starred-positional cases raised as expected even on the base.

The self-review identified one further exact-fromlist ambiguity: `('*',)` may
consult a package's runtime `__all__`. A focused RED used the then-current
candidate in
`C:\Users\point\AppData\Local\Temp\pontius-task3-fix4-green1-766f4d73bb4143e1afa7ae87d2068757`:

~~~powershell
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_manifest_generation.py EvidenceManifestGenerationTests.test_dynamic_dash_c_builtin_import_rejects_bad_binding_and_symbolic_context -v
~~~

Result: exit 1; one test ran in 0.002s with the single expected wildcard
subcase failure. Rejecting the unresolved wildcard surface made the identical
focused command pass in 0.001s.

The primary RED snapshot's protected v9 identity was canonical before testing:

~~~text
bytes=482
sha256=57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535
raw Git blob OID=6e7881032bdaaa55a45bf7465e4f94679e4e983c
~~~

All four manifests were absent before and after RED.

### Fix4 focused and final GREEN evidence

The four new contract tests first passed in 0.003s. All 13 fixed-program tests
(the four new tests plus the nine direct-import, lexical, fixed-expression,
symbolic-context, collision, and fail-closed neighbors) passed in 0.005s after
refactoring.

Final canonical GREEN snapshot:
`C:\Users\point\AppData\Local\Temp\pontius-task3-fix4-green2-766f4d73bb4143e1afa7ae87d2068757`

It was independently recreated as a no-checkout/no-hardlink clone at
`9041ba52f4304fc90b453299d8174fb180162d18`, populated from a
`core.autocrlf=false` archive, then overlaid with only the two final candidate
files. The candidate raw blob OIDs were independently matched to the scoped
commit as recorded above.

Fresh final commands used the required interpreter, `-B -P`, snapshot cwd, and
`PYTHONPATH` exactly `H/src`:

~~~powershell
& $python -B -P tests/test_evidence_manifest_generation.py
& $python -B -P tests/test_evidence_manifests.py
& $python -B -P tests/test_evidence_errors_and_model.py
~~~

Results:

~~~text
Ran 31 tests in 18.025s — OK (command wall time 18.269s)
Ran 11 tests in 0.038s — OK (command wall time 0.395s)
Ran 7 tests in 0.001s — OK (command wall time 0.318s)
49 tests total; measured total command time 18.986s
~~~

The generation suite again performed the one full historical integration
derivation, remeasured all six current identities, and locked all eighteen
absences. The final snapshot's protected v9 identity was unchanged before and
after all tests:

~~~text
bytes=482
sha256=57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535
raw Git blob OID=6e7881032bdaaa55a45bf7465e4f94679e4e983c
~~~

Default absent `--check` still failed read-only before derivation: exit 2 in
0.160s with:

~~~text
evidence manifest generation failed: historical manifest is absent or unreadable; approval and --write are still required
~~~

All four destinations were absent before and after the default check.

### Fix4 regenerated review artifact

The only successful production-style generator command in this round was the
permitted external review emission below. `--write` was never invoked.

~~~powershell
$env:PYTHONPATH='C:\Users\point\AppData\Local\Temp\pontius-task3-fix4-green2-766f4d73bb4143e1afa7ae87d2068757\src'
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tools/generate_evidence_manifests.py --emit-seed-review 'C:\Users\point\AppData\Local\Temp\pontius-task3-seed-review-fix4-766f4d73bb4143e1afa7ae87d2068757.txt'
~~~

Final emission exited 0 in 18.207s.

- Absolute external path:
  `C:\Users\point\AppData\Local\Temp\pontius-task3-seed-review-fix4-766f4d73bb4143e1afa7ae87d2068757.txt`
- Verified outside both repositories: true
- Explicit ordered unique row count: 167
- Normalized SHA-256:
  `812ce6b5e2573219f75f1fce08d1e117b7fdf930efeab3e31f228eea40499c89`
- Artifact bytes: 44,301
- Artifact SHA-256:
  `92e538f7d88ec7bb632d380525b61c0a5c35630f37f4aeb6a55ee4b051bd55c2`

An independent standard-library parser that did not import the generator read
all seven fields of every TSV row, verified exact ordering and uniqueness,
serialized the mappings with the canonical JSON settings, and reproduced the
claimed normalized digest exactly. The byte-identical result means the fixed
call semantics affect trustworthiness rather than this repository's final row
set. The table and digest remain proposed review material only.

### Fix4 no-write, protected-file, and clean-state proof

Before staging, after commit, and in both canonical snapshots, all four
destinations remained absent and byte/absence-identical to base
`4da92ebe48231d1b8913bf89d170b410e6bf7163`:

~~~text
docs/architecture/sealed-current-files.toml    absent
docs/architecture/sealed-current-absences.toml absent
docs/architecture/historical-blobs.toml        absent
docs/architecture/retained-v7.toml             absent
git diff exit over all four paths: 0
~~~

No generator CLI invocation used `--write`; the required invalid-approval tests
continued to exercise only the internal refusal path. The protected v9 file was
not normalized, checked out, added, staged, or otherwise touched. Its unchanged
development-worktree representation remains:

~~~text
bytes=494
sha256=98493b5047ab04267c8b8ab41adccd30a63a53ef6aa441a02d92ece52985f0d6
raw worktree OID=76cdbb746f6b070fdb9ff3bd2f399635952ec902
index/HEAD OID=6e7881032bdaaa55a45bf7465e4f94679e4e983c
~~~

`git diff --check` exited 0 before commit. The scoped commit changed exactly the
two named files, and post-commit `git status --short` was empty. Ruff remains
unavailable at the required absolute `PONTIUS_RUFF` location, so no Ruff result
is claimed. The remaining routine bottleneck is the required full Git
OID/raw-byte historical verification at about 18 seconds; it was not weakened.
All fix4 snapshots, Git homes, and archive files were intentionally left for
controller cleanup.
