"""Exclusive no-argument owner for the ADR-0453 separation keystone."""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Mapping

from . import legal_river_quotient_selective_certified_separation as _source
from .legal_river_quotient_selective_certified_separation_result import (
    DEPENDENCY_RELATIVE_PATHS,
    rebind_selective_separation_file,
    verify_independent_contract,
)


ROOT = Path(__file__).parents[2]
RESULT_PATH = ROOT / _source.RESULT_RELATIVE_PATH
GIT_PATH = Path(r"C:\Program Files\Git\cmd\git.exe")
GIT_BYTES = 46_920
GIT_SHA256 = "7b7971dd13f0c3a284e538601f2f9770b3a87dfaccb5fb52d68141c67ed22364"


def _git(*arguments: str) -> bytes:
    if (
        not GIT_PATH.is_file()
        or GIT_PATH.stat().st_size != GIT_BYTES
        or sha256(GIT_PATH.read_bytes()).hexdigest() != GIT_SHA256
    ):
        raise RuntimeError("selective-separation Git identity differs")
    return subprocess.run(
        [str(GIT_PATH), *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def _canonical_lf_sha256(path: Path) -> str:
    raw = path.read_bytes()
    normalized = bytearray()
    index = 0
    while index < len(raw):
        if raw[index : index + 2] == bytes((13, 10)):
            normalized.append(10)
            index += 2
        else:
            normalized.append(raw[index])
            index += 1
    return sha256(bytes(normalized)).hexdigest()


def dependency_hashes() -> dict[str, str]:
    output = {}
    for relative in DEPENDENCY_RELATIVE_PATHS:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(
                f"selective-separation dependency is absent: {relative}"
            )
        output[relative] = _canonical_lf_sha256(path)
    return output


def strict_source_commit() -> str:
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise RuntimeError("selective-separation owner requires a clean source seal")
    commit = _git("rev-parse", "HEAD").decode("ascii").strip()
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise RuntimeError("selective-separation source commit differs")
    return commit


def write_exclusive(path: Path, payload: bytes) -> None:
    if path != RESULT_PATH or type(payload) is not bytes:
        raise ValueError("selective-separation exclusive writer arguments differ")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def run() -> Mapping[str, object]:
    if RESULT_PATH.exists():
        raise FileExistsError("selective-separation result is already consumed")
    _source.verify_preregistered_contract()
    verify_independent_contract()
    commit = strict_source_commit()
    result = _source.build_result(
        source_commit=commit,
        dependency_hashes=dependency_hashes(),
    )
    write_exclusive(RESULT_PATH, _source.canonical_json_bytes(result))
    rebind_selective_separation_file(RESULT_PATH)
    return result


def main() -> int:
    if len(sys.argv) != 1:
        raise SystemExit("selective-separation owner accepts no arguments")
    result = run()
    print(f"terminal={result['terminal']} rows={result['row_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEPENDENCY_RELATIVE_PATHS",
    "RESULT_PATH",
    "dependency_hashes",
    "main",
    "run",
    "strict_source_commit",
    "write_exclusive",
]
