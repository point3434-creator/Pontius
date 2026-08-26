"""Exclusive no-argument owner for the ADR-0449/ADR-0450 projection."""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Mapping

from . import legal_river_quotient_fixed_width_actual45_fit_projection as _projection


ROOT = Path(__file__).parents[2]
RESULT_PATH = ROOT / _projection.RESULT_RELATIVE_PATH
INPUT_PATH = ROOT / _projection.INPUT_RELATIVE_PATH
GIT_PATH = Path(r"C:\Program Files\Git\cmd\git.exe")
GIT_BYTES = 46_920
GIT_SHA256 = "7b7971dd13f0c3a284e538601f2f9770b3a87dfaccb5fb52d68141c67ed22364"

DEPENDENCY_RELATIVE_PATHS = (
    _projection.CONFIG_RELATIVE_PATH,
    _projection.CORRECTION_CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0448-retain-the-passing-split-runtime-fixed-width-device-preflight.md",
    "docs/decisions/ADR-0449-preregister-the-two-arm-literal-45-fit-projection.md",
    "docs/decisions/ADR-0450-correct-the-fit-projection-runtime-accounting-before-source.md",
    "docs/decisions/ADR-0451-source-seal-the-corrected-literal-45-fit-projector.md",
    "run_legal_river_quotient_fixed_width_actual45_fit_projection.py",
    "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection.py",
    "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_actual45_fit_projection_result.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_outcome.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_result.py",
    "src/pontius/durable_evidence_journal.py",
    "tests/test_legal_river_quotient_fixed_width_actual45_fit_projection.py",
    "artifacts/work_preflight/.gitattributes",
)


def _git(*arguments: str) -> bytes:
    if (
        not GIT_PATH.is_file()
        or GIT_PATH.stat().st_size != GIT_BYTES
        or sha256(GIT_PATH.read_bytes()).hexdigest() != GIT_SHA256
    ):
        raise RuntimeError("fit-projection Git identity differs")
    return subprocess.run(
        [str(GIT_PATH), *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def _canonical_lf_sha256(path: Path) -> str:
    raw = path.read_bytes()
    return sha256(raw.replace(bytes((13, 10)), bytes((10,)))).hexdigest()


def dependency_hashes() -> dict[str, str]:
    output = {}
    for relative in DEPENDENCY_RELATIVE_PATHS:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"fit-projection dependency is absent: {relative}")
        output[relative] = _canonical_lf_sha256(path)
    return output


def strict_source_commit() -> str:
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise RuntimeError("fit-projection owner requires a clean source seal")
    commit = _git("rev-parse", "HEAD").decode("ascii").strip()
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise RuntimeError("fit-projection source commit differs")
    return commit


def write_exclusive(path: Path, payload: bytes) -> None:
    if not isinstance(path, Path) or type(payload) is not bytes:
        raise TypeError("fit-projection exclusive writer arguments differ")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def run() -> Mapping[str, object]:
    if RESULT_PATH.exists():
        raise FileExistsError("fit-projection result is already consumed")
    _projection.verify_preregistered_contract()
    commit = strict_source_commit()
    if (
        not INPUT_PATH.is_file()
        or INPUT_PATH.stat().st_size != _projection.INPUT_BYTES
    ):
        raise FileNotFoundError("fit-projection parent artifact is absent")
    raw = INPUT_PATH.read_bytes()
    result = _projection.build_result(
        raw,
        source_commit=commit,
        dependency_hashes=dependency_hashes(),
    )
    payload = _projection.canonical_json_bytes(result)
    write_exclusive(RESULT_PATH, payload)
    from .legal_river_quotient_fixed_width_actual45_fit_projection_result import (
        rebind_projection_result_file,
    )

    rebind_projection_result_file(RESULT_PATH)
    return result


def main() -> int:
    if len(sys.argv) != 1:
        raise SystemExit("fit-projection owner accepts no arguments")
    result = run()
    projection = result["projection"]
    assert isinstance(projection, Mapping)
    print(
        f"terminal={projection['terminal']} "
        f"eligible={','.join(projection['projection_eligible_arms'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEPENDENCY_RELATIVE_PATHS",
    "INPUT_PATH",
    "RESULT_PATH",
    "dependency_hashes",
    "main",
    "run",
    "strict_source_commit",
    "write_exclusive",
]
