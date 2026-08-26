"""Exclusive one-shot owner for the ADR-0419 device differential."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from queue import Empty, Queue
import secrets
import subprocess
import sys
from threading import Thread
from time import perf_counter_ns
from typing import Callable, Mapping

from .durable_evidence_journal import (
    DurableEvidenceJournalWriter,
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
)


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-cuda-shared-direct-device-v1.json"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_shared_direct_device_v1.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
_OUTPUT = _ROOT / RESULT_RELATIVE_PATH
_RESERVED = _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH
CONFIG_SHA256 = (
    "1dcc3f1ae2d528ab0625c3024f5dc04238ee49df9b6fbdc750b0e6e9352854d3"
)
PREREGISTRATION_COMMIT = "a457f8f73d2f69a66ac3d52361d1e96ddf0f02ac"
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0419-shared-direct-device-exclusive-journal-v1"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0419-shared-direct-device-one-shot-campaign-v1"
).hexdigest()
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_cuda_shared_direct_device_runner"
)
_MODE_ENV = "PONTIUS_ADR0419_SHARED_DIRECT_CHILD_MODE"
_CHALLENGE_ENV = "PONTIUS_ADR0419_SHARED_DIRECT_CHALLENGE"
_HANDSHAKE_MODE = "handshake"
_CAMPAIGN_MODE = "campaign"
_EVENT_PREFIX = b"PONTIUS_ADR0419_EVENT "
_ACK = b"ADR0419_ACK\n"

HANDSHAKE_WALL_NS = 10_000_000_000
PARENT_HARD_WALL_NS = 270_000_000_000
MAXIMUM_ARTIFACT_BYTES = 67_108_864
MAXIMUM_EVENT_COUNT = 4096
MAXIMUM_CHILD_LINE_BYTES = 1_048_576
MAXIMUM_STDERR_BYTES = 4096

CLAIMS = {
    "device_differential_result": None,
    "complete_10_result": None,
    "complete_22_result": None,
    "capacity_projection": None,
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
class ChildOutcome:
    return_code: int
    event_count: int
    stderr: bytes


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"shared-direct runner path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _checked_git(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        timeout=30.0,
    ).stdout


_TRACKED_REQUIRED = (
    CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0419-preregister-the-shared-direct-device-differential.md",
    "src/pontius/legal_river_quotient_cuda_shared_direct_oracle.py",
    "src/pontius/legal_river_quotient_cuda_shared_direct_device.py",
    "src/pontius/legal_river_quotient_cuda_shared_direct_device_runner.py",
    "src/pontius/legal_river_quotient_cuda_shared_direct_device_result.py",
    "tests/test_legal_river_quotient_cuda_shared_direct_device.py",
)


def strict_git_metadata(*, result_created: bool) -> dict[str, object]:
    commit = _checked_git("rev-parse", "HEAD").decode("ascii").strip()
    if len(commit) != 40:
        raise RuntimeError("shared-direct Git commit identity differs")
    for relative in _TRACKED_REQUIRED:
        _checked_git("ls-files", "--error-unmatch", "--", relative)
    status = _checked_git(
        "status", "--porcelain=v1", "--untracked-files=all"
    ).decode("utf-8")
    expected = f"?? {RESULT_RELATIVE_PATH}\n" if result_created else ""
    if status != expected:
        raise RuntimeError("shared-direct strict Git status differs")
    return {"commit": commit, "dirty": False, "strict_status": True}


def dependency_hashes() -> dict[str, str]:
    paths = (
        CONFIG_RELATIVE_PATH,
        "docs/decisions/ADR-0419-preregister-the-shared-direct-device-differential.md",
        "docs/decisions/ADR-0418-source-seal-the-shared-selected-direct-oracle.md",
        "src/pontius/legal_river_quotient_cuda_shared_direct_oracle.py",
        "tests/test_legal_river_quotient_cuda_shared_direct_oracle.py",
        "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py",
        "src/pontius/legal_river_quotient_cuda_compensated_tiles.py",
        "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v1.json",
        "experiments/configs/legal-river-quotient-cuda-compensated-tiles-v2.json",
        (
            "artifacts/work_preflight/"
            "legal_river_quotient_cuda_compensated_work_preflight_v4.jsonl"
        ),
        (
            "artifacts/work_preflight/"
            "legal_river_exact_cubin_zero_suffix_diagnostic_v1.jsonl"
        ),
        "src/pontius/legal_river_quotient_cuda_shared_direct_device.py",
        "src/pontius/legal_river_quotient_cuda_shared_direct_device_runner.py",
        "src/pontius/legal_river_quotient_cuda_shared_direct_device_result.py",
        "tests/test_legal_river_quotient_cuda_shared_direct_device.py",
        "src/pontius/durable_evidence_journal.py",
    )
    return {
        relative: sha256(
            (_ROOT / relative).read_bytes()
            if relative.startswith("artifacts/")
            else (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        for relative in paths
    }


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _header_payload(git: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": "legal-river-shared-direct-owner-header-v1",
        "config_sha256": CONFIG_SHA256,
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "source_seal_git": dict(git),
        "dependency_hashes": dependency_hashes(),
        "result_relative_path": RESULT_RELATIVE_PATH,
        "reserved_actual_result_relative_path": (
            RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        ),
        "claims": dict(CLAIMS),
    }


def _observation_payload(kind: str, event: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(kind, str) or not kind or not isinstance(event, Mapping):
        raise TypeError("shared-direct child event differs")
    return {
        "schema_version": "legal-river-shared-direct-owner-observation-v1",
        "kind": kind,
        "event": dict(event),
        "config_sha256": CONFIG_SHA256,
    }


def _terminal_payload(
    *,
    terminal: str,
    reason: str,
    event_count: int,
    handshake_passed: bool,
) -> dict[str, object]:
    passed = terminal == "completed_validation_pass"
    claims = dict(CLAIMS)
    claims.update(
        {
            "device_differential_result": passed,
            "complete_10_result": passed,
            "complete_22_result": passed,
        }
    )
    return {
        "schema_version": "legal-river-shared-direct-owner-terminal-v1",
        "terminal": terminal,
        "passed": passed,
        "reason": reason[:4096],
        "event_count": event_count,
        "handshake_passed": handshake_passed,
        "capacity_projection": None,
        "complete_25_numerical_value": None,
        "claims": claims,
    }


def _child_emit(kind: str, payload: Mapping[str, object]) -> None:
    event = {"kind": kind, "payload": dict(payload)}
    line = _EVENT_PREFIX + canonical_journal_json_bytes(event) + b"\n"
    if len(line) > MAXIMUM_CHILD_LINE_BYTES:
        raise ValueError("shared-direct child event exceeds line cap")
    sys.stdout.buffer.write(line)
    sys.stdout.buffer.flush()
    if sys.stdin.buffer.readline() != _ACK:
        raise RuntimeError("shared-direct child ACK differs")


def _handshake_child(challenge: str) -> int:
    if (
        len(challenge) != 64
        or any(character not in "0123456789abcdef" for character in challenge)
    ):
        raise ValueError("shared-direct handshake challenge differs")
    _child_emit(
        "bootstrap_handshake",
        {
            "schema_version": "legal-river-shared-direct-handshake-v1",
            "challenge_sha256": sha256(bytes.fromhex(challenge)).hexdigest(),
            "literal_module": LITERAL_WORKER_MODULE,
            "spec_name": __spec__.name if __spec__ is not None else None,
            "runtime_name": __name__,
            "cupy_imported": "cupy" in sys.modules,
        },
    )
    return 0


def _campaign_child() -> int:
    from .legal_river_quotient_cuda_shared_direct_device import (
        run_shared_direct_device_validation,
    )

    terminal = run_shared_direct_device_validation(_child_emit)
    _child_emit("terminal_evidence", terminal)
    return 0


def _decode_child_event(line: bytes) -> tuple[str, Mapping[str, object]]:
    if (
        not line.startswith(_EVENT_PREFIX)
        or not line.endswith(b"\n")
        or len(line) > MAXIMUM_CHILD_LINE_BYTES
    ):
        raise ValueError("shared-direct child line framing differs")
    raw = line[len(_EVENT_PREFIX) : -1]
    value = json.loads(raw)
    if (
        not isinstance(value, dict)
        or set(value) != {"kind", "payload"}
        or not isinstance(value["kind"], str)
        or not isinstance(value["payload"], dict)
        or canonical_journal_json_bytes(value) != raw
    ):
        raise ValueError("shared-direct child event semantics differ")
    return value["kind"], value["payload"]


def _run_child_process(
    mode: str,
    *,
    challenge: str | None,
    wall_ns: int,
    on_event: Callable[[str, Mapping[str, object]], None],
) -> ChildOutcome:
    if mode not in {_HANDSHAKE_MODE, _CAMPAIGN_MODE}:
        raise ValueError("shared-direct child mode differs")
    env = dict(os.environ)
    env[_MODE_ENV] = mode
    if challenge is not None:
        env[_CHALLENGE_ENV] = challenge
    process = subprocess.Popen(
        [sys.executable, "-B", "-m", LITERAL_WORKER_MODULE],
        cwd=_ROOT,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None
    queue: Queue[bytes | None] = Queue()
    stderr_parts: list[bytes] = []

    def stdout_reader() -> None:
        while True:
            line = process.stdout.readline(MAXIMUM_CHILD_LINE_BYTES + 1)
            if not line:
                queue.put(None)
                return
            queue.put(line)

    def stderr_reader() -> None:
        retained = 0
        while True:
            chunk = process.stderr.read(1024)
            if not chunk:
                return
            remaining = MAXIMUM_STDERR_BYTES + 1 - retained
            if remaining > 0:
                stderr_parts.append(chunk[:remaining])
                retained += min(len(chunk), remaining)

    out_thread = Thread(target=stdout_reader, daemon=True)
    err_thread = Thread(target=stderr_reader, daemon=True)
    out_thread.start()
    err_thread.start()
    started = perf_counter_ns()
    count = 0
    saw_eof = False
    try:
        while not saw_eof:
            remaining = wall_ns - (perf_counter_ns() - started)
            if remaining <= 0:
                raise TimeoutError("shared-direct child wall crossed")
            try:
                line = queue.get(timeout=min(0.5, remaining / 1_000_000_000))
            except Empty:
                if process.poll() is not None and not out_thread.is_alive():
                    continue
                continue
            if line is None:
                saw_eof = True
                continue
            if len(line) > MAXIMUM_CHILD_LINE_BYTES:
                raise ValueError("shared-direct child line exceeds cap")
            kind, payload = _decode_child_event(line)
            on_event(kind, payload)
            process.stdin.write(_ACK)
            process.stdin.flush()
            count += 1
            if count > MAXIMUM_EVENT_COUNT:
                raise ValueError("shared-direct child event count exceeds cap")
        remaining = max(
            0.001, (wall_ns - (perf_counter_ns() - started)) / 1_000_000_000
        )
        return_code = process.wait(timeout=remaining)
    except BaseException:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2.0)
        raise
    finally:
        process.stdin.close()
        out_thread.join(timeout=2.0)
        err_thread.join(timeout=2.0)
        process.stdout.close()
        process.stderr.close()
    stderr = b"".join(stderr_parts)
    if len(stderr) > MAXIMUM_STDERR_BYTES:
        raise ValueError("shared-direct child stderr exceeds cap")
    return ChildOutcome(return_code=return_code, event_count=count, stderr=stderr)


def run_no_cuda_bootstrap_handshake() -> Mapping[str, object]:
    challenge = secrets.token_bytes(32)
    challenge_hex = challenge.hex()
    events: list[tuple[str, Mapping[str, object]]] = []
    outcome = _run_child_process(
        _HANDSHAKE_MODE,
        challenge=challenge_hex,
        wall_ns=HANDSHAKE_WALL_NS,
        on_event=lambda kind, payload: events.append((kind, payload)),
    )
    if outcome.return_code != 0 or outcome.stderr or len(events) != 1:
        raise RuntimeError("shared-direct bootstrap child rejected")
    kind, event = events[0]
    if (
        kind != "bootstrap_handshake"
        or event.get("schema_version")
        != "legal-river-shared-direct-handshake-v1"
        or event.get("challenge_sha256") != sha256(challenge).hexdigest()
        or event.get("literal_module") != LITERAL_WORKER_MODULE
        or event.get("spec_name") != LITERAL_WORKER_MODULE
        or event.get("runtime_name") != "__main__"
        or event.get("cupy_imported") is not False
    ):
        raise ValueError("shared-direct bootstrap semantics differ")
    return event


class _BoundedWriter:
    def __init__(self, writer: DurableEvidenceJournalWriter) -> None:
        self.writer = writer
        self.sequence = 0
        self.previous: str | None = None
        self.total_bytes = 0

    def _line(
        self,
        kind: JournalRecordKind,
        payload: Mapping[str, object],
        *,
        previous: str | None = None,
        sequence: int | None = None,
    ) -> JournalRecordEnvelope:
        body = build_journal_record_body(
            protocol_sha256=PROTOCOL_SHA256,
            campaign_sha256=CAMPAIGN_SHA256,
            kind=kind,
            sequence=self.sequence if sequence is None else sequence,
            previous_record_sha256=(
                self.previous if previous is None else previous
            ),
            semantic_identity_sha256=_semantic_digest(payload),
            payload=payload,
        )
        return JournalRecordEnvelope(body=body)

    def append(
        self,
        kind: JournalRecordKind,
        payload: Mapping[str, object],
        *,
        reserve_terminal: bool,
    ) -> None:
        envelope = self._line(kind, payload)
        prospective = self.total_bytes + len(envelope.line_bytes)
        if reserve_terminal and kind is not JournalRecordKind.TERMINAL:
            reserve_payload = _terminal_payload(
                terminal="infrastructure_failure",
                reason="reserved worst-form terminal",
                event_count=MAXIMUM_EVENT_COUNT,
                handshake_passed=True,
            )
            reserve = self._line(
                JournalRecordKind.TERMINAL,
                reserve_payload,
                previous=envelope.line_sha256,
                sequence=self.sequence + 1,
            )
            prospective += len(reserve.line_bytes)
        if prospective > MAXIMUM_ARTIFACT_BYTES:
            raise RuntimeError("shared-direct journal cap would be crossed")
        receipt = self.writer.append(
            kind=kind,
            semantic_identity_sha256=_semantic_digest(payload),
            payload=payload,
        )
        self.sequence += 1
        self.previous = receipt.line_sha256
        self.total_bytes += receipt.line_byte_count


def execute_owner_to_path(path: Path = _OUTPUT) -> Mapping[str, object]:
    if not isinstance(path, Path) or path != _OUTPUT:
        raise ValueError("shared-direct owner output path differs")
    if _RESERVED.exists():
        raise FileExistsError("reserved actual authority must remain absent")
    if path.exists():
        raise FileExistsError("shared-direct result already exists")
    strict_git_metadata(result_created=False)
    handshake_passed = False
    terminal_name = "infrastructure_failure"
    terminal_reason = "owner did not reach campaign"
    event_count = 0
    terminal_evidence: Mapping[str, object] | None = None
    started = perf_counter_ns()
    with DurableEvidenceJournalWriter.create(
        path=path,
        protocol_sha256=PROTOCOL_SHA256,
        campaign_sha256=CAMPAIGN_SHA256,
    ) as raw_writer:
        bounded = _BoundedWriter(raw_writer)
        git = strict_git_metadata(result_created=True)
        bounded.append(
            JournalRecordKind.HEADER,
            _header_payload(git),
            reserve_terminal=True,
        )
        try:
            handshake = run_no_cuda_bootstrap_handshake()
            bounded.append(
                JournalRecordKind.OBSERVATION,
                _observation_payload("bootstrap_handshake", handshake),
                reserve_terminal=True,
            )
            handshake_passed = True

            def append_event(kind: str, event: Mapping[str, object]) -> None:
                nonlocal event_count, terminal_evidence
                bounded.append(
                    JournalRecordKind.OBSERVATION,
                    _observation_payload(kind, event),
                    reserve_terminal=True,
                )
                event_count += 1
                if kind == "terminal_evidence":
                    if terminal_evidence is not None:
                        raise ValueError(
                            "shared-direct terminal evidence repeated"
                        )
                    terminal_evidence = event

            remaining = PARENT_HARD_WALL_NS - (perf_counter_ns() - started)
            if remaining <= 0:
                raise TimeoutError("shared-direct owner wall crossed")
            outcome = _run_child_process(
                _CAMPAIGN_MODE,
                challenge=None,
                wall_ns=remaining,
                on_event=append_event,
            )
            if outcome.return_code != 0 or outcome.stderr:
                raise RuntimeError(
                    "shared-direct campaign child failed: "
                    + outcome.stderr.decode("utf-8", errors="replace")[:1024]
                )
            if terminal_evidence is None:
                raise RuntimeError(
                    "shared-direct campaign omitted terminal evidence"
                )
            terminal_name = str(terminal_evidence.get("terminal"))
            terminal_reason = str(terminal_evidence.get("reason", ""))
        except TimeoutError as error:
            terminal_name = "laboratory_wall_rejection"
            terminal_reason = str(error)
        except Exception as error:
            terminal_name = "infrastructure_failure"
            terminal_reason = (
                f"{type(error).__name__}: {str(error) or 'no message'}"
            )
        outer = _terminal_payload(
            terminal=terminal_name,
            reason=terminal_reason,
            event_count=event_count,
            handshake_passed=handshake_passed,
        )
        bounded.append(
            JournalRecordKind.TERMINAL,
            outer,
            reserve_terminal=False,
        )
    if path.stat().st_size > MAXIMUM_ARTIFACT_BYTES:
        raise RuntimeError("shared-direct retained journal exceeds cap")
    return outer


def main() -> None:
    mode = os.environ.get(_MODE_ENV)
    if mode is not None:
        if mode == _HANDSHAKE_MODE:
            challenge = os.environ.get(_CHALLENGE_ENV, "")
            raise SystemExit(_handshake_child(challenge))
        if mode == _CAMPAIGN_MODE:
            raise SystemExit(_campaign_child())
        raise SystemExit("unknown shared-direct child mode")
    if len(sys.argv) != 1:
        raise SystemExit("shared-direct owner accepts no arguments")
    terminal = execute_owner_to_path()
    print(json.dumps(terminal, sort_keys=True))


if __name__ == "__main__":
    main()


__all__ = [
    "CAMPAIGN_SHA256",
    "CLAIMS",
    "CONFIG_SHA256",
    "LITERAL_WORKER_MODULE",
    "PROTOCOL_SHA256",
    "RESULT_RELATIVE_PATH",
    "dependency_hashes",
    "execute_owner_to_path",
    "run_no_cuda_bootstrap_handshake",
    "strict_git_metadata",
]
