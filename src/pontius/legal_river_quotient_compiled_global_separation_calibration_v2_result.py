"""Independent additive reader for the ADR-0460 absolute-Git successor."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from threading import RLock

from . import legal_river_quotient_compiled_global_separation_calibration_result as _parent
from .durable_evidence_journal import JournalRecordKind, recover_journal_bytes


ROOT = Path(__file__).parents[2]
RECOVERY_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v2-absolute-git.json"
)
RECOVERY_CONFIG_SHA256 = (
    "e9242618e674c74804990c17965de731da15a70adcd0c0094b650d7332313f4e"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v2.jsonl"
)
RESULT_PATH = ROOT / RESULT_RELATIVE_PATH
PARENT_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v1.jsonl"
)
PREREGISTRATION_COMMIT = "edaf6bc53952f4238172ed871fe0d601cb92c168"
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0460-absolute-git-compiled-separation-owner-v2"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0460-absolute-git-compiled-separation-campaign-v2"
).hexdigest()
GIT_PATH = Path(r"C:\Program Files\Git\cmd\git.exe")
GIT_BYTES = 46_920
GIT_SHA256 = "7b7971dd13f0c3a284e538601f2f9770b3a87dfaccb5fb52d68141c67ed22364"
DEPENDENCY_RELATIVE_PATHS = (
    RECOVERY_CONFIG_RELATIVE_PATH,
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v1.json",
    "docs/decisions/ADR-0457-preregister-the-compiled-global-separation-calibration.md",
    "docs/decisions/ADR-0458-source-seal-the-compiled-global-separation-calibration.md",
    "docs/decisions/ADR-0459-retain-the-unjournaled-absolute-git-infrastructure-rejection.md",
    "docs/decisions/ADR-0460-preregister-the-absolute-git-compiled-calibration-successor.md",
    "docs/decisions/ADR-0461-source-seal-the-absolute-git-compiled-calibration-successor.md",
    "run_legal_river_quotient_compiled_global_separation_calibration_v2.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v2.py",
    "run_legal_river_quotient_compiled_global_separation_calibration.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration.py",
    "src/pontius/legal_river_quotient_base_provenance.py",
    "src/pontius/legal_river_quotient_global_separation_topologies.py",
    "src/pontius/legal_river_quotient_selective_certified_separation.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_runner.py",
    "src/pontius/durable_evidence_journal.py",
    "artifacts/work_preflight/.gitattributes",
)


_PARENT_BINDINGS = (
    "RESULT_RELATIVE_PATH",
    "RESULT_PATH",
    "PROTOCOL_SHA256",
    "CAMPAIGN_SHA256",
    "PREREGISTRATION_COMMIT",
    "DEPENDENCY_RELATIVE_PATHS",
    "verify_independent_contract",
)
_LOCK = RLock()


@contextmanager
def _configured_parent_reader() -> Iterator[object]:
    with _LOCK:
        original = {name: getattr(_parent, name) for name in _PARENT_BINDINGS}
        inherited_verify = _parent.verify_independent_contract

        def verify_independent_contract() -> None:
            fresh_result = _parent.RESULT_RELATIVE_PATH
            _parent.RESULT_RELATIVE_PATH = PARENT_RESULT_RELATIVE_PATH
            try:
                inherited_verify()
            finally:
                _parent.RESULT_RELATIVE_PATH = fresh_result

        replacements = {
            "RESULT_RELATIVE_PATH": RESULT_RELATIVE_PATH,
            "RESULT_PATH": RESULT_PATH,
            "PROTOCOL_SHA256": PROTOCOL_SHA256,
            "CAMPAIGN_SHA256": CAMPAIGN_SHA256,
            "PREREGISTRATION_COMMIT": PREREGISTRATION_COMMIT,
            "DEPENDENCY_RELATIVE_PATHS": DEPENDENCY_RELATIVE_PATHS,
            "verify_independent_contract": verify_independent_contract,
        }
        for name, value in replacements.items():
            setattr(_parent, name, value)
        try:
            yield _parent
        finally:
            for name, value in original.items():
                setattr(_parent, name, value)


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _validate_recovery_header(raw: bytes) -> None:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.is_complete or not recovery.records:
        raise ValueError("absolute-Git journal is incomplete")
    first = recovery.records[0]
    if first.body.kind is not JournalRecordKind.HEADER:
        raise ValueError("absolute-Git journal omits header")
    header = first.body.payload
    identity = _mapping(header.get("absolute_git_recovery"), label="recovery identity")
    if (
        identity.get("schema_version") != "pontius-adr0460-absolute-git-recovery-v1"
        or identity.get("config_relative_path") != RECOVERY_CONFIG_RELATIVE_PATH
        or identity.get("config_canonical_lf_sha256") != RECOVERY_CONFIG_SHA256
        or identity.get("scientific_source_canonical_lf_sha256")
        != "d38e96fd445f01a70113a8598094d0449a18271fa4d6ce992c781f0253ae821e"
        or identity.get("literal_cuda_source_sha256")
        != "4f626802bd792788dff74c58adb90e7e30876e0c8f22d7fcb79de0c90334f8f7"
    ):
        raise ValueError("absolute-Git recovery identity differs")
    git = _mapping(identity.get("absolute_git"), label="absolute Git identity")
    if (
        git.get("path") != str(GIT_PATH)
        or git.get("bytes") != GIT_BYTES
        or git.get("sha256") != GIT_SHA256
        or git.get("provenance") != "ADR-0443 host-file manifest"
    ):
        raise ValueError("absolute-Git header executable differs")
    predecessor = _mapping(identity.get("predecessor"), label="predecessor")
    if predecessor != {
        "source_seal_commit": "88148da07324c13b79c72ea494b14167a975c001",
        "result_relative_path": (
            "artifacts/work_preflight/"
            "legal_river_quotient_compiled_global_separation_calibration_v1.jsonl"
        ),
        "result_exists": False,
        "terminal": "unjournaled_preowner_infrastructure_rejection",
        "exception_type": "FileNotFoundError",
        "exception_message": "[WinError 2] The system cannot find the file specified",
        "invocation_count": 1,
    }:
        raise ValueError("absolute-Git predecessor evidence differs")
    predecessor_path = ROOT / str(predecessor["result_relative_path"])
    if predecessor_path.exists():
        raise ValueError("consumed predecessor result unexpectedly exists")


def assess_calibration_bytes(raw: bytes):
    _validate_recovery_header(raw)
    with _configured_parent_reader() as reader:
        return reader.assess_calibration_bytes(raw)


def assess_calibration_file(path: Path = RESULT_PATH):
    if not isinstance(path, Path):
        raise TypeError("absolute-Git result path must be a Path")
    return assess_calibration_bytes(path.read_bytes())


__all__ = ["assess_calibration_bytes", "assess_calibration_file"]
