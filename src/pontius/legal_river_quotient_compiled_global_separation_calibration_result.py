"""Independent standard-library reader for the ADR-0457 calibration.

The producer and its fit implementation are intentionally not imported.  This
reader reconstructs the matrix, phase partitions, exact constrained affine
fits, symbolic target coordinates, materiality conjuncts, and claims boundary
from the durable journal.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from math import comb, factorial
from pathlib import Path

from .durable_evidence_journal import (
    JournalRecordKind,
    recover_journal_bytes,
    recover_journal_file,
)


ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v1.json"
)
CONFIG_SHA256 = "a9a0961656c66d70d145c9f5434460826f3c4972b7b1a18da74b0886a14e18bf"
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v1.jsonl"
)
RESULT_PATH = ROOT / RESULT_RELATIVE_PATH
PROTOCOL_SHA256 = sha256(b"pontius-adr0457-compiled-separation-owner-v1").hexdigest()
CAMPAIGN_SHA256 = sha256(
    b"pontius-adr0457-compiled-separation-calibration-v1"
).hexdigest()
PREREGISTRATION_COMMIT = "cb90e1d5581034f1988c0e2edfa8777972768a20"

DOMAINS = (10, 12, 16, 20, 24)
TARGET_CARDS = 45
PRICE_COEFFICIENTS = (30, -120, 360, -720, 720)
H_SEED_WEIGHTS = (1, -24, 360, -2880, 8640)
H_OUTPUT_SCALE = 24
WORKING_MODULI = (
    4_611_686_018_427_387_701,
    4_611_686_018_427_387_709,
    4_611_686_018_427_387_733,
    4_611_686_018_427_387_737,
    4_611_686_018_427_387_751,
    4_611_686_018_427_387_761,
    4_611_686_018_427_387_787,
    4_611_686_018_427_387_817,
)
REDUNDANT_MODULUS = 4_611_686_018_427_387_847
ARMS = (
    "contract_first_direct_57_scan",
    "rank_truncated_zeta",
    "adr0454_prefix_branch_and_bound",
    "frozen_prefix_then_zeta_hybrid",
)
MODES = ("positive_witness", "prove_none")
BASES = (
    "exact_lattice_base",
    "opaque_per_source_base",
    "lattice_plus_exact_sparse_master_support_correction",
)
REFRESH = ("cold_base_refresh", "exact_provenance_hit")
SCHEDULES = ("positional", "batched_five_then_four_RRNS")
KERNELS = (
    "bind_provenance",
    "contract_h_positional",
    "contract_h_rrns_batch",
    "build_base_positional",
    "build_base_rrns_batch",
    "apply_sparse_patch_positional",
    "apply_sparse_patch_rrns_batch",
    "admit_rrns_first_batch",
    "admit_rrns_second_batch",
    "encode_positional_rrns_batch",
    "build_prefix_base_bounds",
    "build_prefix_term_bounds_positional",
    "build_prefix_term_bounds_rrns",
    "run_prefix_frontier",
    "run_hybrid_frontier",
    "evaluate_selected_leaves_positional",
    "evaluate_selected_leaves_rrns_batch",
    "direct_prices_positional",
    "direct_prices_rrns_batch",
    "zeta_seed_positional",
    "zeta_seed_rrns_batch",
    "zeta_cover_positional",
    "zeta_cover_rrns_batch",
    "zeta_rank_six_positional",
    "zeta_rank_six_rrns_batch",
    "validate_hybrid_switch",
    "terminal_scan",
    "restore_workspace",
)
PASSES = (0, 1, 2, 3, 4, 5)
MEASURED = (1, 2, 3, 4, 5)
PHASES = (
    "provenance_rebind",
    "H_component_contraction",
    "base_payload_transfer",
    "base_structural_cover",
    "base_sparse_patch",
    "arithmetic_encoding",
    "prefix_base_bound_build",
    "prefix_possible_term_bounds",
    "prefix_frontier_operations",
    "exact_leaf_57_term_evaluation",
    "direct_global_57_term_scan",
    "zeta_seed_write",
    "zeta_cover_edges",
    "zeta_rank_six_stream",
    "hybrid_switch",
    "RRNS_decision_key_reconstruction",
    "terminal_sign_witness_or_closure_reduction",
    "terminal_transfer",
    "workspace_baseline_restore",
)
PHASE_CALLBACKS = (
    "reset_and_bind",
    "contract",
    "payload_transfer",
    "structural_cover",
    "sparse_patch",
    "encode_and_admit",
    "prefix_base",
    "prefix_terms",
    "frontier",
    "selected_leaves",
    "direct",
    "zeta_seed",
    "zeta_cover",
    "zeta_stream",
    "hybrid_switch",
    "reconstruct_terminal_values",
    "terminal_reduce",
    "terminal_transfer",
    "restore",
)
COORDINATES = (
    "typed_tokens_compared",
    "signed_component_multiply_adds",
    "payload_bytes_transferred",
    "base_cover_edge_additions",
    "patch_entries_applied",
    "limb_words_or_residue_words_written",
    "descendant_base_values_read",
    "possible_or_guaranteed_terms_examined",
    "heap_pushes_plus_heap_pops_of_the_same_fixed_key_type",
    "subset_terms_evaluated",
    "subset_terms_evaluated",
    "seed_words_written",
    "cover_edge_additions",
    "source_prices_visited",
    "switch_state_transitions",
    "decision_keys_reconstructed",
    "exact_price_comparisons",
    "terminal_bytes_transferred",
    "workspace_bytes_cleared_or_rebound",
)
PUBLIC_WALL_NS = 1_800_000_000_000
LABORATORY_WALL_NS = 1_500_000_000_000
OUTSIDE_WALL_NS = 300_000_000_000
DEVICE_TOTAL_BYTES = 17_094_475_776
DEVICE_RESERVE_BYTES = 2_000_000_000
NAMED_DEVICE_PEAK_CEILING_BYTES = 12_000_000_000
REJECTED_LIVENESS_EQUIVALENCE = (
    "any configuration whose liveness peak reproduces a rejected arm's peak "
    "is that rejected arm, regardless of variable names; rejections attach "
    "to physics, not identifiers"
)
RESULT_BYTE_CEILING = 67_108_864

DEPENDENCY_RELATIVE_PATHS = (
    CONFIG_RELATIVE_PATH,
    "docs/decisions/ADR-0457-preregister-the-compiled-global-separation-calibration.md",
    "docs/decisions/ADR-0458-source-seal-the-compiled-global-separation-calibration.md",
    "run_legal_river_quotient_compiled_global_separation_calibration.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_runner.py",
    "src/pontius/legal_river_quotient_compiled_global_separation_calibration_result.py",
    "tests/test_legal_river_quotient_compiled_global_separation_calibration.py",
    "src/pontius/legal_river_quotient_base_provenance.py",
    "src/pontius/legal_river_quotient_global_separation_topologies.py",
    "src/pontius/legal_river_quotient_selective_certified_separation.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v2_runner.py",
    "src/pontius/legal_river_quotient_fixed_width_device_preflight_v3_runner.py",
    "src/pontius/durable_evidence_journal.py",
    "artifacts/work_preflight/.gitattributes",
)


@dataclass(frozen=True, slots=True)
class IndependentFit:
    intercept: Fraction
    slope: Fraction
    sse: Fraction
    guard: Fraction
    prediction: Fraction
    upper: Fraction
    ceiling: int
    candidate: str


@dataclass(frozen=True, slots=True)
class AssessedCalibration:
    terminal: str
    passed: bool
    complete: bool
    event_count: int
    scientific_call_count: int
    measured_call_count: int
    material_zeta_speed_claim: bool | None
    production_base_classification: str
    candidate_selected: None
    topology_selected: None
    arithmetic_schedule_selected: None
    source_commit: str
    raw_sha256: str


def _canonical_lf(raw: bytes) -> bytes:
    result = bytearray()
    cursor = 0
    while cursor < len(raw):
        byte = raw[cursor]
        if byte == 13 and cursor + 1 < len(raw) and raw[cursor + 1] == 10:
            result.append(10)
            cursor += 2
        else:
            result.append(byte)
            cursor += 1
    return bytes(result)


def _digest(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"calibration reader dependency is absent: {path}")
    return sha256(_canonical_lf(path.read_bytes())).hexdigest()


def _object(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _integer(value: object, *, label: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} is below its minimum")
    return value


def _validate_resource_rows(
    value: object, *, label: str, fields: tuple[str, ...]
) -> dict[str, Mapping[str, object]]:
    rows = _object(value, label=label)
    if tuple(rows) != KERNELS:
        raise ValueError(f"{label} kernel domain or order differs")
    output: dict[str, Mapping[str, object]] = {}
    for name in KERNELS:
        row = _object(rows[name], label=f"{label} {name}")
        if set(row) != {"kernel", *fields} or row.get("kernel") != name:
            raise ValueError(f"{label} row schema differs")
        for field in fields:
            _integer(row[field], label=f"{label} {field}", minimum=0)
        output[name] = row
    return output


def _fraction(value: object, *, label: str) -> Fraction:
    row = _object(value, label=label)
    if set(row) != {"numerator", "denominator"}:
        raise ValueError(f"{label} fraction domain differs")
    numerator = _integer(row["numerator"], label=f"{label} numerator")
    denominator = _integer(
        row["denominator"], label=f"{label} denominator", minimum=1
    )
    result = Fraction(numerator, denominator)
    if result.denominator != denominator:
        raise ValueError(f"{label} fraction is not canonical")
    return result


def verify_independent_contract() -> None:
    config_path = ROOT / CONFIG_RELATIVE_PATH
    if _digest(config_path) != CONFIG_SHA256:
        raise ValueError("calibration reader config identity differs")
    config = json.loads(config_path.read_bytes())
    if not isinstance(config, dict):
        raise ValueError("calibration reader config is not an object")
    scope = _object(config.get("scope"), label="scope")
    phases = _object(config.get("runtime_phase_partition"), label="phases")
    work = _object(config.get("work_ledger"), label="work")
    identity = _object(config.get("prospective_identity"), label="identity")
    if (
        config.get("schema_version")
        != "legal-river-quotient-compiled-global-separation-calibration-config-v1"
        or tuple(scope.get("calibration_card_domains", ())) != DOMAINS
        or scope.get("cells_per_pass") != 480
        or scope.get("total_scientific_cell_invocations") != 2_880
        or tuple(phases.get("ordered_phases", ())) != PHASES
        or tuple(_object(work.get("projection_coordinates"), label="coordinates"))
        != PHASES
        or tuple(
            _object(work.get("projection_coordinates"), label="coordinates").values()
        )
        != COORDINATES
        or identity.get("result_relative_path") != RESULT_RELATIVE_PATH
    ):
        raise ValueError("calibration reader frozen contract differs")


def dependency_hashes() -> dict[str, str]:
    return {relative: _digest(ROOT / relative) for relative in DEPENDENCY_RELATIVE_PATHS}


def _cell_key(row: Mapping[str, object]) -> str:
    return "|".join(
        (
            str(row["cards"]),
            str(row["arm"]),
            str(row["runtime_mode"]),
            str(row["base_mode"]),
            str(row["refresh_state"]),
            str(row["arithmetic_schedule"]),
        )
    )


def _expected_cells(pass_index: int) -> tuple[str, ...]:
    rows = (
        "|".join(map(str, values))
        for values in product(DOMAINS, ARMS, MODES, BASES, REFRESH, SCHEDULES)
    )
    return tuple(
        sorted(
            rows,
            key=lambda key: (
                sha256(f"adr0457|{pass_index}|{key}".encode("ascii")).digest(),
                key,
            ),
        )
    )


def _symbolic(cards: int) -> dict[str, int]:
    sources = comb(cards, 6)
    h_rows = sum(comb(cards, rank) for rank in range(5))
    level_rows = sum(comb(cards, rank) for rank in range(7))
    cover_edges = sum(rank * comb(cards, rank) for rank in range(1, 7))
    prefix_nodes = comb(cards + 1, 6)
    return {
        "sources": sources,
        "h_rows": h_rows,
        "level_rows": level_rows,
        "cover_edges": cover_edges,
        "prefix_nodes": prefix_nodes,
        "prefix_edges": prefix_nodes - 1,
    }


def _support_count(cards: int) -> int:
    sources = comb(cards, 6)
    return (sources + 256) // 257 + (0 if (sources - 1) % 257 == 0 else 1)


def _scratch_restore_bytes(cards: int, schedule: str) -> int:
    geometry = _symbolic(cards)
    if schedule not in SCHEDULES:
        raise ValueError("reader scratch schedule differs")
    support = _support_count(cards)
    arena_rows = max(
        geometry["h_rows"], geometry["sources"], geometry["level_rows"], support
    )
    return (
        4
        + 8
        + 80
        + 36 * geometry["prefix_nodes"]
        + 16 * geometry["h_rows"]
        + 16 * geometry["level_rows"]
        + 16 * support
        + 40 * arena_rows
    )


def _rrns_arena_bytes(cards: int) -> int:
    geometry = _symbolic(cards)
    return 40 * max(
        geometry["h_rows"],
        geometry["sources"],
        geometry["level_rows"],
        _support_count(cards),
    )


def _domain_memory_peak(cards: int) -> int:
    geometry = _symbolic(cards)
    sources = geometry["sources"]
    levels = geometry["level_rows"]
    support = _support_count(cards)
    return sum(
        (
            2 * geometry["h_rows"] * 176 * 8,
            176 * 8,
            37 * geometry["prefix_nodes"] + 4,
            72 + 20 + 16 + 96,
            32 * sources + 64 * support + 64,
            1_152 + 192 * sources + 192 * levels,
            4,
            _scratch_restore_bytes(cards, SCHEDULES[0])
            - 4
            - _rrns_arena_bytes(cards)
            + 40 * sources,
            _rrns_arena_bytes(cards),
        )
    )


def _campaign_memory_peak() -> int:
    return (
        sum(_domain_memory_peak(cards) - _rrns_arena_bytes(cards) for cards in DOMAINS)
        + max(_rrns_arena_bytes(cards) for cards in DOMAINS)
    )


def _expected_liveness(peak: int) -> dict[str, object]:
    return {
        "peak_bytes": peak,
        "peak_boundaries": list(range(20)),
        "boundary_live_bytes": [peak] * 20 + [0],
        "alias_checked": True,
        "ceiling_passed": peak <= NAMED_DEVICE_PEAK_CEILING_BYTES,
        "reserve_passed": peak + DEVICE_RESERVE_BYTES <= DEVICE_TOTAL_BYTES,
    }


def _width_row(quantity: str, bound: int) -> dict[str, object]:
    bits = 1 if bound == 0 else bound.bit_length() + 1
    limbs = (bits + 63) // 64
    return {
        "quantity": quantity,
        "signed_absolute_bound": bound,
        "required_signed_bits": bits,
        "mathematical_limbs": limbs,
        "guard_inclusive_limbs": limbs + 1,
    }


def _zeta_h_bound(rank: int) -> int:
    return sum(
        comb(rank, level) * abs(H_SEED_WEIGHTS[level]) * factorial(rank - level)
        for level in range(min(rank, 4) + 1)
    )


def _expected_arithmetic_admission() -> dict[str, object]:
    raw_terminal_bound = 175 * 8 * 9 + 1
    direct_h_bound = sum(
        comb(6, level) * abs(PRICE_COEFFICIENTS[level]) for level in range(5)
    )
    zeta_h = _zeta_h_bound(6)
    if zeta_h != H_OUTPUT_SCALE * direct_h_bound:
        raise ArithmeticError("reader H circuit bound identity differs")
    base_bound = 722
    output_scaled = zeta_h + H_OUTPUT_SCALE * base_bound + H_OUTPUT_SCALE
    quantity = [
        _width_row("raw_H_component", raw_terminal_bound),
        _width_row("pricing_component", 9),
        _width_row("H_component_product", raw_terminal_bound * 9),
        _width_row("H_contraction_accumulator", 2 * 175 * 8 * 9 + 1),
        _width_row("contracted_h", 1),
        _width_row("base_value", base_bound),
        _width_row("base_structural_level", factorial(6) * base_bound),
        _width_row("direct_price_accumulator", direct_h_bound + base_bound),
        _width_row("prefix_bound", direct_h_bound + base_bound),
        _width_row("zeta_output_scaled", output_scaled),
        _width_row("terminal_price", output_scaled // H_OUTPUT_SCALE),
        _width_row("RRNS_decision_key", output_scaled),
    ]
    zeta = [
        _width_row(
            f"zeta_rank_{rank}",
            _zeta_h_bound(rank) + factorial(rank) * base_bound,
        )
        for rank in range(7)
    ]
    working_product = 1
    for modulus in WORKING_MODULI:
        working_product *= modulus
    all_bounds = [
        int(row["signed_absolute_bound"]) for row in (*quantity, *zeta)
    ]
    payload = {
        "quantity_widths": quantity,
        "zeta_rank_widths": zeta,
        "working_product_decimal": str(working_product),
        "redundant_modulus": REDUNDANT_MODULUS,
        "table_range_sufficient": (
            WORKING_MODULI[0]
            * WORKING_MODULI[1]
            * WORKING_MODULI[2]
            * WORKING_MODULI[3]
            >= 2 * max(int(row["signed_absolute_bound"]) for row in zeta) + 1
        ),
        "scalar_range_sufficient": working_product >= 2 * max(all_bounds) + 1,
        "bounded_single_modulus_decision_sufficient": min(WORKING_MODULI)
        >= 2 * max(all_bounds) + 1,
    }
    return {
        "schema_version": "pontius-adr0457-arithmetic-admission-v1",
        **payload,
        "sha256": sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
                "ascii"
            )
        ).hexdigest(),
    }


def _work(cell: Mapping[str, object], *, target: bool) -> dict[str, int]:
    original_cards = _integer(cell["cards"], label="cell cards")
    cards = TARGET_CARDS if target else original_cards
    geometry = _symbolic(cards)
    sources = geometry["sources"]
    h_rows = geometry["h_rows"]
    arm = str(cell["arm"])
    mode = str(cell["runtime_mode"])
    base = str(cell["base_mode"])
    refresh = str(cell["refresh_state"])
    schedule = str(cell["arithmetic_schedule"])
    prefix = arm in ARMS[2:]
    direct = arm == ARMS[0]
    hybrid = arm == ARMS[3]
    zeta_runs = arm == ARMS[1] or (hybrid and mode == "prove_none")
    positive = mode == "positive_witness"
    cold = refresh == "cold_base_refresh"
    rrns = schedule == SCHEDULES[1]
    structural = base != BASES[1]
    mixed = base == BASES[2]
    support = _support_count(cards)
    payload = 0
    if cold:
        payload = sources * 8 if base == BASES[1] else 8 + (support * 16 if mixed else 0)
    scan = 1 if positive else sources
    early = (sources + 63) // 64
    hard = (sources + 7) // 8
    leaves = 1 if prefix and positive else hard if hybrid and not positive and target else early if hybrid and not positive else 0
    values = {
        "provenance_rebind": 12,
        "H_component_contraction": h_rows * 176,
        "base_payload_transfer": payload,
        "base_structural_cover": geometry["cover_edges"] if cold and structural else 0,
        "base_sparse_patch": support if cold and mixed else 0,
        "arithmetic_encoding": 11 * sources if rrns else 0,
        "prefix_base_bound_build": sources + geometry["prefix_edges"] if prefix else 0,
        "prefix_possible_term_bounds": geometry["prefix_nodes"] * (1 if positive else cards) if prefix else 0,
        "prefix_frontier_operations": (6 * cards - 22) if prefix and positive and target else 2 * geometry["prefix_nodes"] if prefix else 0,
        "exact_leaf_57_term_evaluation": leaves * 57,
        "direct_global_57_term_scan": scan * 57 if direct else 0,
        "zeta_seed_write": h_rows * (11 if rrns else 2) if zeta_runs else 0,
        "zeta_cover_edges": geometry["cover_edges"] if zeta_runs else 0,
        "zeta_rank_six_stream": scan if zeta_runs else 0,
        "hybrid_switch": 1 if hybrid and not positive else 0,
        "RRNS_decision_key_reconstruction": scan if rrns and (direct or zeta_runs) else 0,
        "terminal_sign_witness_or_closure_reduction": scan if direct or zeta_runs else 0,
        "terminal_transfer": 92,
        "workspace_baseline_restore": _scratch_restore_bytes(cards, schedule),
    }
    return values


def _expected_cell_receipts(
    cell: Mapping[str, object], terminal: Mapping[str, object]
) -> tuple[dict[str, int], dict[str, int], dict[str, int], dict[str, int]]:
    work = _work(cell, target=False)
    cards = _integer(cell["cards"], label="receipt cards")
    geometry = _symbolic(cards)
    arm = str(cell["arm"])
    mode = str(cell["runtime_mode"])
    base = str(cell["base_mode"])
    refresh = str(cell["refresh_state"])
    schedule = str(cell["arithmetic_schedule"])
    rrns = schedule == SCHEDULES[1]
    prefix = arm in ARMS[2:]
    direct = arm == ARMS[0]
    hybrid = arm == ARMS[3]
    zeta_runs = arm == ARMS[1] or (hybrid and mode == "prove_none")
    cold = refresh == REFRESH[0]
    scan = 1 if mode == "positive_witness" else geometry["sources"]
    exact_leaves = _integer(
        terminal.get("exact_leaves"), label="receipt exact leaves", minimum=0
    )
    if prefix:
        work["prefix_frontier_operations"] = _integer(
            terminal.get("heap_pushes"), label="receipt heap pushes", minimum=0
        ) + _integer(terminal.get("heap_pops"), label="receipt heap pops", minimum=0)
        work["exact_leaf_57_term_evaluation"] = exact_leaves * 57
    support = _support_count(cards)
    arithmetic = {name: 0 for name in PHASES}
    arithmetic["H_component_contraction"] = (11 if rrns else 2) * geometry["h_rows"]
    if cold and base == BASES[1]:
        arithmetic["base_payload_transfer"] = (11 if rrns else 2) * geometry["sources"]
    if cold and base != BASES[1]:
        arithmetic["base_structural_cover"] = (11 if rrns else 2) * (
            geometry["sources"] + geometry["level_rows"]
        )
    if cold and base == BASES[2]:
        arithmetic["base_sparse_patch"] = (13 if rrns else 2) * support
    arithmetic["arithmetic_encoding"] = 11 * geometry["sources"] if rrns else 0
    arithmetic["prefix_base_bound_build"] = 2 * geometry["prefix_nodes"] if prefix else 0
    arithmetic["prefix_possible_term_bounds"] = 2 * geometry["prefix_nodes"] if prefix else 0
    arithmetic["exact_leaf_57_term_evaluation"] = (11 if rrns else 2) * exact_leaves
    arithmetic["direct_global_57_term_scan"] = (11 if rrns else 2) * scan if direct else 0
    arithmetic["zeta_seed_write"] = (11 if rrns else 2) * geometry["h_rows"] if zeta_runs else 0
    arithmetic["zeta_cover_edges"] = (11 if rrns else 2) * (geometry["level_rows"] - 1) if zeta_runs else 0
    arithmetic["zeta_rank_six_stream"] = (11 if rrns else 2) * scan if zeta_runs else 0
    arithmetic["RRNS_decision_key_reconstruction"] = 11 * scan if rrns and (direct or zeta_runs) else 0
    decisions = {name: 0 for name in PHASES}
    if rrns:
        decisions["H_component_contraction"] = geometry["h_rows"]
        if cold and base == BASES[1]:
            decisions["base_payload_transfer"] = geometry["sources"]
        if cold and base != BASES[1]:
            decisions["base_structural_cover"] = geometry["sources"] + geometry["level_rows"]
        if cold and base == BASES[2]:
            decisions["base_sparse_patch"] = support
        decisions["arithmetic_encoding"] = geometry["sources"]
        decisions["prefix_possible_term_bounds"] = geometry["prefix_nodes"] if prefix else 0
        decisions["exact_leaf_57_term_evaluation"] = exact_leaves
        decisions["direct_global_57_term_scan"] = scan if direct else 0
        decisions["zeta_seed_write"] = geometry["h_rows"] if zeta_runs else 0
        decisions["zeta_cover_edges"] = geometry["level_rows"] - 1 if zeta_runs else 0
        decisions["zeta_rank_six_stream"] = scan if zeta_runs else 0
        decisions["RRNS_decision_key_reconstruction"] = scan if direct or zeta_runs else 0
    transfers = {name: 0 for name in PHASES}
    transfers["provenance_rebind"] = 176 * 8
    transfers["base_payload_transfer"] = work["base_payload_transfer"]
    transfers["terminal_transfer"] = 92
    return work, arithmetic, decisions, transfers


def _ceil(value: Fraction) -> int:
    return -(-value.numerator // value.denominator)


def independent_fit(xs_raw: Sequence[int], ys_raw: Sequence[int], target_raw: int) -> IndependentFit:
    if len(xs_raw) != 5 or len(ys_raw) != 5:
        raise ValueError("reader fit requires five domains")
    xs = tuple(Fraction(_integer(value, label="fit x", minimum=0)) for value in xs_raw)
    ys = tuple(Fraction(_integer(value, label="fit y", minimum=0)) for value in ys_raw)
    target = Fraction(_integer(target_raw, label="target work", minimum=0))
    if len(set(xs)) == 1:
        candidates = (("constant_coordinate", max(ys), Fraction()),)
    else:
        count = Fraction(5)
        sx = sum(xs, Fraction())
        sy = sum(ys, Fraction())
        sxx = sum((value * value for value in xs), Fraction())
        sxy = sum((x * y for x, y in zip(xs, ys, strict=True)), Fraction())
        denominator = count * sxx - sx * sx
        slope = (count * sxy - sx * sy) / denominator
        intercept = (sy - slope * sx) / count
        rows = []
        if intercept >= 0 and slope >= 0:
            rows.append(("feasible_unconstrained_ordinary_least_squares", intercept, slope))
        rows.extend(
            (
                ("slope_zero", sy / count, Fraction()),
                ("intercept_zero", Fraction(), max(Fraction(), sxy / sxx) if sxx else Fraction()),
                ("zero", Fraction(), Fraction()),
            )
        )
        candidates = tuple(rows)

    def score(row: tuple[str, Fraction, Fraction]) -> tuple[Fraction, Fraction, Fraction, Fraction]:
        _, intercept, slope = row
        sse = sum(
            ((y - intercept - slope * x) ** 2 for x, y in zip(xs, ys, strict=True)),
            Fraction(),
        )
        return sse, -(intercept + slope * target), -intercept, -slope

    candidate, intercept, slope = min(candidates, key=score)
    sse = score((candidate, intercept, slope))[0]
    guard = max(
        (Fraction(), *(y - intercept - slope * x for x, y in zip(xs, ys, strict=True)))
    )
    prediction = intercept + slope * target
    upper = Fraction(5, 4) * (prediction + guard)
    return IndependentFit(intercept, slope, sse, guard, prediction, upper, _ceil(upper), candidate)


def _validate_header(header: Mapping[str, object]) -> str:
    if (
        header.get("schema_version") != "pontius-adr0457-owner-header-v1"
        or header.get("protocol_sha256") != PROTOCOL_SHA256
        or header.get("campaign_sha256") != CAMPAIGN_SHA256
        or header.get("config_sha256") != CONFIG_SHA256
        or header.get("preregistration_commit") != PREREGISTRATION_COMMIT
        or header.get("result_relative_path") != RESULT_RELATIVE_PATH
        or header.get("calls_under_one_public_owner") != 2_880
        or header.get("dependency_hashes") != dependency_hashes()
    ):
        raise ValueError("calibration journal header identity differs")
    git = _object(header.get("source_seal_git"), label="source seal git")
    commit = git.get("commit")
    if (
        not isinstance(commit, str)
        or len(commit) != 40
        or any(character not in "0123456789abcdef" for character in commit)
        or git.get("dirty") is not False
        or git.get("strict_status") is not True
    ):
        raise ValueError("calibration source seal identity differs")
    claims = _object(header.get("claims"), label="header claims")
    if (
        claims.get("production_base_classification") != "producer_absent"
        or claims.get("candidate_selected") is not None
        or claims.get("topology_selected") is not None
        or claims.get("arithmetic_schedule_selected") is not None
    ):
        raise ValueError("calibration header claims differ")
    return commit


def _validate_cell_events(events: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    if len(events) != 2_880:
        raise ValueError("calibration scientific call count differs")
    rows = []
    complete_positive: set[tuple[int, str, str, str]] = set()
    cursor = 0
    for pass_index in PASSES:
        expected = _expected_cells(pass_index)
        observed = []
        for expected_key in expected:
            wrapper = events[cursor]
            cursor += 1
            event = _object(wrapper.get("event"), label="calibration cell event")
            if event.get("schema_version") != "pontius-adr0457-calibration-cell-v1":
                raise ValueError("calibration cell schema differs")
            if event.get("pass_index") != pass_index:
                raise ValueError("calibration pass order differs")
            key = event.get("canonical_cell_key")
            if key != expected_key:
                raise ValueError("calibration deterministic cell order differs")
            observed.append(str(key))
            cell = _object(event.get("cell"), label="cell key")
            if _cell_key(cell) != key:
                raise ValueError("calibration canonical key disagrees")
            if event.get("measured") is not (pass_index in MEASURED):
                raise ValueError("calibration measured bit differs")
            partition = _object(event.get("phase_partition"), label="phase partition")
            phase_rows = partition.get("rows")
            if not isinstance(phase_rows, list) or len(phase_rows) != len(PHASES):
                raise ValueError("calibration phase row domain differs")
            terminal = _object(event.get("terminal"), label="cell terminal")
            expected_work, expected_arithmetic, expected_decisions, expected_transfers = (
                _expected_cell_receipts(cell, terminal)
            )
            elapsed = 0
            previous_end = None
            for index, phase in enumerate(phase_rows):
                item = _object(phase, label="phase")
                if (
                    item.get("name") != PHASES[index]
                    or item.get("projection_coordinate") != COORDINATES[index]
                ):
                    raise ValueError("calibration phase name or coordinate differs")
                start = _integer(item.get("start_ns"), label="phase start", minimum=0)
                end = _integer(item.get("end_ns"), label="phase end", minimum=0)
                wall = _integer(item.get("elapsed_ns"), label="phase wall", minimum=0)
                _integer(
                    item.get("device_elapsed_ns"),
                    label="device phase wall",
                    minimum=0,
                )
                if end - start != wall or (previous_end is not None and start != previous_end):
                    raise ValueError("calibration phase partition has a gap or overlap")
                previous_end = end
                elapsed += wall
                for count_name in (
                    "projection_work",
                    "logical_operations",
                    "arithmetic_words",
                    "transferred_bytes",
                    "decision_keys_reconstructed",
                ):
                    _integer(item.get(count_name), label=f"phase {count_name}", minimum=0)
                phase_name = PHASES[index]
                if (
                    item.get("projection_work") != expected_work[phase_name]
                    or item.get("logical_operations") != expected_work[phase_name]
                    or item.get("arithmetic_words") != expected_arithmetic[phase_name]
                    or item.get("transferred_bytes") != expected_transfers[phase_name]
                    or item.get("decision_keys_reconstructed")
                    != expected_decisions[phase_name]
                ):
                    raise ValueError("calibration phase work receipt differs")
            if elapsed != partition.get("primitive_total_ns"):
                raise ValueError("calibration phase sum differs from primitive wall")
            if cell.get("runtime_mode") == "positive_witness":
                if terminal.get("found_positive") != 1 or _integer(
                    terminal.get("witness_price"), label="witness price"
                ) <= 0:
                    raise ValueError("calibration positive-witness terminal differs")
            elif terminal.get("globally_closed") != 1:
                raise ValueError("calibration prove-none terminal differs")
            expected_prefix_keys = (
                _symbolic(_integer(cell["cards"], label="prefix cards"))["prefix_nodes"]
                if cell.get("arithmetic_schedule") == SCHEDULES[1]
                and cell.get("arm") in ARMS[2:]
                else 0
            )
            if terminal.get("prefix_decision_keys") != expected_prefix_keys:
                raise ValueError("calibration prefix decision receipt differs")
            differential = _object(wrapper.get("differential"), label="differential")
            if (
                differential.get("canonical_cell_key") != key
                or differential.get("unbounded_integer_authority_matched") is not True
            ):
                raise ValueError("calibration differential differs")
            complete = differential.get("complete_positive_output")
            if complete is not None:
                full = _object(complete, label="complete positive differential")
                full_key = (
                    _integer(cell["cards"], label="complete cards"),
                    str(cell["arm"]),
                    str(cell["base_mode"]),
                    str(cell["arithmetic_schedule"]),
                )
                if (
                    cell.get("runtime_mode") != "positive_witness"
                    or cell.get("arm") not in ARMS[:2]
                    or full_key in complete_positive
                    or full.get("schema_version")
                    != "pontius-adr0457-complete-positive-differential-v1"
                    or full.get("canonical_cell_key") != key
                    or full.get("authority_coordinates_checked")
                    != comb(full_key[0], 6)
                    or full.get("unbounded_integer_authority_matched") is not True
                    or full.get("laboratory_only") is not True
                ):
                    raise ValueError("complete positive differential differs")
                complete_positive.add(full_key)
            rows.append(event)
        if tuple(observed) != expected:
            raise AssertionError("calibration pass permutation differs")
    expected_complete = set(product(DOMAINS, ARMS[:2], BASES, SCHEDULES))
    if complete_positive != expected_complete:
        raise ValueError("complete positive differential domain differs")
    return rows


def _recompute_projection(
    cells: Sequence[Mapping[str, object]], stored: Mapping[str, object]
) -> bool:
    groups: dict[tuple[str, str, str, str, str], dict[int, list[Mapping[str, object]]]] = {}
    for event in cells:
        if event.get("measured") is not True:
            continue
        cell = _object(event.get("cell"), label="fit cell")
        key = tuple(
            str(cell[name])
            for name in (
                "arm",
                "runtime_mode",
                "base_mode",
                "refresh_state",
                "arithmetic_schedule",
            )
        )
        cards = _integer(cell["cards"], label="fit cards")
        groups.setdefault(key, {}).setdefault(cards, []).append(event)
    fit_rows = stored.get("fit_rows")
    primitive_rows = stored.get("primitive_rows")
    materiality_rows = stored.get("materiality_rows")
    if not isinstance(fit_rows, list) or not isinstance(primitive_rows, list) or not isinstance(materiality_rows, list):
        raise ValueError("stored projection rows differ")
    stored_fits = {
        (
            row["arm"],
            row["runtime_mode"],
            row["base_mode"],
            row["refresh_state"],
            row["arithmetic_schedule"],
            row["phase"],
        ): row
        for row in fit_rows
        if isinstance(row, dict)
    }
    if len(stored_fits) != 4 * 2 * 3 * 2 * 2 * 19:
        raise ValueError("stored fit-row domain differs")
    primitive: dict[tuple[str, str, str, str, str], int] = {}
    for key, domains in groups.items():
        if tuple(sorted(domains)) != DOMAINS:
            raise ValueError("projection drops a card domain")
        target_cell = {
            "cards": DOMAINS[0],
            "arm": key[0],
            "runtime_mode": key[1],
            "base_mode": key[2],
            "refresh_state": key[3],
            "arithmetic_schedule": key[4],
        }
        target = _work(target_cell, target=True)
        ceilings = []
        for phase_index, phase_name in enumerate(PHASES):
            xs = []
            ys = []
            for cards in DOMAINS:
                rows = domains[cards]
                if len(rows) != 5:
                    raise ValueError("projection drops a measured repeat")
                phase_rows = [
                    _object(_object(row["phase_partition"], label="partition")["rows"][phase_index], label="phase")
                    for row in rows
                ]
                works = {_integer(row["projection_work"], label="fit work", minimum=0) for row in phase_rows}
                if len(works) != 1:
                    raise ValueError("projection work changes across repeats")
                xs.append(next(iter(works)))
                ys.append(max(_integer(row["elapsed_ns"], label="fit wall", minimum=0) for row in phase_rows))
            fit = independent_fit(xs, ys, target[phase_name])
            stored_fit = _object(stored_fits[key + (phase_name,)], label="stored fit")
            if (
                stored_fit.get("candidate") != fit.candidate
                or _fraction(stored_fit.get("intercept"), label="intercept") != fit.intercept
                or _fraction(stored_fit.get("slope"), label="slope") != fit.slope
                or _fraction(stored_fit.get("sse"), label="sse") != fit.sse
                or _fraction(stored_fit.get("positive_residual_guard"), label="guard") != fit.guard
                or _fraction(stored_fit.get("target_prediction"), label="prediction") != fit.prediction
                or _fraction(stored_fit.get("target_upper"), label="upper") != fit.upper
                or stored_fit.get("target_upper_ceiling_ns") != fit.ceiling
                or stored_fit.get("target_work") != target[phase_name]
            ):
                raise ValueError("stored affine fit differs from independent reconstruction")
            ceilings.append(fit.ceiling)
        primitive[key] = sum(ceilings)
    stored_primitive = {
        tuple(
            str(row[name])
            for name in (
                "arm",
                "runtime_mode",
                "base_mode",
                "refresh_state",
                "arithmetic_schedule",
            )
        ): row
        for row in primitive_rows
        if isinstance(row, dict)
    }
    if set(stored_primitive) != set(primitive):
        raise ValueError("stored primitive projection domain differs")
    for key, value in primitive.items():
        row = stored_primitive[key]
        if row.get("projected_primitive_upper_ns") != value:
            raise ValueError("stored primitive upper differs")
    expected_materiality = []
    for base, refresh, schedule in product(BASES, REFRESH, SCHEDULES):
        direct = primitive[(ARMS[0], "prove_none", base, refresh, schedule)]
        zeta = primitive[(ARMS[1], "prove_none", base, refresh, schedule)]
        expected_materiality.append(
            {
                "base_mode": base,
                "refresh_state": refresh,
                "arithmetic_schedule": schedule,
                "direct_upper_ns": direct,
                "zeta_upper_ns": zeta,
                "zeta_at_most_half_direct": 2 * zeta <= direct,
            }
        )
    if materiality_rows != expected_materiality:
        raise ValueError("stored materiality conjuncts differ")
    claim = all(row["zeta_at_most_half_direct"] for row in expected_materiality)
    if stored.get("material_zeta_speed_claim") is not claim:
        raise ValueError("stored materiality claim differs")
    if any(
        stored.get(name) is not None
        for name in (
            "candidate_selected",
            "topology_selected",
            "arithmetic_schedule_selected",
        )
    ) or stored.get("production_base_classification") != "producer_absent":
        raise ValueError("projection selected a topology without a production base")
    return claim


def assess_calibration_bytes(raw: bytes) -> AssessedCalibration:
    verify_independent_contract()
    if type(raw) is not bytes or len(raw) > RESULT_BYTE_CEILING:
        raise ValueError("calibration result bytes differ")
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=PROTOCOL_SHA256,
        expected_campaign_sha256=CAMPAIGN_SHA256,
    )
    if not recovery.is_complete:
        reason = recovery.failure.reason if recovery.failure else "journal lacks terminal"
        raise ValueError(f"calibration journal is incomplete: {reason}")
    records = recovery.records
    if records[0].body.kind is not JournalRecordKind.HEADER:
        raise ValueError("calibration journal omits header")
    source_commit = _validate_header(records[0].body.payload)
    terminal = records[-1].body.payload
    if terminal.get("schema_version") != "pontius-adr0457-owner-terminal-v1":
        raise ValueError("calibration owner terminal schema differs")
    name = terminal.get("terminal")
    passed = terminal.get("passed")
    if not isinstance(name, str) or not isinstance(passed, bool):
        raise ValueError("calibration owner terminal differs")
    if passed is not (name == "completed_reduced_compiled_calibration_production_base_absent"):
        raise ValueError("calibration owner terminal pass bit differs")
    if terminal.get("event_count") != len(records) - 2:
        raise ValueError("calibration terminal event count differs")
    public = _integer(terminal.get("public_elapsed_ns"), label="public wall", minimum=0)
    laboratory_raw = terminal.get("laboratory_elapsed_ns")
    laboratory = None if laboratory_raw is None else _integer(laboratory_raw, label="laboratory wall", minimum=0)
    outside_raw = terminal.get("outside_laboratory_elapsed_ns")
    outside = None if outside_raw is None else _integer(outside_raw, label="outside wall")
    if (
        terminal.get("public_wall_ns") != PUBLIC_WALL_NS
        or terminal.get("laboratory_wall_ns") != LABORATORY_WALL_NS
        or terminal.get("outside_laboratory_wall_ns") != OUTSIDE_WALL_NS
    ):
        raise ValueError("calibration owner wall ceilings differ")
    if laboratory is not None and outside != public - laboratory:
        raise ValueError("calibration outside-laboratory partition differs")
    observations = []
    kinds = []
    for index, record in enumerate(records[1:-1]):
        if record.body.kind is not JournalRecordKind.OBSERVATION:
            raise ValueError("calibration nonterminal record kind differs")
        wrapper = record.body.payload
        if (
            wrapper.get("schema_version") != "pontius-adr0457-owner-observation-v1"
            or wrapper.get("event_index") != index
            or wrapper.get("source_commit") != source_commit
        ):
            raise ValueError("calibration observation wrapper differs")
        kinds.append(wrapper.get("kind"))
        observations.append(wrapper)
    if not passed:
        if name == "completed_reduced_compiled_calibration_production_base_absent":
            raise ValueError("rejecting result uses the success terminal")
        return AssessedCalibration(
            str(name),
            False,
            True,
            len(observations),
            sum(kind == "calibration_cell" for kind in kinds),
            0,
            None,
            "producer_absent",
            None,
            None,
            None,
            source_commit,
            sha256(raw).hexdigest(),
        )
    if public > PUBLIC_WALL_NS or laboratory is None or laboratory > LABORATORY_WALL_NS or outside is None or outside > OUTSIDE_WALL_NS:
        raise ValueError("successful calibration exceeds a frozen wall")
    expected_prefix = (
        "bootstrap_handshake",
        "production_base_audit",
        "fixture_authority",
        "arithmetic_admission",
        "hybrid_switch_controls",
        "source_contract",
        "cuda_source_materialization",
        "tool_versions",
        "compile",
        "durable_cubin_capture",
        "resource_command",
        "resource_command",
        "compile_resource_evidence",
        "module_load_and_runtime",
        "device_memory_admission",
        *("device_domain_prepared" for _ in DOMAINS),
    )
    if tuple(kinds[: len(expected_prefix)]) != expected_prefix:
        raise ValueError("calibration bootstrap, audit, or preparation order differs")
    prefix_events = [
        _object(row.get("event"), label="prefix event")
        for row in observations[: len(expected_prefix)]
    ]
    bootstrap = prefix_events[0]
    base_audit = prefix_events[1]
    fixture = prefix_events[2]
    if (
        bootstrap.get("cupy_loaded") is not False
        or bootstrap.get("scientific_source_loaded") is not False
        or base_audit.get("classification") != "producer_absent"
        or base_audit.get("audit_precedes_fixture_and_device_science") is not True
        or fixture.get("synthetic_controls_are_not_a_production_base") is not True
        or not isinstance(fixture.get("manifests"), list)
        or len(fixture["manifests"]) != 30
    ):
        raise ValueError("calibration bootstrap or production-base boundary differs")
    if prefix_events[3] != _expected_arithmetic_admission():
        raise ValueError("calibration arithmetic admission differs")
    source_contract = prefix_events[5]
    materialization = prefix_events[6]
    timed_host = _object(
        source_contract.get("timed_host_surface"), label="timed host surface"
    )
    source_sha = source_contract.get("cuda_source_sha256")
    if (
        source_contract.get("schema_version")
        != "pontius-adr0457-cuda-source-contract-v1"
        or source_contract.get("entry_kernels") != list(KERNELS)
        or source_contract.get("full_codeword_reconstruction_call_sites") != 1
        or source_contract.get("batched_admission_consumer_sites") != 2
        or source_contract.get("resident_nine_schedule_present") is not False
        or source_contract.get("host_scientific_arithmetic_present") is not False
        or source_contract.get("compiler_executed") is not False
        or source_contract.get("device_queried") is not False
        or timed_host
        != {
            "schema_version": "pontius-adr0458-timed-host-surface-v1",
            "phase_callbacks": list(PHASE_CALLBACKS),
            "host_prefix_authority_calls": 0,
            "host_unbounded_scientific_comparisons": 0,
            "nonterminal_device_to_host_scientific_transfers": 0,
            "passed": True,
        }
        or not isinstance(source_sha, str)
        or len(source_sha) != 64
        or materialization.get("schema_version")
        != "pontius-adr0457-source-materialization-v1"
        or materialization.get("cuda_source_sha256") != source_sha
        or materialization.get("entry_kernels") != list(KERNELS)
    ):
        raise ValueError("calibration source or timed-host contract differs")
    compile_resources = prefix_events[12]
    if (
        compile_resources.get("schema_version")
        != "pontius-adr0457-compile-resources-v1"
        or compile_resources.get("register_ceiling") != 255
        or compile_resources.get("spill_store_ceiling_bytes") != 0
        or compile_resources.get("spill_load_ceiling_bytes") != 0
        or compile_resources.get("ptxas_cubin_and_SASS_fields_remain_separate")
        is not True
        or compile_resources.get("passed") is not True
    ):
        raise ValueError("calibration compile-resource contract differs")
    ptxas = _validate_resource_rows(
        compile_resources.get("ptxas"),
        label="ptxas resources",
        fields=(
            "registers",
            "stack_frame_bytes",
            "spill_store_bytes",
            "spill_load_bytes",
        ),
    )
    _validate_resource_rows(
        compile_resources.get("cuobjdump"),
        label="cuobjdump resources",
        fields=("registers", "stack_bytes", "local_bytes", "shared_bytes"),
    )
    _validate_resource_rows(
        compile_resources.get("sass"),
        label="SASS local sites",
        fields=("local_load_sites", "local_store_sites"),
    )
    if any(
        _integer(row["registers"], label="ptxas registers") > 255
        or _integer(row["spill_store_bytes"], label="ptxas spill stores") != 0
        or _integer(row["spill_load_bytes"], label="ptxas spill loads") != 0
        for row in ptxas.values()
    ):
        raise ValueError("calibration ptxas resource ceiling differs")
    module_event = prefix_events[13]
    if (
        module_event.get("schema_version")
        != "pontius-adr0457-module-runtime-v1"
        or module_event.get("kernel_count") != len(KERNELS)
        or module_event.get("one_stream") is not True
        or module_event.get(
            "stack_local_backing_and_static_local_instruction_sites_reported_separately"
        )
        is not True
    ):
        raise ValueError("calibration module-resource contract differs")
    _validate_resource_rows(
        module_event.get("driver"),
        label="driver resources",
        fields=(
            "registers",
            "local_bytes",
            "shared_bytes",
            "maximum_threads_per_block",
        ),
    )
    memory = prefix_events[14]
    if (
        memory.get("schema_version")
        != "pontius-adr0457-device-memory-admission-v1"
        or memory.get("physical_RRNS_table_arena_allocations") != 1
        or memory.get("RRNS_table_arena_channel_capacity") != 5
        or memory.get("five_channel_table_workspace_only") is not True
        or memory.get("resident_nine_table_workspace") is not False
        or memory.get("allocation_precedes_warmup") is not True
        or memory.get("rejected_liveness_equivalence")
        != REJECTED_LIVENESS_EQUIVALENCE
        or memory.get("campaign") != _expected_liveness(_campaign_memory_peak())
    ):
        raise ValueError("calibration physical memory admission differs")
    for cards, event in zip(DOMAINS, prefix_events[15:], strict=True):
        expected_domain_memory = {
            "shared_five_channel_replay": _expected_liveness(
                _domain_memory_peak(cards)
            )
        }
        if (
            event.get("schema_version")
            != "pontius-adr0457-device-domain-prepared-v1"
            or event.get("cards") != cards
            or event.get("memory") != expected_domain_memory
            or event.get("allocation_precedes_warmup") is not True
        ):
            raise ValueError("calibration domain memory admission differs")
    cell_wrappers = [row for row in observations if row.get("kind") == "calibration_cell"]
    cells = _validate_cell_events(cell_wrappers)
    fit_wrappers = [row for row in observations if row.get("kind") == "fit_projection"]
    terminal_wrappers = [row for row in observations if row.get("kind") == "terminal_evidence"]
    if len(fit_wrappers) != 1 or len(terminal_wrappers) != 1:
        raise ValueError("calibration fit or scientific terminal count differs")
    expected_suffix = ("fit_projection", "terminal_evidence")
    if tuple(kinds[-2:]) != expected_suffix:
        raise ValueError("calibration fit/terminal order differs")
    stored_projection = _object(fit_wrappers[0].get("event"), label="fit projection")
    materiality = _recompute_projection(cells, stored_projection)
    scientific_terminal = _object(
        terminal_wrappers[0].get("event"), label="scientific terminal"
    )
    if (
        scientific_terminal.get("terminal")
        != "completed_reduced_compiled_calibration_production_base_absent"
        or scientific_terminal.get("passed") is not True
        or scientific_terminal.get("scientific_call_count") != 2_880
        or scientific_terminal.get("measured_call_count") != 2_400
        or scientific_terminal.get("complete_positive_differential_count") != 60
        or scientific_terminal.get("production_base_classification") != "producer_absent"
        or any(
            scientific_terminal.get(name) is not None
            for name in (
                "candidate_selected",
                "topology_selected",
                "arithmetic_schedule_selected",
            )
        )
    ):
        raise ValueError("calibration scientific terminal differs")
    return AssessedCalibration(
        str(name),
        True,
        True,
        len(observations),
        len(cells),
        2_400,
        materiality,
        "producer_absent",
        None,
        None,
        None,
        source_commit,
        sha256(raw).hexdigest(),
    )


def assess_calibration_file(path: Path = RESULT_PATH) -> AssessedCalibration:
    if not isinstance(path, Path):
        raise TypeError("calibration result path must be a Path")
    return assess_calibration_bytes(path.read_bytes())


__all__ = [
    "AssessedCalibration",
    "CAMPAIGN_SHA256",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "DEPENDENCY_RELATIVE_PATHS",
    "IndependentFit",
    "PROTOCOL_SHA256",
    "RESULT_PATH",
    "RESULT_RELATIVE_PATH",
    "assess_calibration_bytes",
    "assess_calibration_file",
    "dependency_hashes",
    "independent_fit",
    "verify_independent_contract",
]
