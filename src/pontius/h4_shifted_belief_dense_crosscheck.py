"""Cross-check the ADR-0099 shifted-belief path against a literal h4 oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .factor_tt_contraction import FactorTTBeliefWorkspace
from .h32_warm_search_acceptance_audit import (
    build_target_belief,
    parse_h32_warm_search_config,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case, _solver
from .leaf_adjoint_evaluation import evaluate_leaf_adjoint_profile
from .open_mode_audit import _policy_from_json
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .public_tree_tensor import PublicTreeTensorEvaluator
from .public_tree_tensor_cfr import PublicTreeTensorCFR
from .real_policy import policy_digest
from .river import parse_cards
from .showdown_value_rank_screen import _game_from_belief


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-warm-search-acceptance-v1.json"
_POLICY_SOURCE = _ROOT / "experiments" / "results" / "real-policy-source-v1.json"
_H32_RESULT = _ROOT / "experiments" / "results" / "h32-warm-search-acceptance-v1.json"
_IMPLEMENTATION = Path(__file__)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _table_error(
    first: dict[str, dict[str, float]],
    second: dict[str, dict[str, float]],
) -> float:
    if first.keys() != second.keys():
        raise AssertionError("shifted h4 table schemas differ")
    return max(
        abs(first[key][action] - second[key][action])
        for key in first
        for action in first[key]
    )


def _source_policy(
    source: dict[str, Any],
    *,
    family: str,
) -> dict[str, dict[str, float]]:
    geometry = next(
        row
        for row in source["geometries"]
        if int(row["hands_per_player"]) == 4 and row["range_family"] == family
    )
    profile = next(
        row
        for row in geometry["profiles"]
        if row["provenance"]["kind"] == "dcfr_average"
        and int(row["provenance"]["checkpoint"]) == 64
    )
    return _policy_from_json(profile["policy"])


def _evaluation_errors(actual: Any, expected: Any) -> dict[str, float]:
    leaf = actual.evaluation
    dense = expected.evaluation
    return {
        "maximum_utility_error": max(
            abs(first - second)
            for first, second in zip(leaf.utilities, dense.utilities, strict=True)
        ),
        "maximum_best_response_error": max(
            abs(first - second)
            for first, second in zip(
                leaf.best_response_values,
                dense.best_response_values,
                strict=True,
            )
        ),
        "maximum_deviation_gain_error": max(
            abs(first - second)
            for first, second in zip(
                leaf.deviation_gains,
                dense.deviation_gains,
                strict=True,
            )
        ),
        "nash_conv_error": abs(leaf.nash_conv - dense.nash_conv),
        "leaf_nash_conv": float(leaf.nash_conv),
        "dense_nash_conv": float(dense.nash_conv),
        "leaf_zero_sum_residual": float(actual.zero_sum_residual),
    }


def run_h4_shifted_belief_dense_crosscheck() -> dict[str, Any]:
    """Exercise both shifted beliefs through dense and leaf-adjoint paths."""

    parsed = parse_h32_warm_search_config(
        json.loads(_CONFIG.read_text(encoding="utf-8"))
    )
    source = json.loads(_POLICY_SOURCE.read_text(encoding="utf-8"))
    board = parse_cards(*parsed["board"])
    rows = []
    for family in parsed["range_families"]:
        source_belief, topology, sparse, retained = _build_case(
            parsed=parsed,
            board=board,
            hand_count=4,
            family=family,
        )
        source_workspace, _, automata = retained
        blueprint = _source_policy(source, family=family)
        for shift in parsed["target_shifts"]:
            target_belief, descriptor = build_target_belief(
                source_belief,
                board=board,
                shift=shift,
                local_blocker_target_seat=parsed["local_blocker_target_seat"],
            )
            target_base = FactorTTBeliefWorkspace.compile(
                source_workspace.topology.base,
                target_belief,
                query_chunk_records=parsed["query_chunk_records"],
            )
            target_workspace = OpenModeFactorTTWorkspace.compile(
                source_workspace.topology,
                target_base,
            )
            dense_layout = PublicTreeTensorEvaluator(
                _game_from_belief(
                    belief=target_belief,
                    pot=parsed["pot"],
                    stack=parsed["stack"],
                    bet_size=parsed["bet_size"],
                )
            )
            dense_baseline = dense_layout.evaluate(blueprint)
            leaf_baseline = evaluate_leaf_adjoint_profile(
                topology,
                target_workspace,
                sparse,
                blueprint,
                automata,
                hands_by_player=target_belief.hands_by_player,
                maximum_feature_width_per_batch=parsed[
                    "maximum_feature_width_per_batch"
                ],
            )

            dense_solver = PublicTreeTensorCFR(
                dense_layout,
                parsed["solver_variant"],
            )
            leaf_solver = _solver(
                parsed=parsed,
                belief=target_belief,
                topology=topology,
                workspace=target_workspace,
                sparse=sparse,
                automata=automata,
            )
            if set(dense_layout.information_schema()) != set(
                leaf_solver.information_schema()
            ):
                raise AssertionError("shifted h4 external-axis schemas differ")
            warm_mass = (
                parsed["warm_regret_mass_payoff_fraction"]
                * float(topology.game.payoff_span)
            )
            dense_solver.warm_start(blueprint, warm_mass)
            leaf_solver.warm_start(blueprint, warm_mass)
            dense_solver.step()
            leaf_solver.step()
            trajectory_errors = {
                "maximum_regret_error": _table_error(
                    leaf_solver.regret_table(), dense_solver.regret_table()
                ),
                "maximum_strategy_sum_error": _table_error(
                    leaf_solver.strategy_sum_table(),
                    dense_solver.strategy_sum_table(),
                ),
                "maximum_current_policy_error": _table_error(
                    leaf_solver.current_strategy(),
                    dense_solver.current_strategy(),
                ),
                "maximum_average_policy_error": _table_error(
                    leaf_solver.average_strategy(),
                    dense_solver.average_strategy(),
                ),
            }
            leaf_average = leaf_solver.average_strategy()
            dense_post = dense_layout.evaluate(dense_solver.average_strategy())
            leaf_post = evaluate_leaf_adjoint_profile(
                topology,
                target_workspace,
                sparse,
                leaf_average,
                automata,
                hands_by_player=target_belief.hands_by_player,
                maximum_feature_width_per_batch=parsed[
                    "maximum_feature_width_per_batch"
                ],
            )
            rows.append(
                {
                    "range_family": family,
                    "target_shift": shift,
                    "deals": dense_layout.deal_count,
                    "blueprint_policy_sha256": policy_digest(blueprint),
                    "positive_likelihoods": descriptor["positive_likelihoods"],
                    "likelihood_minimum": descriptor["likelihood_minimum"],
                    "likelihood_maximum": descriptor["likelihood_maximum"],
                    "baseline_evaluation": _evaluation_errors(
                        leaf_baseline,
                        dense_baseline,
                    ),
                    "first_warm_step_trajectory": trajectory_errors,
                    "first_warm_average_evaluation": _evaluation_errors(
                        leaf_post,
                        dense_post,
                    ),
                }
            )

    evaluation_rows = [
        evaluation
        for row in rows
        for evaluation in (
            row["baseline_evaluation"],
            row["first_warm_average_evaluation"],
        )
    ]
    trajectory_rows = [row["first_warm_step_trajectory"] for row in rows]
    aggregate = {
        "maximum_utility_error": max(
            row["maximum_utility_error"] for row in evaluation_rows
        ),
        "maximum_best_response_error": max(
            row["maximum_best_response_error"] for row in evaluation_rows
        ),
        "maximum_deviation_gain_error": max(
            row["maximum_deviation_gain_error"] for row in evaluation_rows
        ),
        "maximum_nash_conv_error": max(
            row["nash_conv_error"] for row in evaluation_rows
        ),
        "maximum_regret_error": max(
            row["maximum_regret_error"] for row in trajectory_rows
        ),
        "maximum_strategy_sum_error": max(
            row["maximum_strategy_sum_error"] for row in trajectory_rows
        ),
        "maximum_current_policy_error": max(
            row["maximum_current_policy_error"] for row in trajectory_rows
        ),
        "maximum_average_policy_error": max(
            row["maximum_average_policy_error"] for row in trajectory_rows
        ),
        "maximum_zero_sum_residual": max(
            row["leaf_zero_sum_residual"] for row in evaluation_rows
        ),
    }
    return {
        "schema_version": 1,
        "diagnostic_type": "post_freeze_h4_shifted_belief_dense_crosscheck",
        "status": "executed_after_adr0099_labels_without_changing_adr0099_gates",
        "config_sha256": _sha256(_CONFIG),
        "policy_source_sha256": _sha256(_POLICY_SOURCE),
        "h32_result_sha256": _sha256(_H32_RESULT),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "rows": rows,
        "aggregate": aggregate,
        "passed_existing_1e_10_identity_standard": max(aggregate.values()) <= 1e-10,
        "scope": (
            "External h4 identity under the two ADR-0099 shifted beliefs; "
            "this is not an added ADR-0099 gate or an h32 dense oracle."
        ),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    result = run_h4_shifted_belief_dense_crosscheck()
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
