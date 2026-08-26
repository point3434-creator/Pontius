"""Self-contained repository launcher for the ADR-0422/0423 V2 owner."""

from __future__ import annotations

import os
from pathlib import Path
import runpy
import sys


_RUNNER_MODULE = (
    "pontius.legal_river_quotient_cuda_shared_direct_device_v2_runner"
)


def _resolved_repository() -> tuple[Path, Path]:
    root = Path(__file__).resolve().parent
    source = (root / "src").resolve()
    if (
        not (root / "pyproject.toml").is_file()
        or not (source / "pontius" / "__init__.py").is_file()
        or source.parent != root
    ):
        raise RuntimeError("shared-direct V2 repository geometry differs")
    return root, source


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("shared-direct V2 launcher accepts no arguments")
    root, source = _resolved_repository()
    source_text = str(source)
    sys.path[:] = [
        source_text,
        *(
            entry
            for entry in sys.path
            if entry and Path(entry).resolve() != source
        ),
    ]
    os.environ.pop("PYTHONPATH", None)
    os.environ.pop("PYTHONHOME", None)
    os.chdir(root)
    runpy.run_module(_RUNNER_MODULE, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
