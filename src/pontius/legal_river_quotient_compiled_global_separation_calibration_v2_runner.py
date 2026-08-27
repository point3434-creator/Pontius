"""Absolute-Git owner wrapper for the ADR-0460 calibration successor.

The compiled science remains in the ADR-0458 modules.  This wrapper changes
only process plumbing: every Git call is dispatched to the exact hash-bound
host-manifest executable, including after the compiler environment replaces
``PATH``.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
import sys
from threading import RLock
from time import perf_counter_ns

from . import legal_river_quotient_compiled_global_separation_calibration_runner as _parent
from . import legal_river_quotient_fixed_width_device_preflight_v2_runner as _host
from . import legal_river_quotient_fixed_width_device_preflight_v3_runner as _split
from .durable_evidence_journal import canonical_journal_json_bytes


ROOT = Path(__file__).parents[2]
RECOVERY_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v2-absolute-git.json"
)
RECOVERY_CONFIG_SHA256 = (
    "e9242618e674c74804990c17965de731da15a70adcd0c0094b650d7332313f4e"
)
SCIENTIFIC_CONFIG_RELATIVE_PATH = _parent.CONFIG_RELATIVE_PATH
SCIENTIFIC_CONFIG_SHA256 = _parent.CONFIG_SHA256
PREREGISTRATION_COMMIT = "edaf6bc53952f4238172ed871fe0d601cb92c168"
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v2.jsonl"
)
RESULT_PATH = ROOT / RESULT_RELATIVE_PATH
CONSUMED_RESULT_RELATIVE_PATH = _parent.RESULT_RELATIVE_PATH
CONSUMED_RESULT_PATH = ROOT / CONSUMED_RESULT_RELATIVE_PATH
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration_v2_runner"
)
SCIENTIFIC_MODULE = _parent.SCIENTIFIC_MODULE
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0460-absolute-git-compiled-separation-owner-v2"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0460-absolute-git-compiled-separation-campaign-v2"
).hexdigest()

GIT_PATH = Path(r"C:\Program Files\Git\cmd\git.exe")
GIT_BYTES = 46_920
GIT_SHA256 = "7b7971dd13f0c3a284e538601f2f9770b3a87dfaccb5fb52d68141c67ed22364"

_MODE_ENV = "PONTIUS_ADR0460_COMPILED_SEPARATION_MODE"
_CHALLENGE_ENV = "PONTIUS_ADR0460_COMPILED_SEPARATION_CHALLENGE"
_SPOOL_ENV = "PONTIUS_ADR0460_COMPILED_SEPARATION_SPOOL"
_SOURCE_PROBE = "absolute_git_source_probe_v2"
_CAMPAIGN_CHILD = "campaign_child_v2"
_EVENT_PREFIX = b"PONTIUS_ADR0460_EVENT "
_ACK_PREFIX = b"PONTIUS_ADR0460_ACK "

DEPENDENCY_RELATIVE_PATHS = (
    RECOVERY_CONFIG_RELATIVE_PATH,
    SCIENTIFIC_CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0457-preregister-the-compiled-global-separation-calibration.md",
    "docs/decisions/ADR-0458-source-seal-the-compiled-global-separation-calibration.md",
    "docs/decisions/ADR-0459-retain-the-unjournaled-absolute-git-infrastructure-rejection.md",
    "docs/decisions/ADR-0460-preregister-the-absolute-git-compiled-calibration-successor.md",
    "docs/decisions/ADR-0461-source-seal-the-absolute-git-compiled-calibration-successor.md",
    "run_legal_river_quotient_compiled_global_separation_calibration_v2.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v2.py",
    "run_legal_river_quotient_compiled_global_separation_calibration.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration.py",
    "src/pontius/legal_river_quotient_base_provenance.py",
    "src/pontius/legal_river_quotient_global_separation_topologies.py",
    "src/pontius/legal_river_quotient_selective_certified_separation.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_runner.py",
    "src/pontius/durable_evidence_journal.py",
    "artifacts/work_preflight/.gitattributes",
)

_PARENT_BINDINGS = (
    "RESULT_RELATIVE_PATH",
    "RESULT_PATH",
    "PREREGISTRATION_COMMIT",
    "LITERAL_WORKER_MODULE",
    "PROTOCOL_SHA256",
    "CAMPAIGN_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "_MODE_ENV",
    "_CHALLENGE_ENV",
    "_SPOOL_ENV",
    "_SOURCE_PROBE",
    "_CAMPAIGN_CHILD",
    "_EVENT_PREFIX",
    "_ACK_PREFIX",
    "_git",
    "_header_payload",
)
_BINDING_LOCK = RLock()


def verify_absolute_git() -> dict[str, object]:
    if not GIT_PATH.is_file():
        raise FileNotFoundError("absolute Git executable is absent")
    raw = GIT_PATH.read_bytes()
    digest = sha256(raw).hexdigest()
    if len(raw) != GIT_BYTES or digest != GIT_SHA256:
        raise ValueError("absolute Git executable identity differs")
    return {
        "path": str(GIT_PATH),
        "bytes": len(raw),
        "sha256": digest,
        "provenance": "ADR-0443 host-file manifest",
    }


def _absolute_git(*arguments: str) -> bytes:
    verify_absolute_git()
    completed = subprocess.run(
        [str(GIT_PATH), *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        timeout=30.0,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode("utf-8", "replace")[:4096]
        raise RuntimeError(f"absolute-Git calibration metadata failed: {detail}")
    return completed.stdout


def _recovery_identity() -> dict[str, object]:
    if CONSUMED_RESULT_PATH.exists():
        raise FileExistsError("consumed calibration result unexpectedly exists")
    return {
        "schema_version": "pontius-adr0460-absolute-git-recovery-v1",
        "config_relative_path": RECOVERY_CONFIG_RELATIVE_PATH,
        "config_canonical_lf_sha256": RECOVERY_CONFIG_SHA256,
        "absolute_git": verify_absolute_git(),
        "predecessor": {
            "source_seal_commit": "88148da07324c13b79c72ea494b14167a975c001",
            "result_relative_path": CONSUMED_RESULT_RELATIVE_PATH,
            "result_exists": False,
            "terminal": "unjournaled_preowner_infrastructure_rejection",
            "exception_type": "FileNotFoundError",
            "exception_message": "[WinError 2] The system cannot find the file specified",
            "invocation_count": 1,
        },
        "scientific_source_canonical_lf_sha256": (
            "d38e96fd445f01a70113a8598094d0449a18271fa4d6ce992c781f0253ae821e"
        ),
        "literal_cuda_source_sha256": (
            "4f626802bd792788dff74c58adb90e7e30876e0c8f22d7fcb79de0c90334f8f7"
        ),
    }


@contextmanager
def configured_parent() -> Iterator[object]:
    """Bind fresh lifecycle identities and absolute Git, then restore them."""

    with _BINDING_LOCK:
        original = {name: getattr(_parent, name) for name in _PARENT_BINDINGS}
        inherited_header = _parent._header_payload

        def header_payload(git: Mapping[str, object]) -> dict[str, object]:
            payload = inherited_header(git)
            payload["absolute_git_recovery"] = _recovery_identity()
            return payload

        replacements = {
            "RESULT_RELATIVE_PATH": RESULT_RELATIVE_PATH,
            "RESULT_PATH": RESULT_PATH,
            "PREREGISTRATION_COMMIT": PREREGISTRATION_COMMIT,
            "LITERAL_WORKER_MODULE": LITERAL_WORKER_MODULE,
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
            "_git": _absolute_git,
            "_header_payload": header_payload,
        }
        for name, value in replacements.items():
            setattr(_parent, name, value)
        try:
            yield _parent
        finally:
            for name, value in original.items():
                setattr(_parent, name, value)


def source_seal_probe(challenge_hex: str) -> dict[str, object]:
    """Exercise absolute Git under the exact post-activation environment."""

    if (
        not isinstance(challenge_hex, str)
        or len(challenge_hex) != 64
        or any(character not in "0123456789abcdef" for character in challenge_hex)
    ):
        raise ValueError("absolute-Git source-probe challenge differs")
    if CONSUMED_RESULT_PATH.exists() or RESULT_PATH.exists():
        raise FileExistsError("absolute-Git source-probe result lifecycle differs")
    original = dict(os.environ)
    activated = _host.activate_bound_host_environment()
    _split.expected_child_runtime_evidence(activated.environment)
    try:
        _host._replace_process_environment(activated.environment)
        relative_resolution = shutil.which("git", path=os.environ.get("PATH"))
        if relative_resolution is not None:
            raise ValueError("activated environment unexpectedly resolves relative Git")
        version = _absolute_git("--version").decode("ascii").strip()
        commit = _absolute_git("rev-parse", "HEAD").decode("ascii").strip()
        if len(commit) != 40:
            raise ValueError("absolute-Git source-probe commit differs")
        return {
            "schema_version": "pontius-adr0460-absolute-git-source-probe-v1",
            "challenge_sha256": sha256(challenge_hex.encode("ascii")).hexdigest(),
            "relative_git_resolution": None,
            "absolute_git": verify_absolute_git(),
            "git_version": version,
            "source_commit": commit,
            "environment_replaced": True,
            "compiler_executed": False,
            "cupy_scientific_imported": False,
            "device_queried": False,
            "result_absent": True,
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
        raise RuntimeError("absolute-Git calibration requires no arguments and Python -B")
    mode = os.environ.get(_MODE_ENV)
    if mode == _SOURCE_PROBE:
        challenge = os.environ.get(_CHALLENGE_ENV)
        if not isinstance(challenge, str):
            raise ValueError("absolute-Git source-probe challenge is absent")
        print(canonical_journal_json_bytes(source_seal_probe(challenge)).decode("ascii"))
        return 0
    if mode == _CAMPAIGN_CHILD:
        if _CHALLENGE_ENV in os.environ:
            raise ValueError("absolute-Git campaign challenge is present")
        with configured_parent() as engine:
            return engine._campaign_child_main()
    if mode is not None or _SPOOL_ENV in os.environ or _CHALLENGE_ENV in os.environ:
        raise ValueError("absolute-Git public environment is contaminated")
    if CONSUMED_RESULT_PATH.exists():
        raise FileExistsError("consumed calibration unexpectedly has a result")
    if RESULT_PATH.exists():
        raise FileExistsError("absolute-Git calibration authority is already consumed")

    public_origin = perf_counter_ns()
    original = dict(os.environ)
    activated = _host.activate_bound_host_environment()
    _split.expected_child_runtime_evidence(activated.environment)
    execution = None
    try:
        _host._replace_process_environment(activated.environment)
        with configured_parent() as engine:
            execution = engine.execute_owner_to_path(
                output_path=RESULT_PATH,
                parent_environment=activated.environment,
                monotonic_ns=_public_clock(public_origin),
            )
    finally:
        os.environ.clear()
        os.environ.update(original)
    assert execution is not None
    print(
        "legal-river absolute-Git compiled calibration: "
        f"terminal={execution.terminal['terminal']} "
        f"passed={execution.terminal['passed']}"
    )
    return 0 if execution.terminal["passed"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CAMPAIGN_SHA256",
    "CONSUMED_RESULT_PATH",
    "CONSUMED_RESULT_RELATIVE_PATH",
    "DEPENDENCY_RELATIVE_PATHS",
    "GIT_BYTES",
    "GIT_PATH",
    "GIT_SHA256",
    "LITERAL_WORKER_MODULE",
    "PREREGISTRATION_COMMIT",
    "PROTOCOL_SHA256",
    "RECOVERY_CONFIG_RELATIVE_PATH",
    "RECOVERY_CONFIG_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "SCIENTIFIC_CONFIG_RELATIVE_PATH",
    "SCIENTIFIC_CONFIG_SHA256",
    "configured_parent",
    "main",
    "source_seal_probe",
    "verify_absolute_git",
]
