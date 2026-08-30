"""Helpers loaded by evidence tests without making ``tests`` importable."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def load_test_module(path: Path, name: str) -> ModuleType:
    """Load a test helper by its exact path under ``-P``."""
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load test module: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module
