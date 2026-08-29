# Review package: fffef41cc63492c333bbbf6f181ca4e18861aece..ea9f7cd1622af7cf724d2816fdb0f4f8f307300d

## Commits
ea9f7cd fix(architecture): bind Windows file reparse metadata

## Files changed
 tests/test_stabilization_boundaries.py |  92 ++++++++++++++++++++-
 tools/generate_dependency_baseline.py  | 141 +++++++++++++++++++++++++++++----
 2 files changed, 216 insertions(+), 17 deletions(-)

## Diff
diff --git a/tests/test_stabilization_boundaries.py b/tests/test_stabilization_boundaries.py
index dab45d2..f6f173c 100644
--- a/tests/test_stabilization_boundaries.py
+++ b/tests/test_stabilization_boundaries.py
@@ -377,20 +377,110 @@ class DependencyBaselineTests(unittest.TestCase):
                 with self.assertRaises(GENERATOR.BaselineError) as caught:
                     GENERATOR.read_regular_snapshot(
                         target,
                         maximum_bytes=64,
                         root=root,
                     )
 
             self.assertIn("changed while reading", str(caught.exception))
             self.assertEqual(identity.call_count, 4)
 
+    @unittest.skipUnless(os.name == "nt", "Windows regular-file cloud-tag test")
+    def test_regular_file_snapshot_binds_handle_cloud_metadata(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-cloud-file-") as directory:
+            root = Path(directory).resolve()
+            target = root / "source.py"
+            target.write_bytes(b"VALUE = 1\n")
+            cloud = (0x20 | 0x400, 0x9000E01A)
+
+            real_lstat = GENERATOR.os.lstat
+
+            def cloud_lstat(path: object) -> object:
+                info = real_lstat(path)
+                if Path(path) != target:
+                    return info
+                return SimpleNamespace(
+                    st_dev=info.st_dev,
+                    st_ino=info.st_ino,
+                    st_size=info.st_size,
+                    st_mtime_ns=info.st_mtime_ns,
+                    st_ctime_ns=info.st_ctime_ns,
+                    st_mode=info.st_mode,
+                    st_file_attributes=cloud[0],
+                    st_reparse_tag=cloud[1],
+                )
+
+            with mock.patch.object(
+                GENERATOR.os, "lstat", side_effect=cloud_lstat
+            ), mock.patch.object(
+                GENERATOR,
+                "_windows_regular_handle_metadata",
+                side_effect=(cloud, cloud),
+            ):
+                snapshot = GENERATOR.read_regular_snapshot(
+                    target,
+                    maximum_bytes=64,
+                    root=root,
+                )
+            self.assertEqual(snapshot.raw, b"VALUE = 1\n")
+
+            for label, metadata in (
+                ("name surrogate", (0x20 | 0x400, 0xA000000C)),
+                ("unknown", (0x20 | 0x400, 0x8000001B)),
+            ):
+                with self.subTest(label=label), mock.patch.object(
+                    GENERATOR,
+                    "_windows_regular_handle_metadata",
+                    return_value=metadata,
+                ):
+                    with self.assertRaises(GENERATOR.BaselineError):
+                        GENERATOR.read_regular_snapshot(
+                            target,
+                            maximum_bytes=64,
+                            root=root,
+                        )
+
+            mismatched_cloud = (cloud[0], 0x9000601A)
+            with mock.patch.object(
+                GENERATOR.os,
+                "lstat",
+                side_effect=cloud_lstat,
+            ), mock.patch.object(
+                GENERATOR,
+                "_windows_regular_handle_metadata",
+                side_effect=(cloud, mismatched_cloud),
+            ):
+                with self.assertRaises(GENERATOR.BaselineError) as caught:
+                    GENERATOR.read_regular_snapshot(
+                        target,
+                        maximum_bytes=64,
+                        root=root,
+                    )
+            self.assertIn("changed while reading", str(caught.exception))
+
+            with mock.patch.object(
+                GENERATOR.os,
+                "lstat",
+                side_effect=cloud_lstat,
+            ), mock.patch.object(
+                GENERATOR,
+                "_windows_regular_handle_metadata",
+                return_value=mismatched_cloud,
+            ):
+                with self.assertRaises(GENERATOR.BaselineError) as caught:
+                    GENERATOR.read_regular_snapshot(
+                        target,
+                        maximum_bytes=64,
+                        root=root,
+                    )
+            self.assertIn("changed while opening", str(caught.exception))
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
@@ -967,21 +1057,21 @@ class DependencyBaselineTests(unittest.TestCase):
 
     @unittest.skipUnless(os.name == "nt", "Windows handle ownership test")
     def test_windows_file_binding_reports_an_ambiguous_handle_close(self) -> None:
         create = mock.Mock(return_value=123)
         close = mock.Mock(return_value=False)
         binding_error = OSError("injected descriptor binding failure")
 
         with mock.patch.object(
             GENERATOR,
             "_windows_path_api",
-            return_value=(create, close),
+            return_value=(create, None, close),
         ), mock.patch.object(
             GENERATOR.msvcrt,
             "open_osfhandle",
             side_effect=binding_error,
         ), mock.patch.object(GENERATOR.ctypes, "get_last_error", return_value=6):
             with self.assertRaises(GENERATOR.BaselineError) as caught:
                 GENERATOR._open_regular_no_follow(Path("C:/synthetic.py"))
 
         self.assertEqual(close.call_count, 1)
         self.assertIn(123, caught.exception.retained_owners)
diff --git a/tools/generate_dependency_baseline.py b/tools/generate_dependency_baseline.py
index 2e84983..ad7149a 100644
--- a/tools/generate_dependency_baseline.py
+++ b/tools/generate_dependency_baseline.py
@@ -607,69 +607,116 @@ def _is_disallowed_reparse_values(attributes: int, tag: int) -> bool:
     return not _is_supported_cloud_reparse_tag(tag)
 
 
 def _is_disallowed_reparse(info: os.stat_result) -> bool:
     return _is_disallowed_reparse_values(
         int(getattr(info, "st_file_attributes", 0)),
         int(getattr(info, "st_reparse_tag", 0)),
     )
 
 
-def _file_identity(info: os.stat_result) -> tuple[int, ...]:
+def _identity_reparse_values(
+    info: os.stat_result,
+    windows_metadata: tuple[int, int] | None = None,
+) -> tuple[int, int]:
+    if windows_metadata is not None:
+        return windows_metadata
+    return (
+        int(getattr(info, "st_file_attributes", 0)),
+        int(getattr(info, "st_reparse_tag", 0)),
+    )
+
+
+def _file_identity(
+    info: os.stat_result,
+    *,
+    windows_metadata: tuple[int, int] | None = None,
+) -> tuple[int, ...]:
+    attributes, tag = _identity_reparse_values(info, windows_metadata)
     return (
         int(info.st_dev),
         int(info.st_ino),
         int(info.st_size),
         int(info.st_mtime_ns),
         int(info.st_ctime_ns),
         int(info.st_mode),
-        int(getattr(info, "st_file_attributes", 0)),
-        int(getattr(info, "st_reparse_tag", 0)),
+        attributes,
+        tag,
     )
 
 
-def _path_handle_identity(info: os.stat_result) -> tuple[int, ...]:
+def _path_handle_identity(
+    info: os.stat_result,
+    *,
+    windows_metadata: tuple[int, int] | None = None,
+) -> tuple[int, ...]:
     """Return fields reported consistently by path and handle on Windows."""
 
+    attributes, tag = _identity_reparse_values(info, windows_metadata)
     return (
         int(info.st_dev),
         int(info.st_ino),
         int(info.st_size),
         int(info.st_mtime_ns),
         int(info.st_mode),
-        int(getattr(info, "st_file_attributes", 0)),
-        int(getattr(info, "st_reparse_tag", 0)),
+        attributes,
+        tag,
     )
 
 
+def _path_handle_core_identity(info: os.stat_result) -> tuple[int, ...]:
+    return _path_handle_identity(info)[:5]
+
+
+def _path_matches_open_handle(
+    path_info: os.stat_result,
+    handle_info: os.stat_result,
+    windows_metadata: tuple[int, int] | None,
+) -> bool:
+    if (
+        _path_handle_core_identity(path_info)
+        != _path_handle_core_identity(handle_info)
+    ):
+        return False
+    if windows_metadata is None:
+        return _path_handle_identity(path_info) == _path_handle_identity(handle_info)
+    return _identity_reparse_values(path_info) == windows_metadata
+
+
 def _directory_identity(info: os.stat_result) -> tuple[int, ...]:
     return (
         int(info.st_dev),
         int(info.st_ino),
         int(info.st_mode),
         int(getattr(info, "st_file_attributes", 0)),
         int(getattr(info, "st_reparse_tag", 0)),
     )
 
 
 def _is_retryable_windows_metadata_transition(
     before: os.stat_result,
     after: os.stat_result,
     before_identity: tuple[int, ...],
     after_identity: tuple[int, ...],
+    before_windows_metadata: tuple[int, int] | None,
+    after_windows_metadata: tuple[int, int] | None,
 ) -> bool:
     """Recognize only the ctime-only transition caused by OneDrive hydration."""
 
     return (
         os.name == "nt"
         and before_identity != after_identity
-        and _path_handle_identity(before) == _path_handle_identity(after)
+        and before_windows_metadata == after_windows_metadata
+        and _path_handle_identity(
+            before, windows_metadata=before_windows_metadata
+        )
+        == _path_handle_identity(after, windows_metadata=after_windows_metadata)
     )
 
 
 def _validated_ancestor_chain(path: Path, root: Path) -> tuple[tuple[Path, tuple[int, ...]], ...]:
     if not path.is_absolute() or not root.is_absolute():
         raise BaselineError("secure snapshot paths must be absolute")
     try:
         path.relative_to(root)
     except ValueError as error:
         raise BaselineError("secure snapshot path is outside its repository root") from error
@@ -709,62 +756,97 @@ def _revalidate_ancestor_chain(
             stat.S_ISLNK(info.st_mode)
             or _is_disallowed_reparse(info)
             or not stat.S_ISDIR(info.st_mode)
             or _directory_identity(info) != expected
         ):
             raise BaselineError(
                 f"dependency path ancestor identity changed: {component}"
             )
 
 
-def _windows_path_api() -> tuple[Any, Any]:
+def _windows_path_api() -> tuple[Any, Any, Any]:
     if os.name != "nt":
         raise BaselineError("Windows no-follow file APIs are unavailable")
     try:
         kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
         create = kernel32.CreateFileW
         create.argtypes = (
             wintypes.LPCWSTR,
             wintypes.DWORD,
             wintypes.DWORD,
             wintypes.LPVOID,
             wintypes.DWORD,
             wintypes.DWORD,
             wintypes.HANDLE,
         )
         create.restype = wintypes.HANDLE
+        information = kernel32.GetFileInformationByHandleEx
+        information.argtypes = (
+            wintypes.HANDLE,
+            ctypes.c_int,
+            wintypes.LPVOID,
+            wintypes.DWORD,
+        )
+        information.restype = wintypes.BOOL
         close = kernel32.CloseHandle
         close.argtypes = (wintypes.HANDLE,)
         close.restype = wintypes.BOOL
     except Exception as error:
         raise BaselineError("Windows no-follow file APIs are unavailable") from error
-    return create, close
+    return create, information, close
+
+
+def _windows_regular_handle_metadata(
+    descriptor: int, path: Path
+) -> tuple[int, int]:
+    if os.name != "nt":
+        raise BaselineError("Windows regular-file metadata is unavailable")
+    try:
+        handle = msvcrt.get_osfhandle(descriptor)
+        _, information, _ = _windows_path_api()
+        value = _WindowsFileAttributeTagInformation()
+        succeeded = information(
+            wintypes.HANDLE(handle),
+            9,
+            ctypes.byref(value),
+            ctypes.sizeof(value),
+        )
+    except Exception as error:
+        raise BaselineError(
+            f"dependency file handle metadata cannot be inspected: {path}"
+        ) from error
+    if not succeeded:
+        error = ctypes.get_last_error()
+        raise BaselineError(
+            f"dependency file handle metadata cannot be inspected: {path}"
+        ) from OSError(error, os.strerror(error), str(path))
+    return int(value.FileAttributes), int(value.ReparseTag)
 
 
 def _open_regular_no_follow(path: Path) -> int:
     if os.name != "nt":
         if not hasattr(os, "O_NOFOLLOW"):
             raise BaselineError("secure no-follow file opens are unavailable")
         flags = (
             os.O_RDONLY
             | os.O_NOFOLLOW
             | getattr(os, "O_CLOEXEC", 0)
             | getattr(os, "O_BINARY", 0)
         )
         try:
             return os.open(path, flags)
         except OSError as error:
             raise BaselineError(
                 f"dependency file cannot be opened without links: {path}"
             ) from error
 
-    create, close = _windows_path_api()
+    create, _, close = _windows_path_api()
     try:
         handle = create(
             str(path),
             0x80000000,
             0x00000001 | 0x00000002 | 0x00000004,
             None,
             3,
             0x00200000 | 0x08000000,
             None,
         )
@@ -865,52 +947,77 @@ def read_regular_snapshot(
         stat.S_ISLNK(before_path.st_mode)
         or _is_disallowed_reparse(before_path)
         or not stat.S_ISREG(before_path.st_mode)
     ):
         raise BaselineError(f"dependency path is not a regular nonreparse file: {path}")
     if before_path.st_size > maximum_bytes:
         raise BaselineError(f"dependency file is oversized: {path}")
 
     descriptor = _open_regular_no_follow(path)
     after_handle: os.stat_result | None = None
+    before_windows_metadata: tuple[int, int] | None = None
+    after_windows_metadata: tuple[int, int] | None = None
     retry_metadata_transition = False
     try:
+        if os.name == "nt":
+            before_windows_metadata = _windows_regular_handle_metadata(
+                descriptor, path
+            )
         before_handle = os.fstat(descriptor)
         if (
             not stat.S_ISREG(before_handle.st_mode)
-            or _is_disallowed_reparse(before_handle)
-            or _path_handle_identity(before_path) != _path_handle_identity(before_handle)
+            or (
+                before_windows_metadata is None
+                and _is_disallowed_reparse(before_handle)
+            )
+            or (
+                before_windows_metadata is not None
+                and _is_disallowed_reparse_values(*before_windows_metadata)
+            )
+            or not _path_matches_open_handle(
+                before_path, before_handle, before_windows_metadata
+            )
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
+        if os.name == "nt":
+            after_windows_metadata = _windows_regular_handle_metadata(
+                descriptor, path
+            )
         if len(raw) > maximum_bytes:
             raise BaselineError(f"dependency file is oversized: {path}")
-        before_identity = _file_identity(before_handle)
-        after_identity = _file_identity(after_handle)
+        before_identity = _file_identity(
+            before_handle, windows_metadata=before_windows_metadata
+        )
+        after_identity = _file_identity(
+            after_handle, windows_metadata=after_windows_metadata
+        )
         if len(raw) != before_handle.st_size or before_identity != after_identity:
             if (
                 _allow_windows_metadata_retry
                 and len(raw) == before_handle.st_size
                 and _is_retryable_windows_metadata_transition(
                     before_handle,
                     after_handle,
                     before_identity,
                     after_identity,
+                    before_windows_metadata,
+                    after_windows_metadata,
                 )
             ):
                 retry_metadata_transition = True
             else:
                 raise BaselineError(
                     f"opened dependency file changed while reading: {path}"
                 )
     except OSError as error:
         raise BaselineError(f"dependency file cannot be read: {path}") from error
     finally:
@@ -928,28 +1035,30 @@ def read_regular_snapshot(
             root=root,
             _allow_windows_metadata_retry=False,
         )
     try:
         after_path = os.lstat(path)
     except OSError as error:
         raise BaselineError(f"dependency file disappeared after reading: {path}") from error
     if (
         stat.S_ISLNK(after_path.st_mode)
         or _is_disallowed_reparse(after_path)
-        or _path_handle_identity(after_path) != _path_handle_identity(after_handle)
+        or not _path_matches_open_handle(
+            after_path, after_handle, after_windows_metadata
+        )
     ):
         raise BaselineError(f"dependency file identity changed after reading: {path}")
     _revalidate_ancestor_chain(ancestors)
     return FileSnapshot(
         path,
         raw,
-        _file_identity(after_path),
+        _file_identity(after_handle, windows_metadata=after_windows_metadata),
         ancestors,
         maximum_bytes,
         root,
     )
 
 
 def _validated_regular_file(path: Path, *, maximum_bytes: int) -> bytes:
     if not isinstance(path, Path) or not path.is_absolute():
         raise BaselineError("dependency baseline path must be absolute")
     return read_regular_snapshot(
