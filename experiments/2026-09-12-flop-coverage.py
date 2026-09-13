"""Four-arm serial flop coverage experiment, with bounded, restartable workers.

Full settings implement the reviewed 100bb diagnostic design. The smoke profile
exercises the same paths with much smaller samples and cannot support a strength
or production-abstraction claim. The controller is the sole run-journal writer.
"""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import shutil
import signal
import stat
import statistics
import subprocess
import sys
import time
import uuid

from pontius.early_holdem import EarlyHoldemGame, EarlyHoldemState
from pontius.execution import begin_run, finish_run, git
from pontius.game import TERMINAL_PLAYER
from pontius.holdem_cards import SixSeatHoldemDeal
from pontius.no_limit_betting import BettingStreet, NoLimitBettingState
from pontius.sampled_cfr import ExternalSamplingCFR, SamplingLimit
from pontius import training_checkpoint


ROOT = Path(__file__).resolve().parents[1]
GIB = 1024**3
ARMS = {"A": ("exact", 1), "B": ("exact", 8), "C": ("structural", 1), "D": ("structural", 8)}
STOP_REQUESTED = False
FULL = dict(
    iterations=5000,
    milestones=[0, 100, 1000, 5000],
    seeds=[1101, 1102, 1103],
    calibration_iterations=500,
    resume_steps=100,
    coverage_deals=2000,
    evaluation_deals=2000,
    bootstrap_repetitions=2000,
    max_rows=500_000,
    max_nodes=100_000,
    cell_seconds=1200,
    total_seconds=21600,
    evaluation_seconds=2700,
    soft_memory_bytes=12 * GIB,
    hard_memory_bytes=16 * GIB,
    disk_bytes=50 * GIB,
    free_bytes=100 * GIB,
    recovery_seconds=300,
    shutdown_seconds=30,
)
SMOKE = FULL | dict(
    iterations=4,
    milestones=[0, 2, 4],
    seeds=[1101],
    calibration_iterations=3,
    resume_steps=2,
    coverage_deals=4,
    evaluation_deals=2,
    bootstrap_repetitions=100,
    max_rows=5000,
    cell_seconds=60,
    total_seconds=300,
    evaluation_seconds=60,
    free_bytes=0,
)


class ExperimentLimit(RuntimeError):
    """A retained resource result, not a correctness failure."""


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def file_digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def disk_used(root):
    total = 0
    for path in Path(root).rglob("*"):
        try:
            observed = path.stat()
        except FileNotFoundError:
            # A writer can publish its temporary name while this scan is in flight.
            continue
        if stat.S_ISREG(observed.st_mode):
            total += observed.st_size
    return total


def reserve_disk(root, additional, limit):
    if disk_used(root) + additional > limit:
        raise ExperimentLimit("disk_budget")


def atomic_json(path, value, *, budget_root=None, disk_limit=None, immutable=False):
    path = Path(path)
    raw = encoded(value) + b"\n"
    if immutable and path.exists():
        if path.read_bytes() != raw:
            raise ValueError(f"immutable artifact differs: {path.name}")
        return
    if budget_root is not None:
        reserve_disk(budget_root, len(raw), disk_limit)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(".writing-" + path.name + "-" + uuid.uuid4().hex)
    with temporary.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if immutable and path.exists():
        raise FileExistsError(path)
    temporary.replace(path)
    training_checkpoint._sync_directory(path.parent)


def read_json(path):
    return json.loads(Path(path).read_bytes())


def write_run(run, relative, value, *, immutable=False):
    settings = read_json(run / "manifest.json")["settings"]
    atomic_json(
        run / relative,
        value,
        budget_root=run,
        disk_limit=settings["disk_bytes"] - 2 * 1024 * 1024,
        immutable=immutable,
    )


def stream_seed(seed, domain):
    return int.from_bytes(
        hashlib.sha256(f"flop-coverage-v1/{seed}/{domain}".encode()).digest(), "big"
    )


def game_for(arm, continuation="check_call"):
    return EarlyHoldemGame(100, 1, continuation, flop_representation=ARMS[arm][0])


def make_trainer(arm, seed, settings, sampler=None):
    game = game_for(arm)
    return ExternalSamplingCFR(
        6,
        sampler or game.sample_root,
        game.game_id,
        variant="cfr",
        seed=seed,
        averaging_trajectories=ARMS[arm][1],
        max_rows=settings["max_rows"],
        max_nodes=settings["max_nodes"],
    )


def passive_action(actions):
    return "check" if "check" in actions else "call"


def initial_betting():
    return NoLimitBettingState.new_hand(
        button=0, starting_stacks=(200,) * 6, small_blind=1, big_blind=2
    )


@contextmanager
def controller_lock(run):
    """One coordinator per run; the kernel releases this lock after a crash."""
    run.mkdir(parents=True, exist_ok=True)
    with (run / ".controller.lock").open("a+b") as stream:
        if os.fstat(stream.fileno()).st_size == 0:
            stream.write(b"L")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeError("another controller already owns this run") from error
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def make_panels(settings, deadline=None):
    exact, structural = game_for("A"), game_for("C")
    observations, coverage_deals = [], []
    for profile in ("passive", "uniform"):
        deals_rng = random.Random(stream_seed(2101, "coverage-deals/" + profile))
        for block in range(settings["coverage_deals"]):
            if deadline is not None:
                check_stop(deadline, settings)
            state = exact.sample_root(deals_rng)
            coverage_deals.append(dict(profile=profile, block=block, deal=asdict(state.deal)))
            actions_rng = random.Random(stream_seed(2101, f"coverage/{profile}/{block}"))
            while state.current_player != TERMINAL_PLAYER:
                actions = state.legal_actions()
                if state.betting.street == BettingStreet.FLOP:
                    observations.append(
                        dict(
                            profile=profile,
                            block=block,
                            actor=state.current_player,
                            live=len(state.betting.live_seats),
                            actions=list(actions),
                            keys={
                                "exact": state.information_state_key(state.current_player),
                                "structural": EarlyHoldemState(
                                    structural, state.deal, state.betting
                                ).information_state_key(state.current_player),
                            },
                        )
                    )
                selected = (
                    actions_rng.choice(actions) if profile == "uniform" else passive_action(actions)
                )
                state = state.apply_action(selected)
    play_deals = []
    for opponent in ("passive", "uniform"):
        for continuation in ("check_call", "showdown_betting"):
            rng = random.Random(stream_seed(3101, f"play-deals/{opponent}/{continuation}"))
            for block in range(settings["evaluation_deals"]):
                if deadline is not None:
                    check_stop(deadline, settings)
                play_deals.append(
                    dict(
                        opponent=opponent,
                        continuation=continuation,
                        block=block,
                        deal=asdict(exact.sample_root(rng).deal),
                        action_seed=stream_seed(
                            3101, f"play-actions/{opponent}/{continuation}/{block}"
                        ),
                    )
                )
    return dict(
        format="flop-coverage-panels-v1",
        coverage_seed=2101,
        play_seed=3101,
        coverage_deals=coverage_deals,
        observations=observations,
        play_deals=play_deals,
    )


def prepare_panels(run, settings):
    started = time.perf_counter()
    deadline = read_json(run / "manifest.json").get("deadline_utc")
    if deadline is not None:
        deadline -= 35
        check_stop(deadline, settings)
    metadata_path = run / "panels-metadata.json"
    if not (run / "panels.json").exists():
        panels = make_panels(settings, deadline)
        write_run(run, "panels.json", panels, immutable=True)
    elif not metadata_path.exists():
        panels = read_json(run / "panels.json")
    else:
        panels = None
    if not metadata_path.exists():
        write_run(
            run,
            "panels-metadata.json",
            dict(
                sha256=file_digest(run / "panels.json"),
                seconds=time.perf_counter() - started,
                observations=len(panels["observations"]),
            ),
            immutable=True,
        )
    metadata = read_json(metadata_path)
    if file_digest(run / "panels.json") != metadata["sha256"]:
        raise ValueError("fixed panel checksum mismatch")
    return metadata


def row_probabilities(row):
    total = math.fsum(row.strategy_sum)
    return (
        [value / total for value in row.strategy_sum]
        if total
        else [1.0 / len(row.actions)] * len(row.actions)
    )


def coverage_summary(rows, observations, representation):
    groups = {}
    iteration_histograms = {}
    for observation in observations:
        live = observation["live"]
        live_group = "heads_up" if live == 2 else "three_way" if live == 3 else "four_to_six"
        names = (
            "all",
            observation["profile"],
            live_group,
            observation["profile"] + "/" + live_group,
        )
        row = rows.get(observation["keys"][representation])
        for name in names:
            counters = groups.setdefault(name, Counter())
            counters["observations"] += 1
            if row is None:
                counters["missing"] += 1
                continue
            if tuple(observation["actions"]) != row.actions:
                raise ValueError("panel row has incompatible legal actions")
            counters["averaged" if row.average_visits else "unaveraged"] += 1
            counters["repeat_averaged"] += int(row.average_visits >= 2)
            counters["at_least_20_samples"] += int(row.average_samples >= 20)
            if row.average_samples >= 20:
                histogram = iteration_histograms.setdefault(name, Counter())
                histogram[str(row.average_visits)] += 1
            counters["average_with_prior_regret"] += int(row.average_regret_samples > 0)
            counters["regret_sampled"] += int(row.regret_visits > 0)
    for name in ("all", "heads_up", "three_way", "four_to_six", "passive", "uniform"):
        groups.setdefault(name, Counter())
    output = {}
    measures = (
        "missing",
        "unaveraged",
        "averaged",
        "repeat_averaged",
        "at_least_20_samples",
        "average_with_prior_regret",
        "regret_sampled",
    )
    for name, counters in groups.items():
        size = counters["observations"]
        record = {"observations": size, **{field: counters[field] for field in measures}}
        record.update(
            {field + "_rate": counters[field] / size if size else None for field in measures}
        )
        record["at_least_20_samples_iteration_histogram"] = dict(
            iteration_histograms.get(name, {})
        )
        output[name] = record
    return output


def panel_probabilities(trainer, observations, representation):
    output = []
    for observation in observations:
        row = trainer.rows.get(observation["keys"][representation])
        if row is None:
            passive = passive_action(observation["actions"])
            output.append([float(action == passive) for action in observation["actions"]])
        else:
            output.append(row_probabilities(row))
    return output


def bootstrap_interval(blocks, *, seed, repetitions):
    if len(blocks) < 2 or repetitions < 20 or any(not math.isfinite(x) for x in blocks):
        raise ValueError("bootstrap requires finite independent blocks and >=20 resamples")
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(blocks, k=len(blocks))) for _ in range(repetitions))
    interval = [means[int(0.025 * (repetitions - 1))], means[int(0.975 * (repetitions - 1))]]
    mean = statistics.fmean(blocks)
    return dict(
        independent_deal_blocks=len(blocks),
        mean_bb_per_hand=mean,
        ci95_bb_per_hand=interval,
        mean_bb_per_100=100 * mean,
        ci95_bb_per_100=[100 * endpoint for endpoint in interval],
        method="percentile bootstrap of independent six-seat deal-block means",
    )


def process_rss(pid):
    if sys.platform.startswith("linux"):
        try:
            fields = dict(
                line.split(":", 1)
                for line in Path(f"/proc/{pid}/status").read_text().splitlines()
                if ":" in line
            )
            return int(fields.get("VmRSS", "0 kB").split()[0]) * 1024
        except OSError, ValueError, ProcessLookupError:
            return 0
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("faults", wintypes.DWORD),
                *[
                    (name, ctypes.c_size_t)
                    for name in (
                        "peak",
                        "working",
                        "quota_peak_paged",
                        "quota_paged",
                        "quota_peak_nonpaged",
                        "quota_nonpaged",
                        "pagefile",
                        "peak_pagefile",
                    )
                ],
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x410, False, pid)
        if not handle:
            return 0
        try:
            values = Counters()
            values.cb = ctypes.sizeof(values)
            function = ctypes.WinDLL("psapi").GetProcessMemoryInfo
            function.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
            return values.working if function(handle, ctypes.byref(values), values.cb) else 0
        finally:
            kernel.CloseHandle(handle)
    return 0


def process_tree_rss(pid):
    total = process_rss(pid)
    if sys.platform.startswith("linux"):
        try:
            children = Path(f"/proc/{pid}/task/{pid}/children").read_text().split()
        except OSError:
            children = []
        total += sum(process_tree_rss(int(child)) for child in children)
    return total


def peak_self_rss():
    if sys.platform.startswith("linux"):
        import resource

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    return process_rss(os.getpid())


def current_cgroup():
    if not sys.platform.startswith("linux"):
        return None
    lines = Path("/proc/self/cgroup").read_text().splitlines()
    group = next((line.split(":", 2)[2] for line in lines if line.startswith("0::")), None)
    return Path("/sys/fs/cgroup") / group.lstrip("/") if group is not None else None


def oom_kills():
    group = current_cgroup()
    if group is None:
        return 0
    try:
        events = dict(line.split() for line in (group / "memory.events").read_text().splitlines())
        return int(events.get("oom_kill", 0))
    except OSError:
        return 0


class KeyTimer:
    def __init__(self, game):
        self.game = game
        self.seconds = 0.0
        self.calls = 0

    def sample_root(self, rng):
        return TimedState(self.game.sample_root(rng), self)


class TimedState:
    """Timing-only adapter; all simulator decisions and random draws are unchanged."""

    def __init__(self, state, timer):
        self.state, self.timer = state, timer

    @property
    def current_player(self):
        return self.state.current_player

    def legal_actions(self):
        return self.state.legal_actions()

    def chance_outcomes(self):
        return self.state.chance_outcomes()

    def apply_action(self, action):
        return TimedState(self.state.apply_action(action), self.timer)

    def information_state_key(self, player):
        started = time.perf_counter()
        key = self.state.information_state_key(player)
        self.timer.seconds += time.perf_counter() - started
        self.timer.calls += 1
        return key

    def returns(self):
        return self.state.returns()


def save_trainer(run, directory, trainer, name):
    settings = read_json(run / "manifest.json")["settings"]
    destination = directory / "generations" / name
    if destination.exists():
        saved = training_checkpoint._read_generation(destination)["payload"]
        if saved != trainer.state_dict():
            raise ValueError("existing immutable checkpoint differs from live state")
        return 0.0
    snapshot = trainer.state_dict()
    # The exact payload size plus ample fixed envelope allowance bounds this writer.
    reserve_disk(run, len(encoded(snapshot)) + 3 * 1024 * 1024, settings["disk_bytes"])
    started = time.perf_counter()
    training_checkpoint.save_checkpoint(directory, snapshot, name)
    return time.perf_counter() - started


def export_policy(run, path, trainer):
    if path.exists():
        return file_digest(path)
    settings = read_json(run / "manifest.json")["settings"]
    remaining = settings["disk_bytes"] - disk_used(run) - 2 * 1024 * 1024
    temporary = path.with_name(".writing-" + path.name + "-" + uuid.uuid4().hex)
    written = 0
    with temporary.open("xb") as stream:
        header = dict(
            format="flop-coverage-policy-v1",
            identity=trainer.identity,
            game_id=trainer.game_id,
            iterations=trainer.iterations,
            missing="check/call",
            unaveraged="uniform",
        )
        for record in (header,):
            raw = encoded(record) + b"\n"
            if written + len(raw) > remaining:
                raise ExperimentLimit("disk_budget")
            stream.write(raw)
            written += len(raw)
        for key, row in sorted(trainer.rows.items()):
            raw = (
                encoded(
                    dict(
                        key=key,
                        actions=row.actions,
                        probabilities=row_probabilities(row),
                        average_visits=row.average_visits,
                    )
                )
                + b"\n"
            )
            if written + len(raw) > remaining:
                raise ExperimentLimit("disk_budget")
            stream.write(raw)
            written += len(raw)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.rename(path)
    training_checkpoint._sync_directory(path.parent)
    return file_digest(path)


def milestone(run, cell, trainer, panels, timers, previous_vectors):
    iteration = trainer.iterations
    path = cell / f"milestone-{iteration:06d}.json"
    if path.exists():
        old = read_json(path)
        return old, old["panel_probabilities"]
    cpu_started = time.process_time()
    checkpoint_seconds = save_trainer(
        run, cell / "checkpoints", trainer, f"milestone-{iteration:06d}"
    )
    timers["checkpoint_seconds"] += checkpoint_seconds
    evaluation_started = time.perf_counter()
    representation = ARMS[read_json(cell / "cell.json")["arm"]][0]
    coverage = coverage_summary(trainer.rows, panels["observations"], representation)
    vectors = panel_probabilities(trainer, panels["observations"], representation)
    movement = (
        statistics.fmean(
            0.5 * sum(abs(a - b) for a, b in zip(before, after, strict=True))
            for before, after in zip(previous_vectors, vectors, strict=True)
        )
        if previous_vectors and vectors
        else None
    )
    entropy = (
        statistics.fmean(-sum(p * math.log(p) for p in vector if p) for vector in vectors)
        if vectors
        else None
    )
    counts = Counter()
    for key, row in trainer.rows.items():
        street = json.loads(key)["public"]["street"]
        counts[street + "_rows"] += 1
        counts[street + "_regret_only"] += int(row.regret_visits > 0 and not row.average_visits)
        counts[street + "_average_only"] += int(row.average_visits > 0 and not row.regret_visits)
        counts[street + "_average_samples"] += row.average_samples
        counts[street + "_average_iterations"] += row.average_visits
        counts[street + "_average_regret_samples"] += row.average_regret_samples
    timers["coverage_seconds"] += time.perf_counter() - evaluation_started
    export_started = time.perf_counter()
    policy_path = cell / f"policy-{iteration:06d}.jsonl"
    policy_hash = export_policy(run, policy_path, trainer)
    timers["export_seconds"] += time.perf_counter() - export_started
    timers["cpu_seconds"] += time.process_time() - cpu_started
    result = dict(
        iterations=iteration,
        identity=trainer.identity,
        rows=len(trainer.rows),
        coverage=coverage,
        row_counts=dict(counts),
        panel_probabilities=vectors,
        panel_mean_entropy=entropy,
        panel_policy_movement=movement,
        peak_self_rss_bytes=peak_self_rss(),
        timers=dict(timers),
        wall_seconds=time.time() - read_json(cell / "cell.json")["started_utc"],
        total_nodes=trainer.total_nodes,
        total_regret_nodes=trainer.total_regret_nodes,
        total_average_nodes=trainer.total_average_nodes,
        policy_file=policy_path.name,
        policy_sha256=policy_hash,
        checkpoint_file=f"checkpoints/generations/milestone-{iteration:06d}",
    )
    write_run(run, str(path.relative_to(run)), result, immutable=True)
    return result, vectors


def stop_handler(signum, frame):
    global STOP_REQUESTED
    STOP_REQUESTED = True


def check_stop(deadline, settings):
    if STOP_REQUESTED:
        raise ExperimentLimit("supervisor_stop")
    if time.time() >= deadline:
        raise ExperimentLimit("time_budget")
    if process_tree_rss(os.getpid()) >= settings["soft_memory_bytes"]:
        raise ExperimentLimit("soft_memory_budget")


def cell_worker(run, arm, seed):
    manifest = read_json(run / "manifest.json")
    settings = manifest["settings"]
    cell = run / "cells" / f"{arm}-{seed}"
    cell.mkdir(parents=True, exist_ok=True)
    metadata = cell / "cell.json"
    resumed_process = metadata.exists()
    if not metadata.exists():
        write_run(
            run,
            str(metadata.relative_to(run)),
            dict(
                arm=arm,
                seed=seed,
                started_utc=time.time(),
                deadline_utc=min(time.time() + settings["cell_seconds"], manifest["deadline_utc"]),
            ),
            immutable=True,
        )
    deadline = read_json(metadata)["deadline_utc"]
    game = game_for(arm)
    timer = KeyTimer(game)
    trainer = make_trainer(arm, seed, settings, timer.sample_root)
    timers = dict(
        training_seconds=0.0,
        checkpoint_seconds=0.0,
        checkpoint_load_seconds=0.0,
        coverage_seconds=0.0,
        export_seconds=0.0,
        key_seconds=0.0,
        key_calls=0,
        cpu_seconds=0.0,
        incomplete_after_restart=resumed_process,
    )
    progress_path = cell / "progress.json"
    if progress_path.exists():
        timers.update(read_json(progress_path).get("timers", {}))
    timers["incomplete_after_restart"] = resumed_process
    load_started = time.perf_counter()
    try:
        state = training_checkpoint.load_checkpoint(cell / "checkpoints", trainer.identity)
    except FileNotFoundError:
        state = None
    if state is not None:
        trainer = ExternalSamplingCFR.from_state(state, timer.sample_root, game.game_id)
        del state
    timers["checkpoint_load_seconds"] += time.perf_counter() - load_started
    panels = read_json(run / "panels.json")
    previous_paths = sorted(cell.glob("milestone-*.json"))
    previous_vectors = (
        read_json(previous_paths[-1])["panel_probabilities"] if previous_paths else None
    )
    cpu_started = time.process_time()
    previous_key_seconds, previous_key_calls = timers["key_seconds"], timers["key_calls"]
    previous_cpu = timers["cpu_seconds"]
    last_recovery = time.monotonic()
    stop = "iteration_budget"
    try:
        _, previous_vectors = milestone(run, cell, trainer, panels, timers, previous_vectors)
        while trainer.iterations < settings["iterations"]:
            check_stop(deadline, settings)
            started = time.perf_counter()
            trainer.step()
            timers["training_seconds"] += time.perf_counter() - started
            timers["cpu_seconds"] = previous_cpu + time.process_time() - cpu_started
            timers["key_seconds"] = previous_key_seconds + timer.seconds
            timers["key_calls"] = previous_key_calls + timer.calls
            if trainer.iterations in settings["milestones"]:
                _, previous_vectors = milestone(
                    run, cell, trainer, panels, timers, previous_vectors
                )
                last_recovery = time.monotonic()
            elif time.monotonic() - last_recovery >= settings["recovery_seconds"]:
                timers["checkpoint_seconds"] += save_trainer(
                    run, cell / "checkpoints", trainer, f"recovery-{trainer.iterations:06d}"
                )
                last_recovery = time.monotonic()
            if trainer.iterations % 25 == 0:
                write_run(
                    run,
                    str(progress_path.relative_to(run)),
                    dict(
                        arm=arm,
                        seed=seed,
                        iterations=trainer.iterations,
                        rows=len(trainer.rows),
                        timers=timers,
                        rss_bytes=process_rss(os.getpid()),
                        updated_utc=time.time(),
                    ),
                )
                print(
                    f"{arm}/{seed}: {trainer.iterations} iterations, {len(trainer.rows)} rows",
                    flush=True,
                )
    except (SamplingLimit, ExperimentLimit) as error:
        stop = str(error)
    finally:
        timers["cpu_seconds"] = previous_cpu + time.process_time() - cpu_started
        timers["key_seconds"] = previous_key_seconds + timer.seconds
        timers["key_calls"] = previous_key_calls + timer.calls
    try:
        final_milestone, _ = milestone(run, cell, trainer, panels, timers, previous_vectors)
    except ExperimentLimit as error:
        final_milestone = None
        stop = str(error)
    result = dict(
        arm=arm,
        seed=seed,
        representation=ARMS[arm][0],
        averaging_trajectories=ARMS[arm][1],
        identity=trainer.identity,
        completed_iterations=trainer.iterations,
        stop=stop,
        rows=len(trainer.rows),
        timers=timers,
        peak_self_rss_bytes=peak_self_rss(),
        wall_seconds=time.time() - read_json(metadata)["started_utc"],
        resumed_process=resumed_process,
        final_milestone_saved=final_milestone is not None,
    )
    write_run(run, str((cell / "completed.json").relative_to(run)), result, immutable=True)
    print(json.dumps(result), flush=True)


def regret_state(trainer):
    return dict(
        iterations=trainer.iterations,
        rng=trainer.rng.getstate(),
        nodes=trainer.total_regret_nodes,
        rows={
            key: [row.player, row.actions, row.regrets, row.regret_visits]
            for key, row in trainer.rows.items()
            if row.regret_visits
        },
    )


def calibration_deadline(run, settings):
    manifest = read_json(run / "manifest.json")
    job = run / "jobs/calibrate.json"
    return min(
        read_json(job)["deadline_utc"] if job.exists() else time.time() + settings["cell_seconds"],
        manifest.get("deadline_utc", math.inf),
    )


def calibration_check(run, deadline, settings):
    check_stop(deadline, settings)
    reserve_disk(run, 2 * 1024 * 1024, settings["disk_bytes"])


def memory_observer(pid, output):
    """Independent RSS sampling continues while the observed Python holds its GIL."""
    interval = 0.01
    started = previous = time.monotonic()
    peak, samples, max_gap = 0, 0, 0.0
    while True:
        now = time.monotonic()
        peak = max(peak, process_rss(pid))
        samples += 1
        max_gap = max(max_gap, now - previous)
        previous = now
        result = dict(
            observed_pid=pid,
            sampled_peak_rss_bytes=peak,
            samples=samples,
            sample_interval_seconds=interval,
            maximum_sample_gap_seconds=max_gap,
            observed_window_seconds=now - started,
            method="independent_process_sampled_rss",
            limitation="Sampled phase window including handshake; transient peaks may be missed.",
        )
        if samples == 1:
            atomic_json(output, result)
        if output.with_suffix(".stop").exists() or STOP_REQUESTED:
            atomic_json(output, result)
            return
        time.sleep(interval)


@contextmanager
def checkpoint_memory(run, label, deadline, settings):
    output = run / "controls/memory" / (label + "-" + uuid.uuid4().hex + ".json")
    output.parent.mkdir(parents=True, exist_ok=True)
    child = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "observe-memory",
         "--run-directory", str(run), "--pid", str(os.getpid()), "--output", str(output)],
        cwd=ROOT,
        **child_options(isolated=False),
    )
    measurement = {}
    try:
        ready_deadline = time.monotonic() + 10
        while not output.exists():
            calibration_check(run, deadline, settings)
            if child.poll() is not None or time.monotonic() >= ready_deadline:
                raise RuntimeError("checkpoint memory observer did not become ready")
            time.sleep(0.01)
        yield measurement
    finally:
        output.with_suffix(".stop").touch()
        try:
            child.wait(timeout=5)
            if child.returncode:
                raise RuntimeError("checkpoint memory observer failed")
            if output.exists():
                measurement.update(read_json(output))
        finally:
            if child.poll() is None:
                child.kill()
                child.wait()


def resume_worker(run, arm, checkpoint, output):
    settings = read_json(run / "manifest.json")["settings"]
    deadline = calibration_deadline(run, settings)
    game = game_for(arm)
    result = dict(status="running", arm=arm)
    try:
        calibration_check(run, deadline, settings)
        with checkpoint_memory(run, "load-" + arm, deadline, settings) as load_memory:
            started = time.perf_counter()
            state = training_checkpoint.load_checkpoint(Path(checkpoint))
            trainer = ExternalSamplingCFR.from_state(state, game.sample_root, game.game_id)
            del state
            result["load_seconds"] = time.perf_counter() - started
        result["load_memory"] = load_memory
        result["fresh_process_peak_after_load_bytes"] = peak_self_rss()
        for _ in range(settings["resume_steps"]):
            calibration_check(run, deadline, settings)
            trainer.step()
        result.update(status="passed", logical_sha256=digest(trainer.state_dict()),
                      iterations=trainer.iterations)
    except (SamplingLimit, ExperimentLimit) as error:
        result.update(status="capped", stop=str(error))
    atomic_json(Path(output), result)


def calibration_worker(run):
    settings = read_json(run / "manifest.json")["settings"]
    controls = dict(status="running", passed=False, pairs=[], resumes=[], interrupted_writers=[])
    deadline = calibration_deadline(run, settings)
    active_trainers = []
    try:
        calibration_work(run, settings, controls, active_trainers, deadline)
        controls.update(status="passed", passed=True)
    except (SamplingLimit, ExperimentLimit, subprocess.TimeoutExpired) as error:
        controls.update(status="capped", stop=("time_budget" if isinstance(
            error, subprocess.TimeoutExpired) else str(error)))
    except Exception as error:
        controls.update(status="failed", failure_reason=f"{type(error).__name__}: {error}")
        raise
    finally:
        if active_trainers:
            controls["active"].update(
                common_iterations=min(trainer.iterations for trainer in active_trainers),
                iterations=[trainer.iterations for trainer in active_trainers],
                rows=[len(trainer.rows) for trainer in active_trainers],
            )
        # The supervisor and work checks reserve two MiB for structured stop evidence.
        atomic_json(run / "controls.json", controls, budget_root=run,
                    disk_limit=settings["disk_bytes"], immutable=True)


def calibration_work(run, settings, controls, active_trainers, deadline):
    calibration_check(run, deadline, settings)
    controls["active"] = dict(phase="oracles", arms=[], common_iterations=0, rows=[])
    write_run(run, "controls-progress.json", controls)
    # Run the existing independent three-player update/average oracles on this runtime.
    oracle = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "unittest",
            "tests.test_sampled_cfr_oracles",
            "tests.test_sampled_cfr",
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        **child_options(isolated=False),
    )
    oracle_deadline = min(deadline, time.time() + 180)
    try:
        while True:
            calibration_check(run, oracle_deadline, settings)
            try:
                stdout, stderr = oracle.communicate(timeout=0.1)
                controls["oracle_stdout"], controls["oracle_stderr"] = stdout, stderr
                break
            except subprocess.TimeoutExpired:
                continue
    finally:
        if oracle.poll() is None:
            oracle.kill()
            oracle.communicate()
    if oracle.returncode:
        raise AssertionError("sampled-CFR exact oracle suite failed")
    for left, right in (("A", "B"), ("C", "D")):
        trainers = [make_trainer(arm, 1001, settings) for arm in (left, right)]
        active_trainers[:] = trainers
        controls["active"] = dict(phase="regret_pair", arms=[left, right], common_iterations=0,
                                  rows=[0, 0])
        write_run(run, "controls-progress.json", controls)
        for _ in range(settings["calibration_iterations"]):
            for trainer in trainers:
                calibration_check(run, deadline, settings)
                trainer.step()
            if regret_state(trainers[0]) != regret_state(trainers[1]):
                raise AssertionError("extra averaging changed the regret path")
        controls["pairs"].append(
            dict(arms=[left, right], iterations=settings["calibration_iterations"], matched=True)
        )
        active_trainers.clear()
        del trainers
    for arm in ARMS:
        # This reference remains the original live object; it is never reconstructed.
        live = make_trainer(arm, 1101, settings)
        active_trainers[:] = [live]
        controls["active"] = dict(phase="resume", arms=[arm], common_iterations=0, rows=[0])
        write_run(run, "controls-progress.json", controls)
        for _ in range(min(100, settings["calibration_iterations"])):
            calibration_check(run, deadline, settings)
            live.step()
        # A restarted calibration measures a real save in a fresh disposable store.
        # Earlier reference generations remain immutable and count toward the budget.
        checkpoint = run / "controls" / ("resume-" + arm + "-" + uuid.uuid4().hex)
        started = time.perf_counter()
        with checkpoint_memory(run, "save-" + arm, deadline, settings) as save_memory:
            save_started = time.perf_counter()
            checkpoint_write_seconds = save_trainer(run, checkpoint, live, "live-reference")
            save_seconds = time.perf_counter() - save_started
        resume = dict(arm=arm, save_seconds=save_seconds, save_memory=save_memory,
                      checkpoint_directory=str(checkpoint.relative_to(run)),
                      checkpoint_write_seconds=checkpoint_write_seconds,
                      cumulative_parent_peak_after_save_bytes=peak_self_rss())
        controls["resumes"].append(resume)
        write_run(run, "controls-progress.json", controls)
        output = run / "controls" / ("resume-" + arm + ".json")
        child = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "resume-check",
                "--run-directory",
                str(run),
                "--arm",
                arm,
                "--checkpoint",
                str(checkpoint),
                "--output",
                str(output),
            ],
            cwd=ROOT,
            **child_options(isolated=False),
        )
        try:
            for _ in range(settings["resume_steps"]):
                calibration_check(run, deadline, settings)
                live.step()
            while child.poll() is None:
                calibration_check(run, deadline, settings)
                time.sleep(0.05)
            if child.returncode:
                raise AssertionError("separate-process restart check failed")
            restored = read_json(output)
            resume.update({
                key: value for key, value in restored.items()
                if key in ("load_seconds", "load_memory", "fresh_process_peak_after_load_bytes")
            })
            if restored.get("status") == "capped":
                raise ExperimentLimit("resume_" + restored["stop"])
            if restored["logical_sha256"] != digest(live.state_dict()):
                raise AssertionError("live versus separate-process restart diverged")
        finally:
            if child.poll() is None:
                child.kill()
                child.wait()
        resume.update(
            matched_steps=settings["resume_steps"],
            total_control_seconds=time.perf_counter() - started,
        )
        active_trainers.clear()
        del live
    controls["active"] = dict(phase="interrupted_writers", arms=[], common_iterations=0, rows=[])
    write_run(run, "controls-progress.json", controls)
    controls["interrupted_writers"] = interruption_checks(run, deadline, settings)
    controls.pop("active")


def child_options(*, isolated=True):
    options = (
        {"creationflags": subprocess.CREATE_NO_WINDOW}
        if os.name == "nt"
        else {"start_new_session": isolated}
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(ROOT / "src"), str(ROOT)))
    return options | {"env": environment}


def interrupted_writer(run, boundary):
    root = run / "controls" / ("writer-" + boundary)
    marker = root / "ready"
    original_sync = training_checkpoint._sync_directory

    def synchronize(path):
        original_sync(path)
        selected = (
            path.name.startswith(".staging-")
            if boundary == "staged"
            else path == root / "generations"
        )
        if selected:
            marker.write_text("ready", encoding="utf-8")
            while True:
                time.sleep(0.05)

    training_checkpoint._sync_directory = synchronize
    training_checkpoint.save_checkpoint(
        root, {"identity": "writer-control-v1", "step": 2}, "second"
    )


def interruption_checks(run, calibration_end=None, settings=None):
    results = []
    for boundary, expected in (("staged", 1), ("published", 2)):
        if calibration_end is not None:
            calibration_check(run, calibration_end, settings)
        root = run / "controls" / ("writer-" + boundary)
        # On interrupted calibration, use a distinct disposable attempt directory.
        if root.exists():
            root.rename(root.with_name(root.name + "-retained-" + uuid.uuid4().hex[:8]))
        training_checkpoint.save_checkpoint(
            root, {"identity": "writer-control-v1", "step": 1}, "first"
        )
        child = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "interrupt-writer",
                "--run-directory",
                str(run),
                "--boundary",
                boundary,
            ],
            cwd=ROOT,
            **child_options(isolated=False),
        )
        try:
            deadline = time.monotonic() + 20
            while not (root / "ready").exists() and child.poll() is None:
                if calibration_end is not None:
                    calibration_check(run, calibration_end, settings)
                if time.monotonic() >= deadline:
                    raise AssertionError("writer did not reach the selected boundary")
                time.sleep(0.02)
            if child.poll() is not None:
                raise AssertionError("writer exited before the selected boundary")
            child.kill()
            child.wait(timeout=10)
        finally:
            if child.poll() is None:
                child.kill()
                child.wait()
        recovered = training_checkpoint.load_checkpoint(root)
        if recovered["step"] != expected:
            raise AssertionError("interrupted writer selected the wrong generation")
        results.append(dict(boundary=boundary, recovered_step=expected, passed=True))
    # Deliberately damage only a disposable copy of the published-writer control.
    copy_root = run / "controls" / ("corrupt-copy-" + uuid.uuid4().hex[:8])
    shutil.copytree(run / "controls/writer-published", copy_root)
    (copy_root / "generations/second/checkpoint.json").write_bytes(b'{"truncated":')
    if training_checkpoint.load_checkpoint(copy_root)["step"] != 1:
        raise AssertionError("corrupt newest generation did not fall back")
    results.append(dict(boundary="truncated_copy", recovered_step=1, passed=True))
    return results


def load_policy(cell, milestone_record):
    path = cell / milestone_record["policy_file"]
    if file_digest(path) != milestone_record["policy_sha256"]:
        raise ValueError("exported policy checksum mismatch")
    policy = {}
    with path.open() as stream:
        header = json.loads(next(stream))
        if header["identity"] != milestone_record["identity"]:
            raise ValueError("exported policy identity mismatch")
        for line in stream:
            row = json.loads(line)
            probabilities = row["probabilities"]
            if (
                row["key"] in policy
                or len(probabilities) != len(row["actions"])
                or any(not math.isfinite(p) or p < 0 for p in probabilities)
                or abs(math.fsum(probabilities) - 1) > 1e-10
            ):
                raise ValueError("invalid exported policy probabilities")
            policy[row["key"]] = (tuple(row["actions"]), probabilities, row["average_visits"])
    return header, policy


def play(deal, target, arm, policy, continuation, opponent, action_seed):
    evaluation_game, source_game = game_for(arm, continuation), game_for(arm)
    state = evaluation_game.state_for(deal, initial_betting())
    randoms = [random.Random(stream_seed(action_seed, f"seat-{seat}")) for seat in range(6)]
    coverage = Counter()
    while state.current_player != TERMINAL_PLAYER:
        actor, actions = state.current_player, state.legal_actions()
        rng = randoms[actor]
        if actor != target:
            action = rng.choice(actions) if opponent == "uniform" else passive_action(actions)
        else:
            key = EarlyHoldemState(source_game, state.deal, state.betting).information_state_key(
                actor
            )
            row = policy.get(key)
            street = state.betting.street.value
            if row is None:
                coverage[street + "_missing"] += 1
                action = passive_action(actions)
            else:
                if row[0] != actions:
                    raise ValueError("policy action menu mismatch during paired evaluation")
                coverage[street + ("_averaged" if row[2] else "_unaveraged")] += 1
                action = rng.choices(actions, weights=row[1], k=1)[0]
        state = state.apply_action(action)
    return state.returns()[target], coverage


def common_milestone(run, seed, arms):
    sets = [
        {
            read_json(path)["iterations"]
            for path in (run / "cells" / f"{arm}-{seed}").glob("milestone-*.json")
        }
        for arm in arms
    ]
    common = set.intersection(*sets)
    return max(common) if common else None


def evaluation_worker(run):
    manifest = read_json(run / "manifest.json")
    settings = manifest["settings"]
    panels = read_json(run / "panels.json")
    deadline = min(
        manifest["deadline_utc"] - 5, read_json(run / "jobs/evaluate.json")["deadline_utc"]
    )
    comparisons = []
    complete = True
    for seed in settings["seeds"]:
        iteration = common_milestone(run, seed, list(ARMS))
        if iteration is None:
            complete = False
            continue
        base_cell = run / "cells" / f"A-{seed}"
        base_record = read_json(base_cell / f"milestone-{iteration:06d}.json")
        _, baseline = load_policy(base_cell, base_record)
        interrupted = False
        for arm in "DBC":
            cell = run / "cells" / f"{arm}-{seed}"
            record = read_json(cell / f"milestone-{iteration:06d}.json")
            _, candidate = load_policy(cell, record)
            for opponent in ("passive", "uniform"):
                for continuation in ("check_call", "showdown_betting"):
                    name = f"evaluation/{arm}-{seed}-{opponent}-{continuation}.json"
                    if (run / name).exists():
                        previous = read_json(run / name)
                        comparisons.append(
                            {
                                key: value
                                for key, value in previous.items()
                                if key != "raw_paired_returns"
                            }
                            | {"raw_file": name}
                        )
                        complete &= previous["complete"]
                        continue
                    raw, block_means = [], []
                    candidate_coverage, baseline_coverage = Counter(), Counter()
                    try:
                        for block in panels["play_deals"]:
                            if (block["opponent"], block["continuation"]) != (
                                opponent,
                                continuation,
                            ):
                                continue
                            check_stop(deadline, settings)
                            deal = SixSeatHoldemDeal(
                                tuple(tuple(hand) for hand in block["deal"]["private_hands"]),
                                tuple(block["deal"]["board_runout"]),
                            )
                            differences = []
                            for target in range(6):
                                action_seed = stream_seed(
                                    block["action_seed"], f"rotation-{target}"
                                )
                                candidate_return, candidate_counts = play(
                                    deal,
                                    target,
                                    arm,
                                    candidate,
                                    continuation,
                                    opponent,
                                    action_seed,
                                )
                                baseline_return, baseline_counts = play(
                                    deal, target, "A", baseline, continuation, opponent, action_seed
                                )
                                candidate_coverage.update(candidate_counts)
                                baseline_coverage.update(baseline_counts)
                                raw.append(
                                    [block["block"], target, candidate_return, baseline_return]
                                )
                                differences.append(candidate_return - baseline_return)
                            block_means.append(statistics.fmean(differences))
                    except ExperimentLimit:
                        complete = False
                        interrupted = True
                    panel_complete = len(block_means) == settings["evaluation_deals"]
                    result = dict(
                        arm=arm,
                        seed=seed,
                        baseline="A",
                        iterations=iteration,
                        opponent=opponent,
                        continuation=continuation,
                        primary=arm == "D",
                        complete=panel_complete,
                        candidate_coverage=dict(candidate_coverage),
                        baseline_coverage=dict(baseline_coverage),
                        raw_paired_returns=raw,
                        interval=bootstrap_interval(
                            block_means,
                            seed=stream_seed(3101, name),
                            repetitions=settings["bootstrap_repetitions"],
                        )
                        if panel_complete
                        else None,
                    )
                    write_run(run, name, result, immutable=True)
                    comparisons.append(
                        {key: value for key, value in result.items() if key != "raw_paired_returns"}
                        | {"raw_file": name}
                    )
                    if not panel_complete:
                        complete = False
                        interrupted = True
                        break
                if interrupted:
                    break
            del candidate
            if interrupted:
                break
        del baseline
        if interrupted:
            break
    write_run(
        run,
        "evaluation.json",
        dict(
            complete=complete,
            comparisons=comparisons,
            limitation="Diagnostic opponents/continuations only; no general poker-strength claim.",
        ),
    )


def kill_group(child, force):
    if os.name == "posix":
        # The isolated worker's PID remains its owned PGID after leader exit.
        try:
            os.killpg(child.pid, signal.SIGKILL if force else signal.SIGTERM)
        except ProcessLookupError:
            pass
    elif child.poll() is None:
        if force:
            child.kill()
        else:
            child.terminate()


def group_alive(child):
    if sys.platform.startswith("linux"):
        # Orphan zombies may await init reaping; they cannot execute or write.
        for path in Path("/proc").glob("[0-9]*/stat"):
            try:
                fields = path.read_text().rsplit(") ", 1)[1].split()
                if int(fields[2]) == child.pid and fields[0] != "Z":
                    return True
            except (OSError, ValueError, IndexError, ProcessLookupError):
                continue
        return False
    if os.name == "posix":
        try:
            os.killpg(child.pid, 0)
            return True
        except ProcessLookupError:
            return False
    return child.poll() is None


def cleanup_group(child, grace_seconds):
    kill_group(child, False)
    deadline = time.monotonic() + grace_seconds
    while group_alive(child) and time.monotonic() < deadline:
        time.sleep(0.05)
    kill_group(child, True)
    deadline = time.monotonic() + 5
    while group_alive(child) and time.monotonic() < deadline:
        time.sleep(0.05)
    if group_alive(child):
        raise RuntimeError("worker process group survived forced cleanup")


def monitored_job(run, name, mode, arguments, seconds):
    manifest = read_json(run / "manifest.json")
    settings = manifest["settings"]
    metadata = run / "jobs" / (name + ".json")
    if not metadata.exists():
        write_run(
            run,
            str(metadata.relative_to(run)),
            dict(
                started_utc=time.time(),
                deadline_utc=min(time.time() + seconds, manifest["deadline_utc"] - 5),
            ),
            immutable=True,
        )
    deadline = read_json(metadata)["deadline_utc"]
    if time.time() >= deadline or STOP_REQUESTED:
        return dict(name=name, stop="deadline_before_start", returncode=None, peak_rss_bytes=0)
    log_path = run / "jobs" / (name + ".log")
    reserve_disk(run, 1024 * 1024, settings["disk_bytes"])
    with log_path.open("ab") as log:
        original_oom_kills = oom_kills()
        child = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                mode,
                "--run-directory",
                str(run),
                *arguments,
            ],
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            **child_options(),
        )
        peak, interrupted_at, reason = 0, None, None
        while child.poll() is None:
            rss = process_tree_rss(child.pid)
            peak = max(peak, rss)
            now = time.time()
            if reason is None:
                if STOP_REQUESTED or now >= deadline:
                    reason = "supervisor_time_budget"
                elif rss >= settings["soft_memory_bytes"]:
                    reason = "supervisor_memory_budget"
                elif disk_used(run) >= settings["disk_bytes"] - 2 * 1024 * 1024:
                    reason = "supervisor_disk_budget"
                if reason is not None:
                    kill_group(child, False)
                    interrupted_at = now
            elif now - interrupted_at >= settings["shutdown_seconds"]:
                kill_group(child, True)
            time.sleep(0.2)
        child.wait()
        cleanup_group(
            child,
            max(0, settings["shutdown_seconds"] - (time.time() - interrupted_at))
            if interrupted_at is not None else settings["shutdown_seconds"],
        )
        if reason is None and oom_kills() > original_oom_kills:
            reason = "hard_memory_budget"
    result = dict(
        name=name,
        stop=reason or "completed",
        returncode=child.returncode,
        peak_rss_bytes=peak,
        finished_utc=time.time(),
        wall_seconds=time.time() - read_json(metadata)["started_utc"],
    )
    write_run(run, "jobs/" + name + "-outcome.json", result)
    return result


def coverage_decision(run, settings):
    contrasts = {}
    for arm in "BCD":
        seeds = []
        for seed in settings["seeds"]:
            iteration = common_milestone(run, seed, ["A", arm])
            if iteration is None:
                continue
            records = [
                read_json(run / "cells" / f"{name}-{seed}" / f"milestone-{iteration:06d}.json")
                for name in ("A", arm)
            ]
            rates = [record["coverage"]["all"]["repeat_averaged_rate"] for record in records]
            if None in rates:
                continue
            economics = []
            for record in records:
                covered = record["coverage"]["all"]["repeat_averaged"]
                timers = record.get("timers", {})
                cpu = timers.get("cpu_seconds")
                if timers.get("incomplete_after_restart"):
                    cpu = None
                peak = record.get("peak_self_rss_bytes")
                wall = record.get("wall_seconds")
                cpu = cpu if cpu is not None and math.isfinite(cpu) and cpu > 0 else None
                peak = peak if peak is not None and math.isfinite(peak) and peak > 0 else None
                wall = wall if wall is not None and math.isfinite(wall) and wall > 0 else None
                economics.append(
                    dict(
                        repeat_covered_per_cpu_second=covered / cpu if cpu else None,
                        repeat_covered_per_wall_second=covered / wall if wall else None,
                        repeat_covered_per_peak_gib=(covered * GIB / peak if peak else None),
                    )
                )
            seeds.append(
                dict(
                    seed=seed,
                    iterations=iteration,
                    gain_percentage_points=100 * (rates[1] - rates[0]),
                    baseline_coverage=records[0]["coverage"],
                    treatment_coverage=records[1]["coverage"],
                    economics=economics,
                )
            )
        gains = [row["gain_percentage_points"] for row in seeds]
        coverage_gate_passed = (
            len(gains) == 3
            and sum(gain >= 5 for gain in gains) >= 2
            and statistics.median(gains) > 0
        )
        economic_gains = {}
        for metric in ("repeat_covered_per_cpu_second", "repeat_covered_per_peak_gib"):
            paired = [row["economics"] for row in seeds]
            differences = [pair[1][metric] - pair[0][metric] for pair in paired
                           if all(item[metric] is not None for item in pair)]
            economic_gains[metric] = (
                statistics.median(differences) if len(differences) == 3 else None
            )
        matched_iterations = sorted({row["iterations"] for row in seeds})
        complete = (len(seeds) == 3 and len(matched_iterations) == 1
                    and all(value is not None for value in economic_gains.values()))
        if not complete:
            practical_outcome = "insufficient_measurements"
        elif not coverage_gate_passed:
            practical_outcome = "coverage_gate_not_met"
        elif all(value > 0 for value in economic_gains.values()):
            practical_outcome = "useful_engineering_progress"
        else:
            practical_outcome = "no_practical_improvement"
        contrasts[arm] = dict(
            seeds=seeds,
            coverage_gate_passed=coverage_gate_passed,
            median_economic_gains=economic_gains,
            matched_iterations_across_seeds=matched_iterations,
            measurements_complete=complete,
            practical_outcome=practical_outcome,
        )
    return dict(
        contrasts=contrasts,
        primary_contrast="D minus A",
        practical_outcome=contrasts["D"]["practical_outcome"],
        rule="5 percentage points in >=2/3 seeds at common milestone",
        practical_rule=("Complete three-seed measurements and a passing coverage gate, plus "
                        "positive median treatment-minus-control gains in repeat-covered "
                        "observations per CPU second AND per peak GiB."),
        interpretation="Coverage is an engineering diagnostic; no automatic promotion.",
    )


def ensure_run(run, profile, development, reviewed_commit=None):
    if not run.resolve().is_relative_to((ROOT / "experiments/results").resolve()):
        raise ValueError("run directory must be inside this checkout's experiments/results")
    settings = dict(FULL if profile == "full" else SMOKE)
    context = begin_run(ROOT, allow_working_tree=development, reviewed_commit=reviewed_commit)
    script_sha = file_digest(__file__)
    if not development:
        committed = git(
            ROOT, "show", context["commit"] + ":experiments/2026-09-12-flop-coverage.py"
        )
        if committed.replace(b"\r\n", b"\n") != Path(__file__).read_bytes().replace(b"\r\n", b"\n"):
            raise ValueError("experiment script differs from reviewed commit")
    if profile == "full":
        cgroup = current_cgroup()
        if cgroup is None:
            raise ValueError("full server profile requires Linux cgroup v2")
        maximum = (cgroup / "memory.max").read_text().strip()
        swap = (cgroup / "memory.swap.max").read_text().strip()
        if maximum == "max" or int(maximum) > settings["hard_memory_bytes"] or swap != "0":
            raise ValueError("full profile requires a <=16GiB cgroup with swap disabled")
    manifest_path = run / "manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        if (
            manifest["profile"] != profile
            or manifest["settings"] != settings
            or manifest["source"]["source_sha256"] != context["source_sha256"]
            or manifest["experiment_sha256"] != script_sha
        ):
            raise ValueError("run configuration or source changed; incompatible resume")
        return manifest, context
    if run.exists() and any(path.name != ".controller.lock" for path in run.iterdir()):
        raise ValueError("new run directory is not empty")
    if shutil.disk_usage(ROOT).free < settings["free_bytes"]:
        raise ExperimentLimit("insufficient_free_disk_before_launch")
    run.mkdir(parents=True, exist_ok=True)
    manifest = dict(
        format="flop-coverage-experiment-v1",
        profile=profile,
        settings=settings,
        arms=ARMS,
        source=context,
        experiment_sha256=script_sha,
        started_utc=time.time(),
        deadline_utc=time.time() + settings["total_seconds"],
        python=sys.version,
        platform=platform.platform(),
        stack_bb=100,
        rake=0,
        continuation="check_call",
        coverage_seed=2101,
        evaluation_seed=3101,
        calibration_seed=1001,
        production_promotion=False,
    )
    atomic_json(manifest_path, manifest, immutable=True)
    return manifest, context


def finalize(run, report, context, started):
    atomic_json(run / "final-state.json", report, immutable=True)
    context["output_directory"] = str(run.relative_to(ROOT))
    relative = str((run / "result.json").relative_to(ROOT)).replace("\\", "/")
    journal = ROOT / "execution_journal.jsonl"
    recorded = False
    if journal.exists():
        with journal.open(encoding="utf-8") as stream:
            for line in stream:
                try:
                    recorded |= json.loads(line).get("output") == relative
                except ValueError:
                    continue
    if not recorded:
        finish_run(context, " ".join(sys.argv), report, time.time() - started)
    elif not (run / "result.json").exists():
        atomic_json(run / "result.json", report)


def run_controller(run, profile, development, reviewed_commit=None):
    if (run / "final-state.json").exists():
        report = read_json(run / "final-state.json")
        manifest = read_json(run / "manifest.json")
        finalize(run, report, manifest["source"], manifest["started_utc"])
        print(f"Terminal run retained; no training restarted. Result: {run / 'result.json'}")
        return
    manifest, context = ensure_run(run, profile, development, reviewed_commit)
    settings = manifest["settings"]
    report = dict(
        status="running",
        profile=profile,
        cells=[],
        controls={},
        evaluation={"complete": False},
        jobs=[],
        production_promotion=False,
        manifest_sha256=file_digest(run / "manifest.json"),
    )
    try:
        panel_metadata = prepare_panels(run, settings)
        report["panels_sha256"] = panel_metadata["sha256"]
        print(
            f"Run: {run}\nFrozen panel: {panel_metadata['observations']} flop observations",
            flush=True,
        )
        if not (run / "controls.json").exists():
            outcome = monitored_job(run, "calibrate", "calibrate", [], settings["cell_seconds"])
            report["jobs"].append(outcome)
            if (run / "controls.json").exists():
                report["controls"] = read_json(run / "controls.json")
            elif outcome["stop"] != "completed":
                progress = run / "controls-progress.json"
                report["controls"] = read_json(progress) if progress.exists() else {}
                report["controls"].update(status="capped", passed=False, stop=outcome["stop"],
                                          progress_is_last_retained_observation=True)
                atomic_json(run / "controls.json", report["controls"], immutable=True)
            if outcome["returncode"] != 0 or not (run / "controls.json").exists():
                if outcome["stop"] != "completed":
                    raise ExperimentLimit("calibration_" + outcome["stop"])
                raise AssertionError("calibration failed; inspect jobs/calibrate.log")
        report["controls"] = read_json(run / "controls.json")
        if report["controls"].get("status") == "capped":
            raise ExperimentLimit("calibration_" + report["controls"]["stop"])
        if not report["controls"].get("passed"):
            raise AssertionError("correctness controls did not pass")
        print("Calibration and recovery controls passed.", flush=True)
        training_deadline = manifest["deadline_utc"] - settings["evaluation_seconds"] - 10
        for seed in settings["seeds"]:
            for arm in ARMS:
                completed = run / "cells" / f"{arm}-{seed}" / "completed.json"
                if not completed.exists():
                    if time.time() >= training_deadline:
                        report["cells"].append(
                            dict(
                                arm=arm,
                                seed=seed,
                                stop="training_reserve_deadline",
                                completed_iterations=None,
                                identity=None,
                            )
                        )
                        continue
                    print(f"Starting arm {arm}, seed {seed}", flush=True)
                    outcome = monitored_job(
                        run,
                        f"cell-{arm}-{seed}",
                        "cell",
                        ["--arm", arm, "--seed", str(seed)],
                        min(settings["cell_seconds"], training_deadline - time.time()),
                    )
                    report["jobs"].append(outcome)
                    if outcome["returncode"] not in (0, None) and outcome["stop"] == "completed":
                        raise AssertionError(f"cell {arm}/{seed} failed; inspect its log")
                    if not completed.exists():
                        report["cells"].append(
                            dict(
                                arm=arm,
                                seed=seed,
                                stop=outcome["stop"],
                                completed_iterations=None,
                                identity=None,
                            )
                        )
                        continue
                report["cells"].append(read_json(completed))
                write_run(run, "progress.json", report)
        report["coverage_decision"] = coverage_decision(run, settings)
        if not (run / "evaluation.json").exists():
            print("Starting paired diagnostic evaluation.", flush=True)
            outcome = monitored_job(run, "evaluate", "evaluate", [], settings["evaluation_seconds"])
            report["jobs"].append(outcome)
            if outcome["returncode"] not in (0, None) and outcome["stop"] == "completed":
                raise AssertionError("paired evaluation failed; inspect jobs/evaluate.log")
        if (run / "evaluation.json").exists():
            report["evaluation"] = read_json(run / "evaluation.json")
        all_targets = len(report["cells"]) == 4 * len(settings["seeds"]) and all(
            cell.get("completed_iterations") == settings["iterations"]
            and cell.get("stop") == "iteration_budget"
            for cell in report["cells"]
        )
        report["status"] = (
            "passed" if all_targets and report["evaluation"]["complete"] else "capped"
        )
        report["summary"] = (
            "Bounded four-arm coverage experiment; retained milestones and "
            "diagnostic paired returns. No production or general-strength claim."
        )
    except ExperimentLimit as error:
        report.update(
            status="capped",
            stop=str(error),
            summary="Resource limit retained; no strength verdict.",
        )
    except Exception as error:
        report.update(
            status="failed",
            failure_reason=f"{type(error).__name__}: {error}",
            summary="Experiment failed; retained evidence, no strength verdict.",
        )
    finally:
        report["elapsed_wall_seconds"] = time.time() - manifest["started_utc"]
        report["disk_bytes"] = disk_used(run)
        finalize(run, report, context, manifest["started_utc"])
        print(f"Status: {report['status']}\nResult: {run / 'result.json'}", flush=True)
    if report["status"] == "failed":
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode", choices=("run", "cell", "calibrate", "resume-check", "evaluate", "interrupt-writer",
                         "observe-memory")
    )
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--profile", choices=("full", "smoke"), default="full")
    parser.add_argument("--development", action="store_true")
    parser.add_argument("--reviewed-commit")
    parser.add_argument("--arm", choices=tuple(ARMS))
    parser.add_argument("--seed", type=int)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--boundary", choices=("staged", "published"))
    args = parser.parse_args()
    run = args.run_directory.resolve()
    os.environ["PYTHONPATH"] = os.pathsep.join((str(ROOT / "src"), str(ROOT)))
    if sys.version_info[:2] != (3, 14):
        parser.error("CPython 3.14 is required")
    if args.mode != "interrupt-writer":
        signal.signal(signal.SIGTERM, stop_handler)
        signal.signal(signal.SIGINT, stop_handler)
    if args.mode == "run":
        if not run.is_relative_to((ROOT / "experiments/results").resolve()):
            parser.error("run directory must be inside this checkout's experiments/results")
        with controller_lock(run):
            run_controller(run, args.profile, args.development, args.reviewed_commit)
    elif args.mode == "cell":
        cell_worker(run, args.arm, args.seed)
    elif args.mode == "calibrate":
        calibration_worker(run)
    elif args.mode == "resume-check":
        resume_worker(run, args.arm, args.checkpoint, args.output)
    elif args.mode == "evaluate":
        evaluation_worker(run)
    elif args.mode == "observe-memory":
        memory_observer(args.pid, args.output)
    else:
        interrupted_writer(run, args.boundary)


if __name__ == "__main__":
    main()
