from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import unittest

from pontius.evidence.errors import EvidenceConfigurationError, EvidenceIntegrityError
from pontius.evidence.manifest import (
    canonical_semantic_bytes,
    parse_historical_blobs_manifest,
    parse_retained_v7_manifest,
    parse_sealed_current_absences_manifest,
    parse_sealed_current_files_manifest,
    semantic_sha256,
    validate_current_boundary,
)


COMMIT = "b" * 40
SHA256 = "a" * 64
ROOT = Path("C:/evidence-repository")

_SUPPORT_PATH = Path(__file__).with_name("evidence_test_support.py")
_SUPPORT_SPEC = importlib.util.spec_from_file_location("evidence_test_support", _SUPPORT_PATH)
if _SUPPORT_SPEC is None or _SUPPORT_SPEC.loader is None:
    raise RuntimeError("test support could not be loaded by exact path")
_SUPPORT = importlib.util.module_from_spec(_SUPPORT_SPEC)
_SUPPORT_SPEC.loader.exec_module(_SUPPORT)


def _toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return json.dumps(value)


def _toml_mapping(mapping: dict[str, object], *, skip: set[str] = frozenset()) -> str:
    return "\n".join(f"{key} = {_toml_value(value)}" for key, value in mapping.items() if key not in skip)


def _files_manifest(**overrides: object) -> bytes:
    values: dict[str, object] = {
        "schema_version": "pontius-sealed-current-files-v1",
        "baseline_commit": COMMIT,
        "entry_count": 1,
    }
    values.update({key: value for key, value in overrides.items() if key in values})
    entry = {
        "relative_path": "src/current.py",
        "byte_length": 7,
        "raw_sha256": SHA256,
        "role": "source",
        "governing_decision": "ADR-1",
        "owner": "owner-a",
    }
    entry.update(overrides.get("entry", {}))
    return (_toml_mapping(values) + "\n\n[[files]]\n" + _toml_mapping(entry) + "\n").encode("utf-8")


def _absences_manifest(**overrides: object) -> bytes:
    values: dict[str, object] = {
        "schema_version": "pontius-sealed-current-absences-v1",
        "baseline_commit": COMMIT,
        "entry_count": 1,
    }
    values.update({key: value for key, value in overrides.items() if key in values})
    entry = {
        "relative_path": "src/absent.py",
        "role": "absence",
        "governing_decision": "ADR-2",
        "owner": "owner-b",
    }
    entry.update(overrides.get("entry", {}))
    return (_toml_mapping(values) + "\n\n[[absences]]\n" + _toml_mapping(entry) + "\n").encode("utf-8")


def _blob_records() -> list[dict[str, object]]:
    return [{
        "commit": COMMIT,
        "relative_path": "src/history.py",
        "git_blob_oid": COMMIT,
        "raw_sha256": SHA256,
        "role": "source",
        "phase": "source",
        "governing_decision": "ADR-3",
    }]


def _historical_manifest(**overrides: object) -> bytes:
    blobs = overrides.get("blobs", _blob_records())
    values: dict[str, object] = {
        "schema_version": "pontius-historical-blobs-v1",
        "baseline_commit": COMMIT,
        "snapshot_count": 1,
        "entry_count": len(blobs),
        "entries_sha256": semantic_sha256(blobs),
        "approved_seed_sha256": SHA256,
    }
    values.update({key: value for key, value in overrides.items() if key in values})
    snapshot = {
        "phase": "source",
        "commit": COMMIT,
        "root_tree_oid": COMMIT,
        "governing_decision": "ADR-3",
    }
    snapshot.update(overrides.get("snapshot", {}))
    chunks = [_toml_mapping(values), "[[snapshots]]\n" + _toml_mapping(snapshot)]
    for blob in blobs:
        chunks.append("[[blobs]]\n" + _toml_mapping(blob))
    return ("\n\n".join(chunks) + "\n").encode("utf-8")


def _retained_mapping() -> dict[str, object]:
    return {
        "schema_version": "pontius-retained-v7-v1",
        "source_seal_commit": COMMIT,
        "authorization_commit": COMMIT,
        "historical_reader_commit": COMMIT,
        "journal_protocol_sha256": SHA256,
        "campaign_sha256": SHA256,
        "record_count": 1,
        "observation_count": 0,
        "calibration_cell_count": 0,
        "warmup_cell_count": 0,
        "measured_labelled_partial_cell_count": 0,
        "terminal": "retained",
        "journal_complete": True,
        "scientific_campaign_complete": False,
        "scientific_call_count": 0,
        "authoritative_measured_call_count": 0,
        "passed": False,
        "laboratory_elapsed_ns": 1,
        "laboratory_wall_ns": 2,
        "outside_laboratory_elapsed_ns": 3,
        "outside_laboratory_wall_ns": 4,
        "public_elapsed_ns": 5,
        "public_wall_ns": 6,
        "fit_projection_present": False,
        "production_base_classification": "rejected",
        "candidate_selection_present": False,
        "topology_selection_present": False,
        "arithmetic_schedule_selection_present": False,
        "truncation_authorized": False,
        "historical_blobs_manifest_path": "evidence/historical.toml",
        "absent_launch_paths": ["run_absent.py"],
        "expected_null_claim_paths": ["claim-a", "claim-b"],
    }


def _retained_manifest(*, reverse: bool = False, **overrides: object) -> bytes:
    values = _retained_mapping()
    values.update({key: value for key, value in overrides.items() if key in values})
    identities = {
        "result": {"relative_path": "artifacts/result.json", "byte_length": 1, "raw_sha256": SHA256, "role": "result"},
        "attempt": {"relative_path": "artifacts/attempt.json", "byte_length": 2, "raw_sha256": SHA256, "role": "attempt"},
        "consumed_launch": {"relative_path": "run.py", "byte_length": 3, "raw_sha256": SHA256, "role": "launch"},
    }
    identities.update(overrides.get("identities", {}))
    items = list(values.items())
    if reverse:
        items.reverse()
    chunks = [_toml_mapping(dict(items))]
    for label, identity in identities.items():
        chunks.append(f"[{label}]\n" + _toml_mapping(identity))
    return ("\n\n".join(chunks) + "\n").encode("utf-8")


class EvidenceManifestTests(unittest.TestCase):
    def _source(self, name: str) -> Path:
        return ROOT / "evidence" / name

    def test_parses_each_strict_manifest_schema(self) -> None:
        files = parse_sealed_current_files_manifest(_files_manifest(), source_path=self._source("files.toml"), repository_root=ROOT)
        absences = parse_sealed_current_absences_manifest(_absences_manifest(), source_path=self._source("absences.toml"), repository_root=ROOT)
        historical = parse_historical_blobs_manifest(_historical_manifest(), source_path=self._source("historical.toml"), repository_root=ROOT)
        retained = parse_retained_v7_manifest(_retained_manifest(), source_path=self._source("retained.toml"), repository_root=ROOT)
        self.assertEqual(files.files[0].relative_path, "src/current.py")
        self.assertEqual(absences.absences[0].relative_path, "src/absent.py")
        self.assertEqual(historical.blobs[0].relative_path, "src/history.py")
        self.assertEqual(retained.manifest.terminal, "retained")

    def test_schema_tables_reject_missing_extra_and_wrong_scalar_values(self) -> None:
        cases = (
            ("missing", _files_manifest().replace(b"owner = \"owner-a\"\n", b"")),
            ("extra", _files_manifest() + b"extra = \"value\"\n"),
            ("string-integer", _files_manifest(entry={"byte_length": "7"})),
            ("boolean-integer", _files_manifest(entry={"byte_length": True})),
            ("uppercase-digest", _files_manifest(entry={"raw_sha256": SHA256.upper()})),
            ("short-commit", _files_manifest(baseline_commit="b" * 39)),
            ("traversal", _files_manifest(entry={"relative_path": "../outside.py"})),
            ("absolute", _files_manifest(entry={"relative_path": "/outside.py"})),
            ("drive", _files_manifest(entry={"relative_path": "C:/outside.py"})),
        )
        for name, raw in cases:
            with self.subTest(name=name), self.assertRaises(EvidenceConfigurationError):
                parse_sealed_current_files_manifest(raw, source_path=self._source("files.toml"), repository_root=ROOT)

    def test_each_schema_rejects_its_applicable_malformed_scalar_path_count_and_digest_fields(self) -> None:
        # Files, absences, and historical blobs declare no boolean fields;
        # absences declares no digest. Retained-v7 has no collection-backed
        # declared count, so a count disagreement is not an applicable
        # construct for it.
        cases = (
            ("files-string-entry-length", _files_manifest(entry={"byte_length": "7"}), parse_sealed_current_files_manifest, "files.toml"),
            ("files-boolean-entry-length", _files_manifest(entry={"byte_length": True}), parse_sealed_current_files_manifest, "files.toml"),
            ("files-uppercase-entry-digest", _files_manifest(entry={"raw_sha256": SHA256.upper()}), parse_sealed_current_files_manifest, "files.toml"),
            ("files-short-entry-digest", _files_manifest(entry={"raw_sha256": "a" * 63}), parse_sealed_current_files_manifest, "files.toml"),
            ("files-uppercase-baseline", _files_manifest(baseline_commit=COMMIT.upper()), parse_sealed_current_files_manifest, "files.toml"),
            ("files-short-baseline", _files_manifest(baseline_commit="b" * 39), parse_sealed_current_files_manifest, "files.toml"),
            ("files-absolute-entry-path", _files_manifest(entry={"relative_path": "/outside.py"}), parse_sealed_current_files_manifest, "files.toml"),
            ("files-traversal-entry-path", _files_manifest(entry={"relative_path": "../outside.py"}), parse_sealed_current_files_manifest, "files.toml"),
            ("files-drive-entry-path", _files_manifest(entry={"relative_path": "C:/outside.py"}), parse_sealed_current_files_manifest, "files.toml"),
            ("files-count", _files_manifest(entry_count=2), parse_sealed_current_files_manifest, "files.toml"),
            ("absences-string-count", _absences_manifest(entry_count="1"), parse_sealed_current_absences_manifest, "absences.toml"),
            ("absences-boolean-count", _absences_manifest(entry_count=True), parse_sealed_current_absences_manifest, "absences.toml"),
            ("absences-uppercase-baseline", _absences_manifest(baseline_commit=COMMIT.upper()), parse_sealed_current_absences_manifest, "absences.toml"),
            ("absences-short-baseline", _absences_manifest(baseline_commit="b" * 39), parse_sealed_current_absences_manifest, "absences.toml"),
            ("absences-absolute-path", _absences_manifest(entry={"relative_path": "/outside.py"}), parse_sealed_current_absences_manifest, "absences.toml"),
            ("absences-traversal-path", _absences_manifest(entry={"relative_path": "../outside.py"}), parse_sealed_current_absences_manifest, "absences.toml"),
            ("absences-drive-path", _absences_manifest(entry={"relative_path": "C:/outside.py"}), parse_sealed_current_absences_manifest, "absences.toml"),
            ("absences-count", _absences_manifest(entry_count=2), parse_sealed_current_absences_manifest, "absences.toml"),
            ("historical-string-snapshot-count", _historical_manifest(snapshot_count="1"), parse_historical_blobs_manifest, "historical.toml"),
            ("historical-boolean-snapshot-count", _historical_manifest(snapshot_count=True), parse_historical_blobs_manifest, "historical.toml"),
            ("historical-uppercase-entries-digest", _historical_manifest(entries_sha256=SHA256.upper()), parse_historical_blobs_manifest, "historical.toml"),
            ("historical-short-entries-digest", _historical_manifest(entries_sha256="a" * 63), parse_historical_blobs_manifest, "historical.toml"),
            ("historical-uppercase-blob-digest", _historical_manifest(blobs=[{**_blob_records()[0], "raw_sha256": SHA256.upper()}]), parse_historical_blobs_manifest, "historical.toml"),
            ("historical-short-blob-digest", _historical_manifest(blobs=[{**_blob_records()[0], "raw_sha256": "a" * 63}]), parse_historical_blobs_manifest, "historical.toml"),
            ("historical-uppercase-blob-oid", _historical_manifest(blobs=[{**_blob_records()[0], "git_blob_oid": COMMIT.upper()}]), parse_historical_blobs_manifest, "historical.toml"),
            ("historical-short-blob-oid", _historical_manifest(blobs=[{**_blob_records()[0], "git_blob_oid": "b" * 39}]), parse_historical_blobs_manifest, "historical.toml"),
            ("historical-traversal-blob-path", _historical_manifest(blobs=[{**_blob_records()[0], "relative_path": "../outside.py"}]), parse_historical_blobs_manifest, "historical.toml"),
            ("historical-absolute-blob-path", _historical_manifest(blobs=[{**_blob_records()[0], "relative_path": "/outside.py"}]), parse_historical_blobs_manifest, "historical.toml"),
            ("historical-drive-blob-path", _historical_manifest(blobs=[{**_blob_records()[0], "relative_path": "C:/outside.py"}]), parse_historical_blobs_manifest, "historical.toml"),
            ("historical-snapshot-count", _historical_manifest(snapshot_count=2), parse_historical_blobs_manifest, "historical.toml"),
            ("historical-entry-count", _historical_manifest(entry_count=2), parse_historical_blobs_manifest, "historical.toml"),
            ("retained-string-record-count", _retained_manifest(record_count="1"), parse_retained_v7_manifest, "retained.toml"),
            ("retained-boolean-record-count", _retained_manifest(record_count=True), parse_retained_v7_manifest, "retained.toml"),
            ("retained-string-boolean", _retained_manifest(journal_complete="true"), parse_retained_v7_manifest, "retained.toml"),
            ("retained-integer-boolean", _retained_manifest(journal_complete=1), parse_retained_v7_manifest, "retained.toml"),
            ("retained-uppercase-campaign-digest", _retained_manifest(campaign_sha256=SHA256.upper()), parse_retained_v7_manifest, "retained.toml"),
            ("retained-short-campaign-digest", _retained_manifest(campaign_sha256="a" * 63), parse_retained_v7_manifest, "retained.toml"),
            ("retained-uppercase-commit", _retained_manifest(source_seal_commit=COMMIT.upper()), parse_retained_v7_manifest, "retained.toml"),
            ("retained-short-commit", _retained_manifest(source_seal_commit="b" * 39), parse_retained_v7_manifest, "retained.toml"),
            ("retained-absolute-manifest-path", _retained_manifest(historical_blobs_manifest_path="/historical.toml"), parse_retained_v7_manifest, "retained.toml"),
            ("retained-traversal-manifest-path", _retained_manifest(historical_blobs_manifest_path="../historical.toml"), parse_retained_v7_manifest, "retained.toml"),
            ("retained-drive-manifest-path", _retained_manifest(historical_blobs_manifest_path="C:/historical.toml"), parse_retained_v7_manifest, "retained.toml"),
        )
        for name, raw, parser, source_name in cases:
            with self.subTest(name=name), self.assertRaises(EvidenceConfigurationError):
                parser(raw, source_path=self._source(source_name), repository_root=ROOT)

    def test_each_schema_rejects_missing_or_extra_root_fields(self) -> None:
        cases = (
            ("files-missing", _files_manifest().replace(b"schema_version = ", b"missing_schema_version = "), parse_sealed_current_files_manifest, "files.toml"),
            ("absences-missing", _absences_manifest().replace(b"schema_version = ", b"missing_schema_version = "), parse_sealed_current_absences_manifest, "absences.toml"),
            ("historical-missing", _historical_manifest().replace(b"schema_version = ", b"missing_schema_version = "), parse_historical_blobs_manifest, "historical.toml"),
            ("retained-missing", _retained_manifest().replace(b"schema_version = ", b"missing_schema_version = "), parse_retained_v7_manifest, "retained.toml"),
            ("files-extra", b"unexpected = 1\n" + _files_manifest(), parse_sealed_current_files_manifest, "files.toml"),
            ("absences-extra", b"unexpected = 1\n" + _absences_manifest(), parse_sealed_current_absences_manifest, "absences.toml"),
            ("historical-extra", b"unexpected = 1\n" + _historical_manifest(), parse_historical_blobs_manifest, "historical.toml"),
            ("retained-extra", b"unexpected = 1\n" + _retained_manifest(), parse_retained_v7_manifest, "retained.toml"),
        )
        for name, raw, parser, source_name in cases:
            with self.subTest(name=name), self.assertRaises(EvidenceConfigurationError):
                parser(raw, source_path=self._source(source_name), repository_root=ROOT)

    def test_toml_syntax_and_duplicate_keys_are_configuration_errors_with_cause(self) -> None:
        raw = _files_manifest().replace(b"entry_count = 1", b"entry_count = 1\nentry_count = 1")
        with self.assertRaises(EvidenceConfigurationError) as raised:
            parse_sealed_current_files_manifest(raw, source_path=self._source("files.toml"), repository_root=ROOT)
        self.assertEqual(raised.exception.code, "manifest_toml_invalid")
        self.assertIsNotNone(raised.exception.__cause__)

    def test_duplicate_toml_table_is_a_configuration_error(self) -> None:
        raw = _retained_manifest() + b"\n[result]\nrelative_path = \"other.json\"\nbyte_length = 1\nraw_sha256 = \"" + SHA256.encode() + b"\"\nrole = \"result\"\n"
        with self.assertRaises(EvidenceConfigurationError) as raised:
            parse_retained_v7_manifest(raw, source_path=self._source("retained.toml"), repository_root=ROOT)
        self.assertEqual(raised.exception.code, "manifest_toml_invalid")

    def test_historical_manifest_rejects_duplicate_commit_path_counts_and_digest_disagreement(self) -> None:
        duplicate = _blob_records() * 2
        cases = (
            ("duplicate-identity", _historical_manifest(blobs=duplicate, entry_count=2)),
            ("count", _historical_manifest(entry_count=2)),
            ("digest", _historical_manifest(entries_sha256="c" * 64)),
        )
        for name, raw in cases:
            with self.subTest(name=name), self.assertRaises((EvidenceConfigurationError, EvidenceIntegrityError)):
                parse_historical_blobs_manifest(raw, source_path=self._source("historical.toml"), repository_root=ROOT)

    def test_current_boundary_rejects_overlap_owner_duplicates_and_baseline_disagreement(self) -> None:
        files = parse_sealed_current_files_manifest(_files_manifest(), source_path=self._source("files.toml"), repository_root=ROOT)
        overlap = parse_sealed_current_absences_manifest(_absences_manifest(entry={"relative_path": "src/current.py"}), source_path=self._source("absences.toml"), repository_root=ROOT)
        changed_baseline = parse_sealed_current_absences_manifest(_absences_manifest(baseline_commit="c" * 40), source_path=self._source("absences.toml"), repository_root=ROOT)
        duplicate_owner = parse_sealed_current_files_manifest(
            _files_manifest(entry_count=2) + b"\n[[files]]\nrelative_path = \"src/current.py\"\nbyte_length = 7\nraw_sha256 = \"" + SHA256.encode() + b"\"\nrole = \"source\"\ngoverning_decision = \"ADR-1\"\nowner = \"owner-a\"\n",
            source_path=self._source("files.toml"), repository_root=ROOT,
        )
        for name, left, right in (("overlap", files, overlap), ("baseline", files, changed_baseline), ("owner", duplicate_owner, parse_sealed_current_absences_manifest(_absences_manifest(), source_path=self._source("absences.toml"), repository_root=ROOT))):
            with self.subTest(name=name), self.assertRaises(EvidenceIntegrityError):
                validate_current_boundary(left, right)

    def test_retained_semantic_identity_is_key_order_independent_but_raw_identity_is_not(self) -> None:
        first_raw = _retained_manifest()
        second_raw = _retained_manifest(reverse=True)
        first = parse_retained_v7_manifest(first_raw, source_path=self._source("retained-a.toml"), repository_root=ROOT)
        second = parse_retained_v7_manifest(second_raw, source_path=self._source("retained-b.toml"), repository_root=ROOT)
        self.assertEqual(first.semantic_sha256, second.semantic_sha256)
        self.assertNotEqual(first.source_identity.raw_sha256, second.source_identity.raw_sha256)
        self.assertEqual(canonical_semantic_bytes({"b": (True, 2), "a": None}), b'{"a":null,"b":[true,2]}')
        self.assertEqual(semantic_sha256({"a": 1}), sha256(b'{"a":1}').hexdigest())


if __name__ == "__main__":
    unittest.main(verbosity=2)
