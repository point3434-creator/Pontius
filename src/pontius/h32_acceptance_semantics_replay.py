"""Replay h32 acceptance vectors under frozen incumbent and blueprint contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import sys
import time
from typing import Any, Iterable


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-acceptance-semantics-replay-v1.json"
)
_OUTPUT = (
    _ROOT / "experiments" / "results" / "h32-acceptance-semantics-replay-v1.json"
)
_SOURCE_PATHS = {
    "adr0099": (
        _ROOT / "experiments" / "results" / "h32-warm-search-acceptance-v1.json"
    ),
    "adr0101": (
        _ROOT / "experiments" / "results" / "h32-warm-candidate-stream-v1.json"
    ),
    "adr0103": (
        _ROOT / "experiments" / "results" / "h32-current-interpolation-audit-v1.json"
    ),
}
_IMPLEMENTATION = Path(__file__)

_CONFIG_FIELDS = {
    "evidence_stage",
    "seed",
    "expected_source_sha256",
    "expected_audit_implementation_sha256",
    "source_order",
    "range_families",
    "target_shifts",
    "players",
    "payoff_span",
    "acceptance_guard_normalized",
    "pool_order",
    "order_variants",
    "seeded_permutation_count",
    "fixed_envelope_contract",
    "gates",
}
_GATE_FIELDS = {
    "expected_target_rows",
    "expected_source_target_rows",
    "expected_source_stream_candidates_per_target",
    "expected_union_candidates_per_target",
    "expected_order_variants_per_pool",
    "expected_new_strategy_evaluations",
    "require_source_hash_identity",
    "require_source_status_identity",
    "require_target_descriptor_identity",
    "require_blueprint_identity",
    "maximum_duplicate_quality_error",
    "maximum_quality_sum_error",
    "maximum_quality_normalization_error",
    "require_frozen_legacy_replay_identity",
    "require_fixed_envelope_order_invariance",
    "require_selected_cap_compliance",
    "require_synthetic_tie_semantics",
    "maximum_total_audit_seconds",
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required frozen input is unavailable: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _json_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_h32_acceptance_semantics_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the immutable ADR-0105 replay protocol."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError(
            "acceptance replay fields differ from ADR-0105: "
            f"missing={sorted(_CONFIG_FIELDS - set(config))!r}, "
            f"unknown={sorted(set(config) - _CONFIG_FIELDS)!r}"
        )
    frozen = {
        "evidence_stage": (
            "post_label_semantics_audit_after_adr0104_with_zero_new_strategy_"
            "evaluation"
        ),
        "seed": 20260820,
        "source_order": ["adr0099", "adr0101", "adr0103"],
        "range_families": ["balanced", "blocker_heavy"],
        "target_shifts": [
            "local_blocker_seat3_x2",
            "all_seat_strength_1_to2",
        ],
        "players": 6,
        "payoff_span": 30.0,
        "acceptance_guard_normalized": 1e-10,
        "pool_order": [
            "adr0099_frozen_stream",
            "adr0101_full_interleaved",
            "adr0103_interpolation",
            "full_measured_union",
        ],
        "order_variants": [
            "canonical",
            "reverse",
            "policy_digest",
            "seeded_permutations",
        ],
        "seeded_permutation_count": 64,
        "fixed_envelope_contract": {
            "cap_anchor": "blueprint_deviation_gain_plus_raw_guard_per_seat",
            "objective": "minimum_raw_nash_conv_among_cap_feasible_policies",
            "baseline_abstention": "retain_blueprint_when_within_raw_guard_of_minimum",
            "candidate_tie_band": "raw_nash_conv_at_most_minimum_plus_raw_guard",
            "candidate_tie_break": "lexicographically_smallest_policy_sha256",
            "stream_semantics": "recompute_canonical_choice_over_all_observed_policies",
            "coalition_safety": False,
        },
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("acceptance replay workload differs from ADR-0105")

    expected_source_hashes = {
        "adr0099": "150362ea770c80190c8124148fa66e0a376d98d1bd01b790f3d11e5ad9b5d8a9",
        "adr0101": "b432eda21d1978b1dd576a9f4e7451250f1d53dcf9a88a6efa739d681ecb6f33",
        "adr0103": "ba0fdd6ea8dfd67de3f74c9026588d3555525d362a74ad1f03295f35281cb8c0",
    }
    if config["expected_source_sha256"] != expected_source_hashes:
        raise ValueError("acceptance replay source hashes differ from ADR-0105")
    for source_id, source_path in _SOURCE_PATHS.items():
        if config["expected_source_sha256"][source_id] != _sha256(source_path):
            raise ValueError(f"frozen source hash mismatch for {source_id}")
    if config["expected_audit_implementation_sha256"] != _sha256(_IMPLEMENTATION):
        raise ValueError("frozen acceptance replay implementation hash mismatch")

    expected_gates = {
        "expected_target_rows": 4,
        "expected_source_target_rows": 12,
        "expected_source_stream_candidates_per_target": {
            "adr0099_frozen_stream": 3,
            "adr0101_full_interleaved": 8,
            "adr0103_interpolation": 5,
        },
        "expected_union_candidates_per_target": 13,
        "expected_order_variants_per_pool": 67,
        "expected_new_strategy_evaluations": 0,
        "require_source_hash_identity": True,
        "require_source_status_identity": True,
        "require_target_descriptor_identity": True,
        "require_blueprint_identity": True,
        "maximum_duplicate_quality_error": 1e-15,
        "maximum_quality_sum_error": 1e-12,
        "maximum_quality_normalization_error": 1e-15,
        "require_frozen_legacy_replay_identity": True,
        "require_fixed_envelope_order_invariance": True,
        "require_selected_cap_compliance": True,
        "require_synthetic_tie_semantics": True,
        "maximum_total_audit_seconds": 10.0,
    }
    gates = config["gates"]
    if (
        not isinstance(gates, dict)
        or set(gates) != _GATE_FIELDS
        or gates != expected_gates
    ):
        raise ValueError("acceptance replay gates differ from ADR-0105")

    return {
        **config,
        "source_order": tuple(config["source_order"]),
        "range_families": tuple(config["range_families"]),
        "target_shifts": tuple(config["target_shifts"]),
        "pool_order": tuple(config["pool_order"]),
        "order_variants": tuple(config["order_variants"]),
        "fixed_envelope_contract": dict(config["fixed_envelope_contract"]),
        "gates": {
            **gates,
            "expected_source_stream_candidates_per_target": dict(
                gates["expected_source_stream_candidates_per_target"]
            ),
        },
    }


def canonical_target_descriptor(descriptor: dict[str, Any]) -> dict[str, Any]:
    """Remove measurement-only fields from an otherwise frozen target descriptor."""

    return {
        key: value
        for key, value in descriptor.items()
        if key != "marginal_measurement_ms"
    }


def _quality_view(quality: dict[str, Any], *, players: int) -> dict[str, Any]:
    gains = [float(value) for value in quality["deviation_gains"]]
    if len(gains) != players:
        raise ValueError("acceptance vector has the wrong player count")
    row = {
        "policy_sha256": str(quality["policy_sha256"]),
        "nash_conv": float(quality["nash_conv"]),
        "normalized_nash_conv": float(quality["normalized_nash_conv"]),
        "deviation_gains": gains,
    }
    if (
        len(row["policy_sha256"]) != 64
        or any(character not in "0123456789abcdef" for character in row["policy_sha256"])
        or not all(
            math.isfinite(value)
            for value in [
                row["nash_conv"],
                row["normalized_nash_conv"],
                *row["deviation_gains"],
            ]
        )
    ):
        raise ValueError("non-finite or malformed acceptance quality")
    return row


def _maximum_quality_error(first: dict[str, Any], second: dict[str, Any]) -> float:
    if first["policy_sha256"] != second["policy_sha256"]:
        return math.inf
    values = [
        abs(float(first["nash_conv"]) - float(second["nash_conv"])),
        abs(
            float(first["normalized_nash_conv"])
            - float(second["normalized_nash_conv"])
        ),
    ]
    values.extend(
        abs(float(left) - float(right))
        for left, right in zip(
            first["deviation_gains"],
            second["deviation_gains"],
            strict=True,
        )
    )
    return max(values)


def _candidate_view(
    candidate: dict[str, Any],
    *,
    source_id: str,
    players: int,
) -> dict[str, Any]:
    candidate_id = str(candidate["candidate_id"])
    return {
        "candidate_id": candidate_id,
        "aliases": [candidate_id],
        "source_refs": [f"{source_id}:{candidate_id}"],
        "quality": _quality_view(candidate["quality"], players=players),
    }


def merge_policy_candidates(
    candidates: Iterable[dict[str, Any]],
    *,
    maximum_quality_error: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Deduplicate policy digests while requiring exact-quality agreement."""

    merged: dict[str, dict[str, Any]] = {}
    duplicate_rows = 0
    maximum_error = 0.0
    for candidate in candidates:
        digest = candidate["quality"]["policy_sha256"]
        if digest not in merged:
            merged[digest] = {
                "candidate_id": candidate["candidate_id"],
                "aliases": list(candidate["aliases"]),
                "source_refs": list(candidate["source_refs"]),
                "quality": dict(candidate["quality"]),
            }
            continue
        duplicate_rows += 1
        incumbent = merged[digest]
        error = _maximum_quality_error(incumbent["quality"], candidate["quality"])
        maximum_error = max(maximum_error, error)
        if error > maximum_quality_error:
            raise ValueError(
                f"duplicate policy quality mismatch for {digest}: {error:.3e}"
            )
        incumbent["aliases"] = sorted(
            set(incumbent["aliases"]) | set(candidate["aliases"])
        )
        incumbent["source_refs"] = sorted(
            set(incumbent["source_refs"]) | set(candidate["source_refs"])
        )
        incumbent["candidate_id"] = min(incumbent["aliases"])
    return list(merged.values()), {
        "input_rows": len(merged) + duplicate_rows,
        "unique_policies": len(merged),
        "duplicate_rows": duplicate_rows,
        "maximum_duplicate_quality_error": maximum_error,
    }


def _cap_diagnostics(
    blueprint: dict[str, Any],
    candidate: dict[str, Any],
    *,
    raw_guard: float,
) -> dict[str, Any]:
    excesses = [
        float(candidate_gain) - float(blueprint_gain) - raw_guard
        for blueprint_gain, candidate_gain in zip(
            blueprint["quality"]["deviation_gains"],
            candidate["quality"]["deviation_gains"],
            strict=True,
        )
    ]
    violating_seats = [
        seat for seat, excess in enumerate(excesses) if excess > 0.0
    ]
    return {
        "feasible": not violating_seats,
        "cap_excesses": excesses,
        "maximum_cap_excess": max(excesses),
        "violating_seats": violating_seats,
    }


def select_fixed_blueprint_envelope(
    blueprint: dict[str, Any],
    candidates: Iterable[dict[str, Any]],
    *,
    raw_guard: float,
) -> dict[str, Any]:
    """Select a deterministic scalar optimum inside fixed blueprint caps."""

    candidate_rows = list(candidates)
    feasible = [
        candidate
        for candidate in candidate_rows
        if _cap_diagnostics(blueprint, candidate, raw_guard=raw_guard)["feasible"]
    ]
    feasible_with_blueprint = [blueprint, *feasible]
    minimum_nash_conv = min(
        float(candidate["quality"]["nash_conv"])
        for candidate in feasible_with_blueprint
    )
    blueprint_abstention = (
        float(blueprint["quality"]["nash_conv"])
        <= minimum_nash_conv + raw_guard
    )
    if blueprint_abstention:
        selected = blueprint
        tie_band = [blueprint]
    else:
        tie_band = [
            candidate
            for candidate in feasible
            if float(candidate["quality"]["nash_conv"])
            <= minimum_nash_conv + raw_guard
        ]
        selected = min(
            tie_band,
            key=lambda candidate: (
                candidate["quality"]["policy_sha256"],
                candidate["candidate_id"],
            ),
        )
    selected_caps = _cap_diagnostics(
        blueprint,
        selected,
        raw_guard=raw_guard,
    )
    return {
        "selected_candidate_id": selected["candidate_id"],
        "selected_policy_sha256": selected["quality"]["policy_sha256"],
        "selected_nash_conv": selected["quality"]["nash_conv"],
        "selected_normalized_nash_conv": selected["quality"][
            "normalized_nash_conv"
        ],
        "selected_deviation_gains": selected["quality"]["deviation_gains"],
        "selected_maximum_cap_excess": selected_caps["maximum_cap_excess"],
        "selected_violating_seats": selected_caps["violating_seats"],
        "blueprint_abstention": blueprint_abstention,
        "feasible_candidate_count": len(feasible),
        "infeasible_candidate_count": len(candidate_rows) - len(feasible),
        "minimum_nash_conv": minimum_nash_conv,
        "tie_band_size": len(tie_band),
    }


def replay_fixed_blueprint_stream(
    blueprint: dict[str, Any],
    ordered_candidates: Iterable[dict[str, Any]],
    *,
    raw_guard: float,
) -> dict[str, Any]:
    """Recompute the canonical envelope choice over every observed prefix."""

    seen: list[dict[str, Any]] = []
    incumbent_digest = blueprint["quality"]["policy_sha256"]
    changes = 0
    result = select_fixed_blueprint_envelope(
        blueprint,
        seen,
        raw_guard=raw_guard,
    )
    for candidate in ordered_candidates:
        seen.append(candidate)
        result = select_fixed_blueprint_envelope(
            blueprint,
            seen,
            raw_guard=raw_guard,
        )
        if result["selected_policy_sha256"] != incumbent_digest:
            changes += 1
            incumbent_digest = result["selected_policy_sha256"]
    return {**result, "observed_candidates": len(seen), "incumbent_changes": changes}


def replay_incumbent_relative_pareto(
    blueprint: dict[str, Any],
    ordered_candidates: Iterable[dict[str, Any]],
    *,
    raw_guard: float,
) -> dict[str, Any]:
    """Replay the legacy aggregate-plus-coordinate-monotone acceptance rule."""

    incumbent = blueprint
    trace: list[dict[str, Any]] = []
    for candidate in ordered_candidates:
        improvement = (
            float(incumbent["quality"]["nash_conv"])
            - float(candidate["quality"]["nash_conv"])
        )
        gain_deltas = [
            float(candidate_gain) - float(incumbent_gain)
            for incumbent_gain, candidate_gain in zip(
                incumbent["quality"]["deviation_gains"],
                candidate["quality"]["deviation_gains"],
                strict=True,
            )
        ]
        accepted = improvement > raw_guard and max(gain_deltas) <= raw_guard
        if accepted:
            incumbent = candidate
        trace.append(
            {
                "candidate_id": candidate["candidate_id"],
                "improvement_raw": improvement,
                "maximum_deviation_gain_increase": max(gain_deltas),
                "accepted": accepted,
                "resulting_incumbent": incumbent["candidate_id"],
            }
        )
    return {
        "final_candidate_id": incumbent["candidate_id"],
        "final_policy_sha256": incumbent["quality"]["policy_sha256"],
        "final_nash_conv": incumbent["quality"]["nash_conv"],
        "final_normalized_nash_conv": incumbent["quality"][
            "normalized_nash_conv"
        ],
        "trace": trace,
    }


def _order_rows(
    candidates: list[dict[str, Any]],
    *,
    seed: int,
    seeded_permutation_count: int,
) -> list[tuple[str, list[dict[str, Any]]]]:
    rows = [
        ("canonical", list(candidates)),
        ("reverse", list(reversed(candidates))),
        (
            "policy_digest",
            sorted(
                candidates,
                key=lambda candidate: (
                    candidate["quality"]["policy_sha256"],
                    candidate["candidate_id"],
                ),
            ),
        ),
    ]
    for index in range(seeded_permutation_count):
        shuffled = list(candidates)
        random.Random(seed + index).shuffle(shuffled)
        rows.append((f"seeded_{index:03d}", shuffled))
    return rows


def _artifact_targets(artifact: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    targets: dict[tuple[str, str], dict[str, Any]] = {}
    for family_row in artifact["family_rows"]:
        family = str(family_row["range_family"])
        for target in family_row["targets"]:
            key = (family, str(target["target_shift"]))
            if key in targets:
                raise ValueError(f"duplicate target row: {key!r}")
            targets[key] = target
    return targets


def _source_stream_ids(source_id: str, target: dict[str, Any]) -> list[str]:
    if source_id == "adr0099":
        return [
            str(row["candidate_id"])
            for row in target["sequential_incumbents"]["trace"]
        ]
    if source_id == "adr0101":
        return [
            str(value)
            for value in target["portfolios"]["full_interleaved"]["candidate_ids"]
        ]
    if source_id == "adr0103":
        return [str(value) for value in target["portfolio"]["candidate_ids"]]
    raise ValueError(f"unknown source: {source_id}")


def _source_recorded_legacy(source_id: str, target: dict[str, Any]) -> dict[str, Any]:
    if source_id == "adr0099":
        row = target["sequential_incumbents"]
    elif source_id == "adr0101":
        row = target["portfolios"]["full_interleaved"]
    elif source_id == "adr0103":
        row = target["portfolio"]
    else:
        raise ValueError(f"unknown source: {source_id}")
    return {
        "candidate_id": str(row["final_unilateral_incumbent"]),
        "normalized_nash_conv": float(
            row["final_unilateral_normalized_nash_conv"]
        ),
    }


def _candidate_rows_by_id(target: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = {str(row["candidate_id"]): row for row in target["candidates"]}
    if len(rows) != len(target["candidates"]):
        raise ValueError("duplicate candidate IDs in source target")
    return rows


def _synthetic_tie_semantics(raw_guard: float) -> dict[str, Any]:
    blueprint = {
        "candidate_id": "blueprint_average64",
        "aliases": ["blueprint_average64"],
        "source_refs": ["synthetic:blueprint"],
        "quality": {
            "policy_sha256": "f" * 64,
            "nash_conv": 1.0,
            "normalized_nash_conv": 1.0,
            "deviation_gains": [1.0 / 6.0] * 6,
        },
    }

    def candidate(
        candidate_id: str,
        digest: str,
        nash_conv: float,
        gains: list[float] | None = None,
    ) -> dict[str, Any]:
        return {
            "candidate_id": candidate_id,
            "aliases": [candidate_id],
            "source_refs": [f"synthetic:{candidate_id}"],
            "quality": {
                "policy_sha256": digest,
                "nash_conv": nash_conv,
                "normalized_nash_conv": nash_conv,
                "deviation_gains": gains or [0.15] * 6,
            },
        }

    near = candidate("near", "0" * 64, 1.0 - 0.5 * raw_guard)
    near_result = select_fixed_blueprint_envelope(
        blueprint,
        [near],
        raw_guard=raw_guard,
    )
    best = candidate("best", "f" * 63 + "0", 0.5)
    tied = candidate("digest_winner", "0" * 64, 0.5 + 0.5 * raw_guard)
    tie_forward = select_fixed_blueprint_envelope(
        blueprint,
        [best, tied],
        raw_guard=raw_guard,
    )
    tie_reverse = select_fixed_blueprint_envelope(
        blueprint,
        [tied, best],
        raw_guard=raw_guard,
    )
    violating_gains = [0.15] * 6
    violating_gains[2] = 1.0 / 6.0 + 2.0 * raw_guard
    violating = candidate("violating", "1" * 64, 0.1, violating_gains)
    cap_result = select_fixed_blueprint_envelope(
        blueprint,
        [violating, best],
        raw_guard=raw_guard,
    )
    passed = (
        near_result["selected_candidate_id"] == "blueprint_average64"
        and near_result["blueprint_abstention"]
        and tie_forward["selected_candidate_id"] == "digest_winner"
        and tie_reverse["selected_candidate_id"] == "digest_winner"
        and cap_result["selected_candidate_id"] == "best"
        and cap_result["infeasible_candidate_count"] == 1
    )
    return {
        "passed": passed,
        "below_guard_selected": near_result["selected_candidate_id"],
        "forward_tie_selected": tie_forward["selected_candidate_id"],
        "reverse_tie_selected": tie_reverse["selected_candidate_id"],
        "cap_control_selected": cap_result["selected_candidate_id"],
        "cap_control_infeasible_candidates": cap_result[
            "infeasible_candidate_count"
        ],
    }


def _candidate_diagnostic(
    blueprint: dict[str, Any],
    candidate: dict[str, Any],
    *,
    raw_guard: float,
) -> dict[str, Any]:
    cap = _cap_diagnostics(blueprint, candidate, raw_guard=raw_guard)
    return {
        "candidate_id": candidate["candidate_id"],
        "aliases": candidate["aliases"],
        "source_refs": candidate["source_refs"],
        "policy_sha256": candidate["quality"]["policy_sha256"],
        "nash_conv": candidate["quality"]["nash_conv"],
        "normalized_nash_conv": candidate["quality"]["normalized_nash_conv"],
        "normalized_reduction_from_blueprint": (
            float(blueprint["quality"]["normalized_nash_conv"])
            - float(candidate["quality"]["normalized_nash_conv"])
        ),
        "deviation_gains": candidate["quality"]["deviation_gains"],
        **cap,
    }


def _pool_result(
    blueprint: dict[str, Any],
    candidates: list[dict[str, Any]],
    *,
    raw_guard: float,
    seed: int,
    seeded_permutation_count: int,
) -> dict[str, Any]:
    orders = _order_rows(
        candidates,
        seed=seed,
        seeded_permutation_count=seeded_permutation_count,
    )
    fixed_rows = []
    legacy_rows = []
    for order_id, ordered in orders:
        order_digest = _json_digest(
            [candidate["quality"]["policy_sha256"] for candidate in ordered]
        )
        fixed = replay_fixed_blueprint_stream(
            blueprint,
            ordered,
            raw_guard=raw_guard,
        )
        legacy = replay_incumbent_relative_pareto(
            blueprint,
            ordered,
            raw_guard=raw_guard,
        )
        fixed_rows.append(
            {
                "order_id": order_id,
                "order_digest": order_digest,
                **fixed,
            }
        )
        legacy_rows.append(
            {
                "order_id": order_id,
                "order_digest": order_digest,
                "final_candidate_id": legacy["final_candidate_id"],
                "final_policy_sha256": legacy["final_policy_sha256"],
                "final_normalized_nash_conv": legacy[
                    "final_normalized_nash_conv"
                ],
            }
        )
    fixed_digests = sorted(
        {row["selected_policy_sha256"] for row in fixed_rows}
    )
    legacy_digests = sorted({row["final_policy_sha256"] for row in legacy_rows})
    return {
        "candidate_count": len(candidates),
        "candidate_rows": [
            _candidate_diagnostic(
                blueprint,
                candidate,
                raw_guard=raw_guard,
            )
            for candidate in candidates
        ],
        "order_variant_count": len(orders),
        "fixed_envelope": {
            "canonical": fixed_rows[0],
            "order_invariant": len(fixed_digests) == 1,
            "unique_final_policy_digests": fixed_digests,
            "order_rows": fixed_rows,
        },
        "incumbent_relative_pareto": {
            "canonical": legacy_rows[0],
            "order_invariant": len(legacy_digests) == 1,
            "unique_final_policy_digests": legacy_digests,
            "order_rows": legacy_rows,
        },
    }


def run_h32_acceptance_semantics_replay(config: dict[str, Any]) -> dict[str, Any]:
    """Run the zero-evaluation ADR-0105 acceptance-semantics replay."""

    started = time.perf_counter()
    parsed = parse_h32_acceptance_semantics_config(config)
    raw_guard = parsed["payoff_span"] * parsed["acceptance_guard_normalized"]
    artifacts = {
        source_id: json.loads(path.read_text(encoding="utf-8"))
        for source_id, path in _SOURCE_PATHS.items()
    }
    source_hash_identity = all(
        _sha256(_SOURCE_PATHS[source_id])
        == parsed["expected_source_sha256"][source_id]
        for source_id in parsed["source_order"]
    )
    source_status_identity = all(
        artifact["status"] == "frozen_audit_executed"
        and bool(artifact["gates"]["passed"])
        for artifact in artifacts.values()
    )
    target_maps = {
        source_id: _artifact_targets(artifact)
        for source_id, artifact in artifacts.items()
    }

    target_rows: list[dict[str, Any]] = []
    maximum_blueprint_error = 0.0
    maximum_duplicate_error = 0.0
    maximum_quality_sum_error = 0.0
    maximum_quality_normalization_error = 0.0
    descriptor_identity = True
    blueprint_identity = True
    frozen_legacy_identity = True
    source_target_rows = sum(len(rows) for rows in target_maps.values())

    for family in parsed["range_families"]:
        for shift in parsed["target_shifts"]:
            key = (family, shift)
            source_targets = {
                source_id: target_maps[source_id][key]
                for source_id in parsed["source_order"]
            }
            descriptors = [
                canonical_target_descriptor(target["target_descriptor"])
                for target in source_targets.values()
            ]
            descriptor_digests = [_json_digest(row) for row in descriptors]
            target_descriptor_identity = len(set(descriptor_digests)) == 1
            descriptor_identity = descriptor_identity and target_descriptor_identity

            blueprint_views = [
                _quality_view(target["blueprint_quality"], players=parsed["players"])
                for target in source_targets.values()
            ]
            for view in blueprint_views[1:]:
                error = _maximum_quality_error(blueprint_views[0], view)
                maximum_blueprint_error = max(maximum_blueprint_error, error)
                blueprint_identity = blueprint_identity and error <= 1e-15
            blueprint = {
                "candidate_id": "blueprint_average64",
                "aliases": ["blueprint_average64"],
                "source_refs": [f"{source_id}:blueprint" for source_id in parsed["source_order"]],
                "quality": blueprint_views[0],
            }

            source_candidate_views: dict[str, list[dict[str, Any]]] = {}
            all_measured_views: list[dict[str, Any]] = []
            pool_merge_rows: dict[str, dict[str, Any]] = {}
            recorded_legacy: dict[str, dict[str, Any]] = {}
            for source_id in parsed["source_order"]:
                target = source_targets[source_id]
                by_id = _candidate_rows_by_id(target)
                stream_ids = _source_stream_ids(source_id, target)
                views = [
                    _candidate_view(
                        by_id[candidate_id],
                        source_id=source_id,
                        players=parsed["players"],
                    )
                    for candidate_id in stream_ids
                ]
                source_candidate_views[source_id] = views
                all_measured_views.extend(
                    _candidate_view(
                        candidate,
                        source_id=source_id,
                        players=parsed["players"],
                    )
                    for candidate in target["candidates"]
                )
                recorded_legacy[source_id] = _source_recorded_legacy(
                    source_id,
                    target,
                )

            pools: dict[str, list[dict[str, Any]]] = {}
            for source_id, pool_id in (
                ("adr0099", "adr0099_frozen_stream"),
                ("adr0101", "adr0101_full_interleaved"),
                ("adr0103", "adr0103_interpolation"),
            ):
                merged, merge_row = merge_policy_candidates(
                    source_candidate_views[source_id],
                    maximum_quality_error=parsed["gates"][
                        "maximum_duplicate_quality_error"
                    ],
                )
                pools[pool_id] = merged
                pool_merge_rows[pool_id] = merge_row
            union, union_merge = merge_policy_candidates(
                all_measured_views,
                maximum_quality_error=parsed["gates"][
                    "maximum_duplicate_quality_error"
                ],
            )
            pools["full_measured_union"] = union
            pool_merge_rows["full_measured_union"] = union_merge
            maximum_duplicate_error = max(
                maximum_duplicate_error,
                *(row["maximum_duplicate_quality_error"] for row in pool_merge_rows.values()),
            )

            all_quality_rows = [blueprint["quality"]]
            all_quality_rows.extend(candidate["quality"] for candidate in union)
            for quality in all_quality_rows:
                maximum_quality_sum_error = max(
                    maximum_quality_sum_error,
                    abs(sum(quality["deviation_gains"]) - quality["nash_conv"]),
                )
                maximum_quality_normalization_error = max(
                    maximum_quality_normalization_error,
                    abs(
                        quality["nash_conv"] / parsed["payoff_span"]
                        - quality["normalized_nash_conv"]
                    ),
                )

            pool_results: dict[str, dict[str, Any]] = {}
            for pool_index, pool_id in enumerate(parsed["pool_order"]):
                pool_result = _pool_result(
                    blueprint,
                    pools[pool_id],
                    raw_guard=raw_guard,
                    seed=parsed["seed"] + 1000 * len(target_rows) + 100 * pool_index,
                    seeded_permutation_count=parsed["seeded_permutation_count"],
                )
                pool_result["merge"] = pool_merge_rows[pool_id]
                pool_results[pool_id] = pool_result

            for source_id, pool_id in (
                ("adr0099", "adr0099_frozen_stream"),
                ("adr0101", "adr0101_full_interleaved"),
                ("adr0103", "adr0103_interpolation"),
            ):
                replay = pool_results[pool_id]["incumbent_relative_pareto"][
                    "canonical"
                ]
                recorded = recorded_legacy[source_id]
                identity = (
                    replay["final_candidate_id"] == recorded["candidate_id"]
                    and abs(
                        replay["final_normalized_nash_conv"]
                        - recorded["normalized_nash_conv"]
                    )
                    <= 1e-15
                )
                pool_results[pool_id]["frozen_legacy_replay_identity"] = identity
                pool_results[pool_id]["recorded_legacy"] = recorded
                frozen_legacy_identity = frozen_legacy_identity and identity

            target_rows.append(
                {
                    "range_family": family,
                    "target_shift": shift,
                    "target_descriptor_sha256": descriptor_digests[0],
                    "target_descriptor_identity": target_descriptor_identity,
                    "blueprint": blueprint["quality"],
                    "blueprint_cap_deviation_gains": [
                        value + raw_guard
                        for value in blueprint["quality"]["deviation_gains"]
                    ],
                    "pools": pool_results,
                }
            )

    fixed_order_invariance = all(
        pool["fixed_envelope"]["order_invariant"]
        for target in target_rows
        for pool in target["pools"].values()
    )
    selected_cap_compliance = all(
        not pool["fixed_envelope"]["canonical"]["selected_violating_seats"]
        for target in target_rows
        for pool in target["pools"].values()
    )
    union_counts = [
        target["pools"]["full_measured_union"]["candidate_count"]
        for target in target_rows
    ]
    order_counts = [
        pool["order_variant_count"]
        for target in target_rows
        for pool in target["pools"].values()
    ]
    source_stream_counts = {
        pool_id: sorted(
            {
                target["pools"][pool_id]["candidate_count"]
                for target in target_rows
            }
        )
        for pool_id in parsed["gates"][
            "expected_source_stream_candidates_per_target"
        ]
    }
    tie_semantics = _synthetic_tie_semantics(raw_guard)
    new_strategy_evaluations = 0
    elapsed = time.perf_counter() - started

    gates = {
        "source_hash_identity": source_hash_identity
        == parsed["gates"]["require_source_hash_identity"],
        "source_status_identity": source_status_identity
        == parsed["gates"]["require_source_status_identity"],
        "target_rows": len(target_rows) == parsed["gates"]["expected_target_rows"],
        "source_target_rows": source_target_rows
        == parsed["gates"]["expected_source_target_rows"],
        "source_stream_candidate_counts": all(
            source_stream_counts[pool_id] == [expected]
            for pool_id, expected in parsed["gates"][
                "expected_source_stream_candidates_per_target"
            ].items()
        ),
        "union_candidate_counts": union_counts
        == [parsed["gates"]["expected_union_candidates_per_target"]]
        * len(target_rows),
        "order_variant_counts": all(
            count == parsed["gates"]["expected_order_variants_per_pool"]
            for count in order_counts
        ),
        "target_descriptor_identity": descriptor_identity
        == parsed["gates"]["require_target_descriptor_identity"],
        "blueprint_identity": blueprint_identity
        == parsed["gates"]["require_blueprint_identity"],
        "duplicate_quality_identity": maximum_duplicate_error
        <= parsed["gates"]["maximum_duplicate_quality_error"],
        "quality_sum_identity": maximum_quality_sum_error
        <= parsed["gates"]["maximum_quality_sum_error"],
        "quality_normalization_identity": maximum_quality_normalization_error
        <= parsed["gates"]["maximum_quality_normalization_error"],
        "frozen_legacy_replay_identity": frozen_legacy_identity
        == parsed["gates"]["require_frozen_legacy_replay_identity"],
        "fixed_envelope_order_invariance": fixed_order_invariance
        == parsed["gates"]["require_fixed_envelope_order_invariance"],
        "selected_cap_compliance": selected_cap_compliance
        == parsed["gates"]["require_selected_cap_compliance"],
        "synthetic_tie_semantics": tie_semantics["passed"]
        == parsed["gates"]["require_synthetic_tie_semantics"],
        "zero_new_strategy_evaluations": new_strategy_evaluations
        == parsed["gates"]["expected_new_strategy_evaluations"],
        "total_audit_seconds": elapsed
        <= parsed["gates"]["maximum_total_audit_seconds"],
    }
    gates["passed"] = all(gates.values())

    union_blueprint_total = sum(
        target["blueprint"]["normalized_nash_conv"] for target in target_rows
    )
    union_fixed_total = sum(
        target["pools"]["full_measured_union"]["fixed_envelope"]["canonical"][
            "selected_normalized_nash_conv"
        ]
        for target in target_rows
    )
    union_legacy_total = sum(
        target["pools"]["full_measured_union"]["incumbent_relative_pareto"][
            "canonical"
        ]["final_normalized_nash_conv"]
        for target in target_rows
    )
    legacy_path_dependent_rows = sum(
        not pool["incumbent_relative_pareto"]["order_invariant"]
        for target in target_rows
        for pool in target["pools"].values()
    )
    fixed_selections = [
        {
            "range_family": target["range_family"],
            "target_shift": target["target_shift"],
            "candidate_id": target["pools"]["full_measured_union"][
                "fixed_envelope"
            ]["canonical"]["selected_candidate_id"],
            "policy_sha256": target["pools"]["full_measured_union"][
                "fixed_envelope"
            ]["canonical"]["selected_policy_sha256"],
            "normalized_nash_conv": target["pools"]["full_measured_union"][
                "fixed_envelope"
            ]["canonical"]["selected_normalized_nash_conv"],
        }
        for target in target_rows
    ]

    return {
        "schema_version": 1,
        "status": "frozen_semantics_audit_executed",
        "experiment_type": "h32_zero_evaluation_acceptance_semantics_replay",
        "config": config,
        "config_sha256": _sha256(_CONFIG),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {
            source_id: _sha256(path) for source_id, path in _SOURCE_PATHS.items()
        },
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "counts": {
            "target_rows": len(target_rows),
            "source_target_rows": source_target_rows,
            "new_strategy_evaluations": new_strategy_evaluations,
            "pool_rows": len(target_rows) * len(parsed["pool_order"]),
            "order_rows": len(order_counts)
            * parsed["gates"]["expected_order_variants_per_pool"],
            "legacy_path_dependent_pool_rows": legacy_path_dependent_rows,
        },
        "numeric_diagnostics": {
            "raw_guard": raw_guard,
            "maximum_blueprint_error": maximum_blueprint_error,
            "maximum_duplicate_quality_error": maximum_duplicate_error,
            "maximum_quality_sum_error": maximum_quality_sum_error,
            "maximum_quality_normalization_error": (
                maximum_quality_normalization_error
            ),
        },
        "synthetic_tie_semantics": tie_semantics,
        "targets": target_rows,
        "aggregate": {
            "full_union_blueprint_total_normalized_nash_conv": (
                union_blueprint_total
            ),
            "full_union_fixed_envelope_total_normalized_nash_conv": (
                union_fixed_total
            ),
            "full_union_legacy_canonical_total_normalized_nash_conv": (
                union_legacy_total
            ),
            "full_union_fixed_envelope_reduction_from_blueprint": (
                union_blueprint_total - union_fixed_total
            ),
            "full_union_fixed_envelope_reduction_over_legacy_canonical": (
                union_legacy_total - union_fixed_total
            ),
            "full_union_fixed_selections": fixed_selections,
            "fixed_envelope_order_invariant_all_pool_rows": (
                fixed_order_invariance
            ),
            "fixed_envelope_selected_cap_compliance_all_pool_rows": (
                selected_cap_compliance
            ),
            "legacy_path_dependent_pool_rows": legacy_path_dependent_rows,
        },
        "gates": gates,
        "timing": {"total_audit_seconds": elapsed},
        "limitations": [
            "This is a post-label semantics audit; it creates no new strategy-quality evidence.",
            "Per-seat blueprint caps certify unilateral deviations, not coalitions or collusion.",
            "The selector is a batch or observed-set contract; it may replace a prior incumbent while remaining inside the fixed blueprint envelope.",
            "All vectors come from one board, one bet size, equal stacks, and four generated target beliefs.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = run_h32_acceptance_semantics_replay(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "h32 acceptance semantics replay: "
        f"passed={result['gates']['passed']} "
        f"targets={result['counts']['target_rows']} "
        f"new_evaluations={result['counts']['new_strategy_evaluations']} "
        f"legacy_path_dependent={result['counts']['legacy_path_dependent_pool_rows']} "
        f"seconds={result['timing']['total_audit_seconds']:.3f}"
    )
    return 0 if result["gates"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
