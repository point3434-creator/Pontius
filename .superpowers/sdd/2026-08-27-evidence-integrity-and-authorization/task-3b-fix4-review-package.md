# Review package: 75caae4bc0e723f7f2bbe7d0fb596c4213ab53b7..89303d1e7bdda4f3aec74b131d8a8cc8d1afcc09

## Commits
89303d1 fix(evidence): make native cleanup retry-safe

## Files changed
 tests/test_evidence_manifest_generation.py | 541 ++++++++++++++++++++++++++++-
 tools/generate_evidence_manifests.py       | 446 ++++++++++++++++++------
 2 files changed, 883 insertions(+), 104 deletions(-)

## Diff
diff --git a/tests/test_evidence_manifest_generation.py b/tests/test_evidence_manifest_generation.py
index 7edd481..7bd0e4b 100644
--- a/tests/test_evidence_manifest_generation.py
+++ b/tests/test_evidence_manifest_generation.py
@@ -1173,23 +1173,25 @@ class Selected:
 
     @unittest.skipUnless(os.name == "nt", "Windows native exclusivity test")
     def test_windows_staged_temp_rejects_a_second_writer_while_owned(self) -> None:
         with tempfile.TemporaryDirectory(prefix="pontius-task3-exclusive-temp-") as directory:
             root = Path(directory).resolve()
             architecture = root / "docs" / "architecture"
             architecture.mkdir(parents=True)
             real_create_relative = GENERATOR._windows_create_relative_file
             rejected = False
 
-            def create_and_probe(directory_handle: int, name: str) -> int:
+            def create_and_probe(
+                directory_handle: int, name: str, **kwargs: object
+            ) -> int:
                 nonlocal rejected
-                owned = real_create_relative(directory_handle, name)
+                owned = real_create_relative(directory_handle, name, **kwargs)
                 create, _, close = GENERATOR._windows_directory_api()
                 probe = create(
                     str(architecture / name),
                     0x40000000,
                     0x00000001 | 0x00000002 | 0x00000004,
                     None,
                     3,
                     0x00000080,
                     None,
                 )
@@ -1270,20 +1272,21 @@ class Selected:
             ):
                 try:
                     with GENERATOR._BoundManifestDirectory(root, create_missing=False) as transaction:
                         destinations = tuple(transaction.destinations.values())
                         transaction.stage(destinations[0], b"first")
                         transaction.stage(destinations[1], b"second")
                         raise GENERATOR.GenerationError("trigger cleanup")
                 except BaseException as error:
                     failure = error
             self.assertIsInstance(failure, GENERATOR.GenerationError)
+            self.assertEqual(getattr(failure, "retained_owners", ()), ())
             self.assertGreaterEqual(attempts, 2)
             self.assertFalse(any(path.name.endswith(".tmp") for path in architecture.iterdir()))
 
     @unittest.skipUnless(os.name == "nt", "Windows native lifecycle test")
     def test_windows_directory_cleanup_attempts_every_held_handle(self) -> None:
         with tempfile.TemporaryDirectory(
             prefix="pontius-task3-directory-close-", ignore_cleanup_errors=True
         ) as directory:
             root = Path(directory).resolve()
             (root / "docs" / "architecture").mkdir(parents=True)
@@ -1432,20 +1435,554 @@ class Selected:
                             mock.Mock(),
                             close_function,
                         ),
                     ):
                         close(123)
                 except BaseException as error:
                     failure = error
                 self.assertIsInstance(failure, GENERATOR.GenerationError)
                 self.assertIsInstance(failure.__cause__, OSError)
 
+    @unittest.skipUnless(os.name == "nt", "Windows native API fault matrix")
+    def test_windows_file_api_fault_matrix_is_typed_one_variable_at_a_time(self) -> None:
+        symbols = (
+            ("ntdll", "NtCreateFile"),
+            ("ntdll", "NtSetInformationFile"),
+            ("kernel32", "WriteFile"),
+            ("kernel32", "FlushFileBuffers"),
+            ("kernel32", "CloseHandle"),
+        )
+        cases = (("ntdll_load", None, "ntdll"), ("kernel32_load", None, "kernel32")) + tuple(
+            (f"missing_{symbol}", symbol, dll_name) for dll_name, symbol in symbols
+        )
+        for label, missing_symbol, failing_load in cases:
+            with self.subTest(label=label):
+                ntdll = type("NativeDll", (), {})()
+                ntdll.NtCreateFile = mock.Mock()
+                ntdll.NtSetInformationFile = mock.Mock()
+                kernel32 = type("KernelDll", (), {})()
+                kernel32.WriteFile = mock.Mock()
+                kernel32.FlushFileBuffers = mock.Mock()
+                kernel32.CloseHandle = mock.Mock()
+                if missing_symbol is not None:
+                    delattr(ntdll if failing_load == "ntdll" else kernel32, missing_symbol)
+
+                def load_dll(name: str, **_kwargs: object) -> object:
+                    if missing_symbol is None and name == failing_load:
+                        raise OSError(f"injected {name} load failure")
+                    return ntdll if name == "ntdll" else kernel32
+
+                failure = None
+                with mock.patch.object(GENERATOR.ctypes, "WinDLL", side_effect=load_dll):
+                    try:
+                        GENERATOR._windows_file_api()
+                    except BaseException as error:
+                        failure = error
+                self.assertIsInstance(failure, GENERATOR.GenerationError)
+                self.assertIsInstance(failure.__cause__, (OSError, AttributeError))
+
+    @unittest.skipUnless(os.name == "nt", "Windows directory API fault matrix")
+    def test_windows_directory_api_fault_matrix_is_typed_one_variable_at_a_time(self) -> None:
+        for label, missing_symbol in (
+            ("dll_load", None),
+            ("missing_CreateFileW", "CreateFileW"),
+            ("missing_GetFileInformationByHandle", "GetFileInformationByHandle"),
+            ("missing_CloseHandle", "CloseHandle"),
+        ):
+            with self.subTest(label=label):
+                kernel32 = type("KernelDll", (), {})()
+                kernel32.CreateFileW = mock.Mock()
+                kernel32.GetFileInformationByHandle = mock.Mock()
+                kernel32.CloseHandle = mock.Mock()
+                if missing_symbol is not None:
+                    delattr(kernel32, missing_symbol)
+                loader = (
+                    mock.Mock(side_effect=OSError("injected directory DLL load failure"))
+                    if missing_symbol is None
+                    else mock.Mock(return_value=kernel32)
+                )
+                failure = None
+                with mock.patch.object(GENERATOR.ctypes, "WinDLL", loader):
+                    try:
+                        GENERATOR._windows_directory_api()
+                    except BaseException as error:
+                        failure = error
+                self.assertIsInstance(failure, GENERATOR.GenerationError)
+                self.assertIsInstance(failure.__cause__, (OSError, AttributeError))
+
+    @unittest.skipUnless(os.name == "nt", "Windows directory native fault matrix")
+    def test_windows_directory_native_calls_and_close_failures_are_typed(self) -> None:
+        for label, create in (
+            (
+                "create_exception",
+                mock.Mock(side_effect=RuntimeError("injected CreateFileW exception")),
+            ),
+            ("create_null", mock.Mock(return_value=0)),
+            (
+                "create_invalid",
+                mock.Mock(return_value=GENERATOR.ctypes.c_void_p(-1).value),
+            ),
+        ):
+            with self.subTest(label=label), mock.patch.object(
+                GENERATOR,
+                "_windows_directory_api",
+                return_value=(create, mock.Mock(), mock.Mock()),
+            ):
+                failure = None
+                try:
+                    GENERATOR._windows_open_directory(Path("C:/injected"))
+                except BaseException as error:
+                    failure = error
+                self.assertIsInstance(failure, GENERATOR.GenerationError)
+                self.assertIsInstance(failure.__cause__, (OSError, RuntimeError))
+
+        for label, information in (
+            (
+                "information_exception",
+                mock.Mock(
+                    side_effect=RuntimeError(
+                        "injected GetFileInformationByHandle exception"
+                    )
+                ),
+            ),
+            ("information_false", mock.Mock(return_value=0)),
+        ):
+            with self.subTest(label=label), mock.patch.object(
+                GENERATOR,
+                "_windows_directory_api",
+                return_value=(mock.Mock(), information, mock.Mock()),
+            ):
+                failure = None
+                try:
+                    GENERATOR._windows_directory_handle_identity(
+                        101, Path("C:/injected")
+                    )
+                except BaseException as error:
+                    failure = error
+                self.assertIsInstance(failure, GENERATOR.GenerationError)
+                self.assertIsInstance(failure.__cause__, (OSError, RuntimeError))
+
+        for label, close in (
+            ("false", mock.Mock(return_value=0)),
+            ("exception", mock.Mock(side_effect=RuntimeError("injected CloseHandle exception"))),
+        ):
+            with self.subTest(label=label), mock.patch.object(
+                GENERATOR,
+                "_windows_directory_api",
+                return_value=(mock.Mock(), mock.Mock(), close),
+            ):
+                failure = None
+                try:
+                    GENERATOR._close_windows_directory(101)
+                except BaseException as error:
+                    failure = error
+                self.assertIsInstance(failure, GENERATOR.GenerationError)
+                self.assertIsInstance(failure.__cause__, (OSError, RuntimeError))
+
+    @unittest.skipUnless(os.name == "nt", "Windows directory ownership state machine")
+    def test_windows_open_directory_is_owned_before_identity_validation(self) -> None:
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-directory-owner-") as directory:
+            root = Path(directory).resolve()
+            (root / "docs" / "architecture").mkdir(parents=True)
+            transaction = GENERATOR._BoundManifestDirectory(root, create_missing=False)
+            create = mock.Mock(return_value=101)
+            information_error = RuntimeError("injected directory identity failure")
+            information = mock.Mock(side_effect=information_error)
+            close = mock.Mock(return_value=0)
+
+            failure = None
+            with mock.patch.object(
+                GENERATOR,
+                "_windows_directory_api",
+                return_value=(create, information, close),
+            ):
+                try:
+                    transaction.__enter__()
+                except BaseException as error:
+                    failure = error
+
+            self.assertIsInstance(failure, GENERATOR.GenerationError)
+            self.assertEqual(close.call_count, 1)
+            self.assertEqual(
+                transaction._windows_handles,
+                [(root, 101, None)],
+            )
+            self.assertIn(transaction, getattr(failure, "retained_owners", ()))
+            self.assertIs(
+                getattr(failure, "failures", ())[0].__cause__,
+                information_error,
+            )
+
+            with mock.patch.object(
+                GENERATOR, "_close_windows_directory", return_value=None
+            ):
+                transaction.close()
+            self.assertEqual(transaction._windows_handles, [])
+
+    @unittest.skipUnless(os.name == "nt", "Windows create fault matrix")
+    def test_windows_create_fault_matrix_varies_one_result_at_a_time(self) -> None:
+        cases = (
+            ("return_status", -1, 0, 2, 101, None),
+            ("io_status", 0, -1, 2, 101, None),
+            ("information", 0, 0, 1, 101, None),
+            ("null_handle", 0, 0, 2, 0, None),
+            ("invalid_handle", 0, 0, 2, -1, None),
+            ("exception", 0, 0, 2, 101, RuntimeError("injected NtCreateFile exception")),
+        )
+        for label, returned, io_status, information, handle_value, raised in cases:
+            with self.subTest(label=label):
+                def create(
+                    handle: object,
+                    _access: object,
+                    _attributes: object,
+                    status: object,
+                    *_rest: object,
+                ) -> int:
+                    GENERATOR.ctypes.cast(
+                        handle, GENERATOR.ctypes.POINTER(GENERATOR.wintypes.HANDLE)
+                    ).contents.value = handle_value
+                    status_pointer = GENERATOR.ctypes.cast(
+                        status,
+                        GENERATOR.ctypes.POINTER(GENERATOR._WindowsIOStatusBlock),
+                    )
+                    status_pointer.contents.Status = io_status
+                    status_pointer.contents.Information = information
+                    if raised is not None:
+                        raise raised
+                    return returned
+
+                with mock.patch.object(
+                    GENERATOR,
+                    "_windows_file_api",
+                    return_value=(
+                        create,
+                        mock.Mock(),
+                        mock.Mock(),
+                        mock.Mock(),
+                        mock.Mock(return_value=1),
+                    ),
+                ), mock.patch.object(
+                    GENERATOR, "_windows_dispose_relative_file", return_value=None
+                ):
+                    failure = None
+                    try:
+                        GENERATOR._windows_create_relative_file(123, "candidate.tmp")
+                    except BaseException as error:
+                        failure = error
+                self.assertIsInstance(failure, GENERATOR.GenerationError)
+                if raised is not None:
+                    self.assertIs(failure.__cause__, raised)
+
+    @unittest.skipUnless(os.name == "nt", "Windows information fault matrix")
+    def test_windows_rename_and_disposition_status_channels_are_independent(self) -> None:
+        operations = (
+            (GENERATOR._windows_rename_relative_file, (101, 202, "manifest.toml")),
+            (GENERATOR._windows_dispose_relative_file, (101,)),
+        )
+        cases = (
+            ("return_status", -1, 0, None),
+            ("io_status", 0, -1, None),
+            ("exception", 0, 0, RuntimeError("injected NtSetInformationFile exception")),
+        )
+        for operation, arguments in operations:
+            for label, returned, io_status, raised in cases:
+                with self.subTest(operation=operation.__name__, label=label):
+                    def set_information(
+                        _handle: object, status: object, *_rest: object
+                    ) -> int:
+                        GENERATOR.ctypes.cast(
+                            status,
+                            GENERATOR.ctypes.POINTER(GENERATOR._WindowsIOStatusBlock),
+                        ).contents.Status = io_status
+                        if raised is not None:
+                            raise raised
+                        return returned
+
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
+                        failure = None
+                        try:
+                            operation(*arguments)
+                        except BaseException as error:
+                            failure = error
+                    self.assertIsInstance(failure, GENERATOR.GenerationError)
+                    if raised is not None:
+                        self.assertIs(failure.__cause__, raised)
+
+    @unittest.skipUnless(os.name == "nt", "Windows write fault matrix")
+    def test_windows_write_fault_matrix_and_partial_progress(self) -> None:
+        cases = (
+            ("false", 0, None),
+            ("exception", 1, RuntimeError("injected WriteFile exception")),
+            ("zero", 1, 0),
+            ("oversized", 1, 4),
+        )
+        for label, succeeded, count_or_error in cases:
+            with self.subTest(label=label):
+                def write(
+                    _handle: object,
+                    _buffer: object,
+                    requested: int,
+                    written: object,
+                    _overlapped: object,
+                ) -> int:
+                    if isinstance(count_or_error, BaseException):
+                        raise count_or_error
+                    count = requested + 1 if label == "oversized" else int(count_or_error or 0)
+                    GENERATOR.ctypes.cast(
+                        written, GENERATOR.ctypes.POINTER(GENERATOR.wintypes.DWORD)
+                    ).contents.value = count
+                    return succeeded
+
+                with mock.patch.object(
+                    GENERATOR,
+                    "_windows_file_api",
+                    return_value=(
+                        mock.Mock(),
+                        mock.Mock(),
+                        write,
+                        mock.Mock(),
+                        mock.Mock(),
+                    ),
+                ):
+                    failure = None
+                    try:
+                        GENERATOR._windows_write_file(101, b"abc")
+                    except BaseException as error:
+                        failure = error
+                self.assertIsInstance(failure, GENERATOR.GenerationError)
+                if isinstance(count_or_error, BaseException):
+                    self.assertIs(failure.__cause__, count_or_error)
+
+        requested_chunks = []
+        partial_counts = iter((2, 2, 1))
+
+        def partial_write(
+            _handle: object,
+            buffer: object,
+            requested: int,
+            written: object,
+            _overlapped: object,
+        ) -> int:
+            requested_chunks.append(GENERATOR.ctypes.string_at(buffer, requested))
+            GENERATOR.ctypes.cast(
+                written, GENERATOR.ctypes.POINTER(GENERATOR.wintypes.DWORD)
+            ).contents.value = next(partial_counts)
+            return 1
+
+        with mock.patch.object(
+            GENERATOR,
+            "_windows_file_api",
+            return_value=(
+                mock.Mock(),
+                mock.Mock(),
+                partial_write,
+                mock.Mock(),
+                mock.Mock(),
+            ),
+        ):
+            GENERATOR._windows_write_file(101, b"abcde")
+        self.assertEqual(requested_chunks, [b"abcde", b"cde", b"e"])
+
+    @unittest.skipUnless(os.name == "nt", "Windows flush and close fault matrix")
+    def test_windows_flush_and_file_close_faults_are_typed(self) -> None:
+        for operation_name, operation, index in (
+            ("flush", GENERATOR._windows_flush_file, 3),
+            ("close", GENERATOR._windows_close_file_handle, 4),
+        ):
+            for label, native in (
+                ("false", mock.Mock(return_value=0)),
+                (
+                    "exception",
+                    mock.Mock(side_effect=RuntimeError(f"injected {operation_name} exception")),
+                ),
+            ):
+                with self.subTest(operation=operation_name, label=label):
+                    api = [mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock()]
+                    api[index] = native
+                    with mock.patch.object(
+                        GENERATOR, "_windows_file_api", return_value=tuple(api)
+                    ):
+                        failure = None
+                        try:
+                            operation(101)
+                        except BaseException as error:
+                            failure = error
+                    self.assertIsInstance(failure, GENERATOR.GenerationError)
+                    self.assertIsInstance(failure.__cause__, (OSError, RuntimeError))
+
+    @unittest.skipUnless(os.name == "nt", "Windows cleanup state machine")
+    def test_windows_cleanup_never_closes_an_unarmed_candidate(self) -> None:
+        transaction = GENERATOR._BoundManifestDirectory(
+            Path("C:/injected-transaction"), create_missing=False
+        )
+        candidate = GENERATOR._BoundTemporary("candidate.tmp", 101)
+        transaction._owned_temporary.append(candidate)
+        disposition = mock.Mock(
+            side_effect=GENERATOR.GenerationError("injected disposition failure")
+        )
+        close = mock.Mock()
+        failure = None
+        with mock.patch.object(
+            GENERATOR, "_windows_dispose_relative_file", disposition
+        ), mock.patch.object(GENERATOR, "_windows_close_file_handle", close):
+            try:
+                transaction.close()
+            except BaseException as error:
+                failure = error
+
+        self.assertIsInstance(failure, GENERATOR.GenerationError)
+        self.assertEqual(disposition.call_count, 2)
+        self.assertEqual(close.call_count, 0)
+        self.assertEqual(getattr(candidate, "state", None), "open")
+        self.assertEqual(candidate.handle, 101)
+        self.assertIn(candidate, transaction._owned_temporary)
+        self.assertIn(transaction, getattr(failure, "retained_owners", ()))
+
+    @unittest.skipUnless(os.name == "nt", "Windows cleanup state machine")
+    def test_windows_cleanup_does_not_rearm_deletion_after_close_failure(self) -> None:
+        transaction = GENERATOR._BoundManifestDirectory(
+            Path("C:/injected-transaction"), create_missing=False
+        )
+        candidate = GENERATOR._BoundTemporary("candidate.tmp", 101)
+        transaction._owned_temporary.append(candidate)
+        disposition = mock.Mock(return_value=None)
+        close = mock.Mock(
+            side_effect=(GENERATOR.GenerationError("injected close failure"), None)
+        )
+        with mock.patch.object(
+            GENERATOR, "_windows_dispose_relative_file", disposition
+        ), mock.patch.object(GENERATOR, "_windows_close_file_handle", close):
+            with self.assertRaises(GENERATOR.GenerationError):
+                transaction.cleanup(candidate)
+            self.assertEqual(getattr(candidate, "state", None), "deletion_armed")
+            transaction.cleanup(candidate)
+
+        self.assertEqual(disposition.call_count, 1)
+        self.assertEqual(close.call_count, 2)
+        self.assertEqual(getattr(candidate, "state", None), "closed")
+        self.assertNotIn(candidate, transaction._owned_temporary)
+
+    @unittest.skipUnless(os.name == "nt", "Windows create ownership state machine")
+    def test_windows_malformed_create_is_registered_before_validation_cleanup(self) -> None:
+        events = []
+
+        def create(
+            handle: object,
+            _access: object,
+            _attributes: object,
+            status: object,
+            *_rest: object,
+        ) -> int:
+            GENERATOR.ctypes.cast(
+                handle, GENERATOR.ctypes.POINTER(GENERATOR.wintypes.HANDLE)
+            ).contents.value = 101
+            status_pointer = GENERATOR.ctypes.cast(
+                status, GENERATOR.ctypes.POINTER(GENERATOR._WindowsIOStatusBlock)
+            )
+            status_pointer.contents.Status = -1
+            status_pointer.contents.Information = 2
+            return 0
+
+        def set_information(
+            _handle: object, status: object, _buffer: object, _length: object, kind: int
+        ) -> int:
+            events.append(("set", kind))
+            GENERATOR.ctypes.cast(
+                status, GENERATOR.ctypes.POINTER(GENERATOR._WindowsIOStatusBlock)
+            ).contents.Status = 0
+            return 0
+
+        def close(_handle: object) -> int:
+            events.append(("close", 101))
+            return 1
+
+        with tempfile.TemporaryDirectory(prefix="pontius-task3-malformed-create-") as directory:
+            root = Path(directory).resolve()
+            (root / "docs" / "architecture").mkdir(parents=True)
+            transaction = GENERATOR._BoundManifestDirectory(root, create_missing=False)
+            transaction.__enter__()
+            destination = next(iter(transaction.destinations.values()))
+            stage_failure = None
+            owned = ()
+            with mock.patch.object(
+                GENERATOR,
+                "_windows_file_api",
+                return_value=(create, set_information, mock.Mock(), mock.Mock(), close),
+            ):
+                try:
+                    transaction.stage(destination, b"content")
+                except BaseException as error:
+                    stage_failure = error
+                owned = tuple(transaction._owned_temporary)
+                transaction.close()
+            self.assertIsInstance(stage_failure, GENERATOR.GenerationError)
+            self.assertEqual(len(owned), 1)
+            candidate = owned[0]
+            self.assertEqual(getattr(candidate, "state", None), "closed")
+            self.assertIsNone(candidate.handle)
+            self.assertEqual(events, [("set", 13), ("close", 101)])
+
+    @unittest.skipUnless(os.name == "nt", "Windows cleanup error aggregation")
+    def test_transaction_exit_preserves_body_and_every_cleanup_failure(self) -> None:
+        transaction = GENERATOR._BoundManifestDirectory(
+            Path("C:/injected-transaction"), create_missing=False
+        )
+        candidates = (
+            GENERATOR._BoundTemporary("first.tmp", 101),
+            GENERATOR._BoundTemporary("second.tmp", 202),
+        )
+        transaction._owned_temporary.extend(candidates)
+        body = GENERATOR.GenerationError("injected body failure")
+        disposition_calls = []
+
+        def fail_disposition(handle: int) -> None:
+            disposition_calls.append(handle)
+            raise GENERATOR.GenerationError(f"injected disposition failure {handle}")
+
+        close = mock.Mock()
+        failure = None
+        with mock.patch.object(
+            GENERATOR, "_windows_dispose_relative_file", side_effect=fail_disposition
+        ), mock.patch.object(GENERATOR, "_windows_close_file_handle", close):
+            try:
+                transaction.__exit__(GENERATOR.GenerationError, body, None)
+            except BaseException as error:
+                failure = error
+
+        self.assertIsInstance(failure, GENERATOR.GenerationError)
+        aggregate_failures = getattr(failure, "failures", ())
+        self.assertEqual(len(aggregate_failures), 5)
+        self.assertIs(aggregate_failures[0], body)
+        self.assertEqual(
+            [str(error) for error in aggregate_failures[1:]],
+            [
+                "injected disposition failure 101",
+                "injected disposition failure 101",
+                "injected disposition failure 202",
+                "injected disposition failure 202",
+            ],
+        )
+        self.assertEqual(disposition_calls, [101, 101, 202, 202])
+        self.assertEqual(close.call_count, 0)
+        self.assertEqual(tuple(transaction._owned_temporary), candidates)
+        self.assertIn(transaction, getattr(failure, "retained_owners", ()))
+
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
diff --git a/tools/generate_evidence_manifests.py b/tools/generate_evidence_manifests.py
index 357be26..a9abbb6 100644
--- a/tools/generate_evidence_manifests.py
+++ b/tools/generate_evidence_manifests.py
@@ -139,20 +139,70 @@ RETAINED_V7 = {
 }
 
 _HEX40 = re.compile(r"[0-9a-f]{40}\Z")
 _HEX64 = re.compile(r"[0-9a-f]{64}\Z")
 _REPARSE_ATTRIBUTE = 0x400
 
 
 class GenerationError(RuntimeError):
     """A fail-closed generator error."""
 
+    def __init__(
+        self,
+        message: str,
+        *,
+        failures: Sequence[BaseException] = (),
+        retained_owners: Sequence[object] = (),
+    ) -> None:
+        super().__init__(message)
+        self.failures = tuple(failures)
+        self.retained_owners = tuple(retained_owners)
+
+
+def _aggregate_generation_errors(
+    message: str,
+    failures: Sequence[BaseException],
+    *,
+    retained_owners: Sequence[object] = (),
+) -> GenerationError:
+    supplied_failures = tuple(failures)
+    if not supplied_failures:
+        raise ValueError("generation error aggregation requires at least one failure")
+    owners: list[object] = []
+    for owner in retained_owners:
+        if not any(existing is owner for existing in owners):
+            owners.append(owner)
+
+    ordered_failures: list[BaseException] = []
+
+    def append_failure(failure: BaseException) -> None:
+        if isinstance(failure, GenerationError):
+            for owner in failure.retained_owners:
+                if not any(existing is owner for existing in owners):
+                    owners.append(owner)
+            if failure.failures:
+                for nested in failure.failures:
+                    append_failure(nested)
+                return
+        ordered_failures.append(failure)
+
+    for failure in supplied_failures:
+        append_failure(failure)
+    detail = "; ".join(
+        f"{type(failure).__name__}: {failure}" for failure in ordered_failures
+    )
+    return GenerationError(
+        f"{message}: {detail}",
+        failures=tuple(ordered_failures),
+        retained_owners=owners,
+    )
+
 
 def canonical_semantic_bytes(value: object) -> bytes:
     return json.dumps(
         _normalize_semantic(value, "$"),
         allow_nan=False,
         ensure_ascii=True,
         separators=(",", ":"),
         sort_keys=True,
     ).encode("ascii")
 
@@ -2165,89 +2215,134 @@ if os.name == "nt":
         )
 
 
     class _WindowsFileDispositionInformation(ctypes.Structure):
         _fields_ = (("DeleteFile", ctypes.c_ubyte),)
 
 
 def _windows_directory_api() -> tuple[Any, Any, Any]:
     if os.name != "nt":
         raise GenerationError("Windows directory handles are unavailable")
-    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
-    create = kernel32.CreateFileW
-    create.argtypes = (
-        wintypes.LPCWSTR,
-        wintypes.DWORD,
-        wintypes.DWORD,
-        wintypes.LPVOID,
-        wintypes.DWORD,
-        wintypes.DWORD,
-        wintypes.HANDLE,
-    )
-    create.restype = wintypes.HANDLE
-    information = kernel32.GetFileInformationByHandle
-    information.argtypes = (
-        wintypes.HANDLE,
-        ctypes.POINTER(_WindowsDirectoryInformation),
-    )
-    information.restype = wintypes.BOOL
-    close = kernel32.CloseHandle
-    close.argtypes = (wintypes.HANDLE,)
-    close.restype = wintypes.BOOL
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
+        close = kernel32.CloseHandle
+        close.argtypes = (wintypes.HANDLE,)
+        close.restype = wintypes.BOOL
+    except Exception as error:
+        raise GenerationError("Windows directory handle APIs are unavailable") from error
     return create, information, close
 
 
-def _windows_open_directory(path: Path) -> int:
+def _windows_open_directory(
+    path: Path,
+    *,
+    owner: _BoundManifestDirectory | None = None,
+) -> int:
     create, _, close = _windows_directory_api()
-    handle = create(
-        str(path),
-        0x00000020 | 0x00000080 | 0x00100000,
-        0x00000001 | 0x00000002,
-        None,
-        3,
-        0x02000000 | 0x00200000,
-        None,
-    )
+    try:
+        handle = create(
+            str(path),
+            0x00000020 | 0x00000080 | 0x00100000,
+            0x00000001 | 0x00000002,
+            None,
+            3,
+            0x02000000 | 0x00200000,
+            None,
+        )
+    except Exception as error:
+        raise GenerationError(f"manifest directory handle could not be opened: {path}") from error
     invalid = ctypes.c_void_p(-1).value
-    if handle == invalid:
+    if not handle or handle == invalid:
         error = ctypes.get_last_error()
         raise GenerationError(f"manifest directory handle could not be opened: {path}") from OSError(
             error, os.strerror(error), str(path)
         )
+    numeric_handle = int(handle)
+    owned_entry: tuple[Path, int, tuple[int, int] | None] | None = None
+    if owner is not None:
+        owned_entry = (path, numeric_handle, None)
+        owner._windows_handles.append(owned_entry)
     try:
-        _windows_directory_handle_identity(handle, path)
-    except BaseException:
-        close(handle)
+        identity = _windows_directory_handle_identity(numeric_handle, path)
+    except BaseException as body_error:
+        if owner is not None:
+            raise
+        close_failure = None
+        try:
+            succeeded = close(numeric_handle)
+        except Exception as error:
+            close_failure = GenerationError("manifest directory handle close failed")
+            close_failure.__cause__ = error
+        else:
+            if not succeeded:
+                error = ctypes.get_last_error()
+                close_failure = GenerationError("manifest directory handle close failed")
+                close_failure.__cause__ = OSError(error, os.strerror(error))
+        if close_failure is not None:
+            aggregate = _aggregate_generation_errors(
+                "manifest directory inspection and close both failed",
+                (body_error, close_failure),
+            )
+            raise aggregate from body_error
         raise
-    return int(handle)
+    if owner is not None:
+        assert owned_entry is not None
+        for index, entry in enumerate(owner._windows_handles):
+            if entry is owned_entry:
+                owner._windows_handles[index] = (path, numeric_handle, identity)
+                break
+        else:
+            raise GenerationError("manifest directory handle ownership was lost")
+    return numeric_handle
 
 
 def _windows_directory_handle_identity(handle: int, path: Path) -> tuple[int, int]:
     _, information, _ = _windows_directory_api()
     value = _WindowsDirectoryInformation()
-    if not information(handle, ctypes.byref(value)):
+    try:
+        succeeded = information(handle, ctypes.byref(value))
+    except Exception as error:
+        raise GenerationError(f"manifest directory handle cannot be inspected: {path}") from error
+    if not succeeded:
         error = ctypes.get_last_error()
         raise GenerationError(f"manifest directory handle cannot be inspected: {path}") from OSError(
             error, os.strerror(error), str(path)
         )
     attributes = int(value.dwFileAttributes)
     if not attributes & 0x00000010 or attributes & _REPARSE_ATTRIBUTE:
         raise GenerationError(f"manifest directory handle is not a nonreparse directory: {path}")
     file_index = (int(value.nFileIndexHigh) << 32) | int(value.nFileIndexLow)
     return int(value.dwVolumeSerialNumber), file_index
 
 
 def _close_windows_directory(handle: int) -> None:
     _, _, close = _windows_directory_api()
     try:
         succeeded = close(handle)
-    except (OSError, ValueError) as error:
+    except Exception as error:
         raise GenerationError("manifest directory handle close failed") from error
     if not succeeded:
         error = ctypes.get_last_error()
         raise GenerationError("manifest directory handle close failed") from OSError(
             error, os.strerror(error)
         )
 
 
 def _windows_file_api() -> tuple[Any, Any, Any, Any, Any]:
     if os.name != "nt":
@@ -2287,37 +2382,47 @@ def _windows_file_api() -> tuple[Any, Any, Any, Any, Any]:
             wintypes.LPDWORD,
             wintypes.LPVOID,
         )
         write.restype = wintypes.BOOL
         flush = kernel32.FlushFileBuffers
         flush.argtypes = (wintypes.HANDLE,)
         flush.restype = wintypes.BOOL
         close = kernel32.CloseHandle
         close.argtypes = (wintypes.HANDLE,)
         close.restype = wintypes.BOOL
-    except (AttributeError, OSError) as error:
+    except Exception as error:
         raise GenerationError("Windows handle-relative file APIs are unavailable") from error
     return create, set_information, write, flush, close
 
 
 def _validated_relative_manifest_name(name: str) -> str:
     if (
         not isinstance(name, str)
         or not name
         or name in (".", "..")
         or any(character in name for character in ("/", "\\", ":", "\0"))
     ):
         raise GenerationError("manifest mutation name must be one relative path component")
     return name
 
 
-def _windows_create_relative_file(directory_handle: int, name: str) -> int:
+def _is_valid_windows_handle(value: object) -> bool:
+    invalid = ctypes.c_void_p(-1).value
+    return value is not None and bool(value) and int(value) != invalid
+
+
+def _windows_create_relative_file(
+    directory_handle: int,
+    name: str,
+    *,
+    owner: _BoundTemporary | None = None,
+) -> int:
     name = _validated_relative_manifest_name(name)
     create, _, _, _, _ = _windows_file_api()
     encoded_name = name.encode("utf-16-le")
     if len(encoded_name) > 0xFFFE:
         raise GenerationError("manifest temporary name is too long")
     name_buffer = ctypes.create_unicode_buffer(name)
     unicode_name = _WindowsUnicodeString(
         len(encoded_name),
         len(encoded_name),
         ctypes.cast(name_buffer, wintypes.LPWSTR),
@@ -2325,107 +2430,133 @@ def _windows_create_relative_file(directory_handle: int, name: str) -> int:
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
+    candidate = owner or _BoundTemporary(name, None, windows=True)
     try:
         status = int(
             create(
                 ctypes.byref(handle),
                 0x00000002 | 0x00000080 | 0x00010000 | 0x00100000,
                 ctypes.byref(attributes),
                 ctypes.byref(status_block),
                 None,
                 0x00000080,
                 0,
                 2,
                 0x00000020 | 0x00000040,
                 None,
                 0,
             )
         )
-    except (OSError, ValueError) as error:
-        raise GenerationError("handle-relative manifest temporary creation failed") from error
+    except Exception as error:
+        if _is_valid_windows_handle(handle.value):
+            candidate.claim_windows_handle(int(handle.value))
+        failure = GenerationError("handle-relative manifest temporary creation failed")
+        if owner is None:
+            try:
+                _cleanup_windows_temporary(candidate)
+            except GenerationError as cleanup_error:
+                aggregate = _aggregate_generation_errors(
+                    "manifest temporary creation and cleanup both failed",
+                    (failure, cleanup_error),
+                    retained_owners=(candidate,)
+                    if candidate.state != "closed"
+                    else (),
+                )
+                raise aggregate from error
+        raise failure from error
     invalid_handle = ctypes.c_void_p(-1).value
+    if handle.value and int(handle.value) != invalid_handle:
+        candidate.claim_windows_handle(int(handle.value))
     if (
         status != 0
         or int(status_block.Status) != 0
         or int(status_block.Information) != 2
         or not handle.value
         or int(handle.value) == invalid_handle
     ):
-        if handle.value and int(handle.value) != invalid_handle:
-            try:
-                _windows_dispose_relative_file(int(handle.value))
-            finally:
-                _windows_close_file_handle(int(handle.value))
-        raise GenerationError(
+        failure = GenerationError(
             "handle-relative manifest temporary creation returned malformed status "
             f"0x{status & 0xFFFFFFFF:08x}/{int(status_block.Status) & 0xFFFFFFFF:08x}/"
             f"{int(status_block.Information)}"
         )
+        if owner is None:
+            try:
+                _cleanup_windows_temporary(candidate)
+            except GenerationError as cleanup_error:
+                aggregate = _aggregate_generation_errors(
+                    "malformed manifest temporary creation and cleanup both failed",
+                    (failure, cleanup_error),
+                    retained_owners=(candidate,)
+                    if candidate.state != "closed"
+                    else (),
+                )
+                raise aggregate from failure
+        raise failure
     return int(handle.value)
 
 
 def _windows_write_file(file_handle: int, raw: bytes) -> None:
     if not isinstance(raw, bytes):
         raise GenerationError("manifest temporary content must be bytes")
     _, _, write, _, _ = _windows_file_api()
     offset = 0
     while offset < len(raw):
         chunk = raw[offset : offset + 0xFFFFFFFF]
         buffer = ctypes.create_string_buffer(chunk)
         written = wintypes.DWORD()
         try:
             succeeded = write(
                 wintypes.HANDLE(file_handle),
                 ctypes.byref(buffer),
                 len(chunk),
                 ctypes.byref(written),
                 None,
             )
-        except (OSError, ValueError) as error:
+        except Exception as error:
             raise GenerationError("handle-bound manifest temporary write failed") from error
         if not succeeded:
             error = ctypes.get_last_error()
             raise GenerationError("handle-bound manifest temporary write failed") from OSError(
                 error, os.strerror(error)
             )
         count = int(written.value)
         if count <= 0 or count > len(chunk):
             raise GenerationError("handle-bound manifest temporary write returned malformed length")
         offset += count
 
 
 def _windows_flush_file(file_handle: int) -> None:
     _, _, _, flush, _ = _windows_file_api()
     try:
         succeeded = flush(wintypes.HANDLE(file_handle))
-    except (OSError, ValueError) as error:
+    except Exception as error:
         raise GenerationError("handle-bound manifest temporary flush failed") from error
     if not succeeded:
         error = ctypes.get_last_error()
         raise GenerationError("handle-bound manifest temporary flush failed") from OSError(
             error, os.strerror(error)
         )
 
 
 def _windows_close_file_handle(file_handle: int) -> None:
     _, _, _, _, close = _windows_file_api()
     try:
         succeeded = close(wintypes.HANDLE(file_handle))
-    except (OSError, ValueError) as error:
+    except Exception as error:
         raise GenerationError("manifest temporary handle close failed") from error
     if not succeeded:
         error = ctypes.get_last_error()
         raise GenerationError("manifest temporary handle close failed") from OSError(
             error, os.strerror(error)
         )
 
 
 def _windows_rename_relative_file(
     file_handle: int, directory_handle: int, destination_name: str
@@ -2446,21 +2577,21 @@ def _windows_rename_relative_file(
     try:
         status = int(
             set_information(
                 wintypes.HANDLE(file_handle),
                 ctypes.byref(status_block),
                 ctypes.byref(buffer),
                 len(buffer),
                 10,
             )
         )
-    except (OSError, ValueError) as error:
+    except Exception as error:
         raise GenerationError("handle-relative manifest replacement failed") from error
     if status != 0 or int(status_block.Status) != 0:
         raise GenerationError(
             "handle-relative manifest replacement returned malformed status "
             f"0x{status & 0xFFFFFFFF:08x}/{int(status_block.Status) & 0xFFFFFFFF:08x}"
         )
 
 
 def _windows_set_relative_disposition(file_handle: int, delete: bool) -> None:
     _, set_information, _, _, _ = _windows_file_api()
@@ -2469,93 +2600,208 @@ def _windows_set_relative_disposition(file_handle: int, delete: bool) -> None:
     try:
         status = int(
             set_information(
                 wintypes.HANDLE(file_handle),
                 ctypes.byref(status_block),
                 ctypes.byref(information),
                 ctypes.sizeof(information),
                 13,
             )
         )
-    except (OSError, ValueError) as error:
+    except Exception as error:
         raise GenerationError("handle-bound manifest disposition failed") from error
     if status != 0 or int(status_block.Status) != 0:
         raise GenerationError(
             "handle-bound manifest disposition returned malformed status "
             f"0x{status & 0xFFFFFFFF:08x}/{int(status_block.Status) & 0xFFFFFFFF:08x}"
         )
 
 
 def _windows_dispose_relative_file(file_handle: int) -> None:
     _windows_set_relative_disposition(file_handle, True)
 
 
 class _BoundTemporary:
-    def __init__(self, name: str, handle: int | None) -> None:
+    def __init__(
+        self,
+        name: str,
+        handle: int | None,
+        *,
+        windows: bool | None = None,
+    ) -> None:
         self.name = name
         self.handle = handle
-        self.renamed = False
+        is_windows = handle is not None if windows is None else windows
+        if is_windows:
+            self.state = "open" if handle is not None else "unacquired"
+        else:
+            self.state = "path_owned"
+
+    @property
+    def renamed(self) -> bool:
+        return self.state == "renamed"
+
+    def claim_windows_handle(self, handle: int) -> None:
+        if self.state != "unacquired" or self.handle is not None:
+            raise GenerationError("manifest temporary handle ownership transition is invalid")
+        if not _is_valid_windows_handle(handle):
+            raise GenerationError("manifest temporary handle ownership is invalid")
+        self.handle = int(handle)
+        self.state = "open"
+
+    def mark_deletion_armed(self) -> None:
+        if self.state != "open" or self.handle is None:
+            raise GenerationError("manifest temporary deletion transition is invalid")
+        self.state = "deletion_armed"
+
+    def mark_renamed(self) -> None:
+        if self.state != "open" or self.handle is None:
+            raise GenerationError("manifest temporary rename transition is invalid")
+        self.state = "renamed"
+
+    def mark_closed(self) -> None:
+        if self.state == "unacquired" and self.handle is None:
+            self.state = "closed"
+            return
+        if self.state not in ("deletion_armed", "renamed") or self.handle is None:
+            raise GenerationError("manifest temporary close transition is invalid")
+        self.handle = None
+        self.state = "closed"
+
+
+def _cleanup_windows_temporary(temporary: _BoundTemporary) -> None:
+    if temporary.state == "closed":
+        return
+    if temporary.state == "unacquired":
+        temporary.mark_closed()
+        return
+    if temporary.state not in ("open", "deletion_armed", "renamed"):
+        raise GenerationError("Windows manifest temporary state is invalid")
+    if temporary.handle is None:
+        raise GenerationError("Windows manifest temporary handle is absent")
+
+    failures: list[GenerationError] = []
+    if temporary.state == "open":
+        for _ in range(2):
+            try:
+                _windows_dispose_relative_file(temporary.handle)
+            except GenerationError as error:
+                failures.append(error)
+            except Exception as error:
+                failure = GenerationError("handle-bound manifest disposition failed")
+                failure.__cause__ = error
+                failures.append(failure)
+            else:
+                temporary.mark_deletion_armed()
+                break
+        if temporary.state == "open":
+            aggregate = _aggregate_generation_errors(
+                "manifest temporary deletion could not be armed; handle remains open",
+                failures,
+                retained_owners=(temporary,),
+            )
+            raise aggregate from failures[0]
+
+    try:
+        _windows_close_file_handle(temporary.handle)
+    except GenerationError as error:
+        failures.append(error)
+    except Exception as error:
+        failure = GenerationError("manifest temporary handle close failed")
+        failure.__cause__ = error
+        failures.append(failure)
+    else:
+        temporary.mark_closed()
+
+    if failures:
+        retained = (temporary,) if temporary.state != "closed" else ()
+        aggregate = _aggregate_generation_errors(
+            "manifest temporary cleanup failed",
+            failures,
+            retained_owners=retained,
+        )
+        raise aggregate from failures[0]
 
 
 class _BoundManifestDirectory:
     def __init__(self, repository_root: Path, *, create_missing: bool) -> None:
         self.repository_root = repository_root
         self.create_missing = create_missing
         self.root: Path | None = None
         self.docs: Path | None = None
         self.architecture: Path | None = None
         self.destinations: dict[str, Path] = {}
         self._posix_descriptors: list[tuple[Path, int, tuple[int, int]]] = []
-        self._windows_handles: list[tuple[Path, int, tuple[int, int]]] = []
+        self._windows_handles: list[tuple[Path, int, tuple[int, int] | None]] = []
         self._architecture_descriptor: int | None = None
         self._owned_temporary: list[_BoundTemporary] = []
 
     def __enter__(self) -> "_BoundManifestDirectory":
         if not self.repository_root.is_absolute():
             raise GenerationError("repository root must be absolute")
         _validated_directory(self.repository_root, "repository root")
         self.root = self.repository_root.resolve(strict=True)
         self.docs = self.root / "docs"
         self.architecture = self.docs / "architecture"
         try:
             if os.name == "nt":
                 self._bind_windows()
             else:
                 self._bind_posix()
             self.destinations = _verified_destinations(self.root)
             self.reverify()
             return self
-        except BaseException:
-            self.close()
+        except BaseException as body_error:
+            try:
+                self.close()
+            except GenerationError as cleanup_error:
+                aggregate = _aggregate_generation_errors(
+                    "manifest transaction setup and cleanup both failed",
+                    (body_error, cleanup_error),
+                )
+                raise aggregate from body_error
+            if isinstance(body_error, Exception) and not isinstance(
+                body_error, GenerationError
+            ):
+                failure = GenerationError(
+                    "manifest transaction setup failed",
+                    failures=(body_error,),
+                )
+                raise failure from body_error
             raise
 
     def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
-        self.close()
+        try:
+            self.close()
+        except GenerationError as cleanup_error:
+            if not isinstance(exc, BaseException):
+                raise
+            aggregate = _aggregate_generation_errors(
+                "manifest transaction body and cleanup both failed",
+                (exc, cleanup_error),
+            )
+            raise aggregate from exc
 
     def _bind_windows(self) -> None:
         assert self.root is not None and self.docs is not None and self.architecture is not None
         for path in (self.root, self.docs):
-            handle = _windows_open_directory(path)
-            identity = _windows_directory_handle_identity(handle, path)
-            self._windows_handles.append((path, handle, identity))
+            _windows_open_directory(path, owner=self)
         if not os.path.lexists(self.architecture):
             if not self.create_missing:
                 raise GenerationError("manifest architecture directory is absent")
             try:
                 os.mkdir(self.architecture)
             except OSError as error:
                 raise GenerationError(
                     "manifest architecture directory could not be securely created"
                 ) from error
-        handle = _windows_open_directory(self.architecture)
-        identity = _windows_directory_handle_identity(handle, self.architecture)
-        self._windows_handles.append((self.architecture, handle, identity))
+        _windows_open_directory(self.architecture, owner=self)
 
     def _bind_posix(self) -> None:
         assert self.root is not None and self.docs is not None and self.architecture is not None
         required = ("O_DIRECTORY", "O_NOFOLLOW")
         dir_fd_functions = (os.open, os.mkdir, os.replace, os.unlink)
         if (
             any(not hasattr(os, name) for name in required)
             or any(function not in os.supports_dir_fd for function in dir_fd_functions)
         ):
             raise GenerationError("secure POSIX directory primitives are unavailable")
@@ -2586,20 +2832,24 @@ class _BoundManifestDirectory:
                     (int(architecture_info.st_dev), int(architecture_info.st_ino)),
                 )
             )
             self._architecture_descriptor = architecture_descriptor
         except OSError as error:
             raise GenerationError("manifest directory chain could not be securely bound") from error
 
     def reverify(self) -> None:
         if os.name == "nt":
             for path, handle, expected in self._windows_handles:
+                if expected is None:
+                    raise GenerationError(
+                        f"manifest directory handle identity is unverified: {path}"
+                    )
                 if _windows_directory_handle_identity(handle, path) != expected:
                     raise GenerationError(f"held manifest directory identity changed: {path}")
                 info = os.lstat(path)
                 if (
                     stat.S_ISLNK(info.st_mode)
                     or _is_reparse(info)
                     or not stat.S_ISDIR(info.st_mode)
                     or int(info.st_ino) != expected[1]
                 ):
                     raise GenerationError(f"manifest directory path no longer names its held handle: {path}")
@@ -2618,32 +2868,38 @@ class _BoundManifestDirectory:
                     raise GenerationError(f"manifest directory path no longer names its held handle: {path}")
 
     def stage(self, destination: Path, raw: bytes) -> _BoundTemporary:
         assert self.architecture is not None
         self.reverify()
         name = f".{destination.name}.{uuid.uuid4().hex}.tmp"
         if os.name == "nt":
             if not self._windows_handles:
                 raise GenerationError("Windows manifest directory handle is absent")
             architecture_handle = self._windows_handles[-1][1]
+            temporary = _BoundTemporary(name, None, windows=True)
+            self._owned_temporary.append(temporary)
             try:
-                handle = _windows_create_relative_file(architecture_handle, name)
+                handle = _windows_create_relative_file(
+                    architecture_handle,
+                    name,
+                    owner=temporary,
+                )
             except GenerationError:
                 raise
             except OSError as error:
                 raise GenerationError("manifest temporary file could not be created") from error
-            temporary = _BoundTemporary(name, handle)
-            self._owned_temporary.append(temporary)
+            if temporary.handle != handle or temporary.state != "open":
+                raise GenerationError("Windows manifest temporary ownership was not registered")
             try:
                 self.reverify()
-                _windows_write_file(handle, raw)
-                _windows_flush_file(handle)
+                _windows_write_file(temporary.handle, raw)
+                _windows_flush_file(temporary.handle)
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
@@ -2673,67 +2929,44 @@ class _BoundManifestDirectory:
         if temporary not in self._owned_temporary:
             raise GenerationError("manifest temporary ownership is invalid")
         self.reverify()
         if os.name == "nt":
             if temporary.handle is None or not self._windows_handles:
                 raise GenerationError("Windows manifest temporary handle is absent")
             architecture_handle = self._windows_handles[-1][1]
             _windows_rename_relative_file(
                 temporary.handle, architecture_handle, destination.name
             )
-            temporary.renamed = True
-            _windows_close_file_handle(temporary.handle)
-            temporary.handle = None
-            self._owned_temporary.remove(temporary)
+            temporary.mark_renamed()
+            self.cleanup(temporary)
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
-            if temporary.handle is None:
-                raise GenerationError("Windows manifest temporary handle is absent")
-            failures: list[GenerationError] = []
-            disposition_succeeded = temporary.renamed
-            if not temporary.renamed:
-                for _ in range(2):
-                    try:
-                        _windows_dispose_relative_file(temporary.handle)
-                    except GenerationError as error:
-                        failures.append(error)
-                    else:
-                        disposition_succeeded = True
-                        break
             try:
-                _windows_close_file_handle(temporary.handle)
-            except GenerationError as error:
-                failures.append(error)
-            else:
-                temporary.handle = None
-                if disposition_succeeded:
+                _cleanup_windows_temporary(temporary)
+            finally:
+                if temporary.state == "closed" and temporary in self._owned_temporary:
                     self._owned_temporary.remove(temporary)
-            if failures:
-                raise GenerationError(
-                    "manifest temporary cleanup failed: "
-                    + "; ".join(str(error) for error in failures)
-                ) from failures[0]
             return
         if self._architecture_descriptor is None:
             raise GenerationError("POSIX manifest directory descriptor is absent")
         try:
             os.unlink(temporary.name, dir_fd=self._architecture_descriptor)
         except FileNotFoundError:
             pass
         self._owned_temporary.remove(temporary)
 
     def close(self) -> None:
@@ -2756,24 +2989,33 @@ class _BoundManifestDirectory:
                 self._posix_descriptors.remove(entry)
         for entry in tuple(reversed(self._windows_handles)):
             _, handle, _ = entry
             try:
                 _close_windows_directory(handle)
             except GenerationError as error:
                 failures.append(error)
             else:
                 self._windows_handles.remove(entry)
         if failures:
-            raise GenerationError(
-                "manifest transaction cleanup failed: "
-                + "; ".join(str(error) for error in failures)
-            ) from failures[0]
+            retained = (
+                (self,)
+                if self._owned_temporary
+                or self._posix_descriptors
+                or self._windows_handles
+                else ()
+            )
+            aggregate = _aggregate_generation_errors(
+                "manifest transaction cleanup failed",
+                failures,
+                retained_owners=retained,
+            )
+            raise aggregate from failures[0]
 
 
 def write_manifests(
     repository_root: Path,
     state: Mapping[str, object],
     *,
     approved_seed_sha256: str | None,
 ) -> None:
     approved = validate_approval_digest(
         approved_seed_sha256, str(state["entries_sha256"])
