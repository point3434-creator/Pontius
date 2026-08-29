### Task 1: Implement Stable Errors and Immutable Domain Models

**Files:**

- Create: `src/pontius/evidence/__init__.py`
- Create: `src/pontius/evidence/errors.py`
- Create: `src/pontius/evidence/model.py`
- Create: `tests/test_evidence_errors_and_model.py`

**Interfaces:**

- Consumes: Python 3.11+ standard-library `dataclasses`, `pathlib`, `types`, and `typing`; no existing `pontius` package import.
- Produces: the five `EvidenceError` subclasses with constructor `(code: str, message: str, *, context: Mapping[str, object])`; `EvidenceFileIdentity`, `FileIdentity`, `GitTreeEntry`, `GitIndexEntry`, `AuthorizationPolicy`, `PreauthorizationState`, `LiveAuthorizationState`, `AuthorizationState`, all manifest entry/wrapper models, `LoadedRetainedV7Manifest`, and `RetainedV7Assessment` with the exact frozen fields defined below.

- [ ] Write failing tests for stable error codes, messages, preserved causes, recursively immutable context, frozen model instances, normalized repository-relative paths, lowercase identities, and exact integer/boolean validation.

The tests must construct all five public failures and assert their inheritance and fields:

```python
from pontius.evidence.errors import (
    AuthorizationPhaseError,
    EvidenceConfigurationError,
    EvidenceIntegrityError,
    LifecycleStateError,
    RuntimeContractError,
)

error = AuthorizationPhaseError(
    "authorization_live_state_required",
    "live authorization is required",
    context={"phase": "preauthorization", "paths": ["a", "b"]},
)
self.assertEqual(error.code, "authorization_live_state_required")
self.assertEqual(error.message, "live authorization is required")
self.assertEqual(error.context["paths"], ("a", "b"))
with self.assertRaises(TypeError):
    error.context["phase"] = "live_authorization"
```

Also construct an otherwise valid `EvidenceFileIdentity` with `byte_length=True` and assert rejection. Cover negative lengths, absolute paths, `..` segments, uppercase digests, duplicate authorization paths, and nonpositive maximum config sizes too.

- [ ] Run the new test file in a fresh bootstrap snapshot and confirm it fails because the package does not exist:

```powershell
$priorErrorActionPreference = $ErrorActionPreference
$priorPythonPath = $env:PYTHONPATH
$pushed = $false
try {
    $ErrorActionPreference = "Stop"
    if (-not [IO.Path]::IsPathFullyQualified($python) -or -not [IO.Path]::IsPathFullyQualified($H)) {
        throw "bootstrap executable and harness must be absolute"
    }
    $pythonItem = Get-Item -LiteralPath $python -ErrorAction Stop
    $harnessItem = Get-Item -LiteralPath $H -ErrorAction Stop
    if ($pythonItem.PSIsContainer -or $harnessItem.PSIsContainer -eq $false -or
        (($pythonItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) -or
        (($harnessItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
        throw "bootstrap executable/harness type is invalid"
    }
    Push-Location -LiteralPath $harnessItem.FullName -ErrorAction Stop
    $pushed = $true
    $env:PYTHONPATH = (Join-Path $harnessItem.FullName "src")
    $redOutput = @(& $pythonItem.FullName -B -P tests/test_evidence_errors_and_model.py -v 2>&1)
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 1) { throw "red test returned unexpected exit code: $exitCode" }
    $redText = $redOutput -join "`n"
    if ($redText -notmatch "ModuleNotFoundError" -or $redText -notmatch "pontius\.evidence") {
        throw "red test failed for an unexpected reason"
    }
}
finally {
    if ($null -eq $priorPythonPath) { Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue }
    else { $env:PYTHONPATH = $priorPythonPath }
    if ($pushed) { Pop-Location }
    $ErrorActionPreference = $priorErrorActionPreference
}
```

- [ ] Implement `EvidenceError` with `code`, `message`, and a recursively frozen, sorted `MappingProxyType` context. Accept nested mappings, tuples/lists, sets, strings, integers, booleans, and `None`; reject unsupported objects before constructing the exception. At each translation site, instantiate the exact typed exception in a local variable and use `raise translated from error` to preserve the cause.

- [ ] Implement these `@dataclass(frozen=True, slots=True)` values with validation in `__post_init__`:

```python
@dataclass(frozen=True, slots=True)
class EvidenceFileIdentity:
    relative_path: str
    byte_length: int
    raw_sha256: str
    role: str


@dataclass(frozen=True, slots=True)
class FileIdentity:
    platform: Literal["windows", "posix"]
    volume_or_device: int
    file_id: int
    byte_length: int
    created_or_changed_ns: int
    modified_ns: int
    mode_or_attributes: int
    reparse_tag: int | None


@dataclass(frozen=True, slots=True)
class GitTreeEntry:
    mode: str
    object_type: Literal["blob"]
    object_oid: str
    relative_path: str


@dataclass(frozen=True, slots=True)
class GitIndexEntry:
    mode: str
    blob_oid: str
    stage: int
    relative_path: str


@dataclass(frozen=True, slots=True)
class AuthorizationPolicy:
    config_path: str
    schema_version: str
    authorization_commit_paths: tuple[str, ...]
    maximum_config_bytes: int = 65_536


@dataclass(frozen=True, slots=True)
class PreauthorizationState:
    head_commit: str
    config_path: str
    present: Literal[False] = False
    in_head: Literal[False] = False
    in_index: Literal[False] = False


@dataclass(frozen=True, slots=True)
class LiveAuthorizationState:
    head_commit: str
    authorization_commit: str
    source_seal_commit: str
    config_path: str
    config_raw_sha256: str
    config_canonical_lf_sha256: str
    authorization_commit_paths: tuple[str, ...]


AuthorizationState: TypeAlias = PreauthorizationState | LiveAuthorizationState
```

`FileIdentity` uses the Windows volume serial/file ID or POSIX device/inode in the two integer identity fields; all integer fields reject booleans and negatives, and `reparse_tag` is `None` only on POSIX. Add `SealedCurrentFileEntry(relative_path, byte_length, raw_sha256, role, governing_decision, owner)`, `SealedCurrentAbsenceEntry(relative_path, role, governing_decision, owner)`, `HistoricalSnapshot(phase, commit, root_tree_oid, governing_decision)`, and `HistoricalBlobIdentity(commit, relative_path, git_blob_oid, raw_sha256, role, phase, governing_decision)`, plus the wrapper manifest models, `RetainedV7Manifest`, `LoadedRetainedV7Manifest`, and `RetainedV7Assessment`. The loaded manifest carries both `source_identity: EvidenceFileIdentity` and `semantic_sha256: str`; `RetainedV7Assessment.manifest_identity` is the semantic digest so TOML key order cannot change its meaning.

- [ ] Keep `__init__.py` limited to the five errors and the four user-facing state/assessment types. Do not import `retained_v7`, Git, filesystem, or historical code at package import time.

- [ ] Rerun the focused test in a newly captured snapshot and confirm every case passes.

- [ ] Review checkpoint: run `git diff --check` and inspect `git status --short`. With explicit commit authorization only, create `test(evidence): lock typed error and model contracts`.

---

