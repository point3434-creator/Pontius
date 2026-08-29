# Review package: 79751648d1c2006bc2ad5d1212786db4e8eb314b..88a553c34f4522439d04e1f49a2c2e88e97c1927

## Commits
88a553c fix(architecture): harden dependency baseline checks

## Files changed
 tests/test_stabilization_boundaries.py  |  903 +++++++++++++++++++++
 tools/check_stabilization_boundaries.py |  208 ++++-
 tools/generate_dependency_baseline.py   | 1301 ++++++++++++++++++++++++++++++-
 3 files changed, 2342 insertions(+), 70 deletions(-)

## Diff
diff --git a/tests/test_stabilization_boundaries.py b/tests/test_stabilization_boundaries.py
index d736885..e504767 100644
--- a/tests/test_stabilization_boundaries.py
+++ b/tests/test_stabilization_boundaries.py
@@ -1,19 +1,23 @@
 from __future__ import annotations
 
 from hashlib import sha256
 import importlib.util
 import os
 from pathlib import Path
+import shutil
+import subprocess
 import tempfile
 import tomllib
+from types import SimpleNamespace
 import unittest
+from unittest import mock
 
 
 REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
 GENERATOR_PATH = REPOSITORY_ROOT / "tools" / "generate_dependency_baseline.py"
 CHECKER_PATH = REPOSITORY_ROOT / "tools" / "check_stabilization_boundaries.py"
 BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
 EDGE_DIGEST = "c178ed92158da1c544abaf39ab14842721658a31f3f9246cbeb3e05e3e3da6ee"
 SCC_DIGEST = "9987fddd06742fc2af87de7b8ebf79bc8b2dda7231260f7cc9efdcca18dff345"
 
 
@@ -34,21 +38,80 @@ def _source(text: str) -> bytes:
     return text.encode("utf-8")
 
 
 def _git_executable() -> Path:
     configured = os.environ.get("PONTIUS_GIT")
     if configured is None or not Path(configured).is_absolute():
         raise RuntimeError("PONTIUS_GIT must name an absolute test Git executable")
     return Path(configured)
 
 
+def _run_fixture_git(repository: Path, *arguments: str) -> None:
+    environment = os.environ.copy()
+    environment["GIT_CONFIG_NOSYSTEM"] = "1"
+    environment["GIT_CONFIG_GLOBAL"] = "NUL" if os.name == "nt" else "/dev/null"
+    completed = subprocess.run(
+        [str(_git_executable()), *arguments],
+        cwd=repository,
+        env=environment,
+        stdin=subprocess.DEVNULL,
+        stdout=subprocess.PIPE,
+        stderr=subprocess.PIPE,
+        check=False,
+        timeout=30,
+        shell=False,
+    )
+    if completed.returncode != 0:
+        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
+
+
+def _create_directory_link(link: Path, target: Path) -> None:
+    try:
+        link.symlink_to(target, target_is_directory=True)
+        return
+    except OSError:
+        if os.name != "nt":
+            raise
+    command_processor = os.environ.get("ComSpec", "C:/Windows/System32/cmd.exe")
+    completed = subprocess.run(
+        [command_processor, "/d", "/c", "mklink", "/J", str(link), str(target)],
+        stdin=subprocess.DEVNULL,
+        stdout=subprocess.PIPE,
+        stderr=subprocess.PIPE,
+        check=False,
+        timeout=10,
+        shell=False,
+    )
+    if completed.returncode != 0:
+        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
+
+
+def _copy_checker_fixture(root: Path) -> Path:
+    shutil.copytree(REPOSITORY_ROOT / "src" / "pontius", root / "src" / "pontius")
+    shutil.copytree(REPOSITORY_ROOT / "tools", root / "tools")
+    baseline = root / "docs" / "architecture" / "dependency-baseline.toml"
+    baseline.parent.mkdir(parents=True)
+    shutil.copyfile(
+        REPOSITORY_ROOT / "docs" / "architecture" / baseline.name,
+        baseline,
+    )
+    return baseline
+
+
 class DependencyBaselineTests(unittest.TestCase):
+    def _assert_failure_temporary_policy(self, directory: Path) -> None:
+        temporaries = [path for path in directory.iterdir() if path.name.endswith(".tmp")]
+        if os.name == "nt":
+            self.assertEqual(temporaries, [])
+        else:
+            self.assertEqual(len(temporaries), 1)
+
     def test_exact_baseline_graph_matches_the_approved_mechanical_lock(self) -> None:
         graph = GENERATOR.derive_baseline_graph(
             REPOSITORY_ROOT,
             baseline_commit=BASELINE_COMMIT,
             git_executable=_git_executable(),
         )
 
         self.assertEqual(len(graph.modules), 470)
         self.assertEqual(len(graph.edges), 2577)
         self.assertEqual(GENERATOR.edges_sha256(graph.edges), EDGE_DIGEST)
@@ -198,22 +261,862 @@ class DependencyBaselineTests(unittest.TestCase):
             with self.assertRaises(GENERATOR.BaselineError):
                 GENERATOR.configured_git_executable()
             os.environ["PONTIUS_GIT"] = known_git
             self.assertTrue(GENERATOR.configured_git_executable().is_absolute())
         finally:
             if prior is None:
                 os.environ.pop("PONTIUS_GIT", None)
             else:
                 os.environ["PONTIUS_GIT"] = prior
 
+    def test_identity_bound_read_rejects_same_size_replacement_before_open(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-baseline-read-race-") as directory:
+            root = Path(directory).resolve()
+            target = root / "baseline.toml"
+            replacement = root / "replacement.toml"
+            target.write_bytes(b"first\n")
+            replacement.write_bytes(b"other\n")
+            real_open = getattr(GENERATOR, "_open_regular_no_follow", None)
+
+            def replace_then_open(path: Path) -> int:
+                os.replace(replacement, target)
+                if real_open is None:
+                    return os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0))
+                return real_open(path)
+
+            with mock.patch.object(
+                GENERATOR,
+                "_open_regular_no_follow",
+                create=True,
+                side_effect=replace_then_open,
+            ):
+                with self.assertRaises(GENERATOR.BaselineError) as caught:
+                    GENERATOR._validated_regular_file(target, maximum_bytes=64)
+
+            self.assertIn("changed while opening", str(caught.exception))
+
+    def test_identity_bound_read_rejects_same_size_mutation_during_read(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-baseline-handle-race-") as directory:
+            root = Path(directory).resolve()
+            target = root / "baseline.toml"
+            target.write_bytes(b"first\n")
+            real_read = GENERATOR.os.read
+            mutated = False
+
+            def mutate_then_read(descriptor: int, count: int) -> bytes:
+                nonlocal mutated
+                if not mutated:
+                    target.write_bytes(b"other\n")
+                    mutated = True
+                return real_read(descriptor, count)
+
+            with mock.patch.object(GENERATOR.os, "read", side_effect=mutate_then_read):
+                with self.assertRaises(GENERATOR.BaselineError) as caught:
+                    GENERATOR._validated_regular_file(target, maximum_bytes=64)
+
+            self.assertTrue(mutated, str(caught.exception))
+            self.assertIn("changed while reading", str(caught.exception))
+
+    def test_snapshot_revalidation_rechecks_content_when_metadata_is_concealed(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-baseline-content-pass-") as directory:
+            root = Path(directory).resolve()
+            target = root / "baseline.toml"
+            target.write_bytes(b"first\n")
+            snapshot = GENERATOR.read_regular_snapshot(
+                target,
+                maximum_bytes=64,
+                root=root,
+            )
+            target.write_bytes(b"other\n")
+
+            with mock.patch.object(
+                GENERATOR,
+                "_file_identity",
+                return_value=snapshot.identity,
+            ):
+                with self.assertRaises(GENERATOR.BaselineError) as caught:
+                    snapshot.revalidate()
+
+            self.assertIn("content changed", str(caught.exception))
+
+    def test_check_accepts_only_the_exact_all_crlf_checkout_transformation(self) -> None:
+        graph = GENERATOR.scan_sources(
+            {
+                "src/pontius/__init__.py": b"",
+                "src/pontius/a.py": b"from . import b\n",
+                "src/pontius/b.py": b"",
+            }
+        )
+        expected = GENERATOR.render_baseline(graph, baseline_commit=BASELINE_COMMIT)
+        with tempfile.TemporaryDirectory(prefix="pontius-baseline-autocrlf-") as directory:
+            root = Path(directory).resolve()
+            source = root / "source"
+            checkout = root / "checkout"
+            source.mkdir()
+            _run_fixture_git(source, "init", "--quiet")
+            baseline = source / "docs" / "architecture" / "dependency-baseline.toml"
+            baseline.parent.mkdir(parents=True)
+            baseline.write_bytes(expected)
+            _run_fixture_git(source, "-c", "core.autocrlf=false", "add", ".")
+            _run_fixture_git(
+                source,
+                "-c",
+                "user.name=Pontius Test",
+                "-c",
+                "user.email=pontius@example.invalid",
+                "commit",
+                "--quiet",
+                "-m",
+                "fixture",
+            )
+            _run_fixture_git(
+                root,
+                "-c",
+                "core.autocrlf=true",
+                "clone",
+                "--quiet",
+                str(source),
+                str(checkout),
+            )
+            checked_out = checkout / "docs" / "architecture" / baseline.name
+            actual = checked_out.read_bytes()
+
+            self.assertEqual(actual, expected.replace(b"\n", b"\r\n"))
+            GENERATOR.check_baseline(checked_out, expected)
+
+            mixed = actual.replace(b"\r\n", b"\n", 1)
+            checked_out.write_bytes(mixed)
+            with self.assertRaises(GENERATOR.BaselineError):
+                GENERATOR.check_baseline(checked_out, expected)
+
+    def test_write_rejects_an_architecture_symlink_escape(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-baseline-link-") as directory:
+            root = Path(directory).resolve()
+            docs = root / "docs"
+            docs.mkdir()
+            outside = root / "outside"
+            outside.mkdir()
+            architecture = docs / "architecture"
+            _create_directory_link(architecture, outside)
+            destination = architecture / "dependency-baseline.toml"
+
+            try:
+                with self.assertRaises(GENERATOR.BaselineError):
+                    GENERATOR.validate_write_destination(root, destination)
+                self.assertEqual(list(outside.iterdir()), [])
+            finally:
+                if architecture.is_symlink():
+                    architecture.unlink()
+                else:
+                    architecture.rmdir()
+
+    def test_bound_write_detects_a_post_validation_directory_swap(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-baseline-write-swap-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            destination = architecture / "dependency-baseline.toml"
+            destination.write_bytes(b"old\n")
+            displaced = root / "docs" / "architecture-displaced"
+            expected = GENERATOR.validate_write_destination(root, destination)
+            real_uuid4 = GENERATOR.uuid.uuid4
+            attempted = False
+            swapped = False
+
+            def swap_then_name() -> object:
+                nonlocal attempted, swapped
+                attempted = True
+                try:
+                    os.replace(architecture, displaced)
+                    architecture.mkdir()
+                except OSError:
+                    pass
+                else:
+                    swapped = True
+                return real_uuid4()
+
+            failure = None
+            with mock.patch.object(GENERATOR.uuid, "uuid4", side_effect=swap_then_name):
+                try:
+                    GENERATOR.write_baseline(expected, b"new\n")
+                except GENERATOR.BaselineError as error:
+                    failure = error
+
+            self.assertTrue(attempted)
+            if swapped:
+                self.assertIsNotNone(failure)
+                self.assertEqual(list(architecture.iterdir()), [])
+                self.assertEqual((displaced / destination.name).read_bytes(), b"old\n")
+                self._assert_failure_temporary_policy(displaced)
+            else:
+                self.assertIsNone(failure)
+                self.assertEqual(destination.read_bytes(), b"new\n")
+
+    def test_bound_write_retains_validated_identity_while_binding_parent(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-baseline-bind-swap-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            destination = architecture / "dependency-baseline.toml"
+            destination.write_bytes(b"old\n")
+            displaced = root / "docs" / "architecture-displaced"
+            expected = GENERATOR.validate_write_destination(root, destination)
+            method_name = "_bind_windows" if os.name == "nt" else "_bind_posix"
+            real_bind = getattr(GENERATOR._BoundBaselineDirectory, method_name)
+            swapped = False
+
+            def swap_then_bind(transaction: object) -> None:
+                nonlocal swapped
+                os.replace(architecture, displaced)
+                architecture.mkdir()
+                swapped = True
+                real_bind(transaction)
+
+            failure = None
+            with mock.patch.object(
+                GENERATOR._BoundBaselineDirectory,
+                method_name,
+                autospec=True,
+                side_effect=swap_then_bind,
+            ):
+                try:
+                    GENERATOR.write_baseline(expected, b"new\n")
+                except GENERATOR.BaselineError as error:
+                    failure = error
+
+            self.assertTrue(swapped)
+            self.assertIsNotNone(failure)
+            self.assertEqual(list(architecture.iterdir()), [])
+            self.assertEqual((displaced / destination.name).read_bytes(), b"old\n")
+
+    def test_bound_write_detects_a_directory_swap_at_atomic_replace(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-baseline-replace-swap-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            destination = architecture / "dependency-baseline.toml"
+            destination.write_bytes(b"old\n")
+            displaced = root / "docs" / "architecture-displaced"
+            expected = GENERATOR.validate_write_destination(root, destination)
+            real_replace = getattr(GENERATOR, "_replace_staged_file", None)
+            attempted = False
+            swapped = False
+
+            def swap_then_replace(*arguments: object, **keywords: object) -> None:
+                nonlocal attempted, swapped
+                attempted = True
+                try:
+                    os.replace(architecture, displaced)
+                    architecture.mkdir()
+                except OSError:
+                    pass
+                else:
+                    swapped = True
+                if real_replace is None:
+                    raise AssertionError("bound replacement seam is absent")
+                real_replace(*arguments, **keywords)
+
+            failure = None
+            with mock.patch.object(
+                GENERATOR,
+                "_replace_staged_file",
+                create=True,
+                side_effect=swap_then_replace,
+            ):
+                try:
+                    GENERATOR.write_baseline(expected, b"new\n")
+                except GENERATOR.BaselineError as error:
+                    failure = error
+
+            self.assertTrue(attempted)
+            if swapped:
+                self.assertIsNotNone(failure)
+                self.assertEqual(list(architecture.iterdir()), [])
+                self.assertEqual((displaced / destination.name).read_bytes(), b"new\n")
+                self.assertFalse(any(path.name.endswith(".tmp") for path in displaced.iterdir()))
+            else:
+                self.assertIsNone(failure)
+                self.assertEqual(destination.read_bytes(), b"new\n")
+
+    def test_bound_write_contains_a_staging_fault_without_replacing_destination(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-baseline-write-fault-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            destination = architecture / "dependency-baseline.toml"
+            destination.write_bytes(b"old\n")
+            expected = GENERATOR.validate_write_destination(root, destination)
+
+            with mock.patch.object(
+                GENERATOR,
+                "_write_staged_bytes",
+                create=True,
+                side_effect=OSError("injected staging failure"),
+            ):
+                with self.assertRaises(GENERATOR.BaselineError):
+                    GENERATOR.write_baseline(expected, b"new\n")
+
+            self.assertEqual(destination.read_bytes(), b"old\n")
+            self._assert_failure_temporary_policy(architecture)
+
+    def test_posix_cleanup_does_not_unlink_a_substituted_temporary_entry(self) -> None:
+        transaction = GENERATOR._BoundBaselineDirectory(
+            Path("/synthetic"),
+            Path("/synthetic/docs/architecture/dependency-baseline.toml"),
+        )
+        transaction._architecture_descriptor = 456
+        temporary = GENERATOR._StagedBaseline("temporary.tmp", 123)
+        transaction._temporaries.append(temporary)
+        handle_info = SimpleNamespace(
+            st_dev=1,
+            st_ino=10,
+            st_mode=GENERATOR.stat.S_IFREG | 0o600,
+            st_mtime_ns=1,
+            st_size=4,
+        )
+        substitute_info = SimpleNamespace(
+            st_dev=1,
+            st_ino=11,
+            st_mode=GENERATOR.stat.S_IFREG | 0o600,
+            st_mtime_ns=1,
+            st_size=5,
+        )
+
+        with mock.patch.object(GENERATOR.os, "name", "posix"), mock.patch.object(
+            GENERATOR.os,
+            "fstat",
+            return_value=handle_info,
+        ), mock.patch.object(
+            GENERATOR.os,
+            "stat",
+            return_value=substitute_info,
+        ), mock.patch.object(GENERATOR.os, "unlink") as unlink, mock.patch.object(
+            GENERATOR.os,
+            "close",
+        ) as close:
+            transaction._cleanup_temporary(temporary)
+
+        unlink.assert_not_called()
+        close.assert_called_once_with(123)
+        self.assertEqual(transaction._temporaries, [])
+        self.assertEqual(temporary.state, "closed")
+
+    def test_posix_failure_cleanup_is_close_only_for_an_owned_entry(self) -> None:
+        transaction = GENERATOR._BoundBaselineDirectory(
+            Path("/synthetic"),
+            Path("/synthetic/docs/architecture/dependency-baseline.toml"),
+        )
+        transaction._architecture_descriptor = 456
+        temporary = GENERATOR._StagedBaseline("temporary.tmp", 123)
+        transaction._temporaries.append(temporary)
+        owned_info = SimpleNamespace(
+            st_dev=1,
+            st_ino=10,
+            st_mode=GENERATOR.stat.S_IFREG | 0o600,
+            st_mtime_ns=1,
+            st_size=4,
+        )
+
+        with mock.patch.object(GENERATOR.os, "name", "posix"), mock.patch.object(
+            GENERATOR.os,
+            "fstat",
+            return_value=owned_info,
+        ), mock.patch.object(
+            GENERATOR.os,
+            "stat",
+            return_value=owned_info,
+        ), mock.patch.object(GENERATOR.os, "unlink") as unlink, mock.patch.object(
+            GENERATOR.os,
+            "close",
+        ) as close:
+            transaction._cleanup_temporary(temporary)
+
+        unlink.assert_not_called()
+        close.assert_called_once_with(123)
+        self.assertEqual(transaction._temporaries, [])
+        self.assertEqual(temporary.state, "closed")
+
+    def test_bound_write_contains_a_replace_fault_without_replacing_destination(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-baseline-replace-fault-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            destination = architecture / "dependency-baseline.toml"
+            destination.write_bytes(b"old\n")
+            expected = GENERATOR.validate_write_destination(root, destination)
+
+            with mock.patch.object(
+                GENERATOR,
+                "_replace_staged_file",
+                create=True,
+                side_effect=OSError("injected replacement failure"),
+            ):
+                with self.assertRaises(GENERATOR.BaselineError):
+                    GENERATOR.write_baseline(expected, b"new\n")
+
+            self.assertEqual(destination.read_bytes(), b"old\n")
+            self._assert_failure_temporary_policy(architecture)
+
+    @unittest.skipIf(os.name == "nt", "POSIX directory-descriptor mutation test")
+    def test_posix_write_rejects_staged_entry_substitution_before_replace(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-baseline-posix-entry-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            destination = architecture / "dependency-baseline.toml"
+            destination.write_bytes(b"old\n")
+            expected = GENERATOR.validate_write_destination(root, destination)
+            real_replace = GENERATOR._replace_staged_file
+
+            def substitute_then_replace(
+                transaction: object,
+                temporary: object,
+                destination_name: str,
+            ) -> None:
+                attacker = architecture / "attacker.tmp"
+                attacker.write_bytes(b"evil\n")
+                os.replace(attacker, architecture / temporary.name)
+                real_replace(transaction, temporary, destination_name)
+
+            with mock.patch.object(
+                GENERATOR,
+                "_replace_staged_file",
+                side_effect=substitute_then_replace,
+            ):
+                with self.assertRaises(GENERATOR.BaselineError):
+                    GENERATOR.write_baseline(expected, b"new\n")
+
+            self.assertEqual(destination.read_bytes(), b"old\n")
+            substitutes = [
+                path for path in architecture.iterdir() if path.name.endswith(".tmp")
+            ]
+            self.assertEqual(len(substitutes), 1)
+            self.assertEqual(substitutes[0].read_bytes(), b"evil\n")
+
+    @unittest.skipUnless(os.name == "nt", "Windows handle lifecycle test")
+    def test_windows_cleanup_retries_disposition_but_closes_only_once(self) -> None:
+        transaction = GENERATOR._BoundBaselineDirectory(
+            Path("C:/synthetic"),
+            Path("C:/synthetic/docs/architecture/dependency-baseline.toml"),
+        )
+        temporary = GENERATOR._StagedBaseline("temporary.tmp", 123)
+        transaction._temporaries.append(temporary)
+        disposition_error = GENERATOR.BaselineError("injected disposition failure")
+
+        with mock.patch.object(
+            GENERATOR,
+            "_windows_dispose_relative_file",
+            side_effect=(disposition_error, None),
+        ) as dispose, mock.patch.object(
+            GENERATOR,
+            "_windows_close_file",
+            return_value=None,
+        ) as close:
+            transaction._cleanup_temporary(temporary)
+
+        self.assertEqual(dispose.call_count, 2)
+        self.assertEqual(close.call_count, 1)
+        self.assertEqual(transaction._temporaries, [])
+        self.assertIsNone(temporary.handle)
+
+    @unittest.skipUnless(os.name == "nt", "Windows handle lifecycle test")
+    def test_windows_cleanup_never_retries_an_ambiguous_close_failure(self) -> None:
+        transaction = GENERATOR._BoundBaselineDirectory(
+            Path("C:/synthetic"),
+            Path("C:/synthetic/docs/architecture/dependency-baseline.toml"),
+        )
+        temporary = GENERATOR._StagedBaseline("temporary.tmp", 123)
+        temporary.renamed = True
+        transaction._temporaries.append(temporary)
+
+        with mock.patch.object(
+            GENERATOR,
+            "_windows_close_file",
+            side_effect=GENERATOR.BaselineError("injected close failure"),
+        ) as close:
+            with self.assertRaises(GENERATOR.BaselineError) as caught:
+                transaction._cleanup_temporary(temporary)
+
+        self.assertEqual(close.call_count, 1)
+        self.assertEqual(temporary.state, "close_attempted")
+        self.assertIsNone(temporary.handle)
+        self.assertIn(temporary, transaction._temporaries)
+        self.assertIn(temporary, caught.exception.retained_owners)
+
+    @unittest.skipUnless(os.name == "nt", "Windows handle lifecycle test")
+    def test_windows_directory_close_never_retries_an_ambiguous_failure(self) -> None:
+        close_error = OSError("injected directory close failure")
+        close = mock.Mock(side_effect=(close_error, None))
+
+        with mock.patch.object(
+            GENERATOR,
+            "_windows_directory_api",
+            return_value=(None, None, None, close),
+        ):
+            with self.assertRaises(GENERATOR.BaselineError) as caught:
+                GENERATOR._windows_close_directory(123)
+
+        self.assertEqual(close.call_count, 1)
+        self.assertIn(123, caught.exception.retained_owners)
+
+    @unittest.skipUnless(os.name == "nt", "Windows directory lifecycle test")
+    def test_windows_directory_api_failure_retains_acquired_handle_ownership(self) -> None:
+        api_error = GENERATOR.BaselineError("injected API resolution failure")
+
+        with mock.patch.object(
+            GENERATOR,
+            "_windows_directory_api",
+            side_effect=api_error,
+        ):
+            with self.assertRaises(GENERATOR.BaselineError) as caught:
+                GENERATOR._windows_close_directory(123)
+
+        self.assertIn(123, caught.exception.retained_owners)
+
+    @unittest.skipUnless(os.name == "nt", "Windows directory lifecycle test")
+    def test_windows_transaction_never_retries_an_ambiguous_directory_close(self) -> None:
+        transaction = GENERATOR._BoundBaselineDirectory(
+            Path("C:/synthetic"),
+            Path("C:/synthetic/docs/architecture/dependency-baseline.toml"),
+        )
+        transaction._windows_handles.append(
+            (Path("C:/synthetic"), 123, (42, b"i" * 16))
+        )
+        close_error = GENERATOR.BaselineError("injected directory close failure")
+
+        with mock.patch.object(
+            GENERATOR,
+            "_windows_close_directory",
+            side_effect=close_error,
+        ) as close:
+            with self.assertRaises(GENERATOR.BaselineError):
+                transaction.close()
+            with self.assertRaises(GENERATOR.BaselineError):
+                transaction.close()
+
+        self.assertEqual(close.call_count, 1)
+
+    def test_posix_transaction_never_retries_an_ambiguous_directory_close(self) -> None:
+        transaction = GENERATOR._BoundBaselineDirectory(
+            Path("/synthetic"),
+            Path("/synthetic/docs/architecture/dependency-baseline.toml"),
+        )
+        transaction._posix_descriptors.append((Path("/synthetic"), 123, (1, 2)))
+        close_error = OSError("injected directory close failure")
+
+        with mock.patch.object(
+            GENERATOR.os,
+            "close",
+            side_effect=close_error,
+        ) as close:
+            with self.assertRaises(GENERATOR.BaselineError):
+                transaction.close()
+            with self.assertRaises(GENERATOR.BaselineError):
+                transaction.close()
+
+        self.assertEqual(close.call_count, 1)
+
+    @unittest.skipUnless(os.name == "nt", "Windows directory access test")
+    def test_windows_directory_open_requests_traverse_without_list_access(self) -> None:
+        create = mock.Mock(return_value=123)
+        expected_identity = (42, b"i" * 16)
+
+        with mock.patch.object(
+            GENERATOR,
+            "_windows_directory_api",
+            return_value=(create, None, None, None),
+        ), mock.patch.object(
+            GENERATOR,
+            "_windows_directory_handle_identity",
+            return_value=expected_identity,
+        ):
+            handle, identity = GENERATOR._windows_open_directory(Path("C:/synthetic"))
+
+        desired_access = create.call_args.args[1]
+        self.assertEqual(handle, 123)
+        self.assertEqual(identity, expected_identity)
+        self.assertEqual(desired_access & 0x00000001, 0)
+        self.assertEqual(desired_access & 0x00000020, 0x00000020)
+
+    @unittest.skipUnless(os.name == "nt", "Windows handle ownership test")
+    def test_windows_file_binding_reports_an_ambiguous_handle_close(self) -> None:
+        create = mock.Mock(return_value=123)
+        close = mock.Mock(return_value=False)
+        binding_error = OSError("injected descriptor binding failure")
+
+        with mock.patch.object(
+            GENERATOR,
+            "_windows_path_api",
+            return_value=(create, close),
+        ), mock.patch.object(
+            GENERATOR.msvcrt,
+            "open_osfhandle",
+            side_effect=binding_error,
+        ), mock.patch.object(GENERATOR.ctypes, "get_last_error", return_value=6):
+            with self.assertRaises(GENERATOR.BaselineError) as caught:
+                GENERATOR._open_regular_no_follow(Path("C:/synthetic.py"))
+
+        self.assertEqual(close.call_count, 1)
+        self.assertIn(123, caught.exception.retained_owners)
+        self.assertEqual(len(caught.exception.failures), 2)
+
+    def test_posix_directory_binding_retains_a_descriptor_before_fstat(self) -> None:
+        transaction = GENERATOR._BoundBaselineDirectory(
+            Path("/synthetic"),
+            Path("/synthetic/docs/architecture/dependency-baseline.toml"),
+        )
+        open_directory = mock.Mock(return_value=123)
+        supported_dir_fd = {
+            open_directory,
+            GENERATOR.os.replace,
+            GENERATOR.os.stat,
+            GENERATOR.os.unlink,
+        }
+
+        with mock.patch.object(
+            GENERATOR.os,
+            "O_DIRECTORY",
+            0x10000,
+            create=True,
+        ), mock.patch.object(
+            GENERATOR.os,
+            "O_NOFOLLOW",
+            0x20000,
+            create=True,
+        ), mock.patch.object(
+            GENERATOR.os,
+            "open",
+            open_directory,
+        ), mock.patch.object(
+            GENERATOR.os,
+            "supports_dir_fd",
+            supported_dir_fd,
+        ), mock.patch.object(
+            GENERATOR.os,
+            "supports_follow_symlinks",
+            {GENERATOR.os.stat},
+        ), mock.patch.object(
+            GENERATOR.os,
+            "fstat",
+            side_effect=OSError("injected identity failure"),
+        ), mock.patch.object(GENERATOR.os, "close") as close:
+            with self.assertRaises(GENERATOR.BaselineError):
+                transaction._bind_posix()
+            transaction.close()
+
+        close.assert_called_once_with(123)
+
+    def test_posix_cleanup_never_retries_an_ambiguous_close_failure(self) -> None:
+        transaction = GENERATOR._BoundBaselineDirectory(
+            Path("/synthetic"),
+            Path("/synthetic/docs/architecture/dependency-baseline.toml"),
+        )
+        transaction._architecture_descriptor = 456
+        temporary = GENERATOR._StagedBaseline("temporary.tmp", 123)
+        temporary.renamed = True
+        transaction._temporaries.append(temporary)
+
+        close_error = OSError("injected descriptor close failure")
+        with mock.patch.object(GENERATOR.os, "name", "posix"), mock.patch.object(
+            GENERATOR.os,
+            "close",
+            side_effect=close_error,
+        ) as close:
+            with self.assertRaises(GENERATOR.BaselineError):
+                transaction._cleanup_temporary(temporary)
+            with self.assertRaises(GENERATOR.BaselineError) as caught:
+                transaction._cleanup_temporary(temporary)
+
+        self.assertEqual(close.call_count, 1)
+        self.assertEqual(temporary.state, "close_attempted")
+        self.assertIsNone(temporary.handle)
+        self.assertIn(temporary, transaction._temporaries)
+        self.assertIn(temporary, caught.exception.retained_owners)
+
+    @unittest.skipUnless(os.name == "nt", "Windows handle lifecycle test")
+    def test_windows_cleanup_retains_owner_after_persistent_disposition_fault(self) -> None:
+        transaction = GENERATOR._BoundBaselineDirectory(
+            Path("C:/synthetic"),
+            Path("C:/synthetic/docs/architecture/dependency-baseline.toml"),
+        )
+        temporary = GENERATOR._StagedBaseline("temporary.tmp", 123)
+        transaction._temporaries.append(temporary)
+
+        with mock.patch.object(
+            GENERATOR,
+            "_windows_dispose_relative_file",
+            side_effect=GENERATOR.BaselineError("injected disposition failure"),
+        ):
+            with self.assertRaises(GENERATOR.BaselineError) as caught:
+                transaction._cleanup_temporary(temporary)
+
+        self.assertIn(temporary, transaction._temporaries)
+        self.assertEqual(temporary.handle, 123)
+        self.assertIn(temporary, caught.exception.retained_owners)
+
 
 class StabilizationPolicyTests(unittest.TestCase):
+    def test_checker_commit_pin_is_independent_from_the_generator_constant(self) -> None:
+        baseline = REPOSITORY_ROOT / "docs" / "architecture" / "dependency-baseline.toml"
+        drifted_commit = "b" * 40
+        forged = baseline.read_bytes().replace(
+            BASELINE_COMMIT.encode("ascii"),
+            drifted_commit.encode("ascii"),
+            1,
+        )
+        parsed = GENERATOR.parse_baseline_bytes(forged)
+
+        with mock.patch.object(CHECKER._BASELINE, "BASELINE_COMMIT", drifted_commit):
+            with self.assertRaises(CHECKER.BoundaryError) as caught:
+                CHECKER.authenticate_approved_baseline(parsed)
+
+        self.assertIn("approved mechanical lock", str(caught.exception))
+
+    def test_checker_rejects_a_valid_self_consistent_forged_baseline(self) -> None:
+        graph = GENERATOR.scan_sources(
+            {
+                "src/pontius/__init__.py": b"",
+                "src/pontius/a.py": b"from . import b\n",
+                "src/pontius/b.py": b"",
+            }
+        )
+        forged = GENERATOR.render_baseline(graph, baseline_commit=BASELINE_COMMIT)
+        with tempfile.TemporaryDirectory(prefix="pontius-forged-baseline-") as directory:
+            root = Path(directory).resolve()
+            source = root / "src" / "pontius"
+            source.mkdir(parents=True)
+            (source / "__init__.py").write_bytes(b"")
+            (source / "a.py").write_bytes(b"from . import b\n")
+            (source / "b.py").write_bytes(b"")
+            baseline = root / "docs" / "architecture" / "dependency-baseline.toml"
+            baseline.parent.mkdir(parents=True)
+            baseline.write_bytes(forged)
+
+            with self.assertRaises(CHECKER.BoundaryError) as caught:
+                CHECKER.check_repository(root)
+
+        self.assertIn("approved mechanical lock", str(caught.exception))
+
+    def test_source_collection_revalidates_cross_file_identity_changes(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-source-cross-race-") as directory:
+            root = Path(directory).resolve()
+            source = root / "src" / "pontius"
+            source.mkdir(parents=True)
+            (source / "__init__.py").write_bytes(b"")
+            first = source / "a.py"
+            first.write_bytes(b"VALUE = 1\n")
+            (source / "b.py").write_bytes(b"VALUE = 2\n")
+            replacement = root / "replacement.py"
+            replacement.write_bytes(b"VALUE = 1\n")
+            real_read = CHECKER._read_regular_source
+
+            def mutate_first_while_reading_second(path: Path, *, root: Path) -> object:
+                snapshot = real_read(path, root=root)
+                if path.name == "b.py":
+                    os.replace(replacement, first)
+                return snapshot
+
+            with mock.patch.object(
+                CHECKER,
+                "_read_regular_source",
+                side_effect=mutate_first_while_reading_second,
+            ):
+                with self.assertRaises(CHECKER.BoundaryError) as caught:
+                    CHECKER._collect_sources(root, "src/pontius")
+
+            self.assertIn("identity changed", str(caught.exception))
+
+    def test_source_collection_revalidates_the_complete_python_inventory(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-source-inventory-race-") as directory:
+            root = Path(directory).resolve()
+            source = root / "src" / "pontius"
+            source.mkdir(parents=True)
+            (source / "__init__.py").write_bytes(b"")
+            (source / "a.py").write_bytes(b"VALUE = 1\n")
+            (source / "b.py").write_bytes(b"VALUE = 2\n")
+            added = source / "c.py"
+            real_read = CHECKER._read_regular_source
+
+            def add_path_while_reading_last(path: Path, *, root: Path) -> object:
+                snapshot = real_read(path, root=root)
+                if path.name == "b.py":
+                    added.write_bytes(b"VALUE = 3\n")
+                return snapshot
+
+            with mock.patch.object(
+                CHECKER,
+                "_read_regular_source",
+                side_effect=add_path_while_reading_last,
+            ):
+                with self.assertRaises(CHECKER.BoundaryError) as caught:
+                    CHECKER._collect_sources(root, "src/pontius")
+
+            self.assertIn("source inventory changed", str(caught.exception))
+
+    def test_source_inventory_rejects_noncanonical_python_suffix_case(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-source-suffix-") as directory:
+            root = Path(directory).resolve()
+            source = root / "src" / "pontius"
+            source.mkdir(parents=True)
+            (source / "__init__.py").write_bytes(b"")
+            (source / "unreviewed.PY").write_bytes(b"import cupy\n")
+
+            with self.assertRaises(CHECKER.BoundaryError) as caught:
+                CHECKER._collect_sources(root, "src/pontius")
+
+            self.assertIn("noncanonical Python suffix", str(caught.exception))
+
+    def test_repository_check_revalidates_baseline_identity_after_policy_work(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-final-identity-") as directory:
+            root = Path(directory).resolve()
+            baseline = _copy_checker_fixture(root)
+            real_policy = CHECKER.enforce_orchestration_import_policy
+
+            def mutate_after_policy(sources: object) -> None:
+                real_policy(sources)
+                replacement = root / "baseline-replacement.toml"
+                replacement.write_bytes(baseline.read_bytes())
+                os.replace(replacement, baseline)
+
+            with mock.patch.object(
+                CHECKER,
+                "enforce_orchestration_import_policy",
+                side_effect=mutate_after_policy,
+            ):
+                with self.assertRaises(CHECKER.BoundaryError) as caught:
+                    CHECKER.check_repository(root)
+
+            self.assertIn("dependency baseline identity changed", str(caught.exception))
+
+    def test_repository_check_revalidates_source_identity_after_policy_work(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-final-source-identity-") as directory:
+            root = Path(directory).resolve()
+            _copy_checker_fixture(root)
+            source = root / "src" / "pontius" / "__init__.py"
+            real_policy = CHECKER.enforce_orchestration_import_policy
+
+            def mutate_after_policy(sources: object) -> None:
+                real_policy(sources)
+                replacement = root / "source-replacement.py"
+                replacement.write_bytes(source.read_bytes())
+                os.replace(replacement, source)
+
+            with mock.patch.object(
+                CHECKER,
+                "enforce_orchestration_import_policy",
+                side_effect=mutate_after_policy,
+            ):
+                with self.assertRaises(CHECKER.BoundaryError) as caught:
+                    CHECKER.check_repository(root)
+
+            self.assertIn("Python source identity changed", str(caught.exception))
+
     def test_only_plan_declared_stabilization_origins_are_classified(self) -> None:
         CHECKER.enforce_origin_classification(
             {
                 "src/pontius/evidence/__init__.py": b"",
                 "src/pontius/evidence/authorization.py": b"",
             },
             {
                 "tools/run_tests.py": b"",
                 "tools/test_orchestration/model.py": b"",
             },
diff --git a/tools/check_stabilization_boundaries.py b/tools/check_stabilization_boundaries.py
index cf610fd..5f57f96 100644
--- a/tools/check_stabilization_boundaries.py
+++ b/tools/check_stabilization_boundaries.py
@@ -6,20 +6,26 @@ import argparse
 from collections.abc import Mapping, Sequence
 import importlib.util
 import os
 from pathlib import Path
 import stat
 import sys
 from types import ModuleType
 
 
 BASELINE_RELATIVE_PATH = "docs/architecture/dependency-baseline.toml"
+APPROVED_BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
+APPROVED_MODULE_COUNT = 470
+APPROVED_EDGE_COUNT = 2577
+APPROVED_EDGE_DIGEST = "c178ed92158da1c544abaf39ab14842721658a31f3f9246cbeb3e05e3e3da6ee"
+APPROVED_SCC_COUNT = 469
+APPROVED_SCC_DIGEST = "9987fddd06742fc2af87de7b8ebf79bc8b2dda7231260f7cc9efdcca18dff345"
 _ORCHESTRATION_SIBLING_PREFIX = "tools.test_orchestration"
 EVIDENCE_ORIGIN_PATHS = frozenset(
     {
         "src/pontius/evidence/__init__.py",
         "src/pontius/evidence/authorization.py",
         "src/pontius/evidence/errors.py",
         "src/pontius/evidence/manifest.py",
         "src/pontius/evidence/model.py",
         "src/pontius/evidence/retained_v7.py",
     }
@@ -80,20 +86,44 @@ def _load_generator() -> ModuleType:
 
 
 _BASELINE = _load_generator()
 
 
 def _raise_violations(violations: Sequence[str]) -> None:
     if violations:
         raise BoundaryError(violations)
 
 
+def authenticate_approved_baseline(parsed: object) -> None:
+    """Authenticate the complete accepted graph instead of trusting its metadata."""
+
+    graph = parsed.graph
+    identity = (
+        parsed.baseline_commit,
+        len(graph.modules),
+        len(graph.edges),
+        _BASELINE.edges_sha256(graph.edges),
+        len(graph.sccs),
+        _BASELINE.sccs_sha256(graph.sccs),
+    )
+    approved = (
+        APPROVED_BASELINE_COMMIT,
+        APPROVED_MODULE_COUNT,
+        APPROVED_EDGE_COUNT,
+        APPROVED_EDGE_DIGEST,
+        APPROVED_SCC_COUNT,
+        APPROVED_SCC_DIGEST,
+    )
+    if identity != approved:
+        raise BoundaryError("dependency baseline differs from the approved mechanical lock")
+
+
 def enforce_legacy_edges(baseline: object, current: object) -> None:
     """Require every mechanically grandfathered origin to retain its edge set."""
 
     baseline_modules = {name for name, _ in baseline.modules}
     current_modules = {name for name, _ in current.modules}
     baseline_edges = {name: set() for name in baseline_modules}
     current_edges = {name: set() for name in current_modules}
     for origin, target in baseline.edges:
         baseline_edges[origin].add(target)
     for origin, target in current.edges:
@@ -193,79 +223,193 @@ def enforce_orchestration_import_policy(sources: Mapping[str, bytes]) -> None:
             continue
         sibling = target == _ORCHESTRATION_SIBLING_PREFIX or target.startswith(
             _ORCHESTRATION_SIBLING_PREFIX + "."
         )
         if not _is_stdlib(target) and not sibling:
             violations.append(f"forbidden orchestration import: {origin} -> {target}")
     _raise_violations(violations)
 
 
 def _is_reparse(info: os.stat_result) -> bool:
-    return bool(getattr(info, "st_file_attributes", 0) & 0x400)
+    return bool(int(getattr(info, "st_file_attributes", 0)) & 0x400) or bool(
+        int(getattr(info, "st_reparse_tag", 0))
+    )
+
+
+def _read_regular_source(path: Path, *, root: Path) -> object:
+    try:
+        return _BASELINE.read_regular_snapshot(
+            path,
+            maximum_bytes=_BASELINE.MAXIMUM_SOURCE_BYTES,
+            root=root,
+        )
+    except _BASELINE.BaselineError as error:
+        raise BoundaryError(f"Python source cannot be snapshotted: {path}: {error}") from error
 
 
-def _read_regular_source(path: Path, *, root: Path) -> bytes:
+def _directory_inventory_identity(path: Path) -> tuple[int, ...]:
     try:
         info = os.lstat(path)
     except OSError as error:
-        raise BoundaryError(f"Python source cannot be inspected: {path}") from error
-    if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISREG(info.st_mode):
-        raise BoundaryError(f"Python source is not a regular nonreparse file: {path}")
-    try:
-        relative = path.relative_to(root).as_posix()
-        raw = path.read_bytes()
-    except (OSError, ValueError) as error:
-        raise BoundaryError(
-            f"Python source cannot be read below repository root: {path}"
-        ) from error
-    if len(raw) != info.st_size:
-        raise BoundaryError(f"Python source changed while reading: {relative}")
-    return raw
-
-
-def _collect_sources(repository_root: Path, relative_root: str) -> dict[str, bytes]:
+        raise BoundaryError(f"Python inventory directory cannot be inspected: {path}") from error
+    if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
+        raise BoundaryError(f"Python inventory has a non-directory or reparse: {path}")
+    return _BASELINE._directory_identity(info)
+
+
+def _python_inventory(
+    repository_root: Path, relative_root: str
+) -> tuple[bool, tuple[str, ...], tuple[tuple[str, tuple[int, ...]], ...]]:
     base = repository_root / relative_root
-    if not base.exists():
-        return {}
-    sources: dict[str, bytes] = {}
-    for path in sorted(base.rglob("*.py")):
-        relative = path.relative_to(repository_root).as_posix()
-        sources[relative] = _read_regular_source(path, root=repository_root)
-    return sources
+    if not os.path.lexists(base):
+        return False, (), ()
+    paths: list[str] = []
+    directories: list[tuple[str, tuple[int, ...]]] = []
+
+    def walk_error(error: OSError) -> None:
+        raise BoundaryError(f"Python inventory cannot be walked: {base}") from error
+
+    for current, names, filenames in os.walk(
+        base, topdown=True, onerror=walk_error, followlinks=False
+    ):
+        directory = Path(current)
+        relative_directory = directory.relative_to(repository_root).as_posix()
+        directories.append(
+            (relative_directory, _directory_inventory_identity(directory))
+        )
+        for name in tuple(names):
+            child = directory / name
+            _directory_inventory_identity(child)
+        for filename in filenames:
+            if filename.casefold().endswith(".py"):
+                relative = (directory / filename).relative_to(repository_root).as_posix()
+                if not filename.endswith(".py"):
+                    raise BoundaryError(
+                        f"Python inventory has a noncanonical Python suffix: {relative}"
+                    )
+                paths.append(relative)
+    return True, tuple(sorted(paths)), tuple(sorted(directories))
+
+
+class SourceInventory:
+    """A complete source inventory with identities retained through policy work."""
+
+    __slots__ = (
+        "repository_root",
+        "relative_root",
+        "exists",
+        "paths",
+        "directories",
+        "snapshots",
+        "sources",
+    )
+
+    def __init__(
+        self,
+        repository_root: Path,
+        relative_root: str,
+        exists: bool,
+        paths: Sequence[str],
+        directories: Sequence[tuple[str, tuple[int, ...]]],
+        snapshots: Mapping[str, object],
+    ) -> None:
+        self.repository_root = repository_root
+        self.relative_root = relative_root
+        self.exists = exists
+        self.paths = tuple(paths)
+        self.directories = tuple(directories)
+        self.snapshots = dict(snapshots)
+        self.sources = {
+            relative: snapshot.raw for relative, snapshot in self.snapshots.items()
+        }
+
+    def revalidate(self) -> None:
+        current = _python_inventory(self.repository_root, self.relative_root)
+        if current != (self.exists, self.paths, self.directories):
+            raise BoundaryError(
+                f"Python source inventory changed: {self.relative_root}"
+            )
+        try:
+            for snapshot in self.snapshots.values():
+                snapshot.revalidate()
+        except _BASELINE.BaselineError as error:
+            raise BoundaryError(
+                f"Python source identity changed: {self.relative_root}: {error}"
+            ) from error
+
+
+def _collect_sources(repository_root: Path, relative_root: str) -> SourceInventory:
+    exists, paths, directories = _python_inventory(repository_root, relative_root)
+    snapshots = {
+        relative: _read_regular_source(repository_root / relative, root=repository_root)
+        for relative in paths
+    }
+    inventory = SourceInventory(
+        repository_root,
+        relative_root,
+        exists,
+        paths,
+        directories,
+        snapshots,
+    )
+    inventory.revalidate()
+    return inventory
+
+
+def _revalidate_repository_snapshot(
+    baseline: object,
+    current: SourceInventory,
+    tools: SourceInventory,
+) -> None:
+    try:
+        baseline.revalidate()
+    except _BASELINE.BaselineError as error:
+        raise BoundaryError(f"dependency baseline identity changed: {error}") from error
+    current.revalidate()
+    tools.revalidate()
 
 
 def check_repository(repository_root: Path) -> None:
     try:
         root = repository_root.resolve(strict=True)
     except OSError as error:
         raise BoundaryError("repository root cannot be resolved") from error
     baseline_path = root / BASELINE_RELATIVE_PATH
     try:
-        baseline_raw = _BASELINE._validated_regular_file(
-            baseline_path, maximum_bytes=_BASELINE.MAXIMUM_BASELINE_BYTES
+        baseline_snapshot = _BASELINE.read_regular_snapshot(
+            baseline_path,
+            maximum_bytes=_BASELINE.MAXIMUM_BASELINE_BYTES,
+            root=root,
         )
-        parsed = _BASELINE.parse_baseline_bytes(baseline_raw)
+        parsed = _BASELINE.parse_baseline_bytes(baseline_snapshot.raw)
     except _BASELINE.BaselineError as error:
         raise BoundaryError(f"dependency baseline cannot be loaded: {error}") from error
-    if parsed.baseline_commit != _BASELINE.BASELINE_COMMIT:
-        raise BoundaryError("dependency baseline commit differs from stabilization baseline")
-    current_sources = _collect_sources(root, "src/pontius")
-    tool_sources = _collect_sources(root, "tools")
+    authenticate_approved_baseline(parsed)
+    current_inventory = _collect_sources(root, "src/pontius")
+    tool_inventory = _collect_sources(root, "tools")
+    current_sources = current_inventory.sources
+    tool_sources = tool_inventory.sources
+    _revalidate_repository_snapshot(
+        baseline_snapshot, current_inventory, tool_inventory
+    )
     try:
         current_graph = _BASELINE.scan_sources(current_sources)
     except _BASELINE.BaselineError as error:
         raise BoundaryError(f"current dependency graph cannot be derived: {error}") from error
     enforce_origin_classification(current_sources, tool_sources)
     enforce_legacy_edges(parsed.graph, current_graph)
     enforce_no_new_or_expanded_scc(parsed.graph, current_graph)
     enforce_evidence_import_policy(current_sources)
     enforce_orchestration_import_policy(tool_sources)
+    _revalidate_repository_snapshot(
+        baseline_snapshot, current_inventory, tool_inventory
+    )
 
 
 def parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
     parser = argparse.ArgumentParser(description=__doc__)
     return parser.parse_args(argv)
 
 
 def main(argv: Sequence[str] | None = None) -> int:
     parse_arguments(argv)
     repository_root = Path(__file__).resolve().parents[1]
diff --git a/tools/generate_dependency_baseline.py b/tools/generate_dependency_baseline.py
index c707b9b..2706bdb 100644
--- a/tools/generate_dependency_baseline.py
+++ b/tools/generate_dependency_baseline.py
@@ -2,48 +2,81 @@
 
 This tool is standard-library-only.  It reads Python source from an exact Git
 commit, parses imports with :mod:`ast`, and emits a canonical TOML lock.
 """
 
 from __future__ import annotations
 
 import argparse
 import ast
 from collections.abc import Mapping, Sequence
+import ctypes
 from hashlib import sha256
 import io
 import json
 import os
 from pathlib import Path, PurePosixPath, PureWindowsPath
 import re
 import stat
 import subprocess
 import sys
 import tarfile
 import tempfile
 import tomllib
 from typing import Any
 import uuid
 
+if os.name == "nt":
+    from ctypes import wintypes
+    import msvcrt
+
 
 SCHEMA_VERSION = "pontius-dependency-baseline-v1"
 BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
 BASELINE_RELATIVE_PATH = "docs/architecture/dependency-baseline.toml"
 MAXIMUM_ARCHIVE_BYTES = 64 * 1024 * 1024
 MAXIMUM_BASELINE_BYTES = 4 * 1024 * 1024
+MAXIMUM_SOURCE_BYTES = 16 * 1024 * 1024
+_REPARSE_ATTRIBUTE = 0x400
 _HEX40 = re.compile(r"[0-9a-f]{40}\Z")
 _HEX64 = re.compile(r"[0-9a-f]{64}\Z")
 
 
 class BaselineError(RuntimeError):
     """A deterministic dependency-baseline failure."""
 
+    def __init__(
+        self,
+        message: str,
+        *,
+        failures: Sequence[BaseException] = (),
+        retained_owners: Sequence[object] = (),
+    ) -> None:
+        self.failures = tuple(failures)
+        self.retained_owners = tuple(retained_owners)
+        super().__init__(message)
+
+
+def _aggregate_errors(
+    message: str,
+    failures: Sequence[BaseException],
+    *,
+    retained_owners: Sequence[object] = (),
+) -> BaselineError:
+    ordered = tuple(failures)
+    detail = "; ".join(f"{type(error).__name__}: {error}" for error in ordered)
+    return BaselineError(
+        f"{message}: {detail}",
+        failures=ordered,
+        retained_owners=retained_owners,
+    )
+
 
 class DependencyGraph:
     """Canonical module, internal-edge, and SCC rows."""
 
     __slots__ = ("modules", "edges", "sccs")
 
     def __init__(
         self,
         modules: Sequence[tuple[str, str]],
         edges: Sequence[tuple[str, str]],
@@ -544,39 +577,321 @@ def parse_baseline_bytes(raw: bytes) -> ParsedBaseline:
     if scc_count != len(graph.sccs):
         raise BaselineError("scc_count does not match SCC rows")
     if expected_edge_digest != edges_sha256(graph.edges):
         raise BaselineError("edges_sha256 does not match canonical edge rows")
     if expected_scc_digest != sccs_sha256(graph.sccs):
         raise BaselineError("sccs_sha256 does not match canonical SCC rows")
     return ParsedBaseline(commit, graph)
 
 
 def _is_reparse(info: os.stat_result) -> bool:
-    return bool(getattr(info, "st_file_attributes", 0) & 0x400)
+    return bool(int(getattr(info, "st_file_attributes", 0)) & _REPARSE_ATTRIBUTE) or bool(
+        int(getattr(info, "st_reparse_tag", 0))
+    )
 
 
-def _validated_regular_file(path: Path, *, maximum_bytes: int) -> bytes:
+def _file_identity(info: os.stat_result) -> tuple[int, ...]:
+    return (
+        int(info.st_dev),
+        int(info.st_ino),
+        int(info.st_size),
+        int(info.st_mtime_ns),
+        int(info.st_ctime_ns),
+        int(info.st_mode),
+        int(getattr(info, "st_file_attributes", 0)),
+        int(getattr(info, "st_reparse_tag", 0)),
+    )
+
+
+def _path_handle_identity(info: os.stat_result) -> tuple[int, ...]:
+    """Return fields reported consistently by path and handle on Windows."""
+
+    return (
+        int(info.st_dev),
+        int(info.st_ino),
+        int(info.st_size),
+        int(info.st_mtime_ns),
+        int(info.st_mode),
+        int(getattr(info, "st_file_attributes", 0)),
+        int(getattr(info, "st_reparse_tag", 0)),
+    )
+
+
+def _directory_identity(info: os.stat_result) -> tuple[int, ...]:
+    return (
+        int(info.st_dev),
+        int(info.st_ino),
+        int(info.st_mode),
+        int(getattr(info, "st_file_attributes", 0)),
+        int(getattr(info, "st_reparse_tag", 0)),
+    )
+
+
+def _validated_ancestor_chain(path: Path, root: Path) -> tuple[tuple[Path, tuple[int, ...]], ...]:
+    if not path.is_absolute() or not root.is_absolute():
+        raise BaselineError("secure snapshot paths must be absolute")
     try:
-        info = os.lstat(path)
+        path.relative_to(root)
+    except ValueError as error:
+        raise BaselineError("secure snapshot path is outside its repository root") from error
+    ancestors: list[tuple[Path, tuple[int, ...]]] = []
+    for component in reversed(path.parents):
+        if component == component.parent:
+            continue
+        try:
+            info = os.lstat(component)
+        except OSError as error:
+            raise BaselineError(
+                f"dependency path ancestor cannot be inspected: {component}"
+            ) from error
+        if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
+            raise BaselineError(
+                f"dependency path ancestor is not a nonreparse directory: {component}"
+            )
+        ancestors.append((component, _directory_identity(info)))
+    return tuple(ancestors)
+
+
+def _revalidate_ancestor_chain(
+    ancestors: Sequence[tuple[Path, tuple[int, ...]]],
+) -> None:
+    for component, expected in ancestors:
+        try:
+            info = os.lstat(component)
+        except OSError as error:
+            raise BaselineError(
+                f"dependency path ancestor disappeared: {component}"
+            ) from error
+        if (
+            stat.S_ISLNK(info.st_mode)
+            or _is_reparse(info)
+            or not stat.S_ISDIR(info.st_mode)
+            or _directory_identity(info) != expected
+        ):
+            raise BaselineError(
+                f"dependency path ancestor identity changed: {component}"
+            )
+
+
+def _windows_path_api() -> tuple[Any, Any]:
+    if os.name != "nt":
+        raise BaselineError("Windows no-follow file APIs are unavailable")
+    try:
+        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
+        create = kernel32.CreateFileW
+        create.argtypes = (
+            wintypes.LPCWSTR,
+            wintypes.DWORD,
+            wintypes.DWORD,
+            wintypes.LPVOID,
+            wintypes.DWORD,
+            wintypes.DWORD,
+            wintypes.HANDLE,
+        )
+        create.restype = wintypes.HANDLE
+        close = kernel32.CloseHandle
+        close.argtypes = (wintypes.HANDLE,)
+        close.restype = wintypes.BOOL
+    except Exception as error:
+        raise BaselineError("Windows no-follow file APIs are unavailable") from error
+    return create, close
+
+
+def _open_regular_no_follow(path: Path) -> int:
+    if os.name != "nt":
+        if not hasattr(os, "O_NOFOLLOW"):
+            raise BaselineError("secure no-follow file opens are unavailable")
+        flags = (
+            os.O_RDONLY
+            | os.O_NOFOLLOW
+            | getattr(os, "O_CLOEXEC", 0)
+            | getattr(os, "O_BINARY", 0)
+        )
+        try:
+            return os.open(path, flags)
+        except OSError as error:
+            raise BaselineError(
+                f"dependency file cannot be opened without links: {path}"
+            ) from error
+
+    create, close = _windows_path_api()
+    try:
+        handle = create(
+            str(path),
+            0x80000000,
+            0x00000001 | 0x00000002 | 0x00000004,
+            None,
+            3,
+            0x00200000 | 0x08000000,
+            None,
+        )
+    except Exception as error:
+        raise BaselineError(f"dependency file cannot be opened without reparses: {path}") from error
+    invalid = ctypes.c_void_p(-1).value
+    if not handle or int(handle) == invalid:
+        error = ctypes.get_last_error()
+        raise BaselineError(
+            f"dependency file cannot be opened without reparses: {path}"
+        ) from OSError(error, os.strerror(error), str(path))
+    try:
+        return msvcrt.open_osfhandle(
+            int(handle), os.O_RDONLY | getattr(os, "O_BINARY", 0)
+        )
+    except (OSError, OverflowError) as error:
+        numeric = int(handle)
+        binding_failure = BaselineError(
+            f"dependency file handle cannot be bound: {path}",
+            failures=(error,),
+        )
+        try:
+            succeeded = close(wintypes.HANDLE(numeric))
+        except Exception as cleanup_error:
+            raise _aggregate_errors(
+                "dependency file binding and handle cleanup both failed",
+                (binding_failure, cleanup_error),
+                retained_owners=(numeric,),
+            ) from error
+        if not succeeded:
+            code = ctypes.get_last_error()
+            cleanup_error = OSError(code, os.strerror(code), str(path))
+            raise _aggregate_errors(
+                "dependency file binding and handle cleanup both failed",
+                (binding_failure, cleanup_error),
+                retained_owners=(numeric,),
+            ) from error
+        raise binding_failure from error
+
+
+class FileSnapshot:
+    """Bytes and filesystem identities retained for a later final pass."""
+
+    __slots__ = (
+        "path",
+        "raw",
+        "identity",
+        "ancestors",
+        "maximum_bytes",
+        "root",
+    )
+
+    def __init__(
+        self,
+        path: Path,
+        raw: bytes,
+        identity: tuple[int, ...],
+        ancestors: Sequence[tuple[Path, tuple[int, ...]]],
+        maximum_bytes: int,
+        root: Path,
+    ) -> None:
+        self.path = path
+        self.raw = raw
+        self.identity = identity
+        self.ancestors = tuple(ancestors)
+        self.maximum_bytes = maximum_bytes
+        self.root = root
+
+    def revalidate(self) -> None:
+        current = read_regular_snapshot(
+            self.path,
+            maximum_bytes=self.maximum_bytes,
+            root=self.root,
+        )
+        if current.identity != self.identity:
+            raise BaselineError(f"dependency file identity changed: {self.path}")
+        if current.raw != self.raw:
+            raise BaselineError(f"dependency file content changed: {self.path}")
+
+
+def read_regular_snapshot(
+    path: Path, *, maximum_bytes: int, root: Path
+) -> FileSnapshot:
+    """Read one bounded, identity-bound, nonlink filesystem snapshot."""
+
+    if type(maximum_bytes) is not int or maximum_bytes < 0:
+        raise BaselineError("dependency snapshot bound is invalid")
+    ancestors = _validated_ancestor_chain(path, root)
+    try:
+        before_path = os.lstat(path)
     except OSError as error:
-        raise BaselineError(f"dependency baseline file cannot be inspected: {path}") from error
-    if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISREG(info.st_mode):
-        raise BaselineError(f"dependency baseline path is not a regular file: {path}")
-    if info.st_size > maximum_bytes:
-        raise BaselineError(f"dependency baseline file is oversized: {path}")
+        raise BaselineError(f"dependency file cannot be inspected: {path}") from error
+    if (
+        stat.S_ISLNK(before_path.st_mode)
+        or _is_reparse(before_path)
+        or not stat.S_ISREG(before_path.st_mode)
+    ):
+        raise BaselineError(f"dependency path is not a regular nonreparse file: {path}")
+    if before_path.st_size > maximum_bytes:
+        raise BaselineError(f"dependency file is oversized: {path}")
+
+    descriptor = _open_regular_no_follow(path)
+    after_handle: os.stat_result | None = None
     try:
-        raw = path.read_bytes()
+        before_handle = os.fstat(descriptor)
+        if (
+            not stat.S_ISREG(before_handle.st_mode)
+            or _is_reparse(before_handle)
+            or _path_handle_identity(before_path) != _path_handle_identity(before_handle)
+        ):
+            raise BaselineError(f"dependency file changed while opening: {path}")
+        chunks: list[bytes] = []
+        length = 0
+        while length <= maximum_bytes:
+            chunk = os.read(descriptor, min(1024 * 1024, maximum_bytes + 1 - length))
+            if not chunk:
+                break
+            chunks.append(chunk)
+            length += len(chunk)
+        raw = b"".join(chunks)
+        after_handle = os.fstat(descriptor)
+        if len(raw) > maximum_bytes:
+            raise BaselineError(f"dependency file is oversized: {path}")
+        if (
+            len(raw) != before_handle.st_size
+            or _file_identity(before_handle) != _file_identity(after_handle)
+        ):
+            raise BaselineError(f"opened dependency file changed while reading: {path}")
     except OSError as error:
-        raise BaselineError(f"dependency baseline file cannot be read: {path}") from error
-    if len(raw) != info.st_size:
-        raise BaselineError(f"dependency baseline file changed while reading: {path}")
-    return raw
+        raise BaselineError(f"dependency file cannot be read: {path}") from error
+    finally:
+        try:
+            os.close(descriptor)
+        except OSError as error:
+            raise BaselineError(f"dependency file handle cannot be closed: {path}") from error
+
+    assert after_handle is not None
+    try:
+        after_path = os.lstat(path)
+    except OSError as error:
+        raise BaselineError(f"dependency file disappeared after reading: {path}") from error
+    if (
+        stat.S_ISLNK(after_path.st_mode)
+        or _is_reparse(after_path)
+        or _path_handle_identity(after_path) != _path_handle_identity(after_handle)
+    ):
+        raise BaselineError(f"dependency file identity changed after reading: {path}")
+    _revalidate_ancestor_chain(ancestors)
+    return FileSnapshot(
+        path,
+        raw,
+        _file_identity(after_path),
+        ancestors,
+        maximum_bytes,
+        root,
+    )
+
+
+def _validated_regular_file(path: Path, *, maximum_bytes: int) -> bytes:
+    if not isinstance(path, Path) or not path.is_absolute():
+        raise BaselineError("dependency baseline path must be absolute")
+    return read_regular_snapshot(
+        path, maximum_bytes=maximum_bytes, root=path.parent
+    ).raw
 
 
 def _git_environment(git_executable: Path) -> dict[str, str]:
     allowed = ("SystemRoot", "WINDIR", "ComSpec", "PATHEXT", "TEMP", "TMP", "TMPDIR")
     folded = {key.casefold(): value for key, value in os.environ.items()}
     environment = {key: folded[key.casefold()] for key in allowed if key.casefold() in folded}
     temporary = str(Path(tempfile.gettempdir()).resolve())
     environment["HOME"] = temporary
     environment["USERPROFILE"] = temporary
     if os.name == "nt":
@@ -682,69 +997,979 @@ def derive_baseline_graph(
 ) -> DependencyGraph:
     commit = _require_commit(baseline_commit)
     try:
         root = repository_root.resolve(strict=True)
     except OSError as error:
         raise BaselineError("repository root cannot be resolved") from error
     raw = _run_git_archive(root, baseline_commit=commit, git_executable=git_executable)
     return scan_sources(_sources_from_archive(raw))
 
 
+def _validated_directory(path: Path, *, description: str) -> tuple[int, ...]:
+    try:
+        info = os.lstat(path)
+    except OSError as error:
+        raise BaselineError(f"{description} cannot be inspected: {path}") from error
+    if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
+        raise BaselineError(f"{description} is not a nonreparse directory: {path}")
+    return _directory_identity(info)
+
+
 def validate_write_destination(repository_root: Path, destination: Path) -> Path:
     if not isinstance(destination, Path) or not destination.is_absolute():
         raise BaselineError("--write must explicitly name an absolute baseline path")
-    try:
-        root = repository_root.resolve(strict=True)
-        architecture = (root / "docs" / "architecture").resolve(strict=True)
-    except OSError as error:
-        raise BaselineError("docs/architecture must already be a real directory") from error
-    architecture_info = os.lstat(architecture)
-    if (
-        stat.S_ISLNK(architecture_info.st_mode)
-        or _is_reparse(architecture_info)
-        or not stat.S_ISDIR(architecture_info.st_mode)
-    ):
-        raise BaselineError("docs/architecture is not a regular directory")
+    if not isinstance(repository_root, Path) or not repository_root.is_absolute():
+        raise BaselineError("repository root must be absolute for --write")
+    root = Path(os.path.abspath(repository_root))
+    for component in reversed(root.parents):
+        if component != component.parent:
+            _validated_directory(component, description="repository ancestor")
+    _validated_directory(root, description="repository root")
+    docs = root / "docs"
+    _validated_directory(docs, description="baseline docs ancestor")
+    architecture = docs / "architecture"
+    _validated_directory(architecture, description="baseline architecture directory")
     expected = architecture / "dependency-baseline.toml"
-    candidate = destination.resolve(strict=False)
+    candidate = Path(os.path.abspath(destination))
     if os.path.normcase(str(candidate)) != os.path.normcase(str(expected)):
         raise BaselineError("--write may name only docs/architecture/dependency-baseline.toml")
     if os.path.lexists(candidate):
         info = os.lstat(candidate)
         if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISREG(info.st_mode):
             raise BaselineError("baseline destination is not a regular file")
     return candidate
 
 
+if os.name == "nt":
+    class _WindowsDirectoryInformation(ctypes.Structure):
+        _fields_ = (
+            ("dwFileAttributes", wintypes.DWORD),
+            ("ftCreationTime", wintypes.FILETIME),
+            ("ftLastAccessTime", wintypes.FILETIME),
+            ("ftLastWriteTime", wintypes.FILETIME),
+            ("dwVolumeSerialNumber", wintypes.DWORD),
+            ("nFileSizeHigh", wintypes.DWORD),
+            ("nFileSizeLow", wintypes.DWORD),
+            ("nNumberOfLinks", wintypes.DWORD),
+            ("nFileIndexHigh", wintypes.DWORD),
+            ("nFileIndexLow", wintypes.DWORD),
+        )
+
+
+    class _WindowsFileId128(ctypes.Structure):
+        _fields_ = (("ByteIdentifier", ctypes.c_ubyte * 16),)
+
+
+    class _WindowsFileIdInformation(ctypes.Structure):
+        _fields_ = (
+            ("VolumeSerialNumber", ctypes.c_ulonglong),
+            ("FileId", _WindowsFileId128),
+        )
+
+
+    class _WindowsUnicodeString(ctypes.Structure):
+        _fields_ = (
+            ("Length", wintypes.USHORT),
+            ("MaximumLength", wintypes.USHORT),
+            ("Buffer", wintypes.LPWSTR),
+        )
+
+
+    class _WindowsObjectAttributes(ctypes.Structure):
+        _fields_ = (
+            ("Length", wintypes.ULONG),
+            ("RootDirectory", wintypes.HANDLE),
+            ("ObjectName", ctypes.POINTER(_WindowsUnicodeString)),
+            ("Attributes", wintypes.ULONG),
+            ("SecurityDescriptor", wintypes.LPVOID),
+            ("SecurityQualityOfService", wintypes.LPVOID),
+        )
+
+
+    class _WindowsIOStatusValue(ctypes.Union):
+        _fields_ = (("Status", wintypes.LONG), ("Pointer", wintypes.LPVOID))
+
+
+    class _WindowsIOStatusBlock(ctypes.Structure):
+        _anonymous_ = ("value",)
+        _fields_ = (("value", _WindowsIOStatusValue), ("Information", ctypes.c_size_t))
+
+
+    class _WindowsFileRenameInformation(ctypes.Structure):
+        _fields_ = (
+            ("ReplaceIfExists", ctypes.c_ubyte),
+            ("RootDirectory", wintypes.HANDLE),
+            ("FileNameLength", wintypes.DWORD),
+            ("FileName", wintypes.WCHAR * 1),
+        )
+
+
+    class _WindowsFileDispositionInformation(ctypes.Structure):
+        _fields_ = (("DeleteFile", ctypes.c_ubyte),)
+
+
+def _windows_directory_api() -> tuple[Any, Any, Any, Any]:
+    if os.name != "nt":
+        raise BaselineError("Windows directory handle APIs are unavailable")
+    try:
+        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
+        create = kernel32.CreateFileW
+        create.argtypes = (
+            wintypes.LPCWSTR,
+            wintypes.DWORD,
+            wintypes.DWORD,
+            wintypes.LPVOID,
+            wintypes.DWORD,
+            wintypes.DWORD,
+            wintypes.HANDLE,
+        )
+        create.restype = wintypes.HANDLE
+        information = kernel32.GetFileInformationByHandle
+        information.argtypes = (
+            wintypes.HANDLE,
+            ctypes.POINTER(_WindowsDirectoryInformation),
+        )
+        information.restype = wintypes.BOOL
+        extended_information = kernel32.GetFileInformationByHandleEx
+        extended_information.argtypes = (
+            wintypes.HANDLE,
+            ctypes.c_int,
+            wintypes.LPVOID,
+            wintypes.DWORD,
+        )
+        extended_information.restype = wintypes.BOOL
+        close = kernel32.CloseHandle
+        close.argtypes = (wintypes.HANDLE,)
+        close.restype = wintypes.BOOL
+    except Exception as error:
+        raise BaselineError("Windows directory handle APIs are unavailable") from error
+    return create, information, extended_information, close
+
+
+def _windows_directory_handle_identity(handle: int, path: Path) -> tuple[int, bytes]:
+    _, information, extended_information, _ = _windows_directory_api()
+    value = _WindowsDirectoryInformation()
+    try:
+        succeeded = information(wintypes.HANDLE(handle), ctypes.byref(value))
+    except Exception as error:
+        raise BaselineError(f"baseline directory handle cannot be inspected: {path}") from error
+    if not succeeded:
+        error = ctypes.get_last_error()
+        raise BaselineError(
+            f"baseline directory handle cannot be inspected: {path}"
+        ) from OSError(error, os.strerror(error), str(path))
+    attributes = int(value.dwFileAttributes)
+    if not attributes & 0x10 or attributes & _REPARSE_ATTRIBUTE:
+        raise BaselineError(f"baseline directory handle is not nonreparse: {path}")
+    identity = _WindowsFileIdInformation()
+    try:
+        succeeded = extended_information(
+            wintypes.HANDLE(handle),
+            18,
+            ctypes.byref(identity),
+            ctypes.sizeof(identity),
+        )
+    except Exception as error:
+        raise BaselineError(f"baseline directory identity cannot be inspected: {path}") from error
+    if not succeeded:
+        error = ctypes.get_last_error()
+        raise BaselineError(
+            f"baseline directory identity cannot be inspected: {path}"
+        ) from OSError(error, os.strerror(error), str(path))
+    file_id = bytes(identity.FileId.ByteIdentifier)
+    return int(identity.VolumeSerialNumber), file_id
+
+
+def _windows_open_directory(path: Path) -> tuple[int, tuple[int, bytes]]:
+    create, _, _, _ = _windows_directory_api()
+    try:
+        handle = create(
+            str(path),
+            0x00000020 | 0x00000080 | 0x00100000,
+            0x00000001 | 0x00000002 | 0x00000004,
+            None,
+            3,
+            0x02000000 | 0x00200000,
+            None,
+        )
+    except Exception as error:
+        raise BaselineError(f"baseline directory handle cannot be opened: {path}") from error
+    invalid = ctypes.c_void_p(-1).value
+    if not handle or int(handle) == invalid:
+        error = ctypes.get_last_error()
+        raise BaselineError(
+            f"baseline directory handle cannot be opened: {path}"
+        ) from OSError(error, os.strerror(error), str(path))
+    numeric = int(handle)
+    try:
+        return numeric, _windows_directory_handle_identity(numeric, path)
+    except BaseException as body_error:
+        try:
+            _windows_close_directory(numeric)
+        except BaselineError as cleanup_error:
+            raise _aggregate_errors(
+                "baseline directory inspection and close both failed",
+                (body_error, cleanup_error),
+                retained_owners=cleanup_error.retained_owners,
+            ) from body_error
+        raise
+
+
+def _windows_close_directory(handle: int) -> None:
+    try:
+        _, _, _, close = _windows_directory_api()
+        succeeded = close(wintypes.HANDLE(handle))
+    except Exception as error:
+        raise _aggregate_errors(
+            "baseline directory handle close outcome is ambiguous",
+            (error,),
+            retained_owners=(handle,),
+        ) from error
+    if succeeded:
+        return
+    error = ctypes.get_last_error()
+    cause = OSError(error, os.strerror(error))
+    raise _aggregate_errors(
+        "baseline directory handle close outcome is ambiguous",
+        (cause,),
+        retained_owners=(handle,),
+    ) from cause
+
+
+def _windows_file_api() -> tuple[Any, Any, Any, Any, Any]:
+    if os.name != "nt":
+        raise BaselineError("Windows handle-relative file APIs are unavailable")
+    try:
+        ntdll = ctypes.WinDLL("ntdll")
+        create = ntdll.NtCreateFile
+        create.argtypes = (
+            ctypes.POINTER(wintypes.HANDLE),
+            wintypes.DWORD,
+            ctypes.POINTER(_WindowsObjectAttributes),
+            ctypes.POINTER(_WindowsIOStatusBlock),
+            wintypes.LPVOID,
+            wintypes.ULONG,
+            wintypes.ULONG,
+            wintypes.ULONG,
+            wintypes.ULONG,
+            wintypes.LPVOID,
+            wintypes.ULONG,
+        )
+        create.restype = wintypes.LONG
+        set_information = ntdll.NtSetInformationFile
+        set_information.argtypes = (
+            wintypes.HANDLE,
+            ctypes.POINTER(_WindowsIOStatusBlock),
+            wintypes.LPVOID,
+            wintypes.ULONG,
+            ctypes.c_int,
+        )
+        set_information.restype = wintypes.LONG
+        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
+        write = kernel32.WriteFile
+        write.argtypes = (
+            wintypes.HANDLE,
+            wintypes.LPCVOID,
+            wintypes.DWORD,
+            wintypes.LPDWORD,
+            wintypes.LPVOID,
+        )
+        write.restype = wintypes.BOOL
+        flush = kernel32.FlushFileBuffers
+        flush.argtypes = (wintypes.HANDLE,)
+        flush.restype = wintypes.BOOL
+        close = kernel32.CloseHandle
+        close.argtypes = (wintypes.HANDLE,)
+        close.restype = wintypes.BOOL
+    except Exception as error:
+        raise BaselineError("Windows handle-relative file APIs are unavailable") from error
+    return create, set_information, write, flush, close
+
+
+def _validated_relative_name(name: str) -> str:
+    if (
+        type(name) is not str
+        or not name
+        or name in {".", ".."}
+        or any(character in name for character in ("/", "\\", ":", "\x00"))
+    ):
+        raise BaselineError("baseline mutation name must be one relative component")
+    return name
+
+
+def _windows_create_relative_file(
+    directory_handle: int,
+    name: str,
+    *,
+    owner: "_StagedBaseline | None" = None,
+) -> int:
+    name = _validated_relative_name(name)
+    create, _, _, _, _ = _windows_file_api()
+    encoded = name.encode("utf-16-le")
+    if len(encoded) > 0xFFFE:
+        raise BaselineError("baseline temporary name is too long")
+    name_buffer = ctypes.create_unicode_buffer(name)
+    unicode_name = _WindowsUnicodeString(
+        len(encoded), len(encoded), ctypes.cast(name_buffer, wintypes.LPWSTR)
+    )
+    attributes = _WindowsObjectAttributes(
+        ctypes.sizeof(_WindowsObjectAttributes),
+        wintypes.HANDLE(directory_handle),
+        ctypes.pointer(unicode_name),
+        0x40,
+        None,
+        None,
+    )
+    status_block = _WindowsIOStatusBlock()
+    handle = wintypes.HANDLE()
+    candidate = owner or _StagedBaseline(name, None)
+    try:
+        status = int(
+            create(
+                ctypes.byref(handle),
+                0x00000002 | 0x00000080 | 0x00010000 | 0x00100000,
+                ctypes.byref(attributes),
+                ctypes.byref(status_block),
+                None,
+                0x80,
+                0,
+                2,
+                0x20 | 0x40,
+                None,
+                0,
+            )
+        )
+    except Exception as error:
+        invalid = ctypes.c_void_p(-1).value
+        if handle.value and int(handle.value) != invalid:
+            candidate.handle = int(handle.value)
+            candidate.state = "open"
+        failure = BaselineError("baseline temporary file could not be created")
+        if owner is None and candidate.handle is not None:
+            try:
+                _cleanup_windows_temporary(candidate)
+            except BaselineError as cleanup_error:
+                raise _aggregate_errors(
+                    "baseline temporary creation and cleanup both failed",
+                    (failure, cleanup_error),
+                    retained_owners=cleanup_error.retained_owners,
+                ) from error
+        raise failure from error
+    invalid = ctypes.c_void_p(-1).value
+    if handle.value and int(handle.value) != invalid:
+        candidate.handle = int(handle.value)
+        candidate.state = "open"
+    if (
+        status != 0
+        or int(status_block.Status) != 0
+        or int(status_block.Information) != 2
+        or not handle.value
+        or int(handle.value) == invalid
+    ):
+        failure = BaselineError("baseline temporary creation returned malformed status")
+        if owner is None and candidate.handle is not None:
+            try:
+                _cleanup_windows_temporary(candidate)
+            except BaselineError as cleanup_error:
+                raise _aggregate_errors(
+                    "malformed temporary creation and cleanup both failed",
+                    (failure, cleanup_error),
+                    retained_owners=cleanup_error.retained_owners,
+                ) from failure
+        raise failure
+    return int(handle.value)
+
+
+def _windows_write_file(handle: int, raw: bytes) -> None:
+    _, _, write, _, _ = _windows_file_api()
+    offset = 0
+    while offset < len(raw):
+        chunk = raw[offset : offset + 0xFFFFFFFF]
+        buffer = ctypes.create_string_buffer(chunk)
+        written = wintypes.DWORD()
+        try:
+            succeeded = write(
+                wintypes.HANDLE(handle),
+                ctypes.byref(buffer),
+                len(chunk),
+                ctypes.byref(written),
+                None,
+            )
+        except Exception as error:
+            raise BaselineError("baseline temporary write failed") from error
+        count = int(written.value)
+        if not succeeded or count <= 0 or count > len(chunk):
+            raise BaselineError("baseline temporary write returned malformed length")
+        offset += count
+
+
+def _windows_flush_file(handle: int) -> None:
+    _, _, _, flush, _ = _windows_file_api()
+    try:
+        succeeded = flush(wintypes.HANDLE(handle))
+    except Exception as error:
+        raise BaselineError("baseline temporary flush failed") from error
+    if not succeeded:
+        error = ctypes.get_last_error()
+        raise BaselineError("baseline temporary flush failed") from OSError(
+            error, os.strerror(error)
+        )
+
+
+def _windows_close_file(handle: int) -> None:
+    _, _, _, _, close = _windows_file_api()
+    try:
+        succeeded = close(wintypes.HANDLE(handle))
+    except Exception as error:
+        raise BaselineError("baseline temporary handle cannot be closed") from error
+    if not succeeded:
+        error = ctypes.get_last_error()
+        raise BaselineError("baseline temporary handle cannot be closed") from OSError(
+            error, os.strerror(error)
+        )
+
+
+def _windows_rename_relative_file(
+    handle: int, directory_handle: int, destination_name: str
+) -> None:
+    destination_name = _validated_relative_name(destination_name)
+    _, set_information, _, _, _ = _windows_file_api()
+    encoded = destination_name.encode("utf-16-le")
+    name_offset = _WindowsFileRenameInformation.FileName.offset
+    buffer = ctypes.create_string_buffer(name_offset + len(encoded))
+    information = ctypes.cast(
+        buffer, ctypes.POINTER(_WindowsFileRenameInformation)
+    ).contents
+    information.ReplaceIfExists = 1
+    information.RootDirectory = wintypes.HANDLE(directory_handle)
+    information.FileNameLength = len(encoded)
+    ctypes.memmove(ctypes.addressof(buffer) + name_offset, encoded, len(encoded))
+    status_block = _WindowsIOStatusBlock()
+    try:
+        status = int(
+            set_information(
+                wintypes.HANDLE(handle),
+                ctypes.byref(status_block),
+                ctypes.byref(buffer),
+                len(buffer),
+                10,
+            )
+        )
+    except Exception as error:
+        raise BaselineError("baseline handle-relative replacement failed") from error
+    if status != 0 or int(status_block.Status) != 0:
+        raise BaselineError("baseline handle-relative replacement returned malformed status")
+
+
+def _windows_dispose_relative_file(handle: int) -> None:
+    _, set_information, _, _, _ = _windows_file_api()
+    information = _WindowsFileDispositionInformation(1)
+    status_block = _WindowsIOStatusBlock()
+    try:
+        status = int(
+            set_information(
+                wintypes.HANDLE(handle),
+                ctypes.byref(status_block),
+                ctypes.byref(information),
+                ctypes.sizeof(information),
+                13,
+            )
+        )
+    except Exception as error:
+        raise BaselineError("baseline temporary disposition failed") from error
+    if status != 0 or int(status_block.Status) != 0:
+        raise BaselineError("baseline temporary disposition returned malformed status")
+
+
+class _StagedBaseline:
+    __slots__ = ("name", "handle", "renamed", "state")
+
+    def __init__(self, name: str, handle: int | None) -> None:
+        self.name = name
+        self.handle = handle
+        self.renamed = False
+        self.state = "open" if handle is not None else "unacquired"
+
+
+def _cleanup_windows_temporary(temporary: _StagedBaseline) -> None:
+    if temporary.state == "close_attempted":
+        raise BaselineError(
+            "baseline temporary handle close outcome is ambiguous",
+            retained_owners=(temporary,),
+        )
+    if temporary.handle is None:
+        temporary.state = "closed"
+        return
+    failures: list[BaseException] = []
+    if not temporary.renamed and temporary.state != "deletion_armed":
+        for _ in range(2):
+            try:
+                _windows_dispose_relative_file(temporary.handle)
+            except BaseException as error:
+                failures.append(error)
+            else:
+                temporary.state = "deletion_armed"
+                break
+        if temporary.state != "deletion_armed":
+            raise _aggregate_errors(
+                "baseline temporary deletion could not be armed",
+                failures,
+                retained_owners=(temporary,),
+            ) from failures[0]
+
+    handle = temporary.handle
+    temporary.handle = None
+    temporary.state = "close_attempted"
+    try:
+        _windows_close_file(handle)
+    except BaseException as error:
+        failures.append(error)
+        raise _aggregate_errors(
+            "baseline temporary handle close outcome is ambiguous",
+            failures,
+            retained_owners=(temporary,),
+        ) from error
+    temporary.state = "closed"
+
+
+def _write_staged_bytes(handle: int, raw: bytes, *, windows: bool) -> None:
+    if type(raw) is not bytes:
+        raise BaselineError("dependency baseline content must be bytes")
+    if windows:
+        _windows_write_file(handle, raw)
+        _windows_flush_file(handle)
+        return
+    offset = 0
+    while offset < len(raw):
+        written = os.write(handle, raw[offset:])
+        if written <= 0:
+            raise OSError("baseline temporary write made no progress")
+        offset += written
+    os.fsync(handle)
+
+
+def _posix_staged_entry_matches(
+    directory_descriptor: int, temporary: _StagedBaseline
+) -> bool:
+    if temporary.handle is None:
+        return False
+    try:
+        handle_info = os.fstat(temporary.handle)
+        path_info = os.stat(
+            temporary.name,
+            dir_fd=directory_descriptor,
+            follow_symlinks=False,
+        )
+    except FileNotFoundError:
+        return False
+    except OSError as error:
+        raise BaselineError("POSIX staged baseline identity cannot be inspected") from error
+    return (
+        stat.S_ISREG(handle_info.st_mode)
+        and not stat.S_ISLNK(path_info.st_mode)
+        and stat.S_ISREG(path_info.st_mode)
+        and _path_handle_identity(path_info) == _path_handle_identity(handle_info)
+    )
+
+
+def _replace_staged_file(
+    transaction: "_BoundBaselineDirectory",
+    temporary: _StagedBaseline,
+    destination_name: str,
+) -> None:
+    if os.name == "nt":
+        if temporary.handle is None or transaction._architecture_handle is None:
+            raise BaselineError("Windows baseline replacement handles are absent")
+        _windows_rename_relative_file(
+            temporary.handle,
+            transaction._architecture_handle,
+            destination_name,
+        )
+        return
+    if transaction._architecture_descriptor is None:
+        raise BaselineError("POSIX baseline replacement descriptor is absent")
+    if temporary.handle is None:
+        raise BaselineError("POSIX staged baseline descriptor is absent")
+    if not _posix_staged_entry_matches(
+        transaction._architecture_descriptor, temporary
+    ):
+        raise BaselineError("POSIX staged baseline entry no longer names its descriptor")
+    os.replace(
+        temporary.name,
+        destination_name,
+        src_dir_fd=transaction._architecture_descriptor,
+        dst_dir_fd=transaction._architecture_descriptor,
+    )
+    try:
+        after_handle = os.fstat(temporary.handle)
+        after_path = os.stat(
+            destination_name,
+            dir_fd=transaction._architecture_descriptor,
+            follow_symlinks=False,
+        )
+    except OSError as error:
+        raise BaselineError("POSIX published baseline identity cannot be inspected") from error
+    if _path_handle_identity(after_path) != _path_handle_identity(after_handle):
+        raise BaselineError("POSIX published baseline no longer names its descriptor")
+
+
+class _BoundBaselineDirectory:
+    def __init__(self, repository_root: Path, destination: Path) -> None:
+        self.repository_root = repository_root
+        self.destination = destination
+        self.root = repository_root
+        self.docs = repository_root / "docs"
+        self.architecture = self.docs / "architecture"
+        self._windows_handles: list[tuple[Path, int, tuple[int, bytes]]] = []
+        self._posix_descriptors: list[
+            tuple[Path, int, tuple[int, int] | None]
+        ] = []
+        self._windows_close_attempted: set[int] = set()
+        self._posix_close_attempted: set[int] = set()
+        self._architecture_handle: int | None = None
+        self._architecture_descriptor: int | None = None
+        self._temporaries: list[_StagedBaseline] = []
+        self._validated_directories: tuple[tuple[Path, tuple[int, ...]], ...] = ()
+        self._validated_windows_identities: tuple[
+            tuple[Path, tuple[int, bytes]], ...
+        ] = ()
+
+    def __enter__(self) -> "_BoundBaselineDirectory":
+        validate_write_destination(self.repository_root, self.destination)
+        self._validated_directories = tuple(
+            (path, _validated_directory(path, description="baseline write ancestor"))
+            for path in (self.root, self.docs, self.architecture)
+        )
+        try:
+            if os.name == "nt":
+                self._validated_windows_identities = tuple(
+                    (path, self._windows_path_identity(path))
+                    for path in (self.root, self.docs, self.architecture)
+                )
+                self._bind_windows()
+            else:
+                self._bind_posix()
+            self.reverify()
+            return self
+        except BaseException as body_error:
+            try:
+                self.close()
+            except BaselineError as cleanup_error:
+                raise _aggregate_errors(
+                    "baseline transaction setup and cleanup both failed",
+                    (body_error, cleanup_error),
+                    retained_owners=cleanup_error.retained_owners,
+                ) from body_error
+            raise
+
+    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
+        try:
+            self.close()
+        except BaselineError as cleanup_error:
+            if exc is None:
+                raise
+            assert isinstance(exc, BaseException)
+            raise _aggregate_errors(
+                "dependency baseline operation and cleanup both failed",
+                (exc, cleanup_error),
+                retained_owners=cleanup_error.retained_owners,
+            ) from exc
+
+    def _bind_windows(self) -> None:
+        for path in (self.root, self.docs, self.architecture):
+            handle, identity = _windows_open_directory(path)
+            self._windows_handles.append((path, handle, identity))
+        self._architecture_handle = self._windows_handles[-1][1]
+
+    @staticmethod
+    def _windows_path_identity(path: Path) -> tuple[int, bytes]:
+        handle, identity = _windows_open_directory(path)
+        _windows_close_directory(handle)
+        return identity
+
+    def _bind_posix(self) -> None:
+        if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
+            raise BaselineError("secure POSIX directory primitives are unavailable")
+        required = (os.open, os.replace, os.stat, os.unlink)
+        if any(function not in os.supports_dir_fd for function in required):
+            raise BaselineError("secure POSIX directory-relative operations are unavailable")
+        if os.stat not in os.supports_follow_symlinks:
+            raise BaselineError("secure POSIX no-follow stat is unavailable")
+        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
+
+        def bind(
+            path: Path, name: Path | str, *, parent_descriptor: int | None = None
+        ) -> int:
+            if parent_descriptor is None:
+                descriptor = os.open(name, flags)
+            else:
+                descriptor = os.open(name, flags, dir_fd=parent_descriptor)
+            self._posix_descriptors.append((path, descriptor, None))
+            info = os.fstat(descriptor)
+            identity = (int(info.st_dev), int(info.st_ino))
+            self._posix_descriptors[-1] = (path, descriptor, identity)
+            return descriptor
+
+        try:
+            root_descriptor = bind(self.root, self.root)
+            docs_descriptor = bind(
+                self.docs,
+                "docs",
+                parent_descriptor=root_descriptor,
+            )
+            architecture_descriptor = bind(
+                self.architecture,
+                "architecture",
+                parent_descriptor=docs_descriptor,
+            )
+            self._architecture_descriptor = architecture_descriptor
+        except OSError as error:
+            raise BaselineError("baseline directory chain could not be securely bound") from error
+
+    def reverify(self) -> None:
+        validate_write_destination(self.repository_root, self.destination)
+        if not self._validated_directories:
+            raise BaselineError("baseline directory intent identities are absent")
+        for path, expected_path_identity in self._validated_directories:
+            current_path_identity = _validated_directory(
+                path, description="baseline write ancestor"
+            )
+            if current_path_identity != expected_path_identity:
+                raise BaselineError(
+                    f"baseline directory changed after intent validation: {path}"
+                )
+        if os.name == "nt":
+            if len(self._validated_windows_identities) != len(self._windows_handles):
+                raise BaselineError("baseline Windows intent identities are incomplete")
+            for index, (path, handle, expected_handle) in enumerate(
+                self._windows_handles
+            ):
+                intended_path, intended_identity = self._validated_windows_identities[index]
+                if intended_path != path:
+                    raise BaselineError("baseline directory binding order changed")
+                handle_identity = _windows_directory_handle_identity(handle, path)
+                current_path_identity = self._windows_path_identity(path)
+                if (
+                    handle_identity != expected_handle
+                    or handle_identity != intended_identity
+                    or current_path_identity != intended_identity
+                ):
+                    raise BaselineError(f"held baseline directory identity changed: {path}")
+                info = os.lstat(path)
+                if (
+                    stat.S_ISLNK(info.st_mode)
+                    or _is_reparse(info)
+                    or not stat.S_ISDIR(info.st_mode)
+                ):
+                    raise BaselineError(
+                        f"baseline directory path no longer names its handle: {path}"
+                    )
+            return
+        for index, (path, descriptor, bound_identity) in enumerate(
+            self._posix_descriptors
+        ):
+            intended_path, intended_identity = self._validated_directories[index]
+            intended_device_inode = (intended_identity[0], intended_identity[1])
+            if intended_path != path:
+                raise BaselineError("baseline directory binding order changed")
+            handle_info = os.fstat(descriptor)
+            path_info = os.lstat(path)
+            if (
+                bound_identity is None
+                or bound_identity != intended_device_inode
+                or (int(handle_info.st_dev), int(handle_info.st_ino))
+                != intended_device_inode
+                or (int(path_info.st_dev), int(path_info.st_ino))
+                != intended_device_inode
+                or stat.S_ISLNK(path_info.st_mode)
+                or not stat.S_ISDIR(path_info.st_mode)
+            ):
+                raise BaselineError(
+                    f"baseline directory path no longer names its descriptor: {path}"
+                )
+
+    def stage(self, raw: bytes) -> _StagedBaseline:
+        self.reverify()
+        name = f".{self.destination.name}.{uuid.uuid4().hex}.tmp"
+        if os.name == "nt":
+            if self._architecture_handle is None:
+                raise BaselineError("Windows baseline directory handle is absent")
+            temporary = _StagedBaseline(name, None)
+            self._temporaries.append(temporary)
+            handle = _windows_create_relative_file(
+                self._architecture_handle,
+                name,
+                owner=temporary,
+            )
+            if temporary.handle != handle or temporary.state != "open":
+                raise BaselineError("Windows baseline temporary ownership was not retained")
+            self.reverify()
+            _write_staged_bytes(handle, raw, windows=True)
+            self.reverify()
+            return temporary
+        if self._architecture_descriptor is None:
+            raise BaselineError("POSIX baseline directory descriptor is absent")
+        flags = (
+            os.O_WRONLY
+            | os.O_CREAT
+            | os.O_EXCL
+            | os.O_NOFOLLOW
+            | getattr(os, "O_CLOEXEC", 0)
+        )
+        try:
+            descriptor = os.open(
+                name, flags, 0o600, dir_fd=self._architecture_descriptor
+            )
+        except OSError as error:
+            raise BaselineError("baseline temporary file could not be created") from error
+        temporary = _StagedBaseline(name, descriptor)
+        self._temporaries.append(temporary)
+        self.reverify()
+        _write_staged_bytes(descriptor, raw, windows=False)
+        self.reverify()
+        return temporary
+
+    def replace(self, temporary: _StagedBaseline) -> None:
+        if temporary not in self._temporaries:
+            raise BaselineError("baseline temporary ownership is invalid")
+        self.reverify()
+        _replace_staged_file(self, temporary, self.destination.name)
+        temporary.renamed = True
+        self._cleanup_temporary(temporary)
+        if os.name != "nt" and self._architecture_descriptor is not None:
+            os.fsync(self._architecture_descriptor)
+        self.reverify()
+
+    def _cleanup_temporary(self, temporary: _StagedBaseline) -> None:
+        if temporary not in self._temporaries:
+            return
+        if os.name == "nt":
+            _cleanup_windows_temporary(temporary)
+        else:
+            if temporary.state == "close_attempted":
+                raise BaselineError(
+                    "POSIX baseline descriptor close outcome is ambiguous",
+                    retained_owners=(temporary,),
+                )
+            failures: list[BaseException] = []
+            # Failure cleanup is close-only because a POSIX name can be rebound
+            # between any identity check and a later unlink syscall.
+            if temporary.handle is not None:
+                descriptor = temporary.handle
+                temporary.handle = None
+                temporary.state = "close_attempted"
+                try:
+                    os.close(descriptor)
+                except OSError as error:
+                    failures.append(error)
+                else:
+                    temporary.state = "closed"
+            if failures:
+                raise _aggregate_errors(
+                    "POSIX baseline temporary cleanup failed",
+                    failures,
+                    retained_owners=(temporary,),
+                ) from failures[0]
+        self._temporaries.remove(temporary)
+
+    def close(self) -> None:
+        failures: list[BaseException] = []
+        for temporary in tuple(self._temporaries):
+            try:
+                self._cleanup_temporary(temporary)
+            except BaseException as error:
+                failures.append(error)
+        for entry in tuple(reversed(self._posix_descriptors)):
+            descriptor = entry[1]
+            if descriptor in self._posix_close_attempted:
+                failures.append(
+                    BaselineError(
+                        "POSIX directory descriptor close outcome is ambiguous",
+                        retained_owners=(entry,),
+                    )
+                )
+                continue
+            self._posix_close_attempted.add(descriptor)
+            try:
+                os.close(descriptor)
+            except OSError as error:
+                failures.append(
+                    _aggregate_errors(
+                        "POSIX directory descriptor close outcome is ambiguous",
+                        (error,),
+                        retained_owners=(entry,),
+                    )
+                )
+            else:
+                self._posix_descriptors.remove(entry)
+                self._posix_close_attempted.remove(descriptor)
+        for entry in tuple(reversed(self._windows_handles)):
+            handle = entry[1]
+            if handle in self._windows_close_attempted:
+                failures.append(
+                    BaselineError(
+                        "Windows directory handle close outcome is ambiguous",
+                        retained_owners=(entry,),
+                    )
+                )
+                continue
+            self._windows_close_attempted.add(handle)
+            try:
+                _windows_close_directory(handle)
+            except BaselineError as error:
+                failures.append(error)
+            else:
+                self._windows_handles.remove(entry)
+                self._windows_close_attempted.remove(handle)
+        self._architecture_descriptor = None
+        self._architecture_handle = None
+        if failures:
+            retained: list[object] = []
+            if self._temporaries or self._posix_descriptors or self._windows_handles:
+                retained.append(self)
+            for failure in failures:
+                if isinstance(failure, BaselineError):
+                    retained.extend(failure.retained_owners)
+            raise _aggregate_errors(
+                "dependency baseline transaction cleanup failed",
+                failures,
+                retained_owners=tuple(dict.fromkeys(retained)),
+            ) from failures[0]
+
+
 def write_baseline(destination: Path, raw: bytes) -> None:
-    candidate = destination.parent / f".{destination.name}.{uuid.uuid4().hex}.tmp"
+    if not isinstance(destination, Path) or not destination.is_absolute():
+        raise BaselineError("dependency baseline destination must be absolute")
+    if type(raw) is not bytes or len(raw) > MAXIMUM_BASELINE_BYTES:
+        raise BaselineError("dependency baseline write bytes are invalid or oversized")
+    try:
+        repository_root = destination.parents[2]
+    except IndexError as error:
+        raise BaselineError("dependency baseline destination has no repository root") from error
+    validated = validate_write_destination(repository_root, destination)
     try:
-        with candidate.open("xb") as stream:
-            stream.write(raw)
-            stream.flush()
-            os.fsync(stream.fileno())
-        os.replace(candidate, destination)
+        with _BoundBaselineDirectory(repository_root, validated) as transaction:
+            temporary = transaction.stage(raw)
+            transaction.replace(temporary)
+    except BaselineError:
+        raise
     except OSError as error:
         raise BaselineError("dependency baseline could not be written atomically") from error
-    finally:
-        try:
-            candidate.unlink()
-        except FileNotFoundError:
-            pass
 
 
 def check_baseline(destination: Path, expected: bytes) -> None:
     actual = _validated_regular_file(destination, maximum_bytes=MAXIMUM_BASELINE_BYTES)
     parsed = parse_baseline_bytes(actual)
     if parsed.baseline_commit != BASELINE_COMMIT:
         raise BaselineError("dependency baseline commit differs from the approved lock")
-    if actual != expected:
+    exact_crlf_checkout = expected.replace(b"\n", b"\r\n")
+    if actual != expected and actual != exact_crlf_checkout:
         raise BaselineError("dependency baseline bytes differ from deterministic generation")
 
 
 def parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
     parser = argparse.ArgumentParser(description=__doc__)
     commands = parser.add_mutually_exclusive_group()
     commands.add_argument("--check", action="store_true", help="verify the baseline (default)")
     commands.add_argument(
         "--write",
         type=Path,
