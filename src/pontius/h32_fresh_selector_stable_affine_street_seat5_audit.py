"""Fresh acting-seat-5 replication of the affine street trial."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Mapping

from . import h32_fresh_selector_stable_affine_street_audit as seat0
from .h32_atomic_response_preflight import select_one_atom_per_acting_seat
from .h32_fresh_public_block_value_audit import build_public_node_blocks
from .h32_fresh_regret_vertex_opportunity_audit import (
    build_regret_vertex_candidate,
    recover_iteration_one_dcfr_regret_deltas,
)
from .h32_fresh_union_value_audit import build_fresh_seat4_target
from .incremental_policy_tt import compile_policy_probability_tape
from .real_policy import policy_digest


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments/configs/h32-fresh-selector-stable-affine-street-seat5-v1.json"
)
_OUTPUT = (
    _ROOT
    / "experiments/results/h32-fresh-selector-stable-affine-street-seat5-v1.json"
)
_SEAT0_RESULT = (
    _ROOT / "experiments/results/h32-fresh-selector-stable-affine-street-v1.json"
)
_SEAT0_ADR = (
    _ROOT
    / "docs/decisions"
    / "ADR-0192-fixed-seat0-affine-rule-emits-four-fresh-certified-candidates-before-deadline.md"
)
_TARGET_BUILDER = _ROOT / "src/pontius/h32_fresh_union_value_audit.py"
_IMPLEMENTATION = Path(__file__)
_TEST = (
    _ROOT / "tests/test_h32_fresh_selector_stable_affine_street_seat5_audit.py"
)

_PATHS = {
    "expected_seat0_config_sha256": seat0._CONFIG,
    "expected_seat0_implementation_sha256": seat0._IMPLEMENTATION,
    "expected_seat0_control_test_sha256": seat0._TEST,
    "expected_seat0_result_sha256": _SEAT0_RESULT,
    "expected_seat0_decision_sha256": _SEAT0_ADR,
    "expected_target_builder_sha256": _TARGET_BUILDER,
    "expected_audit_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_FRESH_TARGETS = [
    {
        "target": "panel_1/blocker_heavy/local_blocker_seat4_x2",
        "board_id": "panel_1",
        "board": ["5c", "8c", "8d", "Jc", "As"],
        "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat4_x2",
        "source_belief_sha256": (
            "aa3a5a8abe8dc72fe436134d4b619239a87b002134cdad88a908d833318b5067"
        ),
        "target_belief_sha256": (
            "9cb9f6c30990baab33c710ce5bbef634cd903d5dd11346b26b7037b03d1d5953"
        ),
        "target_descriptor_sha256": (
            "a8dbff19eb77c5e109d31bfb72954ca1fb2dfe28f884e1628e1f9f0c5a51e3a9"
        ),
    },
    {
        "target": "panel_2/balanced/local_blocker_seat4_x2",
        "board_id": "panel_2",
        "board": ["2c", "3s", "5d", "Js", "Qc"],
        "range_family": "balanced",
        "target_shift": "local_blocker_seat4_x2",
        "source_belief_sha256": (
            "0662b2cf2436cbc6dcc5669fe75a2c15f03e652fb40a6903703a10dd14cfa289"
        ),
        "target_belief_sha256": (
            "4bf33595af8b344e01b534ea12ad5619fac2e307f06d4e1e1be55ca6d7f4c0de"
        ),
        "target_descriptor_sha256": (
            "41675715d6df5e230d77688dedc7c18c404ab0807ab604f660fd767612068748"
        ),
    },
    {
        "target": "panel_3/balanced/local_blocker_seat4_x2",
        "board_id": "panel_3",
        "board": ["4h", "7h", "9s", "Jd", "Kc"],
        "range_family": "balanced",
        "target_shift": "local_blocker_seat4_x2",
        "source_belief_sha256": (
            "cadd9449259f56de43ae4d710c2e3fd6ae4733e7b7c8323836b87578a3cc9a71"
        ),
        "target_belief_sha256": (
            "add4941c6ee083319afcbfbe8df2a02afb672c652b46236f0e265cbc4fcf7cac"
        ),
        "target_descriptor_sha256": (
            "99ea66ac4cfc59f083b696b1ddd7ccb22f9c52a8cf2dfea58c8fdf61edf4ef6e"
        ),
    },
    {
        "target": "panel_3/blocker_heavy/local_blocker_seat4_x2",
        "board_id": "panel_3",
        "board": ["4h", "7h", "9s", "Jd", "Kc"],
        "range_family": "blocker_heavy",
        "target_shift": "local_blocker_seat4_x2",
        "source_belief_sha256": (
            "74ce0c18ac82e9ebb799be851f140c7011ad75671a3409f94c7db1db3187278e"
        ),
        "target_belief_sha256": (
            "2df7b14b451769607ed037c0a7cd5ed77f7253c1382d40ac798078690ab4a2db"
        ),
        "target_descriptor_sha256": (
            "64a032424e7a14f47513615395e7586c29fdce6e8bd7e7bfd0f39998721594e7"
        ),
    },
]


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required seat-5 affine replication input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_fresh_selector_stable_affine_street_seat5_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate ADR-0193's seat/target-only replication."""

    fields = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "freshness_base_commit",
        "targets",
        "target_construction",
        "target_seat",
        "acting_seat",
        "replication_scope",
        "outcome_policy",
    }
    if set(config) != fields:
        raise ValueError("seat-5 affine replication fields differ from ADR-0193")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0192_before_any_fresh_seat4_policy_step_or_quality_label"
        ),
        "seed": 20260821,
        "freshness_base_commit": "d59b8577220229e6b49c9b904a57a8c1787b2cb5",
        "targets": _FRESH_TARGETS,
        "target_construction": (
            "double_label_free_maximum_overlap_then_strength_then_smallest_canonical_hand_at_seat4"
        ),
        "target_seat": 4,
        "acting_seat": 5,
        "replication_scope": (
            "reuse_complete_adr0191_live_core_change_only_target_seat4_and_acting_seat5"
        ),
        "outcome_policy": (
            "retain_every_adr0191_outcome_neutral_gate_and_add_no_seat0_outcome_gate"
        ),
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("seat-5 affine replication workload differs from ADR-0193")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"seat-5 affine replication source mismatch: {field}")

    base_config = json.loads(seat0._CONFIG.read_text(encoding="utf-8"))
    base = seat0.parse_h32_fresh_selector_stable_affine_street_config(base_config)
    return {
        **base,
        "evidence_stage": config["evidence_stage"],
        "seed": config["seed"],
        "freshness_base_commit": config["freshness_base_commit"],
        "targets": tuple(dict(row) for row in config["targets"]),
        "target_construction": config["target_construction"],
        "target_seat": config["target_seat"],
        "acting_seat": config["acting_seat"],
        "replication_scope": config["replication_scope"],
        "outcome_policy": config["outcome_policy"],
        "seat0_base": base,
    }


def _construct_seat5_payload(
    *,
    layout: Any,
    hands_by_player: tuple[tuple[Any, ...], ...],
    blueprint: Mapping[str, Mapping[Any, float]],
    solver: Any,
    warm_regret_mass: float,
) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    soft_candidate = solver.current_strategy()
    regret_deltas = recover_iteration_one_dcfr_regret_deltas(
        blueprint,
        solver.regret_table(),
        warm_regret_mass=warm_regret_mass,
    )
    anchors = select_one_atom_per_acting_seat(
        layout,
        hands_by_player,
        blueprint,
        soft_candidate,
    )
    blocks = build_public_node_blocks(blueprint, soft_candidate, anchors)
    seat5 = next(block for block in blocks if int(block["acting_seat"]) == 5)
    keys = tuple(seat5["information_keys"])
    endpoint = build_regret_vertex_candidate(blueprint, regret_deltas, keys)
    endpoint_probabilities = compile_policy_probability_tape(
        layout,
        hands_by_player,
        endpoint,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return {
        "block": seat5,
        "all_block_count": len(blocks),
        "information_keys": keys,
        "endpoint": endpoint,
        "endpoint_probabilities": endpoint_probabilities,
        "soft_candidate_policy_sha256": policy_digest(soft_candidate),
        "direction_policy_sha256": policy_digest(endpoint),
    }, elapsed_ms


def _rename_seat5_candidate_ids(result: dict[str, Any]) -> None:
    """Replace inherited descriptive IDs after all causal choices are closed."""

    for target in result["target_rows"]:
        if target["live"]["emitted_candidate_id"] == "seat0_regret_vertex_affine":
            target["live"]["emitted_candidate_id"] = "seat5_regret_vertex_affine"
        selected = target["block"]["selected_validation"]
        if selected is not None and "candidate_id" in selected["direct"]:
            selected["direct"]["candidate_id"] = "seat5_regret_vertex_affine_teacher"


def run_h32_fresh_selector_stable_affine_street_seat5_audit(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Run the unchanged live core with the frozen seat-5 substitution."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_fresh_selector_stable_affine_street_seat5_config(config)
    original_parser = seat0.parse_h32_fresh_selector_stable_affine_street_config
    original_target_builder = seat0.build_fresh_seat0_target
    original_payload_builder = seat0._construct_seat0_payload
    seat0.parse_h32_fresh_selector_stable_affine_street_config = lambda _: parsed
    seat0.build_fresh_seat0_target = build_fresh_seat4_target
    seat0._construct_seat0_payload = _construct_seat5_payload
    try:
        result = seat0.run_h32_fresh_selector_stable_affine_street_audit(
            config_path,
            output_path,
        )
    finally:
        seat0.parse_h32_fresh_selector_stable_affine_street_config = original_parser
        seat0.build_fresh_seat0_target = original_target_builder
        seat0._construct_seat0_payload = original_payload_builder

    _rename_seat5_candidate_ids(result)
    result["schema_version"] = 2
    result["status"] = "fresh_h32_seat5_affine_street_replication_executed"
    result["config_sha256"] = _sha256(config_path)
    result["implementation_sha256"] = _sha256(_IMPLEMENTATION)
    result["methodology"]["fixed_acting_seat"] = 5
    result["methodology"]["seat0_live_core_reused_unchanged"] = True
    result["replication"] = {
        "seat0_config_sha256": _sha256(seat0._CONFIG),
        "seat0_implementation_sha256": _sha256(seat0._IMPLEMENTATION),
        "seat0_result_sha256": _sha256(_SEAT0_RESULT),
        "target_seat": 4,
        "acting_seat": 5,
        "deadline_guards_changed": False,
        "affine_rule_changed": False,
        "seat0_outcome_gates_added": False,
    }
    result["decision"] = (
        "accept_four_context_fresh_seat5_affine_street_trial"
        if result["passed"]
        else "reject_fresh_seat5_affine_street_trial"
    )
    result["limitations"] = [
        "Only four fresh seat-4 blocker shifts are measured.",
        "Emission is simulated and no external poker action is taken.",
        "The rule always chooses acting seat 5 and does not test a learned selector.",
        "Post-ledger exact teachers cannot influence live selection or emission.",
        "No latency distribution, deployment, composition, or population claim follows.",
    ]
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
    result = run_h32_fresh_selector_stable_affine_street_seat5_audit(
        args.config,
        args.output,
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "passed": result["passed"],
                "aggregate": result["aggregate"],
                "replication": result["replication"],
            },
            indent=2,
        )
    )
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
