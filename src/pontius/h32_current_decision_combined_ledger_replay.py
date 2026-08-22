"""Read-only ledger join for current-decision closure plus retreat proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping

from .h32_affine_resident_cache_preflight import _strict_git_metadata
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    serialize_result,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments/configs/h32-current-decision-combined-ledger-replay-v1.json"
)
_OUTPUT = (
    _ROOT / "experiments/results/h32-current-decision-combined-ledger-replay-v1.json"
)
_CLOSURE = (
    _ROOT / "experiments/results/h32-retained-convex-closure-census-v2.json"
)
_SHADOW = (
    _ROOT / "experiments/results/h32-decision-aligned-live-shadow-v1.json"
)
_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0270-current-decision-programs-close-wide-axis-census-does-not.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_current_decision_combined_ledger_replay.py"
_PATHS = {
    "expected_closure_result_sha256": _CLOSURE,
    "expected_shadow_result_sha256": _SHADOW,
    "expected_parent_decision_sha256": _DECISION,
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required combined-ledger input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_current_decision_combined_ledger_replay_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "scope",
        "pairing_rule",
        "identity_rule",
        "incremental_work_rule",
        "measured_ledger_rule",
        "conservative_ledger_rule",
        "street_budget_ms",
        "frozen_conservative_base_ms",
        "incremental_endpoint_oracle_ceiling_ms",
        "incremental_endpoint_oracle_conservative_charge_ms",
        "maximum_numerical_identity_error",
        "maximum_total_seconds",
        "label_policy",
        "decision_rule",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("combined-ledger fields differ from ADR-0271")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"combined-ledger provenance mismatch: {field}")
    exact = {
        "evidence_stage": (
            "preregistered_after_adr0270_before_any_post_fold_strategy_label"
        ),
        "scope": "six_opened_post_call_current_decision_targets_read_only",
        "pairing_rule": (
            "exact_target_id_manifest_order_join_adr0270_closure_rows_to_"
            "adr0264_safe_retreat_rows"
        ),
        "identity_rule": (
            "same_target_source_actor_cut_count_row_counts_cut_players_first_"
            "response_signatures_and_numerical_source_master_oracle_quantities"
        ),
        "incremental_work_rule": (
            "zero_for_round_zero_targets_otherwise_only_the_adr0270_post_cut_"
            "resolved_endpoint_exact_oracle"
        ),
        "measured_ledger_rule": (
            "adr0264_measured_safe_retreat_ledger_plus_measured_incremental_"
            "resolved_endpoint_oracle"
        ),
        "conservative_ledger_rule": (
            "unchanged_13967_615699994712_ms_floor_plus_zero_or_fixed_1000_ms_"
            "incremental_endpoint_charge"
        ),
        "street_budget_ms": 15000.0,
        "frozen_conservative_base_ms": 13967.615699994712,
        "incremental_endpoint_oracle_ceiling_ms": 1000.0,
        "incremental_endpoint_oracle_conservative_charge_ms": 1000.0,
        "maximum_numerical_identity_error": 2e-11,
        "maximum_total_seconds": 30.0,
        "label_policy": (
            "sealed_artifact_join_only_zero_gpu_work_zero_new_optimizer_or_"
            "strategy_labels_post_fold_labels_zero"
        ),
        "decision_rule": (
            "authorize_post_fold_closure_and_value_preregistration_only_if_"
            "all_six_pair_identity_closure_incremental_ceiling_measured_and_"
            "conservative_ledgers_pass"
        ),
    }
    for field, expected_value in exact.items():
        if config[field] != expected_value:
            raise ValueError(f"combined-ledger field differs from ADR-0271: {field}")
    gates = {
        "expected_targets": 6,
        "expected_round_zero_targets": 4,
        "expected_round_one_targets": 2,
        "expected_existing_exact_oracles_round_zero": 2,
        "expected_combined_exact_oracles_round_one": 3,
        "minimum_conservative_headroom_ms": 0.0,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_exact_pairing": True,
        "require_all_globally_closed": True,
        "require_at_most_one_round": True,
        "require_numerical_identity": True,
        "require_incremental_work_exact": True,
        "require_incremental_oracle_ceiling": True,
        "require_safe_retreat_certificate": True,
        "require_measured_ledgers_fit": True,
        "require_conservative_ledgers_fit": True,
        "require_zero_new_labels": True,
        "require_post_fold_labels_zero": True,
        "require_blueprint_emission": True,
        "require_strategy_population_claim_null": True,
        "require_finite": True,
    }
    if config["gates"] != gates:
        raise ValueError("combined-ledger gates differ from ADR-0271")
    return {**config, "gates": gates}


def _finite_tree(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return True


def _cut_signature_rows(row: Mapping[str, Any]) -> list[tuple[int, str]]:
    return [
        (int(cut["target_player"]), str(cut["response_signature_sha256"]))
        for iteration in row["iterations"]
        for cut in iteration["cut_rows"]
    ]


def build_current_decision_combined_ledger_rows(
    closure: Mapping[str, Any],
    shadow: Mapping[str, Any],
    parsed: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, bool]]:
    """Join the six opened current-decision paths without opening a label."""

    closure_rows = [
        row for row in closure["target_rows"] if row["panel"] == "post_call"
    ]
    shadow_rows = list(shadow["target_rows"])
    closure_ids = [str(row["target_id"]) for row in closure_rows]
    shadow_ids = [str(row["target_id"]) for row in shadow_rows]
    pairing = {
        "closure_ids_unique": len(set(closure_ids)) == len(closure_ids),
        "shadow_ids_unique": len(set(shadow_ids)) == len(shadow_ids),
        "exact_target_set": set(closure_ids) == set(shadow_ids),
        "manifest_order": closure_ids == shadow_ids,
    }
    shadow_by_id = {str(row["target_id"]): row for row in shadow_rows}
    rows = []
    for closure_row in closure_rows:
        target_id = str(closure_row["target_id"])
        if target_id not in shadow_by_id:
            continue
        shadow_row = shadow_by_id[target_id]
        first_iteration = closure_row["iterations"][0]
        final_iteration = closure_row["iterations"][-1]
        cut_rounds = int(closure_row["cut_rounds"])
        incremental_ms = (
            0.0 if cut_rounds == 0 else float(final_iteration["oracle"]["wall_ms"])
        )
        conservative_incremental_ms = (
            0.0
            if cut_rounds == 0
            else float(parsed["incremental_endpoint_oracle_conservative_charge_ms"])
        )
        measured_combined_ms = (
            float(shadow_row["ledger"]["measured_live_ms"]) + incremental_ms
        )
        conservative_combined_ms = (
            float(parsed["frozen_conservative_base_ms"])
            + conservative_incremental_ms
        )
        source_error = abs(
            float(closure_row["source_nash_conv"])
            - float(shadow_row["source_nash_conv"])
        )
        first_master_error = abs(
            float(first_iteration["master"]["lower_bound"])
            - float(shadow_row["masters"][0]["lower_bound"])
        )
        final_master_error = abs(
            float(final_iteration["master"]["lower_bound"])
            - float(shadow_row["masters"][-1]["lower_bound"])
        )
        first_oracle_error = abs(
            float(first_iteration["oracle"]["objective"])
            - float(shadow_row["first_oracle"]["nash_conv"])
        )
        numerical_error = max(
            source_error,
            first_master_error,
            final_master_error,
            first_oracle_error,
        )
        closure_cut_rows = _cut_signature_rows(closure_row)
        shadow_cut_rows = [
            (int(cut["target_player"]), str(cut["response_signature_sha256"]))
            for cut in shadow_row["cut_rows"]
        ]
        identity = {
            "target_id": closure_row["target_id"] == shadow_row["target_id"],
            "source": closure_row["source"] == shadow_row["source"],
            "acting_player": closure_row["acting_player"]
            == shadow_row["acting_player"],
            "public_prefix": closure_row["public_prefix"]
            == shadow_row["public_prefix"],
            "round": closure_row["round"] == shadow_row["round"],
            "cut_rounds": cut_rounds == int(shadow_row["cut_rounds"]),
            "row_counts": closure_row["row_counts_by_player"]
            == shadow_row["row_counts_by_player"],
            "cut_rows": closure_cut_rows == shadow_cut_rows,
            "first_response_signatures": (
                first_iteration["oracle"]["response_signature_sha256"]
                == shadow_row["first_oracle"]["response_signature_sha256"]
            ),
            "numerical": numerical_error
            <= float(parsed["maximum_numerical_identity_error"]),
        }
        rows.append(
            {
                "target_id": target_id,
                "source": closure_row["source"],
                "acting_player": closure_row["acting_player"],
                "cut_rounds": cut_rounds,
                "globally_closed": closure_row["converged"],
                "optimality_gap": closure_row["optimality_gap"],
                "identity": identity,
                "maximum_numerical_identity_error": numerical_error,
                "incremental_endpoint_oracle_ms": incremental_ms,
                "incremental_endpoint_oracle_required": cut_rounds == 1,
                "incremental_endpoint_oracle_within_ceiling": incremental_ms
                <= float(parsed["incremental_endpoint_oracle_ceiling_ms"]),
                "sealed_first_endpoint_epigraph_closed": bool(
                    shadow_row["first_oracle"]["epigraph_closed"]
                ),
                "sealed_endpoint_independently_certified": bool(
                    shadow_row["endpoint_independently_certified"]
                ),
                "safe_retreat_certificate": {
                    "independently_certified": bool(
                        shadow_row["retreat"]["independently_certified"]
                    ),
                    "cap_feasible": bool(
                        shadow_row["retreat"]["exact_certificate"]["cap_feasible"]
                    ),
                    "interior_slack_passed": bool(
                        shadow_row["retreat"]["interior_slack_passed"]
                    ),
                    "acceptance_predicate_passed": bool(
                        shadow_row["retreat"]["acceptance_predicate_passed"]
                    ),
                    "shadow_accepted": bool(
                        shadow_row["retreat"]["shadow_accepted"]
                    ),
                    "exact_positive_value": float(
                        shadow_row["retreat"]["exact_positive_value"]
                    ),
                },
                "existing_safe_path_exact_oracles": int(
                    shadow_row["exact_oracles_executed"]
                ),
                "combined_exact_oracles": int(shadow_row["exact_oracles_executed"])
                + int(cut_rounds == 1),
                "measured_safe_retreat_ledger_ms": float(
                    shadow_row["ledger"]["measured_live_ms"]
                ),
                "measured_combined_ledger_ms": measured_combined_ms,
                "measured_combined_headroom_ms": float(parsed["street_budget_ms"])
                - measured_combined_ms,
                "conservative_base_ms": float(
                    parsed["frozen_conservative_base_ms"]
                ),
                "conservative_incremental_charge_ms": conservative_incremental_ms,
                "conservative_combined_ledger_ms": conservative_combined_ms,
                "conservative_combined_headroom_ms": float(
                    parsed["street_budget_ms"]
                )
                - conservative_combined_ms,
                "measured_fits": measured_combined_ms
                <= float(parsed["street_budget_ms"]),
                "conservative_fits": conservative_combined_ms
                <= float(parsed["street_budget_ms"]),
                "actual_emitted_policy_sha256": shadow_row[
                    "actual_emitted_policy_sha256"
                ],
                "restricted_blueprint_policy_sha256": shadow_row[
                    "restricted_blueprint_policy_sha256"
                ],
            }
        )
    return rows, pairing


def run_h32_current_decision_combined_ledger_replay(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = parse_h32_current_decision_combined_ledger_replay_config(
        json.loads(config_path.read_text(encoding="utf-8"))
    )
    git = _strict_git_metadata()
    if git["dirty"]:
        raise RuntimeError("combined-ledger replay requires a clean Git state")
    closure = load_artifact(
        _CLOSURE,
        expected_sha256=parsed["expected_closure_result_sha256"],
        require_passed=True,
    ).payload
    shadow = load_artifact(
        _SHADOW,
        expected_sha256=parsed["expected_shadow_result_sha256"],
        require_passed=True,
    ).payload
    rows, pairing = build_current_decision_combined_ledger_rows(
        closure,
        shadow,
        parsed,
    )
    closure_rows = [
        row for row in closure["target_rows"] if row["panel"] == "post_call"
    ]

    total_seconds = time.perf_counter() - started
    gate = parsed["gates"]
    round_zero = [row for row in rows if row["cut_rounds"] == 0]
    round_one = [row for row in rows if row["cut_rounds"] == 1]
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": bool(artifact_passed(closure) and artifact_passed(shadow))
        == gate["require_parents_passed"],
        "target_count": len(rows) == gate["expected_targets"],
        "round_counts": (
            len(round_zero) == gate["expected_round_zero_targets"]
            and len(round_one) == gate["expected_round_one_targets"]
        ),
        "exact_pairing": (
            all(pairing.values())
            and all(all(row["identity"].values()) for row in rows)
        )
        == gate["require_exact_pairing"],
        "all_globally_closed": all(row["globally_closed"] for row in rows)
        == gate["require_all_globally_closed"],
        "at_most_one_round": all(row["cut_rounds"] <= 1 for row in rows)
        == gate["require_at_most_one_round"],
        "numerical_identity": (
            max(row["maximum_numerical_identity_error"] for row in rows)
            <= float(parsed["maximum_numerical_identity_error"])
        )
        == gate["require_numerical_identity"],
        "incremental_work_exact": (
            all(
                row["incremental_endpoint_oracle_ms"] == 0.0
                and row["sealed_first_endpoint_epigraph_closed"]
                and row["sealed_endpoint_independently_certified"]
                and row["combined_exact_oracles"]
                == gate["expected_existing_exact_oracles_round_zero"]
                for row in round_zero
            )
            and all(
                row["incremental_endpoint_oracle_ms"]
                == closure_row["iterations"][-1]["oracle"]["wall_ms"]
                and not row["sealed_first_endpoint_epigraph_closed"]
                and not row["sealed_endpoint_independently_certified"]
                and row["combined_exact_oracles"]
                == gate["expected_combined_exact_oracles_round_one"]
                for row, closure_row in (
                    (
                        row,
                        next(
                            item
                            for item in closure_rows
                            if item["target_id"] == row["target_id"]
                        ),
                    )
                    for row in round_one
                )
            )
        )
        == gate["require_incremental_work_exact"],
        "incremental_oracle_ceiling": all(
            row["incremental_endpoint_oracle_within_ceiling"] for row in rows
        )
        == gate["require_incremental_oracle_ceiling"],
        "safe_retreat_certificate": all(
            all(
                value
                for field, value in row["safe_retreat_certificate"].items()
                if field != "exact_positive_value"
            )
            and row["safe_retreat_certificate"]["exact_positive_value"] > 0.0
            for row in rows
        )
        == gate["require_safe_retreat_certificate"],
        "measured_ledgers_fit": all(row["measured_fits"] for row in rows)
        == gate["require_measured_ledgers_fit"],
        "conservative_ledgers_fit": all(
            row["conservative_fits"]
            and row["conservative_combined_headroom_ms"]
            >= gate["minimum_conservative_headroom_ms"]
            for row in rows
        )
        == gate["require_conservative_ledgers_fit"],
        "zero_new_labels": True == gate["require_zero_new_labels"],
        "post_fold_labels_zero": True == gate["require_post_fold_labels_zero"],
        "blueprint_emission": all(
            row["actual_emitted_policy_sha256"]
            == row["restricted_blueprint_policy_sha256"]
            for row in rows
        )
        == gate["require_blueprint_emission"],
        "strategy_population_claim_null": True
        == gate["require_strategy_population_claim_null"],
        "total_time": total_seconds <= float(parsed["maximum_total_seconds"]),
        "finite": _finite_tree(rows) == gate["require_finite"],
    }
    gate_result = finalize_gates(checks)
    result = {
        "schema_version": 1,
        "status": "h32_current_decision_combined_ledger_replay_executed",
        "environment": assemble_environment(runtime={"kind": "cpu_only"}, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "methodology": {
            "targets": len(rows),
            "sealed_artifacts_joined": 2,
            "gpu_work": 0,
            "new_optimizer_labels": 0,
            "new_strategy_labels": 0,
            "post_fold_strategy_labels": 0,
            "candidate_policies_emitted": 0,
        },
        "pairing": pairing,
        "target_rows": rows,
        "aggregate": {
            "round_zero_targets": len(round_zero),
            "round_one_targets": len(round_one),
            "maximum_numerical_identity_error": max(
                row["maximum_numerical_identity_error"] for row in rows
            ),
            "maximum_incremental_endpoint_oracle_ms": max(
                row["incremental_endpoint_oracle_ms"] for row in rows
            ),
            "maximum_measured_combined_ledger_ms": max(
                row["measured_combined_ledger_ms"] for row in rows
            ),
            "minimum_measured_combined_headroom_ms": min(
                row["measured_combined_headroom_ms"] for row in rows
            ),
            "maximum_conservative_combined_ledger_ms": max(
                row["conservative_combined_ledger_ms"] for row in rows
            ),
            "minimum_conservative_combined_headroom_ms": min(
                row["conservative_combined_headroom_ms"] for row in rows
            ),
        },
        **gate_result,
        "decision": (
            "authorize_preregistered_post_fold_current_decision_closure_and_"
            "value_confirmation"
            if gate_result["passed"]
            else "reject_post_fold_combined_closure_and_value_trial_at_current_"
            "ledger"
        ),
        "actual_emitted_policy": "immutable_restricted_blueprint_only",
        "strategy_population_claim": None,
        "total_seconds": total_seconds,
        "limitations": [
            (
                "This is a deterministic join of opened artifacts, not a measured "
                "same-invocation combined path."
            ),
            (
                "The fixed 1000 ms incremental charge leaves only 32.384 ms under "
                "the inherited conservative floor."
            ),
            (
                "Fresh post-fold execution must fail closed if its incremental "
                "endpoint oracle exceeds the frozen ceiling."
            ),
            (
                "No post-fold strategy label is opened and no deployment or "
                "poker-strength claim is made."
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
    result = run_h32_current_decision_combined_ledger_replay(
        args.config,
        args.output,
    )
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
