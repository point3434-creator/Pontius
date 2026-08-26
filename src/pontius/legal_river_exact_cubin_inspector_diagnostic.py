"""Exact-binary CUDA inspector diagnostic frozen by ADR-0404.

Importing this module is device-free.  The real entry point imports CuPy and
the immutable work-preflight source only inside a fresh child process.
"""

from __future__ import annotations

import base64
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
from time import perf_counter_ns, sleep
from typing import BinaryIO


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-exact-cubin-inspector-diagnostic-v1.json"
)
SCIENTIFIC_SOURCE_RELATIVE_PATH = (
    "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py"
)
CONFIG_SHA256 = "d52ac02e83f71cb50b6a61e8a9dd18403171e4ddd25227b2036bb61c2085fe8a"
SCIENTIFIC_SOURCE_SHA256 = (
    "652a4a37cd097a92829364f1ec6976a6f31a4092ab9fc3e0f97a992e2565c4aa"
)
CUDA_SOURCE_SHA256 = "306bcbbccf050d503ddb4314b4d178974f6fb3c361f2cda9d15bf277a693219a"
CUDA_SOURCE_BYTES = 26013
ELF_MAGIC = b"\x7fELF"
CALLER_OPTIONS = (
    "--std=c++14",
    "--ftz=false",
    "--prec-div=true",
    "--prec-sqrt=true",
    "--fmad=false",
)
DIRECT_KERNEL_NAMES = (
    "direct_selected_queries_tile",
    "direct_selected_fold_tile",
    "direct_selected_adjoint_tile",
)
ALL_KERNEL_NAMES = (
    "primitive_pairs",
    "source_coefficients_tile",
    "zeta_level_tile",
    "signed_targets_tile",
    "fold_query_tile",
    "build_numerator_covector_tile",
    "aggregate_query_labels_tile",
    "source_adjoint_contract_tile",
    "reduce_contiguous_pairs",
    "reduce_strided_pairs",
    "finalize_pair_result",
    "direct_selected_queries_tile",
    "direct_selected_fold_tile",
    "direct_selected_adjoint_tile",
    "selected_query_weights",
)
RUNTIME_FIELDS = (
    "device_name",
    "compute_capability",
    "device_total_bytes",
    "cuda_driver_version",
    "cuda_runtime_version",
    "cupy_version",
)
MAXIMUM_STREAM_BYTES = 8_388_608
MAXIMUM_CUBIN_BYTES = 8_388_608
PER_COMMAND_WALL_NS = 30_000_000_000
LABORATORY_WALL_NS = 180_000_000_000
_READ_CHUNK = 65_536


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"exact-cubin diagnostic path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistered_config() -> dict[str, object]:
    path = _ROOT / CONFIG_RELATIVE_PATH
    raw = path.read_bytes()
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != CONFIG_SHA256:
        raise ValueError("exact-cubin diagnostic config differs from ADR-0404")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise TypeError("exact-cubin diagnostic config must be an object")
    parent = value.get("parent_identity")
    capture = value.get("lossless_capture_contract")
    candidates = value.get("candidate_commands_in_order")
    interpretation = value.get("candidate_interpretation_contract")
    if (
        not isinstance(parent, Mapping)
        or not isinstance(capture, Mapping)
        or not isinstance(candidates, list)
        or not isinstance(interpretation, Mapping)
        or parent.get("immutable_scientific_source_canonical_lf_sha256")
        != SCIENTIFIC_SOURCE_SHA256
        or parent.get("embedded_cuda_source_utf8_sha256") != CUDA_SOURCE_SHA256
        or parent.get("embedded_cuda_source_utf8_bytes") != CUDA_SOURCE_BYTES
        or tuple(parent.get("caller_supplied_nvrtc_options_in_order", ()))
        != CALLER_OPTIONS
        or tuple(parent.get("direct_kernel_names_in_order", ()))
        != DIRECT_KERNEL_NAMES
        or capture.get("per_stream_byte_limit") != MAXIMUM_STREAM_BYTES
        or capture.get("cubin_byte_limit") != MAXIMUM_CUBIN_BYTES
        or capture.get("per_command_wall_limit_ns") != PER_COMMAND_WALL_NS
        or capture.get("laboratory_wall_limit_ns") != LABORATORY_WALL_NS
        or interpretation.get("selected_inspector") is not None
        or interpretation.get("driver_only_fallback_forbidden") is not True
        or len(candidates) != 5
    ):
        raise ValueError("exact-cubin diagnostic frozen contract differs")
    return value


def encode_binary(raw: bytes) -> dict[str, object]:
    if not isinstance(raw, bytes):
        raise TypeError("binary evidence must be immutable bytes")
    return {
        "encoding": "base64_standard",
        "byte_count": len(raw),
        "sha256": sha256(raw).hexdigest(),
        "base64": base64.b64encode(raw).decode("ascii"),
    }


def _runtime_mapping(runtime: object) -> dict[str, object]:
    qualified = f"{type(runtime).__module__}.{type(runtime).__qualname__}"
    expected = "pontius.legal_river_quotient_cuda_consumer.CudaRuntimeIdentity"
    if qualified != expected:
        raise TypeError("exact-cubin diagnostic runtime identity type differs")
    result = {field: getattr(runtime, field) for field in RUNTIME_FIELDS}
    if (
        any(
            not isinstance(result[field], str) or not result[field]
            for field in ("device_name", "compute_capability", "cupy_version")
        )
        or any(
            isinstance(result[field], bool)
            or not isinstance(result[field], int)
            or result[field] < 0
            for field in (
                "device_total_bytes",
                "cuda_driver_version",
                "cuda_runtime_version",
            )
        )
    ):
        raise TypeError("exact-cubin diagnostic runtime field type differs")
    if hasattr(runtime, "__dict__"):
        raise TypeError("exact-cubin diagnostic runtime unexpectedly has __dict__")
    return result


@dataclass(frozen=True, slots=True)
class CommandCapture:
    status: str
    return_code: int | None
    stdout: bytes
    stderr: bytes
    elapsed_ns: int

    def __post_init__(self) -> None:
        if self.status not in {"completed", "timeout", "output_limit"}:
            raise ValueError("command capture status differs")
        if self.return_code is not None and (
            isinstance(self.return_code, bool) or not isinstance(self.return_code, int)
        ):
            raise TypeError("command return code must be an integer or null")
        if not isinstance(self.stdout, bytes) or not isinstance(self.stderr, bytes):
            raise TypeError("command streams must be immutable bytes")
        if len(self.stdout) > MAXIMUM_STREAM_BYTES or len(self.stderr) > MAXIMUM_STREAM_BYTES:
            raise ValueError("command stream exceeds frozen cap")
        if isinstance(self.elapsed_ns, bool) or not isinstance(self.elapsed_ns, int):
            raise TypeError("command elapsed time must be an integer")
        if self.elapsed_ns < 0:
            raise ValueError("command elapsed time must be nonnegative")


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2.0)


def run_bounded_binary_command(
    argv: Sequence[str],
    *,
    wall_limit_ns: int = PER_COMMAND_WALL_NS,
    stream_limit: int = MAXIMUM_STREAM_BYTES,
) -> CommandCapture:
    """Run one candidate without check/text conversion or unbounded pipe reads."""

    if (
        not isinstance(argv, Sequence)
        or isinstance(argv, (str, bytes, bytearray))
        or not argv
        or any(not isinstance(item, str) or not item for item in argv)
    ):
        raise TypeError("command argv must be a nonempty string sequence")
    if (
        isinstance(wall_limit_ns, bool)
        or not isinstance(wall_limit_ns, int)
        or wall_limit_ns <= 0
        or isinstance(stream_limit, bool)
        or not isinstance(stream_limit, int)
        or stream_limit <= 0
    ):
        raise ValueError("command bounds must be positive integers")

    creationflags = 0
    if os.name == "nt":
        creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    started = perf_counter_ns()
    process = subprocess.Popen(
        list(argv),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags,
    )
    if process.stdout is None or process.stderr is None:
        _terminate_process(process)
        raise RuntimeError("command pipes were not created")

    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    exceeded = threading.Event()
    lock = threading.Lock()

    def drain(name: str, pipe: BinaryIO) -> None:
        try:
            while True:
                chunk = pipe.read(_READ_CHUNK)
                if not chunk:
                    return
                with lock:
                    buffer = buffers[name]
                    room = max(0, stream_limit - len(buffer))
                    buffer.extend(chunk[:room])
                    if len(chunk) > room:
                        exceeded.set()
        finally:
            pipe.close()

    threads = (
        threading.Thread(target=drain, args=("stdout", process.stdout), daemon=True),
        threading.Thread(target=drain, args=("stderr", process.stderr), daemon=True),
    )
    for thread in threads:
        thread.start()

    status = "completed"
    deadline = started + wall_limit_ns
    try:
        while process.poll() is None:
            if exceeded.is_set():
                status = "output_limit"
                _terminate_process(process)
                break
            if perf_counter_ns() >= deadline:
                status = "timeout"
                _terminate_process(process)
                break
            sleep(0.001)
        if exceeded.is_set():
            status = "output_limit"
    finally:
        _terminate_process(process)
        for thread in threads:
            thread.join(timeout=5.0)
        if any(thread.is_alive() for thread in threads):
            raise RuntimeError("command pipe reader did not terminate")
    elapsed = perf_counter_ns() - started
    if status == "completed" and elapsed > wall_limit_ns:
        status = "timeout"
    return CommandCapture(
        status=status,
        return_code=process.returncode,
        stdout=bytes(buffers["stdout"]),
        stderr=bytes(buffers["stderr"]),
        elapsed_ns=elapsed,
    )


def _tool_paths() -> dict[str, Path]:
    root = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin")
    result = {
        "CUDA_13_3_cuobjdump": root / "cuobjdump.exe",
        "CUDA_13_3_nvdisasm": root / "nvdisasm.exe",
    }
    if any(not path.is_file() for path in result.values()):
        raise FileNotFoundError("exact CUDA 13.3 inspector tool is absent")
    return result


def _candidate_argv(
    row: Mapping[str, object],
    *,
    tools: Mapping[str, Path],
    cubin_path: Path,
) -> list[str]:
    tool_name = row.get("tool")
    arguments = row.get("arguments")
    if not isinstance(tool_name, str) or tool_name not in tools:
        raise ValueError("candidate tool differs")
    if not isinstance(arguments, list) or any(not isinstance(item, str) for item in arguments):
        raise ValueError("candidate arguments differ")
    return [
        str(tools[tool_name]),
        *[
            str(cubin_path) if item == "{exact_temporary_cubin}" else item
            for item in arguments
        ],
    ]


EmitAndWait = Callable[[str, Mapping[str, object]], None]


def run_real_diagnostic(emit_and_wait: EmitAndWait) -> dict[str, object]:
    """Compile once, make the cubin durable, then capture every candidate."""

    if not callable(emit_and_wait):
        raise TypeError("diagnostic emitter must be callable")
    laboratory_started = perf_counter_ns()
    config = load_preregistered_config()
    if canonical_lf_sha256(_ROOT / SCIENTIFIC_SOURCE_RELATIVE_PATH) != SCIENTIFIC_SOURCE_SHA256:
        raise ValueError("immutable scientific source differs")
    if os.environ.get("CUPY_COMPILE_WITH_PTX", "").strip().lower() not in {
        "",
        "0",
        "false",
        "no",
        "off",
    }:
        raise RuntimeError("CUPY_COMPILE_WITH_PTX must be absent or false")

    # Deliberately local: importing this module remains device-free.
    from . import legal_river_quotient_cuda_compensated_work_preflight as science

    cuda_bytes = science.CUDA_SOURCE.encode("utf-8")
    if (
        len(cuda_bytes) != CUDA_SOURCE_BYTES
        or sha256(cuda_bytes).hexdigest() != CUDA_SOURCE_SHA256
        or tuple(science.cuda_compile_options()) != CALLER_OPTIONS
        or tuple(science.KERNEL_NAMES) != ALL_KERNEL_NAMES
        or science._KERNEL_CACHE
        or science._CUBIN_CACHE
        or science._MODULE_CACHE
    ):
        raise ValueError("immutable compile entry differs or cache is not fresh")

    cp = science._cupy_module()
    effective_arch, output_method = cp.cuda.compiler._get_arch_for_options_for_nvrtc()
    if output_method != "cubin" or not str(effective_arch).startswith("-arch=sm_"):
        raise RuntimeError("CuPy effective output is not a direct cubin")
    scientific_config = science.load_preregistered_work_preflight_config()
    science.verify_preregistered_work_preflight_contract(scientific_config)
    runtime = science._paired._runtime_identity(cp)
    science._paired._verify_runtime(runtime, scientific_config)
    kernels = science._kernels(cp)
    if tuple(kernels) != ALL_KERNEL_NAMES:
        raise ValueError("compiled kernel inventory differs")
    device = int(cp.cuda.Device().id)
    cubin = bytes(science._CUBIN_CACHE[device])
    if len(cubin) > MAXIMUM_CUBIN_BYTES or not cubin.startswith(ELF_MAGIC):
        raise RuntimeError("compiled payload is not a bounded ELF cubin")
    all_driver = science._paired._kernel_resource_report(cp, kernels)
    driver_direct = {
        name: {key: int(value) for key, value in all_driver[name].items()}
        for name in DIRECT_KERNEL_NAMES
    }
    emit_and_wait(
        "compiler_capture",
        {
            "schema_version": "legal-river-exact-cubin-compiler-capture-v1",
            "runtime": _runtime_mapping(runtime),
            "caller_options": list(CALLER_OPTIONS),
            "effective_internal_arch_option": str(effective_arch),
            "output_method": str(output_method),
            "kernel_names": list(ALL_KERNEL_NAMES),
            "direct_driver_rows": driver_direct,
            "cubin": encode_binary(cubin),
        },
    )

    candidates = config["candidate_commands_in_order"]
    assert isinstance(candidates, list)
    tools = _tool_paths()
    temporary_path: Path | None = None
    completed_candidates = 0
    terminal = "capture_complete"
    reason = "all frozen candidate outcomes retained"
    try:
        with tempfile.NamedTemporaryFile(suffix=".cubin", delete=False) as handle:
            handle.write(cubin)
            handle.flush()
            os.fsync(handle.fileno())
            temporary_path = Path(handle.name)
        if temporary_path.read_bytes() != cubin:
            raise RuntimeError("temporary cubin differs from durable capture")
        for index, row_value in enumerate(candidates):
            if not isinstance(row_value, Mapping):
                raise TypeError("candidate row must be a mapping")
            argv = _candidate_argv(row_value, tools=tools, cubin_path=temporary_path)
            capture = run_bounded_binary_command(argv)
            emit_and_wait(
                "candidate_command",
                {
                    "schema_version": "legal-river-exact-cubin-candidate-command-v1",
                    "candidate_index": index,
                    "candidate_id": row_value["candidate_id"],
                    "semantic_role": row_value["semantic_role"],
                    "uses_cubin": row_value["uses_cubin"],
                    "argv": argv,
                    "status": capture.status,
                    "return_code": capture.return_code,
                    "stdout": encode_binary(capture.stdout),
                    "stderr": encode_binary(capture.stderr),
                    "elapsed_ns": capture.elapsed_ns,
                },
            )
            completed_candidates += 1
            if capture.status != "completed":
                terminal = f"candidate_{capture.status}_rejection"
                reason = f"{row_value['candidate_id']} ended as {capture.status}"
                break
            if perf_counter_ns() - laboratory_started > LABORATORY_WALL_NS:
                terminal = "laboratory_wall_rejection"
                reason = "diagnostic laboratory wall crossed"
                break
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    emit_and_wait(
        "cleanup",
        {
            "schema_version": "legal-river-exact-cubin-cleanup-v1",
            "temporary_cubin_removed": temporary_path is not None
            and not temporary_path.exists(),
            "candidate_events_retained": completed_candidates,
        },
    )
    return {
        "schema_version": "legal-river-exact-cubin-diagnostic-terminal-evidence-v1",
        "terminal": terminal,
        "passed": terminal == "capture_complete",
        "reason": reason,
        "candidate_events_retained": completed_candidates,
        "selected_inspector": None,
        "resource_gate_result": None,
        "calibration_result": None,
        "capacity_projection": None,
    }


__all__ = [
    "ALL_KERNEL_NAMES",
    "CALLER_OPTIONS",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "CommandCapture",
    "DIRECT_KERNEL_NAMES",
    "LABORATORY_WALL_NS",
    "MAXIMUM_CUBIN_BYTES",
    "MAXIMUM_STREAM_BYTES",
    "PER_COMMAND_WALL_NS",
    "canonical_lf_sha256",
    "encode_binary",
    "load_preregistered_config",
    "run_bounded_binary_command",
    "run_real_diagnostic",
]
