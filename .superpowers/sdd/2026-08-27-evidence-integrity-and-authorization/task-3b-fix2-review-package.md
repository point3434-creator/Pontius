# Review package: ba1e665c3337a8bbdda96ba2cc6fa5c6e52dd163..a16d1acb9570986fcd6f0442a7e38758aaa6b7d5

## Commits
a16d1ac fix(evidence): bind Windows manifest mutations

## Files changed
 tests/test_evidence_manifest_generation.py | 211 ++++++++++++++++++
 tools/generate_evidence_manifests.py       | 342 ++++++++++++++++++++++++++---
 2 files changed, 520 insertions(+), 33 deletions(-)

## Diff
diff --git a/tests/test_evidence_manifest_generation.py b/tests/test_evidence_manifest_generation.py
index b291600..c34a5ca 100644
--- a/tests/test_evidence_manifest_generation.py
+++ b/tests/test_evidence_manifest_generation.py
@@ -995,20 +995,231 @@ class Selected:
                 self.assertIsNotNone(failure)
                 self.assertEqual(list(architecture.iterdir()), [])
                 self.assertEqual(list(displaced.iterdir()), [])
             else:
                 self.assertIsNone(failure)
                 self.assertEqual(
                     tuple(sorted(path.name for path in architecture.iterdir())),
                     tuple(sorted(Path(path).name for path in GENERATOR.MANIFEST_PATHS)),
                 )
 
+    @unittest.skipUnless(os.name == "nt", "Windows handle-relative mutation test")
+    def test_windows_stage_is_bound_after_its_last_path_reverification(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-windows-stage-swap-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            displaced = root / "docs" / "architecture-displaced"
+            attempted = False
+            swapped = False
+            real_create = getattr(GENERATOR, "_windows_create_relative_file", None)
+
+            def swap_then_create(*args: object, **kwargs: object) -> object:
+                nonlocal attempted, swapped
+                attempted = True
+                try:
+                    os.replace(architecture, displaced)
+                    architecture.mkdir()
+                except OSError:
+                    pass
+                else:
+                    swapped = True
+                if real_create is None:
+                    raise AssertionError("handle-relative Windows create is absent")
+                return real_create(*args, **kwargs)
+
+            failure = None
+            with mock.patch.object(
+                GENERATOR,
+                "_windows_create_relative_file",
+                create=True,
+                side_effect=swap_then_create,
+            ):
+                try:
+                    GENERATOR.write_manifests(
+                        root,
+                        SAMPLE_STATE,
+                        approved_seed_sha256=SAMPLE_STATE["entries_sha256"],
+                    )
+                except GENERATOR.GenerationError as error:
+                    failure = error
+
+            self.assertTrue(attempted)
+            if swapped:
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
+    @unittest.skipUnless(os.name == "nt", "Windows handle-relative mutation test")
+    def test_windows_replace_is_bound_after_its_last_path_reverification(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-windows-replace-swap-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            displaced = root / "docs" / "architecture-displaced"
+            attempted = False
+            swapped = False
+            real_rename = getattr(GENERATOR, "_windows_rename_relative_file", None)
+
+            def swap_then_rename(*args: object, **kwargs: object) -> object:
+                nonlocal attempted, swapped
+                if not attempted:
+                    attempted = True
+                    try:
+                        os.replace(architecture, displaced)
+                        architecture.mkdir()
+                    except OSError:
+                        pass
+                    else:
+                        swapped = True
+                if real_rename is None:
+                    raise AssertionError("handle-relative Windows rename is absent")
+                return real_rename(*args, **kwargs)
+
+            failure = None
+            with mock.patch.object(
+                GENERATOR,
+                "_windows_rename_relative_file",
+                create=True,
+                side_effect=swap_then_rename,
+            ):
+                try:
+                    GENERATOR.write_manifests(
+                        root,
+                        SAMPLE_STATE,
+                        approved_seed_sha256=SAMPLE_STATE["entries_sha256"],
+                    )
+                except GENERATOR.GenerationError as error:
+                    failure = error
+
+            self.assertTrue(attempted)
+            if swapped:
+                self.assertIsNotNone(failure)
+                self.assertEqual(list(architecture.iterdir()), [])
+                self.assertFalse(any(path.name.endswith(".tmp") for path in displaced.iterdir()))
+                self.assertTrue(
+                    {path.name for path in displaced.iterdir()}
+                    <= {Path(path).name for path in GENERATOR.MANIFEST_PATHS}
+                )
+            else:
+                self.assertIsNone(failure)
+                self.assertEqual(
+                    tuple(sorted(path.name for path in architecture.iterdir())),
+                    tuple(sorted(Path(path).name for path in GENERATOR.MANIFEST_PATHS)),
+                )
+
+    @unittest.skipUnless(os.name == "nt", "Windows handle-relative mutation test")
+    def test_windows_cleanup_is_bound_after_its_last_path_reverification(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-windows-cleanup-swap-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            displaced = root / "docs" / "architecture-displaced"
+            attempted = False
+            real_dispose = getattr(GENERATOR, "_windows_dispose_relative_file", None)
+
+            def swap_then_dispose(*args: object, **kwargs: object) -> object:
+                nonlocal attempted
+                attempted = True
+                try:
+                    os.replace(architecture, displaced)
+                    architecture.mkdir()
+                except OSError:
+                    pass
+                if real_dispose is None:
+                    raise AssertionError("handle-relative Windows disposal is absent")
+                return real_dispose(*args, **kwargs)
+
+            with mock.patch.object(GENERATOR.os, "write", side_effect=OSError("injected write")), mock.patch.object(
+                GENERATOR,
+                "_windows_dispose_relative_file",
+                create=True,
+                side_effect=swap_then_dispose,
+            ):
+                with self.assertRaises(GENERATOR.GenerationError):
+                    GENERATOR.write_manifests(
+                        root,
+                        SAMPLE_STATE,
+                        approved_seed_sha256=SAMPLE_STATE["entries_sha256"],
+                    )
+
+            self.assertTrue(attempted)
+            self.assertEqual(list(architecture.iterdir()), [])
+            if displaced.exists():
+                self.assertEqual(list(displaced.iterdir()), [])
+
+    @unittest.skipUnless(os.name == "nt", "Windows native capability test")
+    def test_windows_native_file_api_unavailability_fails_closed(self) -> None:
+        failure = None
+        with mock.patch.object(GENERATOR.ctypes, "WinDLL", side_effect=OSError("unavailable")):
+            try:
+                GENERATOR._windows_file_api()
+            except BaseException as error:
+                failure = error
+        self.assertIsInstance(failure, GENERATOR.GenerationError)
+
+    def test_staging_write_failure_leaves_no_temp_or_destination_change(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-stage-write-failure-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            originals = {}
+            for relative in GENERATOR.MANIFEST_PATHS:
+                destination = root / relative
+                originals[relative] = f"original:{destination.name}".encode("ascii")
+                destination.write_bytes(originals[relative])
+
+            with mock.patch.object(GENERATOR.os, "write", side_effect=OSError("injected write")):
+                with self.assertRaises(GENERATOR.GenerationError):
+                    GENERATOR.write_manifests(
+                        root,
+                        SAMPLE_STATE,
+                        approved_seed_sha256=SAMPLE_STATE["entries_sha256"],
+                    )
+
+            self.assertEqual(
+                {relative: (root / relative).read_bytes() for relative in GENERATOR.MANIFEST_PATHS},
+                originals,
+            )
+            self.assertFalse(any(path.name.endswith(".tmp") for path in architecture.iterdir()))
+
+    def test_staging_fsync_failure_leaves_no_temp_or_destination_change(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-stage-fsync-failure-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            originals = {}
+            for relative in GENERATOR.MANIFEST_PATHS:
+                destination = root / relative
+                originals[relative] = f"original:{destination.name}".encode("ascii")
+                destination.write_bytes(originals[relative])
+
+            with mock.patch.object(GENERATOR.os, "fsync", side_effect=OSError("injected fsync")):
+                with self.assertRaises((GENERATOR.GenerationError, OSError)):
+                    GENERATOR.write_manifests(
+                        root,
+                        SAMPLE_STATE,
+                        approved_seed_sha256=SAMPLE_STATE["entries_sha256"],
+                    )
+
+            self.assertEqual(
+                {relative: (root / relative).read_bytes() for relative in GENERATOR.MANIFEST_PATHS},
+                originals,
+            )
+            self.assertFalse(any(path.name.endswith(".tmp") for path in architecture.iterdir()))
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
index f957774..d904dc4 100644
--- a/tools/generate_evidence_manifests.py
+++ b/tools/generate_evidence_manifests.py
@@ -20,20 +20,21 @@ import sys
 import tempfile
 import threading
 import time
 import tomllib
 from typing import Any
 import uuid
 
 if os.name == "nt":
     import ctypes
     from ctypes import wintypes
+    import msvcrt
 
 
 BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
 GIT_EXECUTABLE = Path("C:/Program Files/Git/cmd/git.exe")
 MANIFEST_PATHS = (
     "docs/architecture/sealed-current-files.toml",
     "docs/architecture/sealed-current-absences.toml",
     "docs/architecture/historical-blobs.toml",
     "docs/architecture/retained-v7.toml",
 )
@@ -2121,20 +2122,61 @@ if os.name == "nt":
             ("ftLastWriteTime", wintypes.FILETIME),
             ("dwVolumeSerialNumber", wintypes.DWORD),
             ("nFileSizeHigh", wintypes.DWORD),
             ("nFileSizeLow", wintypes.DWORD),
             ("nNumberOfLinks", wintypes.DWORD),
             ("nFileIndexHigh", wintypes.DWORD),
             ("nFileIndexLow", wintypes.DWORD),
         )
 
 
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
 def _windows_directory_api() -> tuple[Any, Any, Any]:
     if os.name != "nt":
         raise GenerationError("Windows directory handles are unavailable")
     kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
     create = kernel32.CreateFileW
     create.argtypes = (
         wintypes.LPCWSTR,
         wintypes.DWORD,
         wintypes.DWORD,
         wintypes.LPVOID,
@@ -2152,21 +2194,21 @@ def _windows_directory_api() -> tuple[Any, Any, Any]:
     close = kernel32.CloseHandle
     close.argtypes = (wintypes.HANDLE,)
     close.restype = wintypes.BOOL
     return create, information, close
 
 
 def _windows_open_directory(path: Path) -> int:
     create, _, close = _windows_directory_api()
     handle = create(
         str(path),
-        0x00000080,
+        0x00000020 | 0x00000080 | 0x00100000,
         0x00000001 | 0x00000002,
         None,
         3,
         0x02000000 | 0x00200000,
         None,
     )
     invalid = ctypes.c_void_p(-1).value
     if handle == invalid:
         error = ctypes.get_last_error()
         raise GenerationError(f"manifest directory handle could not be opened: {path}") from OSError(
@@ -2193,31 +2235,203 @@ def _windows_directory_handle_identity(handle: int, path: Path) -> tuple[int, in
         raise GenerationError(f"manifest directory handle is not a nonreparse directory: {path}")
     file_index = (int(value.nFileIndexHigh) << 32) | int(value.nFileIndexLow)
     return int(value.dwVolumeSerialNumber), file_index
 
 
 def _close_windows_directory(handle: int) -> None:
     _, _, close = _windows_directory_api()
     close(handle)
 
 
+def _windows_file_api() -> tuple[Any, Any, Any]:
+    if os.name != "nt":
+        raise GenerationError("Windows handle-relative file APIs are unavailable")
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
+        close = kernel32.CloseHandle
+        close.argtypes = (wintypes.HANDLE,)
+        close.restype = wintypes.BOOL
+    except (AttributeError, OSError) as error:
+        raise GenerationError("Windows handle-relative file APIs are unavailable") from error
+    return create, set_information, close
+
+
+def _validated_relative_manifest_name(name: str) -> str:
+    if (
+        not isinstance(name, str)
+        or not name
+        or name in (".", "..")
+        or any(character in name for character in ("/", "\\", ":", "\0"))
+    ):
+        raise GenerationError("manifest mutation name must be one relative path component")
+    return name
+
+
+def _windows_create_relative_file(directory_handle: int, name: str) -> int:
+    name = _validated_relative_manifest_name(name)
+    create, _, close = _windows_file_api()
+    encoded_name = name.encode("utf-16-le")
+    if len(encoded_name) > 0xFFFE:
+        raise GenerationError("manifest temporary name is too long")
+    name_buffer = ctypes.create_unicode_buffer(name)
+    unicode_name = _WindowsUnicodeString(
+        len(encoded_name),
+        len(encoded_name),
+        ctypes.cast(name_buffer, wintypes.LPWSTR),
+    )
+    attributes = _WindowsObjectAttributes(
+        ctypes.sizeof(_WindowsObjectAttributes),
+        wintypes.HANDLE(directory_handle),
+        ctypes.pointer(unicode_name),
+        0x00000040,
+        None,
+        None,
+    )
+    status_block = _WindowsIOStatusBlock()
+    handle = wintypes.HANDLE()
+    status = int(
+        create(
+            ctypes.byref(handle),
+            0x00000002 | 0x00000080 | 0x00010000 | 0x00100000,
+            ctypes.byref(attributes),
+            ctypes.byref(status_block),
+            None,
+            0x00000080,
+            0x00000001 | 0x00000002,
+            2,
+            0x00000020 | 0x00000040,
+            None,
+            0,
+        )
+    )
+    if (
+        status != 0
+        or int(status_block.Status) != 0
+        or int(status_block.Information) != 2
+        or not handle.value
+    ):
+        if handle.value:
+            try:
+                _windows_dispose_relative_file(int(handle.value))
+            finally:
+                close(handle)
+        raise GenerationError(
+            "handle-relative manifest temporary creation returned malformed status "
+            f"0x{status & 0xFFFFFFFF:08x}/{int(status_block.Status) & 0xFFFFFFFF:08x}/"
+            f"{int(status_block.Information)}"
+        )
+    native_handle = int(handle.value)
+    try:
+        return msvcrt.open_osfhandle(native_handle, os.O_WRONLY | os.O_BINARY)
+    except BaseException:
+        try:
+            _windows_dispose_relative_file(native_handle)
+        finally:
+            close(native_handle)
+        raise
+
+
+def _windows_rename_relative_file(
+    file_handle: int, directory_handle: int, destination_name: str
+) -> None:
+    destination_name = _validated_relative_manifest_name(destination_name)
+    _, set_information, _ = _windows_file_api()
+    encoded_name = destination_name.encode("utf-16-le")
+    name_offset = _WindowsFileRenameInformation.FileName.offset
+    buffer = ctypes.create_string_buffer(name_offset + len(encoded_name))
+    information = ctypes.cast(
+        buffer, ctypes.POINTER(_WindowsFileRenameInformation)
+    ).contents
+    information.ReplaceIfExists = 1
+    information.RootDirectory = wintypes.HANDLE(directory_handle)
+    information.FileNameLength = len(encoded_name)
+    ctypes.memmove(ctypes.addressof(buffer) + name_offset, encoded_name, len(encoded_name))
+    status_block = _WindowsIOStatusBlock()
+    status = int(
+        set_information(
+            wintypes.HANDLE(file_handle),
+            ctypes.byref(status_block),
+            ctypes.byref(buffer),
+            len(buffer),
+            10,
+        )
+    )
+    if status != 0 or int(status_block.Status) != 0:
+        raise GenerationError(
+            "handle-relative manifest replacement returned malformed status "
+            f"0x{status & 0xFFFFFFFF:08x}/{int(status_block.Status) & 0xFFFFFFFF:08x}"
+        )
+
+
+def _windows_dispose_relative_file(file_handle: int) -> None:
+    _, set_information, _ = _windows_file_api()
+    information = _WindowsFileDispositionInformation(1)
+    status_block = _WindowsIOStatusBlock()
+    status = int(
+        set_information(
+            wintypes.HANDLE(file_handle),
+            ctypes.byref(status_block),
+            ctypes.byref(information),
+            ctypes.sizeof(information),
+            13,
+        )
+    )
+    if status != 0 or int(status_block.Status) != 0:
+        raise GenerationError(
+            "handle-bound manifest temporary disposal returned malformed status "
+            f"0x{status & 0xFFFFFFFF:08x}/{int(status_block.Status) & 0xFFFFFFFF:08x}"
+        )
+
+
+class _BoundTemporary:
+    def __init__(self, name: str, descriptor: int | None) -> None:
+        self.name = name
+        self.descriptor = descriptor
+
+
 class _BoundManifestDirectory:
     def __init__(self, repository_root: Path, *, create_missing: bool) -> None:
         self.repository_root = repository_root
         self.create_missing = create_missing
         self.root: Path | None = None
         self.docs: Path | None = None
         self.architecture: Path | None = None
         self.destinations: dict[str, Path] = {}
         self._posix_descriptors: list[tuple[Path, int, tuple[int, int]]] = []
         self._windows_handles: list[tuple[Path, int, tuple[int, int]]] = []
         self._architecture_descriptor: int | None = None
+        self._owned_temporary: list[_BoundTemporary] = []
 
     def __enter__(self) -> "_BoundManifestDirectory":
         if not self.repository_root.is_absolute():
             raise GenerationError("repository root must be absolute")
         _validated_directory(self.repository_root, "repository root")
         self.root = self.repository_root.resolve(strict=True)
         self.docs = self.root / "docs"
         self.architecture = self.docs / "architecture"
         try:
             if os.name == "nt":
@@ -2313,102 +2527,164 @@ class _BoundManifestDirectory:
                 path_info = os.lstat(path)
                 path_identity = (int(path_info.st_dev), int(path_info.st_ino))
                 if (
                     handle_identity != expected
                     or path_identity != expected
                     or stat.S_ISLNK(path_info.st_mode)
                     or not stat.S_ISDIR(path_info.st_mode)
                 ):
                     raise GenerationError(f"manifest directory path no longer names its held handle: {path}")
 
-    def stage(self, destination: Path, raw: bytes) -> str | Path:
+    def stage(self, destination: Path, raw: bytes) -> _BoundTemporary:
         assert self.architecture is not None
-        name = f".{destination.name}.{uuid.uuid4().hex}.tmp"
         self.reverify()
+        name = f".{destination.name}.{uuid.uuid4().hex}.tmp"
         if os.name == "nt":
-            candidate = self.architecture / name
-            with candidate.open("xb") as stream:
-                stream.write(raw)
-                stream.flush()
-                os.fsync(stream.fileno())
-            return candidate
+            if not self._windows_handles:
+                raise GenerationError("Windows manifest directory handle is absent")
+            architecture_handle = self._windows_handles[-1][1]
+            try:
+                descriptor = _windows_create_relative_file(architecture_handle, name)
+            except OSError as error:
+                raise GenerationError("manifest temporary file could not be created") from error
+            temporary = _BoundTemporary(name, descriptor)
+            self._owned_temporary.append(temporary)
+            try:
+                self.reverify()
+                offset = 0
+                while offset < len(raw):
+                    written = os.write(descriptor, raw[offset:])
+                    if written <= 0:
+                        raise OSError("manifest temporary write made no progress")
+                    offset += written
+                os.fsync(descriptor)
+                self.reverify()
+                return temporary
+            except GenerationError:
+                raise
+            except OSError as error:
+                raise GenerationError("manifest temporary file could not be staged") from error
         if self._architecture_descriptor is None:
             raise GenerationError("POSIX manifest directory descriptor is absent")
         flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
-        descriptor = os.open(name, flags, 0o600, dir_fd=self._architecture_descriptor)
+        try:
+            descriptor = os.open(name, flags, 0o600, dir_fd=self._architecture_descriptor)
+        except OSError as error:
+            raise GenerationError("manifest temporary file could not be created") from error
+        temporary = _BoundTemporary(name, None)
+        self._owned_temporary.append(temporary)
         try:
             offset = 0
             while offset < len(raw):
-                offset += os.write(descriptor, raw[offset:])
+                written = os.write(descriptor, raw[offset:])
+                if written <= 0:
+                    raise OSError("manifest temporary write made no progress")
+                offset += written
             os.fsync(descriptor)
+            self.reverify()
+        except GenerationError:
+            raise
+        except OSError as error:
+            raise GenerationError("manifest temporary file could not be staged") from error
         finally:
             os.close(descriptor)
-        return name
+        return temporary
 
-    def replace(self, temporary: str | Path, destination: Path) -> None:
+    def replace(self, temporary: _BoundTemporary, destination: Path) -> None:
+        if temporary not in self._owned_temporary:
+            raise GenerationError("manifest temporary ownership is invalid")
         self.reverify()
         if os.name == "nt":
-            os.replace(temporary, destination)
+            if temporary.descriptor is None or not self._windows_handles:
+                raise GenerationError("Windows manifest temporary handle is absent")
+            architecture_handle = self._windows_handles[-1][1]
+            native_handle = msvcrt.get_osfhandle(temporary.descriptor)
+            _windows_rename_relative_file(
+                native_handle, architecture_handle, destination.name
+            )
+            self._owned_temporary.remove(temporary)
+            os.close(temporary.descriptor)
+            temporary.descriptor = None
+            self.reverify()
             return
-        if self._architecture_descriptor is None or not isinstance(temporary, str):
+        if self._architecture_descriptor is None:
             raise GenerationError("POSIX manifest replacement arguments are invalid")
         os.replace(
-            temporary,
+            temporary.name,
             destination.name,
             src_dir_fd=self._architecture_descriptor,
             dst_dir_fd=self._architecture_descriptor,
         )
+        self._owned_temporary.remove(temporary)
+        self.reverify()
 
-    def cleanup(self, temporary: str | Path) -> None:
+    def cleanup(self, temporary: _BoundTemporary) -> None:
+        if temporary not in self._owned_temporary:
+            return
+        if os.name == "nt":
+            if temporary.descriptor is None:
+                raise GenerationError("Windows manifest temporary handle is absent")
+            native_handle = msvcrt.get_osfhandle(temporary.descriptor)
+            try:
+                _windows_dispose_relative_file(native_handle)
+            finally:
+                os.close(temporary.descriptor)
+                temporary.descriptor = None
+                self._owned_temporary.remove(temporary)
+            return
+        if self._architecture_descriptor is None:
+            raise GenerationError("POSIX manifest directory descriptor is absent")
         try:
-            if os.name == "nt":
-                Path(temporary).unlink()
-            elif self._architecture_descriptor is not None and isinstance(temporary, str):
-                os.unlink(temporary, dir_fd=self._architecture_descriptor)
+            os.unlink(temporary.name, dir_fd=self._architecture_descriptor)
         except FileNotFoundError:
             pass
+        self._owned_temporary.remove(temporary)
 
     def close(self) -> None:
+        cleanup_failure: GenerationError | None = None
+        for temporary in tuple(self._owned_temporary):
+            try:
+                self.cleanup(temporary)
+            except GenerationError as error:
+                if cleanup_failure is None:
+                    cleanup_failure = error
         for _, descriptor, _ in reversed(self._posix_descriptors):
             try:
                 os.close(descriptor)
             except OSError:
                 pass
         self._posix_descriptors.clear()
         for _, handle, _ in reversed(self._windows_handles):
             _close_windows_directory(handle)
         self._windows_handles.clear()
+        if cleanup_failure is not None:
+            raise cleanup_failure
 
 
 def write_manifests(
     repository_root: Path,
     state: Mapping[str, object],
     *,
     approved_seed_sha256: str | None,
 ) -> None:
     approved = validate_approval_digest(
         approved_seed_sha256, str(state["entries_sha256"])
     )
     rendered = _render_all(state, approved)
     with _BoundManifestDirectory(repository_root, create_missing=True) as transaction:
-        temporary: dict[str, str | Path] = {}
-        try:
-            for relative, destination in transaction.destinations.items():
-                temporary[relative] = transaction.stage(destination, rendered[relative])
-            transaction.reverify()
-            for relative, destination in transaction.destinations.items():
-                transaction.replace(temporary[relative], destination)
-                temporary.pop(relative)
-            transaction.reverify()
-        finally:
-            for candidate in temporary.values():
-                transaction.cleanup(candidate)
+        temporary: dict[str, _BoundTemporary] = {}
+        for relative, destination in transaction.destinations.items():
+            temporary[relative] = transaction.stage(destination, rendered[relative])
+        transaction.reverify()
+        for relative, destination in transaction.destinations.items():
+            transaction.replace(temporary[relative], destination)
+        transaction.reverify()
 
 
 def check_manifests(
     repository_root: Path, state: Mapping[str, object]
 ) -> None:
     historical_path = repository_root / MANIFEST_PATHS[2]
     try:
         historical_raw = read_regular_file_once(
             historical_path, maximum_bytes=4 * 1024 * 1024
         )
