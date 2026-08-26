"""Bootstrap-safe additive owner for the ADR-0398 work preflight.

This module does not import the consumed v1 owner.  Handshake and campaign
children are launched through one literal-module subprocess transport.  The
handshake path imports neither CuPy nor the unchanged scientific source.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from queue import Empty, Full, Queue
import secrets
import subprocess
import sys
from threading import Event, Thread
from time import perf_counter_ns
from typing import Any, Callable, Mapping

from .durable_evidence_journal import (
    DurableEvidenceJournalWriter,
    JournalRecordKind,
    canonical_journal_json_bytes,
)


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-owner-v2.json"
)
V1_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-v1.json"
)
CORRECTION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-v2.json"
)
V1_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v1.jsonl"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v2.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
_CONFIG = _ROOT / CONFIG_RELATIVE_PATH
_V1_CONFIG = _ROOT / V1_CONFIG_RELATIVE_PATH
_CORRECTION_CONFIG = _ROOT / CORRECTION_CONFIG_RELATIVE_PATH
_V1_RESULT = _ROOT / V1_RESULT_RELATIVE_PATH
_OUTPUT = _ROOT / RESULT_RELATIVE_PATH
_RESERVED = _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH

PREREGISTERED_CONFIG_SHA256 = (
    "e7f2a60035aad77d20461b4e5288bd85375f751b2d9ec410d2f197cfcacaf334"
)
V1_CONFIG_SHA256 = (
    "88a16d62cf978ec61b7481c79b841eda6a2844a41f374c122a21be5310550d3c"
)
CORRECTION_CONFIG_SHA256 = (
    "a522858696c8266485f7aac4b9c2dbb5f0d0c35e59d3e1515f4674d802ac890c"
)
V1_RESULT_SHA256 = (
    "fd8c71ddb534320577dfc9a390946fc3dffe3fe806bf93d456ac33e55fe8e830"
)
V1_RESULT_BYTES = 5322
V1_RESULT_RECORDS = 3
PREREGISTRATION_COMMIT = "2432bee9d003edda665673652b790f9a44e0b120"

WORK_PREFLIGHT_V2_PROTOCOL_SHA256 = sha256(
    b"pontius-adr0398-work-preflight-bootstrap-safe-exclusive-journal-v2"
).hexdigest()
WORK_PREFLIGHT_V2_CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0398-work-preflight-bootstrap-safe-one-shot-campaign-v2"
).hexdigest()
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_cuda_compensated_work_preflight_v2_runner"
)
_CHILD_MODE_ENV = "PONTIUS_ADR0398_WORK_PREFLIGHT_CHILD_MODE"
_CHILD_CHALLENGE_ENV = "PONTIUS_ADR0398_WORK_PREFLIGHT_CHILD_CHALLENGE"
_HANDSHAKE_MODE = "handshake"
_CAMPAIGN_MODE = "campaign"
_EVENT_PREFIX = "PONTIUS_ADR0398_EVENT "

HANDSHAKE_WALL_LIMIT_NS = 10_000_000_000
LABORATORY_WALL_LIMIT_NS = 240_000_000_000
MAXIMUM_EVENT_COUNT = 4096
MAXIMUM_ARTIFACT_BYTES = 16_777_216
MAXIMUM_CHILD_LINE_CHARACTERS = 1_048_576
MAXIMUM_STDERR_CHARACTERS = 4096

CLAIMS = {
    "bootstrap_handshake_result": None,
    "real_compiler_resource_result": None,
    "calibration_result": None,
    "complete_25_numerical_value": None,
    "actual_45_card_value": None,
    "resolver_iteration_result": None,
    "solve_result": None,
    "action_result": None,
    "action_clock_result": None,
    "decision_quality_result": None,
    "truncation_authorized": False,
    "blueprint_result": None,
    "poker_strength_result": None,
}


@dataclass(frozen=True, slots=True)
class LoadedConfig:
    payload: Mapping[str, object]
    sha256: str


@dataclass(frozen=True, slots=True)
class RetainedV1Evidence:
    sha256: str
    byte_count: int
    record_count: int
    terminal: str
    event_count: int
    phase_count: int
    passed: bool
    projection: Mapping[str, object] | None


@dataclass(frozen=True, slots=True)
class BootstrapHandshake:
    event: Mapping[str, object]
    expected_challenge_sha256: str


@dataclass(frozen=True, slots=True)
class OwnerExecution:
    terminal: Mapping[str, object]
    event_count: int


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"work-preflight v2 path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def parse_config(config: Mapping[str, Any]) -> dict[str, object]:
    if not isinstance(config, Mapping) or config.get("schema_version") != (
        "legal-river-quotient-cuda-compensated-work-preflight-owner-config-v2"
    ):
        raise ValueError("work-preflight v2 config schema differs")
    parsed = dict(config)
    parent = parsed.get("parent_identity")
    retained = parsed.get("retained_v1_terminal")
    scope = parsed.get("successor_scope")
    identity = parsed.get("new_identity_contract")
    handshake = parsed.get("bootstrap_handshake")
    science = parsed.get("inherited_science")
    lifecycle = parsed.get("one_shot_lifecycle")
    if not all(
        isinstance(value, Mapping)
        for value in (parent, retained, scope, identity, handshake, science, lifecycle)
    ):
        raise ValueError("work-preflight v2 config sections are malformed")
    assert isinstance(parent, Mapping)
    assert isinstance(retained, Mapping)
    assert isinstance(scope, Mapping)
    assert isinstance(identity, Mapping)
    assert isinstance(handshake, Mapping)
    assert isinstance(science, Mapping)
    assert isinstance(lifecycle, Mapping)
    if (
        identity.get("owner_protocol_sha256") != WORK_PREFLIGHT_V2_PROTOCOL_SHA256
        or identity.get("campaign_sha256") != WORK_PREFLIGHT_V2_CAMPAIGN_SHA256
        or handshake.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or handshake.get("challenge_bytes") != 32
        or handshake.get("handshake_wall_limit_ns") != HANDSHAKE_WALL_LIMIT_NS
        or lifecycle.get("laboratory_total_wall_limit_ns", LABORATORY_WALL_LIMIT_NS)
        != LABORATORY_WALL_LIMIT_NS
        or lifecycle.get("maximum_event_count") != MAXIMUM_EVENT_COUNT
        or lifecycle.get("maximum_artifact_bytes") != MAXIMUM_ARTIFACT_BYTES
    ):
        raise ValueError("work-preflight v2 lifecycle contract differs")
    if (
        retained.get("result_sha256") != V1_RESULT_SHA256
        or retained.get("result_bytes") != V1_RESULT_BYTES
        or retained.get("record_count") != V1_RESULT_RECORDS
        or retained.get("terminal") != "infrastructure_failure"
        or retained.get("phase_count") != 0
        or retained.get("projection") is not None
    ):
        raise ValueError("work-preflight retained v1 identity differs")
    if (
        scope.get("v2_result_relative_path") != RESULT_RELATIVE_PATH
        or scope.get("reserved_actual_result_relative_path")
        != RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        or scope.get("population_25_fixture_compile_allocation_launch_scalar_digest_or_gate_forbidden")
        is not True
        or science.get("calibration_populations") != [10, 22]
        or science.get("projection_population_integer_only") != 25
        or science.get("phase_count") != 16
        or science.get("laboratory_total_wall_limit_ns") != LABORATORY_WALL_LIMIT_NS
        or science.get("target_projection_wall_limit_ns") != 180_000_000_000
        or science.get("exact_spill_load_store_count") is not None
    ):
        raise ValueError("work-preflight v2 scientific boundary differs")
    return parsed


_BOUND_PARENT_FIELDS = {
    "adr0394": "adr0394_relative_path",
    "adr0395": "adr0395_relative_path",
    "adr0396": "adr0396_relative_path",
    "adr0397": "adr0397_relative_path",
    "v1_preregistration_config": "v1_preregistration_config_relative_path",
    "resource_correction_config": "resource_correction_config_relative_path",
    "scientific_source": "scientific_source_relative_path",
    "v1_runner": "v1_runner_relative_path",
    "v1_reader": "v1_reader_relative_path",
    "v1_controls": "v1_controls_relative_path",
    "durable_journal": "durable_journal_relative_path",
}


def _validate_bound_parent_files(config: Mapping[str, object]) -> None:
    parent = config["parent_identity"]
    assert isinstance(parent, Mapping)
    for label, path_field in _BOUND_PARENT_FIELDS.items():
        relative = parent.get(path_field)
        expected = parent.get(f"{label}_canonical_lf_sha256")
        if not isinstance(relative, str) or canonical_lf_sha256(_ROOT / relative) != expected:
            raise ValueError(f"work-preflight v2 bound parent differs: {label}")


def load_public_config(path: Path = _CONFIG) -> LoadedConfig:
    if not isinstance(path, Path):
        raise TypeError("work-preflight v2 config path must be a Path")
    raw = path.read_bytes()
    digest = sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    if digest != PREREGISTERED_CONFIG_SHA256:
        raise ValueError("work-preflight v2 config differs from ADR-0398")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("work-preflight v2 config must be an object")
    parsed = parse_config(value)
    _validate_bound_parent_files(parsed)
    return LoadedConfig(payload=parsed, sha256=digest)


def rebind_retained_v1(path: Path = _V1_RESULT) -> RetainedV1Evidence:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError("retained v1 work-preflight artifact is absent")
    raw = path.read_bytes()
    if len(raw) != V1_RESULT_BYTES or sha256(raw).hexdigest() != V1_RESULT_SHA256:
        raise ValueError("retained v1 work-preflight artifact differs")
    if len(raw.splitlines()) != V1_RESULT_RECORDS:
        raise ValueError("retained v1 work-preflight record count differs")
    from .legal_river_quotient_cuda_compensated_work_preflight_result import (
        rebind_work_preflight_journal,
    )

    rebound = rebind_work_preflight_journal(raw)
    if (
        rebound.terminal != "infrastructure_failure"
        or rebound.passed is not False
        or rebound.event_count != 1
        or len(rebound.phases) != 0
        or rebound.projection is not None
    ):
        raise ValueError("retained v1 work-preflight semantics differ")
    return RetainedV1Evidence(
        sha256=V1_RESULT_SHA256,
        byte_count=len(raw),
        record_count=len(raw.splitlines()),
        terminal=rebound.terminal,
        event_count=rebound.event_count,
        phase_count=len(rebound.phases),
        passed=rebound.passed,
        projection=rebound.projection,
    )


def _checked_git(*arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        timeout=30.0,
    )
    return completed.stdout


_TRACKED_REQUIRED = (
    CONFIG_RELATIVE_PATH,
    V1_RESULT_RELATIVE_PATH,
    "docs/decisions/ADR-0398-preregister-the-bootstrap-safe-work-preflight-v2-owner.md",
)


def strict_git_metadata(output_path: Path = _OUTPUT) -> dict[str, object]:
    commit = _checked_git("rev-parse", "HEAD").decode("ascii").strip()
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise RuntimeError("work-preflight v2 Git commit is malformed")
    for relative in _TRACKED_REQUIRED:
        _checked_git("ls-files", "--error-unmatch", "--", relative)
    raw = _checked_git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = [entry for entry in raw.split(b"\0") if entry]
    allowed = f"?? {output_path.relative_to(_ROOT).as_posix()}".encode("utf-8")
    if entries not in ([], [allowed]):
        raise RuntimeError("work-preflight v2 Git boundary is dirty")
    return {
        "commit": commit,
        "dirty": False,
        "strict_status": True,
        "result_is_only_untracked_path": entries == [allowed] or not entries,
        "tracked_prerequisites": True,
    }


_DEPENDENCY_PATHS = {
    "owner_config": _CONFIG,
    "preregistration_adr": _ROOT
    / "docs/decisions/ADR-0398-preregister-the-bootstrap-safe-work-preflight-v2-owner.md",
    "v1_config": _V1_CONFIG,
    "resource_correction_config": _CORRECTION_CONFIG,
    "resource_correction_adr": _ROOT
    / "docs/decisions/ADR-0395-correct-the-work-preflight-resource-instrument-before-result.md",
    "scientific_source": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
    "v1_runner": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_runner.py",
    "v1_reader": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_result.py",
    "v1_controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_work_preflight.py",
    "v2_runner": Path(__file__),
    "v2_reader": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_v2_result.py",
    "v2_controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_work_preflight_v2.py",
    "parent_source": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "parent_controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_tiles.py",
    "artifact_marker": _ROOT / "artifacts/work_preflight/README.md",
    "artifact_attributes": _ROOT / "artifacts/work_preflight/.gitattributes",
    "retained_v1_result": _V1_RESULT,
    "durable_journal": _ROOT / "src/pontius/durable_evidence_journal.py",
}


def dependency_hashes() -> dict[str, str]:
    return {
        label: canonical_lf_sha256(path)
        for label, path in _DEPENDENCY_PATHS.items()
    }


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _header_payload() -> dict[str, object]:
    return {
        "schema_version": "legal-river-work-preflight-owner-header-v2",
        "owner_protocol_sha256": WORK_PREFLIGHT_V2_PROTOCOL_SHA256,
        "campaign_sha256": WORK_PREFLIGHT_V2_CAMPAIGN_SHA256,
        "config_relative_path": CONFIG_RELATIVE_PATH,
        "config_sha256": PREREGISTERED_CONFIG_SHA256,
        "result_relative_path": RESULT_RELATIVE_PATH,
        "retained_v1_result_relative_path": V1_RESULT_RELATIVE_PATH,
        "retained_v1_result_sha256": V1_RESULT_SHA256,
        "reserved_actual_result_relative_path": RESERVED_ACTUAL_RESULT_RELATIVE_PATH,
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "literal_worker_module": LITERAL_WORKER_MODULE,
        "calibration_populations": [10, 22],
        "projection_population_integer_only": 25,
        "claims": dict(CLAIMS),
    }


def _terminal_payload(
    *,
    terminal: str,
    reason: str,
    event_count: int,
    last_event_semantic_identity_sha256: str | None,
    handshake_passed: bool,
) -> dict[str, object]:
    allowed = {
        "completed_capacity_pass",
        "completed_capacity_rejection",
        "calibration_scientific_rejection",
        "compiler_or_primitive_rejection",
        "laboratory_wall_rejection",
        "infrastructure_failure",
    }
    if terminal not in allowed:
        raise ValueError("work-preflight v2 terminal class is unknown")
    if not isinstance(reason, str) or not reason:
        raise ValueError("work-preflight v2 terminal reason must be nonempty")
    return {
        "schema_version": "legal-river-work-preflight-owner-terminal-v2",
        "terminal": terminal,
        "reason": reason[:4096],
        "passed": terminal == "completed_capacity_pass",
        "event_count": event_count,
        "last_event_semantic_identity_sha256": last_event_semantic_identity_sha256,
        "handshake_passed": handshake_passed,
        "claims": dict(CLAIMS),
    }


def _failure_reason(error: BaseException) -> str:
    message = str(error) or "exception carried no message"
    return f"{type(error).__name__}: {message[:4096]}"


def _event_observation(
    *,
    event_index: int,
    event_kind: str,
    event: Mapping[str, object],
    config_sha256: str,
    source_commit: str,
) -> dict[str, object]:
    if not isinstance(event_kind, str) or not event_kind:
        raise ValueError("work-preflight v2 event kind must be nonempty")
    return {
        "schema_version": "legal-river-work-preflight-owner-observation-v2",
        "event_index": event_index,
        "event_kind": event_kind,
        "config_sha256": config_sha256,
        "v1_config_sha256": V1_CONFIG_SHA256,
        "correction_config_sha256": CORRECTION_CONFIG_SHA256,
        "source_commit": source_commit,
        "event": dict(event),
    }


def _child_emit(kind: str, payload: Mapping[str, object]) -> None:
    line = json.dumps(
        {"kind": kind, "payload": dict(payload)},
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    print(_EVENT_PREFIX + line, flush=True)


def _handshake_child_main(challenge_hex: str) -> int:
    if (
        len(challenge_hex) != 64
        or any(character not in "0123456789abcdef" for character in challenge_hex)
    ):
        raise ValueError("work-preflight v2 child challenge is malformed")
    scientific_module = (
        "pontius.legal_river_quotient_cuda_compensated_work_preflight"
    )
    cupy_loaded = any(name == "cupy" or name.startswith("cupy.") for name in sys.modules)
    event = {
        "schema_version": "legal-river-work-preflight-bootstrap-handshake-v2",
        "challenge_sha256": sha256(bytes.fromhex(challenge_hex)).hexdigest(),
        "literal_worker_module": LITERAL_WORKER_MODULE,
        "spec_name": None if __spec__ is None else __spec__.name,
        "runtime_name": __name__,
        "package_name": __package__,
        "python_no_bytecode": sys.dont_write_bytecode,
        "argv_count": len(sys.argv),
        "cupy_loaded": cupy_loaded,
        "scientific_source_loaded": scientific_module in sys.modules,
    }
    _child_emit("bootstrap_handshake", event)
    _child_emit(
        "child_terminal",
        {
            "schema_version": "legal-river-work-preflight-bootstrap-terminal-v2",
            "terminal": "bootstrap_handshake_pass",
            "passed": True,
        },
    )
    return 0


def _campaign_child_main() -> int:
    from .legal_river_quotient_cuda_compensated_work_preflight import (
        run_calibration_preflight,
    )

    try:
        terminal = run_calibration_preflight(_child_emit)
        _child_emit("child_terminal", terminal)
        return 0
    except BaseException as error:  # noqa: BLE001 - first failure is evidence
        _child_emit(
            "worker_failure",
            {
                "schema_version": "legal-river-work-preflight-worker-failure-v2",
                "reason": _failure_reason(error),
            },
        )
        return 1


ChildProcessExecutor = Callable[
    [str, str | None, Callable[[str, Mapping[str, object]], None], int],
    Mapping[str, object],
]


def _run_child_process(
    mode: str,
    challenge_hex: str | None,
    emit: Callable[[str, Mapping[str, object]], None],
    wall_limit_ns: int,
) -> Mapping[str, object]:
    if mode not in {_HANDSHAKE_MODE, _CAMPAIGN_MODE}:
        raise ValueError("work-preflight v2 child mode differs")
    if isinstance(wall_limit_ns, bool) or not isinstance(wall_limit_ns, int) or wall_limit_ns <= 0:
        raise ValueError("work-preflight v2 child wall must be positive")
    if mode == _HANDSHAKE_MODE:
        if not isinstance(challenge_hex, str):
            raise ValueError("work-preflight v2 handshake challenge is absent")
    elif challenge_hex is not None:
        raise ValueError("work-preflight v2 campaign cannot carry a challenge")

    environment = os.environ.copy()
    environment.pop(_CHILD_MODE_ENV, None)
    environment.pop(_CHILD_CHALLENGE_ENV, None)
    environment[_CHILD_MODE_ENV] = mode
    if challenge_hex is not None:
        environment[_CHILD_CHALLENGE_ENV] = challenge_hex
    process = subprocess.Popen(
        [sys.executable, "-B", "-m", LITERAL_WORKER_MODULE],
        cwd=_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="ascii",
        errors="strict",
        bufsize=1,
    )
    queue: Queue[object] = Queue(maxsize=64)
    stop_reader = Event()
    stderr_chunks: list[str] = []
    stderr_length = 0

    def read_stdout() -> None:
        def put(item: object) -> bool:
            while not stop_reader.is_set():
                try:
                    queue.put(item, timeout=0.1)
                    return True
                except Full:
                    continue
            return False

        try:
            assert process.stdout is not None
            for line in process.stdout:
                if len(line) > MAXIMUM_CHILD_LINE_CHARACTERS:
                    put(RuntimeError("work-preflight v2 child line exceeds ceiling"))
                    return
                if not put(line):
                    return
        except BaseException as error:  # noqa: BLE001 - transport failure is evidence
            put(error)
        finally:
            put(None)

    def read_stderr() -> None:
        nonlocal stderr_length
        try:
            assert process.stderr is not None
            while True:
                chunk = process.stderr.read(4096)
                if not chunk:
                    return
                remaining = MAXIMUM_STDERR_CHARACTERS - stderr_length
                if remaining > 0:
                    stderr_chunks.append(chunk[:remaining])
                    stderr_length += min(len(chunk), remaining)
        except BaseException as error:  # noqa: BLE001 - retain bounded diagnostic
            text = f"<stderr-read-failure:{type(error).__name__}>"
            remaining = MAXIMUM_STDERR_CHARACTERS - stderr_length
            if remaining > 0:
                stderr_chunks.append(text[:remaining])
                stderr_length += min(len(text), remaining)

    stdout_thread = Thread(target=read_stdout, daemon=True)
    stderr_thread = Thread(target=read_stderr, daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    started = perf_counter_ns()
    child_terminal: Mapping[str, object] | None = None
    child_failure: str | None = None
    stdout_closed = False
    child_event_count = 0
    try:
        while True:
            remaining_ns = wall_limit_ns - (perf_counter_ns() - started)
            if remaining_ns <= 0:
                process.kill()
                process.wait(timeout=30.0)
                raise TimeoutError("child_wall_crossed")
            if stdout_closed and process.poll() is not None:
                break
            try:
                item = queue.get(timeout=min(1.0, remaining_ns / 1_000_000_000))
            except Empty:
                if process.poll() is not None and stdout_closed:
                    break
                continue
            if item is None:
                stdout_closed = True
                continue
            if isinstance(item, BaseException):
                raise RuntimeError("work-preflight v2 child stdout reader failed") from item
            if not isinstance(item, str) or not item.startswith(_EVENT_PREFIX):
                raise RuntimeError("work-preflight v2 child emitted an unframed line")
            value = json.loads(item[len(_EVENT_PREFIX):])
            if not isinstance(value, dict) or set(value) != {"kind", "payload"}:
                raise RuntimeError("work-preflight v2 child event is malformed")
            kind = value["kind"]
            payload = value["payload"]
            if not isinstance(kind, str) or not isinstance(payload, dict):
                raise RuntimeError("work-preflight v2 child event types differ")
            if kind == "child_terminal":
                if child_terminal is not None or child_failure is not None:
                    raise RuntimeError("work-preflight v2 child terminal conflicts or repeats")
                child_terminal = payload
            elif kind == "worker_failure":
                if child_terminal is not None or child_failure is not None:
                    raise RuntimeError("work-preflight v2 child failure conflicts or repeats")
                child_failure = str(payload.get("reason", "worker failed"))
            else:
                if child_terminal is not None or child_failure is not None:
                    raise RuntimeError("work-preflight v2 child event follows terminal")
                if child_event_count >= MAXIMUM_EVENT_COUNT:
                    raise RuntimeError("work-preflight v2 child event count exceeds ceiling")
                emit(kind, payload)
                child_event_count += 1
        return_code = process.wait(timeout=30.0)
        stdout_thread.join(timeout=5.0)
        stderr_thread.join(timeout=5.0)
        if child_failure is not None:
            raise RuntimeError(child_failure)
        if return_code != 0:
            stderr = "".join(stderr_chunks)
            raise RuntimeError(f"work-preflight v2 child exited {return_code}: {stderr}")
        if child_terminal is None:
            raise RuntimeError("work-preflight v2 child omitted terminal evidence")
        return child_terminal
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=30.0)
        stop_reader.set()
        stdout_thread.join(timeout=5.0)
        stderr_thread.join(timeout=5.0)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()


def _validated_handshake_event(
    event: Mapping[str, object],
    *,
    expected_challenge_sha256: str,
) -> dict[str, object]:
    expected_keys = {
        "schema_version",
        "challenge_sha256",
        "literal_worker_module",
        "spec_name",
        "runtime_name",
        "package_name",
        "python_no_bytecode",
        "argv_count",
        "cupy_loaded",
        "scientific_source_loaded",
    }
    if not isinstance(event, Mapping) or set(event) != expected_keys:
        raise ValueError("work-preflight v2 handshake fields differ")
    if (
        event.get("schema_version")
        != "legal-river-work-preflight-bootstrap-handshake-v2"
        or event.get("challenge_sha256") != expected_challenge_sha256
        or event.get("literal_worker_module") != LITERAL_WORKER_MODULE
        or event.get("spec_name") != LITERAL_WORKER_MODULE
        or event.get("runtime_name") != "__main__"
        or event.get("package_name") != "pontius"
        or event.get("python_no_bytecode") is not True
        or event.get("argv_count") != 1
        or event.get("cupy_loaded") is not False
        or event.get("scientific_source_loaded") is not False
    ):
        raise ValueError("work-preflight v2 handshake contract differs")
    _require_digest(event.get("challenge_sha256"), label="handshake challenge")
    return dict(event)


def run_no_cuda_bootstrap_handshake(
    *,
    challenge_factory: Callable[[int], bytes] = secrets.token_bytes,
    process_executor: ChildProcessExecutor = _run_child_process,
) -> BootstrapHandshake:
    challenge = challenge_factory(32)
    if not isinstance(challenge, bytes) or len(challenge) != 32:
        raise ValueError("work-preflight v2 challenge factory differs")
    challenge_hex = challenge.hex()
    challenge_digest = sha256(challenge).hexdigest()
    events: list[tuple[str, Mapping[str, object]]] = []

    def collect(kind: str, payload: Mapping[str, object]) -> None:
        events.append((kind, dict(payload)))

    try:
        terminal = process_executor(
            _HANDSHAKE_MODE,
            challenge_hex,
            collect,
            HANDSHAKE_WALL_LIMIT_NS,
        )
    except BaseException as error:  # noqa: BLE001 - type bootstrap failures uniformly
        raise RuntimeError(f"bootstrap_handshake_failed: {_failure_reason(error)}") from error
    if len(events) != 1 or events[0][0] != "bootstrap_handshake":
        raise ValueError("work-preflight v2 handshake event sequence differs")
    if (
        not isinstance(terminal, Mapping)
        or terminal.get("schema_version")
        != "legal-river-work-preflight-bootstrap-terminal-v2"
        or terminal.get("terminal") != "bootstrap_handshake_pass"
        or terminal.get("passed") is not True
        or set(terminal) != {"schema_version", "terminal", "passed"}
    ):
        raise ValueError("work-preflight v2 handshake terminal differs")
    event = _validated_handshake_event(
        events[0][1],
        expected_challenge_sha256=challenge_digest,
    )
    return BootstrapHandshake(
        event=event,
        expected_challenge_sha256=challenge_digest,
    )


CampaignExecutor = Callable[
    [Callable[[str, Mapping[str, object]], None], int],
    Mapping[str, object],
]
HandshakeExecutor = Callable[[], BootstrapHandshake]


def _subprocess_campaign_executor(
    emit: Callable[[str, Mapping[str, object]], None],
    wall_limit_ns: int,
) -> Mapping[str, object]:
    return _run_child_process(_CAMPAIGN_MODE, None, emit, wall_limit_ns)


def execute_owner_to_path(
    *,
    output_path: Path,
    config_loader: Callable[[], LoadedConfig] = load_public_config,
    git_loader: Callable[[], Mapping[str, object]] = strict_git_metadata,
    hashes_loader: Callable[[], Mapping[str, str]] = dependency_hashes,
    v1_loader: Callable[[], RetainedV1Evidence] = rebind_retained_v1,
    handshake_executor: HandshakeExecutor = run_no_cuda_bootstrap_handshake,
    campaign_executor: CampaignExecutor = _subprocess_campaign_executor,
    reserved_path: Path = _RESERVED,
    monotonic_ns: Callable[[], int] = perf_counter_ns,
) -> OwnerExecution:
    """Consume one v2 path; tests may inject science but not bootstrap authority."""

    if not isinstance(output_path, Path):
        raise TypeError("work-preflight v2 output must be a Path")
    if not isinstance(reserved_path, Path):
        raise TypeError("work-preflight v2 reserved path must be a Path")
    terminal_payload: dict[str, object]
    event_count = 0
    last_event_identity: str | None = None
    handshake_passed = False
    with DurableEvidenceJournalWriter.create(
        path=output_path,
        protocol_sha256=WORK_PREFLIGHT_V2_PROTOCOL_SHA256,
        campaign_sha256=WORK_PREFLIGHT_V2_CAMPAIGN_SHA256,
    ) as writer:
        header = _header_payload()
        writer.append(
            kind=JournalRecordKind.HEADER,
            semantic_identity_sha256=_semantic_digest(header),
            payload=header,
        )
        try:
            loaded = config_loader()
            if not isinstance(loaded, LoadedConfig):
                raise TypeError("work-preflight v2 config loader returned wrong type")
            parse_config(loaded.payload)
            git = git_loader()
            if (
                git.get("dirty") is not False
                or git.get("strict_status") is not True
                or not isinstance(git.get("commit"), str)
            ):
                raise RuntimeError("work-preflight v2 strict Git boundary rejected")
            retained_v1 = v1_loader()
            if not isinstance(retained_v1, RetainedV1Evidence):
                raise TypeError("work-preflight v2 v1 loader returned wrong type")
            provenance = {
                "schema_version": "legal-river-work-preflight-provenance-v2",
                "config_sha256": loaded.sha256,
                "v1_config_sha256": V1_CONFIG_SHA256,
                "correction_config_sha256": CORRECTION_CONFIG_SHA256,
                "source_commit": str(git["commit"]),
                "source_dirty": False,
                "dependency_hashes": dict(hashes_loader()),
                "retained_v1": {
                    "sha256": retained_v1.sha256,
                    "byte_count": retained_v1.byte_count,
                    "record_count": retained_v1.record_count,
                    "terminal": retained_v1.terminal,
                    "event_count": retained_v1.event_count,
                    "phase_count": retained_v1.phase_count,
                    "passed": retained_v1.passed,
                    "projection": retained_v1.projection,
                },
                "literal_worker_module": LITERAL_WORKER_MODULE,
                "reserved_actual_result_absent": not reserved_path.exists(),
            }

            def append_event(kind: str, event: Mapping[str, object]) -> None:
                nonlocal event_count, last_event_identity
                if event_count >= MAXIMUM_EVENT_COUNT:
                    raise RuntimeError("work-preflight v2 event count exceeds ceiling")
                observation = _event_observation(
                    event_index=event_count,
                    event_kind=kind,
                    event=event,
                    config_sha256=loaded.sha256,
                    source_commit=str(git["commit"]),
                )
                identity = _semantic_digest(observation)
                writer.append(
                    kind=JournalRecordKind.OBSERVATION,
                    semantic_identity_sha256=identity,
                    payload=observation,
                )
                event_count += 1
                last_event_identity = identity

            append_event("provenance", provenance)
            if provenance["reserved_actual_result_absent"] is not True:
                raise RuntimeError("reserved actual authority is present")

            laboratory_started = monotonic_ns()
            handshake = handshake_executor()
            if not isinstance(handshake, BootstrapHandshake):
                raise TypeError("work-preflight v2 handshake executor returned wrong type")
            accepted_handshake = _validated_handshake_event(
                handshake.event,
                expected_challenge_sha256=handshake.expected_challenge_sha256,
            )
            append_event(
                "bootstrap_handshake",
                {
                    "schema_version": (
                        "legal-river-work-preflight-bootstrap-accepted-v2"
                    ),
                    "parent_challenge_sha256": (
                        handshake.expected_challenge_sha256
                    ),
                    "child": accepted_handshake,
                },
            )
            handshake_passed = True
            elapsed = monotonic_ns() - laboratory_started
            remaining = LABORATORY_WALL_LIMIT_NS - elapsed
            if remaining <= 0:
                raise TimeoutError("laboratory_wall_crossed_after_handshake")

            def append_scientific_event(kind: str, event: Mapping[str, object]) -> None:
                if kind in {"provenance", "bootstrap_handshake"}:
                    raise RuntimeError("scientific child emitted a reserved lifecycle event")
                append_event(kind, event)

            terminal_evidence = campaign_executor(append_scientific_event, remaining)
            laboratory_stop = monotonic_ns()
            if laboratory_stop - laboratory_started > LABORATORY_WALL_LIMIT_NS:
                terminal_payload = _terminal_payload(
                    terminal="laboratory_wall_rejection",
                    reason="laboratory_wall_crossed",
                    event_count=event_count,
                    last_event_semantic_identity_sha256=last_event_identity,
                    handshake_passed=handshake_passed,
                )
            else:
                if not isinstance(terminal_evidence, Mapping):
                    raise TypeError("work-preflight v2 campaign returned wrong type")
                terminal = terminal_evidence.get("terminal")
                passed = terminal_evidence.get("passed")
                if not isinstance(terminal, str) or not isinstance(passed, bool):
                    raise ValueError("work-preflight v2 terminal evidence is malformed")
                if passed is not (terminal == "completed_capacity_pass"):
                    raise ValueError("work-preflight v2 terminal pass bit disagrees")
                append_event("terminal_evidence", terminal_evidence)
                terminal_payload = _terminal_payload(
                    terminal=terminal,
                    reason="retained first terminal evidence",
                    event_count=event_count,
                    last_event_semantic_identity_sha256=last_event_identity,
                    handshake_passed=handshake_passed,
                )
        except TimeoutError as error:
            terminal_payload = _terminal_payload(
                terminal="laboratory_wall_rejection",
                reason=_failure_reason(error),
                event_count=event_count,
                last_event_semantic_identity_sha256=last_event_identity,
                handshake_passed=handshake_passed,
            )
        except BaseException as error:  # noqa: BLE001 - first failure is evidence
            terminal_payload = _terminal_payload(
                terminal="infrastructure_failure",
                reason=_failure_reason(error),
                event_count=event_count,
                last_event_semantic_identity_sha256=last_event_identity,
                handshake_passed=handshake_passed,
            )
        writer.append(
            kind=JournalRecordKind.TERMINAL,
            semantic_identity_sha256=_semantic_digest(terminal_payload),
            payload=terminal_payload,
        )
    if output_path.stat().st_size > MAXIMUM_ARTIFACT_BYTES:
        raise RuntimeError("work-preflight v2 journal exceeds byte ceiling")
    return OwnerExecution(terminal=terminal_payload, event_count=event_count)


def main() -> None:
    if len(sys.argv) != 1:
        raise ValueError("work-preflight v2 owner accepts no arguments")
    child_mode = os.environ.get(_CHILD_MODE_ENV)
    if child_mode is not None:
        if child_mode == _HANDSHAKE_MODE:
            challenge = os.environ.get(_CHILD_CHALLENGE_ENV)
            if not isinstance(challenge, str):
                raise ValueError("work-preflight v2 handshake challenge is absent")
            raise SystemExit(_handshake_child_main(challenge))
        if child_mode == _CAMPAIGN_MODE:
            if _CHILD_CHALLENGE_ENV in os.environ:
                raise ValueError("work-preflight v2 campaign challenge is present")
            raise SystemExit(_campaign_child_main())
        raise ValueError("work-preflight v2 child mode is unknown")
    if _OUTPUT.exists():
        raise FileExistsError("work-preflight v2 authority is already consumed")
    if not _V1_RESULT.is_file():
        raise FileNotFoundError("retained v1 authority is absent")
    if _RESERVED.exists():
        raise FileExistsError("reserved actual authority must remain absent")
    execution = execute_owner_to_path(output_path=_OUTPUT)
    print(
        "legal-river work preflight v2: "
        f"terminal={execution.terminal['terminal']} "
        f"passed={execution.terminal['passed']}"
    )
    if execution.terminal["terminal"] != "completed_capacity_pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()


__all__ = [
    "BootstrapHandshake",
    "CONFIG_RELATIVE_PATH",
    "LITERAL_WORKER_MODULE",
    "LoadedConfig",
    "OwnerExecution",
    "PREREGISTERED_CONFIG_SHA256",
    "RESULT_RELATIVE_PATH",
    "RetainedV1Evidence",
    "V1_RESULT_RELATIVE_PATH",
    "WORK_PREFLIGHT_V2_CAMPAIGN_SHA256",
    "WORK_PREFLIGHT_V2_PROTOCOL_SHA256",
    "canonical_lf_sha256",
    "dependency_hashes",
    "execute_owner_to_path",
    "load_public_config",
    "parse_config",
    "rebind_retained_v1",
    "run_no_cuda_bootstrap_handshake",
]
