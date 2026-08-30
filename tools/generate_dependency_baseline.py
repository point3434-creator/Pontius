"""Generate and verify the mechanical legacy Python dependency baseline.

This tool is standard-library-only.  It reads Python source from an exact Git
commit, parses imports with :mod:`ast`, and emits a canonical TOML lock.
"""

from __future__ import annotations

import argparse
import ast
from collections.abc import Mapping, Sequence
import ctypes
from hashlib import sha256
import io
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from typing import Any
import uuid

if os.name == "nt":
    from ctypes import wintypes
    import msvcrt


SCHEMA_VERSION = "pontius-dependency-baseline-v1"
BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
BASELINE_RELATIVE_PATH = "docs/architecture/dependency-baseline.toml"
MAXIMUM_ARCHIVE_BYTES = 64 * 1024 * 1024
MAXIMUM_BASELINE_BYTES = 4 * 1024 * 1024
MAXIMUM_SOURCE_BYTES = 16 * 1024 * 1024
_REPARSE_ATTRIBUTE = 0x400
_REPARSE_NAME_SURROGATE = 0x20000000
_CLOUD_REPARSE_BASE = 0x9000001A
_CLOUD_REPARSE_MASK = 0xFFFF0FFF
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class BaselineError(RuntimeError):
    """A deterministic dependency-baseline failure."""

    def __init__(
        self,
        message: str,
        *,
        failures: Sequence[BaseException] = (),
        retained_owners: Sequence[object] = (),
    ) -> None:
        self.failures = tuple(failures)
        self.retained_owners = tuple(retained_owners)
        super().__init__(message)


def _aggregate_errors(
    message: str,
    failures: Sequence[BaseException],
    *,
    retained_owners: Sequence[object] = (),
) -> BaselineError:
    ordered = tuple(failures)
    detail = "; ".join(f"{type(error).__name__}: {error}" for error in ordered)
    return BaselineError(
        f"{message}: {detail}",
        failures=ordered,
        retained_owners=retained_owners,
    )


class DependencyGraph:
    """Canonical module, internal-edge, and SCC rows."""

    __slots__ = ("modules", "edges", "sccs")

    def __init__(
        self,
        modules: Sequence[tuple[str, str]],
        edges: Sequence[tuple[str, str]],
        sccs: Sequence[Sequence[str]],
    ) -> None:
        self.modules = tuple((name, path) for name, path in modules)
        self.edges = tuple((origin, target) for origin, target in edges)
        self.sccs = tuple(tuple(component) for component in sccs)


class ParsedBaseline:
    """Validated baseline metadata and graph."""

    __slots__ = ("baseline_commit", "graph")

    def __init__(self, baseline_commit: str, graph: DependencyGraph) -> None:
        self.baseline_commit = baseline_commit
        self.graph = graph


def _require_exact_string(value: object, *, field: str) -> str:
    if type(value) is not str or not value:
        raise BaselineError(f"{field} must be a nonempty string")
    return value


def _require_exact_integer(value: object, *, field: str) -> int:
    if type(value) is not int or value < 0:
        raise BaselineError(f"{field} must be an exact nonnegative integer")
    return value


def _require_commit(value: object, *, field: str = "baseline_commit") -> str:
    text = _require_exact_string(value, field=field)
    if _HEX40.fullmatch(text) is None:
        raise BaselineError(f"{field} must be lowercase 40-hex")
    return text


def _require_digest(value: object, *, field: str) -> str:
    text = _require_exact_string(value, field=field)
    if _HEX64.fullmatch(text) is None:
        raise BaselineError(f"{field} must be lowercase 64-hex")
    return text


def _normalized_relative_path(value: object, *, field: str) -> str:
    text = _require_exact_string(value, field=field)
    if "\\" in text or "\x00" in text or "\r" in text or "\n" in text:
        raise BaselineError(f"{field} is not a normalized repository-relative path")
    posix = PurePosixPath(text)
    windows = PureWindowsPath(text)
    if (
        posix.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or text != posix.as_posix()
        or any(part in {"", ".", ".."} for part in posix.parts)
    ):
        raise BaselineError(f"{field} is not a normalized repository-relative path")
    return text


def module_name_for_path(relative_path: str) -> str:
    """Return the import name represented by a Python repository path."""

    normalized = _normalized_relative_path(relative_path, field="relative_path")
    path = PurePosixPath(normalized)
    if path.suffix != ".py":
        raise BaselineError(f"Python source path does not end in .py: {normalized}")
    parts = list(path.parts)
    if len(parts) >= 3 and parts[:2] == ["src", "pontius"]:
        module_parts = parts[1:]
    elif len(parts) >= 2 and parts[0] in {"tools", "tests"}:
        module_parts = parts
    else:
        raise BaselineError(f"Python source path has no supported module root: {normalized}")
    filename = module_parts[-1]
    module_parts[-1] = filename[:-3]
    if not module_parts or any(not part.isidentifier() for part in module_parts):
        raise BaselineError(f"Python source path has an invalid module name: {normalized}")
    return ".".join(module_parts)


def _is_package_path(relative_path: str) -> bool:
    return PurePosixPath(relative_path).name == "__init__.py"


def _package_import_name(module_name: str) -> str:
    if module_name.endswith(".__init__"):
        return module_name.removesuffix(".__init__")
    return module_name


def _resolve_from_base(
    origin: str,
    *,
    is_package: bool,
    level: int,
    imported_module: str | None,
) -> str:
    if level == 0:
        return imported_module or ""
    normalized_origin = _package_import_name(origin)
    package_parts = (
        normalized_origin.split(".")
        if is_package
        else normalized_origin.split(".")[:-1]
    )
    ascend = level - 1
    if ascend > len(package_parts):
        return ""
    base_parts = package_parts[: len(package_parts) - ascend]
    if imported_module:
        base_parts.extend(imported_module.split("."))
    return ".".join(base_parts)


def _longest_module_prefix(name: str, module_names: set[str]) -> str | None:
    candidate = name
    while candidate:
        if candidate in module_names:
            return candidate
        package_candidate = candidate + ".__init__"
        if package_candidate in module_names:
            return package_candidate
        candidate = candidate.rpartition(".")[0]
    return None


def _import_targets(
    tree: ast.AST,
    *,
    origin: str,
    is_package: bool,
    module_names: set[str],
    internal_only: bool,
) -> tuple[str, ...]:
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if internal_only:
                    resolved = _longest_module_prefix(alias.name, module_names)
                    if resolved is not None:
                        targets.add(resolved)
                else:
                    targets.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base = _resolve_from_base(
                origin,
                is_package=is_package,
                level=node.level,
                imported_module=node.module,
            )
            for alias in node.names:
                candidate = f"{base}.{alias.name}" if base and alias.name != "*" else base
                resolved = _longest_module_prefix(candidate, module_names)
                if resolved is None:
                    resolved = _longest_module_prefix(base, module_names)
                if internal_only:
                    if resolved is not None:
                        targets.add(resolved)
                else:
                    repository_namespace_root = base in {
                        "pontius",
                        "tests",
                        "experiments",
                        "tools",
                    }
                    targets.add(
                        resolved
                        or (
                            candidate
                            if repository_namespace_root and alias.name != "*"
                            else base
                        )
                        or candidate
                    )
    targets.discard("")
    return tuple(sorted(targets))


def _parse_source(raw: bytes, *, relative_path: str) -> ast.AST:
    if type(raw) is not bytes:
        raise BaselineError(f"source bytes are not bytes: {relative_path}")
    try:
        return ast.parse(raw, filename=relative_path)
    except (SyntaxError, ValueError) as error:
        raise BaselineError(f"Python source cannot be parsed: {relative_path}") from error


def import_edges(sources: Mapping[str, bytes]) -> tuple[tuple[str, str], ...]:
    """Return all syntactic import edges for policy checks.

    Internal imports are resolved to the most specific repository module.  Other
    imports retain their syntactic module name.  Imports beneath ``TYPE_CHECKING``
    are intentionally included because the scanner walks the complete AST.
    """

    module_by_path: dict[str, str] = {}
    for supplied_path in sources:
        path = _normalized_relative_path(supplied_path, field="source path")
        module_by_path[path] = module_name_for_path(path)
    if len(set(module_by_path.values())) != len(module_by_path):
        raise BaselineError("multiple Python paths resolve to one module")
    module_names = set(module_by_path.values())
    edges: set[tuple[str, str]] = set()
    for path, origin in sorted(module_by_path.items()):
        tree = _parse_source(sources[path], relative_path=path)
        for target in _import_targets(
            tree,
            origin=origin,
            is_package=_is_package_path(path),
            module_names=module_names,
            internal_only=False,
        ):
            edges.add((origin, target))
    return tuple(sorted(edges))


def _strongly_connected_components(
    module_names: Sequence[str], edges: Sequence[tuple[str, str]]
) -> tuple[tuple[str, ...], ...]:
    adjacency = {name: [] for name in module_names}
    for origin, target in edges:
        adjacency[origin].append(target)
    for targets in adjacency.values():
        targets.sort()

    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[tuple[str, ...]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in adjacency[node]:
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])
        if lowlinks[node] == indices[node]:
            members: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                members.append(member)
                if member == node:
                    break
            components.append(tuple(sorted(members)))

    for module_name in sorted(module_names):
        if module_name not in indices:
            visit(module_name)
    return tuple(sorted(components))


def scan_sources(sources: Mapping[str, bytes]) -> DependencyGraph:
    """Build the canonical internal ``pontius`` import graph from source bytes."""

    if not isinstance(sources, Mapping) or not sources:
        raise BaselineError("dependency source mapping must be nonempty")
    modules: list[tuple[str, str]] = []
    normalized_sources: dict[str, bytes] = {}
    for supplied_path, raw in sources.items():
        path = _normalized_relative_path(supplied_path, field="source path")
        module_name = module_name_for_path(path)
        if not module_name.startswith("pontius"):
            raise BaselineError(f"dependency graph source is outside pontius: {path}")
        if path in normalized_sources:
            raise BaselineError(f"duplicate dependency source path: {path}")
        normalized_sources[path] = raw
        modules.append((module_name, path))
    modules.sort()
    if len({name for name, _ in modules}) != len(modules):
        raise BaselineError("multiple dependency paths resolve to one module")
    module_names = {name for name, _ in modules}
    edges: set[tuple[str, str]] = set()
    for origin, path in modules:
        tree = _parse_source(normalized_sources[path], relative_path=path)
        for target in _import_targets(
            tree,
            origin=origin,
            is_package=_is_package_path(path),
            module_names=module_names,
            internal_only=True,
        ):
            edges.add((origin, target))
    ordered_edges = tuple(sorted(edges))
    sccs = _strongly_connected_components(
        tuple(name for name, _ in modules), ordered_edges
    )
    return DependencyGraph(tuple(modules), ordered_edges, sccs)


def edges_sha256(edges: Sequence[tuple[str, str]]) -> str:
    rows = sorted(set(tuple(edge) for edge in edges))
    raw = "".join(f"{origin}\t{target}\n" for origin, target in rows).encode("ascii")
    return sha256(raw).hexdigest()


def sccs_sha256(sccs: Sequence[Sequence[str]]) -> str:
    rows = sorted(tuple(sorted(component)) for component in sccs)
    raw = "".join("\t".join(component) + "\n" for component in rows).encode("ascii")
    return sha256(raw).hexdigest()


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def render_baseline(graph: DependencyGraph, *, baseline_commit: str) -> bytes:
    commit = _require_commit(baseline_commit)
    _validate_graph(graph)
    lines = [
        f"schema_version = {_toml_string(SCHEMA_VERSION)}",
        f"baseline_commit = {_toml_string(commit)}",
        f"module_count = {len(graph.modules)}",
        f"edge_count = {len(graph.edges)}",
        f"edges_sha256 = {_toml_string(edges_sha256(graph.edges))}",
        f"scc_count = {len(graph.sccs)}",
        f"sccs_sha256 = {_toml_string(sccs_sha256(graph.sccs))}",
    ]
    for module_name, relative_path in graph.modules:
        lines.extend(
            (
                "",
                "[[module]]",
                f"module_name = {_toml_string(module_name)}",
                f"relative_path = {_toml_string(relative_path)}",
            )
        )
    for origin, target in graph.edges:
        lines.extend(
            (
                "",
                "[[edge]]",
                f"origin = {_toml_string(origin)}",
                f"target = {_toml_string(target)}",
            )
        )
    for component in graph.sccs:
        members = ", ".join(_toml_string(member) for member in component)
        lines.extend(("", "[[scc]]", f"members = [{members}]"))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _exact_keys(value: object, expected: set[str], *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(type(key) is not str for key in value):
        raise BaselineError(f"{field} must be a TOML table")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise BaselineError(f"{field} keys differ: missing={missing}, extra={extra}")
    return value


def _table_array(value: object, *, field: str) -> list[object]:
    if type(value) is not list:
        raise BaselineError(f"{field} must be a TOML table array")
    return value


def _module_name(value: object, *, field: str) -> str:
    text = _require_exact_string(value, field=field)
    if any(not part.isidentifier() for part in text.split(".")) or not text.startswith(
        "pontius"
    ):
        raise BaselineError(f"{field} is not a valid pontius module name")
    return text


def _validate_graph(graph: DependencyGraph) -> None:
    modules = tuple(graph.modules)
    edges = tuple(graph.edges)
    sccs = tuple(tuple(component) for component in graph.sccs)
    if modules != tuple(sorted(modules)) or len(set(modules)) != len(modules):
        raise BaselineError("module rows must be sorted and unique")
    names: list[str] = []
    paths: list[str] = []
    for module_name, relative_path in modules:
        name = _module_name(module_name, field="module.module_name")
        path = _normalized_relative_path(relative_path, field="module.relative_path")
        if module_name_for_path(path) != name:
            raise BaselineError("module name does not match its repository path")
        names.append(name)
        paths.append(path)
    if len(set(names)) != len(names) or len(set(paths)) != len(paths):
        raise BaselineError("module names and paths must each be unique")
    name_set = set(names)
    if edges != tuple(sorted(edges)) or len(set(edges)) != len(edges):
        raise BaselineError("edge rows must be sorted and unique")
    for origin, target in edges:
        if origin not in name_set or target not in name_set:
            raise BaselineError("every edge endpoint must resolve to one module")
    normalized_sccs = tuple(tuple(component) for component in sccs)
    if normalized_sccs != tuple(sorted(normalized_sccs)) or len(set(normalized_sccs)) != len(
        normalized_sccs
    ):
        raise BaselineError("SCC rows must be sorted and unique")
    flattened: list[str] = []
    for component in normalized_sccs:
        if not component or component != tuple(sorted(component)) or len(set(component)) != len(
            component
        ):
            raise BaselineError("SCC members must be sorted, nonempty, and unique")
        if any(member not in name_set for member in component):
            raise BaselineError("every SCC member must resolve to one module")
        flattened.extend(component)
    if sorted(flattened) != sorted(names) or len(flattened) != len(names):
        raise BaselineError("every module must occur in exactly one SCC")
    computed = _strongly_connected_components(tuple(names), edges)
    if computed != normalized_sccs:
        raise BaselineError("SCC rows do not match the encoded edge graph")


def parse_baseline_bytes(raw: bytes) -> ParsedBaseline:
    if type(raw) is not bytes or len(raw) > MAXIMUM_BASELINE_BYTES:
        raise BaselineError("dependency baseline bytes are invalid or oversized")
    try:
        decoded = raw.decode("utf-8")
        document = tomllib.loads(decoded)
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise BaselineError("dependency baseline is not valid UTF-8 TOML") from error
    top = _exact_keys(
        document,
        {
            "schema_version",
            "baseline_commit",
            "module_count",
            "edge_count",
            "edges_sha256",
            "scc_count",
            "sccs_sha256",
            "module",
            "edge",
            "scc",
        },
        field="dependency baseline",
    )
    if _require_exact_string(top["schema_version"], field="schema_version") != SCHEMA_VERSION:
        raise BaselineError("dependency baseline schema version is unsupported")
    commit = _require_commit(top["baseline_commit"])
    module_count = _require_exact_integer(top["module_count"], field="module_count")
    edge_count = _require_exact_integer(top["edge_count"], field="edge_count")
    scc_count = _require_exact_integer(top["scc_count"], field="scc_count")
    expected_edge_digest = _require_digest(top["edges_sha256"], field="edges_sha256")
    expected_scc_digest = _require_digest(top["sccs_sha256"], field="sccs_sha256")

    modules: list[tuple[str, str]] = []
    for index, value in enumerate(_table_array(top["module"], field="module")):
        row = _exact_keys(value, {"module_name", "relative_path"}, field=f"module[{index}]")
        modules.append(
            (
                _module_name(row["module_name"], field=f"module[{index}].module_name"),
                _normalized_relative_path(
                    row["relative_path"], field=f"module[{index}].relative_path"
                ),
            )
        )
    edges: list[tuple[str, str]] = []
    for index, value in enumerate(_table_array(top["edge"], field="edge")):
        row = _exact_keys(value, {"origin", "target"}, field=f"edge[{index}]")
        edges.append(
            (
                _module_name(row["origin"], field=f"edge[{index}].origin"),
                _module_name(row["target"], field=f"edge[{index}].target"),
            )
        )
    sccs: list[tuple[str, ...]] = []
    for index, value in enumerate(_table_array(top["scc"], field="scc")):
        row = _exact_keys(value, {"members"}, field=f"scc[{index}]")
        members_value = row["members"]
        if type(members_value) is not list:
            raise BaselineError(f"scc[{index}].members must be an array")
        sccs.append(
            tuple(
                _module_name(member, field=f"scc[{index}].members")
                for member in members_value
            )
        )
    graph = DependencyGraph(modules, edges, sccs)
    _validate_graph(graph)
    if module_count != len(graph.modules):
        raise BaselineError("module_count does not match module rows")
    if edge_count != len(graph.edges):
        raise BaselineError("edge_count does not match edge rows")
    if scc_count != len(graph.sccs):
        raise BaselineError("scc_count does not match SCC rows")
    if expected_edge_digest != edges_sha256(graph.edges):
        raise BaselineError("edges_sha256 does not match canonical edge rows")
    if expected_scc_digest != sccs_sha256(graph.sccs):
        raise BaselineError("sccs_sha256 does not match canonical SCC rows")
    return ParsedBaseline(commit, graph)


def _is_supported_cloud_reparse_tag(tag: int) -> bool:
    return (
        type(tag) is int
        and tag & _REPARSE_NAME_SURROGATE == 0
        and tag & _CLOUD_REPARSE_MASK == _CLOUD_REPARSE_BASE
    )


def _is_any_reparse(info: os.stat_result) -> bool:
    return bool(
        int(getattr(info, "st_file_attributes", 0)) & _REPARSE_ATTRIBUTE
    ) or bool(int(getattr(info, "st_reparse_tag", 0)))


def _is_disallowed_reparse_values(attributes: int, tag: int) -> bool:
    has_reparse_metadata = bool(attributes & _REPARSE_ATTRIBUTE) or bool(tag)
    if not has_reparse_metadata:
        return False
    return not _is_supported_cloud_reparse_tag(tag)


def _is_disallowed_reparse(info: os.stat_result) -> bool:
    return _is_disallowed_reparse_values(
        int(getattr(info, "st_file_attributes", 0)),
        int(getattr(info, "st_reparse_tag", 0)),
    )


def _identity_reparse_values(
    info: os.stat_result,
    windows_metadata: tuple[int, int] | None = None,
) -> tuple[int, int]:
    if windows_metadata is not None:
        return windows_metadata
    return (
        int(getattr(info, "st_file_attributes", 0)),
        int(getattr(info, "st_reparse_tag", 0)),
    )


def _file_identity(
    info: os.stat_result,
    *,
    windows_metadata: tuple[int, int] | None = None,
) -> tuple[int, ...]:
    attributes, tag = _identity_reparse_values(info, windows_metadata)
    return (
        int(info.st_dev),
        int(info.st_ino),
        int(info.st_size),
        int(info.st_mtime_ns),
        int(info.st_ctime_ns),
        int(info.st_mode),
        attributes,
        tag,
    )


def _path_handle_identity(
    info: os.stat_result,
    *,
    windows_metadata: tuple[int, int] | None = None,
) -> tuple[int, ...]:
    """Return fields reported consistently by path and handle on Windows."""

    attributes, tag = _identity_reparse_values(info, windows_metadata)
    return (
        int(info.st_dev),
        int(info.st_ino),
        int(info.st_size),
        int(info.st_mtime_ns),
        int(info.st_mode),
        attributes,
        tag,
    )


def _path_handle_core_identity(info: os.stat_result) -> tuple[int, ...]:
    return _path_handle_identity(info)[:5]


def _path_matches_open_handle(
    path_info: os.stat_result,
    handle_info: os.stat_result,
    windows_metadata: tuple[int, int] | None,
) -> bool:
    if (
        _path_handle_core_identity(path_info)
        != _path_handle_core_identity(handle_info)
    ):
        return False
    if windows_metadata is None:
        return _path_handle_identity(path_info) == _path_handle_identity(handle_info)
    return _identity_reparse_values(path_info) == windows_metadata


def _directory_identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        int(info.st_dev),
        int(info.st_ino),
        int(info.st_mode),
        int(getattr(info, "st_file_attributes", 0)),
        int(getattr(info, "st_reparse_tag", 0)),
    )


def _is_retryable_windows_metadata_transition(
    before: os.stat_result,
    after: os.stat_result,
    before_identity: tuple[int, ...],
    after_identity: tuple[int, ...],
    before_windows_metadata: tuple[int, int] | None,
    after_windows_metadata: tuple[int, int] | None,
) -> bool:
    """Recognize only the ctime-only transition caused by OneDrive hydration."""

    return (
        os.name == "nt"
        and before_identity != after_identity
        and before_windows_metadata == after_windows_metadata
        and _path_handle_identity(
            before, windows_metadata=before_windows_metadata
        )
        == _path_handle_identity(after, windows_metadata=after_windows_metadata)
    )


def _validated_ancestor_chain(path: Path, root: Path) -> tuple[tuple[Path, tuple[int, ...]], ...]:
    if not path.is_absolute() or not root.is_absolute():
        raise BaselineError("secure snapshot paths must be absolute")
    try:
        path.relative_to(root)
    except ValueError as error:
        raise BaselineError("secure snapshot path is outside its repository root") from error
    ancestors: list[tuple[Path, tuple[int, ...]]] = []
    for component in reversed(path.parents):
        if component == component.parent:
            continue
        try:
            info = os.lstat(component)
        except OSError as error:
            raise BaselineError(
                f"dependency path ancestor cannot be inspected: {component}"
            ) from error
        if (
            stat.S_ISLNK(info.st_mode)
            or _is_disallowed_reparse(info)
            or not stat.S_ISDIR(info.st_mode)
        ):
            raise BaselineError(
                f"dependency path ancestor is not a nonreparse directory: {component}"
            )
        ancestors.append((component, _directory_identity(info)))
    return tuple(ancestors)


def _revalidate_ancestor_chain(
    ancestors: Sequence[tuple[Path, tuple[int, ...]]],
) -> None:
    for component, expected in ancestors:
        try:
            info = os.lstat(component)
        except OSError as error:
            raise BaselineError(
                f"dependency path ancestor disappeared: {component}"
            ) from error
        if (
            stat.S_ISLNK(info.st_mode)
            or _is_disallowed_reparse(info)
            or not stat.S_ISDIR(info.st_mode)
            or _directory_identity(info) != expected
        ):
            raise BaselineError(
                f"dependency path ancestor identity changed: {component}"
            )


def _windows_path_api() -> tuple[Any, Any, Any]:
    if os.name != "nt":
        raise BaselineError("Windows no-follow file APIs are unavailable")
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create = kernel32.CreateFileW
        create.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        )
        create.restype = wintypes.HANDLE
        information = kernel32.GetFileInformationByHandleEx
        information.argtypes = (
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
        )
        information.restype = wintypes.BOOL
        close = kernel32.CloseHandle
        close.argtypes = (wintypes.HANDLE,)
        close.restype = wintypes.BOOL
    except Exception as error:
        raise BaselineError("Windows no-follow file APIs are unavailable") from error
    return create, information, close


def _windows_regular_handle_metadata(
    descriptor: int, path: Path
) -> tuple[int, int]:
    if os.name != "nt":
        raise BaselineError("Windows regular-file metadata is unavailable")
    try:
        handle = msvcrt.get_osfhandle(descriptor)
        _, information, _ = _windows_path_api()
        value = _WindowsFileAttributeTagInformation()
        succeeded = information(
            wintypes.HANDLE(handle),
            9,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception as error:
        raise BaselineError(
            f"dependency file handle metadata cannot be inspected: {path}"
        ) from error
    if not succeeded:
        error = ctypes.get_last_error()
        raise BaselineError(
            f"dependency file handle metadata cannot be inspected: {path}"
        ) from OSError(error, os.strerror(error), str(path))
    return int(value.FileAttributes), int(value.ReparseTag)


def _open_regular_no_follow(path: Path) -> int:
    if os.name != "nt":
        if not hasattr(os, "O_NOFOLLOW"):
            raise BaselineError("secure no-follow file opens are unavailable")
        flags = (
            os.O_RDONLY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_BINARY", 0)
        )
        try:
            return os.open(path, flags)
        except OSError as error:
            raise BaselineError(
                f"dependency file cannot be opened without links: {path}"
            ) from error

    create, _, close = _windows_path_api()
    try:
        handle = create(
            str(path),
            0x80000000,
            0x00000001 | 0x00000002 | 0x00000004,
            None,
            3,
            0x00200000 | 0x08000000,
            None,
        )
    except Exception as error:
        raise BaselineError(f"dependency file cannot be opened without reparses: {path}") from error
    invalid = ctypes.c_void_p(-1).value
    if not handle or int(handle) == invalid:
        error = ctypes.get_last_error()
        raise BaselineError(
            f"dependency file cannot be opened without reparses: {path}"
        ) from OSError(error, os.strerror(error), str(path))
    try:
        return msvcrt.open_osfhandle(
            int(handle), os.O_RDONLY | getattr(os, "O_BINARY", 0)
        )
    except (OSError, OverflowError) as error:
        numeric = int(handle)
        binding_failure = BaselineError(
            f"dependency file handle cannot be bound: {path}",
            failures=(error,),
        )
        try:
            succeeded = close(wintypes.HANDLE(numeric))
        except Exception as cleanup_error:
            raise _aggregate_errors(
                "dependency file binding and handle cleanup both failed",
                (binding_failure, cleanup_error),
                retained_owners=(numeric,),
            ) from error
        if not succeeded:
            code = ctypes.get_last_error()
            cleanup_error = OSError(code, os.strerror(code), str(path))
            raise _aggregate_errors(
                "dependency file binding and handle cleanup both failed",
                (binding_failure, cleanup_error),
                retained_owners=(numeric,),
            ) from error
        raise binding_failure from error


class FileSnapshot:
    """Bytes and filesystem identities retained for a later final pass."""

    __slots__ = (
        "path",
        "raw",
        "identity",
        "ancestors",
        "maximum_bytes",
        "root",
    )

    def __init__(
        self,
        path: Path,
        raw: bytes,
        identity: tuple[int, ...],
        ancestors: Sequence[tuple[Path, tuple[int, ...]]],
        maximum_bytes: int,
        root: Path,
    ) -> None:
        self.path = path
        self.raw = raw
        self.identity = identity
        self.ancestors = tuple(ancestors)
        self.maximum_bytes = maximum_bytes
        self.root = root

    def revalidate(self) -> None:
        current = read_regular_snapshot(
            self.path,
            maximum_bytes=self.maximum_bytes,
            root=self.root,
        )
        if current.identity != self.identity:
            raise BaselineError(f"dependency file identity changed: {self.path}")
        if current.raw != self.raw:
            raise BaselineError(f"dependency file content changed: {self.path}")


def read_regular_snapshot(
    path: Path,
    *,
    maximum_bytes: int,
    root: Path,
    _allow_windows_metadata_retry: bool = True,
) -> FileSnapshot:
    """Read one bounded, identity-bound, nonlink filesystem snapshot."""

    if type(maximum_bytes) is not int or maximum_bytes < 0:
        raise BaselineError("dependency snapshot bound is invalid")
    ancestors = _validated_ancestor_chain(path, root)
    try:
        before_path = os.lstat(path)
    except OSError as error:
        raise BaselineError(f"dependency file cannot be inspected: {path}") from error
    if (
        stat.S_ISLNK(before_path.st_mode)
        or _is_disallowed_reparse(before_path)
        or not stat.S_ISREG(before_path.st_mode)
    ):
        raise BaselineError(f"dependency path is not a regular nonreparse file: {path}")
    if before_path.st_size > maximum_bytes:
        raise BaselineError(f"dependency file is oversized: {path}")

    descriptor = _open_regular_no_follow(path)
    after_handle: os.stat_result | None = None
    before_windows_metadata: tuple[int, int] | None = None
    after_windows_metadata: tuple[int, int] | None = None
    retry_metadata_transition = False
    try:
        if os.name == "nt":
            before_windows_metadata = _windows_regular_handle_metadata(
                descriptor, path
            )
        before_handle = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before_handle.st_mode)
            or (
                before_windows_metadata is None
                and _is_disallowed_reparse(before_handle)
            )
            or (
                before_windows_metadata is not None
                and _is_disallowed_reparse_values(*before_windows_metadata)
            )
            or not _path_matches_open_handle(
                before_path, before_handle, before_windows_metadata
            )
        ):
            raise BaselineError(f"dependency file changed while opening: {path}")
        chunks: list[bytes] = []
        length = 0
        while length <= maximum_bytes:
            chunk = os.read(descriptor, min(1024 * 1024, maximum_bytes + 1 - length))
            if not chunk:
                break
            chunks.append(chunk)
            length += len(chunk)
        raw = b"".join(chunks)
        after_handle = os.fstat(descriptor)
        if os.name == "nt":
            after_windows_metadata = _windows_regular_handle_metadata(
                descriptor, path
            )
        if len(raw) > maximum_bytes:
            raise BaselineError(f"dependency file is oversized: {path}")
        before_identity = _file_identity(
            before_handle, windows_metadata=before_windows_metadata
        )
        after_identity = _file_identity(
            after_handle, windows_metadata=after_windows_metadata
        )
        if len(raw) != before_handle.st_size or before_identity != after_identity:
            if (
                _allow_windows_metadata_retry
                and len(raw) == before_handle.st_size
                and _is_retryable_windows_metadata_transition(
                    before_handle,
                    after_handle,
                    before_identity,
                    after_identity,
                    before_windows_metadata,
                    after_windows_metadata,
                )
            ):
                retry_metadata_transition = True
            else:
                raise BaselineError(
                    f"opened dependency file changed while reading: {path}"
                )
    except OSError as error:
        raise BaselineError(f"dependency file cannot be read: {path}") from error
    finally:
        try:
            os.close(descriptor)
        except OSError as error:
            raise BaselineError(f"dependency file handle cannot be closed: {path}") from error

    assert after_handle is not None
    if retry_metadata_transition:
        _revalidate_ancestor_chain(ancestors)
        return read_regular_snapshot(
            path,
            maximum_bytes=maximum_bytes,
            root=root,
            _allow_windows_metadata_retry=False,
        )
    try:
        after_path = os.lstat(path)
    except OSError as error:
        raise BaselineError(f"dependency file disappeared after reading: {path}") from error
    if (
        stat.S_ISLNK(after_path.st_mode)
        or _is_disallowed_reparse(after_path)
        or not _path_matches_open_handle(
            after_path, after_handle, after_windows_metadata
        )
    ):
        raise BaselineError(f"dependency file identity changed after reading: {path}")
    _revalidate_ancestor_chain(ancestors)
    return FileSnapshot(
        path,
        raw,
        _file_identity(after_handle, windows_metadata=after_windows_metadata),
        ancestors,
        maximum_bytes,
        root,
    )


def _validated_regular_file(path: Path, *, maximum_bytes: int) -> bytes:
    if not isinstance(path, Path) or not path.is_absolute():
        raise BaselineError("dependency baseline path must be absolute")
    return read_regular_snapshot(
        path, maximum_bytes=maximum_bytes, root=path.parent
    ).raw


def _git_environment(git_executable: Path) -> dict[str, str]:
    allowed = ("SystemRoot", "WINDIR", "ComSpec", "PATHEXT", "TEMP", "TMP", "TMPDIR")
    folded = {key.casefold(): value for key, value in os.environ.items()}
    environment = {key: folded[key.casefold()] for key in allowed if key.casefold() in folded}
    temporary = str(Path(tempfile.gettempdir()).resolve())
    environment["HOME"] = temporary
    environment["USERPROFILE"] = temporary
    if os.name == "nt":
        system_root = Path(os.environ.get("SystemRoot", "C:/Windows"))
        environment["PATH"] = os.pathsep.join(
            (str(git_executable.parent), str(system_root / "System32"))
        )
    else:
        environment["PATH"] = os.pathsep.join((str(git_executable.parent), "/usr/bin", "/bin"))
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "NUL" if os.name == "nt" else "/dev/null",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_LITERAL_PATHSPECS": "1",
        }
    )
    return environment


def _validated_git_executable(executable: Path) -> Path:
    if not isinstance(executable, Path) or not executable.is_absolute():
        raise BaselineError("Git executable must be an absolute path")
    try:
        resolved = executable.resolve(strict=True)
        info = os.lstat(resolved)
    except OSError as error:
        raise BaselineError("Git executable is unavailable") from error
    if (
        os.path.normcase(str(resolved)) != os.path.normcase(str(executable))
        or stat.S_ISLNK(info.st_mode)
        or _is_any_reparse(info)
        or not stat.S_ISREG(info.st_mode)
    ):
        raise BaselineError("Git executable identity is invalid")
    return resolved


def _run_git_archive(
    repository_root: Path, *, baseline_commit: str, git_executable: Path
) -> bytes:
    executable = _validated_git_executable(git_executable)
    command = [
        str(executable),
        "archive",
        "--format=tar",
        baseline_commit,
        "--",
        "src/pontius",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=repository_root,
            env=_git_environment(executable),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise BaselineError("Git archive command failed") from error
    if completed.returncode != 0 or len(completed.stderr) > 1024 * 1024:
        raise BaselineError("Git archive command did not produce the baseline")
    if len(completed.stdout) > MAXIMUM_ARCHIVE_BYTES:
        raise BaselineError("Git archive exceeds the dependency-source bound")
    return completed.stdout


def _sources_from_archive(raw: bytes) -> dict[str, bytes]:
    sources: dict[str, bytes] = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
            for member in archive:
                if member.isdir():
                    continue
                path = _normalized_relative_path(member.name, field="Git archive path")
                if not member.isfile():
                    raise BaselineError(f"Git archive contains a nonregular path: {path}")
                if not path.startswith("src/pontius/") or not path.endswith(".py"):
                    continue
                stream = archive.extractfile(member)
                if stream is None:
                    raise BaselineError(f"Git archive source cannot be read: {path}")
                content = stream.read()
                if len(content) != member.size:
                    raise BaselineError(f"Git archive source is truncated: {path}")
                if path in sources:
                    raise BaselineError(f"Git archive repeats a Python path: {path}")
                sources[path] = content
    except (tarfile.TarError, OSError) as error:
        raise BaselineError("Git archive is not a valid bounded tar stream") from error
    return sources


def derive_baseline_graph(
    repository_root: Path,
    *,
    baseline_commit: str = BASELINE_COMMIT,
    git_executable: Path,
) -> DependencyGraph:
    commit = _require_commit(baseline_commit)
    try:
        root = repository_root.resolve(strict=True)
    except OSError as error:
        raise BaselineError("repository root cannot be resolved") from error
    raw = _run_git_archive(root, baseline_commit=commit, git_executable=git_executable)
    return scan_sources(_sources_from_archive(raw))


def _validated_directory(path: Path, *, description: str) -> tuple[int, ...]:
    try:
        info = os.lstat(path)
    except OSError as error:
        raise BaselineError(f"{description} cannot be inspected: {path}") from error
    if (
        stat.S_ISLNK(info.st_mode)
        or _is_disallowed_reparse(info)
        or not stat.S_ISDIR(info.st_mode)
    ):
        raise BaselineError(f"{description} is not a nonreparse directory: {path}")
    return _directory_identity(info)


def validate_write_destination(repository_root: Path, destination: Path) -> Path:
    if not isinstance(destination, Path) or not destination.is_absolute():
        raise BaselineError("--write must explicitly name an absolute baseline path")
    if not isinstance(repository_root, Path) or not repository_root.is_absolute():
        raise BaselineError("repository root must be absolute for --write")
    root = Path(os.path.abspath(repository_root))
    for component in reversed(root.parents):
        if component != component.parent:
            _validated_directory(component, description="repository ancestor")
    _validated_directory(root, description="repository root")
    docs = root / "docs"
    _validated_directory(docs, description="baseline docs ancestor")
    architecture = docs / "architecture"
    _validated_directory(architecture, description="baseline architecture directory")
    expected = architecture / "dependency-baseline.toml"
    candidate = Path(os.path.abspath(destination))
    if os.path.normcase(str(candidate)) != os.path.normcase(str(expected)):
        raise BaselineError("--write may name only docs/architecture/dependency-baseline.toml")
    if os.path.lexists(candidate):
        info = os.lstat(candidate)
        if stat.S_ISLNK(info.st_mode) or _is_disallowed_reparse(info) or not stat.S_ISREG(info.st_mode):
            raise BaselineError("baseline destination is not a regular file")
    return candidate


if os.name == "nt":
    class _WindowsDirectoryInformation(ctypes.Structure):
        _fields_ = (
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        )


    class _WindowsFileAttributeTagInformation(ctypes.Structure):
        _fields_ = (
            ("FileAttributes", wintypes.DWORD),
            ("ReparseTag", wintypes.DWORD),
        )


    class _WindowsFileId128(ctypes.Structure):
        _fields_ = (("ByteIdentifier", ctypes.c_ubyte * 16),)


    class _WindowsFileIdInformation(ctypes.Structure):
        _fields_ = (
            ("VolumeSerialNumber", ctypes.c_ulonglong),
            ("FileId", _WindowsFileId128),
        )


    class _WindowsUnicodeString(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.USHORT),
            ("MaximumLength", wintypes.USHORT),
            ("Buffer", wintypes.LPWSTR),
        )


    class _WindowsObjectAttributes(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(_WindowsUnicodeString)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", wintypes.LPVOID),
            ("SecurityQualityOfService", wintypes.LPVOID),
        )


    class _WindowsIOStatusValue(ctypes.Union):
        _fields_ = (("Status", wintypes.LONG), ("Pointer", wintypes.LPVOID))


    class _WindowsIOStatusBlock(ctypes.Structure):
        _anonymous_ = ("value",)
        _fields_ = (("value", _WindowsIOStatusValue), ("Information", ctypes.c_size_t))


    class _WindowsFileRenameInformation(ctypes.Structure):
        _fields_ = (
            ("ReplaceIfExists", ctypes.c_ubyte),
            ("RootDirectory", wintypes.HANDLE),
            ("FileNameLength", wintypes.DWORD),
            ("FileName", wintypes.WCHAR * 1),
        )


    class _WindowsFileDispositionInformation(ctypes.Structure):
        _fields_ = (("DeleteFile", ctypes.c_ubyte),)


def _windows_directory_api() -> tuple[Any, Any, Any, Any]:
    if os.name != "nt":
        raise BaselineError("Windows directory handle APIs are unavailable")
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create = kernel32.CreateFileW
        create.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        )
        create.restype = wintypes.HANDLE
        information = kernel32.GetFileInformationByHandle
        information.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(_WindowsDirectoryInformation),
        )
        information.restype = wintypes.BOOL
        extended_information = kernel32.GetFileInformationByHandleEx
        extended_information.argtypes = (
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
        )
        extended_information.restype = wintypes.BOOL
        close = kernel32.CloseHandle
        close.argtypes = (wintypes.HANDLE,)
        close.restype = wintypes.BOOL
    except Exception as error:
        raise BaselineError("Windows directory handle APIs are unavailable") from error
    return create, information, extended_information, close


def _windows_directory_handle_identity(handle: int, path: Path) -> tuple[int, bytes]:
    _, information, extended_information, _ = _windows_directory_api()
    value = _WindowsDirectoryInformation()
    try:
        succeeded = information(wintypes.HANDLE(handle), ctypes.byref(value))
    except Exception as error:
        raise BaselineError(f"baseline directory handle cannot be inspected: {path}") from error
    if not succeeded:
        error = ctypes.get_last_error()
        raise BaselineError(
            f"baseline directory handle cannot be inspected: {path}"
        ) from OSError(error, os.strerror(error), str(path))
    tag_information = _WindowsFileAttributeTagInformation()
    try:
        succeeded = extended_information(
            wintypes.HANDLE(handle),
            9,
            ctypes.byref(tag_information),
            ctypes.sizeof(tag_information),
        )
    except Exception as error:
        raise BaselineError(
            f"baseline directory reparse tag cannot be inspected: {path}"
        ) from error
    if not succeeded:
        error = ctypes.get_last_error()
        raise BaselineError(
            f"baseline directory reparse tag cannot be inspected: {path}"
        ) from OSError(error, os.strerror(error), str(path))
    attributes = int(tag_information.FileAttributes)
    if attributes != int(value.dwFileAttributes):
        raise BaselineError(f"baseline directory attributes are inconsistent: {path}")
    if not attributes & 0x10 or _is_disallowed_reparse_values(
        attributes, int(tag_information.ReparseTag)
    ):
        raise BaselineError(f"baseline directory handle has a disallowed reparse: {path}")
    identity = _WindowsFileIdInformation()
    try:
        succeeded = extended_information(
            wintypes.HANDLE(handle),
            18,
            ctypes.byref(identity),
            ctypes.sizeof(identity),
        )
    except Exception as error:
        raise BaselineError(f"baseline directory identity cannot be inspected: {path}") from error
    if not succeeded:
        error = ctypes.get_last_error()
        raise BaselineError(
            f"baseline directory identity cannot be inspected: {path}"
        ) from OSError(error, os.strerror(error), str(path))
    file_id = bytes(identity.FileId.ByteIdentifier)
    return int(identity.VolumeSerialNumber), file_id


def _windows_open_directory(path: Path) -> tuple[int, tuple[int, bytes]]:
    create, _, _, _ = _windows_directory_api()
    try:
        handle = create(
            str(path),
            0x00000020 | 0x00000080 | 0x00100000,
            0x00000001 | 0x00000002 | 0x00000004,
            None,
            3,
            0x02000000 | 0x00200000,
            None,
        )
    except Exception as error:
        raise BaselineError(f"baseline directory handle cannot be opened: {path}") from error
    invalid = ctypes.c_void_p(-1).value
    if not handle or int(handle) == invalid:
        error = ctypes.get_last_error()
        raise BaselineError(
            f"baseline directory handle cannot be opened: {path}"
        ) from OSError(error, os.strerror(error), str(path))
    numeric = int(handle)
    try:
        return numeric, _windows_directory_handle_identity(numeric, path)
    except BaseException as body_error:
        try:
            _windows_close_directory(numeric)
        except BaselineError as cleanup_error:
            raise _aggregate_errors(
                "baseline directory inspection and close both failed",
                (body_error, cleanup_error),
                retained_owners=cleanup_error.retained_owners,
            ) from body_error
        raise


def _windows_close_directory(handle: int) -> None:
    try:
        _, _, _, close = _windows_directory_api()
        succeeded = close(wintypes.HANDLE(handle))
    except Exception as error:
        raise _aggregate_errors(
            "baseline directory handle close outcome is ambiguous",
            (error,),
            retained_owners=(handle,),
        ) from error
    if succeeded:
        return
    error = ctypes.get_last_error()
    cause = OSError(error, os.strerror(error))
    raise _aggregate_errors(
        "baseline directory handle close outcome is ambiguous",
        (cause,),
        retained_owners=(handle,),
    ) from cause


def _windows_file_api() -> tuple[Any, Any, Any, Any, Any]:
    if os.name != "nt":
        raise BaselineError("Windows handle-relative file APIs are unavailable")
    try:
        ntdll = ctypes.WinDLL("ntdll")
        create = ntdll.NtCreateFile
        create.argtypes = (
            ctypes.POINTER(wintypes.HANDLE),
            wintypes.DWORD,
            ctypes.POINTER(_WindowsObjectAttributes),
            ctypes.POINTER(_WindowsIOStatusBlock),
            wintypes.LPVOID,
            wintypes.ULONG,
            wintypes.ULONG,
            wintypes.ULONG,
            wintypes.ULONG,
            wintypes.LPVOID,
            wintypes.ULONG,
        )
        create.restype = wintypes.LONG
        set_information = ntdll.NtSetInformationFile
        set_information.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(_WindowsIOStatusBlock),
            wintypes.LPVOID,
            wintypes.ULONG,
            ctypes.c_int,
        )
        set_information.restype = wintypes.LONG
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        write = kernel32.WriteFile
        write.argtypes = (
            wintypes.HANDLE,
            wintypes.LPCVOID,
            wintypes.DWORD,
            wintypes.LPDWORD,
            wintypes.LPVOID,
        )
        write.restype = wintypes.BOOL
        flush = kernel32.FlushFileBuffers
        flush.argtypes = (wintypes.HANDLE,)
        flush.restype = wintypes.BOOL
        close = kernel32.CloseHandle
        close.argtypes = (wintypes.HANDLE,)
        close.restype = wintypes.BOOL
    except Exception as error:
        raise BaselineError("Windows handle-relative file APIs are unavailable") from error
    return create, set_information, write, flush, close


def _validated_relative_name(name: str) -> str:
    if (
        type(name) is not str
        or not name
        or name in {".", ".."}
        or any(character in name for character in ("/", "\\", ":", "\x00"))
    ):
        raise BaselineError("baseline mutation name must be one relative component")
    return name


def _windows_create_relative_file(
    directory_handle: int,
    name: str,
    *,
    owner: "_StagedBaseline | None" = None,
) -> int:
    name = _validated_relative_name(name)
    create, _, _, _, _ = _windows_file_api()
    encoded = name.encode("utf-16-le")
    if len(encoded) > 0xFFFE:
        raise BaselineError("baseline temporary name is too long")
    name_buffer = ctypes.create_unicode_buffer(name)
    unicode_name = _WindowsUnicodeString(
        len(encoded), len(encoded), ctypes.cast(name_buffer, wintypes.LPWSTR)
    )
    attributes = _WindowsObjectAttributes(
        ctypes.sizeof(_WindowsObjectAttributes),
        wintypes.HANDLE(directory_handle),
        ctypes.pointer(unicode_name),
        0x40,
        None,
        None,
    )
    status_block = _WindowsIOStatusBlock()
    handle = wintypes.HANDLE()
    candidate = owner or _StagedBaseline(name, None)
    try:
        status = int(
            create(
                ctypes.byref(handle),
                0x00000002 | 0x00000080 | 0x00010000 | 0x00100000,
                ctypes.byref(attributes),
                ctypes.byref(status_block),
                None,
                0x80,
                0,
                2,
                0x20 | 0x40,
                None,
                0,
            )
        )
    except Exception as error:
        invalid = ctypes.c_void_p(-1).value
        if handle.value and int(handle.value) != invalid:
            candidate.handle = int(handle.value)
            candidate.state = "open"
        failure = BaselineError("baseline temporary file could not be created")
        if owner is None and candidate.handle is not None:
            try:
                _cleanup_windows_temporary(candidate)
            except BaselineError as cleanup_error:
                raise _aggregate_errors(
                    "baseline temporary creation and cleanup both failed",
                    (failure, cleanup_error),
                    retained_owners=cleanup_error.retained_owners,
                ) from error
        raise failure from error
    invalid = ctypes.c_void_p(-1).value
    if handle.value and int(handle.value) != invalid:
        candidate.handle = int(handle.value)
        candidate.state = "open"
    if (
        status != 0
        or int(status_block.Status) != 0
        or int(status_block.Information) != 2
        or not handle.value
        or int(handle.value) == invalid
    ):
        failure = BaselineError("baseline temporary creation returned malformed status")
        if owner is None and candidate.handle is not None:
            try:
                _cleanup_windows_temporary(candidate)
            except BaselineError as cleanup_error:
                raise _aggregate_errors(
                    "malformed temporary creation and cleanup both failed",
                    (failure, cleanup_error),
                    retained_owners=cleanup_error.retained_owners,
                ) from failure
        raise failure
    return int(handle.value)


def _windows_write_file(handle: int, raw: bytes) -> None:
    _, _, write, _, _ = _windows_file_api()
    offset = 0
    while offset < len(raw):
        chunk = raw[offset : offset + 0xFFFFFFFF]
        buffer = ctypes.create_string_buffer(chunk)
        written = wintypes.DWORD()
        try:
            succeeded = write(
                wintypes.HANDLE(handle),
                ctypes.byref(buffer),
                len(chunk),
                ctypes.byref(written),
                None,
            )
        except Exception as error:
            raise BaselineError("baseline temporary write failed") from error
        count = int(written.value)
        if not succeeded or count <= 0 or count > len(chunk):
            raise BaselineError("baseline temporary write returned malformed length")
        offset += count


def _windows_flush_file(handle: int) -> None:
    _, _, _, flush, _ = _windows_file_api()
    try:
        succeeded = flush(wintypes.HANDLE(handle))
    except Exception as error:
        raise BaselineError("baseline temporary flush failed") from error
    if not succeeded:
        error = ctypes.get_last_error()
        raise BaselineError("baseline temporary flush failed") from OSError(
            error, os.strerror(error)
        )


def _windows_close_file(handle: int) -> None:
    _, _, _, _, close = _windows_file_api()
    try:
        succeeded = close(wintypes.HANDLE(handle))
    except Exception as error:
        raise BaselineError("baseline temporary handle cannot be closed") from error
    if not succeeded:
        error = ctypes.get_last_error()
        raise BaselineError("baseline temporary handle cannot be closed") from OSError(
            error, os.strerror(error)
        )


def _windows_rename_relative_file(
    handle: int, directory_handle: int, destination_name: str
) -> None:
    destination_name = _validated_relative_name(destination_name)
    _, set_information, _, _, _ = _windows_file_api()
    encoded = destination_name.encode("utf-16-le")
    name_offset = _WindowsFileRenameInformation.FileName.offset
    buffer = ctypes.create_string_buffer(name_offset + len(encoded))
    information = ctypes.cast(
        buffer, ctypes.POINTER(_WindowsFileRenameInformation)
    ).contents
    information.ReplaceIfExists = 1
    information.RootDirectory = wintypes.HANDLE(directory_handle)
    information.FileNameLength = len(encoded)
    ctypes.memmove(ctypes.addressof(buffer) + name_offset, encoded, len(encoded))
    status_block = _WindowsIOStatusBlock()
    try:
        status = int(
            set_information(
                wintypes.HANDLE(handle),
                ctypes.byref(status_block),
                ctypes.byref(buffer),
                len(buffer),
                10,
            )
        )
    except Exception as error:
        raise BaselineError("baseline handle-relative replacement failed") from error
    if status != 0 or int(status_block.Status) != 0:
        raise BaselineError("baseline handle-relative replacement returned malformed status")


def _windows_dispose_relative_file(handle: int) -> None:
    _, set_information, _, _, _ = _windows_file_api()
    information = _WindowsFileDispositionInformation(1)
    status_block = _WindowsIOStatusBlock()
    try:
        status = int(
            set_information(
                wintypes.HANDLE(handle),
                ctypes.byref(status_block),
                ctypes.byref(information),
                ctypes.sizeof(information),
                13,
            )
        )
    except Exception as error:
        raise BaselineError("baseline temporary disposition failed") from error
    if status != 0 or int(status_block.Status) != 0:
        raise BaselineError("baseline temporary disposition returned malformed status")


class _StagedBaseline:
    __slots__ = ("name", "handle", "renamed", "state")

    def __init__(self, name: str, handle: int | None) -> None:
        self.name = name
        self.handle = handle
        self.renamed = False
        self.state = "open" if handle is not None else "unacquired"


def _cleanup_windows_temporary(temporary: _StagedBaseline) -> None:
    if temporary.state == "close_attempted":
        raise BaselineError(
            "baseline temporary handle close outcome is ambiguous",
            retained_owners=(temporary,),
        )
    if temporary.handle is None:
        temporary.state = "closed"
        return
    failures: list[BaseException] = []
    if not temporary.renamed and temporary.state != "deletion_armed":
        for _ in range(2):
            try:
                _windows_dispose_relative_file(temporary.handle)
            except BaseException as error:
                failures.append(error)
            else:
                temporary.state = "deletion_armed"
                break
        if temporary.state != "deletion_armed":
            raise _aggregate_errors(
                "baseline temporary deletion could not be armed",
                failures,
                retained_owners=(temporary,),
            ) from failures[0]

    handle = temporary.handle
    temporary.handle = None
    temporary.state = "close_attempted"
    try:
        _windows_close_file(handle)
    except BaseException as error:
        failures.append(error)
        raise _aggregate_errors(
            "baseline temporary handle close outcome is ambiguous",
            failures,
            retained_owners=(temporary,),
        ) from error
    temporary.state = "closed"


def _write_staged_bytes(handle: int, raw: bytes, *, windows: bool) -> None:
    if type(raw) is not bytes:
        raise BaselineError("dependency baseline content must be bytes")
    if windows:
        _windows_write_file(handle, raw)
        _windows_flush_file(handle)
        return
    offset = 0
    while offset < len(raw):
        written = os.write(handle, raw[offset:])
        if written <= 0:
            raise OSError("baseline temporary write made no progress")
        offset += written
    os.fsync(handle)


def _posix_staged_entry_matches(
    directory_descriptor: int, temporary: _StagedBaseline
) -> bool:
    if temporary.handle is None:
        return False
    try:
        handle_info = os.fstat(temporary.handle)
        path_info = os.stat(
            temporary.name,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return False
    except OSError as error:
        raise BaselineError("POSIX staged baseline identity cannot be inspected") from error
    return (
        stat.S_ISREG(handle_info.st_mode)
        and not stat.S_ISLNK(path_info.st_mode)
        and stat.S_ISREG(path_info.st_mode)
        and _path_handle_identity(path_info) == _path_handle_identity(handle_info)
    )


def _replace_staged_file(
    transaction: "_BoundBaselineDirectory",
    temporary: _StagedBaseline,
    destination_name: str,
) -> None:
    if os.name == "nt":
        if temporary.handle is None or transaction._architecture_handle is None:
            raise BaselineError("Windows baseline replacement handles are absent")
        _windows_rename_relative_file(
            temporary.handle,
            transaction._architecture_handle,
            destination_name,
        )
        return
    if transaction._architecture_descriptor is None:
        raise BaselineError("POSIX baseline replacement descriptor is absent")
    if temporary.handle is None:
        raise BaselineError("POSIX staged baseline descriptor is absent")
    if not _posix_staged_entry_matches(
        transaction._architecture_descriptor, temporary
    ):
        raise BaselineError("POSIX staged baseline entry no longer names its descriptor")
    os.replace(
        temporary.name,
        destination_name,
        src_dir_fd=transaction._architecture_descriptor,
        dst_dir_fd=transaction._architecture_descriptor,
    )
    try:
        after_handle = os.fstat(temporary.handle)
        after_path = os.stat(
            destination_name,
            dir_fd=transaction._architecture_descriptor,
            follow_symlinks=False,
        )
    except OSError as error:
        raise BaselineError("POSIX published baseline identity cannot be inspected") from error
    if _path_handle_identity(after_path) != _path_handle_identity(after_handle):
        raise BaselineError("POSIX published baseline no longer names its descriptor")


class _BoundBaselineDirectory:
    def __init__(self, repository_root: Path, destination: Path) -> None:
        self.repository_root = repository_root
        self.destination = destination
        self.root = repository_root
        self.docs = repository_root / "docs"
        self.architecture = self.docs / "architecture"
        self._windows_handles: list[tuple[Path, int, tuple[int, bytes]]] = []
        self._posix_descriptors: list[
            tuple[Path, int, tuple[int, int] | None]
        ] = []
        self._windows_close_attempted: set[int] = set()
        self._posix_close_attempted: set[int] = set()
        self._architecture_handle: int | None = None
        self._architecture_descriptor: int | None = None
        self._temporaries: list[_StagedBaseline] = []
        self._validated_directories: tuple[tuple[Path, tuple[int, ...]], ...] = ()
        self._validated_windows_identities: tuple[
            tuple[Path, tuple[int, bytes]], ...
        ] = ()

    def __enter__(self) -> "_BoundBaselineDirectory":
        validate_write_destination(self.repository_root, self.destination)
        self._validated_directories = tuple(
            (path, _validated_directory(path, description="baseline write ancestor"))
            for path in (self.root, self.docs, self.architecture)
        )
        try:
            if os.name == "nt":
                self._validated_windows_identities = tuple(
                    (path, self._windows_path_identity(path))
                    for path in (self.root, self.docs, self.architecture)
                )
                self._bind_windows()
            else:
                self._bind_posix()
            self.reverify()
            return self
        except BaseException as body_error:
            try:
                self.close()
            except BaselineError as cleanup_error:
                raise _aggregate_errors(
                    "baseline transaction setup and cleanup both failed",
                    (body_error, cleanup_error),
                    retained_owners=cleanup_error.retained_owners,
                ) from body_error
            raise

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        try:
            self.close()
        except BaselineError as cleanup_error:
            if exc is None:
                raise
            assert isinstance(exc, BaseException)
            raise _aggregate_errors(
                "dependency baseline operation and cleanup both failed",
                (exc, cleanup_error),
                retained_owners=cleanup_error.retained_owners,
            ) from exc

    def _bind_windows(self) -> None:
        for path in (self.root, self.docs, self.architecture):
            handle, identity = _windows_open_directory(path)
            self._windows_handles.append((path, handle, identity))
        self._architecture_handle = self._windows_handles[-1][1]

    @staticmethod
    def _windows_path_identity(path: Path) -> tuple[int, bytes]:
        handle, identity = _windows_open_directory(path)
        _windows_close_directory(handle)
        return identity

    def _bind_posix(self) -> None:
        if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
            raise BaselineError("secure POSIX directory primitives are unavailable")
        required = (os.open, os.replace, os.stat, os.unlink)
        if any(function not in os.supports_dir_fd for function in required):
            raise BaselineError("secure POSIX directory-relative operations are unavailable")
        if os.stat not in os.supports_follow_symlinks:
            raise BaselineError("secure POSIX no-follow stat is unavailable")
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)

        def bind(
            path: Path, name: Path | str, *, parent_descriptor: int | None = None
        ) -> int:
            if parent_descriptor is None:
                descriptor = os.open(name, flags)
            else:
                descriptor = os.open(name, flags, dir_fd=parent_descriptor)
            self._posix_descriptors.append((path, descriptor, None))
            info = os.fstat(descriptor)
            identity = (int(info.st_dev), int(info.st_ino))
            self._posix_descriptors[-1] = (path, descriptor, identity)
            return descriptor

        try:
            root_descriptor = bind(self.root, self.root)
            docs_descriptor = bind(
                self.docs,
                "docs",
                parent_descriptor=root_descriptor,
            )
            architecture_descriptor = bind(
                self.architecture,
                "architecture",
                parent_descriptor=docs_descriptor,
            )
            self._architecture_descriptor = architecture_descriptor
        except OSError as error:
            raise BaselineError("baseline directory chain could not be securely bound") from error

    def reverify(self) -> None:
        validate_write_destination(self.repository_root, self.destination)
        if not self._validated_directories:
            raise BaselineError("baseline directory intent identities are absent")
        for path, expected_path_identity in self._validated_directories:
            current_path_identity = _validated_directory(
                path, description="baseline write ancestor"
            )
            if current_path_identity != expected_path_identity:
                raise BaselineError(
                    f"baseline directory changed after intent validation: {path}"
                )
        if os.name == "nt":
            if len(self._validated_windows_identities) != len(self._windows_handles):
                raise BaselineError("baseline Windows intent identities are incomplete")
            for index, (path, handle, expected_handle) in enumerate(
                self._windows_handles
            ):
                intended_path, intended_identity = self._validated_windows_identities[index]
                if intended_path != path:
                    raise BaselineError("baseline directory binding order changed")
                handle_identity = _windows_directory_handle_identity(handle, path)
                current_path_identity = self._windows_path_identity(path)
                if (
                    handle_identity != expected_handle
                    or handle_identity != intended_identity
                    or current_path_identity != intended_identity
                ):
                    raise BaselineError(f"held baseline directory identity changed: {path}")
                info = os.lstat(path)
                if (
                    stat.S_ISLNK(info.st_mode)
                    or _is_disallowed_reparse(info)
                    or not stat.S_ISDIR(info.st_mode)
                ):
                    raise BaselineError(
                        f"baseline directory path no longer names its handle: {path}"
                    )
            return
        for index, (path, descriptor, bound_identity) in enumerate(
            self._posix_descriptors
        ):
            intended_path, intended_identity = self._validated_directories[index]
            intended_device_inode = (intended_identity[0], intended_identity[1])
            if intended_path != path:
                raise BaselineError("baseline directory binding order changed")
            handle_info = os.fstat(descriptor)
            path_info = os.lstat(path)
            if (
                bound_identity is None
                or bound_identity != intended_device_inode
                or (int(handle_info.st_dev), int(handle_info.st_ino))
                != intended_device_inode
                or (int(path_info.st_dev), int(path_info.st_ino))
                != intended_device_inode
                or stat.S_ISLNK(path_info.st_mode)
                or not stat.S_ISDIR(path_info.st_mode)
            ):
                raise BaselineError(
                    f"baseline directory path no longer names its descriptor: {path}"
                )

    def stage(self, raw: bytes) -> _StagedBaseline:
        self.reverify()
        name = f".{self.destination.name}.{uuid.uuid4().hex}.tmp"
        if os.name == "nt":
            if self._architecture_handle is None:
                raise BaselineError("Windows baseline directory handle is absent")
            temporary = _StagedBaseline(name, None)
            self._temporaries.append(temporary)
            handle = _windows_create_relative_file(
                self._architecture_handle,
                name,
                owner=temporary,
            )
            if temporary.handle != handle or temporary.state != "open":
                raise BaselineError("Windows baseline temporary ownership was not retained")
            self.reverify()
            _write_staged_bytes(handle, raw, windows=True)
            self.reverify()
            return temporary
        if self._architecture_descriptor is None:
            raise BaselineError("POSIX baseline directory descriptor is absent")
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            descriptor = os.open(
                name, flags, 0o600, dir_fd=self._architecture_descriptor
            )
        except OSError as error:
            raise BaselineError("baseline temporary file could not be created") from error
        temporary = _StagedBaseline(name, descriptor)
        self._temporaries.append(temporary)
        self.reverify()
        _write_staged_bytes(descriptor, raw, windows=False)
        self.reverify()
        return temporary

    def replace(self, temporary: _StagedBaseline) -> None:
        if temporary not in self._temporaries:
            raise BaselineError("baseline temporary ownership is invalid")
        self.reverify()
        _replace_staged_file(self, temporary, self.destination.name)
        temporary.renamed = True
        self._cleanup_temporary(temporary)
        if os.name != "nt" and self._architecture_descriptor is not None:
            os.fsync(self._architecture_descriptor)
        self.reverify()

    def _cleanup_temporary(self, temporary: _StagedBaseline) -> None:
        if temporary not in self._temporaries:
            return
        if os.name == "nt":
            _cleanup_windows_temporary(temporary)
        else:
            if temporary.state == "close_attempted":
                raise BaselineError(
                    "POSIX baseline descriptor close outcome is ambiguous",
                    retained_owners=(temporary,),
                )
            failures: list[BaseException] = []
            # Failure cleanup is close-only because a POSIX name can be rebound
            # between any identity check and a later unlink syscall.
            if temporary.handle is not None:
                descriptor = temporary.handle
                temporary.handle = None
                temporary.state = "close_attempted"
                try:
                    os.close(descriptor)
                except OSError as error:
                    failures.append(error)
                else:
                    temporary.state = "closed"
            if failures:
                raise _aggregate_errors(
                    "POSIX baseline temporary cleanup failed",
                    failures,
                    retained_owners=(temporary,),
                ) from failures[0]
        self._temporaries.remove(temporary)

    def close(self) -> None:
        failures: list[BaseException] = []
        for temporary in tuple(self._temporaries):
            try:
                self._cleanup_temporary(temporary)
            except BaseException as error:
                failures.append(error)
        for entry in tuple(reversed(self._posix_descriptors)):
            descriptor = entry[1]
            if descriptor in self._posix_close_attempted:
                failures.append(
                    BaselineError(
                        "POSIX directory descriptor close outcome is ambiguous",
                        retained_owners=(entry,),
                    )
                )
                continue
            self._posix_close_attempted.add(descriptor)
            try:
                os.close(descriptor)
            except OSError as error:
                failures.append(
                    _aggregate_errors(
                        "POSIX directory descriptor close outcome is ambiguous",
                        (error,),
                        retained_owners=(entry,),
                    )
                )
            else:
                self._posix_descriptors.remove(entry)
                self._posix_close_attempted.remove(descriptor)
        for entry in tuple(reversed(self._windows_handles)):
            handle = entry[1]
            if handle in self._windows_close_attempted:
                failures.append(
                    BaselineError(
                        "Windows directory handle close outcome is ambiguous",
                        retained_owners=(entry,),
                    )
                )
                continue
            self._windows_close_attempted.add(handle)
            try:
                _windows_close_directory(handle)
            except BaselineError as error:
                failures.append(error)
            else:
                self._windows_handles.remove(entry)
                self._windows_close_attempted.remove(handle)
        self._architecture_descriptor = None
        self._architecture_handle = None
        if failures:
            retained: list[object] = []
            if self._temporaries or self._posix_descriptors or self._windows_handles:
                retained.append(self)
            for failure in failures:
                if isinstance(failure, BaselineError):
                    retained.extend(failure.retained_owners)
            raise _aggregate_errors(
                "dependency baseline transaction cleanup failed",
                failures,
                retained_owners=tuple(dict.fromkeys(retained)),
            ) from failures[0]


def write_baseline(destination: Path, raw: bytes) -> None:
    if not isinstance(destination, Path) or not destination.is_absolute():
        raise BaselineError("dependency baseline destination must be absolute")
    if type(raw) is not bytes or len(raw) > MAXIMUM_BASELINE_BYTES:
        raise BaselineError("dependency baseline write bytes are invalid or oversized")
    try:
        repository_root = destination.parents[2]
    except IndexError as error:
        raise BaselineError("dependency baseline destination has no repository root") from error
    validated = validate_write_destination(repository_root, destination)
    try:
        with _BoundBaselineDirectory(repository_root, validated) as transaction:
            temporary = transaction.stage(raw)
            transaction.replace(temporary)
    except BaselineError:
        raise
    except OSError as error:
        raise BaselineError("dependency baseline could not be written atomically") from error


def check_baseline(destination: Path, expected: bytes) -> None:
    actual = _validated_regular_file(destination, maximum_bytes=MAXIMUM_BASELINE_BYTES)
    parsed = parse_baseline_bytes(actual)
    if parsed.baseline_commit != BASELINE_COMMIT:
        raise BaselineError("dependency baseline commit differs from the approved lock")
    exact_crlf_checkout = expected.replace(b"\n", b"\r\n")
    if actual != expected and actual != exact_crlf_checkout:
        raise BaselineError("dependency baseline bytes differ from deterministic generation")


def parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_mutually_exclusive_group()
    commands.add_argument("--check", action="store_true", help="verify the baseline (default)")
    commands.add_argument(
        "--write",
        type=Path,
        metavar="ABSOLUTE_BASELINE_PATH",
        help="atomically write the explicitly named canonical baseline",
    )
    parsed = parser.parse_args(argv)
    if parsed.write is None:
        parsed.check = True
    return parsed


def configured_git_executable() -> Path:
    configured = os.environ.get("PONTIUS_GIT")
    if configured is None or not configured.strip():
        raise BaselineError("PONTIUS_GIT must name an absolute Git executable")
    executable = Path(configured)
    if not executable.is_absolute():
        raise BaselineError("PONTIUS_GIT must name an absolute Git executable")
    return executable


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    repository_root = Path(__file__).resolve().parents[1]
    destination = repository_root / BASELINE_RELATIVE_PATH
    try:
        graph = derive_baseline_graph(
            repository_root,
            baseline_commit=BASELINE_COMMIT,
            git_executable=configured_git_executable(),
        )
        raw = render_baseline(graph, baseline_commit=BASELINE_COMMIT)
        if arguments.write is not None:
            destination = validate_write_destination(repository_root, arguments.write)
            write_baseline(destination, raw)
        else:
            check_baseline(destination, raw)
    except BaselineError as error:
        print(f"dependency baseline generation failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
