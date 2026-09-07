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
DECISION_PROVIDER_ORIGIN_PATHS = frozenset(
    f"src/pontius/decision_provider/{name}.py"
    for name in ("__init__", "model", "providers", "selection", "codec")
)
_PROVIDER = "pontius.decision_provider"
_PROVIDER_RUNTIME = {_PROVIDER + "." + name for name in ("model", "providers", "selection")}
_PROVIDER_TRANSPORT = {_PROVIDER + "." + name for name in ("model", "providers", "codec")}
BLUEPRINT_ARTIFACT_ORIGIN_PATHS = frozenset(
    {
        "src/pontius/blueprint_artifact/__init__.py",
        "src/pontius/blueprint_artifact/codec.py",
    }
)
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
        "tools/v0a_rehearsal_driver.py",
        "tools/v0a_hand_adapter.py",
        "tools/v0a_event_adapter.py",
        "tools/v0a_table_host.py",
        "tools/v0a_table_session.py",
        "tools/v0a_seeded_deals.py",
        "tools/v0a_evaluation.py",
        "tools/v0a_evaluation_v2.py",
        "tools/v0a_evaluation_contract.py",
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
            or added == "pontius.blueprint_artifact"
            or added.startswith("pontius.blueprint_artifact.")
            or added == "pontius.hand_scenario"
            or added.startswith("pontius.hand_scenario.")
            or added in {_BASELINE.module_name_for_path(path)
                         for path in DECISION_PROVIDER_ORIGIN_PATHS}
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
        if (path == "src/pontius/hand_scenario.py" or path.startswith("src/pontius/hand_scenario/"))
        and path not in {
            "src/pontius/hand_scenario/__init__.py", "src/pontius/hand_scenario/codec.py"}
    )
    violations.extend(
        f"unclassified stabilization origin: {path}"
        for path in sorted(current_sources)
        if path == "src/pontius/blueprint_artifact.py"
        or path.startswith("src/pontius/blueprint_artifact/")
        and path not in BLUEPRINT_ARTIFACT_ORIGIN_PATHS
    )
    violations.extend(
        f"unclassified stabilization origin: {path}"
        for path in sorted(current_sources)
        if (
            path == "src/pontius/v0a.py"
            or path.startswith("src/pontius/v0a/")
        )
        and path not in V0A_ORIGIN_PATHS
    )
    violations.extend(
        f"unclassified stabilization origin: {path}"
        for path in sorted(current_sources)
        if (path == "src/pontius/decision_provider.py"
            or path.startswith("src/pontius/decision_provider/"))
        and path not in DECISION_PROVIDER_ORIGIN_PATHS
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
    """Apply ADR-0485's exact v0a dependency and complete-deal boundary."""

    violations: list[str] = []
    try:
        edges = _BASELINE.import_edges(sources)
        for path, raw in sorted(sources.items()):
            origin = _BASELINE.module_name_for_path(path)
            if (
                origin != "pontius.v0a"
                and not origin.startswith("pontius.v0a.")
            ) or origin == V0A_HOST_MODULE:
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
                    if base == "pontius.v0a" and any(
                        alias.name == "replay" for alias in node.names
                    ):
                        violations.append(
                            f"forbidden v0a import: {origin} -> {V0A_HOST_MODULE} "
                            "(the explicit-deal host is never imported by a policy module)"
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
        if origin == "pontius.v0a.runtime" and target in _PROVIDER_RUNTIME:
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
        driver_internal = origin == "tools.v0a_rehearsal_driver" and target in {
            "pontius.immutable_blueprint",
            "pontius.v0a.replay",
            "pontius.v0a.trace",
        }
        adapter_internal = origin == "tools.v0a_hand_adapter" and target in {
            "pontius.hand_scenario.codec", "pontius.blueprint_artifact.codec",
            "pontius.v0a.replay", "pontius.v0a.trace"}
        event_internal = origin == "tools.v0a_event_adapter" and target in {
            "pontius.blueprint_artifact.codec", "pontius.v0a.model",
            "pontius.v0a.runtime", "pontius.v0a.clock", "pontius.v0a.trace"}
        table_internal = origin == "tools.v0a_table_host" and target in {
            "pontius.blueprint_artifact.codec", "pontius.no_limit_betting",
            "pontius.holdem_cards", "pontius.legal_decision_spine_v2",
            "pontius.v0a.model", "pontius.v0a.trace"}
        provider_internal = (origin in {"tools.v0a_event_adapter", "tools.v0a_table_host"}
                             and target in _PROVIDER_TRANSPORT)
        if (not _is_stdlib(target) and not sibling and not driver_internal
                and not adapter_internal and not event_internal and not table_internal
                and not provider_internal):
            violations.append(f"forbidden orchestration import: {origin} -> {target}")
    _raise_violations(violations)


def enforce_decision_provider_import_policy(sources: Mapping[str, bytes]) -> None:
    """ADR-0505: exact trusted provider sources, with no complete-deal or I/O routes."""
    allowed = {
        _PROVIDER: set(),
        _PROVIDER + ".model": {"__future__", "dataclasses", "enum", "hashlib", "json", "math",
            "pontius.holdem_cards", "pontius.no_limit_betting", "pontius.immutable_blueprint",
            "pontius.v0a.model"},
        _PROVIDER + ".providers": {"__future__", "itertools", _PROVIDER + ".model",
            "pontius.immutable_blueprint", "pontius.no_limit_betting", "pontius.river"},
        _PROVIDER + ".selection": {"__future__", _PROVIDER + ".model", _PROVIDER + ".providers",
            "pontius.immutable_blueprint", "pontius.no_limit_betting"},
        _PROVIDER + ".codec": {"__future__", "json", "math", _PROVIDER + ".model",
            "pontius.v0a.model", "pontius.v0a.trace"},
    }
    incoming = {"pontius.v0a.runtime": _PROVIDER_RUNTIME,
        "tools.v0a_event_adapter": _PROVIDER_TRANSPORT,
        "tools.v0a_table_host": _PROVIDER_TRANSPORT}
    violations = []
    for origin, target in _BASELINE.import_edges(sources):
        if origin in allowed and target not in allowed[origin]:
            violations.append(f"forbidden decision provider import: {origin} -> {target}")
        if (target == _PROVIDER or target.startswith(_PROVIDER + ".")) and not (
            target in allowed.get(origin, set()) or target in incoming.get(origin, set())
        ):
            violations.append(f"forbidden decision provider incoming edge: {origin} -> {target}")
    forbidden = {"SixSeatHoldemDeal", "__import__", "__builtins__", "eval", "exec", "compile",
        "open", "input", "globals", "locals", "vars", "modules",
        "import_module", "exec_module", "load_module", "run_module", "run_path"}
    for path in sorted(DECISION_PROVIDER_ORIGIN_PATHS & sources.keys()):
        tree = _BASELINE._parse_source(sources[path], relative_path=path)
        if path.endswith("/__init__.py") and any(not (isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant) and type(node.value.value) is str)
            for node in tree.body):
            violations.append("decision_provider package initializer must be inert")
        for node in ast.walk(tree):
            if (isinstance(node, ast.Name) and node.id in forbidden or
                isinstance(node, ast.Attribute) and node.attr in forbidden or
                isinstance(node, ast.ImportFrom) and any(
                    alias.name == "*" or alias.name in forbidden for alias in node.names)):
                violations.append(f"forbidden decision provider route: {path}:{node.lineno}")
    _raise_violations(violations)


def enforce_blueprint_artifact_import_policy(sources: Mapping[str, bytes]) -> None:
    """Keep the portable codec inert and limited to its two value modules."""

    try:
        edges = _BASELINE.import_edges(sources)
    except _BASELINE.BaselineError as error:
        raise BoundaryError(f"blueprint artifact sources cannot be scanned: {error}") from error
    violations = []
    family = "pontius.blueprint_artifact"
    allowed = {"__future__", "json", "pontius.immutable_blueprint",
               "pontius.no_limit_betting"}
    for origin, target in edges:
        in_family = origin == family or origin.startswith(family + ".")
        targets_family = target == family or target.startswith(family + ".")
        if in_family and target not in allowed:
            violations.append(f"forbidden blueprint artifact import: {origin} -> {target}")
        elif targets_family and not in_family and not (
            origin in {"tools.v0a_hand_adapter", "tools.v0a_event_adapter", "tools.v0a_table_host"}
            and target == family + ".codec"
        ):
            violations.append(f"legacy origin imports blueprint artifact: {origin} -> {target}")
    _raise_violations(violations)


def enforce_hand_adapter_import_policy(sources: Mapping[str, bytes]) -> None:
    """ADR-0493: two inert/value origins and one exact host-side tool opening."""
    allowed = {
        "pontius.hand_scenario": set(),
        "pontius.hand_scenario.codec": {"__future__", "dataclasses", "json",
            "pontius.holdem_cards", "pontius.v0a.model", "pontius.v0a.replay"},
        "tools.v0a_hand_adapter": {"__future__", "argparse", "hashlib", "io", "json",
            "os", "pathlib", "re", "stat", "subprocess", "sys", "tarfile",
            "pontius.hand_scenario.codec", "pontius.blueprint_artifact.codec",
            "pontius.v0a.replay", "pontius.v0a.trace"},
    }
    violations = []
    for origin, target in _BASELINE.import_edges(sources):
        if origin in allowed and target not in allowed[origin]:
            violations.append(f"forbidden hand adapter import: {origin} -> {target}")
        scenario_target = target == "pontius.hand_scenario" or target.startswith(
            "pontius.hand_scenario.")
        if scenario_target and not (
            origin == "tools.v0a_hand_adapter" and target == "pontius.hand_scenario.codec"
        ):
            violations.append(f"forbidden hand scenario incoming edge: {origin} -> {target}")
    raw = sources.get("src/pontius/hand_scenario/__init__.py", b"")
    if any(not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                and type(node.value.value) is str) for node in ast.parse(raw).body):
        violations.append("hand_scenario package initializer must be inert")
    _raise_violations(violations)


def enforce_event_adapter_import_policy(sources: Mapping[str, bytes]) -> None:
    """ADR-0495: one exact host tool with no generalized dependency opening."""
    origin = "tools.v0a_event_adapter"
    allowed = {
        "__future__", "argparse", "hashlib", "io", "json", "msvcrt", "os",
        "pathlib", "re", "stat", "subprocess", "sys",
        "pontius.blueprint_artifact.codec", "pontius.v0a.model",
        "pontius.v0a.runtime", "pontius.v0a.clock", "pontius.v0a.trace",
    }
    allowed |= _PROVIDER_TRANSPORT
    violations = [
        f"forbidden event adapter import: {edge_origin} -> {target}"
        for edge_origin, target in _BASELINE.import_edges(sources)
        if edge_origin == origin and target not in allowed
    ]
    _raise_violations(violations)


def enforce_table_host_import_policy(sources: Mapping[str, bytes]) -> None:
    """ADR-0497: exact public game helpers and bounded native host transport."""
    allowed = {
        "__future__", "argparse", "base64", "ctypes", "dataclasses", "hashlib", "io",
        "json", "math", "os", "pathlib", "queue", "re", "stat", "subprocess", "sys",
        "threading", "time", "pontius.blueprint_artifact.codec", "pontius.no_limit_betting",
        "pontius.holdem_cards", "pontius.legal_decision_spine_v2", "pontius.v0a.model",
        "pontius.v0a.trace",
    }
    allowed |= _PROVIDER_TRANSPORT
    _raise_violations([
        f"forbidden table host import: {origin} -> {target}"
        for origin, target in _BASELINE.import_edges(sources)
        if origin == "tools.v0a_table_host" and target not in allowed
    ])


def enforce_table_session_import_policy(sources: Mapping[str, bytes]) -> None:
    """ADR-0499: closed imports and the one explicitly admitted host-source binding."""
    allowed = {
        "__future__", "argparse", "base64", "dataclasses", "hashlib", "json", "os",
        "pathlib", "re", "stat", "subprocess", "sys", "types",
    }
    violations = [
        f"forbidden table session import: {origin} -> {target}"
        for origin, target in _BASELINE.import_edges(sources)
        if origin == "tools.v0a_table_session" and target not in allowed
    ]
    path = "tools/v0a_table_session.py"
    if path in sources:
        tree = _BASELINE._parse_source(sources[path], relative_path=path)
        # This checks the declared dependency, not general dynamic-execution soundness.
        bindings = {name: [] for name in ("HOST", "HOST_BLOB")}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in bindings:
                        bindings[target.id].append(
                            node.value.value if isinstance(node.value, ast.Constant) else None
                        )
        if bindings != {
            "HOST": ["tools/v0a_table_host.py"],
            "HOST_BLOB": ["6ec8a162b053158203663c48e82314b10750f962"],
        }:
            violations.append("table session fixed host binding differs from ADR-0499")
    _raise_violations(violations)


def enforce_seeded_deals_import_policy(sources: Mapping[str, bytes]) -> None:
    """ADR-0502: exact inert dealer imports and no dynamic import/exec routes."""
    path = "tools/v0a_seeded_deals.py"
    if path not in sources:
        return
    allowed = {"__future__", "argparse", "hashlib", "json", "os", "pathlib",
               "re", "stat", "sys"}
    forbidden = {"__import__", "__builtins__", "eval", "exec", "compile",
                 "getattr", "globals", "locals", "vars", "modules",
                 "import_module", "exec_module", "load_module", "run_module", "run_path"}
    tree = _BASELINE._parse_source(sources[path], relative_path=path)
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name not in allowed for alias in node.names):
                violations.append(f"forbidden seeded deals import at {path}:{node.lineno}")
        elif isinstance(node, ast.ImportFrom):
            if (node.level or node.module not in allowed or any(
                alias.name == "*" or alias.name.startswith("_") or alias.name in forbidden
                for alias in node.names
            )):
                violations.append(f"forbidden seeded deals import at {path}:{node.lineno}")
        elif (isinstance(node, ast.Name) and node.id in forbidden or
              isinstance(node, ast.Attribute) and
              (node.attr in forbidden or node.attr.startswith("_") and not (
                  node.attr == "__init__" and isinstance(node.value, ast.Call) and
                  isinstance(node.value.func, ast.Name) and node.value.func.id == "super"
                  and not node.value.args and not node.value.keywords))):
            violations.append(f"forbidden seeded deals dynamic route at {path}:{node.lineno}")
    _raise_violations(violations)


def enforce_evaluation_import_policy(sources: Mapping[str, bytes]) -> None:
    """ADR-0508: closed imports and three captured, fixed raw loader edges."""
    policies = {
        "tools/v0a_evaluation_contract.py": {
            "__future__", "base64", "hashlib", "json", "math", "re"},
        "tools/v0a_evaluation.py": {"__future__", "argparse", "ctypes", "hashlib", "json", "os",
            "pathlib", "re", "stat", "subprocess", "sys", "threading", "time", "types"},
    }
    policies["tools/v0a_evaluation_v2.py"] = policies["tools/v0a_evaluation.py"]
    fixed = ast.parse("""
OLD = tuple('tools/' + n + '.py' for n in ('v0a_rehearsal_driver', 'v0a_hand_adapter',
    'v0a_event_adapter', 'v0a_table_host', 'v0a_table_session', 'v0a_seeded_deals'))
NEW = ('tools/v0a_evaluation.py', 'tools/v0a_evaluation_contract.py')
ALIASES = ('_pontius_evaluation_contract', '_pontius_evaluation_dealer', '_pontius_evaluation_host')
""").body
    loader = ast.parse("""
for alias, path in zip(ALIASES, (NEW[1], OLD[5], OLD[3])):
    module = types.ModuleType(alias)
    module.__file__ = str(repo / path)
    sys.modules[alias] = module
    s.modules[alias] = module
    exec(compile(s.raw[path], module.__file__, 'exec'), module.__dict__)
""").body[0]
    getters = {ast.dump(ast.parse(text, mode="eval").body) for text in (
        "getattr(self, 'modules', {})", "getattr(error, 'secondary', ())",
        "getattr(error, 'code', str(error) if isinstance(error, ValueError) else phase)")}
    forbidden = {"__import__", "__builtins__", "eval", "globals", "locals", "vars",
                 "import_module", "exec_module", "load_module", "run_module", "run_path"}
    violations = []
    for path, allowed in policies.items():
        if path not in sources:
            continue
        tree = _BASELINE._parse_source(sources[path], relative_path=path)
        wrapper = path in ("tools/v0a_evaluation.py", "tools/v0a_evaluation_v2.py")
        routes = [n for n in ast.walk(tree) if isinstance(n, ast.Name)
                  and n.id in {"exec", "compile"}]
        if wrapper:
            for expected in fixed:
                name = expected.targets[0].id
                if name == "NEW":
                    expected = ast.parse(
                        f"NEW = ({path!r}, 'tools/v0a_evaluation_contract.py')").body[0]
                actual = [n for n in tree.body if isinstance(n, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == name for t in n.targets)]
                if len(actual) != 1 or ast.dump(actual[0]) != ast.dump(expected):
                    violations.append(f"evaluation fixed {name} binding differs")
            functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                         and n.name == "admit_source"]
            loops = [n for f in functions for n in f.body if isinstance(n, ast.For)
                     and ast.dump(n) == ast.dump(loader)]
            if (len(functions) != 1 or len(loops) != 1 or len(routes) != 2 or
                    any(n not in list(ast.walk(loops[0])) for n in routes)):
                violations.append("evaluation captured raw loader differs")
        elif routes:
            violations.append("evaluation contract has a dynamic execution route")
        for node in ast.walk(tree):
            invalid = False
            if isinstance(node, ast.Import):
                invalid = any(alias.name not in allowed for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                invalid = node.level or node.module not in allowed or any(
                    alias.name == "*" or alias.name.startswith("_") for alias in node.names)
            elif isinstance(node, ast.Name):
                invalid = node.id in forbidden
            elif isinstance(node, ast.Attribute):
                invalid = (node.attr in forbidden or node.attr in {"Source", "Table", "Session"}
                    or isinstance(node.value, ast.Attribute) and
                    (node.value.attr == "host" and node.attr != "Job" or
                     node.value.attr == "dealer" and node.attr != "deal_for_hand"))
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                  and node.func.id == "getattr"):
                invalid = not wrapper or ast.dump(node) not in getters
            if invalid:
                violations.append(f"forbidden evaluation dependency at {path}:{node.lineno}")
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
    enforce_decision_provider_import_policy({**current_sources, **tool_sources})
    enforce_blueprint_artifact_import_policy({**current_sources, **tool_sources})
    enforce_hand_adapter_import_policy({**current_sources, **tool_sources})
    enforce_event_adapter_import_policy({**current_sources, **tool_sources})
    enforce_table_host_import_policy({**current_sources, **tool_sources})
    enforce_table_session_import_policy({**current_sources, **tool_sources})
    enforce_seeded_deals_import_policy(tool_sources)
    enforce_evaluation_import_policy(tool_sources)
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
