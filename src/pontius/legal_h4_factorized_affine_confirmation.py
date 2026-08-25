"""Exclusive untouched legal-h4 factorized-affine confirmation owner.

The ADR-0360 population is opened only inside this one-shot terminal.  Every
context receives the frozen three regret vertices and one independently
audited row-growth proposal.  Each direction is evaluated for both players by
the exact fan plus factorized-face consumer, and every raw row needed for
independent reconstruction is retained.  No action or strategy-quality label
is emitted.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Mapping

from .complete_factorized_affine_evidence import (
    canonical_sha256,
    complete_factorized_affine_record,
    complete_factorized_affine_record_checks,
)
from .factorized_tie_aware_affine import (
    FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE,
    FAIL_CLOSED_SINGLE_TAPE,
    V2_SINGLE_TAPE,
    build_factorized_tie_aware_affine_section,
)
from .legal_decision_spine_v2 import public_betting_state_sha256
from .legal_h4_factorized_affine_confirmation_directions import (
    REGRET_PUBLIC_HISTORIES,
    RowGrowthDirectionRejected,
    compile_legal_h4_confirmation_directions,
    direction_descriptor,
)
from .legal_h4_factorized_affine_confirmation_population import (
    ADR0360_CONFIRMATION_PROTOCOL,
    ADR0360_CONFIRMATION_PROTOCOL_SHA256,
    build_adr0360_confirmation_population,
    legal_h4_confirmation_source_policy,
    policy_sha256,
)
from .legal_h4_factorized_affine_confirmation_population_seal import (
    ADR0360_CONFIRMATION_CANONICAL_BYTES,
    ADR0360_CONFIRMATION_CONTEXT_SHA256S,
    ADR0360_CONFIRMATION_GAME_PROVENANCE_SHA256S,
    ADR0360_CONFIRMATION_POLICY_SHA256S,
    ADR0360_CONFIRMATION_POPULATION_SHA256,
    ADR0360_CONFIRMATION_PUBLIC_STATE_SHA256,
)
from .runner_harness import assemble_environment, finalize_gates, serialize_result
from .runner_harness_v2 import load_config


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT
    / "experiments/configs/legal-h4-factorized-affine-confirmation-v1.json"
)
_OUTPUT = (
    _ROOT
    / "experiments/results/legal-h4-factorized-affine-confirmation-v1.json"
)
_IMPLEMENTATION = Path(__file__)
_PATHS = {
    "expected_parent_decision_sha256": _ROOT
    / "docs/decisions/ADR-0360-source-seal-the-fresh-legal-h4-factorized-affine-confirmation-population.md",
    "expected_population_source_sha256": _ROOT
    / "src/pontius/legal_h4_factorized_affine_confirmation_population.py",
    "expected_population_seal_sha256": _ROOT
    / "src/pontius/legal_h4_factorized_affine_confirmation_population_seal.py",
    "expected_population_controls_sha256": _ROOT
    / "tests/test_legal_h4_factorized_affine_confirmation_population.py",
    "expected_direction_compiler_sha256": _ROOT
    / "src/pontius/legal_h4_factorized_affine_confirmation_directions.py",
    "expected_direction_controls_sha256": _ROOT
    / "tests/test_legal_h4_factorized_affine_confirmation_directions.py",
    "expected_complete_evidence_sha256": _ROOT
    / "src/pontius/complete_factorized_affine_evidence.py",
    "expected_complete_evidence_controls_sha256": _ROOT
    / "tests/test_complete_factorized_affine_evidence.py",
    "expected_factorized_affine_sha256": _ROOT
    / "src/pontius/factorized_tie_aware_affine.py",
    "expected_factorized_affine_seal_sha256": _ROOT
    / "src/pontius/factorized_tie_aware_affine_seal.py",
    "expected_factorized_affine_controls_sha256": _ROOT
    / "tests/test_factorized_tie_aware_affine.py",
    "expected_tie_conformance_sha256": _ROOT
    / "src/pontius/tie_semantics_conformance_v2.py",
    "expected_tie_conformance_controls_sha256": _ROOT
    / "tests/test_tie_semantics_conformance_v2.py",
    "expected_directional_face_oracle_sha256": _ROOT
    / "src/pontius/exact_directional_face_oracle.py",
    "expected_directional_face_seal_sha256": _ROOT
    / "src/pontius/exact_directional_face_oracle_seal.py",
    "expected_exact_fan_sha256": _ROOT / "src/pontius/exact_selector_fan.py",
    "expected_exact_selector_oracle_sha256": _ROOT
    / "src/pontius/exact_selector_window_oracle.py",
    "expected_exact_sequence_oracle_sha256": _ROOT
    / "src/pontius/exact_sequence_form_coefficient_oracle.py",
    "expected_selector_window_v2_sha256": _ROOT
    / "src/pontius/selector_window_v2.py",
    "expected_selector_window_sha256": _ROOT / "src/pontius/selector_window.py",
    "expected_cfr_sha256": _ROOT / "src/pontius/cfr.py",
    "expected_row_growth_audit_sha256": _ROOT
    / "src/pontius/one_seat_row_growth_audit.py",
    "expected_generation_primitive_sha256": _ROOT
    / "src/pontius/one_seat_convex_generation.py",
    "expected_lp_sha256": _ROOT / "src/pontius/linear_program.py",
    "expected_evaluation_sha256": _ROOT / "src/pontius/evaluation.py",
    "expected_game_sha256": _ROOT / "src/pontius/game.py",
    "expected_legal_kernel_sha256": _ROOT / "src/pontius/no_limit_betting.py",
    "expected_legal_game_sha256": _ROOT
    / "src/pontius/legal_river_continuation.py",
    "expected_legal_spine_sha256": _ROOT
    / "src/pontius/legal_decision_spine_v2.py",
    "expected_river_sha256": _ROOT / "src/pontius/river.py",
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_strict_loader_sha256": _ROOT / "src/pontius/runner_harness_v2.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _ROOT
    / "tests/test_legal_h4_factorized_affine_confirmation.py",
}

_TARGET_OUTCOME_KEYS = frozenset(
    {
        "active_cell_rows",
        "complete_section_sha256",
        "direction_generation_seconds",
        "endpoint_policy_sha256",
        "exact_source_ties",
        "fan_cells",
        "fan_points",
        "fan_segments",
        "maximum_reachable_support_cardinality",
        "maximum_total_function_cardinality",
        "mode",
        "mode_counts",
        "piece_counts",
        "row_growth_semantic_sha256",
        "section_subject_seconds",
        "selector_window_scale_limits",
        "source_face_cardinality",
        "subject_seconds",
    }
)


@dataclass(frozen=True, slots=True)
class ConfirmationRejected(RuntimeError):
    """Typed first-terminal scientific rejection with partial evidence."""

    reason: str
    record: Mapping[str, object]

    def __str__(self) -> str:
        return self.reason


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _canonical_lf_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required confirmation source is absent: {path}")
    canonical = path.read_bytes().replace(bytes((13, 10)), bytes((10,)))
    return hashlib.sha256(canonical).hexdigest()


def _strict_git_metadata() -> dict[str, object]:
    def checked(*arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            cwd=_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10.0,
        )
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"strict Git metadata failed: {message}")
        return result.stdout.strip()

    commit = checked("rev-parse", "HEAD")
    status = checked("status", "--porcelain=v1", "--untracked-files=all")
    return {"commit": commit, "dirty": bool(status), "strict_status": True}


def _contains_outcome_key(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key) in _TARGET_OUTCOME_KEYS or _contains_outcome_key(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_outcome_key(item) for item in value)
    return False


def _parse_config(config: Mapping[str, Any]) -> dict[str, Any]:
    plain = _plain(config)
    expected = {
        "schema_version",
        "evidence_stage",
        "hash_semantics",
        "expected_parent_protocol_sha256",
        "expected_population_sha256",
        "expected_population_canonical_bytes",
        "expected_context_sha256s",
        "expected_policy_sha256s",
        "expected_game_provenance_sha256s",
        "expected_public_state_sha256",
        *_PATHS,
        "acting_player",
        "target_players",
        "direction_classes_in_order",
        "direction_regret_public_histories_in_order",
        "row_growth_guard",
        "row_growth_max_iterations",
        "row_growth_tolerance",
        "selector_margin_allowance",
        "maximum_tree_nodes",
        "maximum_fan_pieces",
        "ray_authority",
        "point_authority",
        "identity_authority",
        "reachable_identity_role",
        "epigraph_orientation",
        "direction_generation_stage",
        "section_subject_wall_semantics",
        "subject_wall_semantics",
        "campaign_wall_semantics",
        "result_path_lifecycle",
        "failure_interpretation",
        "claims_policy",
        "gates",
    }
    if set(plain) != expected:
        raise ValueError("legal h4 confirmation config fields differ")
    for field, path in _PATHS.items():
        if plain[field] != _canonical_lf_sha256(path):
            raise ValueError(f"legal h4 confirmation provenance differs: {field}")

    protocol = dict(ADR0360_CONFIRMATION_PROTOCOL)
    frozen = {
        "schema_version": "legal-h4-factorized-affine-confirmation-config-v1",
        "evidence_stage": (
            "preregistered_after_adr0360_before_any_fresh_confirmation_target_call"
        ),
        "hash_semantics": "canonical_lf_sha256_for_all_bound_text_sources",
        "expected_parent_protocol_sha256": ADR0360_CONFIRMATION_PROTOCOL_SHA256,
        "expected_population_sha256": ADR0360_CONFIRMATION_POPULATION_SHA256,
        "expected_population_canonical_bytes": ADR0360_CONFIRMATION_CANONICAL_BYTES,
        "expected_context_sha256s": list(ADR0360_CONFIRMATION_CONTEXT_SHA256S),
        "expected_policy_sha256s": list(ADR0360_CONFIRMATION_POLICY_SHA256S),
        "expected_game_provenance_sha256s": list(
            ADR0360_CONFIRMATION_GAME_PROVENANCE_SHA256S
        ),
        "expected_public_state_sha256": ADR0360_CONFIRMATION_PUBLIC_STATE_SHA256,
        "acting_player": protocol["acting_player"],
        "target_players": list(protocol["target_players"]),
        "direction_classes_in_order": list(protocol["direction_classes_in_order"]),
        "direction_regret_public_histories_in_order": list(
            protocol["direction_regret_public_histories_in_order"]
        ),
        "row_growth_guard": protocol["row_growth_guard"],
        "row_growth_max_iterations": protocol["row_growth_max_iterations"],
        "row_growth_tolerance": protocol["row_growth_tolerance"],
        "selector_margin_allowance": protocol["selector_margin_allowance"],
        "maximum_tree_nodes": protocol["maximum_explicit_tree_nodes"],
        "maximum_fan_pieces": protocol["fan_piece_guard"],
        "ray_authority": protocol["ray_authority"],
        "point_authority": protocol["point_authority"],
        "identity_authority": protocol["identity_authority"],
        "reachable_identity_role": "reporting_only",
        "epigraph_orientation": "z_greater_than_or_equal_to_every_row",
        "direction_generation_stage": protocol["direction_generation_stage"],
        "section_subject_wall_semantics": (
            "one_live_factorized_section_build_only_excluding_record_checks_and_"
            "serialization"
        ),
        "subject_wall_semantics": (
            "sum_of_exactly_32_live_factorized_section_builds_only"
        ),
        "campaign_wall_semantics": (
            "population_rebind_through_complete_scientific_payload_and_gate_"
            "materialization_excluding_config_git_result_render_fsync_and_process_"
            "overhead"
        ),
        "result_path_lifecycle": protocol["result_path_policy"],
        "failure_interpretation": protocol["failure_interpretation"],
        "claims_policy": protocol["claims_policy"],
    }
    for field, value in frozen.items():
        if plain[field] != value:
            raise ValueError(f"legal h4 confirmation field differs: {field}")

    expected_gates = {
        "expected_contexts": 4,
        "expected_directions_per_context": 4,
        "expected_regret_directions_per_context": 3,
        "expected_row_growth_directions_per_context": 1,
        "expected_targets_per_direction": 2,
        "expected_sections": 32,
        "maximum_section_subject_seconds": 60.0,
        "maximum_subject_seconds": 360.0,
        "maximum_campaign_seconds": 600.0,
        "maximum_result_bytes": 8_388_608,
        "require_clean_git_state": True,
        "require_population_identity": True,
        "require_context_identity": True,
        "require_direction_inventory": True,
        "require_row_growth_exact_acceptance": True,
        "require_complete_section_evidence": True,
        "require_typed_dispatch": True,
        "require_exact_authorities": True,
        "require_dual_cardinality_semantics": True,
        "require_zero_materialized_tapes": True,
        "require_all_or_nothing_coordinates": True,
        "require_no_target_outcome_gate": True,
        "require_zero_actions_and_quality_rows": True,
        "require_finite": True,
    }
    if plain["gates"] != expected_gates:
        raise ValueError("legal h4 confirmation gates differ")
    if _contains_outcome_key(plain):
        raise ValueError("legal h4 confirmation target outcome entered its config")
    return plain


def _finite_tree(value: object) -> bool:
    if isinstance(value, float):
        return isfinite(value)
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return True


def _typed_dispatch(record: Mapping[str, object]) -> bool:
    source_face = record.get("source_face")
    if not isinstance(source_face, Mapping):
        return False
    cardinality = source_face.get("total_function_cardinality")
    mode = record.get("mode")
    window = record.get("single_tape_window")
    if not isinstance(cardinality, int) or isinstance(cardinality, bool):
        return False
    if cardinality > 1:
        return mode == FACTOR_TIE_AWARE_MAXIMUM_ENVELOPE and window is None
    return cardinality == 1 and (
        (mode == V2_SINGLE_TAPE and isinstance(window, Mapping))
        or (mode == FAIL_CLOSED_SINGLE_TAPE and isinstance(window, Mapping))
    )


def _rejection(
    reason: str,
    *,
    contexts: list[dict[str, object]],
    coordinate: Mapping[str, object] | None = None,
    evidence: Mapping[str, object] | None = None,
) -> ConfirmationRejected:
    record: dict[str, object] = {
        "completed_contexts": contexts,
        "coordinate": None if coordinate is None else dict(coordinate),
    }
    if evidence is not None:
        record["evidence"] = dict(evidence)
    return ConfirmationRejected(reason, record)


def _execute_confirmation(
    parsed: Mapping[str, Any],
    *,
    git: Mapping[str, object],
) -> dict[str, Any]:
    campaign_start = time.perf_counter()
    gates = parsed["gates"]
    assert isinstance(gates, Mapping)
    population = build_adr0360_confirmation_population()
    population_identity = (
        population.digest == parsed["expected_population_sha256"]
        and len(population.canonical_bytes)
        == parsed["expected_population_canonical_bytes"]
        and len(population.contexts) == gates["expected_contexts"]
        and tuple(context.semantic_digest for context in population.contexts)
        == tuple(parsed["expected_context_sha256s"])
    )
    if not population_identity:
        raise _rejection("confirmation population identity differs", contexts=[])

    context_records: list[dict[str, object]] = []
    section_coordinates: list[tuple[str, str, int]] = []
    subject_seconds = 0.0
    all_context_identity = True
    all_direction_inventory = True
    all_row_growth_acceptance = True
    all_section_evidence = True
    all_typed_dispatch = True
    all_exact_authorities = True
    all_dual_cardinality = True
    all_zero_materialization = True
    mode_counts: Counter[str] = Counter()
    piece_counts: list[int] = []
    selector_window_scale_limits: list[float] = []
    maximum_total_cardinality = 0
    maximum_reachable_cardinality = 0

    for context_ordinal, context in enumerate(population.contexts):
        game = context.build_game()
        source = legal_h4_confirmation_source_policy(context, game)
        context_identity = (
            context.semantic_digest == parsed["expected_context_sha256s"][context_ordinal]
            and policy_sha256(source)
            == parsed["expected_policy_sha256s"][context_ordinal]
            and game.provenance_digest
            == parsed["expected_game_provenance_sha256s"][context_ordinal]
            and public_betting_state_sha256(game.base_state)
            == parsed["expected_public_state_sha256"]
        )
        all_context_identity &= context_identity
        if not context_identity:
            raise _rejection(
                "confirmation context identity differs",
                contexts=context_records,
                coordinate={"context_id": context.context_id},
            )

        direction_start = time.perf_counter()
        try:
            compilation = compile_legal_h4_confirmation_directions(
                game,
                source,
                context_id=context.context_id,
                acting_player=int(parsed["acting_player"]),
                guard=float(parsed["row_growth_guard"]),
                max_iterations=int(parsed["row_growth_max_iterations"]),
                tolerance=float(parsed["row_growth_tolerance"]),
            )
        except RowGrowthDirectionRejected as error:
            raise _rejection(
                "confirmation row-growth direction rejected",
                contexts=context_records,
                coordinate={"context_id": context.context_id},
                evidence=error.record,
            ) from error
        direction_seconds = time.perf_counter() - direction_start
        descriptors = tuple(
            direction_descriptor(direction) for direction in compilation.directions
        )
        direction_class_counts = Counter(
            str(descriptor["direction_class"]) for descriptor in descriptors
        )
        direction_inventory = (
            len(descriptors) == gates["expected_directions_per_context"]
            and tuple(
                descriptor["direction_class"] for descriptor in descriptors
            )
            == tuple(parsed["direction_classes_in_order"])
            and tuple(
                descriptor["changed_public_histories"][0]
                for descriptor in descriptors[:3]
            )
            == tuple(parsed["direction_regret_public_histories_in_order"])
            == REGRET_PUBLIC_HISTORIES
            and len({str(descriptor["label"]) for descriptor in descriptors}) == 4
            and len(
                {str(descriptor["endpoint_policy_sha256"]) for descriptor in descriptors}
            )
            == 4
            and direction_class_counts[
                "one_step_dcfr_regret_vertex_per_public_history"
            ]
            == gates["expected_regret_directions_per_context"]
            and direction_class_counts["converged_one_seat_row_growth_proposal"]
            == gates["expected_row_growth_directions_per_context"]
        )
        all_direction_inventory &= direction_inventory
        row_growth_gates = compilation.row_growth.get("gates")
        row_growth_acceptance = (
            isinstance(row_growth_gates, Mapping)
            and compilation.row_growth.get("passed") is True
            and all(value is True for value in row_growth_gates.values())
        )
        all_row_growth_acceptance &= row_growth_acceptance
        if not direction_inventory or not row_growth_acceptance:
            raise _rejection(
                "confirmation direction family failed its frozen acceptance",
                contexts=context_records,
                coordinate={"context_id": context.context_id},
                evidence={
                    "direction_inventory": direction_inventory,
                    "descriptors": list(descriptors),
                    "row_growth": dict(compilation.row_growth),
                },
            )

        context_record: dict[str, object] = {
            "candidate_ordinal": context.candidate_ordinal,
            "context_id": context.context_id,
            "direction_generation_seconds": direction_seconds,
            "game_provenance_sha256": game.provenance_digest,
            "game_structural_sha256": game.structural_digest,
            "public_state_sha256": public_betting_state_sha256(game.base_state),
            "row_growth": dict(compilation.row_growth),
            "semantic_sha256": context.semantic_digest,
            "source_policy_sha256": policy_sha256(source),
            "directions": [],
        }
        direction_records = context_record["directions"]
        assert isinstance(direction_records, list)
        for direction in compilation.directions:
            descriptor = direction_descriptor(direction)
            direction_record: dict[str, object] = {
                **descriptor,
                "targets": [],
            }
            targets = direction_record["targets"]
            assert isinstance(targets, list)
            for target_player in parsed["target_players"]:
                target = int(target_player)
                coordinate = {
                    "context_id": context.context_id,
                    "direction_label": direction.label,
                    "target_player": target,
                }
                section_start = time.perf_counter()
                result = build_factorized_tie_aware_affine_section(
                    game,
                    source,
                    direction.endpoint_policy,
                    acting_player=int(parsed["acting_player"]),
                    target_player=target,
                    selector_margin_allowance=float(
                        parsed["selector_margin_allowance"]
                    ),
                    maximum_fan_pieces=int(parsed["maximum_fan_pieces"]),
                    maximum_tree_nodes=int(parsed["maximum_tree_nodes"]),
                )
                section_seconds = time.perf_counter() - section_start
                subject_seconds += section_seconds
                evidence = complete_factorized_affine_record(result)
                evidence_checks = complete_factorized_affine_record_checks(
                    result, evidence
                )
                typed_dispatch = _typed_dispatch(evidence)
                exact_authorities = (
                    evidence.get("ray_authority") == parsed["ray_authority"]
                    and evidence.get("point_authority") == parsed["point_authority"]
                    and evidence.get("certificate_identity_authority")
                    == parsed["identity_authority"]
                    and evidence.get("reachable_identity_role")
                    == parsed["reachable_identity_role"]
                    and evidence.get("epigraph_orientation")
                    == parsed["epigraph_orientation"]
                )
                section_pass = (
                    all(evidence_checks.values())
                    and typed_dispatch
                    and exact_authorities
                    and section_seconds
                    <= gates["maximum_section_subject_seconds"]
                )
                target_record = {
                    **coordinate,
                    "complete_evidence": evidence,
                    "complete_evidence_checks": evidence_checks,
                    "exact_authorities": exact_authorities,
                    "section_passed": section_pass,
                    "section_subject_seconds": section_seconds,
                    "typed_dispatch": typed_dispatch,
                }
                if not section_pass:
                    raise _rejection(
                        "confirmation section failed its first terminal gate",
                        contexts=context_records,
                        coordinate=coordinate,
                        evidence=target_record,
                    )
                targets.append(target_record)
                section_coordinates.append(
                    (context.context_id, direction.label, target)
                )
                all_section_evidence &= all(evidence_checks.values())
                all_typed_dispatch &= typed_dispatch
                all_exact_authorities &= exact_authorities
                all_dual_cardinality &= evidence_checks[
                    "dual_cardinality_semantics"
                ]
                all_zero_materialization &= evidence_checks[
                    "zero_materialized_tapes"
                ]
                mode_counts[str(evidence["mode"])] += 1
                pieces = evidence["pieces"]
                assert isinstance(pieces, list)
                piece_counts.append(len(pieces))
                source_face = evidence["source_face"]
                assert isinstance(source_face, Mapping)
                maximum_total_cardinality = max(
                    maximum_total_cardinality,
                    int(source_face["total_function_cardinality"]),
                )
                maximum_reachable_cardinality = max(
                    maximum_reachable_cardinality,
                    int(source_face["reachable_support_cardinality"]),
                )
                window = evidence["single_tape_window"]
                if isinstance(window, Mapping):
                    selector_window_scale_limits.append(float(window["scale_limit"]))
            direction_records.append(direction_record)
        context_records.append(context_record)

    campaign_seconds = time.perf_counter() - campaign_start
    coordinate_count = len(section_coordinates)
    all_or_nothing_coordinates = (
        coordinate_count == gates["expected_sections"]
        and len(set(section_coordinates)) == coordinate_count
        and len(parsed["target_players"])
        == gates["expected_targets_per_direction"]
        and gates["expected_sections"]
        == gates["expected_contexts"]
        * gates["expected_directions_per_context"]
        * gates["expected_targets_per_direction"]
        and all(
            len(direction["targets"]) == gates["expected_targets_per_direction"]
            for context in context_records
            for direction in context["directions"]
        )
        and tuple(context.context_id for context in population.contexts)
        == tuple(record["context_id"] for record in context_records)
    )
    emissions = {
        "actions_emitted": 0,
        "quality_rows_serialized": 0,
        "strategy_labels_generated": 0,
        "strategy_quality_claim": None,
    }
    checks = {
        "clean_git_state": (git.get("dirty") is False)
        == gates["require_clean_git_state"],
        "population_identity": population_identity
        == gates["require_population_identity"],
        "context_identity": all_context_identity
        == gates["require_context_identity"],
        "direction_inventory": all_direction_inventory
        == gates["require_direction_inventory"],
        "row_growth_exact_acceptance": all_row_growth_acceptance
        == gates["require_row_growth_exact_acceptance"],
        "complete_section_evidence": all_section_evidence
        == gates["require_complete_section_evidence"],
        "typed_dispatch": all_typed_dispatch == gates["require_typed_dispatch"],
        "exact_authorities": all_exact_authorities
        == gates["require_exact_authorities"],
        "dual_cardinality_semantics": all_dual_cardinality
        == gates["require_dual_cardinality_semantics"],
        "zero_materialized_tapes": all_zero_materialization
        == gates["require_zero_materialized_tapes"],
        "all_or_nothing_coordinates": all_or_nothing_coordinates
        == gates["require_all_or_nothing_coordinates"],
        "no_target_outcome_gate": (not _contains_outcome_key(parsed))
        == gates["require_no_target_outcome_gate"],
        "section_subject_wall": all(
            target["section_subject_seconds"]
            <= gates["maximum_section_subject_seconds"]
            for context in context_records
            for direction in context["directions"]
            for target in direction["targets"]
        ),
        "subject_wall": subject_seconds <= gates["maximum_subject_seconds"],
        "campaign_wall": campaign_seconds <= gates["maximum_campaign_seconds"],
        "zero_actions_and_quality_rows": emissions
        == {
            "actions_emitted": 0,
            "quality_rows_serialized": 0,
            "strategy_labels_generated": 0,
            "strategy_quality_claim": None,
        }
        == gates["require_zero_actions_and_quality_rows"],
    }
    payload: dict[str, Any] = {
        "population": {
            "canonical_bytes": len(population.canonical_bytes),
            "context_sha256s": [
                context.semantic_digest for context in population.contexts
            ],
            "population_sha256": population.digest,
            "protocol_sha256": ADR0360_CONFIRMATION_PROTOCOL_SHA256,
        },
        "contexts": context_records,
        "observations": {
            "maximum_reachable_support_cardinality": maximum_reachable_cardinality,
            "maximum_total_function_cardinality": maximum_total_cardinality,
            "mode_counts": dict(sorted(mode_counts.items())),
            "piece_counts": piece_counts,
            "selector_window_scale_limits": selector_window_scale_limits,
        },
        "section_coordinates_sha256": canonical_sha256(section_coordinates),
        "section_count": coordinate_count,
        "subject_seconds": subject_seconds,
        "campaign_seconds": campaign_seconds,
        **emissions,
    }
    checks["finite"] = _finite_tree(payload) == gates["require_finite"]
    finalized = finalize_gates(checks)
    return {
        **payload,
        **finalized,
        "decision": (
            "accept_untouched_legal_h4_factorized_affine_confirmation"
            if finalized["passed"]
            else "reject_untouched_legal_h4_factorized_affine_confirmation"
        ),
    }


def _write_exclusive(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags, 0o644)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _environment(git: Mapping[str, object] | None) -> dict[str, Any]:
    return assemble_environment(
        runtime={"backend": "cpu_fraction_exact_fan_factorized_face"},
        git=(
            {"available": False, "dirty": None, "commit": None}
            if git is None
            else git
        ),
    )


def _failure_result(
    *,
    loaded_sha256: str | None,
    git: Mapping[str, object] | None,
    stage: str,
    error: BaseException,
) -> dict[str, Any]:
    failure: dict[str, Any] = {
        "stage": stage,
        "type": type(error).__name__,
        "message": str(error),
    }
    if isinstance(error, ConfirmationRejected):
        failure["scientific_rejection"] = dict(error.record)
    return {
        "schema_version": "legal-h4-factorized-affine-confirmation-result-v1",
        "status": "legal_h4_factorized_affine_confirmation_failed",
        "config_sha256": loaded_sha256,
        "implementation_sha256": _canonical_lf_sha256(_IMPLEMENTATION),
        "parent_protocol_sha256": ADR0360_CONFIRMATION_PROTOCOL_SHA256,
        "environment": _environment(git),
        "decision": "reject_untouched_legal_h4_factorized_affine_confirmation",
        "passed": False,
        "gates": {"first_terminal_failure": True, "passed": False},
        "failure": failure,
        "strategy_quality_claim": None,
        "actions_emitted": 0,
        "quality_rows_serialized": 0,
        "strategy_labels_generated": 0,
    }


def run_legal_h4_factorized_affine_confirmation(
    *,
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Consume exactly one untouched confirmation terminal."""

    if output_path.exists():
        raise FileExistsError(f"legal h4 confirmation result path exists: {output_path}")
    loaded = None
    parsed = None
    git: Mapping[str, object] | None = None
    stage = "config"
    try:
        loaded = load_config(
            config_path,
            schema_validator=lambda payload: _parse_config(payload),
        )
        parsed = _parse_config(loaded.payload)
        stage = "git_precondition"
        git = _strict_git_metadata()
        if bool(git["dirty"]):
            raise RuntimeError("legal h4 confirmation invocation requires a clean commit")
        stage = "confirmation"
        payload = _execute_confirmation(parsed, git=git)
        result = {
            "schema_version": "legal-h4-factorized-affine-confirmation-result-v1",
            "status": "legal_h4_factorized_affine_confirmation_executed",
            "config_sha256": loaded.sha256,
            "implementation_sha256": _canonical_lf_sha256(_IMPLEMENTATION),
            "parent_protocol_sha256": ADR0360_CONFIRMATION_PROTOCOL_SHA256,
            "environment": _environment(git),
            "methodology": {
                "contexts": 4,
                "directions_per_context": 4,
                "targets_per_direction": 2,
                "sections": 32,
                "direction_generation_stage": parsed["direction_generation_stage"],
                "section_subject_wall_semantics": parsed[
                    "section_subject_wall_semantics"
                ],
                "subject_wall_semantics": parsed["subject_wall_semantics"],
                "campaign_wall_semantics": parsed["campaign_wall_semantics"],
                "result_path_lifecycle": parsed["result_path_lifecycle"],
                "failure_interpretation": parsed["failure_interpretation"],
                "claims_policy": parsed["claims_policy"],
            },
            "limitations": [
                "finite_fresh_h4_mechanism_confirmation_only",
                "not_full_width_capacity_or_action_clock_latency",
                "not_multiway_response_closure_or_cross_street_handoff",
                "not_action_quality_strategy_strength_or_complete_bot_evidence",
            ],
            **payload,
        }
    except BaseException as error:
        result = _failure_result(
            loaded_sha256=None if loaded is None else loaded.sha256,
            git=git,
            stage=stage,
            error=error,
        )

    rendered = serialize_result(result)
    maximum_result_bytes = (
        8_388_608
        if parsed is None
        else int(parsed["gates"]["maximum_result_bytes"])
    )
    if len(rendered.encode("utf-8")) > maximum_result_bytes:
        result = _failure_result(
            loaded_sha256=None if loaded is None else loaded.sha256,
            git=git,
            stage="result_bytes",
            error=RuntimeError("legal h4 confirmation result exceeds byte bound"),
        )
        rendered = serialize_result(result)
    _write_exclusive(output_path, rendered)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    arguments = parser.parse_args()
    result = run_legal_h4_factorized_affine_confirmation(
        config_path=arguments.config,
        output_path=arguments.output,
    )
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    raise SystemExit(0 if bool(result.get("passed")) else 1)


if __name__ == "__main__":
    main()


__all__ = ["run_legal_h4_factorized_affine_confirmation"]
