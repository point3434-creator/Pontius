"""Exclusive one-shot owner for the composite ADR-0394/ADR-0395 preflight.

The durable header is written before config/Git loading and before importing
the device source.  The real worker runs in a child process so the 240-second
laboratory wall can terminate a stalled CUDA invocation.  Tests inject only
synthetic event executors and never launch that worker.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from queue import Empty, Queue
import subprocess
import sys
from threading import Thread
from time import perf_counter_ns
from typing import Any, Callable, Iterable, Mapping

from .durable_evidence_journal import (
    DurableEvidenceJournalWriter,
    JournalRecordKind,
    canonical_journal_json_bytes,
)


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-v1.json"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v1.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
_CONFIG = _ROOT / CONFIG_RELATIVE_PATH
CORRECTION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-v2.json"
)
_CORRECTION_CONFIG = _ROOT / CORRECTION_CONFIG_RELATIVE_PATH
_OUTPUT = _ROOT / RESULT_RELATIVE_PATH
_RESERVED = _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH
PREREGISTERED_CONFIG_SHA256 = (
    "88a16d62cf978ec61b7481c79b841eda6a2844a41f374c122a21be5310550d3c"
)
CORRECTION_CONFIG_SHA256 = (
    "a522858696c8266485f7aac4b9c2dbb5f0d0c35e59d3e1515f4674d802ac890c"
)
PREREGISTRATION_COMMIT = "fc1892e15522eed4b9935de0404131646820c451"
WORK_PREFLIGHT_PROTOCOL_SHA256 = sha256(
    b"pontius-adr0394-work-preflight-exclusive-journal-v1"
).hexdigest()
WORK_PREFLIGHT_CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0394-work-preflight-one-shot-campaign-v1"
).hexdigest()
LABORATORY_WALL_LIMIT_NS = 240_000_000_000
MAXIMUM_EVENT_COUNT = 4096
MAXIMUM_ARTIFACT_BYTES = 16_777_216
_WORKER_ENV = "PONTIUS_ADR0394_WORK_PREFLIGHT_WORKER"
_EVENT_PREFIX = "PONTIUS_ADR0394_EVENT "

CLAIMS = {
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
    correction: Mapping[str, object]
    correction_sha256: str


@dataclass(frozen=True, slots=True)
class OwnerExecution:
    terminal: Mapping[str, object]
    event_count: int


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"work-preflight owner path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def parse_config(config: Mapping[str, Any]) -> dict[str, object]:
    if not isinstance(config, Mapping) or config.get("schema_version") != (
        "legal-river-quotient-cuda-compensated-work-preflight-config-v1"
    ):
        raise ValueError("work-preflight owner config schema differs")
    parsed = dict(config)
    projection = parsed.get("projection_contract")
    lifecycle = parsed.get("one_shot_lifecycle")
    scope = parsed.get("scope")
    if not all(isinstance(value, Mapping) for value in (projection, lifecycle, scope)):
        raise ValueError("work-preflight owner config sections are malformed")
    assert isinstance(projection, Mapping)
    assert isinstance(lifecycle, Mapping)
    assert isinstance(scope, Mapping)
    if projection.get("calibration_populations") != [10, 22]:
        raise ValueError("work-preflight calibration populations differ")
    if projection.get("target_population") != 25:
        raise ValueError("work-preflight projection population differs")
    if projection.get("target_population_is_never_compiled_or_executed") is not True:
        raise ValueError("work-preflight projection lock differs")
    if lifecycle.get("laboratory_total_wall_limit_ns") != LABORATORY_WALL_LIMIT_NS:
        raise ValueError("work-preflight laboratory wall differs")
    if lifecycle.get("future_result_open_mode") != "exclusive_xb":
        raise ValueError("work-preflight output mode differs")
    forbidden = (
        "population_25_fixture_compile_allocation_kernel_launch_"
        "scalar_digest_or_gate_forbidden"
    )
    if scope.get(forbidden) is not True:
        raise ValueError("work-preflight 25-card numerical lock differs")
    return parsed


def parse_resource_correction(config: Mapping[str, Any]) -> dict[str, object]:
    if not isinstance(config, Mapping) or config.get("schema_version") != (
        "legal-river-quotient-cuda-compensated-work-preflight-resource-correction-v2"
    ):
        raise ValueError("work-preflight correction schema differs")
    parsed = dict(config)
    parent = parsed.get("parent_identity")
    composite = parsed.get("composite_authority")
    resource = parsed.get("corrected_resource_contract")
    if not all(isinstance(value, Mapping) for value in (parent, composite, resource)):
        raise ValueError("work-preflight correction sections are malformed")
    assert isinstance(parent, Mapping)
    assert isinstance(composite, Mapping)
    assert isinstance(resource, Mapping)
    if (
        parent.get("v1_config_canonical_lf_sha256")
        != PREREGISTERED_CONFIG_SHA256
        or composite.get(
            "future_source_owner_and_reader_must_load_verify_and_report_both_config_hashes"
        )
        is not True
        or resource.get("retained_payload_must_begin_with_elf_magic_before_module_load")
        is not True
        or resource.get("cupy_free_reader_must_independently_parse_raw_resource_stdout")
        is not True
    ):
        raise ValueError("work-preflight correction contract differs")
    return parsed


def load_public_config(path: Path = _CONFIG) -> LoadedConfig:
    if not isinstance(path, Path):
        raise TypeError("work-preflight owner config path must be a Path")
    raw = path.read_bytes()
    digest = sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    if digest != PREREGISTERED_CONFIG_SHA256:
        raise ValueError("work-preflight owner config differs from ADR-0394")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("work-preflight owner config must be an object")
    correction_raw = _CORRECTION_CONFIG.read_bytes()
    correction_digest = sha256(
        correction_raw.replace(b"\r\n", b"\n")
    ).hexdigest()
    if correction_digest != CORRECTION_CONFIG_SHA256:
        raise ValueError("work-preflight owner correction differs from ADR-0395")
    correction = json.loads(correction_raw)
    if not isinstance(correction, dict):
        raise ValueError("work-preflight owner correction must be an object")
    return LoadedConfig(
        payload=parse_config(payload),
        sha256=digest,
        correction=parse_resource_correction(correction),
        correction_sha256=correction_digest,
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


def strict_git_metadata(output_path: Path = _OUTPUT) -> dict[str, object]:
    commit = _checked_git("rev-parse", "HEAD").decode("ascii").strip()
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise RuntimeError("work-preflight Git commit is malformed")
    raw = _checked_git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = [entry for entry in raw.split(b"\0") if entry]
    allowed = f"?? {output_path.relative_to(_ROOT).as_posix()}".encode("utf-8")
    if entries not in ([], [allowed]):
        raise RuntimeError("work-preflight Git boundary is dirty")
    return {
        "commit": commit,
        "dirty": False,
        "strict_status": True,
        "result_is_only_untracked_path": entries == [allowed] or not entries,
    }


_DEPENDENCY_PATHS = {
    "config": _CONFIG,
    "resource_correction_config": _CORRECTION_CONFIG,
    "resource_correction_adr": _ROOT
    / "docs/decisions/"
    "ADR-0395-correct-the-work-preflight-resource-instrument-before-result.md",
    "source": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
    "controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_work_preflight.py",
    "runner": Path(__file__),
    "reader": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_result.py",
    "parent_source": _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
    "parent_controls": _ROOT
    / "tests/test_legal_river_quotient_cuda_compensated_tiles.py",
    "artifact_marker": _ROOT / "artifacts/work_preflight/README.md",
    "artifact_attributes": _ROOT / "artifacts/work_preflight/.gitattributes",
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
        "schema_version": "legal-river-work-preflight-owner-header-v1",
        "owner_protocol_sha256": WORK_PREFLIGHT_PROTOCOL_SHA256,
        "config_relative_path": CONFIG_RELATIVE_PATH,
        "correction_config_relative_path": CORRECTION_CONFIG_RELATIVE_PATH,
        "correction_config_sha256": CORRECTION_CONFIG_SHA256,
        "result_relative_path": RESULT_RELATIVE_PATH,
        "reserved_actual_result_relative_path": RESERVED_ACTUAL_RESULT_RELATIVE_PATH,
        "preregistration_commit": PREREGISTRATION_COMMIT,
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
        raise ValueError("work-preflight terminal class is unknown")
    if not isinstance(reason, str) or not reason:
        raise ValueError("work-preflight terminal reason must be nonempty")
    return {
        "schema_version": "legal-river-work-preflight-owner-terminal-v1",
        "terminal": terminal,
        "reason": reason[:4096],
        "passed": terminal == "completed_capacity_pass",
        "event_count": event_count,
        "last_event_semantic_identity_sha256": last_event_semantic_identity_sha256,
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
    correction_config_sha256: str,
    source_commit: str,
) -> dict[str, object]:
    if not isinstance(event_kind, str) or not event_kind:
        raise ValueError("work-preflight event kind must be nonempty")
    return {
        "schema_version": "legal-river-work-preflight-owner-observation-v1",
        "event_index": event_index,
        "event_kind": event_kind,
        "config_sha256": config_sha256,
        "correction_config_sha256": correction_config_sha256,
        "source_commit": source_commit,
        "event": dict(event),
    }


CampaignExecutor = Callable[
    [Callable[[str, Mapping[str, object]], None]],
    Mapping[str, object],
]


def _worker_main() -> int:
    from .legal_river_quotient_cuda_compensated_work_preflight import (
        run_calibration_preflight,
    )

    def emit(kind: str, payload: Mapping[str, object]) -> None:
        line = json.dumps(
            {"kind": kind, "payload": dict(payload)},
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        print(_EVENT_PREFIX + line, flush=True)

    try:
        terminal = run_calibration_preflight(emit)
        emit("terminal_evidence", terminal)
        return 0
    except BaseException as error:  # noqa: BLE001 - first failure is evidence
        emit(
            "worker_failure",
            {
                "schema_version": "legal-river-work-preflight-worker-failure-v1",
                "reason": _failure_reason(error),
            },
        )
        return 1


def _subprocess_campaign_executor(
    emit: Callable[[str, Mapping[str, object]], None],
) -> Mapping[str, object]:
    environment = os.environ.copy()
    environment[_WORKER_ENV] = "1"
    process = subprocess.Popen(
        [sys.executable, "-B", "-m", __name__],
        cwd=_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="ascii",
        errors="strict",
        bufsize=1,
    )
    queue: Queue[str | None] = Queue()
    stderr_chunks: list[str] = []
    stderr_length = 0

    def read_stdout() -> None:
        assert process.stdout is not None
        for line in process.stdout:
            queue.put(line)
        queue.put(None)

    def read_stderr() -> None:
        nonlocal stderr_length
        assert process.stderr is not None
        while True:
            chunk = process.stderr.read(4096)
            if not chunk:
                return
            remaining = 4096 - stderr_length
            if remaining > 0:
                stderr_chunks.append(chunk[:remaining])
                stderr_length += min(len(chunk), remaining)

    thread = Thread(target=read_stdout, daemon=True)
    stderr_thread = Thread(target=read_stderr, daemon=True)
    thread.start()
    stderr_thread.start()
    started = perf_counter_ns()
    terminal: Mapping[str, object] | None = None
    seen_end = False
    try:
        while not seen_end:
            remaining_ns = LABORATORY_WALL_LIMIT_NS - (perf_counter_ns() - started)
            if remaining_ns <= 0:
                process.kill()
                process.wait(timeout=30.0)
                raise TimeoutError("laboratory_wall_crossed")
            try:
                line = queue.get(timeout=min(1.0, remaining_ns / 1_000_000_000))
            except Empty:
                if process.poll() is not None and not thread.is_alive():
                    break
                continue
            if line is None:
                seen_end = True
                continue
            if not line.startswith(_EVENT_PREFIX):
                raise RuntimeError("work-preflight worker emitted an unframed line")
            value = json.loads(line[len(_EVENT_PREFIX):])
            if not isinstance(value, dict) or set(value) != {"kind", "payload"}:
                raise RuntimeError("work-preflight worker event is malformed")
            kind = value["kind"]
            payload = value["payload"]
            if not isinstance(kind, str) or not isinstance(payload, dict):
                raise RuntimeError("work-preflight worker event types differ")
            if kind == "terminal_evidence":
                terminal = payload
            elif kind == "worker_failure":
                raise RuntimeError(str(payload.get("reason", "worker failed")))
            else:
                emit(kind, payload)
        return_code = process.wait(timeout=30.0)
        stderr_thread.join(timeout=5.0)
        if return_code != 0:
            stderr = "".join(stderr_chunks)
            raise RuntimeError(f"work-preflight worker exited {return_code}: {stderr}")
        if terminal is None:
            raise RuntimeError("work-preflight worker omitted terminal evidence")
        return terminal
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=30.0)


def execute_owner_to_path(
    *,
    output_path: Path,
    config_loader: Callable[[], LoadedConfig] = load_public_config,
    git_loader: Callable[[], Mapping[str, object]] = strict_git_metadata,
    hashes_loader: Callable[[], Mapping[str, str]] = dependency_hashes,
    campaign_executor: CampaignExecutor | None = None,
    monotonic_ns: Callable[[], int] = perf_counter_ns,
) -> OwnerExecution:
    """Consume one path; synthetic tests inject every post-header dependency."""

    if not isinstance(output_path, Path):
        raise TypeError("work-preflight owner output must be a Path")
    terminal_payload: dict[str, object]
    event_count = 0
    last_event_identity: str | None = None
    with DurableEvidenceJournalWriter.create(
        path=output_path,
        protocol_sha256=WORK_PREFLIGHT_PROTOCOL_SHA256,
        campaign_sha256=WORK_PREFLIGHT_CAMPAIGN_SHA256,
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
                raise TypeError("work-preflight config loader returned the wrong type")
            parse_config(loaded.payload)
            parse_resource_correction(loaded.correction)
            git = git_loader()
            if (
                git.get("dirty") is not False
                or git.get("strict_status") is not True
                or not isinstance(git.get("commit"), str)
            ):
                raise RuntimeError("work-preflight strict Git boundary rejected")
            provenance = {
                "schema_version": "legal-river-work-preflight-provenance-v1",
                "config_sha256": loaded.sha256,
                "correction_config_sha256": loaded.correction_sha256,
                "source_commit": str(git["commit"]),
                "source_dirty": False,
                "dependency_hashes": dict(hashes_loader()),
                "reserved_actual_result_absent": not _RESERVED.exists(),
            }

            def append_event(kind: str, event: Mapping[str, object]) -> None:
                nonlocal event_count, last_event_identity
                if event_count >= MAXIMUM_EVENT_COUNT:
                    raise RuntimeError("work-preflight event count exceeds its ceiling")
                observation = _event_observation(
                    event_index=event_count,
                    event_kind=kind,
                    event=event,
                    config_sha256=loaded.sha256,
                    correction_config_sha256=loaded.correction_sha256,
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
            executor = (
                _subprocess_campaign_executor
                if campaign_executor is None
                else campaign_executor
            )
            laboratory_started = monotonic_ns()
            terminal_evidence = executor(append_event)
            laboratory_stop = monotonic_ns()
            if laboratory_stop - laboratory_started > LABORATORY_WALL_LIMIT_NS:
                terminal_payload = _terminal_payload(
                    terminal="laboratory_wall_rejection",
                    reason="laboratory_wall_crossed",
                    event_count=event_count,
                    last_event_semantic_identity_sha256=last_event_identity,
                )
            else:
                if not isinstance(terminal_evidence, Mapping):
                    raise TypeError("work-preflight executor returned the wrong type")
                terminal = terminal_evidence.get("terminal")
                passed = terminal_evidence.get("passed")
                if not isinstance(terminal, str) or not isinstance(passed, bool):
                    raise ValueError("work-preflight terminal evidence is malformed")
                if passed is not (terminal == "completed_capacity_pass"):
                    raise ValueError("work-preflight terminal pass bit disagrees")
                append_event("terminal_evidence", terminal_evidence)
                terminal_payload = _terminal_payload(
                    terminal=terminal,
                    reason="retained first terminal evidence",
                    event_count=event_count,
                    last_event_semantic_identity_sha256=last_event_identity,
                )
        except TimeoutError as error:
            terminal_payload = _terminal_payload(
                terminal="laboratory_wall_rejection",
                reason=_failure_reason(error),
                event_count=event_count,
                last_event_semantic_identity_sha256=last_event_identity,
            )
        except BaseException as error:  # noqa: BLE001 - first failure is evidence
            terminal_payload = _terminal_payload(
                terminal="infrastructure_failure",
                reason=_failure_reason(error),
                event_count=event_count,
                last_event_semantic_identity_sha256=last_event_identity,
            )
        writer.append(
            kind=JournalRecordKind.TERMINAL,
            semantic_identity_sha256=_semantic_digest(terminal_payload),
            payload=terminal_payload,
        )
    if output_path.stat().st_size > MAXIMUM_ARTIFACT_BYTES:
        raise RuntimeError("work-preflight journal exceeds its byte ceiling")
    return OwnerExecution(terminal=terminal_payload, event_count=event_count)


def main() -> None:
    if len(sys.argv) != 1:
        raise ValueError("work-preflight owner accepts no arguments")
    if os.environ.get(_WORKER_ENV) == "1":
        raise SystemExit(_worker_main())
    if _OUTPUT.exists():
        raise FileExistsError("work-preflight authority is already consumed")
    if _RESERVED.exists():
        raise FileExistsError("reserved actual authority must remain absent")
    execution = execute_owner_to_path(output_path=_OUTPUT)
    print(
        "legal-river work preflight: "
        f"terminal={execution.terminal['terminal']} "
        f"passed={execution.terminal['passed']}"
    )
    if execution.terminal["terminal"] != "completed_capacity_pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
