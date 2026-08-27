"""Source-sealed compiled reduced-domain separation calibration (ADR-0457).

Importing this module is deliberately inert: it uses only the standard library,
does not read the prospective result, and cannot compile, import CuPy, query a
device, allocate device memory, or take a timing observation.  The separately
owned :func:`execute_calibration` path is the only scientific entry point.

The reduced fixtures are controls, not poker data.  In particular, none of the
synthetic base families defines the still-absent production ``b(S)`` producer.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
from itertools import product
import json
from math import comb, factorial
import os
from pathlib import Path
import re
import struct
import tempfile
from typing import Literal


ROOT = Path(__file__).parents[2]
CONFIG_RELATIVE_PATH = (
    "experiments/configs/"
    "legal-river-quotient-compiled-global-separation-calibration-v1.json"
)
CONFIG_SHA256 = "a9a0961656c66d70d145c9f5434460826f3c4972b7b1a18da74b0886a14e18bf"
PREREGISTRATION_COMMIT = "cb90e1d5581034f1988c0e2edfa8777972768a20"
RESULT_RELATIVE_PATH = (
    "artifacts/work_preflight/"
    "legal_river_quotient_compiled_global_separation_calibration_v1.jsonl"
)

SOURCE_WIDTH = 6
SUBSET_MAXIMUM = 4
FEATURE_WIDTH = 176
DOMAINS = (10, 12, 16, 20, 24)
TARGET_CARDS = 45
PRICE_COEFFICIENTS = (30, -120, 360, -720, 720)
H_SEED_WEIGHTS = (1, -24, 360, -2880, 8640)
H_OUTPUT_SCALE = 24
BASE_OUTPUT_SCALE = 720
BASE_RECONCILIATION_DIVISOR = 30

ARM_NAMES = (
    "contract_first_direct_57_scan",
    "rank_truncated_zeta",
    "adr0454_prefix_branch_and_bound",
    "frozen_prefix_then_zeta_hybrid",
)
RUNTIME_MODES = ("positive_witness", "prove_none")
BASE_MODES = (
    "exact_lattice_base",
    "opaque_per_source_base",
    "lattice_plus_exact_sparse_master_support_correction",
)
REFRESH_STATES = ("cold_base_refresh", "exact_provenance_hit")
ARITHMETIC_SCHEDULES = ("positional", "batched_five_then_four_RRNS")
WARMUP_PASS_INDICES = (0,)
MEASURED_PASS_INDICES = (1, 2, 3, 4, 5)
ALL_PASS_INDICES = WARMUP_PASS_INDICES + MEASURED_PASS_INDICES

PHASE_NAMES = (
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
PHASE_CALLBACK_NAMES = (
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
PHASE_COORDINATES = {
    "provenance_rebind": "typed_tokens_compared",
    "H_component_contraction": "signed_component_multiply_adds",
    "base_payload_transfer": "payload_bytes_transferred",
    "base_structural_cover": "base_cover_edge_additions",
    "base_sparse_patch": "patch_entries_applied",
    "arithmetic_encoding": "limb_words_or_residue_words_written",
    "prefix_base_bound_build": "descendant_base_values_read",
    "prefix_possible_term_bounds": "possible_or_guaranteed_terms_examined",
    "prefix_frontier_operations": "heap_pushes_plus_heap_pops_of_the_same_fixed_key_type",
    "exact_leaf_57_term_evaluation": "subset_terms_evaluated",
    "direct_global_57_term_scan": "subset_terms_evaluated",
    "zeta_seed_write": "seed_words_written",
    "zeta_cover_edges": "cover_edge_additions",
    "zeta_rank_six_stream": "source_prices_visited",
    "hybrid_switch": "switch_state_transitions",
    "RRNS_decision_key_reconstruction": "decision_keys_reconstructed",
    "terminal_sign_witness_or_closure_reduction": "exact_price_comparisons",
    "terminal_transfer": "terminal_bytes_transferred",
    "workspace_baseline_restore": "workspace_bytes_cleared_or_rebound",
}

PUBLIC_WALL_NS = 1_800_000_000_000
LABORATORY_WALL_NS = 1_500_000_000_000
OUTSIDE_LABORATORY_WALL_NS = 300_000_000_000
RESULT_BYTE_CEILING = 67_108_864
STDOUT_BYTE_CEILING = 4_096
STDERR_BYTE_CEILING = 4_096
DEVICE_TOTAL_BYTES = 17_094_475_776
DEVICE_RESERVE_BYTES = 2_000_000_000
NAMED_DEVICE_PEAK_CEILING_BYTES = 12_000_000_000
REJECTED_LIVENESS_EQUIVALENCE = (
    "any configuration whose liveness peak reproduces a rejected arm's peak "
    "is that rejected arm, regardless of variable names; rejections attach "
    "to physics, not identifiers"
)

# The exact ADR-0448 moduli.  The first four plus redundancy are resident in
# pass one; the remaining four are replayed in pass two.  Resident-nine is not
# an alias and is not represented anywhere in the public schedule type.
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
RRNS_FIRST_BATCH = (0, 1, 2, 3, 8)
RRNS_SECOND_BATCH = (4, 5, 6, 7)

KERNEL_NAMES = (
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

NVCC_PATH = Path(
    r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvcc.exe"
)
CUOBJDUMP_PATH = Path(
    r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\cuobjdump.exe"
)
NVDISASM_PATH = Path(
    r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvdisasm.exe"
)
NVCC_OPTIONS = (
    "--cubin",
    "--gpu-architecture=sm_120",
    "--std=c++17",
    "--ftz=false",
    "--prec-div=true",
    "--prec-sqrt=true",
    "--fmad=false",
    "--ptxas-options=-v",
)

PARENT_IDENTITIES = {
    "docs/decisions/ADR-0456-source-seal-the-base-aware-exact-global-separation-topologies.md": (
        "fe3d5c2ca2a762f19e2f2231b53770ebb5a692f25fa0ec53dab7da54f6dd7f29"
    ),
    "experiments/configs/legal-river-quotient-global-separation-topology-bakeoff-v1.json": (
        "3d023b59a5e28e20e1af16ff3c809e9ed8a2a1c23a5c56dcca81fd6181a64da7"
    ),
    "src/pontius/legal_river_quotient_base_provenance.py": (
        "1a048fbb5256526856e9f668d61f48a3fc77dc1601d8bd4c03cc645a316bd894"
    ),
    "src/pontius/legal_river_quotient_global_separation_topologies.py": (
        "11e6a6e24ac07c2db462c007433703deb4ccb56e4fb58caab02b01cdb209c55d"
    ),
    "tests/test_legal_river_quotient_global_separation_topologies.py": (
        "d4e268a35cc470d94782ab167b144c27db88cc32f05a0def4927cccb52d405ca"
    ),
    "docs/decisions/ADR-0448-retain-the-passing-split-runtime-fixed-width-device-preflight.md": (
        "030984cab34351593b3b9e3eb068bc42bacc61ae7b13bfe5d1d5a5f11e489d20"
    ),
    "artifacts/work_preflight/legal_river_quotient_fixed_width_device_preflight_v3.jsonl": (
        "6f0b53f95a5d538f7a3673fe411de4b40724fbf00cfc56c62360352cab3770bb"
    ),
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v1.json": (
        "84da7e82ef07620b0d7869a1e52da6a80f5f3815c0e4dc7007068ce6664ed6af"
    ),
    "experiments/configs/legal-river-quotient-fixed-width-device-preflight-v4-child-runtime-environment.json": (
        "492458e39020fc8d5178624e4a9b8b1c6c0fc4c004852d155618fc11c955547d"
    ),
    "artifacts/work_preflight/.gitattributes": (
        "e66225813ee8a9f06320b4e2f9e8ae4f9851352316b1dc5a3297f8e88c1b3ef1"
    ),
}

# Diagnostic mutation only.  Armed literal spelling: \r\n.  These four source bytes are not a newline and
# must never enter canonical-LF authority.  The real token-bearing parent set
# is frozen so a vacuous, unarmed mutation cannot pass the seal controls.
FORBIDDEN_LITERAL_ESCAPE_TOKEN = bytes((92, 114, 92, 110))
FORBIDDEN_LITERAL_ESCAPE_REPLACEMENT = bytes((92, 110))
PARENT_LITERAL_ESCAPE_OCCURRENCES = {
    "tests/test_legal_river_quotient_global_separation_topologies.py": 1,
}


RuntimeMode = Literal["positive_witness", "prove_none"]
BaseMode = Literal[
    "exact_lattice_base",
    "opaque_per_source_base",
    "lattice_plus_exact_sparse_master_support_correction",
]
RefreshState = Literal["cold_base_refresh", "exact_provenance_hit"]
ArithmeticSchedule = Literal["positional", "batched_five_then_four_RRNS"]


def _canonical_lf(raw: bytes) -> bytes:
    if type(raw) is not bytes:
        raise TypeError("canonical-LF input must be immutable bytes")
    output = bytearray()
    index = 0
    while index < len(raw):
        if raw[index : index + 2] == bytes((13, 10)):
            output.append(10)
            index += 2
        else:
            output.append(raw[index])
            index += 1
    return bytes(output)


def independent_canonical_lf(raw: bytes) -> bytes:
    """A deliberately separate CRLF byte loop for seal controls."""

    if type(raw) is not bytes:
        raise TypeError("independent canonical-LF input must be immutable bytes")
    result = bytearray()
    cursor = 0
    while cursor != len(raw):
        current = raw[cursor]
        if current == 13 and cursor + 1 != len(raw) and raw[cursor + 1] == 10:
            result += bytes((10,))
            cursor += 2
            continue
        result += bytes((current,))
        cursor += 1
    return bytes(result)


def forbidden_literal_escape_mutation(raw: bytes) -> tuple[bytes, int]:
    """Return the historical wrong rewrite and its armed occurrence count."""

    if type(raw) is not bytes:
        raise TypeError("literal-escape mutation input must be immutable bytes")
    count = raw.count(FORBIDDEN_LITERAL_ESCAPE_TOKEN)
    return (
        raw.replace(
            FORBIDDEN_LITERAL_ESCAPE_TOKEN,
            FORBIDDEN_LITERAL_ESCAPE_REPLACEMENT,
        ),
        count,
    )


def canonical_lf_sha256(path: Path) -> str:
    return sha256(_canonical_lf(path.read_bytes())).hexdigest()


def _unique_object(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"JSON object repeats key {key!r}")
        value[key] = item
    return value


def load_preregistered_config() -> dict[str, object]:
    path = ROOT / CONFIG_RELATIVE_PATH
    raw = path.read_bytes()
    if sha256(_canonical_lf(raw)).hexdigest() != CONFIG_SHA256:
        raise ValueError("ADR-0457 calibration config identity differs")
    value = json.loads(
        raw,
        object_pairs_hook=_unique_object,
        parse_float=lambda _: (_ for _ in ()).throw(ValueError("float in config")),
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("constant in config")),
    )
    if not isinstance(value, dict):
        raise TypeError("ADR-0457 calibration config is not an object")
    return value


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def verify_preregistered_contract(*, require_result_absent: bool = True) -> None:
    config = load_preregistered_config()
    if (
        config.get("schema_version")
        != "legal-river-quotient-compiled-global-separation-calibration-config-v1"
    ):
        raise ValueError("ADR-0457 schema differs")
    scope = _mapping(config.get("scope"), label="scope")
    if (
        tuple(scope.get("calibration_card_domains", ())) != DOMAINS
        or scope.get("cells_per_pass") != 480
        or scope.get("total_scientific_cell_invocations") != 2_880
    ):
        raise ValueError("ADR-0457 calibration axes differ")
    arms = tuple(row.get("arm") for row in config.get("topology_arms", ()))
    if arms != ARM_NAMES:
        raise ValueError("ADR-0457 arm order differs")
    schedules = _mapping(config.get("arithmetic_schedules"), label="schedules")
    if (
        tuple(schedules.get("eligible_only", ())) != ARITHMETIC_SCHEDULES
        or schedules.get("resident_nine_RRNS_remains_rejected") is not True
    ):
        raise ValueError("ADR-0457 arithmetic schedule differs")
    phases = _mapping(config.get("runtime_phase_partition"), label="phases")
    ledger = _mapping(config.get("work_ledger"), label="work ledger")
    if (
        tuple(phases.get("ordered_phases", ())) != PHASE_NAMES
        or ledger.get("projection_coordinates") != PHASE_COORDINATES
    ):
        raise ValueError("ADR-0457 phase contract differs")
    base = _mapping(config.get("production_base_boundary"), label="base boundary")
    claims = _mapping(config.get("claims"), label="claims")
    if (
        base.get("current_repository_state") != "producer_absent"
        or claims.get("production_base_classification") != "producer_absent"
        or any(
            claims.get(key) is not None
            for key in (
                "compiled_calibration_result",
                "material_zeta_speed_claim",
                "candidate_selected",
                "topology_selected",
                "arithmetic_schedule_selected",
                "literal_45_numerical_result",
                "resolver_iteration_result",
                "action_clock_result",
                "decision_quality_result",
                "blueprint_result",
                "poker_strength_result",
            )
        )
        or claims.get("truncation_authorized") is not False
    ):
        raise ValueError("ADR-0457 claims boundary differs")
    identity = _mapping(config.get("prospective_identity"), label="identity")
    expected_identity = {
        "launcher_relative_path": (
            "run_legal_river_quotient_compiled_global_separation_calibration.py"
        ),
        "runner_relative_path": (
            "src/pontius/"
            "legal_river_quotient_compiled_global_separation_calibration_runner.py"
        ),
        "scientific_source_relative_path": (
            "src/pontius/legal_river_quotient_compiled_global_separation_calibration.py"
        ),
        "result_reader_relative_path": (
            "src/pontius/"
            "legal_river_quotient_compiled_global_separation_calibration_result.py"
        ),
        "controls_relative_path": (
            "tests/test_legal_river_quotient_compiled_global_separation_calibration.py"
        ),
        "result_relative_path": RESULT_RELATIVE_PATH,
    }
    if any(identity.get(key) != value for key, value in expected_identity.items()):
        raise ValueError("ADR-0457 prospective identity differs")
    for relative, expected in PARENT_IDENTITIES.items():
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"ADR-0457 parent is absent: {relative}")
        raw = path.read_bytes()
        canonical = _canonical_lf(raw)
        if canonical != independent_canonical_lf(raw):
            raise ValueError(f"ADR-0457 canonical-LF implementations differ: {relative}")
        mutated, occurrences = forbidden_literal_escape_mutation(raw)
        expected_occurrences = PARENT_LITERAL_ESCAPE_OCCURRENCES.get(relative, 0)
        if occurrences != expected_occurrences or (mutated != raw) is not bool(occurrences):
            raise ValueError(f"ADR-0457 literal-escape mutation is unarmed: {relative}")
        digest = (
            sha256(raw).hexdigest()
            if relative.endswith(".jsonl")
            else sha256(canonical).hexdigest()
        )
        if digest != expected:
            raise ValueError(f"ADR-0457 parent identity differs: {relative}")
    attributes = (ROOT / "artifacts/work_preflight/.gitattributes").read_text(
        encoding="utf-8"
    )
    if "*.jsonl -text" not in attributes.splitlines():
        raise ValueError("ADR-0457 result path is not protected by -text")
    if require_result_absent and (ROOT / RESULT_RELATIVE_PATH).exists():
        raise FileExistsError("ADR-0457 calibration result is already consumed")


def _plain_int(value: object, *, label: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be a plain integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} is below its minimum")
    return value


def colex_rank(mask: int) -> int:
    value = _plain_int(mask, label="mask", minimum=0)
    rank = 0
    ordinal = 1
    card = 0
    while value:
        if value & 1:
            rank += comb(card, ordinal)
            ordinal += 1
        value >>= 1
        card += 1
    return rank


def colex_unrank(rank: int, cards: int, width: int) -> int:
    remaining = _plain_int(rank, label="colex rank", minimum=0)
    n = _plain_int(cards, label="cards", minimum=1)
    k = _plain_int(width, label="width", minimum=0)
    if k > n or remaining >= comb(n, k):
        raise ValueError("colex rank is outside the domain")
    mask = 0
    upper = n - 1
    for ordinal in range(k, 0, -1):
        card = upper
        while card >= ordinal - 1 and comb(card, ordinal) > remaining:
            card -= 1
        mask |= 1 << card
        remaining -= comb(card, ordinal)
        upper = card - 1
    if remaining:
        raise ArithmeticError("colex unranking left a remainder")
    return mask


@lru_cache(maxsize=None)
def complete_masks(cards: int, width: int) -> tuple[int, ...]:
    n = _plain_int(cards, label="cards", minimum=1)
    k = _plain_int(width, label="width", minimum=0)
    if k > n:
        raise ValueError("mask width exceeds card domain")
    rows = tuple(colex_unrank(rank, n, k) for rank in range(comb(n, k)))
    if tuple(map(colex_rank, rows)) != tuple(range(len(rows))):
        raise AssertionError("complete colex mask domain differs")
    return rows


def source_subsets(source_mask: int) -> tuple[int, ...]:
    if source_mask.bit_count() != SOURCE_WIDTH:
        raise ValueError("source mask must contain six cards")
    rows = []
    subset = source_mask
    while True:
        if subset.bit_count() <= SUBSET_MAXIMUM:
            rows.append(subset)
        if subset == 0:
            break
        subset = (subset - 1) & source_mask
    return tuple(sorted(rows, key=lambda mask: (mask.bit_count(), colex_rank(mask))))


def level_offset(cards: int, level: int) -> int:
    return sum(comb(cards, rank) for rank in range(level))


def flat_h_index(cards: int, mask: int) -> int:
    level = mask.bit_count()
    if level > SUBSET_MAXIMUM or mask >= 1 << cards:
        raise ValueError("H mask lies outside its flattened domain")
    return level_offset(cards, level) + colex_rank(mask)


def pricing_vector() -> tuple[int, ...]:
    return tuple((37 * index + 11) % 19 - 9 for index in range(175)) + (1,)


def desired_h(runtime_mode: RuntimeMode, mask: int) -> int:
    if runtime_mode == "positive_witness":
        return 0
    if runtime_mode == "prove_none":
        return -1 if mask.bit_count() == 1 else 0
    raise ValueError("runtime mode differs")


def raw_h_row(runtime_mode: RuntimeMode, cards: int, mask: int) -> tuple[int, ...]:
    if cards not in DOMAINS or mask >= 1 << cards or mask.bit_count() > SUBSET_MAXIMUM:
        raise ValueError("raw H row domain differs")
    prefix = []
    schema = "pontius-adr0457-compiled-separation-calibration-fixture-v1"
    for index in range(175):
        framing = (
            f"{schema}|{runtime_mode}|{cards}|H|{mask.bit_count()}|{mask}|{index}"
        ).encode("ascii")
        prefix.append(int.from_bytes(sha256(framing).digest()[:8], "big") % 17 - 8)
    q = pricing_vector()
    terminal = desired_h(runtime_mode, mask) - sum(
        value * coefficient for value, coefficient in zip(prefix, q[:175], strict=True)
    )
    return tuple(prefix) + (terminal,)


def contract_h(row: Sequence[int]) -> int:
    if len(row) != FEATURE_WIDTH or any(
        isinstance(item, bool) or not isinstance(item, int) for item in row
    ):
        raise ValueError("raw H row differs")
    return sum(
        item * coefficient
        for item, coefficient in zip(row, pricing_vector(), strict=True)
    )


def sparse_support_ranks(cards: int) -> tuple[int, ...]:
    count = comb(cards, SOURCE_WIDTH)
    return tuple(sorted({0, count - 1, *range(0, count, 257)}))


def base_value(
    runtime_mode: RuntimeMode, base_mode: BaseMode, source_rank: int, cards: int
) -> int:
    rank = _plain_int(source_rank, label="source rank", minimum=0)
    if rank >= comb(cards, SOURCE_WIDTH):
        raise ValueError("source rank lies outside its domain")
    if runtime_mode == "positive_witness":
        structural = 2 if base_mode.endswith("sparse_master_support_correction") else 1
    elif runtime_mode == "prove_none":
        structural = -721
    else:
        raise ValueError("runtime mode differs")
    if base_mode == "lattice_plus_exact_sparse_master_support_correction":
        return structural - int(rank in set(sparse_support_ranks(cards)))
    if base_mode in ("exact_lattice_base", "opaque_per_source_base"):
        return structural
    raise ValueError("synthetic base mode differs")


def exact_price(
    runtime_mode: RuntimeMode, base_mode: BaseMode, cards: int, source_rank: int
) -> int:
    mask = colex_unrank(source_rank, cards, SOURCE_WIDTH)
    total = base_value(runtime_mode, base_mode, source_rank, cards)
    for subset in source_subsets(mask):
        total += PRICE_COEFFICIENTS[subset.bit_count()] * desired_h(
            runtime_mode, subset
        )
    return total


@lru_cache(maxsize=None)
def exact_prices(
    runtime_mode: RuntimeMode, base_mode: BaseMode, cards: int
) -> tuple[int, ...]:
    """Return one immutable unbounded-integer authority row per source rank."""

    if cards not in DOMAINS or runtime_mode not in RUNTIME_MODES or base_mode not in BASE_MODES:
        raise ValueError("exact-price authority key differs")
    return tuple(
        exact_price(runtime_mode, base_mode, cards, rank)
        for rank in range(comb(cards, SOURCE_WIDTH))
    )


def _integer_stream_digest(values: Iterable[int]) -> str:
    digest = sha256()
    count = 0
    for value in values:
        item = _plain_int(value, label="digest integer")
        digest.update(struct.pack("<q", item))
        count += 1
    digest.update(struct.pack("<Q", count))
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class FixtureManifest:
    schema_version: str
    cards: int
    runtime_mode: str
    base_mode: str
    h_row_count: int
    source_count: int
    support_count: int
    pricing_sha256: str
    raw_h_sha256: str
    contracted_h_sha256: str
    base_sha256: str
    support_sha256: str
    expected_price_sha256: str
    raw_component_minimum: int
    raw_component_maximum: int
    expected_price_minimum: int
    expected_price_maximum: int
    authority_sha256: str


@lru_cache(maxsize=None)
def fixture_manifest(
    cards: int, runtime_mode: RuntimeMode, base_mode: BaseMode
) -> FixtureManifest:
    if cards not in DOMAINS or runtime_mode not in RUNTIME_MODES or base_mode not in BASE_MODES:
        raise ValueError("fixture manifest key differs")
    h_masks = tuple(
        mask
        for level in range(SUBSET_MAXIMUM + 1)
        for mask in complete_masks(cards, level)
    )
    raw_digest = sha256()
    contracted = []
    raw_minimum = 0
    raw_maximum = 0
    for mask in h_masks:
        row = raw_h_row(runtime_mode, cards, mask)
        for value in row:
            raw_digest.update(struct.pack("<q", value))
            raw_minimum = min(raw_minimum, value)
            raw_maximum = max(raw_maximum, value)
        contracted.append(contract_h(row))
    raw_digest.update(struct.pack("<Q", len(h_masks) * FEATURE_WIDTH))
    source_count = comb(cards, SOURCE_WIDTH)
    base_values = tuple(
        base_value(runtime_mode, base_mode, rank, cards)
        for rank in range(source_count)
    )
    prices = exact_prices(runtime_mode, base_mode, cards)
    support = sparse_support_ranks(cards) if base_mode == BASE_MODES[2] else ()
    fields = {
        "schema_version": "pontius-adr0457-fixture-manifest-v1",
        "cards": cards,
        "runtime_mode": runtime_mode,
        "base_mode": base_mode,
        "h_row_count": len(h_masks),
        "source_count": source_count,
        "support_count": len(support),
        "pricing_sha256": _integer_stream_digest(pricing_vector()),
        "raw_h_sha256": raw_digest.hexdigest(),
        "contracted_h_sha256": _integer_stream_digest(contracted),
        "base_sha256": _integer_stream_digest(base_values),
        "support_sha256": _integer_stream_digest(support),
        "expected_price_sha256": _integer_stream_digest(prices),
        "raw_component_minimum": raw_minimum,
        "raw_component_maximum": raw_maximum,
        "expected_price_minimum": min(prices),
        "expected_price_maximum": max(prices),
    }
    authority_sha256 = sha256(
        json.dumps(fields, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    return FixtureManifest(**fields | {"authority_sha256": authority_sha256})  # type: ignore[arg-type]


def fixture_manifests() -> tuple[FixtureManifest, ...]:
    return tuple(
        fixture_manifest(cards, mode, base_mode)  # type: ignore[arg-type]
        for cards, mode, base_mode in product(DOMAINS, RUNTIME_MODES, BASE_MODES)
    )


@dataclass(frozen=True, slots=True)
class WidthPlan:
    quantity: str
    signed_absolute_bound: int
    required_signed_bits: int
    mathematical_limbs: int
    guard_inclusive_limbs: int

    def admit(self, value: int) -> None:
        item = _plain_int(value, label=f"{self.quantity} value")
        if abs(item) > self.signed_absolute_bound:
            raise OverflowError(f"{self.quantity} exceeds its frozen semantic bound")


def width_plan(quantity: str, bound: int) -> WidthPlan:
    maximum = _plain_int(bound, label="signed bound", minimum=0)
    bits = 1 if maximum == 0 else maximum.bit_length() + 1
    limbs = (bits + 63) // 64
    return WidthPlan(quantity, maximum, bits, limbs, limbs + 1)


@dataclass(frozen=True, slots=True)
class ArithmeticAdmission:
    quantity_widths: tuple[WidthPlan, ...]
    zeta_rank_widths: tuple[WidthPlan, ...]
    working_product: int
    redundant_modulus: int
    table_range_sufficient: bool
    scalar_range_sufficient: bool
    bounded_single_modulus_decision_sufficient: bool
    sha256: str


def _zeta_h_bound(rank: int) -> int:
    return sum(
        comb(rank, level) * abs(H_SEED_WEIGHTS[level]) * factorial(rank - level)
        for level in range(min(rank, SUBSET_MAXIMUM) + 1)
    )


def derive_arithmetic_admission() -> ArithmeticAdmission:
    raw_terminal_bound = 175 * 8 * 9 + 1
    direct_h_bound = sum(
        comb(SOURCE_WIDTH, level) * abs(PRICE_COEFFICIENTS[level])
        for level in range(SUBSET_MAXIMUM + 1)
    )
    zeta_h = _zeta_h_bound(SOURCE_WIDTH)
    if zeta_h != H_OUTPUT_SCALE * direct_h_bound:
        raise ArithmeticError("H circuit bound identity differs")
    base_bound = 722
    base_scaled = H_OUTPUT_SCALE * base_bound
    patch_scaled = H_OUTPUT_SCALE
    output_scaled = zeta_h + base_scaled + patch_scaled
    rows = (
        width_plan("raw_H_component", raw_terminal_bound),
        width_plan("pricing_component", 9),
        width_plan("H_component_product", raw_terminal_bound * 9),
        width_plan("H_contraction_accumulator", 2 * 175 * 8 * 9 + 1),
        width_plan("contracted_h", 1),
        width_plan("base_value", base_bound),
        width_plan(
            "base_structural_level",
            factorial(SOURCE_WIDTH) * base_bound,
        ),
        width_plan("direct_price_accumulator", direct_h_bound + base_bound),
        width_plan("prefix_bound", direct_h_bound + base_bound),
        width_plan("zeta_output_scaled", output_scaled),
        width_plan("terminal_price", output_scaled // H_OUTPUT_SCALE),
        width_plan("RRNS_decision_key", output_scaled),
    )
    rank_rows = tuple(
        width_plan(
            f"zeta_rank_{rank}",
            _zeta_h_bound(rank) + factorial(rank) * base_bound,
        )
        for rank in range(SOURCE_WIDTH + 1)
    )
    working_product = 1
    for modulus in WORKING_MODULI:
        working_product *= modulus
    largest = max(row.signed_absolute_bound for row in rows + rank_rows)
    payload = {
        "quantity_widths": [asdict(row) for row in rows],
        "zeta_rank_widths": [asdict(row) for row in rank_rows],
        "working_product_decimal": str(working_product),
        "redundant_modulus": REDUNDANT_MODULUS,
        "table_range_sufficient": (
            _product(WORKING_MODULI[:4]) >= 2 * max(r.signed_absolute_bound for r in rank_rows) + 1
        ),
        "scalar_range_sufficient": working_product >= 2 * largest + 1,
        "bounded_single_modulus_decision_sufficient": (
            min(WORKING_MODULI) >= 2 * largest + 1
        ),
    }
    digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    return ArithmeticAdmission(
        rows,
        rank_rows,
        working_product,
        REDUNDANT_MODULUS,
        bool(payload["table_range_sufficient"]),
        bool(payload["scalar_range_sufficient"]),
        bool(payload["bounded_single_modulus_decision_sufficient"]),
        digest,
    )


def _product(values: Iterable[int]) -> int:
    result = 1
    for value in values:
        result *= value
    return result


def _is_prime_u64(value: int) -> bool:
    n = _plain_int(value, label="modulus", minimum=2)
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    if n in small:
        return True
    if any(n % prime == 0 for prime in small):
        return False
    exponent = n - 1
    shifts = 0
    while exponent & 1 == 0:
        exponent >>= 1
        shifts += 1
    for witness in (2, 325, 9375, 28178, 450775, 9_780_504, 1_795_265_022):
        base = witness % n
        if base == 0:
            continue
        x = pow(base, exponent, n)
        if x in (1, n - 1):
            continue
        for _ in range(shifts - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def validate_rrns_parameters() -> None:
    moduli = WORKING_MODULI + (REDUNDANT_MODULUS,)
    if len(set(moduli)) != 9 or not all(_is_prime_u64(value) for value in moduli):
        raise ValueError("RRNS moduli are not distinct primes")
    if REDUNDANT_MODULUS <= max(WORKING_MODULI):
        raise ValueError("RRNS redundant modulus is not the largest")
    admission = derive_arithmetic_admission()
    if not (
        admission.table_range_sufficient
        and admission.scalar_range_sufficient
        and admission.bounded_single_modulus_decision_sufficient
    ):
        raise OverflowError("RRNS range admission differs")


def encode_residues(value: int, *, include_redundant: bool = True) -> tuple[int, ...]:
    item = _plain_int(value, label="RRNS value")
    moduli = WORKING_MODULI + ((REDUNDANT_MODULUS,) if include_redundant else ())
    return tuple(item % modulus for modulus in moduli)


def signed_crt(residues: Sequence[int], moduli: Sequence[int]) -> int:
    if len(residues) != len(moduli) or not residues:
        raise ValueError("CRT codeword shape differs")
    modulus_product = _product(moduli)
    total = 0
    for residue, modulus in zip(residues, moduli, strict=True):
        if isinstance(residue, bool) or not isinstance(residue, int) or not 0 <= residue < modulus:
            raise ValueError("CRT residue is outside its channel")
        partial = modulus_product // modulus
        total = (total + residue * partial * pow(partial, -1, modulus)) % modulus_product
    return total - modulus_product if total > modulus_product // 2 else total


@dataclass(frozen=True, slots=True)
class DecisionKeyReceipt:
    value: int
    absolute_bound: int
    full_codeword_value: int
    base_extension_value: int
    redundant_checked: bool
    semantic_range_checked: bool


def reconstruct_decision_key(
    residues: Sequence[int], *, absolute_bound: int
) -> DecisionKeyReceipt:
    bound = _plain_int(absolute_bound, label="decision bound", minimum=0)
    if len(residues) != 9:
        raise ValueError("decision codeword must contain eight working plus redundancy")
    full = signed_crt(residues[:8], WORKING_MODULI)
    if abs(full) > bound:
        raise OverflowError("decision key is outside its semantic range")
    if residues[8] != full % REDUNDANT_MODULUS:
        raise RuntimeError("rrns_channel_fault_detected")
    first = residues[0]
    if first <= bound:
        extension = first
    elif WORKING_MODULI[0] - first <= bound:
        extension = first - WORKING_MODULI[0]
    else:
        raise OverflowError("bounded base-extension decision lies outside range")
    if any(
        extension % modulus != residue
        for residue, modulus in zip(residues[:8], WORKING_MODULI, strict=True)
    ):
        raise RuntimeError("rrns_channel_fault_detected")
    if extension % REDUNDANT_MODULUS != residues[8]:
        raise RuntimeError("rrns_channel_fault_detected")
    if extension != full:
        raise ArithmeticError("full-codeword and base-extension decisions disagree")
    return DecisionKeyReceipt(full, bound, full, extension, True, True)


@dataclass(frozen=True, slots=True)
class CellKey:
    cards: int
    arm: str
    runtime_mode: str
    base_mode: str
    refresh_state: str
    arithmetic_schedule: str

    @property
    def canonical(self) -> str:
        return "|".join(
            (
                str(self.cards),
                self.arm,
                self.runtime_mode,
                self.base_mode,
                self.refresh_state,
                self.arithmetic_schedule,
            )
        )


def execution_cells() -> tuple[CellKey, ...]:
    rows = tuple(
        CellKey(*values)
        for values in product(
            DOMAINS,
            ARM_NAMES,
            RUNTIME_MODES,
            BASE_MODES,
            REFRESH_STATES,
            ARITHMETIC_SCHEDULES,
        )
    )
    if len(rows) != 480 or len({row.canonical for row in rows}) != 480:
        raise AssertionError("ADR-0457 execution matrix differs")
    return rows


def pass_cells(pass_index: int) -> tuple[CellKey, ...]:
    index = _plain_int(pass_index, label="pass index", minimum=0)
    if index not in ALL_PASS_INDICES:
        raise ValueError("pass index differs")
    return tuple(
        sorted(
            execution_cells(),
            key=lambda row: (
                sha256(f"adr0457|{index}|{row.canonical}".encode("ascii")).digest(),
                row.canonical,
            ),
        )
    )


@dataclass(frozen=True, slots=True)
class PrefixGeometry:
    cards: int
    prefixes: tuple[tuple[int, ...], ...]
    prefix_masks: tuple[int, ...]
    depths: tuple[int, ...]
    parents: tuple[int, ...]
    child_offsets: tuple[int, ...]
    child_indices: tuple[int, ...]
    descendant_counts: tuple[int, ...]
    first_colex_ranks: tuple[int, ...]
    level_offsets: tuple[int, ...]
    sha256: str

    @property
    def node_count(self) -> int:
        return len(self.prefixes)


@lru_cache(maxsize=None)
def prefix_geometry(cards: int) -> PrefixGeometry:
    if cards not in DOMAINS and cards != TARGET_CARDS:
        raise ValueError("prefix geometry domain differs")
    prefixes: list[tuple[int, ...]] = [()]
    level_starts = [0]
    for depth in range(1, SOURCE_WIDTH + 1):
        level_starts.append(len(prefixes))
        maximum_exclusive = cards - SOURCE_WIDTH + depth
        # Generate combinations in lexicographic prefix order.  Node identity
        # is independent of colex source order; first_colex_rank is explicit.
        from itertools import combinations

        prefixes.extend(combinations(range(maximum_exclusive), depth))
    lookup = {prefix: index for index, prefix in enumerate(prefixes)}
    parents = [-1]
    child_rows: list[list[int]] = [[] for _ in prefixes]
    prefix_masks = []
    descendants = []
    first_ranks = []
    for index, prefix in enumerate(prefixes):
        mask = sum(1 << card for card in prefix)
        prefix_masks.append(mask)
        if prefix:
            parent = lookup[prefix[:-1]]
            parents.append(parent)
            child_rows[parent].append(index)
        remaining = SOURCE_WIDTH - len(prefix)
        start = prefix[-1] + 1 if prefix else 0
        descendants.append(comb(cards - start, remaining))
        completion = prefix + tuple(range(start, start + remaining))
        first_ranks.append(colex_rank(sum(1 << card for card in completion)))
    child_offsets = [0]
    child_indices = []
    for row in child_rows:
        child_indices.extend(row)
        child_offsets.append(len(child_indices))
    digest = sha256()
    for prefix, parent, descendant, first in zip(
        prefixes, parents, descendants, first_ranks, strict=True
    ):
        digest.update(struct.pack("<b", len(prefix)))
        digest.update(bytes(prefix))
        digest.update(struct.pack("<qQQ", parent, descendant, first))
    return PrefixGeometry(
        cards,
        tuple(prefixes),
        tuple(prefix_masks),
        tuple(map(len, prefixes)),
        tuple(parents),
        tuple(child_offsets),
        tuple(child_indices),
        tuple(descendants),
        tuple(first_ranks),
        tuple(level_starts + [len(prefixes)]),
        digest.hexdigest(),
    )


@dataclass(frozen=True, slots=True)
class HybridSwitchProof:
    cards: int
    base_mode: str
    sources: int
    early_checkpoint: int
    half_coverage: int
    hard_checkpoint: int
    internal_minimum_bound: int
    leaf_maximum_bound: int
    exact_leaves_at_switch: int
    pruned_sources_at_switch: int
    certified_coverage_at_switch: int
    switches_early: bool


def prove_early_hybrid_switch(cards: int, base_mode: BaseMode) -> HybridSwitchProof:
    if cards not in DOMAINS or base_mode not in BASE_MODES:
        raise ValueError("hybrid switch proof key differs")
    sources = comb(cards, SOURCE_WIDTH)
    early = (sources + 63) // 64
    half = (sources + 1) // 2
    hard = (sources + 7) // 8
    geometry = prefix_geometry(cards)
    base_bounds = [0] * geometry.node_count
    for node in range(geometry.node_count - 1, -1, -1):
        if geometry.depths[node] == SOURCE_WIDTH:
            base_bounds[node] = base_value(
                "prove_none", base_mode, geometry.first_colex_ranks[node], cards
            )
        else:
            children = geometry.child_indices[
                geometry.child_offsets[node] : geometry.child_offsets[node + 1]
            ]
            base_bounds[node] = max(base_bounds[child] for child in children)
    bounds = []
    for node, prefix in enumerate(geometry.prefixes):
        start = prefix[-1] + 1 if prefix else 0
        # This is the unchanged ADR-0454 possible-term formula specialized to
        # the fixture's only nonzero H terms: the selected singleton terms are
        # guaranteed and every singleton in the legal tail is possible.
        remaining = SOURCE_WIDTH - len(prefix)
        possible_singletons = len(prefix) + (cards - start if remaining else 0)
        bounds.append(base_bounds[node] + 120 * possible_singletons)
    internal = [
        bound
        for bound, depth in zip(bounds, geometry.depths, strict=True)
        if depth < SOURCE_WIDTH
    ]
    leaves = [
        bound
        for bound, depth in zip(bounds, geometry.depths, strict=True)
        if depth == SOURCE_WIDTH
    ]
    import heapq

    frontier: list[tuple[int, int, int]] = [
        (-bounds[0], geometry.first_colex_ranks[0], 0)
    ]
    exact_leaves = 0
    pruned = 0
    covered = 0
    switched = False
    while frontier:
        _, _, node = heapq.heappop(frontier)
        if geometry.depths[node] == SOURCE_WIDTH:
            exact_leaves += 1
            covered += 1
            if exact_leaves >= hard or (exact_leaves >= early and covered < half):
                switched = True
                break
            continue
        if bounds[node] <= 0:
            pruned += geometry.descendant_counts[node]
            covered += geometry.descendant_counts[node]
            if covered == sources:
                break
            continue
        for child in geometry.child_indices[
            geometry.child_offsets[node] : geometry.child_offsets[node + 1]
        ]:
            heapq.heappush(
                frontier,
                (-bounds[child], geometry.first_colex_ranks[child], child),
            )
    return HybridSwitchProof(
        cards,
        base_mode,
        sources,
        early,
        half,
        hard,
        min(internal),
        max(leaves),
        exact_leaves,
        pruned,
        covered,
        switched and exact_leaves == early and covered < half,
    )


@lru_cache(maxsize=None)
def expected_prefix_terminal(
    cards: int,
    runtime_mode: RuntimeMode,
    base_mode: BaseMode,
    hybrid: bool,
) -> dict[str, int]:
    """Independent CPU traversal authority for the frozen prefix fixtures."""

    if cards not in DOMAINS or runtime_mode not in RUNTIME_MODES or base_mode not in BASE_MODES:
        raise ValueError("prefix-terminal authority key differs")
    geometry = prefix_geometry(cards)
    sources = comb(cards, SOURCE_WIDTH)
    base_bounds = [0] * geometry.node_count
    for node in range(geometry.node_count - 1, -1, -1):
        if geometry.depths[node] == SOURCE_WIDTH:
            base_bounds[node] = base_value(
                runtime_mode, base_mode, geometry.first_colex_ranks[node], cards
            )
        else:
            children = geometry.child_indices[
                geometry.child_offsets[node] : geometry.child_offsets[node + 1]
            ]
            base_bounds[node] = max(base_bounds[child] for child in children)
    bounds = []
    for node, prefix in enumerate(geometry.prefixes):
        if runtime_mode == "positive_witness":
            bounds.append(base_bounds[node])
        else:
            start = prefix[-1] + 1 if prefix else 0
            remaining = SOURCE_WIDTH - len(prefix)
            possible = len(prefix) + (cards - start if remaining else 0)
            bounds.append(base_bounds[node] + 120 * possible)
    import heapq

    frontier = [(-bounds[0], geometry.first_colex_ranks[0], 0)]
    pushes = 1
    pops = 0
    leaves = 0
    pruned = 0
    covered = 0
    switched = 0
    witness_rank = 0
    witness_price = 0
    early = (sources + 63) // 64
    half = (sources + 1) // 2
    hard = (sources + 7) // 8
    while frontier:
        _, _, node = heapq.heappop(frontier)
        pops += 1
        bound = bounds[node]
        if not hybrid and runtime_mode == "prove_none" and bound <= 0:
            pruned += geometry.descendant_counts[node]
            covered += geometry.descendant_counts[node]
            continue
        if geometry.depths[node] == SOURCE_WIDTH:
            leaves += 1
            covered += 1
            if bound > 0:
                witness_rank = geometry.first_colex_ranks[node]
                witness_price = bound
                break
            if hybrid and runtime_mode == "prove_none" and (
                leaves >= hard or (leaves >= early and covered < half)
            ):
                switched = 1
                break
            continue
        if hybrid and runtime_mode == "prove_none" and bound <= 0:
            pruned += geometry.descendant_counts[node]
            covered += geometry.descendant_counts[node]
            continue
        for child in geometry.child_indices[
            geometry.child_offsets[node] : geometry.child_offsets[node + 1]
        ]:
            heapq.heappush(
                frontier,
                (-bounds[child], geometry.first_colex_ranks[child], child),
            )
            pushes += 1
    if hybrid and runtime_mode == "prove_none" and switched:
        covered = sources
    return {
        "found_positive": int(runtime_mode == "positive_witness"),
        "globally_closed": int(runtime_mode == "prove_none"),
        "switched": switched,
        "witness_rank": witness_rank,
        "witness_price": witness_price,
        "covered_sources": covered,
        "heap_pushes": pushes,
        "heap_pops": pops,
        "exact_leaves": leaves,
        "pruned_sources": pruned,
    }


@dataclass(frozen=True, slots=True)
class PhaseRow:
    name: str
    start_ns: int
    end_ns: int
    elapsed_ns: int
    device_elapsed_ns: int
    projection_coordinate: str
    projection_work: int
    logical_operations: int
    arithmetic_words: int
    transferred_bytes: int
    decision_keys_reconstructed: int


@dataclass(frozen=True, slots=True)
class PhasePartition:
    rows: tuple[PhaseRow, ...]
    primitive_total_ns: int


def phase_partition(
    stamps: Sequence[int],
    work_rows: Sequence[Mapping[str, int]],
    *,
    device_elapsed_ns: Sequence[int] | None = None,
) -> PhasePartition:
    if len(stamps) != len(PHASE_NAMES) + 1 or len(work_rows) != len(PHASE_NAMES):
        raise ValueError("nineteen-phase partition shape differs")
    times = tuple(_plain_int(item, label="phase stamp", minimum=0) for item in stamps)
    device_rows = (
        tuple(0 for _ in PHASE_NAMES)
        if device_elapsed_ns is None
        else tuple(
            _plain_int(value, label="device phase wall", minimum=0)
            for value in device_elapsed_ns
        )
    )
    if len(device_rows) != len(PHASE_NAMES):
        raise ValueError("device phase wall domain differs")
    if any(
        right < left for left, right in zip(times[:-1], times[1:], strict=True)
    ):
        raise ValueError("phase stamps are not monotonic")
    rows = []
    for index, name in enumerate(PHASE_NAMES):
        work = work_rows[index]
        expected = {
            "projection_work",
            "logical_operations",
            "arithmetic_words",
            "transferred_bytes",
            "decision_keys_reconstructed",
        }
        if set(work) != expected:
            raise ValueError("phase work receipt domain differs")
        values = {
            key: _plain_int(value, label=f"{name} {key}", minimum=0)
            for key, value in work.items()
        }
        rows.append(
            PhaseRow(
                name,
                times[index],
                times[index + 1],
                times[index + 1] - times[index],
                device_rows[index],
                PHASE_COORDINATES[name],
                values["projection_work"],
                values["logical_operations"],
                values["arithmetic_words"],
                values["transferred_bytes"],
                values["decision_keys_reconstructed"],
            )
        )
    total = times[-1] - times[0]
    if sum(row.elapsed_ns for row in rows) != total:
        raise ArithmeticError("phase walls do not partition the primitive")
    return PhasePartition(tuple(rows), total)


def wall_passes(elapsed_ns: int, ceiling_ns: int) -> bool:
    return _plain_int(elapsed_ns, label="elapsed wall", minimum=0) <= _plain_int(
        ceiling_ns, label="wall ceiling", minimum=0
    )


@dataclass(frozen=True, slots=True)
class AffineFit:
    intercept: Fraction
    slope: Fraction
    sse: Fraction
    positive_residual_guard: Fraction
    target_prediction: Fraction
    target_upper: Fraction
    target_upper_ceiling: int
    candidate: str


def _fraction_ceiling(value: Fraction) -> int:
    return -(-value.numerator // value.denominator)


def exact_nonnegative_affine_fit(
    work: Sequence[int], responses_ns: Sequence[int], target_work: int
) -> AffineFit:
    if len(work) != 5 or len(responses_ns) != 5:
        raise ValueError("affine fit requires all five domains")
    xs = tuple(Fraction(_plain_int(x, label="fit work", minimum=0)) for x in work)
    ys = tuple(
        Fraction(_plain_int(y, label="fit response", minimum=0))
        for y in responses_ns
    )
    target = Fraction(_plain_int(target_work, label="target work", minimum=0))
    if len(set(xs)) == 1:
        intercept = max(ys)
        slope = Fraction(0)
        candidates = (("constant_coordinate", intercept, slope),)
    else:
        count = Fraction(len(xs))
        sum_x = sum(xs, Fraction())
        sum_y = sum(ys, Fraction())
        sum_xx = sum((x * x for x in xs), Fraction())
        sum_xy = sum((x * y for x, y in zip(xs, ys, strict=True)), Fraction())
        denominator = count * sum_xx - sum_x * sum_x
        unconstrained_slope = (count * sum_xy - sum_x * sum_y) / denominator
        unconstrained_intercept = (sum_y - unconstrained_slope * sum_x) / count
        raw: list[tuple[str, Fraction, Fraction]] = []
        if unconstrained_intercept >= 0 and unconstrained_slope >= 0:
            raw.append(
                (
                    "feasible_unconstrained_ordinary_least_squares",
                    unconstrained_intercept,
                    unconstrained_slope,
                )
            )
        raw.extend(
            (
                ("slope_zero", sum_y / count, Fraction(0)),
                (
                    "intercept_zero",
                    Fraction(0),
                    max(Fraction(0), sum_xy / sum_xx) if sum_xx else Fraction(0),
                ),
                ("zero", Fraction(0), Fraction(0)),
            )
        )
        candidates = tuple(raw)

    def score(row: tuple[str, Fraction, Fraction]) -> tuple[Fraction, Fraction, Fraction, Fraction]:
        _, intercept, slope = row
        sse = sum(
            ((y - intercept - slope * x) ** 2 for x, y in zip(xs, ys, strict=True)),
            Fraction(),
        )
        projection = intercept + slope * target
        return (sse, -projection, -intercept, -slope)

    name, intercept, slope = min(candidates, key=score)
    sse = score((name, intercept, slope))[0]
    guard = max(
        (Fraction(0), *(y - intercept - slope * x for x, y in zip(xs, ys, strict=True)))
    )
    prediction = intercept + slope * target
    upper = Fraction(5, 4) * (prediction + guard)
    return AffineFit(
        intercept,
        slope,
        sse,
        guard,
        prediction,
        upper,
        _fraction_ceiling(upper),
        name,
    )


def fraction_pair(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def parse_fraction_pair(value: object) -> Fraction:
    row = _mapping(value, label="fraction pair")
    if set(row) != {"numerator", "denominator"}:
        raise ValueError("fraction-pair domain differs")
    numerator = _plain_int(row["numerator"], label="fraction numerator")
    denominator = _plain_int(row["denominator"], label="fraction denominator", minimum=1)
    if Fraction(numerator, denominator).denominator != denominator:
        raise ValueError("fraction pair is not canonical")
    return Fraction(numerator, denominator)


@dataclass(frozen=True, slots=True)
class BufferLifetime:
    name: str
    storage_identity: str
    byte_count: int
    birth_boundary: int
    death_boundary: int


@dataclass(frozen=True, slots=True)
class MemoryLiveness:
    peak_bytes: int
    peak_boundaries: tuple[int, ...]
    boundary_live_bytes: tuple[int, ...]
    alias_checked: bool
    ceiling_passed: bool
    reserve_passed: bool


def memory_liveness(
    rows: Sequence[BufferLifetime], *, boundary_count: int
) -> MemoryLiveness:
    count = _plain_int(boundary_count, label="boundary count", minimum=2)
    identities: dict[str, list[BufferLifetime]] = {}
    for row in rows:
        if (
            not row.name
            or not row.storage_identity
            or row.byte_count < 0
            or row.birth_boundary < 0
            or row.death_boundary <= row.birth_boundary
            or row.death_boundary >= count
        ):
            raise ValueError("buffer lifetime differs")
        identities.setdefault(row.storage_identity, []).append(row)
    for group in identities.values():
        for left_index, left in enumerate(group):
            for right in group[left_index + 1 :]:
                if max(left.birth_boundary, right.birth_boundary) < min(
                    left.death_boundary, right.death_boundary
                ):
                    raise ValueError("aliased buffer lifetimes overlap")
    totals = []
    for boundary in range(count):
        live_by_identity: dict[str, int] = {}
        for row in rows:
            if row.birth_boundary <= boundary < row.death_boundary:
                live_by_identity[row.storage_identity] = max(
                    live_by_identity.get(row.storage_identity, 0), row.byte_count
                )
        totals.append(sum(live_by_identity.values()))
    peak = max(totals)
    peaks = tuple(index for index, value in enumerate(totals) if value == peak)
    return MemoryLiveness(
        peak,
        peaks,
        tuple(totals),
        True,
        peak <= NAMED_DEVICE_PEAK_CEILING_BYTES,
        peak + DEVICE_RESERVE_BYTES <= DEVICE_TOTAL_BYTES,
    )


def rrns_batch_arena_rows(cards: int) -> int:
    """Rows in the sole physical five-channel RRNS replay arena."""

    if cards not in DOMAINS and cards != TARGET_CARDS:
        raise ValueError("RRNS arena domain differs")
    geometry = symbolic_geometry(cards)
    support = len(sparse_support_ranks(cards))
    return max(
        geometry["h_rows"],
        geometry["sources"],
        geometry["zeta_nodes"],
        support,
    )


def rrns_batch_arena_bytes(cards: int) -> int:
    return 5 * 8 * rrns_batch_arena_rows(cards)


def reduced_memory_plan(cards: int, schedule: ArithmeticSchedule) -> tuple[BufferLifetime, ...]:
    if cards not in DOMAINS or schedule not in ARITHMETIC_SCHEDULES:
        raise ValueError("reduced memory-plan key differs")
    h_rows = sum(comb(cards, rank) for rank in range(SUBSET_MAXIMUM + 1))
    source_rows = comb(cards, SOURCE_WIDTH)
    nodes = prefix_geometry(cards).node_count
    levels = sum(comb(cards, rank) for rank in range(SOURCE_WIDTH + 1))
    support = len(sparse_support_ranks(cards))
    prefix = f"domain_{cards}"
    return (
        BufferLifetime("raw_H_both_modes", f"{prefix}_raw_H", 2 * h_rows * FEATURE_WIDTH * 8, 0, 20),
        BufferLifetime("pricing", f"{prefix}_pricing", FEATURE_WIDTH * 8, 0, 20),
        BufferLifetime("prefix_geometry", f"{prefix}_geometry", 37 * nodes + 4, 0, 20),
        BufferLifetime("moduli_channels_and_tokens", f"{prefix}_identity", 72 + 20 + 16 + 96, 0, 20),
        BufferLifetime("all_typed_base_payloads", f"{prefix}_payloads", 32 * source_rows + 64 * support + 64, 0, 20),
        BufferLifetime("all_twelve_base_artifacts", f"{prefix}_artifacts", 1_152 + 192 * source_rows + 192 * levels, 0, 20),
        BufferLifetime("shared_status", f"{prefix}_status", 4, 0, 20),
        BufferLifetime(
            "shared_exact_scratch_without_RRNS_arena",
            f"{prefix}_scratch",
            scratch_restore_bytes(cards, schedule)
            - 4
            - rrns_batch_arena_bytes(cards)
            + 40 * source_rows,
            0,
            20,
        ),
        BufferLifetime(
            "sole_five_channel_RRNS_table_arena",
            "global_rrns_batch_arena",
            rrns_batch_arena_bytes(cards),
            0,
            20,
        ),
    )


def campaign_memory_plan() -> tuple[BufferLifetime, ...]:
    domain_rows = tuple(
        row
        for cards in DOMAINS
        for row in reduced_memory_plan(cards, ARITHMETIC_SCHEDULES[0])
        if row.name != "sole_five_channel_RRNS_table_arena"
    )
    shared_arena = BufferLifetime(
        "sole_five_channel_RRNS_table_arena",
        "global_rrns_batch_arena",
        max(rrns_batch_arena_bytes(cards) for cards in DOMAINS),
        0,
        20,
    )
    return domain_rows + (shared_arena,)


def symbolic_geometry(cards: int) -> dict[str, int]:
    n = _plain_int(cards, label="symbolic cards", minimum=SOURCE_WIDTH)
    sources = comb(n, SOURCE_WIDTH)
    h_rows = sum(comb(n, rank) for rank in range(SUBSET_MAXIMUM + 1))
    levels = sum(comb(n, rank) for rank in range(SOURCE_WIDTH + 1))
    cover_edges = sum(rank * comb(n, rank) for rank in range(1, SOURCE_WIDTH + 1))
    prefix_nodes = comb(n + 1, SOURCE_WIDTH)
    return {
        "cards": n,
        "sources": sources,
        "h_rows": h_rows,
        "zeta_nodes": levels,
        "zeta_cover_edges": cover_edges,
        "prefix_nodes": prefix_nodes,
        "prefix_edges": prefix_nodes - 1,
        "direct_subset_terms": 57 * sources,
    }


def scratch_restore_bytes(cards: int, schedule: ArithmeticSchedule) -> int:
    """Exact live scratch bytes restored after one call of ``schedule``."""

    if cards not in DOMAINS and cards != TARGET_CARDS:
        raise ValueError("scratch restore domain differs")
    if schedule not in ARITHMETIC_SCHEDULES:
        raise ValueError("scratch restore schedule differs")
    geometry = symbolic_geometry(cards)
    h_rows = geometry["h_rows"]
    sources = geometry["sources"]
    levels = geometry["zeta_nodes"]
    nodes = geometry["prefix_nodes"]
    support = (sources + 256) // 257 + (0 if (sources - 1) % 257 == 0 else 1)
    return (
        4
        + 8
        + 80
        + 16 * h_rows
        + 16 * levels
        + 36 * nodes
        + 16 * support
        + rrns_batch_arena_bytes(cards)
    )


def _base_payload_bytes(cards: int, base_mode: str, refresh_state: str) -> int:
    if refresh_state == "exact_provenance_hit":
        return 0
    sources = comb(cards, SOURCE_WIDTH)
    if base_mode == "opaque_per_source_base":
        return sources * 8
    if base_mode == BASE_MODES[2]:
        return 8 + len(sparse_support_ranks(cards)) * 16
    return 8


def phase_work_coordinates(cell: CellKey, *, target: bool = False) -> dict[str, int]:
    cards = TARGET_CARDS if target else cell.cards
    geometry = symbolic_geometry(cards)
    sources = geometry["sources"]
    h_rows = geometry["h_rows"]
    prefix_nodes = geometry["prefix_nodes"]
    prefix_arm = cell.arm in ARM_NAMES[2:]
    zeta_arm = cell.arm in (ARM_NAMES[1], ARM_NAMES[3])
    direct_arm = cell.arm == ARM_NAMES[0]
    hybrid = cell.arm == ARM_NAMES[3]
    rrns = cell.arithmetic_schedule == ARITHMETIC_SCHEDULES[1]
    positive = cell.runtime_mode == RUNTIME_MODES[0]
    cold = cell.refresh_state == REFRESH_STATES[0]
    mixed = cell.base_mode == BASE_MODES[2]
    structural = cell.base_mode != BASE_MODES[1]
    support_count = (
        len(sparse_support_ranks(cell.cards))
        if not target
        else (sources + 256) // 257
        + (0 if (sources - 1) % 257 == 0 else 1)
    )
    early = (sources + 63) // 64
    hard = (sources + 7) // 8
    # Target prefix and hybrid work is intentionally the registered complete
    # worst case.  No target value is generated to learn a pruning fraction.
    prefix_frontier = 2 * prefix_nodes if prefix_arm else 0
    prefix_leaves = 0
    if prefix_arm and positive:
        prefix_leaves = 1
    elif hybrid and not positive:
        prefix_leaves = hard if target else early
    direct_sources = (1 if positive else sources) if direct_arm else 0
    zeta_stream = (1 if positive else sources) if zeta_arm else 0
    zeta_runs = zeta_arm and (not hybrid or not positive)
    coordinates = {
        "provenance_rebind": 12,
        "H_component_contraction": h_rows * FEATURE_WIDTH,
        "base_payload_transfer": _base_payload_bytes(
            cell.cards if not target else TARGET_CARDS,
            cell.base_mode,
            cell.refresh_state,
        ),
        "base_structural_cover": (
            geometry["zeta_cover_edges"] if cold and structural else 0
        ),
        "base_sparse_patch": (
            support_count
            if cold and mixed
            else 0
        ),
        "arithmetic_encoding": (
            11 * sources if rrns else 0
        ),
        "prefix_base_bound_build": (sources + geometry["prefix_edges"]) if prefix_arm else 0,
        "prefix_possible_term_bounds": (
            prefix_nodes * (1 if positive else cards) if prefix_arm else 0
        ),
        "prefix_frontier_operations": (
            (6 * cards - 22) if prefix_arm and positive and target else prefix_frontier
        ),
        "exact_leaf_57_term_evaluation": prefix_leaves * 57,
        "direct_global_57_term_scan": direct_sources * 57,
        "zeta_seed_write": h_rows * (11 if rrns else 2) if zeta_runs else 0,
        "zeta_cover_edges": geometry["zeta_cover_edges"] if zeta_runs else 0,
        "zeta_rank_six_stream": zeta_stream if zeta_runs else 0,
        "hybrid_switch": 1 if hybrid and not positive else 0,
        "RRNS_decision_key_reconstruction": (
            (direct_sources if direct_arm else zeta_stream if zeta_runs else 0)
            if rrns
            else 0
        ),
        "terminal_sign_witness_or_closure_reduction": (
            direct_sources if direct_arm else zeta_stream if zeta_runs else 0
        ),
        "terminal_transfer": 92,
        "workspace_baseline_restore": scratch_restore_bytes(cards, cell.arithmetic_schedule),
    }
    if set(coordinates) != set(PHASE_NAMES):
        raise AssertionError("phase-work coordinate domain differs")
    return coordinates


def source_boundary_claims() -> dict[str, object]:
    return {
        "source_seal": True,
        "compiled_calibration_result": None,
        "production_base_classification": "producer_absent",
        "production_base_numerical_admission": None,
        "material_zeta_speed_claim": None,
        "symbolic_45_primitive_projection": None,
        "candidate_selected": None,
        "topology_selected": None,
        "arithmetic_schedule_selected": None,
        "literal_45_numerical_result": None,
        "resolver_iteration_result": None,
        "action_clock_result": None,
        "decision_quality_result": None,
        "truncation_authorized": False,
        "blueprint_result": None,
        "poker_strength_result": None,
    }


# One literal translation unit contains every arm and both eligible arithmetic
# schedules.  Reduced-domain bounds prove one mathematical 64-bit limb for all
# runtime quantities; every positional table nevertheless carries the required
# sign-extension guard limb.  RRNS decision reconstruction is a bounded CRT
# specialization: the first working residue uniquely identifies the symmetric
# integer because 2B+1 < m0, after which all remaining working residues and the
# redundant residue are checked before the positional key can be used.
CUDA_SOURCE = r'''// Pontius ADR-0457 compiled reduced separation calibration
#include <stdint.h>
#include <limits.h>

struct TerminalReceipt {
    int status;
    int found_positive;
    int globally_closed;
    int switched;
    unsigned long long witness_rank;
    long long witness_price;
    unsigned long long covered_sources;
    unsigned long long heap_pushes;
    unsigned long long heap_pops;
    unsigned long long exact_leaves;
    unsigned long long pruned_sources;
    unsigned long long decision_keys;
};

__device__ __forceinline__ unsigned long long choose_small(int n, int k) {
    if (k < 0 || k > n) return 0ULL;
    if (k > n - k) k = n - k;
    unsigned long long value = 1ULL;
    for (int i = 1; i <= k; ++i) {
        value = value * (unsigned long long)(n - k + i) / (unsigned long long)i;
    }
    return value;
}

__device__ __forceinline__ unsigned long long level_offset(int n, int level) {
    unsigned long long value = 0ULL;
    for (int rank = 0; rank < level; ++rank) value += choose_small(n, rank);
    return value;
}

__device__ __forceinline__ unsigned long long colex_rank_mask(unsigned long long mask) {
    unsigned long long rank = 0ULL;
    int ordinal = 1;
    for (int card = 0; card < 63; ++card) {
        if (mask & (1ULL << card)) {
            rank += choose_small(card, ordinal);
            ++ordinal;
        }
    }
    return rank;
}

__device__ __forceinline__ unsigned long long colex_unrank_mask(
    unsigned long long rank, int n, int k) {
    unsigned long long mask = 0ULL;
    int upper = n - 1;
    for (int ordinal = k; ordinal >= 1; --ordinal) {
        int card = upper;
        while (card >= ordinal - 1 && choose_small(card, ordinal) > rank) --card;
        mask |= 1ULL << card;
        rank -= choose_small(card, ordinal);
        upper = card - 1;
    }
    return mask;
}

__device__ __forceinline__ void fail(int *status, int code) {
    atomicCAS(status, 0, code);
}

__device__ __forceinline__ void store_positional(
    unsigned long long *target, unsigned long long index, long long value) {
    target[index * 2ULL] = (unsigned long long)value;
    target[index * 2ULL + 1ULL] = value < 0 ? ~0ULL : 0ULL;
}

__device__ __forceinline__ long long load_positional(
    const unsigned long long *source, unsigned long long index, int *status) {
    unsigned long long low = source[index * 2ULL];
    unsigned long long guard = source[index * 2ULL + 1ULL];
    unsigned long long expected = ((long long)low) < 0 ? ~0ULL : 0ULL;
    if (guard != expected) fail(status, 11);
    return (long long)low;
}

__device__ __forceinline__ unsigned long long residue_add(
    unsigned long long left, unsigned long long right,
    unsigned long long modulus) {
    // Frozen moduli are below 2^62, hence left+right cannot overflow uint64.
    unsigned long long value = left + right;
    return value >= modulus ? value - modulus : value;
}

__device__ __forceinline__ unsigned long long residue_negate(
    unsigned long long value, unsigned long long modulus) {
    return value == 0ULL ? 0ULL : modulus - value;
}

__device__ __forceinline__ unsigned long long residue_from_signed(
    long long value, unsigned long long modulus) {
    if (value >= 0) return (unsigned long long)value % modulus;
    unsigned long long magnitude = (unsigned long long)(-(value + 1LL)) + 1ULL;
    unsigned long long residue = magnitude % modulus;
    return residue == 0ULL ? 0ULL : modulus - residue;
}

__device__ __forceinline__ unsigned long long residue_multiply_small(
    unsigned long long value, long long coefficient,
    unsigned long long modulus) {
    bool negative = coefficient < 0;
    unsigned long long multiplier = negative
        ? (unsigned long long)(-(coefficient + 1LL)) + 1ULL
        : (unsigned long long)coefficient;
    unsigned long long total = 0ULL;
    unsigned long long addend = value;
    while (multiplier) {
        if (multiplier & 1ULL) total = residue_add(total, addend, modulus);
        multiplier >>= 1;
        if (multiplier) addend = residue_add(addend, addend, modulus);
    }
    return negative ? residue_negate(total, modulus) : total;
}

__device__ __forceinline__ long long bounded_symmetric_decode(
    unsigned long long residue, unsigned long long modulus,
    unsigned long long bound, int *status) {
    if (residue <= bound) return (long long)residue;
    if (modulus - residue <= bound) return -(long long)(modulus - residue);
    fail(status, 21);
    return 0LL;
}

__device__ __forceinline__ long long reconstruct_decision_key(
    const unsigned long long (&residues)[9],
    const unsigned long long *moduli, unsigned long long bound,
    int *status) {
    if (bound > (moduli[0] - 1ULL) / 2ULL) {
        fail(status, 22);
        return 0LL;
    }
    long long value = bounded_symmetric_decode(residues[0], moduli[0], bound, status);
    // RRNS decision reconstruction: this loop is both the full working-codeword
    // consistency check and base
    // extension into the redundant channel.  No residue is ordered directly.
    #pragma unroll
    for (int channel = 0; channel < 9; ++channel) {
        unsigned long long expected = residue_from_signed(value, moduli[channel]);
        if (residues[channel] != expected) fail(status, 23);
    }
    if ((unsigned long long)(value < 0 ? -(value + 1LL) + 1ULL : value) > bound) {
        fail(status, 24);
    }
    return value;
}

extern "C" __global__ void bind_provenance(
    const unsigned long long *expected, const unsigned long long *observed,
    int token_count, int *status) {
    int item = blockDim.x * blockIdx.x + threadIdx.x;
    if (item < token_count && expected[item] != observed[item]) fail(status, 31);
}

extern "C" __global__ void contract_h_positional(
    const long long *raw_h, const long long *pricing,
    unsigned long long *contracted, unsigned long long rows, int *status) {
    unsigned long long row = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (row >= rows) return;
    long long total = 0LL;
    for (int feature = 0; feature < 176; ++feature) {
        long long left = raw_h[row * 176ULL + (unsigned long long)feature];
        long long right = pricing[feature];
        // ADR-0457 admits both operands and the accumulator against their
        // independently derived one-limb bounds before this kernel launches.
        long long term = left * right;
        total += term;
    }
    store_positional(contracted, row, total);
}

extern "C" __global__ void contract_h_rrns_batch(
    const long long *raw_h, const long long *pricing,
    unsigned long long *output, unsigned long long rows,
    const unsigned long long *moduli, const int *channels,
    int channel_count, int *status) {
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    unsigned long long count = rows * (unsigned long long)channel_count;
    if (item >= count) return;
    int local = (int)(item % (unsigned long long)channel_count);
    unsigned long long row = item / (unsigned long long)channel_count;
    int channel = channels[local];
    unsigned long long modulus = moduli[channel];
    unsigned long long total = 0ULL;
    for (int feature = 0; feature < 176; ++feature) {
        unsigned long long value = residue_from_signed(
            raw_h[row * 176ULL + (unsigned long long)feature], modulus);
        unsigned long long term = residue_multiply_small(value, pricing[feature], modulus);
        total = residue_add(total, term, modulus);
    }
    output[item] = total;
}

__device__ __forceinline__ bool sparse_support(unsigned long long rank,
    unsigned long long source_count) {
    return rank == 0ULL || rank + 1ULL == source_count || rank % 257ULL == 0ULL;
}

extern "C" __global__ void build_base_positional(
    const long long *payload, unsigned long long payload_count,
    unsigned long long *base, unsigned long long *structural_levels,
    int cards, int runtime_mode, int base_mode, int *status) {
    if (blockIdx.x || threadIdx.x) return;
    unsigned long long sources = choose_small(cards, 6);
    if ((base_mode == 1 && payload_count != sources)
            || (base_mode != 1 && payload_count < 1ULL)) {
        fail(status, 32);
        return;
    }
    for (unsigned long long rank = 0; rank < sources; ++rank) {
        store_positional(base, rank, base_mode == 1 ? payload[rank] : payload[0]);
    }
    if (base_mode != 1) {
        long long structural = payload[0];
        unsigned long long nodes = level_offset(cards, 7);
        for (unsigned long long item = 0; item < nodes; ++item) {
            store_positional(structural_levels, item, 0LL);
        }
        store_positional(structural_levels, 0ULL, structural);
        for (int level = 1; level <= 6; ++level) {
            unsigned long long rows = choose_small(cards, level);
            for (unsigned long long rank = 0; rank < rows; ++rank) {
                unsigned long long mask = colex_unrank_mask(rank, cards, level);
                long long total = 0LL;
                unsigned long long cursor = mask;
                while (cursor) {
                    int card = __ffsll((long long)cursor) - 1;
                    unsigned long long parent = mask & ~(1ULL << card);
                    total += load_positional(
                        structural_levels,
                        level_offset(cards, level - 1) + colex_rank_mask(parent), status);
                    cursor &= cursor - 1ULL;
                }
                store_positional(structural_levels,
                    level_offset(cards, level) + rank, total);
            }
        }
    }
}

extern "C" __global__ void build_base_rrns_batch(
    const long long *payload, unsigned long long payload_count,
    unsigned long long *output, int output_kind,
    int cards, int runtime_mode, int base_mode,
    const unsigned long long *moduli, const int *channels,
    int channel_count, int *status) {
    if (blockIdx.x || threadIdx.x) return;
    unsigned long long sources = choose_small(cards, 6);
    if ((base_mode == 1 && payload_count != sources)
            || (base_mode != 1 && payload_count < 1ULL)) {
        fail(status, 32);
        return;
    }
    if (output_kind == 0) {
        for (unsigned long long rank = 0; rank < sources; ++rank) {
            long long value = base_mode == 1 ? payload[rank] : payload[0];
            for (int local = 0; local < channel_count; ++local) {
                int channel = channels[local];
                output[rank * (unsigned long long)channel_count + local] =
                    residue_from_signed(value, moduli[channel]);
            }
        }
        return;
    }
    if (output_kind == 1 && base_mode != 1) {
        long long seed = payload[0];
        unsigned long long nodes = level_offset(cards, 7);
        for (unsigned long long item = 0; item < nodes * (unsigned long long)channel_count; ++item) {
            output[item] = 0ULL;
        }
        for (int local = 0; local < channel_count; ++local) {
            int channel = channels[local];
            output[local] = residue_from_signed(seed, moduli[channel]);
        }
        for (int level = 1; level <= 6; ++level) {
            unsigned long long rows = choose_small(cards, level);
            for (unsigned long long rank = 0; rank < rows; ++rank) {
                unsigned long long mask = colex_unrank_mask(rank, cards, level);
                for (int local = 0; local < channel_count; ++local) {
                    int channel = channels[local];
                    unsigned long long total = 0ULL;
                    unsigned long long cursor = mask;
                    while (cursor) {
                        int card = __ffsll((long long)cursor) - 1;
                        unsigned long long parent = mask & ~(1ULL << card);
                        unsigned long long index =
                            (level_offset(cards, level - 1) + colex_rank_mask(parent))
                            * (unsigned long long)channel_count + local;
                        total = residue_add(total, output[index], moduli[channel]);
                        cursor &= cursor - 1ULL;
                    }
                    unsigned long long target =
                        (level_offset(cards, level) + rank)
                        * (unsigned long long)channel_count + local;
                    output[target] = total;
                }
            }
        }
        return;
    }
    fail(status, 35);
}

extern "C" __global__ void apply_sparse_patch_positional(
    const long long *payload, unsigned long long payload_count,
    unsigned long long *base, int cards, int base_mode, int *status) {
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    unsigned long long sources = choose_small(cards, 6);
    if (base_mode != 2 || payload_count < 3ULL || !(payload_count & 1ULL)) {
        if (item == 0ULL) fail(status, 33);
        return;
    }
    unsigned long long support_count = (payload_count - 1ULL) / 2ULL;
    if (item >= support_count) return;
    unsigned long long rank = (unsigned long long)payload[1ULL + 2ULL * item];
    long long correction = payload[2ULL + 2ULL * item];
    if (rank >= sources || correction != -1LL || !sparse_support(rank, sources)) {
        fail(status, 34);
        return;
    }
    long long value = load_positional(base, rank, status);
    store_positional(base, rank, value + correction);
}

extern "C" __global__ void apply_sparse_patch_rrns_batch(
    const long long *payload, unsigned long long payload_count,
    unsigned long long *base, int cards, int base_mode,
    const unsigned long long *moduli, const int *channels,
    int channel_count, int *status) {
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    unsigned long long sources = choose_small(cards, 6);
    if (base_mode != 2 || payload_count < 3ULL || !(payload_count & 1ULL)) {
        if (item == 0ULL) fail(status, 33);
        return;
    }
    unsigned long long support_count = (payload_count - 1ULL) / 2ULL;
    if (item >= support_count) return;
    unsigned long long rank = (unsigned long long)payload[1ULL + 2ULL * item];
    long long correction = payload[2ULL + 2ULL * item];
    if (rank >= sources || correction != -1LL || !sparse_support(rank, sources)) {
        fail(status, 34);
        return;
    }
    for (int local = 0; local < channel_count; ++local) {
        int channel = channels[local];
        unsigned long long offset = item * (unsigned long long)channel_count + local;
        base[offset] = residue_from_signed(payload[0] + correction, moduli[channel]);
    }
}

extern "C" __global__ void admit_rrns_first_batch(
    const unsigned long long *first_batch, unsigned long long *decision_keys,
    unsigned long long count, const unsigned long long *moduli,
    unsigned long long bound, int *status) {
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (item >= count) return;
    if (bound > (moduli[0] - 1ULL) / 2ULL) { fail(status, 22); return; }
    unsigned long long row[9] = {0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL};
    row[0] = first_batch[item * 5ULL];
    row[1] = first_batch[item * 5ULL + 1ULL];
    row[2] = first_batch[item * 5ULL + 2ULL];
    row[3] = first_batch[item * 5ULL + 3ULL];
    row[8] = first_batch[item * 5ULL + 4ULL];
    long long key = bounded_symmetric_decode(row[0], moduli[0], bound, status);
    for (int channel = 0; channel < 4; ++channel) {
        if (row[channel] != residue_from_signed(key, moduli[channel])) fail(status, 23);
    }
    if (row[8] != residue_from_signed(key, moduli[8])) fail(status, 23);
    store_positional(decision_keys, item, key);
}

extern "C" __global__ void admit_rrns_second_batch(
    const unsigned long long *second_batch, const unsigned long long *decision_keys,
    unsigned long long count, const unsigned long long *moduli,
    unsigned long long bound, int *status) {
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (item >= count) return;
    long long key = load_positional(decision_keys, item, status);
    unsigned long long magnitude = (unsigned long long)(key < 0 ? -(key + 1LL) + 1ULL : key);
    if (magnitude > bound) fail(status, 24);
    for (int local = 0; local < 4; ++local) {
        int channel = 4 + local;
        unsigned long long observed = second_batch[item * 4ULL + (unsigned long long)local];
        if (observed != residue_from_signed(key, moduli[channel])) fail(status, 23);
    }
}

extern "C" __global__ void encode_positional_rrns_batch(
    const unsigned long long *values, unsigned long long *batch,
    unsigned long long count, const unsigned long long *moduli,
    const int *channels, int channel_count, int *status) {
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    unsigned long long total = count * (unsigned long long)channel_count;
    if (item >= total) return;
    int local = (int)(item % (unsigned long long)channel_count);
    unsigned long long row = item / (unsigned long long)channel_count;
    int channel = channels[local];
    long long value = load_positional(values, row, status);
    batch[item] = residue_from_signed(value, moduli[channel]);
}

extern "C" __global__ void build_prefix_base_bounds(
    const unsigned long long *base, unsigned long long *node_bounds,
    const unsigned char *depths, const unsigned long long *child_offsets,
    const unsigned int *child_indices, const unsigned long long *first_ranks,
    unsigned long long node_count, int *status) {
    if (blockIdx.x || threadIdx.x) return;
    for (unsigned long long reverse = node_count; reverse > 0ULL; --reverse) {
        unsigned long long node = reverse - 1ULL;
        if (depths[node] == 6) {
            store_positional(node_bounds, node,
                load_positional(base, first_ranks[node], status));
            continue;
        }
        unsigned long long begin = child_offsets[node];
        unsigned long long end = child_offsets[node + 1ULL];
        if (begin == end) { fail(status, 41); continue; }
        long long maximum = LLONG_MIN;
        for (unsigned long long edge = begin; edge < end; ++edge) {
            long long value = load_positional(node_bounds, child_indices[edge], status);
            if (value > maximum) maximum = value;
        }
        store_positional(node_bounds, node, maximum);
    }
}

__device__ __forceinline__ long long fixture_prefix_bound(
    long long base_upper, unsigned long long prefix_mask, unsigned char depth,
    int cards, int runtime_mode, int *status) {
    long long total = base_upper;
    if (runtime_mode == 0) return total;
    int start = depth ? 64 - __clzll(prefix_mask) : 0;
    int remaining = 6 - (int)depth;
    for (int card = 0; card < cards; ++card) {
        bool selected = (prefix_mask & (1ULL << card)) != 0ULL;
        bool possible = selected || (card >= start && remaining > 0);
        if (possible) total += 120LL;
    }
    return total;
}

extern "C" __global__ void build_prefix_term_bounds_positional(
    const unsigned long long *base_bounds, unsigned long long *term_bounds,
    const unsigned long long *prefix_masks, const unsigned char *depths,
    unsigned long long node_count, int cards, int runtime_mode, int *status) {
    unsigned long long node = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (node >= node_count) return;
    long long value = fixture_prefix_bound(
        load_positional(base_bounds, node, status), prefix_masks[node],
        depths[node], cards, runtime_mode, status);
    store_positional(term_bounds, node, value);
}

extern "C" __global__ void build_prefix_term_bounds_rrns(
    const unsigned long long *base_bounds, unsigned long long *term_bounds,
    const unsigned long long *prefix_masks, const unsigned char *depths,
    unsigned long long node_count, int cards, int runtime_mode,
    const unsigned long long *moduli, unsigned long long decision_bound,
    unsigned long long *decision_counter, int *status) {
    unsigned long long node = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (node >= node_count) return;
    long long base_value = load_positional(base_bounds, node, status);
    unsigned long long total[9];
    #pragma unroll
    for (int channel = 0; channel < 9; ++channel) {
        total[channel] = residue_from_signed(base_value, moduli[channel]);
    }
    if (runtime_mode != 0) {
        unsigned long long prefix_mask = prefix_masks[node];
        unsigned char depth = depths[node];
        int start = depth ? 64 - __clzll(prefix_mask) : 0;
        int remaining = 6 - (int)depth;
        for (int card = 0; card < cards; ++card) {
            bool selected = (prefix_mask & (1ULL << card)) != 0ULL;
            bool possible = selected || (card >= start && remaining > 0);
            if (!possible) continue;
            unsigned long long contribution[9];
            #pragma unroll
            for (int channel = 0; channel < 9; ++channel) {
                contribution[channel] = residue_from_signed(120LL, moduli[channel]);
            }
            #pragma unroll
            for (int channel = 0; channel < 9; ++channel) {
                total[channel] = residue_add(
                    total[channel], contribution[channel], moduli[channel]);
            }
        }
    }
    long long value = reconstruct_decision_key(total, moduli, decision_bound, status);
    atomicAdd(decision_counter, 1ULL);
    store_positional(term_bounds, node, value);
}

__device__ __forceinline__ bool heap_precedes(
    unsigned int left, unsigned int right, const unsigned long long *bounds,
    const unsigned long long *first_ranks, int *status) {
    long long left_bound = load_positional(bounds, left, status);
    long long right_bound = load_positional(bounds, right, status);
    if (left_bound != right_bound) return left_bound > right_bound;
    return first_ranks[left] < first_ranks[right];
}

__device__ __forceinline__ void heap_push(
    unsigned int *heap, unsigned long long *size, unsigned int node,
    const unsigned long long *bounds, const unsigned long long *first_ranks,
    unsigned long long capacity, int *status) {
    if (*size >= capacity) { fail(status, 51); return; }
    unsigned long long index = (*size)++;
    heap[index] = node;
    while (index) {
        unsigned long long parent = (index - 1ULL) >> 1;
        if (!heap_precedes(heap[index], heap[parent], bounds, first_ranks, status)) break;
        unsigned int temporary = heap[parent];
        heap[parent] = heap[index];
        heap[index] = temporary;
        index = parent;
    }
}

__device__ __forceinline__ unsigned int heap_pop(
    unsigned int *heap, unsigned long long *size,
    const unsigned long long *bounds, const unsigned long long *first_ranks,
    int *status) {
    if (*size == 0ULL) { fail(status, 52); return 0U; }
    unsigned int result = heap[0];
    unsigned int tail = heap[--(*size)];
    if (*size) {
        heap[0] = tail;
        unsigned long long index = 0ULL;
        while (true) {
            unsigned long long left = index * 2ULL + 1ULL;
            if (left >= *size) break;
            unsigned long long right = left + 1ULL;
            unsigned long long best = left;
            if (right < *size && heap_precedes(
                    heap[right], heap[left], bounds, first_ranks, status)) best = right;
            if (!heap_precedes(heap[best], heap[index], bounds, first_ranks, status)) break;
            unsigned int temporary = heap[index];
            heap[index] = heap[best];
            heap[best] = temporary;
            index = best;
        }
    }
    return result;
}

extern "C" __global__ void run_prefix_frontier(
    const unsigned long long *bounds, const unsigned char *depths,
    const unsigned long long *child_offsets, const unsigned int *child_indices,
    const unsigned long long *descendants, const unsigned long long *first_ranks,
    unsigned int *heap, unsigned long long *selected_leaf_ranks,
    unsigned long long node_count,
    unsigned long long source_count, int runtime_mode,
    TerminalReceipt *terminal, int *status) {
    if (blockIdx.x || threadIdx.x) return;
    unsigned long long heap_size = 0ULL;
    heap_push(heap, &heap_size, 0U, bounds, first_ranks, node_count, status);
    terminal->heap_pushes = 1ULL;
    while (heap_size && *status == 0) {
        unsigned int node = heap_pop(heap, &heap_size, bounds, first_ranks, status);
        ++terminal->heap_pops;
        long long bound = load_positional(bounds, node, status);
        if (runtime_mode == 1 && bound <= 0LL) {
            terminal->pruned_sources += descendants[node];
            terminal->covered_sources += descendants[node];
            continue;
        }
        if (depths[node] == 6) {
            selected_leaf_ranks[terminal->exact_leaves] = first_ranks[node];
            ++terminal->exact_leaves;
            ++terminal->covered_sources;
            if (bound > 0LL) {
                terminal->found_positive = 1;
                terminal->witness_rank = first_ranks[node];
                terminal->witness_price = bound;
                return;
            }
            continue;
        }
        for (unsigned long long edge = child_offsets[node];
                edge < child_offsets[(unsigned long long)node + 1ULL]; ++edge) {
            heap_push(heap, &heap_size, child_indices[edge], bounds,
                first_ranks, node_count, status);
            ++terminal->heap_pushes;
        }
    }
    terminal->globally_closed = runtime_mode == 1
        && terminal->covered_sources == source_count ? 1 : 0;
}

extern "C" __global__ void run_hybrid_frontier(
    const unsigned long long *bounds, const unsigned char *depths,
    const unsigned long long *child_offsets, const unsigned int *child_indices,
    const unsigned long long *descendants, const unsigned long long *first_ranks,
    unsigned int *heap, unsigned long long *selected_leaf_ranks,
    unsigned long long node_count, unsigned long long source_count,
    int runtime_mode, TerminalReceipt *terminal, int *status) {
    if (blockIdx.x || threadIdx.x) return;
    unsigned long long heap_size = 0ULL;
    unsigned long long early = (source_count + 63ULL) / 64ULL;
    unsigned long long half = (source_count + 1ULL) / 2ULL;
    unsigned long long hard = (source_count + 7ULL) / 8ULL;
    heap_push(heap, &heap_size, 0U, bounds, first_ranks, node_count, status);
    terminal->heap_pushes = 1ULL;
    while (heap_size && *status == 0) {
        unsigned int node = heap_pop(heap, &heap_size, bounds, first_ranks, status);
        ++terminal->heap_pops;
        long long bound = load_positional(bounds, node, status);
        if (depths[node] == 6) {
            selected_leaf_ranks[terminal->exact_leaves] = first_ranks[node];
            ++terminal->exact_leaves;
            ++terminal->covered_sources;
            if (bound > 0LL) {
                terminal->found_positive = 1;
                terminal->witness_rank = first_ranks[node];
                terminal->witness_price = bound;
                return;
            }
            if (runtime_mode == 1 && (terminal->exact_leaves >= hard
                    || (terminal->exact_leaves >= early
                        && terminal->covered_sources < half))) {
                terminal->switched = 1;
                return;
            }
            continue;
        }
        if (runtime_mode == 1 && bound <= 0LL) {
            terminal->pruned_sources += descendants[node];
            terminal->covered_sources += descendants[node];
            continue;
        }
        for (unsigned long long edge = child_offsets[node];
                edge < child_offsets[(unsigned long long)node + 1ULL]; ++edge) {
            heap_push(heap, &heap_size, child_indices[edge], bounds,
                first_ranks, node_count, status);
            ++terminal->heap_pushes;
        }
    }
    terminal->globally_closed = runtime_mode == 1
        && terminal->covered_sources == source_count ? 1 : 0;
}

__device__ __forceinline__ long long exact_direct_price(
    unsigned long long source_rank, int cards,
    const unsigned long long *h, const unsigned long long *base, int *status) {
    unsigned long long mask = colex_unrank_mask(source_rank, cards, 6);
    long long total = load_positional(base, source_rank, status);
    unsigned long long subset = mask;
    while (true) {
        int level = __popcll(subset);
        if (level <= 4) {
            const long long coefficients[5] = {30LL,-120LL,360LL,-720LL,720LL};
            unsigned long long index = level_offset(cards, level) + colex_rank_mask(subset);
            total += coefficients[level] * load_positional(h, index, status);
        }
        if (subset == 0ULL) break;
        subset = (subset - 1ULL) & mask;
    }
    return total;
}

extern "C" __global__ void evaluate_selected_leaves_positional(
    const unsigned long long *selected_ranks, unsigned long long selected_count,
    const unsigned long long *h, const unsigned long long *base,
    unsigned long long *selected_prices, int cards, int *status) {
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (item >= selected_count) return;
    unsigned long long rank = selected_ranks[item];
    if (rank >= choose_small(cards, 6)) { fail(status, 53); return; }
    store_positional(selected_prices, item,
        exact_direct_price(rank, cards, h, base, status));
}

extern "C" __global__ void evaluate_selected_leaves_rrns_batch(
    const unsigned long long *selected_ranks, unsigned long long selected_count,
    const unsigned long long *h, const unsigned long long *base,
    unsigned long long *selected_prices, int cards,
    const unsigned long long *moduli, const int *channels,
    int channel_count, int *status) {
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (item >= selected_count * (unsigned long long)channel_count) return;
    int local = (int)(item % (unsigned long long)channel_count);
    unsigned long long selected = item / (unsigned long long)channel_count;
    unsigned long long rank = selected_ranks[selected];
    if (rank >= choose_small(cards, 6)) { fail(status, 53); return; }
    int channel = channels[local];
    unsigned long long modulus = moduli[channel];
    unsigned long long total = residue_from_signed(
        load_positional(base, rank, status), modulus);
    unsigned long long mask = colex_unrank_mask(rank, cards, 6);
    unsigned long long subset = mask;
    while (true) {
        int level = __popcll(subset);
        if (level <= 4) {
            const long long coefficients[5] = {30LL,-120LL,360LL,-720LL,720LL};
            unsigned long long index = level_offset(cards, level) + colex_rank_mask(subset);
            unsigned long long value = residue_from_signed(
                load_positional(h, index, status), modulus);
            total = residue_add(total,
                residue_multiply_small(value, coefficients[level], modulus), modulus);
        }
        if (subset == 0ULL) break;
        subset = (subset - 1ULL) & mask;
    }
    selected_prices[item] = total;
}

extern "C" __global__ void direct_prices_positional(
    const unsigned long long *h, const unsigned long long *base,
    unsigned long long *prices, int cards, unsigned long long source_count,
    int *status) {
    unsigned long long rank = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    unsigned long long sources = choose_small(cards, 6);
    if (source_count > sources) { if (rank == 0ULL) fail(status, 54); return; }
    if (rank >= source_count) return;
    long long value = exact_direct_price(rank, cards, h, base, status);
    store_positional(prices, rank, value);
}

extern "C" __global__ void direct_prices_rrns_batch(
    const unsigned long long *h, const unsigned long long *base,
    unsigned long long *prices, int cards, unsigned long long source_count,
    const unsigned long long *moduli, const int *channels,
    int channel_count, int *status) {
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    unsigned long long sources = choose_small(cards, 6);
    if (source_count > sources) { if (item == 0ULL) fail(status, 54); return; }
    unsigned long long count = source_count * (unsigned long long)channel_count;
    if (item >= count) return;
    int local = (int)(item % (unsigned long long)channel_count);
    unsigned long long rank = item / (unsigned long long)channel_count;
    int channel = channels[local];
    unsigned long long modulus = moduli[channel];
    unsigned long long total = residue_from_signed(
        load_positional(base, rank, status), modulus);
    unsigned long long mask = colex_unrank_mask(rank, cards, 6);
    unsigned long long subset = mask;
    while (true) {
        int level = __popcll(subset);
        if (level <= 4) {
            const long long coefficients[5] = {30LL,-120LL,360LL,-720LL,720LL};
            unsigned long long index = level_offset(cards, level) + colex_rank_mask(subset);
            unsigned long long value = residue_from_signed(
                load_positional(h, index, status), modulus);
            total = residue_add(total,
                residue_multiply_small(value, coefficients[level], modulus), modulus);
        }
        if (subset == 0ULL) break;
        subset = (subset - 1ULL) & mask;
    }
    prices[item] = total;
}

extern "C" __global__ void zeta_seed_positional(
    const unsigned long long *h, unsigned long long *levels,
    int cards, int *status) {
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    unsigned long long rows = level_offset(cards, 5);
    if (item >= rows) return;
    unsigned long long offset = 0ULL;
    int level = 0;
    while (level < 5 && item >= offset + choose_small(cards, level)) {
        offset += choose_small(cards, level);
        ++level;
    }
    const long long weights[5] = {1LL,-24LL,360LL,-2880LL,8640LL};
    long long value = load_positional(h, item, status);
    store_positional(levels, item, weights[level] * value);
}

extern "C" __global__ void zeta_seed_rrns_batch(
    const unsigned long long *h, unsigned long long *levels,
    int cards, const unsigned long long *moduli, const int *channels,
    int channel_count, int *status) {
    unsigned long long row_count = level_offset(cards, 5);
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (item >= row_count * (unsigned long long)channel_count) return;
    int local = (int)(item % (unsigned long long)channel_count);
    unsigned long long row = item / (unsigned long long)channel_count;
    unsigned long long offset = 0ULL;
    int level = 0;
    while (level < 5 && row >= offset + choose_small(cards, level)) {
        offset += choose_small(cards, level);
        ++level;
    }
    const long long weights[5] = {1LL,-24LL,360LL,-2880LL,8640LL};
    int channel = channels[local];
    unsigned long long value = residue_from_signed(
        load_positional(h, row, status), moduli[channel]);
    levels[item] = residue_multiply_small(value, weights[level], moduli[channel]);
}

extern "C" __global__ void zeta_cover_positional(
    unsigned long long *levels, int cards, int level, int *status) {
    unsigned long long rank = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    unsigned long long rows = choose_small(cards, level);
    if (rank >= rows) return;
    unsigned long long mask = colex_unrank_mask(rank, cards, level);
    long long total = level <= 4
        ? load_positional(levels, level_offset(cards, level) + rank, status) : 0LL;
    unsigned long long cursor = mask;
    while (cursor) {
        int card = __ffsll((long long)cursor) - 1;
        unsigned long long parent = mask & ~(1ULL << card);
        total += load_positional(levels,
            level_offset(cards, level - 1) + colex_rank_mask(parent), status);
        cursor &= cursor - 1ULL;
    }
    store_positional(levels, level_offset(cards, level) + rank, total);
}

extern "C" __global__ void zeta_cover_rrns_batch(
    const unsigned long long *levels, const unsigned long long *h,
    unsigned long long *batch,
    int cards, int level,
    const unsigned long long *moduli, const int *channels,
    int channel_count, int *status) {
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    unsigned long long rows = choose_small(cards, level);
    if (item >= rows * (unsigned long long)channel_count) return;
    int local = (int)(item % (unsigned long long)channel_count);
    unsigned long long rank = item / (unsigned long long)channel_count;
    int channel = channels[local];
    unsigned long long modulus = moduli[channel];
    unsigned long long target = level_offset(cards, level) + rank;
    const long long weights[5] = {1LL,-24LL,360LL,-2880LL,8640LL};
    unsigned long long total = level <= 4
        ? residue_multiply_small(
            residue_from_signed(load_positional(h, target, status), modulus),
            weights[level], modulus)
        : 0ULL;
    unsigned long long mask = colex_unrank_mask(rank, cards, level);
    unsigned long long cursor = mask;
    while (cursor) {
        int card = __ffsll((long long)cursor) - 1;
        unsigned long long parent = mask & ~(1ULL << card);
        unsigned long long index =
            level_offset(cards, level - 1) + colex_rank_mask(parent);
        unsigned long long value = residue_from_signed(
            load_positional(levels, index, status), modulus);
        total = residue_add(total, value, modulus);
        cursor &= cursor - 1ULL;
    }
    batch[item] = total;
}

extern "C" __global__ void zeta_rank_six_positional(
    const unsigned long long *levels, const unsigned long long *base,
    const unsigned long long *structural_levels, unsigned long long *prices,
    int cards, unsigned long long source_count, int base_mode, int *status) {
    unsigned long long rank = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    unsigned long long sources = choose_small(cards, 6);
    if (source_count > sources) { if (rank == 0ULL) fail(status, 54); return; }
    if (rank >= source_count) return;
    long long h_scaled = load_positional(levels, level_offset(cards, 6) + rank, status);
    long long base_value = load_positional(base, rank, status);
    if (base_mode != 1) {
        long long structural = load_positional(
            structural_levels, level_offset(cards, 6) + rank, status);
        if (structural % 30LL || structural / 30LL != 24LL *
                (base_value + (base_mode == 2 && sparse_support(rank, sources) ? 1LL : 0LL))) {
            fail(status, 61);
        }
    }
    long long scaled = h_scaled + 24LL * base_value;
    if (scaled % 24LL) fail(status, 62);
    store_positional(prices, rank, scaled / 24LL);
}

extern "C" __global__ void zeta_rank_six_rrns_batch(
    const unsigned long long *levels, const unsigned long long *base,
    unsigned long long *prices, int cards, unsigned long long source_count,
    const unsigned long long *moduli, const int *channels,
    int channel_count, int *status) {
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    unsigned long long sources = choose_small(cards, 6);
    if (source_count > sources) { if (item == 0ULL) fail(status, 54); return; }
    if (item >= source_count * (unsigned long long)channel_count) return;
    int local = (int)(item % (unsigned long long)channel_count);
    unsigned long long rank = item / (unsigned long long)channel_count;
    int channel = channels[local];
    unsigned long long modulus = moduli[channel];
    unsigned long long h_scaled = residue_from_signed(
        load_positional(levels, level_offset(cards, 6) + rank, status), modulus);
    unsigned long long base_scaled = residue_multiply_small(
        residue_from_signed(load_positional(base, rank, status), modulus),
        24LL, modulus);
    // The result remains scaled by 24 in RRNS.  It is reconstructed exactly,
    // divisibility is checked positionally, and only then is terminal division
    // performed; no modular inverse of the scale exists in this source.
    prices[item] = residue_add(h_scaled, base_scaled, modulus);
}

extern "C" __global__ void validate_hybrid_switch(
    TerminalReceipt *terminal, unsigned long long source_count,
    int runtime_mode, int *status) {
    if (blockIdx.x || threadIdx.x) return;
    if (runtime_mode == 0 && terminal->switched) fail(status, 64);
    if (runtime_mode == 1 && terminal->switched) {
        unsigned long long early = (source_count + 63ULL) / 64ULL;
        unsigned long long half = (source_count + 1ULL) / 2ULL;
        unsigned long long hard = (source_count + 7ULL) / 8ULL;
        bool early_reason = terminal->exact_leaves >= early
            && terminal->covered_sources < half;
        bool hard_reason = terminal->exact_leaves >= hard;
        if (!early_reason && !hard_reason) fail(status, 65);
    }
}

extern "C" __global__ void terminal_scan(
    const unsigned long long *prices, unsigned long long source_count,
    int runtime_mode, int scaled_by_24, TerminalReceipt *terminal, int *status) {
    if (blockIdx.x || threadIdx.x) return;
    terminal->found_positive = 0;
    terminal->globally_closed = 0;
    terminal->covered_sources = 0ULL;
    terminal->decision_keys = 0ULL;
    for (unsigned long long rank = 0; rank < source_count; ++rank) {
        long long value = load_positional(prices, rank, status);
        if (scaled_by_24) {
            if (value % 24LL) { fail(status, 62); return; }
            value /= 24LL;
        }
        ++terminal->decision_keys;
        if (value > 0LL) {
            terminal->found_positive = 1;
            terminal->witness_rank = rank;
            terminal->witness_price = value;
            if (runtime_mode == 0) return;
            fail(status, 63);
            return;
        }
        ++terminal->covered_sources;
    }
    terminal->globally_closed = runtime_mode == 1 ? 1 : 0;
}

extern "C" __global__ void restore_workspace(
    unsigned char *workspace, unsigned long long byte_count,
    unsigned char baseline) {
    unsigned long long item = (unsigned long long)blockDim.x * blockIdx.x + threadIdx.x;
    if (item < byte_count) workspace[item] = baseline;
}
'''
CUDA_SOURCE_SHA256 = sha256(CUDA_SOURCE.encode("utf-8")).hexdigest()


def cuda_source_contract(source: str = CUDA_SOURCE) -> dict[str, object]:
    if not isinstance(source, str):
        raise TypeError("CUDA source must be text")
    entries = tuple(
        re.findall(r'extern\s+"C"\s+__global__\s+void\s+([A-Za-z0-9_]+)\s*\(', source)
    )
    if entries != KERNEL_NAMES:
        raise ValueError("CUDA entry-kernel order or domain differs")
    required = (
        "reconstruct_decision_key",
        "bounded_symmetric_decode",
        "heap_precedes",
        "RRNS decision reconstruction",
        "No residue is ordered directly",
        "no modular inverse of the scale",
    )
    if any(token not in source for token in required):
        raise ValueError("CUDA decision or scale contract is absent")
    forbidden = (
        "heapq",
        "PyLong",
        "cudaMalloc",
        "cudaFree",
        "__float",
        "double ",
        "resident_nine",
        "inverse_720",
    )
    present_forbidden = tuple(token for token in forbidden if token in source)
    if present_forbidden:
        raise ValueError(f"CUDA source contains forbidden surface: {present_forbidden}")
    full_codeword_calls = source.count("reconstruct_decision_key(") - 1
    batched_admission_consumers = sum(
        name in entries
        for name in ("admit_rrns_first_batch", "admit_rrns_second_batch")
    )
    if full_codeword_calls < 1 or batched_admission_consumers != 2:
        raise ValueError("RRNS decision reconstruction has no scientific consumers")
    return {
        "schema_version": "pontius-adr0457-cuda-source-contract-v1",
        "cuda_source_sha256": sha256(source.encode("utf-8")).hexdigest(),
        "cuda_source_bytes": len(source.encode("utf-8")),
        "entry_kernels": list(entries),
        "decision_reconstruction_call_sites": (
            full_codeword_calls + batched_admission_consumers
        ),
        "full_codeword_reconstruction_call_sites": full_codeword_calls,
        "batched_admission_consumer_sites": batched_admission_consumers,
        "device_resident_prefix_heap": True,
        "resident_nine_schedule_present": False,
        "host_scientific_arithmetic_present": False,
        "compiler_executed": False,
        "device_queried": False,
    }


def timed_host_surface_contract(source_text: str) -> dict[str, object]:
    """Reject unledgered host scientific work inside a timed cell.

    Device launches, frozen control-flow dispatch, phase stamping, terminal
    transport, and workspace clearing are the host's complete allowed role.
    The independent heap/value authorities belong only after the timed cell.
    """

    if not isinstance(source_text, str):
        raise TypeError("timed-host source must be text")
    tree = ast.parse(source_text)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    run = functions.get("_run_calibration_cell")
    if not isinstance(run, ast.FunctionDef):
        raise ValueError("timed calibration cell function is absent")
    callbacks = tuple(
        call.args[0].id
        for call in ast.walk(run)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "phase"
        and len(call.args) == 1
        and isinstance(call.args[0], ast.Name)
    )
    # ast.walk is source-order for these direct expression statements today,
    # but bind the semantic order explicitly instead of relying on that fact.
    direct_callbacks = tuple(
        statement.value.args[0].id
        for statement in run.body
        if isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
        and statement.value.func.id == "phase"
        and len(statement.value.args) == 1
        and isinstance(statement.value.args[0], ast.Name)
    )
    if direct_callbacks != PHASE_CALLBACK_NAMES or set(callbacks) != set(
        PHASE_CALLBACK_NAMES
    ):
        raise ValueError("timed host phase callback domain differs")
    nested = {
        node.name: node
        for node in run.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    forbidden_names = {
        "contract_h",
        "desired_h",
        "exact_price",
        "exact_prices",
        "expected_prefix_terminal",
        "fixture_manifest",
        "prove_early_hybrid_switch",
        "raw_h_row",
        "reconstruct_decision_key",
        "signed_crt",
    }
    for callback in PHASE_CALLBACK_NAMES:
        node = nested.get(callback)
        if node is None:
            raise ValueError(f"timed host callback is absent: {callback}")
        for candidate in ast.walk(node):
            if not isinstance(candidate, ast.Call):
                continue
            if isinstance(candidate.func, ast.Name) and candidate.func.id in forbidden_names:
                raise ValueError(
                    f"host scientific call enters timed callback {callback}: "
                    f"{candidate.func.id}"
                )
            if (
                isinstance(candidate.func, ast.Attribute)
                and candidate.func.attr == "asnumpy"
                and callback != "terminal_transfer"
            ):
                raise ValueError(
                    f"host device value transfer enters timed callback {callback}"
                )
    # A complete Python heap traversal formerly sat between two phase calls.
    # Keep that whole scientific-call family impossible anywhere in the timed
    # function, not merely inside its nested callbacks.
    for candidate in ast.walk(run):
        if (
            isinstance(candidate, ast.Call)
            and isinstance(candidate.func, ast.Name)
            and candidate.func.id in forbidden_names
        ):
            raise ValueError(
                f"host scientific authority enters the timed cell: {candidate.func.id}"
            )
    return {
        "schema_version": "pontius-adr0458-timed-host-surface-v1",
        "phase_callbacks": list(direct_callbacks),
        "host_prefix_authority_calls": 0,
        "host_unbounded_scientific_comparisons": 0,
        "nonterminal_device_to_host_scientific_transfers": 0,
        "passed": True,
    }


def compile_argv(source: Path, cubin: Path) -> tuple[str, ...]:
    if not source.is_absolute() or not cubin.is_absolute():
        raise ValueError("compiled calibration paths must be absolute")
    return (str(NVCC_PATH), *NVCC_OPTIONS, "--output-file", str(cubin), str(source))


@dataclass(frozen=True, slots=True)
class PtxasResource:
    kernel: str
    registers: int
    stack_frame_bytes: int
    spill_store_bytes: int
    spill_load_bytes: int


_PTXAS_ENTRY = re.compile(r"Compiling entry function '([^']+)'")
_PTXAS_PROPERTIES = re.compile(r"Function properties for\s+([^\s]+)")
_PTXAS_MEMORY = re.compile(
    r"(\d+) bytes stack frame, (\d+) bytes spill stores, (\d+) bytes spill loads"
)
_PTXAS_REGISTERS = re.compile(r"Used\s+(\d+) registers")


def parse_ptxas_verbose(raw: bytes) -> dict[str, PtxasResource]:
    if type(raw) is not bytes:
        raise TypeError("ptxas stream must be bytes")
    text = raw.decode("ascii")
    rows: dict[str, dict[str, int]] = {}
    current: str | None = None
    for line in text.splitlines():
        entry = _PTXAS_ENTRY.search(line)
        properties = _PTXAS_PROPERTIES.search(line)
        if entry or properties:
            name = (entry or properties).group(1)  # type: ignore[union-attr]
            current = name if name in KERNEL_NAMES else None
            if current is not None:
                rows.setdefault(current, {})
            continue
        if current is None:
            continue
        memory = _PTXAS_MEMORY.search(line)
        if memory:
            values = {
                "stack_frame_bytes": int(memory.group(1)),
                "spill_store_bytes": int(memory.group(2)),
                "spill_load_bytes": int(memory.group(3)),
            }
            if any(key in rows[current] for key in values):
                raise ValueError(f"ptxas repeats memory fields for {current}")
            rows[current].update(values)
        registers = _PTXAS_REGISTERS.search(line)
        if registers:
            if "registers" in rows[current]:
                raise ValueError(f"ptxas repeats registers for {current}")
            rows[current]["registers"] = int(registers.group(1))
    required = {
        "registers",
        "stack_frame_bytes",
        "spill_store_bytes",
        "spill_load_bytes",
    }
    if set(rows) != set(KERNEL_NAMES) or any(set(row) != required for row in rows.values()):
        raise ValueError("ptxas resource domain is incomplete")
    return {name: PtxasResource(name, **rows[name]) for name in KERNEL_NAMES}


def resource_gate(rows: Mapping[str, PtxasResource]) -> bool:
    if tuple(rows) != KERNEL_NAMES:
        raise ValueError("resource rows are reordered or incomplete")
    return all(
        row.registers <= 255
        and row.spill_store_bytes == 0
        and row.spill_load_bytes == 0
        for row in rows.values()
    )


@dataclass(frozen=True, slots=True)
class CubinResource:
    kernel: str
    registers: int
    stack_bytes: int
    local_bytes: int
    shared_bytes: int


_CUBIN_FUNCTION = re.compile(r"^\s*Function\s+([^:]+):\s*$")
_CUBIN_FIELD = re.compile(r"\b(REG|STACK|LOCAL|SHARED):(\d+)\b")


def parse_cuobjdump_resource_usage(raw: bytes) -> dict[str, CubinResource]:
    if type(raw) is not bytes:
        raise TypeError("cuobjdump resource stream must be bytes")
    text = raw.decode("ascii")
    current: str | None = None
    rows: dict[str, dict[str, int]] = {}
    for line in text.splitlines():
        match = _CUBIN_FUNCTION.match(line)
        if match is not None:
            name = match.group(1).strip()
            current = name if name in KERNEL_NAMES else None
            if current is not None:
                if current in rows:
                    raise ValueError(f"cuobjdump repeats kernel {current}")
                rows[current] = {}
            continue
        if current is None:
            continue
        for key, value in _CUBIN_FIELD.findall(line):
            if key in rows[current]:
                raise ValueError(f"cuobjdump repeats {key} for {current}")
            rows[current][key] = int(value)
    if set(rows) != set(KERNEL_NAMES):
        raise ValueError("cuobjdump resource domain is incomplete")
    output: dict[str, CubinResource] = {}
    for name in KERNEL_NAMES:
        row = rows[name]
        if set(row) != {"REG", "STACK", "LOCAL", "SHARED"}:
            raise ValueError(f"cuobjdump resource row is incomplete: {name}")
        output[name] = CubinResource(
            name,
            row["REG"],
            row["STACK"],
            row["LOCAL"],
            row["SHARED"],
        )
    return output


@dataclass(frozen=True, slots=True)
class SassLocalSites:
    kernel: str
    local_load_sites: int
    local_store_sites: int


_SASS_FUNCTION = re.compile(r"^\s*\.global\s+([^\s]+)\s*$")
_SASS_OPCODE = re.compile(r"\b(LDL|STL)(?:\.[A-Z0-9.]+)?\b")


def parse_nvdisasm_local_sites(raw: bytes) -> dict[str, SassLocalSites]:
    if type(raw) is not bytes:
        raise TypeError("nvdisasm stream must be bytes")
    text = raw.decode("ascii")
    current: str | None = None
    seen: set[str] = set()
    counts = {name: [0, 0] for name in KERNEL_NAMES}
    for line in text.splitlines():
        match = _SASS_FUNCTION.match(line)
        if match is not None:
            name = match.group(1).rstrip(":")
            current = name if name in counts else None
            if current is not None:
                if current in seen:
                    raise ValueError(f"nvdisasm repeats kernel {current}")
                seen.add(current)
            continue
        if current is None:
            continue
        for opcode in _SASS_OPCODE.findall(line):
            counts[current][0 if opcode == "LDL" else 1] += 1
    if seen != set(KERNEL_NAMES):
        raise ValueError("nvdisasm resource domain is incomplete")
    return {
        name: SassLocalSites(name, counts[name][0], counts[name][1])
        for name in KERNEL_NAMES
    }


@dataclass(frozen=True, slots=True)
class DriverResource:
    kernel: str
    registers: int
    local_bytes: int
    shared_bytes: int
    maximum_threads_per_block: int


class CalibrationFailure(RuntimeError):
    """Typed permanent terminal from the one-shot compiled calibration."""

    def __init__(self, terminal: str, reason: str) -> None:
        if not terminal or not reason:
            raise ValueError("calibration failure must be typed and explained")
        super().__init__(reason)
        self.terminal = terminal
        self.reason = reason


@dataclass(frozen=True, slots=True)
class CompiledCalibrationContext:
    cp: object
    np: object
    module: object
    kernels: Mapping[str, object]
    stream: object
    cubin: bytes
    resources: Mapping[str, PtxasResource]
    cubin_resources: Mapping[str, CubinResource]
    sass_resources: Mapping[str, SassLocalSites]
    driver_resources: Mapping[str, DriverResource]
    runtime: Mapping[str, object]
    laboratory_started_ns: int


def _command_evidence(command: object) -> Mapping[str, object]:
    evidence = getattr(command, "evidence", None)
    if not callable(evidence):
        raise TypeError("bounded command evidence surface differs")
    value = evidence()
    if not isinstance(value, Mapping):
        raise TypeError("bounded command evidence is not an object")
    return value


def _load_compiled_context(
    directory: Path,
    emit: Callable[[str, Mapping[str, object]], None],
    *,
    laboratory_started_ns: int,
) -> CompiledCalibrationContext:
    """Compile, inspect, then load the exact retained cubin bytes once."""

    # The import is intentionally inside the owned scientific path.  Source
    # seal imports and probes never reach it.
    from . import legal_river_quotient_fixed_width_device_preflight as inherited

    source_path = (directory / "adr0457_compiled_global_separation.cu").resolve()
    cubin_path = (directory / "adr0457_compiled_global_separation.cubin").resolve()
    inspected_path = (directory / "adr0457_inspected_and_loaded.cubin").resolve()
    raw_source = CUDA_SOURCE.encode("utf-8")
    with source_path.open("xb") as stream:
        stream.write(raw_source)
        stream.flush()
        os.fsync(stream.fileno())
    if source_path.read_bytes() != raw_source:
        raise CalibrationFailure(
            "cuda_source_materialization_rejected",
            "materialized translation unit differs from its sealed literal",
        )
    emit(
        "cuda_source_materialization",
        {
            "schema_version": "pontius-adr0457-source-materialization-v1",
            "cuda_source_sha256": CUDA_SOURCE_SHA256,
            "cuda_source_bytes": len(raw_source),
            "entry_kernels": list(KERNEL_NAMES),
            "compiler_options": list(NVCC_OPTIONS),
        },
    )
    versions = {}
    for label, tool in (
        ("nvcc", NVCC_PATH),
        ("cuobjdump", CUOBJDUMP_PATH),
        ("nvdisasm", NVDISASM_PATH),
    ):
        command = inherited.run_bounded_command(
            (str(tool), "--version"),
            wall_ns=30_000_000_000,
            stdout_limit=1_048_576,
            stderr_limit=1_048_576,
            cwd=directory,
        )
        versions[label] = dict(_command_evidence(command))
        combined = command.stdout + command.stderr
        if command.status != "completed" or command.return_code != 0 or not (
            b"13.3" in combined or b"V13.3" in combined
        ):
            raise CalibrationFailure(
                "tool_identity_rejected", f"{label} is not the frozen CUDA 13.3 tool"
            )
    emit(
        "tool_versions",
        {
            "schema_version": "pontius-adr0457-tool-versions-v1",
            "commands": versions,
        },
    )
    compile_command = inherited.run_bounded_command(
        compile_argv(source_path, cubin_path),
        wall_ns=120_000_000_000,
        stdout_limit=1_048_576,
        stderr_limit=1_048_576,
        cwd=directory,
    )
    emit(
        "compile",
        {
            "schema_version": "pontius-adr0457-compile-v1",
            "command": dict(_command_evidence(compile_command)),
        },
    )
    if compile_command.status != "completed" or compile_command.return_code != 0:
        raise CalibrationFailure("compiler_rejected", "NVCC did not produce the cubin")
    if not cubin_path.is_file():
        raise CalibrationFailure("compiler_rejected", "NVCC output is absent")
    cubin = cubin_path.read_bytes()
    if (
        len(cubin) > 8_388_608
        or not cubin.startswith(bytes((0x7F, 0x45, 0x4C, 0x46)))
    ):
        raise CalibrationFailure("cubin_rejected", "compiled output is not a bounded ELF")
    with inspected_path.open("xb") as stream:
        stream.write(cubin)
        stream.flush()
        os.fsync(stream.fileno())
    if inspected_path.read_bytes() != cubin:
        raise CalibrationFailure("cubin_identity_rejected", "inspection bytes differ")
    emit(
        "durable_cubin_capture",
        {
            "schema_version": "pontius-adr0457-cubin-capture-v1",
            "cubin": inherited.encode_binary(cubin),
            "cubin_sha256": sha256(cubin).hexdigest(),
            "zero_suffix_or_repair_applied": False,
        },
    )
    external = {}
    for label, tool, arguments in (
        (
            "cuobjdump_resource_usage",
            CUOBJDUMP_PATH,
            ("--dump-resource-usage", str(inspected_path)),
        ),
        ("nvdisasm", NVDISASM_PATH, (str(inspected_path),)),
    ):
        command = inherited.run_bounded_command(
            (str(tool), *arguments),
            wall_ns=30_000_000_000,
            stdout_limit=8_388_608,
            stderr_limit=1_048_576,
            cwd=directory,
        )
        external[label] = command
        emit(
            "resource_command",
            {
                "schema_version": "pontius-adr0457-resource-command-v1",
                "command_id": label,
                "command": dict(_command_evidence(command)),
                "inspected_cubin_sha256": sha256(cubin).hexdigest(),
            },
        )
        if command.status != "completed" or command.return_code != 0:
            raise CalibrationFailure(
                "resource_instrument_rejected", f"{label} did not complete"
            )
    try:
        resources = parse_ptxas_verbose(compile_command.stdout + compile_command.stderr)
        cubin_resources = parse_cuobjdump_resource_usage(
            external["cuobjdump_resource_usage"].stdout
        )
        sass_resources = parse_nvdisasm_local_sites(external["nvdisasm"].stdout)
    except (UnicodeDecodeError, TypeError, ValueError) as error:
        raise CalibrationFailure("resource_instrument_rejected", str(error)) from error
    if not resource_gate(resources):
        raise CalibrationFailure(
            "resource_ceiling_rejected", "a compiled kernel spills or exceeds 255 registers"
        )
    emit(
        "compile_resource_evidence",
        {
            "schema_version": "pontius-adr0457-compile-resources-v1",
            "cubin_sha256": sha256(cubin).hexdigest(),
            "ptxas": {name: asdict(row) for name, row in resources.items()},
            "cuobjdump": {
                name: asdict(row) for name, row in cubin_resources.items()
            },
            "sass": {name: asdict(row) for name, row in sass_resources.items()},
            "cuobjdump_sha256": sha256(external["cuobjdump_resource_usage"].stdout).hexdigest(),
            "nvdisasm_sha256": sha256(external["nvdisasm"].stdout).hexdigest(),
            "register_ceiling": 255,
            "spill_store_ceiling_bytes": 0,
            "spill_load_ceiling_bytes": 0,
            "ptxas_cubin_and_SASS_fields_remain_separate": True,
            "passed": True,
        },
    )

    import cupy as cp
    import numpy as np

    properties = cp.cuda.runtime.getDeviceProperties(0)
    device_name = properties["name"]
    if isinstance(device_name, bytes):
        device_name = device_name.decode("utf-8")
    runtime = {
        "device_name": str(device_name),
        "compute_capability": f"{int(properties['major'])}{int(properties['minor'])}",
        "device_total_bytes": int(properties["totalGlobalMem"]),
        "multiprocessor_count": int(properties["multiProcessorCount"]),
        "maximum_threads_per_multiprocessor": int(
            properties["maxThreadsPerMultiProcessor"]
        ),
        "cuda_driver_version": int(cp.cuda.runtime.driverGetVersion()),
        "cuda_runtime_version": int(cp.cuda.runtime.runtimeGetVersion()),
        "cupy_version": str(cp.__version__),
    }
    expected = {
        "device_name": "NVIDIA GeForce RTX 5080",
        "compute_capability": "120",
        "device_total_bytes": DEVICE_TOTAL_BYTES,
        "multiprocessor_count": 84,
        "maximum_threads_per_multiprocessor": 1536,
    }
    if any(runtime[key] != value for key, value in expected.items()):
        raise CalibrationFailure("hardware_identity_rejected", "live GPU differs")
    module = cp.cuda.function.Module()
    module.load(cubin)
    kernels = {name: module.get_function(name) for name in KERNEL_NAMES}
    driver_attributes = {
        "local_bytes": cp.cuda.driver.CU_FUNC_ATTRIBUTE_LOCAL_SIZE_BYTES,
        "registers": cp.cuda.driver.CU_FUNC_ATTRIBUTE_NUM_REGS,
        "shared_bytes": cp.cuda.driver.CU_FUNC_ATTRIBUTE_SHARED_SIZE_BYTES,
        "maximum_threads_per_block": (
            cp.cuda.driver.CU_FUNC_ATTRIBUTE_MAX_THREADS_PER_BLOCK
        ),
    }
    driver_resources = {
        name: DriverResource(
            kernel=name,
            **{
                label: int(cp.cuda.driver.funcGetAttribute(attribute, kernel.ptr))
                for label, attribute in driver_attributes.items()
            },
        )
        for name, kernel in kernels.items()
    }
    stream = cp.cuda.Stream(non_blocking=True)
    emit(
        "module_load_and_runtime",
        {
            "schema_version": "pontius-adr0457-module-runtime-v1",
            "cubin_sha256": sha256(cubin).hexdigest(),
            "runtime": runtime,
            "kernel_count": len(kernels),
            "driver": {
                name: asdict(row) for name, row in driver_resources.items()
            },
            "stack_local_backing_and_static_local_instruction_sites_reported_separately": True,
            "one_stream": True,
        },
    )
    return CompiledCalibrationContext(
        cp,
        np,
        module,
        kernels,
        stream,
        cubin,
        resources,
        cubin_resources,
        sass_resources,
        driver_resources,
        runtime,
        laboratory_started_ns,
    )


def _raw_h_numpy(np: object, cards: int, runtime_mode: RuntimeMode) -> object:
    rows = []
    for level in range(SUBSET_MAXIMUM + 1):
        rows.extend(raw_h_row(runtime_mode, cards, mask) for mask in complete_masks(cards, level))
    return np.ascontiguousarray(rows, dtype=np.int64)  # type: ignore[attr-defined]


def _geometry_numpy(np: object, cards: int) -> dict[str, object]:
    geometry = prefix_geometry(cards)
    return {
        "prefix_masks": np.asarray(geometry.prefix_masks, dtype=np.uint64),  # type: ignore[attr-defined]
        "depths": np.asarray(geometry.depths, dtype=np.uint8),  # type: ignore[attr-defined]
        "child_offsets": np.asarray(geometry.child_offsets, dtype=np.uint64),  # type: ignore[attr-defined]
        "child_indices": np.asarray(geometry.child_indices, dtype=np.uint32),  # type: ignore[attr-defined]
        "descendants": np.asarray(geometry.descendant_counts, dtype=np.uint64),  # type: ignore[attr-defined]
        "first_ranks": np.asarray(geometry.first_colex_ranks, dtype=np.uint64),  # type: ignore[attr-defined]
    }


def _launch(
    context: CompiledCalibrationContext,
    kernel: str,
    count: int,
    arguments: tuple[object, ...],
) -> None:
    items = _plain_int(count, label=f"{kernel} launch count", minimum=0)
    if items == 0:
        return
    threads = 128
    blocks = (items + threads - 1) // threads
    context.kernels[kernel]((blocks,), (threads,), arguments, stream=context.stream)


def _terminal_dtype(np: object) -> object:
    return np.dtype(  # type: ignore[attr-defined]
        [
            ("status", "<i4"),
            ("found_positive", "<i4"),
            ("globally_closed", "<i4"),
            ("switched", "<i4"),
            ("witness_rank", "<u8"),
            ("witness_price", "<i8"),
            ("covered_sources", "<u8"),
            ("heap_pushes", "<u8"),
            ("heap_pops", "<u8"),
            ("exact_leaves", "<u8"),
            ("pruned_sources", "<u8"),
            ("decision_keys", "<u8"),
        ],
        align=True,
    )


@dataclass(slots=True)
class PreparedDeviceDomain:
    cards: int
    h_rows: int
    source_rows: int
    level_rows: int
    prefix_nodes: int
    raw_h: Mapping[str, object]
    pricing_host: object
    pricing: object
    geometry: Mapping[str, object]
    moduli: object
    first_channels: object
    second_channels: object
    expected_tokens: object
    observed_tokens: object
    phase_events: tuple[object, ...]
    base_artifacts: Mapping[tuple[str, str, str], Mapping[str, object]]
    scratch: Mapping[str, object]
    memory_evidence: Mapping[str, object]


def _base_payload_numpy(
    np: object, cards: int, runtime_mode: RuntimeMode, base_mode: BaseMode
) -> object:
    count = comb(cards, SOURCE_WIDTH)
    if base_mode == "opaque_per_source_base":
        values = [base_value(runtime_mode, base_mode, rank, cards) for rank in range(count)]
    elif base_mode == BASE_MODES[2]:
        structural = 2 if runtime_mode == "positive_witness" else -721
        values = [structural]
        for rank in sparse_support_ranks(cards):
            values.extend((rank, -1))
    else:
        values = [1 if runtime_mode == "positive_witness" else -721]
    return np.ascontiguousarray(values, dtype=np.int64)  # type: ignore[attr-defined]


def _prepare_device_domains(
    context: CompiledCalibrationContext,
    emit: Callable[[str, Mapping[str, object]], None],
) -> dict[int, PreparedDeviceDomain]:
    cp = context.cp
    np = context.np
    stream = context.stream
    pricing_host = np.asarray(pricing_vector(), dtype=np.int64)
    pricing_host.setflags(write=False)
    pricing_digest = sha256(pricing_host.tobytes()).hexdigest()
    moduli_host = np.asarray(WORKING_MODULI + (REDUNDANT_MODULUS,), dtype=np.uint64)
    first_channels_host = np.asarray(RRNS_FIRST_BATCH, dtype=np.int32)
    second_channels_host = np.asarray(RRNS_SECOND_BATCH, dtype=np.int32)
    prepared: dict[int, PreparedDeviceDomain] = {}
    campaign_memory = memory_liveness(
        campaign_memory_plan(), boundary_count=len(PHASE_NAMES) + 2
    )
    if not campaign_memory.ceiling_passed or not campaign_memory.reserve_passed:
        raise CalibrationFailure(
            "device_memory_admission_rejected",
            "complete five-domain named allocation exceeds a frozen cap",
        )
    emit(
        "device_memory_admission",
        {
            "schema_version": "pontius-adr0457-device-memory-admission-v1",
            "campaign": asdict(campaign_memory),
            "physical_RRNS_table_arena_allocations": 1,
            "RRNS_table_arena_channel_capacity": 5,
            "five_channel_table_workspace_only": True,
            "resident_nine_table_workspace": False,
            "rejected_liveness_equivalence": REJECTED_LIVENESS_EQUIVALENCE,
            "allocation_precedes_warmup": True,
        },
    )
    # The campaign owns exactly one physical RRNS table arena.  It is allocated
    # only after the independent named-liveness admission above has passed.
    # Every domain and table stage below receives a bounded view of this storage.
    global_rrns_batch_arena = cp.zeros(
        max(rrns_batch_arena_rows(cards) for cards in DOMAINS) * 5,
        dtype=cp.uint64,
    )
    for cards in DOMAINS:
        h_rows = sum(comb(cards, level) for level in range(SUBSET_MAXIMUM + 1))
        source_rows = comb(cards, SOURCE_WIDTH)
        level_rows = sum(comb(cards, level) for level in range(SOURCE_WIDTH + 1))
        geometry_host = _geometry_numpy(np, cards)
        geometry_device = {name: cp.asarray(value) for name, value in geometry_host.items()}
        raw_h_device = {
            mode: cp.asarray(_raw_h_numpy(np, cards, mode)) for mode in RUNTIME_MODES
        }
        pricing_device = cp.asarray(pricing_host)
        moduli_device = cp.asarray(moduli_host)
        first_channels = cp.asarray(first_channels_host)
        second_channels = cp.asarray(second_channels_host)
        tokens = np.asarray(
            [
                int.from_bytes(
                    sha256(
                        f"adr0457|{cards}|pricing|{pricing_digest}|token|{index}".encode(
                            "ascii"
                        )
                    ).digest()[:8],
                    "little",
                )
                for index in range(6)
            ],
            dtype=np.uint64,
        )
        expected_tokens = cp.asarray(tokens)
        observed_tokens = cp.asarray(tokens.copy())
        status = cp.zeros(1, dtype=cp.int32)
        base_artifacts: dict[tuple[str, str, str], dict[str, object]] = {}
        for runtime_mode, base_mode, schedule in product(
            RUNTIME_MODES, BASE_MODES, ARITHMETIC_SCHEDULES
        ):
            key = (runtime_mode, base_mode, schedule)
            payload_host = _base_payload_numpy(
                np, cards, runtime_mode, base_mode  # type: ignore[arg-type]
            )
            payload_host.setflags(write=False)
            payload_device = cp.asarray(payload_host)
            payload_count = int(payload_host.size)
            support_count = (payload_count - 1) // 2 if base_mode == BASE_MODES[2] else 0
            artifact_token_host = np.asarray(
                [
                    int.from_bytes(
                        sha256(
                            (
                                f"adr0457|{cards}|{runtime_mode}|{base_mode}|"
                                f"{schedule}|artifact-token|{index}|"
                                + sha256(payload_host.tobytes()).hexdigest()
                            ).encode("ascii")
                        ).digest()[:8],
                        "little",
                    )
                    for index in range(6)
                ],
                dtype=np.uint64,
            )
            runtime_index = RUNTIME_MODES.index(runtime_mode)
            base_index = BASE_MODES.index(base_mode)
            artifact = {
                "payload_host": payload_host,
                "payload": payload_device,
                "payload_count": payload_count,
                "support_count": support_count,
                "expected_tokens": cp.asarray(artifact_token_host),
                "observed_tokens": cp.asarray(artifact_token_host.copy()),
                "base": cp.zeros(source_rows * 2, dtype=cp.uint64),
                "structural": cp.zeros(level_rows * 2, dtype=cp.uint64),
            }
            _launch(
                context,
                "build_base_positional",
                1,
                (
                    artifact["payload"],
                    np.uint64(payload_count),
                    artifact["base"],
                    artifact["structural"],
                    np.int32(cards),
                    np.int32(runtime_index),
                    np.int32(base_index),
                    status,
                ),
            )
            if support_count:
                _launch(
                    context,
                    "apply_sparse_patch_positional",
                    support_count,
                    (
                        artifact["payload"],
                        np.uint64(payload_count),
                        artifact["base"],
                        np.int32(cards),
                        np.int32(base_index),
                        status,
                    ),
                )
            base_artifacts[key] = artifact
        scratch = {
            "status": status,
            "decision_counter": cp.zeros(1, dtype=cp.uint64),
            "h_positional": cp.zeros(h_rows * 2, dtype=cp.uint64),
            "prices_positional": cp.zeros(source_rows * 2, dtype=cp.uint64),
            "zeta_positional": cp.zeros(level_rows * 2, dtype=cp.uint64),
            # One physical five-channel table arena serves every RRNS stage.
            # Sequential replay is represented by overwrite, so neither a
            # resident-nine table nor parallel per-table batches can exist.
            "rrns_batch_arena": global_rrns_batch_arena[
                : rrns_batch_arena_rows(cards) * 5
            ],
            "patch_decision": cp.zeros(
                len(sparse_support_ranks(cards)) * 2, dtype=cp.uint64
            ),
            "prefix_base_bounds": cp.zeros(
                prefix_geometry(cards).node_count * 2, dtype=cp.uint64
            ),
            "prefix_term_bounds": cp.zeros(
                prefix_geometry(cards).node_count * 2, dtype=cp.uint64
            ),
            "heap": cp.zeros(prefix_geometry(cards).node_count, dtype=cp.uint32),
            "selected_leaf_ranks": cp.zeros(source_rows, dtype=cp.uint64),
            "selected_positional": cp.zeros(source_rows * 2, dtype=cp.uint64),
            "terminal": cp.zeros(1, dtype=_terminal_dtype(np)),
        }
        phase_events = tuple(cp.cuda.Event() for _ in range(len(PHASE_NAMES) + 1))
        stream.synchronize()
        status_value = int(cp.asnumpy(status)[0])
        if status_value:
            raise CalibrationFailure(
                "workspace_preparation_rejected",
                f"domain {cards} preparation status {status_value}",
            )
        domain_memory = memory_liveness(
            reduced_memory_plan(cards, ARITHMETIC_SCHEDULES[0]),
            boundary_count=len(PHASE_NAMES) + 2,
        )
        memory = {"shared_five_channel_replay": asdict(domain_memory)}
        if not domain_memory.ceiling_passed or not domain_memory.reserve_passed:
            raise CalibrationFailure(
                "device_memory_admission_rejected", f"domain {cards} liveness exceeds cap"
            )
        prepared[cards] = PreparedDeviceDomain(
            cards,
            h_rows,
            source_rows,
            level_rows,
            prefix_geometry(cards).node_count,
            raw_h_device,
            pricing_host,
            pricing_device,
            geometry_device,
            moduli_device,
            first_channels,
            second_channels,
            expected_tokens,
            observed_tokens,
            phase_events,
            base_artifacts,
            scratch,
            memory,
        )
        emit(
            "device_domain_prepared",
            {
                "schema_version": "pontius-adr0457-device-domain-prepared-v1",
                "cards": cards,
                "h_rows": h_rows,
                "source_rows": source_rows,
                "zeta_level_rows": level_rows,
                "prefix_nodes": prefix_geometry(cards).node_count,
                "prefix_geometry_sha256": prefix_geometry(cards).sha256,
                "memory": memory,
                "allocation_precedes_warmup": True,
            },
        )
    return prepared


def _empty_phase_work(coordinates: Mapping[str, int]) -> list[dict[str, int]]:
    return [
        {
            "projection_work": coordinates[name],
            "logical_operations": coordinates[name],
            "arithmetic_words": 0,
            "transferred_bytes": 0,
            "decision_keys_reconstructed": 0,
        }
        for name in PHASE_NAMES
    ]


def _terminal_mapping(value: object) -> dict[str, int]:
    names = (
        "status",
        "found_positive",
        "globally_closed",
        "switched",
        "witness_rank",
        "witness_price",
        "covered_sources",
        "heap_pushes",
        "heap_pops",
        "exact_leaves",
        "pruned_sources",
        "decision_keys",
    )
    return {name: int(value[name]) for name in names}


def _run_calibration_cell(
    context: CompiledCalibrationContext,
    prepared: PreparedDeviceDomain,
    cell: CellKey,
    *,
    pass_index: int,
) -> dict[str, object]:
    cp = context.cp
    np = context.np
    stream = context.stream
    scratch = prepared.scratch
    artifact = prepared.base_artifacts[
        (cell.runtime_mode, cell.base_mode, cell.arithmetic_schedule)
    ]
    rrns = cell.arithmetic_schedule == ARITHMETIC_SCHEDULES[1]
    prefix_arm = cell.arm in ARM_NAMES[2:]
    direct_arm = cell.arm == ARM_NAMES[0]
    zeta_arm = cell.arm == ARM_NAMES[1]
    hybrid = cell.arm == ARM_NAMES[3]
    positive = cell.runtime_mode == RUNTIME_MODES[0]
    cold = cell.refresh_state == REFRESH_STATES[0]
    runtime_index = RUNTIME_MODES.index(cell.runtime_mode)
    base_index = BASE_MODES.index(cell.base_mode)
    bounds = {
        row.quantity: row.signed_absolute_bound
        for row in derive_arithmetic_admission().quantity_widths
    }
    structural_bound = bounds["base_structural_level"]
    zeta_bounds = {
        index: row.signed_absolute_bound
        for index, row in enumerate(derive_arithmetic_admission().zeta_rank_widths)
    }
    coordinates = phase_work_coordinates(cell)
    work_rows = _empty_phase_work(coordinates)
    stamps: list[int] = []
    from time import perf_counter_ns

    def phase(function: Callable[[], None]) -> None:
        if not stamps:
            prepared.phase_events[0].record(stream)
            stream.synchronize()
            stamps.append(perf_counter_ns())
        function()
        prepared.phase_events[len(stamps)].record(stream)
        stream.synchronize()
        stamps.append(perf_counter_ns())

    def admit_batch(
        batch: object,
        decision: object,
        count: int,
        bound: int,
        *,
        first: bool,
    ) -> None:
        _launch(
            context,
            "admit_rrns_first_batch" if first else "admit_rrns_second_batch",
            count,
            (
                batch,
                decision,
                np.uint64(count),
                prepared.moduli,
                np.uint64(bound),
                scratch["status"],
            ),
        )

    def reset_and_bind() -> None:
        with stream:
            scratch["status"].fill(0)
            scratch["decision_counter"].fill(0)
            scratch["terminal"].fill(0)
        prepared.pricing.set(prepared.pricing_host, stream=stream)
        _launch(
            context,
            "bind_provenance",
            6,
            (
                prepared.expected_tokens,
                prepared.observed_tokens,
                np.int32(6),
                scratch["status"],
            ),
        )
        _launch(
            context,
            "bind_provenance",
            6,
            (
                artifact["expected_tokens"],
                artifact["observed_tokens"],
                np.int32(6),
                scratch["status"],
            ),
        )

    phase(reset_and_bind)

    def contract() -> None:
        if rrns:
            for first, channels, channel_count in (
                (True, prepared.first_channels, 5),
                (False, prepared.second_channels, 4),
            ):
                _launch(
                    context,
                    "contract_h_rrns_batch",
                    prepared.h_rows * channel_count,
                    (
                        prepared.raw_h[cell.runtime_mode],
                        prepared.pricing,
                        scratch["rrns_batch_arena"],
                        np.uint64(prepared.h_rows),
                        prepared.moduli,
                        channels,
                        np.int32(channel_count),
                        scratch["status"],
                    ),
                )
                admit_batch(
                    scratch["rrns_batch_arena"],
                    scratch["h_positional"],
                    prepared.h_rows,
                    bounds["contracted_h"],
                    first=first,
                )
        else:
            _launch(
                context,
                "contract_h_positional",
                prepared.h_rows,
                (
                    prepared.raw_h[cell.runtime_mode],
                    prepared.pricing,
                    scratch["h_positional"],
                    np.uint64(prepared.h_rows),
                    scratch["status"],
                ),
            )

    phase(contract)

    def payload_transfer() -> None:
        if not cold:
            return
        artifact["payload"].set(artifact["payload_host"], stream=stream)
        if cell.base_mode != BASE_MODES[1]:
            return
        if rrns:
            for first, channels, channel_count in (
                (True, prepared.first_channels, 5),
                (False, prepared.second_channels, 4),
            ):
                _launch(
                    context,
                    "build_base_rrns_batch",
                    1,
                    (
                        artifact["payload"],
                        np.uint64(artifact["payload_count"]),
                        scratch["rrns_batch_arena"],
                        np.int32(0),
                        np.int32(cell.cards),
                        np.int32(runtime_index),
                        np.int32(base_index),
                        prepared.moduli,
                        channels,
                        np.int32(channel_count),
                        scratch["status"],
                    ),
                )
                admit_batch(
                    scratch["rrns_batch_arena"],
                    artifact["base"],
                    prepared.source_rows,
                    bounds["base_value"],
                    first=first,
                )
        else:
            _launch(
                context,
                "build_base_positional",
                1,
                (
                    artifact["payload"],
                    np.uint64(artifact["payload_count"]),
                    artifact["base"],
                    artifact["structural"],
                    np.int32(cell.cards),
                    np.int32(runtime_index),
                    np.int32(base_index),
                    scratch["status"],
                ),
            )

    phase(payload_transfer)

    def structural_cover() -> None:
        if not cold or cell.base_mode == BASE_MODES[1]:
            return
        if rrns:
            for first, channels, channel_count in (
                (True, prepared.first_channels, 5),
                (False, prepared.second_channels, 4),
            ):
                _launch(
                    context,
                    "build_base_rrns_batch",
                    1,
                    (
                        artifact["payload"],
                        np.uint64(artifact["payload_count"]),
                        scratch["rrns_batch_arena"],
                        np.int32(0),
                        np.int32(cell.cards),
                        np.int32(runtime_index),
                        np.int32(base_index),
                        prepared.moduli,
                        channels,
                        np.int32(channel_count),
                        scratch["status"],
                    ),
                )
                admit_batch(
                    scratch["rrns_batch_arena"],
                    artifact["base"],
                    prepared.source_rows,
                    bounds["base_value"],
                    first=first,
                )
                # The structural replay starts only after the base batch has
                # been admitted.  It overwrites the same five-channel arena;
                # concurrent base/structural RRNS residency is impossible.
                _launch(
                    context,
                    "build_base_rrns_batch",
                    1,
                    (
                        artifact["payload"],
                        np.uint64(artifact["payload_count"]),
                        scratch["rrns_batch_arena"],
                        np.int32(1),
                        np.int32(cell.cards),
                        np.int32(runtime_index),
                        np.int32(base_index),
                        prepared.moduli,
                        channels,
                        np.int32(channel_count),
                        scratch["status"],
                    ),
                )
                admit_batch(
                    scratch["rrns_batch_arena"],
                    artifact["structural"],
                    prepared.level_rows,
                    structural_bound,
                    first=first,
                )
        else:
            _launch(
                context,
                "build_base_positional",
                1,
                (
                    artifact["payload"],
                    np.uint64(artifact["payload_count"]),
                    artifact["base"],
                    artifact["structural"],
                    np.int32(cell.cards),
                    np.int32(runtime_index),
                    np.int32(base_index),
                    scratch["status"],
                ),
            )

    phase(structural_cover)

    def sparse_patch() -> None:
        if not cold or cell.base_mode != BASE_MODES[2]:
            return
        if rrns:
            support_count = int(artifact["support_count"])
            for first, channels, channel_count in (
                (True, prepared.first_channels, 5),
                (False, prepared.second_channels, 4),
            ):
                _launch(
                    context,
                    "apply_sparse_patch_rrns_batch",
                    support_count,
                    (
                        artifact["payload"],
                        np.uint64(artifact["payload_count"]),
                        scratch["rrns_batch_arena"],
                        np.int32(cell.cards),
                        np.int32(base_index),
                        prepared.moduli,
                        channels,
                        np.int32(channel_count),
                        scratch["status"],
                    ),
                )
                admit_batch(
                    scratch["rrns_batch_arena"],
                    scratch["patch_decision"],
                    support_count,
                    bounds["base_value"],
                    first=first,
                )
            _launch(
                context,
                "apply_sparse_patch_positional",
                support_count,
                (
                    artifact["payload"],
                    np.uint64(artifact["payload_count"]),
                    artifact["base"],
                    np.int32(cell.cards),
                    np.int32(base_index),
                    scratch["status"],
                ),
            )
        else:
            _launch(
                context,
                "apply_sparse_patch_positional",
                int(artifact["support_count"]),
                (
                    artifact["payload"],
                    np.uint64(artifact["payload_count"]),
                    artifact["base"],
                    np.int32(cell.cards),
                    np.int32(base_index),
                    scratch["status"],
                ),
            )

    phase(sparse_patch)

    def encode_and_admit() -> None:
        if not rrns:
            return
        for first, channels, channel_count in (
            (True, prepared.first_channels, 5),
            (False, prepared.second_channels, 4),
        ):
            _launch(
                context,
                "encode_positional_rrns_batch",
                prepared.source_rows * channel_count,
                (
                    artifact["base"],
                    scratch["rrns_batch_arena"],
                    np.uint64(prepared.source_rows),
                    prepared.moduli,
                    channels,
                    np.int32(channel_count),
                    scratch["status"],
                ),
            )
            admit_batch(
                scratch["rrns_batch_arena"],
                artifact["base"],
                prepared.source_rows,
                bounds["base_value"],
                first=first,
            )

    phase(encode_and_admit)
    h_decision = scratch["h_positional"]
    base_decision = artifact["base"]

    def prefix_base() -> None:
        if not prefix_arm:
            return
        geometry = prepared.geometry
        _launch(
            context,
            "build_prefix_base_bounds",
            1,
            (
                base_decision,
                scratch["prefix_base_bounds"],
                geometry["depths"],
                geometry["child_offsets"],
                geometry["child_indices"],
                geometry["first_ranks"],
                np.uint64(prepared.prefix_nodes),
                scratch["status"],
            ),
        )

    phase(prefix_base)

    def prefix_terms() -> None:
        if not prefix_arm:
            return
        geometry = prepared.geometry
        if rrns:
            _launch(
                context,
                "build_prefix_term_bounds_rrns",
                prepared.prefix_nodes,
                (
                    scratch["prefix_base_bounds"],
                    scratch["prefix_term_bounds"],
                    geometry["prefix_masks"],
                    geometry["depths"],
                    np.uint64(prepared.prefix_nodes),
                    np.int32(cell.cards),
                    np.int32(runtime_index),
                    prepared.moduli,
                    np.uint64(bounds["prefix_bound"]),
                    scratch["decision_counter"],
                    scratch["status"],
                ),
            )
        else:
            _launch(
                context,
                "build_prefix_term_bounds_positional",
                prepared.prefix_nodes,
                (
                    scratch["prefix_base_bounds"],
                    scratch["prefix_term_bounds"],
                    geometry["prefix_masks"],
                    geometry["depths"],
                    np.uint64(prepared.prefix_nodes),
                    np.int32(cell.cards),
                    np.int32(runtime_index),
                    scratch["status"],
                ),
            )

    phase(prefix_terms)

    # Frozen fixture algebra, not an observed host traversal: positive prefix
    # stops at one exact leaf, pure prove-none prefix prunes without a leaf,
    # and the preregistered hybrid control switches exactly at ceil(N/64).
    # The complete independent heap traversal remains post-run verification.
    expected_selected = (
        1
        if prefix_arm and positive
        else (prepared.source_rows + 63) // 64
        if hybrid and not positive
        else 0
    )

    def frontier() -> None:
        if not prefix_arm:
            return
        geometry = prepared.geometry
        common = (
            scratch["prefix_term_bounds"],
            geometry["depths"],
            geometry["child_offsets"],
            geometry["child_indices"],
            geometry["descendants"],
            geometry["first_ranks"],
            scratch["heap"],
            scratch["selected_leaf_ranks"],
            np.uint64(prepared.prefix_nodes),
        )
        if hybrid:
            arguments = common + (
                np.uint64(prepared.source_rows),
                np.int32(runtime_index),
                scratch["terminal"],
                scratch["status"],
            )
            _launch(context, "run_hybrid_frontier", 1, arguments)
        else:
            arguments = common + (
                np.uint64(prepared.source_rows),
                np.int32(runtime_index),
                scratch["terminal"],
                scratch["status"],
            )
            _launch(context, "run_prefix_frontier", 1, arguments)

    phase(frontier)

    def selected_leaves() -> None:
        if expected_selected == 0:
            return
        if rrns:
            for first, channels, channel_count in (
                (True, prepared.first_channels, 5),
                (False, prepared.second_channels, 4),
            ):
                _launch(
                    context,
                    "evaluate_selected_leaves_rrns_batch",
                    expected_selected * channel_count,
                    (
                        scratch["selected_leaf_ranks"],
                        np.uint64(expected_selected),
                        h_decision,
                        base_decision,
                        scratch["rrns_batch_arena"],
                        np.int32(cell.cards),
                        np.uint64(scan_count),
                        prepared.moduli,
                        channels,
                        np.int32(channel_count),
                        scratch["status"],
                    ),
                )
                admit_batch(
                    scratch["rrns_batch_arena"],
                    scratch["selected_positional"],
                    expected_selected,
                    bounds["direct_price_accumulator"],
                    first=first,
                )
        else:
            _launch(
                context,
                "evaluate_selected_leaves_positional",
                expected_selected,
                (
                    scratch["selected_leaf_ranks"],
                    np.uint64(expected_selected),
                    h_decision,
                    base_decision,
                    scratch["selected_positional"],
                    np.int32(cell.cards),
                    scratch["status"],
                ),
            )

    phase(selected_leaves)

    scan_count = 1 if positive else prepared.source_rows

    def direct() -> None:
        if not direct_arm:
            return
        if rrns:
            for first, channels, channel_count in (
                (True, prepared.first_channels, 5),
                (False, prepared.second_channels, 4),
            ):
                _launch(
                    context,
                    "direct_prices_rrns_batch",
                    scan_count * channel_count,
                    (
                        h_decision,
                        base_decision,
                        scratch["rrns_batch_arena"],
                        np.int32(cell.cards),
                        prepared.moduli,
                        channels,
                        np.int32(channel_count),
                        scratch["status"],
                    ),
                )
                admit_batch(
                    scratch["rrns_batch_arena"],
                    scratch["prices_positional"],
                    scan_count,
                    bounds["direct_price_accumulator"],
                    first=first,
                )
        else:
            _launch(
                context,
                "direct_prices_positional",
                scan_count,
                (
                    h_decision,
                    base_decision,
                    scratch["prices_positional"],
                    np.int32(cell.cards),
                    np.uint64(scan_count),
                    scratch["status"],
                ),
            )

    phase(direct)

    zeta_runs = zeta_arm or (hybrid and not positive)

    def zeta_seed() -> None:
        if not zeta_runs:
            return
        if rrns:
            for first, channels, channel_count in (
                (True, prepared.first_channels, 5),
                (False, prepared.second_channels, 4),
            ):
                _launch(
                    context,
                    "zeta_seed_rrns_batch",
                    prepared.h_rows * channel_count,
                    (
                        h_decision,
                        scratch["rrns_batch_arena"],
                        np.int32(cell.cards),
                        prepared.moduli,
                        channels,
                        np.int32(channel_count),
                        scratch["status"],
                    ),
                )
                admit_batch(
                    scratch["rrns_batch_arena"],
                    scratch["zeta_positional"],
                    prepared.h_rows,
                    max(zeta_bounds[level] for level in range(5)),
                    first=first,
                )
        else:
            _launch(
                context,
                "zeta_seed_positional",
                prepared.h_rows,
                (
                    h_decision,
                    scratch["zeta_positional"],
                    np.int32(cell.cards),
                    scratch["status"],
                ),
            )

    phase(zeta_seed)

    def zeta_cover() -> None:
        if not zeta_runs:
            return
        for level in range(1, SOURCE_WIDTH + 1):
            rows = comb(cell.cards, level)
            if rrns:
                offset = level_offset(cell.cards, level)
                decision_view = scratch["zeta_positional"][offset * 2 :]
                for first, channels, channel_count in (
                    (True, prepared.first_channels, 5),
                    (False, prepared.second_channels, 4),
                ):
                    _launch(
                        context,
                        "zeta_cover_rrns_batch",
                        rows * channel_count,
                        (
                            scratch["zeta_positional"],
                            h_decision,
                            scratch["rrns_batch_arena"],
                            np.int32(cell.cards),
                            np.int32(level),
                            prepared.moduli,
                            channels,
                            np.int32(channel_count),
                            scratch["status"],
                        ),
                    )
                    admit_batch(
                        scratch["rrns_batch_arena"],
                        decision_view,
                        rows,
                        zeta_bounds[level],
                        first=first,
                    )
            else:
                _launch(
                    context,
                    "zeta_cover_positional",
                    rows,
                    (
                        scratch["zeta_positional"],
                        np.int32(cell.cards),
                        np.int32(level),
                        scratch["status"],
                    ),
                )

    phase(zeta_cover)

    def zeta_stream() -> None:
        if not zeta_runs:
            return
        if rrns:
            for first, channels, channel_count in (
                (True, prepared.first_channels, 5),
                (False, prepared.second_channels, 4),
            ):
                _launch(
                    context,
                    "zeta_rank_six_rrns_batch",
                    scan_count * channel_count,
                    (
                        scratch["zeta_positional"],
                        base_decision,
                        scratch["rrns_batch_arena"],
                        np.int32(cell.cards),
                        np.uint64(scan_count),
                        prepared.moduli,
                        channels,
                        np.int32(channel_count),
                        scratch["status"],
                    ),
                )
                admit_batch(
                    scratch["rrns_batch_arena"],
                    scratch["prices_positional"],
                    scan_count,
                    bounds["zeta_output_scaled"],
                    first=first,
                )
        else:
            _launch(
                context,
                "zeta_rank_six_positional",
                scan_count,
                (
                    scratch["zeta_positional"],
                    base_decision,
                    artifact["structural"],
                    scratch["prices_positional"],
                    np.int32(cell.cards),
                    np.uint64(scan_count),
                    np.int32(base_index),
                    scratch["status"],
                ),
            )

    phase(zeta_stream)

    def hybrid_switch() -> None:
        if hybrid:
            _launch(
                context,
                "validate_hybrid_switch",
                1,
                (
                    scratch["terminal"],
                    np.uint64(prepared.source_rows),
                    np.int32(runtime_index),
                    scratch["status"],
                ),
            )

    phase(hybrid_switch)

    def reconstruct_terminal_values() -> None:
        if not rrns or not (direct_arm or zeta_runs):
            return
        bound = (
            bounds["zeta_output_scaled"]
            if zeta_runs
            else bounds["direct_price_accumulator"]
        )
        for first, channels, channel_count in (
            (True, prepared.first_channels, 5),
            (False, prepared.second_channels, 4),
        ):
            _launch(
                context,
                "encode_positional_rrns_batch",
                scan_count * channel_count,
                (
                    scratch["prices_positional"],
                    scratch["rrns_batch_arena"],
                    np.uint64(scan_count),
                    prepared.moduli,
                    channels,
                    np.int32(channel_count),
                    scratch["status"],
                ),
            )
            admit_batch(
                scratch["rrns_batch_arena"],
                scratch["prices_positional"],
                scan_count,
                bound,
                first=first,
            )

    phase(reconstruct_terminal_values)

    def terminal_reduce() -> None:
        if prefix_arm and not (hybrid and not positive):
            return
        prices = scratch["prices_positional"]
        _launch(
            context,
            "terminal_scan",
            1,
            (
                prices,
                np.uint64(scan_count),
                np.int32(runtime_index),
                np.int32(1 if rrns and zeta_runs else 0),
                scratch["terminal"],
                scratch["status"],
            ),
        )

    phase(terminal_reduce)
    terminal_host: dict[str, int] = {}

    def terminal_transfer() -> None:
        nonlocal terminal_host
        terminal_value = cp.asnumpy(scratch["terminal"])[0]
        terminal_host = _terminal_mapping(terminal_value)
        terminal_host["status"] = int(cp.asnumpy(scratch["status"])[0])
        terminal_host["prefix_decision_keys"] = int(
            cp.asnumpy(scratch["decision_counter"])[0]
        )

    phase(terminal_transfer)

    def restore() -> None:
        retained_outputs = {
            "prices_positional",
            "selected_leaf_ranks",
            "selected_positional",
        }
        for name in sorted(set(scratch) - retained_outputs):
            value = scratch[name]
            byte_count = int(value.nbytes)
            _launch(
                context,
                "restore_workspace",
                byte_count,
                (value, np.uint64(byte_count), np.uint8(0)),
            )

    phase(restore)
    restored_bytes = sum(
        int(value.nbytes)
        for name, value in scratch.items()
        if name
        not in {"prices_positional", "selected_leaf_ranks", "selected_positional"}
    )
    if restored_bytes != coordinates["workspace_baseline_restore"]:
        raise CalibrationFailure(
            "work_receipt_rejected", "restored workspace byte count differs"
        )
    if len(stamps) != len(PHASE_NAMES) + 1:
        raise CalibrationFailure("phase_partition_rejected", "phase boundary count differs")
    if terminal_host.get("status") != 0:
        terminal = (
            "rrns_channel_fault_detected"
            if terminal_host.get("status") in {21, 22, 23, 24}
            else "compiled_reduced_calibration_rejected"
        )
        raise CalibrationFailure(
            terminal,
            f"cell {cell.canonical} device status {terminal_host.get('status')}",
        )
    if positive:
        if terminal_host.get("found_positive") != 1 or terminal_host.get("witness_price", 0) <= 0:
            raise CalibrationFailure(
                "compiled_reduced_calibration_rejected",
                f"positive witness contract failed for {cell.canonical}",
            )
    elif terminal_host.get("globally_closed") != 1:
        raise CalibrationFailure(
            "compiled_reduced_calibration_rejected",
            f"prove-none closure failed for {cell.canonical}",
        )
    if hybrid and not positive and terminal_host.get("switched") != 1:
        raise CalibrationFailure(
            "compiled_reduced_calibration_rejected",
            f"hybrid did not take its frozen switch for {cell.canonical}",
        )
    expected_prefix_decisions = prepared.prefix_nodes if rrns and prefix_arm else 0
    if terminal_host.get("prefix_decision_keys") != expected_prefix_decisions:
        raise CalibrationFailure(
            "work_receipt_rejected", "prefix decision reconstruction count differs"
        )
    if prefix_arm:
        frontier_work = terminal_host.get("heap_pushes", 0) + terminal_host.get(
            "heap_pops", 0
        )
        leaf_work = terminal_host.get("exact_leaves", 0) * 57
        for name, value in (
            ("prefix_frontier_operations", frontier_work),
            ("exact_leaf_57_term_evaluation", leaf_work),
        ):
            row = work_rows[PHASE_NAMES.index(name)]
            row["projection_work"] = value
            row["logical_operations"] = value

    def annotate(
        name: str,
        *,
        arithmetic_words: int = 0,
        transferred_bytes: int = 0,
        decision_keys: int = 0,
    ) -> None:
        row = work_rows[PHASE_NAMES.index(name)]
        row["arithmetic_words"] = arithmetic_words
        row["transferred_bytes"] = transferred_bytes
        row["decision_keys_reconstructed"] = decision_keys

    support_count = int(artifact["support_count"])
    exact_leaves = terminal_host.get("exact_leaves", 0)
    level_cover_rows = prepared.level_rows - 1
    annotate("provenance_rebind", transferred_bytes=FEATURE_WIDTH * 8)
    annotate(
        "H_component_contraction",
        arithmetic_words=(11 if rrns else 2) * prepared.h_rows,
        decision_keys=prepared.h_rows if rrns else 0,
    )
    annotate(
        "base_payload_transfer",
        arithmetic_words=(11 if rrns else 2) * prepared.source_rows
        if cold and cell.base_mode == BASE_MODES[1]
        else 0,
        transferred_bytes=coordinates["base_payload_transfer"],
        decision_keys=prepared.source_rows
        if rrns and cold and cell.base_mode == BASE_MODES[1]
        else 0,
    )
    annotate(
        "base_structural_cover",
        arithmetic_words=(11 if rrns else 2)
        * (prepared.source_rows + prepared.level_rows)
        if cold and cell.base_mode != BASE_MODES[1]
        else 0,
        decision_keys=(prepared.source_rows + prepared.level_rows)
        if rrns and cold and cell.base_mode != BASE_MODES[1]
        else 0,
    )
    annotate(
        "base_sparse_patch",
        arithmetic_words=(13 if rrns else 2) * support_count
        if cold and cell.base_mode == BASE_MODES[2]
        else 0,
        decision_keys=support_count
        if rrns and cold and cell.base_mode == BASE_MODES[2]
        else 0,
    )
    annotate(
        "arithmetic_encoding",
        arithmetic_words=11 * prepared.source_rows if rrns else 0,
        decision_keys=prepared.source_rows if rrns else 0,
    )
    annotate("prefix_base_bound_build", arithmetic_words=2 * prepared.prefix_nodes if prefix_arm else 0)
    annotate(
        "prefix_possible_term_bounds",
        arithmetic_words=2 * prepared.prefix_nodes if prefix_arm else 0,
        decision_keys=prepared.prefix_nodes if rrns and prefix_arm else 0,
    )
    annotate(
        "exact_leaf_57_term_evaluation",
        arithmetic_words=(11 if rrns else 2) * exact_leaves,
        decision_keys=exact_leaves if rrns else 0,
    )
    annotate(
        "direct_global_57_term_scan",
        arithmetic_words=(11 if rrns else 2) * scan_count if direct_arm else 0,
        decision_keys=scan_count if rrns and direct_arm else 0,
    )
    annotate(
        "zeta_seed_write",
        arithmetic_words=(11 if rrns else 2) * prepared.h_rows if zeta_runs else 0,
        decision_keys=prepared.h_rows if rrns and zeta_runs else 0,
    )
    annotate(
        "zeta_cover_edges",
        arithmetic_words=(11 if rrns else 2) * level_cover_rows if zeta_runs else 0,
        decision_keys=level_cover_rows if rrns and zeta_runs else 0,
    )
    annotate(
        "zeta_rank_six_stream",
        arithmetic_words=(11 if rrns else 2) * scan_count if zeta_runs else 0,
        decision_keys=scan_count if rrns and zeta_runs else 0,
    )
    annotate(
        "RRNS_decision_key_reconstruction",
        arithmetic_words=11 * scan_count if rrns and (direct_arm or zeta_runs) else 0,
        decision_keys=scan_count if rrns and (direct_arm or zeta_runs) else 0,
    )
    annotate("terminal_transfer", transferred_bytes=92)
    device_elapsed = tuple(
        int(
            round(
                cp.cuda.get_elapsed_time(
                    prepared.phase_events[index], prepared.phase_events[index + 1]
                )
                * 1_000_000.0
            )
        )
        for index in range(len(PHASE_NAMES))
    )
    partition = phase_partition(
        stamps, work_rows, device_elapsed_ns=device_elapsed
    )
    return {
        "schema_version": "pontius-adr0457-calibration-cell-v1",
        "pass_index": pass_index,
        "measured": pass_index in MEASURED_PASS_INDICES,
        "cell": asdict(cell),
        "canonical_cell_key": cell.canonical,
        "phase_partition": {
            "rows": [asdict(row) for row in partition.rows],
            "primitive_total_ns": partition.primitive_total_ns,
        },
        "terminal": terminal_host,
        "mode_semantics_verified": True,
        "RRNS_decisions_reconstructed_at_consumer_sites": rrns,
        "stored_pass_bit_authoritative": False,
    }


def _decode_positional_rows(np: object, raw: object, count: int) -> tuple[int, ...]:
    array = np.asarray(raw, dtype=np.uint64).reshape(-1, 2)  # type: ignore[attr-defined]
    if array.shape[0] < count:
        raise ValueError("positional output is shorter than its claimed domain")
    output = []
    for low, guard in array[:count]:
        unsigned = int(low)
        value = unsigned - (1 << 64) if unsigned >> 63 else unsigned
        expected_guard = (1 << 64) - 1 if value < 0 else 0
        if int(guard) != expected_guard:
            raise ArithmeticError("positional output guard differs")
        output.append(value)
    return tuple(output)


def _verify_cell_output(
    context: CompiledCalibrationContext,
    prepared: PreparedDeviceDomain,
    cell: CellKey,
    observation: Mapping[str, object],
) -> dict[str, object]:
    cp = context.cp
    np = context.np
    scratch = prepared.scratch
    terminal = _mapping(observation.get("terminal"), label="cell terminal")
    witness_rank = int(terminal.get("witness_rank", 0))
    exact_leaves = int(terminal.get("exact_leaves", 0))
    if cell.arm in ARM_NAMES[2:]:
        expected_terminal = expected_prefix_terminal(
            cell.cards,
            cell.runtime_mode,  # type: ignore[arg-type]
            cell.base_mode,  # type: ignore[arg-type]
            cell.arm == ARM_NAMES[3],
        )
        if any(terminal.get(name) != value for name, value in expected_terminal.items()):
            raise CalibrationFailure(
                "compiled_reduced_calibration_rejected",
                f"prefix coverage or witness receipt differs: {cell.canonical}",
            )
    if cell.arm in ARM_NAMES[2:] and exact_leaves:
        selected_ranks = tuple(
            int(value)
            for value in cp.asnumpy(scratch["selected_leaf_ranks"][:exact_leaves])
        )
        selected_output = scratch["selected_positional"]
        selected_prices = _decode_positional_rows(
            np, cp.asnumpy(selected_output), exact_leaves
        )
        selected_expected = tuple(
            exact_price(cell.runtime_mode, cell.base_mode, cell.cards, rank)  # type: ignore[arg-type]
            for rank in selected_ranks
        )
        if selected_prices != selected_expected:
            raise CalibrationFailure(
                "compiled_reduced_calibration_rejected",
                f"selected exact-leaf re-evaluation differs: {cell.canonical}",
            )
    if cell.runtime_mode == "positive_witness":
        expected = exact_price(
            cell.runtime_mode, cell.base_mode, cell.cards, witness_rank  # type: ignore[arg-type]
        )
        if expected <= 0 or int(terminal.get("witness_price", 0)) != expected:
            raise CalibrationFailure(
                "compiled_reduced_calibration_rejected",
                f"positive witness differs from authority: {cell.canonical}",
            )
        checked = 1
        digest = _integer_stream_digest((expected,))
    elif cell.arm in ARM_NAMES[:2] or cell.arm == ARM_NAMES[3]:
        expected_rows = exact_prices(
            cell.runtime_mode, cell.base_mode, cell.cards  # type: ignore[arg-type]
        )
        output = scratch["prices_positional"]
        observed = _decode_positional_rows(
            np, cp.asnumpy(output), prepared.source_rows
        )
        if cell.arithmetic_schedule == ARITHMETIC_SCHEDULES[1] and (
            cell.arm == ARM_NAMES[1] or cell.arm == ARM_NAMES[3]
        ):
            expected_rows = tuple(H_OUTPUT_SCALE * value for value in expected_rows)
        if observed != expected_rows:
            mismatch = next(
                index
                for index, (left, right) in enumerate(
                    zip(observed, expected_rows, strict=True)
                )
                if left != right
            )
            raise CalibrationFailure(
                "compiled_reduced_calibration_rejected",
                f"complete output differs at {mismatch}: {cell.canonical}",
            )
        checked = len(observed)
        digest = _integer_stream_digest(observed)
    else:
        checked = int(terminal.get("covered_sources", 0))
        digest = sha256(
            json.dumps(dict(terminal), sort_keys=True, separators=(",", ":")).encode(
                "ascii"
            )
        ).hexdigest()
    result = {
        "schema_version": "pontius-adr0457-cell-differential-v1",
        "canonical_cell_key": cell.canonical,
        "authority_coordinates_checked": checked,
        "output_sha256": digest,
        "unbounded_integer_authority_matched": True,
        "correlated_fault_boundary_checked_by_differential": True,
    }
    with context.stream:
        for name in (
            "prices_positional",
            "selected_leaf_ranks",
            "selected_positional",
        ):
            scratch[name].fill(0)
    context.stream.synchronize()
    return result


def _complete_positive_device_differential(
    context: CompiledCalibrationContext,
    prepared: PreparedDeviceDomain,
    cell: CellKey,
) -> dict[str, object]:
    """Untimed complete direct/zeta validation for one positive fixture.

    The timed positive mode is intentionally a one-witness query.  This
    laboratory-only replay computes every coordinate so that the stronger
    device differential promised by ADR-0457 is not inferred from that one
    witness.
    """

    if cell.runtime_mode != RUNTIME_MODES[0] or cell.arm not in ARM_NAMES[:2]:
        raise ValueError("complete positive differential key differs")
    cp = context.cp
    np = context.np
    scratch = prepared.scratch
    artifact = prepared.base_artifacts[
        (cell.runtime_mode, cell.base_mode, cell.arithmetic_schedule)
    ]
    rrns = cell.arithmetic_schedule == ARITHMETIC_SCHEDULES[1]
    bounds = {
        row.quantity: row.signed_absolute_bound
        for row in derive_arithmetic_admission().quantity_widths
    }
    zeta_bounds = {
        index: row.signed_absolute_bound
        for index, row in enumerate(derive_arithmetic_admission().zeta_rank_widths)
    }

    with context.stream:
        scratch["status"].fill(0)
        scratch["h_positional"].fill(0)
        scratch["prices_positional"].fill(0)
        scratch["zeta_positional"].fill(0)

    def admit(batch: object, decision: object, count: int, bound: int, first: bool) -> None:
        _launch(
            context,
            "admit_rrns_first_batch" if first else "admit_rrns_second_batch",
            count,
            (
                batch,
                decision,
                np.uint64(count),
                prepared.moduli,
                np.uint64(bound),
                scratch["status"],
            ),
        )

    if rrns:
        for first, channels, channel_count in (
            (True, prepared.first_channels, 5),
            (False, prepared.second_channels, 4),
        ):
            _launch(
                context,
                "contract_h_rrns_batch",
                prepared.h_rows * channel_count,
                (
                    prepared.raw_h[cell.runtime_mode],
                    prepared.pricing,
                    scratch["rrns_batch_arena"],
                    np.uint64(prepared.h_rows),
                    prepared.moduli,
                    channels,
                    np.int32(channel_count),
                    scratch["status"],
                ),
            )
            admit(
                scratch["rrns_batch_arena"],
                scratch["h_positional"],
                prepared.h_rows,
                bounds["contracted_h"],
                first,
            )
    else:
        _launch(
            context,
            "contract_h_positional",
            prepared.h_rows,
            (
                prepared.raw_h[cell.runtime_mode],
                prepared.pricing,
                scratch["h_positional"],
                np.uint64(prepared.h_rows),
                scratch["status"],
            ),
        )

    if cell.arm == ARM_NAMES[0]:
        if rrns:
            for first, channels, channel_count in (
                (True, prepared.first_channels, 5),
                (False, prepared.second_channels, 4),
            ):
                _launch(
                    context,
                    "direct_prices_rrns_batch",
                    prepared.source_rows * channel_count,
                    (
                        scratch["h_positional"],
                        artifact["base"],
                        scratch["rrns_batch_arena"],
                        np.int32(cell.cards),
                        np.uint64(prepared.source_rows),
                        prepared.moduli,
                        channels,
                        np.int32(channel_count),
                        scratch["status"],
                    ),
                )
                admit(
                    scratch["rrns_batch_arena"],
                    scratch["prices_positional"],
                    prepared.source_rows,
                    bounds["direct_price_accumulator"],
                    first,
                )
        else:
            _launch(
                context,
                "direct_prices_positional",
                prepared.source_rows,
                (
                    scratch["h_positional"],
                    artifact["base"],
                    scratch["prices_positional"],
                    np.int32(cell.cards),
                    np.uint64(prepared.source_rows),
                    scratch["status"],
                ),
            )
    elif rrns:
        seed_bound = max(zeta_bounds[level] for level in range(5))
        for first, channels, channel_count in (
            (True, prepared.first_channels, 5),
            (False, prepared.second_channels, 4),
        ):
            _launch(
                context,
                "zeta_seed_rrns_batch",
                prepared.h_rows * channel_count,
                (
                    scratch["h_positional"],
                    scratch["rrns_batch_arena"],
                    np.int32(cell.cards),
                    prepared.moduli,
                    channels,
                    np.int32(channel_count),
                    scratch["status"],
                ),
            )
            admit(
                scratch["rrns_batch_arena"],
                scratch["zeta_positional"],
                prepared.h_rows,
                seed_bound,
                first,
            )
        for level in range(1, SOURCE_WIDTH + 1):
            rows = comb(cell.cards, level)
            offset = level_offset(cell.cards, level)
            decision = scratch["zeta_positional"][offset * 2 :]
            for first, channels, channel_count in (
                (True, prepared.first_channels, 5),
                (False, prepared.second_channels, 4),
            ):
                _launch(
                    context,
                    "zeta_cover_rrns_batch",
                    rows * channel_count,
                    (
                        scratch["zeta_positional"],
                        scratch["h_positional"],
                        scratch["rrns_batch_arena"],
                        np.int32(cell.cards),
                        np.int32(level),
                        prepared.moduli,
                        channels,
                        np.int32(channel_count),
                        scratch["status"],
                    ),
                )
                admit(
                    scratch["rrns_batch_arena"],
                    decision,
                    rows,
                    zeta_bounds[level],
                    first,
                )
        for first, channels, channel_count in (
            (True, prepared.first_channels, 5),
            (False, prepared.second_channels, 4),
        ):
            _launch(
                context,
                "zeta_rank_six_rrns_batch",
                prepared.source_rows * channel_count,
                (
                    scratch["zeta_positional"],
                    artifact["base"],
                    scratch["rrns_batch_arena"],
                    np.int32(cell.cards),
                    np.uint64(prepared.source_rows),
                    prepared.moduli,
                    channels,
                    np.int32(channel_count),
                    scratch["status"],
                ),
            )
            admit(
                scratch["rrns_batch_arena"],
                scratch["prices_positional"],
                prepared.source_rows,
                bounds["zeta_output_scaled"],
                first,
            )
    else:
        _launch(
            context,
            "zeta_seed_positional",
            prepared.h_rows,
            (
                scratch["h_positional"],
                scratch["zeta_positional"],
                np.int32(cell.cards),
                scratch["status"],
            ),
        )
        for level in range(1, SOURCE_WIDTH + 1):
            _launch(
                context,
                "zeta_cover_positional",
                comb(cell.cards, level),
                (
                    scratch["zeta_positional"],
                    np.int32(cell.cards),
                    np.int32(level),
                    scratch["status"],
                ),
            )
        _launch(
            context,
            "zeta_rank_six_positional",
            prepared.source_rows,
            (
                scratch["zeta_positional"],
                artifact["base"],
                artifact["structural"],
                scratch["prices_positional"],
                np.int32(cell.cards),
                np.uint64(prepared.source_rows),
                np.int32(BASE_MODES.index(cell.base_mode)),
                scratch["status"],
            ),
        )

    context.stream.synchronize()
    status = int(cp.asnumpy(scratch["status"])[0])
    if status:
        raise CalibrationFailure(
            "compiled_reduced_calibration_rejected",
            f"complete positive differential status {status}: {cell.canonical}",
        )
    observed = _decode_positional_rows(
        np, cp.asnumpy(scratch["prices_positional"]), prepared.source_rows
    )
    expected = exact_prices(cell.runtime_mode, cell.base_mode, cell.cards)  # type: ignore[arg-type]
    if rrns and cell.arm == ARM_NAMES[1]:
        expected = tuple(H_OUTPUT_SCALE * value for value in expected)
    if observed != expected:
        raise CalibrationFailure(
            "compiled_reduced_calibration_rejected",
            f"complete positive output differs: {cell.canonical}",
        )
    digest = _integer_stream_digest(observed)
    with context.stream:
        for name in (
            "status",
            "h_positional",
            "prices_positional",
            "zeta_positional",
            "rrns_batch_arena",
        ):
            scratch[name].fill(0)
    context.stream.synchronize()
    return {
        "schema_version": "pontius-adr0457-complete-positive-differential-v1",
        "canonical_cell_key": cell.canonical,
        "authority_coordinates_checked": prepared.source_rows,
        "output_sha256": digest,
        "unbounded_integer_authority_matched": True,
        "laboratory_only": True,
    }


def _fit_projection(observations: Sequence[Mapping[str, object]]) -> dict[str, object]:
    measured = [
        row
        for row in observations
        if row.get("measured") is True
        and int(row.get("pass_index", -1)) in MEASURED_PASS_INDICES
    ]
    if len(measured) != 480 * len(MEASURED_PASS_INDICES):
        raise ValueError("measured calibration matrix is incomplete")
    by_cell: dict[tuple[str, str, str, str, str], dict[int, list[Mapping[str, object]]]] = {}
    for row in measured:
        cell = _mapping(row.get("cell"), label="fit cell")
        key = (
            str(cell["arm"]),
            str(cell["runtime_mode"]),
            str(cell["base_mode"]),
            str(cell["refresh_state"]),
            str(cell["arithmetic_schedule"]),
        )
        cards = int(cell["cards"])
        by_cell.setdefault(key, {}).setdefault(cards, []).append(row)
    if len(by_cell) != 4 * 2 * 3 * 2 * 2:
        raise ValueError("fit group domain differs")
    fit_rows = []
    primitive_rows = []
    primitive_lookup: dict[tuple[str, str, str, str, str], int] = {}
    for key in sorted(by_cell):
        domains = by_cell[key]
        if tuple(sorted(domains)) != DOMAINS or any(
            len(domains[cards]) != len(MEASURED_PASS_INDICES) for cards in DOMAINS
        ):
            raise ValueError("fit domain or repeat count differs")
        representative = CellKey(DOMAINS[0], *key)
        target_coordinates = phase_work_coordinates(representative, target=True)
        phase_uppers = []
        for phase_index, phase_name in enumerate(PHASE_NAMES):
            xs = []
            ys = []
            domain_rows = []
            for cards in DOMAINS:
                phase_samples = []
                work_samples = []
                for observation in domains[cards]:
                    partition = _mapping(
                        observation.get("phase_partition"), label="fit partition"
                    )
                    rows = partition.get("rows")
                    if not isinstance(rows, list) or len(rows) != len(PHASE_NAMES):
                        raise ValueError("fit phase rows differ")
                    phase = _mapping(rows[phase_index], label="fit phase")
                    if phase.get("name") != phase_name:
                        raise ValueError("fit phase order differs")
                    phase_samples.append(int(phase["elapsed_ns"]))
                    work_samples.append(int(phase["projection_work"]))
                if len(set(work_samples)) != 1:
                    raise ValueError("phase work changes across measured repeats")
                x = work_samples[0]
                y = max(phase_samples)
                xs.append(x)
                ys.append(y)
                domain_rows.append(
                    {
                        "cards": cards,
                        "projection_work": x,
                        "measured_walls_ns": phase_samples,
                        "maximum_response_ns": y,
                        "median_response_ns": sorted(phase_samples)[2],
                    }
                )
            fit = exact_nonnegative_affine_fit(
                xs, ys, target_coordinates[phase_name]
            )
            phase_uppers.append(fit.target_upper_ceiling)
            fit_rows.append(
                {
                    "schema_version": "pontius-adr0457-exact-affine-fit-v1",
                    "arm": key[0],
                    "runtime_mode": key[1],
                    "base_mode": key[2],
                    "refresh_state": key[3],
                    "arithmetic_schedule": key[4],
                    "phase": phase_name,
                    "projection_coordinate": PHASE_COORDINATES[phase_name],
                    "domains": domain_rows,
                    "target_work": target_coordinates[phase_name],
                    "candidate": fit.candidate,
                    "intercept": fraction_pair(fit.intercept),
                    "slope": fraction_pair(fit.slope),
                    "sse": fraction_pair(fit.sse),
                    "positive_residual_guard": fraction_pair(
                        fit.positive_residual_guard
                    ),
                    "target_prediction": fraction_pair(fit.target_prediction),
                    "target_upper": fraction_pair(fit.target_upper),
                    "target_upper_ceiling_ns": fit.target_upper_ceiling,
                }
            )
        primitive_upper = sum(phase_uppers)
        primitive_lookup[key] = primitive_upper
        primitive_rows.append(
            {
                "arm": key[0],
                "runtime_mode": key[1],
                "base_mode": key[2],
                "refresh_state": key[3],
                "arithmetic_schedule": key[4],
                "phase_upper_ceilings_ns": phase_uppers,
                "projected_primitive_upper_ns": primitive_upper,
                "symbolic_45_counterfactual_only": True,
            }
        )
    materiality_rows = []
    for base_mode, refresh_state, schedule in product(
        BASE_MODES, REFRESH_STATES, ARITHMETIC_SCHEDULES
    ):
        direct_key = (
            ARM_NAMES[0],
            "prove_none",
            base_mode,
            refresh_state,
            schedule,
        )
        zeta_key = (
            ARM_NAMES[1],
            "prove_none",
            base_mode,
            refresh_state,
            schedule,
        )
        direct = primitive_lookup[direct_key]
        zeta = primitive_lookup[zeta_key]
        materiality_rows.append(
            {
                "base_mode": base_mode,
                "refresh_state": refresh_state,
                "arithmetic_schedule": schedule,
                "direct_upper_ns": direct,
                "zeta_upper_ns": zeta,
                "zeta_at_most_half_direct": 2 * zeta <= direct,
            }
        )
    passed = all(row["zeta_at_most_half_direct"] for row in materiality_rows)
    return {
        "schema_version": "pontius-adr0457-fit-projection-v1",
        "fit_rows": fit_rows,
        "primitive_rows": primitive_rows,
        "materiality_rows": materiality_rows,
        "material_zeta_speed_claim": passed,
        "candidate_selected": None,
        "topology_selected": None,
        "arithmetic_schedule_selected": None,
        "production_base_classification": "producer_absent",
    }


def execute_calibration(
    emit: Callable[[str, Mapping[str, object]], None],
    *,
    laboratory_started_ns: int,
) -> dict[str, object]:
    """Run the frozen one-shot campaign.  Never called by source-seal tests."""

    from time import perf_counter_ns

    if not callable(emit):
        raise TypeError("calibration emitter must be callable")
    started = _plain_int(
        laboratory_started_ns, label="laboratory start", minimum=0
    )
    verify_preregistered_contract(require_result_absent=False)
    # The base audit must precede fixture generation and every compiler/device
    # operation.  It is deliberately source-bound and cannot infer a producer
    # from the synthetic control values built below.
    from . import legal_river_quotient_base_provenance as base_provenance

    audit = base_provenance.audit_base_producer(None)
    if (
        audit.classification != "producer_absent"
        or audit.terminal != "base_producer_unavailable_no_bakeoff_selection"
    ):
        raise CalibrationFailure(
            "production_base_boundary_rejected", "base producer audit differs"
        )
    emit(
        "production_base_audit",
        {
            "schema_version": "pontius-adr0457-production-base-audit-v1",
            "classification": audit.classification,
            "terminal": audit.terminal,
            "refresh_cadence": audit.refresh_cadence,
            "production_admission": audit.production_admission,
            "audit_precedes_fixture_and_device_science": True,
        },
    )
    validate_rrns_parameters()
    manifests = fixture_manifests()
    manifest_payload = [asdict(row) for row in manifests]
    authority_digest = sha256(
        json.dumps(manifest_payload, sort_keys=True, separators=(",", ":")).encode(
            "ascii"
        )
    ).hexdigest()
    emit(
        "fixture_authority",
        {
            "schema_version": "pontius-adr0457-fixture-authority-v1",
            "manifests": manifest_payload,
            "authority_sha256": authority_digest,
            "authority_committed_before_candidate_observations": True,
            "synthetic_controls_are_not_a_production_base": True,
        },
    )
    admission = derive_arithmetic_admission()
    emit(
        "arithmetic_admission",
        {
            "schema_version": "pontius-adr0457-arithmetic-admission-v1",
            "quantity_widths": [asdict(row) for row in admission.quantity_widths],
            "zeta_rank_widths": [asdict(row) for row in admission.zeta_rank_widths],
            "working_product_decimal": str(admission.working_product),
            "redundant_modulus": admission.redundant_modulus,
            "table_range_sufficient": admission.table_range_sufficient,
            "scalar_range_sufficient": admission.scalar_range_sufficient,
            "bounded_single_modulus_decision_sufficient": (
                admission.bounded_single_modulus_decision_sufficient
            ),
            "sha256": admission.sha256,
        },
    )
    switch_proofs = tuple(
        prove_early_hybrid_switch(cards, base_mode)  # type: ignore[arg-type]
        for cards, base_mode in product(DOMAINS, BASE_MODES)
    )
    if not all(row.switches_early for row in switch_proofs):
        raise CalibrationFailure(
            "hybrid_switch_control_rejected", "a frozen domain/base does not switch early"
        )
    emit(
        "hybrid_switch_controls",
        {
            "schema_version": "pontius-adr0457-hybrid-switch-controls-v1",
            "rows": [asdict(row) for row in switch_proofs],
            "all_switch_exactly_at_ceil_N_over_64": True,
        },
    )
    source_contract = {
        **cuda_source_contract(),
        "timed_host_surface": timed_host_surface_contract(
            Path(__file__).read_text(encoding="utf-8")
        ),
    }
    emit("source_contract", source_contract)
    observations: list[Mapping[str, object]] = []
    differentials: list[Mapping[str, object]] = []
    complete_positive_keys: set[tuple[int, str, str, str]] = set()
    with tempfile.TemporaryDirectory(prefix="pontius-adr0457-calibration-") as temporary:
        context = _load_compiled_context(
            Path(temporary).resolve(), emit, laboratory_started_ns=started
        )
        prepared = _prepare_device_domains(context, emit)
        for pass_index in ALL_PASS_INDICES:
            for cell in pass_cells(pass_index):
                if perf_counter_ns() - started > LABORATORY_WALL_NS:
                    raise CalibrationFailure(
                        "laboratory_wall_rejected",
                        "compiled calibration crossed the frozen laboratory wall",
                    )
                observation = _run_calibration_cell(
                    context, prepared[cell.cards], cell, pass_index=pass_index
                )
                differential = _verify_cell_output(
                    context, prepared[cell.cards], cell, observation
                )
                complete_key = (
                    cell.cards,
                    cell.arm,
                    cell.base_mode,
                    cell.arithmetic_schedule,
                )
                if (
                    cell.runtime_mode == RUNTIME_MODES[0]
                    and cell.arm in ARM_NAMES[:2]
                    and complete_key not in complete_positive_keys
                ):
                    complete = _complete_positive_device_differential(
                        context, prepared[cell.cards], cell
                    )
                    differential = {
                        **dict(differential),
                        "complete_positive_output": complete,
                    }
                    complete_positive_keys.add(complete_key)
                observations.append(observation)
                differentials.append(differential)
                emit(
                    "calibration_cell",
                    {
                        **dict(observation),
                        "differential": dict(differential),
                    },
                )
    projection = _fit_projection(observations)
    emit("fit_projection", projection)
    laboratory_elapsed = perf_counter_ns() - started
    if laboratory_elapsed > LABORATORY_WALL_NS:
        raise CalibrationFailure(
            "laboratory_wall_rejected", "calibration crossed its laboratory wall"
        )
    claims = source_boundary_claims()
    claims["compiled_calibration_result"] = True
    claims["material_zeta_speed_claim"] = projection["material_zeta_speed_claim"]
    claims["symbolic_45_primitive_projection"] = True
    return {
        "schema_version": "pontius-adr0457-compiled-calibration-terminal-evidence-v1",
        "terminal": "completed_reduced_compiled_calibration_production_base_absent",
        "passed": True,
        "laboratory_elapsed_ns": laboratory_elapsed,
        "scientific_call_count": len(observations),
        "warmup_call_count": 480,
        "measured_call_count": 2_400,
        "differential_count": len(differentials),
        "complete_positive_differential_count": len(complete_positive_keys),
        "authority_sha256": authority_digest,
        "fit_projection_sha256": sha256(
            json.dumps(projection, sort_keys=True, separators=(",", ":")).encode(
                "ascii"
            )
        ).hexdigest(),
        "production_base_classification": "producer_absent",
        "candidate_selected": None,
        "topology_selected": None,
        "arithmetic_schedule_selected": None,
        "claims": claims,
    }


__all__ = [
    "ALL_PASS_INDICES",
    "ARITHMETIC_SCHEDULES",
    "ARM_NAMES",
    "BASE_MODES",
    "CONFIG_RELATIVE_PATH",
    "CONFIG_SHA256",
    "CUDA_SOURCE",
    "CUDA_SOURCE_SHA256",
    "DOMAINS",
    "FEATURE_WIDTH",
    "KERNEL_NAMES",
    "MEASURED_PASS_INDICES",
    "PHASE_CALLBACK_NAMES",
    "PHASE_COORDINATES",
    "PHASE_NAMES",
    "PREREGISTRATION_COMMIT",
    "REDUNDANT_MODULUS",
    "REJECTED_LIVENESS_EQUIVALENCE",
    "REFRESH_STATES",
    "RESULT_RELATIVE_PATH",
    "RUNTIME_MODES",
    "WORKING_MODULI",
    "AffineFit",
    "ArithmeticAdmission",
    "BufferLifetime",
    "CalibrationFailure",
    "CellKey",
    "CubinResource",
    "DecisionKeyReceipt",
    "DriverResource",
    "FixtureManifest",
    "HybridSwitchProof",
    "MemoryLiveness",
    "PhasePartition",
    "PhaseRow",
    "PrefixGeometry",
    "PtxasResource",
    "SassLocalSites",
    "WidthPlan",
    "canonical_lf_sha256",
    "colex_rank",
    "colex_unrank",
    "compile_argv",
    "complete_masks",
    "cuda_source_contract",
    "derive_arithmetic_admission",
    "exact_nonnegative_affine_fit",
    "exact_price",
    "exact_prices",
    "execute_calibration",
    "execution_cells",
    "fixture_manifest",
    "fixture_manifests",
    "fraction_pair",
    "forbidden_literal_escape_mutation",
    "independent_canonical_lf",
    "load_preregistered_config",
    "memory_liveness",
    "parse_fraction_pair",
    "parse_cuobjdump_resource_usage",
    "parse_nvdisasm_local_sites",
    "parse_ptxas_verbose",
    "pass_cells",
    "phase_partition",
    "phase_work_coordinates",
    "prefix_geometry",
    "pricing_vector",
    "prove_early_hybrid_switch",
    "raw_h_row",
    "reconstruct_decision_key",
    "reduced_memory_plan",
    "resource_gate",
    "rrns_batch_arena_bytes",
    "rrns_batch_arena_rows",
    "signed_crt",
    "source_boundary_claims",
    "sparse_support_ranks",
    "symbolic_geometry",
    "timed_host_surface_contract",
    "validate_rrns_parameters",
    "verify_preregistered_contract",
    "wall_passes",
]
