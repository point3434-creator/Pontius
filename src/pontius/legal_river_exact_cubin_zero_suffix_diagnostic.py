"""Exact one-byte ELF suffix diagnostic frozen by ADR-0410.

Importing this module is device-, process-, and write-free.  The only real
entry point runs in the fresh child owned by the companion runner.  It reads
the retained ADR-0406 payload, appends exactly one zero after proving the
frozen structural predicate, and never compiles or launches a kernel.
"""

from __future__ import annotations

import base64
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import threading
from time import perf_counter_ns, sleep
from typing import BinaryIO, Final


_ROOT: Final = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH: Final = (
    "experiments/configs/legal-river-exact-cubin-zero-suffix-diagnostic-v1.json"
)
PARENT_ARTIFACT_RELATIVE_PATH: Final = (
    "artifacts/work_preflight/legal_river_exact_cubin_inspector_diagnostic_v1.jsonl"
)
PARENT_SELECTION_RELATIVE_PATH: Final = (
    "experiments/results/legal-river-exact-cubin-inspector-selection-v1.json"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH: Final = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
CONFIG_SHA256: Final = (
    "6473d8726bc359091f21706b06a5798f67e1ba19919a2de66db17f7c0329d32d"
)
PARENT_ARTIFACT_SHA256: Final = (
    "9e0d160dd36884adb85914f819e11882d5becc42071f7847c1503a42c1d83aed"
)
PARENT_ARTIFACT_BYTES: Final = 705_101
PARENT_ARTIFACT_RECORDS: Final = 12
PARENT_SELECTION_SHA256: Final = (
    "ebc66a0d06a84eeb16d5c2d6adf6376227011ef3982c8fcdd09e97496c276d1f"
)
PARENT_SELECTION_BYTES: Final = 3_164
ORIGINAL_PAYLOAD_SHA256: Final = (
    "5dc4973302061b29dccd955ff7ee4dff3d61216316fb5d2fa71e9df22f42cd97"
)
ORIGINAL_PAYLOAD_BYTES: Final = 514_039
REPAIRED_PAYLOAD_SHA256: Final = (
    "97693be7baafd882ad64a1a7da0ede23dc927efd872b0d15697b2486957ea894"
)
REPAIRED_PAYLOAD_BYTES: Final = 514_040
DIRECT_KERNEL_NAMES: Final = (
    "direct_selected_queries_tile",
    "direct_selected_fold_tile",
    "direct_selected_adjoint_tile",
)
ALL_KERNEL_NAMES: Final = (
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
ORIGINAL_DIRECT_DRIVER_ROWS: Final = {
    "direct_selected_queries_tile": {
        "local_size_bytes": 128,
        "maximum_threads_per_block": 1024,
        "registers": 38,
        "shared_size_bytes": 0,
    },
    "direct_selected_fold_tile": {
        "local_size_bytes": 1024,
        "maximum_threads_per_block": 1024,
        "registers": 48,
        "shared_size_bytes": 0,
    },
    "direct_selected_adjoint_tile": {
        "local_size_bytes": 128,
        "maximum_threads_per_block": 1024,
        "registers": 38,
        "shared_size_bytes": 0,
    },
}
QUALIFIED_INSTRUMENT: Final = (
    "cuobjdump_resource_usage_on_exact_zero_suffix_payload"
)
MAXIMUM_STREAM_BYTES: Final = 8_388_608
MAXIMUM_PAYLOAD_BYTES: Final = 8_388_608
PER_COMMAND_WALL_NS: Final = 30_000_000_000
LABORATORY_WALL_NS: Final = 180_000_000_000
_READ_CHUNK: Final = 65_536
_ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
_PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
_PROGRAM_HEADER_FIRST_SEVEN = struct.Struct("<IIQQQQQ")
_SECTION_HEADER = struct.Struct("<IIQQQQIIQQ")
_SHT_NOBITS: Final = 8
_CUOBJDUMP_VERSION_BYTES: Final = (
    b"cuobjdump: NVIDIA (R) fat binary listing tool\r\n"
    b"Copyright (c) 2005-2026 NVIDIA Corporation\r\n"
    b"Built on Tue_Jun__9_14:30:19_Pacific_Daylight_Time_2026\r\n"
    b"Cuda compilation tools, release 13.3, V13.3.73\r\n"
    b"Build cuda_13.3.r13.3/compiler.38244171_0\r\n"
)


class StructuralRejection(ValueError):
    """The sole frozen one-byte reconstruction predicate did not hold."""


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"zero-suffix diagnostic dependency is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _raw_file_identity(path: Path, *, digest: str, byte_count: int) -> bytes:
    raw = path.read_bytes()
    if len(raw) != byte_count or sha256(raw).hexdigest() != digest:
        raise ValueError(f"zero-suffix retained bytes differ: {path}")
    return raw


def load_preregistered_config() -> dict[str, object]:
    path = _ROOT / CONFIG_RELATIVE_PATH
    raw = path.read_bytes()
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != CONFIG_SHA256:
        raise ValueError("zero-suffix config differs from ADR-0410")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise TypeError("zero-suffix config must be an object")
    parent = value.get("parent_identity")
    reconstruction = value.get("reconstruction_contract")
    bounded = value.get("bounded_execution_contract")
    commands = value.get("candidate_commands_in_order")
    terminals = value.get("terminal_contract")
    if (
        value.get("schema_version")
        != "legal-river-exact-cubin-zero-suffix-diagnostic-preregistration-v1"
        or not isinstance(parent, Mapping)
        or not isinstance(reconstruction, Mapping)
        or not isinstance(bounded, Mapping)
        or not isinstance(commands, list)
        or not isinstance(terminals, Mapping)
        or parent.get("original_payload_sha256") != ORIGINAL_PAYLOAD_SHA256
        or parent.get("original_payload_bytes") != ORIGINAL_PAYLOAD_BYTES
        or parent.get("repaired_payload_sha256") != REPAIRED_PAYLOAD_SHA256
        or parent.get("repaired_payload_bytes") != REPAIRED_PAYLOAD_BYTES
        or tuple(value.get("all_kernel_names_in_order", ())) != ALL_KERNEL_NAMES
        or reconstruction.get("suffix_hex") != "00"
        or reconstruction.get("suffix_bytes") != 1
        or bounded.get("per_stream_byte_limit") != MAXIMUM_STREAM_BYTES
        or bounded.get("repaired_payload_byte_limit") != MAXIMUM_PAYLOAD_BYTES
        or bounded.get("per_command_wall_limit_ns") != PER_COMMAND_WALL_NS
        or bounded.get("laboratory_wall_limit_ns") != LABORATORY_WALL_NS
        or len(commands) != 6
        or terminals.get("pass_terminal") != "suffix_reconstruction_pass"
        or terminals.get("resource_gate_result") is not None
        or terminals.get("calibration_result") is not None
        or terminals.get("capacity_projection") is not None
    ):
        raise ValueError("zero-suffix frozen contract differs")
    return value


@dataclass(frozen=True, slots=True)
class ZeroSuffixStructuralContract:
    original_sha256: str
    original_bytes: int
    repaired_sha256: str
    repaired_bytes: int
    header: tuple[object, ...]
    section_table_end: int
    program_table_end: int
    complete_program_headers: tuple[tuple[int, ...], ...]
    final_first_seven: tuple[int, ...]
    final_alignment_low_seven: bytes
    repaired_final_program_header: tuple[int, ...]
    original_tail_32: bytes
    repaired_tail_32: bytes


@dataclass(frozen=True, slots=True)
class ReconstructionEvidence:
    repaired: bytes
    header: Mapping[str, object]
    program_headers: tuple[tuple[int, ...], ...]
    section_table_sha256: str
    section_header_count: int
    section_name_table: tuple[int, ...]


def frozen_structural_contract(
    config: Mapping[str, object] | None = None,
) -> ZeroSuffixStructuralContract:
    value = load_preregistered_config() if config is None else config
    parent = value.get("parent_identity")
    original = value.get("original_elf_contract")
    reconstruction = value.get("reconstruction_contract")
    if not all(isinstance(item, Mapping) for item in (parent, original, reconstruction)):
        raise ValueError("zero-suffix structural config blocks differ")
    assert isinstance(parent, Mapping)
    assert isinstance(original, Mapping)
    assert isinstance(reconstruction, Mapping)
    ident = bytes.fromhex(str(original["ident_hex"]))
    header = (
        ident,
        int(original["e_type"]),
        int(original["e_machine"]),
        int(original["e_version"]),
        int(original["e_entry"]),
        int(original["e_phoff"]),
        int(original["e_shoff"]),
        int(original["e_flags"]),
        int(original["e_ehsize"]),
        int(original["e_phentsize"]),
        int(original["e_phnum"]),
        int(original["e_shentsize"]),
        int(original["e_shnum"]),
        int(original["e_shstrndx"]),
    )
    return ZeroSuffixStructuralContract(
        original_sha256=str(parent["original_payload_sha256"]),
        original_bytes=int(parent["original_payload_bytes"]),
        repaired_sha256=str(parent["repaired_payload_sha256"]),
        repaired_bytes=int(parent["repaired_payload_bytes"]),
        header=header,
        section_table_end=int(original["section_table_end"]),
        program_table_end=int(original["program_table_declared_end"]),
        complete_program_headers=tuple(
            tuple(int(item) for item in row)
            for row in original["complete_program_headers_in_order"]
        ),
        final_first_seven=tuple(
            int(item)
            for item in original["final_partial_program_header_first_seven_fields"]
        ),
        final_alignment_low_seven=bytes.fromhex(
            str(original["final_partial_p_align_low_seven_bytes_hex"])
        ),
        repaired_final_program_header=tuple(
            int(item) for item in reconstruction["repaired_final_program_header"]
        ),
        original_tail_32=bytes.fromhex(str(original["original_tail_32_hex"])),
        repaired_tail_32=bytes.fromhex(str(reconstruction["repaired_tail_32_hex"])),
    )


def _header_mapping(header: tuple[object, ...]) -> dict[str, object]:
    names = (
        "ident_hex",
        "e_type",
        "e_machine",
        "e_version",
        "e_entry",
        "e_phoff",
        "e_shoff",
        "e_flags",
        "e_ehsize",
        "e_phentsize",
        "e_phnum",
        "e_shentsize",
        "e_shnum",
        "e_shstrndx",
    )
    values = (header[0].hex(), *header[1:])
    return dict(zip(names, values, strict=True))


def _bounded_add(offset: int, size: int, limit: int, *, label: str) -> int:
    if min(offset, size, limit) < 0 or offset > limit or size > limit - offset:
        raise StructuralRejection(f"{label} is outside repaired payload")
    return offset + size


def reconstruct_exact_one_zero(
    original: bytes,
    contract: ZeroSuffixStructuralContract,
) -> ReconstructionEvidence:
    """Append the sole permitted zero after proving every structural predicate."""

    if not isinstance(original, bytes) or not isinstance(
        contract, ZeroSuffixStructuralContract
    ):
        raise TypeError("zero-suffix reconstruction inputs differ")
    if (
        len(original) != contract.original_bytes
        or sha256(original).hexdigest() != contract.original_sha256
        or contract.repaired_bytes != contract.original_bytes + 1
        or contract.program_table_end != contract.repaired_bytes
        or contract.section_table_end != int(contract.header[5])
        or len(contract.header) != 14
        or len(original) < _ELF_HEADER.size
    ):
        raise StructuralRejection("original payload identity or table arithmetic differs")
    header = _ELF_HEADER.unpack_from(original, 0)
    if header != contract.header:
        raise StructuralRejection("ELF header differs")
    (
        ident,
        _e_type,
        _e_machine,
        _e_version,
        _e_entry,
        e_phoff,
        e_shoff,
        _e_flags,
        e_ehsize,
        e_phentsize,
        e_phnum,
        e_shentsize,
        e_shnum,
        e_shstrndx,
    ) = header
    if (
        not ident.startswith(b"\x7fELF\x02\x01")
        or e_ehsize != _ELF_HEADER.size
        or e_phentsize != _PROGRAM_HEADER.size
        or e_shentsize != _SECTION_HEADER.size
        or e_phnum != len(contract.complete_program_headers) + 1
        or e_shnum <= 0
        or not 0 <= e_shstrndx < e_shnum
        or e_shoff + e_shentsize * e_shnum != contract.section_table_end
        or e_phoff + e_phentsize * e_phnum != contract.program_table_end
        or len(original) != contract.program_table_end - 1
    ):
        raise StructuralRejection("ELF table geometry differs")
    complete_rows = tuple(
        _PROGRAM_HEADER.unpack_from(original, e_phoff + index * e_phentsize)
        for index in range(e_phnum - 1)
    )
    if complete_rows != contract.complete_program_headers:
        raise StructuralRejection("complete program headers differ")
    final_offset = e_phoff + (e_phnum - 1) * e_phentsize
    final_partial = original[final_offset:]
    if (
        len(final_partial) != e_phentsize - 1
        or _PROGRAM_HEADER_FIRST_SEVEN.unpack_from(final_partial, 0)
        != contract.final_first_seven
        or final_partial[_PROGRAM_HEADER_FIRST_SEVEN.size :]
        != contract.final_alignment_low_seven
        or original[-32:] != contract.original_tail_32
    ):
        raise StructuralRejection("final partial program header differs")

    repaired = original + b"\x00"
    if (
        len(repaired) != contract.repaired_bytes
        or repaired[:-1] != original
        or repaired[-1:] != b"\x00"
        or sha256(repaired).hexdigest() != contract.repaired_sha256
        or repaired[-32:] != contract.repaired_tail_32
    ):
        raise StructuralRejection("sole repaired payload identity differs")
    program_headers = tuple(
        _PROGRAM_HEADER.unpack_from(repaired, e_phoff + index * e_phentsize)
        for index in range(e_phnum)
    )
    if (
        program_headers[:-1] != contract.complete_program_headers
        or program_headers[-1] != contract.repaired_final_program_header
    ):
        raise StructuralRejection("repaired program headers differ")
    for index, row in enumerate(program_headers):
        _p_type, _p_flags, p_offset, _p_vaddr, _p_paddr, p_filesz, p_memsz, p_align = row
        _bounded_add(p_offset, p_filesz, len(repaired), label=f"program {index}")
        if p_memsz < p_filesz:
            raise StructuralRejection(f"program {index} memory size is smaller")
        if p_align not in {0, 1} and p_align & (p_align - 1):
            raise StructuralRejection(f"program {index} alignment is not a power of two")

    section_table_size = e_shentsize * e_shnum
    section_table_end = _bounded_add(
        e_shoff, section_table_size, len(repaired), label="section table"
    )
    if section_table_end != contract.section_table_end:
        raise StructuralRejection("section table end differs")
    section_bytes = repaired[e_shoff:section_table_end]
    sections = tuple(
        _SECTION_HEADER.unpack_from(section_bytes, index * e_shentsize)
        for index in range(e_shnum)
    )
    for index, row in enumerate(sections):
        _name, section_type, _flags, _address, offset, size, *_rest = row
        if section_type != _SHT_NOBITS:
            _bounded_add(offset, size, len(repaired), label=f"section {index}")
    name_table = sections[e_shstrndx]
    if name_table[1] == _SHT_NOBITS:
        raise StructuralRejection("section-name table is not file-backed")
    _bounded_add(name_table[4], name_table[5], len(repaired), label="section-name table")
    return ReconstructionEvidence(
        repaired=repaired,
        header=_header_mapping(header),
        program_headers=program_headers,
        section_table_sha256=sha256(section_bytes).hexdigest(),
        section_header_count=len(sections),
        section_name_table=tuple(int(item) for item in name_table),
    )


def _encode_bounded_binary(
    raw: bytes, *, maximum_bytes: int, semantic_label: str
) -> dict[str, object]:
    if not isinstance(raw, bytes):
        raise TypeError("binary evidence must be immutable bytes")
    if (
        isinstance(maximum_bytes, bool)
        or not isinstance(maximum_bytes, int)
        or maximum_bytes <= 0
        or not isinstance(semantic_label, str)
        or not semantic_label
    ):
        raise TypeError("binary evidence semantic bound differs")
    if len(raw) > maximum_bytes:
        raise ValueError(f"{semantic_label} exceeds its frozen cap")
    return {
        "encoding": "base64_standard",
        "byte_count": len(raw),
        "sha256": sha256(raw).hexdigest(),
        "base64": base64.b64encode(raw).decode("ascii"),
    }


def encode_payload(raw: bytes) -> dict[str, object]:
    return _encode_bounded_binary(
        raw,
        maximum_bytes=MAXIMUM_PAYLOAD_BYTES,
        semantic_label="repaired payload",
    )


def encode_stream(raw: bytes) -> dict[str, object]:
    return _encode_bounded_binary(
        raw,
        maximum_bytes=MAXIMUM_STREAM_BYTES,
        semantic_label="external command stream",
    )


def parse_cuobjdump_resource_usage(raw: bytes) -> dict[str, dict[str, int]]:
    """Independently implement ADR-0407's complete REG/STACK/LOCAL grammar."""

    if not isinstance(raw, bytes):
        raise TypeError("cuobjdump resource stdout must be bytes")
    try:
        output = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("cuobjdump resource stdout is not strict ASCII") from error
    rows: dict[str, dict[str, int]] = {}
    current: str | None = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        match = re.fullmatch(r"Function\s+([^:]+):", line)
        if match:
            current = match.group(1)
            if current in rows:
                raise ValueError("cuobjdump resource output repeats a function")
            rows[current] = {}
            continue
        if current is None or not line:
            continue
        for label, text in re.findall(r"([A-Z]+(?:\[\d+\])?):(\d+)", line):
            if label in rows[current]:
                raise ValueError("cuobjdump resource output repeats a field")
            rows[current][label] = int(text)
    for name in DIRECT_KERNEL_NAMES:
        if name not in rows or not {"REG", "STACK", "LOCAL"}.issubset(rows[name]):
            raise ValueError("cuobjdump direct resource row is incomplete")
    return {
        name: {field: rows[name][field] for field in ("REG", "STACK", "LOCAL")}
        for name in DIRECT_KERNEL_NAMES
    }


@dataclass(frozen=True, slots=True)
class CommandCapture:
    status: str
    return_code: int | None
    stdout: bytes
    stderr: bytes
    elapsed_ns: int

    def __post_init__(self) -> None:
        if self.status not in {"completed", "timeout", "output_limit"}:
            raise ValueError("zero-suffix command status differs")
        if self.return_code is not None and (
            isinstance(self.return_code, bool) or not isinstance(self.return_code, int)
        ):
            raise TypeError("zero-suffix return code differs")
        if not isinstance(self.stdout, bytes) or not isinstance(self.stderr, bytes):
            raise TypeError("zero-suffix command streams differ")
        if len(self.stdout) > MAXIMUM_STREAM_BYTES or len(self.stderr) > MAXIMUM_STREAM_BYTES:
            raise ValueError("zero-suffix command stream exceeds cap")
        if (
            isinstance(self.elapsed_ns, bool)
            or not isinstance(self.elapsed_ns, int)
            or self.elapsed_ns < 0
        ):
            raise TypeError("zero-suffix elapsed time differs")


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
    if (
        not isinstance(argv, Sequence)
        or isinstance(argv, (str, bytes, bytearray))
        or not argv
        or any(not isinstance(item, str) or not item for item in argv)
    ):
        raise TypeError("zero-suffix argv must be a nonempty string sequence")
    if (
        isinstance(wall_limit_ns, bool)
        or not isinstance(wall_limit_ns, int)
        or wall_limit_ns <= 0
        or isinstance(stream_limit, bool)
        or not isinstance(stream_limit, int)
        or stream_limit <= 0
    ):
        raise ValueError("zero-suffix command bounds differ")
    creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0)) if os.name == "nt" else 0
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
        raise RuntimeError("zero-suffix command pipes are absent")
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
                    room = max(0, stream_limit - len(buffers[name]))
                    buffers[name].extend(chunk[:room])
                    if len(chunk) > room:
                        exceeded.set()
        finally:
            pipe.close()

    threads = tuple(
        threading.Thread(target=drain, args=(name, pipe), daemon=True)
        for name, pipe in (("stdout", process.stdout), ("stderr", process.stderr))
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
            raise RuntimeError("zero-suffix command drain did not terminate")
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
    row: Mapping[str, object], *, tools: Mapping[str, Path], payload_path: Path
) -> list[str]:
    tool = row.get("tool")
    arguments = row.get("arguments")
    if not isinstance(tool, str) or tool not in tools:
        raise ValueError("zero-suffix candidate tool differs")
    if not isinstance(arguments, list) or any(not isinstance(item, str) for item in arguments):
        raise ValueError("zero-suffix candidate arguments differ")
    return [
        str(tools[tool]),
        *[
            str(payload_path) if item == "{exact_repaired_temporary_cubin}" else item
            for item in arguments
        ],
    ]


def _load_parent_payload() -> tuple[bytes, dict[str, dict[str, int]]]:
    from .legal_river_exact_cubin_inspector_diagnostic_result import (
        rebind_exact_cubin_diagnostic_file,
    )

    parent_path = _ROOT / PARENT_ARTIFACT_RELATIVE_PATH
    _raw_file_identity(
        parent_path, digest=PARENT_ARTIFACT_SHA256, byte_count=PARENT_ARTIFACT_BYTES
    )
    rebound = rebind_exact_cubin_diagnostic_file(parent_path)
    if (
        rebound.terminal != "capture_complete"
        or rebound.cubin is None
        or rebound.driver_rows is None
        or rebound.cubin.sha256 != ORIGINAL_PAYLOAD_SHA256
        or rebound.cubin.byte_count != ORIGINAL_PAYLOAD_BYTES
        or dict(rebound.driver_rows) != ORIGINAL_DIRECT_DRIVER_ROWS
    ):
        raise ValueError("retained exact-cubin parent rebinding differs")
    return rebound.cubin.raw, {
        name: dict(row) for name, row in rebound.driver_rows.items()
    }


def _module_capture(repaired: bytes) -> dict[str, object]:
    # Deliberately local: importing this module remains device-free.
    import cupy as cp

    module = cp.cuda.function.Module()
    module.load(repaired)
    kernels = {name: module.get_function(name) for name in ALL_KERNEL_NAMES}
    attributes = {
        "local_size_bytes": cp.cuda.driver.CU_FUNC_ATTRIBUTE_LOCAL_SIZE_BYTES,
        "registers": cp.cuda.driver.CU_FUNC_ATTRIBUTE_NUM_REGS,
        "shared_size_bytes": cp.cuda.driver.CU_FUNC_ATTRIBUTE_SHARED_SIZE_BYTES,
        "maximum_threads_per_block": cp.cuda.driver.CU_FUNC_ATTRIBUTE_MAX_THREADS_PER_BLOCK,
    }
    rows = {
        name: {
            label: int(cp.cuda.driver.funcGetAttribute(attribute, kernels[name].ptr))
            for label, attribute in attributes.items()
        }
        for name in DIRECT_KERNEL_NAMES
    }
    return {
        "schema_version": "legal-river-zero-suffix-module-capture-v1",
        "repaired_payload_sha256": sha256(repaired).hexdigest(),
        "repaired_payload_bytes": len(repaired),
        "kernel_names": list(kernels),
        "direct_driver_rows": rows,
        "kernel_launch_count": 0,
    }


def _terminal(
    name: str,
    reason: str,
    *,
    candidate_count: int,
    qualified: str | None = None,
    resource_rows: Mapping[str, Mapping[str, int]] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "legal-river-zero-suffix-terminal-evidence-v1",
        "terminal": name,
        "passed": name == "suffix_reconstruction_pass",
        "reason": reason[:4096],
        "candidate_events_retained": candidate_count,
        "qualified_resource_instrument": qualified,
        "resource_rows": (
            {name: dict(row) for name, row in resource_rows.items()}
            if resource_rows is not None
            else None
        ),
        "resource_gate_result": None,
        "calibration_result": None,
        "capacity_projection": None,
    }


EmitAndWait = Callable[[str, Mapping[str, object]], None]


def run_real_diagnostic(emit_and_wait: EmitAndWait) -> dict[str, object]:
    if not callable(emit_and_wait):
        raise TypeError("zero-suffix emitter must be callable")
    started = perf_counter_ns()
    config = load_preregistered_config()
    if (_ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH).exists():
        raise RuntimeError("reserved actual result is present")
    _raw_file_identity(
        _ROOT / PARENT_SELECTION_RELATIVE_PATH,
        digest=PARENT_SELECTION_SHA256,
        byte_count=PARENT_SELECTION_BYTES,
    )
    try:
        original, original_driver_rows = _load_parent_payload()
        evidence = reconstruct_exact_one_zero(original, frozen_structural_contract(config))
    except StructuralRejection as error:
        return _terminal("structural_rejection", str(error), candidate_count=0)
    repaired = evidence.repaired
    emit_and_wait(
        "repaired_payload",
        {
            "schema_version": "legal-river-zero-suffix-repaired-payload-v1",
            "original_payload_sha256": sha256(original).hexdigest(),
            "original_payload_bytes": len(original),
            "repaired_payload": encode_payload(repaired),
            "elf_header": dict(evidence.header),
            "program_headers": [list(row) for row in evidence.program_headers],
            "section_table_sha256": evidence.section_table_sha256,
            "section_header_count": evidence.section_header_count,
            "section_name_table": list(evidence.section_name_table),
        },
    )

    temporary_path: Path | None = None
    candidate_events: list[tuple[Mapping[str, object], CommandCapture]] = []
    module_event: Mapping[str, object] | None = None
    module_failure: str | None = None
    early_terminal: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".cubin", delete=False) as handle:
            handle.write(repaired)
            handle.flush()
            os.fsync(handle.fileno())
            temporary_path = Path(handle.name)
        temporary_raw = temporary_path.read_bytes()
        if temporary_raw != repaired:
            raise RuntimeError("temporary repaired payload differs")
        emit_and_wait(
            "temporary_payload_ready",
            {
                "schema_version": "legal-river-zero-suffix-temporary-payload-v1",
                "temporary_path": str(temporary_path),
                "readback_sha256": sha256(temporary_raw).hexdigest(),
                "readback_bytes": len(temporary_raw),
                "matches_durable_repaired_payload": True,
            },
        )
        tools = _tool_paths()
        candidates = config["candidate_commands_in_order"]
        assert isinstance(candidates, list)
        for index, row_value in enumerate(candidates):
            if not isinstance(row_value, Mapping):
                raise TypeError("zero-suffix candidate row differs")
            argv = _candidate_argv(row_value, tools=tools, payload_path=temporary_path)
            capture = run_bounded_binary_command(argv)
            event = {
                "schema_version": "legal-river-zero-suffix-candidate-command-v1",
                "candidate_index": index,
                "candidate_id": row_value["candidate_id"],
                "uses_repaired_payload": row_value["uses_repaired_payload"],
                "required_for_suffix_pass": row_value["required_for_suffix_pass"],
                "argv": argv,
                "status": capture.status,
                "return_code": capture.return_code,
                "stdout": encode_stream(capture.stdout),
                "stderr": encode_stream(capture.stderr),
                "elapsed_ns": capture.elapsed_ns,
            }
            emit_and_wait("candidate_command", event)
            candidate_events.append((row_value, capture))
            if capture.status != "completed":
                early_terminal = f"candidate_{capture.status}_rejection"
                break
            if perf_counter_ns() - started > LABORATORY_WALL_NS:
                early_terminal = "laboratory_wall_rejection"
                break
        if early_terminal is None:
            try:
                module_event = _module_capture(repaired)
                emit_and_wait("module_capture", module_event)
            except BaseException as error:  # noqa: BLE001 - module failure is evidence
                module_failure = f"{type(error).__name__}: {(str(error) or 'no message')[:4096]}"
                emit_and_wait(
                    "module_failure",
                    {
                        "schema_version": "legal-river-zero-suffix-module-failure-v1",
                        "repaired_payload_sha256": sha256(repaired).hexdigest(),
                        "repaired_payload_bytes": len(repaired),
                        "reason": module_failure,
                        "kernel_launch_count": 0,
                    },
                )
            if perf_counter_ns() - started > LABORATORY_WALL_NS:
                early_terminal = "laboratory_wall_rejection"
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        emit_and_wait(
            "cleanup",
            {
                "schema_version": "legal-river-zero-suffix-cleanup-v1",
                "temporary_payload_removed": temporary_path is not None
                and not temporary_path.exists(),
                "candidate_events_retained": len(candidate_events),
                "module_event_retained": module_event is not None or module_failure is not None,
            },
        )

    if early_terminal is not None:
        return _terminal(
            early_terminal,
            "bounded external command or laboratory wall rejected",
            candidate_count=len(candidate_events),
        )
    if module_failure is not None or module_event is None:
        return _terminal(
            "module_load_rejection",
            module_failure or "module capture is absent",
            candidate_count=len(candidate_events),
        )
    observed_driver = module_event.get("direct_driver_rows")
    if observed_driver != original_driver_rows:
        return _terminal(
            "driver_row_rejection",
            "repaired module direct-driver rows differ from retained original",
            candidate_count=len(candidate_events),
        )
    if len(candidate_events) != 6:
        return _terminal(
            "diagnostic_failure",
            "candidate inventory is incomplete",
            candidate_count=len(candidate_events),
        )
    by_id = {str(row["candidate_id"]): capture for row, capture in candidate_events}
    try:
        resource_rows = parse_cuobjdump_resource_usage(
            by_id["cuobjdump_resource_usage"].stdout
        )
    except (TypeError, ValueError):
        resource_rows = None
    required_tools_pass = (
        by_id["cuobjdump_version"].return_code == 0
        and by_id["cuobjdump_version"].stdout == _CUOBJDUMP_VERSION_BYTES
        and by_id["cuobjdump_resource_usage"].return_code == 0
        and by_id["cuobjdump_elf"].return_code == 0
        and resource_rows is not None
    )
    if not required_tools_pass:
        return _terminal(
            "tool_rejection",
            "required CUDA 13.3 cuobjdump identity/resource/ELF conjunct failed",
            candidate_count=len(candidate_events),
            resource_rows=resource_rows,
        )
    return _terminal(
        "suffix_reconstruction_pass",
        "exact zero suffix passed structure, same-byte tools, module, and driver seams",
        candidate_count=len(candidate_events),
        qualified=QUALIFIED_INSTRUMENT,
        resource_rows=resource_rows,
    )


__all__ = [
    "ALL_KERNEL_NAMES",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "CommandCapture",
    "DIRECT_KERNEL_NAMES",
    "LABORATORY_WALL_NS",
    "MAXIMUM_PAYLOAD_BYTES",
    "MAXIMUM_STREAM_BYTES",
    "ORIGINAL_DIRECT_DRIVER_ROWS",
    "ORIGINAL_PAYLOAD_BYTES",
    "ORIGINAL_PAYLOAD_SHA256",
    "PER_COMMAND_WALL_NS",
    "QUALIFIED_INSTRUMENT",
    "REPAIRED_PAYLOAD_BYTES",
    "REPAIRED_PAYLOAD_SHA256",
    "ReconstructionEvidence",
    "StructuralRejection",
    "ZeroSuffixStructuralContract",
    "canonical_lf_sha256",
    "encode_payload",
    "encode_stream",
    "frozen_structural_contract",
    "load_preregistered_config",
    "parse_cuobjdump_resource_usage",
    "reconstruct_exact_one_zero",
    "run_bounded_binary_command",
    "run_real_diagnostic",
]
