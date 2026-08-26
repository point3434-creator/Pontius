"""Independent standard-library rebinder for the ADR-0413/ADR-0414 V4 journal."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import struct
from typing import Mapping, Sequence

from .durable_evidence_journal import (
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
    recover_journal_bytes,
    recover_journal_file,
)
from . import legal_river_quotient_cuda_compensated_work_preflight_result as _v1


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-owner-v4.json"
)
ENVELOPE_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-owner-v4-envelope-correction-v2.json"
)
V3_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v3.jsonl"
)
SUFFIX_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/legal_river_exact_cubin_zero_suffix_diagnostic_v1.jsonl"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v4.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
_CONFIG = _ROOT / CONFIG_RELATIVE_PATH
_ENVELOPE_CONFIG = _ROOT / ENVELOPE_CONFIG_RELATIVE_PATH
_V3_RESULT = _ROOT / V3_RESULT_RELATIVE_PATH
_SUFFIX_RESULT = _ROOT / SUFFIX_RESULT_RELATIVE_PATH
_RESULT = _ROOT / RESULT_RELATIVE_PATH

PREREGISTERED_CONFIG_SHA256 = (
    "80aad86a806275c4b8979025237b555332e97a84ec1090845ee12616701b4b43"
)
ENVELOPE_CONFIG_SHA256 = (
    "f4fdb2e89809f4c22422aed883b6d9f1bbb2e1aea6c32dfcf536f7a27d111ab7"
)
SCIENTIFIC_CONFIG_SHA256 = (
    "88a16d62cf978ec61b7481c79b841eda6a2844a41f374c122a21be5310550d3c"
)
RESOURCE_CONFIG_SHA256 = (
    "a522858696c8266485f7aac4b9c2dbb5f0d0c35e59d3e1515f4674d802ac890c"
)
V3_RESULT_SHA256 = "b84d9cd22042427c88f9c42b2da7acd176cdd0d5dec654c7f361bae7fa79cd0d"
V3_RESULT_BYTES = 15_783
V3_RESULT_RECORDS = 7
SUFFIX_RESULT_SHA256 = (
    "f4b3de941ed57e0f4acdfc7314315b6e70b10bd0034cf82113f17bf27e39a2de"
)
SUFFIX_RESULT_BYTES = 6_164_894
SUFFIX_RESULT_RECORDS = 15
PREREGISTRATION_COMMIT = "795e8a80599d0a16f3c723dac040dfe26700f834"

WORK_PREFLIGHT_V4_PROTOCOL_SHA256 = sha256(
    b"pontius-adr0413-work-preflight-repaired-executed-cubin-exclusive-journal-v4"
).hexdigest()
WORK_PREFLIGHT_V4_CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0413-work-preflight-repaired-executed-cubin-one-shot-campaign-v4"
).hexdigest()
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_cuda_compensated_work_preflight_v4_runner"
)
ORIGINAL_PAYLOAD_SHA256 = (
    "5dc4973302061b29dccd955ff7ee4dff3d61216316fb5d2fa71e9df22f42cd97"
)
ORIGINAL_PAYLOAD_BYTES = 514_039
REPAIRED_PAYLOAD_SHA256 = (
    "97693be7baafd882ad64a1a7da0ede23dc927efd872b0d15697b2486957ea894"
)
REPAIRED_PAYLOAD_BYTES = 514_040
MAXIMUM_ARTIFACT_BYTES = 67_108_864
MAXIMUM_EVENT_COUNT = 4096
MAXIMUM_STREAM_BYTES = 8_388_608
STREAM_CHUNK_RAW_BYTES = 196_608
MAXIMUM_CHUNKS_PER_STREAM = 43
MAXIMUM_COMBINED_VERSION_BYTES = 32_768
MAXIMUM_RESOURCE_STDOUT_BYTES = 262_144
PER_COMMAND_WALL_NS = 30_000_000_000
QUALIFIED_INSTRUMENT = "cuobjdump_resource_usage_on_exact_zero_suffix_payload"
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
CUDA_COMPILE_OPTIONS = (
    "--std=c++14",
    "--ftz=false",
    "--prec-div=true",
    "--prec-sqrt=true",
    "--fmad=false",
)
CLAIMS = {
    "v4_source_sealed": False,
    "adapter_probe_result": None,
    "repaired_executed_cubin_result": None,
    "resource_gate_result": None,
    "calibration_result": None,
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

_ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
_PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
_SECTION_HEADER = struct.Struct("<IIQQQQIIQQ")

_DEPENDENCY_PATHS = {
    "base_config": _CONFIG,
    "envelope_config": _ENVELOPE_CONFIG,
    "preregistration_adr": _ROOT
    / "docs/decisions/ADR-0413-preregister-the-repaired-executed-cubin-work-preflight-v4.md",
    "correction_adr": _ROOT
    / "docs/decisions/ADR-0414-correct-the-v4-bounded-evidence-envelope-before-source.md",
    "scientific_config": _ROOT
    / "experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-v1.json",
    "resource_config": _ROOT
    / "experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-v2.json",
    "scientific_source": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
    "suffix_source": _ROOT
    / "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic.py",
    "suffix_reader": _ROOT
    / "src/pontius/legal_river_exact_cubin_zero_suffix_diagnostic_result.py",
    "v3_reader": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v3_result.py",
    "v4_adapter": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_adapter.py",
    "v4_runner": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v4_runner.py",
    "v4_reader": Path(__file__),
    "v4_controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_work_preflight_v4.py",
    "journal": _ROOT / "src/pontius/durable_evidence_journal.py",
    "retained_v3": _V3_RESULT,
    "retained_suffix": _SUFFIX_RESULT,
    "artifact_marker": _ROOT / "artifacts/work_preflight/README.md",
    "artifact_attributes": _ROOT / "artifacts/work_preflight/.gitattributes",
}


@dataclass(frozen=True, slots=True)
class CommandEvidence:
    command_id: str
    status: str
    return_code: int | None
    stdout: bytes
    stderr: bytes
    elapsed_ns: int


@dataclass(frozen=True, slots=True)
class WorkPreflightV4Rebinding:
    terminal: str
    passed: bool
    event_count: int
    handshake: Mapping[str, object] | None
    adapter_probe: Mapping[str, object] | None
    repair: Mapping[str, object] | None
    commands: tuple[CommandEvidence, ...]
    cleanup: Mapping[str, object] | None
    phases: tuple[object, ...]
    projection: Mapping[str, object] | None
    journal_byte_count: int
    scientific_rebinding: _v1.WorkPreflightRebinding


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"work-preflight v4 reader path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


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
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def _load_json(path: Path, digest: str, schema: str) -> dict[str, object]:
    raw = path.read_bytes()
    if len(raw) > 1_048_576 or sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != digest:
        raise ValueError("work-preflight v4 reader config identity differs")
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema_version") != schema:
        raise ValueError("work-preflight v4 reader config schema differs")
    return value


def _load_composite_config() -> tuple[dict[str, object], dict[str, object]]:
    base = _load_json(
        _CONFIG,
        PREREGISTERED_CONFIG_SHA256,
        "legal-river-quotient-cuda-compensated-work-preflight-owner-config-v4",
    )
    correction = _load_json(
        _ENVELOPE_CONFIG,
        ENVELOPE_CONFIG_SHA256,
        "legal-river-quotient-cuda-compensated-work-preflight-owner-v4-envelope-correction-v2",
    )
    for parent in (
        _mapping(base.get("parent_identity"), label="V4 parent"),
        _mapping(correction.get("parent_identity"), label="V4 correction parent"),
    ):
        for key, relative in parent.items():
            if not key.endswith("_relative_path"):
                continue
            digest_key = key[: -len("_relative_path")] + "_canonical_lf_sha256"
            if digest_key in parent and (
                not isinstance(relative, str)
                or canonical_lf_sha256(_ROOT / relative) != parent[digest_key]
            ):
                raise ValueError("work-preflight v4 reader parent identity differs")
    identity = _mapping(base.get("new_identity_contract"), label="V4 identity")
    repair = _mapping(base.get("exact_repair_contract"), label="V4 repair")
    resource = _mapping(base.get("resource_semantics"), label="V4 resource")
    science = _mapping(base.get("inherited_science"), label="V4 science")
    bounded = _mapping(base.get("bounded_evidence_contract"), label="V4 bounds")
    scope = _mapping(base.get("successor_scope"), label="V4 scope")
    journal = _mapping(
        correction.get("corrected_journal_contract"), label="V4 journal"
    )
    parser = _mapping(
        correction.get("parser_admission_contract"), label="V4 parser"
    )
    if (
        identity.get("owner_protocol_sha256") != WORK_PREFLIGHT_V4_PROTOCOL_SHA256
        or identity.get("campaign_sha256") != WORK_PREFLIGHT_V4_CAMPAIGN_SHA256
        or repair.get("original_payload_sha256") != ORIGINAL_PAYLOAD_SHA256
        or repair.get("original_payload_bytes") != ORIGINAL_PAYLOAD_BYTES
        or repair.get("repaired_payload_sha256") != REPAIRED_PAYLOAD_SHA256
        or repair.get("repaired_payload_bytes") != REPAIRED_PAYLOAD_BYTES
        or repair.get("suffix_hex") != "00"
        or resource.get("register_limit_per_thread") != 255
        or resource.get("stack_plus_local_backing_limit_bytes_per_thread") != 4096
        or resource.get("exact_spill_load_store_count") is not None
        or science.get("calibration_populations") != [10, 22]
        or science.get("projection_population_integer_only") != 25
        or science.get("phase_name_count") != 16
        or bounded.get("per_external_stream_byte_limit") != MAXIMUM_STREAM_BYTES
        or journal.get("maximum_journal_bytes") != MAXIMUM_ARTIFACT_BYTES
        or journal.get("stream_chunk_raw_bytes") != STREAM_CHUNK_RAW_BYTES
        or journal.get("maximum_chunks_per_stream") != MAXIMUM_CHUNKS_PER_STREAM
        or parser.get("maximum_combined_version_output_bytes")
        != MAXIMUM_COMBINED_VERSION_BYTES
        or parser.get("maximum_resource_stdout_bytes")
        != MAXIMUM_RESOURCE_STDOUT_BYTES
        or scope.get("v4_result_relative_path") != RESULT_RELATIVE_PATH
        or scope.get("reserved_actual_result_relative_path")
        != RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        or base.get("claims") != CLAIMS
        or correction.get("claims") != CLAIMS
    ):
        raise ValueError("work-preflight v4 reader composite boundary differs")
    return base, correction


def _rebind_retained() -> tuple[dict[str, object], dict[str, object], bytes]:
    v3_raw = _V3_RESULT.read_bytes()
    suffix_raw = _SUFFIX_RESULT.read_bytes()
    if (
        len(v3_raw) != V3_RESULT_BYTES
        or len(v3_raw.splitlines()) != V3_RESULT_RECORDS
        or sha256(v3_raw).hexdigest() != V3_RESULT_SHA256
        or len(suffix_raw) != SUFFIX_RESULT_BYTES
        or len(suffix_raw.splitlines()) != SUFFIX_RESULT_RECORDS
        or sha256(suffix_raw).hexdigest() != SUFFIX_RESULT_SHA256
    ):
        raise ValueError("work-preflight v4 reader retained bytes differ")
    from .legal_river_exact_cubin_zero_suffix_diagnostic_result import (
        rebind_zero_suffix_diagnostic_journal,
    )
    from .legal_river_quotient_cuda_compensated_work_preflight_v3_result import (
        rebind_work_preflight_v3_journal,
    )

    v3 = rebind_work_preflight_v3_journal(v3_raw)
    suffix = rebind_zero_suffix_diagnostic_journal(suffix_raw)
    if (
        v3.terminal != "compiler_or_primitive_rejection"
        or v3.passed
        or v3.phases
        or v3.projection is not None
        or suffix.terminal != "suffix_reconstruction_pass"
        or not suffix.passed
        or suffix.repaired_payload is None
        or suffix.repaired_payload.sha256 != REPAIRED_PAYLOAD_SHA256
        or suffix.qualified_resource_instrument != QUALIFIED_INSTRUMENT
    ):
        raise ValueError("work-preflight v4 reader retained semantics differ")
    return (
        {
            "sha256": V3_RESULT_SHA256,
            "byte_count": V3_RESULT_BYTES,
            "record_count": V3_RESULT_RECORDS,
            "terminal": v3.terminal,
            "phase_count": len(v3.phases),
            "projection": v3.projection,
            "passed": v3.passed,
        },
        {
            "sha256": SUFFIX_RESULT_SHA256,
            "byte_count": SUFFIX_RESULT_BYTES,
            "record_count": SUFFIX_RESULT_RECORDS,
            "terminal": suffix.terminal,
            "qualified_resource_instrument": suffix.qualified_resource_instrument,
            "passed": suffix.passed,
        },
        suffix.repaired_payload.raw,
    )


def _validate_handshake(event: Mapping[str, object]) -> dict[str, object]:
    if set(event) != {"schema_version", "parent_challenge_sha256", "child"}:
        raise ValueError("work-preflight v4 accepted handshake fields differ")
    challenge = _digest(
        event.get("parent_challenge_sha256"), label="V4 handshake challenge"
    )
    child = _mapping(event.get("child"), label="V4 handshake child")
    if set(child) != {
        "schema_version",
        "challenge_sha256",
        "literal_worker_module",
        "spec_name",
        "runtime_name",
        "package_name",
        "python_no_bytecode",
        "argv_count",
        "cupy_loaded",
        "scientific_source_loaded",
    } or (
        event.get("schema_version")
        != "legal-river-work-preflight-bootstrap-accepted-v4"
        or child.get("schema_version")
        != "legal-river-work-preflight-bootstrap-handshake-v4"
        or child.get("challenge_sha256") != challenge
        or child.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or child.get("spec_name") != LITERAL_WORKER_MODULE
        or child.get("runtime_name") != "__main__"
        or child.get("package_name") != "pontius"
        or child.get("python_no_bytecode") is not True
        or child.get("argv_count") != 1
        or child.get("cupy_loaded") is not False
        or child.get("scientific_source_loaded") is not False
    ):
        raise ValueError("work-preflight v4 handshake semantics differ")
    return dict(event)


def _validate_adapter_probe(event: Mapping[str, object]) -> dict[str, object]:
    if set(event) != {"schema_version", "parent_challenge_sha256", "child"}:
        raise ValueError("work-preflight v4 accepted adapter-probe fields differ")
    challenge = _digest(
        event.get("parent_challenge_sha256"), label="V4 adapter-probe challenge"
    )
    child = _mapping(event.get("child"), label="V4 adapter-probe child")
    expected_child = {
        "schema_version",
        "challenge_sha256",
        "literal_worker_module",
        "spec_name",
        "runtime_name",
        "package_name",
        "python_no_bytecode",
        "argv_count",
        "cupy_loaded_before",
        "cupy_loaded_after",
        "scientific_source_loaded_before",
        "scientific_source_loaded_after",
        "probe",
    }
    if set(child) != expected_child or (
        event.get("schema_version")
        != "legal-river-work-preflight-adapter-probe-accepted-v4"
        or child.get("schema_version")
        != "legal-river-work-preflight-adapter-probe-child-v4"
        or child.get("challenge_sha256") != challenge
        or child.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or child.get("spec_name") != LITERAL_WORKER_MODULE
        or child.get("runtime_name") != "__main__"
        or child.get("package_name") != "pontius"
        or child.get("python_no_bytecode") is not True
        or child.get("argv_count") != 1
        or child.get("cupy_loaded_before") is not False
        or child.get("cupy_loaded_after") is not False
        or child.get("scientific_source_loaded_before") is not False
        or child.get("scientific_source_loaded_after") is not True
    ):
        raise ValueError("work-preflight v4 adapter-probe child differs")
    probe = _mapping(child.get("probe"), label="V4 adapter probe")
    expected_probe_keys = {
        "schema_version",
        "event_kinds",
        "effective_maxima",
        "resource_gates",
        "runtime",
        "original_payload_sha256",
        "repaired_payload_sha256",
        "cupy_loaded",
        "scientific_call_counter_unchanged",
        "identities_and_caches_restored",
        "passed",
    }
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
    expected_gates = {
        "register_ceiling": True,
        "local_and_stack_ceiling": True,
        "resident_thread_bound": True,
        "resident_backing_within_device_reserve": True,
    }
    expected_runtime = {
        "device_name": "adapter-probe-device",
        "compute_capability": "00",
        "device_total_bytes": 0,
        "cuda_driver_version": 0,
        "cuda_runtime_version": 0,
        "cupy_version": "adapter-probe-no-cupy",
    }
    if set(probe) != expected_probe_keys or (
        probe.get("schema_version")
        != "legal-river-work-preflight-adapter-probe-v4"
        or probe.get("event_kinds")
        != [
            "repaired_executed_cubin",
            "resource_command_stream",
            "resource_command_terminal",
            "resource_command_stream",
            "resource_command_terminal",
            "resource_temporary_cleanup",
        ]
        or probe.get("effective_maxima") != expected_maxima
        or probe.get("resource_gates") != expected_gates
        or probe.get("runtime") != expected_runtime
        or probe.get("original_payload_sha256") != ORIGINAL_PAYLOAD_SHA256
        or probe.get("repaired_payload_sha256") != REPAIRED_PAYLOAD_SHA256
        or probe.get("cupy_loaded") is not False
        or probe.get("scientific_call_counter_unchanged") is not True
        or probe.get("identities_and_caches_restored") is not True
        or probe.get("passed") is not True
    ):
        raise ValueError("work-preflight v4 adapter-probe semantics differ")
    return dict(event)


def _elf_header_mapping(header: tuple[object, ...]) -> dict[str, object]:
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
    return dict(zip(names, (header[0].hex(), *header[1:]), strict=True))  # type: ignore[union-attr]


def _validate_repair(event: Mapping[str, object], repaired_raw: bytes) -> dict[str, object]:
    expected = {
        "schema_version",
        "original_payload_sha256",
        "original_payload_bytes",
        "repaired_payload_sha256",
        "repaired_payload_bytes",
        "suffix_hex",
        "module_loaded_repaired_bytes",
        "retained_object_is_loaded_object",
        "resolved_function_names",
        "caller_supplied_nvrtc_options",
        "elf_header",
        "program_header_count",
        "section_table_sha256",
        "section_header_count",
        "qualified_resource_instrument",
    }
    if set(event) != expected or (
        event.get("schema_version")
        != "legal-river-work-preflight-repaired-executed-cubin-v4"
        or event.get("original_payload_sha256") != ORIGINAL_PAYLOAD_SHA256
        or event.get("original_payload_bytes") != ORIGINAL_PAYLOAD_BYTES
        or event.get("repaired_payload_sha256") != REPAIRED_PAYLOAD_SHA256
        or event.get("repaired_payload_bytes") != REPAIRED_PAYLOAD_BYTES
        or event.get("suffix_hex") != "00"
        or event.get("module_loaded_repaired_bytes") is not True
        or event.get("retained_object_is_loaded_object") is not True
        or tuple(event.get("resolved_function_names", ())) != ALL_KERNEL_NAMES
        or tuple(event.get("caller_supplied_nvrtc_options", ()))
        != CUDA_COMPILE_OPTIONS
        or event.get("qualified_resource_instrument") != QUALIFIED_INSTRUMENT
    ):
        raise ValueError("work-preflight v4 repair event differs")
    if (
        len(repaired_raw) != REPAIRED_PAYLOAD_BYTES
        or sha256(repaired_raw).hexdigest() != REPAIRED_PAYLOAD_SHA256
        or repaired_raw[-1:] != b"\0"
        or len(repaired_raw[:-1]) != ORIGINAL_PAYLOAD_BYTES
        or sha256(repaired_raw[:-1]).hexdigest() != ORIGINAL_PAYLOAD_SHA256
    ):
        raise ValueError("work-preflight v4 retained repaired bytes differ")
    header = _ELF_HEADER.unpack_from(repaired_raw, 0)
    e_phoff = int(header[5])
    e_shoff = int(header[6])
    e_ehsize = int(header[8])
    e_phentsize = int(header[9])
    e_phnum = int(header[10])
    e_shentsize = int(header[11])
    e_shnum = int(header[12])
    if (
        not header[0].startswith(b"\x7fELF\x02\x01")  # type: ignore[union-attr]
        or e_ehsize != _ELF_HEADER.size
        or e_phentsize != _PROGRAM_HEADER.size
        or e_shentsize != _SECTION_HEADER.size
        or e_phoff + e_phentsize * e_phnum != len(repaired_raw)
        or e_shoff + e_shentsize * e_shnum != e_phoff
    ):
        raise ValueError("work-preflight v4 repaired ELF geometry differs")
    section_bytes = repaired_raw[e_shoff:e_phoff]
    if (
        event.get("elf_header") != _elf_header_mapping(header)
        or event.get("program_header_count") != e_phnum
        or event.get("section_table_sha256") != sha256(section_bytes).hexdigest()
        or event.get("section_header_count") != e_shnum
    ):
        raise ValueError("work-preflight v4 repair structural evidence differs")
    return dict(event)


def _decode_chunk(event: Mapping[str, object]) -> tuple[str, str, int, int, bytes]:
    if set(event) != {
        "schema_version",
        "command_id",
        "stream",
        "chunk_index",
        "chunk_count",
        "chunk_raw_bytes",
        "total_raw_bytes",
        "total_sha256",
        "chunk_base64",
    } or event.get("schema_version") != (
        "legal-river-work-preflight-resource-command-stream-v4"
    ):
        raise ValueError("work-preflight v4 command chunk fields differ")
    command = event.get("command_id")
    stream = event.get("stream")
    index = _integer(event.get("chunk_index"), label="chunk index")
    count = _integer(event.get("chunk_count"), label="chunk count", minimum=1)
    chunk_bytes = _integer(
        event.get("chunk_raw_bytes"), label="chunk raw bytes", minimum=1
    )
    total = _integer(event.get("total_raw_bytes"), label="stream total")
    digest = _digest(event.get("total_sha256"), label="stream digest")
    encoded = event.get("chunk_base64")
    if (
        command not in {"cuobjdump_version", "cuobjdump_resource_usage"}
        or stream not in {"stdout", "stderr"}
        or count > MAXIMUM_CHUNKS_PER_STREAM
        or index >= count
        or chunk_bytes > STREAM_CHUNK_RAW_BYTES
        or total > MAXIMUM_STREAM_BYTES
        or not isinstance(encoded, str)
        or not encoded.isascii()
    ):
        raise ValueError("work-preflight v4 command chunk boundary differs")
    try:
        raw = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError("work-preflight v4 command chunk base64 differs") from error
    if (
        len(raw) != chunk_bytes
        or base64.b64encode(raw).decode("ascii") != encoded
        or (index < count - 1 and chunk_bytes != STREAM_CHUNK_RAW_BYTES)
    ):
        raise ValueError("work-preflight v4 command chunk bytes differ")
    return str(command), str(stream), index, count, raw


def _reconstruct_commands(
    indexed_events: Sequence[tuple[int, str, Mapping[str, object]]]
) -> tuple[tuple[CommandEvidence, ...], dict[str, int]]:
    chunks: dict[tuple[str, str], list[tuple[int, Mapping[str, object]]]] = {}
    terminals: list[tuple[int, Mapping[str, object]]] = []
    for position, kind, event in indexed_events:
        if kind == "resource_command_stream":
            command, stream, _index, _count, _raw = _decode_chunk(event)
            chunks.setdefault((command, stream), []).append((position, event))
        elif kind == "resource_command_terminal":
            terminals.append((position, event))
    if len(chunks) > 4 or len(terminals) > 2:
        raise ValueError("work-preflight v4 command cardinality differs")
    command_order = ("cuobjdump_version", "cuobjdump_resource_usage")
    results: list[CommandEvidence] = []
    positions: dict[str, int] = {}
    consumed_keys: set[tuple[str, str]] = set()
    previous_terminal = -1
    for ordinal, (terminal_position, terminal) in enumerate(terminals):
        expected_command = command_order[ordinal]
        expected_role = (
            "cuobjdump --version"
            if ordinal == 0
            else "cuobjdump --dump-resource-usage repaired-payload"
        )
        if set(terminal) != {
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
        } or (
            terminal.get("schema_version")
            != "legal-river-work-preflight-resource-command-terminal-v4"
            or terminal.get("command_id") != expected_command
            or terminal.get("argv_role") != expected_role
        ):
            raise ValueError("work-preflight v4 command terminal identity differs")
        status = terminal.get("status")
        return_code = terminal.get("return_code")
        elapsed = _integer(terminal.get("elapsed_ns"), label="command elapsed")
        if (
            status not in {"completed", "timeout", "output_limit"}
            or (
                return_code is not None
                and (isinstance(return_code, bool) or not isinstance(return_code, int))
            )
            or (status == "completed" and elapsed > PER_COMMAND_WALL_NS)
        ):
            raise ValueError("work-preflight v4 command outcome differs")
        raw_streams: dict[str, bytes] = {}
        ordered_chunks: list[tuple[int, int, int]] = []
        for stream_rank, stream in enumerate(("stdout", "stderr")):
            key = (expected_command, stream)
            rows = chunks.get(key, [])
            declared_bytes = _integer(
                terminal.get(f"{stream}_bytes"), label=f"{stream} bytes"
            )
            declared_digest = _digest(
                terminal.get(f"{stream}_sha256"), label=f"{stream} digest"
            )
            if not rows:
                raw = b""
            else:
                decoded = [_decode_chunk(row) for _, row in rows]
                counts = {row[3] for row in decoded}
                totals = {
                    _integer(row.get("total_raw_bytes"), label="chunk total")
                    for _, row in rows
                }
                digests = {
                    _digest(row.get("total_sha256"), label="chunk total digest")
                    for _, row in rows
                }
                if (
                    len(counts) != 1
                    or len(totals) != 1
                    or len(digests) != 1
                    or [row[2] for row in decoded] != list(range(decoded[0][3]))
                    or len(decoded) != decoded[0][3]
                ):
                    raise ValueError("work-preflight v4 command chunk sequence differs")
                raw = b"".join(row[4] for row in decoded)
                if totals != {len(raw)} or digests != {sha256(raw).hexdigest()}:
                    raise ValueError("work-preflight v4 command chunk envelope differs")
                consumed_keys.add(key)
                ordered_chunks.extend(
                    (position, stream_rank, row[2])
                    for (position, _event), row in zip(rows, decoded, strict=True)
                )
            if len(raw) != declared_bytes or sha256(raw).hexdigest() != declared_digest:
                raise ValueError("work-preflight v4 command terminal stream differs")
            raw_streams[stream] = raw
        chunk_positions = [row[0] for row in ordered_chunks]
        if any(
            not previous_terminal < position < terminal_position
            for position, _stream_rank, _chunk_index in ordered_chunks
        ) or chunk_positions != sorted(chunk_positions):
            raise ValueError("work-preflight v4 command chunk placement differs")
        previous_terminal = terminal_position
        positions[expected_command] = terminal_position
        results.append(
            CommandEvidence(
                command_id=expected_command,
                status=str(status),
                return_code=return_code,
                stdout=raw_streams["stdout"],
                stderr=raw_streams["stderr"],
                elapsed_ns=elapsed,
            )
        )
    if set(chunks) != consumed_keys:
        raise ValueError("work-preflight v4 command stream is orphaned")
    return tuple(results), positions


def _accepted_ascii(raw: bytes, *, maximum: int, label: str) -> str:
    if len(raw) > maximum or any(
        byte not in {9, 10, 13} and not 0x20 <= byte <= 0x7E for byte in raw
    ):
        raise ValueError(f"work-preflight v4 {label} parser admission differs")
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
                raise ValueError("work-preflight v4 resource function repeats")
            result[current] = {}
            continue
        if current is None or not line:
            continue
        for label, raw_value in re.findall(r"([A-Z]+(?:\[\d+\])?):(\d+)", line):
            if label in result[current]:
                raise ValueError("work-preflight v4 resource field repeats")
            result[current][label] = int(raw_value)
    if not set(DIRECT_KERNEL_NAMES).issubset(result):
        raise ValueError("work-preflight v4 direct resource rows are absent")
    direct = {name: result[name] for name in DIRECT_KERNEL_NAMES}
    if any(not {"REG", "STACK", "LOCAL"}.issubset(row) for row in direct.values()):
        raise ValueError("work-preflight v4 direct resource row is incomplete")
    return direct


def _validate_runtime_resource(
    event: Mapping[str, object],
    repair: Mapping[str, object],
    by_command: Mapping[str, CommandEvidence],
) -> None:
    if set(by_command) != {"cuobjdump_version", "cuobjdump_resource_usage"}:
        raise ValueError("work-preflight v4 qualifying commands are incomplete")
    version = by_command["cuobjdump_version"]
    resource_command = by_command["cuobjdump_resource_usage"]
    if any(
        command.status != "completed" or command.return_code != 0
        for command in (version, resource_command)
    ):
        raise ValueError("work-preflight v4 runtime evidence follows a failed command")
    combined = b"\n".join(
        value.strip() for value in (version.stdout, version.stderr) if value.strip()
    )
    version_text = _accepted_ascii(
        combined, maximum=MAXIMUM_COMBINED_VERSION_BYTES, label="version"
    )
    resource_text = _accepted_ascii(
        resource_command.stdout,
        maximum=MAXIMUM_RESOURCE_STDOUT_BYTES,
        label="resource",
    )
    if re.search(r"(?<!\d)13\.3(?!\d)", version_text) is None:
        raise ValueError("work-preflight v4 resource tool version differs")
    cubin = _mapping(event.get("cubin_resource_usage"), label="V4 cubin resources")
    expected_cubin = {
        "tool_path",
        "tool_version_output",
        "raw_resource_stdout",
        "cubin_sha256",
        "retained_payload_format",
        "caller_supplied_nvrtc_options",
        "cupy_version",
        "cupy_internal_options_disclosure",
        "direct",
        "driver_direct",
        "effective_maxima",
        "runtime_residency",
        "gates",
        "claims",
    }
    if set(cubin) != expected_cubin or (
        cubin.get("tool_version_output") != version_text
        or cubin.get("raw_resource_stdout") != resource_text
        or cubin.get("cubin_sha256") != repair.get("repaired_payload_sha256")
        or cubin.get("retained_payload_format") != "elf-cubin"
        or tuple(cubin.get("caller_supplied_nvrtc_options", ()))
        != CUDA_COMPILE_OPTIONS
        or cubin.get("cupy_internal_options_disclosure")
        != [
            "target_architecture",
            "device_as_default_execution_space",
            "version_dependent_precompiled_header",
        ]
        or not isinstance(cubin.get("tool_path"), str)
        or not cubin.get("tool_path")
    ):
        raise ValueError("work-preflight v4 command/scientific resource seam differs")
    parsed = _parse_resources(resource_text)
    if cubin.get("direct") != parsed:
        raise ValueError("work-preflight v4 resource text reparse differs")
    driver = _mapping(event.get("direct_kernel_resources"), label="V4 driver rows")
    if set(driver) != set(DIRECT_KERNEL_NAMES) or cubin.get("driver_direct") != driver:
        raise ValueError("work-preflight v4 driver resource rows differ")
    maxima: dict[str, dict[str, int]] = {}
    for name in DIRECT_KERNEL_NAMES:
        row = _mapping(driver[name], label="V4 driver row")
        if set(row) != {
            "local_size_bytes",
            "registers",
            "shared_size_bytes",
            "maximum_threads_per_block",
        }:
            raise ValueError("work-preflight v4 driver row fields differ")
        checked = {
            key: _integer(value, label=f"V4 driver {key}")
            for key, value in row.items()
        }
        maxima[name] = {
            "registers": max(checked["registers"], parsed[name]["REG"]),
            "stack_plus_local_backing_bytes": max(
                checked["local_size_bytes"],
                parsed[name]["STACK"] + parsed[name]["LOCAL"],
            ),
        }
    if cubin.get("effective_maxima") != maxima:
        raise ValueError("work-preflight v4 two-instrument maxima differ")
    residency = _mapping(cubin.get("runtime_residency"), label="V4 residency")
    if set(residency) != {
        "multiprocessor_count",
        "maximum_threads_per_multiprocessor",
        "maximum_resident_threads",
        "backing_ceiling_bytes_per_thread",
        "maximum_resident_backing_bytes",
        "frozen_device_reserve_bytes",
    }:
        raise ValueError("work-preflight v4 residency fields differ")
    multiprocessors = _integer(
        residency.get("multiprocessor_count"), label="V4 multiprocessors", minimum=1
    )
    per = _integer(
        residency.get("maximum_threads_per_multiprocessor"),
        label="V4 threads per multiprocessor",
        minimum=1,
    )
    resident_threads = multiprocessors * per
    resident_backing = resident_threads * 4096
    if (
        residency.get("maximum_resident_threads") != resident_threads
        or residency.get("backing_ceiling_bytes_per_thread") != 4096
        or residency.get("maximum_resident_backing_bytes") != resident_backing
        or residency.get("frozen_device_reserve_bytes") != 2_000_000_000
    ):
        raise ValueError("work-preflight v4 residency arithmetic differs")
    gates = {
        "register_ceiling": all(row["registers"] <= 255 for row in maxima.values()),
        "local_and_stack_ceiling": all(
            row["stack_plus_local_backing_bytes"] <= 4096 for row in maxima.values()
        ),
        "resident_thread_bound": resident_threads <= 131_072,
        "resident_backing_within_device_reserve": (
            resident_threads <= 131_072 and resident_backing <= 2_000_000_000
        ),
    }
    runtime = _mapping(event.get("runtime"), label="V4 runtime")
    if (
        cubin.get("gates") != gates
        or cubin.get("cupy_version") != runtime.get("cupy_version")
        or cubin.get("claims")
        != {
            "exact_spill_load_store_count": None,
            "local_and_stack_are_not_relabeled_as_spill_counts": True,
        }
    ):
        raise ValueError("work-preflight v4 resource gate reconstruction differs")


def _compatibility_line(
    *, kind: JournalRecordKind, sequence: int, previous: str | None, payload: Mapping[str, object]
) -> JournalRecordEnvelope:
    return JournalRecordEnvelope(
        body=build_journal_record_body(
            protocol_sha256=_v1.WORK_PREFLIGHT_PROTOCOL_SHA256,
            campaign_sha256=_v1.WORK_PREFLIGHT_CAMPAIGN_SHA256,
            kind=kind,
            sequence=sequence,
            previous_record_sha256=previous,
            semantic_identity_sha256=_semantic_digest(payload),
            payload=payload,
        )
    )


def _build_v1_view(
    observations: Sequence[Mapping[str, object]], terminal: Mapping[str, object]
) -> bytes:
    source_commit = next(
        (
            str(row.get("source_commit"))
            for row in observations
            if row.get("event_kind") == "provenance"
        ),
        "0" * 40,
    )
    excluded = {
        "bootstrap_handshake",
        "adapter_probe",
        "repaired_executed_cubin",
        "resource_command_stream",
        "resource_command_terminal",
        "resource_temporary_cleanup",
    }
    compatibility: list[dict[str, object]] = []
    for observation in observations:
        kind = observation.get("event_kind")
        if kind in excluded:
            continue
        event = dict(_mapping(observation.get("event"), label="V4 compatibility event"))
        if kind == "provenance":
            event = {
                "schema_version": "legal-river-work-preflight-provenance-v1",
                "config_sha256": _v1.PREREGISTERED_CONFIG_SHA256,
                "correction_config_sha256": _v1.CORRECTION_CONFIG_SHA256,
                "source_commit": source_commit,
                "source_dirty": False,
                "dependency_hashes": {
                    label: canonical_lf_sha256(path)
                    for label, path in _v1._DEPENDENCY_PATHS.items()  # type: ignore[attr-defined]
                },
                "reserved_actual_result_absent": True,
            }
        compatibility.append(
            {
                "schema_version": "legal-river-work-preflight-owner-observation-v1",
                "event_index": len(compatibility),
                "event_kind": kind,
                "config_sha256": _v1.PREREGISTERED_CONFIG_SHA256,
                "correction_config_sha256": _v1.CORRECTION_CONFIG_SHA256,
                "source_commit": source_commit,
                "event": event,
            }
        )
    header = {
        "schema_version": "legal-river-work-preflight-owner-header-v1",
        "owner_protocol_sha256": _v1.WORK_PREFLIGHT_PROTOCOL_SHA256,
        "config_relative_path": _v1.CONFIG_RELATIVE_PATH,
        "correction_config_relative_path": _v1.CORRECTION_CONFIG_RELATIVE_PATH,
        "correction_config_sha256": _v1.CORRECTION_CONFIG_SHA256,
        "result_relative_path": _v1.RESULT_RELATIVE_PATH,
        "reserved_actual_result_relative_path": _v1.RESERVED_ACTUAL_RESULT_RELATIVE_PATH,
        "calibration_populations": [10, 22],
        "projection_population_integer_only": 25,
        "preregistration_commit": _v1.PREREGISTRATION_COMMIT,
        "claims": dict(_v1.CLAIMS),
    }
    payloads: list[tuple[JournalRecordKind, Mapping[str, object]]] = [
        (JournalRecordKind.HEADER, header),
        *((JournalRecordKind.OBSERVATION, row) for row in compatibility),
    ]
    last_event_identity = (
        _semantic_digest(compatibility[-1]) if compatibility else None
    )
    payloads.append(
        (
            JournalRecordKind.TERMINAL,
            {
                "schema_version": "legal-river-work-preflight-owner-terminal-v1",
                "terminal": terminal.get("terminal"),
                "reason": str(terminal.get("reason", "V4 compatibility validation"))[:4096],
                "passed": terminal.get("passed"),
                "event_count": len(compatibility),
                "last_event_semantic_identity_sha256": last_event_identity,
                "claims": dict(_v1.CLAIMS),
            },
        )
    )
    lines: list[bytes] = []
    previous: str | None = None
    for sequence, (kind, payload) in enumerate(payloads):
        envelope = _compatibility_line(
            kind=kind, sequence=sequence, previous=previous, payload=payload
        )
        lines.append(envelope.line_bytes)
        previous = envelope.line_sha256
    return b"".join(lines)


def rebind_work_preflight_v4_journal(
    raw: bytes, *, rebind_current_sources: bool = True
) -> WorkPreflightV4Rebinding:
    if not isinstance(raw, bytes) or len(raw) > MAXIMUM_ARTIFACT_BYTES:
        raise ValueError("work-preflight v4 journal bytes differ")
    _load_composite_config()
    retained_v3, retained_suffix, repaired_raw = _rebind_retained()
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=WORK_PREFLIGHT_V4_PROTOCOL_SHA256,
        expected_campaign_sha256=WORK_PREFLIGHT_V4_CAMPAIGN_SHA256,
    )
    if recovery.failure is not None or recovery.invalid_suffix_bytes:
        reason = recovery.failure.reason if recovery.failure is not None else "suffix"
        raise ValueError(f"work-preflight v4 journal is incomplete: {reason}")
    records = recovery.records
    if (
        len(records) < 2
        or len(records) > MAXIMUM_EVENT_COUNT + 2
        or records[0].body.kind is not JournalRecordKind.HEADER
        or records[-1].body.kind is not JournalRecordKind.TERMINAL
        or any(row.body.kind is not JournalRecordKind.OBSERVATION for row in records[1:-1])
    ):
        raise ValueError("work-preflight v4 journal record structure differs")
    for record in records:
        if _semantic_digest(record.body.payload) != record.body.semantic_identity_sha256:
            raise ValueError("work-preflight v4 semantic identity differs")
    header = records[0].body.payload
    if set(header) != {
        "schema_version",
        "owner_protocol_sha256",
        "campaign_sha256",
        "config_relative_path",
        "config_sha256",
        "envelope_config_relative_path",
        "envelope_config_sha256",
        "result_relative_path",
        "retained_v3_result_relative_path",
        "retained_v3_result_sha256",
        "retained_suffix_result_relative_path",
        "retained_suffix_result_sha256",
        "reserved_actual_result_relative_path",
        "preregistration_commit",
        "literal_worker_module",
        "calibration_populations",
        "projection_population_integer_only",
        "claims",
    } or (
        header.get("schema_version") != "legal-river-work-preflight-owner-header-v4"
        or header.get("owner_protocol_sha256") != WORK_PREFLIGHT_V4_PROTOCOL_SHA256
        or header.get("campaign_sha256") != WORK_PREFLIGHT_V4_CAMPAIGN_SHA256
        or header.get("config_relative_path") != CONFIG_RELATIVE_PATH
        or header.get("config_sha256") != PREREGISTERED_CONFIG_SHA256
        or header.get("envelope_config_relative_path") != ENVELOPE_CONFIG_RELATIVE_PATH
        or header.get("envelope_config_sha256") != ENVELOPE_CONFIG_SHA256
        or header.get("result_relative_path") != RESULT_RELATIVE_PATH
        or header.get("retained_v3_result_relative_path") != V3_RESULT_RELATIVE_PATH
        or header.get("retained_v3_result_sha256") != V3_RESULT_SHA256
        or header.get("retained_suffix_result_relative_path") != SUFFIX_RESULT_RELATIVE_PATH
        or header.get("retained_suffix_result_sha256") != SUFFIX_RESULT_SHA256
        or header.get("reserved_actual_result_relative_path")
        != RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        or header.get("preregistration_commit") != PREREGISTRATION_COMMIT
        or header.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or header.get("calibration_populations") != [10, 22]
        or header.get("projection_population_integer_only") != 25
        or header.get("claims") != CLAIMS
    ):
        raise ValueError("work-preflight v4 header contract differs")

    observations: list[Mapping[str, object]] = []
    indexed_events: list[tuple[int, str, Mapping[str, object]]] = []
    source_commit: str | None = None
    provenance: Mapping[str, object] | None = None
    handshake: Mapping[str, object] | None = None
    adapter_probe: Mapping[str, object] | None = None
    repair: Mapping[str, object] | None = None
    cleanup: Mapping[str, object] | None = None
    terminal_evidence: Mapping[str, object] | None = None
    allowed_kinds = {
        "provenance",
        "bootstrap_handshake",
        "adapter_probe",
        "repaired_executed_cubin",
        "resource_command_stream",
        "resource_command_terminal",
        "resource_temporary_cleanup",
        "laboratory",
        "phase",
        "population",
        "projection",
        "terminal_evidence",
    }
    for index, record in enumerate(records[1:-1]):
        observation = record.body.payload
        if set(observation) != {
            "schema_version",
            "event_index",
            "event_kind",
            "config_sha256",
            "envelope_config_sha256",
            "scientific_config_sha256",
            "resource_config_sha256",
            "source_commit",
            "event",
        } or (
            observation.get("schema_version")
            != "legal-river-work-preflight-owner-observation-v4"
            or observation.get("event_index") != index
            or observation.get("config_sha256") != PREREGISTERED_CONFIG_SHA256
            or observation.get("envelope_config_sha256") != ENVELOPE_CONFIG_SHA256
            or observation.get("scientific_config_sha256") != SCIENTIFIC_CONFIG_SHA256
            or observation.get("resource_config_sha256") != RESOURCE_CONFIG_SHA256
        ):
            raise ValueError("work-preflight v4 observation envelope differs")
        commit = observation.get("source_commit")
        if (
            not isinstance(commit, str)
            or len(commit) != 40
            or any(character not in "0123456789abcdef" for character in commit)
            or (source_commit is not None and commit != source_commit)
        ):
            raise ValueError("work-preflight v4 source commit differs")
        source_commit = commit
        kind = observation.get("event_kind")
        if kind not in allowed_kinds:
            raise ValueError("work-preflight v4 event kind differs")
        event = _mapping(observation.get("event"), label="V4 event")
        observations.append(observation)
        indexed_events.append((index, str(kind), event))
        if kind == "provenance":
            if index != 0 or provenance is not None:
                raise ValueError("work-preflight v4 provenance placement differs")
            provenance = event
        elif kind == "bootstrap_handshake":
            if handshake is not None:
                raise ValueError("work-preflight v4 handshake repeats")
            handshake = _validate_handshake(event)
        elif kind == "adapter_probe":
            if adapter_probe is not None:
                raise ValueError("work-preflight v4 adapter probe repeats")
            adapter_probe = _validate_adapter_probe(event)
        elif kind == "repaired_executed_cubin":
            if repair is not None:
                raise ValueError("work-preflight v4 repair repeats")
            repair = _validate_repair(event, repaired_raw)
        elif kind == "resource_temporary_cleanup":
            if cleanup is not None or set(event) != {
                "schema_version",
                "temporary_created",
                "temporary_removed",
                "repaired_payload_sha256",
            } or (
                event.get("schema_version")
                != "legal-river-work-preflight-resource-cleanup-v4"
                or event.get("temporary_created") is not True
                or event.get("temporary_removed") is not True
                or event.get("repaired_payload_sha256") != REPAIRED_PAYLOAD_SHA256
            ):
                raise ValueError("work-preflight v4 cleanup evidence differs")
            cleanup = dict(event)
        elif kind == "terminal_evidence":
            if terminal_evidence is not None or index != len(records[1:-1]) - 1:
                raise ValueError("work-preflight v4 terminal evidence placement differs")
            terminal_evidence = event
    if observations and provenance is None:
        raise ValueError("work-preflight v4 provenance is absent")
    if provenance is not None:
        if set(provenance) != {
            "schema_version",
            "config_sha256",
            "envelope_config_sha256",
            "scientific_config_sha256",
            "resource_config_sha256",
            "source_commit",
            "source_dirty",
            "dependency_hashes",
            "retained_v3",
            "retained_suffix",
            "literal_worker_module",
            "adapter_boundary",
            "reserved_actual_result_absent",
        } or (
            provenance.get("schema_version")
            != "legal-river-work-preflight-provenance-v4"
            or provenance.get("config_sha256") != PREREGISTERED_CONFIG_SHA256
            or provenance.get("envelope_config_sha256") != ENVELOPE_CONFIG_SHA256
            or provenance.get("scientific_config_sha256") != SCIENTIFIC_CONFIG_SHA256
            or provenance.get("resource_config_sha256") != RESOURCE_CONFIG_SHA256
            or provenance.get("source_commit") != source_commit
            or provenance.get("source_dirty") is not False
            or provenance.get("retained_v3") != retained_v3
            or provenance.get("retained_suffix") != retained_suffix
            or provenance.get("literal_worker_module") != LITERAL_WORKER_MODULE
            or provenance.get("adapter_boundary")
            != "exact_serializer_repair_before_load_same_inspected_bytes"
            or provenance.get("reserved_actual_result_absent") is not True
        ):
            raise ValueError("work-preflight v4 provenance contract differs")
        hashes = _mapping(provenance.get("dependency_hashes"), label="V4 hashes")
        if set(hashes) != set(_DEPENDENCY_PATHS):
            raise ValueError("work-preflight v4 dependency inventory differs")
        if rebind_current_sources:
            for label, path in _DEPENDENCY_PATHS.items():
                expected = sha256(
                    path.read_bytes()
                    if label.startswith("retained_")
                    else path.read_bytes().replace(b"\r\n", b"\n")
                ).hexdigest()
                if hashes.get(label) != expected:
                    raise ValueError(f"work-preflight v4 dependency differs: {label}")

    commands, command_positions = _reconstruct_commands(indexed_events)
    positions_by_kind: dict[str, list[int]] = {}
    for position, kind, _event in indexed_events:
        positions_by_kind.setdefault(kind, []).append(position)
    handshake_position = positions_by_kind.get("bootstrap_handshake", [None])[0]
    probe_position = positions_by_kind.get("adapter_probe", [None])[0]
    repair_position = positions_by_kind.get("repaired_executed_cubin", [None])[0]
    cleanup_position = positions_by_kind.get("resource_temporary_cleanup", [None])[0]
    if handshake is not None and handshake_position != 1:
        raise ValueError("work-preflight v4 handshake is not first after provenance")
    if adapter_probe is not None and (
        handshake is None or probe_position != 2
    ):
        raise ValueError("work-preflight v4 adapter probe placement differs")
    if repair is not None and (
        adapter_probe is None or not isinstance(repair_position, int) or repair_position <= 2
    ):
        raise ValueError("work-preflight v4 repair placement differs")
    if commands and repair is None:
        raise ValueError("work-preflight v4 command precedes repair evidence")
    if repair_position is not None and any(
        position <= repair_position for position in command_positions.values()
    ):
        raise ValueError("work-preflight v4 command precedes repair")
    if cleanup is not None and (
        "cuobjdump_resource_usage" not in command_positions
        or not isinstance(cleanup_position, int)
        or cleanup_position <= command_positions["cuobjdump_resource_usage"]
    ):
        raise ValueError("work-preflight v4 cleanup placement differs")
    if "cuobjdump_resource_usage" in command_positions and cleanup is None:
        raise ValueError("work-preflight v4 resource command lacks durable cleanup")
    if len(commands) == 2:
        version = commands[0]
        combined = b"\n".join(
            value.strip()
            for value in (version.stdout, version.stderr)
            if value.strip()
        )
        if (
            version.status != "completed"
            or version.return_code != 0
            or re.search(
                r"(?<!\d)13\.3(?!\d)",
                _accepted_ascii(
                    combined,
                    maximum=MAXIMUM_COMBINED_VERSION_BYTES,
                    label="version",
                ),
            )
            is None
        ):
            raise ValueError(
                "work-preflight v4 resource command follows an unqualified version"
            )

    runtime_positions: list[int] = []
    for position, kind, event in indexed_events:
        if kind == "laboratory" and event.get("kind") == "runtime_primitives_and_compiler":
            runtime_positions.append(position)
            if repair is None or cleanup is None:
                raise ValueError("work-preflight v4 runtime evidence lacks repair/cleanup")
            _validate_runtime_resource(
                event, repair, {command.command_id: command for command in commands}
            )
    if len(runtime_positions) > 1:
        raise ValueError("work-preflight v4 runtime resource event repeats")
    if runtime_positions and (
        not isinstance(cleanup_position, int) or runtime_positions[0] <= cleanup_position
    ):
        raise ValueError("work-preflight v4 runtime event precedes cleanup")
    scientific_positions = [
        position
        for position, kind, _event in indexed_events
        if kind in {"phase", "population", "projection"}
    ]
    if scientific_positions and (
        not runtime_positions or min(scientific_positions) <= runtime_positions[0]
    ):
        raise ValueError("work-preflight v4 calibration precedes runtime authority")

    outer = records[-1].body.payload
    if set(outer) != {
        "schema_version",
        "terminal",
        "reason",
        "passed",
        "event_count",
        "last_event_semantic_identity_sha256",
        "handshake_passed",
        "adapter_probe_passed",
        "claims",
    } or outer.get("schema_version") != "legal-river-work-preflight-owner-terminal-v4":
        raise ValueError("work-preflight v4 terminal fields differ")
    terminal = outer.get("terminal")
    allowed_terminals = {
        "completed_capacity_pass",
        "completed_capacity_rejection",
        "calibration_scientific_rejection",
        "compiler_or_primitive_rejection",
        "laboratory_wall_rejection",
        "infrastructure_failure",
    }
    passed = terminal == "completed_capacity_pass"
    expected_last = records[-2].body.semantic_identity_sha256 if observations else None
    if (
        terminal not in allowed_terminals
        or not isinstance(outer.get("reason"), str)
        or not outer.get("reason")
        or len(str(outer.get("reason"))) > 4096
        or outer.get("passed") is not passed
        or outer.get("event_count") != len(observations)
        or outer.get("last_event_semantic_identity_sha256") != expected_last
        or outer.get("handshake_passed") is not (handshake is not None)
        or outer.get("adapter_probe_passed") is not (adapter_probe is not None)
        or outer.get("claims") != CLAIMS
    ):
        raise ValueError("work-preflight v4 terminal contract differs")
    if terminal_evidence is not None and (
        terminal_evidence.get("terminal") != terminal
        or terminal_evidence.get("passed") is not passed
    ):
        raise ValueError("work-preflight v4 scientific and owner terminals disagree")
    if terminal not in {"infrastructure_failure", "laboratory_wall_rejection"} and (
        handshake is None or adapter_probe is None or terminal_evidence is None
    ):
        raise ValueError("work-preflight v4 scientific terminal lacks lifecycle evidence")

    scientific = _v1.rebind_work_preflight_journal(
        _build_v1_view(observations, outer), rebind_current_sources=False
    )
    if scientific.terminal != terminal or scientific.passed is not passed:
        raise ValueError("work-preflight v4 inherited scientific rebound differs")
    return WorkPreflightV4Rebinding(
        terminal=str(terminal),
        passed=passed,
        event_count=len(observations),
        handshake=handshake,
        adapter_probe=adapter_probe,
        repair=repair,
        commands=commands,
        cleanup=cleanup,
        phases=scientific.phases,
        projection=scientific.projection,
        journal_byte_count=len(raw),
        scientific_rebinding=scientific,
    )


def rebind_work_preflight_v4_file(path: Path = _RESULT) -> WorkPreflightV4Rebinding:
    recovery = recover_journal_file(
        path,
        expected_protocol_sha256=WORK_PREFLIGHT_V4_PROTOCOL_SHA256,
        expected_campaign_sha256=WORK_PREFLIGHT_V4_CAMPAIGN_SHA256,
    )
    if recovery.failure is not None:
        raise ValueError(
            f"work-preflight v4 result is incomplete: {recovery.failure.reason}"
        )
    return rebind_work_preflight_v4_journal(path.read_bytes())


__all__ = [
    "CommandEvidence",
    "ENVELOPE_CONFIG_SHA256",
    "PREREGISTERED_CONFIG_SHA256",
    "RESULT_RELATIVE_PATH",
    "WORK_PREFLIGHT_V4_CAMPAIGN_SHA256",
    "WORK_PREFLIGHT_V4_PROTOCOL_SHA256",
    "WorkPreflightV4Rebinding",
    "rebind_work_preflight_v4_file",
    "rebind_work_preflight_v4_journal",
]
