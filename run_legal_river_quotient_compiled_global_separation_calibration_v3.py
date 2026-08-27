"""Repository-root launcher for the ADR-0463 launch-arity successor."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from pontius.legal_river_quotient_compiled_global_separation_calibration_v3_runner import (  # noqa: E402
    main,
)


if __name__ == "__main__":
    raise SystemExit(main())
