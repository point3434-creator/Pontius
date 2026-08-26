"""Launcher-safe exclusive V2 owner for ADR-0422/0423."""

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
_SOURCE = (_ROOT / "src").resolve()
LAUNCHER_RELATIVE_PATH = (
    "run_legal_river_quotient_cuda_shared_direct_device_v2.py"
)
_LAUNCHER = (_ROOT / LAUNCHER_RELATIVE_PATH).resolve()
CONFIG_RELATIVE_PATH = (
    "experiments/configs/legal-river-quotient-cuda-shared-direct-device-v2.json"
)
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_shared_direct_device_v2.jsonl"
)
V1_RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_cuda_shared_direct_device_v1.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
_OUTPUT = _ROOT / RESULT_RELATIVE_PATH
_V1_OUTPUT = _ROOT / V1_RESULT_RELATIVE_PATH
_RESERVED = _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH
CONFIG_SHA256 = (
    "b8e0d9a5edafa16cdca26d3a5320826b43ccc973140706f8dc042b93b5a90bf9"
)
PREREGISTRATION_COMMIT = "22bcde5371d06a7886e0772c587e2215d8bba0e9"
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0422-shared-direct-device-launcher-safe-journal-v2"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0422-shared-direct-device-launcher-safe-campaign-v2"
).hexdigest()
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_cuda_shared_direct_device_v2_runner"
)
SCIENCE_ADAPTER_MODULE = (
    "pontius.legal_river_quotient_cuda_shared_direct_device"
)

_MODE_ENV = "PONTIUS_ADR0422_SHARED_DIRECT_CHILD_MODE"
_CHALLENGE_ENV = "PONTIUS_ADR0422_SHARED_DIRECT_CHALLENGE"
_PUBLIC_PROBE_ENV = "PONTIUS_ADR0422_PUBLIC_LAUNCHER_PROBE"
_HANDSHAKE_MODE = "handshake"
_PUBLIC_CHILD_MODE = "public_probe_child"
_CAMPAIGN_MODE = "campaign"
_EVENT_PREFIX = b"PONTIUS_ADR0422_EVENT "
_ACK = b"ADR0422_ACK\n"

HANDSHAKE_WALL_NS = 10_000_000_000
PUBLIC_PROBE_WALL_NS = 15_000_000_000
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
        raise ValueError(f"shared-direct V2 path is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_preregistered_config() -> Mapping[str, object]:
    path = _ROOT / CONFIG_RELATIVE_PATH
    if canonical_lf_sha256(path) != CONFIG_SHA256:
        raise ValueError("shared-direct V2 config hash differs")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("shared-direct V2 config root differs")
    return value


def verify_preregistered_contract() -> None:
    config = load_preregistered_config()
    retained = config.get("retained_parent_contract")
    fresh = config.get("fresh_identity")
    public = config.get("public_launcher_contract")
    science = config.get("unchanged_science_contract")
    if (
        config.get("schema_version")
        != "legal-river-quotient-cuda-shared-direct-launcher-recovery-v2"
        or not isinstance(retained, dict)
        or not isinstance(fresh, dict)
        or not isinstance(public, dict)
        or not isinstance(science, dict)
        or fresh.get("root_launcher_relative_path") != LAUNCHER_RELATIVE_PATH
        or fresh.get("runner_relative_path")
        != "src/pontius/legal_river_quotient_cuda_shared_direct_device_v2_runner.py"
        or fresh.get("reader_relative_path")
        != "src/pontius/legal_river_quotient_cuda_shared_direct_device_v2_result.py"
        or fresh.get("result_relative_path") != RESULT_RELATIVE_PATH
        or public.get("launcher_executes_exact_literal_runner_module")
        != LITERAL_WORKER_MODULE
        or science.get("complete_populations_in_order") != [10, 22]
        or science.get("forbidden_population") != 25
        or science.get("capacity_projection") is not None
        or science.get("complete_25_numerical_value") is not None
    ):
        raise ValueError("shared-direct V2 preregistered contract differs")
    bound_parents = (
        ("v1_config",),
        ("v1_source_seal_adr",),
        ("v1_failure_adr",),
        ("v1_adapter",),
        ("v1_runner",),
        ("v1_reader",),
        ("v1_controls",),
    )
    for (prefix,) in bound_parents:
        relative = retained.get(f"{prefix}_relative_path")
        expected = retained.get(f"{prefix}_canonical_lf_sha256")
        if (
            not isinstance(relative, str)
            or not isinstance(expected, str)
            or canonical_lf_sha256(_ROOT / relative) != expected
        ):
            raise ValueError(
                f"shared-direct V2 retained parent differs: {prefix}"
            )
    if (
        retained.get("v1_source_seal_commit")
        != "468fddf035add619a79c898dc4692dbe7b75b488"
        or retained.get("v1_failure_commit")
        != "08241bdd59a5e51358157edd7531ffa094b380fc"
        or retained.get("v1_result_absent_but_identity_consumed") is not True
        or retained.get(
            "v1_runner_and_public_command_may_not_be_imported_invoked_edited_or_replayed"
        )
        is not True
        or _V1_OUTPUT.exists()
        or _RESERVED.exists()
    ):
        raise ValueError("shared-direct V2 retained lifecycle differs")


def _checked_git(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        timeout=30.0,
    ).stdout


_V1_DEPENDENCIES = (
    "experiments/configs/legal-river-quotient-cuda-shared-direct-device-v1.json",
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
DEPENDENCY_RELATIVE_PATHS = tuple(
    dict.fromkeys(
        (
            CONFIG_RELATIVE_PATH,
            "docs/decisions/ADR-0424-correct-the-v1-parent-hash-bindings-before-v2-source-seal.md",
            "docs/decisions/ADR-0423-correct-the-v2-reader-lifecycle-transduction-before-source.md",
            "docs/decisions/ADR-0422-preregister-the-launcher-safe-shared-direct-v2-owner.md",
            "docs/decisions/ADR-0421-retain-the-shared-direct-public-launch-failure.md",
            "docs/decisions/ADR-0420-source-seal-the-shared-direct-device-differential.md",
            LAUNCHER_RELATIVE_PATH,
            "src/pontius/legal_river_quotient_cuda_shared_direct_device_v2_runner.py",
            "src/pontius/legal_river_quotient_cuda_shared_direct_device_v2_result.py",
            "tests/test_legal_river_quotient_cuda_shared_direct_device_v2.py",
            *_V1_DEPENDENCIES,
        )
    )
)


def dependency_hashes() -> dict[str, str]:
    return {
        relative: sha256(
            (_ROOT / relative).read_bytes()
            if relative.startswith("artifacts/")
            else (_ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        for relative in DEPENDENCY_RELATIVE_PATHS
    }


def strict_git_metadata(*, result_created: bool) -> dict[str, object]:
    commit = _checked_git("rev-parse", "HEAD").decode("ascii").strip()
    if len(commit) != 40:
        raise RuntimeError("shared-direct V2 Git commit identity differs")
    for relative in DEPENDENCY_RELATIVE_PATHS:
        _checked_git("ls-files", "--error-unmatch", "--", relative)
    status = _checked_git(
        "status", "--porcelain=v1", "--untracked-files=all"
    ).decode("utf-8")
    expected = f"?? {RESULT_RELATIVE_PATH}\n" if result_created else ""
    if status != expected:
        raise RuntimeError("shared-direct V2 strict Git status differs")
    if _V1_OUTPUT.exists() or _RESERVED.exists():
        raise RuntimeError("shared-direct V2 protected result exists")
    return {"commit": commit, "dirty": False, "strict_status": True}


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _header_payload(git: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": "legal-river-shared-direct-owner-header-v2",
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


def _observation_payload(
    kind: str, event: Mapping[str, object]
) -> dict[str, object]:
    if not isinstance(kind, str) or not kind or not isinstance(event, Mapping):
        raise TypeError("shared-direct V2 child event differs")
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
        raise ValueError("shared-direct V2 child event exceeds line cap")
    sys.stdout.buffer.write(line)
    sys.stdout.buffer.flush()
    if sys.stdin.buffer.readline() != _ACK:
        raise RuntimeError("shared-direct V2 child ACK differs")


def _validate_challenge(challenge: str) -> bytes:
    if (
        len(challenge) != 64
        or any(character not in "0123456789abcdef" for character in challenge)
    ):
        raise ValueError("shared-direct V2 handshake challenge differs")
    return bytes.fromhex(challenge)


def _handshake_child(challenge: str) -> int:
    raw = _validate_challenge(challenge)
    _child_emit(
        "bootstrap_handshake",
        {
            "schema_version": "legal-river-shared-direct-handshake-v1",
            "challenge_sha256": sha256(raw).hexdigest(),
            "literal_module": LITERAL_WORKER_MODULE,
            "spec_name": __spec__.name if __spec__ is not None else None,
            "runtime_name": __name__,
            "cupy_imported": "cupy" in sys.modules,
        },
    )
    return 0


def _public_probe_child(challenge: str) -> int:
    raw = _validate_challenge(challenge)
    _child_emit(
        "launcher_probe_child",
        {
            "schema_version": "legal-river-shared-direct-launcher-child-v2",
            "challenge_sha256": sha256(raw).hexdigest(),
            "literal_module": LITERAL_WORKER_MODULE,
            "spec_name": __spec__.name if __spec__ is not None else None,
            "runtime_name": __name__,
            "repository_root": str(_ROOT.resolve()),
            "source_root": str(_SOURCE),
            "launcher": str(_LAUNCHER),
            "interpreter": str(Path(sys.executable).resolve()),
            "cupy_imported": "cupy" in sys.modules,
            "science_adapter_imported": SCIENCE_ADAPTER_MODULE in sys.modules,
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
        raise ValueError("shared-direct V2 child line framing differs")
    raw = line[len(_EVENT_PREFIX) : -1]
    value = json.loads(raw)
    if (
        not isinstance(value, dict)
        or set(value) != {"kind", "payload"}
        or not isinstance(value["kind"], str)
        or not isinstance(value["payload"], dict)
        or canonical_journal_json_bytes(value) != raw
    ):
        raise ValueError("shared-direct V2 child event semantics differ")
    return value["kind"], value["payload"]


def _run_child_process(
    mode: str,
    *,
    challenge: str | None,
    wall_ns: int,
    on_event: Callable[[str, Mapping[str, object]], None],
) -> ChildOutcome:
    if mode not in {_HANDSHAKE_MODE, _PUBLIC_CHILD_MODE, _CAMPAIGN_MODE}:
        raise ValueError("shared-direct V2 child mode differs")
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment.pop(_PUBLIC_PROBE_ENV, None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment[_MODE_ENV] = mode
    if challenge is None:
        environment.pop(_CHALLENGE_ENV, None)
    else:
        environment[_CHALLENGE_ENV] = challenge
    process = subprocess.Popen(
        [sys.executable, "-B", str(_LAUNCHER)],
        cwd=_ROOT,
        env=environment,
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
                raise TimeoutError("shared-direct V2 child wall crossed")
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
                raise ValueError("shared-direct V2 child line exceeds cap")
            kind, payload = _decode_child_event(line)
            on_event(kind, payload)
            process.stdin.write(_ACK)
            process.stdin.flush()
            count += 1
            if count > MAXIMUM_EVENT_COUNT:
                raise ValueError("shared-direct V2 child event count exceeds cap")
        remaining = max(
            0.001,
            (wall_ns - (perf_counter_ns() - started)) / 1_000_000_000,
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
        raise ValueError("shared-direct V2 child stderr exceeds cap")
    return ChildOutcome(return_code=return_code, event_count=count, stderr=stderr)


def run_no_cuda_bootstrap_handshake() -> Mapping[str, object]:
    challenge = secrets.token_bytes(32)
    events: list[tuple[str, Mapping[str, object]]] = []
    outcome = _run_child_process(
        _HANDSHAKE_MODE,
        challenge=challenge.hex(),
        wall_ns=HANDSHAKE_WALL_NS,
        on_event=lambda kind, payload: events.append((kind, payload)),
    )
    if outcome.return_code != 0 or outcome.stderr or len(events) != 1:
        raise RuntimeError("shared-direct V2 bootstrap child rejected")
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
        raise ValueError("shared-direct V2 bootstrap semantics differ")
    return event


def public_launcher_probe() -> Mapping[str, object]:
    challenge = secrets.token_bytes(32)
    events: list[tuple[str, Mapping[str, object]]] = []
    outcome = _run_child_process(
        _PUBLIC_CHILD_MODE,
        challenge=challenge.hex(),
        wall_ns=PUBLIC_PROBE_WALL_NS,
        on_event=lambda kind, payload: events.append((kind, payload)),
    )
    if outcome.return_code != 0 or outcome.stderr or len(events) != 1:
        raise RuntimeError("shared-direct V2 public child rejected")
    kind, child = events[0]
    parent = {
        "literal_module": LITERAL_WORKER_MODULE,
        "spec_name": __spec__.name if __spec__ is not None else None,
        "runtime_name": __name__,
        "repository_root": str(_ROOT.resolve()),
        "source_root": str(_SOURCE),
        "launcher": str(_LAUNCHER),
        "interpreter": str(Path(sys.executable).resolve()),
        "cupy_imported": "cupy" in sys.modules,
        "science_adapter_imported": SCIENCE_ADAPTER_MODULE in sys.modules,
    }
    expected_child = {
        "schema_version": "legal-river-shared-direct-launcher-child-v2",
        "challenge_sha256": sha256(challenge).hexdigest(),
        **parent,
    }
    if kind != "launcher_probe_child" or child != expected_child:
        raise ValueError("shared-direct V2 public child identity differs")
    if _OUTPUT.exists() or _V1_OUTPUT.exists() or _RESERVED.exists():
        raise ValueError("shared-direct V2 public probe observed a result")
    return {
        "schema_version": "legal-river-shared-direct-public-launcher-probe-v2",
        "parent": parent,
        "child": dict(child),
        "child_command": [sys.executable, "-B", str(_LAUNCHER)],
        "pythonpath_present": "PYTHONPATH" in os.environ,
        "pythonhome_present": "PYTHONHOME" in os.environ,
        "v1_result_absent": True,
        "v2_result_absent": True,
        "reserved_actual_result_absent": True,
    }


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
            raise RuntimeError("shared-direct V2 journal cap would be crossed")
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
        raise ValueError("shared-direct V2 owner output path differs")
    verify_preregistered_contract()
    if _V1_OUTPUT.exists() or _RESERVED.exists():
        raise FileExistsError("shared-direct V2 protected authority exists")
    if path.exists():
        raise FileExistsError("shared-direct V2 result already exists")
    strict_git_metadata(result_created=False)
    handshake_passed = False
    terminal_name = "infrastructure_failure"
    terminal_reason = "V2 owner did not reach campaign"
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

            def append_event(
                kind: str, event: Mapping[str, object]
            ) -> None:
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
                            "shared-direct V2 terminal evidence repeated"
                        )
                    terminal_evidence = event

            remaining = PARENT_HARD_WALL_NS - (perf_counter_ns() - started)
            if remaining <= 0:
                raise TimeoutError("shared-direct V2 owner wall crossed")
            outcome = _run_child_process(
                _CAMPAIGN_MODE,
                challenge=None,
                wall_ns=remaining,
                on_event=append_event,
            )
            if outcome.return_code != 0 or outcome.stderr:
                raise RuntimeError(
                    "shared-direct V2 campaign child failed: "
                    + outcome.stderr.decode("utf-8", errors="replace")[:1024]
                )
            if terminal_evidence is None:
                raise RuntimeError(
                    "shared-direct V2 campaign omitted terminal evidence"
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
        raise RuntimeError("shared-direct V2 retained journal exceeds cap")
    return outer


def main() -> None:
    mode = os.environ.get(_MODE_ENV)
    if mode is not None:
        if mode == _HANDSHAKE_MODE:
            raise SystemExit(
                _handshake_child(os.environ.get(_CHALLENGE_ENV, ""))
            )
        if mode == _PUBLIC_CHILD_MODE:
            raise SystemExit(
                _public_probe_child(os.environ.get(_CHALLENGE_ENV, ""))
            )
        if mode == _CAMPAIGN_MODE:
            raise SystemExit(_campaign_child())
        raise SystemExit("unknown shared-direct V2 child mode")
    if os.environ.get(_PUBLIC_PROBE_ENV) == "1":
        if len(sys.argv) != 1:
            raise SystemExit("shared-direct V2 probe accepts no arguments")
        print(
            canonical_journal_json_bytes(public_launcher_probe()).decode(
                "utf-8"
            )
        )
        return
    if len(sys.argv) != 1:
        raise SystemExit("shared-direct V2 owner accepts no arguments")
    terminal = execute_owner_to_path()
    print(json.dumps(terminal, sort_keys=True))


if __name__ == "__main__":
    main()


__all__ = [
    "CAMPAIGN_SHA256",
    "CLAIMS",
    "CONFIG_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "LAUNCHER_RELATIVE_PATH",
    "LITERAL_WORKER_MODULE",
    "PROTOCOL_SHA256",
    "RESULT_RELATIVE_PATH",
    "dependency_hashes",
    "execute_owner_to_path",
    "public_launcher_probe",
    "run_no_cuda_bootstrap_handshake",
    "strict_git_metadata",
    "verify_preregistered_contract",
]
