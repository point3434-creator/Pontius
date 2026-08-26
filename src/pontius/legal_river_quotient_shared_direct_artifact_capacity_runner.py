"""Exclusive no-argument owner for the ADR-0430 artifact assessment."""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping

from . import legal_river_quotient_shared_direct_artifact_capacity as _capacity


ROOT = Path(__file__).parents[2]
RESULT_PATH = ROOT / _capacity.RESULT_RELATIVE_PATH
INPUT_PATH = ROOT / _capacity.INPUT_RELATIVE_PATH
RESERVED_PATH = ROOT / _capacity.RESERVED_ACTUAL_RESULT_RELATIVE_PATH
SOURCE_SEAL_ADR_RELATIVE_PATH = (
    "docs/decisions/"
    "ADR-0431-source-seal-the-shared-direct-artifact-capacity-assessor.md"
)
DEPENDENCY_RELATIVE_PATHS = (
    _capacity.CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0430-preregister-the-shared-direct-artifact-capacity-assessor.md",
    SOURCE_SEAL_ADR_RELATIVE_PATH,
    "src/pontius/legal_river_quotient_shared_direct_artifact_capacity.py",
    "src/pontius/legal_river_quotient_shared_direct_artifact_capacity_runner.py",
    "src/pontius/legal_river_quotient_shared_direct_artifact_capacity_result.py",
    "tests/test_legal_river_quotient_shared_direct_artifact_capacity.py",
    _capacity.INPUT_RELATIVE_PATH,
    "src/pontius/legal_river_quotient_cuda_shared_direct_device_v3_result.py",
    "src/pontius/durable_evidence_journal.py",
    "experiments/configs/legal-river-quotient-cuda-shared-direct-device-v3.json",
    "docs/decisions/ADR-0429-retain-the-passing-shared-sample-plan-v3-validation.md",
    "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
    "experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-v1.json",
)


def _checked_git(*arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        timeout=10.0,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode(
            "utf-8", errors="replace"
        ).strip()
        raise RuntimeError(f"capacity Git metadata failed: {detail}")
    return completed.stdout


def dependency_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in DEPENDENCY_RELATIVE_PATHS:
        path = ROOT / relative
        raw = path.read_bytes()
        if not relative.startswith("artifacts/"):
            raw = raw.replace(b"\r\n", b"\n")
        hashes[relative] = sha256(raw).hexdigest()
    return hashes


def strict_git_metadata(*, result_created: bool) -> dict[str, object]:
    commit = _checked_git("rev-parse", "HEAD").decode("ascii").strip()
    if (
        len(commit) != 40
        or any(character not in "0123456789abcdef" for character in commit)
    ):
        raise RuntimeError("capacity Git commit identity differs")
    for relative in DEPENDENCY_RELATIVE_PATHS:
        observed = _checked_git("ls-files", "--error-unmatch", "--", relative)
        if observed.decode("utf-8").strip().replace("\\", "/") != relative:
            raise RuntimeError(f"capacity dependency is not tracked: {relative}")
    status = _checked_git(
        "status", "--porcelain=v1", "-z", "--untracked-files=all"
    )
    entries = [entry.replace(b"\\", b"/") for entry in status.split(b"\0") if entry]
    expected = [f"?? {_capacity.RESULT_RELATIVE_PATH}".encode("utf-8")] if result_created else []
    if entries != expected:
        raise RuntimeError("capacity owner requires its exact clean source boundary")
    if (
        RESERVED_PATH.exists()
        or not INPUT_PATH.is_file()
        or INPUT_PATH.stat().st_size != _capacity.INPUT_BYTES
        or sha256(INPUT_PATH.read_bytes()).hexdigest() != _capacity.INPUT_SHA256
        or RESULT_PATH.exists() is not result_created
    ):
        raise RuntimeError("capacity protected artifact lifecycle differs")
    return {"commit": commit, "dirty": False, "strict_status": True}


def write_exclusive(path: Path, payload: bytes) -> None:
    if not isinstance(path, Path) or not isinstance(payload, bytes) or not payload:
        raise TypeError("capacity exclusive writer input differs")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def run() -> Mapping[str, object]:
    if RESULT_PATH.exists():
        raise FileExistsError("capacity result identity is permanently consumed")
    config = _capacity.load_preregistered_config()
    _capacity.verify_preregistered_contract(config)
    git = strict_git_metadata(result_created=False)
    raw = INPUT_PATH.read_bytes()
    endpoints = _capacity.extract_bound_endpoints(raw, rebind_current_sources=True)
    dependencies = dependency_hashes()
    result = _capacity.build_result(
        endpoints=endpoints,
        input_raw=raw,
        source_git_commit=str(git["commit"]),
        dependency_hashes=dependencies,
        config=config,
    )
    payload = _capacity.canonical_json_bytes(result)
    write_exclusive(RESULT_PATH, payload)
    strict_git_metadata(result_created=True)
    return result


def main() -> int:
    if len(sys.argv) != 1 or not sys.dont_write_bytecode:
        raise RuntimeError("capacity owner requires a no-argument Python -B invocation")
    result = run()
    projection = result["projection"]
    assert isinstance(projection, Mapping)
    print(
        str(result["terminal"]),
        int(projection["projected_host_ns"]),
        int(projection["wall_limit_ns"]),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEPENDENCY_RELATIVE_PATHS",
    "dependency_hashes",
    "main",
    "run",
    "strict_git_metadata",
    "write_exclusive",
]
