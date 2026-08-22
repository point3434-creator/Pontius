"""Freeze the last unused Latin posterior panel for convex-retreat replication."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping

import numpy as np

from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_action_conditioned_posterior_manifest import (
    _SOURCE_SPECS,
    _TARGET_PLAN as _OPENED_PLAN,
    _digest_absent_at_commit,
    _source_belief,
    build_action_conditioned_posterior,
)
from .h32_affine_resident_cache_preflight import _strict_git_metadata
from .h32_fresh_board_panel_cache_preflight import _json_digest
from .h32_heldout_continuation_posterior_manifest import (
    _TARGET_PLAN as _HELDOUT_PLAN,
)
from .h32_warm_search_acceptance_audit import _average_policy_from_state
from .real_policy import policy_digest
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    serialize_result,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-convex-replication-posterior-manifest-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-convex-replication-posterior-manifest-v1.json"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_OPENED = _ROOT / "experiments/results/h32-action-conditioned-posterior-manifest-v1.json"
_HELDOUT = (
    _ROOT / "experiments/results/h32-heldout-continuation-posterior-manifest-v1.json"
)
_PARENT = (
    _ROOT
    / "docs/decisions/ADR-0252-convex-retreat-beats-the-live-fallback-on-the-frozen-target.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_convex_replication_posterior_manifest.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_opened_manifest_sha256": _OPENED,
    "expected_heldout_manifest_sha256": _HELDOUT,
    "expected_parent_decision_sha256": _PARENT,
    "expected_posterior_implementation_sha256": (
        _ROOT / "src/pontius/h32_action_conditioned_posterior_manifest.py"
    ),
    "expected_heldout_implementation_sha256": (
        _ROOT / "src/pontius/h32_heldout_continuation_posterior_manifest.py"
    ),
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_manifest_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_TARGET_PLAN = tuple(
    {
        "target_id": f"{source}/checks_then_bet_seat{(source_index + offset) % 6}",
        "source": source,
        "observed_bettor": (source_index + offset) % 6,
        "acting_player": ((source_index + offset) % 6 - 1) % 6,
        "round": round_name,
    }
    for round_name, offset in (("latin_e", 2), ("latin_f", 5))
    for source_index, (source, _board, _family) in enumerate(_SOURCE_SPECS)
)


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required convex replication manifest input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def parse_h32_convex_replication_manifest_config(
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
        "acting_player_rule",
        "posterior_construction",
        "players",
        "hands_per_player",
        "axis_seed",
        "mixture_components",
        "split_index",
        "label_policy",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("convex replication manifest config fields differ from ADR-0253")
    for field_name, path in _PATHS.items():
        if config[field_name] != _sha256(path):
            raise ValueError(f"convex replication provenance mismatch: {field_name}")
    exact = {
        "evidence_stage": (
            "preregistered_after_adr0252_before_any_latin_ef_posterior_warm_"
            "step_convex_candidate_or_strategy_label"
        ),
        "freshness_base_commit": "7f0c2bb6e694d71ee777055a38e5b27a181998db",
        "seed": 20260822,
        "source_specs": [
            {"source": source, "board": list(board), "range_family": family}
            for source, board, family in _SOURCE_SPECS
        ],
        "target_plan": [dict(row) for row in _TARGET_PLAN],
        "panel_design": (
            "latin_offsets_two_and_five_complete_the_36_source_bettor_"
            "combinations_disjoint_from_opened_ab_and_heldout_cd"
        ),
        "acting_player_rule": (
            "last_responder_immediately_before_observed_bettor_modulo_six_"
            "yields_widest_16_public_node_axis"
        ),
        "posterior_construction": (
            "multiply_every_observed_check_and_final_bet_blueprint_likelihood_"
            "in_public_order"
        ),
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
                f"convex replication manifest field differs from ADR-0253: {field_name}"
            )
    gates = {
        "expected_sources": 6,
        "expected_targets": 12,
        "expected_targets_per_source": 2,
        "expected_targets_per_bettor": 2,
        "expected_targets_per_acting_player": 2,
        "expected_observation_rows": 42,
        "maximum_marginal_split_relative_error": 1e-12,
        "maximum_total_seconds": 600.0,
        "require_clean_git_state": True,
        "require_source_parent_passed": True,
        "require_opened_parent_passed": True,
        "require_heldout_parent_passed": True,
        "require_source_checkpoint_identity": True,
        "require_blueprint_identity": True,
        "require_disjoint_from_both_opened_panels": True,
        "require_complete_source_bettor_latin_square": True,
        "require_target_id_fresh": True,
        "require_target_digest_unique": True,
        "require_target_digest_fresh": True,
        "require_target_differs_from_source": True,
        "require_nonzero_bettor_marginal_shift": True,
        "require_nonzero_acting_player_marginal_shift": True,
        "require_last_responder_acting_player": True,
        "require_hand_axes_identity": True,
        "require_finite": True,
        "require_new_strategy_labels_zero": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("convex replication manifest gates differ from ADR-0253")
    return {
        **config,
        "source_specs": tuple(dict(row) for row in config["source_specs"]),
        "target_plan": tuple(dict(row) for row in config["target_plan"]),
        "gates": gates,
    }


def run_h32_convex_replication_posterior_manifest(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = parse_h32_convex_replication_manifest_config(
        json.loads(config_path.read_text(encoding="utf-8"))
    )
    git = _strict_git_metadata()
    if git["dirty"]:
        raise RuntimeError("convex replication manifest requires a clean Git state")
    source_parent = load_artifact(
        _SOURCE,
        expected_sha256=parsed["expected_source_result_sha256"],
        require_passed=True,
    ).payload
    opened_parent = load_artifact(
        _OPENED,
        expected_sha256=parsed["expected_opened_manifest_sha256"],
        require_passed=True,
    ).payload
    heldout_parent = load_artifact(
        _HELDOUT,
        expected_sha256=parsed["expected_heldout_manifest_sha256"],
        require_passed=True,
    ).payload
    prior_rows = [*opened_parent["target_rows"], *heldout_parent["target_rows"]]
    prior_ids = {row["target_id"] for row in prior_rows}
    source_specs = {row["source"]: row for row in parsed["source_specs"]}
    parent_rows = {row["source"]: row for row in source_parent["source_rows"]}
    source_cache = {}
    target_rows = []
    for target_spec in parsed["target_plan"]:
        source_key = str(target_spec["source"])
        if source_key not in source_cache:
            source = _source_belief(parsed, source_specs[source_key])
            state = parent_rows[source_key]["final_checkpoint"]
            blueprint = _average_policy_from_state(state)
            marginals = source.meet_in_middle_contract(
                tuple(range(int(parsed["split_index"])))
            )
            source_cache[source_key] = (source, blueprint, marginals, state)
        source, blueprint, source_marginals, _state = source_cache[source_key]
        bettor = int(target_spec["observed_bettor"])
        acting_player = int(target_spec["acting_player"])
        posterior, descriptor = build_action_conditioned_posterior(
            source,
            blueprint,
            bettor=bettor,
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
        row = {
            **descriptor,
            **target_spec,
            "source_belief_sha256": _belief_digest(source),
            "target_belief_sha256": _belief_digest(posterior),
            "marginal_total_variation_by_seat": tvs,
            "maximum_marginal_total_variation": max(tvs),
            "observed_bettor_marginal_total_variation": tvs[bettor],
            "convex_acting_player_marginal_total_variation": tvs[acting_player],
            "source_split_relative_error": (
                source_marginals.split_partition_relative_error
            ),
            "target_split_relative_error": (
                target_marginals.split_partition_relative_error
            ),
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
    all_combinations = {
        (row["source"], int(row["observed_bettor"]))
        for row in [*prior_rows, *target_rows]
    }
    total_seconds = time.perf_counter() - started
    gate = parsed["gates"]
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "source_parent_passed": artifact_passed(source_parent)
        == gate["require_source_parent_passed"],
        "opened_parent_passed": artifact_passed(opened_parent)
        == gate["require_opened_parent_passed"],
        "heldout_parent_passed": artifact_passed(heldout_parent)
        == gate["require_heldout_parent_passed"],
        "source_count": len(source_cache) == gate["expected_sources"],
        "target_count": len(target_rows) == gate["expected_targets"],
        "source_balance": set(source_counts.values())
        == {gate["expected_targets_per_source"]},
        "bettor_balance": set(bettor_counts.values())
        == {gate["expected_targets_per_bettor"]},
        "acting_player_balance": set(acting_counts.values())
        == {gate["expected_targets_per_acting_player"]},
        "observation_count": sum(row["observation_count"] for row in target_rows)
        == gate["expected_observation_rows"],
        "source_checkpoint_identity": source_identity
        == gate["require_source_checkpoint_identity"],
        "blueprint_identity": blueprint_identity == gate["require_blueprint_identity"],
        "disjoint_from_both_opened_panels": all(
            row["target_id"] not in prior_ids for row in target_rows
        )
        == gate["require_disjoint_from_both_opened_panels"],
        "complete_source_bettor_latin_square": (len(all_combinations) == 36)
        == gate["require_complete_source_bettor_latin_square"],
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
        "nonzero_acting_player_marginal_shift": all(
            row["convex_acting_player_marginal_total_variation"] > 0.0
            for row in target_rows
        )
        == gate["require_nonzero_acting_player_marginal_shift"],
        "last_responder_acting_player": all(
            row["acting_player"] == (row["observed_bettor"] - 1) % 6
            for row in target_rows
        )
        == gate["require_last_responder_acting_player"],
        "hand_axes_identity": all(row["hand_axes_identity"] for row in target_rows)
        == gate["require_hand_axes_identity"],
        "marginal_split_identity": max(
            max(row["source_split_relative_error"], row["target_split_relative_error"])
            for row in target_rows
        )
        <= gate["maximum_marginal_split_relative_error"],
        "total_time": total_seconds <= gate["maximum_total_seconds"],
        "finite": _finite_tree(target_rows) == gate["require_finite"],
        "new_strategy_labels_zero": gate["require_new_strategy_labels_zero"],
        "strategy_population_claim_null": gate["require_strategy_population_claim_null"],
    }
    gate_result = finalize_gates(checks)
    result = {
        "schema_version": 1,
        "status": "h32_convex_replication_posterior_manifest_executed",
        "environment": assemble_environment(runtime={"kind": "cpu_only"}, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "new_warm_steps": 0,
            "convex_candidates": 0,
            "quality_evaluations": 0,
            "certificates": 0,
            "strategy_labels": 0,
        },
        "target_rows": target_rows,
        "aggregate": {
            "source_counts": dict(sorted(source_counts.items())),
            "bettor_counts": {
                str(key): value for key, value in sorted(bettor_counts.items())
            },
            "acting_player_counts": {
                str(key): value for key, value in sorted(acting_counts.items())
            },
            "observation_rows": sum(row["observation_count"] for row in target_rows),
            "minimum_bettor_marginal_tv": min(
                row["observed_bettor_marginal_total_variation"]
                for row in target_rows
            ),
            "maximum_bettor_marginal_tv": max(
                row["observed_bettor_marginal_total_variation"]
                for row in target_rows
            ),
            "minimum_acting_player_marginal_tv": min(
                row["convex_acting_player_marginal_total_variation"]
                for row in target_rows
            ),
            "maximum_acting_player_marginal_tv": max(
                row["convex_acting_player_marginal_total_variation"]
                for row in target_rows
            ),
            "complete_source_bettor_combinations": len(all_combinations),
        },
        **gate_result,
        "decision": (
            "authorize_preregistered_fresh_convex_retreat_replication"
            if gate_result["passed"]
            else "reject_convex_replication_posterior_panel"
        ),
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            (
                "The source boards and blueprints are retained; only the Latin-E/F "
                "source-bettor combinations are fresh."
            ),
            (
                "Posterior marginal TV is a belief descriptor, not a "
                "strategy-opportunity label."
            ),
            (
                "No convex candidate, strategy quality, transfer, deployment, or "
                "population claim is made."
            ),
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_convex_replication_posterior_manifest(args.config, args.output)
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
