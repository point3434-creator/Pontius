# Review package: 135f8e30533ca1cace044554bdfd60a564cf83b1..bf8d7f48ea5d5084ea7a8370e3a5f05e7568376d

## Commits
bf8d7f4 test(evidence): cover manifest schema failures

## Files changed
 tests/test_evidence_manifests.py | 26 ++++++++++++++++++++++++++
 1 file changed, 26 insertions(+)

## Diff
diff --git a/tests/test_evidence_manifests.py b/tests/test_evidence_manifests.py
index f6445be..3febabb 100644
--- a/tests/test_evidence_manifests.py
+++ b/tests/test_evidence_manifests.py
@@ -192,20 +192,46 @@ class EvidenceManifestTests(unittest.TestCase):
             ("uppercase-digest", _files_manifest(entry={"raw_sha256": SHA256.upper()})),
             ("short-commit", _files_manifest(baseline_commit="b" * 39)),
             ("traversal", _files_manifest(entry={"relative_path": "../outside.py"})),
             ("absolute", _files_manifest(entry={"relative_path": "/outside.py"})),
             ("drive", _files_manifest(entry={"relative_path": "C:/outside.py"})),
         )
         for name, raw in cases:
             with self.subTest(name=name), self.assertRaises(EvidenceConfigurationError):
                 parse_sealed_current_files_manifest(raw, source_path=self._source("files.toml"), repository_root=ROOT)
 
+    def test_each_schema_rejects_its_applicable_malformed_scalar_path_count_and_digest_fields(self) -> None:
+        cases = (
+            ("files-boolean-entry-length", _files_manifest(entry={"byte_length": True}), parse_sealed_current_files_manifest, "files.toml"),
+            ("files-uppercase-entry-digest", _files_manifest(entry={"raw_sha256": SHA256.upper()}), parse_sealed_current_files_manifest, "files.toml"),
+            ("files-drive-entry-path", _files_manifest(entry={"relative_path": "C:/outside.py"}), parse_sealed_current_files_manifest, "files.toml"),
+            ("files-count", _files_manifest(entry_count=2), parse_sealed_current_files_manifest, "files.toml"),
+            ("absences-boolean-count", _absences_manifest(entry_count=True), parse_sealed_current_absences_manifest, "absences.toml"),
+            ("absences-short-baseline", _absences_manifest(baseline_commit="b" * 39), parse_sealed_current_absences_manifest, "absences.toml"),
+            ("absences-traversal-path", _absences_manifest(entry={"relative_path": "../outside.py"}), parse_sealed_current_absences_manifest, "absences.toml"),
+            ("absences-count", _absences_manifest(entry_count=2), parse_sealed_current_absences_manifest, "absences.toml"),
+            ("historical-boolean-snapshot-count", _historical_manifest(snapshot_count=True), parse_historical_blobs_manifest, "historical.toml"),
+            ("historical-uppercase-blob-digest", _historical_manifest(blobs=[{**_blob_records()[0], "raw_sha256": SHA256.upper()}]), parse_historical_blobs_manifest, "historical.toml"),
+            ("historical-short-blob-oid", _historical_manifest(blobs=[{**_blob_records()[0], "git_blob_oid": "b" * 39}]), parse_historical_blobs_manifest, "historical.toml"),
+            ("historical-absolute-blob-path", _historical_manifest(blobs=[{**_blob_records()[0], "relative_path": "/outside.py"}]), parse_historical_blobs_manifest, "historical.toml"),
+            ("historical-snapshot-count", _historical_manifest(snapshot_count=2), parse_historical_blobs_manifest, "historical.toml"),
+            ("retained-boolean-record-count", _retained_manifest(record_count=True), parse_retained_v7_manifest, "retained.toml"),
+            ("retained-string-boolean", _retained_manifest(journal_complete="true"), parse_retained_v7_manifest, "retained.toml"),
+            ("retained-uppercase-campaign-digest", _retained_manifest(campaign_sha256=SHA256.upper()), parse_retained_v7_manifest, "retained.toml"),
+            ("retained-short-commit", _retained_manifest(source_seal_commit="b" * 39), parse_retained_v7_manifest, "retained.toml"),
+            ("retained-traversal-manifest-path", _retained_manifest(historical_blobs_manifest_path="../historical.toml"), parse_retained_v7_manifest, "retained.toml"),
+            ("retained-absolute-identity-path", _retained_manifest(identities={"result": {"relative_path": "/result.json", "byte_length": 1, "raw_sha256": SHA256, "role": "result"}}), parse_retained_v7_manifest, "retained.toml"),
+        )
+        for name, raw, parser, source_name in cases:
+            with self.subTest(name=name), self.assertRaises(EvidenceConfigurationError):
+                parser(raw, source_path=self._source(source_name), repository_root=ROOT)
+
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
