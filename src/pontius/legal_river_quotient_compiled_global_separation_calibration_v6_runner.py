"""Fresh ADR-0470 lifecycle around the sealed v3 calibration science.

The v6 owner reuses the audited v4 process mechanics only while every public
identity is rebound to a fresh namespace.  V4 remains permanently uninvoked;
v5 remains permanently closed after its exact retained preauthorization
attempt.  Neither compiled-calibration scientific module is imported here at
module scope.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from hashlib import sha256
import os
from pathlib import Path
import stat
import sys
from threading import RLock

from . import legal_river_quotient_compiled_global_separation_calibration_v4_runner as _v4
from .durable_evidence_journal import canonical_journal_json_bytes


ROOT = Path(__file__).parents[2]
HEADER_CONTRACT_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v7-"
    "inherited-header-contract.json"
)
HEADER_CONTRACT_CONFIG_SHA256 = (
    "2aa2eb3068723c2c3cb5ed13ed7e340f1a51101bfc64ecacd5e01a8486712d03"
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

REJECTED_V3_RESULT_RELATIVE_PATH = _v4.REJECTED_V3_RESULT_RELATIVE_PATH
REJECTED_V3_RESULT_PATH = _v4.REJECTED_V3_RESULT_PATH
V4_RESULT_RELATIVE_PATH = _v4.RESULT_RELATIVE_PATH
V4_RESULT_PATH = _v4.RESULT_PATH
V4_ATTEMPT_RELATIVE_PATH = _v4.ATTEMPT_RELATIVE_PATH
V4_ATTEMPT_PATH = _v4.ATTEMPT_PATH
V4_LAUNCH_PENDING_RELATIVE_PATH = _v4.LAUNCH_PENDING_RELATIVE_PATH
V4_LAUNCH_CONSUMED_RELATIVE_PATH = _v4.LAUNCH_CONSUMED_RELATIVE_PATH
V4_LAUNCH_ABORTED_RELATIVE_PATH = _v4.LAUNCH_ABORTED_RELATIVE_PATH
V4_LAUNCH_PENDING_PATH = _v4.LAUNCH_PENDING_PATH
V4_LAUNCH_CONSUMED_PATH = _v4.LAUNCH_CONSUMED_PATH
V4_LAUNCH_ABORTED_PATH = _v4.LAUNCH_ABORTED_PATH

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
V5_ATTEMPT_SCHEMA_VERSION = "pontius-adr0469-public-attempt-v5-v1"
V5_PROTOCOL_SHA256 = (
    "8ae5b257549a7ffe2807d9cf5f8b54574fa698f13b6b08f79c1a690d53cfc01d"
)
V5_CAMPAIGN_SHA256 = (
    "c3b38c41fa199d0076a75912513fc5eb6b2d5e4dc806e224f861426b9bad6a0d"
)
V5_LAUNCH_PENDING_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5."
    "launch-pending.json"
)
V5_LAUNCH_CONSUMED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5."
    "launch-consumed.json"
)
V5_LAUNCH_ABORTED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5."
    "launch-aborted.json"
)
V5_LAUNCH_PENDING_PATH = ROOT / V5_LAUNCH_PENDING_RELATIVE_PATH
V5_LAUNCH_CONSUMED_PATH = ROOT / V5_LAUNCH_CONSUMED_RELATIVE_PATH
V5_LAUNCH_ABORTED_PATH = ROOT / V5_LAUNCH_ABORTED_RELATIVE_PATH
V5_AUTHORIZATION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v8-"
    "corrected-invocation-authorization.json"
)
V5_AUTHORIZATION_CONFIG_PATH = ROOT / V5_AUTHORIZATION_CONFIG_RELATIVE_PATH

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
    "legal_river_quotient_compiled_global_separation_calibration_v6."
    "launch-pending.json"
)
LAUNCH_CONSUMED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v6."
    "launch-consumed.json"
)
LAUNCH_ABORTED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v6."
    "launch-aborted.json"
)
LAUNCH_PENDING_PATH = ROOT / LAUNCH_PENDING_RELATIVE_PATH
LAUNCH_CONSUMED_PATH = ROOT / LAUNCH_CONSUMED_RELATIVE_PATH
LAUNCH_ABORTED_PATH = ROOT / LAUNCH_ABORTED_RELATIVE_PATH

LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration_v6_runner"
)
SCIENTIFIC_MODULE = _v4.SCIENTIFIC_MODULE
PARENT_SCIENTIFIC_MODULE = _v4.PARENT_SCIENTIFIC_MODULE
PROTOCOL_SHA256 = (
    "ffb1f1831bd31ec61b0bedefa9a5544a02e02e1e6d3512e65ff7824988696911"
)
CAMPAIGN_SHA256 = (
    "ae05bb948abe57c0a3b4b5fcd17cb04555db6a549f8a1d59c192e87ae9c75e3c"
)
ATTEMPT_SCHEMA_VERSION = "pontius-adr0470-public-attempt-v6-v1"
LAUNCH_SCHEMA_VERSION = "pontius-adr0471-one-use-child-launch-v6-v1"
RECOVERY_HEADER_SCHEMA_VERSION = (
    "pontius-adr0470-retained-v5-attempt-recovery-v1"
)

_MODE_ENV = "PONTIUS_ADR0470_COMPILED_SEPARATION_MODE"
_CHALLENGE_ENV = "PONTIUS_ADR0470_COMPILED_SEPARATION_CHALLENGE"
_SPOOL_ENV = "PONTIUS_ADR0470_COMPILED_SEPARATION_SPOOL"
_LAUNCH_TOKEN_ENV = "PONTIUS_ADR0470_COMPILED_SEPARATION_LAUNCH_TOKEN"
_SOURCE_PROBE = "retained_v5_attempt_recovery_source_probe_v6"
_CAMPAIGN_CHILD = "campaign_child_v6"
_EVENT_PREFIX = b"PONTIUS_ADR0470_EVENT "
_ACK_PREFIX = b"PONTIUS_ADR0470_ACK "
_PUBLIC_PYCACHE_ENV = "PONTIUS_ADR0471_PUBLIC_SOURCE_PYCACHE"
_CHILD_PYCACHE_DIRECTORY = "adr0471-unused-child-pycache"
_V5_LEGACY_ENV_NAMES = (
    "PONTIUS_ADR0469_COMPILED_SEPARATION_MODE",
    "PONTIUS_ADR0469_COMPILED_SEPARATION_CHALLENGE",
    "PONTIUS_ADR0469_COMPILED_SEPARATION_SPOOL",
    "PONTIUS_ADR0469_COMPILED_SEPARATION_LAUNCH_TOKEN",
    "PONTIUS_ADR0470_PUBLIC_SOURCE_PYCACHE",
)
_LEGACY_ENV_NAMES = (
    _v4._MODE_ENV,
    _v4._CHALLENGE_ENV,
    _v4._SPOOL_ENV,
    _v4._LAUNCH_TOKEN_ENV,
    _v4._PUBLIC_PYCACHE_ENV,
    *_V5_LEGACY_ENV_NAMES,
)

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

_BINDING_LOCK = RLock()
_INHERITED_SOURCE_SEAL_PROBE = _v4.source_seal_probe
_INHERITED_MAIN = _v4.main
_INHERITED_CONFIGURED_PARENT = _v4.configured_parent
_INHERITED_STRICT_GIT_METADATA = _v4.strict_git_metadata
_INHERITED_CLAIM_PUBLIC_ATTEMPT = _v4.claim_public_attempt
_INHERITED_CLAIM_CHILD_LAUNCH = _v4.claim_child_launch
_INHERITED_CONSUME_CHILD_LAUNCH = _v4.consume_child_launch
_INHERITED_ABORT_CHILD_LAUNCH = _v4.abort_child_launch
_INHERITED_FINALIZE_CHILD_LAUNCH = _v4.finalize_child_launch_after_owner
_INHERITED_CURRENT_DEPENDENCY_HASHES = _v4._current_dependency_hashes

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
    "LITERAL_WORKER_MODULE",
    "SCIENTIFIC_MODULE",
    "PARENT_SCIENTIFIC_MODULE",
    "PROTOCOL_SHA256",
    "CAMPAIGN_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "_MODE_ENV",
    "_CHALLENGE_ENV",
    "_SPOOL_ENV",
    "_LAUNCH_TOKEN_ENV",
    "_SOURCE_PROBE",
    "_CAMPAIGN_CHILD",
    "_EVENT_PREFIX",
    "_ACK_PREFIX",
    "_PUBLIC_PYCACHE_ENV",
    "_CHILD_PYCACHE_DIRECTORY",
    "_authorization_identity",
    "_attempt_bytes",
    "_launch_claim_identity",
    "claim_public_attempt",
    "claim_child_launch",
    "consume_child_launch",
    "abort_child_launch",
    "finalize_child_launch_after_owner",
    "source_seal_probe",
    "configured_parent",
    "strict_git_metadata",
)


def _canonical_lf(raw: bytes) -> bytes:
    if type(raw) is not bytes:
        raise TypeError("v6 canonical input must be bytes")
    return raw.replace(bytes((13, 10)), bytes((10,)))


def _is_lower_hex(value: object, length: int) -> bool:
    return (
        type(value) is str
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_regular_non_reparse(path: Path) -> bool:
    try:
        metadata = path.stat(follow_symlinks=False)
    except (FileNotFoundError, OSError):
        return False
    return (
        stat.S_ISREG(metadata.st_mode)
        and not path.is_symlink()
        and not (
            getattr(metadata, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        )
    )


def _retained_v5_attempt_bytes() -> bytes:
    return canonical_journal_json_bytes(
        {
            "schema_version": V5_ATTEMPT_SCHEMA_VERSION,
            "protocol_sha256": V5_PROTOCOL_SHA256,
            "campaign_sha256": V5_CAMPAIGN_SHA256,
            "result_relative_path": V5_RESULT_RELATIVE_PATH,
            "closed_v4_result_relative_path": V4_RESULT_RELATIVE_PATH,
            "rejected_v3_result_relative_path": REJECTED_V3_RESULT_RELATIVE_PATH,
        }
    )


def _require_retained_predecessor_state() -> None:
    if any(
        os.path.lexists(path)
        for path in (
            REJECTED_V3_RESULT_PATH,
            V4_RESULT_PATH,
            V4_ATTEMPT_PATH,
            V4_LAUNCH_PENDING_PATH,
            V4_LAUNCH_CONSUMED_PATH,
            V4_LAUNCH_ABORTED_PATH,
            V5_RESULT_PATH,
            V5_LAUNCH_PENDING_PATH,
            V5_LAUNCH_CONSUMED_PATH,
            V5_LAUNCH_ABORTED_PATH,
            V5_AUTHORIZATION_CONFIG_PATH,
        )
    ):
        raise FileExistsError("v6 retained predecessor absence differs")
    if not _is_regular_non_reparse(V5_ATTEMPT_PATH):
        raise FileNotFoundError("v6 retained v5 attempt is not a regular file")
    raw = V5_ATTEMPT_PATH.read_bytes()
    expected = _retained_v5_attempt_bytes()
    if (
        len(raw) != V5_ATTEMPT_BYTES
        or sha256(raw).hexdigest() != V5_ATTEMPT_SHA256
        or raw != expected
    ):
        raise ValueError("v6 retained v5 attempt bytes differ")


def _require_unopened_v6_source_state() -> None:
    if any(
        os.path.lexists(path)
        for path in (
            RESULT_PATH,
            ATTEMPT_PATH,
            LAUNCH_PENDING_PATH,
            LAUNCH_CONSUMED_PATH,
            LAUNCH_ABORTED_PATH,
            AUTHORIZATION_CONFIG_PATH,
        )
    ):
        raise FileExistsError("v6 source-seal lifecycle or authorization exists")


def _authorization_identity(commit: str | None = None) -> dict[str, object]:
    _require_retained_predecessor_state()
    try:
        if not _is_regular_non_reparse(AUTHORIZATION_CONFIG_PATH):
            raise FileNotFoundError("v6 invocation authorization is absent")
        raw = AUTHORIZATION_CONFIG_PATH.read_bytes()
        config = _v4._load_json(
            AUTHORIZATION_CONFIG_PATH, label="v6 invocation authorization"
        )
        paths = config.get("authorization_commit_paths")
        source_seal = config.get("source_seal_commit")
        if (
            set(config)
            != {
                "schema_version",
                "source_seal_commit",
                "authorization_commit_paths",
            }
            or config.get("schema_version") != AUTHORIZATION_SCHEMA_VERSION
            or not _is_lower_hex(source_seal, 40)
            or not isinstance(paths, list)
            or any(type(path) is not str for path in paths)
            or paths != list(AUTHORIZATION_COMMIT_PATHS)
        ):
            raise ValueError("v6 authorization fields differ")
        head = (
            _v4._v2._absolute_git("rev-parse", "HEAD").decode("ascii").strip()
            if commit is None
            else commit
        )
        if not _is_lower_hex(head, 40):
            raise ValueError("v6 authorization commit identity differs")
        parent_row = (
            _v4._v2._absolute_git("rev-list", "--parents", "-n", "1", str(head))
            .decode("ascii")
            .strip()
            .split()
        )
        changed = tuple(
            row.replace("\\", "/")
            for row in _v4._v2._absolute_git(
                "diff", "--name-only", "--no-renames", str(source_seal), str(head)
            )
            .decode("utf-8")
            .splitlines()
            if row
        )
        if (
            parent_row != [head, source_seal]
            or tuple(sorted(changed)) != tuple(sorted(AUTHORIZATION_COMMIT_PATHS))
        ):
            raise RuntimeError("v6 authorization commit differs")
        committed_raw = _v4._v2._absolute_git(
            "show", f"{head}:{AUTHORIZATION_CONFIG_RELATIVE_PATH}"
        )
        if _canonical_lf(committed_raw) != _canonical_lf(raw):
            raise RuntimeError(
                "v6 authorization working file differs from its Git blob"
            )
        return {
            "schema_version": AUTHORIZATION_SCHEMA_VERSION,
            "config_relative_path": AUTHORIZATION_CONFIG_RELATIVE_PATH,
            "config_canonical_lf_sha256": sha256(_canonical_lf(raw)).hexdigest(),
            "source_seal_commit": source_seal,
            "authorization_commit": head,
            "authorization_commit_paths": list(paths),
            "single_generation_only": True,
        }
    finally:
        _require_retained_predecessor_state()


def _attempt_bytes() -> bytes:
    return canonical_journal_json_bytes(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "protocol_sha256": PROTOCOL_SHA256,
            "campaign_sha256": CAMPAIGN_SHA256,
            "result_relative_path": RESULT_RELATIVE_PATH,
            "rejected_v3_result_relative_path": REJECTED_V3_RESULT_RELATIVE_PATH,
            "closed_v4_result_relative_path": V4_RESULT_RELATIVE_PATH,
            "closed_v5_result_relative_path": V5_RESULT_RELATIVE_PATH,
            "retained_v5_attempt_relative_path": V5_ATTEMPT_RELATIVE_PATH,
            "retained_v5_attempt_bytes": V5_ATTEMPT_BYTES,
            "retained_v5_attempt_raw_sha256": V5_ATTEMPT_SHA256,
        }
    )


def _launch_claim_identity(token: str, authorization_commit: str) -> dict[str, object]:
    if not _is_lower_hex(token, 64) or not _is_lower_hex(authorization_commit, 40):
        raise ValueError("v6 launch claim identity differs")
    return {
        "schema_version": LAUNCH_SCHEMA_VERSION,
        "token_sha256": sha256(token.encode("ascii")).hexdigest(),
        "authorization_commit": authorization_commit,
        "result_relative_path": RESULT_RELATIVE_PATH,
    }


def _retained_v5_attempt_recovery_identity() -> dict[str, object]:
    _require_retained_predecessor_state()
    return {
        "schema_version": RECOVERY_HEADER_SCHEMA_VERSION,
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
            "rejected_v3_result_relative_path": REJECTED_V3_RESULT_RELATIVE_PATH,
            "rejected_v3_result_exists": False,
            "v4_result_relative_path": V4_RESULT_RELATIVE_PATH,
            "v4_lifecycle_absent": True,
            "v5_result_relative_path": V5_RESULT_RELATIVE_PATH,
            "v5_result_exists": False,
            "v5_launch_marker_count": 0,
            "v5_authorization_relative_path": V5_AUTHORIZATION_CONFIG_RELATIVE_PATH,
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


def _v6_replacements() -> dict[str, object]:
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
        "LITERAL_WORKER_MODULE": LITERAL_WORKER_MODULE,
        "SCIENTIFIC_MODULE": SCIENTIFIC_MODULE,
        "PARENT_SCIENTIFIC_MODULE": PARENT_SCIENTIFIC_MODULE,
        "PROTOCOL_SHA256": PROTOCOL_SHA256,
        "CAMPAIGN_SHA256": CAMPAIGN_SHA256,
        "DEPENDENCY_RELATIVE_PATHS": DEPENDENCY_RELATIVE_PATHS,
        "_MODE_ENV": _MODE_ENV,
        "_CHALLENGE_ENV": _CHALLENGE_ENV,
        "_SPOOL_ENV": _SPOOL_ENV,
        "_LAUNCH_TOKEN_ENV": _LAUNCH_TOKEN_ENV,
        "_SOURCE_PROBE": _SOURCE_PROBE,
        "_CAMPAIGN_CHILD": _CAMPAIGN_CHILD,
        "_EVENT_PREFIX": _EVENT_PREFIX,
        "_ACK_PREFIX": _ACK_PREFIX,
        "_PUBLIC_PYCACHE_ENV": _PUBLIC_PYCACHE_ENV,
        "_CHILD_PYCACHE_DIRECTORY": _CHILD_PYCACHE_DIRECTORY,
        "_authorization_identity": _authorization_identity,
        "_attempt_bytes": _attempt_bytes,
        "_launch_claim_identity": _launch_claim_identity,
        "claim_public_attempt": claim_public_attempt,
        "claim_child_launch": claim_child_launch,
        "consume_child_launch": consume_child_launch,
        "abort_child_launch": abort_child_launch,
        "finalize_child_launch_after_owner": finalize_child_launch_after_owner,
        "source_seal_probe": source_seal_probe,
        "configured_parent": _configured_parent_bound,
        "strict_git_metadata": _strict_git_metadata_bound,
    }


@contextmanager
def _configured_v4() -> Iterator[object]:
    _require_retained_predecessor_state()
    with _v4._BINDING_LOCK, _BINDING_LOCK:
        original = {name: getattr(_v4, name) for name in _V4_BINDINGS}
        for name, value in _v6_replacements().items():
            setattr(_v4, name, value)
        try:
            yield _v4
        finally:
            for name, value in original.items():
                setattr(_v4, name, value)
            _require_retained_predecessor_state()


def _require_legacy_environment_absent() -> None:
    contaminated = sorted(name for name in _LEGACY_ENV_NAMES if name in os.environ)
    if contaminated:
        raise ValueError(
            "v6 environment contains legacy lifecycle names: "
            + ", ".join(contaminated)
        )


def _strict_git_metadata_bound(
    *,
    result_created: bool,
    launch_state: str = "pending",
    launch_token: str | None = None,
) -> dict[str, object]:
    _require_retained_predecessor_state()
    try:
        evidence = _INHERITED_STRICT_GIT_METADATA(
            result_created=result_created,
            launch_state=launch_state,
            launch_token=launch_token,
        )
    finally:
        _require_retained_predecessor_state()
    return evidence


@contextmanager
def _configured_parent_bound(*, launch_token: str | None = None) -> Iterator[object]:
    _require_retained_predecessor_state()
    try:
        with _INHERITED_CONFIGURED_PARENT(launch_token=launch_token) as engine:
            inherited_header = engine._header_payload

            def header_payload(git: Mapping[str, object]) -> dict[str, object]:
                payload = inherited_header(git)
                if "retained_v5_attempt_recovery" in payload:
                    raise ValueError("v6 recovery header key already exists")
                payload["retained_v5_attempt_recovery"] = (
                    _retained_v5_attempt_recovery_identity()
                )
                return payload

            engine._header_payload = header_payload
            try:
                yield engine
            finally:
                engine._header_payload = inherited_header
    finally:
        _require_retained_predecessor_state()


def source_seal_probe(challenge_hex: str) -> dict[str, object]:
    _require_retained_predecessor_state()
    _require_unopened_v6_source_state()
    try:
        with _configured_v4():
            payload = dict(_INHERITED_SOURCE_SEAL_PROBE(challenge_hex))
            inherited_absence = {
                "v6_result_absent": payload.pop("v4_result_absent", None),
                "v6_attempt_absent": payload.pop("attempt_absent", None),
                "v6_launch_markers_absent": payload.pop(
                    "launch_markers_absent", None
                ),
            }
            if any(value is not True for value in inherited_absence.values()):
                raise RuntimeError("inherited v6 source-probe absence differs")
            payload.update(
                {
                    "schema_version": (
                        "pontius-adr0470-retained-attempt-source-probe-v6"
                    ),
                    "retained_v5_attempt_recovery": (
                        _retained_v5_attempt_recovery_identity()
                    ),
                    "v4_lifecycle_absent": True,
                    "v5_attempt_retained_exactly": True,
                    "v5_result_launch_authorization_absent": True,
                    **inherited_absence,
                    "v6_authorization_absent": True,
                }
            )
    finally:
        _require_retained_predecessor_state()
        _require_unopened_v6_source_state()
    return payload


@contextmanager
def configured_parent(*, launch_token: str | None = None) -> Iterator[object]:
    _require_retained_predecessor_state()
    try:
        with _configured_v4():
            with _configured_parent_bound(launch_token=launch_token) as parent:
                yield parent
    finally:
        _require_retained_predecessor_state()


def _current_dependency_hashes() -> dict[str, str]:
    _require_retained_predecessor_state()
    try:
        with _configured_v4():
            hashes = _INHERITED_CURRENT_DEPENDENCY_HASHES()
    finally:
        _require_retained_predecessor_state()
    return hashes


def _launch_marker_bytes(identity: Mapping[str, object], *, state: str) -> bytes:
    _require_retained_predecessor_state()
    try:
        payload = _v4._launch_marker_bytes(identity, state=state)
    finally:
        _require_retained_predecessor_state()
    return payload


def claim_public_attempt(path: Path | None = None) -> None:
    _require_retained_predecessor_state()
    try:
        with _configured_v4():
            _INHERITED_CLAIM_PUBLIC_ATTEMPT(path)
    finally:
        _require_retained_predecessor_state()


def claim_child_launch(token: str, authorization_commit: str) -> dict[str, object]:
    _require_retained_predecessor_state()
    try:
        with _configured_v4():
            identity = _INHERITED_CLAIM_CHILD_LAUNCH(token, authorization_commit)
    finally:
        _require_retained_predecessor_state()
    return identity


def consume_child_launch(token: str) -> dict[str, object]:
    _require_retained_predecessor_state()
    try:
        with _configured_v4():
            identity = _INHERITED_CONSUME_CHILD_LAUNCH(token)
    finally:
        _require_retained_predecessor_state()
    return identity


def abort_child_launch(token: str) -> dict[str, object]:
    _require_retained_predecessor_state()
    try:
        with _configured_v4():
            identity = _INHERITED_ABORT_CHILD_LAUNCH(token)
    finally:
        _require_retained_predecessor_state()
    return identity


def finalize_child_launch_after_owner(token: str) -> str:
    _require_retained_predecessor_state()
    try:
        with _configured_v4():
            state = _INHERITED_FINALIZE_CHILD_LAUNCH(token)
    finally:
        _require_retained_predecessor_state()
    return state


def strict_git_metadata(
    *,
    result_created: bool,
    launch_state: str = "pending",
    launch_token: str | None = None,
) -> dict[str, object]:
    _require_retained_predecessor_state()
    try:
        with _configured_v4():
            evidence = _strict_git_metadata_bound(
                result_created=result_created,
                launch_state=launch_state,
                launch_token=launch_token,
            )
    finally:
        _require_retained_predecessor_state()
    return evidence


def _require_public_interpreter_state(
    *,
    argv: tuple[str, ...],
    dont_write_bytecode: bool,
    safe_path: bool,
) -> None:
    if (
        len(argv) != 1
        or dont_write_bytecode is not True
        or safe_path is not True
    ):
        raise RuntimeError(
            "v6 retained-attempt runner requires no arguments and Python -B -P"
        )


def main() -> int:
    _require_public_interpreter_state(
        argv=tuple(sys.argv),
        dont_write_bytecode=sys.dont_write_bytecode,
        safe_path=sys.flags.safe_path,
    )
    _require_retained_predecessor_state()
    _require_legacy_environment_absent()
    try:
        with _configured_v4():
            return _INHERITED_MAIN()
    finally:
        _require_retained_predecessor_state()


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ATTEMPT_PATH",
    "ATTEMPT_RELATIVE_PATH",
    "AUTHORIZATION_COMMIT_PATHS",
    "AUTHORIZATION_CONFIG_PATH",
    "AUTHORIZATION_CONFIG_RELATIVE_PATH",
    "AUTHORIZATION_SCHEMA_VERSION",
    "CAMPAIGN_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "HEADER_CONTRACT_CONFIG_RELATIVE_PATH",
    "HEADER_CONTRACT_CONFIG_SHA256",
    "LITERAL_WORKER_MODULE",
    "PREREGISTRATION_COMMIT",
    "PROTOCOL_SHA256",
    "RECOVERY_CONFIG_RELATIVE_PATH",
    "RECOVERY_CONFIG_SHA256",
    "RECOVERY_HEADER_SCHEMA_VERSION",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "SCIENTIFIC_MODULE",
    "V5_ATTEMPT_BYTES",
    "V5_ATTEMPT_PATH",
    "V5_ATTEMPT_RELATIVE_PATH",
    "V5_ATTEMPT_SHA256",
    "claim_public_attempt",
    "configured_parent",
    "main",
    "source_seal_probe",
    "strict_git_metadata",
]
