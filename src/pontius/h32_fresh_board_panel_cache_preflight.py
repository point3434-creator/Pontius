"""Cache-only preflight for a deterministic panel of fresh h32 boards."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any, Mapping

import numpy as np

from . import h32_action_width_quality_audit as action_width
from .cupy_sparse_incidence import (
    CuPyBidirectionalIncidence,
    release_cupy_memory_pool,
)
from .fresh_h32_strategy_transfer_audit import _belief_digest
from .h32_affine_resident_cache_preflight import (
    _strict_git_metadata,
    _validate_runtime,
)
from .h32_second_board_resident_cache_preflight import (
    parse_h32_second_board_cache_config,
)
from .h32_warm_search_acceptance_audit import (
    build_target_belief,
    parse_h32_warm_search_config,
)
from .leaf_adjoint_checkpoint_ladder_audit import _build_case
from .multi_size_leaf_adjoint import (
    build_multi_size_leaf_adjoint_terminal_automata,
    multi_size_terminal_groups,
)
from .reporting import environment_metadata
from .river import format_card, parse_card, parse_cards
from .showdown_value_rank_screen import _rank_codes


_ROOT = Path(__file__).parents[2]
_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-fresh-board-panel-cache-v1.json"
)
_OUTPUT = (
    _ROOT / "experiments" / "results" / "h32-fresh-board-panel-cache-v1.json"
)
_PRIOR_RESULT = (
    _ROOT / "experiments" / "results" / "h32-second-board-action-width-v1.json"
)
_PRIOR_DECISION = (
    _ROOT
    / "docs"
    / "decisions"
    / "ADR-0141-second-sized-board-passes-mechanism-and-repeats-cap-abstention.md"
)
_SECOND_CACHE_RESULT = (
    _ROOT / "experiments" / "results" / "h32-second-board-resident-cache-v1.json"
)
_SECOND_CACHE_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-second-board-resident-cache-v1.json"
)
_SECOND_CACHE_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "h32_second_board_resident_cache_preflight.py"
)
_WARM_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-warm-search-acceptance-v1.json"
)
_WARM_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "h32_warm_search_acceptance_audit.py"
)
_LADDER_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "leaf_adjoint_checkpoint_ladder_audit.py"
)
_ACTION_WIDTH_CONFIG = (
    _ROOT / "experiments" / "configs" / "h32-action-width-quality-v1.json"
)
_ACTION_WIDTH_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "h32_action_width_quality_audit.py"
)
_FRESH_IMPLEMENTATION = (
    _ROOT / "src" / "pontius" / "fresh_h32_strategy_transfer_audit.py"
)
_IMPLEMENTATION = Path(__file__)
_CONTROL_TEST = _ROOT / "tests" / "test_h32_fresh_board_panel_cache_preflight.py"

_SEED_COMMIT = "3f7a0f7db3571381236dcd3f87e91730f9a29865"
_SAMPLER_NAMESPACE = "pontius-h32-fresh-board-panel-v1"
_FROZEN_PANELS = (
    {"board_id": "panel_1", "cards": ["5c", "8c", "8d", "Jc", "As"]},
    {"board_id": "panel_2", "cards": ["2c", "3s", "5d", "Js", "Qc"]},
    {"board_id": "panel_3", "cards": ["4h", "7h", "9s", "Jd", "Kc"]},
)
_FROZEN_BOARD_DIGESTS = {
    "panel_1": "713e515d802e3f1fbd4fbfb34342c1b55c2f71a76ee506ac3927ed1cc78f6868",
    "panel_2": "4cf870db7287e5c9dfe5a2f8e138d55527df7a6c23ad4b22b5f8e3ba806bd9d1",
    "panel_3": "261479623ddcd026fc02b55d773c392f0cecd39c3634592bb88da93f92758418",
}
_FROZEN_SOURCE_DIGESTS = {
    "panel_1/balanced": (
        "376e8a44217f35dfdf305035fe8f3bbfb52b010e14050bedaf55da78c9e72885"
    ),
    "panel_1/blocker_heavy": (
        "aa3a5a8abe8dc72fe436134d4b619239a87b002134cdad88a908d833318b5067"
    ),
    "panel_2/balanced": (
        "0662b2cf2436cbc6dcc5669fe75a2c15f03e652fb40a6903703a10dd14cfa289"
    ),
    "panel_2/blocker_heavy": (
        "59f955c6b89bdc56670dc16b19795451404fe80ff37f519bac007975d85200f1"
    ),
    "panel_3/balanced": (
        "cadd9449259f56de43ae4d710c2e3fd6ae4733e7b7c8323836b87578a3cc9a71"
    ),
    "panel_3/blocker_heavy": (
        "74ce0c18ac82e9ebb799be851f140c7011ad75671a3409f94c7db1db3187278e"
    ),
}
_FROZEN_TARGET_DIGESTS = {
    "panel_1/balanced/local_blocker_seat3_x2": (
        "f347f95b256e1ef3ab20f40f9f5cc61667a1aac737182e368f9f7a47800c4393"
    ),
    "panel_1/balanced/all_seat_strength_1_to2": (
        "f8e0c8f174acff53f6a75c6d2c8c5717b796d1437ed5b2fc3943a0ae6ff3566c"
    ),
    "panel_1/blocker_heavy/local_blocker_seat3_x2": (
        "d70fd75916667840b5e03cbb10a7ce7fd1a85965833d0a44da60d15bce729bd3"
    ),
    "panel_1/blocker_heavy/all_seat_strength_1_to2": (
        "c5479556b8d00da4aec9fc975915ab8385298a5bb380e978d248eb38a48873a2"
    ),
    "panel_2/balanced/local_blocker_seat3_x2": (
        "462203f1cb9616a00fb55f06da2764f2023d3d5f6cfd5cd5d0bb62561e3967ab"
    ),
    "panel_2/balanced/all_seat_strength_1_to2": (
        "581207fde0a2fb77254305ffa207febe1cf62d6af94e57d89cd8df4d5325e3ac"
    ),
    "panel_2/blocker_heavy/local_blocker_seat3_x2": (
        "0571db1ddfbebbddc40e7fc8ff0ece2e2ecbc06636aef1100dc246ac1ae3e660"
    ),
    "panel_2/blocker_heavy/all_seat_strength_1_to2": (
        "f807de90ef084fd6b0bacf6fbe4659e8a67af586a0f8f8b6504028220a15433f"
    ),
    "panel_3/balanced/local_blocker_seat3_x2": (
        "8056f7ed272f00010035f9c52c8433e9ad7140b501ae1c83ecd7e10e84a6fa19"
    ),
    "panel_3/balanced/all_seat_strength_1_to2": (
        "16d006ad8400b0d26eca707fc100fcd30c63b1a4ed255ca4c678b0be842cae1a"
    ),
    "panel_3/blocker_heavy/local_blocker_seat3_x2": (
        "40a998aeb0ae58831b9d3d3591c66d2badef34dea57e40b385e5c3c1c0c852e9"
    ),
    "panel_3/blocker_heavy/all_seat_strength_1_to2": (
        "20917911b800696544fd270b9e26e16038b20c6fba0dbd2b85b6cf60ce0cc50e"
    ),
}
_FROZEN_DESCRIPTOR_DIGESTS = {
    "panel_1/balanced/local_blocker_seat3_x2": (
        "a9adf0921480697049697516976e81213d66d46344ebf0bd24b8c46b051095d6"
    ),
    "panel_1/balanced/all_seat_strength_1_to2": (
        "4e9b6c888a5faa8656b76e7f51901ef85c8e57e2a32c410d4e3afa06cfbe5b2b"
    ),
    "panel_1/blocker_heavy/local_blocker_seat3_x2": (
        "95f0d3b0490c28a92241699bf06b7706849cc4ab0f004506f88913165149ad17"
    ),
    "panel_1/blocker_heavy/all_seat_strength_1_to2": (
        "c33fa8bd816db80a84f4b0e7cab03bc2098208841e4632bc0fa1c397962be605"
    ),
    "panel_2/balanced/local_blocker_seat3_x2": (
        "d49525e1f4d703ede11a9782e567c863fbad5080adf544cd576b61cdea9b1a46"
    ),
    "panel_2/balanced/all_seat_strength_1_to2": (
        "59bb3baaac6f0c20e098b4332bf75f9699be46eb04810011cb56417f1017471a"
    ),
    "panel_2/blocker_heavy/local_blocker_seat3_x2": (
        "01f4ef0044ff8c37c974bb4f75d87515167ff3e76d2663017c67721c751d19bb"
    ),
    "panel_2/blocker_heavy/all_seat_strength_1_to2": (
        "d3e2f7e4f282a9e74955edd7ccf7c00822e31aaca75f728335a85a8ef862b818"
    ),
    "panel_3/balanced/local_blocker_seat3_x2": (
        "b5acb7e958fcf40ff6a4d9d204b7650afa82304ff4b1c984342e8870d10bfc9e"
    ),
    "panel_3/balanced/all_seat_strength_1_to2": (
        "6e7d0cee08dea55570f54e8ca4b9dab97b9d5df0a286b07afed731bdb0611e7b"
    ),
    "panel_3/blocker_heavy/local_blocker_seat3_x2": (
        "01fb7b6ede07ca9cc388369f1ab174c04de8c8eac10870306311c8ee3dc810c5"
    ),
    "panel_3/blocker_heavy/all_seat_strength_1_to2": (
        "94e856819d3930afb9e405094679aa11551a0381422deb558119ced41c66069c"
    ),
}

_CONFIG_FIELDS = {
    "evidence_stage",
    "expected_prior_result_sha256",
    "expected_prior_decision_sha256",
    "expected_second_cache_result_sha256",
    "expected_second_cache_config_sha256",
    "expected_second_cache_implementation_sha256",
    "expected_warm_config_sha256",
    "expected_warm_implementation_sha256",
    "expected_ladder_implementation_sha256",
    "expected_action_width_config_sha256",
    "expected_action_width_implementation_sha256",
    "expected_fresh_implementation_sha256",
    "expected_audit_implementation_sha256",
    "expected_control_test_sha256",
    "seed_commit",
    "board_sampler_namespace",
    "board_sampler_rule",
    "panels",
    "panel_board_sha256",
    "disclosed_prior_h32_strategy_boards",
    "pot",
    "stack",
    "one_size_bet",
    "two_size_bets",
    "expected_one_size_payoff_span",
    "expected_two_size_payoff_span",
    "players",
    "hands_per_player",
    "range_families",
    "target_shifts",
    "local_blocker_target_seat",
    "target_order",
    "arm_order_by_target",
    "source_belief_sha256_by_source",
    "target_belief_sha256_by_target",
    "target_descriptor_sha256_by_target",
    "mixture_components",
    "split_index",
    "query_chunk_records",
    "maximum_feature_width_per_batch",
    "minimum_warm_noncache_reserve_bytes",
    "headroom_rule",
    "zero_step_rule",
    "strategy_claim_policy",
    "required_numpy_version",
    "required_scipy_version",
    "required_cupy_version",
    "required_cuda_runtime_version",
    "minimum_cuda_driver_version",
    "required_compute_capability",
    "cuda_dll_environment_variable",
    "gates",
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
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def derive_fresh_panel_boards(
    *,
    seed_commit: str,
    namespace: str,
    panel_count: int,
) -> tuple[dict[str, Any], ...]:
    """Derive disjoint boards without consulting any strategy label."""

    if len(seed_commit) != 40 or any(c not in "0123456789abcdef" for c in seed_commit):
        raise ValueError("fresh-panel seed must be a full lowercase commit hash")
    if namespace != _SAMPLER_NAMESPACE or panel_count != 3:
        raise ValueError("fresh-panel sampler contract differs")
    cards = [format_card(card) for card in range(52)]
    cards.sort(
        key=lambda card: (
            hashlib.sha256(
                f"{namespace}|{seed_commit}|{card}".encode("utf-8")
            ).digest(),
            card,
        )
    )
    panels = []
    for index in range(panel_count):
        selected = cards[index * 5 : (index + 1) * 5]
        selected.sort(key=parse_card)
        panels.append({"board_id": f"panel_{index + 1}", "cards": selected})
    return tuple(panels)


def panel_freshness_diagnostics(
    panels: tuple[Mapping[str, Any], ...],
    prior_boards: tuple[tuple[str, ...], ...],
) -> dict[str, Any]:
    boards = tuple(tuple(panel["cards"]) for panel in panels)
    all_cards = tuple(card for board in boards for card in board)
    return {
        "panel_count": len(boards),
        "unique_board_count": len(set(boards)),
        "panel_card_count": len(all_cards),
        "unique_panel_card_count": len(set(all_cards)),
        "absent_from_disclosed_prior_h32_strategy_boards": all(
            board not in prior_boards for board in boards
        ),
        "pairwise_card_disjoint": len(all_cards) == len(set(all_cards)),
    }


def compute_label_free_panel_identity_rows(
    warm_config: Mapping[str, Any],
    panels: tuple[Mapping[str, Any], ...],
    *,
    expected_sources: Mapping[str, str] | None = None,
    expected_targets: Mapping[str, str] | None = None,
    expected_descriptors: Mapping[str, str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Rebuild source and target identities without sized h32 work."""

    parsed = parse_h32_warm_search_config(dict(warm_config))
    source_rows = []
    target_rows = []
    for panel in panels:
        board_id = str(panel["board_id"])
        cards = list(panel["cards"])
        board = parse_cards(*cards)
        for family in parsed["range_families"]:
            source, _, _, retained = _build_case(
                parsed=parsed,
                board=board,
                hand_count=parsed["wide_hands_per_player"],
                family=family,
            )
            source_key = f"{board_id}/{family}"
            source_digest = _belief_digest(source)
            source_identity = (
                True
                if expected_sources is None
                else source_digest == expected_sources[source_key]
            )
            source_rows.append(
                {
                    "source": source_key,
                    "board_id": board_id,
                    "board": cards,
                    "range_family": family,
                    "source_belief_sha256": source_digest,
                    "expected_digest_identity": source_identity,
                    "passed": source_identity,
                }
            )
            for shift in parsed["target_shifts"]:
                target, descriptor = build_target_belief(
                    source,
                    board=board,
                    shift=shift,
                    local_blocker_target_seat=parsed[
                        "local_blocker_target_seat"
                    ],
                )
                key = f"{source_key}/{shift}"
                target_digest = _belief_digest(target)
                descriptor_digest = _json_digest(descriptor)
                target_identity = (
                    True
                    if expected_targets is None
                    else target_digest == expected_targets[key]
                )
                descriptor_identity = (
                    True
                    if expected_descriptors is None
                    else descriptor_digest == expected_descriptors[key]
                )
                axes_identity = (
                    descriptor["hand_axes_identity"] is True
                    and target.hands_by_player == source.hands_by_player
                )
                target_rows.append(
                    {
                        "target": key,
                        "board_id": board_id,
                        "board": cards,
                        "range_family": family,
                        "target_shift": shift,
                        "target_belief_sha256": target_digest,
                        "target_descriptor_sha256": descriptor_digest,
                        "target_descriptor": descriptor,
                        "target_digest_identity": target_identity,
                        "descriptor_digest_identity": descriptor_identity,
                        "hand_axes_identity": axes_identity,
                        "passed": bool(
                            target_identity
                            and descriptor_identity
                            and axes_identity
                        ),
                    }
                )
            del retained, source
            gc.collect()
    return source_rows, target_rows


def _seed_commit_identity(seed_commit: str) -> bool:
    resolved = subprocess.check_output(
        ["git", "rev-parse", seed_commit],
        cwd=_ROOT,
        text=True,
    ).strip()
    return resolved == seed_commit


def parse_h32_fresh_board_panel_cache_config(
    config: dict[str, Any],
) -> dict[str, Any]:
    """Validate the complete fresh-panel cache-only contract."""

    if set(config) != _CONFIG_FIELDS:
        raise ValueError("fresh-panel cache fields differ from ADR-0142")
    frozen = {
        "evidence_stage": (
            "preregistered_after_adr0141_before_any_panel_h32_sized_tree_"
            "cache_policy_step_or_strategy_quality_measurement"
        ),
        "seed_commit": _SEED_COMMIT,
        "board_sampler_namespace": _SAMPLER_NAMESPACE,
        "board_sampler_rule": (
            "sort_all_52_canonical_cards_by_sha256_namespace_pipe_full_"
            "seed_commit_pipe_card_then_take_15_group_consecutive_fives_"
            "and_sort_each_board_by_card_integer"
        ),
        "panels": list(_FROZEN_PANELS),
        "disclosed_prior_h32_strategy_boards": [
            ["2c", "7d", "9h", "Js", "Qc"],
            ["4h", "6s", "Td", "Qh", "As"],
        ],
        "pot": 12.0,
        "stack": 30.0,
        "one_size_bet": 3.0,
        "two_size_bets": [3.0, 6.0],
        "expected_one_size_payoff_span": 30.0,
        "expected_two_size_payoff_span": 48.0,
        "players": 6,
        "hands_per_player": 32,
        "range_families": ["balanced", "blocker_heavy"],
        "target_shifts": [
            "local_blocker_seat3_x2",
            "all_seat_strength_1_to2",
        ],
        "local_blocker_target_seat": 3,
        "target_order": list(_FROZEN_TARGET_DIGESTS),
        "arm_order_by_target": [
            "one_then_two" if index % 2 == 0 else "two_then_one"
            for index in range(12)
        ],
        "mixture_components": 3,
        "split_index": 3,
        "query_chunk_records": 256,
        "maximum_feature_width_per_batch": 384,
        "minimum_warm_noncache_reserve_bytes": 5_184_456_164,
        "headroom_rule": (
            "all_twenty_four_caches_must_leave_the_prior_pool_and_physical_"
            "noncache_reserve_before_any_panel_strategy_preregistration"
        ),
        "zero_step_rule": (
            "compile_and_measure_only_zero_panel_h32_steps_zero_panel_h32_"
            "policies_zero_panel_h32_quality_evaluations"
        ),
        "strategy_claim_policy": "always_null",
        "required_numpy_version": "2.5.2",
        "required_scipy_version": "1.18.0",
        "required_cupy_version": "14.2.0",
        "required_cuda_runtime_version": 13020,
        "minimum_cuda_driver_version": 13000,
        "required_compute_capability": "120",
        "cuda_dll_environment_variable": "PONTIUS_CUDA_DLL_DIRECTORY",
    }
    if any(config[field] != value for field, value in frozen.items()):
        raise ValueError("fresh-panel cache workload differs from ADR-0142")
    if config["panel_board_sha256"] != _FROZEN_BOARD_DIGESTS:
        raise ValueError("fresh-panel board digests differ")
    if config["source_belief_sha256_by_source"] != _FROZEN_SOURCE_DIGESTS:
        raise ValueError("fresh-panel source belief digests differ")
    if config["target_belief_sha256_by_target"] != _FROZEN_TARGET_DIGESTS:
        raise ValueError("fresh-panel target belief digests differ")
    if config["target_descriptor_sha256_by_target"] != _FROZEN_DESCRIPTOR_DIGESTS:
        raise ValueError("fresh-panel target descriptor digests differ")

    sources = {
        "expected_prior_result_sha256": _PRIOR_RESULT,
        "expected_prior_decision_sha256": _PRIOR_DECISION,
        "expected_second_cache_result_sha256": _SECOND_CACHE_RESULT,
        "expected_second_cache_config_sha256": _SECOND_CACHE_CONFIG,
        "expected_second_cache_implementation_sha256": (
            _SECOND_CACHE_IMPLEMENTATION
        ),
        "expected_warm_config_sha256": _WARM_CONFIG,
        "expected_warm_implementation_sha256": _WARM_IMPLEMENTATION,
        "expected_ladder_implementation_sha256": _LADDER_IMPLEMENTATION,
        "expected_action_width_config_sha256": _ACTION_WIDTH_CONFIG,
        "expected_action_width_implementation_sha256": (
            _ACTION_WIDTH_IMPLEMENTATION
        ),
        "expected_fresh_implementation_sha256": _FRESH_IMPLEMENTATION,
        "expected_audit_implementation_sha256": _IMPLEMENTATION,
        "expected_control_test_sha256": _CONTROL_TEST,
    }
    for field, path in sources.items():
        if config[field] != _sha256(path):
            raise ValueError(f"fresh-panel cache source mismatch: {field}")

    warm_config = json.loads(_WARM_CONFIG.read_text(encoding="utf-8"))
    warm_parsed = parse_h32_warm_search_config(warm_config)
    if warm_parsed["local_blocker_target_seat"] != config[
        "local_blocker_target_seat"
    ]:
        raise ValueError("fresh-panel local blocker seat differs")
    action_config = json.loads(_ACTION_WIDTH_CONFIG.read_text(encoding="utf-8"))
    action_width.parse_h32_action_width_quality_config(action_config)
    second_cache_config = json.loads(
        _SECOND_CACHE_CONFIG.read_text(encoding="utf-8")
    )
    parse_h32_second_board_cache_config(second_cache_config)

    derived = derive_fresh_panel_boards(
        seed_commit=config["seed_commit"],
        namespace=config["board_sampler_namespace"],
        panel_count=3,
    )
    if list(derived) != config["panels"]:
        raise ValueError("fresh-panel board derivation differs")
    if {
        panel["board_id"]: _json_digest(panel["cards"]) for panel in derived
    } != config["panel_board_sha256"]:
        raise ValueError("fresh-panel derived board digest differs")

    expected_gates = {
        "expected_panel_rows": 3,
        "expected_source_rows": 6,
        "expected_target_rows": 12,
        "expected_cache_rows": 24,
        "expected_unique_panel_cards": 15,
        "expected_one_size_public_nodes": 385,
        "expected_two_size_public_nodes": 763,
        "expected_one_size_terminal_groups": 64,
        "expected_two_size_terminal_groups": 127,
        "expected_one_size_logical_automata": 384,
        "expected_two_size_logical_automata": 762,
        "expected_shared_affine_bases": 378,
        "maximum_small_profile_utility_error": 2e-13,
        "maximum_small_quality_error": 2e-11,
        "maximum_small_zero_sum_residual": 2e-11,
        "maximum_cache_compile_ms": 120000.0,
        "maximum_gpu_pool_bytes": 12000000000,
        "maximum_total_preflight_seconds": 1800.0,
        "require_clean_git_state": True,
        "require_parent_identity": True,
        "require_seed_commit_identity": True,
        "require_panel_freshness": True,
        "require_source_identity": True,
        "require_target_identity": True,
        "require_payoff_spans": True,
        "require_maximum_middle_rank_identity": True,
        "require_zero_h32_steps": True,
        "require_zero_h32_policies": True,
        "require_zero_h32_quality_evaluations": True,
        "require_strategy_claim_null": True,
    }
    if config["gates"] != expected_gates:
        raise ValueError("fresh-panel cache gates differ from ADR-0142")
    return {
        **config,
        "panels": tuple(dict(panel) for panel in config["panels"]),
        "disclosed_prior_h32_strategy_boards": tuple(
            tuple(board) for board in config["disclosed_prior_h32_strategy_boards"]
        ),
        "two_size_bets": tuple(config["two_size_bets"]),
        "range_families": tuple(config["range_families"]),
        "target_shifts": tuple(config["target_shifts"]),
        "target_order": tuple(config["target_order"]),
        "arm_order_by_target": tuple(config["arm_order_by_target"]),
        "gates": dict(config["gates"]),
    }


def run_h32_fresh_board_panel_cache_preflight(
    config_path: Path = _CONFIG,
    output_path: Path = _OUTPUT,
) -> dict[str, Any]:
    """Measure one- and two-size cache residency over the fresh panel."""

    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    parsed = parse_h32_fresh_board_panel_cache_config(config)
    prior = json.loads(_PRIOR_RESULT.read_text(encoding="utf-8"))
    second_cache = json.loads(_SECOND_CACHE_RESULT.read_text(encoding="utf-8"))
    parent_identity = (
        prior["passed"]
        and prior["strategy_quality_claim"] is None
        and prior["aggregate_strategy_outcome"][
            "one_size_blueprint_abstentions"
        ]
        == 4
        and prior["aggregate_strategy_outcome"][
            "two_size_blueprint_abstentions"
        ]
        == 4
        and prior["aggregate_strategy_outcome"]["outcome_is_not_a_gate"]
        and second_cache["passed"]
        and second_cache["headroom"]["all_eight_caches_safe"]
        and second_cache["h32_steps_executed"] == 0
        and second_cache["h32_policies_constructed"] == 0
        and second_cache["h32_strategy_quality_evaluations"] == 0
        and second_cache["strategy_quality_claim"] is None
    )
    if not parent_identity:
        raise ValueError("fresh-panel cache parent identity rejected")

    environment = environment_metadata()
    environment["git"] = _strict_git_metadata()
    cp, runtime = _validate_runtime(parsed)
    seed_identity = _seed_commit_identity(parsed["seed_commit"])
    freshness = panel_freshness_diagnostics(
        parsed["panels"],
        parsed["disclosed_prior_h32_strategy_boards"],
    )
    panel_fresh = (
        freshness["panel_count"] == parsed["gates"]["expected_panel_rows"]
        and freshness["unique_board_count"]
        == parsed["gates"]["expected_panel_rows"]
        and freshness["unique_panel_card_count"]
        == parsed["gates"]["expected_unique_panel_cards"]
        and freshness["absent_from_disclosed_prior_h32_strategy_boards"]
        and freshness["pairwise_card_disjoint"]
    )
    if not seed_identity or not panel_fresh:
        raise ValueError("fresh-panel deterministic board identity rejected")

    warm_config = json.loads(_WARM_CONFIG.read_text(encoding="utf-8"))
    warm_parsed = parse_h32_warm_search_config(warm_config)
    source_identity_rows, target_identity_rows = (
        compute_label_free_panel_identity_rows(
            warm_config,
            parsed["panels"],
            expected_sources=parsed["source_belief_sha256_by_source"],
            expected_targets=parsed["target_belief_sha256_by_target"],
            expected_descriptors=parsed[
                "target_descriptor_sha256_by_target"
            ],
        )
    )
    if not all(row["passed"] for row in source_identity_rows):
        raise ValueError("fresh-panel source identity rejected before sized h32")
    if not all(row["passed"] for row in target_identity_rows):
        raise ValueError("fresh-panel target identity rejected before sized h32")

    small = action_width._small_control(parsed)
    small_passed = (
        small["profile_utility_error"]
        <= parsed["gates"]["maximum_small_profile_utility_error"]
        and small["quality_error"]
        <= parsed["gates"]["maximum_small_quality_error"]
        and small["zero_sum_residual"]
        <= parsed["gates"]["maximum_small_zero_sum_residual"]
        and small["compact_round_trip"]
        and small["one_size_public_nodes"]
        == parsed["gates"]["expected_one_size_public_nodes"]
        and small["two_size_public_nodes"]
        == parsed["gates"]["expected_two_size_public_nodes"]
        and small["two_size_terminal_groups"]
        == parsed["gates"]["expected_two_size_terminal_groups"]
        and small["shared_affine_bases"]
        == parsed["gates"]["expected_shared_affine_bases"]
        and small["two_size_payoff_span"]
        == parsed["expected_two_size_payoff_span"]
    )
    if not small_passed:
        raise ValueError("small fresh-panel cache control failed before h32")

    measured_targets = []
    target_index = 0
    for panel in parsed["panels"]:
        board_id = panel["board_id"]
        cards = panel["cards"]
        board = parse_cards(*cards)
        for family in parsed["range_families"]:
            gc.collect()
            release_cupy_memory_pool()
            source, one_layout, sparse, retained = _build_case(
                parsed=warm_parsed,
                board=board,
                hand_count=parsed["hands_per_player"],
                family=family,
            )
            source_key = f"{board_id}/{family}"
            source_workspace, _, one_libraries = retained
            source_identity = (
                _belief_digest(source)
                == parsed["source_belief_sha256_by_source"][source_key]
            )
            codes = tuple(
                np.ascontiguousarray(values, dtype=np.int32)
                for values in _rank_codes(board, source.hands_by_player)
            )
            sized_layout = action_width._representative_sized_tree(
                source,
                pot=parsed["pot"],
                stack=parsed["stack"],
                bet_sizes=parsed["two_size_bets"],
            )
            sized_libraries = build_multi_size_leaf_adjoint_terminal_automata(
                sized_layout,
                codes,
                pot=parsed["pot"],
            )
            gpu = CuPyBidirectionalIncidence.compile(sparse)
            for shift in parsed["target_shifts"]:
                target, descriptor = build_target_belief(
                    source,
                    board=board,
                    shift=shift,
                    local_blocker_target_seat=parsed[
                        "local_blocker_target_seat"
                    ],
                )
                key = f"{source_key}/{shift}"
                descriptor_digest = _json_digest(descriptor)
                target_identity = (
                    source_identity
                    and _belief_digest(target)
                    == parsed["target_belief_sha256_by_target"][key]
                    and descriptor_digest
                    == parsed["target_descriptor_sha256_by_target"][key]
                    and target.hands_by_player == source.hands_by_player
                )
                workspace, workspace_ms = action_width._target_workspace(
                    source_workspace,
                    target,
                    query_chunk_records=parsed["query_chunk_records"],
                )
                order_name = parsed["arm_order_by_target"][target_index]
                arm_order = (
                    ("one_size", "two_size")
                    if order_name == "one_then_two"
                    else ("two_size", "one_size")
                )
                arms = {}
                for arm in arm_order:
                    gc.collect()
                    release_cupy_memory_pool()
                    libraries = (
                        one_libraries if arm == "one_size" else sized_libraries
                    )
                    cache_row, belief_cache, automaton_caches = (
                        action_width._compile_cache(
                            cp,
                            workspace,
                            libraries,
                            arm=arm,
                        )
                    )
                    cache_row["pool_ceiling_headroom_bytes"] = (
                        parsed["gates"]["maximum_gpu_pool_bytes"]
                        - cache_row["pool_total_bytes"]
                    )
                    cache_row["warm_noncache_reserve_safe"] = (
                        cache_row["pool_ceiling_headroom_bytes"]
                        >= parsed["minimum_warm_noncache_reserve_bytes"]
                        and cache_row["physical_device_free_bytes"]
                        >= parsed["minimum_warm_noncache_reserve_bytes"]
                    )
                    arms[arm] = cache_row
                    del automaton_caches, belief_cache
                    gc.collect()
                    release_cupy_memory_pool()

                one = arms["one_size"]
                two = arms["two_size"]
                measured_targets.append(
                    {
                        "board_id": board_id,
                        "board": cards,
                        "range_family": family,
                        "target_shift": shift,
                        "target": key,
                        "arm_order": order_name,
                        "source_belief_sha256": _belief_digest(source),
                        "source_identity": source_identity,
                        "target_descriptor": descriptor,
                        "target_descriptor_sha256": descriptor_digest,
                        "target_belief_sha256": _belief_digest(target),
                        "target_identity": target_identity,
                        "target_workspace_compile_ms": workspace_ms,
                        "one_size_public_nodes": one_layout.public_node_count,
                        "two_size_public_nodes": sized_layout.public_node_count,
                        "one_size_terminal_groups": len(one_libraries[0]),
                        "two_size_terminal_groups": len(
                            multi_size_terminal_groups(sized_layout)
                        ),
                        "one_size_payoff_span": float(
                            one_layout.game.payoff_span
                        ),
                        "two_size_payoff_span": float(
                            sized_layout.game.payoff_span
                        ),
                        "arms": arms,
                        "two_over_one": {
                            "persistent_numeric_bytes": (
                                two["persistent_numeric_bytes"]
                                / one["persistent_numeric_bytes"]
                            ),
                            "automaton_numeric_bytes": (
                                two["automaton_numeric_bytes"]
                                / one["automaton_numeric_bytes"]
                            ),
                            "total_middle_rank": (
                                two["total_middle_rank"]
                                / one["total_middle_rank"]
                            ),
                            "cold_construction_ms": (
                                two["cold_construction_ms"]
                                / one["cold_construction_ms"]
                            ),
                        },
                    }
                )
                target_index += 1
                del workspace, target
                gc.collect()
                release_cupy_memory_pool()
            del gpu
            gc.collect()
            release_cupy_memory_pool()

    total_seconds = time.perf_counter() - started
    gates = parsed["gates"]
    cache_rows = [
        target["arms"][arm]
        for target in measured_targets
        for arm in ("one_size", "two_size")
    ]
    actual_order = tuple(target["target"] for target in measured_targets)
    headroom_safe = all(row["warm_noncache_reserve_safe"] for row in cache_rows)
    h32_steps_executed = 0
    h32_policies_constructed = 0
    h32_strategy_quality_evaluations = 0
    strategy_quality_claim = None
    gate_results = {
        "parent_identity": parent_identity == gates["require_parent_identity"],
        "seed_commit_identity": seed_identity
        == gates["require_seed_commit_identity"],
        "panel_freshness": panel_fresh == gates["require_panel_freshness"],
        "clean_git_state": (not bool(environment["git"]["dirty"]))
        == gates["require_clean_git_state"],
        "small_control": small_passed,
        "source_count_and_identity": (
            len(source_identity_rows) == gates["expected_source_rows"]
            and all(row["passed"] for row in source_identity_rows)
        )
        == gates["require_source_identity"],
        "target_count_order_and_identity": (
            len(measured_targets) == gates["expected_target_rows"]
            and actual_order == parsed["target_order"]
            and all(target["target_identity"] for target in measured_targets)
        )
        == gates["require_target_identity"],
        "cache_count": len(cache_rows) == gates["expected_cache_rows"],
        "public_topology": all(
            target["one_size_public_nodes"]
            == gates["expected_one_size_public_nodes"]
            and target["two_size_public_nodes"]
            == gates["expected_two_size_public_nodes"]
            and target["one_size_terminal_groups"]
            == gates["expected_one_size_terminal_groups"]
            and target["two_size_terminal_groups"]
            == gates["expected_two_size_terminal_groups"]
            for target in measured_targets
        ),
        "logical_automata_and_bases": all(
            target["arms"]["one_size"]["logical_automata"]
            == gates["expected_one_size_logical_automata"]
            and target["arms"]["two_size"]["logical_automata"]
            == gates["expected_two_size_logical_automata"]
            and target["arms"]["two_size"]["shared_affine_bases"]
            == gates["expected_shared_affine_bases"]
            for target in measured_targets
        ),
        "payoff_spans": all(
            target["one_size_payoff_span"]
            == parsed["expected_one_size_payoff_span"]
            and target["two_size_payoff_span"]
            == parsed["expected_two_size_payoff_span"]
            for target in measured_targets
        )
        == gates["require_payoff_spans"],
        "maximum_middle_rank_identity": all(
            target["arms"]["one_size"]["maximum_middle_rank"]
            == target["arms"]["two_size"]["maximum_middle_rank"]
            for target in measured_targets
        )
        == gates["require_maximum_middle_rank_identity"],
        "cache_compile": all(
            row["cold_construction_ms"] <= gates["maximum_cache_compile_ms"]
            for row in cache_rows
        ),
        "gpu_pool_ceiling": all(
            row["pool_total_bytes"] <= gates["maximum_gpu_pool_bytes"]
            for row in cache_rows
        ),
        "zero_h32_steps": (h32_steps_executed == 0)
        == gates["require_zero_h32_steps"],
        "zero_h32_policies": (h32_policies_constructed == 0)
        == gates["require_zero_h32_policies"],
        "zero_h32_quality_evaluations": (
            h32_strategy_quality_evaluations == 0
        )
        == gates["require_zero_h32_quality_evaluations"],
        "strategy_claim_null": (strategy_quality_claim is None)
        == gates["require_strategy_claim_null"],
        "wall_time": total_seconds <= gates["maximum_total_preflight_seconds"],
    }
    passed = all(gate_results.values())
    result = {
        "schema_version": 1,
        "status": "frozen_h32_fresh_board_panel_cache_preflight_executed",
        "experiment_type": "h32_fresh_panel_one_vs_two_size_cache_portability",
        "config": config,
        "config_sha256": _sha256(config_path),
        "implementation_sha256": _sha256(_IMPLEMENTATION),
        "source_sha256": {
            field.removeprefix("expected_"): config[field]
            for field in config
            if field.startswith("expected_") and field.endswith("_sha256")
        },
        "environment": {**environment, **runtime},
        "parent_identity": parent_identity,
        "seed_commit_identity": seed_identity,
        "panel_freshness": freshness,
        "small_control": small,
        "source_identity_preflight": source_identity_rows,
        "target_identity_preflight": target_identity_rows,
        "targets": measured_targets,
        "headroom": {
            "minimum_warm_noncache_reserve_bytes": parsed[
                "minimum_warm_noncache_reserve_bytes"
            ],
            "all_twenty_four_caches_safe": headroom_safe,
            "outcome_is_not_a_mechanism_gate": True,
        },
        "h32_steps_executed": h32_steps_executed,
        "h32_policies_constructed": h32_policies_constructed,
        "h32_strategy_quality_evaluations": (
            h32_strategy_quality_evaluations
        ),
        "gate_results": gate_results,
        "passed": passed,
        "decision": (
            "authorize_fresh_panel_source_blueprint_preregistration"
            if passed and headroom_safe
            else (
                "stop_before_fresh_panel_strategy_and_revisit_cache"
                if passed
                else "reject_fresh_panel_cache_preflight_mechanism"
            )
        ),
        "strategy_quality_claim": strategy_quality_claim,
        "timing": {"total_seconds": total_seconds},
        "limitations": [
            (
                "Three deterministic boards expand the corpus but do not "
                "represent the full river-board population."
            ),
            (
                "The two range families and two likelihood shifts reuse the "
                "existing generator contract."
            ),
            (
                "Headroom is a conservative laboratory reserve, not a "
                "production concurrency proof."
            ),
            "No panel h32 policy was constructed, trained, or evaluated.",
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
    arguments = parser.parse_args()
    result = run_h32_fresh_board_panel_cache_preflight(
        arguments.config,
        arguments.output,
    )
    print(
        "h32 fresh-board panel cache preflight: "
        f"passed={result['passed']}, "
        "headroom_safe="
        f"{result['headroom']['all_twenty_four_caches_safe']}, "
        f"wall={result['timing']['total_seconds']:.3f}s"
    )


if __name__ == "__main__":
    main()
