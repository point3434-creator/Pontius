"""One-shot label-free capacity preflight for literal full-width river work.

The target is the accepted ADR-0290 one-seat card belief lifted to six seat
axes by inserting the controlled private hand as a singleton.  Before the
current FactorTT lineage may allocate its explicit half-assignment topology,
an exact numeric-array lower bound is compared with frozen host/device caps and
live physical headroom.  A failed guard is a complete representation result;
it performs zero target topology builds, contractions, warm steps, actions, or
quality evaluations.

A reduced, outcome-free GPU control exercises the complete compile, scalar
contraction, resident priming contraction, and identical warm contraction path.
Its values are compared internally and never serialized.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import platform
import subprocess
import time
from collections.abc import Mapping
from ctypes import wintypes
from math import comb
from pathlib import Path
from typing import Any

import numpy as np

from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    _cupy_modules,
    release_cupy_memory_pool,
)
from .factor_tt_contraction import FactorTTBeliefWorkspace, FactorTTTopology
from .factorized_belief import FactorizedCardBelief
from .full_width_belief import FullWidthOneSeatBelief
from .full_width_factor_tt_capacity import (
    FactorTTHalfAllocation,
    FactorTTPersistentAllocation,
    canonical_six_seat_river_allocation,
    minimum_scalar_topology_numeric_bytes,
)
from .heterogeneous_leaf_contraction import HeterogeneousLeafTerm
from .holdem_cards import OneSeatCardState
from .no_limit_betting import BettingStreet
from .open_mode_factor_tt import (
    BidirectionalFactorTTTopology,
    OpenModeFactorTTWorkspace,
)
from .resident_heterogeneous_leaf_contraction import (
    CuPyResidentAutomatonCache,
    CuPyResidentBeliefCache,
    contract_resident_heterogeneous_leaf_terms,
)
from .river import evaluate_seven, make_hole, parse_cards
from .runner_harness_v2 import load_config
from .sparse_incidence_open_mode import SparseBidirectionalIncidence
from .structured_showdown_automaton import build_structured_showdown_automaton

_ROOT = Path(__file__).parents[2]
_CONFIG = _ROOT / "experiments/configs/full-width-river-capacity-preflight-v1.json"
_OUTPUT = _ROOT / "experiments/results/full-width-river-capacity-preflight-v1.json"
_IMPLEMENTATION = Path(__file__)
_MODEL = _ROOT / "src/pontius/full_width_factor_tt_capacity.py"
_CONTROL_TEST = _ROOT / "tests/test_full_width_river_capacity_preflight.py"
_PARENT_DECISION = (
    _ROOT
    / "docs/decisions/ADR-0362-retain-the-rejected-terminal-and-rebind-its-scientific-payload.md"
)

_PATHS = {
    "expected_parent_decision_sha256": _PARENT_DECISION,
    "expected_capacity_model_sha256": _MODEL,
    "expected_full_width_belief_sha256": _ROOT / "src/pontius/full_width_belief.py",
    "expected_factorized_belief_sha256": _ROOT / "src/pontius/factorized_belief.py",
    "expected_factor_tt_sha256": _ROOT / "src/pontius/factor_tt_contraction.py",
    "expected_open_mode_sha256": _ROOT / "src/pontius/open_mode_factor_tt.py",
    "expected_sparse_incidence_sha256": (
        _ROOT / "src/pontius/sparse_incidence_open_mode.py"
    ),
    "expected_cupy_incidence_sha256": _ROOT / "src/pontius/cupy_sparse_incidence.py",
    "expected_resident_contraction_sha256": (
        _ROOT / "src/pontius/resident_heterogeneous_leaf_contraction.py"
    ),
    "expected_showdown_automaton_sha256": (
        _ROOT / "src/pontius/structured_showdown_automaton.py"
    ),
    "expected_holdem_cards_sha256": _ROOT / "src/pontius/holdem_cards.py",
    "expected_river_sha256": _ROOT / "src/pontius/river.py",
    "expected_strict_loader_sha256": _ROOT / "src/pontius/runner_harness_v2.py",
    "expected_implementation_sha256": _IMPLEMENTATION,
    "expected_control_test_sha256": _CONTROL_TEST,
}

_STREETS = (
    BettingStreet.PREFLOP,
    BettingStreet.FLOP,
    BettingStreet.TURN,
    BettingStreet.RIVER,
)


def _canonical_lf_sha256(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required full-width capacity source is absent: {path}")
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _parse_config(config: Mapping[str, Any]) -> dict[str, Any]:
    plain = _plain(config)
    expected_fields = {
        "schema_version",
        "evidence_stage",
        "hash_semantics",
        *_PATHS,
        "controlled_seat",
        "private_hand",
        "board",
        "street_widths",
        "players",
        "split_index",
        "component_count",
        "control_opponent_hands",
        "showdown_pot_chips",
        "showdown_bet_chips",
        "target_workload",
        "warm_measurement",
        "preparation_scope",
        "charged_scope",
        "failure_interpretation",
        "claims_policy",
        "required_numpy_version",
        "required_scipy_version",
        "required_cupy_version",
        "required_cuda_runtime_version",
        "minimum_cuda_driver_version",
        "required_compute_capability",
        "required_device_name",
        "gates",
    }
    if set(plain) != expected_fields:
        raise ValueError("full-width capacity config fields differ from ADR-0363")
    for field, path in _PATHS.items():
        if plain[field] != _canonical_lf_sha256(path):
            raise ValueError(f"full-width capacity provenance mismatch: {field}")

    frozen = {
        "schema_version": "full-width-river-capacity-preflight-config-v1",
        "evidence_stage": (
            "preregistered_after_adr0362_before_any_live_literal_full_width_"
            "hardware_capacity_invocation"
        ),
        "hash_semantics": "canonical_lf_sha256_for_bound_text_sources",
        "controlled_seat": 3,
        "private_hand": ["Ks", "Td"],
        "board": ["2c", "7d", "9h", "Js", "Qc"],
        "street_widths": [1225, 1081, 1035, 990],
        "players": 6,
        "split_index": 3,
        "component_count": 1,
        "control_opponent_hands": 12,
        "showdown_pot_chips": 12.0,
        "showdown_bet_chips": 0.0,
        "target_workload": (
            "fixed_hero_six_live_seat_showdown_one_scalar_contraction_"
            "one_resident_prime_one_identical_resident_warm_contraction"
        ),
        "warm_measurement": (
            "second_identical_resident_leaf_contraction_after_one_priming_call_"
            "not_a_cfr_iteration_or_complete_solve"
        ),
        "preparation_scope": (
            "compact_belief_topology_workspace_sparse_operator_automaton_"
            "and_resident_cache_construction"
        ),
        "charged_scope": (
            "one_identical_warm_resident_leaf_contraction_only_with_"
            "fourteen_second_compute_ceiling_inside_fifteen_second_action_wall"
        ),
        "failure_interpretation": (
            "a_numeric_lower_bound_over_any_frozen_resource_cap_rejects_before_"
            "target_allocation_and_triggers_representation_work_without_"
            "authorizing_truncation"
        ),
        "claims_policy": (
            "literal_full_width_representation_memory_and_warm_contraction_"
            "capacity_only_no_action_strategy_quality_strength_or_cfr_solve_claim"
        ),
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13030,
        "required_compute_capability": "120",
        "required_device_name": "NVIDIA GeForce RTX 5080",
    }
    for field, value in frozen.items():
        if plain[field] != value:
            raise ValueError(f"full-width capacity field differs from ADR-0363: {field}")

    expected_gates = {
        "maximum_host_persistent_numeric_bytes": 48_000_000_000,
        "maximum_device_resident_numeric_bytes": 12_000_000_000,
        "minimum_host_free_reserve_bytes": 8_000_000_000,
        "minimum_device_free_reserve_bytes": 2_000_000_000,
        "street_action_wall_ms": 15_000.0,
        "emission_reserve_ms": 1_000.0,
        "maximum_warm_contraction_ms": 14_000.0,
        "maximum_control_error": 1e-10,
        "maximum_control_wall_seconds": 30.0,
        "maximum_target_construction_seconds": 600.0,
        "maximum_campaign_seconds": 900.0,
        "maximum_result_bytes": 1_048_576,
        "minimum_host_total_bytes": 60_000_000_000,
        "maximum_host_total_bytes": 70_000_000_000,
        "minimum_device_total_bytes": 16_000_000_000,
        "maximum_device_total_bytes": 18_000_000_000,
        "require_clean_git_state": True,
        "require_exact_street_axes": True,
        "require_exact_compatible_record_arithmetic": True,
        "require_optimistic_scalar_cross_check": True,
        "require_preallocation_guard_before_target_topology": True,
        "require_reduced_complete_path_control": True,
        "require_typed_terminal": True,
        "require_zero_cartesian_materialization": True,
        "require_zero_actions_strategy_labels_and_quality_rows": True,
        "require_finite": True,
    }
    if plain["gates"] != expected_gates:
        raise ValueError("full-width capacity gates differ from ADR-0363")
    if (
        expected_gates["maximum_warm_contraction_ms"]
        + expected_gates["emission_reserve_ms"]
        != expected_gates["street_action_wall_ms"]
    ):
        raise ValueError("full-width charged and emission walls do not sum to 15 seconds")
    return {
        **plain,
        "private_hand": tuple(plain["private_hand"]),
        "board": tuple(plain["board"]),
        "street_widths": tuple(plain["street_widths"]),
        "gates": dict(plain["gates"]),
    }


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


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = (
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    )


class _ProcessMemoryCountersEx(ctypes.Structure):
    _fields_ = (
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    )


def _host_memory_snapshot() -> dict[str, int]:
    if os.name != "nt":
        raise RuntimeError("the frozen full-width capacity host is Windows")
    status = _MemoryStatusEx()
    status.dwLength = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("GlobalMemoryStatusEx failed")
    counters = _ProcessMemoryCountersEx()
    counters.cb = ctypes.sizeof(counters)
    process = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(
        process,
        ctypes.byref(counters),
        counters.cb,
    ):
        raise OSError("GetProcessMemoryInfo failed")
    return {
        "host_total_physical_bytes": int(status.ullTotalPhys),
        "host_available_physical_bytes": int(status.ullAvailPhys),
        "process_working_set_bytes": int(counters.WorkingSetSize),
        "process_peak_working_set_bytes": int(counters.PeakWorkingSetSize),
        "process_private_bytes": int(counters.PrivateUsage),
    }


def _runtime_snapshot(parsed: Mapping[str, Any]) -> tuple[Any, dict[str, object]]:
    import scipy

    cp, _ = _cupy_modules()
    device_name = cp.cuda.runtime.getDeviceProperties(0)["name"]
    if isinstance(device_name, bytes):
        device_name = device_name.decode("ascii")
    runtime = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "cupy": cp.__version__,
        "cuda_runtime": int(cp.cuda.runtime.runtimeGetVersion()),
        "cuda_driver": int(cp.cuda.runtime.driverGetVersion()),
        "compute_capability": str(cp.cuda.Device(0).compute_capability),
        "device_name": str(device_name),
    }
    required_equal = {
        "numpy": parsed["required_numpy_version"],
        "scipy": parsed["required_scipy_version"],
        "cupy": parsed["required_cupy_version"],
        "cuda_runtime": parsed["required_cuda_runtime_version"],
        "compute_capability": parsed["required_compute_capability"],
        "device_name": parsed["required_device_name"],
    }
    for field, expected in required_equal.items():
        if runtime[field] != expected:
            raise RuntimeError(f"full-width capacity runtime differs: {field}")
    if runtime["cuda_driver"] < parsed["minimum_cuda_driver_version"]:
        raise RuntimeError("CUDA driver is below the full-width capacity floor")
    free, total = cp.cuda.runtime.memGetInfo()
    return cp, {
        **runtime,
        **_host_memory_snapshot(),
        "device_free_bytes": int(free),
        "device_total_bytes": int(total),
    }


def _six_axis_belief(
    belief: FullWidthOneSeatBelief,
) -> FactorizedCardBelief:
    hero = belief.cards.controlled_seat
    hands = tuple(
        (belief.cards.private_hand,) if seat == hero else belief.hand_axis
        for seat in range(6)
    )
    unaries = []
    for seat in range(6):
        if seat == hero:
            unaries.append(np.ones((1, 1), dtype=np.float64))
        else:
            index = belief.opponent_seats.index(seat)
            unaries.append(belief.factorized.unary_weights[index])
    return FactorizedCardBelief(
        hands_by_player=hands,
        mixture_weights=belief.factorized.mixture_weights,
        unary_weights=tuple(unaries),
        board=belief.cards.board,
    )


def _strength_codes(
    belief: FactorizedCardBelief,
) -> tuple[np.ndarray, ...]:
    ranks = tuple(
        tuple(evaluate_seven((*belief.board, *hand)) for hand in axis)
        for axis in belief.hands_by_player
    )
    ordered = tuple(sorted({rank for axis in ranks for rank in axis}))
    code = {rank: index for index, rank in enumerate(ordered)}
    return tuple(
        np.ascontiguousarray([code[rank] for rank in axis], dtype=np.int32)
        for axis in ranks
    )


def _workload_automaton(
    belief: FactorizedCardBelief,
    *,
    controlled_seat: int,
    pot_chips: float,
    bet_chips: float,
) -> Any:
    return build_structured_showdown_automaton(
        strength_codes=_strength_codes(belief),
        contenders=tuple(range(6)),
        target_player=controlled_seat,
        contributed=False,
        pot=pot_chips,
        bet_size=bet_chips,
    )


def _resident_workload(
    belief: FactorizedCardBelief,
    *,
    controlled_seat: int,
    split_index: int,
    pot_chips: float,
    bet_chips: float,
) -> dict[str, object]:
    """Compile and measure one scalar, one prime, and one warm contraction."""

    construction_started = time.perf_counter()
    topology = FactorTTTopology.compile(belief, split_index=split_index)
    bidirectional = BidirectionalFactorTTTopology.compile(topology)
    base = FactorTTBeliefWorkspace.compile(topology, belief)
    workspace = OpenModeFactorTTWorkspace.compile(bidirectional, base)
    sparse = SparseBidirectionalIncidence.compile(workspace)
    automaton = _workload_automaton(
        belief,
        controlled_seat=controlled_seat,
        pot_chips=pot_chips,
        bet_chips=bet_chips,
    )
    train = automaton.to_tensor_train()
    scalar = base.contract(train)
    gpu = CuPyBidirectionalIncidence.compile(sparse)
    belief_cache = CuPyResidentBeliefCache.compile(workspace)
    automaton_cache = CuPyResidentAutomatonCache.compile(
        workspace,
        {"showdown": automaton},
        target_seat=controlled_seat,
    )
    construction_ms = (time.perf_counter() - construction_started) * 1000.0
    term = HeterogeneousLeafTerm(
        key=0,
        automaton=automaton,
        mode_factors=tuple(
            np.ones(count, dtype=np.float64) for count in belief.hand_counts
        ),
    )
    common = {
        "target_seat": controlled_seat,
        "belief_cache": belief_cache,
        "automaton_cache": automaton_cache,
        "cupy_sparse": gpu,
        "maximum_feature_width_per_batch": 384,
    }
    prime_started = time.perf_counter()
    prime = contract_resident_heterogeneous_leaf_terms(
        workspace,
        sparse,
        (term,),
        **common,
    )
    prime_ms = (time.perf_counter() - prime_started) * 1000.0
    warm_started = time.perf_counter()
    warm = contract_resident_heterogeneous_leaf_terms(
        workspace,
        sparse,
        (term,),
        **common,
    )
    warm_ms = (time.perf_counter() - warm_started) * 1000.0

    first = prime.for_key(0)
    second = warm.for_key(0)
    repeat_error = max(
        float(
            np.max(
                np.abs(
                    first.root_normalized_numerators
                    - second.root_normalized_numerators
                )
            )
        ),
        float(
            np.max(
                np.abs(
                    first.root_normalized_reaches - second.root_normalized_reaches
                )
            )
        ),
    )
    resident_expectation = second.reach_conditioned_expectation
    expectation_error = (
        math.inf
        if resident_expectation is None
        else abs(float(resident_expectation) - scalar.expectation)
    )
    allocation = FactorTTPersistentAllocation(
        hand_counts=belief.hand_counts,
        split_index=split_index,
        left=FactorTTHalfAllocation(split_index, topology.left.records),
        right=FactorTTHalfAllocation(6 - split_index, topology.right.records),
        component_count=belief.component_count,
        forward_incidence_entries=topology.incidence_entries,
        reverse_incidence_entries=bidirectional.reverse_incidence_entries,
    )
    pool = _cupy_modules()[0].get_default_memory_pool()
    record = {
        "construction_ms": construction_ms,
        "prime_contraction_ms": prime_ms,
        "warm_contraction_ms": warm_ms,
        "scalar_middle_rank": scalar.middle_rank,
        "automaton_maximum_state_rank": automaton.maximum_state_rank,
        "automaton_numeric_bytes": automaton.numeric_bytes,
        "tensor_train_storage_bytes": train.storage_bytes,
        "topology_numeric_bytes": topology.numeric_bytes,
        "bidirectional_topology_numeric_bytes": bidirectional.numeric_bytes,
        "base_workspace_numeric_bytes": base.numeric_bytes,
        "open_workspace_numeric_bytes": workspace.numeric_bytes,
        "sparse_operator_numeric_bytes": sparse.numeric_bytes,
        "resident_belief_numeric_bytes": belief_cache.numeric_bytes,
        "resident_automaton_numeric_bytes": automaton_cache.numeric_bytes,
        "maximum_gpu_pool_used_bytes": max(
            prime.work.maximum_gpu_pool_used_bytes,
            warm.work.maximum_gpu_pool_used_bytes,
            int(pool.used_bytes()),
        ),
        "maximum_gpu_pool_total_bytes": max(
            prime.work.maximum_gpu_pool_total_bytes,
            warm.work.maximum_gpu_pool_total_bytes,
            int(pool.total_bytes()),
        ),
        "prime_warm_maximum_repeat_error": repeat_error,
        "scalar_resident_expectation_error": expectation_error,
        "allocation_model_matches": {
            "base_topology": allocation.base_topology_numeric_bytes
            == topology.numeric_bytes,
            "bidirectional_topology": (
                allocation.bidirectional_topology_numeric_bytes
                == bidirectional.numeric_bytes
            ),
            "base_workspace": allocation.base_workspace_numeric_bytes
            == base.numeric_bytes,
            "open_workspace": allocation.open_workspace_numeric_bytes
            == workspace.numeric_bytes,
            "resident_belief": allocation.resident_belief_numeric_bytes
            == belief_cache.numeric_bytes,
        },
        "finite": all(
            math.isfinite(value)
            for value in (
                construction_ms,
                prime_ms,
                warm_ms,
                repeat_error,
                expectation_error,
            )
        ),
        "strategy_quality_evaluations": 0,
        "actions_emitted": 0,
        "strategy_labels_emitted": 0,
        "quality_rows_emitted": 0,
    }
    del warm, prime, term, automaton_cache, belief_cache, gpu, train, automaton
    del sparse, workspace, base, bidirectional, topology
    release_cupy_memory_pool()
    return record


def _small_control(parsed: Mapping[str, Any]) -> dict[str, object]:
    board = parse_cards(*parsed["board"])
    hero = make_hole(*parsed["private_hand"])
    remaining = tuple(card for card in range(52) if card not in {*board, *hero})
    count = parsed["control_opponent_hands"]
    opponent_axis = tuple(
        make_hole(remaining[index], remaining[index + 1])
        for index in range(0, 2 * count, 2)
    )
    hands = tuple((hero,) if seat == parsed["controlled_seat"] else opponent_axis for seat in range(6))
    belief = FactorizedCardBelief(
        hands_by_player=hands,
        mixture_weights=np.ones(1, dtype=np.float64),
        unary_weights=tuple(
            np.ones((1, len(axis)), dtype=np.float64) for axis in hands
        ),
        board=board,
    )
    wall_started = time.perf_counter()
    workload = _resident_workload(
        belief,
        controlled_seat=parsed["controlled_seat"],
        split_index=parsed["split_index"],
        pot_chips=parsed["showdown_pot_chips"],
        bet_chips=parsed["showdown_bet_chips"],
    )
    return {
        "opponent_hands_per_axis": count,
        "hand_counts": list(belief.hand_counts),
        "cartesian_assignments": belief.cartesian_assignments,
        "wall_seconds": time.perf_counter() - wall_started,
        "workload": workload,
    }


def _street_inventory(parsed: Mapping[str, Any]) -> tuple[FullWidthOneSeatBelief, list[dict[str, object]]]:
    hero = make_hole(*parsed["private_hand"])
    board = parse_cards(*parsed["board"])
    cards = OneSeatCardState.preflop(
        controlled_seat=parsed["controlled_seat"],
        private_hand=hero,
    )
    belief = FullWidthOneSeatBelief.uniform(cards)
    rows = []
    for index, street in enumerate(_STREETS):
        if belief.cards.street is not street:
            raise AssertionError("full-width capacity street progression drifted")
        snapshot = belief.snapshot()
        rows.append(
            {
                "street": street.value,
                "opponent_hand_counts": list(snapshot.opponent_hand_counts),
                "cartesian_assignments": snapshot.cartesian_assignments,
                "compatible_assignments": snapshot.compatible_assignments,
                "persistent_numeric_bytes": snapshot.persistent_numeric_bytes,
                "known_cards": len(belief.cards.known_cards),
                "digest": snapshot.digest,
            }
        )
        if street is BettingStreet.RIVER:
            continue
        next_street = _STREETS[index + 1]
        reveal_start = len(belief.cards.board)
        reveal_count = 3 if next_street is BettingStreet.FLOP else 1
        cards = belief.cards.advance_to(
            next_street,
            board[reveal_start : reveal_start + reveal_count],
        )
        belief = belief.advance_to(cards)
    return belief, rows


def _capacity_admission(
    *,
    allocation: FactorTTPersistentAllocation,
    optimistic_scalar_bytes: int,
    host_available_bytes: int,
    device_free_bytes: int,
    gates: Mapping[str, Any],
) -> dict[str, bool]:
    checks = {
        "optimistic_scalar_within_host_numeric_cap": (
            optimistic_scalar_bytes <= gates["maximum_host_persistent_numeric_bytes"]
        ),
        "bidirectional_topology_within_host_numeric_cap": (
            allocation.bidirectional_topology_numeric_bytes
            <= gates["maximum_host_persistent_numeric_bytes"]
        ),
        "bidirectional_topology_preserves_live_host_reserve": (
            allocation.bidirectional_topology_numeric_bytes
            + gates["minimum_host_free_reserve_bytes"]
            <= host_available_bytes
        ),
        "resident_belief_within_device_numeric_cap": (
            allocation.resident_belief_numeric_bytes
            <= gates["maximum_device_resident_numeric_bytes"]
        ),
        "resident_belief_preserves_live_device_reserve": (
            allocation.resident_belief_numeric_bytes
            + gates["minimum_device_free_reserve_bytes"]
            <= device_free_bytes
        ),
    }
    return checks


def _run_target(
    parsed: Mapping[str, Any],
    *,
    runtime: Mapping[str, Any],
    control: Mapping[str, Any],
) -> dict[str, object]:
    target_started = time.perf_counter()
    river_belief, streets = _street_inventory(parsed)
    available_cards = len(river_belief.cards.remaining_deck)
    allocation = canonical_six_seat_river_allocation(
        controlled_seat=parsed["controlled_seat"],
        opponent_hand_count=len(river_belief.hand_axis),
        available_cards=available_cards,
        split_index=parsed["split_index"],
        component_count=parsed["component_count"],
    )
    optimistic = minimum_scalar_topology_numeric_bytes(
        opponent_hand_count=len(river_belief.hand_axis),
        available_cards=available_cards,
        component_count=parsed["component_count"],
    )
    admission_checks = _capacity_admission(
        allocation=allocation,
        optimistic_scalar_bytes=optimistic,
        host_available_bytes=runtime["host_available_physical_bytes"],
        device_free_bytes=runtime["device_free_bytes"],
        gates=parsed["gates"],
    )
    admitted = all(admission_checks.values())
    workload = None
    if admitted:
        workload = _resident_workload(
            _six_axis_belief(river_belief),
            controlled_seat=parsed["controlled_seat"],
            split_index=parsed["split_index"],
            pot_chips=parsed["showdown_pot_chips"],
            bet_chips=parsed["showdown_bet_chips"],
        )
        terminal = "literal_full_width_warm_contraction_completed"
    else:
        terminal = "representation_rejected_before_target_allocation"

    expected_widths = parsed["street_widths"]
    exact_axes = all(
        row["opponent_hand_counts"] == [expected_widths[index]] * 5
        for index, row in enumerate(streets)
    )
    explicit_left = comb(45, 2) * comb(43, 2) * comb(41, 2)
    explicit_right = comb(45, 2) * comb(43, 2)
    control_workload = control["workload"]
    control_passed = bool(
        control["wall_seconds"] <= parsed["gates"]["maximum_control_wall_seconds"]
        and control_workload["prime_warm_maximum_repeat_error"]
        <= parsed["gates"]["maximum_control_error"]
        and control_workload["scalar_resident_expectation_error"]
        <= parsed["gates"]["maximum_control_error"]
        and all(control_workload["allocation_model_matches"].values())
        and control_workload["finite"]
    )
    conditional_workload = (
        workload is None
        if not admitted
        else bool(
            workload["warm_contraction_ms"]
            <= parsed["gates"]["maximum_warm_contraction_ms"]
            and workload["prime_warm_maximum_repeat_error"]
            <= parsed["gates"]["maximum_control_error"]
            and workload["scalar_resident_expectation_error"]
            <= parsed["gates"]["maximum_control_error"]
            and all(workload["allocation_model_matches"].values())
            and workload["finite"]
        )
    )
    target_seconds = time.perf_counter() - target_started
    gates = {
        "exact_street_axes": exact_axes,
        "exact_compatible_record_arithmetic": (
            allocation.left.records == explicit_left
            and allocation.right.records == explicit_right
        ),
        "optimistic_scalar_cross_check": (
            optimistic <= allocation.base_topology_numeric_bytes
        ),
        "preallocation_guard_before_target_topology": (
            admitted == all(admission_checks.values())
            and ((admitted and workload is not None) or (not admitted and workload is None))
        ),
        "reduced_complete_path_control": control_passed,
        "typed_terminal": terminal
        in {
            "literal_full_width_warm_contraction_completed",
            "representation_rejected_before_target_allocation",
        },
        "zero_cartesian_materialization": True,
        "zero_actions_strategy_labels_and_quality_rows": (
            control_workload["actions_emitted"] == 0
            and control_workload["strategy_labels_emitted"] == 0
            and control_workload["quality_rows_emitted"] == 0
            and control_workload["strategy_quality_evaluations"] == 0
            and (
                workload is None
                or (
                    workload["actions_emitted"] == 0
                    and workload["strategy_labels_emitted"] == 0
                    and workload["quality_rows_emitted"] == 0
                    and workload["strategy_quality_evaluations"] == 0
                )
            )
        ),
        "target_unit_within_bound": (
            target_seconds <= parsed["gates"]["maximum_target_construction_seconds"]
        ),
        "conditional_warm_contraction": conditional_workload,
        "finite": math.isfinite(target_seconds),
    }
    return {
        "street_inventory": streets,
        "river_semantics": {
            "controlled_seat": parsed["controlled_seat"],
            "controlled_hand": list(parsed["private_hand"]),
            "board": list(parsed["board"]),
            "opponent_axes": 5,
            "opponent_hand_count": len(river_belief.hand_axis),
            "available_cards": available_cards,
            "cartesian_assignments": river_belief.cartesian_assignments,
            "compatible_assignments": river_belief.compatible_assignments,
            "belief_digest": river_belief.digest,
        },
        "allocation_lower_bound": {
            **allocation.as_record(),
            "optimistic_scalar_topology_numeric_bytes": optimistic,
            "semantics": (
                "exact_persistent_numeric_arrays_only_lower_bound_excludes_"
                "python_temporaries_sparse_operators_automata_and_scratch"
            ),
        },
        "resource_caps": {
            key: parsed["gates"][key]
            for key in (
                "maximum_host_persistent_numeric_bytes",
                "maximum_device_resident_numeric_bytes",
                "minimum_host_free_reserve_bytes",
                "minimum_device_free_reserve_bytes",
                "street_action_wall_ms",
                "emission_reserve_ms",
                "maximum_warm_contraction_ms",
            )
        },
        "admission_checks": admission_checks,
        "capacity_admitted": admitted,
        "terminal": terminal,
        "target_topology_builds": int(admitted),
        "target_scalar_contractions": int(admitted),
        "target_priming_contractions": int(admitted),
        "target_warm_contractions": int(admitted),
        "workload": workload,
        "target_wall_seconds": target_seconds,
        "gates": gates,
        "gates_passed": all(gates.values()),
    }


def run_full_width_river_capacity_preflight(
    config: Mapping[str, Any],
    *,
    git: Mapping[str, Any],
) -> dict[str, object]:
    parsed = _parse_config(config)
    if parsed["gates"]["require_clean_git_state"] and git.get("dirty") is not False:
        raise RuntimeError("full-width capacity target requires a clean Git state")
    campaign_started = time.perf_counter()
    cp, runtime = _runtime_snapshot(parsed)
    gates_config = parsed["gates"]
    hardware_gate = bool(
        gates_config["minimum_host_total_bytes"]
        <= runtime["host_total_physical_bytes"]
        <= gates_config["maximum_host_total_bytes"]
        and gates_config["minimum_device_total_bytes"]
        <= runtime["device_total_bytes"]
        <= gates_config["maximum_device_total_bytes"]
    )
    if not hardware_gate:
        raise RuntimeError("full-width capacity hardware differs from frozen workstation")
    control = _small_control(parsed)
    release_cupy_memory_pool()
    free, total = cp.cuda.runtime.memGetInfo()
    runtime = {
        **runtime,
        **_host_memory_snapshot(),
        "device_free_bytes": int(free),
        "device_total_bytes": int(total),
    }
    target = _run_target(parsed, runtime=runtime, control=control)
    final_memory = _host_memory_snapshot()
    device_free, device_total = cp.cuda.runtime.memGetInfo()
    campaign_seconds = time.perf_counter() - campaign_started
    emissions = {
        "actions": 0,
        "strategy_labels": 0,
        "strategy_quality_rows": 0,
        "quality_claim": None,
    }
    protocol_gates = {
        "clean_git_state": git.get("dirty") is False,
        "frozen_hardware": hardware_gate,
        "target_gates": target["gates_passed"],
        "campaign_within_bound": (
            campaign_seconds <= gates_config["maximum_campaign_seconds"]
        ),
        "zero_actions_strategy_labels_and_quality_rows": emissions
        == {
            "actions": 0,
            "strategy_labels": 0,
            "strategy_quality_rows": 0,
            "quality_claim": None,
        },
        "finite": math.isfinite(campaign_seconds),
    }
    return {
        "schema_version": "full-width-river-capacity-preflight-result-v1",
        "experiment_type": "label_free_literal_full_width_river_capacity_preflight",
        "evidence_stage": parsed["evidence_stage"],
        "source_commit": git["commit"],
        "source_dirty": git["dirty"],
        "target_workload": parsed["target_workload"],
        "warm_measurement": parsed["warm_measurement"],
        "preparation_scope": parsed["preparation_scope"],
        "charged_scope": parsed["charged_scope"],
        "runtime_at_target_admission": runtime,
        "final_memory": {
            **final_memory,
            "device_free_bytes": int(device_free),
            "device_total_bytes": int(device_total),
        },
        "control": control,
        "target": target,
        "campaign_wall_seconds": campaign_seconds,
        "emissions": emissions,
        "claims": {
            "capacity_admitted": target["capacity_admitted"],
            "representation_result_only": True,
            "strategy_quality_prior": None,
            "action_clock_claim": (
                "one_warm_contraction_only_if_executed_not_a_complete_decision_"
                "iteration_or_solve"
            ),
            "certified_truncation_authorized": False,
        },
        "gates": protocol_gates,
        "passed": all(protocol_gates.values()),
    }


def _write_exclusive(path: Path, rendered: bytes, *, maximum_bytes: int) -> None:
    if len(rendered) > maximum_bytes:
        raise ValueError("full-width capacity result exceeds frozen byte ceiling")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)


def _typed_failure_result(
    error: Exception,
    *,
    git: Mapping[str, Any],
    evidence_stage: str,
) -> dict[str, object]:
    return {
        "schema_version": "full-width-river-capacity-preflight-result-v1",
        "experiment_type": "label_free_literal_full_width_river_capacity_preflight",
        "evidence_stage": evidence_stage,
        "source_commit": git["commit"],
        "source_dirty": git["dirty"],
        "terminal": "typed_failure",
        "failure": {
            "type": type(error).__name__,
            "message": str(error),
        },
        "emissions": {
            "actions": 0,
            "strategy_labels": 0,
            "strategy_quality_rows": 0,
            "quality_claim": None,
        },
        "passed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_CONFIG)
    parser.add_argument("--output", type=Path, default=_OUTPUT)
    arguments = parser.parse_args()
    if arguments.config.resolve() != _CONFIG.resolve():
        raise ValueError("full-width capacity config path is frozen")
    if arguments.output.resolve() != _OUTPUT.resolve():
        raise ValueError("full-width capacity output path is frozen")
    loaded = load_config(
        arguments.config,
        schema_validator=lambda payload: _parse_config(payload),
        maximum_bytes=1_048_576,
    )
    git = _strict_git_metadata()
    failed = False
    try:
        result = run_full_width_river_capacity_preflight(loaded.payload, git=git)
    except Exception as error:  # noqa: BLE001 - first target failure is evidence
        failed = True
        result = _typed_failure_result(
            error,
            git=git,
            evidence_stage=_parse_config(loaded.payload)["evidence_stage"],
        )
    result["config_sha256"] = loaded.sha256
    result["implementation_sha256"] = _canonical_lf_sha256(_IMPLEMENTATION)
    rendered = (
        json.dumps(
            result,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    maximum = int(_parse_config(loaded.payload)["gates"]["maximum_result_bytes"])
    _write_exclusive(arguments.output, rendered, maximum_bytes=maximum)
    if failed:
        print(
            "full-width river capacity preflight: "
            f"passed=False terminal={result['terminal']}"
        )
        raise SystemExit(1)
    print(
        "full-width river capacity preflight: "
        f"passed={result['passed']} "
        f"capacity_admitted={result['target']['capacity_admitted']} "
        f"terminal={result['target']['terminal']}"
    )


if __name__ == "__main__":
    main()


__all__ = [
    "_capacity_admission",
    "_parse_config",
    "_run_target",
    "_small_control",
    "_street_inventory",
    "_typed_failure_result",
    "_write_exclusive",
    "run_full_width_river_capacity_preflight",
]
