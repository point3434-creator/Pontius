# Review package: c24fd4f4b5f68cecca74f23385b02141fa890ed8..49f6b8141ad3284c3e33d596a5cfd2155ec8709f

## Commits
49f6b81 fix(evidence): constrain preapproval seed derivation

## Files changed
 tests/test_evidence_manifest_generation.py | 288 +++++++++++++++++---
 tests/test_evidence_manifests.py           |  84 +++++-
 tools/generate_evidence_manifests.py       | 424 ++++++++++++++++++++++-------
 3 files changed, 652 insertions(+), 144 deletions(-)

## Diff
diff --git a/tests/test_evidence_manifest_generation.py b/tests/test_evidence_manifest_generation.py
index c73f043..37ffe24 100644
--- a/tests/test_evidence_manifest_generation.py
+++ b/tests/test_evidence_manifest_generation.py
@@ -1,13 +1,15 @@
 from __future__ import annotations
 
 import importlib.util
+import ast
+import io
 import json
 import os
 from pathlib import Path
 import tempfile
 import unittest
 from unittest import mock
 
 
 REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
 TOOL_PATH = REPOSITORY_ROOT / "tools" / "generate_evidence_manifests.py"
@@ -42,20 +44,39 @@ ABSENCE_PATHS = (
     "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.attempt.json",
     "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.jsonl",
     "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-aborted.json",
     "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-consumed.json",
     "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-pending.json",
     "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-aborted.json",
     "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-pending.json",
     "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v8-corrected-invocation-authorization.json",
 )
 
+ABSENCE_ROWS = tuple(
+    (item["relative_path"], item["role"], item["governing_decision"], item["owner"])
+    for item in GENERATOR.CURRENT_ABSENCE_ENTRIES
+)
+
+SAMPLE_ROW = {
+    "commit": "1" * 40, "relative_path": "src/pontius/a.py",
+    "git_blob_oid": "2" * 40, "raw_sha256": "3" * 64,
+    "role": "source_dependency", "phase": "phase-a",
+    "governing_decision": "ADR-0001",
+}
+SAMPLE_STATE = {
+    "current_files": list(GENERATOR.CURRENT_FILE_ENTRIES),
+    "current_absences": list(GENERATOR.CURRENT_ABSENCE_ENTRIES),
+    "snapshots": list(GENERATOR.SNAPSHOTS),
+    "blobs": [SAMPLE_ROW],
+    "entries_sha256": GENERATOR.historical_entries_sha256([SAMPLE_ROW]),
+}
+
 
 SNAPSHOT_PAIRS = (
     ("88148da07324c13b79c72ea494b14167a975c001", "bc5d1952f690da5d49275344919de36224af26cb"),
     ("08bb6857f47f9669b8f531c65079d4decd52a573", "0d01a4133a4e6ab10467ad0bd298630149702a73"),
     ("3de8e0c9eebf67f2cc2573041242a869468de6e9", "ea80b86ac60cb324e3c18ddad83d8bbba0ade933"),
     ("77feb7c78990ca53e70b1302a6866fe5d781411f", "d26ba99c033875342a652ae352067beee1ca44ee"),
     ("ba6a3418b7c991238cc1a65898fd61fa03b4a3cb", "73b53cb04c91459e8b7028ccd292b972d2dfdf69"),
     ("815d23c115289347e3d4028a4866eb9f87d4669a", "894c026603156df4bba1134ba9861e98bd3a6663"),
     ("5c0c9a401e5f2ebf59296832d954d0075c4d4624", "f3418410c442a4d06c62aba9777def72633ca5c5"),
     ("d633f3fb469a27dee688587293c6efb1d2cb2757", "9c9ff658c2836bde5d1df71f5596d1d6aa1a5bd2"),
@@ -69,45 +90,63 @@ AUTHORIZATION_PATHS = (
     "ARCHITECTURE.md",
     "RISK_REGISTER.md",
     "ROADMAP.md",
     "STATUS.md",
     "docs/decisions/ADR-0475-authorize-one-v7-authorization-phase-calibration-invocation.md",
     "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v11-authorization-phase-corrected-invocation-authorization.json",
 )
 
 
 class EvidenceManifestGenerationTests(unittest.TestCase):
-    @classmethod
-    def setUpClass(cls) -> None:
-        cls.state = GENERATOR.derive_manifest_state(REPOSITORY_ROOT)
-
     def test_current_file_identities_and_absences_are_exact_and_disjoint(self) -> None:
         actual_files = tuple(
             (item["relative_path"], item["byte_length"], item["raw_sha256"], item["role"], item["governing_decision"], item["owner"])
             for item in GENERATOR.CURRENT_FILE_ENTRIES
         )
         self.assertEqual(actual_files, CURRENT_FILES)
         self.assertEqual(tuple(sorted(item["relative_path"] for item in GENERATOR.CURRENT_ABSENCE_ENTRIES)), ABSENCE_PATHS)
         self.assertEqual(len(GENERATOR.CURRENT_ABSENCE_ENTRIES), 18)
+        expected_absences = (
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v3.jsonl", "closed_result_absence", "ADR-0466", "compiled_global_separation_calibration_v3"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.jsonl", "closed_result_absence", "ADR-0469", "compiled_global_separation_calibration_v4"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.attempt.json", "closed_attempt_absence", "ADR-0469", "compiled_global_separation_calibration_v4"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.launch-pending.json", "closed_launch_pending_absence", "ADR-0469", "compiled_global_separation_calibration_v4"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.launch-consumed.json", "closed_launch_consumed_absence", "ADR-0469", "compiled_global_separation_calibration_v4"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.launch-aborted.json", "closed_launch_aborted_absence", "ADR-0469", "compiled_global_separation_calibration_v4"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.jsonl", "closed_result_absence", "ADR-0470", "compiled_global_separation_calibration_v5"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.launch-pending.json", "closed_launch_pending_absence", "ADR-0470", "compiled_global_separation_calibration_v5"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.launch-consumed.json", "closed_launch_consumed_absence", "ADR-0470", "compiled_global_separation_calibration_v5"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.launch-aborted.json", "closed_launch_aborted_absence", "ADR-0470", "compiled_global_separation_calibration_v5"),
+            ("experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v8-corrected-invocation-authorization.json", "rejected_authorization_absence", "ADR-0473", "compiled_global_separation_calibration_v6"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.jsonl", "closed_result_absence", "ADR-0473", "compiled_global_separation_calibration_v6"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.attempt.json", "closed_attempt_absence", "ADR-0473", "compiled_global_separation_calibration_v6"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-pending.json", "closed_launch_pending_absence", "ADR-0473", "compiled_global_separation_calibration_v6"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-consumed.json", "closed_launch_consumed_absence", "ADR-0473", "compiled_global_separation_calibration_v6"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-aborted.json", "closed_launch_aborted_absence", "ADR-0473", "compiled_global_separation_calibration_v6"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-pending.json", "closed_launch_pending_absence", "ADR-0476", "compiled_global_separation_calibration_v7"),
+            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-aborted.json", "closed_launch_aborted_absence", "ADR-0476", "compiled_global_separation_calibration_v7"),
+        )
+        self.assertEqual(ABSENCE_ROWS, expected_absences)
         self.assertFalse(set(path for path, *_ in CURRENT_FILES) & set(ABSENCE_PATHS))
-        self.assertEqual(self.state["current_files"], list(GENERATOR.CURRENT_FILE_ENTRIES))
-        self.assertEqual(self.state["current_absences"], list(GENERATOR.CURRENT_ABSENCE_ENTRIES))
+        measured, _ = GENERATOR._measure_current(REPOSITORY_ROOT)
+        self.assertEqual(measured, list(GENERATOR.CURRENT_FILE_ENTRIES))
 
     def test_historical_snapshots_source_seal_group_and_authorization_surface_are_exact(self) -> None:
+        state = GENERATOR.derive_manifest_state(REPOSITORY_ROOT)
         self.assertEqual(tuple((item["commit"], item["root_tree_oid"]) for item in GENERATOR.SNAPSHOTS), SNAPSHOT_PAIRS)
-        source_rows = [row for row in self.state["blobs"] if row["phase"] == "v7_source_seal"]
-        with (REPOSITORY_ROOT / CURRENT_FILES[3][0]).open("rb") as stream:
-            header = json.loads(stream.readline())
+        source_rows = [row for row in state["blobs"] if row["phase"] == "v7_source_seal"]
+        raw = GENERATOR.read_regular_file_once(REPOSITORY_ROOT / CURRENT_FILES[3][0], maximum_bytes=CURRENT_FILES[3][1])
+        header = json.loads(raw.split(b"\n", 1)[0])
         expected_source_paths = tuple(sorted(header["body"]["payload"]["dependency_hashes"]))
         self.assertEqual(len(source_rows), 96)
         self.assertEqual(tuple(row["relative_path"] for row in source_rows), expected_source_paths)
-        authorization_rows = [row for row in self.state["blobs"] if row["phase"] == "v7_live_authorization"]
+        authorization_rows = [row for row in state["blobs"] if row["phase"] == "v7_live_authorization"]
         self.assertEqual(tuple(row["relative_path"] for row in authorization_rows), AUTHORIZATION_PATHS)
         self.assertEqual(len(authorization_rows), 6)
 
     def test_historical_entry_digest_is_order_independent_and_covers_every_field(self) -> None:
         first = {"commit": "1" * 40, "relative_path": "src/a.py", "git_blob_oid": "2" * 40, "raw_sha256": "3" * 64, "role": "source_dependency", "phase": "phase-a", "governing_decision": "ADR-0001"}
         second = {**first, "relative_path": "src/b.py", "raw_sha256": "4" * 64}
         digest = GENERATOR.historical_entries_sha256([second, first])
         self.assertEqual(digest, GENERATOR.historical_entries_sha256([first, second]))
         self.assertNotEqual(digest, GENERATOR.historical_entries_sha256([{**first, "role": "test"}, second]))
 
@@ -123,72 +162,257 @@ class EvidenceManifestGenerationTests(unittest.TestCase):
             "journal_complete": True, "scientific_campaign_complete": False,
             "historical_reader_commit": "aaca2dda40e29be8ebd091d58e7853bce1c62fd8",
         }
         self.assertEqual({key: retained[key] for key in expected}, expected)
 
     def test_approval_refusal_and_mismatch_return_before_any_manifest_write(self) -> None:
         with tempfile.TemporaryDirectory(prefix="pontius-task3-approval-") as directory:
             root = Path(directory)
             for supplied in (None, "A" * 64, "0" * 63, "0" * 64):
                 with self.subTest(supplied=supplied), self.assertRaises(GENERATOR.GenerationError):
-                    GENERATOR.write_manifests(root, self.state, approved_seed_sha256=supplied)
+                    GENERATOR.write_manifests(root, SAMPLE_STATE, approved_seed_sha256=supplied)
             self.assertEqual(list(root.iterdir()), [])
 
     def test_check_is_read_only_when_approval_manifests_are_absent(self) -> None:
         destinations = tuple(REPOSITORY_ROOT / path for path in GENERATOR.MANIFEST_PATHS)
-        before = tuple((path.exists(), path.read_bytes() if path.exists() else None) for path in destinations)
+        snapshot = lambda path: (
+            path.exists(),
+            GENERATOR.read_regular_file_once(path, maximum_bytes=4 * 1024 * 1024) if path.exists() else None,
+        )
+        before = tuple(snapshot(path) for path in destinations)
         with self.assertRaises(GENERATOR.GenerationError):
-            GENERATOR.check_manifests(REPOSITORY_ROOT, self.state)
-        after = tuple((path.exists(), path.read_bytes() if path.exists() else None) for path in destinations)
+            GENERATOR.check_manifests(REPOSITORY_ROOT, SAMPLE_STATE)
+        after = tuple(snapshot(path) for path in destinations)
         self.assertEqual(after, before)
 
     def test_seed_review_is_complete_deterministic_and_binds_the_normalized_digest(self) -> None:
-        first = GENERATOR.render_seed_review(self.state)
-        self.assertEqual(first, GENERATOR.render_seed_review(self.state))
-        self.assertIn(f"normalized_sha256\t{self.state['entries_sha256']}\n".encode("ascii"), first)
+        first = GENERATOR.render_seed_review(SAMPLE_STATE)
+        self.assertEqual(first, GENERATOR.render_seed_review(SAMPLE_STATE))
+        self.assertIn(f"normalized_sha256\t{SAMPLE_STATE['entries_sha256']}\n".encode("ascii"), first)
         rows = [line for line in first.splitlines() if line.startswith(b"row\t")]
-        self.assertEqual(len(rows), len(self.state["blobs"]))
+        self.assertEqual(len(rows), len(SAMPLE_STATE["blobs"]))
         # Preapproval intentionally has no literal complete-row count/digest oracle.
 
     def test_secure_reader_rejects_oversize_symlink_and_final_identity_change(self) -> None:
         with tempfile.TemporaryDirectory(prefix="pontius-task3-reader-") as directory:
             root = Path(directory)
             regular = root / "regular.bin"
             regular.write_bytes(b"evidence")
             self.assertEqual(GENERATOR.read_regular_file_once(regular, maximum_bytes=8), b"evidence")
             with self.assertRaises(GENERATOR.GenerationError):
                 GENERATOR.read_regular_file_once(regular, maximum_bytes=7)
             link = root / "link.bin"
             try:
                 link.symlink_to(regular)
             except OSError:
                 link = None
             if link is not None:
                 with self.assertRaises(GENERATOR.GenerationError):
                     GENERATOR.read_regular_file_once(link, maximum_bytes=8)
-            original_lstat = os.lstat
-            before = original_lstat(regular)
-
-            class ChangedStat:
-                def __init__(self, source: os.stat_result) -> None:
-                    for name in dir(source):
-                        if name.startswith("st_"):
-                            try:
-                                setattr(self, name, getattr(source, name))
-                            except AttributeError:
-                                pass
-                    self.st_size = source.st_size + 1
-
-            with mock.patch.object(GENERATOR.os, "lstat", side_effect=[before, ChangedStat(before)]):
+            identity = GENERATOR._path_handle_identity(os.lstat(regular))
+            changed = (*identity[:-1], identity[-1] + 1)
+            with mock.patch.object(
+                GENERATOR, "_path_handle_identity",
+                side_effect=[identity, identity, changed, identity],
+            ):
+                with self.assertRaises(GENERATOR.GenerationError):
+                    GENERATOR.read_regular_file_once(regular, maximum_bytes=8)
+            with mock.patch.object(GENERATOR, "_path_handle_identity", side_effect=[identity, changed]):
+                with self.assertRaises(GENERATOR.GenerationError):
+                    GENERATOR.read_regular_file_once(regular, maximum_bytes=8)
+            handle_identity = GENERATOR._identity(os.lstat(regular))
+            with mock.patch.object(GENERATOR, "_identity", side_effect=[handle_identity, (*handle_identity[:-1], handle_identity[-1] + 1)]):
                 with self.assertRaises(GENERATOR.GenerationError):
                     GENERATOR.read_regular_file_once(regular, maximum_bytes=8)
 
+    def test_secure_reader_factory_rejects_link_components_and_reads_once(self) -> None:
+        reader = GENERATOR.tool_secure_reader_factory()
+        self.assertIs(reader.read_regular_once.__self__, reader)
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-reader-factory-") as directory:
+            root = Path(directory)
+            regular = root / "regular.bin"
+            regular.write_bytes(b"evidence")
+            with mock.patch.object(GENERATOR.os, "read", wraps=os.read) as read_call:
+                self.assertEqual(reader.read_regular_once(regular, maximum_bytes=8), b"evidence")
+                self.assertEqual(read_call.call_count, 1)
+            linked_parent = root / "linked-parent"
+            actual_parent = root / "actual-parent"
+            actual_parent.mkdir()
+            (actual_parent / "child.bin").write_bytes(b"evidence")
+            try:
+                linked_parent.symlink_to(actual_parent, target_is_directory=True)
+            except OSError:
+                linked_parent = None
+            if linked_parent is not None:
+                with self.assertRaises(GENERATOR.GenerationError):
+                    reader.read_regular_once(linked_parent / "child.bin", maximum_bytes=8)
+
+    def test_selected_class_scope_excludes_other_classes_and_broad_literals(self) -> None:
+        source = '''
+from pontius import selected_owner, unrelated_owner
+CONFIG = "experiments/configs/selected.json"
+UNRELATED = "artifacts/work_preflight/unrelated.json"
+class Selected:
+    owner = selected_owner
+    config = CONFIG
+class Other:
+    owner = unrelated_owner
+    artifact = UNRELATED
+    test = "tests/unrelated.py"
+'''
+        tracked = {
+            "src/pontius/__init__.py", "src/pontius/selected_owner.py",
+            "src/pontius/unrelated_owner.py", "experiments/configs/selected.json",
+            "artifacts/work_preflight/unrelated.json", "tests/unrelated.py",
+        }
+        scope = GENERATOR._selected_class_scope(ast.parse(source), "Selected")
+        reached = GENERATOR._import_paths(scope, "tests/selected.py", tracked)
+        reached |= GENERATOR._literal_paths(scope, source, tracked)
+        self.assertIn("src/pontius/selected_owner.py", reached)
+        self.assertIn("experiments/configs/selected.json", reached)
+        self.assertNotIn("src/pontius/unrelated_owner.py", reached)
+        self.assertNotIn("artifacts/work_preflight/unrelated.json", reached)
+        self.assertNotIn("tests/unrelated.py", reached)
+
+    def test_phase_boundary_seeds_selected_class_named_modules_without_transitive_walk(self) -> None:
+        class Git:
+            def tracked_paths(self, commit: str) -> tuple[str, ...]:
+                return (
+                    "tests/selected.py", "docs/decisions/ADR-1.md",
+                    "src/pontius/__init__.py", "src/pontius/owner.py",
+                    "src/pontius/transitive.py",
+                )
+            def show_blob(self, commit: str, path: str) -> bytes:
+                blobs = {
+                    "tests/selected.py": b"from pontius import owner\nclass Selected:\n    subject = owner\n",
+                    "src/pontius/owner.py": b"from pontius import transitive\n",
+                }
+                return blobs[path]
+        phase = {
+            "commit": "1" * 40, "selected_test": "tests/selected.py",
+            "selected_class": "Selected", "decision_path": "docs/decisions/ADR-1.md",
+        }
+        self.assertEqual(
+            GENERATOR._phase_paths(Git(), phase),
+            ("docs/decisions/ADR-1.md", "src/pontius/__init__.py", "src/pontius/owner.py", "tests/selected.py"),
+        )
+
+    def test_import_forms_resolve_package_submodules_and_relative_submodules(self) -> None:
+        tracked = {
+            "src/pontius/__init__.py", "src/pontius/foo.py",
+            "src/pontius/pkg/__init__.py", "src/pontius/pkg/bar.py",
+        }
+        absolute = GENERATOR._import_paths(ast.parse("from pontius import foo"), "tests/t.py", tracked)
+        relative = GENERATOR._import_paths(ast.parse("from . import bar"), "src/pontius/pkg/owner.py", tracked)
+        self.assertEqual(absolute, {"src/pontius/__init__.py", "src/pontius/foo.py"})
+        self.assertEqual(relative, {"src/pontius/pkg/__init__.py", "src/pontius/pkg/bar.py"})
+
+    def test_dynamic_dash_c_programs_are_exact_and_fail_closed(self) -> None:
+        tracked = {"src/pontius/runner.py"}
+        direct = ast.parse("subprocess.run([python, '-c', \"from pontius import runner\"])")
+        named = ast.parse("program = f\"from pontius import runner; value={VALUE!r}\"\nsubprocess.run([python, '-c', program])")
+        self.assertEqual(GENERATOR._dynamic_program_imports(direct, "tests/t.py", tracked), tracked)
+        self.assertEqual(GENERATOR._dynamic_program_imports(named, "tests/t.py", tracked), tracked)
+        for source in (
+            "subprocess.run([python, '-c', make_program()])",
+            "program = 'from pontius import ' + name\nsubprocess.run([python, '-c', program])",
+            "subprocess.run([python, '-c', 'from pontius import'])",
+            "subprocess.run([python, '-c', 'import pontius.missing'])",
+        ):
+            with self.subTest(source=source), self.assertRaises(GENERATOR.GenerationError):
+                GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked)
+
+    def test_historical_identity_collisions_fail_closed(self) -> None:
+        rows: list[dict[str, object]] = []
+        identities: set[tuple[str, str]] = set()
+        GENERATOR._append_unique_row(rows, identities, SAMPLE_ROW)
+        with self.assertRaises(GENERATOR.GenerationError):
+            GENERATOR._append_unique_row(rows, identities, dict(SAMPLE_ROW))
+
+    def test_absent_check_and_invalid_write_approval_do_not_derive(self) -> None:
+        with mock.patch.object(GENERATOR, "derive_manifest_state", side_effect=AssertionError("walked")):
+            self.assertEqual(GENERATOR.main([]), 2)
+            self.assertEqual(GENERATOR.main(["--write"]), 2)
+            self.assertEqual(GENERATOR.main(["--write", "--approved-seed-sha256", "A" * 64]), 2)
+
+    def test_emit_seed_review_validates_output_before_derivation(self) -> None:
+        with mock.patch.object(GENERATOR, "derive_manifest_state", side_effect=AssertionError("walked")):
+            self.assertEqual(GENERATOR.main(["--emit-seed-review", "relative.txt"]), 2)
+            self.assertEqual(GENERATOR.main(["--emit-seed-review", str(REPOSITORY_ROOT / "review.txt")]), 2)
+
+    def test_manifest_and_seed_review_destinations_reject_nonregular_targets(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-destinations-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            (root / GENERATOR.MANIFEST_PATHS[0]).mkdir()
+            with self.assertRaises(GENERATOR.GenerationError):
+                GENERATOR._verified_destinations(root)
+            output = root / "seed-review.txt"
+            output.mkdir()
+            with self.assertRaises(GENERATOR.GenerationError):
+                GENERATOR._validated_seed_review_output(REPOSITORY_ROOT, output)
+
+    def test_git_cache_revalidates_executable_and_bounded_runner_failures(self) -> None:
+        git = object.__new__(GENERATOR._Git)
+        git.root = REPOSITORY_ROOT
+        git.executable = GENERATOR.GIT_EXECUTABLE
+        git.executable_identity = GENERATOR._identity(os.lstat(git.executable))
+        git.environment = GENERATOR.git_environment(Path(tempfile.gettempdir()).resolve())
+        git._cache = {("cached",): b"value"}
+        with mock.patch.object(GENERATOR, "_validated_bound_executable", side_effect=GENERATOR.GenerationError("replaced")):
+            with self.assertRaises(GENERATOR.GenerationError):
+                git._run(("cached",), maximum_stdout=8)
+        with mock.patch.object(GENERATOR, "_validated_bound_executable", return_value=(git.executable, git.executable_identity)):
+            git._cache = {("cached",): b"12345"}
+            with self.assertRaises(GENERATOR.GenerationError):
+                git._run(("cached",), maximum_stdout=4)
+
+        class Process:
+            def __init__(self, stdout: bytes, stderr: bytes, code: int = 0, timeout: bool = False) -> None:
+                self.stdout, self.stderr = io.BytesIO(stdout), io.BytesIO(stderr)
+                self.returncode, self.timeout = code, timeout
+                self.killed = False
+            def wait(self, timeout: float | None = None) -> int:
+                if self.timeout and not self.killed:
+                    raise GENERATOR.subprocess.TimeoutExpired("git", timeout)
+                return self.returncode
+            def kill(self) -> None:
+                self.killed = True
+            def poll(self) -> int | None:
+                return self.returncode if not self.timeout or self.killed else None
+
+        for name, process, stdout_cap, stderr_cap in (
+            ("stdout", Process(b"12345", b""), 4, 4),
+            ("stderr", Process(b"", b"12345"), 4, 4),
+            ("timeout", Process(b"", b"", timeout=True), 4, 4),
+            ("nonzero", Process(b"", b"bad", code=1), 4, 4),
+        ):
+            with self.subTest(name=name), self.assertRaises(GENERATOR.GenerationError):
+                GENERATOR._collect_bounded_process(process, command="git", stdout_limit=stdout_cap, stderr_limit=stderr_cap, timeout=0.01)
+
+        successful = Process(b"ok", b"")
+        git._cache = {}
+        with mock.patch.object(GENERATOR, "_validated_bound_executable", return_value=(git.executable, git.executable_identity)), mock.patch.object(
+            GENERATOR.subprocess, "Popen", return_value=successful
+        ) as popen:
+            self.assertEqual(git._run(("show", "commit:path", "--"), maximum_stdout=4), b"ok")
+        positional, keyword = popen.call_args
+        self.assertEqual(positional[0], [str(git.executable), "show", "commit:path", "--"])
+        self.assertEqual(keyword["cwd"], git.root)
+        self.assertIs(keyword["env"], git.environment)
+        self.assertIs(keyword["stdin"], GENERATOR.subprocess.DEVNULL)
+        self.assertFalse(keyword["shell"])
+        with mock.patch.object(git, "_run", return_value=b"not-an-oid\n"):
+            with self.assertRaises(GENERATOR.GenerationError):
+                git._oid(("rev-parse", "bad"))
+
     def test_git_environment_is_fresh_literal_and_replacement_disabled(self) -> None:
         with tempfile.TemporaryDirectory(prefix="pontius-task3-git-home-") as directory:
             environment = GENERATOR.git_environment(Path(directory))
         git_values = {key: value for key, value in environment.items() if key.upper().startswith("GIT_")}
         self.assertEqual(git_values, {
             "GIT_CONFIG_GLOBAL": "NUL" if os.name == "nt" else "/dev/null",
             "GIT_CONFIG_NOSYSTEM": "1", "GIT_LITERAL_PATHSPECS": "1", "GIT_NO_REPLACE_OBJECTS": "1",
         })
 
 
diff --git a/tests/test_evidence_manifests.py b/tests/test_evidence_manifests.py
index 249ca8f..deb88bd 100644
--- a/tests/test_evidence_manifests.py
+++ b/tests/test_evidence_manifests.py
@@ -174,20 +174,28 @@ def _retained_manifest(*, reverse: bool = False, **overrides: object) -> bytes:
     chunks = [_toml_mapping(dict(items))]
     for label, identity in identities.items():
         chunks.append(f"[{label}]\n" + _toml_mapping(identity))
     return ("\n\n".join(chunks) + "\n").encode("utf-8")
 
 
 class EvidenceManifestTests(unittest.TestCase):
     def _source(self, name: str) -> Path:
         return ROOT / "evidence" / name
 
+    def _assert_both_reject(self, kind: str, raw: bytes, parser: object, source_name: str) -> None:
+        with self.assertRaises((EvidenceConfigurationError, EvidenceIntegrityError)):
+            parser(raw, source_path=self._source(source_name), repository_root=ROOT)
+        with self.assertRaises(_GENERATOR.GenerationError):
+            _GENERATOR.parse_manifest_bytes(
+                kind, raw, source_path=self._source(source_name), repository_root=ROOT
+            )
+
     def test_parses_each_strict_manifest_schema(self) -> None:
         files = parse_sealed_current_files_manifest(_files_manifest(), source_path=self._source("files.toml"), repository_root=ROOT)
         absences = parse_sealed_current_absences_manifest(_absences_manifest(), source_path=self._source("absences.toml"), repository_root=ROOT)
         historical = parse_historical_blobs_manifest(_historical_manifest(), source_path=self._source("historical.toml"), repository_root=ROOT)
         retained = parse_retained_v7_manifest(_retained_manifest(), source_path=self._source("retained.toml"), repository_root=ROOT)
         self.assertEqual(files.files[0].relative_path, "src/current.py")
         self.assertEqual(absences.absences[0].relative_path, "src/absent.py")
         self.assertEqual(historical.blobs[0].relative_path, "src/history.py")
         self.assertEqual(retained.manifest.terminal, "retained")
 
@@ -197,22 +205,22 @@ class EvidenceManifestTests(unittest.TestCase):
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
-            with self.subTest(name=name), self.assertRaises(EvidenceConfigurationError):
-                parse_sealed_current_files_manifest(raw, source_path=self._source("files.toml"), repository_root=ROOT)
+            with self.subTest(name=name):
+                self._assert_both_reject("sealed-current-files", raw, parse_sealed_current_files_manifest, "files.toml")
 
     def test_each_schema_rejects_its_applicable_malformed_scalar_path_count_and_digest_fields(self) -> None:
         # Files, absences, and historical blobs declare no boolean fields;
         # absences declares no digest. Retained-v7 has no collection-backed
         # declared count, so a count disagreement is not an applicable
         # construct for it.
         cases = (
             ("files-string-entry-length", _files_manifest(entry={"byte_length": "7"}), parse_sealed_current_files_manifest, "files.toml"),
             ("files-boolean-entry-length", _files_manifest(entry={"byte_length": True}), parse_sealed_current_files_manifest, "files.toml"),
             ("files-uppercase-entry-digest", _files_manifest(entry={"raw_sha256": SHA256.upper()}), parse_sealed_current_files_manifest, "files.toml"),
@@ -250,61 +258,121 @@ class EvidenceManifestTests(unittest.TestCase):
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
-            with self.subTest(name=name), self.assertRaises(EvidenceConfigurationError):
-                parser(raw, source_path=self._source(source_name), repository_root=ROOT)
+            kind = {
+                "files.toml": "sealed-current-files", "absences.toml": "sealed-current-absences",
+                "historical.toml": "historical-blobs", "retained.toml": "retained-v7",
+            }[source_name]
+            with self.subTest(name=name):
+                self._assert_both_reject(kind, raw, parser, source_name)
 
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
-            with self.subTest(name=name), self.assertRaises(EvidenceConfigurationError):
-                parser(raw, source_path=self._source(source_name), repository_root=ROOT)
+            kind = {
+                "files.toml": "sealed-current-files", "absences.toml": "sealed-current-absences",
+                "historical.toml": "historical-blobs", "retained.toml": "retained-v7",
+            }[source_name]
+            with self.subTest(name=name):
+                self._assert_both_reject(kind, raw, parser, source_name)
 
     def test_toml_syntax_and_duplicate_keys_are_configuration_errors_with_cause(self) -> None:
         raw = _files_manifest().replace(b"entry_count = 1", b"entry_count = 1\nentry_count = 1")
         with self.assertRaises(EvidenceConfigurationError) as raised:
             parse_sealed_current_files_manifest(raw, source_path=self._source("files.toml"), repository_root=ROOT)
         self.assertEqual(raised.exception.code, "manifest_toml_invalid")
         self.assertIsNotNone(raised.exception.__cause__)
+        with self.assertRaises(_GENERATOR.GenerationError):
+            _GENERATOR.parse_manifest_bytes("sealed-current-files", raw, source_path=self._source("files.toml"), repository_root=ROOT)
 
     def test_duplicate_toml_table_is_a_configuration_error(self) -> None:
         raw = _retained_manifest() + b"\n[result]\nrelative_path = \"other.json\"\nbyte_length = 1\nraw_sha256 = \"" + SHA256.encode() + b"\"\nrole = \"result\"\n"
         with self.assertRaises(EvidenceConfigurationError) as raised:
             parse_retained_v7_manifest(raw, source_path=self._source("retained.toml"), repository_root=ROOT)
         self.assertEqual(raised.exception.code, "manifest_toml_invalid")
+        with self.assertRaises(_GENERATOR.GenerationError):
+            _GENERATOR.parse_manifest_bytes("retained-v7", raw, source_path=self._source("retained.toml"), repository_root=ROOT)
 
     def test_historical_manifest_rejects_duplicate_commit_path_counts_and_digest_disagreement(self) -> None:
         duplicate = _blob_records() * 2
         cases = (
             ("duplicate-identity", _historical_manifest(blobs=duplicate, entry_count=2)),
             ("count", _historical_manifest(entry_count=2)),
             ("digest", _historical_manifest(entries_sha256="c" * 64)),
         )
         for name, raw in cases:
-            with self.subTest(name=name), self.assertRaises((EvidenceConfigurationError, EvidenceIntegrityError)):
-                parse_historical_blobs_manifest(raw, source_path=self._source("historical.toml"), repository_root=ROOT)
+            with self.subTest(name=name):
+                self._assert_both_reject("historical-blobs", raw, parse_historical_blobs_manifest, "historical.toml")
+
+    def test_every_declared_field_is_independently_type_checked_by_both_parsers(self) -> None:
+        files_root = ("schema_version", "baseline_commit", "entry_count")
+        files_entry = ("relative_path", "byte_length", "raw_sha256", "role", "governing_decision", "owner")
+        for field in files_root:
+            value = True if field == "entry_count" else 7
+            with self.subTest(kind="files-root", field=field):
+                self._assert_both_reject("sealed-current-files", _files_manifest(**{field: value}), parse_sealed_current_files_manifest, "files.toml")
+        for field in files_entry:
+            value = True if field == "byte_length" else 7
+            with self.subTest(kind="files-entry", field=field):
+                self._assert_both_reject("sealed-current-files", _files_manifest(entry={field: value}), parse_sealed_current_files_manifest, "files.toml")
+
+        absences_root = ("schema_version", "baseline_commit", "entry_count")
+        absences_entry = ("relative_path", "role", "governing_decision", "owner")
+        for field in absences_root:
+            value = True if field == "entry_count" else 7
+            with self.subTest(kind="absences-root", field=field):
+                self._assert_both_reject("sealed-current-absences", _absences_manifest(**{field: value}), parse_sealed_current_absences_manifest, "absences.toml")
+        for field in absences_entry:
+            with self.subTest(kind="absences-entry", field=field):
+                self._assert_both_reject("sealed-current-absences", _absences_manifest(entry={field: 7}), parse_sealed_current_absences_manifest, "absences.toml")
+
+        historical_roots = ("schema_version", "baseline_commit", "snapshot_count", "entry_count", "entries_sha256", "approved_seed_sha256")
+        for field in historical_roots:
+            value = True if field in {"snapshot_count", "entry_count"} else 7
+            with self.subTest(kind="historical-root", field=field):
+                self._assert_both_reject("historical-blobs", _historical_manifest(**{field: value}), parse_historical_blobs_manifest, "historical.toml")
+        for field in ("phase", "commit", "root_tree_oid", "governing_decision"):
+            with self.subTest(kind="snapshot", field=field):
+                self._assert_both_reject("historical-blobs", _historical_manifest(snapshot={field: 7}), parse_historical_blobs_manifest, "historical.toml")
+        for field in ("commit", "relative_path", "git_blob_oid", "raw_sha256", "role", "phase", "governing_decision"):
+            blob = {**_blob_records()[0], field: 7}
+            with self.subTest(kind="blob", field=field):
+                self._assert_both_reject("historical-blobs", _historical_manifest(blobs=[blob]), parse_historical_blobs_manifest, "historical.toml")
+
+        retained = _retained_mapping()
+        for field, original in retained.items():
+            replacement = 1 if type(original) in (str, bool, list) else True
+            with self.subTest(kind="retained", field=field):
+                self._assert_both_reject("retained-v7", _retained_manifest(**{field: replacement}), parse_retained_v7_manifest, "retained.toml")
+        for table in ("result", "attempt", "consumed_launch"):
+            base = {"relative_path": "a", "byte_length": 1, "raw_sha256": SHA256, "role": "a"}
+            for field, original in base.items():
+                replacement = True if type(original) is int else 7
+                identities = {table: {**base, field: replacement}}
+                with self.subTest(kind=table, field=field):
+                    self._assert_both_reject("retained-v7", _retained_manifest(identities=identities), parse_retained_v7_manifest, "retained.toml")
 
     def test_current_boundary_rejects_overlap_owner_duplicates_and_baseline_disagreement(self) -> None:
         files = parse_sealed_current_files_manifest(_files_manifest(), source_path=self._source("files.toml"), repository_root=ROOT)
         overlap = parse_sealed_current_absences_manifest(_absences_manifest(entry={"relative_path": "src/current.py"}), source_path=self._source("absences.toml"), repository_root=ROOT)
         changed_baseline = parse_sealed_current_absences_manifest(_absences_manifest(baseline_commit="c" * 40), source_path=self._source("absences.toml"), repository_root=ROOT)
         duplicate_owner = parse_sealed_current_files_manifest(
             _files_manifest(entry_count=2) + b"\n[[files]]\nrelative_path = \"src/current.py\"\nbyte_length = 7\nraw_sha256 = \"" + SHA256.encode() + b"\"\nrole = \"source\"\ngoverning_decision = \"ADR-1\"\nowner = \"owner-a\"\n",
             source_path=self._source("files.toml"), repository_root=ROOT,
         )
         for name, left, right in (("overlap", files, overlap), ("baseline", files, changed_baseline), ("owner", duplicate_owner, parse_sealed_current_absences_manifest(_absences_manifest(), source_path=self._source("absences.toml"), repository_root=ROOT))):
diff --git a/tools/generate_evidence_manifests.py b/tools/generate_evidence_manifests.py
index 741daab..7b2cb96 100644
--- a/tools/generate_evidence_manifests.py
+++ b/tools/generate_evidence_manifests.py
@@ -10,20 +10,22 @@ import ast
 from collections.abc import Mapping, Sequence
 from hashlib import sha256
 import json
 import os
 from pathlib import Path, PurePosixPath, PureWindowsPath
 import re
 import stat
 import subprocess
 import sys
 import tempfile
+import threading
+import time
 import tomllib
 from typing import Any
 import uuid
 
 
 BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
 GIT_EXECUTABLE = Path("C:/Program Files/Git/cmd/git.exe")
 MANIFEST_PATHS = (
     "docs/architecture/sealed-current-files.toml",
     "docs/architecture/sealed-current-absences.toml",
@@ -126,21 +128,20 @@ RETAINED_V7 = {
         "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-pending.json",
     ),
     "expected_null_claim_paths": EXPECTED_NULL_CLAIM_PATHS,
     "result": {key: value for key, value in CURRENT_FILE_ENTRIES[3].items() if key in {"relative_path", "byte_length", "raw_sha256", "role"}},
     "attempt": {key: value for key, value in CURRENT_FILE_ENTRIES[4].items() if key in {"relative_path", "byte_length", "raw_sha256", "role"}},
     "consumed_launch": {key: value for key, value in CURRENT_FILE_ENTRIES[5].items() if key in {"relative_path", "byte_length", "raw_sha256", "role"}},
 }
 
 _HEX40 = re.compile(r"[0-9a-f]{40}\Z")
 _HEX64 = re.compile(r"[0-9a-f]{64}\Z")
-_PATH_LITERAL = re.compile(r"(?:src/pontius|tests|experiments/configs|docs/decisions|artifacts/work_preflight)/[A-Za-z0-9_./-]+")
 _REPARSE_ATTRIBUTE = 0x400
 
 
 class GenerationError(RuntimeError):
     """A fail-closed generator error."""
 
 
 def canonical_semantic_bytes(value: object) -> bytes:
     return json.dumps(
         _normalize_semantic(value, "$"),
@@ -195,81 +196,105 @@ def _path_handle_identity(info: Any) -> tuple[int, ...]:
         int(getattr(info, "st_reparse_tag", 0)),
     )
 
 
 def _is_reparse(info: Any) -> bool:
     return bool(int(getattr(info, "st_file_attributes", 0)) & _REPARSE_ATTRIBUTE) or bool(
         int(getattr(info, "st_reparse_tag", 0))
     )
 
 
-def read_regular_file_once(path: Path, *, maximum_bytes: int) -> bytes:
+class _ToolSecureReader:
+    """Reusable tool-local secure-reader seam for the future active reader."""
+
+    def read_regular_once(self, path: Path, *, maximum_bytes: int) -> bytes:
+        return _read_regular_file_once(path, maximum_bytes=maximum_bytes)
+
+
+def tool_secure_reader_factory() -> _ToolSecureReader:
+    return _ToolSecureReader()
+
+
+def _read_regular_file_once(path: Path, *, maximum_bytes: int) -> bytes:
     """Read one bounded snapshot from a regular nonlink/nonreparse path."""
     if (
         type(maximum_bytes) is not int
         or maximum_bytes < 0
         or not isinstance(path, Path)
         or not path.is_absolute()
     ):
         raise GenerationError("secure read arguments are invalid")
+    for component in reversed(path.parents):
+        if component == component.parent:
+            continue
+        try:
+            component_info = os.lstat(component)
+        except OSError as error:
+            raise GenerationError(f"evidence path component cannot be inspected: {component}") from error
+        if stat.S_ISLNK(component_info.st_mode) or _is_reparse(component_info):
+            raise GenerationError(f"evidence path has a link or reparse component: {component}")
     try:
         before_path = os.lstat(path)
     except OSError as error:
         raise GenerationError(f"evidence path cannot be inspected: {path}") from error
     if (
         stat.S_ISLNK(before_path.st_mode)
         or _is_reparse(before_path)
         or not stat.S_ISREG(before_path.st_mode)
     ):
         raise GenerationError(f"evidence path is not a regular nonreparse file: {path}")
+    if before_path.st_size > maximum_bytes:
+        raise GenerationError(f"evidence file exceeds its bounded read: {path}")
     flags = (
         os.O_RDONLY
         | getattr(os, "O_BINARY", 0)
         | getattr(os, "O_CLOEXEC", 0)
         | getattr(os, "O_NOINHERIT", 0)
     )
     if hasattr(os, "O_NOFOLLOW"):
         flags |= os.O_NOFOLLOW
     try:
         descriptor = os.open(path, flags)
     except OSError as error:
         raise GenerationError(f"evidence path cannot be opened without following links: {path}") from error
     try:
         before_handle = os.fstat(descriptor)
         if not stat.S_ISREG(before_handle.st_mode) or _is_reparse(before_handle):
             raise GenerationError(f"opened evidence handle is not regular: {path}")
         if _path_handle_identity(before_path) != _path_handle_identity(before_handle):
             raise GenerationError(f"evidence path changed while opening: {path}")
-        with os.fdopen(descriptor, "rb", closefd=True) as stream:
-            descriptor = -1
-            raw = stream.read(maximum_bytes + 1)
-            after_handle = os.fstat(stream.fileno())
+        raw = os.read(descriptor, maximum_bytes + 1)
+        after_handle = os.fstat(descriptor)
         if len(raw) > maximum_bytes:
             raise GenerationError(f"evidence file exceeds its bounded read: {path}")
         if len(raw) != before_handle.st_size or _identity(before_handle) != _identity(after_handle):
             raise GenerationError(f"opened evidence file changed during its single read: {path}")
     finally:
         if descriptor >= 0:
             os.close(descriptor)
     try:
         after_path = os.lstat(path)
     except OSError as error:
         raise GenerationError(f"evidence path disappeared after reading: {path}") from error
     if (
         stat.S_ISLNK(after_path.st_mode)
         or _is_reparse(after_path)
         or _path_handle_identity(after_path) != _path_handle_identity(after_handle)
     ):
         raise GenerationError(f"evidence path identity changed after reading: {path}")
     return raw
 
 
+def read_regular_file_once(path: Path, *, maximum_bytes: int) -> bytes:
+    return tool_secure_reader_factory().read_regular_once(path, maximum_bytes=maximum_bytes)
+
+
 def git_environment(private_home: Path) -> dict[str, str]:
     if not isinstance(private_home, Path) or not private_home.is_absolute():
         raise GenerationError("Git private home must be absolute")
     allowed = ("SystemRoot", "WINDIR", "ComSpec", "PATHEXT", "TEMP", "TMP", "TMPDIR")
     source = {key.casefold(): value for key, value in os.environ.items()}
     environment = {key: source[key.casefold()] for key in allowed if key.casefold() in source}
     environment["HOME"] = str(private_home)
     environment["USERPROFILE"] = str(private_home)
     system_root = Path(os.environ.get("SystemRoot", "C:/Windows"))
     environment["PATH"] = os.pathsep.join((str(GIT_EXECUTABLE.parent), str(system_root / "System32")))
@@ -277,80 +302,135 @@ def git_environment(private_home: Path) -> dict[str, str]:
         {
             "GIT_CONFIG_NOSYSTEM": "1",
             "GIT_CONFIG_GLOBAL": "NUL" if os.name == "nt" else "/dev/null",
             "GIT_NO_REPLACE_OBJECTS": "1",
             "GIT_LITERAL_PATHSPECS": "1",
         }
     )
     return environment
 
 
-def _validated_executable() -> tuple[Path, tuple[int, ...]]:
+def _validated_bound_executable(
+    executable: Path = GIT_EXECUTABLE, expected_identity: tuple[int, ...] | None = None
+) -> tuple[Path, tuple[int, ...]]:
     try:
-        resolved = GIT_EXECUTABLE.resolve(strict=True)
+        resolved = executable.resolve(strict=True)
     except OSError as error:
         raise GenerationError("the bound Git executable is unavailable") from error
-    if os.path.normcase(str(resolved)) != os.path.normcase(str(GIT_EXECUTABLE)):
+    if os.path.normcase(str(resolved)) != os.path.normcase(str(executable)):
         raise GenerationError("the bound Git executable resolved to a different identity")
     for component in (resolved, *resolved.parents[:-1]):
         info = os.lstat(component)
         if stat.S_ISLNK(info.st_mode) or _is_reparse(info):
             raise GenerationError("the bound Git executable has a link or reparse component")
     info = os.lstat(resolved)
     if not stat.S_ISREG(info.st_mode):
         raise GenerationError("the bound Git executable is not regular")
-    return resolved, _identity(info)
+    identity = _identity(info)
+    if expected_identity is not None and identity != expected_identity:
+        raise GenerationError("the bound Git executable identity changed")
+    return resolved, identity
+
+
+def _collect_bounded_process(
+    process: Any, *, command: str, stdout_limit: int, stderr_limit: int, timeout: float
+) -> tuple[bytes, bytes]:
+    """Drain a child concurrently while retaining at most each declared bound."""
+    outputs: dict[str, bytes] = {}
+    exceeded = threading.Event()
+
+    def drain(name: str, stream: Any, limit: int) -> None:
+        chunks: list[bytes] = []
+        remaining = limit
+        while True:
+            chunk = stream.read(min(65536, remaining + 1))
+            if not chunk:
+                break
+            if len(chunk) > remaining:
+                exceeded.set()
+                break
+            chunks.append(chunk)
+            remaining -= len(chunk)
+        outputs[name] = b"".join(chunks)
+
+    threads = (
+        threading.Thread(target=drain, args=("stdout", process.stdout, stdout_limit), daemon=True),
+        threading.Thread(target=drain, args=("stderr", process.stderr, stderr_limit), daemon=True),
+    )
+    for thread in threads:
+        thread.start()
+    deadline = time.monotonic() + timeout
+    timed_out = False
+    while True:
+        if exceeded.is_set():
+            process.kill()
+            break
+        remaining_time = deadline - time.monotonic()
+        if remaining_time <= 0:
+            timed_out = True
+            process.kill()
+            break
+        try:
+            process.wait(timeout=min(0.05, remaining_time))
+            break
+        except subprocess.TimeoutExpired:
+            continue
+    try:
+        process.wait(timeout=1.0)
+    except subprocess.TimeoutExpired:
+        process.kill()
+    for thread in threads:
+        thread.join(timeout=1.0)
+    process.stdout.close()
+    process.stderr.close()
+    if exceeded.is_set():
+        raise GenerationError(f"Git command output exceeded its bound: {command}")
+    if timed_out:
+        raise GenerationError(f"Git command timed out: {command}")
+    stdout = outputs.get("stdout", b"")
+    stderr = outputs.get("stderr", b"")
+    if process.returncode != 0:
+        detail = stderr.decode("utf-8", "replace").strip()[:500]
+        raise GenerationError(f"Git command failed ({command}): {detail}")
+    return stdout, stderr
 
 
 class _Git:
     def __init__(self, repository_root: Path, private_home: Path) -> None:
         self.root = repository_root.resolve(strict=True)
-        self.executable, self.executable_identity = _validated_executable()
+        self.executable, self.executable_identity = _validated_bound_executable()
         self.environment = git_environment(private_home)
         self._cache: dict[tuple[str, ...], bytes] = {}
 
     def _run(self, arguments: Sequence[str], *, maximum_stdout: int) -> bytes:
+        if type(maximum_stdout) is not int or maximum_stdout < 0 or not arguments:
+            raise GenerationError("Git command bounds are invalid")
         key = tuple(arguments)
+        _validated_bound_executable(self.executable, self.executable_identity)
         if key in self._cache:
-            return self._cache[key]
-        if _identity(os.lstat(self.executable)) != self.executable_identity:
-            raise GenerationError("the bound Git executable identity changed")
-        with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
-            try:
-                completed = subprocess.run(
-                    [str(self.executable), *arguments],
-                    cwd=self.root,
-                    env=self.environment,
-                    stdin=subprocess.DEVNULL,
-                    stdout=stdout_file,
-                    stderr=stderr_file,
-                    timeout=10.0,
-                    check=False,
-                    shell=False,
-                )
-            except subprocess.TimeoutExpired as error:
-                raise GenerationError(f"Git command timed out: {arguments[0]}") from error
-            if _identity(os.lstat(self.executable)) != self.executable_identity:
-                raise GenerationError("the bound Git executable identity changed during execution")
-            stdout_file.seek(0, os.SEEK_END)
-            stdout_size = stdout_file.tell()
-            stderr_file.seek(0, os.SEEK_END)
-            stderr_size = stderr_file.tell()
-            if stdout_size > maximum_stdout or stderr_size > 65536:
-                raise GenerationError(f"Git command output exceeded its bound: {arguments[0]}")
-            stdout_file.seek(0)
-            stderr_file.seek(0)
-            stdout = stdout_file.read(maximum_stdout + 1)
-            stderr = stderr_file.read(65537)
-        if completed.returncode != 0:
-            detail = stderr.decode("utf-8", "replace").strip()[:500]
-            raise GenerationError(f"Git command failed ({arguments[0]}): {detail}")
+            cached = self._cache[key]
+            if len(cached) > maximum_stdout:
+                raise GenerationError(f"cached Git output exceeded its bound: {arguments[0]}")
+            return cached
+        try:
+            process = subprocess.Popen(
+                [str(self.executable), *arguments], cwd=self.root, env=self.environment,
+                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
+                shell=False,
+            )
+        except OSError as error:
+            raise GenerationError(f"Git command could not start: {arguments[0]}") from error
+        stdout, _ = _collect_bounded_process(
+            process, command=arguments[0], stdout_limit=maximum_stdout,
+            stderr_limit=65536, timeout=10.0,
+        )
+        _validated_bound_executable(self.executable, self.executable_identity)
         self._cache[key] = stdout
         return stdout
 
     def root_tree_oid(self, commit: str) -> str:
         return self._oid(("rev-parse", "--verify", f"{commit}^{{tree}}"))
 
     def tracked_paths(self, commit: str) -> tuple[str, ...]:
         raw = self._run(
             ("ls-tree", "-r", "-z", "--name-only", commit, "--"),
             maximum_stdout=4 * 1024 * 1024,
@@ -449,85 +529,193 @@ def _import_paths(tree: ast.AST, current_path: str, tracked: set[str]) -> set[st
             if node.level:
                 package_parts = current_package.split(".") if current_package else []
                 keep = max(0, len(package_parts) - node.level + 1)
                 prefix = package_parts[:keep]
                 if node.module:
                     prefix.extend(node.module.split("."))
                 base = ".".join(prefix)
             else:
                 base = node.module or ""
             modules.append(base)
-            if base == "pontius":
-                modules.extend(f"pontius.{alias.name}" for alias in node.names if alias.name != "*")
+            if base.startswith("pontius"):
+                modules.extend(f"{base}.{alias.name}" for alias in node.names if alias.name != "*")
         for module in modules:
             path = _module_path(module, tracked)
             if path is not None:
                 result.add(path)
-            elif module.startswith("pontius") and module != "pontius":
+            elif module.startswith("pontius") and module != "pontius" and not any(
+                isinstance(node, ast.ImportFrom)
+                and module.endswith("." + alias.name)
+                for alias in node.names
+                if alias.name != "*"
+            ):
                 raise GenerationError(f"unresolved local import {module!r} in {current_path}")
     return result
 
 
+def _bound_names(node: ast.stmt) -> set[str]:
+    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
+        return {node.name}
+    if isinstance(node, (ast.Import, ast.ImportFrom)):
+        return {alias.asname or alias.name.split(".")[0] for alias in node.names}
+    targets: list[ast.AST] = []
+    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
+        targets = list(node.targets) if isinstance(node, ast.Assign) else [node.target]
+    result: set[str] = set()
+    for target in targets:
+        for item in ast.walk(target):
+            if isinstance(item, ast.Name):
+                result.add(item.id)
+    return result
+
+
+def _loaded_names(node: ast.AST) -> set[str]:
+    return {
+        item.id for item in ast.walk(node)
+        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
+    }
+
+
+def _selected_class_scope(tree: ast.AST, selected_class: str) -> ast.Module:
+    if not isinstance(tree, ast.Module) or type(selected_class) is not str or not selected_class:
+        raise GenerationError("selected class scope arguments are invalid")
+    matches = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == selected_class]
+    if len(matches) != 1:
+        raise GenerationError(f"selected class is missing or ambiguous: {selected_class}")
+    bindings: dict[str, ast.stmt] = {}
+    for node in tree.body:
+        if node is matches[0]:
+            continue
+        for name in _bound_names(node):
+            if name in bindings:
+                raise GenerationError(f"module binding is ambiguous in selected-class scope: {name}")
+            bindings[name] = node
+    selected_nodes: list[ast.stmt] = [matches[0]]
+    pending = list(_loaded_names(matches[0]))
+    included: set[int] = {id(matches[0])}
+    required_import_bindings: dict[int, set[str]] = {}
+    while pending:
+        name = pending.pop()
+        node = bindings.get(name)
+        if node is None:
+            continue
+        if isinstance(node, (ast.Import, ast.ImportFrom)):
+            required_import_bindings.setdefault(id(node), set()).add(name)
+        if id(node) in included:
+            continue
+        included.add(id(node))
+        selected_nodes.append(node)
+        pending.extend(_loaded_names(node))
+    order = {id(node): index for index, node in enumerate(tree.body)}
+    selected_nodes.sort(key=lambda node: order[id(node)])
+    pruned: list[ast.stmt] = []
+    for node in selected_nodes:
+        if isinstance(node, (ast.Import, ast.ImportFrom)):
+            required = required_import_bindings[id(node)]
+            aliases = [
+                alias for alias in node.names
+                if (alias.asname or alias.name.split(".")[0]) in required
+            ]
+            if isinstance(node, ast.Import):
+                node = ast.Import(names=aliases)
+            else:
+                node = ast.ImportFrom(module=node.module, names=aliases, level=node.level)
+        pruned.append(node)
+    return ast.Module(body=pruned, type_ignores=[])
+
+
 def _slash_strings(node: ast.AST) -> list[str] | None:
     if isinstance(node, ast.Constant) and type(node.value) is str:
         return [node.value]
     if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
         left = _slash_strings(node.left)
         right = _slash_strings(node.right)
         if left is not None and right is not None:
             return [*left, *right]
     if isinstance(node, (ast.Name, ast.Attribute, ast.Subscript, ast.Call)):
         return []
     return None
 
 
 def _literal_paths(tree: ast.AST, text: str, tracked: set[str]) -> set[str]:
-    candidates: set[str] = set(_PATH_LITERAL.findall(text.replace("\\", "/")))
+    del text
+    candidates: set[str] = set()
     for node in ast.walk(tree):
         if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
             parts = _slash_strings(node)
             if parts:
                 normalized = "/".join(part.strip("/\\") for part in parts if part)
-                for prefix in ("src/", "tests/", "experiments/", "docs/", "artifacts/", "run_"):
+                for prefix in ("experiments/configs/", "docs/decisions/"):
                     position = normalized.find(prefix)
                     if position >= 0:
                         candidates.add(normalized[position:])
         if isinstance(node, ast.Constant) and type(node.value) is str:
             value = node.value.replace("\\", "/")
             if value in tracked:
                 candidates.add(value)
-    allowed = (
-        "src/pontius/",
-        "tests/",
-        "experiments/configs/",
-        "docs/decisions/",
-        "artifacts/work_preflight/",
-        "run_",
-    )
+    allowed = ("experiments/configs/", "docs/decisions/")
     return {_relative_path(path) for path in candidates if path in tracked and path.startswith(allowed)}
 
 
 def _dynamic_program_imports(tree: ast.AST, current_path: str, tracked: set[str]) -> set[str]:
-    result: set[str] = set()
+    bindings: dict[str, ast.AST] = {}
     for node in ast.walk(tree):
-        if (
-            not isinstance(node, ast.Constant)
-            or type(node.value) is not str
-            or "pontius" not in node.value
-            or "import" not in node.value
-        ):
-            continue
+        if isinstance(node, (ast.Assign, ast.AnnAssign)):
+            value = node.value
+            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
+            for target in targets:
+                if isinstance(target, ast.Name):
+                    bindings[target.id] = value
+
+    def program_text(node: ast.AST) -> str:
+        if isinstance(node, ast.Name) and node.id in bindings:
+            return program_text(bindings[node.id])
+        if isinstance(node, ast.Constant) and type(node.value) is str:
+            return node.value
+        if isinstance(node, ast.JoinedStr):
+            parts: list[str] = []
+            for value in node.values:
+                if isinstance(value, ast.Constant) and type(value.value) is str:
+                    parts.append(value.value)
+                elif isinstance(value, ast.FormattedValue):
+                    parts.append(repr("__pontius_dynamic_value__"))
+                else:
+                    raise GenerationError(f"dynamic -c program is not fixed: {current_path}")
+            return "".join(parts)
+        raise GenerationError(f"dynamic -c program is not a fixed literal: {current_path}")
+
+    result: set[str] = set()
+    programs: list[ast.AST] = []
+    for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
+        for argument in call.args:
+            if not isinstance(argument, (ast.List, ast.Tuple)):
+                continue
+            for index, item in enumerate(argument.elts[:-1]):
+                if isinstance(item, ast.Constant) and item.value == "-c":
+                    programs.append(argument.elts[index + 1])
+    for expression in programs:
+        source = program_text(expression)
         try:
-            program = ast.parse(node.value, filename=f"{current_path}::<dynamic-c>")
-        except SyntaxError:
-            continue
+            program = ast.parse(source, filename=f"{current_path}::<dynamic-c>")
+        except SyntaxError as error:
+            raise GenerationError(f"dynamic -c program cannot be parsed: {current_path}") from error
         result.update(_import_paths(program, current_path, tracked))
+        for call in (node for node in ast.walk(program) if isinstance(node, ast.Call)):
+            if (
+                isinstance(call.func, ast.Attribute) and call.func.attr == "import_module"
+                and call.args and isinstance(call.args[0], ast.Constant)
+                and type(call.args[0].value) is str and call.args[0].value.startswith("pontius")
+            ):
+                path = _module_path(call.args[0].value, tracked)
+                if path is None:
+                    raise GenerationError(f"unresolved dynamic local import {call.args[0].value!r} in {current_path}")
+                result.add(path)
     return result
 
 
 def _phase_paths(git: _Git, phase: Mapping[str, str]) -> tuple[str, ...]:
     commit = phase["commit"]
     tracked = set(git.tracked_paths(commit))
     selected_test = phase["selected_test"]
     decision_path = phase["decision_path"]
     for required in (selected_test, decision_path):
         if required not in tracked:
@@ -539,30 +727,29 @@ def _phase_paths(git: _Git, phase: Mapping[str, str]) -> tuple[str, ...]:
         path = pending.pop()
         if path in parsed or not path.endswith(".py"):
             continue
         parsed.add(path)
         raw = git.show_blob(commit, path)
         try:
             text = raw.decode("utf-8")
             tree = ast.parse(text, filename=f"{commit}:{path}")
         except (UnicodeDecodeError, SyntaxError) as error:
             raise GenerationError(f"phase Python blob cannot be parsed: {commit}:{path}") from error
+        scoped_tree = _selected_class_scope(tree, str(phase["selected_class"])) if path == selected_test else tree
         reached = (
-            _import_paths(tree, path, tracked)
-            | _literal_paths(tree, text, tracked)
-            | _dynamic_program_imports(tree, path, tracked)
+            _import_paths(scoped_tree, path, tracked)
+            | _literal_paths(scoped_tree, text, tracked)
+            | _dynamic_program_imports(scoped_tree, path, tracked)
         )
         for candidate in sorted(reached):
             if candidate not in discovered:
                 discovered.add(candidate)
-                if candidate.startswith(("src/pontius/", "tests/", "run_")):
-                    pending.append(candidate)
     return tuple(sorted(discovered))
 
 
 def _historical_role(path: str, phase: Mapping[str, str]) -> str:
     if path == phase.get("selected_test"):
         return "selected_test"
     if path == phase.get("decision_path"):
         return "governing_decision"
     if path.startswith("src/pontius/"):
         return "source_dependency"
@@ -652,20 +839,30 @@ def _dependency_hashes(v7_raw: bytes) -> dict[str, str]:
 
 
 def historical_entries_sha256(rows: Sequence[Mapping[str, object]]) -> str:
     normalized = [
         dict(row)
         for row in sorted(rows, key=lambda item: (str(item["commit"]), str(item["relative_path"])))
     ]
     return semantic_sha256(normalized)
 
 
+def _append_unique_row(
+    rows: list[dict[str, object]], identities: set[tuple[str, str]], row: Mapping[str, object]
+) -> None:
+    identity = (str(row["commit"]), str(row["relative_path"]))
+    if identity in identities:
+        raise GenerationError(f"historical derivation collided at {identity}")
+    identities.add(identity)
+    rows.append(dict(row))
+
+
 def derive_manifest_state(repository_root: Path) -> dict[str, object]:
     if not isinstance(repository_root, Path) or not repository_root.is_absolute():
         raise GenerationError("repository root must be absolute")
     root = repository_root.resolve(strict=True)
     current_files, raw_by_path = _measure_current(root)
     with tempfile.TemporaryDirectory(prefix="pontius-evidence-git-home-") as home_text:
         git = _Git(root, Path(home_text).resolve())
         for snapshot in SNAPSHOTS:
             actual_tree = git.root_tree_oid(str(snapshot["commit"]))
             if actual_tree != snapshot["root_tree_oid"]:
@@ -675,59 +872,47 @@ def derive_manifest_state(repository_root: Path) -> dict[str, object]:
         for phase in EARLIER_PHASES:
             for path in _phase_paths(git, phase):
                 row = _row(
                     git,
                     commit=str(phase["commit"]),
                     relative_path=path,
                     role=_historical_role(path, phase),
                     phase=str(phase["phase"]),
                     decision=str(phase["governing_decision"]),
                 )
-                identity = (str(row["commit"]), str(row["relative_path"]))
-                if identity in identities:
-                    raise GenerationError(f"historical phase derivation collided at {identity}")
-                identities.add(identity)
-                rows.append(row)
+                _append_unique_row(rows, identities, row)
         v7_path = str(CURRENT_FILE_ENTRIES[3]["relative_path"])
         dependencies = _dependency_hashes(raw_by_path[v7_path])
         source_snapshot = SNAPSHOTS[9]
         for path in sorted(dependencies):
             row = _row(
                 git,
                 commit=str(source_snapshot["commit"]),
                 relative_path=path,
                 role="source_seal_dependency",
                 phase=str(source_snapshot["phase"]),
                 decision=str(source_snapshot["governing_decision"]),
             )
             if row["raw_sha256"] != dependencies[path]:
                 raise GenerationError(f"v7 source-seal dependency digest mismatch: {path}")
-            identity = (str(row["commit"]), str(row["relative_path"]))
-            if identity in identities:
-                raise GenerationError(f"historical source-seal collision at {identity}")
-            identities.add(identity)
-            rows.append(row)
+            _append_unique_row(rows, identities, row)
         authorization_snapshot = SNAPSHOTS[10]
         for path in V7_AUTHORIZATION_PATHS:
             row = _row(
                 git,
                 commit=str(authorization_snapshot["commit"]),
                 relative_path=path,
                 role="authorization_surface",
                 phase=str(authorization_snapshot["phase"]),
                 decision=str(authorization_snapshot["governing_decision"]),
             )
-            identity = (str(row["commit"]), str(row["relative_path"]))
-            if identity in identities:
-                raise GenerationError(f"historical authorization collision at {identity}")
-            identities.add(identity)
-            rows.append(row)
+            _append_unique_row(rows, identities, row)
     rows.sort(key=lambda item: (str(item["commit"]), str(item["relative_path"])))
     return {
         "current_files": current_files,
         "current_absences": [dict(entry) for entry in CURRENT_ABSENCE_ENTRIES],
         "snapshots": [dict(snapshot) for snapshot in SNAPSHOTS],
         "blobs": rows,
         "entries_sha256": historical_entries_sha256(rows),
     }
 
 
@@ -1194,31 +1379,36 @@ def _parse_retained(document: dict[str, object]) -> dict[str, object]:
     claim_values = _array(root["expected_null_claim_paths"], "expected_null_claim_paths")
     result["expected_null_claim_paths"] = [
         _string(value, "expected_null_claim_paths") for value in claim_values
     ]
     for field in ("result", "attempt", "consumed_launch"):
         result[field] = _parse_file_identity(root[field], field)
     return result
 
 
 def validate_approval_digest(supplied: str | None, expected: str) -> str:
-    if type(supplied) is not str or _HEX64.fullmatch(supplied) is None:
-        raise GenerationError(
-            "--write requires a lowercase 64-hex --approved-seed-sha256"
-        )
+    supplied = validate_approval_format(supplied)
     if supplied != expected:
         raise GenerationError(
             "the supplied approval digest does not match the freshly derived seed"
         )
     return supplied
 
 
+def validate_approval_format(supplied: str | None) -> str:
+    if type(supplied) is not str or _HEX64.fullmatch(supplied) is None:
+        raise GenerationError(
+            "--write requires a lowercase 64-hex --approved-seed-sha256"
+        )
+    return supplied
+
+
 def _verified_destinations(repository_root: Path) -> dict[str, Path]:
     if not repository_root.is_absolute():
         raise GenerationError("repository root must be absolute")
     root = repository_root.resolve(strict=True)
     architecture = (root / "docs" / "architecture").resolve(strict=True)
     result: dict[str, Path] = {}
     for relative in MANIFEST_PATHS:
         destination = root / relative
         if destination.parent.resolve(strict=True) != architecture:
             raise GenerationError(
@@ -1330,20 +1520,37 @@ def render_seed_review(state: Mapping[str, object]) -> bytes:
             )
         lines.append("row\t" + "\t".join(str(value) for value in values))
     return ("\n".join(lines) + "\n").encode("utf-8")
 
 
 def emit_seed_review(
     repository_root: Path,
     state: Mapping[str, object],
     output_path: Path,
 ) -> None:
+    output_path = _validated_seed_review_output(repository_root, output_path)
+    raw = render_seed_review(state)
+    candidate = output_path.parent / f".{output_path.name}.{uuid.uuid4().hex}.tmp"
+    try:
+        with candidate.open("xb") as stream:
+            stream.write(raw)
+            stream.flush()
+            os.fsync(stream.fileno())
+        os.replace(candidate, output_path)
+    finally:
+        try:
+            candidate.unlink()
+        except FileNotFoundError:
+            pass
+
+
+def _validated_seed_review_output(repository_root: Path, output_path: Path) -> Path:
     if not output_path.is_absolute():
         raise GenerationError("seed review output path must be absolute")
     repository = repository_root.resolve(strict=True)
     temporary_root = Path(tempfile.gettempdir()).resolve(strict=True)
     parent = output_path.parent.resolve(strict=True)
     resolved_output = output_path.resolve(strict=False)
     try:
         resolved_output.relative_to(temporary_root)
     except ValueError as error:
         raise GenerationError(
@@ -1362,33 +1569,35 @@ def emit_seed_review(
     if os.path.lexists(output_path):
         info = os.lstat(output_path)
         if (
             stat.S_ISLNK(info.st_mode)
             or _is_reparse(info)
             or not stat.S_ISREG(info.st_mode)
         ):
             raise GenerationError(
                 "seed review destination is not a regular nonreparse file"
             )
-    raw = render_seed_review(state)
-    candidate = output_path.parent / f".{output_path.name}.{uuid.uuid4().hex}.tmp"
+    return output_path
+
+
+def _preflight_check(repository_root: Path) -> None:
+    historical_path = repository_root / MANIFEST_PATHS[2]
     try:
-        with candidate.open("xb") as stream:
-            stream.write(raw)
-            stream.flush()
-            os.fsync(stream.fileno())
-        os.replace(candidate, output_path)
-    finally:
-        try:
-            candidate.unlink()
-        except FileNotFoundError:
-            pass
+        raw = read_regular_file_once(historical_path, maximum_bytes=4 * 1024 * 1024)
+    except GenerationError as error:
+        raise GenerationError(
+            "historical manifest is absent or unreadable; approval and --write are still required"
+        ) from error
+    parsed = parse_manifest_bytes(
+        "historical-blobs", raw, source_path=historical_path, repository_root=repository_root
+    )
+    validate_approval_format(str(parsed["approved_seed_sha256"]))
 
 
 def _arguments(argv: Sequence[str] | None) -> argparse.Namespace:
     parser = argparse.ArgumentParser(description=__doc__)
     commands = parser.add_mutually_exclusive_group()
     commands.add_argument(
         "--check",
         action="store_true",
         help="compare generated bytes without writing (default)",
     )
@@ -1404,20 +1613,27 @@ def _arguments(argv: Sequence[str] | None) -> argparse.Namespace:
     parsed = parser.parse_args(argv)
     if parsed.approved_seed_sha256 is not None and not parsed.write:
         parser.error("--approved-seed-sha256 is valid only with --write")
     return parsed
 
 
 def main(argv: Sequence[str] | None = None) -> int:
     arguments = _arguments(argv)
     repository_root = Path(__file__).resolve().parents[1]
     try:
+        if arguments.emit_seed_review is not None:
+            _validated_seed_review_output(repository_root, arguments.emit_seed_review)
+        elif arguments.write:
+            validate_approval_format(arguments.approved_seed_sha256)
+            _verified_destinations(repository_root)
+        else:
+            _preflight_check(repository_root)
         state = derive_manifest_state(repository_root)
         if arguments.emit_seed_review is not None:
             emit_seed_review(repository_root, state, arguments.emit_seed_review)
         elif arguments.write:
             write_manifests(
                 repository_root,
                 state,
                 approved_seed_sha256=arguments.approved_seed_sha256,
             )
         else:
