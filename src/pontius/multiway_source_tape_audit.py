"""Audit exact source-compiled range-plus-policy reuse in multiway river."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from .cfr import TabularCFR
from .coalition import (
    CoalitionEvaluationResult,
    assess_multiplayer_candidate,
    evaluate_coalition_threats,
)
from .dependency_tape import CompiledPolicyDeltaTape, DependencyTapeResult
from .evaluation import EvaluationResult, Policy, best_response, evaluate_profile
from .game import Action
from .multiway_river_context import (
    MultiwayRangeTarget,
    MultiwayRiverContext,
    generate_multiway_river_contexts,
    make_multiway_range_targets,
)
from .multiway_search_experiment import (
    _solve_source_blueprint,
    parse_multiway_search_config,
)
from .reporting import environment_metadata

_ROOT = Path(__file__).parents[2]
_CONFIG_FIELDS = {
    "evidence_stage",
    "source_config",
    "source_config_sha256",
    "source_artifact",
    "source_artifact_sha256",
    "expected_search_runner_sha256",
    "expected_context_generator_sha256",
    "expected_multiway_game_sha256",
    "expected_coalition_evaluator_sha256",
    "expected_dependency_tape_sha256",
    "included_splits",
    "expected_groups",
    "expected_contexts",
    "expected_targets",
    "expected_candidate_records",
    "source_compile_scope",
    "target_control_compile_scope",
    "source_outcome_universe",
    "candidate_scope",
    "execution_mode",
    "call_order_sentinel",
    "timing_repeats",
    "primary_break_even_maximum_reuses",
    "gates",
}
_GATE_FIELDS = {
    "maximum_evaluation_error",
    "maximum_metric_reproduction_error",
    "maximum_best_response_action_mismatches",
    "maximum_acceptance_label_mismatches",
    "maximum_call_order_replay_error",
    "require_exact_call_order_action_replay",
    "require_identical_policy_schema",
    "require_support_preservation",
    "source_reuse_path_strictly_faster_than_target_compile_path",
    "source_precompiled_path_strictly_faster_than_ordinary_path",
    "primary_precompiled_rate_strictly_beats_blind",
    "maximum_persisted_tape_byte_ratio",
}
_FROZEN_PATHS = {
    "source_config": (
        "experiments/configs/multiway-river-search-acceptance-development-v1.json"
    ),
    "source_artifact": (
        "experiments/results/multiway-river-search-acceptance-development-v1.json"
    ),
}
_SOURCE_PATHS = {
    "expected_search_runner_sha256": (
        _ROOT / "src" / "pontius" / "multiway_search_experiment.py"
    ),
    "expected_context_generator_sha256": (
        _ROOT / "src" / "pontius" / "multiway_river_context.py"
    ),
    "expected_multiway_game_sha256": (
        _ROOT / "src" / "pontius" / "river_multiway.py"
    ),
    "expected_coalition_evaluator_sha256": (
        _ROOT / "src" / "pontius" / "coalition.py"
    ),
    "expected_dependency_tape_sha256": (
        _ROOT / "src" / "pontius" / "dependency_tape.py"
    ),
}
_ACCEPTANCE_ARMS = (
    "aggregate_exact",
    "unilateral_pareto",
    "coalition_stress",
)


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _finite_nonnegative(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be finite and nonnegative")
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be finite and nonnegative") from error
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return result


def parse_source_tape_audit_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "source-tape audit fields differ from the frozen schema: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    if config["evidence_stage"] != "revealed_multiway_engineering_audit":
        raise ValueError("source-tape audit must remain revealed engineering")

    for field, expected in _FROZEN_PATHS.items():
        if config[field] != expected:
            raise ValueError(f"{field} differs from the frozen input path")
        if Path(str(config[field])).is_absolute():
            raise ValueError(f"{field} must be workspace-relative")
    for field in (
        "source_config_sha256",
        "source_artifact_sha256",
        *_SOURCE_PATHS,
    ):
        if not _is_sha256(config[field]):
            raise ValueError(f"{field} must be a lowercase SHA-256")
    for field, path in _SOURCE_PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"frozen source hash mismatch for {field}")

    if tuple(config["included_splits"]) != ("development",):
        raise ValueError("the audit may materialize only development")
    expected_counts = (
        config["expected_groups"],
        config["expected_contexts"],
        config["expected_targets"],
        config["expected_candidate_records"],
    )
    if expected_counts != (6, 24, 96, 1728):
        raise ValueError("audit counts differ from ADR-0057")
    frozen_strings = {
        "source_compile_scope": "one_per_context",
        "target_control_compile_scope": "one_per_target",
        "source_outcome_universe": "source_support_only",
        "candidate_scope": "all_frozen_solver_checkpoints",
        "execution_mode": "dense",
        "call_order_sentinel": (
            "first_target_primary_candidate_after_all_context_calls"
        ),
    }
    if any(config[field] != value for field, value in frozen_strings.items()):
        raise ValueError("source-tape audit execution scope differs from ADR-0057")
    if config["timing_repeats"] != 1:
        raise ValueError("stateful source-tape audit requires one timing repeat")
    if config["primary_break_even_maximum_reuses"] != 8:
        raise ValueError("primary break-even curve is frozen through eight reuses")

    raw_gates = config["gates"]
    if not isinstance(raw_gates, dict) or set(raw_gates) != _GATE_FIELDS:
        raise ValueError("source-tape audit gates differ from ADR-0057")
    gates = dict(raw_gates)
    gates["maximum_evaluation_error"] = _finite_nonnegative(
        gates["maximum_evaluation_error"],
        "maximum evaluation error",
    )
    gates["maximum_metric_reproduction_error"] = _finite_nonnegative(
        gates["maximum_metric_reproduction_error"],
        "maximum metric reproduction error",
    )
    gates["maximum_call_order_replay_error"] = _finite_nonnegative(
        gates["maximum_call_order_replay_error"],
        "maximum call-order replay error",
    )
    if gates["maximum_evaluation_error"] > 1e-10:
        raise ValueError("evaluation tolerance exceeds the frozen exactness gate")
    if gates["maximum_metric_reproduction_error"] > 1e-12:
        raise ValueError("metric tolerance exceeds the frozen reproduction gate")
    if gates["maximum_call_order_replay_error"] != 0.0:
        raise ValueError("call-order numerical replay must remain exact")
    for field in (
        "maximum_best_response_action_mismatches",
        "maximum_acceptance_label_mismatches",
    ):
        if isinstance(gates[field], bool) or gates[field] != 0:
            raise ValueError(f"{field} must remain zero")
    boolean_fields = _GATE_FIELDS - {
        "maximum_evaluation_error",
        "maximum_metric_reproduction_error",
        "maximum_best_response_action_mismatches",
        "maximum_acceptance_label_mismatches",
        "maximum_call_order_replay_error",
        "maximum_persisted_tape_byte_ratio",
    }
    if any(gates[field] is not True for field in boolean_fields):
        raise ValueError("all frozen boolean source-tape requirements must be true")
    byte_ratio = _finite_nonnegative(
        gates["maximum_persisted_tape_byte_ratio"],
        "maximum persisted tape byte ratio",
    )
    if byte_ratio != 0.26:
        raise ValueError("persisted tape byte ratio differs from ADR-0057")
    gates["maximum_persisted_tape_byte_ratio"] = byte_ratio

    return {
        **config,
        "included_splits": ("development",),
        "gates": gates,
    }


def _read_frozen(
    root: Path,
    relative_path: str,
    expected_sha256: str,
) -> tuple[dict[str, Any], dict[str, object]]:
    root = root.resolve()
    path = (root / relative_path).resolve()
    if root != path and root not in path.parents:
        raise ValueError("frozen input resolves outside the workspace")
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_sha256:
        raise ValueError(f"frozen input hash mismatch for {relative_path}")
    return json.loads(payload), {
        "path": str(path),
        "sha256": digest,
        "bytes": len(payload),
    }


def _timed(operation: Any) -> tuple[Any, float]:
    start = time.perf_counter()
    result = operation()
    return result, (time.perf_counter() - start) * 1000.0


def _evaluation_values(evaluation: EvaluationResult) -> tuple[float, ...]:
    return (
        *evaluation.utilities,
        *evaluation.best_response_values,
        *evaluation.deviation_gains,
        evaluation.nash_conv,
    )


def _evaluation_error(
    first: EvaluationResult,
    second: EvaluationResult,
) -> float:
    return max(
        abs(left - right)
        for left, right in zip(
            _evaluation_values(first),
            _evaluation_values(second),
            strict=True,
        )
    )


def _action_mismatches(
    candidate: tuple[dict[str, Action], ...],
    reference: tuple[dict[str, Action], ...],
) -> int:
    if len(candidate) != len(reference):
        return abs(len(candidate) - len(reference)) + sum(
            len(actions) for actions in candidate
        ) + sum(len(actions) for actions in reference)
    return sum(
        candidate[player].get(key) != reference[player].get(key)
        for player in range(len(reference))
        for key in set(candidate[player]) | set(reference[player])
    )


def _reference_actions(
    game: Any,
    policy: Policy,
) -> tuple[dict[str, Action], ...]:
    return tuple(
        best_response(game, policy, player)[1]
        for player in range(game.num_players)
    )


def _coalition_values(
    result: CoalitionEvaluationResult,
) -> dict[tuple[int, ...], tuple[float, ...]]:
    return {
        threat.coalition: (
            threat.baseline_value,
            threat.best_response_value,
            threat.deviation_gain,
        )
        for threat in result.threats
    }


def _coalition_error(
    first: CoalitionEvaluationResult,
    second: CoalitionEvaluationResult,
) -> float:
    first_values = _coalition_values(first)
    second_values = _coalition_values(second)
    if first_values.keys() != second_values.keys():
        return math.inf
    return max(
        (
            abs(left - right)
            for coalition in first_values
            for left, right in zip(
                first_values[coalition],
                second_values[coalition],
                strict=True,
            )
        ),
        default=0.0,
    )


def _evaluation_payload_error(
    expected: Mapping[str, Any],
    actual: EvaluationResult,
) -> float:
    expected_values = (
        *map(float, expected["utilities"]),
        *map(float, expected["best_response_values"]),
        *map(float, expected["deviation_gains"]),
        float(expected["nash_conv"]),
    )
    error = max(
        abs(left - right)
        for left, right in zip(
            expected_values,
            _evaluation_values(actual),
            strict=True,
        )
    )
    expected_exploitability = expected.get("exploitability")
    if expected_exploitability is None:
        return error if actual.exploitability is None else math.inf
    if actual.exploitability is None:
        return math.inf
    return max(error, abs(float(expected_exploitability) - actual.exploitability))


def _coalition_payload_error(
    expected: Sequence[Mapping[str, Any]],
    actual: CoalitionEvaluationResult,
) -> float:
    expected_values = {
        tuple(map(int, row["coalition"])): (
            float(row["baseline_value"]),
            float(row["best_response_value"]),
            float(row["deviation_gain"]),
        )
        for row in expected
    }
    actual_values = _coalition_values(actual)
    if expected_values.keys() != actual_values.keys():
        return math.inf
    return max(
        (
            abs(left - right)
            for coalition in expected_values
            for left, right in zip(
                expected_values[coalition],
                actual_values[coalition],
                strict=True,
            )
        ),
        default=0.0,
    )


def _candidate_payload_error(
    expected: Mapping[str, Any],
    baseline: EvaluationResult,
    candidate: EvaluationResult,
    coalitions: CoalitionEvaluationResult,
) -> float:
    errors = [
        abs(float(expected["baseline_nash_conv"]) - baseline.nash_conv),
        abs(float(expected["candidate_nash_conv"]) - candidate.nash_conv),
        abs(
            float(expected["raw_nash_conv_reduction"])
            - (baseline.nash_conv - candidate.nash_conv)
        ),
        abs(
            float(expected["normalized_nash_conv_reduction"])
            - (
                (baseline.nash_conv - candidate.nash_conv)
                / float(expected["payoff_span"])
            )
        ),
    ]
    errors.extend(
        abs(float(expected_value) - actual_value)
        for expected_value, actual_value in zip(
            expected["baseline_deviation_gains"],
            baseline.deviation_gains,
            strict=True,
        )
    )
    errors.extend(
        abs(float(expected_value) - actual_value)
        for expected_value, actual_value in zip(
            expected["candidate_deviation_gains"],
            candidate.deviation_gains,
            strict=True,
        )
    )
    errors.append(
        _coalition_payload_error(expected["candidate_coalitions"], coalitions)
    )
    return max(errors)


def _acceptance_labels(assessment: Any) -> dict[str, bool]:
    return {
        "aggregate_exact": assessment.aggregate_nash_conv_strictly_decreases,
        "unilateral_pareto": assessment.unilateral_pareto_accept,
        "coalition_stress": assessment.coalition_stress_accept,
    }


def _label_mismatches(
    expected: Mapping[str, Any],
    actual: Mapping[str, bool],
) -> int:
    return sum(bool(expected[arm]) != bool(actual[arm]) for arm in _ACCEPTANCE_ARMS)


def _unique_index(
    rows: Sequence[Mapping[str, Any]],
    key_fields: tuple[str, ...],
    label: str,
) -> dict[tuple[object, ...], Mapping[str, Any]]:
    result = {}
    for row in rows:
        key = tuple(row[field] for field in key_fields)
        if key in result:
            raise ValueError(f"duplicate {label} key {key!r}")
        result[key] = row
    return result


def primary_reuse_curve(
    *,
    accepted_raw_reduction: float,
    blind_raw_reduction: float,
    blind_solver_ms: float,
    source_compile_ms: float,
    targets_per_context: float,
    baseline_update_ms: float,
    candidate_update_ms: float,
    maximum_reuses: int,
) -> dict[str, object]:
    numeric = (
        accepted_raw_reduction,
        blind_raw_reduction,
        blind_solver_ms,
        source_compile_ms,
        targets_per_context,
        baseline_update_ms,
        candidate_update_ms,
    )
    if any(not math.isfinite(value) for value in numeric):
        raise ValueError("primary reuse inputs must be finite")
    if (
        accepted_raw_reduction <= 0.0
        or blind_raw_reduction <= 0.0
        or blind_solver_ms <= 0.0
        or source_compile_ms < 0.0
        or targets_per_context <= 0.0
        or baseline_update_ms < 0.0
        or candidate_update_ms < 0.0
        or isinstance(maximum_reuses, bool)
        or maximum_reuses <= 0
    ):
        raise ValueError("primary reuse inputs are outside their valid ranges")

    blind_rate = blind_raw_reduction / blind_solver_ms
    precompiled_ms = blind_solver_ms + baseline_update_ms + candidate_update_ms
    rows = []
    minimum_winning_reuses: int | None = None
    for reuse_count in range(1, maximum_reuses + 1):
        compile_charge = targets_per_context * source_compile_ms / reuse_count
        charged_ms = precompiled_ms + compile_charge
        rate = accepted_raw_reduction / charged_ms
        wins = rate > blind_rate
        if wins and minimum_winning_reuses is None:
            minimum_winning_reuses = reuse_count
        rows.append(
            {
                "reuse_count": reuse_count,
                "source_compile_charge_ms": compile_charge,
                "charged_ms": charged_ms,
                "accepted_raw_reduction_per_ms": rate,
                "rate_ratio_to_blind": rate / blind_rate,
                "strictly_beats_blind": wins,
            }
        )
    precompiled_rate = accepted_raw_reduction / precompiled_ms
    return {
        "accepted_raw_reduction": accepted_raw_reduction,
        "blind_raw_reduction": blind_raw_reduction,
        "blind_solver_ms": blind_solver_ms,
        "blind_raw_reduction_per_ms": blind_rate,
        "baseline_update_ms": baseline_update_ms,
        "candidate_update_ms": candidate_update_ms,
        "precompiled_charged_ms": precompiled_ms,
        "precompiled_raw_reduction_per_ms": precompiled_rate,
        "precompiled_rate_ratio_to_blind": precompiled_rate / blind_rate,
        "precompiled_strictly_beats_blind": precompiled_rate > blind_rate,
        "minimum_winning_reuses": minimum_winning_reuses,
        "reuse_curve": rows,
    }


def _generate_contexts(source: dict[str, Any]) -> list[MultiwayRiverContext]:
    return generate_multiway_river_contexts(
        groups=source["requested_groups"],
        seed=source["seed"],
        hands_per_player=source["hands_per_player"],
        families=source["families"],
        splits=source["included_splits"],
        pot_options=source["pot_options"],
        bet_to_pot_options=source["bet_to_pot_options"],
        effective_stack_to_pot=source["effective_stack_to_pot"],
        weight_options=source["range_weight_options"],
    )


def _target_distribution(target: MultiwayRangeTarget) -> dict[Action, float]:
    return dict(target.game.initial_state().chance_outcomes())


def _candidate_audit_record(
    *,
    context: MultiwayRiverContext,
    target: MultiwayRangeTarget,
    policy: Policy,
    solver_name: str,
    checkpoint: int,
    cumulative_solver_ms: float,
    output_policy_ms: float,
    ordinary_baseline: EvaluationResult,
    source_baseline: EvaluationResult,
    target_baseline: EvaluationResult,
    baseline_coalitions: CoalitionEvaluationResult,
    source_tape: CompiledPolicyDeltaTape,
    target_tape: CompiledPolicyDeltaTape,
    target_distribution: Mapping[Action, float],
    expected: Mapping[str, Any],
    source_config: dict[str, Any],
    execution_mode: str,
) -> tuple[dict[str, object], Policy, DependencyTapeResult]:
    ordinary, ordinary_ms = _timed(lambda: evaluate_profile(target.game, policy))
    source_result, source_ms = _timed(
        lambda: source_tape.recertify_profile(
            target_distribution,
            policy,
            mode=execution_mode,  # type: ignore[arg-type]
        )
    )
    target_result, target_ms = _timed(
        lambda: target_tape.recertify_policy(
            policy,
            mode=execution_mode,  # type: ignore[arg-type]
        )
    )
    reference_actions = _reference_actions(target.game, policy)
    candidate_coalitions, coalition_ms = _timed(
        lambda: evaluate_coalition_threats(target.game, policy)
    )

    ordinary_assessment = assess_multiplayer_candidate(
        ordinary_baseline,
        ordinary,
        baseline_coalitions,
        candidate_coalitions,
        payoff_span=target.game.payoff_span,
        numerical_guard_fraction=source_config["numerical_guard_by_payoff_span"],
    )
    source_assessment = assess_multiplayer_candidate(
        source_baseline,
        source_result.evaluation,
        baseline_coalitions,
        candidate_coalitions,
        payoff_span=target.game.payoff_span,
        numerical_guard_fraction=source_config["numerical_guard_by_payoff_span"],
    )
    target_assessment = assess_multiplayer_candidate(
        target_baseline,
        target_result.evaluation,
        baseline_coalitions,
        candidate_coalitions,
        payoff_span=target.game.payoff_span,
        numerical_guard_fraction=source_config["numerical_guard_by_payoff_span"],
    )
    expected_labels = expected["acceptance"]
    ordinary_labels = _acceptance_labels(ordinary_assessment)
    source_labels = _acceptance_labels(source_assessment)
    target_labels = _acceptance_labels(target_assessment)

    errors = {
        "source_vs_ordinary": _evaluation_error(source_result.evaluation, ordinary),
        "target_vs_ordinary": _evaluation_error(target_result.evaluation, ordinary),
        "source_vs_target": _evaluation_error(
            source_result.evaluation,
            target_result.evaluation,
        ),
        "frozen_metric_reproduction": _candidate_payload_error(
            expected,
            ordinary_baseline,
            ordinary,
            candidate_coalitions,
        ),
    }
    action_mismatches = {
        "source_vs_ordinary": _action_mismatches(
            source_result.best_response_actions,
            reference_actions,
        ),
        "target_vs_ordinary": _action_mismatches(
            target_result.best_response_actions,
            reference_actions,
        ),
        "source_vs_target": _action_mismatches(
            source_result.best_response_actions,
            target_result.best_response_actions,
        ),
    }
    label_mismatches = {
        "ordinary_vs_frozen": _label_mismatches(expected_labels, ordinary_labels),
        "source_vs_frozen": _label_mismatches(expected_labels, source_labels),
        "target_vs_frozen": _label_mismatches(expected_labels, target_labels),
    }
    return (
        {
            "context_id": context.context_id,
            "group_id": context.group_id,
            "family": context.family,
            "target_id": target.target_id,
            "target_name": target.name,
            "target_kind": target.kind,
            "solver": solver_name,
            "checkpoint": checkpoint,
            "evaluation_errors": errors,
            "best_response_action_mismatches": action_mismatches,
            "acceptance": {
                "frozen": {arm: bool(expected_labels[arm]) for arm in _ACCEPTANCE_ARMS},
                "ordinary": ordinary_labels,
                "source_reuse": source_labels,
                "target_compiled": target_labels,
                "mismatches": label_mismatches,
            },
            "timing_ms": {
                "warm_start_and_cumulative_steps": cumulative_solver_ms,
                "output_policy": output_policy_ms,
                "ordinary_candidate": ordinary_ms,
                "source_combined_range_policy": source_ms,
                "target_policy_only": target_ms,
                "candidate_coalition": coalition_ms,
            },
            "source_diagnostics": asdict(source_result.diagnostics),
            "target_diagnostics": asdict(target_result.diagnostics),
        },
        copy.deepcopy(policy),
        source_result,
    )


def run_multiway_source_tape_audit(
    config: dict[str, Any],
    *,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    parsed = parse_source_tape_audit_config(config)
    root = _ROOT if workspace_root is None else workspace_root
    source_config_raw, source_config_provenance = _read_frozen(
        root,
        parsed["source_config"],
        parsed["source_config_sha256"],
    )
    source_artifact, source_artifact_provenance = _read_frozen(
        root,
        parsed["source_artifact"],
        parsed["source_artifact_sha256"],
    )
    source_config = parse_multiway_search_config(source_config_raw)
    if source_artifact.get("config") != source_config_raw:
        raise ValueError("source artifact does not contain the frozen source config")
    expected_counts = source_artifact.get("counts", {})
    for field in ("groups", "contexts", "targets", "candidate_records"):
        if int(expected_counts.get(field, -1)) != parsed[f"expected_{field}"]:
            raise ValueError(f"source artifact {field} count differs from ADR-0057")
    if int(expected_counts.get("reserved_contexts_materialized", -1)) != 0:
        raise ValueError("source artifact materialized a reserved context")

    expected_sources = _unique_index(
        source_artifact["sources"],
        ("context_id",),
        "source",
    )
    expected_targets = _unique_index(
        source_artifact["targets"],
        ("target_id",),
        "target",
    )
    expected_records = _unique_index(
        source_artifact["records"],
        ("target_id", "solver", "checkpoint"),
        "candidate",
    )
    contexts = _generate_contexts(source_config)
    if len(contexts) != parsed["expected_contexts"]:
        raise ValueError("regenerated context count differs from ADR-0057")
    if len({context.group_id for context in contexts}) != parsed["expected_groups"]:
        raise ValueError("regenerated group count differs from ADR-0057")
    if any(context.split != "development" for context in contexts):
        raise ValueError("regeneration constructed a reserved context")

    experiment_start = time.perf_counter()
    context_records: list[dict[str, object]] = []
    target_records: list[dict[str, object]] = []
    candidate_records: list[dict[str, object]] = []
    maximum_evaluation_error = 0.0
    maximum_metric_error = 0.0
    action_mismatches = 0
    label_mismatches = 0
    maximum_call_order_error = 0.0
    call_order_action_identity = True
    policy_schema_identity = True
    support_preservation = True

    for context in contexts:
        blueprint, source_record = _solve_source_blueprint(context, source_config)
        frozen_source = expected_sources[(context.context_id,)]
        source_metric_error = max(
            abs(
                float(source_record["selected_nash_conv"])
                - float(frozen_source["selected_nash_conv"])
            ),
            abs(
                float(source_record["selected_normalized_nash_conv"])
                - float(frozen_source["selected_normalized_nash_conv"])
            ),
        )
        if source_record["selected_checkpoint"] != frozen_source["selected_checkpoint"]:
            source_metric_error = math.inf
        maximum_metric_error = max(maximum_metric_error, source_metric_error)

        source_tape, source_compile_ms = _timed(
            lambda: CompiledPolicyDeltaTape(context.game, blueprint)
        )
        source_distribution = context.game.joint_distribution()
        targets = make_multiway_range_targets(context, source_config["target_specs"])
        if len(targets) != 4:
            raise ValueError("each frozen source context must have four targets")
        sentinel: tuple[
            Mapping[Action, float],
            Policy,
            DependencyTapeResult,
        ] | None = None
        context_target_records = []

        for target_index, target in enumerate(targets):
            frozen_target = expected_targets[(target.target_id,)]
            distribution = _target_distribution(target)
            target_support_preserved = (
                set(distribution) == set(source_distribution)
                and target.game.structural_digest == context.game.structural_digest
            )
            support_preservation = support_preservation and target_support_preserved
            ordinary_baseline, ordinary_baseline_ms = _timed(
                lambda: evaluate_profile(target.game, blueprint)
            )
            source_baseline, source_baseline_ms = _timed(
                lambda: source_tape.recertify_profile(
                    distribution,
                    blueprint,
                    mode=parsed["execution_mode"],
                )
            )
            target_tape, target_compile_ms = _timed(
                lambda: CompiledPolicyDeltaTape(target.game, blueprint)
            )
            target_baseline = target_tape.source_result
            baseline_actions = _reference_actions(target.game, blueprint)
            baseline_coalitions, baseline_coalition_ms = _timed(
                lambda: evaluate_coalition_threats(target.game, blueprint)
            )
            baseline_errors = {
                "source_vs_ordinary": _evaluation_error(
                    source_baseline.evaluation,
                    ordinary_baseline,
                ),
                "target_vs_ordinary": _evaluation_error(
                    target_baseline.evaluation,
                    ordinary_baseline,
                ),
                "source_vs_target": _evaluation_error(
                    source_baseline.evaluation,
                    target_baseline.evaluation,
                ),
                "frozen_metric_reproduction": max(
                    _evaluation_payload_error(
                        frozen_target["baseline_evaluation"],
                        ordinary_baseline,
                    ),
                    _coalition_payload_error(
                        frozen_target["baseline_coalitions"],
                        baseline_coalitions,
                    ),
                ),
            }
            baseline_mismatches = {
                "source_vs_ordinary": _action_mismatches(
                    source_baseline.best_response_actions,
                    baseline_actions,
                ),
                "target_vs_ordinary": _action_mismatches(
                    target_baseline.best_response_actions,
                    baseline_actions,
                ),
                "source_vs_target": _action_mismatches(
                    source_baseline.best_response_actions,
                    target_baseline.best_response_actions,
                ),
            }
            maximum_evaluation_error = max(
                maximum_evaluation_error,
                *(
                    value
                    for key, value in baseline_errors.items()
                    if key != "frozen_metric_reproduction"
                ),
            )
            maximum_metric_error = max(
                maximum_metric_error,
                baseline_errors["frozen_metric_reproduction"],
            )
            action_mismatches += sum(baseline_mismatches.values())
            schema_identity = (
                source_tape.policy_input_schema == target_tape.policy_input_schema
            )
            policy_schema_identity = policy_schema_identity and schema_identity

            target_record = {
                "context_id": context.context_id,
                "group_id": context.group_id,
                "family": context.family,
                "target_id": target.target_id,
                "target_name": target.name,
                "target_kind": target.kind,
                "support_preserved": target_support_preserved,
                "policy_schema_identity": schema_identity,
                "baseline_evaluation_errors": baseline_errors,
                "baseline_best_response_action_mismatches": baseline_mismatches,
                "timing_ms": {
                    "ordinary_baseline": ordinary_baseline_ms,
                    "source_baseline_range_update": source_baseline_ms,
                    "target_tape_compile": target_compile_ms,
                    "baseline_coalition": baseline_coalition_ms,
                },
                "target_tape_bytes": target_tape.contiguous_runtime_bytes,
                "source_baseline_diagnostics": asdict(source_baseline.diagnostics),
            }
            target_records.append(target_record)
            context_target_records.append(target_record)

            for solver_name in source_config["candidate_solvers"]:
                solver = TabularCFR(target.game, variant=solver_name)
                _, warm_start_ms = _timed(
                    lambda: solver.warm_start_from_schema(
                        blueprint,
                        source_config["warm_start_multiplier_by_payoff_span"]
                        * target.game.payoff_span,
                        target_tape.policy_input_schema,
                    )
                )
                cumulative_solver_ms = warm_start_ms
                previous = 0
                for checkpoint in source_config["candidate_checkpoints"]:
                    _, run_ms = _timed(lambda: solver.run(checkpoint - previous))
                    cumulative_solver_ms += run_ms
                    previous = checkpoint
                    policy, output_ms = _timed(solver.average_strategy)
                    frozen_candidate = expected_records[
                        (target.target_id, solver_name, checkpoint)
                    ]
                    row, saved_policy, source_result = _candidate_audit_record(
                        context=context,
                        target=target,
                        policy=policy,
                        solver_name=solver_name,
                        checkpoint=checkpoint,
                        cumulative_solver_ms=cumulative_solver_ms,
                        output_policy_ms=output_ms,
                        ordinary_baseline=ordinary_baseline,
                        source_baseline=source_baseline.evaluation,
                        target_baseline=target_baseline.evaluation,
                        baseline_coalitions=baseline_coalitions,
                        source_tape=source_tape,
                        target_tape=target_tape,
                        target_distribution=distribution,
                        expected=frozen_candidate,
                        source_config=source_config,
                        execution_mode=parsed["execution_mode"],
                    )
                    candidate_records.append(row)
                    maximum_evaluation_error = max(
                        maximum_evaluation_error,
                        *(
                            float(value)
                            for key, value in row["evaluation_errors"].items()
                            if key != "frozen_metric_reproduction"
                        ),
                    )
                    maximum_metric_error = max(
                        maximum_metric_error,
                        float(
                            row["evaluation_errors"]["frozen_metric_reproduction"]
                        ),
                    )
                    action_mismatches += sum(
                        int(value)
                        for value in row[
                            "best_response_action_mismatches"
                        ].values()
                    )
                    label_mismatches += sum(
                        int(value)
                        for value in row["acceptance"]["mismatches"].values()
                    )
                    if (
                        target_index == 0
                        and solver_name == source_config["primary_solver"]
                        and checkpoint == source_config["primary_checkpoint"]
                    ):
                        sentinel = (
                            dict(distribution),
                            saved_policy,
                            source_result,
                        )

        if sentinel is None:
            raise AssertionError("primary call-order sentinel was not captured")
        sentinel_distribution, sentinel_policy, sentinel_result = sentinel
        replay, replay_ms = _timed(
            lambda: source_tape.recertify_profile(
                sentinel_distribution,
                sentinel_policy,
                mode=parsed["execution_mode"],
            )
        )
        replay_error = _evaluation_error(
            sentinel_result.evaluation,
            replay.evaluation,
        )
        replay_actions_equal = (
            sentinel_result.best_response_actions == replay.best_response_actions
        )
        maximum_call_order_error = max(maximum_call_order_error, replay_error)
        call_order_action_identity = (
            call_order_action_identity and replay_actions_equal
        )
        context_records.append(
            {
                "context_id": context.context_id,
                "group_id": context.group_id,
                "family": context.family,
                "source_metric_reproduction_error": source_metric_error,
                "source_tape_compile_ms": source_compile_ms,
                "source_tape_bytes": source_tape.contiguous_runtime_bytes,
                "source_topology": source_tape.topology_summary(),
                "targets": len(context_target_records),
                "call_order_replay_error": replay_error,
                "call_order_action_identity": replay_actions_equal,
                "call_order_replay_ms": replay_ms,
            }
        )

    if len(target_records) != parsed["expected_targets"]:
        raise ValueError("regenerated target count differs from ADR-0057")
    if len(candidate_records) != parsed["expected_candidate_records"]:
        raise ValueError("regenerated candidate count differs from ADR-0057")

    timing = {
        "ordinary_baseline_ms": sum(
            float(row["timing_ms"]["ordinary_baseline"]) for row in target_records
        ),
        "ordinary_candidate_ms": sum(
            float(row["timing_ms"]["ordinary_candidate"])
            for row in candidate_records
        ),
        "target_tape_compile_ms": sum(
            float(row["timing_ms"]["target_tape_compile"])
            for row in target_records
        ),
        "target_policy_update_ms": sum(
            float(row["timing_ms"]["target_policy_only"])
            for row in candidate_records
        ),
        "source_tape_compile_ms": sum(
            float(row["source_tape_compile_ms"]) for row in context_records
        ),
        "source_baseline_update_ms": sum(
            float(row["timing_ms"]["source_baseline_range_update"])
            for row in target_records
        ),
        "source_candidate_update_ms": sum(
            float(row["timing_ms"]["source_combined_range_policy"])
            for row in candidate_records
        ),
        "baseline_coalition_ms": sum(
            float(row["timing_ms"]["baseline_coalition"])
            for row in target_records
        ),
        "candidate_coalition_ms": sum(
            float(row["timing_ms"]["candidate_coalition"])
            for row in candidate_records
        ),
    }
    timing["ordinary_path_ms"] = (
        timing["ordinary_baseline_ms"] + timing["ordinary_candidate_ms"]
    )
    timing["target_compiled_path_ms"] = (
        timing["target_tape_compile_ms"] + timing["target_policy_update_ms"]
    )
    timing["source_reuse_path_ms"] = (
        timing["source_tape_compile_ms"]
        + timing["source_baseline_update_ms"]
        + timing["source_candidate_update_ms"]
    )
    timing["source_precompiled_path_ms"] = (
        timing["source_baseline_update_ms"]
        + timing["source_candidate_update_ms"]
    )

    source_bytes = sum(int(row["source_tape_bytes"]) for row in context_records)
    target_bytes = sum(int(row["target_tape_bytes"]) for row in target_records)
    persisted_byte_ratio = source_bytes / target_bytes

    primary_rows = [
        row
        for row in candidate_records
        if row["solver"] == source_config["primary_solver"]
        and row["checkpoint"] == source_config["primary_checkpoint"]
    ]
    frozen_primary = source_artifact["primary_summary"]
    reuse_curve = primary_reuse_curve(
        accepted_raw_reduction=float(
            frozen_primary["arm_raw_reduction"]["aggregate_exact"]
        ),
        blind_raw_reduction=float(frozen_primary["arm_raw_reduction"]["blind"]),
        blind_solver_ms=float(frozen_primary["charged_milliseconds"]["blind"]),
        source_compile_ms=timing["source_tape_compile_ms"],
        targets_per_context=(
            parsed["expected_targets"] / parsed["expected_contexts"]
        ),
        baseline_update_ms=timing["source_baseline_update_ms"],
        candidate_update_ms=sum(
            float(row["timing_ms"]["source_combined_range_policy"])
            for row in primary_rows
        ),
        maximum_reuses=parsed["primary_break_even_maximum_reuses"],
    )
    primary_target_control_ms = (
        float(frozen_primary["charged_milliseconds"]["blind"])
        + timing["target_tape_compile_ms"]
        + sum(
            float(row["timing_ms"]["target_policy_only"])
            for row in primary_rows
        )
    )
    reuse_curve["target_compiled_charged_ms"] = primary_target_control_ms
    reuse_curve["target_compiled_raw_reduction_per_ms"] = (
        float(frozen_primary["arm_raw_reduction"]["aggregate_exact"])
        / primary_target_control_ms
    )

    requirements = parsed["gates"]
    correctness_results = {
        "evaluation_identity": (
            maximum_evaluation_error <= requirements["maximum_evaluation_error"]
        ),
        "frozen_metric_reproduction": (
            maximum_metric_error
            <= requirements["maximum_metric_reproduction_error"]
        ),
        "best_response_action_identity": (
            action_mismatches
            <= requirements["maximum_best_response_action_mismatches"]
        ),
        "acceptance_label_identity": (
            label_mismatches
            <= requirements["maximum_acceptance_label_mismatches"]
        ),
        "call_order_numerical_replay": (
            maximum_call_order_error
            <= requirements["maximum_call_order_replay_error"]
        ),
        "call_order_action_replay": (
            call_order_action_identity
            if requirements["require_exact_call_order_action_replay"]
            else True
        ),
        "policy_schema_identity": (
            policy_schema_identity
            if requirements["require_identical_policy_schema"]
            else True
        ),
        "support_preservation": (
            support_preservation
            if requirements["require_support_preservation"]
            else True
        ),
    }
    performance_results = {
        "source_reuse_faster_than_target_compile": (
            timing["source_reuse_path_ms"] < timing["target_compiled_path_ms"]
            if requirements[
                "source_reuse_path_strictly_faster_than_target_compile_path"
            ]
            else True
        ),
        "source_precompiled_faster_than_ordinary": (
            timing["source_precompiled_path_ms"] < timing["ordinary_path_ms"]
            if requirements[
                "source_precompiled_path_strictly_faster_than_ordinary_path"
            ]
            else True
        ),
        "primary_precompiled_rate_beats_blind": (
            bool(reuse_curve["precompiled_strictly_beats_blind"])
            if requirements["primary_precompiled_rate_strictly_beats_blind"]
            else True
        ),
        "primary_break_even_within_frozen_reuses": (
            reuse_curve["minimum_winning_reuses"] is not None
            and int(reuse_curve["minimum_winning_reuses"])
            <= parsed["primary_break_even_maximum_reuses"]
        ),
        "persisted_tape_bytes": (
            persisted_byte_ratio
            <= requirements["maximum_persisted_tape_byte_ratio"]
        ),
    }
    all_results = (*correctness_results.values(), *performance_results.values())

    return {
        "schema_version": 1,
        "experiment_type": "multiway_source_compiled_range_policy_reuse_audit",
        "status": "revealed_multiway_engineering_audit",
        "config": config,
        "canonical_config_sha256": hashlib.sha256(
            json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "environment": environment_metadata(),
        "provenance": {
            "source_config": source_config_provenance,
            "source_artifact": source_artifact_provenance,
        },
        "counts": {
            "groups": len({context.group_id for context in contexts}),
            "contexts": len(contexts),
            "targets": len(target_records),
            "candidate_records": len(candidate_records),
            "source_tapes_compiled": len(context_records),
            "target_control_tapes_compiled": len(target_records),
            "reserved_contexts_materialized": sum(
                context.split != "development" for context in contexts
            ),
        },
        "correctness": {
            "maximum_evaluation_error": maximum_evaluation_error,
            "maximum_frozen_metric_reproduction_error": maximum_metric_error,
            "best_response_action_mismatches": action_mismatches,
            "acceptance_label_mismatches": label_mismatches,
            "maximum_call_order_replay_error": maximum_call_order_error,
            "call_order_action_identity": call_order_action_identity,
            "policy_schema_identity": policy_schema_identity,
            "support_preservation": support_preservation,
        },
        "timing_ms": {
            **timing,
            "source_reuse_vs_target_compile_speedup": (
                timing["target_compiled_path_ms"]
                / timing["source_reuse_path_ms"]
            ),
            "source_precompiled_vs_ordinary_speedup": (
                timing["ordinary_path_ms"]
                / timing["source_precompiled_path_ms"]
            ),
        },
        "memory": {
            "persisted_source_tape_bytes": source_bytes,
            "persisted_four_target_tape_bytes": target_bytes,
            "source_to_target_byte_ratio": persisted_byte_ratio,
            "target_to_source_reduction_factor": target_bytes / source_bytes,
        },
        "primary_dcfr32": reuse_curve,
        "gates": {
            "requirements": requirements,
            "correctness": correctness_results,
            "performance": performance_results,
            "correctness_passed": all(correctness_results.values()),
            "performance_passed": all(performance_results.values()),
            "passed": all(all_results),
        },
        "timing": {"wall_seconds": time.perf_counter() - experiment_start},
        "contexts": context_records,
        "targets": target_records,
        "records": candidate_records,
        "limitations": [
            "All strategy labels were revealed before this engineering audit.",
            (
                "Support-preserving within-street reuse is the easiest valid "
                "topology case."
            ),
            "Python timing does not predict a native six-player kernel constant.",
            (
                "Coalition evaluation remains ordinary offline work and is not "
                "accelerated."
            ),
            (
                "No approximate range similarity, factorization, or low-rank "
                "claim follows."
            ),
        ],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_multiway_source_tape_audit(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "multiway source-tape audit: "
        f"records={result['counts']['candidate_records']}, "
        f"max_error={result['correctness']['maximum_evaluation_error']:.3e}, "
        f"labels={result['correctness']['acceptance_label_mismatches']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
