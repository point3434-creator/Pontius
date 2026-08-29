# Evidence Integrity and Authorization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a typed, current-HEAD-safe evidence layer that fixes the two CodeRabbit authorization defects without changing sealed v7 code, locks the historical evidence boundary, and assesses retained v7 evidence without invoking an experiment owner.

**Architecture:** Keep the sealed v2-v7 capsule byte-for-byte unchanged. Add a narrow `pontius.evidence` package with immutable models, strict data parsers, explicit filesystem/Git ports, a one-snapshot authorization state machine, and a maintenance-only retained-v7 assessor. The future test orchestrator consumes the same TOML schemas directly and does not import this package.

**Tech Stack:** Python 3.11+, standard library (`dataclasses`, `hashlib`, `json`, `pathlib`, `tomllib`, `subprocess`, `ctypes`, `msvcrt`, `unittest`), the existing `pontius.durable_evidence_journal` seam, Git plumbing, Ruff when provisioned.

**Spec:** [Evidence and Test Stabilization Design](../specs/2026-08-27-evidence-test-stabilization-design.md)

## Global Constraints

- Execute the coordinated plans in this order: this plan Tasks 1-3; orchestration Tasks 1-2 plus its Task 11a; this plan Tasks 4-9; orchestration Tasks 3-10; its Task 11b; then orchestration Task 12. The earlier-phase seed approval in Task 3 is a hard governance gate.
- Treat baseline `a842c4b6a73a2991a63a481f4107580b72750582` as the recorded stabilization boundary. Re-read HEAD and status before each task because the user's checkout may change while work is in progress.
- Do not modify, normalize, stage for replacement, delete, move, or import-and-rewrite any current path later listed in `sealed-current-files.toml`. Do not create any current path later listed in `sealed-current-absences.toml`.
- Do not modify existing v2-v7 source, reader, runner, test, configuration, decision, attempt, marker, or result bytes. In particular, do not patch `legal_river_quotient_compiled_global_separation_calibration_v7_result.py`; the active typed API supersedes its unsafe maintenance use while the historical file remains sealed.
- Do not modify `src/pontius/__init__.py`. Package import cleanup and CUDA bootstrap changes are a later milestone.
- New evidence modules may import only the standard library, sibling `pontius.evidence` modules, and `pontius.durable_evidence_journal`. They must not import compiled-calibration owners/readers/runners, tests, experiments, CuPy/CUDA modules, or GPU modules.
- Active library code raises typed exceptions. It does not print, call `exit`, raise `SystemExit`, invoke a one-shot owner, or write lifecycle state.
- Every file read as evidence is bounded, opened without following links/reparse points, read once from one open handle, and verified before and after the read.
- Use exact types in parsers: `type(value) is int` and `type(value) is bool`. Never allow `bool` to satisfy an integer field.
- Until the canonical runner from the coordinated orchestration plan is operational, run focused tests only in an exact disposable bootstrap snapshot outside OneDrive. Initialize `$primary = (Resolve-Path ".").Path`, `$python = (Resolve-Path ".\.venv\Scripts\python.exe").Path`, `$R = Join-Path ([IO.Path]::GetTempPath()) ("pontius-bootstrap-" + [guid]::NewGuid().ToString("N"))`, and `$H = Join-Path $R "harness"`. Resolve `$gitExe` only from the absolute `PONTIUS_GIT` path and validate its regular nonlink/nonreparse identity before any repository read. Every bootstrap Git invocation, including capture, clone, detach, verification, `hash-object`, and `update-index`, must use `$gitExe` through an argument-vector process helper with `shell=False`/`UseShellExecute=False` and the fresh scrubbed Git environment defined below; no literal `git` command or ambient executable lookup is permitted. Capture HEAD/branch, raw `$gitExe ls-files --stage -z` index records, tracked/untracked/deleted path inventory, regular bytes, modes, platform identities, lengths, and SHA-256 values into a spool under R; recapture and compare them before materialization. Clone with `--local --no-hardlinks --no-checkout`, detach at captured HEAD, clear H's index, write every captured staged blob into H with `$gitExe -C $H hash-object -w --stdin`, rebuild all captured modes/stages by running `$gitExe -C $H update-index -z --index-info` with the captured NUL records on standard input, then overlay spooled working bytes and deletions. Bind every mutating Git command explicitly to H; no object/index write runs with primary as cwd or Git directory. Verify H's HEAD, complete raw index, working inventory, and lack of hardlink/alternate/reparse connection to primary. Set cwd to H, `PYTHONPATH` to exactly `H/src`, and invoke each test file directly with `-B -P`. Never execute a test payload from the primary checkout.
- Because `-P` excludes `tests` from `sys.path`, every evidence test needing `tests/evidence_test_support.py` loads that file by its exact `Path(__file__).with_name("evidence_test_support.py")` through `importlib.util.spec_from_file_location`; it never adds H, H/tests, or the primary checkout to `sys.path`.
- For disposable cleanup, resolve both the OS temporary root and the proposed run directory, require the latter to be a strict descendant with the expected `pontius-` prefix, and only then remove that exact directory. Never recursively remove a computed target that has not passed this check.
- The development interpreter may run focused slices. Release acceptance additionally requires a separately configured CPython 3.11 slot; a missing 3.11 interpreter is an explicit environment gate, never a reason to substitute Python 3.14.
- Ruff is also an explicit environment gate. If it is not provisioned, record that fact and do not claim the static-check acceptance criterion.
- Resolve every Git adapter and bootstrap helper only from an absolute `PONTIUS_GIT` executable path, measure its regular nonlink/nonreparse identity before and after every call, and never fall back to ambient `PATH`. Construct each Git child environment from a minimal platform allowlist needed to start the process, with dedicated `HOME` and `USERPROFILE` below the disposable root plus `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=NUL` on Windows or `/dev/null` on POSIX, `GIT_NO_REPLACE_OBJECTS=1`, and `GIT_LITERAL_PATHSPECS=1`. Do not inherit repository-routing or object-replacement controls: clear `GIT_DIR`, `GIT_COMMON_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_REPLACE_REF_BASE`, `GIT_CEILING_DIRECTORIES`, `GIT_DISCOVERY_ACROSS_FILESYSTEM`, `GIT_CONFIG_COUNT`, every `GIT_CONFIG_KEY_*`/`GIT_CONFIG_VALUE_*`, and every other ambient `GIT_*` key not explicitly set by this contract. The bootstrap helper, generator, and active adapter share conformance tests for this exact environment contract.
- Each task ends with a review checkpoint. Run the listed commit command only after explicit user authorization to create commits; otherwise leave the changes uncommitted and record the checkpoint in the task notes.

## File Structure

Create these active modules:

```text
src/pontius/evidence/
  __init__.py          deliberately small public surface
  errors.py            stable typed failures and recursive immutable context
  model.py             frozen validated values and protocol records
  manifest.py          strict TOML parsing and semantic identities
  filesystem.py        one-read regular-file adapters for Windows and POSIX
  git.py               bounded argument-vector Git adapter
  authorization.py     preauthorization/live-authorization state machine
  retained_v7.py       maintenance-only retained negative assessment
```

Create these governed data files:

```text
docs/architecture/sealed-current-files.toml
docs/architecture/sealed-current-absences.toml
docs/architecture/historical-blobs.toml
docs/architecture/retained-v7.toml
```

Create these tools and tests:

```text
tools/generate_evidence_manifests.py
tests/evidence_test_support.py
tests/test_evidence_errors_and_model.py
tests/test_evidence_manifests.py
tests/test_evidence_manifest_generation.py
tests/test_evidence_filesystem_and_git.py
tests/test_evidence_authorization.py
tests/test_retained_v7_assessment.py
tests/test_evidence_import_boundary.py
```

Do not export evidence APIs from `src/pontius/__init__.py`. Consumers import the explicit submodule they need.

The four TOML schemas are exact:

```text
sealed-current-files:
  schema_version, baseline_commit, entry_count, file[]
  file: relative_path, byte_length, raw_sha256, role,
        governing_decision, owner

sealed-current-absences:
  schema_version, baseline_commit, entry_count, absence[]
  absence: relative_path, role, governing_decision, owner

historical-blobs:
  schema_version, baseline_commit, snapshot_count, entry_count,
  entries_sha256, approved_seed_sha256, snapshot[], blob[]
  snapshot: phase, commit, root_tree_oid, governing_decision
  blob: commit, relative_path, git_blob_oid, raw_sha256, role,
        phase, governing_decision

retained-v7:
  schema_version, source_seal_commit, authorization_commit,
  historical_reader_commit, journal_protocol_sha256, campaign_sha256,
  record_count, observation_count, calibration_cell_count,
  warmup_cell_count, measured_labelled_partial_cell_count, terminal,
  journal_complete, scientific_campaign_complete, scientific_call_count,
  authoritative_measured_call_count, passed, laboratory_elapsed_ns,
  laboratory_wall_ns, outside_laboratory_elapsed_ns,
  outside_laboratory_wall_ns, public_elapsed_ns, public_wall_ns,
  fit_projection_present, production_base_classification,
  candidate_selection_present, topology_selection_present,
  arithmetic_schedule_selection_present,
  truncation_authorized, historical_blobs_manifest_path,
  absent_launch_paths, expected_null_claim_paths,
  result, attempt, consumed_launch
  result/attempt/consumed_launch: relative_path, byte_length,
                                  raw_sha256, role
```

The four independent parsers/generators require these exact schema literals: sealed-current-files `pontius-sealed-current-files-v1`; sealed-current-absences `pontius-sealed-current-absences-v1`; historical-blobs `pontius-historical-blobs-v1`; and retained-v7 `pontius-retained-v7-v1`. Any other string rejects before semantic validation. The stdlib-only orchestration readers use the same literals without importing this package.

`expected_null_claim_paths` is the exact sorted tuple `$.arithmetic_schedule_selected`, `$.candidate_selected`, `$.claims.action_clock_result`, `$.claims.arithmetic_schedule_selected`, `$.claims.blueprint_result`, `$.claims.candidate_selected`, `$.claims.compiled_calibration_result`, `$.claims.decision_quality_result`, `$.claims.literal_45_numerical_result`, `$.claims.material_zeta_speed_claim`, `$.claims.poker_strength_result`, `$.claims.production_base_numerical_admission`, `$.claims.resolver_iteration_result`, `$.claims.symbolic_45_primitive_projection`, `$.claims.topology_selected`, and `$.topology_selected`. TOML therefore encodes null expectations as paths, not nonexistent TOML null values.

The wrapper model interfaces mirror those keys exactly: `SealedCurrentFilesManifest(schema_version, baseline_commit, entry_count, files)`, `SealedCurrentAbsencesManifest(schema_version, baseline_commit, entry_count, absences)`, and `HistoricalBlobsManifest(schema_version, baseline_commit, snapshot_count, entry_count, entries_sha256, approved_seed_sha256, snapshots, blobs)`. Count fields are retained and independently cross-checked against tuple lengths.

`RetainedV7Manifest` has one frozen field for every retained-v7 key above. Commit/digest/path/terminal/classification fields are `str`; counts and wall values are exact `int`; completion/presence/selection/authorization fields are exact `bool`; `absent_launch_paths` and `expected_null_claim_paths` are immutable `tuple[str, ...]`; and `result`, `attempt`, and `consumed_launch` are `EvidenceFileIdentity`. `LoadedRetainedV7Manifest` contains `manifest`, raw `source_identity`, and canonical `semantic_sha256`. `RetainedV7Assessment` contains `manifest_identity`, `terminal`, `journal_complete`, `scientific_campaign_complete`, `scientific_call_count`, `authoritative_measured_call_count`, `passed`, and `historical_commit`.

---

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

### Task 2: Add Strict Manifest Parsing and Canonical Semantic Identity

**Files:**

- Create: `src/pontius/evidence/manifest.py`
- Create: `tests/evidence_test_support.py`
- Create: `tests/test_evidence_manifests.py`
- Modify: `src/pontius/evidence/model.py`

**Interfaces:**

- Consumes: Task 1 model constructors and `EvidenceConfigurationError`/`EvidenceIntegrityError`.
- Produces: `canonical_semantic_bytes(value: object) -> bytes`, `semantic_sha256(value: object) -> str`, the four pure `parse_*_manifest(raw: bytes, *, source_path: Path, repository_root: Path)` functions returning their declared immutable manifest type, and `validate_current_boundary(files_manifest: SealedCurrentFilesManifest, absences_manifest: SealedCurrentAbsencesManifest) -> None`.

- [ ] Write failing table-driven tests using temporary TOML bytes for all four schemas. Cover missing fields, extra fields, duplicate TOML keys/tables, wrong scalar types, booleans in integer fields, uppercase/short hashes, duplicate `(commit, path)` records, count disagreement, path traversal, absolute/drive-qualified paths, present/absent overlap, and an incorrect normalized digest.

- [ ] Add a semantic-order test that serializes the same retained-v7 mapping in two different TOML key orders and asserts equal `semantic_sha256` while preserving distinct raw `source_identity.raw_sha256` values.

- [ ] Run the test file in the bootstrap snapshot and confirm strict loaders are absent.

- [ ] Implement one exact-key helper per table, a normalized POSIX-relative path validator, exact commit/blob/digest validators, and canonical semantic encoding:

```python
def canonical_semantic_bytes(value: object) -> bytes:
    normalized = _normalize_semantic_value(value, path="$")
    return json.dumps(
        normalized,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def semantic_sha256(value: object) -> str:
    return sha256(canonical_semantic_bytes(value)).hexdigest()
```

`_normalize_semantic_value` accepts only `None`, exact booleans, exact integers, strings, lists/tuples, and string-keyed mappings. It sorts mapping keys and preserves list order. TOML duplicate rejection comes from `tomllib`, but translate that exception into `EvidenceConfigurationError("manifest_toml_invalid", "manifest is not valid TOML", context={"path": source_path.as_posix()})` with the original cause.

- [ ] Implement pure bytes parsers with exact source labels and repository-root path validation:

```python
parse_sealed_current_files_manifest(raw, *, source_path, repository_root)
parse_sealed_current_absences_manifest(raw, *, source_path, repository_root)
parse_historical_blobs_manifest(raw, *, source_path, repository_root)
parse_retained_v7_manifest(raw, *, source_path, repository_root)
```

These functions accept immutable `bytes` and do no filesystem I/O. Task 4 adds the public one-read path loaders after the platform adapter exists; no temporary insecure production reader is introduced.

- [ ] Implement `validate_current_boundary(files_manifest, absences_manifest)`. It rejects present/absent overlap, a duplicate semantic owner/path pair, baseline disagreement, or count mismatch. Cross-manifest tests call this function rather than expecting one loader to know about the other file.

- [ ] Enforce historical identity keys as `(commit, relative_path)`, sort snapshots by `(commit, phase)`, sort blobs by `(commit, relative_path)`, and compute `entries_sha256` from the complete normalized blob records. Do not compute or expose a unique-path count.

- [ ] Rerun focused tests and `tests/test_evidence_errors_and_model.py` in a fresh snapshot.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `feat(evidence): add strict manifest contracts`.

---

### Task 3: Generate and Lock the Evidence Boundary Data

**Files:**

- Create: `tools/generate_evidence_manifests.py`
- Create: `docs/architecture/sealed-current-files.toml`
- Create: `docs/architecture/sealed-current-absences.toml`
- Create: `docs/architecture/historical-blobs.toml`
- Create: `docs/architecture/retained-v7.toml`
- Create: `tests/test_evidence_manifest_generation.py`
- Modify: `tests/test_evidence_manifests.py`

**Interfaces:**

- Consumes: Task 2's exact schema/canonicalization contracts as data and conformance vectors, the Git executable bound under the Global Constraints, and the approved design's fixed present/absence/retained identities; it imports no `pontius` implementation.
- Produces: `docs/architecture/sealed-current-files.toml`, `docs/architecture/sealed-current-absences.toml`, `docs/architecture/historical-blobs.toml`, and `docs/architecture/retained-v7.toml`; generator commands `--check`, `--emit-seed-review <absolute-temp-path>`, and `--write --approved-seed-sha256 <digest>` with the exact no-write approval behavior below.

- [ ] Write failing repository tests for the exact six current byte identities, exact eighteen absences, disjoint current sets, exact eleven commit/root-tree pairs, the exact 96-entry v7 source-seal dependency group, the exact six-path v7 authorization surface, generic order-independent historical-entry digest semantics, approval-argument refusal/mismatch behavior, and retained-v7 constants. Do not assert the not-yet-approved complete earlier-phase entry count or digest in this first red slice.

Lock these retained-v7 facts in the test: protocol `2dc6cd5636ca56b4b3b17592860737489a2bf1705de79a75bd395fa309b72272`, campaign `669a959827590b883277840161cd2cdabbed18687ad390f6667bc312362fd23d`, 592 records, 590 observations, 569 calibration cells, 480 warmup cells, 89 measured-labelled partial cells, 569 scientific calls, zero authoritative measured calls, `laboratory_wall_rejected`, `passed=false`, journal complete, scientific campaign incomplete, and historical reader commit `aaca2dda40e29be8ebd091d58e7853bce1c62fd8`.

- [ ] Implement `tools/generate_evidence_manifests.py` as a standard-library-only deterministic generator with three commands: `--check` compares canonical generated bytes without writing and requires the stored approved digest to match the freshly derived seed; `--emit-seed-review <absolute-temp-path>` emits the proposed earlier-phase path/role/decision records and normalized digest outside the repository; `--write --approved-seed-sha256 <lowercase-64-hex>` atomically replaces only the four named manifest files after verifying the destination paths and only when the supplied digest exactly equals the freshly derived seed digest. `--write` without that argument, with a stale digest, or with a malformed digest rejects before any write. The default is `--check`.

- [ ] Implement file-local strict TOML validation and canonical semantic encoding in the generator. Run the same valid/invalid byte vectors through the active Task 2 parser/encoder and this tool-local implementation and require identical acceptance, normalized values, and semantic digests. The conformance test imports each implementation through its allowed boundary; production generator code never imports `pontius`.

- [ ] Encode the six current identities and eighteen exact absence paths from the approved spec as data constants. Lock roles/owners/decisions exactly: v2 result `retained_result/compiled_global_separation_calibration_v2/ADR-0462`; v5 attempt `retained_attempt/compiled_global_separation_calibration_v5/ADR-0470`; v9 config `rejected_authorization/compiled_global_separation_calibration_v6/ADR-0473`; v7 result/attempt/consumed marker use `retained_result`, `retained_attempt`, and `consumed_launch_marker`, owner `compiled_global_separation_calibration_v7`, decision `ADR-0476`. Absence roles follow the exact suffix (`closed_result_absence`, `closed_attempt_absence`, `closed_launch_pending_absence`, `closed_launch_consumed_absence`, `closed_launch_aborted_absence`, or `rejected_authorization_absence`); owners are the matching v3-v7 version; decisions are v3 `ADR-0466`, v4 `ADR-0469`, v5 `ADR-0470`, v8/v6 `ADR-0473`, and v7 `ADR-0476`. Before generation, measure every present file and every absence directly and fail if reality differs; the generator must never update expected hashes from unexpected current bytes.

- [ ] Generate historical blobs by this deterministic phase-surface rule, then emit every final path explicitly:

  1. Seed each earlier phase with its exact selected test file/class from the approved matrix, its versioned owner/reader/runner modules named by those tests, and its governing ADR.
  2. Parse those Git blobs with `ast`, resolve transitive local `pontius` imports that exist at that commit, and include tracked source dependencies reached by that closure.
  3. Parse literal normalized repository paths used by the reachable tests/sources and include existing tracked configuration and decision files under `experiments/configs` and `docs/decisions`.
  4. Parse fixed dynamic `-c` programs declared by the selected tests and include their local import closure.
  5. For v7 source seal, use exactly the 96 `dependency_hashes` keys in retained record zero rather than inferring a replacement closure.
  6. For v7 live authorization, add exactly `ARCHITECTURE.md`, `RISK_REGISTER.md`, `ROADMAP.md`, `STATUS.md`, `docs/decisions/ADR-0475-authorize-one-v7-authorization-phase-calibration-invocation.md`, and `experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v11-authorization-phase-corrected-invocation-authorization.json`.
  7. Resolve every final `(commit, path)` through `git rev-parse <commit>:<path>` and raw `git show <commit>:<path>`, record Git blob OID and raw SHA-256, sort by the pair, and reject collisions or unresolved dynamic imports.

The approved spec did not enumerate every earlier-phase selected path, so this derivation is a proposed seed, not preapproved policy. First emit the complete explicit seed table and digest outside the repository, obtain user approval of that exact table, and only then pass the approved digest through `--approved-seed-sha256`. The CLI argument is the machine-enforced approval token: it must equal the freshly derived digest and becomes `approved_seed_sha256` in the generated manifest. The final manifest contains only explicit entries and no glob.

- [ ] Give the generator a file-local standard-library secure reader with the same behavioral contract as Task 4: no-follow/reparse rejection, regular-file check, one bounded read, before/after handle identity, and final path identity. Reuse the same adapter conformance tests through two factories so the tool-local and active readers cannot drift, while preserving the no-`pontius` import boundary.

- [ ] Bind generator Git calls to one resolved executable identity and a fresh minimal environment: `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=NUL` on Windows or `/dev/null` on POSIX, dedicated HOME/USERPROFILE, `GIT_NO_REPLACE_OBJECTS=1`, and literal pathspec mode. Use argument vectors, explicit repository cwd, `--` path separation, ten-second timeouts, and bounded stdout/stderr; reject any identity change, replacement-object behavior, malformed output, or nonzero status.

- [ ] Lock these snapshot pairs and reject a changed root tree:

```text
88148da07324c13b79c72ea494b14167a975c001  bc5d1952f690da5d49275344919de36224af26cb
08bb6857f47f9669b8f531c65079d4decd52a573  0d01a4133a4e6ab10467ad0bd298630149702a73
3de8e0c9eebf67f2cc2573041242a869468de6e9  ea80b86ac60cb324e3c18ddad83d8bbba0ade933
77feb7c78990ca53e70b1302a6866fe5d781411f  d26ba99c033875342a652ae352067beee1ca44ee
ba6a3418b7c991238cc1a65898fd61fa03b4a3cb  73b53cb04c91459e8b7028ccd292b972d2dfdf69
815d23c115289347e3d4028a4866eb9f87d4669a  894c026603156df4bba1134ba9861e98bd3a6663
5c0c9a401e5f2ebf59296832d954d0075c4d4624  f3418410c442a4d06c62aba9777def72633ca5c5
d633f3fb469a27dee688587293c6efb1d2cb2757  9c9ff658c2836bde5d1df71f5596d1d6aa1a5bd2
cbfa3598f22c7aba7d824f71356ca156f8b01b0c  9873ff13131c91b058307643dc838a8452268fbb
56127da2970f5a8a8056a97a247ebe1fdf4b983b  ee2437ba1b2efbf2dc4ab3c21bbacdbf26c58648
aaca2dda40e29be8ebd091d58e7853bce1c62fd8  e7bd077f40b1970e9b40a83c891996ab02cd5ffd
```

- [ ] Run `--emit-seed-review` to an absolute temporary path, give the user the complete explicit table plus digest, and pause for approval. After approval, add a failing exact oracle for the approved entry count, ordered rows, `entries_sha256`, and `approved_seed_sha256`; prove it fails while the repository still has no written manifest update.

- [ ] Invoke `--write --approved-seed-sha256 <the-exact-user-approved-digest>` only after that red oracle defines the output, inspect the entire generated diff, then run `--check` and both manifest test files in a new snapshot. Never infer, auto-accept, or substitute the approval digest.

- [ ] Independently remeasure the six current hashes and all eighteen absences before and after the tests. Confirm no generator or test writes any governed lifecycle path.

- [ ] Review checkpoint: run `git diff --check` and inspect generated metadata. With explicit commit authorization only, create `build(evidence): lock retained and historical identities`.

---

### Task 4: Implement Secure Filesystem and Git Adapters

**Files:**

- Create: `src/pontius/evidence/filesystem.py`
- Create: `src/pontius/evidence/git.py`
- Create: `tests/test_evidence_filesystem_and_git.py`
- Modify: `src/pontius/evidence/manifest.py`
- Modify: `tests/evidence_test_support.py`

**Interfaces:**

- Consumes: Task 1 identity/Git-entry models, Task 2 pure manifest parsers, absolute `Path` values, and a resolved Git executable.
- Produces: `OpenedFile`, `AuthorizationFileSystem`, `RetainedEvidenceFileSystem`, and `GitRepository` protocols; `SubprocessGitRepository`; and the four secure `load_*_manifest` functions with the exact signatures below.

- [ ] Write failing tests for a regular file read once, maximum-size rejection, symlink rejection, Windows reparse-point rejection, path replacement after open, mutation through the open handle, short/long read, changed handle identity, Git timeout/nonzero/malformed output translation, ambiguous tree/index entries, and NUL-delimited changed paths.

- [ ] Define the exact adapter protocols below. A second call to `read_once` raises `RuntimeContractError("evidence_file_already_read", "evidence file was already read")`.

```python
class OpenedFile(Protocol):
    def __enter__(self) -> OpenedFile: ...
    def __exit__(self, exc_type, exc, traceback) -> None: ...
    def identity(self) -> FileIdentity: ...
    def read_once(self, *, maximum_bytes: int) -> bytes: ...

class AuthorizationFileSystem(Protocol):
    def lexists(self, path: Path) -> bool: ...
    def open_regular_nofollow(self, path: Path) -> OpenedFile: ...
    def path_identity_nofollow(self, path: Path) -> FileIdentity | None: ...

class RetainedEvidenceFileSystem(Protocol):
    def read_regular_once(
        self, path: Path, *, maximum_bytes: int
    ) -> tuple[bytes, FileIdentity]: ...
    def path_identity_nofollow(self, path: Path) -> FileIdentity | None: ...
```

- [ ] On Windows, open with `CreateFileW` and `FILE_FLAG_OPEN_REPARSE_POINT`, reject any reparse tag and non-disk/non-regular handle, convert the accepted handle through `msvcrt.open_osfhandle`, and compare volume serial/file index, size, timestamps, and attributes before/after. On POSIX, use `os.open` with `O_RDONLY | O_CLOEXEC | O_NOFOLLOW` when available, require `stat.S_ISREG`, and compare device/inode/size/timestamps. Fail closed when the platform cannot establish the declared identity.

- [ ] Define a structural `GitRepository` protocol with the exact methods below, then implement it as `SubprocessGitRepository(repository_root: Path, git_executable: Path, timeout_seconds: float = 10.0)` with a fresh minimal Git environment, `shell=False`, explicit `cwd`, argument vectors, and bounded stdout/stderr:

```python
def head_commit(self) -> str: ...
def root_tree_oid(self, commit: str) -> str: ...
def tree_entry(self, commit: str, relative_path: str) -> GitTreeEntry | None: ...
def index_entry(self, relative_path: str) -> GitIndexEntry | None: ...
def show_blob(self, commit: str, relative_path: str) -> bytes: ...
def blob_oid(self, commit: str, relative_path: str) -> str: ...
def parent_commits(self, commit: str) -> tuple[str, ...]: ...
def changed_paths(
    self, parent_commit: str, child_commit: str
) -> tuple[str, ...]: ...
```

Use literal `--` path separation, `-z` where paths are returned, and exact decoding. Reject a non-lowercase 40-character commit/blob OID, an unexpected mode/type/stage, multiple rows, a nonzero status, or oversized output.

- [ ] Add the public path loaders with these exact signatures:

```python
def load_sealed_current_files_manifest(
    manifest_path: Path,
    *,
    repository_root: Path,
    filesystem: RetainedEvidenceFileSystem,
) -> SealedCurrentFilesManifest: ...

def load_sealed_current_absences_manifest(
    manifest_path: Path,
    *,
    repository_root: Path,
    filesystem: RetainedEvidenceFileSystem,
) -> SealedCurrentAbsencesManifest: ...

def load_historical_blobs_manifest(
    manifest_path: Path,
    *,
    repository_root: Path,
    filesystem: RetainedEvidenceFileSystem,
) -> HistoricalBlobsManifest: ...

def load_retained_v7_manifest(
    manifest_path: Path,
    *,
    repository_root: Path,
    filesystem: RetainedEvidenceFileSystem,
) -> LoadedRetainedV7Manifest: ...
```

Each validates the manifest path beneath `repository_root`, reads it exactly once through the supplied secure adapter with the fixed 4 MiB bound, then delegates to the Task 2 bytes parser. Rerun all manifest tests.

- [ ] Run the platform tests in a disposable snapshot on Windows/OneDrive and run the POSIX-specific tests only when the platform adapter applies. The Windows adapter-level fake-handle/reparse-tag test is mandatory and unskippable. Only an additional OS-created reparse fixture may skip when the host cannot create it, with an exact capability reason; core regular-file tests may not skip.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `feat(evidence): add one-read file and git adapters`.

---

### Task 5: Implement the Typed Single-Snapshot Authorization Reader

**Files:**

- Create: `src/pontius/evidence/authorization.py`
- Create: `tests/test_evidence_authorization.py`
- Modify: `tests/evidence_test_support.py`

**Interfaces:**

- Consumes: `AuthorizationPolicy`, `AuthorizationState`, `AuthorizationFileSystem`, `GitRepository`, and the Task 1 typed errors.
- Produces: `read_authorization_state(repository_root: Path, *, policy: AuthorizationPolicy, filesystem: AuthorizationFileSystem, git: GitRepository) -> AuthorizationState` and `require_live_authorization(state: AuthorizationState) -> LiveAuthorizationState`; neither function writes lifecycle state or constructs hidden adapters.

- [ ] Write failing tests named for every approved regression: exact absence returns `PreauthorizationState`; requiring live authorization raises `AuthorizationPhaseError` and never `KeyError`; one changing-file double is called once; raw and canonical-LF digests derive from the compared bytes; mixed filesystem/tree/index states reject; canonical-LF-equivalent but raw-different Git bytes reject; ancestry/path drift rejects; and file/path/HEAD/tree/index mutation during the read rejects.

- [ ] Add a safe test-only reproduction of the original defect: construct the exact preauthorization-shaped legacy mapping, prove direct `legacy["authorization_commit"]` raises `KeyError`, then pass the equivalent `PreauthorizationState` to `require_live_authorization` and prove the stable typed `AuthorizationPhaseError` replaces that leak. Do not import the sealed v7 module.

- [ ] Build deterministic fake Git/filesystem adapters that record every call. The changing-file fake must return two individually valid JSON snapshots on successive reads so the test proves the production reader makes exactly one read rather than passing by accident.

- [ ] Implement strict JSON parsing from the supplied `raw: bytes`: UTF-8 only, duplicate keys rejected with `object_pairs_hook`, floats/nonfinite constants rejected, exact top-level keys `schema_version`, `source_seal_commit`, and `authorization_commit_paths`, and exact values from `AuthorizationPolicy`.

- [ ] Expose the reader as `read_authorization_state(repository_root: Path, *, policy: AuthorizationPolicy, filesystem: AuthorizationFileSystem, git: GitRepository) -> AuthorizationState`. Resolve `policy.config_path` beneath `repository_root`, reject root escape before any adapter call, and execute the following state machine exactly once per invocation. Tests inject structural fakes implementing the same signatures; the function does not construct hidden filesystem or Git dependencies.

- [ ] Implement the state machine in this order:

```python
initial_head = git.head_commit()
initial_tree = git.tree_entry(initial_head, policy.config_path)
initial_index = git.index_entry(policy.config_path)
present = filesystem.lexists(config_path)

if not present:
    _require_exact_absence(initial_tree, initial_index)
    _revalidate_repository_snapshot(git, policy, initial_head, initial_tree, initial_index)
    _require_path_still_absent(filesystem.path_identity_nofollow(config_path))
    return PreauthorizationState(head_commit=initial_head, config_path=policy.config_path)

_require_live_entries(initial_tree, initial_index, policy.config_path)
with filesystem.open_regular_nofollow(config_path) as opened:
    before = opened.identity()
    raw = opened.read_once(maximum_bytes=policy.maximum_config_bytes)
    after = opened.identity()
    _require_unchanged_open_file(before, after, len(raw))

config = _parse_authorization_bytes(raw, policy)
raw_digest = sha256(raw).hexdigest()
canonical_digest = sha256(_canonical_lf(raw)).hexdigest()
_require_exact_git_blob(git.show_blob(initial_head, policy.config_path), raw)
_require_sole_child_and_exact_paths(git, initial_head, config, policy)
_revalidate_repository_snapshot(git, policy, initial_head, initial_tree, initial_index)
_require_same_path_identity(after, filesystem.path_identity_nofollow(config_path))
return _build_live_state(config, policy, initial_head, raw_digest, canonical_digest)
```

`_canonical_lf` converts CRLF pairs to LF while preserving lone CR bytes, exactly matching the historical authorization protocol. Raw Git equality remains mandatory even when canonical hashes match.

- [ ] Implement `require_live_authorization(state) -> LiveAuthorizationState` with an `isinstance` check. For `PreauthorizationState`, raise code `authorization_live_state_required` with phase/config context. Never index a mapping for `authorization_commit`.

- [ ] Assert the initial and final Git calls occur in the expected order and that a successful live state contains no mutable list/dictionary.

- [ ] Add an absence-race double that creates a regular file after the initial `lexists` result. Require the final no-follow identity probe to reject it as `authorization_path_changed`; a dangling link or reparse path also counts as present for this check.

- [ ] Rerun the authorization, filesystem/Git, model, and manifest tests in a new snapshot.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `fix(evidence): guard live authorization and parse one snapshot`.

---

### Task 6: Implement Retained-v7 Identity and Journal Assessment

**Files:**

- Create: `src/pontius/evidence/retained_v7.py`
- Create: `tests/test_retained_v7_assessment.py`
- Modify: `src/pontius/evidence/model.py`
- Modify: `src/pontius/evidence/manifest.py`
- Modify: `tests/evidence_test_support.py`

**Interfaces:**

- Consumes: Task 4 secure loaders/adapters, `HistoricalBlobsManifest`, `LoadedRetainedV7Manifest`, and `recover_journal_bytes`/`canonical_journal_json_bytes` from `pontius.durable_evidence_journal`.
- Produces: `assess_retained_v7(repository_root: Path, *, manifest_path: Path, historical_manifest_path: Path, filesystem: RetainedEvidenceFileSystem, git: GitRepository) -> RetainedV7Assessment` and the internal pure `_validate_retained_semantics(recovery, manifest: RetainedV7Manifest) -> None` seam.

- [ ] Write failing tests that assess the exact retained files from current HEAD and assert this result:

```python
self.assertEqual(assessment.terminal, "laboratory_wall_rejected")
self.assertTrue(assessment.journal_complete)
self.assertFalse(assessment.scientific_campaign_complete)
self.assertEqual(assessment.scientific_call_count, 569)
self.assertEqual(assessment.authoritative_measured_call_count, 0)
self.assertFalse(assessment.passed)
self.assertEqual(
    assessment.historical_commit,
    "aaca2dda40e29be8ebd091d58e7853bce1c62fd8",
)
```

Capture `sys.modules` before/after and assert no v7 owner, runner, or sealed result-reader module was imported. Snapshot the governed lifecycle directory and assert no path was created or changed.

- [ ] Add sequential one-byte mutation subtests for result, attempt, and consumed marker through a fake filesystem. Each mutation must raise `EvidenceIntegrityError` before semantic parsing and must leave the real file untouched. Record one read call per artifact and use only one mutated 7.9 MB result allocation at a time.

- [ ] Implement `assess_retained_v7(repository_root, *, manifest_path, historical_manifest_path, filesystem, git)`. Load both manifests strictly, read result/attempt/consumed once each with exact size bounds, compare byte length and raw SHA-256, and require pending/aborted paths to be absent.

- [ ] Call only the generic journal seam:

```python
recovery = recover_journal_bytes(
    result_raw,
    expected_protocol_sha256=manifest.journal_protocol_sha256,
    expected_campaign_sha256=manifest.campaign_sha256,
)
if not recovery.is_complete:
    raise EvidenceIntegrityError(
        "retained_v7_journal_incomplete",
        "retained v7 journal is not an exact complete chain",
        context={"verified_prefix_bytes": len(recovery.verified_prefix_bytes)},
    )
```

Translate parser exceptions and structured recovery failures into stable integrity codes with preserved causes. Require exactly 592 records in sequence, header first, terminal last, and 590 observations between them. Recompute each payload semantic identity with `canonical_journal_json_bytes` and compare it with the stored semantic digest.

- [ ] Verify both historical roots—source seal `ee2437ba1b2efbf2dc4ab3c21bbacdbf26c58648` and authorization `e7bd077f40b1970e9b40a83c891996ab02cd5ffd`—then every one of the 96 source-seal blobs and all six authorization-surface blobs through explicit commit/path Git calls. Do not require current HEAD to equal the historical commit.

- [ ] Rerun the assessor tests plus `tests/test_durable_evidence_journal.py` in a new snapshot.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `feat(evidence): assess retained v7 through generic journal`.

---

### Task 7: Lock Retained-v7 Semantics Without Recomputing Science

**Files:**

- Modify: `src/pontius/evidence/retained_v7.py`
- Modify: `tests/test_retained_v7_assessment.py`

**Interfaces:**

- Consumes: Task 6 `assess_retained_v7`, `_validate_retained_semantics`, recovered journal values, and the frozen retained-v7 manifest.
- Produces: stricter negative-only semantic validation behind the unchanged public assessor signature and the unchanged frozen `RetainedV7Assessment`; no launch, authorization-generation, ranking, fitting, or passing-result API.

- [ ] Add failing mutation tests for record count/order, observation wrapper keys/types, authorization commit, calibration-cell count and phase split, terminal classification, each wall value, partition sum, governed null claims, attempt/consumed marker structure, and pending/aborted absence.

- [ ] Validate exactly 569 `calibration_cell` observation wrappers, with exact wrapper keys and exact nested event keys recorded by the retained format. Require 480 warmup and 89 measured-labelled partial-pass cells. Treat `measured` labels and stored pass bits as diagnostics only; do not sum them into authoritative measured calls.

- [ ] Validate the terminal facts exactly: laboratory elapsed `1510053980800` ns versus wall `1500000000000`; outside-laboratory elapsed `48722365700` ns versus wall `300000000000`; public elapsed `1558776346500` ns versus wall `1800000000000`; exact elapsed partition sum; `laboratory_wall_rejected`; `passed=false`; no fit projection; production base `producer_absent`; no selected candidate/topology/arithmetic schedule; every downstream governed claim null; truncation unauthorized.

- [ ] Validate attempt and consumed marker JSON using strict duplicate-rejecting parsing, exact schema fields/types, and cross-identities to the authorization/result. Do not expose launch tokens in exceptions, logs, or test failure messages; compare only their hashes where the retained protocol requires it.

- [ ] Factor a pure internal `_validate_retained_semantics(recovery, manifest)` seam after artifact/journal identity verification. Build a self-consistent synthetic chain with recalculated payload, semantic, record, and previous-record hashes, then wildly change numeric calibration-cell values while preserving structural wrappers. Call the pure seam and prove it neither ranks, aggregates, fits, admits, nor rejects cells numerically. Public `assess_retained_v7` still rejects any mutation of the real artifact before this seam.

- [ ] Return only the frozen negative `RetainedV7Assessment`. Do not add any API capable of returning a passing calibration, generating authorization, or launching an owner.

- [ ] Assert `docs/architecture/retained-v7.toml` raw and semantic identities remain byte-for-byte equal to the Task 3 generated lock. Task 7 changes validation/tests only; it does not modify the manifest or generator.

- [ ] Rerun retained assessment tests twice in independent bootstrap snapshots and compare assessment fields and semantic manifest identity.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `test(evidence): lock retained v7 negative semantics`.

---

### Task 8: Enforce the Evidence Import and Historical Boundary

**Files:**

- Create: `tests/test_evidence_import_boundary.py`
- Modify: `tools/generate_evidence_manifests.py`
- Modify: `tests/test_evidence_manifest_generation.py`

**Interfaces:**

- Consumes: all evidence modules and generated manifest paths from Tasks 1-7 plus the recorded baseline commit.
- Produces: a read-only AST/diff boundary test and a generator `--check` result that returns success only when generated bytes, import edges, protected present files, and protected absences all match their locks.

- [ ] Write failing AST-based boundary tests that classify every new evidence module and governed manifest path, permit only standard-library/sibling/journal-seam imports, and explicitly deny owners/readers/runners, CuPy/CUDA/GPU, tests, and experiment imports.

- [ ] Add a protected-diff test that resolves the Git diff from baseline and fails if any current sealed-file path is modified/deleted or any sealed-absence path is created. This check is read-only and never attempts restoration.

- [ ] Add generator self-checks proving it imports no `pontius`, test, GPU, or historical module; invokes Git only by argument vector; and has no command that launches a public owner or rewrites retained artifacts.

- [ ] Run all evidence tests in a fresh snapshot. Run the same boundary test against a temporary mutation that adds a forbidden owner import and prove it fails with the exact offending edge.

- [ ] Run `tools/generate_evidence_manifests.py --check` and independently remeasure all six retained current identities and eighteen absences.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `test(architecture): enforce evidence stabilization boundary`.

---

### Task 9: Verify and Review the Evidence Slice

**Files:**

- Modify only if a valid finding requires it: files created in Tasks 1-8
- Create during review only if required by repository convention: `docs/reviews/2026-08-27-evidence-integrity-review.md`

**Interfaces:**

- Consumes: every focused test/check command from Tasks 1-8, the development and exact CPython 3.11 interpreter identities, Ruff when provisioned, and the two named independent review skills.
- Produces: a review record containing exact commands/results/findings/dispositions and a binary evidence-slice gate decision; production interfaces remain unchanged except for fixes required by a validated review finding.

Use this fail-closed suite command after independently capturing each required harness with the Global Constraints procedure. `$HarnessRoot` must be the new H, never the primary checkout:

```powershell
function Invoke-CheckedNative {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Label
    )
    & $Executable @Arguments
    $invoked = $?
    $exitCode = $LASTEXITCODE
    if (-not $invoked -or $exitCode -ne 0) { throw "$Label failed: $exitCode" }
}

function Invoke-EvidenceSuite {
    param(
        [Parameter(Mandatory = $true)][string]$PythonExe,
        [Parameter(Mandatory = $true)][string]$HarnessRoot
    )
    $testPaths = @(
        "tests/test_evidence_errors_and_model.py",
        "tests/test_evidence_manifests.py",
        "tests/test_evidence_manifest_generation.py",
        "tests/test_evidence_filesystem_and_git.py",
        "tests/test_evidence_authorization.py",
        "tests/test_retained_v7_assessment.py",
        "tests/test_evidence_import_boundary.py",
        "tests/test_durable_evidence_journal.py"
    )
    $priorErrorActionPreference = $ErrorActionPreference
    $priorPythonPath = $env:PYTHONPATH
    $pushed = $false
    try {
        $ErrorActionPreference = "Stop"
        if (-not [IO.Path]::IsPathFullyQualified($PythonExe) -or -not [IO.Path]::IsPathFullyQualified($HarnessRoot)) {
            throw "evidence executable and harness must be absolute"
        }
        $pythonItem = Get-Item -LiteralPath $PythonExe -ErrorAction Stop
        $harnessItem = Get-Item -LiteralPath $HarnessRoot -ErrorAction Stop
        if ($pythonItem.PSIsContainer -or $harnessItem.PSIsContainer -eq $false -or
            (($pythonItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) -or
            (($harnessItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
            throw "evidence executable/harness type is invalid"
        }
        Push-Location -LiteralPath $harnessItem.FullName -ErrorAction Stop
        $pushed = $true
        $env:PYTHONPATH = (Join-Path $harnessItem.FullName "src")
        Invoke-CheckedNative -Executable $pythonItem.FullName -Arguments @("-B", "-P", "tools/generate_evidence_manifests.py", "--check") -Label "manifest precheck"
        foreach ($testPath in $testPaths) {
            Invoke-CheckedNative -Executable $pythonItem.FullName -Arguments @("-B", "-P", $testPath, "-v") -Label $testPath
        }
        Invoke-CheckedNative -Executable $pythonItem.FullName -Arguments @("-B", "-P", "tools/generate_evidence_manifests.py", "--check") -Label "manifest postcheck"
    }
    finally {
        if ($null -eq $priorPythonPath) {
            Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
        }
        else {
            $env:PYTHONPATH = $priorPythonPath
        }
        if ($pushed) { Pop-Location }
        $ErrorActionPreference = $priorErrorActionPreference
    }
}
```

Invoke it as `Invoke-EvidenceSuite -PythonExe $python -HarnessRoot $HDevelopment1`, then as `Invoke-EvidenceSuite -PythonExe $python311 -HarnessRoot $H311`, then as `Invoke-EvidenceSuite -PythonExe $python -HarnessRoot $HDevelopment2`. `$HDevelopment1`, `$H311`, and `$HDevelopment2` are three separately captured snapshots. Resolve `$python311` only from absolute `PONTIUS_CPYTHON311` and verify CPython `(3, 11)` before the second invocation.

For the required final Ruff gate, resolve only the absolute executable named by `PONTIUS_RUFF` and run this exact static check from `$HDevelopment2`:

```powershell
$priorErrorActionPreference = $ErrorActionPreference
$ruffConfigured = [Environment]::GetEnvironmentVariable("PONTIUS_RUFF")
$pushed = $false
try {
    $ErrorActionPreference = "Stop"
    if ([string]::IsNullOrWhiteSpace($ruffConfigured) -or -not [IO.Path]::IsPathFullyQualified($ruffConfigured)) {
        throw "PONTIUS_RUFF must name an absolute executable"
    }
    $ruffItem = Get-Item -LiteralPath $ruffConfigured -ErrorAction Stop
    $harnessItem = Get-Item -LiteralPath $HDevelopment2 -ErrorAction Stop
    if ($ruffItem.PSIsContainer -or $harnessItem.PSIsContainer -eq $false -or
        (($ruffItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) -or
        (($harnessItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
        throw "Ruff executable/harness type is invalid"
    }
    Push-Location -LiteralPath $harnessItem.FullName -ErrorAction Stop
    $pushed = $true
    $ruffArguments = @("check", "--no-cache", "src/pontius/evidence", "tools/generate_evidence_manifests.py", "tests/evidence_test_support.py", "tests/test_evidence_errors_and_model.py", "tests/test_evidence_manifests.py", "tests/test_evidence_manifest_generation.py", "tests/test_evidence_filesystem_and_git.py", "tests/test_evidence_authorization.py", "tests/test_retained_v7_assessment.py", "tests/test_evidence_import_boundary.py")
    Invoke-CheckedNative -Executable $ruffItem.FullName -Arguments $ruffArguments -Label "Ruff evidence gate"
}
finally {
    if ($pushed) { Pop-Location }
    $ErrorActionPreference = $priorErrorActionPreference
}
```

- [ ] Capture a fresh disposable snapshot and run every focused evidence test file directly with the development interpreter, followed by the durable journal regression. Record command, interpreter identity, counts, duration, and exit status.

- [ ] Run Ruff over `src/pontius/evidence`, `tools/generate_evidence_manifests.py`, and the new evidence tests. If absolute `PONTIUS_RUFF` is unavailable or fails identity validation, stop the release claim at the explicit static-tool gate.

- [ ] Configure the exact CPython 3.11 slot and rerun the evidence/model/manifest/authorization/assessor suite there. Record the absolute executable, implementation/version, prefix, and installed-distribution fingerprint. Do not substitute the development interpreter.

- [ ] Rerun the complete evidence suite in a second independent snapshot and compare manifest semantic digests, assessment values, test IDs/counts, and outcomes.

- [ ] Verify primary HEAD/status consistency and the protected current-file/absence manifests before and after both runs. Any changed retained identity takes precedence over green tests and blocks the slice.

- [ ] Invoke `codex-engineering-guardrails:code-verification` for a read-only review of the exact added/changed evidence scope. Triage every finding as fixed, rejected with fresh evidence, or deferred with an approved owner/milestone; blocking or major findings cannot be deferred.

- [ ] Invoke `coderabbit:code-review` on the same exact diff scope. Apply the approved 20-minute limit and record baseline `a842c4b6a73a2991a63a481f4107580b72750582`, tool/plugin version, reported model, UTC time, normalized scope/digest, and raw-output location. State unavailability or timeout honestly rather than treating it as success.

- [ ] Enforce an evidence-slice review fixed point. Any accepted review edit invalidates the earlier green evidence: recapture independent harnesses, rerun the complete development/CPython-3.11/development evidence suites, manifest generation/checks, protected present/absence measurements, Ruff, and both reviews over a newly normalized scope/digest. If canonical historical-seed rows/digest changed, stop and repeat the emit/user-approval/token-write gate; never reuse the old approval. Continue until the complete evidence gate and both review dispositions produce no later edit, and record one final tree/scope digest across every result.

- [ ] With explicit commit authorization only, create the final evidence-slice commit after all required gates pass. Otherwise leave a cleanly reviewed uncommitted diff and hand the exact status to the user.

## Evidence-Slice Completion Gate

After the coordinated orchestration data-contract work (Tasks 1-2 and Task 11a), do not proceed to orchestration runtime Tasks 3-10, Task 11b, or Task 12 until all of these are true:

- the original `KeyError` vector is reproduced and eliminated through `require_live_authorization`;
- the changing-file double proves authorization bytes are read exactly once and the same bytes feed parsing, both hashes, and Git comparison;
- current retained/absent identities pass before and after tests;
- retained v7 assesses as journal-complete but scientifically incomplete with zero authoritative measured calls;
- no sealed code or evidence byte changed;
- the evidence import boundary and exact historical manifest checks pass; and
- fresh repository-owned review has no unresolved valid blocking or major issue.
