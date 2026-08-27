"""Independent reader for the ADR-0470 retained-v5-attempt recovery successor."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
from threading import RLock

from . import legal_river_quotient_compiled_global_separation_calibration_v4_result as _v4
from .durable_evidence_journal import JournalRecordKind, canonical_journal_json_bytes


ROOT = Path(__file__).parents[2]
HEADER_CONTRACT_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v7-inherited-header-contract.json"
)
HEADER_CONTRACT_CONFIG_SHA256 = (
    "2aa2eb3068723c2c3cb5ed13ed7e340f1a51101bfc64ecacd5e01a8486712d03"
)
DEFERRED_IMPORT_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v5-deferred-science-import.json"
)
DEFERRED_IMPORT_CONFIG_SHA256 = (
    "f61d236530e8add3e5eb063f9f3afa641e205defd9cdefaa56fd9a2de53c8d1f"
)
ABSOLUTE_GIT_RECOVERY_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v2-absolute-git.json"
)
ABSOLUTE_GIT_RECOVERY_CONFIG_SHA256 = (
    "e9242618e674c74804990c17965de731da15a70adcd0c0094b650d7332313f4e"
)
RECOVERY_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v8-"
    "v5-attempt-recovery.json"
)
RECOVERY_CONFIG_SHA256 = (
    "5fab5270880625e8f909fd7f1a334f6fa38471ca34bd453de47d93fbfd2413ff"
)
AUTHORIZATION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v9-"
    "corrected-invocation-authorization.json"
)
AUTHORIZATION_CONFIG_PATH = ROOT / AUTHORIZATION_CONFIG_RELATIVE_PATH
AUTHORIZATION_SCHEMA_VERSION = "pontius-adr0472-one-commit-v6-authorization-v1"
AUTHORIZATION_COMMIT_PATHS = (
    "ARCHITECTURE.md",
    "RISK_REGISTER.md",
    "ROADMAP.md",
    "STATUS.md",
    "docs/decisions/ADR-0472-authorize-one-v6-retained-attempt-calibration-invocation.md",
    AUTHORIZATION_CONFIG_RELATIVE_PATH,
)
PREREGISTRATION_COMMIT = "5c0c9a401e5f2ebf59296832d954d0075c4d4624"
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v6.jsonl"
)
RESULT_PATH = ROOT / RESULT_RELATIVE_PATH
ATTEMPT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v6.attempt.json"
)
ATTEMPT_PATH = ROOT / ATTEMPT_RELATIVE_PATH
LAUNCH_PENDING_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v6.launch-pending.json"
)
LAUNCH_CONSUMED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v6.launch-consumed.json"
)
LAUNCH_ABORTED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v6.launch-aborted.json"
)
LAUNCH_PENDING_PATH = ROOT / LAUNCH_PENDING_RELATIVE_PATH
LAUNCH_CONSUMED_PATH = ROOT / LAUNCH_CONSUMED_RELATIVE_PATH
LAUNCH_ABORTED_PATH = ROOT / LAUNCH_ABORTED_RELATIVE_PATH
V4_RESULT_PATH = ROOT / (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.jsonl"
)
V4_ATTEMPT_PATH = ROOT / (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.attempt.json"
)
V4_LAUNCH_PATHS = (
    ROOT
    / (
        "artifacts/work_preflight/"
        "legal_river_quotient_compiled_global_separation_calibration_v4."
        "launch-pending.json"
    ),
    ROOT
    / (
        "artifacts/work_preflight/"
        "legal_river_quotient_compiled_global_separation_calibration_v4."
        "launch-consumed.json"
    ),
    ROOT
    / (
        "artifacts/work_preflight/"
        "legal_river_quotient_compiled_global_separation_calibration_v4."
        "launch-aborted.json"
    ),
)
V5_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5.jsonl"
)
V5_RESULT_PATH = ROOT / V5_RESULT_RELATIVE_PATH
V5_ATTEMPT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5.attempt.json"
)
V5_ATTEMPT_PATH = ROOT / V5_ATTEMPT_RELATIVE_PATH
V5_ATTEMPT_BYTES = 606
V5_ATTEMPT_SHA256 = (
    "104820d0c67391365d18fb76ca72c704e40e467e2993a96c618d4bf91155600d"
)
V5_LAUNCH_RELATIVE_PATHS = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5.launch-pending.json",
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5.launch-consumed.json",
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5.launch-aborted.json",
)
V5_LAUNCH_PATHS = tuple(ROOT / path for path in V5_LAUNCH_RELATIVE_PATHS)
V5_AUTHORIZATION_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v8-"
    "corrected-invocation-authorization.json"
)
V5_AUTHORIZATION_PATH = ROOT / V5_AUTHORIZATION_RELATIVE_PATH
PROTOCOL_SHA256 = "ffb1f1831bd31ec61b0bedefa9a5544a02e02e1e6d3512e65ff7824988696911"
CAMPAIGN_SHA256 = "ae05bb948abe57c0a3b4b5fcd17cb04555db6a549f8a1d59c192e87ae9c75e3c"
ATTEMPT_SCHEMA_VERSION = "pontius-adr0470-public-attempt-v6-v1"
LAUNCH_SCHEMA_VERSION = "pontius-adr0471-one-use-child-launch-v6-v1"
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration_v6_runner"
)
SCIENTIFIC_MODULE = _v4.SCIENTIFIC_MODULE
PARENT_SCIENTIFIC_SOURCE_SHA256 = _v4.PARENT_SCIENTIFIC_SOURCE_SHA256
EFFECTIVE_SCIENTIFIC_SOURCE_SHA256 = _v4.EFFECTIVE_SCIENTIFIC_SOURCE_SHA256
CUDA_SOURCE_SHA256 = _v4.CUDA_SOURCE_SHA256
KERNEL_SIGNATURE_MANIFEST_SHA256 = _v4.KERNEL_SIGNATURE_MANIFEST_SHA256
GIT_PATH = Path(r"C:\Program Files\Git\cmd\git.exe")
GIT_BYTES = 46_920
GIT_SHA256 = "7b7971dd13f0c3a284e538601f2f9770b3a87dfaccb5fb52d68141c67ed22364"
SCIENTIFIC_CONFIG_SHA256 = (
    "a9a0961656c66d70d145c9f5434460826f3c4972b7b1a18da74b0886a14e18bf"
)
ABSOLUTE_GIT_PREDECESSOR_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v1.jsonl"
)
ABSOLUTE_GIT_PREDECESSOR_RESULT_PATH = (
    ROOT / ABSOLUTE_GIT_PREDECESSOR_RESULT_RELATIVE_PATH
)

_REJECTED_CLAIMS = dict(_v4._REJECTED_CLAIMS)
_BASE_READER = _v4._parent
DEPENDENCY_RELATIVE_PATHS = (
    *_v4.DEPENDENCY_RELATIVE_PATHS,
    HEADER_CONTRACT_CONFIG_RELATIVE_PATH,
    RECOVERY_CONFIG_RELATIVE_PATH,
    V5_ATTEMPT_RELATIVE_PATH,
    "docs/decisions/ADR-0469-retain-the-deferred-import-authorization-gate-rejection.md",
    "docs/decisions/ADR-0470-retain-the-accidental-v5-preauthorization-attempt.md",
    "docs/decisions/ADR-0471-source-seal-the-retained-attempt-successor.md",
    "run_legal_river_quotient_compiled_global_separation_calibration_v6.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v6_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v6_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v6.py",
)

_LOCK = RLock()
_INHERITED_ASSESS_BYTES = _v4.assess_calibration_bytes
_INHERITED_ASSESS_FILE = _v4.assess_calibration_file
_INHERITED_VALIDATE_LOCAL_LIFECYCLE = _v4._validate_local_lifecycle
_V4_BINDINGS = (
    "AUTHORIZATION_CONFIG_RELATIVE_PATH",
    "AUTHORIZATION_CONFIG_PATH",
    "AUTHORIZATION_COMMIT_PATHS",
    "PREREGISTRATION_COMMIT",
    "RESULT_RELATIVE_PATH",
    "RESULT_PATH",
    "ATTEMPT_RELATIVE_PATH",
    "ATTEMPT_PATH",
    "LAUNCH_PENDING_RELATIVE_PATH",
    "LAUNCH_CONSUMED_RELATIVE_PATH",
    "LAUNCH_ABORTED_RELATIVE_PATH",
    "LAUNCH_PENDING_PATH",
    "LAUNCH_CONSUMED_PATH",
    "LAUNCH_ABORTED_PATH",
    "PROTOCOL_SHA256",
    "CAMPAIGN_SHA256",
    "LITERAL_WORKER_MODULE",
    "SCIENTIFIC_MODULE",
    "PARENT_SCIENTIFIC_SOURCE_SHA256",
    "EFFECTIVE_SCIENTIFIC_SOURCE_SHA256",
    "CUDA_SOURCE_SHA256",
    "KERNEL_SIGNATURE_MANIFEST_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "_authorization_config",
    "_attempt_bytes",
    "_validate_deferred_header",
)


def _exact_json(observed: object, expected: object) -> bool:
    """Compare parsed JSON without Python's bool/int equality alias."""

    if type(expected) is dict:
        return (
            type(observed) is dict
            and set(observed) == set(expected)
            and all(_exact_json(observed[key], value) for key, value in expected.items())
        )
    if type(expected) is list:
        return (
            type(observed) is list
            and len(observed) == len(expected)
            and all(
                _exact_json(left, right)
                for left, right in zip(observed, expected, strict=True)
            )
        )
    return type(observed) is type(expected) and observed == expected


def _require_exact_json(observed: object, expected: object, *, label: str) -> None:
    if not _exact_json(observed, expected):
        raise ValueError(f"{label} differs")


def _require_exact_int(value: object, *, label: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{label} must be an exact integer")
    return value


def _is_lower_hex(value: object, length: int) -> bool:
    return (
        type(value) is str
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def _canonical_lf(raw: bytes) -> bytes:
    if type(raw) is not bytes:
        raise TypeError("v6 reader canonical input must be bytes")
    output = bytearray()
    previous_was_cr = False
    for value in raw:
        if previous_was_cr:
            if value == 10:
                output.append(10)
                previous_was_cr = False
                continue
            output.append(13)
            previous_was_cr = False
        if value == 13:
            previous_was_cr = True
        else:
            output.append(value)
    if previous_was_cr:
        output.append(13)
    return bytes(output)


def _authorization_config() -> tuple[Mapping[str, object], str]:
    if not _is_regular_non_reparse(AUTHORIZATION_CONFIG_PATH):
        raise FileNotFoundError("v6 reader invocation authorization is absent")
    raw = AUTHORIZATION_CONFIG_PATH.read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_v4._unique_object,
        parse_float=lambda _: (_ for _ in ()).throw(ValueError("float in JSON")),
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("constant in JSON")),
    )
    expected_keys = {
        "schema_version",
        "source_seal_commit",
        "authorization_commit_paths",
    }
    if (
        type(value) is not dict
        or set(value) != expected_keys
        or value.get("schema_version") != AUTHORIZATION_SCHEMA_VERSION
        or not _is_lower_hex(value.get("source_seal_commit"), 40)
        or not _exact_json(
            value.get("authorization_commit_paths"),
            list(AUTHORIZATION_COMMIT_PATHS),
        )
    ):
        raise ValueError("v6 reader invocation authorization fields differ")
    return value, sha256(_canonical_lf(raw)).hexdigest()


def _attempt_bytes() -> bytes:
    return canonical_journal_json_bytes(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "protocol_sha256": PROTOCOL_SHA256,
            "campaign_sha256": CAMPAIGN_SHA256,
            "result_relative_path": RESULT_RELATIVE_PATH,
            "rejected_v3_result_relative_path": _v4.REJECTED_V3_RESULT_RELATIVE_PATH,
            "closed_v4_result_relative_path": (
                "artifacts/work_preflight/"
                "legal_river_quotient_compiled_global_separation_calibration_v4.jsonl"
            ),
            "closed_v5_result_relative_path": V5_RESULT_RELATIVE_PATH,
            "retained_v5_attempt_relative_path": V5_ATTEMPT_RELATIVE_PATH,
            "retained_v5_attempt_bytes": V5_ATTEMPT_BYTES,
            "retained_v5_attempt_raw_sha256": V5_ATTEMPT_SHA256,
        }
    )


def _expected_v5_attempt_bytes() -> bytes:
    return canonical_journal_json_bytes(
        {
            "schema_version": "pontius-adr0469-public-attempt-v5-v1",
            "protocol_sha256": (
                "8ae5b257549a7ffe2807d9cf5f8b54574fa698f13b6b08f79c1a690d53cfc01d"
            ),
            "campaign_sha256": (
                "c3b38c41fa199d0076a75912513fc5eb6b2d5e4dc806e224f861426b9bad6a0d"
            ),
            "result_relative_path": V5_RESULT_RELATIVE_PATH,
            "closed_v4_result_relative_path": (
                "artifacts/work_preflight/"
                "legal_river_quotient_compiled_global_separation_calibration_v4.jsonl"
            ),
            "rejected_v3_result_relative_path": _v4.REJECTED_V3_RESULT_RELATIVE_PATH,
        }
    )


def _is_regular_non_reparse(path: Path) -> bool:
    return (
        path.is_file()
        and not path.is_symlink()
        and not (
            getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
            & stat.FILE_ATTRIBUTE_REPARSE_POINT
        )
    )


def _require_retained_predecessor_state() -> None:
    """Require the exact consumed v5 attempt and every frozen absence."""

    if not _is_regular_non_reparse(V5_ATTEMPT_PATH):
        raise FileNotFoundError("retained v5 attempt is absent or not a regular file")
    raw = V5_ATTEMPT_PATH.read_bytes()
    expected = _expected_v5_attempt_bytes()
    if (
        len(raw) != V5_ATTEMPT_BYTES
        or sha256(raw).hexdigest() != V5_ATTEMPT_SHA256
        or raw != expected
    ):
        raise ValueError("retained v5 attempt bytes differ")
    absent = (
        _v4.REJECTED_V3_RESULT_PATH,
        V4_RESULT_PATH,
        V4_ATTEMPT_PATH,
        *V4_LAUNCH_PATHS,
        V5_RESULT_PATH,
        *V5_LAUNCH_PATHS,
        V5_AUTHORIZATION_PATH,
    )
    if any(os.path.lexists(path) for path in absent):
        raise FileExistsError("closed v3/v4/v5 lifecycle unexpectedly exists")


def _expected_retained_v5_attempt_recovery() -> dict[str, object]:
    return {
        "schema_version": "pontius-adr0470-retained-v5-attempt-recovery-v1",
        "config_relative_path": RECOVERY_CONFIG_RELATIVE_PATH,
        "config_canonical_lf_sha256": RECOVERY_CONFIG_SHA256,
        "retained_v5_attempt": {
            "relative_path": V5_ATTEMPT_RELATIVE_PATH,
            "bytes": V5_ATTEMPT_BYTES,
            "raw_sha256": V5_ATTEMPT_SHA256,
            "regular_file": True,
            "symlink": False,
            "reparse_point": False,
        },
        "closed_predecessors": {
            "rejected_v3_result_relative_path": _v4.REJECTED_V3_RESULT_RELATIVE_PATH,
            "rejected_v3_result_exists": False,
            "v4_result_relative_path": (
                "artifacts/work_preflight/"
                "legal_river_quotient_compiled_global_separation_calibration_v4.jsonl"
            ),
            "v4_lifecycle_absent": True,
            "v5_result_relative_path": V5_RESULT_RELATIVE_PATH,
            "v5_result_exists": False,
            "v5_launch_marker_count": 0,
            "v5_authorization_relative_path": V5_AUTHORIZATION_RELATIVE_PATH,
            "v5_authorization_exists": False,
        },
        "fresh_v6": {
            "result_relative_path": RESULT_RELATIVE_PATH,
            "attempt_relative_path": ATTEMPT_RELATIVE_PATH,
            "launch_pending_relative_path": LAUNCH_PENDING_RELATIVE_PATH,
            "launch_consumed_relative_path": LAUNCH_CONSUMED_RELATIVE_PATH,
            "launch_aborted_relative_path": LAUNCH_ABORTED_RELATIVE_PATH,
            "authorization_config_relative_path": AUTHORIZATION_CONFIG_RELATIVE_PATH,
            "authorization_schema_version": AUTHORIZATION_SCHEMA_VERSION,
        },
    }


def _validate_retained_v5_attempt_recovery(value: object) -> None:
    _require_exact_json(
        value,
        _expected_retained_v5_attempt_recovery(),
        label="v6 retained-v5-attempt recovery identity",
    )
    _require_retained_predecessor_state()


def _expected_absolute_git_recovery() -> dict[str, object]:
    return {
        "schema_version": "pontius-adr0460-absolute-git-recovery-v1",
        "config_relative_path": ABSOLUTE_GIT_RECOVERY_CONFIG_RELATIVE_PATH,
        "config_canonical_lf_sha256": ABSOLUTE_GIT_RECOVERY_CONFIG_SHA256,
        "absolute_git": {
            "path": str(GIT_PATH),
            "bytes": GIT_BYTES,
            "sha256": GIT_SHA256,
            "provenance": "ADR-0443 host-file manifest",
        },
        "predecessor": {
            "source_seal_commit": "88148da07324c13b79c72ea494b14167a975c001",
            "result_relative_path": ABSOLUTE_GIT_PREDECESSOR_RESULT_RELATIVE_PATH,
            "result_exists": False,
            "terminal": "unjournaled_preowner_infrastructure_rejection",
            "exception_type": "FileNotFoundError",
            "exception_message": "[WinError 2] The system cannot find the file specified",
            "invocation_count": 1,
        },
        "scientific_source_canonical_lf_sha256": PARENT_SCIENTIFIC_SOURCE_SHA256,
        "literal_cuda_source_sha256": CUDA_SOURCE_SHA256,
    }


def _validate_absolute_git_recovery(value: object) -> Mapping[str, object]:
    """Validate only the inherited ADR-0460 absolute-Git layer."""

    _require_exact_json(
        value,
        _expected_absolute_git_recovery(),
        label="v6 absolute-Git recovery identity",
    )
    if os.path.lexists(ABSOLUTE_GIT_PREDECESSOR_RESULT_PATH):
        raise ValueError("v6 absolute-Git predecessor result unexpectedly exists")
    assert isinstance(value, Mapping)
    return value


def _validate_deferred_import_recovery(
    value: object,
) -> tuple[Mapping[str, object], Mapping[str, object]]:
    """Validate only the ADR-0466 deferred-import and launch-ABI layer."""

    if type(value) is not dict:
        raise TypeError("v6 launch ABI identity must be an object")
    identity = value
    expected_identity_keys = {
        "schema_version",
        "config_relative_path",
        "config_canonical_lf_sha256",
        "predecessor",
        "rejected_v3",
        "bootstrap_before_science_import",
        "module_aliasing_used",
        "executed_science_identity",
        "launch_arity_contract",
    }
    if (
        set(identity) != expected_identity_keys
        or identity.get("schema_version")
        != "pontius-adr0466-deferred-science-import-recovery-v1"
        or identity.get("config_relative_path")
        != DEFERRED_IMPORT_CONFIG_RELATIVE_PATH
        or identity.get("config_canonical_lf_sha256")
        != DEFERRED_IMPORT_CONFIG_SHA256
        or identity.get("bootstrap_before_science_import") is not True
        or identity.get("module_aliasing_used") is not False
    ):
        raise ValueError("v6 deferred-import recovery identity differs")
    _require_exact_json(
        identity.get("predecessor"),
        {
            "source_seal_commit": "08bb6857f47f9669b8f531c65079d4decd52a573",
            "result_relative_path": _v4.CONSUMED_RESULT_RELATIVE_PATH,
            "result_bytes": _v4.CONSUMED_RESULT_BYTES,
            "result_raw_sha256": _v4.CONSUMED_RESULT_SHA256,
            "terminal": "compiled_reduced_calibration_rejected",
            "scientific_call_count": 1,
            "measured_call_count": 0,
            "failure_code": "CUDA_ERROR_INVALID_VALUE",
            "invocation_count": 1,
        },
        label="v6 deferred-import predecessor",
    )
    if (
        not _v4.CONSUMED_RESULT_PATH.is_file()
        or _v4.CONSUMED_RESULT_PATH.stat().st_size != _v4.CONSUMED_RESULT_BYTES
        or sha256(_v4.CONSUMED_RESULT_PATH.read_bytes()).hexdigest()
        != _v4.CONSUMED_RESULT_SHA256
    ):
        raise ValueError("v6 deferred-import predecessor bytes differ")
    _require_exact_json(
        identity.get("rejected_v3"),
        {
            "source_seal_commit": _v4.REJECTED_V3_SOURCE_SEAL_COMMIT,
            "result_relative_path": _v4.REJECTED_V3_RESULT_RELATIVE_PATH,
            "result_exists": False,
            "public_invocation_count": 0,
        },
        label="v6 rejected-v3 identity",
    )
    if os.path.lexists(_v4.REJECTED_V3_RESULT_PATH):
        raise ValueError("v6 rejected-v3 result unexpectedly exists")
    if not _exact_json(
        identity.get("executed_science_identity"),
        _v4._expected_executed_science_identity(),
    ):
        raise ValueError("v6 header science identity differs")
    contract = identity.get("launch_arity_contract")
    if type(contract) is not dict:
        raise TypeError("v6 launch contract must be an object")
    signatures = contract.get("kernel_signatures")
    if type(signatures) is not dict:
        raise TypeError("v6 kernel signatures must be an object")
    recomputed = _v4._manifest_sha256(signatures)
    if (
        set(contract)
        != {
            "schema_version",
            "parent_scientific_source_canonical_lf_sha256",
            "effective_scientific_source_sha256",
            "literal_cuda_source_sha256",
            "kernel_count",
            "kernel_signatures",
            "manifest_sha256",
            "timed_direct_source_count_expression",
            "selected_leaf_extraneous_scan_count_removed",
            "complete_differential_source_count_expression",
            "central_pre_driver_guard",
        }
        or contract.get("schema_version")
        != "pontius-adr0463-kernel-launch-arity-contract-v1"
        or contract.get("parent_scientific_source_canonical_lf_sha256")
        != PARENT_SCIENTIFIC_SOURCE_SHA256
        or type(contract.get("kernel_count")) is not int
        or contract.get("kernel_count") != 28
        or len(signatures) != 28
        or recomputed != KERNEL_SIGNATURE_MANIFEST_SHA256
        or contract.get("manifest_sha256") != recomputed
        or contract.get("effective_scientific_source_sha256")
        != EFFECTIVE_SCIENTIFIC_SOURCE_SHA256
        or contract.get("literal_cuda_source_sha256") != CUDA_SOURCE_SHA256
        or contract.get("timed_direct_source_count_expression")
        != "np.uint64(scan_count)"
        or contract.get("selected_leaf_extraneous_scan_count_removed") is not True
        or contract.get("complete_differential_source_count_expression")
        != "np.uint64(prepared.source_rows)"
        or contract.get("central_pre_driver_guard") is not True
    ):
        raise ValueError("v6 deferred-import launch contract differs")
    return identity, contract


def _validate_deferred_header(raw: bytes) -> None:
    recovery = _v4.recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.is_complete or not recovery.records:
        raise ValueError("v6 deferred-import journal is incomplete")
    _v4._validate_semantic_identities(recovery)
    first = recovery.records[0]
    if first.body.kind is not JournalRecordKind.HEADER:
        raise ValueError("v6 deferred-import journal omits header")
    header = first.body.payload
    expected_header_keys = {
        "schema_version",
        "protocol_sha256",
        "campaign_sha256",
        "config_sha256",
        "preregistration_commit",
        "source_seal_git",
        "dependency_hashes",
        "result_relative_path",
        "literal_worker_module",
        "scientific_module",
        "calls_under_one_public_owner",
        "claims",
        "absolute_git_recovery",
        "launch_abi_recovery",
        "deferred_science_import_authorization",
        "retained_v5_attempt_recovery",
    }
    if (
        type(header) is not dict
        or set(header) != expected_header_keys
        or header.get("schema_version") != "pontius-adr0457-owner-header-v1"
        or header.get("protocol_sha256") != PROTOCOL_SHA256
        or header.get("campaign_sha256") != CAMPAIGN_SHA256
        or header.get("config_sha256") != SCIENTIFIC_CONFIG_SHA256
        or header.get("preregistration_commit") != PREREGISTRATION_COMMIT
        or header.get("result_relative_path") != RESULT_RELATIVE_PATH
        or header.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or header.get("scientific_module") != SCIENTIFIC_MODULE
        or type(header.get("calls_under_one_public_owner")) is not int
        or header.get("calls_under_one_public_owner") != 2_880
    ):
        raise ValueError("v6 deferred-import header domain differs")
    _require_exact_json(
        header.get("claims"), _REJECTED_CLAIMS, label="v6 header claims"
    )
    _validate_retained_v5_attempt_recovery(
        header.get("retained_v5_attempt_recovery")
    )

    absolute_recovery = _validate_absolute_git_recovery(
        header.get("absolute_git_recovery")
    )
    identity, contract = _validate_deferred_import_recovery(
        header.get("launch_abi_recovery")
    )
    if (
        absolute_recovery["scientific_source_canonical_lf_sha256"]
        != contract["parent_scientific_source_canonical_lf_sha256"]
        or absolute_recovery["literal_cuda_source_sha256"]
        != contract["literal_cuda_source_sha256"]
    ):
        raise ValueError("v6 inherited science cross-identity differs")

    source_git = header.get("source_seal_git")
    dependency_hashes = header.get("dependency_hashes")
    stored_auth = header.get("deferred_science_import_authorization")
    if type(source_git) is not dict or type(dependency_hashes) is not dict:
        raise TypeError("v6 source Git or dependency hashes must be an object")
    if (
        set(dependency_hashes) != set(DEPENDENCY_RELATIVE_PATHS)
        or any(not _is_lower_hex(value, 64) for value in dependency_hashes.values())
    ):
        raise ValueError("v6 dependency-hash domain differs")
    expected_config_hashes = {
        ABSOLUTE_GIT_RECOVERY_CONFIG_RELATIVE_PATH: (
            ABSOLUTE_GIT_RECOVERY_CONFIG_SHA256
        ),
        DEFERRED_IMPORT_CONFIG_RELATIVE_PATH: DEFERRED_IMPORT_CONFIG_SHA256,
        HEADER_CONTRACT_CONFIG_RELATIVE_PATH: HEADER_CONTRACT_CONFIG_SHA256,
        RECOVERY_CONFIG_RELATIVE_PATH: RECOVERY_CONFIG_SHA256,
    }
    if any(
        dependency_hashes.get(path) != digest
        for path, digest in expected_config_hashes.items()
    ):
        raise ValueError("v6 recovery config dependency cross-identity differs")
    config, config_hash = _authorization_config()
    authorization_commit = source_git.get("commit")
    expected_auth = {
        "schema_version": AUTHORIZATION_SCHEMA_VERSION,
        "config_relative_path": AUTHORIZATION_CONFIG_RELATIVE_PATH,
        "config_canonical_lf_sha256": config_hash,
        "source_seal_commit": config["source_seal_commit"],
        "authorization_commit": authorization_commit,
        "authorization_commit_paths": list(AUTHORIZATION_COMMIT_PATHS),
        "single_generation_only": True,
    }
    _require_exact_json(
        stored_auth, expected_auth, label="v6 deferred-import authorization"
    )
    launch_claim = source_git.get("launch_claim")
    if type(launch_claim) is not dict or not _is_lower_hex(
        launch_claim.get("token_sha256"), 64
    ):
        raise ValueError("v6 launch claim token differs")
    expected_launch = {
        "schema_version": LAUNCH_SCHEMA_VERSION,
        "token_sha256": launch_claim["token_sha256"],
        "authorization_commit": authorization_commit,
        "result_relative_path": RESULT_RELATIVE_PATH,
    }
    _require_exact_json(launch_claim, expected_launch, label="v6 launch claim")
    expected_source_git = {
        "commit": authorization_commit,
        "dirty": False,
        "strict_status": True,
        "authorization": expected_auth,
        "attempt_marker_sha256": sha256(_attempt_bytes()).hexdigest(),
        "launch_claim": expected_launch,
        "launch_marker_sha256": sha256(
            _v4._launch_marker_bytes(expected_launch, state="pending")
        ).hexdigest(),
        "authorized_dependency_hashes": dependency_hashes,
    }
    _require_exact_json(source_git, expected_source_git, label="v6 source-seal Git")
    _validate_v6_authorization_git(
        authorization_commit,
        config.get("source_seal_commit"),
        dependency_hashes,
        config_hash,
    )
    _require_retained_predecessor_state()


def _validate_record_type_contract(raw: bytes) -> None:
    """Reject equality-preserving JSON type aliases outside the header."""

    recovery = _v4.recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.is_complete or not recovery.records:
        raise ValueError("v6 typed journal is incomplete")
    for record in recovery.records:
        payload = record.body.payload
        if type(payload) is not dict:
            raise TypeError("v6 record payload must be an object")
        if record.body.kind is JournalRecordKind.HEADER:
            continue
        if record.body.kind is JournalRecordKind.OBSERVATION:
            if (
                payload.get("schema_version")
                != "pontius-adr0457-owner-observation-v1"
                or type(payload.get("event_index")) is not int
                or type(payload.get("kind")) is not str
                or type(payload.get("event")) is not dict
                or not _is_lower_hex(payload.get("source_commit"), 40)
            ):
                raise ValueError("v6 observation wrapper types differ")
            kind = payload["kind"]
            event = payload["event"]
            _validate_inherited_success_event_types(kind, event)
            if kind == "bootstrap_handshake":
                _require_exact_json(
                    event,
                    {
                        "schema_version": "pontius-adr0457-bootstrap-v1",
                        "literal_worker_module": LITERAL_WORKER_MODULE,
                        "python_no_bytecode": True,
                        "child_runtime_environment": _v4._expected_child_runtime(),
                        "cupy_loaded": False,
                        "scientific_source_loaded": False,
                        "parent_journal_present": True,
                    },
                    label="v6 bootstrap type contract",
                )
            elif kind == "terminal_evidence":
                passed = event.get("passed")
                if type(passed) is not bool:
                    raise ValueError("v6 terminal-evidence pass type differs")
                for name in (
                    "science_import_completed",
                    "science_identity_validated",
                    "science_execution_started",
                ):
                    if type(event.get(name)) is not bool:
                        raise ValueError(f"v6 terminal-evidence {name} type differs")
                for name in (
                    "laboratory_elapsed_ns",
                    "scientific_call_count",
                    "warmup_call_count",
                    "measured_call_count",
                    "differential_count",
                    "complete_positive_differential_count",
                ):
                    value = event.get(name)
                    if value is not None and type(value) is not int:
                        raise ValueError(f"v6 terminal-evidence {name} type differs")
                executed = event.get("executed_science_identity")
                if event.get("science_execution_started") is True:
                    _require_exact_json(
                        executed,
                        _v4._expected_executed_science_identity(),
                        label="v6 terminal executed-science identity",
                    )
                elif executed is not None:
                    raise ValueError("v6 pre-import terminal science identity differs")
                claims = event.get("claims")
                if passed:
                    if type(claims) is not dict or type(
                        claims.get("material_zeta_speed_claim")
                    ) is not bool:
                        raise ValueError("v6 successful terminal claims type differs")
                    expected_claims = _v4._expected_success_claims(
                        claims["material_zeta_speed_claim"]
                    )
                else:
                    expected_claims = _REJECTED_CLAIMS
                _require_exact_json(
                    claims, expected_claims, label="v6 terminal-evidence claims"
                )
            continue
        if record.body.kind is JournalRecordKind.TERMINAL:
            passed = payload.get("passed")
            if type(passed) is not bool or type(payload.get("event_count")) is not int:
                raise ValueError("v6 owner terminal Boolean/integer types differ")
            for name in (
                "public_elapsed_ns",
                "public_wall_ns",
                "laboratory_elapsed_ns",
                "laboratory_wall_ns",
                "outside_laboratory_elapsed_ns",
                "outside_laboratory_wall_ns",
            ):
                value = payload.get(name)
                if value is not None and type(value) is not int:
                    raise ValueError(f"v6 owner terminal {name} type differs")
            _require_exact_json(
                payload.get("claims"),
                _v4._expected_owner_success_claims() if passed else _REJECTED_CLAIMS,
                label="v6 owner terminal claims",
            )


def _validate_inherited_success_event_types(
    kind: str, event: Mapping[str, object]
) -> None:
    """Type-seal fixed scientific fields before inherited value validation."""

    if kind == "arithmetic_admission":
        _require_exact_json(
            event,
            _BASE_READER._expected_arithmetic_admission(),
            label="v6 arithmetic-admission type contract",
        )
        return
    if kind == "source_contract":
        _require_exact_int(
            event.get("full_codeword_reconstruction_call_sites"),
            label="v6 reconstruction call sites",
        )
        _require_exact_int(
            event.get("batched_admission_consumer_sites"),
            label="v6 admission consumer sites",
        )
        _require_exact_json(
            event.get("timed_host_surface"),
            {
                "schema_version": "pontius-adr0458-timed-host-surface-v1",
                "phase_callbacks": list(_BASE_READER.PHASE_CALLBACKS),
                "host_prefix_authority_calls": 0,
                "host_unbounded_scientific_comparisons": 0,
                "nonterminal_device_to_host_scientific_transfers": 0,
                "passed": True,
            },
            label="v6 timed-host type contract",
        )
        return
    if kind == "compile_resource_evidence":
        for name in (
            "register_ceiling",
            "spill_store_ceiling_bytes",
            "spill_load_ceiling_bytes",
        ):
            _require_exact_int(event.get(name), label=f"v6 compile resource {name}")
        return
    if kind == "module_load_and_runtime":
        _require_exact_int(event.get("kernel_count"), label="v6 module kernel count")
        return
    if kind == "device_memory_admission":
        _require_exact_int(
            event.get("physical_RRNS_table_arena_allocations"),
            label="v6 physical RRNS arena count",
        )
        _require_exact_int(
            event.get("RRNS_table_arena_channel_capacity"),
            label="v6 RRNS channel capacity",
        )
        _require_exact_json(
            event.get("campaign"),
            _BASE_READER._expected_liveness(
                _BASE_READER._campaign_memory_peak()
            ),
            label="v6 campaign liveness type contract",
        )
        return
    if kind == "device_domain_prepared":
        cards = _require_exact_int(event.get("cards"), label="v6 domain cards")
        _require_exact_json(
            event.get("memory"),
            {
                "shared_five_channel_replay": _BASE_READER._expected_liveness(
                    _BASE_READER._domain_memory_peak(cards)
                )
            },
            label="v6 domain liveness type contract",
        )
        return
    if kind == "calibration_cell":
        _require_exact_int(event.get("pass_index"), label="v6 cell pass index")
        partition = event.get("phase_partition")
        terminal = event.get("terminal")
        differential = event.get("differential")
        if type(partition) is not dict or type(terminal) is not dict:
            raise ValueError("v6 cell partition or terminal must be an object")
        if type(differential) is not dict:
            raise ValueError("v6 cell differential must be an object")
        _require_exact_int(
            partition.get("primitive_total_ns"),
            label="v6 cell primitive total",
        )
        for name in (
            "found_positive",
            "globally_closed",
            "prefix_decision_keys",
        ):
            if name in terminal:
                _require_exact_int(
                    terminal[name], label=f"v6 cell terminal {name}"
                )
        complete = differential.get("complete_positive_output")
        if complete is not None:
            if type(complete) is not dict:
                raise ValueError("v6 complete differential must be an object")
            _require_exact_int(
                complete.get("authority_coordinates_checked"),
                label="v6 complete differential coordinate count",
            )
        return
    if kind == "fit_projection":
        fit_rows = event.get("fit_rows")
        primitive_rows = event.get("primitive_rows")
        materiality_rows = event.get("materiality_rows")
        if not all(
            type(rows) is list
            for rows in (fit_rows, primitive_rows, materiality_rows)
        ):
            raise ValueError("v6 fit-projection rows must be lists")
        for row in fit_rows:
            if type(row) is not dict:
                raise ValueError("v6 fit row must be an object")
            for name in ("target_upper_ceiling_ns", "target_work"):
                _require_exact_int(row.get(name), label=f"v6 fit row {name}")
        for row in primitive_rows:
            if type(row) is not dict:
                raise ValueError("v6 primitive row must be an object")
            _require_exact_int(
                row.get("projected_primitive_upper_ns"),
                label="v6 projected primitive upper",
            )
        for row in materiality_rows:
            if type(row) is not dict:
                raise ValueError("v6 materiality row must be an object")
            _require_exact_int(
                row.get("direct_upper_ns"), label="v6 direct materiality upper"
            )
            _require_exact_int(
                row.get("zeta_upper_ns"), label="v6 zeta materiality upper"
            )
            if type(row.get("zeta_at_most_half_direct")) is not bool:
                raise ValueError("v6 materiality conjunct must be a Boolean")


def _replacements() -> dict[str, object]:
    return {
        "AUTHORIZATION_CONFIG_RELATIVE_PATH": AUTHORIZATION_CONFIG_RELATIVE_PATH,
        "AUTHORIZATION_CONFIG_PATH": AUTHORIZATION_CONFIG_PATH,
        "AUTHORIZATION_COMMIT_PATHS": AUTHORIZATION_COMMIT_PATHS,
        "PREREGISTRATION_COMMIT": PREREGISTRATION_COMMIT,
        "RESULT_RELATIVE_PATH": RESULT_RELATIVE_PATH,
        "RESULT_PATH": RESULT_PATH,
        "ATTEMPT_RELATIVE_PATH": ATTEMPT_RELATIVE_PATH,
        "ATTEMPT_PATH": ATTEMPT_PATH,
        "LAUNCH_PENDING_RELATIVE_PATH": LAUNCH_PENDING_RELATIVE_PATH,
        "LAUNCH_CONSUMED_RELATIVE_PATH": LAUNCH_CONSUMED_RELATIVE_PATH,
        "LAUNCH_ABORTED_RELATIVE_PATH": LAUNCH_ABORTED_RELATIVE_PATH,
        "LAUNCH_PENDING_PATH": LAUNCH_PENDING_PATH,
        "LAUNCH_CONSUMED_PATH": LAUNCH_CONSUMED_PATH,
        "LAUNCH_ABORTED_PATH": LAUNCH_ABORTED_PATH,
        "PROTOCOL_SHA256": PROTOCOL_SHA256,
        "CAMPAIGN_SHA256": CAMPAIGN_SHA256,
        "LITERAL_WORKER_MODULE": LITERAL_WORKER_MODULE,
        "SCIENTIFIC_MODULE": SCIENTIFIC_MODULE,
        "PARENT_SCIENTIFIC_SOURCE_SHA256": PARENT_SCIENTIFIC_SOURCE_SHA256,
        "EFFECTIVE_SCIENTIFIC_SOURCE_SHA256": EFFECTIVE_SCIENTIFIC_SOURCE_SHA256,
        "CUDA_SOURCE_SHA256": CUDA_SOURCE_SHA256,
        "KERNEL_SIGNATURE_MANIFEST_SHA256": KERNEL_SIGNATURE_MANIFEST_SHA256,
        "DEPENDENCY_RELATIVE_PATHS": DEPENDENCY_RELATIVE_PATHS,
        "_authorization_config": _authorization_config,
        "_attempt_bytes": _attempt_bytes,
        "_validate_deferred_header": _validate_deferred_header,
    }


@contextmanager
def _configured_v4_reader() -> Iterator[object]:
    with _v4._LOCK, _LOCK:
        original = {name: getattr(_v4, name) for name in _V4_BINDINGS}
        for name, value in _replacements().items():
            setattr(_v4, name, value)
        try:
            yield _v4
        finally:
            for name, value in original.items():
                setattr(_v4, name, value)


def _validate_v6_authorization_git(
    authorization_commit: object,
    source_seal_commit: object,
    dependency_hashes: Mapping[str, object],
    authorization_config_sha256: str,
) -> None:
    """Run the inherited Git proof only under the complete v6 identity."""

    with _configured_v4_reader():
        _v4._validate_authorization_git(
            authorization_commit,
            source_seal_commit,
            dependency_hashes,
        )
        committed = _v4._absolute_git(
            "show",
            f"{authorization_commit}:{AUTHORIZATION_CONFIG_RELATIVE_PATH}",
        )
        if sha256(_canonical_lf(committed)).hexdigest() != authorization_config_sha256:
            raise ValueError("v6 authorization Git blob differs")


def assess_calibration_bytes(raw: bytes):
    _require_retained_predecessor_state()
    try:
        _validate_record_type_contract(raw)
        with _configured_v4_reader():
            return _INHERITED_ASSESS_BYTES(raw)
    finally:
        _require_retained_predecessor_state()


def _validate_local_lifecycle(raw: bytes) -> None:
    _require_retained_predecessor_state()
    try:
        with _configured_v4_reader():
            _INHERITED_VALIDATE_LOCAL_LIFECYCLE(raw)
    finally:
        _require_retained_predecessor_state()


def assess_calibration_file(path: Path = RESULT_PATH):
    if not isinstance(path, Path):
        raise TypeError("v6 result path must be a Path")
    if path.resolve() != RESULT_PATH.resolve():
        raise ValueError("v6 file assessment requires the public result path")
    _require_retained_predecessor_state()
    try:
        raw = path.read_bytes()
        _validate_local_lifecycle(raw)
        assessed = assess_calibration_bytes(raw)
        final_raw = path.read_bytes()
        if final_raw != raw:
            raise ValueError("v6 result changed during assessment")
        _validate_local_lifecycle(final_raw)
        return assessed
    finally:
        _require_retained_predecessor_state()


__all__ = [
    "CAMPAIGN_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "PROTOCOL_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "assess_calibration_bytes",
    "assess_calibration_file",
]
