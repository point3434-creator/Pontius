from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pontius.cuda_dll_bootstrap import (
    CUDA_DLL_ENVIRONMENT_VARIABLE,
    CUDA_DLL_SOURCE_ENVIRONMENT_VARIABLE,
    REQUIRED_CUDA_DLL_NAMES,
    configure_cuda_dll_directory,
)


class CudaDllBootstrapTests(unittest.TestCase):
    def test_non_windows_does_not_mutate_environment(self) -> None:
        environment = {"PATH": "original"}
        resolved = configure_cuda_dll_directory(
            environment=environment,
            platform="linux",
            candidates=(),
        )
        self.assertIsNone(resolved)
        self.assertEqual(environment, {"PATH": "original"})

    def test_explicit_override_wins_without_eager_gpu_validation(self) -> None:
        environment = {
            CUDA_DLL_ENVIRONMENT_VARIABLE: "Z:/operator-selected-cuda",
            "PATH": "original",
        }
        resolved = configure_cuda_dll_directory(
            environment=environment,
            platform="win32",
            candidates=(("ignored", Path("Z:/ignored")),),
        )
        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved.source, "explicit_environment")
        self.assertEqual(
            environment[CUDA_DLL_ENVIRONMENT_VARIABLE],
            "Z:/operator-selected-cuda",
        )
        self.assertEqual(
            environment[CUDA_DLL_SOURCE_ENVIRONMENT_VARIABLE],
            "explicit_environment",
        )
        self.assertEqual(environment["PATH"], "original")

    def test_first_complete_pinned_bundle_is_configured_process_locally(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            incomplete = root / "incomplete"
            complete = root / "complete" / "cu13" / "bin" / "x86_64"
            incomplete.mkdir()
            complete.mkdir(parents=True)
            for name in REQUIRED_CUDA_DLL_NAMES:
                (complete / name).touch()
            environment = {"PATH": "existing"}
            resolved = configure_cuda_dll_directory(
                environment=environment,
                platform="win32",
                candidates=(
                    ("incomplete", incomplete),
                    ("test_environment", complete),
                ),
            )
            self.assertIsNotNone(resolved)
            assert resolved is not None
            self.assertEqual(resolved.directory, complete.resolve())
            self.assertEqual(resolved.source, "test_environment")
            self.assertEqual(
                environment[CUDA_DLL_ENVIRONMENT_VARIABLE],
                str(complete.resolve()),
            )
            self.assertEqual(
                environment[CUDA_DLL_SOURCE_ENVIRONMENT_VARIABLE],
                "test_environment",
            )
            self.assertEqual(environment["CUDA_PATH"], str(complete.parents[1]))
            self.assertEqual(environment["PATH"].split(";")[0], str(complete.resolve()))
            repeated = configure_cuda_dll_directory(
                environment=environment,
                platform="win32",
                candidates=(("unused", incomplete),),
            )
            self.assertIsNotNone(repeated)
            assert repeated is not None
            self.assertEqual(repeated.source, "test_environment")
            self.assertEqual(
                environment["PATH"].split(";").count(str(complete.resolve())),
                1,
            )

    def test_incomplete_candidates_leave_environment_unset(self) -> None:
        with TemporaryDirectory() as temporary:
            candidate = Path(temporary)
            environment: dict[str, str] = {}
            resolved = configure_cuda_dll_directory(
                environment=environment,
                platform="win32",
                candidates=(("incomplete", candidate),),
            )
            self.assertIsNone(resolved)
            self.assertNotIn(CUDA_DLL_ENVIRONMENT_VARIABLE, environment)


if __name__ == "__main__":
    unittest.main()
