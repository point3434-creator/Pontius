"""Fresh MSVC-bound owner for the ADR-0443 fixed-width device successor."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from time import perf_counter_ns

from . import legal_river_quotient_fixed_width_device_preflight_runner as _engine
from .durable_evidence_journal import canonical_journal_json_bytes


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-fixed-width-device-preflight-v3-msvc-environment.json"
)
CONFIG_SHA256 = "21b74a0f7f13e8eac894d4ecf2c4dd05cde3925ab24449f11944d954ec59067c"
CORRECTION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-fixed-width-device-preflight-v2-topology.json"
)
CORRECTION_CONFIG_SHA256 = (
    "6ebca361aed6c6cfcd11fd2df0b6041c1f676a7e6b07af9739bcd84e64b38e41"
)
PREREGISTRATION_COMMIT = "b24eae342a51fdbfcd393025faf8e4f414a5cc4e"
CORRECTION_COMMIT = "e4704d9011ad4af2f7d610bfa56053d046864d96"
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_fixed_width_device_preflight_v2.jsonl"
)
RESULT_PATH = _ROOT / RESULT_RELATIVE_PATH
CONSUMED_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_fixed_width_device_preflight_v1.jsonl"
)
CONSUMED_RESULT_SHA256 = (
    "9b1ff216879c5e67090d8794242da74ba8bd52aac6753865c3bc822483550c69"
)
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_fixed_width_device_preflight_v2_runner"
)
SCIENTIFIC_MODULE = "pontius.legal_river_quotient_fixed_width_device_preflight"
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0443-msvc-bound-fixed-width-device-owner-v2"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0443-msvc-bound-fixed-width-device-campaign-v2"
).hexdigest()

_MODE_ENV = "PONTIUS_ADR0443_DEVICE_PREFLIGHT_MODE"
_CHALLENGE_ENV = "PONTIUS_ADR0443_DEVICE_PREFLIGHT_CHALLENGE"
_SPOOL_ENV = "PONTIUS_ADR0443_DEVICE_PREFLIGHT_SPOOL"
_SOURCE_SEAL_PROBE = "source_seal_probe_v2"
_CAMPAIGN_CHILD = "campaign_child_v2"
_EVENT_PREFIX = b"PONTIUS_ADR0443_EVENT "
_ACK_PREFIX = b"PONTIUS_ADR0443_ACK "

FULL_ENVIRONMENT_SHA256 = (
    "6b3ccdc1ac479b5b4b9626161cdd5ca28f5d5043f6b87cc65a6f27f8e1a3cfe6"
)
SELECTED_ENVIRONMENT_SHA256 = (
    "a313c9a0fc817a9375912aba0e9acce6984e7d9bb5b28b3ccf56e7ef23a7c1a0"
)
ACTIVATION_WALL_NS = 10_000_000_000
MAXIMUM_ACTIVATION_STDOUT_BYTES = 1_048_576
MAXIMUM_ACTIVATION_STDERR_BYTES = 16_384

BASELINE_ENVIRONMENT_NAMES = (
    "SystemRoot",
    "WINDIR",
    "ComSpec",
    "ProgramFiles",
    "ProgramFiles(x86)",
    "ProgramData",
    "TEMP",
    "TMP",
    "USERPROFILE",
    "LOCALAPPDATA",
    "APPDATA",
    "HOMEDRIVE",
    "HOMEPATH",
    "PATHEXT",
    "PROCESSOR_ARCHITECTURE",
    "NUMBER_OF_PROCESSORS",
)
ACTIVATED_ENVIRONMENT_NAMES = (
    "APPDATA",
    "ComSpec",
    "CommandPromptType",
    "DevEnvDir",
    "EXTERNAL_INCLUDE",
    "ExtensionSdkDir",
    "Framework40Version",
    "FrameworkDir",
    "FrameworkDir64",
    "FrameworkVersion",
    "FrameworkVersion64",
    "HOMEDRIVE",
    "HOMEPATH",
    "INCLUDE",
    "LIB",
    "LIBPATH",
    "LOCALAPPDATA",
    "NUMBER_OF_PROCESSORS",
    "PATH",
    "PATHEXT",
    "PROCESSOR_ARCHITECTURE",
    "PROMPT",
    "Platform",
    "ProgramData",
    "ProgramFiles",
    "ProgramFiles(x86)",
    "SystemRoot",
    "TEMP",
    "TMP",
    "UCRTVersion",
    "USERPROFILE",
    "UniversalCRTSdkDir",
    "VCIDEInstallDir",
    "VCINSTALLDIR",
    "VCPKG_ROOT",
    "VCToolsInstallDir",
    "VCToolsRedistDir",
    "VCToolsVersion",
    "VS170COMNTOOLS",
    "VSCMD_ARG_HOST_ARCH",
    "VSCMD_ARG_TGT_ARCH",
    "VSCMD_ARG_app_plat",
    "VSCMD_VER",
    "VSINSTALLDIR",
    "VisualStudioVersion",
    "WINDIR",
    "WindowsLibPath",
    "WindowsSDKLibVersion",
    "WindowsSDKVersion",
    "WindowsSdkBinPath",
    "WindowsSdkDir",
    "WindowsSdkVerBinPath",
    "__DOTNET_ADD_64BIT",
    "__DOTNET_PREFERRED_BITNESS",
    "__VSCMD_PREINIT_PATH",
)
SELECTED_ENVIRONMENT_NAMES = (
    "VSCMD_ARG_HOST_ARCH",
    "VSCMD_ARG_TGT_ARCH",
    "VCToolsVersion",
    "WindowsSdkDir",
    "WindowsSDKVersion",
    "PATH",
    "INCLUDE",
    "LIB",
    "LIBPATH",
)
REQUIRED_SELECTED_VALUES = {
    "VSCMD_ARG_HOST_ARCH": "x64",
    "VSCMD_ARG_TGT_ARCH": "x64",
    "VCToolsVersion": "14.44.35207",
    "WindowsSdkDir": "C:\\Program Files (x86)\\Windows Kits\\10\\",
    "WindowsSDKVersion": "10.0.26100.0\\",
}

VCVARS64_PATH = Path(
    r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
    r"\VC\Auxiliary\Build\vcvars64.bat"
)
CL_PATH = Path(
    r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
    r"\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe"
)
LINK_PATH = CL_PATH.with_name("link.exe")
RC_PATH = Path(
    r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\rc.exe"
)
GIT_PATH = Path(r"C:\Program Files\Git\cmd\git.exe")

HOST_FILES = (
    ("vswhere", Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"), 469_456, "c54f3b7c9164ea9a0db8641e81ecdda80c2664ef5a47c4191406f848cc07c662"),
    ("vcvars64", VCVARS64_PATH, 39, "6b516d8fcf543c14b2d861e1f45661e0029230fe0dc48e86ce78522801822209"),
    ("vcvarsall", VCVARS64_PATH.with_name("vcvarsall.bat"), 10_524, "ee67e4181ae2578b7842f9f1549a7f66e2166638fa544ce6838d9e9033a02275"),
    ("cl", CL_PATH, 677_736, "88c8344236a27a6e727e0a8edc49aaa2690bdc7a9464b9d18cc7abe70a9f1c0d"),
    ("link", LINK_PATH, 3_252_576, "ca11e6c45debd34bf652dfe984c5360a531a005ed78bf72852330c9c2590cf0d"),
    ("rc", RC_PATH, 55_640, "43da1503c262c30894c851589bf0155f8365d77e63a5f7bc13982320e3a6b42d"),
    ("nvcc", Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvcc.exe"), 20_017_264, "92d993c6e7025e1597d0d895e65e8658f5f1d41576a477656647a7eece2cd35f"),
    ("git", GIT_PATH, 46_920, "7b7971dd13f0c3a284e538601f2f9770b3a87dfaccb5fb52d68141c67ed22364"),
)

DEPENDENCY_RELATIVE_PATHS = (
    CONFIG_RELATIVE_PATH,
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v1.json",
    CORRECTION_CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0439-preregister-the-fixed-width-compiled-device-preflight.md",
    "docs/decisions/ADR-0440-correct-the-batched-device-preflight-phase-topology-before-source-seal.md",
    "docs/decisions/ADR-0441-source-seal-the-corrected-fixed-width-compiled-device-preflight.md",
    "docs/decisions/ADR-0442-retain-the-fixed-width-device-compiler-rejection.md",
    "docs/decisions/ADR-0443-preregister-the-msvc-bound-fixed-width-device-successor.md",
    "docs/decisions/ADR-0444-source-seal-the-msvc-bound-fixed-width-device-successor.md",
    CONSUMED_RESULT_RELATIVE_PATH,
    "run_legal_river_quotient_fixed_width_device_preflight_v2.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_result.py",
    "tests/test_legal_river_quotient_fixed_width_device_preflight_v2.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_result.py",
    "src/pontius/legal_river_quotient_fixed_width_work_comparison.py",
    "src/pontius/legal_river_quotient_exact_integer_operator.py",
    "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "src/pontius/durable_evidence_journal.py",
    "artifacts/work_preflight/.gitattributes",
)

_ORIGINAL_ENGINE_BINDINGS = {
    name: getattr(_engine, name)
    for name in (
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
}
_ORIGINAL_HEADER_PAYLOAD = _engine._header_payload


@dataclass(frozen=True, slots=True)
class ActivatedHostEnvironment:
    environment: Mapping[str, str]
    evidence: Mapping[str, object]


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


def _case_value(environment: Mapping[str, str], name: str) -> str:
    matches = [value for key, value in environment.items() if key.casefold() == name.casefold()]
    if len(matches) != 1 or not isinstance(matches[0], str):
        raise ValueError(f"MSVC environment key differs: {name}")
    return matches[0]


def verify_host_files(
    rows: tuple[tuple[str, Path, int, str], ...] = HOST_FILES,
) -> tuple[dict[str, object], ...]:
    expected_roles = {row[0] for row in HOST_FILES}
    if {row[0] for row in rows} != expected_roles or len(rows) != len(expected_roles):
        raise ValueError("MSVC host-file role domain differs")
    evidence = []
    for role, path, expected_bytes, expected_sha256 in rows:
        if not isinstance(path, Path) or not path.is_file():
            raise FileNotFoundError(f"MSVC host file is absent: {role}")
        raw = path.read_bytes()
        observed = sha256(raw).hexdigest()
        if len(raw) != expected_bytes or observed != expected_sha256:
            raise ValueError(f"MSVC host file identity differs: {role}")
        evidence.append(
            {
                "role": role,
                "path": str(path),
                "bytes": len(raw),
                "sha256": observed,
            }
        )
    return tuple(evidence)


def _parse_set_output(raw: bytes) -> dict[str, str]:
    if not isinstance(raw, bytes) or len(raw) > MAXIMUM_ACTIVATION_STDOUT_BYTES:
        raise ValueError("MSVC activation stdout exceeds its bound")
    text = raw.decode("utf-8", "strict")
    rows: dict[str, str] = {}
    folded: set[str] = set()
    for line in text.splitlines():
        if "=" not in line:
            raise ValueError("MSVC activation output has a non-environment row")
        name, value = line.split("=", 1)
        key = name.casefold()
        if not name or key in folded:
            raise ValueError("MSVC activation output repeats an environment key")
        folded.add(key)
        rows[name] = value
    return rows


def _environment_evidence(
    environment: Mapping[str, str],
    *,
    file_evidence: tuple[dict[str, object], ...],
    activation_elapsed_ns: int,
) -> dict[str, object]:
    activated = {name: _case_value(environment, name) for name in ACTIVATED_ENVIRONMENT_NAMES}
    if len(environment) != len(activated):
        raise ValueError("MSVC activated environment domain differs")
    full_digest = _canonical_mapping_sha256(activated)
    selected = {name: _case_value(activated, name) for name in SELECTED_ENVIRONMENT_NAMES}
    selected_digest = _canonical_mapping_sha256(selected)
    if full_digest != FULL_ENVIRONMENT_SHA256:
        raise ValueError("MSVC full activated environment identity differs")
    if selected_digest != SELECTED_ENVIRONMENT_SHA256:
        raise ValueError("MSVC selected environment identity differs")
    for name, expected in REQUIRED_SELECTED_VALUES.items():
        if selected[name] != expected:
            raise ValueError(f"MSVC selected environment value differs: {name}")
    first_path = selected["PATH"].split(os.pathsep)[0]
    if os.path.normcase(first_path) != os.path.normcase(str(CL_PATH.parent)):
        raise ValueError("MSVC compiler directory is not first in PATH")
    resolutions = {}
    for name, expected in (("cl.exe", CL_PATH), ("link.exe", LINK_PATH), ("rc.exe", RC_PATH)):
        resolved = shutil.which(name, path=selected["PATH"])
        canonical = None if resolved is None else os.path.normpath(resolved)
        if canonical is None or os.path.normcase(canonical) != os.path.normcase(str(expected)):
            raise ValueError(f"MSVC activated tool resolution differs: {name}")
        resolutions[name] = str(expected)
    if (
        isinstance(activation_elapsed_ns, bool)
        or not isinstance(activation_elapsed_ns, int)
        or activation_elapsed_ns < 0
        or activation_elapsed_ns > ACTIVATION_WALL_NS
    ):
        raise ValueError("MSVC activation wall differs")
    return {
        "schema_version": "legal-river-fixed-width-msvc-toolchain-v1",
        "installation_version": "17.14.37614.0",
        "vc_tools_version": "14.44.35207",
        "compiler_version": "19.44.35228.0",
        "windows_sdk_version": "10.0.26100.0",
        "file_identities": list(file_evidence),
        "environment_key_count": len(activated),
        "full_environment_sha256": full_digest,
        "selected_environment_sha256": selected_digest,
        "resolved_tools": resolutions,
        "activation_elapsed_ns": activation_elapsed_ns,
        "compiler_executed": False,
        "ambient_compiler_environment_inherited": False,
    }


def activate_bound_host_environment(
    ambient: Mapping[str, str] | None = None,
) -> ActivatedHostEnvironment:
    source = os.environ if ambient is None else ambient
    before_files = verify_host_files()
    baseline = {name: _case_value(source, name) for name in BASELINE_ENVIRONMENT_NAMES}
    baseline["PATH"] = str(Path(baseline["SystemRoot"]) / "System32")
    command = (
        f'"{baseline["ComSpec"]}" /d /s /c '
        f'""{VCVARS64_PATH}" >nul && set"'
    )
    started = perf_counter_ns()
    completed = subprocess.run(
        command,
        env=baseline,
        check=False,
        capture_output=True,
        timeout=ACTIVATION_WALL_NS / 1_000_000_000,
    )
    elapsed = perf_counter_ns() - started
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace")[:4096]
        raise RuntimeError(f"MSVC activation failed: {detail}")
    if len(completed.stderr) > MAXIMUM_ACTIVATION_STDERR_BYTES or completed.stderr:
        raise RuntimeError("MSVC activation stderr differs")
    environment = _parse_set_output(completed.stdout)
    after_files = verify_host_files()
    if before_files != after_files:
        raise RuntimeError("MSVC host files changed during activation")
    evidence = _environment_evidence(
        environment,
        file_evidence=before_files,
        activation_elapsed_ns=elapsed,
    )
    return ActivatedHostEnvironment(environment=environment, evidence=evidence)


def validate_inherited_host_environment() -> ActivatedHostEnvironment:
    environment = {
        name: _case_value(os.environ, name) for name in ACTIVATED_ENVIRONMENT_NAMES
    }
    files = verify_host_files()
    evidence = _environment_evidence(
        environment,
        file_evidence=files,
        activation_elapsed_ns=0,
    )
    return ActivatedHostEnvironment(environment=environment, evidence=evidence)


def _replace_process_environment(environment: Mapping[str, str]) -> None:
    os.environ.clear()
    os.environ.update(environment)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def _absolute_git(*arguments: str) -> bytes:
    completed = subprocess.run(
        [str(GIT_PATH), *arguments],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        timeout=30.0,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode("utf-8", "replace").strip()
        raise RuntimeError(f"MSVC-bound device-preflight Git metadata failed: {detail}")
    return completed.stdout


@contextmanager
def configured_engine(host_evidence: Mapping[str, object]) -> Iterator[object]:
    if host_evidence.get("schema_version") != "legal-river-fixed-width-msvc-toolchain-v1":
        raise ValueError("MSVC host evidence differs")

    def header_payload(git: Mapping[str, object]) -> dict[str, object]:
        payload = _ORIGINAL_HEADER_PAYLOAD(git)
        payload["host_toolchain"] = dict(host_evidence)
        payload["predecessor"] = {
            "result_relative_path": CONSUMED_RESULT_RELATIVE_PATH,
            "result_raw_sha256": CONSUMED_RESULT_SHA256,
            "terminal": "compiler_rejection",
        }
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
        "_git": _absolute_git,
        "_header_payload": header_payload,
    }
    for name, value in replacements.items():
        setattr(_engine, name, value)
    try:
        yield _engine
    finally:
        for name, value in _ORIGINAL_ENGINE_BINDINGS.items():
            setattr(_engine, name, value)


def source_seal_probe(challenge_hex: str) -> dict[str, object]:
    original_environment = dict(os.environ)
    activated = activate_bound_host_environment()
    try:
        _replace_process_environment(activated.environment)
        with configured_engine(activated.evidence) as engine:
            evidence = engine.source_seal_probe(challenge_hex)
    finally:
        os.environ.clear()
        os.environ.update(original_environment)
    evidence["schema_version"] = "legal-river-fixed-width-msvc-source-seal-probe-v2"
    evidence["host_toolchain"] = dict(activated.evidence)
    return evidence


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
    forbidden = (
        _MODE_ENV,
        _CHALLENGE_ENV,
        _SPOOL_ENV,
        "PONTIUS_ADR0439_DEVICE_PREFLIGHT_MODE",
        "PONTIUS_ADR0439_DEVICE_PREFLIGHT_CHALLENGE",
        "PONTIUS_ADR0439_DEVICE_PREFLIGHT_SPOOL",
    )
    if any(name in os.environ for name in forbidden):
        raise ValueError("MSVC-bound device-preflight owner environment is contaminated")


def main() -> int:
    if len(sys.argv) != 1 or not sys.dont_write_bytecode:
        raise RuntimeError("MSVC-bound device-preflight requires no arguments and Python -B")
    mode = os.environ.get(_MODE_ENV)
    if mode == _SOURCE_SEAL_PROBE:
        challenge = os.environ.get(_CHALLENGE_ENV)
        if not isinstance(challenge, str) or _SPOOL_ENV in os.environ:
            raise ValueError("MSVC source-seal probe environment differs")
        print(canonical_journal_json_bytes(source_seal_probe(challenge)).decode("ascii"))
        return 0
    if mode == _CAMPAIGN_CHILD:
        if _CHALLENGE_ENV in os.environ:
            raise ValueError("MSVC campaign child challenge is present")
        activated = validate_inherited_host_environment()
        with configured_engine(activated.evidence) as engine:
            return engine._campaign_child_main()
    if mode is not None or _CHALLENGE_ENV in os.environ or _SPOOL_ENV in os.environ:
        raise ValueError("MSVC-bound device-preflight mode environment differs")

    _ensure_clean_public_environment()
    public_origin = perf_counter_ns()
    activated = activate_bound_host_environment()
    _replace_process_environment(activated.environment)
    with configured_engine(activated.evidence) as engine:
        if RESULT_PATH.exists():
            raise FileExistsError("MSVC-bound device-preflight authority is already consumed")
        execution = engine.execute_owner_to_path(
            output_path=RESULT_PATH,
            monotonic_ns=_public_clock(public_origin),
        )
    print(
        "legal-river MSVC-bound fixed-width device preflight: "
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
    "ACTIVATED_ENVIRONMENT_NAMES",
    "ActivatedHostEnvironment",
    "CAMPAIGN_SHA256",
    "CONFIG_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "FULL_ENVIRONMENT_SHA256",
    "HOST_FILES",
    "LITERAL_WORKER_MODULE",
    "PROTOCOL_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "SELECTED_ENVIRONMENT_SHA256",
    "activate_bound_host_environment",
    "configured_engine",
    "main",
    "source_seal_probe",
    "validate_inherited_host_environment",
    "verify_host_files",
]
