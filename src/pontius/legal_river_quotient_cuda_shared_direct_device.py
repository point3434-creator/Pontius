"""Prospective ADR-0419 shared-direct bounded device differential.

Import is device-free. Real compilation, loading, external inspection, and
kernel launch occur only through run_shared_direct_device_validation in a
fresh owner child after a separate source seal.
"""

from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from fractions import Fraction
import gc
from hashlib import sha256
import inspect
import json
import math
from math import comb
import os
from pathlib import Path
import re
import struct
import tempfile
from time import perf_counter_ns
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from . import legal_river_exact_cubin_zero_suffix_diagnostic as _suffix
from . import legal_river_quotient_cuda_compensated_tiles as _paired
from . import legal_river_quotient_cuda_compensated_work_preflight as _v4
from . import legal_river_quotient_cuda_shared_direct_oracle as _shared


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-cuda-shared-direct-device-v1.json"
)
PREREGISTRATION_ADR_RELATIVE_PATH = (
    "docs/decisions/ADR-0419-preregister-the-shared-direct-device-differential.md"
)
PROSPECTIVE_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_shared_direct_device_v1.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
REFERENCE_SUFFIX_ARTIFACT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_exact_cubin_zero_suffix_diagnostic_v1.jsonl"
)
RETAINED_V4_ARTIFACT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v4.jsonl"
)
CONFIG_SHA256 = (
    "1dcc3f1ae2d528ab0625c3024f5dc04238ee49df9b6fbdc750b0e6e9352854d3"
)
PREREGISTRATION_ADR_SHA256 = (
    "165673ce976bd8f2653026a648d611014c59d5a150ed8ac3ca542d9229a84a5c"
)
PREREGISTRATION_COMMIT = "a457f8f73d2f69a66ac3d52361d1e96ddf0f02ac"
SHARED_SOURCE_SHA256 = (
    "e676b4dc4af07f294303c525613d92f4f8f24bef7ac60ed047bd5c73c9a9029d"
)
SHARED_CONTROLS_SHA256 = (
    "3e876015541cd135c7dcfb0ae4c30dd5650a5bbad3c04458de5913637c436dba"
)
BUILT_CUDA_SOURCE_SHA256 = (
    "e2049c53eae383a604efd656c6eb18ed54994bfed09f81cc42abff403d757ee4"
)
V4_SOURCE_SHA256 = (
    "652a4a37cd097a92829364f1ec6976a6f31a4092ab9fc3e0f97a992e2565c4aa"
)
PAIRED_SOURCE_SHA256 = (
    "03a7efb35243b8d13d495a7f80838170055096c8e9ae73d2cc723e3d29f1020d"
)
REFERENCE_SUFFIX_ARTIFACT_SHA256 = (
    "f4b3de941ed57e0f4acdfc7314315b6e70b10bd0034cf82113f17bf27e39a2de"
)
RETAINED_V4_ARTIFACT_SHA256 = (
    "4c038ffd45aa1b23e5e4aaf8cef4fbeafaf489a141e58335baf1b66e598816c6"
)
REFERENCE_SUFFIX_ARTIFACT_BYTES = 6_164_894
REFERENCE_REPAIRED_CUBIN_SHA256 = (
    "97693be7baafd882ad64a1a7da0ede23dc927efd872b0d15697b2486957ea894"
)
REFERENCE_REPAIRED_CUBIN_BYTES = 514_040

COMPILER_PAYLOAD_LIMIT = 8_388_608
STREAM_LIMIT = 8_388_608
STREAM_CHUNK_BYTES = 196_608
VERSION_PARSER_LIMIT = 32_768
RESOURCE_PARSER_LIMIT = 262_144
COMMAND_WALL_NS = 30_000_000_000
POPULATION_WALL_NS = 90_000_000_000
LABORATORY_WALL_NS = 240_000_000_000
MAXIMUM_ALIGNMENT = 4_294_967_296

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
_ALLOWED_TRANSITIONS = MappingProxyType(
    {
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
)
_SHARED_COUNTERS = (
    "shared_direct_source_unranks",
    "shared_direct_compatible_coefficient_pair_adds",
    "shared_direct_boundary_pair_copies",
    "shared_direct_final_feature_pair_products",
)
_PHASE_WORK_COUNTERS = MappingProxyType(
    {
        **{
            phase: tuple(counters)
            for phase, counters in _v4._PHASE_WORK_COUNTERS.items()
            if phase not in {"direct_query", "direct_fold"}
        },
        "shared_direct_fold_and_query": _SHARED_COUNTERS,
    }
)

_ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
_PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
_SECTION_HEADER = struct.Struct("<IIQQQQIIQQ")
_SHT_NOBITS = 8
_CUPY_IMPORT_CALLS = 0

Emit = Callable[[str, Mapping[str, object]], None]


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"shared-direct device path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    return value


def load_preregistered_device_config() -> dict[str, object]:
    path = _ROOT / CONFIG_RELATIVE_PATH
    raw = path.read_bytes()
    if len(raw) > 1_048_576 or (
        sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != CONFIG_SHA256
    ):
        raise ValueError("shared-direct device config identity differs")
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema_version") != (
        "legal-river-quotient-cuda-shared-direct-device-preregistration-v1"
    ):
        raise ValueError("shared-direct device config schema differs")
    return value


def verify_preregistered_device_contract(
    config: Mapping[str, object] | None = None,
    *,
    require_prospective_paths_absent: bool = False,
    allow_live_result: bool = False,
) -> None:
    value = load_preregistered_device_config() if config is None else config
    _shared.verify_preregistered_shared_direct_contract()
    _v4.verify_preregistered_work_preflight_contract()
    parent = _mapping(value.get("parent_identity"), label="device parent")
    expected = {
        PREREGISTRATION_ADR_RELATIVE_PATH: PREREGISTRATION_ADR_SHA256,
        "src/pontius/legal_river_quotient_cuda_shared_direct_oracle.py": (
            SHARED_SOURCE_SHA256
        ),
        "tests/test_legal_river_quotient_cuda_shared_direct_oracle.py": (
            SHARED_CONTROLS_SHA256
        ),
        "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py": (
            V4_SOURCE_SHA256
        ),
        "src/pontius/legal_river_quotient_cuda_compensated_tiles.py": (
            PAIRED_SOURCE_SHA256
        ),
    }
    for relative, digest in expected.items():
        if canonical_lf_sha256(_ROOT / relative) != digest:
            raise ValueError(f"shared-direct device parent differs: {relative}")
    exact_artifacts = {
        RETAINED_V4_ARTIFACT_RELATIVE_PATH: RETAINED_V4_ARTIFACT_SHA256,
        REFERENCE_SUFFIX_ARTIFACT_RELATIVE_PATH: (
            REFERENCE_SUFFIX_ARTIFACT_SHA256
        ),
    }
    for relative, digest in exact_artifacts.items():
        if sha256((_ROOT / relative).read_bytes()).hexdigest() != digest:
            raise ValueError(f"shared-direct retained artifact differs: {relative}")
    if sha256(_shared.CUDA_SOURCE.encode("utf-8")).hexdigest() != (
        BUILT_CUDA_SOURCE_SHA256
    ):
        raise ValueError("shared-direct built CUDA source differs")
    if parent.get("source_seal_commit") != (
        "4ddf72a0cad3fa2bfbe1b1743e219c53ccfc1b0c"
    ):
        raise ValueError("shared-direct source-seal commit differs")
    phase = _mapping(
        value.get("phase_and_work_contract"), label="device phase contract"
    )
    if phase.get("phase_order") != list(PHASE_ORDER):
        raise ValueError("shared-direct phase order differs")
    if require_prospective_paths_absent:
        for key in (
            "prospective_adapter_relative_path",
            "prospective_runner_relative_path",
            "prospective_reader_relative_path",
            "prospective_controls_relative_path",
            "prospective_result_relative_path",
        ):
            relative = parent.get(key)
            if not isinstance(relative, str) or (_ROOT / relative).exists():
                raise ValueError(f"shared-direct prospective path opened: {key}")
    forbidden = [RESERVED_ACTUAL_RESULT_RELATIVE_PATH]
    if not allow_live_result:
        forbidden.append(PROSPECTIVE_RESULT_RELATIVE_PATH)
    for relative in forbidden:
        if (_ROOT / relative).exists():
            raise ValueError(f"shared-direct forbidden result exists: {relative}")


@dataclass(frozen=True, slots=True)
class ContainerEvidence:
    mode: str
    raw_sha256: str
    raw_bytes: int
    loaded_sha256: str
    loaded_bytes: int
    loaded: bytes
    header: Mapping[str, object]
    program_header_count: int
    section_header_count: int
    section_table_sha256: str


def _bounded_range(offset: int, size: int, limit: int, *, label: str) -> int:
    if min(offset, size, limit) < 0 or offset > limit or size > limit - offset:
        raise ValueError(f"shared-direct {label} lies outside payload")
    return offset + size


def _header_mapping(header: tuple[object, ...]) -> Mapping[str, object]:
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
    return MappingProxyType(dict(zip(names, values, strict=True)))


def classify_compiler_payload(raw: bytes) -> ContainerEvidence:
    """Admit complete ELF or one frozen missing p_align high byte."""

    if not isinstance(raw, bytes) or not raw or len(raw) > COMPILER_PAYLOAD_LIMIT:
        raise ValueError("shared-direct compiler payload size differs")
    if len(raw) < _ELF_HEADER.size:
        raise ValueError("shared-direct compiler payload omits ELF header")
    header = _ELF_HEADER.unpack_from(raw, 0)
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
        or e_phnum <= 0
        or e_shnum <= 0
        or not 0 <= e_shstrndx < e_shnum
    ):
        raise ValueError("shared-direct ELF header semantics differ")
    ph_end = e_phoff + e_phentsize * e_phnum
    sh_end = e_shoff + e_shentsize * e_shnum
    if max(ph_end, sh_end) <= len(raw):
        mode = "complete_elf_without_edit"
        loaded = raw
    else:
        final_start = e_phoff + e_phentsize * (e_phnum - 1)
        partial = raw[final_start:]
        low_alignment = (
            int.from_bytes(partial[-7:], "little") if len(partial) == 55 else -1
        )
        bounded_alignment = (
            low_alignment in {0, 1}
            or (
                1 < low_alignment <= MAXIMUM_ALIGNMENT
                and low_alignment & (low_alignment - 1) == 0
            )
        )
        if not (
            sh_end <= len(raw)
            and ph_end == len(raw) + 1
            and len(partial) == _PROGRAM_HEADER.size - 1
            and bounded_alignment
        ):
            raise ValueError("shared-direct payload is not the one-zero shape")
        mode = "one_zero_final_program_alignment_completion"
        loaded = raw + b"\x00"

    program_headers = tuple(
        _PROGRAM_HEADER.unpack_from(loaded, e_phoff + i * e_phentsize)
        for i in range(e_phnum)
    )
    for index, row in enumerate(program_headers):
        _type, _flags, offset, _vaddr, _paddr, file_size, memory_size, align = row
        _bounded_range(offset, file_size, len(loaded), label=f"program {index}")
        if memory_size < file_size or not (
            align in {0, 1}
            or (
                1 < align <= MAXIMUM_ALIGNMENT
                and align & (align - 1) == 0
            )
        ):
            raise ValueError("shared-direct program header semantics differ")
    section_end = _bounded_range(
        e_shoff,
        e_shentsize * e_shnum,
        len(loaded),
        label="section table",
    )
    section_bytes = loaded[e_shoff:section_end]
    sections = tuple(
        _SECTION_HEADER.unpack_from(section_bytes, i * e_shentsize)
        for i in range(e_shnum)
    )
    for index, row in enumerate(sections):
        _name, section_type, _flags, _address, offset, size, *_rest = row
        if section_type != _SHT_NOBITS:
            _bounded_range(offset, size, len(loaded), label=f"section {index}")
    names = sections[e_shstrndx]
    if names[1] == _SHT_NOBITS:
        raise ValueError("shared-direct section-name table is not file-backed")
    _bounded_range(names[4], names[5], len(loaded), label="section-name table")
    return ContainerEvidence(
        mode=mode,
        raw_sha256=sha256(raw).hexdigest(),
        raw_bytes=len(raw),
        loaded_sha256=sha256(loaded).hexdigest(),
        loaded_bytes=len(loaded),
        loaded=loaded,
        header=_header_mapping(header),
        program_header_count=len(program_headers),
        section_header_count=len(sections),
        section_table_sha256=sha256(section_bytes).hexdigest(),
    )


def reference_repaired_cubin() -> bytes:
    path = _ROOT / REFERENCE_SUFFIX_ARTIFACT_RELATIVE_PATH
    raw = path.read_bytes()
    if len(raw) != REFERENCE_SUFFIX_ARTIFACT_BYTES or sha256(raw).hexdigest() != (
        REFERENCE_SUFFIX_ARTIFACT_SHA256
    ):
        raise ValueError("shared-direct reference suffix artifact differs")
    from .legal_river_exact_cubin_zero_suffix_diagnostic_result import (
        rebind_zero_suffix_diagnostic_journal,
    )

    rebound = rebind_zero_suffix_diagnostic_journal(raw)
    payload = rebound.repaired_payload
    if (
        rebound.terminal != "suffix_reconstruction_pass"
        or not rebound.passed
        or payload is None
        or payload.byte_count != REFERENCE_REPAIRED_CUBIN_BYTES
        or payload.sha256 != REFERENCE_REPAIRED_CUBIN_SHA256
    ):
        raise ValueError("shared-direct reference cubin semantics differ")
    return payload.raw


def _shared_direct_forward_samples(
    cp: Any,
    kernels: Mapping[str, object],
    resident: Any,
    fixture: Any,
    source_table: Any,
    selected_records: Sequence[int],
    global_start: int,
    logical_width: int,
) -> tuple[np.ndarray, np.ndarray, tuple[int, ...]]:
    features = _paired._tile_boundary_features(
        global_start, global_start + logical_width
    )
    records = np.asarray(selected_records, dtype=np.int64)
    masks = np.asarray(
        [fixture.query_masks[int(record)] for record in records], dtype=np.uint64
    )
    device_masks = cp.asarray(masks, dtype=cp.uint64)
    device_records = cp.asarray(records, dtype=cp.int64)
    device_features = cp.asarray(np.asarray(features, dtype=np.int32))
    query_output = cp.empty((len(records), len(features), 2), dtype=cp.float64)
    fold_output = cp.empty((len(records), 4), dtype=cp.float64)
    if int(query_output.data.ptr) == int(fold_output.data.ptr):
        raise RuntimeError("shared-direct query and fold outputs alias")
    source_offset = _paired.cardinality_offsets(
        fixture.available_cards, _v4.SOURCE_CARDS
    )[_v4.SOURCE_CARDS]
    _paired._launch(
        kernels["direct_selected_fold_tile"],
        len(records),
        (
            source_table,
            np.int64(source_offset),
            np.int64(fixture.geometry.source_occupancies),
            np.int32(fixture.available_cards),
            np.int32(_v4.PHYSICAL_STRIDE_WIDTH),
            device_masks,
            device_records,
            np.int32(len(records)),
            device_features,
            np.int32(len(features)),
            np.int32(global_start),
            np.int32(logical_width),
            np.int32(_v4.SOURCE_RANK),
            resident.query_hands,
            resident.unary,
            resident.factors,
            resident.unary_offsets,
            resident.mixture,
            resident.transitions[3],
            resident.transitions[4],
            resident.terminal,
            np.int32(fixture.geometry.hand_width),
            np.float64(fixture.sunk_value),
            query_output,
            fold_output,
        ),
    )
    cp.cuda.get_current_stream().synchronize()
    return query_output.get(), fold_output.get().reshape(-1, 2, 2), features


def generated_function_sources() -> tuple[str, str]:
    forward = inspect.getsource(_paired._forward_once)
    old_helper = "_direct_forward_samples("
    if forward.count(old_helper) != 1:
        raise ValueError("shared-direct parent forward helper seam differs")
    forward = forward.replace(old_helper, "_shared_direct_forward_samples(", 1)

    population = inspect.getsource(_paired._run_device_population)
    replacements = (
        ("collect_direct = fixture.available_cards == 25", "collect_direct = True"),
        (
            "    del table, compatible, numerator_high, numerator_low",
            "    _phase_hook(\"forward_release\")\n"
            "    del table, compatible, numerator_high, numerator_low",
        ),
        (
            "    if missing_label_control:",
            "    _phase_hook(\"mutations_and_lifecycle\")\n"
            "    if missing_label_control:",
        ),
        (
            "    del table, covector, unique, resident",
            "    _phase_hook(\"final_release\")\n"
            "    del table, covector, unique, resident",
        ),
    )
    for old, new in replacements:
        if population.count(old) != 1:
            raise ValueError(f"shared-direct parent population seam differs: {old}")
        population = population.replace(old, new, 1)
    return forward, population


def _compile_generated_function(
    source: str,
    name: str,
    namespace: Mapping[str, object],
) -> Callable[..., object]:
    local = dict(namespace)
    exec(compile(source, f"<adr0419-{name}>", "exec"), local)
    result = local.get(name)
    if not callable(result):
        raise TypeError(f"shared-direct generated function is absent: {name}")
    return result


@dataclass(frozen=True, slots=True)
class SharedPhaseRow:
    ordinal: int
    population: int
    family: str
    repeat: int
    tile: int
    phase: str
    host_start_ns: int
    host_stop_ns: int
    host_ns: int
    device_ns: int
    chunks: tuple[int, int, int]
    work: Mapping[str, int]

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": "legal-river-shared-direct-phase-v1",
            "ordinal": self.ordinal,
            "population": self.population,
            "family": self.family,
            "repeat": self.repeat,
            "tile": self.tile,
            "phase": self.phase,
            "host_start_ns": self.host_start_ns,
            "host_stop_ns": self.host_stop_ns,
            "host_ns": self.host_ns,
            "device_ns": self.device_ns,
            "chunks": list(self.chunks),
            "work": dict(self.work),
        }


class SharedPhaseLedger:
    def __init__(
        self,
        *,
        population: int,
        family: str,
        chunks: tuple[int, int, int],
        device_terminal: Callable[[], int],
        emit: Callable[[SharedPhaseRow], None] | None,
        deadline_ns: int,
        clock_ns: Callable[[], int] = perf_counter_ns,
    ) -> None:
        if population not in (10, 22) or family not in _v4.POPULATION_FAMILIES:
            raise ValueError("shared-direct phase ledger identity differs")
        if len(chunks) != 3 or any(value <= 0 for value in chunks):
            raise ValueError("shared-direct phase chunks differ")
        self.population = population
        self.family = family
        self.chunks = chunks
        self._device_terminal = device_terminal
        self._emit = emit
        self._deadline = deadline_ns
        self._clock = clock_ns
        self._rows: list[SharedPhaseRow] = []
        self._phase: str | None = None
        self._start: int | None = None
        self._repeat = 0
        self._tile = 0
        self._work: dict[str, int] = {}
        self.direction = "fixture"
        self.mutation_mode = False

    @property
    def rows(self) -> tuple[SharedPhaseRow, ...]:
        return tuple(self._rows)

    def start(self, *, repeat: int, tile: int) -> None:
        if self._start is not None:
            raise RuntimeError("shared-direct phase ledger already started")
        self._phase = PHASE_ORDER[0]
        self._repeat = repeat
        self._tile = tile
        self._start = self._clock()

    def add_work(self, name: str, count: int) -> None:
        if self._phase is None or self._start is None:
            raise RuntimeError("shared-direct work arrived outside a phase")
        if name not in _PHASE_WORK_COUNTERS.get(self._phase, ()):
            raise ValueError("shared-direct work belongs to another phase")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("shared-direct work count differs")
        self._work[name] = self._work.get(name, 0) + count

    def _close(self, stop: int, device_ns: int) -> None:
        assert self._phase is not None and self._start is not None
        if stop < self._start:
            raise RuntimeError("shared-direct phase clock reversed")
        row = SharedPhaseRow(
            ordinal=len(self._rows),
            population=self.population,
            family=self.family,
            repeat=self._repeat,
            tile=self._tile,
            phase=self._phase,
            host_start_ns=self._start,
            host_stop_ns=stop,
            host_ns=stop - self._start,
            device_ns=device_ns,
            chunks=self.chunks,
            work=MappingProxyType(dict(self._work)),
        )
        self._rows.append(row)
        if self._emit is not None:
            self._emit(row)
        self._work.clear()
        self._start = stop

    def switch(self, phase: str, *, repeat: int, tile: int) -> None:
        if self._phase is None or self._start is None:
            raise RuntimeError("shared-direct phase ledger was not started")
        if (phase, repeat, tile) == (self._phase, self._repeat, self._tile):
            return
        if phase not in _ALLOWED_TRANSITIONS[self._phase]:
            raise ValueError(
                f"shared-direct phase transition differs: {self._phase}->{phase}"
            )
        device_ns = self._device_terminal()
        stop = self._clock()
        self._close(stop, device_ns)
        if stop > self._deadline:
            raise TimeoutError("shared_direct_population_wall_crossed")
        self._phase = phase
        self._repeat = repeat
        self._tile = tile

    def finish(self) -> tuple[SharedPhaseRow, ...]:
        if self._phase is None or self._start is None:
            raise RuntimeError("shared-direct phase ledger was not started")
        if self._phase != PHASE_ORDER[-1]:
            raise RuntimeError("shared-direct phase ledger did not reach final release")
        device_ns = self._device_terminal()
        stop = self._clock()
        self._close(stop, device_ns)
        if stop > self._deadline:
            raise TimeoutError("shared_direct_population_wall_crossed")
        rows = tuple(self._rows)
        if any(
            left.host_stop_ns != right.host_start_ns
            for left, right in zip(rows, rows[1:])
        ) or sum(row.host_ns for row in rows) != (
            rows[-1].host_stop_ns - rows[0].host_start_ns
        ):
            raise AssertionError("shared-direct phase partition differs")
        self._phase = None
        self._start = None
        return rows


class _CudaBoundaryClock:
    def __init__(self, cp: Any) -> None:
        self._cp = cp
        self._start = cp.cuda.Event()
        self._start.record()

    def terminal(self) -> int:
        stop = self._cp.cuda.Event()
        stop.record()
        stop.synchronize()
        milliseconds = float(self._cp.cuda.get_elapsed_time(self._start, stop))
        self._start = self._cp.cuda.Event()
        self._start.record()
        return int(math.ceil(milliseconds * 1_000_000.0))


def _integer_argument(arguments: tuple[object, ...], index: int) -> int:
    value = arguments[index]
    if isinstance(value, np.generic):
        return int(value.item())
    return int(value)  # type: ignore[arg-type]


class _CampaignTracker:
    def __init__(self, ledger: SharedPhaseLedger, available_cards: int) -> None:
        self.ledger = ledger
        self.available_cards = available_cards
        self.geometry = _v4.population_geometry(available_cards)
        self.repeat = 0
        self.tile = 0
        self.launch_counts: dict[str, int] = {}

    def set_context(self, direction: str, *, repeat: int, tile: int) -> None:
        self.ledger.direction = direction
        self.repeat = repeat
        self.tile = tile

    def switch(self, phase: str) -> None:
        self.ledger.switch(phase, repeat=self.repeat, tile=self.tile)

    def before_kernel(self, name: str, arguments: tuple[object, ...]) -> None:
        self.launch_counts[name] = self.launch_counts.get(name, 0) + 1
        if name == "direct_selected_queries_tile":
            raise RuntimeError("reference query entered shared population")
        if self.ledger.mutation_mode:
            self.switch("mutations_and_lifecycle")
            return
        direction = self.ledger.direction
        if name == "source_coefficients_tile":
            phase = "forward_source_and_offset"
        elif name == "direct_selected_fold_tile":
            phase = "shared_direct_fold_and_query"
        elif name == "zeta_level_tile":
            phase = (
                "forward_recurrence"
                if direction == "forward"
                else "adjoint_recurrence_and_signed_sources"
            )
        elif name == "signed_targets_tile":
            phase = (
                "forward_signed_targets"
                if _integer_argument(arguments, 4) == 0
                else "adjoint_recurrence_and_signed_sources"
            )
        elif name in {"fold_query_tile", "reduce_contiguous_pairs"}:
            phase = "forward_fold_and_global_tree"
        elif name in {
            "build_numerator_covector_tile",
            "aggregate_query_labels_tile",
        }:
            phase = "adjoint_covector_and_labels"
        elif name == "direct_selected_adjoint_tile":
            phase = "direct_adjoint"
        elif name == "source_adjoint_contract_tile":
            phase = "adjoint_source_contract_and_global_tree"
        elif name in {"reduce_strided_pairs", "finalize_pair_result"}:
            phase = (
                "forward_fold_and_global_tree"
                if direction == "forward"
                else "adjoint_source_contract_and_global_tree"
            )
        else:
            return
        self.switch(phase)

    def after_kernel(self, name: str, arguments: tuple[object, ...]) -> None:
        if self.ledger.mutation_mode:
            return
        add = self.ledger.add_work
        if name == "source_coefficients_tile":
            rank_start = _integer_argument(arguments, 2)
            records = _integer_argument(arguments, 3)
            if rank_start == 0 and records == self.geometry.source_occupancies:
                add("source_pairing_visits", records * 90)
                add("source_weight_pair_times_float64", records * 90 * 6)
        elif name == "zeta_level_tile":
            rows = _integer_argument(arguments, 3)
            n = _integer_argument(arguments, 4)
            level = _integer_argument(arguments, 5)
            logical = _integer_argument(arguments, 7)
            prefix = (
                "forward" if self.ledger.direction == "forward" else "adjoint"
            )
            add(
                f"{prefix}_recurrence_pair_child_adds",
                rows * logical * (n - level),
            )
            add(f"{prefix}_pair_divides", rows * logical)
        elif name == "signed_targets_tile":
            source_cards = _integer_argument(arguments, 2)
            target_cards = _integer_argument(arguments, 5)
            records = _integer_argument(arguments, 7)
            logical = _integer_argument(arguments, 9)
            terms = sum(
                comb(target_cards, level)
                for level in range(source_cards + 1)
            )
            prefix = (
                "forward"
                if _integer_argument(arguments, 4) == 0
                else "adjoint"
            )
            add(f"{prefix}_signed_subset_pair_terms", records * logical * terms)
        elif name == "fold_query_tile":
            add(
                "forward_fold_pair_times_pair",
                _integer_argument(arguments, 2)
                * _integer_argument(arguments, 4),
            )
        elif name == "build_numerator_covector_tile":
            add(
                "adjoint_covector_pair_times_float64",
                _integer_argument(arguments, 2)
                * _integer_argument(arguments, 4),
            )
        elif name == "aggregate_query_labels_tile":
            add(
                "adjoint_label_pair_adds",
                _integer_argument(arguments, 2)
                * _integer_argument(arguments, 3)
                * _integer_argument(arguments, 4),
            )
        elif name == "source_adjoint_contract_tile":
            records = _integer_argument(arguments, 2)
            logical = _integer_argument(arguments, 4)
            add("adjoint_source_pairing_visits", records * 90)
            add("adjoint_source_weight_pair_times_float64", records * 90 * 6)
            add("adjoint_contract_pair_times_pair", records * logical)
        elif name == "reduce_contiguous_pairs":
            add("forward_tree_contributions", _integer_argument(arguments, 2))
        elif name == "reduce_strided_pairs":
            counter = (
                "forward_tree_contributions"
                if self.ledger.direction == "forward"
                else "adjoint_tree_contributions"
            )
            add(counter, _integer_argument(arguments, 4))
        elif name == "direct_selected_fold_tile":
            rows = _integer_argument(arguments, 2)
            n = _integer_argument(arguments, 3)
            queries = _integer_argument(arguments, 7)
            features = _integer_argument(arguments, 9)
            logical = _integer_argument(arguments, 11)
            add("shared_direct_source_unranks", queries * rows)
            add(
                "shared_direct_compatible_coefficient_pair_adds",
                queries * comb(n - 4, 6) * logical,
            )
            add("shared_direct_boundary_pair_copies", queries * features)
            add("shared_direct_final_feature_pair_products", queries * logical)
        elif name == "direct_selected_adjoint_tile":
            sources = _integer_argument(arguments, 1)
            features = _integer_argument(arguments, 3)
            n = _integer_argument(arguments, 6)
            records = _integer_argument(arguments, 8)
            compatible = 6 * comb(n - 6, 4)
            add("direct_adjoint_source_unranks", sources)
            add("direct_adjoint_query_record_visits", sources * records)
            add(
                "direct_adjoint_compatible_query_weight_builds",
                sources * compatible,
            )
            add(
                "direct_adjoint_compatible_boundary_pair_adds",
                sources * compatible * features,
            )


class _KernelProxy:
    def __init__(self, name: str, target: Any, tracker: _CampaignTracker) -> None:
        self.name = name
        self.target = target
        self.tracker = tracker

    @property
    def ptr(self) -> Any:
        return self.target.ptr

    def linear_launch(
        self,
        total: int,
        arguments: tuple[object, ...],
        **kwargs: Any,
    ) -> Any:
        self.tracker.before_kernel(self.name, arguments)
        result = self.target.linear_launch(total, arguments, **kwargs)
        self.tracker.after_kernel(self.name, arguments)
        return result


def build_generated_population_runner(
    tracker: _CampaignTracker,
) -> Callable[..., _paired.PairedPopulationExecution]:
    forward_source, population_source = generated_function_sources()
    namespace = dict(vars(_paired))
    namespace["_shared_direct_forward_samples"] = _shared_direct_forward_samples
    generated_forward = _compile_generated_function(
        forward_source, "_forward_once", namespace
    )
    forward_counts: dict[int, int] = {}
    adjoint_counts: dict[int, int] = {}

    def tile_index(start: int) -> int:
        return tuple(value for value, _ in _v4.LOGICAL_TILES).index(start)

    def forward_once(*args: Any, **kwargs: Any) -> dict[str, object]:
        tile = tile_index(int(kwargs["global_start"]))
        repeat = forward_counts.get(tile, 0)
        forward_counts[tile] = repeat + 1
        tracker.set_context("forward", repeat=repeat, tile=tile)
        tracker.switch("forward_source_and_offset")
        result = generated_forward(*args, **kwargs)
        tracker.switch("forward_capture_and_digest")
        return result  # type: ignore[return-value]

    def adjoint_once(*args: Any, **kwargs: Any) -> dict[str, object]:
        if tracker.ledger.mutation_mode:
            return _paired._adjoint_once(*args, **kwargs)
        tile = tile_index(int(kwargs["global_start"]))
        repeat = adjoint_counts.get(tile, 0)
        adjoint_counts[tile] = repeat + 1
        tracker.set_context("adjoint", repeat=repeat, tile=tile)
        tracker.switch("adjoint_covector_and_labels")
        result = _paired._adjoint_once(*args, **kwargs)
        tracker.switch("adjoint_capture_digest_and_exact_stream")
        return result

    def phase_hook(phase: str) -> None:
        if phase == "mutations_and_lifecycle":
            tracker.ledger.mutation_mode = True
        tracker.switch(phase)

    namespace.update(
        {
            "_forward_once": forward_once,
            "_adjoint_once": adjoint_once,
            "_phase_hook": phase_hook,
        }
    )
    return _compile_generated_function(
        population_source, "_run_device_population", namespace
    )  # type: ignore[return-value]


def _instrumented_kernels(
    kernels: Mapping[str, object],
    tracker: _CampaignTracker,
) -> Mapping[str, object]:
    return MappingProxyType(
        {
            name: _KernelProxy(name, target, tracker)
            for name, target in kernels.items()
        }
    )


def run_shared_family(
    cp: Any,
    kernels: Mapping[str, object],
    fixture: Any,
    *,
    family: str,
    chunks: tuple[int, int, int],
    tile_order: tuple[tuple[int, int], ...],
    missing_label_control: bool,
    deadline_ns: int,
    emit_phase: Callable[[SharedPhaseRow], None] | None,
) -> tuple[
    _paired.PairedPopulationExecution,
    tuple[SharedPhaseRow, ...],
    Mapping[str, int],
]:
    clock = _CudaBoundaryClock(cp)
    ledger = SharedPhaseLedger(
        population=fixture.available_cards,
        family=family,
        chunks=chunks,
        device_terminal=clock.terminal,
        emit=emit_phase,
        deadline_ns=deadline_ns,
    )
    first_tile = tuple(start for start, _ in _v4.LOGICAL_TILES).index(
        tile_order[0][0]
    )
    ledger.start(repeat=0, tile=first_tile)
    tracker = _CampaignTracker(ledger, fixture.available_cards)
    runner = build_generated_population_runner(tracker)
    execution = runner(
        cp,
        _instrumented_kernels(kernels, tracker),
        fixture,
        forward_query_chunk=chunks[0],
        adjoint_query_occupancy_chunk=chunks[1],
        adjoint_source_chunk=chunks[2],
        tile_order=tile_order,
        missing_label_control=missing_label_control,
    )
    rows = ledger.finish()
    return execution, rows, MappingProxyType(dict(tracker.launch_counts))


def expected_shared_campaign_work(available_cards: int) -> dict[str, int]:
    if available_cards not in (10, 22):
        raise ValueError("shared-direct expected work population differs")
    result = dict(_v4.complete_campaign_work(available_cards))
    result.pop("direct_query_source_unranks")
    result.pop("direct_query_compatible_boundary_pair_adds")
    result["shared_direct_source_unranks"] = result.pop(
        "direct_fold_source_unranks"
    )
    result["shared_direct_compatible_coefficient_pair_adds"] = result.pop(
        "direct_fold_compatible_coefficient_pair_adds"
    )
    result["shared_direct_final_feature_pair_products"] = result.pop(
        "direct_fold_final_feature_pair_products"
    )
    result["shared_direct_boundary_pair_copies"] = 512
    return result


def sum_phase_work(rows: Sequence[SharedPhaseRow]) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        for name, count in row.work.items():
            result[name] = result.get(name, 0) + int(count)
    return result


def phase_totals(rows: Sequence[SharedPhaseRow]) -> dict[str, int]:
    result = {phase: 0 for phase in PHASE_ORDER}
    for row in rows:
        result[row.phase] += row.host_ns
    return result


def _cupy_module():
    global _CUPY_IMPORT_CALLS
    _CUPY_IMPORT_CALLS += 1
    import cupy as cp

    return cp


def cupy_import_call_count() -> int:
    return _CUPY_IMPORT_CALLS


def _plain(value: Any) -> object:
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("shared-direct evidence contains a nonfinite float")
        return value.hex()
    if isinstance(value, Fraction):
        return [value.numerator, value.denominator]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value).hex()
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [_plain(item) for item in value]
    raise TypeError(
        f"unsupported shared-direct evidence type: {type(value).__name__}"
    )


def _emit_raw_chunks(
    emit: Emit,
    *,
    kind: str,
    stream_id: str,
    raw: bytes,
) -> None:
    if not isinstance(raw, bytes) or len(raw) > STREAM_LIMIT:
        raise ValueError("shared-direct retained stream exceeds cap")
    chunks = tuple(
        raw[index : index + STREAM_CHUNK_BYTES]
        for index in range(0, len(raw), STREAM_CHUNK_BYTES)
    )
    digest = sha256(raw).hexdigest()
    for index, chunk in enumerate(chunks):
        emit(
            kind,
            {
                "schema_version": "legal-river-shared-direct-raw-chunk-v1",
                "stream_id": stream_id,
                "chunk_index": index,
                "chunk_count": len(chunks),
                "chunk_raw_bytes": len(chunk),
                "total_raw_bytes": len(raw),
                "total_sha256": digest,
                "chunk_base64": b64encode(chunk).decode("ascii"),
            },
        )


@dataclass(slots=True)
class LoadedDeviceModules:
    shared_module: Any
    shared_kernels: Mapping[str, object]
    shared_payload: bytes
    container: ContainerEvidence
    reference_module: Any | None = None
    reference_kernels: Mapping[str, object] | None = None


def compile_and_load_shared_module(
    cp: Any,
    emit: Emit,
) -> LoadedDeviceModules:
    binary, _ = cp.cuda.compiler.compile_using_nvrtc(
        _shared.CUDA_SOURCE,
        options=_v4.CUDA_COMPILE_OPTIONS,
        cache_in_memory=True,
    )
    raw = bytes(binary)
    if len(raw) > COMPILER_PAYLOAD_LIMIT:
        raise ValueError("shared-direct compiler payload exceeds cap")
    _emit_raw_chunks(
        emit,
        kind="compiler_payload_chunk",
        stream_id="shared_nvrtc_payload",
        raw=raw,
    )
    emit(
        "compiler_payload_terminal",
        {
            "schema_version": "legal-river-shared-direct-compiler-payload-v1",
            "stream_id": "shared_nvrtc_payload",
            "byte_count": len(raw),
            "sha256": sha256(raw).hexdigest(),
            "built_cuda_source_sha256": BUILT_CUDA_SOURCE_SHA256,
            "caller_supplied_nvrtc_options": list(_v4.CUDA_COMPILE_OPTIONS),
        },
    )
    container = classify_compiler_payload(raw)
    emit(
        "container",
        {
            "schema_version": "legal-river-shared-direct-container-v1",
            "mode": container.mode,
            "raw_sha256": container.raw_sha256,
            "raw_bytes": container.raw_bytes,
            "loaded_sha256": container.loaded_sha256,
            "loaded_bytes": container.loaded_bytes,
            "appended_suffix_hex": (
                "00"
                if container.mode
                == "one_zero_final_program_alignment_completion"
                else ""
            ),
            "header": dict(container.header),
            "program_header_count": container.program_header_count,
            "section_header_count": container.section_header_count,
            "section_table_sha256": container.section_table_sha256,
        },
    )
    module = cp.cuda.function.Module()
    module.load(container.loaded)
    kernels = MappingProxyType(
        {
            name: module.get_function(name)
            for name in _v4.KERNEL_NAMES
        }
    )
    emit(
        "module",
        {
            "schema_version": "legal-river-shared-direct-module-v1",
            "loaded_sha256": sha256(container.loaded).hexdigest(),
            "loaded_bytes": len(container.loaded),
            "retained_object_is_loaded_object": True,
            "resolved_function_names": list(_v4.KERNEL_NAMES),
        },
    )
    return LoadedDeviceModules(
        shared_module=module,
        shared_kernels=kernels,
        shared_payload=container.loaded,
        container=container,
    )


def load_reference_control_module(
    cp: Any,
    modules: LoadedDeviceModules,
) -> None:
    raw = reference_repaired_cubin()
    module = cp.cuda.function.Module()
    module.load(raw)
    modules.reference_module = module
    modules.reference_kernels = MappingProxyType(
        {
            name: module.get_function(name)
            for name in (
                "direct_selected_queries_tile",
                "direct_selected_fold_tile",
            )
        }
    )


def _accepted_ascii(raw: bytes, *, maximum: int, label: str) -> str:
    if not isinstance(raw, bytes) or len(raw) > maximum:
        raise ValueError(f"shared-direct {label} exceeds parser admission")
    if any(
        byte not in {9, 10, 13} and not 0x20 <= byte <= 0x7E
        for byte in raw
    ):
        raise ValueError(f"shared-direct {label} is not strict ASCII")
    return raw.decode("ascii")


def _emit_command(
    emit: Emit,
    command_id: str,
    role: str,
    capture: _suffix.CommandCapture,
) -> None:
    for stream, raw in (
        ("stdout", capture.stdout),
        ("stderr", capture.stderr),
    ):
        _emit_raw_chunks(
            emit,
            kind="resource_command_chunk",
            stream_id=f"{command_id}:{stream}",
            raw=raw,
        )
    emit(
        "resource_command_terminal",
        {
            "schema_version": "legal-river-shared-direct-command-v1",
            "command_id": command_id,
            "argv_role": role,
            "status": capture.status,
            "return_code": capture.return_code,
            "stdout_bytes": len(capture.stdout),
            "stdout_sha256": sha256(capture.stdout).hexdigest(),
            "stderr_bytes": len(capture.stderr),
            "stderr_sha256": sha256(capture.stderr).hexdigest(),
            "elapsed_ns": capture.elapsed_ns,
        },
    )


def inspect_shared_resources(
    cp: Any,
    modules: LoadedDeviceModules,
    emit: Emit,
) -> dict[str, object]:
    all_driver = _paired._kernel_resource_report(cp, modules.shared_kernels)
    direct_names = (
        "direct_selected_queries_tile",
        "direct_selected_fold_tile",
        "direct_selected_adjoint_tile",
    )
    driver = {name: dict(all_driver[name]) for name in direct_names}
    tool = Path(
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\cuobjdump.exe"
    )
    if not tool.is_file():
        raise ValueError("shared-direct CUDA 13.3 cuobjdump is unavailable")
    version = _suffix.run_bounded_binary_command(
        [str(tool), "--version"],
        wall_limit_ns=COMMAND_WALL_NS,
        stream_limit=STREAM_LIMIT,
    )
    _emit_command(emit, "cuobjdump_version", "cuobjdump --version", version)
    if version.status != "completed" or version.return_code != 0:
        raise ValueError("shared-direct cuobjdump version command rejected")
    version_raw = b"\n".join(
        value.strip()
        for value in (version.stdout, version.stderr)
        if value.strip()
    )
    version_text = _accepted_ascii(
        version_raw,
        maximum=VERSION_PARSER_LIMIT,
        label="version output",
    )
    if re.search(r"(?<!\d)13\.3(?!\d)", version_text) is None:
        raise ValueError("shared-direct cuobjdump version differs")

    temporary: Path | None = None
    resource: _suffix.CommandCapture | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".cubin", delete=False) as handle:
            handle.write(modules.shared_payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        resource = _suffix.run_bounded_binary_command(
            [str(tool), "--dump-resource-usage", str(temporary)],
            wall_limit_ns=COMMAND_WALL_NS,
            stream_limit=STREAM_LIMIT,
        )
        _emit_command(
            emit,
            "cuobjdump_resource_usage",
            "cuobjdump --dump-resource-usage shared-payload",
            resource,
        )
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
            emit(
                "resource_cleanup",
                {
                    "schema_version": "legal-river-shared-direct-cleanup-v1",
                    "temporary_created": True,
                    "temporary_removed": not temporary.exists(),
                },
            )
    assert resource is not None
    if resource.status != "completed" or resource.return_code != 0:
        raise ValueError("shared-direct cuobjdump resource command rejected")
    resource_text = _accepted_ascii(
        resource.stdout,
        maximum=RESOURCE_PARSER_LIMIT,
        label="resource stdout",
    )
    parsed = _v4.parse_cuobjdump_resource_usage(resource_text)
    direct = {name: parsed[name] for name in direct_names}
    properties = cp.cuda.runtime.getDeviceProperties(int(cp.cuda.Device().id))
    combined = _v4.combined_direct_kernel_resource_report(
        direct,
        driver,
        multiprocessor_count=int(properties["multiProcessorCount"]),
        maximum_threads_per_multiprocessor=int(
            properties["maxThreadsPerMultiProcessor"]
        ),
    )
    evidence = {
        "schema_version": "legal-river-shared-direct-resource-v1",
        "tool_version": version_text,
        "shared_cubin_sha256": sha256(modules.shared_payload).hexdigest(),
        "shared_cubin_bytes": len(modules.shared_payload),
        "direct": direct,
        "driver_direct": driver,
        "effective_maxima": combined["effective_maxima"],
        "runtime_residency": combined["runtime_residency"],
        "gates": combined["gates"],
        "exact_spill_load_store_count": None,
    }
    emit("resource", evidence)
    return evidence


def complete_ten_reference_control(
    cp: Any,
    modules: LoadedDeviceModules,
    fixture: Any,
) -> dict[str, object]:
    if fixture.available_cards != 10 or modules.reference_kernels is None:
        raise ValueError("shared-direct complete-ten reference is unavailable")
    resident = _paired._allocate_resident(cp, fixture)
    geometry = fixture.geometry
    table = cp.empty(
        (geometry.source_recurrence_rows, _v4.PHYSICAL_STRIDE_WIDTH),
        dtype=cp.float64,
    )
    source_offset = _paired.cardinality_offsets(10, _v4.SOURCE_CARDS)[
        _v4.SOURCE_CARDS
    ]
    _, query_records = _v4.sample_rows(10)
    gates: dict[str, bool] = {}
    reference_digests: list[str] = []
    shared_digests: list[str] = []
    try:
        for tile, (start, stop) in enumerate(_v4.LOGICAL_TILES):
            logical = stop - start
            table.fill(_paired._POISON)
            _paired._launch_source_tile(
                modules.shared_kernels,
                resident,
                fixture,
                table,
                source_offset,
                0,
                geometry.source_occupancies,
                start,
                logical,
            )
            cp.cuda.get_current_stream().synchronize()
            ref_query, ref_fold, ref_features = _paired._direct_forward_samples(
                cp,
                modules.reference_kernels,
                resident,
                fixture,
                table,
                query_records,
                start,
                logical,
            )
            query, fold, features = _shared_direct_forward_samples(
                cp,
                modules.shared_kernels,
                resident,
                fixture,
                table,
                query_records,
                start,
                logical,
            )
            repeat_query, repeat_fold, repeat_features = (
                _shared_direct_forward_samples(
                    cp,
                    modules.shared_kernels,
                    resident,
                    fixture,
                    table,
                    query_records,
                    start,
                    logical,
                )
            )
            gates[f"tile_{tile}_feature_identity"] = (
                ref_features == features == repeat_features
            )
            gates[f"tile_{tile}_query_byte_identity"] = (
                ref_query.tobytes() == query.tobytes()
            )
            gates[f"tile_{tile}_fold_byte_identity"] = (
                ref_fold.tobytes() == fold.tobytes()
            )
            gates[f"tile_{tile}_shared_repeat_identity"] = (
                query.tobytes() == repeat_query.tobytes()
                and fold.tobytes() == repeat_fold.tobytes()
            )
            reference_digests.append(
                _paired._reporting_digest(ref_query, ref_fold)
            )
            shared_digests.append(_paired._reporting_digest(query, fold))
    finally:
        del table, resident
        gc.collect()
        cp.get_default_memory_pool().free_all_blocks()
        cp.get_default_pinned_memory_pool().free_all_blocks()
    gates["all_tile_digests_identical"] = reference_digests == shared_digests
    gates["query_fold_allocations_distinct"] = True
    gates["absolute_pool_release"] = (
        int(cp.get_default_memory_pool().used_bytes()) == 0
        and int(cp.get_default_memory_pool().total_bytes()) == 0
        and int(cp.get_default_pinned_memory_pool().n_free_blocks()) == 0
    )
    return {
        "schema_version": "legal-river-shared-direct-complete-ten-control-v1",
        "population": 10,
        "reference_query_launches": 3,
        "reference_fold_launches": 3,
        "shared_primary_launches": 3,
        "shared_repeat_launches": 3,
        "reference_digests": reference_digests,
        "shared_digests": shared_digests,
        "gates": gates,
        "all_gates_pass": all(gates.values()),
    }


def _runtime_payload(runtime: Any) -> dict[str, object]:
    return {
        "device_name": runtime.device_name,
        "compute_capability": runtime.compute_capability,
        "device_total_bytes": runtime.device_total_bytes,
        "cuda_driver_version": runtime.cuda_driver_version,
        "cuda_runtime_version": runtime.cuda_runtime_version,
        "cupy_version": runtime.cupy_version,
    }


def _terminal(
    name: str,
    *,
    reason: str,
    failed_population: int | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "legal-river-shared-direct-terminal-evidence-v1",
        "terminal": name,
        "passed": name == "completed_validation_pass",
        "reason": reason[:4096],
        "failed_population": failed_population,
        "capacity_projection": None,
        "complete_25_numerical_value": None,
    }


def _chunk_tuple(
    config: Mapping[str, object],
    cards: int,
    family: str,
) -> tuple[int, int, int]:
    population = _mapping(
        config.get("population_contract"), label="shared population"
    )
    chunks = _mapping(population.get("chunks"), label="shared chunks")
    by_cards = _mapping(chunks.get(str(cards)), label="shared card chunks")
    key = (
        "default"
        if family == _v4.POPULATION_FAMILIES[0]
        else "alternate"
    )
    values = by_cards.get(key)
    if not isinstance(values, list) or len(values) != 3:
        raise ValueError("shared-direct chunk tuple differs")
    result = tuple(int(value) for value in values)
    if any(value <= 0 for value in result):
        raise ValueError("shared-direct chunk value differs")
    return result  # type: ignore[return-value]


def _population_evidence(
    cards: int,
    executions: Sequence[_paired.PairedPopulationExecution],
    fixture: Any,
    rows: Sequence[SharedPhaseRow],
    launch_counts: Sequence[Mapping[str, int]],
    population_started_ns: int,
) -> dict[str, object]:
    if len(executions) != 2 or len(launch_counts) != 2:
        raise ValueError("shared-direct population family count differs")
    evidence = _v4._pair_error_evidence(
        cards, executions[0], executions[1], fixture
    )
    work = sum_phase_work(rows)
    expected = expected_shared_campaign_work(cards)
    totals = phase_totals(rows)
    campaign_host_ns = sum(totals.values())
    gates = dict(evidence["gates"])  # type: ignore[arg-type]
    gates.update(
        {
            "executed_work_ledger_exact": work == expected,
            "phase_partition_exact": all(
                left.host_stop_ns == right.host_start_ns
                for family in _v4.POPULATION_FAMILIES
                for left, right in zip(
                    [row for row in rows if row.family == family],
                    [row for row in rows if row.family == family][1:],
                )
            ),
            "all_fifteen_phases_observed": all(
                {
                    row.phase
                    for row in rows
                    if row.family == family
                }
                == set(PHASE_ORDER)
                for family in _v4.POPULATION_FAMILIES
            ),
            "population_reference_query_launches_zero": all(
                counts.get("direct_selected_queries_tile", 0) == 0
                for counts in launch_counts
            ),
            "shared_fold_launch_count": sum(
                counts.get("direct_selected_fold_tile", 0)
                for counts in launch_counts
            )
            == 12,
        }
    )
    population_elapsed_host_ns = perf_counter_ns() - population_started_ns
    gates["population_wall"] = population_elapsed_host_ns <= POPULATION_WALL_NS
    evidence["gates"] = gates
    evidence["all_gates_pass"] = all(gates.values())
    evidence["phase_host_ns"] = totals
    evidence["campaign_host_ns"] = campaign_host_ns
    evidence["population_elapsed_host_ns"] = population_elapsed_host_ns
    evidence["executed_work"] = work
    evidence["expected_work"] = expected
    evidence["launch_counts"] = [dict(value) for value in launch_counts]
    return evidence


def run_shared_direct_device_validation(
    emit: Emit | None = None,
) -> dict[str, object]:
    """Run the sole bounded science call; never construct population 25."""

    callback = emit or (lambda _kind, _payload: None)
    config = load_preregistered_device_config()
    verify_preregistered_device_contract(
        config, allow_live_result=emit is not None
    )
    started = perf_counter_ns()

    def send(kind: str, payload: Mapping[str, object]) -> None:
        callback(kind, _plain(payload))  # type: ignore[arg-type]

    try:
        cp = _cupy_module()
        runtime = _paired._runtime_identity(cp)
        v1, _ = _paired.load_preregistered_compensated_tile_configs()
        _paired._verify_runtime(runtime, v1)
        send(
            "runtime",
            {
                "schema_version": "legal-river-shared-direct-runtime-v1",
                "runtime": _runtime_payload(runtime),
                "built_cuda_source_sha256": BUILT_CUDA_SOURCE_SHA256,
            },
        )
        modules = compile_and_load_shared_module(cp, send)
    except Exception as error:
        return _terminal(
            "compiler_container_rejection",
            reason=f"{type(error).__name__}: {str(error) or 'no message'}",
        )

    try:
        resource = inspect_shared_resources(cp, modules, send)
        primitive = _paired._run_primitive_controls(cp, modules.shared_kernels)
        direct_order = _v4.run_direct_order_controls()
        send(
            "primitive",
            {
                "schema_version": "legal-river-shared-direct-primitive-v1",
                "operation_count": primitive.operation_count,
                "maximum_absolute_errors": primitive.maximum_absolute_errors,
                "low_lane_nonzero_counts": primitive.low_lane_nonzero_counts,
                "reporting_digest": primitive.reporting_digest,
                "gates": primitive.gates,
                "direct_order_controls": direct_order,
            },
        )
        if (
            not all(resource["gates"].values())  # type: ignore[union-attr]
            or not primitive.all_gates_pass
            or direct_order["all_gates_pass"] is not True
        ):
            return _terminal(
                "resource_rejection",
                reason="resource, primitive, or direct-order gate rejected",
            )
    except Exception as error:
        return _terminal(
            "resource_rejection",
            reason=f"{type(error).__name__}: {str(error) or 'no message'}",
        )

    fixtures: dict[int, Any] = {}
    try:
        fixtures[10] = _v4.compile_calibration_fixture(10)
        load_reference_control_module(cp, modules)
        send(
            "reference_module",
            {
                "schema_version": "legal-river-shared-direct-reference-module-v1",
                "reference_repaired_cubin_sha256": REFERENCE_REPAIRED_CUBIN_SHA256,
                "reference_repaired_cubin_bytes": REFERENCE_REPAIRED_CUBIN_BYTES,
                "allowed_function_names": [
                    "direct_selected_queries_tile",
                    "direct_selected_fold_tile",
                ],
            },
        )
        control = complete_ten_reference_control(cp, modules, fixtures[10])
        send("complete_ten_control", control)
        modules.reference_kernels = None
        modules.reference_module = None
        gc.collect()
        send(
            "reference_release",
            {
                "schema_version": "legal-river-shared-direct-reference-release-v1",
                "reference_functions_unreachable": True,
            },
        )
        if control["all_gates_pass"] is not True:
            return _terminal(
                "complete_ten_differential_rejection",
                reason="complete-ten reference/shared byte gate rejected",
                failed_population=10,
            )
        resident = _paired._allocate_resident(cp, fixtures[10])
        query_weight = _paired._query_weight_evidence(
            cp, modules.shared_kernels, resident, fixtures[10]
        )
        del resident
        gc.collect()
        cp.get_default_memory_pool().free_all_blocks()
        cp.get_default_pinned_memory_pool().free_all_blocks()
        send(
            "query_weight",
            {
                "schema_version": "legal-river-shared-direct-query-weight-v1",
                "records": list(query_weight.records),
                "maximum_absolute_error": query_weight.maximum_absolute_error,
                "nonzero_low_count": query_weight.nonzero_low_count,
                "reporting_digest": query_weight.reporting_digest,
                "gates": query_weight.gates,
            },
        )
        if not query_weight.all_gates_pass:
            return _terminal(
                "population_scientific_rejection",
                reason="complete-ten query-weight gate rejected",
                failed_population=10,
            )
    except Exception as error:
        return _terminal(
            "complete_ten_differential_rejection",
            reason=f"{type(error).__name__}: {str(error) or 'no message'}",
            failed_population=10,
        )

    for cards in (10, 22):
        if perf_counter_ns() - started > LABORATORY_WALL_NS:
            return _terminal(
                "laboratory_wall_rejection",
                reason="shared-direct laboratory wall crossed before population",
                failed_population=cards,
            )
        try:
            fixture = fixtures.get(cards) or _v4.compile_calibration_fixture(cards)
            fixtures[cards] = fixture
            population_started = perf_counter_ns()
            deadline = population_started + POPULATION_WALL_NS
            executions: list[_paired.PairedPopulationExecution] = []
            rows: list[SharedPhaseRow] = []
            counts: list[Mapping[str, int]] = []
            for family in _v4.POPULATION_FAMILIES:
                chunks = _chunk_tuple(config, cards, family)
                reverse = family == _v4.POPULATION_FAMILIES[1]

                def emit_phase(row: SharedPhaseRow) -> None:
                    rows.append(row)
                    send("phase", row.payload())

                execution, _, launches = run_shared_family(
                    cp,
                    modules.shared_kernels,
                    fixture,
                    family=family,
                    chunks=chunks,
                    tile_order=(
                        tuple(reversed(_v4.LOGICAL_TILES))
                        if reverse
                        else _v4.LOGICAL_TILES
                    ),
                    missing_label_control=not reverse,
                    deadline_ns=deadline,
                    emit_phase=emit_phase,
                )
                executions.append(execution)
                counts.append(launches)
                if perf_counter_ns() > deadline:
                    raise TimeoutError("shared_direct_population_wall_crossed")
            evidence = _population_evidence(
                cards,
                executions,
                fixture,
                rows,
                counts,
                population_started,
            )
            send("population", evidence)
            if evidence["all_gates_pass"] is not True:
                return _terminal(
                    "population_scientific_rejection",
                    reason="shared-direct population gate rejected",
                    failed_population=cards,
                )
        except TimeoutError as error:
            return _terminal(
                "population_wall_rejection",
                reason=str(error),
                failed_population=cards,
            )
        except Exception as error:
            return _terminal(
                "population_scientific_rejection",
                reason=f"{type(error).__name__}: {str(error) or 'no message'}",
                failed_population=cards,
            )

    if perf_counter_ns() - started > LABORATORY_WALL_NS:
        return _terminal(
            "laboratory_wall_rejection",
            reason="shared-direct laboratory wall crossed after populations",
        )
    return _terminal(
        "completed_validation_pass",
        reason="all frozen shared-direct validation gates passed",
    )


def source_seal_report() -> Mapping[str, object]:
    config = load_preregistered_device_config()
    verify_preregistered_device_contract(config)
    forward, population = generated_function_sources()
    reference = reference_repaired_cubin()
    complete = classify_compiler_payload(reference)
    repaired = classify_compiler_payload(reference[:-1])
    gates = {
        "cupy_not_imported": _CUPY_IMPORT_CALLS == 0,
        "built_cuda_source_bound": (
            sha256(_shared.CUDA_SOURCE.encode("utf-8")).hexdigest()
            == BUILT_CUDA_SOURCE_SHA256
        ),
        "forward_helper_one_substitution": (
            forward.count("_shared_direct_forward_samples(") == 1
            and re.search(r"(?<!shared)_direct_forward_samples\(", forward)
            is None
        ),
        "population_collect_direct_true": (
            population.count("collect_direct = True") == 1
            and "fixture.available_cards == 25" not in population
        ),
        "population_phase_hooks_exact": population.count("_phase_hook(") == 3,
        "complete_container_control": (
            complete.mode == "complete_elf_without_edit"
        ),
        "one_zero_container_control": (
            repaired.mode == "one_zero_final_program_alignment_completion"
            and repaired.loaded_sha256 == complete.loaded_sha256
        ),
        "slot_nine_is_feature_count": (
            "features = _integer_argument(arguments, 9)" in inspect.getsource(
                _CampaignTracker.after_kernel
            )
        ),
        "slot_eleven_is_logical_width": (
            "logical = _integer_argument(arguments, 11)" in inspect.getsource(
                _CampaignTracker.after_kernel
            )
        ),
        "population_25_not_admitted": (
            set((10, 22)) == set(_v4.CALIBRATION_POPULATIONS)
        ),
        "prospective_result_absent": not (
            _ROOT / PROSPECTIVE_RESULT_RELATIVE_PATH
        ).exists(),
        "reserved_actual_absent": not (
            _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        ).exists(),
    }
    return MappingProxyType(
        {
            "schema_version": "legal-river-shared-direct-device-source-seal-v1",
            "config_sha256": CONFIG_SHA256,
            "built_cuda_source_sha256": BUILT_CUDA_SOURCE_SHA256,
            "generated_forward_sha256": sha256(
                forward.encode("utf-8")
            ).hexdigest(),
            "generated_population_sha256": sha256(
                population.encode("utf-8")
            ).hexdigest(),
            "reference_cubin_sha256": complete.loaded_sha256,
            "gates": MappingProxyType(gates),
            "all_gates_pass": all(gates.values()),
        }
    )


__all__ = [
    "BUILT_CUDA_SOURCE_SHA256",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "ContainerEvidence",
    "LABORATORY_WALL_NS",
    "PHASE_ORDER",
    "POPULATION_WALL_NS",
    "PROSPECTIVE_RESULT_RELATIVE_PATH",
    "RESERVED_ACTUAL_RESULT_RELATIVE_PATH",
    "SharedPhaseLedger",
    "SharedPhaseRow",
    "build_generated_population_runner",
    "canonical_lf_sha256",
    "classify_compiler_payload",
    "complete_ten_reference_control",
    "cupy_import_call_count",
    "expected_shared_campaign_work",
    "generated_function_sources",
    "load_preregistered_device_config",
    "reference_repaired_cubin",
    "run_shared_direct_device_validation",
    "run_shared_family",
    "source_seal_report",
    "verify_preregistered_device_contract",
]
