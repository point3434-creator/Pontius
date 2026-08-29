# Review package: c4d158e4601c61ce445be5f57894ccef61cddbf0..ba1e665c3337a8bbdda96ba2cc6fa5c6e52dd163

## Commits
ba1e665 fix(evidence): bind manifest write transaction

## Files changed
 tests/test_evidence_manifest_generation.py |  81 +++++++
 tools/generate_evidence_manifests.py       | 351 ++++++++++++++++++++++++-----
 2 files changed, 379 insertions(+), 53 deletions(-)

## Diff
diff --git a/tests/test_evidence_manifest_generation.py b/tests/test_evidence_manifest_generation.py
index 6d6aee6..b291600 100644
--- a/tests/test_evidence_manifest_generation.py
+++ b/tests/test_evidence_manifest_generation.py
@@ -914,20 +914,101 @@ class Selected:
                 approved_seed_sha256=SAMPLE_STATE["entries_sha256"],
             )
 
             architecture = root / "docs" / "architecture"
             expected_names = tuple(sorted(Path(path).name for path in GENERATOR.MANIFEST_PATHS))
             self.assertEqual(tuple(sorted(path.name for path in architecture.iterdir())), expected_names)
             for relative, expected in rendered.items():
                 self.assertEqual((root / relative).read_bytes(), expected)
             self.assertEqual(tuple(path.name for path in root.iterdir()), ("docs",))
 
+    def test_main_write_bootstraps_missing_directory_while_check_remains_read_only(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-main-write-") as directory:
+            root = Path(directory).resolve()
+            (root / "docs").mkdir()
+            synthetic_tool = root / "tools" / "generate_evidence_manifests.py"
+            with mock.patch.object(GENERATOR, "__file__", str(synthetic_tool)), mock.patch.object(
+                GENERATOR, "derive_manifest_state", return_value=SAMPLE_STATE
+            ):
+                self.assertEqual(
+                    GENERATOR.main(
+                        [
+                            "--write",
+                            "--approved-seed-sha256",
+                            SAMPLE_STATE["entries_sha256"],
+                        ]
+                    ),
+                    0,
+                )
+            architecture = root / "docs" / "architecture"
+            self.assertEqual(
+                tuple(sorted(path.name for path in architecture.iterdir())),
+                tuple(sorted(Path(path).name for path in GENERATOR.MANIFEST_PATHS)),
+            )
+
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-main-check-") as directory:
+            root = Path(directory).resolve()
+            (root / "docs").mkdir()
+            synthetic_tool = root / "tools" / "generate_evidence_manifests.py"
+            with mock.patch.object(GENERATOR, "__file__", str(synthetic_tool)), mock.patch.object(
+                GENERATOR, "derive_manifest_state", side_effect=AssertionError("walked")
+            ):
+                self.assertEqual(GENERATOR.main(["--check"]), 2)
+            self.assertFalse((root / "docs" / "architecture").exists())
+            with self.assertRaises(GENERATOR.GenerationError):
+                GENERATOR._verified_destinations(root)
+
+    def test_bound_manifest_transaction_defeats_post_validation_directory_swap(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-bound-swap-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            displaced = root / "docs" / "architecture-displaced"
+            swap_attempted = False
+            swap_succeeded = False
+            original_uuid4 = GENERATOR.uuid.uuid4
+
+            def attempt_swap() -> object:
+                nonlocal swap_attempted, swap_succeeded
+                swap_attempted = True
+                try:
+                    os.replace(architecture, displaced)
+                    architecture.mkdir()
+                except OSError:
+                    pass
+                else:
+                    swap_succeeded = True
+                return original_uuid4()
+
+            failure = None
+            with mock.patch.object(GENERATOR.uuid, "uuid4", side_effect=attempt_swap):
+                try:
+                    GENERATOR.write_manifests(
+                        root,
+                        SAMPLE_STATE,
+                        approved_seed_sha256=SAMPLE_STATE["entries_sha256"],
+                    )
+                except GENERATOR.GenerationError as error:
+                    failure = error
+
+            self.assertTrue(swap_attempted)
+            if swap_succeeded:
+                self.assertIsNotNone(failure)
+                self.assertEqual(list(architecture.iterdir()), [])
+                self.assertEqual(list(displaced.iterdir()), [])
+            else:
+                self.assertIsNone(failure)
+                self.assertEqual(
+                    tuple(sorted(path.name for path in architecture.iterdir())),
+                    tuple(sorted(Path(path).name for path in GENERATOR.MANIFEST_PATHS)),
+                )
+
     def test_manifest_directory_rejects_non_directory_link_and_reparse_targets(self) -> None:
         with tempfile.TemporaryDirectory(prefix="pontius-task3-directory-kind-") as directory:
             root = Path(directory).resolve()
             docs = root / "docs"
             docs.mkdir()
             architecture = docs / "architecture"
             architecture.write_bytes(b"not a directory")
             with self.assertRaises(GENERATOR.GenerationError):
                 GENERATOR._verified_destinations(root)
 
diff --git a/tools/generate_evidence_manifests.py b/tools/generate_evidence_manifests.py
index 96ed3f9..f957774 100644
--- a/tools/generate_evidence_manifests.py
+++ b/tools/generate_evidence_manifests.py
@@ -1,35 +1,40 @@
 """Deterministically derive and guard the evidence-boundary manifests.
 
 This tool is standard-library-only and deliberately does not import pontius.
 """
 
 from __future__ import annotations
 
 import argparse
 import ast
 from collections.abc import Mapping, Sequence
+import errno
 from hashlib import sha256
 import json
 import os
 from pathlib import Path, PurePosixPath, PureWindowsPath
 import re
 import stat
 import subprocess
 import sys
 import tempfile
 import threading
 import time
 import tomllib
 from typing import Any
 import uuid
 
+if os.name == "nt":
+    import ctypes
+    from ctypes import wintypes
+
 
 BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
 GIT_EXECUTABLE = Path("C:/Program Files/Git/cmd/git.exe")
 MANIFEST_PATHS = (
     "docs/architecture/sealed-current-files.toml",
     "docs/architecture/sealed-current-absences.toml",
     "docs/architecture/historical-blobs.toml",
     "docs/architecture/retained-v7.toml",
 )
 
@@ -2045,51 +2050,38 @@ def _validated_directory(path: Path, description: str) -> tuple[int, ...]:
     try:
         info = os.lstat(path)
     except OSError as error:
         raise GenerationError(f"{description} cannot be inspected: {path}") from error
     if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
         raise GenerationError(f"{description} is not a directory without links or reparses: {path}")
     return _directory_identity(info)
 
 
 def _manifest_destinations(
-    repository_root: Path, *, create_missing: bool
-) -> tuple[dict[str, Path], tuple[int, ...] | None]:
+    repository_root: Path, *, allow_missing_architecture: bool
+) -> dict[str, Path]:
     if not repository_root.is_absolute():
         raise GenerationError("repository root must be absolute")
     _validated_directory(repository_root, "repository root")
     root = repository_root.resolve(strict=True)
     _validated_directory(root, "resolved repository root")
     docs = root / "docs"
     docs_identity = _validated_directory(docs, "manifest docs ancestor")
     architecture = docs / "architecture"
     try:
-        architecture_identity: tuple[int, ...] | None = _validated_directory(
+        architecture_identity = _validated_directory(
             architecture, "manifest architecture directory"
         )
     except GenerationError:
-        if os.path.lexists(architecture) or not create_missing:
-            if os.path.lexists(architecture):
-                raise
-            architecture_identity = None
-        else:
-            try:
-                os.mkdir(architecture)
-            except OSError as error:
-                raise GenerationError(
-                    "manifest architecture directory could not be securely created"
-                ) from error
-            if _validated_directory(docs, "manifest docs ancestor") != docs_identity:
-                raise GenerationError("manifest docs ancestor identity changed during bootstrap")
-            architecture_identity = _validated_directory(
-                architecture, "manifest architecture directory"
-            )
+        if os.path.lexists(architecture) or not allow_missing_architecture:
+            raise
+        architecture_identity = None
     result: dict[str, Path] = {}
     for relative in MANIFEST_PATHS:
         destination = root / relative
         if destination.parent != architecture:
             raise GenerationError(
                 "manifest destination is outside the exact architecture directory"
             )
         if os.path.lexists(destination):
             info = os.lstat(destination)
             if (
@@ -2102,68 +2094,321 @@ def _manifest_destinations(
                 )
         result[relative] = destination
     if _validated_directory(docs, "manifest docs ancestor") != docs_identity:
         raise GenerationError("manifest docs ancestor identity changed during destination validation")
     if architecture_identity is not None:
         if (
             _validated_directory(architecture, "manifest architecture directory")
             != architecture_identity
         ):
             raise GenerationError("manifest architecture directory identity changed")
-    return result, architecture_identity
+    return result
 
 
 def _verified_destinations(repository_root: Path) -> dict[str, Path]:
-    destinations, _ = _manifest_destinations(repository_root, create_missing=False)
-    return destinations
+    return _manifest_destinations(repository_root, allow_missing_architecture=False)
+
+
+def _validated_write_destination_intent(repository_root: Path) -> dict[str, Path]:
+    return _manifest_destinations(repository_root, allow_missing_architecture=True)
+
+
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
 
 
-def write_manifests(
-    repository_root: Path,
-    state: Mapping[str, object],
-    *,
-    approved_seed_sha256: str | None,
-) -> None:
-    approved = validate_approval_digest(
-        approved_seed_sha256, str(state["entries_sha256"])
+def _windows_directory_api() -> tuple[Any, Any, Any]:
+    if os.name != "nt":
+        raise GenerationError("Windows directory handles are unavailable")
+    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
+    create = kernel32.CreateFileW
+    create.argtypes = (
+        wintypes.LPCWSTR,
+        wintypes.DWORD,
+        wintypes.DWORD,
+        wintypes.LPVOID,
+        wintypes.DWORD,
+        wintypes.DWORD,
+        wintypes.HANDLE,
     )
-    destinations, architecture_identity = _manifest_destinations(
-        repository_root, create_missing=True
+    create.restype = wintypes.HANDLE
+    information = kernel32.GetFileInformationByHandle
+    information.argtypes = (
+        wintypes.HANDLE,
+        ctypes.POINTER(_WindowsDirectoryInformation),
     )
-    if architecture_identity is None:
-        raise GenerationError("manifest architecture directory was not established")
-    rendered = _render_all(state, approved)
-    rechecked, rechecked_identity = _manifest_destinations(
-        repository_root, create_missing=False
+    information.restype = wintypes.BOOL
+    close = kernel32.CloseHandle
+    close.argtypes = (wintypes.HANDLE,)
+    close.restype = wintypes.BOOL
+    return create, information, close
+
+
+def _windows_open_directory(path: Path) -> int:
+    create, _, close = _windows_directory_api()
+    handle = create(
+        str(path),
+        0x00000080,
+        0x00000001 | 0x00000002,
+        None,
+        3,
+        0x02000000 | 0x00200000,
+        None,
     )
-    if rechecked != destinations or rechecked_identity != architecture_identity:
-        raise GenerationError("manifest destination identity changed before writing")
-    temporary: dict[str, Path] = {}
+    invalid = ctypes.c_void_p(-1).value
+    if handle == invalid:
+        error = ctypes.get_last_error()
+        raise GenerationError(f"manifest directory handle could not be opened: {path}") from OSError(
+            error, os.strerror(error), str(path)
+        )
     try:
-        for relative, destination in destinations.items():
-            candidate = (
-                destination.parent / f".{destination.name}.{uuid.uuid4().hex}.tmp"
+        _windows_directory_handle_identity(handle, path)
+    except BaseException:
+        close(handle)
+        raise
+    return int(handle)
+
+
+def _windows_directory_handle_identity(handle: int, path: Path) -> tuple[int, int]:
+    _, information, _ = _windows_directory_api()
+    value = _WindowsDirectoryInformation()
+    if not information(handle, ctypes.byref(value)):
+        error = ctypes.get_last_error()
+        raise GenerationError(f"manifest directory handle cannot be inspected: {path}") from OSError(
+            error, os.strerror(error), str(path)
+        )
+    attributes = int(value.dwFileAttributes)
+    if not attributes & 0x00000010 or attributes & _REPARSE_ATTRIBUTE:
+        raise GenerationError(f"manifest directory handle is not a nonreparse directory: {path}")
+    file_index = (int(value.nFileIndexHigh) << 32) | int(value.nFileIndexLow)
+    return int(value.dwVolumeSerialNumber), file_index
+
+
+def _close_windows_directory(handle: int) -> None:
+    _, _, close = _windows_directory_api()
+    close(handle)
+
+
+class _BoundManifestDirectory:
+    def __init__(self, repository_root: Path, *, create_missing: bool) -> None:
+        self.repository_root = repository_root
+        self.create_missing = create_missing
+        self.root: Path | None = None
+        self.docs: Path | None = None
+        self.architecture: Path | None = None
+        self.destinations: dict[str, Path] = {}
+        self._posix_descriptors: list[tuple[Path, int, tuple[int, int]]] = []
+        self._windows_handles: list[tuple[Path, int, tuple[int, int]]] = []
+        self._architecture_descriptor: int | None = None
+
+    def __enter__(self) -> "_BoundManifestDirectory":
+        if not self.repository_root.is_absolute():
+            raise GenerationError("repository root must be absolute")
+        _validated_directory(self.repository_root, "repository root")
+        self.root = self.repository_root.resolve(strict=True)
+        self.docs = self.root / "docs"
+        self.architecture = self.docs / "architecture"
+        try:
+            if os.name == "nt":
+                self._bind_windows()
+            else:
+                self._bind_posix()
+            self.destinations = _verified_destinations(self.root)
+            self.reverify()
+            return self
+        except BaseException:
+            self.close()
+            raise
+
+    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
+        self.close()
+
+    def _bind_windows(self) -> None:
+        assert self.root is not None and self.docs is not None and self.architecture is not None
+        for path in (self.root, self.docs):
+            handle = _windows_open_directory(path)
+            identity = _windows_directory_handle_identity(handle, path)
+            self._windows_handles.append((path, handle, identity))
+        if not os.path.lexists(self.architecture):
+            if not self.create_missing:
+                raise GenerationError("manifest architecture directory is absent")
+            try:
+                os.mkdir(self.architecture)
+            except OSError as error:
+                raise GenerationError(
+                    "manifest architecture directory could not be securely created"
+                ) from error
+        handle = _windows_open_directory(self.architecture)
+        identity = _windows_directory_handle_identity(handle, self.architecture)
+        self._windows_handles.append((self.architecture, handle, identity))
+
+    def _bind_posix(self) -> None:
+        assert self.root is not None and self.docs is not None and self.architecture is not None
+        required = ("O_DIRECTORY", "O_NOFOLLOW")
+        dir_fd_functions = (os.open, os.mkdir, os.replace, os.unlink)
+        if (
+            any(not hasattr(os, name) for name in required)
+            or any(function not in os.supports_dir_fd for function in dir_fd_functions)
+        ):
+            raise GenerationError("secure POSIX directory primitives are unavailable")
+        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
+        try:
+            root_descriptor = os.open(self.root, flags)
+            root_info = os.fstat(root_descriptor)
+            self._posix_descriptors.append(
+                (self.root, root_descriptor, (int(root_info.st_dev), int(root_info.st_ino)))
+            )
+            docs_descriptor = os.open("docs", flags, dir_fd=root_descriptor)
+            docs_info = os.fstat(docs_descriptor)
+            self._posix_descriptors.append(
+                (self.docs, docs_descriptor, (int(docs_info.st_dev), int(docs_info.st_ino)))
             )
+            try:
+                architecture_descriptor = os.open("architecture", flags, dir_fd=docs_descriptor)
+            except OSError as error:
+                if error.errno != errno.ENOENT or not self.create_missing:
+                    raise
+                os.mkdir("architecture", dir_fd=docs_descriptor)
+                architecture_descriptor = os.open("architecture", flags, dir_fd=docs_descriptor)
+            architecture_info = os.fstat(architecture_descriptor)
+            self._posix_descriptors.append(
+                (
+                    self.architecture,
+                    architecture_descriptor,
+                    (int(architecture_info.st_dev), int(architecture_info.st_ino)),
+                )
+            )
+            self._architecture_descriptor = architecture_descriptor
+        except OSError as error:
+            raise GenerationError("manifest directory chain could not be securely bound") from error
+
+    def reverify(self) -> None:
+        if os.name == "nt":
+            for path, handle, expected in self._windows_handles:
+                if _windows_directory_handle_identity(handle, path) != expected:
+                    raise GenerationError(f"held manifest directory identity changed: {path}")
+                info = os.lstat(path)
+                if (
+                    stat.S_ISLNK(info.st_mode)
+                    or _is_reparse(info)
+                    or not stat.S_ISDIR(info.st_mode)
+                    or int(info.st_ino) != expected[1]
+                ):
+                    raise GenerationError(f"manifest directory path no longer names its held handle: {path}")
+        else:
+            for path, descriptor, expected in self._posix_descriptors:
+                handle_info = os.fstat(descriptor)
+                handle_identity = (int(handle_info.st_dev), int(handle_info.st_ino))
+                path_info = os.lstat(path)
+                path_identity = (int(path_info.st_dev), int(path_info.st_ino))
+                if (
+                    handle_identity != expected
+                    or path_identity != expected
+                    or stat.S_ISLNK(path_info.st_mode)
+                    or not stat.S_ISDIR(path_info.st_mode)
+                ):
+                    raise GenerationError(f"manifest directory path no longer names its held handle: {path}")
+
+    def stage(self, destination: Path, raw: bytes) -> str | Path:
+        assert self.architecture is not None
+        name = f".{destination.name}.{uuid.uuid4().hex}.tmp"
+        self.reverify()
+        if os.name == "nt":
+            candidate = self.architecture / name
             with candidate.open("xb") as stream:
-                stream.write(rendered[relative])
+                stream.write(raw)
                 stream.flush()
                 os.fsync(stream.fileno())
-            temporary[relative] = candidate
-        for relative, destination in destinations.items():
-            os.replace(temporary[relative], destination)
-            temporary.pop(relative)
-    finally:
-        for candidate in temporary.values():
+            return candidate
+        if self._architecture_descriptor is None:
+            raise GenerationError("POSIX manifest directory descriptor is absent")
+        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
+        descriptor = os.open(name, flags, 0o600, dir_fd=self._architecture_descriptor)
+        try:
+            offset = 0
+            while offset < len(raw):
+                offset += os.write(descriptor, raw[offset:])
+            os.fsync(descriptor)
+        finally:
+            os.close(descriptor)
+        return name
+
+    def replace(self, temporary: str | Path, destination: Path) -> None:
+        self.reverify()
+        if os.name == "nt":
+            os.replace(temporary, destination)
+            return
+        if self._architecture_descriptor is None or not isinstance(temporary, str):
+            raise GenerationError("POSIX manifest replacement arguments are invalid")
+        os.replace(
+            temporary,
+            destination.name,
+            src_dir_fd=self._architecture_descriptor,
+            dst_dir_fd=self._architecture_descriptor,
+        )
+
+    def cleanup(self, temporary: str | Path) -> None:
+        try:
+            if os.name == "nt":
+                Path(temporary).unlink()
+            elif self._architecture_descriptor is not None and isinstance(temporary, str):
+                os.unlink(temporary, dir_fd=self._architecture_descriptor)
+        except FileNotFoundError:
+            pass
+
+    def close(self) -> None:
+        for _, descriptor, _ in reversed(self._posix_descriptors):
             try:
-                candidate.unlink()
-            except FileNotFoundError:
+                os.close(descriptor)
+            except OSError:
                 pass
+        self._posix_descriptors.clear()
+        for _, handle, _ in reversed(self._windows_handles):
+            _close_windows_directory(handle)
+        self._windows_handles.clear()
+
+
+def write_manifests(
+    repository_root: Path,
+    state: Mapping[str, object],
+    *,
+    approved_seed_sha256: str | None,
+) -> None:
+    approved = validate_approval_digest(
+        approved_seed_sha256, str(state["entries_sha256"])
+    )
+    rendered = _render_all(state, approved)
+    with _BoundManifestDirectory(repository_root, create_missing=True) as transaction:
+        temporary: dict[str, str | Path] = {}
+        try:
+            for relative, destination in transaction.destinations.items():
+                temporary[relative] = transaction.stage(destination, rendered[relative])
+            transaction.reverify()
+            for relative, destination in transaction.destinations.items():
+                transaction.replace(temporary[relative], destination)
+                temporary.pop(relative)
+            transaction.reverify()
+        finally:
+            for candidate in temporary.values():
+                transaction.cleanup(candidate)
 
 
 def check_manifests(
     repository_root: Path, state: Mapping[str, object]
 ) -> None:
     historical_path = repository_root / MANIFEST_PATHS[2]
     try:
         historical_raw = read_regular_file_once(
             historical_path, maximum_bytes=4 * 1024 * 1024
         )
@@ -2315,21 +2560,21 @@ def _arguments(argv: Sequence[str] | None) -> argparse.Namespace:
 
 
 def main(argv: Sequence[str] | None = None) -> int:
     arguments = _arguments(argv)
     repository_root = Path(__file__).resolve().parents[1]
     try:
         if arguments.emit_seed_review is not None:
             _validated_seed_review_output(repository_root, arguments.emit_seed_review)
         elif arguments.write:
             validate_approval_format(arguments.approved_seed_sha256)
-            _verified_destinations(repository_root)
+            _validated_write_destination_intent(repository_root)
         else:
             _preflight_check(repository_root)
         state = derive_manifest_state(repository_root)
         if arguments.emit_seed_review is not None:
             emit_seed_review(repository_root, state, arguments.emit_seed_review)
         elif arguments.write:
             write_manifests(
                 repository_root,
                 state,
                 approved_seed_sha256=arguments.approved_seed_sha256,
