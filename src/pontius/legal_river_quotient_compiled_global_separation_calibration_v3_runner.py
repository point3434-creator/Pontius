"""Fresh ADR-0463 owner for the kernel-launch arity successor."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from hashlib import sha256
import os
from pathlib import Path
import shutil
import sys
from threading import RLock
from time import perf_counter_ns

from . import legal_river_quotient_compiled_global_separation_calibration as _parent_science
from . import legal_river_quotient_compiled_global_separation_calibration_runner as _parent
from . import legal_river_quotient_compiled_global_separation_calibration_v2_runner as _v2
from . import legal_river_quotient_compiled_global_separation_calibration_v3 as _science
from . import legal_river_quotient_fixed_width_device_preflight_v2_runner as _host
from . import legal_river_quotient_fixed_width_device_preflight_v3_runner as _split
from .durable_evidence_journal import canonical_journal_json_bytes
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
    "legal-river-quotient-compiled-global-separation-calibration-v4-launch-abi-completeness.json"
)
RECOVERY_CONFIG_SHA256 = (
    "58668f557bcc1f3420454124b8d930d7e59a9d1a870003a8093776f1175d9a92"
)
PREREGISTRATION_COMMIT = "e0a53d161fe27b95556ff73844253b352d223cfd"
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v3.jsonl"
)
RESULT_PATH = ROOT / RESULT_RELATIVE_PATH
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration_v3_runner"
)
SCIENTIFIC_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration_v3"
)
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0463-launch-abi-compiled-separation-owner-v3"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0463-launch-abi-compiled-separation-campaign-v3"
).hexdigest()

_MODE_ENV = "PONTIUS_ADR0463_COMPILED_SEPARATION_MODE"
_CHALLENGE_ENV = "PONTIUS_ADR0463_COMPILED_SEPARATION_CHALLENGE"
_SPOOL_ENV = "PONTIUS_ADR0463_COMPILED_SEPARATION_SPOOL"
_SOURCE_PROBE = "launch_arity_source_probe_v3"
_CAMPAIGN_CHILD = "campaign_child_v3"
_EVENT_PREFIX = b"PONTIUS_ADR0463_EVENT "
_ACK_PREFIX = b"PONTIUS_ADR0463_ACK "

DEPENDENCY_RELATIVE_PATHS = (
    RECOVERY_CONFIG_RELATIVE_PATH,
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
    "run_legal_river_quotient_compiled_global_separation_calibration_v3.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v3_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v3.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_v2_outcome.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration_v2_outcome.py",
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
    "SCIENTIFIC_MODULE",
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
    "_header_payload",
)
_BINDING_LOCK = RLock()
_PARENT_SCIENCE_MODULE_KEY = _parent.SCIENTIFIC_MODULE


def _launch_abi_identity() -> dict[str, object]:
    outcome = assess_compiled_calibration_v2_outcome_file()
    if RESULT_PATH.exists():
        raise FileExistsError("launch-arity successor result already exists")
    return {
        "schema_version": "pontius-adr0464-launch-abi-completeness-recovery-v1",
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
        "parent_scientific_source_canonical_lf_sha256": (
            _science.PARENT_SOURCE_CANONICAL_LF_SHA256
        ),
        "effective_scientific_source_sha256": (
            _science.EFFECTIVE_SCIENTIFIC_SOURCE_SHA256
        ),
        "literal_cuda_source_sha256": _science.CUDA_SOURCE_SHA256,
        "launch_arity_contract": _science.launch_arity_contract(),
        "only_scientific_delta": (
            "timed RRNS direct source_count insertion, selected-leaf obsolete "
            "scan_count removal, and declaration-derived central launch-arity guard"
        ),
    }


@contextmanager
def configured_parent() -> Iterator[object]:
    """Layer fresh v3 identities over the source-sealed absolute-Git owner."""

    with _BINDING_LOCK, _v2.configured_parent() as engine:
        original = {name: getattr(engine, name) for name in _PARENT_BINDINGS}
        inherited_header = engine._header_payload

        def header_payload(git: Mapping[str, object]) -> dict[str, object]:
            payload = inherited_header(git)
            payload["launch_abi_recovery"] = _launch_abi_identity()
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
            "_header_payload": header_payload,
        }
        for name, value in replacements.items():
            setattr(engine, name, value)
        try:
            yield engine
        finally:
            for name, value in original.items():
                setattr(engine, name, value)


@contextmanager
def _fresh_scientific_module_alias() -> Iterator[None]:
    previous = sys.modules.get(_PARENT_SCIENCE_MODULE_KEY)
    sys.modules[_PARENT_SCIENCE_MODULE_KEY] = _science
    try:
        yield
    finally:
        if previous is None:
            sys.modules.pop(_PARENT_SCIENCE_MODULE_KEY, None)
        else:
            sys.modules[_PARENT_SCIENCE_MODULE_KEY] = previous


def source_seal_probe(challenge_hex: str) -> dict[str, object]:
    if (
        not isinstance(challenge_hex, str)
        or len(challenge_hex) != 64
        or any(character not in "0123456789abcdef" for character in challenge_hex)
    ):
        raise ValueError("launch-arity source-probe challenge differs")
    outcome = assess_compiled_calibration_v2_outcome_file()
    if RESULT_PATH.exists():
        raise FileExistsError("launch-arity source-probe result exists")
    original = dict(os.environ)
    activated = _host.activate_bound_host_environment()
    _split.expected_child_runtime_evidence(activated.environment)
    try:
        _host._replace_process_environment(activated.environment)
        if shutil.which("git", path=os.environ.get("PATH")) is not None:
            raise ValueError("activated environment unexpectedly resolves relative Git")
        version = _v2._absolute_git("--version").decode("ascii").strip()
        commit = _v2._absolute_git("rev-parse", "HEAD").decode("ascii").strip()
        return {
            "schema_version": "pontius-adr0463-launch-arity-source-probe-v1",
            "challenge_sha256": sha256(challenge_hex.encode("ascii")).hexdigest(),
            "relative_git_resolution": None,
            "git_version": version,
            "source_commit": commit,
            "consumed_result_sha256": CONSUMED_RESULT_SHA256,
            "consumed_terminal": outcome.terminal,
            "launch_arity_manifest_sha256": (
                _science.KERNEL_SIGNATURE_MANIFEST_SHA256
            ),
            "kernel_count": len(_science.KERNEL_SIGNATURES),
            "environment_replaced": True,
            "compiler_executed": False,
            "cupy_scientific_imported": False,
            "device_queried": False,
            "fresh_result_absent": True,
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
        raise RuntimeError("launch-arity calibration requires no arguments and Python -B")
    mode = os.environ.get(_MODE_ENV)
    if mode == _SOURCE_PROBE:
        challenge = os.environ.get(_CHALLENGE_ENV)
        if not isinstance(challenge, str):
            raise ValueError("launch-arity source-probe challenge is absent")
        print(canonical_journal_json_bytes(source_seal_probe(challenge)).decode("ascii"))
        return 0
    if mode == _CAMPAIGN_CHILD:
        if _CHALLENGE_ENV in os.environ:
            raise ValueError("launch-arity campaign challenge is present")
        with configured_parent() as engine, _fresh_scientific_module_alias():
            return engine._campaign_child_main()
    if mode is not None or _SPOOL_ENV in os.environ or _CHALLENGE_ENV in os.environ:
        raise ValueError("launch-arity public environment is contaminated")
    assess_compiled_calibration_v2_outcome_file()
    if RESULT_PATH.exists():
        raise FileExistsError("launch-arity calibration authority is already consumed")

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
        "legal-river launch-arity compiled calibration: "
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
    "LITERAL_WORKER_MODULE",
    "PREREGISTRATION_COMMIT",
    "PROTOCOL_SHA256",
    "RECOVERY_CONFIG_RELATIVE_PATH",
    "RECOVERY_CONFIG_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "SCIENTIFIC_MODULE",
    "configured_parent",
    "main",
    "source_seal_probe",
]
