"""Frozen development mechanism test for exact policy-delta recertification."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable

from .cfr import TabularCFR
from .dependency_tape import CompiledPolicyDeltaTape, DependencyTapeResult
from .depth_limited import PolicyContinuationValues
from .evaluation import EvaluationResult, Policy, best_response, evaluate_profile
from .reporting import environment_metadata
from .river_context import generate_river_contexts
from .river_selective import (
    MultiSizeExpansionMask,
    complete_information_schema,
    compose_selective_policy,
    multi_size_state_cache_key,
)
from .river_selective_experiment import (
    _build_blueprint,
    _range_targets,
    _validate_config as _validate_selective_config,
    _wide_game,
)
from .selective_tree import (
    SelectiveExpansionGame,
    collect_selective_cutoff_states,
    full_tree_state_count,
)

_CONFIG_FIELDS = {
    "evidence_stage",
    "source_artifact",
    "source_artifact_sha256",
    "source_config_sha256",
    "source_implementation_commit",
    "expected_groups",
    "expected_contexts",
    "expected_targets",
    "candidate_masks",
    "primary_mask",
    "warm_start_multiplier_by_payoff_span",
    "full_tree_equivalent_iteration_budget",
    "dense_threshold",
    "changed_probability_tolerance",
    "acceptance_tolerance_by_payoff_span",
    "timing_warmup_repetitions",
    "timing_measurement_repetitions",
    "execution_modes",
    "gates",
}
_GATE_FIELDS = {
    "maximum_absolute_evaluation_error",
    "maximum_regenerated_label_error",
    "maximum_acceptance_decision_mismatches",
    "maximum_best_response_action_mismatches",
    "minimum_hot_update_speedup_over_full_evaluation",
    "minimum_hot_verified_normalized_quality_rate_ratio_over_blind",
}


@dataclass(frozen=True, slots=True)
class _Candidate:
    context_id: str
    group_id: str
    family: str
    target_name: str
    target_kind: str
    mask_name: str
    payoff_span: float
    policy: Policy
    baseline: EvaluationResult
    full: EvaluationResult
    solver_iterations: int
    tree_states_per_traversal: int
    changed_information_sets: int
    exact_leaf_build_seconds: float
    initialization_seconds: float
    solve_seconds: float

    @property
    def candidate_online_seconds(self) -> float:
        return self.exact_leaf_build_seconds + self.initialization_seconds + self.solve_seconds


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _validate_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "policy-delta config fields do not match the frozen schema: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    if config["evidence_stage"] != "revealed_development_mechanism_test":
        raise ValueError("policy-delta evidence stage must remain development-only")

    source_artifact = str(config["source_artifact"])
    artifact_sha = str(config["source_artifact_sha256"])
    source_config_sha = str(config["source_config_sha256"])
    source_commit = str(config["source_implementation_commit"])
    if not source_artifact or Path(source_artifact).is_absolute():
        raise ValueError("source_artifact must be a nonempty workspace-relative path")
    for label, value in (
        ("source_artifact_sha256", artifact_sha),
        ("source_config_sha256", source_config_sha),
        ("source_implementation_commit", source_commit),
    ):
        if not _is_sha256(value) and not (
            label == "source_implementation_commit"
            and len(value) == 40
            and all(character in "0123456789abcdef" for character in value)
        ):
            raise ValueError(f"{label} is not a lowercase hexadecimal digest")

    expected_groups = int(config["expected_groups"])
    expected_contexts = int(config["expected_contexts"])
    expected_targets = int(config["expected_targets"])
    if min(expected_groups, expected_contexts, expected_targets) <= 0:
        raise ValueError("expected source counts must be positive")

    candidate_masks = tuple(str(value) for value in config["candidate_masks"])
    primary_mask = str(config["primary_mask"])
    if candidate_masks != ("b3r1", "b3r2") or primary_mask != "b3r2":
        raise ValueError("candidate masks and primary mask are frozen by ADR-0046")
    warm = float(config["warm_start_multiplier_by_payoff_span"])
    budget = int(config["full_tree_equivalent_iteration_budget"])
    dense_threshold = float(config["dense_threshold"])
    change_tolerance = float(config["changed_probability_tolerance"])
    acceptance_tolerance = float(config["acceptance_tolerance_by_payoff_span"])
    warmups = int(config["timing_warmup_repetitions"])
    repetitions = int(config["timing_measurement_repetitions"])
    modes = tuple(str(value) for value in config["execution_modes"])
    if not math.isfinite(warm) or warm <= 0.0 or budget <= 0:
        raise ValueError("warm mass and work budget must be positive")
    if not math.isfinite(dense_threshold) or not 0.0 < dense_threshold < 1.0:
        raise ValueError("dense threshold must lie strictly between zero and one")
    if (
        not math.isfinite(change_tolerance)
        or not 0.0 <= change_tolerance <= 1e-10
        or not math.isfinite(acceptance_tolerance)
        or not 0.0 < acceptance_tolerance <= 1e-10
    ):
        raise ValueError("policy and acceptance tolerances exceed the exactness envelope")
    if warmups != 1 or repetitions != 7:
        raise ValueError("the frozen timing protocol requires one warmup and seven measurements")
    if modes != ("sparse", "dense", "auto"):
        raise ValueError("execution modes must be sparse, dense, and auto in that order")

    raw_gates = config["gates"]
    if not isinstance(raw_gates, dict) or set(raw_gates) != _GATE_FIELDS:
        raise ValueError("policy-delta gates do not match ADR-0046")
    gates = {key: float(value) for key, value in raw_gates.items()}
    if any(not math.isfinite(value) or value < 0.0 for value in gates.values()):
        raise ValueError("policy-delta gates must be finite and nonnegative")
    if gates["maximum_absolute_evaluation_error"] > 1e-10:
        raise ValueError("evaluation error gate exceeds the tape contract")

    return {
        "evidence_stage": str(config["evidence_stage"]),
        "source_artifact": source_artifact,
        "source_artifact_sha256": artifact_sha,
        "source_config_sha256": source_config_sha,
        "source_implementation_commit": source_commit,
        "expected_groups": expected_groups,
        "expected_contexts": expected_contexts,
        "expected_targets": expected_targets,
        "candidate_masks": candidate_masks,
        "primary_mask": primary_mask,
        "warm_start_multiplier_by_payoff_span": warm,
        "full_tree_equivalent_iteration_budget": budget,
        "dense_threshold": dense_threshold,
        "changed_probability_tolerance": change_tolerance,
        "acceptance_tolerance_by_payoff_span": acceptance_tolerance,
        "timing_warmup_repetitions": warmups,
        "timing_measurement_repetitions": repetitions,
        "execution_modes": modes,
        "gates": gates,
    }


def accept_candidate(
    baseline_nash_conv: float,
    candidate_nash_conv: float,
    *,
    payoff_span: float,
    tolerance_by_payoff_span: float,
) -> bool:
    values = (
        baseline_nash_conv,
        candidate_nash_conv,
        payoff_span,
        tolerance_by_payoff_span,
    )
    if any(not math.isfinite(value) for value in values):
        raise ValueError("acceptance inputs must be finite")
    if payoff_span <= 0.0 or tolerance_by_payoff_span < 0.0:
        raise ValueError("payoff span must be positive and tolerance nonnegative")
    return (
        baseline_nash_conv - candidate_nash_conv
        > tolerance_by_payoff_span * payoff_span
    )


def _evaluation_error(first: EvaluationResult, second: EvaluationResult) -> float:
    errors = [
        abs(left - right)
        for first_values, second_values in (
            (first.utilities, second.utilities),
            (first.best_response_values, second.best_response_values),
            (first.deviation_gains, second.deviation_gains),
        )
        for left, right in zip(first_values, second_values, strict=True)
    ]
    errors.append(abs(first.nash_conv - second.nash_conv))
    if first.exploitability is None or second.exploitability is None:
        if first.exploitability is not second.exploitability:
            return math.inf
    else:
        errors.append(abs(first.exploitability - second.exploitability))
    return max(errors, default=0.0)


def _action_mismatches(
    first: tuple[dict[str, object], ...],
    second: tuple[dict[str, object], ...],
) -> int:
    if len(first) != len(second):
        return max(len(first), len(second))
    mismatches = 0
    for first_player, second_player in zip(first, second, strict=True):
        keys = set(first_player) | set(second_player)
        mismatches += sum(first_player.get(key) != second_player.get(key) for key in keys)
    return mismatches


def _policy_changed_information_sets(
    source: Policy,
    target: Policy,
    schema: dict[str, tuple[object, ...]],
    tolerance: float,
) -> int:
    return sum(
        any(
            abs(source[key][action] - target[key][action]) > tolerance
            for action in actions
        )
        for key, actions in schema.items()
    )


def _make_candidate(
    *,
    context_id: str,
    group_id: str,
    family: str,
    target_name: str,
    target_kind: str,
    target: Any,
    blueprint: Policy,
    baseline: EvaluationResult,
    target_schema: dict[str, tuple[object, ...]],
    mask_config: dict[str, object],
    selective_config: dict[str, Any],
    parsed: dict[str, Any],
) -> _Candidate:
    mask_name = str(mask_config["name"])
    mask = MultiSizeExpansionMask.from_amounts(
        target,
        bet_amounts=tuple(
            target.pot * float(value)
            for value in mask_config["expanded_bet_pot_fractions"]
        ),
        raise_to_amounts=tuple(
            target.pot * float(value)
            for value in mask_config["expanded_raise_to_pot_fractions"]
        ),
    )
    leaf_values = PolicyContinuationValues(
        target.num_players,
        blueprint,
        key=multi_size_state_cache_key,
    )
    selective = SelectiveExpansionGame(target, leaf_values, mask)
    selective_states = full_tree_state_count(selective.initial_state())
    cutoff_states = collect_selective_cutoff_states(selective)
    leaf_start = time.perf_counter()
    for state in cutoff_states:
        leaf_values(state)
    exact_leaf_build_seconds = time.perf_counter() - leaf_start
    selective_schema = complete_information_schema(selective)

    full_states = full_tree_state_count(target.initial_state())
    full_iteration_visits = target.num_players * full_states
    selective_iteration_visits = target.num_players * selective_states
    checkpoint = max(
        1,
        (
            parsed["full_tree_equivalent_iteration_budget"]
            * full_iteration_visits
        )
        // selective_iteration_visits,
    )
    solver = TabularCFR(selective, variant=selective_config["online_solver"])
    initialization_start = time.perf_counter()
    solver.warm_start_from_schema(
        blueprint,
        regret_mass=(
            parsed["warm_start_multiplier_by_payoff_span"] * target.payoff_span
        ),
        information_sets=selective_schema,
    )
    initialization_seconds = time.perf_counter() - initialization_start
    solve_start = time.perf_counter()
    solver.run(checkpoint)
    solve_seconds = time.perf_counter() - solve_start
    completed = compose_selective_policy(
        blueprint,
        solver.average_strategy(),
        target_schema,
    )
    full = evaluate_profile(target, completed)
    return _Candidate(
        context_id=context_id,
        group_id=group_id,
        family=family,
        target_name=target_name,
        target_kind=target_kind,
        mask_name=mask_name,
        payoff_span=target.payoff_span,
        policy=completed,
        baseline=baseline,
        full=full,
        solver_iterations=checkpoint,
        tree_states_per_traversal=selective_states,
        changed_information_sets=_policy_changed_information_sets(
            blueprint,
            completed,
            target_schema,
            parsed["changed_probability_tolerance"],
        ),
        exact_leaf_build_seconds=exact_leaf_build_seconds,
        initialization_seconds=initialization_seconds,
        solve_seconds=solve_seconds,
    )


def _timed_call(call: Callable[[], object]) -> float:
    start = time.perf_counter()
    call()
    return time.perf_counter() - start


def _paired_timings(
    *,
    full_call: Callable[[], object],
    tape_call: Callable[[], object],
    record_index: int,
    warmups: int,
    repetitions: int,
) -> tuple[float, float, list[float], list[float]]:
    for warmup in range(warmups):
        if (record_index + warmup) % 2 == 0:
            full_call()
            tape_call()
        else:
            tape_call()
            full_call()
    full_times = []
    tape_times = []
    for repetition in range(repetitions):
        if (record_index + repetition) % 2 == 0:
            full_times.append(_timed_call(full_call))
            tape_times.append(_timed_call(tape_call))
        else:
            tape_times.append(_timed_call(tape_call))
            full_times.append(_timed_call(full_call))
    return median(full_times), median(tape_times), full_times, tape_times


def _compile_tape_timing(
    *,
    target: Any,
    blueprint: Policy,
    parsed: dict[str, Any],
) -> tuple[CompiledPolicyDeltaTape, float, list[float]]:
    def compile_once() -> CompiledPolicyDeltaTape:
        return CompiledPolicyDeltaTape(
            target,
            blueprint,
            dense_threshold=parsed["dense_threshold"],
            changed_policy_tolerance=parsed["changed_probability_tolerance"],
        )

    for _ in range(parsed["timing_warmup_repetitions"]):
        compile_once()
    times = []
    tape = None
    for _ in range(parsed["timing_measurement_repetitions"]):
        start = time.perf_counter()
        tape = compile_once()
        times.append(time.perf_counter() - start)
    assert tape is not None
    return tape, median(times), times


def _artifact_indexes(
    artifact: dict[str, Any],
) -> tuple[
    dict[tuple[str, str], dict[str, Any]],
    dict[tuple[object, ...], dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    targets = {
        (str(row["context_id"]), str(row["target_name"])): row
        for row in artifact["targets"]
    }
    records = {
        (
            str(row["context_id"]),
            str(row["target_name"]),
            str(row["mask_name"]),
            float(row["warm_start_multiplier_by_payoff_span"]),
            int(row["full_tree_equivalent_iteration_budget"]),
        ): row
        for row in artifact["records"]
    }
    blueprints = {str(row["context_id"]): row for row in artifact["blueprints"]}
    return targets, records, blueprints


def run_policy_delta_experiment(
    config: dict[str, Any],
    *,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    parsed = _validate_config(config)
    root = Path.cwd() if workspace_root is None else workspace_root
    artifact_path = (root / parsed["source_artifact"]).resolve()
    if root.resolve() not in artifact_path.parents:
        raise ValueError("source artifact resolves outside the workspace")
    artifact_bytes = artifact_path.read_bytes()
    artifact_sha = hashlib.sha256(artifact_bytes).hexdigest()
    if artifact_sha != parsed["source_artifact_sha256"]:
        raise ValueError("source artifact SHA-256 does not match the frozen config")
    artifact = json.loads(artifact_bytes)
    if artifact.get("config_sha256") != parsed["source_config_sha256"]:
        raise ValueError("source artifact canonical config hash does not match")
    if artifact.get("environment", {}).get("git", {}).get("commit") != parsed[
        "source_implementation_commit"
    ]:
        raise ValueError("source artifact implementation commit does not match")
    expected_counts = {
        "groups": parsed["expected_groups"],
        "contexts": parsed["expected_contexts"],
        "targets": parsed["expected_targets"],
    }
    if any(int(artifact["counts"].get(key, -1)) != value for key, value in expected_counts.items()):
        raise ValueError("source artifact counts do not match the frozen config")

    selective_config = dict(artifact["config"])
    selective_parsed = _validate_selective_config(selective_config)
    if parsed["warm_start_multiplier_by_payoff_span"] not in selective_parsed[
        "warm_start_multipliers_by_payoff_span"
    ]:
        raise ValueError("frozen warm mass is absent from the source experiment")
    if parsed["full_tree_equivalent_iteration_budget"] not in selective_parsed[
        "full_tree_equivalent_iteration_budgets"
    ]:
        raise ValueError("frozen work budget is absent from the source experiment")
    mask_by_name = {
        str(mask["name"]): mask for mask in selective_parsed["masks"]
    }
    if any(name not in mask_by_name for name in parsed["candidate_masks"]):
        raise ValueError("frozen candidate mask is absent from the source experiment")

    target_index, record_index, blueprint_index = _artifact_indexes(artifact)
    contexts = generate_river_contexts(
        groups=selective_parsed["groups"],
        seed=selective_parsed["seed"],
        hands_per_player=selective_parsed["hands_per_player"],
        families=selective_parsed["families"],
        splits=selective_parsed["included_splits"],
        sequential_raise=False,
    )
    if len(contexts) != parsed["expected_contexts"]:
        raise ValueError("deterministic regeneration produced the wrong context count")

    experiment_start = time.perf_counter()
    source_records: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    all_errors: list[float] = []
    label_errors: list[float] = []
    acceptance_mismatches = 0
    action_mismatches = 0
    record_counter = 0

    for context in contexts:
        source = _wide_game(context.game, selective_parsed)
        blueprint, source_evaluation, blueprint_metrics = _build_blueprint(
            source,
            selective_parsed,
        )
        frozen_blueprint = blueprint_index[context.context_id]
        source_label_error = max(
            abs(source_evaluation.nash_conv - float(frozen_blueprint["source_nash_conv"])),
            abs(
                source_evaluation.nash_conv / source.payoff_span
                - float(frozen_blueprint["source_normalized_nash_conv"])
            ),
        )
        label_errors.append(source_label_error)

        for target_name, target_kind, range_target, _ in _range_targets(
            context.game,
            selective_parsed,
        ):
            target = _wide_game(range_target, selective_parsed)
            target_schema = complete_information_schema(target)
            baseline = evaluate_profile(target, blueprint)
            frozen_target = target_index[(context.context_id, target_name)]
            baseline_label_error = abs(
                baseline.nash_conv
                - float(frozen_target["blueprint_full_universe_nash_conv"])
            )
            label_errors.append(baseline_label_error)

            tape, compile_seconds, compile_samples = _compile_tape_timing(
                target=target,
                blueprint=blueprint,
                parsed=parsed,
            )
            source_error = _evaluation_error(tape.source_result.evaluation, baseline)
            all_errors.append(source_error)
            topology = tape.topology_summary()
            identity = tape.recertify_policy(blueprint, mode="auto")
            identity_passes = (
                identity is tape.source_result
                and identity.diagnostics.dirty_nodes == 0
            )

            candidates = [
                _make_candidate(
                    context_id=context.context_id,
                    group_id=context.group_id,
                    family=context.family,
                    target_name=target_name,
                    target_kind=target_kind,
                    target=target,
                    blueprint=blueprint,
                    baseline=baseline,
                    target_schema=target_schema,
                    mask_config=mask_by_name[mask_name],
                    selective_config=selective_parsed,
                    parsed=parsed,
                )
                for mask_name in parsed["candidate_masks"]
            ]

            forward_results: dict[str, DependencyTapeResult] = {}
            for candidate in candidates:
                frozen = record_index[
                    (
                        candidate.context_id,
                        candidate.target_name,
                        candidate.mask_name,
                        parsed["warm_start_multiplier_by_payoff_span"],
                        parsed["full_tree_equivalent_iteration_budget"],
                    )
                ]
                frozen_candidate_nash = float(frozen["full_universe_nash_conv"])
                frozen_reduction = float(frozen["nash_conv_reduction_from_blueprint"])
                regenerated_reduction = baseline.nash_conv - candidate.full.nash_conv
                candidate_label_error = max(
                    abs(candidate.full.nash_conv - frozen_candidate_nash),
                    abs(regenerated_reduction - frozen_reduction),
                )
                label_errors.append(candidate_label_error)

                full_actions = tuple(
                    best_response(target, candidate.policy, player)[1]
                    for player in range(target.num_players)
                )
                mode_results = {
                    mode: tape.recertify_policy(candidate.policy, mode=mode)
                    for mode in parsed["execution_modes"]
                }
                forward_results[candidate.mask_name] = mode_results["sparse"]
                mode_errors = {
                    mode: _evaluation_error(result.evaluation, candidate.full)
                    for mode, result in mode_results.items()
                }
                all_errors.extend(mode_errors.values())
                mode_action_mismatches = {
                    mode: _action_mismatches(result.best_response_actions, full_actions)
                    for mode, result in mode_results.items()
                }
                action_mismatches += sum(mode_action_mismatches.values())

                full_accepts = accept_candidate(
                    baseline.nash_conv,
                    candidate.full.nash_conv,
                    payoff_span=target.payoff_span,
                    tolerance_by_payoff_span=parsed[
                        "acceptance_tolerance_by_payoff_span"
                    ],
                )
                mode_accepts = {
                    mode: accept_candidate(
                        baseline.nash_conv,
                        result.evaluation.nash_conv,
                        payoff_span=target.payoff_span,
                        tolerance_by_payoff_span=parsed[
                            "acceptance_tolerance_by_payoff_span"
                        ],
                    )
                    for mode, result in mode_results.items()
                }
                candidate_acceptance_mismatches = sum(
                    decision != full_accepts for decision in mode_accepts.values()
                )
                acceptance_mismatches += candidate_acceptance_mismatches

                full_median, tape_median, full_samples, tape_samples = _paired_timings(
                    full_call=lambda target=target, policy=candidate.policy: evaluate_profile(
                        target,
                        policy,
                    ),
                    tape_call=lambda tape=tape, policy=candidate.policy: tape.evaluate_policy(
                        policy,
                        mode="auto",
                    ),
                    record_index=record_counter,
                    warmups=parsed["timing_warmup_repetitions"],
                    repetitions=parsed["timing_measurement_repetitions"],
                )
                record_counter += 1
                diagnostics = {
                    mode: asdict(result.diagnostics)
                    for mode, result in mode_results.items()
                }
                records.append(
                    {
                        "context_id": candidate.context_id,
                        "group_id": candidate.group_id,
                        "family": candidate.family,
                        "target_name": candidate.target_name,
                        "target_kind": candidate.target_kind,
                        "mask_name": candidate.mask_name,
                        "payoff_span": candidate.payoff_span,
                        "solver_iterations": candidate.solver_iterations,
                        "tree_states_per_traversal": candidate.tree_states_per_traversal,
                        "changed_full_information_sets": candidate.changed_information_sets,
                        "full_information_sets": len(target_schema),
                        "exact_leaf_build_seconds": candidate.exact_leaf_build_seconds,
                        "initialization_seconds": candidate.initialization_seconds,
                        "solve_seconds": candidate.solve_seconds,
                        "candidate_online_seconds": candidate.candidate_online_seconds,
                        "baseline_nash_conv": baseline.nash_conv,
                        "candidate_nash_conv": candidate.full.nash_conv,
                        "nash_conv_reduction": regenerated_reduction,
                        "normalized_nash_conv_reduction": regenerated_reduction
                        / target.payoff_span,
                        "full_accepts_candidate": full_accepts,
                        "mode_acceptance_decisions": mode_accepts,
                        "acceptance_decision_mismatches": candidate_acceptance_mismatches,
                        "regenerated_label_error": candidate_label_error,
                        "mode_evaluation_errors": mode_errors,
                        "mode_best_response_action_mismatches": mode_action_mismatches,
                        "mode_diagnostics": diagnostics,
                        "full_evaluation_median_seconds": full_median,
                        "hot_policy_update_median_seconds": tape_median,
                        "full_evaluation_timing_samples": full_samples,
                        "hot_policy_update_timing_samples": tape_samples,
                    }
                )

            first = candidates[0]
            for candidate in reversed(candidates):
                reverse = tape.recertify_policy(candidate.policy, mode="sparse")
                forward = forward_results[candidate.mask_name]
                replay_error = _evaluation_error(reverse.evaluation, forward.evaluation)
                all_errors.append(replay_error)
                action_mismatches += _action_mismatches(
                    reverse.best_response_actions,
                    forward.best_response_actions,
                )
            repeated = tape.recertify_policy(first.policy, mode="sparse")
            repeat_error = _evaluation_error(
                repeated.evaluation,
                forward_results[first.mask_name].evaluation,
            )
            all_errors.append(repeat_error)
            repeat_action_mismatches = _action_mismatches(
                repeated.best_response_actions,
                forward_results[first.mask_name].best_response_actions,
            )
            action_mismatches += repeat_action_mismatches
            source_records.append(
                {
                    "context_id": context.context_id,
                    "group_id": context.group_id,
                    "family": context.family,
                    "target_name": target_name,
                    "target_kind": target_kind,
                    "blueprint_iterations": int(blueprint_metrics["iterations"]),
                    "source_regenerated_label_error": source_label_error,
                    "baseline_regenerated_label_error": baseline_label_error,
                    "source_tape_evaluation_error": source_error,
                    "identity_passes": identity_passes,
                    "reverse_order_repeat_error": repeat_error,
                    "reverse_order_action_mismatches": repeat_action_mismatches,
                    "compile_median_seconds": compile_seconds,
                    "compile_timing_samples": compile_samples,
                    "topology": topology,
                }
            )

    if len(source_records) != parsed["expected_targets"]:
        raise AssertionError("regeneration produced the wrong target count")
    if len(records) != parsed["expected_targets"] * len(parsed["candidate_masks"]):
        raise AssertionError("regeneration produced the wrong candidate count")

    primary = [row for row in records if row["mask_name"] == parsed["primary_mask"]]
    primary_source_keys = {
        (row["context_id"], row["target_name"]) for row in primary
    }
    primary_sources = [
        row
        for row in source_records
        if (row["context_id"], row["target_name"]) in primary_source_keys
    ]
    signed_normalized_reduction = math.fsum(
        float(row["normalized_nash_conv_reduction"]) for row in primary
    )
    accepted_normalized_reduction = math.fsum(
        float(row["normalized_nash_conv_reduction"])
        for row in primary
        if row["full_accepts_candidate"]
    )
    solve_seconds = math.fsum(float(row["candidate_online_seconds"]) for row in primary)
    full_seconds = math.fsum(
        float(row["full_evaluation_median_seconds"]) for row in primary
    )
    hot_seconds = math.fsum(
        float(row["hot_policy_update_median_seconds"]) for row in primary
    )
    compile_seconds = math.fsum(
        float(row["compile_median_seconds"]) for row in primary_sources
    )

    def rate(quality: float, seconds: float) -> float:
        return quality / (seconds * 1000.0)

    blind_rate = rate(signed_normalized_reduction, solve_seconds)
    ordinary_rate = rate(accepted_normalized_reduction, solve_seconds + full_seconds)
    hot_rate = rate(accepted_normalized_reduction, solve_seconds + hot_seconds)
    compile_rate = rate(
        accepted_normalized_reduction,
        solve_seconds + compile_seconds + hot_seconds,
    )
    hot_speedup = full_seconds / hot_seconds
    hot_rate_ratio = hot_rate / blind_rate
    compile_rate_ratio = compile_rate / blind_rate

    order_control = math.fsum(
        float(row["normalized_nash_conv_reduction"])
        for row in reversed(primary)
        if row["full_accepts_candidate"]
    )
    order_invariant = order_control == accepted_normalized_reduction
    identity_passes = all(row["identity_passes"] for row in source_records)
    topological = all(
        row["topology"]["dependencies_are_topological"] for row in source_records
    )
    requirements = parsed["gates"]
    gate_results = {
        "exact_evaluation_identity": max(all_errors, default=0.0)
        <= requirements["maximum_absolute_evaluation_error"],
        "regenerated_label_identity": max(label_errors, default=0.0)
        <= requirements["maximum_regenerated_label_error"],
        "acceptance_decision_identity": acceptance_mismatches
        <= requirements["maximum_acceptance_decision_mismatches"],
        "best_response_action_identity": action_mismatches
        <= requirements["maximum_best_response_action_mismatches"],
        "source_relative_identity_and_order": identity_passes and order_invariant,
        "dependencies_are_topological": topological,
        "hot_update_faster_than_full_evaluation": hot_speedup
        > requirements["minimum_hot_update_speedup_over_full_evaluation"],
        "hot_verified_rate_beats_blind": hot_rate_ratio
        > requirements[
            "minimum_hot_verified_normalized_quality_rate_ratio_over_blind"
        ],
    }

    summaries = []
    for mask_name in parsed["candidate_masks"]:
        rows = [row for row in records if row["mask_name"] == mask_name]
        summaries.append(
            {
                "mask_name": mask_name,
                "records": len(rows),
                "mean_changed_information_set_fraction": mean(
                    float(row["changed_full_information_sets"])
                    / float(row["full_information_sets"])
                    for row in rows
                ),
                "median_changed_information_set_fraction": median(
                    float(row["changed_full_information_sets"])
                    / float(row["full_information_sets"])
                    for row in rows
                ),
                "mean_changed_policy_entry_fraction": mean(
                    float(row["mode_diagnostics"]["sparse"]["changed_policy_entries"])
                    / float(row["mode_diagnostics"]["sparse"]["policy_input_entries"])
                    for row in rows
                ),
                "median_dirty_node_fraction": median(
                    float(row["mode_diagnostics"]["sparse"]["dirty_node_fraction"])
                    for row in rows
                ),
                "mean_dirty_node_fraction": mean(
                    float(row["mode_diagnostics"]["sparse"]["dirty_node_fraction"])
                    for row in rows
                ),
                "automatic_sparse_fraction": mean(
                    row["mode_diagnostics"]["auto"]["execution_mode"] == "sparse"
                    for row in rows
                ),
                "median_hot_update_speedup_over_full_evaluation": median(
                    float(row["full_evaluation_median_seconds"])
                    / float(row["hot_policy_update_median_seconds"])
                    for row in rows
                ),
                "accepted_candidates": sum(row["full_accepts_candidate"] for row in rows),
            }
        )

    return {
        "schema_version": 1,
        "experiment_type": "policy_delta_recertification_development_matrix",
        "status": "revealed_development_mechanism_test",
        "config": config,
        "config_sha256": hashlib.sha256(
            json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "source_artifact_sha256": artifact_sha,
        "environment": environment_metadata(),
        "counts": {
            "groups": len({row["group_id"] for row in source_records}),
            "contexts": len({row["context_id"] for row in source_records}),
            "targets": len(source_records),
            "candidate_records": len(records),
            "primary_records": len(primary),
        },
        "aggregate": {
            "maximum_absolute_evaluation_error": max(all_errors, default=0.0),
            "maximum_regenerated_label_error": max(label_errors, default=0.0),
            "acceptance_decision_mismatches": acceptance_mismatches,
            "best_response_action_mismatches": action_mismatches,
            "primary_signed_normalized_reduction": signed_normalized_reduction,
            "primary_accepted_normalized_reduction": accepted_normalized_reduction,
            "primary_solve_seconds": solve_seconds,
            "primary_full_evaluation_seconds": full_seconds,
            "primary_hot_policy_update_seconds": hot_seconds,
            "primary_compile_seconds": compile_seconds,
            "blind_normalized_reduction_per_millisecond": blind_rate,
            "ordinary_exact_gate_normalized_reduction_per_millisecond": ordinary_rate,
            "hot_tape_gate_normalized_reduction_per_millisecond": hot_rate,
            "compile_charged_tape_gate_normalized_reduction_per_millisecond": compile_rate,
            "hot_update_speedup_over_full_evaluation": hot_speedup,
            "hot_verified_rate_ratio_over_blind": hot_rate_ratio,
            "compile_charged_rate_ratio_over_blind": compile_rate_ratio,
            "compile_charged_beats_blind": compile_rate_ratio > 1.0,
            "accepted_primary_candidates": sum(
                row["full_accepts_candidate"] for row in primary
            ),
        },
        "controls": {
            "identity_passes": identity_passes,
            "record_order_invariant": order_invariant,
            "dependencies_are_topological": topological,
            "payoff_scale_and_tie_controls_are_automated_tests": True,
        },
        "gates": {
            "requirements": requirements,
            "results": gate_results,
            "passed": all(gate_results.values()),
        },
        "summaries": summaries,
        "timing": {"wall_seconds": time.perf_counter() - experiment_start},
        "sources": source_records,
        "records": records,
        "interpretation_limits": {
            "development_labels_revealed": True,
            "selector_claim_authorized": False,
            "six_player_safety_claim_authorized": False,
            "native_latency_claim_authorized": False,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_policy_delta_experiment(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "policy delta recertification: "
        f"records={result['counts']['candidate_records']}, "
        f"max_error={result['aggregate']['maximum_absolute_evaluation_error']:.3e}, "
        f"hot_speedup={result['aggregate']['hot_update_speedup_over_full_evaluation']:.3f}x, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
