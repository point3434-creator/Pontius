"""Reproducible command-line runner for exact-game solver experiments."""

from __future__ import annotations

import argparse
import json
import platform
import random
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .cfr import TabularCFR
from .evaluation import Policy, evaluate_profile
from .kuhn import KuhnPoker


def _git_metadata() -> dict[str, Any]:
    def run(*arguments: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *arguments],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            return None
        return result.stdout.strip()

    return {
        "commit": run("rev-parse", "HEAD") or "unborn",
        "dirty": bool(run("status", "--porcelain")),
    }


def _json_policy(policy: Policy) -> dict[str, dict[str, float]]:
    return {
        key: {str(action): probability for action, probability in distribution.items()}
        for key, distribution in policy.items()
    }


def run_experiment(config: dict[str, Any]) -> dict[str, Any]:
    game_name = str(config.get("game", "kuhn2"))
    solver_name = str(config.get("solver", "cfr"))
    iterations = int(config.get("iterations", 20_000))
    report_every = int(config.get("report_every", max(1, iterations // 10)))
    seed = int(config.get("seed", 0))

    if not game_name.startswith("kuhn") or not game_name[4:].isdigit():
        raise ValueError(f"unsupported game {game_name!r}")
    num_players = int(game_name[4:])
    if not 2 <= num_players <= 6:
        raise ValueError(f"unsupported game {game_name!r}")
    if solver_name not in {"cfr", "lcfr", "cfr_plus", "dcfr"}:
        raise ValueError(f"unsupported solver {solver_name!r}")
    if iterations <= 0 or report_every <= 0:
        raise ValueError("iterations and report_every must be positive")

    random.seed(seed)
    game = KuhnPoker(num_players)
    solver = TabularCFR(game, variant=solver_name)  # type: ignore[arg-type]
    trace: list[dict[str, Any]] = []
    experiment_start = time.perf_counter()
    solver_seconds = 0.0
    trace_evaluation_seconds = 0.0

    while solver.iteration < iterations:
        batch_size = min(report_every, iterations - solver.iteration)
        batch_start = time.perf_counter()
        solver.run(batch_size)
        solver_seconds += time.perf_counter() - batch_start

        trace_evaluation_start = time.perf_counter()
        evaluation = evaluate_profile(game, solver.average_strategy())
        trace_evaluation_seconds += time.perf_counter() - trace_evaluation_start
        trace.append(
            {
                "iteration": solver.iteration,
                "solver_seconds": solver_seconds,
                "nash_conv": evaluation.nash_conv,
                "exploitability": evaluation.exploitability,
                "utilities": list(evaluation.utilities),
            }
        )

    evaluation_start = time.perf_counter()
    average_policy = solver.average_strategy()
    current_policy = solver.current_strategy()
    average_evaluation = evaluate_profile(game, average_policy)
    current_evaluation = evaluate_profile(game, current_policy)
    final_evaluation_seconds = time.perf_counter() - evaluation_start
    wall_seconds = time.perf_counter() - experiment_start

    return {
        "schema_version": 1,
        "config": {
            "game": game_name,
            "solver": solver_name,
            "iterations": iterations,
            "report_every": report_every,
            "seed": seed,
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "git": _git_metadata(),
        },
        "timing": {
            "solver_seconds": solver_seconds,
            "trace_evaluation_seconds": trace_evaluation_seconds,
            "final_evaluation_seconds": final_evaluation_seconds,
            "wall_seconds": wall_seconds,
        },
        "solver": {
            "information_sets": len(solver.information_sets),
            "iterations": solver.iteration,
        },
        "average": {
            **asdict(average_evaluation),
            "policy": _json_policy(average_policy),
        },
        "current": {
            **asdict(current_evaluation),
            "policy": _json_policy(current_policy),
        },
        "trace": trace,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="JSON configuration file")
    parser.add_argument("--game", choices=[f"kuhn{players}" for players in range(2, 7)])
    parser.add_argument("--solver", choices=["cfr", "lcfr", "cfr_plus", "dcfr"])
    parser.add_argument("--iterations", type=int)
    parser.add_argument("--report-every", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config: dict[str, Any] = {}
    if args.config is not None:
        config = json.loads(args.config.read_text(encoding="utf-8"))
    for name in ("game", "solver", "iterations", "report_every", "seed"):
        value = getattr(args, name)
        if value is not None:
            config[name] = value

    result = run_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    average = result["average"]
    timing = result["timing"]
    exploitability = average["exploitability"]
    optional_metric = (
        f", exploitability={exploitability:.8f}" if exploitability is not None else ""
    )
    print(
        f"{result['config']['solver']} on {result['config']['game']}: "
        f"iterations={result['config']['iterations']}, "
        f"solver={timing['solver_seconds']:.3f}s, "
        f"value_p0={average['utilities'][0]:.8f}, "
        f"nash_conv={average['nash_conv']:.8f}"
        f"{optional_metric}"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
