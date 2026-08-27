"""Source-only repository launcher for the deferred-import calibration owner."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "src").resolve()
PUBLIC_PYCACHE_ENV = "PONTIUS_ADR0467_PUBLIC_SOURCE_PYCACHE"


def _source_extension_collisions() -> tuple[str, ...]:
    return tuple(
        sorted(
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in SOURCE.rglob("*")
            if path.is_file() and path.suffix.lower() in {".pyd", ".so"}
        )
    )


def _main() -> int:
    if len(sys.argv) != 1 or not sys.dont_write_bytecode:
        raise RuntimeError("deferred-import launcher requires no arguments and Python -B")
    collisions = _source_extension_collisions()
    if collisions:
        raise RuntimeError(
            "deferred-import source tree contains extension-module shadows: "
            + ", ".join(collisions)
        )
    with tempfile.TemporaryDirectory(
        prefix="pontius-adr0467-public-source-"
    ) as directory:
        prefix = (Path(directory).resolve() / "unused-pycache").resolve()
        if prefix.exists():
            raise RuntimeError("deferred-import launcher pycache prefix is not fresh")
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
        from pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner import (
            main,
        )

        return main()


if __name__ == "__main__":
    raise SystemExit(_main())
