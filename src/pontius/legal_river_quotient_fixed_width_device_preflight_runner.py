"""Exclusive durable owner for the ADR-0439/0440 device preflight."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from threading import Event, Thread, Timer
from time import perf_counter_ns

from .durable_evidence_journal import (
    DurableEvidenceJournalWriter,
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
)


_ROOT = Path(__file__).parents[2]
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_fixed_width_device_preflight_v1.jsonl"
)
RESULT_PATH = _ROOT / RESULT_RELATIVE_PATH
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
RESERVED_ACTUAL_RESULT_PATH = _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH
CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v1.json"
)
CORRECTION_CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-fixed-width-device-preflight-v2-topology.json"
)
CONFIG_SHA256 = "84da7e82ef07620b0d7869a1e52da6a80f5f3815c0e4dc7007068ce6664ed6af"
CORRECTION_CONFIG_SHA256 = (
    "6ebca361aed6c6cfcd11fd2df0b6041c1f676a7e6b07af9739bcd84e64b38e41"
)
PREREGISTRATION_COMMIT = "096d4ae0a78fa9de3c3c3838c8a64997b716816d"
CORRECTION_COMMIT = "e4704d9011ad4af2f7d610bfa56053d046864d96"

LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_fixed_width_device_preflight_runner"
)
SCIENTIFIC_MODULE = "pontius.legal_river_quotient_fixed_width_device_preflight"
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0439-0440-fixed-width-device-preflight-owner-v1"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0439-0440-fixed-width-device-preflight-campaign-v1"
).hexdigest()

PUBLIC_WALL_NS = 270_000_000_000
LABORATORY_WALL_NS = 240_000_000_000
OUTSIDE_LABORATORY_WALL_NS = 30_000_000_000
SOURCE_SEAL_PROBE_WALL_NS = 10_000_000_000
MAXIMUM_JOURNAL_BYTES = 67_108_864
MAXIMUM_CHILD_FRAME_BYTES = 1_048_576
MAXIMUM_SPOOL_EVENT_BYTES = 16_777_216
MAXIMUM_STDERR_BYTES = 16_384
MAXIMUM_EVENTS = 128

_MODE_ENV = "PONTIUS_ADR0439_DEVICE_PREFLIGHT_MODE"
_CHALLENGE_ENV = "PONTIUS_ADR0439_DEVICE_PREFLIGHT_CHALLENGE"
_SPOOL_ENV = "PONTIUS_ADR0439_DEVICE_PREFLIGHT_SPOOL"
_SOURCE_SEAL_PROBE = "source_seal_probe"
_CAMPAIGN_CHILD = "campaign_child"
_EVENT_PREFIX = b"PONTIUS_ADR0439_EVENT "
_ACK_PREFIX = b"PONTIUS_ADR0439_ACK "

CLAIMS = {
    "device_preflight_result": None,
    "candidate_selected": None,
    "population_25_numeric_value": None,
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

DEPENDENCY_RELATIVE_PATHS = (
    CONFIG_RELATIVE_PATH,
    CORRECTION_CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0439-preregister-the-fixed-width-compiled-device-preflight.md",
    "docs/decisions/ADR-0440-correct-the-batched-device-preflight-phase-topology-before-source-seal.md",
    "docs/decisions/ADR-0441-source-seal-the-corrected-fixed-width-compiled-device-preflight.md",
    "run_legal_river_quotient_fixed_width_device_preflight.py",
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


@dataclass(frozen=True, slots=True)
class OwnerExecution:
    terminal: Mapping[str, object]
    event_count: int


class PublicProcessTimeout(TimeoutError):
    """Typed parent watchdog terminal, distinct from the laboratory wall."""


def _canonical_lf(raw: bytes) -> bytes:
    if type(raw) is not bytes:
        raise TypeError("runner canonical input must be bytes")
    output = bytearray()
    index = 0
    while index < len(raw):
        if raw[index] == 13 and index + 1 < len(raw) and raw[index + 1] == 10:
            output.append(10)
            index += 2
        else:
            output.append(raw[index])
            index += 1
    return bytes(output)


def dependency_hashes() -> dict[str, str]:
    output = {}
    for relative in DEPENDENCY_RELATIVE_PATHS:
        path = _ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"device-preflight dependency is absent: {relative}")
        output[relative] = sha256(_canonical_lf(path.read_bytes())).hexdigest()
    return output


def _git(*arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=_ROOT,
        check=False,
        capture_output=True,
        timeout=30.0,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode(
            "utf-8", "replace"
        ).strip()
        raise RuntimeError(f"device-preflight Git metadata failed: {detail}")
    return completed.stdout


def strict_git_metadata(*, result_created: bool) -> dict[str, object]:
    commit = _git("rev-parse", "HEAD").decode("ascii").strip()
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise RuntimeError("device-preflight Git commit identity differs")
    for relative in DEPENDENCY_RELATIVE_PATHS:
        tracked = _git("ls-files", "--error-unmatch", "--", relative)
        if tracked.decode("utf-8").strip().replace("\\", "/") != relative:
            raise RuntimeError(f"device-preflight dependency is not tracked: {relative}")
    status = _git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = [entry.replace(b"\\", b"/") for entry in status.split(b"\0") if entry]
    expected = [f"?? {RESULT_RELATIVE_PATH}".encode("utf-8")] if result_created else []
    if entries != expected:
        raise RuntimeError("device-preflight owner requires its exact clean source seal")
    if (
        RESULT_PATH.exists() is not result_created
        or RESERVED_ACTUAL_RESULT_PATH.exists()
    ):
        raise RuntimeError("device-preflight protected result lifecycle differs")
    return {"commit": commit, "dirty": False, "strict_status": True}


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _header_payload(git: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": "legal-river-fixed-width-device-owner-header-v1",
        "protocol_sha256": PROTOCOL_SHA256,
        "campaign_sha256": CAMPAIGN_SHA256,
        "config_sha256": CONFIG_SHA256,
        "correction_config_sha256": CORRECTION_CONFIG_SHA256,
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "correction_commit": CORRECTION_COMMIT,
        "source_seal_git": dict(git),
        "dependency_hashes": dependency_hashes(),
        "result_relative_path": RESULT_RELATIVE_PATH,
        "reserved_actual_result_relative_path": RESERVED_ACTUAL_RESULT_RELATIVE_PATH,
        "literal_worker_module": LITERAL_WORKER_MODULE,
        "scientific_module": SCIENTIFIC_MODULE,
        "claims": dict(CLAIMS),
    }


def _terminal_payload(
    *, terminal: str, reason: str, event_count: int, public_elapsed_ns: int,
    laboratory_elapsed_ns: int | None,
) -> dict[str, object]:
    if not isinstance(terminal, str) or not terminal:
        raise ValueError("device-preflight terminal must be named")
    outside = (
        None
        if laboratory_elapsed_ns is None
        else public_elapsed_ns - laboratory_elapsed_ns
    )
    passed = terminal == "completed_device_preflight"
    claims = dict(CLAIMS)
    claims["device_preflight_result"] = (
        True if terminal in {"completed_device_preflight", "completed_no_device_candidate"} else None
    )
    return {
        "schema_version": "legal-river-fixed-width-device-owner-terminal-v1",
        "terminal": terminal,
        "passed": passed,
        "reason": reason[:4096],
        "event_count": event_count,
        "public_elapsed_ns": public_elapsed_ns,
        "public_wall_ns": PUBLIC_WALL_NS,
        "laboratory_elapsed_ns": laboratory_elapsed_ns,
        "laboratory_wall_ns": LABORATORY_WALL_NS,
        "outside_laboratory_elapsed_ns": outside,
        "outside_laboratory_wall_ns": OUTSIDE_LABORATORY_WALL_NS,
        "claims": claims,
    }


def _bounded_append(
    writer: DurableEvidenceJournalWriter,
    *, kind: JournalRecordKind, payload: Mapping[str, object],
    previous_line_sha256: str | None,
) -> str:
    semantic = _semantic_digest(payload)
    body = build_journal_record_body(
        protocol_sha256=PROTOCOL_SHA256,
        campaign_sha256=CAMPAIGN_SHA256,
        kind=kind,
        sequence=writer.next_sequence,
        previous_record_sha256=previous_line_sha256,
        semantic_identity_sha256=semantic,
        payload=payload,
    )
    prospective = JournalRecordEnvelope(body=body)
    reserve_bytes = 0
    if kind is not JournalRecordKind.TERMINAL:
        reserve_payload = _terminal_payload(
            terminal="infrastructure_failure",
            reason="x" * 4096,
            event_count=MAXIMUM_EVENTS,
            public_elapsed_ns=PUBLIC_WALL_NS + 1,
            laboratory_elapsed_ns=LABORATORY_WALL_NS,
        )
        reserve_body = build_journal_record_body(
            protocol_sha256=PROTOCOL_SHA256,
            campaign_sha256=CAMPAIGN_SHA256,
            kind=JournalRecordKind.TERMINAL,
            sequence=writer.next_sequence + 1,
            previous_record_sha256=prospective.line_sha256,
            semantic_identity_sha256=_semantic_digest(reserve_payload),
            payload=reserve_payload,
        )
        reserve_bytes = len(JournalRecordEnvelope(body=reserve_body).line_bytes)
    current = writer.path.stat().st_size
    if current + len(prospective.line_bytes) + reserve_bytes > MAXIMUM_JOURNAL_BYTES:
        raise RuntimeError("device-preflight journal capacity would be exceeded")
    receipt = writer.append(kind=kind, semantic_identity_sha256=semantic, payload=payload)
    if receipt.line_sha256 != prospective.line_sha256:
        raise RuntimeError("device-preflight prospective journal identity differs")
    return receipt.line_sha256


def _result_snapshot(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"present": False, "byte_count": None, "sha256": None}
    if not path.is_file():
        raise ValueError("device-preflight protected result is not a file")
    raw = path.read_bytes()
    return {
        "present": True,
        "byte_count": len(raw),
        "sha256": sha256(raw).hexdigest(),
    }


def source_seal_probe(
    challenge_hex: str, *, result_path: Path = RESULT_PATH
) -> dict[str, object]:
    try:
        challenge = bytes.fromhex(challenge_hex)
    except ValueError as error:
        raise ValueError("device-preflight source-seal challenge differs") from error
    if len(challenge) != 32:
        raise ValueError("device-preflight source-seal challenge length differs")
    scientific_loaded = SCIENTIFIC_MODULE in sys.modules
    cupy_loaded = any(name == "cupy" or name.startswith("cupy.") for name in sys.modules)
    result_before = _result_snapshot(result_path)
    result_after = _result_snapshot(result_path)
    return {
        "schema_version": "legal-river-fixed-width-device-source-seal-probe-v1",
        "challenge_sha256": sha256(challenge).hexdigest(),
        "literal_worker_module": LITERAL_WORKER_MODULE,
        "argv_count": len(sys.argv),
        "python_no_bytecode": bool(sys.dont_write_bytecode),
        "runtime_name": __name__,
        "package_name": __package__,
        "cupy_loaded": cupy_loaded,
        "scientific_source_loaded": scientific_loaded,
        "result_absent": not result_before["present"],
        "result_before": result_before,
        "result_after": result_after,
        "result_unchanged": result_before == result_after,
        "compiler_executed": False,
        "device_queried": False,
    }


def _child_emit_factory(spool: Path) -> Callable[[str, Mapping[str, object]], None]:
    counter = 0

    def emit(kind: str, payload: Mapping[str, object]) -> None:
        nonlocal counter
        if not isinstance(kind, str) or not kind or not isinstance(payload, Mapping):
            raise TypeError("device-preflight child event differs")
        raw = canonical_journal_json_bytes(dict(payload))
        if len(raw) > MAXIMUM_SPOOL_EVENT_BYTES:
            raise RuntimeError("device-preflight child event exceeds spool ceiling")
        path = spool / f"event-{counter:04d}.json"
        counter += 1
        with path.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        descriptor = canonical_journal_json_bytes(
            {
                "kind": kind,
                "name": path.name,
                "byte_count": len(raw),
                "sha256": sha256(raw).hexdigest(),
            }
        )
        frame = _EVENT_PREFIX + descriptor + b"\n"
        if len(frame) > MAXIMUM_CHILD_FRAME_BYTES:
            raise RuntimeError("device-preflight child descriptor exceeds frame ceiling")
        sys.stdout.buffer.write(frame)
        sys.stdout.buffer.flush()
        acknowledgment = sys.stdin.buffer.readline(MAXIMUM_CHILD_FRAME_BYTES + 1)
        expected = _ACK_PREFIX + sha256(raw).hexdigest().encode("ascii") + b"\n"
        if acknowledgment != expected:
            raise RuntimeError("device-preflight child evidence ACK differs")

    return emit


def _campaign_child_main() -> int:
    spool_raw = os.environ.get(_SPOOL_ENV)
    if not isinstance(spool_raw, str):
        raise ValueError("device-preflight child spool is absent")
    spool = Path(spool_raw).resolve()
    if not spool.is_dir() or not RESULT_PATH.is_file():
        raise RuntimeError("device-preflight child lifecycle differs")
    emit = _child_emit_factory(spool)
    laboratory_start = perf_counter_ns()
    emit(
        "bootstrap_handshake",
        {
            "schema_version": "legal-river-fixed-width-device-bootstrap-v1",
            "literal_worker_module": LITERAL_WORKER_MODULE,
            "argv_count": len(sys.argv),
            "python_no_bytecode": bool(sys.dont_write_bytecode),
            "cupy_loaded": any(
                name == "cupy" or name.startswith("cupy.") for name in sys.modules
            ),
            "scientific_source_loaded": SCIENTIFIC_MODULE in sys.modules,
            "parent_journal_present": RESULT_PATH.is_file(),
        },
    )
    bootstrap_end = perf_counter_ns()
    from . import legal_river_quotient_fixed_width_device_preflight as scientific

    try:
        evidence = scientific.execute_device_preflight(
            emit,
            laboratory_started_ns=laboratory_start,
            bootstrap_ended_ns=bootstrap_end,
        )
    except scientific.DevicePreflightFailure as error:
        evidence = {
            "schema_version": "legal-river-quotient-fixed-width-device-preflight-v1",
            "terminal": error.terminal,
            "passed": False,
            "reason": error.reason,
            "candidate_selected": None,
            "claims": dict(CLAIMS),
        }
    emit("terminal_evidence", evidence)
    return 0


def _read_stderr(stream: object, target: bytearray, overflow: Event) -> None:
    while True:
        block = stream.read(4096)
        if not block:
            return
        remaining = MAXIMUM_STDERR_BYTES + 1 - len(target)
        if remaining > 0:
            target.extend(block[:remaining])
        if len(target) > MAXIMUM_STDERR_BYTES:
            overflow.set()


def _child_environment(spool: Path) -> dict[str, str]:
    environment = dict(os.environ)
    for name in (
        "NVCC_PREPEND_FLAGS",
        "NVCC_APPEND_FLAGS",
        "CUDAFE_FLAGS",
        "PTXAS_OPTIONS",
        "PYTHONSTARTUP",
        "PYTHONINSPECT",
    ):
        environment.pop(name, None)
    environment["PYTHONPATH"] = str(_ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONNOUSERSITE"] = "1"
    environment[_MODE_ENV] = _CAMPAIGN_CHILD
    environment[_SPOOL_ENV] = str(spool)
    environment.pop(_CHALLENGE_ENV, None)
    return environment


def _run_campaign_child(
    append_event: Callable[[str, Mapping[str, object]], None]
) -> Mapping[str, object]:
    with tempfile.TemporaryDirectory(prefix="pontius-adr0439-spool-") as directory:
        spool = Path(directory).resolve()
        process = subprocess.Popen(
            [sys.executable, "-B", "-m", LITERAL_WORKER_MODULE],
            cwd=_ROOT,
            env=_child_environment(spool),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdin is not None and process.stdout is not None
        assert process.stderr is not None
        stderr = bytearray()
        stderr_overflow = Event()
        stderr_thread = Thread(
            target=_read_stderr,
            args=(process.stderr, stderr, stderr_overflow),
            daemon=True,
        )
        stderr_thread.start()
        timed_out = Event()

        def terminate() -> None:
            timed_out.set()
            if process.poll() is None:
                process.kill()

        # The scientific child records and checks its 240-second laboratory
        # internally.  Parent/child transport after that boundary belongs to
        # the separate 30-second public envelope, so the watchdog must not
        # collapse those two semantic walls into one.
        timer = Timer(PUBLIC_WALL_NS / 1_000_000_000, terminate)
        timer.daemon = True
        timer.start()
        terminal: Mapping[str, object] | None = None
        event_count = 0
        post_terminal = False
        try:
            while True:
                line = process.stdout.readline(MAXIMUM_CHILD_FRAME_BYTES + 1)
                if not line:
                    break
                if len(line) > MAXIMUM_CHILD_FRAME_BYTES or not line.endswith(b"\n"):
                    raise RuntimeError("device-preflight child frame exceeds its bound")
                if not line.startswith(_EVENT_PREFIX):
                    raise RuntimeError("device-preflight child stdout is not an event")
                if post_terminal:
                    raise RuntimeError("device-preflight child emitted after terminal evidence")
                descriptor_raw = line[len(_EVENT_PREFIX) : -1]
                descriptor = json.loads(descriptor_raw)
                if (
                    not isinstance(descriptor, dict)
                    or set(descriptor) != {"kind", "name", "byte_count", "sha256"}
                    or not isinstance(descriptor["kind"], str)
                    or not isinstance(descriptor["name"], str)
                    or isinstance(descriptor["byte_count"], bool)
                    or not isinstance(descriptor["byte_count"], int)
                    or descriptor["byte_count"] < 0
                    or descriptor["byte_count"] > MAXIMUM_SPOOL_EVENT_BYTES
                    or not isinstance(descriptor["sha256"], str)
                ):
                    raise ValueError("device-preflight child descriptor differs")
                path = (spool / descriptor["name"]).resolve()
                if path.parent != spool or path.name != descriptor["name"] or not path.is_file():
                    raise ValueError("device-preflight child spool path escapes")
                raw = path.read_bytes()
                if (
                    len(raw) != descriptor["byte_count"]
                    or sha256(raw).hexdigest() != descriptor["sha256"]
                    or canonical_journal_json_bytes(json.loads(raw)) != raw
                ):
                    raise ValueError("device-preflight child spool identity differs")
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise TypeError("device-preflight child payload must be an object")
                append_event(descriptor["kind"], payload)
                path.unlink()
                process.stdin.write(
                    _ACK_PREFIX + descriptor["sha256"].encode("ascii") + b"\n"
                )
                process.stdin.flush()
                event_count += 1
                if event_count > MAXIMUM_EVENTS:
                    raise RuntimeError("device-preflight child event count exceeds ceiling")
                if descriptor["kind"] == "terminal_evidence":
                    terminal = payload
                    post_terminal = True
            return_code = process.wait(timeout=5.0)
        finally:
            timer.cancel()
            if process.poll() is None:
                process.kill()
            stderr_thread.join(timeout=5.0)
        if timed_out.is_set():
            raise PublicProcessTimeout(
                "device-preflight public child watchdog crossed"
            )
        if stderr_overflow.is_set():
            raise RuntimeError("device-preflight child stderr exceeds ceiling")
        if return_code != 0:
            raise RuntimeError(
                f"device-preflight child exited {return_code}: "
                + bytes(stderr).decode("utf-8", "replace")
            )
        if terminal is None:
            raise RuntimeError("device-preflight child omitted terminal evidence")
        return terminal


def execute_owner_to_path(
    *,
    output_path: Path,
    campaign_executor: Callable[
        [Callable[[str, Mapping[str, object]], None]], Mapping[str, object]
    ] = _run_campaign_child,
    monotonic_ns: Callable[[], int] = perf_counter_ns,
) -> OwnerExecution:
    if not isinstance(output_path, Path):
        raise TypeError("device-preflight output must be a Path")
    if output_path.exists():
        raise FileExistsError("device-preflight authority is already consumed")
    git = strict_git_metadata(result_created=False) if output_path == RESULT_PATH else {
        "commit": "0" * 40,
        "dirty": False,
        "strict_status": True,
    }
    header = _header_payload(git)
    started = monotonic_ns()
    event_count = 0
    previous: str | None = None
    laboratory_elapsed: int | None = None
    terminal_payload: dict[str, object]
    with DurableEvidenceJournalWriter.create(
        path=output_path,
        protocol_sha256=PROTOCOL_SHA256,
        campaign_sha256=CAMPAIGN_SHA256,
    ) as writer:
        try:
            previous = _bounded_append(
                writer,
                kind=JournalRecordKind.HEADER,
                payload=header,
                previous_line_sha256=previous,
            )
            if output_path == RESULT_PATH:
                strict_git_metadata(result_created=True)

            def append_event(kind: str, event: Mapping[str, object]) -> None:
                nonlocal event_count, previous, laboratory_elapsed
                if event_count >= MAXIMUM_EVENTS:
                    raise RuntimeError("device-preflight event count exceeds ceiling")
                observation = {
                    "schema_version": "legal-river-fixed-width-device-owner-observation-v1",
                    "event_index": event_count,
                    "kind": kind,
                    "event": dict(event),
                    "source_commit": git["commit"],
                }
                previous = _bounded_append(
                    writer,
                    kind=JournalRecordKind.OBSERVATION,
                    payload=observation,
                    previous_line_sha256=previous,
                )
                event_count += 1
                if kind == "laboratory_partition":
                    value = event.get("total_ns")
                    if isinstance(value, bool) or not isinstance(value, int):
                        raise ValueError("device-preflight laboratory elapsed differs")
                    laboratory_elapsed = value

            evidence = campaign_executor(append_event)
            terminal = evidence.get("terminal")
            passed = evidence.get("passed")
            if not isinstance(terminal, str) or not isinstance(passed, bool):
                raise ValueError("device-preflight terminal evidence differs")
            if passed is not (terminal == "completed_device_preflight"):
                raise ValueError("device-preflight terminal pass bit disagrees")
            public_elapsed = monotonic_ns() - started
            if terminal in {
                "completed_device_preflight",
                "completed_no_device_candidate",
            }:
                if public_elapsed > PUBLIC_WALL_NS:
                    terminal = "public_wall_rejection"
                elif laboratory_elapsed is None:
                    terminal = "laboratory_partition_rejection"
                elif public_elapsed - laboratory_elapsed > OUTSIDE_LABORATORY_WALL_NS:
                    terminal = "outside_laboratory_wall_rejection"
            terminal_payload = _terminal_payload(
                terminal=terminal,
                reason="retained first terminal from the frozen one-shot owner",
                event_count=event_count,
                public_elapsed_ns=public_elapsed,
                laboratory_elapsed_ns=laboratory_elapsed,
            )
        except PublicProcessTimeout as error:
            terminal_payload = _terminal_payload(
                terminal="public_wall_rejection",
                reason=str(error),
                event_count=event_count,
                public_elapsed_ns=monotonic_ns() - started,
                laboratory_elapsed_ns=laboratory_elapsed,
            )
        except TimeoutError as error:
            terminal_payload = _terminal_payload(
                terminal="laboratory_wall_rejection",
                reason=str(error),
                event_count=event_count,
                public_elapsed_ns=monotonic_ns() - started,
                laboratory_elapsed_ns=laboratory_elapsed,
            )
        except BaseException as error:  # noqa: BLE001 - terminal must be durable
            terminal_payload = _terminal_payload(
                terminal="infrastructure_failure",
                reason=f"{type(error).__name__}: {error}",
                event_count=event_count,
                public_elapsed_ns=monotonic_ns() - started,
                laboratory_elapsed_ns=laboratory_elapsed,
            )
        _bounded_append(
            writer,
            kind=JournalRecordKind.TERMINAL,
            payload=terminal_payload,
            previous_line_sha256=previous,
        )
    if output_path.stat().st_size > MAXIMUM_JOURNAL_BYTES:
        raise RuntimeError("device-preflight journal exceeds byte ceiling")
    return OwnerExecution(terminal=terminal_payload, event_count=event_count)


def main() -> int:
    if len(sys.argv) != 1 or not sys.dont_write_bytecode:
        raise RuntimeError("device-preflight owner requires no arguments and Python -B")
    mode = os.environ.get(_MODE_ENV)
    if mode == _SOURCE_SEAL_PROBE:
        challenge = os.environ.get(_CHALLENGE_ENV)
        if not isinstance(challenge, str) or _SPOOL_ENV in os.environ:
            raise ValueError("device-preflight source-seal probe environment differs")
        print(canonical_journal_json_bytes(source_seal_probe(challenge)).decode("ascii"))
        return 0
    if mode == _CAMPAIGN_CHILD:
        if _CHALLENGE_ENV in os.environ:
            raise ValueError("device-preflight campaign challenge is present")
        return _campaign_child_main()
    if mode is not None or _CHALLENGE_ENV in os.environ or _SPOOL_ENV in os.environ:
        raise ValueError("device-preflight owner environment is contaminated")
    if RESULT_PATH.exists():
        raise FileExistsError("device-preflight authority is already consumed")
    execution = execute_owner_to_path(output_path=RESULT_PATH)
    print(
        "legal-river fixed-width device preflight: "
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
    "CLAIMS",
    "CONFIG_SHA256",
    "CORRECTION_CONFIG_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "LITERAL_WORKER_MODULE",
    "MAXIMUM_JOURNAL_BYTES",
    "OwnerExecution",
    "PROTOCOL_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "dependency_hashes",
    "execute_owner_to_path",
    "main",
    "source_seal_probe",
    "strict_git_metadata",
]
