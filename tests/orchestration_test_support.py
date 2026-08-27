"""Exact-path support for orchestration tests executed with ``-P``."""

from __future__ import annotations

import importlib.machinery
import importlib.util
from pathlib import Path
import sys
from types import ModuleType


PACKAGE_NAME = "pontius_test_orchestration"


def load_orchestration_modules(snapshot_root: Path) -> tuple[ModuleType, ModuleType, ModuleType]:
    """Load the tool package without adding a repository path to ``sys.path``."""
    package_root = snapshot_root / "tools" / "test_orchestration"
    for name in tuple(sys.modules):
        if name == PACKAGE_NAME or name.startswith(f"{PACKAGE_NAME}."):
            del sys.modules[name]

    package = ModuleType(PACKAGE_NAME)
    package.__file__ = str(package_root / "__init__.py")
    package.__package__ = PACKAGE_NAME
    package.__path__ = [str(package_root)]
    package_spec = importlib.machinery.ModuleSpec(PACKAGE_NAME, loader=None, is_package=True)
    package_spec.submodule_search_locations = [str(package_root)]
    package.__spec__ = package_spec
    sys.modules[PACKAGE_NAME] = package

    loaded: list[ModuleType] = []
    for short_name in ("errors", "model", "configuration"):
        full_name = f"{PACKAGE_NAME}.{short_name}"
        path = package_root / f"{short_name}.py"
        specification = importlib.util.spec_from_file_location(full_name, path)
        if specification is None or specification.loader is None:
            raise RuntimeError(f"cannot load orchestration module: {path}")
        module = importlib.util.module_from_spec(specification)
        sys.modules[full_name] = module
        specification.loader.exec_module(module)
        loaded.append(module)
    return loaded[0], loaded[1], loaded[2]
