"""Optional CuPy execution of the frozen CSR incidence operators.

The CPU topology remains authoritative.  This module uploads its two SciPy CSR
maps and exposes a charged host->GPU, ``Q @ (A @ features)``, GPU->host
transform.  CuPy is imported lazily so neither the core laboratory nor the CPU
sparse screen acquires a CUDA dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
import os
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np

from .sparse_incidence_open_mode import (
    SparseBidirectionalIncidence,
    SparseIncidenceDirection,
)

_WINDOWS_DLL_HANDLE: object | None = None


@dataclass(frozen=True, slots=True)
class CuPyTransformWork:
    host_to_device_ms: float
    kernel_ms: float
    device_to_host_ms: float
    wall_ms: float
    pool_used_bytes: int
    pool_total_bytes: int


@dataclass(frozen=True, slots=True)
class CuPySparseIncidenceDirection:
    cpu: SparseIncidenceDirection
    source_matrix: Any
    query_matrix: Any
    upload_ms: float
    numeric_bytes: int

    @classmethod
    def compile(
        cls,
        cpu: SparseIncidenceDirection,
    ) -> CuPySparseIncidenceDirection:
        cp, cupy_sparse = _cupy_modules()
        started = time.perf_counter()
        source = cupy_sparse.csr_matrix(cpu.source_matrix)
        query = cupy_sparse.csr_matrix(cpu.query_matrix)
        cp.cuda.runtime.deviceSynchronize()
        return cls(
            cpu=cpu,
            source_matrix=source,
            query_matrix=query,
            upload_ms=(time.perf_counter() - started) * 1000.0,
            numeric_bytes=cpu.numeric_bytes,
        )

    def transform(self, features: np.ndarray) -> tuple[np.ndarray, CuPyTransformWork]:
        if (
            features.ndim != 2
            or features.shape[0] != self.cpu.source_records
            or features.dtype != np.float64
            or not features.flags.c_contiguous
        ):
            raise ValueError("CuPy incidence features differ from CPU source records")
        cp, _ = _cupy_modules()
        wall_started = time.perf_counter()
        started = time.perf_counter()
        device_features = cp.asarray(features)
        cp.cuda.runtime.deviceSynchronize()
        host_to_device_ms = (time.perf_counter() - started) * 1000.0

        begin = cp.cuda.Event()
        end = cp.cuda.Event()
        begin.record()
        incidence = self.source_matrix @ device_features
        device_result = self.query_matrix @ incidence
        end.record()
        end.synchronize()
        kernel_ms = float(cp.cuda.get_elapsed_time(begin, end))

        started = time.perf_counter()
        result = cp.asnumpy(device_result)
        cp.cuda.runtime.deviceSynchronize()
        device_to_host_ms = (time.perf_counter() - started) * 1000.0
        pool = cp.get_default_memory_pool()
        work = CuPyTransformWork(
            host_to_device_ms=host_to_device_ms,
            kernel_ms=kernel_ms,
            device_to_host_ms=device_to_host_ms,
            wall_ms=(time.perf_counter() - wall_started) * 1000.0,
            pool_used_bytes=int(pool.used_bytes()),
            pool_total_bytes=int(pool.total_bytes()),
        )
        del device_features, incidence, device_result
        return np.ascontiguousarray(result, dtype=np.float64), work


@dataclass(frozen=True, slots=True)
class CuPyBidirectionalIncidence:
    cpu: SparseBidirectionalIncidence
    right_to_left: CuPySparseIncidenceDirection
    left_to_right: CuPySparseIncidenceDirection
    cupy_version: str
    cuda_runtime_version: int
    cuda_driver_version: int
    compute_capability: str

    @classmethod
    def compile(
        cls,
        cpu: SparseBidirectionalIncidence,
    ) -> CuPyBidirectionalIncidence:
        cp, _ = _cupy_modules()
        return cls(
            cpu=cpu,
            right_to_left=CuPySparseIncidenceDirection.compile(cpu.right_to_left),
            left_to_right=CuPySparseIncidenceDirection.compile(cpu.left_to_right),
            cupy_version=str(cp.__version__),
            cuda_runtime_version=int(cp.cuda.runtime.runtimeGetVersion()),
            cuda_driver_version=int(cp.cuda.runtime.driverGetVersion()),
            compute_capability=str(cp.cuda.Device(0).compute_capability),
        )

    @property
    def upload_ms(self) -> float:
        return self.right_to_left.upload_ms + self.left_to_right.upload_ms

    @property
    def numeric_bytes(self) -> int:
        return self.right_to_left.numeric_bytes + self.left_to_right.numeric_bytes


def release_cupy_memory_pool() -> None:
    """Release cached optional-screen device blocks between large cases."""

    cp, _ = _cupy_modules()
    cp.get_default_memory_pool().free_all_blocks()
    cp.get_default_pinned_memory_pool().free_all_blocks()


def _cupy_modules() -> tuple[Any, Any]:
    _prepare_optional_windows_cuda()
    try:
        import cupy as cp
        import cupyx.scipy.sparse as cupy_sparse
    except ImportError as error:
        raise RuntimeError("the optional GPU incidence screen requires CuPy") from error
    return cp, cupy_sparse


def _prepare_optional_windows_cuda() -> None:
    """Load packaged CUDA DLLs when a temporary Windows screen requests it."""

    global _WINDOWS_DLL_HANDLE
    if not sys.platform.startswith("win") or _WINDOWS_DLL_HANDLE is not None:
        return
    supplied = os.environ.get("PONTIUS_CUDA_DLL_DIRECTORY")
    if not supplied:
        return
    directory = Path(supplied).resolve()
    if not directory.is_dir():
        raise RuntimeError("PONTIUS_CUDA_DLL_DIRECTORY is not a directory")
    root = directory.parents[1]
    os.environ.setdefault("CUDA_PATH", str(root))
    _WINDOWS_DLL_HANDLE = os.add_dll_directory(str(directory))
    for name in (
        "cudart64_13.dll",
        "nvJitLink_130_0.dll",
        "nvrtc-builtins64_133.dll",
        "nvrtc64_130_0.dll",
        "cusparse64_12.dll",
    ):
        path = directory / name
        if path.is_file():
            ctypes.WinDLL(str(path))
