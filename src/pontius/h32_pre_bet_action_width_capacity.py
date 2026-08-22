"""Label-free h32 capacity screen for a widened current-decision master."""

from __future__ import annotations

import argparse
from collections import Counter
import gc
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

import numpy as np

from .atomic_json_checkpoint import write_atomic_json_checkpoint
from .axis_cfr_checkpoint import axis_cfr_checkpoint_digest
from .behavioral_one_seat_master import (
    BehavioralMasterSolution,
    solve_behavioral_one_seat_master,
)
from .canonical_affine_resident_automaton_cache import (
    CuPyCanonicalAffineResidentAutomatonCache,
)
from .continuation_public_tree_tensor import ContinuationPublicTreeTensorEvaluator
from .cross_payoff_leaf_adjoint import (
    evaluate_device_fold_cross_payoff_leaf_adjoint,
)
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    release_cupy_memory_pool,
)
from .device_fold_resident_leaf_adjoint_cfr import (
    DeviceFoldResidentLeafAdjointPublicTreeCFR,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import (
    _strict_git_metadata,
    _validate_runtime,
)
from .h32_decision_aligned_posterior_manifest import (
    build_public_sequence_posterior,
)
from .h32_resident_record_to_hand_fold_differential import _work_ledger
from .h32_warm_search_acceptance_audit import (
    _average_policy_from_state,
    _policy_distance,
)
from .incremental_policy_tt import compile_policy_probability_tape
from .incremental_leaf_adjoint_response import compile_leaf_adjoint_response_caches
from .leaf_adjoint_cfr import build_leaf_adjoint_terminal_automata
from .leaf_adjoint_checkpoint_ladder_audit import (
    _build_case,
)
from .multi_size_affine_cross_payoff import (
    evaluate_multi_size_affine_cross_payoff,
)
from .multi_size_affine_resident_leaf_adjoint_cfr import (
    MultiSizeAffineResidentLeafAdjointPublicTreeCFR,
)
from .multi_size_affine_resident_leaf_adjoint_evaluation import (
    evaluate_multi_size_affine_resident_profile,
)
from .multi_size_continuation_public_tree_tensor import (
    MultiSizeContinuationPublicTreeTensorEvaluator,
)
from .multi_size_leaf_adjoint import (
    build_multi_size_leaf_adjoint_terminal_automata,
    multi_size_terminal_groups,
)
from .multi_size_policy_bridge import embed_one_size_policy, sized_policy_digest
from .open_mode_factor_tt import OpenModeFactorTTWorkspace
from .payoff_semantics import payoff_span, raw_guard
from .public_node_behavioral_axis import compile_public_node_behavioral_axis
from .public_node_open_axis import public_node_open_axis_payoff_row
from .public_policy_tt import _first_compatible_assignment, information_schema_for_axes
from .public_tree_tensor import PublicTreeTensorEvaluator
from .real_policy import policy_digest
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
)
from .river import CHECK, parse_cards
from .river_multiway import MultiwayRiverDeal
from .river_multiway_multi_size import MultiwayMultiSizeRiverHoldem
from .runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    serialize_result,
)
from .sequence_form_open_axis import (
    SequenceFormAffineRow,
    constant_minus_affine_row,
    splice_fixed_response_probability_tape_for_axes,
    subtract_affine_rows,
)
from .showdown_value_rank_screen import _rank_codes, _terminal_groups


_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/h32-pre-bet-action-width-capacity-v1.json"
_OUTPUT = _ROOT / "experiments/results/h32-pre-bet-action-width-capacity-v1.json"
_CHECKPOINT = (
    _ROOT / "experiments/results/h32-pre-bet-action-width-capacity-v1.partial.json"
)
_SOURCE = _ROOT / "experiments/results/h32-fresh-panel-source-blueprints-v1.json"
_SOURCE_CONFIG = (
    _ROOT / "experiments/configs/h32-fresh-panel-source-blueprints-v1.json"
)
_DECISION_PLAN = (
    _ROOT / "experiments/configs/h32-decision-aligned-posterior-manifest-v1.json"
)
_PARENT_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0276-post-fold-failures-close-in-two-and-three-rounds.md"
)
_ACTION_WIDTH_DECISION = (
    _ROOT / "docs/decisions/ADR-0237-full-bisector-library-does-not-fit-every-street.md"
)
_IMPLEMENTATION = Path(__file__)
_TEST = _ROOT / "tests/test_h32_pre_bet_action_width_capacity.py"

_PATHS = {
    "expected_source_result_sha256": _SOURCE,
    "expected_source_config_sha256": _SOURCE_CONFIG,
    "expected_decision_plan_sha256": _DECISION_PLAN,
    "expected_parent_decision_sha256": _PARENT_DECISION,
    "expected_action_width_decision_sha256": _ACTION_WIDTH_DECISION,
    "expected_sized_continuation_sha256": (
        _ROOT / "src/pontius/multi_size_continuation_public_tree_tensor.py"
    ),
    "expected_sized_cross_payoff_sha256": (
        _ROOT / "src/pontius/multi_size_affine_cross_payoff.py"
    ),
    "expected_public_node_row_sha256": (
        _ROOT / "src/pontius/public_node_open_axis.py"
    ),
    "expected_public_node_axis_sha256": (
        _ROOT / "src/pontius/public_node_behavioral_axis.py"
    ),
    "expected_canonical_cache_sha256": (
        _ROOT / "src/pontius/canonical_affine_resident_automaton_cache.py"
    ),
    "expected_sized_solver_sha256": (
        _ROOT / "src/pontius/multi_size_affine_resident_leaf_adjoint_cfr.py"
    ),
    "expected_sized_evaluation_sha256": (
        _ROOT / "src/pontius/multi_size_affine_resident_leaf_adjoint_evaluation.py"
    ),
    "expected_policy_bridge_sha256": (
        _ROOT / "src/pontius/multi_size_policy_bridge.py"
    ),
    "expected_checkpoint_helper_sha256": (
        _ROOT / "src/pontius/atomic_json_checkpoint.py"
    ),
    "expected_runner_harness_sha256": _ROOT / "src/pontius/runner_harness.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _TEST,
    "expected_sized_continuation_test_sha256": (
        _ROOT / "tests/test_multi_size_continuation_public_tree_tensor.py"
    ),
    "expected_sized_cross_payoff_test_sha256": (
        _ROOT / "tests/test_multi_size_affine_cross_payoff.py"
    ),
    "expected_public_node_test_sha256": (
        _ROOT / "tests/test_public_node_open_axis.py"
    ),
}


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required action-width capacity input is unavailable: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_digest(value: Any) -> str:
    rendered = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


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


def pre_bet_check_observations(acting_player: int) -> tuple[dict[str, Any], ...]:
    """Return exactly the public checks observed before one seat acts."""

    if isinstance(acting_player, bool) or acting_player not in range(6):
        raise ValueError("pre-bet current actor must be one of six seats")
    history: list[tuple[int, str]] = []
    rows = []
    for actor in range(acting_player):
        rows.append(
            {
                "actor": actor,
                "public_history": (
                    "root"
                    if not history
                    else "/".join(
                        f"p{seat}:{action}" for seat, action in history
                    )
                ),
                "action": CHECK,
            }
        )
        history.append((actor, CHECK))
    return tuple(rows)


def target_specs(parsed: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Expand the frozen source-by-position Cartesian inventory."""

    return tuple(
        {
            **dict(source),
            "acting_player": acting_player,
            "target_id": f"{source['source']}/checks_to_seat{acting_player}",
            "public_prefix": [
                [actor, CHECK] for actor in range(acting_player)
            ],
        }
        for source in parsed["sources"]
        for acting_player in parsed["acting_player_order"]
    )


def derive_capacity_proxy(
    *,
    warm_step_ms: float,
    initial_row_ms: float,
    first_master_ms: float,
    source_oracle_ms: float,
    five_cut_row_proxy_ms: float,
    second_master_reserve_ms: float,
    proof_reserve_ms: float,
    retreat_envelope_reserve_ms: float,
    emission_reserve_ms: float,
    street_budget_ms: float,
) -> dict[str, float | bool]:
    """Price one complete cut round without evaluating a master candidate."""

    values = (
        warm_step_ms,
        initial_row_ms,
        first_master_ms,
        source_oracle_ms,
        five_cut_row_proxy_ms,
        second_master_reserve_ms,
        proof_reserve_ms,
        retreat_envelope_reserve_ms,
        emission_reserve_ms,
        street_budget_ms,
    )
    if any(not math.isfinite(float(value)) or float(value) < 0.0 for value in values):
        raise ValueError("action-width capacity inputs must be finite and nonnegative")
    if street_budget_ms <= 0.0:
        raise ValueError("action-width capacity requires a positive street budget")
    oracle_proxy = max(float(source_oracle_ms), float(warm_step_ms))
    second_master = max(float(first_master_ms), float(second_master_reserve_ms))
    total = math.fsum(
        (
            float(warm_step_ms),
            float(initial_row_ms),
            float(first_master_ms),
            2.0 * oracle_proxy,
            float(five_cut_row_proxy_ms),
            second_master,
            float(proof_reserve_ms),
            float(retreat_envelope_reserve_ms),
            float(emission_reserve_ms),
        )
    )
    return {
        "endpoint_oracle_proxy_ms_each": oracle_proxy,
        "second_master_proxy_ms": second_master,
        "complete_one_round_proxy_ms": total,
        "headroom_ms": float(street_budget_ms) - total,
        "fits_street": total <= float(street_budget_ms),
    }


def _parse_config(config: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "evidence_stage",
        *_PATHS,
        "seed",
        "sources",
        "acting_player_order",
        "expected_inventory_sha256",
        "target_rule",
        "scope_rule",
        "arm_rule",
        "current_node_rule",
        "baseline_label_rule",
        "candidate_label_rule",
        "capacity_rule",
        "promotion_rule",
        "street_budget_ms",
        "second_master_reserve_ms",
        "proof_reserve_ms",
        "retreat_envelope_reserve_ms",
        "emission_reserve_ms",
        "minimum_noncache_reserve_bytes",
        "pot",
        "stack",
        "one_size_bets",
        "two_size_bets",
        "players",
        "hands_per_player",
        "axis_seed",
        "mixture_components",
        "split_index",
        "query_chunk_records",
        "solver_variant",
        "warm_regret_mass_payoff_fraction",
        "maximum_feature_width_per_batch",
        "acceptance_guard_normalized",
        "lp_tolerance",
        "candidate_projection_tolerance",
        "required_numpy_version",
        "required_scipy_version",
        "required_cupy_version",
        "required_cuda_runtime_version",
        "minimum_cuda_driver_version",
        "required_compute_capability",
        "cuda_dll_environment_variable",
        "maximum_campaign_seconds",
        "gates",
    }
    if set(config) != expected:
        raise ValueError("pre-bet action-width capacity fields differ from ADR-0277")
    for field_name, path in _PATHS.items():
        if config[field_name] != _sha256(path):
            raise ValueError(f"pre-bet action-width provenance mismatch: {field_name}")
    if len(config["expected_inventory_sha256"]) != 64:
        raise ValueError("pre-bet inventory digest is malformed")
    exact = {
        "evidence_stage": (
            "preregistered_after_adr0276_before_any_h32_pre_bet_widened_warm_"
            "step_master_or_candidate_evaluation"
        ),
        "seed": 20260822,
        "acting_player_order": list(range(6)),
        "target_rule": (
            "cartesian_six_retained_sources_by_all_six_current_positions_"
            "posterior_conditioned_only_on_prior_checks"
        ),
        "scope_rule": (
            "optimize_exactly_the_current_public_node_hold_every_future_own_"
            "and_all_opponent_policy_rows_at_the_embedded_blueprint"
        ),
        "arm_rule": (
            "one_size_raw_resident_incumbent_versus_two_size_scale_canonical_"
            "affine_resident_candidate"
        ),
        "current_node_rule": (
            "one_public_node_thirty_two_information_sets_sixty_four_versus_"
            "ninety_six_policy_variables"
        ),
        "baseline_label_rule": (
            "exact_embedded_blueprint_response_evaluations_only_as_required_"
            "optimizer_inputs_values_and_coefficients_not_serialized"
        ),
        "candidate_label_rule": (
            "zero_master_candidate_endpoint_retreat_certificate_or_strategy_"
            "quality_evaluations_and_blueprint_only_emission"
        ),
        "capacity_rule": (
            "warm_plus_eleven_initial_rows_plus_first_master_plus_two_max_of_"
            "source_oracle_or_warm_proxies_plus_five_measured_response_row_"
            "proxy_plus_second_master_proof_envelope_and_emission_reserves"
        ),
        "promotion_rule": (
            "an_acting_position_is_capacity_admitted_only_if_the_two_size_"
            "proxy_fits_all_six_sources_after_every_memory_and_mechanism_gate"
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
        "solver_variant": "dcfr",
        "warm_regret_mass_payoff_fraction": 0.1,
        "maximum_feature_width_per_batch": 384,
        "acceptance_guard_normalized": 1e-10,
        "lp_tolerance": 1e-10,
        "candidate_projection_tolerance": 1e-10,
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
        "maximum_campaign_seconds": 3600.0,
    }
    for field_name, expected_value in exact.items():
        if config[field_name] != expected_value:
            raise ValueError(
                f"pre-bet action-width field differs from ADR-0277: {field_name}"
            )
    source_config = json.loads(_SOURCE_CONFIG.read_text(encoding="utf-8"))
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
    if config["sources"] != expected_sources:
        raise ValueError("pre-bet action-width sources differ from sealed source order")
    gates = {
        "expected_sources": 6,
        "expected_targets": 36,
        "expected_arms": 72,
        "expected_cache_rows": 72,
        "expected_warm_steps_if_safe": 72,
        "expected_baseline_seat_evaluations_if_safe": 432,
        "expected_initial_passes_per_arm": 11,
        "expected_initial_gain_rows_per_arm": 6,
        "expected_current_information_sets": 32,
        "expected_one_size_policy_variables": 64,
        "expected_two_size_policy_variables": 96,
        "expected_one_size_public_nodes_by_actor": [385, 321, 257, 193, 129, 65],
        "expected_two_size_public_nodes_by_actor": [763, 636, 509, 382, 255, 128],
        "expected_one_size_terminal_groups_by_actor": [64, 63, 61, 57, 49, 33],
        "expected_two_size_terminal_groups_by_actor": [127, 125, 121, 113, 97, 65],
        "maximum_source_row_error": 2e-11,
        "maximum_master_primal_error": 1e-8,
        "maximum_master_dual_error": 1e-8,
        "maximum_projection_error": 1e-8,
        "maximum_warm_start_probability_error": 1e-12,
        "maximum_warm_start_mean_total_variation": 1e-13,
        "maximum_cache_compile_ms": 120000.0,
        "maximum_warm_step_ms": 120000.0,
        "maximum_initial_row_ms": 120000.0,
        "maximum_master_ms": 60000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "minimum_physical_free_bytes": 1000000000,
        "require_clean_git_state": True,
        "require_parents_passed": True,
        "require_inventory_identity": True,
        "require_source_checkpoint_identity": True,
        "require_target_identity": True,
        "require_blueprint_identity": True,
        "require_current_node_only": True,
        "require_off_node_immutable": True,
        "require_conditional_barrier": True,
        "require_checkpoint_bytes_truth": True,
        "require_zero_candidate_evaluations": True,
        "require_blueprint_emission": True,
        "require_strategy_population_claim_null": True,
        "require_finite": True,
    }
    if config["gates"] != gates:
        raise ValueError("pre-bet action-width gates differ from ADR-0277")
    return {
        **config,
        "sources": tuple(dict(row) for row in config["sources"]),
        "acting_player_order": tuple(config["acting_player_order"]),
        "one_size_bets": tuple(config["one_size_bets"]),
        "two_size_bets": tuple(config["two_size_bets"]),
        "gates": gates,
    }


def _memory_snapshot(cp: Any) -> dict[str, int]:
    free, total = cp.cuda.runtime.memGetInfo()
    pool = cp.get_default_memory_pool()
    return {
        "gpu_pool_used_bytes": int(pool.used_bytes()),
        "gpu_pool_total_bytes": int(pool.total_bytes()),
        "gpu_free_bytes": int(free),
        "gpu_total_bytes": int(total),
    }


def _sized_game(
    belief: Any,
    *,
    pot: float,
    stack: float,
    bet_sizes: tuple[float, ...],
) -> MultiwayMultiSizeRiverHoldem:
    assignment = _first_compatible_assignment(belief)
    deal = MultiwayRiverDeal(
        tuple(
            belief.hands_by_player[seat][assignment[seat]]
            for seat in range(belief.num_players)
        )
    )
    return MultiwayMultiSizeRiverHoldem.from_joint_weights(
        board=belief.board,
        pot=pot,
        stacks=(stack,) * belief.num_players,
        bet_sizes=bet_sizes,
        joint_weights={deal: 1.0},
    )


def _source_objects(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
    source_spec: Mapping[str, Any],
) -> dict[str, Any]:
    board = parse_cards(*source_spec["board"])
    source_parsed = {**dict(parsed), "bet_size": float(parsed["one_size_bets"][0])}
    source, full, sparse, retained = _build_case(
        parsed=source_parsed,
        board=board,
        hand_count=int(parsed["hands_per_player"]),
        family=str(source_spec["range_family"]),
    )
    source_workspace, _, _ = retained
    source_row = next(
        row
        for row in source_parent["source_rows"]
        if row["source"] == source_spec["source"]
    )
    state = source_row["final_checkpoint"]
    full_blueprint = _average_policy_from_state(state)
    return {
        "board": board,
        "source": source,
        "full": full,
        "sparse": sparse,
        "source_workspace": source_workspace,
        "state": state,
        "full_blueprint": full_blueprint,
        "source_checkpoint_sha256": state["state_sha256"],
        "source_average_policy_sha256": state["average_policy_sha256"],
        "source_identity": (
            _belief_digest(source) == source_spec["source_belief_sha256"]
            and axis_cfr_checkpoint_digest(state) == state["state_sha256"]
            and policy_digest(full_blueprint) == state["average_policy_sha256"]
        ),
    }


def _target_belief_and_inventory(
    source_objects: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> tuple[Any, dict[str, Any]]:
    """Build one frozen check-conditioned belief and its label-free identity."""

    acting_player = int(spec["acting_player"])
    observations = pre_bet_check_observations(acting_player)
    belief, _ = build_public_sequence_posterior(
        source_objects["source"],
        source_objects["full_blueprint"],
        observations,
    )
    public_prefix = tuple((row["actor"], row["action"]) for row in observations)
    inventory = {
        "target_id": spec["target_id"],
        "source": spec["source"],
        "acting_player": acting_player,
        "public_prefix": [list(row) for row in public_prefix],
        "board": list(spec["board"]),
        "range_family": spec["range_family"],
        "source_belief_sha256": spec["source_belief_sha256"],
        "source_checkpoint_sha256": source_objects["source_checkpoint_sha256"],
        "source_average_policy_sha256": source_objects[
            "source_average_policy_sha256"
        ],
        "target_belief_sha256": _belief_digest(belief),
    }
    return belief, inventory


def build_inventory_rows(
    parsed: Mapping[str, Any],
    source_parent: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    """Reconstruct the complete CPU-only target inventory before GPU work."""

    specs = target_specs(parsed)
    rows = []
    for source_spec in parsed["sources"]:
        source = _source_objects(parsed, source_parent, source_spec)
        for spec in (
            row for row in specs if row["source"] == source_spec["source"]
        ):
            _, inventory = _target_belief_and_inventory(source, spec)
            rows.append(inventory)
    return tuple(rows)


def _target_objects(
    parsed: Mapping[str, Any],
    source_objects: Mapping[str, Any],
    spec: Mapping[str, Any],
    gpu: CuPyBidirectionalIncidence,
) -> dict[str, Any]:
    acting_player = int(spec["acting_player"])
    belief, inventory = _target_belief_and_inventory(source_objects, spec)
    public_prefix = tuple(tuple(row) for row in inventory["public_prefix"])
    base_started = time.perf_counter()
    base = FactorTTBeliefWorkspace.compile(
        source_objects["source_workspace"].topology.base,
        belief,
        query_chunk_records=int(parsed["query_chunk_records"]),
    )
    workspace = OpenModeFactorTTWorkspace.compile(
        source_objects["source_workspace"].topology,
        base,
    )
    workspace_ms = (time.perf_counter() - base_started) * 1000.0

    one_started = time.perf_counter()
    one_layout = (
        PublicTreeTensorEvaluator(source_objects["full"].game)
        if not public_prefix
        else ContinuationPublicTreeTensorEvaluator(
            source_objects["full"].game,
            public_prefix=public_prefix,
        )
    )
    one_layout_ms = (time.perf_counter() - one_started) * 1000.0
    two_started = time.perf_counter()
    two_layout = MultiSizeContinuationPublicTreeTensorEvaluator(
        _sized_game(
            belief,
            pot=float(parsed["pot"]),
            stack=float(parsed["stack"]),
            bet_sizes=tuple(parsed["two_size_bets"]),
        ),
        public_prefix=public_prefix,
    )
    two_layout_ms = (time.perf_counter() - two_started) * 1000.0

    one_schema = information_schema_for_axes(one_layout, belief.hands_by_player)
    one_blueprint = {
        key: dict(source_objects["full_blueprint"][key]) for key in one_schema
    }
    two_blueprint = embed_one_size_policy(
        source_objects["full"],
        two_layout,
        belief.hands_by_player,
        source_objects["full_blueprint"],
        retained_bet_size=float(parsed["one_size_bets"][0]),
    )
    codes = tuple(
        np.ascontiguousarray(values, dtype=np.int32)
        for values in _rank_codes(source_objects["board"], belief.hands_by_player)
    )
    one_automata_started = time.perf_counter()
    one_automata = build_leaf_adjoint_terminal_automata(
        one_layout,
        codes,
        pot=float(parsed["pot"]),
        bet_size=float(parsed["one_size_bets"][0]),
    )
    one_automata_ms = (time.perf_counter() - one_automata_started) * 1000.0
    two_automata_started = time.perf_counter()
    two_automata = build_multi_size_leaf_adjoint_terminal_automata(
        two_layout,
        codes,
        pot=float(parsed["pot"]),
    )
    two_automata_ms = (time.perf_counter() - two_automata_started) * 1000.0
    return {
        "spec": spec,
        "inventory": inventory,
        "source_identity": bool(source_objects["source_identity"]),
        "belief": belief,
        "workspace": workspace,
        "workspace_ms": workspace_ms,
        "sparse": source_objects["sparse"],
        "gpu": gpu,
        "arms": {
            "one_size": {
                "layout": one_layout,
                "layout_ms": one_layout_ms,
                "automata": one_automata,
                "automata_ms": one_automata_ms,
                "blueprint": one_blueprint,
                "blueprint_sha256": policy_digest(one_blueprint),
                "cache_class": CuPyResidentAutomatonCache,
            },
            "two_size": {
                "layout": two_layout,
                "layout_ms": two_layout_ms,
                "automata": two_automata,
                "automata_ms": two_automata_ms,
                "blueprint": two_blueprint,
                "blueprint_sha256": sized_policy_digest(two_blueprint),
                "cache_class": CuPyCanonicalAffineResidentAutomatonCache,
            },
        },
    }


def _library_numeric_bytes(libraries: Sequence[Mapping[str, Any]]) -> int:
    unique = {id(value): value for library in libraries for value in library.values()}
    return sum(int(value.numeric_bytes) for value in unique.values())


def _compile_cache_arm(
    cp: Any,
    target: Mapping[str, Any],
    arm_name: str,
    parsed: Mapping[str, Any],
) -> tuple[dict[str, Any], CuPyResidentBeliefCache, tuple[Any, ...]]:
    arm = target["arms"][arm_name]
    gc.collect()
    release_cupy_memory_pool()
    pool = cp.get_default_memory_pool()
    baseline = _memory_snapshot(cp)
    cp.cuda.runtime.deviceSynchronize()
    started = time.perf_counter()
    belief_cache = CuPyResidentBeliefCache.compile(target["workspace"])
    caches = tuple(
        arm["cache_class"].compile(
            target["workspace"],
            arm["automata"][seat],
            target_seat=seat,
        )
        for seat in range(int(parsed["players"]))
    )
    cp.cuda.runtime.deviceSynchronize()
    cache_ms = (time.perf_counter() - started) * 1000.0
    snapshot = _memory_snapshot(cp)
    cache_bytes = sum(int(cache.numeric_bytes) for cache in caches)
    persistent = int(belief_cache.numeric_bytes) + cache_bytes
    pool_headroom = int(parsed["gates"]["maximum_gpu_pool_bytes"]) - snapshot[
        "gpu_pool_total_bytes"
    ]
    physical_headroom = snapshot["gpu_free_bytes"] - int(
        parsed["minimum_noncache_reserve_bytes"]
    )
    row = {
        "arm": arm_name,
        "layout_compile_ms": float(arm["layout_ms"]),
        "automata_compile_ms": float(arm["automata_ms"]),
        "device_cache_compile_ms": cache_ms,
        "cold_construction_ms": math.fsum(
            (float(arm["layout_ms"]), float(arm["automata_ms"]), cache_ms)
        ),
        "host_automata_numeric_bytes": _library_numeric_bytes(arm["automata"]),
        "belief_numeric_bytes": int(belief_cache.numeric_bytes),
        "automaton_numeric_bytes": cache_bytes,
        "persistent_numeric_bytes": persistent,
        "raw_equivalent_automaton_numeric_bytes": sum(
            int(getattr(cache, "raw_equivalent_numeric_bytes", cache.numeric_bytes))
            for cache in caches
        ),
        "total_logical_middle_rank": sum(
            int(cache.total_middle_rank) for cache in caches
        ),
        "stored_topology_middle_rank": sum(
            int(getattr(cache, "stored_topology_middle_rank", cache.total_middle_rank))
            for cache in caches
        ),
        "maximum_middle_rank": max(int(cache.maximum_middle_rank) for cache in caches),
        "logical_automata": sum(int(cache.unique_automata) for cache in caches),
        "shared_bases": sum(
            int(getattr(cache, "shared_topologies", cache.unique_automata))
            for cache in caches
        ),
        "pool_baseline_used_bytes": baseline["gpu_pool_used_bytes"],
        "pool_baseline_total_bytes": baseline["gpu_pool_total_bytes"],
        "pool_used_bytes": snapshot["gpu_pool_used_bytes"],
        "pool_total_bytes": snapshot["gpu_pool_total_bytes"],
        "pool_total_increase_bytes": snapshot["gpu_pool_total_bytes"]
        - baseline["gpu_pool_total_bytes"],
        "pool_cap_headroom_bytes": pool_headroom,
        "physical_device_free_bytes": snapshot["gpu_free_bytes"],
        "physical_headroom_over_reserve_bytes": physical_headroom,
        "safe_for_runtime": (
            snapshot["gpu_pool_total_bytes"]
            <= int(parsed["gates"]["maximum_gpu_pool_bytes"])
            and pool_headroom >= int(parsed["minimum_noncache_reserve_bytes"])
            and snapshot["gpu_free_bytes"]
            >= int(parsed["minimum_noncache_reserve_bytes"])
        ),
        "pool_allocator_used_bytes": int(pool.used_bytes()),
    }
    return row, belief_cache, caches


def _layout_geometry(target: Mapping[str, Any], arm_name: str) -> dict[str, Any]:
    layout = target["arms"][arm_name]["layout"]
    groups = (
        len(_terminal_groups(layout))
        if arm_name == "one_size"
        else len(multi_size_terminal_groups(layout))
    )
    return {
        "public_nodes": int(layout.public_node_count),
        "strategic_nodes": int(layout.strategic_node_count),
        "terminal_nodes": int(layout.terminal_node_count),
        "terminal_groups": groups,
        "root_player": int(layout.nodes[0].player),
        "root_action_width": len(layout.nodes[0].actions),
        "payoff_span": payoff_span(layout),
    }


def _cache_phase_target(
    parsed: Mapping[str, Any],
    cp: Any,
    target: Mapping[str, Any],
) -> dict[str, Any]:
    arms = {}
    for arm_name in ("one_size", "two_size"):
        cache, belief_cache, caches = _compile_cache_arm(
            cp,
            target,
            arm_name,
            parsed,
        )
        arms[arm_name] = {
            "geometry": _layout_geometry(target, arm_name),
            "blueprint_sha256": target["arms"][arm_name]["blueprint_sha256"],
            "cache": cache,
        }
        del caches, belief_cache
        gc.collect()
        release_cupy_memory_pool()
    return {
        **target["inventory"],
        "source_identity": bool(target["source_identity"]),
        "target_workspace_compile_ms": float(target["workspace_ms"]),
        "arms": arms,
        "ratios": {
            field: (
                arms["two_size"]["cache"][field]
                / arms["one_size"]["cache"][field]
            )
            for field in (
                "persistent_numeric_bytes",
                "total_logical_middle_rank",
                "cold_construction_ms",
            )
        },
    }


def _master_telemetry(solution: BehavioralMasterSolution) -> dict[str, Any]:
    """Return timing and verification only, deliberately redacting values."""

    return {
        "policy_variables": len(solution.variables),
        "epigraph_variables": len(solution.epigraph),
        "equality_rows": solution.equality_rows,
        "inequality_rows": solution.inequality_rows,
        "highs_iterations": solution.highs_iterations,
        "solve_ms": solution.solve_ms,
        "maximum_equality_error": solution.maximum_equality_error,
        "maximum_inequality_violation": solution.maximum_inequality_violation,
        "maximum_bound_violation": solution.maximum_bound_violation,
        "maximum_stationarity_error": solution.maximum_stationarity_error,
        "maximum_complementarity_error": solution.maximum_complementarity_error,
        "duality_gap": solution.duality_gap,
        "objective_epigraph_and_variables_serialized": False,
    }


def _pass_telemetry(kind: str, payoff_player: int, wall_ms: float, result: Any) -> dict[str, Any]:
    return {
        "kind": kind,
        "payoff_player": payoff_player,
        "wall_ms": wall_ms,
        "terminal_contractions": int(result.terminal_contractions),
        "terminal_sparse_batches": int(result.terminal_sparse_batches),
        "maximum_middle_rank": int(result.maximum_terminal_middle_rank),
        "maximum_gpu_pool_total_bytes": int(result.maximum_gpu_pool_total_bytes),
        "resident_work": _work_ledger((result.resident_work,)),
    }


def _one_pass(
    target: Mapping[str, Any],
    probabilities: Any,
    *,
    acting_player: int,
    payoff_player: int,
    source_value: float,
    belief_cache: Any,
    caches: Sequence[Any],
    cp: Any,
    parsed: Mapping[str, Any],
) -> tuple[SequenceFormAffineRow, dict[str, Any]]:
    cp.cuda.runtime.deviceSynchronize()
    started = time.perf_counter()
    extracted = evaluate_device_fold_cross_payoff_leaf_adjoint(
        target["arms"]["one_size"]["layout"],
        target["workspace"],
        target["sparse"],
        probabilities,
        target["arms"]["one_size"]["automata"][payoff_player],
        acting_player=acting_player,
        payoff_player=payoff_player,
        belief_cache=belief_cache,
        automaton_cache=caches[payoff_player],
        cupy_sparse=target["gpu"],
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
        record_to_hand_backend="gpu_cupy",
    )
    cp.cuda.runtime.deviceSynchronize()
    wall_ms = (time.perf_counter() - started) * 1000.0
    row = public_node_open_axis_payoff_row(
        target["arms"]["one_size"]["layout"],
        probabilities,
        extracted,
        acting_player=acting_player,
        public_node=0,
        source_value=source_value,
    )
    return row, _pass_telemetry("pending", payoff_player, wall_ms, extracted)


def _two_pass(
    target: Mapping[str, Any],
    probabilities: Any,
    *,
    acting_player: int,
    payoff_player: int,
    source_value: float,
    belief_cache: Any,
    caches: Sequence[Any],
    cp: Any,
    parsed: Mapping[str, Any],
) -> tuple[SequenceFormAffineRow, dict[str, Any]]:
    cp.cuda.runtime.deviceSynchronize()
    started = time.perf_counter()
    extracted = evaluate_multi_size_affine_cross_payoff(
        target["arms"]["two_size"]["layout"],
        target["workspace"],
        target["sparse"],
        probabilities,
        target["arms"]["two_size"]["automata"][payoff_player],
        acting_player=acting_player,
        payoff_player=payoff_player,
        belief_cache=belief_cache,
        automaton_cache=caches[payoff_player],
        cupy_sparse=target["gpu"],
        maximum_feature_width_per_batch=int(parsed["maximum_feature_width_per_batch"]),
    )
    cp.cuda.runtime.deviceSynchronize()
    wall_ms = (time.perf_counter() - started) * 1000.0
    row = public_node_open_axis_payoff_row(
        target["arms"]["two_size"]["layout"],
        probabilities,
        extracted,
        acting_player=acting_player,
        public_node=0,
        source_value=source_value,
    )
    return row, _pass_telemetry("pending", payoff_player, wall_ms, extracted)


def _runtime_arm(
    parsed: Mapping[str, Any],
    cp: Any,
    target: Mapping[str, Any],
    arm_name: str,
) -> dict[str, Any]:
    arm = target["arms"][arm_name]
    layout = arm["layout"]
    blueprint = arm["blueprint"]
    belief = target["belief"]
    acting_player = int(target["spec"]["acting_player"])
    cache_row, belief_cache, caches = _compile_cache_arm(
        cp,
        target,
        arm_name,
        parsed,
    )
    if not cache_row["safe_for_runtime"]:
        raise MemoryError("runtime arm opened after a failed cache-safety barrier")

    if arm_name == "one_size":
        source_started = time.perf_counter()
        response_caches = compile_leaf_adjoint_response_caches(
            layout,
            target["workspace"],
            target["sparse"],
            blueprint,
            tuple(arm["automata"]),
            hands_by_player=belief.hands_by_player,
            maximum_feature_width_per_batch=int(
                parsed["maximum_feature_width_per_batch"]
            ),
            belief_cache=belief_cache,
            automaton_caches=tuple(caches),
            cupy_sparse=target["gpu"],
        )
        source_oracle_ms = (time.perf_counter() - source_started) * 1000.0
        source_probabilities = response_caches[0].source_probabilities
        evaluations = tuple(cache.source_evaluation for cache in response_caches)
        solver = DeviceFoldResidentLeafAdjointPublicTreeCFR(
            layout,
            target["workspace"],
            target["sparse"],
            arm["automata"],
            str(parsed["solver_variant"]),
            belief_cache=belief_cache,
            automaton_caches=caches,
            cupy_sparse=target["gpu"],
            maximum_feature_width_per_batch=int(
                parsed["maximum_feature_width_per_batch"]
            ),
            hands_by_player=belief.hands_by_player,
            record_to_hand_backend="gpu_cupy",
        )
        pass_function = _one_pass
    else:
        source_profile = evaluate_multi_size_affine_resident_profile(
            layout,
            target["workspace"],
            target["sparse"],
            blueprint,
            arm["automata"],
            belief_cache=belief_cache,
            automaton_caches=tuple(caches),
            cupy_sparse=target["gpu"],
            hands_by_player=belief.hands_by_player,
            maximum_feature_width_per_batch=int(
                parsed["maximum_feature_width_per_batch"]
            ),
        )
        source_probabilities = compile_policy_probability_tape(
            layout,
            belief.hands_by_player,
            blueprint,
        )
        evaluations = source_profile.seats
        source_oracle_ms = float(source_profile.wall_ms)
        solver = MultiSizeAffineResidentLeafAdjointPublicTreeCFR(
            layout,
            target["workspace"],
            target["sparse"],
            arm["automata"],
            str(parsed["solver_variant"]),
            belief_cache=belief_cache,
            automaton_caches=tuple(caches),
            cupy_sparse=target["gpu"],
            maximum_feature_width_per_batch=int(
                parsed["maximum_feature_width_per_batch"]
            ),
            hands_by_player=belief.hands_by_player,
        )
        pass_function = _two_pass

    warm_mass = float(parsed["warm_regret_mass_payoff_fraction"]) * payoff_span(
        layout
    )
    solver.warm_start(blueprint, warm_mass)
    warm_distance = _policy_distance(blueprint, solver.current_strategy())
    cp.cuda.runtime.deviceSynchronize()
    warm_started = time.perf_counter()
    solver.step()
    cp.cuda.runtime.deviceSynchronize()
    warm_ms = (time.perf_counter() - warm_started) * 1000.0
    if solver.last_step_work is None:
        raise AssertionError("pre-bet action-width warm step emitted no work")
    warm_works = tuple(row.resident_work for row in solver.last_step_work.traversers)
    warm_row = {
        "wall_ms": warm_ms,
        "reported_wall_ms": float(solver.last_step_work.wall_ms),
        "terminal_contraction_ms": float(
            solver.last_step_work.terminal_contraction_ms
        ),
        **_work_ledger(warm_works),
    }

    profile_rows: dict[int, SequenceFormAffineRow] = {}
    gain_rows: list[SequenceFormAffineRow] = []
    pass_rows = []
    errors = []
    cp.cuda.runtime.deviceSynchronize()
    initial_started = time.perf_counter()
    for payoff_player in range(layout.num_players):
        evaluation = evaluations[payoff_player]
        row, telemetry = pass_function(
            target,
            source_probabilities,
            acting_player=acting_player,
            payoff_player=payoff_player,
            source_value=float(evaluation.profile_utility),
            belief_cache=belief_cache,
            caches=caches,
            cp=cp,
            parsed=parsed,
        )
        telemetry["kind"] = "profile"
        profile_rows[payoff_player] = row
        pass_rows.append(telemetry)
        errors.append(
            abs(row.value(source_probabilities) - float(evaluation.profile_utility))
        )
    for payoff_player in range(layout.num_players):
        evaluation = evaluations[payoff_player]
        if payoff_player == acting_player:
            gain = constant_minus_affine_row(
                float(evaluation.best_response_value),
                profile_rows[payoff_player],
            )
        else:
            response_probabilities = splice_fixed_response_probability_tape_for_axes(
                layout,
                source_probabilities,
                evaluation.best_response_actions,
                responding_player=payoff_player,
                hands_by_player=belief.hands_by_player,
            )
            response, telemetry = pass_function(
                target,
                response_probabilities,
                acting_player=acting_player,
                payoff_player=payoff_player,
                source_value=float(evaluation.best_response_value),
                belief_cache=belief_cache,
                caches=caches,
                cp=cp,
                parsed=parsed,
            )
            telemetry["kind"] = "fixed_response"
            pass_rows.append(telemetry)
            gain = subtract_affine_rows(response, profile_rows[payoff_player])
        errors.append(
            abs(
                gain.value(source_probabilities)
                - float(evaluation.best_response_value - evaluation.profile_utility)
            )
        )
        gain_rows.append(gain)
    cp.cuda.runtime.deviceSynchronize()
    initial_row_ms = (time.perf_counter() - initial_started) * 1000.0

    axis = compile_public_node_behavioral_axis(
        layout,
        belief.hands_by_player,
        blueprint,
        public_node=0,
    )
    guard = raw_guard(layout, float(parsed["acceptance_guard_normalized"]))
    source_gains = tuple(max(0.0, float(row.deviation_gain)) for row in evaluations)
    caps = tuple(value + guard for value in source_gains)
    master = solve_behavioral_one_seat_master(
        axis,
        tuple((row,) for row in gain_rows),
        caps,
        tolerance=float(parsed["lp_tolerance"]),
    )
    candidate, projection_error = axis.policy_from_variables(
        master.variables,
        blueprint,
        tolerance=float(parsed["candidate_projection_tolerance"]),
    )
    candidate_probabilities = compile_policy_probability_tape(
        layout,
        belief.hands_by_player,
        candidate,
    )
    changed_nodes = [
        node_index
        for node_index, (source_row, candidate_row) in enumerate(
            zip(source_probabilities, candidate_probabilities, strict=True)
        )
        if source_row is not None
        and candidate_row is not None
        and not np.array_equal(source_row, candidate_row)
    ]
    current_keys = {row.key for row in axis.information_sets}
    off_node_immutable = all(
        candidate[key] == blueprint[key] for key in blueprint if key not in current_keys
    )
    fixed_response_ms = math.fsum(
        row["wall_ms"] for row in pass_rows if row["kind"] == "fixed_response"
    )
    capacity = derive_capacity_proxy(
        warm_step_ms=warm_ms,
        initial_row_ms=initial_row_ms,
        first_master_ms=float(master.solve_ms),
        source_oracle_ms=source_oracle_ms,
        five_cut_row_proxy_ms=fixed_response_ms,
        second_master_reserve_ms=float(parsed["second_master_reserve_ms"]),
        proof_reserve_ms=float(parsed["proof_reserve_ms"]),
        retreat_envelope_reserve_ms=float(parsed["retreat_envelope_reserve_ms"]),
        emission_reserve_ms=float(parsed["emission_reserve_ms"]),
        street_budget_ms=float(parsed["street_budget_ms"]),
    )
    snapshot = _memory_snapshot(cp)
    result = {
        "arm": arm_name,
        "blueprint_sha256": arm["blueprint_sha256"],
        "geometry": _layout_geometry(target, arm_name),
        "cache": cache_row,
        "warm_start_distance": warm_distance,
        "warm_step": warm_row,
        "source_oracle_timing_ms": source_oracle_ms,
        "baseline_seat_evaluations": layout.num_players,
        "initial_profile_passes": sum(row["kind"] == "profile" for row in pass_rows),
        "initial_response_passes": sum(
            row["kind"] == "fixed_response" for row in pass_rows
        ),
        "initial_gain_rows": len(gain_rows),
        "initial_row_ms": initial_row_ms,
        "initial_pass_rows": pass_rows,
        "maximum_source_row_error": max(errors),
        "current_node_information_sets": len(axis.information_sets),
        "current_node_policy_variables": axis.variable_count,
        "master": _master_telemetry(master),
        "candidate_projection_error": projection_error,
        "candidate_changed_public_nodes": changed_nodes,
        "off_node_policy_immutable": off_node_immutable,
        "capacity": capacity,
        "master_candidate_evaluations": 0,
        "retreat_evaluations": 0,
        "strategy_quality_rows_serialized": 0,
        "optimizer_value_fields_serialized": 0,
        "memory_after_runtime": snapshot,
    }
    del candidate_probabilities, candidate, solver, caches, belief_cache
    if arm_name == "one_size":
        del response_caches
    else:
        del source_profile
    gc.collect()
    release_cupy_memory_pool()
    return result


def _inventory_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    return _json_digest([dict(row) for row in rows])


def run_h32_pre_bet_action_width_capacity(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
    checkpoint_path: Path = _CHECKPOINT,
) -> dict[str, Any]:
    started = time.perf_counter()
    parsed = _parse_config(json.loads(config_path.read_text(encoding="utf-8")))
    git = _strict_git_metadata()
    if git["dirty"]:
        raise RuntimeError("pre-bet action-width capacity requires clean Git")
    cp, runtime = _validate_runtime(parsed)
    source_parent = load_artifact(
        _SOURCE,
        expected_sha256=parsed["expected_source_result_sha256"],
        require_passed=True,
    ).payload
    source_config = load_artifact(
        _SOURCE_CONFIG,
        expected_sha256=parsed["expected_source_config_sha256"],
    ).payload
    decision_plan = load_artifact(
        _DECISION_PLAN,
        expected_sha256=parsed["expected_decision_plan_sha256"],
    ).payload

    specs = target_specs(parsed)
    cache_rows = []
    inventory_rows = []
    checkpoint_sha256 = None
    for source_spec in parsed["sources"]:
        source = _source_objects(parsed, source_parent, source_spec)
        gpu = CuPyBidirectionalIncidence.compile(source["sparse"])
        for spec in (row for row in specs if row["source"] == source_spec["source"]):
            target = _target_objects(parsed, source, spec, gpu)
            inventory_rows.append(target["inventory"])
            cache_rows.append(_cache_phase_target(parsed, cp, target))
            checkpoint_sha256 = write_atomic_json_checkpoint(
                {
                    "schema_version": 1,
                    "status": "h32_pre_bet_action_width_capacity_partial",
                    "phase": "cache",
                    "config_sha256": _sha256(config_path),
                    "cache_targets_completed": len(cache_rows),
                    "runtime_targets_completed": 0,
                    "cache_rows": cache_rows,
                    "runtime_rows": [],
                },
                checkpoint_path,
            )
        del gpu, source
        gc.collect()
        release_cupy_memory_pool()

    all_cache_safe = all(
        arm["cache"]["safe_for_runtime"]
        for row in cache_rows
        for arm in row["arms"].values()
    )
    runtime_rows = []
    if all_cache_safe:
        for source_spec in parsed["sources"]:
            source = _source_objects(parsed, source_parent, source_spec)
            gpu = CuPyBidirectionalIncidence.compile(source["sparse"])
            for spec in (
                row for row in specs if row["source"] == source_spec["source"]
            ):
                target = _target_objects(parsed, source, spec, gpu)
                arms = {
                    arm_name: _runtime_arm(parsed, cp, target, arm_name)
                    for arm_name in ("one_size", "two_size")
                }
                runtime_rows.append(
                    {
                        **target["inventory"],
                        "source_identity": bool(target["source_identity"]),
                        "arms": arms,
                    }
                )
                checkpoint_sha256 = write_atomic_json_checkpoint(
                    {
                        "schema_version": 1,
                        "status": "h32_pre_bet_action_width_capacity_partial",
                        "phase": "runtime",
                        "config_sha256": _sha256(config_path),
                        "cache_targets_completed": len(cache_rows),
                        "runtime_targets_completed": len(runtime_rows),
                        "cache_rows": cache_rows,
                        "runtime_rows": runtime_rows,
                    },
                    checkpoint_path,
                )
            del gpu, source
            gc.collect()
            release_cupy_memory_pool()

    gate = parsed["gates"]
    expected_runtime_targets = gate["expected_targets"] if all_cache_safe else 0
    expected_warm_steps = gate["expected_warm_steps_if_safe"] if all_cache_safe else 0
    all_runtime_arms = [
        arm for row in runtime_rows for arm in row["arms"].values()
    ]
    all_cache_arms = [arm for row in cache_rows for arm in row["arms"].values()]
    actual_inventory_sha256 = _inventory_digest(inventory_rows)
    checkpoint_actual_sha256 = _sha256(checkpoint_path)
    target_by_id = {row["target_id"]: row for row in runtime_rows}
    admitted_positions = [
        acting_player
        for acting_player in parsed["acting_player_order"]
        if all_cache_safe
        and all(
            target_by_id[spec["target_id"]]["arms"]["two_size"]["capacity"][
                "fits_street"
            ]
            for spec in specs
            if spec["acting_player"] == acting_player
        )
    ]
    maximum_master_primal = max(
        (
            max(
                arm["master"]["maximum_equality_error"],
                arm["master"]["maximum_inequality_violation"],
                arm["master"]["maximum_bound_violation"],
            )
            for arm in all_runtime_arms
        ),
        default=0.0,
    )
    maximum_master_dual = max(
        (
            max(
                arm["master"]["maximum_stationarity_error"],
                arm["master"]["maximum_complementarity_error"],
                arm["master"]["duality_gap"],
            )
            for arm in all_runtime_arms
        ),
        default=0.0,
    )
    elapsed = time.perf_counter() - started
    checks = {
        "clean_git": (not git["dirty"]) == gate["require_clean_git_state"],
        "parents_passed": (
            artifact_passed(source_parent)
            and source_config["source_order"]
            == [row["source"] for row in parsed["sources"]]
            and len(decision_plan["target_plan"]) == gate["expected_sources"]
        )
        == gate["require_parents_passed"],
        "inventory_identity": (
            len(specs) == gate["expected_targets"]
            and len(inventory_rows) == gate["expected_targets"]
            and actual_inventory_sha256 == parsed["expected_inventory_sha256"]
        )
        == gate["require_inventory_identity"],
        "source_checkpoint_identity": all(
            row["source_identity"] for row in cache_rows
        )
        == gate["require_source_checkpoint_identity"],
        "target_identity": (
            len({row["target_id"] for row in inventory_rows})
            == gate["expected_targets"]
            and len({row["target_belief_sha256"] for row in inventory_rows})
            == gate["expected_targets"]
        )
        == gate["require_target_identity"],
        "blueprint_identity": all(
            len(arm["blueprint_sha256"]) == 64
            and (
                not all_cache_safe
                or arm["blueprint_sha256"]
                == target_by_id[row["target_id"]]["arms"][arm_name][
                    "blueprint_sha256"
                ]
            )
            for row in cache_rows
            for arm_name, arm in row["arms"].items()
        )
        == gate["require_blueprint_identity"],
        "cache_count": (
            len(all_cache_arms) == gate["expected_arms"]
            and len(all_cache_arms) == gate["expected_cache_rows"]
        ),
        "geometry": all(
            row["arms"]["one_size"]["geometry"]["public_nodes"]
            == gate["expected_one_size_public_nodes_by_actor"][row["acting_player"]]
            and row["arms"]["two_size"]["geometry"]["public_nodes"]
            == gate["expected_two_size_public_nodes_by_actor"][row["acting_player"]]
            and row["arms"]["one_size"]["geometry"]["terminal_groups"]
            == gate["expected_one_size_terminal_groups_by_actor"][
                row["acting_player"]
            ]
            and row["arms"]["two_size"]["geometry"]["terminal_groups"]
            == gate["expected_two_size_terminal_groups_by_actor"][
                row["acting_player"]
            ]
            and row["arms"]["one_size"]["geometry"]["root_player"]
            == row["acting_player"]
            and row["arms"]["two_size"]["geometry"]["root_player"]
            == row["acting_player"]
            and row["arms"]["one_size"]["geometry"]["root_action_width"] == 2
            and row["arms"]["two_size"]["geometry"]["root_action_width"] == 3
            for row in cache_rows
        ),
        "conditional_barrier": (
            len(runtime_rows) == expected_runtime_targets
            and len(all_runtime_arms) == expected_warm_steps
        )
        == gate["require_conditional_barrier"],
        "warm_identity": all(
            arm["warm_start_distance"]["maximum_probability_error"]
            <= gate["maximum_warm_start_probability_error"]
            and arm["warm_start_distance"]["mean_total_variation"]
            <= gate["maximum_warm_start_mean_total_variation"]
            for arm in all_runtime_arms
        ),
        "initial_rows": all(
            arm["initial_profile_passes"] == 6
            and arm["initial_response_passes"] == 5
            and arm["initial_gain_rows"] == gate["expected_initial_gain_rows_per_arm"]
            and len(arm["initial_pass_rows"])
            == gate["expected_initial_passes_per_arm"]
            and arm["maximum_source_row_error"] <= gate["maximum_source_row_error"]
            for arm in all_runtime_arms
        ),
        "master_numerics": (
            maximum_master_primal <= gate["maximum_master_primal_error"]
            and maximum_master_dual <= gate["maximum_master_dual_error"]
            and all(
                arm["candidate_projection_error"]
                <= gate["maximum_projection_error"]
                for arm in all_runtime_arms
            )
            and all(
                arm["master"]["solve_ms"] <= gate["maximum_master_ms"]
                for arm in all_runtime_arms
            )
        ),
        "current_node_only": all(
            arm["current_node_information_sets"]
            == gate["expected_current_information_sets"]
            and arm["current_node_policy_variables"]
            == (
                gate["expected_one_size_policy_variables"]
                if arm["arm"] == "one_size"
                else gate["expected_two_size_policy_variables"]
            )
            and set(arm["candidate_changed_public_nodes"]).issubset({0})
            for arm in all_runtime_arms
        )
        == gate["require_current_node_only"],
        "off_node_immutable": all(
            arm["off_node_policy_immutable"] for arm in all_runtime_arms
        )
        == gate["require_off_node_immutable"],
        "resource_caps": (
            all(
                arm["cache"]["device_cache_compile_ms"]
                <= gate["maximum_cache_compile_ms"]
                and arm["cache"]["pool_total_bytes"]
                <= gate["maximum_gpu_pool_bytes"]
                and arm["cache"]["physical_device_free_bytes"]
                >= gate["minimum_physical_free_bytes"]
                for arm in all_cache_arms
            )
            and all(
                arm["warm_step"]["wall_ms"] <= gate["maximum_warm_step_ms"]
                and arm["initial_row_ms"] <= gate["maximum_initial_row_ms"]
                for arm in all_runtime_arms
            )
            and elapsed <= float(parsed["maximum_campaign_seconds"])
        ),
        "checkpoint_bytes_truth": (
            checkpoint_sha256 == checkpoint_actual_sha256
        )
        == gate["require_checkpoint_bytes_truth"],
        "baseline_evaluation_count": sum(
            arm["baseline_seat_evaluations"] for arm in all_runtime_arms
        )
        == (
            gate["expected_baseline_seat_evaluations_if_safe"]
            if all_cache_safe
            else 0
        ),
        "zero_candidate_evaluations": all(
            arm["master_candidate_evaluations"] == 0
            and arm["retreat_evaluations"] == 0
            and arm["strategy_quality_rows_serialized"] == 0
            and arm["optimizer_value_fields_serialized"] == 0
            for arm in all_runtime_arms
        )
        == gate["require_zero_candidate_evaluations"],
        "blueprint_emission": True == gate["require_blueprint_emission"],
        "strategy_population_claim_null": True
        == gate["require_strategy_population_claim_null"],
        "finite": _finite_tree((cache_rows, runtime_rows))
        == gate["require_finite"],
    }
    gate_result = finalize_gates(checks)
    position_rows = [
        {
            "acting_player": acting_player,
            "targets": sum(
                row["acting_player"] == acting_player for row in runtime_rows
            ),
            "one_size_all_fit": bool(
                all_cache_safe
                and all(
                    row["arms"]["one_size"]["capacity"]["fits_street"]
                    for row in runtime_rows
                    if row["acting_player"] == acting_player
                )
            ),
            "two_size_all_fit": acting_player in admitted_positions,
            "maximum_one_size_proxy_ms": max(
                (
                    row["arms"]["one_size"]["capacity"][
                        "complete_one_round_proxy_ms"
                    ]
                    for row in runtime_rows
                    if row["acting_player"] == acting_player
                ),
                default=None,
            ),
            "maximum_two_size_proxy_ms": max(
                (
                    row["arms"]["two_size"]["capacity"][
                        "complete_one_round_proxy_ms"
                    ]
                    for row in runtime_rows
                    if row["acting_player"] == acting_player
                ),
                default=None,
            ),
        }
        for acting_player in parsed["acting_player_order"]
    ]
    result = {
        "schema_version": 1,
        "status": "h32_pre_bet_action_width_capacity_executed",
        "environment": assemble_environment(runtime=runtime, git=git),
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "checkpoint_sha256": checkpoint_actual_sha256,
        "methodology": {
            "sources": gate["expected_sources"],
            "targets": len(cache_rows),
            "cache_arms": len(all_cache_arms),
            "warm_steps": len(all_runtime_arms),
            "baseline_optimizer_seat_evaluations": 6 * len(all_runtime_arms),
            "master_candidates_constructed_not_evaluated": len(all_runtime_arms),
            "master_candidate_endpoint_evaluations": 0,
            "retreat_or_certificate_evaluations": 0,
            "strategy_quality_rows_serialized": 0,
            "candidate_policies_emitted": 0,
        },
        "inventory_sha256": actual_inventory_sha256,
        "all_cache_safe_for_runtime": all_cache_safe,
        "cache_rows": cache_rows,
        "runtime_rows": runtime_rows,
        "position_rows": position_rows,
        "aggregate": {
            "admitted_acting_players": admitted_positions,
            "admitted_position_count": len(admitted_positions),
            "two_size_fits_by_position": {
                str(row["acting_player"]): row["two_size_all_fit"]
                for row in position_rows
            },
            "maximum_gpu_pool_total_bytes": max(
                arm["cache"]["pool_total_bytes"] for arm in all_cache_arms
            ),
            "minimum_physical_free_bytes": min(
                arm["cache"]["physical_device_free_bytes"]
                for arm in all_cache_arms
            ),
            "maximum_source_row_error": max(
                (arm["maximum_source_row_error"] for arm in all_runtime_arms),
                default=0.0,
            ),
            "maximum_master_primal_error": maximum_master_primal,
            "maximum_master_dual_error": maximum_master_dual,
            "arm_fit_counts": dict(
                Counter(
                    arm_name
                    for row in runtime_rows
                    for arm_name, arm in row["arms"].items()
                    if arm["capacity"]["fits_street"]
                )
            ),
        },
        **gate_result,
        "decision": (
            "authorize_position_scoped_widened_quality_preregistration"
            if gate_result["passed"] and admitted_positions
            else "memory_unsafe_stop_before_runtime"
            if gate_result["passed"] and not all_cache_safe
            else "no_position_supports_complete_widened_proxy_retain_one_size"
            if gate_result["passed"]
            else "reject_pre_bet_action_width_capacity_execution"
        ),
        "actual_emitted_policy": "immutable_one_size_blueprint_only",
        "strategy_population_claim": None,
        "total_seconds": elapsed,
        "limitations": [
            (
                "Capacity uses no evaluated master candidate; endpoint-oracle "
                "cost is conservatively proxied by max(source oracle, warm step)."
            ),
            (
                "Targets are the Cartesian product of retained sources and "
                "positions, not an IID deployment sample."
            ),
            (
                "Any admitted position authorizes only a separately frozen "
                "strategy-quality trial with exact certification."
            ),
        ],
    }
    output_path.write_text(serialize_result(result), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, default=_CHECKPOINT)
    args = parser.parse_args()
    result = run_h32_pre_bet_action_width_capacity(
        args.config,
        args.output,
        args.checkpoint,
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
