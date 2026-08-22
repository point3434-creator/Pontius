"""Freeze fresh h32 post-call posteriors whose root actor is on the clock."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

import numpy as np

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .behavioral_one_seat_master import BehavioralOneSeatAxis
from .continuation_public_tree_tensor import (
    ContinuationPublicTreeTensorEvaluator,
    _state_after_public_prefix,
)
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_action_conditioned_posterior_manifest import (
    _SOURCE_SPECS,
    _digest_absent_at_commit,
    _policy_node_index,
    _source_belief,
    action_likelihood,
    observed_bet_sequence,
)
from .h32_affine_resident_cache_preflight import _strict_git_metadata
from .h32_fresh_board_panel_cache_preflight import _json_digest
from .h32_warm_search_acceptance_audit import _average_policy_from_state
from .one_seat_convex_generation import compiled_layout_path_single_visit_report
from .public_policy_tt import information_schema_for_axes, representative_public_tree
from .real_policy import policy_digest
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    serialize_result,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments/configs/h32-decision-aligned-posterior-manifest-v1.json"
)
_OUTPUT = (
    _ROOT / "experiments/results/h32-decision-aligned-posterior-manifest-v1.json"
)
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_LATIN_F_RESULT = (
    _ROOT / "experiments/results/h32-latin-f-convex-retreat-confirmation-v1.json"
)
_LATIN_F_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0260-latin-f-confirms-convex-breadth-with-two-interior-abstentions.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_decision_aligned_posterior_manifest.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_latin_f_result_sha256": _LATIN_F_RESULT,
    "expected_latin_f_decision_sha256": _LATIN_F_DECISION,
    "expected_posterior_primitive_sha256": (
        _ROOT / "src/pontius/h32_action_conditioned_posterior_manifest.py"
    ),
    "expected_continuation_sha256": (
        _ROOT / "src/pontius/continuation_public_tree_tensor.py"
    ),
    "expected_behavioral_axis_sha256": (
        _ROOT / "src/pontius/behavioral_one_seat_master.py"
    ),
    "expected_topology_gate_sha256": (
        _ROOT / "src/pontius/one_seat_convex_generation.py"
    ),
    "expected_public_policy_sha256": _ROOT / "src/pontius/public_policy_tt.py",
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_manifest_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _target_plan() -> tuple[dict[str, Any], ...]:
    rows = []
    for source_index, (source, _board, _family) in enumerate(_SOURCE_SPECS):
        bettor = source_index
        observed_responder = (bettor + 1) % 6
        acting_player = (bettor + 2) % 6
        rows.append(
            {
                "target_id": (
                    f"{source}/checks_then_bet_seat{bettor}_then_"
                    f"call_seat{observed_responder}"
                ),
                "source": source,
                "observed_bettor": bettor,
                "observed_responder": observed_responder,
                "observed_response": "call",
                "acting_player": acting_player,
                "round": "decision_aligned_call_v1",
            }
        )
    return tuple(rows)


_TARGET_PLAN = _target_plan()


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required decision-aligned manifest input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _history_text(history: Sequence[tuple[int, str]]) -> str:
    if not history:
        return "root"
    return "/".join(f"p{actor}:{action}" for actor, action in history)


def observed_bet_then_one_call_sequence(
    bettor: int,
    *,
    players: int = 6,
) -> tuple[dict[str, Any], ...]:
    """Return checks, one bet, and exactly the first responder's call."""

    if players != 6:
        raise ValueError("decision-aligned h32 sequence requires six players")
    prefix = [dict(row) for row in observed_bet_sequence(bettor)]
    history = [(int(row["actor"]), str(row["action"])) for row in prefix]
    responder = (bettor + 1) % players
    prefix.append(
        {
            "actor": responder,
            "public_history": _history_text(history),
            "action": "call",
        }
    )
    return tuple(prefix)


def public_prefix_from_observations(
    observations: Sequence[Mapping[str, Any]],
) -> tuple[tuple[int, str], ...]:
    if not observations:
        raise ValueError("decision-aligned public observations must be nonempty")
    return tuple(
        (int(observation["actor"]), str(observation["action"]))
        for observation in observations
    )


def build_public_sequence_posterior(
    source: Any,
    policy: Mapping[str, Mapping[str, float]],
    observations: Sequence[Mapping[str, Any]],
) -> tuple[Any, dict[str, Any]]:
    """Apply a frozen legal public sequence as exact unary Bayes likelihoods."""

    index = _policy_node_index(policy)
    posterior = source
    rows = []
    for supplied in observations:
        observation = {
            "actor": int(supplied["actor"]),
            "public_history": str(supplied["public_history"]),
            "action": str(supplied["action"]),
        }
        likelihood = action_likelihood(index, source, observation)
        posterior = posterior.with_likelihood(observation["actor"], likelihood)
        rows.append(
            {
                **observation,
                "likelihood_minimum": float(np.min(likelihood)),
                "likelihood_maximum": float(np.max(likelihood)),
                "likelihood_mean": float(np.mean(likelihood)),
                "positive_hand_count": int(np.count_nonzero(likelihood > 0.0)),
                "zero_hand_count": int(np.count_nonzero(likelihood == 0.0)),
            }
        )
    return posterior, {
        "construction": (
            "sequential_blueprint_action_likelihoods_for_checks_bet_and_one_call"
        ),
        "public_sequence": [dict(row) for row in observations],
        "observation_rows": rows,
        "observation_count": len(rows),
        "hand_axes_identity": posterior.hands_by_player == source.hands_by_player,
    }


def _finite_tree(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return True


def parse_h32_decision_aligned_posterior_manifest_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "freshness_base_commit",
        "seed",
        "source_specs",
        "target_plan",
        "panel_design",
        "observation_rule",
        "acting_player_rule",
        "topology_rule",
        "pot",
        "stack",
        "bet_size",
        "players",
        "hands_per_player",
        "axis_seed",
        "mixture_components",
        "split_index",
        "label_policy",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("decision-aligned manifest fields differ from ADR-0261")
    for field_name, path in _PATHS.items():
        if config[field_name] != _sha256(path):
            raise ValueError(f"decision-aligned provenance mismatch: {field_name}")
    exact = {
        "evidence_stage": (
            "preregistered_after_adr0260_before_any_decision_aligned_warm_step_"
            "convex_candidate_certificate_or_strategy_label"
        ),
        "freshness_base_commit": "f7cce5450e1b9d55b145d738cd6032820fe89abc",
        "seed": 20260822,
        "source_specs": [
            {"source": source, "board": list(board), "range_family": family}
            for source, board, family in _SOURCE_SPECS
        ],
        "target_plan": [dict(row) for row in _TARGET_PLAN],
        "panel_design": (
            "six_fixed_retained_sources_one_each_balanced_over_bettor_observed_"
            "responder_and_current_acting_player"
        ),
        "observation_rule": (
            "all_public_checks_before_the_bettor_then_bet_then_exactly_the_first_"
            "responder_calls"
        ),
        "acting_player_rule": (
            "second_responder_is_current_player_immediately_after_the_observed_call"
        ),
        "topology_rule": (
            "continuation_starts_at_current_call_fold_decision_with_three_"
            "downstream_responders_and_path_single_visit_required"
        ),
        "pot": 12.0,
        "stack": 30.0,
        "bet_size": 3.0,
        "players": 6,
        "hands_per_player": 32,
        "axis_seed": 20260819,
        "mixture_components": 3,
        "split_index": 3,
        "label_policy": (
            "zero_warm_steps_convex_candidates_quality_evaluations_certificates_"
            "or_strategy_labels_manifest_only"
        ),
    }
    for field_name, expected_value in exact.items():
        if config[field_name] != expected_value:
            raise ValueError(
                f"decision-aligned manifest field differs from ADR-0261: {field_name}"
            )
    gates = {
        "expected_sources": 6,
        "expected_targets": 6,
        "expected_targets_per_source": 1,
        "expected_targets_per_bettor": 1,
        "expected_targets_per_observed_responder": 1,
        "expected_targets_per_acting_player": 1,
        "expected_observation_rows": 27,
        "expected_remaining_responders": 4,
        "expected_acting_public_nodes": 1,
        "expected_behavioral_information_sets": 32,
        "expected_policy_variables": 64,
        "maximum_marginal_split_relative_error": 1e-12,
        "maximum_total_seconds": 600.0,
        "require_clean_git_state": True,
        "require_source_parent_passed": True,
        "require_latin_f_parent_passed": True,
        "require_live_shadow_authorized": True,
        "require_source_checkpoint_identity": True,
        "require_blueprint_identity": True,
        "require_target_id_fresh": True,
        "require_target_digest_unique": True,
        "require_target_digest_fresh": True,
        "require_target_differs_from_source": True,
        "require_nonzero_bettor_marginal_shift": True,
        "require_nonzero_observed_responder_marginal_shift": True,
        "require_nonzero_acting_player_marginal_shift": True,
        "require_hand_axes_identity": True,
        "require_legal_public_prefix": True,
        "require_current_player_alignment": True,
        "require_call_fold_root": True,
        "require_three_downstream_responders": True,
        "require_path_single_visit": True,
        "require_zero_topology_mismatches": True,
        "require_finite": True,
        "require_new_strategy_labels_zero": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("decision-aligned manifest gates differ from ADR-0261")
    return {
        **config,
        "source_specs": tuple(dict(row) for row in config["source_specs"]),
        "target_plan": tuple(dict(row) for row in config["target_plan"]),
        "gates": gates,
    }


def run_h32_decision_aligned_posterior_manifest(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Construct identities and topology only; never evaluate strategy quality."""

    started = time.perf_counter()
    parsed = parse_h32_decision_aligned_posterior_manifest_config(
        json.loads(config_path.read_text(encoding="utf-8"))
    )
    git = _strict_git_metadata()
    if git["dirty"]:
        raise RuntimeError("decision-aligned manifest requires a clean Git state")
    source_parent = load_artifact(
        _SOURCE,
        expected_sha256=parsed["expected_source_result_sha256"],
        require_passed=True,
    ).payload
    latin_f_parent = load_artifact(
        _LATIN_F_RESULT,
        expected_sha256=parsed["expected_latin_f_result_sha256"],
        require_passed=True,
    ).payload
    source_specs = {row["source"]: row for row in parsed["source_specs"]}
    parent_rows = {row["source"]: row for row in source_parent["source_rows"]}
    source_cache: dict[str, tuple[Any, Any, Any, Mapping[str, Any]]] = {}
    target_rows = []
    for target_spec in parsed["target_plan"]:
        source_key = str(target_spec["source"])
        if source_key not in source_cache:
            source = _source_belief(parsed, source_specs[source_key])
            state = parent_rows[source_key]["final_checkpoint"]
            blueprint = _average_policy_from_state(state)
            source_marginals = source.meet_in_middle_contract(
                tuple(range(int(parsed["split_index"])))
            )
            source_cache[source_key] = (source, blueprint, source_marginals, state)
        source, blueprint, source_marginals, _state = source_cache[source_key]
        bettor = int(target_spec["observed_bettor"])
        observed_responder = int(target_spec["observed_responder"])
        acting_player = int(target_spec["acting_player"])
        observations = observed_bet_then_one_call_sequence(bettor)
        public_prefix = public_prefix_from_observations(observations)
        posterior, descriptor = build_public_sequence_posterior(
            source,
            blueprint,
            observations,
        )
        target_marginals = posterior.meet_in_middle_contract(
            tuple(range(int(parsed["split_index"])))
        )
        tvs = [
            0.5 * float(np.sum(np.abs(before - after)))
            for before, after in zip(
                source_marginals.marginals,
                target_marginals.marginals,
                strict=True,
            )
        ]

        full = representative_public_tree(
            source,
            pot=float(parsed["pot"]),
            stack=float(parsed["stack"]),
            bet_size=float(parsed["bet_size"]),
        )
        continuation = ContinuationPublicTreeTensorEvaluator(
            full.game,
            public_prefix=public_prefix,
        )
        root_state = _state_after_public_prefix(
            full.game,
            full.deals[0],
            public_prefix,
        )
        schema = information_schema_for_axes(
            continuation,
            posterior.hands_by_player,
        )
        restricted_blueprint = {key: dict(blueprint[key]) for key in schema}
        axis = BehavioralOneSeatAxis.compile(
            continuation,
            posterior.hands_by_player,
            restricted_blueprint,
            acting_player=acting_player,
        )
        topology = compiled_layout_path_single_visit_report(continuation)
        row = {
            **descriptor,
            **target_spec,
            "public_prefix": [list(item) for item in public_prefix],
            "source_belief_sha256": _belief_digest(source),
            "target_belief_sha256": _belief_digest(posterior),
            "marginal_total_variation_by_seat": tvs,
            "maximum_marginal_total_variation": max(tvs),
            "observed_bettor_marginal_total_variation": tvs[bettor],
            "observed_responder_marginal_total_variation": tvs[observed_responder],
            "acting_player_marginal_total_variation": tvs[acting_player],
            "source_split_relative_error": (
                source_marginals.split_partition_relative_error
            ),
            "target_split_relative_error": (
                target_marginals.split_partition_relative_error
            ),
            "root_current_player": root_state.current_player,
            "root_legal_actions": list(root_state.legal_actions()),
            "remaining_responders": len(root_state.pending_responders),
            "downstream_responders_after_actor": len(root_state.pending_responders) - 1,
            "continuation_public_nodes": len(continuation.nodes),
            "acting_public_nodes": len(axis.acting_nodes),
            "behavioral_information_sets": len(axis.information_sets),
            "policy_variables": axis.variable_count,
            "path_single_visit": topology.passed,
            "topology_mismatch_count": continuation.topology_mismatch_count(),
        }
        descriptor_digest = _json_digest(row)
        target_rows.append(
            {
                **row,
                "target_descriptor_sha256": descriptor_digest,
                "target_id_fresh_at_base_commit": _digest_absent_at_commit(
                    row["target_id"], parsed["freshness_base_commit"]
                ),
                "target_digest_fresh_at_base_commit": _digest_absent_at_commit(
                    row["target_belief_sha256"], parsed["freshness_base_commit"]
                )
                and _digest_absent_at_commit(
                    descriptor_digest,
                    parsed["freshness_base_commit"],
                ),
            }
        )

    source_counts = Counter(row["source"] for row in target_rows)
    bettor_counts = Counter(int(row["observed_bettor"]) for row in target_rows)
    responder_counts = Counter(
        int(row["observed_responder"]) for row in target_rows
    )
    acting_counts = Counter(int(row["acting_player"]) for row in target_rows)
    digests = [row["target_belief_sha256"] for row in target_rows]
    source_identity = all(
        axis_cfr_checkpoint_digest(source_cache[key][3])
        == source_cache[key][3]["state_sha256"]
        and _belief_digest(source_cache[key][0])
        == parent_rows[key]["source_belief_sha256"]
        for key in source_cache
    )
    blueprint_identity = all(
        policy_digest(source_cache[key][1])
        == source_cache[key][3]["average_policy_sha256"]
        for key in source_cache
    )
    total_seconds = time.perf_counter() - started
    gate = parsed["gates"]
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "source_parent_passed": artifact_passed(source_parent)
        == gate["require_source_parent_passed"],
        "latin_f_parent_passed": artifact_passed(latin_f_parent)
        == gate["require_latin_f_parent_passed"],
        "live_shadow_authorized": (
            latin_f_parent.get("decision")
            == "accept_latin_ef_breadth_and_authorize_live_shadow_preregistration"
        )
        == gate["require_live_shadow_authorized"],
        "source_count": len(source_cache) == gate["expected_sources"],
        "target_count": len(target_rows) == gate["expected_targets"],
        "source_balance": set(source_counts.values())
        == {gate["expected_targets_per_source"]},
        "bettor_balance": set(bettor_counts.values())
        == {gate["expected_targets_per_bettor"]},
        "observed_responder_balance": set(responder_counts.values())
        == {gate["expected_targets_per_observed_responder"]},
        "acting_player_balance": set(acting_counts.values())
        == {gate["expected_targets_per_acting_player"]},
        "observation_count": sum(row["observation_count"] for row in target_rows)
        == gate["expected_observation_rows"],
        "source_checkpoint_identity": source_identity
        == gate["require_source_checkpoint_identity"],
        "blueprint_identity": blueprint_identity == gate["require_blueprint_identity"],
        "target_id_fresh": all(
            row["target_id_fresh_at_base_commit"] for row in target_rows
        )
        == gate["require_target_id_fresh"],
        "target_digest_unique": (len(set(digests)) == len(digests))
        == gate["require_target_digest_unique"],
        "target_digest_fresh": all(
            row["target_digest_fresh_at_base_commit"] for row in target_rows
        )
        == gate["require_target_digest_fresh"],
        "target_differs_from_source": all(
            row["target_belief_sha256"] != row["source_belief_sha256"]
            for row in target_rows
        )
        == gate["require_target_differs_from_source"],
        "nonzero_bettor_marginal_shift": all(
            row["observed_bettor_marginal_total_variation"] > 0.0
            for row in target_rows
        )
        == gate["require_nonzero_bettor_marginal_shift"],
        "nonzero_observed_responder_marginal_shift": all(
            row["observed_responder_marginal_total_variation"] > 0.0
            for row in target_rows
        )
        == gate["require_nonzero_observed_responder_marginal_shift"],
        "nonzero_acting_player_marginal_shift": all(
            row["acting_player_marginal_total_variation"] > 0.0
            for row in target_rows
        )
        == gate["require_nonzero_acting_player_marginal_shift"],
        "hand_axes_identity": all(row["hand_axes_identity"] for row in target_rows)
        == gate["require_hand_axes_identity"],
        "legal_public_prefix": all(
            row["observed_responder"] == (row["observed_bettor"] + 1) % 6
            and row["observed_response"] == "call"
            for row in target_rows
        )
        == gate["require_legal_public_prefix"],
        "current_player_alignment": all(
            row["root_current_player"] == row["acting_player"]
            == (row["observed_bettor"] + 2) % 6
            for row in target_rows
        )
        == gate["require_current_player_alignment"],
        "call_fold_root": all(
            row["root_legal_actions"] == ["fold", "call"] for row in target_rows
        )
        == gate["require_call_fold_root"],
        "three_downstream_responders": all(
            row["remaining_responders"] == gate["expected_remaining_responders"]
            and row["downstream_responders_after_actor"] == 3
            for row in target_rows
        )
        == gate["require_three_downstream_responders"],
        "axis_counts": all(
            row["acting_public_nodes"] == gate["expected_acting_public_nodes"]
            and row["behavioral_information_sets"]
            == gate["expected_behavioral_information_sets"]
            and row["policy_variables"] == gate["expected_policy_variables"]
            for row in target_rows
        ),
        "path_single_visit": all(row["path_single_visit"] for row in target_rows)
        == gate["require_path_single_visit"],
        "zero_topology_mismatches": all(
            row["topology_mismatch_count"] == 0 for row in target_rows
        )
        == gate["require_zero_topology_mismatches"],
        "marginal_split_identity": max(
            max(row["source_split_relative_error"], row["target_split_relative_error"])
            for row in target_rows
        )
        <= gate["maximum_marginal_split_relative_error"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": _finite_tree(target_rows) == gate["require_finite"],
        "new_strategy_labels_zero": True == gate["require_new_strategy_labels_zero"],
        "strategy_population_claim_null": True
        == gate["require_strategy_population_claim_null"],
    }
    gate_result = finalize_gates(checks)
    result = {
        "schema_version": 1,
        "status": "h32_decision_aligned_posterior_manifest_executed",
        "environment": assemble_environment(runtime={"kind": "cpu_only"}, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "new_warm_steps": 0,
            "convex_candidates": 0,
            "quality_evaluations": 0,
            "certificates": 0,
            "strategy_labels": 0,
            "posterior_targets_constructed": len(target_rows),
            "continuation_topologies_compiled": len(target_rows),
        },
        "target_rows": target_rows,
        "aggregate": {
            "source_counts": dict(sorted(source_counts.items())),
            "bettor_counts": {
                str(key): value for key, value in sorted(bettor_counts.items())
            },
            "observed_responder_counts": {
                str(key): value for key, value in sorted(responder_counts.items())
            },
            "acting_player_counts": {
                str(key): value for key, value in sorted(acting_counts.items())
            },
            "observation_rows": sum(row["observation_count"] for row in target_rows),
            "minimum_acting_player_marginal_tv": min(
                row["acting_player_marginal_total_variation"] for row in target_rows
            ),
            "maximum_acting_player_marginal_tv": max(
                row["acting_player_marginal_total_variation"] for row in target_rows
            ),
            "minimum_observed_responder_marginal_tv": min(
                row["observed_responder_marginal_total_variation"]
                for row in target_rows
            ),
            "maximum_observed_responder_marginal_tv": max(
                row["observed_responder_marginal_total_variation"]
                for row in target_rows
            ),
            "acting_public_nodes_per_target": sorted(
                {row["acting_public_nodes"] for row in target_rows}
            ),
            "downstream_responders_per_target": sorted(
                {row["downstream_responders_after_actor"] for row in target_rows}
            ),
        },
        **gate_result,
        "decision": (
            "authorize_preregistered_decision_aligned_live_shadow_trial"
            if gate_result["passed"]
            else "reject_decision_aligned_live_shadow_panel"
        ),
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            "The six boards and source blueprints are retained; freshness applies to the deeper post-call posterior identities.",
            "Every target observes a call, so this panel does not test a post-fold posterior.",
            "The panel is structurally balanced but is not an IID sample of deployment decisions.",
            "Marginal TV and topology are label-free descriptors, not strategy-opportunity labels.",
            "No warm step, candidate, certificate, strategy quality, deployment, or poker-strength claim is made.",
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_decision_aligned_posterior_manifest(args.config, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "decision": result["decision"],
                "aggregate": result["aggregate"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
