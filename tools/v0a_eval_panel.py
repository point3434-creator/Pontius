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
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import queue
import signal
import subprocess
import sys
import threading
import time
import tracemalloc
import uuid
from typing import NamedTuple

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
DEVELOPMENT_BOARD = ["2c", "7d", "9h", "Js", "Qc"]
DEVELOPMENT_HANDS = (["As", "Ad"], ["Kh", "Kd"], ["Td", "8d"], ["3c", "4d"])
ROYAL_CONTROL = dict(board=["Ts", "Js", "Qs", "Ks", "As"], hand=["2c", "3d"])
STAGES = ("production", "production_warm", "reference_construction", "forced_check",
          "forced_bet", "best_response", "comparison")
HEX = "0123456789abcdef"


class ScheduledHand(NamedTuple):
    role: str
    board: tuple
    hand: tuple

    @property
    def record_key(self):
        from pontius import eval_bridge as bridge
        return (self.role, tuple(bridge.format_card(card) for card in self.board),
                bridge.hand_name(self.hand))


class AdmittedPlan(NamedTuple):
    """Immutable wire snapshot and role-bearing schedule shared by all local consumers."""
    wire: str
    schedule: tuple

    @property
    def document(self):
        return json.loads(self.wire)


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
    if isinstance(plan, AdmittedPlan):
        return plan
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
    sample = ()
    if phase == "preflight":
        refuse(plan["coverage"] in COVERAGE, "coverage must be declared-full or test-subset")
        hands, controls = plan["development_hands"], plan["controls"]
        refuse(type(hands) is list and type(controls) is list
               and all(type(control) is dict and set(control) == {"board", "hand"}
                       for control in controls),
               "development_hands must be a list and controls {board, hand} objects")
        sample = tuple(ScheduledHand("development", *sample_identity(bridge, plan["board"], hand))
                       for hand in hands)
        sample += tuple(ScheduledHand("control", *sample_identity(
            bridge, control["board"], control["hand"])) for control in controls)
        refuse(len({(unit.board, unit.hand) for unit in sample}) == len(sample),
               "development_hands and controls must be distinct")
        if plan["coverage"] == "declared-full":
            declared = declared_sample(bridge)
            expected = [ScheduledHand("development", *identity) for identity in declared[:-1]]
            expected += [ScheduledHand("control", *declared[-1])]
            refuse(plan["board"] == DEVELOPMENT_BOARD and set(sample) == set(expected),
                   "declared-full preflight must sample exactly the declared board, the four "
                   "declared hands and the royal control")
    return AdmittedPlan(json.dumps(plan, separators=(",", ":")), sample)


def sample_identity(bridge, board_names, hand_names):
    """(board, hand) as card tuples; the hand must lie in the board's compatible universe."""
    board = bridge.board_cards(board_names)
    refuse(type(hand_names) is list and len(hand_names) == 2
           and all(type(name) is str for name in hand_names), "a hand is two card strings")
    hand = tuple(sorted(bridge.parse_cards(*hand_names)))
    refuse(hand in bridge.hero_hands(board), "a hand must be two distinct cards off its board")
    return board, hand


def declared_sample(bridge):
    """The exact declared-full sample: the four development hands and the royal control."""
    sample = [sample_identity(bridge, DEVELOPMENT_BOARD, hand) for hand in DEVELOPMENT_HANDS]
    return sample + [sample_identity(bridge, ROYAL_CONTROL["board"], ROYAL_CONTROL["hand"])]


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
    admitted = validate_plan(plan)
    plan = admitted.document
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
    for label, unit_board, hero in admitted.schedule:
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


@contextmanager
def defer_interrupts(report):
    """Record console interrupts without unwinding between owned release operations."""
    previous = None
    if threading.current_thread() is threading.main_thread():
        previous = signal.getsignal(signal.SIGINT)

        def interrupted(signum, frame):
            report["status"] = "interrupted"
            report["cleanup"]["console interrupt"] = "interrupted"

        signal.signal(signal.SIGINT, interrupted)
    try:
        yield
    finally:
        if previous is not None:
            signal.signal(signal.SIGINT, previous)


def close_stream(stream, timeout):
    """One closer owns the stream even if another I/O thread holds its lock past cleanup."""
    done, failures = threading.Event(), []

    def close():
        try:
            stream.close()
        except BaseException as error:
            failures.append(error)
        finally:
            done.set()

    threading.Thread(target=close, daemon=True).start()
    if not done.wait(timeout):
        raise TimeoutError("stream close remains pending in its owning thread")
    if failures:
        raise failures[0]


def supervise(plan, context, seconds, memory_bytes, report=None):
    """One worker from suspended launch inside a memory-limited job; cleanup never loses data.

    Assignment is tracked so an unassigned suspended process is killed rather than
    orphaned. Every cleanup release is its own bounded attempt (``attempt`` below): a
    failure or an interrupt in one is recorded under ``report["cleanup"]`` and never
    prevents the next, and the job is closed last. The caller may own ``report``, so
    drained observations are caller-owned from first receipt, even if this function unwinds.
    """
    admitted = validate_plan(plan)
    host = load_host()
    events = queue.Queue()
    if report is None:
        report = dict(status="failed", observations=[], errors=[])
    observations, errors = report["observations"], report["errors"]
    report.update(peak_job_memory_bytes=0, cleanup_verified=False, cleanup={},
                  resource_state_verified=False)
    started = time.perf_counter()
    job, process, assigned, threads = None, None, False, []

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
            stream.write(json.dumps(dict(plan=admitted.document, seconds=seconds)) + "\n")
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
                record = next((row for row in observations if row.get("kind") == "preflight"
                               and (row["label"], tuple(row["board"]), row["hand"]) == key), None)
                if record is None:
                    observations.append(dict(
                        hand=event["hand"], label=event["label"], board=event["board"],
                        kind="preflight", stages={}, complete=False, missing_stages=list(STAGES)))
                    record = observations[-1]
                if record["complete"]:
                    errors.append(f"repeated observation of {event['label']} {event['hand']}")
                elif kind == "stage":
                    record["stages"][event["stage"]] = {
                        name: value for name, value in event.items()
                        if name not in ("event", "stage", "hand", "label", "board")}
                    record["missing_stages"] = [name for name in STAGES
                                                if name not in record["stages"]]
                else:
                    record["complete"] = True
            elif kind == "failed":
                errors.append(event["error"])
            elif kind == "ready":
                report["ready"] = event

    with defer_interrupts(report):
        try:
            job = host.Job(memory_limit=memory_bytes)
            if report["status"] == "interrupted":
                raise KeyboardInterrupt
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
                if report["status"] == "interrupted":
                    break
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
            def attempt(name, function):
                try:
                    function()
                    report["cleanup"][name] = "ok"
                except KeyboardInterrupt:
                    report["cleanup"][name] = "interrupted"
                    report["status"] = "interrupted"
                except Exception as error:
                    report["cleanup"][name] = f"{type(error).__name__}: {error}"
                    errors.append(f"cleanup {name}: {report['cleanup'][name]}")

            def verify():
                report["worker_exit_code"] = process.poll()
                report["resource_state_verified"] = (
                    job.active() == 0 and report["worker_exit_code"] is not None
                    and not any(thread.is_alive() for thread in threads)
                    and all(stream.closed for stream in streams))

            cleanup_deadline = time.perf_counter() + 10

            def join(thread):
                thread.join(timeout=max(0, cleanup_deadline - time.perf_counter()))
                if thread.is_alive():
                    raise TimeoutError("I/O thread did not exit before the cleanup deadline")

            if process is not None:
                streams = (process.stdin, process.stdout, process.stderr)
                attempt("terminate job", lambda: (
                    job.terminate() if assigned and job.active() else None))
                attempt("kill process", lambda: process.kill() if process.poll() is None else None)
                attempt("wait", lambda: process.wait(timeout=10))
                for index, thread in enumerate(threads):
                    attempt(f"join thread {index}", lambda thread=thread: join(thread))
                for name, stream in zip(("stdin", "stdout", "stderr"), streams):
                    attempt("close " + name, lambda stream=stream: close_stream(
                        stream, max(0, cleanup_deadline - time.perf_counter())))
                attempt("drain", drain)
                attempt("verify", verify)
            if job is not None:
                attempt("close job", job.close)
    # The normal handler must be restored before finalizing this certificate. A late
    # console interrupt then unwinds instead of silently changing its inputs mid-store.
    report["cleanup_verified"] = (
        report["resource_state_verified"]
        and all(value == "ok" for value in report["cleanup"].values()))
    if admitted.document["phase"] == "preflight":
        report["sample_complete"] = complete_sample(observations, admitted) is not None
        if report["status"] == "completed" and not report["sample_complete"]:
            errors.append("the admitted role-bearing sample is incomplete or disagrees")
    if report["status"] == "completed" and (errors or not report["cleanup_verified"]
                                            or any(not row.get("complete", True)
                                                   for row in observations)):
        report["status"] = "failed"
    report["worker_seconds"] = time.perf_counter() - started
    return report


def retain_boundaries(report, run_directory):
    """Write and bind each boundary artifact; an encoding leaves the observation only after
    its artifact is renamed into place, so a failed write loses nothing already measured."""
    for row in report["observations"]:
        if row.get("kind") != "capacity":
            continue
        pending = row.get("boundary_base64", {})
        retained = row.setdefault("boundary_artifacts", {})
        publications = row.setdefault("boundary_publications", {})
        try:
            for count in sorted(pending):
                raw = base64.b64decode(pending[count])
                path = run_directory / f"capacity-boundary-{count}.blueprint.json"
                staging = path.with_name(path.name + ".partial")
                identity = dict(path=path.name, bytes=len(raw),
                                sha256=hashlib.sha256(raw).hexdigest())
                publication = publications.setdefault(count, dict(**identity, state="pending"))
                try:
                    staging.write_bytes(raw)
                    publication["state"] = "publishing"
                    os.replace(staging, path)
                finally:
                    # A rename may have succeeded before interruption was delivered. The
                    # intended identity was registered first; reconcile the actual file.
                    if path.is_file():
                        observed = path.read_bytes()
                        refuse(observed == raw, "published boundary differs from measured bytes")
                        retained[count] = identity
                        publication["state"] = "bound"
                        del pending[count]
                    else:
                        publication["state"] = "pending"
        finally:
            if pending:
                row["boundary_retention"] = ("incomplete; recoverable encodings remain in "
                                             "boundary_base64")
            else:
                row.pop("boundary_base64", None)
                row["boundary_retention"] = "complete"


def complete_sample(observations, admitted):
    """Reconcile actual completed records against the same schedule the worker executes."""
    required = {unit.record_key for unit in admitted.schedule}
    records = {}
    for row in observations:
        if row.get("kind") != "preflight":
            continue
        key = row["label"], tuple(row["board"]), row["hand"]
        stages = row["stages"]
        if (key not in required or key in records or row["complete"] is not True
                or set(stages) != set(STAGES)
                or stages["comparison"]["comparison"]["passed"] is not True):
            return None
        records[key] = row
    return records if set(records) == required else None


def full_pool_estimate(observations, hero_count, admitted):
    """Production-only estimate from a declared-full sample; the reference is sample-only."""
    coverage = admitted.document.get("coverage")
    if coverage is None:
        return None
    if coverage != "declared-full":
        return dict(kind="not_estimated", reason=f"coverage is {coverage}")
    complete = complete_sample(observations, admitted)
    if complete is None:
        return dict(kind="not_estimated", reason="admitted sample incomplete or disagrees")
    costs = [complete[unit.record_key]["stages"]["production"]["cost"]["elapsed_seconds"]
             for unit in admitted.schedule if unit.role == "development"]
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
        admitted = validate_plan(parse_plan(plan_raw))
        plan = admitted.document
        supervise(admitted, context, plan["resource"]["seconds"],
                  plan["resource"]["memory_mib"] * 1024 * 1024, report)
        retain_boundaries(report, run_directory)
        from pontius.eval_bridge import HERO_COUNT
        report.update(phase=plan["phase"], coverage=plan.get("coverage"),
                      plan={key: value for key, value in plan.items() if key != "permutation"},
                      permutation_sha256=hashlib.sha256(
                          json.dumps(plan["permutation"]).encode()).hexdigest(),
                      full_pool_estimate=full_pool_estimate(
                          report["observations"], HERO_COUNT, admitted))
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
