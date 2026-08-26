"""Independent standard-library rebinder for ADR-0410's suffix journal."""

from __future__ import annotations

import base64
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import struct
from typing import Final

from .durable_evidence_journal import recover_journal_bytes, recover_journal_file


_ROOT: Final = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH: Final = (
    "experiments/configs/legal-river-exact-cubin-zero-suffix-diagnostic-v1.json"
)
RESULT_RELATIVE_PATH: Final = (
    "artifacts/work_preflight/legal_river_exact_cubin_zero_suffix_diagnostic_v1.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH: Final = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
_CONFIG = _ROOT / CONFIG_RELATIVE_PATH
_RESULT = _ROOT / RESULT_RELATIVE_PATH
_RESERVED = _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH
CONFIG_SHA256: Final = (
    "6473d8726bc359091f21706b06a5798f67e1ba19919a2de66db17f7c0329d32d"
)
PROTOCOL_SHA256: Final = sha256(
    b"pontius-adr0410-exact-zero-suffix-exclusive-journal-v1"
).hexdigest()
CAMPAIGN_SHA256: Final = sha256(
    b"pontius-adr0410-exact-zero-suffix-one-shot-campaign-v1"
).hexdigest()
LITERAL_WORKER_MODULE: Final = (
    "pontius.legal_river_exact_cubin_zero_suffix_diagnostic_runner"
)
MAXIMUM_ARTIFACT_BYTES: Final = 67_108_864
MAXIMUM_PAYLOAD_BYTES: Final = 8_388_608
MAXIMUM_STREAM_BYTES: Final = 8_388_608
ORIGINAL_PAYLOAD_SHA256: Final = (
    "5dc4973302061b29dccd955ff7ee4dff3d61216316fb5d2fa71e9df22f42cd97"
)
ORIGINAL_PAYLOAD_BYTES: Final = 514_039
REPAIRED_PAYLOAD_SHA256: Final = (
    "97693be7baafd882ad64a1a7da0ede23dc927efd872b0d15697b2486957ea894"
)
REPAIRED_PAYLOAD_BYTES: Final = 514_040
PARENT_ARTIFACT_SHA256: Final = (
    "9e0d160dd36884adb85914f819e11882d5becc42071f7847c1503a42c1d83aed"
)
PARENT_ARTIFACT_BYTES: Final = 705_101
PARENT_SELECTION_SHA256: Final = (
    "ebc66a0d06a84eeb16d5c2d6adf6376227011ef3982c8fcdd09e97496c276d1f"
)
PARENT_SELECTION_BYTES: Final = 3_164
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
_OUTER_TERMINALS: Final = frozenset(
    {
        "suffix_reconstruction_pass",
        "structural_rejection",
        "candidate_timeout_rejection",
        "candidate_output_limit_rejection",
        "tool_rejection",
        "module_load_rejection",
        "driver_row_rejection",
        "laboratory_wall_rejection",
        "diagnostic_failure",
        "infrastructure_failure",
    }
)


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"zero-suffix reader dependency is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    return value


def _digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def _load_config() -> dict[str, object]:
    raw = _CONFIG.read_bytes()
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != CONFIG_SHA256:
        raise ValueError("zero-suffix reader config differs from ADR-0410")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise TypeError("zero-suffix reader config must be an object")
    commands = value.get("candidate_commands_in_order")
    if not isinstance(commands, list) or len(commands) != 6:
        raise ValueError("zero-suffix reader command inventory differs")
    return value


@dataclass(frozen=True, slots=True)
class BinaryEvidence:
    raw: bytes
    sha256: str
    byte_count: int


def decode_binary(
    value: object, *, label: str, maximum_bytes: int
) -> BinaryEvidence:
    row = _mapping(value, label=label)
    if set(row) != {"encoding", "byte_count", "sha256", "base64"}:
        raise ValueError(f"{label} fields differ")
    if row["encoding"] != "base64_standard":
        raise ValueError(f"{label} encoding differs")
    count = row["byte_count"]
    encoded = row["base64"]
    digest = _digest(row["sha256"], label=f"{label} digest")
    if (
        isinstance(count, bool)
        or not isinstance(count, int)
        or isinstance(maximum_bytes, bool)
        or not isinstance(maximum_bytes, int)
        or maximum_bytes <= 0
        or not 0 <= count <= maximum_bytes
        or not isinstance(encoded, str)
        or not encoded.isascii()
    ):
        raise ValueError(f"{label} bounds differ")
    try:
        raw = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError(f"{label} base64 differs") from error
    if (
        len(raw) != count
        or sha256(raw).hexdigest() != digest
        or base64.b64encode(raw).decode("ascii") != encoded
    ):
        raise ValueError(f"{label} envelope differs from bytes")
    return BinaryEvidence(raw=raw, sha256=digest, byte_count=count)


@dataclass(frozen=True, slots=True)
class CandidateEvidence:
    candidate_id: str
    status: str
    return_code: int | None
    stdout: BinaryEvidence
    stderr: BinaryEvidence
    elapsed_ns: int
    required: bool


@dataclass(frozen=True, slots=True)
class ZeroSuffixDiagnosticRebinding:
    terminal: str
    passed: bool
    event_count: int
    source_commit: str | None
    repaired_payload: BinaryEvidence | None
    candidates: tuple[CandidateEvidence, ...]
    module_driver_rows: Mapping[str, Mapping[str, int]] | None
    resource_rows: Mapping[str, Mapping[str, int]] | None
    qualified_resource_instrument: str | None
    cleanup: Mapping[str, object] | None
    journal_byte_count: int


def _validate_header(payload: Mapping[str, object]) -> None:
    expected = {
        "schema_version": "legal-river-zero-suffix-owner-header-v1",
        "protocol_sha256": PROTOCOL_SHA256,
        "campaign_sha256": CAMPAIGN_SHA256,
        "config_relative_path": CONFIG_RELATIVE_PATH,
        "config_sha256": CONFIG_SHA256,
        "result_relative_path": RESULT_RELATIVE_PATH,
        "reserved_actual_result_relative_path": RESERVED_ACTUAL_RESULT_RELATIVE_PATH,
        "literal_worker_module": LITERAL_WORKER_MODULE,
        "qualified_resource_instrument": None,
        "resource_gate_result": None,
        "calibration_result": None,
        "capacity_projection": None,
    }
    if dict(payload) != expected:
        raise ValueError("zero-suffix journal header differs")


def _validate_current_dependencies(event: Mapping[str, object]) -> None:
    dependencies = _mapping(event.get("dependency_hashes"), label="dependency hashes")
    expected = {
        "config": _CONFIG,
        "adr0409": _ROOT
        / "docs/decisions/ADR-0409-retain-the-empty-exact-cubin-inspector-selection.md",
        "adr0410": _ROOT
        / "docs/decisions/ADR-0410-preregister-the-one-byte-elf-suffix-diagnostic.md",
        "parent_reader": _ROOT
        / "src/pontius/legal_river_exact_cubin_inspector_diagnostic_result.py",
        "diagnostic": _ROOT
        / "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic.py",
        "owner": _ROOT
        / "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic_runner.py",
        "reader": _ROOT
        / "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic_result.py",
        "controls": _ROOT
        / "tests/test_legal_river_exact_cubin_zero_suffix_diagnostic.py",
        "durable_journal": _ROOT / "src/pontius/durable_evidence_journal.py",
    }
    if set(dependencies) != set(expected):
        raise ValueError("zero-suffix dependency inventory differs")
    for name, path in expected.items():
        if dependencies[name] != canonical_lf_sha256(path):
            raise ValueError(f"zero-suffix dependency differs: {name}")


def _validate_retained_artifacts(value: object) -> None:
    rows = _mapping(value, label="retained artifacts")
    expected = {
        "diagnostic": (
            "artifacts/work_preflight/legal_river_exact_cubin_inspector_diagnostic_v1.jsonl",
            PARENT_ARTIFACT_SHA256,
            PARENT_ARTIFACT_BYTES,
            12,
        ),
        "selection": (
            "experiments/results/legal-river-exact-cubin-inspector-selection-v1.json",
            PARENT_SELECTION_SHA256,
            PARENT_SELECTION_BYTES,
            1,
        ),
    }
    if set(rows) != set(expected):
        raise ValueError("zero-suffix retained artifact inventory differs")
    for name, (relative, digest, count, records) in expected.items():
        row = _mapping(rows[name], label=f"retained {name}")
        if row != {
            "relative_path": relative,
            "sha256": digest,
            "byte_count": count,
            "record_count": records,
        }:
            raise ValueError(f"zero-suffix retained facts differ: {name}")
        raw = (_ROOT / relative).read_bytes()
        if (
            sha256(raw).hexdigest() != digest
            or len(raw) != count
            or len(raw.splitlines()) != records
        ):
            raise ValueError(f"zero-suffix retained bytes differ: {name}")


def _validate_handshake(event: Mapping[str, object]) -> None:
    challenge = event.get("challenge")
    if (
        event.get("schema_version") != "legal-river-zero-suffix-handshake-v1"
        or not isinstance(challenge, str)
        or len(challenge) != 64
        or any(ch not in "0123456789abcdef" for ch in challenge)
        or event.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or event.get("runtime_name") != "__main__"
        or event.get("spec_name") != LITERAL_WORKER_MODULE
        or event.get("python_no_bytecode") is not True
        or event.get("cupy_loaded") is not False
        or event.get("parent_reader_loaded") is not False
    ):
        raise ValueError("zero-suffix bootstrap handshake differs")


def _bounded_add(offset: int, size: int, limit: int, *, label: str) -> int:
    if min(offset, size, limit) < 0 or offset > limit or size > limit - offset:
        raise ValueError(f"{label} is outside repaired payload")
    return offset + size


def _expected_header(config: Mapping[str, object]) -> tuple[object, ...]:
    original = _mapping(config.get("original_elf_contract"), label="ELF contract")
    return (
        bytes.fromhex(str(original["ident_hex"])),
        *(
            int(original[name])
            for name in (
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
        ),
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
    return dict(zip(names, (header[0].hex(), *header[1:]), strict=True))


def _validate_repaired_payload(
    event: Mapping[str, object], config: Mapping[str, object]
) -> BinaryEvidence:
    if (
        event.get("schema_version") != "legal-river-zero-suffix-repaired-payload-v1"
        or "synthetic_protocol_probe" in event
        or event.get("original_payload_sha256") != ORIGINAL_PAYLOAD_SHA256
        or event.get("original_payload_bytes") != ORIGINAL_PAYLOAD_BYTES
    ):
        raise ValueError("zero-suffix repaired-payload identity differs")
    repaired = decode_binary(
        event.get("repaired_payload"),
        label="repaired payload",
        maximum_bytes=MAXIMUM_PAYLOAD_BYTES,
    )
    if (
        repaired.sha256 != REPAIRED_PAYLOAD_SHA256
        or repaired.byte_count != REPAIRED_PAYLOAD_BYTES
        or repaired.raw[-1:] != b"\x00"
        or sha256(repaired.raw[:-1]).hexdigest() != ORIGINAL_PAYLOAD_SHA256
        or len(repaired.raw[:-1]) != ORIGINAL_PAYLOAD_BYTES
    ):
        raise ValueError("zero-suffix exact prefix/suffix identity differs")
    original = _mapping(config.get("original_elf_contract"), label="ELF contract")
    reconstruction = _mapping(
        config.get("reconstruction_contract"), label="reconstruction contract"
    )
    header = _ELF_HEADER.unpack_from(repaired.raw, 0)
    if header != _expected_header(config):
        raise ValueError("zero-suffix independent ELF header differs")
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
        or e_phoff + e_phentsize * e_phnum != len(repaired.raw)
        or e_shoff + e_shentsize * e_shnum != e_phoff
        or not 0 <= e_shstrndx < e_shnum
    ):
        raise ValueError("zero-suffix independent table geometry differs")
    original_prefix = repaired.raw[:-1]
    final_offset = e_phoff + (e_phnum - 1) * e_phentsize
    final_partial = original_prefix[final_offset:]
    if (
        len(final_partial) != e_phentsize - 1
        or _PROGRAM_HEADER_FIRST_SEVEN.unpack_from(final_partial, 0)
        != tuple(original["final_partial_program_header_first_seven_fields"])
        or final_partial[_PROGRAM_HEADER_FIRST_SEVEN.size :].hex()
        != original["final_partial_p_align_low_seven_bytes_hex"]
        or original_prefix[-32:].hex() != original["original_tail_32_hex"]
        or repaired.raw[-32:].hex() != reconstruction["repaired_tail_32_hex"]
    ):
        raise ValueError("zero-suffix independent partial-header evidence differs")
    program_headers = tuple(
        _PROGRAM_HEADER.unpack_from(repaired.raw, e_phoff + index * e_phentsize)
        for index in range(e_phnum)
    )
    expected_programs = tuple(
        tuple(int(item) for item in row)
        for row in original["complete_program_headers_in_order"]
    ) + (tuple(int(item) for item in reconstruction["repaired_final_program_header"]),)
    if program_headers != expected_programs:
        raise ValueError("zero-suffix independent program rows differ")
    for index, row in enumerate(program_headers):
        _type, _flags, offset, _vaddr, _paddr, filesz, memsz, alignment = row
        _bounded_add(offset, filesz, len(repaired.raw), label=f"program {index}")
        if memsz < filesz or (
            alignment not in {0, 1} and alignment & (alignment - 1)
        ):
            raise ValueError(f"zero-suffix independent program invariant differs: {index}")
    section_end = _bounded_add(
        e_shoff, e_shentsize * e_shnum, len(repaired.raw), label="section table"
    )
    section_bytes = repaired.raw[e_shoff:section_end]
    sections = tuple(
        _SECTION_HEADER.unpack_from(section_bytes, index * e_shentsize)
        for index in range(e_shnum)
    )
    for index, row in enumerate(sections):
        if row[1] != _SHT_NOBITS:
            _bounded_add(row[4], row[5], len(repaired.raw), label=f"section {index}")
    name_table = sections[e_shstrndx]
    if name_table[1] == _SHT_NOBITS:
        raise ValueError("zero-suffix section-name table is not file-backed")
    _bounded_add(name_table[4], name_table[5], len(repaired.raw), label="name table")
    if (
        event.get("elf_header") != _header_mapping(header)
        or event.get("program_headers") != [list(row) for row in program_headers]
        or event.get("section_table_sha256") != sha256(section_bytes).hexdigest()
        or event.get("section_header_count") != len(sections)
        or event.get("section_name_table") != list(name_table)
    ):
        raise ValueError("zero-suffix durable structural fields differ")
    return repaired


def _validate_driver_rows(value: object) -> dict[str, dict[str, int]]:
    rows = _mapping(value, label="direct driver rows")
    fields = {
        "local_size_bytes",
        "registers",
        "shared_size_bytes",
        "maximum_threads_per_block",
    }
    if set(rows) != set(DIRECT_KERNEL_NAMES):
        raise ValueError("zero-suffix driver kernel inventory differs")
    result: dict[str, dict[str, int]] = {}
    for name in DIRECT_KERNEL_NAMES:
        row = _mapping(rows[name], label=f"driver row {name}")
        if set(row) != fields or any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in row.values()
        ):
            raise ValueError(f"zero-suffix driver row differs: {name}")
        result[name] = {key: int(item) for key, item in row.items()}
    return result


def parse_cuobjdump_resource_usage(raw: bytes) -> dict[str, dict[str, int]]:
    if not isinstance(raw, bytes):
        raise TypeError("zero-suffix resource stdout must be bytes")
    try:
        output = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("zero-suffix resource stdout is not strict ASCII") from error
    rows: dict[str, dict[str, int]] = {}
    current: str | None = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        match = re.fullmatch(r"Function\s+([^:]+):", line)
        if match:
            current = match.group(1)
            if current in rows:
                raise ValueError("zero-suffix resource output repeats a function")
            rows[current] = {}
            continue
        if current is None or not line:
            continue
        for label, text in re.findall(r"([A-Z]+(?:\[\d+\])?):(\d+)", line):
            if label in rows[current]:
                raise ValueError("zero-suffix resource output repeats a field")
            rows[current][label] = int(text)
    for name in DIRECT_KERNEL_NAMES:
        if name not in rows or not {"REG", "STACK", "LOCAL"}.issubset(rows[name]):
            raise ValueError("zero-suffix direct resource row is incomplete")
    return {
        name: {field: rows[name][field] for field in ("REG", "STACK", "LOCAL")}
        for name in DIRECT_KERNEL_NAMES
    }


def _validate_temporary(event: Mapping[str, object], repaired: BinaryEvidence) -> str:
    path = event.get("temporary_path")
    if (
        event.get("schema_version") != "legal-river-zero-suffix-temporary-payload-v1"
        or not isinstance(path, str)
        or not path.lower().endswith(".cubin")
        or event.get("readback_sha256") != repaired.sha256
        or event.get("readback_bytes") != repaired.byte_count
        or event.get("matches_durable_repaired_payload") is not True
    ):
        raise ValueError("zero-suffix temporary payload evidence differs")
    return path


def _validate_candidate(
    event: Mapping[str, object],
    expected: Mapping[str, object],
    *,
    index: int,
    temporary_path: str,
) -> CandidateEvidence:
    if (
        event.get("schema_version") != "legal-river-zero-suffix-candidate-command-v1"
        or event.get("candidate_index") != index
        or event.get("candidate_id") != expected.get("candidate_id")
        or event.get("uses_repaired_payload") is not expected.get("uses_repaired_payload")
        or event.get("required_for_suffix_pass")
        is not expected.get("required_for_suffix_pass")
    ):
        raise ValueError("zero-suffix candidate identity differs")
    argv = event.get("argv")
    configured = expected.get("arguments")
    tool = {
        "CUDA_13_3_cuobjdump": r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\cuobjdump.exe",
        "CUDA_13_3_nvdisasm": r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvdisasm.exe",
    }.get(expected.get("tool"))
    if (
        tool is None
        or not isinstance(argv, list)
        or not isinstance(configured, list)
        or len(argv) != len(configured) + 1
        or argv[0] != tool
    ):
        raise ValueError("zero-suffix candidate argv shape differs")
    for observed, frozen in zip(argv[1:], configured, strict=True):
        if frozen == "{exact_repaired_temporary_cubin}":
            if observed != temporary_path:
                raise ValueError("zero-suffix candidate temporary path differs")
        elif observed != frozen:
            raise ValueError("zero-suffix candidate argument differs")
    status = event.get("status")
    return_code = event.get("return_code")
    elapsed = event.get("elapsed_ns")
    if (
        status not in {"completed", "timeout", "output_limit"}
        or (
            return_code is not None
            and (isinstance(return_code, bool) or not isinstance(return_code, int))
        )
        or isinstance(elapsed, bool)
        or not isinstance(elapsed, int)
        or elapsed < 0
        or (status == "completed" and elapsed > 30_000_000_000)
    ):
        raise ValueError("zero-suffix candidate outcome differs")
    return CandidateEvidence(
        candidate_id=str(event["candidate_id"]),
        status=str(status),
        return_code=return_code,
        stdout=decode_binary(
            event.get("stdout"),
            label="candidate stdout",
            maximum_bytes=MAXIMUM_STREAM_BYTES,
        ),
        stderr=decode_binary(
            event.get("stderr"),
            label="candidate stderr",
            maximum_bytes=MAXIMUM_STREAM_BYTES,
        ),
        elapsed_ns=elapsed,
        required=bool(event["required_for_suffix_pass"]),
    )


def _validate_module(
    event: Mapping[str, object], repaired: BinaryEvidence
) -> dict[str, dict[str, int]]:
    if (
        event.get("schema_version") != "legal-river-zero-suffix-module-capture-v1"
        or event.get("repaired_payload_sha256") != repaired.sha256
        or event.get("repaired_payload_bytes") != repaired.byte_count
        or tuple(event.get("kernel_names", ())) != ALL_KERNEL_NAMES
        or event.get("kernel_launch_count") != 0
    ):
        raise ValueError("zero-suffix module capture differs")
    return _validate_driver_rows(event.get("direct_driver_rows"))


def _derive_scientific_terminal(
    *,
    candidates: list[CandidateEvidence],
    module_failure: bool,
    module_rows: Mapping[str, Mapping[str, int]] | None,
    worker_failure: bool,
) -> tuple[str, dict[str, dict[str, int]] | None, str | None]:
    if worker_failure:
        return "diagnostic_failure", None, None
    for candidate in candidates:
        if candidate.status == "timeout":
            return "candidate_timeout_rejection", None, None
        if candidate.status == "output_limit":
            return "candidate_output_limit_rejection", None, None
    if module_failure:
        return "module_load_rejection", None, None
    if module_rows is None:
        return "diagnostic_failure", None, None
    if dict(module_rows) != ORIGINAL_DIRECT_DRIVER_ROWS:
        return "driver_row_rejection", None, None
    if len(candidates) != 6:
        return "diagnostic_failure", None, None
    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    try:
        resources = parse_cuobjdump_resource_usage(
            by_id["cuobjdump_resource_usage"].stdout.raw
        )
    except (KeyError, TypeError, ValueError):
        resources = None
    required_pass = (
        by_id.get("cuobjdump_version") is not None
        and by_id["cuobjdump_version"].return_code == 0
        and by_id["cuobjdump_version"].stdout.raw == _CUOBJDUMP_VERSION_BYTES
        and by_id.get("cuobjdump_resource_usage") is not None
        and by_id["cuobjdump_resource_usage"].return_code == 0
        and by_id.get("cuobjdump_elf") is not None
        and by_id["cuobjdump_elf"].return_code == 0
        and resources is not None
    )
    if not required_pass:
        return "tool_rejection", resources, None
    return "suffix_reconstruction_pass", resources, QUALIFIED_INSTRUMENT


def rebind_zero_suffix_diagnostic_journal(raw: bytes) -> ZeroSuffixDiagnosticRebinding:
    if not isinstance(raw, bytes) or len(raw) > MAXIMUM_ARTIFACT_BYTES:
        raise ValueError("zero-suffix journal bytes differ")
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if recovery.failure is not None or recovery.invalid_suffix_bytes:
        reason = recovery.failure.reason if recovery.failure is not None else "suffix"
        raise ValueError(f"zero-suffix journal is incomplete: {reason}")
    records = recovery.records
    if len(records) < 2:
        raise ValueError("zero-suffix journal omits header or terminal")
    if records[0].body.kind.value != "header" or records[-1].body.kind.value != "terminal":
        raise ValueError("zero-suffix journal endpoints differ")
    _validate_header(records[0].body.payload)
    observations = records[1:-1]
    if len(observations) > 16:
        raise ValueError("zero-suffix observation count exceeds ceiling")
    if any(record.body.kind.value != "observation" for record in observations):
        raise ValueError("zero-suffix journal middle record differs")
    outer = records[-1].body.payload
    terminal = outer.get("terminal")
    passed = outer.get("passed")
    reason = outer.get("reason")
    if (
        outer.get("schema_version") != "legal-river-zero-suffix-owner-terminal-v1"
        or terminal not in _OUTER_TERMINALS
        or not isinstance(passed, bool)
        or passed is not (terminal == "suffix_reconstruction_pass")
        or not isinstance(reason, str)
        or not reason
        or len(reason) > 4096
        or not reason.isascii()
        or outer.get("event_count") != len(observations)
        or outer.get("resource_gate_result") is not None
        or outer.get("calibration_result") is not None
        or outer.get("capacity_projection") is not None
    ):
        raise ValueError("zero-suffix outer terminal differs")
    expected_last = observations[-1].body.semantic_identity_sha256 if observations else None
    if outer.get("last_event_semantic_identity_sha256") != expected_last:
        raise ValueError("zero-suffix outer terminal identity differs")

    config = _load_config()
    source_commit: str | None = None
    kinds: list[str] = []
    events: list[Mapping[str, object]] = []
    for index, record in enumerate(observations):
        payload = record.body.payload
        if (
            payload.get("schema_version") != "legal-river-zero-suffix-observation-v1"
            or payload.get("event_index") != index
            or payload.get("config_sha256") != CONFIG_SHA256
        ):
            raise ValueError("zero-suffix observation envelope differs")
        commit = payload.get("source_commit")
        if not isinstance(commit, str) or len(commit) != 40:
            raise ValueError("zero-suffix observation commit differs")
        if source_commit is None:
            source_commit = commit
        elif source_commit != commit:
            raise ValueError("zero-suffix observation commit changed")
        kind = payload.get("event_kind")
        event = _mapping(payload.get("event"), label="observation event")
        if not isinstance(kind, str):
            raise TypeError("zero-suffix observation kind differs")
        kinds.append(kind)
        events.append(event)

    cursor = 0
    repaired: BinaryEvidence | None = None
    candidates: list[CandidateEvidence] = []
    module_rows: dict[str, dict[str, int]] | None = None
    module_failure = False
    worker_failure = False
    cleanup: Mapping[str, object] | None = None
    terminal_evidence: Mapping[str, object] | None = None
    if events:
        if kinds[0] != "provenance":
            raise ValueError("zero-suffix first observation is not provenance")
        provenance = events[0]
        if (
            provenance.get("schema_version") != "legal-river-zero-suffix-provenance-v1"
            or provenance.get("config_sha256") != CONFIG_SHA256
            or provenance.get("source_commit") != source_commit
            or provenance.get("source_dirty") is not False
            or provenance.get("reserved_actual_result_absent") is not True
            or provenance.get("literal_worker_module") != LITERAL_WORKER_MODULE
            or _RESERVED.exists()
        ):
            raise ValueError("zero-suffix provenance differs")
        _validate_current_dependencies(provenance)
        _validate_retained_artifacts(provenance.get("retained_artifacts"))
        cursor = 1
    if cursor < len(events) and kinds[cursor] == "bootstrap_handshake":
        _validate_handshake(events[cursor])
        cursor += 1
    temporary_path: str | None = None
    if cursor < len(events) and kinds[cursor] == "repaired_payload":
        repaired = _validate_repaired_payload(events[cursor], config)
        cursor += 1
        if cursor >= len(events) or kinds[cursor] != "temporary_payload_ready":
            raise ValueError("zero-suffix temporary evidence is absent")
        temporary_path = _validate_temporary(events[cursor], repaired)
        cursor += 1
        command_rows = config["candidate_commands_in_order"]
        assert isinstance(command_rows, list)
        while cursor < len(events) and kinds[cursor] == "candidate_command":
            if len(candidates) >= len(command_rows):
                raise ValueError("zero-suffix candidate count exceeds inventory")
            expected = _mapping(command_rows[len(candidates)], label="candidate config")
            candidates.append(
                _validate_candidate(
                    events[cursor],
                    expected,
                    index=len(candidates),
                    temporary_path=temporary_path,
                )
            )
            cursor += 1
        if cursor < len(events) and kinds[cursor] == "module_capture":
            module_rows = _validate_module(events[cursor], repaired)
            cursor += 1
        elif cursor < len(events) and kinds[cursor] == "module_failure":
            failure = events[cursor]
            if (
                failure.get("schema_version") != "legal-river-zero-suffix-module-failure-v1"
                or failure.get("repaired_payload_sha256") != repaired.sha256
                or failure.get("repaired_payload_bytes") != repaired.byte_count
                or failure.get("kernel_launch_count") != 0
                or not isinstance(failure.get("reason"), str)
            ):
                raise ValueError("zero-suffix module failure evidence differs")
            module_failure = True
            cursor += 1
        if cursor < len(events) and kinds[cursor] == "cleanup":
            candidate_cleanup = events[cursor]
            if (
                candidate_cleanup.get("schema_version") != "legal-river-zero-suffix-cleanup-v1"
                or candidate_cleanup.get("temporary_payload_removed") is not True
                or candidate_cleanup.get("candidate_events_retained") != len(candidates)
                or candidate_cleanup.get("module_event_retained")
                is not (module_rows is not None or module_failure)
            ):
                raise ValueError("zero-suffix cleanup differs")
            cleanup = candidate_cleanup
            cursor += 1
    if cursor < len(events) and kinds[cursor] == "worker_failure":
        failure = events[cursor]
        if (
            failure.get("schema_version") != "legal-river-zero-suffix-worker-failure-v1"
            or not isinstance(failure.get("reason"), str)
        ):
            raise ValueError("zero-suffix worker failure differs")
        worker_failure = True
        cursor += 1
    if cursor < len(events) and kinds[cursor] == "terminal_evidence":
        terminal_evidence = events[cursor]
        cursor += 1
    if cursor != len(events):
        raise ValueError("zero-suffix observation order differs")

    resource_rows: dict[str, dict[str, int]] | None = None
    qualified: str | None = None
    if terminal_evidence is not None:
        evidence_reason = terminal_evidence.get("reason")
        if (
            terminal_evidence.get("schema_version")
            != "legal-river-zero-suffix-terminal-evidence-v1"
            or terminal_evidence.get("terminal") != terminal
            or terminal_evidence.get("passed") is not passed
            or terminal_evidence.get("candidate_events_retained") != len(candidates)
            or terminal_evidence.get("resource_gate_result") is not None
            or terminal_evidence.get("calibration_result") is not None
            or terminal_evidence.get("capacity_projection") is not None
            or not isinstance(evidence_reason, str)
            or not evidence_reason
        ):
            raise ValueError("zero-suffix terminal evidence differs")
        if terminal == "structural_rejection":
            if repaired is not None or candidates or module_rows is not None:
                raise ValueError("zero-suffix structural rejection opened later evidence")
        elif terminal == "laboratory_wall_rejection":
            pass
        else:
            derived, resource_rows, qualified = _derive_scientific_terminal(
                candidates=candidates,
                module_failure=module_failure,
                module_rows=module_rows,
                worker_failure=worker_failure,
            )
            if terminal != derived:
                raise ValueError(
                    f"zero-suffix terminal differs from independent derivation: {derived}"
                )
        if terminal_evidence.get("qualified_resource_instrument") != qualified:
            raise ValueError("zero-suffix qualified instrument differs")
        retained_rows = terminal_evidence.get("resource_rows")
        expected_rows = resource_rows
        if retained_rows != expected_rows:
            raise ValueError("zero-suffix terminal resource rows differ")
        if outer.get("qualified_resource_instrument") != qualified:
            raise ValueError("zero-suffix outer qualified instrument differs")
        if outer.get("resource_rows") != expected_rows:
            raise ValueError("zero-suffix outer resource rows differ")
    elif terminal not in {"infrastructure_failure", "laboratory_wall_rejection"}:
        raise ValueError("zero-suffix scientific terminal evidence is absent")
    elif (
        outer.get("qualified_resource_instrument") is not None
        or outer.get("resource_rows") is not None
    ):
        raise ValueError("zero-suffix infrastructure terminal opened claims")

    if terminal == "suffix_reconstruction_pass" and (
        repaired is None
        or len(candidates) != 6
        or module_rows != ORIGINAL_DIRECT_DRIVER_ROWS
        or cleanup is None
        or qualified != QUALIFIED_INSTRUMENT
        or resource_rows is None
    ):
        raise ValueError("zero-suffix passing inventory differs")
    return ZeroSuffixDiagnosticRebinding(
        terminal=str(terminal),
        passed=passed,
        event_count=len(observations),
        source_commit=source_commit,
        repaired_payload=repaired,
        candidates=tuple(candidates),
        module_driver_rows=module_rows,
        resource_rows=resource_rows,
        qualified_resource_instrument=qualified,
        cleanup=cleanup,
        journal_byte_count=len(raw),
    )


def rebind_zero_suffix_diagnostic_file(
    path: Path = _RESULT,
) -> ZeroSuffixDiagnosticRebinding:
    recovery = recover_journal_file(
        path,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise ValueError(
            f"zero-suffix diagnostic result is incomplete: {recovery.failure.reason}"
        )
    return rebind_zero_suffix_diagnostic_journal(path.read_bytes())


__all__ = [
    "BinaryEvidence",
    "CAMPAIGN_SHA256",
    "CandidateEvidence",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "PROTOCOL_SHA256",
    "RESULT_RELATIVE_PATH",
    "ZeroSuffixDiagnosticRebinding",
    "canonical_lf_sha256",
    "decode_binary",
    "parse_cuobjdump_resource_usage",
    "rebind_zero_suffix_diagnostic_file",
    "rebind_zero_suffix_diagnostic_journal",
]
