# Review package: 88a553c34f4522439d04e1f49a2c2e88e97c1927..94c79c7e0b92429aa467e704c27c42dcdbd5c9ea

## Commits
94c79c7 fix(architecture): support OneDrive snapshots

## Files changed
 .gitattributes                          |   3 +
 tests/test_stabilization_boundaries.py  | 113 ++++++++++++++++++++++++++
 tools/check_stabilization_boundaries.py |  12 ++-
 tools/generate_dependency_baseline.py   | 138 +++++++++++++++++++++++++++-----
 4 files changed, 238 insertions(+), 28 deletions(-)

## Diff
diff --git a/.gitattributes b/.gitattributes
index 0f82859..136f438 100644
--- a/.gitattributes
+++ b/.gitattributes
@@ -38,10 +38,13 @@
 /experiments/results/legal-responder-raise-h4-factorized-affine-v1.json -text
 /experiments/configs/legal-h4-factorized-affine-confirmation-v1.json -text
 /experiments/results/legal-h4-factorized-affine-confirmation-v1.json -text
 /experiments/configs/full-width-river-capacity-preflight-v1.json -text
 /experiments/results/full-width-river-capacity-preflight-v1.json -text
 /experiments/configs/full-width-river-capacity-preflight-v2.json -text
 /experiments/results/full-width-river-capacity-preflight-v2.json -text
 /artifacts/gpu_occupied_card_quotient_staged_scaling_v2.jsonl -text
 /artifacts/literal_45_quotient_target_v1.jsonl -text
 /artifacts/legal_river_quotient_cuda_consumer_v1.jsonl -text
+/docs/architecture/dependency-baseline.toml text eol=lf
+/tests/test-inventory.json text eol=lf
+/tests/test-profiles.toml text eol=lf
diff --git a/tests/test_stabilization_boundaries.py b/tests/test_stabilization_boundaries.py
index e504767..40613a3 100644
--- a/tests/test_stabilization_boundaries.py
+++ b/tests/test_stabilization_boundaries.py
@@ -261,20 +261,121 @@ class DependencyBaselineTests(unittest.TestCase):
             with self.assertRaises(GENERATOR.BaselineError):
                 GENERATOR.configured_git_executable()
             os.environ["PONTIUS_GIT"] = known_git
             self.assertTrue(GENERATOR.configured_git_executable().is_absolute())
         finally:
             if prior is None:
                 os.environ.pop("PONTIUS_GIT", None)
             else:
                 os.environ["PONTIUS_GIT"] = prior
 
+    def test_reparse_policy_allows_only_identity_stable_cloud_tags(self) -> None:
+        reparse = 0x400
+        cloud_tags = (0x9000001A, 0x9000601A, 0x9000E01A, 0x9000F01A)
+        rejected_tags = (0, 0xA0000003, 0xA000000C, 0x8000001B, 0x9000001B)
+
+        for tag in cloud_tags:
+            with self.subTest(tag=hex(tag)):
+                self.assertFalse(
+                    GENERATOR._is_disallowed_reparse_values(reparse, tag)
+                )
+        for tag in rejected_tags:
+            with self.subTest(tag=hex(tag)):
+                self.assertTrue(
+                    GENERATOR._is_disallowed_reparse_values(reparse, tag)
+                )
+        self.assertFalse(GENERATOR._is_disallowed_reparse_values(0, 0))
+
+    @unittest.skipUnless(os.name == "nt", "Windows cloud-tag handle test")
+    def test_windows_directory_identity_accepts_cloud_but_rejects_name_surrogate(
+        self,
+    ) -> None:
+        attributes = 0x10 | 0x400
+        active_tag = 0x9000E01A
+
+        def information(_handle: object, pointer: object) -> bool:
+            pointer._obj.dwFileAttributes = attributes
+            return True
+
+        def extended(
+            _handle: object, information_class: int, pointer: object, _size: int
+        ) -> bool:
+            if information_class == 9:
+                pointer._obj.FileAttributes = attributes
+                pointer._obj.ReparseTag = active_tag
+            elif information_class == 18:
+                pointer._obj.VolumeSerialNumber = 42
+                for index in range(16):
+                    pointer._obj.FileId.ByteIdentifier[index] = index
+            else:  # pragma: no cover - fail loudly if the production contract drifts
+                raise AssertionError(information_class)
+            return True
+
+        with mock.patch.object(
+            GENERATOR,
+            "_windows_directory_api",
+            return_value=(None, information, extended, None),
+        ):
+            self.assertEqual(
+                GENERATOR._windows_directory_handle_identity(123, Path("C:/cloud")),
+                (42, bytes(range(16))),
+            )
+            active_tag = 0xA000000C
+            with self.assertRaises(GENERATOR.BaselineError):
+                GENERATOR._windows_directory_handle_identity(
+                    123, Path("C:/name-surrogate")
+                )
+
+    @unittest.skipUnless(os.name == "nt", "Windows hydration retry test")
+    def test_identity_bound_read_retries_one_metadata_only_cloud_transition(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-baseline-cloud-transition-") as directory:
+            root = Path(directory).resolve()
+            target = root / "source.py"
+            target.write_bytes(b"VALUE = 1\n")
+
+            with mock.patch.object(
+                GENERATOR,
+                "_file_identity",
+                side_effect=((1,), (2,), (3,), (3,), (4,)),
+            ) as identity:
+                snapshot = GENERATOR.read_regular_snapshot(
+                    target,
+                    maximum_bytes=64,
+                    root=root,
+                )
+
+            self.assertEqual(snapshot.raw, b"VALUE = 1\n")
+            self.assertEqual(snapshot.identity, (4,))
+            self.assertEqual(identity.call_count, 5)
+
+    @unittest.skipUnless(os.name == "nt", "Windows hydration retry test")
+    def test_identity_bound_read_rejects_a_second_metadata_transition(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-baseline-cloud-repeat-") as directory:
+            root = Path(directory).resolve()
+            target = root / "source.py"
+            target.write_bytes(b"VALUE = 1\n")
+
+            with mock.patch.object(
+                GENERATOR,
+                "_file_identity",
+                side_effect=((1,), (2,), (3,), (4,)),
+            ) as identity:
+                with self.assertRaises(GENERATOR.BaselineError) as caught:
+                    GENERATOR.read_regular_snapshot(
+                        target,
+                        maximum_bytes=64,
+                        root=root,
+                    )
+
+            self.assertIn("changed while reading", str(caught.exception))
+            self.assertEqual(identity.call_count, 4)
+
     def test_identity_bound_read_rejects_same_size_replacement_before_open(self) -> None:
         with tempfile.TemporaryDirectory(prefix="pontius-baseline-read-race-") as directory:
             root = Path(directory).resolve()
             target = root / "baseline.toml"
             replacement = root / "replacement.toml"
             target.write_bytes(b"first\n")
             replacement.write_bytes(b"other\n")
             real_open = getattr(GENERATOR, "_open_regular_no_follow", None)
 
             def replace_then_open(path: Path) -> int:
@@ -381,20 +482,32 @@ class DependencyBaselineTests(unittest.TestCase):
             actual = checked_out.read_bytes()
 
             self.assertEqual(actual, expected.replace(b"\n", b"\r\n"))
             GENERATOR.check_baseline(checked_out, expected)
 
             mixed = actual.replace(b"\r\n", b"\n", 1)
             checked_out.write_bytes(mixed)
             with self.assertRaises(GENERATOR.BaselineError):
                 GENERATOR.check_baseline(checked_out, expected)
 
+    def test_generated_governance_files_are_pinned_to_lf(self) -> None:
+        attributes = (REPOSITORY_ROOT / ".gitattributes").read_text(encoding="utf-8")
+        expected = (
+            "/docs/architecture/dependency-baseline.toml text eol=lf",
+            "/tests/test-inventory.json text eol=lf",
+            "/tests/test-profiles.toml text eol=lf",
+        )
+
+        for rule in expected:
+            with self.subTest(rule=rule):
+                self.assertEqual(attributes.splitlines().count(rule), 1)
+
     def test_write_rejects_an_architecture_symlink_escape(self) -> None:
         with tempfile.TemporaryDirectory(prefix="pontius-baseline-link-") as directory:
             root = Path(directory).resolve()
             docs = root / "docs"
             docs.mkdir()
             outside = root / "outside"
             outside.mkdir()
             architecture = docs / "architecture"
             _create_directory_link(architecture, outside)
             destination = architecture / "dependency-baseline.toml"
diff --git a/tools/check_stabilization_boundaries.py b/tools/check_stabilization_boundaries.py
index 5f57f96..19b268a 100644
--- a/tools/check_stabilization_boundaries.py
+++ b/tools/check_stabilization_boundaries.py
@@ -222,43 +222,41 @@ def enforce_orchestration_import_policy(sources: Mapping[str, bytes]) -> None:
         if not origin.startswith("tools"):
             continue
         sibling = target == _ORCHESTRATION_SIBLING_PREFIX or target.startswith(
             _ORCHESTRATION_SIBLING_PREFIX + "."
         )
         if not _is_stdlib(target) and not sibling:
             violations.append(f"forbidden orchestration import: {origin} -> {target}")
     _raise_violations(violations)
 
 
-def _is_reparse(info: os.stat_result) -> bool:
-    return bool(int(getattr(info, "st_file_attributes", 0)) & 0x400) or bool(
-        int(getattr(info, "st_reparse_tag", 0))
-    )
-
-
 def _read_regular_source(path: Path, *, root: Path) -> object:
     try:
         return _BASELINE.read_regular_snapshot(
             path,
             maximum_bytes=_BASELINE.MAXIMUM_SOURCE_BYTES,
             root=root,
         )
     except _BASELINE.BaselineError as error:
         raise BoundaryError(f"Python source cannot be snapshotted: {path}: {error}") from error
 
 
 def _directory_inventory_identity(path: Path) -> tuple[int, ...]:
     try:
         info = os.lstat(path)
     except OSError as error:
         raise BoundaryError(f"Python inventory directory cannot be inspected: {path}") from error
-    if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
+    if (
+        stat.S_ISLNK(info.st_mode)
+        or _BASELINE._is_disallowed_reparse(info)
+        or not stat.S_ISDIR(info.st_mode)
+    ):
         raise BoundaryError(f"Python inventory has a non-directory or reparse: {path}")
     return _BASELINE._directory_identity(info)
 
 
 def _python_inventory(
     repository_root: Path, relative_root: str
 ) -> tuple[bool, tuple[str, ...], tuple[tuple[str, tuple[int, ...]], ...]]:
     base = repository_root / relative_root
     if not os.path.lexists(base):
         return False, (), ()
diff --git a/tools/generate_dependency_baseline.py b/tools/generate_dependency_baseline.py
index 2706bdb..20ecd76 100644
--- a/tools/generate_dependency_baseline.py
+++ b/tools/generate_dependency_baseline.py
@@ -30,20 +30,23 @@ if os.name == "nt":
     import msvcrt
 
 
 SCHEMA_VERSION = "pontius-dependency-baseline-v1"
 BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
 BASELINE_RELATIVE_PATH = "docs/architecture/dependency-baseline.toml"
 MAXIMUM_ARCHIVE_BYTES = 64 * 1024 * 1024
 MAXIMUM_BASELINE_BYTES = 4 * 1024 * 1024
 MAXIMUM_SOURCE_BYTES = 16 * 1024 * 1024
 _REPARSE_ATTRIBUTE = 0x400
+_REPARSE_NAME_SURROGATE = 0x20000000
+_CLOUD_REPARSE_BASE = 0x9000001A
+_CLOUD_REPARSE_MASK = 0xFFFF0FFF
 _HEX40 = re.compile(r"[0-9a-f]{40}\Z")
 _HEX64 = re.compile(r"[0-9a-f]{64}\Z")
 
 
 class BaselineError(RuntimeError):
     """A deterministic dependency-baseline failure."""
 
     def __init__(
         self,
         message: str,
@@ -576,23 +579,39 @@ def parse_baseline_bytes(raw: bytes) -> ParsedBaseline:
         raise BaselineError("edge_count does not match edge rows")
     if scc_count != len(graph.sccs):
         raise BaselineError("scc_count does not match SCC rows")
     if expected_edge_digest != edges_sha256(graph.edges):
         raise BaselineError("edges_sha256 does not match canonical edge rows")
     if expected_scc_digest != sccs_sha256(graph.sccs):
         raise BaselineError("sccs_sha256 does not match canonical SCC rows")
     return ParsedBaseline(commit, graph)
 
 
-def _is_reparse(info: os.stat_result) -> bool:
-    return bool(int(getattr(info, "st_file_attributes", 0)) & _REPARSE_ATTRIBUTE) or bool(
-        int(getattr(info, "st_reparse_tag", 0))
+def _is_supported_cloud_reparse_tag(tag: int) -> bool:
+    return (
+        type(tag) is int
+        and tag & _REPARSE_NAME_SURROGATE == 0
+        and tag & _CLOUD_REPARSE_MASK == _CLOUD_REPARSE_BASE
+    )
+
+
+def _is_disallowed_reparse_values(attributes: int, tag: int) -> bool:
+    has_reparse_metadata = bool(attributes & _REPARSE_ATTRIBUTE) or bool(tag)
+    if not has_reparse_metadata:
+        return False
+    return not _is_supported_cloud_reparse_tag(tag)
+
+
+def _is_disallowed_reparse(info: os.stat_result) -> bool:
+    return _is_disallowed_reparse_values(
+        int(getattr(info, "st_file_attributes", 0)),
+        int(getattr(info, "st_reparse_tag", 0)),
     )
 
 
 def _file_identity(info: os.stat_result) -> tuple[int, ...]:
     return (
         int(info.st_dev),
         int(info.st_ino),
         int(info.st_size),
         int(info.st_mtime_ns),
         int(info.st_ctime_ns),
@@ -619,58 +638,77 @@ def _path_handle_identity(info: os.stat_result) -> tuple[int, ...]:
 def _directory_identity(info: os.stat_result) -> tuple[int, ...]:
     return (
         int(info.st_dev),
         int(info.st_ino),
         int(info.st_mode),
         int(getattr(info, "st_file_attributes", 0)),
         int(getattr(info, "st_reparse_tag", 0)),
     )
 
 
+def _is_retryable_windows_metadata_transition(
+    before: os.stat_result,
+    after: os.stat_result,
+    before_identity: tuple[int, ...],
+    after_identity: tuple[int, ...],
+) -> bool:
+    """Recognize only the ctime-only transition caused by OneDrive hydration."""
+
+    return (
+        os.name == "nt"
+        and before_identity != after_identity
+        and _path_handle_identity(before) == _path_handle_identity(after)
+    )
+
+
 def _validated_ancestor_chain(path: Path, root: Path) -> tuple[tuple[Path, tuple[int, ...]], ...]:
     if not path.is_absolute() or not root.is_absolute():
         raise BaselineError("secure snapshot paths must be absolute")
     try:
         path.relative_to(root)
     except ValueError as error:
         raise BaselineError("secure snapshot path is outside its repository root") from error
     ancestors: list[tuple[Path, tuple[int, ...]]] = []
     for component in reversed(path.parents):
         if component == component.parent:
             continue
         try:
             info = os.lstat(component)
         except OSError as error:
             raise BaselineError(
                 f"dependency path ancestor cannot be inspected: {component}"
             ) from error
-        if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
+        if (
+            stat.S_ISLNK(info.st_mode)
+            or _is_disallowed_reparse(info)
+            or not stat.S_ISDIR(info.st_mode)
+        ):
             raise BaselineError(
                 f"dependency path ancestor is not a nonreparse directory: {component}"
             )
         ancestors.append((component, _directory_identity(info)))
     return tuple(ancestors)
 
 
 def _revalidate_ancestor_chain(
     ancestors: Sequence[tuple[Path, tuple[int, ...]]],
 ) -> None:
     for component, expected in ancestors:
         try:
             info = os.lstat(component)
         except OSError as error:
             raise BaselineError(
                 f"dependency path ancestor disappeared: {component}"
             ) from error
         if (
             stat.S_ISLNK(info.st_mode)
-            or _is_reparse(info)
+            or _is_disallowed_reparse(info)
             or not stat.S_ISDIR(info.st_mode)
             or _directory_identity(info) != expected
         ):
             raise BaselineError(
                 f"dependency path ancestor identity changed: {component}"
             )
 
 
 def _windows_path_api() -> tuple[Any, Any]:
     if os.name != "nt":
@@ -795,83 +833,109 @@ class FileSnapshot:
             maximum_bytes=self.maximum_bytes,
             root=self.root,
         )
         if current.identity != self.identity:
             raise BaselineError(f"dependency file identity changed: {self.path}")
         if current.raw != self.raw:
             raise BaselineError(f"dependency file content changed: {self.path}")
 
 
 def read_regular_snapshot(
-    path: Path, *, maximum_bytes: int, root: Path
+    path: Path,
+    *,
+    maximum_bytes: int,
+    root: Path,
+    _allow_windows_metadata_retry: bool = True,
 ) -> FileSnapshot:
     """Read one bounded, identity-bound, nonlink filesystem snapshot."""
 
     if type(maximum_bytes) is not int or maximum_bytes < 0:
         raise BaselineError("dependency snapshot bound is invalid")
     ancestors = _validated_ancestor_chain(path, root)
     try:
         before_path = os.lstat(path)
     except OSError as error:
         raise BaselineError(f"dependency file cannot be inspected: {path}") from error
     if (
         stat.S_ISLNK(before_path.st_mode)
-        or _is_reparse(before_path)
+        or _is_disallowed_reparse(before_path)
         or not stat.S_ISREG(before_path.st_mode)
     ):
         raise BaselineError(f"dependency path is not a regular nonreparse file: {path}")
     if before_path.st_size > maximum_bytes:
         raise BaselineError(f"dependency file is oversized: {path}")
 
     descriptor = _open_regular_no_follow(path)
     after_handle: os.stat_result | None = None
+    retry_metadata_transition = False
     try:
         before_handle = os.fstat(descriptor)
         if (
             not stat.S_ISREG(before_handle.st_mode)
-            or _is_reparse(before_handle)
+            or _is_disallowed_reparse(before_handle)
             or _path_handle_identity(before_path) != _path_handle_identity(before_handle)
         ):
             raise BaselineError(f"dependency file changed while opening: {path}")
         chunks: list[bytes] = []
         length = 0
         while length <= maximum_bytes:
             chunk = os.read(descriptor, min(1024 * 1024, maximum_bytes + 1 - length))
             if not chunk:
                 break
             chunks.append(chunk)
             length += len(chunk)
         raw = b"".join(chunks)
         after_handle = os.fstat(descriptor)
         if len(raw) > maximum_bytes:
             raise BaselineError(f"dependency file is oversized: {path}")
-        if (
-            len(raw) != before_handle.st_size
-            or _file_identity(before_handle) != _file_identity(after_handle)
-        ):
-            raise BaselineError(f"opened dependency file changed while reading: {path}")
+        before_identity = _file_identity(before_handle)
+        after_identity = _file_identity(after_handle)
+        if len(raw) != before_handle.st_size or before_identity != after_identity:
+            if (
+                _allow_windows_metadata_retry
+                and len(raw) == before_handle.st_size
+                and _is_retryable_windows_metadata_transition(
+                    before_handle,
+                    after_handle,
+                    before_identity,
+                    after_identity,
+                )
+            ):
+                retry_metadata_transition = True
+            else:
+                raise BaselineError(
+                    f"opened dependency file changed while reading: {path}"
+                )
     except OSError as error:
         raise BaselineError(f"dependency file cannot be read: {path}") from error
     finally:
         try:
             os.close(descriptor)
         except OSError as error:
             raise BaselineError(f"dependency file handle cannot be closed: {path}") from error
 
     assert after_handle is not None
+    if retry_metadata_transition:
+        _revalidate_ancestor_chain(ancestors)
+        return read_regular_snapshot(
+            path,
+            maximum_bytes=maximum_bytes,
+            root=root,
+            _allow_windows_metadata_retry=False,
+        )
     try:
         after_path = os.lstat(path)
     except OSError as error:
         raise BaselineError(f"dependency file disappeared after reading: {path}") from error
     if (
         stat.S_ISLNK(after_path.st_mode)
-        or _is_reparse(after_path)
+        or _is_disallowed_reparse(after_path)
         or _path_handle_identity(after_path) != _path_handle_identity(after_handle)
     ):
         raise BaselineError(f"dependency file identity changed after reading: {path}")
     _revalidate_ancestor_chain(ancestors)
     return FileSnapshot(
         path,
         raw,
         _file_identity(after_path),
         ancestors,
         maximum_bytes,
@@ -916,21 +980,21 @@ def _validated_git_executable(executable: Path) -> Path:
     if not isinstance(executable, Path) or not executable.is_absolute():
         raise BaselineError("Git executable must be an absolute path")
     try:
         resolved = executable.resolve(strict=True)
         info = os.lstat(resolved)
     except OSError as error:
         raise BaselineError("Git executable is unavailable") from error
     if (
         os.path.normcase(str(resolved)) != os.path.normcase(str(executable))
         or stat.S_ISLNK(info.st_mode)
-        or _is_reparse(info)
+        or _is_disallowed_reparse(info)
         or not stat.S_ISREG(info.st_mode)
     ):
         raise BaselineError("Git executable identity is invalid")
     return resolved
 
 
 def _run_git_archive(
     repository_root: Path, *, baseline_commit: str, git_executable: Path
 ) -> bytes:
     executable = _validated_git_executable(git_executable)
@@ -1002,21 +1066,25 @@ def derive_baseline_graph(
         raise BaselineError("repository root cannot be resolved") from error
     raw = _run_git_archive(root, baseline_commit=commit, git_executable=git_executable)
     return scan_sources(_sources_from_archive(raw))
 
 
 def _validated_directory(path: Path, *, description: str) -> tuple[int, ...]:
     try:
         info = os.lstat(path)
     except OSError as error:
         raise BaselineError(f"{description} cannot be inspected: {path}") from error
-    if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
+    if (
+        stat.S_ISLNK(info.st_mode)
+        or _is_disallowed_reparse(info)
+        or not stat.S_ISDIR(info.st_mode)
+    ):
         raise BaselineError(f"{description} is not a nonreparse directory: {path}")
     return _directory_identity(info)
 
 
 def validate_write_destination(repository_root: Path, destination: Path) -> Path:
     if not isinstance(destination, Path) or not destination.is_absolute():
         raise BaselineError("--write must explicitly name an absolute baseline path")
     if not isinstance(repository_root, Path) or not repository_root.is_absolute():
         raise BaselineError("repository root must be absolute for --write")
     root = Path(os.path.abspath(repository_root))
@@ -1027,41 +1095,48 @@ def validate_write_destination(repository_root: Path, destination: Path) -> Path
     docs = root / "docs"
     _validated_directory(docs, description="baseline docs ancestor")
     architecture = docs / "architecture"
     _validated_directory(architecture, description="baseline architecture directory")
     expected = architecture / "dependency-baseline.toml"
     candidate = Path(os.path.abspath(destination))
     if os.path.normcase(str(candidate)) != os.path.normcase(str(expected)):
         raise BaselineError("--write may name only docs/architecture/dependency-baseline.toml")
     if os.path.lexists(candidate):
         info = os.lstat(candidate)
-        if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISREG(info.st_mode):
+        if stat.S_ISLNK(info.st_mode) or _is_disallowed_reparse(info) or not stat.S_ISREG(info.st_mode):
             raise BaselineError("baseline destination is not a regular file")
     return candidate
 
 
 if os.name == "nt":
     class _WindowsDirectoryInformation(ctypes.Structure):
         _fields_ = (
             ("dwFileAttributes", wintypes.DWORD),
             ("ftCreationTime", wintypes.FILETIME),
             ("ftLastAccessTime", wintypes.FILETIME),
             ("ftLastWriteTime", wintypes.FILETIME),
             ("dwVolumeSerialNumber", wintypes.DWORD),
             ("nFileSizeHigh", wintypes.DWORD),
             ("nFileSizeLow", wintypes.DWORD),
             ("nNumberOfLinks", wintypes.DWORD),
             ("nFileIndexHigh", wintypes.DWORD),
             ("nFileIndexLow", wintypes.DWORD),
         )
 
 
+    class _WindowsFileAttributeTagInformation(ctypes.Structure):
+        _fields_ = (
+            ("FileAttributes", wintypes.DWORD),
+            ("ReparseTag", wintypes.DWORD),
+        )
+
+
     class _WindowsFileId128(ctypes.Structure):
         _fields_ = (("ByteIdentifier", ctypes.c_ubyte * 16),)
 
 
     class _WindowsFileIdInformation(ctypes.Structure):
         _fields_ = (
             ("VolumeSerialNumber", ctypes.c_ulonglong),
             ("FileId", _WindowsFileId128),
         )
 
@@ -1150,23 +1225,44 @@ def _windows_directory_handle_identity(handle: int, path: Path) -> tuple[int, by
     value = _WindowsDirectoryInformation()
     try:
         succeeded = information(wintypes.HANDLE(handle), ctypes.byref(value))
     except Exception as error:
         raise BaselineError(f"baseline directory handle cannot be inspected: {path}") from error
     if not succeeded:
         error = ctypes.get_last_error()
         raise BaselineError(
             f"baseline directory handle cannot be inspected: {path}"
         ) from OSError(error, os.strerror(error), str(path))
-    attributes = int(value.dwFileAttributes)
-    if not attributes & 0x10 or attributes & _REPARSE_ATTRIBUTE:
-        raise BaselineError(f"baseline directory handle is not nonreparse: {path}")
+    tag_information = _WindowsFileAttributeTagInformation()
+    try:
+        succeeded = extended_information(
+            wintypes.HANDLE(handle),
+            9,
+            ctypes.byref(tag_information),
+            ctypes.sizeof(tag_information),
+        )
+    except Exception as error:
+        raise BaselineError(
+            f"baseline directory reparse tag cannot be inspected: {path}"
+        ) from error
+    if not succeeded:
+        error = ctypes.get_last_error()
+        raise BaselineError(
+            f"baseline directory reparse tag cannot be inspected: {path}"
+        ) from OSError(error, os.strerror(error), str(path))
+    attributes = int(tag_information.FileAttributes)
+    if attributes != int(value.dwFileAttributes):
+        raise BaselineError(f"baseline directory attributes are inconsistent: {path}")
+    if not attributes & 0x10 or _is_disallowed_reparse_values(
+        attributes, int(tag_information.ReparseTag)
+    ):
+        raise BaselineError(f"baseline directory handle has a disallowed reparse: {path}")
     identity = _WindowsFileIdInformation()
     try:
         succeeded = extended_information(
             wintypes.HANDLE(handle),
             18,
             ctypes.byref(identity),
             ctypes.sizeof(identity),
         )
     except Exception as error:
         raise BaselineError(f"baseline directory identity cannot be inspected: {path}") from error
@@ -1750,21 +1846,21 @@ class _BoundBaselineDirectory:
                 current_path_identity = self._windows_path_identity(path)
                 if (
                     handle_identity != expected_handle
                     or handle_identity != intended_identity
                     or current_path_identity != intended_identity
                 ):
                     raise BaselineError(f"held baseline directory identity changed: {path}")
                 info = os.lstat(path)
                 if (
                     stat.S_ISLNK(info.st_mode)
-                    or _is_reparse(info)
+                    or _is_disallowed_reparse(info)
                     or not stat.S_ISDIR(info.st_mode)
                 ):
                     raise BaselineError(
                         f"baseline directory path no longer names its handle: {path}"
                     )
             return
         for index, (path, descriptor, bound_identity) in enumerate(
             self._posix_descriptors
         ):
             intended_path, intended_identity = self._validated_directories[index]
