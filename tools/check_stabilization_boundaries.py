"""Check legacy dependency drift and stabilization import boundaries."""

from __future__ import annotations

import argparse
import ast
from collections.abc import Mapping, Sequence
import importlib.util
import os
from pathlib import Path
import stat
import sys
from types import ModuleType


BASELINE_RELATIVE_PATH = "docs/architecture/dependency-baseline.toml"
APPROVED_BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
APPROVED_MODULE_COUNT = 470
APPROVED_EDGE_COUNT = 2577
APPROVED_EDGE_DIGEST = "c178ed92158da1c544abaf39ab14842721658a31f3f9246cbeb3e05e3e3da6ee"
APPROVED_SCC_COUNT = 469
APPROVED_SCC_DIGEST = "9987fddd06742fc2af87de7b8ebf79bc8b2dda7231260f7cc9efdcca18dff345"
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
V0A_ORIGIN_PATHS = frozenset(
    {
        "src/pontius/v0a/__init__.py",
        "src/pontius/v0a/clock.py",
        "src/pontius/v0a/model.py",
        "src/pontius/v0a/replay.py",
        "src/pontius/v0a/runtime.py",
        "src/pontius/v0a/trace.py",
    }
)
# ADR-0485 fixes the v0a package's permitted external dependencies. Only
# `replay` may additionally reach the public river evaluator and the
# complete-deal type, because it is the explicit-deal host; the policy modules
# must never see them.
V0A_PERMITTED_INTERNAL = frozenset(
    {
        "pontius.action_clock",
        "pontius.preparation_bank",
        "pontius.legal_decision_spine_v2",
        "pontius.no_limit_betting",
        "pontius.holdem_cards",
        "pontius.immutable_blueprint",
    }
)
V0A_HOST_ONLY_INTERNAL = frozenset({"pontius.river"})
V0A_HOST_MODULE = "pontius.v0a.replay"
ORCHESTRATION_ORIGIN_PATHS = frozenset(
    {
        "tools/__init__.py",
        "tools/check_stabilization_boundaries.py",
        "tools/ci_native_diagnostics.py",
        "tools/generate_retained_backup_manifest.py",
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


def authenticate_approved_baseline(parsed: object) -> None:
    """Authenticate the complete accepted graph instead of trusting its metadata."""

    graph = parsed.graph
    identity = (
        parsed.baseline_commit,
        len(graph.modules),
        len(graph.edges),
        _BASELINE.edges_sha256(graph.edges),
        len(graph.sccs),
        _BASELINE.sccs_sha256(graph.sccs),
    )
    approved = (
        APPROVED_BASELINE_COMMIT,
        APPROVED_MODULE_COUNT,
        APPROVED_EDGE_COUNT,
        APPROVED_EDGE_DIGEST,
        APPROVED_SCC_COUNT,
        APPROVED_SCC_DIGEST,
    )
    if identity != approved:
        raise BoundaryError("dependency baseline differs from the approved mechanical lock")


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
        classified = (
            added == "pontius.evidence"
            or added.startswith("pontius.evidence.")
            or added == "pontius.v0a"
            or added.startswith("pontius.v0a.")
        )
        if not classified:
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
        for path in sorted(current_sources)
        if path.startswith("src/pontius/v0a/") and path not in V0A_ORIGIN_PATHS
    )
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


def enforce_v0a_import_policy(sources: Mapping[str, bytes]) -> None:
    """Apply ADR-0485's exact v0a dependency allowlist.

    The policy modules may reach only the six permitted sealed kernels and
    their own siblings. The explicit-deal host is the sole module allowed the
    river evaluator and complete-deal type. Non-host modules cannot import the
    host or reference that type. This checks static trusted-component source,
    not reflection, fabricated names, or arbitrary Python dataflow.
    """

    violations: list[str] = []
    try:
        edges = _BASELINE.import_edges(sources)
        for path, raw in sorted(sources.items()):
            origin = _BASELINE.module_name_for_path(path)
            if not origin.startswith("pontius.v0a.") or origin == V0A_HOST_MODULE:
                continue
            tree = _BASELINE._parse_source(raw, relative_path=path)
            for node in ast.walk(tree):
                forbidden = False
                if isinstance(node, ast.ImportFrom):
                    base = _BASELINE._resolve_from_base(
                        origin,
                        is_package=path.endswith("/__init__.py"),
                        level=node.level,
                        imported_module=node.module,
                    )
                    forbidden = any(
                        alias.name == "SixSeatHoldemDeal"
                        or (alias.name == "*" and base == "pontius.holdem_cards")
                        for alias in node.names
                    )
                elif isinstance(node, ast.Name):
                    forbidden = node.id == "SixSeatHoldemDeal"
                elif isinstance(node, ast.Attribute):
                    forbidden = node.attr == "SixSeatHoldemDeal"
                if forbidden:
                    violations.append(
                        f"forbidden v0a complete-deal access: {origin}:{node.lineno} "
                        "(only the explicit-deal host may use SixSeatHoldemDeal)"
                    )
    except _BASELINE.BaselineError as error:
        raise BoundaryError(f"v0a sources cannot be scanned: {error}") from error
    for origin, target in edges:
        if origin != "pontius.v0a" and not origin.startswith("pontius.v0a."):
            continue
        sibling = target == "pontius.v0a" or target.startswith("pontius.v0a.")
        if sibling:
            if target == V0A_HOST_MODULE and origin != V0A_HOST_MODULE:
                violations.append(
                    f"forbidden v0a import: {origin} -> {target} "
                    "(the explicit-deal host is never imported by a policy module)"
                )
            continue
        if _is_stdlib(target):
            continue
        if target in V0A_PERMITTED_INTERNAL:
            continue
        if target in V0A_HOST_ONLY_INTERNAL and origin == V0A_HOST_MODULE:
            continue
        violations.append(f"forbidden v0a import: {origin} -> {target}")
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


def _read_regular_source(path: Path, *, root: Path) -> object:
    try:
        return _BASELINE.read_regular_snapshot(
            path,
            maximum_bytes=_BASELINE.MAXIMUM_SOURCE_BYTES,
            root=root,
        )
    except _BASELINE.BaselineError as error:
        raise BoundaryError(f"Python source cannot be snapshotted: {path}: {error}") from error


def _directory_inventory_identity(path: Path) -> tuple[int, ...]:
    try:
        info = os.lstat(path)
    except OSError as error:
        raise BoundaryError(f"Python inventory directory cannot be inspected: {path}") from error
    if (
        stat.S_ISLNK(info.st_mode)
        or _BASELINE._is_disallowed_reparse(info)
        or not stat.S_ISDIR(info.st_mode)
    ):
        raise BoundaryError(f"Python inventory has a non-directory or reparse: {path}")
    return _BASELINE._directory_identity(info)


def _python_inventory(
    repository_root: Path, relative_root: str
) -> tuple[bool, tuple[str, ...], tuple[tuple[str, tuple[int, ...]], ...]]:
    base = repository_root / relative_root
    if not os.path.lexists(base):
        return False, (), ()
    paths: list[str] = []
    directories: list[tuple[str, tuple[int, ...]]] = []

    def walk_error(error: OSError) -> None:
        raise BoundaryError(f"Python inventory cannot be walked: {base}") from error

    for current, names, filenames in os.walk(
        base, topdown=True, onerror=walk_error, followlinks=False
    ):
        directory = Path(current)
        relative_directory = directory.relative_to(repository_root).as_posix()
        directories.append(
            (relative_directory, _directory_inventory_identity(directory))
        )
        for name in tuple(names):
            child = directory / name
            _directory_inventory_identity(child)
        for filename in filenames:
            if filename.casefold().endswith(".py"):
                relative = (directory / filename).relative_to(repository_root).as_posix()
                if not filename.endswith(".py"):
                    raise BoundaryError(
                        f"Python inventory has a noncanonical Python suffix: {relative}"
                    )
                paths.append(relative)
    return True, tuple(sorted(paths)), tuple(sorted(directories))


class SourceInventory:
    """A complete source inventory with identities retained through policy work."""

    __slots__ = (
        "repository_root",
        "relative_root",
        "exists",
        "paths",
        "directories",
        "snapshots",
        "sources",
    )

    def __init__(
        self,
        repository_root: Path,
        relative_root: str,
        exists: bool,
        paths: Sequence[str],
        directories: Sequence[tuple[str, tuple[int, ...]]],
        snapshots: Mapping[str, object],
    ) -> None:
        self.repository_root = repository_root
        self.relative_root = relative_root
        self.exists = exists
        self.paths = tuple(paths)
        self.directories = tuple(directories)
        self.snapshots = dict(snapshots)
        self.sources = {
            relative: snapshot.raw for relative, snapshot in self.snapshots.items()
        }

    def revalidate(self) -> None:
        current = _python_inventory(self.repository_root, self.relative_root)
        if current != (self.exists, self.paths, self.directories):
            raise BoundaryError(
                f"Python source inventory changed: {self.relative_root}"
            )
        try:
            for snapshot in self.snapshots.values():
                snapshot.revalidate()
        except _BASELINE.BaselineError as error:
            raise BoundaryError(
                f"Python source identity changed: {self.relative_root}: {error}"
            ) from error


def _collect_sources(repository_root: Path, relative_root: str) -> SourceInventory:
    exists, paths, directories = _python_inventory(repository_root, relative_root)
    snapshots = {
        relative: _read_regular_source(repository_root / relative, root=repository_root)
        for relative in paths
    }
    inventory = SourceInventory(
        repository_root,
        relative_root,
        exists,
        paths,
        directories,
        snapshots,
    )
    inventory.revalidate()
    return inventory


def _revalidate_repository_snapshot(
    baseline: object,
    current: SourceInventory,
    tools: SourceInventory,
) -> None:
    try:
        baseline.revalidate()
    except _BASELINE.BaselineError as error:
        raise BoundaryError(f"dependency baseline identity changed: {error}") from error
    current.revalidate()
    tools.revalidate()


def check_repository(repository_root: Path) -> None:
    try:
        root = repository_root.resolve(strict=True)
    except OSError as error:
        raise BoundaryError("repository root cannot be resolved") from error
    baseline_path = root / BASELINE_RELATIVE_PATH
    try:
        baseline_snapshot = _BASELINE.read_regular_snapshot(
            baseline_path,
            maximum_bytes=_BASELINE.MAXIMUM_BASELINE_BYTES,
            root=root,
        )
        parsed = _BASELINE.parse_baseline_bytes(baseline_snapshot.raw)
    except _BASELINE.BaselineError as error:
        raise BoundaryError(f"dependency baseline cannot be loaded: {error}") from error
    authenticate_approved_baseline(parsed)
    current_inventory = _collect_sources(root, "src/pontius")
    tool_inventory = _collect_sources(root, "tools")
    current_sources = current_inventory.sources
    tool_sources = tool_inventory.sources
    _revalidate_repository_snapshot(
        baseline_snapshot, current_inventory, tool_inventory
    )
    try:
        current_graph = _BASELINE.scan_sources(current_sources)
    except _BASELINE.BaselineError as error:
        raise BoundaryError(f"current dependency graph cannot be derived: {error}") from error
    enforce_origin_classification(current_sources, tool_sources)
    enforce_legacy_edges(parsed.graph, current_graph)
    enforce_no_new_or_expanded_scc(parsed.graph, current_graph)
    enforce_evidence_import_policy(current_sources)
    enforce_v0a_import_policy(current_sources)
    enforce_orchestration_import_policy(tool_sources)
    _revalidate_repository_snapshot(
        baseline_snapshot, current_inventory, tool_inventory
    )


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
