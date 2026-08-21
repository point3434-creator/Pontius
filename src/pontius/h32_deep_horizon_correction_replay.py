"""Read-only correction replay for the rejected deep-horizon v1 artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .h32_fresh_board_panel_cache_preflight import _json_digest
from .reporting import environment_metadata


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-deep-horizon-correction-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-deep-horizon-correction-v1.json"
_SOURCE_RESULT = _ROOT / "experiments/results/h32-deep-horizon-opportunity-v1.json"
_SOURCE_CONFIG = _ROOT / "experiments/configs/h32-deep-horizon-opportunity-v1.json"
_SOURCE_IMPLEMENTATION = _ROOT / "src/pontius/h32_deep_horizon_opportunity_audit.py"
_PARENT_RESULT = _ROOT / "experiments/results/h32-fresh-regret-vertex-opportunity-v1.json"
_FAILURE_ADR = _ROOT / "docs/decisions/ADR-0182-deep-horizon-v1-is-rejected-by-two-miscopied-descriptor-hashes.md"
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_deep_horizon_correction_replay.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE_RESULT,
    "expected_source_config_sha256": _SOURCE_CONFIG,
    "expected_source_implementation_sha256": _SOURCE_IMPLEMENTATION,
    "expected_parent_result_sha256": _PARENT_RESULT,
    "expected_failure_decision_sha256": _FAILURE_ADR,
    "expected_correction_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
}

_CORRECTIONS = [
    {
        "target": "panel_1/balanced/local_blocker_seat1_x2",
        "incorrect_descriptor_sha256": "6109b0afb8548629870f64853a960118a842b062b97809e908efbf3ca5f7d9d0d",
        "correct_descriptor_sha256": "6109b0afb8548629870f6484d5f1050468aad320c0e1c92e8506d841c9dc7f7b",
    },
    {
        "target": "panel_3/blocker_heavy/local_blocker_seat1_x2",
        "incorrect_descriptor_sha256": "de67f2fbba92ea16ad5ede876b9c6451affb06f0b30c4f6baa7def53950f981c26",
        "correct_descriptor_sha256": "de67f2fbba92ea16ad5ede876b9c6451affb06d103e5f1f6e0b30c4df8b56eeb",
    },
]


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required correction input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_deep_horizon_correction_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate ADR-0183's closed read-only repair contract."""

    fields = {
        "evidence_stage", *_PATHS, "source_status", "corrections",
        "expected_substantive_false_gates", "correction_scope", "aggregate_rule",
        "strategy_recomputation", "gates",
    }
    if set(config) != fields:
        raise ValueError("deep-horizon correction fields differ from ADR-0183")
    frozen = {
        "evidence_stage": "post_failure_read_only_metadata_correction_after_adr0182",
        "source_status": "rejected_result_only_target_identity_substantively_false",
        "corrections": _CORRECTIONS,
        "expected_substantive_false_gates": ["target_identity"],
        "correction_scope": "replace_only_the_two_expected_descriptor_hashes_for_gate_replay_from_authoritative_adr0178_parent",
        "aggregate_rule": "copy_source_aggregate_byte_for_byte_after_canonical_json_round_trip",
        "strategy_recomputation": "forbidden",
    }
    if any(config[key] != value for key, value in frozen.items()):
        raise ValueError("deep-horizon correction workload differs from ADR-0183")
    for field, path in _PATHS.items():
        if config[field] != _sha256(path):
            raise ValueError(f"deep-horizon correction source mismatch: {field}")
    gates = {
        "expected_target_rows": 2,
        "require_source_rejected": True,
        "require_only_target_identity_failed": True,
        "require_source_provenance": True,
        "require_belief_identity": True,
        "require_descriptor_rehash_identity": True,
        "require_parent_descriptor_identity": True,
        "require_exact_two_corrections": True,
        "require_all_other_source_gates_true": True,
        "require_aggregate_identity": True,
        "require_no_strategy_recomputation": True,
        "require_strategy_population_claim_null": True,
    }
    if config["gates"] != gates:
        raise ValueError("deep-horizon correction gates differ from ADR-0183")
    return {
        **config,
        "corrections": tuple(dict(row) for row in config["corrections"]),
        "expected_substantive_false_gates": tuple(config["expected_substantive_false_gates"]),
        "gates": dict(gates),
    }


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def validate_correction_payload(
    *, parsed: Mapping[str, Any], source: Mapping[str, Any],
    source_config: Mapping[str, Any], parent: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate that the failed artifact differs only in frozen descriptor metadata."""

    source_gates = dict(source["gates"])
    substantive_false = sorted(
        key for key, value in source_gates.items() if not value and key != "passed"
    )
    corrections = {row["target"]: row for row in parsed["corrections"]}
    source_specs = {row["target"]: row for row in source_config["targets"]}
    parent_rows = {row["target"]: row for row in parent["target_rows"]}
    target_checks = []
    for target in source["target_rows"]:
        name = target["target"]
        if name not in corrections or name not in source_specs or name not in parent_rows:
            raise ValueError("correction target cannot be resolved uniquely")
        correction, spec, parent_row = corrections[name], source_specs[name], parent_rows[name]
        target_checks.append({
            "target": name,
            "belief_identity": (
                target["target_belief_sha256"] == spec["target_belief_sha256"]
                and target["target_belief_sha256"] == parent_row["target_belief_sha256"]
            ),
            "incorrect_descriptor_identity": (
                spec["target_descriptor_sha256"] == correction["incorrect_descriptor_sha256"]
            ),
            "descriptor_rehash_identity": (
                _json_digest(target["target_descriptor"])
                == target["target_descriptor_sha256"]
                == correction["correct_descriptor_sha256"]
            ),
            "parent_descriptor_identity": (
                target["target_descriptor_sha256"] == parent_row["target_descriptor_sha256"]
            ),
            "block_replay": bool(target["parent_block_replay"]),
        })
    all_other_true = all(
        bool(value) for key, value in source_gates.items()
        if key not in {"target_identity", "passed"}
    )
    aggregate_round_trip = json.loads(_canonical(source["aggregate"]))
    gates_config = parsed["gates"]
    gates = {
        "source_rejected": (
            source["gates"]["passed"] is False
            and source["decision"] == "reject_deep_horizon_audit"
        ) == gates_config["require_source_rejected"],
        "only_target_identity_failed": (
            substantive_false == list(parsed["expected_substantive_false_gates"])
        ) == gates_config["require_only_target_identity_failed"],
        "source_provenance": (
            source["config_sha256"] == parsed["expected_source_config_sha256"]
            and source["implementation_sha256"] == parsed["expected_source_implementation_sha256"]
        ) == gates_config["require_source_provenance"],
        "target_rows": len(target_checks) == gates_config["expected_target_rows"],
        "belief_identity": all(row["belief_identity"] for row in target_checks) == gates_config["require_belief_identity"],
        "descriptor_rehash_identity": all(row["descriptor_rehash_identity"] for row in target_checks) == gates_config["require_descriptor_rehash_identity"],
        "parent_descriptor_identity": all(row["parent_descriptor_identity"] for row in target_checks) == gates_config["require_parent_descriptor_identity"],
        "exact_two_corrections": (
            len(corrections) == len(target_checks) == 2
            and all(row["incorrect_descriptor_identity"] for row in target_checks)
        ) == gates_config["require_exact_two_corrections"],
        "all_other_source_gates_true": all_other_true == gates_config["require_all_other_source_gates_true"],
        "aggregate_identity": (
            _canonical(aggregate_round_trip) == _canonical(source["aggregate"])
        ) == gates_config["require_aggregate_identity"],
        "no_strategy_recomputation": True == gates_config["require_no_strategy_recomputation"],
        "strategy_population_claim_null": (
            source["strategy_population_claim"] is None
        ) == gates_config["require_strategy_population_claim_null"],
    }
    gates["passed"] = all(gates.values())
    corrected_source_gates = dict(source_gates)
    corrected_source_gates["target_identity"] = gates["passed"]
    corrected_source_gates["passed"] = all(
        value for key, value in corrected_source_gates.items() if key != "passed"
    )
    return {
        "target_checks": target_checks,
        "substantive_false_gates": substantive_false,
        "aggregate": aggregate_round_trip,
        "aggregate_canonical_sha256": hashlib.sha256(
            _canonical(aggregate_round_trip).encode("utf-8")
        ).hexdigest(),
        "corrected_source_gates": corrected_source_gates,
        "gates": gates,
    }


def run_h32_deep_horizon_correction_replay(
    config_path: Path = _CONFIG, output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Replay only the frozen metadata gate against the retained v1 artifact."""

    parsed = parse_h32_deep_horizon_correction_config(
        json.loads(config_path.read_text(encoding="utf-8")),
    )
    source = json.loads(_SOURCE_RESULT.read_text(encoding="utf-8"))
    source_config = json.loads(_SOURCE_CONFIG.read_text(encoding="utf-8"))
    parent = json.loads(_PARENT_RESULT.read_text(encoding="utf-8"))
    replay = validate_correction_payload(
        parsed=parsed, source=source, source_config=source_config, parent=parent,
    )
    result = {
        "schema_version": 1,
        "status": "h32_deep_horizon_v1_metadata_correction_replayed",
        "methodology": {
            "read_only": True, "gpu_work_executed": False,
            "strategy_quality_recomputed": False, "aggregate_recomputed": False,
            "source_result_remains_rejected": True,
        },
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_result_sha256": _sha256(_SOURCE_RESULT),
        "environment": environment_metadata(),
        **replay,
        "decision": (
            "accept_metadata_corrected_deep_horizon_measurement"
            if replay["gates"]["passed"] else "reject_deep_horizon_correction"
        ),
        "strategy_population_claim": None,
        "limitations": list(source["limitations"]) + [
            "The original v1 artifact remains a rejected invocation.",
            "This replay corrects only two descriptor expectations from the authoritative parent and performs no GPU or strategy computation.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
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
    result = run_h32_deep_horizon_correction_replay(args.config, args.output)
    print(json.dumps({"output": str(args.output), "passed": result["gates"]["passed"], "aggregate": result["aggregate"]}, indent=2))
    if not result["gates"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
