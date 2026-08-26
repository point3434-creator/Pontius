"""Repository-root entry point for the ADR-0446 split-runtime successor."""

from __future__ import annotations

from pathlib import Path
import sys


_ROOT = Path(__file__).resolve().parent
_SRC = str(_ROOT / "src")
if not sys.path or sys.path[0] != _SRC:
    sys.path.insert(0, _SRC)

from pontius.legal_river_quotient_fixed_width_device_preflight_v3_runner import main


if __name__ == "__main__":
    raise SystemExit(main())
