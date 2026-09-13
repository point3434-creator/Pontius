"""Bounded native six-max training, resume profiling, and policy smoke check."""

from __future__ import annotations

import argparse
from collections import Counter
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time
import traceback
import uuid

from pontius.execution import begin_run, finish_run

ROOT = Path(__file__).resolve().parents[1]
PROJECT = Path("D:/Projects/pluribus-lite")
SEED = 2026090807


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def process_tree_memory(root_pid):
    """Sample descendants from launch; working sets may double-count shared pages."""
    class ProcessEntry(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("usage", wintypes.DWORD),
                    ("pid", wintypes.DWORD), ("heap", ctypes.c_size_t),
                    ("module", wintypes.DWORD), ("threads", wintypes.DWORD),
                    ("parent", wintypes.DWORD), ("priority", wintypes.LONG),
                    ("flags", wintypes.DWORD), ("exe", wintypes.WCHAR * 260)]

    class MemoryCounters(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                "peak_working_set", "working_set", "peak_paged", "paged",
                "peak_nonpaged", "nonpaged", "commit", "peak_commit", "private")]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32NextW.argtypes = kernel.Process32FirstW.argtypes
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE,
                                         ctypes.POINTER(MemoryCounters), wintypes.DWORD]
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    entry = ProcessEntry()
    entry.size = ctypes.sizeof(entry)
    parents = {}
    try:
        present = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while present:
            parents[entry.pid] = entry.parent
            present = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    selected = {root_pid}
    while True:
        extended = selected | {pid for pid, parent in parents.items() if parent in selected}
        if extended == selected:
            break
        selected = extended
    samples = []
    for pid in sorted(selected):
        handle = kernel.OpenProcess(0x410, False, pid)
        if not handle:
            continue
        try:
            counters = MemoryCounters()
            counters.size = ctypes.sizeof(counters)
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.size):
                raise ctypes.WinError(ctypes.get_last_error())
            samples.append(dict(pid=pid, working_set=counters.working_set,
                                private=counters.private, peak_commit=counters.peak_commit))
        finally:
            kernel.CloseHandle(handle)
    return samples


def supervise(command, directory, label, seconds, stop_directory):
    started = time.perf_counter()
    samples = []
    stop_reason = None
    with (directory / f"{label}.log").open("w", encoding="utf-8") as output:
        process = subprocess.Popen(command, cwd=PROJECT, stdout=output,
                                   stderr=subprocess.STDOUT, env=os.environ.copy())
        try:
            while process.poll() is None:
                elapsed = time.perf_counter() - started
                memory = process_tree_memory(process.pid)
                samples.append(dict(seconds=elapsed, processes=memory))
                private = sum(item["private"] for item in memory)
                if private > 16 * 2**30 or elapsed > seconds:
                    stop_reason = "private_memory_limit" if private > 16 * 2**30 else "watchdog"
                    (stop_directory / "STOP").write_text(stop_reason, encoding="ascii")
                if private > 20 * 2**30 or elapsed > seconds + 60:
                    raise TimeoutError(f"{label} exceeded bounded resource limit")
                time.sleep(2)
        finally:
            if process.poll() is None:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, check=False)
                process.wait(timeout=15)
            write_json(directory / f"{label}-memory.json", samples)
    result = dict(command=command, exit_code=process.returncode,
                  seconds=time.perf_counter() - started, stop_reason=stop_reason,
                  peak_sampled_private=0 if not samples else max(
                      sum(item["private"] for item in sample["processes"]) for sample in samples),
                  peak_sampled_working_set=max((sum(item["working_set"] for item in sample[
                      "processes"]) for sample in samples), default=0))
    if process.returncode or stop_reason:
        raise RuntimeError(f"{label} failed: {result}")
    return result


def probe(directory):
    import cProfile
    import pstats
    import numpy as np
    from pluribus_lite.abstraction import BucketAssigner
    from pluribus_lite.engine import NLHE
    from pluribus_lite.mccfr import BlueprintPolicy, MCCFRTrainer

    assigner = BucketAssigner(str(directory / "buckets"))
    checkpoint = directory / "training/blueprint_ckpt"
    trainer = MCCFRTrainer(assigner, num_players=6, stack=200, sb=1, bb=2,
                           seed=SEED, max_infosets=8_000_000, min_visits=2,
                           discount_every=10_000, discount_until=2_000_000, stream_base=0)
    started = time.perf_counter()
    trainer.load(str(checkpoint), require_fingerprint=True)
    result = dict(load_seconds=time.perf_counter() - started,
                  iteration_before=trainer.iteration, rows_before=trainer.table.rows)
    profiler = cProfile.Profile()
    started = time.perf_counter()
    profiler.enable()
    for _ in range(200):
        trainer.run_iteration()
    profiler.disable()
    result["profiled_training_seconds"] = time.perf_counter() - started
    profiler.dump_stats(str(directory / "resume.prof"))
    with (directory / "profile.txt").open("w", encoding="utf-8") as output:
        pstats.Stats(profiler, stream=output).strip_dirs().sort_stats("cumulative").print_stats(45)
        pstats.Stats(profiler, stream=output).strip_dirs().sort_stats("tottime").print_stats(30)
    result.update(iteration_after=trainer.iteration, rows_after=trainer.table.rows)
    if trainer.iteration != result["iteration_before"] + 200:
        raise ValueError("Resume did not advance exactly 200 iterations")
    resumed = directory / "resumed-checkpoint"
    started = time.perf_counter()
    trainer.save(str(resumed))
    result["save_seconds"] = time.perf_counter() - started
    generator = random.Random(SEED + 1)
    counts = Counter()
    decisions = []
    with BlueprintPolicy(trainer.nodes, assigner) as live:
        with BlueprintPolicy(str(resumed), assigner, loader="full") as loaded:
            if loaded.meta_players != 6 or loaded.ckpt_iteration != trainer.iteration:
                raise ValueError("Saved policy metadata does not match resumed trainer")
            for hand in range(48):
                game = NLHE(6, stack=200, sb=1, bb=2, rng=generator)
                game.reset()
                steps = 0
                while not game.is_over():
                    legal = game.legal_actions()
                    expected, status = live.probabilities_with_status(game)
                    actual, saved_status = loaded.probabilities_with_status(game)
                    if saved_status != status or not np.array_equal(expected, actual):
                        raise ValueError("Checkpoint changed a policy distribution")
                    if not np.isfinite(actual).all() or (actual < 0).any():
                        raise ValueError("Invalid action probabilities")
                    if abs(float(actual.sum()) - 1) > 1e-10 or len(actual) != len(legal):
                        raise ValueError("Action probabilities do not match legal menu")
                    counts[f"{game.street}:{status}"] += 1
                    action = (1 if hand % 2 else generator.choices(legal, actual, k=1)[0])
                    decisions.append(dict(hand=hand, street=game.street, status=status,
                                          probabilities=actual.tolist(), action=action))
                    game.step(action)
                    steps += 1
                    if steps > 200:
                        raise ValueError("Hand exceeded 200 decisions")
                if sum(game.payoffs()) != 0:
                    raise ValueError("Settlement is not zero sum")
    result.update(hands=48, decisions=len(decisions), counts=dict(counts),
                  distribution_reload_checks=len(decisions))
    trainer.table.close()
    if trainer.sketch is not None:
        trainer.sketch.close()
    write_json(directory / "policy-samples.json", decisions)
    write_json(directory / "probe.json", result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(PROJECT))
    if args.probe:
        probe(args.probe)
        return 0
    context = begin_run(ROOT)
    started = time.perf_counter()
    directory = ROOT / "experiments/results/runs" / uuid.uuid4().hex
    directory.mkdir(parents=True)
    print(f"Pilot outputs: {directory}", flush=True)
    context["output_directory"] = directory.relative_to(ROOT).as_posix()
    shutil.copyfile(__file__, directory / "experiment.py")
    report = dict(status="failed", seed=SEED, workers=2, seconds=600,
                  max_infosets=8_000_000, scope="Training feasibility, not playing strength")
    try:
        git = ["git", "-c", f"safe.directory={PROJECT.as_posix()}", "-C", str(PROJECT)]
        report["external_commit"] = subprocess.check_output(
            git + ["rev-parse", "HEAD"], text=True).strip()
        scope = ["pluribus_lite", "train_blueprint.py"]
        changed = subprocess.check_output(git + ["status", "--porcelain", "--", *scope], text=True)
        if changed.strip():
            raise ValueError("External training source is modified: " + changed)
        names = subprocess.check_output(git + ["ls-files", "--", *scope], text=True).splitlines()
        report["source_hashes"] = {name: digest(PROJECT / name) for name in names}
        buckets = directory / "buckets"
        buckets.mkdir()
        for name in ("meta.json", "flop_centroids.npy", "turn_centroids.npy"):
            shutil.copyfile(PROJECT / "buckets_BACKUP_a2cdd84d" / name, buckets / name)
        report["bucket_input_hashes"] = {path.name: digest(path) for path in buckets.iterdir()}
        write_json(directory / "design.json", report)
        training = directory / "training"
        training.mkdir()
        command = [sys.executable, "-B", "-u", str(PROJECT / "train_blueprint.py"),
                   "--num-players", "6", "--stack", "200", "--sb", "1", "--bb", "2",
                   "--workers", "2", "--sync-every", "100", "--max-infosets", "8000000",
                   "--seed", str(SEED), "--hours", str(1 / 6), "--save-min", "2",
                   "--buckets", str(buckets), "--run-dir", str(training)]
        report["training"] = supervise(command, directory, "training", 720, training)
        report["checkpoint_before_resume"] = json.loads(
            (training / "blueprint_ckpt/meta.json").read_text())
        print("Training completed; checking resume and policy reload", flush=True)
        report["probe_process"] = supervise(
            [sys.executable, "-B", "-u", str(Path(__file__).resolve()), "--probe", str(directory)],
            directory, "probe", 180, training)
        report["probe"] = json.loads((directory / "probe.json").read_text())
        report["status"] = "passed"
        report["summary"] = (f"Six-max pilot: {report['probe']['iteration_before']:,} iterations; "
                             "200 resumed iterations and 48 policy hands passed")
    except Exception:
        report["failure"] = traceback.format_exc()
        report["summary"] = "Six-max training pilot failed; partial evidence retained"
        print(report["failure"], flush=True)
    finally:
        report["output_hashes"] = {path.relative_to(directory).as_posix(): digest(path)
                                   for path in directory.rglob("*") if path.is_file()}
        finish_run(context, "2026-09-08-six-max-training", report, time.perf_counter() - started)
        print(directory / "result.json", flush=True)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
