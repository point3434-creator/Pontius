"""Deterministic Windows discovery for the pinned packaged CUDA runtime."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import site
import sys
from typing import MutableMapping, Sequence


CUDA_DLL_ENVIRONMENT_VARIABLE = "PONTIUS_CUDA_DLL_DIRECTORY"
CUDA_DLL_SOURCE_ENVIRONMENT_VARIABLE = "PONTIUS_CUDA_DLL_SOURCE"
PACKAGED_CUDA_RELATIVE_DIRECTORY = Path("nvidia/cu13/bin/x86_64")
REQUIRED_CUDA_DLL_NAMES = (
    "cudart64_13.dll",
    "nvJitLink_130_0.dll",
    "nvrtc-builtins64_133.dll",
    "nvrtc64_130_0.dll",
    "cusparse64_12.dll",
)


@dataclass(frozen=True, slots=True)
class CudaDllResolution:
    directory: Path
    source: str


def _default_candidates() -> tuple[tuple[str, Path], ...]:
    candidates: list[tuple[str, Path]] = [
        (
            "active_python_environment",
            Path(sys.prefix) / "Lib/site-packages" / PACKAGED_CUDA_RELATIVE_DIRECTORY,
        )
    ]
    try:
        site_packages = tuple(site.getsitepackages())
    except AttributeError:
        site_packages = ()
    candidates.extend(
        (
            "active_python_site_packages",
            Path(directory) / PACKAGED_CUDA_RELATIVE_DIRECTORY,
        )
        for directory in site_packages
    )
    candidates.append(
        (
            "repository_local_environment",
            Path(__file__).parents[2]
            / ".venv/Lib/site-packages"
            / PACKAGED_CUDA_RELATIVE_DIRECTORY,
        )
    )
    unique = []
    seen: set[str] = set()
    for source, candidate in candidates:
        identity = os.path.normcase(str(candidate.resolve()))
        if identity in seen:
            continue
        seen.add(identity)
        unique.append((source, candidate))
    return tuple(unique)


def _complete_cuda_directory(directory: Path) -> bool:
    return directory.is_dir() and all(
        (directory / name).is_file() for name in REQUIRED_CUDA_DLL_NAMES
    )


def configure_cuda_dll_directory(
    *,
    environment: MutableMapping[str, str] | None = None,
    platform: str | None = None,
    candidates: Sequence[tuple[str, Path]] | None = None,
) -> CudaDllResolution | None:
    """Set the process-local CUDA DLL path when a complete pinned bundle exists.

    An explicit environment value always wins and is validated later by the
    GPU loader. Automatic discovery is deliberately limited to the active or
    repository-local Python environment; arbitrary system CUDA installations
    are not silently selected.
    """

    environ = os.environ if environment is None else environment
    active_platform = sys.platform if platform is None else platform
    if not active_platform.startswith("win"):
        return None
    supplied = environ.get(CUDA_DLL_ENVIRONMENT_VARIABLE)
    if supplied:
        source = environ.setdefault(
            CUDA_DLL_SOURCE_ENVIRONMENT_VARIABLE,
            "explicit_environment",
        )
        return CudaDllResolution(Path(supplied).resolve(), source)

    search = _default_candidates() if candidates is None else tuple(candidates)
    for source, candidate in search:
        directory = candidate.resolve()
        if not _complete_cuda_directory(directory):
            continue
        value = str(directory)
        environ[CUDA_DLL_ENVIRONMENT_VARIABLE] = value
        environ[CUDA_DLL_SOURCE_ENVIRONMENT_VARIABLE] = source
        cuda_root = directory.parents[1]
        environ.setdefault("CUDA_PATH", str(cuda_root))
        path_separator = ";" if active_platform.startswith("win") else os.pathsep
        path_rows = tuple(
            row for row in environ.get("PATH", "").split(path_separator) if row
        )
        normalized = {os.path.normcase(str(Path(row))) for row in path_rows}
        if os.path.normcase(value) not in normalized:
            environ["PATH"] = path_separator.join((value, *path_rows))
        return CudaDllResolution(directory, source)
    return None
