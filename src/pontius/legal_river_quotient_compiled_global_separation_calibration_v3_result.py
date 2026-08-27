"""Independent lifecycle reader for the ADR-0463 launch-arity successor."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from threading import RLock

from . import legal_river_quotient_compiled_global_separation_calibration_v2_result as _parent
from .durable_evidence_journal import JournalRecordKind, recover_journal_bytes


ROOT = Path(__file__).parents[2]
RECOVERY_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v4-launch-abi-completeness.json"
)
RECOVERY_CONFIG_SHA256 = (
    "58668f557bcc1f3420454124b8d930d7e59a9d1a870003a8093776f1175d9a92"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v3.jsonl"
)
RESULT_PATH = ROOT / RESULT_RELATIVE_PATH
CONSUMED_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v2.jsonl"
)
CONSUMED_RESULT_PATH = ROOT / CONSUMED_RESULT_RELATIVE_PATH
CONSUMED_RESULT_BYTES = 3_299_268
CONSUMED_RESULT_SHA256 = (
    "67ac14d408fe8c4299ee603ec1d8c454975094507d4ac28cda73001a42feb90d"
)
PREREGISTRATION_COMMIT = "e0a53d161fe27b95556ff73844253b352d223cfd"
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0463-launch-abi-compiled-separation-owner-v3"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0463-launch-abi-compiled-separation-campaign-v3"
).hexdigest()
SCIENTIFIC_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration_v3"
)
PARENT_SCIENTIFIC_SOURCE_SHA256 = (
    "d38e96fd445f01a70113a8598094d0449a18271fa4d6ce992c781f0253ae821e"
)
EFFECTIVE_SCIENTIFIC_SOURCE_SHA256 = (
    "7c63e2706f5aa28c37f25bfa58d09f03d2f5fe26f3a3312fe2baf7b849cec3fc"
)
CUDA_SOURCE_SHA256 = (
    "4f626802bd792788dff74c58adb90e7e30876e0c8f22d7fcb79de0c90334f8f7"
)
KERNEL_SIGNATURE_MANIFEST_SHA256 = (
    "8c25833e55a75a76a226251166a564b6ab8e52efdbb543958c33b93e8b7c63f8"
)

DEPENDENCY_RELATIVE_PATHS = (
    RECOVERY_CONFIG_RELATIVE_PATH,
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v3-launch-abi.json",
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v2-absolute-git.json",
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v1.json",
    "docs/decisions/ADR-0457-preregister-the-compiled-global-separation-calibration.md",
    "docs/decisions/ADR-0458-source-seal-the-compiled-global-separation-calibration.md",
    "docs/decisions/ADR-0459-retain-the-unjournaled-absolute-git-infrastructure-rejection.md",
    "docs/decisions/ADR-0460-preregister-the-absolute-git-compiled-calibration-successor.md",
    "docs/decisions/ADR-0461-source-seal-the-absolute-git-compiled-calibration-successor.md",
    "docs/decisions/ADR-0462-retain-the-timed-rrns-direct-launch-arity-rejection.md",
    "docs/decisions/ADR-0463-preregister-the-kernel-launch-arity-successor.md",
    "docs/decisions/ADR-0464-correct-the-launch-arity-successor-before-source-seal.md",
    "docs/decisions/ADR-0465-source-seal-the-kernel-launch-arity-successor.md",
    "run_legal_river_quotient_compiled_global_separation_calibration_v3.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v3.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_outcome.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v2_outcome.py",
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
    "PREREGISTRATION_COMMIT",
    "PROTOCOL_SHA256",
    "CAMPAIGN_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
)
_LOCK = RLock()


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _validate_launch_abi_header(raw: bytes) -> None:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.is_complete or not recovery.records:
        raise ValueError("launch-arity journal is incomplete")
    first = recovery.records[0]
    if first.body.kind is not JournalRecordKind.HEADER:
        raise ValueError("launch-arity journal omits header")
    header = first.body.payload
    if header.get("scientific_module") != SCIENTIFIC_MODULE:
        raise ValueError("launch-arity scientific module differs")
    identity = _mapping(header.get("launch_abi_recovery"), label="launch ABI identity")
    if (
        identity.get("schema_version")
        != "pontius-adr0464-launch-abi-completeness-recovery-v1"
        or identity.get("config_relative_path") != RECOVERY_CONFIG_RELATIVE_PATH
        or identity.get("config_canonical_lf_sha256") != RECOVERY_CONFIG_SHA256
        or identity.get("parent_scientific_source_canonical_lf_sha256")
        != PARENT_SCIENTIFIC_SOURCE_SHA256
        or identity.get("effective_scientific_source_sha256")
        != EFFECTIVE_SCIENTIFIC_SOURCE_SHA256
        or identity.get("literal_cuda_source_sha256") != CUDA_SOURCE_SHA256
        or identity.get("only_scientific_delta")
        != (
            "timed RRNS direct source_count insertion, selected-leaf obsolete "
            "scan_count removal, and declaration-derived central launch-arity guard"
        )
    ):
        raise ValueError("launch-arity recovery identity differs")
    predecessor = _mapping(identity.get("predecessor"), label="predecessor")
    if predecessor != {
        "source_seal_commit": "08bb6857f47f9669b8f531c65079d4decd52a573",
        "result_relative_path": CONSUMED_RESULT_RELATIVE_PATH,
        "result_bytes": CONSUMED_RESULT_BYTES,
        "result_raw_sha256": CONSUMED_RESULT_SHA256,
        "terminal": "compiled_reduced_calibration_rejected",
        "scientific_call_count": 1,
        "measured_call_count": 0,
        "failure_code": "CUDA_ERROR_INVALID_VALUE",
        "invocation_count": 1,
    }:
        raise ValueError("launch-arity predecessor differs")
    if (
        not CONSUMED_RESULT_PATH.is_file()
        or CONSUMED_RESULT_PATH.stat().st_size != CONSUMED_RESULT_BYTES
        or sha256(CONSUMED_RESULT_PATH.read_bytes()).hexdigest()
        != CONSUMED_RESULT_SHA256
    ):
        raise ValueError("launch-arity predecessor raw identity differs")
    contract = _mapping(identity.get("launch_arity_contract"), label="arity contract")
    signatures = _mapping(contract.get("kernel_signatures"), label="kernel signatures")
    if (
        contract.get("schema_version")
        != "pontius-adr0463-kernel-launch-arity-contract-v1"
        or contract.get("kernel_count") != 28
        or len(signatures) != 28
        or contract.get("manifest_sha256") != KERNEL_SIGNATURE_MANIFEST_SHA256
        or contract.get("central_pre_driver_guard") is not True
        or contract.get("timed_direct_source_count_expression")
        != "np.uint64(scan_count)"
        or contract.get("selected_leaf_extraneous_scan_count_removed") is not True
        or contract.get("complete_differential_source_count_expression")
        != "np.uint64(prepared.source_rows)"
        or signatures.get("direct_prices_rrns_batch")
        != [
            "h",
            "base",
            "prices",
            "cards",
            "source_count",
            "moduli",
            "channels",
            "channel_count",
            "status",
        ]
    ):
        raise ValueError("launch-arity contract differs")


@contextmanager
def _configured_parent_reader() -> Iterator[object]:
    with _LOCK:
        original = {name: getattr(_parent, name) for name in _PARENT_BINDINGS}
        replacements = {
            "RESULT_RELATIVE_PATH": RESULT_RELATIVE_PATH,
            "RESULT_PATH": RESULT_PATH,
            "PREREGISTRATION_COMMIT": PREREGISTRATION_COMMIT,
            "PROTOCOL_SHA256": PROTOCOL_SHA256,
            "CAMPAIGN_SHA256": CAMPAIGN_SHA256,
            "DEPENDENCY_RELATIVE_PATHS": DEPENDENCY_RELATIVE_PATHS,
        }
        for name, value in replacements.items():
            setattr(_parent, name, value)
        try:
            yield _parent
        finally:
            for name, value in original.items():
                setattr(_parent, name, value)


def assess_calibration_bytes(raw: bytes):
    _validate_launch_abi_header(raw)
    with _configured_parent_reader() as reader:
        return reader.assess_calibration_bytes(raw)


def assess_calibration_file(path: Path = RESULT_PATH):
    if not isinstance(path, Path):
        raise TypeError("launch-arity result path must be a Path")
    return assess_calibration_bytes(path.read_bytes())


__all__ = [
    "CAMPAIGN_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "PROTOCOL_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "assess_calibration_bytes",
    "assess_calibration_file",
]
