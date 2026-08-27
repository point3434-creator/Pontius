"""Exclusive split-environment owner for the ADR-0457 calibration."""

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


ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v1.json"
)
CONFIG_SHA256 = "a9a0961656c66d70d145c9f5434460826f3c4972b7b1a18da74b0886a14e18bf"
PREREGISTRATION_COMMIT = "cb90e1d5581034f1988c0e2edfa8777972768a20"
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v1.jsonl"
)
RESULT_PATH = ROOT / RESULT_RELATIVE_PATH
LITERAL_WORKER_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration_runner"
)
SCIENTIFIC_MODULE = (
    "pontius.legal_river_quotient_compiled_global_separation_calibration"
)
PROTOCOL_SHA256 = sha256(b"pontius-adr0457-compiled-separation-owner-v1").hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0457-compiled-separation-calibration-v1"
).hexdigest()

PUBLIC_WALL_NS = 1_800_000_000_000
LABORATORY_WALL_NS = 1_500_000_000_000
OUTSIDE_LABORATORY_WALL_NS = 300_000_000_000
MAXIMUM_JOURNAL_BYTES = 67_108_864
MAXIMUM_EVENT_BYTES = 16_777_216
MAXIMUM_CHILD_FRAME_BYTES = 1_048_576
MAXIMUM_STDERR_BYTES = 4_096
MAXIMUM_EVENTS = 4_096

_MODE_ENV = "PONTIUS_ADR0457_COMPILED_SEPARATION_MODE"
_CHALLENGE_ENV = "PONTIUS_ADR0457_COMPILED_SEPARATION_CHALLENGE"
_SPOOL_ENV = "PONTIUS_ADR0457_COMPILED_SEPARATION_SPOOL"
_SOURCE_PROBE = "source_probe"
_CAMPAIGN_CHILD = "campaign_child"
_EVENT_PREFIX = b"PONTIUS_ADR0457_EVENT "
_ACK_PREFIX = b"PONTIUS_ADR0457_ACK "

CLAIMS = {
    "compiled_calibration_result": None,
    "production_base_classification": "producer_absent",
    "production_base_numerical_admission": None,
    "material_zeta_speed_claim": None,
    "symbolic_45_primitive_projection": None,
    "candidate_selected": None,
    "topology_selected": None,
    "arithmetic_schedule_selected": None,
    "literal_45_numerical_result": None,
    "resolver_iteration_result": None,
    "action_clock_result": None,
    "decision_quality_result": None,
    "truncation_authorized": False,
    "blueprint_result": None,
    "poker_strength_result": None,
}

DEPENDENCY_RELATIVE_PATHS = (
    CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0457-preregister-the-compiled-global-separation-calibration.md",
    "docs/decisions/ADR-0458-source-seal-the-compiled-global-separation-calibration.md",
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


@dataclass(frozen=True, slots=True)
class OwnerExecution:
    terminal: Mapping[str, object]
    event_count: int


class PublicProcessTimeout(TimeoutError):
    """The public watchdog, distinct from the scientific laboratory wall."""


def _canonical_lf(raw: bytes) -> bytes:
    if type(raw) is not bytes:
        raise TypeError("runner canonical input must be bytes")
    output = bytearray()
    cursor = 0
    while cursor < len(raw):
        if raw[cursor] == 13 and cursor + 1 < len(raw) and raw[cursor + 1] == 10:
            output.append(10)
            cursor += 2
        else:
            output.append(raw[cursor])
            cursor += 1
    return bytes(output)


def dependency_hashes() -> dict[str, str]:
    result = {}
    for relative in DEPENDENCY_RELATIVE_PATHS:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"calibration dependency is absent: {relative}")
        result[relative] = sha256(_canonical_lf(path.read_bytes())).hexdigest()
    return result


def _git(*arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        timeout=30.0,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode("utf-8", "replace")[:4096]
        raise RuntimeError(f"calibration Git metadata failed: {detail}")
    return completed.stdout


def strict_git_metadata(*, result_created: bool) -> dict[str, object]:
    commit = _git("rev-parse", "HEAD").decode("ascii").strip()
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise RuntimeError("calibration source commit identity differs")
    for relative in DEPENDENCY_RELATIVE_PATHS:
        tracked = _git("ls-files", "--error-unmatch", "--", relative)
        if tracked.decode("utf-8").strip().replace("\\", "/") != relative:
            raise RuntimeError(f"calibration dependency is not tracked: {relative}")
    status = _git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = [row.replace(b"\\", b"/") for row in status.split(b"\0") if row]
    expected = [f"?? {RESULT_RELATIVE_PATH}".encode("utf-8")] if result_created else []
    if entries != expected:
        raise RuntimeError("calibration owner requires its exact clean source seal")
    if RESULT_PATH.exists() is not result_created:
        raise RuntimeError("calibration result lifecycle differs")
    return {"commit": commit, "dirty": False, "strict_status": True}


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(dict(payload))).hexdigest()


def _header_payload(git: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": "pontius-adr0457-owner-header-v1",
        "protocol_sha256": PROTOCOL_SHA256,
        "campaign_sha256": CAMPAIGN_SHA256,
        "config_sha256": CONFIG_SHA256,
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "source_seal_git": dict(git),
        "dependency_hashes": dependency_hashes(),
        "result_relative_path": RESULT_RELATIVE_PATH,
        "literal_worker_module": LITERAL_WORKER_MODULE,
        "scientific_module": SCIENTIFIC_MODULE,
        "calls_under_one_public_owner": 2_880,
        "claims": dict(CLAIMS),
    }


def _terminal_payload(
    *,
    terminal: str,
    reason: str,
    event_count: int,
    public_elapsed_ns: int,
    laboratory_elapsed_ns: int | None,
) -> dict[str, object]:
    outside = (
        None
        if laboratory_elapsed_ns is None
        else public_elapsed_ns - laboratory_elapsed_ns
    )
    success = terminal == "completed_reduced_compiled_calibration_production_base_absent"
    claims = dict(CLAIMS)
    if success:
        claims["compiled_calibration_result"] = True
        claims["symbolic_45_primitive_projection"] = True
    return {
        "schema_version": "pontius-adr0457-owner-terminal-v1",
        "terminal": terminal,
        "passed": success,
        "reason": reason[:4096],
        "event_count": event_count,
        "public_elapsed_ns": public_elapsed_ns,
        "public_wall_ns": PUBLIC_WALL_NS,
        "laboratory_elapsed_ns": laboratory_elapsed_ns,
        "laboratory_wall_ns": LABORATORY_WALL_NS,
        "outside_laboratory_elapsed_ns": outside,
        "outside_laboratory_wall_ns": OUTSIDE_LABORATORY_WALL_NS,
        "candidate_selected": None,
        "topology_selected": None,
        "arithmetic_schedule_selected": None,
        "claims": claims,
    }


def _bounded_append(
    writer: DurableEvidenceJournalWriter,
    *,
    kind: JournalRecordKind,
    payload: Mapping[str, object],
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
    reserve = 0
    if kind is not JournalRecordKind.TERMINAL:
        reserve_payload = _terminal_payload(
            terminal="compiled_reduced_calibration_rejected",
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
        reserve = len(JournalRecordEnvelope(body=reserve_body).line_bytes)
    if writer.path.stat().st_size + len(prospective.line_bytes) + reserve > MAXIMUM_JOURNAL_BYTES:
        raise RuntimeError("calibration journal capacity would be exceeded")
    receipt = writer.append(
        kind=kind, semantic_identity_sha256=semantic, payload=payload
    )
    if receipt.line_sha256 != prospective.line_sha256:
        raise RuntimeError("calibration prospective journal identity differs")
    return receipt.line_sha256


def _source_probe_payload(challenge_hex: str) -> dict[str, object]:
    try:
        challenge = bytes.fromhex(challenge_hex)
    except ValueError as error:
        raise ValueError("calibration source-probe challenge differs") from error
    if len(challenge) != 32:
        raise ValueError("calibration source-probe challenge length differs")
    return {
        "schema_version": "pontius-adr0457-source-probe-v1",
        "challenge_sha256": sha256(challenge).hexdigest(),
        "python_no_bytecode": bool(sys.dont_write_bytecode),
        "argv_count": len(sys.argv),
        "cupy_loaded": any(name == "cupy" or name.startswith("cupy.") for name in sys.modules),
        "scientific_source_loaded": SCIENTIFIC_MODULE in sys.modules,
        "compiler_executed": False,
        "device_queried": False,
        "result_absent": not RESULT_PATH.exists(),
    }


def source_seal_probe(challenge_hex: str) -> dict[str, object]:
    """Exercise the inherited split environment without loading science."""

    from . import legal_river_quotient_fixed_width_device_preflight_v2_runner as host
    from . import legal_river_quotient_fixed_width_device_preflight_v3_runner as split

    challenge = bytes.fromhex(challenge_hex)
    if len(challenge) != 32:
        raise ValueError("calibration source-seal challenge differs")
    original = dict(os.environ)
    activated = host.activate_bound_host_environment()
    runtime = split.expected_child_runtime_evidence(activated.environment)
    try:
        host._replace_process_environment(activated.environment)
        with tempfile.TemporaryDirectory(prefix="pontius-adr0457-source-probe-") as directory:
            spool = Path(directory).resolve()
            environment = _child_environment(
                spool,
                activated.environment,
                source_probe=True,
                challenge_hex=challenge_hex,
            )
            completed = subprocess.run(
                [sys.executable, "-B", "-m", LITERAL_WORKER_MODULE],
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                timeout=30.0,
            )
    finally:
        os.environ.clear()
        os.environ.update(original)
    if completed.returncode != 0 or completed.stderr:
        raise RuntimeError(
            "calibration source-probe child failed: "
            + (completed.stderr or completed.stdout).decode("utf-8", "replace")[:4096]
        )
    child = json.loads(completed.stdout)
    if not isinstance(child, dict):
        raise TypeError("calibration source-probe output differs")
    return {
        "schema_version": "pontius-adr0457-split-source-seal-probe-v1",
        "challenge_sha256": sha256(challenge).hexdigest(),
        "host_toolchain": dict(activated.evidence),
        "child_runtime_environment": dict(runtime),
        "child": child,
        "compiler_executed": False,
        "cupy_scientific_imported": False,
        "device_queried": False,
        "result_absent": not RESULT_PATH.exists(),
    }


def _child_environment(
    spool: Path,
    parent_environment: Mapping[str, str],
    *,
    source_probe: bool = False,
    challenge_hex: str | None = None,
) -> dict[str, str]:
    from . import legal_river_quotient_fixed_width_device_preflight_v3_runner as split

    environment = dict(parent_environment)
    environment.update(split.STATIC_CHILD_VALUES)
    environment["PATH"] = str(split.RUNTIME_DIRECTORY) + os.pathsep + parent_environment["PATH"]
    environment[split._MODE_ENV] = split._CAMPAIGN_CHILD
    environment[split._SPOOL_ENV] = str(spool)
    environment[_MODE_ENV] = _SOURCE_PROBE if source_probe else _CAMPAIGN_CHILD
    environment[_SPOOL_ENV] = str(spool)
    if source_probe:
        if challenge_hex is None:
            raise ValueError("source-probe challenge is absent")
        environment[_CHALLENGE_ENV] = challenge_hex
    else:
        environment.pop(_CHALLENGE_ENV, None)
    return environment


def _validate_child_runtime() -> Mapping[str, object]:
    from . import legal_river_quotient_fixed_width_device_preflight_v3_runner as split

    filtered = {
        name: value
        for name, value in os.environ.items()
        if name not in {_MODE_ENV, _SPOOL_ENV, _CHALLENGE_ENV}
    }
    validated = split.validate_child_runtime_environment(
        filtered, expected_mode=split._CAMPAIGN_CHILD
    )
    return validated.runtime_evidence


def _child_emit_factory(spool: Path) -> Callable[[str, Mapping[str, object]], None]:
    counter = 0

    def emit(kind: str, payload: Mapping[str, object]) -> None:
        nonlocal counter
        raw = canonical_journal_json_bytes(dict(payload))
        if len(raw) > MAXIMUM_EVENT_BYTES:
            raise RuntimeError("calibration child event exceeds spool ceiling")
        path = spool / f"event-{counter:04d}.json"
        counter += 1
        with path.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
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
            raise RuntimeError("calibration child descriptor exceeds frame ceiling")
        sys.stdout.buffer.write(frame)
        sys.stdout.buffer.flush()
        acknowledgment = sys.stdin.buffer.readline(MAXIMUM_CHILD_FRAME_BYTES + 1)
        expected = _ACK_PREFIX + sha256(raw).hexdigest().encode("ascii") + b"\n"
        if acknowledgment != expected:
            raise RuntimeError("calibration child ACK differs")

    return emit


def _campaign_child_main() -> int:
    runtime = _validate_child_runtime()
    spool = Path(os.environ[_SPOOL_ENV]).resolve()
    if not spool.is_dir() or not RESULT_PATH.is_file():
        raise RuntimeError("calibration child lifecycle differs")
    emit = _child_emit_factory(spool)
    laboratory_start = perf_counter_ns()
    emit(
        "bootstrap_handshake",
        {
            "schema_version": "pontius-adr0457-bootstrap-v1",
            "literal_worker_module": LITERAL_WORKER_MODULE,
            "python_no_bytecode": bool(sys.dont_write_bytecode),
            "child_runtime_environment": dict(runtime),
            "cupy_loaded": any(
                name == "cupy" or name.startswith("cupy.") for name in sys.modules
            ),
            "scientific_source_loaded": SCIENTIFIC_MODULE in sys.modules,
            "parent_journal_present": RESULT_PATH.is_file(),
        },
    )
    from . import legal_river_quotient_compiled_global_separation_calibration as science

    try:
        evidence = science.execute_calibration(
            emit, laboratory_started_ns=laboratory_start
        )
    except science.CalibrationFailure as error:
        evidence = {
            "schema_version": "pontius-adr0457-compiled-calibration-terminal-evidence-v1",
            "terminal": error.terminal,
            "passed": False,
            "reason": error.reason,
            "laboratory_elapsed_ns": perf_counter_ns() - laboratory_start,
            "candidate_selected": None,
            "topology_selected": None,
            "arithmetic_schedule_selected": None,
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


def _run_campaign_child(
    append_event: Callable[[str, Mapping[str, object]], None],
    parent_environment: Mapping[str, str],
) -> Mapping[str, object]:
    with tempfile.TemporaryDirectory(prefix="pontius-adr0457-spool-") as directory:
        spool = Path(directory).resolve()
        process = subprocess.Popen(
            [sys.executable, "-B", "-m", LITERAL_WORKER_MODULE],
            cwd=ROOT,
            env=_child_environment(spool, parent_environment),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdin is not None and process.stdout is not None
        assert process.stderr is not None
        stderr = bytearray()
        stderr_overflow = Event()
        thread = Thread(
            target=_read_stderr,
            args=(process.stderr, stderr, stderr_overflow),
            daemon=True,
        )
        thread.start()
        timed_out = Event()

        def terminate() -> None:
            timed_out.set()
            if process.poll() is None:
                process.kill()

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
                    raise RuntimeError("calibration child frame exceeds ceiling")
                if not line.startswith(_EVENT_PREFIX) or post_terminal:
                    raise RuntimeError("calibration child stdout lifecycle differs")
                descriptor = json.loads(line[len(_EVENT_PREFIX) : -1])
                if not isinstance(descriptor, dict) or set(descriptor) != {
                    "kind",
                    "name",
                    "byte_count",
                    "sha256",
                }:
                    raise ValueError("calibration child descriptor differs")
                path = (spool / descriptor["name"]).resolve()
                if path.parent != spool or not path.is_file():
                    raise ValueError("calibration spool path escapes")
                raw = path.read_bytes()
                if (
                    len(raw) != descriptor["byte_count"]
                    or len(raw) > MAXIMUM_EVENT_BYTES
                    or sha256(raw).hexdigest() != descriptor["sha256"]
                    or canonical_journal_json_bytes(json.loads(raw)) != raw
                ):
                    raise ValueError("calibration spool evidence differs")
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise TypeError("calibration event must be an object")
                append_event(str(descriptor["kind"]), payload)
                path.unlink()
                process.stdin.write(
                    _ACK_PREFIX + descriptor["sha256"].encode("ascii") + b"\n"
                )
                process.stdin.flush()
                event_count += 1
                if event_count > MAXIMUM_EVENTS:
                    raise RuntimeError("calibration child event count exceeds ceiling")
                if descriptor["kind"] == "terminal_evidence":
                    terminal = payload
                    post_terminal = True
            return_code = process.wait(timeout=5.0)
        finally:
            timer.cancel()
            if process.poll() is None:
                process.kill()
            thread.join(timeout=5.0)
        if timed_out.is_set():
            raise PublicProcessTimeout("calibration public child watchdog crossed")
        if stderr_overflow.is_set():
            raise RuntimeError("calibration child stderr exceeds ceiling")
        if return_code != 0:
            raise RuntimeError(
                f"calibration child exited {return_code}: "
                + bytes(stderr).decode("utf-8", "replace")
            )
        if terminal is None:
            raise RuntimeError("calibration child omitted terminal evidence")
        return terminal


def execute_owner_to_path(
    *,
    output_path: Path,
    campaign_executor: Callable[
        [Callable[[str, Mapping[str, object]], None]], Mapping[str, object]
    ]
    | None = None,
    monotonic_ns: Callable[[], int] = perf_counter_ns,
    parent_environment: Mapping[str, str] | None = None,
) -> OwnerExecution:
    if output_path.exists():
        raise FileExistsError("calibration authority is already consumed")
    git = (
        strict_git_metadata(result_created=False)
        if output_path == RESULT_PATH
        else {"commit": "0" * 40, "dirty": False, "strict_status": True}
    )
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
                    raise RuntimeError("calibration event count exceeds ceiling")
                observation = {
                    "schema_version": "pontius-adr0457-owner-observation-v1",
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
                if kind == "terminal_evidence":
                    value = event.get("laboratory_elapsed_ns")
                    if isinstance(value, bool) or not isinstance(value, int):
                        raise ValueError("calibration laboratory elapsed differs")
                    laboratory_elapsed = value

            if campaign_executor is None:
                if parent_environment is None:
                    raise ValueError("calibration parent environment is absent")
                evidence = _run_campaign_child(append_event, parent_environment)
            else:
                evidence = campaign_executor(append_event)
            terminal = evidence.get("terminal")
            passed = evidence.get("passed")
            if not isinstance(terminal, str) or not isinstance(passed, bool):
                raise ValueError("calibration terminal evidence differs")
            if passed is not (
                terminal
                == "completed_reduced_compiled_calibration_production_base_absent"
            ):
                raise ValueError("calibration terminal pass bit disagrees")
            public_elapsed = monotonic_ns() - started
            if passed:
                if public_elapsed > PUBLIC_WALL_NS:
                    terminal = "public_wall_rejected"
                elif laboratory_elapsed is None or laboratory_elapsed > LABORATORY_WALL_NS:
                    terminal = "laboratory_wall_rejected"
                elif public_elapsed - laboratory_elapsed > OUTSIDE_LABORATORY_WALL_NS:
                    terminal = "outside_laboratory_wall_rejected"
            terminal_payload = _terminal_payload(
                terminal=terminal,
                reason="retained first terminal from the frozen one-shot owner",
                event_count=event_count,
                public_elapsed_ns=public_elapsed,
                laboratory_elapsed_ns=laboratory_elapsed,
            )
        except PublicProcessTimeout as error:
            terminal_payload = _terminal_payload(
                terminal="public_wall_rejected",
                reason=str(error),
                event_count=event_count,
                public_elapsed_ns=monotonic_ns() - started,
                laboratory_elapsed_ns=laboratory_elapsed,
            )
        except BaseException as error:  # noqa: BLE001 - terminal must be durable
            terminal_payload = _terminal_payload(
                terminal="compiled_reduced_calibration_rejected",
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
        raise RuntimeError("calibration journal exceeds byte ceiling")
    return OwnerExecution(terminal_payload, event_count)


def main() -> int:
    if len(sys.argv) != 1 or not sys.dont_write_bytecode:
        raise RuntimeError("compiled calibration requires no arguments and Python -B")
    mode = os.environ.get(_MODE_ENV)
    if mode == _SOURCE_PROBE:
        challenge = os.environ.get(_CHALLENGE_ENV)
        if not isinstance(challenge, str):
            raise ValueError("calibration source-probe challenge is absent")
        _validate_child_runtime()
        print(canonical_journal_json_bytes(_source_probe_payload(challenge)).decode("ascii"))
        return 0
    if mode == _CAMPAIGN_CHILD:
        if _CHALLENGE_ENV in os.environ:
            raise ValueError("calibration campaign challenge is present")
        return _campaign_child_main()
    if mode is not None or _SPOOL_ENV in os.environ or _CHALLENGE_ENV in os.environ:
        raise ValueError("calibration public environment is contaminated")
    if RESULT_PATH.exists():
        raise FileExistsError("calibration authority is already consumed")
    from . import legal_river_quotient_fixed_width_device_preflight_v2_runner as host
    from . import legal_river_quotient_fixed_width_device_preflight_v3_runner as split

    public_origin = perf_counter_ns()
    original = dict(os.environ)
    activated = host.activate_bound_host_environment()
    split.expected_child_runtime_evidence(activated.environment)
    try:
        host._replace_process_environment(activated.environment)
        execution = execute_owner_to_path(
            output_path=RESULT_PATH,
            parent_environment=activated.environment,
            monotonic_ns=_public_clock(public_origin),
        )
    finally:
        os.environ.clear()
        os.environ.update(original)
    print(
        "legal-river compiled global separation calibration: "
        f"terminal={execution.terminal['terminal']} "
        f"passed={execution.terminal['passed']}"
    )
    return 0 if execution.terminal["passed"] is True else 1


def _public_clock(origin_ns: int) -> Callable[[], int]:
    first = True

    def clock() -> int:
        nonlocal first
        if first:
            first = False
            return origin_ns
        return perf_counter_ns()

    return clock


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CAMPAIGN_SHA256",
    "CLAIMS",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "LITERAL_WORKER_MODULE",
    "OwnerExecution",
    "PROTOCOL_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "SCIENTIFIC_MODULE",
    "dependency_hashes",
    "execute_owner_to_path",
    "main",
    "source_seal_probe",
    "strict_git_metadata",
]
