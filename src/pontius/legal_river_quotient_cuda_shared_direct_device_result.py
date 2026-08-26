"""Independent standard-library reader for the ADR-0419 device journal."""

from __future__ import annotations

from base64 import b64decode, b64encode
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
import math
from math import comb
from pathlib import Path
import re
import struct
from typing import Mapping, Sequence

from .durable_evidence_journal import (
    JournalRecordKind,
    canonical_journal_json_bytes,
    recover_journal_bytes,
)


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-cuda-shared-direct-device-v1.json"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_shared_direct_device_v1.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
_CONFIG = _ROOT / CONFIG_RELATIVE_PATH
_RESULT = _ROOT / RESULT_RELATIVE_PATH
CONFIG_SHA256 = (
    "1dcc3f1ae2d528ab0625c3024f5dc04238ee49df9b6fbdc750b0e6e9352854d3"
)
PREREGISTRATION_COMMIT = "a457f8f73d2f69a66ac3d52361d1e96ddf0f02ac"
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0419-shared-direct-device-exclusive-journal-v1"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0419-shared-direct-device-one-shot-campaign-v1"
).hexdigest()
BUILT_CUDA_SOURCE_SHA256 = (
    "e2049c53eae383a604efd656c6eb18ed54994bfed09f81cc42abff403d757ee4"
)
REFERENCE_REPAIRED_CUBIN_SHA256 = (
    "97693be7baafd882ad64a1a7da0ede23dc927efd872b0d15697b2486957ea894"
)
MAXIMUM_ARTIFACT_BYTES = 67_108_864
MAXIMUM_EVENT_COUNT = 4096
STREAM_CHUNK_BYTES = 196_608
MAXIMUM_STREAM_BYTES = 8_388_608
COMMAND_WALL_NS = 30_000_000_000
MAXIMUM_ALIGNMENT = 4_294_967_296
REGISTER_LIMIT = 255
BACKING_LIMIT = 4096
RESIDENT_THREAD_LIMIT = 131_072
DEVICE_RESERVE_BYTES = 2_000_000_000
POPULATION_WALL_NS = 90_000_000_000
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_cuda_shared_direct_device_runner"
)
DIRECT_KERNEL_NAMES = (
    "direct_selected_queries_tile",
    "direct_selected_fold_tile",
    "direct_selected_adjoint_tile",
)
ALLOWED_TERMINALS = {
    "completed_validation_pass",
    "compiler_container_rejection",
    "resource_rejection",
    "complete_ten_differential_rejection",
    "population_scientific_rejection",
    "population_wall_rejection",
    "laboratory_wall_rejection",
    "infrastructure_failure",
}

DEPENDENCY_RELATIVE_PATHS = (
    CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0419-preregister-the-shared-direct-device-differential.md",
    "docs/decisions/ADR-0418-source-seal-the-shared-selected-direct-oracle.md",
    "src/pontius/legal_river_quotient_cuda_shared_direct_oracle.py",
    "tests/test_legal_river_quotient_cuda_shared_direct_oracle.py",
    "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
    "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v1.json",
    "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v2.json",
    (
        "artifacts/work_preflight/"
        "legal_river_quotient_cuda_compensated_work_preflight_v4.jsonl"
    ),
    (
        "artifacts/work_preflight/"
        "legal_river_exact_cubin_zero_suffix_diagnostic_v1.jsonl"
    ),
    "src/pontius/legal_river_quotient_cuda_shared_direct_device.py",
    "src/pontius/legal_river_quotient_cuda_shared_direct_device_runner.py",
    "src/pontius/legal_river_quotient_cuda_shared_direct_device_result.py",
    "tests/test_legal_river_quotient_cuda_shared_direct_device.py",
    "src/pontius/durable_evidence_journal.py",
)

PHASE_ORDER = (
    "fixture_and_resident_birth",
    "forward_source_and_offset",
    "shared_direct_fold_and_query",
    "forward_recurrence",
    "forward_signed_targets",
    "forward_fold_and_global_tree",
    "forward_capture_and_digest",
    "forward_release",
    "adjoint_covector_and_labels",
    "adjoint_recurrence_and_signed_sources",
    "direct_adjoint",
    "adjoint_source_contract_and_global_tree",
    "adjoint_capture_digest_and_exact_stream",
    "mutations_and_lifecycle",
    "final_release",
)
FAMILIES = (
    "default_chunks_forward_tile_order",
    "alternate_chunks_reverse_tile_order",
)
_ALLOWED_TRANSITIONS = {
    "fixture_and_resident_birth": ("forward_source_and_offset",),
    "forward_source_and_offset": ("shared_direct_fold_and_query",),
    "shared_direct_fold_and_query": ("forward_recurrence",),
    "forward_recurrence": ("forward_signed_targets",),
    "forward_signed_targets": ("forward_fold_and_global_tree",),
    "forward_fold_and_global_tree": (
        "forward_signed_targets",
        "forward_capture_and_digest",
    ),
    "forward_capture_and_digest": (
        "forward_source_and_offset",
        "forward_release",
    ),
    "forward_release": ("adjoint_covector_and_labels",),
    "adjoint_covector_and_labels": (
        "adjoint_recurrence_and_signed_sources",
    ),
    "adjoint_recurrence_and_signed_sources": (
        "direct_adjoint",
        "adjoint_source_contract_and_global_tree",
    ),
    "direct_adjoint": ("adjoint_recurrence_and_signed_sources",),
    "adjoint_source_contract_and_global_tree": (
        "adjoint_recurrence_and_signed_sources",
        "adjoint_capture_digest_and_exact_stream",
    ),
    "adjoint_capture_digest_and_exact_stream": (
        "adjoint_covector_and_labels",
        "mutations_and_lifecycle",
    ),
    "mutations_and_lifecycle": ("final_release",),
    "final_release": (),
}
_PHASE_COUNTERS = {
    "forward_source_and_offset": {
        "source_pairing_visits",
        "source_weight_pair_times_float64",
    },
    "shared_direct_fold_and_query": {
        "shared_direct_source_unranks",
        "shared_direct_compatible_coefficient_pair_adds",
        "shared_direct_boundary_pair_copies",
        "shared_direct_final_feature_pair_products",
    },
    "forward_recurrence": {
        "forward_recurrence_pair_child_adds",
        "forward_pair_divides",
    },
    "forward_signed_targets": {"forward_signed_subset_pair_terms"},
    "forward_fold_and_global_tree": {
        "forward_fold_pair_times_pair",
        "forward_tree_contributions",
    },
    "adjoint_covector_and_labels": {
        "adjoint_covector_pair_times_float64",
        "adjoint_label_pair_adds",
    },
    "adjoint_recurrence_and_signed_sources": {
        "adjoint_recurrence_pair_child_adds",
        "adjoint_pair_divides",
        "adjoint_signed_subset_pair_terms",
    },
    "direct_adjoint": {
        "direct_adjoint_compatible_query_weight_builds",
        "direct_adjoint_compatible_boundary_pair_adds",
        "direct_adjoint_query_record_visits",
        "direct_adjoint_source_unranks",
    },
    "adjoint_source_contract_and_global_tree": {
        "adjoint_source_pairing_visits",
        "adjoint_source_weight_pair_times_float64",
        "adjoint_contract_pair_times_pair",
        "adjoint_tree_contributions",
    },
}

_ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
_PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
_SECTION_HEADER = struct.Struct("<IIQQQQIIQQ")
_SHT_NOBITS = 8

CLAIMS = {
    "device_differential_result": None,
    "complete_10_result": None,
    "complete_22_result": None,
    "capacity_projection": None,
    "complete_25_numerical_value": None,
    "actual_45_card_value": None,
    "resolver_iteration_result": None,
    "solve_result": None,
    "action_result": None,
    "action_clock_result": None,
    "decision_quality_result": None,
    "truncation_authorized": False,
    "blueprint_result": None,
    "poker_strength_result": None,
}


@dataclass(frozen=True, slots=True)
class ReboundPhase:
    population: int
    family: str
    ordinal: int
    phase: str
    host_start_ns: int
    host_stop_ns: int
    host_ns: int
    work: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class SharedDirectDeviceRebinding:
    terminal: str
    passed: bool
    source_commit: str
    container_mode: str | None
    compiler_payload_sha256: str | None
    shared_cubin_sha256: str | None
    complete_ten_control_passed: bool | None
    populations: tuple[int, ...]
    phases: tuple[ReboundPhase, ...]
    event_count: int


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"shared-direct reader path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    return value


def _integer(value: object, *, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer at least {minimum}")
    return value


def _digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a SHA-256 digest")
    return value


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _load_config() -> dict[str, object]:
    raw = _CONFIG.read_bytes()
    if sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != CONFIG_SHA256:
        raise ValueError("shared-direct reader config identity differs")
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema_version") != (
        "legal-river-quotient-cuda-shared-direct-device-preregistration-v1"
    ):
        raise ValueError("shared-direct reader config schema differs")
    return value


def _fraction(value: object, *, label: str) -> Fraction:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes, bytearray))
        or len(value) != 2
    ):
        raise ValueError(f"{label} must be an exact fraction pair")
    numerator = value[0]
    denominator = value[1]
    if (
        isinstance(numerator, bool)
        or not isinstance(numerator, int)
        or isinstance(denominator, bool)
        or not isinstance(denominator, int)
        or denominator <= 0
    ):
        raise ValueError(f"{label} fraction fields differ")
    return Fraction(numerator, denominator)


def _bounded_range(offset: int, size: int, limit: int, *, label: str) -> int:
    if min(offset, size, limit) < 0 or offset > limit or size > limit - offset:
        raise ValueError(f"shared-direct reader {label} lies outside payload")
    return offset + size


def _classify_payload(raw: bytes) -> tuple[str, bytes, dict[str, object]]:
    if not isinstance(raw, bytes) or len(raw) < _ELF_HEADER.size:
        raise ValueError("shared-direct reader compiler payload differs")
    header = _ELF_HEADER.unpack_from(raw, 0)
    (
        ident,
        _etype,
        _machine,
        _version,
        _entry,
        phoff,
        shoff,
        _flags,
        ehsize,
        phentsize,
        phnum,
        shentsize,
        shnum,
        shstrndx,
    ) = header
    if (
        not ident.startswith(b"\x7fELF\x02\x01")
        or ehsize != _ELF_HEADER.size
        or phentsize != _PROGRAM_HEADER.size
        or shentsize != _SECTION_HEADER.size
        or phnum <= 0
        or shnum <= 0
        or not 0 <= shstrndx < shnum
    ):
        raise ValueError("shared-direct reader ELF header differs")
    ph_end = phoff + phentsize * phnum
    sh_end = shoff + shentsize * shnum
    if max(ph_end, sh_end) <= len(raw):
        mode = "complete_elf_without_edit"
        loaded = raw
    else:
        final = raw[phoff + phentsize * (phnum - 1) :]
        low = int.from_bytes(final[-7:], "little") if len(final) == 55 else -1
        valid = low in {0, 1} or (
            1 < low <= MAXIMUM_ALIGNMENT and low & (low - 1) == 0
        )
        if not (
            sh_end <= len(raw)
            and ph_end == len(raw) + 1
            and len(final) == 55
            and valid
        ):
            raise ValueError("shared-direct reader one-zero shape differs")
        mode = "one_zero_final_program_alignment_completion"
        loaded = raw + b"\x00"
    programs = tuple(
        _PROGRAM_HEADER.unpack_from(loaded, phoff + i * phentsize)
        for i in range(phnum)
    )
    for index, row in enumerate(programs):
        _type, _flags, offset, _vaddr, _paddr, size, memory, align = row
        _bounded_range(offset, size, len(loaded), label=f"program {index}")
        if memory < size or not (
            align in {0, 1}
            or (
                1 < align <= MAXIMUM_ALIGNMENT
                and align & (align - 1) == 0
            )
        ):
            raise ValueError("shared-direct reader program header differs")
    section_end = _bounded_range(
        shoff, shentsize * shnum, len(loaded), label="section table"
    )
    section_bytes = loaded[shoff:section_end]
    sections = tuple(
        _SECTION_HEADER.unpack_from(section_bytes, i * shentsize)
        for i in range(shnum)
    )
    for index, row in enumerate(sections):
        _name, section_type, _flags, _address, offset, size, *_rest = row
        if section_type != _SHT_NOBITS:
            _bounded_range(offset, size, len(loaded), label=f"section {index}")
    names = sections[shstrndx]
    if names[1] == _SHT_NOBITS:
        raise ValueError("shared-direct reader name table differs")
    _bounded_range(names[4], names[5], len(loaded), label="name table")
    details = {
        "raw_sha256": sha256(raw).hexdigest(),
        "raw_bytes": len(raw),
        "loaded_sha256": sha256(loaded).hexdigest(),
        "loaded_bytes": len(loaded),
        "program_header_count": len(programs),
        "section_header_count": len(sections),
        "section_table_sha256": sha256(section_bytes).hexdigest(),
        "header": dict(
            zip(
                (
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
                ),
                (header[0].hex(), *header[1:]),
                strict=True,
            )
        ),
    }
    return mode, loaded, details


def _decode_chunk(event: Mapping[str, object]) -> tuple[str, int, int, bytes]:
    expected = {
        "schema_version",
        "stream_id",
        "chunk_index",
        "chunk_count",
        "chunk_raw_bytes",
        "total_raw_bytes",
        "total_sha256",
        "chunk_base64",
    }
    if set(event) != expected or event.get("schema_version") != (
        "legal-river-shared-direct-raw-chunk-v1"
    ):
        raise ValueError("shared-direct reader raw chunk fields differ")
    stream_id = event.get("stream_id")
    index = _integer(event.get("chunk_index"), label="chunk index")
    count = _integer(event.get("chunk_count"), label="chunk count", minimum=1)
    size = _integer(event.get("chunk_raw_bytes"), label="chunk bytes", minimum=1)
    total = _integer(event.get("total_raw_bytes"), label="stream bytes", minimum=1)
    digest = _digest(event.get("total_sha256"), label="stream digest")
    encoded = event.get("chunk_base64")
    if (
        not isinstance(stream_id, str)
        or not stream_id
        or index >= count
        or size > STREAM_CHUNK_BYTES
        or total > MAXIMUM_STREAM_BYTES
        or not isinstance(encoded, str)
        or not encoded.isascii()
    ):
        raise ValueError("shared-direct reader raw chunk boundary differs")
    try:
        raw = b64decode(encoded.encode("ascii"), validate=True)
    except (TypeError, ValueError) as error:
        raise ValueError("shared-direct reader raw chunk base64 differs") from error
    if (
        len(raw) != size
        or b64encode(raw).decode("ascii") != encoded
        or (index < count - 1 and size != STREAM_CHUNK_BYTES)
        or event.get("total_raw_bytes") != total
        or event.get("total_sha256") != digest
    ):
        raise ValueError("shared-direct reader raw chunk bytes differ")
    return stream_id, index, count, raw


def _reconstruct_stream(
    indexed: Sequence[tuple[int, Mapping[str, object]]],
    *,
    stream_id: str,
    terminal_position: int,
) -> bytes:
    rows = [(position, event) for position, event in indexed if event.get("stream_id") == stream_id]
    if not rows:
        return b""
    decoded = [_decode_chunk(event) for _, event in rows]
    if (
        any(row[0] != stream_id for row in decoded)
        or [row[1] for row in decoded] != list(range(decoded[0][2]))
        or len(decoded) != decoded[0][2]
        or len({row[2] for row in decoded}) != 1
        or [position for position, _ in rows] != sorted(position for position, _ in rows)
        or any(position >= terminal_position for position, _ in rows)
    ):
        raise ValueError("shared-direct reader raw chunk sequence differs")
    totals = {event.get("total_raw_bytes") for _, event in rows}
    digests = {event.get("total_sha256") for _, event in rows}
    raw = b"".join(row[3] for row in decoded)
    if totals != {len(raw)} or digests != {sha256(raw).hexdigest()}:
        raise ValueError("shared-direct reader raw stream envelope differs")
    return raw


def _accepted_ascii(raw: bytes, *, maximum: int, label: str) -> str:
    if len(raw) > maximum or any(
        byte not in {9, 10, 13} and not 0x20 <= byte <= 0x7E for byte in raw
    ):
        raise ValueError(f"shared-direct reader {label} parser admission differs")
    return raw.decode("ascii")


def _parse_resources(output: str) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    current: str | None = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        function = re.fullmatch(r"Function\s+([^:]+):", line)
        if function:
            current = function.group(1)
            if current in result:
                raise ValueError("shared-direct reader resource function repeats")
            result[current] = {}
            continue
        if current is None or not line:
            continue
        for label, raw_value in re.findall(r"([A-Z]+(?:\[\d+\])?):(\d+)", line):
            if label in result[current]:
                raise ValueError("shared-direct reader resource field repeats")
            result[current][label] = int(raw_value)
    if not set(DIRECT_KERNEL_NAMES).issubset(result):
        raise ValueError("shared-direct reader direct resource rows are absent")
    direct = {name: result[name] for name in DIRECT_KERNEL_NAMES}
    if any(not {"REG", "STACK", "LOCAL"}.issubset(row) for row in direct.values()):
        raise ValueError("shared-direct reader direct resource row is incomplete")
    return direct


def _reconstruct_commands(
    indexed_events: Sequence[tuple[int, str, Mapping[str, object]]]
) -> tuple[dict[str, dict[str, object]], dict[str, int]]:
    chunks = [
        (position, event)
        for position, kind, event in indexed_events
        if kind == "resource_command_chunk"
    ]
    terminals = [
        (position, event)
        for position, kind, event in indexed_events
        if kind == "resource_command_terminal"
    ]
    if len(terminals) > 2:
        raise ValueError("shared-direct reader command cardinality differs")
    expected_order = (
        ("cuobjdump_version", "cuobjdump --version"),
        (
            "cuobjdump_resource_usage",
            "cuobjdump --dump-resource-usage shared-payload",
        ),
    )
    result: dict[str, dict[str, object]] = {}
    positions: dict[str, int] = {}
    consumed: set[str] = set()
    previous_terminal = -1
    for ordinal, (position, terminal) in enumerate(terminals):
        command_id, role = expected_order[ordinal]
        expected_fields = {
            "schema_version",
            "command_id",
            "argv_role",
            "status",
            "return_code",
            "stdout_bytes",
            "stdout_sha256",
            "stderr_bytes",
            "stderr_sha256",
            "elapsed_ns",
        }
        if (
            set(terminal) != expected_fields
            or terminal.get("schema_version")
            != "legal-river-shared-direct-command-v1"
            or terminal.get("command_id") != command_id
            or terminal.get("argv_role") != role
        ):
            raise ValueError("shared-direct reader command terminal differs")
        status = terminal.get("status")
        return_code = terminal.get("return_code")
        elapsed = _integer(terminal.get("elapsed_ns"), label="command elapsed")
        if (
            status not in {"completed", "timeout", "output_limit"}
            or (
                return_code is not None
                and (isinstance(return_code, bool) or not isinstance(return_code, int))
            )
            or (status == "completed" and elapsed > COMMAND_WALL_NS)
        ):
            raise ValueError("shared-direct reader command outcome differs")
        streams: dict[str, bytes] = {}
        for stream in ("stdout", "stderr"):
            stream_id = f"{command_id}:{stream}"
            relevant = [(p, e) for p, e in chunks if e.get("stream_id") == stream_id]
            raw = _reconstruct_stream(
                relevant,
                stream_id=stream_id,
                terminal_position=position,
            )
            if relevant and any(p <= previous_terminal for p, _ in relevant):
                raise ValueError("shared-direct reader command chunk placement differs")
            declared_size = _integer(
                terminal.get(f"{stream}_bytes"), label=f"{stream} bytes"
            )
            declared_digest = _digest(
                terminal.get(f"{stream}_sha256"), label=f"{stream} digest"
            )
            if len(raw) != declared_size or sha256(raw).hexdigest() != declared_digest:
                raise ValueError("shared-direct reader command stream differs")
            streams[stream] = raw
            if relevant:
                consumed.add(stream_id)
        result[command_id] = {
            "status": status,
            "return_code": return_code,
            "elapsed_ns": elapsed,
            **streams,
        }
        positions[command_id] = position
        previous_terminal = position
    observed_stream_ids = {str(event.get("stream_id")) for _, event in chunks}
    if observed_stream_ids != consumed:
        raise ValueError("shared-direct reader command stream is orphaned")
    return result, positions


def _validate_resource(
    event: Mapping[str, object],
    commands: Mapping[str, Mapping[str, object]],
    *,
    loaded: bytes,
) -> None:
    expected_fields = {
        "schema_version",
        "tool_version",
        "shared_cubin_sha256",
        "shared_cubin_bytes",
        "direct",
        "driver_direct",
        "effective_maxima",
        "runtime_residency",
        "gates",
        "exact_spill_load_store_count",
    }
    if (
        set(event) != expected_fields
        or event.get("schema_version") != "legal-river-shared-direct-resource-v1"
        or set(commands) != {"cuobjdump_version", "cuobjdump_resource_usage"}
    ):
        raise ValueError("shared-direct reader resource fields differ")
    version = commands["cuobjdump_version"]
    resource_command = commands["cuobjdump_resource_usage"]
    if any(
        row.get("status") != "completed" or row.get("return_code") != 0
        for row in (version, resource_command)
    ):
        raise ValueError("shared-direct reader resource follows failed command")
    version_raw = b"\n".join(
        value.strip()
        for value in (version["stdout"], version["stderr"])
        if isinstance(value, bytes) and value.strip()
    )
    version_text = _accepted_ascii(version_raw, maximum=32_768, label="version")
    if (
        re.search(r"(?<!\d)13\.3(?!\d)", version_text) is None
        or event.get("tool_version") != version_text
    ):
        raise ValueError("shared-direct reader resource tool version differs")
    resource_stdout = resource_command["stdout"]
    assert isinstance(resource_stdout, bytes)
    parsed = _parse_resources(
        _accepted_ascii(resource_stdout, maximum=262_144, label="resource")
    )
    direct = _mapping(event.get("direct"), label="resource direct")
    if direct != parsed:
        raise ValueError("shared-direct reader parsed resource rows differ")
    driver = _mapping(event.get("driver_direct"), label="resource driver")
    if set(driver) != set(DIRECT_KERNEL_NAMES):
        raise ValueError("shared-direct reader driver kernel set differs")
    maxima: dict[str, dict[str, int]] = {}
    for name in DIRECT_KERNEL_NAMES:
        cubin_row = _mapping(direct[name], label=f"resource cubin {name}")
        driver_row = _mapping(driver[name], label=f"resource driver {name}")
        if set(driver_row) != {
            "local_size_bytes",
            "registers",
            "shared_size_bytes",
            "maximum_threads_per_block",
        }:
            raise ValueError("shared-direct reader driver fields differ")
        for value in (*cubin_row.values(), *driver_row.values()):
            _integer(value, label="resource integer")
        maxima[name] = {
            "registers": max(int(driver_row["registers"]), int(cubin_row["REG"])),
            "stack_plus_local_backing_bytes": max(
                int(driver_row["local_size_bytes"]),
                int(cubin_row["STACK"]) + int(cubin_row["LOCAL"]),
            ),
        }
    residency = _mapping(event.get("runtime_residency"), label="resource residency")
    multiprocessors = _integer(
        residency.get("multiprocessor_count"), label="multiprocessors", minimum=1
    )
    threads_per = _integer(
        residency.get("maximum_threads_per_multiprocessor"),
        label="threads per multiprocessor",
        minimum=1,
    )
    resident_threads = multiprocessors * threads_per
    resident_backing = resident_threads * BACKING_LIMIT
    expected_residency = {
        "multiprocessor_count": multiprocessors,
        "maximum_threads_per_multiprocessor": threads_per,
        "maximum_resident_threads": resident_threads,
        "backing_ceiling_bytes_per_thread": BACKING_LIMIT,
        "maximum_resident_backing_bytes": resident_backing,
        "frozen_device_reserve_bytes": DEVICE_RESERVE_BYTES,
    }
    expected_gates = {
        "register_ceiling": all(row["registers"] <= REGISTER_LIMIT for row in maxima.values()),
        "local_and_stack_ceiling": all(
            row["stack_plus_local_backing_bytes"] <= BACKING_LIMIT
            for row in maxima.values()
        ),
        "resident_thread_bound": resident_threads <= RESIDENT_THREAD_LIMIT,
        "resident_backing_within_device_reserve": (
            resident_threads <= RESIDENT_THREAD_LIMIT
            and resident_backing <= DEVICE_RESERVE_BYTES
        ),
    }
    if (
        event.get("shared_cubin_sha256") != sha256(loaded).hexdigest()
        or event.get("shared_cubin_bytes") != len(loaded)
        or event.get("effective_maxima") != maxima
        or event.get("runtime_residency") != expected_residency
        or event.get("gates") != expected_gates
        or event.get("exact_spill_load_store_count") is not None
    ):
        raise ValueError("shared-direct reader resource derivation differs")


def expected_shared_campaign_work(available_cards: int) -> dict[str, int]:
    """Independently rederive the complete two-family/two-repeat work."""

    if available_cards not in (10, 22):
        raise ValueError("shared-direct reader population differs")
    source_cards = 6
    query_cards = 4
    labels = 6
    width = 176
    executions = 4
    tiles = 3
    selected = 16
    boundary = 8
    source = comb(available_cards, source_cards)
    query = comb(available_cards, query_cards)
    records = labels * query
    compatible_sources = comb(available_cards - query_cards, source_cards)
    compatible_records = labels * comb(available_cards - source_cards, query_cards)
    forward_terms = 1 << query_cards
    adjoint_terms = sum(comb(source_cards, level) for level in range(5))
    return {
        "source_pairing_visits": source * 90 * executions * tiles,
        "source_weight_pair_times_float64": (
            source * 90 * source_cards * executions * tiles
        ),
        "forward_recurrence_pair_child_adds": (
            executions
            * width
            * sum(
                comb(available_cards, level) * (available_cards - level)
                for level in range(source_cards)
            )
        ),
        "forward_pair_divides": (
            executions
            * width
            * sum(comb(available_cards, level) for level in range(source_cards))
        ),
        "forward_signed_subset_pair_terms": executions * records * width * forward_terms,
        "forward_fold_pair_times_pair": executions * records * width,
        "forward_tree_contributions": executions * records * (tiles + 1),
        "adjoint_covector_pair_times_float64": executions * records * width,
        "adjoint_label_pair_adds": executions * query * labels * width,
        "adjoint_recurrence_pair_child_adds": (
            executions
            * width
            * sum(
                comb(available_cards, level) * (available_cards - level)
                for level in range(query_cards)
            )
        ),
        "adjoint_pair_divides": (
            executions
            * width
            * sum(comb(available_cards, level) for level in range(query_cards))
        ),
        "adjoint_signed_subset_pair_terms": executions * source * width * adjoint_terms,
        "adjoint_source_pairing_visits": source * 90 * executions * tiles,
        "adjoint_source_weight_pair_times_float64": (
            source * 90 * source_cards * executions * tiles
        ),
        "adjoint_contract_pair_times_pair": executions * source * width,
        "adjoint_tree_contributions": executions * source * tiles,
        "shared_direct_source_unranks": selected * source * tiles * executions,
        "shared_direct_compatible_coefficient_pair_adds": (
            selected * compatible_sources * width * executions
        ),
        "shared_direct_final_feature_pair_products": selected * width * executions,
        "shared_direct_boundary_pair_copies": 512,
        "direct_adjoint_source_unranks": selected * tiles * executions,
        "direct_adjoint_query_record_visits": selected * records * tiles * executions,
        "direct_adjoint_compatible_query_weight_builds": (
            selected * compatible_records * tiles * executions
        ),
        "direct_adjoint_compatible_boundary_pair_adds": (
            selected * compatible_records * boundary * executions
        ),
    }


def _expected_chunks(population: int, family: str) -> tuple[int, int, int]:
    values = {
        10: {
            FAMILIES[0]: (17, 3, 11),
            FAMILIES[1]: (13, 2, 7),
        },
        22: {
            FAMILIES[0]: (32768, 4096, 32768),
            FAMILIES[1]: (16381, 2047, 16381),
        },
    }
    try:
        return values[population][family]
    except KeyError as error:
        raise ValueError("shared-direct reader phase identity differs") from error


def _parse_phase(event: Mapping[str, object]) -> ReboundPhase:
    expected_fields = {
        "schema_version",
        "ordinal",
        "population",
        "family",
        "repeat",
        "tile",
        "phase",
        "host_start_ns",
        "host_stop_ns",
        "host_ns",
        "device_ns",
        "chunks",
        "work",
    }
    if set(event) != expected_fields or event.get("schema_version") != (
        "legal-river-shared-direct-phase-v1"
    ):
        raise ValueError("shared-direct reader phase fields differ")
    population = _integer(event.get("population"), label="phase population", minimum=1)
    family = event.get("family")
    ordinal = _integer(event.get("ordinal"), label="phase ordinal")
    repeat = _integer(event.get("repeat"), label="phase repeat")
    tile = _integer(event.get("tile"), label="phase tile")
    phase = event.get("phase")
    start = _integer(event.get("host_start_ns"), label="phase start")
    stop = _integer(event.get("host_stop_ns"), label="phase stop")
    elapsed = _integer(event.get("host_ns"), label="phase elapsed")
    _integer(event.get("device_ns"), label="phase device elapsed")
    chunks = event.get("chunks")
    if (
        not isinstance(family, str)
        or family not in FAMILIES
        or not isinstance(phase, str)
        or phase not in PHASE_ORDER
        or tile > 2
        or stop < start
        or elapsed != stop - start
        or list(_expected_chunks(population, family)) != chunks
    ):
        raise ValueError("shared-direct reader phase boundary differs")
    work = _mapping(event.get("work"), label="phase work")
    allowed = _PHASE_COUNTERS.get(phase, set())
    if not set(work).issubset(allowed):
        raise ValueError("shared-direct reader phase work is misplaced")
    rebound_work: dict[str, int] = {}
    for name, value in work.items():
        rebound_work[str(name)] = _integer(value, label=f"phase work {name}")
    return ReboundPhase(
        population=population,
        family=family,
        ordinal=ordinal,
        phase=phase,
        host_start_ns=start,
        host_stop_ns=stop,
        host_ns=elapsed,
        work=rebound_work,
    )


def _validate_phase_group(rows: Sequence[ReboundPhase]) -> None:
    if not rows:
        raise ValueError("shared-direct reader phase group is empty")
    if [row.ordinal for row in rows] != list(range(len(rows))):
        raise ValueError("shared-direct reader phase ordinals differ")
    if rows[0].phase != PHASE_ORDER[0] or rows[-1].phase != PHASE_ORDER[-1]:
        raise ValueError("shared-direct reader phase endpoints differ")
    if {row.phase for row in rows} != set(PHASE_ORDER):
        raise ValueError("shared-direct reader phase coverage differs")
    for left, right in zip(rows, rows[1:]):
        if (
            left.population != right.population
            or left.family != right.family
            or left.host_stop_ns != right.host_start_ns
            or right.phase not in _ALLOWED_TRANSITIONS[left.phase]
        ):
            raise ValueError("shared-direct reader phase partition differs")
    if sum(row.host_ns for row in rows) != rows[-1].host_stop_ns - rows[0].host_start_ns:
        raise ValueError("shared-direct reader phase sum differs")


_ERROR_LIMITS = {
    "source_absolute": Fraction.from_float(2e-12),
    "source_scale_relative": Fraction.from_float(2e-11),
    "direct_forward_absolute": Fraction.from_float(2e-10),
    "direct_forward_scale_relative": Fraction.from_float(2e-11),
    "direct_fold_absolute": Fraction.from_float(2e-10),
    "direct_fold_scale_relative": Fraction.from_float(2e-11),
    "direct_adjoint_absolute": Fraction.from_float(2e-10),
    "direct_adjoint_scale_relative": Fraction.from_float(2e-11),
    "captured_forward_transpose_absolute": Fraction.from_float(2e-10),
    "captured_forward_transpose_relative": Fraction.from_float(2e-11),
    "device_forward_transpose_absolute": Fraction.from_float(2e-10),
    "device_forward_transpose_relative": Fraction.from_float(2e-11),
    "device_reducer_forward_absolute": Fraction.from_float(2e-10),
    "device_reducer_transpose_absolute": Fraction.from_float(2e-10),
}
_ERROR_TO_GATE = {
    "source_absolute": "selected_fraction_source_absolute",
    "source_scale_relative": "selected_fraction_source_relative",
    "direct_forward_absolute": "selected_direct_forward_absolute",
    "direct_forward_scale_relative": "selected_direct_forward_relative",
    "direct_fold_absolute": "selected_direct_fold_absolute",
    "direct_fold_scale_relative": "selected_direct_fold_relative",
    "direct_adjoint_absolute": "selected_direct_adjoint_absolute",
    "direct_adjoint_scale_relative": "selected_direct_adjoint_relative",
    "captured_forward_transpose_absolute": "captured_forward_transpose_absolute",
    "captured_forward_transpose_relative": "captured_forward_transpose_relative",
    "device_forward_transpose_absolute": "device_forward_transpose_absolute",
    "device_forward_transpose_relative": "device_forward_transpose_relative",
    "device_reducer_forward_absolute": "device_reducer_forward_absolute",
    "device_reducer_transpose_absolute": "device_reducer_transpose_absolute",
}


def _validate_population(
    event: Mapping[str, object], rows: Sequence[ReboundPhase]
) -> int:
    expected_fields = {
        "schema_version",
        "population",
        "scalar_pairs",
        "conditional_value",
        "maximum_errors",
        "reporting_digests",
        "telemetry",
        "gates",
        "all_gates_pass",
        "phase_host_ns",
        "campaign_host_ns",
        "population_elapsed_host_ns",
        "executed_work",
        "expected_work",
        "launch_counts",
    }
    if set(event) != expected_fields or event.get("schema_version") != (
        "legal-river-work-preflight-population-evidence-v1"
    ):
        raise ValueError("shared-direct reader population fields differ")
    population = _integer(event.get("population"), label="population", minimum=1)
    if population not in (10, 22) or any(row.population != population for row in rows):
        raise ValueError("shared-direct reader population identity differs")
    by_family = {family: [row for row in rows if row.family == family] for family in FAMILIES}
    for family_rows in by_family.values():
        _validate_phase_group(family_rows)
    expected_family_order = [
        family
        for family in FAMILIES
        for _row in by_family[family]
    ]
    if [row.family for row in rows] != expected_family_order:
        raise ValueError("shared-direct reader family phase order differs")
    if by_family[FAMILIES[0]][-1].host_stop_ns > (
        by_family[FAMILIES[1]][0].host_start_ns
    ):
        raise ValueError("shared-direct reader family phase intervals overlap")
    derived_work: dict[str, int] = {}
    phase_totals = {phase: 0 for phase in PHASE_ORDER}
    for row in rows:
        phase_totals[row.phase] += row.host_ns
        for name, count in row.work.items():
            derived_work[name] = derived_work.get(name, 0) + count
    expected_work = expected_shared_campaign_work(population)
    campaign_wall = sum(phase_totals.values())
    population_elapsed = _integer(
        event.get("population_elapsed_host_ns"),
        label="population elapsed host",
    )
    if (
        event.get("executed_work") != derived_work
        or event.get("expected_work") != expected_work
        or derived_work != expected_work
        or event.get("phase_host_ns") != phase_totals
        or event.get("campaign_host_ns") != campaign_wall
        or population_elapsed < campaign_wall
    ):
        raise ValueError("shared-direct reader population work differs")
    launches = event.get("launch_counts")
    if not isinstance(launches, list) or len(launches) != 2:
        raise ValueError("shared-direct reader population launch counts differ")
    launch_rows = [_mapping(row, label="population launches") for row in launches]
    for row in launch_rows:
        for value in row.values():
            _integer(value, label="population launch count")
    derived_runtime_gates = {
        "executed_work_ledger_exact": True,
        "phase_partition_exact": True,
        "all_fifteen_phases_observed": True,
        "population_reference_query_launches_zero": all(
            row.get("direct_selected_queries_tile", 0) == 0 for row in launch_rows
        ),
        "shared_fold_launch_count": sum(
            int(row.get("direct_selected_fold_tile", 0)) for row in launch_rows
        )
        == 12,
        "population_wall": population_elapsed <= POPULATION_WALL_NS,
    }
    errors = _mapping(event.get("maximum_errors"), label="population errors")
    expected_error_names = set(_ERROR_LIMITS)
    limits = dict(_ERROR_LIMITS)
    error_to_gate = dict(_ERROR_TO_GATE)
    if population == 10:
        complete = {
            "complete_fraction_source_absolute": Fraction.from_float(2e-12),
            "complete_fraction_source_relative": Fraction.from_float(2e-11),
            "complete_fraction_forward_absolute": Fraction.from_float(2e-10),
            "complete_fraction_forward_relative": Fraction.from_float(2e-11),
            "complete_fraction_fold_absolute": Fraction.from_float(2e-10),
            "complete_fraction_fold_relative": Fraction.from_float(2e-11),
            "complete_fraction_adjoint_absolute": Fraction.from_float(2e-10),
            "complete_fraction_adjoint_relative": Fraction.from_float(2e-11),
        }
        limits.update(complete)
        expected_error_names.update(complete)
        error_to_gate.update({name: name for name in complete})
    if set(errors) != expected_error_names:
        raise ValueError("shared-direct reader population error set differs")
    derived_numerical = {
        error_to_gate[name]: _fraction(value, label=f"population error {name}") <= limits[name]
        for name, value in errors.items()
    }
    conditional = _fraction(event.get("conditional_value"), label="conditional value")
    gates = _mapping(event.get("gates"), label="population gates")
    expected_derived = {
        **derived_numerical,
        **derived_runtime_gates,
        "chip_units": Fraction(-10) <= conditional <= Fraction(50),
    }
    if any(gates.get(name) is not value for name, value in expected_derived.items()):
        raise ValueError("shared-direct reader population derived gate differs")
    if any(not isinstance(value, bool) for value in gates.values()):
        raise ValueError("shared-direct reader population gate type differs")
    if event.get("all_gates_pass") is not all(gates.values()):
        raise ValueError("shared-direct reader population all-gates differs")
    digests = _mapping(event.get("reporting_digests"), label="population digests")
    if set(digests) != {
        "source_samples",
        "query_samples",
        "fold_samples",
        "adjoint_samples",
        "direct_samples",
        "contribution_streams",
    }:
        raise ValueError("shared-direct reader reporting digest set differs")
    for label, value in digests.items():
        _digest(value, label=f"population digest {label}")
    scalar_pairs = _mapping(event.get("scalar_pairs"), label="scalar pairs")
    for label, pair in scalar_pairs.items():
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or any(not isinstance(value, str) for value in pair)
        ):
            raise ValueError(f"shared-direct reader scalar pair differs: {label}")
        try:
            parsed = [float.fromhex(value) for value in pair]
        except ValueError as error:
            raise ValueError("shared-direct reader scalar hex differs") from error
        if any(not math.isfinite(value) for value in parsed):
            raise ValueError("shared-direct reader scalar is nonfinite")
    telemetry = _mapping(event.get("telemetry"), label="population telemetry")
    if set(telemetry) != {"maximum_pool_total_bytes", "maximum_host_numeric_bytes"}:
        raise ValueError("shared-direct reader telemetry fields differ")
    for value in telemetry.values():
        _integer(value, label="population telemetry")
    return population


def _validate_runtime(event: Mapping[str, object]) -> None:
    if set(event) != {"schema_version", "runtime", "built_cuda_source_sha256"} or (
        event.get("schema_version") != "legal-river-shared-direct-runtime-v1"
        or event.get("built_cuda_source_sha256") != BUILT_CUDA_SOURCE_SHA256
    ):
        raise ValueError("shared-direct reader runtime fields differ")
    runtime = _mapping(event.get("runtime"), label="runtime identity")
    if set(runtime) != {
        "device_name",
        "compute_capability",
        "device_total_bytes",
        "cuda_driver_version",
        "cuda_runtime_version",
        "cupy_version",
    }:
        raise ValueError("shared-direct reader runtime identity differs")
    _integer(runtime.get("device_total_bytes"), label="device bytes", minimum=1)


def _all_boolean_gates(event: Mapping[str, object], *, label: str) -> bool:
    gates = _mapping(event.get("gates"), label=f"{label} gates")
    if not gates or any(not isinstance(value, bool) for value in gates.values()):
        raise ValueError(f"shared-direct reader {label} gate types differ")
    return all(gates.values())


def _validate_primitive(event: Mapping[str, object]) -> bool:
    if set(event) != {
        "schema_version",
        "operation_count",
        "maximum_absolute_errors",
        "low_lane_nonzero_counts",
        "reporting_digest",
        "gates",
        "direct_order_controls",
    } or event.get("schema_version") != "legal-river-shared-direct-primitive-v1":
        raise ValueError("shared-direct reader primitive fields differ")
    _integer(event.get("operation_count"), label="primitive operations", minimum=1)
    _digest(event.get("reporting_digest"), label="primitive digest")
    for mapping_label in ("maximum_absolute_errors", "low_lane_nonzero_counts"):
        values = _mapping(event.get(mapping_label), label=f"primitive {mapping_label}")
        if not values:
            raise ValueError("shared-direct reader primitive evidence is empty")
    direct = _mapping(event.get("direct_order_controls"), label="direct-order controls")
    direct_gates = _mapping(direct.get("gates"), label="direct-order gates")
    if (
        not direct_gates
        or any(not isinstance(value, bool) for value in direct_gates.values())
        or direct.get("all_gates_pass") is not all(direct_gates.values())
    ):
        raise ValueError("shared-direct reader direct-order controls differ")
    return _all_boolean_gates(event, label="primitive") and all(direct_gates.values())


def _validate_reference_module(event: Mapping[str, object]) -> None:
    if set(event) != {
        "schema_version",
        "reference_repaired_cubin_sha256",
        "reference_repaired_cubin_bytes",
        "allowed_function_names",
    } or (
        event.get("schema_version") != "legal-river-shared-direct-reference-module-v1"
        or event.get("reference_repaired_cubin_sha256")
        != REFERENCE_REPAIRED_CUBIN_SHA256
        or event.get("reference_repaired_cubin_bytes") != 514_040
        or event.get("allowed_function_names")
        != ["direct_selected_queries_tile", "direct_selected_fold_tile"]
    ):
        raise ValueError("shared-direct reader reference module differs")


def _validate_complete_ten_control(event: Mapping[str, object]) -> bool:
    if set(event) != {
        "schema_version",
        "population",
        "reference_query_launches",
        "reference_fold_launches",
        "shared_primary_launches",
        "shared_repeat_launches",
        "reference_digests",
        "shared_digests",
        "gates",
        "all_gates_pass",
    } or (
        event.get("schema_version")
        != "legal-river-shared-direct-complete-ten-control-v1"
        or event.get("population") != 10
        or event.get("reference_query_launches") != 3
        or event.get("reference_fold_launches") != 3
        or event.get("shared_primary_launches") != 3
        or event.get("shared_repeat_launches") != 3
    ):
        raise ValueError("shared-direct reader complete-ten control differs")
    reference = event.get("reference_digests")
    shared = event.get("shared_digests")
    if (
        not isinstance(reference, list)
        or not isinstance(shared, list)
        or len(reference) != 3
        or reference != shared
    ):
        raise ValueError("shared-direct reader complete-ten digests differ")
    for digest in reference:
        _digest(digest, label="complete-ten digest")
    passed = _all_boolean_gates(event, label="complete-ten")
    if event.get("all_gates_pass") is not passed:
        raise ValueError("shared-direct reader complete-ten all-gates differs")
    return passed


def _validate_query_weight(event: Mapping[str, object]) -> bool:
    if set(event) != {
        "schema_version",
        "records",
        "maximum_absolute_error",
        "nonzero_low_count",
        "reporting_digest",
        "gates",
    } or event.get("schema_version") != "legal-river-shared-direct-query-weight-v1":
        raise ValueError("shared-direct reader query-weight fields differ")
    records = event.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("shared-direct reader query-weight records differ")
    _integer(event.get("nonzero_low_count"), label="query-weight low count")
    _digest(event.get("reporting_digest"), label="query-weight digest")
    error = event.get("maximum_absolute_error")
    if not isinstance(error, str):
        raise ValueError("shared-direct reader query-weight error differs")
    try:
        parsed = float.fromhex(error)
    except ValueError as exc:
        raise ValueError("shared-direct reader query-weight error hex differs") from exc
    if not math.isfinite(parsed):
        raise ValueError("shared-direct reader query-weight error is nonfinite")
    return _all_boolean_gates(event, label="query-weight")


def _validate_terminal_evidence(event: Mapping[str, object]) -> tuple[str, bool, str]:
    if set(event) != {
        "schema_version",
        "terminal",
        "passed",
        "reason",
        "failed_population",
        "capacity_projection",
        "complete_25_numerical_value",
    } or event.get("schema_version") != (
        "legal-river-shared-direct-terminal-evidence-v1"
    ):
        raise ValueError("shared-direct reader terminal evidence fields differ")
    terminal = event.get("terminal")
    reason = event.get("reason")
    passed = terminal == "completed_validation_pass"
    failed_population = event.get("failed_population")
    if (
        terminal not in ALLOWED_TERMINALS
        or terminal == "infrastructure_failure"
        or not isinstance(reason, str)
        or not reason
        or len(reason) > 4096
        or event.get("passed") is not passed
        or failed_population not in {None, 10, 22}
        or event.get("capacity_projection") is not None
        or event.get("complete_25_numerical_value") is not None
    ):
        raise ValueError("shared-direct reader terminal evidence differs")
    return str(terminal), passed, reason


def rebind_shared_direct_device_journal(
    raw: bytes,
    *,
    rebind_current_sources: bool = True,
) -> SharedDirectDeviceRebinding:
    """Reconstruct and independently re-evaluate one sealed device journal."""

    if not isinstance(raw, bytes) or not raw or len(raw) > MAXIMUM_ARTIFACT_BYTES:
        raise ValueError("shared-direct reader journal bytes differ")
    _load_config()
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if recovery.failure is not None or recovery.invalid_suffix_bytes:
        reason = recovery.failure.reason if recovery.failure is not None else "suffix"
        raise ValueError(f"shared-direct reader journal is incomplete: {reason}")
    records = recovery.records
    if (
        len(records) < 2
        or len(records) > MAXIMUM_EVENT_COUNT + 3
        or records[0].body.kind is not JournalRecordKind.HEADER
        or records[-1].body.kind is not JournalRecordKind.TERMINAL
        or any(
            record.body.kind is not JournalRecordKind.OBSERVATION
            for record in records[1:-1]
        )
    ):
        raise ValueError("shared-direct reader record structure differs")
    for record in records:
        if _semantic_digest(record.body.payload) != record.body.semantic_identity_sha256:
            raise ValueError("shared-direct reader semantic identity differs")

    header = records[0].body.payload
    if set(header) != {
        "schema_version",
        "config_sha256",
        "preregistration_commit",
        "source_seal_git",
        "dependency_hashes",
        "result_relative_path",
        "reserved_actual_result_relative_path",
        "claims",
    } or (
        header.get("schema_version") != "legal-river-shared-direct-owner-header-v1"
        or header.get("config_sha256") != CONFIG_SHA256
        or header.get("preregistration_commit") != PREREGISTRATION_COMMIT
        or header.get("result_relative_path") != RESULT_RELATIVE_PATH
        or header.get("reserved_actual_result_relative_path")
        != RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        or header.get("claims") != CLAIMS
    ):
        raise ValueError("shared-direct reader header contract differs")
    source_git = _mapping(header.get("source_seal_git"), label="source-seal git")
    source_commit = source_git.get("commit")
    if (
        set(source_git) != {"commit", "dirty", "strict_status"}
        or not isinstance(source_commit, str)
        or len(source_commit) != 40
        or any(character not in "0123456789abcdef" for character in source_commit)
        or source_git.get("dirty") is not False
        or source_git.get("strict_status") is not True
    ):
        raise ValueError("shared-direct reader source-seal git differs")
    dependencies = _mapping(header.get("dependency_hashes"), label="dependency hashes")
    if set(dependencies) != set(DEPENDENCY_RELATIVE_PATHS):
        raise ValueError("shared-direct reader dependency inventory differs")
    for relative, retained in dependencies.items():
        _digest(retained, label=f"dependency {relative}")
        if rebind_current_sources:
            path = _ROOT / relative
            current = sha256(
                path.read_bytes()
                if relative.startswith("artifacts/")
                else path.read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            if retained != current:
                raise ValueError(f"shared-direct reader dependency differs: {relative}")
    if rebind_current_sources and (_ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH).exists():
        raise ValueError("shared-direct reader reserved actual result exists")

    indexed_events: list[tuple[int, str, Mapping[str, object]]] = []
    allowed_kinds = {
        "bootstrap_handshake",
        "runtime",
        "compiler_payload_chunk",
        "compiler_payload_terminal",
        "container",
        "module",
        "resource_command_chunk",
        "resource_command_terminal",
        "resource_cleanup",
        "resource",
        "primitive",
        "reference_module",
        "complete_ten_control",
        "reference_release",
        "query_weight",
        "phase",
        "population",
        "terminal_evidence",
    }
    for index, record in enumerate(records[1:-1]):
        observation = record.body.payload
        if set(observation) != {"schema_version", "kind", "event", "config_sha256"} or (
            observation.get("schema_version")
            != "legal-river-shared-direct-owner-observation-v1"
            or observation.get("config_sha256") != CONFIG_SHA256
        ):
            raise ValueError("shared-direct reader observation envelope differs")
        kind = observation.get("kind")
        if kind not in allowed_kinds:
            raise ValueError("shared-direct reader observation kind differs")
        event = _mapping(observation.get("event"), label="observation event")
        indexed_events.append((index, str(kind), event))
    if not indexed_events or indexed_events[0][1] != "bootstrap_handshake":
        raise ValueError("shared-direct reader bootstrap is not first")
    handshake = indexed_events[0][2]
    if set(handshake) != {
        "schema_version",
        "challenge_sha256",
        "literal_module",
        "spec_name",
        "runtime_name",
        "cupy_imported",
    } or (
        handshake.get("schema_version") != "legal-river-shared-direct-handshake-v1"
        or handshake.get("literal_module") != LITERAL_WORKER_MODULE
        or handshake.get("spec_name") != LITERAL_WORKER_MODULE
        or handshake.get("runtime_name") != "__main__"
        or handshake.get("cupy_imported") is not False
    ):
        raise ValueError("shared-direct reader bootstrap differs")
    _digest(handshake.get("challenge_sha256"), label="bootstrap challenge")
    positions: dict[str, list[int]] = {}
    for position, kind, _event in indexed_events:
        positions.setdefault(kind, []).append(position)
    singleton_kinds = {
        "runtime",
        "compiler_payload_terminal",
        "container",
        "module",
        "resource_cleanup",
        "resource",
        "primitive",
        "reference_module",
        "complete_ten_control",
        "reference_release",
        "query_weight",
        "terminal_evidence",
    }
    if any(len(positions.get(kind, ())) > 1 for kind in singleton_kinds):
        raise ValueError("shared-direct reader singleton event repeats")

    compiler_chunks = [
        (position, event)
        for position, kind, event in indexed_events
        if kind == "compiler_payload_chunk"
    ]
    compiler_terminal_events = [
        (position, event)
        for position, kind, event in indexed_events
        if kind == "compiler_payload_terminal"
    ]
    compiler_payload: bytes | None = None
    container_mode: str | None = None
    loaded: bytes | None = None
    details: dict[str, object] | None = None
    if compiler_terminal_events:
        terminal_position, compiler_terminal = compiler_terminal_events[0]
        if set(compiler_terminal) != {
            "schema_version",
            "stream_id",
            "byte_count",
            "sha256",
            "built_cuda_source_sha256",
            "caller_supplied_nvrtc_options",
        } or (
            compiler_terminal.get("schema_version")
            != "legal-river-shared-direct-compiler-payload-v1"
            or compiler_terminal.get("stream_id") != "shared_nvrtc_payload"
            or compiler_terminal.get("built_cuda_source_sha256")
            != BUILT_CUDA_SOURCE_SHA256
            or compiler_terminal.get("caller_supplied_nvrtc_options")
            != [
                "--std=c++14",
                "--ftz=false",
                "--prec-div=true",
                "--prec-sqrt=true",
                "--fmad=false",
            ]
        ):
            raise ValueError("shared-direct reader compiler terminal differs")
        compiler_payload = _reconstruct_stream(
            compiler_chunks,
            stream_id="shared_nvrtc_payload",
            terminal_position=terminal_position,
        )
        if (
            not compiler_payload
            or compiler_terminal.get("byte_count") != len(compiler_payload)
            or compiler_terminal.get("sha256") != sha256(compiler_payload).hexdigest()
        ):
            raise ValueError("shared-direct reader compiler stream differs")
        container_mode, loaded, details = _classify_payload(compiler_payload)
    elif compiler_chunks:
        raise ValueError("shared-direct reader compiler chunks are orphaned")

    container_events = [event for _, kind, event in indexed_events if kind == "container"]
    if container_events:
        if (
            details is None
            or loaded is None
            or compiler_terminal_events[0][0] >= positions["container"][0]
        ):
            raise ValueError("shared-direct reader container placement differs")
        event = container_events[0]
        expected_container = {
            "schema_version": "legal-river-shared-direct-container-v1",
            "mode": container_mode,
            "raw_sha256": details["raw_sha256"],
            "raw_bytes": details["raw_bytes"],
            "loaded_sha256": details["loaded_sha256"],
            "loaded_bytes": details["loaded_bytes"],
            "appended_suffix_hex": (
                "00"
                if container_mode == "one_zero_final_program_alignment_completion"
                else ""
            ),
            "header": details["header"],
            "program_header_count": details["program_header_count"],
            "section_header_count": details["section_header_count"],
            "section_table_sha256": details["section_table_sha256"],
        }
        if event != expected_container:
            raise ValueError("shared-direct reader container derivation differs")
    module_events = [event for _, kind, event in indexed_events if kind == "module"]
    if module_events:
        if loaded is None or not container_events:
            raise ValueError("shared-direct reader module lacks container")
        expected_module = {
            "schema_version": "legal-river-shared-direct-module-v1",
            "loaded_sha256": sha256(loaded).hexdigest(),
            "loaded_bytes": len(loaded),
            "retained_object_is_loaded_object": True,
            "resolved_function_names": [
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
            ],
        }
        if module_events[0] != expected_module:
            raise ValueError("shared-direct reader loaded module differs")

    runtime_events = [event for _, kind, event in indexed_events if kind == "runtime"]
    if runtime_events:
        _validate_runtime(runtime_events[0])
    commands, command_positions = _reconstruct_commands(indexed_events)
    cleanup_events = [event for _, kind, event in indexed_events if kind == "resource_cleanup"]
    cleanup_without_resource_command = False
    if cleanup_events:
        cleanup = cleanup_events[0]
        if cleanup != {
            "schema_version": "legal-river-shared-direct-cleanup-v1",
            "temporary_created": True,
            "temporary_removed": True,
        }:
            raise ValueError("shared-direct reader cleanup differs")
        resource_command_position = command_positions.get(
            "cuobjdump_resource_usage"
        )
        if resource_command_position is None:
            cleanup_without_resource_command = True
        elif positions["resource_cleanup"][0] <= resource_command_position:
            raise ValueError("shared-direct reader cleanup placement differs")
    resource_events = [event for _, kind, event in indexed_events if kind == "resource"]
    resource_passed: bool | None = None
    if resource_events:
        if loaded is None or not cleanup_events:
            raise ValueError("shared-direct reader resource lacks loaded cleanup")
        _validate_resource(resource_events[0], commands, loaded=loaded)
        resource_passed = all(
            _mapping(resource_events[0].get("gates"), label="resource gates").values()
        )

    primitive_events = [event for _, kind, event in indexed_events if kind == "primitive"]
    primitive_passed = _validate_primitive(primitive_events[0]) if primitive_events else None
    reference_events = [event for _, kind, event in indexed_events if kind == "reference_module"]
    if reference_events:
        _validate_reference_module(reference_events[0])
    control_events = [event for _, kind, event in indexed_events if kind == "complete_ten_control"]
    control_passed = (
        _validate_complete_ten_control(control_events[0]) if control_events else None
    )
    release_events = [event for _, kind, event in indexed_events if kind == "reference_release"]
    if release_events and release_events[0] != {
        "schema_version": "legal-river-shared-direct-reference-release-v1",
        "reference_functions_unreachable": True,
    }:
        raise ValueError("shared-direct reader reference release differs")
    query_events = [event for _, kind, event in indexed_events if kind == "query_weight"]
    query_passed = _validate_query_weight(query_events[0]) if query_events else None

    phase_indexed = [
        (position, _parse_phase(event))
        for position, kind, event in indexed_events
        if kind == "phase"
    ]
    if any(row.population == 25 for _, row in phase_indexed):
        raise ValueError("shared-direct reader observed forbidden population 25")
    population_events = [
        (position, event)
        for position, kind, event in indexed_events
        if kind == "population"
    ]
    populations: list[int] = []
    consumed_phase_positions: set[int] = set()
    previous_population_position = -1
    for position, event in population_events:
        rows = [
            row
            for phase_position, row in phase_indexed
            if previous_population_position < phase_position < position
        ]
        population = _validate_population(event, rows)
        populations.append(population)
        consumed_phase_positions.update(
            phase_position
            for phase_position, _row in phase_indexed
            if previous_population_position < phase_position < position
        )
        previous_population_position = position
    if populations not in ([], [10], [10, 22]):
        raise ValueError("shared-direct reader population order differs")
    terminal_rows = [event for _, kind, event in indexed_events if kind == "terminal_evidence"]
    terminal_evidence: tuple[str, bool, str] | None = None
    if terminal_rows:
        if positions["terminal_evidence"][0] != indexed_events[-1][0]:
            raise ValueError("shared-direct reader terminal evidence is not last")
        terminal_evidence = _validate_terminal_evidence(terminal_rows[0])
    if len(consumed_phase_positions) != len(phase_indexed):
        allowed_tail = terminal_evidence is not None and terminal_evidence[0] in {
            "population_wall_rejection",
            "population_scientific_rejection",
            "laboratory_wall_rejection",
        }
        if not allowed_tail:
            raise ValueError("shared-direct reader phase rows are orphaned")

    outer = records[-1].body.payload
    if set(outer) != {
        "schema_version",
        "terminal",
        "passed",
        "reason",
        "event_count",
        "handshake_passed",
        "capacity_projection",
        "complete_25_numerical_value",
        "claims",
    } or outer.get("schema_version") != "legal-river-shared-direct-owner-terminal-v1":
        raise ValueError("shared-direct reader outer terminal fields differ")
    terminal = outer.get("terminal")
    passed = terminal == "completed_validation_pass"
    reason = outer.get("reason")
    expected_claims = dict(CLAIMS)
    expected_claims.update(
        {
            "device_differential_result": passed,
            "complete_10_result": passed,
            "complete_22_result": passed,
        }
    )
    if (
        terminal not in ALLOWED_TERMINALS
        or not isinstance(reason, str)
        or not reason
        or len(reason) > 4096
        or outer.get("passed") is not passed
        or outer.get("event_count") != len(indexed_events) - 1
        or outer.get("handshake_passed") is not True
        or outer.get("capacity_projection") is not None
        or outer.get("complete_25_numerical_value") is not None
        or outer.get("claims") != expected_claims
    ):
        raise ValueError("shared-direct reader outer terminal differs")
    if terminal_evidence is not None and terminal_evidence != (terminal, passed, reason):
        raise ValueError("shared-direct reader scientific and outer terminals disagree")
    if terminal not in {"infrastructure_failure", "laboratory_wall_rejection"} and (
        terminal_evidence is None
    ):
        raise ValueError("shared-direct reader scientific terminal is absent")
    if cleanup_without_resource_command and terminal not in {
        "resource_rejection",
        "infrastructure_failure",
    }:
        raise ValueError("shared-direct reader commandless cleanup terminal differs")

    if passed:
        required_singletons = {
            "runtime",
            "compiler_payload_terminal",
            "container",
            "module",
            "resource_cleanup",
            "resource",
            "primitive",
            "reference_module",
            "complete_ten_control",
            "reference_release",
            "query_weight",
            "terminal_evidence",
        }
        if (
            any(len(positions.get(kind, ())) != 1 for kind in required_singletons)
            or container_mode not in {
                "complete_elf_without_edit",
                "one_zero_final_program_alignment_completion",
            }
            or resource_passed is not True
            or primitive_passed is not True
            or control_passed is not True
            or query_passed is not True
            or populations != [10, 22]
            or len(consumed_phase_positions) != len(phase_indexed)
        ):
            raise ValueError("shared-direct reader completed-pass evidence is incomplete")
    elif terminal in {
        "compiler_container_rejection",
        "resource_rejection",
        "complete_ten_differential_rejection",
    } and (phase_indexed or population_events):
        raise ValueError("shared-direct reader early rejection contains population science")

    return SharedDirectDeviceRebinding(
        terminal=str(terminal),
        passed=passed,
        source_commit=source_commit,
        container_mode=container_mode,
        compiler_payload_sha256=(
            sha256(compiler_payload).hexdigest() if compiler_payload is not None else None
        ),
        shared_cubin_sha256=(sha256(loaded).hexdigest() if loaded is not None else None),
        complete_ten_control_passed=control_passed,
        populations=tuple(populations),
        phases=tuple(row for _, row in phase_indexed),
        event_count=len(indexed_events),
    )


def rebind_shared_direct_device_file(
    path: Path = _RESULT,
    *,
    rebind_current_sources: bool = True,
) -> SharedDirectDeviceRebinding:
    if not isinstance(path, Path):
        raise TypeError("shared-direct reader path must be a Path")
    return rebind_shared_direct_device_journal(
        path.read_bytes(), rebind_current_sources=rebind_current_sources
    )


__all__ = [
    "ALLOWED_TERMINALS",
    "CAMPAIGN_SHA256",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "PHASE_ORDER",
    "PROTOCOL_SHA256",
    "RESULT_RELATIVE_PATH",
    "RESERVED_ACTUAL_RESULT_RELATIVE_PATH",
    "ReboundPhase",
    "SharedDirectDeviceRebinding",
    "canonical_lf_sha256",
    "expected_shared_campaign_work",
    "rebind_shared_direct_device_file",
    "rebind_shared_direct_device_journal",
]
