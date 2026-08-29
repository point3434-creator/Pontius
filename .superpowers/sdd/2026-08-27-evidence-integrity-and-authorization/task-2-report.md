# Task 2 report — strict manifest parsing and semantic identity

## Status

Implemented strict, pure-byte TOML manifest parsers and canonical semantic
identity helpers. No production filesystem reader was added.

## Files

- `src/pontius/evidence/manifest.py` — canonical JSON semantic encoding,
  SHA-256 identities, exact-key TOML validation, four pure parsers, historical
  digest/identity checks, and current-boundary validation.
- `tests/evidence_test_support.py` — exact-path test-helper loader for `-P`.
- `tests/test_evidence_manifests.py` — fixture-driven schema, malformed-input,
  semantic-order, digest, and cross-manifest boundary tests.

`src/pontius/evidence/model.py` required no change: the reviewed Task 1 model
constructors and `LoadedRetainedV7Manifest` already provided the complete
declared immutable seam required by these pure parsers.

## Implementation and self-review

- Parsers accept only exact immutable `bytes`, call `tomllib` directly, and do
  no file reads or other filesystem I/O.
- TOML decode/syntax/duplicate-key/table failures preserve their cause and
  become `EvidenceConfigurationError("manifest_toml_invalid", ...)` with the
  required source path context.
- Root and record tables require their exact fields. Strings, booleans,
  integers, SHA-256 values, Git identities, and repository-relative paths are
  validated before model construction; booleans do not satisfy integer fields.
- Historical blobs are uniquely keyed by `(commit, relative_path)`, sorted by
  that key, and their claimed digest covers every normalized blob field.
  Snapshots are sorted by `(commit, phase)`.
- The retained-v7 loader distinguishes byte identity from semantic identity:
  key ordering changes `source_identity.raw_sha256` but not `semantic_sha256`.
- The separate current-boundary validator rejects baseline/count disagreement,
  present/absent overlap, and duplicate owner/path identities.
- The module imports only the standard library and sibling evidence modules.
  It exposes no path-count metric and adds no temporary production reader.

## TDD evidence

All test payloads were run only in disposable `%TEMP%` snapshots cloned with
`C:/Program Files/Git/cmd/git.exe`; none ran from the development worktree.
Each snapshot used the copied nonreparse interpreter with `-B -P` and
`PYTHONPATH` set exactly to `H/src`.

### RED

Snapshot: `C:\Users\point\AppData\Local\Temp\pontius-task2-red-44e20eb37588411cb417ee33e4e33fc7`

Command:

```powershell
$env:PYTHONPATH = (Join-Path $harness 'src')
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_manifests.py -v
```

Exit status: `1`.

```text
ModuleNotFoundError: No module named 'pontius.evidence.manifest'
```

This is the expected bootstrap failure: the test imports the strict loaders
that did not yet exist.

### GREEN

Final snapshot: `C:\Users\point\AppData\Local\Temp\pontius-task2-final-green2-975cb17221434dec8601d74b4adbb271`

Commands:

```powershell
$env:PYTHONPATH = (Join-Path $harness 'src')
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_manifests.py -v
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_errors_and_model.py -v
```

Exit statuses: `0`, `0`.

```text
Ran 8 tests in 0.005s
OK

Ran 7 tests in 0.001s
OK
```

An earlier GREEN snapshot identified a test-fixture mistake in the duplicate
owner/path case (the fixture used a different path); it exited `1`, was fixed
in the test fixture, and is not claimed as passing evidence.

## Review checkpoint

`git diff --check` exited `0` before staging. The staged diff check is rerun
immediately before the local authorized commit.

## Concerns

Disposable snapshots remain in `%TEMP%` because no cleanup command was run.
They are outside OneDrive and no repository content was removed or rewritten.

## Fix Round 1 — all-schema malformed-input matrix

### Changed files

- `tests/test_evidence_manifests.py` — added table rows for each parser's
  applicable malformed integer/boolean, digest or Git identity, path, and
  count dimensions. Absence manifests deliberately have no digest field;
  retained-v7 has no independent collection count to compare.

No production file changed. The pre-existing strict shared validators correctly
rejected every new case, so no minimum production correction was warranted.

### Initial focused snapshot result

Snapshot: `C:\Users\point\AppData\Local\Temp\pontius-task2-fix1-red-4a23c0ad82cb47328e98a213282de4e4`

Command:

```powershell
$env:PYTHONPATH = (Join-Path $harness 'src')
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_manifests.py -v
```

Exit status: `0`.

```text
Ran 9 tests in 0.007s
OK
```

The newly added behavioral cases did not produce a RED result because the
already-committed generic validators covered them. This is recorded rather than
manufacturing a failure by weakening production code or misreporting the run.

### Final GREEN regression

Snapshot: `C:\Users\point\AppData\Local\Temp\pontius-task2-fix1-green-6845b3b0e9a343aab8abcc2e0f073430`

Commands:

```powershell
$env:PYTHONPATH = (Join-Path $harness 'src')
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_manifests.py -v
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_errors_and_model.py -v
```

Exit statuses: `0`, `0`.

```text
Ran 9 tests in 0.007s
OK

Ran 7 tests in 0.001s
OK
```

`git diff --check` was run before staging and the staged check is run again
before the local fix commit.

## Fix Round 2 — complete applicable malformed variants

### Changed files

- `tests/test_evidence_manifests.py` — expanded the four-schema table matrix
  to cover string and boolean integer violations, both uppercase and short
  digest/Git identity forms, all absolute/traversal/drive path forms, malformed
  retained booleans, and every collection-backed count disagreement. The table
  comment expressly records field families that a schema does not declare.

No production file changed: the new variants were rejected by the existing
strict validators.

### Initial snapshot (honest RED status)

Snapshot: `C:\Users\point\AppData\Local\Temp\pontius-task2-fix2-initial-0186b3d3b3f142419c28856dc40cb3ed`

Command:

```powershell
$env:PYTHONPATH = (Join-Path $harness 'src')
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_manifests.py -v
```

Exit status: `0`.

```text
Ran 9 tests in 0.010s
OK
```

No RED was available without deliberately weakening the already-correct shared
validators; no such manufactured failure was used.

### Final GREEN regression

Snapshot: `C:\Users\point\AppData\Local\Temp\pontius-task2-fix2-green-38a8e01807f14bdab1dd8fa6a0b880cb`

Commands:

```powershell
$env:PYTHONPATH = (Join-Path $harness 'src')
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_manifests.py -v
& 'C:\Users\point\AppData\Local\Temp\pontius-evidence-test-stabilization\.venv\Scripts\python.exe' -B -P tests/test_evidence_errors_and_model.py -v
```

Exit statuses: `0`, `0`.

```text
Ran 9 tests in 0.009s
OK

Ran 7 tests in 0.001s
OK
```
