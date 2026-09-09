"""Run an existing blueprint workload in one worker, with boundary-only provenance."""

from __future__ import annotations

import argparse
import cProfile
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pstats
import queue
import secrets
import subprocess
import sys
import threading
import time
import uuid
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pontius.execution import begin_run, child_context, CONTEXT_ENV, finish_run, git  # noqa: E402


def load_tool(name):
    path = ROOT / "tools" / ("v0a_" + name + ".py")
    module_name = "pontius_workload_" + name
    if module_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    return sys.modules[module_name]


def input_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"input outside population root or missing: {relative}")
    return path


def load_inputs(root, cells, expected_population_sha256):
    """Read and verify the selected retained inputs once, before worker launch."""
    population_raw = input_path(root, "population.json").read_bytes()
    population_digest = hashlib.sha256(population_raw).hexdigest()
    if population_digest != expected_population_sha256:
        raise ValueError("population manifest differs from retained plan")
    population = json.loads(population_raw)
    references = [population["selections"]]
    artifacts = {artifact["size"]: artifact for artifact in population["artifacts"]}
    for size in sorted({cell["size"] for cell in cells}):
        references.append(artifacts[size]["file"])
    sessions = {reference["path"]: reference for reference in population["sessions"]}
    for cell in cells:
        if cell["kind"] == "session":
            parameters = cell["parameters"]
            name = (
                f"sessions/d{parameters['deal']}-s{parameters['seat']}-l{parameters['lineup']}.json"
            )
            references.append(sessions[name])
    captured, identities = {}, {"population.json": population_digest}
    for reference in references:
        name = reference["path"]
        if name in captured:
            continue
        raw = input_path(root, name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != reference["sha256"] or len(raw) != reference["bytes"]:
            raise ValueError(f"retained input differs: {name}")
        identities[name] = digest
        # Only JSON selections need a retained in-memory copy. Timed artifact reads
        # deliberately still exercise the filesystem, without another provenance hash.
        captured[name] = raw if name == population["selections"]["path"] else None
    return population, json.loads(captured[population["selections"]["path"]]), identities


def emit(value):
    print(json.dumps(value, separators=(",", ":"), allow_nan=False), flush=True)


def session_observation(cell, population_root):
    session_tool = load_tool("table_session")
    parameters = cell["parameters"]
    session_path = (
        population_root
        / "sessions"
        / (f"d{parameters['deal']}-s{parameters['seat']}-l{parameters['lineup']}.json")
    )
    args = SimpleNamespace(
        session=str(session_path),
        blueprint=str(population_root / "artifacts" / f"{cell['size']}.json"),
        session_id=parameters["session_id"],
        strategy=parameters["strategy"],
        auto=True,
        format="json",
        development=False,
        reviewed_commit=None,
    )
    profiler = cProfile.Profile() if parameters.get("diagnostic") else None
    if profiler:
        profiler.enable()
    try:
        report = session_tool.Session(args, None).run()
    finally:
        if profiler:
            profiler.disable()
    result = {"session": report}
    if profiler:
        result["profile"] = [
            dict(
                file=key[0],
                line=key[1],
                function=key[2],
                primitive_calls=value[0],
                total_calls=value[1],
                self_seconds=value[2],
                cumulative_seconds=value[3],
            )
            for key, value in pstats.Stats(profiler).stats.items()
        ]
    if report["status"] != "completed":
        raise ValueError(f"session failed: {report['failure_reason']}")
    return result


def worker():
    request = json.loads(sys.stdin.readline())
    population_root = Path(request["population_root"])
    population = load_tool("blueprint_workload_population")
    measure = load_tool("blueprint_workload_measure")
    artifacts = {artifact["size"]: artifact for artifact in request["population"]["artifacts"]}
    emit({"event": "ready"})
    for cell in request["cells"]:
        nonce = secrets.token_hex(16)
        emit({"event": "grant_requested", "id": cell["id"], "nonce": nonce})
        grant = json.loads(sys.stdin.readline())
        if grant != {"id": cell["id"], "nonce": nonce, "granted": True}:
            raise ValueError("cell grant does not match request")
        started = time.perf_counter()
        emit({"event": "cell_started", "id": cell["id"]})
        try:
            if cell["kind"] == "session":
                observation = session_observation(cell, population_root)
            else:
                metadata = artifacts[cell["size"]]
                observation = measure.measure_cell(
                    cell,
                    dict(
                        artifact_path=population_root / metadata["file"]["path"],
                        artifact_metadata=metadata,
                        selections=request["selections"],
                        population=population,
                        clock=time.perf_counter_ns,
                        stage=lambda stage: emit({"event": "stage", "stage": stage}),
                    ),
                )
            emit(
                {
                    "event": "cell_completed",
                    "id": cell["id"],
                    "kind": cell["kind"],
                    "size": cell["size"],
                    "elapsed_seconds": time.perf_counter() - started,
                    "observation": observation,
                }
            )
        except Exception as error:
            emit(
                {
                    "event": "cell_failed",
                    "id": cell["id"],
                    "error": f"{type(error).__name__}: {error}",
                }
            )
            return 1
    return 0


def supervise(request, context, seconds, memory_bytes):
    """Own the persistent worker and its descendants from suspended launch to exit."""
    host = load_tool("table_host")
    job = host.Job(memory_limit=memory_bytes)
    events = queue.Queue()
    process = None
    assigned = False
    threads = []
    rows, errors = [], []
    started = time.perf_counter()
    report = dict(
        status="failed",
        cells=rows,
        worker_count=1,
        ready_seconds=None,
        peak_job_memory_bytes=0,
        errors=errors,
        cleanup_verified=False,
    )
    current = None
    grants = 0

    def remaining_seconds():
        remaining = seconds - (time.perf_counter() - started)
        if remaining <= 0:
            raise TimeoutError("run budget exhausted")
        return remaining

    def receive(stream):
        try:
            for line in stream:
                events.put(json.loads(line))
        except Exception as error:
            errors.append(f"worker output: {type(error).__name__}: {error}")

    def send(stream):
        try:
            stream.write(json.dumps(request, separators=(",", ":")) + "\n")
            stream.flush()
        except (BrokenPipeError, OSError):
            pass

    def receive_errors(stream):
        for line in stream:
            errors.append(line.rstrip())

    def drain_events():
        nonlocal current, grants
        while not events.empty():
            event = events.get_nowait()
            if event["event"] == "grant_requested":
                if grants >= len(request["cells"]):
                    raise ValueError("unexpected extra cell grant request")
                cell = request["cells"][grants]
                if event["id"] != cell["id"] or len(event["nonce"]) != 32:
                    raise ValueError("out-of-order or invalid cell grant request")
                observed_head = git(ROOT, "rev-parse", "--verify", "HEAD^{commit}",
                                    timeout=remaining_seconds()).decode().strip()
                if observed_head != context["head"]:
                    raise ValueError("HEAD changed during the run")
                names = [f"artifacts/{cell['size']}.json"]
                if cell["kind"] == "session":
                    parameters = cell["parameters"]
                    names.append(
                        f"sessions/d{parameters['deal']}-s{parameters['seat']}"
                        f"-l{parameters['lineup']}.json"
                    )
                for name in names:
                    remaining_seconds()
                    digest = hashlib.sha256()
                    with input_path(Path(request["population_root"]), name).open("rb") as stream:
                        while chunk := stream.read(1024 * 1024):
                            remaining_seconds()
                            digest.update(chunk)
                    if digest.hexdigest() != request["input_hashes"][name]:
                        raise ValueError(f"cell input changed: {name}")
                remaining_seconds()
                grant = {"id": cell["id"], "nonce": event["nonce"], "granted": True}
                process.stdin.write(json.dumps(grant) + "\n")
                process.stdin.flush()
                grants += 1
            elif event["event"] == "ready":
                report["ready_seconds"] = time.perf_counter() - started
            elif event["event"] == "cell_started":
                current = event["id"]
            elif event["event"] == "cell_completed":
                rows.append(event)
                current = None
            elif event["event"] == "cell_failed":
                errors.append(event["error"])
                current = event["id"]

    try:
        environment = dict(os.environ, **{CONTEXT_ENV: child_context(context)})
        process = subprocess.Popen(
            [sys.executable, "-B", "-P", str(Path(__file__)), "worker"],
            cwd=ROOT,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            creationflags=host.CREATE_SUSPENDED | subprocess.CREATE_NO_WINDOW,
        )
        job.assign(process)
        assigned = True
        for function, stream in (
            (receive, process.stdout),
            (receive_errors, process.stderr),
            (send, process.stdin),
        ):
            thread = threading.Thread(target=function, args=(stream,), daemon=True)
            thread.start()
            threads.append(thread)
        report["peak_job_memory_bytes"] = job.peak_memory()
        job.resume(process)
        while True:
            report["peak_job_memory_bytes"] = max(
                report["peak_job_memory_bytes"], job.peak_memory()
            )
            drain_events()
            if process.poll() is not None and not threads[0].is_alive() and events.empty():
                report["status"] = (
                    "completed" if process.returncode == 0 and not errors else "failed"
                )
                break
            if time.perf_counter() - started >= seconds:
                report["status"] = "budget_exhausted"
                break
            time.sleep(0.02)
    except KeyboardInterrupt:
        report["status"] = "interrupted"
    except (TimeoutError, subprocess.TimeoutExpired):
        report["status"] = "budget_exhausted"
    except Exception as error:
        errors.append(f"{type(error).__name__}: {error}")
    finally:
        try:
            if process is not None:
                if assigned and job.active():
                    job.terminate()
                elif process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
                for thread in threads:
                    thread.join(timeout=10)
                streams_closed = False
                if any(thread.is_alive() for thread in threads):
                    errors.append("cleanup: pipe users did not stop; streams left open")
                else:
                    streams_closed = True
                    for stream in (process.stdin, process.stdout, process.stderr):
                        try:
                            stream.close()
                        except Exception as error:
                            streams_closed = False
                            errors.append(f"cleanup: {type(error).__name__}: {error}")
                    streams_closed = streams_closed and all(
                        stream.closed for stream in (process.stdin, process.stdout, process.stderr)
                    )
                while not events.empty():
                    event = events.get_nowait()
                    if event["event"] == "cell_completed":
                        rows.append(event)
                        current = None
                    elif event["event"] in ("cell_started", "cell_failed"):
                        current = event["id"]
                report["cleanup_verified"] = streams_closed and job.active() == 0 and not any(
                    thread.is_alive() for thread in threads
                )
                report["worker_exit_code"] = process.returncode
        except Exception as error:
            report["cleanup_verified"] = False
            errors.append(f"cleanup: {type(error).__name__}: {error}")
            if process is not None and process.poll() is None:
                process.kill()
                process.wait(timeout=10)
        finally:
            job.close()
    report.update(
        grants=grants,
        worker_seconds=time.perf_counter() - started,
        completed=len(rows),
        planned=len(request["cells"]),
        interrupted_cell=current,
        unattempted=max(0, len(request["cells"]) - len(rows) - int(current is not None)),
    )
    if not report["cleanup_verified"] or (report["status"] == "completed" and errors):
        report["status"] = "failed"
    if report["status"] == "completed" and len(rows) != len(request["cells"]):
        report["status"] = "failed"
        errors.append("worker exited without completing the selected cells")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "read", "worker"))
    parser.add_argument("--population-root", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--reviewed-commit")
    parser.add_argument("--development", action="store_true")
    parser.add_argument("--kinds", nargs="+")
    parser.add_argument("--sizes", nargs="+", type=int)
    parser.add_argument("--cells", type=int)
    parser.add_argument("--seconds", type=float, default=3600)
    parser.add_argument("--memory-mib", type=int, default=3072)
    args = parser.parse_args(argv)
    if args.mode == "worker":
        return worker()
    if args.mode == "read":
        if not args.result:
            parser.error("read requires --result (a result JSON or a legacy run directory)")
        report = (
            load_tool("blueprint_workload_report").read_run(args.result)
            if args.result.is_dir()
            else json.loads(args.result.read_bytes())
        )
        emit(report)
        return 0
    if not args.population_root:
        parser.error("run requires --population-root containing population.json and plan.json")
    if args.seconds <= 0 or args.memory_mib <= 0 or (args.cells is not None and args.cells <= 0):
        parser.error("time, memory and cell limits must be positive")
    started = time.perf_counter()
    context = begin_run(
        ROOT, reviewed_commit=args.reviewed_commit, allow_working_tree=args.development
    )
    run_directory = ROOT / "experiments/results/runs" / uuid.uuid4().hex
    run_directory.mkdir(parents=True)
    context["output_directory"] = run_directory.relative_to(ROOT).as_posix()
    runtime_record = dict(
        python=sys.version,
        executable=sys.executable,
        source_commit=context["commit"],
        source_sha256=context["source_sha256"],
        source_verified=context["verified"],
    )
    (run_directory / "runtimes.json").write_text(
        json.dumps([runtime_record]) + "\n", encoding="utf-8"
    )
    report = dict(status="failed")
    try:
        population_root = args.population_root.resolve()
        plan_raw = input_path(population_root, "plan.json").read_bytes()
        plan = json.loads(plan_raw)
        runtime = f"{sys.version_info.major}.{sys.version_info.minor}"
        cells = [
            cell
            for cell in plan["cells"]
            if cell["runtime"] == runtime
            and (not args.kinds or cell["kind"] in args.kinds)
            and (not args.sizes or cell["size"] in args.sizes)
        ]
        cells = cells[: args.cells]
        if not cells:
            raise ValueError("no matching cells for this runtime and selection")
        population, selections, identities = load_inputs(
            population_root, cells, plan["population_sha256"]
        )
        request = dict(
            population_root=str(population_root),
            population=population,
            input_hashes=identities,
            selections=selections,
            cells=cells,
        )
        plan_digest = hashlib.sha256(plan_raw).hexdigest()
        preparation_seconds = time.perf_counter() - started
        remaining = args.seconds - preparation_seconds
        if remaining <= 0:
            report = dict(
                status="budget_exhausted",
                cells=[],
                completed=0,
                planned=len(cells),
                unattempted=len(cells),
                worker_count=0,
            )
        else:
            report = supervise(request, context, remaining, args.memory_mib * 1024 * 1024)
        report.update(
            runtime=runtime,
            source_verified=context["verified"],
            source_sha256=context["source_sha256"],
            input_hashes=identities,
            plan_sha256=plan_digest,
            preparation_seconds=preparation_seconds,
            selected_cells=[cell["id"] for cell in cells],
            memory_scope=(
                "persistent worker job peak from suspended launch; cumulative across cells"
            ),
        )
    except Exception as error:
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
    report["summary"] = (
        f"{report.get('completed', 0)}/{report.get('planned', 0)} cells completed; "
        f"{report.get('status')}; one worker per runtime"
    )
    finish_run(context, "v0a_blueprint_workload run", report, time.perf_counter() - started)
    emit(report)
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
