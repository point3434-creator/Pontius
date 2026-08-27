"""Fresh ADR-0469 lifecycle around the sealed v3 calibration science.

The v5 owner reuses the audited v4 process mechanics only while every public
identity is rebound to a fresh namespace.  V4 remains permanently uninvoked.
Neither compiled-calibration science module is imported here at module scope.
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
    "legal-river-quotient-compiled-global-separation-calibration-v7-inherited-header-contract.json"
)
HEADER_CONTRACT_CONFIG_SHA256 = (
    "2aa2eb3068723c2c3cb5ed13ed7e340f1a51101bfc64ecacd5e01a8486712d03"
)
AUTHORIZATION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v8-"
    "corrected-invocation-authorization.json"
)
AUTHORIZATION_CONFIG_PATH = ROOT / AUTHORIZATION_CONFIG_RELATIVE_PATH
AUTHORIZATION_SCHEMA_VERSION = "pontius-adr0471-one-commit-authorization-v1"
AUTHORIZATION_COMMIT_PATHS = (
    "ARCHITECTURE.md",
    "RISK_REGISTER.md",
    "ROADMAP.md",
    "STATUS.md",
    "docs/decisions/ADR-0471-authorize-one-corrected-deferred-import-calibration-invocation.md",
    AUTHORIZATION_CONFIG_RELATIVE_PATH,
)
PREREGISTRATION_COMMIT = "4229fb57d75a279be44d74235afb82c030d84308"

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

RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5.jsonl"
)
RESULT_PATH = ROOT / RESULT_RELATIVE_PATH
ATTEMPT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5.attempt.json"
)
ATTEMPT_PATH = ROOT / ATTEMPT_RELATIVE_PATH
LAUNCH_PENDING_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5.launch-pending.json"
)
LAUNCH_CONSUMED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5.launch-consumed.json"
)
LAUNCH_ABORTED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v5.launch-aborted.json"
)
LAUNCH_PENDING_PATH = ROOT / LAUNCH_PENDING_RELATIVE_PATH
LAUNCH_CONSUMED_PATH = ROOT / LAUNCH_CONSUMED_RELATIVE_PATH
LAUNCH_ABORTED_PATH = ROOT / LAUNCH_ABORTED_RELATIVE_PATH

LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration_v5_runner"
)
SCIENTIFIC_MODULE = _v4.SCIENTIFIC_MODULE
PARENT_SCIENTIFIC_MODULE = _v4.PARENT_SCIENTIFIC_MODULE
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0469-inherited-header-contract-owner-v5"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0469-inherited-header-contract-campaign-v5"
).hexdigest()
ATTEMPT_SCHEMA_VERSION = "pontius-adr0469-public-attempt-v5-v1"
LAUNCH_SCHEMA_VERSION = "pontius-adr0470-one-use-child-launch-v5-v1"

_MODE_ENV = "PONTIUS_ADR0469_COMPILED_SEPARATION_MODE"
_CHALLENGE_ENV = "PONTIUS_ADR0469_COMPILED_SEPARATION_CHALLENGE"
_SPOOL_ENV = "PONTIUS_ADR0469_COMPILED_SEPARATION_SPOOL"
_LAUNCH_TOKEN_ENV = "PONTIUS_ADR0469_COMPILED_SEPARATION_LAUNCH_TOKEN"
_SOURCE_PROBE = "inherited_header_contract_source_probe_v5"
_CAMPAIGN_CHILD = "campaign_child_v5"
_EVENT_PREFIX = b"PONTIUS_ADR0469_EVENT "
_ACK_PREFIX = b"PONTIUS_ADR0469_ACK "
_PUBLIC_PYCACHE_ENV = "PONTIUS_ADR0470_PUBLIC_SOURCE_PYCACHE"
_CHILD_PYCACHE_DIRECTORY = "adr0470-unused-child-pycache"
_LEGACY_ENV_NAMES = (
    _v4._MODE_ENV,
    _v4._CHALLENGE_ENV,
    _v4._SPOOL_ENV,
    _v4._LAUNCH_TOKEN_ENV,
    _v4._PUBLIC_PYCACHE_ENV,
)

DEPENDENCY_RELATIVE_PATHS = (
    *_v4.DEPENDENCY_RELATIVE_PATHS,
    HEADER_CONTRACT_CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0469-retain-the-deferred-import-authorization-gate-rejection.md",
    "docs/decisions/ADR-0470-retain-the-accidental-v5-preauthorization-attempt.md",
    "run_legal_river_quotient_compiled_global_separation_calibration_v5.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v5_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v5_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v5.py",
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
    "source_seal_probe",
    "strict_git_metadata",
)


def _canonical_lf(raw: bytes) -> bytes:
    return raw.replace(bytes((13, 10)), bytes((10,)))


def _is_lower_hex(value: object, length: int) -> bool:
    return (
        type(value) is str
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def _authorization_identity(commit: str | None = None) -> dict[str, object]:
    if (
        not AUTHORIZATION_CONFIG_PATH.is_file()
        or AUTHORIZATION_CONFIG_PATH.is_symlink()
        or (
            getattr(
                AUTHORIZATION_CONFIG_PATH.stat(follow_symlinks=False),
                "st_file_attributes",
                0,
            )
            & stat.FILE_ATTRIBUTE_REPARSE_POINT
        )
    ):
        raise FileNotFoundError("v5 invocation authorization is absent")
    raw = AUTHORIZATION_CONFIG_PATH.read_bytes()
    config = _v4._load_json(
        AUTHORIZATION_CONFIG_PATH, label="v5 invocation authorization"
    )
    paths = config.get("authorization_commit_paths")
    source_seal = config.get("source_seal_commit")
    if (
        set(config)
        != {"schema_version", "source_seal_commit", "authorization_commit_paths"}
        or config.get("schema_version") != AUTHORIZATION_SCHEMA_VERSION
        or not _is_lower_hex(source_seal, 40)
        or not isinstance(paths, list)
        or any(type(path) is not str for path in paths)
        or paths != list(AUTHORIZATION_COMMIT_PATHS)
    ):
        raise ValueError("v5 authorization fields differ")
    head = (
        _v4._v2._absolute_git("rev-parse", "HEAD").decode("ascii").strip()
        if commit is None
        else commit
    )
    if not _is_lower_hex(head, 40):
        raise ValueError("v5 authorization commit identity differs")
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
        raise RuntimeError("v5 authorization commit differs")
    committed_raw = _v4._v2._absolute_git(
        "show", f"{head}:{AUTHORIZATION_CONFIG_RELATIVE_PATH}"
    )
    if _canonical_lf(committed_raw) != _canonical_lf(raw):
        raise RuntimeError("v5 authorization working file differs from its Git blob")
    return {
        "schema_version": AUTHORIZATION_SCHEMA_VERSION,
        "config_relative_path": AUTHORIZATION_CONFIG_RELATIVE_PATH,
        "config_canonical_lf_sha256": sha256(_canonical_lf(raw)).hexdigest(),
        "source_seal_commit": source_seal,
        "authorization_commit": head,
        "authorization_commit_paths": list(paths),
        "single_generation_only": True,
    }


def _attempt_bytes() -> bytes:
    return canonical_journal_json_bytes(
        {
            "schema_version": ATTEMPT_SCHEMA_VERSION,
            "protocol_sha256": PROTOCOL_SHA256,
            "campaign_sha256": CAMPAIGN_SHA256,
            "result_relative_path": RESULT_RELATIVE_PATH,
            "rejected_v3_result_relative_path": _v4.REJECTED_V3_RESULT_RELATIVE_PATH,
            "closed_v4_result_relative_path": V4_RESULT_RELATIVE_PATH,
        }
    )


def _launch_claim_identity(token: str, authorization_commit: str) -> dict[str, object]:
    if not _is_lower_hex(token, 64) or not _is_lower_hex(authorization_commit, 40):
        raise ValueError("v5 launch claim identity differs")
    return {
        "schema_version": LAUNCH_SCHEMA_VERSION,
        "token_sha256": sha256(token.encode("ascii")).hexdigest(),
        "authorization_commit": authorization_commit,
        "result_relative_path": RESULT_RELATIVE_PATH,
    }


def _v5_replacements() -> dict[str, object]:
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
        "source_seal_probe": source_seal_probe,
        "strict_git_metadata": _strict_git_metadata_bound,
    }


@contextmanager
def _configured_v4() -> Iterator[object]:
    with _v4._BINDING_LOCK, _BINDING_LOCK:
        original = {name: getattr(_v4, name) for name in _V4_BINDINGS}
        for name, value in _v5_replacements().items():
            setattr(_v4, name, value)
        try:
            yield _v4
        finally:
            for name, value in original.items():
                setattr(_v4, name, value)


def _require_v4_lifecycle_absent() -> None:
    if any(
        os.path.lexists(path)
        for path in (
            V4_RESULT_PATH,
            V4_ATTEMPT_PATH,
            V4_LAUNCH_PENDING_PATH,
            V4_LAUNCH_CONSUMED_PATH,
            V4_LAUNCH_ABORTED_PATH,
        )
    ):
        raise FileExistsError("closed v4 lifecycle unexpectedly exists")


def _require_legacy_environment_absent() -> None:
    contaminated = sorted(name for name in _LEGACY_ENV_NAMES if name in os.environ)
    if contaminated:
        raise ValueError(
            "v5 environment contains legacy lifecycle names: "
            + ", ".join(contaminated)
        )


def _strict_git_metadata_bound(
    *,
    result_created: bool,
    launch_state: str = "pending",
    launch_token: str | None = None,
) -> dict[str, object]:
    _require_v4_lifecycle_absent()
    try:
        evidence = _INHERITED_STRICT_GIT_METADATA(
            result_created=result_created,
            launch_state=launch_state,
            launch_token=launch_token,
        )
    finally:
        _require_v4_lifecycle_absent()
    return evidence


def source_seal_probe(challenge_hex: str) -> dict[str, object]:
    _require_v4_lifecycle_absent()
    try:
        with _configured_v4():
            payload = dict(_INHERITED_SOURCE_SEAL_PROBE(challenge_hex))
            if payload.pop("v4_result_absent", None) is not True:
                raise RuntimeError("inherited source probe result absence differs")
            payload.update(
                {
                    "schema_version": "pontius-adr0469-inherited-header-source-probe-v5",
                    "v4_lifecycle_absent": True,
                    "v5_result_absent": True,
                }
            )
    finally:
        _require_v4_lifecycle_absent()
    return payload


@contextmanager
def configured_parent(*, launch_token: str | None = None) -> Iterator[object]:
    _require_v4_lifecycle_absent()
    try:
        with _configured_v4() as engine:
            with _INHERITED_CONFIGURED_PARENT(launch_token=launch_token) as parent:
                yield parent
    finally:
        _require_v4_lifecycle_absent()


def _current_dependency_hashes() -> dict[str, str]:
    with _configured_v4():
        return _INHERITED_CURRENT_DEPENDENCY_HASHES()


def _launch_marker_bytes(identity: Mapping[str, object], *, state: str) -> bytes:
    return _v4._launch_marker_bytes(identity, state=state)


def claim_public_attempt(path: Path | None = None) -> None:
    _require_v4_lifecycle_absent()
    try:
        with _configured_v4():
            _INHERITED_CLAIM_PUBLIC_ATTEMPT(path)
    finally:
        _require_v4_lifecycle_absent()


def claim_child_launch(token: str, authorization_commit: str) -> dict[str, object]:
    _require_v4_lifecycle_absent()
    try:
        with _configured_v4():
            identity = _INHERITED_CLAIM_CHILD_LAUNCH(token, authorization_commit)
    finally:
        _require_v4_lifecycle_absent()
    return identity


def consume_child_launch(token: str) -> dict[str, object]:
    _require_v4_lifecycle_absent()
    try:
        with _configured_v4():
            identity = _INHERITED_CONSUME_CHILD_LAUNCH(token)
    finally:
        _require_v4_lifecycle_absent()
    return identity


def abort_child_launch(token: str) -> dict[str, object]:
    _require_v4_lifecycle_absent()
    try:
        with _configured_v4():
            identity = _INHERITED_ABORT_CHILD_LAUNCH(token)
    finally:
        _require_v4_lifecycle_absent()
    return identity


def finalize_child_launch_after_owner(token: str) -> str:
    _require_v4_lifecycle_absent()
    try:
        with _configured_v4():
            state = _INHERITED_FINALIZE_CHILD_LAUNCH(token)
    finally:
        _require_v4_lifecycle_absent()
    return state


def strict_git_metadata(
    *,
    result_created: bool,
    launch_state: str = "pending",
    launch_token: str | None = None,
) -> dict[str, object]:
    _require_v4_lifecycle_absent()
    try:
        with _configured_v4():
            return _strict_git_metadata_bound(
                result_created=result_created,
                launch_state=launch_state,
                launch_token=launch_token,
            )
    finally:
        _require_v4_lifecycle_absent()


def main() -> int:
    _require_v4_lifecycle_absent()
    _require_legacy_environment_absent()
    try:
        with _configured_v4():
            return _INHERITED_MAIN()
    finally:
        _require_v4_lifecycle_absent()


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ATTEMPT_PATH",
    "ATTEMPT_RELATIVE_PATH",
    "AUTHORIZATION_COMMIT_PATHS",
    "AUTHORIZATION_CONFIG_PATH",
    "AUTHORIZATION_CONFIG_RELATIVE_PATH",
    "CAMPAIGN_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "LITERAL_WORKER_MODULE",
    "PREREGISTRATION_COMMIT",
    "PROTOCOL_SHA256",
    "HEADER_CONTRACT_CONFIG_RELATIVE_PATH",
    "HEADER_CONTRACT_CONFIG_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "SCIENTIFIC_MODULE",
    "claim_public_attempt",
    "configured_parent",
    "main",
    "source_seal_probe",
    "strict_git_metadata",
]
