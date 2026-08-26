"""Composite ADR-0413/ADR-0414 repaired executed-cubin adapter.

The scientific work-preflight source is immutable. In one fresh child this
module substitutes exactly three process-local seams around one scientific
call: the exact evidence serializer, the compiler/module loader, and bounded
resource inspection. The live compiler return must equal the hash-bound
514,039-byte prefix; exactly one structural zero is appended before module
load, and the identical repaired object is retained and inspected.
"""

from __future__ import annotations

from base64 import b64encode
from contextlib import contextmanager
from dataclasses import dataclass, fields, is_dataclass
from fractions import Fraction
from hashlib import sha256
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
from types import MappingProxyType
from typing import Any, Callable, Iterator, Mapping, Sequence

import numpy as np

from . import legal_river_exact_cubin_zero_suffix_diagnostic as _suffix
from . import legal_river_exact_cubin_zero_suffix_diagnostic_result as _suffix_reader
from . import legal_river_quotient_cuda_compensated_work_preflight as _source
from .legal_river_quotient_cuda_consumer import CudaRuntimeIdentity


_ROOT = Path(__file__).parents[2]
BASE_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-owner-v4.json"
)
CORRECTION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-owner-v4-envelope-correction-v2.json"
)
SCIENTIFIC_SOURCE_RELATIVE_PATH = (
    "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py"
)
SUFFIX_SOURCE_RELATIVE_PATH = (
    "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic.py"
)
SUFFIX_READER_RELATIVE_PATH = (
    "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic_result.py"
)
SUFFIX_ARTIFACT_RELATIVE_PATH = (
    "artifacts/work_preflight/legal_river_exact_cubin_zero_suffix_diagnostic_v1.jsonl"
)
BASE_CONFIG_SHA256 = "80aad86a806275c4b8979025237b555332e97a84ec1090845ee12616701b4b43"
CORRECTION_CONFIG_SHA256 = (
    "f4fdb2e89809f4c22422aed883b6d9f1bbb2e1aea6c32dfcf536f7a27d111ab7"
)
SCIENTIFIC_SOURCE_SHA256 = (
    "652a4a37cd097a92829364f1ec6976a6f31a4092ab9fc3e0f97a992e2565c4aa"
)
SUFFIX_SOURCE_SHA256 = (
    "6cb0fa3c4486bf8abf24931adc5fd97c6e905c62051b9d13826732cdf4249a24"
)
SUFFIX_READER_SHA256 = (
    "5faf0bbecbf1ff9c65b19327ff8700b757a5909c6fb22f6f07385b825d49357a"
)
SUFFIX_ARTIFACT_SHA256 = (
    "f4b3de941ed57e0f4acdfc7314315b6e70b10bd0034cf82113f17bf27e39a2de"
)
SUFFIX_ARTIFACT_BYTES = 6_164_894
ORIGINAL_PAYLOAD_SHA256 = _suffix.ORIGINAL_PAYLOAD_SHA256
ORIGINAL_PAYLOAD_BYTES = _suffix.ORIGINAL_PAYLOAD_BYTES
REPAIRED_PAYLOAD_SHA256 = _suffix.REPAIRED_PAYLOAD_SHA256
REPAIRED_PAYLOAD_BYTES = _suffix.REPAIRED_PAYLOAD_BYTES
MAXIMUM_PAYLOAD_BYTES = 8_388_608
MAXIMUM_STREAM_BYTES = 8_388_608
STREAM_CHUNK_RAW_BYTES = 196_608
MAXIMUM_COMBINED_VERSION_BYTES = 32_768
MAXIMUM_RESOURCE_STDOUT_BYTES = 262_144
PER_COMMAND_WALL_NS = 30_000_000_000
QUALIFIED_INSTRUMENT = "cuobjdump_resource_usage_on_exact_zero_suffix_payload"
APPROVED_RUNTIME_FIELDS = (
    "device_name",
    "compute_capability",
    "device_total_bytes",
    "cuda_driver_version",
    "cuda_runtime_version",
    "cupy_version",
)
DIRECT_KERNEL_NAMES = (
    "direct_selected_queries_tile",
    "direct_selected_fold_tile",
    "direct_selected_adjoint_tile",
)

_ORIGINAL_SCIENTIFIC_PLAIN = _source._plain
_ORIGINAL_SCIENTIFIC_KERNELS = _source._kernels
_ORIGINAL_SCIENTIFIC_RESOURCE = _source._compiled_cubin_resource_usage

Emit = Callable[[str, Mapping[str, object]], None]
CommandRunner = Callable[..., _suffix.CommandCapture]
ToolLoader = Callable[[], Path]


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"work-preflight v4 adapter path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _load_json_contract(
    path: Path, expected: str, schema: str
) -> dict[str, object]:
    import json

    raw = path.read_bytes()
    if len(raw) > 1_048_576:
        raise ValueError("work-preflight v4 config exceeds its byte ceiling")
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != expected:
        raise ValueError("work-preflight v4 config identity differs")
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema_version") != schema:
        raise ValueError("work-preflight v4 config schema differs")
    return value


def load_composite_config() -> tuple[dict[str, object], dict[str, object]]:
    base = _load_json_contract(
        _ROOT / BASE_CONFIG_RELATIVE_PATH,
        BASE_CONFIG_SHA256,
        "legal-river-quotient-cuda-compensated-work-preflight-owner-config-v4",
    )
    correction = _load_json_contract(
        _ROOT / CORRECTION_CONFIG_RELATIVE_PATH,
        CORRECTION_CONFIG_SHA256,
        "legal-river-quotient-cuda-compensated-work-preflight-owner-v4-envelope-correction-v2",
    )
    repair = base.get("exact_repair_contract")
    resource = base.get("resource_semantics")
    bounded = base.get("bounded_evidence_contract")
    journal = correction.get("corrected_journal_contract")
    parser = correction.get("parser_admission_contract")
    if not all(
        isinstance(item, Mapping)
        for item in (repair, resource, bounded, journal, parser)
    ):
        raise ValueError("work-preflight v4 composite config blocks differ")
    assert isinstance(repair, Mapping)
    assert isinstance(resource, Mapping)
    assert isinstance(bounded, Mapping)
    assert isinstance(journal, Mapping)
    assert isinstance(parser, Mapping)
    if (
        repair.get("original_payload_sha256") != ORIGINAL_PAYLOAD_SHA256
        or repair.get("original_payload_bytes") != ORIGINAL_PAYLOAD_BYTES
        or repair.get("repaired_payload_sha256") != REPAIRED_PAYLOAD_SHA256
        or repair.get("repaired_payload_bytes") != REPAIRED_PAYLOAD_BYTES
        or repair.get("suffix_hex") != "00"
        or resource.get("register_limit_per_thread") != 255
        or resource.get("stack_plus_local_backing_limit_bytes_per_thread")
        != 4096
        or bounded.get("repaired_payload_byte_limit") != MAXIMUM_PAYLOAD_BYTES
        or bounded.get("per_external_stream_byte_limit") != MAXIMUM_STREAM_BYTES
        or journal.get("stream_chunk_raw_bytes") != STREAM_CHUNK_RAW_BYTES
        or parser.get("maximum_combined_version_output_bytes")
        != MAXIMUM_COMBINED_VERSION_BYTES
        or parser.get("maximum_resource_stdout_bytes")
        != MAXIMUM_RESOURCE_STDOUT_BYTES
    ):
        raise ValueError("work-preflight v4 composite contract differs")
    return base, correction


def verify_immutable_sources_and_identities() -> None:
    load_composite_config()
    expected = {
        SCIENTIFIC_SOURCE_RELATIVE_PATH: SCIENTIFIC_SOURCE_SHA256,
        SUFFIX_SOURCE_RELATIVE_PATH: SUFFIX_SOURCE_SHA256,
        SUFFIX_READER_RELATIVE_PATH: SUFFIX_READER_SHA256,
    }
    for relative, digest in expected.items():
        if canonical_lf_sha256(_ROOT / relative) != digest:
            raise RuntimeError(
                f"work-preflight v4 immutable dependency differs: {relative}"
            )
    if (
        _source._plain is not _ORIGINAL_SCIENTIFIC_PLAIN
        or _source._kernels is not _ORIGINAL_SCIENTIFIC_KERNELS
        or _source._compiled_cubin_resource_usage
        is not _ORIGINAL_SCIENTIFIC_RESOURCE
    ):
        raise RuntimeError("work-preflight v4 scientific seam identity differs")
    if _source._KERNEL_CACHE or _source._MODULE_CACHE or _source._CUBIN_CACHE:
        raise RuntimeError("work-preflight v4 scientific caches are not empty")


def qualified_original_payload() -> bytes:
    path = _ROOT / SUFFIX_ARTIFACT_RELATIVE_PATH
    raw = path.read_bytes()
    if (
        len(raw) != SUFFIX_ARTIFACT_BYTES
        or sha256(raw).hexdigest() != SUFFIX_ARTIFACT_SHA256
    ):
        raise RuntimeError("work-preflight v4 suffix artifact identity differs")
    rebound = _suffix_reader.rebind_zero_suffix_diagnostic_journal(raw)
    repaired = rebound.repaired_payload
    if (
        rebound.terminal != "suffix_reconstruction_pass"
        or not rebound.passed
        or rebound.qualified_resource_instrument != QUALIFIED_INSTRUMENT
        or repaired is None
        or repaired.sha256 != REPAIRED_PAYLOAD_SHA256
        or repaired.byte_count != REPAIRED_PAYLOAD_BYTES
        or repaired.raw[-1:] != b"\x00"
    ):
        raise RuntimeError("work-preflight v4 suffix artifact semantics differ")
    original = repaired.raw[:-1]
    if (
        len(original) != ORIGINAL_PAYLOAD_BYTES
        or sha256(original).hexdigest() != ORIGINAL_PAYLOAD_SHA256
    ):
        raise RuntimeError("work-preflight v4 original payload identity differs")
    return original


def plain_evidence_v4(value: Any) -> Any:
    """Normalize the immutable JSON domain plus exact CudaRuntimeIdentity."""

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
            field.name: plain_evidence_v4(getattr(value, field.name))
            for field in declared
        }
    if isinstance(value, Mapping):
        return {str(key): plain_evidence_v4(item) for key, item in value.items()}
    if isinstance(value, tuple) and hasattr(type(value), "_fields"):
        raise TypeError(
            f"unsupported work-preflight evidence type: {type(value).__name__}"
        )
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [plain_evidence_v4(item) for item in value]
    raise TypeError(f"unsupported work-preflight evidence type: {type(value).__name__}")


def _stream_chunks(
    command_id: str, stream_name: str, raw: bytes
) -> tuple[dict[str, object], ...]:
    if stream_name not in {"stdout", "stderr"} or not isinstance(raw, bytes):
        raise TypeError("work-preflight v4 command stream differs")
    if len(raw) > MAXIMUM_STREAM_BYTES:
        raise ValueError("work-preflight v4 command stream exceeds capture cap")
    digest = sha256(raw).hexdigest()
    chunks = tuple(
        raw[index : index + STREAM_CHUNK_RAW_BYTES]
        for index in range(0, len(raw), STREAM_CHUNK_RAW_BYTES)
    )
    return tuple(
        {
            "schema_version": (
                "legal-river-work-preflight-resource-command-stream-v4"
            ),
            "command_id": command_id,
            "stream": stream_name,
            "chunk_index": index,
            "chunk_count": len(chunks),
            "chunk_raw_bytes": len(chunk),
            "total_raw_bytes": len(raw),
            "total_sha256": digest,
            "chunk_base64": b64encode(chunk).decode("ascii"),
        }
        for index, chunk in enumerate(chunks)
    )


def emit_command_capture(
    command_id: str,
    argv_role: str,
    capture: _suffix.CommandCapture,
    emit: Emit,
) -> None:
    if command_id not in {"cuobjdump_version", "cuobjdump_resource_usage"}:
        raise ValueError("work-preflight v4 command identity differs")
    if not isinstance(capture, _suffix.CommandCapture):
        raise TypeError("work-preflight v4 command capture type differs")
    for stream_name, raw in (("stdout", capture.stdout), ("stderr", capture.stderr)):
        for event in _stream_chunks(command_id, stream_name, raw):
            emit("resource_command_stream", event)
    emit(
        "resource_command_terminal",
        {
            "schema_version": (
                "legal-river-work-preflight-resource-command-terminal-v4"
            ),
            "command_id": command_id,
            "argv_role": argv_role,
            "status": capture.status,
            "return_code": capture.return_code,
            "stdout_bytes": len(capture.stdout),
            "stdout_sha256": sha256(capture.stdout).hexdigest(),
            "stderr_bytes": len(capture.stderr),
            "stderr_sha256": sha256(capture.stderr).hexdigest(),
            "elapsed_ns": capture.elapsed_ns,
        },
    )


def _accepted_ascii(raw: bytes, *, maximum: int, label: str) -> str:
    if not isinstance(raw, bytes) or len(raw) > maximum:
        raise _source.CompilerResourceRejection(
            f"{label} exceeds parser admission"
        )
    if any(
        byte not in {9, 10, 13} and not 0x20 <= byte <= 0x7E for byte in raw
    ):
        raise _source.CompilerResourceRejection(
            f"{label} is not admitted strict ASCII"
        )
    return raw.decode("ascii")


@dataclass(slots=True)
class _InstalledState:
    original: bytes | None = None
    repaired: bytes | None = None
    module_loaded: bool = False
    repair_event_emitted: bool = False
    temporary_created: bool = False
    temporary_removed: bool = False


def _default_tool_loader() -> Path:
    path = Path(
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\cuobjdump.exe"
    )
    if not path.is_file():
        raise _source.CompilerResourceRejection(
            "CUDA 13.3 cuobjdump is unavailable"
        )
    return path


@contextmanager
def installed_repaired_executed_cubin(
    emit: Emit,
    *,
    command_runner: CommandRunner = _suffix.run_bounded_binary_command,
    tool_loader: ToolLoader = _default_tool_loader,
) -> Iterator[_InstalledState]:
    """Install the three frozen process-local seams and restore them exactly."""

    verify_immutable_sources_and_identities()
    if threading.active_count() != 1:
        raise RuntimeError("work-preflight v4 adapter process has another live thread")
    if not callable(emit) or not callable(command_runner) or not callable(tool_loader):
        raise TypeError("work-preflight v4 adapter callable seam differs")
    state = _InstalledState()
    contract = _suffix.frozen_structural_contract()

    def repaired_kernels(cp: Any) -> Mapping[str, object]:
        device = int(cp.cuda.Device().id)
        if _source._KERNEL_CACHE or _source._MODULE_CACHE or _source._CUBIN_CACHE:
            raise RuntimeError(
                "work-preflight v4 compile caches changed before repair"
            )
        binary, _ = cp.cuda.compiler.compile_using_nvrtc(
            _source.CUDA_SOURCE,
            options=_source.CUDA_COMPILE_OPTIONS,
            cache_in_memory=True,
        )
        original = bytes(binary)
        if len(original) > MAXIMUM_PAYLOAD_BYTES:
            raise _source.CompilerResourceRejection(
                "work-preflight v4 compiler payload exceeds cap"
            )
        evidence = _suffix.reconstruct_exact_one_zero(original, contract)
        repaired = evidence.repaired
        module = cp.cuda.function.Module()
        module.load(repaired)
        functions = MappingProxyType(
            {name: module.get_function(name) for name in _source.KERNEL_NAMES}
        )
        state.original = original
        state.repaired = repaired
        state.module_loaded = True
        _source._MODULE_CACHE[device] = module
        _source._CUBIN_CACHE[device] = repaired
        _source._KERNEL_CACHE[device] = functions
        emit(
            "repaired_executed_cubin",
            {
                "schema_version": (
                    "legal-river-work-preflight-repaired-executed-cubin-v4"
                ),
                "original_payload_sha256": sha256(original).hexdigest(),
                "original_payload_bytes": len(original),
                "repaired_payload_sha256": sha256(repaired).hexdigest(),
                "repaired_payload_bytes": len(repaired),
                "suffix_hex": repaired[-1:].hex(),
                "module_loaded_repaired_bytes": True,
                "retained_object_is_loaded_object": (
                    _source._CUBIN_CACHE[device] is repaired
                ),
                "resolved_function_names": list(_source.KERNEL_NAMES),
                "caller_supplied_nvrtc_options": list(
                    _source.CUDA_COMPILE_OPTIONS
                ),
                "elf_header": dict(evidence.header),
                "program_header_count": len(evidence.program_headers),
                "section_table_sha256": evidence.section_table_sha256,
                "section_header_count": evidence.section_header_count,
                "qualified_resource_instrument": QUALIFIED_INSTRUMENT,
            },
        )
        state.repair_event_emitted = True
        return functions

    def bounded_resource_inspector(
        cp: Any,
        driver_direct: Mapping[str, Mapping[str, int]],
    ) -> dict[str, object]:
        device = int(cp.cuda.Device().id)
        binary = _source._CUBIN_CACHE.get(device)
        if (
            state.repaired is None
            or binary is not state.repaired
            or sha256(binary).hexdigest() != REPAIRED_PAYLOAD_SHA256
            or not state.module_loaded
            or not state.repair_event_emitted
        ):
            raise _source.CompilerResourceRejection(
                "work-preflight v4 executed/inspected identity differs"
            )
        tool = tool_loader()
        version = command_runner(
            [str(tool), "--version"],
            wall_limit_ns=PER_COMMAND_WALL_NS,
            stream_limit=MAXIMUM_STREAM_BYTES,
        )
        emit_command_capture(
            "cuobjdump_version", "cuobjdump --version", version, emit
        )
        if version.status != "completed" or version.return_code != 0:
            raise _source.CompilerResourceRejection(
                "work-preflight v4 cuobjdump version rejected"
            )
        combined_version = b"\n".join(
            value.strip()
            for value in (version.stdout, version.stderr)
            if value.strip()
        )
        version_output = _accepted_ascii(
            combined_version,
            maximum=MAXIMUM_COMBINED_VERSION_BYTES,
            label="cuobjdump version output",
        )
        if re.search(r"(?<!\d)13\.3(?!\d)", version_output) is None:
            raise _source.CompilerResourceRejection(
                "cuobjdump is not the frozen CUDA 13.3 tool"
            )

        temporary_path: Path | None = None
        try:
            if not state.repair_event_emitted:
                raise RuntimeError(
                    "work-preflight v4 repair evidence is not durable"
                )
            with tempfile.NamedTemporaryFile(
                suffix=".cubin", delete=False
            ) as handle:
                handle.write(binary)
                handle.flush()
                os.fsync(handle.fileno())
                temporary_path = Path(handle.name)
            state.temporary_created = True
            resource = command_runner(
                [str(tool), "--dump-resource-usage", str(temporary_path)],
                wall_limit_ns=PER_COMMAND_WALL_NS,
                stream_limit=MAXIMUM_STREAM_BYTES,
            )
            emit_command_capture(
                "cuobjdump_resource_usage",
                "cuobjdump --dump-resource-usage repaired-payload",
                resource,
                emit,
            )
            if resource.status != "completed" or resource.return_code != 0:
                raise _source.CompilerResourceRejection(
                    "work-preflight v4 resource command rejected"
                )
            raw_resource_stdout = _accepted_ascii(
                resource.stdout,
                maximum=MAXIMUM_RESOURCE_STDOUT_BYTES,
                label="cuobjdump resource stdout",
            )
            parsed = _source.parse_cuobjdump_resource_usage(
                raw_resource_stdout
            )
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
                state.temporary_removed = not temporary_path.exists()
                emit(
                    "resource_temporary_cleanup",
                    {
                        "schema_version": (
                            "legal-river-work-preflight-resource-cleanup-v4"
                        ),
                        "temporary_created": state.temporary_created,
                        "temporary_removed": state.temporary_removed,
                        "repaired_payload_sha256": REPAIRED_PAYLOAD_SHA256,
                    },
                )
        direct = {name: parsed[name] for name in DIRECT_KERNEL_NAMES}
        properties = cp.cuda.runtime.getDeviceProperties(device)
        combined = _source.combined_direct_kernel_resource_report(
            direct,
            driver_direct,
            multiprocessor_count=int(properties["multiProcessorCount"]),
            maximum_threads_per_multiprocessor=int(
                properties["maxThreadsPerMultiProcessor"]
            ),
        )
        return {
            "tool_path": str(tool),
            "tool_version_output": version_output,
            "raw_resource_stdout": raw_resource_stdout,
            "cubin_sha256": sha256(binary).hexdigest(),
            "retained_payload_format": "elf-cubin",
            "caller_supplied_nvrtc_options": list(
                _source.CUDA_COMPILE_OPTIONS
            ),
            "cupy_version": str(cp.__version__),
            "cupy_internal_options_disclosure": [
                "target_architecture",
                "device_as_default_execution_space",
                "version_dependent_precompiled_header",
            ],
            "direct": direct,
            "driver_direct": {
                name: dict(row) for name, row in driver_direct.items()
            },
            "effective_maxima": combined["effective_maxima"],
            "runtime_residency": combined["runtime_residency"],
            "gates": combined["gates"],
            "claims": {
                "exact_spill_load_store_count": None,
                "local_and_stack_are_not_relabeled_as_spill_counts": True,
            },
        }

    _source._plain = plain_evidence_v4
    _source._kernels = repaired_kernels
    _source._compiled_cubin_resource_usage = bounded_resource_inspector
    try:
        yield state
    finally:
        installed = (
            _source._plain,
            _source._kernels,
            _source._compiled_cubin_resource_usage,
        )
        _source._plain = _ORIGINAL_SCIENTIFIC_PLAIN
        _source._kernels = _ORIGINAL_SCIENTIFIC_KERNELS
        _source._compiled_cubin_resource_usage = _ORIGINAL_SCIENTIFIC_RESOURCE
        _source._KERNEL_CACHE.clear()
        _source._MODULE_CACHE.clear()
        _source._CUBIN_CACHE.clear()
        if installed != (
            plain_evidence_v4,
            repaired_kernels,
            bounded_resource_inspector,
        ):
            raise RuntimeError("work-preflight v4 installed seam identity changed")
        verify_immutable_sources_and_identities()


def run_repaired_calibration_preflight(
    emit: Emit | None = None,
    *,
    command_runner: CommandRunner = _suffix.run_bounded_binary_command,
    tool_loader: ToolLoader = _default_tool_loader,
) -> dict[str, object]:
    """Call immutable science once with the composite V4 seams installed."""

    callback: Emit = emit if emit is not None else lambda _kind, _event: None
    with installed_repaired_executed_cubin(
        callback,
        command_runner=command_runner,
        tool_loader=tool_loader,
    ):
        return _source.run_calibration_preflight(callback)


def _probe_resource_stdout() -> bytes:
    rows = {
        "direct_selected_queries_tile": (40, 7, 5),
        "direct_selected_fold_tile": (50, 15, 9),
        "direct_selected_adjoint_tile": (30, 4, 6),
    }
    return b"".join(
        (
            f"Function {name}:\n REG:{reg} STACK:{stack} LOCAL:{local}\n"
        ).encode("ascii")
        for name, (reg, stack, local) in rows.items()
    )


def run_device_free_adapter_probe(
    emit: Emit | None = None,
) -> dict[str, object]:
    """Exercise repair/load/retain/inspect with exact bytes and no CuPy."""

    if any(name == "cupy" or name.startswith("cupy.") for name in sys.modules):
        raise RuntimeError("work-preflight v4 adapter probe inherited CuPy")
    verify_immutable_sources_and_identities()
    original = qualified_original_payload()
    events: list[tuple[str, Mapping[str, object]]] = []

    def capture(kind: str, event: Mapping[str, object]) -> None:
        events.append((kind, dict(event)))
        if emit is not None:
            emit(kind, event)

    class FakeFunction:
        pass

    class FakeModule:
        loaded: bytes | None = None

        def load(self, raw: bytes) -> None:
            self.loaded = raw

        def get_function(self, name: str) -> FakeFunction:
            if self.loaded is None or name not in _source.KERNEL_NAMES:
                raise RuntimeError(
                    "work-preflight v4 fake module lookup differs"
                )
            return FakeFunction()

    class FakeCompiler:
        @staticmethod
        def compile_using_nvrtc(
            source: str, *, options: Sequence[str], cache_in_memory: bool
        ) -> tuple[bytes, None]:
            if (
                source != _source.CUDA_SOURCE
                or tuple(options) != _source.CUDA_COMPILE_OPTIONS
                or not cache_in_memory
            ):
                raise RuntimeError(
                    "work-preflight v4 fake compiler contract differs"
                )
            return original, None

    class FakeDevice:
        id = 0

    class FakeRuntime:
        @staticmethod
        def getDeviceProperties(device: int) -> Mapping[str, int]:
            if device != 0:
                raise RuntimeError("work-preflight v4 fake device differs")
            return {
                "multiProcessorCount": 84,
                "maxThreadsPerMultiProcessor": 1536,
            }

    class FakeCuda:
        Device = FakeDevice
        compiler = FakeCompiler
        runtime = FakeRuntime

        class function:
            Module = FakeModule

    class FakeCupy:
        __version__ = "14.2.0-probe"
        cuda = FakeCuda

    def fake_command_runner(
        argv: Sequence[str], *, wall_limit_ns: int, stream_limit: int
    ) -> _suffix.CommandCapture:
        if (
            wall_limit_ns != PER_COMMAND_WALL_NS
            or stream_limit != MAXIMUM_STREAM_BYTES
        ):
            raise RuntimeError("work-preflight v4 probe command bounds differ")
        if list(argv)[-1] == "--version":
            stdout = b"Cuda compilation tools, release 13.3, V13.3.73\n"
        elif "--dump-resource-usage" in argv:
            stdout = _probe_resource_stdout()
        else:
            raise RuntimeError("work-preflight v4 probe command differs")
        return _suffix.CommandCapture(
            status="completed",
            return_code=0,
            stdout=stdout,
            stderr=b"",
            elapsed_ns=1,
        )

    driver = {
        "direct_selected_queries_tile": {
            "local_size_bytes": 11,
            "registers": 41,
            "shared_size_bytes": 0,
            "maximum_threads_per_block": 1024,
        },
        "direct_selected_fold_tile": {
            "local_size_bytes": 30,
            "registers": 49,
            "shared_size_bytes": 0,
            "maximum_threads_per_block": 1024,
        },
        "direct_selected_adjoint_tile": {
            "local_size_bytes": 8,
            "registers": 30,
            "shared_size_bytes": 0,
            "maximum_threads_per_block": 1024,
        },
    }
    original_counter = _source._BOUNDED_EXECUTION_CALLS
    with installed_repaired_executed_cubin(
        capture,
        command_runner=fake_command_runner,
        tool_loader=lambda: Path(r"C:\frozen-probe\cuobjdump.exe"),
    ) as state:
        _source._kernels(FakeCupy)
        report = _source._compiled_cubin_resource_usage(FakeCupy, driver)
        if not state.temporary_removed:
            raise RuntimeError(
                "work-preflight v4 probe temporary cleanup failed"
            )
    if _source._BOUNDED_EXECUTION_CALLS != original_counter:
        raise RuntimeError(
            "work-preflight v4 probe changed scientific call counter"
        )
    expected_maxima = {
        "direct_selected_adjoint_tile": {
            "registers": 30,
            "stack_plus_local_backing_bytes": 10,
        },
        "direct_selected_fold_tile": {
            "registers": 50,
            "stack_plus_local_backing_bytes": 30,
        },
        "direct_selected_queries_tile": {
            "registers": 41,
            "stack_plus_local_backing_bytes": 12,
        },
    }
    if (
        report["effective_maxima"] != expected_maxima
        or not all(report["gates"].values())
    ):
        raise RuntimeError("work-preflight v4 probe resource envelope differs")
    event_kinds = [kind for kind, _ in events]
    if (
        not event_kinds
        or event_kinds[0] != "repaired_executed_cubin"
        or event_kinds.count("resource_command_terminal") != 2
        or event_kinds[-1] != "resource_temporary_cleanup"
    ):
        raise RuntimeError("work-preflight v4 probe event order differs")
    runtime = CudaRuntimeIdentity(
        device_name="adapter-probe-device",
        compute_capability="00",
        device_total_bytes=0,
        cuda_driver_version=0,
        cuda_runtime_version=0,
        cupy_version="adapter-probe-no-cupy",
    )
    if any(name == "cupy" or name.startswith("cupy.") for name in sys.modules):
        raise RuntimeError("work-preflight v4 adapter probe imported CuPy")
    return {
        "schema_version": "legal-river-work-preflight-adapter-probe-v4",
        "event_kinds": event_kinds,
        "effective_maxima": report["effective_maxima"],
        "resource_gates": report["gates"],
        "runtime": plain_evidence_v4(runtime),
        "original_payload_sha256": ORIGINAL_PAYLOAD_SHA256,
        "repaired_payload_sha256": REPAIRED_PAYLOAD_SHA256,
        "cupy_loaded": False,
        "scientific_call_counter_unchanged": True,
        "identities_and_caches_restored": True,
        "passed": True,
    }


__all__ = [
    "APPROVED_RUNTIME_FIELDS",
    "BASE_CONFIG_SHA256",
    "CORRECTION_CONFIG_SHA256",
    "MAXIMUM_COMBINED_VERSION_BYTES",
    "MAXIMUM_PAYLOAD_BYTES",
    "MAXIMUM_RESOURCE_STDOUT_BYTES",
    "MAXIMUM_STREAM_BYTES",
    "ORIGINAL_PAYLOAD_SHA256",
    "QUALIFIED_INSTRUMENT",
    "REPAIRED_PAYLOAD_SHA256",
    "SCIENTIFIC_SOURCE_SHA256",
    "STREAM_CHUNK_RAW_BYTES",
    "canonical_lf_sha256",
    "emit_command_capture",
    "installed_repaired_executed_cubin",
    "load_composite_config",
    "plain_evidence_v4",
    "qualified_original_payload",
    "run_device_free_adapter_probe",
    "run_repaired_calibration_preflight",
    "verify_immutable_sources_and_identities",
]
