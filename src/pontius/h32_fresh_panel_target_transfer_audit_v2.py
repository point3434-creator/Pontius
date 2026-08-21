"""Numerically corrected warm-start gate for ADR-0146 target transfer."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from . import h32_fresh_panel_target_transfer_audit as v1
from .h32_warm_search_acceptance_audit import _policy_distance
from .resident_leaf_adjoint_cfr import ResidentLeafAdjointPublicTreeCFR

_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-fresh-panel-target-transfer-v2.json"
_OUTPUT = _ROOT / "experiments/results/h32-fresh-panel-target-transfer-v2.json"
_V1_CONFIG = _ROOT / "experiments/configs/h32-fresh-panel-target-transfer-v1.json"
_FAILED = _ROOT / "experiments/results/h32-fresh-panel-target-transfer-v1.json"
_FAILED_ADR = _ROOT / "docs/decisions/ADR-0147-target-transfer-run-rejected-by-overstrict-warm-digest-gate.md"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_fresh_panel_target_transfer_audit_v2.py"

_PATHS = {
    "expected_v1_config_sha256": _V1_CONFIG,
    "expected_v1_implementation_sha256": v1._IMPLEMENTATION,
    "expected_failed_result_sha256": _FAILED,
    "expected_failed_decision_sha256": _FAILED_ADR,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required corrected-transfer input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_fresh_panel_target_transfer_v2_config(config: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "evidence_stage", *_PATHS, "correction_scope",
        "maximum_warm_start_probability_error", "maximum_warm_start_mean_total_variation",
        "require_warm_start_digest_identity", "outcome_policy",
    }
    if set(config) != fields:
        raise ValueError("corrected target-transfer fields differ from ADR-0148")
    frozen = {
        "evidence_stage": "preregistered_after_adr0147_before_corrected_target_rerun",
        "correction_scope": "replace_only_exact_warm_policy_digest_gate_with_established_numerical_probability_and_mean_tv_gates",
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "require_warm_start_digest_identity": False,
        "outcome_policy": "retain_v1_target_candidate_order_acceptance_and_all_outcome_neutral_gates",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("corrected target-transfer workload differs from ADR-0148")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"corrected target-transfer source mismatch: {field}")
    base = json.loads(_V1_CONFIG.read_text(encoding="utf-8"))
    parsed = v1.parse_h32_fresh_panel_target_transfer_config(base)
    return {**config, "base": parsed}


_WARM_DISTANCES: list[dict[str, float]] = []


class _TrackedResidentSolver(ResidentLeafAdjointPublicTreeCFR):
    def warm_start(self, blueprint: dict[str, dict[str, float]], regret_mass: float) -> None:
        super().warm_start(blueprint, regret_mass)
        _WARM_DISTANCES.append(_policy_distance(blueprint, self.current_strategy()))


def _tracked_solver(parsed: dict[str, Any], belief: Any, layout: Any, workspace: Any,
                    sparse: Any, automata: Any, gpu: Any, belief_cache: Any,
                    automaton_caches: Any) -> ResidentLeafAdjointPublicTreeCFR:
    return _TrackedResidentSolver(
        layout, workspace, sparse, automata, parsed["solver_variant"],
        belief_cache=belief_cache, automaton_caches=automaton_caches, cupy_sparse=gpu,
        maximum_feature_width_per_batch=parsed["maximum_feature_width_per_batch"],
        hands_by_player=belief.hands_by_player,
    )


def run_h32_fresh_panel_target_transfer_v2_audit(
    config_path: Path = _CONFIG, output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_fresh_panel_target_transfer_v2_config(config)
    _WARM_DISTANCES.clear()
    original_solver = v1._solver
    v1._solver = _tracked_solver
    try:
        result = v1.run_h32_fresh_panel_target_transfer_audit(_V1_CONFIG, output_path)
    finally:
        v1._solver = original_solver
    if len(_WARM_DISTANCES) != len(result["targets"]):
        raise AssertionError("corrected warm-start instrumentation count differs")
    for target, distance in zip(result["targets"], _WARM_DISTANCES, strict=True):
        target["warm_start_digest_identity"] = target.pop("warm_start_identity")
        target["warm_start_distance"] = distance
    maximum_probability = max(row["maximum_probability_error"] for row in _WARM_DISTANCES)
    maximum_mean_tv = max(row["mean_total_variation"] for row in _WARM_DISTANCES)
    result["gate_results"].pop("warm_identity")
    result["gate_results"]["warm_start_probability_error"] = (
        maximum_probability <= parsed["maximum_warm_start_probability_error"]
    )
    result["gate_results"]["warm_start_mean_total_variation"] = (
        maximum_mean_tv <= parsed["maximum_warm_start_mean_total_variation"]
    )
    result["schema_version"] = 2
    result["status"] = "corrected_h32_fresh_panel_target_transfer_executed"
    result["config"] = config
    result["config_sha256"] = _sha256(config_path)
    result["implementation_sha256"] = _sha256(_IMPLEMENTATION)
    result["correction"] = {
        "failed_v1_result_sha256": _sha256(_FAILED),
        "reused_v1_config_sha256": _sha256(_V1_CONFIG),
        "reused_v1_implementation_sha256": _sha256(v1._IMPLEMENTATION),
        "maximum_warm_start_probability_error": maximum_probability,
        "maximum_warm_start_mean_total_variation": maximum_mean_tv,
        "warm_start_digest_identities": [
            target["warm_start_digest_identity"] for target in result["targets"]
        ],
        "scientific_matrix_changed": False,
        "outcome_gates_changed": False,
    }
    result["passed"] = all(result["gate_results"].values())
    result["decision"] = (
        "accept_fresh_panel_two_step_transfer_measurement"
        if result["passed"] else "reject_corrected_target_transfer_mechanism"
    )
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args()
    result = run_h32_fresh_panel_target_transfer_v2_audit(args.config, args.output)
    print(
        "corrected fresh-panel target transfer: "
        f"passed={result['passed']}, "
        f"selections={result['strategy_transfer']['non_blueprint_selections']}, "
        f"wall={result['timing']['total_seconds']:.3f}s"
    )


if __name__ == "__main__":
    main()
