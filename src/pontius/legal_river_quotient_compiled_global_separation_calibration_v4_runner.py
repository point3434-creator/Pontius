"""Fresh ADR-0466 owner with bootstrap-before-science child semantics.

This module deliberately imports neither compiled-calibration scientific module
at module scope.  The campaign child emits and acknowledges its bootstrap first,
then imports the exact ADR-0465 v3 overlay by its own fully qualified name.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from hashlib import sha256
import importlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sys
from threading import RLock
from time import perf_counter_ns

from . import legal_river_quotient_compiled_global_separation_calibration_runner as _parent
from . import legal_river_quotient_compiled_global_separation_calibration_v2_runner as _v2
from . import legal_river_quotient_fixed_width_device_preflight_v2_runner as _host
from . import legal_river_quotient_fixed_width_device_preflight_v3_runner as _split
from .durable_evidence_journal import (
    JournalRecordKind,
    canonical_journal_json_bytes,
    recover_journal_file,
)
from .legal_river_quotient_compiled_global_separation_calibration_v2_outcome import (
    RESULT_BYTES as CONSUMED_RESULT_BYTES,
    RESULT_PATH as CONSUMED_RESULT_PATH,
    RESULT_RELATIVE_PATH as CONSUMED_RESULT_RELATIVE_PATH,
    RESULT_SHA256 as CONSUMED_RESULT_SHA256,
    assess_compiled_calibration_v2_outcome_file,
)


ROOT = Path(__file__).parents[2]
RECOVERY_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v5-deferred-science-import.json"
)
RECOVERY_CONFIG_SHA256 = (
    "f61d236530e8add3e5eb063f9f3afa641e205defd9cdefaa56fd9a2de53c8d1f"
)
AUTHORIZATION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v6-invocation-authorization.json"
)
AUTHORIZATION_CONFIG_PATH = ROOT / AUTHORIZATION_CONFIG_RELATIVE_PATH
AUTHORIZATION_COMMIT_PATHS = (
    "ARCHITECTURE.md",
    "RISK_REGISTER.md",
    "ROADMAP.md",
    "STATUS.md",
    "docs/decisions/ADR-0468-authorize-one-deferred-import-calibration-invocation.md",
    AUTHORIZATION_CONFIG_RELATIVE_PATH,
)
PREREGISTRATION_COMMIT = "001b7e1e18424e4b47c218876bccd7c9aa09ad59"
REJECTED_V3_SOURCE_SEAL_COMMIT = "77feb7c78990ca53e70b1302a6866fe5d781411f"
REJECTED_V3_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v3.jsonl"
)
REJECTED_V3_RESULT_PATH = ROOT / REJECTED_V3_RESULT_RELATIVE_PATH
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.jsonl"
)
RESULT_PATH = ROOT / RESULT_RELATIVE_PATH
ATTEMPT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.attempt.json"
)
ATTEMPT_PATH = ROOT / ATTEMPT_RELATIVE_PATH
LAUNCH_PENDING_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.launch-pending.json"
)
LAUNCH_CONSUMED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.launch-consumed.json"
)
LAUNCH_ABORTED_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v4.launch-aborted.json"
)
LAUNCH_PENDING_PATH = ROOT / LAUNCH_PENDING_RELATIVE_PATH
LAUNCH_CONSUMED_PATH = ROOT / LAUNCH_CONSUMED_RELATIVE_PATH
LAUNCH_ABORTED_PATH = ROOT / LAUNCH_ABORTED_RELATIVE_PATH
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration_v4_runner"
)
SCIENTIFIC_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration_v3"
)
PARENT_SCIENTIFIC_MODULE = _parent.SCIENTIFIC_MODULE
PARENT_SCIENTIFIC_SOURCE_SHA256 = (
    "d38e96fd445f01a70113a8598094d0449a18271fa4d6ce992c781f0253ae821e"
)
EFFECTIVE_SCIENTIFIC_SOURCE_SHA256 = (
    "7c63e2706f5aa28c37f25bfa58d09f03d2f5fe26f3a3312fe2baf7b849cec3fc"
)
CUDA_SOURCE_SHA256 = (
    "4f626802bd792788dff74c58adb90e7e30876e0c8f22d7fcb79de0c90334f8f7"
)
KERNEL_SIGNATURE_MANIFEST_SHA256 = (
    "8c25833e55a75a76a226251166a564b6ab8e52efdbb543958c33b93e8b7c63f8"
)
V3_SCIENTIFIC_SOURCE_SHA256 = (
    "030a35eb36508a0f9f61f4df5ee0315e9e6bf9cfa47ae90d3578aea530e86c37"
)
PARENT_SCIENTIFIC_SOURCE_PATH = (
    ROOT / "src/pontius/legal_river_quotient_compiled_global_separation_calibration.py"
)
V3_SCIENTIFIC_SOURCE_PATH = (
    ROOT / "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3.py"
)
_CUDA_ENTRY_RE = re.compile(
    r'extern\s+"C"\s+__global__\s+void\s+'
    r"(?P<name>[A-Za-z_]\w*)\s*\((?P<parameters>.*?)\)\s*\{",
    re.DOTALL,
)
_PARAMETER_NAME_RE = re.compile(r"([A-Za-z_]\w*)\s*$")
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0466-deferred-science-import-owner-v4"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0466-deferred-science-import-campaign-v4"
).hexdigest()

_MODE_ENV = "PONTIUS_ADR0466_COMPILED_SEPARATION_MODE"
_CHALLENGE_ENV = "PONTIUS_ADR0466_COMPILED_SEPARATION_CHALLENGE"
_SPOOL_ENV = "PONTIUS_ADR0466_COMPILED_SEPARATION_SPOOL"
_LAUNCH_TOKEN_ENV = "PONTIUS_ADR0466_COMPILED_SEPARATION_LAUNCH_TOKEN"
_SOURCE_PROBE = "deferred_science_import_source_probe_v4"
_CAMPAIGN_CHILD = "campaign_child_v4"
_EVENT_PREFIX = b"PONTIUS_ADR0466_EVENT "
_ACK_PREFIX = b"PONTIUS_ADR0466_ACK "
_PUBLIC_PYCACHE_ENV = "PONTIUS_ADR0467_PUBLIC_SOURCE_PYCACHE"
_PYTHON_PYCACHE_ENV = "PYTHONPYCACHEPREFIX"
_PYTHON_SAFE_PATH_ENV = "PYTHONSAFEPATH"
_CHILD_PYCACHE_DIRECTORY = "adr0467-unused-child-pycache"

DEPENDENCY_RELATIVE_PATHS = (
    RECOVERY_CONFIG_RELATIVE_PATH,
    AUTHORIZATION_CONFIG_RELATIVE_PATH,
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v4-launch-abi-completeness.json",
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v3-launch-abi.json",
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v2-absolute-git.json",
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v1.json",
    "docs/decisions/ADR-0457-preregister-the-compiled-global-separation-calibration.md",
    "docs/decisions/ADR-0458-source-seal-the-compiled-global-separation-calibration.md",
    "docs/decisions/ADR-0459-retain-the-unjournaled-absolute-git-infrastructure-rejection.md",
    "docs/decisions/ADR-0460-preregister-the-absolute-git-compiled-calibration-successor.md",
    "docs/decisions/ADR-0461-source-seal-the-absolute-git-compiled-calibration-successor.md",
    "docs/decisions/ADR-0462-retain-the-timed-rrns-direct-launch-arity-rejection.md",
    "docs/decisions/ADR-0463-preregister-the-kernel-launch-arity-successor.md",
    "docs/decisions/ADR-0464-correct-the-launch-arity-successor-before-source-seal.md",
    "docs/decisions/ADR-0465-source-seal-the-kernel-launch-arity-successor.md",
    "docs/decisions/ADR-0466-reject-the-v3-source-seal-and-preregister-deferred-science-import.md",
    "docs/decisions/ADR-0467-source-seal-the-deferred-science-import-successor.md",
    "docs/decisions/ADR-0468-authorize-one-deferred-import-calibration-invocation.md",
    "run_legal_river_quotient_compiled_global_separation_calibration_v4.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v4_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v4_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v4.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v3.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_outcome.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v2_outcome.py",
    "run_legal_river_quotient_compiled_global_separation_calibration_v2.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_result.py",
    "run_legal_river_quotient_compiled_global_separation_calibration.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_result.py",
    "src/pontius/legal_river_quotient_base_provenance.py",
    "src/pontius/legal_river_quotient_global_separation_topologies.py",
    "src/pontius/legal_river_quotient_selective_certified_separation.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_exact_integer_operator.py",
    "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "src/pontius/legal_river_quotient_fixed_width_work_comparison.py",
    "src/pontius/legal_river_quotient_cuda_consumer.py",
    "src/pontius/gpu_occupied_card_quotient.py",
    "src/pontius/factor_tt_contraction.py",
    "src/pontius/occupied_card_quotient.py",
    "src/pontius/structured_showdown_automaton.py",
    "src/pontius/legal_river_quotient_bridge.py",
    "src/pontius/legal_river_quotient_consumer_capacity.py",
    "src/pontius/tensor_train.py",
    "src/pontius/tensor_train_algebra.py",
    "src/pontius/action_clock.py",
    "src/pontius/factorized_belief.py",
    "src/pontius/full_width_belief.py",
    "src/pontius/full_width_reference_policy.py",
    "src/pontius/game.py",
    "src/pontius/holdem_cards.py",
    "src/pontius/immutable_blueprint.py",
    "src/pontius/legal_decision_spine_v2.py",
    "src/pontius/no_limit_betting.py",
    "src/pontius/preparation_bank.py",
    "src/pontius/river.py",
    "src/pontius/street_deadline.py",
    "src/pontius/cfr.py",
    "src/pontius/coalition.py",
    "src/pontius/dependency_tape.py",
    "src/pontius/evaluation.py",
    "src/pontius/kuhn.py",
    "src/pontius/legal_decision_spine.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_runner.py",
    "src/pontius/reference_hand_replay.py",
    "src/pontius/river_incremental.py",
    "src/pontius/river_multi_size.py",
    "src/pontius/river_multiway.py",
    "src/pontius/updates.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_runner.py",
    "src/pontius/__init__.py",
    "src/pontius/cuda_dll_bootstrap.py",
    "src/pontius/durable_evidence_journal.py",
    "artifacts/work_preflight/.gitattributes",
)

_PARENT_BINDINGS = (
    "RESULT_RELATIVE_PATH",
    "RESULT_PATH",
    "PREREGISTRATION_COMMIT",
    "LITERAL_WORKER_MODULE",
    "SCIENTIFIC_MODULE",
    "PROTOCOL_SHA256",
    "CAMPAIGN_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "_MODE_ENV",
    "_CHALLENGE_ENV",
    "_SPOOL_ENV",
    "_child_environment",
    "_SOURCE_PROBE",
    "_CAMPAIGN_CHILD",
    "_EVENT_PREFIX",
    "_ACK_PREFIX",
    "strict_git_metadata",
    "_header_payload",
)
_BINDING_LOCK = RLock()

_EXECUTION_MODULES = (
    "pontius.legal_river_quotient_fixed_width_device_preflight",
    "pontius.legal_river_quotient_exact_integer_operator",
    "pontius.legal_river_quotient_cuda_compensated_tiles",
    "pontius.legal_river_quotient_fixed_width_work_comparison",
    "pontius.legal_river_quotient_base_provenance",
)


class DeferredScienceLoadFailure(RuntimeError):
    """Typed import/validation failure with truthful stage discriminators."""

    def __init__(
        self,
        reason: str,
        *,
        import_completed: bool,
        identity_validated: bool,
    ) -> None:
        super().__init__(reason)
        self.import_completed = import_completed
        self.identity_validated = identity_validated


def _canonical_lf(raw: bytes) -> bytes:
    if type(raw) is not bytes:
        raise TypeError("deferred-import canonical input must be bytes")
    return raw.replace(bytes((13, 10)), bytes((10,)))


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"deferred-import JSON repeats key {key!r}")
        value[key] = item
    return value


def _load_json(path: Path, *, label: str) -> Mapping[str, object]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
        parse_float=lambda _: (_ for _ in ()).throw(ValueError("float in JSON")),
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("constant in JSON")),
    )
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _manifest_sha256(contract: Mapping[str, object]) -> str:
    signatures = contract.get("kernel_signatures")
    if not isinstance(signatures, Mapping):
        raise TypeError("kernel signatures must be an object")
    normalized: dict[str, list[str]] = {}
    for name, parameters in signatures.items():
        if not isinstance(name, str) or not isinstance(parameters, list):
            raise TypeError("kernel signature row differs")
        if any(not isinstance(parameter, str) for parameter in parameters):
            raise TypeError("kernel signature parameter differs")
        normalized[name] = list(parameters)
    return sha256(
        json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def _literal_assignments(
    source_text: str, names: tuple[str, ...]
) -> dict[str, object]:
    wanted = set(names)
    found: dict[str, object] = {}
    for node in ast.parse(source_text).body:
        if (
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and isinstance(
                target := (node.targets[0] if isinstance(node, ast.Assign) else node.target),
                ast.Name,
            )
            and target.id in wanted
        ):
            if target.id in found:
                raise ValueError(f"source literal repeats {target.id}")
            value = node.value
            if value is None:
                raise ValueError(f"source literal is absent for {target.id}")
            found[target.id] = ast.literal_eval(value)
    if set(found) != wanted:
        raise ValueError("source literal domain differs")
    return found


def _source_launch_arity_contract() -> dict[str, object]:
    """Derive the sealed launch contract from source without importing science."""

    parent_raw = PARENT_SCIENTIFIC_SOURCE_PATH.read_bytes()
    parent_canonical = _canonical_lf(parent_raw)
    if sha256(parent_canonical).hexdigest() != PARENT_SCIENTIFIC_SOURCE_SHA256:
        raise ValueError("source-derived parent scientific identity differs")
    v3_raw = V3_SCIENTIFIC_SOURCE_PATH.read_bytes()
    v3_canonical = _canonical_lf(v3_raw)
    if sha256(v3_canonical).hexdigest() != V3_SCIENTIFIC_SOURCE_SHA256:
        raise ValueError("source-derived v3 scientific identity differs")
    parent_text = parent_canonical.decode("utf-8")
    v3_text = v3_canonical.decode("utf-8")
    parent_literals = _literal_assignments(
        parent_text, ("KERNEL_NAMES", "CUDA_SOURCE")
    )
    v3_literals = _literal_assignments(
        v3_text,
        (
            "_OLD_TIMED_DIRECT_ARGUMENTS",
            "_NEW_TIMED_DIRECT_ARGUMENTS",
            "_OLD_SELECTED_LEAF_ARGUMENTS",
            "_NEW_SELECTED_LEAF_ARGUMENTS",
        ),
    )
    kernel_names = parent_literals["KERNEL_NAMES"]
    cuda_source = parent_literals["CUDA_SOURCE"]
    if (
        not isinstance(kernel_names, tuple)
        or len(kernel_names) != 28
        or any(not isinstance(name, str) for name in kernel_names)
        or not isinstance(cuda_source, str)
        or sha256(cuda_source.encode("utf-8")).hexdigest() != CUDA_SOURCE_SHA256
    ):
        raise ValueError("source-derived CUDA identity differs")
    effective = parent_text
    for old_name, new_name in (
        ("_OLD_TIMED_DIRECT_ARGUMENTS", "_NEW_TIMED_DIRECT_ARGUMENTS"),
        ("_OLD_SELECTED_LEAF_ARGUMENTS", "_NEW_SELECTED_LEAF_ARGUMENTS"),
    ):
        old = v3_literals[old_name]
        new = v3_literals[new_name]
        if (
            not isinstance(old, str)
            or not isinstance(new, str)
            or effective.count(old) != 1
        ):
            raise ValueError("source-derived launch repair differs")
        effective = effective.replace(old, new, 1)
    if sha256(effective.encode("utf-8")).hexdigest() != EFFECTIVE_SCIENTIFIC_SOURCE_SHA256:
        raise ValueError("source-derived effective scientific identity differs")
    unordered: dict[str, list[str]] = {}
    for match in _CUDA_ENTRY_RE.finditer(cuda_source):
        name = match.group("name")
        if name in unordered:
            raise ValueError("source-derived CUDA entry repeats")
        parameters = match.group("parameters").strip()
        names = []
        for declaration in ([] if not parameters else parameters.split(",")):
            found = _PARAMETER_NAME_RE.search(" ".join(declaration.split()))
            if found is None:
                raise ValueError("source-derived CUDA parameter differs")
            names.append(found.group(1))
        unordered[name] = names
    if set(unordered) != set(kernel_names):
        raise ValueError("source-derived CUDA entry domain differs")
    signatures = {name: unordered[name] for name in kernel_names}
    manifest = sha256(
        json.dumps(signatures, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    if manifest != KERNEL_SIGNATURE_MANIFEST_SHA256:
        raise ValueError("source-derived launch manifest differs")
    return {
        "schema_version": "pontius-adr0463-kernel-launch-arity-contract-v1",
        "parent_scientific_source_canonical_lf_sha256": (
            PARENT_SCIENTIFIC_SOURCE_SHA256
        ),
        "effective_scientific_source_sha256": EFFECTIVE_SCIENTIFIC_SOURCE_SHA256,
        "literal_cuda_source_sha256": CUDA_SOURCE_SHA256,
        "kernel_count": len(signatures),
        "kernel_signatures": signatures,
        "manifest_sha256": manifest,
        "timed_direct_source_count_expression": "np.uint64(scan_count)",
        "selected_leaf_extraneous_scan_count_removed": True,
        "complete_differential_source_count_expression": (
            "np.uint64(prepared.source_rows)"
        ),
        "central_pre_driver_guard": True,
    }


def _validate_loaded_science(science: object) -> dict[str, object]:
    if getattr(science, "__name__", None) != SCIENTIFIC_MODULE:
        raise ValueError("deferred-import scientific module identity differs")
    contract_factory = getattr(science, "launch_arity_contract", None)
    execute = getattr(science, "execute_calibration", None)
    if not callable(contract_factory) or not callable(execute):
        raise ValueError("deferred-import scientific authorities are absent")
    contract = contract_factory()
    if not isinstance(contract, Mapping):
        raise TypeError("deferred-import launch contract must be an object")
    manifest = _manifest_sha256(contract)
    if (
        getattr(science, "PARENT_SOURCE_CANONICAL_LF_SHA256", None)
        != PARENT_SCIENTIFIC_SOURCE_SHA256
        or getattr(science, "EFFECTIVE_SCIENTIFIC_SOURCE_SHA256", None)
        != EFFECTIVE_SCIENTIFIC_SOURCE_SHA256
        or getattr(science, "CUDA_SOURCE_SHA256", None) != CUDA_SOURCE_SHA256
        or getattr(science, "KERNEL_SIGNATURE_MANIFEST_SHA256", None)
        != KERNEL_SIGNATURE_MANIFEST_SHA256
        or contract.get("kernel_count") != 28
        or len(contract.get("kernel_signatures", {})) != 28
        or manifest != KERNEL_SIGNATURE_MANIFEST_SHA256
        or contract.get("manifest_sha256") != manifest
        or contract.get("central_pre_driver_guard") is not True
    ):
        raise ValueError("deferred-import scientific seal differs")
    return {
        "schema_version": "pontius-adr0466-executed-science-identity-v1",
        "module": SCIENTIFIC_MODULE,
        "parent_scientific_source_canonical_lf_sha256": (
            PARENT_SCIENTIFIC_SOURCE_SHA256
        ),
        "effective_scientific_source_sha256": EFFECTIVE_SCIENTIFIC_SOURCE_SHA256,
        "literal_cuda_source_sha256": CUDA_SOURCE_SHA256,
        "kernel_signature_manifest_sha256": manifest,
        "kernel_count": 28,
        "central_pre_driver_guard": True,
    }


def _load_sealed_science() -> tuple[object, dict[str, object]]:
    try:
        science = importlib.import_module(SCIENTIFIC_MODULE)
    except Exception as error:
        raise DeferredScienceLoadFailure(
            f"{type(error).__name__}: {error}",
            import_completed=False,
            identity_validated=False,
        ) from error
    try:
        identity = _validate_loaded_science(science)
    except Exception as error:
        raise DeferredScienceLoadFailure(
            f"{type(error).__name__}: {error}",
            import_completed=True,
            identity_validated=False,
        ) from error
    loaded = []
    try:
        for name in _EXECUTION_MODULES:
            module = importlib.import_module(name)
            if (
                getattr(module, "__name__", None) != name
                or sys.modules.get(name) is not module
            ):
                raise ValueError("deferred-import execution module identity differs")
            loaded.append(name)
        if any(name == "cupy" or name.startswith("cupy.") for name in sys.modules):
            raise RuntimeError("deferred-import execution preload imported CuPy")
    except Exception as error:
        raise DeferredScienceLoadFailure(
            f"{type(error).__name__}: {error}",
            import_completed=True,
            identity_validated=False,
        ) from error
    identity["preloaded_execution_modules"] = loaded
    return science, identity


def _attempt_bytes() -> bytes:
    return canonical_journal_json_bytes(
        {
            "schema_version": "pontius-adr0466-public-attempt-v1",
            "protocol_sha256": PROTOCOL_SHA256,
            "campaign_sha256": CAMPAIGN_SHA256,
            "result_relative_path": RESULT_RELATIVE_PATH,
            "rejected_v3_result_relative_path": REJECTED_V3_RESULT_RELATIVE_PATH,
        }
    )


def claim_public_attempt(path: Path | None = None) -> None:
    if path is None:
        path = ATTEMPT_PATH
    if not isinstance(path, Path):
        raise TypeError("deferred-import attempt path must be a Path")
    _exclusive_durable_write(path, _attempt_bytes())


def _launch_claim_identity(token: str, authorization_commit: str) -> dict[str, object]:
    if (
        not isinstance(token, str)
        or len(token) != 64
        or any(character not in "0123456789abcdef" for character in token)
        or not isinstance(authorization_commit, str)
        or len(authorization_commit) != 40
        or any(character not in "0123456789abcdef" for character in authorization_commit)
    ):
        raise ValueError("deferred-import launch claim identity differs")
    return {
        "schema_version": "pontius-adr0467-one-use-child-launch-v1",
        "token_sha256": sha256(token.encode("ascii")).hexdigest(),
        "authorization_commit": authorization_commit,
        "result_relative_path": RESULT_RELATIVE_PATH,
    }


def _launch_marker_bytes(
    identity: Mapping[str, object], *, state: str
) -> bytes:
    if state not in {"pending", "consumed", "aborted"}:
        raise ValueError("deferred-import launch marker state differs")
    return canonical_journal_json_bytes({**dict(identity), "state": state})


def _require_repo_source_imports(prefix: Path) -> None:
    if prefix.exists():
        raise RuntimeError("deferred-import fresh pycache prefix was populated")
    package_root = (ROOT / "src" / "pontius").resolve()
    for name, module in tuple(sys.modules.items()):
        if name != "pontius" and not name.startswith("pontius."):
            continue
        spec = getattr(module, "__spec__", None)
        origin = getattr(spec, "origin", None)
        if not isinstance(origin, str) or Path(origin).suffix.lower() != ".py":
            raise RuntimeError("deferred-import Pontius module is not source-backed")
        try:
            Path(origin).resolve().relative_to(package_root)
        except ValueError as error:
            raise RuntimeError(
                "deferred-import Pontius module origin escapes the source package"
            ) from error
        cached = getattr(module, "__cached__", None)
        if not isinstance(cached, str):
            raise RuntimeError("deferred-import repo module lacks cache provenance")
        cached_path = Path(cached).resolve()
        try:
            cached_path.relative_to(prefix)
        except ValueError as error:
            raise RuntimeError(
                "deferred-import repo module resolved against an unbound pycache"
            ) from error
        if cached_path.exists():
            raise RuntimeError("deferred-import repo bytecode unexpectedly exists")


def _require_source_tree_no_extensions() -> None:
    source = (ROOT / "src").resolve()
    collisions = sorted(
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in source.rglob("*")
        if path.is_file() and path.suffix.lower() in {".pyd", ".so"}
    )
    if collisions:
        raise RuntimeError(
            "deferred-import source tree contains extension-module shadows: "
            + ", ".join(collisions)
        )


def _require_public_source_loader() -> None:
    raw_prefix = os.environ.pop(_PUBLIC_PYCACHE_ENV, None)
    if not isinstance(raw_prefix, str) or not raw_prefix:
        raise RuntimeError("deferred-import public source bootstrap is absent")
    prefix = Path(raw_prefix).resolve()
    source = (ROOT / "src").resolve()
    if (
        sys.pycache_prefix is None
        or Path(sys.pycache_prefix).resolve() != prefix
        or not sys.path
        or Path(sys.path[0]).resolve() != source
        or any(
            not entry or Path(entry).resolve() == ROOT
            for entry in sys.path
        )
    ):
        raise RuntimeError("deferred-import public source bootstrap differs")
    _require_source_tree_no_extensions()
    _require_repo_source_imports(prefix)


def _exclusive_durable_write(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        written = 0
        while written < len(payload):
            count = os.write(descriptor, payload[written:])
            if count <= 0:
                raise OSError("deferred-import durable write made no progress")
            written += count
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    if path.read_bytes() != payload:
        raise RuntimeError("deferred-import durable marker differs")
    if os.name != "nt":
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)


def claim_child_launch(token: str, authorization_commit: str) -> dict[str, object]:
    identity = _launch_claim_identity(token, authorization_commit)
    if LAUNCH_CONSUMED_PATH.exists() or LAUNCH_ABORTED_PATH.exists():
        raise FileExistsError("deferred-import child launch is already terminal")
    _exclusive_durable_write(
        LAUNCH_PENDING_PATH, _launch_marker_bytes(identity, state="pending")
    )
    return identity


def _durable_unlink(path: Path) -> None:
    path.unlink()
    if os.name != "nt":
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)


def _transition_child_launch(
    token: str,
    *,
    terminal_path: Path,
    terminal_state: str,
) -> dict[str, object]:
    authorization = _authorization_identity()
    identity = _launch_claim_identity(token, str(authorization["authorization_commit"]))
    pending = _launch_marker_bytes(identity, state="pending")
    if not LAUNCH_PENDING_PATH.is_file() or LAUNCH_PENDING_PATH.read_bytes() != pending:
        raise RuntimeError("deferred-import pending child launch differs")
    if LAUNCH_CONSUMED_PATH.exists() or LAUNCH_ABORTED_PATH.exists():
        raise FileExistsError("deferred-import child launch already transitioned")
    _exclusive_durable_write(
        terminal_path, _launch_marker_bytes(identity, state=terminal_state)
    )
    _durable_unlink(LAUNCH_PENDING_PATH)
    return identity


def consume_child_launch(token: str) -> dict[str, object]:
    return _transition_child_launch(
        token,
        terminal_path=LAUNCH_CONSUMED_PATH,
        terminal_state="consumed",
    )


def abort_child_launch(token: str) -> dict[str, object]:
    return _transition_child_launch(
        token,
        terminal_path=LAUNCH_ABORTED_PATH,
        terminal_state="aborted",
    )


def finalize_child_launch_after_owner(token: str) -> str:
    authorization = _authorization_identity()
    identity = _launch_claim_identity(token, str(authorization["authorization_commit"]))
    pending = _launch_marker_bytes(identity, state="pending")
    consumed = _launch_marker_bytes(identity, state="consumed")
    aborted = _launch_marker_bytes(identity, state="aborted")
    if LAUNCH_PENDING_PATH.exists():
        if LAUNCH_PENDING_PATH.read_bytes() != pending:
            raise RuntimeError("deferred-import final pending launch differs")
        if LAUNCH_CONSUMED_PATH.is_file() and LAUNCH_CONSUMED_PATH.read_bytes() == consumed:
            if LAUNCH_ABORTED_PATH.exists():
                raise RuntimeError("deferred-import launch has two terminal states")
            _durable_unlink(LAUNCH_PENDING_PATH)
        elif LAUNCH_ABORTED_PATH.is_file() and LAUNCH_ABORTED_PATH.read_bytes() == aborted:
            if LAUNCH_CONSUMED_PATH.exists():
                raise RuntimeError("deferred-import launch has two terminal states")
            _durable_unlink(LAUNCH_PENDING_PATH)
        elif not LAUNCH_CONSUMED_PATH.exists() and not LAUNCH_ABORTED_PATH.exists():
            abort_child_launch(token)
        else:
            raise RuntimeError("deferred-import launch transition is inconsistent")
    states = {
        "consumed": LAUNCH_CONSUMED_PATH.is_file()
        and LAUNCH_CONSUMED_PATH.read_bytes() == consumed,
        "aborted": LAUNCH_ABORTED_PATH.is_file()
        and LAUNCH_ABORTED_PATH.read_bytes() == aborted,
    }
    if sum(states.values()) != 1 or LAUNCH_PENDING_PATH.exists():
        raise RuntimeError("deferred-import launch lacks one terminal state")
    return next(state for state, present in states.items() if present)


def _authorization_identity(commit: str | None = None) -> dict[str, object]:
    if not AUTHORIZATION_CONFIG_PATH.is_file():
        raise FileNotFoundError("deferred-import invocation authorization is absent")
    raw = AUTHORIZATION_CONFIG_PATH.read_bytes()
    config = _load_json(AUTHORIZATION_CONFIG_PATH, label="invocation authorization")
    if (
        set(config)
        != {"schema_version", "source_seal_commit", "authorization_commit_paths"}
        or config.get("schema_version")
        != "pontius-adr0468-one-commit-authorization-v1"
    ):
        raise ValueError("deferred-import authorization schema differs")
    source_seal = config.get("source_seal_commit")
    paths = config.get("authorization_commit_paths")
    if (
        type(source_seal) is not str
        or len(source_seal) != 40
        or any(character not in "0123456789abcdef" for character in source_seal)
        or not isinstance(paths, list)
        or any(not isinstance(path, str) for path in paths)
        or paths != list(AUTHORIZATION_COMMIT_PATHS)
    ):
        raise ValueError("deferred-import authorization fields differ")
    head = (
        _v2._absolute_git("rev-parse", "HEAD").decode("ascii").strip()
        if commit is None
        else commit
    )
    parent_row = (
        _v2._absolute_git("rev-list", "--parents", "-n", "1", head)
        .decode("ascii")
        .strip()
        .split()
    )
    changed = tuple(
        row.replace("\\", "/")
        for row in _v2._absolute_git(
            "diff", "--name-only", "--no-renames", source_seal, head
        )
        .decode("utf-8")
        .splitlines()
        if row
    )
    if (
        parent_row != [head, source_seal]
        or tuple(sorted(changed)) != tuple(sorted(AUTHORIZATION_COMMIT_PATHS))
    ):
        raise RuntimeError("deferred-import authorization commit differs")
    return {
        "schema_version": str(config["schema_version"]),
        "config_relative_path": AUTHORIZATION_CONFIG_RELATIVE_PATH,
        "config_canonical_lf_sha256": sha256(_canonical_lf(raw)).hexdigest(),
        "source_seal_commit": source_seal,
        "authorization_commit": head,
        "authorization_commit_paths": list(paths),
        "single_generation_only": True,
    }


def _dependency_hashes_at_commit(commit: str) -> dict[str, str]:
    hashes = {}
    for relative in DEPENDENCY_RELATIVE_PATHS:
        raw = _v2._absolute_git("show", f"{commit}:{relative}")
        hashes[relative] = sha256(_canonical_lf(raw)).hexdigest()
    return hashes


def _current_dependency_hashes() -> dict[str, str]:
    hashes = {}
    for relative in DEPENDENCY_RELATIVE_PATHS:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"deferred-import dependency is absent: {relative}")
        hashes[relative] = sha256(_canonical_lf(path.read_bytes())).hexdigest()
    return hashes


def _expected_status_entries(
    *, result_created: bool, launch_state: str = "pending"
) -> list[bytes]:
    launch_paths = {
        "pending": LAUNCH_PENDING_RELATIVE_PATH,
        "consumed": LAUNCH_CONSUMED_RELATIVE_PATH,
        "aborted": LAUNCH_ABORTED_RELATIVE_PATH,
    }
    if launch_state not in launch_paths:
        raise ValueError("deferred-import launch state differs")
    paths = [ATTEMPT_RELATIVE_PATH, launch_paths[launch_state]]
    if result_created:
        paths.append(RESULT_RELATIVE_PATH)
    return sorted(f"?? {path}".encode("utf-8") for path in paths)


def strict_git_metadata(
    *,
    result_created: bool,
    launch_state: str = "pending",
    launch_token: str | None = None,
) -> dict[str, object]:
    commit = _v2._absolute_git("rev-parse", "HEAD").decode("ascii").strip()
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise RuntimeError("deferred-import source commit identity differs")
    authorization = _authorization_identity(commit)
    launch_identity = _launch_claim_identity(
        os.environ.get(_LAUNCH_TOKEN_ENV, "") if launch_token is None else launch_token,
        commit,
    )
    for relative in DEPENDENCY_RELATIVE_PATHS:
        tracked = _v2._absolute_git("ls-files", "--error-unmatch", "--", relative)
        if tracked.decode("utf-8").strip().replace("\\", "/") != relative:
            raise RuntimeError(f"deferred-import dependency is not tracked: {relative}")
    status = _v2._absolute_git(
        "status", "--porcelain=v1", "-z", "--untracked-files=all"
    )
    entries = sorted(row.replace(b"\\", b"/") for row in status.split(b"\0") if row)
    if entries != _expected_status_entries(
        result_created=result_created, launch_state=launch_state
    ):
        raise RuntimeError("deferred-import owner requires its exact authorized state")
    if not ATTEMPT_PATH.is_file() or ATTEMPT_PATH.read_bytes() != _attempt_bytes():
        raise RuntimeError("deferred-import attempt marker differs")
    if RESULT_PATH.exists() is not result_created:
        raise RuntimeError("deferred-import result lifecycle differs")
    launch_paths = {
        "pending": LAUNCH_PENDING_PATH,
        "consumed": LAUNCH_CONSUMED_PATH,
        "aborted": LAUNCH_ABORTED_PATH,
    }
    selected_launch_path = launch_paths[launch_state]
    if (
        not selected_launch_path.is_file()
        or selected_launch_path.read_bytes()
        != _launch_marker_bytes(launch_identity, state=launch_state)
        or any(
            path.exists()
            for state, path in launch_paths.items()
            if state != launch_state
        )
    ):
        raise RuntimeError("deferred-import child launch lifecycle differs")
    authorized_hashes = _dependency_hashes_at_commit(commit)
    current_hashes = _current_dependency_hashes()
    if current_hashes != authorized_hashes:
        raise RuntimeError("deferred-import dependency bytes differ from authorization")
    return {
        "commit": commit,
        "dirty": False,
        "strict_status": True,
        "authorization": authorization,
        "attempt_marker_sha256": sha256(_attempt_bytes()).hexdigest(),
        "launch_claim": launch_identity,
        "launch_marker_sha256": sha256(
            _launch_marker_bytes(launch_identity, state="pending")
        ).hexdigest(),
        "authorized_dependency_hashes": authorized_hashes,
    }


def _launch_abi_identity() -> dict[str, object]:
    outcome = assess_compiled_calibration_v2_outcome_file()
    if REJECTED_V3_RESULT_PATH.exists() or RESULT_PATH.exists():
        raise FileExistsError("deferred-import result lifecycle differs")
    contract = _source_launch_arity_contract()
    executed = {
        "schema_version": "pontius-adr0466-executed-science-identity-v1",
        "module": SCIENTIFIC_MODULE,
        "parent_scientific_source_canonical_lf_sha256": (
            PARENT_SCIENTIFIC_SOURCE_SHA256
        ),
        "effective_scientific_source_sha256": EFFECTIVE_SCIENTIFIC_SOURCE_SHA256,
        "literal_cuda_source_sha256": CUDA_SOURCE_SHA256,
        "kernel_signature_manifest_sha256": KERNEL_SIGNATURE_MANIFEST_SHA256,
        "kernel_count": 28,
        "central_pre_driver_guard": True,
        "preloaded_execution_modules": list(_EXECUTION_MODULES),
    }
    return {
        "schema_version": "pontius-adr0466-deferred-science-import-recovery-v1",
        "config_relative_path": RECOVERY_CONFIG_RELATIVE_PATH,
        "config_canonical_lf_sha256": RECOVERY_CONFIG_SHA256,
        "predecessor": {
            "source_seal_commit": outcome.source_commit,
            "result_relative_path": CONSUMED_RESULT_RELATIVE_PATH,
            "result_bytes": CONSUMED_RESULT_BYTES,
            "result_raw_sha256": CONSUMED_RESULT_SHA256,
            "terminal": outcome.terminal,
            "scientific_call_count": outcome.scientific_call_count,
            "measured_call_count": outcome.measured_call_count,
            "failure_code": outcome.failure_code,
            "invocation_count": 1,
        },
        "rejected_v3": {
            "source_seal_commit": REJECTED_V3_SOURCE_SEAL_COMMIT,
            "result_relative_path": REJECTED_V3_RESULT_RELATIVE_PATH,
            "result_exists": False,
            "public_invocation_count": 0,
        },
        "bootstrap_before_science_import": True,
        "module_aliasing_used": False,
        "executed_science_identity": executed,
        "launch_arity_contract": dict(contract),
    }


@contextmanager
def configured_parent(*, launch_token: str | None = None) -> Iterator[object]:
    """Layer fresh v4 identities over the absolute-Git parent lifecycle."""

    with _BINDING_LOCK, _v2.configured_parent() as engine:
        original = {name: getattr(engine, name) for name in _PARENT_BINDINGS}
        inherited_header = engine._header_payload
        inherited_child_environment = engine._child_environment
        effective_launch_token = (
            os.environ.get(_LAUNCH_TOKEN_ENV) if launch_token is None else launch_token
        )

        def bound_strict_git_metadata(*, result_created: bool) -> dict[str, object]:
            if not isinstance(effective_launch_token, str):
                raise ValueError("deferred-import launch token is absent")
            return strict_git_metadata(
                result_created=result_created,
                launch_state="pending",
                launch_token=effective_launch_token,
            )

        def child_environment(
            spool: Path,
            parent_environment: Mapping[str, str],
            *,
            source_probe: bool = False,
            challenge_hex: str | None = None,
        ) -> dict[str, str]:
            if source_probe or challenge_hex is not None:
                raise ValueError("deferred-import parent source-probe path is forbidden")
            if not isinstance(effective_launch_token, str):
                raise ValueError("deferred-import launch token is absent")
            environment = inherited_child_environment(spool, parent_environment)
            pycache_prefix = (spool / _CHILD_PYCACHE_DIRECTORY).resolve()
            if pycache_prefix.exists():
                raise RuntimeError("deferred-import child pycache prefix is not fresh")
            environment[_PYTHON_PYCACHE_ENV] = str(pycache_prefix)
            environment[_PYTHON_SAFE_PATH_ENV] = "1"
            environment[_LAUNCH_TOKEN_ENV] = effective_launch_token
            return environment

        def header_payload(git: Mapping[str, object]) -> dict[str, object]:
            payload = inherited_header(git)
            payload["launch_abi_recovery"] = _launch_abi_identity()
            payload["deferred_science_import_authorization"] = _authorization_identity(
                str(git["commit"])
            )
            return payload

        replacements = {
            "RESULT_RELATIVE_PATH": RESULT_RELATIVE_PATH,
            "RESULT_PATH": RESULT_PATH,
            "PREREGISTRATION_COMMIT": PREREGISTRATION_COMMIT,
            "LITERAL_WORKER_MODULE": LITERAL_WORKER_MODULE,
            "SCIENTIFIC_MODULE": SCIENTIFIC_MODULE,
            "PROTOCOL_SHA256": PROTOCOL_SHA256,
            "CAMPAIGN_SHA256": CAMPAIGN_SHA256,
            "DEPENDENCY_RELATIVE_PATHS": DEPENDENCY_RELATIVE_PATHS,
            "_MODE_ENV": _MODE_ENV,
            "_CHALLENGE_ENV": _CHALLENGE_ENV,
            "_SPOOL_ENV": _SPOOL_ENV,
            "_SOURCE_PROBE": _SOURCE_PROBE,
            "_CAMPAIGN_CHILD": _CAMPAIGN_CHILD,
            "_EVENT_PREFIX": _EVENT_PREFIX,
            "_ACK_PREFIX": _ACK_PREFIX,
            "strict_git_metadata": bound_strict_git_metadata,
            "_header_payload": header_payload,
            "_child_environment": child_environment,
        }
        for name, value in replacements.items():
            setattr(engine, name, value)
        try:
            yield engine
        finally:
            for name, value in original.items():
                setattr(engine, name, value)


def _execute_deferred_campaign(
    *,
    runtime: Mapping[str, object],
    emit: Callable[[str, Mapping[str, object]], None],
    module_loader: Callable[[], tuple[object, dict[str, object]]] = _load_sealed_science,
    pre_terminal_validator: Callable[[], None] | None = None,
    monotonic_ns: Callable[[], int] = perf_counter_ns,
) -> int:
    if SCIENTIFIC_MODULE in sys.modules or PARENT_SCIENTIFIC_MODULE in sys.modules:
        raise RuntimeError("deferred-import science was loaded before bootstrap")
    if any(name == "cupy" or name.startswith("cupy.") for name in sys.modules):
        raise RuntimeError("deferred-import CuPy was loaded before bootstrap")
    laboratory_start = monotonic_ns()
    emit(
        "bootstrap_handshake",
        {
            "schema_version": "pontius-adr0457-bootstrap-v1",
            "literal_worker_module": LITERAL_WORKER_MODULE,
            "python_no_bytecode": bool(sys.dont_write_bytecode),
            "child_runtime_environment": dict(runtime),
            "cupy_loaded": False,
            "scientific_source_loaded": False,
            "parent_journal_present": RESULT_PATH.is_file(),
        },
    )
    science: object | None = None
    executed: dict[str, object] | None = None
    import_completed = False
    identity_validated = False
    execution_started = False
    failure: Exception | None = None
    try:
        science, executed = module_loader()
        import_completed = True
        identity_validated = True
        execution_started = True
        evidence = dict(
            science.execute_calibration(
                emit, laboratory_started_ns=laboratory_start
            )
        )
    except Exception as error:
        failure = error
        if isinstance(error, DeferredScienceLoadFailure):
            import_completed = error.import_completed
            identity_validated = error.identity_validated
    try:
        if pre_terminal_validator is not None:
            pre_terminal_validator()
    except Exception as error:
        failure = error
    if failure is not None:
        error = failure
        if isinstance(error, DeferredScienceLoadFailure):
            import_completed = error.import_completed
            identity_validated = error.identity_validated
        calibration_failure = getattr(science, "CalibrationFailure", ()) if science else ()
        terminal = (
            getattr(error, "terminal")
            if calibration_failure and isinstance(error, calibration_failure)
            else "deferred_science_import_rejected"
        )
        reason = (
            getattr(error, "reason")
            if calibration_failure and isinstance(error, calibration_failure)
            else f"{type(error).__name__}: {error}"
        )
        bounded_reason = str(reason)[:4096]
        evidence = {
            "schema_version": "pontius-adr0457-compiled-calibration-terminal-evidence-v1",
            "terminal": terminal,
            "passed": False,
            "reason": bounded_reason,
            "laboratory_elapsed_ns": monotonic_ns() - laboratory_start,
            "candidate_selected": None,
            "topology_selected": None,
            "arithmetic_schedule_selected": None,
            "claims": dict(_parent.CLAIMS),
        }
    evidence["executed_science_identity"] = executed
    evidence["science_import_completed"] = import_completed
    evidence["science_identity_validated"] = identity_validated
    evidence["science_execution_started"] = execution_started
    emit("terminal_evidence", evidence)
    return 0


def _require_header_only_result(launch_identity: Mapping[str, object]) -> None:
    recovery = recover_journal_file(
        RESULT_PATH,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if (
        recovery.is_complete
        or len(recovery.records) != 1
        or recovery.records[0].body.kind is not JournalRecordKind.HEADER
    ):
        raise RuntimeError("deferred-import child requires a header-only journal")
    header = recovery.records[0].body.payload
    git = header.get("source_seal_git")
    if (
        not isinstance(git, Mapping)
        or git.get("launch_claim") != dict(launch_identity)
        or git.get("commit") != launch_identity.get("authorization_commit")
        or header.get("deferred_science_import_authorization")
        != git.get("authorization")
    ):
        raise RuntimeError("deferred-import child header launch identity differs")


def _load_and_validate_child_science(
    *, token: str, expected_pycache: Path
) -> tuple[object, dict[str, object]]:
    loaded: tuple[object, dict[str, object]] | None = None
    try:
        loaded = _load_sealed_science()
        _require_repo_source_imports(expected_pycache)
        strict_git_metadata(
            result_created=True, launch_state="consumed", launch_token=token
        )
        return loaded
    except DeferredScienceLoadFailure:
        raise
    except Exception as error:
        raise DeferredScienceLoadFailure(
            f"{type(error).__name__}: {error}",
            import_completed=loaded is not None,
            identity_validated=False,
        ) from error


def _campaign_child_main() -> int:
    token = os.environ.get(_LAUNCH_TOKEN_ENV)
    if not isinstance(token, str):
        raise ValueError("deferred-import child launch token is absent")
    spool = Path(os.environ[_SPOOL_ENV]).resolve()
    pycache_raw = os.environ.get(_PYTHON_PYCACHE_ENV)
    safe_path_raw = os.environ.get(_PYTHON_SAFE_PATH_ENV)
    expected_pycache = (spool / _CHILD_PYCACHE_DIRECTORY).resolve()
    if (
        not isinstance(pycache_raw, str)
        or Path(pycache_raw).resolve() != expected_pycache
        or sys.pycache_prefix is None
        or Path(sys.pycache_prefix).resolve() != expected_pycache
        or safe_path_raw != "1"
        or not sys.flags.safe_path
    ):
        raise RuntimeError("deferred-import child source-loader environment differs")
    _require_source_tree_no_extensions()
    _require_repo_source_imports(expected_pycache)
    filtered = {
        name: value
        for name, value in os.environ.items()
        if name
        not in {
            _MODE_ENV,
            _SPOOL_ENV,
            _CHALLENGE_ENV,
            _LAUNCH_TOKEN_ENV,
            _PYTHON_PYCACHE_ENV,
            _PYTHON_SAFE_PATH_ENV,
        }
    }
    runtime = dict(_split.validate_child_runtime_environment(
        filtered, expected_mode=_split._CAMPAIGN_CHILD
    ).runtime_evidence)
    runtime.update(
        {
            "v4_python_safe_path": True,
            "v4_fresh_pycache_prefix": True,
            "v4_repo_bytecode_loaded": False,
        }
    )
    if (
        not spool.is_dir()
        or not RESULT_PATH.is_file()
        or not ATTEMPT_PATH.is_file()
        or ATTEMPT_PATH.read_bytes() != _attempt_bytes()
        or REJECTED_V3_RESULT_PATH.exists()
    ):
        raise RuntimeError("deferred-import child lifecycle differs")
    authorization = _authorization_identity()
    launch_identity = _launch_claim_identity(
        token, str(authorization["authorization_commit"])
    )
    strict_git_metadata(
        result_created=True, launch_state="pending", launch_token=token
    )
    _require_header_only_result(launch_identity)
    consume_child_launch(token)
    strict_git_metadata(
        result_created=True, launch_state="consumed", launch_token=token
    )
    emit = _parent._child_emit_factory(spool)

    def load_and_rebind() -> tuple[object, dict[str, object]]:
        return _load_and_validate_child_science(
            token=token, expected_pycache=expected_pycache
        )

    return _execute_deferred_campaign(
        runtime=runtime,
        emit=emit,
        module_loader=load_and_rebind,
        pre_terminal_validator=lambda: strict_git_metadata(
            result_created=True,
            launch_state="consumed",
            launch_token=token,
        ),
    )


def source_seal_probe(challenge_hex: str) -> dict[str, object]:
    if (
        not isinstance(challenge_hex, str)
        or len(challenge_hex) != 64
        or any(character not in "0123456789abcdef" for character in challenge_hex)
    ):
        raise ValueError("deferred-import source-probe challenge differs")
    if (
        REJECTED_V3_RESULT_PATH.exists()
        or RESULT_PATH.exists()
        or ATTEMPT_PATH.exists()
        or LAUNCH_PENDING_PATH.exists()
        or LAUNCH_CONSUMED_PATH.exists()
        or LAUNCH_ABORTED_PATH.exists()
    ):
        raise FileExistsError("deferred-import source-probe lifecycle differs")
    before_science = SCIENTIFIC_MODULE in sys.modules
    before_parent = PARENT_SCIENTIFIC_MODULE in sys.modules
    before_cupy = any(
        name == "cupy" or name.startswith("cupy.") for name in sys.modules
    )
    if before_science or before_parent or before_cupy:
        raise RuntimeError("deferred-import source probe loaded science early")
    pycache_raw = os.environ.get(_PYTHON_PYCACHE_ENV)
    if (
        not isinstance(pycache_raw, str)
        or sys.pycache_prefix is None
        or Path(sys.pycache_prefix).resolve() != Path(pycache_raw).resolve()
        or os.environ.get(_PYTHON_SAFE_PATH_ENV) != "1"
        or not sys.flags.safe_path
    ):
        raise RuntimeError("deferred-import source probe loader environment differs")
    pycache_prefix = Path(pycache_raw).resolve()
    _require_repo_source_imports(pycache_prefix)
    original = dict(os.environ)
    activated = _host.activate_bound_host_environment()
    runtime = _split.expected_child_runtime_evidence(activated.environment)
    try:
        _host._replace_process_environment(activated.environment)
        if shutil.which("git", path=os.environ.get("PATH")) is not None:
            raise ValueError("activated environment unexpectedly resolves relative Git")
        version = _v2._absolute_git("--version").decode("ascii").strip()
        commit = _v2._absolute_git("rev-parse", "HEAD").decode("ascii").strip()
        science, executed = _load_sealed_science()
        _require_repo_source_imports(pycache_prefix)
        return {
            "schema_version": "pontius-adr0466-deferred-import-source-probe-v1",
            "challenge_sha256": sha256(challenge_hex.encode("ascii")).hexdigest(),
            "relative_git_resolution": None,
            "git_version": version,
            "source_commit": commit,
            "child_runtime_environment": dict(runtime),
            "science_loaded_before_probe_import": before_science,
            "parent_science_loaded_before_probe_import": before_parent,
            "cupy_loaded_before_probe_import": before_cupy,
            "science_loaded_after_probe_import": SCIENTIFIC_MODULE in sys.modules,
            "loaded_module_is_exact": science is sys.modules[SCIENTIFIC_MODULE],
            "python_safe_path": True,
            "fresh_pycache_prefix": True,
            "repo_bytecode_loaded": False,
            "executed_science_identity": executed,
            "compiler_executed": False,
            "device_queried": False,
            "v3_result_absent": True,
            "v4_result_absent": True,
            "attempt_absent": True,
            "launch_markers_absent": True,
        }
    finally:
        os.environ.clear()
        os.environ.update(original)


def _public_clock(origin_ns: int):
    first = True

    def clock() -> int:
        nonlocal first
        if first:
            first = False
            return origin_ns
        return perf_counter_ns()

    return clock


def main() -> int:
    if len(sys.argv) != 1 or not sys.dont_write_bytecode:
        raise RuntimeError("deferred-import calibration requires no arguments and Python -B")
    mode = os.environ.get(_MODE_ENV)
    if mode == _SOURCE_PROBE:
        challenge = os.environ.get(_CHALLENGE_ENV)
        if not isinstance(challenge, str):
            raise ValueError("deferred-import source-probe challenge is absent")
        print(canonical_journal_json_bytes(source_seal_probe(challenge)).decode("ascii"))
        return 0
    if mode == _CAMPAIGN_CHILD:
        if _CHALLENGE_ENV in os.environ:
            raise ValueError("deferred-import campaign challenge is present")
        with configured_parent():
            return _campaign_child_main()
    if (
        mode is not None
        or _SPOOL_ENV in os.environ
        or _CHALLENGE_ENV in os.environ
        or _LAUNCH_TOKEN_ENV in os.environ
    ):
        raise ValueError("deferred-import public environment is contaminated")
    _require_public_source_loader()
    if (
        ATTEMPT_PATH.exists()
        or RESULT_PATH.exists()
        or LAUNCH_PENDING_PATH.exists()
        or LAUNCH_CONSUMED_PATH.exists()
        or LAUNCH_ABORTED_PATH.exists()
    ):
        raise FileExistsError("deferred-import calibration authority is already consumed")
    claim_public_attempt()
    assess_compiled_calibration_v2_outcome_file()
    if REJECTED_V3_RESULT_PATH.exists():
        raise FileExistsError("rejected v3 result unexpectedly exists")
    authorization = _authorization_identity()
    launch_token = secrets.token_hex(32)
    claim_child_launch(launch_token, str(authorization["authorization_commit"]))

    public_origin = perf_counter_ns()
    original = dict(os.environ)
    execution = None
    final_launch_state = None
    try:
        activated = _host.activate_bound_host_environment()
        _split.expected_child_runtime_evidence(activated.environment)
        _host._replace_process_environment(activated.environment)
        with configured_parent(launch_token=launch_token) as engine:
            execution = engine.execute_owner_to_path(
                output_path=RESULT_PATH,
                parent_environment=activated.environment,
                monotonic_ns=_public_clock(public_origin),
            )
    finally:
        os.environ.clear()
        os.environ.update(original)
        final_launch_state = finalize_child_launch_after_owner(launch_token)
    assert execution is not None
    strict_git_metadata(
        result_created=True,
        launch_state=str(final_launch_state),
        launch_token=launch_token,
    )
    print(
        "legal-river deferred-import compiled calibration: "
        f"terminal={execution.terminal['terminal']} "
        f"passed={execution.terminal['passed']}"
    )
    return 0 if execution.terminal["passed"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ATTEMPT_PATH",
    "ATTEMPT_RELATIVE_PATH",
    "AUTHORIZATION_COMMIT_PATHS",
    "AUTHORIZATION_CONFIG_PATH",
    "AUTHORIZATION_CONFIG_RELATIVE_PATH",
    "CAMPAIGN_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "LITERAL_WORKER_MODULE",
    "PREREGISTRATION_COMMIT",
    "PROTOCOL_SHA256",
    "RECOVERY_CONFIG_RELATIVE_PATH",
    "RECOVERY_CONFIG_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "SCIENTIFIC_MODULE",
    "claim_public_attempt",
    "configured_parent",
    "main",
    "source_seal_probe",
    "strict_git_metadata",
]
