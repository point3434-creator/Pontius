"""Independent reader for the ADR-0473 authorization-phase successor."""

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
V5_RECOVERY_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v8-"
    "v5-attempt-recovery.json"
)
V5_RECOVERY_CONFIG_SHA256 = (
    "5fab5270880625e8f909fd7f1a334f6fa38471ca34bd453de47d93fbfd2413ff"
)
RECOVERY_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v10-"
    "authorization-phase-recovery.json"
)
RECOVERY_CONFIG_PATH = ROOT / RECOVERY_CONFIG_RELATIVE_PATH
RECOVERY_CONFIG_BYTES = 6_793
RECOVERY_CONFIG_SHA256 = (
    "55b0526a655099a24ce20b83bc4855f6dfb37cc5b5a7a4a213665ee93565ac38"
)
RECOVERY_HEADER_SCHEMA_VERSION = "pontius-adr0473-v6-authorization-gate-recovery-v1"
AUTHORIZATION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v11-"
    "authorization-phase-corrected-invocation-authorization.json"
)
AUTHORIZATION_CONFIG_PATH = ROOT / AUTHORIZATION_CONFIG_RELATIVE_PATH
AUTHORIZATION_SCHEMA_VERSION = "pontius-adr0475-one-commit-v7-authorization-v1"
PREAUTHORIZATION_TAG = "preauthorization"
LIVE_AUTHORIZATION_TAG = "live_authorization"
AUTHORIZATION_COMMIT_PATHS = (
    "ARCHITECTURE.md",
    "RISK_REGISTER.md",
    "ROADMAP.md",
    "STATUS.md",
    "docs/decisions/ADR-0475-authorize-one-v7-authorization-phase-calibration-invocation.md",
    AUTHORIZATION_CONFIG_RELATIVE_PATH,
)
PREREGISTRATION_COMMIT = "5e9896e96d9179fd443ff2a014473111d4fec854"
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v7.jsonl"
)
RESULT_PATH = ROOT / RESULT_RELATIVE_PATH
ATTEMPT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v7.attempt.json"
)
ATTEMPT_PATH = ROOT / ATTEMPT_RELATIVE_PATH
LAUNCH_PENDING_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v7.launch-pending.json"
)
LAUNCH_CONSUMED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v7.launch-consumed.json"
)
LAUNCH_ABORTED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v7.launch-aborted.json"
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
V4_LAUNCH_PENDING_PATH = ROOT / (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.launch-pending.json"
)
V4_LAUNCH_CONSUMED_PATH = ROOT / (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.launch-consumed.json"
)
V4_LAUNCH_ABORTED_PATH = ROOT / (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.launch-aborted.json"
)
V4_LAUNCH_PATHS = (
    V4_LAUNCH_PENDING_PATH,
    V4_LAUNCH_CONSUMED_PATH,
    V4_LAUNCH_ABORTED_PATH,
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
(
    V5_LAUNCH_PENDING_PATH,
    V5_LAUNCH_CONSUMED_PATH,
    V5_LAUNCH_ABORTED_PATH,
) = V5_LAUNCH_PATHS
V5_AUTHORIZATION_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v8-"
    "corrected-invocation-authorization.json"
)
V5_AUTHORIZATION_PATH = ROOT / V5_AUTHORIZATION_RELATIVE_PATH
V7_LIFECYCLE_PATHS = (
    RESULT_PATH,
    ATTEMPT_PATH,
    LAUNCH_PENDING_PATH,
    LAUNCH_CONSUMED_PATH,
    LAUNCH_ABORTED_PATH,
)
V6_AUTHORIZATION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v9-"
    "corrected-invocation-authorization.json"
)
V6_AUTHORIZATION_CONFIG_PATH = ROOT / V6_AUTHORIZATION_CONFIG_RELATIVE_PATH
V6_AUTHORIZATION_CONFIG_BYTES = 482
V6_AUTHORIZATION_CONFIG_SHA256 = (
    "57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535"
)
V6_SOURCE_SEAL_COMMIT = "d633f3fb469a27dee688587293c6efb1d2cb2757"
V6_AUTHORIZATION_COMMIT = "cbfa3598f22c7aba7d824f71356ca156f8b01b0c"
V6_AUTHORIZATION_SCHEMA_VERSION = "pontius-adr0472-one-commit-v6-authorization-v1"
V6_AUTHORIZATION_COMMIT_PATHS = (
    "ARCHITECTURE.md",
    "RISK_REGISTER.md",
    "ROADMAP.md",
    "STATUS.md",
    "docs/decisions/ADR-0472-authorize-one-v6-retained-attempt-calibration-invocation.md",
    V6_AUTHORIZATION_CONFIG_RELATIVE_PATH,
)
V6_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v6.jsonl"
)
V6_ATTEMPT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v6.attempt.json"
)
V6_LAUNCH_RELATIVE_PATHS = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v6.launch-pending.json",
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v6.launch-consumed.json",
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v6.launch-aborted.json",
)
V6_RESULT_PATH = ROOT / V6_RESULT_RELATIVE_PATH
V6_ATTEMPT_PATH = ROOT / V6_ATTEMPT_RELATIVE_PATH
(
    V6_LAUNCH_PENDING_PATH,
    V6_LAUNCH_CONSUMED_PATH,
    V6_LAUNCH_ABORTED_PATH,
) = tuple(ROOT / path for path in V6_LAUNCH_RELATIVE_PATHS)
V6_LAUNCH_PATHS = (
    V6_LAUNCH_PENDING_PATH,
    V6_LAUNCH_CONSUMED_PATH,
    V6_LAUNCH_ABORTED_PATH,
)
V6_LIFECYCLE_PATHS = (
    V6_RESULT_PATH,
    V6_ATTEMPT_PATH,
    V6_LAUNCH_PENDING_PATH,
    V6_LAUNCH_CONSUMED_PATH,
    V6_LAUNCH_ABORTED_PATH,
)
PROTOCOL_SHA256 = "2dc6cd5636ca56b4b3b17592860737489a2bf1705de79a75bd395fa309b72272"
CAMPAIGN_SHA256 = "669a959827590b883277840161cd2cdabbed18687ad390f6667bc312362fd23d"
ATTEMPT_SCHEMA_VERSION = "pontius-adr0473-public-attempt-v7-v1"
LAUNCH_SCHEMA_VERSION = "pontius-adr0474-one-use-child-launch-v7-v1"
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration_v7_runner"
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
    V5_RECOVERY_CONFIG_RELATIVE_PATH,
    V5_ATTEMPT_RELATIVE_PATH,
    V6_AUTHORIZATION_CONFIG_RELATIVE_PATH,
    RECOVERY_CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0469-retain-the-deferred-import-authorization-gate-rejection.md",
    "docs/decisions/ADR-0470-retain-the-accidental-v5-preauthorization-attempt.md",
    "docs/decisions/ADR-0471-source-seal-the-retained-attempt-successor.md",
    "docs/decisions/ADR-0472-authorize-one-v6-retained-attempt-calibration-invocation.md",
    "docs/decisions/ADR-0473-retain-the-v6-authorization-phase-gate-rejection.md",
    "docs/decisions/ADR-0474-source-seal-the-authorization-phase-successor.md",
    "run_legal_river_quotient_compiled_global_separation_calibration_v7.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v7_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v7_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v7.py",
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
        raise TypeError("v7 reader canonical input must be bytes")
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


def _parse_unique_json(raw: bytes, *, label: str) -> object:
    if type(raw) is not bytes:
        raise TypeError(f"{label} input must be bytes")
    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_v4._unique_object,
        parse_float=lambda _: (_ for _ in ()).throw(ValueError("float in JSON")),
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("constant in JSON")),
    )


def _recovery_config() -> Mapping[str, object]:
    if not _is_regular_non_reparse(RECOVERY_CONFIG_PATH):
        raise FileNotFoundError("v7 authorization-phase recovery config is absent")
    raw = RECOVERY_CONFIG_PATH.read_bytes()
    if (
        len(raw) != RECOVERY_CONFIG_BYTES
        or sha256(_canonical_lf(raw)).hexdigest() != RECOVERY_CONFIG_SHA256
    ):
        raise ValueError("v7 authorization-phase recovery config bytes differ")
    value = _parse_unique_json(raw, label="v7 recovery config")
    if (
        type(value) is not dict
        or set(value)
        != {
            "schema_version",
            "rejected_authorization",
            "observed_gate_rejection",
            "closed_v6",
            "fresh_v7",
            "phase_contract",
            "claims",
        }
        or value.get("schema_version") != RECOVERY_HEADER_SCHEMA_VERSION
    ):
        raise ValueError("v7 authorization-phase recovery config domain differs")
    return value


def _authorization_config() -> tuple[Mapping[str, object], str]:
    if not _is_regular_non_reparse(AUTHORIZATION_CONFIG_PATH):
        raise FileNotFoundError("v7 reader invocation authorization is absent")
    raw = AUTHORIZATION_CONFIG_PATH.read_bytes()
    value = _parse_unique_json(raw, label="v7 authorization config")
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
        raise ValueError("v7 reader invocation authorization fields differ")
    return value, sha256(_canonical_lf(raw)).hexdigest()


def _git_head() -> str:
    commit = _v4._absolute_git("rev-parse", "HEAD").decode("ascii").strip()
    if not _is_lower_hex(commit, 40):
        raise ValueError("v7 HEAD identity differs")
    return commit


def _git_tree_entry(commit: str, relative_path: str) -> dict[str, str] | None:
    raw = _v4._absolute_git("ls-tree", "-z", commit, "--", relative_path)
    if raw == b"":
        return None
    rows = raw.split(b"\0")
    if len(rows) != 2 or rows[-1] != b"" or b"\t" not in rows[0]:
        raise RuntimeError("v7 authorization HEAD-tree entry is ambiguous")
    metadata, encoded_path = rows[0].split(b"\t", 1)
    fields = metadata.split()
    if len(fields) != 3:
        raise RuntimeError("v7 authorization HEAD-tree metadata differs")
    try:
        return {
            "mode": fields[0].decode("ascii"),
            "type": fields[1].decode("ascii"),
            "object": fields[2].decode("ascii"),
            "path": encoded_path.decode("utf-8").replace("\\", "/"),
        }
    except UnicodeDecodeError as exc:
        raise RuntimeError("v7 authorization HEAD-tree encoding differs") from exc


def _git_index_entry(relative_path: str) -> dict[str, str] | None:
    raw = _v4._absolute_git("ls-files", "--stage", "-z", "--", relative_path)
    if raw == b"":
        return None
    rows = raw.split(b"\0")
    if len(rows) != 2 or rows[-1] != b"" or b"\t" not in rows[0]:
        raise RuntimeError("v7 authorization index entry is ambiguous")
    metadata, encoded_path = rows[0].split(b"\t", 1)
    fields = metadata.split()
    if len(fields) != 3:
        raise RuntimeError("v7 authorization index metadata differs")
    try:
        return {
            "mode": fields[0].decode("ascii"),
            "object": fields[1].decode("ascii"),
            "stage": fields[2].decode("ascii"),
            "path": encoded_path.decode("utf-8").replace("\\", "/"),
        }
    except UnicodeDecodeError as exc:
        raise RuntimeError("v7 authorization index encoding differs") from exc


def _authorization_tag(commit: str | None = None) -> dict[str, object]:
    """Return the exact preauthorization/live-authorization checkout state."""

    _require_retained_predecessor_state()
    try:
        head = _git_head()
        if (
            not _is_lower_hex(head, 40)
            or commit is not None
            and (not _is_lower_hex(commit, 40) or commit != head)
        ):
            raise ValueError("v7 authorization commit identity differs")
        tree_entry = _git_tree_entry(head, AUTHORIZATION_CONFIG_RELATIVE_PATH)
        index_entry = _git_index_entry(AUTHORIZATION_CONFIG_RELATIVE_PATH)
        present = os.path.lexists(AUTHORIZATION_CONFIG_PATH)
        if not present:
            if tree_entry is not None or index_entry is not None:
                raise RuntimeError("v7 authorization absence conflicts with Git state")
            return {
                "phase": PREAUTHORIZATION_TAG,
                "authorization_config_relative_path": AUTHORIZATION_CONFIG_RELATIVE_PATH,
                "authorization_present": False,
                "authorization_in_head": False,
                "authorization_in_index": False,
                "head_commit": head,
            }
        if not _is_regular_non_reparse(AUTHORIZATION_CONFIG_PATH):
            raise RuntimeError("v7 authorization is dangling or non-regular")
        if (
            tree_entry is None
            or index_entry is None
            or tree_entry
            != {
                "mode": "100644",
                "type": "blob",
                "object": tree_entry["object"],
                "path": AUTHORIZATION_CONFIG_RELATIVE_PATH,
            }
            or index_entry
            != {
                "mode": "100644",
                "object": tree_entry["object"],
                "stage": "0",
                "path": AUTHORIZATION_CONFIG_RELATIVE_PATH,
            }
        ):
            raise RuntimeError("v7 authorization Git file state differs")
        raw = AUTHORIZATION_CONFIG_PATH.read_bytes()
        config, config_hash = _authorization_config()
        source_seal = config.get("source_seal_commit")
        parent_row = (
            _v4._absolute_git("rev-list", "--parents", "-n", "1", head)
            .decode("ascii")
            .strip()
            .split()
        )
        changed = tuple(
            row.replace("\\", "/")
            for row in _v4._absolute_git(
                "diff", "--name-only", "--no-renames", str(source_seal), head
            )
            .decode("utf-8")
            .splitlines()
            if row
        )
        if (
            parent_row != [head, source_seal]
            or tuple(sorted(changed)) != tuple(sorted(AUTHORIZATION_COMMIT_PATHS))
        ):
            raise RuntimeError("v7 authorization commit differs")
        committed_raw = _v4._absolute_git(
            "show", f"{head}:{AUTHORIZATION_CONFIG_RELATIVE_PATH}"
        )
        if committed_raw != raw:
            raise RuntimeError("v7 authorization working file differs from its Git blob")
        return {
            "phase": LIVE_AUTHORIZATION_TAG,
            "authorization_config_relative_path": AUTHORIZATION_CONFIG_RELATIVE_PATH,
            "authorization_present": True,
            "authorization_in_head": True,
            "authorization_in_index": True,
            "head_commit": head,
            "schema_version": AUTHORIZATION_SCHEMA_VERSION,
            "config_canonical_lf_sha256": config_hash,
            "source_seal_commit": source_seal,
            "authorization_commit": head,
            "authorization_commit_paths": list(AUTHORIZATION_COMMIT_PATHS),
            "single_generation_only": True,
        }
    finally:
        _require_retained_predecessor_state()


def _require_authorization_phase(
    expected_phase: str, *, commit: str | None = None
) -> dict[str, object]:
    if expected_phase not in {PREAUTHORIZATION_TAG, LIVE_AUTHORIZATION_TAG}:
        raise ValueError("v7 expected authorization phase differs")
    tag = _authorization_tag(commit)
    if tag.get("phase") != expected_phase:
        raise RuntimeError("v7 authorization phase differs from repository state")
    return tag


def _authorization_identity(commit: str | None = None) -> dict[str, object]:
    value = _require_authorization_phase(LIVE_AUTHORIZATION_TAG, commit=commit)
    return {
        "schema_version": value.get("schema_version"),
        "config_relative_path": value.get("authorization_config_relative_path"),
        "config_canonical_lf_sha256": value.get("config_canonical_lf_sha256"),
        "source_seal_commit": value.get("source_seal_commit"),
        "authorization_commit": value.get("authorization_commit"),
        "authorization_commit_paths": value.get("authorization_commit_paths"),
        "single_generation_only": value.get("single_generation_only"),
    }


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
            "closed_v6_result_relative_path": V6_RESULT_RELATIVE_PATH,
            "closed_v6_attempt_relative_path": V6_ATTEMPT_RELATIVE_PATH,
            "rejected_v6_authorization_config_relative_path": (
                V6_AUTHORIZATION_CONFIG_RELATIVE_PATH
            ),
            "rejected_v6_authorization_config_canonical_lf_sha256": (
                V6_AUTHORIZATION_CONFIG_SHA256
            ),
            "recovery_config_relative_path": RECOVERY_CONFIG_RELATIVE_PATH,
            "recovery_config_canonical_lf_sha256": RECOVERY_CONFIG_SHA256,
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
    """Require exact retained v5/v6 evidence and every frozen absence."""

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
    if not _is_regular_non_reparse(V6_AUTHORIZATION_CONFIG_PATH):
        raise FileNotFoundError("rejected v6 authorization is absent or not regular")
    v6_raw = V6_AUTHORIZATION_CONFIG_PATH.read_bytes()
    v6_value = _parse_unique_json(v6_raw, label="rejected v6 authorization")
    _require_exact_json(
        v6_value,
        {
            "schema_version": V6_AUTHORIZATION_SCHEMA_VERSION,
            "source_seal_commit": V6_SOURCE_SEAL_COMMIT,
            "authorization_commit_paths": list(V6_AUTHORIZATION_COMMIT_PATHS),
        },
        label="rejected v6 authorization",
    )
    committed_v6 = _v4._absolute_git(
        "show", f"{V6_AUTHORIZATION_COMMIT}:{V6_AUTHORIZATION_CONFIG_RELATIVE_PATH}"
    )
    parent_row = (
        _v4._absolute_git(
            "rev-list", "--parents", "-n", "1", V6_AUTHORIZATION_COMMIT
        )
        .decode("ascii")
        .strip()
        .split()
    )
    changed = tuple(
        row.replace("\\", "/")
        for row in _v4._absolute_git(
            "diff",
            "--name-only",
            "--no-renames",
            V6_SOURCE_SEAL_COMMIT,
            V6_AUTHORIZATION_COMMIT,
        )
        .decode("utf-8")
        .splitlines()
        if row
    )
    if (
        len(v6_raw) != V6_AUTHORIZATION_CONFIG_BYTES
        or sha256(_canonical_lf(v6_raw)).hexdigest()
        != V6_AUTHORIZATION_CONFIG_SHA256
        or v6_raw != committed_v6
        or parent_row != [V6_AUTHORIZATION_COMMIT, V6_SOURCE_SEAL_COMMIT]
        or tuple(sorted(changed)) != tuple(sorted(V6_AUTHORIZATION_COMMIT_PATHS))
    ):
        raise ValueError("rejected v6 authorization evidence differs")

    absent = (
        _v4.REJECTED_V3_RESULT_PATH,
        V4_RESULT_PATH,
        V4_ATTEMPT_PATH,
        *V4_LAUNCH_PATHS,
        V5_RESULT_PATH,
        *V5_LAUNCH_PATHS,
        V5_AUTHORIZATION_PATH,
        V6_RESULT_PATH,
        V6_ATTEMPT_PATH,
        V6_LAUNCH_PENDING_PATH,
        V6_LAUNCH_CONSUMED_PATH,
        V6_LAUNCH_ABORTED_PATH,
    )
    if any(os.path.lexists(path) for path in absent):
        raise FileExistsError("closed predecessor or fresh v7 lifecycle unexpectedly exists")


def _expected_v6_authorization_gate_recovery() -> dict[str, object]:
    return {
        "schema_version": RECOVERY_HEADER_SCHEMA_VERSION,
        "config_relative_path": RECOVERY_CONFIG_RELATIVE_PATH,
        "config_canonical_lf_sha256": RECOVERY_CONFIG_SHA256,
        "preregistered_recovery_config": dict(_recovery_config()),
        "retained_v5_attempt": {
            "relative_path": V5_ATTEMPT_RELATIVE_PATH,
            "bytes": V5_ATTEMPT_BYTES,
            "raw_sha256": V5_ATTEMPT_SHA256,
            "regular_file": True,
            "symlink": False,
            "reparse_point": False,
        },
    }


def _validate_v6_authorization_gate_recovery(value: object) -> None:
    _require_exact_json(
        value,
        _expected_v6_authorization_gate_recovery(),
        label="v7 v6-authorization-gate recovery identity",
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
        label="v7 absolute-Git recovery identity",
    )
    if os.path.lexists(ABSOLUTE_GIT_PREDECESSOR_RESULT_PATH):
        raise ValueError("v7 absolute-Git predecessor result unexpectedly exists")
    assert isinstance(value, Mapping)
    return value


def _validate_deferred_import_recovery(
    value: object,
) -> tuple[Mapping[str, object], Mapping[str, object]]:
    """Validate only the ADR-0466 deferred-import and launch-ABI layer."""

    if type(value) is not dict:
        raise TypeError("v7 launch ABI identity must be an object")
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
        raise ValueError("v7 deferred-import recovery identity differs")
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
        label="v7 deferred-import predecessor",
    )
    if (
        not _v4.CONSUMED_RESULT_PATH.is_file()
        or _v4.CONSUMED_RESULT_PATH.stat().st_size != _v4.CONSUMED_RESULT_BYTES
        or sha256(_v4.CONSUMED_RESULT_PATH.read_bytes()).hexdigest()
        != _v4.CONSUMED_RESULT_SHA256
    ):
        raise ValueError("v7 deferred-import predecessor bytes differ")
    _require_exact_json(
        identity.get("rejected_v3"),
        {
            "source_seal_commit": _v4.REJECTED_V3_SOURCE_SEAL_COMMIT,
            "result_relative_path": _v4.REJECTED_V3_RESULT_RELATIVE_PATH,
            "result_exists": False,
            "public_invocation_count": 0,
        },
        label="v7 rejected-v3 identity",
    )
    if os.path.lexists(_v4.REJECTED_V3_RESULT_PATH):
        raise ValueError("v7 rejected-v3 result unexpectedly exists")
    if not _exact_json(
        identity.get("executed_science_identity"),
        _v4._expected_executed_science_identity(),
    ):
        raise ValueError("v7 header science identity differs")
    contract = identity.get("launch_arity_contract")
    if type(contract) is not dict:
        raise TypeError("v7 launch contract must be an object")
    signatures = contract.get("kernel_signatures")
    if type(signatures) is not dict:
        raise TypeError("v7 kernel signatures must be an object")
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
        raise ValueError("v7 deferred-import launch contract differs")
    return identity, contract


def _validate_deferred_header(raw: bytes) -> None:
    recovery = _v4.recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.is_complete or not recovery.records:
        raise ValueError("v7 deferred-import journal is incomplete")
    _v4._validate_semantic_identities(recovery)
    first = recovery.records[0]
    if first.body.kind is not JournalRecordKind.HEADER:
        raise ValueError("v7 deferred-import journal omits header")
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
        "v6_authorization_gate_recovery",
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
        raise ValueError("v7 deferred-import header domain differs")
    _require_exact_json(
        header.get("claims"), _REJECTED_CLAIMS, label="v7 header claims"
    )
    _validate_v6_authorization_gate_recovery(
        header.get("v6_authorization_gate_recovery")
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
        raise ValueError("v7 inherited science cross-identity differs")

    source_git = header.get("source_seal_git")
    dependency_hashes = header.get("dependency_hashes")
    stored_auth = header.get("deferred_science_import_authorization")
    if type(source_git) is not dict or type(dependency_hashes) is not dict:
        raise TypeError("v7 source Git or dependency hashes must be an object")
    if (
        set(dependency_hashes) != set(DEPENDENCY_RELATIVE_PATHS)
        or any(not _is_lower_hex(value, 64) for value in dependency_hashes.values())
    ):
        raise ValueError("v7 dependency-hash domain differs")
    expected_config_hashes = {
        ABSOLUTE_GIT_RECOVERY_CONFIG_RELATIVE_PATH: (
            ABSOLUTE_GIT_RECOVERY_CONFIG_SHA256
        ),
        DEFERRED_IMPORT_CONFIG_RELATIVE_PATH: DEFERRED_IMPORT_CONFIG_SHA256,
        HEADER_CONTRACT_CONFIG_RELATIVE_PATH: HEADER_CONTRACT_CONFIG_SHA256,
        V5_RECOVERY_CONFIG_RELATIVE_PATH: V5_RECOVERY_CONFIG_SHA256,
        V6_AUTHORIZATION_CONFIG_RELATIVE_PATH: V6_AUTHORIZATION_CONFIG_SHA256,
        RECOVERY_CONFIG_RELATIVE_PATH: RECOVERY_CONFIG_SHA256,
    }
    if any(
        dependency_hashes.get(path) != digest
        for path, digest in expected_config_hashes.items()
    ):
        raise ValueError("v7 recovery config dependency cross-identity differs")
    authorization_tag = _authorization_tag()
    expected_auth = _authorization_identity(
        commit=str(authorization_tag["authorization_commit"])
    )
    authorization_commit = authorization_tag["authorization_commit"]
    _require_exact_json(
        stored_auth, expected_auth, label="v7 deferred-import authorization"
    )
    launch_claim = source_git.get("launch_claim")
    if type(launch_claim) is not dict or not _is_lower_hex(
        launch_claim.get("token_sha256"), 64
    ):
        raise ValueError("v7 launch claim token differs")
    expected_launch = {
        "schema_version": LAUNCH_SCHEMA_VERSION,
        "token_sha256": launch_claim["token_sha256"],
        "authorization_commit": authorization_commit,
        "result_relative_path": RESULT_RELATIVE_PATH,
    }
    _require_exact_json(launch_claim, expected_launch, label="v7 launch claim")
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
    _require_exact_json(source_git, expected_source_git, label="v7 source-seal Git")
    _validate_v7_authorization_git(
        authorization_commit,
        authorization_tag.get("source_seal_commit"),
        dependency_hashes,
        authorization_tag["config_canonical_lf_sha256"],
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
        raise ValueError("v7 typed journal is incomplete")
    for record in recovery.records:
        payload = record.body.payload
        if type(payload) is not dict:
            raise TypeError("v7 record payload must be an object")
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
                raise ValueError("v7 observation wrapper types differ")
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
                    label="v7 bootstrap type contract",
                )
            elif kind == "terminal_evidence":
                passed = event.get("passed")
                if type(passed) is not bool:
                    raise ValueError("v7 terminal-evidence pass type differs")
                for name in (
                    "science_import_completed",
                    "science_identity_validated",
                    "science_execution_started",
                ):
                    if type(event.get(name)) is not bool:
                        raise ValueError(f"v7 terminal-evidence {name} type differs")
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
                        raise ValueError(f"v7 terminal-evidence {name} type differs")
                executed = event.get("executed_science_identity")
                if event.get("science_execution_started") is True:
                    _require_exact_json(
                        executed,
                        _v4._expected_executed_science_identity(),
                        label="v7 terminal executed-science identity",
                    )
                elif executed is not None:
                    raise ValueError("v7 pre-import terminal science identity differs")
                claims = event.get("claims")
                if passed:
                    if type(claims) is not dict or type(
                        claims.get("material_zeta_speed_claim")
                    ) is not bool:
                        raise ValueError("v7 successful terminal claims type differs")
                    expected_claims = _v4._expected_success_claims(
                        claims["material_zeta_speed_claim"]
                    )
                else:
                    expected_claims = _REJECTED_CLAIMS
                _require_exact_json(
                    claims, expected_claims, label="v7 terminal-evidence claims"
                )
            continue
        if record.body.kind is JournalRecordKind.TERMINAL:
            passed = payload.get("passed")
            if type(passed) is not bool or type(payload.get("event_count")) is not int:
                raise ValueError("v7 owner terminal Boolean/integer types differ")
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
                    raise ValueError(f"v7 owner terminal {name} type differs")
            _require_exact_json(
                payload.get("claims"),
                _v4._expected_owner_success_claims() if passed else _REJECTED_CLAIMS,
                label="v7 owner terminal claims",
            )


def _validate_inherited_success_event_types(
    kind: str, event: Mapping[str, object]
) -> None:
    """Type-seal fixed scientific fields before inherited value validation."""

    if kind == "arithmetic_admission":
        _require_exact_json(
            event,
            _BASE_READER._expected_arithmetic_admission(),
            label="v7 arithmetic-admission type contract",
        )
        return
    if kind == "source_contract":
        _require_exact_int(
            event.get("full_codeword_reconstruction_call_sites"),
            label="v7 reconstruction call sites",
        )
        _require_exact_int(
            event.get("batched_admission_consumer_sites"),
            label="v7 admission consumer sites",
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
            label="v7 timed-host type contract",
        )
        return
    if kind == "compile_resource_evidence":
        for name in (
            "register_ceiling",
            "spill_store_ceiling_bytes",
            "spill_load_ceiling_bytes",
        ):
            _require_exact_int(event.get(name), label=f"v7 compile resource {name}")
        return
    if kind == "module_load_and_runtime":
        _require_exact_int(event.get("kernel_count"), label="v7 module kernel count")
        return
    if kind == "device_memory_admission":
        _require_exact_int(
            event.get("physical_RRNS_table_arena_allocations"),
            label="v7 physical RRNS arena count",
        )
        _require_exact_int(
            event.get("RRNS_table_arena_channel_capacity"),
            label="v7 RRNS channel capacity",
        )
        _require_exact_json(
            event.get("campaign"),
            _BASE_READER._expected_liveness(
                _BASE_READER._campaign_memory_peak()
            ),
            label="v7 campaign liveness type contract",
        )
        return
    if kind == "device_domain_prepared":
        cards = _require_exact_int(event.get("cards"), label="v7 domain cards")
        _require_exact_json(
            event.get("memory"),
            {
                "shared_five_channel_replay": _BASE_READER._expected_liveness(
                    _BASE_READER._domain_memory_peak(cards)
                )
            },
            label="v7 domain liveness type contract",
        )
        return
    if kind == "calibration_cell":
        _require_exact_int(event.get("pass_index"), label="v7 cell pass index")
        partition = event.get("phase_partition")
        terminal = event.get("terminal")
        differential = event.get("differential")
        if type(partition) is not dict or type(terminal) is not dict:
            raise ValueError("v7 cell partition or terminal must be an object")
        if type(differential) is not dict:
            raise ValueError("v7 cell differential must be an object")
        _require_exact_int(
            partition.get("primitive_total_ns"),
            label="v7 cell primitive total",
        )
        for name in (
            "found_positive",
            "globally_closed",
            "prefix_decision_keys",
        ):
            if name in terminal:
                _require_exact_int(
                    terminal[name], label=f"v7 cell terminal {name}"
                )
        complete = differential.get("complete_positive_output")
        if complete is not None:
            if type(complete) is not dict:
                raise ValueError("v7 complete differential must be an object")
            _require_exact_int(
                complete.get("authority_coordinates_checked"),
                label="v7 complete differential coordinate count",
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
            raise ValueError("v7 fit-projection rows must be lists")
        for row in fit_rows:
            if type(row) is not dict:
                raise ValueError("v7 fit row must be an object")
            for name in ("target_upper_ceiling_ns", "target_work"):
                _require_exact_int(row.get(name), label=f"v7 fit row {name}")
        for row in primitive_rows:
            if type(row) is not dict:
                raise ValueError("v7 primitive row must be an object")
            _require_exact_int(
                row.get("projected_primitive_upper_ns"),
                label="v7 projected primitive upper",
            )
        for row in materiality_rows:
            if type(row) is not dict:
                raise ValueError("v7 materiality row must be an object")
            _require_exact_int(
                row.get("direct_upper_ns"), label="v7 direct materiality upper"
            )
            _require_exact_int(
                row.get("zeta_upper_ns"), label="v7 zeta materiality upper"
            )
            if type(row.get("zeta_at_most_half_direct")) is not bool:
                raise ValueError("v7 materiality conjunct must be a Boolean")


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


def _validate_v7_authorization_git(
    authorization_commit: object,
    source_seal_commit: object,
    dependency_hashes: Mapping[str, object],
    authorization_config_sha256: str,
) -> None:
    """Run the inherited Git proof only under the complete v7 identity."""

    if (
        type(dependency_hashes) is not dict
        or set(dependency_hashes) != set(DEPENDENCY_RELATIVE_PATHS)
        or any(not _is_lower_hex(value, 64) for value in dependency_hashes.values())
        or not _is_lower_hex(authorization_config_sha256, 64)
    ):
        raise ValueError("v7 authorization dependency domain differs")
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
            raise ValueError("v7 authorization Git blob differs")


def _dependency_hashes_at_commit(commit: str) -> dict[str, str]:
    """Produce hashes only inside the complete v7-over-v4 binding domain."""

    if not _is_lower_hex(commit, 40):
        raise ValueError("v7 dependency commit identity differs")
    with _configured_v4_reader():
        hashes = _v4._dependency_hashes_at_commit(commit)
    if set(hashes) != set(DEPENDENCY_RELATIVE_PATHS):
        raise ValueError("v7 produced dependency domain differs")
    return hashes


def _authorization_snapshot() -> dict[str, object]:
    _require_retained_predecessor_state()
    tag = _authorization_tag()
    _require_retained_predecessor_state()
    return tag


def _require_authorization_snapshot(expected: Mapping[str, object]) -> None:
    _require_retained_predecessor_state()
    _require_exact_json(
        _authorization_tag(), expected, label="v7 authorization phase snapshot"
    )


def assess_calibration_bytes(raw: bytes):
    authorization = _authorization_snapshot()
    try:
        _validate_record_type_contract(raw)
        with _configured_v4_reader():
            return _INHERITED_ASSESS_BYTES(raw)
    finally:
        _require_authorization_snapshot(authorization)


def _validate_local_lifecycle(raw: bytes) -> None:
    authorization = _authorization_snapshot()
    try:
        with _configured_v4_reader():
            _INHERITED_VALIDATE_LOCAL_LIFECYCLE(raw)
    finally:
        _require_authorization_snapshot(authorization)


def assess_calibration_file(path: Path = RESULT_PATH):
    if not isinstance(path, Path):
        raise TypeError("v7 result path must be a Path")
    if path.resolve() != RESULT_PATH.resolve():
        raise ValueError("v7 file assessment requires the public result path")
    authorization = _authorization_snapshot()
    try:
        raw = path.read_bytes()
        _validate_local_lifecycle(raw)
        assessed = assess_calibration_bytes(raw)
        final_raw = path.read_bytes()
        if final_raw != raw:
            raise ValueError("v7 result changed during assessment")
        _validate_local_lifecycle(final_raw)
        return assessed
    finally:
        _require_authorization_snapshot(authorization)


__all__ = [
    "CAMPAIGN_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "LIVE_AUTHORIZATION_TAG",
    "PREAUTHORIZATION_TAG",
    "PROTOCOL_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "assess_calibration_bytes",
    "assess_calibration_file",
]
