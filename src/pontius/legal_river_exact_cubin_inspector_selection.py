"""Artifact-only selector for ADR-0407's exact-cubin diagnostic corpus.

Importing this module is device-, process-, network-, and write-free.  The
authoritative entry point reads only ADR-0406's immutable journal after it has
validated this module's separately committed source seal.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Final

from .legal_river_exact_cubin_inspector_diagnostic_result import (
    BinaryEvidence,
    CandidateEvidence,
    ExactCubinDiagnosticRebinding,
    rebind_exact_cubin_diagnostic_file,
)


_ROOT: Final = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH: Final = (
    "experiments/configs/legal-river-exact-cubin-inspector-selection-v1.json"
)
INPUT_RELATIVE_PATH: Final = (
    "artifacts/work_preflight/legal_river_exact_cubin_inspector_diagnostic_v1.jsonl"
)
RESULT_RELATIVE_PATH: Final = (
    "experiments/results/legal-river-exact-cubin-inspector-selection-v1.json"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH: Final = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
CONFIG_SHA256: Final = (
    "70ca948001fc406cd3e4a9e9f8fd4f359184ed622753d92749c542d44a3ed73a"
)
INPUT_SHA256: Final = (
    "9e0d160dd36884adb85914f819e11882d5becc42071f7847c1503a42c1d83aed"
)
INPUT_BYTES: Final = 705_101
INPUT_RECORDS: Final = 12
INPUT_SOURCE_COMMIT: Final = "596a90e92285e04ec9e7e3e2f68b22cb195aa46b"
INPUT_CUBIN_SHA256: Final = (
    "5dc4973302061b29dccd955ff7ee4dff3d61216316fb5d2fa71e9df22f42cd97"
)
INPUT_CUBIN_BYTES: Final = 514_039
ELF_MAGIC: Final = b"\x7fELF"
SELECTOR_VERSION: Final = "legal-river-exact-cubin-inspector-selector-v1"
ASSESSMENT_SCHEMA_VERSION: Final = (
    "legal-river-exact-cubin-inspector-selection-assessment-v1"
)
DIRECT_KERNEL_NAMES: Final = (
    "direct_selected_queries_tile",
    "direct_selected_fold_tile",
    "direct_selected_adjoint_tile",
)
CANDIDATE_IDS: Final = (
    "cuobjdump_version",
    "cuobjdump_resource_usage",
    "cuobjdump_elf",
    "nvdisasm_version",
    "nvdisasm_default",
)
CANDIDATE_ROLES: Final = (
    "identity_support_only",
    "only_semantically_eligible_resource_candidate",
    "container_metadata_support_only",
    "identity_support_only",
    "disassembly_and_register_metadata_support_only_because_complete_stack_local_semantics_are_absent",
)
CANDIDATE_SELECTABLE: Final = (False, True, False, False, False)
CUOBJDUMP_IDENTITY_SUBSTRINGS: Final = (
    "cuobjdump: NVIDIA (R) fat binary listing tool",
    "Cuda compilation tools, release 13.3, V13.3.73",
    "Build cuda_13.3.r13.3/compiler.38244171_0",
)
REGISTER_CEILING: Final = 255
STACK_PLUS_LOCAL_CEILING_BYTES: Final = 4_096

_CONFIG = _ROOT / CONFIG_RELATIVE_PATH
_INPUT = _ROOT / INPUT_RELATIVE_PATH
_RESULT = _ROOT / RESULT_RELATIVE_PATH
_RESERVED = _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH


def canonical_lf_sha256(path: Path) -> str:
    """Hash one source/config file with checkout line endings normalized."""

    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"selector dependency is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _strict_ascii(raw: bytes, *, label: str) -> str:
    if not isinstance(raw, bytes):
        raise TypeError(f"{label} must be bytes")
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError(f"{label} is not strict ASCII") from error


def parse_cuobjdump_resource_usage(raw: bytes) -> dict[str, dict[str, int]]:
    """Parse the prospectively frozen complete per-function resource grammar."""

    output = _strict_ascii(raw, label="cuobjdump resource stdout")
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
        for label, value in re.findall(r"([A-Z]+(?:\[\d+\])?):(\d+)", line):
            if label in rows[current]:
                raise ValueError("cuobjdump resource output repeats a field")
            rows[current][label] = int(value)

    for name in DIRECT_KERNEL_NAMES:
        if name not in rows:
            raise ValueError("cuobjdump resource output omits a direct kernel")
        if not {"REG", "STACK", "LOCAL"}.issubset(rows[name]):
            raise ValueError("cuobjdump direct resource row is incomplete")
    return {
        name: {field: rows[name][field] for field in ("REG", "STACK", "LOCAL")}
        for name in DIRECT_KERNEL_NAMES
    }


@dataclass(frozen=True, slots=True)
class RetainedInputContract:
    artifact_sha256: str
    artifact_bytes: int
    artifact_records: int
    source_commit: str
    terminal: str
    event_count: int
    cubin_sha256: str
    cubin_bytes: int
    cubin_magic: bytes


REAL_INPUT_CONTRACT: Final = RetainedInputContract(
    artifact_sha256=INPUT_SHA256,
    artifact_bytes=INPUT_BYTES,
    artifact_records=INPUT_RECORDS,
    source_commit=INPUT_SOURCE_COMMIT,
    terminal="capture_complete",
    event_count=10,
    cubin_sha256=INPUT_CUBIN_SHA256,
    cubin_bytes=INPUT_CUBIN_BYTES,
    cubin_magic=ELF_MAGIC,
)


@dataclass(frozen=True, slots=True)
class CandidateAssessment:
    candidate_id: str
    role: str
    selectable: bool
    status: str
    return_code: int | None
    stdout_sha256: str
    stdout_bytes: int
    stderr_sha256: str
    stderr_bytes: int
    qualification_status: str
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InspectorSelectionAssessment:
    schema_version: str
    selector_version: str
    selector_source_sha256: str
    input_artifact_sha256: str
    input_artifact_bytes: int
    input_artifact_records: int
    input_source_commit: str
    cubin_sha256: str
    cubin_bytes: int
    identity_contract_pass: bool
    candidate_assessments: tuple[CandidateAssessment, ...]
    selected_inspector: str | None
    selected_resource_rows: Mapping[str, Mapping[str, int]] | None
    combined_direct_rows: Mapping[str, Mapping[str, int]] | None
    terminal: str
    resource_gate_result: None
    calibration_result: None
    capacity_projection: None


def _validate_binary(value: BinaryEvidence, *, label: str) -> None:
    if not isinstance(value, BinaryEvidence):
        raise TypeError(f"{label} type differs")
    if value.byte_count != len(value.raw) or value.sha256 != sha256(value.raw).hexdigest():
        raise ValueError(f"{label} identity differs")


def _validate_driver_rows(
    rows: Mapping[str, Mapping[str, int]] | None,
) -> dict[str, dict[str, int]]:
    if not isinstance(rows, Mapping) or set(rows) != set(DIRECT_KERNEL_NAMES):
        raise ValueError("selector driver kernel inventory differs")
    expected_fields = {
        "local_size_bytes",
        "maximum_threads_per_block",
        "registers",
        "shared_size_bytes",
    }
    result: dict[str, dict[str, int]] = {}
    for name in DIRECT_KERNEL_NAMES:
        row = rows[name]
        if not isinstance(row, Mapping) or set(row) != expected_fields:
            raise ValueError("selector driver row fields differ")
        copied: dict[str, int] = {}
        for field in sorted(expected_fields):
            value = row[field]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("selector driver row value differs")
            copied[field] = value
        result[name] = copied
    return result


def validate_rebinding_identity(
    rebinding: ExactCubinDiagnosticRebinding,
    *,
    raw_artifact: bytes,
    contract: RetainedInputContract = REAL_INPUT_CONTRACT,
) -> tuple[dict[str, dict[str, int]], tuple[CandidateEvidence, ...]]:
    """Rebind artifact, payload, driver, and ordered candidate identities."""

    if not isinstance(rebinding, ExactCubinDiagnosticRebinding):
        raise TypeError("selector rebinding type differs")
    if not isinstance(raw_artifact, bytes):
        raise TypeError("selector raw artifact must be bytes")
    if (
        len(raw_artifact) != contract.artifact_bytes
        or len(raw_artifact.splitlines()) != contract.artifact_records
        or sha256(raw_artifact).hexdigest() != contract.artifact_sha256
    ):
        raise ValueError("selector artifact identity differs")
    if (
        rebinding.terminal != contract.terminal
        or not rebinding.passed
        or rebinding.event_count != contract.event_count
        or rebinding.source_commit != contract.source_commit
        or rebinding.journal_byte_count != contract.artifact_bytes
    ):
        raise ValueError("selector diagnostic terminal identity differs")
    if rebinding.cubin is None:
        raise ValueError("selector cubin is absent")
    _validate_binary(rebinding.cubin, label="selector cubin")
    if (
        rebinding.cubin.sha256 != contract.cubin_sha256
        or rebinding.cubin.byte_count != contract.cubin_bytes
        or not rebinding.cubin.raw.startswith(contract.cubin_magic)
    ):
        raise ValueError("selector cubin contract differs")
    candidates = rebinding.candidates
    if (
        not isinstance(candidates, tuple)
        or tuple(candidate.candidate_id for candidate in candidates) != CANDIDATE_IDS
    ):
        raise ValueError("selector candidate inventory differs")
    for candidate in candidates:
        if not isinstance(candidate, CandidateEvidence):
            raise TypeError("selector candidate type differs")
        _validate_binary(candidate.stdout, label=f"{candidate.candidate_id} stdout")
        _validate_binary(candidate.stderr, label=f"{candidate.candidate_id} stderr")
        if (
            candidate.status not in {"completed", "timeout", "output_limit"}
            or isinstance(candidate.return_code, bool)
            or (
                candidate.return_code is not None
                and not isinstance(candidate.return_code, int)
            )
            or isinstance(candidate.elapsed_ns, bool)
            or not isinstance(candidate.elapsed_ns, int)
            or candidate.elapsed_ns < 0
        ):
            raise ValueError("selector candidate transport row differs")
    return _validate_driver_rows(rebinding.driver_rows), candidates


def _identity_reasons(candidate: CandidateEvidence) -> tuple[str, ...]:
    reasons: list[str] = []
    if candidate.status != "completed":
        reasons.append("identity_status_not_completed")
    if candidate.return_code != 0:
        reasons.append("identity_return_code_nonzero")
    if candidate.stderr.byte_count != 0:
        reasons.append("identity_stderr_nonempty")
    try:
        text = _strict_ascii(candidate.stdout.raw, label="cuobjdump identity stdout")
    except ValueError:
        reasons.append("identity_stdout_not_ascii")
    else:
        for index, required in enumerate(CUOBJDUMP_IDENTITY_SUBSTRINGS):
            if required not in text:
                reasons.append(f"identity_substring_{index}_absent")
    return tuple(reasons)


def _resource_reasons(
    candidate: CandidateEvidence,
) -> tuple[tuple[str, ...], dict[str, dict[str, int]] | None]:
    reasons: list[str] = []
    if candidate.status != "completed":
        reasons.append("resource_status_not_completed")
    if candidate.return_code != 0:
        reasons.append("resource_return_code_nonzero")
    if candidate.stderr.byte_count != 0:
        reasons.append("resource_stderr_nonempty")
    parsed: dict[str, dict[str, int]] | None = None
    if not reasons:
        try:
            parsed = parse_cuobjdump_resource_usage(candidate.stdout.raw)
        except (TypeError, ValueError):
            reasons.append("resource_stdout_parser_rejection")
    return tuple(reasons), parsed


def _candidate_assessment(
    candidate: CandidateEvidence,
    *,
    role: str,
    selectable: bool,
    qualification_status: str,
    reasons: Sequence[str] = (),
) -> CandidateAssessment:
    return CandidateAssessment(
        candidate_id=candidate.candidate_id,
        role=role,
        selectable=selectable,
        status=candidate.status,
        return_code=candidate.return_code,
        stdout_sha256=candidate.stdout.sha256,
        stdout_bytes=candidate.stdout.byte_count,
        stderr_sha256=candidate.stderr.sha256,
        stderr_bytes=candidate.stderr.byte_count,
        qualification_status=qualification_status,
        reasons=tuple(reasons),
    )


def assess_candidates(
    candidates: Sequence[CandidateEvidence],
    driver_rows: Mapping[str, Mapping[str, int]],
    *,
    selector_source_sha256: str,
    input_contract: RetainedInputContract = REAL_INPUT_CONTRACT,
) -> InspectorSelectionAssessment:
    """Apply only ADR-0407's frozen candidate and quantity semantics."""

    if tuple(candidate.candidate_id for candidate in candidates) != CANDIDATE_IDS:
        raise ValueError("selector candidate order differs")
    if (
        not isinstance(selector_source_sha256, str)
        or len(selector_source_sha256) != 64
        or any(character not in "0123456789abcdef" for character in selector_source_sha256)
    ):
        raise ValueError("selector source digest differs")
    direct_driver = _validate_driver_rows(driver_rows)
    for candidate in candidates:
        _validate_binary(candidate.stdout, label=f"{candidate.candidate_id} stdout")
        _validate_binary(candidate.stderr, label=f"{candidate.candidate_id} stderr")

    identity_reasons = _identity_reasons(candidates[0])
    resource_reasons, parsed = _resource_reasons(candidates[1])
    identity_pass = not identity_reasons
    qualifies = identity_pass and not resource_reasons and parsed is not None

    reports: list[CandidateAssessment] = []
    for index, candidate in enumerate(candidates):
        if index == 0:
            state = "identity_support_pass" if identity_pass else "identity_support_rejected"
            reasons = identity_reasons
        elif index == 1:
            state = "qualified" if qualifies else "resource_candidate_rejected"
            reasons = resource_reasons + (
                () if identity_pass else ("paired_identity_contract_rejected",)
            )
        else:
            state = "ineligible_support_only"
            reasons = ("candidate_role_not_complete_resource_instrument",)
        reports.append(
            _candidate_assessment(
                candidate,
                role=CANDIDATE_ROLES[index],
                selectable=CANDIDATE_SELECTABLE[index],
                qualification_status=state,
                reasons=reasons,
            )
        )

    selected_rows: dict[str, dict[str, int]] | None = None
    combined: dict[str, dict[str, int]] | None = None
    if qualifies:
        assert parsed is not None
        selected_rows = parsed
        combined = {}
        for name in DIRECT_KERNEL_NAMES:
            driver = direct_driver[name]
            external = parsed[name]
            combined[name] = {
                "driver_registers": driver["registers"],
                "candidate_REG": external["REG"],
                "registers_max": max(driver["registers"], external["REG"]),
                "driver_local_size_bytes": driver["local_size_bytes"],
                "candidate_STACK_bytes": external["STACK"],
                "candidate_LOCAL_bytes": external["LOCAL"],
                "candidate_stack_plus_local_bytes": external["STACK"]
                + external["LOCAL"],
                "local_backing_max_bytes": max(
                    driver["local_size_bytes"],
                    external["STACK"] + external["LOCAL"],
                ),
            }

    return InspectorSelectionAssessment(
        schema_version=ASSESSMENT_SCHEMA_VERSION,
        selector_version=SELECTOR_VERSION,
        selector_source_sha256=selector_source_sha256,
        input_artifact_sha256=input_contract.artifact_sha256,
        input_artifact_bytes=input_contract.artifact_bytes,
        input_artifact_records=input_contract.artifact_records,
        input_source_commit=input_contract.source_commit,
        cubin_sha256=input_contract.cubin_sha256,
        cubin_bytes=input_contract.cubin_bytes,
        identity_contract_pass=identity_pass,
        candidate_assessments=tuple(reports),
        selected_inspector="cuobjdump_resource_usage" if qualifies else None,
        selected_resource_rows=selected_rows,
        combined_direct_rows=combined,
        terminal="qualified_inspector" if qualifies else "no_qualified_inspector",
        resource_gate_result=None,
        calibration_result=None,
        capacity_projection=None,
    )


def canonical_assessment_bytes(assessment: InspectorSelectionAssessment) -> bytes:
    """Return one canonical assessment record without its terminal LF."""

    if not isinstance(assessment, InspectorSelectionAssessment):
        raise TypeError("selector assessment type differs")
    value = {
        "dataclass": (
            "pontius.legal_river_exact_cubin_inspector_selection."
            "InspectorSelectionAssessment"
        ),
        "fields": asdict(assessment),
    }
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def select_sealed_adr0406_artifact() -> InspectorSelectionAssessment:
    """Read and select only the exact retained artifact after source sealing."""

    from .legal_river_exact_cubin_inspector_selection_seal import (
        ADR0408_SELECTOR_SOURCE_SHA256,
    )

    if _RESULT.exists():
        raise FileExistsError("selector authoritative result already exists")
    if _RESERVED.exists():
        raise RuntimeError("selector reserved actual result exists")
    if canonical_lf_sha256(_CONFIG) != CONFIG_SHA256:
        raise RuntimeError("selector config differs from ADR-0407")
    source_digest = canonical_lf_sha256(Path(__file__))
    if source_digest != ADR0408_SELECTOR_SOURCE_SHA256:
        raise RuntimeError("selector source differs from its committed seal")
    raw = _INPUT.read_bytes()
    if (
        len(raw) != INPUT_BYTES
        or len(raw.splitlines()) != INPUT_RECORDS
        or sha256(raw).hexdigest() != INPUT_SHA256
    ):
        raise RuntimeError("selector input artifact differs from ADR-0407")
    rebinding = rebind_exact_cubin_diagnostic_file(_INPUT)
    driver_rows, candidates = validate_rebinding_identity(
        rebinding,
        raw_artifact=raw,
    )
    return assess_candidates(
        candidates,
        driver_rows,
        selector_source_sha256=source_digest,
    )


def write_sealed_selection_result() -> InspectorSelectionAssessment:
    """Create ADR-0407's authoritative deterministic result exactly once."""

    if _RESULT.exists():
        raise FileExistsError("selector authoritative result already exists")
    assessment = select_sealed_adr0406_artifact()
    payload = canonical_assessment_bytes(assessment) + b"\n"
    _RESULT.parent.mkdir(parents=True, exist_ok=True)
    with _RESULT.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return assessment


def _main() -> int:
    assessment = write_sealed_selection_result()
    print(f"legal-river exact-cubin selector: terminal={assessment.terminal}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "ASSESSMENT_SCHEMA_VERSION",
    "CANDIDATE_IDS",
    "CANDIDATE_ROLES",
    "CANDIDATE_SELECTABLE",
    "CONFIG_SHA256",
    "CandidateAssessment",
    "DIRECT_KERNEL_NAMES",
    "INPUT_BYTES",
    "INPUT_RECORDS",
    "INPUT_SHA256",
    "InspectorSelectionAssessment",
    "REAL_INPUT_CONTRACT",
    "REGISTER_CEILING",
    "RESULT_RELATIVE_PATH",
    "RetainedInputContract",
    "SELECTOR_VERSION",
    "STACK_PLUS_LOCAL_CEILING_BYTES",
    "assess_candidates",
    "canonical_assessment_bytes",
    "canonical_lf_sha256",
    "parse_cuobjdump_resource_usage",
    "select_sealed_adr0406_artifact",
    "validate_rebinding_identity",
    "write_sealed_selection_result",
]
