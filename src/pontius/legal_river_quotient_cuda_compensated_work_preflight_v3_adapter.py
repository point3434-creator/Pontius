"""Exact-type evidence adapter for the ADR-0401 work-preflight recovery.

The scientific work-preflight source is hash-bound and remains read-only.  A
fresh probe or campaign child may install :func:`plain_evidence_v3` around one
scientific call, then must restore the exact original normalizer in ``finally``.
No generic Python-object serializer is provided here.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import fields, is_dataclass
from fractions import Fraction
from hashlib import sha256
import math
from pathlib import Path
import sys
import threading
from typing import Any, Callable, Iterator, Mapping, Sequence

import numpy as np

from . import legal_river_quotient_cuda_compensated_work_preflight as _source
from .legal_river_quotient_cuda_consumer import CudaRuntimeIdentity


_ROOT = Path(__file__).parents[2]
SCIENTIFIC_SOURCE_RELATIVE_PATH = (
    "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py"
)
SCIENTIFIC_SOURCE_SHA256 = (
    "652a4a37cd097a92829364f1ec6976a6f31a4092ab9fc3e0f97a992e2565c4aa"
)
APPROVED_RUNTIME_FIELDS = (
    "device_name",
    "compute_capability",
    "device_total_bytes",
    "cuda_driver_version",
    "cuda_runtime_version",
    "cupy_version",
)
FORCED_PROBE_EXCEPTION = "forced_serializer_probe_compiler_failure"
_ORIGINAL_SCIENTIFIC_PLAIN = _source._plain


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"work-preflight v3 adapter path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def verify_scientific_source_and_plain() -> None:
    """Bind the immutable source bytes and exact original function identity."""

    if canonical_lf_sha256(_ROOT / SCIENTIFIC_SOURCE_RELATIVE_PATH) != (
        SCIENTIFIC_SOURCE_SHA256
    ):
        raise RuntimeError("work-preflight v3 scientific source differs")
    if _source._plain is not _ORIGINAL_SCIENTIFIC_PLAIN:
        raise RuntimeError("work-preflight v3 scientific normalizer identity differs")
    if (
        _ORIGINAL_SCIENTIFIC_PLAIN.__module__ != _source.__name__
        or _ORIGINAL_SCIENTIFIC_PLAIN.__name__ != "_plain"
    ):
        raise RuntimeError("work-preflight v3 original normalizer provenance differs")


def plain_evidence_v3(value: Any) -> Any:
    """Normalize the legacy JSON domain plus one exact approved dataclass."""

    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("work-preflight evidence contains a nonfinite float")
        return value.hex()
    if isinstance(value, Fraction):
        return [value.numerator, value.denominator]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value).hex()
    if is_dataclass(value):
        if type(value) is not CudaRuntimeIdentity:
            raise TypeError(
                f"unsupported work-preflight evidence type: {type(value).__name__}"
            )
        declared = fields(value)
        if tuple(field.name for field in declared) != APPROVED_RUNTIME_FIELDS:
            raise TypeError("approved runtime identity field inventory differs")
        return {
            field.name: plain_evidence_v3(getattr(value, field.name))
            for field in declared
        }
    if isinstance(value, Mapping):
        return {str(key): plain_evidence_v3(item) for key, item in value.items()}
    if isinstance(value, tuple) and hasattr(type(value), "_fields"):
        raise TypeError(f"unsupported work-preflight evidence type: {type(value).__name__}")
    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return [plain_evidence_v3(item) for item in value]
    raise TypeError(f"unsupported work-preflight evidence type: {type(value).__name__}")


@contextmanager
def installed_scientific_plain() -> Iterator[None]:
    """Install the adapter process-locally around exactly one source call."""

    verify_scientific_source_and_plain()
    if threading.active_count() != 1:
        raise RuntimeError("work-preflight v3 adapter process has another live thread")
    _source._plain = plain_evidence_v3
    installed_identity: object = plain_evidence_v3
    try:
        yield
    finally:
        installed_identity = _source._plain
        _source._plain = _ORIGINAL_SCIENTIFIC_PLAIN
        if installed_identity is not plain_evidence_v3:
            raise RuntimeError("work-preflight v3 adapter identity changed during call")
        if _source._plain is not _ORIGINAL_SCIENTIFIC_PLAIN:
            raise RuntimeError("work-preflight v3 scientific normalizer did not restore")


def _cupy_loaded() -> bool:
    return any(name == "cupy" or name.startswith("cupy.") for name in sys.modules)


def run_forced_serializer_probe(
    emit: Callable[[str, Mapping[str, object]], None] | None = None,
) -> dict[str, object]:
    """Exercise the real scientific failure reporter without CUDA or a compiler."""

    if _cupy_loaded():
        raise RuntimeError("work-preflight v3 serializer probe inherited CuPy")
    verify_scientific_source_and_plain()
    if threading.active_count() != 1:
        raise RuntimeError("work-preflight v3 serializer probe has another live thread")

    runtime = CudaRuntimeIdentity(
        device_name="serializer-probe-device",
        compute_capability="00",
        device_total_bytes=0,
        cuda_driver_version=0,
        cuda_runtime_version=0,
        cupy_version="serializer-probe-no-cupy",
    )
    opaque_cupy = object()
    originals = {
        "cupy_loader": _source._cupy_module,
        "runtime_identity": _source._paired._runtime_identity,
        "runtime_verifier": _source._paired._verify_runtime,
        "kernel_compiler": _source._kernels,
    }
    original_counter = _source._BOUNDED_EXECUTION_CALLS
    if original_counter != 0:
        raise RuntimeError("work-preflight v3 serializer probe source counter is not zero")
    compiler_entry_calls = 0
    captured: list[tuple[str, Mapping[str, object]]] = []

    def no_cuda_loader() -> object:
        return opaque_cupy

    def probe_runtime_identity(cp: object) -> CudaRuntimeIdentity:
        if cp is not opaque_cupy:
            raise RuntimeError("work-preflight v3 probe runtime received wrong sentinel")
        return runtime

    def probe_runtime_verifier(
        observed: CudaRuntimeIdentity,
        config: Mapping[str, object],
    ) -> None:
        if observed is not runtime or not isinstance(config, Mapping):
            raise RuntimeError("work-preflight v3 probe runtime verifier seam differs")

    def forced_kernel_compiler(cp: object) -> Mapping[str, object]:
        nonlocal compiler_entry_calls
        compiler_entry_calls += 1
        if cp is not opaque_cupy:
            raise RuntimeError("work-preflight v3 probe compiler received wrong sentinel")
        raise RuntimeError(FORCED_PROBE_EXCEPTION)

    def capture(kind: str, payload: Mapping[str, object]) -> None:
        captured.append((kind, dict(payload)))

    terminal: Mapping[str, object] | None = None
    try:
        _source._cupy_module = no_cuda_loader
        _source._paired._runtime_identity = probe_runtime_identity
        _source._paired._verify_runtime = probe_runtime_verifier
        _source._kernels = forced_kernel_compiler
        with installed_scientific_plain():
            terminal = _source.run_calibration_preflight(capture)
    finally:
        _source._cupy_module = originals["cupy_loader"]  # type: ignore[assignment]
        _source._paired._runtime_identity = originals["runtime_identity"]  # type: ignore[assignment]
        _source._paired._verify_runtime = originals["runtime_verifier"]  # type: ignore[assignment]
        _source._kernels = originals["kernel_compiler"]  # type: ignore[assignment]
        _source._BOUNDED_EXECUTION_CALLS = original_counter

    restoration = {
        "scientific_plain": _source._plain is _ORIGINAL_SCIENTIFIC_PLAIN,
        "cupy_loader": _source._cupy_module is originals["cupy_loader"],
        "runtime_identity": (
            _source._paired._runtime_identity is originals["runtime_identity"]
        ),
        "runtime_verifier": (
            _source._paired._verify_runtime is originals["runtime_verifier"]
        ),
        "kernel_compiler": _source._kernels is originals["kernel_compiler"],
        "bounded_call_counter": _source._BOUNDED_EXECUTION_CALLS == original_counter,
    }
    if not all(restoration.values()):
        raise RuntimeError("work-preflight v3 serializer probe restoration failed")
    if _cupy_loaded():
        raise RuntimeError("work-preflight v3 serializer probe imported CuPy")
    if compiler_entry_calls != 1:
        raise RuntimeError("work-preflight v3 serializer probe compiler-call count differs")
    if len(captured) != 1 or captured[0][0] != "laboratory":
        raise RuntimeError("work-preflight v3 serializer probe event sequence differs")
    event = dict(captured[0][1])
    expected_runtime = plain_evidence_v3(runtime)
    if (
        event.get("schema_version")
        != "legal-river-work-preflight-laboratory-v1"
        or event.get("kind") != "compiler_resource_failure"
        or event.get("runtime") != expected_runtime
        or event.get("stage") != "kernel_compile_and_resource_inspection"
        or event.get("reason") != f"RuntimeError: {FORCED_PROBE_EXCEPTION}"
        or event.get("correction_config_sha256") != _source.CORRECTION_CONFIG_SHA256
    ):
        raise RuntimeError("work-preflight v3 serializer probe event differs")
    if not isinstance(terminal, Mapping) or terminal != {
        "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
        "terminal": "compiler_or_primitive_rejection",
        "failed_population": None,
        "passed": False,
        "projection": None,
    }:
        raise RuntimeError("work-preflight v3 serializer probe terminal differs")

    if emit is not None:
        emit("laboratory", event)
    return {
        "schema_version": "legal-river-work-preflight-serializer-probe-v3",
        "runtime": expected_runtime,
        "scientific_event": event,
        "scientific_terminal": dict(terminal),
        "forced_exception_reason": f"RuntimeError: {FORCED_PROBE_EXCEPTION}",
        "compiler_entry_calls": compiler_entry_calls,
        "cupy_loaded": False,
        "restoration": restoration,
        "passed": True,
    }


def run_adapted_calibration_preflight(
    emit: Callable[[str, Mapping[str, object]], None] | None = None,
) -> dict[str, object]:
    """Call immutable science once with only the exact serializer substituted."""

    verify_scientific_source_and_plain()
    with installed_scientific_plain():
        return _source.run_calibration_preflight(emit)


__all__ = [
    "APPROVED_RUNTIME_FIELDS",
    "FORCED_PROBE_EXCEPTION",
    "SCIENTIFIC_SOURCE_SHA256",
    "installed_scientific_plain",
    "plain_evidence_v3",
    "run_adapted_calibration_preflight",
    "run_forced_serializer_probe",
    "verify_scientific_source_and_plain",
]
