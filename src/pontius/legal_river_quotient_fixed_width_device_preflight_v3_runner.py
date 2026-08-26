"""Split parent-compiler/child-runtime owner for the ADR-0446 successor."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from threading import RLock
from time import perf_counter_ns

from . import legal_river_quotient_fixed_width_device_preflight_runner as _engine
from . import legal_river_quotient_fixed_width_device_preflight_v2_runner as _parent
from .durable_evidence_journal import canonical_journal_json_bytes


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-fixed-width-device-preflight-v4-child-runtime-environment.json"
)
CONFIG_SHA256 = "492458e39020fc8d5178624e4a9b8b1c6c0fc4c004852d155618fc11c955547d"
CORRECTION_CONFIG_RELATIVE_PATH = _parent.CORRECTION_CONFIG_RELATIVE_PATH
CORRECTION_CONFIG_SHA256 = _parent.CORRECTION_CONFIG_SHA256
PREREGISTRATION_COMMIT = "68e3ce35779701ef5eeb8fad9f6c42ccdd7b05ac"
CORRECTION_COMMIT = _parent.CORRECTION_COMMIT
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_fixed_width_device_preflight_v3.jsonl"
)
RESULT_PATH = _ROOT / RESULT_RELATIVE_PATH
CONSUMED_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_fixed_width_device_preflight_v2.jsonl"
)
CONSUMED_RESULT_PATH = _ROOT / CONSUMED_RESULT_RELATIVE_PATH
CONSUMED_RESULT_BYTES = 10_557
CONSUMED_RESULT_SHA256 = (
    "af5210920d61ef4a39dc027d303a83b64b09ada794f67526ee856ac0e5901085"
)
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_fixed_width_device_preflight_v3_runner"
)
SCIENTIFIC_MODULE = _parent.SCIENTIFIC_MODULE
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0446-split-runtime-fixed-width-device-owner-v3"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0446-split-runtime-fixed-width-device-campaign-v3"
).hexdigest()

_MODE_ENV = "PONTIUS_ADR0446_DEVICE_PREFLIGHT_MODE"
_CHALLENGE_ENV = "PONTIUS_ADR0446_DEVICE_PREFLIGHT_CHALLENGE"
_SPOOL_ENV = "PONTIUS_ADR0446_DEVICE_PREFLIGHT_SPOOL"
_SOURCE_SEAL_PROBE = "source_seal_probe_v3"
_SOURCE_SEAL_CHILD = "source_seal_child_v3"
_CAMPAIGN_CHILD = "campaign_child_v3"
_EVENT_PREFIX = b"PONTIUS_ADR0446_EVENT "
_ACK_PREFIX = b"PONTIUS_ADR0446_ACK "

PARENT_FULL_ENVIRONMENT_SHA256 = _parent.FULL_ENVIRONMENT_SHA256
PARENT_SELECTED_ENVIRONMENT_SHA256 = _parent.SELECTED_ENVIRONMENT_SHA256
CHILD_FULL_ENVIRONMENT_SHA256 = (
    "287903a61870ad16883bfcb764f50758857cdc463fe803c5b21ee41ff2a6a874"
)
CHILD_SELECTED_ENVIRONMENT_SHA256 = (
    "10068a92a3a2fe39269b77c2c22e07e0889261f0dcc696f074a2f786c1167270"
)
CHILD_CAMPAIGN_ENVIRONMENT_KEY_COUNT = 63
RUNTIME_DIRECTORY = (
    _ROOT / ".venv/Lib/site-packages/nvidia/cu13/bin/x86_64"
).resolve()
CUDA_ROOT = RUNTIME_DIRECTORY.parents[1]
RUNTIME_FILES = (
    (
        "cudart64_13.dll",
        RUNTIME_DIRECTORY / "cudart64_13.dll",
        551_024,
        "b00ca6f53699120da815bf3e06e2e4285fae2f201235b883dcbb50eec51e2a2a",
    ),
    (
        "nvJitLink_130_0.dll",
        RUNTIME_DIRECTORY / "nvJitLink_130_0.dll",
        92_465_776,
        "727a0acfc4495b229143b53843004eef36e0a3463fb2e1c7c4215468607fd613",
    ),
    (
        "nvrtc-builtins64_133.dll",
        RUNTIME_DIRECTORY / "nvrtc-builtins64_133.dll",
        6_684_784,
        "82c703802846329d3bab3d8df06f8c956516a0eeec568033092d6c0a69b2733a",
    ),
    (
        "nvrtc64_130_0.dll",
        RUNTIME_DIRECTORY / "nvrtc64_130_0.dll",
        101_385_328,
        "c7af6b5dbd001852d1b4a18effc6fbcfc94787eddadffea629a8333cb25b05fe",
    ),
    (
        "cusparse64_12.dll",
        RUNTIME_DIRECTORY / "cusparse64_12.dll",
        166_481_008,
        "fa7629e5eda676ccb685119490d2db88881b044cccf4023a9c326ad7513c425b",
    ),
)

STATIC_CHILD_VALUES = {
    "CUDA_PATH": str(CUDA_ROOT),
    "PONTIUS_CUDA_DLL_DIRECTORY": str(RUNTIME_DIRECTORY),
    "PONTIUS_CUDA_DLL_SOURCE": "active_python_environment",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONNOUSERSITE": "1",
    "PYTHONPATH": str(_ROOT / "src"),
}

DEPENDENCY_RELATIVE_PATHS = (
    CONFIG_RELATIVE_PATH,
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v3-msvc-environment.json",
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v1.json",
    CORRECTION_CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0439-preregister-the-fixed-width-compiled-device-preflight.md",
    "docs/decisions/ADR-0440-correct-the-batched-device-preflight-phase-topology-before-source-seal.md",
    "docs/decisions/ADR-0441-source-seal-the-corrected-fixed-width-compiled-device-preflight.md",
    "docs/decisions/ADR-0442-retain-the-fixed-width-device-compiler-rejection.md",
    "docs/decisions/ADR-0443-preregister-the-msvc-bound-fixed-width-device-successor.md",
    "docs/decisions/ADR-0444-source-seal-the-msvc-bound-fixed-width-device-successor.md",
    "docs/decisions/ADR-0445-retain-the-msvc-bound-zero-event-infrastructure-rejection.md",
    "docs/decisions/ADR-0446-preregister-the-split-child-runtime-environment-successor.md",
    "docs/decisions/ADR-0447-source-seal-the-split-child-runtime-environment-successor.md",
    CONSUMED_RESULT_RELATIVE_PATH,
    _parent.CONSUMED_RESULT_RELATIVE_PATH,
    "run_legal_river_quotient_fixed_width_device_preflight_v3.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_result.py",
    "tests/test_legal_river_quotient_fixed_width_device_preflight_v3.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_result.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_outcome.py",
    "tests/test_legal_river_quotient_fixed_width_device_preflight_v2_outcome.py",
    "src/pontius/__init__.py",
    "src/pontius/cuda_dll_bootstrap.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_result.py",
    "tests/test_legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_fixed_width_work_comparison.py",
    "src/pontius/legal_river_quotient_exact_integer_operator.py",
    "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "src/pontius/durable_evidence_journal.py",
    "artifacts/work_preflight/.gitattributes",
)

_ENGINE_BINDING_NAMES = (
    "RESULT_RELATIVE_PATH",
    "RESULT_PATH",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "CORRECTION_CONFIG_RELATIVE_PATH",
    "CORRECTION_CONFIG_SHA256",
    "PREREGISTRATION_COMMIT",
    "CORRECTION_COMMIT",
    "LITERAL_WORKER_MODULE",
    "PROTOCOL_SHA256",
    "CAMPAIGN_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "_MODE_ENV",
    "_CHALLENGE_ENV",
    "_SPOOL_ENV",
    "_SOURCE_SEAL_PROBE",
    "_CAMPAIGN_CHILD",
    "_EVENT_PREFIX",
    "_ACK_PREFIX",
    "_git",
    "_header_payload",
)
_ENGINE_LOCK = RLock()


@dataclass(frozen=True, slots=True)
class ValidatedChildRuntime:
    parent_environment: Mapping[str, str]
    host_evidence: Mapping[str, object]
    runtime_evidence: Mapping[str, object]


def _canonical_mapping_sha256(value: Mapping[str, str]) -> str:
    return sha256(
        json.dumps(
            dict(value),
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()


def _casefold_environment(environment: Mapping[str, str]) -> dict[str, tuple[str, str]]:
    folded: dict[str, tuple[str, str]] = {}
    for name, value in environment.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise TypeError("child runtime environment row differs")
        key = name.casefold()
        if key in folded:
            raise ValueError("child runtime environment repeats a key")
        folded[key] = (name, value)
    return folded


def _folded_value(folded: Mapping[str, tuple[str, str]], name: str) -> str:
    row = folded.get(name.casefold())
    if row is None:
        raise ValueError(f"child runtime environment key is absent: {name}")
    return row[1]


def verify_runtime_files(
    rows: Sequence[tuple[str, Path, int, str]] = RUNTIME_FILES,
) -> tuple[dict[str, object], ...]:
    expected_names = tuple(row[0] for row in RUNTIME_FILES)
    if tuple(row[0] for row in rows) != expected_names:
        raise ValueError("child runtime file domain differs")
    evidence = []
    for name, path, expected_bytes, expected_sha256 in rows:
        if not isinstance(path, Path) or path.parent.resolve() != RUNTIME_DIRECTORY:
            raise ValueError(f"child runtime file path differs: {name}")
        if not path.is_file():
            raise FileNotFoundError(f"child runtime file is absent: {name}")
        raw = path.read_bytes()
        digest = sha256(raw).hexdigest()
        if len(raw) != expected_bytes or digest != expected_sha256:
            raise ValueError(f"child runtime file identity differs: {name}")
        evidence.append(
            {
                "name": name,
                "path": str(path),
                "bytes": len(raw),
                "sha256": digest,
            }
        )
    return tuple(evidence)


def _resolve_child_tools(path_value: str) -> dict[str, str]:
    resolutions = {}
    for name, expected in (
        ("cl.exe", _parent.CL_PATH),
        ("link.exe", _parent.LINK_PATH),
        ("rc.exe", _parent.RC_PATH),
    ):
        resolved = shutil.which(name, path=path_value)
        canonical = None if resolved is None else os.path.normpath(resolved)
        if canonical is None or os.path.normcase(canonical) != os.path.normcase(
            str(expected)
        ):
            raise ValueError(f"child runtime tool resolution differs: {name}")
        resolutions[name] = str(expected)
    return resolutions


def _runtime_evidence(
    *,
    parent_environment: Mapping[str, str],
    child_activated: Mapping[str, str],
    runtime_files: tuple[dict[str, object], ...],
) -> dict[str, object]:
    parent_full = _canonical_mapping_sha256(parent_environment)
    parent_selected = {
        name: _parent._case_value(parent_environment, name)
        for name in _parent.SELECTED_ENVIRONMENT_NAMES
    }
    child_full = _canonical_mapping_sha256(child_activated)
    child_selected = {
        name: _parent._case_value(child_activated, name)
        for name in _parent.SELECTED_ENVIRONMENT_NAMES
    }
    child_path = child_selected["PATH"]
    expected_child_path = str(RUNTIME_DIRECTORY) + os.pathsep + parent_selected["PATH"]
    path_rows = child_path.split(os.pathsep)
    if (
        parent_full != PARENT_FULL_ENVIRONMENT_SHA256
        or _canonical_mapping_sha256(parent_selected)
        != PARENT_SELECTED_ENVIRONMENT_SHA256
        or child_full != CHILD_FULL_ENVIRONMENT_SHA256
        or _canonical_mapping_sha256(child_selected)
        != CHILD_SELECTED_ENVIRONMENT_SHA256
        or child_path != expected_child_path
        or path_rows.count(str(RUNTIME_DIRECTORY)) != 1
        or len(path_rows) < 2
        or os.path.normcase(path_rows[0]) != os.path.normcase(str(RUNTIME_DIRECTORY))
        or os.path.normcase(path_rows[1])
        != os.path.normcase(str(_parent.CL_PATH.parent))
    ):
        raise ValueError("child runtime activated projection differs")
    return {
        "schema_version": "legal-river-fixed-width-child-runtime-v1",
        "parent_activated_key_count": len(parent_environment),
        "parent_full_environment_sha256": parent_full,
        "parent_selected_environment_sha256": _canonical_mapping_sha256(
            parent_selected
        ),
        "child_activated_key_count": len(child_activated),
        "child_full_environment_sha256": child_full,
        "child_selected_environment_sha256": _canonical_mapping_sha256(
            child_selected
        ),
        "complete_campaign_environment_key_count": (
            CHILD_CAMPAIGN_ENVIRONMENT_KEY_COUNT
        ),
        "changed_parent_activated_keys": ["PATH"],
        "path_prefix": str(RUNTIME_DIRECTORY),
        "path_prefix_occurrence_count": 1,
        "parent_path_is_exact_child_suffix": True,
        "runtime_source": "active_python_environment",
        "cuda_root": str(CUDA_ROOT),
        "static_child_values": dict(STATIC_CHILD_VALUES),
        "required_runtime_files": list(runtime_files),
        "resolved_tools": _resolve_child_tools(child_path),
        "compiler_executed": False,
        "cupy_scientific_imported": False,
        "device_queried": False,
    }


def expected_child_runtime_evidence(
    parent_environment: Mapping[str, str],
) -> Mapping[str, object]:
    parent = {
        name: _parent._case_value(parent_environment, name)
        for name in _parent.ACTIVATED_ENVIRONMENT_NAMES
    }
    if len(parent_environment) != len(parent):
        raise ValueError("parent compiler environment domain differs")
    child = dict(parent)
    child["PATH"] = str(RUNTIME_DIRECTORY) + os.pathsep + parent["PATH"]
    return _runtime_evidence(
        parent_environment=parent,
        child_activated=child,
        runtime_files=verify_runtime_files(),
    )


def validate_child_runtime_environment(
    environment: Mapping[str, str] | None = None,
    *,
    expected_mode: str = _CAMPAIGN_CHILD,
    challenge_required: bool = False,
) -> ValidatedChildRuntime:
    source = os.environ if environment is None else environment
    folded = _casefold_environment(source)
    expected_names = set(_parent.ACTIVATED_ENVIRONMENT_NAMES)
    expected_names.update(STATIC_CHILD_VALUES)
    expected_names.update({_MODE_ENV, _SPOOL_ENV})
    if challenge_required:
        expected_names.add(_CHALLENGE_ENV)
    expected_domain = {name.casefold() for name in expected_names}
    if set(folded) != expected_domain:
        raise ValueError("child runtime complete environment domain differs")
    expected_count = CHILD_CAMPAIGN_ENVIRONMENT_KEY_COUNT + int(challenge_required)
    if len(folded) != expected_count:
        raise ValueError("child runtime complete environment key count differs")
    for name, expected in STATIC_CHILD_VALUES.items():
        if _folded_value(folded, name) != expected:
            raise ValueError(f"child runtime static value differs: {name}")
    if _folded_value(folded, _MODE_ENV) != expected_mode:
        raise ValueError("child runtime mode differs")
    spool = Path(_folded_value(folded, _SPOOL_ENV))
    if not spool.is_absolute() or spool.resolve() != spool or not spool.is_dir():
        raise ValueError("child runtime spool differs")
    challenge = folded.get(_CHALLENGE_ENV.casefold())
    if challenge_required:
        if challenge is None or len(bytes.fromhex(challenge[1])) != 32:
            raise ValueError("child runtime challenge differs")
    elif challenge is not None:
        raise ValueError("child runtime campaign challenge is present")

    child_activated = {
        name: _folded_value(folded, name)
        for name in _parent.ACTIVATED_ENVIRONMENT_NAMES
    }
    child_path = child_activated["PATH"]
    prefix = str(RUNTIME_DIRECTORY) + os.pathsep
    if not child_path.startswith(prefix) or child_path.count(
        str(RUNTIME_DIRECTORY)
    ) != 1:
        raise ValueError("child runtime PATH prefix differs")
    parent_environment = dict(child_activated)
    parent_environment["PATH"] = child_path[len(prefix) :]
    host_files = _parent.verify_host_files()
    host_evidence = _parent._environment_evidence(
        parent_environment,
        file_evidence=host_files,
        activation_elapsed_ns=0,
    )
    runtime = _runtime_evidence(
        parent_environment=parent_environment,
        child_activated=child_activated,
        runtime_files=verify_runtime_files(),
    )
    return ValidatedChildRuntime(
        parent_environment=parent_environment,
        host_evidence=host_evidence,
        runtime_evidence=runtime,
    )


@contextmanager
def configured_engine(
    host_evidence: Mapping[str, object],
    runtime_evidence: Mapping[str, object],
) -> Iterator[object]:
    if (
        host_evidence.get("schema_version")
        != "legal-river-fixed-width-msvc-toolchain-v1"
        or runtime_evidence.get("schema_version")
        != "legal-river-fixed-width-child-runtime-v1"
    ):
        raise ValueError("split-runtime evidence differs")
    with _ENGINE_LOCK, _parent.configured_engine(host_evidence) as engine:
        original = {name: getattr(engine, name) for name in _ENGINE_BINDING_NAMES}
        inherited_header = engine._header_payload

        def header_payload(git: Mapping[str, object]) -> dict[str, object]:
            payload = inherited_header(git)
            payload["predecessor"] = {
                "result_relative_path": CONSUMED_RESULT_RELATIVE_PATH,
                "result_raw_sha256": CONSUMED_RESULT_SHA256,
                "terminal": "infrastructure_failure",
                "event_count": 0,
            }
            payload["child_runtime_environment"] = dict(runtime_evidence)
            return payload

        replacements = {
            "RESULT_RELATIVE_PATH": RESULT_RELATIVE_PATH,
            "RESULT_PATH": RESULT_PATH,
            "CONFIG_RELATIVE_PATH": CONFIG_RELATIVE_PATH,
            "CONFIG_SHA256": CONFIG_SHA256,
            "CORRECTION_CONFIG_RELATIVE_PATH": CORRECTION_CONFIG_RELATIVE_PATH,
            "CORRECTION_CONFIG_SHA256": CORRECTION_CONFIG_SHA256,
            "PREREGISTRATION_COMMIT": PREREGISTRATION_COMMIT,
            "CORRECTION_COMMIT": CORRECTION_COMMIT,
            "LITERAL_WORKER_MODULE": LITERAL_WORKER_MODULE,
            "PROTOCOL_SHA256": PROTOCOL_SHA256,
            "CAMPAIGN_SHA256": CAMPAIGN_SHA256,
            "DEPENDENCY_RELATIVE_PATHS": DEPENDENCY_RELATIVE_PATHS,
            "_MODE_ENV": _MODE_ENV,
            "_CHALLENGE_ENV": _CHALLENGE_ENV,
            "_SPOOL_ENV": _SPOOL_ENV,
            "_SOURCE_SEAL_PROBE": _SOURCE_SEAL_PROBE,
            "_CAMPAIGN_CHILD": _CAMPAIGN_CHILD,
            "_EVENT_PREFIX": _EVENT_PREFIX,
            "_ACK_PREFIX": _ACK_PREFIX,
            "_git": _parent._absolute_git,
            "_header_payload": header_payload,
        }
        for name, value in replacements.items():
            setattr(engine, name, value)
        try:
            yield engine
        finally:
            for name, value in original.items():
                setattr(engine, name, value)


def _source_probe_child_environment(
    parent_environment: Mapping[str, str],
    *,
    spool: Path,
    challenge_hex: str,
) -> dict[str, str]:
    environment = dict(parent_environment)
    environment.update(
        {
            "PYTHONPATH": str(_ROOT / "src"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            _MODE_ENV: _SOURCE_SEAL_CHILD,
            _SPOOL_ENV: str(spool),
            _CHALLENGE_ENV: challenge_hex,
        }
    )
    return environment


def _run_source_probe_child(
    parent_environment: Mapping[str, str], challenge_hex: str
) -> Mapping[str, object]:
    with tempfile.TemporaryDirectory(prefix="pontius-adr0446-probe-") as directory:
        spool = Path(directory).resolve()
        completed = subprocess.run(
            [sys.executable, "-B", "-m", LITERAL_WORKER_MODULE],
            cwd=_ROOT,
            env=_source_probe_child_environment(
                parent_environment, spool=spool, challenge_hex=challenge_hex
            ),
            check=False,
            capture_output=True,
            text=True,
            timeout=30.0,
        )
    if completed.returncode != 0 or completed.stderr:
        raise RuntimeError(
            "split-runtime source-probe child failed: "
            + (completed.stderr or completed.stdout)[:4096]
        )
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise TypeError("split-runtime source-probe child output differs")
    return value


def source_seal_probe(challenge_hex: str) -> dict[str, object]:
    try:
        challenge = bytes.fromhex(challenge_hex)
    except ValueError as error:
        raise ValueError("split-runtime source-seal challenge differs") from error
    if len(challenge) != 32:
        raise ValueError("split-runtime source-seal challenge length differs")
    original_environment = dict(os.environ)
    activated = _parent.activate_bound_host_environment()
    runtime_evidence = expected_child_runtime_evidence(activated.environment)
    try:
        _parent._replace_process_environment(activated.environment)
        with configured_engine(activated.evidence, runtime_evidence) as engine:
            inherited = engine.source_seal_probe(challenge_hex)
        child = _run_source_probe_child(activated.environment, challenge_hex)
    finally:
        os.environ.clear()
        os.environ.update(original_environment)
    return {
        "schema_version": "legal-river-fixed-width-split-runtime-source-seal-probe-v3",
        "challenge_sha256": sha256(challenge).hexdigest(),
        "host_toolchain": dict(activated.evidence),
        "child_runtime_environment": dict(runtime_evidence),
        "child": dict(child),
        "inherited": dict(inherited),
        "compiler_executed": False,
        "cupy_scientific_imported": False,
        "device_queried": False,
        "result_absent": not RESULT_PATH.exists(),
    }


def _public_clock(origin_ns: int):
    first = True

    def clock() -> int:
        nonlocal first
        if first:
            first = False
            return origin_ns
        return perf_counter_ns()

    return clock


def _ensure_clean_public_environment() -> None:
    forbidden = {
        _MODE_ENV,
        _CHALLENGE_ENV,
        _SPOOL_ENV,
        _parent._MODE_ENV,
        _parent._CHALLENGE_ENV,
        _parent._SPOOL_ENV,
        "PONTIUS_ADR0439_DEVICE_PREFLIGHT_MODE",
        "PONTIUS_ADR0439_DEVICE_PREFLIGHT_CHALLENGE",
        "PONTIUS_ADR0439_DEVICE_PREFLIGHT_SPOOL",
    }
    if any(name in os.environ for name in forbidden):
        raise ValueError("split-runtime device-preflight owner environment is contaminated")


def _source_seal_child(challenge_hex: str) -> dict[str, object]:
    validated = validate_child_runtime_environment(
        expected_mode=_SOURCE_SEAL_CHILD,
        challenge_required=True,
    )
    challenge = bytes.fromhex(challenge_hex)
    return {
        "schema_version": "legal-river-fixed-width-split-runtime-child-probe-v1",
        "challenge_sha256": sha256(challenge).hexdigest(),
        "child_runtime_environment": dict(validated.runtime_evidence),
        "literal_worker_module": LITERAL_WORKER_MODULE,
        "cupy_loaded": any(
            name == "cupy" or name.startswith("cupy.") for name in sys.modules
        ),
        "scientific_source_loaded": SCIENTIFIC_MODULE in sys.modules,
        "compiler_executed": False,
        "device_queried": False,
        "result_absent": not RESULT_PATH.exists(),
    }


def main() -> int:
    if len(sys.argv) != 1 or not sys.dont_write_bytecode:
        raise RuntimeError(
            "split-runtime device-preflight requires no arguments and Python -B"
        )
    mode = os.environ.get(_MODE_ENV)
    if mode == _SOURCE_SEAL_PROBE:
        challenge = os.environ.get(_CHALLENGE_ENV)
        if not isinstance(challenge, str) or _SPOOL_ENV in os.environ:
            raise ValueError("split-runtime source-seal probe environment differs")
        print(canonical_journal_json_bytes(source_seal_probe(challenge)).decode("ascii"))
        return 0
    if mode == _SOURCE_SEAL_CHILD:
        challenge = os.environ.get(_CHALLENGE_ENV)
        if not isinstance(challenge, str):
            raise ValueError("split-runtime source-seal child challenge differs")
        print(canonical_journal_json_bytes(_source_seal_child(challenge)).decode("ascii"))
        return 0
    if mode == _CAMPAIGN_CHILD:
        if _CHALLENGE_ENV in os.environ:
            raise ValueError("split-runtime campaign child challenge is present")
        validated = validate_child_runtime_environment()
        with configured_engine(
            validated.host_evidence, validated.runtime_evidence
        ) as engine:
            return engine._campaign_child_main()
    if mode is not None or _CHALLENGE_ENV in os.environ or _SPOOL_ENV in os.environ:
        raise ValueError("split-runtime device-preflight mode environment differs")

    _ensure_clean_public_environment()
    public_origin = perf_counter_ns()
    activated = _parent.activate_bound_host_environment()
    runtime_evidence = expected_child_runtime_evidence(activated.environment)
    _parent._replace_process_environment(activated.environment)
    with configured_engine(activated.evidence, runtime_evidence) as engine:
        if RESULT_PATH.exists():
            raise FileExistsError(
                "split-runtime device-preflight authority is already consumed"
            )
        execution = engine.execute_owner_to_path(
            output_path=RESULT_PATH,
            monotonic_ns=_public_clock(public_origin),
        )
    print(
        "legal-river split-runtime fixed-width device preflight: "
        f"terminal={execution.terminal['terminal']} "
        f"passed={execution.terminal['passed']}"
    )
    return 0 if execution.terminal["terminal"] in {
        "completed_device_preflight",
        "completed_no_device_candidate",
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CAMPAIGN_SHA256",
    "CHILD_FULL_ENVIRONMENT_SHA256",
    "CHILD_SELECTED_ENVIRONMENT_SHA256",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "CONSUMED_RESULT_RELATIVE_PATH",
    "CONSUMED_RESULT_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "LITERAL_WORKER_MODULE",
    "PROTOCOL_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "RUNTIME_DIRECTORY",
    "RUNTIME_FILES",
    "STATIC_CHILD_VALUES",
    "configured_engine",
    "expected_child_runtime_evidence",
    "main",
    "source_seal_probe",
    "validate_child_runtime_environment",
    "verify_runtime_files",
]
