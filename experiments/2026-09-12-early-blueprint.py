"""Does a bounded early-street MCCFR reference preserve state and learn coverage?

Small local feasibility/continuation-sensitivity experiment, not a strength or
full-scale throughput claim. Run with PYTHONPATH=src and CPython 3.14. Defaults
are bounded; each named generation and the whole run directory are immutable.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import statistics
import sys
import time

from pontius.early_holdem import EarlyHoldemGame, EarlyHoldemState
from pontius.execution import begin_run, finish_run
from pontius.game import TERMINAL_PLAYER
from pontius.no_limit_betting import BettingStreet
from pontius.sampled_cfr import ExternalSamplingCFR, SamplingLimit
from pontius.training_checkpoint import load_checkpoint, save_checkpoint


def row_coverage(trainer):
    counts = Counter()
    for key, row in trainer.rows.items():
        street = json.loads(key)["public"]["street"]
        counts[f"{street}_rows"] += 1
        counts[f"{street}_actions"] += len(row.actions)
        if row.average_visits:
            counts[f"{street}_averaged"] += 1
            total = sum(row.strategy_sum)
            if max(row.strategy_sum) - min(row.strategy_sum) > 1e-12 * total:
                counts[f"{street}_nonuniform"] += 1
        if row.average_visits > 1:
            counts[f"{street}_repeat_averaged"] += 1
    return dict(counts)


def public_preflop_count(stack_bb, max_raises, limit=20_000):
    """Count public decision nodes and action slots up to a stated hard cap."""
    game = EarlyHoldemGame(stack_bb, max_raises)
    pending = [game.sample_root(random.Random(0))]
    nodes = slots = leaves = 0
    while pending and nodes < limit:
        state = pending.pop()
        if state.current_player == TERMINAL_PLAYER or state.betting.street == BettingStreet.FLOP:
            leaves += 1
            continue
        actions = state.legal_actions()
        nodes += 1
        slots += len(actions)
        pending.extend(state.apply_action(action) for action in actions)
    return dict(stack_bb=stack_bb, max_raises=max_raises, public_decisions=nodes,
                public_action_slots=slots, boundary_leaves=leaves, complete=not pending,
                cap=limit, raw_fp64_accumulator_bytes_if_169_per_node=slots * 169 * 16)


def choose_action(state, target, source_game, policy, rng, opponent, coverage):
    actions = state.legal_actions()
    if state.current_player != target:
        if opponent == "uniform":
            return rng.choice(actions)
        return "check" if "check" in actions else "call"
    # Transfer ONLY across the two continuation controls. Public/action/card
    # abstractions and stack depth are identical; retain the training key identity.
    view = EarlyHoldemState(source_game, state.deal, state.betting)
    key = view.information_state_key(target)
    row = policy.get(key)
    street = state.betting.street.value
    if row is None:
        coverage[f"{street}_missing"] += 1
        return "check" if "check" in actions else "call"
    weights, visits = row
    if tuple(weights) != actions:
        raise ValueError("policy action menu mismatch")
    coverage[f"{street}_{'averaged_hit' if visits else 'unaveraged_hit'}"] += 1
    return rng.choices(actions, tuple(weights.values()), k=1)[0]


def play(game, deal, target, source_game, policy, action_seed, opponent, coverage):
    state = game.state_for(deal, game.sample_root(random.Random(0)).betting)
    # Per-seat streams keep common random action choices aligned where possible.
    randoms = [random.Random(action_seed + 104729 * player) for player in range(6)]
    while state.current_player != TERMINAL_PLAYER:
        action = choose_action(state, target, source_game, policy,
                               randoms[state.current_player], opponent, coverage)
        state = state.apply_action(action)
    return state.returns()[target]


def evaluate(trainer, source_game, deals, seed):
    probabilities = trainer.average_policy()
    policy = {key: (weights, trainer.rows[key].average_visits)
              for key, weights in probabilities.items()}
    results = []
    for continuation in ("check_call", "showdown_betting"):
        game = EarlyHoldemGame(source_game.stack_bb, source_game.max_raises, continuation)
        for opponent in ("passive", "uniform"):
            deck_rng = random.Random(seed)
            blocks = []
            coverage = Counter()
            raw = []
            for block in range(deals):
                deal = game.sample_root(deck_rng).deal
                differences = []
                for target in range(6):
                    action_seed = seed + 1000003 * block + 7919 * target
                    candidate = play(game, deal, target, source_game, policy,
                                     action_seed, opponent, coverage)
                    baseline = play(game, deal, target, source_game, {},
                                    action_seed, opponent, Counter())
                    differences.append(candidate - baseline)
                    raw.append([block, target, candidate, baseline])
                blocks.append(statistics.mean(differences))
            mean = statistics.mean(blocks)
            half_width = 1.96 * statistics.stdev(blocks) / math.sqrt(len(blocks))
            results.append(dict(
                continuation=continuation, opponent=opponent, independent_deal_blocks=deals,
                candidate_hands=6 * deals, baseline="empty-table-passive-fallback",
                mean_difference_bb_per_hand=mean,
                approximate_95pct_normal_ci=[mean - half_width, mean + half_width],
                coverage=dict(coverage), raw_paired_returns=raw,
                limitation=("Exploratory normal CI over deal blocks; "
                            "small fixed panel, no strength claim"),
            ))
    return results


def train_cell(directory, game, variant, args):
    trainer = ExternalSamplingCFR(
        6, game.sample_root, game.game_id, variant=variant, seed=args.seed,
        max_rows=args.max_rows, max_nodes=args.max_nodes,
    )
    save_checkpoint(directory, trainer.state_dict(), "milestone-000000")
    started = time.perf_counter()
    stop = "iteration_budget"
    milestones = []
    for index in range(args.iterations):
        if time.perf_counter() - started >= args.seconds_per_cell:
            stop = "time_budget_at_iteration_boundary"
            break
        try:
            trainer.step()
        except SamplingLimit as error:
            stop = str(error)
            break
        if index + 1 == args.iterations // 2:
            name = f"milestone-{trainer.iterations:06d}"
            save_checkpoint(directory, trainer.state_dict(), name)
            milestones.append(name)
    elapsed = time.perf_counter() - started
    if trainer.iterations:
        name = f"milestone-{trainer.iterations:06d}"
        if name not in milestones:
            save_checkpoint(directory, trainer.state_dict(), name)
            milestones.append(name)
    persisted = load_checkpoint(directory, expected_identity=trainer.identity)
    snapshot = trainer.state_dict()
    if snapshot != persisted:
        raise AssertionError("complete state changed across checkpoint storage")
    uninterrupted = ExternalSamplingCFR.from_state(snapshot, game.sample_root, game.game_id)
    restarted = ExternalSamplingCFR.from_state(persisted, game.sample_root, game.game_id)
    resume_steps = 0
    resume_stop = None
    for _ in range(3):
        outcomes = []
        for candidate in (uninterrupted, restarted):
            try:
                candidate.step()
                outcomes.append(None)
            except SamplingLimit as error:
                outcomes.append(str(error))
        if outcomes[0] != outcomes[1] or uninterrupted.state_dict() != restarted.state_dict():
            raise AssertionError("serial continuation after resume diverged")
        if outcomes[0] is not None:
            resume_stop = outcomes[0]
            break
        resume_steps += 1
    policy = dict(format="pontius-early-policy-reference-v1", identity=trainer.identity,
                  game_id=game.game_id, variant=variant, iterations=trainer.iterations,
                  probabilities=trainer.average_policy(), missing_policy="check/call",
                  unaveraged_policy="uniform", quantized=False)
    policy_path = directory / "policy.json"
    raw = json.dumps(policy, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    policy_path.write_bytes(raw)
    result = dict(
        variant=variant, continuation=game.continuation, stack_bb=game.stack_bb,
        game_id=game.game_id, identity=trainer.identity, completed_iterations=trainer.iterations,
        stop=stop, seconds_including_midpoint_checkpoint=elapsed, visited_nodes=trainer.total_nodes,
        rows=len(trainer.rows), coverage=row_coverage(trainer),
        resumed_steps_identically=resume_steps, resume_stop=resume_stop,
        checkpoint_bytes=sum(path.stat().st_size for path in directory.rglob("checkpoint.json")),
        policy_bytes=len(raw), policy_sha256=hashlib.sha256(raw).hexdigest(),
        permanent_milestones=["milestone-000000", *milestones],
    )
    result["evaluation"] = evaluate(trainer, game, args.evaluation_deals, args.seed + 999983)
    compact = {key: value for key, value in result.items() if key != "evaluation"}
    print(json.dumps(compact), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--evaluation-deals", type=int, default=32)
    parser.add_argument("--stack-bb", type=int, default=100)
    parser.add_argument("--max-rows", type=int, default=20_000)
    parser.add_argument("--max-nodes", type=int, default=100_000)
    parser.add_argument("--seconds-per-cell", type=float, default=60)
    parser.add_argument("--seed", type=int, default=20260912)
    args = parser.parse_args()
    if args.iterations < 2 or args.evaluation_deals < 2 or args.seconds_per_cell <= 0:
        parser.error("require >=2 iterations, >=2 evaluation deals, positive seconds")
    root = Path(__file__).resolve().parents[1]
    name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S-%f-early-blueprint")
    run = root / "experiments/results/runs" / name
    run.mkdir(parents=True, exist_ok=False)
    context = begin_run(root, allow_working_tree=True)
    context["output_directory"] = str(run.relative_to(root))
    started = time.perf_counter()
    report = dict(status="running", parameters=vars(args), python=sys.version,
                  platform=platform.platform(), cells=[], public_tree_counts=[],
                  experiment_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    try:
        for depth in (20, 100, 200):
            report["public_tree_counts"].append(public_preflop_count(depth, 1))
        for continuation in ("check_call", "showdown_betting"):
            game = EarlyHoldemGame(args.stack_bb, 1, continuation)
            for variant in ("cfr", "linear"):
                report["cells"].append(train_cell(run / f"{continuation}-{variant}",
                                                   game, variant, args))
        report.update(status="passed", summary=(
            "Four bounded early-street training cells; checkpoint round trips and serial "
            "resumes matched; sparse-coverage paired evaluation, no poker-strength claim."
        ))
    except Exception as error:
        report.update(status="failed", failure_reason=f"{type(error).__name__}: {error}")
        raise
    finally:
        finish_run(context, " ".join(sys.argv), report, time.perf_counter() - started)
        print(f"Result: {run / 'result.json'}", flush=True)


if __name__ == "__main__":
    main()
