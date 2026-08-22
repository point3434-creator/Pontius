"""Fail-closed result plumbing shared by new evidence runners."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .reporting import environment_metadata


@dataclass(frozen=True, slots=True)
class LoadedArtifact:
    """A decoded artifact together with the digest of the bytes consumed."""

    payload: Mapping[str, Any]
    sha256: str


def artifact_passed(artifact: Mapping[str, Any]) -> bool:
    """Read the canonical pass bit and reject absent or contradictory schemas."""

    missing = object()
    top = artifact.get("passed", missing)
    gates = artifact.get("gates")
    nested = gates.get("passed", missing) if isinstance(gates, Mapping) else missing
    values = [value for value in (top, nested) if value is not missing]
    if not values or any(type(value) is not bool for value in values):
        raise ValueError("artifact must expose a Boolean passed field")
    if len(values) == 2 and values[0] != values[1]:
        raise ValueError("artifact top-level and gate pass fields disagree")
    return bool(values[0])


def require_path(
    artifact: Mapping[str, Any], path: Sequence[str], *, artifact_name: str
) -> Any:
    """Read one frozen schema path with a useful fail-closed error."""

    value: Any = artifact
    for key in path:
        if not isinstance(value, Mapping) or key not in value:
            joined = ".".join(path)
            raise ValueError(f"{artifact_name} lacks required field {joined}")
        value = value[key]
    return value


def load_artifact(
    path: Path,
    *,
    expected_sha256: str | None = None,
    require_passed: bool = False,
) -> LoadedArtifact:
    """Hash, decode, and optionally require a passing JSON artifact."""

    if not path.is_file():
        raise ValueError(f"required artifact is unavailable: {path}")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(f"artifact digest differs: {path}")
    payload = json.loads(raw)
    if not isinstance(payload, Mapping):
        raise ValueError(f"artifact root must be an object: {path}")
    if require_passed and not artifact_passed(payload):
        raise ValueError(f"required parent artifact did not pass: {path}")
    return LoadedArtifact(payload=payload, sha256=digest)


def assemble_environment(
    *,
    runtime: Mapping[str, Any],
    git: Mapping[str, Any],
    base: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the canonical nested runtime/Git environment payload."""

    payload = dict(environment_metadata() if base is None else base)
    if "runtime" in payload:
        raise ValueError("base environment must not predefine runtime")
    payload.pop("git", None)
    payload["runtime"] = dict(runtime)
    payload["git"] = dict(git)
    return payload


def finalize_gates(checks: Mapping[str, bool]) -> dict[str, Any]:
    """Return matching top-level and nested pass fields from Boolean checks."""

    if not checks or "passed" in checks:
        raise ValueError("gate checks must be nonempty and must not define passed")
    if any(type(value) is not bool for value in checks.values()):
        raise ValueError("every gate check must be Boolean")
    passed = all(checks.values())
    return {"gates": {**checks, "passed": passed}, "passed": passed}


def serialize_result(result: Mapping[str, Any]) -> str:
    """Serialize exactly once and reject non-finite JSON values."""

    return json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
