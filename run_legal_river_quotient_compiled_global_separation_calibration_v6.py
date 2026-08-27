"""Source-only repository launcher for the ADR-0470 v6 calibration owner."""

from __future__ import annotations

import sys


if not sys.dont_write_bytecode or not sys.flags.safe_path:
    raise RuntimeError("v6 retained-attempt launcher requires Python -B -P")


import os
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "src").resolve()
PUBLIC_PYCACHE_ENV = "PONTIUS_ADR0471_PUBLIC_SOURCE_PYCACHE"


def _source_extension_collisions() -> tuple[str, ...]:
    return tuple(
        sorted(
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in SOURCE.rglob("*")
            if path.is_file() and path.suffix.lower() in {".pyd", ".so"}
        )
    )


def _main() -> int:
    if len(sys.argv) != 1 or not sys.dont_write_bytecode or not sys.flags.safe_path:
        raise RuntimeError("v6 retained-attempt launcher requires Python -B -P")
    collisions = _source_extension_collisions()
    if collisions:
        raise RuntimeError(
            "v6 retained-attempt source tree contains extension-module shadows: "
            + ", ".join(collisions)
        )
    with tempfile.TemporaryDirectory(
        prefix="pontius-adr0471-public-source-"
    ) as directory:
        prefix = (Path(directory).resolve() / "unused-pycache").resolve()
        if prefix.exists():
            raise RuntimeError(
                "v6 retained-attempt launcher pycache prefix is not fresh"
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
        from pontius.legal_river_quotient_compiled_global_separation_calibration_v6_runner import (
            _require_retained_predecessor_state,
            main,
        )

        _require_retained_predecessor_state()
        try:
            return main()
        finally:
            _require_retained_predecessor_state()


if __name__ == "__main__":
    raise SystemExit(_main())
