"""Seed-only h32 campaign for exact pre-bet initial-row cache bytes.

The resulting hashes are observations, not trust roots.  This executable has
no capacity-replay or strategy-label phase; a later clean preregistration must
pin the literal seed-result hash before any cache can be admitted on-clock.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

from .atomic_json_checkpoint import write_atomic_json_checkpoint
from .campaign_deadline import CampaignDeadlineStop, MonotonicCampaignDeadline
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    release_cupy_memory_pool,
)
from .h32_affine_resident_cache_preflight import (
    _strict_git_metadata,
    _validate_runtime,
)
from .h32_pre_bet_action_width_capacity import (
    _inventory_digest,
    _source_objects,
    _target_objects,
    target_specs,
)
from .h32_pre_bet_initial_row_gpu import (
    h32_gpu_row_primitive_digest,
    seed_h32_pre_bet_initial_row_cache,
)
from .h32_pre_bet_work_reduction_analysis import (
    analyze_h32_pre_bet_work_reduction,
)
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    serialize_result,
)


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-pre-bet-initial-row-cache-seed-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-pre-bet-initial-row-cache-seed-v1.json"
_CHECKPOINT = (
    _ROOT / "experiments/results/h32-pre-bet-initial-row-cache-seed-v1.partial.json"
)
_CACHE_ROOT = _ROOT / "experiments/cache/h32-pre-bet-initial-row-cache-seed-v1"
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_SOURCE_CONFIG = (
    _ROOT / "experiments/configs/h32-fresh-panel-source-blueprints-v1.json"
)
_SEALED_TIMING = (
    _ROOT / "experiments/results/h32-pre-bet-action-width-capacity-v1.json"
)
_ADR_0278 = (
    _ROOT
    / "docs/decisions"
    / "ADR-0278-reject-pre-bet-action-width-capacity-invocation-on-campaign-duration.md"
)
_ADR_0279 = (
    _ROOT
    / "docs/decisions"
    / "ADR-0279-install-active-campaign-deadlines-and-prioritize-exact-pre-bet-row-speculation.md"
)
_ADR_0280 = (
    _ROOT
    / "docs/decisions/ADR-0280-exact-pre-bet-row-cache-passes-cpu-h2-fail-closed-control.md"
)
_IMPLEMENTATION = Path(__file__)
_GPU_PRIMITIVE = _ROOT / "src/pontius/h32_pre_bet_initial_row_gpu.py"
_CACHE_IMPLEMENTATION = _ROOT / "src/pontius/pre_bet_initial_row_cache.py"
_PARENT_RUNNER = _ROOT / "src/pontius/h32_pre_bet_action_width_capacity.py"
_TIMING_ANALYZER = _ROOT / "src/pontius/h32_pre_bet_work_reduction_analysis.py"
_DEADLINE = _ROOT / "src/pontius/campaign_deadline.py"
_CHECKPOINT_HELPER = _ROOT / "src/pontius/atomic_json_checkpoint.py"
_RUNNER_HARNESS = _ROOT / "src/pontius/runner_harness.py"
_TEST = _ROOT / "tests/test_h32_pre_bet_initial_row_cache_seed.py"
_CAMPAIGN_MAXIMUM_SECONDS = 3600.0

_PATHS = {
    "expected_source_result_sha256": (_SOURCE, "literal"),
    "expected_source_config_sha256": (_SOURCE_CONFIG, "canonical_lf"),
    "expected_sealed_timing_result_sha256": (_SEALED_TIMING, "literal"),
    "expected_rejection_decision_sha256": (_ADR_0278, "canonical_lf"),
    "expected_work_reduction_decision_sha256": (_ADR_0279, "canonical_lf"),
    "expected_cache_control_decision_sha256": (_ADR_0280, "canonical_lf"),
    "expected_parent_runner_sha256": (_PARENT_RUNNER, "canonical_lf"),
    "expected_timing_analyzer_sha256": (_TIMING_ANALYZER, "canonical_lf"),
    "expected_deadline_implementation_sha256": (_DEADLINE, "canonical_lf"),
    "expected_cache_implementation_sha256": (_CACHE_IMPLEMENTATION, "canonical_lf"),
    "expected_gpu_primitive_implementation_sha256": (
        _GPU_PRIMITIVE,
        "canonical_lf",
    ),
    "expected_checkpoint_helper_sha256": (_CHECKPOINT_HELPER, "canonical_lf"),
    "expected_runner_harness_sha256": (_RUNNER_HARNESS, "canonical_lf"),
    "expected_implementation_sha256": (_IMPLEMENTATION, "canonical_lf"),
    "expected_control_test_sha256": (_TEST, "canonical_lf"),
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required pre-bet cache-seed input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _provenance_sha256(path: Path, hash_mode: str) -> str:
    if hash_mode == "literal":
        return _sha256(path)
    if hash_mode != "canonical_lf":
        raise ValueError("pre-bet cache-seed provenance hash mode is invalid")
    if not path.is_file():
        raise ValueError(f"required pre-bet cache-seed input is unavailable: {path}")
    payload = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in payload:
        raise ValueError(f"pre-bet cache-seed input has unsupported line endings: {path}")
    return hashlib.sha256(payload).hexdigest()


def _strict_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("pre-bet cache-seed config contains a duplicate field")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"pre-bet cache-seed config contains {value}")


def _load_config(path: Path) -> dict[str, Any]:
    decoded = json.loads(
        path.read_bytes(),
        object_pairs_hook=_strict_json_object,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(decoded, dict):
        raise ValueError("pre-bet cache-seed config root must be an object")
    return decoded


def _cache_file_name(source_index: int, source: str, arm_name: str) -> str:
    token = source.replace("_", "-").replace("/", "-")
    return f"{source_index + 1:02d}-{token}-seat5-{arm_name.replace('_', '-')}.json"


def _cache_entry_specs(sources: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for source_index, source in enumerate(sources):
        target_id = f"{source['source']}/checks_to_seat5"
        for arm_name in ("one_size", "two_size"):
            rows.append(
                {
                    "target_id": target_id,
                    "arm": arm_name,
                    "path": (
                        "experiments/cache/h32-pre-bet-initial-row-cache-seed-v1/"
                        + _cache_file_name(
                            source_index,
                            str(source["source"]),
                            arm_name,
                        )
                    ),
                }
            )
    return rows


def _exact_contract() -> dict[str, Any]:
    return {
        "evidence_stage": (
            "preregistered_after_adr0280_before_any_h32_exact_row_cache_seed_"
            "lookup_capacity_replay_master_candidate_or_strategy_label"
        ),
        "authorized_phase": "cache_seed_only",
        "trusted_seed_manifest_sha256": None,
        "capacity_replay_authorized": False,
        "acting_player_order": [5],
        "target_rule": (
            "all_six_retained_sources_at_seat5_selected_only_from_the_sealed_"
            "label_free_timing_matrix"
        ),
        "arm_rule": (
            "seed_distinct_exact_one_size_and_two_size_initial_row_bundles_"
            "without_replay"
        ),
        "temporal_trust_rule": (
            "same_invocation_cache_hashes_are_observed_only_and_require_a_"
            "later_clean_config_to_pin_the_complete_seed_result_hash"
        ),
        "miss_rule": (
            "every_future_lookup_miss_is_a_completed_immutable_one_size_"
            "blueprint_fallback_with_zero_rows_masters_candidates_or_labels"
        ),
        "prelabel_rule": (
            "all_twelve_cache_bytes_must_be_frozen_before_a_separate_replay_"
            "preregistration_and_no_seed_invocation_can_open_a_label"
        ),
        "street_budget_ms": 15000.0,
        "second_master_reserve_ms": 500.0,
        "proof_reserve_ms": 1250.0,
        "retreat_envelope_reserve_ms": 50.0,
        "emission_reserve_ms": 1000.0,
        "minimum_noncache_reserve_bytes": 5_184_456_164,
        "pot": 12.0,
        "stack": 30.0,
        "one_size_bets": [3.0],
        "two_size_bets": [3.0, 6.0],
        "players": 6,
        "hands_per_player": 32,
        "axis_seed": 20260819,
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 384,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
        "maximum_campaign_seconds": _CAMPAIGN_MAXIMUM_SECONDS,
        "maximum_context_unit_seconds": 120.0,
        "maximum_cache_seed_unit_seconds": 120.0,
        "selection_evidence": {
            "scenario": "remove_warm_plus_zero_cost_exact_initial_row_cache_hit",
            "selected_acting_player": 5,
            "fit_count": 6,
            "complete_positions": [5],
            "worst_selected_position_proxy_ms": 12966.496699966956,
            "conditional_headroom_ms": 2033.503300033044,
            "status": "conditional_ceiling_not_capacity_evidence",
        },
    }


def _expected_gates() -> dict[str, Any]:
    return {
        "expected_sources": 6,
        "expected_targets": 6,
        "expected_cache_entries": 12,
        "expected_profile_rows_per_entry": 6,
        "expected_response_rows_per_entry": 5,
        "expected_gain_rows_per_entry": 6,
        "maximum_source_row_error": 2e-11,
        "maximum_gain_source_error": 2e-11,
        "maximum_cache_cold_construction_ms": 120000.0,
        "maximum_source_oracle_ms": 120000.0,
        "maximum_initial_row_ms": 120000.0,
        "maximum_mechanical_lookup_ms": 2000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_sealed_timing_selection": True,
        "require_distinct_gpu_primitive_manifests": True,
        "require_source_checkpoint_identity": True,
        "require_inventory_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_cache_byte_truth": True,
        "require_exact_row_byte_round_trip": True,
        "require_active_deadline": True,
        "require_checkpoint_bytes_truth": True,
        "require_temporal_separation": True,
        "require_campaign_prelabel_barrier": True,
        "require_blueprint_fallback": True,
        "require_zero_candidate_evaluations": True,
        "require_zero_strategy_labels": True,
        "require_zero_policy_emissions": True,
        "require_strategy_population_claim_null": True,
        "require_finite": True,
    }


def _exact_json_equal(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(  # type: ignore[arg-type]
            _exact_json_equal(actual[key], value)  # type: ignore[index]
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(  # type: ignore[arg-type]
            _exact_json_equal(left, right)
            for left, right in zip(actual, expected, strict=True)  # type: ignore[arg-type]
        )
    return actual == expected


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected_fields = {
        *_PATHS,
        "expected_one_size_gpu_row_primitive_sha256",
        "expected_two_size_gpu_row_primitive_sha256",
        "expected_inventory_sha256",
        "sources",
        "cache_entries",
        "gates",
        *_exact_contract(),
    }
    if set(config) != expected_fields:
        raise ValueError("pre-bet cache-seed config fields differ from ADR-0281")
    for field_name, (path, hash_mode) in _PATHS.items():
        if config[field_name] != _provenance_sha256(path, hash_mode):
            raise ValueError(f"pre-bet cache-seed provenance mismatch: {field_name}")
    exact = _exact_contract()
    for field_name, expected_value in exact.items():
        if not _exact_json_equal(config[field_name], expected_value):
            raise ValueError(f"pre-bet cache-seed contract differs: {field_name}")
    source_config = _load_config(_SOURCE_CONFIG)
    boards = {
        row["board_id"]: list(row["cards"])
        for row in source_config["panels"]
    }
    expected_sources = [
        {
            "source": source,
            "board": boards[source.split("/")[0]],
            "range_family": source.split("/")[1],
            "source_belief_sha256": source_config[
                "source_belief_sha256_by_source"
            ][source],
        }
        for source in source_config["source_order"]
    ]
    if not _exact_json_equal(config["sources"], expected_sources):
        raise ValueError("pre-bet cache-seed sources differ from sealed source order")
    expected_entries = _cache_entry_specs(expected_sources)
    if not _exact_json_equal(config["cache_entries"], expected_entries):
        raise ValueError("pre-bet cache-seed file inventory differs")
    gates = _expected_gates()
    if not _exact_json_equal(config["gates"], gates):
        raise ValueError("pre-bet cache-seed gates differ from ADR-0281")
    if (
        not isinstance(config["expected_inventory_sha256"], str)
        or len(config["expected_inventory_sha256"]) != 64
        or config["expected_inventory_sha256"]
        != config["expected_inventory_sha256"].lower()
        or any(
            character not in "0123456789abcdef"
            for character in config["expected_inventory_sha256"]
        )
    ):
        raise ValueError("pre-bet cache-seed inventory digest is malformed")
    timing = analyze_h32_pre_bet_work_reduction(_SEALED_TIMING)
    selected = timing["arms"]["two_size"]["scenarios"][
        "remove_warm_plus_zero_cost_exact_initial_row_cache_hit"
    ]
    selection = config["selection_evidence"]
    if (
        selected["fit_count"] != selection["fit_count"]
        or selected["complete_positions"] != selection["complete_positions"]
        or selected["maximum_by_position_ms"]["5"]
        != selection["worst_selected_position_proxy_ms"]
        or 15000.0 - selected["maximum_by_position_ms"]["5"]
        != selection["conditional_headroom_ms"]
    ):
        raise ValueError("pre-bet cache-seed sealed timing selection differs")
    parsed = {
        **config,
        "sources": tuple(dict(row) for row in expected_sources),
        "cache_entries": tuple(dict(row) for row in expected_entries),
        "acting_player_order": tuple(config["acting_player_order"]),
        "one_size_bets": tuple(config["one_size_bets"]),
        "two_size_bets": tuple(config["two_size_bets"]),
        "gates": gates,
    }
    one_digest = h32_gpu_row_primitive_digest("one_size", parsed)
    two_digest = h32_gpu_row_primitive_digest("two_size", parsed)
    if one_digest == two_digest:
        raise ValueError("pre-bet cache-seed GPU primitive manifests alias")
    if (
        config["expected_one_size_gpu_row_primitive_sha256"] != one_digest
        or config["expected_two_size_gpu_row_primitive_sha256"] != two_digest
    ):
        raise ValueError("pre-bet cache-seed GPU primitive manifest differs")
    return parsed


@dataclass(slots=True)
class CacheSeedPrelabelBarrier:
    """Ordered all-cache barrier with no replay-opening operation."""

    expected: tuple[tuple[str, str], ...]
    completed: list[tuple[str, str]] = field(default_factory=list)
    phase: str = "cache_seed"

    def record(self, target_id: str, arm_name: str) -> None:
        if self.phase != "cache_seed":
            raise RuntimeError("pre-bet cache-seed barrier is already frozen")
        observed = (target_id, arm_name)
        if len(self.completed) >= len(self.expected) or observed != self.expected[
            len(self.completed)
        ]:
            raise RuntimeError("pre-bet cache-seed order differs from preregistration")
        self.completed.append(observed)

    def freeze_untrusted_bytes(self) -> None:
        if tuple(self.completed) != self.expected:
            raise RuntimeError("pre-bet cache-seed barrier is incomplete")
        self.phase = "cache_bytes_observed_untrusted"

    def snapshot(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "expected_cache_entries": len(self.expected),
            "completed_cache_entries": len(self.completed),
            "complete": tuple(self.completed) == self.expected,
            "capacity_replay_authorized": False,
            "trusted_seed_manifest_sha256": None,
            "candidate_endpoints_opened": 0,
            "certificates_opened": 0,
            "strategy_quality_rows_opened": 0,
            "candidate_policies_emitted": 0,
        }


class _SeedGateStop(RuntimeError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"pre-bet cache-seed fail-fast stop: {reason}")


def _finite_tree(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return False


def _cache_path(relative: str) -> Path:
    candidate = (_ROOT / relative).resolve()
    cache_root = _CACHE_ROOT.resolve()
    if candidate.parent != cache_root:
        raise ValueError("pre-bet cache-seed path escapes the frozen cache directory")
    return candidate


def _entry_passes_component_gates(
    row: Mapping[str, Any],
    gates: Mapping[str, Any],
) -> bool:
    return bool(
        row["cache"]["cold_construction_ms"]
        <= gates["maximum_cache_cold_construction_ms"]
        and row["source_oracle_ms"] <= gates["maximum_source_oracle_ms"]
        and row["initial_row_ms"] <= gates["maximum_initial_row_ms"]
        and row["mechanical_round_trip_lookup_ms"]
        <= gates["maximum_mechanical_lookup_ms"]
        and row["maximum_source_row_error"] <= gates["maximum_source_row_error"]
        and row["maximum_gain_source_error"] <= gates["maximum_gain_source_error"]
        and row["cache"]["pool_total_bytes"] <= gates["maximum_gpu_pool_bytes"]
        and row["memory_after_seed"]["gpu_free_bytes"]
        >= gates["minimum_physical_free_bytes"]
        and row["exact_row_byte_round_trip"]
    )


def run_h32_pre_bet_initial_row_cache_seed(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
    checkpoint_path: Path = _CHECKPOINT,
) -> dict[str, Any]:
    """Run the seed-only campaign once; never admit or replay its own hashes."""

    deadline = MonotonicCampaignDeadline(_CAMPAIGN_MAXIMUM_SECONDS)
    parsed = _parse_config(_load_config(config_path))
    all_outputs = [output_path, checkpoint_path] + [
        _cache_path(row["path"]) for row in parsed["cache_entries"]
    ]
    if any(path.exists() for path in all_outputs):
        raise RuntimeError("pre-bet cache-seed invocation requires absent output paths")
    git = _strict_git_metadata()
    if git["dirty"]:
        raise RuntimeError("pre-bet cache-seed invocation requires clean Git")
    cp, runtime = _validate_runtime(parsed)
    source_parent_artifact = load_artifact(
        _SOURCE,
        expected_sha256=parsed["expected_source_result_sha256"],
        require_passed=True,
    )
    source_config_artifact = load_artifact(
        _SOURCE_CONFIG,
        expected_sha256=parsed["expected_source_config_sha256"],
    )
    source_parent = source_parent_artifact.payload
    source_config = source_config_artifact.payload
    specs = target_specs(parsed)
    expected_order = tuple(
        (row["target_id"], row["arm"]) for row in parsed["cache_entries"]
    )
    barrier = CacheSeedPrelabelBarrier(expected_order)
    cache_rows: list[dict[str, Any]] = []
    inventory_rows: list[dict[str, Any]] = []
    unit_rows: list[dict[str, Any]] = []
    stop_record: dict[str, Any] | None = None
    checkpoint_sha256: str | None = None

    def persist_checkpoint(phase: str) -> None:
        nonlocal checkpoint_sha256
        checkpoint_sha256 = write_atomic_json_checkpoint(
            {
                "schema_version": 1,
                "status": "h32_pre_bet_initial_row_cache_seed_partial",
                "authorized_phase": "cache_seed_only",
                "phase": phase,
                "config_sha256": _sha256(config_path),
                "cache_entries_completed": len(cache_rows),
                "inventory_targets_completed": len(inventory_rows),
                "cache_rows": cache_rows,
                "inventory_rows": inventory_rows,
                "unit_rows": unit_rows,
                "barrier": barrier.snapshot(),
                "deadline": deadline.snapshot().as_record(),
                "stop": stop_record,
            },
            checkpoint_path,
        )

    try:
        for source_spec in parsed["sources"]:
            source = None
            gpu = None
            target = None
            target_spec = next(
                row for row in specs if row["source"] == source_spec["source"]
            )
            context_name = f"context/{target_spec['target_id']}"
            context_started_ns = time.monotonic_ns()
            try:
                with deadline.bounded_unit(
                    context_name,
                    float(parsed["maximum_context_unit_seconds"]),
                    checkpoint=lambda name=context_name: persist_checkpoint(
                        f"before/{name}"
                    ),
                ) as admitted:
                    source = _source_objects(parsed, source_parent, source_spec)
                    gpu = CuPyBidirectionalIncidence.compile(source["sparse"])
                    target = _target_objects(parsed, source, target_spec, gpu)
                    inventory_rows.append(dict(target["inventory"]))
                unit_rows.append(
                    {
                        "unit": context_name,
                        "maximum_seconds": parsed["maximum_context_unit_seconds"],
                        "admitted_deadline": admitted.as_record(),
                        "elapsed_seconds": (
                            time.monotonic_ns() - context_started_ns
                        )
                        / 1_000_000_000.0,
                        "completed": True,
                    }
                )
                assert target is not None
                for arm_name in ("one_size", "two_size"):
                    entry_spec = next(
                        row
                        for row in parsed["cache_entries"]
                        if row["target_id"] == target_spec["target_id"]
                        and row["arm"] == arm_name
                    )
                    unit_name = f"seed/{target_spec['target_id']}/{arm_name}"
                    unit_started_ns = time.monotonic_ns()
                    seeded: dict[str, Any] | None = None
                    with deadline.bounded_unit(
                        unit_name,
                        float(parsed["maximum_cache_seed_unit_seconds"]),
                        checkpoint=lambda name=unit_name: persist_checkpoint(
                            f"before/{name}"
                        ),
                    ) as admitted:
                        seeded = seed_h32_pre_bet_initial_row_cache(
                            parsed,
                            cp,
                            target,
                            arm_name,
                            _cache_path(entry_spec["path"]),
                        )
                    assert seeded is not None
                    seeded = {
                        **target["inventory"],
                        "source_identity": bool(target["source_identity"]),
                        "cache_path": entry_spec["path"],
                        "complete_seed_unit_ms": (
                            time.monotonic_ns() - unit_started_ns
                        )
                        / 1_000_000.0,
                        **seeded,
                    }
                    cache_rows.append(seeded)
                    unit_rows.append(
                        {
                            "unit": unit_name,
                            "maximum_seconds": parsed[
                                "maximum_cache_seed_unit_seconds"
                            ],
                            "admitted_deadline": admitted.as_record(),
                            "elapsed_seconds": seeded["complete_seed_unit_ms"]
                            / 1000.0,
                            "completed": True,
                        }
                    )
                    if not _entry_passes_component_gates(seeded, parsed["gates"]):
                        raise _SeedGateStop(f"component_gate/{unit_name}")
                    barrier.record(target_spec["target_id"], arm_name)
            finally:
                target = None
                gpu = None
                source = None
                gc.collect()
                release_cupy_memory_pool()
        barrier.freeze_untrusted_bytes()
    except CampaignDeadlineStop as exc:
        stop_record = {"kind": "campaign_deadline", **exc.as_record()}
    except _SeedGateStop as exc:
        stop_record = {"kind": "component_gate", "reason": exc.reason}

    persist_checkpoint("seed_complete" if stop_record is None else "stopped")
    actual_inventory_sha256 = _inventory_digest(inventory_rows)
    final_deadline = deadline.snapshot()
    all_paths_match = all(
        _cache_path(row["cache_path"]).is_file()
        and _sha256(_cache_path(row["cache_path"])) == row["cache_sha256"]
        and _cache_path(row["cache_path"]).stat().st_size == row["cache_bytes"]
        for row in cache_rows
    )
    all_counters = [
        row[key]
        for row in cache_rows
        for key in (
            "warm_steps",
            "master_solves",
            "candidate_endpoint_evaluations",
            "separation_or_certificate_evaluations",
            "strategy_quality_rows",
            "candidate_policies_emitted",
        )
    ]
    gates = parsed["gates"]
    barrier_snapshot = barrier.snapshot()
    checks = {
        "clean_git_start": (not git["dirty"]) == gates["require_clean_git_state"],
        "parents_passed": (
            artifact_passed(source_parent)
            and source_config["source_order"]
            == [row["source"] for row in parsed["sources"]]
        )
        == gates["require_parents_passed"],
        "sealed_timing_selection": (
            parsed["acting_player_order"] == (5,)
            and parsed["selection_evidence"]["complete_positions"] == [5]
            and parsed["selection_evidence"]["status"]
            == "conditional_ceiling_not_capacity_evidence"
        )
        == gates["require_sealed_timing_selection"],
        "distinct_gpu_primitive_manifests": (
            parsed["expected_one_size_gpu_row_primitive_sha256"]
            != parsed["expected_two_size_gpu_row_primitive_sha256"]
            and all(
                row["row_primitive_sha256"]
                == parsed[f"expected_{row['arm']}_gpu_row_primitive_sha256"]
                for row in cache_rows
            )
        )
        == gates["require_distinct_gpu_primitive_manifests"],
        "source_checkpoint_identity": all(
            row["source_identity"] for row in cache_rows
        )
        == gates["require_source_checkpoint_identity"],
        "inventory_identity": (
            len(inventory_rows) == gates["expected_targets"]
            and actual_inventory_sha256 == parsed["expected_inventory_sha256"]
        )
        == gates["require_inventory_identity"],
        "target_identity": (
            len({row["target_id"] for row in inventory_rows})
            == gates["expected_targets"]
            and len({row["target_belief_sha256"] for row in inventory_rows})
            == gates["expected_targets"]
        )
        == gates["require_target_identity"],
        "blueprint_identity": all(
            isinstance(row["blueprint_sha256"], str)
            and len(row["blueprint_sha256"]) == 64
            for row in cache_rows
        )
        == gates["require_blueprint_identity"],
        "cache_count_and_roles": (
            len(cache_rows) == gates["expected_cache_entries"]
            and all(
                row["initial_profile_rows"]
                == gates["expected_profile_rows_per_entry"]
                and row["initial_response_rows"]
                == gates["expected_response_rows_per_entry"]
                and row["initial_gain_rows"]
                == gates["expected_gain_rows_per_entry"]
                for row in cache_rows
            )
        ),
        "cache_byte_truth": all_paths_match
        == gates["require_cache_byte_truth"],
        "row_numerics": all(
            row["maximum_source_row_error"] <= gates["maximum_source_row_error"]
            and row["maximum_gain_source_error"] <= gates["maximum_gain_source_error"]
            for row in cache_rows
        ),
        "exact_row_byte_round_trip": all(
            row["exact_row_byte_round_trip"] for row in cache_rows
        )
        == gates["require_exact_row_byte_round_trip"],
        "component_caps": all(
            _entry_passes_component_gates(row, gates) for row in cache_rows
        ),
        "resource_caps": (
            stop_record is None
            and not final_deadline.deadline_crossed
            and final_deadline.elapsed_seconds <= parsed["maximum_campaign_seconds"]
            and all(
                row["complete_seed_unit_ms"]
                <= 1000.0 * parsed["maximum_cache_seed_unit_seconds"]
                for row in cache_rows
            )
        ),
        "active_deadline": (
            final_deadline.maximum_seconds == _CAMPAIGN_MAXIMUM_SECONDS
            and len(unit_rows)
            == gates["expected_targets"] + gates["expected_cache_entries"]
            and all(row["maximum_seconds"] > 0.0 for row in unit_rows)
        )
        == gates["require_active_deadline"],
        "checkpoint_byte_truth": (
            checkpoint_sha256 is not None
            and _sha256(checkpoint_path) == checkpoint_sha256
        )
        == gates["require_checkpoint_bytes_truth"],
        "temporal_separation": (
            parsed["authorized_phase"] == "cache_seed_only"
            and parsed["trusted_seed_manifest_sha256"] is None
            and parsed["capacity_replay_authorized"] is False
            and all(
                row["cache_hash_status"]
                == "observed_untrusted_until_external_seal"
                for row in cache_rows
            )
        )
        == gates["require_temporal_separation"],
        "campaign_prelabel_barrier": (
            barrier_snapshot["complete"]
            and barrier_snapshot["phase"] == "cache_bytes_observed_untrusted"
            and barrier_snapshot["capacity_replay_authorized"] is False
        )
        == gates["require_campaign_prelabel_barrier"],
        "immutable_blueprint_fallback": (
            parsed["miss_rule"].startswith("every_future_lookup_miss")
            and sum(row["candidate_policies_emitted"] for row in cache_rows) == 0
        )
        == gates["require_blueprint_fallback"],
        "zero_candidate_evaluations": all(
            row["candidate_endpoint_evaluations"] == 0
            and row["separation_or_certificate_evaluations"] == 0
            for row in cache_rows
        )
        == gates["require_zero_candidate_evaluations"],
        "zero_strategy_labels": all(
            row["strategy_quality_rows"] == 0 for row in cache_rows
        )
        == gates["require_zero_strategy_labels"],
        "zero_policy_emissions": all(
            row["candidate_policies_emitted"] == 0 for row in cache_rows
        )
        == gates["require_zero_policy_emissions"],
        "strategy_population_claim_null": True
        == gates["require_strategy_population_claim_null"],
        "finite": _finite_tree(
            {
                "cache_rows": cache_rows,
                "unit_rows": unit_rows,
                "deadline": final_deadline.as_record(),
                "stop": stop_record,
            }
        )
        == gates["require_finite"],
    }
    finalized = finalize_gates(checks)
    result = {
        "schema_version": 1,
        "status": "h32_pre_bet_initial_row_cache_seed_manifest",
        "evidence_stage": parsed["evidence_stage"],
        "authorized_phase": parsed["authorized_phase"],
        "config_sha256": _sha256(config_path),
        "implementation_sha256": parsed["expected_implementation_sha256"],
        "gpu_primitive_implementation_sha256": parsed[
            "expected_gpu_primitive_implementation_sha256"
        ],
        "cache_implementation_sha256": parsed[
            "expected_cache_implementation_sha256"
        ],
        "source_result_sha256": source_parent_artifact.sha256,
        "source_config_sha256": source_config_artifact.sha256,
        "sealed_timing_result_sha256": _sha256(_SEALED_TIMING),
        "inventory_sha256": actual_inventory_sha256,
        "checkpoint_sha256": checkpoint_sha256,
        "selection_evidence": parsed["selection_evidence"],
        "cache_entries": cache_rows,
        "cache_entry_order": list(expected_order),
        "primitive_manifests": {
            "one_size": parsed["expected_one_size_gpu_row_primitive_sha256"],
            "two_size": parsed["expected_two_size_gpu_row_primitive_sha256"],
        },
        "temporal_trust": {
            "seed_manifest_sha256": None,
            "seed_manifest_hash_status": "not_self_trusted",
            "trusted_seed_manifest_sha256": None,
            "capacity_replay_authorized": False,
            "required_next_step": (
                "external_clean_commit_pins_this_literal_result_hash_before_"
                "separate_capacity_replay_preregistration"
            ),
        },
        "barrier": barrier_snapshot,
        "deadline": final_deadline.as_record(),
        "unit_rows": unit_rows,
        "stop": stop_record,
        "methodology": {
            "warm_steps": sum(row["warm_steps"] for row in cache_rows),
            "master_solves": sum(row["master_solves"] for row in cache_rows),
            "candidate_endpoint_evaluations": sum(
                row["candidate_endpoint_evaluations"] for row in cache_rows
            ),
            "separation_or_certificate_evaluations": sum(
                row["separation_or_certificate_evaluations"] for row in cache_rows
            ),
            "strategy_quality_rows": sum(
                row["strategy_quality_rows"] for row in cache_rows
            ),
            "candidate_policies_emitted": sum(
                row["candidate_policies_emitted"] for row in cache_rows
            ),
            "counter_sum": sum(all_counters),
            "actual_external_policy": "immutable_one_size_blueprint_only",
        },
        "strategy_population_claim": None,
        "environment": assemble_environment(runtime=runtime, git=git),
        "decision": (
            "seal_observed_cache_bytes_before_separate_replay_preregistration"
            if finalized["passed"]
            else "reject_cache_seed_invocation_without_capacity_replay"
        ),
        **finalized,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = serialize_result(result).encode("utf-8")
    output_path.write_bytes(rendered)
    if output_path.read_bytes() != rendered:
        raise OSError("persisted pre-bet cache-seed result bytes differ")
    return result


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, default=_CHECKPOINT)
    args = parser.parse_args()
    result = run_h32_pre_bet_initial_row_cache_seed(
        args.config,
        args.output,
        args.checkpoint,
    )
    print(serialize_result(result), end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
