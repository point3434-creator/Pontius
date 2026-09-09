"""Slice A evaluation-panel entry: capacity and per-hand preflight in one supervised worker."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import tracemalloc
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pontius.execution import begin_run, child_context, CONTEXT_ENV, finish_run  # noqa: E402

PLAN_VERSION = "pontius-eval-panel-plan-v1"
PHASES = ("capacity", "preflight")
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


def validate_plan(plan):
    """Every mandatory input is checked; a missing one refuses rather than defaulting."""
    from pontius.eval_bridge import board_cards
    refuse(isinstance(plan, dict) and plan.get("version") == PLAN_VERSION, "unknown plan version")
    refuse(plan.get("phase") in PHASES, "plan phase must be capacity or preflight")
    board_cards(plan.get("board", ()))
    stacks = plan.get("stacks")
    refuse(type(stacks) is int and stacks >= 2, "stacks must be an integer >= 2")
    seed = plan.get("pool_seed")
    refuse(type(seed) is str and len(seed) == 64 and all(digit in HEX for digit in seed),
           "pool_seed must be 64 lowercase hex digits")
    resource = plan.get("resource")
    refuse(type(resource) is dict and resource.get("seconds", 0) > 0
           and resource.get("memory_mib", 0) > 0,
           "resource must declare positive seconds and memory_mib")
    if plan["phase"] == "preflight":
        hands = plan.get("development_hands")
        refuse(type(hands) is list and hands
               and all(type(hand) is list and len(hand) == 2 for hand in hands),
               "preflight requires development_hands as two-card lists")
        controls = plan.get("controls")
        refuse(type(controls) is list
               and all(set(control) == {"board", "hand"} for control in controls),
               "preflight requires controls as {board, hand} objects")
        for control in controls:
            board_cards(control["board"])
    return plan


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


def preflight_hand(bridge, root, board, hero, label):
    """Production first, then the sealed reference in its separately costed parts."""
    observation = dict(hand=bridge.hand_name(hero), label=label, cache_before=cache_state(),
                       board=[bridge.format_card(card) for card in board])
    production, observation["production_cost"] = measure(
        lambda: bridge.hand_totals(root, board, hero))
    observation.update(production=production, cache_after_production=cache_state())
    reference, observation["reference_construction_cost"] = measure(
        lambda: bridge.build_reference(root, board, hero))
    values, observation["forced_values_cost"] = measure(lambda: bridge.forced_values(reference))
    (response_value, response_map), observation["best_response_cost"] = measure(
        lambda: bridge.reference_best_response(reference))
    observation["forced_values"] = values
    observation["comparison"], observation["comparison_cost"] = measure(
        lambda: bridge.validate_reference(
            production, values, response_value, response_map, reference["hero_key"]))
    return observation


def run_plan(plan, emit, deadline):
    """Execute one phase, emitting an observation per unit; stops at the first failure."""
    from pontius import eval_bridge as bridge
    board = bridge.board_cards(plan["board"])
    root, initialization = measure(lambda: bridge.replay_root(stacks=plan["stacks"]))
    emit(dict(event="ready", initialization_cost=initialization, python=sys.version,
              executable=sys.executable))
    if plan["phase"] == "capacity":
        permutation = bridge.strength_blind_permutation(
            bridge.hero_hands(board), plan["pool_seed"])
        report, cost = measure(lambda: bridge.capacity_probe(root, board, permutation))
        emit(dict(event="observation", kind="capacity", cost=cost, probe=report,
                  permutation_sha256=bridge.permutation_digest(permutation),
                  permutation=[bridge.hand_name(hand) for hand in permutation]))
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
        observation = preflight_hand(bridge, unit_root, unit_board, hero, label)
        emit(dict(event="observation", kind="preflight", **observation))
        if not observation["comparison"]["passed"]:
            reason = observation["comparison"]["reason"]
            emit(dict(event="failed", error="reference disagreement: " + reason))
            return


def worker():
    def emit(event):
        sys.stdout.write(json.dumps(event, separators=(",", ":")) + "\n")
        sys.stdout.flush()
    request = json.loads(sys.stdin.readline())
    try:
        plan = validate_plan(request["plan"])
        run_plan(plan, emit, time.perf_counter() + request["seconds"])
        emit(dict(event="completed"))
        return 0
    except Exception as error:  # the parent retains the cause; the worker never continues
        emit(dict(event="failed", error=f"{type(error).__name__}: {error}"))
        return 1


def supervise(plan, context, seconds, memory_bytes):
    """One worker from suspended launch inside a memory-limited job, until exit or budget."""
    host = load_host()
    job = host.Job(memory_limit=memory_bytes)
    events, errors, observations = [], [], []
    report = dict(status="failed", observations=observations, errors=errors,
                  peak_job_memory_bytes=0)
    started = time.perf_counter()
    process, readers = None, []

    def receive(stream):
        for line in stream:
            try:
                events.append(json.loads(line))
            except ValueError as error:
                errors.append(f"worker output: {error}")

    try:
        environment = dict(os.environ, **{CONTEXT_ENV: child_context(context)})
        process = subprocess.Popen(
            [sys.executable, "-B", "-P", str(Path(__file__)), "worker"], cwd=ROOT,
            env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8",
            creationflags=host.CREATE_SUSPENDED | subprocess.CREATE_NO_WINDOW)
        job.assign(process)
        readers = [threading.Thread(target=receive, args=(process.stdout,), daemon=True),
                   threading.Thread(target=lambda: errors.extend(
                       line.rstrip() for line in process.stderr), daemon=True)]
        for reader in readers:
            reader.start()
        job.resume(process)
        process.stdin.write(json.dumps(dict(plan=plan, seconds=seconds)) + "\n")
        process.stdin.flush()
        while process.poll() is None or readers[0].is_alive():
            report["peak_job_memory_bytes"] = max(
                report["peak_job_memory_bytes"], job.peak_memory())
            if time.perf_counter() - started >= seconds:
                report["status"] = "budget_exhausted"
                break
            time.sleep(0.05)
        else:
            report["status"] = "completed" if process.returncode == 0 else "failed"
    except KeyboardInterrupt:
        report["status"] = "interrupted"
    except Exception as error:
        errors.append(f"{type(error).__name__}: {error}")
    finally:
        if process is not None:
            if job.active():
                job.terminate()
            process.wait(timeout=10)
            for reader in readers:
                reader.join(timeout=10)
            report["cleanup_verified"] = job.active() == 0
            report["worker_exit_code"] = process.returncode
        job.close()
    for event in events:
        if event["event"] == "observation":
            observations.append(event)
        elif event["event"] == "failed":
            errors.append(event["error"])
        elif event["event"] == "ready":
            report["ready"] = event
    if report["status"] == "completed" and (errors or not report.get("cleanup_verified")):
        report["status"] = "failed"
    report["worker_seconds"] = time.perf_counter() - started
    return report


def full_pool_estimate(observations, hero_count):
    """A labeled estimate from the development sample; the reference is sample-only."""
    costs = [row["production_cost"]["elapsed_seconds"] for row in observations
             if row.get("kind") == "preflight" and row["label"] == "development"]
    if not costs:
        return None
    return dict(kind="estimate", hands=hero_count, sample=len(costs),
                production_seconds_min=min(costs) * hero_count,
                production_seconds_mean=sum(costs) / len(costs) * hero_count,
                production_seconds_max=max(costs) * hero_count,
                note="production only; the sealed reference is sample-only and excluded")


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
    run_directory = ROOT / "experiments/results/runs" / uuid.uuid4().hex
    run_directory.mkdir(parents=True)
    context["output_directory"] = run_directory.relative_to(ROOT).as_posix()
    report = dict(status="failed")
    try:
        plan_raw = args.plan.read_bytes()
        plan = validate_plan(json.loads(plan_raw))
        (run_directory / "runtimes.json").write_text(json.dumps([dict(
            python=sys.version, executable=sys.executable, source_commit=context["commit"],
            source_sha256=context["source_sha256"])]) + "\n", encoding="utf-8")
        report = supervise(plan, context, plan["resource"]["seconds"],
                           plan["resource"]["memory_mib"] * 1024 * 1024)
        from pontius.eval_bridge import HERO_COUNT
        report.update(phase=plan["phase"], plan=plan,
                      plan_sha256=hashlib.sha256(plan_raw).hexdigest(),
                      full_pool_estimate=full_pool_estimate(report["observations"], HERO_COUNT))
    except Exception as error:
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
    report["summary"] = (f"{report.get('phase', 'plan')} {report['status']}; "
                         f"{len(report.get('observations', []))} observations")
    finish_run(context, "v0a_eval_panel run", report, time.perf_counter() - started)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
