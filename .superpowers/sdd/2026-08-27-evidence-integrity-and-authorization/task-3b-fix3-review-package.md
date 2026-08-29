# Review package: a16d1acb9570986fcd6f0442a7e38758aaa6b7d5..75caae4bc0e723f7f2bbe7d0fb596c4213ab53b7

## Commits
75caae4 fix(evidence): close native transaction gaps

## Files changed
 tests/test_evidence_manifest_generation.py | 308 ++++++++++++++++++++++++++++-
 tools/generate_evidence_manifests.py       | 279 ++++++++++++++++++--------
 2 files changed, 496 insertions(+), 91 deletions(-)

## Diff
diff --git a/tests/test_evidence_manifest_generation.py b/tests/test_evidence_manifest_generation.py
index c34a5ca..7edd481 100644
--- a/tests/test_evidence_manifest_generation.py
+++ b/tests/test_evidence_manifest_generation.py
@@ -1128,60 +1128,346 @@ class Selected:
                 attempted = True
                 try:
                     os.replace(architecture, displaced)
                     architecture.mkdir()
                 except OSError:
                     pass
                 if real_dispose is None:
                     raise AssertionError("handle-relative Windows disposal is absent")
                 return real_dispose(*args, **kwargs)
 
-            with mock.patch.object(GENERATOR.os, "write", side_effect=OSError("injected write")), mock.patch.object(
+            with mock.patch.object(
+                GENERATOR,
+                "_windows_write_file",
+                create=True,
+                side_effect=OSError("injected write"),
+            ), mock.patch.object(
                 GENERATOR,
                 "_windows_dispose_relative_file",
                 create=True,
                 side_effect=swap_then_dispose,
             ):
                 with self.assertRaises(GENERATOR.GenerationError):
                     GENERATOR.write_manifests(
                         root,
                         SAMPLE_STATE,
                         approved_seed_sha256=SAMPLE_STATE["entries_sha256"],
                     )
 
             self.assertTrue(attempted)
             self.assertEqual(list(architecture.iterdir()), [])
             if displaced.exists():
                 self.assertEqual(list(displaced.iterdir()), [])
 
     @unittest.skipUnless(os.name == "nt", "Windows native capability test")
     def test_windows_native_file_api_unavailability_fails_closed(self) -> None:
+        for unavailable in (OSError("unavailable"), object()):
+            with self.subTest(unavailable=type(unavailable).__name__):
+                failure = None
+                replacement = mock.Mock(side_effect=unavailable) if isinstance(unavailable, OSError) else mock.Mock(return_value=unavailable)
+                with mock.patch.object(GENERATOR.ctypes, "WinDLL", replacement):
+                    try:
+                        GENERATOR._windows_file_api()
+                    except BaseException as error:
+                        failure = error
+                self.assertIsInstance(failure, GENERATOR.GenerationError)
+
+    @unittest.skipUnless(os.name == "nt", "Windows native exclusivity test")
+    def test_windows_staged_temp_rejects_a_second_writer_while_owned(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-exclusive-temp-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            real_create_relative = GENERATOR._windows_create_relative_file
+            rejected = False
+
+            def create_and_probe(directory_handle: int, name: str) -> int:
+                nonlocal rejected
+                owned = real_create_relative(directory_handle, name)
+                create, _, close = GENERATOR._windows_directory_api()
+                probe = create(
+                    str(architecture / name),
+                    0x40000000,
+                    0x00000001 | 0x00000002 | 0x00000004,
+                    None,
+                    3,
+                    0x00000080,
+                    None,
+                )
+                invalid = GENERATOR.ctypes.c_void_p(-1).value
+                rejected = probe == invalid
+                if not rejected:
+                    close(probe)
+                return owned
+
+            with mock.patch.object(
+                GENERATOR, "_windows_create_relative_file", side_effect=create_and_probe
+            ):
+                GENERATOR.write_manifests(
+                    root,
+                    SAMPLE_STATE,
+                    approved_seed_sha256=SAMPLE_STATE["entries_sha256"],
+                )
+            self.assertTrue(rejected)
+
+    @unittest.skipUnless(os.name == "nt", "Windows native lifecycle test")
+    def test_windows_renamed_candidate_remains_owned_until_close_succeeds(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-rename-close-") as directory:
+            root = Path(directory).resolve()
+            (root / "docs" / "architecture").mkdir(parents=True)
+            real_close = getattr(GENERATOR, "_windows_close_file_handle", None)
+            attempts = 0
+
+            def fail_once_then_close(handle: int) -> None:
+                nonlocal attempts
+                attempts += 1
+                if attempts == 1:
+                    raise GENERATOR.GenerationError("injected close failure")
+                if real_close is None:
+                    raise AssertionError("tracked Windows file close is absent")
+                real_close(handle)
+
+            failure = None
+            with mock.patch.object(
+                GENERATOR,
+                "_windows_close_file_handle",
+                create=True,
+                side_effect=fail_once_then_close,
+            ):
+                try:
+                    GENERATOR.write_manifests(
+                        root,
+                        SAMPLE_STATE,
+                        approved_seed_sha256=SAMPLE_STATE["entries_sha256"],
+                    )
+                except BaseException as error:
+                    failure = error
+            self.assertIsInstance(failure, GENERATOR.GenerationError)
+            self.assertGreaterEqual(attempts, 2)
+            architecture = root / "docs" / "architecture"
+            self.assertFalse(any(path.name.endswith(".tmp") for path in architecture.iterdir()))
+
+    @unittest.skipUnless(os.name == "nt", "Windows native lifecycle test")
+    def test_windows_cleanup_continues_after_disposition_failure(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-multi-cleanup-") as directory:
+            root = Path(directory).resolve()
+            architecture = root / "docs" / "architecture"
+            architecture.mkdir(parents=True)
+            real_dispose = GENERATOR._windows_dispose_relative_file
+            attempts = 0
+
+            def fail_first_disposition(handle: int) -> None:
+                nonlocal attempts
+                attempts += 1
+                if attempts == 1:
+                    raise GENERATOR.GenerationError("injected disposition failure")
+                real_dispose(handle)
+
+            failure = None
+            with mock.patch.object(
+                GENERATOR,
+                "_windows_dispose_relative_file",
+                side_effect=fail_first_disposition,
+            ):
+                try:
+                    with GENERATOR._BoundManifestDirectory(root, create_missing=False) as transaction:
+                        destinations = tuple(transaction.destinations.values())
+                        transaction.stage(destinations[0], b"first")
+                        transaction.stage(destinations[1], b"second")
+                        raise GENERATOR.GenerationError("trigger cleanup")
+                except BaseException as error:
+                    failure = error
+            self.assertIsInstance(failure, GENERATOR.GenerationError)
+            self.assertGreaterEqual(attempts, 2)
+            self.assertFalse(any(path.name.endswith(".tmp") for path in architecture.iterdir()))
+
+    @unittest.skipUnless(os.name == "nt", "Windows native lifecycle test")
+    def test_windows_directory_cleanup_attempts_every_held_handle(self) -> None:
+        with tempfile.TemporaryDirectory(
+            prefix="pontius-task3-directory-close-", ignore_cleanup_errors=True
+        ) as directory:
+            root = Path(directory).resolve()
+            (root / "docs" / "architecture").mkdir(parents=True)
+            transaction = GENERATOR._BoundManifestDirectory(root, create_missing=False)
+            transaction.__enter__()
+            held = tuple(handle for _, handle, _ in transaction._windows_handles)
+            real_close = GENERATOR._close_windows_directory
+            attempts = []
+
+            def close_and_fail_first(handle: int) -> None:
+                attempts.append(handle)
+                real_close(handle)
+                if len(attempts) == 1:
+                    raise GENERATOR.GenerationError("injected directory close failure")
+
+            failure = None
+            with mock.patch.object(
+                GENERATOR, "_close_windows_directory", side_effect=close_and_fail_first
+            ):
+                try:
+                    transaction.close()
+                except BaseException as error:
+                    failure = error
+            for handle in held:
+                if handle not in attempts:
+                    real_close(handle)
+            transaction._windows_handles.clear()
+            self.assertIsInstance(failure, GENERATOR.GenerationError)
+            self.assertEqual(attempts, list(reversed(held)))
+
+    @unittest.skipUnless(os.name == "nt", "Windows native status test")
+    def test_windows_native_create_rejects_malformed_status_and_api_errors(self) -> None:
+        cases = (
+            ("nonzero", -1, -1, 0, 0),
+            ("null", 0, 0, 2, 0),
+            ("invalid", 0, 0, 2, -1),
+            ("information", 0, 0, 1, 0),
+        )
+        for label, returned, io_status, information, handle_value in cases:
+            with self.subTest(label=label):
+                def fake_create(handle: object, _access: object, _attributes: object, status: object, *_rest: object) -> int:
+                    handle_pointer = GENERATOR.ctypes.cast(handle, GENERATOR.ctypes.POINTER(GENERATOR.wintypes.HANDLE))
+                    handle_pointer.contents.value = handle_value
+                    status_pointer = GENERATOR.ctypes.cast(status, GENERATOR.ctypes.POINTER(GENERATOR._WindowsIOStatusBlock))
+                    status_pointer.contents.Status = io_status
+                    status_pointer.contents.Information = information
+                    return returned
+
+                def fake_set(_handle: object, status: object, *_rest: object) -> int:
+                    status_pointer = GENERATOR.ctypes.cast(status, GENERATOR.ctypes.POINTER(GENERATOR._WindowsIOStatusBlock))
+                    status_pointer.contents.Status = 0
+                    return 0
+
+                failure = None
+                with mock.patch.object(
+                    GENERATOR,
+                    "_windows_file_api",
+                    return_value=(
+                        fake_create,
+                        fake_set,
+                        mock.Mock(return_value=1),
+                        mock.Mock(return_value=1),
+                        mock.Mock(return_value=1),
+                    ),
+                ):
+                    try:
+                        GENERATOR._windows_create_relative_file(123, "candidate.tmp")
+                    except BaseException as error:
+                        failure = error
+                self.assertIsInstance(failure, GENERATOR.GenerationError)
+
+        def raising_create(*_args: object) -> int:
+            raise OSError("native create failed")
+
         failure = None
-        with mock.patch.object(GENERATOR.ctypes, "WinDLL", side_effect=OSError("unavailable")):
+        with mock.patch.object(
+            GENERATOR,
+            "_windows_file_api",
+            return_value=(raising_create, mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock()),
+        ):
             try:
-                GENERATOR._windows_file_api()
+                GENERATOR._windows_create_relative_file(123, "candidate.tmp")
             except BaseException as error:
                 failure = error
         self.assertIsInstance(failure, GENERATOR.GenerationError)
+        self.assertIsInstance(failure.__cause__, OSError)
+
+    @unittest.skipUnless(os.name == "nt", "Windows native status test")
+    def test_windows_native_rename_disposition_and_close_errors_are_typed(self) -> None:
+        def raising_set(*_args: object) -> int:
+            raise OSError("native set failed")
+
+        for operation, arguments in (
+            (GENERATOR._windows_rename_relative_file, (123, 456, "manifest.toml")),
+            (GENERATOR._windows_dispose_relative_file, (123,)),
+        ):
+            for mode in ("exception", "status"):
+                with self.subTest(operation=operation.__name__, mode=mode):
+                    def failing_status(_handle: object, status: object, *_rest: object) -> int:
+                        status_pointer = GENERATOR.ctypes.cast(
+                            status, GENERATOR.ctypes.POINTER(GENERATOR._WindowsIOStatusBlock)
+                        )
+                        status_pointer.contents.Status = -1
+                        return -1
+
+                    set_information = raising_set if mode == "exception" else failing_status
+                    failure = None
+                    with mock.patch.object(
+                        GENERATOR,
+                        "_windows_file_api",
+                        return_value=(
+                            mock.Mock(),
+                            set_information,
+                            mock.Mock(),
+                            mock.Mock(),
+                            mock.Mock(),
+                        ),
+                    ):
+                        try:
+                            operation(*arguments)
+                        except BaseException as error:
+                            failure = error
+                    self.assertIsInstance(failure, GENERATOR.GenerationError)
+                    if mode == "exception":
+                        self.assertIsInstance(failure.__cause__, OSError)
+
+        close = getattr(GENERATOR, "_windows_close_file_handle", None)
+        for close_result in (0, OSError("native close failed")):
+            with self.subTest(close_result=type(close_result).__name__):
+                failure = None
+                close_function = (
+                    mock.Mock(side_effect=close_result)
+                    if isinstance(close_result, OSError)
+                    else mock.Mock(return_value=close_result)
+                )
+                try:
+                    if close is None:
+                        raise AssertionError("tracked Windows file close is absent")
+                    with mock.patch.object(
+                        GENERATOR,
+                        "_windows_file_api",
+                        return_value=(
+                            mock.Mock(),
+                            mock.Mock(),
+                            mock.Mock(),
+                            mock.Mock(),
+                            close_function,
+                        ),
+                    ):
+                        close(123)
+                except BaseException as error:
+                    failure = error
+                self.assertIsInstance(failure, GENERATOR.GenerationError)
+                self.assertIsInstance(failure.__cause__, OSError)
 
     def test_staging_write_failure_leaves_no_temp_or_destination_change(self) -> None:
         with tempfile.TemporaryDirectory(prefix="pontius-task3-stage-write-failure-") as directory:
             root = Path(directory).resolve()
             architecture = root / "docs" / "architecture"
             architecture.mkdir(parents=True)
             originals = {}
             for relative in GENERATOR.MANIFEST_PATHS:
                 destination = root / relative
                 originals[relative] = f"original:{destination.name}".encode("ascii")
                 destination.write_bytes(originals[relative])
 
-            with mock.patch.object(GENERATOR.os, "write", side_effect=OSError("injected write")):
+            write_patcher = (
+                mock.patch.object(
+                    GENERATOR,
+                    "_windows_write_file",
+                    create=True,
+                    side_effect=OSError("injected write"),
+                )
+                if os.name == "nt"
+                else mock.patch.object(GENERATOR.os, "write", side_effect=OSError("injected write"))
+            )
+            with write_patcher:
                 with self.assertRaises(GENERATOR.GenerationError):
                     GENERATOR.write_manifests(
                         root,
                         SAMPLE_STATE,
                         approved_seed_sha256=SAMPLE_STATE["entries_sha256"],
                     )
 
             self.assertEqual(
                 {relative: (root / relative).read_bytes() for relative in GENERATOR.MANIFEST_PATHS},
                 originals,
@@ -1192,22 +1478,32 @@ class Selected:
         with tempfile.TemporaryDirectory(prefix="pontius-task3-stage-fsync-failure-") as directory:
             root = Path(directory).resolve()
             architecture = root / "docs" / "architecture"
             architecture.mkdir(parents=True)
             originals = {}
             for relative in GENERATOR.MANIFEST_PATHS:
                 destination = root / relative
                 originals[relative] = f"original:{destination.name}".encode("ascii")
                 destination.write_bytes(originals[relative])
 
-            with mock.patch.object(GENERATOR.os, "fsync", side_effect=OSError("injected fsync")):
-                with self.assertRaises((GENERATOR.GenerationError, OSError)):
+            flush_patcher = (
+                mock.patch.object(
+                    GENERATOR,
+                    "_windows_flush_file",
+                    create=True,
+                    side_effect=OSError("injected flush"),
+                )
+                if os.name == "nt"
+                else mock.patch.object(GENERATOR.os, "fsync", side_effect=OSError("injected fsync"))
+            )
+            with flush_patcher:
+                with self.assertRaises(GENERATOR.GenerationError):
                     GENERATOR.write_manifests(
                         root,
                         SAMPLE_STATE,
                         approved_seed_sha256=SAMPLE_STATE["entries_sha256"],
                     )
 
             self.assertEqual(
                 {relative: (root / relative).read_bytes() for relative in GENERATOR.MANIFEST_PATHS},
                 originals,
             )
diff --git a/tools/generate_evidence_manifests.py b/tools/generate_evidence_manifests.py
index d904dc4..357be26 100644
--- a/tools/generate_evidence_manifests.py
+++ b/tools/generate_evidence_manifests.py
@@ -20,21 +20,20 @@ import sys
 import tempfile
 import threading
 import time
 import tomllib
 from typing import Any
 import uuid
 
 if os.name == "nt":
     import ctypes
     from ctypes import wintypes
-    import msvcrt
 
 
 BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
 GIT_EXECUTABLE = Path("C:/Program Files/Git/cmd/git.exe")
 MANIFEST_PATHS = (
     "docs/architecture/sealed-current-files.toml",
     "docs/architecture/sealed-current-absences.toml",
     "docs/architecture/historical-blobs.toml",
     "docs/architecture/retained-v7.toml",
 )
@@ -2232,24 +2231,32 @@ def _windows_directory_handle_identity(handle: int, path: Path) -> tuple[int, in
         )
     attributes = int(value.dwFileAttributes)
     if not attributes & 0x00000010 or attributes & _REPARSE_ATTRIBUTE:
         raise GenerationError(f"manifest directory handle is not a nonreparse directory: {path}")
     file_index = (int(value.nFileIndexHigh) << 32) | int(value.nFileIndexLow)
     return int(value.dwVolumeSerialNumber), file_index
 
 
 def _close_windows_directory(handle: int) -> None:
     _, _, close = _windows_directory_api()
-    close(handle)
+    try:
+        succeeded = close(handle)
+    except (OSError, ValueError) as error:
+        raise GenerationError("manifest directory handle close failed") from error
+    if not succeeded:
+        error = ctypes.get_last_error()
+        raise GenerationError("manifest directory handle close failed") from OSError(
+            error, os.strerror(error)
+        )
 
 
-def _windows_file_api() -> tuple[Any, Any, Any]:
+def _windows_file_api() -> tuple[Any, Any, Any, Any, Any]:
     if os.name != "nt":
         raise GenerationError("Windows handle-relative file APIs are unavailable")
     try:
         ntdll = ctypes.WinDLL("ntdll")
         create = ntdll.NtCreateFile
         create.argtypes = (
             ctypes.POINTER(wintypes.HANDLE),
             wintypes.DWORD,
             ctypes.POINTER(_WindowsObjectAttributes),
             ctypes.POINTER(_WindowsIOStatusBlock),
@@ -2265,159 +2272,235 @@ def _windows_file_api() -> tuple[Any, Any, Any]:
         set_information = ntdll.NtSetInformationFile
         set_information.argtypes = (
             wintypes.HANDLE,
             ctypes.POINTER(_WindowsIOStatusBlock),
             wintypes.LPVOID,
             wintypes.ULONG,
             ctypes.c_int,
         )
         set_information.restype = wintypes.LONG
         kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
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
         close = kernel32.CloseHandle
         close.argtypes = (wintypes.HANDLE,)
         close.restype = wintypes.BOOL
     except (AttributeError, OSError) as error:
         raise GenerationError("Windows handle-relative file APIs are unavailable") from error
-    return create, set_information, close
+    return create, set_information, write, flush, close
 
 
 def _validated_relative_manifest_name(name: str) -> str:
     if (
         not isinstance(name, str)
         or not name
         or name in (".", "..")
         or any(character in name for character in ("/", "\\", ":", "\0"))
     ):
         raise GenerationError("manifest mutation name must be one relative path component")
     return name
 
 
 def _windows_create_relative_file(directory_handle: int, name: str) -> int:
     name = _validated_relative_manifest_name(name)
-    create, _, close = _windows_file_api()
+    create, _, _, _, _ = _windows_file_api()
     encoded_name = name.encode("utf-16-le")
     if len(encoded_name) > 0xFFFE:
         raise GenerationError("manifest temporary name is too long")
     name_buffer = ctypes.create_unicode_buffer(name)
     unicode_name = _WindowsUnicodeString(
         len(encoded_name),
         len(encoded_name),
         ctypes.cast(name_buffer, wintypes.LPWSTR),
     )
     attributes = _WindowsObjectAttributes(
         ctypes.sizeof(_WindowsObjectAttributes),
         wintypes.HANDLE(directory_handle),
         ctypes.pointer(unicode_name),
         0x00000040,
         None,
         None,
     )
     status_block = _WindowsIOStatusBlock()
     handle = wintypes.HANDLE()
-    status = int(
-        create(
-            ctypes.byref(handle),
-            0x00000002 | 0x00000080 | 0x00010000 | 0x00100000,
-            ctypes.byref(attributes),
-            ctypes.byref(status_block),
-            None,
-            0x00000080,
-            0x00000001 | 0x00000002,
-            2,
-            0x00000020 | 0x00000040,
-            None,
-            0,
+    try:
+        status = int(
+            create(
+                ctypes.byref(handle),
+                0x00000002 | 0x00000080 | 0x00010000 | 0x00100000,
+                ctypes.byref(attributes),
+                ctypes.byref(status_block),
+                None,
+                0x00000080,
+                0,
+                2,
+                0x00000020 | 0x00000040,
+                None,
+                0,
+            )
         )
-    )
+    except (OSError, ValueError) as error:
+        raise GenerationError("handle-relative manifest temporary creation failed") from error
+    invalid_handle = ctypes.c_void_p(-1).value
     if (
         status != 0
         or int(status_block.Status) != 0
         or int(status_block.Information) != 2
         or not handle.value
+        or int(handle.value) == invalid_handle
     ):
-        if handle.value:
+        if handle.value and int(handle.value) != invalid_handle:
             try:
                 _windows_dispose_relative_file(int(handle.value))
             finally:
-                close(handle)
+                _windows_close_file_handle(int(handle.value))
         raise GenerationError(
             "handle-relative manifest temporary creation returned malformed status "
             f"0x{status & 0xFFFFFFFF:08x}/{int(status_block.Status) & 0xFFFFFFFF:08x}/"
             f"{int(status_block.Information)}"
         )
-    native_handle = int(handle.value)
-    try:
-        return msvcrt.open_osfhandle(native_handle, os.O_WRONLY | os.O_BINARY)
-    except BaseException:
+    return int(handle.value)
+
+
+def _windows_write_file(file_handle: int, raw: bytes) -> None:
+    if not isinstance(raw, bytes):
+        raise GenerationError("manifest temporary content must be bytes")
+    _, _, write, _, _ = _windows_file_api()
+    offset = 0
+    while offset < len(raw):
+        chunk = raw[offset : offset + 0xFFFFFFFF]
+        buffer = ctypes.create_string_buffer(chunk)
+        written = wintypes.DWORD()
         try:
-            _windows_dispose_relative_file(native_handle)
-        finally:
-            close(native_handle)
-        raise
+            succeeded = write(
+                wintypes.HANDLE(file_handle),
+                ctypes.byref(buffer),
+                len(chunk),
+                ctypes.byref(written),
+                None,
+            )
+        except (OSError, ValueError) as error:
+            raise GenerationError("handle-bound manifest temporary write failed") from error
+        if not succeeded:
+            error = ctypes.get_last_error()
+            raise GenerationError("handle-bound manifest temporary write failed") from OSError(
+                error, os.strerror(error)
+            )
+        count = int(written.value)
+        if count <= 0 or count > len(chunk):
+            raise GenerationError("handle-bound manifest temporary write returned malformed length")
+        offset += count
+
+
+def _windows_flush_file(file_handle: int) -> None:
+    _, _, _, flush, _ = _windows_file_api()
+    try:
+        succeeded = flush(wintypes.HANDLE(file_handle))
+    except (OSError, ValueError) as error:
+        raise GenerationError("handle-bound manifest temporary flush failed") from error
+    if not succeeded:
+        error = ctypes.get_last_error()
+        raise GenerationError("handle-bound manifest temporary flush failed") from OSError(
+            error, os.strerror(error)
+        )
+
+
+def _windows_close_file_handle(file_handle: int) -> None:
+    _, _, _, _, close = _windows_file_api()
+    try:
+        succeeded = close(wintypes.HANDLE(file_handle))
+    except (OSError, ValueError) as error:
+        raise GenerationError("manifest temporary handle close failed") from error
+    if not succeeded:
+        error = ctypes.get_last_error()
+        raise GenerationError("manifest temporary handle close failed") from OSError(
+            error, os.strerror(error)
+        )
 
 
 def _windows_rename_relative_file(
     file_handle: int, directory_handle: int, destination_name: str
 ) -> None:
     destination_name = _validated_relative_manifest_name(destination_name)
-    _, set_information, _ = _windows_file_api()
+    _, set_information, _, _, _ = _windows_file_api()
     encoded_name = destination_name.encode("utf-16-le")
     name_offset = _WindowsFileRenameInformation.FileName.offset
     buffer = ctypes.create_string_buffer(name_offset + len(encoded_name))
     information = ctypes.cast(
         buffer, ctypes.POINTER(_WindowsFileRenameInformation)
     ).contents
     information.ReplaceIfExists = 1
     information.RootDirectory = wintypes.HANDLE(directory_handle)
     information.FileNameLength = len(encoded_name)
     ctypes.memmove(ctypes.addressof(buffer) + name_offset, encoded_name, len(encoded_name))
     status_block = _WindowsIOStatusBlock()
-    status = int(
-        set_information(
-            wintypes.HANDLE(file_handle),
-            ctypes.byref(status_block),
-            ctypes.byref(buffer),
-            len(buffer),
-            10,
+    try:
+        status = int(
+            set_information(
+                wintypes.HANDLE(file_handle),
+                ctypes.byref(status_block),
+                ctypes.byref(buffer),
+                len(buffer),
+                10,
+            )
         )
-    )
+    except (OSError, ValueError) as error:
+        raise GenerationError("handle-relative manifest replacement failed") from error
     if status != 0 or int(status_block.Status) != 0:
         raise GenerationError(
             "handle-relative manifest replacement returned malformed status "
             f"0x{status & 0xFFFFFFFF:08x}/{int(status_block.Status) & 0xFFFFFFFF:08x}"
         )
 
 
-def _windows_dispose_relative_file(file_handle: int) -> None:
-    _, set_information, _ = _windows_file_api()
-    information = _WindowsFileDispositionInformation(1)
+def _windows_set_relative_disposition(file_handle: int, delete: bool) -> None:
+    _, set_information, _, _, _ = _windows_file_api()
+    information = _WindowsFileDispositionInformation(int(delete))
     status_block = _WindowsIOStatusBlock()
-    status = int(
-        set_information(
-            wintypes.HANDLE(file_handle),
-            ctypes.byref(status_block),
-            ctypes.byref(information),
-            ctypes.sizeof(information),
-            13,
+    try:
+        status = int(
+            set_information(
+                wintypes.HANDLE(file_handle),
+                ctypes.byref(status_block),
+                ctypes.byref(information),
+                ctypes.sizeof(information),
+                13,
+            )
         )
-    )
+    except (OSError, ValueError) as error:
+        raise GenerationError("handle-bound manifest disposition failed") from error
     if status != 0 or int(status_block.Status) != 0:
         raise GenerationError(
-            "handle-bound manifest temporary disposal returned malformed status "
+            "handle-bound manifest disposition returned malformed status "
             f"0x{status & 0xFFFFFFFF:08x}/{int(status_block.Status) & 0xFFFFFFFF:08x}"
         )
 
 
+def _windows_dispose_relative_file(file_handle: int) -> None:
+    _windows_set_relative_disposition(file_handle, True)
+
+
 class _BoundTemporary:
-    def __init__(self, name: str, descriptor: int | None) -> None:
+    def __init__(self, name: str, handle: int | None) -> None:
         self.name = name
-        self.descriptor = descriptor
+        self.handle = handle
+        self.renamed = False
 
 
 class _BoundManifestDirectory:
     def __init__(self, repository_root: Path, *, create_missing: bool) -> None:
         self.repository_root = repository_root
         self.create_missing = create_missing
         self.root: Path | None = None
         self.docs: Path | None = None
         self.architecture: Path | None = None
         self.destinations: dict[str, Path] = {}
@@ -2536,34 +2619,31 @@ class _BoundManifestDirectory:
 
     def stage(self, destination: Path, raw: bytes) -> _BoundTemporary:
         assert self.architecture is not None
         self.reverify()
         name = f".{destination.name}.{uuid.uuid4().hex}.tmp"
         if os.name == "nt":
             if not self._windows_handles:
                 raise GenerationError("Windows manifest directory handle is absent")
             architecture_handle = self._windows_handles[-1][1]
             try:
-                descriptor = _windows_create_relative_file(architecture_handle, name)
+                handle = _windows_create_relative_file(architecture_handle, name)
+            except GenerationError:
+                raise
             except OSError as error:
                 raise GenerationError("manifest temporary file could not be created") from error
-            temporary = _BoundTemporary(name, descriptor)
+            temporary = _BoundTemporary(name, handle)
             self._owned_temporary.append(temporary)
             try:
                 self.reverify()
-                offset = 0
-                while offset < len(raw):
-                    written = os.write(descriptor, raw[offset:])
-                    if written <= 0:
-                        raise OSError("manifest temporary write made no progress")
-                    offset += written
-                os.fsync(descriptor)
+                _windows_write_file(handle, raw)
+                _windows_flush_file(handle)
                 self.reverify()
                 return temporary
             except GenerationError:
                 raise
             except OSError as error:
                 raise GenerationError("manifest temporary file could not be staged") from error
         if self._architecture_descriptor is None:
             raise GenerationError("POSIX manifest directory descriptor is absent")
         flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
         try:
@@ -2587,84 +2667,113 @@ class _BoundManifestDirectory:
             raise GenerationError("manifest temporary file could not be staged") from error
         finally:
             os.close(descriptor)
         return temporary
 
     def replace(self, temporary: _BoundTemporary, destination: Path) -> None:
         if temporary not in self._owned_temporary:
             raise GenerationError("manifest temporary ownership is invalid")
         self.reverify()
         if os.name == "nt":
-            if temporary.descriptor is None or not self._windows_handles:
+            if temporary.handle is None or not self._windows_handles:
                 raise GenerationError("Windows manifest temporary handle is absent")
             architecture_handle = self._windows_handles[-1][1]
-            native_handle = msvcrt.get_osfhandle(temporary.descriptor)
             _windows_rename_relative_file(
-                native_handle, architecture_handle, destination.name
+                temporary.handle, architecture_handle, destination.name
             )
+            temporary.renamed = True
+            _windows_close_file_handle(temporary.handle)
+            temporary.handle = None
             self._owned_temporary.remove(temporary)
-            os.close(temporary.descriptor)
-            temporary.descriptor = None
             self.reverify()
             return
         if self._architecture_descriptor is None:
             raise GenerationError("POSIX manifest replacement arguments are invalid")
         os.replace(
             temporary.name,
             destination.name,
             src_dir_fd=self._architecture_descriptor,
             dst_dir_fd=self._architecture_descriptor,
         )
         self._owned_temporary.remove(temporary)
         self.reverify()
 
     def cleanup(self, temporary: _BoundTemporary) -> None:
         if temporary not in self._owned_temporary:
             return
         if os.name == "nt":
-            if temporary.descriptor is None:
+            if temporary.handle is None:
                 raise GenerationError("Windows manifest temporary handle is absent")
-            native_handle = msvcrt.get_osfhandle(temporary.descriptor)
+            failures: list[GenerationError] = []
+            disposition_succeeded = temporary.renamed
+            if not temporary.renamed:
+                for _ in range(2):
+                    try:
+                        _windows_dispose_relative_file(temporary.handle)
+                    except GenerationError as error:
+                        failures.append(error)
+                    else:
+                        disposition_succeeded = True
+                        break
             try:
-                _windows_dispose_relative_file(native_handle)
-            finally:
-                os.close(temporary.descriptor)
-                temporary.descriptor = None
-                self._owned_temporary.remove(temporary)
+                _windows_close_file_handle(temporary.handle)
+            except GenerationError as error:
+                failures.append(error)
+            else:
+                temporary.handle = None
+                if disposition_succeeded:
+                    self._owned_temporary.remove(temporary)
+            if failures:
+                raise GenerationError(
+                    "manifest temporary cleanup failed: "
+                    + "; ".join(str(error) for error in failures)
+                ) from failures[0]
             return
         if self._architecture_descriptor is None:
             raise GenerationError("POSIX manifest directory descriptor is absent")
         try:
             os.unlink(temporary.name, dir_fd=self._architecture_descriptor)
         except FileNotFoundError:
             pass
         self._owned_temporary.remove(temporary)
 
     def close(self) -> None:
-        cleanup_failure: GenerationError | None = None
+        failures: list[GenerationError] = []
         for temporary in tuple(self._owned_temporary):
             try:
                 self.cleanup(temporary)
             except GenerationError as error:
-                if cleanup_failure is None:
-                    cleanup_failure = error
-        for _, descriptor, _ in reversed(self._posix_descriptors):
+                failures.append(error)
+        for entry in tuple(reversed(self._posix_descriptors)):
+            _, descriptor, _ = entry
             try:
                 os.close(descriptor)
-            except OSError:
-                pass
-        self._posix_descriptors.clear()
-        for _, handle, _ in reversed(self._windows_handles):
-            _close_windows_directory(handle)
-        self._windows_handles.clear()
-        if cleanup_failure is not None:
-            raise cleanup_failure
+            except OSError as error:
+                failures.append(
+                    GenerationError("POSIX manifest directory descriptor close failed")
+                )
+                failures[-1].__cause__ = error
+            else:
+                self._posix_descriptors.remove(entry)
+        for entry in tuple(reversed(self._windows_handles)):
+            _, handle, _ = entry
+            try:
+                _close_windows_directory(handle)
+            except GenerationError as error:
+                failures.append(error)
+            else:
+                self._windows_handles.remove(entry)
+        if failures:
+            raise GenerationError(
+                "manifest transaction cleanup failed: "
+                + "; ".join(str(error) for error in failures)
+            ) from failures[0]
 
 
 def write_manifests(
     repository_root: Path,
     state: Mapping[str, object],
     *,
     approved_seed_sha256: str | None,
 ) -> None:
     approved = validate_approval_digest(
         approved_seed_sha256, str(state["entries_sha256"])
