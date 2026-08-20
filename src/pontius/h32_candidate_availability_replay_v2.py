"""Additive control-flow correction for the frozen availability replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from . import h32_candidate_availability_replay as v1


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments" / "configs" / "h32-candidate-availability-replay-v2.json"
_OUTPUT = _ROOT / "experiments" / "results" / "h32-candidate-availability-replay-v2.json"
_V1_CONFIG = _ROOT / "experiments" / "configs" / "h32-candidate-availability-replay-v1.json"
_V1_OUTPUT = _ROOT / "experiments" / "results" / "h32-candidate-availability-replay-v1.json"
_V1_IMPLEMENTATION = _ROOT / "src" / "pontius" / "h32_candidate_availability_replay.py"
_IMPLEMENTATION = Path(__file__)


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"availability correction source is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_h32_candidate_availability_v2_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage": (
            "additive_control_flow_correction_after_v1_nameerror_before_any_"
            "result_artifact"
        ),
        "expected_v1_config_sha256": _sha256(_V1_CONFIG),
        "expected_v1_implementation_sha256": _sha256(_V1_IMPLEMENTATION),
        "expected_correction_implementation_sha256": _sha256(_IMPLEMENTATION),
        "correction": "supply_stage_count_sentinel_from_frozen_availability_only",
        "require_no_v1_result_artifact": True,
    }
    if config != expected:
        raise ValueError("candidate-availability v2 correction config differs")
    if _V1_OUTPUT.exists():
        raise ValueError("candidate-availability v1 unexpectedly produced an artifact")
    return dict(config)


def _stage_count_sentinel(parsed_v1: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage_rows": [
            {
                "available_candidate_ids": [
                    candidate_id
                    for candidate_id, iteration in parsed_v1["availability"].items()
                    if int(iteration) <= stage
                ]
            }
            for stage in parsed_v1["stages"]
        ]
    }


def run_h32_candidate_availability_replay_v2(config: dict[str, Any]) -> dict[str, Any]:
    parse_h32_candidate_availability_v2_config(config)
    v1_config = json.loads(_V1_CONFIG.read_text(encoding="utf-8"))
    parsed_v1 = v1.parse_h32_candidate_availability_config(v1_config)
    if hasattr(v1, "row"):
        raise ValueError("candidate-availability v1 row sentinel already exists")
    v1.row = _stage_count_sentinel(parsed_v1)
    try:
        result = v1.run_h32_candidate_availability_replay(v1_config)
    finally:
        del v1.row
    result["status"] = "post_label_replay_executed_v2"
    result["base_config"] = result.pop("config")
    result["base_config_sha256"] = result.pop("config_sha256")
    result["base_implementation_sha256"] = result.pop("implementation_sha256")
    result["config"] = config
    result["config_sha256"] = _sha256(_CONFIG)
    result["implementation_sha256"] = _sha256(_IMPLEMENTATION)
    result["correction"] = {
        "kind": config["correction"],
        "v1_failure": "NameError: name 'row' is not defined",
        "scientific_workload_changed": False,
        "gate_changed": False,
        "source_changed": False,
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args(argv)
    result = run_h32_candidate_availability_replay_v2(
        json.loads(args.config.read_text(encoding="utf-8"))
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "h32 candidate availability replay v2: "
        f"passed={result['gates']['passed']} "
        f"step2={result['aggregate']['step2_full_selection_identity_count']}/"
        f"{result['aggregate']['targets']} "
        f"saved_minutes={result['aggregate']['avoided_recorded_full_measurement_minutes']:.3f}"
    )
    return 0 if result["gates"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
