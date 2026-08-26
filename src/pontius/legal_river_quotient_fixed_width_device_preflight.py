"""ADR-0439 fixed-width compiled-device preflight.

Importing this module is deliberately standard-library, process, compiler,
device, and result free.  CUDA and the retained CPU authority are loaded only
inside the explicit campaign entry point.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from threading import Event, Thread
from time import perf_counter_ns
from typing import Any, Callable


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v1.json"
)
CONFIG_SHA256 = "84da7e82ef07620b0d7869a1e52da6a80f5f3815c0e4dc7007068ce6664ed6af"
PREREGISTRATION_ADR_RELATIVE_PATH = (
    "docs/decisions/ADR-0439-preregister-the-fixed-width-compiled-device-preflight.md"
)
PREREGISTRATION_ADR_SHA256 = (
    "861e10e5ab9d924554ba588d7f69735b39da343547c53329033837de596c1f71"
)
PREREGISTRATION_COMMIT = "096d4ae0a78fa9de3c3c3838c8a64997b716816d"
FROZEN_PARENT_COMMIT = "41a6b8222b5d81b8d7457ea91a9aa2fc212edb6e"
CORRECTION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-fixed-width-device-preflight-v2-topology.json"
)
CORRECTION_CONFIG_SHA256 = (
    "6ebca361aed6c6cfcd11fd2df0b6041c1f676a7e6b07af9739bcd84e64b38e41"
)
CORRECTION_ADR_RELATIVE_PATH = (
    "docs/decisions/"
    "ADR-0440-correct-the-batched-device-preflight-phase-topology-before-source-seal.md"
)
CORRECTION_ADR_SHA256 = (
    "9c8a93ff89e67ce7a83e9d276614464ecbdce3cdbddab65bc9e7f87065fb7f46"
)
CORRECTION_COMMIT = "e4704d9011ad4af2f7d610bfa56053d046864d96"
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_fixed_width_device_preflight_v1.jsonl"
)
RESULT_PATH = _ROOT / RESULT_RELATIVE_PATH

NVCC_PATH = Path(
    r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvcc.exe"
)
CUOBJDUMP_PATH = Path(
    r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\cuobjdump.exe"
)
NVDISASM_PATH = Path(
    r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvdisasm.exe"
)
NVCC_OPTIONS = (
    "--cubin",
    "--gpu-architecture=sm_120",
    "--std=c++17",
    "--ftz=false",
    "--prec-div=true",
    "--prec-sqrt=true",
    "--fmad=false",
    "--ptxas-options=-v",
)

KERNEL_NAMES = (
    "positional_encode_aggregate",
    "positional_forward_level",
    "positional_forward_selective",
    "positional_forward_stream",
    "positional_adjoint_level",
    "positional_adjoint_selective",
    "positional_adjoint_stream",
    "positional_contract",
    "rrns_encode_aggregate",
    "rrns_forward_level",
    "rrns_forward_selective",
    "rrns_forward_stream",
    "rrns_adjoint_level",
    "rrns_adjoint_selective",
    "rrns_adjoint_stream",
    "rrns_contract",
)

POSITIONAL = "positional"
RESIDENT_RRNS = "resident_nine_RRNS"
BATCHED_RRNS = "batched_five_then_four_RRNS"
ARMS = (POSITIONAL, RESIDENT_RRNS, BATCHED_RRNS)
POPULATIONS = ("complete_10", "signed_12")

REGISTER_CEILING = 255
BACKING_CEILING_BYTES = 4096
SPILL_BYTE_CEILING = 0
BLOCK_THREADS = 128
DEVICE_RESERVE_BYTES = 2_000_000_000
EXPECTED_DEVICE_TOTAL_BYTES = 17_094_475_776

PUBLIC_WALL_NS = 270_000_000_000
LABORATORY_WALL_NS = 240_000_000_000
COMPILE_RESOURCE_WALL_NS = 60_000_000_000
OUTSIDE_LABORATORY_WALL_NS = 30_000_000_000
PER_POPULATION_ARM_WALL_NS = 30_000_000_000
PER_COMMAND_WALL_NS = 30_000_000_000

MAXIMUM_CUBIN_BYTES = 8_388_608
MAXIMUM_COMPILER_STREAM_BYTES = 1_048_576
MAXIMUM_EXTERNAL_STREAM_BYTES = 8_388_608

SINGLE_PASS_PHASE_NAMES = (
    "candidate_state_validation_and_input_digest",
    "device_allocation_and_input_transfer",
    "family_admission_pair_encoding_and_label_aggregation",
    "forward_recurrence",
    "forward_selective_queries",
    "forward_streamed_global_scan_and_scalar_contract",
    "adjoint_recurrence",
    "adjoint_selective_queries",
    "adjoint_streamed_global_scan_and_scalar_contract",
    "scalar_output_transfer_reconstruction_divisibility_fault_check_and_rounding",
    "verification_output_transfer_and_exact_differential",
    "candidate_cleanup",
)

BATCHED_PHASE_NAMES = (
    "candidate_state_validation_and_input_digest",
    "device_allocation_and_input_transfer",
    "first_batch_family_admission_pair_encoding_and_label_aggregation",
    "first_batch_forward_recurrence",
    "first_batch_forward_selective_queries",
    "first_batch_forward_streamed_global_scan_and_scalar_contract",
    "first_batch_adjoint_recurrence",
    "first_batch_adjoint_selective_queries",
    "first_batch_adjoint_streamed_global_scan_and_scalar_contract",
    "first_batch_output_drain_and_workspace_reuse_boundary",
    "second_batch_family_admission_pair_encoding_and_label_aggregation",
    "second_batch_forward_recurrence",
    "second_batch_forward_selective_queries",
    "second_batch_forward_streamed_global_scan_and_scalar_contract",
    "second_batch_adjoint_recurrence",
    "second_batch_adjoint_selective_queries",
    "second_batch_adjoint_streamed_global_scan_and_scalar_contract",
    "scalar_output_transfer_reconstruction_divisibility_fault_check_and_rounding",
    "verification_output_transfer_and_exact_differential",
    "candidate_cleanup",
)

# Compatibility name for generic single-pass controls.  Arm-aware code must use
# ``phase_names_for_arm`` rather than borrowing this tuple for batched RRNS.
PHASE_NAMES = SINGLE_PASS_PHASE_NAMES

GLOBAL_PHASE_NAMES = (
    "bootstrap_handshake",
    "tool_identity_and_cuda_source_materialization",
    "compile",
    "durable_cubin_capture",
    "external_resource_inspection",
    "module_load_and_driver_attributes",
    "complete_10_host_authority_and_fixture",
    "complete_12_host_authority_and_fixture",
    "final_device_and_temporary_cleanup",
)

_DIGEST = re.compile(r"^[0-9a-f]{64}$")


def normalize_crlf_bytes(data: bytes) -> bytes:
    """Production CRLF-only normalizer; literal token is an armed seal target."""

    if type(data) is not bytes:
        raise TypeError("canonical input must be immutable bytes")
    return data.replace(b"\r\n", b"\n")


def independent_normalize_crlf_bytes(data: bytes) -> bytes:
    """Independently normalize CRLF with a forward byte state machine."""

    if type(data) is not bytes:
        raise TypeError("independent canonical input must be immutable bytes")
    output = bytearray()
    index = 0
    while index < len(data):
        current = data[index]
        if current == 13 and index + 1 < len(data) and data[index + 1] == 10:
            output.append(10)
            index += 2
        else:
            output.append(current)
            index += 1
    return bytes(output)


def canonical_lf_bytes(path: Path) -> bytes:
    """Normalize only physical CRLF bytes; never rewrite escape text."""

    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"fixed-width device-preflight path is absent: {path}")
    raw = path.read_bytes()
    production = normalize_crlf_bytes(raw)
    independent = independent_normalize_crlf_bytes(raw)
    if production != independent:
        raise ValueError("independent canonical-LF normalizers differ")
    return production


def canonical_lf_sha256(path: Path) -> str:
    return sha256(canonical_lf_bytes(path)).hexdigest()


@dataclass(frozen=True, slots=True)
class ArmedMutationReceipt:
    relative_path: str
    occurrence_count: int
    canonical_lf_sha256: str
    forbidden_mutation_sha256: str


def literal_escape_mutation_receipt(
    path: Path,
    *,
    expected_occurrences: int,
    require_armed: bool,
) -> ArmedMutationReceipt:
    """Count the raw escape trigger before evaluating its forbidden rewrite."""

    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"literal-mutation target is absent: {path}")
    count_expected = _require_plain_int(
        expected_occurrences, label="literal-mutation occurrence count", minimum=0
    )
    raw = path.read_bytes()
    token = bytes((92, 114, 92, 110))
    replacement = bytes((92, 110))
    count = raw.count(token)
    if count != count_expected:
        raise ValueError("literal-mutation occurrence count differs")
    if require_armed and count == 0:
        raise ValueError("unarmed_literal_escape_mutation")
    production = normalize_crlf_bytes(raw)
    independent = independent_normalize_crlf_bytes(raw)
    if production != independent:
        raise ValueError("independent canonical-LF normalizers differ")
    mutated_raw = raw.replace(token, replacement)
    mutated = normalize_crlf_bytes(mutated_raw)
    canonical_digest = sha256(production).hexdigest()
    mutation_digest = sha256(mutated).hexdigest()
    if count:
        if mutated_raw == raw or mutated == production:
            raise ValueError("armed literal mutation did not change bytes")
        if mutation_digest == canonical_digest:
            raise ValueError("armed literal mutation did not change digest")
    elif mutated_raw != raw or mutation_digest != canonical_digest:
        raise ValueError("token-free literal mutation was not the identity")
    try:
        relative = path.relative_to(_ROOT).as_posix()
    except ValueError:
        relative = str(path)
    return ArmedMutationReceipt(
        relative_path=relative,
        occurrence_count=count,
        canonical_lf_sha256=canonical_digest,
        forbidden_mutation_sha256=mutation_digest,
    )


def _require_plain_int(
    value: object, *, label: str, minimum: int | None = None
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    return value


def _require_digest(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def load_preregistered_config() -> dict[str, object]:
    path = _ROOT / CONFIG_RELATIVE_PATH
    if canonical_lf_sha256(path) != CONFIG_SHA256:
        raise ValueError("fixed-width device-preflight config hash differs")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("fixed-width device-preflight config must be an object")
    return value


def load_correction_config() -> dict[str, object]:
    path = _ROOT / CORRECTION_CONFIG_RELATIVE_PATH
    if canonical_lf_sha256(path) != CORRECTION_CONFIG_SHA256:
        raise ValueError("fixed-width device-preflight correction hash differs")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("fixed-width device-preflight correction must be an object")
    if (
        value.get("schema_version")
        != "legal-river-quotient-fixed-width-device-preflight-topology-correction-v2"
        or tuple(value.get("single_pass_candidate_phases_in_order", ()))
        != SINGLE_PASS_PHASE_NAMES
        or tuple(value.get("batched_candidate_phases_in_order", ()))
        != BATCHED_PHASE_NAMES
    ):
        raise ValueError("fixed-width device-preflight correction contract differs")
    return value


def verify_preregistered_contract() -> dict[str, object]:
    config = load_preregistered_config()
    correction = load_correction_config()
    if (
        config.get("schema_version")
        != "legal-river-quotient-fixed-width-device-preflight-v1"
        or config.get("parent_commit") != FROZEN_PARENT_COMMIT
        or tuple(config.get("required_entry_kernels", ())) != KERNEL_NAMES
        or tuple(row.get("arm") for row in config.get("arms", ())) != ARMS
        or config.get("walls_ns", {}).get("public_process") != PUBLIC_WALL_NS
        or config.get("walls_ns", {}).get("laboratory") != LABORATORY_WALL_NS
    ):
        raise ValueError("fixed-width device-preflight frozen contract differs")
    if canonical_lf_sha256(_ROOT / PREREGISTRATION_ADR_RELATIVE_PATH) != (
        PREREGISTRATION_ADR_SHA256
    ):
        raise ValueError("fixed-width device-preflight preregistration ADR differs")
    if canonical_lf_sha256(_ROOT / CORRECTION_ADR_RELATIVE_PATH) != (
        CORRECTION_ADR_SHA256
    ):
        raise ValueError("fixed-width device-preflight correction ADR differs")
    parent_identity = correction.get("parent_identity")
    if not isinstance(parent_identity, dict) or (
        parent_identity.get("v1_config_canonical_lf_sha256") != CONFIG_SHA256
        or parent_identity.get("adr0439_canonical_lf_sha256")
        != PREREGISTRATION_ADR_SHA256
        or parent_identity.get("preregistration_commit") != PREREGISTRATION_COMMIT
    ):
        raise ValueError("fixed-width device-preflight correction parent differs")
    parents = config.get("expected_parents")
    if not isinstance(parents, dict):
        raise TypeError("fixed-width device-preflight parents must be an object")
    for label, raw in parents.items():
        if not isinstance(raw, dict) or not isinstance(raw.get("relative_path"), str):
            raise TypeError(f"fixed-width device-preflight parent {label} differs")
        path = _ROOT / raw["relative_path"]
        if "canonical_lf_sha256" in raw:
            actual = canonical_lf_sha256(path)
            expected = raw["canonical_lf_sha256"]
        else:
            actual = sha256(path.read_bytes()).hexdigest()
            expected = raw.get("raw_sha256")
        if actual != expected:
            raise ValueError(f"fixed-width device-preflight parent differs: {label}")
    prospective = config.get("prospective_paths")
    if not isinstance(prospective, dict):
        raise TypeError("fixed-width device-preflight prospective paths differ")
    if prospective.get("result") != RESULT_RELATIVE_PATH:
        raise ValueError("fixed-width device-preflight result identity differs")
    return config


def phase_names_for_arm(arm: str) -> tuple[str, ...]:
    if arm in {POSITIONAL, RESIDENT_RRNS}:
        return SINGLE_PASS_PHASE_NAMES
    if arm == BATCHED_RRNS:
        return BATCHED_PHASE_NAMES
    raise ValueError("unknown fixed-width device arm")


@dataclass(frozen=True, slots=True)
class BoundedCommand:
    argv: tuple[str, ...]
    return_code: int | None
    stdout: bytes
    stderr: bytes
    elapsed_ns: int
    status: str

    def __post_init__(self) -> None:
        if not self.argv or any(not isinstance(item, str) or not item for item in self.argv):
            raise ValueError("bounded command argv differs")
        if self.return_code is not None and (
            isinstance(self.return_code, bool) or not isinstance(self.return_code, int)
        ):
            raise TypeError("bounded command return code differs")
        if not isinstance(self.stdout, bytes) or not isinstance(self.stderr, bytes):
            raise TypeError("bounded command streams must be immutable")
        _require_plain_int(self.elapsed_ns, label="bounded command elapsed", minimum=0)
        if self.status not in {"completed", "timeout", "output_limit"}:
            raise ValueError("bounded command status differs")

    def evidence(self) -> dict[str, object]:
        return {
            "argv": list(self.argv),
            "return_code": self.return_code,
            "status": self.status,
            "elapsed_ns": self.elapsed_ns,
            "stdout_base64": base64.b64encode(self.stdout).decode("ascii"),
            "stdout_bytes": len(self.stdout),
            "stdout_sha256": sha256(self.stdout).hexdigest(),
            "stderr_base64": base64.b64encode(self.stderr).decode("ascii"),
            "stderr_bytes": len(self.stderr),
            "stderr_sha256": sha256(self.stderr).hexdigest(),
        }


def run_bounded_command(
    argv: Sequence[str],
    *,
    wall_ns: int,
    stdout_limit: int,
    stderr_limit: int,
    cwd: Path | None = None,
) -> BoundedCommand:
    """Run a bounded command without interpreting either raw stream."""

    command = tuple(argv)
    wall = _require_plain_int(wall_ns, label="command wall", minimum=1)
    out_limit = _require_plain_int(stdout_limit, label="stdout limit", minimum=1)
    err_limit = _require_plain_int(stderr_limit, label="stderr limit", minimum=1)
    started = perf_counter_ns()
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdout is not None and process.stderr is not None
    stdout_buffer = bytearray()
    stderr_buffer = bytearray()
    overflow = Event()

    def drain(stream: object, target: bytearray, limit: int) -> None:
        while True:
            block = stream.read(65_536)
            if not block:
                return
            remaining = limit + 1 - len(target)
            if remaining > 0:
                target.extend(block[:remaining])
            if len(target) > limit:
                overflow.set()
                if process.poll() is None:
                    process.kill()

    threads = (
        Thread(target=drain, args=(process.stdout, stdout_buffer, out_limit), daemon=True),
        Thread(target=drain, args=(process.stderr, stderr_buffer, err_limit), daemon=True),
    )
    for thread in threads:
        thread.start()
    try:
        process.wait(timeout=wall / 1_000_000_000)
        status = "completed"
        return_code: int | None = process.returncode
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        status = "timeout"
        return_code = None
    for thread in threads:
        thread.join()
    process.stdout.close()
    process.stderr.close()
    stdout = bytes(stdout_buffer)
    stderr = bytes(stderr_buffer)
    elapsed = perf_counter_ns() - started
    if overflow.is_set():
        status = "output_limit"
        return_code = None
    return BoundedCommand(
        argv=command,
        return_code=return_code,
        stdout=bytes(stdout),
        stderr=bytes(stderr),
        elapsed_ns=elapsed,
        status=status,
    )


@dataclass(frozen=True, slots=True)
class PtxasResource:
    kernel: str
    registers: int
    stack_frame_bytes: int
    spill_store_bytes: int
    spill_load_bytes: int


_PTXAS_FUNCTION = re.compile(
    r"(?:Compiling entry function|Function properties for)\s+'?([^'\s]+)'?"
)
_PTXAS_STACK = re.compile(
    r"(?P<stack>\d+) bytes stack frame,\s*"
    r"(?P<stores>\d+) bytes spill stores,\s*"
    r"(?P<loads>\d+) bytes spill loads"
)
_PTXAS_REGISTERS = re.compile(r"Used\s+(?P<registers>\d+)\s+registers\b")


def parse_ptxas_verbose(raw: bytes) -> dict[str, PtxasResource]:
    if not isinstance(raw, bytes):
        raise TypeError("ptxas log must be immutable bytes")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("ptxas log must be ASCII") from error
    current: str | None = None
    rows: dict[str, dict[str, int]] = {}
    for line in text.splitlines():
        found = _PTXAS_FUNCTION.search(line)
        if found is not None:
            name = found.group(1)
            if name in KERNEL_NAMES:
                current = name
                rows.setdefault(name, {})
            else:
                current = None
            continue
        if current is None:
            continue
        stack = _PTXAS_STACK.search(line)
        if stack is not None:
            row = rows[current]
            for key, group in (
                ("stack_frame_bytes", "stack"),
                ("spill_store_bytes", "stores"),
                ("spill_load_bytes", "loads"),
            ):
                if key in row:
                    raise ValueError(f"ptxas repeats {key} for {current}")
                row[key] = int(stack.group(group))
        registers = _PTXAS_REGISTERS.search(line)
        if registers is not None:
            row = rows[current]
            if "registers" in row:
                raise ValueError(f"ptxas repeats registers for {current}")
            row["registers"] = int(registers.group("registers"))
    expected_fields = {
        "registers",
        "stack_frame_bytes",
        "spill_store_bytes",
        "spill_load_bytes",
    }
    if set(rows) != set(KERNEL_NAMES):
        raise ValueError("ptxas log omits or adds an entry kernel")
    output: dict[str, PtxasResource] = {}
    for name in KERNEL_NAMES:
        row = rows[name]
        if set(row) != expected_fields:
            raise ValueError(f"ptxas resource row is incomplete: {name}")
        output[name] = PtxasResource(kernel=name, **row)
    return output


@dataclass(frozen=True, slots=True)
class CubinResource:
    kernel: str
    registers: int
    stack_bytes: int
    local_bytes: int
    shared_bytes: int


_CUBIN_FUNCTION = re.compile(r"^\s*Function\s+([^:]+):\s*$")
_CUBIN_FIELD = re.compile(r"\b(REG|STACK|LOCAL|SHARED):(\d+)\b")


def parse_cuobjdump_resource_usage(raw: bytes) -> dict[str, CubinResource]:
    if not isinstance(raw, bytes):
        raise TypeError("cuobjdump resource stream must be immutable bytes")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("cuobjdump resource stream must be ASCII") from error
    current: str | None = None
    rows: dict[str, dict[str, int]] = {}
    for line in text.splitlines():
        match = _CUBIN_FUNCTION.match(line)
        if match is not None:
            name = match.group(1).strip()
            current = name if name in KERNEL_NAMES else None
            if current is not None:
                if current in rows:
                    raise ValueError(f"cuobjdump repeats kernel {current}")
                rows[current] = {}
            continue
        if current is None:
            continue
        for key, value in _CUBIN_FIELD.findall(line):
            if key in rows[current]:
                raise ValueError(f"cuobjdump repeats {key} for {current}")
            rows[current][key] = int(value)
    if set(rows) != set(KERNEL_NAMES):
        raise ValueError("cuobjdump omits or adds an entry kernel")
    output: dict[str, CubinResource] = {}
    for name in KERNEL_NAMES:
        row = rows[name]
        if set(row) != {"REG", "STACK", "LOCAL", "SHARED"}:
            raise ValueError(f"cuobjdump resource row is incomplete: {name}")
        output[name] = CubinResource(
            kernel=name,
            registers=row["REG"],
            stack_bytes=row["STACK"],
            local_bytes=row["LOCAL"],
            shared_bytes=row["SHARED"],
        )
    return output


@dataclass(frozen=True, slots=True)
class SassLocalSites:
    kernel: str
    local_load_sites: int
    local_store_sites: int


_SASS_FUNCTION = re.compile(r"^\s*\.global\s+([^\s]+)\s*$")
_SASS_OPCODE = re.compile(r"\b(LDL|STL)(?:\.[A-Z0-9.]+)?\b")


def parse_nvdisasm_local_sites(raw: bytes) -> dict[str, SassLocalSites]:
    if not isinstance(raw, bytes):
        raise TypeError("nvdisasm stream must be immutable bytes")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("nvdisasm stream must be ASCII") from error
    current: str | None = None
    seen: set[str] = set()
    counts = {name: [0, 0] for name in KERNEL_NAMES}
    for line in text.splitlines():
        match = _SASS_FUNCTION.match(line)
        if match is not None:
            name = match.group(1).rstrip(":")
            current = name if name in counts else None
            if current is not None:
                if current in seen:
                    raise ValueError(f"nvdisasm repeats kernel {current}")
                seen.add(current)
            continue
        if current is None:
            continue
        for opcode in _SASS_OPCODE.findall(line):
            counts[current][0 if opcode == "LDL" else 1] += 1
    if seen != set(KERNEL_NAMES):
        raise ValueError("nvdisasm omits or adds an entry kernel")
    return {
        name: SassLocalSites(
            kernel=name,
            local_load_sites=counts[name][0],
            local_store_sites=counts[name][1],
        )
        for name in KERNEL_NAMES
    }


@dataclass(frozen=True, slots=True)
class DriverResource:
    kernel: str
    registers: int
    local_bytes: int
    shared_bytes: int
    maximum_threads_per_block: int


@dataclass(frozen=True, slots=True)
class EffectiveResource:
    kernel: str
    registers: int
    backing_bytes: int
    spill_store_bytes: int
    spill_load_bytes: int
    static_local_load_sites: int
    static_local_store_sites: int
    shared_bytes: int
    maximum_threads_per_block: int
    eligible: bool


def combine_resource_evidence(
    ptxas: Mapping[str, PtxasResource],
    cubin: Mapping[str, CubinResource],
    sass: Mapping[str, SassLocalSites],
    driver: Mapping[str, DriverResource],
    *,
    device_shared_limit_bytes: int,
) -> dict[str, EffectiveResource]:
    expected = set(KERNEL_NAMES)
    if any(set(rows) != expected for rows in (ptxas, cubin, sass, driver)):
        raise ValueError("resource instrument kernel domains differ")
    shared_limit = _require_plain_int(
        device_shared_limit_bytes,
        label="device shared-memory limit",
        minimum=0,
    )
    output: dict[str, EffectiveResource] = {}
    for name in KERNEL_NAMES:
        a, b, c, d = ptxas[name], cubin[name], sass[name], driver[name]
        if any(row.kernel != name for row in (a, b, c, d)):
            raise ValueError("resource row label differs from its key")
        registers = max(a.registers, b.registers, d.registers)
        backing = max(a.stack_frame_bytes, b.stack_bytes + b.local_bytes, d.local_bytes)
        eligible = (
            registers <= REGISTER_CEILING
            and backing <= BACKING_CEILING_BYTES
            and a.spill_store_bytes <= SPILL_BYTE_CEILING
            and a.spill_load_bytes <= SPILL_BYTE_CEILING
            and BLOCK_THREADS <= d.maximum_threads_per_block
            and max(b.shared_bytes, d.shared_bytes) <= shared_limit
        )
        output[name] = EffectiveResource(
            kernel=name,
            registers=registers,
            backing_bytes=backing,
            spill_store_bytes=a.spill_store_bytes,
            spill_load_bytes=a.spill_load_bytes,
            static_local_load_sites=c.local_load_sites,
            static_local_store_sites=c.local_store_sites,
            shared_bytes=max(b.shared_bytes, d.shared_bytes),
            maximum_threads_per_block=d.maximum_threads_per_block,
            eligible=eligible,
        )
    return output


@dataclass(frozen=True, slots=True)
class BufferLifetime:
    logical_name: str
    storage_identity: str
    byte_count: int
    birth_boundary: int
    death_boundary: int

    def __post_init__(self) -> None:
        if not self.logical_name or not self.storage_identity:
            raise ValueError("buffer names must be nonempty")
        _require_plain_int(self.byte_count, label="buffer bytes", minimum=1)
        birth = _require_plain_int(self.birth_boundary, label="buffer birth", minimum=0)
        death = _require_plain_int(self.death_boundary, label="buffer death", minimum=0)
        if birth >= death:
            raise ValueError("buffer lifetime must contain at least one phase")


@dataclass(frozen=True, slots=True)
class MemoryLiveness:
    boundary_live_bytes: tuple[int, ...]
    peak_live_bytes: int
    peak_boundary: int
    device_reserve_bytes: int
    device_total_bytes: int
    eligible: bool


def memory_liveness(
    buffers: Iterable[BufferLifetime],
    *,
    boundary_count: int,
    device_total_bytes: int = EXPECTED_DEVICE_TOTAL_BYTES,
    reserve_bytes: int = DEVICE_RESERVE_BYTES,
) -> MemoryLiveness:
    count = _require_plain_int(boundary_count, label="boundary count", minimum=2)
    total = _require_plain_int(device_total_bytes, label="device total", minimum=1)
    reserve = _require_plain_int(reserve_bytes, label="device reserve", minimum=0)
    rows = tuple(buffers)
    if not rows:
        raise ValueError("memory liveness requires buffers")
    by_storage: dict[str, list[BufferLifetime]] = {}
    logical_names: set[str] = set()
    for row in rows:
        if not isinstance(row, BufferLifetime):
            raise TypeError("memory liveness row must be typed")
        if row.logical_name in logical_names:
            raise ValueError("memory liveness repeats a logical buffer")
        logical_names.add(row.logical_name)
        if row.death_boundary > count:
            raise ValueError("buffer death exceeds the boundary domain")
        by_storage.setdefault(row.storage_identity, []).append(row)
    for identity, aliases in by_storage.items():
        ordered = sorted(aliases, key=lambda item: (item.birth_boundary, item.death_boundary))
        for left, right in zip(ordered, ordered[1:]):
            if right.birth_boundary < left.death_boundary:
                raise ValueError(f"storage aliases overlap: {identity}")
    live = []
    for boundary in range(count):
        active_by_storage: dict[str, int] = {}
        for row in rows:
            if row.birth_boundary <= boundary < row.death_boundary:
                if row.storage_identity in active_by_storage:
                    raise AssertionError("overlapping alias escaped validation")
                active_by_storage[row.storage_identity] = row.byte_count
        live.append(sum(active_by_storage.values()))
    peak = max(live)
    peak_boundary = live.index(peak)
    return MemoryLiveness(
        boundary_live_bytes=tuple(live),
        peak_live_bytes=peak,
        peak_boundary=peak_boundary,
        device_reserve_bytes=reserve,
        device_total_bytes=total,
        eligible=peak + reserve <= total,
    )


@dataclass(frozen=True, slots=True)
class PhaseRow:
    name: str
    start_ns: int
    end_ns: int
    elapsed_ns: int


@dataclass(frozen=True, slots=True)
class PhasePartition:
    rows: tuple[PhaseRow, ...]
    total_ns: int


def phase_partition(
    names: Sequence[str], boundary_stamps_ns: Sequence[int]
) -> PhasePartition:
    phase_names = tuple(names)
    stamps = tuple(
        _require_plain_int(value, label="phase boundary", minimum=0)
        for value in boundary_stamps_ns
    )
    if len(stamps) != len(phase_names) + 1:
        raise ValueError("phase boundary count differs")
    if len(set(phase_names)) != len(phase_names) or any(not name for name in phase_names):
        raise ValueError("phase names must be unique and nonempty")
    if any(right < left for left, right in zip(stamps, stamps[1:])):
        raise ValueError("phase boundaries are not monotonic")
    rows = tuple(
        PhaseRow(name, left, right, right - left)
        for name, left, right in zip(
            phase_names, stamps[:-1], stamps[1:], strict=True
        )
    )
    total = stamps[-1] - stamps[0]
    if sum(row.elapsed_ns for row in rows) != total:
        raise AssertionError("phase partition does not sum to its wall")
    return PhasePartition(rows=rows, total_ns=total)


def wall_passes(elapsed_ns: int, ceiling_ns: int) -> bool:
    elapsed = _require_plain_int(elapsed_ns, label="elapsed wall", minimum=0)
    ceiling = _require_plain_int(ceiling_ns, label="wall ceiling", minimum=0)
    return elapsed <= ceiling


def encode_binary(raw: bytes) -> dict[str, object]:
    if not isinstance(raw, bytes):
        raise TypeError("binary evidence must be immutable")
    return {
        "base64": base64.b64encode(raw).decode("ascii"),
        "byte_count": len(raw),
        "sha256": sha256(raw).hexdigest(),
    }


def decode_binary(value: Mapping[str, object], *, maximum: int) -> bytes:
    if set(value) != {"base64", "byte_count", "sha256"}:
        raise ValueError("binary evidence fields differ")
    count = _require_plain_int(value["byte_count"], label="binary byte count", minimum=0)
    if count > maximum:
        raise ValueError("binary evidence exceeds its cap")
    digest = _require_digest(value["sha256"], label="binary evidence digest")
    encoded = value["base64"]
    if not isinstance(encoded, str):
        raise TypeError("binary evidence base64 must be text")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError("binary evidence base64 differs") from error
    if len(raw) != count or sha256(raw).hexdigest() != digest:
        raise ValueError("binary evidence identity differs")
    return raw


def compile_argv(source: Path, cubin: Path) -> tuple[str, ...]:
    if not isinstance(source, Path) or not isinstance(cubin, Path):
        raise TypeError("compiler paths must be Path values")
    if source == cubin:
        raise ValueError("compiler source and output paths must differ")
    return (
        str(NVCC_PATH),
        *NVCC_OPTIONS,
        "--output-file",
        str(cubin),
        str(source),
    )


def _arm_kernel_names(arm: str) -> tuple[str, ...]:
    if arm == POSITIONAL:
        return tuple(name for name in KERNEL_NAMES if name.startswith("positional_"))
    if arm in {RESIDENT_RRNS, BATCHED_RRNS}:
        return tuple(name for name in KERNEL_NAMES if name.startswith("rrns_"))
    raise ValueError("unknown fixed-width device arm")


def arm_resource_eligible(
    arm: str, resources: Mapping[str, EffectiveResource]
) -> bool:
    names = _arm_kernel_names(arm)
    if set(resources) != set(KERNEL_NAMES):
        raise ValueError("effective resource domain differs")
    return all(resources[name].eligible for name in names)


def symbolic_literal45_liveness() -> dict[str, dict[str, object]]:
    """Price the frozen literal-45 buffers without constructing a value.

    Level six remains the captured high/low pair buffer.  The fixed-width
    forward workspace contains levels zero through five only; materializing a
    fixed-width level-six table would silently abandon ADR-0438's hybrid.
    """

    from math import comb

    cards = 45
    width = 64
    query_chunk = 4096
    source_chunk = 4096
    source_rows = comb(cards, 6)
    query_rows = comb(cards, 4)
    labeled_rows = 6 * query_rows
    forward_rows = sum(comb(cards, level) for level in range(6))
    adjoint_rows = sum(comb(cards, level) for level in range(5))
    common = (
        BufferLifetime(
            "captured_source_high_low_pairs",
            "captured_source_high_low_pairs",
            source_rows * width * 2 * 8,
            1,
            9,
        ),
        BufferLifetime(
            "captured_labeled_covector_high_low_pairs",
            "captured_labeled_covector_high_low_pairs",
            labeled_rows * width * 2 * 8,
            1,
            3,
        ),
        BufferLifetime(
            "captured_labeled_weight_high_low_pairs",
            "captured_labeled_weight_high_low_pairs",
            labeled_rows * 2 * 8,
            1,
            6,
        ),
        BufferLifetime(
            "query_masks_and_labels",
            "query_masks_and_labels",
            labeled_rows * (8 + 4),
            1,
            3,
        ),
        BufferLifetime(
            "resident_source_rank_to_cards",
            "resident_source_rank_to_cards",
            source_rows * 6,
            1,
            9,
        ),
    )
    output: dict[str, dict[str, object]] = {}
    for arm, cell_bytes, channels in (
        (POSITIONAL, 40, 0),
        (RESIDENT_RRNS, 72, 9),
        (BATCHED_RRNS, 40, 5),
    ):
        if arm != BATCHED_RRNS:
            rows = common + (
                BufferLifetime(
                    "forward_levels_zero_through_five",
                    "recurrence_workspace",
                    forward_rows * width * cell_bytes,
                    2,
                    6,
                ),
                BufferLifetime(
                    "adjoint_levels_zero_through_four",
                    "recurrence_workspace",
                    adjoint_rows * width * cell_bytes,
                    6,
                    9,
                ),
                BufferLifetime(
                    "aggregated_query_covectors",
                    "aggregated_query_covectors",
                    query_rows * width * cell_bytes,
                    2,
                    7,
                ),
                BufferLifetime(
                    "aggregated_query_weights",
                    "aggregated_query_weights",
                    query_rows * cell_bytes,
                    2,
                    6,
                ),
                BufferLifetime(
                    "streamed_forward_chunk",
                    "streamed_output_workspace",
                    query_chunk * width * cell_bytes,
                    5,
                    6,
                ),
                BufferLifetime(
                    "streamed_adjoint_chunk",
                    "streamed_output_workspace",
                    source_chunk * width * cell_bytes,
                    8,
                    9,
                ),
                BufferLifetime(
                    "selected_and_scalar_outputs",
                    "selected_and_scalar_outputs",
                    max(1, channels) * (6 * width + 3) * 8,
                    4,
                    11,
                ),
            )
        else:
            persistent = tuple(
                BufferLifetime(
                    row.logical_name,
                    row.storage_identity,
                    row.byte_count,
                    row.birth_boundary,
                    17,
                )
                for row in common
            )
            rows = persistent + (
                BufferLifetime(
                    "first_forward_levels_zero_through_five",
                    "recurrence_workspace",
                    forward_rows * width * cell_bytes,
                    2,
                    6,
                ),
                BufferLifetime(
                    "first_adjoint_levels_zero_through_four",
                    "recurrence_workspace",
                    adjoint_rows * width * cell_bytes,
                    6,
                    9,
                ),
                BufferLifetime(
                    "second_forward_levels_zero_through_five",
                    "recurrence_workspace",
                    forward_rows * width * cell_bytes,
                    10,
                    14,
                ),
                BufferLifetime(
                    "second_adjoint_levels_zero_through_four",
                    "recurrence_workspace",
                    adjoint_rows * width * cell_bytes,
                    14,
                    17,
                ),
                BufferLifetime(
                    "first_aggregated_query_covectors",
                    "aggregated_query_covectors",
                    query_rows * width * cell_bytes,
                    2,
                    7,
                ),
                BufferLifetime(
                    "second_aggregated_query_covectors",
                    "aggregated_query_covectors",
                    query_rows * width * 4 * 8,
                    10,
                    15,
                ),
                BufferLifetime(
                    "first_aggregated_query_weights",
                    "aggregated_query_weights",
                    query_rows * cell_bytes,
                    2,
                    6,
                ),
                BufferLifetime(
                    "second_aggregated_query_weights",
                    "aggregated_query_weights",
                    query_rows * 4 * 8,
                    10,
                    14,
                ),
                BufferLifetime(
                    "first_streamed_forward_chunk",
                    "streamed_output_workspace",
                    query_chunk * width * cell_bytes,
                    5,
                    6,
                ),
                BufferLifetime(
                    "first_streamed_adjoint_chunk",
                    "streamed_output_workspace",
                    source_chunk * width * cell_bytes,
                    8,
                    9,
                ),
                BufferLifetime(
                    "second_streamed_forward_chunk",
                    "streamed_output_workspace",
                    query_chunk * width * 4 * 8,
                    13,
                    14,
                ),
                BufferLifetime(
                    "second_streamed_adjoint_chunk",
                    "streamed_output_workspace",
                    source_chunk * width * 4 * 8,
                    16,
                    17,
                ),
                BufferLifetime(
                    "retained_batched_digests_and_scalar_residues",
                    "retained_batched_digests_and_scalar_residues",
                    9 * (6 * width + 3) * 8,
                    4,
                    19,
                ),
            )
        result = memory_liveness(
            rows, boundary_count=len(phase_names_for_arm(arm)) + 1
        )
        output[arm] = {
            "buffers": [asdict(row) for row in rows],
            "liveness": asdict(result),
            "fixed_width_level_six_materialized": False,
            "forward_workspace_levels": [0, 1, 2, 3, 4, 5],
            "literal_geometry": {
                "cards": cards,
                "feature_tile_width": width,
                "source_rows": source_rows,
                "query_rows": query_rows,
                "labeled_query_rows": labeled_rows,
                "forward_rows_zero_through_five": forward_rows,
                "adjoint_rows_zero_through_four": adjoint_rows,
            },
        }
    return output


def signed_integer_to_words(value: int, limbs: int) -> tuple[int, ...]:
    item = _require_plain_int(value, label="signed fixed-width value")
    count = _require_plain_int(limbs, label="signed fixed-width limbs", minimum=1)
    modulus = 1 << (64 * count)
    minimum = -(1 << (64 * count - 1))
    maximum = (1 << (64 * count - 1)) - 1
    if item < minimum or item > maximum:
        raise OverflowError("signed fixed-width value exceeds its allocation")
    encoded = item % modulus
    return tuple((encoded >> (64 * index)) & ((1 << 64) - 1) for index in range(count))


def words_to_signed_integer(words: Sequence[int]) -> int:
    values = tuple(
        _require_plain_int(value, label="fixed-width word", minimum=0)
        for value in words
    )
    if not values or any(value >= 1 << 64 for value in values):
        raise ValueError("fixed-width words differ")
    unsigned = sum(value << (64 * index) for index, value in enumerate(values))
    if values[-1] >> 63:
        unsigned -= 1 << (64 * len(values))
    return unsigned


def signed_schoolbook_product_words(
    left: int, right: int, *, left_limbs: int, right_limbs: int, output_limbs: int
) -> tuple[int, ...]:
    """Standard-library oracle for the CUDA product's add-and-propagate form."""

    a = signed_integer_to_words(left, left_limbs)
    b = signed_integer_to_words(right, right_limbs)
    a_negative = bool(a[-1] >> 63)
    b_negative = bool(b[-1] >> 63)

    def magnitude(words: tuple[int, ...], negative: bool) -> list[int]:
        if not negative:
            return list(words)
        width = 1 << (64 * len(words))
        value = (-words_to_signed_integer(words)) % width
        return [(value >> (64 * i)) & ((1 << 64) - 1) for i in range(len(words))]

    left_words = magnitude(a, a_negative)
    right_words = magnitude(b, b_negative)
    output = [0] * output_limbs
    mask = (1 << 64) - 1
    for i, left_word in enumerate(left_words):
        for j, right_word in enumerate(right_words):
            position = i + j
            if position >= output_limbs:
                if left_word * right_word:
                    raise OverflowError("schoolbook product exceeds its allocation")
                continue
            product = left_word * right_word
            low = product & mask
            high = product >> 64
            total = output[position] + low
            output[position] = total & mask
            carry = total >> 64
            position += 1
            if position < output_limbs:
                total = output[position] + high + carry
                output[position] = total & mask
                carry = total >> 64
                position += 1
                while carry and position < output_limbs:
                    total = output[position] + carry
                    output[position] = total & mask
                    carry = total >> 64
                    position += 1
            if carry:
                raise OverflowError("schoolbook carry exceeds its allocation")
    unsigned = sum(word << (64 * index) for index, word in enumerate(output))
    if a_negative ^ b_negative:
        unsigned = (-unsigned) % (1 << (64 * output_limbs))
    result = tuple(
        (unsigned >> (64 * index)) & mask for index in range(output_limbs)
    )
    expected = left * right
    if words_to_signed_integer(result) != expected:
        raise OverflowError("signed product exceeds its destination")
    return result


@dataclass(frozen=True, slots=True)
class ValidationPopulation:
    label: str
    captured: object
    authority: object
    source_high: object
    source_low: object
    query_high: object
    query_low: object
    weight_high: object
    weight_low: object
    query_labels: object
    source_cards: object
    input_sha256: str
    forward_levels: object
    adjoint_levels: object


def _make_signed_validation_population(exact: Any) -> object:
    import math

    cards = 12
    source_masks = exact.complete_masks(cards, 6)
    query_occupancies = exact.complete_masks(cards, 4)
    source_rows = []
    for rank, _ in enumerate(source_masks):
        row = []
        for feature in range(5):
            if feature == 4:
                high = math.ldexp(float(8 + rank % 5), -3)
                low = math.ldexp(1.0, -96 - rank % 3)
            elif (rank + 3 * feature) % 17 == 0:
                high = -0.0 if rank & 1 else 0.0
                low = 0.0
            else:
                sign = -1.0 if (rank + feature) & 1 else 1.0
                exponent = -18 if (rank + feature) % 3 else 21
                high = sign * math.ldexp(
                    float(8 + (rank + feature) % 7), exponent - 3
                )
                low = -sign * math.ldexp(
                    1.0, -104 + (rank + feature) % 5
                )
            row.append(exact.CapturedPair(high, low))
        source_rows.append(tuple(row))
    query_masks = []
    query_labels = []
    covectors = []
    weights = []
    for occupancy_rank, query_mask in enumerate(query_occupancies):
        for label in range(6):
            query_masks.append(query_mask)
            query_labels.append(label)
            weights.append(
                exact.CapturedPair(
                    math.ldexp(float(9 + (occupancy_rank + label) % 6), -4),
                    math.ldexp(1.0, -101 - label % 3),
                )
            )
            row = []
            for feature in range(5):
                if (occupancy_rank + label + feature) % 19 == 0:
                    row.append(exact.CapturedPair(0.0, -0.0))
                    continue
                sign = (
                    -1.0
                    if (occupancy_rank + 2 * label + feature) & 1
                    else 1.0
                )
                exponent = -14 if (occupancy_rank + feature) % 4 else 17
                row.append(
                    exact.CapturedPair(
                        sign
                        * math.ldexp(
                            float(8 + (occupancy_rank + label + feature) % 5),
                            exponent - 3,
                        ),
                        -sign
                        * math.ldexp(
                            1.0,
                            -109 + (occupancy_rank + label + feature) % 7,
                        ),
                    )
                )
            covectors.append(tuple(row))
    window = exact.FrozenExponentWindow(-120, 30)
    return exact.CapturedOperatorInput(
        available_cards=cards,
        source_masks=source_masks,
        source_rows=tuple(source_rows),
        query_masks=tuple(query_masks),
        query_labels=tuple(query_labels),
        query_covectors=tuple(covectors),
        query_weights=tuple(weights),
        reach_feature=4,
        source_window=window,
        covector_window=window,
        weight_window=window,
    )


def _make_natural_validation_population(exact: Any, paired: Any) -> object:
    fixture = paired.compile_consumer_population_fixture(10)
    unary = fixture.unary_weights.reshape(-1)
    factors = fixture.mode_factors.reshape(-1)
    source_masks = []
    source_rows = []
    transitions0, transitions1, transitions2 = fixture.transitions[:3]

    def mask(cards: Sequence[int]) -> int:
        return sum(1 << int(card) for card in cards)

    def captured(value: object) -> object:
        return exact.CapturedPair(float(value.high), float(value.low))

    for rank in range(fixture.geometry.source_occupancies):
        cards = paired.colex_unrank(rank, 10, 6)
        source_masks.append(mask(cards))
        row = [paired.FloatPair(0.0, 0.0) for _ in range(176)]
        for positions in fixture.source_pair_positions:
            hands = tuple(
                int(
                    fixture.pair_to_hand[
                        cards[int(positions[2 * seat])],
                        cards[int(positions[2 * seat + 1])],
                    ]
                )
                for seat in range(3)
            )
            state0 = int(transitions0[0, hands[0]])
            state1 = int(transitions1[state0, hands[1]])
            state2 = int(transitions2[state1, hands[2]])
            indices = tuple(
                int(fixture.unary_offsets[seat]) + hands[seat]
                for seat in range(3)
            )
            weight = paired._pair_weight_host(1.0, unary, factors, indices)
            row[state2] = paired._pair_add_host(row[state2], weight)
            row[paired.REACH_GLOBAL_FEATURE] = paired._pair_add_host(
                row[paired.REACH_GLOBAL_FEATURE], weight
            )
        source_rows.append(tuple(captured(value) for value in row))
    query_masks = []
    query_labels = []
    covectors = []
    weights = []
    transitions3, transitions4 = fixture.transitions[3:5]
    for record in range(fixture.geometry.labeled_query_records):
        query_masks.append(int(fixture.query_masks[record]))
        query_labels.append(record % 6)
        hand4 = int(fixture.query_hand_indices[record, 0])
        hand5 = int(fixture.query_hand_indices[record, 1])
        indices = (
            int(fixture.unary_offsets[3]),
            int(fixture.unary_offsets[4]) + hand4,
            int(fixture.unary_offsets[5]) + hand5,
        )
        weight = paired._pair_weight_host(
            float(fixture.mixture_weights[0]), unary, factors, indices
        )
        weights.append(captured(weight))
        row = []
        for feature in range(176):
            if feature == paired.REACH_GLOBAL_FEATURE:
                payoff = fixture.sunk_value
            else:
                state3 = int(transitions3[feature, 0])
                state4 = int(transitions4[state3, hand4])
                payoff = float(fixture.terminal_winner_values[state4, hand5])
            row.append(captured(paired._pair_times_float64_host(weight, payoff)))
        covectors.append(tuple(row))
    return exact.CapturedOperatorInput(
        available_cards=10,
        source_masks=tuple(source_masks),
        source_rows=tuple(source_rows),
        query_masks=tuple(query_masks),
        query_labels=tuple(query_labels),
        query_covectors=tuple(covectors),
        query_weights=tuple(weights),
        reach_feature=paired.REACH_GLOBAL_FEATURE,
    )


def _canonical_population_arrays(captured: object, np: Any) -> dict[str, object]:
    source_order = sorted(range(len(captured.source_masks)), key=captured.source_masks.__getitem__)
    source_rows = tuple(captured.source_rows[index] for index in source_order)
    source_masks = tuple(captured.source_masks[index] for index in source_order)
    groups: dict[int, dict[int, int]] = {}
    for index, (mask, label) in enumerate(
        zip(captured.query_masks, captured.query_labels, strict=True)
    ):
        if label in groups.setdefault(mask, {}):
            raise ValueError("validation query label repeats")
        groups[mask][label] = index
    if any(set(group) != set(range(6)) for group in groups.values()):
        raise ValueError("validation query labels do not close")
    query_order = tuple(
        groups[mask][label] for mask in sorted(groups) for label in range(6)
    )
    query_rows = tuple(captured.query_covectors[index] for index in query_order)
    query_weights = tuple(captured.query_weights[index] for index in query_order)
    labels = np.asarray(
        [captured.query_labels[index] for index in query_order], dtype=np.int32
    )

    def components(rows: Sequence[Sequence[object]]) -> tuple[object, object]:
        high = np.asarray(
            [[pair.high for pair in row] for row in rows], dtype=np.float64
        )
        low = np.asarray(
            [[pair.low for pair in row] for row in rows], dtype=np.float64
        )
        return np.ascontiguousarray(high), np.ascontiguousarray(low)

    source_high, source_low = components(source_rows)
    query_high, query_low = components(query_rows)
    weight_high, weight_low = components(tuple((pair,) for pair in query_weights))
    source_cards = np.asarray(
        [
            [card for card in range(captured.available_cards) if mask & (1 << card)]
            for mask in source_masks
        ],
        dtype=np.uint8,
    )
    digest = sha256()
    for value in (
        source_high,
        source_low,
        query_high,
        query_low,
        weight_high,
        weight_low,
        labels,
        source_cards,
    ):
        digest.update(value.tobytes(order="C"))
    digest.update(
        json.dumps(
            {
                "available_cards": captured.available_cards,
                "feature_width": source_high.shape[1],
                "reach_feature": captured.reach_feature,
                "source_masks": list(source_masks),
                "query_masks": sorted(groups),
            },
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    )
    return {
        "source_high": source_high,
        "source_low": source_low,
        "query_high": query_high,
        "query_low": query_low,
        "weight_high": weight_high,
        "weight_low": weight_low,
        "query_labels": labels,
        "source_cards": np.ascontiguousarray(source_cards),
        "input_sha256": digest.hexdigest(),
    }


def build_validation_population(label: str) -> ValidationPopulation:
    """Build one already-open reduced fixture and its unbounded authority."""

    import numpy as np

    from . import legal_river_quotient_exact_integer_operator as exact
    from . import legal_river_quotient_cuda_compensated_tiles as paired

    if label == "complete_10":
        captured = _make_natural_validation_population(exact, paired)
    elif label == "signed_12":
        captured = _make_signed_validation_population(exact)
    else:
        raise ValueError("unknown validation population")
    authority = exact.execute_exact_integer_operator(captured)
    arrays = _canonical_population_arrays(captured, np)
    source = dict(authority.source_rows)
    covectors = dict(authority.aggregated_query_covectors)
    forward_levels = exact.build_forward_levels(captured.available_cards, source)
    adjoint_levels = exact.build_adjoint_levels(captured.available_cards, covectors)
    return ValidationPopulation(
        label=label,
        captured=captured,
        authority=authority,
        source_high=arrays["source_high"],
        source_low=arrays["source_low"],
        query_high=arrays["query_high"],
        query_low=arrays["query_low"],
        weight_high=arrays["weight_high"],
        weight_low=arrays["weight_low"],
        query_labels=arrays["query_labels"],
        source_cards=arrays["source_cards"],
        input_sha256=arrays["input_sha256"],
        forward_levels=forward_levels,
        adjoint_levels=adjoint_levels,
    )


def _flatten_rows(rows: Iterable[Sequence[int]]) -> tuple[int, ...]:
    return tuple(int(value) for row in rows for value in row)


def _level_values(levels: object, maximum_level: int) -> tuple[int, ...]:
    return _flatten_rows(
        row
        for level in range(maximum_level + 1)
        for _, row in levels.rows[level]
    )


def _positional_bytes(values: Iterable[int], limbs: int) -> bytes:
    output = bytearray()
    for value in values:
        for word in signed_integer_to_words(int(value), limbs):
            output.extend(word.to_bytes(8, "little"))
    return bytes(output)


def _rrns_montgomery_bytes(
    values: Iterable[int], channel_indices: Sequence[int], fixed: Any
) -> bytes:
    _, scalar = fixed.validate_frozen_rrns()
    moduli = scalar.all_moduli
    constants = tuple(fixed.montgomery_constants(modulus) for modulus in moduli)
    output = bytearray()
    for value in values:
        for channel in channel_indices:
            encoded = fixed.montgomery_encode(int(value) % moduli[channel], constants[channel])
            output.extend(int(encoded).to_bytes(8, "little"))
    return bytes(output)


def _selected_coordinates(population: ValidationPopulation) -> tuple[
    tuple[int, ...], tuple[int, ...], tuple[int, ...], tuple[int, ...]
]:
    authority = population.authority
    query_rows = len(authority.forward_scaled_rows)
    source_rows = len(authority.adjoint_scaled_rows)
    width = authority.feature_width
    forward_ranks = (0, query_rows // 2, query_rows - 1, query_rows // 3)
    forward_features = (0, authority.reach_feature if hasattr(authority, "reach_feature") else population.captured.reach_feature, width - 1, min(1, width - 1))
    adjoint_ranks = (0, source_rows // 2, source_rows - 1, source_rows // 3)
    adjoint_features = (0, population.captured.reach_feature, width - 1, min(1, width - 1))
    return forward_ranks, forward_features, adjoint_ranks, adjoint_features


def _representation_expectations(
    population: ValidationPopulation,
    *,
    arm: str,
    channel_indices: Sequence[int] = (),
) -> dict[str, bytes]:
    authority = population.authority
    source_values = _flatten_rows(row for _, row in authority.source_rows)
    covector_values = _flatten_rows(
        row for _, row in authority.aggregated_query_covectors
    )
    weight_values = tuple(value for _, value in authority.aggregated_query_weights)
    forward_values = _flatten_rows(row for _, row in authority.forward_scaled_rows)
    adjoint_values = _flatten_rows(row for _, row in authority.adjoint_scaled_rows)
    forward_ranks, forward_features, adjoint_ranks, adjoint_features = (
        _selected_coordinates(population)
    )
    selected_forward = tuple(
        authority.forward_scaled_rows[rank][1][feature]
        for rank, feature in zip(forward_ranks, forward_features, strict=True)
    )
    selected_adjoint = tuple(
        authority.adjoint_scaled_rows[rank][1][feature]
        for rank, feature in zip(adjoint_ranks, adjoint_features, strict=True)
    )
    rows = {
        "source_encoding": source_values,
        "aggregated_covectors": covector_values,
        "aggregated_weights": weight_values,
        "forward_levels": _level_values(population.forward_levels, 5),
        "forward_selected": selected_forward,
        "forward_stream": forward_values,
        "adjoint_levels": _level_values(population.adjoint_levels, 4),
        "adjoint_selected": selected_adjoint,
        "adjoint_stream": adjoint_values,
    }
    if arm == POSITIONAL:
        return {name: _positional_bytes(values, 5) for name, values in rows.items()}
    if arm not in {RESIDENT_RRNS, BATCHED_RRNS} or not channel_indices:
        raise ValueError("RRNS representation expectation lacks channels")
    from . import legal_river_quotient_fixed_width_work_comparison as fixed

    return {
        name: _rrns_montgomery_bytes(values, channel_indices, fixed)
        for name, values in rows.items()
    }


def _digest_expectations(rows: Mapping[str, bytes]) -> dict[str, str]:
    if not rows or any(not isinstance(value, bytes) for value in rows.values()):
        raise TypeError("representation expectations must be nonempty byte rows")
    return {name: sha256(value).hexdigest() for name, value in rows.items()}


def _reduced_authority_manifest(
    population: ValidationPopulation,
    *,
    positional: Mapping[str, bytes],
    resident: Mapping[tuple[int, ...], Mapping[str, bytes]],
    batched: Mapping[tuple[int, ...], Mapping[str, bytes]],
) -> dict[str, object]:
    """Bind the host authority before any candidate in this population runs."""

    authority = population.authority
    expected_resident = (tuple(range(9)),)
    expected_batched = ((0, 1, 2, 3, 8), (4, 5, 6, 7))
    if tuple(resident) != expected_resident or tuple(batched) != expected_batched:
        raise ValueError("reduced authority RRNS batch domain differs")
    return {
        "schema_version": "fixed-width-device-reduced-authority-manifest-v1",
        "population": population.label,
        "input_sha256": population.input_sha256,
        "geometry": {
            "available_cards": authority.available_cards,
            "feature_width": authority.feature_width,
            "source_occupancies": len(authority.source_rows),
            "query_occupancies": len(authority.forward_scaled_rows),
            "labeled_query_records": int(population.query_high.shape[0]),
        },
        "representation_digests": {
            POSITIONAL: _digest_expectations(positional),
            RESIDENT_RRNS: {
                str(batch): _digest_expectations(resident[batch])
                for batch in expected_resident
            },
            BATCHED_RRNS: {
                str(batch): _digest_expectations(batched[batch])
                for batch in expected_batched
            },
        },
        "scalar_values_decimal": {
            "forward_numerator": str(authority.forward_integer_numerator),
            "adjoint_numerator": str(authority.adjoint_integer_numerator),
            "reach": str(authority.forward_integer_reach),
        },
        "conditional_value_bits": authority.conditional_value_bits,
    }


class DevicePreflightFailure(RuntimeError):
    def __init__(self, terminal: str, reason: str) -> None:
        super().__init__(reason)
        self.terminal = terminal
        self.reason = reason


@dataclass(frozen=True, slots=True)
class CompiledDeviceContext:
    cp: object
    module: object
    kernels: Mapping[str, object]
    streams: Mapping[str, object]
    cubin: bytes
    resources: Mapping[str, EffectiveResource]
    runtime: Mapping[str, object]
    compile_and_resource_elapsed_ns: int
    global_phase_rows: tuple[PhaseRow, ...]


def _tool_version_ok(raw: bytes) -> bool:
    text = raw.decode("ascii", "replace")
    return "release 13.3" in text or "V13.3" in text


def _load_compiled_context(
    directory: Path,
    emit: Callable[[str, Mapping[str, object]], None],
    *,
    start_ns: int | None = None,
) -> CompiledDeviceContext:
    """Compile once, retain raw evidence, then load exactly the retained bytes."""

    started = (
        perf_counter_ns()
        if start_ns is None
        else _require_plain_int(start_ns, label="compiled-context start", minimum=0)
    )
    phase_stamps = [started]
    source_path = directory / "fixed_width_device_preflight.cu"
    compiler_output = directory / "compiler-output.cubin"
    inspected_path = directory / "inspected-and-loaded.cubin"
    source_bytes = CUDA_SOURCE.encode("utf-8")
    with source_path.open("xb") as handle:
        handle.write(source_bytes)
        handle.flush()
        os.fsync(handle.fileno())
    if source_path.read_bytes() != source_bytes:
        raise DevicePreflightFailure(
            "cuda_source_materialization_rejection",
            "materialized CUDA source differs from the sealed literal",
        )
    emit(
        "tool_identity_and_cuda_source_materialization",
        {
            "schema_version": "fixed-width-device-source-materialization-v1",
            "cuda_source_sha256": CUDA_SOURCE_SHA256,
            "cuda_source_bytes": len(source_bytes),
            "compiler_options": list(NVCC_OPTIONS),
        },
    )
    versions = {}
    version_commands: dict[str, BoundedCommand] = {}
    for label, path in (
        ("nvcc", NVCC_PATH),
        ("cuobjdump", CUOBJDUMP_PATH),
        ("nvdisasm", NVDISASM_PATH),
    ):
        command = run_bounded_command(
            (str(path), "--version"),
            wall_ns=PER_COMMAND_WALL_NS,
            stdout_limit=MAXIMUM_EXTERNAL_STREAM_BYTES,
            stderr_limit=MAXIMUM_EXTERNAL_STREAM_BYTES,
            cwd=directory,
        )
        versions[label] = command.evidence()
        version_commands[label] = command
    emit(
        "tool_versions",
        {
            "schema_version": "fixed-width-device-tool-versions-v1",
            "commands": versions,
        },
    )
    for label, command in version_commands.items():
        if (
            command.status != "completed"
            or command.return_code != 0
            or not _tool_version_ok(command.stdout + command.stderr)
        ):
            raise DevicePreflightFailure(
                "tool_identity_rejection", f"{label} is not the frozen CUDA 13.3 tool"
            )
    phase_stamps.append(perf_counter_ns())
    compile_command = run_bounded_command(
        compile_argv(source_path, compiler_output),
        wall_ns=COMPILE_RESOURCE_WALL_NS,
        stdout_limit=MAXIMUM_COMPILER_STREAM_BYTES,
        stderr_limit=MAXIMUM_COMPILER_STREAM_BYTES,
        cwd=directory,
    )
    emit(
        "compile",
        {
            "schema_version": "fixed-width-device-compile-v1",
            "command": compile_command.evidence(),
        },
    )
    if compile_command.status != "completed" or compile_command.return_code != 0:
        raise DevicePreflightFailure("compiler_rejection", "nvcc did not produce a cubin")
    if not compiler_output.is_file():
        raise DevicePreflightFailure("compiler_rejection", "nvcc output is absent")
    phase_stamps.append(perf_counter_ns())
    cubin = compiler_output.read_bytes()
    if (
        not cubin.startswith(bytes((0x7F, 0x45, 0x4C, 0x46)))
        or len(cubin) == 0
        or len(cubin) > MAXIMUM_CUBIN_BYTES
    ):
        raise DevicePreflightFailure(
            "direct_cubin_rejection", "compiler output is not a bounded direct ELF cubin"
        )
    emit(
        "durable_cubin_capture",
        {
            "schema_version": "fixed-width-device-cubin-capture-v1",
            "cubin": encode_binary(cubin),
            "zero_suffix_or_repair_applied": False,
        },
    )
    phase_stamps.append(perf_counter_ns())
    with inspected_path.open("xb") as handle:
        handle.write(cubin)
        handle.flush()
        os.fsync(handle.fileno())
    if inspected_path.read_bytes() != cubin:
        raise DevicePreflightFailure(
            "cubin_identity_rejection", "inspection cubin differs from retained bytes"
        )
    external = {}
    for label, path, arguments in (
        (
            "cuobjdump_resource_usage",
            CUOBJDUMP_PATH,
            ("--dump-resource-usage", str(inspected_path)),
        ),
        ("nvdisasm", NVDISASM_PATH, (str(inspected_path),)),
    ):
        command = run_bounded_command(
            (str(path), *arguments),
            wall_ns=PER_COMMAND_WALL_NS,
            stdout_limit=MAXIMUM_EXTERNAL_STREAM_BYTES,
            stderr_limit=MAXIMUM_EXTERNAL_STREAM_BYTES,
            cwd=directory,
        )
        external[label] = command
        emit(
            "external_resource_command",
            {
                "schema_version": "fixed-width-device-resource-command-v1",
                "command_id": label,
                "command": command.evidence(),
                "inspected_cubin_sha256": sha256(cubin).hexdigest(),
            },
        )
        if command.status != "completed" or command.return_code != 0:
            raise DevicePreflightFailure(
                "resource_instrument_rejection", f"{label} did not complete"
            )
    try:
        ptxas = parse_ptxas_verbose(compile_command.stdout + compile_command.stderr)
        cubin_rows = parse_cuobjdump_resource_usage(
            external["cuobjdump_resource_usage"].stdout
        )
        sass = parse_nvdisasm_local_sites(external["nvdisasm"].stdout)
    except (TypeError, ValueError) as error:
        raise DevicePreflightFailure(
            "resource_instrument_rejection", str(error)
        ) from error
    phase_stamps.append(perf_counter_ns())

    import cupy as cp

    properties = cp.cuda.runtime.getDeviceProperties(0)
    name = properties["name"]
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    runtime = {
        "device_name": str(name),
        "compute_capability": f"{int(properties['major'])}{int(properties['minor'])}",
        "device_total_bytes": int(properties["totalGlobalMem"]),
        "multiprocessor_count": int(properties["multiProcessorCount"]),
        "maximum_threads_per_multiprocessor": int(
            properties["maxThreadsPerMultiProcessor"]
        ),
        "maximum_shared_bytes_per_block": max(
            int(properties.get("sharedMemPerBlock", 0)),
            int(properties.get("sharedMemPerBlockOptin", 0)),
        ),
        "cuda_driver_version": int(cp.cuda.runtime.driverGetVersion()),
        "cuda_runtime_version": int(cp.cuda.runtime.runtimeGetVersion()),
        "cupy_version": str(cp.__version__),
    }
    emit(
        "live_hardware_identity",
        {
            "schema_version": "fixed-width-device-live-hardware-v1",
            "runtime": runtime,
        },
    )
    expected_runtime = {
        "device_name": "NVIDIA GeForce RTX 5080",
        "compute_capability": "120",
        "device_total_bytes": EXPECTED_DEVICE_TOTAL_BYTES,
        "multiprocessor_count": 84,
        "maximum_threads_per_multiprocessor": 1536,
    }
    if any(runtime[key] != value for key, value in expected_runtime.items()) or (
        runtime["cuda_driver_version"] < 13030
        or runtime["cuda_runtime_version"] < 13020
    ):
        raise DevicePreflightFailure(
            "hardware_identity_rejection", "live CUDA identity differs from ADR-0439"
        )
    module = cp.cuda.function.Module()
    module.load(cubin)
    kernels = {name: module.get_function(name) for name in KERNEL_NAMES}
    streams = {arm: cp.cuda.Stream(non_blocking=True) for arm in ARMS}
    attributes = {
        "local_bytes": cp.cuda.driver.CU_FUNC_ATTRIBUTE_LOCAL_SIZE_BYTES,
        "registers": cp.cuda.driver.CU_FUNC_ATTRIBUTE_NUM_REGS,
        "shared_bytes": cp.cuda.driver.CU_FUNC_ATTRIBUTE_SHARED_SIZE_BYTES,
        "maximum_threads_per_block": (
            cp.cuda.driver.CU_FUNC_ATTRIBUTE_MAX_THREADS_PER_BLOCK
        ),
    }
    driver = {
        name: DriverResource(
            kernel=name,
            **{
                label: int(cp.cuda.driver.funcGetAttribute(attribute, kernel.ptr))
                for label, attribute in attributes.items()
            },
        )
        for name, kernel in kernels.items()
    }
    resources = combine_resource_evidence(
        ptxas,
        cubin_rows,
        sass,
        driver,
        device_shared_limit_bytes=runtime["maximum_shared_bytes_per_block"],
    )
    emit(
        "module_load_and_resource_evidence",
        {
            "schema_version": "fixed-width-device-resource-evidence-v1",
            "cubin_sha256": sha256(cubin).hexdigest(),
            "runtime": runtime,
            "ptxas": _serialize_dataclass_rows(ptxas),
            "cuobjdump": _serialize_dataclass_rows(cubin_rows),
            "sass": _serialize_dataclass_rows(sass),
            "driver": _serialize_dataclass_rows(driver),
            "effective": _serialize_dataclass_rows(resources),
            "arm_streams": {
                "count": len(streams),
                "arms": list(streams),
                "one_persistent_nonblocking_stream_per_arm": True,
            },
        },
    )
    phase_stamps.append(perf_counter_ns())
    elapsed = phase_stamps[-1] - started
    if not wall_passes(elapsed, COMPILE_RESOURCE_WALL_NS):
        raise DevicePreflightFailure(
            "compile_resource_wall_rejection", "compile and resource wall exceeded"
        )
    return CompiledDeviceContext(
        cp=cp,
        module=module,
        kernels=kernels,
        streams=streams,
        cubin=cubin,
        resources=resources,
        runtime=runtime,
        compile_and_resource_elapsed_ns=elapsed,
        global_phase_rows=phase_partition(
            GLOBAL_PHASE_NAMES[1:6], phase_stamps
        ).rows,
    )


# The device translation unit is literal and hash-bound at source seal.  It is
# intentionally defined below the standard-library evidence machinery so that
# importing this module cannot compile or load it.
CUDA_SOURCE = r'''// ADR-0439 exact fixed-width quotient preflight
#include <stdint.h>

extern "C" __device__ __forceinline__ uint64_t add_words(
    uint64_t a, uint64_t b, uint64_t carry_in, uint64_t *carry_out) {
    uint64_t first = a + b;
    uint64_t c1 = first < a;
    uint64_t second = first + carry_in;
    uint64_t c2 = second < first;
    *carry_out = c1 | c2;
    return second;
}

extern "C" __device__ __forceinline__ uint64_t sub_words(
    uint64_t a, uint64_t b, uint64_t borrow_in, uint64_t *borrow_out) {
    uint64_t first = a - b;
    uint64_t b1 = a < b;
    uint64_t second = first - borrow_in;
    uint64_t b2 = first < borrow_in;
    *borrow_out = b1 | b2;
    return second;
}

template<int N>
__device__ __forceinline__ void clear_words(uint64_t (&out)[N]) {
    #pragma unroll
    for (int i = 0; i < N; ++i) out[i] = 0ULL;
}

template<int N>
__device__ __forceinline__ void load_words(
    const uint64_t *source, uint64_t (&out)[N]) {
    #pragma unroll
    for (int i = 0; i < N; ++i) out[i] = source[i];
}

template<int N>
__device__ __forceinline__ void store_words(
    uint64_t *target, const uint64_t (&value)[N]) {
    #pragma unroll
    for (int i = 0; i < N; ++i) target[i] = value[i];
}

template<int N>
__device__ __forceinline__ void add_in_place(
    uint64_t (&left)[N], const uint64_t (&right)[N]) {
    uint64_t carry = 0ULL;
    #pragma unroll
    for (int i = 0; i < N; ++i) {
        left[i] = add_words(left[i], right[i], carry, &carry);
    }
}

template<int N>
__device__ __forceinline__ void subtract_in_place(
    uint64_t (&left)[N], const uint64_t (&right)[N]) {
    uint64_t borrow = 0ULL;
    #pragma unroll
    for (int i = 0; i < N; ++i) {
        left[i] = sub_words(left[i], right[i], borrow, &borrow);
    }
}

template<int N>
__device__ __forceinline__ void negate_words(uint64_t (&value)[N]) {
    uint64_t carry = 1ULL;
    #pragma unroll
    for (int i = 0; i < N; ++i) {
        uint64_t item = ~value[i];
        uint64_t next = item + carry;
        carry = (next < item);
        value[i] = next;
    }
}

template<int N>
__device__ __forceinline__ void signed_small_multiply(
    const uint64_t (&source)[N], int coefficient, uint64_t (&out)[N]) {
    bool negative = ((int64_t)source[N - 1]) < 0;
    uint64_t magnitude[N];
    #pragma unroll
    for (int i = 0; i < N; ++i) magnitude[i] = source[i];
    if (negative) negate_words(magnitude);
    uint64_t multiplier = coefficient < 0 ? (uint64_t)(-coefficient) : (uint64_t)coefficient;
    uint64_t carry = 0ULL;
    #pragma unroll
    for (int i = 0; i < N; ++i) {
        uint64_t low = magnitude[i] * multiplier;
        uint64_t high = __umul64hi(magnitude[i], multiplier);
        uint64_t next = low + carry;
        high += (next < low);
        out[i] = next;
        carry = high;
    }
    if (negative ^ (coefficient < 0)) negate_words(out);
}

template<int A, int B, int O>
__device__ __forceinline__ void signed_product(
    const uint64_t (&left_in)[A], const uint64_t (&right_in)[B],
    uint64_t (&out)[O]) {
    clear_words(out);
    bool left_negative = ((int64_t)left_in[A - 1]) < 0;
    bool right_negative = ((int64_t)right_in[B - 1]) < 0;
    uint64_t left[A], right[B];
    #pragma unroll
    for (int i = 0; i < A; ++i) left[i] = left_in[i];
    #pragma unroll
    for (int i = 0; i < B; ++i) right[i] = right_in[i];
    if (left_negative) negate_words(left);
    if (right_negative) negate_words(right);
    #pragma unroll
    for (int i = 0; i < A; ++i) {
        #pragma unroll
        for (int j = 0; j < B && i + j < O; ++j) {
            int position = i + j;
            uint64_t low = left[i] * right[j];
            uint64_t high = __umul64hi(left[i], right[j]);
            uint64_t previous = out[position];
            out[position] += low;
            uint64_t carry = out[position] < previous;
            ++position;
            if (position < O) {
                previous = out[position];
                out[position] += high;
                uint64_t propagate = out[position] < previous;
                previous = out[position];
                out[position] += carry;
                propagate |= out[position] < previous;
                ++position;
                while (propagate && position < O) {
                    previous = out[position];
                    out[position] += 1ULL;
                    propagate = out[position] < previous;
                    ++position;
                }
            }
        }
    }
    if (left_negative ^ right_negative) negate_words(out);
}

__device__ __forceinline__ uint64_t choose_small(int n, int k) {
    if (k < 0 || k > n) return 0ULL;
    if (k > n - k) k = n - k;
    uint64_t value = 1ULL;
    for (int i = 1; i <= k; ++i) value = value * (uint64_t)(n - k + i) / (uint64_t)i;
    return value;
}

__device__ __forceinline__ uint64_t colex_rank_mask(uint64_t mask) {
    uint64_t rank = 0ULL;
    int index = 1;
    for (int card = 0; card < 63; ++card) {
        if (mask & (1ULL << card)) {
            rank += choose_small(card, index);
            ++index;
        }
    }
    return rank;
}

__device__ __forceinline__ uint64_t colex_unrank_mask(uint64_t rank, int n, int k) {
    uint64_t mask = 0ULL;
    int upper = n - 1;
    for (int index = k; index >= 1; --index) {
        int card = upper;
        while (card >= index - 1 && choose_small(card, index) > rank) --card;
        mask |= 1ULL << card;
        rank -= choose_small(card, index);
        upper = card - 1;
    }
    return mask;
}

__device__ __forceinline__ uint64_t resident_cards_mask(
    const uint8_t *cards, uint64_t rank, int width) {
    uint64_t mask = 0ULL;
    for (int index = 0; index < width; ++index) {
        mask |= 1ULL << cards[rank * (uint64_t)width + index];
    }
    return mask;
}

__device__ __forceinline__ uint64_t level_offset(int n, int level) {
    uint64_t offset = 0ULL;
    for (int k = 0; k < level; ++k) offset += choose_small(n, k);
    return offset;
}

__device__ __forceinline__ uint64_t montgomery_reduce(
    uint64_t low, uint64_t high, uint64_t modulus, uint64_t nprime) {
    uint64_t m = low * nprime;
    uint64_t mn_low = m * modulus;
    uint64_t mn_high = __umul64hi(m, modulus);
    uint64_t sum_low = low + mn_low;
    uint64_t carry = sum_low < low;
    uint64_t value = high + mn_high + carry;
    if (value >= modulus) value -= modulus;
    return value;
}

__device__ __forceinline__ uint64_t montgomery_multiply(
    uint64_t left, uint64_t right, uint64_t modulus, uint64_t nprime) {
    return montgomery_reduce(left * right, __umul64hi(left, right), modulus, nprime);
}

__device__ __forceinline__ uint64_t residue_add(
    uint64_t left, uint64_t right, uint64_t modulus) {
    uint64_t value = left + right;
    if (value < left || value >= modulus) value -= modulus;
    return value;
}

__device__ __forceinline__ uint64_t residue_subtract(
    uint64_t left, uint64_t right, uint64_t modulus) {
    return left >= right ? left - right : modulus - (right - left);
}

__device__ __forceinline__ bool decode_component(
    double value, uint64_t *mantissa, int *exponent, bool *negative,
    int window_minimum, int window_maximum, int *status) {
    union { double floating; uint64_t bits; } decoded;
    decoded.floating = value;
    uint64_t fraction = decoded.bits & ((1ULL << 52) - 1ULL);
    int exponent_bits = (int)((decoded.bits >> 52) & 0x7ffULL);
    if (exponent_bits == 0x7ff) {
        atomicCAS(status, 0, 2);
        return false;
    }
    if (exponent_bits == 0 && fraction == 0ULL) return false;
    uint64_t value_mantissa = exponent_bits
        ? fraction | (1ULL << 52) : fraction;
    int value_exponent = exponent_bits ? exponent_bits - 1023 - 52 : -1074;
    int trailing = __ffsll((long long)value_mantissa) - 1;
    value_mantissa >>= trailing;
    value_exponent += trailing;
    if (value_exponent < window_minimum || value_exponent > window_maximum) {
        atomicCAS(status, 0, 3);
        return false;
    }
    *mantissa = value_mantissa;
    *exponent = value_exponent;
    *negative = (decoded.bits >> 63) != 0ULL;
    return true;
}

__device__ __forceinline__ void encode_pair_positional(
    double high, double low, uint64_t (&total)[5], int family_exponent,
    int window_minimum, int window_maximum, int *status) {
    double values[2] = {high, low};
    for (int component = 0; component < 2; ++component) {
        uint64_t mantissa = 0ULL;
        int exponent = 0;
        bool negative = false;
        if (!decode_component(
                values[component], &mantissa, &exponent, &negative,
                window_minimum, window_maximum, status)) continue;
        int shift = exponent - family_exponent;
        if (shift < 0 || shift >= 320) {
            atomicCAS(status, 0, 4);
            continue;
        }
        uint64_t encoded[5]; clear_words(encoded);
        int word = shift >> 6;
        int bit = shift & 63;
        encoded[word] |= mantissa << bit;
        if (bit) {
            uint64_t upper = mantissa >> (64 - bit);
            if (word + 1 < 5) encoded[word + 1] |= upper;
            else if (upper) { atomicCAS(status, 0, 4); continue; }
        }
        if (negative) negate_words(encoded);
        add_in_place(total, encoded);
    }
}

// Encoding modes: 0 scans canonical exponents over raw rows, 1 encodes raw
// source rows, 2 encodes and aggregates six query covectors, and 3 encodes
// and aggregates six query weights.  Modes 2 and 3 validate the literal
// label set {0,...,5} independently inside this arm.
extern "C" __global__ void positional_encode_aggregate(
    const double *high, const double *low, const int *labels, uint64_t *output,
    long long logical_rows, int width, int limbs, int family_exponent,
    int window_minimum, int window_maximum, int mode, int *family_minimum,
    int *status) {
    long long item = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    long long count = logical_rows * (long long)width;
    if (item >= count) return;
    if (limbs != 5) { atomicCAS(status, 0, 1); return; }
    if (mode == 0) {
        double values[2] = {high[item], low[item]};
        for (int component = 0; component < 2; ++component) {
            uint64_t mantissa = 0ULL;
            int exponent = 0;
            bool negative = false;
            if (decode_component(
                    values[component], &mantissa, &exponent, &negative,
                    window_minimum, window_maximum, status)) {
                atomicMin(family_minimum, exponent);
            }
        }
        return;
    }
    if (mode < 1 || mode > 3) { atomicCAS(status, 0, 5); return; }
    int records = mode >= 2 ? 6 : 1;
    uint64_t total[5]; clear_words(total);
    int label_mask = 0;
    for (int record = 0; record < records; ++record) {
        long long source_item = mode >= 2
            ? ((item / width) * 6LL + record) * width + item % width
            : item;
        if (mode >= 2 && item % width == 0) {
            int label = labels[(item / width) * 6LL + record];
            if (label < 0 || label >= 6 || (label_mask & (1 << label))) {
                atomicCAS(status, 0, 6);
            } else {
                label_mask |= 1 << label;
            }
        }
        encode_pair_positional(
            high[source_item], low[source_item], total, family_exponent,
            window_minimum, window_maximum, status);
    }
    if (mode >= 2 && item % width == 0 && label_mask != 63) {
        atomicCAS(status, 0, 6);
    }
    store_words(output + item * 5LL, total);
}

__device__ __forceinline__ void positional_level_impl(
    uint64_t *levels, int n, int level, int width, int descending) {
    uint64_t rows = choose_small(n, level);
    uint64_t item = (uint64_t)blockDim.x * blockIdx.x + threadIdx.x;
    if (item >= rows * (uint64_t)width) return;
    uint64_t rank = item / (uint64_t)width;
    int feature = (int)(item % (uint64_t)width);
    uint64_t mask = colex_unrank_mask(rank, n, level);
    uint64_t total[5]; clear_words(total);
    for (int step = 0; step < n; ++step) {
        int card = descending ? n - 1 - step : step;
        if (mask & (1ULL << card)) continue;
        uint64_t child_rank = colex_rank_mask(mask | (1ULL << card));
        uint64_t child_index = (level_offset(n, level + 1) + child_rank) * width + feature;
        uint64_t child[5]; load_words(levels + child_index * 5ULL, child);
        add_in_place(total, child);
    }
    uint64_t target = (level_offset(n, level) + rank) * width + feature;
    store_words(levels + target * 5ULL, total);
}

extern "C" __global__ void positional_forward_level(
    uint64_t *levels, const double *source_high, const double *source_low,
    int n, int level, int width, int family_exponent,
    int window_minimum, int window_maximum, int descending, int *status) {
    uint64_t rows = choose_small(n, level);
    uint64_t item = (uint64_t)blockDim.x * blockIdx.x + threadIdx.x;
    if (item >= rows * (uint64_t)width) return;
    uint64_t rank = item / (uint64_t)width;
    int feature = (int)(item % (uint64_t)width);
    uint64_t mask = colex_unrank_mask(rank, n, level);
    uint64_t total[5]; clear_words(total);
    for (int step = 0; step < n; ++step) {
        int card = descending ? n - 1 - step : step;
        if (mask & (1ULL << card)) continue;
        uint64_t child_rank = colex_rank_mask(mask | (1ULL << card));
        uint64_t child[5];
        if (level == 5) {
            clear_words(child);
            uint64_t source_item = child_rank * (uint64_t)width + feature;
            encode_pair_positional(
                source_high[source_item], source_low[source_item], child,
                family_exponent, window_minimum, window_maximum, status);
        } else {
            uint64_t child_index = (level_offset(n, level + 1) + child_rank)
                * width + feature;
            load_words(levels + child_index * 5ULL, child);
        }
        add_in_place(total, child);
    }
    uint64_t target = (level_offset(n, level) + rank) * width + feature;
    store_words(levels + target * 5ULL, total);
}

template<bool ADJOINT>
__device__ __forceinline__ void positional_signed_row(
    const uint64_t *levels, uint64_t mask, int n, int width, int feature,
    int descending, uint64_t (&total)[5]) {
    clear_words(total);
    int maximum = ADJOINT ? 4 : 4;
    uint64_t subset = descending ? mask : 0ULL;
    while (true) {
        int level = __popcll(subset);
        if (level <= maximum) {
            int coefficient;
            if (ADJOINT) {
                const int weights[5] = {30, 120, 360, 720, 720};
                coefficient = weights[level];
            } else {
                const int weights[5] = {1, 6, 30, 120, 360};
                coefficient = weights[level];
            }
            if (level & 1) coefficient = -coefficient;
            uint64_t rank = colex_rank_mask(subset);
            uint64_t index = (level_offset(n, level) + rank) * width + feature;
            uint64_t row[5], scaled[5];
            load_words(levels + index * 5ULL, row);
            signed_small_multiply(row, coefficient, scaled);
            add_in_place(total, scaled);
        }
        if (descending) {
            if (subset == 0ULL) break;
            subset = (subset - 1ULL) & mask;
        } else {
            if (subset == mask) break;
            subset = (subset - mask) & mask;
        }
    }
}

extern "C" __global__ void positional_forward_stream(
    const uint64_t *levels, uint64_t *output, int n, int width,
    uint64_t row_start, uint64_t row_count, int descending) {
    uint64_t item = (uint64_t)blockDim.x * blockIdx.x + threadIdx.x;
    if (item >= row_count * (uint64_t)width) return;
    uint64_t rank = row_start + item / (uint64_t)width;
    int feature = (int)(item % (uint64_t)width);
    uint64_t mask = colex_unrank_mask(rank, n, 4);
    uint64_t total[5];
    positional_signed_row<false>(levels, mask, n, width, feature, descending, total);
    store_words(output + item * 5ULL, total);
}

extern "C" __global__ void positional_forward_selective(
    const uint64_t *levels, const uint64_t *masks, const int *features,
    uint64_t *output, int count, int n, int width, int descending) {
    int item = blockDim.x * blockIdx.x + threadIdx.x;
    if (item >= count) return;
    uint64_t total[5];
    positional_signed_row<false>(
        levels, masks[item], n, width, features[item], descending, total);
    store_words(output + (uint64_t)item * 5ULL, total);
}

extern "C" __global__ void positional_adjoint_level(
    uint64_t *levels, int n, int level, int width, int descending) {
    positional_level_impl(levels, n, level, width, descending);
}

extern "C" __global__ void positional_adjoint_stream(
    const uint64_t *levels, const uint8_t *source_cards, uint64_t *output,
    int n, int width,
    uint64_t row_start, uint64_t row_count, int descending) {
    uint64_t item = (uint64_t)blockDim.x * blockIdx.x + threadIdx.x;
    if (item >= row_count * (uint64_t)width) return;
    uint64_t rank = row_start + item / (uint64_t)width;
    int feature = (int)(item % (uint64_t)width);
    uint64_t mask = resident_cards_mask(source_cards, rank, 6);
    uint64_t total[5];
    positional_signed_row<true>(levels, mask, n, width, feature, descending, total);
    store_words(output + item * 5ULL, total);
}

extern "C" __global__ void positional_adjoint_selective(
    const uint64_t *levels, const uint64_t *masks, const int *features,
    uint64_t *output, int count, int n, int width, int descending) {
    int item = blockDim.x * blockIdx.x + threadIdx.x;
    if (item >= count) return;
    uint64_t total[5];
    positional_signed_row<true>(
        levels, masks[item], n, width, features[item], descending, total);
    store_words(output + (uint64_t)item * 5ULL, total);
}

extern "C" __global__ void positional_contract(
    const uint64_t *left, const uint64_t *right, const uint64_t *weights,
    const double *source_high, const double *source_low,
    uint64_t *numerator, uint64_t *reach, long long rows, int width,
    int reach_feature, int mode, int source_family_exponent,
    int window_minimum, int window_maximum, int *status) {
    if (blockIdx.x || threadIdx.x) return;
    uint64_t total[8]; clear_words(total);
    uint64_t reach_total[7]; clear_words(reach_total);
    for (long long row = 0; row < rows; ++row) {
        for (int feature = 0; feature < width; ++feature) {
            uint64_t a[5], b[5], product[8];
            if (mode == 0) {
                load_words(left + (row * width + feature) * 5LL, a);
            } else {
                clear_words(a);
                encode_pair_positional(
                    source_high[row * width + feature],
                    source_low[row * width + feature], a,
                    source_family_exponent, window_minimum, window_maximum,
                    status);
            }
            load_words(right + (row * width + feature) * 5LL, b);
            signed_product<5, 5, 8>(a, b, product);
            add_in_place(total, product);
        }
        if (mode == 0) {
            uint64_t a[5], b[5], product[7];
            load_words(left + (row * width + reach_feature) * 5LL, a);
            load_words(weights + row * 5LL, b);
            signed_product<5, 5, 7>(a, b, product);
            add_in_place(reach_total, product);
        }
    }
    store_words(numerator, total);
    store_words(reach, reach_total);
}

__device__ __forceinline__ uint64_t encode_pair_rrns(
    double high, double low, int family_exponent,
    int window_minimum, int window_maximum, uint64_t modulus,
    uint64_t nprime, uint64_t r2, int *status) {
    uint64_t total = 0ULL;
    double values[2] = {high, low};
    for (int component = 0; component < 2; ++component) {
        uint64_t mantissa = 0ULL;
        int exponent = 0;
        bool negative = false;
        if (!decode_component(
                values[component], &mantissa, &exponent, &negative,
                window_minimum, window_maximum, status)) continue;
        int shift = exponent - family_exponent;
        if (shift < 0) { atomicCAS(status, 0, 4); continue; }
        uint64_t standard = mantissa % modulus;
        for (int bit = 0; bit < shift; ++bit) {
            standard = residue_add(standard, standard, modulus);
        }
        if (negative && standard) standard = modulus - standard;
        uint64_t montgomery = montgomery_multiply(
            standard, r2, modulus, nprime);
        total = residue_add(total, montgomery, modulus);
    }
    return total;
}

extern "C" __global__ void rrns_encode_aggregate(
    const double *high, const double *low, const int *labels,
    uint64_t *output, long long logical_rows, int width,
    int family_exponent, int window_minimum, int window_maximum, int mode,
    const uint64_t *moduli, const uint64_t *nprimes, const uint64_t *r2,
    const int *channel_indices, int channel_count, int *family_minimum,
    int *status) {
    long long item = (long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (mode == 0) {
        long long count = logical_rows * (long long)width;
        if (item >= count) return;
        double values[2] = {high[item], low[item]};
        for (int component = 0; component < 2; ++component) {
            uint64_t mantissa = 0ULL;
            int exponent = 0;
            bool negative = false;
            if (decode_component(
                    values[component], &mantissa, &exponent, &negative,
                    window_minimum, window_maximum, status)) {
                atomicMin(family_minimum, exponent);
            }
        }
        return;
    }
    if (mode < 1 || mode > 3 || channel_count <= 0) {
        if (item == 0) atomicCAS(status, 0, 5);
        return;
    }
    long long count = logical_rows * (long long)width * channel_count;
    if (item >= count) return;
    int local_channel = (int)(item % channel_count);
    long long value_index = item / channel_count;
    int channel = channel_indices[local_channel];
    uint64_t modulus = moduli[channel];
    int records = mode >= 2 ? 6 : 1;
    uint64_t total = 0ULL;
    int label_mask = 0;
    for (int record = 0; record < records; ++record) {
        long long source_item = mode >= 2
            ? ((value_index / width) * 6LL + record) * width
                + value_index % width
            : value_index;
        if (mode >= 2 && local_channel == 0 && value_index % width == 0) {
            int label = labels[(value_index / width) * 6LL + record];
            if (label < 0 || label >= 6 || (label_mask & (1 << label))) {
                atomicCAS(status, 0, 6);
            } else {
                label_mask |= 1 << label;
            }
        }
        uint64_t encoded = encode_pair_rrns(
            high[source_item], low[source_item], family_exponent,
            window_minimum, window_maximum, modulus, nprimes[channel],
            r2[channel], status);
        total = residue_add(total, encoded, modulus);
    }
    if (mode >= 2 && local_channel == 0 && value_index % width == 0
            && label_mask != 63) {
        atomicCAS(status, 0, 6);
    }
    output[value_index * channel_count + local_channel] = total;
}

__device__ __forceinline__ void rrns_level_impl(
    uint64_t *levels, const double *source_high, const double *source_low,
    int n, int level, int width, int channels, int family_exponent,
    int window_minimum, int window_maximum, const uint64_t *moduli,
    const uint64_t *nprimes, const uint64_t *r2,
    const int *channel_indices, int descending, int *status) {
    uint64_t rows = choose_small(n, level);
    uint64_t item = (uint64_t)blockDim.x * blockIdx.x + threadIdx.x;
    uint64_t count = rows * (uint64_t)width * channels;
    if (item >= count) return;
    int channel_local = (int)(item % channels);
    uint64_t quotient = item / channels;
    int feature = (int)(quotient % width);
    uint64_t rank = quotient / width;
    int channel = channel_indices[channel_local];
    uint64_t modulus = moduli[channel];
    uint64_t mask = colex_unrank_mask(rank, n, level);
    uint64_t total = 0ULL;
    for (int step = 0; step < n; ++step) {
        int card = descending ? n - 1 - step : step;
        if (mask & (1ULL << card)) continue;
        uint64_t child_rank = colex_rank_mask(mask | (1ULL << card));
        uint64_t child;
        if (level == 5) {
            uint64_t source_item = child_rank * (uint64_t)width + feature;
            child = encode_pair_rrns(
                source_high[source_item], source_low[source_item],
                family_exponent, window_minimum, window_maximum, modulus,
                nprimes[channel], r2[channel], status);
        } else {
            uint64_t index = ((level_offset(n, level + 1) + child_rank) * width
                + feature) * channels + channel_local;
            child = levels[index];
        }
        total = residue_add(total, child, modulus);
    }
    uint64_t target = ((level_offset(n, level) + rank) * width + feature)
        * channels + channel_local;
    levels[target] = total;
}

extern "C" __global__ void rrns_forward_level(
    uint64_t *levels, const double *source_high, const double *source_low,
    int n, int level, int width, int channels, int family_exponent,
    int window_minimum, int window_maximum, const uint64_t *moduli,
    const uint64_t *nprimes, const uint64_t *r2,
    const int *channel_indices, int descending, int *status) {
    rrns_level_impl(
        levels, source_high, source_low, n, level, width, channels,
        family_exponent, window_minimum, window_maximum, moduli, nprimes, r2,
        channel_indices, descending, status);
}

template<bool ADJOINT>
__device__ __forceinline__ uint64_t rrns_signed_row(
    const uint64_t *levels, uint64_t mask, int n, int width, int feature,
    int channels, int channel_local, int channel, const uint64_t *moduli,
    int descending) {
    uint64_t modulus = moduli[channel];
    uint64_t total = 0ULL;
    uint64_t subset = descending ? mask : 0ULL;
    while (true) {
        int level = __popcll(subset);
        if (level <= 4) {
            int coefficient;
            if (ADJOINT) {
                const int weights[5] = {30, 120, 360, 720, 720};
                coefficient = weights[level];
            } else {
                const int weights[5] = {1, 6, 30, 120, 360};
                coefficient = weights[level];
            }
            uint64_t rank = colex_rank_mask(subset);
            uint64_t index = ((level_offset(n, level) + rank) * width + feature) * channels + channel_local;
            uint64_t value = levels[index];
            uint64_t scaled = 0ULL;
            int magnitude = coefficient < 0 ? -coefficient : coefficient;
            for (int bit = 0; bit < 10; ++bit) {
                if (magnitude & (1 << bit)) scaled = residue_add(scaled, value, modulus);
                value = residue_add(value, value, modulus);
            }
            total = (level & 1) ? residue_subtract(total, scaled, modulus) : residue_add(total, scaled, modulus);
        }
        if (descending) {
            if (subset == 0ULL) break;
            subset = (subset - 1ULL) & mask;
        } else {
            if (subset == mask) break;
            subset = (subset - mask) & mask;
        }
    }
    return total;
}

extern "C" __global__ void rrns_forward_stream(
    const uint64_t *levels, uint64_t *output, int n, int width, int channels,
    const uint64_t *moduli, const int *channel_indices,
    uint64_t row_start, uint64_t row_count, int descending) {
    uint64_t item = (uint64_t)blockDim.x * blockIdx.x + threadIdx.x;
    uint64_t count = row_count * (uint64_t)width * channels;
    if (item >= count) return;
    int channel_local = (int)(item % channels);
    uint64_t quotient = item / channels;
    int feature = (int)(quotient % width);
    uint64_t rank = row_start + quotient / width;
    int channel = channel_indices[channel_local];
    uint64_t mask = colex_unrank_mask(rank, n, 4);
    output[item] = rrns_signed_row<false>(levels, mask, n, width, feature, channels, channel_local, channel, moduli, descending);
}

extern "C" __global__ void rrns_forward_selective(
    const uint64_t *levels, const uint64_t *masks, const int *features,
    uint64_t *output, int count, int n, int width, int channels,
    const uint64_t *moduli, const int *channel_indices, int descending) {
    int item = blockDim.x * blockIdx.x + threadIdx.x;
    if (item >= count * channels) return;
    int channel_local = item % channels;
    int row = item / channels;
    int channel = channel_indices[channel_local];
    output[item] = rrns_signed_row<false>(levels, masks[row], n, width, features[row], channels, channel_local, channel, moduli, descending);
}

extern "C" __global__ void rrns_adjoint_level(
    uint64_t *levels, int n, int level, int width, int channels,
    const uint64_t *moduli, const int *channel_indices, int descending) {
    uint64_t rows = choose_small(n, level);
    uint64_t item = (uint64_t)blockDim.x * blockIdx.x + threadIdx.x;
    uint64_t count = rows * (uint64_t)width * channels;
    if (item >= count) return;
    int channel_local = (int)(item % channels);
    uint64_t quotient = item / channels;
    int feature = (int)(quotient % width);
    uint64_t rank = quotient / width;
    int channel = channel_indices[channel_local];
    uint64_t modulus = moduli[channel];
    uint64_t mask = colex_unrank_mask(rank, n, level);
    uint64_t total = 0ULL;
    for (int step = 0; step < n; ++step) {
        int card = descending ? n - 1 - step : step;
        if (mask & (1ULL << card)) continue;
        uint64_t child_rank = colex_rank_mask(mask | (1ULL << card));
        uint64_t index = ((level_offset(n, level + 1) + child_rank) * width
            + feature) * channels + channel_local;
        total = residue_add(total, levels[index], modulus);
    }
    uint64_t target = ((level_offset(n, level) + rank) * width + feature)
        * channels + channel_local;
    levels[target] = total;
}

extern "C" __global__ void rrns_adjoint_stream(
    const uint64_t *levels, const uint8_t *source_cards, uint64_t *output,
    int n, int width, int channels,
    const uint64_t *moduli, const int *channel_indices,
    uint64_t row_start, uint64_t row_count, int descending) {
    uint64_t item = (uint64_t)blockDim.x * blockIdx.x + threadIdx.x;
    uint64_t count = row_count * (uint64_t)width * channels;
    if (item >= count) return;
    int channel_local = (int)(item % channels);
    uint64_t quotient = item / channels;
    int feature = (int)(quotient % width);
    uint64_t rank = row_start + quotient / width;
    int channel = channel_indices[channel_local];
    uint64_t mask = resident_cards_mask(source_cards, rank, 6);
    output[item] = rrns_signed_row<true>(levels, mask, n, width, feature, channels, channel_local, channel, moduli, descending);
}

extern "C" __global__ void rrns_adjoint_selective(
    const uint64_t *levels, const uint64_t *masks, const int *features,
    uint64_t *output, int count, int n, int width, int channels,
    const uint64_t *moduli, const int *channel_indices, int descending) {
    int item = blockDim.x * blockIdx.x + threadIdx.x;
    if (item >= count * channels) return;
    int channel_local = item % channels;
    int row = item / channels;
    int channel = channel_indices[channel_local];
    output[item] = rrns_signed_row<true>(levels, masks[row], n, width, features[row], channels, channel_local, channel, moduli, descending);
}

extern "C" __global__ void rrns_contract(
    const uint64_t *left, const uint64_t *right, const uint64_t *weights,
    const double *source_high, const double *source_low,
    uint64_t *numerator, uint64_t *reach, long long rows, int width,
    int reach_feature, int channels, const uint64_t *moduli,
    const uint64_t *nprimes, const uint64_t *r2,
    const int *channel_indices, int mode, int source_family_exponent,
    int window_minimum, int window_maximum, int *status) {
    int local = blockDim.x * blockIdx.x + threadIdx.x;
    if (local >= channels) return;
    int channel = channel_indices[local];
    uint64_t modulus = moduli[channel];
    uint64_t total = 0ULL;
    uint64_t reach_total = 0ULL;
    for (long long row = 0; row < rows; ++row) {
        for (int feature = 0; feature < width; ++feature) {
            uint64_t a = mode == 0
                ? left[(row * width + feature) * channels + local]
                : encode_pair_rrns(
                    source_high[row * width + feature],
                    source_low[row * width + feature], source_family_exponent,
                    window_minimum, window_maximum, modulus,
                    nprimes[channel], r2[channel], status);
            uint64_t b = right[(row * width + feature) * channels + local];
            total = residue_add(total, montgomery_multiply(a, b, modulus, nprimes[channel]), modulus);
        }
        if (mode == 0) {
            uint64_t a = left[(row * width + reach_feature) * channels + local];
            uint64_t b = weights[row * channels + local];
            reach_total = residue_add(reach_total, montgomery_multiply(a, b, modulus, nprimes[channel]), modulus);
        }
    }
    numerator[local] = total;
    reach[local] = reach_total;
}
'''

CUDA_SOURCE_SHA256 = sha256(CUDA_SOURCE.encode("utf-8")).hexdigest()


def cuda_source_contract() -> dict[str, object]:
    """Return source-only facts without compiling or importing a device stack."""

    global_names = tuple(
        re.findall(
            r'extern\s+"C"\s+__global__\s+void\s+([A-Za-z0-9_]+)\s*\(',
            CUDA_SOURCE,
        )
    )
    if len(global_names) != len(KERNEL_NAMES) or set(global_names) != set(KERNEL_NAMES):
        raise ValueError("CUDA entry-kernel inventory differs")
    forbidden = ("fast_math", "inverse_720", "pow(720", "cupy", "numpy")
    if any(token in CUDA_SOURCE.lower() for token in forbidden):
        raise ValueError("CUDA source contains a forbidden semantic token")
    return {
        "cuda_source_sha256": CUDA_SOURCE_SHA256,
        "cuda_source_bytes": len(CUDA_SOURCE.encode("utf-8")),
        "kernel_names": list(KERNEL_NAMES),
        "compiler_options": list(NVCC_OPTIONS),
    }


def _serialize_dataclass_rows(rows: Mapping[str, object]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in rows.items():
        if hasattr(value, "__dataclass_fields__"):
            output[key] = asdict(value)
        else:
            raise TypeError("resource evidence contains an unknown concrete type")
    return output


def _launch_device(
    kernel: object,
    total: int,
    arguments: tuple[object, ...],
    stream: object,
) -> None:
    count = _require_plain_int(total, label="device launch count", minimum=1)
    with stream:
        kernel.linear_launch(
            count,
            arguments,
            shared_mem=0,
            block_max_size=BLOCK_THREADS,
        )


def _append_synchronized_stamp(stream: object, stamps: list[int]) -> None:
    stream.synchronize()
    stamps.append(perf_counter_ns())


def _device_u64_bytes(cp: Any, value: object) -> bytes:
    host = cp.asnumpy(value)
    return host.astype("<u8", copy=False).tobytes(order="C")


def _window_rows() -> dict[str, tuple[int, int]]:
    parent = json.loads(
        (
            _ROOT
            / "experiments/configs/"
            "legal-river-quotient-fixed-width-work-comparison-v1.json"
        ).read_text(encoding="utf-8")
    )
    raw = parent["fixed_width_admission"]["known_control_only_windows"]
    return {name: (int(value[0]), int(value[1])) for name, value in raw.items()}


def _run_positional_candidate(
    context: CompiledDeviceContext,
    population: ValidationPopulation,
    *,
    descending: bool,
    expected: Mapping[str, bytes],
    start_ns: int | None = None,
) -> dict[str, object]:
    cp = context.cp
    import numpy as np
    from math import comb

    authority = population.authority
    cards = authority.available_cards
    width = authority.feature_width
    source_rows = len(authority.source_rows)
    query_rows = len(authority.aggregated_query_covectors)
    labeled_rows = population.query_high.shape[0]
    windows = _window_rows()
    kernels = context.kernels
    stream = context.streams[POSITIONAL]
    stamps = [
        perf_counter_ns()
        if start_ns is None
        else _require_plain_int(start_ns, label="candidate start", minimum=0)
    ]
    if population.input_sha256 != population.input_sha256.lower():
        raise AssertionError("population input digest is not canonical")
    _append_synchronized_stamp(stream, stamps)

    with stream:
        source_high = cp.asarray(population.source_high)
        source_low = cp.asarray(population.source_low)
        query_high = cp.asarray(population.query_high)
        query_low = cp.asarray(population.query_low)
        weight_high = cp.asarray(population.weight_high)
        weight_low = cp.asarray(population.weight_low)
        labels = cp.asarray(population.query_labels)
        source_cards = cp.asarray(population.source_cards)
        dummy_labels = cp.zeros(1, dtype=cp.int32)
        status = cp.zeros(1, dtype=cp.int32)
        family_minima = {
            name: cp.full(1, 2_147_483_647, dtype=cp.int32)
            for name in windows
        }
        source_encoded = cp.empty(source_rows * width * 5, dtype=cp.uint64)
        covectors = cp.empty(query_rows * width * 5, dtype=cp.uint64)
        weights = cp.empty(query_rows * 5, dtype=cp.uint64)
        forward_level_rows = sum(comb(cards, level) for level in range(6))
        adjoint_level_rows = sum(comb(cards, level) for level in range(5))
        forward_levels = cp.zeros(forward_level_rows * width * 5, dtype=cp.uint64)
        adjoint_levels = cp.zeros(adjoint_level_rows * width * 5, dtype=cp.uint64)
        forward_selected = cp.empty(4 * 5, dtype=cp.uint64)
        adjoint_selected = cp.empty(4 * 5, dtype=cp.uint64)
        forward_stream = cp.empty(query_rows * width * 5, dtype=cp.uint64)
        adjoint_stream = cp.empty(source_rows * width * 5, dtype=cp.uint64)
        numerator = cp.zeros(8, dtype=cp.uint64)
        reach = cp.zeros(7, dtype=cp.uint64)
        adjoint_numerator = cp.zeros(8, dtype=cp.uint64)
        unused_reach = cp.zeros(7, dtype=cp.uint64)
        forward_ranks, forward_features, adjoint_ranks, adjoint_features = (
            _selected_coordinates(population)
        )
        forward_masks = cp.asarray(
            np.asarray(
                [authority.forward_scaled_rows[rank][0] for rank in forward_ranks],
                dtype=np.uint64,
            )
        )
        forward_feature_array = cp.asarray(
            np.asarray(forward_features, dtype=np.int32)
        )
        adjoint_masks = cp.asarray(
            np.asarray(
                [authority.adjoint_scaled_rows[rank][0] for rank in adjoint_ranks],
                dtype=np.uint64,
            )
        )
        adjoint_feature_array = cp.asarray(
            np.asarray(adjoint_features, dtype=np.int32)
        )
    _append_synchronized_stamp(stream, stamps)

    families = (
        (
            "source_rows",
            source_high,
            source_low,
            dummy_labels,
            source_encoded,
            source_rows,
            width,
            authority.source_family_exponent,
            1,
        ),
        (
            "labeled_query_covectors",
            query_high,
            query_low,
            labels,
            covectors,
            query_rows,
            width,
            authority.covector_family_exponent,
            2,
        ),
        (
            "labeled_query_weights",
            weight_high,
            weight_low,
            labels,
            weights,
            query_rows,
            1,
            authority.weight_family_exponent,
            3,
        ),
    )
    for name, high, low, family_labels, output, logical_rows, family_width, exponent, mode in families:
        raw_rows = source_rows if mode == 1 else labeled_rows
        low_window, high_window = windows[name]
        _launch_device(
            kernels["positional_encode_aggregate"],
            raw_rows * family_width,
            (
                high,
                low,
                family_labels,
                output,
                np.int64(raw_rows),
                np.int32(family_width),
                np.int32(5),
                np.int32(exponent),
                np.int32(low_window),
                np.int32(high_window),
                np.int32(0),
                family_minima[name],
                status,
            ),
            stream,
        )
        _launch_device(
            kernels["positional_encode_aggregate"],
            logical_rows * family_width,
            (
                high,
                low,
                family_labels,
                output,
                np.int64(logical_rows),
                np.int32(family_width),
                np.int32(5),
                np.int32(exponent),
                np.int32(low_window),
                np.int32(high_window),
                np.int32(mode),
                family_minima[name],
                status,
            ),
            stream,
        )
    level_four_offset = sum(comb(cards, level) for level in range(4))
    with stream:
        adjoint_levels[
            level_four_offset * width * 5 : (level_four_offset + query_rows)
            * width
            * 5
        ] = covectors
    stream.synchronize()
    observed_status = int(cp.asnumpy(status)[0])
    observed_minima = {
        name: int(cp.asnumpy(value)[0]) for name, value in family_minima.items()
    }
    expected_minima = {
        "source_rows": authority.source_family_exponent,
        "labeled_query_covectors": authority.covector_family_exponent,
        "labeled_query_weights": authority.weight_family_exponent,
    }
    if observed_status != 0 or observed_minima != expected_minima:
        raise DevicePreflightFailure(
            "positional_admission_rejection",
            f"positional status/minima differ: {observed_status}/{observed_minima}",
        )
    stamps.append(perf_counter_ns())

    direction = np.int32(1 if descending else 0)
    source_window = windows["source_rows"]
    for level in range(5, -1, -1):
        _launch_device(
            kernels["positional_forward_level"],
            comb(cards, level) * width,
            (
                forward_levels,
                source_high,
                source_low,
                np.int32(cards),
                np.int32(level),
                np.int32(width),
                np.int32(authority.source_family_exponent),
                np.int32(source_window[0]),
                np.int32(source_window[1]),
                direction,
                status,
            ),
            stream,
        )
    _append_synchronized_stamp(stream, stamps)

    _launch_device(
        kernels["positional_forward_selective"],
        4,
        (
            forward_levels,
            forward_masks,
            forward_feature_array,
            forward_selected,
            np.int32(4),
            np.int32(cards),
            np.int32(width),
            direction,
        ),
        stream,
    )
    _append_synchronized_stamp(stream, stamps)

    _launch_device(
        kernels["positional_forward_stream"],
        query_rows * width,
        (
            forward_levels,
            forward_stream,
            np.int32(cards),
            np.int32(width),
            np.uint64(0),
            np.uint64(query_rows),
            direction,
        ),
        stream,
    )
    _launch_device(
        kernels["positional_contract"],
        1,
        (
            forward_stream,
            covectors,
            weights,
            source_high,
            source_low,
            numerator,
            reach,
            np.int64(query_rows),
            np.int32(width),
            np.int32(population.captured.reach_feature),
            np.int32(0),
            np.int32(authority.source_family_exponent),
            np.int32(source_window[0]),
            np.int32(source_window[1]),
            status,
        ),
        stream,
    )
    _append_synchronized_stamp(stream, stamps)

    for level in range(3, -1, -1):
        _launch_device(
            kernels["positional_adjoint_level"],
            comb(cards, level) * width,
            (
                adjoint_levels,
                np.int32(cards),
                np.int32(level),
                np.int32(width),
                direction,
            ),
            stream,
        )
    _append_synchronized_stamp(stream, stamps)

    _launch_device(
        kernels["positional_adjoint_selective"],
        4,
        (
            adjoint_levels,
            adjoint_masks,
            adjoint_feature_array,
            adjoint_selected,
            np.int32(4),
            np.int32(cards),
            np.int32(width),
            direction,
        ),
        stream,
    )
    _append_synchronized_stamp(stream, stamps)

    _launch_device(
        kernels["positional_adjoint_stream"],
        source_rows * width,
        (
            adjoint_levels,
            source_cards,
            adjoint_stream,
            np.int32(cards),
            np.int32(width),
            np.uint64(0),
            np.uint64(source_rows),
            direction,
        ),
        stream,
    )
    _launch_device(
        kernels["positional_contract"],
        1,
        (
            forward_stream,
            adjoint_stream,
            weights,
            source_high,
            source_low,
            adjoint_numerator,
            unused_reach,
            np.int64(source_rows),
            np.int32(width),
            np.int32(population.captured.reach_feature),
            np.int32(1),
            np.int32(authority.source_family_exponent),
            np.int32(source_window[0]),
            np.int32(source_window[1]),
            status,
        ),
        stream,
    )
    _append_synchronized_stamp(stream, stamps)

    numerator_value = words_to_signed_integer(cp.asnumpy(numerator).tolist())
    reach_value = words_to_signed_integer(cp.asnumpy(reach).tolist())
    adjoint_value = words_to_signed_integer(
        cp.asnumpy(adjoint_numerator).tolist()
    )
    from . import legal_river_quotient_exact_integer_operator as exact

    if any(value % 720 for value in (numerator_value, reach_value, adjoint_value)):
        raise DevicePreflightFailure(
            "positional_divisibility_rejection", "scaled positional scalar is not divisible by 720"
        )
    conditional = exact.correctly_rounded_binary64(
        numerator_value,
        reach_value,
        authority.covector_family_exponent - authority.weight_family_exponent,
    )
    if (
        numerator_value != authority.forward_integer_numerator
        or adjoint_value != authority.adjoint_integer_numerator
        or reach_value != authority.forward_integer_reach
        or exact.binary64_bits(conditional) != authority.conditional_value_bits
    ):
        raise DevicePreflightFailure(
            "positional_scalar_differential_rejection",
            "positional scalar or terminal bits differ from authority",
        )
    _append_synchronized_stamp(stream, stamps)

    device_outputs = {
        "source_encoding": source_encoded,
        "aggregated_covectors": covectors,
        "aggregated_weights": weights,
        "forward_levels": forward_levels,
        "forward_selected": forward_selected,
        "forward_stream": forward_stream,
        "adjoint_levels": adjoint_levels,
        "adjoint_selected": adjoint_selected,
        "adjoint_stream": adjoint_stream,
    }
    output_digests = {}
    for name, value in device_outputs.items():
        raw = _device_u64_bytes(cp, value)
        if raw != expected[name]:
            raise DevicePreflightFailure(
                "positional_output_differential_rejection",
                f"positional output differs: {name}",
            )
        output_digests[name] = sha256(raw).hexdigest()
    if int(cp.asnumpy(status)[0]) != 0:
        raise DevicePreflightFailure(
            "positional_status_rejection", "positional device status changed"
        )
    _append_synchronized_stamp(stream, stamps)

    del device_outputs
    del (
        source_high,
        source_low,
        query_high,
        query_low,
        weight_high,
        weight_low,
        labels,
        source_cards,
        source_encoded,
        covectors,
        weights,
        forward_levels,
        adjoint_levels,
        forward_selected,
        adjoint_selected,
        forward_stream,
        adjoint_stream,
        numerator,
        reach,
        adjoint_numerator,
        unused_reach,
        dummy_labels,
        status,
        family_minima,
        forward_masks,
        forward_feature_array,
        adjoint_masks,
        adjoint_feature_array,
        families,
        high,
        low,
        family_labels,
        output,
        value,
    )
    stream.synchronize()
    cp.get_default_memory_pool().free_all_blocks(stream=stream)
    cp.get_default_pinned_memory_pool().free_all_blocks()
    _append_synchronized_stamp(stream, stamps)
    partition = phase_partition(SINGLE_PASS_PHASE_NAMES, stamps)
    return {
        "schema_version": "fixed-width-device-candidate-run-v1",
        "arm": POSITIONAL,
        "population": population.label,
        "traversal_order": "descending_colex" if descending else "ascending_colex",
        "input_sha256": population.input_sha256,
        "phase_partition": {
            "rows": [asdict(row) for row in partition.rows],
            "total_ns": partition.total_ns,
        },
        "output_digests": output_digests,
        "scalar_values_decimal": {
            "forward_numerator": str(numerator_value),
            "adjoint_numerator": str(adjoint_value),
            "reach": str(reach_value),
        },
        "conditional_value_bits": authority.conditional_value_bits,
        "exact_verified": True,
    }


def _run_rrns_candidate(
    context: CompiledDeviceContext,
    population: ValidationPopulation,
    *,
    arm: str,
    descending: bool,
    expected_by_channels: Mapping[tuple[int, ...], Mapping[str, bytes]],
    start_ns: int | None = None,
) -> dict[str, object]:
    if arm == RESIDENT_RRNS:
        batches = ((0, 1, 2, 3, 4, 5, 6, 7, 8),)
    elif arm == BATCHED_RRNS:
        batches = ((0, 1, 2, 3, 8), (4, 5, 6, 7))
    else:
        raise ValueError("RRNS runner received a non-RRNS arm")
    cp = context.cp
    import numpy as np
    from math import comb
    from . import legal_river_quotient_exact_integer_operator as exact
    from . import legal_river_quotient_fixed_width_work_comparison as fixed

    authority = population.authority
    cards = authority.available_cards
    width = authority.feature_width
    source_rows = len(authority.source_rows)
    query_rows = len(authority.aggregated_query_covectors)
    labeled_rows = population.query_high.shape[0]
    forward_level_rows = sum(comb(cards, level) for level in range(6))
    adjoint_level_rows = sum(comb(cards, level) for level in range(5))
    maximum_channels = max(len(batch) for batch in batches)
    windows = _window_rows()
    _, scalar_parameters = fixed.validate_frozen_rrns()
    moduli = scalar_parameters.all_moduli
    constants = tuple(fixed.montgomery_constants(modulus) for modulus in moduli)
    kernels = context.kernels
    stream = context.streams[arm]
    stamps = [
        perf_counter_ns()
        if start_ns is None
        else _require_plain_int(start_ns, label="candidate start", minimum=0)
    ]
    _append_synchronized_stamp(stream, stamps)

    with stream:
        source_high = cp.asarray(population.source_high)
        source_low = cp.asarray(population.source_low)
        query_high = cp.asarray(population.query_high)
        query_low = cp.asarray(population.query_low)
        weight_high = cp.asarray(population.weight_high)
        weight_low = cp.asarray(population.weight_low)
        labels = cp.asarray(population.query_labels)
        source_cards = cp.asarray(population.source_cards)
        dummy_labels = cp.zeros(1, dtype=cp.int32)
        status = cp.zeros(1, dtype=cp.int32)
        family_minima = {
            name: cp.full(1, 2_147_483_647, dtype=cp.int32)
            for name in windows
        }
        moduli_device = cp.asarray(np.asarray(moduli, dtype=np.uint64))
        nprimes_device = cp.asarray(
            np.asarray([row.negative_inverse for row in constants], dtype=np.uint64)
        )
        r2_device = cp.asarray(
            np.asarray([row.r_squared_modulus for row in constants], dtype=np.uint64)
        )
        batch_index_arrays = {
            batch: cp.asarray(np.asarray(batch, dtype=np.int32)) for batch in batches
        }
        source_encoded = cp.empty(
            source_rows * width * maximum_channels, dtype=cp.uint64
        )
        covectors = cp.empty(
            query_rows * width * maximum_channels, dtype=cp.uint64
        )
        weights = cp.empty(query_rows * maximum_channels, dtype=cp.uint64)
        forward_levels = cp.empty(
            forward_level_rows * width * maximum_channels, dtype=cp.uint64
        )
        adjoint_levels = cp.empty(
            adjoint_level_rows * width * maximum_channels, dtype=cp.uint64
        )
        forward_selected = cp.empty(4 * maximum_channels, dtype=cp.uint64)
        adjoint_selected = cp.empty(4 * maximum_channels, dtype=cp.uint64)
        forward_stream = cp.empty(
            query_rows * width * maximum_channels, dtype=cp.uint64
        )
        adjoint_stream = cp.empty(
            source_rows * width * maximum_channels, dtype=cp.uint64
        )
        numerator = cp.empty(maximum_channels, dtype=cp.uint64)
        reach = cp.empty(maximum_channels, dtype=cp.uint64)
        adjoint_numerator = cp.empty(maximum_channels, dtype=cp.uint64)
        unused_reach = cp.empty(maximum_channels, dtype=cp.uint64)
        forward_ranks, forward_features, adjoint_ranks, adjoint_features = (
            _selected_coordinates(population)
        )
        forward_masks = cp.asarray(
            np.asarray(
                [authority.forward_scaled_rows[rank][0] for rank in forward_ranks],
                dtype=np.uint64,
            )
        )
        forward_feature_array = cp.asarray(
            np.asarray(forward_features, dtype=np.int32)
        )
        adjoint_masks = cp.asarray(
            np.asarray(
                [authority.adjoint_scaled_rows[rank][0] for rank in adjoint_ranks],
                dtype=np.uint64,
            )
        )
        adjoint_feature_array = cp.asarray(
            np.asarray(adjoint_features, dtype=np.int32)
        )
    _append_synchronized_stamp(stream, stamps)
    direction = np.int32(1 if descending else 0)
    source_window = windows["source_rows"]
    scalar_montgomery = {
        "forward_numerator": {},
        "adjoint_numerator": {},
        "reach": {},
    }
    scalar_codeword_rows: dict[str, dict[str, object]] = {}
    batch_output_digests: dict[str, dict[str, str]] = {}
    retained_output_bytes: dict[tuple[int, ...], dict[str, bytes]] = {}
    admission_snapshots: dict[tuple[int, ...], tuple[int, dict[str, int]]] = {}
    pass_statuses: dict[tuple[int, ...], int] = {}

    def clear_pass_arrays() -> None:
        with stream:
            for value in (
                forward_levels,
                adjoint_levels,
                numerator,
                reach,
                adjoint_numerator,
                unused_reach,
            ):
                value.fill(0)
            status.fill(0)
            for value in family_minima.values():
                value.fill(2_147_483_647)

    def encode_phase(batch: tuple[int, ...]) -> None:
        channels = len(batch)
        channel_array = batch_index_arrays[batch]
        families = (
            (
                "source_rows",
                source_high,
                source_low,
                dummy_labels,
                source_encoded,
                source_rows,
                width,
                authority.source_family_exponent,
                1,
            ),
            (
                "labeled_query_covectors",
                query_high,
                query_low,
                labels,
                covectors,
                query_rows,
                width,
                authority.covector_family_exponent,
                2,
            ),
            (
                "labeled_query_weights",
                weight_high,
                weight_low,
                labels,
                weights,
                query_rows,
                1,
                authority.weight_family_exponent,
                3,
            ),
        )
        for name, high, low, family_labels, output, logical_rows, family_width, exponent, mode in families:
            raw_rows = source_rows if mode == 1 else labeled_rows
            low_window, high_window = windows[name]
            _launch_device(
                kernels["rrns_encode_aggregate"],
                raw_rows * family_width,
                (
                    high,
                    low,
                    family_labels,
                    output,
                    np.int64(raw_rows),
                    np.int32(family_width),
                    np.int32(exponent),
                    np.int32(low_window),
                    np.int32(high_window),
                    np.int32(0),
                    moduli_device,
                    nprimes_device,
                    r2_device,
                    channel_array,
                    np.int32(channels),
                    family_minima[name],
                    status,
                ),
                stream,
            )
            _launch_device(
                kernels["rrns_encode_aggregate"],
                logical_rows * family_width * channels,
                (
                    high,
                    low,
                    family_labels,
                    output,
                    np.int64(logical_rows),
                    np.int32(family_width),
                    np.int32(exponent),
                    np.int32(low_window),
                    np.int32(high_window),
                    np.int32(mode),
                    moduli_device,
                    nprimes_device,
                    r2_device,
                    channel_array,
                    np.int32(channels),
                    family_minima[name],
                    status,
                ),
                stream,
            )
        level_four_offset = sum(comb(cards, level) for level in range(4))
        with stream:
            adjoint_levels[
                level_four_offset
                * width
                * channels : (level_four_offset + query_rows)
                * width
                * channels
            ] = covectors[: query_rows * width * channels]

    def forward_recurrence(batch: tuple[int, ...]) -> None:
        channels = len(batch)
        for level in range(5, -1, -1):
            _launch_device(
                kernels["rrns_forward_level"],
                comb(cards, level) * width * channels,
                (
                    forward_levels,
                    source_high,
                    source_low,
                    np.int32(cards),
                    np.int32(level),
                    np.int32(width),
                    np.int32(channels),
                    np.int32(authority.source_family_exponent),
                    np.int32(source_window[0]),
                    np.int32(source_window[1]),
                    moduli_device,
                    nprimes_device,
                    r2_device,
                    batch_index_arrays[batch],
                    direction,
                    status,
                ),
                stream,
            )

    def forward_selective_phase(batch: tuple[int, ...]) -> None:
        channels = len(batch)
        _launch_device(
            kernels["rrns_forward_selective"],
            4 * channels,
            (
                forward_levels,
                forward_masks,
                forward_feature_array,
                forward_selected,
                np.int32(4),
                np.int32(cards),
                np.int32(width),
                np.int32(channels),
                moduli_device,
                batch_index_arrays[batch],
                direction,
            ),
            stream,
        )

    def forward_stream_phase(batch: tuple[int, ...]) -> None:
        channels = len(batch)
        _launch_device(
            kernels["rrns_forward_stream"],
            query_rows * width * channels,
            (
                forward_levels,
                forward_stream,
                np.int32(cards),
                np.int32(width),
                np.int32(channels),
                moduli_device,
                batch_index_arrays[batch],
                np.uint64(0),
                np.uint64(query_rows),
                direction,
            ),
            stream,
        )
        _launch_device(
            kernels["rrns_contract"],
            channels,
            (
                forward_stream,
                covectors,
                weights,
                source_high,
                source_low,
                numerator,
                reach,
                np.int64(query_rows),
                np.int32(width),
                np.int32(population.captured.reach_feature),
                np.int32(channels),
                moduli_device,
                nprimes_device,
                r2_device,
                batch_index_arrays[batch],
                np.int32(0),
                np.int32(authority.source_family_exponent),
                np.int32(source_window[0]),
                np.int32(source_window[1]),
                status,
            ),
            stream,
        )

    def adjoint_recurrence(batch: tuple[int, ...]) -> None:
        channels = len(batch)
        for level in range(3, -1, -1):
            _launch_device(
                kernels["rrns_adjoint_level"],
                comb(cards, level) * width * channels,
                (
                    adjoint_levels,
                    np.int32(cards),
                    np.int32(level),
                    np.int32(width),
                    np.int32(channels),
                    moduli_device,
                    batch_index_arrays[batch],
                    direction,
                ),
                stream,
            )

    def adjoint_selective_phase(batch: tuple[int, ...]) -> None:
        channels = len(batch)
        _launch_device(
            kernels["rrns_adjoint_selective"],
            4 * channels,
            (
                adjoint_levels,
                adjoint_masks,
                adjoint_feature_array,
                adjoint_selected,
                np.int32(4),
                np.int32(cards),
                np.int32(width),
                np.int32(channels),
                moduli_device,
                batch_index_arrays[batch],
                direction,
            ),
            stream,
        )

    def adjoint_stream_phase(batch: tuple[int, ...]) -> None:
        channels = len(batch)
        _launch_device(
            kernels["rrns_adjoint_stream"],
            source_rows * width * channels,
            (
                adjoint_levels,
                source_cards,
                adjoint_stream,
                np.int32(cards),
                np.int32(width),
                np.int32(channels),
                moduli_device,
                batch_index_arrays[batch],
                np.uint64(0),
                np.uint64(source_rows),
                direction,
            ),
            stream,
        )
        _launch_device(
            kernels["rrns_contract"],
            channels,
            (
                forward_stream,
                adjoint_stream,
                weights,
                source_high,
                source_low,
                adjoint_numerator,
                unused_reach,
                np.int64(source_rows),
                np.int32(width),
                np.int32(population.captured.reach_feature),
                np.int32(channels),
                moduli_device,
                nprimes_device,
                r2_device,
                batch_index_arrays[batch],
                np.int32(1),
                np.int32(authority.source_family_exponent),
                np.int32(source_window[0]),
                np.int32(source_window[1]),
                status,
            ),
            stream,
        )

    def drain_outputs(batch: tuple[int, ...]) -> dict[str, str]:
        """Transfer bounded residues and digest them without consulting authority."""

        channels = len(batch)
        device_outputs = {
            "source_encoding": source_encoded[: source_rows * width * channels],
            "aggregated_covectors": covectors[: query_rows * width * channels],
            "aggregated_weights": weights[: query_rows * channels],
            "forward_levels": forward_levels[
                : forward_level_rows * width * channels
            ],
            "forward_selected": forward_selected[: 4 * channels],
            "forward_stream": forward_stream[: query_rows * width * channels],
            "adjoint_levels": adjoint_levels[
                : adjoint_level_rows * width * channels
            ],
            "adjoint_selected": adjoint_selected[: 4 * channels],
            "adjoint_stream": adjoint_stream[: source_rows * width * channels],
        }
        digests: dict[str, str] = {}
        raw_by_name: dict[str, bytes] = {}
        for name, value in device_outputs.items():
            raw = _device_u64_bytes(cp, value)
            raw_by_name[name] = raw
            digests[name] = sha256(raw).hexdigest()
        retained_output_bytes[batch] = raw_by_name
        return digests

    def capture_scalar_residues(batch: tuple[int, ...]) -> None:
        """Transfer raw Montgomery scalar residues without reconstruction."""

        channels = len(batch)
        scalar_arrays = {
            "forward_numerator": numerator,
            "adjoint_numerator": adjoint_numerator,
            "reach": reach,
        }
        for name, value in scalar_arrays.items():
            raw_values = cp.asnumpy(value[:channels]).tolist()
            for local, channel in enumerate(batch):
                scalar_montgomery[name][channel] = int(raw_values[local])

    def capture_admission_snapshot(batch: tuple[int, ...]) -> None:
        observed_minima = {
            name: int(cp.asnumpy(value)[0]) for name, value in family_minima.items()
        }
        admission_snapshots[batch] = (int(cp.asnumpy(status)[0]), observed_minima)

    for batch_index, batch in enumerate(batches):
        clear_pass_arrays()
        encode_phase(batch)
        stream.synchronize()
        capture_admission_snapshot(batch)
        stamps.append(perf_counter_ns())
        forward_recurrence(batch)
        _append_synchronized_stamp(stream, stamps)
        forward_selective_phase(batch)
        _append_synchronized_stamp(stream, stamps)
        forward_stream_phase(batch)
        _append_synchronized_stamp(stream, stamps)
        adjoint_recurrence(batch)
        _append_synchronized_stamp(stream, stamps)
        adjoint_selective_phase(batch)
        _append_synchronized_stamp(stream, stamps)
        adjoint_stream_phase(batch)
        _append_synchronized_stamp(stream, stamps)
        if arm == BATCHED_RRNS and batch_index == 0:
            batch_output_digests[str(batch)] = drain_outputs(batch)
            capture_scalar_residues(batch)
            pass_statuses[batch] = int(cp.asnumpy(status)[0])
            with stream:
                forward_levels.fill(0)
                adjoint_levels.fill(0)
                forward_stream.fill(0)
                adjoint_stream.fill(0)
            _append_synchronized_stamp(stream, stamps)

    last_batch = batches[-1]
    # The batched first-pass residues survived only as bounded host words.
    # Transfer the resident/second-pass scalars now, then reconstruct all nine
    # channels under the explicitly named scalar phase.
    capture_scalar_residues(last_batch)
    pass_statuses[last_batch] = int(cp.asnumpy(status)[0])
    expected_minima = {
        "source_rows": authority.source_family_exponent,
        "labeled_query_covectors": authority.covector_family_exponent,
        "labeled_query_weights": authority.weight_family_exponent,
    }
    if set(admission_snapshots) != set(batches) or set(pass_statuses) != set(batches):
        raise DevicePreflightFailure(
            "rrns_admission_rejection", f"{arm} admission snapshots are incomplete"
        )
    for batch, (observed_status, observed_minima) in admission_snapshots.items():
        if observed_status != 0 or pass_statuses[batch] != 0:
            raise DevicePreflightFailure(
                "rrns_status_rejection", f"{arm} device status changed for {batch}"
            )
        if observed_minima != expected_minima:
            raise DevicePreflightFailure(
                "rrns_admission_rejection", f"{arm} family minima differ for {batch}"
            )
    if any(set(values) != set(range(9)) for values in scalar_montgomery.values()):
        raise DevicePreflightFailure(
            "rrns_scalar_differential_rejection",
            f"{arm} scalar channel coverage differs",
        )
    decoded_scalars = {}
    for name, authority_value in (
        ("forward_numerator", authority.forward_integer_numerator),
        ("adjoint_numerator", authority.adjoint_integer_numerator),
        ("reach", authority.forward_integer_reach),
    ):
        residues = tuple(
            fixed.montgomery_decode(
                scalar_montgomery[name][channel], constants[channel]
            )
            for channel in range(9)
        )
        codeword = fixed.RRNSValue(residues, scalar_parameters)
        decoded = fixed.rrns_reconstruct_both(codeword)
        if decoded % 720 or decoded != authority_value:
            raise DevicePreflightFailure(
                "rrns_scalar_differential_rejection", f"{arm} {name} differs"
            )
        for channel in range(9):
            observation = fixed.observe_rrns_fault(codeword, (channel,))
            if not (
                observation.full_CRT_detected
                and observation.base_extension_detected
                and observation.eligible_for_single_channel_claim
            ):
                raise DevicePreflightFailure(
                    "rrns_fault_detection_rejection",
                    f"{arm} failed scalar channel fault control",
                )
        scalar_codeword_rows[name] = {
            "label": name,
            "decoded_decimal": str(decoded),
            "residues": list(residues),
        }
        decoded_scalars[name] = decoded
    conditional = exact.correctly_rounded_binary64(
        decoded_scalars["forward_numerator"],
        decoded_scalars["reach"],
        authority.covector_family_exponent - authority.weight_family_exponent,
    )
    if exact.binary64_bits(conditional) != authority.conditional_value_bits:
        raise DevicePreflightFailure(
            "rrns_rounding_rejection", f"{arm} terminal bits differ"
        )
    consistent_wrong = fixed.RRNSValue.encode(
        decoded_scalars["forward_numerator"] + 720, scalar_parameters
    )
    if fixed.rrns_reconstruct_both(consistent_wrong) != (
        decoded_scalars["forward_numerator"] + 720
    ):
        raise AssertionError("correlated-fault boundary control did not pass RRNS")
    try:
        fixed.require_unbounded_match(
            fixed.rrns_reconstruct_both(consistent_wrong),
            authority.forward_integer_numerator,
        )
    except ArithmeticError:
        correlated_fault_boundary = "rrns_passed_unbounded_differential_rejected"
    else:
        raise DevicePreflightFailure(
            "rrns_correlated_fault_boundary_rejection",
            "consistent all-channel corruption escaped the differential",
        )
    _append_synchronized_stamp(stream, stamps)

    batch_output_digests[str(last_batch)] = drain_outputs(last_batch)
    if set(retained_output_bytes) != set(batches):
        raise DevicePreflightFailure(
            "rrns_output_differential_rejection",
            f"{arm} retained output batches are incomplete",
        )
    for batch in batches:
        expected = expected_by_channels[batch]
        observed = retained_output_bytes[batch]
        if set(observed) != set(expected):
            raise DevicePreflightFailure(
                "rrns_output_differential_rejection",
                f"{arm} output domains differ for channels {batch}",
            )
        for name, raw in observed.items():
            if raw != expected[name]:
                raise DevicePreflightFailure(
                    "rrns_output_differential_rejection",
                    f"{arm} output differs for channels {batch}: {name}",
                )
    table_batch = next(
        batch for batch in batches if set((0, 1, 2, 3, 8)).issubset(batch)
    )
    table_raw = retained_output_bytes[table_batch]["source_encoding"]
    table_parameters, _ = fixed.validate_frozen_rrns()
    table_values = {}
    for local, channel in enumerate(table_batch):
        if channel in {0, 1, 2, 3, 8}:
            encoded = int.from_bytes(table_raw[local * 8 : (local + 1) * 8], "little")
            table_values[channel] = fixed.montgomery_decode(
                encoded, constants[channel]
            )
    table_codeword = fixed.RRNSValue(
        tuple(table_values[channel] for channel in (0, 1, 2, 3, 8)),
        table_parameters,
    )
    table_decoded = fixed.rrns_reconstruct_both(table_codeword)
    for channel in range(5):
        observation = fixed.observe_rrns_fault(table_codeword, (channel,))
        if not observation.eligible_for_single_channel_claim or not (
            observation.full_CRT_detected and observation.base_extension_detected
        ):
            raise DevicePreflightFailure(
                "rrns_table_fault_control_rejection", "table fault was not detected"
            )
    rrns_fault_evidence = {
        "schema_version": "fixed-width-device-rrns-fault-evidence-v1",
        "changed_residue_delta": 1,
        "table_code": {
            "working_moduli": list(table_parameters.working_primes),
            "redundant_modulus": table_parameters.redundant_prime,
            "absolute_bound_decimal": str(table_parameters.absolute_bound),
            "codewords": [
                {
                    "label": "source_encoding_first",
                    "decoded_decimal": str(table_decoded),
                    "residues": list(table_codeword.residues),
                }
            ],
        },
        "scalar_code": {
            "working_moduli": list(scalar_parameters.working_primes),
            "redundant_modulus": scalar_parameters.redundant_prime,
            "absolute_bound_decimal": str(scalar_parameters.absolute_bound),
            "codewords": [
                scalar_codeword_rows[name]
                for name in (
                    "forward_numerator",
                    "adjoint_numerator",
                    "reach",
                )
            ],
        },
        "correlated_control": {
            "label": "forward_numerator_plus_720",
            "decoded_decimal": str(decoded_scalars["forward_numerator"] + 720),
            "unbounded_authority_decimal": str(
                authority.forward_integer_numerator
            ),
            "residues": list(consistent_wrong.residues),
        },
    }
    _append_synchronized_stamp(stream, stamps)

    del (
        source_high,
        source_low,
        query_high,
        query_low,
        weight_high,
        weight_low,
        labels,
        source_cards,
        source_encoded,
        covectors,
        weights,
        forward_levels,
        adjoint_levels,
        forward_selected,
        adjoint_selected,
        forward_stream,
        adjoint_stream,
        numerator,
        reach,
        adjoint_numerator,
        unused_reach,
        dummy_labels,
        status,
        family_minima,
        moduli_device,
        nprimes_device,
        r2_device,
        batch_index_arrays,
        forward_masks,
        forward_feature_array,
        adjoint_masks,
        adjoint_feature_array,
        retained_output_bytes,
        admission_snapshots,
        scalar_montgomery,
        table_values,
        scalar_codeword_rows,
        pass_statuses,
    )
    stream.synchronize()
    cp.get_default_memory_pool().free_all_blocks(stream=stream)
    cp.get_default_pinned_memory_pool().free_all_blocks()
    _append_synchronized_stamp(stream, stamps)
    partition = phase_partition(phase_names_for_arm(arm), stamps)
    return {
        "schema_version": "fixed-width-device-candidate-run-v1",
        "arm": arm,
        "population": population.label,
        "traversal_order": "descending_colex" if descending else "ascending_colex",
        "input_sha256": population.input_sha256,
        "phase_partition": {
            "rows": [asdict(row) for row in partition.rows],
            "total_ns": partition.total_ns,
        },
        "batch_output_digests": batch_output_digests,
        "scalar_values_decimal": {
            name: str(value) for name, value in decoded_scalars.items()
        },
        "conditional_value_bits": authority.conditional_value_bits,
        "single_changed_channel_controls": 32,
        "correlated_fault_boundary": correlated_fault_boundary,
        "rrns_fault_evidence": rrns_fault_evidence,
        "exact_verified": True,
    }


def _phase_rows_from_evidence(value: Mapping[str, object]) -> tuple[PhaseRow, ...]:
    partition = value.get("phase_partition")
    if not isinstance(partition, Mapping):
        raise TypeError("candidate phase partition is absent")
    raw_rows = partition.get("rows")
    if not isinstance(raw_rows, list):
        raise TypeError("candidate phase rows are absent")
    rows = []
    for raw in raw_rows:
        if not isinstance(raw, Mapping) or set(raw) != {
            "name",
            "start_ns",
            "end_ns",
            "elapsed_ns",
        }:
            raise ValueError("candidate phase row fields differ")
        name = raw["name"]
        if not isinstance(name, str) or not name:
            raise TypeError("candidate phase name differs")
        start = _require_plain_int(raw["start_ns"], label="phase start", minimum=0)
        end = _require_plain_int(raw["end_ns"], label="phase end", minimum=0)
        elapsed = _require_plain_int(
            raw["elapsed_ns"], label="phase elapsed", minimum=0
        )
        if end - start != elapsed:
            raise ValueError("candidate phase elapsed differs")
        rows.append(PhaseRow(name, start, end, elapsed))
    total = _require_plain_int(
        partition.get("total_ns"), label="candidate phase total", minimum=0
    )
    if not rows or sum(row.elapsed_ns for row in rows) != total:
        raise ValueError("candidate phase total differs")
    return tuple(rows)


def laboratory_partition(
    rows: Sequence[PhaseRow], *, start_ns: int, end_ns: int
) -> dict[str, object]:
    """Validate one exact, gap-free laboratory ledger with repeated phase names."""

    start = _require_plain_int(start_ns, label="laboratory start", minimum=0)
    end = _require_plain_int(end_ns, label="laboratory end", minimum=0)
    ledger = tuple(rows)
    if not ledger or ledger[0].start_ns != start or ledger[-1].end_ns != end:
        raise ValueError("laboratory endpoint differs")
    for left, right in zip(ledger, ledger[1:]):
        if left.end_ns != right.start_ns:
            raise ValueError("laboratory ledger has a gap or overlap")
    total = end - start
    if total < 0 or sum(row.elapsed_ns for row in ledger) != total:
        raise ValueError("laboratory ledger sum differs")
    return {
        "schema_version": "fixed-width-device-laboratory-partition-v1",
        "rows": [asdict(row) for row in ledger],
        "total_ns": total,
        "exact_sum": True,
    }


def _candidate_schedule() -> tuple[tuple[str, str, int, bool], ...]:
    """Return (kind, arm, repeat, descending) in the frozen order."""

    schedule: list[tuple[str, str, int, bool]] = []
    for arm in ARMS:
        schedule.append(("warmup", arm, 0, False))
    rotations = (
        ARMS,
        (RESIDENT_RRNS, BATCHED_RRNS, POSITIONAL),
        (BATCHED_RRNS, POSITIONAL, RESIDENT_RRNS),
    )
    for descending in (False, True):
        for repeat, rotation in enumerate(rotations):
            for arm in rotation:
                schedule.append(("timed", arm, repeat, descending))
    return tuple(schedule)


def execute_device_preflight(
    emit: Callable[[str, Mapping[str, object]], None],
    *,
    laboratory_started_ns: int,
    bootstrap_ended_ns: int,
) -> dict[str, object]:
    """Execute the one frozen reduced-population device screen.

    The runner owns the process and durable transport.  Its bootstrap begins
    the laboratory before this scientific module is imported, so both
    endpoints are passed in explicitly and remain in the same monotonic clock
    domain.  Candidate evidence is retained in memory until the laboratory
    closes.  Raw compiler/cubin/resource evidence and each reduced host-
    authority manifest cross an ACK boundary inside the laboratory: raw bytes
    precede interpretation or execution, and authority precedes its candidates.
    """

    if not callable(emit):
        raise TypeError("device-preflight emitter must be callable")
    laboratory_start = _require_plain_int(
        laboratory_started_ns, label="laboratory start", minimum=0
    )
    bootstrap_end = _require_plain_int(
        bootstrap_ended_ns, label="bootstrap end", minimum=laboratory_start
    )
    verify_preregistered_contract()
    cuda_source_contract()
    ledger: list[PhaseRow] = [
        PhaseRow(
            GLOBAL_PHASE_NAMES[0],
            laboratory_start,
            bootstrap_end,
            bootstrap_end - laboratory_start,
        )
    ]
    observations: list[dict[str, object]] = []
    authority_manifests: list[dict[str, object]] = []
    timed_totals = {
        population: {arm: 0 for arm in ARMS} for population in POPULATIONS
    }
    observed_counts = {
        population: {
            arm: {"warmup": 0, "timed_ascending": 0, "timed_descending": 0}
            for arm in ARMS
        }
        for population in POPULATIONS
    }
    symbolic = symbolic_literal45_liveness()
    directory_owner = tempfile.TemporaryDirectory(
        prefix="pontius-fixed-width-device-preflight-"
    )
    context: CompiledDeviceContext | None = None
    cursor = bootstrap_end
    resource_eligibility: dict[str, bool] = {arm: False for arm in ARMS}
    try:
        directory = Path(directory_owner.name)
        context = _load_compiled_context(directory, emit, start_ns=cursor)
        ledger.extend(context.global_phase_rows)
        cursor = context.global_phase_rows[-1].end_ns
        resource_eligibility = {
            arm: arm_resource_eligible(arm, context.resources) for arm in ARMS
        }

        for population_index, label in enumerate(POPULATIONS):
            fixture_start = cursor
            population = build_validation_population(label)
            positional_expected = _representation_expectations(
                population, arm=POSITIONAL
            )
            resident_channels = tuple(range(9))
            first_batch = (0, 1, 2, 3, 8)
            second_batch = (4, 5, 6, 7)
            resident_expected = {
                resident_channels: _representation_expectations(
                    population,
                    arm=RESIDENT_RRNS,
                    channel_indices=resident_channels,
                )
            }
            batched_expected = {
                first_batch: _representation_expectations(
                    population,
                    arm=BATCHED_RRNS,
                    channel_indices=first_batch,
                ),
                second_batch: _representation_expectations(
                    population,
                    arm=BATCHED_RRNS,
                    channel_indices=second_batch,
                ),
            }
            authority_manifest = _reduced_authority_manifest(
                population,
                positional=positional_expected,
                resident=resident_expected,
                batched=batched_expected,
            )
            # This ACK is inside the named fixture phase.  The immutable host
            # authority therefore reaches durable storage before any device
            # candidate for this population can run.
            emit("reduced_population_authority", authority_manifest)
            authority_manifests.append(authority_manifest)
            fixture_end = perf_counter_ns()
            fixture_name = GLOBAL_PHASE_NAMES[6 + population_index]
            ledger.append(
                PhaseRow(
                    fixture_name,
                    fixture_start,
                    fixture_end,
                    fixture_end - fixture_start,
                )
            )
            cursor = fixture_end

            for kind, arm, repeat, descending in _candidate_schedule():
                if arm == POSITIONAL:
                    result = _run_positional_candidate(
                        context,
                        population,
                        descending=descending,
                        expected=positional_expected,
                        start_ns=cursor,
                    )
                else:
                    result = _run_rrns_candidate(
                        context,
                        population,
                        arm=arm,
                        descending=descending,
                        expected_by_channels=(
                            resident_expected if arm == RESIDENT_RRNS else batched_expected
                        ),
                        start_ns=cursor,
                    )
                phase_rows = _phase_rows_from_evidence(result)
                if tuple(row.name for row in phase_rows) != phase_names_for_arm(arm):
                    raise DevicePreflightFailure(
                        "phase_partition_rejection",
                        f"{arm} phase names differ from the frozen topology",
                    )
                ledger.extend(phase_rows)
                cursor = phase_rows[-1].end_ns
                result["schedule_kind"] = kind
                result["repeat_index"] = repeat
                result["arm_order_index"] = next(
                    index
                    for index, row in enumerate(_candidate_schedule())
                    if row == (kind, arm, repeat, descending)
                )
                observations.append(result)
                if kind == "warmup":
                    observed_counts[label][arm]["warmup"] += 1
                else:
                    order_key = (
                        "timed_descending" if descending else "timed_ascending"
                    )
                    observed_counts[label][arm][order_key] += 1
                    timed_totals[label][arm] += int(
                        result["phase_partition"]["total_ns"]
                    )

            # Host fixtures and expectations have no customer after their
            # population's sealed observations.  Their Python teardown is
            # charged to the following global/candidate interval via cursor.
            del (
                population,
                positional_expected,
                resident_expected,
                batched_expected,
            )

        final_start = cursor
        cp = context.cp
        cp.cuda.Device(0).synchronize()
        resources = context.resources
        runtime = context.runtime
        cubin_sha256 = sha256(context.cubin).hexdigest()
        compile_and_resource_elapsed_ns = context.compile_and_resource_elapsed_ns
        del context
        cp.get_default_memory_pool().free_all_blocks()
        cp.get_default_pinned_memory_pool().free_all_blocks()
        directory_owner.cleanup()

        expected_counts = {
            "warmup": 1,
            "timed_ascending": 3,
            "timed_descending": 3,
        }
        if any(
            observed_counts[population][arm] != expected_counts
            for population in POPULATIONS
            for arm in ARMS
        ):
            raise DevicePreflightFailure(
                "execution_schedule_rejection", "candidate observation counts differ"
            )
        resource_rows = _serialize_dataclass_rows(resources)
        compile_pass = wall_passes(
            compile_and_resource_elapsed_ns, COMPILE_RESOURCE_WALL_NS
        )
        arm_preconditions: dict[str, dict[str, object]] = {}
        for arm in ARMS:
            memory_pass = bool(symbolic[arm]["liveness"]["eligible"])
            walls = {
                population: {
                    "elapsed_ns": timed_totals[population][arm],
                    "ceiling_ns": PER_POPULATION_ARM_WALL_NS,
                    "passed": wall_passes(
                        timed_totals[population][arm], PER_POPULATION_ARM_WALL_NS
                    ),
                }
                for population in POPULATIONS
            }
            arm_observations = [row for row in observations if row["arm"] == arm]
            exact_pass = len(arm_observations) == 14 and all(
                row.get("exact_verified") is True for row in arm_observations
            )
            rrns_pass = arm == POSITIONAL or all(
                row.get("single_changed_channel_controls") == 32
                and row.get("correlated_fault_boundary")
                == "rrns_passed_unbounded_differential_rejected"
                for row in arm_observations
            )
            arm_preconditions[arm] = {
                "memory_pass": memory_pass,
                "walls": walls,
                "exact_pass": exact_pass,
                "rrns_pass": rrns_pass,
            }
        final_end = perf_counter_ns()
        ledger.append(
            PhaseRow(
                GLOBAL_PHASE_NAMES[-1],
                final_start,
                final_end,
                final_end - final_start,
            )
        )
        laboratory = laboratory_partition(
            ledger, start_ns=laboratory_start, end_ns=final_end
        )
        laboratory_pass = wall_passes(laboratory["total_ns"], LABORATORY_WALL_NS)
        eligibility: dict[str, dict[str, object]] = {}
        for arm in ARMS:
            preconditions = arm_preconditions[arm]
            memory_pass = bool(preconditions["memory_pass"])
            walls = preconditions["walls"]
            exact_pass = bool(preconditions["exact_pass"])
            rrns_pass = bool(preconditions["rrns_pass"])
            eligible = (
                resource_eligibility[arm]
                and memory_pass
                and exact_pass
                and rrns_pass
                and compile_pass
                and laboratory_pass
                and all(row["passed"] for row in walls.values())
            )
            eligibility[arm] = {
                "resource_eligible": resource_eligibility[arm],
                "symbolic_literal_45_memory_eligible": memory_pass,
                "complete_reduced_exactness": exact_pass,
                "RRNS_fault_contract": rrns_pass,
                "compile_and_resource_wall": compile_pass,
                "laboratory_wall": laboratory_pass,
                "timed_population_walls": walls,
                "eligible": eligible,
            }
        terminal = (
            "completed_device_preflight"
            if any(row["eligible"] for row in eligibility.values())
            else "completed_no_device_candidate"
        )
        evidence = {
            "schema_version": "legal-river-quotient-fixed-width-device-preflight-v1",
            "terminal": terminal,
            "passed": terminal == "completed_device_preflight",
            "cuda_source_sha256": CUDA_SOURCE_SHA256,
            "cubin_sha256": cubin_sha256,
            "runtime": runtime,
            "compile_and_resource_elapsed_ns": compile_and_resource_elapsed_ns,
            "resource_rows": resource_rows,
            "symbolic_literal_45_memory_liveness": symbolic,
            "candidate_observations": observations,
            "authority_manifests": authority_manifests,
            "observed_counts": observed_counts,
            "laboratory_partition": laboratory,
            "eligibility": eligibility,
            "candidate_selected": None,
            "claims": {
                "population_25_numeric_value": None,
                "actual_45_card_value": None,
                "resolver_iteration_result": None,
                "solve_result": None,
                "action_result": None,
                "action_clock_result": None,
                "decision_quality_result": None,
                "truncation_authorized": False,
                "blueprint_result": None,
                "poker_strength_result": None,
            },
        }
        emit("symbolic_literal_45_memory_liveness", symbolic)
        for result in observations:
            emit("candidate_observation", result)
        emit("laboratory_partition", laboratory)
        emit("candidate_eligibility", eligibility)
        return evidence
    finally:
        # Idempotent on normal completion; essential for typed early terminals.
        directory_owner.cleanup()


__all__ = [
    "ARMS",
    "ArmedMutationReceipt",
    "BACKING_CEILING_BYTES",
    "BATCHED_RRNS",
    "BATCHED_PHASE_NAMES",
    "BLOCK_THREADS",
    "BoundedCommand",
    "BufferLifetime",
    "CUDA_SOURCE",
    "CUDA_SOURCE_SHA256",
    "COMPILE_RESOURCE_WALL_NS",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "CubinResource",
    "DEVICE_RESERVE_BYTES",
    "DriverResource",
    "DevicePreflightFailure",
    "EffectiveResource",
    "EXPECTED_DEVICE_TOTAL_BYTES",
    "GLOBAL_PHASE_NAMES",
    "KERNEL_NAMES",
    "LABORATORY_WALL_NS",
    "MAXIMUM_COMPILER_STREAM_BYTES",
    "MAXIMUM_CUBIN_BYTES",
    "MAXIMUM_EXTERNAL_STREAM_BYTES",
    "MemoryLiveness",
    "NVCC_OPTIONS",
    "PER_COMMAND_WALL_NS",
    "PER_POPULATION_ARM_WALL_NS",
    "PHASE_NAMES",
    "POSITIONAL",
    "PREREGISTRATION_COMMIT",
    "PUBLIC_WALL_NS",
    "PhasePartition",
    "PhaseRow",
    "PtxasResource",
    "REGISTER_CEILING",
    "RESIDENT_RRNS",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "SPILL_BYTE_CEILING",
    "SassLocalSites",
    "SINGLE_PASS_PHASE_NAMES",
    "arm_resource_eligible",
    "canonical_lf_bytes",
    "canonical_lf_sha256",
    "combine_resource_evidence",
    "compile_argv",
    "cuda_source_contract",
    "decode_binary",
    "encode_binary",
    "execute_device_preflight",
    "independent_normalize_crlf_bytes",
    "laboratory_partition",
    "literal_escape_mutation_receipt",
    "load_preregistered_config",
    "memory_liveness",
    "normalize_crlf_bytes",
    "parse_cuobjdump_resource_usage",
    "parse_nvdisasm_local_sites",
    "parse_ptxas_verbose",
    "phase_partition",
    "phase_names_for_arm",
    "run_bounded_command",
    "signed_integer_to_words",
    "signed_schoolbook_product_words",
    "symbolic_literal45_liveness",
    "verify_preregistered_contract",
    "wall_passes",
    "words_to_signed_integer",
]
