"""Check legacy dependency drift and stabilization import boundaries."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import importlib.util
import os
from pathlib import Path
import stat
import sys
from types import ModuleType


BASELINE_RELATIVE_PATH = "docs/architecture/dependency-baseline.toml"
_ORCHESTRATION_SIBLING_PREFIX = "tools.test_orchestration"
EVIDENCE_ORIGIN_PATHS = frozenset(
    {
        "src/pontius/evidence/__init__.py",
        "src/pontius/evidence/authorization.py",
        "src/pontius/evidence/errors.py",
        "src/pontius/evidence/manifest.py",
        "src/pontius/evidence/model.py",
        "src/pontius/evidence/retained_v7.py",
    }
)
ORCHESTRATION_ORIGIN_PATHS = frozenset(
    {
        "tools/__init__.py",
        "tools/check_stabilization_boundaries.py",
        "tools/compare_run_summaries.py",
        "tools/generate_dependency_baseline.py",
        "tools/generate_evidence_manifests.py",
        "tools/generate_test_inventory.py",
        "tools/run_tests.py",
        "tools/stabilization_verification.py",
        "tools/test_child.py",
        "tools/test_orchestration/__init__.py",
        "tools/test_orchestration/configuration.py",
        "tools/test_orchestration/engine.py",
        "tools/test_orchestration/environment.py",
        "tools/test_orchestration/errors.py",
        "tools/test_orchestration/evidence_guard.py",
        "tools/test_orchestration/git.py",
        "tools/test_orchestration/model.py",
        "tools/test_orchestration/posix_group.py",
        "tools/test_orchestration/process.py",
        "tools/test_orchestration/protocol.py",
        "tools/test_orchestration/windows_job.py",
        "tools/test_orchestration/workspace.py",
    }
)


class BoundaryError(RuntimeError):
    """One or more deterministic architecture-boundary violations."""

    def __init__(self, violations: Sequence[str] | str) -> None:
        if isinstance(violations, str):
            normalized = (violations,)
        else:
            normalized = tuple(sorted(set(violations)))
        if not normalized:
            raise ValueError("a boundary error requires at least one violation")
        self.violations = normalized
        super().__init__("; ".join(normalized))


def _load_generator() -> ModuleType:
    path = Path(__file__).resolve().with_name("generate_dependency_baseline.py")
    spec = importlib.util.spec_from_file_location("_pontius_dependency_baseline", path)
    if spec is None or spec.loader is None:
        raise BoundaryError("dependency baseline implementation cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except (OSError, ImportError) as error:
        raise BoundaryError("dependency baseline implementation cannot be loaded") from error
    return module


_BASELINE = _load_generator()


def _raise_violations(violations: Sequence[str]) -> None:
    if violations:
        raise BoundaryError(violations)


def enforce_legacy_edges(baseline: object, current: object) -> None:
    """Require every mechanically grandfathered origin to retain its edge set."""

    baseline_modules = {name for name, _ in baseline.modules}
    current_modules = {name for name, _ in current.modules}
    baseline_edges = {name: set() for name in baseline_modules}
    current_edges = {name: set() for name in current_modules}
    for origin, target in baseline.edges:
        baseline_edges[origin].add(target)
    for origin, target in current.edges:
        current_edges[origin].add(target)
    violations: list[str] = []
    for missing in sorted(baseline_modules - current_modules):
        violations.append(f"legacy module is missing: {missing}")
    for added in sorted(current_modules - baseline_modules):
        if added != "pontius.evidence" and not added.startswith("pontius.evidence."):
            violations.append(f"new source module lacks stabilization classification: {added}")
    for origin in sorted(baseline_modules & current_modules):
        removed = baseline_edges[origin] - current_edges[origin]
        added = current_edges[origin] - baseline_edges[origin]
        if removed or added:
            detail = [f"legacy outgoing edges changed for {origin}"]
            detail.extend(f"removed {origin} -> {target}" for target in sorted(removed))
            detail.extend(f"added {origin} -> {target}" for target in sorted(added))
            violations.append(", ".join(detail))
    _raise_violations(violations)


def _cyclic_components(graph: object) -> set[tuple[str, ...]]:
    self_edges = {origin for origin, target in graph.edges if origin == target}
    return {
        tuple(component)
        for component in graph.sccs
        if len(component) > 1 or component[0] in self_edges
    }


def enforce_no_new_or_expanded_scc(baseline: object, current: object) -> None:
    allowed = _cyclic_components(baseline)
    violations = []
    for component in sorted(_cyclic_components(current)):
        if component not in allowed:
            violations.append(
                "new or expanded internal SCC: " + ", ".join(component)
            )
    _raise_violations(violations)


def _is_stdlib(target: str) -> bool:
    root = target.partition(".")[0]
    return root in sys.stdlib_module_names or root == "__future__"


def enforce_origin_classification(
    current_sources: Mapping[str, bytes], tool_sources: Mapping[str, bytes]
) -> None:
    """Reject stabilization origins that neither accepted plan declares."""

    violations = [
        f"unclassified stabilization origin: {path}"
        for path in sorted(current_sources)
        if path.startswith("src/pontius/evidence/") and path not in EVIDENCE_ORIGIN_PATHS
    ]
    violations.extend(
        f"unclassified stabilization origin: {path}"
        for path in sorted(tool_sources)
        if path.startswith("tools/") and path not in ORCHESTRATION_ORIGIN_PATHS
    )
    _raise_violations(violations)


def enforce_evidence_import_policy(sources: Mapping[str, bytes]) -> None:
    """Apply the exact active-evidence dependency allowlist."""

    violations: list[str] = []
    try:
        edges = _BASELINE.import_edges(sources)
    except _BASELINE.BaselineError as error:
        raise BoundaryError(f"evidence sources cannot be scanned: {error}") from error
    for origin, target in edges:
        if origin != "pontius.evidence" and not origin.startswith("pontius.evidence."):
            continue
        allowed = (
            _is_stdlib(target)
            or target == "pontius.durable_evidence_journal"
            or target == "pontius.evidence"
            or target.startswith("pontius.evidence.")
        )
        if not allowed:
            violations.append(f"forbidden evidence import: {origin} -> {target}")
    _raise_violations(violations)


def enforce_orchestration_import_policy(sources: Mapping[str, bytes]) -> None:
    """Keep orchestration tools on the standard library and declared siblings."""

    violations: list[str] = []
    try:
        edges = _BASELINE.import_edges(sources)
    except _BASELINE.BaselineError as error:
        raise BoundaryError(f"orchestration sources cannot be scanned: {error}") from error
    for origin, target in edges:
        if not origin.startswith("tools"):
            continue
        sibling = target == _ORCHESTRATION_SIBLING_PREFIX or target.startswith(
            _ORCHESTRATION_SIBLING_PREFIX + "."
        )
        if not _is_stdlib(target) and not sibling:
            violations.append(f"forbidden orchestration import: {origin} -> {target}")
    _raise_violations(violations)


def _is_reparse(info: os.stat_result) -> bool:
    return bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _read_regular_source(path: Path, *, root: Path) -> bytes:
    try:
        info = os.lstat(path)
    except OSError as error:
        raise BoundaryError(f"Python source cannot be inspected: {path}") from error
    if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISREG(info.st_mode):
        raise BoundaryError(f"Python source is not a regular nonreparse file: {path}")
    try:
        relative = path.relative_to(root).as_posix()
        raw = path.read_bytes()
    except (OSError, ValueError) as error:
        raise BoundaryError(
            f"Python source cannot be read below repository root: {path}"
        ) from error
    if len(raw) != info.st_size:
        raise BoundaryError(f"Python source changed while reading: {relative}")
    return raw


def _collect_sources(repository_root: Path, relative_root: str) -> dict[str, bytes]:
    base = repository_root / relative_root
    if not base.exists():
        return {}
    sources: dict[str, bytes] = {}
    for path in sorted(base.rglob("*.py")):
        relative = path.relative_to(repository_root).as_posix()
        sources[relative] = _read_regular_source(path, root=repository_root)
    return sources


def check_repository(repository_root: Path) -> None:
    try:
        root = repository_root.resolve(strict=True)
    except OSError as error:
        raise BoundaryError("repository root cannot be resolved") from error
    baseline_path = root / BASELINE_RELATIVE_PATH
    try:
        baseline_raw = _BASELINE._validated_regular_file(
            baseline_path, maximum_bytes=_BASELINE.MAXIMUM_BASELINE_BYTES
        )
        parsed = _BASELINE.parse_baseline_bytes(baseline_raw)
    except _BASELINE.BaselineError as error:
        raise BoundaryError(f"dependency baseline cannot be loaded: {error}") from error
    if parsed.baseline_commit != _BASELINE.BASELINE_COMMIT:
        raise BoundaryError("dependency baseline commit differs from stabilization baseline")
    current_sources = _collect_sources(root, "src/pontius")
    tool_sources = _collect_sources(root, "tools")
    try:
        current_graph = _BASELINE.scan_sources(current_sources)
    except _BASELINE.BaselineError as error:
        raise BoundaryError(f"current dependency graph cannot be derived: {error}") from error
    enforce_origin_classification(current_sources, tool_sources)
    enforce_legacy_edges(parsed.graph, current_graph)
    enforce_no_new_or_expanded_scc(parsed.graph, current_graph)
    enforce_evidence_import_policy(current_sources)
    enforce_orchestration_import_policy(tool_sources)


def parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    parse_arguments(argv)
    repository_root = Path(__file__).resolve().parents[1]
    try:
        check_repository(repository_root)
    except BoundaryError as error:
        print(f"stabilization boundary check failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
