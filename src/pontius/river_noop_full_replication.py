"""Fresh fixed-rule replication for the river no-op/full computation gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from .cfr import TabularCFR
from .depth_limited import PolicyContinuationValues
from .evaluation import Policy, evaluate_profile
from .reporting import environment_metadata
from .river_context import CONTEXT_FAMILIES, generate_river_contexts
from .river_incremental import RiverRangeDelta
from .river_selective import (
    MultiSizeExpansionMask,
    complete_information_schema,
    compose_selective_policy,
    multi_size_state_cache_key,
)
from .river_selective_experiment import (
    _boundary_online_features,
    _build_blueprint,
    _range_targets,
    _wide_game,
)
from .river_selective_screen import NO_OP, _compact_oracle, _evaluate_selections
from .selective_tree import (
    SelectiveExpansionGame,
    collect_selective_cutoff_states,
    full_tree_state_count,
)
from .updates import UPDATE_RULES

_CONFIG_FIELDS = {
    "evidence_stage",
    "requested_groups",
    "seed",
    "hands_per_player",
    "families",
    "included_splits",
    "bet_pot_fractions",
    "raise_to_pot_fractions",
    "candidate_masks",
    "blueprint_solver",
    "blueprint_quality_checkpoints",
    "online_solver",
    "warm_start_multiplier_by_searched_game_payoff_span",
    "full_tree_equivalent_iteration_budget",
    "target_names",
    "root_tv_budget",
    "maximum_donor_fraction",
    "factorized_likelihood_minimum",
    "factorized_likelihood_maximum",
    "frozen_rule",
    "frozen_rule_sha256",
    "discovery_source_artifact",
    "discovery_source_artifact_sha256",
    "expected_selective_tree_sha256",
    "expected_river_selective_sha256",
    "expected_selective_experiment_sha256",
    "gates",
}
_GATE_FIELDS = {
    "minimum_development_board_groups",
    "maximum_source_normalized_nash_conv",
    "aggregate_raw_reduction_strictly_beats_fixed_b3r2",
    "aggregate_normalized_reduction_strictly_beats_fixed_b3r2",
    "minimum_positive_raw_uplift_group_fraction",
    "minimum_compact_oracle_opportunity_capture_fraction",
    "aggregate_state_visits_not_above_fixed_b3r2",
    "charged_raw_reduction_per_millisecond_strictly_beats_fixed_b3r2",
    "maximum_selected_target_harm_not_above_fixed_b3r2",
    "minimum_each_rule_arm_fraction",
}
_TARGET_NAMES = (
    "blocker_reweight_p0",
    "blocker_reweight_p1",
    "factorized_likelihood_p0",
)
_SOURCE_FILES = {
    "expected_selective_tree_sha256": "selective_tree.py",
    "expected_river_selective_sha256": "river_selective.py",
    "expected_selective_experiment_sha256": "river_selective_experiment.py",
}
_TOLERANCE = 1e-12


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _validate_masks(raw_masks: object) -> tuple[dict[str, object], ...]:
    if not isinstance(raw_masks, list) or len(raw_masks) != 2:
        raise ValueError("replication requires exactly b3r1 and b3r2 masks")
    result = []
    for raw in raw_masks:
        if not isinstance(raw, dict) or set(raw) != {
            "name",
            "expanded_bet_pot_fractions",
            "expanded_raise_to_pot_fractions",
        }:
            raise ValueError("candidate mask schema does not match ADR-0050")
        result.append(
            {
                "name": str(raw["name"]),
                "expanded_bet_pot_fractions": tuple(
                    float(value) for value in raw["expanded_bet_pot_fractions"]
                ),
                "expanded_raise_to_pot_fractions": tuple(
                    float(value) for value in raw["expanded_raise_to_pot_fractions"]
                ),
            }
        )
    expected = (
        {
            "name": "b3r1",
            "expanded_bet_pot_fractions": (0.25, 0.5, 0.75),
            "expanded_raise_to_pot_fractions": (1.5,),
        },
        {
            "name": "b3r2",
            "expanded_bet_pot_fractions": (0.25, 0.5, 0.75),
            "expanded_raise_to_pot_fractions": (1.5, 2.0),
        },
    )
    if tuple(result) != expected:
        raise ValueError("candidate masks differ from the frozen compact oracle")
    return tuple(result)


def _validate_config(config: dict[str, Any]) -> dict[str, Any]:
    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "no-op/full replication fields do not match the frozen schema: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    if config["evidence_stage"] != "fresh_group_separated_development_replication":
        raise ValueError("replication evidence stage cannot change")

    requested_groups = int(config["requested_groups"])
    seed = int(config["seed"])
    hands = int(config["hands_per_player"])
    families = tuple(str(value) for value in config["families"])
    splits = tuple(str(value) for value in config["included_splits"])
    bets = tuple(float(value) for value in config["bet_pot_fractions"])
    raises = tuple(float(value) for value in config["raise_to_pot_fractions"])
    masks = _validate_masks(config["candidate_masks"])
    blueprint_solver = str(config["blueprint_solver"])
    checkpoints = tuple(int(value) for value in config["blueprint_quality_checkpoints"])
    online_solver = str(config["online_solver"])
    warm = float(config["warm_start_multiplier_by_searched_game_payoff_span"])
    budget = int(config["full_tree_equivalent_iteration_budget"])
    target_names = tuple(str(value) for value in config["target_names"])
    root_tv = float(config["root_tv_budget"])
    donor_fraction = float(config["maximum_donor_fraction"])
    likelihood_min = float(config["factorized_likelihood_minimum"])
    likelihood_max = float(config["factorized_likelihood_maximum"])
    if requested_groups != 36 or seed != 20261219:
        raise ValueError("fresh group count and seed are frozen by ADR-0050")
    if hands != 4 or families != CONTEXT_FAMILIES or splits != ("development",):
        raise ValueError("fresh context family and split contract changed")
    if bets != (0.25, 0.5, 0.75) or raises != (1.5, 2.0):
        raise ValueError("searched 3x2 action universe changed")
    if blueprint_solver != "dcfr" or online_solver != "dcfr":
        raise ValueError("replication solvers must remain DCFR")
    if checkpoints != (512, 1024, 2048, 4096):
        raise ValueError("blueprint checkpoints changed")
    if not math.isfinite(warm) or warm != 0.1 or budget != 32:
        raise ValueError("warm mass and work budget changed")
    if target_names != _TARGET_NAMES:
        raise ValueError("range targets changed")
    if (
        root_tv != 0.01
        or donor_fraction != 0.75
        or likelihood_min != 0.5
        or likelihood_max != 1.5
    ):
        raise ValueError("range perturbation contract changed")
    if blueprint_solver not in UPDATE_RULES or online_solver not in UPDATE_RULES:
        raise ValueError("unsupported solver")

    paths = {}
    for name in ("frozen_rule", "discovery_source_artifact"):
        value = str(config[name])
        if not value or Path(value).is_absolute():
            raise ValueError(f"{name} must be workspace relative")
        paths[name] = value
    hashes = {}
    for name in (
        "frozen_rule_sha256",
        "discovery_source_artifact_sha256",
        *_SOURCE_FILES,
    ):
        value = str(config[name])
        if not _is_sha256(value):
            raise ValueError(f"{name} must be a lowercase SHA-256")
        hashes[name] = value

    raw_gates = config["gates"]
    if not isinstance(raw_gates, dict) or set(raw_gates) != _GATE_FIELDS:
        raise ValueError("replication gates do not match ADR-0050")
    gates: dict[str, float | int | bool] = {
        "minimum_development_board_groups": int(
            raw_gates["minimum_development_board_groups"]
        ),
        "maximum_source_normalized_nash_conv": float(
            raw_gates["maximum_source_normalized_nash_conv"]
        ),
        "minimum_positive_raw_uplift_group_fraction": float(
            raw_gates["minimum_positive_raw_uplift_group_fraction"]
        ),
        "minimum_compact_oracle_opportunity_capture_fraction": float(
            raw_gates["minimum_compact_oracle_opportunity_capture_fraction"]
        ),
        "minimum_each_rule_arm_fraction": float(
            raw_gates["minimum_each_rule_arm_fraction"]
        ),
    }
    boolean_gates = _GATE_FIELDS - set(gates)
    for name in boolean_gates:
        if raw_gates[name] is not True:
            raise ValueError(f"replication gate {name!r} must remain enabled")
        gates[name] = True
    if gates["minimum_development_board_groups"] != 20:
        raise ValueError("minimum fresh board groups changed")
    if gates["maximum_source_normalized_nash_conv"] != 1e-5:
        raise ValueError("source blueprint quality gate changed")
    for name in (
        "minimum_positive_raw_uplift_group_fraction",
        "minimum_compact_oracle_opportunity_capture_fraction",
        "minimum_each_rule_arm_fraction",
    ):
        value = float(gates[name])
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"fraction gate {name!r} must lie in [0, 1]")

    return {
        "evidence_stage": str(config["evidence_stage"]),
        "requested_groups": requested_groups,
        "seed": seed,
        "hands_per_player": hands,
        "families": families,
        "included_splits": splits,
        "bet_pot_fractions": bets,
        "raise_to_pot_fractions": raises,
        "candidate_masks": masks,
        "blueprint_solver": blueprint_solver,
        "blueprint_quality_checkpoints": checkpoints,
        "online_solver": online_solver,
        "warm_start_multiplier_by_searched_game_payoff_span": warm,
        "full_tree_equivalent_iteration_budget": budget,
        "target_names": target_names,
        "root_tv_budget": root_tv,
        "maximum_donor_fraction": donor_fraction,
        "factorized_likelihood_minimum": likelihood_min,
        "factorized_likelihood_maximum": likelihood_max,
        **paths,
        **hashes,
        "gates": gates,
    }


def _read_frozen(
    root: Path,
    relative: str,
    expected_sha: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = (root / relative).resolve()
    if root.resolve() not in path.parents:
        raise ValueError("frozen input resolves outside the workspace")
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_sha:
        raise ValueError(f"frozen input hash mismatch for {relative}")
    return json.loads(payload), {
        "path": str(path),
        "sha256": digest,
        "bytes": len(payload),
    }


def _source_file_sha256(filename: str) -> str:
    return hashlib.sha256(Path(__file__).with_name(filename).read_bytes()).hexdigest()


def _validate_rule(rule: dict[str, Any], parsed: dict[str, Any]) -> dict[str, Any]:
    if rule.get("rule_id") != "river-noop-full-gate-v1":
        raise ValueError("unexpected no-op/full rule id")
    if rule.get("status") != "frozen_before_fresh_development_replication":
        raise ValueError("no-op/full rule is not frozen for replication")
    decision = rule.get("decision")
    if not isinstance(decision, dict) or decision != {
        "feature": "range_delta_changed_deal_fraction",
        "operator": "<=",
        "threshold": 0.14835164835164835,
        "true_arm": "no_op",
        "false_arm": "b3r2",
        "tie_arm": "no_op",
    }:
        raise ValueError("frozen no-op/full decision changed")
    regime = rule.get("solver_regime")
    if not isinstance(regime, dict) or (
        regime.get("online_solver") != parsed["online_solver"]
        or float(regime.get("warm_start_multiplier_by_searched_game_payoff_span", -1.0))
        != parsed["warm_start_multiplier_by_searched_game_payoff_span"]
        or int(regime.get("full_tree_equivalent_iteration_budget", -1))
        != parsed["full_tree_equivalent_iteration_budget"]
        or regime.get("search_mask") != "b3r2"
        or regime.get("diagnostic_oracle_mask") != "b3r1"
    ):
        raise ValueError("rule and replication solver regimes differ")
    return decision


def choose_rule_arm(changed_deal_fraction: float, decision: dict[str, Any]) -> str:
    if not math.isfinite(changed_deal_fraction) or not 0.0 <= changed_deal_fraction <= 1.0:
        raise ValueError("changed-deal fraction must lie in [0, 1]")
    return (
        str(decision["true_arm"])
        if changed_deal_fraction <= float(decision["threshold"])
        else str(decision["false_arm"])
    )


def _helper_config(parsed: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_stage": "group_separated_development",
        "blueprint_solver": parsed["blueprint_solver"],
        "blueprint_quality_checkpoints": parsed["blueprint_quality_checkpoints"],
        "bet_pot_fractions": parsed["bet_pot_fractions"],
        "raise_to_pot_fractions": parsed["raise_to_pot_fractions"],
        "target_names": parsed["target_names"],
        "root_tv_budget": parsed["root_tv_budget"],
        "maximum_donor_fraction": parsed["maximum_donor_fraction"],
        "factorized_likelihood_minimum": parsed["factorized_likelihood_minimum"],
        "factorized_likelihood_maximum": parsed["factorized_likelihood_maximum"],
        "gates": {
            "maximum_source_normalized_nash_conv": parsed["gates"][
                "maximum_source_normalized_nash_conv"
            ]
        },
    }


def _candidate_record(
    *,
    target: Any,
    blueprint: Policy,
    baseline_nash_conv: float,
    target_schema: dict[str, tuple[object, ...]],
    mask_config: dict[str, object],
    parsed: dict[str, Any],
) -> dict[str, Any]:
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
    leaf_seconds = time.perf_counter() - leaf_start
    selective_schema = complete_information_schema(selective)
    full_states = full_tree_state_count(target.initial_state())
    full_iteration_visits = target.num_players * full_states
    selective_iteration_visits = target.num_players * selective_states
    state_visit_budget = (
        parsed["full_tree_equivalent_iteration_budget"] * full_iteration_visits
    )
    iterations = max(1, state_visit_budget // selective_iteration_visits)
    solver = TabularCFR(selective, variant=parsed["online_solver"])
    initialization_start = time.perf_counter()
    solver.warm_start_from_schema(
        blueprint,
        regret_mass=(
            parsed["warm_start_multiplier_by_searched_game_payoff_span"]
            * target.payoff_span
        ),
        information_sets=selective_schema,
    )
    initialization_seconds = time.perf_counter() - initialization_start
    solve_start = time.perf_counter()
    solver.run(iterations)
    solve_seconds = time.perf_counter() - solve_start
    policy = compose_selective_policy(
        blueprint,
        solver.average_strategy(),
        target_schema,
    )
    label_start = time.perf_counter()
    evaluation = evaluate_profile(target, policy)
    label_seconds = time.perf_counter() - label_start
    reduction = baseline_nash_conv - evaluation.nash_conv
    actual_visits = iterations * selective_iteration_visits
    if actual_visits > state_visit_budget:
        raise AssertionError("candidate exceeded its frozen state-visit budget")
    return {
        "mask_name": mask_name,
        "solver_iterations": iterations,
        "tree_states_per_traversal": selective_states,
        "cutoff_states": len(cutoff_states),
        "state_visit_budget": state_visit_budget,
        "actual_state_visits": actual_visits,
        "exact_leaf_build_seconds": leaf_seconds,
        "initialization_seconds": initialization_seconds,
        "solve_seconds": solve_seconds,
        "cold_candidate_seconds": leaf_seconds + initialization_seconds + solve_seconds,
        "exact_label_seconds": label_seconds,
        "candidate_nash_conv": evaluation.nash_conv,
        "raw_reduction": reduction,
        "normalized_reduction": reduction / target.payoff_span,
    }


def _freshness_controls(
    discovery: dict[str, Any],
    fresh_contexts: tuple[Any, ...],
) -> dict[str, Any]:
    old_config = discovery["config"]
    old_contexts = generate_river_contexts(
        groups=int(old_config["groups"]),
        seed=int(old_config["seed"]),
        hands_per_player=int(old_config["hands_per_player"]),
        families=tuple(str(value) for value in old_config["families"]),
        splits=("development",),
        sequential_raise=False,
    )
    old_boards = {context.game.board for context in old_contexts}
    old_ranges = {context.game.provenance_digest for context in old_contexts}
    new_boards = {context.game.board for context in fresh_contexts}
    new_ranges = {context.game.provenance_digest for context in fresh_contexts}
    return {
        "discovery_board_overlap": len(old_boards & new_boards),
        "discovery_full_range_overlap": len(old_ranges & new_ranges),
        "all_returned_contexts_are_development": all(
            context.split == "development" for context in fresh_contexts
        ),
        "development_only_requested": True,
    }


def _replication_gates(
    *,
    parsed: dict[str, Any],
    group_count: int,
    blueprint_records: list[dict[str, Any]],
    fixed: dict[str, Any],
    selected: dict[str, Any],
    compact_oracle: dict[str, Any],
    freshness: dict[str, Any],
) -> tuple[dict[str, bool], dict[str, Any]]:
    requirements = parsed["gates"]
    fixed_raw = float(fixed["raw_reduction"])
    selected_raw = float(selected["raw_reduction"])
    opportunity = float(compact_oracle["raw_reduction"]) - fixed_raw
    capture = (
        (selected_raw - fixed_raw) / opportunity if opportunity > 0.0 else None
    )
    groups = set(fixed["group_raw_reduction"]) | set(selected["group_raw_reduction"])
    positive_group_fraction = mean(
        float(selected["group_raw_reduction"].get(group, 0.0))
        > float(fixed["group_raw_reduction"].get(group, 0.0)) + _TOLERANCE
        for group in groups
    )
    counts = Counter(selected["selection_counts"])
    targets = int(selected["targets"])
    minimum_arm_fraction = min(counts[NO_OP], counts["b3r2"]) / targets
    results = {
        "minimum_development_board_groups": group_count
        >= int(requirements["minimum_development_board_groups"]),
        "fresh_board_and_range_identity": (
            freshness["discovery_board_overlap"] == 0
            and freshness["discovery_full_range_overlap"] == 0
            and freshness["all_returned_contexts_are_development"]
            and freshness["development_only_requested"]
        ),
        "source_blueprint_quality": all(
            row["quality_threshold_passed"]
            and float(row["source_normalized_nash_conv"])
            <= float(requirements["maximum_source_normalized_nash_conv"])
            for row in blueprint_records
        ),
        "aggregate_raw_reduction_strictly_beats_fixed_b3r2": selected_raw
        > fixed_raw + _TOLERANCE,
        "aggregate_normalized_reduction_strictly_beats_fixed_b3r2": float(
            selected["normalized_reduction"]
        )
        > float(fixed["normalized_reduction"]) + _TOLERANCE,
        "minimum_positive_raw_uplift_group_fraction": positive_group_fraction
        >= float(requirements["minimum_positive_raw_uplift_group_fraction"]),
        "minimum_compact_oracle_opportunity_capture_fraction": capture is not None
        and capture
        >= float(requirements["minimum_compact_oracle_opportunity_capture_fraction"]),
        "aggregate_state_visits_not_above_fixed_b3r2": int(selected["state_visits"])
        <= int(fixed["state_visits"]),
        "charged_raw_reduction_per_millisecond_strictly_beats_fixed_b3r2": float(
            selected["raw_reduction_per_millisecond"]
        )
        > float(fixed["raw_reduction_per_millisecond"]),
        "maximum_selected_target_harm_not_above_fixed_b3r2": float(
            selected["maximum_target_harm"]
        )
        <= float(fixed["maximum_target_harm"]) + _TOLERANCE,
        "minimum_each_rule_arm_fraction": minimum_arm_fraction
        >= float(requirements["minimum_each_rule_arm_fraction"]),
    }
    diagnostics = {
        "compact_oracle_raw_opportunity_over_fixed": opportunity,
        "compact_oracle_opportunity_capture_fraction": capture,
        "positive_raw_uplift_group_fraction": positive_group_fraction,
        "minimum_rule_arm_fraction": minimum_arm_fraction,
        "raw_uplift_over_fixed": selected_raw - fixed_raw,
        "normalized_uplift_over_fixed": float(selected["normalized_reduction"])
        - float(fixed["normalized_reduction"]),
    }
    return results, diagnostics


def run_noop_full_replication(
    config: dict[str, Any],
    *,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    parsed = _validate_config(config)
    root = Path.cwd() if workspace_root is None else workspace_root
    rule, rule_provenance = _read_frozen(
        root,
        parsed["frozen_rule"],
        parsed["frozen_rule_sha256"],
    )
    discovery, discovery_provenance = _read_frozen(
        root,
        parsed["discovery_source_artifact"],
        parsed["discovery_source_artifact_sha256"],
    )
    decision = _validate_rule(rule, parsed)
    current_source_hashes = {
        name: _source_file_sha256(filename) for name, filename in _SOURCE_FILES.items()
    }
    if any(current_source_hashes[name] != parsed[name] for name in _SOURCE_FILES):
        raise ValueError("frozen selective source file changed before replication")

    experiment_start = time.perf_counter()
    contexts = generate_river_contexts(
        groups=parsed["requested_groups"],
        seed=parsed["seed"],
        hands_per_player=parsed["hands_per_player"],
        families=parsed["families"],
        splits=parsed["included_splits"],
        sequential_raise=False,
    )
    if not contexts:
        raise ValueError("fresh configuration generated no development contexts")
    freshness = _freshness_controls(discovery, contexts)
    helper = _helper_config(parsed)
    masks = {str(mask["name"]): mask for mask in parsed["candidate_masks"]}
    blueprint_records: list[dict[str, Any]] = []
    target_records: list[dict[str, Any]] = []
    candidate_records: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []

    for context in contexts:
        source = _wide_game(context.game, helper)
        source_schema = complete_information_schema(source)
        blueprint, source_evaluation, blueprint_metrics = _build_blueprint(source, helper)
        if set(blueprint) != set(source_schema):
            raise AssertionError("fresh blueprint is incomplete")
        blueprint_records.append(
            {
                "context_id": context.context_id,
                "group_id": context.group_id,
                "family": context.family,
                "source_provenance_digest": context.game.provenance_digest,
                "source_structural_digest": context.game.structural_digest,
                "source_payoff_span": source.payoff_span,
                **blueprint_metrics,
            }
        )

        for target_name, target_kind, range_target, target_metadata in _range_targets(
            context.game,
            helper,
        ):
            target = _wide_game(range_target, helper)
            target_schema = complete_information_schema(target)
            if target_schema != source_schema:
                raise AssertionError("fresh support-preserving target changed schema")
            delta = RiverRangeDelta.between(context.game, range_target)
            feature_start = time.perf_counter()
            boundary_features = _boundary_online_features(
                context,
                range_target,
                target,
                blueprint,
                delta,
            )
            feature_seconds = time.perf_counter() - feature_start
            changed_fraction = float(boundary_features[decision["feature"]])
            rule_arm = choose_rule_arm(changed_fraction, decision)
            baseline_start = time.perf_counter()
            baseline = evaluate_profile(target, blueprint)
            baseline_seconds = time.perf_counter() - baseline_start
            candidates = {
                mask_name: _candidate_record(
                    target=target,
                    blueprint=blueprint,
                    baseline_nash_conv=baseline.nash_conv,
                    target_schema=target_schema,
                    mask_config=masks[mask_name],
                    parsed=parsed,
                )
                for mask_name in ("b3r1", "b3r2")
            }
            target_records.append(
                {
                    "context_id": context.context_id,
                    "group_id": context.group_id,
                    "family": context.family,
                    "target_name": target_name,
                    "target_kind": target_kind,
                    "target_metadata": target_metadata,
                    "target_payoff_span": target.payoff_span,
                    "changed_deals": len(delta.changes),
                    "source_deals": len(context.game.deals),
                    "range_delta_changed_deal_fraction": changed_fraction,
                    "frozen_rule_arm": rule_arm,
                    "boundary_feature_seconds": feature_seconds,
                    "baseline_nash_conv": baseline.nash_conv,
                    "baseline_exact_evaluation_seconds": baseline_seconds,
                }
            )
            for candidate in candidates.values():
                candidate_records.append(
                    {
                        "context_id": context.context_id,
                        "group_id": context.group_id,
                        "family": context.family,
                        "target_name": target_name,
                        "target_kind": target_kind,
                        "target_payoff_span": target.payoff_span,
                        **candidate,
                    }
                )
            examples.append(
                {
                    "context_id": context.context_id,
                    "target_name": target_name,
                    "group_id": context.group_id,
                    "features": {decision["feature"]: changed_fraction},
                    "boundary_feature_seconds": feature_seconds,
                    "frozen_rule_arm": rule_arm,
                    "arms": {
                        NO_OP: {
                            "raw_reduction": 0.0,
                            "normalized_reduction": 0.0,
                            "state_visits": 0,
                            "solve_seconds": 0.0,
                            "exact_label_seconds": 0.0,
                        },
                        **{
                            mask_name: {
                                "raw_reduction": candidate["raw_reduction"],
                                "normalized_reduction": candidate[
                                    "normalized_reduction"
                                ],
                                "state_visits": candidate["actual_state_visits"],
                                "solve_seconds": candidate["cold_candidate_seconds"],
                                "exact_label_seconds": candidate["exact_label_seconds"],
                            }
                            for mask_name, candidate in candidates.items()
                        },
                    },
                }
            )

    fixed = _evaluate_selections(
        examples,
        ["b3r2"] * len(examples),
        feature_seconds=0.0,
        decision_seconds=0.0,
    )
    decision_start = time.perf_counter()
    selections = [str(row["frozen_rule_arm"]) for row in examples]
    decision_seconds = time.perf_counter() - decision_start
    selected = _evaluate_selections(
        examples,
        selections,
        feature_seconds=sum(float(row["boundary_feature_seconds"]) for row in examples),
        decision_seconds=decision_seconds,
    )
    compact_oracle = _compact_oracle(examples, (NO_OP, "b3r2", "b3r1"))
    group_count = len({context.group_id for context in contexts})
    gate_results, diagnostics = _replication_gates(
        parsed=parsed,
        group_count=group_count,
        blueprint_records=blueprint_records,
        fixed=fixed,
        selected=selected,
        compact_oracle=compact_oracle,
        freshness=freshness,
    )

    return {
        "schema_version": 1,
        "experiment_type": "river_noop_full_gate_fresh_development_replication",
        "status": (
            "fresh_development_replication_passed"
            if all(gate_results.values())
            else "fresh_development_replication_failed_retain_full_b3r2"
        ),
        "config": config,
        "config_sha256": hashlib.sha256(
            json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "environment": environment_metadata(),
        "provenance": {
            "rule": rule_provenance,
            "discovery_source": discovery_provenance,
            "source_file_hashes": current_source_hashes,
        },
        "counts": {
            "requested_groups": parsed["requested_groups"],
            "development_groups": group_count,
            "contexts": len(contexts),
            "targets": len(examples),
            "candidate_records": len(candidate_records),
        },
        "freshness": freshness,
        "fixed_b3r2": fixed,
        "frozen_rule_result": selected,
        "compact_oracle": compact_oracle,
        "replication_diagnostics": diagnostics,
        "gates": {
            "requirements": parsed["gates"],
            "results": gate_results,
            "passed": all(gate_results.values()),
        },
        "timing": {"wall_seconds": time.perf_counter() - experiment_start},
        "blueprints": blueprint_records,
        "targets": target_records,
        "candidates": candidate_records,
        "interpretation_limits": {
            "fixed_rule_was_not_refit": True,
            "b3r1_used_only_for_oracle": True,
            "reserved_validation_or_test_constructed": False,
            "individual_action_pruning_authorized": False,
            "native_specialization_authorized": False,
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
    result = run_noop_full_replication(config)
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(
        "no-op/full replication: "
        f"groups={result['counts']['development_groups']}, "
        f"targets={result['counts']['targets']}, "
        f"passed={result['gates']['passed']}, "
        f"wall={result['timing']['wall_seconds']:.3f}s"
    )
    if args.output is not None:
        print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
