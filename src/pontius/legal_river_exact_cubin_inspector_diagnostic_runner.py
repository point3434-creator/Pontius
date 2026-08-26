"""Exclusive owner for the ADR-0404 exact-cubin diagnostic corpus."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import queue
import secrets
import subprocess
import sys
import threading
from time import perf_counter_ns
from typing import BinaryIO

from .durable_evidence_journal import (
    DurableEvidenceJournalWriter,
    JournalRecordEnvelope,
    JournalRecordKind,
    build_journal_record_body,
    canonical_journal_json_bytes,
)
from . import legal_river_exact_cubin_inspector_diagnostic as diagnostic


_ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = diagnostic.CONFIG_RELATIVE_PATH
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/legal_river_exact_cubin_inspector_diagnostic_v1.jsonl"
)
RESERVED_ACTUAL_RESULT_RELATIVE_PATH = (
    "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"
)
_CONFIG = _ROOT / CONFIG_RELATIVE_PATH
_OUTPUT = _ROOT / RESULT_RELATIVE_PATH
_RESERVED = _ROOT / RESERVED_ACTUAL_RESULT_RELATIVE_PATH
PREREGISTERED_CONFIG_SHA256 = diagnostic.CONFIG_SHA256
PROTOCOL_SHA256 = sha256(
    b"pontius-adr0404-exact-cubin-inspector-diagnostic-exclusive-journal-v1"
).hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0404-exact-cubin-inspector-diagnostic-one-shot-campaign-v1"
).hexdigest()
LITERAL_WORKER_MODULE = "pontius.legal_river_exact_cubin_inspector_diagnostic_runner"
MAXIMUM_ARTIFACT_BYTES = 50_331_648
MAXIMUM_EVENT_COUNT = 16
MAXIMUM_STDERR_BYTES = 65_536
_CHILD_MODE_ENV = "PONTIUS_EXACT_CUBIN_DIAGNOSTIC_CHILD_MODE"
_CHILD_CHALLENGE_ENV = "PONTIUS_EXACT_CUBIN_DIAGNOSTIC_CHALLENGE"
_REAL_MODE = "diagnostic"
_PROBE_MODE = "protocol_probe"
_HANG_MODE = "protocol_hang_after_handshake"
_POST_TERMINAL_MODE = "protocol_emit_after_terminal"
_SCIENTIFIC_TERMINALS = frozenset(
    {
        "capture_complete",
        "candidate_timeout_rejection",
        "candidate_output_limit_rejection",
        "laboratory_wall_rejection",
        "diagnostic_failure",
    }
)


@dataclass(frozen=True, slots=True)
class LoadedConfig:
    payload: Mapping[str, object]
    sha256: str


@dataclass(frozen=True, slots=True)
class OwnerExecution:
    terminal: Mapping[str, object]
    event_count: int


def canonical_lf_sha256(path: Path) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError(f"exact-cubin owner dependency is absent: {path}")
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def parse_config(value: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError("exact-cubin owner config must be a mapping")
    scope = value.get("successor_scope")
    capture = value.get("lossless_capture_contract")
    lifecycle = value.get("owner_and_journal_contract")
    interpretation = value.get("candidate_interpretation_contract")
    claims = value.get("claims")
    candidates = value.get("candidate_commands_in_order")
    if (
        value.get("schema_version")
        != "legal-river-exact-cubin-inspector-diagnostic-preregistration-v1"
        or not isinstance(scope, Mapping)
        or not isinstance(capture, Mapping)
        or not isinstance(lifecycle, Mapping)
        or not isinstance(interpretation, Mapping)
        or not isinstance(claims, Mapping)
        or not isinstance(candidates, list)
        or scope.get("result_relative_path") != RESULT_RELATIVE_PATH
        or scope.get("reserved_actual_result_relative_path")
        != RESERVED_ACTUAL_RESULT_RELATIVE_PATH
        or capture.get("journal_byte_limit") != MAXIMUM_ARTIFACT_BYTES
        or capture.get("laboratory_wall_limit_ns") != diagnostic.LABORATORY_WALL_NS
        or lifecycle.get("new_protocol_seed")
        != "pontius-adr0404-exact-cubin-inspector-diagnostic-exclusive-journal-v1"
        or lifecycle.get("new_campaign_seed")
        != "pontius-adr0404-exact-cubin-inspector-diagnostic-one-shot-campaign-v1"
        or interpretation.get("selected_inspector") is not None
        or len(candidates) != 5
        or any(value not in (None, False) for value in claims.values())
    ):
        raise ValueError("exact-cubin owner config contract differs")
    return value


def load_public_config(path: Path = _CONFIG) -> LoadedConfig:
    if not isinstance(path, Path):
        raise TypeError("exact-cubin owner config path must be a Path")
    raw = path.read_bytes()
    digest = sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    if digest != PREREGISTERED_CONFIG_SHA256:
        raise ValueError("exact-cubin owner config differs from ADR-0404")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise TypeError("exact-cubin owner config must be an object")
    parse_config(value)
    parent = value["parent_identity"]
    assert isinstance(parent, Mapping)
    for relative_field, digest_field in (
        ("adr0403_relative_path", "adr0403_canonical_lf_sha256"),
        (
            "immutable_scientific_source_relative_path",
            "immutable_scientific_source_canonical_lf_sha256",
        ),
    ):
        relative = parent.get(relative_field)
        expected = parent.get(digest_field)
        if (
            not isinstance(relative, str)
            or not isinstance(expected, str)
            or canonical_lf_sha256(_ROOT / relative) != expected
        ):
            raise ValueError(f"exact-cubin owner bound dependency differs: {relative_field}")
    return LoadedConfig(payload=value, sha256=digest)


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30.0,
    )
    return completed.stdout


def strict_git_metadata(result_path: Path = _OUTPUT) -> dict[str, object]:
    commit = _git("rev-parse", "HEAD").strip()
    if len(commit) != 40:
        raise RuntimeError("exact-cubin owner Git commit differs")
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        timeout=30.0,
    ).stdout
    entries = [item.decode("utf-8") for item in raw.split(b"\0") if item]
    relative = result_path.resolve().relative_to(_ROOT.resolve()).as_posix()
    allowed = {f"?? {relative}"}
    if set(entries) != allowed:
        raise RuntimeError(f"exact-cubin owner strict Git boundary rejected: {entries!r}")
    return {"commit": commit, "dirty": False, "strict_status": True}


def retained_artifact_facts() -> dict[str, object]:
    rows = {
        "v1": (
            _ROOT
            / "artifacts/work_preflight/legal_river_quotient_cuda_compensated_work_preflight_v1.jsonl",
            "fd8c71ddb534320577dfc9a390946fc3dffe3fe806bf93d456ac33e55fe8e830",
            5322,
            3,
        ),
        "v2": (
            _ROOT
            / "artifacts/work_preflight/legal_river_quotient_cuda_compensated_work_preflight_v2.jsonl",
            "9b9a3f606004a281773f6dc83c86fe2f70811ab825fbf1e0b8b47c1c75abdad3",
            8508,
            4,
        ),
        "v3": (
            _ROOT
            / "artifacts/work_preflight/legal_river_quotient_cuda_compensated_work_preflight_v3.jsonl",
            "b84d9cd22042427c88f9c42b2da7acd176cdd0d5dec654c7f361bae7fa79cd0d",
            15783,
            7,
        ),
    }
    result: dict[str, object] = {}
    for name, (path, digest, byte_count, records) in rows.items():
        raw = path.read_bytes()
        if (
            sha256(raw).hexdigest() != digest
            or len(raw) != byte_count
            or len(raw.splitlines()) != records
        ):
            raise ValueError(f"exact-cubin owner retained {name} artifact differs")
        result[name] = {
            "relative_path": path.relative_to(_ROOT).as_posix(),
            "sha256": digest,
            "byte_count": byte_count,
            "record_count": records,
        }
    return result


def dependency_hashes() -> dict[str, str]:
    paths = {
        "config": _CONFIG,
        "adr0403": _ROOT
        / "docs/decisions/ADR-0403-retain-the-work-preflight-v3-resource-inspector-rejection.md",
        "adr0404": _ROOT
        / "docs/decisions/ADR-0404-preregister-the-exact-cubin-inspector-diagnostic.md",
        "scientific_source": _ROOT / diagnostic.SCIENTIFIC_SOURCE_RELATIVE_PATH,
        "diagnostic": _ROOT
        / "src/pontius/legal_river_exact_cubin_inspector_diagnostic.py",
        "owner": _ROOT
        / "src/pontius/legal_river_exact_cubin_inspector_diagnostic_runner.py",
        "reader": _ROOT
        / "src/pontius/legal_river_exact_cubin_inspector_diagnostic_result.py",
        "controls": _ROOT
        / "tests/test_legal_river_exact_cubin_inspector_diagnostic.py",
        "durable_journal": _ROOT / "src/pontius/durable_evidence_journal.py",
    }
    return {name: canonical_lf_sha256(path) for name, path in paths.items()}


def _semantic_digest(payload: Mapping[str, object]) -> str:
    return sha256(canonical_journal_json_bytes(payload)).hexdigest()


def _header_payload() -> dict[str, object]:
    return {
        "schema_version": "legal-river-exact-cubin-diagnostic-owner-header-v1",
        "protocol_sha256": PROTOCOL_SHA256,
        "campaign_sha256": CAMPAIGN_SHA256,
        "config_relative_path": CONFIG_RELATIVE_PATH,
        "config_sha256": PREREGISTERED_CONFIG_SHA256,
        "result_relative_path": RESULT_RELATIVE_PATH,
        "reserved_actual_result_relative_path": RESERVED_ACTUAL_RESULT_RELATIVE_PATH,
        "literal_worker_module": LITERAL_WORKER_MODULE,
        "selected_inspector": None,
        "calibration_result": None,
        "capacity_projection": None,
    }


def _observation(
    *,
    index: int,
    kind: str,
    event: Mapping[str, object],
    config_sha256: str,
    source_commit: str,
) -> dict[str, object]:
    return {
        "schema_version": "legal-river-exact-cubin-diagnostic-observation-v1",
        "event_index": index,
        "event_kind": kind,
        "event": dict(event),
        "config_sha256": config_sha256,
        "source_commit": source_commit,
    }


def _terminal_payload(
    *,
    terminal: str,
    passed: bool,
    reason: str,
    event_count: int,
    last_identity: str | None,
) -> dict[str, object]:
    bounded_reason = reason.encode("ascii", "backslashreplace").decode("ascii")[:4096]
    return {
        "schema_version": "legal-river-exact-cubin-diagnostic-owner-terminal-v1",
        "terminal": terminal,
        "passed": passed,
        "reason": bounded_reason,
        "event_count": event_count,
        "last_event_semantic_identity_sha256": last_identity,
        "selected_inspector": None,
        "resource_gate_result": None,
        "calibration_result": None,
        "capacity_projection": None,
    }


def _frame(kind: str, event: Mapping[str, object]) -> bytes:
    return canonical_journal_json_bytes({"kind": kind, "event": dict(event)}) + b"\n"


def _write_frame(kind: str, event: Mapping[str, object]) -> None:
    sys.stdout.buffer.write(_frame(kind, event))
    sys.stdout.buffer.flush()


def _wait_for_ack(index: int, challenge: str) -> None:
    raw = sys.stdin.buffer.readline()
    expected = f"ACK {index} {challenge}\n".encode("ascii")
    if raw != expected:
        raise RuntimeError("exact-cubin child durable ack differs")


def _synthetic_compiler_event() -> dict[str, object]:
    cubin = diagnostic.encode_binary(b"\x7fELF\x00\xffsynthetic-cubin")
    driver = {
        name: {
            "local_size_bytes": 0,
            "registers": 32 + index,
            "shared_size_bytes": 0,
            "maximum_threads_per_block": 256,
        }
        for index, name in enumerate(diagnostic.DIRECT_KERNEL_NAMES)
    }
    return {
        "schema_version": "legal-river-exact-cubin-compiler-capture-v1",
        "runtime": {
            "device_name": "protocol-probe-no-device",
            "compute_capability": "00",
            "device_total_bytes": 0,
            "cuda_driver_version": 0,
            "cuda_runtime_version": 0,
            "cupy_version": "protocol-probe-no-cupy",
        },
        "caller_options": list(diagnostic.CALLER_OPTIONS),
        "effective_internal_arch_option": "-arch=sm_00",
        "output_method": "cubin",
        "kernel_names": list(diagnostic.ALL_KERNEL_NAMES),
        "direct_driver_rows": driver,
        "cubin": cubin,
    }


def _worker_main(mode: str, challenge: str) -> int:
    if mode not in {_REAL_MODE, _PROBE_MODE, _HANG_MODE, _POST_TERMINAL_MODE}:
        raise ValueError("exact-cubin child mode differs")
    if len(challenge) != 64 or any(character not in "0123456789abcdef" for character in challenge):
        raise ValueError("exact-cubin child challenge differs")
    index = 0

    def emit_and_wait(kind: str, event: Mapping[str, object]) -> None:
        nonlocal index
        _write_frame(kind, event)
        _wait_for_ack(index, challenge)
        index += 1

    emit_and_wait(
        "bootstrap_handshake",
        {
            "schema_version": "legal-river-exact-cubin-diagnostic-handshake-v1",
            "challenge": challenge,
            "literal_worker_module": LITERAL_WORKER_MODULE,
            "runtime_name": __name__,
            "spec_name": __spec__.name if __spec__ is not None else None,
            "python_no_bytecode": sys.dont_write_bytecode,
            "cupy_loaded": "cupy" in sys.modules,
            "scientific_source_loaded": (
                "pontius.legal_river_quotient_cuda_compensated_work_preflight"
                in sys.modules
            ),
        },
    )
    if mode == _HANG_MODE:
        # The parent must enforce the deadline while stdout remains open and silent.
        threading.Event().wait(10.0)
        return 1
    if mode == _POST_TERMINAL_MODE:
        terminal = {
            "schema_version": "legal-river-exact-cubin-diagnostic-terminal-evidence-v1",
            "terminal": "diagnostic_failure",
            "passed": False,
            "reason": "synthetic terminal before forbidden extra frame",
            "candidate_events_retained": 0,
            "selected_inspector": None,
            "resource_gate_result": None,
            "calibration_result": None,
            "capacity_projection": None,
        }
        emit_and_wait("terminal_evidence", terminal)
        _write_frame(
            "post_terminal_forbidden",
            {"schema_version": "forbidden-post-terminal-control-v1"},
        )
        return 1
    try:
        if mode == _PROBE_MODE:
            emit_and_wait("compiler_capture", _synthetic_compiler_event())
            for candidate_index, row in enumerate(
                diagnostic.load_preregistered_config()["candidate_commands_in_order"]
            ):
                assert isinstance(row, Mapping)
                stdout = bytes((candidate_index, 0, 255)) + b"stdout"
                stderr = bytes((255 - candidate_index, 0)) + b"stderr"
                tool = (
                    r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\cuobjdump.exe"
                    if row["tool"] == "CUDA_13_3_cuobjdump"
                    else r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvdisasm.exe"
                )
                arguments = [
                    r"C:\Users\point\AppData\Local\Temp\protocol-probe.cubin"
                    if item == "{exact_temporary_cubin}"
                    else item
                    for item in row["arguments"]
                ]
                emit_and_wait(
                    "candidate_command",
                    {
                        "schema_version": "legal-river-exact-cubin-candidate-command-v1",
                        "candidate_index": candidate_index,
                        "candidate_id": row["candidate_id"],
                        "semantic_role": row["semantic_role"],
                        "uses_cubin": row["uses_cubin"],
                        "argv": [tool, *arguments],
                        "status": "completed",
                        "return_code": candidate_index + 1,
                        "stdout": diagnostic.encode_binary(stdout),
                        "stderr": diagnostic.encode_binary(stderr),
                        "elapsed_ns": candidate_index + 1,
                    },
                )
            emit_and_wait(
                "cleanup",
                {
                    "schema_version": "legal-river-exact-cubin-cleanup-v1",
                    "temporary_cubin_removed": True,
                    "candidate_events_retained": 5,
                },
            )
            terminal = {
                "schema_version": "legal-river-exact-cubin-diagnostic-terminal-evidence-v1",
                "terminal": "capture_complete",
                "passed": True,
                "reason": "synthetic protocol capture complete",
                "candidate_events_retained": 5,
                "selected_inspector": None,
                "resource_gate_result": None,
                "calibration_result": None,
                "capacity_projection": None,
            }
        else:
            terminal = diagnostic.run_real_diagnostic(emit_and_wait)
    except BaseException as error:  # noqa: BLE001 - child failure is evidence
        emit_and_wait(
            "worker_failure",
            {
                "schema_version": "legal-river-exact-cubin-diagnostic-worker-failure-v1",
                "reason": f"{type(error).__name__}: {(str(error) or 'no message')[:4096]}",
            },
        )
        terminal = {
            "schema_version": "legal-river-exact-cubin-diagnostic-terminal-evidence-v1",
            "terminal": "diagnostic_failure",
            "passed": False,
            "reason": "fresh child retained a diagnostic failure",
            "candidate_events_retained": 0,
            "selected_inspector": None,
            "resource_gate_result": None,
            "calibration_result": None,
            "capacity_projection": None,
        }
    emit_and_wait("terminal_evidence", terminal)
    return 0 if terminal["terminal"] == "capture_complete" else 1


def _strict_frame(line: bytes) -> tuple[str, Mapping[str, object]]:
    if not line.endswith(b"\n") or line.endswith(b"\r\n"):
        raise ValueError("exact-cubin child frame must end in LF")
    value = json.loads(line)
    if not isinstance(value, dict) or set(value) != {"kind", "event"}:
        raise ValueError("exact-cubin child frame shape differs")
    canonical = canonical_journal_json_bytes(value) + b"\n"
    if canonical != line:
        raise ValueError("exact-cubin child frame is not canonical")
    kind = value["kind"]
    event = value["event"]
    if not isinstance(kind, str) or not isinstance(event, Mapping):
        raise TypeError("exact-cubin child frame types differ")
    return kind, event


def _drain_stderr(pipe: BinaryIO, sink: queue.Queue[bytes]) -> None:
    collected = bytearray()
    overflow = False
    try:
        while True:
            chunk = pipe.read(4096)
            if not chunk:
                break
            room = max(0, MAXIMUM_STDERR_BYTES - len(collected))
            collected.extend(chunk[:room])
            if len(chunk) > room:
                overflow = True
    finally:
        pipe.close()
    sink.put(b"__OVERFLOW__" if overflow else bytes(collected))


def _drain_stdout(pipe: BinaryIO, sink: queue.Queue[bytes | None]) -> None:
    try:
        while True:
            line = pipe.readline()
            if not line:
                break
            sink.put(line)
    finally:
        pipe.close()
        sink.put(None)


def run_child_process(
    *,
    mode: str,
    emit: Callable[[str, Mapping[str, object]], None],
    wall_limit_ns: int,
) -> Mapping[str, object]:
    if mode not in {_REAL_MODE, _PROBE_MODE, _HANG_MODE, _POST_TERMINAL_MODE}:
        raise ValueError("exact-cubin parent child mode differs")
    challenge = secrets.token_hex(32)
    env = dict(os.environ)
    env[_CHILD_MODE_ENV] = mode
    env[_CHILD_CHALLENGE_ENV] = challenge
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    current_pythonpath = env.get("PYTHONPATH", "")
    prefix = os.pathsep.join((str(_ROOT / "src"), str(_ROOT)))
    env["PYTHONPATH"] = prefix + (os.pathsep + current_pythonpath if current_pythonpath else "")
    creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0)) if os.name == "nt" else 0
    process = subprocess.Popen(
        [sys.executable, "-B", "-m", LITERAL_WORKER_MODULE],
        cwd=_ROOT,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags,
    )
    if process.stdin is None or process.stdout is None or process.stderr is None:
        process.kill()
        raise RuntimeError("exact-cubin child pipes are absent")
    stderr_queue: queue.Queue[bytes] = queue.Queue(maxsize=2)
    stdout_queue: queue.Queue[bytes | None] = queue.Queue(maxsize=2)
    stderr_thread = threading.Thread(
        target=_drain_stderr,
        args=(process.stderr, stderr_queue),
        daemon=True,
    )
    stdout_thread = threading.Thread(
        target=_drain_stdout,
        args=(process.stdout, stdout_queue),
        daemon=True,
    )
    stderr_thread.start()
    stdout_thread.start()
    started = perf_counter_ns()
    index = 0
    terminal: Mapping[str, object] | None = None
    total_stdout = 0
    try:
        while True:
            remaining_ns = wall_limit_ns - (perf_counter_ns() - started)
            if remaining_ns <= 0:
                raise TimeoutError("exact-cubin child laboratory wall crossed")
            try:
                line = stdout_queue.get(timeout=min(0.1, remaining_ns / 1e9))
            except queue.Empty:
                continue
            if line is None:
                if perf_counter_ns() - started > wall_limit_ns:
                    raise TimeoutError("exact-cubin child laboratory wall crossed at EOF")
                break
            total_stdout += len(line)
            if total_stdout > MAXIMUM_ARTIFACT_BYTES:
                raise RuntimeError("exact-cubin child stdout exceeds journal cap")
            kind, event = _strict_frame(line)
            if terminal is not None:
                raise RuntimeError("exact-cubin child emitted after terminal evidence")
            emit(kind, event)
            if perf_counter_ns() - started > wall_limit_ns:
                raise TimeoutError(
                    "exact-cubin child laboratory wall crossed after durable append"
                )
            process.stdin.write(f"ACK {index} {challenge}\n".encode("ascii"))
            process.stdin.flush()
            index += 1
            if kind == "terminal_evidence":
                terminal = event
        process.stdin.close()
        remaining = max(0.001, (wall_limit_ns - (perf_counter_ns() - started)) / 1e9)
        process.wait(timeout=remaining)
        if perf_counter_ns() - started > wall_limit_ns:
            raise TimeoutError("exact-cubin child laboratory wall crossed at exit")
    except BaseException:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5.0)
        if not process.stdin.closed:
            process.stdin.close()
        raise
    finally:
        stderr_thread.join(timeout=5.0)
        stdout_thread.join(timeout=5.0)
    if stderr_thread.is_alive() or stdout_thread.is_alive():
        raise RuntimeError("exact-cubin child pipe reader did not terminate")
    stderr = stderr_queue.get_nowait() if not stderr_queue.empty() else b""
    if stderr == b"__OVERFLOW__":
        raise RuntimeError("exact-cubin child stderr exceeds cap")
    if terminal is None:
        raise RuntimeError(
            f"exact-cubin child omitted terminal evidence: {stderr.decode('utf-8', 'replace')[:4096]}"
        )
    expected_code = 0 if terminal.get("terminal") == "capture_complete" else 1
    if process.returncode != expected_code:
        raise RuntimeError(
            f"exact-cubin child exit {process.returncode} disagrees with terminal"
        )
    return terminal


def run_device_free_protocol_probe(
    emit: Callable[[str, Mapping[str, object]], None]
) -> Mapping[str, object]:
    return run_child_process(mode=_PROBE_MODE, emit=emit, wall_limit_ns=30_000_000_000)


def _failure_reason(error: BaseException) -> str:
    return f"{type(error).__name__}: {(str(error) or 'exception carried no message')[:4096]}"


CampaignExecutor = Callable[
    [Callable[[str, Mapping[str, object]], None], int], Mapping[str, object]
]


def _real_campaign_executor(
    emit: Callable[[str, Mapping[str, object]], None], wall_limit_ns: int
) -> Mapping[str, object]:
    return run_child_process(mode=_REAL_MODE, emit=emit, wall_limit_ns=wall_limit_ns)


def execute_owner_to_path(
    *,
    output_path: Path,
    config_loader: Callable[[], LoadedConfig] = load_public_config,
    git_loader: Callable[[], Mapping[str, object]] = strict_git_metadata,
    hashes_loader: Callable[[], Mapping[str, str]] = dependency_hashes,
    retained_loader: Callable[[], Mapping[str, object]] = retained_artifact_facts,
    campaign_executor: CampaignExecutor = _real_campaign_executor,
    reserved_path: Path = _RESERVED,
) -> OwnerExecution:
    if not isinstance(output_path, Path) or not isinstance(reserved_path, Path):
        raise TypeError("exact-cubin owner paths must be Paths")
    event_count = 0
    last_identity: str | None = None
    last_line_sha256: str | None = None
    terminal_payload: Mapping[str, object]
    with DurableEvidenceJournalWriter.create(
        path=output_path,
        protocol_sha256=PROTOCOL_SHA256,
        campaign_sha256=CAMPAIGN_SHA256,
    ) as writer:
        header = _header_payload()
        header_receipt = writer.append(
            kind=JournalRecordKind.HEADER,
            semantic_identity_sha256=_semantic_digest(header),
            payload=header,
        )
        last_line_sha256 = header_receipt.line_sha256
        try:
            loaded = config_loader()
            if not isinstance(loaded, LoadedConfig):
                raise TypeError("exact-cubin owner config loader returned wrong type")
            parse_config(loaded.payload)
            git = git_loader()
            if (
                git.get("dirty") is not False
                or git.get("strict_status") is not True
                or not isinstance(git.get("commit"), str)
            ):
                raise RuntimeError("exact-cubin owner strict Git facts differ")
            retained = retained_loader()
            if not isinstance(retained, Mapping) or set(retained) != {"v1", "v2", "v3"}:
                raise ValueError("exact-cubin retained artifact facts differ")

            def append_event(kind: str, event: Mapping[str, object]) -> None:
                nonlocal event_count, last_identity, last_line_sha256
                if event_count >= MAXIMUM_EVENT_COUNT:
                    raise RuntimeError("exact-cubin event count exceeds ceiling")
                observation = _observation(
                    index=event_count,
                    kind=kind,
                    event=event,
                    config_sha256=loaded.sha256,
                    source_commit=str(git["commit"]),
                )
                identity = _semantic_digest(observation)
                if last_line_sha256 is None:
                    raise RuntimeError("exact-cubin writer lost its prior line identity")
                prospective_body = build_journal_record_body(
                    protocol_sha256=PROTOCOL_SHA256,
                    campaign_sha256=CAMPAIGN_SHA256,
                    kind=JournalRecordKind.OBSERVATION,
                    sequence=writer.next_sequence,
                    previous_record_sha256=last_line_sha256,
                    semantic_identity_sha256=identity,
                    payload=observation,
                )
                prospective = JournalRecordEnvelope(body=prospective_body)
                longest_terminal = max(
                    _SCIENTIFIC_TERMINALS | {"infrastructure_failure"}, key=len
                )
                reserve_payload = _terminal_payload(
                    terminal=longest_terminal,
                    passed=False,
                    reason="x" * 4096,
                    event_count=MAXIMUM_EVENT_COUNT,
                    last_identity="f" * 64,
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
                reserve = JournalRecordEnvelope(body=reserve_body)
                if (
                    output_path.stat().st_size
                    + len(prospective.line_bytes)
                    + len(reserve.line_bytes)
                    > MAXIMUM_ARTIFACT_BYTES
                ):
                    raise RuntimeError(
                        "exact-cubin observation would exceed the journal cap"
                    )
                receipt = writer.append(
                    kind=JournalRecordKind.OBSERVATION,
                    semantic_identity_sha256=identity,
                    payload=observation,
                )
                if receipt.line_sha256 != prospective.line_sha256:
                    raise RuntimeError("exact-cubin prospective append identity differs")
                event_count += 1
                last_identity = identity
                last_line_sha256 = receipt.line_sha256

            append_event(
                "provenance",
                {
                    "schema_version": "legal-river-exact-cubin-diagnostic-provenance-v1",
                    "config_sha256": loaded.sha256,
                    "source_commit": git["commit"],
                    "source_dirty": False,
                    "dependency_hashes": dict(hashes_loader()),
                    "retained_artifacts": dict(retained),
                    "reserved_actual_result_absent": not reserved_path.exists(),
                    "literal_worker_module": LITERAL_WORKER_MODULE,
                },
            )
            if reserved_path.exists():
                raise RuntimeError("reserved actual result is present")
            evidence = campaign_executor(append_event, diagnostic.LABORATORY_WALL_NS)
            if not isinstance(evidence, Mapping):
                raise TypeError("exact-cubin campaign terminal must be a mapping")
            terminal = evidence.get("terminal")
            passed = evidence.get("passed")
            if terminal not in _SCIENTIFIC_TERMINALS or not isinstance(passed, bool):
                raise ValueError("exact-cubin campaign terminal is malformed")
            if passed is not (terminal == "capture_complete"):
                raise ValueError("exact-cubin campaign pass bit disagrees")
            terminal_payload = _terminal_payload(
                terminal=terminal,
                passed=passed,
                reason="retained first diagnostic terminal evidence",
                event_count=event_count,
                last_identity=last_identity,
            )
        except TimeoutError as error:
            terminal_payload = _terminal_payload(
                terminal="laboratory_wall_rejection",
                passed=False,
                reason=_failure_reason(error),
                event_count=event_count,
                last_identity=last_identity,
            )
        except BaseException as error:  # noqa: BLE001 - first failure is evidence
            terminal_payload = _terminal_payload(
                terminal="infrastructure_failure",
                passed=False,
                reason=_failure_reason(error),
                event_count=event_count,
                last_identity=last_identity,
            )
        writer.append(
            kind=JournalRecordKind.TERMINAL,
            semantic_identity_sha256=_semantic_digest(terminal_payload),
            payload=terminal_payload,
        )
    if output_path.stat().st_size > MAXIMUM_ARTIFACT_BYTES:
        raise RuntimeError("exact-cubin journal exceeds byte ceiling")
    return OwnerExecution(terminal=terminal_payload, event_count=event_count)


def main() -> None:
    child_mode = os.environ.get(_CHILD_MODE_ENV)
    if child_mode is not None:
        challenge = os.environ.get(_CHILD_CHALLENGE_ENV)
        if not isinstance(challenge, str):
            raise ValueError("exact-cubin child challenge is absent")
        raise SystemExit(_worker_main(child_mode, challenge))
    if len(sys.argv) != 1:
        raise ValueError("exact-cubin diagnostic owner accepts no arguments")
    if _OUTPUT.exists():
        raise FileExistsError("exact-cubin diagnostic result is already consumed")
    if _RESERVED.exists():
        raise FileExistsError("reserved actual result must remain absent")
    execution = execute_owner_to_path(output_path=_OUTPUT)
    print(
        "legal-river exact-cubin diagnostic: "
        f"terminal={execution.terminal['terminal']} "
        f"passed={execution.terminal['passed']}"
    )
    if execution.terminal["terminal"] != "capture_complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()


__all__ = [
    "CAMPAIGN_SHA256",
    "CONFIG_RELATIVE_PATH",
    "LITERAL_WORKER_MODULE",
    "LoadedConfig",
    "OwnerExecution",
    "PROTOCOL_SHA256",
    "RESULT_RELATIVE_PATH",
    "canonical_lf_sha256",
    "dependency_hashes",
    "execute_owner_to_path",
    "load_public_config",
    "parse_config",
    "retained_artifact_facts",
    "run_child_process",
    "run_device_free_protocol_probe",
    "strict_git_metadata",
]
