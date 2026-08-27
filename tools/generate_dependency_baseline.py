"""Generate and verify the mechanical legacy Python dependency baseline.

This tool is standard-library-only.  It reads Python source from an exact Git
commit, parses imports with :mod:`ast`, and emits a canonical TOML lock.
"""

from __future__ import annotations

import argparse
import ast
from collections.abc import Mapping, Sequence
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


SCHEMA_VERSION = "pontius-dependency-baseline-v1"
BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
BASELINE_RELATIVE_PATH = "docs/architecture/dependency-baseline.toml"
MAXIMUM_ARCHIVE_BYTES = 64 * 1024 * 1024
MAXIMUM_BASELINE_BYTES = 4 * 1024 * 1024
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class BaselineError(RuntimeError):
    """A deterministic dependency-baseline failure."""


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


def _is_reparse(info: os.stat_result) -> bool:
    return bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _validated_regular_file(path: Path, *, maximum_bytes: int) -> bytes:
    try:
        info = os.lstat(path)
    except OSError as error:
        raise BaselineError(f"dependency baseline file cannot be inspected: {path}") from error
    if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISREG(info.st_mode):
        raise BaselineError(f"dependency baseline path is not a regular file: {path}")
    if info.st_size > maximum_bytes:
        raise BaselineError(f"dependency baseline file is oversized: {path}")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise BaselineError(f"dependency baseline file cannot be read: {path}") from error
    if len(raw) != info.st_size:
        raise BaselineError(f"dependency baseline file changed while reading: {path}")
    return raw


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
        or _is_reparse(info)
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


def validate_write_destination(repository_root: Path, destination: Path) -> Path:
    if not isinstance(destination, Path) or not destination.is_absolute():
        raise BaselineError("--write must explicitly name an absolute baseline path")
    try:
        root = repository_root.resolve(strict=True)
        architecture = (root / "docs" / "architecture").resolve(strict=True)
    except OSError as error:
        raise BaselineError("docs/architecture must already be a real directory") from error
    architecture_info = os.lstat(architecture)
    if (
        stat.S_ISLNK(architecture_info.st_mode)
        or _is_reparse(architecture_info)
        or not stat.S_ISDIR(architecture_info.st_mode)
    ):
        raise BaselineError("docs/architecture is not a regular directory")
    expected = architecture / "dependency-baseline.toml"
    candidate = destination.resolve(strict=False)
    if os.path.normcase(str(candidate)) != os.path.normcase(str(expected)):
        raise BaselineError("--write may name only docs/architecture/dependency-baseline.toml")
    if os.path.lexists(candidate):
        info = os.lstat(candidate)
        if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISREG(info.st_mode):
            raise BaselineError("baseline destination is not a regular file")
    return candidate


def write_baseline(destination: Path, raw: bytes) -> None:
    candidate = destination.parent / f".{destination.name}.{uuid.uuid4().hex}.tmp"
    try:
        with candidate.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(candidate, destination)
    except OSError as error:
        raise BaselineError("dependency baseline could not be written atomically") from error
    finally:
        try:
            candidate.unlink()
        except FileNotFoundError:
            pass


def check_baseline(destination: Path, expected: bytes) -> None:
    actual = _validated_regular_file(destination, maximum_bytes=MAXIMUM_BASELINE_BYTES)
    parsed = parse_baseline_bytes(actual)
    if parsed.baseline_commit != BASELINE_COMMIT:
        raise BaselineError("dependency baseline commit differs from the approved lock")
    if actual != expected:
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
