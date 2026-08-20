"""Generate canonical own-axis DCFR and literal-response policy objects.

This is deliberately a source-artifact stage.  It solves and serializes finite
policies, exact source-game evaluations, and provenance.  It does not inspect
tensor ranks, select a representation, or impose an equilibrium-quality gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

from .evaluation import EvaluationResult, Policy
from .factorized_belief import FactorizedCardBelief
from .factorized_belief_audit import _derived_seed, _raw_factors, generate_hand_axes
from .public_tree_tensor import PublicTreeTensorEvaluator
from .public_tree_tensor_cfr import PublicTreeTensorCFR
from .real_policy import (
    mean_policy_total_variation,
    policy_digest,
    policy_statistics,
    splice_unilateral_best_response,
)
from .reporting import environment_metadata
from .river import format_card, parse_cards
from .showdown_value_rank_screen import _game_from_belief

_ROOT = Path(__file__).parents[2]
_FAMILIES = ("balanced", "blocker_heavy")
_TARGETS = (0, 1, 2, 3, 4, 5)
_LADDERS = {4: (0, 1, 4, 16, 64, 256), 7: (0, 1, 4, 16, 64)}
_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_river_sha256",
    "expected_multiway_game_sha256",
    "expected_updates_sha256",
    "expected_factorized_belief_sha256",
    "expected_factorized_audit_sha256",
    "expected_public_tree_tensor_sha256",
    "expected_public_tree_tensor_cfr_sha256",
    "expected_real_policy_sha256",
    "expected_source_generator_sha256",
    "board",
    "pot",
    "stack",
    "bet_size",
    "players",
    "hands_per_player",
    "range_families",
    "mixture_components",
    "axis_seed_rule",
    "solver",
    "warm_start_policy",
    "warm_start_regret_mass",
    "solver_output",
    "checkpoint_ladders",
    "best_response_reference_checkpoint",
    "best_response_target_players",
    "rederivation_repeats",
    "canonical_policy_rule",
    "source_quality_authority",
    "gates",
}
_GATE_FIELDS = {
    "maximum_rederivation_policy_error",
    "maximum_best_response_target_value_error",
    "maximum_policy_schema_mismatches",
    "maximum_source_zero_sum_error",
    "require_rederivation_digest_identity",
    "require_all_checkpoint_profiles",
    "require_all_target_response_profiles",
}
_SOURCE_PATHS = {
    "expected_river_sha256": _ROOT / "src" / "pontius" / "river.py",
    "expected_multiway_game_sha256": (
        _ROOT / "src" / "pontius" / "river_multiway.py"
    ),
    "expected_updates_sha256": _ROOT / "src" / "pontius" / "updates.py",
    "expected_factorized_belief_sha256": (
        _ROOT / "src" / "pontius" / "factorized_belief.py"
    ),
    "expected_factorized_audit_sha256": (
        _ROOT / "src" / "pontius" / "factorized_belief_audit.py"
    ),
    "expected_public_tree_tensor_sha256": (
        _ROOT / "src" / "pontius" / "public_tree_tensor.py"
    ),
    "expected_public_tree_tensor_cfr_sha256": (
        _ROOT / "src" / "pontius" / "public_tree_tensor_cfr.py"
    ),
    "expected_real_policy_sha256": _ROOT / "src" / "pontius" / "real_policy.py",
    "expected_source_generator_sha256": (
        _ROOT / "src" / "pontius" / "real_policy_source.py"
    ),
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen source is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_real_policy_source_config(config: dict[str, Any]) -> dict[str, Any]:
    """Strictly parse the preregistered own-axis policy-source contract."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "real-policy source fields differ from ADR-0074: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    if config["evidence_stage"] != "preregistered_revealed_source_artifact":
        raise ValueError("real-policy source must remain preregistered and revealed")
    if config["seed"] != 20260819:
        raise ValueError("real-policy source seed differs from ADR-0074")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")

    frozen = {
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "hands_per_player": [4, 7],
        "range_families": list(_FAMILIES),
        "mixture_components": 3,
        "axis_seed_rule": "ADR0067_public_policy_root_axis",
        "solver": "dcfr",
        "warm_start_policy": "uniform",
        "warm_start_regret_mass": 1.0,
        "solver_output": "average_strategy",
        "checkpoint_ladders": {str(key): list(value) for key, value in _LADDERS.items()},
        "best_response_reference_checkpoint": 16,
        "best_response_target_players": list(_TARGETS),
        "rederivation_repeats": 2,
        "canonical_policy_rule": "sorted_information_keys_actions_json_float64",
        "source_quality_authority": "metadata_only_never_a_gate_or_selector",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("real-policy source execution contract differs from ADR-0074")

    gates = config["gates"]
    if not isinstance(gates, dict) or set(gates) != _GATE_FIELDS:
        raise ValueError("real-policy source gates differ from ADR-0074")
    expected_gates = {
        "maximum_rederivation_policy_error": 1e-12,
        "maximum_best_response_target_value_error": 1e-10,
        "maximum_policy_schema_mismatches": 0,
        "maximum_source_zero_sum_error": 1e-10,
        "require_rederivation_digest_identity": True,
        "require_all_checkpoint_profiles": True,
        "require_all_target_response_profiles": True,
    }
    if gates != expected_gates:
        raise ValueError("real-policy source gates differ from ADR-0074")
    return {
        **config,
        "hands_per_player": tuple(config["hands_per_player"]),
        "range_families": tuple(config["range_families"]),
        "best_response_target_players": tuple(config["best_response_target_players"]),
        "checkpoint_ladders": {
            int(key): tuple(value) for key, value in config["checkpoint_ladders"].items()
        },
        "gates": dict(gates),
    }


def _json_policy(policy: Policy) -> dict[str, dict[str, float]]:
    return {
        key: {
            str(action): float(probability)
            for action, probability in sorted(distribution.items())
        }
        for key, distribution in sorted(policy.items())
    }


def _evaluation_json(result: EvaluationResult) -> dict[str, object]:
    return {
        "utilities": list(result.utilities),
        "best_response_values": list(result.best_response_values),
        "deviation_gains": list(result.deviation_gains),
        "nash_conv": result.nash_conv,
        "exploitability": result.exploitability,
    }


def _maximum_policy_error(first: Policy, second: Policy) -> float:
    if set(first) != set(second):
        return math.inf
    maximum = 0.0
    for key in first:
        if set(first[key]) != set(second[key]):
            return math.inf
        maximum = max(
            maximum,
            *(abs(first[key][action] - second[key][action]) for action in first[key]),
        )
    return maximum


def _schema_mismatches(
    policy: Policy,
    schema: dict[str, tuple[str, ...]],
) -> int:
    mismatches = len(set(policy) ^ set(schema))
    for key in set(policy) & set(schema):
        mismatches += int(set(policy[key]) != set(schema[key]))
    return mismatches


def _checkpoint_policies(
    layout: PublicTreeTensorEvaluator,
    *,
    checkpoints: tuple[int, ...],
    regret_mass: float,
) -> tuple[
    dict[int, Policy],
    list[dict[str, float | int]],
    float,
    int,
]:
    """Solve once, replay once, and return primary average policies."""

    primary = PublicTreeTensorCFR(layout, "dcfr")
    primary.warm_start({}, regret_mass)
    policies: dict[int, Policy] = {}
    timing_rows: list[dict[str, float | int]] = []
    previous = 0
    for checkpoint in checkpoints:
        started = time.perf_counter()
        primary.run(checkpoint - previous)
        policies[checkpoint] = primary.average_strategy()
        timing_rows.append(
            {
                "checkpoint": checkpoint,
                "iterations_since_previous": checkpoint - previous,
                "solve_ms_since_previous": (time.perf_counter() - started) * 1000.0,
            }
        )
        previous = checkpoint

    replay = PublicTreeTensorCFR(layout, "dcfr")
    replay.warm_start({}, regret_mass)
    maximum_error = 0.0
    digest_mismatches = 0
    previous = 0
    for checkpoint in checkpoints:
        replay.run(checkpoint - previous)
        reproduced = replay.average_strategy()
        maximum_error = max(
            maximum_error,
            _maximum_policy_error(policies[checkpoint], reproduced),
        )
        digest_mismatches += int(
            policy_digest(policies[checkpoint]) != policy_digest(reproduced)
        )
        previous = checkpoint
    return policies, timing_rows, maximum_error, digest_mismatches


def solve_policy_geometry(
    layout: PublicTreeTensorEvaluator,
    *,
    geometry_id: str,
    checkpoints: tuple[int, ...],
    regret_mass: float,
    response_checkpoint: int,
    response_targets: tuple[int, ...],
) -> dict[str, object]:
    """Create all canonical average and unilateral-response profiles."""

    if not checkpoints or checkpoints[0] != 0 or tuple(sorted(set(checkpoints))) != checkpoints:
        raise ValueError("checkpoints must be unique, increasing, and start at zero")
    if response_checkpoint not in checkpoints:
        raise ValueError("response checkpoint must be present in the ladder")
    if any(target not in range(layout.num_players) for target in response_targets):
        raise ValueError("response target lies outside the player range")

    policies, timing_rows, replay_error, digest_mismatches = _checkpoint_policies(
        layout,
        checkpoints=checkpoints,
        regret_mass=regret_mass,
    )
    schema = layout.information_schema()
    profiles: list[dict[str, object]] = []
    evaluations = {}
    evaluation_times = {}
    schema_mismatches = 0
    maximum_zero_sum_error = 0.0
    for checkpoint in checkpoints:
        policy = policies[checkpoint]
        started = time.perf_counter()
        detailed = layout.evaluate(policy)
        evaluation_times[checkpoint] = (time.perf_counter() - started) * 1000.0
        evaluations[checkpoint] = detailed
        schema_mismatches += _schema_mismatches(policy, schema)
        maximum_zero_sum_error = max(
            maximum_zero_sum_error,
            abs(math.fsum(detailed.evaluation.utilities)),
        )
        profile_id = f"{geometry_id}|dcfr_average|checkpoint={checkpoint}"
        profiles.append(
            {
                "profile_id": profile_id,
                "provenance": {
                    "kind": "dcfr_average",
                    "checkpoint": checkpoint,
                    "iteration_zero_uses_current_policy_fallback": checkpoint == 0,
                },
                "policy_sha256": policy_digest(policy),
                "statistics": policy_statistics(policy),
                "exact_source_evaluation": _evaluation_json(detailed.evaluation),
                "policy": _json_policy(policy),
            }
        )

    baseline = policies[response_checkpoint]
    baseline_result = evaluations[response_checkpoint]
    maximum_response_error = 0.0
    for target in response_targets:
        candidate = splice_unilateral_best_response(
            layout=layout,
            hands_by_player=layout.hands_by_player,
            baseline=baseline,
            target_player=target,
            best_response_actions=baseline_result.best_response_actions[target],
        )
        started = time.perf_counter()
        detailed = layout.evaluate(candidate)
        response_evaluation_ms = (time.perf_counter() - started) * 1000.0
        target_error = abs(
            detailed.evaluation.utilities[target]
            - baseline_result.evaluation.best_response_values[target]
        )
        maximum_response_error = max(maximum_response_error, target_error)
        maximum_zero_sum_error = max(
            maximum_zero_sum_error,
            abs(math.fsum(detailed.evaluation.utilities)),
        )
        schema_mismatches += _schema_mismatches(candidate, schema)
        profile_id = f"{geometry_id}|literal_br|target={target}|against={response_checkpoint}"
        profiles.append(
            {
                "profile_id": profile_id,
                "provenance": {
                    "kind": "literal_unilateral_best_response",
                    "target_player": target,
                    "against_checkpoint": response_checkpoint,
                    "dispatch_product": "explicit_public_state_or_policy_tape",
                },
                "policy_sha256": policy_digest(candidate),
                "statistics": policy_statistics(candidate),
                "exact_source_evaluation": _evaluation_json(detailed.evaluation),
                "best_response_target_value_error": target_error,
                "evaluation_ms": response_evaluation_ms,
                "policy": _json_policy(candidate),
            }
        )

    consecutive_tv = [
        {
            "from_checkpoint": left,
            "to_checkpoint": right,
            "mean_information_set_total_variation": mean_policy_total_variation(
                policies[left], policies[right]
            ),
        }
        for left, right in zip(checkpoints[:-1], checkpoints[1:], strict=True)
    ]
    return {
        "profiles": profiles,
        "checkpoint_timing_rows": timing_rows,
        "checkpoint_evaluation_ms": {
            str(key): value for key, value in evaluation_times.items()
        },
        "consecutive_checkpoint_tv": consecutive_tv,
        "maximum_rederivation_policy_error": replay_error,
        "rederivation_digest_mismatches": digest_mismatches,
        "maximum_best_response_target_value_error": maximum_response_error,
        "policy_schema_mismatches": schema_mismatches,
        "maximum_source_zero_sum_error": maximum_zero_sum_error,
    }


def run_real_policy_source(config: dict[str, Any]) -> dict[str, object]:
    """Execute the frozen own-axis policy artifact generation."""

    parsed = parse_real_policy_source_config(config)
    started = time.perf_counter()
    board = parse_cards(*parsed["board"])
    geometries: list[dict[str, object]] = []
    maximum_replay_error = 0.0
    digest_mismatches = 0
    maximum_response_error = 0.0
    schema_mismatches = 0
    maximum_zero_sum_error = 0.0
    checkpoint_profiles = 0
    response_profiles = 0

    for hand_count in parsed["hands_per_player"]:
        for family in parsed["range_families"]:
            geometry_started = time.perf_counter()
            axis_seed = _derived_seed(
                parsed["seed"],
                "public-policy-root-axis",
                hand_count,
                family,
            )
            axes = generate_hand_axes(
                board=board,
                players=parsed["players"],
                hands_per_player=hand_count,
                family=family,
                seed=axis_seed,
            )
            mixture, unaries = _raw_factors(
                hands_by_player=axes,
                components=parsed["mixture_components"],
                seed=axis_seed,
                family=family,
            )
            belief = FactorizedCardBelief(
                hands_by_player=axes,
                mixture_weights=mixture,
                unary_weights=unaries,
                board=board,
            )
            game_started = time.perf_counter()
            game = _game_from_belief(
                belief=belief,
                pot=parsed["pot"],
                stack=parsed["stack"],
                bet_size=parsed["bet_size"],
            )
            game_ms = (time.perf_counter() - game_started) * 1000.0
            layout_started = time.perf_counter()
            layout = PublicTreeTensorEvaluator(game)
            layout_ms = (time.perf_counter() - layout_started) * 1000.0
            geometry_id = f"h{hand_count}|{family}"
            solved = solve_policy_geometry(
                layout,
                geometry_id=geometry_id,
                checkpoints=parsed["checkpoint_ladders"][hand_count],
                regret_mass=parsed["warm_start_regret_mass"],
                response_checkpoint=parsed["best_response_reference_checkpoint"],
                response_targets=parsed["best_response_target_players"],
            )
            profiles = solved["profiles"]
            assert isinstance(profiles, list)
            checkpoint_profiles += len(parsed["checkpoint_ladders"][hand_count])
            response_profiles += len(parsed["best_response_target_players"])
            maximum_replay_error = max(
                maximum_replay_error,
                float(solved["maximum_rederivation_policy_error"]),
            )
            digest_mismatches += int(solved["rederivation_digest_mismatches"])
            maximum_response_error = max(
                maximum_response_error,
                float(solved["maximum_best_response_target_value_error"]),
            )
            schema_mismatches += int(solved["policy_schema_mismatches"])
            maximum_zero_sum_error = max(
                maximum_zero_sum_error,
                float(solved["maximum_source_zero_sum_error"]),
            )
            geometries.append(
                {
                    "geometry_id": geometry_id,
                    "hands_per_player": hand_count,
                    "range_family": family,
                    "axis_seed": axis_seed,
                    "hand_axes": [
                        [
                            [format_card(hand[0]), format_card(hand[1])]
                            for hand in hands
                        ]
                        for hands in layout.hands_by_player
                    ],
                    "joint_deals": layout.deal_count,
                    "game_structural_digest": game.structural_digest,
                    "game_provenance_digest": game.provenance_digest,
                    "public_nodes": layout.public_node_count,
                    "terminal_nodes": layout.terminal_node_count,
                    "information_sets": len(layout.information_schema()),
                    "layout_memory": layout.memory_summary(),
                    "solver_memory": PublicTreeTensorCFR(layout, "dcfr").memory_summary(),
                    "game_materialization_ms": game_ms,
                    "layout_compile_ms": layout_ms,
                    "geometry_wall_ms": (time.perf_counter() - geometry_started) * 1000.0,
                    **solved,
                }
            )

    expected_checkpoint_profiles = sum(
        len(parsed["checkpoint_ladders"][hand_count])
        * len(parsed["range_families"])
        for hand_count in parsed["hands_per_player"]
    )
    expected_response_profiles = (
        len(parsed["hands_per_player"])
        * len(parsed["range_families"])
        * len(parsed["best_response_target_players"])
    )
    gates = parsed["gates"]
    gate_results = {
        "rederivation_policy_identity": (
            maximum_replay_error <= gates["maximum_rederivation_policy_error"]
        ),
        "rederivation_digest_identity": (
            digest_mismatches == 0
            if gates["require_rederivation_digest_identity"]
            else True
        ),
        "best_response_target_value_identity": (
            maximum_response_error
            <= gates["maximum_best_response_target_value_error"]
        ),
        "policy_schema_identity": (
            schema_mismatches <= gates["maximum_policy_schema_mismatches"]
        ),
        "source_zero_sum_identity": (
            maximum_zero_sum_error <= gates["maximum_source_zero_sum_error"]
        ),
        "all_checkpoint_profiles": (
            checkpoint_profiles == expected_checkpoint_profiles
            if gates["require_all_checkpoint_profiles"]
            else True
        ),
        "all_target_response_profiles": (
            response_profiles == expected_response_profiles
            if gates["require_all_target_response_profiles"]
            else True
        ),
    }
    return {
        "schema_version": 1,
        "artifact_type": "canonical_own_axis_real_policy_source",
        "status": "preregistered_revealed_source_artifact_only",
        "config": parsed,
        "config_sha256": _sha256(
            _ROOT / "experiments" / "configs" / "real-policy-source-v1.json"
        ),
        "implementation_sha256": _sha256(
            _ROOT / "src" / "pontius" / "real_policy_source.py"
        ),
        "environment": environment_metadata(),
        "counts": {
            "geometries": len(geometries),
            "checkpoint_profiles": checkpoint_profiles,
            "unilateral_response_profiles": response_profiles,
            "total_policy_profiles": checkpoint_profiles + response_profiles,
        },
        "aggregate": {
            "maximum_rederivation_policy_error": maximum_replay_error,
            "rederivation_digest_mismatches": digest_mismatches,
            "maximum_best_response_target_value_error": maximum_response_error,
            "policy_schema_mismatches": schema_mismatches,
            "maximum_source_zero_sum_error": maximum_zero_sum_error,
        },
        "gates": {"results": gate_results, "passed": all(gate_results.values())},
        "timing": {"wall_seconds": time.perf_counter() - started},
        "geometries": geometries,
        "limitations": [
            "NashConv and every source-quality statistic are metadata, never a gate.",
            "Checkpoint zero is the uniform current-policy fallback before any average contribution.",
            "A finite six-player DCFR trajectory has no two-player convergence guarantee.",
            "These selected hand axes are representation probes, not full 1,081-combo ranges.",
            "Literal unilateral responses certify source-game deviations, not coalition safety.",
        ],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_real_policy_source(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "real-policy source: "
        f"profiles={result['counts']['total_policy_profiles']}, "
        f"replay_error={result['aggregate']['maximum_rederivation_policy_error']:.3g}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
