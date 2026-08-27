"""Source-only repository launcher for the ADR-0473 v7 calibration owner."""

from __future__ import annotations

import sys


if not sys.dont_write_bytecode or not sys.flags.safe_path:
    raise RuntimeError("v7 authorization-phase launcher requires Python -B -P")


import os
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "src").resolve()
PUBLIC_PYCACHE_ENV = "PONTIUS_ADR0474_PUBLIC_SOURCE_PYCACHE"
PUBLIC_LIFECYCLE_ENV_NAMES = (
    "PONTIUS_ADR0473_COMPILED_SEPARATION_MODE",
    "PONTIUS_ADR0473_COMPILED_SEPARATION_CHALLENGE",
    "PONTIUS_ADR0473_COMPILED_SEPARATION_SPOOL",
    "PONTIUS_ADR0473_COMPILED_SEPARATION_LAUNCH_TOKEN",
    PUBLIC_PYCACHE_ENV,
)


def _source_extension_collisions() -> tuple[str, ...]:
    return tuple(
        sorted(
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in SOURCE.rglob("*")
            if path.is_file() and path.suffix.lower() in {".pyd", ".so"}
        )
    )


def _require_public_environment_absent() -> None:
    contaminated = tuple(
        sorted(name for name in PUBLIC_LIFECYCLE_ENV_NAMES if name in os.environ)
    )
    if contaminated:
        raise ValueError(
            "v7 authorization-phase launcher environment contains lifecycle names: "
            + ", ".join(contaminated)
        )


def _main() -> int:
    if len(sys.argv) != 1 or not sys.dont_write_bytecode or not sys.flags.safe_path:
        raise RuntimeError("v7 authorization-phase launcher requires Python -B -P")
    _require_public_environment_absent()
    collisions = _source_extension_collisions()
    if collisions:
        raise RuntimeError(
            "v7 authorization-phase source tree contains extension-module shadows: "
            + ", ".join(collisions)
        )
    with tempfile.TemporaryDirectory(
        prefix="pontius-adr0474-public-source-"
    ) as directory:
        prefix = (Path(directory).resolve() / "unused-pycache").resolve()
        if prefix.exists():
            raise RuntimeError(
                "v7 authorization-phase launcher pycache prefix is not fresh"
            )
        sys.pycache_prefix = str(prefix)
        root = str(ROOT)
        retained = []
        for entry in sys.path:
            if not entry:
                continue
            try:
                if str(Path(entry).resolve()) == root:
                    continue
            except (OSError, RuntimeError):
                continue
            retained.append(entry)
        sys.path[:] = [str(SOURCE), *retained]
        os.environ[PUBLIC_PYCACHE_ENV] = str(prefix)
        from pontius.legal_river_quotient_compiled_global_separation_calibration_v7_runner import (
            _authorization_tag,
            _require_retained_predecessor_state,
            _require_unopened_v7_lifecycle_state,
            main,
        )

        _require_retained_predecessor_state()
        _require_unopened_v7_lifecycle_state()
        authorization_tag = _authorization_tag()
        try:
            return main()
        finally:
            _require_retained_predecessor_state()
            if _authorization_tag() != authorization_tag:
                raise RuntimeError("v7 authorization tag changed during public launch")


if __name__ == "__main__":
    raise SystemExit(_main())
