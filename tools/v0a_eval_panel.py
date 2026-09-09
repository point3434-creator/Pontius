"""Slice A evaluation-panel entry: capacity and per-hand preflight in one supervised worker.

Plan contract (schema ``pontius-eval-panel-plan-v2``): the phases implemented here are
``capacity`` and ``preflight``. Both bind the runtime, the replayed prefix, the complete
hand universe, the pool seed and the resulting ordered permutation, and finite resource
limits. ``preflight`` also declares its coverage, development hands and controls. The
seed/index witness bank of the later agreement phase is not an input to these two phases
and is refused if present; that is a stated phase-specific reading, not a dropped field.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import tracemalloc
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pontius.execution import begin_run, child_context, CONTEXT_ENV, finish_run  # noqa: E402

PLAN_VERSION = "pontius-eval-panel-plan-v2"
PLAN_LIMIT = 262_144
MEMORY_LIMIT_MIB = 1 << 20
COMMON_KEYS = frozenset({"version", "phase", "runtime", "board", "stacks", "prefix",
                         "hand_universe_sha256", "hand_count", "pool_seed", "permutation",
                         "resource"})
PREFLIGHT_KEYS = COMMON_KEYS | {"coverage", "development_hands", "controls"}
COVERAGE = ("declared-full", "test-subset")
FULL_SAMPLE = dict(development_hands=4, controls=1)
STAGES = ("production", "production_warm", "reference_construction", "forced_check",
          "forced_bet", "best_response", "comparison")
HEX = "0123456789abcdef"


def refuse(condition, message):
    if not condition:
        raise ValueError(message)


def load_host():
    if "pontius_eval_panel_host" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "pontius_eval_panel_host", ROOT / "tools/v0a_table_host.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["pontius_eval_panel_host"] = module
        spec.loader.exec_module(module)
    return sys.modules["pontius_eval_panel_host"]


def parse_plan(raw):
    """Bounded, finite, constant-free JSON; nonfinite numbers and NaN tokens are refused."""
    refuse(type(raw) is bytes and 0 < len(raw) <= PLAN_LIMIT, "plan must be 1..262144 bytes")

    def constant(token):
        raise ValueError("plan contains a nonfinite JSON constant: " + token)

    plan = json.loads(raw.decode("utf-8"), parse_constant=constant)
    refuse(finite(plan), "plan contains a nonfinite number")
    return plan


def finite(value):
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite(item) for item in value.values())
    if isinstance(value, list):
        return all(finite(item) for item in value)
    return True


def validate_plan(plan):
    """Every mandatory input is checked against the replayed game; nothing is defaulted."""
    from pontius import eval_bridge as bridge
    refuse(isinstance(plan, dict) and plan.get("version") == PLAN_VERSION, "unknown plan version")
    phase = plan.get("phase")
    refuse(phase in ("capacity", "preflight"), "plan phase must be capacity or preflight")
    refuse(set(plan) == (PREFLIGHT_KEYS if phase == "preflight" else COMMON_KEYS),
           "plan has missing or unknown members for its phase")
    runtime = plan["runtime"]
    refuse(type(runtime) is dict and set(runtime) == {"python"}
           and runtime["python"] == ".".join(map(str, sys.version_info[:3])),
           "plan runtime.python must name the executing interpreter")
    board = bridge.board_cards(plan["board"])
    refuse(plan["stacks"] == bridge.DECLARED_STACK and type(plan["stacks"]) is int,
           "stacks must be the declared 4")
    refuse(plan["prefix"] == bridge.prefix_document(), "prefix must equal the declared prefix")
    universe = bridge.hero_hands(board)
    refuse(plan["hand_count"] == len(universe) and type(plan["hand_count"]) is int,
           "hand_count must equal the compatible hero universe")
    refuse(plan["hand_universe_sha256"] == bridge.hand_universe_digest(universe),
           "hand_universe_sha256 must equal the digest of the compatible hero universe")
    seed = plan["pool_seed"]
    refuse(type(seed) is str and len(seed) == 64 and all(digit in HEX for digit in seed),
           "pool_seed must be 64 lowercase hex digits")
    order = bridge.strength_blind_permutation(universe, seed)
    expected = [bridge.hand_name(hand) for hand in order]
    refuse(plan["permutation"] == expected,
           "permutation must list the seeded strength-blind order of the whole universe")
    resource = plan["resource"]
    refuse(type(resource) is dict and set(resource) == {"seconds", "memory_mib"},
           "resource must declare exactly seconds and memory_mib")
    seconds, memory = resource["seconds"], resource["memory_mib"]
    refuse(type(seconds) in (int, float) and math.isfinite(seconds) and seconds > 0,
           "resource.seconds must be a finite positive number")
    refuse(type(memory) is int and 1 <= memory <= MEMORY_LIMIT_MIB,
           "resource.memory_mib must be an exact integer within 1..1048576")
    if phase == "preflight":
        refuse(plan["coverage"] in COVERAGE, "coverage must be declared-full or test-subset")
        hands, controls = plan["development_hands"], plan["controls"]
        refuse(type(hands) is list and all(type(hand) is list and len(hand) == 2 for hand in hands),
               "development_hands must be two-card lists")
        refuse(type(controls) is list
               and all(type(control) is dict and set(control) == {"board", "hand"}
                       for control in controls),
               "controls must be {board, hand} objects")
        for control in controls:
            bridge.board_cards(control["board"])
        if plan["coverage"] == "declared-full":
            refuse(len(hands) >= FULL_SAMPLE["development_hands"]
                   and len(controls) >= FULL_SAMPLE["controls"],
                   "declared-full preflight requires the full development sample")
    return plan


def json_safe(value):
    """Nonfinite floats become tagged strings so the strict result writer never refuses."""
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite": repr(value)}
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def measure(function):
    """Elapsed, process CPU, and traced allocation peak; the platform peak is the job's."""
    tracemalloc.start()
    started, cpu = time.perf_counter(), time.process_time()
    try:
        value = function()
    finally:
        _, traced_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return value, dict(elapsed_seconds=time.perf_counter() - started,
                       cpu_seconds=time.process_time() - cpu, traced_peak_bytes=traced_peak)


def cache_state():
    # Read-only introspection of the unchanged ranker's cache, so cold and warm are labeled.
    from pontius import river
    return river._evaluate_seven_cached.cache_info()._asdict()


def preflight_hand(bridge, root, board, hero, label, emit):
    """Emit one stage event per completed measured stage; a kill keeps what completed."""
    identity = dict(hand=bridge.hand_name(hero), label=label,
                    board=[bridge.format_card(card) for card in board])

    def stage(name, function, payload):
        cache_before = cache_state()
        value, cost = measure(function)
        emit(dict(event="stage", stage=name, cost=cost, cache_before=cache_before,
                  cache_after=cache_state(), **identity, **payload(value)))
        return value

    production = stage("production", lambda: bridge.hand_totals(root, board, hero),
                       lambda value: dict(production=value))
    stage("production_warm", lambda: bridge.hand_totals(root, board, hero),
          lambda value: dict(repeat_matches=value == production))
    reference = stage("reference_construction",
                      lambda: bridge.build_reference(root, board, hero),
                      lambda value: dict(hero_key=value["hero_key"]))
    values = {}
    for name, action in (("forced_check", bridge.CHECK), ("forced_bet", reference["bet"])):
        values[str(action)] = stage(
            name, lambda action=action: bridge.forced_value(reference, action),
            lambda value: dict(value=value))
    response = stage("best_response", lambda: bridge.reference_best_response(reference),
                     lambda value: dict(value=value[0], selected=value[1]))
    comparison = stage("comparison", lambda: bridge.validate_reference(
        production, values, response[0], response[1], reference["hero_key"]),
        lambda value: dict(comparison=value))
    emit(dict(event="hand_completed", **identity))
    return comparison


def run_plan(plan, emit, deadline):
    """Execute one phase; stops at the first reference disagreement or exhausted budget."""
    from pontius import eval_bridge as bridge
    board = bridge.board_cards(plan["board"])
    root, initialization = measure(lambda: bridge.replay_root(stacks=plan["stacks"]))
    bridge.require_declared_root(root)
    emit(dict(event="ready", initialization_cost=initialization, python=sys.version,
              executable=sys.executable, work=dict(sealed_evaluator="not_instrumented")))
    if plan["phase"] == "capacity":
        permutation = bridge.strength_blind_permutation(bridge.hero_hands(board), plan["pool_seed"])
        report, cost = measure(lambda: bridge.capacity_probe(root, board, permutation))
        boundary = report.pop("boundary_encodings")
        emit(dict(event="observation", kind="capacity", cost=cost, probe=report,
                  permutation_sha256=bridge.permutation_digest(permutation),
                  boundary_base64={str(count): base64.b64encode(raw).decode("ascii")
                                   for count, raw in boundary.items()}))
        return
    units = [(board, bridge.parse_cards(*hand), "development")
             for hand in plan["development_hands"]]
    units += [(bridge.board_cards(control["board"]), bridge.parse_cards(*control["hand"]),
               "control") for control in plan["controls"]]
    for unit_board, hero, label in units:
        if time.perf_counter() >= deadline:
            emit(dict(event="failed", error="preflight budget exhausted before the next hand"))
            return
        unit_root = root if unit_board == board else bridge.replay_root(stacks=plan["stacks"])
        comparison = preflight_hand(bridge, unit_root, unit_board, hero, label, emit)
        if not comparison["passed"]:
            emit(dict(event="failed", error="reference disagreement: " + comparison["reason"]))
            return


def worker():
    def emit(event):
        sys.stdout.write(json.dumps(json_safe(event), separators=(",", ":")) + "\n")
        sys.stdout.flush()
    try:
        request = json.loads(sys.stdin.readline())
        plan = validate_plan(request["plan"])
        run_plan(plan, emit, time.perf_counter() + request["seconds"])
        emit(dict(event="completed"))
        return 0
    except Exception as error:  # the parent retains the cause; the worker never continues
        emit(dict(event="failed", error=f"{type(error).__name__}: {error}"))
        return 1


def supervise(plan, context, seconds, memory_bytes):
    """One worker from suspended launch inside a memory-limited job; cleanup never loses data.

    Mirrors the blueprint workload supervisor: assignment is tracked so an unassigned
    suspended process is killed rather than orphaned, every cleanup step runs under its
    own guard, the job is closed in a nested ``finally``, and events are drained during
    the loop and again after exit so completed stages survive any later failure.
    """
    host = load_host()
    job = host.Job(memory_limit=memory_bytes)
    events, errors, observations, hands = queue.Queue(), [], [], {}
    report = dict(status="failed", observations=observations, errors=errors,
                  peak_job_memory_bytes=0, cleanup_verified=False)
    started = time.perf_counter()
    process, assigned, threads = None, False, []

    def receive(stream):
        try:
            for line in stream:
                events.put(json.loads(line))
        except Exception as error:
            errors.append(f"worker output: {type(error).__name__}: {error}")

    def receive_errors(stream):
        for line in stream:
            errors.append(line.rstrip())

    def send(stream):
        try:
            stream.write(json.dumps(dict(plan=plan, seconds=seconds)) + "\n")
            stream.flush()
        except (BrokenPipeError, OSError):
            pass

    def drain():
        while not events.empty():
            event = events.get_nowait()
            kind = event.get("event")
            if kind == "observation":
                observations.append(event)
            elif kind in ("stage", "hand_completed"):
                key = (event["label"], tuple(event["board"]), event["hand"])
                record = hands.setdefault(key, dict(
                    hand=event["hand"], label=event["label"], board=event["board"],
                    kind="preflight", stages={}, complete=False))
                if kind == "stage":
                    record["stages"][event["stage"]] = {
                        name: value for name, value in event.items()
                        if name not in ("event", "stage", "hand", "label", "board")}
                else:
                    record["complete"] = True
            elif kind == "failed":
                errors.append(event["error"])
            elif kind == "ready":
                report["ready"] = event

    try:
        environment = dict(os.environ, **{CONTEXT_ENV: child_context(context)})
        process = subprocess.Popen(
            [sys.executable, "-B", "-P", str(Path(__file__)), "worker"], cwd=ROOT,
            env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8",
            creationflags=host.CREATE_SUSPENDED | subprocess.CREATE_NO_WINDOW)
        job.assign(process)
        assigned = True
        for function, stream in ((receive, process.stdout), (receive_errors, process.stderr),
                                 (send, process.stdin)):
            thread = threading.Thread(target=function, args=(stream,), daemon=True)
            thread.start()
            threads.append(thread)
        job.resume(process)
        while True:
            report["peak_job_memory_bytes"] = max(
                report["peak_job_memory_bytes"], job.peak_memory())
            drain()
            if process.poll() is not None and not threads[0].is_alive() and events.empty():
                report["status"] = (
                    "completed" if process.returncode == 0 and not errors else "failed")
                break
            if time.perf_counter() - started >= seconds:
                report["status"] = "budget_exhausted"
                break
            time.sleep(0.02)
    except KeyboardInterrupt:
        report["status"] = "interrupted"
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
                for stream in (process.stdin, process.stdout, process.stderr):
                    stream.close()
                drain()
                report["cleanup_verified"] = (
                    job.active() == 0 and process.poll() is not None
                    and not any(thread.is_alive() for thread in threads)
                    and all(stream.closed for stream in
                            (process.stdin, process.stdout, process.stderr)))
                report["worker_exit_code"] = process.returncode
        except Exception as error:
            report["cleanup_verified"] = False
            errors.append(f"cleanup: {type(error).__name__}: {error}")
            if process is not None and process.poll() is None:
                process.kill()
        finally:
            try:
                job.close()
            except Exception as error:
                errors.append(f"job close: {type(error).__name__}: {error}")
    for record in hands.values():
        record["missing_stages"] = [name for name in STAGES if name not in record["stages"]]
        observations.append(record)
    if report["status"] == "completed" and (errors or not report["cleanup_verified"]
                                            or any(not row.get("complete", True)
                                                   for row in observations)):
        report["status"] = "failed"
    report["worker_seconds"] = time.perf_counter() - started
    return report


def retain_boundaries(report, run_directory):
    """Write the measured boundary artifacts into the run directory and bind them."""
    for row in report["observations"]:
        if row.get("kind") != "capacity":
            continue
        retained = {}
        for count, encoded in row.pop("boundary_base64").items():
            raw = base64.b64decode(encoded)
            path = run_directory / f"capacity-boundary-{count}.blueprint.json"
            path.write_bytes(raw)
            retained[count] = dict(path=path.name, bytes=len(raw),
                                   sha256=hashlib.sha256(raw).hexdigest())
        row["boundary_artifacts"] = retained


def full_pool_estimate(observations, hero_count, coverage):
    """Production-only estimate from a declared-full sample; the reference is sample-only."""
    if coverage is None:
        return None
    if coverage != "declared-full":
        return dict(kind="not_estimated", reason=f"coverage is {coverage}")
    costs = [row["stages"]["production"]["cost"]["elapsed_seconds"] for row in observations
             if row.get("kind") == "preflight" and row["label"] == "development"
             and "production" in row["stages"]]
    if not costs:
        return None
    return dict(kind="estimate", hands=hero_count, sample=len(costs),
                production_seconds_min=min(costs) * hero_count,
                production_seconds_mean=sum(costs) / len(costs) * hero_count,
                production_seconds_max=max(costs) * hero_count,
                assumptions="first sampled hand is cold; later hands reuse cached villain "
                            "ranks; production only; the sealed reference is sample-only")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "worker"))
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--reviewed-commit")
    parser.add_argument("--development", action="store_true")
    args = parser.parse_args(argv)
    if args.mode == "worker":
        return worker()
    if not args.plan:
        parser.error("run requires --plan")
    started = time.perf_counter()
    context = begin_run(ROOT, reviewed_commit=args.reviewed_commit,
                        allow_working_tree=args.development)
    report = dict(status="failed", observations=[], errors=[])
    try:
        run_directory = ROOT / "experiments/results/runs" / uuid.uuid4().hex
        run_directory.mkdir(parents=True)
        context["output_directory"] = run_directory.relative_to(ROOT).as_posix()
        (run_directory / "runtimes.json").write_text(json.dumps([dict(
            python=sys.version, executable=sys.executable, source_commit=context["commit"],
            source_sha256=context["source_sha256"])]) + "\n", encoding="utf-8")
        plan_raw = args.plan.read_bytes()
        report["plan_sha256"] = hashlib.sha256(plan_raw).hexdigest()
        plan = validate_plan(parse_plan(plan_raw))
        report = dict(supervise(plan, context, plan["resource"]["seconds"],
                                plan["resource"]["memory_mib"] * 1024 * 1024),
                      plan_sha256=report["plan_sha256"])
        retain_boundaries(report, run_directory)
        from pontius.eval_bridge import HERO_COUNT
        report.update(phase=plan["phase"], coverage=plan.get("coverage"),
                      plan={key: value for key, value in plan.items() if key != "permutation"},
                      permutation_sha256=hashlib.sha256(
                          json.dumps(plan["permutation"]).encode()).hexdigest(),
                      full_pool_estimate=full_pool_estimate(
                          report["observations"], HERO_COUNT, plan.get("coverage")))
    except KeyboardInterrupt:
        report.update(status="interrupted", error="interrupted before completion")
    except Exception as error:
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
    finally:
        report = json_safe(report)
        report["summary"] = (f"{report.get('phase', 'plan')} {report['status']}; "
                             f"{len(report.get('observations', []))} observations")
        finish_run(context, "v0a_eval_panel run", report, time.perf_counter() - started)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
