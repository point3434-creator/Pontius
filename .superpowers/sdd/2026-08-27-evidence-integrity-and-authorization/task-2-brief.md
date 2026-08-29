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

