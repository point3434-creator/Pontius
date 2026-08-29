# Review package: bf8d7f48ea5d5084ea7a8370e3a5f05e7568376d..4da92ebe48231d1b8913bf89d170b410e6bf7163

## Commits
4da92eb test(evidence): complete manifest failure matrix

## Files changed
 tests/test_evidence_manifests.py | 29 ++++++++++++++++++++++++++++-
 1 file changed, 28 insertions(+), 1 deletion(-)

## Diff
diff --git a/tests/test_evidence_manifests.py b/tests/test_evidence_manifests.py
index 3febabb..f11baa8 100644
--- a/tests/test_evidence_manifests.py
+++ b/tests/test_evidence_manifests.py
@@ -193,40 +193,67 @@ class EvidenceManifestTests(unittest.TestCase):
             ("short-commit", _files_manifest(baseline_commit="b" * 39)),
             ("traversal", _files_manifest(entry={"relative_path": "../outside.py"})),
             ("absolute", _files_manifest(entry={"relative_path": "/outside.py"})),
             ("drive", _files_manifest(entry={"relative_path": "C:/outside.py"})),
         )
         for name, raw in cases:
             with self.subTest(name=name), self.assertRaises(EvidenceConfigurationError):
                 parse_sealed_current_files_manifest(raw, source_path=self._source("files.toml"), repository_root=ROOT)
 
     def test_each_schema_rejects_its_applicable_malformed_scalar_path_count_and_digest_fields(self) -> None:
+        # Files, absences, and historical blobs declare no boolean fields;
+        # absences declares no digest. Retained-v7 has no collection-backed
+        # declared count, so a count disagreement is not an applicable
+        # construct for it.
         cases = (
+            ("files-string-entry-length", _files_manifest(entry={"byte_length": "7"}), parse_sealed_current_files_manifest, "files.toml"),
             ("files-boolean-entry-length", _files_manifest(entry={"byte_length": True}), parse_sealed_current_files_manifest, "files.toml"),
             ("files-uppercase-entry-digest", _files_manifest(entry={"raw_sha256": SHA256.upper()}), parse_sealed_current_files_manifest, "files.toml"),
+            ("files-short-entry-digest", _files_manifest(entry={"raw_sha256": "a" * 63}), parse_sealed_current_files_manifest, "files.toml"),
+            ("files-uppercase-baseline", _files_manifest(baseline_commit=COMMIT.upper()), parse_sealed_current_files_manifest, "files.toml"),
+            ("files-short-baseline", _files_manifest(baseline_commit="b" * 39), parse_sealed_current_files_manifest, "files.toml"),
+            ("files-absolute-entry-path", _files_manifest(entry={"relative_path": "/outside.py"}), parse_sealed_current_files_manifest, "files.toml"),
+            ("files-traversal-entry-path", _files_manifest(entry={"relative_path": "../outside.py"}), parse_sealed_current_files_manifest, "files.toml"),
             ("files-drive-entry-path", _files_manifest(entry={"relative_path": "C:/outside.py"}), parse_sealed_current_files_manifest, "files.toml"),
             ("files-count", _files_manifest(entry_count=2), parse_sealed_current_files_manifest, "files.toml"),
+            ("absences-string-count", _absences_manifest(entry_count="1"), parse_sealed_current_absences_manifest, "absences.toml"),
             ("absences-boolean-count", _absences_manifest(entry_count=True), parse_sealed_current_absences_manifest, "absences.toml"),
+            ("absences-uppercase-baseline", _absences_manifest(baseline_commit=COMMIT.upper()), parse_sealed_current_absences_manifest, "absences.toml"),
             ("absences-short-baseline", _absences_manifest(baseline_commit="b" * 39), parse_sealed_current_absences_manifest, "absences.toml"),
+            ("absences-absolute-path", _absences_manifest(entry={"relative_path": "/outside.py"}), parse_sealed_current_absences_manifest, "absences.toml"),
             ("absences-traversal-path", _absences_manifest(entry={"relative_path": "../outside.py"}), parse_sealed_current_absences_manifest, "absences.toml"),
+            ("absences-drive-path", _absences_manifest(entry={"relative_path": "C:/outside.py"}), parse_sealed_current_absences_manifest, "absences.toml"),
             ("absences-count", _absences_manifest(entry_count=2), parse_sealed_current_absences_manifest, "absences.toml"),
+            ("historical-string-snapshot-count", _historical_manifest(snapshot_count="1"), parse_historical_blobs_manifest, "historical.toml"),
             ("historical-boolean-snapshot-count", _historical_manifest(snapshot_count=True), parse_historical_blobs_manifest, "historical.toml"),
+            ("historical-uppercase-entries-digest", _historical_manifest(entries_sha256=SHA256.upper()), parse_historical_blobs_manifest, "historical.toml"),
+            ("historical-short-entries-digest", _historical_manifest(entries_sha256="a" * 63), parse_historical_blobs_manifest, "historical.toml"),
             ("historical-uppercase-blob-digest", _historical_manifest(blobs=[{**_blob_records()[0], "raw_sha256": SHA256.upper()}]), parse_historical_blobs_manifest, "historical.toml"),
+            ("historical-short-blob-digest", _historical_manifest(blobs=[{**_blob_records()[0], "raw_sha256": "a" * 63}]), parse_historical_blobs_manifest, "historical.toml"),
+            ("historical-uppercase-blob-oid", _historical_manifest(blobs=[{**_blob_records()[0], "git_blob_oid": COMMIT.upper()}]), parse_historical_blobs_manifest, "historical.toml"),
             ("historical-short-blob-oid", _historical_manifest(blobs=[{**_blob_records()[0], "git_blob_oid": "b" * 39}]), parse_historical_blobs_manifest, "historical.toml"),
+            ("historical-traversal-blob-path", _historical_manifest(blobs=[{**_blob_records()[0], "relative_path": "../outside.py"}]), parse_historical_blobs_manifest, "historical.toml"),
             ("historical-absolute-blob-path", _historical_manifest(blobs=[{**_blob_records()[0], "relative_path": "/outside.py"}]), parse_historical_blobs_manifest, "historical.toml"),
+            ("historical-drive-blob-path", _historical_manifest(blobs=[{**_blob_records()[0], "relative_path": "C:/outside.py"}]), parse_historical_blobs_manifest, "historical.toml"),
             ("historical-snapshot-count", _historical_manifest(snapshot_count=2), parse_historical_blobs_manifest, "historical.toml"),
+            ("historical-entry-count", _historical_manifest(entry_count=2), parse_historical_blobs_manifest, "historical.toml"),
+            ("retained-string-record-count", _retained_manifest(record_count="1"), parse_retained_v7_manifest, "retained.toml"),
             ("retained-boolean-record-count", _retained_manifest(record_count=True), parse_retained_v7_manifest, "retained.toml"),
             ("retained-string-boolean", _retained_manifest(journal_complete="true"), parse_retained_v7_manifest, "retained.toml"),
+            ("retained-integer-boolean", _retained_manifest(journal_complete=1), parse_retained_v7_manifest, "retained.toml"),
             ("retained-uppercase-campaign-digest", _retained_manifest(campaign_sha256=SHA256.upper()), parse_retained_v7_manifest, "retained.toml"),
+            ("retained-short-campaign-digest", _retained_manifest(campaign_sha256="a" * 63), parse_retained_v7_manifest, "retained.toml"),
+            ("retained-uppercase-commit", _retained_manifest(source_seal_commit=COMMIT.upper()), parse_retained_v7_manifest, "retained.toml"),
             ("retained-short-commit", _retained_manifest(source_seal_commit="b" * 39), parse_retained_v7_manifest, "retained.toml"),
+            ("retained-absolute-manifest-path", _retained_manifest(historical_blobs_manifest_path="/historical.toml"), parse_retained_v7_manifest, "retained.toml"),
             ("retained-traversal-manifest-path", _retained_manifest(historical_blobs_manifest_path="../historical.toml"), parse_retained_v7_manifest, "retained.toml"),
-            ("retained-absolute-identity-path", _retained_manifest(identities={"result": {"relative_path": "/result.json", "byte_length": 1, "raw_sha256": SHA256, "role": "result"}}), parse_retained_v7_manifest, "retained.toml"),
+            ("retained-drive-manifest-path", _retained_manifest(historical_blobs_manifest_path="C:/historical.toml"), parse_retained_v7_manifest, "retained.toml"),
         )
         for name, raw, parser, source_name in cases:
             with self.subTest(name=name), self.assertRaises(EvidenceConfigurationError):
                 parser(raw, source_path=self._source(source_name), repository_root=ROOT)
 
     def test_each_schema_rejects_missing_or_extra_root_fields(self) -> None:
         cases = (
             ("files-missing", _files_manifest().replace(b"schema_version = ", b"missing_schema_version = "), parse_sealed_current_files_manifest, "files.toml"),
             ("absences-missing", _absences_manifest().replace(b"schema_version = ", b"missing_schema_version = "), parse_sealed_current_absences_manifest, "absences.toml"),
             ("historical-missing", _historical_manifest().replace(b"schema_version = ", b"missing_schema_version = "), parse_historical_blobs_manifest, "historical.toml"),
